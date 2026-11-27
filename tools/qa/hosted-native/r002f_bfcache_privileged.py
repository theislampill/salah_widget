#!/usr/bin/env python3
"""Fixed APT commands in an owned root PID/mount namespace, with actual teardown.

The ordinary caller never asserts that an unprivileged kill stopped root children.
The root init owns its timer and cancellation, qualifies detached-child teardown,
and exits the namespace before the caller records an actual returned launcher.
"""
import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import pwd
import signal
import subprocess
import sys
import time

import r002f_bfcache_tools as tools

HERE = Path(__file__).resolve().parent
PROTOCOL = 'r002f-bfcache-privileged-controller/1'
REQUEST = 'r002f-bfcache-privileged-request/1'
LABELS = ('apt-update', 'apt-install')
need = tools.need


class PrivilegedCancelled(RuntimeError):
    """Must not be swallowed by selectors' InterruptedError/EINTR handling."""


class PrivilegedDeadline(RuntimeError):
    """The owned absolute timer has expired; cleanup keeps its original bound."""


CONTROL = '''import json,os,signal,sys
read,write=os.pipe()
child=os.fork()
if child==0:
    os.close(read);os.setsid()
    for fd in (0,1,2):
        try:os.close(fd)
        except OSError:pass
    os.write(write,b"R");os.close(write)
    while True:signal.pause()
os.close(write)
assert os.read(read,1)==b"R"
os.close(read)
print(json.dumps({"child":os.getpid(),"detached":child,"uid":os.getuid()}),flush=True)
'''

APT_ACCESS_CONTROL = ('import os,sys;from pathlib import Path;os.setgroups([]);os.setgid(int(sys.argv[2]));os.setuid(int(sys.argv[1]));'
    'root=Path(sys.argv[3]);'
    '[p.read_bytes() for p in (root/"apt.conf",root/"sources.list",Path(sys.argv[4]))];'
    'a=root/"lists/partial/source-access-control";b=root/"cache/archives/partial/source-access-control";'
    'a.write_bytes(b"APT_SANDBOX_CONTROL");b.write_bytes(b"APT_SANDBOX_CONTROL");a.unlink();b.unlink();'
    'print("APT_SANDBOX_ACCESS_CONFIRMED")')


def source_records():
    """The root request binds the same complete selected source dependency map."""
    import runner_environment as runner
    return {name: tools.file_record(runner.ROOT / name) for name in runner.source_files()}


def apt_access_argv(uid, gid, work):
    import r002f_bfcache_system as system
    return ['/usr/bin/python3', '-B', '-c', APT_ACCESS_CONTROL, str(uid), str(gid), str(work), system.KEYRING]


def admit_small_process(value, argv, folder, label):
    """Read the actual bounded qualification process, including retained bytes."""
    need(value.get('argv') == argv and value.get('cwd') == str(folder) and value.get('complete') is True
         and type(value.get('returncode')) is int and value['returncode'] == 0
         and value.get('timedOut') is False and value.get('overflow') is False and value.get('groupStopped') is True
         and type(value.get('pid')) is int and value['pid'] > 1 and not value.get('error'),
         'actual qualification command/process differs')
    seconds = value.get('timeoutSeconds'); elapsed = value.get('elapsedSeconds')
    need(type(seconds) in (int, float) and math.isfinite(seconds) and 0 < seconds <= 5
         and type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed <= seconds,
         'actual qualification deadline differs')
    need(set(value['streams']) == {'stdout', 'stderr'}, 'actual qualification streams missing')
    for key in ('stdout', 'stderr'):
        row = value['streams'][key]; tools.require_record(row)
        need(row['path'] == str(folder / (label + '.' + key))
             and all(type(value[field][key]) is int for field in ('observedBytes', 'retainedBytes', 'maxBytes'))
             and value['observedBytes'][key] == value['retainedBytes'][key] == row['bytes']
             and 0 <= row['bytes'] <= value['maxBytes'][key] == 4096,
             'actual qualification retained-byte accounting differs')
    return True


def namespaces():
    return {name: os.readlink('/proc/self/ns/' + name) for name in ('pid', 'mnt', 'net')}


