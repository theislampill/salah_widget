"use strict";
// Retained October 8 R0004 controls, rebound to the current delivered source.
const test=require("node:test"),assert=require("node:assert/strict"),crypto=require("node:crypto");
const {source,record,harness,req,settle}=require("./r0003-harness.cjs");
const sha=x=>crypto.createHash("sha256").update(x).digest("hex");
const key="salah:35.68|139.69|America/New_York|2|0";
function variant(before,after){const raw=source();assert.equal(raw.split(before).length,2);return raw.replace(before,after);}
test("R0004 retained omitted-hint same-day12Z control needs no correction",async()=>{
  const h=harness({epoch:"2026-09-07T12:00:00Z",hash:"#lat=35.68&lon=139.69&method=2"}),boot=h.boot();
  req(h).ok(record("07-09-2026","Asia/Tokyo","same-day"));await settle();await boot;
  assert.equal(h.state().today.tag,"same-day");assert.equal(h.state().lastDate,"07-09-2026");assert.equal(h.state().tz,"Asia/Tokyo");
  assert.equal(h.requests.filter(r=>r.url.includes("/timings/07-09-2026?")).length,1);
  assert.ok(h.requests.every(r=>!r.url.includes("/timings/08-09-2026?")||h.run("_requestSlots.prefetch")!==null));
});
test("R0004 retained early-filter mutant loses offline availability; explicit hint survives",async()=>{
  const raw=variant("const cached=readPrayerCache(op.cacheKey);","const rawCached=readPrayerCache(op.cacheKey); const cached=rawCached && rawCached.date===prayerCivilDay() ? rawCached : null;");
  const bytes=JSON.stringify({date:"08-09-2026",data:record("08-09-2026","Asia/Tokyo","cached8")});
  for(const explicit of [false,true]){
    const h=harness({source:raw,epoch:"2026-09-07T22:00:00Z",hash:"#lat=35.68&lon=139.69&method=2"+(explicit?"&tz=Asia%2FTokyo":""),offline:true});
    const selected=explicit?key.replace("America/New_York","Asia/Tokyo"):key;h.storage.set(selected,bytes);
    const boot=h.boot();await h.advance(2700);await boot;
    assert.equal(h.state().today?.tag??null,explicit?"cached8":null);assert.equal(h.storage.get(selected),bytes);
  }
  console.log(JSON.stringify({variant:"early-cache-filter",sourceSha256:sha(raw),result:"offline availability lost; explicit control retained"}));
});
test("R0004 retained removed-correction mutant is contained by independent adoption",async()=>{
  const raw=variant("if(day!==requested){","if(false){");
  for(const explicit of [false,true]){
    const day=explicit?"08-09-2026":"07-09-2026",h=harness({source:raw,epoch:"2026-09-07T22:00:00Z",hash:"#lat=35.68&lon=139.69&method=2"+(explicit?"&tz=Asia%2FTokyo":"")}),boot=h.boot();
    req(h,day).ok(record(day,"Asia/Tokyo","response"));await settle();await boot;
    assert.equal(h.state().today?.tag??null,explicit?"response":null);
    if(!explicit){assert.equal(h.paints.length,0);assert.equal(h.requests.length,1);}
  }
  console.log(JSON.stringify({variant:"removed-day-check",sourceSha256:sha(raw),result:"no current paint; independent classifier prevents false current; explicit control retained"}));
});
