'use strict';
// R0034 native cells (issue 101 ES34-13, ES34-16, ES34-17). Global Playwright, forced zone America/New_York,
// Playwright clock installed at a fixed instant (then resumed: real-time flow), prayer fulfilled from
// tests/r0002-ordinary.json, weather answered in-page from fixtures, every other non-loopback request aborted.
// No provider is contacted. One JSON line per cell on stdout; artefacts under --out.
//   --mode lanes      ES34-17 preview lanes: timeScale 2/10/60 with a forecast track whose CONSUMED inputs are constant
//                     (rh/wind interpolate, vis >= 20000), timeScale 60 with visibility varying below 20000, and a
//                     SalahClock.set({rate:10}) control preview. Records first refined composition and badge timeline.
//   --mode neutral    ES34-16 frozen-clock scenes (simTime, sim weather/Moon): card screenshot once the refined frame
//                     is composed; compare trees byte for byte (and a repeat of the same tree as the noise floor).
//   --mode measure    ES34-13 PRA-F-34 measurement, 60 s real time per scene: putImageData / toDataURL counts and
//                     durations, refined lastComposeMs samples, long tasks (where supported), timer lateness.
// Usage: node tools/qa/r0034_native_cells.cjs --mode <m> --root <tree> --out <dir> --engine <e> [--seconds N]
//        [--playwright <pkg>]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root),out=path.resolve(a.out),engine=a.engine||'chromium',mode=a.mode;
fs.mkdirSync(out,{recursive:true});
const ordinary=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json'),'utf8'));
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
function record(day){const r=JSON.parse(JSON.stringify(ordinary)),[d,mo,y]=day.split('-').map(Number);r.meta.timezone='America/New_York';
 r.date.gregorian={...r.date.gregorian,date:day,day:String(d).padStart(2,'0'),month:{number:mo,en:MONTHS[mo-1]},year:String(y)};return r;}
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream','.woff2':'font/woff2'};
const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://x');const p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
 if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
// Weather fixture: current record + a 72-point hourly track starting 2 h before the instant. `wx` is a JSON spec.
function shim(wx){return `(()=>{const nf=window.fetch.bind(window),iso=ms=>new Date(ms-new Date(ms).getTimezoneOffset()*60000).toISOString().slice(0,16),W=${JSON.stringify(wx)};
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){const w=Date.now(),m=Math.floor(w/60000)*60000,h0=Math.floor(w/3600000)*3600000-7200000,N=72,t=[],arr=f=>Array.from({length:N},(_,i)=>f(i));
   for(let i=0;i<N;i++)t.push(iso(h0+i*3600000));
   return json({timezone:'America/New_York',utc_offset_seconds:-new Date(w).getTimezoneOffset()*60,elevation:30,
    current:{time:iso(m),interval:900,weather_code:W.code,temperature_2m:70,apparent_temperature:70,relative_humidity_2m:55,dew_point_2m:53,wind_speed_10m:5,wind_direction_10m:90,wind_gusts_10m:8,cloud_cover:W.cloud,precipitation:0,is_day:W.isDay,visibility:24000},
    hourly:{time:t,temperature_2m:arr(()=>70),weather_code:arr(()=>W.code),precipitation:arr(()=>0),cloud_cover:arr(()=>W.cloud),relative_humidity_2m:arr(i=>i%2?80:40),
     wind_speed_10m:arr(i=>i%2?9:3),visibility:arr(i=>W.visVary?(i%2?16000:8000):(i%2?30000:24000)),is_day:arr(()=>W.isDay)}});}
  if(u.includes('api.rainviewer.com'))return Promise.reject(new TypeError('controlled radar unavailable'));
  return nf(input,init);};})();`;}
const INSTRUMENT=`(()=>{const M=window.__m={put:[],url:[],long:[],late:[],compose:[]};const P=CanvasRenderingContext2D.prototype,pi=P.putImageData;
 P.putImageData=function(...x){const t=performance.now();try{return pi.apply(this,x);}finally{M.put.push(performance.now()-t);}};
 const C=HTMLCanvasElement.prototype,tu=C.toDataURL;C.toDataURL=function(...x){const t=performance.now();try{return tu.apply(this,x);}finally{M.url.push(performance.now()-t);}};
 try{new PerformanceObserver(l=>{for(const e of l.getEntries())M.long.push(e.duration);}).observe({type:'longtask',buffered:true});M.longSupported=true;}catch{M.longSupported=false;}
 let last=performance.now();setInterval(()=>{const n=performance.now();M.late.push(n-last-20);last=n;},20);})();`;
