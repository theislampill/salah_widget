"use strict";
// R0030 / issue 97: settings Reset authority, dirty-close commit and apply-failure state
// (docs/state-contracts/R0030.md). Runs the actual generated index.html applyConfig, persistence
// publisher and settings block against the actual config.js through tests/r0011-fixture.cjs (real
// applyConfig, VM doubles for providers and renderers, no network, no browser). VM evidence only;
// the native recipe is tools/qa/run_r0030_native.cjs.
// R0030_REF=<git ref> runs the same cases against that ref's generated index.html (RED witness);
// R0030_MUTANT=<name> applies one named source mutation (tests/r0030-reset-authority-mutations.test.cjs).
const test=require("node:test"),assert=require("node:assert/strict");
const {widget,drain}=require("./r0011-fixture.cjs");
const REF=process.env.R0030_REF||undefined, MUTANT=process.env.R0030_MUTANT||null;
const T={timeout:10000};
const {MUTANTS}=require("./r0030-mutants.cjs");
if(MUTANT&&!MUTANTS[MUTANT])throw new Error("unknown R0030 mutant "+MUTANT);
const mutate=MUTANT?source=>source.split(MUTANTS[MUTANT][0]).join(MUTANTS[MUTANT][1]):undefined;
const LONDON={lat:51.5,lon:-.12,label:"London",method:"3",units:"f",source:"manual"};
const DETECTED={ok:true,cfg:{lat:24.47,lon:39.61,label:"Madinah",area:"Madinah, SA",method:"4",units:"c",source:"coarse-ip"}};
const security=()=>{throw new DOMException("blocked","SecurityError");};
// A ref is read once with a large buffer (the generated page exceeds execFileSync's default).
const show=file=>require("node:child_process").execFileSync("git",["show",REF+":"+file],{cwd:require("node:path").resolve(__dirname,".."),encoding:"utf8",maxBuffer:1<<28});
const AT_REF=REF?{source:show("index.html"),configMutate:(text=>()=>text)(show("config.js"))}:{};
const make=(extra={})=>widget({...AT_REF,seed:LONDON,mutate,...extra});
const stored=f=>f.sandbox.SalahConfig.loadLocal();
const status=f=>f.elements.get("set-status").textContent;
const live=f=>f.elements.get("settings-persistence-status").textContent;
const isOpen=f=>f.card.classList.contains("settings-open");
async function settlePrayer(f){for(let i=0;i<4;i++){for(const p of f.calls.prayer)p.resolve();await drain();}}
const formTuple=f=>["set-label","set-lat","set-lon","set-method","set-units","set-time","set-datefmt","set-appearance"].map(id=>f.elements.get(id).value);
// Unobserved rejections are the PRA-F-33 defect: collect them instead of letting the runner crash.
const unhandled=[];process.on("unhandledRejection",e=>unhandled.push(e));

