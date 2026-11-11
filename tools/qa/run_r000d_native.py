"""R000D bounded native observation: elapsed weather/radar retry spacing under a wall-clock correction.

An init script installs independent fixture clocks inside the page: wall (Date) = real time + offset, elapsed
(performance.now) = real time + offset, or pinned. The OS clock is never touched. Weather/radar provider
responses and the radar tile are controlled (no provider-availability or outage claim); the product files are
served unchanged from --root. Cells: accepted -> backward wall correction -> future-dated rejection ->
59 999/60 000 and 599 999/600 000 elapsed boundaries at the real product gate -> owned completion and visible
header recovery; then a second correction recovered through the ordinary visible loop poll only.
"""
import argparse, functools, http.server, json, struct, sys, threading, time, zlib
from pathlib import Path
from playwright.sync_api import sync_playwright

START = '2026-09-07T09:00:00Z'
INIT = r"""(()=>{
 const ND=Date,realPerf=performance.now.bind(performance),c={wallOffset:ND.parse('%START%')-ND.now(),monoOffset:0,pin:null};
 const wall=()=>ND.now()+c.wallOffset,iso=ms=>new ND(ms).toISOString().slice(0,16);
 class FixtureDate extends ND{constructor(...a){super(...(a.length?a:[wall()]));}static now(){return wall();}}
 window.Date=FixtureDate; performance.now=()=>c.pin!=null?c.pin:realPerf()+c.monoOffset;
 const calls=window.__r000dCalls={weather:0,radar:0},nf=window.fetch.bind(window);
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){calls.weather++;const w=wall(),m=Math.floor(w/60000)*60000,h=Math.floor(w/3600000)*3600000;
   return json({timezone:'UTC',elevation:600,current:{time:iso(m),interval:900,weather_code:3,temperature_2m:20,apparent_temperature:19,
    relative_humidity_2m:40,dew_point_2m:6,wind_speed_10m:2,wind_direction_10m:180,wind_gusts_10m:4,cloud_cover:90,precipitation:0,is_day:1},
    hourly:{time:[iso(h),iso(h+3600000)],temperature_2m:[20,19],weather_code:[3,3],precipitation:[0,0]}});}
  if(u.includes('api.rainviewer.com')){calls.radar++;const s=Math.floor(wall()/1000);
   return json({generated:s,host:'https://tilecache.rainviewer.com',radar:{past:[{time:s,path:'/v2/radar/'+s}]}});}
  return nf(input,init);};
 window.__r000dClock={stepWall(ms){c.wallOffset+=ms;},advance(ms){c.monoOffset+=ms;c.wallOffset+=ms;},pin(v){c.pin=v;},
  release(){if(c.pin!=null){c.monoOffset=c.pin-realPerf();c.pin=null;}},read(){return {wall:wall(),mono:performance.now()};}};
})();""".replace('%START%', START)
SNAP = """()=>{const q=qaState();return {clock:__r000dClock.read(),calls:{...__r000dCalls},wt:document.querySelector('#wt')?.textContent??null,
 fx:document.querySelector('.c')?.dataset.fx??null,currentEligible:q.cache.currentEligible,weatherAgeSec:q.cache.weatherAgeSec,
 radarAvailable:q.wxTruth.radarAvailable,radarAgeSec:q.wxTruth.radarAgeSec,requests:q.wxTruth.requests,retry:q.wxTruth.retry??null,
 wxBusy,radarBusy}}"""
BOUNDARY = """([kind,interval])=>{const call=kind==='weather'?fetchWeather:fetchRadar,s=_wxRetry[kind].startedAt,n=()=>__r000dCalls[kind];
 const n0=n();__r000dClock.pin(s+interval-1);const before=qaState().wxTruth.retry[kind];call();const n1=n();
 __r000dClock.pin(s+interval);call();const n2=n();__r000dClock.release();return {startedAt:s,n0,n1,n2,stateBefore:before.state,nextBefore:before.nextEligibleInMs};}"""


def tile_png():
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    raw = (b'\0' + bytes([82, 147, 196, 255]) * 256) * 256
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', 256, 256, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


def prayer(route, record):
    day = route.request.url.split('/timings/')[1].split('?')[0]
    d, m, y = day.split('-'); r = json.loads(json.dumps(record))
    r['date']['gregorian'].update(date=day, day=d, month={'number': int(m), 'en': 'Fixture'}, year=y)
    route.fulfill(status=200, content_type='application/json', body=json.dumps({'code': 200, 'status': 'OK', 'data': r}))


def wait(page, predicate, timeout=30000):
    end = time.monotonic() + timeout / 1000
    while time.monotonic() < end:
        if page.evaluate(predicate):
            return True
        page.wait_for_timeout(100)
    return False


