'use strict';
// R002D D-13 / D-15 native recipe (issue 94). Serves an unchanged generated tree from --root on 127.0.0.1,
// stubs the prayer provider (meta.timezone Asia/Riyadh) and aborts every other non-local request (weather,
// radar, geocoding: unavailable), forces the browser time zone, installs a mocked clock at a chosen instant
// and lets it run. Per cell it records the .c class-transition log (sky-pending / sky-initializing /
// moon-ready, sampled once per animation frame), the prayer request days, qaState().zone (when the tree exposes it), the final scene key, the
// prayer rows and a settled card screenshot. Cells compare the builder-shape hash (no tz) with the
// tz=Asia%2FRiyadh control and a rejected hint. It never contacts a real provider.
//
// Usage: node tools/qa/run_r002d_native.cjs --root <tree> --out <fresh dir> [--engines chromium,firefox,webkit]
//        [--playwright <path to the playwright package>]
// The report states what was observed; it does not claim pixel identity unless the bytes compare equal.
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const args=Object.fromEntries(process.argv.slice(2).reduce((a,v,i,all)=>(v.startsWith('--')&&a.push([v.slice(2),all[i+1]]),a),[]));
const root=path.resolve(args.root||path.join(__dirname,'..','..')),out=path.resolve(args.out||'r002d-native-out');
const engines=(args.engines||'chromium,firefox,webkit').split(',');
const {chromium,firefox,webkit}=require(args.playwright||'playwright');
const ENG={chromium,firefox,webkit};
fs.mkdirSync(out,{recursive:false});
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const ordinary=JSON.parse(fs.readFileSync(path.join(root,'tests/r0002-ordinary.json'),'utf8'));
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
function record(day,zone){
  const r=JSON.parse(JSON.stringify(ordinary)),[d,mo,y]=day.split('-').map(Number);r.meta.timezone=zone;
  r.date.gregorian={...r.date.gregorian,date:day,day:String(d).padStart(2,'0'),month:{number:mo,en:MONTHS[mo-1]},year:String(y)};
  return r;
}
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream','.woff2':'font/woff2','.jpg':'image/jpeg','.webp':'image/webp'};
const server=http.createServer((req,res)=>{
  const u=new URL(req.url,'http://x'),p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
  if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
  res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);
});
const CELLS=[];
for(const [instant,label] of [['2026-09-07T22:00:00Z','days-differ'],['2026-09-07T12:00:00Z','days-equal']])
  for(const [hash,name] of [['#lat=24.47&lon=39.61&label=Madinah&method=4&seed=1','builder'],['#lat=24.47&lon=39.61&label=Madinah&method=4&seed=1&tz=Asia%2FRiyadh','control'],['#lat=24.47&lon=39.61&label=Madinah&method=4&seed=1&tz=Bogus%2FZone','rejected']])
    CELLS.push({instant,label,hash,name});
