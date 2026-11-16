'use strict';
// Moon-reuse feasibility audit (2026-11-16): refined-Moon byte determinism and per-step display error.
// Every browser goes through iso.cjs (proxy + resolver rules + context '**/*' route installed before navigation;
// env.finish() throws if any non-loopback request was allowed). Usage:
//   node determinism.cjs <repoRoot> <outJson> <bytesDir> [engines=chromium,firefox,webkit]
const fs=require('node:fs'),path=require('node:path');
const {createEnv,launch}=require('./iso.cjs');
const [root,outFile,bytesDir,enginesArg]=process.argv.slice(2);
const ENGINES=(enginesArg||'chromium,firefox,webkit').split(',');
const SC={
  C:{name:'C',f:.15,waxing:true,sun:[-0.7000000000000002,0.7141428428542849,0]},
  H:{name:'H',f:.5,waxing:false,sun:[6.123233995736766e-17,-1,0]},
  G:{name:'G',f:.8,waxing:true,sun:[0.6000000000000001,0.7999999999999999,0]},
  F:{name:'F',f:.98,waxing:false,sun:[0.96,-0.28000000000000014,0]}};
const PAGE='/docs/audit/moon-refinement-reuse-20261116/harness/moonprobe.html';
const log=(...a)=>console.log(new Date().toISOString(),...a);
async function openProbe(L,env){
  const page=await L.context.newPage();page.on('pageerror',e=>log('pageerror',String(e)));
  await page.goto(`http://127.0.0.1:${env.origins.ports['127.0.0.1']}${PAGE}`,{waitUntil:'load'});
  await page.waitForFunction(()=>window.probeReady===true);return page;
}
async function run(page,variant,sceneName,label,opts={}){
  const t=Date.now();
  const r=await page.evaluate(async([v,sc,o,reuse])=>{if(!reuse||!window.__h||window.__h.variant!==v)window.__h=await probe.boot(v);const r=await probe.render(window.__h,sc,o);r.bootMs=window.__h.bootMs;r.workerSourceSha256=window.__h.sourceSha;return r;},[variant,SC[sceneName],{exportBytes:!!opts.exportBytes},!!opts.reuse]);
  r.label=label;r.wallMs=Date.now()-t;
  if(r.bytes){fs.mkdirSync(bytesDir,{recursive:true});for(const [k,v] of Object.entries(r.bytes))fs.writeFileSync(path.join(bytesDir,`${opts.engine}-${sceneName}-${label}-${k}.b64`),v);delete r.bytes;}
  log(opts.engine,label,variant,sceneName,Math.round(r.ms)+'ms',r.hashes.rgba.slice(0,12),r.hashes.surfaceLinear.slice(0,12));
  return r;
}
(async()=>{
  const out=fs.existsSync(outFile)?JSON.parse(fs.readFileSync(outFile,'utf8')):{};
  for(const engine of ENGINES){
    const env=await createEnv({root});const rec={engine,runs:[],started:new Date().toISOString()};
    try{
      // Browser 1, tab 1: three sequential renders of G in ONE worker (repeat path), then C (camera reused).
      let L=await launch(env,{engine,mode:'route'});
      let p=await openProbe(L,env);rec.info=await p.evaluate(()=>probe.info());rec.math=await p.evaluate(()=>probe.mathFingerprint());
      rec.runs.push(await run(p,'product','G','b1t1-first',{engine,exportBytes:true}));
      rec.runs.push(await run(p,'product','G','b1t1-repeat2',{engine,reuse:true}));
      rec.runs.push(await run(p,'product','G','b1t1-repeat3',{engine,reuse:true}));
      rec.runs.push(await run(p,'product','C','b1t1-C-after-G',{engine,reuse:true,exportBytes:true}));
      // Browser 1, tab 2: fresh worker, G.
      const p2=await openProbe(L,env);rec.runs.push(await run(p2,'product','G','b1t2-fresh',{engine}));
      await L.close();
      // Browser 2: fresh browser process, G; then the stepwise variant.
      L=await launch(env,{engine,mode:'route'});p=await openProbe(L,env);
      rec.runs.push(await run(p,'product','G','b2t1-fresh',{engine}));
      const stepScenes=engine==='chromium'?['C','H','G','F']:['G'];
      for(const s of stepScenes){const q=await openProbe(L,env);rec.runs.push(await run(q,'stepwise',s,'b2-stepwise-'+s,{engine}));await q.close();}
      if(engine==='chromium'){
        for(const k of [1,2]){const q=await openProbe(L,env);rec.runs.push(await run(q,'shards2','G','b2-shards2-'+k,{engine}));await q.close();}
      }
      await L.close();
      if(engine==='chromium'){
        L=await launch(env,{engine,mode:'route',deviceScaleFactor:2});
        for(const k of [1,2]){const q=await openProbe(L,env);rec.runs.push(await run(q,'product','G','b3-dpr2-'+k,{engine}));if(k===1)rec.infoDpr2=await q.evaluate(()=>probe.info());await q.close();}
        await L.close();
      }
    }catch(e){rec.error=String(e&&e.stack||e);log('ERROR',engine,rec.error);}
    rec.isolation=env.finish();rec.finished=new Date().toISOString();
    log(engine,'isolation',JSON.stringify(rec.isolation.totalRequests),'allowedExternal',rec.isolation.allowedExternal);
    out[engine]=rec;fs.writeFileSync(outFile,JSON.stringify(out,null,1));
  }
})().catch(e=>{console.error(e);process.exit(1);});
