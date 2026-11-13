'use strict';
// R002D D-06 / D-13 / D-15 native recipe (issue 94). Serves an unchanged generated tree from --root on
// 127.0.0.1, stubs the prayer provider (meta.timezone Asia/Riyadh) and aborts every other non-local request
// (weather, radar, fonts, geocoding: unavailable). No real provider is contacted. Browser zone is forced to
// America/Los_Angeles and a mocked clock is installed at the cell instant and left running.
//
// Discriminators (exact, counted in the page through init-script hooks installed before any product script):
//   sceneBegins     - DOMTokenList.add calls carrying "sky-pending" (only beginSkyScene adds it; one begin =
//                     one cloud-receipt withdrawal "scene superseded" in the same function)
//   moonInvalidations / initialDocumentInvalidations - SalahMoonRuntime.invalidate calls (wrapped on assignment)
//   initialHeadRetirements - SalahMoonRuntime.finishInitialDocument calls
// Sampled every 250 ms for 8 s: cloud publication receipts (qaState().clouds.publication), Moon runtime epoch,
// refined-sky status, and per animation frame the presented sky-pending / sky-initializing / moon-ready classes.
//
// Cells per engine: wall-clock builder-shaped embed (no tz; hint America/New_York != provider Asia/Riyadh)
// and control (tz=Asia/Riyadh = provider) at 2026-09-07T22:00Z (civil days differ), each run TWICE for the
// run-to-run pixel noise floor; a frozen hint=provider scene (simTime=21:30, no timeScale) run twice; and a
// rejected hint (tz=Bogus/Zone) once.
//
// Usage: node tools/qa/run_r002d_native.cjs --root <tree> --out <fresh dir> [--engines chromium,firefox,webkit]
//        [--playwright <path to the playwright package>]
//        node tools/qa/run_r002d_native.cjs --compare <main report.json> <branch report.json> --out <fresh dir>
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const argv=process.argv.slice(2),args={};
for(let i=0;i<argv.length;i++)if(argv[i].startsWith('--')){const k=argv[i].slice(2),v=[];while(argv[i+1]&&!argv[i+1].startsWith('--'))v.push(argv[++i]);args[k]=v.length>1?v:v[0];}
const {chromium,firefox,webkit}=require(args.playwright||'playwright');
const ENG={chromium,firefox,webkit};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const out=path.resolve(args.out||'r002d-native-out');fs.mkdirSync(out,{recursive:false});

async function pixelDiffer(){
  const browser=await chromium.launch({headless:true}),page=await browser.newPage();
  const diff=(a,b)=>page.evaluate(async([a,b])=>{const load=async u=>{const i=new Image();i.src=u;await i.decode();const c=new OffscreenCanvas(i.width,i.height),x=c.getContext('2d');x.drawImage(i,0,0);return x.getImageData(0,0,i.width,i.height);};
    const A=await load(a),B=await load(b);if(A.width!==B.width||A.height!==B.height)return {sizeDiffers:true};let n=0,max=0;
    for(let i=0;i<A.data.length;i+=4){let d=0;for(let k=0;k<4;k++)d=Math.max(d,Math.abs(A.data[i+k]-B.data[i+k]));if(d){n++;max=Math.max(max,d);}}return {differingPixels:n,of:A.width*A.height,maxDelta:max};},
    ['data:image/png;base64,'+fs.readFileSync(a).toString('base64'),'data:image/png;base64,'+fs.readFileSync(b).toString('base64')]);
  return {diff:async(a,b)=>({...(await diff(a,b)),bytesEqual:sha(fs.readFileSync(a))===sha(fs.readFileSync(b))}),close:()=>browser.close()};
}

