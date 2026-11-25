"""Behavioral controls for isolated observation admission and failure retention."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
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
        self.assertTrue(not stat.exists() or stat.read_text().split()[2] == 'Z')


class OuterBoundary(unittest.TestCase):
    def check_outer(self, namespace_result, inner_status):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp)
            capture = task/'capture'; capture.mkdir()
            lanes = [{'id': name, 'workOrder': 'R0035', 'timeoutSeconds': 5,
                      'result': {'kind': 'r0035-trials', 'path': str(capture/(name+'.json'))}}
                     for name in ('first', 'second')]
            (capture/'lanes.json').write_text(json.dumps({'protocol': 'salah-hosted-native-lanes/1',
                                                         'sequential': True, 'lanes': lanes}))
            calls = []
            def run(argv, *_args):
                calls.append(argv)
                if len(calls) == 1:
                    return {'returncode': 0, 'timedOut': False}
                if inner_status is not None:
                    M.write_json(capture/'lane-status'/'first.json', inner_status)
                return namespace_result
            args = SimpleNamespace(task=task, engine='chromium')
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
                         for name, order in (('rain', 'R0040'), ('moon', 'R003F'), ('stars', 'R0035'))]
                if include_blocked:
                    lanes.insert(0, {'id': 'r002f-chromium-dpr1', 'workOrder': 'R002F', 'timeoutSeconds': 900,
                                     'preparation': {'status': 'INCOMPLETE', 'reason': 'controlled build failure'}})
                (capture/'lanes.json').write_text(json.dumps({'protocol': 'salah-hosted-native-lanes/1',
                                                             'sequential': True, 'lanes': lanes}))
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
                self.assertEqual([by_id[name]['status'] for name in ('rain', 'moon', 'stars')], ['PASS']*3)
                self.assertEqual(by_id['r002f-chromium-dpr1']['status'], 'NOT_RUN')
                self.assertEqual(by_id['r002f-chromium-dpr1']['preparationStatus'], 'INCOMPLETE')
                self.assertEqual(len(calls), 4, 'only preparation and the three admitted lanes execute')
                self.assertEqual(report['status'], 'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES')


class Campaign(unittest.TestCase):
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

    def test_optional_preparation_failure_preserves_plan_and_seals_only_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp); (task/'capture').mkdir()
            args = SimpleNamespace(task=task, research=Path('/sources/research'), baseline=Path('/sources/main'),
                                   historical=Path('/sources/history'), engine='firefox', phase='prepare', lane=None,
                                   r002f=True, r002f_dpr=2, r002f_rounds=2, r002f_section='prayer', r003f_dpr=2)
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
            self.assertEqual(planner[planner.index('--r002f-process')+1], str(task/'capture'/'r002f-preparation-process.json'))
            self.assertTrue((task/'capture'/'r002f-preparation'/'build-result.json').is_file())
            self.assertTrue((task/'capture'/'r002f-preparation'/'candidate-build-1.stderr').is_file())
            self.assertFalse(any(path.name == 'index.html' for path in (task/'capture').rglob('*')))

    def test_namespace_command_preserves_the_selected_campaign_controls(self):
        args = SimpleNamespace(task=Path('/task'), research=Path('/sources/research'), baseline=Path('/sources/main'),
                               historical=Path('/sources/history'), engine='webkit', r002f=True, r002f_dpr=3,
                               r002f_rounds=2, r002f_section='preview', r003f_dpr=2)
        runtime = {'node': '/dependencies/node', 'python': '/dependencies/python', 'modules': '/dependencies/modules'}
        argv = M.isolated_command(args, runtime, 'lane', 'r002f-webkit-dpr3')
        self.assertIn('--r002f', argv)
        for key, value in (('--engine', 'webkit'), ('--r003f-dpr', '2'), ('--r002f-dpr', '3'),
                           ('--r002f-rounds', '2'), ('--r002f-section', 'preview')):
            self.assertEqual(argv[argv.index(key)+1], value)


if __name__ == '__main__': unittest.main()
