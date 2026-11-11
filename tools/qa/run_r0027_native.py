"""R0027 bounded generated-entry smoke (PREPARED; the root schedules runs one at a time).

Serves --root unchanged on 127.0.0.1, loads the GENERATED index.html at a twilight scene with a
fast-forwarded clock (simTime + timeScale), lets the sky render for --seconds, and records:
console/page errors; that the refined sky canvas (and the first-paint preview canvas) is
non-blank and changes between two frames; and, via an init script, the maximum size of any Map
whose size exceeds --threshold in the page realm (first-paint + UI bundle share one global) and
in the sky worker realm (the worker Blob gets the same observer prepended; it reports over a
BroadcastChannel, so no product message is altered). Observation only; no product byte changes.

Expected: candidate max inner fit-map size <= 12,000; a --root main control may grow past it
only if the bounded run produces more than 12,000 distinct twilight colours. If neither reaches
12,000, the report says which size was reached; that is not a bound proof (the Node tests are).
No pixel-equality claim is made here: exact numbers are proved by the Node oracle tests.
"""
import argparse, functools, hashlib, http.server, json, sys, threading, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OBSERVER = r"""(()=>{const T=%THRESHOLD%,R=%REALM%;const st={max:0,maxFit:0,maps:0};const seen=new WeakSet();
const isFit=v=>v!==null&&typeof v==='object'&&Object.keys(v).length===2&&'samples' in v&&'temperatureProxyK' in v;
const set=Map.prototype.set;Map.prototype.set=function(k,v){const r=set.call(this,k,v);const n=this.size;
 if(n>T){if(!seen.has(this)){seen.add(this);st.maps++;}if(n>st.max)st.max=n;if(typeof k==='number'&&isFit(v)&&n>st.maxFit)st.maxFit=n;}return r;};
const ch=typeof BroadcastChannel==='function'?new BroadcastChannel('r0027-map-observer'):null;
setInterval(()=>{ch&&ch.postMessage({realm:R,...st});},500);globalThis.__r0027MapObserver=st;})();"""
INIT = r"""(()=>{%PAGE%
 window.__r0027Realms={};const ch=new BroadcastChannel('r0027-map-observer');ch.onmessage=e=>{window.__r0027Realms[e.data.realm]=e.data;};
 const hook=%WORKER%;const NB=window.Blob;
 function ObservedBlob(parts,opts){if(Array.isArray(parts)&&typeof parts[0]==='string'&&parts[0].includes('sfFitCache')&&parts[0].includes('self.onmessage')){window.__r0027WorkerObserved=(window.__r0027WorkerObserved||0)+1;parts=[hook+'\n',...parts];}return new NB(parts,opts);}
 ObservedBlob.prototype=NB.prototype;window.Blob=ObservedBlob;})();"""
