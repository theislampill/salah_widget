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


# Deliberate source-only runtime doubles, independent of each plan under test.
CONTROL_RUNTIME = {'node':'/control/node', 'python':'/control/python', 'modules':'/control/modules',
                   'playwright':'/control/modules/playwright', 'pngjs':'/control/modules/pngjs'}


def campaign_plan(lanes, orders, retained=False):
    for lane in lanes:
        command=[CONTROL_RUNTIME['python' if lane['workOrder'] == 'R0035' else 'node'], '/control/recipe']
        if lane['workOrder']=='R0040':command.append(CONTROL_RUNTIME['playwright'])
        if lane['workOrder'] in ('R003F','R002F'):command+=['--playwright',CONTROL_RUNTIME['playwright']]
        if lane['workOrder']=='R003F':command+=['--pngjs',CONTROL_RUNTIME['pngjs']]
        lane.setdefault('argv', [] if lane.get('preparation', {}).get('status') == 'INCOMPLETE' else command)
        lane.setdefault('env', {'NODE_PATH':CONTROL_RUNTIME['modules']})
    return {'protocol': 'salah-hosted-native-lanes/1', 'sequential': True,
            'workOrders': orders, 'evidenceRetention': retained, 'lanes': lanes}


class DispatchRuntimeAdmission(unittest.TestCase):
    """Explicit source-only runtime authority; no copied plan field is trusted."""
    def setUp(self):
        import test_lanes
        self.fixture=test_lanes.LaneControls();self.fixture.setUp()
        self.runtime={'node':'/dependencies/node','python':'/dependencies/venv/bin/python',
                      'modules':'/dependencies/node_modules','playwright':'/dependencies/node_modules/playwright',
                      'pngjs':'/dependencies/node_modules/pngjs'}
        self.args=SimpleNamespace(engine='chromium',r002f=True,r002f_dpr=1,
                                  work_orders=['R0040','R003F','R0035','R002F'])
    def plan(self,retained=False):
        self.args.retain_evidence=retained
        return self.fixture.plan(include_r002f=True,retain_evidence=retained,
            r002f_preparation={'status':'PASS','trees':{'baseline':{'root':'/synthetic/baseline'},
                                                      'candidate':{'root':'/synthetic/candidate'}}})
    def test_every_executable_and_copied_original_is_bound_before_dispatch(self):
        for retained in (False,True):
            plan=self.plan(retained)
            self.assertEqual(M.admit_plan(plan,self.args,self.runtime),plan['lanes'])
            for index in range(len(plan['lanes'])):
                for together in (False,True):
                    changed=copy.deepcopy(plan);lane=changed['lanes'][index]
                    lane['argv'][0]='/synthetic/unadmitted-executable'
                    if together and 'evidenceRetention' in lane:
                        lane['evidenceRetention']['originalArgv'][0]=lane['argv'][0]
                    with self.subTest(retained=retained,lane=lane['id'],together=together),\
                         self.assertRaisesRegex(ValueError,'acquired runtime'):
                        M.admit_plan(changed,self.args,self.runtime)
    def test_runtime_is_required_explicit_absolute_and_role_specific(self):
        plan=self.plan()
        for runtime in (None,{}, {'node':'node','python':self.runtime['python']},
                        {'node':self.runtime['python'],'python':self.runtime['node']},
                        {'node':False,'python':self.runtime['python']}):
            with self.subTest(runtime=runtime),self.assertRaises(ValueError):M.admit_plan(plan,self.args,runtime)
        with self.assertRaises(TypeError):M.admit_plan(plan,self.args)
    def test_all_lane_runtime_preflight_precedes_any_optional_source_verifier(self):
        plan=self.plan();plan['lanes'][-1]['argv'][0]='/synthetic/unadmitted-executable'
        with patch.object(M,'validate_prepared',side_effect=AssertionError('no source verifier yet')) as check,\
             patch.object(M.matrix,'admit',side_effect=AssertionError('no matrix verifier yet')) as matrix_check,\
             self.assertRaisesRegex(ValueError,'acquired runtime'):
            M.admit_plan(plan,self.args,self.runtime)
        check.assert_not_called();matrix_check.assert_not_called()
    def test_acquired_packages_reject_joint_environment_and_argument_rebinding(self):
        for retained in (False,True):
            plan=self.plan(retained)
            for index in range(len(plan['lanes'])):
                for coupled in (False,True):
                    changed=copy.deepcopy(plan);lane=changed['lanes'][index]
                    lane['env']['NODE_PATH']='/synthetic/unadmitted-modules'
                    if coupled:
                        commands=[lane['argv']]
                        if 'evidenceRetention' in lane:commands.append(lane['evidenceRetention']['originalArgv'])
                        for command in commands:
                            for i,part in enumerate(command):
                                if part.startswith(self.runtime['modules']+'/'):
                                    command[i]=part.replace(self.runtime['modules'],'/synthetic/unadmitted-modules',1)
                    with self.subTest(lane=lane['id'],retained=retained,coupled=coupled),\
                         self.assertRaisesRegex(ValueError,'acquired runtime'):M.admit_plan(changed,self.args,self.runtime)
    def test_explicit_playwright_pngjs_paths_are_bound_even_with_unchanged_environment(self):
        for retained in (False,True):
            plan=self.plan(retained)
            for index,lane in enumerate(plan['lanes']):
                for dependency in ('playwright','pngjs'):
                    if self.runtime[dependency] not in lane['argv']:continue
                    changed=copy.deepcopy(plan);row=changed['lanes'][index]
                    for command in [row['argv'],row.get('evidenceRetention',{}).get('originalArgv',[])]:
                        for i,part in enumerate(command):
                            if part==self.runtime[dependency]:command[i]='/synthetic/unadmitted-package'
                    with self.subTest(lane=lane['id'],dependency=dependency),\
                         self.assertRaisesRegex(ValueError,'acquired runtime'):M.admit_plan(changed,self.args,self.runtime)


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
                code = M.outside(args, CONTROL_RUNTIME)
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
                    code = M.outside(args, CONTROL_RUNTIME)
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
            admitted = M.admit_plan(campaign_plan(lanes, orders), args, CONTROL_RUNTIME)
            self.assertEqual([row['id'] for row in admitted], [identifier for identifier, _ in expected])
            row = next(row for row in admitted if row['id'] in missing)
            self.assertEqual(row['preparation']['status'], 'INCOMPLETE')
            self.assertIn('missing from the plan', row['preparation']['reason'])
        self.assertEqual(len(M.admit_plan(campaign_plan([], orders), args, CONTROL_RUNTIME)), 5)

    def test_duplicate_wrong_identity_or_unselected_lanes_are_rejected_before_execution(self):
        args = SimpleNamespace(engine='chromium', r002f=False, work_orders=['R0035'])
        timing = {'id': 'r0035-chromium-timing', 'workOrder': 'R0035'}
        capture = {'id': 'r0035-chromium-capture', 'workOrder': 'R0035'}
        for rows in ([timing, timing, capture], [timing, {'id': 'unknown', 'workOrder': 'R0035'}],
                     [timing, {'id': 'r0035-firefox-capture', 'workOrder': 'R0035'}],
                     [timing, {**capture, 'workOrder': 'R0040'}],
                     [timing, capture, {'id': 'r0040-chromium', 'workOrder': 'R0040'}]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                M.admit_plan(campaign_plan(rows, ['R0035']), args, CONTROL_RUNTIME)
        for metadata in ({'workOrders': ['R0040']}, {'evidenceRetention': True}):
            with self.subTest(metadata=metadata), self.assertRaises(ValueError):
                M.admit_plan({**campaign_plan([timing, capture], ['R0035']), **metadata}, args, CONTROL_RUNTIME)
        for evidence in ({'evidenceRetention': {'instrumented': True}}, {'evidenceRetention': 'yes'}):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                M.admit_plan(campaign_plan([{**timing, **evidence}, capture], ['R0035']), args, CONTROL_RUNTIME)
        args.retain_evidence = True
        with self.assertRaises(ValueError):
            M.admit_plan(campaign_plan([timing, capture], ['R0035'], True), args, CONTROL_RUNTIME)

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
                    self.assertEqual(M.outside(args, CONTROL_RUNTIME), 2)
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
                self.assertEqual(M.outside(args, CONTROL_RUNTIME), 2)
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
                self.assertEqual(M.outside(args, CONTROL_RUNTIME), 0)
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
        with self.assertRaises(ValueError): M.admit_plan(plan,args, CONTROL_RUNTIME)
        with self.assertRaises(ValueError): M.admit_plan({**plan,'r003fHarness':'corrected-b0'},args, CONTROL_RUNTIME)
        missing=M.admit_plan({**plan,'r003fHarness':'corrected-b0','lanes':[]},args, CONTROL_RUNTIME)
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
        self.assertEqual([row['id'] for row in M.admit_plan(plan, args, CONTROL_RUNTIME)], [timing['id']])
        missing = M.admit_plan({**plan, 'lanes': []}, args, CONTROL_RUNTIME)
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]['preparation']['status'], 'INCOMPLETE')
        for change in ({'r0035Controls': {'guard': 'default', 'scope': 'all', 'mode': 'timing'}},
                       {'lanes': [timing, {'id': 'r0035-chromium-capture', 'workOrder': 'R0035'}]}):
            with self.subTest(change=change), self.assertRaises(ValueError): M.admit_plan({**plan, **change}, args, CONTROL_RUNTIME)

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
                         patch.object(M.runner_environment, 'current', return_value={'scope':'SOURCE_CONTROL_ONLY'}), \
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
            lane = {'id': identifier, 'workOrder': 'R0040', 'argv': [CONTROL_RUNTIME['node'], '/control/offline-driver', CONTROL_RUNTIME['playwright']], 'cwd': str(task),
                    'stdout': str(capture/'driver.stdout'), 'stderr': str(capture/'driver.stderr'), 'timeoutSeconds': 5,
                    'stopAllOnExit': [86], 'evidenceRetention': {'instrumented': True},
                    'result': {'kind': 'r0040-options', 'path': str(capture/'absent-original-report.json')}}
            (capture/'lanes.json').write_text(json.dumps(campaign_plan([lane], ['R0040'], True)))
            args = SimpleNamespace(task=task, engine='chromium', phase='lane', lane=identifier,
                                   work_orders=['R0040'], retain_evidence=True)
            with patch.object(M, 'controls', return_value='/private/isolation.json'), patch.dict(os.environ), \
                 patch.object(M, 'run_bounded', return_value={'returncode': 86, 'timedOut': False}):
                self.assertEqual(M.inside(args, CONTROL_RUNTIME), 0)
            receipt = json.loads((capture/'lane-status'/(identifier+'.json')).read_text())
            self.assertEqual(receipt['returncode'], 86)
            self.assertEqual(receipt['status'], 'EXTERNAL_CONTINUATION_VETOED')
            self.assertTrue(receipt['stopAll'])


