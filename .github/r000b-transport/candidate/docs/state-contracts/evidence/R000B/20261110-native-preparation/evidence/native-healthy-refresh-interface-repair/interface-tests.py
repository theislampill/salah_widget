class HealthyRefreshInterfaceTests(unittest.TestCase):
    def receipt_probe(self, case, receipt_epoch):
        receipt = deepcopy(case['new'])
        receipt.update(retrievedAt=receipt_epoch, at=receipt_epoch + 1)
        captured = case['frame'](case['after']['elapsedMs'], receipt)
        record = ORACLE.healthy_refresh_record(captured)
        self.assertIsNotNone(record)
        return record, captured

    def test_actual_rich_targets_compact_receipts_and_monotonic_deadlines_qualify(self):
        case = healthy_refresh_case()
        record = ORACLE.healthy_refresh_record(case['after'])
        self.assertIsNotNone(record)
        self.assertEqual(len(record['target']), 10)
        self.assertEqual(set(record['publication']['target']), {'generation', 'lat', 'lon'})
        self.assertNotEqual(record['target'], record['publication']['target'])
        self.assertEqual(record['target'], case['after']['raw']['target'])
        self.assertTrue(ORACLE._healthy_refresh_sample(case['before'], [case['old'], case['new']], full=True))
        request = ORACLE._healthy_refresh_request(record, case['after'], case['ledger'], case['clock'])
        self.assertIsNotNone(request)
        self.assertEqual(request['clockOrigin']['started'], 125.25)
        self.assertEqual(request['timing']['jsonPerformanceMs'], 180130.25)
        self.assertEqual(request['timing']['retrievalPerformanceInterval'], [180135.25, 180136.25])
        self.assertEqual(request['timing']['deadlinePerformanceMs'], 190125.25)
        self.assertTrue(refresh_verdict(case)['ok'])

    def test_target_coordinates_and_generation_still_reject_drift(self):
        for surface in ['snapshot', 'raw', 'receipt']:
            for key in ['generation', 'lat', 'lon']:
                with self.subTest(surface=surface, key=key):
                    case = healthy_refresh_case()
                    target = (case['after']['target'] if surface == 'snapshot' else case['after']['raw']['target']
                              if surface == 'raw' else case['after']['actualCloud']['publication']['target'])
                    target[key] += 1
                    self.assertIsNone(ORACLE.healthy_refresh_record(case['after']))
                    self.assertFalse(refresh_verdict(case)['ok'])
        for owner in ['runtime', 'request']:
            with self.subTest(owner=owner):
                case = healthy_refresh_case()
                if owner == 'runtime':
                    case['after']['runtimeGeneration'] += 1
                else:
                    case['ledger'][-1]['nativeOwner']['generation'] += 1
                self.assertFalse(refresh_verdict(case)['ok'])

    def test_raw_and_snapshot_provenance_must_remain_equal(self):
        case = healthy_refresh_case()
        case['after']['raw']['target']['provider'] = 'unmatched provenance'
        self.assertIsNone(ORACLE.healthy_refresh_record(case['after']))
        case = healthy_refresh_case()
        case['full'][1]['raw']['target']['source'] = 'manual'
        self.assertTrue(ORACLE.healthy_refresh_pair(case['before'], case['after'], case['ledger'], case['clock'])['ok'])
        verdict = refresh_verdict(case)
        self.assertFalse(verdict['ok'])
        self.assertFalse(verdict['checks']['allRetainedFullSamplesHealthy'])

    def test_absent_or_wrong_observed_clock_origin_fails_closed(self):
        good = healthy_refresh_case()['clock']
        origins = [None, {}, {'started': good['started']}, {'startUtc': good['startUtc']},
                   {**good, 'started': 0}, {**good, 'started': good['started'] + 1},
                   {**good, 'started': -1}, {**good, 'started': True}, {**good, 'startUtc': good['startUtc'] + 1}]
        for origin in origins:
            with self.subTest(origin=origin):
                case = healthy_refresh_case(); case['clock'] = origin
                self.assertFalse(refresh_verdict(case)['ok'])
        case = healthy_refresh_case()
        # Omitting the new context is explicit missing evidence, never a zero origin.
        self.assertFalse(ORACLE.healthy_refresh_pair(case['before'], case['after'], case['ledger'])['ok'])

    def test_consistent_nonzero_origins_do_not_assume_navigation_zero(self):
        for origin in [0.125, 125.25, 7777.375, 65536.5]:
            with self.subTest(origin=origin):
                case = healthy_refresh_case(performance_origin=origin)
                request = ORACLE._healthy_refresh_request(ORACLE.healthy_refresh_record(case['after']),
                                                         case['after'], case['ledger'], case['clock'])
                self.assertIsNotNone(request)
                self.assertEqual(request['timing']['jsonPerformanceMs'], origin + 180005)
                self.assertTrue(refresh_verdict(case)['ok'])

    def test_origin_is_bound_to_existing_native_motion_observations(self):
        for endpoint in ['before', 'after']:
            for field in ['lastRt', 'elapsedRtMs']:
                with self.subTest(endpoint=endpoint, field=field):
                    case = healthy_refresh_case()
                    case[endpoint]['actualCloud']['motion'][field] += 0.01
                    self.assertIsNone(ORACLE._healthy_refresh_clock(case[endpoint], case['clock']))
                    self.assertFalse(refresh_verdict(case)['ok'])
        case = healthy_refresh_case()
        del case['after']['actualCloud']['motion']['lastRt']
        self.assertIsNone(ORACLE._healthy_refresh_clock(case['after'], case['clock']))

    def test_epoch_shaped_deadline_cannot_masquerade_as_native_deadline(self):
        case = healthy_refresh_case()
        case['ledger'][-1]['nativeOwner']['deadlineAt'] = REFRESH_START_UTC + 192000
        self.assertFalse(refresh_verdict(case)['ok'])

    def test_body_completion_at_or_after_native_deadline_is_refused(self):
        for late_ms in [0, 0.25, 5]:
            with self.subTest(late_ms=late_ms):
                case = healthy_refresh_case(end_ms=205000)
                request = case['ledger'][-1]
                request['jsonElapsedMs'] = request['nativeOwner']['deadlineAt'] - case['clock']['started'] + late_ms
                record, captured = self.receipt_probe(case, case['clock']['startUtc'] + math.ceil(request['jsonElapsedMs']))
                self.assertIsNone(ORACLE._healthy_refresh_request(record, captured, case['ledger'], case['clock']))

    def test_whole_integer_receipt_interval_must_strictly_precede_deadline(self):
        case = healthy_refresh_case(end_ms=205000)
        deadline_elapsed = case['ledger'][-1]['nativeOwner']['deadlineAt'] - case['clock']['started']
        self.assertEqual(deadline_elapsed, 190000)
        # Whole interval ending one millisecond before the deadline is proven safe.
        record, captured = self.receipt_probe(case, case['clock']['startUtc'] + deadline_elapsed - 2)
        matched = ORACLE._healthy_refresh_request(record, captured, case['ledger'], case['clock'])
        self.assertIsNotNone(matched)
        self.assertEqual(matched['timing']['deadlineMarginFromReceiptUpperMs'], 1)
        # Exact upper-bound contact is deliberately conservative; receipt at the
        # deadline or later must also fail. These are matcher-only interval probes.
        for offset in [-1, 0, 1]:
            with self.subTest(receipt_offset_from_deadline=offset):
                record, captured = self.receipt_probe(case, case['clock']['startUtc'] + deadline_elapsed + offset)
                self.assertIsNone(ORACLE._healthy_refresh_request(record, captured, case['ledger'], case['clock']))
        case['ledger'][-1]['nativeOwner']['deadlineAt'] -= 0.5
        record, captured = self.receipt_probe(case, case['clock']['startUtc'] + deadline_elapsed - 1)
        self.assertIsNone(ORACLE._healthy_refresh_request(record, captured, case['ledger'], case['clock']))

    def test_ambiguous_consumed_response_is_still_refused(self):
        case = healthy_refresh_case()
        case['ledger'].append(deepcopy(case['ledger'][-1]))
        self.assertIsNone(ORACLE._healthy_refresh_request(ORACLE.healthy_refresh_record(case['after']),
                                                        case['after'], case['ledger'], case['clock']))
        self.assertFalse(refresh_verdict(case)['ok'])

    def test_fractional_epoch_receipt_cannot_claim_an_integer_clock_interval(self):
        case = healthy_refresh_case()
        record, captured = self.receipt_probe(case, case['new']['retrievedAt'] + 0.5)
        self.assertIsNone(ORACLE._healthy_refresh_request(record, captured, case['ledger'], case['clock']))

    def test_source_or_receipt_substitution_does_not_match_consumed_record(self):
        for surface, field in [('raw', 'currentValidAt'), ('raw', 'retrievedAt'),
                               ('candidate', 'sourceValidAt'), ('candidate', 'retrievedAt'), ('receipt', 'retrievedAt')]:
            with self.subTest(surface=surface, field=field):
                case = healthy_refresh_case()
                value = case['after']['actualCloud']['publication'] if surface == 'receipt' else case['after'][surface]
                value[field] += 1
                self.assertIsNone(ORACLE.healthy_refresh_record(case['after']))
                self.assertFalse(refresh_verdict(case)['ok'])
