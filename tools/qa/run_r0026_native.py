"""R0026 bounded native observation: external location admission and truthful search feedback.

Serves the GENERATED builder.html / index.html unchanged from --root on 127.0.0.1. Every non-local request is
intercepted at the browser-context level: provider hosts (GeoJS, ipinfo, Nominatim, Zippopotam, Aladhan) get
controlled fixture replies, everything else is aborted; nothing is continued to the network, and the report
lists every external request with its disposition. navigator.geolocation and the geolocation permission query
are init-script doubles returning fixture positions only; no real position or permission is ever requested.
Cells: builder detect (invalid GeoJS → fallback), admitted search, valid no-match, provider failure, partial
coverage, invalid browser position, stale success/error; widget boot detect, the same settings cells, and the
resulting config after close. This is a bounded UI-feedback observation, not provider-availability evidence.
"""
import argparse, functools, hashlib, http.server, json, sys, threading, time
from importlib import metadata
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
GEO_INIT = r"""(()=>{const g=window.__r0026Geo={pos:null,calls:0};
 const geo={getCurrentPosition(ok,bad){g.calls++;setTimeout(()=>{const p=g.pos;p?ok({coords:{latitude:p[0],longitude:p[1],accuracy:p[2]},timestamp:Date.now()}):bad({code:1,message:'fixture denied'});},50);},
  watchPosition(){return 0;},clearWatch(){}};
 Object.defineProperty(Navigator.prototype,'geolocation',{get(){return geo;},configurable:true});
 if(navigator.permissions){const q=navigator.permissions.query.bind(navigator.permissions);
  navigator.permissions.query=d=>d&&d.name==='geolocation'?Promise.resolve({state:'granted'}):q(d);}})();"""
PLACES = {'London': [('51.5', '-0.12', 'London', 'England', 'United Kingdom', 'gb')],
          'Cairo': [('30.04', '31.24', 'Cairo', 'Cairo', 'Egypt', 'eg')],
          'Paris': [('48.86', '2.35', 'Paris', 'Ile-de-France', 'France', 'fr')],
          'M5V2T6': [('43.64', '-79.39', 'Toronto', 'Ontario', 'Canada', 'ca')],
          'Oldtown': [('10.5', '20.5', 'Oldtown', 'Fixture', 'Fixture', 'fx')], 'Nowhere': []}
FAILING = {'Paris'}   # Nominatim answers HTTP 503 with a healthy-looking body for these queries


def nominatim_body(q):
    return [{'class': 'place', 'lat': a, 'lon': o, 'name': c, 'address': {'city': c, 'state': s, 'country': n, 'country_code': cc}}
            for a, o, c, s, n, cc in PLACES.get(q, [])]


def portable_argv(argv):
    # Record the command without local absolute paths: repository files relative to the repository, others by name.
    out = []
    for a in argv:
        p = Path(a)
        if p.is_absolute():
            try:
                a = p.resolve().relative_to(REPO).as_posix()
            except ValueError:
                a = '<external>/' + p.name
        out.append(a)
    return out


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def wait(page, predicate, arg=None, timeout=15000):
    end = time.monotonic() + timeout / 1000
    while time.monotonic() < end:
        try:
            if page.evaluate(predicate, arg):
                return True
        except Exception:
            pass
        page.wait_for_timeout(100)
    return False


