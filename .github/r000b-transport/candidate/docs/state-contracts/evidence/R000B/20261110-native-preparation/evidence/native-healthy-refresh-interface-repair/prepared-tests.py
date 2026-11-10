"""Pure HN1–HN4 harness controls: no browser, listener, product body, or main().

Frozen-v1 driver SHA256:
6f0669ced88030c2dd3b9db40520cf1b5aa68669e019cfc3623b0952494f0e7f
The small old predicates below preserve the independent review's counterexamples.
The new predicates are extracted from the actual driver FunctionDef nodes.
"""

# R000B_F01_HEALTHY_REFRESH_ORACLE_CONTROLS_V1
# R000B_HR1_HR2_INTERFACE_CONTROLS_V1
import ast
import datetime
from copy import deepcopy
import math
from pathlib import Path
import re
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / 'tools/qa/run_r000b_withdrawal.py'
FIXTURE = ROOT / 'tests/rlgwo/r000b-no-timetable-fixture.html'
NAMES = {'_finite_number', '_bounds', '_column_alpha_support', 'rain_origin_evidence',
         'rain_origin', 'observed_sky_error_fields', 'all_visible_joins_empty',
         'resume_visible_sequence', 'cloud_motion_continuity', 'phase_progress',
         'actual_empty', 'effects_off', 'joined_empty', 'independent_celestial', 'healthy_cloud',
         '_healthy_refresh_target_projection', '_healthy_refresh_clock',
         'healthy_refresh_record', '_healthy_refresh_request', '_healthy_refresh_receipt',
         '_healthy_refresh_sample', 'healthy_refresh_pair', 'healthy_refresh_evidence'}


def load_oracles(path=DRIVER):
    parsed = ast.parse(path.read_text())
    functions = [node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name in NAMES]
    namespace = {'math': math, 're': re, 'datetime': datetime, 'EXPECTED_COVERAGE': [0.92, 0.90, 0.60],
                 'INITIAL_SOURCE_UTC': 1788900300000}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), namespace)
    return SimpleNamespace(**{name: namespace[name] for name in NAMES if name in namespace})


ORACLE = load_oracles()
PHASE_PERIOD, NOISE_PERIOD = 1.25, 4294967296
WIND_X = -math.sin(math.radians(225))
CLOUD_SPEED = 0.06 + 0.6 * ((2 - 0.5) / (14 - 0.5))
PHASE_RATES = [WIND_X * CLOUD_SPEED * (0.024 + i * 0.006) for i in range(3)]
LIFE_RATES = [0.018 + i * 0.004 for i in range(3)]


def old_phase_progress(a, b):
    return [min(abs(x - y), 1.25 - abs(x - y)) for x, y in zip(a['phase'], b['phase'])]


def old_bounded_phase(a, b, elapsed_ms):
    return max(old_phase_progress(a, b)) <= max(0.03, elapsed_ms / 1000 * 0.05)


def old_rain_origin(state):
    effects = state['effects']
    shown = [p for p in effects['particles'] if p['displayed']]
    return (effects['cloudGateActive'] and bool(shown)
            and all(p['kind'] == 'rain' and p['normalizedDensity'] is not None
                    and p['normalizedDensity'] > 0.16 for p in shown))


def motion_point(at, phase=None, life=None, wander=19600000.0, paused=False, reduced=False):
    return {'elapsedMs': at, 'motion': {'key': 'declared-fixed-site', 'population': 313.25,
        'fieldSeed': 17.75, 'phase': phase or [0.3, 0.5, 0.7],
        'life': life or [32100000.0, 39200000.0, 46300000.0], 'wander': wander,
        'lastRt': at + 100, 'elapsedRtMs': at, 'paused': paused, 'reduced': reduced,
        'wind': {'wx': WIND_X, 'wspd': CLOUD_SPEED}}}


def advance(point, at, seconds=None):
    result = deepcopy(point)
    dt = (at - point['motion']['elapsedRtMs']) / 1000 if seconds is None else seconds
    result['elapsedMs'] = at
    m = result['motion']; m['elapsedRtMs'] = at; m['lastRt'] = at + 100
    m['phase'] = [(v - rate * dt) % PHASE_PERIOD for v, rate in zip(m['phase'], PHASE_RATES)]
    m['life'] = [(v + rate * dt) % NOISE_PERIOD for v, rate in zip(m['life'], LIFE_RATES)]
    m['wander'] = (m['wander'] + 0.011 * dt) % NOISE_PERIOD
    return result


