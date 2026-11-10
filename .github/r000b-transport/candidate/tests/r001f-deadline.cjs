"use strict";
const assert=require("node:assert/strict"),vm=require("node:vm"),{fixture,readSource,deferred,drain}=require("./r000f-fixture.cjs");
const {widget}=require("./r0011-fixture.cjs");
const ref=process.argv.includes("--ref")?process.argv[process.argv.indexOf("--ref")+1]:undefined;
const mutant=process.argv.includes("--mutant")?process.argv[process.argv.indexOf("--mutant")+1]:undefined;
const geo={latitude:"24.47",longitude:"39.61",city:"Madinah",country_code:"SA",timezone:"Asia/Riyadh",accuracy:"5"};
const ip={loc:"51.5,-0.12",city:"London",country:"GB",timezone:"Europe/London"};
function make(realTime=false) {
  const timers=new Map(),requests=[];let id=0;
  const context={URLSearchParams,AbortController,Intl,Date,
    setTimeout:realTime?setTimeout:(fn,ms)=>{const key=++id;timers.set(key,{fn,ms});return key;},
    clearTimeout:realTime?clearTimeout:key=>timers.delete(key),
    fetch:(url,opts)=>{const d=deferred();requests.push({url,opts,...d});return d.promise;}};
  context.window=context;vm.createContext(context);
  let source=readSource("config.js",ref);
  if(mutant==="headers")source=source.replace('.then(function (r) { if (!r.ok)', '.then(function (r) { clearTimeout(to); if (!r.ok)');
  if(mutant==="abort-only")source=source.replace('reject(new Error("coarse location timeout"));','');
  vm.runInContext(source,context);
  function fire(){assert.equal(timers.size,1,"attempt must still own its deadline");const [key,timer]=[...timers][0];timers.delete(key);timer.fn();}
  return {context,timers,requests,fire,run:opts=>context.SalahConfig.coarseDetect(opts)};
}
const cases=[],test=(name,body)=>cases.push({name,body});
test("body stall retains deadline and advances exactly once before late resolution",async()=>{
  const f=make(),body=deferred();let completions=0,value;
  f.run({timeoutMs:5}).then(v=>{value=v;completions++;});await drain();assert.equal(f.requests.length,1);
  f.requests[0].resolve({ok:true,json:()=>body.promise});await drain();assert.equal(f.timers.size,1,"deadline survives successful headers");assert.equal(completions,0);
  f.fire();await drain();assert.equal(f.requests[0].opts.signal.aborted,true);assert.equal(f.requests.length,2,"timeout owns one fallback");
  f.requests[1].resolve({ok:true,json:async()=>ip});await drain();assert.equal(value.provider,"ipinfo");assert.equal(value.cfg.lat,51.5);assert.equal(completions,1);assert.equal(f.timers.size,0);
  body.resolve(geo);await drain();assert.equal(completions,1);assert.equal(f.requests.length,2);
});
test("healthy GeoJS body retains original shape, timezone precedence and cleans timer",async()=>{
  const f=make(),p=f.run({timeoutMs:5});await drain();f.requests[0].resolve({ok:true,json:async()=>geo});const r=await p;
  assert.equal(r.ok,true);assert.equal(r.provider,"GeoJS");assert.equal(r.source,"coarse-ip");assert.equal(r.status,"ok");assert.deepEqual([r.cfg.lat,r.cfg.lon,r.cfg.method,r.cfg.units],[24.47,39.61,"4","c"]);assert.equal(r.cfg.tz,Intl.DateTimeFormat().resolvedOptions().timeZone);assert.equal(f.requests.length,1);assert.equal(f.timers.size,0);
});
test("both hung attempts exhaust with no third request or active timer",async()=>{
  const f=make();let value;f.run({timeoutMs:5}).then(v=>value=v);await drain();f.fire();await drain();assert.equal(f.requests.length,2);f.requests[1].resolve({ok:true,json:()=>new Promise(()=>{})});await drain();f.fire();await drain();assert.deepEqual(JSON.parse(JSON.stringify(value)),{ok:false,source:"coarse-ip",status:"failed"});assert.equal(f.requests.length,2);assert.equal(f.timers.size,0);
});
for(const [name,response] of [
  ["HTTP failure",{ok:false,status:503}],
  ["JSON rejection",{ok:true,json:()=>Promise.reject(new SyntaxError("incomplete"))}],
  ["unusable coords",{ok:true,json:async()=>({latitude:"unknown",longitude:"unknown"})}]
])test(`${name} reaches healthy fallback and removes old timer`,async()=>{
  const f=make(),p=f.run({timeoutMs:5});await drain();f.requests[0].resolve(response);await drain();assert.equal(f.requests.length,2);assert.equal(f.timers.size,1);f.requests[1].resolve({ok:true,json:async()=>ip});assert.equal((await p).provider,"ipinfo");assert.equal(f.timers.size,0);
});
test("body wins before deadline while deadline wins reversed schedule",async()=>{
  const f=make(),body=deferred(),p=f.run({timeoutMs:5});await drain();f.requests[0].resolve({ok:true,json:()=>body.promise});await drain();assert.equal(f.timers.size,1,"body still owns timer");const oldTimer=[...f.timers.values()][0];
  body.resolve(geo);assert.equal((await p).provider,"GeoJS");oldTimer.fn();await drain();assert.equal(f.requests.length,1);assert.equal(f.timers.size,0);
});
test("old body rejection stays handled after fallback succeeds",async()=>{
  const errors=[],listener=error=>errors.push(error);process.on("unhandledRejection",listener);
  try {const f=make(),body=deferred();let value;f.run({timeoutMs:5}).then(v=>value=v);await drain();f.requests[0].resolve({ok:true,json:()=>body.promise});await drain();assert.equal(f.timers.size,1);f.fire();await drain();assert.equal(f.requests.length,2);f.requests[1].resolve({ok:true,json:async()=>ip});await drain();body.reject(new Error("late"));await new Promise(resolve=>setImmediate(resolve));assert.equal(value.provider,"ipinfo");assert.equal(f.requests.length,2);assert.deepEqual(errors,[]);}
  finally{process.removeListener("unhandledRejection",listener);}
});
test("timeoutMs zero retains default six-second option",async()=>{
  const f=make(),p=f.run({timeoutMs:0});await drain();assert.equal([...f.timers.values()][0].ms,6000);f.requests[0].resolve({ok:true,json:async()=>geo});await p;
});
test("real elapsed body wait returns bounded fallback without transport cooperation",async()=>{
  const f=make(true),started=performance.now(),original=f.context.fetch;let value;
  f.context.fetch=(url,opts)=>{const p=original(url,opts);if(url.includes("ipinfo"))f.requests.at(-1).resolve({ok:true,json:async()=>ip});return p;};
  f.run({timeoutMs:20}).then(v=>value=v);await drain();f.requests[0].resolve({ok:true,json:()=>new Promise(()=>{})});
  await new Promise(resolve=>setTimeout(resolve,40));assert.equal(f.requests.length,2);const elapsed=performance.now()-started;assert.equal(value?.provider,"ipinfo");assert.ok(elapsed>=20 && elapsed<1000,`elapsed ${elapsed}`);console.log(JSON.stringify({realElapsedMs:elapsed,instrument:"Node event-loop/deferred-body; browser stream NOT_RUN"}));
});
test("actual local boot exhaustion opens manual settings and render loop",async()=>{
  const c=make(),f=widget({ref,open:false});f.sandbox.SalahConfig.coarseDetect=()=>c.run({timeoutMs:5});const p=f.boot();await drain();c.fire();await drain();assert.equal(c.requests.length,2);c.fire();await drain();
  // Do not await an unsettled RED: the real caller must already have recovered.
  assert.equal(f.run("_autoDetectStatus"),"failed");await p;
  assert.equal(f.run("_autoDetectStatus"),"failed");assert.equal(f.card.classList.contains("settings-open"),true);assert.equal(f.calls.loop,1);assert.equal(f.calls.prayer.length,0);assert.match(f.elements.get("set-status").textContent,/Enter to search/);
});
test("actual builder exhaustion offers manual recovery",async()=>{
  const c=make(),f=fixture("builder",{ref});f.sandbox.SalahConfig.coarseDetect=()=>c.run({timeoutMs:5});f.run("detectArea()");await drain();c.fire();await drain();assert.equal(c.requests.length,2);c.fire();await drain();assert.match(f.elements.get("geotip").textContent,/Couldn’t detect.*type a place/);assert.equal(f.elements.get("geo").classList.contains("off"),true);
});
test("new builder edit rejects fallback location and feedback",async()=>{
  const c=make(),f=fixture("builder",{ref});f.sandbox.SalahConfig.coarseDetect=()=>c.run({timeoutMs:5});f.run("detectArea()");await drain();c.fire();await drain();assert.equal(c.requests.length,2);f.input("lat","30");f.input("lon","31");const before=f.snapshot();c.requests[1].resolve({ok:true,json:async()=>ip});await drain();assert.equal(f.snapshot(),before);
});
(async()=>{let failed=0;for(const c of cases){try{await c.body();console.log("PASS",c.name);}catch(e){failed++;console.error("FAIL",c.name,"\n",e.stack);}}console.log(JSON.stringify({cases:cases.length,passed:cases.length-failed,failed,ref:ref||"working-tree",mutant:mutant||null,native:"NOT_RUN"}));process.exitCode=failed?1:0;})();