const STATE=`(()=>{const s=window.SalahRealSky?.state,c=document.querySelector('.c');return {badge:document.querySelector('.real-sky-status')?.textContent??null,
 composed:!!c?.classList.contains('real-sky-composed'),availability:s?.availability?.reason??null,status:s?.status??null,accepted:s?.lifecycle?.accepted??null,
 invalidations:s?.lifecycle?.invalidations??null,churn:s?.lifecycle?.churn??null,lastComposeMs:s?.last?.composition?.lastComposeMs??null};})()`;
const BASE='#lat=28.5383&lon=-81.3792&label=Central%20FL&method=2&tz=America%2FNew_York&seed=1';
const pct=(x,p)=>{if(!x.length)return null;const s=[...x].sort((a,b)=>a-b);return +s[Math.min(s.length-1,Math.floor(p*(s.length-1)))].toFixed(3);};
async function open(browser,base,{hash,wx,instant,reduced=false,instrument=false}){
 const ctx=await browser.newContext({viewport:{width:325,height:530},deviceScaleFactor:1,timezoneId:'America/New_York',locale:'en-US',reducedMotion:reduced?'reduce':'no-preference'});
 const aborted=[];await ctx.route('**/*',route=>{const u=route.request().url();if(u.startsWith(base)||u.startsWith('data:')||u.startsWith('blob:'))return route.continue();
  const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
  if(m)return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1])})});aborted.push(new URL(u).host);return route.abort();});
 await ctx.addInitScript(shim(wx));if(instrument)await ctx.addInitScript(INSTRUMENT);
 const page=await ctx.newPage();await page.clock.install({time:Date.parse(instant)});await page.clock.resume();
 const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,160)));
 await page.goto(base+'/index.html'+hash);return {ctx,page,aborted,errors};}