def process_row(pid):
    path = Path('/proc') / str(pid)
    raw = (path / 'stat').read_text(); fields = raw.rsplit(') ', 1)[1].split()
    status = (path / 'status').read_text()
    uid = int(next(line for line in status.splitlines() if line.startswith('Uid:')).split()[1])
    again = (path / 'stat').read_text().rsplit(') ', 1)[1].split()
    need(fields[19] == again[19], 'process identity changed during census')
    return {'pid': pid, 'ppid': int(fields[1]), 'group': int(fields[2]), 'session': int(fields[3]),
            'startTicks': fields[19], 'uid': uid}


def descendants(namespace):
    if namespace: need(os.geteuid() == 0 and os.getpid() == 1, 'owned root PID namespace required')
    rows = {}
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal() or int(path.name) == os.getpid(): continue
        try: rows[int(path.name)] = process_row(int(path.name))
        except (FileNotFoundError, ProcessLookupError): continue
        except PermissionError:
            if namespace: raise
    if namespace: selected = set(rows)
    else:
        selected = {os.getpid()}; previous = set()
        while selected != previous:
            previous = set(selected); selected.update(pid for pid, row in rows.items() if row['ppid'] in selected)
        selected.discard(os.getpid())
    need(len(selected) <= 512, 'owned descendant census exceeded bound')
    result = [rows[pid] for pid in sorted(selected)]
    need(namespace or all(row['uid'] == os.getuid() for row in result), 'same-UID source control crossed ownership')
    return result


def reap_owned(namespace):
    """Actual SIGKILL and waitpid; namespace exit remains a second kernel boundary."""
    killed = []; reaped = []
    while True:
        rows = descendants(namespace)
        if rows:
            if namespace:
                # PID 1 is excluded by Linux kill(-1); other PID namespaces are not visible.
                try: os.kill(-1, signal.SIGKILL)
                except ProcessLookupError: pass
                killed += rows
            else:
                for row in rows:
                    try:
                        current = process_row(row['pid'])
                        need(current['startTicks'] == row['startTicks'] and current['uid'] == os.getuid(), 'foreign/reused PID refused')
                        os.kill(row['pid'], signal.SIGKILL); killed.append(row)
                    except (FileNotFoundError, ProcessLookupError): pass
        try:
            pid, status = os.waitpid(-1, 0 if rows else os.WNOHANG)
        except ChildProcessError:
            need(not descendants(namespace), 'owned processes remain without waited children')
            break
        if pid:
            reaped.append({'pid': pid, 'status': status,
                           'signal': os.WTERMSIG(status) if os.WIFSIGNALED(status) else None,
                           'returncode': os.WEXITSTATUS(status) if os.WIFEXITED(status) else None})
        elif not rows: break
    remaining = descendants(namespace)
    need(not remaining, 'owned descendants did not stop')
    return {'killed': killed, 'reaped': reaped, 'remaining': remaining}


def qualify(folder, label, deadline, *, namespace, owner=None):
    if namespace: need(os.getuid() == 0 and os.getpid() == 1, 'owned root PID namespace required')
    else:
        need(os.getuid() > 0 and os.getpid() != 1, 'same-UID source control must not run as root init')
        libc = ctypes.CDLL(None, use_errno=True)
        need(libc.prctl(36, 1, 0, 0, 0) == 0, 'source controller could not become a child subreaper')
    need(not descendants(namespace), 'controller started with unrelated descendants')
    seconds = min(5, deadline - time.monotonic()); need(seconds > 0, 'qualification reached aggregate deadline')
    result = {'scope': 'HOSTED_ROOT_PID_NAMESPACE' if namespace else 'SOURCE_CONTROL_SAME_UID_ONLY',
              'status': 'INCOMPLETE', 'hostedRootQualification': namespace, 'nativeObservation': False}
    try:
        process = tools.run_bounded([sys.executable, '-B', '-c', CONTROL], folder, label + '-qualifier', seconds,
                                     max_stdout=4096, max_stderr=4096, output_owner=owner)
        result['process'] = process
        need(process['complete'], 'actual detached-child qualifier did not return')
        declared = json.loads(Path(process['streams']['stdout']['path']).read_bytes())
        escaped = descendants(namespace); result['escaped'] = escaped
        need(declared == {'child': process['pid'], 'detached': escaped[0]['pid'] if len(escaped) == 1 else None, 'uid': os.getuid()}
             and len(escaped) == 1 and escaped[0]['uid'] == os.getuid() and escaped[0]['ppid'] == os.getpid()
             and escaped[0]['group'] == escaped[0]['session'] == escaped[0]['pid'], 'actual escaped session/process identity differs')
        result.update(reap_owned(namespace))
        need(len(result['reaped']) == 1 and result['reaped'][0]['pid'] == declared['detached']
             and result['reaped'][0]['signal'] == signal.SIGKILL, 'detached source-control child was not actually reaped')
        result['status'] = 'QUALIFIED'
    finally:
        if descendants(namespace): result['failureCleanup'] = reap_owned(namespace)
    return result