if(args.compare){
  // D-15: hint=provider cells, main vs branch, read against each tree's own run-to-run noise floor.
  (async()=>{
    const [ma,br]=args.compare.map(p=>path.resolve(p)),M=JSON.parse(fs.readFileSync(ma)),B=JSON.parse(fs.readFileSync(br)),px=await pixelDiffer();
    const shot=(rep,dir,e,cell,run)=>path.join(path.dirname(dir),rep.cells.find(c=>c.engine===e&&c.cell===cell&&c.run===run).screenshot.file);
    const result={main:M.inputs,branch:B.inputs,engines:B.engines,pairs:[]};
    for(const e of Object.keys(B.engines))for(const cell of ['control','frozen-control']){
      const r={engine:e,cell,mainNoise:await px.diff(shot(M,ma,e,cell,1),shot(M,ma,e,cell,2)),branchNoise:await px.diff(shot(B,br,e,cell,1),shot(B,br,e,cell,2)),
        mainVsBranch:[await px.diff(shot(M,ma,e,cell,1),shot(B,br,e,cell,1)),await px.diff(shot(M,ma,e,cell,2),shot(B,br,e,cell,2))]};
      const floor=Math.max(r.mainNoise.maxDelta,r.branchNoise.maxDelta),floorPx=Math.max(r.mainNoise.differingPixels,r.branchNoise.differingPixels);
      r.withinNoise=r.mainVsBranch.every(d=>d.maxDelta<=floor&&d.differingPixels<=Math.max(floorPx,0)*2);
      r.byteIdentical=r.mainVsBranch.every(d=>d.bytesEqual);
      result.pairs.push(r);
    }
    await px.close();fs.writeFileSync(path.join(out,'compare.json'),JSON.stringify(result,null,1)+'\n');console.log(JSON.stringify(result.pairs,null,1));
  })().catch(e=>{console.error(e);process.exitCode=1;});
  return;
}

