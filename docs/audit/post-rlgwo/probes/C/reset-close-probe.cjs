"use strict";
// Effect-free probe: uses the repo's own VM fixture (reads worktree files, no network, no writes).
const path=require("node:path");
const WT=process.argv[2];
const {fixture,drain}=require(path.join(WT,"tests","r000f-fixture.cjs"));
const detected={ok:true,cfg:{lat:40.7,lon:-74,label:"New York",method:"2",source:"coarse-ip"}};
const out={};
(async()=>{
  // P1: pre-reset edit, Reset (clear ok), close while coarse detection pending.
  { const f=fixture("settings");
    f.input("set-method","3","change");
    f.click("set-reset");
    const afterReset={storage:[...f.storage.keys()],status:f.elements.get("set-status").textContent};
    f.click("setClose");
    const afterClose={storage:f.sandbox.SalahConfig.loadLocal(),applied:f.calls.applied.map(a=>({lat:a.cfg.lat,method:a.cfg.method,opts:a.opts})),status:f.elements.get("set-status").textContent};
    await f.resolve("coarse",0,detected);
    out.P1={afterReset,afterClose:{saved:afterClose.storage&&{lat:afterClose.storage.lat,method:afterClose.storage.method},applied:afterClose.applied,status:afterClose.status},
      afterCoarse:{applied:f.calls.applied.length,saved:(s=>s&&{lat:s.lat,method:s.method})(f.sandbox.SalahConfig.loadLocal())}};
  }
  // P2: no pre-reset edit, Reset, close while pending: runtime keeps old config, storage empty.
  { const f=fixture("settings");
    f.click("set-reset"); f.click("setClose");
    await f.resolve("coarse",0,detected);
    out.P2={applied:f.calls.applied.length,storageKeys:[...f.storage.keys()],runtimeLat:f.run("lat"),status:f.elements.get("set-status").textContent};
  }
  // P3 builder: local mode coordinate edit still schedules a BigDataCloud reverse lookup though export omits coordinates.
  { const f=fixture("builder");
    await f.resolve("coarse",0,{ok:false});
    f.click("mode-local");
    const before=f.calls.reverse.length, code0=f.elements.get("code").value, src0=f.elements.get("pv").src;
    f.input("lat","25"); await f.advance(800);
    out.P3={reverseRequestsAdded:f.calls.reverse.length-before,reverseUrl:f.calls.reverse.at(-1),exportUnchanged:f.elements.get("code").value===code0,previewUnchanged:f.elements.get("pv").src===src0};
  }
  console.log(JSON.stringify(out,null,1));
})().catch(e=>{console.error(e);process.exitCode=1;});
