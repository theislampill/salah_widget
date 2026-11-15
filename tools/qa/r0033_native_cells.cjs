'use strict';
// R0033 native cells (issue 100: R33-01/02/04/11/12/13/14/15/17, gate D Moon opacity, transition frame sequences).
// Global Playwright; forced zone Asia/Riyadh; Playwright clock installed at a fixed instant; frozen simTime scenes;
// prayer fulfilled from a fixture, weather answered in-page from a fixture, every other non-loopback request aborted.
// The loopback server can WITHHOLD the Moon terrain/colour assets: 404 no-store, 404 heuristically cacheable (no
// Cache-Control) or a stalled response (healthy initial tier with refinement pending). No provider is contacted.
// One JSON line per cell on stdout; PNG artefacts under --out.
//   --cell scenes        healthy initial-tier Moon scenes (crescent/half/gibbous/full/new), card PNG + Moon crop + facts
//   --cell construction  injected construction failure (the Moon's own 250 ms interval throws once) + startup frames
//   --cell recover1      assets 404 (no-store), restore, one automatic attempt recovers (no driver retry)
//   --cell recover3      assets 404 for two automatic attempts, restore, the third recovers
//   --cell exhaust       assets 404 for all three attempts: exhausted, initial disc retained
//   --cell cached404     Firefox b21 pattern: cacheable 404, restore, the recovery attempt reaches the server
//   --cell startup       healthy half-Moon startup frame sequence (commit consistency, no unlit committed frame)
// Usage: node tools/qa/r0033_native_cells.cjs --cell <c> --root <tree> --out <dir> --engine <e> [--playwright <pkg>]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root),out=path.resolve(a.out),engine=a.engine||'chromium',cell=a.cell,tag=a.tag||path.basename(root);
fs.mkdirSync(out,{recursive:true});
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.gz':'application/octet-stream','.bin':'application/octet-stream','.woff2':'font/woff2'};
const MOON_ASSETS=['/moon/assets/dem.bin.gz','/moon/assets/colour.bin.gz'];
const policy={assets:'serve'};const served=[];const held=[];
const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://x');const p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
 const asset=MOON_ASSETS.includes(u.pathname);if(asset)served.push({path:u.pathname,policy:policy.assets,at:Date.now()});
 if(asset&&policy.assets==='stall'){held.push(res);return;}
 if(asset&&policy.assets==='404'){res.writeHead(404,{'cache-control':'no-store'});return res.end();}
 if(asset&&policy.assets==='404-cacheable'){res.writeHead(404,{'content-type':'text/plain','last-modified':'Mon, 01 Jan 2024 00:00:00 GMT'});return res.end('withheld');}
 if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':asset?'max-age=3600':'no-store'});fs.createReadStream(p).pipe(res);});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const prayer=day=>{const [d,m,y]=day.split('-').map(Number);return {timings:{Fajr:'04:47',Sunrise:'06:05',Dhuhr:'12:19',Asr:'15:48',Maghrib:'18:33',Sunset:'18:33',Isha:'20:03'},
 meta:{timezone:'Asia/Riyadh',method:{id:4,params:{Fajr:18.5,Isha:'90 min'}}},date:{gregorian:{date:day,day:String(d).padStart(2,'0'),month:{number:m,en:'September'},year:String(y)},hijri:{day:'26',month:{number:3,en:'Rabi'},year:'1448'}}};};
const SHIM=`(()=>{const nf=window.fetch.bind(window),iso=ms=>new Date(ms+3*3600000).toISOString().slice(0,16);
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){const w=Date.now(),m=Math.floor(w/60000)*60000,h0=Math.floor(w/3600000)*3600000-7200000,N=72,t=[],arr=f=>Array.from({length:N},f);
   for(let i=0;i<N;i++)t.push(iso(h0+i*3600000));
   return json({timezone:'Asia/Riyadh',utc_offset_seconds:10800,elevation:600,current:{time:iso(m),interval:900,weather_code:0,temperature_2m:24,apparent_temperature:24,relative_humidity_2m:40,dew_point_2m:10,wind_speed_10m:3,wind_direction_10m:90,wind_gusts_10m:5,cloud_cover:0,cloud_cover_low:0,cloud_cover_mid:0,cloud_cover_high:0,precipitation:0,rain:0,showers:0,snowfall:0,is_day:0,visibility:24000},
    hourly:{time:t,temperature_2m:arr(()=>24),weather_code:arr(()=>0),precipitation:arr(()=>0),cloud_cover:arr(()=>0),relative_humidity_2m:arr(()=>40),wind_speed_10m:arr(()=>3),visibility:arr(()=>24000),is_day:arr(()=>0)}});}
  if(u.includes('api.rainviewer.com'))return Promise.reject(new TypeError('controlled radar unavailable'));
  return nf(input,init);};})();`;
