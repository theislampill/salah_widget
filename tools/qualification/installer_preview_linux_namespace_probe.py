#!/usr/bin/env python3
"""Two source-free namespace controls; never installer/product acceptance.

The original generic-unshare route is compared once with packaged bwrap's own
user/net namespace route. Filesystem binds and the pinned --sandbox-child
seccomp observer are identical. No security policy is changed and neither
subject runs with host-root privilege. Exit 0 means terminal diagnostic evidence
was acquired, including any negative control outcome; exit 2 means incomplete.
"""
import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import signal
import stat
import subprocess
import sys
import time

HARNESS_SHA256 = '5a3a39906f0ff40d959cce5f985a368f01eaf92cb4a3cecdd8f39a1941327760'
PREPARATION_SHA256 = '4ddf713e6ae1a8112f0c96fd756e9dc143109dbecd3faa32afa3d1e43d4d54c4'
SUBJECT_SECONDS = 30
CLEANUP_SECONDS = 5
CAPTURE_BYTES = 1024 * 1024
ROUTES = ('original-unshare', 'packaged-bwrap')
POLICY_FILES = (
    '/proc/sys/kernel/apparmor_restrict_unprivileged_userns',
    '/proc/sys/kernel/unprivileged_userns_clone', '/proc/sys/user/max_user_namespaces',
    '/sys/module/apparmor/parameters/enabled', '/sys/kernel/security/lsm',
    '/etc/apparmor.d/bwrap', '/etc/apparmor.d/usr.bin.bwrap',
    '/etc/apparmor.d/unshare', '/etc/apparmor.d/usr.bin.unshare',
)
CONTROL = r'''import errno, hashlib, json, os, socket, sys, time
from pathlib import Path
os.umask(0o077)
spec = json.loads(Path(sys.argv[1]).read_text())
case = Path(spec['case'])
def emit(path, value):
    temporary = path.with_suffix('.partial')
    temporary.write_text(json.dumps(value, sort_keys=True) + '\n')
    temporary.replace(path)
def read(path):
    try: return {'text': Path(path).read_text()}
    except OSError as error: return {'error': str(error), 'errno': error.errno}
def identity():
    return {'pid': os.getpid(), 'ppid': os.getppid(), 'uid': os.getuid(),
            'euid': os.geteuid(), 'gid': os.getgid(), 'egid': os.getegid(),
            'groups': os.getgroups(), 'pgid': os.getpgrp(), 'sid': os.getsid(0),
            'namespaceIds': {n: os.readlink('/proc/self/ns/' + n) for n in ('user','net','mnt','pid')},
            'status': read('/proc/self/status'), 'uidMap': read('/proc/self/uid_map'),
            'gidMap': read('/proc/self/gid_map'), 'profile': read('/proc/self/attr/current')}
result = {'schema': 'r0016-namespace-control.v1', 'nonce': spec['nonce'], 'complete': False}
try:
    ready = {'nonce': spec['nonce'], 'identity': identity(), 'phase': 'pre-effect-ready',
             'monotonicNs': time.monotonic_ns()}
    emit(case / 'ready.json', ready)
    while not (case / 'go.json').exists():
        if time.monotonic_ns() >= spec['deadlineMonotonicNs']:
            raise TimeoutError('owned readiness release did not arrive by the subject deadline')
        time.sleep(0.01)
    if json.loads((case / 'go.json').read_text()) != {'nonce': spec['nonce']}:
        raise RuntimeError('readiness release identity differs')
    result['identity'] = identity()
    owned = case / 'allowed-write.txt'
    owned.write_bytes(spec['nonce'].encode('ascii'))
    result['ownedWrite'] = {'path': str(owned), 'bytes': owned.stat().st_size,
                            'sha256': hashlib.sha256(owned.read_bytes()).hexdigest()}
    result['outsideWrites'] = []
    for name in ('new-file', 'sentinel'):
        path = Path(spec['outside']) / name
        try:
            path.write_bytes(b'contained-control-write')
            row = {'name': name, 'denied': False, 'errno': None}
        except OSError as error:
            row = {'name': name, 'denied': error.errno in (errno.EROFS, errno.EACCES, errno.EPERM), 'errno': error.errno}
        result['outsideWrites'].append(row)
    result['transports'] = []
    for name, kind in (('TCP', socket.SOCK_STREAM), ('UDP', socket.SOCK_DGRAM)):
        channel = None
        stage = 'socket'
        try:
            channel = socket.socket(socket.AF_INET, kind)
            channel.settimeout(1)
            stage = 'connect' if name == 'TCP' else 'sendto'
            if name == 'TCP': channel.connect(('127.0.0.1', 9))
            else: channel.sendto(b'owned-namespace-control', ('127.0.0.1', 9))
            row = {'transport': name, 'denied': False, 'errno': None, 'stage': stage}
        except OSError as error:
            row = {'transport': name, 'denied': error.errno in (errno.EPERM, errno.EACCES),
                   'errno': error.errno, 'stage': stage}
        finally:
            if channel is not None: channel.close()
        result['transports'].append(row)
    result['complete'] = True
except BaseException as error:
    result['error'] = {'type': type(error).__name__, 'message': str(error)}
result['finishedMonotonicNs'] = time.monotonic_ns()
emit(case / 'control-result.json', result)
print(json.dumps(result, sort_keys=True), flush=True)
raise SystemExit(0 if result['complete'] else 70)
'''


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def binding(path):
    raw = path.read_bytes()
    info = path.stat()
    return {'path': str(path), 'physical': str(path.resolve()), 'sha256': digest(raw),
            'bytes': len(raw), 'uid': info.st_uid, 'gid': info.st_gid,
            'mode': stat.S_IMODE(info.st_mode), 'device': info.st_dev, 'inode': info.st_ino}


