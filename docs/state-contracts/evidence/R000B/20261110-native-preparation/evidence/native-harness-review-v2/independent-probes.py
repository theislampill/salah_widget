"""Reviewer pure controls: actual retained-v1 and repaired ASTs; no product/main."""
import ast
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path('/workspace/scratch/15b8fb6ac4c2/r000b-work')
OUT = Path(__file__).resolve().parent
V1 = OUT.parent / 'native-harness-v1/tools/qa/run_r000b_withdrawal.py'
V2 = ROOT / 'tools/qa/run_r000b_withdrawal.py'
PINS = {
    str(V1): '6f0669ced88030c2dd3b9db40520cf1b5aa68669e019cfc3623b0952494f0e7f',
    str(V2): '73afb4d772e32bd21f2697777914f3db8d2d28c3833271ef669037b079fb28bc'}
NAMES = {'phase_progress', 'actual_empty', 'joined_empty', 'healthy_cloud',
         'effects_off', 'independent_celestial', 'rain_origin',
         '_finite_number', '_bounds', '_column_alpha_support',
         'rain_origin_evidence', 'all_visible_joins_empty',
         'resume_visible_sequence', 'cloud_motion_continuity'}


def load(path):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PINS[str(path)]
    tree = ast.parse(raw, filename=str(path))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in NAMES]
    ns = {'math': math, 're': re, 'EXPECTED_COVERAGE': [.92, .90, .60]}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), 'exec'), ns)
    return tree, ns


def actual_check(tree, name, ns, **variables):
    nodes = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
             and any(isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant)
                     and t.slice.value == name for t in n.targets)]
    assert len(nodes) == 1, (name, len(nodes))
    return eval(compile(ast.Expression(body=nodes[0].value), '<actual-main-check-AST>', 'eval'),
                {**ns, **variables})


old_tree, old = load(V1)
new_tree, new = load(V2)
results = {'scope': 'pure actual driver predicates and selected actual main check expressions; no imports/main/product execution',
           'driverPins': PINS, 'controls': []}


def retain(name, inputs, outputs, expectations):
    for key, expected in expectations.items():
        assert outputs[key] == expected, (name, key, outputs)
    results['controls'].append({'name': name, 'inputs': inputs, 'outputs': outputs,
                                'expectations': expectations, 'matched': True})


wind_x = -math.sin(math.radians(225))
speed = .06 + .6 * ((2 - .5) / (14 - .5))
before = {'elapsedMs': 8900, 'motion': {
    'key': 'same-site', 'population': 313.25, 'fieldSeed': 17.75,
    'phase': [1.2308685189282167, 1.226085648660271, 1.2213027783923252],
    'life': [32100000., 39200000., 46300000.], 'wander': 19600000.,
    'elapsedRtMs': 8900, 'paused': False, 'reduced': False,
    'wind': {'wx': wind_x, 'wspd': speed}}}
after = deepcopy(before)
after['elapsedMs'] = 8920
after['motion'].update(elapsedRtMs=8920, phase=[0., 0., 0.], life=[0., 0., 0.], wander=0.)
for name, second in [('HN2-original-full-reset', after),
                     ('HN2-life-only-reset', deepcopy(before)),
                     ('HN2-wander-only-reset', deepcopy(before))]:
    if name.endswith('life-only-reset'):
        second['motion']['life'] = [0., 0., 0.]
    if name.endswith('wander-only-reset'):
        second['motion']['wander'] = 0.
    second['elapsedMs'] = second['motion']['elapsedRtMs'] = 8920
    samples = [before, second]
    verdict = new['cloud_motion_continuity'](samples, 'default')
    retain(name, samples, {
        'oldBoundedPhase': actual_check(old_tree, 'boundedPhaseSteps', old, trace=samples),
        'oldPopulation': actual_check(old_tree, 'populationAndSeedRetained', old,
                                      trace=samples, first_motion=before['motion']),
        'newContinuity': verdict['ok'], 'newViolations': verdict['violations']},
        {'oldBoundedPhase': True, 'oldPopulation': True, 'newContinuity': False})