def reset_counterexample():
    before = motion_point(8900, phase=[1.2308685189282167, 1.226085648660271, 1.2213027783923252])
    after = deepcopy(before); after['elapsedMs'] = 8920; after['motion']['elapsedRtMs'] = 8920
    after['motion'].update(phase=[0.0, 0.0, 0.0], life=[0.0, 0.0, 0.0], wander=0.0)
    return before, after


def make_image(width, height, points, mask=False):
    rgba = bytearray(bytes([255, 255, 255, 255]) * (width * height) if mask else bytes(width * height * 4))
    for x, y, alpha in points:
        at = (y * width + x) * 4
        rgba[at:at + 4] = bytes([180, 190, 210, 255 - alpha if mask else alpha])
    return width, height, bytes(rgba)


def rain_scene(column=5, source_top=None, fraction=0.5, reduced=False, empty_column=False, clear_mask=False):
    bounds = {'left': 1, 'top': 1, 'width': 323, 'height': 528}
    left_percent = column / 144 * 100
    pos = {'left': left_percent / 100 * 323, 'top': 0.19 * 528 if source_top is None else source_top,
           'width': 1.5, 'height': 14}
    base = {'left': 1 + pos['left'], 'top': 1 + pos['top'], 'width': pos['width'], 'height': pos['height']}
    tx, ty = (0, 0) if reduced else (fraction * 8, -10 + 142 * fraction)
    rect = {**base, 'left': base['left'] + tx, 'top': base['top'] + ty}
    particle = {'index': 0, 'displayed': True, 'kind': 'rain', 'normalizedDensity': 0.9,
                'originTop': str(pos['top']) + 'px', 'column': column, 'leftPercent': left_percent,
                'opacity': 0.6, 'animation': 'none' if reduced else 'fall', 'rect': rect,
                'originGeometry': {'position': pos, 'baseOrigin': base,
                    'parent': {'bounds': bounds.copy(), 'clientLeft': 0, 'clientTop': 0, 'clientWidth': 323,
                               'clientHeight': 528, 'offsetWidth': 323, 'offsetHeight': 528},
                    'transform': {'is2D': True, 'a': 1, 'b': 0, 'c': 0, 'd': 1, 'e': tx, 'f': ty}}}
    native_column = 30 if empty_column else column
    mask_column = 70 if empty_column else math.floor((base['left'] - 1 + 0.75) * 325 / 323)
    native = make_image(144, 232, [(native_column, 45, 255)])
    mask = make_image(325, 530, [] if clear_mask else [(mask_column, 100, 255)], mask=True)
    columns = [0] * 144; columns[native_column] = 255
    state = {'actualCloud': {'ready': True, 'coverage': [0.92, 0.90, 0.60],
                'density': {'max': 10, 'nonzero': 2},
                'raster': {'alphaSum': 255, 'alphaNonzero': 1, 'columnAlpha': columns,
                           'bounds': bounds.copy(), 'filter': 'blur(0.55px)'}},
             'celestial': {'activeCanvas': {'bounds': bounds.copy()},
                           'consumedSolarMask': {'blockedAlphaSum': 0 if clear_mask else 255}},
             'effects': {'cloudGateActive': True, 'rainSlant': '8px', 'particles': [particle]}}
    return state, native, mask


def resume_scene(status='ready', stale=False, visible=True):
    receipt = {'revision': 2, 'state': 'withdrawn-unavailable'}
    composition = {'maxCloudAlpha': 1 if stale else 0, 'meanCloudAlpha': 0.2 if stale else 0,
                   'cloudAuthority': {'revision': 1, 'state': 'eligible-published'} if stale else receipt}
    canvas = {'visibility': 'visible', 'display': 'block', 'opacity': 1, 'rgbNonzero': 100,
              'maxRGB': 100, 'minRGB': 0, 'bounds': {'left': 1, 'top': 1, 'width': 323, 'height': 528}}
    return {'modelIsNull': True, 'actualCloud': {'ready': False, 'coverage': [0, 0, 0], 'targets': [0, 0, 0],
                'density': {'sum': 0, 'max': 0, 'nonzero': 0}, 'raster': {'alphaSum': 0, 'alphaNonzero': 0}, 'publication': receipt},
            'effects': {'precip': 'off', 'lightning': 'off', 'rainOpacity': 0, 'displayedParticles': 0},
            'celestial': {'owner': 'refined' if visible else None, 'status': status,
                'consumedSolarMask': {'blockedAlphaSum': 255 if stale else 0}, 'composition': composition,
                'activeCanvas': canvas if visible else None, 'skyPending': False, 'frameAgeMs': 3000,
                'moonReady': True, 'moonPresence': 0.02,
                'visibleForegrounds': [{'owner': 'refined', 'status': status, 'canvas': canvas, 'composition': composition}] if visible else []}}


