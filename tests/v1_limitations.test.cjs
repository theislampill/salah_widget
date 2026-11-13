"use strict";
// R0037 limitation witness for the FROZEN V1 copy (CF08, ISM-V1-006). It asserts that V1 still behaves as
// docs/V1_PRESERVATION.md "Known limitations of the frozen copy" documents: Reset claims "Local settings cleared."
// even when the browser refused the removal. This is a characterisation of a known defect, not a statement that
// the behaviour is correct, and it is not an expected-failure declaration. If V1 bytes are ever changed under owner
// authority (DG1-B), this witness must be revisited together with the limitation record.
// Effect-free: the exact v1/config.js runs in a VM with an in-memory storage double; the exact _resetLocal text is
// extracted from v1/index.html with its UI and network collaborators stubbed. No network, browser or file write.
const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const root=path.resolve(__dirname,"..");
const cfgSrc=fs.readFileSync(path.join(root,"v1/config.js"),"utf8");
const html=fs.readFileSync(path.join(root,"v1/index.html"),"utf8");
const KEY="salah_widget:v1:config:v1";
const saved=JSON.stringify({v:1,lat:24.47,lon:39.61,label:"Saved city",method:"4",school:"0",time:"24",units:"c",source:"manual"});

function resetSource(){
  const m=html.match(/async function _resetLocal\(\)\{[\s\S]*?\n\}\n/);
  assert.ok(m,"_resetLocal present in frozen v1/index.html");
  return m[0];
}
async function reset({removeThrows,coarseOk}){
  const data=new Map([[KEY,saved]]);
  const storage={
    getItem:k=>data.has(k)?data.get(k):null,
    setItem:(k,v)=>{data.set(k,String(v));},
    removeItem:k=>{ if(removeThrows){ const e=new Error("denied"); e.name="SecurityError"; throw e; } data.delete(k); },
  };
  const window={localStorage:storage};
  vm.runInNewContext(cfgSrc,{window,URLSearchParams});
  const real=window.SalahConfig, results=[];
  const SalahConfig=Object.assign({},real,{
    clearLocal:()=>{ const r=real.clearLocal(); results.push(r); return r; },
    coarseDetect:async()=>coarseOk?{ok:true,cfg:{area:"Fixture area",label:"Fixture"}}:{ok:false},
    applyHashPrefs:c=>c,
  });
  const statuses=[];
  const ctx={window:{SalahConfig},SalahConfig,_hashCfg:{},_storageErr:"prior-error",
    _setStatus:t=>statuses.push(t),applyConfig:async()=>{},_populateSettingsForm:()=>{}};
  vm.runInNewContext(resetSource()+"\n;globalThis.__r=_resetLocal();",ctx);
  await ctx.__r;
  // VM-realm objects are compared as plain data.
  return {clear:JSON.parse(JSON.stringify(results[0])),stored:data.get(KEY),storageErr:ctx._storageErr,statuses,reload:real.loadLocal()};
}

test("R0037 V1 limitation CF08: Reset claims success although removal was refused (coarse lookup fails)",async()=>{
  const r=await reset({removeThrows:true,coarseOk:false});
  assert.deepEqual(r.clear,{ok:false,error:"SecurityError"},"clearLocal reports the refusal");
  assert.equal(r.stored,saved,"the saved record survives");
  assert.equal(r.storageErr,null,"the storage error is cleared anyway");
  assert.deepEqual(r.statuses,["Local settings cleared.","Local settings cleared — enter your location."]);
  assert.equal(r.reload&&r.reload.label,"Saved city","the surviving record is restored on reload");
});
test("R0037 V1 limitation CF08: Reset claims success although removal was refused (coarse lookup succeeds)",async()=>{
  const r=await reset({removeThrows:true,coarseOk:true});
  assert.equal(r.clear.ok,false); assert.equal(r.stored,saved);
  assert.deepEqual(r.statuses,["Local settings cleared.","Reset — using estimated area: Fixture area"]);
});
test("R0037 V1 limitation CF08 control: a permitted removal really removes the record",async()=>{
  const r=await reset({removeThrows:false,coarseOk:false});
  assert.deepEqual(r.clear,{ok:true}); assert.equal(r.stored,undefined); assert.equal(r.reload,null);
  assert.deepEqual(r.statuses,["Local settings cleared.","Local settings cleared — enter your location."]);
});
