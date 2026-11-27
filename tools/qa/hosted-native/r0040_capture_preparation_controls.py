"""Offline guarded-recipe controls. No browser, build or native evidence."""
import difflib
import gzip
import hashlib
import importlib.util
import json
import marshal
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('capture_preparation', HERE/'r0040_capture_prepare.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def record(data):
    return {'bytes': len(data), 'sha256': sha(data),
            'gitBlob': hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()}


class RecipeFixture:
    """Small genuine Git inputs exercise the unchanged recipe, with test-only pins."""
    def __init__(self, root):
        self.root = root
        self.research, self.main, self.historical = [root/name for name in ('research', 'main', 'historical')]
        for directory in (self.research, self.main, self.historical): directory.mkdir()
        self.raw = {f'tools/qa/{name}': data for name, data in {
            'precip_eval_lib.cjs': b'helper original\n', 'precip_models_geom.js': b'geometry original\n',
            'precip_declared_gain.json': b'{"enforceDeclaredGain":false}\n',
            'precip_models.js': b'const treatment="raw";\n',
            'precip_models_capture.cjs': b'legacy capture raw\n', 'precip_models_post.py': b'legacy post raw\n'}.items()}
        for name, data in self.raw.items():
            target = self.historical/name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
        gain = {**self.raw, 'tools/qa/precip_declared_gain.json': b'{"enforceDeclaredGain":true}\n',
                'tools/qa/precip_models.js': b'const treatment="gain";\n',
                'tools/qa/precip_models_capture.cjs': b'legacy capture gain\n',
                'tools/qa/precip_models_post.py': b'legacy post gain\n'}
        revised = {**gain, 'tools/qa/precip_models.js': b'const treatment="revised";\n'}
        patches, stages = [], []
        for name, before, after in (('declared-gain.patch.gz', self.raw, gain), ('layer-study.patch.gz', gain, revised)):
            body = ''.join(''.join(difflib.unified_diff(before[file].decode().splitlines(True),
                            after[file].decode().splitlines(True), 'a/'+file, 'b/'+file))
                           for file in before if before[file] != after[file]).encode()
            compressed = gzip.compress(body, mtime=0)
            relative = 'docs/state-contracts/evidence/R0040/'+name
            path = self.research/relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(compressed)
            patches.append({'path': relative, 'compressedSha256': sha(compressed), 'expandedSha256': sha(body)})
            stages.append({'patch': name, 'checkExit': 0, 'applyExit': 0,
                           'files': {file: record(data) for file, data in after.items()}})
        index = b'genuine controlled main entry\n'; (self.main/'index.html').write_bytes(index)
        inventory = {'files': {'index.html': record(index)}, 'fileCount': 1}
        inventory_bytes = (json.dumps(inventory)+'\n').encode(); (self.main/'GENERATED.json').write_bytes(inventory_bytes)
        self.pins = {'productSha': sha(index), 'geometrySha': sha(revised['tools/qa/precip_models_geom.js']),
                     'rendererSha': sha(revised['tools/qa/precip_models.js']), 'options': None,
                     'evidenceClass': 'native-controlled-capture'}
        code = self.research/'tools/qa/r0040'; code.mkdir(parents=True)
        (code/'pack_design.py').write_text('PROFILE={"enforceDeclaredGain":True}\n')
        (code/'pins-revised.json').write_text(json.dumps(self.pins)+'\n')
        research_inputs = {p.relative_to(self.research).as_posix(): record(p.read_bytes()) for p in code.iterdir()}
        self.body = {'protocol': 'r0040-native-capture-preflight/1', 'researchCommit': self.commit(self.research),
                     'historical': {'files': {name: record(data) for name, data in self.raw.items()}},
                     'researchInputs': research_inputs, 'patches': patches, 'stages': stages, 'pins': self.pins,
                     'main': {'head': self.commit(self.main), 'generatedInventorySha256': sha(inventory_bytes),
                              'generatedMembers': 1,
                              'runtimeFiles': {'index.html': record(index), 'GENERATED.json': record(inventory_bytes)}}}
        self.manifest = root/'manifest.json'; self.save_manifest()

    @staticmethod
    def commit(root):
        env = {**os.environ, 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_TERMINAL_PROMPT': '0'}
        def git(*args):
            return subprocess.check_output(['git', '-C', str(root), *args], env=env, stderr=subprocess.PIPE).decode().strip()
        git('init', '-q'); git('add', '.')
        git('-c', 'user.name=Control', '-c', 'user.email=control.invalid', 'commit', '-qm', 'controlled source')
        return git('rev-parse', 'HEAD')

    def save_manifest(self):
        self.manifest.write_text(json.dumps(self.body, indent=2)+'\n')

    def args(self, label='first'):
        return SimpleNamespace(manifest=self.manifest, research=self.research, historical=self.historical,
                               main=self.main, out=self.root/'work', receipts=self.root/('receipts-'+label))

    def run(self, label='first'):
        with patch.object(M, 'MANIFEST_SHA256', sha(self.manifest.read_bytes())):
            return M.prepare(self.args(label))


class PreparationControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.fixture = RecipeFixture(self.root)
    def tearDown(self): self.tmp.cleanup()

    def test_exact_document_recipe_and_manifest_are_pinned(self):
        manifest, recipe = M.load_contract(M.DEFAULT_MANIFEST)
        self.assertEqual(sha(recipe), '9fc26a75cb62c145f9de7bd7aa386ac6714c238f3e08089558d34f02882f9730')
        self.assertEqual(len(recipe), 4708)
        self.assertEqual(len(manifest['historical']['files']), 6)
        self.assertEqual([row['patch'] for row in manifest['stages']], ['declared-gain.patch.gz', 'layer-study.patch.gz'])
        changed = self.root/'changed-manifest.json'; changed.write_bytes(M.DEFAULT_MANIFEST.read_bytes()+b'\n')
        with self.assertRaises(ValueError): M.load_contract(changed)
        document = self.root/'changed-document.md'; document.write_bytes(M.DOCUMENT.read_bytes().replace(b'import gzip,', b'import gzip ,', 1))
        with self.assertRaises(ValueError): M.load_contract(M.DEFAULT_MANIFEST, document)

    def test_exact_recipe_preserves_six_files_two_stages_and_original_receipt(self):
        result = self.fixture.run()
        self.assertEqual((result['status'], result['returncode'], result['timedOut']), ('PREPARED', 0, False))
        self.assertEqual(result['protocol'], 'r0040-capture-preparation-process/1')
        self.assertEqual(result['inputs'], {key: str(getattr(self.fixture.args(), key).resolve())
                                           for key in ('manifest', 'research', 'historical', 'main', 'out')})
        prepared = Path(result['preparedReceipt']['path'])
        self.assertEqual(result['preparedReceipt']['sha256'], sha(prepared.read_bytes()))
        original = json.loads(prepared.read_bytes())
        self.assertEqual(original['protocol'], 'r0040-capture-preparation/1')
        self.assertEqual(original['stages'], self.fixture.body['stages'])
        self.assertEqual(original['pins'], self.fixture.pins)
        self.assertEqual(len(result['finalHistoricalFiles']), 6)
        for name, data in self.fixture.raw.items(): self.assertEqual((self.fixture.historical/name).read_bytes(), data)
        self.assertTrue((self.root/'receipts-first/attempt.json').is_file())
        self.assertEqual(json.loads((self.root/'receipts-first/process.json').read_text()), result)
        self.assertEqual([name for name in result['streams']], ['stdout', 'stderr'])

    def test_input_drift_missing_or_symlink_is_retained_before_work_creation(self):
        for kind in ('changed', 'missing', 'symlink', 'research-drift'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                fixture = RecipeFixture(Path(tmp)); path = fixture.historical/'tools/qa/precip_models_geom.js'
                if kind == 'changed': path.write_bytes(b'changed source\n')
                elif kind == 'missing': (fixture.historical/'tools/qa/precip_models_capture.cjs').unlink()
                elif kind == 'symlink':
                    original = fixture.root/'original'; path.rename(original); path.symlink_to(original)
                else: (fixture.research/'tools/qa/r0040/pack_design.py').write_text('PROFILE={}\n')
                result = fixture.run()
                self.assertEqual(result['status'], 'INCOMPLETE'); self.assertNotEqual(result['returncode'], 0)
                self.assertFalse((fixture.root/'work').exists())
                stderr = fixture.root/'receipts-first/recipe.stderr'
                self.assertIn(b'FileNotFoundError' if kind == 'missing' else b'AssertionError', stderr.read_bytes())
                self.assertEqual(result['streams']['stderr']['sha256'], sha(stderr.read_bytes()))

    def test_reversed_patch_order_preserves_failed_patch_stream_and_partial_tree(self):
        self.fixture.body['patches'].reverse(); self.fixture.body['stages'].reverse(); self.fixture.save_manifest()
        result = self.fixture.run()
        self.assertEqual(result['status'], 'INCOMPLETE'); self.assertEqual(result['returncode'], 1)
        original = json.loads((self.root/'work/receipts/prepared.json').read_text())
        self.assertEqual(original['status'], 'INCOMPLETE'); self.assertEqual(original['stages'], [])
        failure = self.root/'work/receipts/1-check.stderr'
        self.assertIn(b'patch does not apply', failure.read_bytes())
        self.assertEqual((self.root/'work/historical/tools/qa/precip_models.js').read_bytes(), self.fixture.raw['tools/qa/precip_models.js'])

    def test_wrong_second_stage_postimage_retains_completed_first_stage(self):
        self.fixture.body['stages'][1]['files']['tools/qa/precip_models.js']['sha256'] = '0'*64
        self.fixture.save_manifest()
        result = self.fixture.run()
        self.assertEqual(result['status'], 'INCOMPLETE'); self.assertEqual(result['returncode'], 1)
        original = json.loads((self.root/'work/receipts/prepared.json').read_text())
        self.assertEqual(original['stages'], self.fixture.body['stages'][:1])
        self.assertTrue((self.root/'work/receipts/2-apply.stdout').is_file())
        self.assertIn(b'AssertionError', (self.root/'receipts-first/recipe.stderr').read_bytes())

    def test_existing_outputs_and_receipts_are_never_rewritten(self):
        first = self.fixture.run(); prepared = Path(first['preparedReceipt']['path']); before = prepared.read_bytes()
        result = self.fixture.run('retry')
        self.assertEqual(result['status'], 'INCOMPLETE'); self.assertNotEqual(result['returncode'], 0)
        self.assertTrue(result['outputPreexisted'])
        self.assertEqual(prepared.read_bytes(), before)
        self.assertIn(b'fresh output required', (self.root/'receipts-retry/recipe.stderr').read_bytes())
        receipt = (self.root/'receipts-retry/process.json').read_bytes()
        with self.assertRaises(ValueError): self.fixture.run('retry')
        self.assertEqual((self.root/'receipts-retry/process.json').read_bytes(), receipt)

    def test_cached_bytecode_cannot_replace_verified_profile_source(self):
        source = self.fixture.research/'tools/qa/r0040/pack_design.py'
        cache = Path(importlib.util.cache_from_source(str(source))); cache.parent.mkdir()
        header = importlib.util.MAGIC_NUMBER+struct.pack('<III', 0, int(source.stat().st_mtime), source.stat().st_size)
        cache.write_bytes(header+marshal.dumps(compile('PROFILE={"poisoned":True}', str(source), 'exec')))
        result = self.fixture.run()
        self.assertEqual(result['status'], 'PREPARED')
        self.assertIn('-I', result['argv']); self.assertIn('-B', result['argv'])
        self.assertTrue(any(arg.startswith('pycache_prefix=') for arg in result['argv']))

    def test_optimized_python_refuses_before_source_mutation(self):
        args = self.fixture.args()
        argv = [sys.executable, '-O', str(HERE/'r0040_capture_prepare.py')]
        for name in ('manifest', 'research', 'historical', 'main', 'out', 'receipts'):
            argv += ['--'+name, str(getattr(args, name))]
        run = subprocess.run(argv, capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('optimized Python', run.stderr)
        self.assertFalse(args.out.exists())

    def test_terminal_fsync_failure_cannot_publish_a_prepared_process_receipt(self):
        original_fsync = os.fsync
        def fail_terminal(fd):
            if 'process.json' in Path(os.readlink('/proc/self/fd/'+str(fd))).name:
                raise OSError('injected terminal process fsync failure')
            return original_fsync(fd)
        with patch.object(M.os, 'fsync', side_effect=fail_terminal), self.assertRaisesRegex(OSError, 'terminal process fsync'):
            self.fixture.run()
        self.assertFalse((self.root/'receipts-first/process.json').exists())
        self.assertEqual(json.loads((self.root/'work/receipts/prepared.json').read_text())['status'], 'PREPARED')
        self.assertTrue((self.root/'receipts-first/recipe.stdout').is_file())

    def test_timeout_retains_streams_and_kills_the_process_group(self):
        receipt = {'returncode': None, 'timedOut': False}
        code = ('import os,time,pathlib; child=os.fork(); '
                'pathlib.Path("child-pid").write_text(str(child)) if child else None; '
                'print("partial stdout",flush=True); time.sleep(30)')
        M.run_child([sys.executable, '-c', code], b'', self.root, self.root/'stdout', self.root/'stderr', receipt, 0.5)
        self.assertTrue(receipt['timedOut']); self.assertNotEqual(receipt['returncode'], 0)
        self.assertIn(b'partial stdout', (self.root/'stdout').read_bytes())
        child = int((self.root/'child-pid').read_text()); stat = Path('/proc')/str(child)/'stat'
        self.assertTrue(not stat.exists() or stat.read_text().split()[2] == 'Z')


if __name__ == '__main__': unittest.main(verbosity=2)
