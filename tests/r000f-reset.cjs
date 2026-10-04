"use strict";
// Held-out review regression: reset coordinates remain current while later
// preference edits still own their fields and their pending close-save state.
const assert=require("node:assert/strict");
const {fixture,deferred,drain}=require("./r000f-fixture.cjs");
const ref=process.argv.includes("--ref")?process.argv[process.argv.indexOf("--ref")+1]:undefined;
const mutant=process.argv.includes("--mutant")?process.argv[process.argv.indexOf("--mutant")+1]:undefined;
const detected={ok:true,cfg:{lat:40.7,lon:-74,label:"New York",method:"2",source:"coarse-ip"}};
function make() {
  const mutate=source=>mutant==="preapply"?source.replace("Object.assign(c,_newerSetPrefs(prefOwner));","")
    :mutant==="restore"?source.replace('Object.entries(prefs).forEach(([key,value])=>{ _byId(_SET_PREF_IDS[key]).value=value; });',"")
    :mutant==="dirty"?source.replace("_setDirty=Object.keys(prefs).length>0;","_setDirty=false;"):source;
  return fixture("settings",{ref,mutate:mutant?mutate:undefined});
}
const cases=[],test=(name,body)=>cases.push({name,body});
test("reset preserves newer method in applied config, form and close save",async()=>{
  const f=make(); f.click("set-reset"); f.input("set-method","3","change"); await f.resolve("coarse",0,detected);
  assert.equal(f.tuple()[1],"40.7"); assert.equal(f.tuple()[3],"3"); assert.equal(f.calls.applied[0].cfg.method,"3"); assert.equal(f.run("_setDirty"),true);
  f.click("setClose"); assert.equal(f.sandbox.SalahConfig.loadLocal().method,"3");
});
test("reset preserves every newer display preference without cancelling coordinates",async()=>{
  const f=make(); f.click("set-reset");
  f.input("set-school","1","change"); f.input("set-units","c","change"); f.input("set-time","12","change"); f.input("set-appearance","contrast","change"); f.input("set-datefmt","DD/MM/YYYY");
  await f.resolve("coarse",0,detected);
  assert.equal(f.tuple()[1],"40.7");
  assert.deepEqual(["set-school","set-units","set-time","set-appearance","set-datefmt"].map(id=>f.elements.get(id).value),["1","c","12","contrast","DD/MM/YYYY"]);
  assert.equal(f.run("_setDirty"),true); const applied=f.calls.applied[0].cfg;
  assert.deepEqual([applied.school,applied.units,applied.time,applied.appearance,applied.datefmt],["1","c","12","contrast","DD/MM/YYYY"]);
  f.click("setClose"); const saved=f.sandbox.SalahConfig.loadLocal(); assert.deepEqual([saved.school,saved.units,saved.time,saved.appearance,saved.datefmt],["1","c","12","contrast","DD/MM/YYYY"]);
});
test("reset recognises date preset change as ownership of the format box",async()=>{
  const f=make(); f.click("set-reset"); f.input("set-datefmt-preset","DD MMMM YYYY","change"); await f.resolve("coarse",0,detected);
  assert.equal(f.elements.get("set-datefmt").value,"DD MMMM YYYY"); assert.equal(f.elements.get("set-datefmt-preset").value,"DD MMMM YYYY"); assert.equal(f.run("_setDirty"),true);
});
test("reset retains preference edits made during the apply await",async()=>{
  const f=make(),gate=deferred(),original=f.sandbox.applyConfig;
  f.sandbox.applyConfig=async(...args)=>{await original(...args);await gate.promise;};
  f.click("set-reset"); await f.resolve("coarse",0,detected);
  f.input("set-method","3","change"); f.input("set-units","c","change"); f.input("set-time","12","change"); f.input("set-datefmt","DD/MM/YYYY");
  gate.resolve(); await drain();
  assert.deepEqual(f.tuple(),["New York","40.7","-74","3"]);
  assert.deepEqual(["set-units","set-time","set-datefmt"].map(id=>f.elements.get(id).value),["c","12","DD/MM/YYYY"]);
  assert.equal(f.run("_setDirty"),true); f.click("setClose"); assert.equal(f.sandbox.SalahConfig.loadLocal().method,"3");
});
test("reset protects A to B to A preference edits and their dirty state",async()=>{
  const f=make(); f.click("set-reset"); f.input("set-method","3","change"); f.input("set-method","4","change"); await f.resolve("coarse",0,detected);
  assert.equal(f.tuple()[3],"4"); assert.equal(f.run("_setDirty"),true); assert.equal(f.calls.applied[0].cfg.method,"4");
});
test("positive: reset without newer preference edits still restores defaults",async()=>{
  const f=make(); f.input("set-method","3","change"); f.input("set-units","c","change"); f.click("set-reset"); await f.resolve("coarse",0,detected);
  assert.deepEqual(f.tuple(),["New York","40.7","-74","2"]); assert.equal(f.elements.get("set-units").value,"f"); assert.equal(f.run("_setDirty"),false); assert.equal(f.storage.size,0);
});
test("location edit during apply still invalidates the entire reset continuation",async()=>{
  const f=make(),gate=deferred(),original=f.sandbox.applyConfig;
  f.sandbox.applyConfig=async(...args)=>{await original(...args);await gate.promise;};
  f.click("set-reset"); await f.resolve("coarse",0,detected); f.input("set-lat","30"); f.input("set-lon","31"); const before=f.snapshot();
  gate.resolve(); await drain(); assert.equal(f.snapshot(),before);
});
test("close and reopen during apply still invalidate the reset continuation",async()=>{
  const f=make(),gate=deferred(),original=f.sandbox.applyConfig;
  f.sandbox.applyConfig=async(...args)=>{await original(...args);await gate.promise;};
  f.click("set-reset"); await f.resolve("coarse",0,detected); f.click("setClose"); f.buckle.dispatch("click"); const before=f.snapshot();
  gate.resolve(); await drain(); assert.equal(f.snapshot(),before);
});
test("failed current reset retains newer preferences for manual close save",async()=>{
  const f=make(); f.click("set-reset"); f.input("set-method","3","change"); await f.reject("coarse",0);
  assert.equal(f.tuple()[3],"3"); assert.equal(f.run("_setDirty"),true); f.click("setClose"); assert.equal(f.sandbox.SalahConfig.loadLocal().method,"3");
});
async function main(){let failed=0;for(const c of cases){try{await c.body();console.log("PASS",c.name);}catch(e){failed++;console.error("FAIL",c.name,"\n",e.stack);}}
  console.log(JSON.stringify({cases:cases.length,passed:cases.length-failed,failed,ref:ref||"working-tree",mutant:mutant||null,native:"NOT_RUN"}));process.exitCode=failed?1:0;}
main();
