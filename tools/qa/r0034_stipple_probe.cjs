'use strict';
// R0034 owner-artifact probe: Central Florida, 2026-11-13 15:15 local (20:15Z), clear day, real-time clock
// (Playwright clock installed then resumed), widget in a 325x530 iframe on a textured page, every non-loopback
// request aborted; weather answered in-page from a fixture. Samples lifecycle every 250 ms and pixels every 1 s.
// Usage: node tools/qa/r0034_stipple_probe.cjs --root <tree> --out <dir> --engine chromium --dpr 1.25 [--seconds 20] [--playwright <pkg>]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root),out=path.resolve(a.out),dpr=+(a.dpr||1),secs=+(a.seconds||20),engine=a.engine||'chromium';
fs.mkdirSync(out,{recursive:true});
const ordinary=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json'),'utf8'));
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
function record(day){const r=JSON.parse(JSON.stringify(ordinary)),[d,mo,y]=day.split('-').map(Number);r.meta.timezone='America/New_York';
 r.date.gregorian={...r.date.gregorian,date:day,day:String(d).padStart(2,'0'),month:{number:mo,en:MONTHS[mo-1]},year:String(y)};return r;}
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream','.woff2':'font/woff2'};
const HOST=`<!doctype html><meta charset=utf-8><style>html,body{margin:0;height:100%}body{background:
 repeating-linear-gradient(37deg,#3a5a2a 0 3px,#6b7d4a 3px 7px,#2c3d22 7px 9px),linear-gradient(#8fa,#253);background-blend-mode:multiply}
 iframe{position:absolute;left:30px;top:20px;width:325px;height:530px;border:0;background:transparent}</style>
 <iframe id=w allowtransparency=true src="/index.html#lat=28.5383&lon=-81.3792&label=Central%20FL&method=2&tz=America%2FNew_York&seed=1"></iframe>`;
const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://x');if(u.pathname==='/__host.html'){res.writeHead(200,{'content-type':'text/html'});return res.end(HOST);}
 const p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
 if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);});
const SHIM=`(()=>{const nf=window.fetch.bind(window),iso=ms=>new Date(ms-new Date(ms).getTimezoneOffset()*60000).toISOString().slice(0,16);window.__calls={weather:0,radar:0};window.__wx={rh:55,cloud:0,wind:5};
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){window.__calls.weather++;const w=Date.now(),m=Math.floor(w/60000)*60000,h=Math.floor(w/3600000)*3600000;
   return json({timezone:'America/New_York',utc_offset_seconds:-new Date(w).getTimezoneOffset()*60,elevation:30,current:{time:iso(m),interval:900,weather_code:0,temperature_2m:70,apparent_temperature:70,
    relative_humidity_2m:window.__wx.rh,dew_point_2m:53,wind_speed_10m:window.__wx.wind,wind_direction_10m:90,wind_gusts_10m:8,cloud_cover:window.__wx.cloud,precipitation:0,is_day:1,visibility:24000},
    hourly:{time:[iso(h),iso(h+3600000)],temperature_2m:[70,69],weather_code:[0,0],precipitation:[0,0],cloud_cover:[0,0]}});}
  if(u.includes('api.rainviewer.com')){window.__calls.radar++;return Promise.reject(new TypeError('controlled radar unavailable'));}
  return nf(input,init);};})();`;
// High-frequency energy of a byte region: mean |4p - (left+right+up+down)| of luminance (smooth sky ~0).
const HF=`(d,w,x0,y0,x1,y1)=>{let s=0,n=0;const L=(x,y)=>{const i=(y*w+x)*4;return .2126*d[i]+.7152*d[i+1]+.0722*d[i+2];};
 for(let y=y0+1;y<y1-1;y++)for(let x=x0+1;x<x1-1;x++){s+=Math.abs(4*L(x,y)-L(x-1,y)-L(x+1,y)-L(x,y-1)-L(x,y+1));n++;}return s/n;}`;
