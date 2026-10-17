"use strict";
// Actual source-bound boot, day classifier, loader, ownership, rAF and model/DOM
// consumers run via the existing fixture. Controlled source evidence, not native QA.
const test=require("node:test"),assert=require("node:assert/strict");
const crypto=require("node:crypto");
const {source,record,harness,req,settle}=require("./r0003-harness.cjs");
const zone="America/New_York",day7="07-03-2026",day8="08-03-2026",day9="09-03-2026";
const base="2026-03-08T04:30:00Z",twoHours=7200000;
const text=node=>(node.innerHTML||node.textContent||"").replace(/<[^>]*>/g,"").replace(/\s+/g," ").trim();
function prayer(day,tag=day){
  const data=record(day,zone,tag);
  Object.assign(data.timings,{Fajr:"05:00",Sunrise:"06:00",Dhuhr:"12:30",Asr:"15:00",Maghrib:"18:00",Sunset:"18:00",Isha:"20:00"});
  return data;
}
function fixture(raw=source(),format="24",extra={}){
  return harness({source:raw,epoch:base,hash:`#lat=40.7128&lon=-74.006&tz=${zone}&method=2&time=${format}&datefmt=YYYY-MM-DD`,...extra});
}
async function bootDay(raw=source(),format="24"){
  const h=fixture(raw,format),boot=(await h.startBoot()).pending;
  req(h,day7).ok(prayer(day7));await settle();await boot;
  req(h,day8).ok(prayer(day8));await settle();await h.frame();
  assert.equal(h.run("model().leftMin"),270);
  assert.equal(text(h.nodes.get("#ce")),"2026-03-07CE");
  return h;
}
async function forward(h){
  h.wallBy(twoHours);await h.frame();
  req(h,day9).ok(prayer(day9));await settle();await h.frame();
  assert.equal(h.state().lastDate,day8);
  assert.equal(h.run("model().leftMin"),150);
  assert.equal(h.requests.length,3);
}
async function reverse(raw=source(),format="24"){
  const h=await bootDay(raw,format);await forward(h);
  h.wallBy(-twoHours);await h.frame();
  assert.equal(h.requests.length,4,"reverse day must promptly start a fresh Mar7 acquisition");
  assert.ok(h.requests[3].url.includes(`/timings/${day7}?`));
  h.requests[3].ok(prayer(day7,"returned7"));await settle();await h.frame();
  assert.equal(h.requests.length,5);
  h.requests[4].ok(prayer(day8,"next8"));await settle();await h.frame();
  assert.equal(h.state().today.tag,"returned7");
  assert.equal(h.state().lastDate,day7);assert.equal(h.state()._prayerStale,false);
  assert.equal(h.state().tomorrow.tag,"next8");
  assert.equal(h.run("model().nowEpoch"),1772944200000);
  assert.equal(h.run("model().nextEpoch"),1772960400000);
  assert.equal(h.run("model().leftMin"),270);assert.equal(h.run("_lastRender.leftMin"),270);
  assert.equal(h.nodes.get(".nt").textContent,format==="24"?"05:00":"5:00 AM");
  assert.equal(text(h.nodes.get(".left")),"4h 30m left until Fajr");
  assert.equal(text(h.nodes.get("#ce")),"2026-03-07CE");
  assert.equal(h.nodes.get(".c").dataset.stale,"");
  assert.equal(h.paints.at(-1).today.tag,"returned7");
  assert.equal(h.run("_requestSlots.current"),null);
  assert.equal(h.run("_requestSlots.prefetch"),null);
  return h;
}
for(const format of ["24","12"])test(`R0005/R0020 accepted forward day permits prompt return and painted270m in ${format}h`,async()=>{
  await reverse(source(),format);
});