class ReadBoundaryTests(unittest.TestCase):
    def test_hn1_effectful_lunar_runtime_api_absent_from_bridge(self):
        text = FIXTURE.read_text()
        bridge = text[text.index('function installWithdrawalReadBridge(){'):text.index('\n  async function start(){')]
        self.assertNotIn('SalahMoonRuntime', bridge)
        for name in ['render', 'paintClouds', 'tieRainToClouds', 'fetchWeather', 'fetchRadar', 'loadPrayerData',
                     'applyCloudState', 'atmosphere', 'reconcileClouds', 'cloudsCurrent', 'cloudPublicationCurrent', 'surface', 'applyConfig', 'adoptPrayerBundle']:
            self.assertNotRegex(re.sub(r'//[^\n]*', '', bridge), r'\b' + name + r'\s*\(')

    def test_hn1_missing_error_fields_are_unobserved(self):
        fields = ORACLE.observed_sky_error_fields({'celestial': {}})
        self.assertTrue(all(field['observed'] is False and field['value'] is None for field in fields))
        fields = ORACLE.observed_sky_error_fields({'celestial': {'refined': {'errors': []}, 'preview': {'catalogueError': 'failed'}}})
        self.assertEqual([field['observed'] for field in fields], [True, True])
        self.assertEqual([field['value'] for field in fields], [[], 'failed'])


class MotionTests(unittest.TestCase):
    def test_hn2_exact_8_9_second_reset_old_pass_new_fail(self):
        before, after = reset_counterexample()
        self.assertTrue(old_bounded_phase(before['motion'], after['motion'], 20))
        verdict = ORACLE.cloud_motion_continuity([before, after], 'default')
        self.assertFalse(verdict['ok'])
        self.assertTrue(any(v.get('axis', '').startswith('phase') for v in verdict['violations']))

    def test_hn2_life_or_wander_reset_with_held_phase_old_pass_new_fail(self):
        for axis in ['life', 'wander']:
            with self.subTest(axis=axis):
                before = motion_point(8900); after = deepcopy(before)
                after['elapsedMs'] = after['motion']['elapsedRtMs'] = 8920
                after['motion'][axis] = [0, 0, 0] if axis == 'life' else 0
                self.assertTrue(old_bounded_phase(before['motion'], after['motion'], 20))
                self.assertFalse(ORACLE.cloud_motion_continuity([before, after], 'full')['ok'])

    def test_healthy_signed_wrap_and_noise_wrap(self):
        before = motion_point(1000, phase=[0.00001, 0.3, 1.1],
                              life=[1e8, NOISE_PERIOD - 0.01, 2e8], wander=NOISE_PERIOD - 0.005)
        after = advance(before, 1800)
        self.assertTrue(ORACLE.cloud_motion_continuity([before, after], 'default')['ok'])

    def test_reduced_axes_hold_and_reject_even_small_life_drift(self):
        before = motion_point(1000, reduced=True); after = deepcopy(before)
        after['elapsedMs'] = after['motion']['elapsedRtMs'] = 10000
        self.assertTrue(ORACLE.cloud_motion_continuity([before, after], 'reduced')['ok'])
        after['motion']['life'][0] += 0.001
        self.assertFalse(ORACLE.cloud_motion_continuity([before, after], 'reduced')['ok'])

    def test_hidden_hold_resume_active_time_and_no_backlog(self):
        before = motion_point(4000); paused = advance(before, 5000); paused['motion']['paused'] = True
        held = deepcopy(paused); held['elapsedMs'] = 11000
        resume_boundary = deepcopy(paused); resume_boundary['elapsedMs'] = resume_boundary['motion']['elapsedRtMs'] = 12000
        resume_boundary['motion']['paused'] = False
        resumed = advance(resume_boundary, 12020, seconds=0.02)
        changes = [{'hidden': True, 'nativeMotionAfter': paused['motion']}, {'hidden': False, 'nativeMotionAfter': resume_boundary['motion']}]
        self.assertTrue(ORACLE.cloud_motion_continuity([before, paused, held, resume_boundary, resumed], 'default', changes)['ok'])
        backlog = advance(resume_boundary, 12020, seconds=7.02)
        self.assertFalse(ORACLE.cloud_motion_continuity([before, paused, held, resume_boundary, backlog], 'default', changes)['ok'])

    def test_hidden_axes_must_hold(self):
        before = motion_point(5000, paused=True); after = deepcopy(before); after['elapsedMs'] = 10000
        after['motion']['wander'] += 0.001
        self.assertFalse(ORACLE.cloud_motion_continuity([before, after], 'default')['ok'])


