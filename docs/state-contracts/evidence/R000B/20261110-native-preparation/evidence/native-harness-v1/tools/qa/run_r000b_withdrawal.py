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

import argparse
import base64
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
    artifacts = {}
    for name, value in media.items():
        data = decode_png_url(value)
        path = out / f'{stage}-{name}.png'
        path.write_bytes(data)
        artifacts[name] = {'file': path.name, 'sha256': sha(data), 'pixels': png_summary(data)}
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


def rain_origin(state):
    effects = state['effects']
    shown = [p for p in effects['particles'] if p['displayed']]
    return (effects['cloudGateActive'] and bool(shown)
            and all(p['kind'] == 'rain' and p['normalizedDensity'] is not None
                    and p['normalizedDensity'] > 0.16 for p in shown))


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
            wait(page, "() => {const f=__withdrawalFixture;if(f.state==='error')throw Error(f.error);return !!f.resumeFirstVisible;}", 6000)
            fixture_resume = page.evaluate('() => ({first:__withdrawalFixture.resumeFirstRaf,visible:__withdrawalFixture.resumeFirstVisible,observation:__withdrawalFixture.resumeObservation})')
            first_resume = record_state('resume-first-raf', fixture_resume['first'], screenshot=False)
            first_visible = record_state('resume-first-visible-publication', fixture_resume['visible'], screenshot=False)
            row['resumeObservation'] = fixture_resume['observation']
            row['checks']['firstResumeWithdrawsNativeMaterial'] = actual_empty(first_resume) and effects_off(first_resume) and first_resume['modelIsNull']
            row['checks']['firstVisibleResumeHasNoStaleJoin'] = actual_empty(first_visible) and joined_empty(first_visible) and independent_celestial(first_visible)
            row['checks']['resumeDoesNotReplayHiddenMotion'] = max(phase_progress(paused['actualCloud']['motion'], first_resume['actualCloud']['motion'])) < 0.002
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

        fixture = page.evaluate(FIXTURE)
        # Keep the first resumed raw snapshots as their own immutable artifacts;
        # avoid duplicating their large PNG strings inside the final trace.
        for key in ('resumeFirstRaf', 'resumeFirstVisible'):
            if key in fixture:
                fixture[key] = {'savedAs': 'resume-first-raf.json' if key == 'resumeFirstRaf' else 'resume-first-visible-publication.json'}
        row['fixture'] = fixture
        warm = [s for s in fixture['passive'] if s['modelIsNull'] and s['candidate']['eligible']]
        row['inclusiveBoundaryObservation'] = {'observed': bool(warm), 'samples': warm,
            'status': 'OBSERVED' if warm else 'NOT_NATURALLY_REACHED',
            'scope': 'The900000 ms inclusive source bound and midnight share one integer millisecond. No clock or render was forced to manufacture the overlap; deterministic source tests qualify the exact boundary separately.'}
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
        row['checks']['noNativeRendererErrors'] = all(not (s['celestial'].get('refined') or {}).get('errors')
            and not (s['celestial'].get('preview') or {}).get('catalogueError')
            and not (s['celestial'].get('moonRuntime') or {}).get('errors') for s in observed)
        row['checks']['sameTargetAndScene'] = all(s['target'] == current['target'] and s['sceneIdentity'] == current['sceneIdentity'] and s['runtimeGeneration'] == current['runtimeGeneration'] for s in observed)
        trace = [s for s in fixture['passive'] if s['elapsedMs'] >= current['elapsedMs']]
        first_motion = current['actualCloud']['motion']
        row['checks']['populationAndSeedRetained'] = all(s['motion']['key'] == first_motion['key'] and s['motion']['population'] == first_motion['population'] and s['motion']['fieldSeed'] == first_motion['fieldSeed'] for s in trace)
        row['checks']['boundedPhaseSteps'] = all(max(phase_progress(a['motion'], b['motion']), default=0) <= max(0.03, (b['elapsedMs'] - a['elapsedMs']) / 1000 * 0.05)
                                                     for a, b in zip(trace, trace[1:]))
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
        row['checks']['noErrors'] = not row['pageErrors'] and not row['consoleErrors'] and not fixture.get('consoleErrors') and not fixture.get('error') and not teardown_errors
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
