#!/usr/bin/env python3
"""R0015 21-05 native Linux HOME-owner proof; no product/source modifications.

Usage: python3 r0015-linux-owner-proof.py /absolute/install.sh
The supervisor may use existing passwordless sudo. It only changes ownership or
permissions of one newly-created /tmp/r0015-owner-* fixture. Every production
function executes after dropping to the isolated numeric consumer UID/GID with
no supplementary groups. No account, real home, profile, or global path changes.
Without distinct-UID capability, emit a non-passing acquisition receipt plus a
local same-UID positive. A user-namespace root with one mapped UID is insufficient.
Exit 0: native required controls PASS; 1: exercised failure; 2: acquisition/setup gap.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import traceback


"""Bounded Linux fixture export; no archive extraction or source-object changes."""
import gzip
import io
import secrets
import tarfile


_EXPORT_LIMIT = 64 * 1024 * 1024
_EXPORT_FILE_LIMIT = 16 * 1024 * 1024
_EXPORT_ENTRY_LIMIT = 4096
_EXPORT_ARCHIVE_LIMIT = 80 * 1024 * 1024
_EXPORT_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def _export_require(ok, message):
    if not ok:
        raise ValueError('Fixture export refused: ' + message)


def _export_meta(info):
    return dict(device=info.st_dev, inode=info.st_ino, uid=info.st_uid,
                gid=info.st_gid, mode=stat.S_IMODE(info.st_mode),
                native_type=stat.S_IFMT(info.st_mode), links=info.st_nlink,
                size=info.st_size, mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns)


def _export_token(info):
    value = _export_meta(info) if not isinstance(info, dict) else info
    return {key: value[key] for key in ('device', 'inode', 'uid', 'gid', 'mode', 'native_type')}


def _export_json(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':')) + '\n').encode('utf-8')


def _export_read_fd(fd, limit):
    before = _export_meta(os.fstat(fd))
    _export_require(before['native_type'] == stat.S_IFREG and before['links'] == 1,
                    'readback object is not a singly linked regular file')
    _export_require(0 <= before['size'] <= limit, 'regular file exceeds export bound')
    data = bytearray()
    while len(data) <= limit:
        part = os.read(fd, min(1024 * 1024, limit + 1 - len(data)))
        if not part:
            break
        data.extend(part)
    _export_require(len(data) == before['size'] and len(data) <= limit, 'file length changed during readback')
    _export_require(_export_meta(os.fstat(fd)) == before, 'file identity or metadata changed during readback')
    return bytes(data), before


def _capture_export_tree(root_fd, excluded=None):
    """Read only descriptor-relative entries; never traverse an evidence symlink."""
    rows, contents = [], {}
    root_device = os.fstat(root_fd).st_dev
    total = 0

    def visit(fd, relative, depth):
        nonlocal total
        _export_require(depth <= 64, 'directory nesting exceeds export bound')
        before = os.fstat(fd)
        _export_require(stat.S_ISDIR(before.st_mode) and before.st_dev == root_device,
                        'directory type or filesystem changed')
        rows.append(dict(path=relative, kind='directory', **_export_meta(before)))
        names = sorted(os.listdir(fd))
        if relative == '.' and excluded:
            name, token = excluded
            _export_require(name in names, 'new export directory is missing')
            observed = os.stat(name, dir_fd=fd, follow_symlinks=False)
            _export_require(_export_token(observed) == token, 'new export directory identity changed')
            names.remove(name)
        for name in names:
            _export_require(name not in ('', '.', '..') and '/' not in name and '\x00' not in name,
                            'noncanonical source member name')
            name.encode('utf-8', errors='strict')
            path = name if relative == '.' else relative + '/' + name
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            _export_require(info.st_dev == root_device, 'source member crosses a filesystem boundary')
            _export_require(len(rows) < _EXPORT_ENTRY_LIMIT, 'too many source members')
            if stat.S_ISDIR(info.st_mode):
                child = os.open(name, _EXPORT_DIR_FLAGS, dir_fd=fd)
                try:
                    _export_require(_export_meta(os.fstat(child)) == _export_meta(info), 'directory changed while opening')
                    visit(child, path, depth + 1)
                finally:
                    os.close(child)
            elif stat.S_ISREG(info.st_mode):
                _export_require(info.st_nlink == 1, 'source regular file has unbounded hard links')
                child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
                try:
                    _export_require(_export_meta(os.fstat(child)) == _export_meta(info), 'file changed while opening')
                    data, metadata = _export_read_fd(child, _EXPORT_FILE_LIMIT)
                finally:
                    os.close(child)
                total += len(data)
                _export_require(total <= _EXPORT_LIMIT, 'source bytes exceed export bound')
                rows.append(dict(path=path, kind='file', sha256=digest(data), **metadata))
                contents[path] = data
            elif stat.S_ISLNK(info.st_mode):
                target = os.readlink(name, dir_fd=fd)
                target.encode('utf-8', errors='strict')
                rows.append(dict(path=path, kind='symlink', target=target, **_export_meta(info)))
            else:
                raise ValueError('Fixture export refused: special source member ' + path)
            _export_require(_export_meta(os.stat(name, dir_fd=fd, follow_symlinks=False)) == _export_meta(info),
                            'source entry changed during capture')
        after_names = sorted(os.listdir(fd))
        if relative == '.' and excluded:
            name, token = excluded
            _export_require(name in after_names and
                            _export_token(os.stat(name, dir_fd=fd, follow_symlinks=False)) == token,
                            'new export directory was replaced during capture')
            after_names.remove(name)
        _export_require(after_names == names and _export_meta(os.fstat(fd)) == _export_meta(before),
                        'source directory changed during capture')

    visit(root_fd, '.', 0)
    return rows, contents


def _compare_export_snapshots(original, current):
    _export_require(len(original) == len(current), 'source member count changed')
    _export_require(original[0]['path'] == current[0]['path'] == '.', 'source root record missing')
    _export_require(_export_token(original[0]) == _export_token(current[0]), 'source root custody changed')
    _export_require(original[1:] == current[1:], 'original source entries changed during export')


def _verify_export_archive(data, expected_sha, manifest_sha):
    _export_require(len(data) <= _EXPORT_ARCHIVE_LIMIT and digest(data) == expected_sha, 'archive digest mismatch')
    with gzip.GzipFile(fileobj=io.BytesIO(data), mode='rb') as compressed:
        raw = compressed.read(_EXPORT_ARCHIVE_LIMIT + 1)
    _export_require(len(raw) <= _EXPORT_ARCHIVE_LIMIT, 'expanded archive exceeds export bound')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        members = archive.getmembers()
        _export_require(3 <= len(members) <= _EXPORT_ENTRY_LIMIT + 2, 'archive member count is invalid')
        by_name = {member.name: member for member in members}
        _export_require(len(by_name) == len(members), 'duplicate archive member')
        manifest_member = by_name.get('manifest.json')
        observation_member = by_name.get('observation.json')
        _export_require(manifest_member is not None and manifest_member.isreg() and
                        manifest_member.size <= 4 * 1024 * 1024, 'manifest is missing or not bounded regular data')
        manifest_bytes = archive.extractfile(manifest_member).read()
        _export_require(digest(manifest_bytes) == manifest_sha, 'manifest digest mismatch')
        manifest = json.loads(manifest_bytes)
        _export_require(manifest.get('schema') == 'r0015-owner-fixture-export/v1', 'unsupported manifest schema')
        rows = manifest.get('entries')
        _export_require(isinstance(rows, list) and 1 <= len(rows) <= _EXPORT_ENTRY_LIMIT, 'empty or invalid source manifest')
        _export_require(observation_member is not None and observation_member.isreg() and
                        observation_member.size <= 4 * 1024 * 1024, 'observation is missing or not bounded regular data')
        observation_bytes = archive.extractfile(observation_member).read()
        _export_require(digest(observation_bytes) == manifest['observation_sha256'], 'observation digest mismatch')
        observation = json.loads(observation_bytes)
        expected_names = {'manifest.json', 'observation.json'}
        source_paths = set()
        for row in rows:
            path = row['path']
            _export_require(isinstance(path, str) and path not in source_paths and
                            (path == '.' or (not path.startswith('/') and
                             all(part not in ('', '.', '..') for part in path.split('/')))),
                            'duplicate or noncanonical manifest path')
            source_paths.add(path)
            name = 'fixture' if path == '.' else 'fixture/' + path
            expected_names.add(name)
            member = by_name.get(name)
            _export_require(member is not None, 'manifest member is missing')
            _export_require((member.uid, member.gid, member.mode) == (row['uid'], row['gid'], row['mode']),
                            'archive ownership or mode differs from native manifest')
            _export_require(member.pax_headers.get('mtime') ==
                            str(row['mtime_ns'] // 1000000000) + '.' + format(row['mtime_ns'] % 1000000000, '09d'),
                            'archive timestamp differs from native manifest')
            kind = row['kind']
            if kind == 'file':
                _export_require(member.isreg() and member.size == row['size'] and member.size <= _EXPORT_FILE_LIMIT,
                                'regular member type or length differs')
                _export_require(digest(archive.extractfile(member).read()) == row['sha256'], 'regular member bytes differ')
            elif kind == 'directory':
                _export_require(member.isdir() and member.size == 0, 'directory member type differs')
            elif kind == 'symlink':
                _export_require(member.issym() and member.size == 0 and member.linkname == row['target'],
                                'symlink literal target differs')
            else:
                raise ValueError('Fixture export refused: unsupported manifest member type')
        _export_require(set(by_name) == expected_names, 'unmanifested archive member')
        _export_require(rows[0]['path'] == '.' and rows[0]['kind'] == 'directory', 'manifest root is invalid')
        _export_require(digest(_export_json(rows)) == manifest['original_snapshot_sha256'], 'source snapshot digest mismatch')
    return manifest, observation


class OwnedFixtureExport:
    """Capability captured immediately after this supervisor creates its fixture."""
    def __init__(self, root):
        self.root = Path(root)
        _export_require(self.root.is_absolute() and self.root.parent == Path('/tmp') and
                        re.fullmatch(r'r0015-owner-[A-Za-z0-9_-]+', self.root.name) is not None,
                        'input is not the exact fresh owner-fixture root')
        self.parent_fd = os.open('/tmp', _EXPORT_DIR_FLAGS)
        self.root_fd = os.open(self.root.name, _EXPORT_DIR_FLAGS, dir_fd=self.parent_fd)
        self.token = _export_token(os.fstat(self.root_fd))
        self._assert_root(self.root)

    def _assert_root(self, requested):
        _export_require(Path(requested) == self.root, 'requested root is outside the captured fixture')
        _export_require(self.token['uid'] == os.geteuid() and self.token['mode'] == 0o755,
                        'fixture root is not supervisor-owned mode0755')
        _export_require(_export_token(os.fstat(self.root_fd)) == self.token and
                        _export_token(os.stat(self.root.name, dir_fd=self.parent_fd, follow_symlinks=False)) == self.token,
                        'captured root pathname or identity changed')

    def close(self):
        os.close(self.root_fd)
        os.close(self.parent_fd)

    def export(self, requested, observation):
        self._assert_root(requested)
        _export_require(observation.get('fixture') == str(self.root), 'observation names a different fixture')
        original, contents = _capture_export_tree(self.root_fd)
        observation_bytes = _export_json(observation)
        _export_require(len(observation_bytes) <= 4 * 1024 * 1024, 'observation exceeds export bound')
        export_name = 'export-' + secrets.token_hex(16)
        old_umask = os.umask(0o022)
        try:
            os.mkdir(export_name, mode=0o755, dir_fd=self.root_fd)
        finally:
            os.umask(old_umask)
        export_fd = os.open(export_name, _EXPORT_DIR_FLAGS, dir_fd=self.root_fd)
        try:
            export_token = _export_token(os.fstat(export_fd))
            _export_require(export_token['uid'] == self.token['uid'] and export_token['mode'] == 0o755,
                            'new export directory has unexpected custody')
            current, unused = _capture_export_tree(self.root_fd, (export_name, export_token))
            _compare_export_snapshots(original, current)
            manifest = dict(schema='r0015-owner-fixture-export/v1', source_root=str(self.root),
                            entries=original, original_snapshot_sha256=digest(_export_json(original)),
                            observation_sha256=digest(observation_bytes),
                            export_addition=dict(path=export_name, identity=export_token,
                                                 root_after_allocation=current[0]),
                            scope='all original regular files, directories and literal symlinks; new exporter child excluded by native identity; no source permissions changed')
            manifest_bytes = _export_json(manifest)
            _export_require(len(manifest_bytes) <= 4 * 1024 * 1024, 'manifest exceeds export bound')
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode='w:gz', format=tarfile.PAX_FORMAT) as archive:
                for name, payload in (('manifest.json', manifest_bytes), ('observation.json', observation_bytes)):
                    member = tarfile.TarInfo(name)
                    member.uid, member.gid, member.mode = self.token['uid'], self.token['gid'], 0o644
                    member.size = len(payload)
                    archive.addfile(member, io.BytesIO(payload))
                for row in original:
                    name = 'fixture' if row['path'] == '.' else 'fixture/' + row['path']
                    member = tarfile.TarInfo(name)
                    member.uid, member.gid, member.mode = row['uid'], row['gid'], row['mode']
                    member.mtime = row['mtime_ns'] // 1000000000
                    member.pax_headers['mtime'] = str(member.mtime) + '.' + format(row['mtime_ns'] % 1000000000, '09d')
                    if row['kind'] == 'file':
                        member.size = row['size']
                        archive.addfile(member, io.BytesIO(contents[row['path']]))
                    else:
                        member.type = tarfile.DIRTYPE if row['kind'] == 'directory' else tarfile.SYMTYPE
                        if row['kind'] == 'symlink':
                            member.linkname = row['target']
                        archive.addfile(member)
            data = buffer.getvalue()
            archive_sha, manifest_sha = digest(data), digest(manifest_bytes)
            _verify_export_archive(data, archive_sha, manifest_sha)
            old_umask = os.umask(0o022)
            try:
                fd = os.open('fixture.partial', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                             0o644, dir_fd=export_fd)
            finally:
                os.umask(old_umask)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            fd = os.open('fixture.partial', os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=export_fd)
            try:
                readback, unused = _export_read_fd(fd, _EXPORT_ARCHIVE_LIMIT)
            finally:
                os.close(fd)
            _verify_export_archive(readback, archive_sha, manifest_sha)
            current, unused = _capture_export_tree(self.root_fd, (export_name, export_token))
            _compare_export_snapshots(original, current)
            self._assert_root(requested)
            # Hard-link publication refuses an existing destination; the private
            # partial link is removed immediately, leaving one regular archive.
            os.link('fixture.partial', 'fixture.tar.gz', src_dir_fd=export_fd, dst_dir_fd=export_fd,
                    follow_symlinks=False)
            os.unlink('fixture.partial', dir_fd=export_fd)
            os.fsync(export_fd)
            fd = os.open('fixture.tar.gz', os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=export_fd)
            try:
                readback, archive_identity = _export_read_fd(fd, _EXPORT_ARCHIVE_LIMIT)
            finally:
                os.close(fd)
            _verify_export_archive(readback, archive_sha, manifest_sha)
            _export_require(archive_identity['uid'] == self.token['uid'] and archive_identity['mode'] == 0o644,
                            'published archive has unexpected ownership or mode')
            return dict(schema='r0015-owner-fixture-export/v1', status='VERIFIED', source_root=str(self.root),
                        source_identity=self.token, directory=export_name, directory_identity=export_token,
                        path=str(self.root / export_name / 'fixture.tar.gz'), identity=archive_identity,
                        sha256=archive_sha, manifest_sha256=manifest_sha, original_snapshot_sha256=manifest['original_snapshot_sha256'],
                        observation_sha256=manifest['observation_sha256'], members=len(original),
                        export_addition=manifest['export_addition'])
        finally:
            os.close(export_fd)


def read_verified_fixture_export(receipt):
    """Collector API: return archive bytes and manifest, without extracting them."""
    export = receipt.get('fixture_export')
    _export_require(isinstance(export, dict) and export.get('status') == 'VERIFIED' and
                    export.get('schema') == 'r0015-owner-fixture-export/v1', 'no verified export receipt')
    root = Path(receipt['fixture'])
    _export_require(root.is_absolute() and root.parent == Path('/tmp') and
                    re.fullmatch(r'r0015-owner-[A-Za-z0-9_-]+', root.name) is not None and
                    export['source_root'] == str(root), 'export root is outside the exact reported fixture')
    name = export['directory']
    _export_require(re.fullmatch(r'export-[0-9a-f]{32}', name) is not None and
                    export['path'] == str(root / name / 'fixture.tar.gz'), 'export path is outside the exact fixture')
    parent = os.open('/tmp', _EXPORT_DIR_FLAGS)
    root_fd = export_fd = file_fd = None
    try:
        root_fd = os.open(root.name, _EXPORT_DIR_FLAGS, dir_fd=parent)
        _export_require(_export_token(os.fstat(root_fd)) == export['source_identity'], 'readback root identity changed')
        export_fd = os.open(name, _EXPORT_DIR_FLAGS, dir_fd=root_fd)
        _export_require(_export_token(os.fstat(export_fd)) == export['directory_identity'], 'readback export directory changed')
        file_fd = os.open('fixture.tar.gz', os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=export_fd)
        data, observed = _export_read_fd(file_fd, _EXPORT_ARCHIVE_LIMIT)
        _export_require(observed == export['identity'], 'readback archive identity changed')
        _export_require(_export_meta(os.stat('fixture.tar.gz', dir_fd=export_fd, follow_symlinks=False)) == observed,
                        'readback archive pathname changed')
        _export_require(_export_token(os.stat(name, dir_fd=root_fd, follow_symlinks=False)) == export['directory_identity'] and
                        _export_token(os.stat(root.name, dir_fd=parent, follow_symlinks=False)) == export['source_identity'],
                        'readback ancestor pathname changed')
        manifest, observation = _verify_export_archive(data, export['sha256'], export['manifest_sha256'])
        _export_require(manifest['source_root'] == str(root) and manifest['original_snapshot_sha256'] == export['original_snapshot_sha256'] and
                        manifest['observation_sha256'] == export['observation_sha256'] and len(manifest['entries']) == export['members'],
                        'manifest does not match the published export receipt')
        _export_require(all(key in receipt and receipt[key] == value for key, value in observation.items()),
                        'embedded original observation differs from the test receipt')
        return data, manifest
    finally:
        for fd in (file_fd, export_fd, root_fd, parent):
            if fd is not None:
                os.close(fd)



def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(path):
    p = Path(path)
    s = p.lstat()
    result = dict(path=str(p), uid=s.st_uid, gid=s.st_gid,
                  mode=oct(stat.S_IMODE(s.st_mode)), device=s.st_dev, inode=s.st_ino,
                  symlink=stat.S_ISLNK(s.st_mode), physical=str(p.resolve()))
    if stat.S_ISREG(s.st_mode):
        result.update(bytes=s.st_size, sha256=digest(p.read_bytes()))
    return result


def proc_identity():
    status = Path('/proc/self/status').read_text()
    fields = {line.split(':', 1)[0]: line.split(':', 1)[1].strip()
              for line in status.splitlines()
              if line.startswith(('Uid:', 'Gid:', 'Groups:', 'CapInh:', 'CapPrm:',
                                  'CapEff:', 'CapBnd:', 'NoNewPrivs:'))}
    return dict(uid=os.getuid(), euid=os.geteuid(), gid=os.getgid(), groups=os.getgroups(),
                proc_status=fields,
                uid_map=Path('/proc/self/uid_map').read_text(),
                gid_map=Path('/proc/self/gid_map').read_text())


def mapped(number, filename):
    return any(int(row.split()[0]) <= number < int(row.split()[0]) + int(row.split()[2])
               for row in Path('/proc/self/' + filename).read_text().splitlines())


def command(argv, **kwargs):
    r = subprocess.run(argv, capture_output=True, text=True, timeout=25, **kwargs)
    return dict(command=argv, exit=r.returncode, stdout=r.stdout, stderr=r.stderr)


def function(text, name):
    start = '^' + re.escape(name) + r'\(\) \{'
    match = re.search(start + r'[^\n]*\}\n', text, re.M)
    if not match:
        match = re.search(start + r'\n.*?^\}\n', text, re.M | re.S)
    if not match:
        raise ValueError('Missing exact production function: ' + name)
    return match.group()


def snapshot(paths):
    answer = {}
    for base in paths:
        base = Path(base)
        entries = [base] + sorted(base.rglob('*')) if base.is_dir() and not base.is_symlink() else [base]
        for path in entries:
            if path.exists() or path.is_symlink():
                answer[str(path)] = identity(path)
    return answer


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main(args):
    source_path = Path(args.SourceFile).resolve(strict=True)
    require(source_path.is_file(), 'SourceFile must be a regular file')
    source = source_path.read_bytes()
    text = source.decode('utf-8')
    names = ('need_cmd', 'err', 'warn', 'path_identity', 'trusted_parent',
             'verify_root', 'guard_owned_path', 'initialize_staging', 'cleanup_staging')
    fragments = {name: function(text, name) for name in names}
    helper = fragments['trusted_parent']
    old_guard = '[ "$owner" = "$uid" ] && [ -O "$path" ] && (( (8#$mode & 0022) == 0 ))'
    new_guard = '(( (8#$mode & 0022) == 0 ))'
    require(helper.count(old_guard) == 1, 'Terminal HOME owner guard source drift')
    mutant_helper = helper.replace(old_guard, new_guard, 1)
    library = '\n'.join(fragments.values())
    mutant_library = library.replace(helper, mutant_helper, 1)
    result = dict(schema='r0015-native-owner-proof/v1', source=str(source_path),
                  source_sha256=digest(source), fixture_sha256=digest(Path(__file__).read_bytes()),
                  native_host=dict(system=platform.system(), release=platform.release(),
                                   platform=platform.platform(), machine=platform.machine()),
                  supervisor=proc_identity(), source_functions=list(names),
                  source_fragment_sha256=digest(library.encode()),
                  mutation=dict(original_guard=old_guard, replacement=new_guard,
                                mutant_fragment_sha256=digest(mutant_library.encode()),
                                scope='Only terminal self-owner and -O conjunction removed; mode, ancestor and physical guards preserved'),
                  results=[], observations={}, limits=['Filesystem admission/lifetime fixture only; no browser installation.',
                                      'No real home/account/profile/network/clipboard modification.',
                                      'Retained fixture files intentionally left for evidence.'])
    require(platform.system() == 'Linux', 'This fixture requires actual Linux')
    subject_uid = args.consumer_uid
    subject_gid = args.consumer_gid
    privileged = (os.geteuid() == 0 and subject_uid != 0 and
                  mapped(subject_uid, 'uid_map') and mapped(subject_gid, 'gid_map'))
    result['requested_subject'] = dict(uid=subject_uid, gid=subject_gid)
    result['acquisition'] = dict(privileged_distinct_uid_available=privileged,
                               sudo=shutil.which('sudo'), elevated=args._elevated)

    # Re-execute only this bounded supervisor through existing passwordless sudo.
    # Production source is never executed by the supervisor's root identity.
    if not privileged and not args._elevated and not args.no_sudo and shutil.which('sudo'):
        probe = command([shutil.which('sudo'), '-n', 'true'])
        if probe['exit'] == 0:
            child = command([shutil.which('sudo'), '-n', '--', sys.executable,
                             str(Path(__file__).resolve()), str(source_path),
                             '--consumer-uid', str(subject_uid), '--consumer-gid', str(subject_gid),
                             '--_elevated'])
            try:
                receipt = json.loads(child['stdout'])
                receipt['sudo_acquisition'] = dict(probe=probe, command=child['command'],
                                                   exit=child['exit'], stderr=child['stderr'],
                                                   original_supervisor=result['supervisor'])
                return receipt, child['exit']
            except (ValueError, TypeError):
                result['acquisition']['sudo_child'] = child
        else:
            result['acquisition']['sudo_probe'] = probe

    if not privileged:
        subject_uid, subject_gid = os.getuid(), os.getgid()
        result['limits'].append('Required foreign-owner/matched-pair and owner-mutant controls unavailable here; local same-UID positive is not their substitute.')
    result['executing_subject'] = dict(uid=subject_uid, gid=subject_gid,
                                      matches_requested=(subject_uid == args.consumer_uid and subject_gid == args.consumer_gid))
    fixture_root = Path(tempfile.mkdtemp(prefix='r0015-owner-', dir='/tmp'))
    fixture_root.chmod(0o755)
    result['fixture'] = str(fixture_root)
    exporter = OwnedFixtureExport(fixture_root)
    try:
        fixture_home = fixture_root / 'subject-home'
        fixture_tmp = fixture_root / 'subject-tmp'
        fixture_bin = fixture_root / 'bin'
        fixture_home.mkdir(mode=0o755)
        fixture_tmp.mkdir(mode=0o700)
        fixture_bin.mkdir(mode=0o755)
        events = fixture_root / 'mktemp-events.jsonl'
        events.write_text('')
        events.chmod(0o600)
        victim = fixture_root / 'outside-sentinel.txt'
        victim.write_bytes(b'unchanged outside sentinel\n')
        victim.chmod(0o644)
        if privileged:
            # All subjects below are fresh children; no host account or parent change.
            for path in (fixture_root, fixture_home, fixture_bin, victim):
                os.chown(path, 0, 0)
            for path in (fixture_tmp, events):
                os.chown(path, subject_uid, subject_gid)
        native_mktemp = shutil.which('mktemp')
        native_bash = shutil.which('bash')
        require(native_mktemp and native_bash, 'Required native bash/mktemp missing')
        wrapper = fixture_bin / 'mktemp'
        wrapper.write_text('#!' + sys.executable + '\n' +
                          'import json,os,sys\nfrom pathlib import Path\n' +
                          'root=Path(os.environ["TASK_FIXTURE_ROOT"]).resolve(strict=True)\n' +
                          'target=Path(sys.argv[-1]); parent=target.parent.resolve(strict=True)\n' +
                          'if parent != root and root not in parent.parents: raise SystemExit("fixture mktemp escape refused")\n' +
                          'with open(os.environ["TASK_MKTEMP_EVENTS"],"a") as out: out.write(json.dumps({"argv":sys.argv[1:],"uid":os.getuid(),"gid":os.getgid()})+"\\n")\n' +
                          'os.execv(' + repr(native_mktemp) + ',[' + repr(native_mktemp) + ']+sys.argv[1:])\n')
        wrapper.chmod(0o755)
        result['native_tools'] = {name: shutil.which(name) for name in ('bash', 'stat', 'id', 'mktemp', 'python3', 'curl')}
        result['bash_version'] = command([native_bash, '--version'])
        result['filesystem'] = command(['stat', '-f', '-c', '%T', str(fixture_root)])
        result['parents'] = [identity(p) for p in ('/', '/tmp', fixture_root, fixture_home, fixture_tmp)]
        env = {'PATH': str(fixture_bin) + ':/usr/bin:/bin', 'LANG': 'C.UTF-8',
               'HOME': str(fixture_home), 'TMPDIR': str(fixture_tmp),
               'TASK_FIXTURE_ROOT': str(fixture_root), 'TASK_MKTEMP_EVENTS': str(events)}
        setup = 'set -Eeuo pipefail\nPLATFORM=linux\nDRY_RUN=0\nWORK_ROOT=""; WORK_ID=""; BUNDLE_ROOT=""; BUNDLE_ID=""; DOWNLOAD_ROOT=""; PRESET_ROOT=""\n'

        def drop_subject():
            os.setgroups([])
            os.setgid(subject_gid)
            os.setuid(subject_uid)

        def run(body, mutant=False):
            kwargs = dict(env=env, cwd=fixture_root)
            if privileged:
                kwargs['preexec_fn'] = drop_subject
            return command([native_bash, '--noprofile', '--norc', '-c',
                            setup + (mutant_library if mutant else library) + '\n' + body], **kwargs)

        def check(name, action):
            try:
                detail = action()
                result['results'].append(dict(case=name, pass_=True, status='PASS', executed=True, detail=detail))
            except Exception as error:
                result['results'].append(dict(case=name, pass_=False, status='FAIL', executed=True,
                                              error=str(error)))

        # Record the actual source consumer identity, including post-drop capabilities.
        actor = run('id -u; id -g; id -G; /usr/bin/python3 -c \'import json,os,pathlib; print(json.dumps({"uid":os.getuid(),"gid":os.getgid(),"groups":os.getgroups(),"status":{l.split(":",1)[0]:l.split(":",1)[1].strip() for l in pathlib.Path("/proc/self/status").read_text().splitlines() if l.startswith(("CapEff:","CapPrm:","NoNewPrivs:"))}}))\'\n')
        result['subject_receipt'] = actor
        require(actor['exit'] == 0 and actor['stdout'].splitlines()[0] == str(subject_uid),
                'Subject identity/bootstrap mismatch')
        actor_fields = json.loads(actor['stdout'].splitlines()[-1])
        require(actor_fields['uid'] == subject_uid and actor_fields['gid'] == subject_gid,
                'Actual Python subject UID/GID mismatch')
        if privileged:
            require(actor_fields['groups'] == [] and
                    int(actor_fields['status']['CapEff'], 16) == 0 and
                    int(actor_fields['status']['CapPrm'], 16) == 0,
                    'Native subject retained supplementary groups or capabilities')
        subjects = [fixture_home, fixture_tmp, victim]
        result['legacy_tmp_premise'] = dict(subject_uid=subject_uid, temporary_parent=identity('/tmp'),
                                            comment='Old wrong-owner fixture selected /tmp without checking owner or mode.')
        result['source_guard_parse'] = command([native_bash, '-n', '-c', setup + library])
        result['mutant_guard_parse'] = command([native_bash, '-n', '-c', setup + mutant_library])
        require(result['source_guard_parse']['exit'] == 0 and result['mutant_guard_parse']['exit'] == 0,
                'Source or owner-only mutant has a parse failure')

        def negative():
            before = snapshot(subjects)
            before_events = events.read_bytes()
            actual = run('initialize_staging\n')
            after = snapshot(subjects)
            result['observations']['negative'] = dict(execution=actual, before=before, after=after,
                                                       mktemp_events=events.read_text())
            require(actual['exit'] != 0 and 'Use a private, owned staging parent' in actual['stderr'],
                    'Foreign HOME did not reach expected owner refusal: ' + repr(actual))
            require(actual['stdout'] == '', 'Rejected initializer returned usable output')
            require(before == after and before_events == events.read_bytes(), 'Rejected HOME caused an output/mktemp effect')
            return dict(execution=actual, before=before, after=after, mktemp_calls=0)

        def negative_mutant():
            before = snapshot(subjects)
            before_events = events.read_bytes()
            original = run('trusted_parent "$HOME" home\n')
            mutation = run('trusted_parent "$HOME" home\n', mutant=True)
            result['observations']['owner_mutant'] = dict(original=original, mutant=mutation,
                                                           before=before, after=snapshot(subjects),
                                                           mktemp_events=events.read_text())
            require(original['exit'] != 0 and 'Use a private, owned staging parent' in original['stderr'],
                    'Original helper did not reject only final HOME owner')
            require(mutation['exit'] == 0 and mutation['stdout'] == str(fixture_home) + '\n',
                    'Owner-only mutant did not admit the foreign parent: ' + repr(mutation))
            require(before == snapshot(subjects) and before_events == events.read_bytes(), 'Helper discriminator changed subjects')
            return dict(original=original, mutant=mutation, mutant_rejected_by_oracle=True,
                        oracle='foreign HOME must not be returned by actual trusted_parent; later mktemp is not executed')

        if privileged:
            check('R0015-A05 foreign UID0 HOME mode0755 refused before staging effects', negative)
            check('R0015-A07 terminal owner-only mutant admits foreign HOME; original refuses', negative_mutant)
            # The mandatory positive changes this same HOME's owner only; mode and ancestors remain.
            pair_before = identity(fixture_home)
            os.chown(fixture_home, subject_uid, 0)
            result['matched_pair_change'] = dict(before=pair_before, after=identity(fixture_home),
                                                 difference='HOME UID only; same GID0, path, device/inode, mode0755 and ancestors')
        else:
            for name in ('R0015-A05 foreign UID0 HOME mode0755 admission', 'R0015-A07 terminal owner-only mutant'):
                result['results'].append(dict(case=name, pass_=False, status='BLOCKED', executed=False,
                                              reason='No privileged supervisor with mapped distinct subject UID/GID; no qualified foreign-owner fixture'))

        def positive():
            before_victim = identity(victim)
            actual = run('''initialize_staging
    guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$BUNDLE_ROOT/retained-proof.txt" file
    (umask 077; printf 'retained fixture proof\\n' > "$BUNDLE_ROOT/retained-proof.txt")
    printf '%s\\n%s\\n%s\\n%s\\n' "$WORK_ROOT" "$WORK_ID" "$BUNDLE_ROOT" "$BUNDLE_ID"
    cleanup_staging
    ''')
            result['observations']['positive'] = dict(execution=actual, mktemp_events=events.read_text())
            require(actual['exit'] == 0, 'Owned HOME positive failed: ' + repr(actual))
            lines = actual['stdout'].splitlines()
            require(len(lines) == 4, 'Positive returned polluted or missing root identities')
            scratch, scratch_id, bundle, bundle_id = lines
            require(Path(scratch).parent == fixture_tmp and not Path(scratch).exists(), 'Scratch scope or actual cleanup incorrect')
            require(Path(bundle).parent == fixture_home, 'Retained bundle is outside fixture HOME')
            bundle_meta = identity(bundle)
            require(bundle_meta['uid'] == subject_uid and bundle_meta['mode'] == '0o700' and not bundle_meta['symlink'],
                    'Retained bundle owner/mode/type incorrect')
            fields = bundle_id.split(':')
            require(fields == [str(bundle_meta['device']), str(bundle_meta['inode']), str(subject_uid), '700'],
                    'Native retained identity differs from source receipt')
            require(scratch_id.split(':')[-2:] == [str(subject_uid), '700'], 'Native scratch owner/mode not0700')
            fresh_env = dict(env, TASK_RETAINED_PROOF=str(Path(bundle) / 'retained-proof.txt'))
            kwargs = dict(env=fresh_env, cwd=fixture_root)
            if privileged:
                kwargs['preexec_fn'] = drop_subject
            consumer = command([native_bash, '--noprofile', '--norc', '-c',
                                'set -e; id -u; cat "$TASK_RETAINED_PROOF"'], **kwargs)
            result['observations']['positive']['fresh_consumer'] = consumer
            require(consumer['exit'] == 0 and consumer['stdout'] == str(subject_uid) + '\nretained fixture proof\n',
                    'Fresh consumer could not read exact retained bytes')
            require(identity(victim) == before_victim, 'Outside sentinel changed')
            helper_positive = run('trusted_parent "$HOME" home\n')
            mutant_positive = run('trusted_parent "$HOME" home\n', mutant=True)
            require(helper_positive['exit'] == 0 and mutant_positive['exit'] == 0 and
                    helper_positive['stdout'] == mutant_positive['stdout'] == str(fixture_home) + '\n',
                    'Healthy helper or owner-only mutant disabled the positive')
            return dict(execution=actual, scratch_id=scratch_id, bundle_identity=bundle_meta,
                        retained_file=identity(Path(bundle) / 'retained-proof.txt'), fresh_consumer=consumer,
                        original_helper=helper_positive, mutant_helper=mutant_positive,
                        mktemp_events=[json.loads(line) for line in events.read_text().splitlines()])

        check('R0015-A06 matched native owned HOME positive' if privileged else
              'local same-UID owned HOME positive (not matched foreign-owner acceptance)', positive)
        result['post_state'] = snapshot(subjects)
        result['native_distinct_uid_claim'] = privileged
        failed = any(row['status'] == 'FAIL' for row in result['results'])
        result['status'] = 'FAIL' if failed else ('PASS' if privileged else 'BLOCKED_ACQUISITION')
        exit_code = 1 if failed else (0 if privileged else 2)

    except Exception as error:
        result['status'] = 'ERROR'
        result['results'].append(dict(case='fixture bootstrap after owned-root creation',
                                      pass_=False, status='ERROR', executed=False, error=str(error)))
        result['traceback'] = traceback.format_exc()
        exit_code = 2
    result['observation_status'] = result['status']
    try:
        result['fixture_export'] = exporter.export(fixture_root, result)
        # Verify published bytes through the same no-follow reader the
        # unprivileged collector will use; original observations stay intact.
        read_verified_fixture_export(result)
    except Exception as error:
        result['fixture_export'] = dict(schema='r0015-owner-fixture-export/v1',
                                       status='FAIL', error=str(error))
        result['results'].append(dict(case='private fixture evidence export', pass_=False,
                                      status='FAIL_EVIDENCE_ACQUISITION', executed=True, error=str(error)))
        result['status'] = 'FAIL_EVIDENCE_ACQUISITION'
        if exit_code == 0:
            exit_code = 1
    finally:
        exporter.close()
    return result, exit_code


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('SourceFile')
    parser.add_argument('--consumer-uid', type=int, default=1000)
    parser.add_argument('--consumer-gid', type=int, default=1000)
    parser.add_argument('--no-sudo', action='store_true')
    parser.add_argument('--_elevated', action='store_true', help=argparse.SUPPRESS)
    options = parser.parse_args()
    try:
        receipt, exit_code = main(options)
    except Exception as exc:
        receipt = dict(schema='r0015-native-owner-proof/v1', status='ERROR',
                       results=[dict(case='fixture bootstrap', pass_=False, status='ERROR',
                                     executed=False, error=str(exc))], traceback=traceback.format_exc())
        exit_code = 2
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    raise SystemExit(exit_code)