test("R0006 failed same-day attempts retain60s cooldown through repeated frames",async()=>{
  const h=fixture(),boot=(await h.startBoot()).pending;h.requests[0].fail();
  await h.advance(900);h.requests[1].fail();
  await h.advance(2700);h.requests[2].fail();await settle();await boot;
  assert.deepEqual(h.requests.map(r=>r.at),[0,900,2700]);
  assert.equal(h.state().today,null);
  for(let at=3000;at<=59000;at+=1000){await h.advance(at);await h.frame();}
  assert.equal(h.requests.length,3);
  await h.advance(60000);await h.frame();
  assert.equal(h.requests.length,4);assert.equal(h.requests[3].at,60000);
  for(let i=0;i<20;i++)await h.frame();
  assert.equal(h.requests.length,4,"owning operation must prevent overlapping retry starts");
  h.requests[3].ok(prayer(day7,"recovered7"));await settle();await h.frame();
  req(h,day8).ok(prayer(day8));await settle();await h.frame();
  assert.equal(h.paints.at(-1).today.tag,"recovered7");
  for(let i=0;i<20;i++){h.run("loadPrayerData()");await h.frame();}
  assert.equal(h.requests.length,5,"success and repeated same-day callers must preserve the60s start budget");
});

async function pendingOwner(raw=source()){
  const h=fixture(raw);h.seed(prayer(day7));
  h.run("loadPrayerData();startRenderLoop()");await h.frame();
  const current=req(h,day7),prefetch=req(h,day8),owner=h.run("_requestSlots.current.operationId");
  h.wallBy(twoHours);await h.frame();
  prefetch.ok(prayer(day8,"promoted8"));await settle();
  assert.equal(h.state().today.tag,"promoted8");
  assert.equal(h.run("_requestSlots.current.operationId"),owner,"prefetch settlement must not release current ownership");
  assert.equal(h.run("_requestSlots.prefetch"),null);
  await h.frame();const nextOwner=h.run("_requestSlots.prefetch.operationId");
  current.ok(prayer(day7,"late7"));await settle();
  const corrected=h.requests.filter(r=>r.url.includes(`/timings/${day8}?`))[1];
  assert.ok(corrected,"active loader must keep its corrected-day request after late promotion");
  assert.equal(h.run("_requestSlots.current.operationId"),owner);
  assert.equal(h.run("_requestSlots.current.prayerAttempts"),2);
  corrected.ok(prayer(day8,"corrected8"));await settle();await h.frame();
  assert.equal(h.state().today.tag,"corrected8");assert.equal(h.state().lastDate,day8);
  assert.equal(h.run("_requestSlots.current"),null);
  assert.equal(h.run("_requestSlots.prefetch.operationId"),nextOwner,"current finally must not release the active successor prefetch");
  assert.equal(h.state()._prayerStale,false);
  req(h,day9).ok(prayer(day9));await settle();await h.frame();
  return h;
}
test("R0005/R0006 late prefetch promotion preserves owning current loader and finally",async()=>{
  await pendingOwner();
});
const retirement=`    if(changedDay && _prayerCooldown.current && _prayerCooldown.current.day!==current){
      _prayerCooldown.current={day:current,nextTry:0};
    }`;
test("R0005 remove-retirement mutant recreates the prompt reverse-day failure",async()=>{
  const raw=source();assert.equal(raw.split(retirement).length-1,1);
  const mutant=raw.replace(retirement,"");
  for(const format of ["24","12"])await assert.rejects(()=>reverse(mutant,format),/reverse day must promptly start/);
  console.log(JSON.stringify({removedRetirementSha256:crypto.createHash("sha256").update(mutant).digest("hex"),killedBy:"actual reverse acquisition in both formats"}));
});
test("R0006 null-retirement mutant loses the actual owning loader's corrected-day request",async()=>{
  const raw=source();assert.equal(raw.split(retirement).length-1,1);
  const mutant=raw.replace(retirement,'    if(changedDay && _prayerCooldown.current && _prayerCooldown.current.day!==current){ _prayerCooldown.current=null; }');
  await assert.rejects(()=>pendingOwner(mutant),/active loader must keep its corrected-day request/);
  console.log(JSON.stringify({nullRetirementSha256:crypto.createHash("sha256").update(mutant).digest("hex"),killedBy:"actual pending current loader after late prefetch promotion"}));
});
console.log(JSON.stringify({dayReturnSourceSha256:crypto.createHash("sha256").update(source()).digest("hex"),evidence:"source-bound only; native repair verification remains separate"}));