def fact(path):
    try:
        with Path(path).open('rb') as stream:
            raw = stream.read(128 * 1024 + 1)
        if len(raw) > 128 * 1024:
            return {'path': str(path), 'error': 'read-only fact exceeds bounded capture size'}
        return {'path': str(path), 'bytes': len(raw), 'sha256': digest(raw), 'text': raw.decode('utf-8')}
    except (OSError, UnicodeError) as error:
        return {'path': str(path), 'error': str(error), 'errno': getattr(error, 'errno', None)}


def proc_identity(pid, full=True):
    base = Path('/proc') / str(pid)
    raw = (base / 'stat').read_text()
    tail = raw.rsplit(')', 1)[1].split()
    result = {'pid': pid, 'ppid': int(tail[1]), 'pgid': int(tail[2]), 'sid': int(tail[3]),
              'state': tail[0], 'startTicks': int(tail[19]), 'statRaw': raw}
    if full:
        result.update(namespaceIds={name: os.readlink(base / 'ns' / name) for name in ('user', 'net', 'mnt', 'pid')},
                      status=fact(base / 'status'), uidMap=fact(base / 'uid_map'),
                      gidMap=fact(base / 'gid_map'), profile=fact(base / 'attr/current'),
                      executable=os.readlink(base / 'exe'), commandLine=fact(base / 'cmdline'))
    return result


def children(pid):
    result = set()
    for thread in (Path('/proc') / str(pid) / 'task').iterdir():
        try:
            result.update(int(p) for p in (thread / 'children').read_text().split())
        except FileNotFoundError:
            continue
    return sorted(result)


def status_fields(record):
    return dict(line.split(':', 1) for line in record['status'].get('text', '').splitlines() if ':' in line)


def inventory(root):
    """Two full equal inventories establish bounded stability, never atomicity."""
    def once():
        rows, errors = [], []
        try:
            pending = [root]
            while pending:
                path = pending.pop()
                before = path.lstat()
                row = {'name': str(path.relative_to(root)), 'mode': before.st_mode,
                       'uid': before.st_uid, 'gid': before.st_gid, 'device': before.st_dev,
                       'inode': before.st_ino, 'nlink': before.st_nlink,
                       'mtimeNs': before.st_mtime_ns, 'ctimeNs': before.st_ctime_ns,
                       'size': before.st_size}
                if stat.S_ISDIR(before.st_mode):
                    pending.extend(sorted(path.iterdir(), reverse=True))
                    row['kind'] = 'directory'
                elif stat.S_ISREG(before.st_mode):
                    row.update(kind='regular', sha256=digest(path.read_bytes()))
                else:
                    raise RuntimeError('Unexpected negative-control entry type: ' + str(path))
                after = path.lstat()
                stable = ('st_mode', 'st_uid', 'st_gid', 'st_dev', 'st_ino', 'st_nlink',
                          'st_mtime_ns', 'st_ctime_ns', 'st_size')
                if any(getattr(before, key) != getattr(after, key) for key in stable):
                    raise RuntimeError('Entry changed during inventory: ' + str(path))
                rows.append(row)
        except (OSError, RuntimeError) as error:
            errors.append(str(error))
        return {'rows': sorted(rows, key=lambda r: r['name']), 'errors': errors}
    passes = [once(), once()]
    return {'scope': 'two-pass-bounded-stability-not-atomic', 'passes': passes,
            'complete': not any(p['errors'] for p in passes) and passes[0]['rows'] == passes[1]['rows']}