def source_control(folder):
    """Called only by a separate unprivileged control process, never by hosted CLI."""
    folder = Path(folder)
    return qualify(folder, 'source', time.monotonic() + 10, namespace=False)


def deadline_interrupt(cancel, deadline):
    if Path(cancel).exists(): raise PrivilegedCancelled('original caller cancelled privileged acquisition')
    if time.monotonic() >= deadline: raise PrivilegedDeadline('original privileged acquisition deadline reached')


def source_failure_control(folder, mode):
    """Actual same-UID negative children; explicitly not privileged qualification."""
    need(os.getuid() > 0 and os.getpid() != 1 and mode in ('timeout', 'overflow', 'cancel', 'outer-deadline'),
         'unprivileged source-only failure control required')
    libc = ctypes.CDLL(None, use_errno=True); need(libc.prctl(36, 1, 0, 0, 0) == 0, 'source subreaper unavailable')
    folder = Path(folder); cancel = folder / 'source.cancel'
    code = CONTROL + ('sys.stdout.buffer.write(b"X"*16384);sys.stdout.buffer.flush()\n' if mode == 'overflow' else '')
    code += 'while True:signal.pause()\n'
    value = {'scope': 'SOURCE_CONTROL_SAME_UID_ONLY', 'mode': mode, 'nativeObservation': False,
             'hostedRootQualification': False, 'status': 'INCOMPLETE'}
    previous = None
    if mode in ('cancel', 'outer-deadline'):
        def interrupt(signum, frame):
            rows = descendants(False)
            if len(rows) == 2 and any(row['pid'] == row['session'] == row['group'] and row['ppid'] != os.getpid() for row in rows):
                value['interruptionPopulation'] = rows
                signal.setitimer(signal.ITIMER_REAL, 0)
                if mode == 'cancel': cancel.write_bytes(b'CANCEL\n')
                deadline_interrupt(cancel, time.monotonic() - 1 if mode == 'outer-deadline' else time.monotonic() + 1)
        previous = signal.signal(signal.SIGALRM, interrupt); signal.setitimer(signal.ITIMER_REAL, 0.02, 0.02)
    try:
        value['process'] = tools.run_bounded([sys.executable, '-B', '-c', code], folder, 'source-failure',
                                             0.3 if mode == 'timeout' else 3, max_stdout=4096, max_stderr=4096)
    except Exception as error: value['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        if previous is not None:
            signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, previous)
        value['escaped'] = descendants(False); value.update(reap_owned(False))
        value['streams'] = {key: tools.file_record(folder / ('source-failure.' + key)) for key in ('stdout', 'stderr')}
        tools.save(folder / 'source-control-state.json', value)
    need(1 <= len(value['escaped']) <= 2 and len(value['reaped']) == len(value['escaped'])
         and all(row['signal'] == signal.SIGKILL for row in value['reaped'])
         and not value['remaining'], 'actual negative-control detached descendant was not reaped')
    if mode == 'timeout': need(value['process']['timedOut'] is True and value['process']['complete'] is False, 'actual timeout missing')
    elif mode == 'overflow': need(value['process']['overflow'] is True and value['process']['complete'] is False, 'actual overflow missing')
    else: need(value.get('error', '').startswith('PrivilegedCancelled:' if mode == 'cancel' else 'PrivilegedDeadline:'), 'actual outer cancellation/deadline missing')
    value['status'] = 'EXPECTED_REFUSAL_WITH_ACTUAL_TEARDOWN'
    return value


