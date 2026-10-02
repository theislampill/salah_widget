"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const {source,copy,record,harness,cfg,req,settle}=require("./r0003-harness.cjs");
test("R0003 actual applyConfig A then B: obsolete A cannot change current data, zone or B cache",async()=>{
  const h=harness(),a=h.apply(cfg(10,"A")),ar=req(h),b=h.apply(cfg(20,"B")),br=req(h,"07-09-2026",20);
  br.ok(record(undefined,"UTC","B-current"));await settle();await b;
  const before=h.writes.length;ar.ok(record(undefined,"UTC","A-obsolete"));await settle();await a;
  assert.equal(h.state().today.tag,"B-current");assert.equal(h.writes.length,before);assert.equal(h.state().lat,20);
});

test("R0003 positive actual applyConfig: later B succeeds after early A completion",async()=>{
  const h=harness(),a=h.apply(cfg(10,"A")),ar=req(h),b=h.apply(cfg(20,"B")),br=req(h,"07-09-2026",20);
  ar.ok(record(undefined,"UTC","A-early"));await settle();await a;br.ok(record(undefined,"UTC","B-current"));await settle();await b;
  assert.equal(h.state().today.tag,"B-current");assert.equal(h.state().lat,20);
});

test("R0003 ABA identity: original A remains obsolete when coordinates return to A",async()=>{
  const h=harness(),a1=h.apply(cfg(10,"A1")),r1=req(h),b=h.apply(cfg(20,"B")),rb=req(h,undefined,20),a2=h.apply(cfg(10,"A2"));
  const r2=h.requests.filter(r=>r.url.includes("/timings/07-09-2026?")&&new URL(r.url).searchParams.get("latitude")==="10")[1];
  r2.ok(record(undefined,"UTC","A2-current"));await settle();await a2;rb.ok(record(undefined,"UTC","B-obsolete"));await settle();await b;r1.ok(record(undefined,"UTC","A1-obsolete"));await settle();await a1;
  assert.equal(h.state().today.tag,"A2-current");
});

