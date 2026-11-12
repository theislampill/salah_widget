"""Owned-fixture observations for the R0016 exact -File entry harness.

No installer logic. Windows-only lock/ACL observations refuse other hosts.
No profile path is exempted from equality because of its name.
"""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time


def require(value, reason):
    if not value:
        raise AssertionError(reason)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.partial')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def native_security(path=None, handle=None):
    require(os.name == 'nt', 'BLOCKED_NATIVE_HOST: Windows security readback required')
    from ctypes import wintypes as w
    advapi = ctypes.WinDLL('advapi32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    descriptor = ctypes.c_void_p()
    text = w.LPWSTR()
    length = w.ULONG()
    if handle is None:
        get = advapi.GetNamedSecurityInfoW
        get.argtypes = [w.LPWSTR, w.DWORD, w.DWORD, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        get.restype = w.DWORD
        error = get(str(path), 1, 7, None, None, None, None, ctypes.byref(descriptor))
    else:
        get = advapi.GetSecurityInfo
        get.argtypes = [w.HANDLE, w.DWORD, w.DWORD, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
        get.restype = w.DWORD
        error = get(handle, 1, 7, None, None, None, None, ctypes.byref(descriptor))
    require(error == 0, 'Native security readback failed: ' + str(error))
    convert = advapi.ConvertSecurityDescriptorToStringSecurityDescriptorW
    convert.argtypes = [ctypes.c_void_p, w.DWORD, w.DWORD, ctypes.POINTER(w.LPWSTR), ctypes.POINTER(w.ULONG)]
    convert.restype = w.BOOL
    free = kernel.LocalFree
    free.argtypes = [ctypes.c_void_p]
    free.restype = ctypes.c_void_p
    try:
        require(convert(descriptor, 1, 7, ctypes.byref(text), ctypes.byref(length)), 'Native SDDL conversion failed')
        return text.value
    finally:
        if text:
            free(ctypes.cast(text, ctypes.c_void_p))
        free(descriptor)


def profile_snapshot(root):
    """Full owned USERPROFILE inventory, including its own identity and DACL.

    Directory times are retained too. The normal-mode comparator permits only
    the observed parent mtime change from the one expressly inventoried new
    direct child; preview has no metadata exemption.
    """
    root = Path(root)
    rows = []
    for path in [root] + sorted(root.rglob('*')):
        item = path.lstat()
        require(not path.is_symlink() and not (getattr(item, 'st_file_attributes', 0) & 0x400), 'Profile snapshot refuses reparse/symlink entry: ' + str(path))
        directory = stat.S_ISDIR(item.st_mode)
        require(directory or stat.S_ISREG(item.st_mode), 'Profile snapshot refuses special entry: ' + str(path))
        row = dict(path=path.relative_to(root).as_posix(), kind='directory' if directory else 'file',
                   mode=item.st_mode, device=item.st_dev, inode=item.st_ino,
                   uid=item.st_uid, gid=item.st_gid,
                   mtimeNs=item.st_mtime_ns, ctimeNs=item.st_ctime_ns,
                   attributes=getattr(item, 'st_file_attributes', None),
                   security=native_security(path=path) if os.name == 'nt' else None)
        if not directory:
            raw = path.read_bytes()
            row.update(bytes=len(raw), sha256=digest(raw),
                       links=item.st_nlink)
            after = path.lstat()
            require((item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns) ==
                    (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
                    'Profile file changed while being observed: ' + str(path))
        rows.append(row)
    return rows


def profile_delta(before, after):
    left = {row['path']: row for row in before}
    right = {row['path']: row for row in after}
    require(len(left) == len(before) and len(right) == len(after), 'Duplicate profile snapshot path')
    return dict(added=sorted(set(right) - set(left)), removed=sorted(set(left) - set(right)),
                changed=sorted(path for path in set(left) & set(right) if left[path] != right[path]))


def assert_profile_window(before, after, retained_relative=None, expected_retained_paths=None):
    """Only the actual validated new bundle may be added in normal mode."""
    if retained_relative is None:
        require(before == after, 'USERPROFILE changed during the actual entry window')
        return
    retained = Path(retained_relative).as_posix()
    require(retained and '/' not in retained and retained not in ('.', '..'), 'Expected one direct retained bundle child')
    keep = lambda row: row['path'] != retained and not row['path'].startswith(retained + '/')
    require(all(keep(row) for row in before), 'Normal entry reused an existing retained path')
    outside_after = [dict(row) for row in after if keep(row)]
    prior_root = next(row for row in before if row['path'] == '.')
    observed_root = next(row for row in outside_after if row['path'] == '.')
    # Creating this explicitly validated direct child can change HOME's mtime.
    # Keep the raw value in the receipt; no identity, ACL, creation-time or
    # existing descendant change is exempted.
    if 'mtimeNs' in prior_root:
        observed_root['mtimeNs'] = prior_root['mtimeNs']
    require(before == outside_after, 'USERPROFILE changed outside the one validated new bundle')
    expected = set(expected_retained_paths or ())
    actual = {row['path'] for row in after if not keep(row)}
    require(expected and actual == expected, 'Retained bundle inventory contains an unexpected or missing entry')


class NativeReadLock:
    """Exclusive readable handle: bytes stay observable while other opens fail."""
    def __init__(self, path, owned_root):
        require(os.name == 'nt', 'BLOCKED_NATIVE_HOST: Windows share-mode observation required')
        from ctypes import wintypes as w
        self.path = Path(path).resolve(strict=True)
        owned_root = Path(owned_root).resolve(strict=True)
        require(self.path.is_relative_to(owned_root), 'Read lock escaped owned fixture')
        for component in [self.path] + list(self.path.parents):
            if not component.is_relative_to(owned_root) and component != owned_root:
                break
            info = component.lstat()
            require(not (getattr(info, 'st_file_attributes', 0) & 0x400) and not component.is_symlink(), 'Read lock refuses a reparse ancestor')
        self.path_stat = self.path.stat()
        require(stat.S_ISREG(self.path_stat.st_mode), 'Read lock requires a regular owned file')
        self.original_bytes = self.path.read_bytes()
        require(len(self.original_bytes) <= 1024 * 1024, 'Metadata fixture exceeds bounded read size')
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create = self.kernel.CreateFileW
        create.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, ctypes.c_void_p, w.DWORD, w.DWORD, w.HANDLE]
        create.restype = w.HANDLE
        self.handle = None
        class FileTime(ctypes.Structure):
            _fields_ = [('low', w.DWORD), ('high', w.DWORD)]
        class Information(ctypes.Structure):
            _fields_ = [('attributes', w.DWORD), ('created', FileTime), ('accessed', FileTime),
                        ('written', FileTime), ('volume', w.DWORD), ('sizeHigh', w.DWORD),
                        ('sizeLow', w.DWORD), ('links', w.DWORD), ('indexHigh', w.DWORD), ('indexLow', w.DWORD)]
        self.Information = Information
        require(ctypes.sizeof(Information) == 52, 'Unsupported native file-information layout')
        self.kernel.GetFileInformationByHandle.argtypes = [w.HANDLE, ctypes.POINTER(Information)]
        self.kernel.GetFileInformationByHandle.restype = w.BOOL
        self.kernel.SetFilePointerEx.argtypes = [w.HANDLE, ctypes.c_longlong, ctypes.POINTER(ctypes.c_longlong), w.DWORD]
        self.kernel.SetFilePointerEx.restype = w.BOOL
        self.kernel.ReadFile.argtypes = [w.HANDLE, ctypes.c_void_p, w.DWORD, ctypes.POINTER(w.DWORD), ctypes.c_void_p]
        self.kernel.ReadFile.restype = w.BOOL
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.kernel.CloseHandle.restype = w.BOOL
        # GENERIC_READ|READ_CONTROL; no sharing; OPEN_EXISTING; OPEN_REPARSE_POINT.
        handle = create(str(self.path), 0x80020000, 0, None, 3, 0x00200000, None)
        require(handle not in (None, ctypes.c_void_p(-1).value), 'Exclusive file acquisition failed: ' + str(ctypes.get_last_error()))
        self.handle = handle
        try:
            self.initial = self.observe()
            require(self.initial['sha256'] == digest(self.original_bytes), 'Acquired handle bytes differ from fixture bytes')
        except BaseException:
            self.close_after_failure()
            raise

    def observe(self):
        from ctypes import wintypes as w
        info = self.Information()
        require(self.handle is not None and self.kernel.GetFileInformationByHandle(self.handle, ctypes.byref(info)), 'Held metadata identity read failed')
        size = (info.sizeHigh << 32) | info.sizeLow
        require(size <= 1024 * 1024 and info.links == 1 and not (info.attributes & 0x410), 'Held metadata is not the bounded regular single-link fixture')
        position = ctypes.c_longlong()
        require(self.kernel.SetFilePointerEx(self.handle, 0, ctypes.byref(position), 0), 'Held metadata rewind failed')
        buffer = ctypes.create_string_buffer(max(1, size))
        count = w.DWORD()
        require(self.kernel.ReadFile(self.handle, buffer, size, ctypes.byref(count), None) and count.value == size, 'Held metadata byte read failed')
        raw = buffer.raw[:count.value]
        return dict(path=str(self.path), volume=info.volume, indexHigh=info.indexHigh,
                    indexLow=info.indexLow, bytes=len(raw), sha256=digest(raw),
                    attributes=info.attributes, links=info.links,
                    created=[info.created.high, info.created.low],
                    written=[info.written.high, info.written.low],
                    security=native_security(handle=self.handle))

    def snapshot_row(self, relative):
        observation = self.observe()
        require(observation == self.initial, 'Unreadable metadata changed while held')
        return (str(relative), self.path_stat.st_mode, observation['sha256'])

    def restore(self):
        before_close = self.observe()
        require(before_close == self.initial, 'Unreadable fixture drift before restoration')
        require(self.kernel.CloseHandle(self.handle), 'Exclusive fixture handle close failed')
        self.handle = None
        restored = self.path.read_bytes()
        info = self.path.stat()
        require(restored == self.original_bytes and (info.st_dev, info.st_ino) == (self.path_stat.st_dev, self.path_stat.st_ino), 'Original fixture readability/bytes/identity not restored')
        require(native_security(path=self.path) == self.initial['security'], 'Fixture security changed while locked')
        return dict(before=self.initial, heldAfter=before_close, restoredSha256=digest(restored),
                    restoredIdentity=[info.st_dev, info.st_ino], restored=True,
                    scope='Actual Windows handle share refusal; no ACL mutation; bytes observed through the own held handle.')

    def close_after_failure(self):
        if self.handle is not None:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def invoke_with_profile_boundary(command, env, control, home, timeout):
    """Exact command, fresh PID/nonce handshake, and unfiltered profile states."""
    control = Path(control)
    control.mkdir(exist_ok=True)
    before = profile_snapshot(home)
    save(control / 'profile-before-launch.json', before)
    ready_path = Path(env['INSTALL_READY_FILE'])
    ack_path = Path(env['INSTALL_PROFILE_ACK'])
    stdout_path, stderr_path = control / 'stdout.raw', control / 'stderr.raw'
    started = time.monotonic()
    at_ready = None
    error = None
    with stdout_path.open('wb') as stdout_file, stderr_path.open('wb') as stderr_file:
        process = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL, stdout=stdout_file, stderr=stderr_file)
        env['INSTALL_EXPECTED_PID'] = str(process.pid)
        expected = str(process.pid) + '\t' + env['INSTALL_READY_NONCE']
        try:
            while process.poll() is None:
                if at_ready is None and ready_path.is_file() and ready_path.read_text(encoding='utf-8-sig') == expected:
                    at_ready = profile_snapshot(home)
                    save(control / 'profile-at-ready.json', at_ready)
                    temporary = ack_path.with_name(ack_path.name + '.partial')
                    temporary.write_text(expected, encoding='utf-8')
                    temporary.replace(ack_path)
                if time.monotonic() - started > timeout:
                    raise subprocess.TimeoutExpired(command, timeout)
                time.sleep(0.02)
        except BaseException as problem:
            error = problem
            process.kill()
        finally:
            process.wait(timeout=10)
    stdout, stderr = stdout_path.read_bytes(), stderr_path.read_bytes()
    after = profile_snapshot(home)
    receipt = dict(command=command, pid=process.pid, nonce=env['INSTALL_READY_NONCE'],
                   entryExit=process.returncode, ready=at_ready is not None,
                   before=before, atReady=at_ready, after=after,
                   startupDelta=profile_delta(before, at_ready) if at_ready is not None else None,
                   entryDelta=profile_delta(at_ready, after) if at_ready is not None else None,
                   fullDelta=profile_delta(before, after), elapsedSeconds=time.monotonic()-started,
                   timeoutSeconds=timeout, stdoutSha256=digest(stdout), stderrSha256=digest(stderr),
                   error=str(error) if error else None)
    save(control / 'profile-after-exit.json', after)
    save(control / 'profile-window.json', receipt)
    if error is not None:
        if isinstance(error, subprocess.TimeoutExpired):
            error.stdout, error.stderr = stdout, stderr
        raise error
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr), receipt