class RainTests(unittest.TestCase):
    def qualify(self, state, native, mask):
        state['rainOriginEvidence'] = ORACLE.rain_origin_evidence(state, native, mask)
        return ORACLE.rain_origin(state)

    def test_hn3_displaced_base_old_pass_new_fail(self):
        state, native, mask = rain_scene(source_top=0)
        self.assertTrue(old_rain_origin(state)); self.assertTrue(ORACLE.healthy_cloud(state))
        self.assertFalse(self.qualify(state, native, mask))
        self.assertIn('Declared19% CSS base origin displaced', state['rainOriginEvidence']['particles'][0]['errors'])

    def test_hn3_distant_only_alpha_old_pass_new_fail(self):
        state, native, mask = rain_scene(empty_column=True)
        self.assertTrue(old_rain_origin(state)); self.assertTrue(ORACLE.healthy_cloud(state))
        self.assertEqual(state['actualCloud']['raster']['columnAlpha'][5], 0)
        self.assertFalse(self.qualify(state, native, mask))
        evidence = state['rainOriginEvidence']['particles'][0]
        self.assertEqual(evidence['nativeSupport']['alphaSum'], 0)
        self.assertEqual(evidence['publishedSupport']['alphaSum'], 0)

    def test_healthy_slanted_visible_segment_uses_untransformed_column(self):
        state, native, mask = rain_scene(fraction=0.65)
        self.assertTrue(self.qualify(state, native, mask))
        point = state['rainOriginEvidence']['particles'][0]
        self.assertNotEqual(point['baseOrigin']['left'], point['visibleSegment']['left'])
        self.assertAlmostEqual(point['fallFraction'], 0.65)

    def test_healthy_reduced_segment_is_held_at_base(self):
        self.assertTrue(self.qualify(*rain_scene(reduced=True)))

    def test_masked_out_native_alpha_does_not_supply_displayed_support(self):
        state, native, mask = rain_scene(clear_mask=True)
        self.assertFalse(self.qualify(state, native, mask))

    def test_wrong_slant_or_nontranslation_transform_fails(self):
        for mutation in ['slant', 'rotation']:
            with self.subTest(mutation=mutation):
                state, native, mask = rain_scene()
                if mutation == 'slant':
                    state['effects']['rainSlant'] = '80px'
                else:
                    state['effects']['particles'][0]['originGeometry']['transform']['b'] = 0.1
                self.assertFalse(self.qualify(state, native, mask))

    def test_contract_does_not_invent_invisible_start_exact_contour(self):
        state, native, mask = rain_scene()
        point = state['effects']['particles'][0]
        source_mask_column = math.floor((point['originGeometry']['baseOrigin']['left'] - 1 + 0.75) * 325 / 323)
        # Same displayed cloud column within the retained vertical deck. The
        # bounded oracle deliberately does not require the alpha to touch the
        # invisible animation start or an invented exact cloud-base contour.
        mask = make_image(325, 530, [(source_mask_column, 130, 255)], mask=True)
        self.assertTrue(self.qualify(state, native, mask))


