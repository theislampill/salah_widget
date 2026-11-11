from pathlib import Path
import hashlib

target = Path('/workspace/scratch/15b8fb6ac4c2/r000b-work/tools/qa/run_r000b_withdrawal.py')
assert hashlib.sha256(target.read_bytes()).hexdigest() == '6f0669ced88030c2dd3b9db40520cf1b5aa68669e019cfc3623b0952494f0e7f'
text = target.read_text()

def replace(old, new):
    global text
    assert text.count(old) == 1, old[:100]
    text = text.replace(old, new)

replace('import argparse\n', '# R000B_HN2_HN3_HN4_NATIVE_ORACLES_V2\nimport argparse\n')
replace('''    artifacts = {}
    for name, value in media.items():''', '''    artifacts, decoded = {}, {}
    for name, value in media.items():''')
replace('''        artifacts[name] = {'file': path.name, 'sha256': sha(data), 'pixels': png_summary(data)}
    mask = state['celestial'].pop('solarMask')''', '''        artifacts[name] = {'file': path.name, 'sha256': sha(data), 'pixels': png_summary(data)}
        if name == 'native-cloud':
            decoded[name] = png_rgba(data)
    mask_image = None
    mask = state['celestial'].pop('solarMask')''')
replace('''        pixels = png_summary(data, inverse_alpha=True)
        mask_result.update''', '''        pixels = png_summary(data, inverse_alpha=True)
        mask_image = png_rgba(data)
        mask_result.update''')
replace('''    state['celestial']['consumedSolarMask'] = mask_result
    return artifacts''', '''    state['celestial']['consumedSolarMask'] = mask_result
    state['rainOriginEvidence'] = rain_origin_evidence(state, decoded.get('native-cloud'), mask_image)
    state['rainOriginEvidence']['artifacts'] = {'native': artifacts.get('native-cloud'), 'publishedMask': mask_result}
    return artifacts''')

