'use strict';
// R002C native recipe (issue 93): R2C-13 injected-fault qualification and R2C-14 healthy pixel conservatism.
// Serves two unchanged generated trees (--base, --cand) from 127.0.0.1, stubs the prayer provider with the
// tests/r0002-ordinary.json record (meta.timezone Asia/Riyadh) and aborts every other non-local request
// (weather, radar, fonts, geocoding: unavailable). No real provider is contacted; no real geolocation.
// Browser zone forced to America/Los_Angeles; a mocked clock is installed at the cell instant and runs.
//
// R2C-14 healthy cells: frozen simTime scenes from the AGENTS evidence list (noon, sunrise, sunset, overcast,
//   rain, thunder, gibbous and crescent Moon, near-Fajr), each run twice per tree for the run-to-run noise
//   floor; the 325x530 card screenshot of base and candidate is compared (byte equality and pixel delta).
// R2C-13 fault cells (real-time, 55 s before the stub Isha so the countdown text changes every second): an
//   init script wraps window.SalahMoonRuntime on assignment so request() throws on every call after the
//   first N (N=2 "after-start"; N=0 "boot"). Samples once per second for 12 s: .left text, the published
//   receipt (qaState().render.leftMin, when present), rows; counts pageerror events and console errors.
//   These are INJECTED faults; they qualify containment, not a natural trigger.
//
// Usage: node tools/qa/run_r002c_native.cjs --base <tree> --cand <tree> --out <fresh dir>
//        [--engines chromium,firefox,webkit] [--playwright <path to the playwright package>]
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const argv=process.argv.slice(2),args={};
for(let i=0;i<argv.length;i++)if(argv[i].startsWith('--')){const k=argv[i].slice(2),v=[];while(argv[i+1]&&!argv[i+1].startsWith('--'))v.push(argv[++i]);args[k]=v.length>1?v:v[0];}
const {chromium,firefox,webkit}=require(args.playwright||'playwright');
const ENG={chromium,firefox,webkit};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
if(!args.base||!args.cand||!args.out){console.error('usage: --base <tree> --cand <tree> --out <fresh dir>');process.exit(2);}
const out=path.resolve(args.out);fs.mkdirSync(out,{recursive:false});
const roots={base:path.resolve(args.base),cand:path.resolve(args.cand)};
const engines=(args.engines||'chromium,firefox,webkit').split(',');
const ordinary=JSON.parse(fs.readFileSync(path.join(roots.cand,'tests/r0002-ordinary.json'),'utf8'));
const MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December'];
function record(day,zone){
  const r=JSON.parse(JSON.stringify(ordinary)),[d,mo,y]=day.split('-').map(Number);r.meta.timezone=zone;
  r.date.gregorian={...r.date.gregorian,date:day,day:String(d).padStart(2,'0'),month:{number:mo,en:MONTHS[mo-1]},year:String(y)};
  return r;
}
const TYPES={'.html':'text/html','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.css':'text/css','.png':'image/png','.svg':'image/svg+xml','.wasm':'application/wasm','.bin':'application/octet-stream','.woff2':'font/woff2','.jpg':'image/jpeg','.webp':'image/webp'};
function serve(root){return http.createServer((req,res)=>{
  const u=new URL(req.url,'http://x'),p=path.normalize(path.join(root,decodeURIComponent(u.pathname)));
  if(!p.startsWith(root)||!fs.existsSync(p)||fs.statSync(p).isDirectory()){res.writeHead(404);return res.end();}
  res.writeHead(200,{'content-type':TYPES[path.extname(p)]||'application/octet-stream','cache-control':'no-store'});fs.createReadStream(p).pipe(res);
});}
const SITE='#lat=24.47&lon=39.61&label=Madinah&method=4&seed=1&tz=Asia%2FRiyadh';
const HEALTHY_ALL=[['noon','&simTime=12:30&simWx=0&simCloud=0'],['sunrise','&simTime=05:50&simWx=0&simCloud=0'],['sunset','&simTime=18:55&simWx=0&simCloud=0'],
  ['overcast','&simTime=12:30&simWx=3&simCloud=100'],['rain','&simTime=14:00&simWx=63'],['thunder','&simTime=14:00&simWx=95&simPrecip=5'],
  ['gibbous','&simTime=22:00&simMoon=0.92&simWax=1&simMoonAlt=20&simMoonH=42'],['crescent','&simTime=20:30&simMoon=0.08&simWax=1&simMoonAlt=20&simMoonH=42'],['near-fajr','&simTime=04:40']];