class RainCapture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.task = Path(self.tmp.name)
        self.capture = self.task/'capture'; self.capture.mkdir()
        self.runtime={'node':'/runtime/node','python':sys.executable,'modules':'/runtime/modules',
                      'playwright':'/runtime/modules/playwright','pngjs':'/runtime/pngjs'}
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
        self.assertEqual(M.admit_plan(self.plan,self.args, self.runtime),[self.lane])
        for mutate in (lambda p:p.update(r0040Mode='options'),lambda p:p['lanes'][0]['argv'].__setitem__(-1,'M2'),
                       lambda p:p['lanes'][0].update(clearEnv=[]),lambda p:p['lanes'][0]['env'].update(R0040_OPTIONS='x'),
                       lambda p:p['lanes'][0].update(timeoutSeconds=720),
                       lambda p:p['lanes'][0]['result'].update(kind='r0040-options')):
            changed=copy.deepcopy(self.plan);mutate(changed)
            with self.assertRaises(ValueError):M.admit_plan(changed,self.args, self.runtime)
        runtime={'node':'/runtime/node','python':sys.executable,'modules':'/runtime/modules'}
        argv=M.isolated_command(self.args,runtime,'lane',self.lane['id'])
        self.assertEqual(argv[argv.index('--r0040-mode')+1],'capture')

    def test_capture_environment_removes_inherited_options_before_actual_child(self):
        M.write_json(self.capture/'lanes.json',self.plan)
        with patch.object(M,'controls',return_value='/private/isolation.json'),\
             patch.dict(os.environ,{'R0040_OPTIONS':'forbidden','R0040_DISPERSION':'differential'}),\
             patch.object(M,'run_bounded',return_value={'returncode':0,'timedOut':False}) as run:
            self.assertEqual(M.inside(self.args,self.runtime),0)
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
            self.assertEqual(M.outside(self.args,self.runtime),0)
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
            self.assertEqual(M.outside(self.args,self.runtime),2)
        self.assertEqual(calls,[['prepare',None],['lane','r002f-chromium-dpr1']])
        report=json.loads((self.capture/'observation.json').read_text())
        self.assertEqual([row['status'] for row in report['lanes']],['NOT_RUN','PASS'])
        self.assertEqual(report['lanes'][0]['preparationStatus'],'INCOMPLETE')
        self.assertEqual(report['status'],'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES')