def enable_subreaper():
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'PR_SET_CHILD_SUBREAPER failed')
    current = ctypes.c_int()
    if libc.prctl(37, ctypes.byref(current), 0, 0, 0) != 0 or current.value != 1:
        raise RuntimeError('Process-local child-subreaper status is not confirmed')
    return {'processLocal': True, 'confirmed': 1, 'controllerPid': os.getpid()}


def cleanup(process, deadline):
    """Freeze and kill only pidfd-bound descendants of this dedicated subreaper."""
    record = {'complete': False, 'signals': [], 'reapedAdopted': [], 'errors': []}
    handles = {}
    def freeze(pid, expected_parent):
        if time.monotonic() >= deadline:
            raise TimeoutError('owned cleanup deadline reached')
        before = proc_identity(pid, full=False)
        if before['ppid'] != expected_parent:
            return  # Reparenting is reacquired from our own children next pass.
        fd = os.pidfd_open(pid)
        try:
            after = proc_identity(pid, full=False)
        except BaseException:
            os.close(fd)
            raise
        if (after['startTicks'], after['ppid']) != (before['startTicks'], expected_parent):
            os.close(fd)
            return
        handles[fd] = after
        signal.pidfd_send_signal(fd, signal.SIGSTOP)
        record['signals'].append({'identity': after, 'signal': 'SIGSTOP'})
        while time.monotonic() < deadline:
            state = proc_identity(pid, full=False)['state']
            if state in ('T', 't', 'Z', 'X'):
                break
            time.sleep(0.005)
        else:
            raise TimeoutError('owned process did not stop before cleanup deadline')
        for child in children(pid):
            freeze(child, pid)
    try:
        while time.monotonic() < deadline:
            process.poll()  # Reaps only the direct Popen child.
            direct = children(os.getpid())
            if not direct:
                record['complete'] = process.returncode is not None
                break
            for pid in direct:
                try:
                    freeze(pid, os.getpid())
                except (ProcessLookupError, FileNotFoundError):
                    continue
            for fd, identity in reversed(list(handles.items())):
                try:
                    signal.pidfd_send_signal(fd, signal.SIGKILL)
                    record['signals'].append({'identity': identity, 'signal': 'SIGKILL'})
                except ProcessLookupError:
                    pass
                finally:
                    os.close(fd)
                    del handles[fd]
            process.poll()
            for pid in children(os.getpid()):
                if pid == process.pid:
                    continue
                try:
                    done, wait_status = os.waitpid(pid, os.WNOHANG)
                    if done:
                        record['reapedAdopted'].append({'pid': done, 'waitStatus': wait_status})
                except ChildProcessError:
                    pass
            time.sleep(0.01)
    except BaseException as error:
        record['errors'].append({'type': type(error).__name__, 'message': str(error)})
    finally:
        for fd, identity in handles.items():
            try:
                signal.pidfd_send_signal(fd, signal.SIGKILL)
                record['signals'].append({'identity': identity, 'signal': 'SIGKILL-final'})
            except ProcessLookupError:
                pass
            except BaseException as error:
                record['errors'].append({'phase': 'final-kill', 'pid': identity['pid'],
                                         'type': type(error).__name__, 'message': str(error)})
            finally:
                try:
                    os.close(fd)
                except BaseException as error:
                    record['errors'].append({'phase': 'final-close', 'pid': identity['pid'],
                                             'type': type(error).__name__, 'message': str(error)})
        try:
            process.poll()
        except BaseException as error:
            record['errors'].append({'phase': 'final-direct-wait',
                                     'type': type(error).__name__, 'message': str(error)})
        try:
            record['remainingDirectChildren'] = [proc_identity(p, full=False) for p in children(os.getpid())]
        except BaseException as error:
            record['remainingReadError'] = type(error).__name__ + ': ' + str(error)
        record['directExit'] = process.returncode
        record['complete'] = (not record['errors'] and not record.get('remainingReadError') and
                              record.get('remainingDirectChildren') == [] and process.returncode is not None)
    return record