HELPERS = r'''def _finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _bounds(value):
    return (isinstance(value, dict) and all(_finite_number(value.get(k)) for k in ('left', 'top', 'width', 'height'))
            and value['width'] > 0 and value['height'] > 0)


def _column_alpha_support(image, bounds, left, right, inverse=False):
    """Independently read an actual PNG column footprint, without density data."""
    width, height, rgba = image
    if width < 1 or height < 1 or len(rgba) != width * height * 4 or not _bounds(bounds):
        raise ValueError('Invalid actual raster geometry')
    first = max(0, min(width - 1, math.floor((left - bounds['left']) * width / bounds['width'])))
    last = max(0, min(width - 1, math.ceil((right - bounds['left']) * width / bounds['width']) - 1))
    values = [255 - rgba[(y * width + x) * 4 + 3] if inverse else rgba[(y * width + x) * 4 + 3]
              for y in range(height) for x in range(first, last + 1)]
    return {'firstColumn': first, 'lastColumn': last, 'alphaSum': sum(values),
            'alphaMax': max(values, default=0), 'nonzeroPixels': sum(v != 0 for v in values)}


def rain_origin_evidence(state, native_image, published_mask_image):
    """Bind the accepted column/origin contract to independent actual pixels.

    The CSS base is19% of the measured parent. The visible segment is measured
    separately and back-projected through its actual fall translation/slant.
    This does not demand an exact cloud contour at the invisible animation
    start. The primary alpha witness is the actually published, already
    blurred/masked cloud column. Native backing association allows3sigma of
    the declared0.55px blur plus half a backing pixel; no second blur halo is
    applied to the published mask. Pixel review remains separate.
    """
    shown = [p for p in state.get('effects', {}).get('particles', []) if p.get('displayed')]
    result = {'schema': 'r000b-rain-origin/v2', 'ok': False, 'particles': [],
              'contract': 'measured CSS base origin plus assigned visible cloud column; not an exact cloud contour at an invisible animation start',
              'coordinateToleranceCssPx': 0.75, 'supportAlphaThreshold': 0,
              'publishedSupport': 'exact inverse-alpha PNG already includes native scaling, blur and vertical mask'}
    if not shown:
        result['reason'] = 'No displayed particles to qualify'
        return result
    raster = state.get('actualCloud', {}).get('raster') or {}
    cloud = raster.get('bounds')
    foreground = (state.get('celestial', {}).get('activeCanvas') or {}).get('bounds')
    blur_match = re.fullmatch(r'blur\(([0-9.]+)px\)', raster.get('filter', ''))
    blur = float(blur_match[1]) if blur_match else 0 if raster.get('filter') == 'none' else None
    if native_image is None or published_mask_image is None or not _bounds(cloud) or not _bounds(foreground) or blur is None or abs(blur - 0.55) > 1e-9:
        result['reason'] = 'Missing actual PNG/layout evidence or changed declared blur'
        return result
    tolerance = result['coordinateToleranceCssPx']
    aligned = all(abs(cloud[k] - foreground[k]) <= tolerance for k in ('left', 'top', 'width', 'height'))
    slant_text = state['effects'].get('rainSlant', '').strip()
    slant = float(slant_text[:-2]) if re.fullmatch(r'-?[0-9.]+px', slant_text) else None
    for particle in shown:
        errors = []
        geometry = particle.get('originGeometry') or {}
        position, parent, matrix, base = (geometry.get(k) for k in ('position', 'parent', 'transform', 'baseOrigin'))
        observation = {'index': particle.get('index'), 'baseOrigin': base, 'visibleSegment': particle.get('rect'),
                       'visibleSegmentOpacity': particle.get('opacity'), 'animation': particle.get('animation'), 'errors': errors}
        result['particles'].append(observation)
        complete = (isinstance(position, dict) and all(_finite_number(position.get(k)) for k in ('left', 'top', 'width', 'height'))
                    and isinstance(parent, dict) and _bounds(parent.get('bounds'))
                    and all(_finite_number(parent.get(k)) for k in ('clientLeft', 'clientTop', 'clientWidth', 'clientHeight', 'offsetWidth', 'offsetHeight'))
                    and isinstance(matrix, dict) and all(_finite_number(matrix.get(k)) for k in ('a', 'b', 'c', 'd', 'e', 'f'))
                    and _bounds(base) and _bounds(particle.get('rect')) and _finite_number(particle.get('leftPercent')))
        if not complete:
            errors.append('Incomplete measured origin/parent/transform evidence')
            continue
        pb, rect = parent['bounds'], particle['rect']
        if particle.get('kind') != 'rain' or position['width'] <= 0 or position['height'] <= 0:
            errors.append('Unsupported displayed particle')
        if not aligned or any(abs(pb[k] - parent['offset' + k.title()]) > tolerance for k in ('width', 'height')):
            errors.append('Changed full-card parent/cloud/foreground geometry')
        expected_cloud = {'left': pb['left'] + parent['clientLeft'], 'top': pb['top'] + parent['clientTop'],
                          'width': parent['clientWidth'], 'height': parent['clientHeight']}
        if any(abs(cloud[k] - expected_cloud[k]) > tolerance for k in expected_cloud):
            errors.append('Cloud is not registered to the measured parent padding box')
        if abs(position['top'] - 0.19 * parent['clientHeight']) > tolerance:
            errors.append('Declared19% CSS base origin displaced')
        if abs(position['left'] - particle['leftPercent'] / 100 * parent['clientWidth']) > tolerance:
            errors.append('Source percentage does not match resolved untransformed left')
        expected_base = {'left': expected_cloud['left'] + position['left'], 'top': expected_cloud['top'] + position['top'],
                         'width': position['width'], 'height': position['height']}
        if any(abs(base[k] - expected_base[k]) > tolerance for k in expected_base):
            errors.append('Base origin is not the measured parent plus resolved position')
        if not (cloud['left'] <= base['left'] < base['left'] + base['width'] <= cloud['left'] + cloud['width']
                and cloud['top'] <= base['top'] <= cloud['top'] + cloud['height']):
            errors.append('Origin outside measured cloud bounds')
        if matrix.get('is2D') is not True or any(abs(matrix[k] - expected) > 1e-9 for k, expected in [('a', 1), ('b', 0), ('c', 0), ('d', 1)]):
            errors.append('Unsupported nontranslation transform')
        if any(abs(rect[k] - expected) > tolerance for k, expected in [('left', base['left'] + matrix['e']),
                ('top', base['top'] + matrix['f']), ('width', base['width']), ('height', base['height'])]):
            errors.append('Visible segment does not match base plus actual translation')
        if particle.get('animation') == 'none':
            if abs(matrix['e']) > 1e-9 or abs(matrix['f']) > 1e-9:
                errors.append('Reduced/no-animation segment is not held at its CSS base')
        elif particle.get('animation') == 'fall' and slant is not None:
            fraction = (matrix['f'] + 10) / 142
            observation['fallFraction'] = fraction
            if not -tolerance / 142 <= fraction <= 1 + tolerance / 142 or abs(matrix['e'] - fraction * slant) > tolerance:
                errors.append('Visible fall segment contradicts the declared slant path')
        else:
            errors.append('Unsupported rain animation/slant')
        # Primary witness is the exact displayed mask. Its blur is already in
        # the pixels, so only half an output pixel handles raster coordinates.
        output_half_pixel = foreground['width'] / published_mask_image[0] / 2
        native_allowance = 3 * blur + cloud['width'] / native_image[0] / 2
        observation['publishedCoordinateAllowanceCssPx'] = output_half_pixel
        observation['nativeAssociationAllowanceCssPx'] = native_allowance
        observation['nativeSupport'] = _column_alpha_support(native_image, cloud,
            base['left'] - native_allowance, base['left'] + base['width'] + native_allowance)
        observation['publishedSupport'] = _column_alpha_support(published_mask_image, foreground,
            base['left'] - output_half_pixel, base['left'] + base['width'] + output_half_pixel, inverse=True)
        if observation['nativeSupport']['alphaSum'] <= 0:
            errors.append('No independently read native cloud alpha near the assigned source column')
        if observation['publishedSupport']['alphaSum'] <= 0:
            errors.append('No actually published masked cloud alpha in the assigned source column')
    result['ok'] = bool(result['particles']) and all(not p['errors'] for p in result['particles'])
    return result


def rain_origin(state):
    evidence = state.get('rainOriginEvidence') or {}
    return evidence.get('schema') == 'r000b-rain-origin/v2' and evidence.get('ok') is True


def observed_sky_error_fields(state):
    """Missing diagnostics are explicitly unobserved, never an empty list."""
    sky = state.get('celestial') or {}
    fields = []
    for owner, name in [('refined', 'errors'), ('preview', 'catalogueError')]:
        value = sky.get(owner)
        observed = isinstance(value, dict) and name in value
        fields.append({'owner': owner, 'field': name, 'observed': observed,
                       'value': value[name] if observed else None,
                       'coverage': 'observed' if observed else 'not-published/uninspected'})
    return fields


def all_visible_joins_empty(state):
    """Check displayed pixels regardless of ready/pending diagnostic status."""
    sky = state.get('celestial') or {}
    layers = sky.get('visibleForegrounds')
    if not isinstance(layers, list):
        return False
    receipt = state.get('actualCloud', {}).get('publication')
    for layer in layers:
        canvas, composition = layer.get('canvas') or {}, layer.get('composition') or {}
        if not (canvas.get('visibility') == 'visible' and canvas.get('display') != 'none'
                and _finite_number(canvas.get('opacity')) and canvas['opacity'] > 0 and _bounds(canvas.get('bounds'))):
            return False
        if not (sky.get('consumedSolarMask', {}).get('blockedAlphaSum') == 0
                and composition.get('maxCloudAlpha') == 0 and composition.get('meanCloudAlpha') == 0
                and receipt is not None and receipt.get('state') == 'withdrawn-unavailable'
                and composition.get('cloudAuthority') == receipt):
            return False
    return True


def resume_visible_sequence(states):
    """Every retained visible opportunity must pass; later ready cannot erase one."""
    return (bool(states) and any(s.get('celestial', {}).get('visibleForegrounds') for s in states)
            and all(actual_empty(s) and effects_off(s) and s['modelIsNull'] and all_visible_joins_empty(s) for s in states))


def cloud_motion_continuity(samples, mode, visibility_changes=()):
    """Signed/bounded axes for the fixture's fixed225deg/2mps admitted wind.

    Actual native elapsed integration timestamps own each bound. Declared
    hidden intervals are removed using passive post-visibility native receipts.
    Reduced and fully hidden samples must hold every accumulated axis exactly.
    No unsigned0.03 floor can conceal a backwards reset.
    """
    phase_period, noise_period = 1.25, 4294967296
    wind_x = -math.sin(math.radians(225))
    cloud_speed = 0.06 + 0.6 * ((2 - 0.5) / (14 - 0.5))
    phase_rates = [wind_x * cloud_speed * (0.024 + i * 0.006) for i in range(3)]
    life_rates = [0.018 + i * 0.004 for i in range(3)]
    result = {'schema': 'r000b-motion-continuity/v2', 'ok': False, 'steps': 0, 'violations': [],
              'phaseDirection': 'decreasing modulo1.25 for declared225deg wind', 'phaseRatesPerSecond': phase_rates,
              'lifeRatesPerSecond': life_rates, 'wanderRatePerSecond': 0.011,
              'phaseNumericalTolerance': 1e-9, 'noiseNumericalTolerance': 1e-5, 'hiddenIntervalsElapsedMs': []}
    violations = result['violations']
    hidden_start = None
    for event in visibility_changes:
        motion = event.get('nativeMotionAfter') or {}
        at = motion.get('elapsedRtMs')
        if not _finite_number(at):
            violations.append({'reason': 'Visibility boundary lacks an actual native elapsed receipt'})
            continue
        if event.get('hidden') is True and hidden_start is None:
            hidden_start = at
        elif event.get('hidden') is False and hidden_start is not None and at >= hidden_start:
            result['hiddenIntervalsElapsedMs'].append([hidden_start, at]); hidden_start = None
        else:
            violations.append({'reason': 'Malformed visibility interval'})
    if hidden_start is not None:
        violations.append({'reason': 'Hidden interval never resumed'})
    if len(samples) < 2:
        violations.append({'reason': 'Insufficient continuity samples'})
        return result
    first = samples[0].get('motion') or {}
    for index, sample in enumerate(samples):
        motion = sample.get('motion') or {}
        if any(motion.get(k) != first.get(k) for k in ('key', 'population', 'fieldSeed')):
            violations.append({'sample': index, 'reason': 'Population/seed/key changed'})
        wind = motion.get('wind') or {}
        if not (_finite_number(wind.get('wx')) and _finite_number(wind.get('wspd'))
                and abs(wind['wx'] - wind_x) <= 1e-12 and abs(wind['wspd'] - cloud_speed) <= 1e-12):
            violations.append({'sample': index, 'reason': 'Declared fixed cloud velocity changed/unobserved'})
        if motion.get('reduced') is not (mode == 'reduced'):
            violations.append({'sample': index, 'reason': 'Reduced-motion state differs from declared mode'})
        values = [*(motion.get('phase') or []), *(motion.get('life') or []), motion.get('wander'), motion.get('elapsedRtMs')]
        if len(values) != 8 or not all(_finite_number(v) for v in values):
            violations.append({'sample': index, 'reason': 'Missing/nonfinite actual motion axes'})
    if violations:
        return result
    for index, (a, b) in enumerate(zip(samples, samples[1:])):
        ma, mb = a['motion'], b['motion']; left, right = ma['elapsedRtMs'], mb['elapsedRtMs']
        result['steps'] += 1
        if right < left:
            violations.append({'step': index, 'reason': 'Native integration timestamp moved backwards'})
            continue
        active_ms = right - left
        for start, end in result['hiddenIntervalsElapsedMs']:
            active_ms -= max(0, min(right, end) - max(left, start))
        active_seconds = max(0, active_ms) / 1000
        held = mode == 'reduced' or ma.get('paused') is True and mb.get('paused') is True
        if held:
            if ma['phase'] != mb['phase'] or ma['life'] != mb['life'] or ma['wander'] != mb['wander']:
                violations.append({'step': index, 'reason': 'Hidden/reduced accumulated axes moved'})
            continue
        for axis, (before, after, rate) in enumerate(zip(ma['phase'], mb['phase'], phase_rates)):
            delta = (after - before + phase_period / 2) % phase_period - phase_period / 2
            if delta > 1e-9 or -delta > rate * active_seconds + 1e-9:
                violations.append({'step': index, 'axis': 'phase' + str(axis), 'delta': delta,
                                   'maximumForwardDistance': rate * active_seconds, 'reason': 'Wrong direction or excessive phase step'})
        for axis, (before, after, rate) in enumerate(zip(ma['life'], mb['life'], life_rates)):
            delta = (after - before) % noise_period
            if delta > rate * active_seconds + 1e-5:
                violations.append({'step': index, 'axis': 'life' + str(axis), 'delta': delta,
                                   'maximumForwardDistance': rate * active_seconds, 'reason': 'Lifecycle reset/backwards/excessive step'})
        wander_delta = (mb['wander'] - ma['wander']) % noise_period
        if wander_delta > 0.011 * active_seconds + 1e-5:
            violations.append({'step': index, 'axis': 'wander', 'delta': wander_delta,
                               'maximumForwardDistance': 0.011 * active_seconds, 'reason': 'Wander reset/backwards/excessive step'})
    result['ok'] = not violations
    return result
'''
replace('''def rain_origin(state):
    effects = state['effects']
    shown = [p for p in effects['particles'] if p['displayed']]
    return (effects['cloudGateActive'] and bool(shown)
            and all(p['kind'] == 'rain' and p['normalizedDensity'] is not None
                    and p['normalizedDensity'] > 0.16 for p in shown))
''', HELPERS)

