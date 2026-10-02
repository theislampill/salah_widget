"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const {source,copy,record,harness,cfg,req,settle}=require("./r0003-harness.cjs");
test("R0006 stalled headers settle three whole attempts by 32.7 seconds and start recovery loop",async()=>{
  const h=harness();let settled=false;h.boot().then(()=>{settled=true;});await h.advance(32700);
  assert.equal(settled,true);assert.equal(h.state()._loopStarted,true);assert.equal(h.requests.filter(r=>r.url.includes("/timings/")).length,3);
});

test("R0006 stalled body is covered by same whole-attempt deadline",async()=>{
  const h=harness();let settled=false;h.boot().then(()=>{settled=true;});req(h).headers.resolve({ok:true,status:200,json:()=>req(h).body.promise});await h.advance(32700);
  assert.equal(settled,true);assert.equal(h.state().today,null);
});

test("R0006 positive two prompt failures preserve third success with 900/1800 backoffs",async()=>{
  const h=harness(),boot=h.boot();req(h).fail();await h.advance(900);h.requests[1].fail();await h.advance(2700);h.requests[2].ok(record(undefined,"UTC","third-success"));await settle();await boot;
  assert.equal(h.state().today.tag,"third-success");assert.deepEqual(h.requests.slice(0,3).map(r=>r.at),[0,900,2700]);
});

test("R0006 same-day cold failure recovers at real elapsed 60s without midnight or wall clock",async()=>{
  const h=harness({offline:true}),boot=h.boot();await h.advance(2700);await boot;assert.equal(h.state().today,null);
  h.wallBy(-3600000);await h.advance(59000);await h.frame();assert.equal(h.requests.length,3);await h.advance(60000);await h.frame();assert.equal(h.requests.length,4);
});
