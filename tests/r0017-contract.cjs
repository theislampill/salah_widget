/* R0017: source-bound storage and unavailable-widget controls. No browser/network. */
"use strict";
const fs=require("node:fs"), path=require("node:path"), vm=require("node:vm"), assert=require("node:assert/strict");
const root=path.resolve(process.argv.slice(2).find(a=>!a.startsWith("--"))||path.join(__dirname,".."));
const configSource=fs.readFileSync(path.join(root,"config.js"),"utf8");
const smokeSource=fs.readFileSync(path.join(root,"tests/smoke.html"),"utf8");
const key="salah_widget:config:v1";
const saved='{"v":1,"lat":12,"lon":34,"label":"fixture-user-setting","method":"4","savedAt":42}';
class MemoryStorage {
  constructor(raw=saved){this.data=new Map([["unrelated-origin-key","retained"]]);if(raw!==null)this.data.set(key,raw);this.calls=[];}
  getItem(k){this.calls.push(["get",k]);return this.data.has(k)?this.data.get(k):null;}
  setItem(k,v){this.calls.push(["set",k]);this.data.set(k,String(v));}
  removeItem(k){this.calls.push(["remove",k]);this.data.delete(k);}
}
function configContext(storage,{throwGetter=false,source=configSource}={}){
  const ctx=vm.createContext({URLSearchParams,Date,Intl,DOMException,console});ctx.window=ctx;
  Object.defineProperty(ctx,"localStorage",{get(){if(throwGetter)throw new DOMException("blocked","SecurityError");return storage;}});
  vm.runInContext(source,ctx,{filename:"config.js"});return ctx;
}
function harness(configPresent=true,raw=saved,source=smokeSource){
  let ticks=0,nextTimer=0;const timers=new Set(),log=[],storage=new MemoryStorage(raw),elements={out:{appendChild(s){log.push({class:s.className,text:s.textContent});}},sum:{},w:{contentWindow:null}};
  class Clock extends Date{static now(){return 1800000000000+ticks;}}
  const ctx=vm.createContext({URLSearchParams,URL,Storage:MemoryStorage,localStorage:storage,Date:Clock,Intl,DOMException,console,
    location:{search:"",href:"http://127.0.0.1/tests/smoke.html"},
    document:{getElementById(k){return elements[k];},createElement(){return {}; }},
    setTimeout(fn,ms){const id=++nextTimer;timers.add(id);setImmediate(()=>{if(timers.delete(id)){ticks+=ms;fn();}});return id;},clearTimeout(id){timers.delete(id);},
    fetch(){throw Error("Network prohibited in instrument fixture");}});ctx.window=ctx;
  if(configPresent)vm.runInContext(configSource,ctx,{filename:"config.js"});
  const script=[...source.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].find(m=>! /\bsrc\s*=/.test(m[1]))[2];
  return {ctx,storage,log,elements,script};
}
async function unavailable(configPresent=true,raw=saved,source=smokeSource){
  const {ctx,storage,log,elements,script}=harness(configPresent,raw,source);
  await vm.runInContext(script,ctx,{filename:"tests/smoke.html"});
  return {summary:elements.sum.textContent,className:elements.sum.className,smoke:ctx.__smoke,before:raw,
    after:storage.data.get(key)??null,unrelated:storage.data.get("unrelated-origin-key"),realStorageCalls:storage.calls,log};
}
function replaceOnce(source,from,to){assert.equal(source.split(from).length,2,"mutation/driver anchor is not unique");return source.replace(from,to);}
function helperHarness(source=smokeSource,raw=saved){
  const result=harness(true,raw,source);
  const driver='(async()=>{try{await run();}catch(e){line("fail","harness error: "+e.message);}finally{finalize();}})();';
  vm.runInContext(replaceOnce(result.script,driver,""),result.ctx,{filename:"actual smoke helpers (driver held)"});return result;
}
const results=[];
async function check(name,fn){try{await fn();results.push({name,result:"PASS"});}catch(e){results.push({name,result:"FAIL",error:e.message});}}
async function main(){
  const observed=await unavailable();const missingConfig=await unavailable(false);
  if(process.argv.includes("--observe-baseline")){console.log(JSON.stringify({kind:"instrument-only; widget never executed",observed,missingConfig},null,2));return;}
  await check("contained positive: default APIs retain save/load/resolve/clear semantics",()=>{
    const storage=new MemoryStorage(null),sc=configContext(storage).SalahConfig;
    assert.equal(sc.storageAvailable().ok,true);
    assert.equal(sc.saveLocal({lat:51.5,lon:-0.12,label:"London",method:"3"}).ok,true);
    assert.equal(sc.loadLocal().lat,51.5);assert.equal(sc.resolve("#local=1").cfg.label,"London");
    assert.equal(sc.resolve("#preferLocal=1&lat=10&lon=20").cfg.lat,51.5);
    assert.equal(sc.resolve("#lat=10&lon=20").cfg.lat,10);
    assert.equal(sc.clearLocal().ok,true);assert.equal(sc.loadLocal(),null);
  });
  await check("explicit storage saves privately and reaches both resolver consumers",()=>{
    const real=new MemoryStorage(),privateStore=new MemoryStorage(null),sc=configContext(real).SalahConfig;
    assert.equal(sc.storageAvailable(privateStore).ok,true);
    assert.equal(sc.saveLocal({lat:51.5,lon:-0.12,label:"London",method:"3"},privateStore).ok,true);
    assert.equal(sc.loadLocal(privateStore).lat,51.5);
    assert.equal(sc.resolve("#local=1",privateStore).cfg.lat,51.5);
    assert.equal(sc.resolve("#preferLocal=1&lat=10&lon=20",privateStore).cfg.lat,51.5);
    assert.equal(sc.resolve("#lat=10&lon=20",privateStore).cfg.lat,10);
    assert.equal(sc.clearLocal(privateStore).ok,true);assert.equal(sc.loadLocal(privateStore),null);
    assert.equal(real.data.get(key),saved,"owner settings changed");assert.deepEqual(real.calls,[],"real storage was reached");
  });
  await check("blocked default getter and explicit denied storage preserve safe shapes",()=>{
    const sc=configContext(new MemoryStorage(),{throwGetter:true}).SalahConfig;
    assert.equal(sc.storageAvailable().ok,false);assert.equal(sc.loadLocal(),null);
    assert.equal(sc.saveLocal({lat:1,lon:2}).ok,false);assert.equal(sc.clearLocal().ok,false);
    const denied={getItem(){throw new DOMException("blocked","SecurityError");},setItem(){throw new DOMException("blocked","SecurityError");},removeItem(){throw new DOMException("blocked","SecurityError");}};
    assert.equal(sc.storageAvailable(denied).ok,false);assert.equal(sc.loadLocal(denied),null);
    assert.equal(sc.saveLocal({lat:1,lon:2},denied).error,"SecurityError");assert.equal(sc.clearLocal(denied).error,"SecurityError");
    const privateStore=new MemoryStorage(null);assert.equal(sc.saveLocal({lat:1,lon:2},privateStore).ok,true);
  });
  await check("null iframe cannot PASS and names missing required execution",()=>{
    assert.notEqual(observed.className,"pass","unexecuted widget is green");
    assert.equal(observed.smoke.status,"INCOMPLETE");assert.ok(observed.smoke.required.missing.length>0);
    assert.ok(observed.smoke.required.executed>0,"config positive control did not execute");
  });
  await check("missing config is FAIL, not a required-scene timeout",()=>{
    assert.equal(missingConfig.smoke.status,"FAIL");assert.ok(missingConfig.smoke.fail>0);
  });
  for(const raw of [saved,"{malformed exact raw bytes",null])await check("unavailable run preserves owner raw="+JSON.stringify(raw),async()=>{
    const r=await unavailable(true,raw);assert.equal(r.after,raw);assert.equal(r.unrelated,"retained");assert.deepEqual(r.realStorageCalls,[]);
  });
  for(const raw of [saved,"{malformed exact raw bytes",null])for(const outcome of ["pass","fail","throw","timeout"])await check("required recorder "+outcome+" preserves sentinel raw="+JSON.stringify(raw),async()=>{
    // Deliberate synthetic callbacks characterize the recorder only, never widget health.
    const {ctx,storage}=helperHarness(smokeSource,raw);
    const callback=outcome==="pass"?'ok=>ok("controlled assertion",true)':outcome==="fail"?'ok=>ok("controlled assertion",false)':outcome==="throw"?'()=>{throw Error("controlled callback exception");}':'ok=>{window.lateOk=ok;return new Promise(()=>{});}';
    await vm.runInContext('required("weather gate availability",'+callback+')',ctx);
    vm.runInContext("finalize()",ctx);
    const entry=ctx.__smoke.required.cases.find(c=>c.name==="weather gate availability");
    assert.equal(entry.state,outcome==="timeout"?"missing":outcome==="pass"?"executed":"failed");
    if(outcome==="timeout"){const before=ctx.__smoke.pass;vm.runInContext('lateOk("late callback",true);finalize()',ctx);assert.equal(ctx.__smoke.pass,before);}
    assert.equal(storage.data.get(key)??null,raw);assert.equal(storage.data.get("unrelated-origin-key"),"retained");assert.deepEqual(storage.calls,[]);
  });
  await check("suppressed required callback remains named missing",async()=>{
    const h=helperHarness();vm.runInContext("finalize()",h.ctx);
    assert.ok(h.ctx.__smoke.required.missing.includes("weather gate availability"));assert.equal(h.ctx.__smoke.status,"INCOMPLETE");
    await vm.runInContext('required("weather gate availability",()=>{})',h.ctx);vm.runInContext("finalize()",h.ctx);
    assert.ok(h.ctx.__smoke.required.missing.includes("weather gate availability"));
  });
  for(const edge of ["savedP","savedL"])await check("mutant killed: resolver drops private store at "+edge,()=>{
    const source=replaceOnce(configSource,"var "+edge+" = loadLocal(storage);","var "+edge+" = loadLocal();");
    const real=new MemoryStorage(),privateStore=new MemoryStorage(null),sc=configContext(real,{source}).SalahConfig;
    sc.saveLocal({lat:51.5,lon:-0.12},privateStore);
    const resolved=sc.resolve(edge==="savedP"?"#preferLocal=1&lat=10&lon=20":"#local=1",privateStore);
    assert.notEqual(resolved.cfg.lat,51.5);assert.ok(real.calls.length>0,"storage access oracle missed the mutant");
  });
  await check("mutant killed: aggregate ignores missing requirements",async()=>{
    const source=replaceOnce(smokeSource,'const status=fail?"FAIL":missingNames.length?"INCOMPLETE":"PASS";','const status=fail?"FAIL":"PASS";');
    const r=await unavailable(true,saved,source);assert.equal(r.smoke.status,"PASS");assert.ok(r.smoke.required.missing.length>0,"missing-name oracle missed the mutant");
  });
  await check("mutant killed: timeout counted as executed",async()=>{
    const source=replaceOnce(smokeSource,'entry.state="missing";entry.reason=reason;','entry.state="executed";entry.reason=reason;');
    const h=helperHarness(source);await vm.runInContext('required("weather gate availability",()=>new Promise(()=>{}))',h.ctx);vm.runInContext("finalize()",h.ctx);
    assert.equal(h.ctx.__smoke.required.cases.find(c=>c.name==="weather gate availability").state,"executed");
    assert.ok(!h.ctx.__smoke.required.missing.includes("weather gate availability"),"named timeout oracle missed mutant");
  });
  for(const control of ["stale-attempt","stale-hash","cache-without-json"])await check("readiness rejects "+control,async()=>{
    const h=helperHarness();h.ctx.__control=control;
    // The adversarial frame deliberately pretends to have prayer/render state. It
    // must be rejected BEFORE that fake state can become execution evidence.
    const result=await vm.runInContext(`(async()=>{
      const want="fixture-scene&tz=Asia/Riyadh&qa=1";
      fr.contentWindow={location:{hash:__control==="stale-hash"?"#old-scene":"#"+want},
        __widgetFixture:{attempt:__control==="stale-attempt"?0:1,hash:want,state:"ready",sourceSha256:"a".repeat(64),storageIsolated:true,clockFixed:true,fetchIntercepted:true,
          ledger:__control==="cache-without-json"?[]:[{attempt:1,url:"https://api.aladhan.com/v1/timings/07-09-2026",jsonReads:1,result:"json-consumed"}]},
        qaState(){return {cache:{prayerLoaded:true},render:{currentKey:"Dhuhr",nextKey:"Asr"}};}};
      return await loadUntil("fixture-scene",300,()=>true);
    })()`,h.ctx);assert.equal(result.w,null);
  });
  console.log(JSON.stringify({kind:"source-bound instrument/storage controls; no widget/browser qualification",root,results,
    unavailable:{summary:observed.summary,smoke:observed.smoke,realStorageCalls:observed.realStorageCalls},missingConfig:{summary:missingConfig.summary,smoke:missingConfig.smoke}},null,2));
  if(results.some(r=>r.result==="FAIL"))process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