def save_owned(path, value, owner):
    uid, gid = os.geteuid(), os.getegid()
    try:
        os.setegid(owner[1]); os.seteuid(owner[0]); return tools.save(path, value)
    finally:
        os.seteuid(uid); os.setegid(gid)


def launcher(request_path, digest, seconds, environment):
    return ['/usr/bin/sudo', '-n', '/usr/bin/timeout', '--signal=KILL', str(seconds) + 's',
            '/usr/bin/unshare', '--pid', '--fork', '--mount', '--mount-proc', '--propagation', 'private', '--kill-child=KILL',
            '/usr/bin/env', '-i', *[key + '=' + value for key, value in sorted(environment.items())],
            '/usr/bin/python3', '-B', str(HERE / 'r002f_bfcache_privileged.py'), '--request', str(request_path), '--request-sha256', digest]


def execute(argv, folder, label, timeout, *, work, version, env, max_stdout, max_stderr, cwd):
    """Wait for the root controller; cancellation is a scoped file, never an unprivileged root kill."""
    import r002f_bfcache_system as system
    folder = Path(folder); work = Path(work); task = folder.parent.parent
    need(label in LABELS and Path(cwd) == folder and 0 < timeout <= system.LIMITS[label]
         and argv == system.command(label, work, work / 'sources.list', version)
         and env == system.command_environment(work), 'fixed privileged acquisition command differs')
    request_path = folder / (label + '.request.json'); result_path = folder / (label + '.controller.json')
    cancel = folder / (label + '.cancel')
    began = time.monotonic()
    request = {'protocol': REQUEST, 'label': label, 'task': str(task), 'folder': str(folder), 'work': str(work),
               'argv': argv, 'version': version, 'timeoutSeconds': timeout, 'deadlineMonotonic': began + timeout,
               'environment': env, 'uid': os.getuid(), 'gid': os.getgid(), 'parentNamespaces': namespaces(),
               'maxBytes': {'stdout': max_stdout, 'stderr': max_stderr},
               'launcherInputsScope': 'HISTORICAL_PRE_LAUNCH_SYSTEM_FILES',
               'launcherInputs': {name: tools.file_record(path, system=True) for name, path in system.BOOTSTRAP.items()
                                  if name in ('sudo', 'timeout', 'unshare', 'env', 'systemPython')},
               'sources': source_records()}
    request_record = tools.save(request_path, request)
    launch = launcher(request_path, request_record['sha256'], timeout, env)
    paths = {key: folder / (label + '-launcher.' + key) for key in ('stdout', 'stderr')}
    process = None; interrupted = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        with os.fdopen(os.open(paths['stdout'], flags, 0o600), 'wb') as out, \
             os.fdopen(os.open(paths['stderr'], flags, 0o600), 'wb') as err:
            process = subprocess.Popen(launch, cwd=folder, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err)
            try: process.wait()
            except BaseException as error:
                interrupted = type(error).__name__ + ': ' + str(error)
                if not cancel.exists(): system.write_bytes(cancel, b'CANCEL\n')
                # Both root init and the privileged timeout already own their
                # original absolute bound. Await actual namespace/launcher exit.
                process.wait()
    finally:
        completion = {'argv': launch, 'cwd': str(folder), 'environment': env, 'pid': None if process is None else process.pid,
                      'returned': process is not None and process.returncode is not None,
                      'returncode': None if process is None else process.returncode, 'interrupted': interrupted,
                      'timeoutSeconds': timeout, 'elapsedSeconds': time.monotonic() - began,
                      'streams': {key: tools.file_record(path) for key, path in paths.items() if path.exists()}}
        tools.save(folder / (label + '.launcher.json'), completion)
    need(completion['returned'] and completion['returncode'] == 0 and not interrupted
         and completion['elapsedSeconds'] <= timeout
         and set(completion['streams']) == {'stdout', 'stderr'}
         and all(row['bytes'] <= 65536 for row in completion['streams'].values()), 'privileged launcher did not return within its original bound')
    body = tools.load(result_path)
    need(body.get('status') == 'COMPLETE' and body.get('request') == request_record, 'privileged command/controller incomplete')
    value = body['command']
    value['privilegedController'] = {'request': request_record, 'result': tools.file_record(result_path),
                                   'launcher': tools.file_record(folder / (label + '.launcher.json'))}
    admit(value['privilegedController'], argv, folder, label)
    return value