class DateOnlyCapture(unittest.TestCase):
    """Synthetic custody with the real clock-admission function; no browser."""
    write_final = RainCapture.write_final

    def setUp(self):
        RainCapture.setUp(self)
        import shutil
        self.node = shutil.which('node')
        self.runtime['node']=self.node
        entry=self.capture/'r0040-preparation-entry.json'
        M.write_json(entry, {'protocol':'synthetic-current-source-double/1'})
        for key in ('prepared','process'):
            M.write_json(self.admission[key], {'protocol':'synthetic-current-source-double/1','role':key})
        self.admission['entryReceipt']={'path':str(entry),'sha256':M.digest(entry)}
        self.admission['dateOnlyPreparation']={**self.admission['entryReceipt'],'actualExitCode':0}
        self.admission['dateOnlyDiagnostic']=self.planner.r0040_dateonly_identity()
        self.admission['sourceCustody']={
            'manifestSha256':self.planner.R0040_MANIFEST_SHA256,
            'recipeSourceSha256':'9fc26a75cb62c145f9de7bd7aa386ac6714c238f3e08089558d34f02882f9730',
            'preparationProcess':{'path':self.admission['process'],'sha256':M.digest(Path(self.admission['process']))},
            'prepared':{'path':self.admission['prepared'],'sha256':M.digest(Path(self.admission['prepared']))},
            'preparationOuterExit':'Coordinator must independently require the preparation entry actual exit zero.'}
        self.plan=self.planner.make_plan(self.prepared,self.capture/'lanes',python_playwright=Path(sys.executable),
            node=Path(self.node),node_modules=Path('/runtime/modules'),pngjs=Path('/runtime/pngjs'),
            work_orders=['R0040'],r0040_mode='capture-dateonly',r0040_preparation=self.admission)
        self.lane=self.plan['lanes'][0];self.args.r0040_mode='capture-dateonly';self.args.lane=self.lane['id']
        original=Path(self.lane['result']['path']);M.write_json(original,self.raw)
        self.final.update(status='ADMITTED_DATE_ONLY_FOR_OFFLINE_VERIFICATION',timingClass='instrumented-date-only-clock',
            diagnostic=self.planner.r0040_dateonly_identity(),
            originalReport={'file':str(original),'bytes':original.stat().st_size,'sha256':M.digest(original)},
            pages=[{'id':1,'errors':[],'closed':True}],
            requests=[{'id':1,'url':'http://127.0.0.1:3187/index.html','method':'GET','resourceType':'document',
                'observedBy':['context','route'],'callbackState':'returned','browserState':'finished',
                'actions':[{'action':'continue','state':'completed','destination':'http://127.0.0.1:3187/index.html','refused':False}]}],
            scene={'base':'http://127.0.0.1:3187','options':{'clock':'running','utcMs':self.raw['utcMs']},
                   'log':{'errors':[],'continuedExternal':[]}},
            closes={name:{'called':True,'returned':True,'event':True} for name in ('context','browser','server')})
        self.final['closes']['browser']['disconnections']=[{'duringClose':True}]
        keys=('Date','performance','performanceNow','timeOrigin','setTimeout','clearTimeout','setInterval',
              'clearInterval','requestAnimationFrame','cancelAnimationFrame','queueMicrotask')
        def sample(t):
            return {'performanceBeforeMs':t,'performanceAfterMs':t+0.25,'dateNowMs':self.raw['utcMs']+int(t)-100,
                    'newDateMs':self.raw['utcMs']+int(t)-100,'timeOriginMs':100000,'preserved':dict.fromkeys(keys,True)}
        proof={'protocol':'r0040-date-only-clock-proof/1','status':'COMPLETE','utcMs':self.raw['utcMs'],
               'anchorPerformanceMs':100,'timeOriginMs':100000,'before':sample(101),'after':sample(155),
               'timer':{'requestedDelayMs':40,'sample':sample(145)},
               'frames':[{'timestampMs':110,'sample':sample(111)},{'timestampMs':125,'sample':sample(126)}],'error':None}
        run=subprocess.run([self.node,'-e','const d=require(process.argv[1]); process.stdout.write(JSON.stringify(d.admitClockProof(JSON.parse(process.argv[2]),Number(process.argv[3]))));',
                            str(M.HERE/'r0040_dateonly.cjs'),json.dumps(proof),str(self.raw['utcMs'])],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.final['clockProofs']=[{'status':'OBSERVED','raw':proof,'admission':json.loads(run.stdout),'error':None}]
        isolation=Path(self.lane['result']['isolationReceiptPath'])
        M.write_json(isolation,{'protocol':'salah-hosted-native-isolation/1','passed':True,'uid':1001,
                               'netns':'net:[synthetic-inner]','outerNetns':'net:[synthetic-outer]',
                               'browserControl':{'passed':True}})
        self.sources={'isolation':{'file':str(isolation),'sha256':M.digest(isolation)},
            **self.admission['sourceCustody'],'preparationEntry':self.admission['dateOnlyPreparation'],
            'sources':{'research':self.manifest['researchInputs'],'historical':self.manifest['stages'][-1]['files'],
                       'main':self.manifest['main']['runtimeFiles']},
            'originalArgv':self.lane['evidenceRetention']['originalArgv'][2:],
            'diagnostic':self.planner.r0040_dateonly_identity()}
        verified={'isolation':self.sources['isolation'],'preparationEntry':self.sources['preparationEntry'],
                  'diagnostic':self.sources['diagnostic'],'sourcePopulation':{'research':12,'historical':6,'main':177}}
        self.current={'returncode':0,'timedOut':False,'stdout':json.dumps(verified),'stderr':''}
        self.current_patch=patch.object(M,'_dateonly_current_check',return_value=self.current)
        self.check=self.current_patch.start();self.addCleanup(self.current_patch.stop)
        self.write_evidence()

    def tearDown(self): self.tmp.cleanup()

    def write_evidence(self):
        M.write_json(self.lane['result']['finalAdmissionPath'],self.final)
        payloads=[{'event':'sources',**self.sources},
                  {'event':'date-only-clock-proof','proof':self.final['clockProofs'][0]},
                  {'event':'driver-process-ended',**self.final}]
        self.rows=[{'sequence':i+1,'atUtc':'2000-01-01T00:00:00.000Z','monotonicNs':str(i+1),**row}
                   for i,row in enumerate(payloads)]
        Path(self.lane['result']['journalPath']).write_text(''.join(json.dumps(row)+'\n' for row in self.rows))

    def test_dateonly_complete_evidence_has_distinct_acquisition_not_product_pass(self):
        verdict=M.classify_lane(self.lane,0)
        self.assertEqual(verdict['status'],'ADMITTED_DATE_ONLY_FOR_OFFLINE_VERIFICATION',verdict)
        self.assertEqual(verdict['timingClass'],'instrumented-date-only-clock')
        self.assertEqual(verdict['nativeQualification'],'NOT_VERIFIED')
        self.assertEqual(verdict['humanAcceptance'],'OUTSTANDING')
        inner={**verdict,'id':self.lane['id']}
        self.assertEqual(M.namespace_status(self.lane,{'returncode':0,'timedOut':False},inner)['status'],verdict['status'])
        for status in ('PASS',M.CAPTURE_ADMITTED):
            self.assertEqual(M.namespace_status(self.lane,{'returncode':0,'timedOut':False},{**inner,'status':status})['status'],'ISOLATION_UNCONFIRMED')

    def test_dateonly_clock_claim_is_recomputed_from_actual_function_even_with_consistent_journal(self):
        original=copy.deepcopy(self.final)
        for mutate in (lambda f:f['clockProofs'][0]['raw']['after'].update(dateNowMs=self.raw['utcMs']),
                       lambda f:f['clockProofs'][0]['raw']['before']['preserved'].update(setTimeout=False),
                       lambda f:f['clockProofs'][0]['raw'].update(timeOriginMs=999),
                       lambda f:f['clockProofs'][0]['raw'].update(frames=[]),
                       lambda f:f['clockProofs'][0]['admission'].update(rafCallbacks=True),
                       lambda f:f['diagnostic']['helper'].update(transformedSha256='0'*64)):
            self.final=copy.deepcopy(original);mutate(self.final);self.write_evidence()
            self.assertEqual(M.classify_lane(self.lane,0)['status'],'INCOMPLETE')

    def test_dateonly_terminal_journal_and_full_source_population_are_required(self):
        for mutation in ('missing-final','duplicate-final','reordered','different-final','truncated','missing-source','partial-main'):
            self.write_evidence();rows=copy.deepcopy(self.rows); journal=Path(self.lane['result']['journalPath'])
            if mutation=='missing-final': rows.pop()
            elif mutation=='duplicate-final': rows.append(copy.deepcopy(rows[-1]))
            elif mutation=='reordered': rows[0],rows[1]=rows[1],rows[0]
            elif mutation=='different-final': rows[-1]['exitCode']=False
            elif mutation=='missing-source': rows.pop(0)
            elif mutation=='partial-main': rows[0]['sources']['main'].pop(next(iter(rows[0]['sources']['main'])))
            text=''.join(json.dumps(row)+'\n' for row in rows)
            journal.write_text(text[:-1] if mutation=='truncated' else text)
            self.assertEqual(M.classify_lane(self.lane,0)['status'],'INCOMPLETE',mutation)

    def test_dateonly_late_request_crash_and_disconnect_cannot_be_relabeled_as_admitted(self):
        original=copy.deepcopy(self.final)
        for mutate in (lambda f:f['requests'][0].update(browserState='failed'),
                       lambda f:f['requests'][0]['actions'][0].update(destination='https://unapproved.invalid/'),
                       lambda f:f['requests'].append(copy.deepcopy(f['requests'][0])),
                       lambda f:f['pages'][0].update(crashed=True),
                       lambda f:f['closes']['browser']['disconnections'][0].update(duringClose=False),
                       lambda f:f['closes']['context'].update(called=False)):
            self.final=copy.deepcopy(original);mutate(self.final);self.write_evidence()
            self.assertEqual(M.classify_lane(self.lane,0)['status'],'INCOMPLETE')

    def test_dateonly_current_namespace_preparation_or_source_failure_retains_diagnostics(self):
        for failure in ({'returncode':1,'timedOut':False,'stdout':'partial source check','stderr':'controlled current namespace mismatch'},
                        {'returncode':None,'timedOut':True,'stdout':'partial source check','stderr':'controlled source timeout'}):
            self.check.return_value=failure
            result=M.classify_lane(self.lane,0)
            self.assertEqual(result['status'],'INCOMPLETE');self.assertEqual(result['currentSourceCheck'],failure)
        self.check.return_value=self.current
        altered=self.task/'altered-manifest.json';altered.write_bytes(M.R0040_MANIFEST.read_bytes()+b'\n')
        original_sha=self.admission['sourceCustody']['manifestSha256']
        self.admission['sourceCustody']['manifestSha256']=self.sources['manifestSha256']=M.digest(altered)
        self.write_evidence()
        with patch.object(M,'R0040_MANIFEST',altered):
            self.assertEqual(M.classify_lane(self.lane,0)['status'],'INCOMPLETE')
        self.admission['sourceCustody']['manifestSha256']=self.sources['manifestSha256']=original_sha
        self.write_evidence()
        Path(self.admission['process']).write_text('{"changed":true}')
        self.assertEqual(M.classify_lane(self.lane,0)['status'],'INCOMPLETE')

    def test_dateonly_failure_veto_timeout_and_outer_namespace_precedence(self):
        self.assertEqual(M.classify_lane(self.lane,9)['status'],'FAIL')
        self.assertEqual(M.classify_lane(self.lane,-9,True)['status'],'INCOMPLETE')
        self.final.update(status='FAILED',exitCode=1,issues=['controlled late cleanup failure']);self.write_evidence()
        self.assertEqual(M.classify_lane(self.lane,-9,True)['status'],'FAIL')
        veto=M.classify_lane(self.lane,86);self.assertEqual(veto['status'],M.VETO_STATUS)
        self.assertIn('not evidence of an actual network escape',veto['reason'])
        for process,status in (({'returncode':0,'timedOut':False},M.VETO_STATUS),
                               ({'returncode':86,'timedOut':False},'ISOLATION_FAIL'),
                               ({'returncode':1,'timedOut':False},'ISOLATION_UNCONFIRMED')):
            self.assertEqual(M.namespace_status(self.lane,process,{**veto,'id':self.lane['id']})['status'],status)

    def test_dateonly_selected_population_argv_and_preparation_paths_cannot_be_substituted(self):
        self.assertEqual(M.admit_plan(self.plan,self.args, self.runtime),[self.lane])
        missing=copy.deepcopy(self.plan);missing['lanes']=[]
        self.assertEqual(M.admit_plan(missing,self.args, self.runtime)[0]['preparation']['status'],'INCOMPLETE')
        for mutate in (lambda p:p['lanes'].append(copy.deepcopy(p['lanes'][0])),
                       lambda p:p['lanes'][0]['argv'].__setitem__(-1,'M2'),
                       lambda p:p['lanes'][0]['argv'].__setitem__(1,str(M.HERE/'retain_r0040_capture.cjs')),
                       lambda p:p['lanes'][0]['preparation']['entryReceipt'].update(path='/other/entry.json'),
                       lambda p:p['lanes'][0]['result'].update(kind='r0040-capture'),
                       lambda p:p['lanes'][0]['result'].update(isolationReceiptPath='/other/receipt.json')):
            plan=copy.deepcopy(self.plan);mutate(plan)
            with self.assertRaises(ValueError): M.admit_plan(plan,self.args, self.runtime)
        runtime={'node':self.node,'python':sys.executable,'modules':'/runtime/modules'}
        argv=M.isolated_command(self.args,runtime,'lane',self.lane['id'])
        self.assertEqual(argv[argv.index('--r0040-mode')+1],'capture-dateonly')

    def test_dateonly_environment_and_outer_campaign_preserve_distinct_status(self):
        M.write_json(self.capture/'lanes.json',self.plan)
        receipt=self.lane['result']['isolationReceiptPath']
        with patch.object(M,'controls',return_value=receipt),patch.dict(os.environ,{'R0040_OPTIONS':'forbidden'}),\
             patch.object(M,'run_bounded',return_value={'returncode':0,'timedOut':False}) as run:
            self.assertEqual(M.inside(self.args,self.runtime),0)
        self.assertNotIn('R0040_OPTIONS',run.call_args.args[2])
        self.assertEqual(run.call_args.args[2]['R0040_DISPERSION'],'common')
        with patch.object(M,'isolated_command',return_value=['synthetic-isolated']),\
             patch.object(M,'run_bounded',return_value={'returncode':0,'timedOut':False}) as outer_run:
            self.assertEqual(M.outside(self.args,self.runtime),0)
        self.assertEqual(outer_run.call_args.args[-1], 355)
        report=json.loads((self.capture/'observation.json').read_text())
        self.assertEqual(report['status'],'OBSERVED')
        self.assertEqual(report['lanes'][0]['status'],'ADMITTED_DATE_ONLY_FOR_OFFLINE_VERIFICATION')
        self.assertEqual(report['lanes'][0]['nativeQualification'],'NOT_VERIFIED')

    def test_dateonly_optional_preparation_threads_actual_outer_failure_without_fallback(self):
        self.args.phase='prepare';self.args.lane=None;self.args.work_orders=['R0040','R0035']
        # A different private attempt prevents overwriting setup custody.
        self.args.task=self.task/'attempt';capture=self.args.task/'capture';capture.mkdir(parents=True)
        runtime={'python':sys.executable,'node':self.node,'modules':'/runtime/modules','pngjs':'/runtime/pngjs'}
        calls=[]
        def bounded(argv,cwd,env,stdout,stderr,timeout):
            calls.append({'argv':argv,'timeout':timeout})
            Path(stdout).parent.mkdir(parents=True,exist_ok=True)
            name=Path(argv[1]).name
            Path(stdout).write_text('controlled preparation stream');Path(stderr).write_text('')
            if name=='prepare.py':
                M.write_json(self.args.task/'work/prepared/receipts/prepared.json',self.prepared)
            elif name=='r0040_capture_prepare.py':
                Path(stderr).write_text('controlled original source refusal')
                return {'returncode':7,'timedOut':False}
            elif name=='lanes.py':
                entry=capture/'r0040-preparation-entry.json'
                admission=self.planner.admit_r0040(self.prepared,self.args.task/'work/r0040-capture',
                    capture/'r0040-preparation/process.json',entry,capture/'lanes',Path(self.node),
                    Path('/runtime/modules/playwright'),mode='capture-dateonly')
                self.assertEqual(admission['status'],'INCOMPLETE')
                plan=self.planner.make_plan(self.prepared,capture/'lanes',python_playwright=Path(sys.executable),
                    node=Path(self.node),node_modules=Path('/runtime/modules'),pngjs=Path('/runtime/pngjs'),
                    work_orders=self.args.work_orders,r0040_mode='capture-dateonly',r0040_preparation=admission)
                M.write_json(stdout,plan)
            return {'returncode':0,'timedOut':False}
        with patch.object(M,'controls',return_value='/synthetic/isolation.json'),patch.object(M,'run_bounded',side_effect=bounded):
            self.assertEqual(M.inside(self.args,runtime),0)
        entry=json.loads((capture/'r0040-preparation-entry.json').read_text())
        self.assertEqual(entry['returncode'],7);self.assertEqual(entry['cwd'],str(M.HERE))
        self.assertEqual(entry['argv'],calls[1]['argv']);self.assertEqual(calls[1]['timeout'],240)
        self.assertEqual(calls[-1]['timeout'],120)
        argv=calls[-1]['argv'];self.assertEqual(argv[argv.index('--r0040-mode')+1],'capture-dateonly')
        self.assertEqual(argv[argv.index('--r0040-entry-process')+1],str(capture/'r0040-preparation-entry.json'))
        plan=json.loads((capture/'lanes.json').read_text())
        self.assertEqual(plan['lanes'][0]['argv'],[])
        self.assertEqual([p['id'] for p in plan['lanes'][1:]],['r0035-chromium-timing','r0035-chromium-capture'])
        self.assertTrue(all(p['argv'] for p in plan['lanes'][1:]))


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
        # This bounded model fixture has no complete Git checkout; only that
        # existing common-source boundary is doubled. Optional source/custody
        # materialization and current re-admission below are real.
        self.common_check=patch.object(M,'validate_prepared',return_value=self.prepared)
        self.common_check.start();self.addCleanup(self.common_check.stop)
        M.write_json(self.task/'capture/preparation-process.json',{'returncode':0,'timedOut':False})
        self.args=SimpleNamespace(task=self.task,research=self.fixture.driver_path.parents[2],baseline=self.root/'main',
            historical=Path('/bounded/history'),engine='chromium',work_orders=['R0035'],r002f=False,
            retain_evidence=False,r0035_guard='off',r0035_scope='all',r0035_mode='timing',r0035_stages=True)
        self.runtime={'python':sys.executable,'node':'/bounded/node','modules':'/bounded/modules',
                      'playwright':'/bounded/modules/playwright','pngjs':'/bounded/pngjs'}
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
        plan['preparedReceipt']={'path':str(self.prepared_path),'sha256':M.digest(self.prepared_path)}
        return plan,plan['lanes'][-1]
    def test_actual_preparation_and_planner_admit_only_current_source_flags_and_zero_exit(self):
        plan,lane=self.prepared_plan();self.assertEqual(M.admit_plan(plan,self.args, self.runtime),[lane])
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

    def test_stage_executable_and_copied_runtime_rebinding_precede_source_readmission(self):
        plan,lane=self.prepared_plan()
        self.assertEqual(M.admit_plan(plan,self.args,self.runtime),[lane])
        for fields in (('argv',),('original',),('argv','original'),('argv','original','copied')):
            changed=copy.deepcopy(plan);row=changed['lanes'][0]
            for field in fields:
                if field=='argv':row['argv'][0]='/synthetic/unadmitted-python'
                elif field=='original':row['evidenceRetention']['originalArgv'][0]='/synthetic/unadmitted-python'
                else:row['preparation']['python']='/synthetic/unadmitted-python'
            with self.subTest(fields=fields),patch.object(M,'admit_r0035_stages') as check,\
                 self.assertRaisesRegex(ValueError,'acquired runtime'):M.admit_plan(changed,self.args,self.runtime)
            check.assert_not_called()
        process=self.folder/'process.json';body=json.loads(process.read_bytes())
        body['argv'][0]='/synthetic/unadmitted-python';M.write_json(process,body)
        with patch.object(M,'admit_r0035_stages') as check,self.assertRaisesRegex(ValueError,'acquired runtime'):
            M.admit_plan(plan,self.args,self.runtime)
        check.assert_not_called()

    def test_stage_full_current_admission_rejects_changed_source_and_receipt_authority(self):
        plan,lane=self.prepared_plan()
        for mutate in (lambda p:p['lanes'][0]['preparation'].update(process='/synthetic/other-process'),
                       lambda p:p['lanes'][0]['preparation']['custody']['process'].update(sha256='0'*64),
                       lambda p:p['lanes'][0]['preparation'].update(root='/synthetic/other-source'),
                       lambda p:p['preparedReceipt'].update(sha256='0'*64),
                       lambda p:p['lanes'][0]['preparation'].update(python='/synthetic/ignored-python')):
            changed=copy.deepcopy(plan);mutate(changed)
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):M.admit_plan(changed,self.args,self.runtime)
        process=self.folder/'process.json';original=process.read_bytes()
        for change in ({'returncode':7},{'timedOut':True},{'materializerSha256':'0'*64}):
            M.write_json(process,{**json.loads(original),**change})
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'current preparation'):
                M.admit_plan(plan,self.args,self.runtime)
            process.write_bytes(original)
        source=Path(lane['preparation']['root'])/M.stage_material.LIVE;original=source.read_bytes()
        source.write_bytes(original+b'\n<!-- controlled source drift -->\n')
        with self.assertRaisesRegex(ValueError,'current preparation'):M.admit_plan(plan,self.args,self.runtime)
        source.write_bytes(original)
        self.assertEqual(M.admit_plan(plan,self.args,self.runtime),[lane])

    def test_stage_selection_and_namespace_forwarding_cannot_be_omitted_or_substituted(self):
        plan,lane=self.prepared_plan()
        self.assertEqual(M.admit_plan({**plan,'lanes':[]},self.args, self.runtime)[0]['preparation']['status'],'INCOMPLETE')
        for changed in ({**plan,'lanes':[lane,lane]},{**plan,'r0035Stages':False}):
            with self.assertRaises(ValueError):M.admit_plan(changed,self.args, self.runtime)
        changed=copy.deepcopy(plan);changed['lanes'][0]['argv'][1]='unwrapped.py'
        with self.assertRaises(ValueError):M.admit_plan(changed,self.args, self.runtime)
        changed=copy.deepcopy(plan);changed['r0035Controls']['guard']='default'
        with self.assertRaises(ValueError):M.admit_plan(changed,self.args, self.runtime)
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


class TabhideControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.task=Path(self.temp.name)
        self.output=self.task/'capture/lanes/r002f-tabhide-chromium-dpr1';self.output.mkdir(parents=True)
        self.lane={'id':'r002f-tabhide-chromium-dpr1','workOrder':'R002F','engine':'chromium','dpr':1,
            'timeoutSeconds':1800,'output':str(self.output),'argv':['node',str(M.HERE/'r002f_tabhide.cjs')],
            'result':{'kind':'r002f-tabhide','path':str(self.output/'result.json'),
                'expectedSourceManifestSha256':M.R002F_TABHIDE_MANIFEST_SHA256,'expectedSources':{'baseline':{},'candidate':{}}},
            'preparation':{'trees':{'baseline':{'root':'/private/main'},'candidate':{'root':'/private/candidate'}}},
            'evidenceRetention':{'instrumented':True},'stopAllOnExit':[86]}
        self.report={'protocol':'r002f-tabhide-native/1','status':M.TABHIDE_OBSERVED,
                     'sourceManifestSha256':M.R002F_TABHIDE_MANIFEST_SHA256,'sources':{'baseline':{},'candidate':{}},'rows':[]}

    def save(self,value=None):M.write_json(self.output/'result.json',self.report if value is None else value)

    def test_tabhide_campaign_selects_only_reviewed_population_and_old_default_remains(self):
        value={'schemaVersion':1,'engine':'chromium','r003fDpr':1,'workOrders':['R002F'],
               'r002f':{'enabled':True,'dpr':1,'rounds':1,'section':'all'},'r002fRoute':'tabhide'}
        file=self.task/'campaign.json';M.write_json(file,value);self.assertEqual(M.read_campaign(file),value)
        for change in ({'engine':'firefox'},{'r002fRoute':True},{'r002fRoute':'synthetic'}):
            M.write_json(file,{**value,**change})
            with self.assertRaises(ValueError):M.read_campaign(file)
        value.pop('r002fRoute');M.write_json(file,value);self.assertNotIn('r002fRoute',M.read_campaign(file))

    def test_tabhide_report_admission_requires_offline_verifier_and_records_actual_invocation(self):
        self.save()
        def verify(argv,cwd,env,stdout,stderr,timeout):
            # Explicit nonnative boundary double; no native report is fabricated.
            self.assertEqual(argv[2],'--verify-json');self.assertEqual(timeout,45)
            self.assertEqual(argv[-1],str(self.task/'capture/isolation'/self.lane['id']/'receipt.json'))
            M.write_json(stdout,{'status':M.TABHIDE_OBSERVED,'nativeQualification':'LIFECYCLE_OBSERVATION_ONLY','humanAcceptance':'OUTSTANDING'})
            Path(stderr).write_text('');return {'returncode':0,'timedOut':False,'elapsedSeconds':.01}
        with patch.object(M,'run_bounded',side_effect=verify):got=M.classify_lane(self.lane,0)
        self.assertEqual(got['status'],M.TABHIDE_OBSERVED);self.assertEqual(got['verification']['returncode'],0)
        self.assertEqual(got['nativeQualification'],'LIFECYCLE_OBSERVATION_ONLY')
        for result in ({'returncode':2,'timedOut':False},{'returncode':-15,'timedOut':True}):
            with patch.object(M,'run_bounded',return_value=result):
                self.assertEqual(M.classify_lane(self.lane,0)['status'],'INCOMPLETE')

    def test_tabhide_failures_survive_timeout_missing_report_and_failed_later_cleanup(self):
        self.assertEqual(M.classify_lane(self.lane,1,True)['status'],'FAIL')
        for body in ({'protocol':'r002f-tabhide-native/1','status':'FAIL','rows':None},
                     {'rows':[{'verdict':{'status':'FAIL'}}]}):
            self.save(body);self.assertEqual(M.classify_lane(self.lane,-15,True)['status'],'FAIL')
        for body in ({'rows':None},{'rows':[{'verdict':None}]},{}):
            self.save(body);self.assertEqual(M.classify_lane(self.lane,0)['status'],'INCOMPLETE')

    def test_tabhide_veto_and_actual_boundary_failure_are_distinct_and_stop_all(self):
        self.save({'status':M.VETO_STATUS,'continuationVetoed':True});veto=M.classify_lane(self.lane,86)
        self.assertEqual(veto['status'],M.VETO_STATUS);self.assertTrue(veto['stopAll']);self.assertIn('not evidence',veto['reason'])
        self.save({'status':'ISOLATION_FAIL','continuationVetoed':False})
        self.assertEqual(M.classify_lane(self.lane,86)['status'],'ISOLATION_FAIL')
        self.save({});self.assertEqual(M.classify_lane(self.lane,86)['status'],'ISOLATION_FAIL')

    def test_tabhide_outer_namespace_failure_cannot_be_promoted_by_observed_inner(self):
        inner={'id':self.lane['id'],'status':M.TABHIDE_OBSERVED,'returncode':0,'timedOut':False,'stopAll':False,
               'nativeQualification':'LIFECYCLE_OBSERVATION_ONLY'}
        self.assertEqual(M.namespace_status(self.lane,{'returncode':0,'timedOut':False},inner)['status'],M.TABHIDE_OBSERVED)
        for outer,status in (({'returncode':86,'timedOut':False},'ISOLATION_FAIL'),
                             ({'returncode':1,'timedOut':False},'ISOLATION_UNCONFIRMED'),
                             ({'returncode':0,'timedOut':True},'ISOLATION_UNCONFIRMED')):
            self.assertEqual(M.namespace_status(self.lane,outer,inner)['status'],status)
        inner['status']='PASS';self.assertEqual(M.namespace_status(self.lane,{'returncode':0,'timedOut':False},inner)['status'],'ISOLATION_UNCONFIRMED')

    def test_tabhide_wrong_source_and_observation_status_never_invoke_verifier(self):
        for changes in ({'sourceManifestSha256':'0'*64},{'sources':{}},{'status':'PASS'},{'status':'INCOMPLETE'}):
            self.save({**self.report,**changes})
            with patch.object(M,'run_bounded') as run:self.assertEqual(M.classify_lane(self.lane,0)['status'],'INCOMPLETE')
            run.assert_not_called()

    def test_tabhide_plan_requires_exact_identity_population_and_aggregate_deadline(self):
        import lanes
        prepared={'sources':{'research':{'root':'/research'},'historical':{'root':'/history'}},
                  'trees':{k:{'root':'/private/'+k} for k in ('main','r0035','r003f','r0040')}}
        plan=lanes.make_plan(prepared,self.task/'capture/lanes',python_playwright=Path('/python'),node=Path('/node'),
                            node_modules=Path('/modules'),pngjs=Path('/pngjs'),include_r002f=True,work_orders=['R002F'],r002f_route='tabhide')
        args=SimpleNamespace(task=self.task,engine='chromium',r002f=True,r002f_route='tabhide',work_orders=['R002F'])
        self.assertEqual(M.admit_plan(plan,args, CONTROL_RUNTIME)[0]['argv'],[])
        for mutate in (lambda x:x['lanes'][0].update(timeoutSeconds=900),lambda x:x['lanes'][0]['result'].update(kind='r002f-probe'),
                       lambda x:x['lanes'][0]['result'].update(expectedRows=[]),lambda x:x['lanes'][0].update(argv=['substitute'])):
            changed=copy.deepcopy(plan);mutate(changed)
            with self.assertRaises(ValueError):M.admit_plan(changed,args, CONTROL_RUNTIME)

    def test_tabhide_budgets_are_selected_without_extending_default_recipe_deadlines(self):
        self.assertEqual(M.campaign_budget({}), {'coordinatorSeconds':2640,'workflowObservationMinutes':45})
        headed=M.campaign_budget({'r002fRoute':'tabhide','workOrders':['R002F']})
        self.assertEqual(headed,{'coordinatorSeconds':3900,'workflowObservationMinutes':66})
        self.assertGreaterEqual(headed['coordinatorSeconds'],1920+1800+75)
        self.assertGreater(headed['workflowObservationMinutes']*60,headed['coordinatorSeconds'])
        for campaign in ({'r002fRoute':'invalid'},{'r002fRoute':'tabhide','workOrders':['R002F','R003F']},
                         {'r002fRoute':'tabhide','workOrders':['R002F'],'r003fHarness':'corrected-matrix'}):
            with self.assertRaises(ValueError):M.campaign_budget(campaign)
        workflow=(M.HERE.parents[2]/'.github/workflows/research-native-pilot.yml').read_text()
        self.assertIn('timeout-minutes: 300',workflow)
        self.assertIn('timeout-minutes: ${{ fromJSON(steps.budget.outputs.observation_minutes) }}',workflow)
        self.assertIn("campaign_budget(read_campaign",workflow)

    def test_tabhide_outer_uses_selected_namespace_budget_and_retains_timeout_precedence(self):
        # Explicit process/isolation boundaries: no namespace or browser is launched.
        (self.task/'capture/lanes.json').write_text('{}')
        args=SimpleNamespace(task=self.task,engine='chromium',work_orders=['R002F'],r002f=True,r002f_route='tabhide')
        calls=[]
        def run(argv,_cwd,_env,_out,_err,timeout):
            calls.append((argv,timeout))
            if len(calls)==1:return {'returncode':0,'timedOut':False}
            M.write_json(self.task/'capture/lane-status'/(self.lane['id']+'.json'),
                         {'id':self.lane['id'],'status':M.TABHIDE_OBSERVED,'returncode':0,
                          'timedOut':False,'stopAll':False,'nativeQualification':'LIFECYCLE_OBSERVATION_ONLY'})
            return {'returncode':-15,'timedOut':True}
        with patch.object(M,'isolated_command',side_effect=lambda _a,_r,phase,lane=None:[phase,lane]), \
             patch.object(M,'admit_plan',return_value=[self.lane]),patch.object(M,'run_bounded',side_effect=run), \
             patch.object(M.time,'monotonic',return_value=100):
            self.assertEqual(M.outside(args,CONTROL_RUNTIME),2)
        self.assertEqual([timeout for _,timeout in calls],[1920,1875])
        report=json.loads((self.task/'capture/observation.json').read_text())
        self.assertEqual(report['budget']['coordinatorSeconds'],3900)
        self.assertEqual(report['lanes'][0]['status'],'ISOLATION_UNCONFIRMED')
        self.assertTrue(report['lanes'][0]['stopAll'])


