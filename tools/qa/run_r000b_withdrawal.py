"""Bounded R000B native midnight/no-timetable withdrawal evidence.

The served product bodies are unchanged. A private fixture supplies synthetic
Responses and one initial Date epoch offset; subsequent elapsed time is native
1x. Only read-only owner/pixel observations occur during the run. Optional hidden
expiry uses an explicitly labelled document visibility property/event seam, not
OS sleep/wake. No product acquisition, render, install, painter, reconciliation,
foreground-capture, or lunar-surface helper is called by this driver.

Exit 0 means the selected assertion contract was demonstrated, with pixel review
still pending. baseline-defect can exit 0 only for the actual retained-cloud
defect plus healthy controls, and never receives a product-success status.
"""

# R000B_HN2_HN3_HN4_NATIVE_ORACLES_V2
# R000B_F01_HEALTHY_REFRESH_EXTENSION_V1
# R000B_HR1_HR2_INTERFACE_REPAIR_V1
import argparse
import base64
import datetime
import hashlib
import http.server
import json
import math
import os
from pathlib import Path
import re
import struct
import sys
import threading
import time
import traceback
import uuid
from urllib.parse import unquote, urlencode, urlsplit
import zlib

from run_r000c_native import dump, sha, wait


READ = "() => __withdrawalRead.read(__withdrawalRead.identity())"
FIXTURE = "() => window.__withdrawalFixture"
LATEST = """() => {
  const f=window.__withdrawalFixture;
  if(f?.state==='error')throw Error(f.error);
  return f?.state==='ready'?f.latest:null;
}"""
HEALTHY_REFRESH_PROGRESS = """() => {
  const f=window.__withdrawalFixture;
  if(f?.state==='error')throw Error(f.error);
  if(f?.state!=='ready')throw Error('Expected the existing ready fixture');
  return {elapsedMs:performance.now()-f.started,maxElapsedMs:f.maxElapsedMs,
          clockOrigin:{started:f.started,startUtc:f.startUtc},
          latest:f.latest,ledger:f.ledger.filter(request=>request.kind==='weather')};
}"""
EXPECTED_COVERAGE = [0.92, 0.90, 0.60]
INITIAL_SOURCE_UTC = 1788900300000  # 2026-09-08 20:45:00Z = 23:45 Asia/Riyadh


def identities(root, paths):
    return {name: {'bytes': (root / name).stat().st_size,
                   'sha256': sha((root / name).read_bytes())}
            for name in paths}