const root=path.resolve(args.root||path.join(__dirname,'..','..'));
const engines=(args.engines||'chromium,firefox,webkit').split(',');
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
const SITE='#lat=24.47&lon=39.61&label=Madinah&method=4&seed=1';
const CELLS=[['builder',SITE,2],['control',SITE+'&tz=Asia%2FRiyadh',2],['frozen-control',SITE+'&tz=Asia%2FRiyadh&simTime=21:30',2],['rejected',SITE+'&tz=Bogus%2FZone',1]];
const INSTANT='2026-09-07T22:00:00Z';
const HOOKS=`(()=>{const L=window.__r002d={t0:performance.now(),begins:[],inv:[],finish:[],frames:[],samples:[]};const at=()=>Math.round(performance.now()-L.t0);
 const add=DOMTokenList.prototype.add;DOMTokenList.prototype.add=function(...a){if(a.includes('sky-pending'))L.begins.push(at());return add.apply(this,a);};
 let rt;Object.defineProperty(window,'SalahMoonRuntime',{configurable:true,enumerable:true,get(){return rt;},set(v){
  if(v&&typeof v.invalidate==='function'&&!v.__r002dWrapped){const inv=v.invalidate,fin=v.finishInitialDocument;
   v.invalidate=function(r,o){L.inv.push([at(),String(r),!!(o&&o.initialDocument)]);return inv.call(this,r,o);};
   if(typeof fin==='function')v.finishInitialDocument=function(){L.finish.push(at());return fin.call(this);};
   Object.defineProperty(v,'__r002dWrapped',{value:true});}
  rt=v;}});
 const start=()=>{const c=document.querySelector('.c');if(!c)return requestAnimationFrame(start);let prev='';
  const tick=()=>{const s=['sky-pending','sky-initializing','moon-ready'].filter(k=>c.classList.contains(k)).join(' ');if(s!==prev){L.frames.push([at(),s]);prev=s;}if(at()<8000)requestAnimationFrame(tick);};requestAnimationFrame(tick);
  const sample=()=>{let pub=null,epoch=null,refined=null;try{const p=window.qaState?.().clouds?.publication;pub=p?[p.revision,p.state,p.reason]:null;}catch(e){}
   try{epoch=window.SalahMoonRuntime?.state?.epoch??null;}catch(e){}try{const s=window.SalahRealSky?.state;refined=s?[s.status,s.lifecycle?.status??null]:null;}catch(e){}
   const last=L.samples[L.samples.length-1],row=[at(),pub,epoch,refined];if(!last||JSON.stringify(last.slice(1))!==JSON.stringify(row.slice(1)))L.samples.push(row);if(at()<8000)setTimeout(sample,250);};sample();};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();})();`;
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
  const report={scope:'R002D native discriminators; stubbed prayer provider (Asia/Riyadh); every other non-local request aborted; mocked running clock at '+INSTANT,
    inputs:Object.fromEntries(['index.html','config.js'].map(f=>[f,sha(fs.readFileSync(path.join(root,f)))])),engines:{},cells:[],summary:[]};
  for(const engine of engines){
    const browser=await ENG[engine].launch({headless:true});report.engines[engine]=browser.version();
    for(const [cell,hash,runs] of CELLS)for(let run=1;run<=runs;run++){
      const context=await browser.newContext({viewport:{width:325,height:530},deviceScaleFactor:1,timezoneId:'America/Los_Angeles',locale:'en-US',reducedMotion:'reduce'});
      const days=[];
      await context.route('**/*',route=>{const u=route.request().url();
        if(u.startsWith(base))return route.continue();
        const m=/api\.aladhan\.com\/v1\/timings\/([^?]*)/.exec(u);
        if(m){days.push(m[1]);if(/^\d{2}-\d{2}-\d{4}$/.test(m[1]))return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,status:'OK',data:record(m[1],'Asia/Riyadh')})});}
        return route.abort();});
      const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));
      await page.clock.install({time:new Date(INSTANT)});
      await page.addInitScript(HOOKS);
      await page.goto(base+'/index.html'+hash,{waitUntil:'domcontentloaded'});
      await page.waitForFunction(()=>{try{return !!today&&_loopStarted}catch(e){return false}},null,{timeout:15000}).catch(()=>{});
      await page.waitForFunction(()=>performance.now()-window.__r002d.t0>8200,null,{timeout:30000}).catch(()=>{});
      const s=await page.evaluate(()=>{const L=window.__r002d;let zone=null;try{zone=window.qaState().zone??null}catch(e){}
        return {tz,cacheTz:_cacheTz,sceneKey:_skySceneKey,today:!!today,zone,sceneBegins:L.begins.length,beginsAt:L.begins,moonInvalidations:L.inv.length,
          initialDocumentInvalidations:L.inv.filter(x=>x[2]).length,invalidations:L.inv,initialHeadRetirements:L.finish.length,frames:L.frames,samples:L.samples,
          sceneSupersededReceipts:[...new Set(L.samples.filter(x=>x[1]&&x[1][2]==='scene superseded').map(x=>x[1][0]))].length,
          epochs:[...new Set(L.samples.map(x=>x[2]))],rows:[...document.querySelectorAll('.times .p')].map(p=>p.textContent)};});
      const shot=await page.locator('.c').screenshot(),file=`${engine}-${cell}-${run}.png`;fs.writeFileSync(path.join(out,file),shot);
      report.cells.push({engine,cell,run,hash,days,errors,...s,screenshot:{file,sha256:sha(shot)}});
      await context.close();
    }
    await browser.close();
  }
  const px=await pixelDiffer();
  for(const engine of engines){
    const get=(cell,run=1)=>report.cells.find(c=>c.engine===engine&&c.cell===cell&&c.run===run);
    const f=(cell,run)=>path.join(out,get(cell,run).screenshot.file);
    const pick=c=>({sceneBegins:c.sceneBegins,moonInvalidations:c.moonInvalidations,initialHeadRetirements:c.initialHeadRetirements,sceneSupersededReceiptsSampled:c.sceneSupersededReceipts,epochs:c.epochs.length,zone:c.tz,days:c.days});
    report.summary.push({engine,builder:[pick(get('builder',1)),pick(get('builder',2))],control:[pick(get('control',1)),pick(get('control',2))],rejected:pick(get('rejected')),
      builderEqualsControlCounts:['sceneBegins','moonInvalidations','initialHeadRetirements'].every(k=>[1,2].every(r=>get('builder',r)[k]===get('control',r)[k])),
      noise:{builder:await px.diff(f('builder',1),f('builder',2)),control:await px.diff(f('control',1),f('control',2)),frozenControl:await px.diff(f('frozen-control',1),f('frozen-control',2))},
      builderVsControl:await px.diff(f('builder',1),f('control',1)),rowsEqual:JSON.stringify(get('builder').rows)===JSON.stringify(get('control').rows)});
  }
  await px.close();
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,1)+'\n');
  console.log(JSON.stringify({inputs:report.inputs,engines:report.engines,summary:report.summary},null,1));
  server.close();
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
