"""Evidence controls only. Synthetic timings never constitute native cost proof."""
from copy import deepcopy
import importlib.util
import hashlib
from pathlib import Path
import unittest


MODULE = Path(__file__).with_name('r0022-paint-cost.py')
spec = importlib.util.spec_from_file_location('paint_cost', MODULE)
cost = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cost)


def fixture():
    state = {'pendingJobs': 0, 'rafChains': 1, 'timerChains': 0, 'intervalChains': 0, 'listeners': 3, 'providers': 1,
             'networkRequests': 0, 'renderRequests': 0, 'readbacks': 0, 'textureAllocations': 0,
             'retainedArrays': 4, 'retainedBytes': 100}
    slots = []
    for block in range(4):
        for order, side in enumerate('ABBA'):
            slots.append({'block': block, 'order': order, 'side': side,
                          'elapsedMs': 5000, 'durationsMs': [1, 1, 2, 2],
                          'exceptions': [], 'startState': deepcopy(state),
                          'endState': deepcopy(state)})
    return {'schema': 'r0022-paint-cost/v1', 'measurementKind': 'actual-browser',
            'status': 'RAW_BATCHES_RETURNED', 'noiseDisposition': 'CONTROLLED',
            'startedAtUtc': '2026-10-13T08:00:01Z',
            'authority': {'budgetDecisionSha256': 'a' * 64,
                          'resourceAdmissionSha256': 'b' * 64,
                          'independentAdapterReviewSha256': 'c' * 64},
            'setup': {'engine': 'chromium', 'browserVersion': 'recorded',
                      'executableSha256': 'd' * 64, 'machine': 'recorded',
                      'powerSetting': 'recorded', 'profile': 'disposable',
                      'viewport': [390, 600], 'card': [325, 530], 'dpr': 1,
                      'sceneSha256': 'e' * 64, 'quiescenceSha256': 'f' * 64},
            'sources': {'originalNativeBefore': '1' * 64,
                        'candidateNativeAfter': '2' * 64,
                        'displayBefore': '3' * 64, 'displayAfter': '4' * 64},
            'changedScopes': ['admission'],
            'scopes': [{'name': name, 'warmMs': {'A': 5000, 'B': 5000},
                        'status': 'RAW_BATCHES_RETURNED',
                        'actualFunction': name, 'adapterSha256': '5' * 64,
                        'slots': deepcopy(slots)}
                       for name in ('atmosphere', 'paint', 'renderMoon', 'admission')]}


DECISION = {'schema': 'r0022-cost-budget-decision/v1', 'approved': True,
            'absoluteFloorMs': .25, 'relativeIncrease': .1,
            'adoptedAtUtc': '2026-10-13T08:00:00Z',
            'approvedBeforeMeasurement': True}