replace('''            wait(page, "() => {const f=__withdrawalFixture;if(f.state==='error')throw Error(f.error);return !!f.resumeFirstVisible;}", 6000)
            fixture_resume = page.evaluate('() => ({first:__withdrawalFixture.resumeFirstRaf,visible:__withdrawalFixture.resumeFirstVisible,observation:__withdrawalFixture.resumeObservation})')
            first_resume = record_state('resume-first-raf', fixture_resume['first'], screenshot=False)
            first_visible = record_state('resume-first-visible-publication', fixture_resume['visible'], screenshot=False)
            row['resumeObservation'] = fixture_resume['observation']
            row['checks']['firstResumeWithdrawsNativeMaterial'] = actual_empty(first_resume) and effects_off(first_resume) and first_resume['modelIsNull']
            row['checks']['firstVisibleResumeHasNoStaleJoin'] = actual_empty(first_visible) and joined_empty(first_visible) and independent_celestial(first_visible)
            row['checks']['resumeDoesNotReplayHiddenMotion'] = max(phase_progress(paused['actualCloud']['motion'], first_resume['actualCloud']['motion'])) < 0.002
            expired = capture('resumed-expired')''',
'''            wait(page, "() => {const f=__withdrawalFixture;if(f.state==='error')throw Error(f.error);return f.resumeObservation?.complete===true;}", 6000)
            fixture_resume = page.evaluate('() => ({opportunities:__withdrawalFixture.resumeOpportunities,observation:__withdrawalFixture.resumeObservation,visibility:__withdrawalFixture.visibility})')
            resume_states, resume_files = [], []
            for opportunity in fixture_resume['opportunities']:
                if opportunity['state'] is not None:
                    stage = 'resume-opportunity-' + str(opportunity['frame']).zfill(3)
                    observed_state = record_state(stage, opportunity['state'], screenshot=False)
                    resume_states.append(observed_state)
                    resume_files.append({'frame': opportunity['frame'], 'visible': opportunity['visible'], 'file': stage + '.json'})
                else:
                    resume_files.append({'frame': opportunity['frame'], 'visible': False, 'state': 'No displayed foreground at this observed opportunity'})
            first_resume = resume_states[0]
            visible_states = [state for state in resume_states if state['celestial']['visibleForegrounds']]
            first_visible, ready_resume = visible_states[0], resume_states[-1]
            row['resumeObservation'] = {**fixture_resume['observation'], 'opportunities': resume_files}
            row['checks']['firstResumeWithdrawsNativeAndDisplayedMaterial'] = (actual_empty(first_resume) and effects_off(first_resume)
                and first_resume['modelIsNull'] and all_visible_joins_empty(first_resume))
            row['checks']['everyVisibleResumeOpportunityHasNoStaleJoin'] = resume_visible_sequence(resume_states)
            row['checks']['separateReadyResumeRecovery'] = independent_celestial(ready_resume) and all_visible_joins_empty(ready_resume)
            resume_motion = [{'elapsedMs': paused['elapsedMs'], 'motion': paused['actualCloud']['motion']},
                             {'elapsedMs': first_resume['elapsedMs'], 'motion': first_resume['actualCloud']['motion']}]
            row['resumeMotionEvidence'] = cloud_motion_continuity(resume_motion, args.mode, fixture_resume['visibility']['changes'])
            row['checks']['resumeDoesNotReplayHiddenMotion'] = row['resumeMotionEvidence']['ok']
            expired = capture('resumed-expired')''')
