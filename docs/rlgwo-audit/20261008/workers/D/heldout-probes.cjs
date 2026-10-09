"use strict";
const assert=require("node:assert/strict"),crypto=require("node:crypto"),fs=require("node:fs"),path=require("node:path");
const sourceRoot="C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget";
const auditRoot="C:/Users/theis/Documents/Codex/pr42-rlgwo-closure-20261008";
const target="18ff14860ff41c084b1db5f396bb62aa9c22b1be";
const {fixture,drain,readSource}=require(path.join(sourceRoot,"tests/r000f-fixture.cjs"));
const {widget}=require(path.join(sourceRoot,"tests/r0011-fixture.cjs"));
const london={lat:51.5,lon:-.12,name:"London",norm:"London",cc:"gb"};
const cases=[],test=(name,run)=>cases.push({name,run});
test("all six complete immutable issue bodies match their initial SHA256",()=>{
  for(const n of [15,16,17,18,31,35]){
    const p=JSON.parse(fs.readFileSync(path.join(auditRoot,"issues",`${n}.json`),"utf8"));
    assert.equal(crypto.createHash("sha256").update(p.issue.body,"utf8").digest("hex"),p.contract.bodySha256);
    assert.equal(p.comments.length,0);
  }
});
test("obsolete builder coarse failure cannot replace accepted London outputs",async()=>{
  const f=fixture("builder",{ref:target});f.input("label","London");f.key("label","Enter");await f.resolve("search",0,[london]);
  const before=f.snapshot();await f.reject("coarse",0);assert.equal(f.snapshot(),before);
});
test("obsolete builder reverse failure cannot replace newer reverse outputs",async()=>{
  const f=fixture("builder",{ref:target});f.input("lat","40.7");f.input("lon","-74");await f.advance(700);
  f.input("lat","24.47");f.input("lon","39.61");await f.advance(700);
  await f.resolve("reverse",1,{city:"Madinah",countryCode:"SA",continentCode:"AS"});
  const before=f.snapshot();await f.reject("reverse",0);assert.equal(f.snapshot(),before);
});
test("obsolete builder GPS error preserves newer manual tuple feedback and export",async()=>{
  const f=fixture("builder",{ref:target});f.click("geo");f.input("lat","30");f.input("lon","31");
  const before=f.snapshot();await f.reject("gps",0);assert.equal(f.snapshot(),before);
});
test("obsolete settings GPS and reset errors preserve newer manual state and stored bytes",async()=>{
  for(const op of ["gps","coarse"]){
    const f=fixture("settings",{ref:target});f.click(op==="gps"?"set-pin":"set-reset");f.input("set-lat","30");f.input("set-lon","31");
    const before=f.snapshot();await f.reject(op,0);assert.equal(f.snapshot(),before);assert.equal(f.calls.applied.length,0);
  }
});
test("obsolete settings GPS and reset errors cannot change reopened session",async()=>{
  for(const op of ["gps","coarse"]){
    const f=fixture("settings",{ref:target});f.click(op==="gps"?"set-pin":"set-reset");f.click("setClose");f.buckle.dispatch("click");
    const before=f.snapshot();await f.reject(op,0);assert.equal(f.snapshot(),before);
  }
});
test("preferLocal without saved data boots explicit fixed fallback",async()=>{
  const f=widget({ref:target,hash:"#preferLocal=1&lat=24.47&lon=39.61&method=2&units=f",open:false});const boot=f.boot();
  assert.deepEqual([f.config().lat,f.config().lon,f.config().method,f.config().units],[24.47,39.61,"2","f"]);
  assert.equal(f.calls.coarse.length,0);assert.equal(f.calls.prayer.length,1);f.calls.prayer[0].resolve();await boot;
});
test("browser POSITION_UNAVAILABLE preserves target evidence without retry",async()=>{
  const f=widget({ref:target,seed:{lat:51.5,lon:-.12,label:"London",method:"3",units:"f",source:"manual"}}),before=f.config();
  f.click("set-pin");f.calls.gps[0].reject({code:2,message:"controlled position unavailable"});await drain();
  assert.deepEqual(f.config(),before);assert.equal(f.calls.gps.length,1);assert.match(f.elements.get("set-status").textContent,/unavailable/);
});
test("R0023 native wrapper widget script guard is inapplicable to delivered six-script entry",()=>{
  const s=readSource("index.html",target),scripts=[...s.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
  assert.equal(scripts.length,6);const guard=scripts.length!==2||!/src="config\.js"/.test(scripts[0][1])||scripts[1][1].trim();
  assert.ok(guard);console.log(JSON.stringify({instrument:"exact production text and unchanged wrapper guard; browser NOT_RUN",requiredScriptCount:2,deliveredScriptCount:scripts.length,guardWouldThrow:"Page script anchors changed",attributes:scripts.map(m=>m[1])}));
});
(async()=>{let failed=0;for(const c of cases){try{await c.run();console.log("PASS",c.name);}catch(e){failed++;console.error("FAIL",c.name,"\n",e.stack);}}
console.log(JSON.stringify({cases:cases.length,passed:cases.length-failed,failed,target,native:"NOT_RUN",scope:"held-out exact-source VM/body-custody/fixture-applicability checks; no production edits"}));process.exitCode=failed?1:0;})();
