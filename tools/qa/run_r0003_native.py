"""R0003 bounded native observation: configuration-effect classification through the REAL in-widget settings UI.

Each cell runs in a fresh browser context on the served product files (unchanged, from --root) with every provider
host stubbed by Playwright routes (prayer/Aladhan, weather/Open-Meteo, radar/RainViewer + tile, coarse area/GeoJS);
any other non-local request is aborted, so no live provider request is ever made. The page clock is the real one.
Requests to each stubbed host are counted in the driver. Cells (owner decision D6/D10):
  label, time12, dateLong, identical, appearance  - cosmetic edit via settings open/edit/close: no new provider
      request, generation/scene/zone diagnostics unchanged, card updated, 325x530 card and key boxes unchanged;
  genuine    - coordinates changed in settings: new generation, new requests, old owner invalidated;
  race       - A held in flight, settings move to B (held), cosmetic label edit, late A released (must be rejected),
               then B released (must commit), label shown;
  saveRetry  - config storage fails (init-script Storage stub for the config key only): R0011 warning, failing and
               then successful retry of the unchanged config: reported outcome, no restart;
  reset      - #local=1 coarse-detected config, then settings Reset detecting the SAME values: real broad reset;
  hidden     - visibility forced hidden (the widget's own visibilitychange handler), cosmetic edit, no background
               render; first resumed frame shows the change.
The report JSON records argv, headed flag, engine/browser version and sha256 of the served files.
"""
import argparse, functools, hashlib, http.server, json, struct, sys, threading, time, zlib
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
HASH = '#preferLocal=1&lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&units=c&qa=1'
INIT = r"""(()=>{
 const set=Storage.prototype.setItem;
 Storage.prototype.setItem=function(k,v){ if(window.__r0003FailStore&&String(k).startsWith('salah_widget:config'))
   throw new DOMException('fixture denied','SecurityError'); return set.call(this,k,v); };
})();"""
DIAG = """()=>{const c=document.querySelector('.c'),box=s=>{const e=document.querySelector(s);if(!e)return null;const r=e.getBoundingClientRect();
 return [Math.round(r.left*10)/10,Math.round(r.top*10)/10,Math.round(r.width*10)/10,Math.round(r.height*10)/10];};
 const ce=document.querySelector('#ce'),nt=document.querySelector('.foc .nt'),cr=c.getBoundingClientRect();
 const tms=[...document.querySelectorAll('.times .p')].map(p=>{const r=p.getBoundingClientRect(),t=p.querySelector('.tm').getBoundingClientRect();
   return {text:p.textContent,inside:t.left>=r.left-0.5&&t.right<=r.right+0.5}});
 return {generation:_runtimeGeneration,hostGeneration:window.SalahMoonHost?SalahMoonHost.capture().generation:null,
  sceneKey:_skySceneKey,tz,cacheTz:_cacheTz,todayTag:today&&today.tag||null,todayLoaded:!!today,loop:_loopStarted,
  slots:Object.fromEntries(Object.entries(_requestSlots).map(([k,v])=>[k,v&&v.operationId])),
  persist:typeof _persistOutcome!=='undefined'&&_persistOutcome?_persistOutcome.status:null,
  warning:document.querySelector('.buckle').classList.contains('persist-warning'),
  buckleLabel:document.querySelector('.buckle').getAttribute('aria-label'),
  paused:c.classList.contains('paused'),appearance:c.dataset.appearance,
  loc:document.querySelector('#loc').textContent,locTruncatedByCss:(e=>e.scrollWidth>e.clientWidth+0.5)(document.querySelector('#loc')),nt:nt?nt.textContent:null,ce:ce.textContent,ah:document.querySelector('#ah').textContent,
  ceAria:document.querySelector('#ceDateButton').getAttribute('aria-label'),ceTruncated:ce.scrollWidth>ce.clientWidth+0.5,
  ntInsideCard:nt?nt.getBoundingClientRect().right<=cr.right+0.5&&nt.getBoundingClientRect().left>=cr.left-0.5:null,
  times:tms,boxes:{card:box('.c'),header:box('.h'),loc:box('#loc'),buckle:box('.buckle'),nt:box('.foc .nt'),times:box('.times'),footer:box('.d'),ce:box('#ce'),ah:box('#ah')}};}"""
READY = "()=>{try{return !!today&&_loopStarted&&!document.querySelector('.c').classList.contains('settings-open')}catch(e){return false}}"


