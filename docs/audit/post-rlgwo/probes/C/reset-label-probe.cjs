"use strict";
// Effect-free: repo VM fixture; label (display-name) edit during Reset's apply await, then close.
const path=require("node:path");
const WT=process.argv[2];
const {fixture,deferred,drain}=require(path.join(WT,"tests","r000f-fixture.cjs"));
const detected={ok:true,cfg:{lat:40.7,lon:-74,label:"New York",method:"2",source:"coarse-ip"}};
(async()=>{
  const res={};
  for(const when of ["duringCoarse","duringApply"]){
    const f=fixture("settings"),gate=deferred(),original=f.sandbox.applyConfig;
    f.sandbox.applyConfig=async(...a)=>{await original(...a); await gate.promise;};
    f.click("set-reset");
    if(when==="duringCoarse"){ f.input("set-label","Home"); await f.resolve("coarse",0,detected); }
    else { await f.resolve("coarse",0,detected); f.input("set-label","Home"); }
    gate.resolve(); await drain();
    const runtimeBeforeClose={lat:f.run("lat"),label:f.run("label")};
    const formBeforeClose=f.tuple();
    f.click("setClose"); gate.resolve(); await drain();
    const s=f.sandbox.SalahConfig.loadLocal();
    res[when]={runtimeBeforeClose,formBeforeClose,appliedSeq:f.calls.applied.map(a=>({lat:a.cfg.lat,label:a.cfg.label,opts:a.opts})),saved:s&&{lat:s.lat,label:s.label}};
  }
  console.log(JSON.stringify(res,null,1));
})().catch(e=>{console.error(e);process.exitCode=1;});
