"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const {source,copy,record,harness,cfg,req,settle}=require("./r0003-harness.cjs");
test("R0004 empty Tokyo cache: first accepted current paint is resolved-zone day 8",async()=>{
  const h=harness({epoch:"2026-09-07T22:00:00Z",hash:"#lat=35.68&lon=139.69&method=2"}),boot=h.boot();
  req(h).ok(record("07-09-2026","Asia/Tokyo","bootstrap"));await settle();
  const corrected=req(h,"08-09-2026");if(corrected){corrected.ok(record("08-09-2026","Asia/Tokyo","corrected"));await settle();}
  await boot;const current=h.paints.filter(p=>!p._prayerStale);assert.ok(current.length>0);assert.equal(current[0].today.date.gregorian.date,"08-09-2026");
});

test("R0004 selected main cache: valid resolved day 8 cache survives offline wrong hint",async()=>{
  const h=harness({epoch:"2026-09-07T22:00:00Z",hash:"#lat=35.68&lon=139.69&method=2",offline:true});
  h.storage.set("salah:35.68|139.69|America/New_York|2|0",JSON.stringify({date:"08-09-2026",data:record("08-09-2026","Asia/Tokyo","cached8")}));
  const boot=h.boot();await h.advance(2700);await boot;assert.equal(h.state().today?.tag,"cached8");assert.equal(h.state().tz,"Asia/Tokyo");assert.ok(h.paints.some(p=>p.today.tag==="cached8"));
});

test("R0004 positive explicitly matching Tokyo day 8 cache survives offline refresh",async()=>{
  const h=harness({epoch:"2026-09-07T22:00:00Z",hash:"#lat=35.68&lon=139.69&tz=Asia%2FTokyo&method=2",offline:true});
  h.storage.set("salah:35.68|139.69|Asia/Tokyo|2|0",JSON.stringify({date:"08-09-2026",data:record("08-09-2026","Asia/Tokyo","cached8")}));
  const boot=h.boot();await h.advance(2700);await boot;assert.equal(h.state().today?.tag,"cached8");assert.equal(h.state().tz,"Asia/Tokyo");
});

const selected="salah:35.68|139.69|America/New_York|2|0",zoneFree="salah:35.68|139.69|2|0";
test("R0004 wrong-day valid Tokyo cache cannot paint as current while offline",async()=>{
  const h=harness({epoch:"2026-09-07T22:00:00Z",hash:"#lat=35.68&lon=139.69&method=2",offline:true}),bytes=JSON.stringify({date:"07-09-2026",data:record("07-09-2026","Asia/Tokyo","old7")});h.storage.set(selected,bytes);
  const boot=h.boot();await h.advance(2700);await boot;assert.equal(h.state().today,null);assert.equal(h.paints.length,0);assert.equal(h.state().tz,"Asia/Tokyo");assert.equal(h.storage.get(selected),bytes);assert.equal(h.writes.length,0);
  assert.ok(h.requests.every(r=>r.url.includes("/timings/08-09-2026?")));
});
test("R0004 zone-free-only cache remains a miss; no scanning or deletion",async()=>{
  const h=harness({epoch:"2026-09-07T22:00:00Z",hash:"#lat=35.68&lon=139.69&method=2",offline:true});h.storage.set(zoneFree,JSON.stringify({date:"08-09-2026",data:record("08-09-2026","Asia/Tokyo","unselected")}));
  const boot=h.boot();await h.advance(2700);await boot;assert.equal(h.state().today,null);assert.equal(h.state().tz,"America/New_York");assert.equal(h.storage.has(zoneFree),true);
  assert.ok(h.reads.every(k=>k===selected));
});
test("R0004 both key variants choose only valid main envelope and preserve its bytes",async()=>{
  const h=harness({epoch:"2026-09-07T22:00:00Z",hash:"#lat=35.68&lon=139.69&method=2",offline:true}),bytes=JSON.stringify({date:"08-09-2026",data:record("08-09-2026","Asia/Tokyo","main")});
  h.storage.set(selected,bytes);h.storage.set(zoneFree,JSON.stringify({date:"08-09-2026",data:record("08-09-2026","UTC","unselected")}));
  const boot=h.boot();await h.advance(2700);await boot;assert.equal(h.state().today.tag,"main");assert.equal(h.storage.get(selected),bytes);assert.equal(h.writes.length,0);assert.ok(h.reads.every(k=>k===selected));
});
test("R0004 corrupt selected envelope cannot establish zone; healthy corrected body recovers",async()=>{
  const h=harness({epoch:"2026-09-07T22:00:00Z",hash:"#lat=35.68&lon=139.69&method=2"});h.storage.set(selected,'{"date":"08-09-2026","data":{"meta":{"timezone":"Asia/Tokyo"}}}');
  const boot=h.boot();assert.equal(h.state().tz,"America/New_York");req(h).ok(record("07-09-2026","Asia/Tokyo","bootstrap"));await settle();
  req(h,"08-09-2026").ok(record("08-09-2026","Asia/Tokyo","corrected"));await settle();await boot;assert.equal(h.state().today.tag,"corrected");assert.ok(h.paints.every(p=>p.today.date.gregorian.date==="08-09-2026"));
});
test("R0004 correction still validates body identity; budget cannot make a third day request",async()=>{
  const h=harness({epoch:"2026-09-07T22:00:00Z",hash:"#lat=35.68&lon=139.69&method=2"}),boot=h.boot();req(h).ok(record("07-09-2026","Asia/Tokyo","bootstrap"));await settle();
  req(h,"08-09-2026").ok(record("09-09-2026","Asia/Tokyo","wrong-correction"));await h.advance(1800);h.requests.at(-1).ok(record("09-09-2026","Asia/Tokyo","wrong-again"));await settle();await boot;
  assert.equal(h.requests.length,3);assert.equal(h.state().today,null);assert.equal(h.paints.length,0);assert.ok(h.requests.every(r=>!r.url.includes("/09-09-2026?")));
});