const HEALTHY=args.scenes?HEALTHY_ALL.filter(([s])=>String(args.scenes).split(',').includes(s)):HEALTHY_ALL;
const SETTLE=+(args.settle||2500);   // ms after the loop starts before the healthy screenshot
const HEALTHY_INSTANT='2026-09-07T12:00:00Z';
const FAULT_INSTANT='2026-09-07T16:29:05Z';   // 19:29:05 Riyadh: 55 s before the stub Isha (19:30)
const FAULTS=('no-faults' in args)?[]:[['after-start',2],['boot',0]];
const HOOK=n=>`(()=>{const L=window.__r2c={calls:0,throws:0};let rt;
 Object.defineProperty(window,'SalahMoonRuntime',{configurable:true,enumerable:true,get(){return rt;},set(v){
  if(v&&typeof v.request==='function'&&!v.__r2cWrapped){const rq=v.request;
   v.request=function(...a){L.calls++;if(L.calls>${n}){L.throws++;throw new Error('injected R002C Moon request failure');}return rq.apply(this,a);};
   Object.defineProperty(v,'__r2cWrapped',{value:true});}
  rt=v;}});})();`;
async function cell(browser,base,{hash,instant,hook}){
  const context=await browser.newContext({viewport:{width:325,height:530},deviceScaleFactor:1,timezoneId:'America/Los_Angeles',locale:'en-US',reducedMotion:'reduce'});
  const days=[];
  await context.route('**/*',route=>{const u=route.request().url();
    if(u.startsWith(base))return route.continue();
    const m=/api\.aladhan\.com\/v1\/timings\/([^?]*)/.exec(u);
    if(m){days.push(m[1]);if(/^\d{2}-\d{2}-\d{4}$/.test(m[1]))return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1],'Asia/Riyadh')})});}
    return route.abort();});
  const page=await context.newPage();const pageErrors=[],consoleErrors=[];
  page.on('pageerror',e=>pageErrors.push(String(e&&e.message||e).slice(0,200)));
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text().slice(0,200));});
  await page.clock.install({time:new Date(instant)});
  if(hook)await page.addInitScript(hook);
  await page.goto(base+'/index.html'+hash,{waitUntil:'domcontentloaded'});
  return {context,page,days,pageErrors,consoleErrors};
}
const read=page=>page.evaluate(()=>{let render=null,faults=null,loop=null,today=null;
  try{const r=window.qaState().render;render=r?{leftMin:r.leftMin,currentKey:r.currentKey,nextKey:r.nextKey,fx:r.fx}:null;}catch(e){}
  try{faults=window.qaState().renderFaults??'absent';}catch(e){faults='unreadable';}
  try{loop=_loopStarted;}catch(e){}try{today=!!window.eval('today');}catch(e){}
  return {left:document.querySelector('.left')?.textContent??null,cn:document.querySelector('.cn')?.textContent??null,
    rows:[...document.querySelectorAll('.times .p')].map(p=>p.textContent).join('|'),render,faults,loop,today,moon:window.__r2c?{...window.__r2c}:null,
    moonRuntime:(()=>{try{const s=window.SalahMoonRuntime?.state;return s?{status:s.status??null,visibleSource:s.visibleSource??null,quality:s.quality??null,epoch:s.epoch??null}:null;}catch(e){return 'unreadable';}})()};});