// The Moon wrapper's own 250 ms poll interval throws once (a real construction-stage failure, injected).
const CONSTRUCTION=`(()=>{const si=window.setInterval;let armed=true;window.setInterval=function(f,ms,...r){if(armed&&ms===250&&document.currentScript?.id==='moon-initial-code'){armed=false;throw new Error('r0033-injected Moon construction failure');}return si.call(this,f,ms,...r);};})();`;
const BASE='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&seed=1&simTime=22:00&simWx=0';
const PHASES={crescent:'&simMoon=0.08&simWax=1&simMoonAlt=20&simMoonH=42',half:'&simMoon=0.5&simWax=1&simMoonAlt=20&simMoonH=42',gibbous:'&simMoon=0.92&simWax=1&simMoonAlt=20&simMoonH=42',
 full:'&simMoon=0.98&simWax=1&simMoonAlt=20&simMoonH=42',new:'&simMoon=0.01&simWax=1&simMoonAlt=20&simMoonH=42'};
const FACTS=`(()=>{const m=window.SalahMoonRuntime,s=m?.state,c=document.querySelector('.c'),cs=getComputedStyle(c),q=window.qaState?.(),t=q?.moonTruth,ph=document.querySelector('.mphoto')?.getBoundingClientRect();
 return {registered:!!m,constructionError:window.SalahMoonConstructionError??null,status:s?.status??null,visibleSource:s?.visibleSource??null,current:s?.current??null,workerAlive:s?.workerAlive??null,
  recovery:s?.recovery??null,retryCount:s?.retryCount??null,presentable:m?.presentable??null,errors:(s?.errors??[]).slice(-3),moonReady:c.classList.contains('moon-ready'),
  maskOn:!!document.querySelector('.moon-mask-disc')?.classList.contains('mask-on'),skyPending:c.classList.contains('sky-pending'),
  moonocc:cs.getPropertyValue('--moonocc').trim(),moongrp:cs.getPropertyValue('--moongrp').trim(),moonbeam:cs.getPropertyValue('--moonbeam').trim(),
  moonTruth:t?{displayMode:t.displayMode,moonlightOpacity:t.moonlightOpacity,reason:t.reason,light:t.lunarLight?{eligible:t.lunarLight.eligible,reason:t.lunarLight.reason,beam:t.lunarLight.beam,cloudLight:t.lunarLight.cloudLight,localStarWash:t.lunarLight.localStarWash}:null}:null,
  disc:ph?{x:ph.x,y:ph.y,w:ph.width,h:ph.height}:null,composed:c.classList.contains('real-sky-composed')};})()`;
async function open(browser,base,hash,{construction=false}={}){
 const ctx=await browser.newContext({viewport:{width:325,height:530},deviceScaleFactor:1,timezoneId:'Asia/Riyadh',locale:'en-US',reducedMotion:'reduce'});
 const aborted=[];await ctx.route('**/*',route=>{const u=route.request().url();if(u.startsWith(base)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
  const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
  if(m)return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:prayer(m[1])})});aborted.push(new URL(u).host);return route.abort();});
 await ctx.addInitScript(SHIM);
 const page=await ctx.newPage();await page.clock.install({time:Date.parse('2026-09-08T19:00:00Z')});await page.clock.resume();
 // After the clock: its own init script replaces setInterval, so the fault wrapper must wrap the clock's version.
 if(construction)await page.addInitScript(CONSTRUCTION);
 const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,160)));
 await page.goto(base+'/index.html'+hash);return {ctx,page,aborted,errors};}
const facts=page=>page.evaluate(FACTS);
async function until(page,pred,ms,step=250){const t0=Date.now();let f;while(Date.now()-t0<ms){f=await facts(page);if(pred(f))return {ok:true,f,ms:Date.now()-t0};await page.waitForTimeout(step);}return {ok:false,f,ms:Date.now()-t0};}
async function shot(page,name,disc){const png=await page.screenshot();fs.writeFileSync(path.join(out,`${tag}-${engine}-${name}.png`),png);
 let crop=null;if(disc){const pad=14,clip={x:Math.max(0,disc.x-pad),y:Math.max(0,disc.y-pad),width:Math.min(325,disc.w+2*pad),height:Math.min(200,disc.h+2*pad)};crop=await page.screenshot({clip});fs.writeFileSync(path.join(out,`${tag}-${engine}-${name}-moon.png`),crop);}
 return {sha256:sha(png),moonSha256:crop?sha(crop):null};}