def build_command(route, fixture, case, environment, harness, control, specification):
    if route == 'original-unshare':
        prefix = ['/usr/bin/unshare', '--user', '--map-root-user', '--net', '/usr/bin/bwrap']
    elif route == 'packaged-bwrap':
        prefix = ['/usr/bin/bwrap', '--unshare-user', '--uid', '0', '--gid', '0', '--unshare-net']
    else:
        raise ValueError('Only the two frozen namespace routes are permitted')
    common = ['--die-with-parent', '--ro-bind', '/', '/', '--bind', str(fixture), str(fixture),
              '--proc', '/proc', '--dev', '/dev', '--chdir', str(case), '--clearenv']
    for key, value in sorted(environment.items()):
        common += ['--setenv', key, value]
    command = prefix + common + ['/usr/bin/python3', str(harness), '--sandbox-child',
                                 '/usr/bin/python3', str(control), str(specification)]
    return command, common


def observe_ready(path, nonce, process):
    ready = json.loads(path.read_text())
    if ready.get('nonce') != nonce or ready.get('phase') != 'pre-effect-ready':
        raise RuntimeError('Subject readiness identity differs')
    pid = ready['identity']['pid']
    chain, seen = [], set()
    while pid != os.getpid():
        if pid <= 1 or pid in seen:
            raise RuntimeError('Readiness PID is not a descendant of this controller')
        seen.add(pid)
        row = proc_identity(pid)
        chain.append(row)
        pid = row['ppid']
    if process.pid not in seen:
        raise RuntimeError('Readiness ancestry does not include the launched process')
    if chain[0]['namespaceIds'] != ready['identity']['namespaceIds']:
        raise RuntimeError('Parent-read namespace identities differ from subject readiness')
    return {'subject': ready, 'parentReadAncestry': chain}


def assess(record, before, after, nonce, host):
    reasons = []
    if record.get('executionOutcome') != 'TERMINAL_EXIT' or record.get('returncode') != 0:
        reasons.append('Control did not exit zero naturally within the subject budget')
    if record.get('stderrNonempty'):
        reasons.append('Subject stderr is nonempty; raw negative evidence retained')
    if not record.get('cleanup', {}).get('complete') or record['cleanup'].get('signals'):
        reasons.append('Natural terminal descendant cleanup was not established')
    if not before['complete'] or not after['complete']:
        reasons.append('Outside-control snapshot acquisition is incomplete')
    elif before['passes'][1]['rows'] != after['passes'][1]['rows']:
        reasons.append('Owned outside-control state changed')
    ready = record.get('readiness', {})
    result = record.get('controlResult', {})
    identity = ready.get('subject', {}).get('identity', {})
    if result.get('nonce') != nonce or result.get('complete') is not True or record.get('stdoutEqualsControlResult') is not True:
        reasons.append('Complete nonce-bound child result and raw stdout do not reconcile')
    stable_identity = ('pid', 'ppid', 'uid', 'euid', 'gid', 'egid', 'groups', 'pgid', 'sid', 'namespaceIds')
    if not identity or any(result.get('identity', {}).get(key) != identity.get(key) for key in stable_identity):
        reasons.append('Child identity changed between pre-effect readiness and control')
    ns = identity.get('namespaceIds', {})
    if not all(ns.get(n) and ns[n] != host['namespaceIds'][n] for n in ('user', 'net', 'mnt')) or ns.get('pid') != host['namespaceIds']['pid']:
        reasons.append('Expected user/net/mount separation and original PID namespace are unproved')
    if identity.get('uid') != 0 or identity.get('euid') != 0:
        reasons.append('Mapped namespace UID0 is unproved')
    chain = ready.get('parentReadAncestry', [])
    fields = status_fields(chain[0]) if chain else {}
    uid_values = fields.get('Uid', '').split()
    if len(uid_values) != 4 or any(int(value) != os.getuid() for value in uid_values):
        reasons.append('Parent-observed subject host UID is not the unprivileged controller UID')
    if fields.get('NoNewPrivs', '').strip() != '1' or fields.get('Seccomp', '').strip() != '2':
        reasons.append('Actual no-new-privileges/seccomp state is unproved')
    if record.get('ownedWriteMatches') is not True:
        reasons.append('Allowed owned write did not match its nonce bytes')
    outside = result.get('outsideWrites', [])
    if [x.get('name') for x in outside] != ['new-file', 'sentinel'] or not all(x.get('denied') is True for x in outside):
        reasons.append('Both outside owned-sentinel writes were not denied')
    transport = result.get('transports', [])
    if [x.get('transport') for x in transport] != ['TCP', 'UDP'] or not all(x.get('denied') is True and x.get('errno') == errno.EPERM and x.get('stage') == 'socket' for x in transport):
        reasons.append('TCP and UDP socket attempts were not independently denied at the original filter boundary')
    attempts = record.get('transportAttempts')
    if not isinstance(attempts, list) or len(attempts) != 2 or not all(x.get('pid') == identity.get('pid') and x.get('syscall') == 'socket' and x.get('decision') == 'DENIED_EPERM' for x in attempts):
        reasons.append('Original observer did not retain both exact-child socket-attempt denials')
    return {'containmentControlObserved': not reasons, 'reasons': reasons, 'productRowsExecuted': 0}