function observed(h){return {state:h.state(),writes:copy(h.writes),cache:[...h.storage],errors:copy(h.errors)};}
for(const [name,extra]of [["method-only",{method:"3"}],["school-only",{school:"1"}]]) test(`R0003 same coordinates ${name} owns its captured request and cache`,async()=>{
  const h=harness(),a=h.apply(cfg(10,"old")),old=req(h),b=h.apply(cfg(10,"new",extra));
  const current=h.requests.filter(r=>r.url.includes("/timings/07-09-2026?"))[1],url=new URL(current.url);
  assert.equal(url.searchParams.get("method"),extra.method||"2");assert.equal(url.searchParams.get("school"),extra.school||"0");
  current.ok(record(undefined,"UTC","selected"));await settle();await b;const before=observed(h);
  old.ok(record(undefined,"UTC","old"));await settle();await a;assert.deepEqual(observed(h),before);
  assert.ok(h.writes.some(w=>w.key===`salah:10|10|UTC|${extra.method||2}|${extra.school||0}`));
});
test("R0003 obsolete rejection and retained old timer cannot release or report over B",async()=>{
  const h=harness(),a=h.apply(cfg(10,"A")),old=req(h),oldTimer=[...h.timers.values()][0].fn,b=h.apply(cfg(20,"B")),current=req(h,undefined,20);
  await settle();assert.equal(h.run("_requestSlots.current.lat"),20);const before=observed(h);
  oldTimer();old.fail();await settle();await a;assert.deepEqual(observed(h),before);assert.equal(h.run("_requestSlots.current.lat"),20);
  current.ok(record(undefined,"UTC","B-current"));await settle();await b;assert.equal(h.state().today.tag,"B-current");assert.equal(h.run("_requestSlots.current"),null);
});
test("R0003 obsolete tomorrow body cannot enter new selection or its cache",async()=>{
  const h=harness();h.seed(record(undefined,"UTC","A"));h.run("render()");const old=req(h,"08-09-2026");
  old.headers.resolve({ok:true,status:200,json:()=>old.body.promise});await settle();const b=h.apply(cfg(20,"B"));req(h,undefined,20).ok(record(undefined,"UTC","B"));await settle();await b;
  const before=observed(h);old.body.resolve({code:200,status:"OK",data:record("08-09-2026","UTC","A-next")});await settle();assert.deepEqual(observed(h),before);
});
test("R0003 winning response persists and reloads through actual selected-cache loader",async()=>{
  const h=harness(),a=h.apply(cfg(10,"A")),old=req(h),b=h.apply(cfg(20,"B"));req(h,undefined,20).ok(record(undefined,"UTC","B"));await settle();await b;old.ok(record(undefined,"UTC","A"));await settle();await a;
  const reload=harness({hash:"#lat=20&lon=20&tz=UTC&method=2",offline:true});for(const [k,v]of h.storage)reload.storage.set(k,v);
  const boot=reload.boot();await reload.advance(2700);await boot;assert.equal(reload.state().today.tag,"B");assert.equal(reload.writes.length,0);assert.ok(reload.paints.length>0);
});
test("R0003 independent central slots retain B owners after A cleanup for all remote kinds",()=>{
  const h=harness();
  for(const kind of ["current","prefetch","weather","radar"]){
    h.run(`var old_${kind}=beginRequest('${kind}','07-09-2026')`);
  }
  h.run("beginRuntimeGeneration()");
  for(const kind of ["current","prefetch","weather","radar"]){
    assert.equal(h.run(`beginRequest('${kind}','08-09-2026')!==null`),true);
    assert.equal(h.run(`finishRequest(old_${kind})`),false);assert.equal(h.run(`_requestSlots.${kind}.requestedDay`),"08-09-2026");
  }
});
test("R0003 abort removal leaves stale rejection and healthy B commitment intact",async()=>{
  const before='controller:typeof AbortController!=="undefined"?new AbortController():null';assert.equal(source().split(before).length-1,1);
  const h=harness({source:source().replace(before,"controller:null")}),a=h.apply(cfg(10,"A")),old=req(h),b=h.apply(cfg(20,"B"));
  req(h,undefined,20).ok(record(undefined,"UTC","B"));await settle();await b;const state=observed(h);old.ok(record(undefined,"UTC","A"));await settle();await a;
  assert.deepEqual(observed(h),state);assert.equal(h.state().today.tag,"B");assert.ok(h.requests.every(r=>!r.init.signal));
});
test("R0003 mutant unconditional finally is killed by replacement-slot ownership",async()=>{
  const before="if(!requestEligible(op)) return false;\n  _requestSlots[op.kind]=null; return true;";assert.equal(source().split(before).length-1,1);
  const h=harness({source:source().replace(before,"_requestSlots[op.kind]=null; return true;")});h.apply(cfg(10,"A"));h.apply(cfg(20,"B"));await settle();
  assert.throws(()=>assert.equal(h.run("_requestSlots.current && _requestSlots.current.lat"),20));
});
test("R0003 historical Madinah/Riyadh to New York race preserves exact winning zone and Asr",async()=>{
  const h=harness();h.run("nowParts=function(){return {y:2026,mo:9,d:7,h:12,mi:0,s:0,dateStr:'07-09-2026'};}");
  const madinah=cfg(24.47,"Madinah",{lon:39.61,method:"4"}),newYork=cfg(40.71,"New York",{lon:-74.01});
  const dataA=record(undefined,"Asia/Riyadh","A"),dataB=record(undefined,"America/New_York","B");
  Object.assign(dataA.timings,{Fajr:"04:46",Sunrise:"06:00",Dhuhr:"12:00",Asr:"15:49",Maghrib:"18:00",Sunset:"18:00",Isha:"19:30"});
  Object.assign(dataB.timings,{Fajr:"05:00",Sunrise:"06:00",Dhuhr:"12:00",Asr:"15:30",Maghrib:"18:00",Sunset:"18:00",Isha:"19:30"});
  const a=h.apply(madinah),old=req(h,undefined,24.47),b=h.apply(newYork);req(h,undefined,40.71).ok(dataB);await settle();await b;
  const before=observed(h);old.ok(dataA);await settle();await a;assert.deepEqual(observed(h),before);assert.equal(h.state().tz,"America/New_York");assert.equal(h.run("model().nextTime"),"15:30");
  assert.equal(JSON.parse(h.storage.get("salah:40.71|-74.01|UTC|2|0")).data.meta.timezone,"America/New_York");
});
test("R0003 equator/prime-meridian current acquisition preserves numeric zero coordinates",async()=>{
  const h=harness(),applied=h.apply(cfg(0,"zero"));req(h,undefined,0).ok(record(undefined,"UTC","zero"));await settle();await applied;
  assert.equal(h.state().lat,0);assert.equal(h.state().lon,0);assert.equal(h.state().today.tag,"zero");assert.ok(h.writes.some(w=>w.key==="salah:0|0|UTC|2|0"));
});
