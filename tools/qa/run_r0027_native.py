"""R0027 bounded generated-entry smoke (the root schedules runs one at a time; never run browsers in parallel).

Serves --root unchanged on 127.0.0.1 and loads the GENERATED index.html at an Orlando civil/nautical-twilight
scene (simTime 23:05 UTC in November, sun about -6 degrees) whose clock advances at --scene's timeScale. It
claims only: the delivered bundle loads; the refined, worker-rendered sky (.real-sky-canvas) composes, is
visible, non-blank and changes between samples; and the inner exact-B-V fit map was observed at a size N
(N <= 12,000 expected). It is NOT a bound proof: a normal scene's working set (about 1.9k distinct catalogue
B-V keys plus the twilight colours of the run) never reaches 12,000; the Node tests prove the bound.

Readiness (compare tools/qa/run_r0021_native.py): sampling starts only after SalahRealSky reports a ready frame
AND the card carries .real-sky-composed with the refined canvas visible (--ready-timeout-s). Why the default
uses timeScale=4, not 120: the native lifecycle rejects every worker result whose observer UTC lags the host
clock by more than 30 s of scene time and reports availability `rate-throughput` (real-sky/native-lifecycle.mjs);
at 120x that is a 250 ms wall budget, below one worker render, so at 120x the refined canvas never becomes
visible and only the first-paint preview shows (run1, a driver defect, recorded in docs/state-contracts/R0027.md).

Network: prayer timings are fulfilled from tests/r0002-ordinary.json; weather (open-meteo) is answered in-page
with a controlled clear-night record and radar (rainviewer) is rejected in-page as "controlled radar
unavailable" (as tools/qa/run_r0021_native.py), so no request reaches a provider. Every other non-local request
is aborted by the route guard; console errors attributable to those aborted URLs are classified
`expectedAbort` and listed, never counted as page errors.

Map observer (init script, observation only; no product byte changes): Map.prototype.set is wrapped in the page
realm (first-paint inline script + native-sky.js share one global) and in the sky worker realm (the worker Blob
gets the same observer prepended; it reports over a BroadcastChannel, so no product message is altered). A map
is classified once, on its first set: `fit` = number key and a value whose own keys are exactly samples and
temperatureProxyK (the record `fit={samples:blackbodyShape(T),temperatureProxyK:T}` in
real-sky/core/src/spectral.mjs, i.e. sfFitCache); `selection` = string key `hip|spectralType|bv` and a value with
samples and kind (the outer sfCache). Fit/selection sizes are recorded at any size; other maps only above
--threshold. Run1's detector only recorded maps above the threshold, so a fit map below 1,000 read as 0, and
its 1,5xx map was the outer selection cache (string keys).

  PYTHONUTF8=1 <venv-python> tools/qa/run_r0027_native.py --engine chromium --out <new-dir>
  PYTHONUTF8=1 <venv-python> tools/qa/run_r0027_native.py --engine firefox --root <main-checkout> --root-label main-645b53cc --out <new-dir>
"""
import argparse, functools, hashlib, http.server, json, sys, threading, time
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
CAPACITY = 12000
SCENE = 'lat=28.5383&lon=-81.3792&tz=UTC&label=Fixture&method=4&simTime=23:05&timeScale=4&qa=1'
OBSERVER = r"""(()=>{const T=%THRESHOLD%,R=%REALM%;const st={realm:R,maxOther:0,maxFit:0,fitMaps:0,fitSets:0,maxSelection:0,selectionMaps:0,otherMaps:0};
const kind=new WeakMap();const own=Object.keys;
const isFit=v=>v!==null&&typeof v==='object'&&own(v).length===2&&'samples' in v&&'temperatureProxyK' in v;
const isSel=(k,v)=>typeof k==='string'&&k.split('|').length===3&&v!==null&&typeof v==='object'&&'samples' in v&&'kind' in v;
const set=Map.prototype.set;Map.prototype.set=function(k,v){const r=set.call(this,k,v);let c=kind.get(this);
 if(c===undefined){c=typeof k==='number'&&isFit(v)?'fit':isSel(k,v)?'selection':'other';kind.set(this,c);if(c==='fit')st.fitMaps++;else if(c==='selection')st.selectionMaps++;}
 const n=this.size;if(c==='fit'){st.fitSets++;if(n>st.maxFit)st.maxFit=n;}else if(c==='selection'){if(n>st.maxSelection)st.maxSelection=n;}
 else if(n>T&&n>st.maxOther){if(st.maxOther<=T)st.otherMaps++;st.maxOther=n;}return r;};
const ch=typeof BroadcastChannel==='function'?new BroadcastChannel('r0027-map-observer'):null;
setInterval(()=>{ch&&ch.postMessage({...st});},500);globalThis.__r0027MapObserver=st;})();"""
INIT = r"""(()=>{%PAGE%
 window.__r0027Realms={};const ch=new BroadcastChannel('r0027-map-observer');ch.onmessage=e=>{window.__r0027Realms[e.data.realm]=e.data;};
 const hook=%WORKER%;const NB=window.Blob;
 function ObservedBlob(parts,opts){if(Array.isArray(parts)&&typeof parts[0]==='string'&&parts[0].includes('sfFitCache')&&parts[0].includes('self.onmessage')){window.__r0027WorkerObserved=(window.__r0027WorkerObserved||0)+1;parts=[hook+'\n',...parts];}return new NB(parts,opts);}
 ObservedBlob.prototype=NB.prototype;window.Blob=ObservedBlob;
 // Controlled providers, answered in-page (no request leaves): clear night weather; radar unavailable.
 const calls=window.__r0027Calls={weather:0,radar:0},nf=window.fetch.bind(window),iso=ms=>new Date(ms).toISOString().slice(0,16);
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){calls.weather++;const w=Date.now(),m=Math.floor(w/60000)*60000,h=Math.floor(w/3600000)*3600000;
   return json({timezone:'UTC',elevation:30,current:{time:iso(m),interval:900,weather_code:0,temperature_2m:20,apparent_temperature:19,
    relative_humidity_2m:50,dew_point_2m:9,wind_speed_10m:3,wind_direction_10m:180,wind_gusts_10m:5,cloud_cover:0,precipitation:0,is_day:0},
    hourly:{time:[iso(h),iso(h+3600000)],temperature_2m:[20,19],weather_code:[0,0],precipitation:[0,0]}});}
  if(u.includes('api.rainviewer.com')){calls.radar++;return Promise.reject(new TypeError('controlled radar unavailable'));}
  return nf(input,init);};
})();"""
CANVAS = """()=>{const out={};for(const sel of ['.real-sky-canvas','.real-sky-preview']){const c=document.querySelector(sel);if(!c){out[sel]=null;continue;}
 const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let sum=0,nonzero=0,h=2166136261;
 for(let i=0;i<d.length;i+=4){const v=d[i]+d[i+1]+d[i+2];sum+=v;if(v)nonzero++;h=Math.imul(h^v,16777619)>>>0;}
 out[sel]={w:c.width,h:c.height,visible:getComputedStyle(c).visibility,display:getComputedStyle(c).display,nonzeroPixels:nonzero,meanRGB:sum/(d.length/4)/3,fnv:h};}return out;}"""
