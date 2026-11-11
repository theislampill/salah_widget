"""R0021 bounded native observation: construction, retirement and replay ownership under an enforced CSP.

PREPARED, NOT YET RUN. The root schedules native runs one at a time; do not run this concurrently with other
browser work. Serves the GENERATED page unchanged from --root and enforces the R0017 widget-fixture policy
(tests/widget-fixture.html) as a real Content-Security-Policy response header on index.html. Prayer and weather
providers are controlled (no provider claim); every other non-local host is aborted.

Evidence channels (each event carries the driver phase it occurred in):
 - init script: HTMLImageElement src assignments (prefix + JS stack), `securitypolicyviolation` events,
   Worker construction/termination, blob URL create/revoke, document `visibilitychange` listener balance;
 - Chromium only: CDP Network.requestWillBeSent / loadingFailed (request-level initiator stack, blockedReason).
   Firefox has no CDP here: its retirement cell is page-level only and is reported as such.

Cells:
 first-boot        sky/preview/Moon owners installed once; Moon runtime live with its own detail
 live-handoff      not retiring: live invalidation and active asset retry still run the preview handoff
 retirement        synthetic pagehide (outgoing document kept for readback): NO data:/blob: image request,
                   NO CSP violation in the retiring phase; refined owner disposed; then persisted pageshow resumes
 navigation        (Chromium) real navigation away: CDP shows no data:/blob: image request issued by the
                   outgoing document after the retirement mark
 construction      injected 2D-context refusal (x2) and setInterval failure during retry: no orphan
                   .real-sky-canvas, worker/blob/listener balance restored, preview still ready; a healthy
                   retry yields exactly one canvas
 cycles            5 synthetic pagehide/pageshow(persisted) cycles: canvas/worker/listener counts constant
 moon-replay       re-executing the generated moon/moon-host.js over the live runtime is refused before
                   any mutation (same runtime/detail/initial objects, no new canvas/worker/URL)
 recovery-visual   screenshot + 3 s frame difference after the cycles (sky animating); night crop of the
                   Moon for human opacity review (screenshots override metrics)

Main control: run with --root <checkout of 645b53cc>. Expected FAIL there: retirement (a preview mask Image.src
during pagehide when the cloud mask changed; cloud-dependent), construction (orphan canvases), moon-replay (no
refusal; the new detail is disposed by the old runtime). Expected PASS on both: first-boot, live-handoff,
cycles, recovery-visual (subject to human review).

  PYTHONUTF8=1 <venv-python> tools/qa/run_r0021_native.py --engine chromium --out <new-dir>
  PYTHONUTF8=1 <venv-python> tools/qa/run_r0021_native.py --engine firefox --out <new-dir>
  PYTHONUTF8=1 <venv-python> tools/qa/run_r0021_native.py --engine chromium --root <main-checkout> --out <new-dir>
"""
import argparse, base64, functools, hashlib, http.server, json, re, sys, threading, time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
SERVED = ['index.html', 'real-sky/native-sky.js', 'real-sky/native-worker.js', 'real-sky/native-data.js',
          'moon/moon-host.js', 'moon/moon-worker.js', 'config.js']