def run(engine, root, out, headed, cells):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    record = json.loads((Path(__file__).resolve().parents[2] / 'tests/r0002-ordinary.json').read_text(encoding='utf-8'))
    report = {'engine': engine, 'root': 'repository' if root.resolve() == Path(__file__).resolve().parents[2] else root.name, 'start': START, 'cells': {}, 'console': [], 'tiles': 0}
    png = tile_png()
    with sync_playwright() as p:
        browser = getattr(p, engine).launch(headless=not headed)
        report['browserVersion'] = browser.version
        ctx = browser.new_context(viewport={'width': 325, 'height': 530})
        ctx.add_init_script(INIT)
        page = ctx.new_page()
        page.on('console', lambda m: report['console'].append([m.type, m.text]) if m.type in ('error', 'warning') else None)
        page.on('pageerror', lambda e: report['console'].append(['pageerror', str(e)]))

        def tile(route):
            report['tiles'] += 1
            route.fulfill(status=200, content_type='image/png', headers={'Access-Control-Allow-Origin': '*'}, body=png)
        # Later registrations win: the abort-all for fonts/other hosts goes first, the controlled hosts after it.
        page.route(lambda u: not u.startswith('http://127.0.0.1'), lambda r: r.abort())
        page.route('https://tilecache.rainviewer.com/**', tile)
        page.route('https://api.aladhan.com/**', lambda r: prayer(r, record))
        page.goto(f'http://127.0.0.1:{server.server_address[1]}/index.html#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1')
        snap = lambda: page.evaluate(SNAP)
        shot = lambda name: page.screenshot(path=str(out / f'{engine}-{name}.png'))   # the 325x530 viewport is the card; no element-stability wait on animated clouds
        cell = report['cells']
        ok = wait(page, "()=>{try{const q=qaState();return q.cache.currentEligible&&q.wxTruth.radarAvailable&&!wxBusy&&!radarBusy}catch(e){return false}}")
        cell['accepted'] = {'pass': ok, **snap()}; shot('1-accepted')
        page.evaluate('()=>__r000dClock.stepWall(-7200000)'); page.wait_for_timeout(1500)
        s = snap(); cell['rejected'] = {'pass': not s['currentEligible'] and not s['radarAvailable'] and s['wt'] == '', **s}; shot('2-rejected')
        if 'boundary' in cells:
            for kind, interval in (('weather', 60000), ('radar', 600000)):
                b = page.evaluate(BOUNDARY, [kind, interval])
                done = wait(page, "()=>!wxBusy&&qaState().cache.currentEligible&&document.querySelector('#wt').textContent==='20°'" if kind == 'weather'
                            else "()=>!radarBusy&&qaState().wxTruth.radarAvailable")
                cell[kind + 'Boundary'] = {'pass': b['n1'] == b['n0'] and b['n2'] == b['n0'] + 1 and b['stateBefore'] == 'cooldown' and done, **b, 'after': snap()}
            shot('3-boundary-recovered')
            page.evaluate('()=>__r000dClock.stepWall(-7200000)'); page.wait_for_timeout(1500)
        c0 = snap(); page.evaluate('()=>__r000dClock.advance(630001)')   # elapsed passes; the next visible frame is a poll opportunity
        done = wait(page, "()=>!wxBusy&&!radarBusy&&qaState().cache.currentEligible&&qaState().wxTruth.radarAvailable&&document.querySelector('#wt').textContent==='20°'", 15000)
        page.wait_for_timeout(3000); c1 = snap()
        cell['loopRecovery'] = {'pass': done and c1['calls']['weather'] == c0['calls']['weather'] + 1 and c1['calls']['radar'] == c0['calls']['radar'] + 1,
                                'withdrawnBefore': not c0['currentEligible'] and c0['wt'] == '', 'before': c0, 'after': c1}
        shot('4-loop-recovered')
        browser.close()
    server.shutdown()
    report['pass'] = all(v['pass'] for v in report['cells'].values())
    (out / f'{engine}-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'engine': engine, 'version': report['browserVersion'], 'pass': report['pass'],
                      'cells': {k: v['pass'] for k, v in report['cells'].items()}, 'consoleErrors': len(report['console'])}))
    return report['pass']


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--engine', choices=['chromium', 'firefox'], required=True)
    a.add_argument('--root', default=str(Path(__file__).resolve().parents[2]))
    a.add_argument('--out', required=True)
    a.add_argument('--headed', action='store_true')
    a.add_argument('--cells', default='boundary,loop')
    o = a.parse_args(); out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    sys.exit(0 if run(o.engine, Path(o.root), out, o.headed, o.cells.split(',')) else 1)