SKY = """()=>{const s=window.SalahRealSky?.state;const c=document.querySelector('.c');return {status:s?.status??null,reason:s?.reason??null,renders:s?.renders??null,
 presentationDraws:s?.presentationDraws??null,rejections:s?.rejections??null,errors:s?.errors??null,availability:s?.availability??null,
 lifecycle:s?.lifecycle?{requests:s.lifecycle.requests,accepted:s.lifecycle.accepted,rejected:s.lifecycle.rejected,invalidations:s.lifecycle.invalidations,availability:s.lifecycle.availability}:null,
 composed:!!c?.classList.contains('real-sky-composed'),assets:window.SalahRealSkyAssets?.state.status??null,preview:window.SalahSkyPreview?.state.status??null,
 badge:document.querySelector('.real-sky-status')?.textContent??null,sunAltDeg:s?.last?.physicalState?.sun?.altDeg??null,calls:{...window.__r0027Calls}}}"""
READY = """()=>{const s=window.SalahRealSky?.state,c=document.querySelector('.c'),k=document.querySelector('.real-sky-canvas');
 return !!(s&&s.status==='ready'&&c?.classList.contains('real-sky-composed')&&k&&getComputedStyle(k).visibility==='visible')}"""
MAPS = '()=>({page:window.__r0027MapObserver,realms:window.__r0027Realms,workerObserved:window.__r0027WorkerObserved||0})'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wait(page, predicate, timeout_s):
    end = time.monotonic() + timeout_s
    while time.monotonic() < end:
        if page.evaluate(predicate):
            return True
        page.wait_for_timeout(250)
    return False