def run(engine, root, out, headed, tag):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    class Server(http.server.ThreadingHTTPServer):
        def handle_error(self, request, client_address):   # client-side resets on page close are not findings
            report.setdefault('serverResets', 0); report['serverResets'] += 1
    report = {}
    server = Server(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_address[1]}'
    prayer_record = json.loads((REPO / 'tests/r0002-ordinary.json').read_text(encoding='utf-8'))
    report.update({'argv': portable_argv(sys.argv), 'engine': engine, 'headed': headed, 'playwright': metadata.version('playwright'),
              'root': 'repository' if root.resolve() == REPO else root.name,
              'served': {f: sha(root / f) for f in ('index.html', 'builder.html', 'config.js', 'offline.html')},
              'cells': {}, 'external': [], 'console': []})
    held, seen = [], []

    def provider(route):
        u = urlparse(route.request.url); host = u.hostname; q = parse_qs(u.query).get('q', [''])[0]
        def reply(status, body, why):
            report['external'].append([host, u.path, why]); route.fulfill(status=status, content_type='application/json',
                headers={'Access-Control-Allow-Origin': '*'}, body=json.dumps(body))
        if host == 'get.geojs.io':
            return reply(200, {'latitude': '999', 'longitude': '999', 'city': 'Fixture999', 'country_code': 'US'}, 'stub geojs invalid')
        if host == 'ipinfo.io':
            return reply(200, {'loc': '51.5,-0.12', 'city': 'London', 'country': 'GB', 'timezone': 'Europe/London'}, 'stub ipinfo')
        if host == 'api.zippopotam.us':
            return reply(503, {'error': 'fixture'}, 'stub zippopotam 503') if u.path == '/ca/M5V' else reply(404, {}, 'stub zippopotam 404')
        if host == 'nominatim.openstreetmap.org':
            if q == 'Oldtown':
                report['external'].append([host, u.path, 'stub nominatim held']); held.append(route); return None
            return reply(503 if q in FAILING else 200, nominatim_body(q), f'stub nominatim {q}')
        if host == 'api.aladhan.com':
            day = route.request.url.split('/timings/')[1].split('?')[0]; d, m, y = day.split('-')
            r = json.loads(json.dumps(prayer_record)); r['date']['gregorian'].update(date=day, day=d, month={'number': int(m), 'en': 'Fixture'}, year=y)
            return reply(200, {'code': 200, 'status': 'OK', 'data': r}, 'stub aladhan')
        report['external'].append([host, u.path, 'aborted']); route.abort()

    with sync_playwright() as p:
        browser = getattr(p, engine).launch(headless=not headed)
        report['browserVersion'] = browser.version
        cell = report['cells']

        def context(width, height):
            ctx = browser.new_context(viewport={'width': width, 'height': height})
            ctx.add_init_script(GEO_INIT)
            ctx.route(lambda url: not url.startswith(base), provider)
            ctx.on('request', lambda r: seen.append(r.url) if r.url.startswith('http') and not r.url.startswith(base) else None)
            page = ctx.new_page()
            page.on('console', lambda m: report['console'].append([m.type, m.text[:200]]) if m.type == 'error' else None)
            page.on('pageerror', lambda e: report['console'].append(['pageerror', str(e)[:200]]))
            return ctx, page

        # ---- builder ------------------------------------------------------------------------------------------
        ctx, page = context(1100, 900)
        tip = lambda: page.evaluate("()=>document.getElementById('geotip').textContent")
        tipinfo = lambda: page.evaluate("()=>{const e=document.getElementById('geotip');return {title:e.title,role:e.getAttribute('role'),ariaLive:e.getAttribute('aria-live'),scrollWidth:e.scrollWidth,clientWidth:e.clientWidth}}")
        form = lambda: page.evaluate("()=>[document.getElementById('lat').value,document.getElementById('lon').value]")
        shot = lambda name: page.screenshot(path=str(out / f'{tag}-builder-{name}.png'))

        def search(q, expect):
            page.fill('#label', q); page.press('#label', 'Enter')
            return wait(page, '(re)=>new RegExp(re).test(document.getElementById("geotip").textContent)', expect, 6000)
        page.goto(base + '/builder.html')
        ok = wait(page, "()=>/^(Detected|Couldn)/.test(document.getElementById('geotip').textContent)")
        cell['builderDetect'] = {'pass': ok and form() == ['51.50000', '-0.12000'] and tip().startswith('Detected: London'), 'tip': tip(), 'form': form()}; shot('1-detect')
        for name, q, want in (('builderAdmitted', 'London', ['51.50000', '-0.12000']), ('builderNoMatch', 'Nowhere', None),
                              ('builderUnavailable', 'Paris', None), ('builderPartial', 'M5V2T6', ['43.64000', '-79.39000'])):
            before = form(); settled = search(q, '^(?!Searching)'); t, f, ti = tip(), form(), tipinfo()
            good = {'builderAdmitted': t.startswith('Found: London'), 'builderNoMatch': t.startswith('No matching place found'),
                    'builderUnavailable': t == 'Search unavailable — a provider failed. Try again.'
                        and 'Try again, use the pin (browser location), or enter coordinates.' in ti['title'],
                    'builderPartial': t.startswith('Partial results, a provider failed: Toronto')}[name]
            # Meaning-first: the outcome must be fully visible (no ellipsis) and repeated in title, with status semantics.
            visible = ti['scrollWidth'] <= ti['clientWidth'] and ti['title'].startswith(t) and ti['role'] == 'status' and ti['ariaLive'] == 'polite'
            cell[name] = {'pass': settled and good and visible and f == (want or before), 'tip': t, 'tipElement': ti, 'form': f, 'formBefore': before}
            shot(name)
        before = form(); page.evaluate('()=>{window.__r0026Geo.pos=[999,10,20];}'); page.click('#geo')
        wait(page, "()=>!/^Requesting/.test(document.getElementById('geotip').textContent)", None, 5000)
        cell['builderInvalidPosition'] = {'pass': tip().startswith('Browser location invalid — not used') and form() == before, 'tipElement': tipinfo(), 'tip': tip(), 'form': form(), 'geoCalls': page.evaluate('()=>window.__r0026Geo.calls')}
        shot('invalid-position')
        for late in ('error', 'success'):
            page.fill('#label', 'Oldtown'); page.press('#label', 'Enter'); page.wait_for_timeout(300)
            found = search('Cairo', '^Found: Cairo'); current = (tip(), form())
            route = held.pop(0)
            if late == 'error':
                route.fulfill(status=503, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body='[]')
            else:
                route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=json.dumps(nominatim_body('Oldtown')))
            page.wait_for_timeout(1500)
            cell['builderStale_' + late] = {'pass': found and (tip(), form()) == current and current[1] == ['30.04000', '31.24000'], 'tip': tip(), 'form': form()}
        report['builderCode'] = page.evaluate("()=>document.getElementById('code').value.match(/src=\"([^\"]+)\"/)[1].split('#')[1]")
        ctx.close()

        # ---- widget (local mode: boot detection, then settings) ------------------------------------------------
        ctx, page = context(325, 530)
        status = lambda: page.evaluate("()=>document.getElementById('set-status').textContent.split('\\n').pop()")
        sform = lambda: page.evaluate("()=>[document.getElementById('set-lat').value,document.getElementById('set-lon').value]")
        sshot = lambda name: page.screenshot(path=str(out / f'{tag}-widget-{name}.png'))
        page.goto(base + '/index.html#local=1&qa=1')
        booted = wait(page, "()=>{try{return qaState().config.autoDetectStatus!=='pending'&&document.querySelector('.buckle.interactive')}catch(e){return false}}", None, 20000)
        cfg = page.evaluate("()=>{const c=qaState().config;return {lat:c.lat,lon:c.lon,label:c.label,status:c.autoDetectStatus,source:c.autoDetectSource}}")
        cell['widgetBootDetect'] = {'pass': booted and [cfg['lat'], cfg['lon']] == [51.5, -0.12], 'config': cfg}; sshot('1-boot')
        page.click('.buckle'); wait(page, "()=>document.querySelector('.c').classList.contains('settings-open')")

        def ssearch(q):
            page.fill('#set-label', q); page.press('#set-label', 'Enter')
            return wait(page, "()=>!/Searching/.test(document.getElementById('set-status').textContent)", None, 6000)
        for name, q, prefix, want in (('settingsNoMatch', 'Nowhere', 'Couldn’t find “Nowhere”', None), ('settingsUnavailable', 'Paris', 'Search unavailable for “Paris” — a provider failed', None),
                                      ('settingsPartial', 'M5V2T6', 'Partial results, a provider failed: Toronto', ['43.64000', '-79.39000']), ('settingsAdmitted', 'London', 'Found: London', ['51.50000', '-0.12000'])):
            before = sform(); settled = ssearch(q); s, f = status(), sform()
            cell[name] = {'pass': settled and s.startswith(prefix) and f == (want or before), 'status': s, 'form': f, 'formBefore': before,
                          'errClass': page.evaluate("()=>document.getElementById('set-status').classList.contains('err')")}
            sshot(name)
        before = sform(); page.evaluate('()=>{window.__r0026Geo.pos=[NaN,10,20];}'); page.click('#set-pin')
        wait(page, "()=>!/Requesting/.test(document.getElementById('set-status').textContent)", None, 5000)
        cell['settingsInvalidPosition'] = {'pass': 'invalid coordinates' in status() and sform() == before, 'status': status(), 'form': sform()}; sshot('invalid-position')
        page.fill('#set-label', 'Oldtown'); page.press('#set-label', 'Enter'); page.wait_for_timeout(300)
        found = ssearch('Cairo') and status().startswith('Found: Cairo'); current = (status(), sform())
        held.pop(0).fulfill(status=503, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body='[]'); page.wait_for_timeout(1500)
        cell['settingsStale_error'] = {'pass': found and (status(), sform()) == current, 'status': status(), 'form': sform()}
        page.click('#setClose'); page.wait_for_timeout(1500)
        cfg = page.evaluate("()=>{const c=qaState().config;return {lat:c.lat,lon:c.lon,label:c.label}}")
        cell['settingsResultingConfig'] = {'pass': [cfg['lat'], cfg['lon']] == [30.04, 31.24] and current[1] == ['30.04000', '31.24000'], 'config': cfg, 'formAtClose': current[1]}
        sshot('closed')
        ctx.close(); browser.close()
    server.shutdown()
    hosts = {urlparse(u).hostname for u in seen}
    handled = {(h, pth) for h, pth, _ in report['external']}
    report['externalHosts'] = sorted(hosts)
    report['unhandledExternal'] = [u for u in seen if (urlparse(u).hostname, urlparse(u).path) not in handled]
    report['noRequestLeft'] = not report['unhandledExternal'] and all(why != 'continued' for _, _, why in report['external'])
    report['pass'] = report['noRequestLeft'] and all(v['pass'] for v in report['cells'].values())
    (out / f'{tag}-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'engine': engine, 'version': report['browserVersion'], 'pass': report['pass'], 'noRequestLeft': report['noRequestLeft'],
                      'cells': {k: v['pass'] for k, v in report['cells'].items()}, 'consoleErrors': len(report['console'])}, ensure_ascii=False))
    return report['pass']


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--engine', choices=['chromium', 'firefox'], required=True)
    a.add_argument('--root', default=str(REPO))
    a.add_argument('--out', required=True)
    a.add_argument('--tag', default=None, help='file prefix (default: engine)')
    a.add_argument('--headed', action='store_true')
    o = a.parse_args(); out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    sys.exit(0 if run(o.engine, Path(o.root), out, o.headed, o.tag or o.engine) else 1)