def script_identities(data):
    source = data.decode('utf-8')
    return [{'index': i, 'attributes': match[1], 'sha256': sha(match[2].encode()),
             'characters': len(match[2].encode('utf-16-le')) // 2}
            for i, match in enumerate(re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script>', source, re.I))]


def png_rgba(data):
    """Read browser-generated 8-bit RGB/RGBA PNGs without an extra dependency.

    This is solely artifact readback. It never supplies product image pixels.
    Reject unsupported/interlaced formats instead of manufacturing a metric.
    """
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Artifact is not a PNG')
    offset, payload, header = 8, bytearray(), None
    while offset < len(data):
        size = struct.unpack('!I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        value = data[offset + 8:offset + 8 + size]
        crc = struct.unpack('!I', data[offset + 8 + size:offset + 12 + size])[0]
        if zlib.crc32(kind + value) & 0xffffffff != crc:
            raise ValueError('PNG CRC mismatch')
        if kind == b'IHDR':
            header = struct.unpack('!2I5B', value)
        elif kind == b'IDAT':
            payload.extend(value)
        offset += size + 12
        if kind == b'IEND':
            break
    if header is None:
        raise ValueError('PNG lacks IHDR')
    width, height, depth, colour, compression, filtering, interlace = header
    if depth != 8 or colour not in (2, 6) or compression or filtering or interlace:
        raise ValueError('Unsupported browser PNG format: ' + repr(header))
    channels = 4 if colour == 6 else 3
    stride = width * channels
    raw = zlib.decompress(payload)
    if len(raw) != height * (stride + 1):
        raise ValueError('PNG decoded length mismatch')
    previous = bytearray(stride)
    rgba = bytearray(width * height * 4)

    def paeth(a, b, c):
        p = a + b - c
        pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
        return a if pa <= pb and pa <= pc else b if pb <= pc else c

    for y in range(height):
        at = y * (stride + 1)
        method = raw[at]
        row = bytearray(raw[at + 1:at + stride + 1])
        if method > 4:
            raise ValueError('Invalid PNG filter')
        for x in range(stride):
            a = row[x - channels] if x >= channels else 0
            b = previous[x]
            c = previous[x - channels] if x >= channels else 0
            predictor = 0 if method == 0 else a if method == 1 else b if method == 2 else (a + b) // 2 if method == 3 else paeth(a, b, c)
            row[x] = (row[x] + predictor) & 255
        if channels == 4:
            rgba[y * width * 4:(y + 1) * width * 4] = row
        else:
            for x in range(width):
                p = (y * width + x) * 4
                rgba[p:p + 4] = row[x * 3:x * 3 + 3] + b'\xff'
        previous = row
    return width, height, bytes(rgba)


def png_summary(data, inverse_alpha=False):
    width, height, pixels = png_rgba(data)
    values = [255 - a if inverse_alpha else a for a in pixels[3::4]]
    return {'width': width, 'height': height, 'alphaSum': sum(values),
            'alphaMax': max(values, default=0), 'alphaNonzero': sum(a != 0 for a in values),
            'meanAlpha': sum(values) / (255 * width * height)}


def decode_png_url(value):
    prefix = 'data:image/png;base64,'
    if not value.startswith(prefix):
        raise ValueError('Canvas did not produce a PNG data URL')
    return base64.b64decode(value[len(prefix):], validate=True)


def retain_media(out, stage, state):
    media = state.pop('media')
    artifacts, decoded = {}, {}
    for name, value in media.items():
        data = decode_png_url(value)
        path = out / f'{stage}-{name}.png'
        path.write_bytes(data)
        artifacts[name] = {'file': path.name, 'sha256': sha(data), 'pixels': png_summary(data)}
        if name == 'native-cloud':
            decoded[name] = png_rgba(data)
    mask_image = None
    mask = state['celestial'].pop('solarMask')
    mask_path = out / f'{stage}-consumed-solar-mask.txt'
    mask_path.write_text(mask + '\n', encoding='utf-8')
    mask_result = {'sourceFile': mask_path.name, 'sourceSha256': sha((mask + '\n').encode())}
    compact = re.sub(r'\s+', '', mask)
    if compact == 'linear-gradient(#fff,#fff)':
        mask_result.update(kind='opaque-clear-gradient', blockedAlphaSum=0, blockedAlphaMax=0,
                           blockedAlphaNonzero=0)
    elif re.fullmatch(r'url\(["\']?(data:image/png;base64,[A-Za-z0-9+/=]+)["\']?\)', mask):
        encoded = re.fullmatch(r'url\(["\']?(data:image/png;base64,[A-Za-z0-9+/=]+)["\']?\)', mask)[1]
        data = decode_png_url(encoded)
        path = out / f'{stage}-consumed-solar-mask.png'
        path.write_bytes(data)
        pixels = png_summary(data, inverse_alpha=True)
        mask_image = png_rgba(data)
        mask_result.update(kind='published-inverse-cloud-alpha-png', file=path.name, sha256=sha(data),
                           width=pixels['width'], height=pixels['height'],
                           blockedAlphaSum=pixels['alphaSum'], blockedAlphaMax=pixels['alphaMax'],
                           blockedAlphaNonzero=pixels['alphaNonzero'], meanBlockedAlpha=pixels['meanAlpha'])
    elif not mask:
        mask_result.update(kind='absent', blockedAlphaSum=None, blockedAlphaMax=None,
                           blockedAlphaNonzero=None)
    else:
        raise ValueError('Unreviewed consumed solar mask encoding')
    state['celestial']['consumedSolarMask'] = mask_result
    state['rainOriginEvidence'] = rain_origin_evidence(state, decoded.get('native-cloud'), mask_image)
    state['rainOriginEvidence']['artifacts'] = {'native': artifacts.get('native-cloud'), 'publishedMask': mask_result}
    return artifacts


def actual_empty(state):
    cloud = state['actualCloud']
    return (cloud['ready'] is False and cloud['coverage'] == [0, 0, 0]
            and cloud['targets'] == [0, 0, 0] and cloud['density']['sum'] == 0
            and cloud['density']['max'] == 0 and cloud['density']['nonzero'] == 0
            and cloud['raster']['alphaSum'] == 0 and cloud['raster']['alphaNonzero'] == 0)


def joined_empty(state, require_new_diagnostics=True):
    sky = state['celestial']
    composition = sky.get('composition') or {}
    receipt = composition.get('cloudAuthority')
    return (sky['owner'] in ('preview', 'refined')
            and sky['consumedSolarMask']['blockedAlphaSum'] == 0
            and (not require_new_diagnostics or
                 composition.get('maxCloudAlpha') == 0 and composition.get('meanCloudAlpha') == 0
                 and receipt is not None and receipt.get('state') == 'withdrawn-unavailable'
                 and receipt == state['actualCloud']['publication']))


def healthy_cloud(state):
    cloud = state['actualCloud']
    return (cloud['ready'] and all(abs(a - b) < 1e-9 for a, b in zip(cloud['coverage'], EXPECTED_COVERAGE))
            and cloud['density']['max'] >= 2 and cloud['density']['nonzero'] > 0
            and cloud['raster']['alphaSum'] > 0 and cloud['raster']['alphaNonzero'] > 0
            and state['celestial']['consumedSolarMask']['blockedAlphaSum'] is not None
            and state['celestial']['consumedSolarMask']['blockedAlphaSum'] > 0)


def unknown_weather(state):
    header = state['lastWeatherHeader'] or {}
    return (state['header']['temperature'] == '' and state['header']['icon'] == '—'
            and 'unavailable' in state['header']['label'].lower()
            and header.get('conditionState') == 'unavailable'
            and header.get('code') is None and header.get('rawCode') is None
            and header.get('observedPresent') is False
            and state['effects']['fx'] == 'unavailable')


def effects_off(state):
    effects = state['effects']
    return (effects['precip'] == 'off' and effects['lightning'] == 'off'
            and effects['rainOpacity'] == 0 and effects['displayedParticles'] == 0)


def independent_celestial(state):
    sky = state['celestial']
    canvas = sky.get('activeCanvas') or {}
    return (sky['owner'] in ('preview', 'refined') and sky['status'] == 'ready'
            and sky['skyPending'] is False and sky['frameAgeMs'] is not None
            and 0 <= sky['frameAgeMs'] <= 30000 and canvas.get('visibility') == 'visible'
            and canvas.get('display') != 'none' and canvas.get('rgbNonzero', 0) > 0
            and canvas.get('maxRGB', 0) > canvas.get('minRGB', 0)
            and sky['moonReady'] is True and sky['moonPresence'] > 0)


def _finite_number(value):
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


def _healthy_refresh_target_projection(target):
    """Match the product receipt's generation/lat/lon identity projection."""
    if not isinstance(target, dict) or not all(_finite_number(target.get(key)) for key in ('generation', 'lat', 'lon')):
        return None
    return {key: target[key] for key in ('generation', 'lat', 'lon')}


def _healthy_refresh_clock(captured, origin):
    """Bind the observed fixture origins to an existing native motion sample."""
    if not isinstance(origin, dict):
        return None
    started, start_utc = origin.get('started'), origin.get('startUtc')
    motion = captured.get('actualCloud', {}).get('motion') or {}
    values = [started, start_utc, captured.get('elapsedMs'), captured.get('wallUtcMs'),
              motion.get('lastRt'), motion.get('elapsedRtMs')]
    if not all(_finite_number(value) for value in values):
        return None
    # Only an equality-of-origin floating-point allowance; this never extends an
    # attempt deadline. The epoch is checked against the already declared case.
    residual = motion['lastRt'] - motion['elapsedRtMs'] - started
    if not (started >= 0 and start_utc == INITIAL_SOURCE_UTC + 890000
            and 0 <= motion['elapsedRtMs'] <= captured['elapsedMs']
            and abs(residual) <= 1e-7
            and captured['wallUtcMs'] == math.floor(captured['wallUtcMs'])
            and captured['wallUtcMs'] >= start_utc + math.floor(captured['elapsedMs'])):
        return None
    return {'started': started, 'startUtc': start_utc, 'motionOriginResidualMs': residual}


def healthy_refresh_record(state):
    """Identity of a full capture whose native publication consumes its record."""
    cloud, raw = state.get('actualCloud') or {}, state.get('raw') or {}
    receipt, candidate = cloud.get('publication') or {}, state.get('candidate') or {}
    target = state.get('target')
    projection = _healthy_refresh_target_projection(target)
    source, retrieved = raw.get('currentValidAt'), raw.get('retrievedAt')
    if not (state.get('modelIsNull') is False and state.get('selected') is True
            and _finite_number(source) and _finite_number(retrieved)
            and receipt.get('state') == 'eligible-published' and receipt.get('lane') == 'live'
            and projection is not None and receipt.get('target') == projection
            and target == raw.get('target')
            and receipt.get('conditionState') == 'model-estimated-rain'
            and receipt.get('sourceValidAt') == source and receipt.get('retrievedAt') == retrieved
            and candidate.get('eligible') is True and candidate.get('sourceValidAt') == source
            and candidate.get('retrievedAt') == retrieved
            and _finite_number(receipt.get('revision')) and isinstance(target, dict) and _finite_number(target.get('generation'))
            and target.get('generation') == state.get('runtimeGeneration')):
        return None
    return {'sourceValidAt': source, 'retrievedAt': retrieved, 'target': target,
            'lane': receipt['lane'], 'publication': receipt}


def _healthy_refresh_request(record, captured, ledger, clock=None):
    """Bind a consumed response in its observed epoch and monotonic domains."""
    origin = _healthy_refresh_clock(captured, clock)
    if origin is None or not isinstance(record, dict) or _healthy_refresh_target_projection(record.get('target')) is None:
        return None
    started, start_utc = origin['started'], origin['startUtc']
    retrieved = record.get('retrievedAt')
    if not _finite_number(retrieved) or retrieved != math.floor(retrieved) or retrieved < start_utc:
        return None
    # Date.now() is startUtc+floor(performance.now()-started). Subtract the
    # integer epochs first, preserving the observed fractional monotonic origin.
    receipt_lower = started + (retrieved - start_utc)
    receipt_upper = receipt_lower + 1
    matches = []
    for request in ledger:
        if not isinstance(request, dict) or request.get('kind') != 'weather':
            continue
        owner, body = request.get('nativeOwner') or {}, request.get('inputBody') or {}
        current = body.get('current') or {}
        try:
            value = current.get('time')
            if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', value):
                continue
            source = int(datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M').replace(
                tzinfo=datetime.timezone(datetime.timedelta(hours=3))).timestamp() * 1000)
        except (ValueError, OverflowError):
            continue
        numbers = [request.get('elapsedMs'), request.get('wallUtcMs'), request.get('jsonElapsedMs'),
                   owner.get('deadlineAt'), request.get('weatherOrdinal')]
        if not all(_finite_number(value) for value in numbers):
            continue
        request_native = started + request['elapsedMs']
        json_native = started + request['jsonElapsedMs']
        deadline = owner['deadlineAt']
        json_wall_lower = start_utc + math.floor(request['jsonElapsedMs'])
        if (request.get('status') == 200 and request.get('jsonReads') == 1 and request.get('jsonSettled') is True
                and request.get('result') == 'json-consumed' and body.get('timezone') == 'Asia/Riyadh'
                and current.get('interval') == 900 and source == record['sourceValidAt']
                and owner.get('operationId') is not None and owner.get('attemptId') is not None
                and owner.get('generation') == record['target']['generation']
                and 0 <= request['elapsedMs'] <= request['jsonElapsedMs'] <= captured['elapsedMs']
                and start_utc + math.floor(request['elapsedMs']) <= request['wallUtcMs'] <= retrieved
                and json_wall_lower <= retrieved <= captured['wallUtcMs']
                # beginAttempt precedes this fixture request and the frozen
                # weather owner gives it a 10000 ms budget. Epoch-shaped or
                # unrelated deadlines cannot be silently accepted as monotonic.
                and request_native < deadline <= request_native + 10000 + 1e-7
                and json_native < deadline and receipt_upper < deadline):
            matches.append({'weatherOrdinal': request['weatherOrdinal'], 'elapsedMs': request['elapsedMs'],
                'wallUtcMs': request['wallUtcMs'], 'jsonElapsedMs': request['jsonElapsedMs'],
                'status': request['status'], 'jsonReads': request['jsonReads'], 'jsonSettled': request['jsonSettled'],
                'result': request['result'], 'inputSourceTime': current['time'], 'inputSourceUtc': source,
                'nativeOwner': owner, 'clockOrigin': origin,
                'timing': {'requestPerformanceMs': request_native, 'jsonPerformanceMs': json_native,
                    'retrievalPerformanceInterval': [receipt_lower, receipt_upper], 'intervalUpperExclusive': True,
                    'deadlinePerformanceMs': deadline, 'deadlineMarginFromReceiptUpperMs': deadline - receipt_upper,
                    'conservatism': 'The entire one-millisecond integer receipt interval must finish strictly before the native deadline; a valid receipt in the final millisecond can therefore be refused.'}})
    return matches[0] if len(matches) == 1 else None


def _healthy_refresh_receipt(receipt, wall, receipts):
    """A may stay active while B is a candidate; A must keep its own lease."""
    return (isinstance(receipt, dict) and receipt in receipts and _finite_number(wall)
            and receipt.get('state') == 'eligible-published' and receipt.get('lane') == 'live'
            and receipt.get('conditionState') == 'model-estimated-rain'
            and all(_finite_number(receipt.get(key)) and 0 <= wall - receipt[key] <= 900000
                    for key in ('sourceValidAt', 'retrievedAt')))


def _healthy_refresh_sample(state, receipts, full=False):
    """Check every retained sample using exactly the fields that it observes."""
    candidate, coverage = state.get('candidate') or {}, state.get('coverage')
    known_records = [(receipt.get('sourceValidAt'), receipt.get('retrievedAt')) for receipt in receipts]
    if not (state.get('modelIsNull') is False and state.get('loopStarted') is True
            and state.get('cloudReady') is True and isinstance(coverage, list) and len(coverage) == 3
            and all(_finite_number(a) and abs(a - b) < 1e-9 for a, b in zip(coverage, EXPECTED_COVERAGE))
            and state.get('documentHidden') is False and state.get('cardPaused') is False
            and candidate.get('eligible') is True
            and (candidate.get('sourceValidAt'), candidate.get('retrievedAt')) in known_records
            and _healthy_refresh_receipt(state.get('publication'), state.get('wallUtcMs'), receipts)
            and state.get('foregroundOwner') in ('preview', 'refined')
            and state.get('foregroundVisible') is True and state.get('foregroundHasCloudMask') is True
            and state.get('precip') == 'on' and state.get('lightning') == 'off'):
        return False
    if not full:
        return True
    cloud, sky, raw = state.get('actualCloud') or {}, state.get('celestial') or {}, state.get('raw') or {}
    layers, targets = sky.get('visibleForegrounds'), cloud.get('targets')
    try:
        if not (healthy_cloud(state) and rain_origin(state)
                and state.get('prayer', {}).get('modelIsNull') is False and state.get('selected') is True
                and cloud.get('publication') == state['publication']
                and cloud.get('coverage') == coverage and isinstance(targets, list) and len(targets) == 3
                and all(_finite_number(a) and abs(a - b) < 1e-9 for a, b in zip(targets, EXPECTED_COVERAGE))
                and (raw.get('currentValidAt'), raw.get('retrievedAt')) == (candidate['sourceValidAt'], candidate['retrievedAt'])
                and raw.get('target') == state.get('target')
                and _healthy_refresh_target_projection(state.get('target')) == receipts[0]['target']
                and state.get('runtimeGeneration') == receipts[0]['target']['generation']
                and isinstance(layers, list) and layers
                and any(layer.get('owner') == sky.get('owner') for layer in layers)):
            return False
        for layer in layers:
            canvas, composition = layer.get('canvas') or {}, layer.get('composition') or {}
            maximum, mean = composition.get('maxCloudAlpha'), composition.get('meanCloudAlpha')
            if not (canvas.get('visibility') == 'visible' and canvas.get('display') != 'none'
                    and _finite_number(canvas.get('opacity')) and canvas['opacity'] > 0 and _bounds(canvas.get('bounds'))
                    and canvas.get('rgbNonzero', 0) > 0 and canvas.get('maxRGB', 0) > canvas.get('minRGB', 0)
                    and _finite_number(maximum) and _finite_number(mean) and 0 < mean <= maximum <= 1
                    and _healthy_refresh_receipt(composition.get('cloudAuthority'), state['wallUtcMs'], receipts)):
                return False
    except (KeyError, TypeError, ValueError):
        return False
    return True


def healthy_refresh_pair(before, after, ledger, clock=None):
    """Select a real post-recovery replacement, never timestamp-only renewal."""
    left, right = healthy_refresh_record(before), healthy_refresh_record(after)
    result = {'schema': 'r000b-healthy-refresh-pair/v1', 'ok': False,
              'beforeRecord': left, 'afterRecord': right, 'clockOrigin': clock, 'reason': None}
    if left is None or right is None:
        result['reason'] = 'Both full captures must bind current record and native consumed receipt'
        return result
    if not (right['sourceValidAt'] > left['sourceValidAt'] and right['retrievedAt'] > left['retrievedAt']
            and right['publication']['revision'] > left['publication']['revision']
            and left['target'] == right['target'] and left['lane'] == right['lane']
            and _finite_number(before.get('elapsedMs')) and _finite_number(after.get('elapsedMs'))
            and before['elapsedMs'] < after['elapsedMs']):
        result['reason'] = 'No genuinely newer source and retrieval after the recovered capture'
        return result
    before_request = _healthy_refresh_request(left, before, ledger, clock)
    after_request = _healthy_refresh_request(right, after, ledger, clock)
    result.update(beforeRequest=before_request, afterRequest=after_request)
    if not (before_request and after_request and after_request['elapsedMs'] > before['elapsedMs']
            and after_request['weatherOrdinal'] > before_request['weatherOrdinal']
            and after_request['wallUtcMs'] - before_request['wallUtcMs'] >= 60000
            and after_request['nativeOwner']['operationId'] != before_request['nativeOwner']['operationId']
            and after_request['nativeOwner']['attemptId'] != before_request['nativeOwner']['attemptId']):
        result['reason'] = 'No distinct owned response consumed by an ordinary request after recovery'
        return result
    receipts = [left['publication'], right['publication']]
    for state, record in ((before, left), (after, right)):
        if not (_healthy_refresh_sample(state, receipts, full=True) and independent_celestial(state)
                and state['celestial'].get('composition', {}).get('cloudAuthority') == record['publication']
                and all(layer.get('composition', {}).get('cloudAuthority') == record['publication']
                        for layer in state['celestial']['visibleForegrounds'])):
            result['reason'] = 'Paired full captures must contain healthy raster/mask and the matching foreground publication'
            return result
    result.update(ok=True, reason='Owned ordinary response replaced the recovered record and reached full native/foreground publication')
    return result


def healthy_refresh_evidence(before, after, passive, full_samples, ledger, mode, clock=None):
    """Qualify all retained healthy-interval samples; clean endpoints cannot erase a gap."""
    pair = healthy_refresh_pair(before, after, ledger, clock)
    result = {'schema': 'r000b-healthy-refresh-continuity/v1', 'ok': False, 'pair': pair,
              'checks': {'ordinaryConsumedReplacementAfterRecovery': pair['ok']}, 'sampleFailures': [],
              'samplingLimit': 'Every retained passive sample checks model/ready/coverage/immutable active receipt/displayed mask presence; actual raster and mask alpha are checked on every retained full snapshot. The original continuous clip remains required. No forced capture-before-render ordering is claimed.'}
    start, end = before.get('elapsedMs'), after.get('elapsedMs')
    if not (_finite_number(start) and _finite_number(end) and end > start):
        result['sampleFailures'].append({'reason': 'Invalid bounded healthy interval'})
        return result
    result['intervalElapsedMs'] = [start, end]
    result['checks']['retainedSampleTimestampsObserved'] = all(isinstance(sample, dict) and _finite_number(sample.get('elapsedMs'))
                                                              for sample in [*passive, *full_samples])
    trace = [sample for sample in passive if _finite_number(sample.get('elapsedMs')) and start <= sample['elapsedMs'] <= end]
    full = [sample for sample in full_samples
            if _finite_number(sample.get('elapsedMs')) and start <= sample['elapsedMs'] <= end]
    if before not in full:
        full.insert(0, before)
    if after not in full:
        full.append(after)
    receipts = [record['publication'] for record in (pair['beforeRecord'], pair['afterRecord']) if record is not None]
    result['sampleCounts'] = {'passive': len(trace), 'full': len(full)}
    ordered_trace = sorted(trace, key=lambda sample: sample['elapsedMs'])
    boundaries = [start, *(sample['elapsedMs'] for sample in ordered_trace), end]
    result['maxPassiveObservationGapMs'] = max(b - a for a, b in zip(boundaries, boundaries[1:]))
    for channel, samples, is_full in [('passive', trace, False), ('full', full, True)]:
        for index, sample in enumerate(samples):
            if not receipts or not _healthy_refresh_sample(sample, receipts, full=is_full):
                result['sampleFailures'].append({'channel': channel, 'index': index, 'elapsedMs': sample['elapsedMs'],
                                                'reason': 'Model, active lease, ready deck, geometry-backed material or displayed foreground continuity failed'})
        result['checks']['allRetained' + channel.title() + 'SamplesHealthy'] = bool(samples) and not any(
            failure.get('channel') == channel for failure in result['sampleFailures'])
    chronology = sorted([*trace, *full], key=lambda sample: sample['elapsedMs'])
    positions = [receipts.index(sample['publication']) if sample.get('publication') in receipts else -1 for sample in chronology]
    result['checks']['consumedPublicationMovesOnlyFromAToB'] = (bool(receipts) and bool(positions)
        and positions[0] == 0 and positions[-1] == len(receipts) - 1 and all(a <= b for a, b in zip(positions, positions[1:])))
    motions = [{'elapsedMs': sample['elapsedMs'], 'motion': sample.get('actualCloud', {}).get('motion', sample.get('motion'))}
               for sample in chronology]
    result['motion'] = cloud_motion_continuity(motions, mode)
    result['checks']['signedPhaseLifeWanderAndPopulationContinuity'] = result['motion']['ok']
    result['ok'] = all(result['checks'].values())
    return result


def phase_progress(a, b):
    return [min(abs(x - y), 1.25 - abs(x - y))
            for x, y in zip(a['phase'], b['phase'])]


def motion_artifact_delta(out, before, after):
    wa, ha, a = png_rgba((out / before['file']).read_bytes())
    wb, hb, b = png_rgba((out / after['file']).read_bytes())
    if (wa, ha) != (wb, hb):
        raise ValueError('Cloud backing dimensions changed during watch')
    changed = sum(a[i:i + 4] != b[i:i + 4] for i in range(0, len(a), 4))
    alpha_delta = sum(abs(x - y) for x, y in zip(a[3::4], b[3::4]))
    return {'width': wa, 'height': ha, 'changedPixels': changed,
            'alphaAbsoluteDelta': alpha_delta,
            'interpretation': 'Artifact difference and actual accumulated phase are controls; the original clip still requires visual review. No qaState cloud hash is used.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='Exact generated product checkout to serve')
    parser.add_argument('--fixture-root', type=Path, help='Candidate fixture/helper checkout; defaults to --root')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--expected-manifest', type=Path, required=True,
                        help='Independently frozen r000b-native-expected/v1 product/script identities; this runner never creates its own approval manifest')
    parser.add_argument('--browser', choices=['chromium', 'firefox'], required=True)
    parser.add_argument('--python-packages', type=Path, help='Optional existing directory containing Playwright Python packages')
    parser.add_argument('--mode', choices=['default', 'reduced', 'full'], required=True)
    parser.add_argument('--expect', choices=['baseline-defect', 'withdrawal'], required=True)
    parser.add_argument('--hidden-expiry', action='store_true', help='Declared controlled document visibility event boundary; candidate/default only')
    args = parser.parse_args()
    if args.hidden_expiry and (args.mode != 'default' or args.expect != 'withdrawal'):
        parser.error('--hidden-expiry is scoped to candidate/default withdrawal evidence')
    root, out = args.root.resolve(), args.out.resolve()
    fixture_root = (args.fixture_root or args.root).resolve()
    if out.is_relative_to(root) or out.is_relative_to(fixture_root):
        raise ValueError('Keep every original acquisition outside product and fixture checkouts')
    out.mkdir(parents=True, exist_ok=False)
    row = {'schema': 'r000b-withdrawal-native/v1', 'status': 'FAIL',
           'id': 'ES0B-' + args.expect + '-' + args.browser + '-' + args.mode + ('-hidden' if args.hidden_expiry else ''),
           'expect': args.expect, 'productRoot': str(root), 'fixtureRoot': str(fixture_root),
           'checks': {}, 'observations': [], 'watches': [], 'limitations': __doc__,
           'pixelReview': 'PENDING: screenshots, cloud/rain origin, independent celestial output, and original video require inspection',
           'pageErrors': [], 'consoleErrors': [], 'unexpectedNetwork': [], 'httpRequests': []}
    dump(out / 'receipt.json', row)
    browser = context = page = pw = server = server_thread = None
    before = source_before = harness_before = None
    completed = False
    teardown_errors = []
    artifacts_by_stage = {}
    try:
        sys.path.insert(0, str(fixture_root / 'tools/cp9'))
        if args.python_packages:
            package_path = args.python_packages.resolve()
            if not package_path.is_dir():
                raise ValueError('--python-packages is not an existing directory')
            sys.path.insert(0, str(package_path))
        from browser_runtime import browser_options, browser_identity
        from runtime_identity import runtime_identity
        from playwright.sync_api import sync_playwright
        import browser_runtime
        import runtime_identity as runtime_identity_module
        import run_r000c_native

        before = runtime_identity(root)
        source_paths = ['src/native/index.html', 'src/native/config.js', 'real-sky/native-host-hooks.js',
                        'real-sky/native-composition.mjs', 'real-sky/native-host.mjs', 'real-sky/native-preview-host.mjs',
                        'tools/build_native.py', 'tests/native-script-contract.js']
        harness_paths = ['tests/rlgwo/r000b-no-timetable-fixture.html', 'tools/qa/run_r000b_withdrawal.py',
                         'tools/qa/run_r000c_native.py', 'tools/cp9/browser_runtime.py', 'tools/cp9/runtime_identity.py']
        source_before, harness_before = identities(root, source_paths), identities(fixture_root, harness_paths)
        wrapper = (fixture_root / harness_paths[0]).read_bytes()
        index = (root / 'index.html').read_bytes()
        row.update(runtime=before, authoredSources=source_before, fixtureSources=harness_before,
                   executedDriver={'path': str(Path(__file__).resolve()), 'sha256': sha(Path(__file__).read_bytes())},
                   sourceSha256=sha(index), scriptBodies=script_identities(index), wrapperSha256=sha(wrapper))
        expected_bytes = args.expected_manifest.resolve().read_bytes()
        expected = json.loads(expected_bytes)
        if expected.get('schema') != 'r000b-native-expected/v1':
            raise ValueError('Expected an independently frozen r000b-native-expected/v1 manifest')
        expected_bindings = {'runtimeTreeSha256': before['treeSha256'], 'indexSha256': row['sourceSha256'],
                             'scriptBodies': row['scriptBodies']}
        for name, actual in expected_bindings.items():
            if expected.get(name) != actual:
                raise ValueError('Approved source manifest mismatch: ' + name)
        for name, actual in [('authoredSources', source_before), ('fixtureSources', harness_before)]:
            if name in expected and expected[name] != actual:
                raise ValueError('Approved source manifest mismatch: ' + name)
        (out / 'expected-manifest.json').write_bytes(expected_bytes)
        row['approvedManifest'] = {'file': 'expected-manifest.json', 'sha256': sha(expected_bytes),
                                   'runtimeTreeSha256': expected['runtimeTreeSha256'], 'indexSha256': expected['indexSha256']}
        row['checks']['approvedSourceManifest'] = True
        row['checks']['executedHarnessMatchesDeclaredFixtureRoot'] = sha(Path(__file__).read_bytes()) == harness_before[harness_paths[1]]['sha256']
        row['executedHelperModules'] = {name: {'path': str(Path(module.__file__).resolve()), 'sha256': sha(Path(module.__file__).read_bytes())}
            for name, module in [('tools/qa/run_r000c_native.py', run_r000c_native),
                                 ('tools/cp9/browser_runtime.py', browser_runtime),
                                 ('tools/cp9/runtime_identity.py', runtime_identity_module)]}
        row['checks']['executedHelperIdentities'] = all(value['sha256'] == harness_before[name]['sha256']
                                                       for name, value in row['executedHelperModules'].items())
        if not row['checks']['executedHarnessMatchesDeclaredFixtureRoot'] or not row['checks']['executedHelperIdentities']:
            raise ValueError('Executed qualification code differs from declared fixture-root identities')
        case = {'id': row['id'], 'clock': 'single initial epoch offset; native elapsed 1x integer milliseconds',
                'startUtc': '2026-09-08T20:59:50.000Z', 'startCivil': '2026-09-08T23:59:50+03:00',
                'initialSourceTime': '2026-09-08T23:45', 'initialSourceUtc': INITIAL_SOURCE_UTC,
                'initialSourceAgeMs': 890000, 'inclusiveSourceBoundMs': 900000, 'intervalSeconds': 900,
                'site': {'lat': 24.7136, 'lon': 46.6753, 'label': 'Riyadh', 'zone': 'Asia/Riyadh', 'intent': 'fixed-site'},
                'weather': {'temperatureC': 24, 'WMO': 63, 'precipitationMm': 2, 'rainMm': 2,
                            'cloudPercent': 92, 'lowPercent': 92, 'midPercent': 90, 'highPercent': 60,
                            'windSpeedMs': 2, 'windDirectionDeg': 225, 'isDay': 0},
                'replacement': 'Every ordinary subsequent weather request succeeds with the current civil minute source time; no hourly track is supplied',
                'prayerRecovery': '09/10 Sep responses are controlled503 before fixture elapsed100000 ms, then ordinary current retry may succeed',
                'ordinaryRetrySemantics': 'Weather maintenance opportunities are about30 s apart with an existing >=60 s attempt guard; prayer operations have their own60 s cooldown and three attempt budget',
                'radar': 'Admitted synthetic empty index; unavailable, no quantity or dry-observation authority',
                'motionPreference': 'no-preference' if args.mode == 'default' else 'reduce',
                'fullOverride': args.mode == 'full', 'recoveredWatchSeconds': 30,
                'healthyRefresh': 'Required owned ordinary weather replacement after genuine model recovery; reuse recovered watch captures or passively wait within unchanged240 s fixture cap; no forced capture ordering',
                'visibility': 'controlled document property and visibilitychange, hide after5 s/resume after12 s; not OS sleep/wake' if args.hidden_expiry else 'native visible document',
                'expectation': args.expect, 'baselineWatch': 'Stop after15 s defect/control capture; no product PASS'}
        dump(out / 'case-input.json', case)

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                path = unquote(urlsplit(self.path).path)
                request = {'path': path, 'hostMonotonic': time.monotonic()}
                row['httpRequests'].append(request)
                if path == '/fixture.html':
                    data, mime = wrapper, 'text/html; charset=utf-8'
                elif path == '/favicon.ico':
                    request['status'] = 204
                    self.send_response(204)
                    self.end_headers()
                    return
                elif path.startswith('/product/'):
                    relative = path[len('/product/'):]
                    target = (root / relative).resolve()
                    expected = before['files'].get(relative)
                    if expected is None or not target.is_relative_to(root) or not target.is_file():
                        request['status'] = 404
                        self.send_error(404)
                        return
                    data = target.read_bytes()
                    if sha(data) != expected['sha256']:
                        request.update(status=409, reason='Manifest drift before serving')
                        self.send_error(409)
                        return
                    request['sha256'] = expected['sha256']
                    suffix = target.suffix.lower()
                    mime = {'html': 'text/html', 'js': 'text/javascript', 'mjs': 'text/javascript',
                            'css': 'text/css', 'json': 'application/json', 'wasm': 'application/wasm',
                            'png': 'image/png', 'gz': 'application/octet-stream'}.get(suffix[1:], 'application/octet-stream')
                else:
                    request['status'] = 404
                    self.send_error(404)
                    return
                request.update(status=200, bytes=len(data))
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                try:
                    self.wfile.write(data)
                except (BrokenPipeError, ConnectionResetError):
                    request['clientClosed'] = True

        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.daemon_threads = True
        server_thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': 0.1}, daemon=True)
        server_thread.start()
        origin = f'http://127.0.0.1:{server.server_port}'
        os.environ['SALAH_BROWSER'] = args.browser
        pw = sync_playwright().start()
        family, options = browser_options()
        if family != args.browser or family == 'chromium' and options.get('chromium_sandbox') is not True:
            raise ValueError('Requested engine/sandbox boundary changed')
        browser = getattr(pw, family).launch(**options)
        executable = options.get('executable_path') or getattr(pw, family).executable_path
        row['browser'] = {**browser_identity(browser), 'executable': executable,
                          'executableSha256': sha(Path(executable).read_bytes()), 'headless': options['headless']}
        context = browser.new_context(viewport={'width': 390, 'height': 600}, device_scale_factor=1,
                                      timezone_id='Asia/Riyadh', reduced_motion=case['motionPreference'],
                                      service_workers='block', accept_downloads=False,
                                      record_video_dir=str(out / 'video'), record_video_size={'width': 390, 'height': 600})

        def route_request(route):
            parsed = urlsplit(route.request.url)
            request_origin = f'{parsed.scheme}://{parsed.netloc}'
            if request_origin == origin and (parsed.path in ('/fixture.html', '/favicon.ico') or parsed.path.startswith('/product/')):
                route.continue_()
            else:
                # Unexpected inputs are reported without query strings, userinfo,
                # headers, cookies, or response bodies that could carry secrets.
                row['unexpectedNetwork'].append({'scheme': parsed.scheme, 'host': parsed.hostname,
                                                 'path': parsed.path, 'method': route.request.method})
                route.abort('blockedbyclient')

        context.route('**/*', route_request)
        page = context.new_page()
        page.on('pageerror', lambda error: row['pageErrors'].append(str(error)))
        page.on('console', lambda message: row['consoleErrors'].append(message.text) if message.type == 'error' else None)
        cfg = {'lat': '24.7136', 'lon': '46.6753', 'tz': 'Asia/Riyadh', 'label': 'Riyadh',
               'method': 4, 'school': 0, 'units': 'c', 'seed': 1}
        if args.mode == 'full':
            cfg['motion'] = 'full'
        query = {'case': 'ES0B-midnight-withdrawal', 'attempt': 1,
                 'run': row['id'] + '-' + uuid.uuid4().hex, 'expectedSource': expected['indexSha256']}
        if args.hidden_expiry:
            query['visibility'] = 'controlled'
        row['url'] = origin + '/fixture.html?' + urlencode(query) + '#' + urlencode(cfg)
        row['navigationHostMonotonic'] = time.monotonic()

        def await_state(expression, timeout=15000):
            predicate = LATEST.replace('return f?.state===\'ready\'?f.latest:null;',
                                       "const s=f?.state==='ready'?f.latest:null;return !!s&&(" + expression + ');')
            wait(page, predicate, timeout)

        def record_state(stage, state, screenshot=True):
            artifacts = retain_media(out, stage, state)
            observation = {'stage': stage, 'hostMonotonic': time.monotonic(), 'state': state, 'artifacts': artifacts}
            if screenshot:
                start = time.monotonic()
                for suffix, clip in [('viewport', None), ('card', {k: state['card'][k] for k in ('left', 'top', 'width', 'height')})]:
                    path = out / f'{stage}-{suffix}.png'
                    params = {'path': str(path), 'animations': 'allow'}
                    if clip:
                        params['clip'] = {'x': clip['left'], 'y': clip['top'], 'width': clip['width'], 'height': clip['height']}
                    page.screenshot(**params)
                    artifacts[suffix] = {'file': path.name, 'sha256': sha(path.read_bytes())}
                observation['screenshotWindow'] = {'startHostMonotonic': start, 'endHostMonotonic': time.monotonic(),
                                                   'note': 'Screenshots follow the read snapshot; the original continuous video preserves the intervening frames.'}
            artifacts_by_stage[stage] = artifacts
            row['observations'].append(observation)
            dump(out / f'{stage}.json', observation)
            cloud, effects = state['actualCloud'], state['effects']
            row['checks'][stage + '/325x530'] = state['card']['width'] == 325 and state['card']['height'] == 530
            row['checks'][stage + '/footerFits'] = 0 <= state['footer']['top'] < state['footer']['bottom'] <= 530.1
            row['checks'][stage + '/sixRows'] = len(state['rows']) == 6 and len({r['key'] for r in state['rows']}) == 6
            row['checks'][stage + '/rowsFit'] = all(0 <= r['rect']['left'] < r['rect']['right'] <= 325.1
                and 0 <= r['rect']['top'] < r['rect']['bottom'] <= state['footer']['top'] for r in state['rows'])
            row['checks'][stage + '/liveClock'] = state['clock'] == {'TIMESCALE': 1, 'FOLLOW_WALL_CLOCK': True, 'ADVANCING': False}
            row['checks'][stage + '/noLightning'] = effects['lightning'] == 'off'
            row['checks'][stage + '/consumerDomBounded'] = state['resources']['cloudCanvases'] == 1 and state['resources']['particles'] == 72
            row['checks'][stage + '/backingReadbackMatches'] = cloud['raster']['alphaSum'] == artifacts['native-cloud']['pixels']['alphaSum']
            dump(out / 'progress.json', row)
            return state

        def capture(stage):
            return record_state(stage, page.evaluate(READ))

        page.goto(row['url'], wait_until='commit', timeout=60000)
        await_state('!s.modelIsNull&&s.loopStarted&&s.candidate.eligible&&s.cloudReady&&s.precip===\'on\'&&s.temperature===\'24°\'&&s.foregroundVisible&&s.foregroundHasCloudMask', 9000)
        current = capture('healthy-before-midnight')
        row['checks']['healthyBeforeMidnight'] = current['elapsedMs'] < 9000 and not current['modelIsNull'] and healthy_cloud(current)
        row['checks']['healthyModelRainOrigin'] = rain_origin(current) and current['effects']['rainOpacity'] > 0
        row['checks']['healthyIndependentCelestial'] = independent_celestial(current)
        row['checks']['initialRawSourceAndReceiptDistinct'] = (current['raw']['currentValidAt'] == INITIAL_SOURCE_UTC
            and current['raw']['currentIntervalSec'] == 900 and current['raw']['retrievedAt'] > INITIAL_SOURCE_UTC
            and current['cache']['parsed']['w']['currentValidAt'] == INITIAL_SOURCE_UTC)
        row['checks']['initialModelDisclosure'] = ('current model estimate' in current['header']['label']
            and 'direct local observation unavailable' in current['header']['label']
            and current['lastWeatherHeader']['observedPresent'] is False)

        if args.hidden_expiry:
            await_state('s.elapsedMs>=5000', 7000)
            page.evaluate('() => __withdrawalVisibility.transition(__withdrawalRead.identity(),true)')
            await_state('s.documentHidden&&s.documentVisibility===\'hidden\'&&s.cardPaused&&s.motion.paused', 2000)
            paused = capture('hidden-before-expiry')
            row['checks']['hiddenBoundaryReached'] = paused['documentHidden'] and paused['cardPaused'] and paused['actualCloud']['motion']['paused']
            await_state('s.elapsedMs>=11000&&s.modelIsNull&&!s.candidate.eligible', 8000)
            hidden_expired = capture('hidden-after-901s')
            row['checks']['hiddenClockContinues'] = hidden_expired['candidate']['sourceAgeMs'] >= 901000 and hidden_expired['documentHidden']
            await_state('s.elapsedMs>=12000', 3000)
            page.evaluate('() => __withdrawalVisibility.transition(__withdrawalRead.identity(),false)')
            wait(page, "() => {const f=__withdrawalFixture;if(f.state==='error')throw Error(f.error);return f.resumeObservation?.complete===true;}", 6000)
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
            expired = capture('resumed-expired')
        else:
            await_state('s.elapsedMs>=8500', 10000)
            before_midnight = capture('last-eligible-before-midnight')
            row['checks']['preBoundaryStillEligible'] = before_midnight['candidate']['eligible'] and before_midnight['candidate']['sourceAgeMs'] <= 900000
            await_state('s.elapsedMs>=11000&&s.modelIsNull&&!s.candidate.eligible', 10000)
            expired = capture('expired-901s')

        row['checks']['actualPrayerModelIsNull'] = (expired['modelIsNull'] and expired['prayer']['modelIsNull']
            and expired['prayer']['currentDay'] == '09-09-2026' and expired['prayer']['todayDay'] == '08-09-2026'
            and expired['prayer']['lastRender'] is None and all(r['time'] == '—' for r in expired['rows']))
        row['checks']['expiredHeaderAndEffectsWithdraw'] = unknown_weather(expired) and effects_off(expired)
        row['checks']['expiredIndependentCelestial'] = independent_celestial(expired)
        row['checks']['rawAndCacheSurviveExpiry'] = expired['raw'] == current['raw'] and expired['cache']['bytes'] == current['cache']['bytes']
        row['checks']['expiredSourceAgeAtLeast901s'] = expired['candidate']['sourceAgeMs'] >= 901000
        await_state('s.elapsedMs>=16000' if args.hidden_expiry else 's.elapsedMs>=15000', 10000)
        repeated = capture('expired-repeat')

        if args.expect == 'baseline-defect':
            row['checks']['baselineActualCloudDefect'] = healthy_cloud(expired) and healthy_cloud(repeated)
            row['checks']['baselineHasNoWithdrawalReceipt'] = expired['actualCloud']['publication'] is None
            row['checks']['baselineNoFreshIngressBeforeDefect'] = expired['raw']['currentValidAt'] == INITIAL_SOURCE_UTC
            final = repeated
        else:
            row['checks']['expiredNativeMaterialEmpty'] = actual_empty(expired) and actual_empty(repeated)
            row['checks']['expiredJoinedMaterialEmpty'] = joined_empty(expired) and joined_empty(repeated)
            row['checks']['expiredConsumedReceipt'] = all((s['actualCloud']['publication'] or {}).get('state') == 'withdrawn-unavailable' for s in (expired, repeated))
            row['checks']['repeatedWithdrawalIdempotent'] = (expired['actualCloud']['publication'] == repeated['actualCloud']['publication']
                and expired['effects']['particleCount'] == repeated['effects']['particleCount'])
            await_state('s.elapsedMs>60000&&s.modelIsNull&&s.candidate.eligible&&s.candidate.sourceValidAt!==f.initialSourceUtc&&s.temperature===\'24°\'&&s.publication?.sourceValidAt===s.candidate.sourceValidAt', 100000)
            replacement = capture('fresh-weather-without-prayers')
            row['checks']['ordinaryFreshReplacementBeforePrayer'] = replacement['modelIsNull'] and replacement['candidate']['eligible'] and replacement['raw']['currentValidAt'] > INITIAL_SOURCE_UTC
            row['checks']['replacementCannotReviveOldDeck'] = actual_empty(replacement) and joined_empty(replacement) and effects_off(replacement)
            row['checks']['replacementHeaderStillModel'] = replacement['header']['temperature'] == '24°' and replacement['lastWeatherHeader']['observedPresent'] is False
            await_state('s.elapsedMs>=100000&&!s.modelIsNull&&s.candidate.eligible&&s.cloudReady&&s.precip===\'on\'&&s.foregroundVisible&&s.foregroundHasCloudMask', 100000)
            recovered = capture('recovered')
            row['checks']['ordinaryPrayerRecovery'] = recovered['prayer']['todayDay'] == '09-09-2026' and not recovered['modelIsNull'] and healthy_cloud(recovered)
            receipt = recovered['actualCloud']['publication'] or {}
            row['checks']['recoveredOnlyCurrentAuthority'] = (receipt.get('state') == 'eligible-published'
                and receipt.get('sourceValidAt') == recovered['raw']['currentValidAt']
                and receipt.get('retrievedAt') == recovered['raw']['retrievedAt']
                and recovered['raw']['currentValidAt'] > INITIAL_SOURCE_UTC)
            row['checks']['recoveredRainOrigin'] = rain_origin(recovered)
            watch = {'stage': 'recovered', 'startHostMonotonic': time.monotonic(),
                     'startFixtureElapsedMs': recovered['elapsedMs'], 'requiredSeconds': 30,
                     'mode': args.mode, 'observer': 'continuous original video plus bounded passive owner/DOM trace; no full diagnostic reads or screenshots inside watch'}
            print(json.dumps({'stage': 'recovered-watch', 'requiredSeconds': 30, 'case': row['id']}), flush=True)
            page.wait_for_timeout(30000)
            watch['endHostMonotonic'] = time.monotonic()
            row['watches'].append(watch)
            final = capture('recovered-30s')
            row['checks']['recoveredWatchDuration'] = watch['endHostMonotonic'] - watch['startHostMonotonic'] >= 30
            row['checks']['recoveredWatchHealthy'] = healthy_cloud(final) and rain_origin(final) and independent_celestial(final)
            progress = phase_progress(recovered['actualCloud']['motion'], final['actualCloud']['motion'])
            row['motionEvidence'] = {'actualPhaseProgress': progress,
                'before': recovered['actualCloud']['motion'], 'after': final['actualCloud']['motion'],
                'backingArtifactDelta': motion_artifact_delta(out, artifacts_by_stage['recovered']['native-cloud'], artifacts_by_stage['recovered-30s']['native-cloud']),
                'pixelVerdict': 'PENDING'}
            if args.mode == 'reduced':
                row['checks']['reducedMotionHoldsPhase'] = progress == [0, 0, 0] and final['actualCloud']['motion']['life'] == recovered['actualCloud']['motion']['life']
            else:
                row['checks']['defaultOrFullAccumulatesPhase'] = max(progress) > 0.001 and row['motionEvidence']['backingArtifactDelta']['changedPixels'] > 0

            # R000B_F01_REQUIRED_ORDINARY_HEALTHY_REFRESH_V1
            # The original30-second watch above remains uninterrupted. Reuse its
            # actual full captures when they already bracket an owned refresh.
            refresh_before = healthy_refresh_record(recovered)
            if refresh_before is None:
                raise ValueError('Recovered capture lacks a bound current record/native receipt')
            refresh_progress = page.evaluate(HEALTHY_REFRESH_PROGRESS)
            refresh_clock_origin = refresh_progress.get('clockOrigin')
            if _healthy_refresh_clock(recovered, refresh_clock_origin) is None:
                raise ValueError('Observed fixture clock origin is missing or inconsistent with native motion')
            if refresh_progress['maxElapsedMs'] != 240000:
                raise ValueError('Healthy refresh requires the unchanged240-second fixture budget')
            refresh_after_stage = 'recovered-30s'
            refresh_pair = healthy_refresh_pair(recovered, final, refresh_progress['ledger'], refresh_clock_origin)
            refresh_acquisition = row['healthyRefreshAcquisition'] = {
                'beforeStage': 'recovered', 'afterStage': refresh_after_stage, 'clockOrigin': refresh_clock_origin,
                'reusedRecoveredWatchCaptures': refresh_pair['ok'], 'captureAttemptsAfterWatch': 0,
                'fixtureMaxElapsedMs': refresh_progress['maxElapsedMs'], 'captureDeadlineElapsedMs': 235000,
                'captureHeadroomMs': 5000, 'waitStartElapsedMs': refresh_progress['elapsedMs'],
                'lastPairSelection': refresh_pair,
                'scope': 'Actual ordinary post-model refresh only; no forced producer or capture-before-render ordering'}
            row['checks']['healthyRefreshAcquired'] = refresh_pair['ok']
            if not refresh_pair['ok']:
                print(json.dumps({'stage': 'await-ordinary-healthy-refresh', 'case': row['id'],
                                  'captureDeadlineElapsedMs': 235000}), flush=True)
            while not refresh_pair['ok']:
                if refresh_progress.get('clockOrigin') != refresh_clock_origin:
                    raise ValueError('Observed fixture clock origin changed during healthy refresh acquisition')
                remaining = refresh_acquisition['captureDeadlineElapsedMs'] - refresh_progress['elapsedMs']
                if remaining <= 0:
                    raise TimeoutError('No owned healthy full publication after prayer recovery within the remaining240-second fixture budget: ' + str(refresh_pair['reason']))
                latest = refresh_progress.get('latest') or {}
                candidate = latest.get('candidate') or {}
                # This reads only the existing passive record. If A remains the
                # active receipt while B is a candidate, a snapshot may retain A;
                # only an ordinary full publication of B can complete selection.
                if (candidate.get('eligible') is True
                        and _finite_number(candidate.get('sourceValidAt')) and _finite_number(candidate.get('retrievedAt'))
                        and candidate['sourceValidAt'] > refresh_before['sourceValidAt']
                        and candidate['retrievedAt'] > refresh_before['retrievedAt']):
                    refresh_acquisition['captureAttemptsAfterWatch'] += 1
                    refresh_after_stage = 'healthy-refresh-' + str(refresh_acquisition['captureAttemptsAfterWatch']).zfill(3)
                    final = capture(refresh_after_stage)
                    refresh_progress = page.evaluate(HEALTHY_REFRESH_PROGRESS)
                    if refresh_progress.get('clockOrigin') != refresh_clock_origin:
                        raise ValueError('Observed fixture clock origin changed at the healthy refresh capture')
                    refresh_pair = healthy_refresh_pair(recovered, final, refresh_progress['ledger'], refresh_clock_origin)
                    refresh_acquisition.update(afterStage=refresh_after_stage, lastPairSelection=refresh_pair)
                    row['checks']['healthyRefreshAcquired'] = refresh_pair['ok']
                    if refresh_pair['ok']:
                        break
                    remaining = refresh_acquisition['captureDeadlineElapsedMs'] - refresh_progress['elapsedMs']
                    if remaining <= 0:
                        continue
                page.wait_for_timeout(min(1000, remaining))
                refresh_progress = page.evaluate(HEALTHY_REFRESH_PROGRESS)
            refresh_acquisition['endElapsedMs'] = refresh_progress['elapsedMs']
            refresh_acquisition['observedRequest'] = refresh_pair['afterRequest']

        fixture = page.evaluate(FIXTURE)
        # Keep the first resumed raw snapshots as their own immutable artifacts;
        # avoid duplicating their large PNG strings inside the final trace.
        for key in ('resumeFirstRaf', 'resumeFirstVisible', 'resumeReady'):
            if key in fixture:
                fixture[key] = {'savedIn': 'resumeObservation.opportunities; first/visible/ready are separately identified by actual visibility and status'}
        for opportunity in fixture.get('resumeOpportunities', []):
            if opportunity.get('state') is not None:
                opportunity['state'] = {'savedAs': 'resume-opportunity-' + str(opportunity['frame']).zfill(3) + '.json'}
        row['fixture'] = fixture
        if args.expect == 'withdrawal':
            if {'started': fixture.get('started'), 'startUtc': fixture.get('startUtc')} != refresh_clock_origin:
                raise ValueError('Final fixture clock origin differs from the observed acquisition origin')
            refresh_observations = [observation for observation in row['observations']
                if recovered['elapsedMs'] <= observation['state']['elapsedMs'] <= final['elapsedMs']]
            refresh_evidence = healthy_refresh_evidence(recovered, final, fixture['passive'],
                [observation['state'] for observation in refresh_observations], fixture['ledger'], args.mode, refresh_clock_origin)
            refresh_trace_path = out / 'healthy-refresh-passive.json'
            dump(refresh_trace_path, [sample for sample in fixture['passive']
                if recovered['elapsedMs'] <= sample['elapsedMs'] <= final['elapsedMs']])
            refresh_evidence['retainedFullCaptures'] = [{'stage': observation['stage'],
                'file': observation['stage'] + '.json', 'artifacts': observation['artifacts']}
                for observation in refresh_observations]
            refresh_evidence['passiveTrace'] = {'file': refresh_trace_path.name, 'sha256': sha(refresh_trace_path.read_bytes())}
            row['healthyRefreshEvidence'] = refresh_evidence
            row['checks'].update({'healthyRefresh/' + name: passed for name, passed in refresh_evidence['checks'].items()})
            row['checks']['healthyRefreshContinuity'] = refresh_evidence['ok']
            dump(out / 'healthy-refresh-evidence.json', refresh_evidence)

        warm = [s for s in fixture['passive']
                if s['modelIsNull'] and s['candidate']['eligible']
                and s['candidate'].get('sourceValidAt') == INITIAL_SOURCE_UTC
                and s['candidate'].get('sourceAgeMs') == 900000
                and s.get('wallUtcMs') == INITIAL_SOURCE_UTC + 900000]
        row['inclusiveBoundaryObservation'] = {'observed': bool(warm), 'samples': warm,
            'status': 'OBSERVED' if warm else 'NOT_NATURALLY_REACHED',
            'scope': 'The 900000 ms inclusive source bound and midnight share one integer millisecond. No clock or render was forced to manufacture the overlap; deterministic source tests qualify the exact boundary separately.'}
        weather = [r for r in fixture['ledger'] if r.get('kind') == 'weather']
        prayer = [r for r in fixture['ledger'] if r.get('kind') == 'prayer']
        failed_prayer = [r for r in prayer if r.get('status') == 503]
        row['checks']['controlled503NeverParsed'] = bool(failed_prayer) and all(r['jsonReads'] == 0 for r in failed_prayer)
        row['checks']['weatherAttemptSpacing'] = all(b['wallUtcMs'] - a['wallUtcMs'] >= 60000 for a, b in zip(weather, weather[1:]))
        row['checks']['noExpiryOrResumeRequestStorm'] = len([r for r in weather if r['elapsedMs'] < 30000]) == 1
        row['checks']['weatherResponsesReallyConsumed'] = bool(weather) and all(r['status'] == 200 and r['jsonReads'] == 1 and r.get('jsonSettled') for r in weather)
        row['checks']['weatherAttemptOwnership'] = all(r.get('nativeOwner', {}).get('operationId') is not None and r.get('nativeOwner', {}).get('attemptId') is not None for r in weather)
        grouped = {}
        for request in prayer:
            owner = request.get('nativeOwner') or {}
            grouped.setdefault(owner.get('operationId'), []).append(request)
        row['checks']['prayerAttemptBudget'] = None not in grouped and all(1 <= len(requests) <= 3 for requests in grouped.values())
        if args.expect == 'withdrawal':
            successful_current = [r for r in prayer if r['prayerDay'] == '09-09-2026' and r['status'] == 200]
            row['checks']['providerRecoveryUsesOrdinaryRetry'] = bool(successful_current) and all(r['elapsedMs'] >= 100000 for r in successful_current)
            row['checks']['replacementPrecedesPrayerResponse'] = len(weather) >= 2 and bool(successful_current) and weather[1]['elapsedMs'] < successful_current[0]['elapsedMs']
        row['checks']['sourceBinding'] = fixture['sourceSha256'] == row['sourceSha256'] == fixture['expectedSourceSha256']
        row['checks']['unchangedBodies'] = fixture['productBodiesUnchanged'] and fixture['scriptBodies'] == row['scriptBodies']
        row['checks']['privateIngress'] = fixture['storageIsolated'] and fixture['clockIsolated'] and fixture['fetchIntercepted'] and fixture['initialStorageEntries'] == 0
        allowed_events = {'consumer-read'} | ({'visibility-hidden', 'visibility-visible'} if args.hidden_expiry else set())
        row['checks']['noProductControlHelper'] = all(e['action'] in allowed_events for e in fixture['events'])
        row['checks']['native1xElapsed'] = abs((final['wallUtcMs'] - current['wallUtcMs']) - (final['elapsedMs'] - current['elapsedMs'])) < 2
        observed = [o['state'] for o in row['observations']]
        row['observedSkyDiagnosticFields'] = [{'stage': o['stage'], 'fields': observed_sky_error_fields(o['state'])} for o in row['observations']]
        inspected_error_fields = [field for record in row['observedSkyDiagnosticFields'] for field in record['fields'] if field['observed']]
        row['checks']['noErrorsInObservedSkyDiagnosticFields'] = bool(inspected_error_fields) and all(not field['value'] for field in inspected_error_fields)
        row['uninspectedDiagnostics'] = ['Handled Moon worker diagnostic errors: effectful Moon runtime state/surface/presentation getters are deliberately not read; DOM and pixel evidence is retained instead.']
        row['checks']['sameTargetAndScene'] = all(s['target'] == current['target'] and s['sceneIdentity'] == current['sceneIdentity'] and s['runtimeGeneration'] == current['runtimeGeneration'] for s in observed)
        trace = [s for s in fixture['passive'] if s['elapsedMs'] >= current['elapsedMs']]
        first_motion = current['actualCloud']['motion']
        row['checks']['populationAndSeedRetained'] = all(s['motion']['key'] == first_motion['key'] and s['motion']['population'] == first_motion['population'] and s['motion']['fieldSeed'] == first_motion['fieldSeed'] for s in trace)
        motion_samples = [{'elapsedMs': state['elapsedMs'], 'motion': state['actualCloud']['motion']} for state in observed]
        motion_samples += [{'elapsedMs': state['elapsedMs'], 'motion': state['motion']} for state in trace]
        visibility_changes = fixture.get('visibility', {}).get('changes', [])
        motion_samples += [{'elapsedMs': event['elapsedAfterDispatchMs'], 'motion': event['nativeMotionAfter']} for event in visibility_changes]
        motion_samples.sort(key=lambda sample: sample['elapsedMs'])
        row['motionContinuityEvidence'] = cloud_motion_continuity(motion_samples, args.mode, visibility_changes)
        row['checks']['signedPhaseLifeWanderContinuity'] = row['motionContinuityEvidence']['ok']
        row['checks']['motionPreference'] = final['motionPreference'] == {'reduced': args.mode != 'default', 'full': args.mode == 'full'} and final['actualCloud']['motion']['reduced'] == (args.mode == 'reduced')
        if args.hidden_expiry:
            changes = fixture['visibility']['changes']
            row['checks']['singleDeclaredVisibilityCycle'] = len(changes) == 2 and changes[0]['hidden'] is True and changes[1]['hidden'] is False and not final['documentHidden'] and not final['actualCloud']['motion']['paused']
        completed = True
    except Exception:
        row['exception'] = traceback.format_exc()
    finally:
        if page is not None and 'fixture' not in row:
            try:
                row['fixture'] = page.evaluate(FIXTURE)
            except Exception:
                pass
        if page is not None and not completed:
            try:
                page.screenshot(path=str(out / 'failure-last-viewport.png'), animations='allow')
            except Exception:
                pass
        if context is not None:
            try:
                context.close()
            except Exception:
                teardown_errors.append(traceback.format_exc())
        if page is not None and page.video:
            try:
                video = Path(page.video.path())
                row['video'] = {'file': video.relative_to(out).as_posix(), 'bytes': video.stat().st_size,
                                'sha256': sha(video.read_bytes()), 'original': True,
                                'scope': 'Continuous native recording from navigation through final observation; never replaced by an edited clip'}
            except Exception:
                teardown_errors.append(traceback.format_exc())
        if browser is not None:
            try:
                browser.close()
            except Exception:
                teardown_errors.append(traceback.format_exc())
        if pw is not None:
            try:
                pw.stop()
            except Exception:
                teardown_errors.append(traceback.format_exc())
        if server is not None:
            try:
                server.shutdown()
                server.server_close()
                server_thread.join(timeout=5)
                if server_thread.is_alive():
                    raise RuntimeError('Local qualification server did not stop')
            except Exception:
                teardown_errors.append(traceback.format_exc())
        if before is not None:
            try:
                row['checks']['runtimeUnchanged'] = runtime_identity(root) == before
                row['checks']['authoredSourcesUnchanged'] = identities(root, source_paths) == source_before
                row['checks']['fixtureSourcesUnchanged'] = identities(fixture_root, harness_paths) == harness_before
            except Exception:
                row['checks']['identityRecheckSucceeded'] = False
                teardown_errors.append(traceback.format_exc())
        fixture = row.get('fixture') or {}
        row['teardownErrors'] = teardown_errors
        # R000B_HN_ERROR_CHANNELS_V2_1
        row['checks']['noErrorsInObservedBrowserFixtureAndTeardownChannels'] = not row['pageErrors'] and not row['consoleErrors'] and not fixture.get('consoleErrors') and not fixture.get('error') and not teardown_errors
        row['checks']['networkContained'] = not row['unexpectedNetwork'] and not any(r.get('status', 200) >= 400 for r in row['httpRequests'])
        row['checks']['originalVideoRetained'] = row.get('video', {}).get('bytes', 0) > 0
        row['checks']['sequenceCompleted'] = completed
        if completed and all(value is True for value in row['checks'].values()):
            row['status'] = ('BASELINE_DEFECT_DEMONSTRATED_PENDING_PIXEL_REVIEW' if args.expect == 'baseline-defect'
                             else 'PASS_ASSERTIONS_PENDING_PIXEL_REVIEW')
        manifest = {p.relative_to(out).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
                    for p in sorted(out.rglob('*')) if p.is_file() and p.name not in {'receipt.json', 'progress.json', 'artifact-manifest.json'}}
        dump(out / 'artifact-manifest.json', manifest)
        row['artifactManifestSha256'] = sha((out / 'artifact-manifest.json').read_bytes())
        dump(out / 'receipt.json', row)
        print(json.dumps({'case': row['id'], 'status': row['status'],
                          'failedChecks': [name for name, value in row['checks'].items() if value is not True],
                          'exception': row.get('exception')}), flush=True)
    return 0 if row['status'] in {'PASS_ASSERTIONS_PENDING_PIXEL_REVIEW', 'BASELINE_DEFECT_DEMONSTRATED_PENDING_PIXEL_REVIEW'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