class ResumeTests(unittest.TestCase):
    def test_hn4_visible_pending_stale_then_ready_old_pass_new_fail(self):
        first, later = resume_scene(status='pending', stale=True), resume_scene()
        self.assertTrue(ORACLE.actual_empty(first) and ORACLE.effects_off(first) and first['modelIsNull'])
        old_selected_first = first['celestial']['owner'] and first['celestial']['status'] == 'ready' and first['celestial']['activeCanvas']['visibility'] == 'visible'
        self.assertFalse(old_selected_first)
        self.assertTrue(ORACLE.actual_empty(later) and ORACLE.joined_empty(later) and ORACLE.independent_celestial(later))
        self.assertFalse(ORACLE.all_visible_joins_empty(first))
        self.assertFalse(ORACLE.resume_visible_sequence([first, later]))

    def test_intervening_visible_pending_stale_frame_is_not_erased(self):
        self.assertFalse(ORACLE.resume_visible_sequence([resume_scene(status='pending'), resume_scene(status='pending', stale=True), resume_scene()]))

    def test_clean_pending_visible_then_ready_is_healthy(self):
        self.assertTrue(ORACLE.resume_visible_sequence([resume_scene(status='pending'), resume_scene()]))

    def test_no_displayed_first_frame_then_clean_visible_recovery(self):
        self.assertTrue(ORACLE.resume_visible_sequence([resume_scene(status='pending', visible=False), resume_scene()]))

    def test_observer_records_visibility_before_separate_ready_endpoint(self):
        source = FIXTURE.read_text()
        observer = source[source.index('observeResume(owner){'):source.index('\n  async function start(){')]
        self.assertIn('actuallyDisplayed(document.querySelector', observer)
        self.assertLess(observer.index('report.resumeOpportunities.push'), observer.index('if(ready)'))
        self.assertIn('if(visible&&!report.resumeFirstVisible)', observer)


REFRESH_START_UTC = 1788900300000 + 890000


