'use strict';
// R003B slice S1 (CI-02) state-synchronised capture harness. Global Playwright, one engine/config per run.
// The tree is served from loopback; the widget sits in a 325x530 iframe on a textured host page (the owner's
// embedding); prayer records come from tests/r0002-ordinary.json, weather from an in-page clear-sky fixture, and
// every other non-loopback request is aborted (no provider is contacted). Mocked clock (installed, then resumed).
// The refined owner is re-invalidated every 400 ms for --hold ms so the preview with "Sky preview · refining…"
// stays on screen, then released. In the PREVIEW state and the REFINED state, for each variant (test-only injected
// CSS, never a product edit) it records, at one instant: canvas readbacks (PNG) of the preview and refined canvases,
// a pixel hash before and after the composited screenshot (sync proof), the composited screenshot of the iframe,
// producer state and frame identity, backing/CSS rects, DPR. A 100 ms time series spans the preview->refined
// handoff (layer visibility/display/opacity/z-order/DOM order, canvas hashes) with composited samples.
// Usage: node tools/qa/r003b_s1_capture.cjs --root <tree> --out <dir> --engine firefox|chromium|webkit
//   [--scene owner|day|fajr|night] [--dpr 1] [--headed 0|1] [--variants base,nopreview,...|all|min]
//   [--cloud <cover %, weather code 2>] [--ffdpp <layout.css.devPixelsPerPx>] [--wr hw|sw] [--hold 7000] [--tag <name>] [--playwright <pkg>]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root),engine=a.engine||'firefox',hold=+(a.hold||7000),headed=a.headed==='1';
const scene=a.scene||'owner',dpr=+(a.dpr||1),tag=a.tag||`${engine}-${scene}${a.cloud?'-cloud'+a.cloud:''}-dpr${dpr}${headed?'-headed':''}${a.ffdpp?'-ffdpp'+a.ffdpp:''}${a.wr?'-wr'+a.wr:''}`;
const out=path.resolve(a.out,tag);fs.mkdirSync(out,{recursive:true});
// Central Florida (the R0034 probe location), America/New_York. UTC instants on 2026-11-13/14.
const SCENES={owner:{utc:'2026-11-13T20:15:00Z',isDay:1},day:{utc:'2026-11-13T17:30:00Z',isDay:1},
 fajr:{utc:'2026-11-13T10:50:00Z',isDay:0},night:{utc:'2026-11-14T03:30:00Z',isDay:0}};
const S=SCENES[scene];if(!S)throw new Error('unknown scene '+scene);
const SKY='.real-sky-canvas,.real-sky-preview';
const VARIANTS={base:'',nopreview:'.real-sky-preview{visibility:hidden!important}',
 nobackdrop:'*{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}',
 onetoone:`${SKY}{inset:-1px!important;width:calc(100% + 2px)!important;height:calc(100% + 2px)!important}`,
 pixelated:`${SKY}{image-rendering:pixelated!important}`};
VARIANTS['nobackdrop+onetoone']=VARIANTS.nobackdrop+VARIANTS.onetoone;
// Diagnostic: the hidden DOM cloud canvas shown alone (sky canvases hidden), to register baked clouds against it.
VARIANTS.domclouds=`${SKY}{visibility:hidden!important}html body .c .wfx .cloudcanvas,html body .c.real-sky-composed .wfx .cloudcanvas{visibility:visible!important}`;
const vlist=a.variants==='min'?['base','onetoone']:(!a.variants||a.variants==='all')?Object.keys(VARIANTS):a.variants.split(',');
const ordinary=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json'),'utf8'));
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
function record(day){const r=JSON.parse(JSON.stringify(ordinary)),[d,mo,y]=day.split('-').map(Number);r.meta.timezone='America/New_York';
 r.date.gregorian={...r.date.gregorian,date:day,day:String(d).padStart(2,'0'),month:{number:mo,en:MONTHS[mo-1]},year:String(y)};return r;}
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream','.woff2':'font/woff2'};
const HOST=`<!doctype html><meta charset=utf-8><style>html,body{margin:0;height:100%}body{background:
 repeating-linear-gradient(37deg,#3a5a2a 0 3px,#6b7d4a 3px 7px,#2c3d22 7px 9px),radial-gradient(circle at 30% 40%,#cde 0,#6a8 40%,#253 100%);background-blend-mode:multiply}
 iframe{position:absolute;left:30px;top:20px;width:325px;height:530px;border:0;background:transparent}</style>
 <iframe id=w allowtransparency=true src="/index.html#lat=28.5383&lon=-81.3792&label=Central%20FL&method=2&tz=America%2FNew_York&seed=1"></iframe>`;
