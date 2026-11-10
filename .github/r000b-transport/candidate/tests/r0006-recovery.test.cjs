"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const {source,copy,record,harness,cfg,req,settle}=require("./r0003-harness.cjs");
test("R0006 stalled headers settle three whole attempts by 32.7 seconds and start recovery loop",async()=>{
  const h=harness();let settled=false;(await h.startBoot()).pending.then(()=>{settled=true;});await h.advance(32700);
  assert.equal(settled,true);assert.equal(h.state()._loopStarted,true);assert.equal(h.requests.filter(r=>r.url.includes("/timings/")).length,3);
});

test("R0006 stalled body is covered by same whole-attempt deadline",async()=>{
  const h=harness();let settled=false;(await h.startBoot()).pending.then(()=>{settled=true;});req(h).headers.resolve({ok:true,status:200,json:()=>req(h).body.promise});await h.advance(32700);
  assert.equal(settled,true);assert.equal(h.state().today,null);
});

test("R0006 positive two prompt failures preserve third success with 900/1800 backoffs",async()=>{
  const h=harness(),boot=(await h.startBoot()).pending;req(h).fail();await h.advance(900);h.requests[1].fail();await h.advance(2700);h.requests[2].ok(record(undefined,"UTC","third-success"));await settle();await boot;
  assert.equal(h.state().today.tag,"third-success");assert.deepEqual(h.requests.slice(0,3).map(r=>r.at),[0,900,2700]);
});

test("R0006 same-day cold failure recovers at real elapsed 60s without midnight or wall clock",async()=>{
  const h=harness({offline:true}),boot=(await h.startBoot()).pending;await h.advance(2700);await boot;assert.equal(h.state().today,null);
  h.wallBy(-3600000);await h.advance(59000);await h.frame();assert.equal(h.requests.length,3);await h.advance(60000);await h.frame();assert.equal(h.requests.length,4);
});