def healthy_refresh_case(refresh_ms=180000, end_ms=None, mode='default', performance_origin=125.25):
    """Invented observations/owned responses; no product or browser execution."""
    start_ms, end_ms = 130000, (refresh_ms + 1000 if end_ms is None else end_ms)
    prior_ms = refresh_ms - 60000
    clock = {'started': performance_origin, 'startUtc': REFRESH_START_UTC}
    target = {'generation': 7, 'lat': 24.7136, 'lon': 46.6753, 'intent': 'fixed-site', 'source': 'hash',
              'accuracyM': None, 'acquiredAt': None, 'provider': None, 'area': None, 'bounds': None}

    def receipt(request_ms, revision):
        return {'revision': revision, 'state': 'eligible-published', 'reason': 'complete atmosphere',
                'target': {'generation': 7, 'lat': 24.7136, 'lon': 46.6753}, 'lane': 'live',
                'sourceValidAt': (REFRESH_START_UTC + request_ms) // 60000 * 60000,
                'retrievedAt': REFRESH_START_UTC + request_ms + 10,
                'conditionState': 'model-estimated-rain',
                'at': REFRESH_START_UTC + (start_ms if revision == 4 else request_ms + 20)}

    old, new = receipt(prior_ms, 4), receipt(refresh_ms, 5)
    seed = motion_point(start_ms, phase=[0.6, 0.8, 1.0], reduced=mode == 'reduced')

    def frame(at, active, candidate=None):
        candidate = active if candidate is None else candidate
        state = rain_scene()[0]
        state.update(elapsedMs=at, wallUtcMs=REFRESH_START_UTC + at, modelIsNull=False,
            loopStarted=True, cloudReady=True, coverage=EXPECTED_REFRESH_COVERAGE.copy(),
            publication=deepcopy(active), documentHidden=False, documentVisibility='visible', cardPaused=False,
            foregroundOwner='refined', foregroundVisible=True, foregroundHasCloudMask=True,
            precip='on', lightning='off', target=target.copy(), runtimeGeneration=7, selected=True,
            prayer={'modelIsNull': False, 'todayDay': '09-09-2026'},
            candidate={'eligible': True, 'sourceValidAt': candidate['sourceValidAt'], 'retrievedAt': candidate['retrievedAt']},
            raw={'currentValidAt': candidate['sourceValidAt'], 'retrievedAt': candidate['retrievedAt'], 'target': target.copy()},
            rainOriginEvidence={'schema': 'r000b-rain-origin/v2', 'ok': True})
        moved = advance(seed, at, seconds=0 if mode == 'reduced' else (at - start_ms) / 1000)['motion']
        moved['lastRt'] = clock['started'] + moved['elapsedRtMs']
        state['motion'] = deepcopy(moved)
        state['actualCloud'].update(publication=deepcopy(active), targets=EXPECTED_REFRESH_COVERAGE.copy(), motion=deepcopy(moved))
        canvas = {'visibility': 'visible', 'display': 'block', 'opacity': 1, 'rgbNonzero': 100,
                  'maxRGB': 100, 'minRGB': 0, 'bounds': {'left': 1, 'top': 1, 'width': 323, 'height': 528}}
        composition = {'maxCloudAlpha': 0.8, 'meanCloudAlpha': 0.1, 'cloudAuthority': deepcopy(active)}
        state['celestial'].update(owner='refined', status='ready', skyPending=False, frameAgeMs=100,
            moonReady=True, moonPresence=0.02, activeCanvas=deepcopy(canvas), composition=deepcopy(composition),
            visibleForegrounds=[{'owner': 'refined', 'status': 'ready', 'canvas': deepcopy(canvas), 'composition': deepcopy(composition)}])
        return state

    def request(at, active, ordinal):
        civil = datetime.datetime.fromtimestamp(active['sourceValidAt'] / 1000, datetime.timezone.utc) + datetime.timedelta(hours=3)
        return {'kind': 'weather', 'weatherOrdinal': ordinal, 'elapsedMs': at, 'wallUtcMs': REFRESH_START_UTC + at,
                'jsonElapsedMs': at + 5, 'jsonReads': 1, 'jsonSettled': True, 'status': 200, 'result': 'json-consumed',
                'nativeOwner': {'generation': 7, 'operationId': ordinal * 2, 'attemptId': ordinal * 3,
                                'deadlineAt': clock['started'] + at + 10000},
                'inputBody': {'timezone': 'Asia/Riyadh', 'current': {'time': civil.strftime('%Y-%m-%dT%H:%M'), 'interval': 900}}}

    def passive_frame(at, active, candidate=None):
        full = frame(at, active, candidate)
        names = ('elapsedMs', 'wallUtcMs', 'modelIsNull', 'loopStarted', 'cloudReady', 'coverage', 'publication',
                 'motion', 'candidate', 'documentHidden', 'documentVisibility', 'cardPaused', 'foregroundOwner',
                 'foregroundVisible', 'foregroundHasCloudMask', 'precip', 'lightning')
        return {name: full[name] for name in names}

    before, after = frame(start_ms, old), frame(end_ms, new)
    trace = [passive_frame(at, old if at < refresh_ms + 20 else new) for at in range(start_ms + 1000, end_ms, 1000)]
    if start_ms < refresh_ms + 15 < end_ms:
        trace.append(passive_frame(refresh_ms + 15, old, new))
    trace.sort(key=lambda value: value['elapsedMs'])
    watch_end = min(start_ms + 30000, end_ms)
    watch = frame(watch_end, old if watch_end < refresh_ms + 20 else new)
    return {'before': before, 'after': after, 'passive': trace, 'full': [before, watch, after],
            'ledger': [request(prior_ms, old, 2), request(refresh_ms, new, 3)], 'mode': mode, 'frame': frame, 'passiveFrame': passive_frame,
            'old': old, 'new': new, 'refreshMs': refresh_ms, 'clock': clock}


EXPECTED_REFRESH_COVERAGE = [0.92, 0.90, 0.60]


def refresh_verdict(case):
    return ORACLE.healthy_refresh_evidence(case['before'], case['after'], case['passive'],
                                         case['full'], case['ledger'], case['mode'], case.get('clock'))


