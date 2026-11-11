"""Bounded failure controls for the own-ref publication envelope, not product QA."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('r000b_assembly', ROOT / 'tools/qa/r000b_assemble_candidate.py')
assembly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assembly)


def manifest():
    return {'schema': 'r000b-generated-candidate/v1', 'branch': assembly.BRANCH,
            'baseline': {'commit': assembly.BASELINE_COMMIT, 'tree': assembly.BASELINE_TREE},
            'inputs': {name: 'a' * 64 for name in assembly.REQUIRED_INPUTS},
            'generated': {name: 'b' * 64 for name in assembly.GENERATED},
            'approvedChanges': sorted(assembly.AUTHORED)}


class PublicationEnvelope(unittest.TestCase):
    def test_exact_reviewed_envelope_is_admitted(self):
        assembly.validate_manifest(manifest())

    def test_baseline_output_injection_and_unreviewed_identity_are_rejected(self):
        for value in ['a' * 40 + '\ncandidate=' + 'b' * 40, 'a' * 40, None, 123]:
            with self.subTest(value=value):
                candidate = manifest()
                candidate['baseline']['commit'] = value
                with self.assertRaises(ValueError):
                    assembly.validate_manifest(candidate)

    def test_wrong_tree_or_extra_baseline_fields_are_rejected(self):
        for baseline in [{'commit': assembly.BASELINE_COMMIT, 'tree': 'a' * 40},
                         {'commit': assembly.BASELINE_COMMIT, 'tree': assembly.BASELINE_TREE, 'candidate': 'a' * 40}]:
            candidate = manifest()
            candidate['baseline'] = baseline
            with self.assertRaises(ValueError):
                assembly.validate_manifest(candidate)

    def test_incomplete_input_inventory_cannot_qualify_the_builder(self):
        candidate = manifest()
        candidate['inputs'] = {'src/native/index.html': 'a' * 64}
        with self.assertRaises(ValueError):
            assembly.validate_manifest(candidate)

    def test_protected_or_other_owner_delta_is_rejected(self):
        for name in ['v1/index.html', 'vendor/real-sky/src/astronomy.mjs',
                     'moon/src/moon-detail.mjs', 'tests/r0017-scheduler.test.cjs',
                     '.github/workflows/r0017-windows-phase2.yml', '../outside']:
            candidate = manifest()
            candidate['approvedChanges'].append(name)
            candidate['inputs'][name] = 'a' * 64
            with self.subTest(path=name), self.assertRaises(ValueError):
                assembly.validate_manifest(candidate)

    def test_approved_document_requires_its_exact_input_hash(self):
        candidate = manifest()
        candidate['approvedChanges'].append('README.md')
        with self.assertRaises(ValueError):
            assembly.validate_manifest(candidate)
        candidate['inputs']['README.md'] = 'c' * 64
        assembly.validate_manifest(candidate)

    def test_generated_inventory_cannot_omit_or_add_an_output(self):
        for name in ['offline.html', 'moon/BUILD.json', 'real-sky/native-worker.js']:
            candidate = manifest()
            if name in candidate['generated']:
                del candidate['generated'][name]
            else:
                candidate['generated'][name] = 'b' * 64
            with self.subTest(path=name), self.assertRaises(ValueError):
                assembly.validate_manifest(candidate)

    def test_protected_rename_keeps_both_paths_in_authorization_delta(self):
        original = assembly.ROOT
        with tempfile.TemporaryDirectory(prefix='r000b-rename-envelope-') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), 'config', 'diff.renames', 'true'], check=True)
            protected = 'vendor/real-sky/retained-input.txt'
            allowed = 'tests/weather-no-timetable-rename.txt'
            (root / protected).parent.mkdir(parents=True)
            (root / protected).write_bytes(b'unchanged protected bytes\n')
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
            before = subprocess.check_output(['git', '-C', str(root), 'write-tree'], text=True).strip()
            (root / allowed).parent.mkdir(parents=True)
            (root / protected).rename(root / allowed)
            subprocess.run(['git', '-C', str(root), 'add', '-A'], check=True)
            after = subprocess.check_output(['git', '-C', str(root), 'write-tree'], text=True).strip()
            assembly.ROOT = root
            try:
                old_operation = set(assembly.git('diff', '--name-only', before, after).splitlines())
                self.assertEqual(old_operation, {allowed}, 'Reached the original hidden-deletion counterexample')
                current = assembly.changed_paths(before, after)
                self.assertEqual(current, {protected, allowed})
                self.assertFalse(all(assembly.allowed_change(path) for path in current))
            finally:
                assembly.ROOT = original

    def test_actual_git_blob_is_checked_even_when_worktree_bytes_match(self):
        original = assembly.ROOT
        with tempfile.TemporaryDirectory(prefix='r000b-assembly-envelope-') as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'index.html').write_bytes(b'committed bytes\n')
            subprocess.run(['git', '-C', str(root), 'add', 'index.html'], check=True)
            tree = subprocess.check_output(['git', '-C', str(root), 'write-tree'], text=True).strip()
            (root / 'index.html').write_bytes(b'expected worktree bytes\n')
            assembly.ROOT = root
            try:
                expected = {'index.html': hashlib.sha256(b'expected worktree bytes\n').hexdigest()}
                assembly.verify_files(expected, 'test worktree')
                with self.assertRaises(ValueError):
                    assembly.verify_git_files(tree, expected)
                actual = {'index.html': hashlib.sha256(b'committed bytes\n').hexdigest()}
                assembly.verify_git_files(tree, actual)
            finally:
                assembly.ROOT = original


if __name__ == '__main__':
    unittest.main()