const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://x');if(u.pathname==='/__host.html'){res.writeHead(200,{'content-type':'text/html'});return res.end(HOST);}
 const p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
 if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);});
const SHIM=`(()=>{const nf=window.fetch.bind(window),iso=ms=>new Date(ms-new Date(ms).getTimezoneOffset()*60000).toISOString().slice(0,16);window.__calls={weather:0,radar:0};
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){window.__calls.weather++;const w=Date.now(),m=Math.floor(w/60000)*60000,h=Math.floor(w/3600000)*3600000;
   return json({timezone:'America/New_York',utc_offset_seconds:-new Date(w).getTimezoneOffset()*60,elevation:30,current:{time:iso(m),interval:900,weather_code:${a.cloud?2:0},temperature_2m:70,apparent_temperature:70,
    relative_humidity_2m:55,dew_point_2m:53,wind_speed_10m:5,wind_direction_10m:90,wind_gusts_10m:8,cloud_cover:${+(a.cloud||0)},precipitation:0,is_day:${S.isDay},visibility:24000},
    hourly:{time:[iso(h),iso(h+3600000)],temperature_2m:[70,69],weather_code:[${a.cloud?2:0},${a.cloud?2:0}],precipitation:[0,0],cloud_cover:[${+(a.cloud||0)},${+(a.cloud||0)}]}});}
  if(u.includes('api.rainviewer.com')){window.__calls.radar++;return Promise.reject(new TypeError('controlled radar unavailable'));}
  return nf(input,init);};
 if(window.top!==window){const start=performance.now(),HOLD=${hold};window.__hold={released:false};
  const iv=setInterval(()=>{if(performance.now()-start>HOLD){clearInterval(iv);window.__hold.released=true;return;}window.SalahRealSky?.invalidate?.('r003b-s1 probe hold');},400);}})();`;
// In-frame helpers: FNV-1a over RGBA, layer descriptors, element geometry, producer state.
const HELPERS=`window.__s1={hash(sel){const k=document.querySelector(sel);if(!k)return null;let d;try{d=k.getContext('2d').getImageData(0,0,k.width,k.height).data;}catch(e){return 'unreadable';}
  let h=2166136261>>>0;for(let i=0;i<d.length;i+=4){h=Math.imul(h^d[i],16777619);h=Math.imul(h^d[i+1],16777619);h=Math.imul(h^d[i+2],16777619);}return (h>>>0).toString(16);},
 layer(sel){const k=document.querySelector(sel);if(!k)return null;const s=getComputedStyle(k),r=k.getBoundingClientRect();
  return {backing:[k.width,k.height],rect:[r.left,r.top,r.width,r.height],ratio:[+(k.width/r.width).toFixed(5),+(k.height/r.height).toFixed(5)],
   visibility:s.visibility,display:s.display,opacity:s.opacity,zIndex:s.zIndex,imageRendering:s.imageRendering,domIndex:[...k.parentNode.children].indexOf(k)};},
 geom(){const q=s=>[...document.querySelectorAll(s)].map(e=>{const r=e.getBoundingClientRect();return [+r.left.toFixed(3),+r.top.toFixed(3),+r.width.toFixed(3),+r.height.toFixed(3)];});
  const o={};for(const s of ['.c','.h','.buckle','.e','.wt','.arc','.bar','.cn','.nt','.times','.p','.d','.left'])o[s]=q(s);return o;},
 state(){const s=window.SalahRealSky?.state,p=window.SalahSkyPreview?.state,c=document.querySelector('.c');
  return {badge:document.querySelector('.real-sky-status')?.textContent??null,refined:s?{status:s.status,draws:s.draws??null,utcMs:s.utcMs??null,epoch:s.lifecycle?.epoch??null,accepted:s.lifecycle?.accepted??null}:null,
   preview:p?{status:p.status,draws:p.draws??null,utcMs:p.utcMs??null}:null,composed:!!c?.classList.contains('real-sky-composed'),previewReady:!!c?.classList.contains('real-sky-preview-ready'),
   released:window.__hold?.released??null,clock:Date.now(),dpr:devicePixelRatio,visibilityState:document.visibilityState};}};`;