def tile_png():
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    raw = (b'\0' + bytes([82, 147, 196, 255]) * 256) * 256
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', 256, 256, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


def rel(arg):
    """Report paths relative to the repository; anything outside it is reduced to its last component."""
    try:
        path = Path(arg)
        if not path.is_absolute():
            return arg.replace(chr(92), '/')
        try:
            return path.resolve().relative_to(REPO).as_posix()
        except ValueError:
            return '<outside-repository>/' + path.name
    except Exception:
        return arg


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def wait(page, predicate, timeout=30000):
    end = time.monotonic() + timeout / 1000
    while time.monotonic() < end:
        try:
            if page.evaluate(predicate):
                return True
        except Exception:
            pass
        page.wait_for_timeout(100)
    return False


class Stubs:
    """Controlled provider responses and per-host request counts for one context."""
    def __init__(self, record, png):
        self.record, self.png = record, png
        self.counts = {'prayer': 0, 'weather': 0, 'radar': 0, 'tile': 0, 'coarse': 0, 'aborted': 0}
        self.hold, self.held, self.urls = False, [], []
        self.tag = 'A'

    def prayer_body(self, url, tag):
        day = url.split('/timings/')[1].split('?')[0]
        d, m, y = day.split('-'); r = json.loads(json.dumps(self.record)); r['tag'] = tag
        r['date']['gregorian'].update(date=day, day=d, month={'number': int(m), 'en': MONTHS[int(m) - 1]}, year=y)
        return json.dumps({'code': 200, 'status': 'OK', 'data': r})

    def prayer(self, route):
        self.counts['prayer'] += 1; self.urls.append(route.request.url)
        if self.hold:
            self.held.append((route, self.tag)); return
        route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=self.prayer_body(route.request.url, self.tag))

    def release(self, index):
        route, tag = self.held[index]
        route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=self.prayer_body(route.request.url, tag))

    def weather(self, route):
        self.counts['weather'] += 1
        now = time.time() * 1000; iso = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).strftime('%Y-%m-%dT%H:%M')
        m, h = (now // 60000) * 60000, (now // 3600000) * 3600000
        body = {'timezone': 'UTC', 'elevation': 600, 'current': {'time': iso(m), 'interval': 900, 'weather_code': 3, 'temperature_2m': 20,
                'apparent_temperature': 19, 'relative_humidity_2m': 40, 'dew_point_2m': 6, 'wind_speed_10m': 2, 'wind_direction_10m': 180,
                'wind_gusts_10m': 4, 'cloud_cover': 90, 'precipitation': 0, 'is_day': 1},
                'hourly': {'time': [iso(h), iso(h + 3600000)], 'temperature_2m': [20, 19], 'weather_code': [3, 3], 'precipitation': [0, 0]}}
        route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=json.dumps(body))

    def radar(self, route):
        self.counts['radar'] += 1; s = int(time.time())
        route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'},
                      body=json.dumps({'generated': s, 'host': 'https://tilecache.rainviewer.com', 'radar': {'past': [{'time': s, 'path': f'/v2/radar/{s}'}]}}))

    def tile(self, route):
        self.counts['tile'] += 1
        route.fulfill(status=200, content_type='image/png', headers={'Access-Control-Allow-Origin': '*'}, body=self.png)

    def coarse(self, route):
        self.counts['coarse'] += 1
        route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'},
                      body=json.dumps({'latitude': '21.42', 'longitude': '39.83', 'city': 'Makkah', 'region': 'Makkah', 'country': 'Saudi Arabia',
                                       'country_code': 'SA', 'timezone': 'UTC', 'accuracy': 20}))

    def abort(self, route):
        self.counts['aborted'] += 1; route.abort()


