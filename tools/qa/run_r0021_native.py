"""R0021 bounded native observation: construction, retirement and replay ownership under an enforced CSP.

The root schedules native runs one at a time; do not run this concurrently with other
browser work. Serves the GENERATED page unchanged from --root and enforces the R0017 widget-fixture policy
(tests/widget-fixture.html) as a real Content-Security-Policy response header on index.html. Prayer and weather
providers are controlled (no provider claim); every other non-local host is aborted.

Evidence channels (each event carries the driver phase it occurred in):
 - init script: HTMLImageElement src assignments (prefix + JS stack), `securitypolicyviolation` events,
   Worker construction/termination (sky workers told apart by a native-sky.js stack), blob URL create/revoke,
   document `visibilitychange` listener balance (the Moon's listener told apart by its source text), rAF callbacks
   run per phase, trusted page-lifecycle events (pagehide/pageshow/visibilitychange/freeze/resume, with
   visibilityState), pending Image.decode() calls, and whole-page peaks of these counts;
 - sessionStorage trace (only while a cell sets `persist`): image/violation/lifecycle records and rAF counts are
   written synchronously, so they survive a real navigation that discards the outgoing document;
 - Chromium only: CDP Network.requestWillBeSent / loadingFailed (blockedReason) and Page.backForwardCacheNotUsed.
   Firefox has no CDP here: its retirement evidence is page-level only and is reported as such.

Cells (acceptance cells decide the run's overall `pass`; diagnostic cells are reported literally and never count):
 first-boot          sky/preview/Moon owners installed once; Moon runtime live with its own detail
 live-handoff        not retiring: live invalidation and active asset retry still run the preview handoff
 retirement-synthetic  DIAGNOSTIC (was `retirement` until 2026-11-11; pass rule unchanged): synthetic pagehide
                     dispatched into a visible, fully active document. NO data:/blob: image request, NO CSP violation
                     in the retiring phase; refined owner disposed; then synthetic persisted pageshow resumes. A real
                     pagehide never leaves a visible, fully active document behind (HTML "unload a document": the
                     page is hidden and then discarded or frozen in the back/forward cache, and the rendering update
                     with its rAF callbacks runs only for fully active documents), so the native render loop's live
                     preview presentation it records is an artifact of the synthetic event. The cell reports the rAF
                     callbacks run while retiring as that evidence. See docs/state-contracts/R0021.md "Completion
                     ledger 2026-11-11".
 retirement-bfcache  ACCEPTANCE oracle for retirement under a supported lifecycle: on a fresh page, real same-origin
                     navigation away, then history back. Same precondition as the synthetic cell (refined-composed
                     card and a changing data-URL cloud mask). Counts EVERY data:/blob: image assignment (page-level,
                     sessionStorage trace of the outgoing document) and, in Chromium, EVERY data:/blob: CDP request
                     in the retiring phase, with no exclusion; requires none, no CSP violation, and a ready refined sky
                     after the return (bfcache restore with pageshow.persisted, or a reload when the engine does not
                     use the back/forward cache; which one happened and the browser's reasons are reported).
                     Playwright launches Chromium with --disable-back-forward-cache; --enable-bfcache removes it. The
                     Playwright Firefox build disables the back/forward cache (its playwright.cfg), so Firefox
                     exercises the reload path.
 navigation          (Chromium) real navigation to about:blank: CDP shows no data:/blob: image request issued by the
                     outgoing document after the retirement mark; precondition as above, else precondition-not-met
 construction        injected 2D-context refusal (x2) and setInterval failure during retry: no orphan
                     .real-sky-canvas, worker/blob/listener balance restored, preview still ready; a healthy
                     retry yields exactly one canvas
 census              ES21-09: whole-page peaks across three active retries (replacement) and three live invalidations:
                     refined canvas, refined worker and refined blob URL each peak at <= 1 (no refined overlap), and
                     every count returns to its baseline; the overlap of all other resources is reported
 cycles              5 synthetic pagehide/pageshow(persisted) cycles: canvas/worker/listener counts constant
 moon-replay         re-executing the generated moon/moon-host.js over the live runtime is refused before
                     any mutation (same runtime/detail/initial objects, no new canvas/worker/URL)
 moon-construction   a real Moon wrapper construction failure in the browser (the Moon's own 250 ms poll interval, or
                     its deferred first frame, throws during construction) on a fresh page: registry and detail slots
                     clear, no Moon listener/interval left, the sky and prayer UI still work; then a fresh wrapper
                     install (moon/moon-host.js) succeeds
 retirement-cover-change  acceptance oracle for a changed-mask retirement (id kept stable for committed evidence; the
                     name overstates the cover change): precondition = the MEASURED difference between the preview's last
                     decoded mask and the composed data-URL mask at navigation. In the committed runs that difference
                     arose before the switched weather was served. Counting/pass rule as retirement-bfcache. It does not
                     itself enforce --reduced-motion; the report records options.reducedMotion and reducedMotionRequired.
 moon-asset-failure  a REALISTIC Moon failure: in a fresh context the fixture server answers 404 for the Moon worker's
                     terrain/colour assets on a clear night. The runtime stays registered (not half-built: one listener,
                     one poll interval, no live Moon worker), the calendar/fallback Moon stays visible (moon-ready,
                     screenshot), the card works; two retries while withheld are accepted and fail cleanly; after the
                     assets return one retry recovers; a further retry is refused (bounded)
 recovery-visual     screenshot + 3 s frame difference after the cycles (sky animating)
 night               night crop of the Moon for human opacity review (screenshots override metrics)
 presentation        DIAGNOSTIC capture for ES21-13: fixed scenes (simTime freezes the scene clock; Date.now is fixed;
                     reduced motion) photographed twice per tree; `--compare-presentation A B` decides candidate versus
                     control pixel agreement against each tree's own repeat noise. Screenshots are looked at.

Crash safety: the report is rewritten after every cell; a cell that throws is recorded as `crashed` (error text,
pass=false) and, after a browser/page crash, later cells as `not-run`. Firefox finding (2026-11-11, recorded in
docs/state-contracts/R0021.md): a synthetic pagehide dispatched immediately (<=~100 ms) after the resumed sky
reports READY crashes Firefox 153's content process on BOTH 645b53cc and the candidate, with or without this
driver's instrumentation; a >=200 ms settle, rapid active retry and raw worker create/terminate do not. The cycles
cell therefore settles --cycles-settle-ms (default 500) after each resume; --cycles-settle-ms 0 reproduces it.
Retirement precondition: on 2026-11-11 the enforced fixture CSP (connect-src 'self') blocked the cross-origin prayer
fetch before the Playwright route could answer it, so no prayer data arrived and no cloud was painted.
--in-page-prayer (opt-in; default runs are unchanged) answers the same controlled record inside the page. With it and
--fragment '...&simWx=3&simCloud=100&timeScale=4' the precondition holds.

Main control: run with --root <checkout of pre-R0021 main 32f97b06>. Expected FAIL there: retirement-bfcache and
navigation (one retirement-initiated preview mask Image), construction (orphan canvases), moon-replay (no refusal),
moon-construction (half-built runtime left registered). Expected PASS on both: first-boot, live-handoff, cycles,
census, recovery-visual (subject to human review).

  PYTHONUTF8=1 <venv-python> tools/qa/run_r0021_native.py --engine chromium --out <new-dir>
  PYTHONUTF8=1 <venv-python> tools/qa/run_r0021_native.py --engine firefox --out <new-dir>
  PYTHONUTF8=1 <venv-python> tools/qa/run_r0021_native.py --engine chromium --root <main-checkout> --out <new-dir>
  PYTHONUTF8=1 <venv-python> tools/qa/run_r0021_native.py --engine chromium --compare-presentation <dirA> <dirB> --out <new-dir>
"""
import argparse, base64, functools, hashlib, http.server, json, re, sys, threading, time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]
SERVED = ['index.html', 'real-sky/native-sky.js', 'real-sky/native-worker.js', 'real-sky/native-data.js',
          'moon/moon-host.js', 'moon/moon-worker.js', 'config.js']
