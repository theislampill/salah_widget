"""Offline central controls; namespace/current-source doubles are explicit.

The real reviewed leaf replays actual retained Buffer bytes. No browser,
positive native namespace, image acceptance or product qualification is run.
"""
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch

import lanes as L
import test_observe as legacy

M = legacy.M
HERE = Path(__file__).resolve().parent
MODE = 'capture-passive'
KIND = 'r0040-capture-passive'
ADMITTED = 'ADMITTED_PASSIVE_DATE_ONLY_FOR_OFFLINE_VERIFICATION'


def sha(data):
    return hashlib.sha256(data).hexdigest()


class PassiveCentral(unittest.TestCase):
    def setUp(self):
        self.f = legacy.DateOnlyCapture(methodName='runTest')
        self.f.setUp()
        self.addCleanup(self.f.tearDown)
        self.addCleanup(self.f.doCleanups)
        self.node = self.f.node

    def node_json(self, script, body):
        run = subprocess.run([self.node, '-e', script, str(HERE)], input=json.dumps(body),
                             text=True, capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stderr)
        return json.loads(run.stdout)

    def central(self):
        self.assertTrue((HERE/'r0040_passive_central.py').is_file(), 'passive central admission not implemented')
        return importlib.import_module('r0040_passive_central')

    def prepare_fixture(self):
        f = self.f
        f.prepared['sources']['research']['root'] = str(HERE.parents[2])
        f.args.research = HERE.parents[2]
        common = f.task/'work/prepared/receipts/prepared.json'
        M.write_json(common, f.prepared)
        inputs = {'manifest': str(L.R0040_MANIFEST), 'research': str(f.args.research),
                  'historical': f.prepared['sources']['historical']['root'],
                  'main': f.prepared['trees']['main']['root'], 'out': f.admission['work']}
        folder = f.capture/'r0040-preparation'
        streams = {}
        for label in ('stdout', 'stderr'):
            path = folder/('recipe.'+label)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'synthetic original preparation stream\n')
            streams[label] = {'file': path.name, 'path': str(path), 'bytes': path.stat().st_size,
                              'sha256': sha(path.read_bytes())}
            (f.capture/('r0040-preparation.'+label)).write_bytes(b'synthetic outer entry stream\n')
        process = {'protocol': 'r0040-capture-preparation-process/1', 'status': 'PREPARED',
                   'nativeStatus': 'NOT_RUN', 'returncode': 0, 'timedOut': False, 'inputs': inputs,
                   'argv': [sys.executable, '-I', '-B', '-X', 'pycache_prefix='+str(folder/'unused-bytecode-cache'), '-',
                            *[inputs[key] for key in ('manifest', 'research', 'historical', 'main', 'out')]],
                   'timeoutSeconds': 180, 'elapsedSeconds': 0.1, 'streams': streams}
        M.write_json(f.admission['process'], process)
        entry = {'protocol': 'r0040-capture-preparation-entry/1', 'returncode': 0, 'timedOut': False,
                 'elapsedSeconds': 0.2, 'timeoutSeconds': 240, 'cwd': str(HERE),
                 'wrapperSha256': L.R0040_PREPARER_SHA256,
                 'argv': [sys.executable, str(HERE/'r0040_capture_prepare.py'),
                          *[part for key in ('manifest', 'research', 'historical', 'main', 'out')
                            for part in ('--'+key, inputs[key])], '--receipts', str(folder)]}
        M.write_json(f.admission['entryReceipt']['path'], entry)
        f.admission['entryReceipt']['sha256'] = M.digest(Path(f.admission['entryReceipt']['path']))
        f.admission['dateOnlyPreparation'] = {**f.admission['entryReceipt'], 'actualExitCode': 0}
        f.admission['sourceCustody']['preparationProcess']['sha256'] = M.digest(Path(f.admission['process']))
        return common, entry, process

    def fixture(self):
        f = self.f
        common, _, _ = self.prepare_fixture()
        identity = self.node_json("const p=require(process.argv[1]+'/r0040_passive.cjs');"
                                 "process.stdout.write(JSON.stringify(p.passiveIdentity(process.argv[1]+'/../r0040/capture.cjs')));", {})
        f.admission['passiveDiagnostic'] = identity
        f.admission['passiveSources'] = self.central().verify_sources()
        f.admission['passiveRuntime'] = self.central().preparation_runtime(
            f.admission['entryReceipt']['path'], f.admission['process'], common, f.prepared,
            f.runtime, f.task)
        try:
            f.plan = L.make_plan(f.prepared, f.capture/'lanes', python_playwright=Path(sys.executable),
                                node=Path(self.node), node_modules=Path(f.runtime['modules']),
                                pngjs=Path(f.runtime['pngjs']), work_orders=['R0040'],
                                r0040_mode=MODE, r0040_preparation=f.admission)
        except ValueError as error:
            self.fail('new opt-in passive route is not admitted: '+str(error))
        f.plan['preparedReceipt'] = {'path': str(common), 'sha256': M.digest(common)}
        f.lane = f.plan['lanes'][0]
        f.args.r0040_mode = MODE
        f.args.lane = f.lane['id']
        report = Path(f.lane['result']['path'])
        M.write_json(report, f.raw)
        f.final['originalReport'] = {'file': str(report), 'bytes': report.stat().st_size, 'sha256': M.digest(report)}
        f.sources.update(**f.admission['sourceCustody'], preparationEntry=f.admission['dateOnlyPreparation'],
                         originalArgv=f.lane['evidenceRetention']['originalArgv'][2:], passive=identity)
        isolation = Path(f.lane['result']['isolationReceiptPath'])
        M.write_json(isolation, {'protocol': 'salah-hosted-native-isolation/1', 'passed': True, 'uid': 1001,
                                'netns': 'net:[synthetic-inner]', 'outerNetns': 'net:[synthetic-outer]',
                                'browserControl': {'passed': True}})
        f.sources['isolation'] = {'file': str(isolation), 'sha256': M.digest(isolation)}
        f.current['stdout'] = json.dumps({'isolation': f.sources['isolation'],
            'preparationEntry': f.sources['preparationEntry'], 'diagnostic': f.sources['diagnostic'],
            'sourcePopulation': {'research': 12, 'historical': 6, 'main': 177}})
        f.write_evidence()
        evidence = Path(f.lane['evidenceRetention']['output'])
        self.stop_path = evidence/'passive-original-stop-1.json'
        self.stop_path.write_bytes(b'{"result":{"value":[{"at":1010},{"at":1020},{"at":1030}]}}\n')
        runtime = {'protocol': 'r0040-passive-runtime-snapshot/1', 'clockDomain': 'main-performance',
                   'timeOriginMs': 1000, 'performanceBeforeMs': 10, 'performanceAfterMs': 20,
                   'runtime': {'availability': 'ABSENT'},
                   'observer': {'protocol': 'r0040-passive-workers/1', 'clockDomain': 'main-performance',
                       'timeOriginMs': 1000, 'limit': 2048, 'workerLimit': 16,
                       'workersConstructed': 0, 'workersObserved': 0, 'droppedWorkers': 0,
                       'dropped': 0, 'faults': 0, 'installed': True, 'prototypePreserved': True,
                       'events': [{'ordinal': 0, 'event': 'observer-installed', 'workerId': None, 'atMs': 1}]}}
        sampler = {'protocol': 'r0040-passive-sampler/1', 'clockDomain': 'isolated-performance',
                   'timeOriginMs': 1000, 'limit': 4096, 'dropped': 0, 'faults': 0,
                   'rows': [[0, 10, 11, 12], [1, 20, 21, 22], [2, 30, 31, 32]]}
        inspections = self.node_json("const fs=require('fs'),u=require(process.argv[1]+'/r0040_passive_runtime.cjs'),"
            "s=require(process.argv[1]+'/r0040_passive_sampler.cjs'),p=JSON.parse(fs.readFileSync(0,'utf8'));"
            "process.stdout.write(JSON.stringify({runtime:u.inspectRuntime(p.runtime),sampler:s.inspectSampler(p.sampler)}));",
            {'runtime': runtime, 'sampler': sampler})
        stop_bytes = self.stop_path.read_bytes()
        observation = {'protocol': 'r0040-passive-observation/1', 'identity': identity, 'errors': [],
            'host': {'protocol': 'r0040-passive-host/1', 'clockDomain': 'node-hrtime', 'limit': 2048,
                     'dropped': 0, 'faults': 0, 'rows': [
                         {'ordinal': i, 'event': name, 'monotonicNs': str(i+1)} for i, name in enumerate(
                             ('observer-created', 'playwright-page-closed', 'playwright-context-closed', 'server-closed'))]},
            'runtimes': [{'phase': phase, 'status': 'OBSERVED', 'error': None, 'raw': copy.deepcopy(runtime),
                         'inspection': inspections['runtime']} for phase in ('readiness-returned', 'before-context-close')],
            'samplers': [{'id': 1, 'contextId': 9, 'start': identity['sampler'], 'streamStarted': True,
                'streamStopped': True, 'originalStopReturned': True, 'originalSampleCount': 3, 'detached': True,
                'originalStopResponse': {'protocol': 'r0040-passive-original-stop/1', 'status': 'RETAINED',
                    'limits': {'samples': 4096, 'bytes': 8388608}, 'error': None, 'observedBytes': len(stop_bytes),
                    'artifact': {'file': self.stop_path.name, 'bytes': len(stop_bytes), 'sha256': sha(stop_bytes)}},
                'extractions': [{'phase': 'after-original-stop', 'status': 'OBSERVED', 'error': None,
                                 'raw': sampler, 'inspection': inspections['sampler']}]}]}
        inspection = self.node_json("const fs=require('fs'),p=require(process.argv[1]+'/r0040_passive.cjs'),"
            "v=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(p.inspectPassive(v.observation,v.identity,fs.readFileSync(v.stop))));",
            {'observation': observation, 'identity': identity, 'stop': str(self.stop_path)})
        base = Path(f.lane['result']['finalAdmissionPath']).read_bytes()
        self.passive = {'protocol': 'r0040-passive-final-observation/1', 'status': ADMITTED,
            'exitCode': 0, 'originalExitCode': 0, 'continuationVetoed': False, 'retentionError': None,
            'baseAdmission': {'file': 'final-admission.json', 'sha256': sha(base), 'bytes': len(base)},
            'observation': observation, 'inspection': inspection, 'issues': [],
            'timingClass': 'instrumented-passive-date-only', 'nativeQualification': 'NOT_VERIFIED',
            'humanAcceptance': 'OUTSTANDING'}
        self.save_passive()
        return f

    def save_passive(self):
        f = self.f
        M.write_json(f.lane['result']['passiveAdmissionPath'], self.passive)
        rows = [copy.deepcopy(f.rows[0]),
                {'event': 'passive-instrumentation', 'identity': self.passive['observation']['identity']},
                copy.deepcopy(f.rows[1]),
                {'event': 'passive-original-stop-response', 'sessionId': 1,
                 'observation': self.passive['observation']['samplers'][0]['originalStopResponse']},
                {'event': 'passive-observation-ended', 'observation': self.passive['observation'],
                 'inspection': self.passive['inspection'], 'issues': self.passive['issues']},
                copy.deepcopy(f.rows[2]),
                {'event': 'passive-terminal-status', 'protocol': 'r0040-passive-terminal-status/1',
                 'originalExitCode': 0, 'dateOnlyAdmissionExitCode': 0, 'exitCode': 0,
                 'continuationVetoed': False, 'issues': [],
                 'scope': 'Supplemental expected terminal status; external actual process result remains mandatory.'}]
        self.passive_rows = [dict(row, sequence=i+1) for i, row in enumerate(rows)]
        Path(f.lane['result']['journalPath']).write_text(''.join(json.dumps(row)+'\n' for row in self.passive_rows))

    def test_opt_in_route_binds_original_arguments_and_extra_budget(self):
        try:
            plan = L.make_plan(self.f.prepared, self.f.capture/'lanes', python_playwright=Path(sys.executable),
                              node=Path(self.node), node_modules=Path('/runtime/modules'), pngjs=Path('/runtime/pngjs'),
                              work_orders=['R0040'], r0040_mode=MODE)
        except ValueError as error:
            self.fail('passive route absent: '+str(error))
        lane = plan['lanes'][0]
        self.assertEqual((lane['id'], lane['result']['kind']), ('r0040-chromium-capture-passive', KIND))
        self.assertEqual(lane['argv'], [])
        self.assertEqual((lane['timeoutSeconds'], lane['preCaptureCheckSeconds'], lane['postCaptureCheckSeconds']), (240, 120, 130))
        f = self.fixture()
        self.assertEqual(f.lane['argv'][1], str(HERE/'r0040_passive.cjs'))
        self.assertEqual(f.lane['argv'][f.lane['argv'].index('--')+1:], f.lane['evidenceRetention']['originalArgv'][2:])
        self.assertEqual(f.lane['argv'][-4:], ['chromium', 'bday', 'moderate', 'M1'])

    def test_original_dateonly_rejects_passive_tail_but_new_route_admits_actual_stop_bytes(self):
        f = self.fixture()
        self.assertEqual(M.r0040_dateonly_status(f.raw, f.lane, 0, False)['status'], 'INCOMPLETE')
        result = M.classify_lane(f.lane, 0)
        self.assertEqual(result['status'], ADMITTED, result)
        self.assertEqual(result['dateOnlyStatus'], L.R0040_DATEONLY_ADMITTED)
        self.assertEqual(result['timingClass'], 'instrumented-passive-date-only')
        self.assertEqual(result['nativeQualification'], 'NOT_VERIFIED')
        self.assertEqual(result['humanAcceptance'], 'OUTSTANDING')
        self.assertEqual(result['passiveVerification']['returncode'], 0)
        self.assertEqual(result['passiveInspection']['samplerRows'], 3)

    def test_raw_stop_population_cannot_be_replaced_by_coupled_prefix_count_and_inspection(self):
        f = self.fixture()
        sample = self.passive['observation']['samplers'][0]
        sample['originalSampleCount'] = 2
        sample['extractions'][0]['raw']['rows'].pop()
        sample['extractions'][0]['inspection']['count'] = 2
        sample['extractions'][0]['inspection']['intervals'].pop()
        self.passive['inspection']['samplerRows'] = 2
        self.save_passive()
        result = M.classify_lane(f.lane, 0)
        self.assertEqual(result['status'], 'INCOMPLETE')
        self.assertIn('population', result['passiveVerification']['stderr'])

    def test_raw_stop_missing_changed_symlink_or_escaped_name_is_not_admitted(self):
        f = self.fixture()
        original = self.stop_path.read_bytes()
        self.stop_path.unlink()
        self.assertEqual(M.classify_lane(f.lane, 0)['status'], 'INCOMPLETE')
        self.stop_path.write_bytes(original+b' ')
        self.assertEqual(M.classify_lane(f.lane, 0)['status'], 'INCOMPLETE')
        self.stop_path.unlink()
        alternate = self.stop_path.with_name('other.json')
        alternate.write_bytes(original)
        self.stop_path.symlink_to(alternate)
        self.assertEqual(M.classify_lane(f.lane, 0)['status'], 'INCOMPLETE')
        self.stop_path.unlink()
        self.stop_path.write_bytes(original)
        self.passive['observation']['samplers'][0]['originalStopResponse']['artifact']['file'] = '../other.json'
        self.save_passive()
        self.assertEqual(M.classify_lane(f.lane, 0)['status'], 'INCOMPLETE')

    def test_terminal_tail_and_observation_must_match_actual_receipts(self):
        f = self.fixture()
        journal = Path(f.lane['result']['journalPath'])
        for mutate in (lambda rows: rows.pop(), lambda rows: rows.append(copy.deepcopy(rows[-1])),
                       lambda rows: rows[-1].update(exitCode=False),
                       lambda rows: rows[-1].update(dateOnlyAdmissionExitCode=1),
                       lambda rows: rows[3].update(sessionId=True),
                       lambda rows: rows[-3]['inspection'].update(samplerRows=1),
                       lambda rows: rows[0]['passive'].update(entrySha256='0'*64)):
            rows = copy.deepcopy(self.passive_rows)
            mutate(rows)
            journal.write_text(''.join(json.dumps(row)+'\n' for row in rows))
            self.assertEqual(M.classify_lane(f.lane, 0)['status'], 'INCOMPLETE')

    def test_original_failures_child_veto_and_outer_timeout_keep_precedence(self):
        f = self.fixture()
        for code, timeout, want in ((9, False, 'FAIL'), (-9, True, 'INCOMPLETE'), (86, False, M.VETO_STATUS)):
            result = M.classify_lane(f.lane, code, timeout)
            self.assertEqual(result['status'], want)
        inner = {**M.classify_lane(f.lane, 0), 'id': f.lane['id']}
        self.assertEqual(M.namespace_status(f.lane, {'returncode': 0, 'timedOut': False}, inner)['status'], ADMITTED)
        for outer, want in (({'returncode': 86, 'timedOut': False}, 'ISOLATION_FAIL'),
                            ({'returncode': 1, 'timedOut': False}, 'ISOLATION_UNCONFIRMED'),
                            ({'returncode': 0, 'timedOut': True}, 'ISOLATION_UNCONFIRMED')):
            self.assertEqual(M.namespace_status(f.lane, outer, inner)['status'], want)
        for tag in ('PASS', M.CAPTURE_ADMITTED, L.R0040_DATEONLY_ADMITTED):
            self.assertEqual(M.namespace_status(f.lane, {'returncode': 0, 'timedOut': False},
                                               {**inner, 'status': tag})['status'], 'ISOLATION_UNCONFIRMED')

    def test_runtime_binding_rejects_both_preparation_python_substitutions(self):
        common, _, _ = self.prepare_fixture()
        f, central = self.f, self.central()
        original = {key: Path(f.admission[key]).read_bytes() for key in ('process',)}
        entry_path = Path(f.admission['entryReceipt']['path'])
        original['entry'] = entry_path.read_bytes()
        for path in (entry_path, Path(f.admission['process'])):
            body = json.loads(path.read_bytes())
            body['argv'][0] = '/synthetic/unadmitted-python'
            M.write_json(path, body)
            with self.assertRaisesRegex(ValueError, 'acquired runtime'):
                central.preparation_runtime(entry_path, f.admission['process'], common, f.prepared, f.runtime, f.task)
            path.write_bytes(original['entry' if path == entry_path else 'process'])
        result = central.preparation_runtime(entry_path, f.admission['process'], common, f.prepared, f.runtime, f.task)
        self.assertEqual(result['python'], sys.executable)
        self.assertEqual(result['commonPreparation']['sha256'], M.digest(common))

    def test_runtime_binding_rejects_failed_process_stream_drift_and_wrong_source_root(self):
        common, _, _ = self.prepare_fixture()
        f, central = self.f, self.central()
        process = Path(f.admission['process'])
        original = process.read_bytes()
        for mutate in (lambda body: body.update(returncode=False), lambda body: body.update(timedOut=True),
                       lambda body: body.update(timeoutSeconds=1),
                       lambda body: body['inputs'].update(main='/synthetic/other-main'),
                       lambda body: body['streams']['stdout'].update(sha256='0'*64)):
            body = json.loads(original)
            mutate(body)
            M.write_json(process, body)
            with self.assertRaises(ValueError):
                central.preparation_runtime(f.admission['entryReceipt']['path'], process, common, f.prepared, f.runtime, f.task)
        process.write_bytes(original)

    def test_current_admission_and_full_canonical_plan_cannot_be_rebound_together(self):
        f = self.fixture()
        central = self.central()
        current = {'returncode': 0, 'timedOut': False, 'stdout': json.dumps(f.admission), 'stderr': ''}
        with patch.object(central, 'readmit', return_value=current):
            rows = M.admit_plan(f.plan, f.args, f.runtime)
            self.assertEqual(rows[0]['id'], f.lane['id'])
            self.assertEqual(rows[0]['preExecutionCurrentness'], current)
            for mutate in (lambda p: p['lanes'][0]['preparation']['sourceCustody'].update(recipeSourceSha256='0'*64),
                           lambda p: p['lanes'][0]['result']['passiveDiagnostic'].update(entrySha256='0'*64),
                           lambda p: p['lanes'][0]['argv'].__setitem__(-1, 'M2'),
                           lambda p: p['lanes'][0].update(timeoutSeconds=180),
                           lambda p: p['lanes'][0]['result'].update(passiveAdmissionPath='/other/passive.json')):
                changed = copy.deepcopy(f.plan)
                mutate(changed)
                with self.assertRaises(ValueError):
                    M.admit_plan(changed, f.args, f.runtime)

    def test_executable_module_and_preparation_binding_precede_readmission(self):
        f = self.fixture()
        central = self.central()
        for mutate in (lambda p: p['lanes'][0]['argv'].__setitem__(0, '/unadmitted/node'),
                       lambda p: p['lanes'][0]['env'].update(NODE_PATH='/unadmitted/modules'),
                       lambda p: p['lanes'][0]['evidenceRetention']['originalArgv'].__setitem__(2, '/unadmitted/playwright')):
            changed = copy.deepcopy(f.plan)
            mutate(changed)
            with patch.object(central, 'readmit', side_effect=AssertionError('unadmitted verifier executed')), self.assertRaises(ValueError):
                M.admit_plan(changed, f.args, f.runtime)
        path = Path(f.admission['entryReceipt']['path'])
        body = json.loads(path.read_bytes())
        body['argv'][0] = '/unadmitted/python'
        M.write_json(path, body)
        with patch.object(central, 'readmit', side_effect=AssertionError('unadmitted verifier executed')), self.assertRaises(ValueError):
            M.admit_plan(f.plan, f.args, f.runtime)

    def test_unadmitted_namespace_remains_a_real_refusal_before_capture(self):
        f = self.fixture()
        f.current_patch.stop()
        result = M.classify_lane(f.lane, 0)
        self.assertEqual(result['status'], 'INCOMPLETE')
        self.assertNotEqual(result['currentSourceCheck']['returncode'], 0)
        self.assertIn('nonroot receipt identity mismatch', result['currentSourceCheck']['stderr'].lower())
        self.assertNotIn('passiveVerification', result)

    def test_failed_or_timed_out_current_readmission_prevents_the_capture_child(self):
        f = self.fixture()
        M.write_json(f.capture/'lanes.json', f.plan)
        central = self.central()
        for process in ({'returncode': 2, 'timedOut': False, 'stdout': '', 'stderr': 'source drift'},
                        {'returncode': -9, 'timedOut': True, 'stdout': 'partial currentness', 'stderr': ''},
                        {'returncode': False, 'timedOut': False, 'stdout': json.dumps(f.admission), 'stderr': ''}):
            with patch.object(M, 'controls', return_value=f.lane['result']['isolationReceiptPath']), \
                 patch.dict(os.environ), patch.object(central, 'readmit', return_value=process), \
                 patch.object(M, 'run_bounded', side_effect=AssertionError('capture child executed')) as child:
                with self.assertRaisesRegex(ValueError, 'current source readmission failed'):
                    M.inside(f.args, f.runtime)
                child.assert_not_called()

    def test_real_bounded_check_retains_failed_and_timeout_streams_and_stops_descendants(self):
        central = self.central()
        code = "import os,sys;print('retained output',flush=True);print('retained error',file=sys.stderr,flush=True);assert 'NODE_OPTIONS' not in os.environ;sys.exit(7)"
        failed = central.bounded_check([sys.executable, '-c', code], {}, 5, {**os.environ, 'NODE_OPTIONS': '--bad-option'})
        self.assertEqual((failed['returncode'], failed['timedOut']), (7, False))
        self.assertEqual(failed['stdout'], 'retained output\n')
        self.assertEqual(failed['stderr'], 'retained error\n')
        code = "import subprocess,sys,time;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(20)']);print(p.pid,flush=True);print('timeout prefix',file=sys.stderr,flush=True);time.sleep(20)"
        timeout = central.bounded_check([sys.executable, '-c', code], {}, 0.4)
        self.assertEqual((timeout['returncode'], timeout['timedOut']), (-9, True))
        self.assertEqual(timeout['stderr'], 'timeout prefix\n')
        pid = int(timeout['stdout'].strip())
        state = Path('/proc')/str(pid)/'stat'
        for _ in range(20):
            if not state.exists() or state.read_text().split()[2] == 'Z':
                break
            time.sleep(0.01)
        self.assertTrue(not state.exists() or state.read_text().split()[2] == 'Z', 'timed-out descendant is still running')

    def test_coordinator_uses_real_boundaries_and_retains_child_and_outer_currentness(self):
        f = self.fixture()
        M.write_json(f.capture/'lanes.json', f.plan)
        current = {'returncode': 0, 'timedOut': False, 'stdout': json.dumps(f.admission), 'stderr': ''}
        with patch.object(self.central(), 'readmit', return_value=current), \
             patch.object(M, 'controls', return_value=f.lane['result']['isolationReceiptPath']), \
             patch.dict(os.environ, {'R0040_OPTIONS': 'forbidden'}), \
             patch.object(M, 'run_bounded', return_value={'returncode': 0, 'timedOut': False}) as run:
            self.assertEqual(M.inside(f.args, f.runtime), 0)
            self.assertEqual(run.call_args.args[0], f.lane['argv'])
            self.assertEqual(run.call_args.args[-1], 240)
            self.assertNotIn('R0040_OPTIONS', run.call_args.args[2])
            self.assertEqual(run.call_args.args[2]['R0040_DISPERSION'], 'common')
        inner = json.loads((f.capture/'lane-status'/(f.lane['id']+'.json')).read_bytes())
        self.assertEqual(inner['preExecutionCurrentness'], current)
        for outer, want in (({'returncode': 0, 'timedOut': False}, 'OBSERVED'),
                            ({'returncode': 86, 'timedOut': False}, 'ISOLATION_FAIL'),
                            ({'returncode': -9, 'timedOut': True}, 'ISOLATION_UNCONFIRMED')):
            with patch.object(self.central(), 'readmit', return_value=current), \
                 patch.object(M, 'isolated_command', side_effect=lambda a, r, phase, lane=None: [phase, lane]), \
                 patch.object(M, 'run_bounded', side_effect=[{'returncode': 0, 'timedOut': False}, outer]) as run:
                self.assertEqual(M.outside(f.args, f.runtime), 0 if want == 'OBSERVED' else 2)
            self.assertEqual([call.args[-1] for call in run.call_args_list], [1350, 565])
            report = json.loads((f.capture/'observation.json').read_bytes())
            self.assertEqual(report['status'], want)
            self.assertEqual(report['lanes'][0]['outerCurrentness'], current)
            self.assertEqual(report['lanes'][0]['status'], ADMITTED if want == 'OBSERVED' else want)
            self.assertEqual(report['budget'], {'coordinatorSeconds': 2640, 'workflowObservationMinutes': 45})

    def test_coordinator_budget_exhaustion_does_not_start_capture(self):
        f = self.fixture()
        M.write_json(f.capture/'lanes.json', f.plan)
        current = {'returncode': 0, 'timedOut': False, 'stdout': json.dumps(f.admission), 'stderr': ''}
        with patch.object(self.central(), 'readmit', return_value=current), \
             patch.object(M, 'time') as clock, \
             patch.object(M, 'isolated_command', side_effect=lambda a, r, phase, lane=None: [phase, lane]), \
             patch.object(M, 'run_bounded', return_value={'returncode': 0, 'timedOut': False}) as run:
            clock.monotonic.side_effect = [100, 2700]
            self.assertEqual(M.outside(f.args, f.runtime), 2)
        self.assertEqual(len(run.call_args_list), 1)
        self.assertEqual(run.call_args.args[0], ['prepare', None])
        report = json.loads((f.capture/'observation.json').read_bytes())
        self.assertEqual(report['lanes'][0]['status'], 'NOT_RUN')
        self.assertEqual(report['lanes'][0]['reason'], 'bounded observation budget exhausted')

    def test_actual_failed_preparation_retains_its_process_and_never_falls_back(self):
        f = self.f
        f.args.task = f.task/'failed-attempt'
        f.args.phase = 'prepare'
        f.args.lane = None
        f.args.r0040_mode = MODE
        capture = f.args.task/'capture'
        capture.mkdir(parents=True)
        real_run = M.run_bounded
        calls = []
        def run(argv, cwd, env, stdout, stderr, timeout):
            calls.append((argv, timeout))
            Path(stdout).parent.mkdir(parents=True, exist_ok=True)
            name = Path(argv[1]).name
            if name == 'r0040_capture_prepare.py':
                return real_run(argv, cwd, env, stdout, stderr, timeout)
            Path(stdout).write_text('explicit common preparation or planner double\n')
            Path(stderr).write_text('')
            if name == 'prepare.py':
                M.write_json(f.args.task/'work/prepared/receipts/prepared.json', f.prepared)
            elif name == 'lanes.py':
                admission = L.admit_r0040(f.prepared, f.args.task/'work/r0040-capture',
                    capture/'r0040-preparation/process.json', capture/'r0040-preparation-entry.json',
                    capture/'lanes', Path(self.node), Path(f.runtime['playwright']), mode=MODE,
                    python=f.runtime['python'], common_prepared=f.args.task/'work/prepared/receipts/prepared.json',
                    task=f.args.task, modules=f.runtime['modules'])
                self.assertEqual(admission['status'], 'INCOMPLETE')
                plan = L.make_plan(f.prepared, capture/'lanes', python_playwright=Path(sys.executable),
                    node=Path(self.node), node_modules=Path(f.runtime['modules']), pngjs=Path(f.runtime['pngjs']),
                    work_orders=['R0040'], r0040_mode=MODE, r0040_preparation=admission)
                M.write_json(stdout, plan)
            return {'returncode': 0, 'timedOut': False, 'elapsedSeconds': 0.1}
        with patch.object(M, 'controls', return_value='/synthetic/isolation.json'), \
             patch.dict(os.environ), patch.object(M, 'run_bounded', side_effect=run):
            self.assertEqual(M.inside(f.args, f.runtime), 0)
        self.assertEqual([Path(argv[1]).name for argv, _ in calls], ['prepare.py', 'r0040_capture_prepare.py', 'lanes.py'])
        self.assertEqual([timeout for _, timeout in calls], [900, 240, 120])
        entry = json.loads((capture/'r0040-preparation-entry.json').read_bytes())
        child = json.loads((capture/'r0040-preparation/process.json').read_bytes())
        self.assertNotEqual(entry['returncode'], 0)
        self.assertEqual(entry['argv'], calls[1][0])
        self.assertEqual(child['status'], 'INCOMPLETE')
        self.assertEqual(child['nativeStatus'], 'NOT_RUN')
        self.assertNotEqual(child['returncode'], 0)
        self.assertIn('Traceback', (capture/'r0040-preparation/recipe.stderr').read_text())
        plan = json.loads((capture/'lanes.json').read_bytes())
        self.assertEqual(plan['lanes'][0]['argv'], [])
        with patch.object(M, 'isolated_command', return_value=['synthetic-preparation-namespace']), \
             patch.object(M, 'run_bounded', return_value={'returncode': 0, 'timedOut': False}) as process:
            self.assertEqual(M.outside(f.args, f.runtime), 2)
        self.assertEqual(len(process.call_args_list), 1)
        report = json.loads((capture/'observation.json').read_bytes())
        self.assertEqual(report['lanes'][0]['status'], 'NOT_RUN')

    def test_single_passive_population_has_explicit_budgets_and_forbids_combination(self):
        campaign = {'schemaVersion': 1, 'engine': 'chromium', 'r003fDpr': 1, 'workOrders': ['R0040'],
                    'r0040Mode': MODE, 'r002f': {'enabled': False, 'dpr': 1, 'rounds': 1, 'section': 'all'}}
        path = self.f.task/'campaign.json'
        M.write_json(path, campaign)
        try:
            self.assertEqual(M.read_campaign(path), campaign)
        except ValueError as error:
            self.fail('passive campaign rejected: '+str(error))
        self.assertEqual(M.campaign_budget(campaign), {'coordinatorSeconds': 2640, 'workflowObservationMinutes': 45})
        for change in ({'workOrders': ['R0040', 'R0035']}, {'engine': 'firefox'}, {'r0035Costs': True},
                       {'r0035Stages': True}, {'r003fHarness': 'corrected-matrix'}, {'r002fRoute': 'tabhide'}):
            M.write_json(path, {**campaign, **change})
            with self.assertRaises(ValueError):
                M.read_campaign(path)


if __name__ == '__main__':
    unittest.main()
