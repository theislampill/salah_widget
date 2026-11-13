'use strict';
// R002F (issue 96) native cells for rows R2F-06, R2F-09, R2F-12, R2F-13 and R2F-14:
//   node tools/qa/run_r002f_native_extra.cjs <playwright> <candidate tree> <baseline tree> <out dir> [engines] [cells]
// cells (default all): hidden, crops, preview, notimetable, pixeldiff, motion.
// Every non-loopback request is route-stubbed: Aladhan from the recorded fixture tests/r0002-ordinary.json (or
// HTTP 503 for the no-timetable cell), Open-Meteo by the upstream floor(now, 15 min) rule read from the PAGE clock,
// RainViewer an empty manifest; anything else is aborted. No provider is contacted. All cells except "motion" use
// Playwright's mocked clock (Date, timers, rAF, performance.now). "motion" is a REAL-time watch (30 s): the clock is
// installed at the fixture date and then resumed, so it flows at wall rate (no boundary inside the watch). Never uses qaState().clouds.hash. Prints one JSON line per engine x cell.
const fs=require('fs'),path=require('path'),http=require('http'),crypto=require('crypto');
const [pwDir,candArg,baseArg,outArg,engArg,cellArg]=process.argv.slice(2);
if(!pwDir||!candArg||!baseArg||!outArg) throw Error('usage: run_r002f_native_extra.cjs <playwright> <candidate> <baseline> <out> [engines] [cells]');
const pw=require(pwDir), out=path.resolve(outArg), engines=(engArg||'chromium,firefox,webkit').split(','), cells=(cellArg||'hidden,crops,preview,notimetable,pixeldiff,motion').split(',');
fs.mkdirSync(out,{recursive:true});
const MIME={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.wasm':'application/wasm','.png':'image/png','.bin':'application/octet-stream','.css':'text/css','.svg':'image/svg+xml','.webp':'image/webp','.jpg':'image/jpeg'};
function serve(root){ root=path.resolve(root); const srv=http.createServer((q,s)=>{const p=path.join(root,decodeURIComponent(new URL(q.url,'http://x').pathname));
  if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){s.writeHead(404);return s.end();}
  s.writeHead(200,{'content-type':MIME[path.extname(p)]||'application/octet-stream'});fs.createReadStream(p).pipe(s);});
  return new Promise(r=>srv.listen(0,'127.0.0.1',()=>r({srv,base:'http://127.0.0.1:'+srv.address().port,name:path.basename(root)}))); }
const rec=JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','tests','r0002-ordinary.json'),'utf8'));
const B=Date.parse('2026-09-07T09:00:00Z'), iso=ms=>new Date(ms+3*3600000).toISOString().slice(0,16);
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const SCENES={thunder:{code:95,precip:2,cloud:95},rain:{code:63,precip:2,cloud:95},cloudy:{code:3,precip:0,cloud:95}};
const LOOK=`(()=>{const c=document.querySelector('.c'),cv=document.querySelector('.cloudcanvas');let painted=0;
  try{const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data;for(let i=3;i<d.length;i+=4)if(d[i])painted++;}catch(e){painted=-1;}
  return {now:Date.now(),sel:!!selectedWeather(),ready:_cloudReady,painted,wt:document.querySelector('#wt').textContent,wi:document.querySelector('#wi').textContent,
  precip:c.dataset.precip,lightning:c.dataset.lightning,left:(document.querySelector('.left')||{}).textContent||null,seed:_cloudFieldSeed,population:_cloudMotion.population};})()`;
