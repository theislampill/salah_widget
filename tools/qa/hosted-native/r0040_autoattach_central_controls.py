"""Synthetic mechanism custody controls using actual leaf/Buffer replay.

The legacy namespace and generated-source checks are explicit test doubles;
none of these cases launches a browser, namespace or preparation build.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

import capture_pipeline as pipeline
import lanes as L
import r0040_autoattach_central as C
import r0040_passive_central_controls as old_controls

M = old_controls.M
HERE = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()


class MechanismCentral(unittest.TestCase):
    def setUp(self):
        self.old = old_controls.PassiveCentral('runTest')
        self.old.setUp()
        self.addCleanup(self.old.doCleanups)
        self.f = self.old.f

    def fixture(self):
        f = self.old.fixture()
        value = self.old.node_json("const f=require(process.argv[1]+'/r0040_autoattach_fixture.cjs');"
            "f.completeData().then(x=>process.stdout.write(JSON.stringify({identity:x.identity,"
            "observation:x.observation,passive:x.passive,stop:JSON.parse(x.stop),requests:x.baseBody.requests})));", {})
        f.admission.update(mechanismDiagnostic=value['identity'], mechanismSources=C.verify_sources(),
                           mechanismCallerSources=C.caller_sources())
        f.plan = L.make_plan(f.prepared, f.capture/'lanes', python_playwright=Path(sys.executable),
            node=Path(self.old.node), node_modules=Path(f.runtime['modules']), pngjs=Path(f.runtime['pngjs']),
            work_orders=['R0040'], r0040_mode=C.MODE, r0040_preparation=f.admission)
        common = f.task/'work/prepared/receipts/prepared.json'
        f.plan['preparedReceipt'] = {'path': str(common), 'sha256': M.digest(common)}
        f.lane = f.plan['lanes'][0]
        f.args.r0040_mode, f.args.lane = C.MODE, f.lane['id']
        report = Path(f.lane['result']['path'])
        M.write_json(report, f.raw)
        f.final['originalReport'] = {'file': str(report), 'bytes': report.stat().st_size, 'sha256': M.digest(report)}
        base = 'http://127.0.0.1:40001'
        f.final['scene']['base'] = base
        first = f.final['requests'][0]
        first['url'] = base+'/index.html'
        first['actions'][0]['destination'] = first['url']
        for i, request in enumerate(value['requests'], 2):
            f.final['requests'].append({**request, 'id': i, 'resourceType': 'fetch', 'observedBy': ['context', 'route'],
                'callbackState': 'returned', 'actions': [{'action': 'continue', 'state': 'completed',
                    'destination': request['url'], 'refused': False}]})
        self.observation, self.passive_observation = value['observation'], value['passive']
        proof = f.final['clockProofs'][0]['raw']
        main = self.observation['bracket']['main']['raw']
        main['timeOriginMs'] = proof['timeOriginMs']
        main['anchor'] = {key: proof[key] for key in ('utcMs', 'anchorPerformanceMs', 'timeOriginMs')}
        main['anchor']['protocol'] = 'r0040-date-only-installed/1'
        main['rows'] = [[0, 100, 200, 202, 'returned'], [1, 101, 210, 212, 'returned']]
        for row in self.passive_observation['runtimes']:
            row['raw']['timeOriginMs'] = row['raw']['observer']['timeOriginMs'] = proof['timeOriginMs']
        stop = value['stop']
        for i, row in enumerate(stop['result']['value']):
            row['phaseMs'] = 101 + 10*i
        self.stop = (json.dumps(stop)+'\n').encode()
        self.stop_path = Path(f.lane['evidenceRetention']['output'])/'passive-original-stop-1.json'
        self.stop_path.parent.mkdir(parents=True, exist_ok=True)
        self.stop_path.write_bytes(self.stop)
        sampler = self.passive_observation['samplers'][0]
        sampler['originalStopResponse']['observedBytes'] = len(self.stop)
        sampler['originalStopResponse']['artifact'] = {'file': self.stop_path.name, 'bytes': len(self.stop), 'sha256': sha(self.stop)}
        f.sources.update(originalArgv=f.lane['evidenceRetention']['originalArgv'][2:], mechanism=value['identity'])
        isolation = Path(f.lane['result']['isolationReceiptPath'])
        M.write_json(isolation, {'protocol': 'salah-hosted-native-isolation/1', 'passed': True, 'uid': 1001,
            'netns': 'net:[synthetic-inner]', 'outerNetns': 'net:[synthetic-outer]', 'browserControl': {'passed': True}})
        f.sources['isolation'] = {'file': str(isolation), 'sha256': M.digest(isolation)}
        f.current['stdout'] = json.dumps({'isolation': f.sources['isolation'],
            'preparationEntry': f.sources['preparationEntry'], 'diagnostic': f.sources['diagnostic'],
            'sourcePopulation': {'research': 12, 'historical': 6, 'main': 177}})
        self.save()
        return f

    def save(self):
        f = self.f
        f.write_evidence()
        result = self.old.node_json("const fs=require('fs'),m=require(process.argv[1]+'/r0040_autoattach.cjs'),"
            "p=require(process.argv[1]+'/r0040_passive.cjs'),u=require(process.argv[1]+'/r0040_passive_runtime.cjs'),"
            "x=JSON.parse(fs.readFileSync(0,'utf8')),stop=fs.readFileSync(x.stop);"
            "for(const r of x.passive.runtimes)r.inspection=u.inspectRuntime(r.raw);"
            "process.stdout.write(JSON.stringify({passive:x.passive,old:p.inspectPassive(x.passive,x.identity.passive,stop),"
            "inspection:m.inspectMechanism(x.observation,x.identity,x.base,x.passive,stop)}));",
            {'stop': str(self.stop_path), 'base': f.final, 'identity': f.admission['mechanismDiagnostic'],
             'passive': self.passive_observation, 'observation': self.observation})
        self.passive_observation = result['passive']
        old = copy.deepcopy(self.old.passive)
        old.update(observation=result['passive'], inspection=result['old'])
        base_bytes = Path(f.lane['result']['finalAdmissionPath']).read_bytes()
        old['baseAdmission'] = {'file': 'final-admission.json', 'bytes': len(base_bytes), 'sha256': sha(base_bytes)}
        M.write_json(f.lane['result']['passiveAdmissionPath'], old)
        old_bytes = Path(f.lane['result']['passiveAdmissionPath']).read_bytes()
        self.receipt = {'protocol': 'r0040-autoattach-final-observation/1', 'status': C.ADMITTED,
            'exitCode': 0, 'originalExitCode': 0, 'continuationVetoed': False, 'retentionError': None,
            'baseAdmission': old['baseAdmission'], 'passiveAdmission': {'file': 'passive-observation.json',
                'bytes': len(old_bytes), 'sha256': sha(old_bytes)}, 'observation': self.observation,
            'inspection': result['inspection'], 'timingClass': C.TIMING,
            'nativeQualification': 'NOT_VERIFIED', 'humanAcceptance': 'OUTSTANDING'}
        M.write_json(f.lane['result']['mechanismAdmissionPath'], self.receipt)
        prefix = lambda phase: {'event': 'autoattach-network-prefix', 'phase': phase,
                                'observation': self.observation['network']}
        rows = [copy.deepcopy(f.rows[0]),
            {'event': 'passive-instrumentation', 'identity': old['observation']['identity']},
            {'event': 'autoattach-instrumentation', 'identity': f.admission['mechanismDiagnostic']},
            prefix('before-context-creation'), copy.deepcopy(f.rows[1]), prefix('readiness-returned'),
            {'event': 'passive-original-stop-response', 'sessionId': 1,
             'observation': old['observation']['samplers'][0]['originalStopResponse']},
            {'event': 'autoattach-bracket-prefix', 'observation': self.observation['bracket']},
            prefix('after-original-context-close'),
            {'event': 'autoattach-observation-ended', 'observation': self.observation, 'inspection': result['inspection']},
            {'event': 'passive-observation-ended', 'observation': old['observation'], 'inspection': old['inspection'], 'issues': []},
            copy.deepcopy(f.rows[2]), {'event': 'passive-terminal-status', 'protocol': 'r0040-passive-terminal-status/1',
                'originalExitCode': 0, 'dateOnlyAdmissionExitCode': 0, 'exitCode': 0,
                'continuationVetoed': False, 'issues': [], 'scope': C.passive.TERMINAL_SCOPE}]
        self.rows = [dict(row, sequence=i+1) for i, row in enumerate(rows)]
        self.write_rows()

    def write_rows(self):
        Path(self.f.lane['result']['journalPath']).write_text(''.join(json.dumps(row)+'\n' for row in self.rows))

    def result(self):
        value = M.classify_lane(self.f.lane, 0)
        self.assertEqual(value['status'], C.ADMITTED, value)
        return {**value, 'id': self.f.lane['id']}

    def test_route_budget_and_original_eight_arguments(self):
        f = self.fixture()
        self.assertEqual(f.lane['argv'][1], str(HERE/'r0040_autoattach.cjs'))
        self.assertEqual(f.lane['argv'][f.lane['argv'].index('--')+1:], f.lane['evidenceRetention']['originalArgv'][2:])
        self.assertEqual(len(f.lane['argv'][f.lane['argv'].index('--')+1:]), 8)
        self.assertEqual((f.lane['timeoutSeconds'], f.lane['preCaptureCheckSeconds'], f.lane['postCaptureCheckSeconds']), (240, 120, 130))
        self.assertEqual(sum((240, 120, 130, 75)), 565)
        campaign = {'engine': 'chromium', 'workOrders': ['R0040'], 'r0040Mode': C.MODE, 'r002f': {'enabled': False}}
        self.assertEqual(M.campaign_budget(campaign), {'coordinatorSeconds': 2640, 'workflowObservationMinutes': 45})
        for orders, engine in ((['R0040', 'R0035'], 'chromium'), (['R0040'], 'firefox')):
            with self.assertRaises(ValueError): L.rain_mode(C.MODE, orders, engine)

    def test_combined_actual_buffer_replay_and_old_gate(self):
        self.fixture()
        value = self.result()
        self.assertEqual(value['mechanismVerification']['timeoutSeconds'], 30)
        self.assertEqual(value['passiveInspection']['samplerRows'], 2)
        self.assertEqual(value['mechanismInspection']['bracket']['status'], 'OBSERVED')
        self.assertEqual(value['mechanismInspection']['network']['status'], 'OBSERVED')
        self.assertEqual(value['nativeQualification'], 'NOT_VERIFIED')
        self.assertEqual(value['humanAcceptance'], 'OUTSTANDING')
        self.assertEqual(M.r0040_dateonly_status(self.f.raw, self.f.lane, 0, False)['status'], 'INCOMPLETE')

    def test_actual_failure_and_namespace_always_take_precedence(self):
        f = self.fixture()
        value = self.result()
        for exit_code, timed_out in ((1, False), (86, False), (0, True)):
            with patch.object(C, 'final_check', side_effect=AssertionError('must not promote original failure')):
                self.assertNotEqual(M.classify_lane(f.lane, exit_code, timed_out)['status'], C.ADMITTED)
        for code, timeout, expected in ((86, False, 'ISOLATION_FAIL'), (7, False, 'ISOLATION_UNCONFIRMED'), (0, True, 'ISOLATION_UNCONFIRMED')):
            self.assertEqual(M.namespace_status(f.lane, {'returncode': code, 'timedOut': timeout}, value)['status'], expected)
        for code in (1, 86, False, '0'):
            with self.assertRaisesRegex(ValueError, 'actual mechanism child'):
                C.final_check(f.lane, code, f.sources, self.rows)

    def test_raw_stop_tamper_missing_or_symlink_cannot_be_replaced_by_receipt(self):
        f = self.fixture()
        self.stop_path.write_bytes(self.stop+b' ')
        value = M.classify_lane(f.lane, 0)
        self.assertEqual(value['status'], 'INCOMPLETE')
        self.assertNotEqual(value['mechanismVerification']['returncode'], 0)
        self.stop_path.unlink()
        self.assertEqual(M.classify_lane(f.lane, 0)['status'], 'INCOMPLETE')
        other = f.task/'synthetic-stop.json'; other.write_bytes(self.stop)
        self.stop_path.symlink_to(other)
        self.assertEqual(M.classify_lane(f.lane, 0)['status'], 'INCOMPLETE')

    def test_coupled_prefix_cut_still_refuses_actual_full_stop(self):
        f = self.fixture()
        self.observation['bracket']['main']['raw']['rows'].pop()
        self.observation['bracket']['join']['raw']['rows'].pop()
        self.save()
        self.assertEqual(self.receipt['inspection']['bracket']['status'], 'INCOMPLETE')
        self.assertEqual(self.receipt['inspection']['network']['status'], 'OBSERVED')
        self.assertEqual(M.classify_lane(f.lane, 0)['status'], 'INCOMPLETE')

    def test_incomplete_network_retains_complete_bracket_without_qualification(self):
        f = self.fixture()
        self.observation['network']['setup']['status'] = 'INCOMPLETE'
        self.save()
        self.assertEqual(self.receipt['inspection']['bracket']['status'], 'OBSERVED')
        self.assertEqual(self.receipt['inspection']['network']['status'], 'INCOMPLETE')
        self.assertEqual(M.classify_lane(f.lane, 0)['status'], 'INCOMPLETE')

    def test_missing_duplicate_or_reordered_journal_prefix_refuses(self):
        f = self.fixture()
        original = copy.deepcopy(self.rows)
        for transform in (lambda rows: rows[:7]+rows[8:], lambda rows: rows[:7]+[rows[7]]+rows[7:],
                          lambda rows: rows[:7]+[rows[8], rows[7]]+rows[9:]):
            self.rows = [dict(row, sequence=i+1) for i, row in enumerate(transform(copy.deepcopy(original)))]
            self.write_rows()
            self.assertEqual(M.classify_lane(f.lane, 0)['status'], 'INCOMPLETE')

    def test_current_caller_and_leaf_source_are_bound(self):
        f = self.fixture()
        f.admission['mechanismCallerSources']['lanes.py']['sha256'] = '0'*64
        self.assertEqual(M.classify_lane(f.lane, 0)['status'], 'INCOMPLETE')
        source = f.task/'synthetic-source'; source.mkdir()
        for name in C.SOURCE_PINS: shutil.copy2(HERE/name, source/name)
        with patch.object(C, 'HERE', source):
            C.verify_sources()
            with (source/'r0040_mechanism_bracket.cjs').open('ab') as file: file.write(b'\n// source drift\n')
            with self.assertRaisesRegex(ValueError, 'source drift'): C.verify_sources()

    def test_plan_current_readmission_and_canonical_recipe_are_strict(self):
        f = self.fixture()
        good = {'returncode': 0, 'timedOut': False, 'stdout': json.dumps(f.admission), 'stderr': ''}
        with patch.object(C, 'readmit', return_value=good):
            self.assertEqual(M.admit_plan(f.plan, f.args, f.runtime)[0]['preExecutionCurrentness'], good)
        for returned in (None, [], False, 'PASS', {'status': 'INCOMPLETE'}, {**f.admission, 'mechanismSources': {}}):
            with patch.object(C, 'readmit', return_value={**good, 'stdout': json.dumps(returned)}):
                with self.assertRaises(ValueError): M.admit_plan(f.plan, f.args, f.runtime)
        for mutation in ({'returncode': True}, {'returncode': 1}, {'timedOut': True}):
            with patch.object(C, 'readmit', return_value={**good, **mutation}):
                with self.assertRaises(ValueError): M.admit_plan(f.plan, f.args, f.runtime)
        f.lane['argv'][-1] = 'M0'
        with patch.object(C, 'readmit', return_value=good):
            with self.assertRaises(ValueError): M.admit_plan(f.plan, f.args, f.runtime)

    def test_actual_source_readmission_refuses_missing_preparation(self):
        f = self.f
        result = C.readmit(f.task/'absent-common.json', f.runtime, f.task)
        self.assertEqual(result['returncode'], 2, result)
        self.assertFalse(result['timedOut'])
        self.assertEqual(result['timeoutSeconds'], 120)
        self.assertTrue(result['stderr'])

    def test_namespace_requires_both_diagnostics_and_distinct_label(self):
        f = self.fixture()
        value = self.result()
        outer = {'returncode': 0, 'timedOut': False}
        self.assertEqual(M.namespace_status(f.lane, outer, value)['status'], C.ADMITTED)
        for mutate in (lambda x: x.update(status='PASS'), lambda x: x.update(status=C.passive.ADMITTED),
                       lambda x: x.update(returncode=True), lambda x: x['mechanismInspection']['network'].update(status='INCOMPLETE'),
                       lambda x: x['mechanismInspection']['bracket'].update(status='INCOMPLETE'),
                       lambda x: x['mechanismVerification'].update(returncode=True),
                       lambda x: x['mechanismVerification'].update(timeoutSeconds=60),
                       lambda x: x['mechanismVerification'].update(argv=['node', '-e', 'forged']),
                       lambda x: x['mechanismVerification'].update(stdout='{}'),
                       lambda x: x.update(mechanismInspection=None),
                       lambda x: x.update(mechanismVerification=None),
                       lambda x: x['mechanismDiagnostic'].update(entrySha256='0'*64)):
            altered = copy.deepcopy(value); mutate(altered)
            self.assertEqual(M.namespace_status(f.lane, outer, altered)['status'], 'ISOLATION_UNCONFIRMED')

    def pipeline_fixture(self):
        f = self.fixture()
        inner = self.result()
        row = M.namespace_status(f.lane, {'returncode': 0, 'timedOut': False, 'elapsedSeconds': 0.01}, inner)
        return {'workOrders': ['R0040'], 'r0040Mode': C.MODE}, f.plan, {'lanes': [row]}

    def test_pipeline_complete_record_requires_actual_current_artifacts(self):
        campaign, plan, body = self.pipeline_fixture()
        self.assertTrue(pipeline.autoattach_complete_record(campaign, plan, body))
        self.stop_path.write_bytes(self.stop+b' ')
        with self.assertRaises(pipeline.Rejected): pipeline.autoattach_complete_record(campaign, plan, body)

    def test_pipeline_retains_failed_or_partial_mode_without_promotion(self):
        campaign, plan, body = self.pipeline_fixture()
        for status in ('FAIL', 'INCOMPLETE', 'ISOLATION_FAIL', 'ISOLATION_UNCONFIRMED'):
            altered = copy.deepcopy(body); altered['lanes'][0]['status'] = status
            self.assertIs(pipeline.autoattach_complete_record(campaign, plan, altered), False)
        for status in ('PASS', C.passive.ADMITTED, L.R0040_DATEONLY_ADMITTED):
            altered = copy.deepcopy(body); altered['lanes'][0]['status'] = status
            with self.assertRaises(pipeline.Rejected): pipeline.autoattach_complete_record(campaign, plan, altered)

    def test_pipeline_rejects_cross_route_or_forged_component_completion(self):
        campaign, plan, body = self.pipeline_fixture()
        with self.assertRaises(pipeline.Rejected):
            pipeline.autoattach_complete_record({**campaign, 'r0040Mode': C.passive.MODE}, plan, body)
        for mutate in (lambda x: x['lanes'][0]['mechanismInspection']['network'].update(status='INCOMPLETE'),
                       lambda x: x['lanes'][0]['namespaceProcess'].update(returncode=1),
                       lambda x: x['lanes'][0].update(innerStatus=None)):
            altered = copy.deepcopy(body); mutate(altered)
            with self.assertRaises(pipeline.Rejected): pipeline.autoattach_complete_record(campaign, plan, altered)

    def test_pipeline_coupled_artifact_refresh_cannot_hide_original_failure(self):
        campaign, plan, body = self.pipeline_fixture()
        path = Path(plan['lanes'][0]['result']['finalAdmissionPath'])
        actual = json.loads(path.read_bytes()); actual.update(status='FAILED', exitCode=1)
        M.write_json(path, actual)
        for row in (body['lanes'][0], body['lanes'][0]['innerStatus']):
            row['mechanismArtifacts']['base'] = C.record(path)
        with self.assertRaises(pipeline.Rejected): pipeline.autoattach_complete_record(campaign, plan, body)


if __name__ == '__main__':
    unittest.main()
