"""Serial R000C consumer qualification, adapted from the retained C weather driver.

Controlled fetch returns native Responses; no provider/ground-observation claim.
Product script bodies and assets remain unchanged. Record native video only while
the context is live, following the successful R0006 video-only recording mode.
"""
import argparse
import functools
import hashlib
import http.server
import json
import math
import os
from pathlib import Path
import struct
import sys
import threading
import time
import traceback
from urllib.parse import urlencode, unquote, urlsplit
import zlib


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_evidence(value):
    # Native diagnostic NaN/Infinity are not JSON numbers. Preserve their type
    # explicitly; never coerce them into a missing or valid weather measurement.
    if isinstance(value, float) and not math.isfinite(value):
        return {'$nativeNonFiniteNumber': 'NaN' if math.isnan(value) else 'Infinity' if value > 0 else '-Infinity'}
    if isinstance(value, dict):
        return {k: json_evidence(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_evidence(v) for v in value]
    return value


def dump(path, value):
    path.write_text(json.dumps(json_evidence(value), indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def wait(page, predicate, timeout=45000):
    end = time.monotonic() + timeout / 1000
    while time.monotonic() < end:
        if page.evaluate(predicate):
            return
        page.wait_for_timeout(200)
    raise TimeoutError('Predicate did not become true: ' + predicate)


def tile_png():
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    raw = (b'\0' + bytes([130, 123, 105, 73]) * 256) * 256
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', 256, 256, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


READ = '() => __smokeWeather.read(__smokeWeather.identity())'
READY = "() => {const f=window.__widgetFixture,b=window.__smokeWeather;if(f?.state==='error')throw Error(f.error);if(f?.state!=='ready'||!b)return false;const s=b.read(b.identity());return s.qa.cache.prayerLoaded&&s.modelEligible&&!s.wxBusy&&!s.radarBusy&&s.radar?.sample&&s.qa.weatherHeader?.rawCode===95;}"
# Read the existing admitted record and DOM only. qaState() also reads canvas
# pixels and lunar getters, so it is not a passive recovery polling operation.
RECOVERED_PASSIVE = """() => {
    const b=window.__smokeWeather;
    window.__fixtureClock.assertOwned(b.identity());
    const particles=[...document.querySelectorAll('.drop,.flake')].filter(e=>{
        const s=getComputedStyle(e);
        return s.display!=='none'&&s.visibility==='visible'&&+s.opacity>.03;
    }).length;
    return weather?.precip===2&&document.querySelector('.c').dataset.precip==='on'&&particles>0;
}"""


def check(snapshot, fixture, temp, precip, expected_source):
    wet = precip is not None and precip > 0
    truth = snapshot['qa']['wxTruth']
    checks = {
        'exactSource': fixture['sourceSha256'] == expected_source,
        'isolatedIngress': fixture['storageIsolated'] and fixture['clockIsolated'] and fixture['fetchIntercepted'],
        'nativeResponseConsumed': any('api.open-meteo.com/v1/forecast' in r['url'] and r.get('jsonSettled') and r['jsonReads'] == 1 for r in fixture['ledger']),
        'temperatureAdmitted': snapshot['raw']['temp'] == temp,
        'temperatureCached': snapshot['cached']['w']['temp'] == temp,
        'temperatureHeader': snapshot['temperature'] == ('' if temp is None else str(temp) + '°'),
        'precipitationAdmitted': snapshot['raw']['precip'] == precip,
        'precipitationCached': snapshot['cached']['w']['precip'] == precip,
        'conditionRetained': snapshot['icon'] == '⛈️' and snapshot['fx'] == 'thunder',
        'modelDisclosure': 'current model estimate' in snapshot['headerLabel'] and 'direct local observation unavailable' in snapshot['headerLabel'],
        'effectDataset': snapshot['precip'] == ('on' if wet else 'off'),
        'particles': snapshot['visibleParticles'] > 0 if wet else snapshot['visibleParticles'] == 0,
        'noLightning': snapshot['lightning'] == 'off' and not truth['visualPermissions']['lightning'],
        'notObserved': truth['observedPresent'] is False,
        'radarNoAmount': truth['radarPrecipMm'] == 0 and snapshot['radar']['precipMm'] == 0 and truth['radarConfirming'] is False,
        'cardGeometry': snapshot['card'] == {'width': 325, 'height': 530},
        'footerFits': snapshot['footer']['top'] >= 0 and snapshot['footer']['bottom'] <= 530.1,
        'readOnlyBridge': all(e['action'] == 'consumer-read' for e in fixture['weatherEvents']),
    }
    if precip is None:
        checks['invalidAmountReason'] = snapshot['raw']['admission'].get('precip') == 'invalid measurement'
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--browser', choices=['chromium', 'firefox'], required=True)
    parser.add_argument('--python-packages', type=Path, required=True)
    parser.add_argument('--case-id', action='append')
    parser.add_argument('--headed', action='store_true')
    parser.add_argument('--single-document', action='store_true')
    parser.add_argument('--boundary-observer', action='store_true',
        help='Night only: unchanged full assertions at watch boundaries; passive recovery polling and no diagnostic reads inside watches')
    parser.add_argument('--host-watch-wait', action='store_true',
        help='Headed boundary-observer only: use the retained preservation driver host sleep during each unchanged watch')
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    if out.is_relative_to(root):
        raise ValueError('Keep original acquisitions outside the checkout')
    out.mkdir(parents=True, exist_ok=False)
    packet = json.loads(args.cases.read_bytes())
    for rel, digest in packet['sourceFiles'].items():
        if sha((root / rel).read_bytes()) != digest:
            raise ValueError('Source drift: ' + rel)
    sys.path.insert(0, str(root / 'tools/cp9'))
    sys.path.insert(0, str(args.python_packages.resolve()))
    from browser_runtime import browser_options, browser_identity
    from runtime_identity import runtime_identity
    from playwright.sync_api import sync_playwright
    before = runtime_identity(root)
    if before['treeSha256'] != packet['runtime']['treeSha256']:
        raise ValueError('Runtime drift')
    selected = [c for c in packet['cases'] if not args.case_id or c['id'] in args.case_id]
    if not selected or args.case_id and {c['id'] for c in selected} != set(args.case_id):
        raise ValueError('Empty or unknown case selection')
    if args.boundary_observer and any(not c.get('night') for c in selected):
        raise ValueError('Boundary observer is scoped to the night recovery cases')
    if args.host_watch_wait and not (args.boundary_observer and args.headed):
        raise ValueError('Host watch wait requires the headed boundary-observer mode')
    wrapper = root / 'tests/rlgwo/weather-browser-fixture.html'
    served_wrapper = wrapper.read_bytes()
    document_binding = None
    if args.single_document:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from r000c_single_document import prepare
        served_wrapper, document_binding = prepare((root / 'index.html').read_bytes(), served_wrapper)
        dump(out / 'single-document-binding.json', document_binding)
    tile = tile_png()
    requests = []

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            path = unquote(urlsplit(self.path).path)
            requests.append({'path': path, 'hostMonotonic': time.monotonic()})
            if path == '/fixture.html':
                data, mime = served_wrapper, 'text/html; charset=utf-8'
            elif path.startswith('/tile/'):
                data, mime = tile, 'image/png'
            elif path.startswith('/product/'):
                target = (root / path[len('/product/'):]).resolve()
                if not target.is_relative_to(root) or not target.is_file():
                    self.send_error(404)
                    return
                data, mime = target.read_bytes(), self.guess_type(str(target))
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)

    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = 'http://127.0.0.1:' + str(server.server_port)
    os.environ['SALAH_BROWSER'] = args.browser
    report = {'schema': 'r000c-native-acquisition/v1', 'status': 'RUNNING', 'runtime': before,
              'sourceCommit': packet['sourceCommit'], 'casesSha256': sha(args.cases.read_bytes()),
              'driverSha256': sha(Path(__file__).read_bytes()), 'wrapperSha256': sha(wrapper.read_bytes()),
              'servedHtmlSha256': sha(served_wrapper), 'documentMode': 'single-document-preparse' if args.single_document else 'original-document-wrapper',
              'observerMode': 'full-diagnostic-boundaries-passive-recovery' if args.boundary_observer else 'original-full-diagnostic-every-five-seconds',
              'watchWaitMode': 'host-monotonic-sleep' if args.host_watch_wait else 'browser-timeout',
              'tileSha256': sha(tile), 'cases': [], 'limitations': __doc__}
    dump(out / 'results.json', report)
    try:
        with sync_playwright() as pw:
            for number, case in enumerate(selected, 1):
                case_out = out / case['id']
                case_out.mkdir()
                dump(case_out / 'case-input.json', case)
                row = {'id': case['id'], 'status': 'FAIL', 'observations': [], 'checks': {},
                       'observerMode': report['observerMode'], 'watchWaitMode': report['watchWaitMode'], 'watches': []}
                browser = context = page = None
                errors = []
                try:
                    family, options = browser_options()
                    if args.headed:
                        options['headless'] = False
                    browser = getattr(pw, family).launch(**options)
                    executable = options.get('executable_path') or getattr(pw, family).executable_path
                    row['browser'] = {**browser_identity(browser), 'headless': options['headless'],
                                      'executable': executable, 'executableSha256': sha(Path(executable).read_bytes())}
                    context = browser.new_context(viewport={'width': 390, 'height': 600}, device_scale_factor=1,
                        timezone_id='Asia/Riyadh', reduced_motion=case['motionPreference'],
                        record_video_dir=str(case_out / 'video'), record_video_size={'width': 390, 'height': 600})
                    page = context.new_page()
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    config = {'lat': 24.47, 'lon': 39.61, 'tz': 'Asia/Riyadh', 'label': 'Madinah',
                              'method': 4, 'school': 0, 'units': 'c', 'seed': 1}
                    if case.get('night'):
                        config.update(simMoon=0.5, simMoonAlt=20, simMoonH=42)
                    if case.get('fullMotion'):
                        config['motion'] = 'full'
                    query = {'case': case['inputCase'], 'attempt': number, 'run': 'R000C-20261014', 'night': int(case.get('night', False))}
                    url = origin + '/fixture.html?' + urlencode(query) + '#' + urlencode(config)
                    row['url'] = url
                    row['navigationHostMonotonic'] = time.monotonic()
                    page.goto(url, wait_until='domcontentloaded', timeout=45000)
                    wait(page, READY)
                    wet = case['precip'] is not None and case['precip'] > 0
                    wait(page, "() => {const s=__smokeWeather.read(__smokeWeather.identity());return " +
                         ("s.precip==='on'&&s.visibleParticles>0" if wet else "s.precip==='off'&&s.visibleParticles===0") + ";}")

                    def capture(stage, temp, precip):
                        snapshot = page.evaluate(READ)
                        fixture = page.evaluate('() => __widgetFixture')
                        checks = check(snapshot, fixture, temp, precip, packet['sourceFiles']['index.html'])
                        row['checks'].update({stage + '/' + k: v for k, v in checks.items()})
                        observation = {'stage': stage, 'hostMonotonic': time.monotonic(), 'state': snapshot}
                        row['observations'].append(observation)
                        dump(case_out / (stage + '.json'), observation)
                        return snapshot

                    capture('initial', case['temp'], case['precip'])
                    watch_start = time.monotonic()
                    initial_reads = [case['watchSeconds']] if args.boundary_observer else range(5, case['watchSeconds'] + 1, 5)
                    for elapsed in initial_reads:
                        remaining = max(0, watch_start + elapsed - time.monotonic())
                        if args.host_watch_wait:
                            time.sleep(remaining)
                        else:
                            page.wait_for_timeout(remaining * 1000)
                        if elapsed == case['watchSeconds']:
                            row['watches'].append({'stage': 'initial', 'startHostMonotonic': watch_start,
                                'endHostMonotonic': time.monotonic(), 'requiredSeconds': case['watchSeconds']})
                        capture('initial-' + str(elapsed) + 's', case['temp'], case['precip'])
                    if case.get('night'):
                        # Recover only through the ordinary >=60-second ingress retry; never call fetchWeather.
                        recovery_predicate = RECOVERED_PASSIVE if args.boundary_observer else "() => {const s=__smokeWeather.read(__smokeWeather.identity());return s.raw?.precip===2&&s.precip==='on'&&s.visibleParticles>0;}"
                        wait(page, recovery_predicate, 65000)
                        capture('recovered', 20, 2)
                        recovered_start = time.monotonic()
                        recovered_reads = [30] if args.boundary_observer else range(5, 31, 5)
                        for elapsed in recovered_reads:
                            remaining = max(0, recovered_start + elapsed - time.monotonic())
                            if args.host_watch_wait:
                                time.sleep(remaining)
                            else:
                                page.wait_for_timeout(remaining * 1000)
                            if elapsed == 30:
                                row['watches'].append({'stage': 'recovered', 'startHostMonotonic': recovered_start,
                                    'endHostMonotonic': time.monotonic(), 'requiredSeconds': 30})
                            capture('recovered-' + str(elapsed) + 's', 20, 2)
                        row['checks']['movingWall'] = row['observations'][-1]['state']['wallUtcMs'] - row['observations'][0]['state']['wallUtcMs'] >= 60000
                    fixture = page.evaluate('() => __widgetFixture')
                    row['fixture'] = fixture
                    row['checks']['noPageErrors'] = not errors and not fixture['consoleErrors']
                    row['checks']['privateStorageInitiallyEmpty'] = fixture['initialStorageEntries'] == 0
                    if case['inputCase'] == '12-absent-temp':
                        bodies = [r['parsedBody']['current'] for r in fixture['ledger'] if 'api.open-meteo.com' in r['url'] and r.get('jsonSettled')]
                        row['checks']['propertyActuallyAbsent'] = bool(bodies) and all('temperature_2m' not in b for b in bodies)
                    try:
                        page.evaluate('() => __smokeWeather.read({...__smokeWeather.identity(),attempt:-1})')
                        row['checks']['wrongOwnerRejected'] = False
                    except Exception:
                        row['checks']['wrongOwnerRejected'] = True
                    row['status'] = 'PASS_ASSERTIONS_PENDING_PIXEL_REVIEW' if all(row['checks'].values()) else 'FAIL'
                except Exception:
                    row['exception'] = traceback.format_exc()
                finally:
                    row['pageErrors'] = errors
                    if context:
                        context.close()
                    if page and page.video:
                        video = Path(page.video.path())
                        row['video'] = {'file': video.relative_to(case_out).as_posix(), 'sha256': sha(video.read_bytes())}
                    if browser:
                        browser.close()
                    dump(case_out / 'receipt.json', row)
                    report['cases'].append({'id': row['id'], 'status': row['status'], 'receiptSha256': sha((case_out / 'receipt.json').read_bytes())})
                    dump(out / 'results.json', report)
                    print(case['id'], row['status'], flush=True)
    finally:
        server.shutdown()
        report['httpRequests'] = requests
        report['runtimeUnchanged'] = runtime_identity(root) == before
        report['status'] = 'PASS_ASSERTIONS_PENDING_PIXEL_REVIEW' if len(report['cases']) == len(selected) and all(c['status'] == 'PASS_ASSERTIONS_PENDING_PIXEL_REVIEW' for c in report['cases']) and report['runtimeUnchanged'] else 'FAIL'
        dump(out / 'results.json', report)
    return 0 if report['status'] == 'PASS_ASSERTIONS_PENDING_PIXEL_REVIEW' else 1


if __name__ == '__main__':
    raise SystemExit(main())
