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

test("R0005 late next-day prefetch rescues current when midnight acquisition exhausts",async()=>{
  const h=harness({epoch:"2026-09-07T23:59:59Z"});h.seed(record(undefined,"UTC","old7"));h.run("render();startRenderLoop()");const prefetch=req(h,"08-09-2026");
  await h.advance(1000);await h.frame();h.requests[1].fail();await h.advance(1900);h.requests[2].fail();await h.advance(3700);h.requests[3].fail();await settle();
  assert.equal(h.state().today.tag,"old7");assert.equal(h.state()._prayerStale,true);
  prefetch.ok(record("08-09-2026","UTC","rescue8"));await settle();assert.equal(h.state().today.tag,"rescue8");assert.equal(h.state().tomorrow,null);assert.equal(h.state().fetchingTomorrow,false);
  await h.frame();assert.equal(h.paints.at(-1).today.tag,"rescue8");assert.equal(h.state()._prayerStale,false);assert.ok(req(h,"09-09-2026"));
  assert.equal(JSON.parse(h.storage.get("salah:10|10|UTC|2|0")).date,"08-09-2026");
});
test("R0005 payload neither current nor successor is discarded after further day movement",async()=>{
  const h=harness();h.seed(record(undefined,"UTC","day7"));h.run("render();startRenderLoop()");const old=req(h,"08-09-2026");
  h.wallBy(2*86400000);await h.frame();req(h,"09-09-2026").ok(record("09-09-2026","UTC","day9"));await settle();const before={today:h.state().today,writes:copy(h.writes)};
  old.ok(record("08-09-2026","UTC","old8"));await settle();assert.deepEqual(h.state().today,before.today);assert.deepEqual(h.writes,before.writes);assert.notEqual(h.state().tomorrow?.date.gregorian.date,"08-09-2026");
});
test("R0005 backward correction reclassifies and acquires the actual earlier civil day",async()=>{
  const h=harness({epoch:"2026-09-08T12:00:00Z"});h.seed(record("08-09-2026","UTC","day8"));h.run("startRenderLoop()");await h.frame();
  h.wallBy(-86400000);await h.frame();assert.equal(h.state()._prayerStale,true);req(h,"07-09-2026").ok(record("07-09-2026","UTC","earlier7"));await settle();await h.frame();
  assert.equal(h.state().lastDate,"07-09-2026");assert.equal(h.state().today.tag,"earlier7");assert.equal(h.state()._prayerStale,false);assert.equal(h.paints.at(-1).today.tag,"earlier7");
});
test("R0005 hidden next-day completion marks dirty and paints once on frozen visible resume",async()=>{
  const h=harness({hash:"#lat=10&lon=10&tz=UTC&method=2&simTime=12:00"});h.seed(record());h.run("startRenderLoop()");await h.frame();const prefetch=req(h,"08-09-2026"),before=h.paints.length;
  h.hide();assert.equal(h.frames.size,0);prefetch.ok(record("08-09-2026","UTC","next8"));await settle();await h.advance(5000);assert.equal(h.paints.length,before);assert.equal(h.frames.size,0);
  h.show();assert.equal(h.frames.size,1);await h.frame();assert.equal(h.paints.length,before+1);assert.equal(h.state().tomorrow.tag,"next8");
  for(let i=0;i<20;i++){await h.advance(h.elapsed()+16);await h.frame();}assert.equal(h.paints.length,before+1);
});
test("R0005 usable next-day record suppresses redundant work; promotion allows one new successor",async()=>{
  const h=harness({hash:"#lat=10&lon=10&tz=UTC&method=2&simTime=12:00"});h.seed(record());h.run("startRenderLoop()");await h.frame();req(h,"08-09-2026").ok(record("08-09-2026","UTC","next8"));await settle();
  for(let i=0;i<66;i++){await h.advance(i*1000);await h.frame();}assert.equal(h.requests.length,1);
  h.run("_simBase+=86400000");await h.frame();assert.equal(h.state().today.tag,"next8");assert.equal(h.requests.length,2);assert.ok(req(h,"09-09-2026"));
});
for(const [epoch,day,next,zone]of [
  ["2026-12-31T23:59:59Z","31-12-2026","01-01-2027","UTC"],
  ["2028-02-29T23:59:59Z","29-02-2028","01-03-2028","UTC"],
  ["2026-03-08T04:59:59Z","07-03-2026","08-03-2026","America/New_York"]
])test(`R0005 full actual midnight promotion across ${day} -> ${next} in ${zone}`,async()=>{
  const h=harness({epoch,offline:true});h.seed(record(day,zone,"old"),record(next,zone,"prefetched"));h.run("startRenderLoop()");await h.frame();await h.advance(1000);await h.frame();
  assert.equal(h.state().lastDate,next);assert.equal(h.state().today.tag,"prefetched");assert.equal(h.state()._prayerStale,false);assert.equal(h.paints.at(-1).today.date.gregorian.date,next);
});
test("R0005 mutant removing promotion is killed by offline completed prefetch",async()=>{
  const before="if(prayerRecordReady(tomorrow,day)) adoptPrayerBundle(tomorrow,day);";assert.equal(source().split(before).length-1,1);
  const h=harness({source:source().replace(before,"if(prayerRecordReady(tomorrow,day)) {}"),epoch:"2026-09-07T23:59:59Z",offline:true});h.seed(record(),record("08-09-2026","UTC","prefetched"));h.run("startRenderLoop()");await h.frame();await h.advance(1000);await h.frame();
  assert.throws(()=>assert.equal(h.state().today.tag,"prefetched"));assert.equal(h.state()._prayerStale,true);
});
test("R0005 mutant unconditional tomorrow settlement is killed by actual midnight duplicate",async()=>{
  const before=".then(data=>{ adoptPrayerBundle(data,day,op,false); })";assert.equal(source().split(before).length-1,1);
  const h=harness({source:source().replace(before,".then(data=>{ tomorrow=data; })"),epoch:"2026-09-07T23:59:59Z"});h.seed(record());h.run("render();startRenderLoop()");const old=req(h,"08-09-2026");
  await h.advance(1000);await h.frame();h.requests[1].ok(record("08-09-2026","UTC","new"));await settle();old.ok(record("08-09-2026","UTC","late"));await settle();
  assert.throws(()=>assert.notEqual(h.state().tomorrow?.date.gregorian.date,"08-09-2026"));
});
test("R0005 mutant removing dirty consumer is killed by frozen async visible resume",async()=>{
  const before="sec!==_lastSec || _renderDirty";assert.equal(source().split(before).length-1,1);
  const h=harness({source:source().replace(before,"sec!==_lastSec"),hash:"#lat=10&lon=10&tz=UTC&method=2&simTime=12:00"});h.seed(record());h.run("startRenderLoop()");await h.frame();h.hide();const beforePaint=h.paints.length;
  req(h,"08-09-2026").ok(record("08-09-2026"));await settle();h.show();await h.frame();assert.throws(()=>assert.equal(h.paints.length,beforePaint+1));
});