def apt_access(work, folder, label, deadline, owner):
    import r002f_bfcache_system as system
    account = pwd.getpwnam('_apt'); need(account.pw_uid > 0 and account.pw_gid > 0, 'nonroot _apt account required')
    for path in (work / 'lists/partial', work / 'cache/archives/partial'):
        need(path.is_dir() and not path.is_symlink(), 'literal package sandbox directory required')
        os.chown(path, account.pw_uid, account.pw_gid); path.chmod(0o700)
    seconds = min(5, deadline - time.monotonic()); need(seconds > 0, 'sandbox access qualification reached aggregate deadline')
    value = tools.run_bounded(apt_access_argv(account.pw_uid, account.pw_gid, work),
                              folder, label + '-apt-access', seconds, max_stdout=4096, max_stderr=4096, output_owner=owner)
    need(value['complete'] and Path(value['streams']['stdout']['path']).read_bytes() == b'APT_SANDBOX_ACCESS_CONFIRMED\n',
         'actual _apt sandbox cannot read/write the bound public package workspace')
    return {'uid': account.pw_uid, 'gid': account.pw_gid, 'process': value, 'status': 'PASS'}


def root_run(request_path, expected_sha256):
    need(os.getuid() == os.geteuid() == 0 and os.getpid() == 1, 'owned root PID namespace required before any package command')
    import r002f_bfcache_system as system
    request_record = tools.file_record(request_path); need(request_record['sha256'] == expected_sha256, 'privileged request identity differs')
    request = tools.load(request_path); label = request['label']; folder = Path(request['folder']); work = Path(request['work'])
    task = Path(request['task']); owner = (request['uid'], request['gid']); actual = namespaces()
    need(request.get('protocol') == REQUEST and label in LABELS and all(type(value) is int and value > 0 for value in owner)
         and request_record['uid'] == owner[0] and Path(request_path) == folder / (label + '.request.json')
         and folder == task / 'capture/r002f-bfcache-tools', 'scoped privileged request differs')
    for path in (task, task / 'capture', folder):
        need(path.resolve() == path and not path.is_symlink() and path.stat().st_uid == owner[0]
             and path.stat().st_mode & 0o777 == 0o700, 'private owner task path differs')
    need(actual['pid'] != request['parentNamespaces']['pid'] and actual['mnt'] != request['parentNamespaces']['mnt']
         and actual['net'] == request['parentNamespaces']['net'], 'owned PID/mount namespace and acquisition network differ')
    need(type(request['timeoutSeconds']) in (int, float) and 0 < request['timeoutSeconds'] <= system.LIMITS[label]
         and type(request['deadlineMonotonic']) in (int, float) and math.isfinite(request['deadlineMonotonic'])
         and 0 < request['deadlineMonotonic'] - time.monotonic() <= request['timeoutSeconds'], 'original absolute acquisition deadline differs')
    need(request['environment'] == system.command_environment(work)
         and request['argv'] == system.command(label, work, work / 'sources.list', request['version'])
         and request['maxBytes'] == {'stdout': 4 * 1024 * 1024, 'stderr': 4 * 1024 * 1024}, 'fixed privileged command/environment differs')
    expected_launch = {name: path for name, path in system.BOOTSTRAP.items()
                       if name in ('sudo', 'timeout', 'unshare', 'env', 'systemPython')}
    need(request.get('launcherInputsScope') == 'HISTORICAL_PRE_LAUNCH_SYSTEM_FILES'
         and set(request['launcherInputs']) == set(expected_launch)
         and all(request['launcherInputs'][name]['path'] == path for name, path in expected_launch.items()),
         'actual privileged launcher input population differs')
    tools.current_records(request['launcherInputs'])
    system.workspace_current(work, owner[0])
    need(request['sources'] == source_records(), 'complete privileged source population changed before package invocation')
    if label == 'apt-install':
        need(system.decoder_candidate((folder / 'decoder-policy.stdout').read_text(), (folder / 'decoder-madison.stdout').read_text())
             == request['version'], 'root install candidate has no actual official policy')
    body = {'protocol': PROTOCOL, 'status': 'INCOMPLETE', 'nativeObservation': False, 'request': request_record,
            'root': {'uid': os.getuid(), 'pid': os.getpid(), 'namespaces': actual}, 'command': None,
            'launcherInputsAdmittedBeforeCommand': hashlib.sha256(json.dumps(request['launcherInputs'], sort_keys=True).encode()).hexdigest()}
    cancel = folder / (label + '.cancel'); deadline = request['deadlineMonotonic']; started = time.monotonic()
    def interrupt(signum, frame):
        try: deadline_interrupt(cancel, deadline)
        except BaseException:
            # One interruption owns teardown. A repeating alarm must not break
            # kill/wait or stream-finalization again while cleanup is in flight.
            signal.setitimer(signal.ITIMER_REAL, 0)
            raise
    previous = signal.signal(signal.SIGALRM, interrupt); signal.setitimer(signal.ITIMER_REAL, 0.02, 0.02)
    try:
        body['qualification'] = qualify(folder, label, deadline, namespace=True, owner=owner)
        need(body['qualification']['status'] == 'QUALIFIED', 'actual hosted privileged teardown qualification failed')
        body['aptSandbox'] = apt_access(work, folder, label, deadline, owner)
        need(not descendants(True), 'qualification left an owned child')
        remaining = deadline - time.monotonic(); need(remaining > 0, 'original deadline reached before apt invocation')
        body['command'] = tools.run_bounded(request['argv'], folder, label, remaining, max_stdout=request['maxBytes']['stdout'],
                                            max_stderr=request['maxBytes']['stderr'], env=request['environment'], cwd=folder,
                                            output_owner=owner)
        body['unexpectedDescendants'] = descendants(True)
        need(body['command']['complete'] and not body['unexpectedDescendants'], 'actual apt command or privileged descendant custody incomplete')
        body['status'] = 'COMPLETE'
    except Exception as error: body['error'] = type(error).__name__ + ': ' + str(error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, previous)
        body['cleanup'] = reap_owned(True)
        for path in (work / 'lists/partial', work / 'cache/archives/partial'):
            if path.is_dir() and not path.is_symlink(): os.chown(path, *owner); path.chmod(0o700)
        body['elapsedSeconds'] = time.monotonic() - started
        save_owned(folder / (label + '.controller.json'), body, owner)
    return 0 if body['status'] == 'COMPLETE' else 2