class HealthyRefreshTests(unittest.TestCase):
    def test_refresh_inside_existing_30_second_watch_reuses_real_pair(self):
        case = healthy_refresh_case(refresh_ms=150000, end_ms=160000)
        verdict = refresh_verdict(case)
        self.assertTrue(verdict['ok'], verdict)
        self.assertGreater(verdict['pair']['afterRequest']['elapsedMs'], case['before']['elapsedMs'])
        self.assertEqual(verdict['pair']['afterRecord']['publication'], case['after']['celestial']['composition']['cloudAuthority'])

    def test_later_ordinary_refresh_allows_A_lease_during_B_handoff(self):
        case = healthy_refresh_case()
        handoff = case['frame'](case['refreshMs'] + 15, case['old'], case['new'])
        handoff['celestial']['status'] = 'pending'
        handoff['celestial']['visibleForegrounds'][0]['status'] = 'pending'
        case['full'].append(handoff)
        verdict = refresh_verdict(case)
        self.assertTrue(verdict['ok'], verdict)
        self.assertEqual(handoff['publication']['retrievedAt'], case['old']['retrievedAt'])
        self.assertNotEqual(handoff['candidate']['retrievedAt'], handoff['publication']['retrievedAt'])

    def test_no_post_recovery_record_replacement_cannot_qualify(self):
        case = healthy_refresh_case()
        case['after'] = case['frame'](181000, case['old'])
        self.assertFalse(refresh_verdict(case)['ok'])
        self.assertFalse(ORACLE.healthy_refresh_pair(case['before'], case['after'], case['ledger'], case.get('clock'))['ok'])

    def test_request_started_before_model_recovery_cannot_qualify(self):
        case = healthy_refresh_case(refresh_ms=120000, end_ms=160000)
        pair = ORACLE.healthy_refresh_pair(case['before'], case['after'], case['ledger'], case.get('clock'))
        self.assertFalse(pair['ok'])
        self.assertIn('after recovery', pair['reason'])

    def test_timestamp_only_renewal_or_missing_consumed_owned_response_fails(self):
        for fault in ['same-source-renewal', 'json-unread', 'json-unsettled', 'missing-owner', 'same-operation', 'expired-attempt']:
            with self.subTest(fault=fault):
                case = healthy_refresh_case()
                if fault == 'same-source-renewal':
                    renewed = deepcopy(case['new']); renewed['sourceValidAt'] = case['old']['sourceValidAt']
                    case['after'] = case['frame'](181000, renewed)
                elif fault == 'json-unread':
                    case['ledger'][-1]['jsonReads'] = 0
                elif fault == 'json-unsettled':
                    case['ledger'][-1]['jsonSettled'] = False
                elif fault == 'missing-owner':
                    case['ledger'][-1]['nativeOwner']['operationId'] = None
                elif fault == 'same-operation':
                    case['ledger'][-1]['nativeOwner']['operationId'] = case['ledger'][0]['nativeOwner']['operationId']
                else:
                    case['ledger'][-1]['nativeOwner']['deadlineAt'] = case['clock']['started'] + (case['new']['retrievedAt'] - case['clock']['startUtc'])
                self.assertFalse(refresh_verdict(case)['ok'])

    def test_supplied_body_time_cannot_be_substituted_by_candidate_timestamp(self):
        case = healthy_refresh_case()
        case['ledger'][-1]['inputBody']['current']['time'] = case['ledger'][0]['inputBody']['current']['time']
        self.assertFalse(refresh_verdict(case)['ok'])

    def test_candidate_B_without_native_or_foreground_B_receipt_fails(self):
        for fault in ['native-A', 'foreground-A', 'no-receipt']:
            with self.subTest(fault=fault):
                case = healthy_refresh_case()
                if fault == 'native-A':
                    case['after'] = case['frame'](181000, case['old'], case['new'])
                elif fault == 'foreground-A':
                    case['after']['celestial']['composition']['cloudAuthority'] = deepcopy(case['old'])
                    case['after']['celestial']['visibleForegrounds'][0]['composition']['cloudAuthority'] = deepcopy(case['old'])
                else:
                    case['after']['actualCloud']['publication'] = None
                self.assertFalse(refresh_verdict(case)['ok'])

    def test_every_retained_passive_gap_is_checked_despite_healthy_endpoints(self):
        for field, bad_value in [('modelIsNull', True), ('cloudReady', False), ('coverage', [0, 0, 0]),
                                 ('foregroundVisible', False), ('foregroundHasCloudMask', False), ('precip', 'off')]:
            with self.subTest(field=field):
                case = healthy_refresh_case()
                case['passive'][12][field] = bad_value
                self.assertTrue(ORACLE.healthy_refresh_pair(case['before'], case['after'], case['ledger'], case.get('clock'))['ok'])
                verdict = refresh_verdict(case)
                self.assertFalse(verdict['ok'])
                self.assertFalse(verdict['checks']['allRetainedPassiveSamplesHealthy'])

    def test_every_retained_full_raster_mask_and_foreground_is_checked(self):
        for fault in ['native-raster', 'mask', 'foreground-alpha', 'rain-origin']:
            with self.subTest(fault=fault):
                case = healthy_refresh_case()
                middle = case['full'][1]
                if fault == 'native-raster':
                    middle['actualCloud']['raster']['alphaSum'] = 0
                    middle['actualCloud']['raster']['alphaNonzero'] = 0
                elif fault == 'mask':
                    middle['celestial']['consumedSolarMask']['blockedAlphaSum'] = 0
                elif fault == 'foreground-alpha':
                    middle['celestial']['visibleForegrounds'][0]['composition']['meanCloudAlpha'] = 0
                else:
                    middle['rainOriginEvidence']['ok'] = False
                self.assertTrue(ORACLE.healthy_refresh_pair(case['before'], case['after'], case['ledger'], case.get('clock'))['ok'])
                verdict = refresh_verdict(case)
                self.assertFalse(verdict['ok'])
                self.assertFalse(verdict['checks']['allRetainedFullSamplesHealthy'])

    def test_resets_between_clean_endpoints_use_existing_motion_oracle(self):
        for axis in ['phase', 'life', 'wander', 'population']:
            with self.subTest(axis=axis):
                case = healthy_refresh_case()
                motion = case['passive'][12]['motion']
                motion[axis] = [0, 0, 0] if axis in ('phase', 'life') else 0
                self.assertTrue(ORACLE.healthy_refresh_pair(case['before'], case['after'], case['ledger'], case.get('clock'))['ok'])
                verdict = refresh_verdict(case)
                self.assertFalse(verdict['ok'])
                self.assertFalse(verdict['checks']['signedPhaseLifeWanderAndPopulationContinuity'])

    def test_retained_full_snapshot_at_endpoint_timestamp_is_not_skipped(self):
        case = healthy_refresh_case()
        retained = deepcopy(case['before'])
        retained['actualCloud']['raster']['alphaSum'] = 0
        case['full'].append(retained)
        verdict = refresh_verdict(case)
        self.assertFalse(verdict['ok'])
        self.assertFalse(verdict['checks']['allRetainedFullSamplesHealthy'])

    def test_active_A_cannot_renew_its_lease_change_target_lane_or_withdraw(self):
        for fault in ['renew', 'target', 'lane', 'withdrawn', 'expired-age']:
            with self.subTest(fault=fault):
                case = healthy_refresh_case()
                handoff = next(sample for sample in case['passive'] if sample['elapsedMs'] == case['refreshMs'] + 15)
                if fault == 'renew':
                    handoff['publication']['retrievedAt'] = case['new']['retrievedAt']
                elif fault == 'target':
                    handoff['publication']['target']['lat'] += 1
                elif fault == 'lane':
                    handoff['publication']['lane'] = 'preview'
                elif fault == 'withdrawn':
                    handoff['publication']['state'] = 'withdrawn-unavailable'
                else:
                    handoff['wallUtcMs'] += 900001
                self.assertFalse(refresh_verdict(case)['ok'])

    def test_publication_cannot_roll_back_from_B_to_A_between_endpoints(self):
        case = healthy_refresh_case()
        case['passive'].extend([case['passiveFrame'](180500, case['new']), case['passiveFrame'](180750, case['old'], case['new'])])
        verdict = refresh_verdict(case)
        self.assertFalse(verdict['ok'])
        self.assertFalse(verdict['checks']['consumedPublicationMovesOnlyFromAToB'])

    def test_missing_passive_interval_is_not_continuity_proof(self):
        case = healthy_refresh_case(); case['passive'] = []
        verdict = refresh_verdict(case)
        self.assertFalse(verdict['ok'])
        self.assertFalse(verdict['checks']['allRetainedPassiveSamplesHealthy'])

    def test_reduced_and_full_healthy_refresh_use_existing_motion_modes(self):
        for mode in ['reduced', 'full']:
            with self.subTest(mode=mode):
                verdict = refresh_verdict(healthy_refresh_case(mode=mode))
                self.assertTrue(verdict['ok'], verdict)


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


if __name__ == '__main__':
    unittest.main()
