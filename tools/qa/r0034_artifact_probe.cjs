'use strict';
// R0034 owner-artifact localisation probe (2026-11-14 recurrence). Investigation instrument only: changes no product file.
// Scene: Central Florida (lat 28.54, lon -81.38), America/New_York, live real-time path (no simTime), Playwright clock
// installed at 2026-11-14 10:26 local and RUNNING. Every non-loopback request is aborted; the weather record is a fixture
// answered in-page (open-meteo shim, optionally delayed), prayer times are a fixture via route, radar is rejected.
// For each run in --plan (JSON array) it captures the card composite and, optionally, a 500 ms time series from load and
// a single-layer isolation pass (one element hidden at a time with test-only CSS) at a frozen instant.
// Usage: node tools/qa/r0034_artifact_probe.cjs --root <tree> --out <dir> --engine firefox|chromium --headed 1|0 --plan <plan.json>
//   optional: --fixed 1 (hold Date.now at --utc), --extra '&debugOptic=halo' (fragment suffix), --utc <ISO> --lat --lon --tz --label (scene override; the prayer fixture keeps the owner's displayed times)
//   plan item: {name, dpr:1, embed:'iframe'|'direct', wx:{code,cloud,low,mid,high,hum,wind,wdir,vis,temp}, wxDelay:ms,
//               settle:ms, series:ms, isolate:bool, freeze:bool, evalFile:<js expression file evaluated in the widget frame; {pngs:{k:dataURL}} saved>}
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root),out=path.resolve(a.out),engine=a.engine||'firefox',headed=a.headed==='1';
const plan=JSON.parse(fs.readFileSync(a.plan,'utf8'));fs.mkdirSync(out,{recursive:true});
const T0=Date.parse(a.utc||'2026-11-14T15:26:00Z');   // default 10:26 America/New_York (EST, UTC-5); --utc overrides
const ordinary=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json'),'utf8'));
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
function record(day){const r=JSON.parse(JSON.stringify(ordinary)),[d,mo,y]=day.split('-').map(Number);r.meta.timezone='America/New_York';
 // the owner's displayed times for 2026-11-14
 Object.assign(r.timings,{Fajr:'05:44',Sunrise:'06:52',Dhuhr:'12:14',Asr:'15:15',Sunset:'17:36',Maghrib:'17:36',Isha:'18:43'});
 r.date.gregorian={...r.date.gregorian,date:day,day:String(d).padStart(2,'0'),month:{number:mo,en:MONTHS[mo-1]},year:String(y)};return r;}
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream','.woff2':'font/woff2'};
const FRAG=`lat=${a.lat||28.54}&lon=${a.lon||-81.38}&label=${encodeURIComponent(a.label||'Central FL')}&method=2&tz=${encodeURIComponent(a.tz||'America/New_York')}&qa=1${a.extra||''}`;
// A photographic-looking wallpaper (layered gradients + fine texture); the card's outside is not measured.
const HOST=dpr=>`<!doctype html><meta charset=utf-8><style>html,body{margin:0;height:100%}body{background:
 repeating-linear-gradient(83deg,rgba(60,40,20,.35) 0 2px,rgba(150,110,70,.2) 2px 5px,rgba(40,30,20,.3) 5px 7px),
 radial-gradient(ellipse at 20% 80%,#8a5a2a 0,#5c3d22 30%,transparent 60%),linear-gradient(180deg,#7fa8c8 0,#a9c4d6 35%,#6b5233 60%,#3e2b19 100%)}
 iframe{position:absolute;left:30px;top:20px;width:325px;height:530px;border:0;background:transparent}</style>
 <iframe id=w allowtransparency=true src="/index.html#${FRAG}"></iframe>`;
const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://x');if(u.pathname==='/__host.html'){res.writeHead(200,{'content-type':'text/html'});return res.end(HOST());}
 const p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
 if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);});
