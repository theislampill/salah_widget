"""Reject unknown source custody; this does not qualify rendered lunar pixels."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
SPEC = importlib.util.spec_from_file_location('moon_builder', ROOT / 'tools/build_moon.py')
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class InitialSourceAssociation(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='salah-receiver-association-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.pin = json.loads((ROOT / 'moon/initial-manifest.json').read_bytes())
        for name in [*self.pin['source'], 'moon/initial-manifest.json',
                     'moon/initial-source-association.json']:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if (ROOT / name).exists():
                shutil.copyfile(ROOT / name, target)

    def validate(self):
        return builder.validate_initial_sources(self.root,
            json.loads((self.root / 'moon/initial-manifest.json').read_bytes()))

    def test_exact_reviewed_pair_is_admitted(self):
        self.assertEqual(self.validate(), builder.INITIAL_SOURCE_ASSOCIATION_SHA256)

    def test_each_associated_file_rejects_even_an_unused_comment(self):
        for name in ['moon-detail.mjs', 'moon-engine.mjs', 'asset-digest.mjs']:
            with self.subTest(name=name):
                path = self.root / 'moon/src' / name
                before = path.read_bytes()
                path.write_bytes(before + b'\n// Unknown source change.\n')
                with self.assertRaisesRegex(ValueError, 'source drift'):
                    self.validate()
                path.write_bytes(before)

    def test_unassociated_source_is_still_strict(self):
        path = self.root / 'moon/src/surface_v5.mjs'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'source drift'):
            self.validate()

    def test_original_manifest_cannot_be_rewritten(self):
        path = self.root / 'moon/initial-manifest.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'association ancestry'):
            self.validate()

    def test_rebinding_or_emptying_the_loaded_manifest_cannot_bypass_custody(self):
        path = self.root / 'moon/initial-manifest.json'
        original = path.read_bytes()
        for sources in [{}, {name: builder.sha((self.root / name).read_bytes())
                             for name in self.pin['source']}]:
            with self.subTest(sources=sources):
                changed = json.loads(original)
                changed['source'] = sources
                path.write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError, 'association ancestry'):
                    self.validate()
        unknown = self.root / 'moon/src/surface_v5.mjs'
        unknown.write_bytes(unknown.read_bytes() + b'\n// Unreviewed numerical change.\n')
        changed['source'] = {name: builder.sha((self.root / name).read_bytes())
                             for name in self.pin['source']}
        path.write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError, 'association ancestry'):
            self.validate()

    def test_missing_association_is_rejected(self):
        (self.root / 'moon/initial-source-association.json').unlink()
        with self.assertRaisesRegex(ValueError, 'association identity'):
            self.validate()

    def test_association_changes_cannot_add_or_replace_permissions(self):
        path = self.root / 'moon/initial-source-association.json'
        raw = path.read_bytes()
        mutations = [b'{', raw + b'\n']
        data = json.loads(raw)
        data['pairs'].append({'path': 'moon/src/surface_v5.mjs',
                              'originalSha256': '0' * 64, 'currentSha256': '1' * 64})
        mutations.append(json.dumps(data).encode())
        data['pairs'] = data['pairs'][:1]
        mutations.append(json.dumps(data).encode())
        data['pairs'][0]['currentSha256'] = '0' * 64
        mutations.append(json.dumps(data).encode())
        for content in mutations:
            with self.subTest(content=content[:40]):
                path.write_bytes(content)
                with self.assertRaisesRegex(ValueError, 'association identity'):
                    self.validate()
        path.write_bytes(raw)


if __name__ == '__main__':
    unittest.main()
