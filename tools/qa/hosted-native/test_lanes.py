#!/usr/bin/env python3
"""Offline preparation/admission controls. No browser is imported or launched."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def module(name):
    path = HERE / (name + '.py')
    if not path.is_file():
        raise AssertionError(name + ' entry has not been implemented')
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PreparationControls(unittest.TestCase):
    def test_shallow_partial_baseline_stays_real_and_clean_without_available_remote(self):
        """The hosted clone tried to transfer omitted archive blobs after networking was removed."""
        prepare = module('prepare')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); origin = root/'origin'; origin.mkdir()
            env = {**os.environ, 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_TERMINAL_PROMPT': '0'}
            def git(cwd, *args):
                return subprocess.check_output(['git', *args], cwd=cwd, env=env, stderr=subprocess.PIPE, text=True).strip()
            git(origin, 'init', '-q'); git(origin, 'config', 'uploadpack.allowFilter', 'true')
            for name in ('required', 'source-only', 'omitted-archive'):
                (origin/name).write_text(name+' source bytes\n')
            git(origin, 'add', '.')
            git(origin, '-c', 'user.name=Control', '-c', 'user.email=control.invalid', 'commit', '-qm', 'fixture')
            baseline = root/'partial'
            git(root, 'clone', '--filter=blob:none', '--depth', '1', '--no-checkout', origin.as_uri(), str(baseline))
            git(baseline, 'sparse-checkout', 'set', '--no-cone', '/required', '/source-only')
            git(baseline, 'checkout', '--detach', 'HEAD')
            self.assertEqual(git(baseline, 'rev-parse', '--is-shallow-repository'), 'true')
            head, tree = git(baseline, 'rev-parse', 'HEAD'), git(baseline, 'rev-parse', 'HEAD^{tree}')
            origin.rename(root/'origin-unavailable')
            main, receipts = root/'main', root/'receipts'; receipts.mkdir()
            prepare.detached_sparse_baseline(baseline, main, head, ['/required'], prepare.Commands(receipts), root)
            self.assertEqual(prepare.git_identity(main, head, tree)['commit'], head)
            self.assertEqual((main/'required').read_text(), 'required source bytes\n')
            self.assertFalse((main/'omitted-archive').exists())
            self.assertFalse((main/'source-only').exists())
            self.assertEqual((baseline/'source-only').read_text(), 'source-only source bytes\n')
            self.assertEqual(prepare.git_identity(baseline, head, tree)['tree'], tree)

    def test_changed_inventory_payload_is_rejected(self):
        """Dropping generated-file verification would admit changed served bytes."""
        prepare = module('prepare')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'index.html').write_bytes(b'original generated entry')
            inventory = {'schema': 'salah-generated-inventory/1', 'generator': 'tools/build_native.py',
                         'fileCount': 1, 'byteCount': 24,
                         'files': {'index.html': {'bytes': 24, 'sha256': sha(root / 'index.html')}}}
            (root / 'GENERATED.json').write_text(json.dumps(inventory))
            pins = {'index.html': sha(root / 'index.html'), 'GENERATED.json': sha(root / 'GENERATED.json')}
            prepare.verify_generated(root, pins)
            (root / 'index.html').write_bytes(b'mutated generated entry!')
            with self.assertRaises(ValueError):
                prepare.verify_generated(root, pins)

    def test_source_identity_rejects_dirty_and_wrong_head(self):
        """Checking HEAD alone would admit an uncommitted recipe or owner change."""
        prepare = module('prepare')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = {**os.environ, 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1'}
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], env=env, stderr=subprocess.DEVNULL, text=True).strip()
            git('init', '-q')
            (root / 'source').write_text('original')
            git('add', 'source')
            git('-c', 'user.name=Control', '-c', 'user.email=control.invalid', 'commit', '-qm', 'fixture')
            head, tree = git('rev-parse', 'HEAD'), git('rev-parse', 'HEAD^{tree}')
            self.assertEqual(prepare.git_identity(root, head, tree)['commit'], head)
            with self.assertRaises(ValueError):
                prepare.git_identity(root, '0' * 40, tree)
            (root / 'source').write_text('uncommitted change')
            with self.assertRaises(ValueError):
                prepare.git_identity(root, head, tree)

    def test_real_rain_patch_and_preimage_refusal(self):
        """Applying an option patch to the wrong owner must fail before mutation."""
        prepare = module('prepare')
        patch = ROOT / 'docs/state-contracts/evidence/R0040/phase1-options.patch.gz'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'src/native').mkdir(parents=True)
            target = root / 'src/native/index.html'
            target.write_bytes((ROOT / 'src/native/index.html').read_bytes())
            prepare.apply_rain_patch(root, patch)
            self.assertEqual(sha(target), 'f83c4a729d0f0798bd234fb7b531c0a5bf2b767194b50de7a0b6bc71a6e07084')
            prior = target.read_bytes()
            with self.assertRaises(ValueError):
                prepare.apply_rain_patch(root, patch)
            self.assertEqual(target.read_bytes(), prior)
            self.assertEqual(sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()), ['src/native/index.html'])

    def test_preparation_refuses_reuse_without_rewriting_failure(self):
        """A second invocation must never replace the first failed run's receipt."""
        module('prepare')
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'used'
            output.mkdir()
            receipt = output / 'failure.json'
            receipt.write_bytes(b'{"status":"FAIL","original":true}\n')
            before = receipt.read_bytes()
            run = subprocess.run([sys.executable, str(HERE / 'prepare.py'), '--research', str(ROOT),
                                  '--baseline', str(ROOT), '--historical', str(ROOT), '--out', str(output)],
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(receipt.read_bytes(), before)
            self.assertEqual([p.name for p in output.iterdir()], ['failure.json'])


class LaneControls(unittest.TestCase):
    def setUp(self):
        self.lanes = module('lanes')
        self.base = Path('/private/control')
        self.prepared = {'schemaVersion': 1, 'protocol': 'salah-hosted-native-preparation/1', 'status': 'PREPARED',
                         'sources': {'research': {'root': '/sources/research', 'commit': '55d1b3edb66d2c35679707120b01ee1d3455e4a3'},
                                     'baseline': {'root': '/sources/main', 'commit': 'df644ef60156b67b5c487395176369bcec7a0d7b'},
                                     'historical': {'root': '/sources/history'}},
                         'trees': {name: {'root': '/private/prepared/trees/' + name} for name in ('main', 'r0035', 'r0040', 'r003f')}}

    def plan(self, **kwargs):
        return self.lanes.make_plan(self.prepared, self.base, python_playwright=Path('/dependencies/venv/bin/python'),
                                    node=Path('/dependencies/node'), node_modules=Path('/dependencies/node_modules'),
                                    pngjs=Path('/dependencies/node_modules/pngjs'), **kwargs)

    def test_declared_commands_use_real_cli_and_private_outputs(self):
        """Wrong positional order or --dpr=1 would invoke the wrong existing recipe."""
        plan = self.plan()
        self.assertTrue(plan['sequential'])
        self.assertEqual([lane['workOrder'] for lane in plan['lanes']], ['R0040', 'R003F', 'R0035', 'R0035'])
        rain, moon, timing, capture = plan['lanes']
        self.assertEqual(rain['argv'], ['/dependencies/node', '/sources/research/tools/qa/r0040/native-options.cjs',
                                      '/dependencies/node_modules/playwright', '/sources/history',
                                      '/private/prepared/trees/r0040', rain['output'], 'chromium'])
        self.assertEqual(moon['argv'][-4:], ['--playwright', '/dependencies/node_modules/playwright', '--pngjs', '/dependencies/node_modules/pngjs'])
        self.assertEqual(moon['argv'][moon['argv'].index('--dpr') + 1], '1')
        for lane in plan['lanes']:
            for key in ('output', 'stdout', 'stderr'):
                self.assertTrue(Path(lane[key]).is_relative_to(self.base))
            self.assertGreater(lane['timeoutSeconds'], 0)
            self.assertEqual(lane['env']['NODE_PATH'], '/dependencies/node_modules')
        self.assertEqual(timing['argv'][0], '/dependencies/venv/bin/python')
        self.assertNotIn('--capture', timing['argv'])
        self.assertIn('--capture', capture['argv'])
        self.assertNotEqual(timing['output'], capture['output'])
        self.assertEqual(capture['dependsOn'], [timing['id']])
        self.assertEqual(moon['exitStatuses']['3'], 'ISOLATION FAIL')
        self.assertEqual(moon['exitStatuses']['4'], 'ANDON')
        self.assertEqual(moon['stopScopeOnAndon'], 'R003F')

    def test_star_arms_share_build_and_correct_active_predicate(self):
        """Independent roots, guessed active predicates or changed scene flags invalidate comparison."""
        plan = self.plan()
        stars = plan['r0035Plan']
        self.assertEqual(stars['kind'], 'independent-reconstruction')
        self.assertEqual(stars['arms']['main']['flags'], '')
        full, changed = (stars['arms'][name] for name in ('unmodified', 'mitigated'))
        self.assertEqual(full['root'], changed['root'])
        self.assertEqual(full['commit'], changed['commit'])
        self.assertEqual(full['producerProbe'], {'path': 'stars.status', 'equals': 'active'})
        self.assertEqual(changed['producerProbe'], full['producerProbe'])
        sys.path.insert(0, str(ROOT / 'tools/r0035'))
        try:
            import native_trials
            native_trials.verify_reconstructed_flags(stars['arms'])
            for name, arm in stars['arms'].items():
                native_trials.producer_flags(name, arm['flags'], True)
        finally:
            sys.path.pop(0)
        self.assertEqual(full['flags'], '&r35arm=full&r35scope=all&r35amplitude=1&r35glass=0.5&r35margin=4')
        for lane in plan['lanes'][2:]:
            values = dict(zip(lane['argv'][4::2], lane['argv'][5::2]))
            self.assertEqual(values['--rounds'], '1')
            self.assertEqual(values['--seconds'], '15')
            self.assertEqual(values['--clock'], 'ordinary')
            self.assertEqual(values['--scene'], 'dark')
            self.assertEqual(values['--motion'], 'normal')

    def test_engine_and_dpr_do_not_silently_change_other_recipes(self):
        """A DPR2 label cannot be assigned to drivers whose existing CLI fixes DPR1."""
        plan = self.plan(engine='firefox', r003f_dpr=2)
        rain, moon, timing, _ = plan['lanes']
        self.assertEqual(rain['argv'][-1], 'firefox')
        self.assertEqual(moon['argv'][moon['argv'].index('--dpr') + 1], '2')
        self.assertEqual(timing['argv'][timing['argv'].index('--engine') + 1], 'firefox')
        self.assertEqual(rain['dpr'], 1)
        self.assertEqual(timing['dpr'], 1)
        self.assertEqual(moon['dpr'], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