const SHIM=(wx,delay)=>`(()=>{const nf=window.fetch.bind(window),iso=ms=>new Date(ms-new Date(ms).getTimezoneOffset()*60000).toISOString().slice(0,16);
 window.__calls={weather:0,radar:0,weatherAnsweredAt:null};const W=${JSON.stringify(wx)};
 const json=v=>new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}});
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){window.__calls.weather++;const w=Date.now(),m=Math.floor(w/900000)*900000,h=Math.floor(w/3600000)*3600000;
   const cur={time:iso(m),interval:900,weather_code:W.code,temperature_2m:W.temp??51,apparent_temperature:(W.temp??51)-2,relative_humidity_2m:W.hum,dew_point_2m:40,
    wind_speed_10m:W.wind,wind_direction_10m:W.wdir,wind_gusts_10m:W.wind*1.5,cloud_cover:W.cloud,cloud_cover_low:W.low,cloud_cover_mid:W.mid,cloud_cover_high:W.high,
    precipitation:0,rain:0,showers:0,snowfall:0,is_day:1,visibility:W.vis};
   const hrs=[0,1,2,3].map(k=>h+k*3600000),col=(x)=>hrs.map(()=>x);
   const body={latitude:28.54,longitude:-81.38,timezone:'America/New_York',utc_offset_seconds:-new Date(w).getTimezoneOffset()*60,elevation:30,current:cur,
    hourly:{time:hrs.map(iso),temperature_2m:col(W.temp??51),apparent_temperature:col((W.temp??51)-2),relative_humidity_2m:col(W.hum),dew_point_2m:col(40),
     cloud_cover:col(W.cloud),cloud_cover_low:col(W.low),cloud_cover_mid:col(W.mid),cloud_cover_high:col(W.high),wind_speed_10m:col(W.wind),wind_direction_10m:col(W.wdir),
     wind_gusts_10m:col(W.wind*1.5),precipitation:col(0),weather_code:col(W.code),visibility:col(W.vis),is_day:col(1)}};
   return new Promise(r=>setTimeout(()=>{window.__calls.weatherAnsweredAt=performance.now();r(json(body));},${delay|0}));}
  if(u.includes('api.rainviewer.com')){window.__calls.radar++;return Promise.reject(new TypeError('controlled radar unavailable'));}
  return nf(input,init);};})();`;
const STATE=`(()=>{const c=document.querySelector('.c'),cs=c?getComputedStyle(c):null,g=k=>cs?cs.getPropertyValue(k).trim():null;
 const vars={};for(const k of ['--ray','--anticrep','--sunray','--sunamt','--sunvx','--sunvy','--sunx2','--sunlift','--sunpulse','--sundisc','--sunhalo','--sundogs','--sunpillar','--rain-op','--grain'])vars[k]=g(k);
 let qa=null;try{const q=window.qaState?.();qa=q?{wxTruth:q.wxTruth,optics:q.optics??null,clouds:q.clouds?{cover:q.clouds.cover,type:q.clouds.type}:null}:null;}catch(e){qa={error:String(e.message)}}
 const s=window.SalahRealSky?.state;
 const el=sel=>{const e=document.querySelector(sel);if(!e)return null;const st=getComputedStyle(e),r=e.getBoundingClientRect();return {vis:st.visibility,disp:st.display,op:st.opacity,rect:[r.x,r.y,r.width,r.height].map(Math.round)};};
 return {perfMs:Math.round(performance.now()),now:new Date().toISOString(),calls:window.__calls,badge:document.querySelector('.real-sky-status')?.textContent??null,
  cls:c?c.className:null,status:s?.status??null,vars,qa,godray:el('.wfx .godray'),rays:el('.atmo .suncorner .rays'),suncorner:el('.atmo .suncorner'),
  dbglayers:document.querySelector('.dbglayers')?.textContent?.slice(0,600)??null};})()`;
const GPU=`(()=>{const c=document.createElement('canvas'),g=c.getContext('webgl')||c.getContext('experimental-webgl');let r=null,v=null;
 if(g){const x=g.getExtension('WEBGL_debug_renderer_info');r=x?g.getParameter(x.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER);v=x?g.getParameter(x.UNMASKED_VENDOR_WEBGL):g.getParameter(g.VENDOR);}
 return {userAgent:navigator.userAgent,devicePixelRatio,webglRenderer:r,webglVendor:v};})()`;
// Every element inside the card except the debug readouts; hidden one at a time.
const ENUM=`(()=>{const c=document.querySelector('.c');const out=[];let i=0;
 for(const e of c.querySelectorAll('*')){i++;const st=getComputedStyle(e);if(st.display==='none'||st.visibility==='hidden')continue;
  if(e.closest('.dbglayers,.dbgmoon,.dbgmotion,.simclock,defs'))continue;const r=e.getBoundingClientRect();
  if(r.right<0||r.left>150||r.bottom<240||r.top>400)continue;   // must cover part of the bar region (card x 0-150, y 240-400)
  const id='r34-'+i;e.setAttribute('data-r34',id);
  out.push({id,tag:e.tagName.toLowerCase(),cls:(e.getAttribute('class')||'').slice(0,60),depth:(()=>{let d=0,p=e;while(p&&p!==c){d++;p=p.parentElement;}return d;})(),
   rect:[r.x,r.y,r.width,r.height].map(Math.round),op:st.opacity,blend:st.mixBlendMode,filter:st.filter.slice(0,40),bf:(st.backdropFilter||'').slice(0,40)});}
 return out;})()`;
