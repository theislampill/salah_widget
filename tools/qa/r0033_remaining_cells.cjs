'use strict';
// R0033 remaining acceptance rows (issue 100): native recipes for R33-05, R33-08, R33-09, R33-19 and R33-22.
// Every browser starts through tools/qa/r0033_isolation.cjs (refusing proxy, catch-all route and WebSocket route
// before any page, every request logged, exit 3 on any escape). Synthetic fixture only: lat 24.47, lon 39.61,
// Madinah, zone Asia/Riyadh; prayer fulfilled from a fixture, weather answered in-page from a fixture, radar
// rejected in-page; no geolocation permission is granted and no provider is contacted. The only pages opened are the
// served tree's index.html (HTTP or file entry) and tests/smoke.html.
// Moon facts are read through SalahMoonRuntime.observe() only (non-adopting, R0036), never .state/.surface().
//   --cell secondload  R33-05  healthy boot asset requests (<= 2) and a second same-session load (reload, new page)
//   --cell fileentry   R33-08  file entry: one withheld chunk script fails the boot (class transport); the automatic
//                              attempt appends every chunk script exactly once and the terrain returns
//   --cell smoke       R33-22  unchanged tests/smoke.html; reports cases 21 and 22 (R0017 CASE-21/22) and the total
//   --cell m5          R33-19  M5 (a)-(d): re-request interval, worker busy fraction, time to refined surface, WASM
//                              memory, 4 Hz poll calls and layout reads per minute, one hide/show; --minutes (30), --dpr
//   --cell throttle    R33-09  M5 (e), Chromium only: refinement duration unthrottled and under CDP CPU throttling
//                              --rate (4|6), --samples (3), --dpr; reports whether the throttle reached the workers
// Limits recorded with each result: under a Playwright route Chromium disables its HTTP cache, so a Chromium second
// load cannot show cache reuse (Firefox can); CPU time is Chromium-only (CDP SystemInfo); WASM memory is the summed
// shard figure the worker reports (no per-shard split); visibility is synthesised (document.hidden + event).
// Usage: node tools/qa/r0033_remaining_cells.cjs --cell <c> --root <tree> --out <dir> --engine <chromium|firefox|webkit>
//        [--dpr 1|2|3] [--minutes 30] [--rate 4] [--samples 3] [--playwright <pkg>]
// Output: one JSON line per cell on stdout (with the isolation verdict) and <out>/<cell>-<engine>[-dprN]-requests.json.
// Exit: 0 complete, 1 error, 2 INCOMPLETE (a measurement could not be made), 3 isolation escape.
require('./v1_net_guard.cjs').install();                                  // before any other module can connect
const iso=require('./r0033_isolation.cjs');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),{pathToFileURL}=require('node:url');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),root=path.resolve(a.root),out=path.resolve(a.out),engine=a.engine||'chromium',cell=a.cell;
const dpr=Number(a.dpr||1),minutes=Number(a.minutes||30),rate=Number(a.rate||4),samples=Number(a.samples||3);
fs.mkdirSync(out,{recursive:true});
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.gz':'application/octet-stream','.bin':'application/octet-stream','.woff2':'font/woff2'};
const MOON_ASSETS=['/moon/assets/dem.bin.gz','/moon/assets/colour.bin.gz'];
const served=[];
const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://x');const p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
 const asset=MOON_ASSETS.includes(u.pathname);if(asset)served.push({path:u.pathname,at:Date.now(),cacheControl:req.headers['cache-control']??null,conditional:!!(req.headers['if-modified-since']||req.headers['if-none-match'])});
 if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':asset?'max-age=3600':'no-store'});fs.createReadStream(p).pipe(res);});
const prayer=day=>{const [d,m,y]=day.split('-').map(Number);return {timings:{Fajr:'04:47',Sunrise:'06:05',Dhuhr:'12:19',Asr:'15:48',Maghrib:'18:33',Sunset:'18:33',Isha:'20:03'},
 meta:{timezone:'Asia/Riyadh',method:{id:4,params:{Fajr:18.5,Isha:'90 min'}}},date:{gregorian:{date:day,day:String(d).padStart(2,'0'),month:{number:m,en:'September'},year:String(y)},hijri:{day:'26',month:{number:3,en:'Rabi'},year:'1448'}}};};