HASH = '#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1'
NIGHT = '#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1&simTime=23:30&simMoon=0.5&simWax=1&simMoonAlt=40&simMoonH=180'
INIT = r"""(()=>{
 const R=window.__r0021={phase:'load',images:[],violations:[],workers:{made:0,ended:0},urls:{made:0,revoked:0},vis:0,errors:[]};
 const mark=o=>Object.assign(o,{phase:R.phase,t:performance.now()});
 const d=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src');
 Object.defineProperty(HTMLImageElement.prototype,'src',{configurable:true,get(){return d.get.call(this);},set(v){
  const s=String(v);if(s)R.images.push(mark({prefix:s.slice(0,30),scheme:s.split(':')[0],stack:String(new Error().stack).split('\n').slice(1,9).join('\n')}));d.set.call(this,v);}});
 document.addEventListener('securitypolicyviolation',e=>R.violations.push(mark({blockedURI:String(e.blockedURI).slice(0,40),directive:e.effectiveDirective,disposition:e.disposition})),true);
 const W=window.Worker;window.Worker=class extends W{constructor(...a){super(...a);R.workers.made++;}terminate(){R.workers.ended++;return super.terminate();}};
 const cu=URL.createObjectURL,ru=URL.revokeObjectURL;URL.createObjectURL=o=>{R.urls.made++;return cu.call(URL,o);};URL.revokeObjectURL=u=>{R.urls.revoked++;return ru.call(URL,u);};
 const add=EventTarget.prototype.addEventListener,rem=EventTarget.prototype.removeEventListener,live=new WeakSet();
 EventTarget.prototype.addEventListener=function(n,f,o){if(this===document&&n==='visibilitychange'&&f&&!live.has(f)){live.add(f);R.vis++;}return add.call(this,n,f,o);};
 EventTarget.prototype.removeEventListener=function(n,f,o){if(this===document&&n==='visibilitychange'&&f&&live.has(f)){live.delete(f);R.vis--;}return rem.call(this,n,f,o);};
 window.addEventListener('error',e=>R.errors.push(mark({message:String(e.message)})));
 // One-shot construction-failure injection used only by the construction cell.
 const gc=HTMLCanvasElement.prototype.getContext;R.failContext=0;R.failInterval=0;
 HTMLCanvasElement.prototype.getContext=function(...a){if(R.failContext>0&&this.className==='real-sky-canvas'){R.failContext--;return null;}return gc.apply(this,a);};
 const si=window.setInterval;window.setInterval=function(...a){if(R.failInterval>0){R.failInterval--;throw new Error('driver-injected setInterval failure');}return si.apply(this,a);};
 // Controlled providers (as tools/qa/run_r000d_native.py): overcast, so the solar cloud mask is non-trivial.
 const nf=window.fetch.bind(window),iso=ms=>new Date(ms).toISOString().slice(0,16);
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){const w=Date.now(),m=Math.floor(w/60000)*60000,h=Math.floor(w/3600000)*3600000;
   return json({timezone:'UTC',elevation:600,current:{time:iso(m),interval:900,weather_code:3,temperature_2m:20,apparent_temperature:19,
    relative_humidity_2m:40,dew_point_2m:6,wind_speed_10m:6,wind_direction_10m:180,wind_gusts_10m:9,cloud_cover:70,precipitation:0,is_day:1},
    hourly:{time:[iso(h),iso(h+3600000)],temperature_2m:[20,19],weather_code:[3,3],precipitation:[0,0]}});}
  if(u.includes('api.rainviewer.com'))return Promise.reject(new TypeError('controlled radar unavailable'));
  return nf(input,init);};
})();"""
COUNTS = """()=>{const R=window.__r0021;return {sky:document.querySelectorAll('.real-sky-canvas').length,preview:document.querySelectorAll('.real-sky-preview').length,
 detail:document.querySelectorAll('.moon-detail-canvas').length,workersLive:R.workers.made-R.workers.ended,urlsLive:R.urls.made-R.urls.revoked,vis:R.vis,
 assets:window.SalahRealSkyAssets?.state.status??null,skyStatus:window.SalahRealSky?.state.status??null,previewStatus:window.SalahSkyPreview?.state.status??null,
 previewDraws:window.SalahSkyPreview?.state.draws??null,moonRuntime:!!window.SalahMoonRuntime,moonDisposed:window.SalahMoonRuntime?.disposed??null,moonDetail:!!window.SalahMoonDetail}}"""
READY = "()=>window.SalahRealSkyAssets?.state.status==='ready'&&window.SalahSkyPreview?.state.status==='ready'&&!!window.SalahRealSky"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wait(page, predicate, timeout=30000):
    end = time.monotonic() + timeout / 1000
    while time.monotonic() < end:
        if page.evaluate(predicate):
            return True
        page.wait_for_timeout(100)
    return False


def prayer(route, record):
    day = route.request.url.split('/timings/')[1].split('?')[0]
    d, m, y = day.split('-'); r = json.loads(json.dumps(record))
    r['date']['gregorian'].update(date=day, day=d, month={'number': int(m), 'en': 'Fixture'}, year=y)
    route.fulfill(status=200, content_type='application/json', body=json.dumps({'code': 200, 'status': 'OK', 'data': r}))