// ---- ES30-01/02: I1 — a pre-Reset dirty edit is never re-persisted by close (probe R1) ----
test("ES30-02 R1: pre-dispatch edit + Reset + close during detection never re-persists the pre-Reset site",T,async()=>{
  const f=make();f.input("set-method","2","change");f.click("set-reset");
  assert.equal(stored(f),null);assert.equal(f.run("_persistOutcome.status"),"cleared");
  f.click("setClose");
  assert.equal(stored(f),null,"close commits nothing the user edited after the Reset");
  assert.equal(f.config().lat,51.5,"runtime keeps the old site while detecting");
  await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  assert.equal(f.config().lat,24.47,"Reset target lands after close (G1-A)");assert.equal(f.config().method,"4","pre-dispatch method discarded");
  assert.equal(stored(f),null,"nothing re-persisted");assert.equal(isOpen(f),false);
});
test("ES30-02 R1 apply phase: close during the Reset apply commits only post-dispatch edits merged into the target",T,async()=>{
  const f=make();f.input("set-method","2","change");f.click("set-reset");await f.resolveCall("coarse",0,DETECTED);
  assert.equal(f.calls.prayer.length,1,"Reset apply awaits prayer");
  f.input("set-units","f","change");f.click("setClose");
  assert.equal(stored(f),null,"nothing saved while the Reset apply is pending");
  await settlePrayer(f);
  const saved=stored(f);assert.ok(saved,"the post-dispatch units edit is close-saved");
  assert.deepEqual([saved.lat,saved.lon,saved.method,saved.units],[24.47,39.61,"4","f"]);
  assert.deepEqual([f.config().lat,f.config().units],[24.47,"f"]);
});
// ---- ES30-03: G2(i) — a display-name edit is not a location intent (probe R2 + reset-label-probe) ----
test("ES30-03 R2: display-name edit during detection then close lands the Reset target with the typed name",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-label","Home");f.click("setClose");
  assert.equal(stored(f),null);
  await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  assert.deepEqual([f.config().lat,f.config().label],[24.47,"Home"]);
  const saved=stored(f);assert.ok(saved,"the name edit is close-saved");assert.deepEqual([saved.lat,saved.label],[24.47,"Home"]);
});
test("ES30-03 display-name edit during the Reset apply keeps Reset ownership and the typed name",T,async()=>{
  const f=make();f.click("set-reset");await f.resolveCall("coarse",0,DETECTED);f.input("set-label","Home");await settlePrayer(f);
  assert.deepEqual(formTuple(f).slice(0,3),["Home","24.47","39.61"],"form shows the target with the typed name");
  assert.equal(f.run("_setDirty"),true);assert.match(status(f),/Using estimated area: Madinah, SA/);
  f.click("setClose");await settlePrayer(f);
  const saved=stored(f);assert.deepEqual([saved.lat,saved.label],[24.47,"Home"]);assert.equal(f.config().label,"Home");
});
test("ES30-03 A to B to A display name during detection still counts as a post-dispatch edit",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-label","Home");f.input("set-label","London");
  await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  assert.equal(f.config().lat,24.47);assert.equal(f.config().label,"London");assert.equal(f.run("_setDirty"),true);
});
// ---- ES30-06: I4/OM-04 — nothing claims the cleared record (probe R3) ----
test("ES30-06 R3: after a successful clear no surface claims a saved position; classifier neutral",T,async()=>{
  const now=Date.now(),evidence={source:"browser-geolocation",accuracyM:12,acquiredAt:now-60000};
  const f=make({now,seed:{...LONDON,source:"browser-geolocation",locationEvidence:evidence}});
  assert.match(f.elements.get("set-pin").title,/^Saved browser position/,"control: the seeded record is claimed before Reset");
  const before=f.run("JSON.stringify(CONFIG)");
  f.click("set-reset");
  assert.doesNotMatch(f.elements.get("set-pin").title,/Saved/,"the open panel withdraws the claim at clear");
  f.click("setClose");f.buckle.dispatch("click");
  assert.equal(stored(f),null);assert.equal(f.run("_setLocationSaved"),false);
  assert.doesNotMatch(f.elements.get("set-pin").title,/Saved/);assert.doesNotMatch(f.elements.get("set-pin").getAttribute("aria-label"),/Saved/);
  assert.notEqual(f.config().source,"localStorage","runtime provenance marker no longer claims storage");
  assert.equal(f.config().origin,"browser-geolocation");assert.equal(f.config().savedAt,null);
  f.sandbox.__before=JSON.parse(before);
  assert.equal(f.run('classifyConfigChange(__before,CONFIG,{reset:false}).path'),"none","marker change is classifier-neutral");
  assert.equal(f.run('classifyConfigChange(CONFIG,SalahConfig.normalize(CONFIG),{reset:false}).path'),"none");
});
// ---- ES30-08/08a: clear failure unchanged; G1b(a); G1-A closed-panel failure (G1a A1) ----
test("ES30-08 denied clear keeps pre-dispatch dirtiness: close saves the edit with the current site",T,async()=>{
  const f=make(),key=f.sandbox.SalahConfig.KEY;f.input("set-method","2","change");f.sandbox.localStorage.removeItem=security;f.click("set-reset");
  assert.equal(f.calls.coarse.length,0);assert.equal(f.run("_setDirty"),true,"the Reset click did not clear dirtiness");
  f.click("setClose");await settlePrayer(f);
  const saved=JSON.parse(f.storage.get(key));assert.deepEqual([saved.lat,saved.method],[51.5,"2"]);
});
test("ES30-08a G1b(a): detection fails with the dispatching panel open; the visible form keeps manual close-save",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-method","2","change");await f.resolveCall("coarse",0,{ok:false});
  assert.match(status(f),/Enter your location\./);assert.equal(f.run("_setDirty"),true);
  f.click("setClose");await settlePrayer(f);
  assert.deepEqual([stored(f).lat,stored(f).method],[51.5,"2"],"accepted G1b(a) exception of I1");
});
test("ES30-08a G1-A/G1a(A1): detection fails after close; deferred edits apply session-only, no reopen, next open shows it",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-units","c","change");f.click("setClose");
  await f.resolveCall("coarse",0,{ok:false});await settlePrayer(f);
  assert.equal(isOpen(f),false,"no automatic reopen");assert.equal(stored(f),null,"pre-Reset site never re-persisted");
  assert.deepEqual([f.config().lat,f.config().units],[51.5,"c"],"deferred edit applied for the session");
  f.buckle.dispatch("click");assert.match(status(f),/Saved settings cleared\.\nEnter your location\./);
});
test("ES30-08a detection fails while a later session is open: that session is not rewritten; its close is session-only",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-units","c","change");f.click("setClose");f.buckle.dispatch("click");
  const before=[formTuple(f),status(f)];await f.resolveCall("coarse",0,{ok:false});
  assert.deepEqual([formTuple(f),status(f)],before);
  f.click("setClose");await settlePrayer(f);
  assert.equal(stored(f),null);assert.equal(f.config().units,"c");
  f.buckle.dispatch("click");assert.match(status(f),/Enter your location\./);
});
// ---- ES30-09: storage-denied close during Reset ----
test("ES30-09 storage-denied close during Reset: session-only warning on the merged target, nothing written",T,async()=>{
  const f=make();f.click("set-reset");f.sandbox.localStorage.setItem=security;f.input("set-label","Home");f.click("setClose");
  await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  assert.equal(f.storage.has(f.sandbox.SalahConfig.KEY),false);assert.deepEqual([f.config().lat,f.config().label],[24.47,"Home"]);
  assert.match(live(f),/Changes apply for this session only/);assert.equal(f.buckle.classList.contains("persist-warning"),true);
});
// ---- ES30-10: G5(a) — preferLocal Reset follows the resolver (N1) ----
test("ES30-10 N1: preferLocal hash site Reset makes no coarse request and applies the hash site",T,async()=>{
  const f=make({hash:"#preferLocal=1&lat=21.4225&lon=39.8262&label=Makkah"});
  assert.equal(f.config().lat,51.5,"control: saved record wins before Reset");
  f.click("set-reset");await settlePrayer(f);
  assert.equal(f.calls.coarse.length,0,"no IP request");
  assert.deepEqual([f.config().lat,f.config().source],[21.4225,"hash"]);assert.equal(stored(f),null);
  assert.doesNotMatch(status(f),/Detecting your area|estimated area/);
  assert.equal(f.json('SalahConfig.resolve(location.hash).cfg.lat'),21.4225,"runtime equals what reload would select");
});
test("ES30-10 control: local mode without a saved record still detects on Reset",T,async()=>{
  const f=make();f.click("set-reset");assert.equal(f.calls.coarse.length,1);assert.match(status(f),/Detecting your area/);
});
// ---- ES30-05: newer explicit location intents still supersede Reset ----
test("ES30-05 coordinate edit during detection supersedes Reset; close saves the typed site",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-lat","30");f.input("set-lon","31");await f.resolveCall("coarse",0,DETECTED);
  assert.equal(f.calls.prayer.length,0);f.click("setClose");await settlePrayer(f);assert.deepEqual([stored(f).lat,stored(f).lon],[30,31]);
});
// D1 per the issue's table: a place-search CANDIDATE SHOWN and a GPS SUCCESS supersede Reset; the search
// start and the pin click do not, so a failed or empty lookup leaves the Reset target to land.
const BERLIN=[{lat:52.52,lon:13.41,name:"Berlin",norm:"Berlin, Germany",cc:"de"}];
const FIX={coords:{latitude:48.85,longitude:2.35,accuracy:25},timestamp:Date.now()};
const gpsFail=async f=>{f.calls.gps.at(-1).reject({code:1,message:"denied"});await drain();await drain();};
test("ES30-05 D1 a shown place-search candidate supersedes Reset; close saves the chosen place",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-label","Berlin");f.key("set-label","Enter");
  await f.resolveCall("search",0,BERLIN);await f.resolveCall("coarse",0,DETECTED);
  assert.equal(f.calls.prayer.length,0,"stale Reset target not applied");f.click("setClose");await settlePrayer(f);
  assert.deepEqual([stored(f).lat,stored(f).label],[52.52,"Berlin"]);
});
test("ES30-05 D1 a place search with no match does not end Reset; the target lands",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-label","Nowhere");f.key("set-label","Enter");
  await f.resolveCall("search",0,[]);await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  assert.equal(f.config().lat,24.47,"Reset target landed");assert.equal(f.elements.get("set-lat").value,"24.47");
});
test("ES30-05 D1 a GPS fix supersedes Reset; close saves the fix",T,async()=>{
  const f=make();f.click("set-reset");f.click("set-pin");await f.resolveCall("gps",0,FIX);await drain();
  await f.resolveCall("coarse",0,DETECTED);assert.equal(f.calls.prayer.length,0,"stale Reset target not applied");
  f.click("setClose");await settlePrayer(f);assert.deepEqual([stored(f).lat,stored(f).lon],[48.85,2.35]);
});
test("ES30-05 D1 a denied GPS request does not end Reset; the target lands",T,async()=>{
  const f=make();f.click("set-reset");f.click("set-pin");await gpsFail(f);
  await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);assert.equal(f.config().lat,24.47);
});
test("ES30-05 another Reset owns: the first detection result is discarded",T,async()=>{
  const f=make();f.click("set-reset");f.click("set-reset");assert.equal(f.calls.coarse.length,2);
  await f.resolveCall("coarse",0,{ok:true,cfg:{...DETECTED.cfg,lat:10,lon:10,label:"Stale"}});assert.equal(f.calls.prayer.length,0);
  await f.resolveCall("coarse",1,DETECTED);await settlePrayer(f);assert.equal(f.config().label,"Madinah");
});
// ---- review F1: a post-Reset edit survives close, reopen and a later lookup / Reset ----
test("F1 Reset, edit, close, reopen, denied GPS click, close: the edit is saved on the Reset target",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-method","2","change");f.click("setClose");f.buckle.dispatch("click");
  assert.equal(f.elements.get("set-method").value,"2");f.click("set-pin");await gpsFail(f);f.click("setClose");
  await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  assert.deepEqual([f.config().lat,f.config().method],[24.47,"2"]);const saved=stored(f);assert.ok(saved,"edit saved");assert.deepEqual([saved.lat,saved.method],[24.47,"2"]);
});
test("F1 Reset, edit, close, reopen, GPS fix, close: the fix is saved with the edit",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-method","2","change");f.click("setClose");f.buckle.dispatch("click");
  f.click("set-pin");await f.resolveCall("gps",0,FIX);await drain();f.click("setClose");await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  const saved=stored(f);assert.deepEqual([saved.lat,saved.method],[48.85,"2"]);
});
test("F1 Reset, edit, close, reopen, place candidate, close: the place is saved with the edit",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-method","2","change");f.click("setClose");f.buckle.dispatch("click");
  f.input("set-label","Berlin");f.key("set-label","Enter");await f.resolveCall("search",0,BERLIN);f.click("setClose");
  await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  const saved=stored(f);assert.deepEqual([saved.lat,saved.method,saved.label],[52.52,"2","Berlin"]);
});
test("F1 Reset, edit, close, reopen, second Reset: the edit predates the second Reset and is discarded (accepted rule)",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-method","2","change");f.click("setClose");f.buckle.dispatch("click");
  f.click("set-reset");await f.resolveCall("coarse",1,DETECTED);await settlePrayer(f);
  assert.deepEqual([f.config().lat,f.config().method],[24.47,"4"]);assert.equal(f.run("_setDirty"),false);f.click("setClose");assert.equal(stored(f),null);
});
test("F1 a second Reset whose clear fails leaves the first Reset and its recorded edit in force",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-method","2","change");f.click("setClose");f.buckle.dispatch("click");
  f.sandbox.localStorage.removeItem=security;f.click("set-reset");assert.equal(f.calls.coarse.length,1,"failed clear starts no detection");
  f.click("setClose");await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  const saved=stored(f);assert.deepEqual([saved.lat,saved.method],[24.47,"2"]);
});
// ---- review F2: survivors x20, x02, x18, x34, x32 ----
test("F2 a held target released by a newer coordinate intent is not applied",T,async()=>{
  const f=make();f.click("set-reset");f.click("setClose");f.buckle.dispatch("click");await f.resolveCall("coarse",0,DETECTED);
  f.input("set-lat","30");f.input("set-lon","31");await settlePrayer(f);
  assert.equal(f.calls.prayer.length,0,"stale held target not applied");assert.equal(f.config().lat,51.5);
  f.click("setClose");await settlePrayer(f);assert.deepEqual([f.config().lat,stored(f).lat],[30,30]);
});
test("F2 close during a pending Reset leaves no uncommitted dirtiness behind",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-units","c","change");f.click("setClose");assert.equal(f.run("_setDirty"),false);
});
test("F2 after a closed-panel detection failure the form owns location again: a later close saves",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-units","c","change");f.click("setClose");await f.resolveCall("coarse",0,{ok:false});await settlePrayer(f);
  f.buckle.dispatch("click");f.input("set-time","12","change");f.click("setClose");await settlePrayer(f);
  const saved=stored(f);assert.ok(saved,"visible-form close-save");assert.deepEqual([saved.lat,saved.units,saved.time],[51.5,"c","12"]);
});
test("F2 the closed-panel failure notice is shown on the next open only",T,async()=>{
  const f=make();f.click("set-reset");f.click("setClose");await f.resolveCall("coarse",0,{ok:false});
  f.buckle.dispatch("click");assert.match(status(f),/Enter your location\./);f.click("setClose");f.buckle.dispatch("click");assert.doesNotMatch(status(f),/Enter your location\./);
});
test("F2 limit: a Reset apply fault with the panel closed drops the owner and saves nothing (no pre-Reset re-persist)",T,async()=>{
  const f=make();f.sandbox.console={...console,error(){}};f.click("set-reset");f.input("set-units","c","change");f.click("setClose");
  f.sandbox.bindConfig=()=>{throw new TypeError("injected bindConfig");};await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  assert.equal(stored(f),null,"nothing persisted, in particular not the pre-Reset site");assert.match(live(f),/Settings could not be applied \(TypeError\)/);
  assert.equal(f.config().units,"f","documented limit: the recorded edit is not applied");
});
// ---- review F3: a stale successful apply cannot withdraw a newer failure ----
test("F3 a stale successful apply does not withdraw a newer apply's failure line",T,async()=>{
  const f=make(),real=f.sandbox.bindConfig;f.sandbox.console={...console,error(){}};
  f.input("set-units","c","change");f.click("setClose");assert.equal(f.calls.prayer.length,1,"apply A pending on prayer");
  f.buckle.dispatch("click");f.sandbox.bindConfig=()=>{throw new TypeError("injected B");};f.input("set-lat","30");f.input("set-lon","31");f.click("setClose");await drain();
  assert.match(live(f),/could not be applied/);f.sandbox.bindConfig=real;
  f.calls.prayer[0].resolve();await drain();await drain();assert.match(live(f),/could not be applied/,"A's stale success leaves B's failure reported");
});
// ---- ES30-13: duplicate / concurrent / interrupted ----
test("ES30-13 close, reopen, close during detection: commit takes location from the Reset owner; edits of both sessions kept",T,async()=>{
  const f=make();f.click("set-reset");f.input("set-method","2","change");f.click("setClose");f.buckle.dispatch("click");
  assert.equal(f.elements.get("set-method").value,"2","reopened form keeps the pending post-dispatch edit");
  assert.equal(f.elements.get("set-lat").value,"51.5","reopened form shows the runtime site");
  f.input("set-units","c","change");f.click("setClose");assert.equal(stored(f),null);
  await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  const saved=stored(f);assert.deepEqual([saved.lat,saved.method,saved.units],[24.47,"2","c"]);
});
test("ES30-13 detection lands while a later session is open: held, not rewritten, landed on that session's close",T,async()=>{
  const f=make();f.click("set-reset");f.click("setClose");f.buckle.dispatch("click");const before=[formTuple(f),status(f)];
  await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  assert.deepEqual([formTuple(f),status(f)],before,"later session untouched");assert.equal(f.config().lat,51.5);assert.equal(f.calls.prayer.length,0);
  f.click("setClose");await settlePrayer(f);
  assert.equal(f.config().lat,24.47);assert.equal(stored(f),null,"clean close: nothing saved");
});
test("ES30-13 Reset apply settling in a later session does not rewrite that session's form or status",T,async()=>{
  const f=make();f.click("set-reset");await f.resolveCall("coarse",0,DETECTED);f.click("setClose");f.buckle.dispatch("click");
  const before=[formTuple(f),status(f)];await settlePrayer(f);
  assert.deepEqual([formTuple(f),status(f)],before);
  f.input("set-time","12","change");f.click("setClose");await settlePrayer(f);
  const saved=stored(f);assert.deepEqual([saved.lat,saved.time],[24.47,"12"]);
});
// ---- ES30-04/positive controls ----
test("ES30-04 positive: Reset completing with the panel open is unchanged (status, form, no resave)",T,async()=>{
  const f=make();f.click("set-reset");await f.resolveCall("coarse",0,DETECTED);await settlePrayer(f);
  assert.equal(status(f),"Saved settings cleared.\nUsing estimated area: Madinah, SA");
  assert.deepEqual(formTuple(f).slice(0,4),["Madinah","24.47","39.61","4"]);assert.equal(f.run("_setDirty"),false);
  f.click("setClose");await settlePrayer(f);assert.equal(stored(f),null);assert.equal(f.calls.prayer.length,1,"close after completion restarts nothing");
});
// ---- ES30-11/12: PRA-F-33 — settings apply rejections are observed and reported (G3 a) ----
const CALLEES=["beginRuntimeGeneration","bindConfig","resetForNewLocation","loadPrayerData","startRenderLoop"];
for(const callee of CALLEES){
  test(`ES30-12 close-save: injected ${callee} fault is observed and reported; persistence fact kept`,T,async()=>{
    const f=make();f.sandbox[callee]=()=>{throw new TypeError("injected "+callee);};const errors=[];f.sandbox.console={...console,error:(...a)=>errors.push(a)};
    const seen=unhandled.length;f.input("set-lat","30");f.input("set-lon","31");f.click("setClose");await settlePrayer(f);
    assert.equal(unhandled.length,seen,"no unhandled rejection");
    assert.equal(stored(f).lat,30,"successful save is not rolled back");assert.equal(f.run("_persistOutcome.status"),"saved");
    assert.match(live(f),/Settings saved in this browser\.\nSettings could not be applied \(TypeError\)\. Reload the widget to try again\./);
    assert.equal(errors.length,1,"reported once");
    f.buckle.dispatch("click");assert.match(status(f),/Settings could not be applied/);assert.equal(f.elements.get("set-status").classList.contains("err"),true);
  });
}
test("ES30-12 Reset apply fault is observed and reported in the dispatching session",T,async()=>{
  const f=make();f.sandbox.bindConfig=()=>{throw new TypeError("injected bindConfig");};f.sandbox.console={...console,error(){}};
  const seen=unhandled.length;f.click("set-reset");await f.resolveCall("coarse",0,DETECTED);await drain();
  assert.equal(unhandled.length,seen);assert.match(status(f),/Saved settings cleared\.\nSettings could not be applied \(TypeError\)/);
  assert.doesNotMatch(status(f),/Using estimated area/,"no claim that the target applied");assert.equal(f.calls.loop,0,"no loop started");
});
test("ES30-12 a later successful apply withdraws the failure report",T,async()=>{
  const f=make(),real=f.sandbox.bindConfig;f.sandbox.bindConfig=()=>{throw new TypeError("once");};f.sandbox.console={...console,error(){}};
  f.input("set-units","c","change");f.click("setClose");await drain();assert.match(live(f),/could not be applied/);
  f.sandbox.bindConfig=real;f.buckle.dispatch("click");f.input("set-units","f","change");f.click("setClose");await settlePrayer(f);
  assert.doesNotMatch(live(f),/could not be applied/);assert.equal(live(f),"Settings saved in this browser.");
});
