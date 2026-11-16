'use strict';
// Moon-reuse feasibility audit (2026-11-16), supplement to determinism.cjs (Chromium only):
//  (1) two tabs refining the same scene CONCURRENTLY (scheduling/contention), hashes compared;
//  (2) stepwise per-step error with PREMULTIPLIED (displayed-over-black) texture metrics, because straight-alpha
//      colour of near-transparent limb pixels is ill-conditioned (prefix-sum division by a tiny coverage).
// Every browser goes through iso.cjs. Usage: node supplement.cjs <repoRoot> <outJson>
const fs=require('node:fs');
const {createEnv,launch}=require('./iso.cjs');
const [root,outFile]=process.argv.slice(2);
const SC={C:{name:'C',f:.15,waxing:true,sun:[-0.7000000000000002,0.7141428428542849,0]},G:{name:'G',f:.8,waxing:true,sun:[0.6000000000000001,0.7999999999999999,0]}};
const PAGE='/docs/audit/moon-refinement-reuse-20261116/harness/moonprobe.html';
(async()=>{
  const env=await createEnv({root});const out={engine:'chromium',concurrent:[],stepwise:[]};
  try{
    const L=await launch(env,{engine:'chromium',mode:'route'});
    const open=async()=>{const p=await L.context.newPage();await p.goto(`http://127.0.0.1:${env.origins.ports['127.0.0.1']}${PAGE}`);await p.waitForFunction(()=>window.probeReady===true);return p;};
    const [a,b]=[await open(),await open()];
    const go=(p,v,s)=>p.evaluate(async([v,sc])=>{const h=await probe.boot(v);const r=await probe.render(h,sc);return {ms:r.ms,hashes:r.hashes,steps:r.steps};},[v,SC[s]]);
    const [ra,rb]=await Promise.all([go(a,'product','G'),go(b,'product','G')]);
    out.concurrent.push({tab:'a',...ra},{tab:'b',...rb});console.log('concurrent',Math.round(ra.ms),Math.round(rb.ms),ra.hashes.rgba===rb.hashes.rgba&&ra.hashes.surfaceLinear===rb.hashes.surfaceLinear);
    for(const s of ['G','C']){const p=await open();const r=await go(p,'stepwise',s);out.stepwise.push({scene:s,ms:r.ms,hashes:r.hashes,steps:r.steps});await p.close();console.log('stepwise',s,Math.round(r.ms));}
    await L.close();
  }catch(e){out.error=String(e&&e.stack||e);console.error(out.error);}
  out.isolation=env.finish();console.log('isolation',JSON.stringify(out.isolation.totalRequests),'allowed',out.isolation.allowedExternal);
  fs.writeFileSync(outFile,JSON.stringify(out,null,1));
})().catch(e=>{console.error(e);process.exit(1);});