class CostEvidenceTests(unittest.TestCase):
    def check(self, raw):
        return cost.assess(raw, DECISION, decision_sha256='a' * 64)

    def test_completed_worker_requests_cannot_hide_inside_or_between_slots(self):
        raw = fixture()
        for slot in raw['scopes'][0]['slots']:
            if slot['side'] == 'B':
                slot['startState']['renderRequests'] = slot['endState']['renderRequests'] = 17
        self.assertEqual(self.check(raw)['status'], 'PASS_COST_ONLY', 'Inherited request totals may differ')
        changed = deepcopy(raw)
        changed['scopes'][0]['slots'][1]['endState']['renderRequests'] += 1
        self.assertEqual(self.check(changed)['status'], 'INCOMPLETE')
        changed = deepcopy(raw)
        for slot in changed['scopes'][0]['slots'][5:]:
            if slot['side'] == 'B':
                slot['startState']['renderRequests'] += 1
                slot['endState']['renderRequests'] += 1
        self.assertEqual(self.check(changed)['status'], 'INCOMPLETE')

    def test_unobserved_worker_request_counter_cannot_pass(self):
        raw = fixture()
        del raw['scopes'][0]['slots'][0]['startState']['renderRequests']
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_explicit_approved_timestamp_alias_retains_prior_adoption(self):
        decision = {k: v for k, v in DECISION.items() if k != 'adoptedAtUtc'}
        decision['approvedAtUtc'] = DECISION['adoptedAtUtc']
        self.assertEqual(cost.assess(fixture(), decision, decision_sha256='a' * 64)['status'],
                         'PASS_COST_ONLY')
        for value in ('2026-10-13T08:00:02Z', '2026-10-13T08:00:00', None, 'invalid'):
            with self.subTest(value=value):
                decision['approvedAtUtc'] = value
                self.assertEqual(cost.assess(fixture(), decision, decision_sha256='a' * 64)['status'],
                                 'INCOMPLETE')

    def test_conflicting_or_invalid_supplied_adoption_timestamp_fails(self):
        for value in ('2026-10-13T07:59:59Z', None, 'invalid'):
            decision = {**DECISION, 'approvedAtUtc': value}
            self.assertEqual(cost.assess(fixture(), decision, decision_sha256='a' * 64)['status'],
                             'INCOMPLETE')
        decision = {**DECISION, 'approvedAtUtc': '2026-10-13T10:00:00+02:00'}
        self.assertEqual(cost.assess(fixture(), decision, decision_sha256='a' * 64)['status'],
                         'PASS_COST_ONLY')

    def test_unobserved_timer_or_interval_cannot_pass(self):
        for field in ('timerChains', 'intervalChains'):
            raw = fixture()
            raw['scopes'][0]['slots'][0]['endState'][field] = 1
            self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')
            for slot in raw['scopes'][0]['slots']:
                slot['startState'][field] = slot['endState'][field] = 1
            self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_original_budget_boundary_is_inclusive(self):
        raw = fixture()
        for scope in raw['scopes']:
            for slot in scope['slots']:
                if slot['side'] == 'B':
                    slot['durationsMs'] = [1.25, 1.25, 2.25, 2.25]
        self.assertEqual(self.check(raw)['status'], 'PASS_COST_ONLY')

    def test_one_slow_call_cannot_hide_in_median(self):
        raw = fixture()
        for scope in raw['scopes']:
            for slot in scope['slots']:
                if slot['side'] == 'B':
                    slot['durationsMs'] = [1, 1, 2, 5]
        self.assertEqual(self.check(raw)['status'], 'FAIL_COST_BUDGET')

    def test_missing_admission_is_incomplete(self):
        raw = fixture()
        raw['scopes'].pop()
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_wrong_order_is_not_relabelled_as_abba(self):
        raw = fixture()
        raw['scopes'][0]['slots'][1]['side'] = 'A'
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_early_batch_cannot_pass(self):
        raw = fixture()
        raw['scopes'][0]['slots'][0]['elapsedMs'] = 4999
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_raw_sample_count_must_fit_elapsed_time(self):
        raw = fixture()
        raw['scopes'][0]['slots'][0]['durationsMs'] = [5001]
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_missing_counters_not_defaulted_to_zero(self):
        raw = fixture()
        del raw['scopes'][0]['slots'][0]['startState']['readbacks']
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_extra_texture_or_network_is_incomplete(self):
        for key in ('textureAllocations', 'networkRequests', 'readbacks', 'listeners'):
            with self.subTest(key=key):
                raw = fixture()
                raw['scopes'][0]['slots'][1]['endState'][key] += 1
                self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_inherited_readbacks_recorded_without_inventing_a_zero_gate(self):
        raw = fixture()
        for scope in raw['scopes']:
            totals = {'A': 0, 'B': 0}
            for slot in scope['slots']:
                side = slot['side']
                slot['startState']['readbacks'] = totals[side]
                totals[side] += len(slot['durationsMs'])
                slot['endState']['readbacks'] = totals[side]
        result = self.check(raw)
        self.assertEqual(result['status'], 'PASS_COST_ONLY')
        self.assertEqual(result['scopes'][0]['observedEventTotals']['A']['readbacks'], 32)

    def test_counter_reset_cannot_hide_a_new_readback(self):
        raw = fixture()
        raw['scopes'][0]['slots'][0]['startState']['readbacks'] = 10
        raw['scopes'][0]['slots'][0]['endState']['readbacks'] = 10
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_retained_memory_growth_is_incomplete(self):
        raw = fixture()
        raw['scopes'][0]['slots'][0]['endState']['retainedBytes'] += 1
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_unequal_before_after_state_is_incomplete(self):
        raw = fixture()
        for slot in raw['scopes'][0]['slots']:
            if slot['side'] == 'B':
                slot['startState']['providers'] = slot['endState']['providers'] = 2
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_finite_declared_l1_arrays_do_not_invent_an_equal_memory_gate(self):
        raw = fixture()
        for scope in raw['scopes']:
            for slot in scope['slots']:
                if slot['side'] == 'B':
                    for point in ('startState', 'endState'):
                        slot[point]['retainedArrays'] += 2
                        slot[point]['retainedBytes'] += 100
        result = self.check(raw)
        self.assertEqual(result['status'], 'PASS_COST_ONLY')
        self.assertEqual(result['scopes'][0]['retainedStateBySide']['B']['retainedBytes'], 200)

    def test_growth_between_same_side_slots_is_incomplete(self):
        raw = fixture()
        for point in ('startState', 'endState'):
            raw['scopes'][0]['slots'][4][point]['retainedBytes'] += 1
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_warmup_exception_and_nonfinite_preserved(self):
        for mutation in ('warm', 'exception', 'nan', 'empty'):
            with self.subTest(mutation=mutation):
                raw = fixture()
                slot = raw['scopes'][0]['slots'][0]
                if mutation == 'warm': raw['scopes'][0]['warmMs']['A'] = 0
                if mutation == 'exception': slot['exceptions'] = ['original error']
                if mutation == 'nan': slot['durationsMs'] = [float('nan')]
                if mutation == 'empty': slot['durationsMs'] = []
                self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_missing_or_retuned_budget_cannot_pass(self):
        for key, value in (('approved', False), ('approvedBeforeMeasurement', False),
                           ('absoluteFloorMs', .3), ('relativeIncrease', .2)):
            with self.subTest(key=key):
                decision = {**DECISION, key: value}
                self.assertEqual(cost.assess(fixture(), decision,
                                            decision_sha256='a' * 64)['status'], 'INCOMPLETE')

    def test_decision_hash_mismatch_cannot_pass(self):
        self.assertEqual(cost.assess(fixture(), DECISION,
                                    decision_sha256='9' * 64)['status'], 'INCOMPLETE')

    def test_late_and_naive_budget_timestamps_cannot_pass(self):
        for adopted in ('2026-10-13T08:00:02Z', '2026-10-13T08:00:00', None):
            with self.subTest(adopted=adopted):
                decision = {**DECISION, 'adoptedAtUtc': adopted}
                self.assertEqual(cost.assess(fixture(), decision,
                                            decision_sha256='a' * 64)['status'], 'INCOMPLETE')

    def test_synthetic_receipt_cannot_be_native_proof(self):
        raw = fixture()
        raw['measurementKind'] = 'synthetic'
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_complete_samples_do_not_erase_custody_failure_or_noise(self):
        for mutation in ('scope-error', 'outer-interruption', 'noise'):
            with self.subTest(mutation=mutation):
                raw = fixture()
                if mutation == 'scope-error': raw['scopes'][0]['error'] = 'final raw custody failed'
                if mutation == 'outer-interruption': raw['status'] = 'INCOMPLETE'
                if mutation == 'noise': raw['noiseDisposition'] = 'INCOMPLETE'
                self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_duplicate_scopes_and_extra_blocks_rejected(self):
        raw = fixture()
        raw['scopes'].append(deepcopy(raw['scopes'][0]))
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')
        raw = fixture()
        raw['scopes'][0]['slots'].append(deepcopy(raw['scopes'][0]['slots'][0]))
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')

    def test_malformed_types_are_incomplete_without_default_zeros(self):
        for key, value in (('authority', []), ('setup', []), ('sources', []),
                           ('changedScopes', [{}]), ('scopes', [{'name': {}}])):
            with self.subTest(key=key):
                self.assertEqual(self.check({**fixture(), key: value})['status'], 'INCOMPLETE')
        raw = fixture()
        raw['scopes'][0]['slots'][0]['side'] = {}
        self.assertEqual(self.check(raw)['status'], 'INCOMPLETE')