// Frame sequence: N screenshots at a fixed cadence, plus per-frame facts; saved as numbered PNGs.
async function frames(page,name,n,step){const seq=[];for(let i=0;i<n;i++){const t=Date.now();const png=await page.screenshot();fs.writeFileSync(path.join(out,`${tag}-${engine}-${name}-f${String(i).padStart(2,'0')}.png`),png);
 const f=await facts(page);seq.push({i,sha256:sha(png).slice(0,12),moonReady:f.moonReady,skyPending:f.skyPending,moonbeam:f.moonbeam,eligible:f.moonTruth?.light?.eligible??null,visibleSource:f.visibleSource});
 const wait=step-(Date.now()-t);if(wait>0)await page.waitForTimeout(wait);}return seq;}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const browser=await PW[engine].launch({headless:true});const emit=o=>console.log(JSON.stringify({cell,engine,tree:tag,...o}));
 try{
  if(cell==='scenes'){
   policy.assets='stall';
   for(const [name,suffix] of Object.entries(PHASES)){
    const o=await open(browser,base,BASE+suffix);
    const r=await until(o.page,f=>f.moonReady&&f.current&&!f.skyPending&&f.composed,60000);await o.page.waitForTimeout(3000);
    const f=await facts(o.page);emit({scene:name,settled:r.ok,settleMs:r.ms,facts:f,shot:await shot(o.page,'scene-'+name,f.disc),errors:o.errors,aborted:[...new Set(o.aborted)]});await o.ctx.close();
   }
  }else if(cell==='construction'||cell==='startup'){
   policy.assets='stall';const o=await open(browser,base,BASE+PHASES.half,{construction:cell==='construction'});
   const seq=await frames(o.page,cell,24,125);await o.page.waitForTimeout(3000);const f=await facts(o.page);
   emit({facts:f,frames:seq,shot:await shot(o.page,cell+'-final',f.disc??{x:200,y:20,w:100,h:100}),errors:o.errors});await o.ctx.close();
  }else if(['recover1','recover3','exhaust','cached404'].includes(cell)){
   policy.assets=cell==='cached404'?'404-cacheable':'404';
   const failAttempts=cell==='recover1'||cell==='cached404'?0:cell==='recover3'?2:3,backoff=[30000,120000,600000];
   const o=await open(browser,base,BASE+PHASES.half);const log=[];
   const first=await until(o.page,f=>f.status==='unavailable'&&f.recovery?.state==='scheduled',90000);log.push({phase:'first-failure',ok:first.ok,recovery:first.f?.recovery,current:first.f?.current,visibleSource:first.f?.visibleSource,light:first.f?.moonTruth?.light});
   const failure=await shot(o.page,cell+'-after-failure',first.f?.disc);
   for(let i=0;i<failAttempts;i++){const n=served.length;await o.page.clock.fastForward(backoff[i]+1000);
    const r=await until(o.page,f=>f.recovery&&f.recovery.attempts===i+1&&!f.workerAlive&&f.status==='unavailable',90000);log.push({phase:'attempt-'+(i+1)+'-failed',ok:r.ok,recovery:r.f?.recovery,serverAssetRequests:served.length-n,visibleSource:r.f?.visibleSource,current:r.f?.current});}
   let recovered=null,seq=null;
   if(cell==='exhaust'){await o.page.clock.fastForward(2*3600*1000);await o.page.waitForTimeout(2000);const f=await facts(o.page);log.push({phase:'two-hours-later',recovery:f.recovery,workerAlive:f.workerAlive,visibleSource:f.visibleSource,current:f.current,light:f.moonTruth?.light});}
   else{policy.assets='serve';const n=served.length;await o.page.clock.fastForward(backoff[failAttempts]+1000);
    const live=await until(o.page,f=>f.workerAlive&&f.status!=='unavailable',60000);
    seq=await frames(o.page,cell+'-recovering',8,500);
    const done=await until(o.page,f=>f.visibleSource==='refined-terrain'||f.visibleSource==='terrain-preview',300000,1000);
    recovered={workerStarted:live.ok,serverAssetRequests:served.length-n,refined:done.ok,refinedMs:done.ms,recovery:done.f?.recovery,status:done.f?.status,visibleSource:done.f?.visibleSource,retryCount:done.f?.retryCount};}
   const f=await facts(o.page);emit({log,recovered,final:f,failureShot:failure,finalShot:await shot(o.page,cell+'-final',f.disc),frames:seq,servedAssetRequests:served.length,errors:o.errors});await o.ctx.close();
  }else throw Error('unknown cell '+cell);
 }catch(e){emit({error:String(e.stack||e).slice(0,600)});process.exitCode=1;}
 finally{for(const r of held)try{r.destroy();}catch{}await browser.close();server.close();}
})();