def admit_qualification(value):
    need(value.get('scope') == 'HOSTED_ROOT_PID_NAMESPACE' and value.get('hostedRootQualification') is True
         and value.get('nativeObservation') is False and value.get('status') == 'QUALIFIED'
         and len(value['escaped']) == len(value['reaped']) == 1 and not value['remaining'],
         'actual root qualification population differs')
    process = value['process']; escaped = value['escaped'][0]; reaped = value['reaped'][0]
    output = Path(process['streams']['stdout']['path'])
    need(output.name.endswith('-qualifier.stdout'), 'literal root qualification stream differs')
    admit_small_process(process, ['/usr/bin/python3', '-B', '-c', CONTROL], output.parent, output.name[:-7])
    need(escaped['uid'] == 0 and escaped['ppid'] == 1 and escaped['pid'] == escaped['group'] == escaped['session']
         and reaped['pid'] == escaped['pid'] and reaped['signal'] == signal.SIGKILL and reaped['returncode'] is None,
         'actual root detached PID/session/wait result differs')
    tools.current_records(process)
    body = json.loads(Path(process['streams']['stdout']['path']).read_bytes())
    need(body == {'child': process['pid'], 'detached': escaped['pid'], 'uid': 0}, 'actual root qualifier output differs')
    return True


def admit(value, argv, folder, label):
    import r002f_bfcache_system as system
    request = tools.load(value['request']['path']); body = tools.load(value['result']['path']); launch = tools.load(value['launcher']['path'])
    need(body.get('protocol') == PROTOCOL and body.get('status') == 'COMPLETE' and body.get('nativeObservation') is False
         and body.get('request') == value['request'] and not body.get('error') and request['argv'] == argv and request['label'] == label,
         'current privileged controller/request differs')
    need(request.get('launcherInputsScope') == 'HISTORICAL_PRE_LAUNCH_SYSTEM_FILES'
         and body.get('launcherInputsAdmittedBeforeCommand') == hashlib.sha256(json.dumps(request['launcherInputs'], sort_keys=True).encode()).hexdigest(),
         'historical actual launcher admission is missing')
    need(request.get('protocol') == REQUEST and request['sources'] == source_records()
         and request['task'] == str(folder.parent.parent)
         and all(type(request[key]) is int and request[key] > 0 for key in ('uid', 'gid'))
         and type(request['timeoutSeconds']) in (int, float) and math.isfinite(request['timeoutSeconds'])
         and 0 < request['timeoutSeconds'] <= system.LIMITS[label]
         and request['maxBytes'] == {'stdout': 4 * 1024 * 1024, 'stderr': 4 * 1024 * 1024},
         'complete retained privileged request/source population differs')
    work = Path(request['work'])
    need(request['environment'] == system.command_environment(work)
         and request['argv'] == system.command(label, work, work / 'sources.list', request['version'])
         and Path(request['folder']) == folder and value['request']['path'] == str(folder / (label + '.request.json'))
         and value['result']['path'] == str(folder / (label + '.controller.json'))
         and value['launcher']['path'] == str(folder / (label + '.launcher.json')), 'literal current privileged task/command differs')
    need(body['root']['uid'] == 0 and body['root']['pid'] == 1
         and body['root']['namespaces']['pid'] != request['parentNamespaces']['pid']
         and body['root']['namespaces']['mnt'] != request['parentNamespaces']['mnt']
         and body['root']['namespaces']['net'] == request['parentNamespaces']['net'], 'actual root namespace receipt differs')
    admit_qualification(body['qualification'])
    sandbox = body['aptSandbox']; process = sandbox['process']
    need(sandbox['status'] == 'PASS' and all(type(sandbox[key]) is int and sandbox[key] > 0 for key in ('uid', 'gid'))
         and Path(process['streams']['stdout']['path']).read_bytes() == b'APT_SANDBOX_ACCESS_CONFIRMED\n'
         and not body['unexpectedDescendants'] and not body['cleanup']['remaining'], 'actual privileged/_apt qualification or teardown missing')
    admit_small_process(process, apt_access_argv(sandbox['uid'], sandbox['gid'], work), folder, label + '-apt-access')
    need(launch['argv'] == launcher(value['request']['path'], value['request']['sha256'], request['timeoutSeconds'], request['environment'])
         and launch['cwd'] == str(folder) and launch['environment'] == request['environment']
         and type(launch['pid']) is int and launch['pid'] > 0 and launch['timeoutSeconds'] == request['timeoutSeconds']
         and launch['returned'] is True and type(launch['returncode']) is int and launch['returncode'] == 0
         and not launch['interrupted'] and 0 <= launch['elapsedSeconds'] <= request['timeoutSeconds'], 'actual privileged launcher return missing')
    tools.current_records(value); tools.current_records(body); tools.current_records(request['sources']); tools.current_records(launch)
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--request', required=True)
    parser.add_argument('--request-sha256', default='')
    args = parser.parse_args()
    try: return root_run(args.request, args.request_sha256)
    except Exception as error:
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr); return 2


if __name__ == '__main__': sys.exit(main())