async function watch(page,ms,step=250){const t0=Date.now(),tr=[];while(Date.now()-t0<ms){try{tr.push({ms:Date.now()-t0,...await page.evaluate(STATE)});}catch(e){tr.push({ms:Date.now()-t0,error:String(e.message).slice(0,80)});}await page.waitForTimeout(step);}return tr;}
function longest(tr,re){let best=0,start=null;for(const s of tr){if(re.test(s.badge||'')){start??=s.ms;best=Math.max(best,s.ms-start);}else start=null;}return best;}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const browser=await PW[engine].launch({headless:true});const results=[];
 try{
 const clear={code:0,cloud:0,isDay:1,visVary:false};
 if(mode==='lanes'){
  const secs=+(a.seconds||45)*1000;
  const cells=[['ts2',BASE+'&timeScale=2',clear],['ts10',BASE+'&timeScale=10',clear],['ts60',BASE+'&timeScale=60',clear],['ts60-vis',BASE+'&timeScale=60',{...clear,visVary:true}],['clock10',BASE,clear]];
  for(const [name,hash,wx] of cells){
   const o=await open(browser,base,{hash,wx,instant:'2026-11-13T17:00:00Z'});
   if(name==='clock10'){await o.page.waitForTimeout(2500);await o.page.evaluate(()=>window.SalahClock.set({rate:10}));}
   const tr=await watch(o.page,secs);
   results.push({cell:name,engine,hash,firstComposedMs:tr.find(s=>s.composed)?.ms??null,composedSamples:tr.filter(s=>s.composed).length,samples:tr.length,
    badges:[...new Set(tr.map(s=>s.badge))],availabilityReasons:[...new Set(tr.map(s=>s.availability))],longestRefiningMs:longest(tr,/refining/),
    accepted:tr.at(-1)?.accepted??null,invalidations:tr.at(-1)?.invalidations??null,churn:tr.at(-1)?.churn??null,errors:o.errors,aborted:[...new Set(o.aborted)]});
   console.log(JSON.stringify(results.at(-1)));await o.ctx.close();
  }
 }else if(mode==='neutral'){
  const scenes=[['clear-day','&simTime=12:30&simWx=0'],['broken','&simTime=12:30&simWx=2&simCloud=50'],['overcast','&simTime=12:30&simWx=3&simCloud=100'],
   ['clear-night','&simTime=22:00&simWx=0'],['crescent','&simTime=19:30&simWx=0&simMoon=0.08&simWax=1&simMoonAlt=20&simMoonH=42']];
  for(const [name,suffix] of scenes){
   const o=await open(browser,base,{hash:BASE+suffix,wx:clear,instant:'2026-11-13T17:00:00Z',reduced:true});
   let tr=[];const t0=Date.now();while(Date.now()-t0<30000){const s=await o.page.evaluate(STATE);tr.push(s);if(s.composed&&s.status==='ready')break;await o.page.waitForTimeout(250);}
   await o.page.waitForTimeout(2500);const png=await o.page.screenshot();fs.writeFileSync(path.join(out,`${engine}-${name}.png`),png);
   const sky=await o.page.evaluate(()=>{const k=document.querySelector('.real-sky-canvas');return k?k.toDataURL('image/png'):null;});
   const skyBytes=sky?Buffer.from(sky.split(',')[1],'base64'):null;if(skyBytes)fs.writeFileSync(path.join(out,`${engine}-${name}-sky.png`),skyBytes);
   results.push({scene:name,engine,composed:!!tr.at(-1)?.composed,screenshotSha256:sha(png),refinedCanvasSha256:skyBytes?sha(skyBytes):null,errors:o.errors});
   console.log(JSON.stringify(results.at(-1)));await o.ctx.close();
  }
 }else if(mode==='measure'){
  const secs=+(a.seconds||60)*1000;
  const scenes=[['clear-day','2026-11-13T17:00:00Z',clear,false],['broken','2026-11-13T17:00:00Z',{...clear,code:2,cloud:50},false],['overcast','2026-11-13T17:00:00Z',{...clear,code:3,cloud:100},false],
   ['clear-night','2026-11-14T03:00:00Z',{...clear,isDay:0},false],['clear-day-reduced','2026-11-13T17:00:00Z',clear,true]];
  for(const [name,instant,wx,reduced] of scenes){
   const o=await open(browser,base,{hash:BASE+(reduced?'':'&motion=full'),wx,instant,reduced,instrument:true});
   await o.page.waitForTimeout(5000);await o.page.evaluate(()=>{const M=window.__m;M.put.length=M.url.length=M.long.length=M.late.length=0;});
   const tr=await watch(o.page,secs,250);const m=await o.page.evaluate(()=>window.__m);const compose=[...new Set(tr.map(s=>s.lastComposeMs).filter(x=>x!=null))];
   results.push({scene:name,engine,seconds:secs/1000,refinedComposedFraction:+(tr.filter(s=>s.composed).length/tr.length).toFixed(3),
    putImageData:{count:m.put.length,p50:pct(m.put,.5),p95:pct(m.put,.95),max:pct(m.put,1)},toDataURL:{perMinute:+(m.url.length*60000/secs).toFixed(1),p50:pct(m.url,.5),p95:pct(m.url,.95),max:pct(m.url,1)},
    refinedLastComposeMs:{distinctSamples:compose.length,p50:pct(compose,.5),p95:pct(compose,.95),max:pct(compose,1)},
    longTasks:m.longSupported?{count:m.long.length,totalMs:+m.long.reduce((x,y)=>x+y,0).toFixed(1),max:pct(m.long,1),busyFraction:+(m.long.reduce((x,y)=>x+y,0)/secs).toFixed(4)}:'unsupported in this engine',
    timerLatenessMs:{p50:pct(m.late,.5),p95:pct(m.late,.95),max:pct(m.late,1),over50:m.late.filter(x=>x>50).length},errors:o.errors});
   console.log(JSON.stringify(results.at(-1)));await o.ctx.close();
  }
 }
 fs.writeFileSync(path.join(out,`${mode}-${engine}.json`),JSON.stringify({mode,engine,version:browser.version(),root:path.basename(root),results},null,1));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