const STATE=`(()=>{const s=window.SalahRealSky?.state,c=document.querySelector('.c'),hf=${HF};
 const canv={};for(const sel of ['.real-sky-canvas','.real-sky-preview']){const k=document.querySelector(sel);if(!k){canv[sel]=null;continue;}
  let d=null;try{d=k.getContext('2d').getImageData(0,0,325,530).data;}catch(e){}
  canv[sel]={vis:getComputedStyle(k).visibility,disp:getComputedStyle(k).display,cssW:k.getBoundingClientRect().width,cssH:k.getBoundingClientRect().height,
   hfFlatSky:d?hf(d,325,150,390,310,412):null,hfUpper:d?hf(d,325,200,120,320,180):null};}
 return {t:Date.now(),badge:document.querySelector('.real-sky-status')?.textContent??null,status:s?.status??null,reason:s?.reason??null,
  availability:s?.availability?.reason??null,epoch:s?.lifecycle?.epoch??null,accepted:s?.lifecycle?.accepted??null,invalidations:s?.lifecycle?.invalidations??null,
  composed:!!c?.classList.contains('real-sky-composed'),previewReady:!!c?.classList.contains('real-sky-preview-ready'),preview:window.SalahSkyPreview?.state?.status??null,
  pending:window.SalahSkyPreview?.state?.reason??null,calls:window.__calls,canv};})()`;
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const browser=await PW[engine].launch({headless:true});
 const ctx=await browser.newContext({viewport:{width:400,height:600},deviceScaleFactor:dpr,timezoneId:'America/New_York',locale:'en-US'});
 const aborted=[];await ctx.route('**/*',route=>{const u=route.request().url();if(u.startsWith(base)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
  const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
  if(m)return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1])})});
  aborted.push(new URL(u).host);return route.abort();});
 await ctx.addInitScript(SHIM);
 const page=await ctx.newPage();await page.clock.install({time:Date.parse(a.time||'2026-11-13T20:15:00Z')});await page.clock.resume();
 const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,200)));
 await page.goto(base+'/__host.html');const frame=()=>page.frames().find(f=>f.url().includes('index.html'));
 const t0=Date.now(),trace=[];let shot=0;
 while(Date.now()-t0<secs*1000){
  const f=frame();if(f){try{trace.push({ms:Date.now()-t0,...await f.evaluate(STATE)});}catch(e){trace.push({ms:Date.now()-t0,error:String(e.message).slice(0,120)});}}
  if((Date.now()-t0)>=shot*1000){fs.writeFileSync(path.join(out,`${engine}-dpr${dpr}-t${String(shot).padStart(2,'0')}.png`),await page.locator('#w').screenshot());shot++;}
  await page.waitForTimeout(250);
 }
 // Simulated live weather adoption that changes ONLY unconsumed fields (rh, wind): the accepted record is replaced
 // in the page exactly as fetchWeather assigns it. Records whether the refined frame is withdrawn ("refining…").
 const f=frame(),adoption=[];
 const before=await f.evaluate(()=>{const had=typeof weather!=='undefined'&&weather;if(had){weather={...weather,rh:(weather.rh??50)+7,wind:(weather.wind??3)+2};_renderDirty=true;}return {adopted:!!had};});
 const ta=Date.now();while(Date.now()-ta<8000){adoption.push({ms:Date.now()-ta,...await f.evaluate(STATE)});await page.waitForTimeout(250);}
 const adoptionSummary={...before,withdrawn:adoption.some(s=>!s.composed),refiningSamples:adoption.filter(s=>/refining/.test(s.badge||'')).length,
  recomposedMs:(()=>{const i=adoption.findIndex(s=>!s.composed);if(i<0)return null;const j=adoption.findIndex((s,k)=>k>i&&s.composed);return j<0?'not within 8 s':adoption[j].ms;})(),
  invalidationsDelta:(adoption.at(-1)?.invalidations??0)-(adoption[0]?.invalidations??0)};
 // Forced states: preview-only (refined disposed -> preview handoff) and with glass backdrop-filter removed.
 const grab=async tag=>{await page.waitForTimeout(600);fs.writeFileSync(path.join(out,`${engine}-dpr${dpr}-${tag}.png`),await page.locator('#w').screenshot());return f.evaluate(STATE);};
 const forced={refinedOrCurrent:await grab('current')};
 await f.addStyleTag({content:'*{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}'});forced.currentNoBackdrop=await grab('current-nobackdrop');
 await f.evaluate(()=>{document.querySelectorAll('style').forEach(s=>{if(s.textContent.startsWith('*{backdrop-filter:none'))s.remove();});window.SalahRealSky?.dispose();});
 forced.previewOnly=await grab('preview-only');
 await f.addStyleTag({content:'*{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}'});forced.previewNoBackdrop=await grab('preview-nobackdrop');
 const weatherState=await f.evaluate(()=>{try{const q=window.qaState();return {wxTruth:q.wxTruth??null,weather:q.weather??null,header:document.querySelector('.c')?.innerText.split(String.fromCharCode(10)).slice(0,3)};}catch(e){return {error:String(e.message)};}});
 const version=browser.version();await browser.close();server.close();
 const firstRefined=trace.find(s=>s.composed),badges=[...new Set(trace.map(s=>s.badge))];
 const summary={engine,version,dpr,secs,adoption:adoptionSummary,weatherState,aborted:[...new Set(aborted)],errors,firstRefinedMs:firstRefined?.ms??null,badges,
  refiningMs:trace.filter(s=>/refining/.test(s.badge||'')).map(s=>s.ms).reduce((m,x,i,arr)=>i?m:[arr[0],arr.at(-1)],null),
  maxInvalidations:Math.max(...trace.map(s=>s.invalidations??0)),forced:Object.fromEntries(Object.entries(forced).map(([k,s])=>[k,{badge:s.badge,composed:s.composed,previewReady:s.previewReady,canv:s.canv}]))};
 fs.writeFileSync(path.join(out,`${engine}-dpr${dpr}.json`),JSON.stringify({summary,trace,adoption},null,1));
 console.log(JSON.stringify(summary));
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
