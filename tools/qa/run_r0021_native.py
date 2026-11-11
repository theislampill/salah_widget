"""R0021 bounded native observation: construction, retirement and replay ownership under an enforced CSP.

The root schedules native runs one at a time; do not run this concurrently with other
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
                   outgoing document after the retirement mark; like retirement, it requires a refined-composed
                   card and a changing data-URL cloud mask, else precondition-not-met (never a vacuous PASS)
 construction      injected 2D-context refusal (x2) and setInterval failure during retry: no orphan
                   .real-sky-canvas, worker/blob/listener balance restored, preview still ready; a healthy
                   retry yields exactly one canvas
 cycles            5 synthetic pagehide/pageshow(persisted) cycles: canvas/worker/listener counts constant
 moon-replay       re-executing the generated moon/moon-host.js over the live runtime is refused before
                   any mutation (same runtime/detail/initial objects, no new canvas/worker/URL)
 recovery-visual   screenshot + 3 s frame difference after the cycles (sky animating); night crop of the
                   Moon for human opacity review (screenshots override metrics)

Crash safety: the report is rewritten after every cell; a cell that throws is recorded as `crashed` (error text,
pass=false) and, after a browser/page crash, later cells as `not-run`. Firefox finding (2026-11-11, recorded in
docs/state-contracts/R0021.md): a synthetic pagehide dispatched immediately (<=~100 ms) after the resumed sky
reports READY crashes Firefox 153's content process on BOTH 645b53cc and the candidate, with or without this
driver's instrumentation; a >=200 ms settle, rapid active retry and raw worker create/terminate do not. The cycles
cell therefore settles --cycles-settle-ms (default 500) after each resume; --cycles-settle-ms 0 reproduces it.
Retirement cell: passes only when its precondition held (refined-composed card AND a changing data-URL cloud
mask at pagehide); otherwise it reports precondition-not-met rather than a vacuous PASS. On 2026-11-11 no tried
scene (plain, --fragment with simWx=3&simCloud=100, and a low-Moon overcast timeScale=30 night) produced a
non-clear solar mask at pagehide in Chromium 148, on main or candidate, so this cell did not reproduce the finding.
Cause (found later): the enforced fixture CSP (connect-src 'self') blocks the cross-origin prayer fetch before the
Playwright route can answer it, so no prayer data arrives and no cloud is painted. --in-page-prayer (opt-in; default
runs are unchanged) answers the same controlled record inside the page. With it and
--fragment '...&simWx=3&simCloud=100&timeScale=4' the precondition holds. Each retiring-phase image event keeps its
JS stack, which names the initiator (lifecycle dispose versus the live preview render loop); the cell's pass rule
is not changed by this.

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
 const R=window.__r0021={phase:'load',images:[],violations:[],workers:{made:0,ended:0},urls:{made:0,revoked:0},vis:0,visLog:[],errors:[]};
 const mark=o=>Object.assign(o,{phase:R.phase,t:performance.now()});
 const d=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src');
 Object.defineProperty(HTMLImageElement.prototype,'src',{configurable:true,get(){return d.get.call(this);},set(v){
  const s=String(v);if(s)R.images.push(mark({prefix:s.slice(0,30),scheme:s.split(':')[0],stack:String(new Error().stack).split('\n').slice(1,9).join('\n')}));d.set.call(this,v);}});
 document.addEventListener('securitypolicyviolation',e=>R.violations.push(mark({blockedURI:String(e.blockedURI).slice(0,40),directive:e.effectiveDirective,disposition:e.disposition})),true);
 const W=window.Worker;window.Worker=class extends W{constructor(...a){super(...a);R.workers.made++;}terminate(){R.workers.ended++;return super.terminate();}};
 const cu=URL.createObjectURL,ru=URL.revokeObjectURL;URL.createObjectURL=o=>{R.urls.made++;return cu.call(URL,o);};URL.revokeObjectURL=u=>{R.urls.revoked++;return ru.call(URL,u);};
 const add=EventTarget.prototype.addEventListener,rem=EventTarget.prototype.removeEventListener,live=new WeakSet();
 EventTarget.prototype.addEventListener=function(n,f,o){if(this===document&&n==='visibilitychange'&&f&&!live.has(f)){live.add(f);R.vis++;R.visLog.push(mark({op:'add',stack:String(new Error().stack).split('\n').slice(1,5).join(' | ')}));}return add.call(this,n,f,o);};
 EventTarget.prototype.removeEventListener=function(n,f,o){if(this===document&&n==='visibilitychange'&&f&&live.has(f)){live.delete(f);R.vis--;R.visLog.push(mark({op:'remove',stack:String(new Error().stack).split('\n').slice(1,5).join(' | ')}));}return rem.call(this,n,f,o);};
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
PRAYER_IN_PAGE = r"""((rec)=>{const f=window.fetch;
 window.fetch=(input,init)=>{const u=String(input&&input.url||input),m=/^https:\/\/api\.aladhan\.com\/v1\/timings\/(\d\d)-(\d\d)-(\d{4})/.exec(u);
  if(!m)return f(input,init);const r=JSON.parse(JSON.stringify(rec));
  Object.assign(r.date.gregorian,{date:m[1]+'-'+m[2]+'-'+m[3],day:m[1],month:{number:+m[2],en:'Fixture'},year:m[3]});
  return Promise.resolve(new Response(JSON.stringify({code:200,status:'OK',data:r}),{status:200,headers:{'Content-Type':'application/json'}}));};
})(__RECORD__);"""
# JS-stack initiator classes for retiring-phase image events (informational; owner 10.6).
RETIREMENT_STACK = re.compile(r'NativeSkyLifecycle\.dispose')
RENDER_LOOP_STACK = re.compile(r'present \(.*\n\s+at loop \(', re.S)   # SalahSkyPreview.present called from the native rAF loop
COUNTS = """()=>{const R=window.__r0021;return {sky:document.querySelectorAll('.real-sky-canvas').length,preview:document.querySelectorAll('.real-sky-preview').length,
 detail:document.querySelectorAll('.moon-detail-canvas').length,workersLive:R.workers.made-R.workers.ended,urlsLive:R.urls.made-R.urls.revoked,vis:R.vis,
 assets:window.SalahRealSkyAssets?.state.status??null,skyStatus:window.SalahRealSky?.state.status??null,previewStatus:window.SalahSkyPreview?.state.status??null,
 previewDraws:window.SalahSkyPreview?.state.draws??null,moonRuntime:!!window.SalahMoonRuntime,moonDisposed:window.SalahMoonRuntime?.disposed??null,moonDetail:!!window.SalahMoonDetail}}"""
READY = "()=>window.SalahRealSkyAssets?.state.status==='ready'&&window.SalahSkyPreview?.state.status==='ready'&&!!window.SalahRealSky"
# The native boot's render loop installs its own one-time document visibilitychange listener. In Firefox it
# can start after the sky is READY, so resource baselines wait for it (a boot listener is not a leak).
BOOTED = "()=>typeof _loopStarted!=='undefined'&&_loopStarted===true"


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


CELLS = ['first-boot', 'live-handoff', 'retirement', 'construction', 'cycles', 'moon-replay', 'recovery-visual', 'night', 'navigation']


def run(engine, root, out, headed, selected=CELLS, cycles_wait=200, cycles_fresh=False, composed_wait=60000, cycles_settle=500, fragment=None,
        in_page_prayer=False):
    fragment = fragment or HASH
    policy = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', (REPO / 'tests/widget-fixture.html').read_text(encoding='utf-8')).group(1)
    index = (root / 'index.html').read_bytes()

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_address[1]}'
    record = json.loads((REPO / 'tests/r0002-ordinary.json').read_text(encoding='utf-8'))
    report = {'schema': 'r0021-native/2', 'engine': engine, 'headed': headed, 'out': out.name, 'complete': False,
              'evidenceLevel': 'request-level (CDP) and page-level' if engine == 'chromium' else 'page-level only (no CDP request log in this engine)',
              'root': 'repository' if root.resolve() == REPO else root.name, 'policy': policy, 'policyDelivery': 'response header on index.html',
              'served': {n: sha(root / n) for n in SERVED if (root / n).is_file()},
              'options': {'fragment': fragment, 'cells': selected, 'cyclesWaitMs': cycles_wait, 'cyclesSettleMs': cycles_settle, 'cyclesFreshPage': cycles_fresh, 'composedWaitMs': composed_wait, 'inPagePrayer': in_page_prayer},
              'cells': {}, 'console': [], 'cdp': [], 'crashes': []}
    cells = report['cells']

    def save():
        # Written after every cell, so a browser crash never loses completed cells.
        report['pass'] = report['complete'] and all(v['pass'] for v in cells.values())
        text = json.dumps(report, indent=2, ensure_ascii=False)
        for form in sorted({str(REPO), str(REPO).replace('\\', '\\\\'), REPO.as_posix(), str(root.resolve()), str(root.resolve()).replace('\\', '\\\\'), root.resolve().as_posix()}, key=len, reverse=True):
            text = text.replace(form, '<root>')
        (out / f'{engine}-report.json').write_text(text + '\n', encoding='utf-8')

    with sync_playwright() as p:
        browser = getattr(p, engine).launch(headless=not headed)
        report['browserVersion'] = browser.version
        ctx = browser.new_context(viewport={'width': 325, 'height': 530})
        ctx.add_init_script(INIT)
        if in_page_prayer:
            # Opt-in (ES21-12 precondition attempt): the enforced fixture CSP (connect-src 'self') blocks the
            # cross-origin prayer fetch before the Playwright route below can answer it, so the page never gets
            # prayer data. This answers the same controlled record inside the page, exactly as INIT already does
            # for the weather provider. Product code, CSP and every cell's pass condition are unchanged.
            ctx.add_init_script(PRAYER_IN_PAGE.replace('__RECORD__', json.dumps(record)))
        cdp_phase = {'value': 'load'}

        def open_page(fragment, label):
            pg = ctx.new_page()
            pg.on('console', lambda m: report['console'].append([label, m.type, m.text[:300]]) if m.type in ('error', 'warning') else None)
            pg.on('pageerror', lambda e: report['console'].append([label, 'pageerror', str(e)[:300]]))
            pg.on('crash', lambda _p: report['crashes'].append({'page': label, 'phase': cdp_phase['value']}))
            pg.route(lambda u: not u.startswith(origin), lambda r: r.abort())
            pg.route('https://api.aladhan.com/**', lambda r: prayer(r, record))
            pg.route(origin + '/index.html', lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8',
                                                                  headers={'Content-Security-Policy': policy}, body=index))
            pg.goto(origin + '/index.html' + fragment)
            return pg

        page = open_page(fragment, 'main')
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

        def mark(name, pg=None):
            cdp_phase['value'] = name; phase(pg or page, name)

        counts = lambda pg=None: (pg or page).evaluate(COUNTS)
        shot = lambda name, clip=None: page.screenshot(path=str(out / f'{engine}-{name}.png'), clip=clip)
        state = {'crashed': None}

        def cell(name, fn):
            if name not in selected:
                return
            if state['crashed']:
                cells[name] = {'pass': False, 'status': 'not-run', 'reason': 'page crashed in cell ' + state['crashed']}; save(); return
            try:
                fn()
            except Exception as error:   # record, never lose earlier cells
                text = f'{type(error).__name__}: {str(error)[:600]}'
                partial = {k: v for k, v in cells.get(name, {}).items() if k not in ('pass', 'status', 'error')}
                cells[name] = {'pass': False, 'status': 'crashed', 'error': text, 'phase': cdp_phase['value'], **partial}
                if re.search(r'crash|closed', text, re.I):
                    state['crashed'] = name
            save()

        def first_boot():
            ok = wait(page, READY, 60000); c = counts()
            # moonDisposed is null where the runtime does not expose the field (645b53cc); the claim is "not disposed".
            cells['first-boot'] = {'pass': bool(ok and c['sky'] == 1 and c['preview'] == 1 and c['moonRuntime'] and c['moonDisposed'] is not True and c['moonDetail']),
                                   'moonDisposedField': 'exposed' if c['moonDisposed'] is not None else 'absent', **c}
            shot('1-first-boot'); page.wait_for_timeout(1500)

        def live_handoff():
            mark('live-invalidation'); d0 = counts()['previewDraws']
            page.evaluate("()=>window.SalahRealSky.invalidate('driver live withdrawal')")
            inv = wait(page, f"()=>window.SalahSkyPreview.state.draws>{d0}", 10000)
            mark('active-retry'); d1 = counts()['previewDraws']
            page.evaluate('()=>window.SalahRealSkyAssets.retry()')
            ret = wait(page, f"()=>window.SalahSkyPreview.state.draws>{d1}", 10000) and wait(page, READY, 30000)
            cells['live-handoff'] = {'pass': bool(inv and ret and counts()['sky'] == 1), 'invalidationHandoff': inv, 'retryHandoff': ret, 'after': counts()}

        def retirement():
            # The finding needs a refined-composed card (the preview then holds an older mask) and moving clouds,
            # so the preview's pagehide handoff would publish a CHANGED mask. Record whether that precondition held.
            composed = wait(page, "()=>document.querySelector('.c').classList.contains('real-sky-composed')", composed_wait)
            mask = "()=>getComputedStyle(document.querySelector('.c')).getPropertyValue('--native-sun-cloud-mask').trim()"
            m1 = page.evaluate(mask); page.wait_for_timeout(1500); m2 = page.evaluate(mask)
            # Without a changing data-URL cloud mask the pagehide handoff has nothing new to publish and the cell
            # would pass vacuously; such a run is reported as precondition-not-met, never as a PASS.
            precondition = bool(composed and m2.startswith('url(') and m1 != m2)
            before = counts(); mark('retiring')
            page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))")
            page.wait_for_timeout(1000)
            ev = events_in(page, 'retiring'); after = counts()
            data_images = [x for x in ev['images'] if x['scheme'] in ('data', 'blob')]
            # Initiator classification (owner 10.6) from each event's JS stack; informational, the pass rule is unchanged.
            retirement_initiated = [x for x in data_images if RETIREMENT_STACK.search(x.get('stack', ''))]
            render_loop = [x for x in data_images if x not in retirement_initiated and RENDER_LOOP_STACK.search(x.get('stack', ''))]
            cdp_retiring = [x for x in report['cdp'] if x['phase'] == 'retiring']
            mark('resume'); page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))")
            resumed = wait(page, READY, 30000); r = counts()
            clean = bool(not data_images and not ev['violations'] and not cdp_retiring and after['sky'] == 0 and after['assets'] == 'suspended' and resumed and r['sky'] == 1)
            cells['retirement'] = {'pass': clean and precondition, **({} if precondition else {'status': 'precondition-not-met'}), 'cleanRetirement': clean,
                                   'maskChangingAtPagehide': precondition, 'maskPrefixes': [m1[:40], m2[:40]], 'refinedComposedBeforePagehide': composed, 'retiringImages': ev['images'],
                                   'initiators': {'retirementInitiated': len(retirement_initiated), 'renderLoop': len(render_loop),
                                                  'other': len(data_images) - len(retirement_initiated) - len(render_loop), 'cdpRetiringRequests': len(cdp_retiring)}, 'retiringViolations': ev['violations'], 'retiringCdp': cdp_retiring,
                                   'before': before, 'afterPagehide': after, 'resumed': r, 'requestLevel': engine == 'chromium'}
            shot('2-resumed')

        def construction():
            booted = wait(page, BOOTED, 60000)
            mark('construction'); base = counts(); cells['construction'] = {'baseline': base, 'nativeLoopStarted': booted}
            seq = {}
            for label, arm in (('contextRefusal1', 'failContext'), ('contextRefusal2', 'failContext'), ('intervalFailure', 'failInterval')):
                page.evaluate('a=>{window.__r0021[a]=1;}', arm); page.evaluate('()=>window.SalahRealSkyAssets.retry()'); page.wait_for_timeout(500)
                seq[label] = counts(); cells['construction'][label] = seq[label]
            page.evaluate('()=>window.SalahRealSkyAssets.retry()'); healed = wait(page, READY, 30000); f4 = counts()
            bal = lambda x: x['workersLive'] <= base['workersLive'] - 1 and x['vis'] <= base['vis'] - 1   # the retired refined owner's worker/listener are gone
            cells['construction'] = {'pass': bool(all(x['sky'] == 0 and x['assets'] == 'unavailable' and x['previewStatus'] == 'ready' and bal(x) for x in seq.values())
                                     and healed and f4['sky'] == 1 and f4['workersLive'] == base['workersLive'] and f4['vis'] == base['vis']),
                                     'baseline': base, 'nativeLoopStarted': booted, **seq, 'recovered': f4}

        def cycles():
            pg = open_page(HASH, 'cycles') if cycles_fresh else page
            if cycles_fresh:
                wait(pg, READY, 60000)
            booted = wait(pg, BOOTED, 60000)
            mark('cycles', pg); start = counts(pg); seen = []
            cells['cycles'] = {'start': start, 'cycles': seen, 'freshPage': cycles_fresh, 'waitMs': cycles_wait}
            for i in range(5):
                cdp_phase['value'] = f'cycles-{i}-pagehide'
                pg.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))"); pg.wait_for_timeout(cycles_wait)
                cdp_phase['value'] = f'cycles-{i}-pageshow'
                pg.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))"); wait(pg, READY, 30000)
                pg.wait_for_timeout(cycles_settle)   # see header: a zero settle crashes Firefox's content process on main and candidate
                seen.append(counts(pg))
            keys = ('sky', 'preview', 'detail', 'workersLive', 'urlsLive', 'vis')
            vis_log = pg.evaluate("()=>window.__r0021.visLog.filter(x=>x.phase.startsWith('cycles')||x.phase==='load')")
            cells['cycles'] = {'nativeLoopStarted': booted, 'visibilityListenerLog': vis_log, 'pass': all(all(s[k] == start[k] for k in keys) for s in seen), 'start': start, 'cycles': seen, 'freshPage': cycles_fresh, 'waitMs': cycles_wait, 'settleMs': cycles_settle}
            if cycles_fresh:
                pg.close()

        def moon_replay():
            mark('moon-replay')
            page.evaluate("()=>{window.__r0021.refs={runtime:window.SalahMoonRuntime,detail:window.SalahMoonDetail,initial:window.SalahMoonInitial};}")
            m0 = counts()
            outcome = page.evaluate("""async()=>{const text=await (await fetch('moon/moon-host.js')).text();const R=window.__r0021,n=R.errors.length;
              const s=document.createElement('script');s.textContent=text;document.head.append(s);s.remove();
              return {errors:R.errors.slice(n).map(e=>e.message),same:window.SalahMoonRuntime===R.refs.runtime&&window.SalahMoonDetail===R.refs.detail&&window.SalahMoonInitial===R.refs.initial,
                disposed:window.SalahMoonRuntime?.disposed??null};}""")
            page.wait_for_timeout(500); m1 = counts()
            cells['moon-replay'] = {'pass': bool(outcome['same'] and outcome['disposed'] is False and any('replay refused' in e for e in outcome['errors'])
                                    and all(m1[k] == m0[k] for k in ('detail', 'workersLive', 'urlsLive', 'vis'))), 'outcome': outcome, 'before': m0, 'after': m1}

        def recovery_visual():
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

        def night_cell():
            night = open_page(NIGHT, 'night'); wait(night, READY, 60000)
            for _ in range(3):
                night.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))"); night.wait_for_timeout(200)
                night.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))"); wait(night, READY, 30000)
                night.wait_for_timeout(cycles_settle)   # same Firefox synthetic-pagehide crash as the cycles cell
            night.wait_for_timeout(1500)
            box = night.evaluate("()=>{const r=document.querySelector('.mphoto')?.getBoundingClientRect();return r&&r.width>0?{x:Math.max(0,r.left-20),y:Math.max(0,r.top-20),width:r.width+40,height:r.height+40}:null}")
            night.screenshot(path=str(out / f'{engine}-4-night-card.png'))
            if box:
                night.screenshot(path=str(out / f'{engine}-4-night-moon-crop.png'), clip=box)
            truth = night.evaluate("()=>{try{return qaState().moonTruth??null}catch(e){return String(e)}}")
            cells['night'] = {'pass': bool(box), 'status': 'human-review', 'nightMoonCrop': bool(box), 'moonTruth': truth, 'nightCounts': night.evaluate(COUNTS)}
            night.close()

        def navigation():
            # Real navigation: the outgoing document retires for real (Chromium request log only).
            if engine != 'chromium':
                cells['navigation'] = {'pass': True, 'status': 'not-applicable', 'reason': 'no request-level instrument in this engine'}; return
            # Discriminating only when the outgoing card is refined-composed and its cloud mask is a changing
            # data URL; with the constant clear gradient there is nothing to publish (precondition-not-met, never PASS).
            composed = wait(page, "()=>document.querySelector('.c').classList.contains('real-sky-composed')", composed_wait)
            mask = "()=>getComputedStyle(document.querySelector('.c')).getPropertyValue('--native-sun-cloud-mask').trim()"
            m1 = page.evaluate(mask); page.wait_for_timeout(1500); m2 = page.evaluate(mask); mark('navigation')
            page.goto('about:blank'); page.wait_for_timeout(1000)
            nav = [x for x in report['cdp'] if x['phase'] == 'navigation']
            precondition = bool(composed and m2.startswith('url(') and m1 != m2)
            cells['navigation'] = {'pass': (not nav) and precondition, **({} if precondition else {'status': 'precondition-not-met'}),
                                   'maskChangingAtNavigation': precondition, 'maskPrefixes': [m1[:40], m2[:40]], 'refinedComposedBeforeNavigation': composed,
                                   'navigationDataBlobRequests': len(nav), 'navigationCdp': nav}

        for name, fn in (('first-boot', first_boot), ('live-handoff', live_handoff), ('retirement', retirement), ('construction', construction),
                         ('cycles', cycles), ('moon-replay', moon_replay), ('recovery-visual', recovery_visual), ('night', night_cell), ('navigation', navigation)):
            cell(name, fn)
        report['complete'] = state['crashed'] is None
        try:
            browser.close()
        except Exception as error:
            report['closeError'] = str(error)[:300]
    server.shutdown()
    save()
    print(json.dumps({'engine': engine, 'version': report['browserVersion'], 'pass': report['pass'], 'complete': report['complete'],
                      'cells': {k: (True if v['pass'] else v.get('status', False)) for k, v in cells.items()}, 'crashes': report['crashes']}))
    return report['pass']


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('--engine', choices=['chromium', 'firefox'], required=True)
    a.add_argument('--root', default=str(REPO))
    a.add_argument('--out', required=True)
    a.add_argument('--headed', action='store_true')
    a.add_argument('--cells', default=','.join(CELLS), help='comma-separated subset (bisection); execution order is fixed')
    a.add_argument('--cycles-wait-ms', type=int, default=200)
    a.add_argument('--cycles-fresh-page', action='store_true', help='run the cycles cell on a newly loaded page')
    a.add_argument('--composed-wait-ms', type=int, default=60000, help='retirement: wait up to this long for a refined-composed card')
    a.add_argument('--fragment', default=None, help='main page fragment (default: the plain fixture scene)')
    a.add_argument('--in-page-prayer', action='store_true', help='answer the controlled prayer record inside the page (the enforced CSP blocks the routed provider)')
    a.add_argument('--cycles-settle-ms', type=int, default=500, help='cycles: settle after each resumed READY (0 reproduces the Firefox crash)')
    o = a.parse_args(); out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    sys.exit(0 if run(o.engine, Path(o.root), out, o.headed, o.cells.split(','), o.cycles_wait_ms, o.cycles_fresh_page, o.composed_wait_ms, o.cycles_settle_ms, o.fragment, o.in_page_prayer) else 1)