def phase(page, name):
    page.evaluate('n=>{window.__r0021.phase=n;}', name)


def events_in(page, name):
    return page.evaluate("n=>{const R=window.__r0021;return {images:R.images.filter(x=>x.phase===n),violations:R.violations.filter(x=>x.phase===n),errors:R.errors.filter(x=>x.phase===n)}}", name)


def run(engine, root, out, headed, argv):
    policy = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', (REPO / 'tests/widget-fixture.html').read_text(encoding='utf-8')).group(1)
    index = (root / 'index.html').read_bytes()

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_address[1]}'
    record = json.loads((REPO / 'tests/r0002-ordinary.json').read_text(encoding='utf-8'))
    report = {'schema': 'r0021-native/1', 'engine': engine, 'headed': headed, 'argv': argv,
              'root': 'repository' if root.resolve() == REPO else root.name, 'policy': policy, 'policyDelivery': 'response header on index.html',
              'served': {n: sha(root / n) for n in SERVED if (root / n).is_file()}, 'cells': {}, 'console': [], 'cdp': []}
    cells = report['cells']
    with sync_playwright() as p:
        browser = getattr(p, engine).launch(headless=not headed)
        report['browserVersion'] = browser.version
        ctx = browser.new_context(viewport={'width': 325, 'height': 530})
        ctx.add_init_script(INIT)
        page = ctx.new_page()
        page.on('console', lambda m: report['console'].append([m.type, m.text[:300]]) if m.type in ('error', 'warning') else None)
        page.on('pageerror', lambda e: report['console'].append(['pageerror', str(e)[:300]]))
        cdp_phase = {'value': 'load'}
        if engine == 'chromium':
            cdp = ctx.new_cdp_session(page); cdp.send('Network.enable')
            ids = {}

            def sent(e):
                url = e['request']['url']
                if url.startswith(('data:', 'blob:')):
                    ids[e['requestId']] = len(report['cdp'])
                    report['cdp'].append({'phase': cdp_phase['value'], 'type': e.get('type'), 'prefix': url[:30], 'frame': e.get('frameId'),
                                          'initiator': json.dumps(e.get('initiator', {}))[:1500]})

            def failed(e):
                if e['requestId'] in ids:
                    report['cdp'][ids[e['requestId']]].update(failed=True, blockedReason=e.get('blockedReason'), canceled=e.get('canceled'))
            cdp.on('Network.requestWillBeSent', sent); cdp.on('Network.loadingFailed', failed)

        def mark(name):
            cdp_phase['value'] = name; phase(page, name)

        page.route(lambda u: not u.startswith(origin), lambda r: r.abort())
        page.route('https://api.aladhan.com/**', lambda r: prayer(r, record))
        page.route(origin + '/index.html', lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8',
                                                                headers={'Content-Security-Policy': policy}, body=index))
        page.goto(origin + '/index.html' + HASH)
        counts = lambda: page.evaluate(COUNTS)
        shot = lambda name, clip=None: page.screenshot(path=str(out / f'{engine}-{name}.png'), clip=clip)

        ok = wait(page, READY, 60000); c = counts()
        cells['first-boot'] = {'pass': ok and c['sky'] == 1 and c['preview'] == 1 and c['moonRuntime'] and c['moonDisposed'] is False and c['moonDetail'], **c}
        shot('1-first-boot')
        page.wait_for_timeout(1500)

        mark('live-invalidation'); d0 = counts()['previewDraws']
        page.evaluate("()=>window.SalahRealSky.invalidate('driver live withdrawal')")
        inv = wait(page, f"()=>window.SalahSkyPreview.state.draws>{d0}", 10000)
        mark('active-retry'); d1 = counts()['previewDraws']
        page.evaluate('()=>window.SalahRealSkyAssets.retry()')
        ret = wait(page, f"()=>window.SalahSkyPreview.state.draws>{d1}", 10000) and wait(page, READY, 30000)
        cells['live-handoff'] = {'pass': inv and ret and counts()['sky'] == 1, 'invalidationHandoff': inv, 'retryHandoff': ret, 'after': counts()}

        page.wait_for_timeout(1500)   # let clouds move so the next mask differs (main-control reproduction)
        before = counts(); mark('retiring')
        page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))")
        page.wait_for_timeout(1000)
        ev = events_in(page, 'retiring'); after = counts()
        dataImages = [x for x in ev['images'] if x['scheme'] in ('data', 'blob')]
        cdpRetiring = [x for x in report['cdp'] if x['phase'] == 'retiring']
        mark('resume'); page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))")
        resumed = wait(page, READY, 30000); r = counts()
        cells['retirement'] = {'pass': not dataImages and not ev['violations'] and not cdpRetiring and after['sky'] == 0 and after['assets'] == 'suspended' and resumed and r['sky'] == 1,
                               'retiringImages': ev['images'], 'retiringViolations': ev['violations'], 'retiringCdp': cdpRetiring,
                               'before': before, 'afterPagehide': after, 'resumed': r, 'requestLevel': engine == 'chromium'}
        shot('2-resumed')

        mark('construction'); base = counts()
        page.evaluate('()=>{window.__r0021.failContext=1;}'); page.evaluate('()=>window.SalahRealSkyAssets.retry()'); page.wait_for_timeout(500); f1 = counts()
        page.evaluate('()=>{window.__r0021.failContext=1;}'); page.evaluate('()=>window.SalahRealSkyAssets.retry()'); page.wait_for_timeout(500); f2 = counts()
        page.evaluate('()=>{window.__r0021.failInterval=1;}'); page.evaluate('()=>window.SalahRealSkyAssets.retry()'); page.wait_for_timeout(500); f3 = counts()
        page.evaluate('()=>window.SalahRealSkyAssets.retry()'); healed = wait(page, READY, 30000); f4 = counts()
        bal = lambda x: x['workersLive'] <= base['workersLive'] - 1 and x['vis'] <= base['vis'] - 1   # the retired refined owner's worker/listener are gone
        cells['construction'] = {'pass': all(x['sky'] == 0 and x['assets'] == 'unavailable' and x['previewStatus'] == 'ready' and bal(x) for x in (f1, f2, f3))
                                 and healed and f4['sky'] == 1 and f4['workersLive'] == base['workersLive'] and f4['vis'] == base['vis'],
                                 'baseline': base, 'contextRefusal1': f1, 'contextRefusal2': f2, 'intervalFailure': f3, 'recovered': f4}

        mark('cycles'); start = counts(); seen = []
        for i in range(5):
            page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))"); page.wait_for_timeout(200)
            page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))"); wait(page, READY, 30000)
            seen.append(counts())
        keys = ('sky', 'preview', 'detail', 'workersLive', 'urlsLive', 'vis')
        cells['cycles'] = {'pass': all(all(s[k] == start[k] for k in keys) for s in seen), 'start': start, 'cycles': seen}

        mark('moon-replay')
        page.evaluate("()=>{window.__r0021.refs={runtime:window.SalahMoonRuntime,detail:window.SalahMoonDetail,initial:window.SalahMoonInitial};}")
        m0 = counts()
        outcome = page.evaluate("""async()=>{const text=await (await fetch('moon/moon-host.js')).text();const R=window.__r0021,n=R.errors.length;
          const s=document.createElement('script');s.textContent=text;document.head.append(s);s.remove();
          return {errors:R.errors.slice(n).map(e=>e.message),same:window.SalahMoonRuntime===R.refs.runtime&&window.SalahMoonDetail===R.refs.detail&&window.SalahMoonInitial===R.refs.initial,
            disposed:window.SalahMoonRuntime?.disposed??null};}""")
        page.wait_for_timeout(500); m1 = counts()
        cells['moon-replay'] = {'pass': outcome['same'] and outcome['disposed'] is False and any('replay refused' in e for e in outcome['errors'])
                                and all(m1[k] == m0[k] for k in ('detail', 'workersLive', 'urlsLive', 'vis')), 'outcome': outcome, 'before': m0, 'after': m1}

        mark('recovery-visual'); page.wait_for_timeout(1000)
        a = page.screenshot(); page.wait_for_timeout(3000); b = page.screenshot()
        (out / f'{engine}-3a-motion.png').write_bytes(a); (out / f'{engine}-3b-motion.png').write_bytes(b)
        # Frame difference is computed in a separate policy-free about:blank page so its decode of the two
        # screenshots is never product traffic or a CSP event of the widget document.
        helper = ctx.new_page()
        diff = helper.evaluate("""async([a,b])=>{const load=s=>new Promise(r=>{const i=new Image();i.onload=()=>r(i);i.src='data:image/png;base64,'+s;});
          const [x,y]=await Promise.all([load(a),load(b)]);const c=document.createElement('canvas');c.width=x.width;c.height=x.height;const g=c.getContext('2d');
          g.drawImage(x,0,0);const p=g.getImageData(0,0,c.width,c.height).data;g.drawImage(y,0,0);const q=g.getImageData(0,0,c.width,c.height).data;
          let n=0;for(let i=0;i<p.length;i+=4)if(Math.abs(p[i]-q[i])+Math.abs(p[i+1]-q[i+1])+Math.abs(p[i+2]-q[i+2])>6)n++;return n/(p.length/4);}""",
                               [base64.b64encode(a).decode(), base64.b64encode(b).decode()])
        helper.close()
        cells['recovery-visual'] = {'pass': diff > 0, 'changedPixelFraction3s': diff, 'humanReview': [f'{engine}-3a-motion.png', f'{engine}-3b-motion.png']}

        # Real navigation: the outgoing document retires for real (Chromium request log only).
        if engine == 'chromium':
            page.wait_for_timeout(1500); mark('navigation')
            page.goto('about:blank'); page.wait_for_timeout(1000)
            nav = [x for x in report['cdp'] if x['phase'] == 'navigation']
            cells['navigation'] = {'pass': not nav, 'navigationCdp': nav}

        night = ctx.new_page()
        night.route(lambda u: not u.startswith(origin), lambda r: r.abort())
        night.route('https://api.aladhan.com/**', lambda r: prayer(r, record))
        night.route(origin + '/index.html', lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', headers={'Content-Security-Policy': policy}, body=index))
        night.goto(origin + '/index.html' + NIGHT); wait(night, READY, 60000)
        for _ in range(3):
            night.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))"); night.wait_for_timeout(200)
            night.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))"); wait(night, READY, 30000)
        night.wait_for_timeout(1500)
        box = night.evaluate("()=>{const r=document.querySelector('.mphoto')?.getBoundingClientRect();return r&&r.width>0?{x:Math.max(0,r.left-20),y:Math.max(0,r.top-20),width:r.width+40,height:r.height+40}:null}")
        night.screenshot(path=str(out / f'{engine}-4-night-card.png'))
        if box:
            night.screenshot(path=str(out / f'{engine}-4-night-moon-crop.png'), clip=box)
        truth = night.evaluate("()=>{try{return qaState().moonTruth??null}catch(e){return String(e)}}")
        cells['recovery-visual'].update(nightMoonCrop=bool(box), moonTruth=truth, nightCounts=night.evaluate(COUNTS))
        browser.close()
    server.shutdown()
    report['pass'] = all(v['pass'] for v in cells.values())
    text = json.dumps(report, indent=2, ensure_ascii=False)
    for form in {str(REPO), str(REPO).replace('\\', '\\\\'), REPO.as_posix(), str(root), root.as_posix()}:
        text = text.replace(form, '<root>')
    (out / f'{engine}-report.json').write_text(text + '\n', encoding='utf-8')
    print(json.dumps({'engine': engine, 'version': report['browserVersion'], 'pass': report['pass'], 'cells': {k: v['pass'] for k, v in cells.items()}}))
    return report['pass']


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('--engine', choices=['chromium', 'firefox'], required=True)
    a.add_argument('--root', default=str(REPO))
    a.add_argument('--out', required=True)
    a.add_argument('--headed', action='store_true')
    o = a.parse_args(); out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    sys.exit(0 if run(o.engine, Path(o.root), out, o.headed, sys.argv[1:]) else 1)