HASH = '#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1'
NIGHT = '#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1&simTime=23:30&simMoon=0.5&simWax=1&simMoonAlt=40&simMoonH=180'
# Presentation scenes (ES21-13): simTime without timeScale freezes the scene clock; Date.now is fixed per page.
PRESENTATION_FIXED_UTC = '2026-11-11T12:00:00Z'
PRESENTATION_SCENES = {
    'day-broken': '#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1&simTime=12:30&simWx=2&simCloud=50',
    'night-half': NIGHT,
    'night-new': '#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1&simTime=23:30&simMoon=0.01&simWax=1&simMoonAlt=40&simMoonH=180',
    # Clear-sky scenes (added after review): the Sun's nucleus and the ashen new-moon disc are not hidden by cloud.
    'day-clear': '#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1&simTime=12:30&simWx=0&simCloud=0',
    'night-half-clear': NIGHT + '&simWx=0&simCloud=0',
    'night-new-clear': '#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1&simTime=23:30&simMoon=0.01&simWax=1&simMoonAlt=40&simMoonH=180&simWx=0&simCloud=0',
}
NIGHT_CLEAR = NIGHT + '&simWx=0&simCloud=0'
# Realistic Moon failure: the fixture server answers 404 for the Moon worker's terrain/colour assets.
MOON_ASSET_PATHS = ('/moon/assets/dem.bin.gz', '/moon/assets/colour.bin.gz')
AWAY = '__r0021_away.html'   # same-origin page served by a route (never a repository file)
AWAY_HTML = '<!doctype html><meta charset="utf-8"><title>away</title><p>R0021 navigation target</p>'
INIT = r"""(()=>{
 const R=window.__r0021={doc:Math.random().toString(36).slice(2,10),phase:'load',images:[],violations:[],workers:{made:0,ended:0,skyMade:0,skyEnded:0},urls:{made:0,revoked:0},
  skyUrls:new Set(),vis:0,moonVis:0,visLog:[],errors:[],persist:false,storeErrors:0,rafRuns:{},lifecycle:[],injections:[],moonIntervals:new Set(),decodes:{pending:0},peak:null};
 const mark=o=>Object.assign(o,{phase:R.phase,t:performance.now(),doc:R.doc});
 // Synchronous trace that survives a real navigation away (only while a cell sets R.persist).
 const store=o=>{if(!R.persist)return;try{const k='r0021-trace',a=JSON.parse(sessionStorage.getItem(k)||'[]');a.push(o);sessionStorage.setItem(k,JSON.stringify(a));}catch(e){R.storeErrors++;}};
 R.store=store;
 const live=()=>({sky:document.querySelectorAll('.real-sky-canvas').length,preview:document.querySelectorAll('.real-sky-preview').length,detail:document.querySelectorAll('.moon-detail-canvas').length,
  workersLive:R.workers.made-R.workers.ended,skyWorkersLive:R.workers.skyMade-R.workers.skyEnded,urlsLive:R.urls.made-R.urls.revoked,skyUrlsLive:R.skyUrls.size,vis:R.vis,moonVis:R.moonVis,pendingDecodes:R.decodes.pending});
 const peak=()=>{if(!R.peak)return;try{const c=live();for(const k in c)if(!(R.peak[k]>=c[k]))R.peak[k]=c[k];}catch(e){}};
 R.live=live;R.resetPeak=()=>{R.peak=live();};
 // Trusted lifecycle events, registered first so they run before the product's own listeners.
 const life=e=>{if(e.type==='pagehide'&&e.isTrusted){R.pagehideAt=performance.now();R.rafAfterPagehide=0;
   // Written at the pagehide itself, so a document in which no callback runs afterwards still reports 0 (never null).
   if(R.persist){try{sessionStorage.setItem('r0021-rafpost|'+R.doc,JSON.stringify({afterPagehide:0,pagehideAt:R.pagehideAt,times:R.rafTimes.slice(-60)}));}catch(x){R.storeErrors++;}}}
  if(e.type==='pageshow'&&e.isTrusted)R.pagehideAt=null;
  const o=mark({type:e.type,persisted:e.persisted??null,vis:document.visibilityState,trusted:e.isTrusted});R.lifecycle.push(o);store({kind:'lifecycle',...o});};
 R.pagehideAt=null;R.rafAfterPagehide=0;R.rafTimes=[];
 window.addEventListener('pagehide',life,true);
 window.addEventListener('pageshow',e=>{if(e.isTrusted&&e.persisted&&R.phase==='retiring')R.phase='restored';life(e);},true);
 document.addEventListener('visibilitychange',life,true);document.addEventListener('freeze',life,true);document.addEventListener('resume',life,true);
 const owners=new WeakMap();R.decodedMask={preview:null,refined:null,other:null};R.decodedAt={};
 const d=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src');
 Object.defineProperty(HTMLImageElement.prototype,'src',{configurable:true,get(){return d.get.call(this);},set(v){
  const s=String(v);if(s){const o=mark({prefix:s.slice(0,30),scheme:s.split(':')[0],stack:String(new Error().stack).split('\n').slice(1,9).join('\n')});R.images.push(o);if(o.scheme==='data'||o.scheme==='blob')store({kind:'image',...o});
   // Mask owner from the caller: the preview paints (paint -> publish), the refined host composes (compose -> publish).
   if(o.scheme==='data')owners.set(this,/(^|\n)\s*(at )?(\S+\.)?compose[ @(]/.test(o.stack)?'refined':/(^|\n)\s*(at )?(\S+\.)?paint[ @(]/.test(o.stack)?'preview':'other');}d.set.call(this,v);}});
 document.addEventListener('securitypolicyviolation',e=>{const o=mark({blockedURI:String(e.blockedURI).slice(0,40),directive:e.effectiveDirective,disposition:e.disposition});R.violations.push(o);store({kind:'violation',...o});},true);
 const W=window.Worker;window.Worker=class extends W{constructor(...a){super(...a);const sky=/native-sky\.js/.test(String(new Error().stack));this.__r0021sky=sky;R.workers.made++;if(sky)R.workers.skyMade++;peak();}
  terminate(){R.workers.ended++;if(this.__r0021sky&&!this.__r0021ended){this.__r0021ended=true;R.workers.skyEnded++;}return super.terminate();}};
 const cu=URL.createObjectURL,ru=URL.revokeObjectURL;
 URL.createObjectURL=o=>{R.urls.made++;const u=cu.call(URL,o);if(/native-sky\.js/.test(String(new Error().stack)))R.skyUrls.add(u);peak();return u;};
 URL.revokeObjectURL=u=>{R.urls.revoked++;R.skyUrls.delete(u);return ru.call(URL,u);};
 const add=EventTarget.prototype.addEventListener,rem=EventTarget.prototype.removeEventListener,live2=new WeakSet(),isMoon=f=>String(f).includes("clear('document hidden')");
 EventTarget.prototype.addEventListener=function(n,f,o){if(this===document&&n==='visibilitychange'&&f&&!live2.has(f)){live2.add(f);R.vis++;if(isMoon(f))R.moonVis++;R.visLog.push(mark({op:'add',stack:String(new Error().stack).split('\n').slice(1,5).join(' | ')}));peak();}return add.call(this,n,f,o);};
 EventTarget.prototype.removeEventListener=function(n,f,o){if(this===document&&n==='visibilitychange'&&f&&live2.has(f)){live2.delete(f);R.vis--;if(isMoon(f))R.moonVis--;R.visLog.push(mark({op:'remove',stack:String(new Error().stack).split('\n').slice(1,5).join(' | ')}));}return rem.call(this,n,f,o);};
 window.addEventListener('error',e=>R.errors.push(mark({message:String(e.message)})));
 // Canvas insertions and pending decodes update the whole-page peaks (census cell).
 for(const [proto,name] of [[Element.prototype,'prepend'],[Element.prototype,'append'],[Node.prototype,'appendChild'],[Node.prototype,'insertBefore'],
   [Element.prototype,'before'],[Element.prototype,'after'],[Element.prototype,'replaceWith'],[Node.prototype,'replaceChild']]){
  const f=proto[name];proto[name]=function(...a){const r=f.apply(this,a);if(a.some(n=>n instanceof HTMLCanvasElement))peak();return r;};}
 const dec=HTMLImageElement.prototype.decode;HTMLImageElement.prototype.decode=function(...a){R.decodes.pending++;peak();let p;try{p=dec.apply(this,a);}catch(e){R.decodes.pending--;throw e;}const done=()=>{R.decodes.pending--;};const img=this;
  p.then(()=>{done();const w=owners.get(img);if(w){R.decodedMask[w]='url("'+d.get.call(img)+'")';R.decodedAt[w]=performance.now();}},done);return p;};
 // rAF callbacks actually run, per phase (persisted while R.persist so a discarded document still reports them).
 // One-shot Moon first-frame construction failure (moon-construction cell, armed per page by window.__r0021_arm).
 const raf=window.requestAnimationFrame;
 window.requestAnimationFrame=function(cb){
  const arm=window.__r0021_arm;
  if(arm&&arm.kind==='moon-frame'&&!arm.used&&typeof cb==='function'&&String(cb).startsWith('()=>{startFrame=requestAnimationFrame(start);}')){arm.used=true;R.injections.push(mark({kind:'moon-frame'}));throw new Error('driver-injected Moon requestAnimationFrame failure');}
  return raf.call(window,function(t){const p=R.phase;R.rafRuns[p]=(R.rafRuns[p]||0)+1;
   // Measured split at the trusted pagehide: callbacks that actually run after it, with their times.
   const after=R.pagehideAt!==null;if(after)R.rafAfterPagehide++;if(R.persist&&R.rafTimes.length<400)R.rafTimes.push(Math.round(performance.now()));
   if(R.persist){try{sessionStorage.setItem('r0021-raf|'+R.doc+'|'+p,String(R.rafRuns[p]));sessionStorage.setItem('r0021-rafpost|'+R.doc,JSON.stringify({afterPagehide:R.rafAfterPagehide,pagehideAt:R.pagehideAt,times:R.rafTimes.slice(-60)}));}catch(e){R.storeErrors++;}}return cb.call(this,t);});
 };
 // One-shot construction-failure injection used only by the construction cell.
 const gc=HTMLCanvasElement.prototype.getContext;R.failContext=0;R.failInterval=0;
 HTMLCanvasElement.prototype.getContext=function(...a){if(R.failContext>0&&this.className==='real-sky-canvas'){R.failContext--;return null;}return gc.apply(this,a);};
 const si=window.setInterval,ci=window.clearInterval;
 window.setInterval=function(...a){if(R.failInterval>0){R.failInterval--;throw new Error('driver-injected setInterval failure');}
  const moon=typeof a[0]==='function'&&a[1]===250&&String(a[0])==='()=>poll()',arm=window.__r0021_arm;
  if(moon&&arm&&arm.kind==='moon-interval'&&!arm.used){arm.used=true;R.injections.push(mark({kind:'moon-interval'}));throw new Error('driver-injected Moon setInterval failure');}
  const id=si.apply(this,a);if(moon)R.moonIntervals.add(id);return id;};
 window.clearInterval=function(id){R.moonIntervals.delete(id);return ci.call(this,id);};
 // Controlled providers (as tools/qa/run_r000d_native.py): overcast, so the solar cloud mask is non-trivial.
 const nf=window.fetch.bind(window),iso=ms=>new Date(ms).toISOString().slice(0,16);
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){const w=Date.now(),m=Math.floor(w/60000)*60000,h=Math.floor(w/3600000)*3600000;
   const X=window.__r0021_wx||{code:3,cover:70};R.wxServed=(R.wxServed||0)+1;
   return json({timezone:'UTC',elevation:600,current:{time:iso(m),interval:900,weather_code:X.code,temperature_2m:20,apparent_temperature:19,
    relative_humidity_2m:40,dew_point_2m:6,wind_speed_10m:6,wind_direction_10m:180,wind_gusts_10m:9,cloud_cover:X.cover,precipitation:0,is_day:1},
    hourly:{time:[iso(h),iso(h+3600000)],temperature_2m:[20,19],weather_code:[X.code,X.code],precipitation:[0,0]}});}
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
# V8 stacks name the class ("at NativeSkyLifecycle.dispose (", "at present (" / "at loop ("); Firefox (SpiderMonkey)
# stacks are "fn@url:line:col" without the class, so the lifecycle dispose chain is "invalidate@…" directly followed
# by "dispose@…" (2026-11-11 fix: the first Firefox runs, b4-*, classified every event as `other`).
RETIREMENT_STACK = re.compile(r'NativeSkyLifecycle\.dispose|^invalidate@[^\n]*\ndispose@', re.M)
RENDER_LOOP_STACK = re.compile(r'present \(.*\n\s+at loop \(|^present@[^\n]*\n(?:[^\n]*\n)*?loop@', re.S | re.M)   # SalahSkyPreview.present called from the native rAF loop
COUNTS = """()=>{const R=window.__r0021;return {...R.live(),
 assets:window.SalahRealSkyAssets?.state.status??null,skyStatus:window.SalahRealSky?.state.status??null,previewStatus:window.SalahSkyPreview?.state.status??null,
 previewDraws:window.SalahSkyPreview?.state.draws??null,moonRuntime:!!window.SalahMoonRuntime,moonDisposed:window.SalahMoonRuntime?.disposed??null,moonDetail:!!window.SalahMoonDetail}}"""
READY = "()=>window.SalahRealSkyAssets?.state.status==='ready'&&window.SalahSkyPreview?.state.status==='ready'&&!!window.SalahRealSky"
COMPOSED = "()=>document.querySelector('.c').classList.contains('real-sky-composed')"
MASK = "()=>getComputedStyle(document.querySelector('.c')).getPropertyValue('--native-sun-cloud-mask').trim()"
# The native boot's render loop installs its own one-time document visibilitychange listener. In Firefox it
# can start after the sky is READY, so resource baselines wait for it (a boot listener is not a leak).
BOOTED = "()=>typeof _loopStarted!=='undefined'&&_loopStarted===true"
PRAYER_UI = r"""()=>{const t=document.querySelector('.times')?.innerText??'';return {fajr:/Fajr/i.test(t),time:/\d{1,2}:\d\d/.test(t),unavailable:/unavailable/i.test(t)}}"""
TRACE = """()=>{try{const raf={};for(let i=0;i<sessionStorage.length;i++){const k=sessionStorage.key(i);if(k.startsWith('r0021-raf|'))raf[k]=+sessionStorage.getItem(k);}
 return {trace:JSON.parse(sessionStorage.getItem('r0021-trace')||'[]'),raf};}catch(e){return {error:String(e),trace:[],raf:{}};}}"""
START_TRACE = """()=>{try{sessionStorage.removeItem('r0021-trace');for(let i=sessionStorage.length-1;i>=0;i--){const k=sessionStorage.key(i);if(k.startsWith('r0021-raf|'))sessionStorage.removeItem(k);}}catch(e){}
 const R=window.__r0021;R.persist=true;R.store({kind:'marker',doc:R.doc,vis:document.visibilityState});R.phase='retiring';return R.doc;}"""
# Pixel difference of two PNGs (base64), computed in a policy-free helper page, never in the widget document.
DIFF_JS = """async([a,b,diffImage])=>{const load=s=>new Promise((r,j)=>{const i=new Image();i.onload=()=>r(i);i.onerror=j;i.src='data:image/png;base64,'+s;});
 const [x,y]=await Promise.all([load(a),load(b)]);if(x.width!==y.width||x.height!==y.height)return {sizeMismatch:[x.width,x.height,y.width,y.height]};
 const c=document.createElement('canvas');c.width=x.width;c.height=x.height;const g=c.getContext('2d',{willReadFrequently:true});
 g.drawImage(x,0,0);const p=g.getImageData(0,0,c.width,c.height).data;g.clearRect(0,0,c.width,c.height);g.drawImage(y,0,0);const q=g.getImageData(0,0,c.width,c.height);
 let strict=0,thr=0,max=0,x0=1e9,y0=1e9,x1=-1,y1=-1;const out=new ImageData(c.width,c.height);
 for(let i=0;i<p.length;i+=4){const dd=Math.abs(p[i]-q.data[i])+Math.abs(p[i+1]-q.data[i+1])+Math.abs(p[i+2]-q.data[i+2])+Math.abs(p[i+3]-q.data[i+3]);
  const v=(p[i]+p[i+1]+p[i+2])/12;out.data[i]=out.data[i+1]=out.data[i+2]=v;out.data[i+3]=255;
  if(dd>0){strict++;const k=i/4,px=k%c.width,py=(k-px)/c.width;x0=Math.min(x0,px);y0=Math.min(y0,py);x1=Math.max(x1,px);y1=Math.max(y1,py);out.data[i]=255;out.data[i+1]=0;out.data[i+2]=255;}
  if(dd-Math.abs(p[i+3]-q.data[i+3])>6)thr++;max=Math.max(max,dd);}
 let png=null;if(diffImage){g.putImageData(out,0,0);png=c.toDataURL('image/png').split(',')[1];}
 const n=p.length/4;return {pixels:n,strictChanged:strict,strictFraction:strict/n,changedFraction6:thr/n,maxDelta:max,bbox:strict?[x0,y0,x1,y1]:null,png};}"""


def local_prefixes(extra=()):
    """Absolute local prefixes that must never reach a log or report: repository, served root, Python install, home."""
    out = set()
    for p, tag in [(REPO, '<repo>'), (Path(sys.prefix), '<python>'), (Path(sys.base_prefix), '<python>'), (Path.home(), '<home>')] + list(extra):
        p = str(Path(p).resolve())
        if len(p) < 4:
            continue
        for form in {p, p.replace('\\', '/'), p[0].lower() + p[1:], p[0].upper() + p[1:]}:
            out.add((form, tag)); out.add((form.replace('\\', '\\\\'), tag)); out.add((form.replace('\\', '/'), tag))
    return sorted(out, key=lambda x: -len(x[0]))


def sanitize(text, extra=()):
    """Replace every local absolute prefix in text (longest first)."""
    for form, tag in local_prefixes(extra):
        text = text.replace(form, tag)
    return text


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


CELLS = ['first-boot', 'live-handoff', 'retirement-synthetic', 'construction', 'census', 'cycles', 'moon-replay', 'recovery-visual', 'night',
         'retirement-bfcache', 'navigation', 'moon-construction', 'moon-asset-failure', 'retirement-cover-change', 'presentation']
FIREFOX_BFCACHE = ('disabled by the Playwright Firefox build: its playwright.cfg sets fission.bfcacheInParent=false and states that '
                   'BFCache is also disabled in content via a docShell property')


def run(engine, root, out, headed, selected=CELLS, cycles_wait=200, cycles_fresh=False, composed_wait=60000, cycles_settle=500, fragment=None,
        in_page_prayer=False, enable_bfcache=False, reduced_motion=False, precondition_rule='changing', moon_404_cacheable=False, cover_wait=90000):
    fragment = fragment or HASH
    policy = re.search(r'http-equiv="Content-Security-Policy" content="([^"]+)"', (REPO / 'tests/widget-fixture.html').read_text(encoding='utf-8')).group(1)
    index = (root / 'index.html').read_bytes()

    blocked, served_log = set(), []

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            path = self.path.split('?')[0]
            if path.startswith('/moon/'):
                served_log.append({'path': path, 'blocked': path in blocked, 't': round(time.monotonic(), 3)})
            if path in blocked:
                # Default: a non-cacheable failure (no-store), so a later retry reaches the server. --moon-404-cacheable
                # omits it: Firefox then serves the heuristically cached 404 to the product's force-cache fetch.
                self.send_response(404); self.send_header('Content-Type', 'text/plain')
                if not moon_404_cacheable:
                    self.send_header('Cache-Control', 'no-store')
                self.end_headers(); self.wfile.write(b'R0021 driver: asset withheld')
                return
            return super().do_GET()

    class Server(http.server.ThreadingHTTPServer):
        def handle_error(self, request, client_address):
            # A browser aborting a connection is expected; never print a traceback with local paths.
            kind, value = sys.exc_info()[:2]
            server_errors.append(sanitize(f'{kind.__name__}: {value}', [(root, '<root>')])[:200])
    server_errors = []
    server = Server(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    origin = f'http://127.0.0.1:{server.server_address[1]}'
    record = json.loads((REPO / 'tests/r0002-ordinary.json').read_text(encoding='utf-8'))
    prayer_script = PRAYER_IN_PAGE.replace('__RECORD__', json.dumps(record))
    report = {'schema': 'r0021-native/3', 'engine': engine, 'headed': headed, 'out': out.name, 'complete': False,
              'evidenceLevel': 'request-level (CDP) and page-level' if engine == 'chromium' else 'page-level only (no CDP request log in this engine)',
              'root': 'repository' if root.resolve() == REPO else root.name, 'policy': policy, 'policyDelivery': 'response header on index.html',
              'served': {n: sha(root / n) for n in SERVED if (root / n).is_file()},
              'options': {'fragment': fragment, 'cells': selected, 'cyclesWaitMs': cycles_wait, 'cyclesSettleMs': cycles_settle, 'cyclesFreshPage': cycles_fresh,
                          'composedWaitMs': composed_wait, 'inPagePrayer': in_page_prayer, 'enableBfcache': enable_bfcache, 'reducedMotion': reduced_motion,
                          'preconditionRule': precondition_rule, 'moon404Cacheable': moon_404_cacheable, 'coverWaitMs': cover_wait},
              'bfcache': ('launched without --disable-back-forward-cache' if enable_bfcache else 'Playwright default (--disable-back-forward-cache)') if engine == 'chromium' else FIREFOX_BFCACHE,
              'cells': {}, 'console': [], 'cdp': [], 'bfcacheNotUsed': [], 'crashes': [], 'serverErrors': server_errors}
    cells = report['cells']

    def save():
        # Written after every cell, so a browser crash never loses completed cells. Diagnostic cells
        # (acceptance:false) are reported literally and never count toward the overall pass.
        acceptance = {k: v for k, v in cells.items() if v.get('acceptance', True)}
        report['diagnosticCells'] = {k: v.get('status', v['pass']) if not v['pass'] else True for k, v in cells.items() if not v.get('acceptance', True)}
        report['pass'] = bool(report['complete'] and acceptance and all(v['pass'] for v in acceptance.values()))
        text = sanitize(json.dumps(report, indent=2, ensure_ascii=False), [(root, '<root>')])
        (out / f'{engine}-report.json').write_text(text + '\n', encoding='utf-8')

    with sync_playwright() as p:
        launch = {'headless': not headed}
        if engine == 'chromium' and enable_bfcache:
            launch['ignore_default_args'] = ['--disable-back-forward-cache']
        browser = getattr(p, engine).launch(**launch)
        report['browserVersion'] = browser.version

        def new_context(**extra):
            c = browser.new_context(viewport={'width': 325, 'height': 530}, **({'reduced_motion': 'reduce'} if reduced_motion else {}), **extra)
            c.add_init_script(INIT)
            if in_page_prayer:
                # Opt-in (ES21-12 precondition): the enforced fixture CSP (connect-src 'self') blocks the cross-origin
                # prayer fetch before the Playwright route below can answer it, so the page never gets prayer data.
                # This answers the same controlled record inside the page, exactly as INIT does for the weather
                # provider. Product code, CSP and every cell's pass condition are unchanged.
                c.add_init_script(prayer_script)
            return c
        ctx = new_context()
        cdp_phase = {'value': 'load'}

        def open_page(fragment, label, context=None, scripts=()):
            pg = (context or ctx).new_page()
            for s in scripts:
                pg.add_init_script(s)
            pg.on('console', lambda m: report['console'].append([label, m.type, m.text[:300]]) if m.type in ('error', 'warning') else None)
            pg.on('pageerror', lambda e: report['console'].append([label, 'pageerror', str(e)[:300]]))
            pg.on('crash', lambda _p: report['crashes'].append({'page': label, 'phase': cdp_phase['value']}))
            pg.route(lambda u: not u.startswith(origin), lambda r: r.abort())
            pg.route('https://api.aladhan.com/**', lambda r: prayer(r, record))
            pg.route(origin + '/index.html', lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8',
                                                                  headers={'Content-Security-Policy': policy}, body=index))
            pg.route(origin + '/' + AWAY, lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=AWAY_HTML))
            pg.goto(origin + '/index.html' + fragment)
            return pg

        def attach_cdp(pg, label):
            # Chromium request-level channel for one page: every data:/blob: request with its phase, and the
            # browser's own back/forward-cache refusal reasons.
            if engine != 'chromium':
                return None
            s = pg.context.new_cdp_session(pg); s.send('Network.enable'); s.send('Page.enable')
            ids = {}

            def sent(e):
                url = e['request']['url']
                if url.startswith(('data:', 'blob:')):
                    ids[e['requestId']] = len(report['cdp'])
                    report['cdp'].append({'page': label, 'phase': cdp_phase['value'], 'type': e.get('type'), 'prefix': url[:30], 'frame': e.get('frameId'),
                                          'initiator': json.dumps(e.get('initiator', {}))[:1500]})

            def failed(e):
                if e['requestId'] in ids:
                    report['cdp'][ids[e['requestId']]].update(failed=True, blockedReason=e.get('blockedReason'), canceled=e.get('canceled'))
            s.on('Network.requestWillBeSent', sent); s.on('Network.loadingFailed', failed)
            s.on('Page.backForwardCacheNotUsed', lambda e: report['bfcacheNotUsed'].append({'page': label, 'phase': cdp_phase['value'],
                 'explanations': e.get('notRestoredExplanations'), 'tree': json.dumps(e.get('notRestoredExplanationsTree'))[:3000]}))
            return s

        page = open_page(fragment, 'main')
        attach_cdp(page, 'main')

        def mark(name, pg=None):
            cdp_phase['value'] = name; phase(pg or page, name)

        counts = lambda pg=None: (pg or page).evaluate(COUNTS)
        shot = lambda name, clip=None, pg=None: (pg or page).screenshot(path=str(out / f'{engine}-{name}.png'), clip=clip)
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
                cells[name] = {**partial, 'pass': False, 'status': 'crashed', 'error': text, 'phase': cdp_phase['value']}
                if re.search(r'crash|closed', text, re.I):
                    state['crashed'] = name
            save()

        def precondition_of(pg, rule='changing'):
            # The finding needs a refined-composed card (the preview then holds an older mask) and moving clouds, so
            # a retirement handoff would publish a CHANGED mask. Without it the cell would pass vacuously.
            # rule='published' (reduced-motion variant, retirement-bfcache only): a data-URL cloud mask is published on a
            # composed card. Under reduced motion the mask may hold still; a PASS under this rule is discriminating only
            # when the same run's control FAILs, which the ledger states for every such pair.
            composed = wait(pg, COMPOSED, composed_wait)
            m1 = pg.evaluate(MASK); pg.wait_for_timeout(1500); m2 = pg.evaluate(MASK)
            if rule == 'published':
                return bool(composed and m2.startswith('url(')), composed, [m1[:40], m2[:40], 'changed' if m1 != m2 else 'unchanged']
            return bool(composed and m2.startswith('url(') and m1 != m2), composed, [m1[:40], m2[:40]]

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
            shot('1b-live-handoff-invalidation')   # the handoff pixels, for human review
            mark('active-retry'); d1 = counts()['previewDraws']
            page.evaluate('()=>window.SalahRealSkyAssets.retry()')
            ret = wait(page, f"()=>window.SalahSkyPreview.state.draws>{d1}", 10000) and wait(page, READY, 30000)
            cells['live-handoff'] = {'pass': bool(inv and ret and counts()['sky'] == 1), 'invalidationHandoff': inv, 'retryHandoff': ret, 'after': counts()}

        def retirement_synthetic():
            # DIAGNOSTIC: unsupported lifecycle (see the header). The pass rule is the original one, unchanged.
            precondition, composed, prefixes = precondition_of(page)
            before = counts(); mark('retiring')
            page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}))")
            page.wait_for_timeout(1000)
            ev = events_in(page, 'retiring'); after = counts()
            raf_retiring = page.evaluate("()=>window.__r0021.rafRuns.retiring||0")
            vis_at_pagehide = page.evaluate("()=>document.visibilityState")
            data_images = [x for x in ev['images'] if x['scheme'] in ('data', 'blob')]
            # Initiator classification (owner 10.6) from each event's JS stack; informational, the pass rule is unchanged.
            retirement_initiated = [x for x in data_images if RETIREMENT_STACK.search(x.get('stack', ''))]
            render_loop = [x for x in data_images if x not in retirement_initiated and RENDER_LOOP_STACK.search(x.get('stack', ''))]
            cdp_retiring = [x for x in report['cdp'] if x['phase'] == 'retiring' and x.get('page') == 'main']
            mark('resume'); page.evaluate("()=>window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}))")
            resumed = wait(page, READY, 30000); r = counts()
            clean = bool(not data_images and not ev['violations'] and not cdp_retiring and after['sky'] == 0 and after['assets'] == 'suspended' and resumed and r['sky'] == 1)
            cells['retirement-synthetic'] = {'pass': clean and precondition, **({} if precondition else {'status': 'precondition-not-met'}), 'acceptance': False,
                                             'role': 'diagnostic: synthetic pagehide into a visible, fully active document (unsupported lifecycle); never counted as pass',
                                             'cleanRetirement': clean, 'maskChangingAtPagehide': precondition, 'maskPrefixes': prefixes, 'refinedComposedBeforePagehide': composed,
                                             'documentVisibilityAfterPagehide': vis_at_pagehide, 'rafCallbacksWhileRetiring': raf_retiring, 'retiringImages': ev['images'],
                                             'initiators': {'retirementInitiated': len(retirement_initiated), 'renderLoop': len(render_loop),
                                                            'other': len(data_images) - len(retirement_initiated) - len(render_loop), 'cdpRetiringRequests': len(cdp_retiring)},
                                             'retiringViolations': ev['violations'], 'retiringCdp': cdp_retiring,
                                             'before': before, 'afterPagehide': after, 'resumed': r, 'requestLevel': engine == 'chromium'}
            shot('2-resumed')

        def retirement_bfcache(name='retirement-bfcache', label='bfcache', scripts=(), frag=None, precheck=None, rule=None):
            # ACCEPTANCE: a supported lifecycle. Real same-origin navigation away, then history back, on a fresh page.
            rule = rule or precondition_rule
            pg = open_page(frag or fragment, label, scripts=scripts); attach_cdp(pg, label)
            ready = wait(pg, READY, 60000)
            precondition, composed, prefixes = (precheck or (lambda q: precondition_of(q, rule)))(pg)
            before = counts(pg)
            cdp_phase['value'] = 'retiring'; doc = pg.evaluate(START_TRACE)   # also sets the page phase to 'retiring'
            pg.goto(origin + '/' + AWAY)
            pg.wait_for_timeout(1000)
            cdp_phase['value'] = 'restore'
            pg.go_back(wait_until='commit')
            wait(pg, "()=>!!window.__r0021", 30000)
            back_doc = pg.evaluate('()=>window.__r0021.doc')
            persisted = back_doc == doc
            data = pg.evaluate(TRACE); pg.evaluate('()=>{window.__r0021.persist=false;}')
            outgoing = [x for x in data['trace'] if x.get('doc') == doc]
            marker = any(x['kind'] == 'marker' for x in outgoing)
            images = [x for x in outgoing if x['kind'] == 'image' and x['phase'] == 'retiring' and x['scheme'] in ('data', 'blob')]
            violations = [x for x in outgoing if x['kind'] == 'violation' and x['phase'] == 'retiring']
            lifecycle = [x for x in data['trace'] if x['kind'] == 'lifecycle']
            raf_retiring = data['raf'].get(f'r0021-raf|{doc}|retiring', 0)
            raf_post = pg.evaluate(f"()=>{{try{{return JSON.parse(sessionStorage.getItem('r0021-rafpost|{doc}')||'null')}}catch(e){{return String(e)}}}}")
            pagehide_t = next((x['t'] for x in lifecycle if x.get('doc') == doc and x['type'] == 'pagehide'), None)
            memory = pg.evaluate("()=>{const R=window.__r0021;return {images:R.images.filter(x=>x.phase==='retiring'&&(x.scheme==='data'||x.scheme==='blob')),violations:R.violations.filter(x=>x.phase==='retiring'),storeErrors:R.storeErrors}}") if persisted else None
            cdp_retiring = [x for x in report['cdp'] if x['phase'] == 'retiring' and x.get('page') == label]
            not_restored = pg.evaluate("()=>{try{const n=performance.getEntriesByType('navigation')[0];return n&&n.notRestoredReasons?JSON.parse(JSON.stringify(n.notRestoredReasons)):null}catch(e){return String(e)}}")
            resumed = wait(pg, READY, 60000); r = counts(pg)
            retirement_initiated = [x for x in images if RETIREMENT_STACK.search(x.get('stack', ''))]
            clean = bool(marker and not images and not violations and not (memory and (memory['images'] or memory['violations'])) and not cdp_retiring
                         and resumed and r['sky'] == 1)
            cells[name] = {'pass': bool(ready and clean and precondition), **({} if precondition else {'status': 'precondition-not-met'}),
                                           # A 'published' (static-mask) precondition cannot discriminate: the control publishes nothing either.
                                           **({'acceptance': False, 'nonDiscriminating': True} if rule == 'published' else {}),
                                           'return': 'bfcache-restore (pageshow.persisted)' if persisted else 'reload (back/forward cache not used)',
                                           'persisted': persisted, 'bfcache': report['bfcache'], 'notRestoredReasons': not_restored,
                                           'bfcacheNotUsed': [x for x in report['bfcacheNotUsed'] if x['page'] == label],
                                           'cleanRetirement': clean, 'traceMarker': marker, 'maskChangingAtNavigation': precondition, 'maskPrefixes': prefixes,
                                           'refinedComposedBeforeNavigation': composed, 'retiringImages': images, 'retiringViolations': violations,
                                           'retiringImagesInMemory': memory, 'retiringCdp': cdp_retiring, 'rafCallbacksWhileRetiring': raf_retiring,
                                           'preconditionRule': rule, 'trustedPagehideAt': pagehide_t,
                                           'rafAfterTrustedPagehide': raf_post.get('afterPagehide') if isinstance(raf_post, dict) else raf_post,
                                           'rafCallbackTimesTail': raf_post.get('times') if isinstance(raf_post, dict) else None,
                                           'lifecycleEvents': lifecycle, 'initiators': {'retirementInitiated': len(retirement_initiated), 'other': len(images) - len(retirement_initiated),
                                                                                        'cdpRetiringRequests': len(cdp_retiring)},
                                           'before': before, 'afterReturn': r, 'readyAfterReturn': resumed, 'requestLevel': engine == 'chromium'}
            shot('2b-bfcache-return' if name == 'retirement-bfcache' else '2c-' + name + '-return', pg=pg)
            pg.close()

        def retirement_cover_change():
            # Reduced-motion reproduction attempt (one bounded attempt, 2026-11-11). Precondition, measured: at navigation
            # the composed mask is a data URL that differs from the preview's last DECODED mask (the only state in which
            # the control's retirement handoff creates a new Image; native-composition.mjs reuses displayed/decoded
            # masks). The in-page weather stub starts broken (code 2, cover 30); after the refined sky composes it switches
            # to overcast (code 3, cover 100); the cell navigates as soon as the difference is observed.
            # Caveat (2026-11-11 review): the id is kept stable for committed evidence, but in the committed runs the
            # difference arose before the switched weather was served (wxServed stayed 1); the refined composition
            # overtook the preview's last decode. The precondition is that MEASURED difference, not the cover change.
            # The cell does not itself enforce --reduced-motion (the evidence runs pass it; the report records it).
            probe = "()=>({composed:document.querySelector('.c').classList.contains('real-sky-composed'),mask:getComputedStyle(document.querySelector('.c')).getPropertyValue('--native-sun-cloud-mask').trim(),decoded:window.__r0021.decodedMask.preview,wx:window.__r0021.wxServed||0})"

            def precheck(pg):
                composed = wait(pg, COMPOSED, composed_wait); samples = []
                start = pg.evaluate(probe); samples.append({'t': 0, **{k: (v[:48] if isinstance(v, str) else v) for k, v in start.items()}})
                pg.evaluate("()=>{window.__r0021_wx={code:3,cover:100};}")
                t0 = time.monotonic(); met = False
                while time.monotonic() - t0 < cover_wait / 1000:
                    q = pg.evaluate(probe)
                    met = bool(q['composed'] and q['mask'].startswith('url(') and q['mask'] != q['decoded'])
                    if len(samples) < 200:
                        samples.append({'t': round(time.monotonic() - t0, 2), 'composed': q['composed'], 'mask': q['mask'][-24:], 'decoded': (q['decoded'] or '')[-24:], 'wx': q['wx'], 'differs': met})
                    if met:
                        break
                    pg.wait_for_timeout(250)
                cover_samples.extend(samples)
                return met, composed, [start['mask'][:40], 'differs-from-preview-decoded' if met else 'never-differed']

            cover_samples = []
            retirement_bfcache('retirement-cover-change', 'cover', scripts=["window.__r0021_wx={code:2,cover:30};"], precheck=precheck, rule='decoded-differs')
            cells['retirement-cover-change']['coverSamples'] = cover_samples[-60:]
            cells['retirement-cover-change']['coverWaitMs'] = cover_wait
            cells['retirement-cover-change']['preconditionNote'] = "precondition is the MEASURED difference between the preview's last decoded mask and the composed mask; in the committed runs (b16-b18) it arose before the switched weather was served (wxServed stayed 1): the refined composition overtook the preview's last decode, so the cover change is not what produced it"
            cells['retirement-cover-change']['reducedMotionRequired'] = 'not enforced by the cell; the reduced-motion evidence runs pass --reduced-motion'
            cells['retirement-cover-change']['reducedMotion'] = reduced_motion

        def construction():
            booted = wait(page, BOOTED, 60000)
            mark('construction'); base = counts(); cells['construction'] = {'baseline': base, 'nativeLoopStarted': booted}
            seq = {}
            for label, arm in (('contextRefusal1', 'failContext'), ('contextRefusal2', 'failContext'), ('intervalFailure', 'failInterval')):
                page.evaluate('a=>{window.__r0021[a]=1;}', arm); page.evaluate('()=>window.SalahRealSkyAssets.retry()'); page.wait_for_timeout(500)
                seq[label] = counts(); cells['construction'][label] = seq[label]
                if label == 'contextRefusal2':
                    seq[label]['prayerUi'] = page.evaluate(PRAYER_UI); shot('5-construction-unavailable')   # UI independence, human review
            page.evaluate('()=>window.SalahRealSkyAssets.retry()'); healed = wait(page, READY, 30000); f4 = counts()
            bal = lambda x: x['workersLive'] <= base['workersLive'] - 1 and x['vis'] <= base['vis'] - 1   # the retired refined owner's worker/listener are gone
            cells['construction'] = {'pass': bool(all(x['sky'] == 0 and x['assets'] == 'unavailable' and x['previewStatus'] == 'ready' and bal(x) for x in seq.values())
                                     and healed and f4['sky'] == 1 and f4['workersLive'] == base['workersLive'] and f4['vis'] == base['vis']),
                                     'baseline': base, 'nativeLoopStarted': booted, **seq, 'recovered': f4}

        def census():
            # ES21-09: whole-page peaks (sampled at every canvas insertion, worker/URL creation, listener add and
            # decode start) across replacement. The refined instance's own resources must never overlap.
            ready = wait(page, READY, 30000); booted = wait(page, BOOTED, 60000)
            mark('census'); base = counts(); page.evaluate('()=>window.__r0021.resetPeak()')
            steps = []
            for i in range(3):
                page.evaluate('()=>window.SalahRealSkyAssets.retry()'); ok = wait(page, READY, 30000); page.wait_for_timeout(500)
                steps.append({'step': f'active-retry-{i}', 'ready': ok, **counts()})
            for i in range(3):
                d0 = counts()['previewDraws']; page.evaluate("()=>window.SalahRealSky.invalidate('driver census invalidation')")
                ok = wait(page, f"()=>window.SalahSkyPreview.state.draws>{d0}", 10000); page.wait_for_timeout(300)
                steps.append({'step': f'live-invalidation-{i}', 'handoff': ok, **counts()})
            peak = page.evaluate('()=>window.__r0021.peak'); final = counts()
            keys = ('sky', 'preview', 'detail', 'workersLive', 'skyWorkersLive', 'urlsLive', 'skyUrlsLive', 'vis', 'moonVis')
            per_instance = {'refinedCanvas': 1, 'refinedWorker': 1, 'refinedBlobUrl': 1, 'previewCanvas': 1, 'moonDetailCanvas': 1}
            cells['census'] = {'pass': bool(ready and booted and all(s.get('ready', s.get('handoff')) for s in steps)
                                            and peak['sky'] <= 1 and peak['skyWorkersLive'] <= 1 and peak['skyUrlsLive'] <= 1 and peak['preview'] <= 1 and peak['detail'] <= 1
                                            and all(final[k] == base[k] for k in keys)),
                               'perInstanceBound': per_instance, 'baseline': base, 'peak': peak, 'final': final,
                               'temporaryOverlap': {k: peak[k] - base[k] for k in peak if isinstance(peak[k], (int, float)) and isinstance(base.get(k), (int, float))},
                               'steps': steps, 'note': 'pendingDecodes and all overlaps are reported, not judged; TA3 decode bounds stay source-asserted'}

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

        replay = """async()=>{const text=await (await fetch('moon/moon-host.js')).text();const R=window.__r0021,n=R.errors.length;
              const s=document.createElement('script');s.textContent=text;document.head.append(s);s.remove();
              return {errors:R.errors.slice(n).map(e=>e.message),same:window.SalahMoonRuntime===R.refs?.runtime&&window.SalahMoonDetail===R.refs?.detail&&window.SalahMoonInitial===R.refs?.initial,
                disposed:window.SalahMoonRuntime?.disposed??null,runtime:!!window.SalahMoonRuntime,detail:!!window.SalahMoonDetail};}"""

        def moon_replay():
            mark('moon-replay')
            page.evaluate("()=>{window.__r0021.refs={runtime:window.SalahMoonRuntime,detail:window.SalahMoonDetail,initial:window.SalahMoonInitial};}")
            m0 = counts()
            outcome = page.evaluate(replay)
            page.wait_for_timeout(500); m1 = counts()
            cells['moon-replay'] = {'pass': bool(outcome['same'] and outcome['disposed'] is False and any('replay refused' in e for e in outcome['errors'])
                                    and all(m1[k] == m0[k] for k in ('detail', 'workersLive', 'urlsLive', 'vis'))), 'outcome': outcome, 'before': m0, 'after': m1}

        def moon_construction():
            # A real Moon wrapper construction failure in the browser, then a fresh install.
            result = {}
            for kind in ('moon-interval', 'moon-frame'):
                label = 'moon-construction-' + kind
                pg = open_page(NIGHT, label, scripts=[f"window.__r0021_arm={{kind:'{kind}',used:false}};"] + ([] if in_page_prayer else [prayer_script]))
                ready = wait(pg, READY, 60000); booted = wait(pg, BOOTED, 60000); pg.wait_for_timeout(1000)
                failed = pg.evaluate("""()=>{const R=window.__r0021,m=window.SalahMoonRuntime;return {injections:R.injections.map(x=>x.kind),errors:R.errors.map(e=>e.message),
                   runtimeSlot:m===undefined?'undefined':m===null?'null':m.disposed===true?'disposed-registered':'live',detailSlot:window.SalahMoonDetail==null?'clear':'present',
                   moonVisListeners:R.moonVis,moonIntervalsLive:R.moonIntervals.size,detailCanvases:document.querySelectorAll('.moon-detail-canvas').length,nonSkyWorkersLive:(R.workers.made-R.workers.ended)-(R.workers.skyMade-R.workers.skyEnded)}}""")
                failed['prayerUi'] = pg.evaluate(PRAYER_UI); failed['counts'] = counts(pg)
                shot(f'6-{kind}-failed', pg=pg)
                unwound = bool(failed['injections'] == [kind] and any('driver-injected Moon' in e for e in failed['errors'])
                               and failed['runtimeSlot'] in ('undefined', 'null') and failed['detailSlot'] == 'clear'
                               and failed['moonVisListeners'] == 0 and failed['moonIntervalsLive'] == 0 and failed['detailCanvases'] == 0)
                functional = bool(ready and failed['counts']['sky'] == 1 and failed['counts']['previewStatus'] == 'ready'
                                  and failed['prayerUi']['fajr'] and failed['prayerUi']['time'] and not failed['prayerUi']['unavailable'])
                fresh = pg.evaluate(replay); pg.wait_for_timeout(1500)
                after = pg.evaluate("()=>{const R=window.__r0021;return {moonVisListeners:R.moonVis,moonIntervalsLive:R.moonIntervals.size,state:window.SalahMoonRuntime?.state?.status??null}}")
                shot(f'6-{kind}-reinstalled', pg=pg)
                reinstalled = bool(fresh['runtime'] and fresh['disposed'] is not True and fresh['detail'] and not any('replay refused' in e for e in fresh['errors'])
                                   and after['moonVisListeners'] == 1 and after['moonIntervalsLive'] == 1)
                result[kind] = {'pass': unwound and functional and reinstalled, 'unwound': unwound, 'cardFunctional': functional, 'reinstalled': reinstalled,
                                'nativeLoopStarted': booted, 'afterFailure': failed, 'reinstall': fresh, 'afterReinstall': after}
                pg.close()
            cells['moon-construction'] = {'pass': all(v['pass'] for v in result.values()), **result}

        def moon_asset_failure():
            # A REALISTIC Moon failure: the fixture answers 404 for the Moon worker's terrain/colour assets, on a clear
            # night in a fresh context (no browser cache). Observes the registered runtime's own failure path, the
            # visible calendar/fallback Moon, the card, and bounded retry; then assets return and one retry recovers.
            mctx = new_context()
            if not in_page_prayer:
                mctx.add_init_script(prayer_script)
            blocked.update(MOON_ASSET_PATHS); served_log.clear()
            moon_state = """()=>{const m=window.SalahMoonRuntime,R=window.__r0021,s=m?.state;return {registered:!!m,disposed:m?.disposed??null,status:s?.status??null,
              errors:(s?.errors??[]).slice(-3),retryCount:s?.retryCount??null,workerAlive:s?.workerAlive??null,visibleSource:s?.visibleSource??null,current:s?.current??null,
              moonReady:document.querySelector('.c').classList.contains('moon-ready'),moonVisibility:getComputedStyle(document.querySelector('.moon')).visibility,
              moonVisListeners:R.moonVis,moonIntervalsLive:R.moonIntervals.size,detailCanvases:document.querySelectorAll('.moon-detail-canvas').length,
              nonSkyWorkersLive:(R.workers.made-R.workers.ended)-(R.workers.skyMade-R.workers.skyEnded)}}"""
            try:
                pg = open_page(NIGHT_CLEAR, 'moon-asset-failure', context=mctx)
                ready = wait(pg, READY, 60000); booted = wait(pg, BOOTED, 60000)
                failed_seen = wait(pg, "()=>{const s=window.SalahMoonRuntime?.state;return !!s&&(s.status==='unavailable'||s.errors.length>0)}", 90000)
                pg.wait_for_timeout(1500)
                failed = pg.evaluate(moon_state); failed['prayerUi'] = pg.evaluate(PRAYER_UI); failed['counts'] = counts(pg)
                shot('7-moon-asset-failure', pg=pg)
                retries = []; hits = [len([x for x in served_log if x['blocked']])]
                for i in range(2):   # bounded retry while the assets are still withheld
                    n0 = len(served_log)
                    accepted = pg.evaluate('()=>window.SalahMoonRuntime.retry()')
                    wait(pg, "()=>{const s=window.SalahMoonRuntime.state;return !s.workerAlive&&s.status==='unavailable'}", 60000); pg.wait_for_timeout(500)
                    retries.append({'accepted': accepted, 'serverAssetRequests': len([x for x in served_log[n0:] if x['path'] in MOON_ASSET_PATHS]), **pg.evaluate(moon_state)})
                blocked.clear(); n0 = len(served_log)
                accepted = pg.evaluate('()=>window.SalahMoonRuntime.retry()')
                wait(pg, "()=>{const s=window.SalahMoonRuntime.state;return s.status!=='unavailable'&&s.workerAlive}", 60000)
                # FINAL settled state (not a transient): 10 s after the retry, the runtime must still be out of
                # 'unavailable' with a live worker, and this retry's asset requests must have reached the server.
                pg.wait_for_timeout(10000)
                after = pg.evaluate(moon_state); after['acceptedRetry'] = accepted
                after['serverAssetRequests'] = len([x for x in served_log[n0:] if x['path'] in MOON_ASSET_PATHS])
                recovered = bool(after['status'] != 'unavailable' and after['workerAlive'])
                shot('7-moon-asset-recovered', pg=pg)
                beyond = pg.evaluate('()=>window.SalahMoonRuntime.retry()')   # bound: refused while a worker is live or retryCount>=3
                withheld = [x for x in served_log if x['blocked']]
                # disposed is null where the runtime lacks the field (pre-R0021); the claim is "not disposed" (as first-boot).
                healthy_fallback = bool(failed['registered'] and failed['disposed'] is not True and failed['moonVisListeners'] == 1
                                        and failed['moonIntervalsLive'] == 1 and failed['detailCanvases'] <= 1 and failed['nonSkyWorkersLive'] == 0)
                visible = bool(failed['moonReady'] and failed['moonVisibility'] == 'visible')
                functional = bool(ready and failed['counts']['sky'] == 1 and failed['prayerUi']['fajr'] and failed['prayerUi']['time'] and not failed['prayerUi']['unavailable'])
                bounded = bool(all(r['accepted'] for r in retries) and all(r['moonVisListeners'] == 1 and r['moonIntervalsLive'] == 1 for r in retries) and beyond is False)
                cells['moon-asset-failure'] = {'pass': bool(withheld and failed_seen and healthy_fallback and visible and functional and bounded and recovered and after['moonVisListeners'] == 1),
                                               'injectionReached': bool(withheld), 'withheldRequests': withheld[:10], 'failureObserved': failed_seen,
                                               'registeredNotHalfBuilt': healthy_fallback, 'fallbackMoonVisible': visible, 'cardFunctional': functional,
                                               'boundedRetry': bounded, 'recoveredAfterAssetsReturn': recovered, 'recoveryRule': 'final state 10 s after the retry',
                                               'retryBeyondRefused': beyond is False, 'moon404Cacheable': moon_404_cacheable, 'failureServerAssetRequests': hits[0],
                                               'nativeLoopStarted': booted, 'afterFailure': failed, 'retriesWhileWithheld': retries, 'afterRecovery': after,
                                               'humanReview': [f'{engine}-7-moon-asset-failure.png', f'{engine}-7-moon-asset-recovered.png']}
                pg.close()
            finally:
                blocked.clear(); mctx.close()

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
            precondition, composed, prefixes = precondition_of(page); mark('navigation')
            page.goto('about:blank'); page.wait_for_timeout(1000)
            nav = [x for x in report['cdp'] if x['phase'] == 'navigation']
            cells['navigation'] = {'pass': (not nav) and precondition, **({} if precondition else {'status': 'precondition-not-met'}),
                                   'maskChangingAtNavigation': precondition, 'maskPrefixes': prefixes, 'refinedComposedBeforeNavigation': composed,
                                   'navigationDataBlobRequests': len(nav), 'navigationCdp': nav}

        def presentation():
            # DIAGNOSTIC capture (ES21-13). Own context: fixed Date.now, reduced motion, in-page prayer record.
            pctx = browser.new_context(viewport={'width': 325, 'height': 530}, reduced_motion='reduce')
            pctx.add_init_script(INIT); pctx.add_init_script(prayer_script)
            pctx.clock.set_fixed_time(PRESENTATION_FIXED_UTC)
            scenes = {}
            for name, frag in PRESENTATION_SCENES.items():
                pg = open_page(frag, 'presentation-' + name, context=pctx)
                ready = wait(pg, READY, 60000); composed = wait(pg, COMPOSED, composed_wait); pg.wait_for_timeout(3000)
                a = pg.screenshot(); pg.wait_for_timeout(2000); b = pg.screenshot()
                (out / f'{engine}-p-{name}-a.png').write_bytes(a); (out / f'{engine}-p-{name}-b.png').write_bytes(b)
                helper = pctx.new_page()
                noise = helper.evaluate(DIFF_JS, [base64.b64encode(a).decode(), base64.b64encode(b).decode(), False]); helper.close()
                noise.pop('png', None)
                scenes[name] = {'fragment': frag, 'ready': ready, 'composed': composed, 'sha256a': hashlib.sha256(a).hexdigest(), 'repeatNoise': noise,
                                'prayerUi': pg.evaluate(PRAYER_UI), 'moonTruth': pg.evaluate("()=>{try{return qaState().moonTruth??null}catch(e){return String(e)}}")}
                pg.close()
            pctx.close()
            cells['presentation'] = {'pass': all(s['ready'] and s['composed'] for s in scenes.values()), 'status': 'captured; verdict by --compare-presentation and human review',
                                     'acceptance': False, 'role': 'diagnostic capture for ES21-13', 'fixedUtc': PRESENTATION_FIXED_UTC, 'reducedMotion': True, 'scenes': scenes}

        for name, fn in (('first-boot', first_boot), ('live-handoff', live_handoff), ('retirement-synthetic', retirement_synthetic), ('construction', construction),
                         ('census', census), ('cycles', cycles), ('moon-replay', moon_replay), ('recovery-visual', recovery_visual), ('night', night_cell),
                         ('retirement-bfcache', retirement_bfcache), ('navigation', navigation), ('moon-construction', moon_construction),
                         ('moon-asset-failure', moon_asset_failure), ('retirement-cover-change', retirement_cover_change), ('presentation', presentation)):
            cell(name, fn)
        report['complete'] = state['crashed'] is None
        try:
            browser.close()
        except Exception as error:
            report['closeError'] = str(error)[:300]
    server.shutdown()
    save()
    print(json.dumps({'engine': engine, 'version': report['browserVersion'], 'pass': report['pass'], 'complete': report['complete'],
                      'cells': {k: (True if v['pass'] else v.get('status', False)) for k, v in cells.items()}, 'diagnostic': report['diagnosticCells'], 'crashes': report['crashes']}))
    return report['pass']


def compare_presentation(engine, a_dir, b_dir, out):
    """Candidate versus control pixel agreement for the presentation captures of one engine.

    A scene AGREES when the two trees' first captures are byte-for-byte equal in pixels (strict), or when their
    changed fraction (per-pixel RGB delta > 6) does not exceed the larger repeat noise either tree showed for that
    scene within its own run. Anything else DIFFERS and needs a human look at the written diff image."""
    ra = json.loads((a_dir / f'{engine}-report.json').read_text(encoding='utf-8'))
    rb = json.loads((b_dir / f'{engine}-report.json').read_text(encoding='utf-8'))
    sa, sb = ra['cells']['presentation']['scenes'], rb['cells']['presentation']['scenes']
    result = {'schema': 'r0021-presentation-compare/1', 'engine': engine, 'a': {'dir': a_dir.name, 'root': ra['root'], 'served': ra['served']},
              'b': {'dir': b_dir.name, 'root': rb['root'], 'served': rb['served']}, 'scenes': {}}
    with sync_playwright() as p:
        browser = p.chromium.launch(); pg = browser.new_page()
        for name in sorted(set(sa) & set(sb)):
            A = (a_dir / f'{engine}-p-{name}-a.png').read_bytes(); B = (b_dir / f'{engine}-p-{name}-a.png').read_bytes()
            d = pg.evaluate(DIFF_JS, [base64.b64encode(A).decode(), base64.b64encode(B).decode(), True])
            png = d.pop('png', None)
            if png:
                (out / f'{engine}-p-{name}-diff.png').write_bytes(base64.b64decode(png))
            noise = max(sa[name]['repeatNoise'].get('changedFraction6', 0), sb[name]['repeatNoise'].get('changedFraction6', 0))
            verdict = ('size-mismatch' if 'sizeMismatch' in d else 'identical' if d['strictChanged'] == 0
                       else 'within-repeat-noise' if d['changedFraction6'] <= noise and noise > 0 else 'differs')
            result['scenes'][name] = {'verdict': verdict, 'diff': d, 'repeatNoise6': noise, 'inputsReady': bool(sa[name]['ready'] and sa[name]['composed'] and sb[name]['ready'] and sb[name]['composed'])}
        browser.close()
    result['pass'] = bool(result['scenes']) and all(s['verdict'] in ('identical', 'within-repeat-noise') and s['inputsReady'] for s in result['scenes'].values())
    (out / f'{engine}-presentation-compare.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'engine': engine, 'pass': result['pass'], 'scenes': {k: v['verdict'] for k, v in result['scenes'].items()}}))
    return result['pass']


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('--engine', choices=['chromium', 'firefox'], required=True)
    a.add_argument('--root', default=str(REPO))
    a.add_argument('--out', required=True)
    a.add_argument('--headed', action='store_true')
    a.add_argument('--cells', default=','.join(CELLS), help='comma-separated subset (bisection); execution order is fixed')
    a.add_argument('--cycles-wait-ms', type=int, default=200)
    a.add_argument('--cycles-fresh-page', action='store_true', help='run the cycles cell on a newly loaded page')
    a.add_argument('--composed-wait-ms', type=int, default=60000, help='retirement/navigation: wait up to this long for a refined-composed card')
    a.add_argument('--fragment', default=None, help='main page fragment (default: the plain fixture scene)')
    a.add_argument('--in-page-prayer', action='store_true', help='answer the controlled prayer record inside the page (the enforced CSP blocks the routed provider)')
    a.add_argument('--cycles-settle-ms', type=int, default=500, help='cycles: settle after each resumed READY (0 reproduces the Firefox crash)')
    a.add_argument('--enable-bfcache', action='store_true', help='Chromium: launch without Playwright\'s --disable-back-forward-cache')
    a.add_argument('--reduced-motion', action='store_true', help='emulate prefers-reduced-motion: reduce for the main context')
    a.add_argument('--precondition', choices=['changing', 'published'], default='changing',
                   help="retirement-bfcache precondition: 'changing' data-URL mask (default) or 'published' data-URL mask (reduced-motion variant)")
    a.add_argument('--moon-404-cacheable', action='store_true', help='moon-asset-failure: send the withheld 404 without Cache-Control: no-store')
    a.add_argument('--cover-wait-ms', type=int, default=90000, help='retirement-cover-change: wait up to this long for the mask to differ from the preview decode')
    a.add_argument('--compare-presentation', nargs=2, metavar=('DIR_A', 'DIR_B'), help='compare two runs\' presentation captures instead of running cells')
    # An uncaught driver error must not print local absolute paths into a run log either.
    sys.excepthook = lambda kind, value, tb: sys.stderr.write(sanitize(''.join(__import__('traceback').format_exception(kind, value, tb))))
    o = a.parse_args(); out = Path(o.out); out.mkdir(parents=True, exist_ok=False)
    if o.compare_presentation:
        sys.exit(0 if compare_presentation(o.engine, Path(o.compare_presentation[0]), Path(o.compare_presentation[1]), out) else 1)
    unknown = [c for c in o.cells.split(',') if c not in CELLS]
    if unknown:
        a.error('unknown cells: ' + ','.join(unknown) + (' (retirement was renamed retirement-synthetic)' if 'retirement' in unknown else ''))
    sys.exit(0 if run(o.engine, Path(o.root), out, o.headed, o.cells.split(','), o.cycles_wait_ms, o.cycles_fresh_page, o.composed_wait_ms, o.cycles_settle_ms, o.fragment,
                      o.in_page_prayer, o.enable_bfcache, o.reduced_motion, o.precondition, o.moon_404_cacheable, o.cover_wait_ms) else 1)