test("R0006 deadline trace is 0/10900/22700; terminal operation clears timers and busy",async()=>{
  const h=harness(),boot=(await h.startBoot()).pending;await h.advance(32700);await boot;
  assert.deepEqual(h.requests.map(r=>r.at),[0,10900,22700]);assert.equal(h.timers.size,0);assert.equal(h.run("_requestSlots.current"),null);assert.equal(h.run("_rolloverBusy"),false);assert.equal(h.state()._loopStarted,true);
});
test("R0006 late old body after timeout cannot overwrite healthy retry or produce an unhandled rejection",async()=>{
  const h=harness(),boot=(await h.startBoot()).pending,late=req(h);late.headers.resolve({ok:true,status:200,json:()=>late.body.promise});await h.advance(10900);
  h.requests[1].ok(record(undefined,"UTC","retry-current"));await settle();await boot;const before={state:h.state(),writes:copy(h.writes),errors:copy(h.errors)};
  late.body.resolve({code:200,status:"OK",data:record(undefined,"Asia/Riyadh","expired-body")});await settle();assert.deepEqual({state:h.state(),writes:copy(h.writes),errors:copy(h.errors)},before);
});
test("R0006 delayed timeout callback cannot admit a body beyond real elapsed deadline",async()=>{
  const h=harness(),boot=(await h.startBoot()).pending,late=req(h);late.headers.resolve({ok:true,status:200,json:()=>late.body.promise});await settle();h.elapse(10001);
  late.body.resolve({code:200,status:"OK",data:record(undefined,"UTC","expired")});await settle();assert.equal(h.state().today,null);assert.equal(h.writes.length,0);
  await h.advance(10901);h.requests[1].ok(record(undefined,"UTC","healthy-retry"));await settle();await boot;assert.equal(h.state().today.tag,"healthy-retry");
});
test("R0006 recovered same-day network at elapsed60s paints without reload or midnight",async()=>{
  const options={offline:true},h=harness(options),boot=(await h.startBoot()).pending;await h.advance(2700);await boot;options.offline=false;
  await h.advance(59000);await h.frame();assert.equal(h.requests.length,3);await h.advance(60000);await h.frame();assert.equal(h.requests.length,4);
  h.requests[3].ok(record(undefined,"UTC","restored"));await settle();await h.frame();assert.equal(h.state().today.tag,"restored");assert.equal(h.paints.at(-1).today.tag,"restored");assert.equal(h.state().lastDate,"07-09-2026");
});
for(const [name,hash,step]of [
  ["forward wall",undefined,3600000],["backward wall",undefined,-3600000],
  ["frozen scene","#lat=10&lon=10&tz=UTC&method=2&simTime=12:00",0],
  ["accelerated same-day scene","#lat=10&lon=10&tz=UTC&method=2&simTime=00:00&timeScale=120",3600000]
])test(`R0006 ${name} retains real elapsed cold retry eligibility`,async()=>{
  const h=harness({offline:true,...(hash?{hash}: {})}),boot=(await h.startBoot()).pending;await h.advance(2700);await boot;h.wallBy(step);
  await h.advance(59000);await h.frame();assert.equal(h.requests.length,3);await h.advance(60000);await h.frame();assert.equal(h.requests.length,4);
});
test("R0006 hidden cooldown schedules one current operation on eligible visible resume",async()=>{
  const options={offline:true},h=harness(options),boot=(await h.startBoot()).pending;await h.advance(2700);await boot;h.hide();options.offline=false;
  await h.advance(180000);assert.equal(h.requests.length,3);assert.equal(h.frames.size,0);h.show();await h.frame();assert.equal(h.requests.length,4);assert.equal(h.requests.at(-1).at,180000);
  for(let i=0;i<20;i++){await h.advance(h.elapsed()+16);await h.frame();}assert.equal(h.requests.length,4);
});
async function storm(raw=source()){
  const h=harness({source:raw,offline:true});h.seed(record());h.run("render();startRenderLoop()");
  for(let i=0;i<66;i++){await h.advance(i*1000);await h.frame();}
  return h;
}
test("R0006 66 actual render opportunities with real retry delays make exactly six low-level starts",async()=>{
  const h=await storm();assert.deepEqual(h.requests.map(r=>r.at),[0,900,2700,60000,60900,62700]);assert.equal(h.state().fetchingTomorrow,false);assert.equal(h.timers.size,0);
});
test("R0006 mutant removing cooldown is killed by the same 66-opportunity schedule",async()=>{
  const before="if(cooldown && cooldown.day===day && elapsed<cooldown.nextTry) return null;";assert.equal(source().split(before).length-1,1);
  const h=await storm(source().replace(before,""));assert.throws(()=>assert.ok(h.requests.length<=6));console.log(JSON.stringify({cooldownMutantRequests:h.requests.length}));
});
test("R0006 mutant removing cold branch is killed by same-day recovery",async()=>{
  const before="if(!prayerRecordReady(today,day) && !_requestSlots.current) loadPrayerData();";assert.equal(source().split(before).length-1,1);
  const h=harness({source:source().replace(before,""),offline:true}),boot=(await h.startBoot()).pending;await h.advance(2700);await boot;await h.advance(60000);await h.frame();assert.throws(()=>assert.equal(h.requests.length,4));
});
test("R0006 mutant removing deadline recreates indefinitely pending headers",async()=>{
  const before="a.timer=setTimeout(a.cancel,10000);";assert.equal(source().split(before).length-1,1);
  const h=harness({source:source().replace(before,"")});let settled=false;(await h.startBoot()).pending.then(()=>{settled=true;});await h.advance(32700);assert.throws(()=>assert.equal(settled,true));assert.equal(h.requests.length,1);
});
test("R0006 headers-only deadline mutant is killed by stalled actual response body",async()=>{
  const before='if(r.ok!==true) throw new Error("bad api HTTP");\n          const j=await r.json();';assert.equal(source().split(before).length-1,1);
  const h=harness({source:source().replace(before,'if(r.ok!==true) throw new Error("bad api HTTP");\n          clearTimeout(a.timer); a.timer=null;\n          const j=await r.json();')});let settled=false;(await h.startBoot()).pending.then(()=>{settled=true;});const held=req(h);held.headers.resolve({ok:true,status:200,json:()=>held.body.promise});await h.advance(32700);assert.throws(()=>assert.equal(settled,true));assert.equal(h.requests.length,1);
});