replace('''        for key in ('resumeFirstRaf', 'resumeFirstVisible'):
            if key in fixture:
                fixture[key] = {'savedAs': 'resume-first-raf.json' if key == 'resumeFirstRaf' else 'resume-first-visible-publication.json'}''',
'''        for key in ('resumeFirstRaf', 'resumeFirstVisible', 'resumeReady'):
            if key in fixture:
                fixture[key] = {'savedIn': 'resumeObservation.opportunities; first/visible/ready are separately identified by actual visibility and status'}
        for opportunity in fixture.get('resumeOpportunities', []):
            if opportunity.get('state') is not None:
                opportunity['state'] = {'savedAs': 'resume-opportunity-' + str(opportunity['frame']).zfill(3) + '.json'}''')
replace('''        row['checks']['noNativeRendererErrors'] = all(not (s['celestial'].get('refined') or {}).get('errors')
            and not (s['celestial'].get('preview') or {}).get('catalogueError')
            and not (s['celestial'].get('moonRuntime') or {}).get('errors') for s in observed)''',
'''        row['observedSkyDiagnosticFields'] = [{'stage': o['stage'], 'fields': observed_sky_error_fields(o['state'])} for o in row['observations']]
        inspected_error_fields = [field for record in row['observedSkyDiagnosticFields'] for field in record['fields'] if field['observed']]
        row['checks']['noErrorsInObservedSkyDiagnosticFields'] = bool(inspected_error_fields) and all(not field['value'] for field in inspected_error_fields)
        row['uninspectedDiagnostics'] = ['Handled Moon worker diagnostic errors: effectful Moon runtime state/surface/presentation getters are deliberately not read; DOM and pixel evidence is retained instead.']''')
replace('''        row['checks']['boundedPhaseSteps'] = all(max(phase_progress(a['motion'], b['motion']), default=0) <= max(0.03, (b['elapsedMs'] - a['elapsedMs']) / 1000 * 0.05)
                                                     for a, b in zip(trace, trace[1:]))''',
'''        motion_samples = [{'elapsedMs': state['elapsedMs'], 'motion': state['actualCloud']['motion']} for state in observed]
        motion_samples += [{'elapsedMs': state['elapsedMs'], 'motion': state['motion']} for state in trace]
        visibility_changes = fixture.get('visibility', {}).get('changes', [])
        motion_samples += [{'elapsedMs': event['elapsedAfterDispatchMs'], 'motion': event['nativeMotionAfter']} for event in visibility_changes]
        motion_samples.sort(key=lambda sample: sample['elapsedMs'])
        row['motionContinuityEvidence'] = cloud_motion_continuity(motion_samples, args.mode, visibility_changes)
        row['checks']['signedPhaseLifeWanderContinuity'] = row['motionContinuityEvidence']['ok']''')
target.write_text(text)
print(hashlib.sha256(target.read_bytes()).hexdigest(), target)
