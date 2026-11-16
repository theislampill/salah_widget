'use strict';
// Moon-reuse audit, Job 3 drafting-era RED witness (VM, no browser, no network).
// Reuses the rig() of moon/tests/host.test.cjs (extracted read-only from the file) to drive the UNMODIFIED
// moon/src/moon-native.mjs + moon-precision.mjs with the product's own ephemeris (moonIllum from
// src/native/index.html), stepping the native fraction once per simulated minute as the native host does
// (index.html L3841). A fake worker answers every render with a result after <jobS> seconds.
// Usage: node defect-vm.cjs <repoRoot> <startISO> <minutes> <jobS> [up=1]
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const [root,startISO,minutes,jobS,upArg]=process.argv.slice(2);
const testSrc=fs.readFileSync(path.join(root,'moon/tests/host.test.cjs'),'utf8');
const a=testSrc.indexOf('function rig('),b=testSrc.indexOf('\n}\n',a)+3;
const rig=new Function('require','__dirname','process','fs','vm','path','crypto','const src=process.env.SALAH_MOON_SOURCE_DIR;'+testSrc.slice(a,b)+';return rig;')(require,path.join(root,'moon/tests'),{env:{SALAH_MOON_SOURCE_DIR:path.join(root,'moon/src')}},fs,vm,path,crypto);
const html=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');const s0=html.indexOf('const _RAD=Math.PI/180'),s1=html.indexOf('// Galactic centre',s0);
const eph={Math,Date};vm.createContext(eph);vm.runInContext(html.slice(s0,s1)+';this.moonIllum=moonIllum;',eph);
const r=rig({initial:true,diameter:109});const start=Date.parse(startISO);
Object.assign(r.state,{timeScale:1,up:upArg==null?1:+upArg,utcMs:start});
const il0=eph.moonIllum(new Date(start));r.state.fraction=il0.fraction;r.state.waxing=il0.waxing;
const worker=r.workers.at(-1);worker.emit({kind:'ready'});
const rt=r.w.SalahMoonRuntime;const log=[];let pendingReply=null,lastRenderId=null;
const tick=dtMs=>{r.advance(dtMs);r.state.utcMs+=dtMs;};
for(let m=0;m<+minutes;m++){
  // the native snapshot refreshes at the minute boundary
  const il=eph.moonIllum(new Date(start+m*60000));r.state.fraction=il.fraction;r.state.waxing=il.waxing;
  for(let q=0;q<240;q++){ // 4 Hz polls within the minute
    rt.request();const req=r.request(); // request() = the native paint hook (poll without force)
    if(req&&req.id!==lastRenderId){lastRenderId=req.id;pendingReply={id:req.id,at:m*60000+q*250+(+jobS)*1000, // absolute simulated time (erratum: was minute-relative at 153c2066)
      msg:r.response('result')};log.push({minute:m,event:'render',id:req.id});}
    if(pendingReply&&m*60000+q*250>=pendingReply.at&&r.request()?.id===pendingReply.id){pendingReply.msg.diagnostics={kernel:'metric-radial-terrain-wasm-mb1',quality:{status:'empirical-adaptive'}};worker.emit(pendingReply.msg);log.push({minute:m,event:'result',id:pendingReply.id});pendingReply=null;}
    tick(250);
  }
}
const st=rt.state;
const out={startISO,minutes:+minutes,jobSeconds:+jobS,up:r.state.up,renders:log.filter(x=>x.event==='render').length,results:log.filter(x=>x.event==='result').length,
  hostFallbacks:r.fallbacks,initialRenders:r.initialRenders,cancelled:st.cancelled,reason:st.reason,visibleSourceAtEnd:st.visibleSource,status:st.status};
console.log(JSON.stringify(out));if(process.env.VMDEBUG)console.log(JSON.stringify(log.filter(x=>x.minute>=2&&x.minute<4)));
