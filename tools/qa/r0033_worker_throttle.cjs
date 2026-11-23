'use strict';
// R0033 row R33-09 (issue 100, M5 (e)): a CPU slowdown that demonstrably reaches the Moon refinement WORKERS, and the
// refinement duration measured under it. Additive to tools/qa/r0033_remaining_cells.cjs, whose `throttle` cell found
// that Chromium's CDP Emulation.setCPUThrottlingRate slows only the page's main thread (worker targets refuse it).
// Every browser starts through tools/qa/r0033_isolation.cjs (refusing proxy, catch-all route and WebSocket route
// before any page, every request logged, exit 3 on any escape); synthetic fixtures only, no provider is contacted.
//
// No method is trusted without a calibration: a fixed CPU-bound benchmark (an integer JS loop and a hand-assembled
// WASM loop) runs in a dedicated worker, and the JS loop also on the main thread, before and while the method is
// applied; the slowdown ratio of each is reported.
//   --mode calibrate --method <m>   calibration page only (served from loopback, no product code)
//        none         repeated baseline (stability control)
//        cdp-page     CDP Emulation.setCPUThrottlingRate on the page session (control: expected to slow the main thread only)
//        cdp-worker   the same command sent on each WORKER target's own flattened session, over a raw loopback CDP
//                     connection (Chromium started with --remote-debugging-port on 127.0.0.1)
//        jobcap       Windows Job Object, CPU rate control HARD CAP, on every renderer process of this browser
//                     (tools/qa/r0033_jobcap.ps1); --rate R caps the renderer processes together at 1/R of ONE logical
//                     processor, i.e. a single thread runs at most 1/R of full speed
//        affinity     the same job, no rate cap, restricted to one logical processor
//   --mode refine --method jobcap --rate R --dpr N --samples 3 --root <tree>
//        the R33-09 measurement: unthrottled refinement samples, then the cap, an in-page worker calibration under the
//        cap, throttled refinement samples (240 s product deadline; 200 s = 240/1.2 threshold), then uncap and a
//        post-calibration. Durations are host-side wall time from SalahMoonRuntime.refresh() to the adopted result.
//        Model: the whole renderer gets 1/R of ONE processor, so a single thread alone runs at 1/R; the multi-threaded
//        refinement (about 55 CPU-s over about 2.6 busy cores) slows far more than R. A pessimistic single-core bound.
//   --mode refine-throughput --method jobcap --rate R --dpr N --samples 3 --root <tree>
//        concurrency-adjusted: the renderer is joined to the job uncapped, its mean busy cores B over the unthrottled
//        refinements is measured by job accounting, and the cap is B/R cores; a 4-worker simultaneous calibration
//        (expected per-loop slowdown 4/cap, +-20 %, job CPU +-10 % of the cap) decides validity.
// Usage: node tools/qa/r0033_worker_throttle.cjs --mode <calibrate|refine> --method <m> --out <dir> [--rate 4] [--dpr 1]
//        [--samples 3] [--reps 5] [--root <tree>] [--playwright <pkg>]
// Output: one JSON line on stdout (with the isolation verdict) and <out>/<tag>-requests.json.
// Exit: 0 complete, 1 error, 2 INCOMPLETE (calibration outside tolerance or no measurement), 3 isolation escape.
require('./v1_net_guard.cjs').install();
const iso=require('./r0033_isolation.cjs');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),net=require('node:net'),{spawn}=require('node:child_process');
const a={};const v=process.argv.slice(2);for(let i=0;i<v.length;i+=2)a[v[i].slice(2)]=v[i+1];
const PW=require(a.playwright||'playwright'),mode=a.mode,method=a.method||'none',out=path.resolve(a.out);
const rate=Number(a.rate||4),dpr=Number(a.dpr||1),samples=Number(a.samples||3),reps=Number(a.reps||5),root=a.root?path.resolve(a.root):null;
const TOLERANCE=0.15;   // a method is valid at rate R when the worker benchmark slows by R within +-15 %
fs.mkdirSync(out,{recursive:true});