const GPU=`(()=>{const c=document.createElement('canvas'),g=c.getContext('webgl')||c.getContext('experimental-webgl');let r=null,v=null;
 if(g){const x=g.getExtension('WEBGL_debug_renderer_info');r=x?g.getParameter(x.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER);v=x?g.getParameter(x.UNMASKED_VENDOR_WEBGL):g.getParameter(g.VENDOR);}
 return {userAgent:navigator.userAgent,devicePixelRatio,webglRenderer:r,webglVendor:v,outerInner:[outerWidth,innerWidth],visualViewportScale:window.visualViewport?.scale??null};})()`;
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const opts={headless:!headed};
 if(engine==='firefox'){opts.firefoxUserPrefs={};
  if(a.wr==='hw')Object.assign(opts.firefoxUserPrefs,{'gfx.webrender.all':true,'gfx.webrender.software':false,'layers.acceleration.force-enabled':true});
  if(a.wr==='sw')Object.assign(opts.firefoxUserPrefs,{'gfx.webrender.software':true});
  if(a.ffdpp)opts.firefoxUserPrefs['layout.css.devPixelsPerPx']=String(a.ffdpp);}
 if(engine==='chromium'&&headed)opts.args=['--ignore-gpu-blocklist','--enable-gpu-rasterization'];
 const browser=await PW[engine].launch(opts);
 const meta={tag,engine,version:browser.version(),headed,scene,sceneUtc:S.utc,dpr,ffdpp:a.ffdpp??null,wr:a.wr??null,hold,variants:vlist,root:path.basename(root)};
 try{
 const ctx=await browser.newContext({viewport:{width:400,height:600},deviceScaleFactor:a.ffdpp?undefined:dpr,timezoneId:'America/New_York',locale:'en-US'});
 const aborted=[];await ctx.route('**/*',route=>{const u=route.request().url();if(u.startsWith(base)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
  const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
  if(m)return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1])})});
  aborted.push(new URL(u).host);return route.abort();});
 await ctx.addInitScript(SHIM);await ctx.addInitScript(HELPERS);
 const page=await ctx.newPage();await page.clock.install({time:Date.parse(S.utc)});await page.clock.resume();
 const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,200)));
 const t0=Date.now();await page.goto(base+'/__host.html');
 const frame=()=>page.frames().find(f=>f.url().includes('index.html'));
 meta.gpu=await page.evaluate(GPU);
 const sf=meta.gpu.devicePixelRatio,clip={x:30,y:20,width:325,height:530};
 const writePng=(name,url)=>{if(url)fs.writeFileSync(path.join(out,name),Buffer.from(url.split(',')[1],'base64'));};
 const captures=[];
 // One synchronised capture: hashes -> readbacks -> screenshot -> hashes. sync=true iff no canvas changed across it.
 async function capture(state,variant){const f=frame();
  const h=variant&&VARIANTS[variant]?await f.addStyleTag({content:VARIANTS[variant]}):null;
  await f.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));await page.waitForTimeout(250);
  const before=await f.evaluate(()=>({p:__s1.hash('.real-sky-preview'),r:__s1.hash('.real-sky-canvas'),st:__s1.state(),
   layers:{preview:__s1.layer('.real-sky-preview'),refined:__s1.layer('.real-sky-canvas')},geom:__s1.geom(),
   urls:{preview:document.querySelector('.real-sky-preview')?.toDataURL('image/png')??null,refined:document.querySelector('.real-sky-canvas')?.toDataURL('image/png')??null}}));
  const name=`${state}-${variant}`;fs.writeFileSync(path.join(out,name+'-composite.png'),await page.screenshot({clip}));
  const after=await f.evaluate(()=>({p:__s1.hash('.real-sky-preview'),r:__s1.hash('.real-sky-canvas'),st:__s1.state()}));
  if(variant==='base'){writePng(`${state}-preview-canvas.png`,before.urls.preview);writePng(`${state}-refined-canvas.png`,before.urls.refined);}
  if(h)await h.evaluate(e=>e.remove());
  const rec={state,variant,ms:Date.now()-t0,sync:before.p===after.p&&before.r===after.r&&before.st.composed===after.st.composed,hash:{preview:before.p,refined:before.r,previewAfter:after.p,refinedAfter:after.r},
   producer:before.st,layers:before.layers,geom:before.geom};captures.push(rec);return rec;}
 const series=[];let previewDone=false,refinedDone=false,n=0;
 while(Date.now()-t0<hold+9000&&!refinedDone){const f=frame();
  if(f){try{const s=await f.evaluate(()=>({...__s1.state(),layers:{preview:__s1.layer('.real-sky-preview'),refined:__s1.layer('.real-sky-canvas')},hp:__s1.hash('.real-sky-preview'),hr:__s1.hash('.real-sky-canvas')}));
   const ms=Date.now()-t0;series.push({ms,...s});
   if(!previewDone&&s.previewReady&&!s.composed&&/refining/.test(s.badge||'')&&ms>2500){previewDone=true;for(const vv of vlist)await capture('preview',vv);}
   if(previewDone&&s.released&&n<12&&ms%2==0){fs.writeFileSync(path.join(out,`handoff-${String(n).padStart(2,'0')}-${s.composed?'composed':'preview'}.png`),await page.screenshot({clip}));series[series.length-1].shot=n;n++;}
   if(s.composed&&s.released&&!refinedDone){const first=series.find(x=>x.composed&&x.released);if(ms-first.ms>2500){refinedDone=true;for(const vv of vlist)await capture('refined',vv);}}
  }catch(e){series.push({ms:Date.now()-t0,error:String(e.message).slice(0,160)});}}
  await page.waitForTimeout(100);}
 const firstComposed=series.find(x=>x.composed&&x.released),firstReleased=series.find(x=>x.released);
 // Frame pacing in the refined state (3 s of rAF intervals in the widget frame) and JS heap where exposed.
 const perf=await frame().evaluate(()=>new Promise(res=>{const d=[];let last=performance.now();const t0=last;
  const step=t=>{d.push(t-last);last=t;if(t-t0<3000)requestAnimationFrame(step);else{d.sort((a,b)=>a-b);
   res({frames:d.length,meanMs:+(d.reduce((a,b)=>a+b,0)/d.length).toFixed(2),p95Ms:+d[Math.floor(d.length*.95)].toFixed(2),
    heapUsed:performance.memory?.usedJSHeapSize??null,canvasBackingBytes:[...document.querySelectorAll('canvas')].reduce((a,c)=>a+c.width*c.height*4,0)});}};
  requestAnimationFrame(step);})).catch(e=>({error:String(e.message).slice(0,120)}));
 const stale=series.filter(x=>x.composed&&x.layers?.preview&&x.layers.preview.display!=='none'&&x.layers.preview.visibility!=='hidden'&&+x.layers.preview.opacity>0);
 const summary={...meta,aborted:[...new Set(aborted)],errors,screenshotScale:sf,
  firstPreviewRefiningMs:series.find(x=>/refining/.test(x.badge||''))?.ms??null,firstComposedAfterReleaseMs:firstComposed?.ms??null,releaseToComposedMs:firstComposed&&firstReleased?firstComposed.ms-firstReleased.ms:null,perf,
  previewLayerCompositedWhileComposed:stale.length,samples:series.length,captures:captures.map(c=>({state:c.state,variant:c.variant,sync:c.sync,composed:c.producer.composed,badge:c.producer.badge,
   preview:c.layers.preview&&{ratio:c.layers.preview.ratio,rect:c.layers.preview.rect,vis:c.layers.preview.visibility,disp:c.layers.preview.display},refined:c.layers.refined&&{ratio:c.layers.refined.ratio,rect:c.layers.refined.rect,vis:c.layers.refined.visibility}}))};
 fs.writeFileSync(path.join(out,'capture.json'),JSON.stringify({summary,captures,series},null,1));
 console.log(JSON.stringify({tag,version:meta.version,renderer:meta.gpu.webglRenderer,dpr:sf,releaseToComposed:summary.releaseToComposedMs,perf,stale:stale.length,
  sync:captures.map(c=>c.state[0]+':'+c.variant+':'+(c.sync?'ok':'MOVED')).join(' '),errors:errors.length}));
 }finally{await browser.close().catch(()=>{});server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
