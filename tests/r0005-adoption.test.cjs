"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const {source,copy,record,harness,cfg,req,settle}=require("./r0003-harness.cjs");
test("R0005 completed prefetch promotes at midnight while network is offline",async()=>{
  const h=harness({epoch:"2026-09-07T23:59:59Z",offline:true});h.seed(record(undefined,"UTC","day7"),record("08-09-2026","UTC","prefetched8"));
  h.run("startRenderLoop()");await h.frame();await h.advance(1000);await h.frame();
  assert.equal(h.state().today.tag,"prefetched8");assert.equal(h.state().lastDate,"08-09-2026");assert.equal(h.state()._prayerStale,false);
});

test("R0005 positive normal next-day prefetch remains tomorrow before midnight",async()=>{
  const h=harness();h.seed(record(undefined,"UTC","day7"));h.run("render()");req(h,"08-09-2026").ok(record("08-09-2026","UTC","prefetched8"));await settle();
  assert.equal(h.state().today.tag,"day7");assert.equal(h.state().tomorrow.tag,"prefetched8");
});

test("R0005 late prefetch crossing midnight cannot repopulate tomorrow with current day",async()=>{
  const h=harness({epoch:"2026-09-07T23:59:59Z"});h.seed(record(undefined,"UTC","day7"));h.run("render();startRenderLoop()");const old=req(h,"08-09-2026");
  await h.advance(1000);await h.frame();const newer=h.requests.filter(r=>r.url.includes("/timings/08-09-2026?"))[1];
  newer.ok(record("08-09-2026","UTC","new-current8"));await settle();old.ok(record("08-09-2026","UTC","late-prefetch8"));await settle();
  assert.equal(h.state().today.tag,"new-current8");assert.notEqual(h.state().tomorrow?.date.gregorian.date,"08-09-2026");assert.equal(h.state().fetchingTomorrow,false);
});

test("R0005 frozen simulated second repaints accepted asynchronous rollover in existing rAF",async()=>{
  const h=harness({epoch:"2026-09-07T12:00:00Z",hash:"#lat=10&lon=10&tz=UTC&method=2&simTime=12:00"});h.seed(record(undefined,"UTC","day7"));h.run("startRenderLoop()");await h.frame();
  h.run("_simBase+=86400000");await h.frame();const held=req(h,"08-09-2026");held.ok(record("08-09-2026","UTC","new-current8"));await settle();
  const before=h.paints.length;for(let i=0;i<20;i++){await h.advance(h.elapsed()+16);await h.frame();}
  assert.ok(h.paints.length>before);assert.equal(h.paints.at(-1).today.tag,"new-current8");assert.equal(h.nodes.get(".c").dataset.stale,"");
});

test("R0005 held-out warm 100-frame control avoids repeated admission/Intl construction",async()=>{
  const h=harness();h.seed(record(),record("08-09-2026"));
  h.run(`let reviewIntl=0,reviewAdmissions=0;const originalIntl=Intl,originalCtor=Intl.DateTimeFormat,originalAdmit=admitPrayerRecord;
    Intl=Object.create(originalIntl);Intl.DateTimeFormat=function(...a){reviewIntl++;return new originalCtor(...a);};
    admitPrayerRecord=function(...a){reviewAdmissions++;return originalAdmit(...a);};startRenderLoop();`);
  await h.frame();h.run("reviewIntl=0;reviewAdmissions=0;");const paints=h.paints.length;
  for(let i=0;i<100;i++){await h.advance(h.elapsed()+16);await h.frame();}
  const observed={frames:100,elapsed:1600,intl:h.run("reviewIntl"),admission:h.run("reviewAdmissions"),paints:h.paints.length-paints,requests:h.requests.length,stale:h.state()._prayerStale};
  console.log(JSON.stringify({warmLoop:observed}));assert.equal(observed.admission,0);assert.ok(observed.intl<=106);assert.equal(observed.paints,1);assert.equal(observed.requests,0);assert.equal(observed.stale,false);
});