class MatrixCoordinatorControls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.task=Path(self.tmp.name)
        self.runtime={'node':'/synthetic/admitted-node','python':'/synthetic/python','modules':'/synthetic/modules',
                      'playwright':'/synthetic/modules/playwright','pngjs':'/synthetic/modules/pngjs'}
        self.selector={'id':'owner_11150942_owner_wax_-81.9_150_clear_shipped_reduce_default','variant':'B0'}
        self.args=SimpleNamespace(task=self.task,engine='chromium',r003f_dpr=1,r003f_harness='corrected-matrix',r003f_matrix=self.selector,work_orders=['R003F'])
    def blocked_plan(self):
        import test_lanes
        fixture=test_lanes.LaneControls();fixture.setUp();fixture.base=self.task/'capture/lanes'
        return fixture.plan(work_orders=['R003F'],r003f_harness='corrected-matrix',r003f_matrix=self.selector)
    def test_matrix_budget_preserves_legacy_and_rejects_unsummed_combination(self):
        self.assertEqual(M.campaign_budget({}),{'coordinatorSeconds':2640,'workflowObservationMinutes':45})
        budget=M.observation_budget(self.args);self.assertGreater(budget['coordinatorSeconds'],3000)
        with self.assertRaises(ValueError):M.campaign_budget({'r003fHarness':'corrected-matrix','r003fMatrix':self.selector,'workOrders':['R003F'],'engine':'chromium','r003fDpr':1,'r002fRoute':'tabhide'})
    def test_matrix_selected_missing_duplicate_or_substituted_plan_cannot_succeed(self):
        p=self.blocked_plan();self.assertEqual(len(M.admit_plan(p,self.args, self.runtime)),1)
        p['lanes']=[];self.assertEqual(M.admit_plan(p,self.args, self.runtime)[0]['preparation']['status'],'INCOMPLETE')
        p=self.blocked_plan();p['lanes']*=2
        with self.assertRaises(ValueError):M.admit_plan(p,self.args, self.runtime)
        p=self.blocked_plan();p['r003fMatrix']['variant']='all'
        with self.assertRaises(ValueError):M.admit_plan(p,self.args, self.runtime)
    def admitted_plan(self):
        plan=self.blocked_plan();control=M.matrix_campaign(self.args)
        entry=self.task/'capture/r003f-matrix-preparation-entry.json'
        child=self.task/'capture/r003f-matrix-preparation/process.json'
        inputs={'prepared':'/synthetic/common','common-process':'/synthetic/process','common-context':'/synthetic/context',
                'out':str(self.task/'work/r003f-matrix'),'receipts':str(child.parent),
                'node':self.runtime['node'],'pins-sha256':M.MATRIX_PINS}
        M.write_json(child,{'inputs':inputs,'argv':[self.runtime['node'],'/synthetic/materializer']})
        M.write_json(entry,{'argv':M.matrix.prepare_argv(self.runtime['python'],inputs),'process':str(child)})
        preparation={'status':'PASS','root':str(self.task/'work/r003f-matrix'),
            'entry':M.matrix.record(entry),'child':M.matrix.record(child),
            'common':{'prepared':{'path':'/synthetic/common','sha256':'c'*64}},
            'central':{'sha256':M.MATRIX_PINS},'harness':{'materializationSha256':M.matrix.MATERIALIZATION,'outputFiles':[{}]*16},
            'node':self.runtime['node'],'python':self.runtime['python'],'runtime':'/synthetic/runtime','research':'/synthetic/research'}
        lane=M.matrix.make_lane(control,preparation,self.task/'capture/lanes','chromium',1,preparation['node'],
                                Path('/synthetic/modules'),Path('/synthetic/modules/pngjs'),M.MATRIX_PINS)
        plan['lanes']=[lane];plan['preparedReceipt']=copy.deepcopy(preparation['common']['prepared'])
        return plan,copy.deepcopy(preparation)
    def test_matrix_canonical_executable_is_bound_to_actual_runtime_before_readmission(self):
        plan,current=self.admitted_plan()
        with patch.object(M.matrix,'admit',return_value=current) as check:
            self.assertEqual(len(M.admit_plan(plan,self.args,self.runtime)),1)
            check.assert_called_once_with(self.task/'capture/r003f-matrix-preparation-entry.json',M.MATRIX_PINS)
        for fields in (('argv',),('original',),('argv','original'),('argv','original','preparation')):
            changed=copy.deepcopy(plan);lane=changed['lanes'][0]
            for field in fields:
                if field=='argv':lane['argv'][0]='/synthetic/unadmitted-executable'
                elif field=='original':lane['matrixObservation']['originalArgv'][0]='/synthetic/unadmitted-executable'
                else:lane['preparation']['node']='/synthetic/unadmitted-executable'
            with self.subTest(fields=fields),patch.object(M.matrix,'admit') as check,\
                 self.assertRaisesRegex(ValueError,'acquired runtime'):M.admit_plan(changed,self.args,self.runtime)
            check.assert_not_called()
    def test_matrix_complete_current_admission_rejects_copied_receipt_path_and_source_substitution(self):
        plan,current=self.admitted_plan()
        mutations=(lambda p:p['lanes'][0]['preparation']['entry'].update(sha256='0'*64),
                   lambda p:p['lanes'][0]['preparation']['child'].update(path='/synthetic/other-child'),
                   lambda p:p['lanes'][0]['preparation']['central'].update(path='/synthetic/other-central'),
                   lambda p:p['lanes'][0]['preparation']['common']['prepared'].update(sha256='0'*64),
                   lambda p:p['lanes'][0]['preparation'].update(runtime='/synthetic/other-runtime'),
                   lambda p:p['lanes'][0]['preparation'].update(research='/synthetic/other-research'),
                   lambda p:p['lanes'][0]['preparation']['harness']['outputFiles'][0].update(sha256='0'*64),
                   lambda p:p['preparedReceipt'].update(path='/synthetic/other-common'))
        for mutate in mutations:
            changed=copy.deepcopy(plan);mutate(changed)
            with self.subTest(mutate=mutate),patch.object(M.matrix,'admit',return_value=current),\
                 self.assertRaisesRegex(ValueError,'current preparation'):M.admit_plan(changed,self.args,self.runtime)
    def test_matrix_canonical_dependency_rebinding_is_rejected_before_any_source_verifier(self):
        plan,current=self.admitted_plan()
        for dependency in ('all','playwright','pngjs'):
            changed=copy.deepcopy(plan);lane=changed['lanes'][0]
            if dependency=='all':
                lane=M.matrix.make_lane(M.matrix_campaign(self.args),copy.deepcopy(current),self.task/'capture/lanes',
                    'chromium',1,self.runtime['node'],Path('/synthetic/unadmitted-modules'),
                    Path('/synthetic/unadmitted-modules/pngjs'),M.MATRIX_PINS)
                changed['lanes']=[lane]
            else:
                for command in (lane['argv'],lane['matrixObservation']['originalArgv']):
                    command[command.index('--'+dependency)+1]='/synthetic/unadmitted-package'
            with self.subTest(dependency=dependency),patch.object(M.matrix,'admit') as check,\
                 self.assertRaisesRegex(ValueError,'acquired runtime'):M.admit_plan(changed,self.args,self.runtime)
            check.assert_not_called()

    def test_matrix_report_zero_never_passes_without_actual_intake(self):
        lane=self.blocked_plan()['lanes'][0];file=Path(lane['result']['path']);file.parent.mkdir(parents=True);file.write_text(json.dumps({'status':'DIAGNOSTIC'}))
        r=M.classify_lane(lane,0);self.assertEqual(r['status'],'INCOMPLETE');self.assertFalse(r['stopAll'])
    def test_matrix_actual_intake_result_requires_full_source_and_namespace_binding(self):
        import r003f_matrix_campaign as matrix
        import shutil
        control=M.matrix_campaign(self.args);target=self.task/'capture/lanes'
        admission={'status':'PASS','root':str(self.task/'work/r003f-matrix'),'runtime':'/synthetic/runtime',
                   'entry':{'path':str(self.task/'capture/r003f-matrix-preparation-entry.json')},'node':'/synthetic/node',
                   'python':'/synthetic/python','research':'/synthetic/research'}
        lane=matrix.make_lane(control,admission,target,'chromium',1,'/synthetic/node',Path('/synthetic/modules'),Path('/synthetic/modules/pngjs'),M.MATRIX_PINS)
        file=Path(lane['result']['path']);file.parent.mkdir(parents=True);file.write_text(json.dumps({'status':'DIAGNOSTIC'}))
        driver=Path(lane['result']['driverPath']);driver.parent.mkdir();driver.write_text('{}')
        iso=self.task/'isolation.json';iso.write_text('{}')
        def run(argv,cwd,env,stdout,stderr,timeout):
            self.assertEqual(Path(argv[1]).name,'r003f_matrix_intake.cjs');self.assertEqual(timeout,180)
            self.assertEqual(json.loads(Path(argv[-1]).read_text())['selection'],lane['result']['selection'])
            body={'protocol':'R003F/matrix-intake/1','status':'ADMITTED_MATRIX_DIAGNOSTIC','nativeAcceptance':'NOT_EVALUATED',
                  'humanAcceptance':'OUTSTANDING','summary':matrix.record(file),'driver':matrix.record(driver),
                  'noVariantUnion':True,'originalStatus':'DIAGNOSTIC','sourceAdmission':{**admission,'matrix':control},'isolation':matrix.record(iso)}
            if broken:body.pop('sourceAdmission')
            Path(stdout).write_text(json.dumps(body));Path(stderr).write_text('')
            return {'returncode':0,'timedOut':False}
        with patch.dict(os.environ,{'SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT':str(iso)}),patch.object(M,'run_bounded',side_effect=run):
            broken=False;r=M.classify_lane(lane,0);self.assertEqual(r['status'],'ADMITTED_MATRIX_DIAGNOSTIC')
            self.assertEqual(M.namespace_status(lane,{'returncode':0,'timedOut':False},{**r,'id':lane['id']})['status'],'ADMITTED_MATRIX_DIAGNOSTIC')
            shutil.rmtree(file.parent.with_name(file.parent.name+'-intake'))
            broken=True;r=M.classify_lane(lane,0);self.assertEqual(r['status'],'INCOMPLETE')

    def test_matrix_original_failure_and_timeout_precedence(self):
        lane=self.blocked_plan()['lanes'][0]
        for code,status,stop in [(3,'ISOLATION_FAIL',True),(4,'ANDON',False),(86,'ISOLATION_FAIL',True),(2,'INCOMPLETE',False)]:
            r=M.classify_lane(lane,code,True);self.assertEqual((r['status'],r['stopAll']),(status,stop))
    def test_matrix_outer_namespace_failure_dominates_admitted_diagnostic(self):
        lane=self.blocked_plan()['lanes'][0]
        inner={'id':lane['id'],'status':'ADMITTED_MATRIX_DIAGNOSTIC','stopAll':False,'returncode':0,'timedOut':False,'nativeQualification':'NOT_EVALUATED','humanAcceptance':'OUTSTANDING'}
        r=M.namespace_status(lane,{'returncode':86,'timedOut':False},inner);self.assertEqual(r['status'],'ISOLATION_FAIL')
        r=M.namespace_status(lane,{'returncode':1,'timedOut':False},inner);self.assertEqual(r['status'],'ISOLATION_UNCONFIRMED')
    def test_matrix_status_cannot_be_generic_pass(self):
        lane=self.blocked_plan()['lanes'][0]
        inner={'id':lane['id'],'status':'PASS','stopAll':False,'returncode':0,'timedOut':False}
        self.assertEqual(M.namespace_status(lane,{'returncode':0,'timedOut':False},inner)['status'],'ISOLATION_UNCONFIRMED')
    def test_matrix_namespace_forwarding_retains_selector(self):
        runtime={'node':'/node','python':'/python','modules':'/modules'};self.args.baseline=Path('/baseline');self.args.research=Path('/research');self.args.historical=Path('/history')
        argv=M.isolated_command(self.args,runtime,'prepare');self.assertEqual(json.loads(argv[argv.index('--r003f-matrix')+1]),self.selector)
    def test_matrix_inside_preserves_actual_optional_failure_and_forwards_it_to_planner(self):
        import r003f_matrix_campaign as matrix
        capture=self.task/'capture';capture.mkdir();self.args.phase='prepare';self.args.lane=None
        self.args.research=Path('/synthetic/research');self.args.baseline=Path('/synthetic/baseline');self.args.historical=Path('/synthetic/history')
        runtime={'node':'/synthetic/node','python':'/synthetic/python','modules':'/synthetic/modules','pngjs':'/synthetic/modules/pngjs'}
        receipt=capture/'isolation.json';receipt.write_text('{}');calls=[]
        def run(argv,cwd,env,stdout,stderr,timeout):
            calls.append(argv);Path(stdout).parent.mkdir(parents=True,exist_ok=True);Path(stdout).write_text('');Path(stderr).write_text('')
            if Path(argv[1]).name=='prepare.py':
                destination=self.task/'work/prepared/receipts';destination.mkdir(parents=True);(destination/'prepared.json').write_text('{}')
            elif Path(argv[1]).name=='r003f_matrix_campaign.py':
                Path(stderr).write_text('controlled original materialization failure');return {'returncode':2,'timedOut':False}
            elif Path(argv[1]).name=='lanes.py':
                self.assertEqual(json.loads(argv[argv.index('--r003f-matrix')+1]),self.selector)
                outer=json.loads(Path(argv[argv.index('--r003f-matrix-entry')+1]).read_text());self.assertEqual(outer['returncode'],2)
            else:self.fail('unexpected command '+str(argv))
            return {'returncode':0,'timedOut':False}
        with patch.object(M,'controls',return_value=str(receipt)),patch.object(M,'run_bounded',side_effect=run),patch.dict(os.environ,{},clear=False):
            self.assertEqual(M.inside(self.args,runtime),0)
        self.assertEqual([Path(x[1]).name for x in calls],['prepare.py','r003f_matrix_campaign.py','lanes.py'])
        context=json.loads((capture/'preparation-context.json').read_text());self.assertEqual(context['argv'],calls[0]);self.assertEqual(context['isolation'],matrix.record(receipt))
        outer=json.loads((capture/'r003f-matrix-preparation-entry.json').read_text());self.assertEqual(outer['argv'],calls[1]);self.assertEqual(outer['timeoutSeconds'],180)
        self.assertIn('controlled original', (capture/'r003f-matrix-preparation.stderr').read_text())

    def test_matrix_campaign_rejects_ignored_selector_and_empty_population(self):
        p=self.task/'campaign.json';base={'schemaVersion':1,'engine':'chromium','r003fDpr':1,'r002f':{'enabled':False,'dpr':1,'rounds':1,'section':'all'},'workOrders':['R003F'],'r003fHarness':'corrected-matrix','r003fMatrix':self.selector}
        p.write_text(json.dumps(base));self.assertEqual(M.read_campaign(p),base)
        for change in ({'r003fHarness':'published'},{'workOrders':[]},{'r003fMatrix':{}},{'r003fMatrix':{'id':self.selector['id'],'variant':['B0','B0']}}):
            p.write_text(json.dumps({**base,**change}))
            with self.assertRaises(ValueError):M.read_campaign(p)