// Hand-assembled WASM: (func (export "run") (param i32) (result i32)) an LCG loop of n steps.
function wasmBytes(){const s=n=>{const o=[];for(;;){const b=n&0x7f;n>>=7;if((n===0&&!(b&0x40))||(n===-1&&(b&0x40))){o.push(b);return o;}o.push(b|0x80);}};
 const body=[0x01,0x01,0x7f, 0x03,0x40, 0x20,0x01,0x41,...s(1664525),0x6c,0x41,...s(1013904223),0x6a,0x21,0x01, 0x20,0x00,0x41,0x01,0x6b,0x22,0x00,0x0d,0x00, 0x0b, 0x20,0x01, 0x0b];
 const sec=(id,c)=>[id,c.length,...c];
 return [0x00,0x61,0x73,0x6d,0x01,0x00,0x00,0x00,...sec(1,[0x01,0x60,0x01,0x7f,0x01,0x7f]),...sec(3,[0x01,0x00]),...sec(7,[0x01,0x03,0x72,0x75,0x6e,0x00,0x00]),...sec(10,[0x01,body.length,...body])];}
const N_JS=400000000,N_WASM=400000000;
// Installs window.__cal(kind, n): kind 'js-worker' | 'wasm-worker' | 'js-main'; resolves to wall ms (performance.now).
const CAL=`(()=>{const src='const w=new Uint8Array(${JSON.stringify(wasmBytes())});let inst=null;'+
 'onmessage=async e=>{if(!inst)inst=(await WebAssembly.instantiate(w)).instance;const{kind,n}=e.data,t=performance.now();let r=1;'+
 'if(kind==="js"){for(let i=0;i<n;i++)r=(Math.imul(r,1664525)+1013904223)|0;}else r=inst.exports.run(n);postMessage({ms:performance.now()-t,r});};';
 let w=null;const worker=()=>w||(w=new Worker(URL.createObjectURL(new Blob([src],{type:'text/javascript'}))));
 window.__cal=(kind,n)=>{if(kind==='js-main'){const t=performance.now();let r=1;for(let i=0;i<n;i++)r=(Math.imul(r,1664525)+1013904223)|0;return Promise.resolve({ms:performance.now()-t,r});}
  return new Promise(res=>{const k=worker();k.onmessage=e=>res(e.data);k.postMessage({kind:kind==='js-worker'?'js':'wasm',n});});};
 // n dedicated workers running the JS loop at the same time; resolves to each worker's wall ms.
 const pool=[];window.__calPar=(n,iters)=>{while(pool.length<n)pool.push(new Worker(URL.createObjectURL(new Blob([src],{type:'text/javascript'}))));
  return Promise.all(pool.slice(0,n).map(k=>new Promise(res=>{k.onmessage=e=>res(e.data.ms);k.postMessage({kind:'js',n:iters});})));};})();`;
// Multi-worker calibration (refine-throughput): PAR_N simultaneous worker loops of N_PAR steps (about 1.2 s each
// unthrottled, long enough to average a hard cap enforced in budget intervals). Under a cap of c cores (c < PAR_N)
// each loop's expected slowdown is PAR_N/c. Tolerance, fixed before any run: the median per-loop ratio within
// +-20 % of PAR_N/c, and the job CPU during that calibration within +-10 % of c.
const PAR_N=4,N_PAR=1600000000,PAR_TOL=0.20,CAP_TOL=0.10;
async function parBench(page,n){await page.evaluate(([k])=>window.__calPar(k,2e7),[PAR_N]);const reps=[];
 for(let i=0;i<n;i++)reps.push(await page.evaluate(([k,m])=>window.__calPar(k,m),[PAR_N,N_PAR]));const all=reps.flat();return {reps,median:median(all),min:Math.min(...all),max:Math.max(...all)};}
const median=x=>{const s=[...x].sort((p,q)=>p-q);return s.length?s[Math.floor((s.length-1)/2)]:null;};
const stats=x=>{if(!x.length)return null;const s=[...x].sort((p,q)=>p-q),at=q=>s[Math.min(s.length-1,Math.ceil(q*s.length)-1)];return {n:s.length,min:s[0],median:at(.5),p95:at(.95),max:s[s.length-1]};};
async function bench(page,kinds,n){const r={};for(const k of kinds){await page.evaluate(([k])=>window.__cal(k,2e7),[k]);   // warm-up (JIT tier-up)
  const ms=[];for(let i=0;i<n;i++)ms.push((await page.evaluate(([k,m])=>window.__cal(k,m),[k,k.startsWith('wasm')?N_WASM:N_JS])).ms);r[k]={ms,median:median(ms)};}return r;}
