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