def run_case(label, output, fixture, outside, harness, control, host):
    case = fixture / label
    case.mkdir(mode=0o700)
    outside.mkdir(mode=0o700)
    nonce = secrets.token_hex(16)
    (outside / 'sentinel').write_text('owned outside sentinel ' + nonce)
    before = inventory(outside)
    evidence = output / label
    evidence.mkdir(mode=0o700)
    save(evidence / 'outside-before.json', before)
    record = {'case': label, 'productRowsExecuted': 0, 'subjectSeconds': SUBJECT_SECONDS,
              'cleanupSeconds': CLEANUP_SECONDS, 'returncode': None, 'executionOutcome': 'NOT_LAUNCHED'}
    save(evidence / 'result.json', record)
    if not before['complete'] or children(os.getpid()):
        raise RuntimeError('Prelaunch acquisition or prior owned cleanup is incomplete')
    environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'HOME': str(fixture / 'home'),
                   'TMPDIR': str(fixture / 'tmp'), 'PYTHONDONTWRITEBYTECODE': '1',
                   'R0016_TRANSPORT_LOG': str(case / 'network.jsonl')}
    started = time.monotonic()
    deadline = started + SUBJECT_SECONDS
    specification = evidence / 'control-spec.json'
    save(specification, {'nonce': nonce, 'case': str(case), 'outside': str(outside),
                         'deadlineMonotonicNs': int(deadline * 1_000_000_000)})
    command, common = build_command(label, fixture, case, environment, harness, control, specification)
    record.update(command=command, commonFilesystemAndEnvironment=common, environment=environment,
                  startedMonotonicNs=int(started * 1_000_000_000), deadlineMonotonicNs=int(deadline * 1_000_000_000),
                  startNewSession=True, stdin='DEVNULL', cwd=str(case), nonce=nonce)
    save(evidence / 'launch.json', record)
    process = None
    with (evidence / 'stdout.raw').open('xb', buffering=0) as stdout, (evidence / 'stderr.raw').open('xb', buffering=0) as stderr:
        try:
            process = subprocess.Popen(command, env=environment, cwd=case, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, start_new_session=True)
            record['launchPid'] = process.pid
            record['executionOutcome'] = 'RUNNING'
            save(evidence / 'launch.json', record)
            while process.poll() is None:
                if (case / 'ready.json').exists() and 'readiness' not in record:
                    record['readiness'] = observe_ready(case / 'ready.json', nonce, process)
                    save(evidence / 'readiness.json', record['readiness'])
                    save(case / 'go.json', {'nonce': nonce})
                if max(os.fstat(stdout.fileno()).st_size, os.fstat(stderr.fileno()).st_size) > CAPTURE_BYTES:
                    raise RuntimeError('Raw subject capture exceeded bounded size; original bytes retained')
                if time.monotonic() >= deadline:
                    record['executionOutcome'] = 'TIMEOUT'
                    break
                time.sleep(0.01)
            if process.returncode is not None:
                observed = time.monotonic()
                record['terminalObservedMonotonicNs'] = int(observed * 1_000_000_000)
                record['executionOutcome'] = ('TERMINAL_EXIT' if observed <= deadline
                                              else 'LATE_TERMINAL_EXIT')
        except BaseException as error:
            record['error'] = {'type': type(error).__name__, 'message': str(error)}
            if record['executionOutcome'] == 'RUNNING':
                record['executionOutcome'] = 'CONTROLLER_ERROR'
        finally:
            if process is not None:
                record['cleanup'] = cleanup(process, min(time.monotonic() + CLEANUP_SECONDS, deadline + CLEANUP_SECONDS))
                record['returncode'] = process.returncode
            else:
                record['cleanup'] = {'complete': children(os.getpid()) == [], 'signals': [], 'notLaunched': True}
    record['elapsedSeconds'] = time.monotonic() - started
    record['captures'] = {n: binding(evidence / n) for n in ('stdout.raw', 'stderr.raw')}
    record['capturesStable'] = record['cleanup']['complete']
    record['stderrNonempty'] = record['captures']['stderr.raw']['bytes'] != 0
    record['captureBudgetExceeded'] = any(row['bytes'] > CAPTURE_BYTES for row in record['captures'].values())
    record['acquisitionComplete'] = (process is not None and record['returncode'] is not None and
                                     record['cleanup']['complete'] and not record['captureBudgetExceeded'] and
                                     'error' not in record)
    after = inventory(outside) if record['cleanup']['complete'] else {'complete': False, 'passes': [], 'reason': 'Owned process cleanup incomplete'}
    save(evidence / 'outside-after.json', after)
    try:
        if (case / 'control-result.json').exists():
            record['controlResult'] = json.loads((case / 'control-result.json').read_text())
            record['stdoutEqualsControlResult'] = json.loads((evidence / 'stdout.raw').read_text()) == record['controlResult']
        record['ownedWriteMatches'] = (case / 'allowed-write.txt').is_file() and (case / 'allowed-write.txt').read_bytes() == nonce.encode('ascii')
        record['transportAttempts'] = ([json.loads(line) for line in (case / 'network.jsonl').read_text().splitlines()]
                                       if (case / 'network.jsonl').exists() else None)
        record['oracle'] = assess(record, before, after, nonce, host)
    except (OSError, ValueError, TypeError, KeyError) as error:
        record['acquisitionComplete'] = False
        record['parseError'] = {'type': type(error).__name__, 'message': str(error)}
    record['acquisitionComplete'] = record['acquisitionComplete'] and before['complete'] and after['complete']
    record['classification'] = ('CONTAINMENT_CONTROL_OBSERVED' if record['acquisitionComplete'] and record.get('oracle', {}).get('containmentControlObserved') else
                                'DIAGNOSTIC_FAILURE_OBSERVED' if record['acquisitionComplete'] else 'DIAGNOSTIC_ACQUISITION_INCOMPLETE')
    save(evidence / 'result.json', record)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    repo = args.repo.resolve(strict=True)
    output = args.output.parent.resolve(strict=True) / args.output.name
    if output == repo or repo in output.parents:
        parser.error('Diagnostic output must be outside the repository')
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    result = {'schema': 'r0016-linux-namespace-diagnostic.v1', 'classification': 'DIAGNOSTIC_ACQUISITION_INCOMPLETE',
              'scope': 'Two fixed source-free namespace controls; no product acceptance or host-policy modification',
              'productRowsExecuted': 0, 'cases': [], 'probe': binding(Path(__file__).resolve())}
    save(output / 'result.json', result)
    def interrupted(signum, frame):
        raise InterruptedError('Controller received signal ' + str(signum))
    signal.signal(signal.SIGTERM, interrupted)
    try:
        if platform.system() != 'Linux' or platform.machine() != 'x86_64' or os.getuid() == 0 or os.getuid() != os.geteuid():
            raise RuntimeError('Native unprivileged Linux x86_64 controller required')
        if not hasattr(os, 'pidfd_open') or not hasattr(signal, 'pidfd_send_signal'):
            raise RuntimeError('Identity-bound pidfd cleanup support required')
        os.umask(0o077)
        head = (repo / '.git/HEAD').read_text().strip()
        if not re.fullmatch('[0-9a-f]{40}', head) or head != os.environ.get('GITHUB_SHA'):
            raise RuntimeError('Exact detached workflow checkout identity required')
        result['commit'] = head
        result['host'] = {'platform': platform.platform(), 'uid': os.getuid(), 'gid': os.getgid(),
                          'python': sys.version, 'controller': proc_identity(os.getpid()),
                          'policyFacts': [fact(p) for p in POLICY_FILES]}
        helper = repo / 'tools/qualification/installer_preview_linux_prerequisites.py'
        source = repo / 'tests/install-preview.py'
        source_raw = source.read_bytes()
        if digest(helper.read_bytes()) != PREPARATION_SHA256 or digest(source_raw) != HARNESS_SHA256:
            raise RuntimeError('Pinned original observer or reviewed prerequisite helper differs')
        result['sourceBindings'] = {'observerHarness': binding(source), 'preparationHelper': binding(helper)}
        prep = args.preparation.resolve(strict=True)
        preparation = json.loads((prep / 'result.json').read_text())
        if preparation.get('complete') is not True or any(c.get('exit') != 0 or c.get('timedOut') is not False for c in preparation['commands']):
            raise RuntimeError('Reviewed signed prerequisite acquisition is not complete')
        result['preparationReceipt'] = binding(prep / 'result.json')
        result['executables'] = {name: binding(Path('/usr/bin') / name) for name in ('bwrap', 'unshare', 'python3')}
        if any(item['uid'] != 0 or item['mode'] & 0o022 for item in result['executables'].values()):
            raise RuntimeError('Selected system executables must be root-owned and not writable by group/others')
        for name in ('bwrap', 'unshare'):
            item = result['executables'][name]
            if item['mode'] & (stat.S_ISUID | stat.S_ISGID):
                raise RuntimeError('Set-ID launcher forbidden for this host-unprivileged comparison')
            if preparation['tools'][name]['sha256'] != item['sha256'] or preparation['tools'][name]['path'] != item['path']:
                raise RuntimeError('Packaged prerequisite executable identity changed')
        frozen = output / 'frozen'
        frozen.mkdir(mode=0o700)
        harness = frozen / 'install-preview.py'
        harness.write_bytes(source_raw)
        control = frozen / 'namespace-control.py'
        control.write_text(CONTROL)
        result['frozen'] = {'observer': binding(harness), 'control': binding(control)}
        result['subreaper'] = enable_subreaper()
        if children(os.getpid()):
            raise RuntimeError('Dedicated diagnostic controller already has children')
        fixture = output / 'fixture'
        fixture.mkdir(mode=0o700)
        (fixture / 'home').mkdir(mode=0o700)
        (fixture / 'tmp').mkdir(mode=0o700)
        for label in ROUTES:
            observed = run_case(label, output, fixture, output / ('outside-' + label), harness, control,
                                result['host']['controller'])
            result['cases'].append(observed)
            save(output / 'result.json', result)
            if not observed['acquisitionComplete'] or observed.get('error', {}).get('type') in ('KeyboardInterrupt', 'InterruptedError', 'SystemExit'):
                result['remainingCaseSuppressed'] = 'Prior acquisition/owned cleanup is incomplete or controller interrupted'
                break
        acquired = len(result['cases']) == 2 and all(c['acquisitionComplete'] for c in result['cases'])
        result['classification'] = 'NAMESPACE_DISCRIMINATOR_ACQUIRED' if acquired else 'DIAGNOSTIC_ACQUISITION_INCOMPLETE'
        result['inferenceLimit'] = 'Route-dependent success is an executable/namespace observation, not proof of a particular loaded AppArmor rule and never installer acceptance.'
    except BaseException as error:
        result['error'] = {'type': type(error).__name__, 'message': str(error)}
    save(output / 'result.json', result)
    print(json.dumps({'classification': result['classification'], 'result': str(output / 'result.json'), 'productRowsExecuted': 0}))
    return 0 if result['classification'] == 'NAMESPACE_DISCRIMINATOR_ACQUIRED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