const fixture=u=>{const m=u.hostname==='api.aladhan.com'&&/\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u.pathname);return m?{code:200,status:'OK',data:prayer(m[1])}:null;};
// In-page weather fixture (clear night) and radar refusal: neither request leaves the page.
const SHIM=`(()=>{const nf=window.fetch.bind(window),iso=ms=>new Date(ms+3*3600000).toISOString().slice(0,16);
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){const w=Date.now(),m=Math.floor(w/60000)*60000,h0=Math.floor(w/3600000)*3600000-7200000,N=72,t=[],arr=f=>Array.from({length:N},f);
   for(let i=0;i<N;i++)t.push(iso(h0+i*3600000));
   return json({timezone:'Asia/Riyadh',utc_offset_seconds:10800,elevation:600,current:{time:iso(m),interval:900,weather_code:0,temperature_2m:24,apparent_temperature:24,relative_humidity_2m:40,dew_point_2m:10,wind_speed_10m:3,wind_direction_10m:90,wind_gusts_10m:5,cloud_cover:0,cloud_cover_low:0,cloud_cover_mid:0,cloud_cover_high:0,precipitation:0,rain:0,showers:0,snowfall:0,is_day:0,visibility:24000},
    hourly:{time:t,temperature_2m:arr(()=>24),weather_code:arr(()=>0),precipitation:arr(()=>0),cloud_cover:arr(()=>0),relative_humidity_2m:arr(()=>40),wind_speed_10m:arr(()=>3),visibility:arr(()=>24000),is_day:arr(()=>0)}});}
  if(u.includes('api.rainviewer.com'))return Promise.reject(new TypeError('controlled radar unavailable'));
  return nf(input,init);};})();`;
// Counters and a transition log, installed AFTER the Playwright clock (which replaces setInterval). The Moon's own
// 250 ms poll is the interval created by the script with id moon-initial-code; its layout read is .mphoto's
// getBoundingClientRect. The sampler reads observe() (pure) every 250 ms and records only changes; its own layout
// reads are excluded from the count (they still happen: a stated perturbation of the CPU figures).
const PROBE=`(()=>{const R=window.__r0033={pollCalls:0,layoutReads:0,log:[],chunks:[],withhold:0,self:0};
 R.observe=()=>{R.self++;try{return window.SalahMoonRuntime?.observe?.()??null;}finally{R.self--;}};   // the recipe's own reads are not counted
 const si=window.setInterval;window.setInterval=function(f,ms,...r){if(ms===250&&document.currentScript?.id==='moon-initial-code'&&typeof f==='function'){const g=f;f=function(){R.pollCalls++;return g.apply(this,arguments);};}return si.call(this,f,ms,...r);};
 const gb=Element.prototype.getBoundingClientRect;Element.prototype.getBoundingClientRect=function(){if(!R.self&&this.classList&&this.classList.contains('mphoto'))R.layoutReads++;return gb.call(this);};
 const ap=Element.prototype.append;Element.prototype.append=function(...n){for(const e of n)if(e instanceof HTMLScriptElement&&/moon\\/file-data\\//.test(e.src)){
   const attempt=R.observe()?.state?.recovery?.attempts??null;if(R.withhold>0){R.withhold--;R.chunks.push({attempt,name:e.src.split('/').pop(),withheld:true});e.src=e.src.replace(/[^/]+$/,'r0033-withheld-chunk.js');}
   else R.chunks.push({attempt,name:e.src.split('/').pop(),withheld:false});}return ap.apply(this,n);};
 let last='';si.call(window,()=>{const o=R.observe();if(!o)return;const s=o.state,k=[s.status,s.pending,s.renders,s.cancelled,s.visibleSource,o.current].join('|');
  if(k!==last){last=k;R.log.push({t:performance.now(),status:s.status,pending:s.pending,renders:s.renders,cancelled:s.cancelled,visibleSource:s.visibleSource,current:o.current});}},250);})();`;
