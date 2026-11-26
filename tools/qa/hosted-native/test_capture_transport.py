#!/usr/bin/env python3
"""Synthetic source/ZIP controls; no browser, crypto operation, or key access."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import envelope as E
try:
    import capture_transport as T
except ModuleNotFoundError as error:
    if error.name != 'capture_transport':
        raise
    T = None


def population(root):
    return {str(p.relative_to(root)): ('directory' if p.is_dir() else p.read_bytes())
            for p in sorted(root.rglob('*'))}


class PortableCaptureTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(T, 'portable capture stage/restore implementation is absent')
        self.temp = tempfile.TemporaryDirectory(prefix='portable-capture-control-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'source'
        self.source.mkdir()
        self.protected = self.root/'runtime'
        self.protected.mkdir()
        (self.source/'case.dat').write_bytes(bytes(range(256)))
        (self.source/'CASE.dat').write_bytes(b'distinct\x00\xff')
        (self.source/'empty.bin').write_bytes(b'')
        for directory in ('Folder', 'folder', 'empty/nested'):
            (self.source/directory).mkdir(parents=True)
        (self.source/'Folder/item.json').write_bytes(b'{"fixture":1}\n')
        (self.source/'folder/item.json').write_bytes(b'{"fixture":2}\n')
        self.original = population(self.source)
        self.stage = self.root/'stage'
        self.restored = self.root/'restored'

    def execute(self, operation, source=None, output=None):
        return T.execute(operation, source or (self.source if operation == 'stage' else self.stage),
                         output or (self.stage if operation == 'stage' else self.restored),
                         protected_roots=[self.protected])

    def mapping(self):
        return json.loads((self.stage/'mapping.json').read_bytes())

    def alter_mapping(self, change):
        body = self.mapping()
        change(body)
        (self.stage/'mapping.json').write_text(json.dumps(body))

    def assert_restore_rejected(self):
        with self.assertRaises(T.Rejected):
            self.execute('restore')
        self.assertFalse(self.restored.exists())

    def test_original_envelope_still_rejects_case_collisions(self):
        with self.assertRaises(E.Rejected):
            E.create_archive(self.source, self.root/'original.zip')
        self.assertEqual(population(self.source), self.original)

    def test_roundtrip_preserves_exact_files_directories_and_binary_bytes(self):
        staged = self.execute('stage')
        self.assertEqual(staged['status'], 'STAGED')
        self.assertEqual(self.execute('restore')['status'], 'RESTORED')
        self.assertEqual(population(self.restored), self.original)
        self.assertEqual(population(self.source), self.original)

    def test_staged_paths_are_portable_and_logical_names_remain_private(self):
        self.execute('stage')
        body = self.mapping()
        self.assertEqual(body['protocol'], 'salah-portable-capture/1')
        names = [str(p.relative_to(self.stage)) for p in self.stage.rglob('*') if p.is_file()]
        E.distinct_paths(names)
        self.assertEqual(set(names), {'mapping.json', *[f'payload/{i:08d}.bin' for i in range(5)]})
        self.assertEqual({row['logicalPath'] for row in body['files']},
                         {name for name, value in self.original.items() if value != 'directory'})

    def test_unchanged_envelope_zip_functions_transport_the_package(self):
        self.execute('stage')
        archive = self.root/'portable.zip'
        E.create_archive(self.stage, archive)
        opened = self.root/'opened'
        E.extract_verified(archive, opened)
        self.execute('restore', source=opened)
        self.assertEqual(population(self.restored), self.original)

    def test_mapping_and_payload_are_deterministic_and_private_modes(self):
        self.execute('stage')
        second = self.root/'second'
        self.execute('stage', output=second)
        self.assertEqual(population(self.stage), population(second))
        for p in [self.stage, *self.stage.rglob('*')]:
            self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o700 if p.is_dir() else 0o600)

    def test_empty_tree_and_empty_directories_survive(self):
        empty = self.root/'empty-source'
        (empty/'empty/nested').mkdir(parents=True)
        self.execute('stage', source=empty)
        self.execute('restore')
        self.assertEqual(population(self.restored), population(empty))

    def test_zero_payload_zip_roundtrip_preserves_logical_empty_directories(self):
        empty = self.root/'empty-source'
        (empty/'Empty/inner').mkdir(parents=True)
        (empty/'empty').mkdir()
        self.execute('stage', source=empty)
        self.assertFalse((self.stage/'payload').exists())
        archive = self.root/'empty.zip'
        E.create_archive(self.stage, archive)
        opened = self.root/'opened'
        E.extract_verified(archive, opened)
        self.execute('restore', source=opened)
        self.assertEqual(population(self.restored), population(empty))

    def test_existing_outputs_are_never_overwritten(self):
        self.stage.mkdir()
        (self.stage/'sentinel').write_bytes(b'keep')
        with self.assertRaises(T.Rejected):
            self.execute('stage')
        self.assertEqual((self.stage/'sentinel').read_bytes(), b'keep')

    def test_source_and_protected_destinations_are_refused(self):
        for target in [self.source/'new', self.protected/'new']:
            with self.assertRaises(T.Rejected):
                self.execute('stage', output=target)
            self.assertFalse(target.exists())
        self.assertEqual(population(self.source), self.original)

    def test_output_parent_alias_to_source_or_runtime_is_refused(self):
        for index, target in enumerate([self.source, self.protected]):
            alias = self.root/f'alias{index}'
            alias.symlink_to(target, target_is_directory=True)
            with self.assertRaises(T.Rejected):
                self.execute('stage', output=alias/'new')
            self.assertFalse((target/'new').exists())
        self.assertEqual(population(self.source), self.original)

    def test_symlinked_input_root_or_ancestor_is_refused(self):
        alias = self.root/'source-alias'
        alias.symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(T.Rejected):
            self.execute('stage', source=alias)
        with self.assertRaises(T.Rejected):
            self.execute('stage', source=alias/'Folder')
        self.assertFalse(self.stage.exists())

    def test_source_symlinks_and_nonregular_entries_are_refused(self):
        extra = self.source/'extra'
        extra.symlink_to(self.source/'case.dat')
        with self.assertRaises(T.Rejected):
            self.execute('stage')
        extra.unlink()
        os.mkfifo(extra)
        with self.assertRaises(T.Rejected):
            self.execute('stage')
        self.assertFalse(self.stage.exists())

    def test_duplicate_json_keys_are_refused(self):
        self.execute('stage')
        p = self.stage/'mapping.json'
        p.write_text('{"protocol":"salah-portable-capture/1",'+p.read_text()[1:])
        self.assert_restore_rejected()

    def test_unsafe_logical_paths_are_refused(self):
        self.execute('stage')
        original = (self.stage/'mapping.json').read_bytes()
        for name in ['../escape', '/absolute', 'a//b', 'a/../b', 'a\\b', 'C:drive', 'CON', 'tail.', 'tail ', 'cafe\u0301']:
            (self.stage/'mapping.json').write_bytes(original)
            self.alter_mapping(lambda x: x['files'][0].update(logicalPath=name))
            self.assert_restore_rejected()

    def test_duplicate_logical_names_and_file_directory_overlap_are_refused(self):
        self.execute('stage')
        original = (self.stage/'mapping.json').read_bytes()
        self.alter_mapping(lambda x: x['files'][1].update(logicalPath=x['files'][0]['logicalPath']))
        self.assert_restore_rejected()
        (self.stage/'mapping.json').write_bytes(original)
        self.alter_mapping(lambda x: x['directories'].append(x['files'][0]['logicalPath']))
        self.assert_restore_rejected()

    def test_payload_mapping_is_exact_unique_and_canonical(self):
        self.execute('stage')
        original = (self.stage/'mapping.json').read_bytes()
        for value in ['../escape', 'payload/99999999.bin', 'payload/00000001.bin']:
            (self.stage/'mapping.json').write_bytes(original)
            self.alter_mapping(lambda x: x['files'][0].update(payloadPath=value))
            self.assert_restore_rejected()

    def test_mapping_fields_types_counts_and_hashes_are_strict(self):
        self.execute('stage')
        original = (self.stage/'mapping.json').read_bytes()
        changes = [lambda x:x.update(extra=True), lambda x:x.update(totalBytes=True),
                   lambda x:x['files'][0].update(size=True), lambda x:x['files'][0].update(sha256='BAD'),
                   lambda x:x.update(totalBytes=x['totalBytes']+1), lambda x:x['directories'].append('undeclared-parent/child')]
        for change in changes:
            (self.stage/'mapping.json').write_bytes(original)
            self.alter_mapping(change)
            self.assert_restore_rejected()

    def test_payload_bytes_missing_members_and_extra_population_are_refused(self):
        self.execute('stage')
        file = self.stage/'payload/00000000.bin'
        original = file.read_bytes()
        file.write_bytes(original+b'x')
        self.assert_restore_rejected()
        file.unlink()
        self.assert_restore_rejected()
        file.write_bytes(original)
        (self.stage/'extra').mkdir()
        self.assert_restore_rejected()

    def test_payload_symlink_is_refused(self):
        self.execute('stage')
        p = self.stage/'payload/00000000.bin'
        p.unlink()
        p.symlink_to(self.source/'CASE.dat')
        self.assert_restore_rejected()

    def test_limits_reject_without_partial_success(self):
        for limit, value in [('MAX_FILES', 2), ('MAX_DIRECTORIES', 1), ('MAX_TOTAL_BYTES', 1), ('MAX_MAP_BYTES', 16), ('MAX_DEPTH', 1)]:
            with mock.patch.object(T, limit, value), self.assertRaises(T.Rejected):
                self.execute('stage')
            self.assertFalse(self.stage.exists())
        large = self.source/'large'
        with large.open('wb') as stream:
            stream.truncate((1 << 30)+1)
        with self.assertRaises(T.Rejected):
            self.execute('stage')
        self.assertFalse(self.stage.exists())

    def test_source_change_during_copy_is_rejected(self):
        original = T._copy_file
        changed = False
        def copying(*args, **kwargs):
            nonlocal changed
            result = original(*args, **kwargs)
            if not changed:
                changed = True
                (self.source/'case.dat').write_bytes(b'controlled source change')
            return result
        with mock.patch.object(T, '_copy_file', copying), self.assertRaises(T.Rejected):
            self.execute('stage')
        self.assertFalse(self.stage.exists())
        self.assertEqual((self.source/'case.dat').read_bytes(), b'controlled source change')

    def test_partial_write_failure_cleans_only_owned_output(self):
        original = T._copy_file
        before = set(self.root.iterdir())
        def copying(*args, **kwargs):
            original(*args, **kwargs)
            raise OSError('controlled private write failure')
        with mock.patch.object(T, '_copy_file', copying), self.assertRaises(T.Rejected):
            self.execute('stage')
        self.assertEqual(set(self.root.iterdir()), before)
        self.assertEqual(population(self.source), self.original)

    def test_short_writes_preserve_every_byte(self):
        write = os.write
        with mock.patch.object(T.os, 'write', lambda fd, data: write(fd, data[:7])):
            self.execute('stage')
            self.execute('restore')
        self.assertEqual(population(self.restored), self.original)

    def test_failed_temporary_directory_open_removes_owned_reservation(self):
        opening = os.open
        before = set(self.root.iterdir())
        def failing(name, flags, *args, **kwargs):
            if str(name).startswith('capture-transport-') and flags == T.DIR_FLAGS:
                raise PermissionError('controlled private directory open')
            return opening(name, flags, *args, **kwargs)
        with mock.patch.object(T.os, 'open', failing), self.assertRaises(T.Rejected):
            self.execute('stage')
        self.assertEqual(set(self.root.iterdir()), before)

    def test_failed_publication_open_removes_owned_output(self):
        opening = os.open
        before = set(self.root.iterdir())
        def failing(name, flags, *args, **kwargs):
            if name == self.stage.name and flags == T.DIR_FLAGS:
                raise PermissionError('controlled private publication open')
            return opening(name, flags, *args, **kwargs)
        with mock.patch.object(T.os, 'open', failing), self.assertRaises(T.Rejected):
            self.execute('stage')
        self.assertEqual(set(self.root.iterdir()), before)

    def test_target_parent_open_failure_does_not_leak_source_descriptor(self):
        opening = T.parent_fd
        before = set(os.listdir('/proc/self/fd'))
        def failing(root, name):
            if name.startswith('payload/'):
                raise PermissionError('controlled target parent open')
            return opening(root, name)
        with mock.patch.object(T, 'parent_fd', failing), self.assertRaises(T.Rejected):
            self.execute('stage')
        after = set(os.listdir('/proc/self/fd'))
        try:
            self.assertEqual(after, before)
        finally:
            for fd in after-before:
                try:
                    os.close(int(fd))
                except OSError:
                    pass

    def test_parent_substitution_never_redirects_into_runtime(self):
        parent = self.root/'destination-parent'
        parent.mkdir()
        moved = self.root/'moved-parent'
        original = T._copy_file
        changed = False
        def copying(*args, **kwargs):
            nonlocal changed
            result = original(*args, **kwargs)
            if not changed:
                changed = True
                parent.rename(moved)
                parent.symlink_to(self.protected, target_is_directory=True)
            return result
        with mock.patch.object(T, '_copy_file', copying), self.assertRaises(T.Rejected):
            self.execute('stage', output=parent/'stage')
        self.assertEqual(list(self.protected.iterdir()), [])
        self.assertEqual(list(moved.iterdir()), [])
        self.assertEqual(population(self.source), self.original)

    def test_case_insensitive_directory_collision_cannot_merge(self):
        self.execute('stage')
        mkdir = os.mkdir
        def exclusive(name, *args, **kwargs):
            if name == 'folder':
                raise FileExistsError('controlled case-insensitive collision')
            return mkdir(name, *args, **kwargs)
        with mock.patch.object(T.os, 'mkdir', exclusive):
            self.assert_restore_rejected()
        self.assertEqual(population(self.source), self.original)

    def test_cli_never_prints_private_paths_or_error_details(self):
        script = Path(T.__file__)
        base = [sys.executable, str(script), 'stage', '--source', str(self.source), '--out', str(self.stage), '--protect', str(self.protected)]
        p = subprocess.run(base, capture_output=True, text=True, timeout=20)
        self.assertEqual((p.returncode, p.stdout, p.stderr), (0, 'CAPTURE_STAGE_OK\n', ''))
        for args in [base, base+['--PRIVATE_CANARY_ARGUMENT'], [sys.executable, str(script), 'stage', '--source', '/PRIVATE_CANARY_MISSING']]:
            p = subprocess.run(args, capture_output=True, text=True, timeout=20)
            self.assertNotEqual(p.returncode, 0)
            self.assertEqual(p.stdout, '')
            self.assertRegex(p.stderr, r'^CAPTURE_TRANSPORT_REJECTED:[A-Z_]+\n$')
            self.assertNotIn('PRIVATE_CANARY', p.stderr)
            self.assertNotIn(str(self.root), p.stderr)


if __name__ == '__main__':
    unittest.main()
