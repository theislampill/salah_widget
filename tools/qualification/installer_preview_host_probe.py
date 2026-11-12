#!/usr/bin/env python3
"""New R0016 source-free Windows acquisition; never evaluates installer source.

Example (native execution requires the parent's separate reviewed publication):
  python installer_preview_host_probe.py --host ps51 --powershell <absolute.exe>
      --output-parent <owned-runner-scratch>

The observer AND its children receive owned profile/TEMP/cache bindings before
their runtimes start. Default means no noGather override in the declared common
environment. NoGather is an experiment, not a claim of PowerShell 5.1 support.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

SCHEMA = 'r0016-source-free-host-acquisition.v1'
MAX_FILES = 8192
MAX_FILE_BYTES = 64 * 1024 * 1024


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


def environment_for(state, host, inherited, no_gather):
    """Construct an allowlisted environment; do not copy credentials/hooks."""
    state, host = Path(state).absolute(), Path(host).absolute()
    original = {key.upper(): value for key, value in inherited.items()}
    system = Path(original['SYSTEMROOT'])
    profile = state / 'user-profile'
    env = {
        'SystemRoot': str(system), 'WINDIR': str(system),
        'ComSpec': str(system / 'System32/cmd.exe'),
        'PATH': ';'.join(map(str, (host.parent, system / 'System32', system))),
        'USERPROFILE': str(profile), 'HOME': str(profile),
        'TEMP': str(state / 'temp'), 'TMP': str(state / 'temp'),
        'LOCALAPPDATA': str(profile / 'AppData/Local'),
        'APPDATA': str(profile / 'AppData/Roaming'),
        'PSModulePath': str(host.parent / 'Modules'),
        'PSModuleAnalysisCachePath': str(state / 'host-cache/module-analysis-cache'),
        'DOTNET_CLI_HOME': str(state / 'host-cache/dotnet'),
        'POWERSHELL_TELEMETRY_OPTOUT': '1', 'DOTNET_CLI_TELEMETRY_OPTOUT': '1',
        'DOTNET_SKIP_FIRST_TIME_EXPERIENCE': '1', 'DOTNET_EnableDiagnostics': '0',
    }
    if 'SYSTEMDRIVE' in original:
        env['SystemDrive'] = original['SYSTEMDRIVE']
    if no_gather:
        env['COMPlus_MultiCoreJitNoProfileGather'] = '1'
    return env


def prepare_environment(env):
    for key in ('USERPROFILE', 'TEMP', 'LOCALAPPDATA', 'APPDATA', 'DOTNET_CLI_HOME'):
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    Path(env['PSModuleAnalysisCachePath']).parent.mkdir(parents=True, exist_ok=True)
    (Path(env['USERPROFILE']) / 'existing-sentinel.bin').write_bytes(b'R0016 source-free owned sentinel\n')


def native_sddl(path):
    import ctypes as c
    from ctypes import wintypes as w
    adv, kernel = c.WinDLL('advapi32', use_last_error=True), c.WinDLL('kernel32', use_last_error=True)
    adv.GetNamedSecurityInfoW.argtypes = [w.LPWSTR, w.DWORD, w.DWORD, c.c_void_p, c.c_void_p, c.c_void_p, c.c_void_p, c.POINTER(c.c_void_p)]
    adv.GetNamedSecurityInfoW.restype = w.DWORD
    adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [c.c_void_p, w.DWORD, w.DWORD, c.POINTER(w.LPWSTR), c.c_void_p]
    adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype = w.BOOL
    kernel.LocalFree.argtypes = [c.c_void_p]
    kernel.LocalFree.restype = c.c_void_p
    descriptor, text = c.c_void_p(), w.LPWSTR()
    code = adv.GetNamedSecurityInfoW(str(path), 1, 7, None, None, None, None, c.byref(descriptor))
    if code:
        raise OSError(code, 'GetNamedSecurityInfoW failed', str(path))
    try:
        if not adv.ConvertSecurityDescriptorToStringSecurityDescriptorW(descriptor, 1, 7, c.byref(text), None):
            raise c.WinError(c.get_last_error())
        return text.value
    finally:
        if text:
            kernel.LocalFree(c.cast(text, c.c_void_p))
        kernel.LocalFree(descriptor)


def _inventory_pass(root):
    """One bounded enumeration; not an atomic filesystem observation."""
    root = Path(root)
    started = utc()
    pending, rows = [root], []
    while pending:
        path = pending.pop()
        before = path.lstat()
        if path.is_symlink() or getattr(before, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Snapshot refuses reparse entry: ' + str(path))
        directory = stat.S_ISDIR(before.st_mode)
        if not directory and not stat.S_ISREG(before.st_mode):
            raise ValueError('Snapshot refuses special entry: ' + str(path))
        row = dict(path=path.relative_to(root).as_posix(), kind='directory' if directory else 'file',
                   attributes=getattr(before, 'st_file_attributes', None),
                   mtimeUtcTicks=str(before.st_mtime_ns // 100 + 621355968000000000),
                   sddl=native_sddl(path), bytes=None, sha256=None)
        if directory:
            pending.extend(sorted(path.iterdir(), reverse=True))
        else:
            if before.st_size > MAX_FILE_BYTES:
                raise ValueError('Snapshot file byte bound exceeded: ' + str(path))
            raw = path.read_bytes()
            row.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            after = path.lstat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                raise ValueError('File changed while observed: ' + str(path))
        rows.append(row)
        if len(rows) > MAX_FILES:
            raise ValueError('Snapshot entry bound exceeded')
    return dict(schema='r0016-inventory-pass.v1', root=str(root), startedUtc=started,
                completedUtc=utc(), complete=True,
                rows=sorted(rows, key=lambda row: row['path']))


def snapshot(root):
    """Require agreement of two full inventories; no atomicity is claimed."""
    passes = [_inventory_pass(root), _inventory_pass(root)]
    agree = passes[0]['rows'] == passes[1]['rows']
    return dict(schema='r0016-double-inventory.v2', root=str(Path(root)),
                startedUtc=passes[0]['startedUtc'], completedUtc=passes[1]['completedUtc'],
                complete=agree, passesAgree=agree, passes=passes, rows=passes[1]['rows'],
                error=None if agree else 'Consecutive complete inventories differ',
                scope='Two consecutive full inventories compared exactly; a bounded stability check, not an atomic filesystem snapshot. Both passes are retained; no exclusions or retries.')


def save_required_snapshot(root, output):
    value = snapshot(root)
    save(output, value)
    if not value['complete']:
        raise ValueError('Required inventory acquisition is incomplete: ' + str(output))
    return value


def run_observer(command, env, root, timeout):
    """Create suspended -> assign kill-on-close job -> resume; direct files."""
    import ctypes as c
    from ctypes import wintypes as w
    import _winapi
    import msvcrt

    class Limits(c.Structure):
        _fields_ = [('process_time', c.c_longlong), ('job_time', c.c_longlong), ('flags', w.DWORD),
                    ('min_working', c.c_size_t), ('max_working', c.c_size_t), ('active_limit', w.DWORD),
                    ('affinity', c.c_size_t), ('priority', w.DWORD), ('scheduling', w.DWORD)]

    class Extended(c.Structure):
        _fields_ = [('basic', Limits), ('io', c.c_ulonglong * 6), ('process_memory', c.c_size_t),
                    ('job_memory', c.c_size_t), ('peak_process_memory', c.c_size_t), ('peak_job_memory', c.c_size_t)]

    kernel = c.WinDLL('kernel32', use_last_error=True)
    for name, args, result in (
        ('CreateJobObjectW', [c.c_void_p, w.LPCWSTR], w.HANDLE),
        ('SetInformationJobObject', [w.HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL),
        ('AssignProcessToJobObject', [w.HANDLE, w.HANDLE], w.BOOL),
        ('TerminateJobObject', [w.HANDLE, w.UINT], w.BOOL),
        ('ResumeThread', [w.HANDLE], w.DWORD), ('CloseHandle', [w.HANDLE], w.BOOL)):
        function = getattr(kernel, name)
        function.argtypes, function.restype = args, result
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise c.WinError(c.get_last_error())
    limits = Extended()
    limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
    process = thread = None
    receipt = dict(command=command, startedUtc=utc(), timeoutSeconds=timeout, processId=None,
                   jobAssignedBeforeResume=False, timedOut=False, exit=None,
                   capture='direct files; no redirected pipe drain', drain='not applicable',
                   jobClosedKillOnClose=False, error=None)
    try:
        if not kernel.SetInformationJobObject(job, 9, c.byref(limits), c.sizeof(limits)):
            raise c.WinError(c.get_last_error())
        with open(os.devnull, 'rb') as stdin, (root / 'observer.stdout.raw').open('xb') as stdout, (root / 'observer.stderr.raw').open('xb') as stderr:
            handles = [msvcrt.get_osfhandle(stream.fileno()) for stream in (stdin, stdout, stderr)]
            for handle in handles:
                os.set_handle_inheritable(handle, True)
            startup = subprocess.STARTUPINFO()
            startup.dwFlags = subprocess.STARTF_USESTDHANDLES
            startup.hStdInput, startup.hStdOutput, startup.hStdError = handles
            startup.lpAttributeList = {'handle_list': handles}
            try:
                process, thread, pid, tid = _winapi.CreateProcess(command[0], subprocess.list2cmdline(command),
                    None, None, True, 0x4 | 0x400 | 0x08000000, env, str(root), startup)
            finally:
                for handle in handles:
                    os.set_handle_inheritable(handle, False)
            receipt.update(processId=pid, threadId=tid, createdSuspendedUtc=utc())
            if not kernel.AssignProcessToJobObject(job, int(process)):
                raise c.WinError(c.get_last_error())
            receipt['jobAssignedBeforeResume'] = True
            save(root / 'observer.launch.json', receipt)
            if kernel.ResumeThread(int(thread)) == 0xffffffff:
                raise c.WinError(c.get_last_error())
            receipt['resumedUtc'] = utc()
            started = time.monotonic()
            while _winapi.WaitForSingleObject(process, 200) != _winapi.WAIT_OBJECT_0:
                if time.monotonic() - started >= timeout:
                    receipt['timedOut'] = True
                    if not kernel.TerminateJobObject(job, 124):
                        raise c.WinError(c.get_last_error())
                    break
            terminal = _winapi.WaitForSingleObject(process, 5000) == _winapi.WAIT_OBJECT_0
            receipt.update(exitObserved=terminal, exit=_winapi.GetExitCodeProcess(process) if terminal else None,
                           exitObservedUtc=utc(), elapsedSeconds=time.monotonic() - started)
    except BaseException as error:
        receipt['error'] = type(error).__name__ + ': ' + str(error)
        if process is not None:
            try:
                _winapi.TerminateProcess(process, 125)
                receipt['failureExitObserved'] = _winapi.WaitForSingleObject(process, 5000) == _winapi.WAIT_OBJECT_0
            except OSError as stop_error:
                receipt['failureStopError'] = str(stop_error)
    finally:
        # Closing this handle kills any remaining descendants even after errors.
        receipt['jobClosedKillOnClose'] = bool(kernel.CloseHandle(job))
        if not receipt['jobClosedKillOnClose']:
            receipt['jobCloseError'] = str(c.WinError(c.get_last_error()))
            receipt['error'] = receipt['error'] or 'Job Object close failed'
        if thread is not None:
            _winapi.CloseHandle(thread)
        if process is not None:
            _winapi.CloseHandle(process)
        receipt['finishedUtc'] = utc()
        for kind in ('stdout', 'stderr'):
            path = root / ('observer.' + kind + '.raw')
            if path.is_file():
                receipt[kind] = dict(path=str(path), bytes=path.stat().st_size, sha256=digest(path))
        save(root / 'observer.process.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=('ps51', 'ps766'), required=True)
    parser.add_argument('--powershell', type=Path, required=True)
    parser.add_argument('--output-parent', type=Path, required=True)
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('Native Windows required; no portability substitute is credited')
    host, parent = args.powershell.absolute(), args.output_parent.absolute()
    if not host.is_file() or not parent.is_dir():
        parser.error('Existing native executable and output directory required')
    for path in (parent, *parent.parents, host, *host.parents):
        if path.lstat().st_file_attributes & 0x400:
            parser.error('Reparse ancestor is outside this acquisition scope: ' + str(path))
    host, parent = host.resolve(strict=True), parent.resolve(strict=True)
    source = Path(__file__).resolve()
    observer = source.with_suffix('.ps1')
    root = Path(tempfile.mkdtemp(prefix='r0016-host-probe-', dir=parent)).resolve()
    control = root / 'control'
    control.mkdir()
    frozen = control / observer.name
    shutil.copyfile(observer, frozen)
    shutil.copyfile(source, control / source.name)
    observer_state = root / 'observer-state'
    observer_env = environment_for(observer_state, host, os.environ, False)
    prepare_environment(observer_env)
    modes = []
    for mode, no_gather in (('default', False), ('no-gather', True)):
        watched = root / mode / 'watched'
        env = environment_for(watched, host, os.environ, no_gather)
        prepare_environment(env)
        (watched / 'event-control').mkdir()
        mode_control = root / mode / 'control'
        mode_control.mkdir()
        modes.append(dict(name=mode, watched=str(watched), control=str(mode_control), environment=env))
    plan = dict(schema=SCHEMA, root=str(root), preparedUtc=utc(), hostKind=args.host,
                host=dict(path=str(host), sha256=digest(host)),
                launcher=dict(path=str(source), sha256=digest(source)),
                observer=dict(path=str(frozen), sha256=digest(frozen)), observerEnvironment=observer_env,
                modes=modes, childTimeoutSeconds=60, holdMilliseconds=500,
                recorderDrainMilliseconds=1500, recorderEventLimit=4096,
                observerTimeoutSeconds=360, prelaunchTempRebinding=True,
                scope='Source-free acquisition only; observer and child TEMP/profile/cache rebound before runtime launch. No OS effect sandbox or global process trace; zero installer qualification rows.',
                allocation='Exclusive tempfile.mkdtemp; inherited per-directory ACL is recorded, not represented as a new security policy.')
    save(control / 'plan.json', plan)
    result = dict(schema=SCHEMA, fixture=str(root), status='ACQUISITION_INCOMPLETE', installerExecuted=False,
                  productQualificationRows=0, sourceUnchanged=False, planSha256=digest(control / 'plan.json'))
    print(json.dumps(dict(fixture=str(root), stage='owned environments prepared')), flush=True)
    try:
        save_required_snapshot(observer_state, root / 'observer-state.before.json')
        command = [str(host), '-NoProfile', '-File', str(frozen), '-Plan', str(control / 'plan.json')]
        process = run_observer(command, observer_env, root, plan['observerTimeoutSeconds'])
        save_required_snapshot(observer_state, root / 'observer-state.after.json')
        result['process'] = process
        result['sourceUnchanged'] = (digest(source) == plan['launcher']['sha256'] and
            digest(observer) == plan['observer']['sha256'] and digest(frozen) == plan['observer']['sha256'] and digest(host) == plan['host']['sha256'])
        summary = root / 'observer-result.json'
        if summary.is_file():
            result['observerResultSha256'] = digest(summary)
            data = json.loads(summary.read_text(encoding='utf-8-sig'))
            if process['exit'] == 0 and not process['timedOut'] and not process['error'] and result['sourceUnchanged'] and data.get('acquired') is True:
                result['status'] = 'ACQUIRED_NOT_PRODUCT_ACCEPTANCE'
    except BaseException as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
    save(root / 'result.json', result)
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'ACQUIRED_NOT_PRODUCT_ACCEPTANCE' else 2


if __name__ == '__main__':
    sys.exit(main())
