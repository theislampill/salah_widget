'use strict';
// Moon-reuse feasibility audit (2026-11-16): storage availability/integrity for a refined-Moon-sized entry, three
// engines, normal (non-persistent, "incognito-like" fresh) context and opaque-origin iframe. Through iso.cjs.
// Usage: node storage.cjs <repoRoot> <outJson> <bytes>
const fs=require('node:fs');
const {createEnv,launch}=require('./iso.cjs');
const [root,outFile,bytes]=process.argv.slice(2);
(async()=>{const out={};
  for(const engine of ['chromium','firefox','webkit']){
    const env=await createEnv({root});const rec={};
    try{const L=await launch(env,{engine,mode:'route'});const p=await L.context.newPage();
      await p.goto(`http://127.0.0.1:${env.origins.ports['127.0.0.1']}/docs/audit/moon-refinement-reuse-20261116/harness/storageprobe.html`);
      await p.waitForFunction(()=>window.storageReady===true);
      rec.normal=await p.evaluate(b=>storageProbe.all(b),+bytes);
      rec.opaqueIframe=await p.evaluate(()=>opaqueProbe());
      await L.close();
    }catch(e){rec.error=String(e&&e.stack||e);}
    rec.isolation=env.finish();out[engine]=rec;console.log(engine,JSON.stringify(rec.normal&&{idb:rec.normal.indexedDB,cache:rec.normal.cacheApi,opfs:rec.normal.opfs,quota:rec.normal.estimate&&rec.normal.estimate.quota}),JSON.stringify(rec.opaqueIframe),'allowed',rec.isolation.allowedExternal);
  }
  fs.writeFileSync(outFile,JSON.stringify(out,null,1));
})().catch(e=>{console.error(e);process.exit(1);});