const ratios=(b,t)=>Object.fromEntries(Object.keys(t).map(k=>[k,b[k]&&t[k]?t[k].median/b[k].median:null]));

// ---- Job Object helper (Windows) -----------------------------------------------------------------------------------
function jobHelper(){
 const p=spawn('pwsh',['-NoProfile','-NonInteractive','-File',path.join(__dirname,'r0033_jobcap.ps1')],{stdio:['pipe','pipe','pipe']});
 let buf='';const waiting=[],lines=[];p.stdout.on('data',d=>{buf+=d;let i;while((i=buf.indexOf('\n'))>=0){const l=buf.slice(0,i).trim();buf=buf.slice(i+1);if(!l)continue;const o=JSON.parse(l);lines.push(o);const w=waiting.shift();if(w)w(o);}});
 let err='';p.stderr.on('data',d=>err+=d);
 const next=()=>new Promise(r=>waiting.push(r));const ready=next();
 const cmd=async c=>{const r=next();p.stdin.write(c+'\n');const o=await r;if(o.error)throw Error('jobcap '+c+': error '+o.error+' '+err);return o;};
 return {ready,cmd,log:lines,close:async()=>{try{await cmd('quit');}catch{}p.stdin.end();}};}
async function rendererPids(S){const c=await S.browser.newBrowserCDPSession(),r=await c.send('SystemInfo.getProcessInfo');await c.detach();return r.processInfo.filter(p=>p.type==='renderer').map(p=>p.id);}

// ---- raw loopback CDP (cdp-worker) ---------------------------------------------------------------------------------
const freePort=()=>new Promise(r=>{const s=net.createServer().listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>r(p));});});
const getJson=url=>new Promise((res,rej)=>http.get(url,r=>{let d='';r.on('data',c=>d+=c);r.on('end',()=>{try{res(JSON.parse(d));}catch(e){rej(e);}});}).on('error',rej));
async function rawCdp(port){const {webSocketDebuggerUrl}=await getJson(`http://127.0.0.1:${port}/json/version`);
 if(!/^ws:\/\/127\.0\.0\.1:/.test(webSocketDebuggerUrl))throw Error('CDP endpoint is not loopback');
 const ws=new WebSocket(webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
 let id=0;const pend=new Map(),events=[];ws.onmessage=m=>{const o=JSON.parse(m.data);if(o.id&&pend.has(o.id)){pend.get(o.id)(o);pend.delete(o.id);}else events.push(o);};
 const send=(method,params={},sessionId)=>new Promise(r=>{const i=++id;pend.set(i,r);ws.send(JSON.stringify({id:i,method,params,...(sessionId?{sessionId}:{})}));});
 return {send,events,close:()=>ws.close()};}

const PRAYER=day=>{const [d,m,y]=day.split('-').map(Number);return {timings:{Fajr:'04:47',Sunrise:'06:05',Dhuhr:'12:19',Asr:'15:48',Maghrib:'18:33',Sunset:'18:33',Isha:'20:03'},
 meta:{timezone:'Asia/Riyadh',method:{id:4,params:{Fajr:18.5,Isha:'90 min'}}},date:{gregorian:{date:day,day:String(d).padStart(2,'0'),month:{number:m,en:'September'},year:String(y)},hijri:{day:'26',month:{number:3,en:'Rabi'},year:'1448'}}};};
const fixture=u=>{const m=u.hostname==='api.aladhan.com'&&/\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u.pathname);return m?{code:200,status:'OK',data:PRAYER(m[1])}:null;};
// The same in-page weather fixture (clear night) and radar refusal as r0033_remaining_cells.cjs.
const SHIM=`(()=>{const nf=window.fetch.bind(window),iso=ms=>new Date(ms+3*3600000).toISOString().slice(0,16);
 const json=v=>Promise.resolve(new Response(JSON.stringify(v),{status:200,headers:{'Content-Type':'application/json'}}));
 window.fetch=(input,init)=>{const u=String(input&&input.url||input);
  if(u.includes('api.open-meteo.com')){const w=Date.now(),m=Math.floor(w/60000)*60000,h0=Math.floor(w/3600000)*3600000-7200000,N=72,t=[],arr=f=>Array.from({length:N},f);
   for(let i=0;i<N;i++)t.push(iso(h0+i*3600000));
   return json({timezone:'Asia/Riyadh',utc_offset_seconds:10800,elevation:600,current:{time:iso(m),interval:900,weather_code:0,temperature_2m:24,apparent_temperature:24,relative_humidity_2m:40,dew_point_2m:10,wind_speed_10m:3,wind_direction_10m:90,wind_gusts_10m:5,cloud_cover:0,cloud_cover_low:0,cloud_cover_mid:0,cloud_cover_high:0,precipitation:0,rain:0,showers:0,snowfall:0,is_day:0,visibility:24000},
    hourly:{time:t,temperature_2m:arr(()=>24),weather_code:arr(()=>0),precipitation:arr(()=>0),cloud_cover:arr(()=>0),relative_humidity_2m:arr(()=>40),wind_speed_10m:arr(()=>3),visibility:arr(()=>24000),is_day:arr(()=>0)}});}
  if(u.includes('api.rainviewer.com'))return Promise.reject(new TypeError('controlled radar unavailable'));
  return nf(input,init);};})();`;