CANVAS = """()=>{const out={};for(const sel of ['.real-sky-canvas','.real-sky-preview']){const c=document.querySelector(sel);if(!c){out[sel]=null;continue;}
 const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let sum=0,nonzero=0,h=2166136261;
 for(let i=0;i<d.length;i+=4){const v=d[i]+d[i+1]+d[i+2];sum+=v;if(v)nonzero++;h=Math.imul(h^v,16777619)>>>0;}
 out[sel]={w:c.width,h:c.height,visible:getComputedStyle(c).visibility,nonzeroPixels:nonzero,meanRGB:sum/(d.length/4)/3,fnv:h};}return out;}"""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(engine, root, out, headed, seconds, threshold, scene):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    served = ['index.html', 'config.js', 'real-sky/native-sky.js', 'real-sky/native-data.js', 'real-sky/native-sky.css']
    report = {'engine': engine, 'argv': sys.argv[1:], 'headed': headed, 'root': 'repository' if root.resolve() == ROOT else root.name,
              'scene': scene, 'seconds': seconds, 'threshold': threshold,
              'servedSha256': {p: sha(root / p) for p in served if (root / p).exists()}, 'console': [], 'samples': []}
    record = json.loads((ROOT / 'tests/r0002-ordinary.json').read_text(encoding='utf-8'))
    def prayer(route):
        day = route.request.url.split('/timings/')[1].split('?')[0]
        d, m, y = day.split('-'); r = json.loads(json.dumps(record))
        r['date']['gregorian'].update(date=day, day=d, month={'number': int(m), 'en': 'Fixture'}, year=y)
        route.fulfill(status=200, content_type='application/json', body=json.dumps({'code': 200, 'status': 'OK', 'data': r}))
    page_obs = OBSERVER.replace('%THRESHOLD%', str(threshold)).replace('%REALM%', '"page"')
    worker_obs = OBSERVER.replace('%THRESHOLD%', str(threshold)).replace('%REALM%', '"worker"')
    init = INIT.replace('%PAGE%', page_obs).replace('%WORKER%', json.dumps(worker_obs))
    with sync_playwright() as p:
        browser = getattr(p, engine).launch(headless=not headed)
        report['browserVersion'] = browser.version
        ctx = browser.new_context(viewport={'width': 325, 'height': 530})
        ctx.add_init_script(init)
        page = ctx.new_page()
        page.on('console', lambda m: report['console'].append([m.type, m.text]) if m.type in ('error', 'warning') else None)
        page.on('pageerror', lambda e: report['console'].append(['pageerror', str(e)]))
        page.route(lambda u: not u.startswith('http://127.0.0.1'), lambda r: r.abort())
        page.route('https://api.aladhan.com/**', prayer)
        page.goto(f'http://127.0.0.1:{server.server_address[1]}/index.html#{scene}')
        t0 = time.monotonic(); first = None
        while time.monotonic() - t0 < seconds:
            page.wait_for_timeout(2000)
            s = {'t': round(time.monotonic() - t0, 1), 'canvas': page.evaluate(CANVAS),
                 'maps': page.evaluate('()=>({page:window.__r0027MapObserver,realms:window.__r0027Realms,workerObserved:window.__r0027WorkerObserved||0})')}
            report['samples'].append(s); first = first or s
        page.screenshot(path=str(out / f'{engine}-final.png'))
        browser.close()
    server.shutdown()
    last = report['samples'][-1]
    sky = [s['canvas'].get('.real-sky-canvas') for s in report['samples'] if s['canvas'].get('.real-sky-canvas')]
    worker = (last['maps']['realms'] or {}).get('worker') or {}
    pageobs = last['maps']['page'] or {}
    report['summary'] = {
        'pageErrors': sum(1 for c in report['console'] if c[0] in ('error', 'pageerror')),
        'skyNonBlank': bool(sky) and sky[-1]['nonzeroPixels'] > 0,
        'skyChanged': len({c['fnv'] for c in sky}) > 1,
        'workerObserved': last['maps']['workerObserved'],
        'maxMapSize': {'page': pageobs.get('max', 0), 'worker': worker.get('max', 0)},
        'maxFitMapSize': {'page': pageobs.get('maxFit', 0), 'worker': worker.get('maxFit', 0)},
        'reachedCapacity': max(pageobs.get('maxFit', 0), worker.get('maxFit', 0)) >= 12000,
        'boundRespected': max(pageobs.get('maxFit', 0), worker.get('maxFit', 0)) <= 12000,
    }
    (out / f'{engine}-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'engine': engine, 'version': report['browserVersion'], **report['summary']}))
    return report['summary']['pageErrors'] == 0 and report['summary']['skyNonBlank'] and report['summary']['skyChanged']


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--engine', choices=['chromium', 'firefox'], required=True)
    a.add_argument('--root', default=str(ROOT))
    a.add_argument('--out', required=True)
    a.add_argument('--headed', action='store_true')
    a.add_argument('--seconds', type=int, default=90)
    a.add_argument('--threshold', type=int, default=1000)
    a.add_argument('--scene', default='lat=28.5383&lon=-81.3792&tz=UTC&label=Fixture&method=4&simTime=23:05&timeScale=120&qa=1')
    o = a.parse_args(); out = Path(o.out); out.mkdir(parents=True, exist_ok=True)
    sys.exit(0 if run(o.engine, Path(o.root), out, o.headed, o.seconds, o.threshold, o.scene) else 1)