const FACTS=`(()=>{const m=window.SalahMoonRuntime,R=window.__r0033,o=R?R.observe():m?.observe?.()??null,s=o?.state??null,c=document.querySelector('.c');
 return {registered:!!m,status:s?.status??null,visibleSource:s?.visibleSource??null,current:o?.current??null,pending:s?.pending??null,renders:s?.renders??null,cancelled:s?.cancelled??null,workerAlive:s?.workerAlive??null,
  recovery:s?.recovery??null,retryCount:s?.retryCount??null,errors:(s?.errors??[]).slice(-3),
  last:s?.last?{totalMs:s.last.totalMs??null,memoryBytes:s.last.memoryBytes??null,workers:s.last.rowScheduling?.workers??null}:null,
  phase:s?.phasePrecision?{diameterDevicePixels:s.phasePrecision.diameterDevicePixels,refreshThresholdDevicePixels:s.phasePrecision.refreshThresholdDevicePixels,signedPositionDrift:s.phasePrecision.signedPositionDrift}:null,
  moonReady:c?c.classList.contains('moon-ready'):null,dpr:window.devicePixelRatio,now:performance.now(),pollCalls:R?.pollCalls??null,layoutReads:R?.layoutReads??null};})()`;
const HASH='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&seed=1';
const FROZEN=HASH+'&simTime=22:00&simWx=0&simMoon=0.5&simWax=1&simMoonAlt=20&simMoonH=42';   // the first slice's half-Moon scene
async function open(S,url,{clock='2026-09-08T19:00:00Z',origin=null,fileRoot=null,scale=1,motion='reduce',inits=[]}={}){
 const C=await S.context({viewport:{width:325,height:530},deviceScaleFactor:scale,timezoneId:'Asia/Riyadh',locale:'en-US',reducedMotion:motion},{origin,fileRoot,fixture});
 await C.context.addInitScript(SHIM);
 const page=await C.newPage();await page.clock.install({time:Date.parse(clock)});await page.clock.resume();
 await page.addInitScript(PROBE);for(const s of inits)await page.addInitScript(s);
 const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,160)));
 await page.goto(url);return {context:C.context,page,errors};
}
const facts=page=>page.evaluate(FACTS);
async function until(page,pred,ms,step=250){const t0=Date.now();let f=null;while(Date.now()-t0<ms){f=await facts(page);if(pred(f))return {ok:true,f,ms:Date.now()-t0};await page.waitForTimeout(step);}return {ok:false,f,ms:Date.now()-t0};}
const terrain=f=>f.visibleSource==='refined-terrain'||f.visibleSource==='terrain-preview';
const refined=f=>f.visibleSource==='refined-terrain'&&f.status==='ready'&&!f.pending;
const stats=x=>{if(!x.length)return null;const s=[...x].sort((p,q)=>p-q),at=q=>s[Math.min(s.length-1,Math.ceil(q*s.length)-1)];return {n:s.length,min:s[0],median:at(.5),p95:at(.95),max:s[s.length-1],mean:s.reduce((p,q)=>p+q,0)/s.length};};
// Chromium only: summed CPU seconds of the browser's renderer processes (CDP SystemInfo). Null elsewhere.
async function rendererCpu(S){if(engine!=='chromium')return null;try{const c=await S.browser.newBrowserCDPSession(),r=await c.send('SystemInfo.getProcessInfo');await c.detach();
 return r.processInfo.filter(p=>p.type==='renderer').reduce((n,p)=>n+p.cpuTime,0);}catch(e){return null;}}