const FACTS=`(()=>{const o=window.SalahMoonRuntime?.observe?.()??null,s=o?.state??null;return {status:s?.status??null,visibleSource:s?.visibleSource??null,pending:s?.pending??null,renders:s?.renders??null,
 recovery:s?.recovery??null,errors:(s?.errors??[]).slice(-3),last:s?.last?{totalMs:s.last.totalMs??null,workers:s.last.rowScheduling?.workers??null,workerTimes:s.last.rowScheduling?.workerTimes??null}:null,dpr:window.devicePixelRatio};})()`;
const FROZEN='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&seed=1&simTime=22:00&simWx=0&simMoon=0.5&simWax=1&simMoonAlt=20&simMoonH=42';
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm'};
const server=http.createServer((req,res)=>{const u=new URL(req.url,'http://x');
 if(u.pathname==='/__r0033_cal.html'){res.writeHead(200,{'content-type':'text/html','cache-control':'no-store'});return res.end('<!doctype html><meta charset="utf-8"><title>R33-09 calibration</title><p>calibration</p>');}
 if(!root){res.writeHead(404);return res.end();}
 const p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
 if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);});

(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const port=method==='cdp-worker'?await freePort():null;
 // cdp-worker only: the same isolated launch with one added argument (a loopback DevTools port).
 const P=port?{chromium:{launch:o=>PW.chromium.launch({...o,args:[...(o.args||[]),'--remote-debugging-address=127.0.0.1','--remote-debugging-port='+port]})}}:PW;
 const S=await iso.launch(P,'chromium');const tag=`${mode}-${method}${mode.startsWith('refine')?'-dpr'+dpr:''}${method==='none'||method==='affinity'?'':'-x'+rate}`;
 const emit=o=>console.log(JSON.stringify({mode,method,rate,version:S.browser.version(),logicalProcessors:require('node:os').cpus().length,...o,isolation:S.verdict()}));
 let job=null,incomplete=false;
 try{
  const C=await S.context({viewport:{width:325,height:530},deviceScaleFactor:dpr,timezoneId:'Asia/Riyadh',locale:'en-US',reducedMotion:'no-preference'},{origin:base,fixture});
  await C.context.addInitScript(SHIM);await C.context.addInitScript(CAL);
  const page=await C.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e.message).slice(0,160)));
  const cores=require('node:os').cpus().length,cpuRate=Math.max(1,Math.round(10000/(cores*rate)));
  const apply=async()=>{const info={method};
   if(method==='cdp-page'){const c=await C.context.newCDPSession(page);await c.send('Emulation.setCPUThrottlingRate',{rate});info.page=true;info.release=()=>c.send('Emulation.setCPUThrottlingRate',{rate:1});}
   else if(method==='cdp-worker'){const r=await rawCdp(port);const t=(await r.send('Target.getTargets')).result.targetInfos,pageT=t.find(x=>x.type==='page'&&x.url.startsWith(base));
    const ps=(await r.send('Target.attachToTarget',{targetId:pageT.targetId,flatten:true})).result.sessionId;
    await r.send('Target.setAutoAttach',{autoAttach:true,waitForDebuggerOnStart:false,flatten:true},ps);await new Promise(q=>setTimeout(q,500));
    const workers=r.events.filter(e=>e.method==='Target.attachedToTarget'&&/worker/.test(e.params.targetInfo.type)).map(e=>({type:e.params.targetInfo.type,sessionId:e.params.sessionId}));
    info.workerTargets=workers.length;info.responses=[];
    for(const w of workers){const x=await r.send('Emulation.setCPUThrottlingRate',{rate},w.sessionId);info.responses.push({type:w.type,ok:!x.error,error:x.error?.message??null});}
    info.release=async()=>{for(const w of workers)await r.send('Emulation.setCPUThrottlingRate',{rate:1},w.sessionId);r.close();};}
   else if(method==='jobcap'||method==='affinity'){job=jobHelper();const created=await job.ready;if(created.error)throw Error('CreateJobObject error '+created.error);
    const pids=await rendererPids(S);info.rendererPids=pids.length;for(const p of pids)await job.cmd('assign '+p);
    if(method==='jobcap'){await job.cmd('cap '+cpuRate);info.cpuRate=cpuRate;info.capCores=cpuRate*cores/10000;}else{await job.cmd('affinity 1');info.affinityMask=1;}
    info.release=async()=>{await job.cmd(method==='jobcap'?'uncap':'affinity 0');};}
   return info;};
  const account=async()=>job?{at:Date.now(),...(await job.cmd('account'))}:null;
  const busyCores=(x,y)=>x&&y?((y.user100ns+y.kernel100ns)-(x.user100ns+x.kernel100ns))/1e4/(y.at-x.at):null;
  if(mode==='calibrate'){
   await page.goto(base+'/__r0033_cal.html');const kinds=['js-worker','wasm-worker','js-main'];
   const before=await bench(page,kinds,reps);const info=await apply();const a0=await account();
   const during=await bench(page,kinds,reps);const a1=await account();const r=ratios(before,during);
   if(info.release)await info.release();const after=await bench(page,kinds,reps);delete info.release;
   const target=method==='none'||method==='affinity'?null:rate,valid=target?Math.abs(r['js-worker']/target-1)<=TOLERANCE&&Math.abs(r['wasm-worker']/target-1)<=TOLERANCE:null;
   if(target&&!valid)incomplete=true;
   emit({benchmark:{iterationsJs:N_JS,iterationsWasm:N_WASM,reps},before,during,after,slowdown:r,recovered:ratios(before,after),applied:info,
    jobBusyCoresDuring:busyCores(a0,a1),targetSlowdown:target,tolerance:TOLERANCE,validAtRate:valid,errors});
  }else if(mode==='refine'){
   if(method!=='jobcap')throw Error('refine runs only with --method jobcap (the method whose calibration reaches workers)');
   if(!root)throw Error('--root <tree> required');
   await page.clock.install({time:Date.parse('2026-09-08T19:00:00Z')});await page.clock.resume();
   await page.goto(base+'/index.html'+FROZEN);
   const facts=()=>page.evaluate(FACTS);
   const until=async(pred,ms,step=250)=>{const t0=Date.now();let f=null;while(Date.now()-t0<ms){f=await facts();if(pred(f))return {ok:true,f,ms:Date.now()-t0};await page.waitForTimeout(step);}return {ok:false,f,ms:Date.now()-t0};};
   const refined=f=>f.visibleSource==='refined-terrain'&&f.status==='ready'&&!f.pending;
   const first=await until(refined,600000,500);if(!first.ok)throw Error('no refined surface before the cap: '+JSON.stringify(first.f));
   async function sample(){const before=await facts(),t=Date.now();await page.evaluate(()=>window.SalahMoonRuntime.refresh());
    const r=await until(f=>(f.renders>before.renders&&f.status==='ready'&&!f.pending)||f.status==='unavailable',300000,250);
    return {ms:Date.now()-t,completed:r.ok&&r.f.renders>before.renders,killed:r.f?.status==='unavailable',lastClass:r.f?.recovery?.lastClass??null,errors:r.f?.errors??null,workerTotalMs:r.f?.last?.totalMs??null,rowWorkers:r.f?.last?.workers??null,rowWorkerMs:r.f?.last?.workerTimes??null};}
   const kinds=['js-worker','wasm-worker'],calBefore=await bench(page,kinds,3);
   const baseline=[];for(let i=0;i<samples;i++)baseline.push(await sample());
   const info=await apply();const calDuring=await bench(page,kinds,3),calRatio=ratios(calBefore,calDuring);
   const a0=await account(),throttled=[];for(let i=0;i<samples;i++){const s=await sample();throttled.push(s);if(s.killed)break;}const a1=await account();
   await info.release();delete info.release;const calAfter=await bench(page,kinds,3);
   const b=stats(baseline.filter(s=>s.completed).map(s=>s.ms)),t=stats(throttled.filter(s=>s.completed).map(s=>s.ms)),killed=throttled.some(s=>s.killed);
   const valid=Math.abs(calRatio['js-worker']/rate-1)<=TOLERANCE&&Math.abs(calRatio['wasm-worker']/rate-1)<=TOLERANCE;
   incomplete=!valid||!b||(!t&&!killed);
   emit({dpr,samples,deadlineMs:240000,thresholdMs:240000/1.2,applied:info,
    calibration:{before:calBefore,during:calDuring,after:calAfter,slowdown:calRatio,recovered:ratios(calBefore,calAfter),targetSlowdown:rate,tolerance:TOLERANCE,validAtRate:valid},
    baseline:{samples:baseline,ms:b},throttled:{samples:throttled,ms:t,killedByDeadline:killed},jobBusyCoresDuringThrottledSamples:busyCores(a0,a1),
    refinementSlowdown:b&&t?t.median/b.median:null,p95ExceedsThreshold:killed||(t?t.p95>240000/1.2:null),errors,
    limits:['the cap limits all renderer processes together (main thread, compositor, the Moon worker and its row workers share 1/R of one logical processor); it is a single-slow-core device model, harsher than R-times-slower cores of the same count',
     'the GPU and browser processes are not capped','p95 over '+samples+' samples is the maximum','durations are host-side wall time from refresh() to the adopted result']});
  }else if(mode==='refine-throughput'){
   // Concurrency-adjusted model: the renderer is put in the job UNCAPPED first, its mean busy cores B is measured by job
   // accounting over the unthrottled refinement samples, and the cap is then B/R cores, so the refinement's total CPU
   // demand is served R times more slowly (an aggregate approximation of R-times-slower cores, not a per-thread throttle).
   if(method!=='jobcap')throw Error('refine-throughput runs only with --method jobcap');
   if(!root)throw Error('--root <tree> required');
   await page.clock.install({time:Date.parse('2026-09-08T19:00:00Z')});await page.clock.resume();
   await page.goto(base+'/index.html'+FROZEN);
   const facts=()=>page.evaluate(FACTS);
   const until=async(pred,ms,step=250)=>{const t0=Date.now();let f=null;while(Date.now()-t0<ms){f=await facts();if(pred(f))return {ok:true,f,ms:Date.now()-t0};await page.waitForTimeout(step);}return {ok:false,f,ms:Date.now()-t0};};
   const refined=f=>f.visibleSource==='refined-terrain'&&f.status==='ready'&&!f.pending;
   const first=await until(refined,600000,500);if(!first.ok)throw Error('no refined surface before the cap: '+JSON.stringify(first.f));
   async function sample(){const before=await facts(),t=Date.now(),c0=await account();await page.evaluate(()=>window.SalahMoonRuntime.refresh());
    const r=await until(f=>(f.renders>before.renders&&f.status==='ready'&&!f.pending)||f.status==='unavailable',300000,250);const c1=await account();
    return {ms:Date.now()-t,cpuSeconds:((c1.user100ns+c1.kernel100ns)-(c0.user100ns+c0.kernel100ns))/1e7,busyCores:busyCores(c0,c1),completed:r.ok&&r.f.renders>before.renders,killed:r.f?.status==='unavailable',lastClass:r.f?.recovery?.lastClass??null,errors:r.f?.errors??null,workerTotalMs:r.f?.last?.totalMs??null};}
   job=jobHelper();const created=await job.ready;if(created.error)throw Error('CreateJobObject error '+created.error);
   const assigned=new Set();const assignAll=async()=>{for(const p of await rendererPids(S))if(!assigned.has(p)){await job.cmd('assign '+p);assigned.add(p);}};
   await assignAll();
   const kinds=['js-worker','wasm-worker'],calBefore=await bench(page,kinds,3),parBefore=await parBench(page,3);
   const baseline=[];for(let i=0;i<samples;i++)baseline.push(await sample());
   const done=baseline.filter(s=>s.completed);if(!done.length)throw Error('no unthrottled refinement completed');
   const B=done.reduce((n,s)=>n+s.cpuSeconds,0)/done.reduce((n,s)=>n+s.ms/1000,0),capCores=B/rate,capRate=Math.max(1,Math.round(capCores*10000/cores)),capActual=capRate*cores/10000;
   await assignAll();await job.cmd('cap '+capRate);let capped=true;
   try{
    const calDuring=await bench(page,kinds,3),p0=await account(),parDuring=await parBench(page,3),p1=await account();
    const expectedPar=Math.max(1,PAR_N/capActual),parRatio=parDuring.median/parBefore.median,parCores=busyCores(p0,p1);
    const parValid=Math.abs(parRatio/expectedPar-1)<=PAR_TOL&&Math.abs(parCores/capActual-1)<=CAP_TOL;
    const a0=await account(),throttled=[];for(let i=0;i<samples;i++){const s=await sample();throttled.push(s);if(s.killed)break;}const a1=await account();
    await job.cmd('uncap');capped=false;const calAfter=await bench(page,kinds,3);
    const b=stats(done.map(s=>s.ms)),t=stats(throttled.filter(s=>s.completed).map(s=>s.ms)),killed=throttled.some(s=>s.killed);
    incomplete=!parValid||!b||(!t&&!killed);
    emit({model:'throughput (cap = measured busy cores / R)',dpr,samples,deadlineMs:240000,thresholdMs:240000/1.2,rendererPids:assigned.size,
     unthrottledBusyCores:B,unthrottledCpuSecondsPerRefinement:stats(done.map(s=>s.cpuSeconds)),capCores:capActual,cpuRate:capRate,
     calibration:{singleLoop:{before:calBefore,during:calDuring,slowdown:ratios(calBefore,calDuring),expected:Math.max(1,1/capActual),after:calAfter,recovered:ratios(calBefore,calAfter),informational:true},
      multiWorker:{workers:PAR_N,iterations:N_PAR,before:parBefore,during:parDuring,perLoopSlowdown:parRatio,spread:[parDuring.min/parBefore.median,parDuring.max/parBefore.median],expected:expectedPar,jobBusyCores:parCores,tolerance:{ratio:PAR_TOL,cores:CAP_TOL},valid:parValid}},
     baseline:{samples:baseline,ms:b},throttled:{samples:throttled,ms:t,killedByDeadline:killed},jobBusyCoresDuringThrottledSamples:busyCores(a0,a1),
     refinementSlowdown:b&&t?t.median/b.median:null,targetSlowdown:rate,p95ExceedsThreshold:killed||(t?t.p95>240000/1.2:null),errors,
     limits:['aggregate cap B/R approximates R-times-slower cores for the refinement as a whole; it is not a per-thread throttle: serial phases run faster than 1/R and parallel phases slower','one host (16 logical processors), Chromium only','the GPU and browser processes are not capped','p95 over '+samples+' samples is the maximum','durations are host-side wall time from refresh() to the adopted result']});
   }finally{if(capped)await job.cmd('uncap').catch(()=>{});}
  }else throw Error('unknown mode '+mode);
 }catch(e){emit({error:String(e.stack||e).slice(0,600)});process.exitCode=1;}
 finally{if(job){await job.cmd('uncap').catch(()=>{});await job.close();}await S.settle();fs.writeFileSync(path.join(out,tag+'-requests.json'),JSON.stringify({mode,method,verdict:S.verdict(),requests:S.ledger.requests},null,1));await S.close();server.close();}
 const verdict=S.verdict();if(!verdict.ok){console.error('ISOLATION ESCAPE '+JSON.stringify(verdict.escapes));process.exitCode=3;}else if(!process.exitCode&&incomplete)process.exitCode=2;
})();