healthy = deepcopy(before)
healthy['elapsedMs'] = healthy['motion']['elapsedRtMs'] = 9900
healthy['motion']['phase'] = [(value - wind_x * speed * (.024 + i * .006)) % 1.25
                             for i, value in enumerate(before['motion']['phase'])]
healthy['motion']['life'] = [value + .018 + i * .004
                            for i, value in enumerate(before['motion']['life'])]
healthy['motion']['wander'] += .011
retain('HN2-healthy-default-and-full', [before, healthy],
       {mode: new['cloud_motion_continuity']([before, healthy], mode)['ok']
        for mode in ('default', 'full')}, {'default': True, 'full': True})


def raster(width, height, points, inverse=False):
    data = bytearray(bytes([255, 255, 255, 255]) * width * height if inverse else bytes(width * height * 4))
    for x, y, alpha in points:
        i = (y * width + x) * 4
        data[i:i + 4] = bytes([180, 190, 210, 255 - alpha if inverse else alpha])
    return width, height, bytes(data)


def rain(top_offset=0., native_column=5, mask_column=12, reduced=False):
    box = {'left': 1., 'top': 1., 'width': 323., 'height': 528.}
    position = {'left': 5 / 144 * 323, 'top': .19 * 528 + top_offset, 'width': 1.5, 'height': 14.}
    base = {**position, 'left': 1 + position['left'], 'top': 1 + position['top']}
    x, y = (0., 0.) if reduced else (5.2, 82.3)
    segment = {**base, 'left': base['left'] + x, 'top': base['top'] + y}
    particle = {'index': 0, 'displayed': True, 'kind': 'rain', 'normalizedDensity': .9,
        'column': 5, 'leftPercent': 5 / 144 * 100, 'originTop': str(position['top']) + 'px',
        'opacity': .6, 'animation': 'none' if reduced else 'fall', 'rect': segment,
        'originGeometry': {'position': position, 'baseOrigin': base,
            'parent': {'bounds': box, 'clientLeft': 0., 'clientTop': 0.,
                       'clientWidth': 323., 'clientHeight': 528., 'offsetWidth': 323., 'offsetHeight': 528.},
            'transform': {'is2D': True, 'a': 1., 'b': 0., 'c': 0., 'd': 1., 'e': x, 'f': y}}}
    columns = [0] * 144; columns[native_column] = 255
    state = {'actualCloud': {'ready': True, 'coverage': [.92, .90, .60],
        'density': {'max': 10., 'nonzero': 2}, 'raster': {'bounds': box,
            'filter': 'blur(0.55px)', 'alphaSum': 255, 'alphaNonzero': 1, 'columnAlpha': columns}},
        'celestial': {'activeCanvas': {'bounds': box}, 'consumedSolarMask': {'blockedAlphaSum': 255}},
        'effects': {'cloudGateActive': True, 'rainSlant': '8px', 'particles': [particle]}}
    return state, raster(144, 232, [(native_column, 45, 255)]), raster(325, 530, [(mask_column, 100, 255)], True)


rain_cases = [
    ('HN3-displaced-base', {'top_offset': -.19 * 528}, False),
    ('HN3-distant-only-alpha', {'native_column': 30, 'mask_column': 70}, False),
    ('HN3-healthy-slanted', {}, True),
    ('HN3-healthy-reduced', {'reduced': True}, True),
    ('HN3-published-mask-no-extra-blur-halo', {'mask_column': 19}, False),
    ('HN3-declared-coordinate-bound-reject', {'top_offset': .76}, False),
    ('HN3-declared-coordinate-bound-allow', {'top_offset': .74}, True)]
