/* Actual wrapper hooks/transport under VM; DOM parsing is deliberately stopped.
 * These controls do not execute/qualify the widget or replace native smoke runs. */
"use strict";
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict"),crypto=require("node:crypto");
const root=path.resolve(process.argv[2]||path.join(__dirname,".."));
const index=fs.readFileSync(path.join(root,"index.html")),wrapper=fs.readFileSync(path.join(root,"tests/widget-fixture.html"),"utf8");
const script=[...wrapper.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)][0][1];
const todayURL="https://api.aladhan.com/v1/timings/07-09-2026?latitude=24.47&longitude=39.61&method=4&school=0";
const tomorrowURL="https://api.aladhan.com/v1/timings/08-09-2026?latitude=24.47&longitude=39.61&method=4&school=0";
async function setup(mode="healthy",options={}){
  let sourceCalls=0,realStorageCalls=0;const errorEl={};
  const source=options.source??index;
  const ctx=vm.createContext({URL,URLSearchParams,Date,DOMException,Response,TextDecoder,Uint8Array,console,
    crypto:crypto.webcrypto,location:{search:"?mode="+mode+"&attempt=1",hash:"#lat=24.47&lon=39.61&method=4&simWx=0&tz=Asia/Riyadh&qa=1",href:"http://127.0.0.1:8765/tests/widget-fixture.html"},
    document:{getElementById(){return errorEl;}},
    DOMParser:class{parseFromString(){throw Error("Controlled parser stop: VM is not a browser");}},
    fetch(input){sourceCalls++;assert.equal(String(input),"http://127.0.0.1:8765/index.html");
      if(options.rejectSource)return Promise.reject(Error("Controlled source fetch rejection"));
      return Promise.resolve(new Response(source,{status:options.status??200}));}
  });ctx.window=ctx;
  Object.defineProperty(ctx,"localStorage",{configurable:true,get(){realStorageCalls++;throw Error("Real storage access forbidden");}});
  // Expose completion of the existing wrapper IIFE, changing no transport logic.
  const exposed=script.replace("start().catch(failure);","return start().catch(failure);");
  assert.notEqual(exposed,script,"wrapper completion anchor missing");
  await vm.runInContext(exposed,ctx,{filename:"actual widget-fixture script (parser deliberately stopped)"});
  return {ctx,report:ctx.__widgetFixture,errorEl,sourceCalls,realStorageCalls};
}
const results=[];
async function check(name,fn){try{await fn();results.push({name,result:"PASS"});}catch(e){results.push({name,result:"FAIL",error:e.message});}}
async function main(){
  await check("actual wrapper loads source digest and isolates all hooks before parser",async()=>{
    const h=await setup();assert.equal(h.sourceCalls,1);assert.equal(h.realStorageCalls,0);
    assert.equal(h.report.sourceSha256,crypto.createHash("sha256").update(index).digest("hex"));
    assert.equal(h.report.initialStorageEntries,0);assert.equal(h.report.storageIsolated,true);assert.equal(h.report.clockFixed,true);assert.equal(h.report.fetchIntercepted,true);
    assert.match(h.report.error,/Controlled parser stop/);assert.match(h.errorEl.textContent,/Fixture bootstrap error/);
    assert.equal(h.ctx.Date.now(),1788773400000);assert.equal(new h.ctx.Date().toISOString(),"2026-09-07T09:30:00.000Z");
    assert.equal(new h.ctx.Date(0).toISOString(),"1970-01-01T00:00:00.000Z");assert.equal(h.ctx.Date.UTC(1970,0,1),0);assert.equal(h.ctx.Date.parse("1970-01-01T00:00:00Z"),0);
  });
  await check("healthy transport uses real Response/json and distinct synthetic dates",async()=>{
    const h=await setup(),today=await h.ctx.fetch(todayURL,{cache:"no-store"}),tomorrow=await h.ctx.fetch(new URL(tomorrowURL));
    assert.equal(today.ok,true);assert.equal(today.headers.get("Content-Type"),"application/json");
    const a=await today.json(),b=await tomorrow.json();
    assert.equal(a.data.timings.Asr,"15:30");assert.equal(a.data.meta.timezone,"Asia/Riyadh");
    assert.equal(a.data.date.gregorian.date,"07-09-2026");assert.equal(b.data.date.gregorian.date,"08-09-2026");assert.equal(b.data.date.gregorian.day,"08");
    assert.equal(h.report.ledger.length,2);assert.ok(h.report.ledger.every(r=>r.jsonReads===1&&r.result==="json-consumed"));assert.equal(h.sourceCalls,1);
  });
  await check("controlled rejection has no JSON reads/network fallback",async()=>{
    const h=await setup("reject");await assert.rejects(h.ctx.fetch(todayURL),/Controlled prayer rejection/);
    assert.equal(h.report.ledger[0].result,"rejected");assert.equal(h.report.ledger[0].jsonReads,0);assert.equal(h.sourceCalls,1);
  });
  await check("controlled hang remains pending with no JSON/network fallback",async()=>{
    const h=await setup("hang"),marker=Symbol("pending");
    assert.equal(await Promise.race([h.ctx.fetch(todayURL),new Promise(resolve=>setTimeout(()=>resolve(marker),10))]),marker);
    assert.equal(h.report.ledger[0].result,"pending");assert.equal(h.report.ledger[0].jsonReads,0);assert.equal(h.sourceCalls,1);
  });
  for(const mode of ["bootstrap-error","unknown"])await check("pre-parse fixture "+mode+" is explicit error with no source/storage",async()=>{
    const h=await setup(mode);assert.equal(h.report.state,"error");assert.equal(h.sourceCalls,0);assert.equal(h.realStorageCalls,0);
    assert.match(h.report.error,mode==="unknown"?/Unknown fixture mode/:/Controlled fixture bootstrap failure/);
  });
  for(const url of [todayURL.replace("latitude=24.47","latitude=24.48"),todayURL+"&extra=1",todayURL.replace("07-09-2026","09-09-2026"),"https://api.open-meteo.com/v1/forecast"])await check("transport rejects unadmitted request "+url,async()=>{
    const h=await setup();await assert.rejects(h.ctx.fetch(url),/Unexpected fixture request/);
    assert.equal(h.report.ledger[0].result,"unexpected-request");assert.equal(h.report.ledger[0].jsonReads,0);assert.equal(h.sourceCalls,1);
  });
  await check("source fetch rejection fails before hook installation",async()=>{
    const h=await setup("healthy",{rejectSource:true});assert.match(h.report.error,/Controlled source fetch rejection/);assert.equal(h.report.storageIsolated,false);assert.equal(h.realStorageCalls,0);
  });
  await check("changed script anchor fails before hook installation",async()=>{
    const changed=index.toString("utf8").replace('<script src="config.js"></script>','<script src="other.js"></script>');
    const h=await setup("healthy",{source:changed});assert.match(h.report.error,/Unreviewed widget script anchors/);assert.equal(h.report.storageIsolated,false);assert.equal(h.realStorageCalls,0);
  });
  console.log(JSON.stringify({kind:"source-bound wrapper transport/hooks; controlled parser stop, no widget/native qualification",root,
    indexSha256:crypto.createHash("sha256").update(index).digest("hex"),wrapperSha256:crypto.createHash("sha256").update(wrapper).digest("hex"),results},null,2));
  if(results.some(r=>r.result==="FAIL"))process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
