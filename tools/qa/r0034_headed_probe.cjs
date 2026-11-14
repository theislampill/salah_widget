'use strict';
// R0034 owner-artifact probe, HEADED: Firefox with hardware WebRender requested (or Chromium with GPU), DPR 1, the
// widget in a 325x530 iframe over a textured page, real-time clock at Central Florida 2026-11-13 15:15 local, clear
// weather fixture answered in-page, every non-loopback request aborted. The refined owner is re-invalidated every 400 ms
// for --hold ms so the preview with "Sky preview · refining…" stays on screen, then released so the refined
// frame composes. Captures the composited outer page (page.screenshot clip of the iframe) and the sky canvas
// readbacks in the preview state, the refined state and during the transition; layer toggles in the preview state.
// Usage: node tools/qa/r0034_headed_probe.cjs --root <tree> --out <dir> --engine firefox [--hold 9000] [--headed 1]
//        [--playwright <pkg>]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root),out=path.resolve(a.out),engine=a.engine||'firefox',hold=+(a.hold||9000),headed=a.headed!=='0';
fs.mkdirSync(out,{recursive:true});
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
   return json({timezone:'America/New_York',utc_offset_seconds:-new Date(w).getTimezoneOffset()*60,elevation:30,current:{time:iso(m),interval:900,weather_code:0,temperature_2m:70,apparent_temperature:70,
    relative_humidity_2m:55,dew_point_2m:53,wind_speed_10m:5,wind_direction_10m:90,wind_gusts_10m:8,cloud_cover:0,precipitation:0,is_day:1,visibility:24000},
    hourly:{time:[iso(h),iso(h+3600000)],temperature_2m:[70,69],weather_code:[0,0],precipitation:[0,0],cloud_cover:[0,0]}});}
  if(u.includes('api.rainviewer.com')){window.__calls.radar++;return Promise.reject(new TypeError('controlled radar unavailable'));}
  return nf(input,init);};
 // Hold the refined result back: re-invalidate the refined owner every 400 ms until HOLD ms after start. Each
 // invalidation withdraws the refined frame and hands the preview back with its "refining" badge, as a live
 // identity change does; in-flight results are rejected by the epoch fence.
 const start=performance.now(),HOLD=${hold};const iv=setInterval(()=>{if(performance.now()-start>HOLD){clearInterval(iv);return;}window.SalahRealSky?.invalidate?.('r0034 probe hold');},400);})();`;
const HF=`(d,w,x0,y0,x1,y1)=>{let s=0,n=0;const L=(x,y)=>{const i=(y*w+x)*4;return .2126*d[i]+.7152*d[i+1]+.0722*d[i+2];};
 for(let y=y0+1;y<y1-1;y++)for(let x=x0+1;x<x1-1;x++){s+=Math.abs(4*L(x,y)-L(x-1,y)-L(x+1,y)-L(x,y-1)-L(x,y+1));n++;}return s/n;}`;
const STATE=`(()=>{const s=window.SalahRealSky?.state,c=document.querySelector('.c'),hf=${HF};const canv={};
 for(const sel of ['.real-sky-canvas','.real-sky-preview']){const k=document.querySelector(sel);if(!k){canv[sel]=null;continue;}let d=null;try{d=k.getContext('2d').getImageData(0,0,325,530).data;}catch(e){}
  canv[sel]={vis:getComputedStyle(k).visibility,disp:getComputedStyle(k).display,hfFlatSky:d?hf(d,325,20,282,310,290):null};}
 return {t:Date.now(),badge:document.querySelector('.real-sky-status')?.textContent??null,status:s?.status??null,composed:!!c?.classList.contains('real-sky-composed'),
  previewReady:!!c?.classList.contains('real-sky-preview-ready'),epoch:s?.lifecycle?.epoch??null,accepted:s?.lifecycle?.accepted??null,canv};})()`;
const GPU=`(()=>{const c=document.createElement('canvas'),g=c.getContext('webgl')||c.getContext('experimental-webgl');let r=null,v=null;
 if(g){const x=g.getExtension('WEBGL_debug_renderer_info');r=x?g.getParameter(x.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER);v=x?g.getParameter(x.UNMASKED_VENDOR_WEBGL):g.getParameter(g.VENDOR);}
 return {userAgent:navigator.userAgent,devicePixelRatio,webglRenderer:r,webglVendor:v};})()`;
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const opts={headless:!headed};
 if(engine==='firefox')opts.firefoxUserPrefs={'gfx.webrender.all':true,'gfx.webrender.software':false,'layers.acceleration.force-enabled':true};
 if(engine==='chromium')opts.args=['--ignore-gpu-blocklist','--enable-gpu-rasterization'];
 const browser=await PW[engine].launch(opts);let closed=false;const close=async()=>{if(!closed){closed=true;await browser.close().catch(()=>{});server.close();}};
 try{
 const ctx=await browser.newContext({viewport:{width:400,height:600},deviceScaleFactor:1,timezoneId:'America/New_York',locale:'en-US'});
 const aborted=[];await ctx.route('**/*',route=>{const u=route.request().url();if(u.startsWith(base)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
  const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
  if(m)return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1])})});
  aborted.push(new URL(u).host);return route.abort();});
 await ctx.addInitScript(SHIM);
 const page=await ctx.newPage();await page.clock.install({time:Date.parse('2026-11-13T20:15:00Z')});await page.clock.resume();
 const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,200)));
 await page.goto(base+'/__host.html');const frame=()=>page.frames().find(f=>f.url().includes('index.html'));
 const gpu=await page.evaluate(GPU);const clip={x:30,y:20,width:325,height:530};
 const shot=async tag=>fs.writeFileSync(path.join(out,`${engine}-${tag}.png`),await page.screenshot({clip}));
 const canvasPng=async(sel,tag)=>{const url=await frame().evaluate(s=>{const k=document.querySelector(s);return k?k.toDataURL('image/png'):null;},sel);
  if(url)fs.writeFileSync(path.join(out,`${engine}-${tag}-canvas.png`),Buffer.from(url.split(',')[1],'base64'));return !!url;};
 const t0=Date.now(),trace=[];let n=0;const states={};
 while(Date.now()-t0<hold+5000){
  const f=frame();if(f){try{const s=await f.evaluate(STATE);trace.push({ms:Date.now()-t0,...s});
   if(!states.preview&&s.previewReady&&!s.composed&&/refining/.test(s.badge||'')&&Date.now()-t0>3000){
    states.preview=s;await shot('preview');await canvasPng('.real-sky-preview','preview');
    for(const [tag,css] of [['preview-nobackdrop','*{backdrop-filter:none!important}'],['preview-pixelated','canvas{image-rendering:pixelated!important}'],['preview-nopreviewcanvas','.real-sky-preview{visibility:hidden!important}']]){
     const h=await f.addStyleTag({content:css});await page.waitForTimeout(300);await shot(tag);await h.evaluate(e=>e.remove());}
   }
   if(s.composed&&!states.refined){states.transition=trace.slice(-3).map(x=>x.ms);}
   if(s.composed&&!states.refined&&Date.now()-t0>hold+1500){states.refined=s;await shot('refined');await canvasPng('.real-sky-canvas','refined');
    const h=await f.addStyleTag({content:'*{backdrop-filter:none!important}'});await page.waitForTimeout(300);await shot('refined-nobackdrop');await h.evaluate(e=>e.remove());}
  }catch(e){trace.push({ms:Date.now()-t0,error:String(e.message).slice(0,120)});}}
  const ms=Date.now()-t0;if(ms>hold-1500&&ms<hold+2500&&n<16){await shot('transition-'+String(n).padStart(2,'0'));n++;}
  await page.waitForTimeout(250);
 }
 const summary={engine,version:browser.version(),headed,hold,gpu,aborted:[...new Set(aborted)],errors,
  firstPreviewRefiningMs:trace.find(s=>/refining/.test(s.badge||''))?.ms??null,firstComposedMs:trace.find(s=>s.composed)?.ms??null,
  preview:states.preview?{badge:states.preview.badge,canv:states.preview.canv}:null,refined:states.refined?{badge:states.refined.badge,canv:states.refined.canv}:null};
 fs.writeFileSync(path.join(out,`${engine}.json`),JSON.stringify({summary,trace},null,1));console.log(JSON.stringify(summary));
 }finally{await close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