for name, arguments, expected in rain_cases:
    state, native, mask = rain(**arguments)
    evidence = new['rain_origin_evidence'](state, native, mask)
    retain(name, {'snapshot': state, 'imageConstruction': {'arguments': arguments,
        'nativeSize': [144, 232], 'maskSize': [325, 530], 'nativePointY': 45,
        'maskPointY': 100, 'pointAlpha': 255, 'maskIsInverseAlpha': True}},
        {'oldHealthy': old['healthy_cloud'](state), 'oldRainOrigin': old['rain_origin'](state),
         'newRainOrigin': evidence['ok'], 'newEvidence': evidence},
        {'oldHealthy': True, 'oldRainOrigin': True, 'newRainOrigin': expected})


receipt = {'revision': 2, 'state': 'withdrawn-unavailable'}
canvas = {'visibility': 'visible', 'display': 'block', 'opacity': 1,
          'bounds': {'left': 1, 'top': 1, 'width': 323, 'height': 528},
          'rgbNonzero': 100, 'maxRGB': 100, 'minRGB': 0}
stale_composition = {'maxCloudAlpha': 1, 'meanCloudAlpha': .2,
                     'cloudAuthority': {'revision': 1, 'state': 'eligible-published'}}
first = {'modelIsNull': True,
    'actualCloud': {'ready': False, 'coverage': [0, 0, 0], 'targets': [0, 0, 0],
                   'density': {'sum': 0, 'max': 0, 'nonzero': 0},
                   'raster': {'alphaSum': 0, 'alphaNonzero': 0}, 'publication': receipt},
    'effects': {'precip': 'off', 'lightning': 'off', 'rainOpacity': 0, 'displayedParticles': 0},
    'celestial': {'owner': 'refined', 'status': 'pending',
                  'consumedSolarMask': {'blockedAlphaSum': 255}, 'composition': stale_composition,
                  'activeCanvas': canvas, 'skyPending': False, 'frameAgeMs': 3000,
                  'moonReady': True, 'moonPresence': .02,
                  'visibleForegrounds': [{'owner': 'refined', 'status': 'pending',
                                          'canvas': canvas, 'composition': stale_composition}]}}
later = deepcopy(first)
clean_composition = {'maxCloudAlpha': 0, 'meanCloudAlpha': 0, 'cloudAuthority': receipt}
later['celestial'].update(status='ready', consumedSolarMask={'blockedAlphaSum': 0},
    composition=clean_composition, visibleForegrounds=[{'owner': 'refined', 'status': 'ready',
                                                      'canvas': canvas, 'composition': clean_composition}])
retain('HN4-original-stale-pending-then-ready', [first, later], {
    'oldFirstNativeCheck': actual_check(old_tree, 'firstResumeWithdrawsNativeMaterial', old, first_resume=first),
    'oldLaterReadyCheck': actual_check(old_tree, 'firstVisibleResumeHasNoStaleJoin', old, first_visible=later),
    'newFirstCheck': actual_check(new_tree, 'firstResumeWithdrawsNativeAndDisplayedMaterial', new, first_resume=first),
    'newWholePrefixCheck': actual_check(new_tree, 'everyVisibleResumeOpportunityHasNoStaleJoin', new, resume_states=[first, later])},
    {'oldFirstNativeCheck': True, 'oldLaterReadyCheck': True, 'newFirstCheck': False, 'newWholePrefixCheck': False})

clean_pending = deepcopy(later)
clean_pending['celestial']['status'] = clean_pending['celestial']['visibleForegrounds'][0]['status'] = 'pending'
retain('HN4-intervening-stale-not-erased', [clean_pending, first, later],
       {'newWholePrefixCheck': new['resume_visible_sequence']([clean_pending, first, later])},
       {'newWholePrefixCheck': False})
retain('HN4-clean-pending-ready-control', [clean_pending, later],
       {'newWholePrefixCheck': new['resume_visible_sequence']([clean_pending, later])},
       {'newWholePrefixCheck': True})

results['count'] = len(results['controls'])
results['allExpectedOutcomesMatched'] = True
(OUT / 'independent-counterexamples.json').write_text(json.dumps(results, indent=2, allow_nan=False) + '\n')
print(json.dumps({'controls': results['count'], 'allExpectedOutcomesMatched': True,
                  'output': str(OUT / 'independent-counterexamples.json')}, indent=2))
