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
