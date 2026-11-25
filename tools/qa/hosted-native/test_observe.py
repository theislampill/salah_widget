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


if __name__ == '__main__': unittest.main()
