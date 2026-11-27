"""Synthetic T1 composition controls for the new opt-in mechanism route.

Positive preparation/namespace prerequisites are explicit fixture doubles.
Only bounded source children run; native dispatch is forbidden by each case.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import observe as O
import capture_pipeline as P
import r0040_autoattach_central as C
import r0040_autoattach_central_controls as fixtures

HERE = Path(__file__).resolve().parent
RAW_OUT = b'actual source refusal\x00\xff\n'
RAW_ERR = b'actual source error\xfe\n'


class MechanismCurrentness(unittest.TestCase):
    def fixture(self):
        owner = fixtures.MechanismCentral('runTest'); owner.setUp()
        self.addCleanup(owner.doCleanups)
        return owner.fixture()

    def command(self, f):
        return [f.runtime['python'], '-B', str(HERE/'r0040_autoattach_central.py'), '--readmit']

    def process(self, f, code=2, timed=False):
        return {'argv': self.command(f), 'cwd': str(HERE), 'timeoutSeconds': 120,
            'returncode': code, 'timedOut': timed, 'stdout': RAW_OUT.decode('utf8', 'replace'),
            'stderr': RAW_ERR.decode('utf8', 'replace'), 'stdoutBytes': RAW_OUT, 'stderrBytes': RAW_ERR}

    def execute(self, f, process, mutate=None, exception=None, write_failure=False):
        plan = copy.deepcopy(f.plan)
        if mutate: mutate(plan)
        O.write_json(f.task/'runtime.json', f.runtime)
        O.write_json(f.capture/'acquisition-identity.json', {'protocol': 'salah-hosted-native-acquisition/1', 'runtime': f.runtime})
        O.write_json(f.capture/'lanes.json', plan)
        original_plan = (f.capture/'lanes.json').read_bytes()
        args = ['observe.py', '--task', str(f.task), '--engine', 'chromium', '--work-orders', 'R0040', '--r0040-mode', C.MODE]
        for key in ('research', 'baseline', 'historical'): args += ['--'+key, str(getattr(f.args, key))]
        calls = []
        def only_preparation(*args):
            calls.append(args)
            if len(calls) > 1: raise AssertionError('currentness refusal dispatched native work')
            return {'returncode': 0, 'timedOut': False, 'elapsedSeconds': 0.01}
        write = O.write_json
        def retained_write(path, body):
            if write_failure and 'currentness' in Path(path).parts: raise OSError('synthetic retention failure')
            return write(path, body)
        with patch.object(sys, 'argv', args), patch.object(O, 'isolated_command', return_value=['synthetic-preparation']), \
             patch.object(O, 'run_bounded', side_effect=only_preparation), \
             patch.object(C, 'readmit', return_value=process, side_effect=exception) as child, \
             patch.object(O, 'write_json', side_effect=retained_write):
            code = O.main(); count = child.call_count
        self.assertEqual((f.capture/'lanes.json').read_bytes(), original_plan)
        body = json.loads((f.capture/'observation.json').read_bytes())
        campaign = {'engine': 'chromium', 'workOrders': ['R0040'], 'r0040Mode': C.MODE, 'r002f': {'enabled': False}}
        load = P.load
        def current(path): return campaign if Path(path) == P.HERE/'campaign.json' else load(path)
        with patch.object(P, 'completed', side_effect=lambda task, roots, phase: 0 if phase == 'acquisition' else code), \
             patch.object(P, 'load', side_effect=current):
            try: gate = P.admit_producers(f.task, {})
            except P.Rejected as error: gate = 'REJECTED:'+str(error)
        return code, body, gate, count

    def known_refusal(self, f, process):
        code, body, gate, calls = self.execute(f, process)
        self.assertEqual((code, calls), (2, 1))
        self.assertEqual(body['status'], 'OBSERVED_WITH_INCOMPLETE_OR_FAILED_LANES')
        self.assertEqual([(r['id'], r['status']) for r in body['lanes']], [(f.lane['id'], 'NOT_RUN')])
        self.assertNotIn('namespaceProcess', body['lanes'][0])
        self.assertEqual(gate, 'COMPLETED_OBSERVATION')
        self.assertFalse((f.capture/'coordinator-error-outer.json').exists())
        files = list((f.capture/'currentness').glob('*/process.json')); self.assertEqual(len(files), 1)
        value = json.loads(files[0].read_bytes())
        self.assertTrue(value['knownReturnedRefusal'])
        self.assertEqual(value['process']['argv'], self.command(f))
        self.assertEqual(value['process']['returncode'], process['returncode'])
        self.assertEqual(value['process']['timedOut'], process['timedOut'])
        for key, wanted in [('stdout', RAW_OUT), ('stderr', RAW_ERR)]:
            row = value['streams'][key]
            self.assertEqual(Path(row['path']).read_bytes(), wanted)
            self.assertEqual(row['bytes'], len(wanted))
            self.assertEqual(row['sha256'], hashlib.sha256(wanted).hexdigest())

    def test_new_readmission_requests_actual_raw_streams_and_keeps_120_seconds(self):
        f = self.fixture()
        actual = C.passive.bounded_check([sys.executable, '-c',
            "import os;os.write(1,b'\\xff\\x00');os.write(2,b'\\xfe');raise SystemExit(2)"], {}, 5, raw=True)
        self.assertEqual((actual['returncode'], actual['timedOut']), (2, False))
        self.assertEqual(actual['stdoutBytes'], b'\xff\x00'); self.assertEqual(actual['stderrBytes'], b'\xfe')
        with patch.object(C.passive, 'bounded_check', return_value=actual) as process:
            result = C.readmit(f.task/'work/prepared/receipts/prepared.json', f.runtime, f.task)
        self.assertIs(process.call_args.kwargs.get('raw'), True)
        self.assertEqual(process.call_args.args[0], self.command(f)); self.assertEqual(process.call_args.args[2], 120)
        self.assertEqual(result['stdoutBytes'], b'\xff\x00')
        refused = C.readmit(f.task/'absent-preparation.json', f.runtime, f.task)
        self.assertEqual(refused['returncode'], 2)
        self.assertIsInstance(refused['stdoutBytes'], bytes); self.assertIsInstance(refused['stderrBytes'], bytes)

    def test_completed_mechanism_refusal_retains_raw_bytes_without_dispatch(self):
        f = self.fixture(); self.known_refusal(f, self.process(f))

    def test_drained_mechanism_timeout_retains_raw_bytes_without_dispatch(self):
        f = self.fixture(); self.known_refusal(f, self.process(f, code=-9, timed=True))

    def test_unknown_or_foreign_process_cannot_gain_refusal_authority(self):
        for change in ({'returncode': None}, {'returncode': False}, {'returncode': -9}, {'timedOut': 'true'},
                       {'stdoutBytes': None}, {'argv': ['foreign']}, {'cwd': '/foreign'}, {'timeoutSeconds': 121},
                       {'error': 'unknown'}, {'interrupted': True}):
            with self.subTest(change=change):
                f = self.fixture(); code, body, gate, _ = self.execute(f, {**self.process(f), **change})
                self.assertEqual(code, 2); self.assertEqual(body['lanes'], [])
                self.assertEqual(gate, 'REJECTED:PRODUCER_INCOMPLETE')

    def test_complete_canonical_one_lane_is_required_before_readmission(self):
        for mutate in (lambda p: p['lanes'].clear(), lambda p: p['lanes'].append(copy.deepcopy(p['lanes'][0])),
                       lambda p: p['lanes'][0].update(stopAllOnExit=[]),
                       lambda p: p['lanes'][0]['exitStatuses'].update({'0': 'PASS'}),
                       lambda p: p['lanes'][0]['result'].update(mechanismAdmissionPath='/foreign/receipt')):
            with self.subTest(mutate=mutate):
                f = self.fixture(); code, body, gate, calls = self.execute(f, self.process(f), mutate=mutate)
                self.assertEqual((code, calls), (2, 0)); self.assertEqual(body['lanes'], [])
                self.assertEqual(gate, 'REJECTED:PRODUCER_INCOMPLETE')

    def test_zero_exit_malformed_output_is_not_recoverable_refusal(self):
        f = self.fixture(); code, body, gate, _ = self.execute(f, self.process(f, code=0))
        self.assertEqual(code, 2); self.assertEqual(body['lanes'], [])
        self.assertEqual(gate, 'REJECTED:PRODUCER_INCOMPLETE')

    def test_interruption_or_retention_failure_never_becomes_not_run(self):
        for exception, write_failure in ((InterruptedError('synthetic interruption'), False), (None, True)):
            f = self.fixture(); code, body, gate, _ = self.execute(f, self.process(f), exception=exception, write_failure=write_failure)
            self.assertEqual(code, 2); self.assertEqual(body['lanes'], [])
            self.assertEqual(gate, 'REJECTED:PRODUCER_INCOMPLETE')


if __name__ == '__main__': unittest.main()
