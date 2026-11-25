#!/usr/bin/env python3
"""Offline preparation/admission controls. No browser is imported or launched."""
import hashlib
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

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
    def test_runtime_subset_needs_no_omitted_promisor_blob(self):
        """Even a path-selected git archive fetched omitted blobs on the hosted runner."""
        prepare = module('prepare')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); origin = root/'origin'; origin.mkdir()
            env = {**os.environ, 'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_TERMINAL_PROMPT': '0'}
            def git(cwd, *args):
                return subprocess.check_output(['git', *args], cwd=cwd, env=env, stderr=subprocess.PIPE, text=True).strip()
            git(origin, 'init', '-q'); git(origin, 'config', 'uploadpack.allowFilter', 'true')
            (origin/'runtime').mkdir()
            (origin/'runtime/required').write_text('exact served runtime\n')
            (origin/'omitted-archive').write_text('not acquired and not needed\n')
            git(origin, 'add', '.')
            git(origin, '-c', 'user.name=Control', '-c', 'user.email=control.invalid', 'commit', '-qm', 'fixture')
            source = root/'partial'
            git(root, 'clone', '--filter=blob:none', '--depth', '1', '--no-checkout', origin.as_uri(), str(source))
            git(source, 'sparse-checkout', 'set', '--no-cone', '/runtime/')
            git(source, 'checkout', '--detach', 'HEAD')
            head, tree = git(source, 'rev-parse', 'HEAD'), git(source, 'rev-parse', 'HEAD^{tree}')
            origin.rename(root/'origin-unavailable')
            destination = root/'served'
            with patch.object(prepare, 'BASELINE', head), patch.object(prepare, 'RUNTIME_PATHS', ('runtime',)):
                rows = prepare.materialize_runtime(source, destination)
            self.assertEqual(set(rows), {'runtime/required'})
            self.assertEqual((destination/'runtime/required').read_text(), 'exact served runtime\n')
            self.assertEqual(rows['runtime/required']['gitBlob'], git(source, 'rev-parse', 'HEAD:runtime/required'))
            self.assertEqual(prepare.git_identity(source, head, tree)['tree'], tree)
            self.assertFalse((destination/'omitted-archive').exists())

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

    def rain_admission(self):
        manifest = json.loads((ROOT/'docs/state-contracts/evidence/R0040/native-capture-preflight.json').read_text())
        return {'status': 'PASS', 'work': '/private/work/rain-capture',
                'manifest': str(ROOT/'docs/state-contracts/evidence/R0040/native-capture-preflight.json'),
                'prepared': '/private/work/rain-capture/receipts/prepared.json',
                'process': '/private/control/rain-preparation/process.json',
                'wrapperSha256': 'd252e345225c0d3565c0c2a321324ca206083ba371eb43654193d422f9b2235f',
                'expectedCapture': manifest['plannedNativeCell']['expectedCapture'], 'pins': manifest['pins']}

    def test_capture_plan_uses_exact_revised_cell_and_separate_private_retention(self):
        admission = self.rain_admission()
        original = self.plan()
        plan = self.plan(r0040_mode='capture', r0040_preparation=admission)
        self.assertEqual(plan['r0040Mode'], 'capture')
        rain = plan['lanes'][0]
        self.assertEqual(plan['lanes'][1:], original['lanes'][1:])
        self.assertEqual(rain['id'], 'r0040-chromium-capture')
        self.assertEqual(rain['timeoutSeconds'], 180)
        expected = ['/dependencies/node', str(HERE/'retain_r0040_capture.cjs'),
                    '--driver', '/sources/research/tools/qa/r0040/capture.cjs',
                    '--manifest', admission['manifest'], '--prepared', admission['prepared'],
                    '--preparation-process', admission['process'], '--evidence', rain['evidenceRetention']['output'],
                    '--', '/dependencies/node_modules/playwright', '/private/work/rain-capture/historical',
                    '/private/prepared/trees/main', rain['output'], 'chromium', 'bday', 'moderate', 'M1']
        self.assertEqual(rain['argv'], expected)
        self.assertEqual(rain['env']['R0040_DISPERSION'], 'common')
        self.assertEqual(rain['clearEnv'], ['R0040_OPTIONS'])
        self.assertNotIn('R0040_OPTIONS', rain['env'])
        self.assertEqual(rain['stopAllOnExit'], [86])
        self.assertEqual(rain['result']['kind'], 'r0040-capture')
        self.assertEqual(rain['result']['path'], str(Path(rain['output'])/'capture.json'))
        self.assertEqual(rain['result']['expectedCapture'], admission['expectedCapture'])
        for name in ('output', 'stdout', 'stderr'):
            self.assertTrue(Path(rain[name]).is_relative_to(self.base))
        self.assertTrue(Path(rain['result']['finalAdmissionPath']).is_relative_to(self.base))
        self.assertNotEqual(Path(rain['result']['finalAdmissionPath']).parent, Path(rain['output']))
        self.assertNotIn('--capture', rain['argv'])
        self.assertEqual(self.plan(r0040_mode='capture', r0040_preparation=admission,
                                   retain_evidence=True)['lanes'][0]['argv'], expected)

    def test_capture_missing_or_failed_preparation_blocks_only_rain(self):
        original = self.plan(include_r002f=True)
        for admission in (None, {'status': 'INCOMPLETE', 'reason': 'missing historical model'}):
            plan = self.plan(include_r002f=True, r0040_mode='capture', r0040_preparation=admission)
            self.assertEqual(plan['lanes'][1:], original['lanes'][1:])
            self.assertEqual(plan['lanes'][0]['preparation']['status'], 'INCOMPLETE')
            self.assertEqual(plan['lanes'][0]['argv'], [])
        for change in ({'r0040_mode': 'capture', 'engine': 'webkit'},
                       {'r0040_mode': 'capture', 'work_orders': ['R0035']},
                       {'r0040_mode': True}, {'r0040_mode': 'lossless-pass'}):
            with self.assertRaises(ValueError): self.plan(**change)

    def test_capture_admission_requires_both_process_levels_and_complete_source_checks(self):
        manifest_path = ROOT/'docs/state-contracts/evidence/R0040/native-capture-preflight.json'
        manifest = json.loads(manifest_path.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); work = root/'work'; process = root/'process.json'; entry = root/'entry.json'
            successful = {'protocol': 'r0040-capture-preparation-entry/1', 'returncode': 0, 'timedOut': False,
                          'wrapperSha256': sha(HERE/'r0040_capture_prepare.py')}
            child = {'protocol': 'r0040-capture-preparation-process/1', 'status': 'PREPARED',
                     'returncode': 0, 'timedOut': False, 'nativeStatus': 'NOT_RUN',
                     'inputs': {'manifest': str(manifest_path), 'research': '/sources/research',
                                'historical': '/sources/history', 'main': '/private/prepared/trees/main', 'out': str(work)}}
            checked = {'sources': {'historical': manifest['stages'][-1]['files'],
                                   'research': manifest['researchInputs'], 'main': manifest['main']['runtimeFiles']},
                       'custody': {'manifestSha256': self.lanes.R0040_MANIFEST_SHA256}}
            def admit():
                return self.lanes.admit_r0040(self.prepared, work, process, entry, self.base,
                                              Path('/dependencies/node'), Path('/dependencies/node_modules/playwright'))
            process.write_text(json.dumps(child)); entry.write_text(json.dumps(successful))
            with patch.object(self.lanes.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=json.dumps(checked), stderr='')) as verify:
                result = admit()
                self.assertEqual(result['status'], 'PASS', result)
                self.assertEqual(result['verifiedPopulation'], {'historical': 6, 'research': 12, 'main': 177})
                command = verify.call_args.args[0]
                self.assertIn('verifySources', command[2])
                self.assertIn(str(HERE/'retain_r0040_capture.cjs'), command)
                self.assertEqual(verify.call_args.kwargs['env']['R0040_DISPERSION'], 'common')
                self.assertNotIn('R0040_OPTIONS', verify.call_args.kwargs['env'])
            for body in ({**successful, 'returncode': 2}, {**successful, 'returncode': False},
                         {**successful, 'timedOut': True}, {**successful, 'protocol': 'wrong'}):
                entry.write_text(json.dumps(body))
                with patch.object(self.lanes.subprocess, 'run') as verify:
                    self.assertEqual(admit()['status'], 'INCOMPLETE'); verify.assert_not_called()
            entry.write_text(json.dumps(successful))
            for body in ({**child, 'returncode': 1}, {**child, 'timedOut': True}, {**child, 'status': 'INCOMPLETE'}):
                process.write_text(json.dumps(body))
                with patch.object(self.lanes.subprocess, 'run') as verify:
                    self.assertEqual(admit()['status'], 'INCOMPLETE'); verify.assert_not_called()
            process.write_text(json.dumps(child))
            for group in ('historical', 'research', 'main'):
                partial = copy.deepcopy(checked); partial['sources'][group].pop(next(iter(partial['sources'][group])))
                with patch.object(self.lanes.subprocess, 'run', return_value=SimpleNamespace(returncode=0, stdout=json.dumps(partial), stderr='')):
                    self.assertEqual(admit()['status'], 'INCOMPLETE')
            with patch.object(self.lanes.subprocess, 'run', return_value=SimpleNamespace(returncode=1, stdout='', stderr='actual source drift')):
                self.assertEqual(admit()['status'], 'INCOMPLETE')
            with patch.object(self.lanes.subprocess, 'run', side_effect=subprocess.TimeoutExpired(
                    'source guard', 90, output=b'partial source receipt', stderr=b'partial source diagnostic')):
                timed = admit()
                self.assertEqual(timed['status'], 'INCOMPLETE')
                self.assertEqual(timed['sourceCheck']['stdout'], 'partial source receipt')
                self.assertEqual(timed['sourceCheck']['stderr'], 'partial source diagnostic')

    def test_capture_sparse_checkout_contains_every_historical_and_orchestration_input(self):
        workflow = (ROOT/'.github/workflows/research-native-pilot.yml').read_text()
        historical = workflow.split('path: historical', 1)[1].split('- name:', 1)[0]
        manifest = json.loads((ROOT/'docs/state-contracts/evidence/R0040/native-capture-preflight.json').read_text())
        for name in manifest['historical']['files']:
            self.assertIn('/'+name+'\n', historical)
        orchestration = workflow.split('path: orchestration', 1)[1].split('- name:', 1)[0]
        for name in ('docs/state-contracts/R0040-native-capture-preflight.md',
                     'docs/state-contracts/evidence/R0040/native-capture-preflight.json',
                     'docs/state-contracts/evidence/R0040/native-capture-preparation-controls.json'):
            self.assertIn('/'+name+'\n', orchestration)

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

    def test_selection_keeps_both_star_lanes_and_omits_unselected_workstreams(self):
        plan = self.plan(work_orders=['R0035'])
        self.assertEqual(plan['workOrders'], ['R0035'])
        self.assertEqual([row['id'] for row in plan['lanes']],
                         ['r0035-chromium-timing', 'r0035-chromium-capture'])
        self.assertEqual(plan['lanes'][1]['dependsOn'], [plan['lanes'][0]['id']])
        self.assertFalse(plan['evidenceRetention'])
        plan = self.plan(work_orders=['R002F', 'R0040'], include_r002f=True)
        self.assertEqual([row['workOrder'] for row in plan['lanes']], ['R0040', 'R002F'])
        self.assertEqual(plan['lanes'][-1]['preparation']['status'], 'INCOMPLETE')

    def test_guard_off_is_a_shared_diagnostic_change_with_original_admission(self):
        original = self.plan(work_orders=['R0035'])
        diagnostic = self.plan(work_orders=['R0035'], r0035_guard='off', r0035_mode='timing')
        self.assertEqual([row['id'] for row in diagnostic['lanes']], ['r0035-chromium-timing'])
        self.assertEqual(diagnostic['lanes'][0], original['lanes'][0])
        self.assertEqual(diagnostic['r0035Plan']['arms']['main'], original['r0035Plan']['arms']['main'])
        for arm in ('unmodified', 'mitigated'):
            before, after = original['r0035Plan']['arms'][arm], diagnostic['r0035Plan']['arms'][arm]
            self.assertEqual(after, {**before, 'flags': before['flags']+'&r35guard=off'})
            self.assertEqual(after['producerProbe'], {'path': 'stars.status', 'equals': 'active'})
        sys.path.insert(0, str(ROOT/'tools/r0035'))
        try:
            import native_trials
            native_trials.verify_reconstructed_flags(diagnostic['r0035Plan']['arms'])
            for name, arm in diagnostic['r0035Plan']['arms'].items():
                native_trials.producer_flags(name, arm['flags'], True)
        finally:
            sys.path.pop(0)

    def test_corrected_moon_plan_keeps_original_runtime_and_requires_admitted_helpers(self):
        original = self.plan(work_orders=['R003F'])['lanes'][0]
        missing = self.plan(work_orders=['R003F'], r003f_harness='corrected-b0')['lanes'][0]
        self.assertEqual(missing['argv'], [])
        self.assertEqual(missing['preparation']['status'], 'INCOMPLETE')
        admission = {'status': 'PASS', 'root': '/private/work/corrected-b0',
                     'harness': {'protocol': 'R003F/corrected-harness/1'}}
        plan = self.plan(work_orders=['R003F'], r003f_harness='corrected-b0', r003f_preparation=admission)
        corrected = plan['lanes'][0]
        self.assertEqual(plan['r003fHarness'], 'corrected-b0')
        self.assertEqual(corrected['argv'][1], '/private/work/corrected-b0/tools/qa/r003f_owner_baseline.cjs')
        self.assertEqual(corrected['argv'][2:], original['argv'][2:])
        self.assertEqual(corrected['result']['expectedHarness'], admission['harness'])
        for key in ('timeoutSeconds', 'exitStatuses', 'stopAllOnExit', 'stopScopeOnAndon'):
            self.assertEqual(corrected[key], original[key])
        with self.assertRaises(ValueError): self.plan(work_orders=['R0040'], r003f_harness='corrected-b0')

    def test_corrected_moon_admission_rechecks_exact_materialization_and_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); target = root/'corrected'; process = root/'process.json'
            built = subprocess.run(['node', str(HERE/'r003f_materialize.cjs'), '--source', str(ROOT), '--out', str(target)],
                                   capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            process.write_text(json.dumps({'returncode': 0, 'timedOut': False}))
            receipt = target/'materialization.json'
            admitted = self.lanes.admit_r003f(receipt, process)
            self.assertEqual(admitted['status'], 'PASS', admitted)
            self.assertEqual(admitted['root'], str(target))
            self.assertEqual(admitted['harness']['materializationSha256'], sha(receipt))
            for status in ({'returncode': 2, 'timedOut': False}, {'returncode': 0, 'timedOut': True},
                           {'returncode': False, 'timedOut': False}, {'returncode': 0}):
                process.write_text(json.dumps(status))
                self.assertEqual(self.lanes.admit_r003f(receipt, process)['status'], 'INCOMPLETE')
            process.write_text(json.dumps({'returncode': 0, 'timedOut': False}))
            helper=target/'tools/qa/r003f_capture.cjs'; original=helper.read_bytes()
            helper.write_bytes(original+b'\n// drift\n')
            self.assertEqual(self.lanes.admit_r003f(receipt, process)['status'], 'INCOMPLETE')
            helper.write_bytes(original)
            moved=root/'elsewhere.cjs'; helper.rename(moved); helper.symlink_to(moved)
            self.assertEqual(self.lanes.admit_r003f(receipt, process)['status'], 'INCOMPLETE')
            helper.unlink(); moved.rename(helper)
            original_receipt=receipt.read_bytes(); receipt.write_text('{"status":"PREPARED"}')
            self.assertEqual(self.lanes.admit_r003f(receipt, process)['status'], 'INCOMPLETE')
            receipt.write_bytes(original_receipt)
            self.assertEqual(self.lanes.admit_r003f(receipt, None)['status'], 'INCOMPLETE')
            self.assertEqual(self.lanes.admit_r003f(receipt, process)['status'], 'PASS')

    def test_diagnostic_population_and_scope_do_not_create_phantom_dependencies(self):
        plan = self.plan(work_orders=['R0035'], r0035_mode='capture', r0035_scope='preview-members')
        self.assertEqual([row['id'] for row in plan['lanes']], ['r0035-chromium-capture'])
        self.assertEqual(plan['lanes'][0]['dependsOn'], [])
        self.assertNotIn('dependencyPolicy', plan['lanes'][0])
        for name in ('unmodified', 'mitigated'):
            self.assertIn('&r35scope=preview-members&', plan['r0035Plan']['arms'][name]['flags'])
        for controls in ({'r0035_guard': True}, {'r0035_guard': 'ignore'}, {'r0035_scope': 'bright'},
                         {'r0035_mode': ''}, {'r0035_mode': ['timing']}):
            with self.subTest(controls=controls), self.assertRaises(ValueError):
                self.plan(work_orders=['R0035'], **controls)
        with self.assertRaises(ValueError):
            self.plan(work_orders=['R0040'], r0035_guard='off')

    def test_selection_rejects_empty_unknown_duplicate_and_contradictory_orders(self):
        for orders in ([], ['R0035', 'R0035'], ['R9999'], 'R0035', [35], [None]):
            with self.subTest(orders=orders), self.assertRaises(ValueError):
                self.plan(work_orders=orders)
        for orders, enabled in ((['R002F'], False), (['R0040'], True)):
            with self.subTest(orders=orders, enabled=enabled), self.assertRaises(ValueError):
                self.plan(work_orders=orders, include_r002f=enabled)
        for retention in ('yes', 1, None):
            with self.subTest(retention=retention), self.assertRaises(ValueError):
                self.plan(retain_evidence=retention)

    def test_retention_preserves_original_argv_results_and_separate_private_outputs(self):
        original = self.plan(include_r002f=True)
        retained = self.plan(include_r002f=True, retain_evidence=True)
        self.assertFalse(original['evidenceRetention'])
        self.assertTrue(retained['evidenceRetention'])
        self.assertEqual(original['workOrders'], ['R0040', 'R003F', 'R0035', 'R002F'])
        destinations = []
        for before, after in zip(original['lanes'], retained['lanes']):
            if before['workOrder'] not in ('R0040', 'R0035'):
                self.assertEqual(before, after)
                continue
            self.assertEqual(before['result'], after['result'])
            for key in ('output', 'stdout', 'stderr', 'cwd', 'env', 'dependsOn', 'timeoutSeconds'):
                self.assertEqual(before[key], after[key])
            argv = after['argv']; evidence = after['evidenceRetention']
            self.assertEqual(argv[0], before['argv'][0])
            self.assertEqual(argv[argv.index('--driver')+1], before['argv'][1])
            self.assertEqual(argv[argv.index('--')+1:], before['argv'][2:])
            wrapper = 'retain_r0040.cjs' if before['workOrder'] == 'R0040' else 'retain_r0035.py'
            self.assertEqual(argv[1], str(HERE/wrapper))
            self.assertEqual(evidence['originalArgv'], before['argv'])
            self.assertIs(evidence['instrumented'], True)
            self.assertIs(evidence['timingComparableToOriginal'], False)
            self.assertIn('fsync', evidence['overhead'])
            self.assertEqual(argv[argv.index('--evidence')+1], evidence['output'])
            self.assertTrue(Path(evidence['output']).is_relative_to(self.base))
            self.assertNotEqual(evidence['output'], after['output'])
            self.assertEqual(after['stopAllOnExit'], [86])
            self.assertEqual(after['exitStatuses']['86'], 'EXTERNAL_CONTINUATION_VETOED')
            destinations.append(evidence['output'])
        self.assertEqual(len(set(destinations)), 3)

    def test_r002f_uses_exact_probe_and_disposable_arms_with_private_outputs(self):
        admission = {'status': 'PASS', 'receipt': {'path': '/private/r002f-build/build-result.json', 'sha256': 'a'*64},
                     'trees': {'baseline': {'root': '/private/r002f-build/baseline'},
                               'candidate': {'root': '/private/r002f-build/candidate'}}}
        ordinary = self.plan(engine='webkit', r003f_dpr=2)
        plan = self.plan(engine='webkit', r003f_dpr=2, include_r002f=True, r002f_preparation=admission,
                         r002f_dpr=3, r002f_rounds=2, r002f_section='preview')
        self.assertEqual(plan['lanes'][:4], ordinary['lanes'])
        lane = plan['lanes'][-1]
        self.assertEqual(lane['id'], 'r002f-webkit-dpr3')
        self.assertEqual(lane['workOrder'], 'R002F')
        self.assertEqual(lane['argv'][:2], ['/dependencies/node', str(HERE/'r002f_probe.cjs')])
        values = dict(zip(lane['argv'][2::2], lane['argv'][3::2]))
        self.assertEqual(values, {'--playwright': '/dependencies/node_modules/playwright',
                                 '--baseline': '/private/r002f-build/baseline',
                                 '--candidate': '/private/r002f-build/candidate', '--out': lane['output'],
                                 '--engine': 'webkit', '--dpr': '3', '--rounds': '2',
                                 '--section': 'preview', '--timeout-ms': '60000'})
        for key in ('output', 'stdout', 'stderr'):
            self.assertTrue(Path(lane[key]).is_relative_to(self.base))
        self.assertEqual(lane['timeoutSeconds'], 900)
        self.assertEqual(lane['result']['path'], str(Path(lane['output'])/'result.json'))
        self.assertEqual(lane['result']['expectedObserverSha256'],
                         '673c0656d8e2d8e1c343d1258be5070fa9447f3f43878460791ea8570468558f')
        self.assertEqual(lane['result']['expectedRounds'], 2)
        self.assertEqual(lane['result']['expectedSection'], 'preview')
        self.assertFalse(Path(values['--candidate']).is_relative_to(self.base))

    def test_failed_or_missing_r002f_preparation_emits_explicit_blocked_lane(self):
        ordinary = self.plan()
        for admission in (None, {'status': 'INCOMPLETE', 'reason': 'controlled preparation failure'}):
            plan = self.plan(include_r002f=True, r002f_preparation=admission)
            self.assertEqual(plan['lanes'][:4], ordinary['lanes'])
            lane = plan['lanes'][-1]
            self.assertEqual(lane['workOrder'], 'R002F')
            self.assertEqual(lane['preparation']['status'], 'INCOMPLETE')
            self.assertEqual(lane['argv'], [])

    def test_r002f_preparation_admission_rejects_missing_or_status_only_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'build-result.json'
            for data in (None, {'status': 'PASS'}, {'protocol': 'r002f-hosted-build/1', 'status': 'PASS'}):
                if data is not None: path.write_text(json.dumps(data))
                admission = self.lanes.admit_r002f(path)
                self.assertEqual(admission['status'], 'INCOMPLETE')
                self.assertIn('reason', admission)

    def test_r002f_preparation_admission_rechecks_both_actual_generated_trees(self):
        from r002f_prepare import BASE_COMMIT, RESEARCH_COMMIT, BASE_INDEX, COMBINED_INDEX, BASE_INVENTORY, COMBINED_INVENTORY, PATCH
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); path = root/'build-result.json'
            body = {'protocol': 'r002f-hosted-build/1', 'status': 'PASS', 'baseProvenance': BASE_COMMIT,
                    'researchProvenance': RESEARCH_COMMIT, 'wrapperSha256': sha(HERE/'r002f_prepare.py'),
                    'patch': {'patch': PATCH}, 'arms': {}}
            for arm, index, inventory in (('baseline', BASE_INDEX, BASE_INVENTORY), ('candidate', COMBINED_INDEX, COMBINED_INVENTORY)):
                (root/arm).mkdir()
                body['arms'][arm] = {'path': arm, 'indexSha256': index, 'inventorySha256': inventory,
                                     'builds': [{'indexSha256': index}, {'indexSha256': index, 'written': 0, 'removed': 0, 'unchanged': 117}]}
            path.write_text(json.dumps(body))
            with patch.object(self.lanes, 'verify_generated', return_value={'fileCount': 116}) as verify:
                self.assertEqual(self.lanes.admit_r002f(path)['status'], 'PASS')
                self.assertEqual([call.args[0] for call in verify.call_args_list], [root/'baseline', root/'candidate'])
            with patch.object(self.lanes, 'verify_generated', side_effect=ValueError('changed actual bytes')):
                self.assertEqual(self.lanes.admit_r002f(path)['status'], 'INCOMPLETE')
            process = root/'process.json'
            for result in ({'returncode': 2, 'timedOut': False}, {'returncode': 0, 'timedOut': True}):
                process.write_text(json.dumps(result))
                with patch.object(self.lanes, 'verify_generated') as verify:
                    self.assertEqual(self.lanes.admit_r002f(path, process)['status'], 'INCOMPLETE')
                    verify.assert_not_called()

    def test_sparse_checkouts_retain_exact_v1_pages_receipt_for_both_build_inputs(self):
        workflow = (ROOT/'.github/workflows/research-native-pilot.yml').read_text()
        target = '/docs/state-contracts/evidence/R002B/config-e11bdd3d/ci-build-pages-payload.json'
        self.assertEqual(workflow.count(target), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