class ActualOwnerBridgeTests(unittest.TestCase):
    def setUp(self):
        self.owner = (Path(__file__).resolve().parents[1] / 'real-sky/native-host.mjs').read_bytes()
        self.digest = hashlib.sha256(self.owner).hexdigest()

    def test_actual_selected_owner_is_recoverable_exactly(self):
        prepared = cost.prepare_host_owner(self.owner, self.digest)
        self.assertEqual(prepared.count(b'__r0022CostProbe'), 4)
        self.assertIn(b'bind({accept,current:request=>lifecycle.current(request,snapshot()),readState})', prepared)
        self.assertIn(b'captureRaw(result,request)', prepared)

    def test_hash_drift_is_rejected_before_fixture_output(self):
        with self.assertRaisesRegex(ValueError, 'preimage mismatch'):
            cost.prepare_host_owner(self.owner + b'\n', self.digest)

    def test_duplicate_hook_is_rejected(self):
        prepared = cost.prepare_host_owner(self.owner, self.digest)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            cost.prepare_host_owner(prepared, hashlib.sha256(prepared).hexdigest())

    def test_changed_accept_signature_is_not_guessed(self):
        changed = self.owner.replace(cost.HOST_ACCEPT, b' function accept(other){', 1)
        with self.assertRaisesRegex(ValueError, 'unavailable or ambiguous'):
            cost.prepare_host_owner(changed, hashlib.sha256(changed).hexdigest())

    def test_crlf_source_literals_survive(self):
        source = self.owner.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        prepared = cost.prepare_host_owner(source, hashlib.sha256(source).hexdigest())
        self.assertEqual(prepared.replace(b'\r\n', b'').count(b'\n'), 0)


if __name__ == '__main__':
    unittest.main()