async function open(engine,srv,{scene='thunder',prayer='ok',clock=B-150000,real=false,reduced=false}={}){
  const S=SCENES[scene], b=await pw[engine].launch(), c=await b.newContext({viewport:{width:325,height:530},timezoneId:'Asia/Riyadh',reducedMotion:reduced?'reduce':'no-preference'});
  let page=null; const requests=[];
  await c.route('**/*',async r=>{const u=r.request().url(); if(u.startsWith(srv.base)) return r.continue();
    const json=(body,status=200)=>r.fulfill({status,contentType:'application/json',headers:{'access-control-allow-origin':'*'},body:JSON.stringify(body)});
    if(u.includes('api.aladhan.com')){ if(prayer!=='ok') return json({code:503,status:'unavailable'},503);
      const m=/timings\/(\d\d-\d\d-\d{4})/.exec(u),x=JSON.parse(JSON.stringify(rec));x.meta.timezone='Asia/Riyadh';if(m)x.date.gregorian.date=m[1];return json({code:200,status:'OK',data:x}); }
    if(u.includes('api.open-meteo.com')){ let now; try{ now=await page.evaluate(()=>Date.now()); }catch(e){ now=Date.now(); }
      requests.push(now); const q=Math.floor(now/900000)*900000,hr=q-q%3600000;
      return json({timezone:'Asia/Riyadh',elevation:600,current:{time:iso(q),interval:900,weather_code:S.code,temperature_2m:24,apparent_temperature:26,relative_humidity_2m:80,
        dew_point_2m:18,wind_speed_10m:6,wind_direction_10m:225,wind_gusts_10m:9,cloud_cover:S.cloud,cloud_cover_low:92,cloud_cover_mid:90,cloud_cover_high:60,precipitation:S.precip,rain:S.precip,showers:0,snowfall:0,is_day:1,visibility:10000},
        hourly:{time:[iso(hr),iso(hr+3600000),iso(hr+7200000)],temperature_2m:[24,24,24],weather_code:[S.code,S.code,S.code],cloud_cover:[S.cloud,S.cloud,S.cloud],precipitation:[S.precip,S.precip,S.precip]}}); }
    if(u.includes('api.rainviewer.com')) return json({radar:{past:[]}});
    return r.abort();});
  const p=await c.newPage(); page=p; const errors=[]; p.on('pageerror',e=>errors.push(String(e)));
  await p.clock.install({time:new Date(clock)}); if(real) await p.clock.resume();   // real: the mocked clock then flows in real time
  await p.goto(srv.base+'/index.html#lat=24.47&lon=39.61&label=Madinah&method=4&seed=1&tz=Asia%2FRiyadh');
  const now=()=>p.evaluate(()=>Date.now()), look=()=>p.evaluate(LOOK);
  const until=async(ms,step=250)=>{ while(await now()<ms) await p.clock.runFor(step); };
  const ready=async()=>{ for(let i=0;i<80;i++){ if(await p.evaluate(()=>{try{return window.eval('_loopStarted&&!!selectedWeather()&&_cloudReady')}catch(e){return false}})) return true; if(real) await p.waitForTimeout(250); else await p.clock.runFor(250);} return false; };
  return {b,p,requests,errors,now,look,until,ready,shot:async name=>{const f=path.join(out,name+'.png');await p.screenshot({path:f});return sha(fs.readFileSync(f)).slice(0,16);}};
}
const cellsImpl={
  // R2F-06: hidden across three provider steps, then visible: requests while hidden and on resume.
  async hidden(engine,cand){ const w=await open(engine,cand); await w.ready(); await w.until(B-60000);
    const before=w.requests.length; await w.p.evaluate(()=>{Object.defineProperty(document,'visibilityState',{value:'hidden',configurable:true});document.dispatchEvent(new Event('visibilitychange'));});
    await w.until(B+2*900000+60000,5000); const hiddenRequests=w.requests.length-before;
    await w.p.evaluate(()=>{Object.defineProperty(document,'visibilityState',{value:'visible',configurable:true});document.dispatchEvent(new Event('visibilitychange'));});
    const resumeAt=await w.now(); await w.until(resumeAt+60000); const s=await w.look();
    const r={hiddenRequests,resumeRequests:w.requests.length-before-hiddenRequests,resumeRequestOffsetsMs:w.requests.slice(before+hiddenRequests).map(t=>t-resumeAt),
      afterResume:{sel:s.sel,ready:s.ready,painted:s.painted,wt:s.wt},shot:await w.shot(`hidden-${engine}-after-resume`),pageErrors:w.errors};
    await w.b.close(); return r; },
  // R2F-09: crops across the boundary for rain and cloudy scenes (phase ~25 s: renewal at B+3 s).
  async crops(engine,cand){ const res={};
    for(const scene of ['rain','cloudy']){ const w=await open(engine,cand,{scene,clock:B+25000-150000}); await w.ready();
      await w.until(B-1000); const a=await w.look(); const sa=await w.shot(`crops-${engine}-${scene}-1-before`);
      await w.until(B+1500); const g=await w.look(); const sg=await w.shot(`crops-${engine}-${scene}-2-gap`);
      await w.until(B+4000); const z=await w.look(); const sz=await w.shot(`crops-${engine}-${scene}-3-after`);
      res[scene]={before:{t:a.now-B,sel:a.sel,painted:a.painted,wt:a.wt,precip:a.precip,png:sa},gap:{t:g.now-B,sel:g.sel,painted:g.painted,wt:g.wt,precip:g.precip,png:sg},
        after:{t:z.now-B,sel:z.sel,painted:z.painted,wt:z.wt,precip:z.precip,png:sz},identityKept:a.seed===z.seed&&a.population===z.population,pageErrors:w.errors};
      await w.b.close(); }
    return res; },
  // R2F-12: explicit preview inside and after the hourly track.
  async preview(engine,cand){ const w=await open(engine,cand); await w.ready();
    const last=await w.p.evaluate(()=>window.eval('weatherTrack.ep[weatherTrack.ep.length-1]'));
    await w.p.evaluate(t=>window.SalahClock.set({rate:0,utcMs:t}),last-1800000); await w.p.clock.runFor(1000); const i=await w.look(); const si=await w.shot(`preview-${engine}-inside`);
    await w.p.evaluate(t=>window.SalahClock.set({rate:0,utcMs:t}),last+3600000); await w.p.clock.runFor(1000); const o=await w.look(); const so=await w.shot(`preview-${engine}-after-track`);
    const r={inside:{sel:i.sel,ready:i.ready,painted:i.painted,wt:i.wt,wi:i.wi,png:si},afterTrack:{sel:o.sel,ready:o.ready,painted:o.painted,wt:o.wt,wi:o.wi,precip:o.precip,png:so},pageErrors:w.errors};
    await w.b.close(); return r; },
  // R2F-13: prayer provider failing, healthy wet weather: header vs deck for 2 minutes (R000B no-timetable policy).
  async notimetable(engine,cand){ const w=await open(engine,cand,{scene:'rain',prayer:'fail'}); const t0=await w.now(); const samples=[];
    for(let k=0;k<=8;k++){ await w.until(t0+k*15000,250); const s=await w.look(); samples.push({t:s.now-t0,sel:s.sel,ready:s.ready,painted:s.painted,wt:s.wt,precip:s.precip,left:s.left}); }
    const png0=await w.shot(`notimetable-${engine}-2min`); const r={samples,png:png0,pageErrors:w.errors}; await w.b.close(); return r; },
  // R2F-14: fixed-clock frames with no boundary crossing (reduced motion, CSS animations disabled for the capture);
  // baseline vs candidate, plus a same-tree repeat (noise floor).
  async pixeldiff(engine,cand,base){ const shotAt=async(srv,tag)=>{ const w=await open(engine,srv,{clock:B-600000,reduced:true}); await w.ready(); await w.until(B-480000);
      const f=path.join(out,`pixeldiff-${engine}-${tag}.png`); await w.p.screenshot({path:f,animations:'disabled'}); const r={png:sha(fs.readFileSync(f)).slice(0,16),file:f,errors:w.errors}; await w.b.close(); return r; };
    const c1=await shotAt(cand,'candidate-1'), c2=await shotAt(cand,'candidate-2'), b1=await shotAt(base,'baseline-1'), b2=await shotAt(base,'baseline-2');
    const diff=async(f1,f2)=>{ const b=await pw.chromium.launch(), p=await b.newPage();
      const n=await p.evaluate(async([a,c])=>{const load=s=>new Promise(r=>{const i=new Image();i.onload=()=>r(i);i.src=s;});const [x,y]=await Promise.all([load(a),load(c)]);
        const cv=document.createElement('canvas');cv.width=x.width;cv.height=x.height;const g=cv.getContext('2d');g.drawImage(x,0,0);const A=g.getImageData(0,0,cv.width,cv.height).data;
        g.clearRect(0,0,cv.width,cv.height);g.drawImage(y,0,0);const C=g.getImageData(0,0,cv.width,cv.height).data;let px=0,max=0;
        for(let i=0;i<A.length;i+=4){const d=Math.max(Math.abs(A[i]-C[i]),Math.abs(A[i+1]-C[i+1]),Math.abs(A[i+2]-C[i+2]));if(d){px++;if(d>max)max=d;}}return {px,max};},
        ['data:image/png;base64,'+fs.readFileSync(f1).toString('base64'),'data:image/png;base64,'+fs.readFileSync(f2).toString('base64')]); await b.close(); return n; };
    return {candidateRepeatIdentical:c1.png===c2.png,baselineRepeatIdentical:b1.png===b2.png,candidateVsBaselineIdentical:c1.png===b1.png,
      noiseCandidate:await diff(c1.file,c2.file),noiseBaseline:await diff(b1.file,b2.file),cross1:await diff(c1.file,b1.file),cross2:await diff(c2.file,b2.file),
      pngs:{candidate1:c1.png,candidate2:c2.png,baseline1:b1.png,baseline2:b2.png},pageErrors:[...c1.errors,...c2.errors,...b1.errors,...b2.errors]}; },
  // AGENTS M0: real-time 30 s watch of the live widget (stubbed providers): cloud-canvas change at 15 s and 30 s,
  // against the change between two reads of one frame (noise floor). Real Date: no boundary is aimed at.
  async motion(engine,cand,base){ const one=async srv=>{ const w=await open(engine,srv,{real:true,clock:B-600000}); const isReady=await w.ready(); const state=await w.look();
    const grab=()=>w.p.evaluate(()=>{const cv=document.querySelector('.cloudcanvas');return Array.from(cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data.filter((_,i)=>i%4===3));});
    const d=(a,b)=>{let n=0,s=0;for(let i=0;i<a.length;i++){const x=Math.abs(a[i]-b[i]);if(x){n++;s+=x;}}return {changedPx:n,meanAbs:+(s/a.length).toFixed(3)};};
    const g0=await grab(), g0b=await grab(); await w.p.waitForTimeout(15000); const g15=await grab(); await w.shot(`motion-${engine}-${srv===cand?'candidate':'baseline'}-15s`); await w.p.waitForTimeout(15000); const g30=await grab();
    const r={ready:isReady,state:{sel:state.sel,ready:state.ready,painted:state.painted,wt:state.wt,left:state.left},noiseFloor:d(g0,g0b),delta15s:d(g0,g15),delta30s:d(g0,g30),painted:g0.filter(x=>x).length,pageErrors:w.errors}; await w.b.close(); return r; };
    return {candidate:await one(cand),baseline:await one(base)}; },
};
(async()=>{ const cand=await serve(candArg), base=await serve(baseArg); let bad=false;
  for(const engine of engines) for(const cell of cells){ try{ const r=await cellsImpl[cell](engine,cand,base); console.log(JSON.stringify({engine,cell,...r})); }
    catch(e){ bad=true; console.log(JSON.stringify({engine,cell,error:String(e&&e.message||e)})); } }
  cand.srv.close(); base.srv.close(); process.exit(bad?2:0); })().catch(e=>{console.error(e);process.exit(1);});