const setHidden=(page,hidden)=>page.evaluate(h=>{Object.defineProperty(document,'hidden',{value:h,configurable:true});Object.defineProperty(document,'visibilityState',{value:h?'hidden':'visible',configurable:true});document.dispatchEvent(new Event('visibilitychange'));},hidden);
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const S=await iso.launch(PW,engine);let incomplete=false;const tag=`${cell}-${engine}${a.dpr?'-dpr'+dpr:''}${cell==='throttle'?'-x'+rate:''}`;
 const emit=o=>console.log(JSON.stringify({cell,engine,version:S.browser.version(),...o,isolation:S.verdict()}));
 try{
  if(cell==='secondload'){
   const o=await open(S,base+'/index.html'+FROZEN,{origin:base});
   const first=await until(o.page,terrain,300000,500),n1=served.length;
   await o.page.reload();const second=await until(o.page,terrain,300000,500),n2=served.length;
   // The Playwright clock belongs to the context, so the second page shares the installed clock and the catch-all route.
   const p2=await o.context.newPage();await p2.goto(base+'/index.html'+FROZEN);
   const third=await until(p2,terrain,300000,500),n3=served.length;
   const row=(r,from,to)=>({terrain:r.ok,ms:r.ms,serverAssetRequests:to-from,requests:served.slice(from,to).map(x=>({path:x.path,cacheControl:x.cacheControl,conditional:x.conditional})),recovery:r.f?.recovery??null,retryCount:r.f?.retryCount??null,status:r.f?.status??null});
   incomplete=!(first.ok&&second.ok&&third.ok);
   emit({declaredPolicy:'healthy boot: cache force-cache (moon-native bootCache); a later load of the same session is another healthy boot',firstLoad:row(first,0,n1),reload:row(second,n1,n2),newPageSameContext:row(third,n2,n3),
    withinBaseline:n1<=2&&n2-n1<=2&&n3-n2<=2,limit:engine==='chromium'?'a Playwright route disables the Chromium HTTP cache: reuse cannot be shown here, only the request bound':null,errors:o.errors});
  }else if(cell==='fileentry'){
   // Armed by an init script, so the withheld chunk is the first one the first boot appends.
   const o=await open(S,pathToFileURL(path.join(root,'index.html')).href+FROZEN,{fileRoot:root,inits:['window.__r0033.withhold=1;']});
   const failed=await until(o.page,f=>f.status==='unavailable'&&f.recovery?.state==='scheduled'&&f.recovery?.lastClass==='transport',120000);
   const boot=await o.page.evaluate(()=>window.__r0033.chunks.slice());
   await o.page.clock.fastForward(31000);
   const back=await until(o.page,terrain,300000,500),chunks=await o.page.evaluate(()=>window.__r0033.chunks.slice());
   const attempt=chunks.slice(boot.length),names=attempt.map(c=>c.name),dup=names.filter((n,i)=>names.indexOf(n)!==i);
   const withheld=boot.filter(c=>c.withheld).length;incomplete=!(failed.ok&&back.ok)||withheld!==1;
   emit({entry:'file',withheldChunks:withheld,bootFailure:{ok:failed.ok,recovery:failed.f?.recovery??null,chunksAppended:boot},automaticAttempt:{terrain:back.ok,ms:back.ms,recovery:back.f?.recovery??null,retryCount:back.f?.retryCount??null,
    chunkScriptsAppended:attempt.length,distinct:new Set(names).size,duplicates:dup,eachOnce:attempt.length>0&&dup.length===0},final:back.f,errors:o.errors});
  }else if(cell==='smoke'){
   const C=await S.context({},{origin:base,fixture:null}),page=await C.newPage(),errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,160)));
   await page.goto(base+'/tests/smoke.html',{waitUntil:'domcontentloaded'});
   let r=null;try{await page.waitForFunction('!!window.__smoke',null,{timeout:300000});r=await page.evaluate('window.__smoke');}catch(e){r=null;}
   const cases=r?.required?.cases??[],pick=i=>cases[i]?{index:i+1,name:cases[i].name,expected:cases[i].expected,assertions:cases[i].assertions,state:cases[i].state,reason:cases[i].reason}:null;
   incomplete=!r||r.status!=='PASS';
   emit({instrument:'tests/smoke.html (unchanged)',status:r?.status??'TIMEOUT',pass:r?.pass??null,fail:r?.fail??null,skip:r?.skip??null,case21:pick(20),case22:pick(21),failed:r?.required?.failed??null,missing:r?.required?.missing??null,pageErrors:errors});
  }else if(cell==='m5'){
   const cpu0=await rendererCpu(S),t0=Date.now();
   const o=await open(S,base+'/index.html'+HASH,{origin:base,clock:'2026-09-26T19:00:00Z',scale:dpr,motion:'no-preference'});
   const first=await until(o.page,refined,600000,500);const cpu1=await rendererCpu(S),refinedAt=Date.now();
   const perMinute=[];let prev=await facts(o.page);const begin=Date.now();
   for(let i=0;i<minutes&&first.ok;i++){await o.page.waitForTimeout(60000);const f=await facts(o.page);perMinute.push({minute:i+1,pollCalls:f.pollCalls-prev.pollCalls,layoutReads:f.layoutReads-prev.layoutReads,status:f.status,renders:f.renders});prev=f;}
   const windowMs=Date.now()-begin,cpu2=await rendererCpu(S),end=await facts(o.page),log=await o.page.evaluate(()=>window.__r0033.log.slice());
   // Host-side request/result times from the transition log: a job is posted when status becomes 'rendering'; it ends at the next renders increment.
   const jobs=[];let open1=null,renders=null;for(const e of log){if(renders===null)renders=e.renders;if(e.status==='rendering'&&e.pending&&!open1)open1={start:e.t};if(e.renders>renders){renders=e.renders;if(open1){jobs.push({start:open1.start,end:e.t,ms:e.t-open1.start});open1=null;}}}
   const starts=jobs.map(j=>j.start),intervals=starts.slice(1).map((s,i)=>s-starts[i]),w0=first.ok?first.f.now:0,inWindow=jobs.filter(j=>j.start>=w0),busy=inWindow.reduce((n,j)=>n+j.ms,0);
   // (b) one hide/show after the window: time back to a refined surface and renderer CPU spent on it.
   let hideShow=null;if(first.ok){await setHidden(o.page,true);await o.page.waitForTimeout(2000);const hidden=await facts(o.page),c0=await rendererCpu(S),h0=Date.now();await setHidden(o.page,false);
    const again=await until(o.page,refined,600000,500),c1=await rendererCpu(S);hideShow={statusWhileHidden:hidden.status,visibleSourceWhileHidden:hidden.visibleSource,refinedAgain:again.ok,msToRefined:Date.now()-h0,rendererCpuSeconds:c0!=null&&c1!=null?c1-c0:null};}
   incomplete=!first.ok||perMinute.length<minutes||!(hideShow?.refinedAgain);
   emit({clock:'2026-09-26T19:00:00Z advancing at 1x (real Moon above the horizon)',dpr,windowMinutes:perMinute.length,windowMs,
    timeToRefined:{ok:first.ok,msFromLaunchOfPage:first.ok?refinedAt-t0:null,msAfterLoadEvent:first.ms,rendererCpuSeconds:cpu0!=null&&cpu1!=null?cpu1-cpu0:null,workerTotalMs:first.f?.last?.totalMs??null},
    reRequest:{jobsCompleted:jobs.length,jobsInWindow:inWindow.length,intervalMs:stats(intervals),jobMs:stats(jobs.map(j=>j.ms)),busyFraction:windowMs>0?busy/windowMs:null,cancelled:end.cancelled,phase:end.phase},
    memory:{summedShardWasmBytes:end.last?.memoryBytes??null,shardWorkers:end.last?.workers??null,r0017ReferenceBytes:653262848,ratioToR0017:end.last?.memoryBytes?end.last.memoryBytes/653262848:null},
    poll:{perMinute,pollCallsPerMinute:stats(perMinute.map(m=>m.pollCalls)),layoutReadsPerMinute:stats(perMinute.map(m=>m.layoutReads))},
    windowRendererCpuSeconds:cpu1!=null&&cpu2!=null?cpu2-cpu1:null,hideShow,errors:o.errors,
    limits:['CPU is renderer-process time from CDP SystemInfo (Chromium only); it includes the whole card, not only the Moon','WASM memory is the summed shard figure reported by the worker; process memory is not measured','visibility is synthesised','the recipe reads observe() at 4 Hz in the page (its layout reads are not counted but do occur)']});
  }else if(cell==='throttle'){
   if(engine!=='chromium')throw Error('throttle is a Chromium CDP cell');
   const o=await open(S,base+'/index.html'+FROZEN,{origin:base,scale:dpr,motion:'no-preference'});
   const first=await until(o.page,refined,600000,500);
   // One forced refinement through the product's own refresh() driver; host-side duration from the request to the result.
   async function sample(){const before=await facts(o.page),t=Date.now();await o.page.evaluate(()=>window.SalahMoonRuntime.refresh());
    const r=await until(o.page,f=>(f.renders>before.renders&&f.status==='ready'&&!f.pending)||f.status==='unavailable',300000,250);
    return {ms:Date.now()-t,completed:r.ok&&r.f.renders>before.renders,killed:r.f?.status==='unavailable',lastClass:r.f?.recovery?.lastClass??null,workerTotalMs:r.f?.last?.totalMs??null};}
   const baseline=[];for(let i=0;i<samples&&first.ok;i++)baseline.push(await sample());
   // CDP throttle: the page target, and every worker target reachable through non-flattened auto-attach (two levels:
   // the Moon worker and its row workers). Whether this reaches the workers is MEASURED below, not assumed.
   const client=await o.context.newCDPSession(o.page),applied={page:false,workers:0,errors:[]};let id=1;
   const wrap=(method,params)=>JSON.stringify({id:id++,method,params});
   const toWorker=(chain,method,params)=>{let message=wrap(method,params);for(let i=chain.length-1;i>0;i--)message=wrap('Target.sendMessageToTarget',{sessionId:chain[i],message});return client.send('Target.sendMessageToTarget',{sessionId:chain[0],message});};
   const attach=chain=>{applied.workers++;toWorker(chain,'Emulation.setCPUThrottlingRate',{rate}).catch(e=>applied.errors.push(String(e.message).slice(0,120)));
    toWorker(chain,'Target.setAutoAttach',{autoAttach:true,waitForDebuggerOnStart:false,flatten:false}).catch(e=>applied.errors.push(String(e.message).slice(0,120)));};
   client.on('Target.attachedToTarget',e=>{if(/worker/.test(e.targetInfo.type))attach([e.sessionId]);});
   client.on('Target.receivedMessageFromTarget',e=>{try{const m=JSON.parse(e.message);if(m.error)applied.errors.push(String(m.error.message).slice(0,120));if(m.method==='Target.attachedToTarget'&&/worker/.test(m.params.targetInfo.type))attach([e.sessionId,m.params.sessionId]);}catch{}});
   await client.send('Emulation.setCPUThrottlingRate',{rate});applied.page=true;
   await client.send('Target.setAutoAttach',{autoAttach:true,waitForDebuggerOnStart:false,flatten:false});
   const throttled=[];for(let i=0;i<samples&&first.ok;i++){const s=await sample();throttled.push(s);if(s.killed)break;}
   await client.send('Emulation.setCPUThrottlingRate',{rate:1}).catch(()=>{});
   const b=stats(baseline.filter(s=>s.completed).map(s=>s.ms)),t=stats(throttled.filter(s=>s.completed).map(s=>s.ms)),slowdown=b&&t?t.median/b.median:null,killed=throttled.some(s=>s.killed);
   // The discriminator is only meaningful if the refinement itself slowed down: otherwise the throttle did not reach the workers.
   const reached=killed||(slowdown!=null&&slowdown>=1+0.5*(rate-1));incomplete=!first.ok||!b||(!t&&!killed)||!reached;
   emit({dpr,rate,samples,deadlineMs:240000,thresholdMs:240000/1.2,baseline:{samples:baseline,ms:b},throttled:{samples:throttled,ms:t,killedByDeadline:killed},
    effectiveSlowdown:slowdown,throttleReachedRefinement:reached,p95ExceedsThreshold:killed||(t?t.p95>240000/1.2:null),cdp:applied,errors:o.errors,
    limits:['p95 over '+samples+' samples is the maximum','durations are host-side wall time from refresh() to the adopted result','when throttleReachedRefinement is false the row is not answered by this run']});
  }else throw Error('unknown cell '+cell);
 }catch(e){emit({error:String(e.stack||e).slice(0,600)});process.exitCode=1;}
 finally{fs.writeFileSync(path.join(out,tag+'-requests.json'),JSON.stringify({cell,engine,verdict:S.verdict(),served,requests:S.ledger.requests},null,1));await S.close();server.close();}
 const verdict=S.verdict();if(!verdict.ok){console.error('ISOLATION ESCAPE '+JSON.stringify(verdict.escapes));process.exitCode=3;}else if(!process.exitCode&&incomplete)process.exitCode=2;
})();