class CostIntegration(unittest.TestCase):
    def setUp(self):
        StageIntegration.setUp(self)
        self.args.r0035_costs=True;self.folder=self.task/'capture/r0035-cost-preparation'
    tearDown=StageIntegration.tearDown
    test_cost_executable_and_copied_runtime_rebinding_precede_source_readmission=StageIntegration.test_stage_executable_and_copied_runtime_rebinding_precede_source_readmission
    test_cost_full_current_admission_rejects_changed_source_and_receipt_authority=StageIntegration.test_stage_full_current_admission_rejects_changed_source_and_receipt_authority
    def prepared_plan(self):
        self.assertTrue(hasattr(M,'cost_campaign'),'explicit central cost selection has not been implemented')
        result=M.prepare_stages(self.args,self.runtime,self.task/'work/prepared')
        self.assertEqual(result['returncode'],0)
        admission=self.planner.admit_r0035_stages(self.prepared,self.prepared_path,self.folder/'process.json','off','all',costs=True)
        self.assertEqual(admission['status'],'PASS',admission)
        (self.task/'capture/lanes').mkdir()
        plan=self.planner.make_plan(self.prepared,self.task/'capture/lanes',python_playwright=Path(sys.executable),
            node=Path('/bounded/node'),node_modules=Path('/bounded/modules'),pngjs=Path('/bounded/pngjs'),
            work_orders=['R0035'],r0035_guard='off',r0035_mode='timing',r0035_stages=True,r0035_costs=True,
            r0035_stage_preparation=admission)
        plan['preparedReceipt']={'path':str(self.prepared_path),'sha256':M.digest(self.prepared_path)}
        return plan,plan['lanes'][0]

    def test_cost_actual_optional_preparation_and_full_current_plan_bindings(self):
        plan,lane=self.prepared_plan();self.assertEqual(M.admit_plan(plan,self.args, self.runtime),[lane])
        self.assertEqual(lane['preparation']['collectorSha256'],M.cost_material.HELPER_SHA256)
        self.assertEqual(lane['id'],'r0035-chromium-timing-costs')
        self.assertIn('--r0035-costs',M.isolated_command(self.args,self.runtime,'prepare'))
        for mutate in (lambda p:p['lanes'][0]['argv'].__setitem__(-1,'full'),
                       lambda p:p['lanes'][0]['stageObservation'].update(protocol='r0035-stage-diagnostic/1'),
                       lambda p:p['lanes'][0].update(postObservationCheckSeconds=0),
                       lambda p:p['lanes'][0]['preparation'].update(collectorSha256='0'*64)):
            altered=copy.deepcopy(plan);mutate(altered)
            with self.assertRaises(ValueError):M.admit_plan(altered,self.args, self.runtime)
        path=self.folder/'process.json';raw=path.read_bytes()
        for change in ({'returncode':False},{'timedOut':None},{'retentionError':False},
                       {'retentionError':''},{'timeoutSeconds':239},{'cwd':'/changed/cwd'},
                       {'argv':['unbound']},{'collectorSha256':'0'*64}):
            body=json.loads(raw);body.update(change);M.write_json(path,body)
            with self.subTest(change=change):
                self.assertEqual(self.planner.admit_r0035_stages(self.prepared,self.prepared_path,path,'off','all',costs=True)['status'],'INCOMPLETE')
        path.write_bytes(raw)

    def test_cost_campaign_rejects_other_engines_scopes_and_unreviewed_combinations(self):
        value={'schemaVersion':1,'engine':'chromium','r003fDpr':1,'workOrders':['R0035'],
               'r002f':{'enabled':False,'dpr':1,'rounds':1,'section':'all'},
               'r0035':{'guard':'off','scope':'all','mode':'timing'},'r0035Stages':True,'r0035Costs':True}
        path=self.root/'campaign.json';M.write_json(path,value);self.assertEqual(M.read_campaign(path),value)
        for change in ({'r0035Costs':'yes'},{'r0035Stages':False},{'engine':'firefox'},
                       {'r0035':{'guard':'default','scope':'all','mode':'timing'}},
                       {'workOrders':['R0035','R003F']},{'r0035':{'guard':'off','scope':'preview-members','mode':'timing'}}):
            M.write_json(path,{**value,**change})
            with self.subTest(change=change),self.assertRaises(ValueError):M.read_campaign(path)

    def test_cost_actual_preparation_failure_blocks_without_fallback_and_keeps_streams(self):
        self.assertTrue(hasattr(M,'cost_campaign'),'explicit central cost selection has not been implemented')
        def fail(argv,cwd,env,stdout,stderr,timeout):
            M.write_json(Path(stdout),{'synthetic':'partial source prefix'});Path(stderr).write_text('controlled source refusal')
            return {'returncode':7,'timedOut':False}
        with patch.object(M,'run_bounded',side_effect=fail):result=M.prepare_stages(self.args,self.runtime,self.task/'work/prepared')
        self.assertEqual(result['returncode'],7);self.assertIn('refusal',(self.folder/'stderr').read_text())
        admission=self.planner.admit_r0035_stages(self.prepared,self.prepared_path,self.folder/'process.json','off','all',costs=True)
        self.assertEqual(admission['status'],'INCOMPLETE')
        plan=self.planner.make_plan(self.prepared,self.task/'capture/lanes',python_playwright=Path(sys.executable),
            node=Path('/bounded/node'),node_modules=Path('/bounded/modules'),pngjs=Path('/bounded/pngjs'),
            work_orders=['R0035'],r0035_guard='off',r0035_mode='timing',r0035_stages=True,r0035_costs=True,
            r0035_stage_preparation=admission)
        self.assertEqual(plan['lanes'][0]['argv'],[])

    def run_cost_original(self,failed=False):
        import observe_r0035_costs as cost_observer
        import r0035_cost_controls as cost_controls
        entry=cost_observer.entry_support()
        self.fixtures=SimpleNamespace(fixtures=self.fixtures.fixtures,stage_trace=lambda:cost_controls.cost_trace(cost_observer))
        with patch.dict(sys.modules,{'observe_r0035_stages':entry}):
            return StageIntegration.run_original_with_stages(self,failed)

    def test_cost_admitted_totals_cannot_erase_original_failed_qualification(self):
        plan,lane=self.run_cost_original(failed=True)
        with patch.object(M,'_r0035_cost_current_check',side_effect=self.synthetic_current) as current:
            verdict=M.classify_lane(lane,0)
        self.assertEqual(verdict['status'],'FAIL');self.assertEqual(verdict['originalStatus'],'FAIL')
        self.assertEqual(verdict['stageObservation']['status'],'OBSERVED',verdict);current.assert_called_once()
        self.assertEqual(verdict['timingClass'],'instrumented-preparation-costs')
        self.assertEqual(json.loads(Path(lane['result']['path']).read_text())[1]['qualification']['verdict'],'failed')

    @staticmethod
    def synthetic_current(lane,final):
        identity=json.loads(Path(lane['preparation']['identity']).read_bytes())
        return {'returncode':0,'timedOut':False,'stderr':'','stdout':json.dumps({
            'status':'CURRENT','isolation':final['isolation'],'preparation':lane['preparation']['custody'],
            'originalFiles':len(identity['baseFiles']),'derivedFiles':len(identity['files'])})}

    def test_cost_complete_intake_stays_distinct_and_requires_final_source_receipt(self):
        plan,lane=self.run_cost_original()
        with patch.object(M,'_r0035_cost_current_check',side_effect=self.synthetic_current):verdict=M.classify_lane(lane,0)
        self.assertEqual(verdict['status'],M.COSTS_OBSERVED,verdict)
        inner={**verdict,'id':lane['id']}
        self.assertEqual(M.namespace_status(lane,{'returncode':0,'timedOut':False},inner)['status'],M.COSTS_OBSERVED)
        self.assertEqual(M.namespace_status(lane,{'returncode':0,'timedOut':False},{**inner,'status':M.STAGES_OBSERVED})['status'],'ISOLATION_UNCONFIRMED')
        for foreign in ('ADMITTED_MATRIX_DIAGNOSTIC','VERIFIED_MATRIX_CAPTURE'):
            result=M.namespace_status(lane,{'returncode':0,'timedOut':False},{**inner,'status':foreign})
            self.assertEqual(result['status'],'ISOLATION_UNCONFIRMED');self.assertTrue(result['stopAll'])
        with patch.object(M,'_r0035_cost_current_check',return_value={'returncode':0,'timedOut':False,'stdout':'{}','stderr':''}):
            self.assertEqual(M.classify_lane(lane,0)['status'],'INCOMPLETE')
        path=Path(lane['result']['stageDriverPath']);raw=path.read_bytes()
        for change in ({'collectorSha256':'0'*64},{'baseWrapperSha256':'0'*64},{'observations':[]},{'trials':2}):
            body=json.loads(raw);body.update(change);M.write_json(path,body)
            with patch.object(M,'_r0035_cost_current_check',side_effect=self.synthetic_current) as current:
                self.assertEqual(M.classify_lane(lane,0)['status'],'INCOMPLETE');current.assert_not_called()
        path.write_bytes(raw)

    def test_cost_final_currentness_child_rejects_actual_missing_namespace(self):
        plan,lane=self.prepared_plan()
        path=self.task/'capture/isolation'/lane['id']/'receipt.json'
        result=M._r0035_cost_current_check(lane,{'isolation':{'file':str(path),'sha256':'not-observed'}})
        self.assertNotEqual(result['returncode'],0);self.assertFalse(result['timedOut'])
        self.assertIn('No such file',result['stderr']);self.assertFalse(path.exists())

    def test_cost_currentness_failure_and_outer_failure_keep_their_original_precedence(self):
        plan,lane=self.run_cost_original()
        with patch.object(M,'_r0035_cost_current_check',return_value={'returncode':1,'timedOut':False,'stdout':'','stderr':'source changed'}):
            verdict=M.classify_lane(lane,0)
        self.assertEqual(verdict['status'],'INCOMPLETE');self.assertEqual(verdict['originalStatus'],'PASS')
        veto=M.classify_lane(lane,86);self.assertEqual(veto['status'],M.VETO_STATUS);veto['id']=lane['id']
        self.assertEqual(M.namespace_status(lane,{'returncode':0,'timedOut':False},veto)['status'],M.VETO_STATUS)
        self.assertEqual(M.namespace_status(lane,{'returncode':86,'timedOut':False},veto)['status'],'ISOLATION_FAIL')
        self.assertEqual(M.namespace_status(lane,{'returncode':1,'timedOut':False},veto)['status'],'ISOLATION_UNCONFIRMED')

    def test_cost_success_requires_literal_normal_inner_and_outer_process_completion(self):
        plan,lane=self.run_cost_original()
        with patch.object(M,'_r0035_cost_current_check',side_effect=self.synthetic_current):
            good=M.classify_lane(lane,0);good['id']=lane['id']
            for code,timeout in ((False,False),(0,None)):
                with self.subTest(code=code,timeout=timeout):
                    self.assertEqual(M.r0035_stage_status(lane,code,timeout)['status'],'INCOMPLETE')
        for process in ({'returncode':False,'timedOut':False},{'returncode':0,'timedOut':None}):
            self.assertEqual(M.namespace_status(lane,process,good)['status'],'ISOLATION_UNCONFIRMED')
        inner={**good,'returncode':False}
        self.assertEqual(M.namespace_status(lane,{'returncode':0,'timedOut':False},inner)['status'],'ISOLATION_UNCONFIRMED')

    def test_cost_inside_planner_and_outer_namespace_budget_use_the_distinct_source(self):
        self.args.phase='prepare';self.args.lane=None;calls=[];real_run=M.run_bounded
        def run(argv,cwd,env,stdout,stderr,timeout):
            calls.append(argv)
            if Path(argv[1]).name=='r0035_cost_materialize.py':return real_run(argv,cwd,env,stdout,stderr,timeout)
            return {'returncode':0,'timedOut':False}
        with patch.object(M,'controls',return_value='synthetic-isolation-receipt'),patch.object(M,'run_bounded',side_effect=run),\
             patch.dict(os.environ,{},clear=False):self.assertEqual(M.inside(self.args,self.runtime),0)
        self.assertEqual([Path(c[1]).name for c in calls],['prepare.py','r0035_cost_materialize.py','lanes.py'])
        self.assertIn('--r0035-costs',calls[-1]);self.assertIn('--r0035-stages',calls[-1])
        self.assertEqual(calls[-1][calls[-1].index('--r0035-stage-process')+1],str(self.folder/'process.json'))
        admission=self.planner.admit_r0035_stages(self.prepared,self.prepared_path,self.folder/'process.json','off','all',costs=True)
        plan=self.planner.make_plan(self.prepared,self.task/'capture/lanes',python_playwright=Path(sys.executable),
            node=Path('/bounded/node'),node_modules=Path('/bounded/modules'),pngjs=Path('/bounded/pngjs'),work_orders=['R0035'],
            r0035_guard='off',r0035_mode='timing',r0035_stages=True,r0035_costs=True,r0035_stage_preparation=admission)
        plan['preparedReceipt']={'path':str(self.prepared_path),'sha256':M.digest(self.prepared_path)}
        M.write_json(self.task/'capture/lanes.json',plan);lane=plan['lanes'][0]
        M.write_json(self.task/'capture/lane-status'/(lane['id']+'.json'),
                     {'id':lane['id'],'status':'FAIL','stopAll':False,'returncode':0,'timedOut':False})
        with patch.object(M,'isolated_command',return_value=['synthetic-isolated']),\
             patch.object(M,'run_bounded',return_value={'returncode':0,'timedOut':False}) as outer:
            self.assertEqual(M.outside(self.args,self.runtime),2)
        self.assertEqual([call.args[-1] for call in outer.call_args_list],[1260,645])