def run(engine, root, root_label, out, headed, seconds, threshold, scene, ready_timeout):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_address[1]}'
    served = ['index.html', 'config.js', 'real-sky/native-sky.js', 'real-sky/native-worker.js', 'real-sky/native-data.js', 'real-sky/native-sky.css']
    # Engine, root label and option values only; never argv or an absolute path.
    report = {'schema': 'r0027-native/2', 'engine': engine, 'root': root_label, 'out': out.name,
              'options': {'headed': headed, 'scene': scene, 'seconds': seconds, 'threshold': threshold, 'readyTimeoutS': ready_timeout},
              'claim': 'bundle loads; refined worker sky composes, is visible, non-blank and changes; inner fit map observed at size N <= 12,000 (not a bound proof)',
              'servedSha256': {p: sha(root / p) for p in served if (root / p).exists()}, 'console': [], 'aborted': [], 'samples': []}
    record = json.loads((ROOT / 'tests/r0002-ordinary.json').read_text(encoding='utf-8'))

    def prayer(route):
        day = route.request.url.split('/timings/')[1].split('?')[0]
        d, m, y = day.split('-'); r = json.loads(json.dumps(record))
        r['date']['gregorian'].update(date=day, day=d, month={'number': int(m), 'en': 'Fixture'}, year=y)
        route.fulfill(status=200, content_type='application/json', body=json.dumps({'code': 200, 'status': 'OK', 'data': r}))

    def guard(route):
        u = urlsplit(route.request.url)
        report['aborted'].append(f'{u.scheme}://{u.netloc}{u.path}')
        route.abort()

    def on_console(m):
        if m.type not in ('error', 'warning'):
            return
        loc = (m.location or {}).get('url', '') if hasattr(m, 'location') else ''
        hit = next((a for a in report['aborted'] if loc.startswith(a) or a in m.text), None)
        report['console'].append({'type': m.type, 'class': 'expectedAbort' if (m.type == 'error' and hit) else m.type,
                                  'abortedUrl': hit, 'text': m.text[:300]})

    page_obs = OBSERVER.replace('%THRESHOLD%', str(threshold)).replace('%REALM%', '"page"')
    worker_obs = OBSERVER.replace('%THRESHOLD%', str(threshold)).replace('%REALM%', '"worker"')
    init = INIT.replace('%PAGE%', page_obs).replace('%WORKER%', json.dumps(worker_obs))
    with sync_playwright() as p:
        browser = getattr(p, engine).launch(headless=not headed)
        report['browserVersion'] = browser.version
        ctx = browser.new_context(viewport={'width': 325, 'height': 530})
        ctx.add_init_script(init)
        page = ctx.new_page()
        page.on('console', on_console)
        page.on('pageerror', lambda e: report['console'].append({'type': 'pageerror', 'class': 'pageerror', 'abortedUrl': None, 'text': str(e)[:300]}))
        page.on('crash', lambda _p: report.setdefault('crashes', []).append('page crashed'))
        page.route(lambda u: not u.startswith(origin), guard)
        page.route('https://api.aladhan.com/**', prayer)
        page.goto(f'{origin}/index.html#{scene}')
        t0 = time.monotonic()
        ready = wait(page, READY, ready_timeout)
        report['refinedComposedAfterS'] = round(time.monotonic() - t0, 1) if ready else None
        report['atReady'] = {'sky': page.evaluate(SKY), 'canvas': page.evaluate(CANVAS)}
        if ready:
            page.screenshot(path=str(out / f'{engine}-composed.png'))
        t1 = time.monotonic()
        while time.monotonic() - t1 < seconds:
            page.wait_for_timeout(2000)
            report['samples'].append({'t': round(time.monotonic() - t0, 1), 'canvas': page.evaluate(CANVAS), 'sky': page.evaluate(SKY), 'maps': page.evaluate(MAPS)})
        page.screenshot(path=str(out / f'{engine}-final.png'))
        browser.close()
    server.shutdown()
    samples = report['samples']
    last = samples[-1]
    sky = [s['canvas'].get('.real-sky-canvas') or {} for s in samples]
    visible = [c for c in sky if c.get('visible') == 'visible']
    worker = (last['maps']['realms'] or {}).get('worker') or {}
    pageobs = last['maps']['page'] or {}
    real = [c for c in report['console'] if c['class'] in ('error', 'pageerror')]
    max_fit = max(pageobs.get('maxFit', 0), worker.get('maxFit', 0))
    report['summary'] = {
        'pageErrors': len(real),
        'expectedAbortErrors': sum(1 for c in report['console'] if c['class'] == 'expectedAbort'),
        'refinedComposed': ready,
        'refinedVisibleSamples': f'{len(visible)}/{len(sky)}',
        'skyNonBlank': bool(visible) and sky[-1].get('visible') == 'visible' and sky[-1].get('nonzeroPixels', 0) > 0,
        'skyChanged': len({c['fnv'] for c in visible}) > 1,
        'finalAvailability': (last['sky'].get('availability') or {}).get('reason'),
        'workerObserved': last['maps']['workerObserved'],
        'fitMapSize': {'page': pageobs.get('maxFit', 0), 'worker': worker.get('maxFit', 0)},
        'fitMaps': {'page': pageobs.get('fitMaps', 0), 'worker': worker.get('fitMaps', 0)},
        'selectionMapSize': {'page': pageobs.get('maxSelection', 0), 'worker': worker.get('maxSelection', 0)},
        'otherMapAboveThreshold': {'page': pageobs.get('maxOther', 0), 'worker': worker.get('maxOther', 0)},
        'fitMapObserved': worker.get('maxFit', 0) > 0,
        'fitMapWithinCapacity': max_fit <= CAPACITY,
        'reachedCapacity': max_fit >= CAPACITY,
    }
    s = report['summary']
    report['pass'] = bool(s['pageErrors'] == 0 and s['refinedComposed'] and s['skyNonBlank'] and s['skyChanged']
                          and s['workerObserved'] >= 1 and s['fitMapObserved'] and s['fitMapWithinCapacity'] and not report.get('crashes'))
    (out / f'{engine}-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'engine': engine, 'root': root_label, 'version': report['browserVersion'], 'pass': report['pass'], **s}))
    return report['pass']


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('--engine', choices=['chromium', 'firefox'], required=True)
    a.add_argument('--root', default=str(ROOT))
    a.add_argument('--root-label', default=None, help='label recorded for --root (default: "repository" or the directory name)')
    a.add_argument('--out', required=True)
    a.add_argument('--headed', action='store_true')
    a.add_argument('--seconds', type=int, default=60, help='sampling time after the refined sky first composes')
    a.add_argument('--threshold', type=int, default=1000, help='record unclassified maps only above this size')
    a.add_argument('--ready-timeout-s', type=int, default=60)
    a.add_argument('--scene', default=SCENE)
    o = a.parse_args(); out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    root = Path(o.root)
    label = o.root_label or ('repository' if root.resolve() == ROOT else root.resolve().name)
    sys.exit(0 if run(o.engine, root, label, out, o.headed, o.seconds, o.threshold, o.scene, o.ready_timeout_s) else 1)