const SKY='.real-sky-canvas,.real-sky-preview';
const TOGGLES={nobackdrop_all:'*{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}',
 nobackdrop_e_wt:'.e,.wt{backdrop-filter:none!important;-webkit-backdrop-filter:none!important}',
 nopreview:'.real-sky-preview{visibility:hidden!important}',
 onetoone:`${SKY}{inset:-1px!important;width:calc(100% + 2px)!important;height:calc(100% + 2px)!important}`,
 no_godray:'.wfx .godray{visibility:hidden!important}',no_suncorner_rays:'.atmo .suncorner .rays{visibility:hidden!important}',
 no_both_rays:'.wfx .godray,.atmo .suncorner .rays{visibility:hidden!important}'};
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const opts={headless:!headed};
 if(engine==='firefox')opts.firefoxUserPrefs={'gfx.webrender.all':true,'gfx.webrender.software':false,'layers.acceleration.force-enabled':true};
 if(engine==='chromium')opts.args=['--ignore-gpu-blocklist','--enable-gpu-rasterization'];
 const browser=await PW[engine].launch(opts);const results=[];
 try{for(const run of plan){
  const dpr=run.dpr||1,embed=run.embed||'iframe',dir=path.join(out,run.name);fs.mkdirSync(dir,{recursive:true});
  const vw=embed==='iframe'?400:325,vh=embed==='iframe'?600:530;
  const ctx=await browser.newContext({viewport:{width:vw,height:vh},deviceScaleFactor:dpr,timezoneId:a.tz||'America/New_York',locale:'en-US'});
  const aborted=[];await ctx.route('**/*',route=>{const u=route.request().url();if(u.startsWith(base)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
   const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
   if(m)return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1])})});
   aborted.push(new URL(u).host);return route.abort();});
  await ctx.addInitScript(SHIM(run.wx,run.wxDelay||0));
  const page=await ctx.newPage();
  // --fixed 1: Date.now() held at T0 while timers run (deterministic refined frame for byte comparison); default: running mocked clock
  if(a.fixed==='1')await page.clock.setFixedTime(T0);else{await page.clock.install({time:T0});await page.clock.resume();}
  const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,200)));
  const t0=Date.now();
  await page.goto(embed==='iframe'?base+'/__host.html':base+'/index.html#'+FRAG+(run.debugLayers?'&debugLayers=1':''));
  const frame=()=>embed==='iframe'?page.frames().find(f=>f.url().includes('index.html')):page.mainFrame();
  const clip=embed==='iframe'?{x:30,y:20,width:325,height:530}:{x:0,y:0,width:325,height:530};
  const shot=async file=>fs.writeFileSync(path.join(dir,file),await page.screenshot({clip}));
  const rec={name:run.name,engine,headed,dpr,embed,wx:run.wx,wxDelay:run.wxDelay||0,gpu:await page.evaluate(GPU),series:[],errors,aborted};
  if(run.series){let n=0;while(Date.now()-t0<run.series){const f=frame();let s=null;if(f){try{s=await f.evaluate(STATE);}catch(e){s={error:String(e.message).slice(0,100)}}}
    const file=`series-${String(n).padStart(3,'0')}.png`;await shot(file);rec.series.push({ms:Date.now()-t0,file,state:s});n++;await page.waitForTimeout(400);}}
  else await page.waitForTimeout(run.settle||14000);
  const f=frame();rec.final=await f.evaluate(STATE);await shot('final.png');
  // raw canvas readbacks
  for(const [sel,tag] of [['.real-sky-preview','raw-preview'],['.real-sky-canvas','raw-refined']]){
   const url=await f.evaluate(s=>{const k=document.querySelector(s);try{return k?k.toDataURL('image/png'):null;}catch(e){return null;}},sel);
   if(url)fs.writeFileSync(path.join(dir,tag+'.png'),Buffer.from(url.split(',')[1],'base64'));}
  if(run.evalFile){const ev=await f.evaluate(fs.readFileSync(path.resolve(run.evalFile),'utf8'));
   if(ev&&ev.pngs){for(const [k,u] of Object.entries(ev.pngs))fs.writeFileSync(path.join(dir,'eval-'+k+'.png'),Buffer.from(u.split(',')[1],'base64'));delete ev.pngs;}
   rec.eval=ev;}
  if(run.freeze){   // frozen-instant capture only (R0034-A1 before/after): composite + raw refined canvas at the same instant
   if(a.fixed!=='1')await page.clock.pauseAt(await page.evaluate(()=>Date.now())+500);await page.waitForTimeout(1500);rec.frozen=await f.evaluate(STATE);await shot('frozen.png');
   const u=await f.evaluate(()=>{const k=document.querySelector('.real-sky-canvas');try{return k?k.toDataURL('image/png'):null;}catch(e){return null;}});
   if(u)fs.writeFileSync(path.join(dir,'frozen-raw-refined.png'),Buffer.from(u.split(',')[1],'base64'));
   const pv=await f.evaluate(()=>{const k=document.querySelector('.real-sky-preview');try{return k?k.toDataURL('image/png'):null;}catch(e){return null;}});
   if(pv)fs.writeFileSync(path.join(dir,'frozen-raw-preview.png'),Buffer.from(pv.split(',')[1],'base64'));}
  if(run.isolate){
   await page.clock.pauseAt(await page.evaluate(()=>Date.now())+500);await page.waitForTimeout(1500);   // freeze clock-driven painting
   rec.isoState=await f.evaluate(STATE);await shot('iso-base-a.png');await page.waitForTimeout(600);await shot('iso-base-b.png');
   const iso=[];
   // Test-only A/B of the daytime solar-field lattice (see r0034_artifact_patch_lattice.js), clock frozen.
   const patchSrc=fs.readFileSync(path.join(__dirname,'r0034_artifact_patch_lattice.js'),'utf8');
   await f.evaluate(()=>{window.__r34mode='patch';});rec.patch=await f.evaluate(patchSrc);await page.waitForTimeout(700);await shot('iso-t-lattice41x67.png');
   iso.push({kind:'toggle',key:'lattice41x67',file:'iso-t-lattice41x67.png'});
   const u=await f.evaluate(()=>{const k=document.querySelector('.real-sky-canvas');return k?k.toDataURL('image/png'):null;});if(u)fs.writeFileSync(path.join(dir,'raw-refined-lattice41x67.png'),Buffer.from(u.split(',')[1],'base64'));
   await f.evaluate(()=>{window.__r34mode='restore';});rec.restore=await f.evaluate(patchSrc);await page.waitForTimeout(700);await shot('iso-base-restored.png');
   for(const [k,css] of Object.entries(TOGGLES)){const h=await f.addStyleTag({content:css});await page.waitForTimeout(700);await shot(`iso-t-${k}.png`);
    await h.evaluate(e=>e.remove());await page.waitForTimeout(300);iso.push({kind:'toggle',key:k,file:`iso-t-${k}.png`});}
   const els=await f.evaluate(ENUM);rec.elements=els;
   for(const e of els){const h=await f.addStyleTag({content:`[data-r34="${e.id}"]{visibility:hidden!important}`});await page.waitForTimeout(450);
    await shot(`iso-e-${e.id}.png`);await h.evaluate(x=>x.remove());iso.push({kind:'element',key:e.id,file:`iso-e-${e.id}.png`});}
   await shot('iso-base-c.png');rec.isoStateEnd=await f.evaluate(STATE);rec.isolation=iso;}
  results.push(rec);fs.writeFileSync(path.join(dir,'run.json'),JSON.stringify(rec,null,1));
  console.log(JSON.stringify({name:run.name,badge:rec.final.badge,vars:rec.final.vars,cls:rec.final.cls,errors:errors.length,aborted:[...new Set(aborted)]}));
  await ctx.close();}
 }finally{await browser.close().catch(()=>{});server.close();}
 fs.writeFileSync(path.join(out,`summary-${engine}${headed?'-headed':''}.json`),JSON.stringify(results.map(r=>({name:r.name,engine:r.engine,headed:r.headed,dpr:r.dpr,embed:r.embed,wx:r.wx,gpu:r.gpu,final:r.final})),null,1));
})().catch(e=>{console.error(e);process.exitCode=1;});
