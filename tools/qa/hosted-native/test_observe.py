"""Behavioral controls for isolated observation admission and failure retention."""
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('hosted_observe', Path(__file__).with_name('observe.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def admitted_snapshot():
    return {'uids': [1001, 1001, 1001], 'gids': [1001, 1001, 1001], 'groups': [],
            'netns': 'net:[200]', 'links': [{'ifname': 'lo', 'flags': ['LOOPBACK', 'UP']}],
            'routes4': [{'dst': '127.0.0.0/8', 'dev': 'lo'}],
            'routes6': [{'dst': '::1', 'dev': 'lo'}],
            'status': {**{k: '0000000000000000' for k in M.CAP_FIELDS}, 'NoNewPrivs': '1'},
            'externalSocketErrno': 101}


def campaign_plan(lanes, orders, retained=False):
    return {'protocol': 'salah-hosted-native-lanes/1', 'sequential': True,
            'workOrders': orders, 'evidenceRetention': retained, 'lanes': lanes}


class Admission(unittest.TestCase):
    def test_accepts_only_fresh_loopback_namespace_without_privilege(self):
        M.validate_snapshot(admitted_snapshot(), 'net:[100]')

    def test_rejects_root_or_saved_root(self):
        for uids in ([0, 0, 0], [1001, 1001, 0]):
            s = admitted_snapshot(); s['uids'] = uids
            with self.assertRaises(ValueError): M.validate_snapshot(s, 'net:[100]')

    def test_rejects_reused_network_namespace(self):
        with self.assertRaises(ValueError): M.validate_snapshot(admitted_snapshot(), 'net:[200]')

    def test_rejects_extra_interface_even_without_default_route(self):
        s = admitted_snapshot(); s['links'].append({'ifname': 'eth0', 'flags': ['UP']})
        with self.assertRaises(ValueError): M.validate_snapshot(s, 'net:[100]')

    def test_rejects_default_or_nonloopback_routes(self):
        for route in ({'dst': 'default', 'dev': 'lo'}, {'dst': '192.0.2.0/24', 'dev': 'eth0'},
                      {'dst': '192.0.2.0/24', 'dev': 'lo'}, {'dst': '::/0', 'dev': 'lo'}):
            s = admitted_snapshot(); s['routes4'].append(route)
            with self.assertRaises(ValueError): M.validate_snapshot(s, 'net:[100]')

    def test_rejects_any_capability_or_missing_no_new_privileges(self):
        for field in (*M.CAP_FIELDS, 'NoNewPrivs'):
            s = admitted_snapshot(); s['status'][field] = '0' if field == 'NoNewPrivs' else '1'
            with self.assertRaises(ValueError): M.validate_snapshot(s, 'net:[100]')

    def test_rejects_socket_success_timeout_or_remote_refusal(self):
        for code in (0, 110, 111):
            s = admitted_snapshot(); s['externalSocketErrno'] = code
            with self.assertRaises(ValueError): M.validate_snapshot(s, 'net:[100]')

    def test_environment_drops_credentials_proxies_and_home_overrides(self):
        os.environ['HOSTED_TEST_SECRET'] = 'must-not-copy'
        env = M.clean_environment('/opt/node/bin/node', '/opt/python/bin/python', '/tmp/task',
                                  '/tmp/task/node-browsers', '/tmp/task/node/node_modules',
                                  '/source/baseline', '/source/research')
        for name in ('HOSTED_TEST_SECRET', 'GITHUB_TOKEN', 'ACTIONS_RUNTIME_TOKEN', 'HOME',
                     'CODEX_HOME', 'HTTPS_PROXY', 'NODE_USE_ENV_PROXY', 'PYTHONPATH', 'NODE_OPTIONS'):
            self.assertNotIn(name, env)
        self.assertEqual(env['PLAYWRIGHT_BROWSERS_PATH'], '/tmp/task/node-browsers')
        self.assertEqual(env['GIT_CONFIG_VALUE_0'], '/source/baseline')
        self.assertEqual(env['GIT_CONFIG_VALUE_1'], '/source/research')


class Verdict(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def lane(self, kind, data=None):
        p = self.root / 'result.json'
        if data is not None: p.write_text(json.dumps(data))
        return {'id': 'test', 'workOrder': 'R003F', 'result': {'kind': kind, 'path': str(p)}}

    def test_corrected_r003f_requires_harness_identity_population_and_both_ui_receipts(self):
        harness = {'protocol': 'R003F/corrected-harness/1', 'driverSha256': 'frozen-control-driver'}
        ui = {'protocol': 'R003F/native-ui/1', 'status': 'PASS', 'failures': [], 'observed': {'control': True}}
        body = {'protocol': 'R003F/P1/B0-owner/2', 'status': 'MEASURED', 'isolation': {'ok': True},
                'engine': 'chromium', 'dpr': 1, 'indexSha256': M.BASE_INDEX, 'harness': harness,
                'captures': {key: {'state': {'nativeUi': copy.deepcopy(ui)}, 'nativeUiAfter': copy.deepcopy(ui)}
                             for key in ('offset', 'b0', 'b0-repeat', 'reference')}}
        def classify(value, code=0):
            lane = self.lane('r003f-b0', value); lane.update(engine='chromium', dpr=1)
            lane['result'].update(expectedHarness=harness, expectedIndexSha256=M.BASE_INDEX,
                                  expectedCaptures=['offset', 'b0', 'b0-repeat', 'reference'])
            return M.classify_lane(lane, code)
        self.assertEqual(classify(body)['status'], 'PASS')
        for mutate in (lambda b:b.pop('harness'), lambda b:b['harness'].update(driverSha256='changed'),
                       lambda b:b.update(engine='webkit'), lambda b:b.update(dpr=2),
                       lambda b:b.update(indexSha256='wrong'), lambda b:b['captures'].pop('reference'),
                       lambda b:b['captures']['b0'].pop('nativeUiAfter'),
                       lambda b:b['captures']['b0']['state']['nativeUi'].update(status='INCOMPLETE'),
                       lambda b:b['captures']['b0']['nativeUiAfter'].update(failures=['displaced UI']),
                       lambda b:b['captures']['b0']['nativeUiAfter'].pop('observed')):
            changed=copy.deepcopy(body); mutate(changed)
            with self.subTest(change=changed): self.assertEqual(classify(changed)['status'], 'INCOMPLETE')
        self.assertEqual(classify({'status':'FAIL (Andon)'}, 4)['status'], 'ANDON')
        self.assertEqual(classify({'isolation':{'ok':False}}, 3)['status'], 'ISOLATION_FAIL')

    def test_r0035_exit_zero_does_not_override_failed_admission(self):
        l = self.lane('r0035-trials', [{'admitted': True}, {'admitted': False}])
        self.assertEqual(M.classify_lane(l, 0)['status'], 'INCOMPLETE')

    def test_r0035_empty_population_does_not_pass(self):
        self.assertEqual(M.classify_lane(self.lane('r0035-trials', []), 0)['status'], 'INCOMPLETE')

    def test_r0035_partial_or_duplicated_arms_do_not_pass(self):
        for rows in ([{'arm':'main','admitted':True}],
                     [{'arm':'main','admitted':True}]*3):
            self.assertEqual(M.classify_lane(self.lane('r0035-trials', rows), 0)['status'], 'INCOMPLETE')
        complete = [{'arm':name,'admitted':True,'qualification':{'verdict':'passed'}}
                    for name in ('main','unmodified','mitigated')]
        self.assertEqual(M.classify_lane(self.lane('r0035-trials', complete), 0)['status'], 'PASS')

    def test_r0035_failed_and_indeterminate_admissions_remain_distinct(self):
        for verdict, expected in (('failed', 'FAIL'), ('indeterminate', 'INCOMPLETE')):
            rows = [{'arm': name, 'admitted': False, 'qualification': {'verdict': verdict}}
                    for name in ('main', 'unmodified', 'mitigated')]
            self.assertEqual(M.classify_lane(self.lane('r0035-trials', rows), 0)['status'], expected)

    def test_r0035_setup_exception_without_report_is_incomplete(self):
        self.assertEqual(M.classify_lane(self.lane('r0035-trials'), 1)['status'], 'INCOMPLETE')

    def test_r0035_partial_failed_admission_is_preserved(self):
        rows = [{'arm': 'main', 'admitted': False, 'qualification': {'verdict': 'failed'}}]
        self.assertEqual(M.classify_lane(self.lane('r0035-trials', rows), 1)['status'], 'FAIL')

    def test_r003f_incomplete_exit_does_not_become_assertion_failure(self):
        lane = self.lane('r003f-b0', {'status': 'INCOMPLETE', 'isolation': {'ok': True}})
        self.assertEqual(M.classify_lane(lane, 2)['status'], 'INCOMPLETE')

    def test_reported_isolation_failure_dominates_timeout(self):
        lane = self.lane('r003f-b0', {'status': 'ISOLATION FAIL', 'isolation': {'ok': False}})
        result = M.classify_lane(lane, -9, True)
        self.assertEqual(result['status'], 'ISOLATION_FAIL')
        self.assertTrue(result['stopAll'])

    def test_r003f_andon_and_isolation_remain_distinct(self):
        l = self.lane('r003f-b0', {'status': 'FAIL (Andon)', 'isolation': {'ok': True}})
        self.assertEqual(M.classify_lane(l, 4)['status'], 'ANDON')
        self.assertFalse(M.classify_lane(l, 4)['stopAll'])
        self.assertTrue(M.classify_lane(l, 3)['stopAll'])

    def test_no_report_or_timeout_is_incomplete(self):
        l = self.lane('r003f-b0')
        self.assertEqual(M.classify_lane(l, 0)['status'], 'INCOMPLETE')
        self.assertEqual(M.classify_lane(l, -9, True)['status'], 'INCOMPLETE')

    def test_r0040_requires_complete_distinct_population(self):
        cells = [{'id': x} for x in M.RAIN_CELLS]
        l = self.lane('r0040-options', {'cells': cells})
        self.assertEqual(M.classify_lane(l, 0)['status'], 'PASS')
        l = self.lane('r0040-options', {'cells': cells[:-1] + [cells[0]]})
        self.assertEqual(M.classify_lane(l, 0)['status'], 'INCOMPLETE')

    def test_retained_child_veto_is_prevented_continuation_even_with_complete_report(self):
        lane = self.lane('r0040-options', {'cells': [{'id': x} for x in M.RAIN_CELLS]})
        lane.update(workOrder='R0040', stopAllOnExit=[86], evidenceRetention={'instrumented': True})
        result = M.classify_lane(lane, 86)
        self.assertEqual(result['status'], 'EXTERNAL_CONTINUATION_VETOED')
        self.assertEqual(result['returncode'], 86)
        self.assertTrue(result['stopAll'])
        self.assertIn('prevented', result['reason'])
        self.assertIn('not evidence of an actual network escape', result['reason'])

    def test_retention_failure_exit_cannot_be_overridden_by_original_success_report(self):
        cases = [('r0040-options', {'cells': [{'id': x} for x in M.RAIN_CELLS]}, 'FAIL'),
                 ('r0035-trials', [{'arm': arm, 'admitted': True, 'qualification': {'verdict': 'passed'}}
                                   for arm in ('main', 'unmodified', 'mitigated')], 'INCOMPLETE')]
        for kind, report, expected in cases:
            lane = self.lane(kind, report)
            lane.update(stopAllOnExit=[86], evidenceRetention={'instrumented': True})
            self.assertEqual(M.classify_lane(lane, 1)['status'], expected)

    def test_namespace_veto_receipt_never_overrules_outer_boundary_failure(self):
        lane = {'id': 'retained', 'stopAllOnExit': [86], 'evidenceRetention': {'instrumented': True}}
        inner = {'id': 'retained', 'status': 'EXTERNAL_CONTINUATION_VETOED',
                 'returncode': 86, 'stopAll': True, 'reason': 'prevented external continuation'}
        result = M.namespace_status(lane, {'returncode': 0, 'timedOut': False}, inner)
        self.assertEqual(result['status'], 'EXTERNAL_CONTINUATION_VETOED')
        self.assertTrue(result['stopAll'])
        for process, expected in (({'returncode': 86, 'timedOut': False}, 'ISOLATION_FAIL'),
                                  ({'returncode': -9, 'timedOut': True}, 'ISOLATION_UNCONFIRMED'),
                                  ({'returncode': 1, 'timedOut': False}, 'ISOLATION_UNCONFIRMED')):
            result = M.namespace_status(lane, process, inner)
            self.assertEqual(result['status'], expected)
            self.assertEqual(result['innerStatus'], inner)
            self.assertEqual(result['namespaceProcess'], process)
        for changes in ({'returncode': 0}, {'stopAll': False}, {'status': 'PASS', 'stopAll': True}):
            result = M.namespace_status(lane, {'returncode': 0, 'timedOut': False}, {**inner, **changes})
            self.assertEqual(result['status'], 'ISOLATION_UNCONFIRMED')

    def r002f(self, *, section='all', rounds=1):
        body = {'protocol': 'r002f-hosted-native/1', 'status': 'PASS', 'engine': 'chromium',
                'dpr': 1, 'rounds': rounds, 'section': section,
                'observerSha256': '673c0656d8e2d8e1c343d1258be5070fa9447f3f43878460791ea8570468558f',
                'sources': {
                    'baseline': {'indexSha256': '88411488017ea590e6b4c5a21adc143977c0907089eabb80b0cbe8f0ba18a8a1'},
                    'candidate': {'indexSha256': '55a8bdbc7b7ab5cb53ede3b58c0ef1e4101c7c89bc6936860bd4bc5f3acb8fe2'}},
                'prayerPairs': [], 'preview': []}
        if section != 'preview':
            body['prayerPairs'] = [{'scenario': scenario, 'round': round_, 'verdict': {'status': 'PASS'},
                                   'baseline': f'baseline-{scenario}-{round_}.json',
                                   'candidate': f'candidate-{scenario}-{round_}.json'}
                                  for round_ in range(1, rounds + 1) for scenario in ('fajr', 'maghrib', 'midnight')]
        if section != 'prayer':
            body['preview'] = [{'arm': arm, 'file': arm+'-preview.json',
                                'verdict': {'status': 'OBSERVED' if arm == 'baseline' else 'PASS'}}
                               for arm in ('baseline', 'candidate')]
        lane = self.lane('r002f-probe', body)
        lane.update(workOrder='R002F', engine='chromium', dpr=1)
        lane['result'].update(expectedRounds=rounds, expectedSection=section,
                              expectedObserverSha256=body['observerSha256'])
        return lane, body

    def test_r002f_pass_requires_protocol_identity_and_exact_requested_population(self):
        for section, rounds in (('all', 1), ('prayer', 2), ('preview', 1)):
            lane, _ = self.r002f(section=section, rounds=rounds)
            self.assertEqual(M.classify_lane(lane, 0)['status'], 'PASS')
        changes = [lambda b: b.update(protocol='other'), lambda b: b.update(observerSha256='0'*64),
                   lambda b: b.update(dpr=2), lambda b: b.update(engine='webkit'),
                   lambda b: b.update(dpr=True), lambda b: b.update(rounds=True),
                   lambda b: b.update(rounds=2), lambda b: b.update(section='prayer'),
                   lambda b: b.update(prayerPairs=[]), lambda b: b['prayerPairs'].pop(),
                   lambda b: b['prayerPairs'].__setitem__(2, b['prayerPairs'][0]),
                   lambda b: b.update(preview=[]), lambda b: b['preview'].pop(),
                   lambda b: b['preview'].__setitem__(1, b['preview'][0]),
                   lambda b: b['preview'][0]['verdict'].update(status='PASS'),
                   lambda b: b['sources']['candidate'].update(indexSha256='0'*64)]
        for mutate in changes:
            lane, body = self.r002f(); mutate(body)
            Path(lane['result']['path']).write_text(json.dumps(body))
            self.assertEqual(M.classify_lane(lane, 0)['status'], 'INCOMPLETE', body)

    def test_r002f_original_fail_incomplete_and_inconclusive_are_preserved(self):
        for status, code in (('FAIL', 1), ('INCOMPLETE', 2), ('INCONCLUSIVE', 2)):
            lane, body = self.r002f(); body['status'] = status
            Path(lane['result']['path']).write_text(json.dumps(body))
            self.assertEqual(M.classify_lane(lane, code)['status'], status)
        lane, body = self.r002f(); body['prayerPairs'][0]['verdict']['status'] = 'FAIL'
        body['prayerPairs'] = body['prayerPairs'][:1]
        Path(lane['result']['path']).write_text(json.dumps(body))
        self.assertEqual(M.classify_lane(lane, -9, True)['status'], 'FAIL')
        lane, body = self.r002f(); body['prayerPairs'][0]['verdict']['status'] = 'INCONCLUSIVE'
        Path(lane['result']['path']).write_text(json.dumps(body))
        self.assertEqual(M.classify_lane(lane, 2)['status'], 'INCONCLUSIVE')

    def test_r002f_missing_report_and_status_only_report_cannot_pass(self):
        for data in (None, {'status': 'PASS'}, {'protocol': 'r002f-hosted-native/1', 'status': 'PASS'}):
            lane = self.lane('r002f-probe', data)
            self.assertEqual(M.classify_lane(lane, 0)['status'], 'INCOMPLETE')

    def test_namespace_preserves_legitimate_r002f_inconclusive(self):
        inner = {'id': 'r002f', 'status': 'INCONCLUSIVE', 'stopAll': False, 'returncode': 2}
        result = M.namespace_status({'id': 'r002f'}, {'returncode': 0, 'timedOut': False}, inner)
        self.assertEqual(result['status'], 'INCONCLUSIVE')
        self.assertFalse(result['stopAll'])

    def test_process_failure_preserves_both_streams(self):
        stdout, stderr = self.root/'stdout', self.root/'stderr'
        result = M.run_bounded([sys.executable, '-c', "import sys;print('data');print('error',file=sys.stderr);sys.exit(7)"],
                               str(self.root), {}, stdout, stderr, 5)
        self.assertEqual(result['returncode'], 7)
        self.assertIn('data', stdout.read_text()); self.assertIn('error', stderr.read_text())

    def test_timeout_kills_descendant_process_group(self):
        pidfile = self.root/'pid'
        code = "import os,time,pathlib; p=os.fork(); pathlib.Path('pid').write_text(str(p)) if p else None; time.sleep(30)"
        result = M.run_bounded([sys.executable, '-c', code], str(self.root), {},
                               self.root/'stdout', self.root/'stderr', 0.3)
        self.assertTrue(result['timedOut'])
        pid = int(pidfile.read_text())
        stat = Path('/proc')/str(pid)/'stat'
        # Group signalling can precede the descendant's scheduled exit. Observe
        # that exit with a bound; do not confuse one transient /proc read with a
        # surviving descendant, and never change the production kill sequence.
        deadline=time.monotonic()+1
        while True:
            try: state=stat.read_text().split()[2]
            except FileNotFoundError: state=None
            if state in (None,'Z') or time.monotonic()>=deadline:break
            time.sleep(.01)
        self.assertIn(state,(None,'Z'))


class OuterBoundary(unittest.TestCase):
    def check_outer(self, namespace_result, inner_status):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp)
            capture = task/'capture'; capture.mkdir()
            lanes = [{'id': name, 'workOrder': 'R0035', 'timeoutSeconds': 5,
                      'result': {'kind': 'r0035-trials', 'path': str(capture/(name+'.json'))}}
                     for name in ('r0035-chromium-timing', 'r0035-chromium-capture')]
            (capture/'lanes.json').write_text(json.dumps(campaign_plan(lanes, ['R0035'])))
            calls = []
            def run(argv, *_args):
                calls.append(argv)
                if len(calls) == 1:
                    return {'returncode': 0, 'timedOut': False}
                if inner_status is not None:
                    inner_status['id'] = lanes[0]['id']
                    M.write_json(capture/'lane-status'/(lanes[0]['id']+'.json'), inner_status)
                return namespace_result
            args = SimpleNamespace(task=task, engine='chromium', work_orders=['R0035'])
            with patch.object(M, 'isolated_command', side_effect=lambda *a: ['isolated']), \
                 patch.object(M, 'run_bounded', side_effect=run):
                code = M.outside(args, {})
            report = json.loads((capture/'observation.json').read_text())
            self.assertEqual(len(calls), 2, 'unconfirmed wrapper must prevent the next lane')
            self.assertNotEqual(code, 0)
            self.assertEqual(report['lanes'][0]['status'], 'ISOLATION_UNCONFIRMED')
            self.assertTrue(report['lanes'][0]['stopAll'])
            self.assertEqual(report['lanes'][0]['namespaceProcess'], namespace_result)
            self.assertEqual(report['lanes'][1]['status'], 'NOT_RUN')
            if inner_status is not None:
                self.assertEqual(report['lanes'][0]['innerStatus'], inner_status)

    def test_namespace_timeout_overrides_inner_pass_and_stops_all(self):
        self.check_outer({'returncode': -9, 'timedOut': True},
                         {'id': 'first', 'status': 'PASS', 'returncode': 0,
                          'timedOut': False, 'stopAll': False})

    def test_namespace_startup_failure_without_receipt_stops_all(self):
        self.check_outer({'returncode': 1, 'timedOut': False}, None)

    def test_namespace_success_without_admission_receipt_stops_all(self):
        self.check_outer({'returncode': 0, 'timedOut': False}, None)

    def test_missing_or_unprepared_r002f_does_not_erase_independent_lanes(self):
        for include_blocked in (False, True):
            with self.subTest(include_blocked=include_blocked), tempfile.TemporaryDirectory() as tmp:
                task = Path(tmp); capture = task/'capture'; capture.mkdir()
                lanes = [{'id': name, 'workOrder': order, 'timeoutSeconds': 5}
                         for name, order in (('r0040-chromium', 'R0040'), ('r003f-b0-chromium-dpr1', 'R003F'),
                                             ('r0035-chromium-timing', 'R0035'), ('r0035-chromium-capture', 'R0035'))]
                if include_blocked:
                    lanes.insert(0, {'id': 'r002f-chromium-dpr1', 'workOrder': 'R002F', 'timeoutSeconds': 900,
                                     'preparation': {'status': 'INCOMPLETE', 'reason': 'controlled build failure'}})
                (capture/'lanes.json').write_text(json.dumps(campaign_plan(lanes, ['R0040', 'R003F', 'R0035', 'R002F'])))
                calls = []
                def run(argv, *_args):
                    calls.append(argv)
                    if argv[0] == 'lane':
                        M.write_json(capture/'lane-status'/(argv[1]+'.json'),
                                     {'id': argv[1], 'status': 'PASS', 'stopAll': False})
                    return {'returncode': 0, 'timedOut': False}
                args = SimpleNamespace(task=task, engine='chromium', r002f=True, r002f_dpr=1,
                                       r002f_rounds=1, r002f_section='all', r003f_dpr=1)
                with patch.object(M, 'isolated_command', side_effect=lambda _a, _r, phase, lane=None: [phase, lane]), \
                     patch.object(M, 'run_bounded', side_effect=run):
                    code = M.outside(args, {})
                report = json.loads((capture/'observation.json').read_text())
                by_id = {row['id']: row for row in report['lanes']}
                self.assertEqual(code, 2)
                self.assertEqual([by_id[name]['status'] for name in ('r0040-chromium', 'r003f-b0-chromium-dpr1',
                                                                   'r0035-chromium-timing', 'r0035-chromium-capture')], ['PASS']*4)
                self.assertEqual(by_id['r002f-chromium-dpr1']['status'], 'NOT_RUN')
                self.assertEqual(by_id['r002f-chromium-dpr1']['preparationStatus'], 'INCOMPLETE')
                self.assertEqual(len(calls), 5, 'only preparation and the four admitted lanes execute')
                self.assertEqual(report['status'], 'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES')

    def test_each_missing_selected_lane_is_retained_as_not_run(self):
        expected = [('r0040-chromium', 'R0040'), ('r003f-b0-chromium-dpr1', 'R003F'),
                    ('r0035-chromium-timing', 'R0035'), ('r0035-chromium-capture', 'R0035'),
                    ('r002f-chromium-dpr1', 'R002F')]
        orders = ['R0040', 'R003F', 'R0035', 'R002F']
        args = SimpleNamespace(engine='chromium', r003f_dpr=1, r002f=True, r002f_dpr=1, work_orders=orders)
        for missing in ([identifier] for identifier, _ in expected):
            lanes = [{'id': identifier, 'workOrder': order} for identifier, order in expected if identifier not in missing]
            admitted = M.admit_plan(campaign_plan(lanes, orders), args)
            self.assertEqual([row['id'] for row in admitted], [identifier for identifier, _ in expected])
            row = next(row for row in admitted if row['id'] in missing)
            self.assertEqual(row['preparation']['status'], 'INCOMPLETE')
            self.assertIn('missing from the plan', row['preparation']['reason'])
        self.assertEqual(len(M.admit_plan(campaign_plan([], orders), args)), 5)

    def test_duplicate_wrong_identity_or_unselected_lanes_are_rejected_before_execution(self):
        args = SimpleNamespace(engine='chromium', r002f=False, work_orders=['R0035'])
        timing = {'id': 'r0035-chromium-timing', 'workOrder': 'R0035'}
        capture = {'id': 'r0035-chromium-capture', 'workOrder': 'R0035'}
        for rows in ([timing, timing, capture], [timing, {'id': 'unknown', 'workOrder': 'R0035'}],
                     [timing, {'id': 'r0035-firefox-capture', 'workOrder': 'R0035'}],
                     [timing, {**capture, 'workOrder': 'R0040'}],
                     [timing, capture, {'id': 'r0040-chromium', 'workOrder': 'R0040'}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                M.admit_plan(campaign_plan(rows, ['R0035']), args)
        for metadata in ({'workOrders': ['R0040']}, {'evidenceRetention': True}):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                M.admit_plan({**campaign_plan([timing, capture], ['R0035']), **metadata}, args)
        for evidence in ({'evidenceRetention': {'instrumented': True}}, {'evidenceRetention': 'yes'}):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                M.admit_plan(campaign_plan([{**timing, **evidence}, capture], ['R0035']), args)
        args.retain_evidence = True
        with self.assertRaises(ValueError):
            M.admit_plan(campaign_plan([timing, capture], ['R0035'], True), args)

    def test_missing_selected_capture_or_empty_plan_cannot_yield_observed_campaign(self):
        for present in (['r0035-chromium-timing'], []):
            with self.subTest(present=present), tempfile.TemporaryDirectory() as tmp:
                task = Path(tmp); capture = task/'capture'; capture.mkdir()
                lanes = [{'id': name, 'workOrder': 'R0035', 'timeoutSeconds': 5} for name in present]
                (capture/'lanes.json').write_text(json.dumps(campaign_plan(lanes, ['R0035'])))
                calls = []
                def run(argv, *_args):
                    calls.append(argv)
                    if argv[0] == 'lane':
                        M.write_json(capture/'lane-status'/(argv[1]+'.json'),
                                     {'id': argv[1], 'status': 'PASS', 'returncode': 0, 'stopAll': False})
                    return {'returncode': 0, 'timedOut': False}
                args = SimpleNamespace(task=task, engine='chromium', work_orders=['R0035'])
                with patch.object(M, 'isolated_command', side_effect=lambda _a, _r, phase, lane=None: [phase, lane]), \
                     patch.object(M, 'run_bounded', side_effect=run):
                    self.assertEqual(M.outside(args, {}), 2)
                report = json.loads((capture/'observation.json').read_text())
                self.assertEqual(report['status'], 'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES')
                self.assertEqual(len(calls), 1+len(present))
                self.assertEqual(len(report['lanes']), 2)
                self.assertEqual(report['lanes'][-1]['id'], 'r0035-chromium-capture')
                self.assertEqual(report['lanes'][-1]['status'], 'NOT_RUN')
                self.assertEqual(report['lanes'][-1]['preparationStatus'], 'INCOMPLETE')

    def test_veto_stops_later_selected_lanes_without_claiming_network_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp); capture = task/'capture'; capture.mkdir()
            lanes = [{'id': name, 'workOrder': order, 'timeoutSeconds': 5,
                      'stopAllOnExit': [86], 'evidenceRetention': {'instrumented': True}}
                     for name, order in (('r0040-chromium', 'R0040'),
                                         ('r0035-chromium-timing', 'R0035'), ('r0035-chromium-capture', 'R0035'))]
            (capture/'lanes.json').write_text(json.dumps(campaign_plan(lanes, ['R0040', 'R0035'], True)))
            calls = []
            def run(argv, *_args):
                calls.append(argv)
                if argv[0] == 'lane':
                    M.write_json(capture/'lane-status'/(argv[1]+'.json'),
                                 {'id': argv[1], 'status': 'EXTERNAL_CONTINUATION_VETOED', 'returncode': 86,
                                  'stopAll': True, 'reason': 'prevented external continuation'})
                return {'returncode': 0, 'timedOut': False}
            args = SimpleNamespace(task=task, engine='chromium', work_orders=['R0040', 'R0035'], retain_evidence=True)
            with patch.object(M, 'isolated_command', side_effect=lambda _a, _r, phase, lane=None: [phase, lane]), \
                 patch.object(M, 'run_bounded', side_effect=run):
                self.assertEqual(M.outside(args, {}), 2)
            report = json.loads((capture/'observation.json').read_text())
            self.assertEqual(report['status'], 'EXTERNAL_CONTINUATION_VETOED')
            self.assertEqual(len(calls), 2)
            self.assertEqual([row['status'] for row in report['lanes']], ['EXTERNAL_CONTINUATION_VETOED', 'NOT_RUN', 'NOT_RUN'])
            self.assertIn('prevented', report['lanes'][-1]['reason'])

    def test_selected_independent_campaign_does_not_repeat_an_earlier_andon_workstream(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp); capture = task/'capture'; capture.mkdir()
            earlier = task/'earlier-observation.json'; earlier.write_text('{"status":"ANDON","workOrder":"R003F"}\n')
            original = earlier.read_bytes()
            lanes = [{'id': name, 'workOrder': 'R0035', 'timeoutSeconds': 5}
                     for name in ('r0035-chromium-timing', 'r0035-chromium-capture')]
            (capture/'lanes.json').write_text(json.dumps(campaign_plan(lanes, ['R0035'])))
            calls = []
            def run(argv, *_args):
                calls.append(argv)
                if argv[0] == 'lane':
                    M.write_json(capture/'lane-status'/(argv[1]+'.json'),
                                 {'id': argv[1], 'status': 'PASS', 'returncode': 0, 'stopAll': False})
                return {'returncode': 0, 'timedOut': False}
            args = SimpleNamespace(task=task, engine='chromium', work_orders=['R0035'])
            with patch.object(M, 'isolated_command', side_effect=lambda _a, _r, phase, lane=None: [phase, lane]), \
                 patch.object(M, 'run_bounded', side_effect=run):
                self.assertEqual(M.outside(args, {}), 0)
            self.assertEqual(calls, [['prepare', None], ['lane', 'r0035-chromium-timing'], ['lane', 'r0035-chromium-capture']])
            self.assertEqual(earlier.read_bytes(), original)


class Campaign(unittest.TestCase):
    def test_corrected_moon_campaign_controls_cannot_be_ignored_or_substituted(self):
        value={'schemaVersion':1,'engine':'chromium','r003fDpr':1,'workOrders':['R003F'],
               'r003fHarness':'corrected-b0','r002f':{'enabled':False,'dpr':1,'rounds':1,'section':'all'}}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'campaign.json'; path.write_text(json.dumps(value))
            self.assertEqual(M.read_campaign(path), value)
            for change in ({'r003fHarness':True},{'r003fHarness':'fixed'},{'workOrders':['R0040']}):
                path.write_text(json.dumps({**value,**change}))
                with self.assertRaises(ValueError): M.read_campaign(path)
        args=SimpleNamespace(engine='chromium',work_orders=['R003F'],r002f=False,r003f_harness='corrected-b0')
        plan=campaign_plan([{'id':'r003f-b0-chromium-dpr1','workOrder':'R003F'}], ['R003F'])
        with self.assertRaises(ValueError): M.admit_plan(plan,args)
        with self.assertRaises(ValueError): M.admit_plan({**plan,'r003fHarness':'corrected-b0'},args)
        missing=M.admit_plan({**plan,'r003fHarness':'corrected-b0','lanes':[]},args)
        self.assertEqual(len(missing),1)
        self.assertEqual(missing[0]['preparation']['status'],'INCOMPLETE')

    def test_corrected_moon_preparation_failure_preserves_receipts_and_other_lanes(self):
        with tempfile.TemporaryDirectory() as tmp:
            task=Path(tmp); (task/'capture').mkdir()
            args=SimpleNamespace(task=task,research=Path('/sources/research'),baseline=Path('/sources/main'),
                                 historical=Path('/sources/history'),engine='chromium',phase='prepare',lane=None,
                                 work_orders=['R0040','R003F'],r002f=False,r003f_harness='corrected-b0')
            runtime={'python':'/runtime/python','node':'/runtime/node','modules':'/runtime/modules','pngjs':'/runtime/pngjs'}
            calls=[]
            def bounded(argv,cwd,env,stdout,stderr,timeout):
                calls.append(argv); Path(stdout).parent.mkdir(parents=True,exist_ok=True)
                Path(stdout).write_text('partial stdout'); Path(stderr).write_text('partial stderr')
                if Path(argv[1]).name=='prepare.py':
                    target=task/'work/prepared/receipts'; target.mkdir(parents=True)
                    (target/'prepared.json').write_text('{"status":"PREPARED"}')
                if Path(argv[1]).name=='r003f_materialize.cjs':
                    target=Path(argv[argv.index('--out')+1]); target.mkdir(parents=True)
                    (target/'materialization.json').write_text('{"status":"INCOMPLETE"}')
                    return {'returncode':2,'timedOut':False}
                return {'returncode':0,'timedOut':False}
            with patch.object(M,'controls',return_value='/private/admitted.json'),patch.object(M,'run_bounded',side_effect=bounded),patch.dict(os.environ,{},clear=True):
                self.assertEqual(M.inside(args,runtime),0)
            self.assertEqual([Path(x[1]).name for x in calls],['prepare.py','r003f_materialize.cjs','lanes.py'])
            planner=calls[-1]
            self.assertEqual(planner[planner.index('--r003f-harness')+1],'corrected-b0')
            self.assertEqual(planner[planner.index('--r003f-prepared')+1],str(task/'work/r003f-corrected/materialization.json'))
            self.assertEqual(json.loads((task/'capture/r003f-preparation-process.json').read_text())['returncode'],2)
            self.assertEqual((task/'capture/r003f-materialization.json').read_text(),'{"status":"INCOMPLETE"}')
            self.assertEqual((task/'capture/r003f-preparation.stderr').read_text(),'partial stderr')
    def test_star_diagnostic_controls_reject_ignored_or_invalid_requests(self):
        data = {'schemaVersion': 1, 'engine': 'chromium', 'r003fDpr': 1, 'workOrders': ['R0035'],
                'r002f': {'enabled': False, 'dpr': 1, 'rounds': 1, 'section': 'all'},
                'r0035': {'guard': 'off', 'scope': 'all', 'mode': 'timing'}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'campaign.json'; path.write_text(json.dumps(data))
            self.assertEqual(M.read_campaign(path), data)
            for controls in (None, [], 'off', {'guard': True}, {'guard': 'disabled'},
                             {'scope': 'bright'}, {'mode': 'none'}, {'seconds': 60}):
                path.write_text(json.dumps({**data, 'r0035': controls}))
                with self.subTest(controls=controls), self.assertRaises(ValueError): M.read_campaign(path)
            path.write_text(json.dumps({**data, 'workOrders': ['R0040']}))
            with self.assertRaises(ValueError): M.read_campaign(path)

    def test_star_selected_mode_and_config_cannot_be_satisfied_by_a_different_plan(self):
        args = SimpleNamespace(engine='chromium', work_orders=['R0035'], r002f=False,
                               r0035_guard='off', r0035_scope='all', r0035_mode='timing')
        timing = {'id': 'r0035-chromium-timing', 'workOrder': 'R0035'}
        controls = {'guard': 'off', 'scope': 'all', 'mode': 'timing'}
        plan = {**campaign_plan([timing], ['R0035']), 'r0035Controls': controls}
        self.assertEqual([row['id'] for row in M.admit_plan(plan, args)], [timing['id']])
        missing = M.admit_plan({**plan, 'lanes': []}, args)
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]['preparation']['status'], 'INCOMPLETE')
        for change in ({'r0035Controls': {'guard': 'default', 'scope': 'all', 'mode': 'timing'}},
                       {'lanes': [timing, {'id': 'r0035-chromium-capture', 'workOrder': 'R0035'}]}):
            with self.subTest(change=change), self.assertRaises(ValueError): M.admit_plan({**plan, **change}, args)

    def test_campaign_controls_are_bounded_and_not_silently_coerced(self):
        data = {'schemaVersion': 1, 'engine': 'webkit', 'r003fDpr': 2,
                'r002f': {'enabled': True, 'dpr': 3, 'rounds': 2, 'section': 'preview'}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'campaign.json'; path.write_text(json.dumps(data))
            self.assertEqual(M.read_campaign(path), data)
            for change in ({'dpr': 4}, {'dpr': True}, {'rounds': 0}, {'rounds': 11},
                           {'rounds': True}, {'section': 'unknown'}, {'enabled': 'yes'}):
                broken = copy.deepcopy(data); broken['r002f'].update(change)
                path.write_text(json.dumps(broken))
                with self.assertRaises(ValueError): M.read_campaign(path)
            for change in ({'engine': 'safari'}, {'r003fDpr': 3}, {'r003fDpr': True}):
                path.write_text(json.dumps({**data, **change}))
                with self.assertRaises(ValueError): M.read_campaign(path)
            for change in ({'workOrders': []}, {'workOrders': None}, {'workOrders': ['R0035', 'R0035']}, {'workOrders': ['unknown']},
                           {'workOrders': 'R0035'}, {'workOrders': [35]}, {'workOrders': ['R0035']},
                           {'evidenceRetention': 'yes'}, {'evidenceRetention': 1}, {'evidenceRetention': None}):
                path.write_text(json.dumps({**data, **change}))
                with self.assertRaises(ValueError): M.read_campaign(path)
            broken = copy.deepcopy(data); broken['r002f']['enabled'] = False; broken['workOrders'] = ['R002F']
            path.write_text(json.dumps(broken))
            with self.assertRaises(ValueError): M.read_campaign(path)
            selected = copy.deepcopy(data); selected['r002f']['enabled'] = False
            selected.update(workOrders=['R0040', 'R0035'], evidenceRetention=True)
            path.write_text(json.dumps(selected))
            self.assertEqual(M.read_campaign(path), selected)

    def test_campaign_file_reaches_outer_dispatch_with_unchanged_defaults_and_explicit_options(self):
        checked_in = Path(__file__).with_name('campaign.json')
        unchanged = checked_in.read_bytes()
        baseline = {'schemaVersion': 1, 'engine': 'chromium', 'r003fDpr': 1,
                    'r002f': {'enabled': True, 'dpr': 1, 'rounds': 1, 'section': 'all'}}
        selected = copy.deepcopy(baseline)
        selected.update(workOrders=['R0035', 'R0040'], evidenceRetention=True,
                        r0035={'guard': 'off', 'scope': 'preview-members', 'mode': 'timing'})
        selected['r002f']['enabled'] = False
        corrected = copy.deepcopy(baseline)
        corrected.update(workOrders=['R003F'],r003fHarness='corrected-b0')
        corrected['r002f']['enabled'] = False
        current = json.loads(unchanged)
        for data, orders, retained in ((baseline, ['R0040', 'R003F', 'R0035', 'R002F'], False),
                                       (selected, ['R0040', 'R0035'], True),
                                       (corrected, ['R003F'], False),
                                       (current, M.selected_work_orders(current.get('workOrders'),
                                        current['r002f']['enabled']), current.get('evidenceRetention', False))):
            with self.subTest(retained=retained), tempfile.TemporaryDirectory() as tmp:
                task = Path(tmp); (task/'runtime.json').write_text('{}')
                campaign = task/'input-campaign.json'; campaign.write_text(json.dumps(data))
                argv = ['observe.py', '--task', str(task), '--research', '/sources/research',
                        '--baseline', '/sources/main', '--historical', '/sources/history', '--campaign', str(campaign)]
                prior_umask = os.umask(0o077)
                try:
                    with patch.object(sys, 'argv', argv), patch.object(M.signal, 'signal'), \
                         patch.object(M, 'outside', return_value=0) as dispatch:
                        self.assertEqual(M.main(), 0)
                    args = dispatch.call_args.args[0]
                    self.assertEqual(args.work_orders, orders)
                    self.assertIs(args.retain_evidence, retained)
                    self.assertIs(args.r002f, 'R002F' in orders)
                    self.assertEqual(M.star_campaign(args), M.star_controls(data.get('r0035')))
                    self.assertIs(M.stage_campaign(args), data.get('r0035Stages',False))
                    self.assertEqual(M.moon_campaign(args), data.get('r003fHarness','published'))
                    self.assertEqual(M.rain_campaign(args), data.get('r0040Mode','options'))
                    self.assertEqual((args.r002f_dpr, args.r002f_rounds, args.r002f_section),
                                     tuple(data['r002f'][key] for key in ('dpr', 'rounds', 'section')))
                    self.assertEqual(json.loads((task/'capture'/'campaign.json').read_text()), data)
                finally:
                    os.umask(prior_umask)
        self.assertEqual(checked_in.read_bytes(), unchanged)

    def test_optional_preparation_failure_preserves_plan_and_seals_only_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp); (task/'capture').mkdir()
            args = SimpleNamespace(task=task, research=Path('/sources/research'), baseline=Path('/sources/main'),
                                   historical=Path('/sources/history'), engine='firefox', phase='prepare', lane=None,
                                   r002f=True, r002f_dpr=2, r002f_rounds=2, r002f_section='prayer', r003f_dpr=2,
                                   work_orders=['R0040', 'R0035', 'R002F'], retain_evidence=True,
                                   r0035_guard='off', r0035_scope='preview-members', r0035_mode='timing')
            runtime = {'python': '/dependencies/python', 'node': '/dependencies/node',
                       'modules': '/dependencies/modules', 'pngjs': '/dependencies/modules/pngjs'}
            calls = []
            def run(argv, _cwd, _env, stdout, stderr, _timeout):
                calls.append(argv); Path(stdout).parent.mkdir(parents=True, exist_ok=True)
                Path(stdout).write_text('private command output'); Path(stderr).write_text('private failure')
                if 'r002f_prepare.py' in Path(argv[1]).name:
                    target = Path(argv[argv.index('--out')+1]); target.mkdir(parents=True)
                    (target/'build-result.json').write_text('{"status":"INCOMPLETE"}')
                    (target/'candidate').mkdir(); (target/'candidate'/'index.html').write_text('SOURCE BODY')
                    (target/'candidate-build-1.stderr').write_text('private builder failure')
                    return {'returncode': 2, 'timedOut': False}
                if Path(argv[1]).name == 'prepare.py':
                    target = Path(argv[argv.index('--out')+1]); (target/'receipts').mkdir(parents=True)
                    (target/'receipts'/'prepared.json').write_text('{"status":"PREPARED"}')
                return {'returncode': 0, 'timedOut': False}
            with patch.object(M, 'controls', return_value='/private/isolation.json'), \
                 patch.object(M, 'run_bounded', side_effect=run), patch.dict(os.environ):
                self.assertEqual(M.inside(args, runtime), 0)
            self.assertEqual([Path(argv[1]).name for argv in calls], ['prepare.py', 'r002f_prepare.py', 'lanes.py'])
            planner = calls[-1]
            for key, value in (('--r003f-dpr', '2'), ('--r002f-dpr', '2'), ('--r002f-rounds', '2'), ('--r002f-section', 'prayer')):
                self.assertEqual(planner[planner.index(key)+1], value)
            self.assertIn('--r002f-prepared', planner)
            start = planner.index('--work-orders')+1
            self.assertEqual(planner[start:start+3], args.work_orders)
            self.assertIn('--retain-evidence', planner)
            for key, value in (('--r0035-guard', 'off'), ('--r0035-scope', 'preview-members'), ('--r0035-mode', 'timing')):
                self.assertEqual(planner[planner.index(key)+1], value)
            self.assertEqual(planner[planner.index('--r002f-process')+1], str(task/'capture'/'r002f-preparation-process.json'))
            self.assertTrue((task/'capture'/'r002f-preparation'/'build-result.json').is_file())
            self.assertTrue((task/'capture'/'r002f-preparation'/'candidate-build-1.stderr').is_file())
            self.assertFalse(any(path.name == 'index.html' for path in (task/'capture').rglob('*')))

    def test_namespace_command_preserves_the_selected_campaign_controls(self):
        args = SimpleNamespace(task=Path('/task'), research=Path('/sources/research'), baseline=Path('/sources/main'),
                               historical=Path('/sources/history'), engine='webkit', r002f=True, r002f_dpr=3,
                               r002f_rounds=2, r002f_section='preview', r003f_dpr=2,
                               work_orders=['R003F', 'R0035', 'R002F'], retain_evidence=True,
                               r003f_harness='corrected-b0',
                               r0035_guard='off', r0035_scope='preview-members', r0035_mode='timing')
        runtime = {'node': '/dependencies/node', 'python': '/dependencies/python', 'modules': '/dependencies/modules'}
        argv = M.isolated_command(args, runtime, 'lane', 'r002f-webkit-dpr3')
        self.assertIn('--r002f', argv)
        start = argv.index('--work-orders')+1
        self.assertEqual(argv[start:start+3], args.work_orders)
        self.assertIn('--retain-evidence', argv)
        self.assertEqual(argv[argv.index('--r003f-harness')+1],'corrected-b0')
        for key, value in (('--r0035-guard', 'off'), ('--r0035-scope', 'preview-members'), ('--r0035-mode', 'timing')):
            self.assertEqual(argv[argv.index(key)+1], value)
        for key, value in (('--engine', 'webkit'), ('--r003f-dpr', '2'), ('--r002f-dpr', '3'),
                           ('--r002f-rounds', '2'), ('--r002f-section', 'preview')):
            self.assertEqual(argv[argv.index(key)+1], value)

    def test_retained_veto_writes_actual_child_status_before_normal_coordinator_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp); capture = task/'capture'; capture.mkdir()
            identifier = 'r0040-chromium'
            lane = {'id': identifier, 'workOrder': 'R0040', 'argv': ['offline-driver-control'], 'cwd': str(task),
                    'stdout': str(capture/'driver.stdout'), 'stderr': str(capture/'driver.stderr'), 'timeoutSeconds': 5,
                    'stopAllOnExit': [86], 'evidenceRetention': {'instrumented': True},
                    'result': {'kind': 'r0040-options', 'path': str(capture/'absent-original-report.json')}}
            (capture/'lanes.json').write_text(json.dumps(campaign_plan([lane], ['R0040'], True)))
            args = SimpleNamespace(task=task, engine='chromium', phase='lane', lane=identifier,
                                   work_orders=['R0040'], retain_evidence=True)
            with patch.object(M, 'controls', return_value='/private/isolation.json'), patch.dict(os.environ), \
                 patch.object(M, 'run_bounded', return_value={'returncode': 86, 'timedOut': False}):
                self.assertEqual(M.inside(args, {}), 0)
            receipt = json.loads((capture/'lane-status'/(identifier+'.json')).read_text())
            self.assertEqual(receipt['returncode'], 86)
            self.assertEqual(receipt['status'], 'EXTERNAL_CONTINUATION_VETOED')
            self.assertTrue(receipt['stopAll'])


class RainCapture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.task = Path(self.tmp.name)
        self.capture = self.task/'capture'; self.capture.mkdir()
        import lanes
        self.planner = lanes
        manifest = json.loads(lanes.R0040_MANIFEST.read_text())
        self.manifest = manifest
        self.prepared = {'sources': {'research': {'root': '/sources/research'}, 'historical': {'root': '/sources/history'}},
                         'trees': {name: {'root': '/private/work/prepared/trees/'+name} for name in ('main','r0040','r003f','r0035')}}
        self.admission = {'status': 'PASS', 'work': str(self.task/'work/r0040-capture'),
                          'manifest': str(lanes.R0040_MANIFEST),
                          'prepared': str(self.task/'work/r0040-capture/receipts/prepared.json'),
                          'process': str(self.capture/'r0040-preparation/process.json'),
                          'wrapperSha256': lanes.R0040_CAPTURE_WRAPPER_SHA256,
                          'expectedCapture': manifest['plannedNativeCell']['expectedCapture'], 'pins': manifest['pins']}
        self.args = SimpleNamespace(task=self.task, research=Path('/sources/research'), baseline=Path('/sources/main'),
                                    historical=Path('/sources/history'), engine='chromium', r002f=False,
                                    work_orders=['R0040'], r0040_mode='capture', phase='lane', lane='r0040-chromium-capture')
        self.plan = self.planner.make_plan(self.prepared,self.capture/'lanes',python_playwright=Path(sys.executable),
                                          node=Path('/runtime/node'),node_modules=Path('/runtime/modules'),pngjs=Path('/runtime/pngjs'),
                                          work_orders=['R0040'],r0040_mode='capture',r0040_preparation=self.admission)
        self.lane = self.plan['lanes'][0]
        expected = self.manifest['plannedNativeCell']['expectedCapture']
        self.raw = {**{k:v for k,v in expected.items() if k not in ('source','effectiveRateMmPerHour')},
                    **self.manifest['pins'], 'before': expected['source'], 'after': expected['source']}
        report = Path(self.lane['result']['path']); report.parent.mkdir(parents=True)
        report.write_text(json.dumps(self.raw))
        self.final = {'protocol':'r0040-capture-final-admission/1','status':'ADMITTED_FOR_OFFLINE_VERIFICATION',
                      'originalExitCode':0,'exitCode':0,'continuationVetoed':False,
                      'originalReport': {'file':str(report),'bytes':report.stat().st_size,
                                         'sha256':hashlib.sha256(report.read_bytes()).hexdigest()},
                      'issues':[],'reportIssues':[],'errors':[],'driverErrors':[],'requests':[], 'pages':[],
                      'scene':{'log':{'errors':[],'continuedExternal':[]}},
                      'closes':{name:{'returned':True,'event':True} for name in ('context','browser','server')},
                      'retentionError':None,'nativeQualification':'NOT_VERIFIED','humanAcceptance':'OUTSTANDING',
                      'timingClass':'instrumented-host-retention'}
        self.write_final()

    def tearDown(self): self.tmp.cleanup()

    def write_final(self):
        M.write_json(self.lane['result']['finalAdmissionPath'],self.final)

    def test_complete_capture_is_admitted_only_for_unchanged_offline_verifier(self):
        result=M.classify_lane(self.lane,0)
        self.assertEqual(result['status'],'ADMITTED_FOR_OFFLINE_VERIFICATION')
        self.assertIs(result['stopAll'],False)
        self.assertEqual(result['nativeQualification'],'NOT_VERIFIED')
        wrapped=M.namespace_status(self.lane,{'returncode':0,'timedOut':False},{**result,'id':self.lane['id']})
        self.assertEqual(wrapped['status'],'ADMITTED_FOR_OFFLINE_VERIFICATION')
        relabeled=M.namespace_status(self.lane,{'returncode':0,'timedOut':False},
                                      {**result,'id':self.lane['id'],'status':'PASS'})
        self.assertEqual(relabeled['status'],'ISOLATION_UNCONFIRMED')

    def test_missing_partial_or_mismatched_capture_receipts_cannot_admit(self):
        original=copy.deepcopy(self.final)
        for mutate in (lambda f:f.clear(), lambda f:f.update(protocol='wrong'),lambda f:f.pop('originalReport'),
                       lambda f:f['originalReport'].update(sha256='0'*64),lambda f:f.update(exitCode=False),
                       lambda f:f['closes']['context'].update(returned=False), lambda f:f.pop('requests'),
                       lambda f:f.update(nativeQualification='PASS')):
            self.final=copy.deepcopy(original);mutate(self.final);self.write_final()
            self.assertEqual(M.classify_lane(self.lane,0)['status'],'INCOMPLETE')
        Path(self.lane['result']['finalAdmissionPath']).unlink()
        self.assertEqual(M.classify_lane(self.lane,0)['status'],'INCOMPLETE')
        self.final=original;self.write_final()
        Path(self.lane['result']['path']).unlink()
        self.assertEqual(M.classify_lane(self.lane,0)['status'],'INCOMPLETE')

    def test_capture_failures_timeout_and_prevented_veto_keep_their_original_priority(self):
        self.assertEqual(M.classify_lane(self.lane,7)['status'],'FAIL')
        self.assertEqual(M.classify_lane(self.lane,-9,True)['status'],'INCOMPLETE')
        self.final.update(status='FAILED',originalExitCode=5,exitCode=5,issues=['original driver failed'])
        self.write_final()
        self.assertEqual(M.classify_lane(self.lane,-9,True)['status'],'FAIL')
        self.final.update(originalExitCode=0,exitCode=1,issues=['late page crash'])
        self.write_final()
        self.assertEqual(M.classify_lane(self.lane,1)['status'],'FAIL')
        self.final.update(status='CONTINUATION_VETOED',exitCode=86,continuationVetoed=True)
        self.write_final()
        veto=M.classify_lane(self.lane,86)
        self.assertEqual(veto['status'],M.VETO_STATUS);self.assertTrue(veto['stopAll'])
        self.assertEqual(M.namespace_status(self.lane,{'returncode':0,'timedOut':False},
                                            {**veto,'id':self.lane['id']})['status'],M.VETO_STATUS)
        self.assertEqual(M.namespace_status(self.lane,{'returncode':9,'timedOut':False},
                                            {**veto,'id':self.lane['id']})['status'],'ISOLATION_UNCONFIRMED')

    def test_capture_campaign_rejects_changed_mode_cell_or_substitute_plan(self):
        value={'schemaVersion':1,'engine':'chromium','r003fDpr':1,'workOrders':['R0040'],
               'r0040Mode':'capture','r002f':{'enabled':False,'dpr':1,'rounds':1,'section':'all'}}
        path=self.task/'campaign.json';path.write_text(json.dumps(value))
        self.assertEqual(M.read_campaign(path),value)
        for change in ({'r0040Mode':True},{'r0040Mode':'pass'},{'engine':'firefox'},{'workOrders':['R003F']}):
            path.write_text(json.dumps({**value,**change}))
            with self.assertRaises(ValueError):M.read_campaign(path)
        self.assertEqual(M.admit_plan(self.plan,self.args),[self.lane])
        for mutate in (lambda p:p.update(r0040Mode='options'),lambda p:p['lanes'][0]['argv'].__setitem__(-1,'M2'),
                       lambda p:p['lanes'][0].update(clearEnv=[]),lambda p:p['lanes'][0]['env'].update(R0040_OPTIONS='x'),
                       lambda p:p['lanes'][0].update(timeoutSeconds=720),
                       lambda p:p['lanes'][0]['result'].update(kind='r0040-options')):
            changed=copy.deepcopy(self.plan);mutate(changed)
            with self.assertRaises(ValueError):M.admit_plan(changed,self.args)
        runtime={'node':'/runtime/node','python':sys.executable,'modules':'/runtime/modules'}
        argv=M.isolated_command(self.args,runtime,'lane',self.lane['id'])
        self.assertEqual(argv[argv.index('--r0040-mode')+1],'capture')

    def test_capture_environment_removes_inherited_options_before_actual_child(self):
        M.write_json(self.capture/'lanes.json',self.plan)
        with patch.object(M,'controls',return_value='/private/isolation.json'),\
             patch.dict(os.environ,{'R0040_OPTIONS':'forbidden','R0040_DISPERSION':'differential'}),\
             patch.object(M,'run_bounded',return_value={'returncode':0,'timedOut':False}) as run:
            self.assertEqual(M.inside(self.args,{}),0)
        self.assertNotIn('R0040_OPTIONS',run.call_args.args[2])
        self.assertEqual(run.call_args.args[2]['R0040_DISPERSION'],'common')
        self.assertEqual(run.call_args.args[0],self.lane['argv'])

    def test_actual_partial_preparation_keeps_original_stage_logs_and_independent_lanes(self):
        import r0040_capture_preparation_controls as fixtures
        with tempfile.TemporaryDirectory() as tmp:
            fixture=fixtures.RecipeFixture(Path(tmp))
            # The first full patch succeeds; the second postimage is rejected by
            # the actual unchanged recipe in a real child, with explicit test pins.
            fixture.body['stages'][1]['files']['tools/qa/precip_models.js']['sha256']='0'*64
            fixture.save_manifest()
            self.args.phase='prepare';self.args.lane=None;self.args.work_orders=['R0040','R0035']
            runtime={'python':sys.executable,'node':'/runtime/node','modules':'/runtime/modules','pngjs':'/runtime/pngjs'}
            original_run=M.run_bounded; calls=[]
            def bounded(argv,cwd,env,stdout,stderr,timeout):
                calls.append(argv); name=Path(argv[1]).name
                if name=='r0040_capture_prepare.py':
                    command=list(argv)
                    for key in ('manifest','research','historical','main'):
                        command[command.index('--'+key)+1]=str(getattr(fixture,key))
                    code=('import sys; sys.path.insert(0,sys.argv.pop(1)); import r0040_capture_prepare as p; '
                          'p.MANIFEST_SHA256=sys.argv.pop(1); raise SystemExit(p.main())')
                    command=[sys.executable,'-c',code,str(M.HERE),fixtures.sha(fixture.manifest.read_bytes()),*command[2:]]
                    return original_run(command,cwd,env,stdout,stderr,timeout)
                Path(stdout).parent.mkdir(parents=True,exist_ok=True)
                Path(stdout).write_text('controlled common preparation or planner');Path(stderr).write_text('')
                if name=='prepare.py':
                    M.write_json(self.task/'work/prepared/receipts/prepared.json',self.prepared)
                elif name=='lanes.py':
                    entry=self.capture/'r0040-preparation-entry.json'
                    admission=self.planner.admit_r0040(self.prepared,self.task/'work/r0040-capture',
                               self.capture/'r0040-preparation/process.json',entry,self.capture/'lanes',
                               Path('/runtime/node'),Path('/runtime/modules/playwright'))
                    plan=self.planner.make_plan(self.prepared,self.capture/'lanes',python_playwright=Path(sys.executable),
                              node=Path('/runtime/node'),node_modules=Path('/runtime/modules'),pngjs=Path('/runtime/pngjs'),
                              work_orders=['R0040','R0035'],r0040_mode='capture',r0040_preparation=admission)
                    Path(stdout).write_text(json.dumps(plan))
                return {'returncode':0,'timedOut':False}
            with patch.object(M,'controls',return_value='/private/isolation.json'),patch.object(M,'run_bounded',side_effect=bounded),patch.dict(os.environ):
                self.assertEqual(M.inside(self.args,runtime),0)
            entry=json.loads((self.capture/'r0040-preparation-entry.json').read_text())
            self.assertEqual(entry['returncode'],1)
            process=json.loads((self.capture/'r0040-preparation/process.json').read_text())
            self.assertEqual(process['returncode'],1);self.assertEqual(process['status'],'INCOMPLETE')
            original=json.loads((self.capture/'r0040-preparation-original/prepared.json').read_text())
            self.assertEqual(len(original['stages']),1)
            self.assertTrue((self.capture/'r0040-preparation-original/2-apply.stdout').is_file())
            self.assertIn('AssertionError',(self.capture/'r0040-preparation/recipe.stderr').read_text())
            self.assertFalse(any(p.name=='precip_models.js' for p in self.capture.rglob('*')))
            plan=json.loads((self.capture/'lanes.json').read_text())
            self.assertEqual([p['workOrder'] for p in plan['lanes']],['R0040','R0035','R0035'])
            self.assertEqual(plan['lanes'][0]['argv'],[])
            self.assertTrue(all(p['argv'] for p in plan['lanes'][1:]))
            planner=calls[-1]
            self.assertEqual(planner[planner.index('--r0040-mode')+1],'capture')
            self.assertEqual(planner[planner.index('--r0040-entry-process')+1],str(self.capture/'r0040-preparation-entry.json'))

    def test_acquisition_campaign_can_complete_without_claiming_lossless_pass(self):
        M.write_json(self.capture/'lanes.json',self.plan)
        calls=[]
        def run(argv,*args):
            calls.append(argv)
            if len(calls)>1:
                result=M.classify_lane(self.lane,0)
                M.write_json(self.capture/'lane-status'/(self.lane['id']+'.json'),{**result,'id':self.lane['id']})
            return {'returncode':0,'timedOut':False}
        with patch.object(M,'isolated_command',return_value=['isolated']),patch.object(M,'run_bounded',side_effect=run):
            self.assertEqual(M.outside(self.args,{}),0)
        report=json.loads((self.capture/'observation.json').read_text())
        self.assertEqual(report['status'],'OBSERVED')
        self.assertEqual(report['lanes'][0]['status'],'ADMITTED_FOR_OFFLINE_VERIFICATION')
        self.assertEqual(report['lanes'][0]['nativeQualification'],'NOT_VERIFIED')

    def test_failed_capture_preparation_is_not_run_while_selected_prayer_lane_proceeds(self):
        self.args.work_orders=['R0040','R002F'];self.args.r002f=True
        self.args.r002f_dpr=1;self.args.r002f_rounds=5;self.args.r002f_section='prayer'
        plan=self.planner.make_plan(self.prepared,self.capture/'lanes',python_playwright=Path(sys.executable),
                 node=Path('/runtime/node'),node_modules=Path('/runtime/modules'),pngjs=Path('/runtime/pngjs'),
                 work_orders=self.args.work_orders,r0040_mode='capture',
                 r0040_preparation={'status':'INCOMPLETE','reason':'controlled partial source'},include_r002f=True,
                 r002f_preparation={'status':'PASS','trees':{'baseline':{'root':'/prepared/baseline'},
                                                           'candidate':{'root':'/prepared/candidate'}}},
                 r002f_rounds=5,r002f_section='prayer')
        M.write_json(self.capture/'lanes.json',plan);calls=[]
        def run(argv,*args):
            calls.append(argv)
            if len(calls)>1:
                M.write_json(self.capture/'lane-status/r002f-chromium-dpr1.json',
                             {'id':'r002f-chromium-dpr1','status':'PASS','returncode':0,'timedOut':False,'stopAll':False})
            return {'returncode':0,'timedOut':False}
        with patch.object(M,'isolated_command',side_effect=lambda _a,_r,phase,lane=None:[phase,lane]),\
             patch.object(M,'run_bounded',side_effect=run):
            self.assertEqual(M.outside(self.args,{}),2)
        self.assertEqual(calls,[['prepare',None],['lane','r002f-chromium-dpr1']])
        report=json.loads((self.capture/'observation.json').read_text())
        self.assertEqual([row['status'] for row in report['lanes']],['NOT_RUN','PASS'])
        self.assertEqual(report['lanes'][0]['preparationStatus'],'INCOMPLETE')
        self.assertEqual(report['status'],'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES')


class StageIntegration(unittest.TestCase):
    def setUp(self):
        import lanes
        import r0035_stage_controls as fixtures
        self.planner=lanes;self.fixtures=fixtures;self.fixture=fixtures.StageEntryControls()
        self.fixture.setUp();self.root=self.fixture.root
        self.base,self.source,self.source_path=self.fixture.source_fixture()
        self.baseline=patch.object(lanes,'BASELINE',self.source['arms']['main']['commit']);self.baseline.start()
        self.task=self.root/'task';(self.task/'capture').mkdir(parents=True)
        self.prepared={'protocol':'salah-hosted-native-preparation/1','status':'PREPARED',
            'sources':{'research':{'root':str(self.fixture.driver_path.parents[2])},'historical':{'root':'/bounded/history'}},
            'trees':{'main':{'root':self.source['arms']['main']['root']},'r0035':{'root':str(self.base)},
                     'r0040':{'root':'/bounded/rain'},'r003f':{'root':'/bounded/moon'}}}
        self.prepared_path=self.task/'work/prepared/receipts/prepared.json'
        M.write_json(self.prepared_path,self.prepared)
        M.write_json(self.task/'capture/preparation-process.json',{'returncode':0,'timedOut':False})
        self.args=SimpleNamespace(task=self.task,research=self.fixture.driver_path.parents[2],baseline=self.root/'main',
            historical=Path('/bounded/history'),engine='chromium',work_orders=['R0035'],r002f=False,
            retain_evidence=False,r0035_guard='off',r0035_scope='all',r0035_mode='timing',r0035_stages=True)
        self.runtime={'python':sys.executable,'node':'/bounded/node','modules':'/bounded/modules','pngjs':'/bounded/pngjs'}
        self.folder=self.task/'capture/r0035-stage-preparation'
    def tearDown(self):
        self.baseline.stop();self.fixture.tearDown()
    def prepared_plan(self):
        result=M.prepare_stages(self.args,self.runtime,self.task/'work/prepared')
        self.assertEqual(result['returncode'],0)
        admission=self.planner.admit_r0035_stages(self.prepared,self.prepared_path,self.folder/'process.json','off','all')
        self.assertEqual(admission['status'],'PASS',admission)
        (self.task/'capture/lanes').mkdir()
        plan=self.planner.make_plan(self.prepared,self.task/'capture/lanes',python_playwright=Path(sys.executable),
            node=Path('/bounded/node'),node_modules=Path('/bounded/modules'),pngjs=Path('/bounded/pngjs'),
            work_orders=self.args.work_orders,r0035_guard='off',r0035_mode='timing',r0035_stages=True,
            r0035_stage_preparation=admission)
        return plan,plan['lanes'][-1]
    def test_actual_preparation_and_planner_admit_only_current_source_flags_and_zero_exit(self):
        plan,lane=self.prepared_plan();self.assertEqual(M.admit_plan(plan,self.args),[lane])
        self.assertEqual((self.folder/'original-prepared.json').read_bytes(),self.prepared_path.read_bytes())
        self.assertEqual((self.folder/'original-lab-identity.json').read_bytes(),(self.base/'r0035-lab-identity.json').read_bytes())
        rejected=self.planner.admit_r0035_stages(self.prepared,self.prepared_path,self.folder/'process.json','default','all')
        self.assertEqual(rejected['status'],'INCOMPLETE');self.assertIn('flags',rejected['reason'])
        original=(self.folder/'process.json').read_bytes()
        for change in ({'returncode':7},{'returncode':True},{'timedOut':True},{'retentionError':'bounded retention fault'}):
            value=json.loads(original);value.update(change);M.write_json(self.folder/'process.json',value)
            with self.subTest(change=change):
                self.assertEqual(self.planner.admit_r0035_stages(self.prepared,self.prepared_path,
                    self.folder/'process.json','off','all')['status'],'INCOMPLETE')

    def test_native_wrapper_refuses_changed_preparation_before_original_import(self):
        import observe_r0035_stages as observer
        plan,lane=self.prepared_plan();argv=lane['argv'][2:]
        process=self.folder/'process.json';body=json.loads(process.read_bytes());body['returncode']=7;M.write_json(process,body)
        loader=self.fixture.loader
        with patch.object(observer.material,'support',return_value=loader),patch.object(loader,'verify_isolation',return_value={}),\
             patch.object(loader,'load_driver',side_effect=AssertionError('original driver must not load')) as load:
            with self.assertRaisesRegex(ValueError,'changed after planning'):observer.main(argv)
            argv[argv.index('--preparation-sha256')+1]=M.digest(process)
            with self.assertRaisesRegex(ValueError,'did not complete'):observer.main(argv)
            load.assert_not_called()
        self.assertFalse(Path(lane['output']).exists());self.assertFalse(Path(lane['evidenceRetention']['output']).exists())

    def test_stage_selection_and_namespace_forwarding_cannot_be_omitted_or_substituted(self):
        plan,lane=self.prepared_plan()
        self.assertEqual(M.admit_plan({**plan,'lanes':[]},self.args)[0]['preparation']['status'],'INCOMPLETE')
        for changed in ({**plan,'lanes':[lane,lane]},{**plan,'r0035Stages':False}):
            with self.assertRaises(ValueError):M.admit_plan(changed,self.args)
        changed=copy.deepcopy(plan);changed['lanes'][0]['argv'][1]='unwrapped.py'
        with self.assertRaises(ValueError):M.admit_plan(changed,self.args)
        changed=copy.deepcopy(plan);changed['r0035Controls']['guard']='default'
        with self.assertRaises(ValueError):M.admit_plan(changed,self.args)
        command=M.isolated_command(self.args,self.runtime,'prepare')
        self.assertEqual(command.count('--r0035-stages'),1)
        self.args.r0035_stages=False
        self.assertNotIn('--r0035-stages',M.isolated_command(self.args,self.runtime,'prepare'))

    def test_explicit_stage_campaign_rejects_ignored_or_contradictory_controls(self):
        value={'schemaVersion':1,'engine':'chromium','r003fDpr':1,'workOrders':['R0035'],
               'r002f':{'enabled':False,'dpr':1,'rounds':1,'section':'all'},
               'r0035':{'guard':'off','scope':'all','mode':'timing'},'r0035Stages':True}
        path=self.root/'campaign.json';M.write_json(path,value);self.assertEqual(M.read_campaign(path),value)
        for change in ({'r0035Stages':'yes'},{'r0035Stages':1},{'r0035Stages':None},{'evidenceRetention':True},
                       {'workOrders':['R0040']},{'r0035':{'guard':'off','scope':'all','mode':'both'}}):
            M.write_json(path,{**value,**change})
            with self.subTest(change=change),self.assertRaises(ValueError):M.read_campaign(path)

    def test_inside_preparation_forwards_actual_stage_custody_to_the_planner(self):
        self.args.phase='prepare';self.args.lane=None;calls=[];real_run=M.run_bounded
        def run(argv,cwd,env,stdout,stderr,timeout):
            calls.append(argv)
            if Path(argv[1]).name=='r0035_stage_materialize.py':return real_run(argv,cwd,env,stdout,stderr,timeout)
            return {'returncode':0,'timedOut':False}
        with patch.object(M,'controls',return_value='bounded-isolation-receipt'),patch.object(M,'run_bounded',side_effect=run),\
             patch.dict(os.environ,{},clear=False):
            self.assertEqual(M.inside(self.args,self.runtime),0)
        self.assertEqual([Path(c[1]).name for c in calls],['prepare.py','r0035_stage_materialize.py','lanes.py'])
        planner=calls[-1];self.assertIn('--r0035-stages',planner)
        self.assertEqual(planner[planner.index('--r0035-stage-process')+1],str(self.folder/'process.json'))
        self.assertEqual(json.loads((self.folder/'process.json').read_text())['returncode'],0)

    def test_optional_stage_source_failure_retains_streams_and_allows_other_selected_lane(self):
        self.args.work_orders=['R0040','R0035']
        def failed(argv,cwd,env,stdout,stderr,timeout):
            M.write_json(Path(argv[argv.index('--out')+1])/'partial.json',{'stage':'bounded failure'})
            stdout.write_text('retained partial stdout');stderr.write_text('retained source failure')
            return {'returncode':7,'timedOut':False}
        with patch.object(M,'run_bounded',side_effect=failed):
            result=M.prepare_stages(self.args,self.runtime,self.task/'work/prepared')
        self.assertEqual(result['returncode'],7);self.assertEqual((self.folder/'stderr').read_text(),'retained source failure')
        admission=self.planner.admit_r0035_stages(self.prepared,self.prepared_path,self.folder/'process.json','off','all')
        self.assertEqual(admission['status'],'INCOMPLETE')
        plan=self.planner.make_plan(self.prepared,self.task/'capture/lanes',python_playwright=Path(sys.executable),
            node=Path('/bounded/node'),node_modules=Path('/bounded/modules'),pngjs=Path('/bounded/pngjs'),
            work_orders=self.args.work_orders,r0035_guard='off',r0035_mode='timing',r0035_stages=True,
            r0035_stage_preparation=admission)
        M.write_json(self.task/'capture/lanes.json',plan);calls=[]
        def run(argv,*args):
            calls.append(argv)
            if argv[0]=='lane':M.write_json(self.task/'capture/lane-status/r0040-chromium.json',
                {'id':'r0040-chromium','status':'PASS','stopAll':False,'returncode':0,'timedOut':False})
            return {'returncode':0,'timedOut':False}
        with patch.object(M,'isolated_command',side_effect=lambda a,r,phase,lane=None:[phase,lane]),patch.object(M,'run_bounded',side_effect=run):
            self.assertEqual(M.outside(self.args,self.runtime),2)
        self.assertEqual(calls,[['prepare',None],['lane','r0040-chromium']])
        self.assertEqual(json.loads((self.task/'capture/observation.json').read_text())['lanes'][1]['status'],'NOT_RUN')

    def run_original_with_stages(self,failed=False):
        import observe_r0035_stages as observer
        import types
        plan,lane=self.prepared_plan();driver=self.fixture.loader.load_driver(self.fixture.driver_path)
        driver.start_server=lambda *args:'http://127.0.0.1:8765'
        class Browser:
            version='bounded-original-driver';ordinal=0
            def close(self):pass
            def new_context(inner,**kwargs):
                inner.ordinal+=1;label=['main','unmodified','mitigated'][inner.ordinal-1]
                context=self.fixtures.fixtures.FakeBrowser(driver).context;original=context.page.evaluate
                def evaluate(expression,*values):
                    if expression==observer.READ_STAGES:return None if label=='main' else self.fixtures.stage_trace()
                    if expression==driver.READ:
                        result=self.fixtures.fixtures.scene()
                        if failed and label=='unmodified':result['prayersReady']=False
                        return result
                    if 'window.__r0035.end=' in expression:
                        publication=None if label=='main' else {'start':1000,'end':3000,'overflow':False,
                            'initial':{'status':'active','tier':'refined','identity':'accepted'},
                            'events':[{'kind':'publication','at':t,'epoch':1,'tier':'refined','identity':'accepted',
                                'utcMs':1000+t,'ageMs':0,'changed':True,'nonempty':True} for t in range(1000,3001,80)]}
                        return {'start':1000,'end':3000,'frames':list(range(1000,3000,16)),
                            'states':[dict(self.fixtures.fixtures.scene(),t=1100),dict(self.fixtures.fixtures.scene(),t=2100)],
                            'publication':publication}
                    return original(expression,*values)
                context.page.evaluate=evaluate;return context
        browser=Browser()
        class Playwright:
            def __enter__(self):return SimpleNamespace(chromium=SimpleNamespace(launch=lambda:browser))
            def __exit__(self,*args):pass
        api=types.ModuleType('playwright.sync_api');api.sync_playwright=Playwright;api.TimeoutError=self.fixtures.fixtures.BrowserTimeout
        path=self.task/'capture/isolation'/lane['id']/'receipt.json'
        M.write_json(path,{'protocol':'salah-hosted-native-isolation/1','passed':True,'browserControl':{'passed':True},
                          'uid':1001,'netns':'net:[200]','outerNetns':'net:[100]'})
        with patch.object(observer.material,'support',return_value=self.fixture.loader),\
             patch.object(self.fixture.loader,'load_driver',return_value=driver),\
             patch.dict(sys.modules,{'playwright.sync_api':api}),\
             patch.dict(os.environ,{'SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT':str(path)}),\
             patch.object(os,'getuid',return_value=1001),patch.object(os,'readlink',return_value='net:[200]'):
            observer.main(lane['argv'][2:])
        return plan,lane

    def test_actual_original_driver_and_stage_receipts_preserve_failed_admission_at_exit_zero(self):
        plan,lane=self.run_original_with_stages(failed=True)
        verdict=M.classify_lane(lane,0)
        self.assertEqual(verdict['status'],'FAIL');self.assertEqual(verdict['originalStatus'],'FAIL')
        self.assertEqual(verdict['stageObservation']['status'],'OBSERVED',verdict)
        self.assertEqual(json.loads(Path(lane['result']['path']).read_text())[1]['qualification']['verdict'],'failed')

    def test_stage_success_requires_all_original_reports_and_distinct_complete_evidence(self):
        plan,lane=self.run_original_with_stages();verdict=M.classify_lane(lane,0)
        self.assertEqual(verdict['status'],M.STAGES_OBSERVED,verdict)
        self.assertEqual(verdict['originalStatus'],'PASS')
        path=Path(lane['result']['stageDriverPath']);raw=path.read_bytes()
        for change in ({'observations':[]},{'trials':2},{'status':'INCOMPLETE'},{'identitySha256':'0'*64}):
            body=json.loads(raw);body.update(change);M.write_json(path,body)
            self.assertEqual(M.classify_lane(lane,0)['status'],'INCOMPLETE')
        path.write_bytes(raw)
        original=Path(lane['output'])/'01-unmodified/trial.json';original.write_bytes(original.read_bytes()+b'\n')
        self.assertEqual(M.classify_lane(lane,0)['status'],'INCOMPLETE')

    def test_stage_veto_timeout_and_outer_namespace_failure_keep_precedence(self):
        plan,lane=self.prepared_plan()
        inner=M.classify_lane(lane,86);self.assertEqual(inner['status'],M.VETO_STATUS);self.assertTrue(inner['stopAll'])
        inner['id']=lane['id']
        self.assertEqual(M.namespace_status(lane,{'returncode':0,'timedOut':False},inner)['status'],M.VETO_STATUS)
        self.assertEqual(M.namespace_status(lane,{'returncode':86,'timedOut':False},inner)['status'],'ISOLATION_FAIL')
        self.assertEqual(M.namespace_status(lane,{'returncode':1,'timedOut':False},inner)['status'],'ISOLATION_UNCONFIRMED')
        self.assertEqual(M.namespace_status(lane,{'returncode':0,'timedOut':True},inner)['status'],'ISOLATION_UNCONFIRMED')
        self.assertEqual(M.classify_lane(lane,-15,True)['status'],'INCOMPLETE')
        bogus={'id':lane['id'],'status':'PASS','stopAll':False,'returncode':0,'timedOut':False}
        self.assertEqual(M.namespace_status(lane,{'returncode':0,'timedOut':False},bogus)['status'],'ISOLATION_UNCONFIRMED')


if __name__ == '__main__': unittest.main()
