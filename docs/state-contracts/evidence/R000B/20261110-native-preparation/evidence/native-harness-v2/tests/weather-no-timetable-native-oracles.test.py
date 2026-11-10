"""Pure HN1–HN4 harness controls: no browser, listener, product body, or main().

Frozen-v1 driver SHA256:
6f0669ced88030c2dd3b9db40520cf1b5aa68669e019cfc3623b0952494f0e7f
The small old predicates below preserve the independent review's counterexamples.
The new predicates are extracted from the actual driver FunctionDef nodes.
"""

import ast
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
         'actual_empty', 'effects_off', 'joined_empty', 'independent_celestial', 'healthy_cloud'}


def load_oracles(path=DRIVER):
    parsed = ast.parse(path.read_text())
    functions = [node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name in NAMES]
    namespace = {'math': math, 're': re, 'EXPECTED_COVERAGE': [0.92, 0.90, 0.60]}
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


if __name__ == '__main__':
    unittest.main()
