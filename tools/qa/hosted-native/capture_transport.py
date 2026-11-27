#!/usr/bin/env python3
"""Portable private staging/restoration; no crypto, native acceptance or key IO."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import stat
import sys
import types

PROTOCOL = 'salah-portable-capture/1'
ENVELOPE_SHA256 = '50b3a4e388f608f7a824b53d3e320c6957f4c4b6f4be5053e69ce01c1dee21be'
MAX_FILES = 19_999
MAX_DIRECTORIES = 20_000
MAX_DEPTH = 64
MAX_FILE_BYTES = 1 << 30
MAX_TOTAL_BYTES = 4 << 30
MAX_MAP_BYTES = 8 << 20
CHUNK = 1 << 20
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK


class Rejected(Exception):
    """Only fixed, non-content categories cross the CLI boundary."""


def need(value, category):
    if not value:
        raise Rejected(category)


def envelope():
    filename = Path(__file__).with_name('envelope.py')
    need(all(not p.is_symlink() for p in [filename, *filename.parents]), 'DEPENDENCY')
    need(filename.is_file(), 'DEPENDENCY')
    data = filename.read_bytes()
    need(hashlib.sha256(data).hexdigest() == ENVELOPE_SHA256, 'DEPENDENCY')
    module = types.ModuleType('portable_capture_envelope')
    module.__file__ = str(filename)
    # Evaluate the bytes that were checked; do not adopt an unrelated bytecode cache.
    exec(compile(data, str(filename), 'exec'), module.__dict__)
    return module


def token(info):
    return (info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode), info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def parent_fd(root, name):
    parts = name.split('/')
    current = os.dup(root)
    try:
        for part in parts[:-1]:
            child = os.open(part, DIR_FLAGS, dir_fd=current)
            os.close(current)
            current = child
        return current, parts[-1]
    except BaseException:
        os.close(current)
        raise


def inventory(root, E, file_limit):
    result = {'.': ('directory', token(os.fstat(root)))}
    counts = {'file': 0, 'directory': 0}
    total = 0
    def visit(descriptor, prefix='', depth=0):
        nonlocal total
        with os.scandir(descriptor) as entries:
            for entry in entries:
                name = E.safe_name(prefix+entry.name)
                need(depth+1 <= MAX_DEPTH, 'LIMIT')
                info = os.stat(entry.name, dir_fd=descriptor, follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    counts['directory'] += 1
                    need(counts['directory'] <= MAX_DIRECTORIES, 'LIMIT')
                    child = os.open(entry.name, DIR_FLAGS, dir_fd=descriptor)
                    try:
                        need(token(os.fstat(child)) == token(info), 'SOURCE_CHANGED')
                        result[name] = ('directory', token(info))
                        visit(child, name+'/', depth+1)
                        need(token(os.fstat(child)) == token(info), 'SOURCE_CHANGED')
                    finally:
                        os.close(child)
                else:
                    need(stat.S_ISREG(info.st_mode), 'POPULATION')
                    counts['file'] += 1
                    total += info.st_size
                    need(counts['file'] <= file_limit and 0 <= info.st_size <= MAX_FILE_BYTES
                         and total <= MAX_TOTAL_BYTES, 'LIMIT')
                    result[name] = ('file', token(info))
    visit(root)
    need(token(os.fstat(root)) == result['.'][1], 'SOURCE_CHANGED')
    return result


def write_all(descriptor, data):
    view = memoryview(data)
    while view:
        count = os.write(descriptor, view)
        need(type(count) is int and 0 < count <= len(view), 'IO')
        view = view[count:]


def file_reader(root, name, expected=None):
    parent, leaf = parent_fd(root, name)
    try:
        fd = os.open(leaf, READ_FLAGS, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        info = os.fstat(fd)
        need(stat.S_ISREG(info.st_mode), 'POPULATION')
        need(0 <= info.st_size <= MAX_FILE_BYTES, 'LIMIT')
        if expected is not None:
            need(token(info) == expected, 'SOURCE_CHANGED')
        return fd, info
    except BaseException:
        os.close(fd)
        raise


def consume(fd, before, sink=None):
    size = 0
    digest = hashlib.sha256()
    while True:
        chunk = os.read(fd, CHUNK)
        if not chunk:
            break
        size += len(chunk)
        need(size <= before.st_size, 'SOURCE_CHANGED')
        digest.update(chunk)
        if sink is not None:
            sink(chunk)
    need(size == before.st_size and token(os.fstat(fd)) == token(before), 'SOURCE_CHANGED')
    return size, digest.hexdigest()


def _copy_file(source, name, expected, target, target_name):
    fd, before = file_reader(source, name, expected)
    parent = None
    output = None
    try:
        parent, leaf = parent_fd(target, target_name)
        output = os.open(leaf, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=parent)
        result = consume(fd, before, lambda data: write_all(output, data))
        os.fsync(output)
        return result
    finally:
        try:
            if output is not None:
                os.close(output)
        finally:
            try:
                if parent is not None:
                    os.close(parent)
            finally:
                os.close(fd)


def write_bytes(root, name, data):
    parent, leaf = parent_fd(root, name)
    fd = None
    try:
        fd = os.open(leaf, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=parent)
        write_all(fd, data)
        os.fsync(fd)
    finally:
        if fd is not None:
            os.close(fd)
        os.close(parent)


def make_directories(root, names):
    for name in sorted(names, key=lambda x: (x.count('/'), x)):
        parent, leaf = parent_fd(root, name)
        try:
            # Exclusive even for directories: case-fold aliases must never merge.
            os.mkdir(leaf, 0o700, dir_fd=parent)
        finally:
            os.close(parent)


def verify_tree(root, E, directories, files):
    observed = inventory(root, E, MAX_FILES+1)
    expected = {'.': 'directory', **{name: 'directory' for name in directories},
                **{row['path']: 'file' for row in files}}
    need({name: value[0] for name, value in observed.items()} == expected, 'POPULATION')
    for row in files:
        fd, before = file_reader(root, row['path'], observed[row['path']][1])
        try:
            size, digest = consume(fd, before)
        finally:
            os.close(fd)
        need(size == row['size'] and digest == row['sha256'], 'INTEGRITY')


def mapping_bytes(body):
    return (json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(',', ':'))+'\n').encode()


def validate_map(body, E):
    need(type(body) is dict and set(body) == {'protocol', 'directories', 'files', 'totalBytes'}
         and body['protocol'] == PROTOCOL, 'FORMAT')
    directories, files = body['directories'], body['files']
    need(type(directories) is list and len(directories) <= MAX_DIRECTORIES
         and type(files) is list and len(files) <= MAX_FILES, 'LIMIT')
    for name in directories:
        E.safe_name(name)
        need(len(name.split('/')) <= MAX_DEPTH, 'LIMIT')
    need(directories == sorted(set(directories)), 'POPULATION')
    names = []
    total = 0
    for index, row in enumerate(files):
        need(type(row) is dict and set(row) == {'logicalPath', 'payloadPath', 'size', 'sha256'}, 'FORMAT')
        name = E.safe_name(row['logicalPath'])
        need(len(name.split('/')) <= MAX_DEPTH, 'LIMIT')
        need(row['payloadPath'] == f'payload/{index:08d}.bin', 'POPULATION')
        need(type(row['size']) is int and 0 <= row['size'] <= MAX_FILE_BYTES, 'LIMIT')
        need(type(row['sha256']) is str and E.HEX256.fullmatch(row['sha256']), 'FORMAT')
        names.append(name)
        total += row['size']
    need(names == sorted(set(names)) and not set(names).intersection(directories), 'POPULATION')
    directory_set = set(directories)
    for name in [*names, *directories]:
        parts = name.split('/')
        need(all('/'.join(parts[:i]) in directory_set for i in range(1, len(parts))), 'POPULATION')
    need(type(body['totalBytes']) is int and body['totalBytes'] == total
         and total <= MAX_TOTAL_BYTES, 'LIMIT')
    return directories, files


def anchored(path, descriptor, E):
    E.no_symlink_path(path)
    info = path.stat()
    held = os.fstat(descriptor)
    need(stat.S_ISDIR(info.st_mode) and (info.st_dev, info.st_ino) == (held.st_dev, held.st_ino), 'PATH')


def remove_owned(parent, name, identity):
    try:
        current = os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return
    need(stat.S_ISDIR(current.st_mode) and (current.st_dev, current.st_ino) == identity, 'CLEANUP')
    need(shutil.rmtree.avoids_symlink_attacks, 'PLATFORM')
    shutil.rmtree(name, dir_fd=parent)


def publish(staged, parent, leaf, E):
    os.mkdir(leaf, 0o700, dir_fd=parent)
    created = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
    identity = (created.st_dev, created.st_ino)
    target = None
    try:
        need(stat.S_ISDIR(created.st_mode), 'PATH')
        target = os.open(leaf, DIR_FLAGS, dir_fd=parent)
        opened = os.fstat(target)
        need((opened.st_dev, opened.st_ino) == identity, 'PATH')
        entries = inventory(staged, E, MAX_FILES+1)
        directories = [name for name, value in entries.items() if name != '.' and value[0] == 'directory']
        make_directories(target, directories)
        for name, value in entries.items():
            if value[0] != 'file':
                continue
            source_parent, source_leaf = parent_fd(staged, name)
            target_parent = None
            try:
                target_parent, target_leaf = parent_fd(target, name)
                # link() is exclusive. Unlike rename(), it cannot replace a file.
                os.link(source_leaf, target_leaf, src_dir_fd=source_parent,
                        dst_dir_fd=target_parent, follow_symlinks=False)
            finally:
                try:
                    if target_parent is not None:
                        os.close(target_parent)
                finally:
                    os.close(source_parent)
        current = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        need((current.st_dev, current.st_ino) == identity, 'PATH')
        os.fsync(target)
        return identity
    except BaseException:
        remove_owned(parent, leaf, identity)
        raise
    finally:
        if target is not None:
            os.close(target)


def _execute(operation, source, output, protected_roots, E):
    need(type(operation) is str and operation in ('stage', 'restore'), 'ARGUMENT')
    need(isinstance(protected_roots, (list, tuple)) and bool(protected_roots), 'ARGUMENT')
    source, output = E.no_symlink_path(source), E.no_symlink_path(output)
    protected = [source, E.no_symlink_path(Path(__file__).resolve().parents[3]),
                 *[E.no_symlink_path(p) for p in protected_roots]]
    need(source.is_dir() and output.parent.is_dir(), 'PATH')
    need(not output.exists() and not output.is_symlink(), 'PATH')
    need(all(not output.is_relative_to(p) and not p.is_relative_to(output) for p in protected), 'PATH')
    source_fd = os.open(source, DIR_FLAGS)
    outer = None
    staged = None
    temporary = None
    published = None
    try:
        outer = os.open(output.parent, DIR_FLAGS)
        anchored(source, source_fd, E)
        anchored(output.parent, outer, E)
        before = inventory(source_fd, E, MAX_FILES if operation == 'stage' else MAX_FILES+1)
        candidate = 'capture-transport-'+secrets.token_hex(16)
        os.mkdir(candidate, 0o700, dir_fd=outer)
        created = os.stat(candidate, dir_fd=outer, follow_symlinks=False)
        temporary_identity = (created.st_dev, created.st_ino)
        temporary = candidate
        need(stat.S_ISDIR(created.st_mode), 'PATH')
        staged = os.open(temporary, DIR_FLAGS, dir_fd=outer)
        opened = os.fstat(staged)
        need((opened.st_dev, opened.st_ino) == temporary_identity, 'PATH')
        if operation == 'stage':
            directories = sorted(name for name, value in before.items() if name != '.' and value[0] == 'directory')
            names = sorted(name for name, value in before.items() if value[0] == 'file')
            if names:
                make_directories(staged, ['payload'])
            rows = []
            for index, name in enumerate(names):
                payload = f'payload/{index:08d}.bin'
                size, digest = _copy_file(source_fd, name, before[name][1], staged, payload)
                rows.append({'logicalPath': name, 'payloadPath': payload, 'size': size, 'sha256': digest})
            body = {'protocol': PROTOCOL, 'directories': directories, 'files': rows,
                    'totalBytes': sum(row['size'] for row in rows)}
            validate_map(body, E)
            raw = mapping_bytes(body)
            need(len(raw) <= MAX_MAP_BYTES and body['totalBytes']+len(raw) <= MAX_TOTAL_BYTES, 'LIMIT')
            write_bytes(staged, 'mapping.json', raw)
            files = [{'path': row['payloadPath'], 'size': row['size'], 'sha256': row['sha256']} for row in rows]
            files.append({'path': 'mapping.json', 'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
            verify_tree(staged, E, ['payload'] if rows else [], files)
        else:
            need('mapping.json' in before and before['mapping.json'][0] == 'file', 'POPULATION')
            fd, info = file_reader(source_fd, 'mapping.json', before['mapping.json'][1])
            try:
                need(info.st_size <= MAX_MAP_BYTES, 'LIMIT')
                chunks = []
                consume(fd, info, chunks.append)
                raw = b''.join(chunks)
            finally:
                os.close(fd)
            body = E.load_json(raw)
            directories, rows = validate_map(body, E)
            need(body['totalBytes']+len(raw) <= MAX_TOTAL_BYTES, 'LIMIT')
            files = [{'path': row['payloadPath'], 'size': row['size'], 'sha256': row['sha256']} for row in rows]
            files.append({'path': 'mapping.json', 'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
            verify_tree(source_fd, E, ['payload'] if rows else [], files)
            make_directories(staged, directories)
            for row in rows:
                size, digest = _copy_file(source_fd, row['payloadPath'], before[row['payloadPath']][1], staged, row['logicalPath'])
                need(size == row['size'] and digest == row['sha256'], 'INTEGRITY')
            verify_tree(staged, E, directories,
                        [{'path': row['logicalPath'], 'size': row['size'], 'sha256': row['sha256']} for row in rows])
        anchored(source, source_fd, E)
        need(inventory(source_fd, E, MAX_FILES+1) == before, 'SOURCE_CHANGED')
        anchored(output.parent, outer, E)
        published = publish(staged, outer, output.name, E)
        anchored(output.parent, outer, E)
        E.no_symlink_path(output)
        actual = output.stat()
        need((actual.st_dev, actual.st_ino) == published, 'PATH')
        remove_owned(outer, temporary, temporary_identity)
        temporary = None
        return {'protocol': PROTOCOL, 'status': 'STAGED' if operation == 'stage' else 'RESTORED',
                'fileCount': len(rows), 'directoryCount': len(directories), 'totalBytes': body['totalBytes'],
                'mappingSha256': hashlib.sha256(raw).hexdigest()}
    except BaseException:
        if published is not None:
            remove_owned(outer, output.name, published)
        raise
    finally:
        try:
            if staged is not None:
                os.close(staged)
            if temporary is not None:
                remove_owned(outer, temporary, temporary_identity)
        finally:
            if outer is not None:
                os.close(outer)
            os.close(source_fd)


def execute(operation, source, output, *, protected_roots):
    E = envelope()
    try:
        return _execute(operation, source, output, protected_roots, E)
    except Rejected:
        raise
    except E.Rejected:
        raise Rejected('FORMAT') from None
    except OSError:
        raise Rejected('IO') from None
    except (ValueError, TypeError, UnicodeError, KeyError, RecursionError):
        raise Rejected('FORMAT') from None


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Rejected('ARGUMENT')


def main(argv=None):
    try:
        parser = Parser(prog='capture_transport', description=__doc__)
        parser.add_argument('operation', choices=('stage', 'restore'))
        parser.add_argument('--source', required=True, type=Path)
        parser.add_argument('--out', required=True, type=Path)
        parser.add_argument('--protect', required=True, action='append', type=Path)
        args = parser.parse_args(argv)
        signal.signal(signal.SIGTERM, lambda *unused: (_ for _ in ()).throw(KeyboardInterrupt()))
        execute(args.operation, args.source, args.out, protected_roots=args.protect)
    except Rejected as error:
        print('CAPTURE_TRANSPORT_REJECTED:'+str(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print('CAPTURE_TRANSPORT_REJECTED:INTERRUPTED', file=sys.stderr)
        return 1
    except Exception:
        print('CAPTURE_TRANSPORT_REJECTED:INTERNAL', file=sys.stderr)
        return 1
    print('CAPTURE_STAGE_OK' if args.operation == 'stage' else 'CAPTURE_RESTORE_OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