async function pixelDiffer(){
  const browser=await chromium.launch({headless:true}),page=await browser.newPage();
  const diff=(a,b)=>page.evaluate(async([a,b])=>{const load=async u=>{const i=new Image();i.src=u;await i.decode();const c=new OffscreenCanvas(i.width,i.height),x=c.getContext('2d');x.drawImage(i,0,0);return x.getImageData(0,0,i.width,i.height);};
    const A=await load(a),B=await load(b);if(A.width!==B.width||A.height!==B.height)return {sizeDiffers:true};let n=0,max=0;
    for(let i=0;i<A.data.length;i+=4){let d=0;for(let k=0;k<4;k++)d=Math.max(d,Math.abs(A.data[i+k]-B.data[i+k]));if(d){n++;max=Math.max(max,d);}}return {differingPixels:n,of:A.width*A.height,maxDelta:max};},
    ['data:image/png;base64,'+a.toString('base64'),'data:image/png;base64,'+b.toString('base64')]);
  return {diff:async(a,b)=>({...(await diff(a,b)),bytesEqual:sha(a)===sha(b)}),close:()=>browser.close()};
}
const servers={},bases={};
(async()=>{
  for(const k of ['base','cand']){servers[k]=serve(roots[k]);await new Promise(r=>servers[k].listen(0,'127.0.0.1',r));bases[k]='http://127.0.0.1:'+servers[k].address().port;}
  const report={scope:'R002C native: R2C-14 healthy pixel conservatism and R2C-13 injected Moon request faults; stubbed prayer provider; every other non-local request aborted; mocked running clock',
    inputs:Object.fromEntries(Object.entries(roots).map(([k,r])=>[k,Object.fromEntries(['index.html','config.js'].map(f=>[f,sha(fs.readFileSync(path.join(r,f)))]))])),engines:{},healthy:[],faults:[]};
  const px=await pixelDiffer();
  for(const engine of engines){
    const browser=await ENG[engine].launch({headless:true});report.engines[engine]=browser.version();
    for(const [scene,extra] of HEALTHY){
      const shots={};
      for(const run of [1,2])for(const k of ['base','cand']){            // interleaved, so timing drift is not attributed to a tree
        const c=await cell(browser,bases[k],{hash:SITE+extra,instant:HEALTHY_INSTANT});
        await c.page.waitForFunction(()=>{try{return !!window.eval('today')&&window.eval('_loopStarted')}catch(e){return false}},null,{timeout:15000}).catch(()=>{});
        // Let asynchronous Moon terrain refinement settle, so its progress at the capture instant is not compared.
        await c.page.waitForFunction(()=>{const s=window.SalahMoonRuntime?.state?.status;return !s||!['refining','pending','initializing','loading'].includes(s);},null,{timeout:30000}).catch(()=>{});
        await c.page.waitForTimeout(SETTLE);
        const shot=await c.page.locator('.c').screenshot(),file=`${engine}-${scene}-${k}-${run}.png`;fs.writeFileSync(path.join(out,file),shot);shots[k+run]=shot;
        if(run===1)report.healthy.push({engine,scene,tree:k,pageErrors:c.pageErrors,consoleErrors:c.consoleErrors,state:await read(c.page)});
        await c.context.close();
      }
      const row={engine,scene,baseNoise:await px.diff(shots.base1,shots.base2),candNoise:await px.diff(shots.cand1,shots.cand2),
        baseVsCand:[await px.diff(shots.base1,shots.cand1),await px.diff(shots.base2,shots.cand2)]};
      const floor=Math.max(row.baseNoise.maxDelta,row.candNoise.maxDelta);
      row.byteIdentical=row.baseVsCand.every(d=>d.bytesEqual);row.withinNoise=row.baseVsCand.every(d=>!d.sizeDiffers&&d.maxDelta<=floor);
      report.healthy.push({summary:row});console.log(JSON.stringify({engine,scene,byteIdentical:row.byteIdentical,withinNoise:row.withinNoise,baseVsCand:row.baseVsCand}));
    }
    for(const [variant,n] of FAULTS)for(const k of ['base','cand']){
      const c=await cell(browser,bases[k],{hash:SITE,instant:FAULT_INSTANT,hook:HOOK(n)});
      const samples=[];
      for(let i=0;i<13;i++){await c.page.waitForTimeout(1000);samples.push(await read(c.page));}
      const lefts=samples.map(s=>s.left),changes=lefts.slice(1).filter((v,i)=>v!==lefts[i]).length;
      const row={engine,variant,tree:k,days:c.days,pageErrors:c.pageErrors,consoleErrors:c.consoleErrors,leftTexts:lefts,leftChanges:changes,
        loadingPersists:lefts.every(v=>v==='Loading…'||v===''||v==null),final:samples[samples.length-1]};
      const shot=await c.page.locator('.c').screenshot(),file=`${engine}-fault-${variant}-${k}.png`;fs.writeFileSync(path.join(out,file),shot);row.screenshot=file;
      report.faults.push(row);console.log(JSON.stringify({engine,variant,tree:k,leftChanges:changes,pageErrors:c.pageErrors.length,consoleErrors:c.consoleErrors.length,first:lefts[0],last:lefts[lefts.length-1],moon:row.final.moon,faults:row.final.faults&&Object.keys(row.final.faults)}));
      await c.context.close();
    }
    await browser.close();
  }
  await px.close();
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,1)+'\n');
  for(const s of Object.values(servers))s.close();
})().catch(e=>{console.error(e);for(const s of Object.values(servers))s.close();process.exitCode=1;});