def run(engine, root, out, headed, cells, tag):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_address[1]}/index.html'
    record = json.loads((REPO / 'tests/r0002-ordinary.json').read_text(encoding='utf-8'))
    report = {'driver': 'tools/qa/run_r0003_native.py', 'argv': [rel(a) for a in sys.argv], 'python': rel(sys.executable), 'headed': headed, 'engine': engine, 'tag': tag,
              'root': 'repository' if root.resolve() == REPO else root.name,
              'servedSha256': {f: sha(root / f) for f in ('index.html', 'config.js', 'offline.html', 'src/native/index.html')},
              'startedUtc': datetime.now(timezone.utc).isoformat(), 'cells': {}}
    png = tile_png()
    with sync_playwright() as p:
        browser = getattr(p, engine).launch(headless=not headed)
        report['browserVersion'] = browser.version

        def open_page(hash_=HASH):
            ctx = browser.new_context(viewport={'width': 325, 'height': 530}, timezone_id='UTC')
            ctx.add_init_script(INIT)
            st = Stubs(record, png); page = ctx.new_page(); log = []
            page.on('console', lambda m: log.append([m.type, m.text]) if m.type in ('error', 'warning') else None)
            page.on('pageerror', lambda e: log.append(['pageerror', str(e)]))
            page.route(lambda u: not u.startswith('http://127.0.0.1'), st.abort)          # later registrations win
            page.route('https://api.aladhan.com/**', st.prayer)
            page.route('https://api.open-meteo.com/**', st.weather)
            page.route('https://api.rainviewer.com/**', st.radar)
            page.route('https://tilecache.rainviewer.com/**', st.tile)
            page.route('https://get.geojs.io/**', st.coarse)
            return ctx, page, st, log

        def shot(page, name):
            page.screenshot(path=str(out / f'{tag}-{name}.png'))

        def diag(page):
            return page.evaluate(DIAG)

        def settle(page, ms=1500):
            page.wait_for_timeout(ms)
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')

        def settings(page, edit):
            page.click('.buckle'); page.wait_for_selector('.c.settings-open', timeout=5000)
            edit(page)
            page.click('#setClose'); page.wait_for_timeout(50)

        def cosmetic(name, edit, check):
            ctx, page, st, log = open_page(); page.goto(base + HASH)
            ready = wait(page, READY); settle(page)
            before, counts = diag(page), dict(st.counts); shot(page, f'{name}-1-before')
            settings(page, edit); settle(page)
            after, counts2 = diag(page), dict(st.counts); shot(page, f'{name}-2-after')
            same = {k: before[k] == after[k] for k in ('generation', 'hostGeneration', 'sceneKey', 'tz', 'cacheTz', 'slots', 'todayTag')}
            geometry = {k: before['boxes'][k] == after['boxes'][k] for k in ('card', 'header', 'buckle', 'times', 'footer')}
            providers = {k: counts2[k] == counts[k] for k in ('prayer', 'weather', 'radar', 'coarse')}
            ok, detail = check(before, after)
            report['cells'][name] = {'pass': bool(ready and all(same.values()) and all(geometry.values()) and all(providers.values()) and ok),
                                     'ready': ready, 'unchanged': same, 'geometryUnchanged': geometry, 'noNewProviderRequest': providers,
                                     'presentation': detail, 'counts': [counts, counts2], 'before': before, 'after': after, 'console': log}
            ctx.close()

        if 'label' in cells:
            cosmetic('label', lambda pg: pg.fill('#set-label', 'Fixture Renamed'),
                     lambda b, a: (a['loc'] == 'Fixture Renamed', {'loc': [b['loc'], a['loc']]}))
        if 'time12' in cells:
            cosmetic('time12', lambda pg: pg.select_option('#set-time', '12'),
                     lambda b, a: (a['nt'] is not None and a['nt'].endswith(('AM', 'PM')) and a['ntInsideCard'] and all(t['inside'] for t in a['times'])
                                   and all(t['text'].endswith(('AM', 'PM')) for t in a['times']), {'nt': [b['nt'], a['nt']], 'times': [t['text'] for t in a['times']]}))
        if 'dateLong' in cells:
            def long_check(b, a):
                text = a['ceAria'].split(': ', 1)[-1]
                return (any(mo in text for mo in MONTHS) and a['ceAria'] != b['ceAria'] and a['ce'].replace('CE', '').strip() != '',
                        {'ce': [b['ce'], a['ce']], 'aria': [b['ceAria'], a['ceAria']], 'ceTruncatedByCssEllipsis': a['ceTruncated'], 'ceBox': a['boxes']['ce']})
            cosmetic('dateLong', lambda pg: pg.select_option('#set-datefmt-preset', 'DD MMMM YYYY'), long_check)
        if 'identical' in cells:
            cosmetic('identical', lambda pg: (pg.fill('#set-label', 'Fixture '), pg.fill('#set-label', 'Fixture')),
                     lambda b, a: (a['persist'] == 'saved' and a['loc'] == b['loc'] and a['nt'] == b['nt'], {'persist': a['persist']}))
        if 'appearance' in cells:
            cosmetic('appearance', lambda pg: pg.select_option('#set-appearance', 'contrast'),
                     lambda b, a: (a['appearance'] == 'contrast', {'appearance': [b['appearance'], a['appearance']]}))

        if 'genuine' in cells:
            ctx, page, st, log = open_page(); page.goto(base + HASH); ready = wait(page, READY); settle(page)
            before, c0 = diag(page), dict(st.counts)
            settings(page, lambda pg: (pg.fill('#set-lat', '21.42'), pg.fill('#set-lon', '39.83')))
            fresh = wait(page, READY); settle(page); after, c1 = diag(page), dict(st.counts); shot(page, 'genuine-after')
            moved = any('latitude=21.42' in u for u in st.urls)
            report['cells']['genuine'] = {'pass': bool(ready and fresh and after['generation'] == before['generation'] + 1 and c1['prayer'] > c0['prayer']
                                                      and c1['weather'] > c0['weather'] and moved),
                                          'generation': [before['generation'], after['generation']], 'counts': [c0, c1], 'newTargetRequested': moved,
                                          'before': before, 'after': after, 'console': log}
            ctx.close()

        if 'race' in cells:
            ctx, page, st, log = open_page(); st.hold = True; st.tag = 'A'; page.goto(base + HASH)
            wait(page, "()=>document.querySelector('.buckle').classList.contains('interactive')")
            end = time.monotonic() + 20
            while not st.held and time.monotonic() < end:
                page.wait_for_timeout(100)
            st.tag = 'B'
            settings(page, lambda pg: (pg.fill('#set-lat', '21.42'), pg.fill('#set-lon', '39.83')))
            end = time.monotonic() + 20
            while len(st.held) < 2 and time.monotonic() < end:
                page.wait_for_timeout(100)
            g_b, n_b = page.evaluate('()=>_runtimeGeneration'), st.counts['prayer']
            settings(page, lambda pg: pg.fill('#set-label', 'Fixture During B')); page.wait_for_timeout(500)
            g_c, n_c = page.evaluate('()=>_runtimeGeneration'), st.counts['prayer']
            st.release(0); page.wait_for_timeout(1500)
            after_a = diag(page)
            if len(st.held) > 1:
                st.release(1)
            committed = wait(page, "()=>!!today&&today.tag==='B'", 15000); settle(page)
            final = diag(page); shot(page, 'race-after')
            for i in range(2, len(st.held)):
                st.release(i)
            report['cells']['race'] = {'pass': bool(len(st.held) >= 2 and g_c == g_b and n_c == n_b and after_a['todayTag'] is None and committed
                                                   and final['loc'] == 'Fixture During B'),
                                       'heldPrayerRequests': len(st.held), 'heldUrls': [r.request.url for r, _ in st.held],
                                       'generationAtB': g_b, 'generationAfterCosmetic': g_c, 'prayerRequestsAtB': n_b, 'prayerRequestsAfterCosmetic': n_c,
                                       'afterLateA': {'todayTag': after_a['todayTag']}, 'bCommitted': committed, 'final': final, 'console': log}
            ctx.close()

        if 'saveRetry' in cells:
            ctx, page, st, log = open_page(); page.goto(base + HASH); ready = wait(page, READY); settle(page)
            g0, c0 = diag(page), dict(st.counts)
            page.evaluate('()=>{window.__r0003FailStore=true}')
            settings(page, lambda pg: pg.fill('#set-label', 'Fixture Session')); settle(page); failed = diag(page); shot(page, 'saveRetry-1-failed')
            settings(page, lambda pg: (pg.fill('#set-label', 'Fixture Session '), pg.fill('#set-label', 'Fixture Session'))); settle(page)
            retry_fail = diag(page)
            page.evaluate('()=>{window.__r0003FailStore=false}')
            settings(page, lambda pg: (pg.fill('#set-label', 'Fixture Session '), pg.fill('#set-label', 'Fixture Session'))); settle(page)
            retry_ok, c1 = diag(page), dict(st.counts); shot(page, 'saveRetry-2-saved')
            stored = page.evaluate("()=>JSON.parse(localStorage.getItem('salah_widget:config:v1')||'null')")
            report['cells']['saveRetry'] = {'pass': bool(ready and failed['persist'] == 'session-only' and failed['warning'] and retry_fail['persist'] == 'session-only'
                                                        and retry_fail['warning'] and retry_ok['persist'] == 'saved' and not retry_ok['warning']
                                                        and stored and stored.get('label') == 'Fixture Session'
                                                        and retry_ok['generation'] == g0['generation'] == failed['generation']
                                                        and all(c1[k] == c0[k] for k in ('prayer', 'weather', 'radar'))),
                                            'generation': [g0['generation'], failed['generation'], retry_fail['generation'], retry_ok['generation']],
                                            'persist': [failed['persist'], retry_fail['persist'], retry_ok['persist']],
                                            'warning': [failed['warning'], retry_fail['warning'], retry_ok['warning']],
                                            'buckleLabel': [failed['buckleLabel'], retry_ok['buckleLabel']], 'counts': [c0, c1], 'storedLabel': stored and stored.get('label'),
                                            'console': log}
            ctx.close()

        if 'reset' in cells:
            ctx, page, st, log = open_page(); page.goto(base + '#local=1&qa=1'); ready = wait(page, READY); settle(page)
            before, c0 = diag(page), dict(st.counts)
            equal = page.evaluate("()=>typeof classifyConfigChange==='function'?classifyConfigChange(CONFIG,SalahConfig.normalize(JSON.parse(JSON.stringify(CONFIG))),{reset:false}).path:null")
            page.click('.buckle'); page.wait_for_selector('.c.settings-open', timeout=5000)
            page.click('#set-reset')
            reset = wait(page, f"()=>_runtimeGeneration>{before['generation']}&&!!today", 20000); settle(page)
            after, c1 = diag(page), dict(st.counts); shot(page, 'reset-after')
            page.click('#setClose')
            report['cells']['reset'] = {'pass': bool(ready and reset and c1['coarse'] == c0['coarse'] + 1 and c1['prayer'] > c0['prayer']
                                                    and after['generation'] == before['generation'] + 1),
                                        'detectedEqualClassifiedWithoutIntent': equal, 'generation': [before['generation'], after['generation']],
                                        'counts': [c0, c1], 'loc': [before['loc'], after['loc']], 'console': log}
            ctx.close()

        if 'hidden' in cells:
            ctx, page, st, log = open_page(); page.goto(base + HASH); ready = wait(page, READY); settle(page)
            before, c0 = diag(page), dict(st.counts)
            page.evaluate("()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'hidden'});document.dispatchEvent(new Event('visibilitychange'));}")
            page.wait_for_timeout(300); paused = diag(page)
            settings(page, lambda pg: (pg.select_option('#set-time', '12'), pg.select_option('#set-datefmt-preset', 'DD MMMM YYYY')))
            page.wait_for_timeout(1500); held = diag(page)
            page.evaluate("()=>{Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'visible'});document.dispatchEvent(new Event('visibilitychange'));}")
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))'); resumed, c1 = diag(page), dict(st.counts)
            shot(page, 'hidden-resumed')
            report['cells']['hidden'] = {'pass': bool(ready and paused['paused'] and held['nt'] == before['nt'] and held['ce'] == before['ce']
                                                     and not resumed['paused'] and resumed['nt'].endswith(('AM', 'PM')) and any(m in resumed['ce'] for m in MONTHS)
                                                     and resumed['generation'] == before['generation'] and all(c1[k] == c0[k] for k in ('prayer', 'weather', 'radar'))),
                                         'nt': [before['nt'], held['nt'], resumed['nt']], 'ce': [before['ce'], held['ce'], resumed['ce']],
                                         'paused': [paused['paused'], resumed['paused']], 'generation': [before['generation'], resumed['generation']],
                                         'counts': [c0, c1], 'console': log}
            ctx.close()
        browser.close()
    server.shutdown()
    report['finishedUtc'] = datetime.now(timezone.utc).isoformat()
    report['pass'] = all(v['pass'] for v in report['cells'].values())
    (out / f'{tag}-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'engine': engine, 'tag': tag, 'version': report['browserVersion'], 'pass': report['pass'],
                      'cells': {k: v['pass'] for k, v in report['cells'].items()}}))
    return report['pass']


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--engine', choices=['chromium', 'firefox'], required=True)
    a.add_argument('--root', default=str(REPO))
    a.add_argument('--out', required=True)
    a.add_argument('--tag', default=None)
    a.add_argument('--headed', action='store_true')
    a.add_argument('--cells', default='label,time12,dateLong,identical,appearance,genuine,race,saveRetry,reset,hidden')
    o = a.parse_args(); out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    sys.exit(0 if run(o.engine, Path(o.root), out, o.headed, o.cells.split(','), o.tag or o.engine) else 1)