const OBSERVE=`(()=>{window.__r002d={log:[],t0:performance.now()};
 const start=()=>{const c=document.querySelector('.c');if(!c)return requestAnimationFrame(start);
  // Sampled once per animation frame: a class state that never reaches a frame is never presented.
  const at=()=>Math.round(performance.now()-__r002d.t0);__r002d.initial=[...c.classList];let prev=new Set(c.classList);
  const tick=()=>{const now=new Set(c.classList);for(const k of ['sky-pending','sky-initializing','moon-ready']){if(now.has(k)&&!prev.has(k))__r002d.log.push(['+'+k,at()]);if(!now.has(k)&&prev.has(k))__r002d.log.push(['-'+k,at()]);}
   prev=now;if(__r002d.log.length<400)requestAnimationFrame(tick);};requestAnimationFrame(tick);};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();})();`;
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
  const report={scope:'R002D D-13/D-15 native observation; stubbed prayer provider; weather/radar unavailable; mocked clock running',root:path.basename(root),
    inputs:Object.fromEntries(['index.html','config.js','offline.html'].map(f=>[f,fs.existsSync(path.join(root,f))?sha(fs.readFileSync(path.join(root,f))):null])),engines:{},cells:[]};
  for(const engine of engines){
    const browser=await ENG[engine].launch({headless:true});report.engines[engine]=browser.version();
    for(const cell of CELLS){
      const context=await browser.newContext({viewport:{width:325,height:530},deviceScaleFactor:1,timezoneId:'America/Los_Angeles',locale:'en-US',reducedMotion:'reduce'});
      const days=[],aborted=[];
      await context.route('**/*',route=>{const u=route.request().url();
        if(u.startsWith(base))return route.continue();
        const m=/api\.aladhan\.com\/v1\/timings\/(\d{2}-\d{2}-\d{4})/.exec(u);
        if(m){days.push(m[1]);return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1],'Asia/Riyadh')})});}
        if(/aladhan/.test(u))days.push('UNRESOLVED:'+u.replace(/\?.*/,''));
        aborted.push(u.replace(/\?.*/,''));return route.abort();});
      const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));
      await page.clock.install({time:new Date(cell.instant)});
      await page.addInitScript(OBSERVE);
      await page.goto(base+'/index.html'+cell.hash,{waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>{try{return !!today&&_loopStarted}catch(e){return false}},null,{timeout:30000}).catch(()=>{});
      await page.waitForTimeout(4000);
      const state=await page.evaluate(()=>{let zone=null;try{zone=window.qaState().zone??null}catch(e){}
        return {tz,cacheTz:_cacheTz,sceneKey:_skySceneKey,today:!!today,zone,log:window.__r002d.log,initial:window.__r002d.initial,
          rows:[...document.querySelectorAll('.times .p')].map(p=>p.textContent),left:document.querySelector('.left')?.textContent??null,
          classes:document.querySelector('.c').className};});
      const shot=await page.locator('.c').screenshot();const file=`${engine}-${cell.label}-${cell.name}.png`;fs.writeFileSync(path.join(out,file),shot);
      // Scene (re)starts observed: every +sky-pending, plus an initial pending state present at observation start.
      const sceneStarts=state.log.filter(e=>e[0]==='+sky-pending').length+((state.initial||[]).includes('sky-pending')?1:0);
      const firstCommit=state.log.findIndex(e=>e[0]==='-sky-pending');
      const repending=firstCommit<0?0:state.log.slice(firstCommit+1).filter(e=>e[0]==='+sky-pending').length;
      report.cells.push({engine,...cell,days,abortedHosts:[...new Set(aborted.map(u=>new URL(u).host))],errors,...state,sceneStarts,repending,screenshot:{file,sha256:sha(shot),bytes:shot.length}});
      await context.close();
    }
    await browser.close();
  }
  // Pairwise comparisons within an engine and instant: builder vs control vs rejected.
  report.comparisons=[];
  for(const engine of engines)for(const label of ['days-differ','days-equal']){
    const pick=n=>report.cells.find(c=>c.engine===engine&&c.label===label&&c.name===n);
    const b=pick('builder'),c=pick('control'),r=pick('rejected');
    report.comparisons.push({engine,label,builderEqualsControlBytes:b.screenshot.sha256===c.screenshot.sha256,rejectedEqualsBuilderBytes:r.screenshot.sha256===b.screenshot.sha256,
      rowsEqual:JSON.stringify(b.rows)===JSON.stringify(c.rows)&&JSON.stringify(r.rows)===JSON.stringify(c.rows),
      repending:{builder:b.repending,control:c.repending,rejected:r.repending},sceneStarts:{builder:b.sceneStarts,control:c.sceneStarts,rejected:r.sceneStarts},zones:{builder:b.tz,control:c.tz,rejected:r.tz}});
  }
  // Pixel difference (count of differing pixels and max channel delta) for each comparison pair, decoded in Chromium.
  const decoder=await chromium.launch({headless:true}),dp=await decoder.newPage();
  const pixdiff=async(fa,fb)=>dp.evaluate(async([a,b])=>{const load=async u=>{const i=new Image();i.src=u;await i.decode();const c=new OffscreenCanvas(i.width,i.height),x=c.getContext('2d');x.drawImage(i,0,0);return x.getImageData(0,0,i.width,i.height);};
    const A=await load(a),B=await load(b);if(A.width!==B.width||A.height!==B.height)return {sizeDiffers:true};let n=0,max=0;
    for(let i=0;i<A.data.length;i+=4){let d=0;for(let k=0;k<4;k++)d=Math.max(d,Math.abs(A.data[i+k]-B.data[i+k]));if(d){n++;max=Math.max(max,d);}}return {differingPixels:n,of:A.width*A.height,maxDelta:max};},
    ['data:image/png;base64,'+fs.readFileSync(path.join(out,fa)).toString('base64'),'data:image/png;base64,'+fs.readFileSync(path.join(out,fb)).toString('base64')]);
  for(const cmp of report.comparisons){const f=n=>`${cmp.engine}-${cmp.label}-${n}.png`;cmp.pixels={builderVsControl:await pixdiff(f('builder'),f('control')),rejectedVsControl:await pixdiff(f('rejected'),f('control'))};}
  await decoder.close();
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,1)+'\n');
  console.log(JSON.stringify({engines:report.engines,comparisons:report.comparisons},null,1));
  server.close();
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