class CombinedRouteControls(unittest.TestCase):
    def test_outer_process_types_are_strict_for_every_lane_and_preserve_failure_priority(self):
        cases=[]
        for kind in ('r0040-options','r003f-b0','r002f-probe','r0035-trials'):
            cases.append(({'result':{'kind':kind}},{'status':'PASS'}))
        cases.append(({'result':{'kind':'r0040-capture'}},{'status':M.CAPTURE_ADMITTED,'nativeQualification':'NOT_VERIFIED'}))
        cases.append(({'result':{'kind':'r0040-capture-dateonly'}},{'status':M.R0040_DATEONLY_ADMITTED,
            'nativeQualification':'NOT_VERIFIED','humanAcceptance':'OUTSTANDING','timingClass':'instrumented-date-only-clock','diagnostic':M.r0040_dateonly_identity()}))
        cases.append(({'result':{'kind':'r002f-tabhide'}},{'status':M.TABHIDE_OBSERVED,'nativeQualification':'LIFECYCLE_OBSERVATION_ONLY'}))
        for variant,status,qualification in [('B0','ADMITTED_MATRIX_DIAGNOSTIC','NOT_EVALUATED'),('all','VERIFIED_MATRIX_CAPTURE','ORIGINAL_COMPLETE_EIGHT_REPLAY_ONLY')]:
            cases.append(({'result':{'kind':'r003f-matrix','selection':{'variant':variant}}},
                {'status':status,'humanAcceptance':'OUTSTANDING','nativeQualification':qualification}))
        for cost in (False,True):
            cases.append(({'result':{'kind':'r0035-trials'},'stageObservation':{'protocol':'r0035-cost-diagnostic/1' if cost else 'r0035-stage-diagnostic/1'}},
                {'status':M.COSTS_OBSERVED if cost else M.STAGES_OBSERVED,'originalStatus':'PASS','stageObservation':{'status':'OBSERVED'},
                 'timingClass':M.cost_material.TIMING if cost else 'instrumented-stage-observation','nativeQualification':'UNCHANGED_ORIGINAL_REPORT_ONLY'}))
        malformed=[None,[],{}, {'returncode':0}, {'timedOut':False}]
        malformed += [{'returncode':value,'timedOut':False} for value in (False,True,0.0,1.0,None,'0')]
        malformed += [{'returncode':0,'timedOut':value} for value in (0,1,None,'false')]
        for lane,fields in cases:
            lane['id']='controlled-lane';inner={'id':lane['id'],'stopAll':False,'returncode':0,'timedOut':False,**fields}
            self.assertEqual(M.namespace_status(lane,{'returncode':0,'timedOut':False},inner)['status'],fields['status'])
            for process in malformed:
                with self.subTest(kind=lane['result'],process=process):
                    result=M.namespace_status(lane,process,inner)
                    self.assertEqual(result['status'],'ISOLATION_UNCONFIRMED');self.assertTrue(result['stopAll'])
            for process in ({'returncode':1,'timedOut':False},{'returncode':0,'timedOut':True}):
                self.assertEqual(M.namespace_status(lane,process,inner)['status'],'ISOLATION_UNCONFIRMED')
            self.assertEqual(M.namespace_status(lane,{'returncode':86,'timedOut':True},inner)['status'],'ISOLATION_FAIL')
            failure={**inner,'status':'ISOLATION_FAIL','stopAll':True}
            self.assertEqual(M.namespace_status(lane,{},failure)['status'],'ISOLATION_FAIL')
            original={**inner,'status':'FAIL'}
            retained=M.namespace_status(lane,{'returncode':1,'timedOut':False},original)
            self.assertEqual(retained['status'],'ISOLATION_UNCONFIRMED');self.assertEqual(retained['innerStatus']['status'],'FAIL')

    def test_matrix_success_labels_cannot_cross_into_any_other_lane_kind(self):
        for kind in ('r0035-trials','r002f-tabhide','r002f-probe','r0040-options','r0040-capture','r0040-capture-dateonly','r003f-b0'):
            lane={'id':'controlled-lane','result':{'kind':kind}}
            for status in ('ADMITTED_MATRIX_DIAGNOSTIC','VERIFIED_MATRIX_CAPTURE'):
                inner={'id':lane['id'],'status':status,'stopAll':False,'returncode':0,'timedOut':False,
                       'humanAcceptance':'OUTSTANDING','nativeQualification':'NOT_EVALUATED'}
                result=M.namespace_status(lane,{'returncode':0,'timedOut':False},inner)
                with self.subTest(kind=kind,status=status):
                    self.assertEqual(result['status'],'ISOLATION_UNCONFIRMED');self.assertTrue(result['stopAll'])

    def test_selected_routes_retain_each_frozen_operational_envelope(self):
        selector={'id':'owner_11150942_owner_wax_-81.9_150_clear_shipped_reduce_default','variant':'B0'}
        routes=[({},(2640,45)),({'r002fRoute':'tabhide','workOrders':['R002F']},(3900,66)),
                ({'r003fHarness':'corrected-matrix','r003fMatrix':selector,'workOrders':['R003F']},(3540,60)),
                ({'r0035Costs':True,'r0035Stages':True,'workOrders':['R0035'],
                  'r0035':{'guard':'off','scope':'all','mode':'timing'}},(2640,45))]
        for campaign,(seconds,minutes) in routes:
            with self.subTest(campaign=campaign):self.assertEqual(M.campaign_budget(campaign),
                {'coordinatorSeconds':seconds,'workflowObservationMinutes':minutes})
    def test_workflow_budget_has_one_unique_step_id_before_observation(self):
        import re
        workflow=(M.HERE.parents[2]/'.github/workflows/research-native-pilot.yml').read_text()
        identifiers=re.findall(r'^        id: (\S+)$',workflow,re.M)
        self.assertEqual(len(identifiers),len(set(identifiers)))
        self.assertEqual(identifiers.count('budget'),1)
        self.assertLess(workflow.index('        id: budget'),workflow.index('      - name: Observe sequentially'))
        self.assertEqual(workflow.count('budget = campaign_budget(read_campaign('),1)

    def test_each_unsummed_new_route_pair_is_rejected_before_execution(self):
        flags=[{'r002fRoute':'tabhide'},{'r003fHarness':'corrected-matrix'},{'r0035Costs':True}]
        for i,a in enumerate(flags):
            for b in flags[i+1:]:
                for selected in (['R002F'],['R003F'],['R0035']):
                    with self.subTest(a=a,b=b,selected=selected),self.assertRaisesRegex(ValueError,'simultaneous'):
                        M.campaign_budget({**a,**b,'workOrders':selected})

if __name__ == '__main__': unittest.main()
