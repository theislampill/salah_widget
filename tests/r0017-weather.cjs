/* R0017 successor smoke oracles execute the actual joined runtime.
 * VM DOM/canvas/clock boundaries do not qualify browser pixels or live motion. */
"use strict";
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm"),assert=require("node:assert/strict"),crypto=require("node:crypto");
const {load,sha}=require("./r001d-harness.cjs");
const root=path.resolve(process.argv[2]||path.join(__dirname,".."));
const sourcePath=path.join(root,"index.html"),smokePath=path.join(root,"tests/smoke.html");
const source=fs.readFileSync(sourcePath,"utf8"),smoke=fs.readFileSync(smokePath,"utf8");
const wrapper=fs.readFileSync(path.join(root,"tests/widget-fixture.html"),"utf8");
function region(text,start,end){const a=text.indexOf(start),b=text.indexOf(end,a);assert(a>=0&&b>a,"actual test-instrument region missing: "+start);return text.slice(a,b);}
const declared=vm.runInNewContext(region(smoke,"const CASES=","const cases=")+"CASES");
// The existing full-runtime VM owns its DOM and storage. Replay the ACTUAL wrapper
// guard/Response/clock/bridge bodies into it; only parser/readiness and network are
// boundaries. This does not prove native preparse order or browser readiness.
async function weatherFixture(hash,wrapperText=wrapper){
  const h=load({sourcePath,hash:"#"+hash});
  const report={run:"r0017-source-control",attempt:1,documentId:crypto.randomUUID(),hash,state:"ready",sourceSha256:h.sourceHash,
    clockNow:h.clock.wall,ledger:[],weatherEvents:[]};
  Object.assign(h.ctx,{__widgetFixture:report,__report:report,__nativeDate:Date,Response,URL,TextEncoder});
  h.run('const run=__report.run,attempt=__report.attempt,documentId=__report.documentId,hash=__report.hash,report=__report,ownedDocument=document,mode="healthy",NativeDate=__nativeDate;let clockNow=Date.now();'+
    region(wrapperText,'const identity=()=>','  function failure(')+
    region(wrapperText,'function modelInput(){','  // Serialized as a separate')+
    region(wrapperText,'class FixtureDate extends NativeDate','    report.initialStorageEntries=')+
    region(wrapperText,'function installWeatherBridge(){','  async function start(){')+'installWeatherBridge();');
  if(!hash.includes("simWx="))await h.complete(h.run('fetchWeather()'));
  else h.run('startWeather()');
  h.run('render()');return h;
}
async function consumers(wrapperText=wrapper){
  const groups=[];
  const ctx=vm.createContext({URL,Promise,console,prayerReady:()=>true,scene:async(hash,name,fn,ready)=>{
    const h=await weatherFixture(hash+"&tz=Asia/Riyadh&qa=1",wrapperText),assertions=[];
    assert.equal(ready(h.ctx),true,"controlled actual consumer prerequisites: "+name);
    await fn(h.ctx,h.ctx.qaState(),(label,condition)=>assertions.push({label,condition:!!condition}));
    groups.push({name,expected:declared.find(r=>r[0]===name)?.[1],assertions});
  }});
  ctx.window=ctx;
  await vm.runInContext('const base="lat=24.47&lon=39.61&label=Madinah&method=4";'+
    region(smoke,'function weatherCurrent(','async function run(){')+'weatherConsumers()',ctx);
  return groups;
}
const failures=groups=>groups.flatMap(g=>g.assertions.filter(a=>!a.condition).map(a=>({group:g.name,...a})));
const results=[];let consumerGroups=[];
async function check(name,fn){try{await fn();results.push({name,result:"PASS"});}catch(e){results.push({name,result:"FAIL",error:e.message});}}
async function main(){
  await check("all thirteen actual smoke model/proxy assertions obey joined weather policy",()=>{
    const h=load({sourcePath}),seen=[];
    const start=smoke.indexOf('await required("weather gate assertions",ok=>{'),end=smoke.indexOf('\n  });',start);
    assert(start>=0&&end>start,"existing thirteen-case group is missing");
    h.ctx.__record=(name,condition)=>seen.push({name,condition:!!condition});
    h.run('const G=gateWeatherCode,C=wxClass;const ok=__record;'+smoke.slice(start+'await required("weather gate assertions",ok=>{'.length,end));
    assert.equal(seen.length,13,"old denominator was dropped");
    assert.equal(seen.find(r=>r.name==="thunder code + heavy keeps thunder").condition,true,"useful heavy model positive was lost");
    assert.equal(seen.find(r=>r.name==="rain code + wet keeps rain").condition,true,"useful wet model positive was lost");
    assert.deepEqual(seen.filter(r=>!r.condition),[],"smoke contains obsolete weather oracles: "+JSON.stringify(seen.filter(r=>!r.condition)));
  });
  await check("contained positive reaches actual admitted current model, atmosphere, paint and QA",()=>{
    const h=load({sourcePath,hash:'#lat=24.47&lon=39.61&method=4&tz=Asia/Riyadh&units=c'});
    h.run('__fixtureWeatherCurrent.weather_code=95;__fixtureWeatherCurrent.precipitation=5;weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:"c",zone:tz,retrievedAt:Date.now()});render();');
    const q=h.ctx.qaState();
    assert.equal(q.cache.currentEligible,true);assert.equal(q.wxTruth.modelCondition,"thunder");
    assert.equal(h.select('#wt').textContent,"24°");assert.equal(h.select('#wi').textContent,"≈");
    assert.equal(q.wxTruth.current,"model-estimated-wet");assert.equal(q.wxTruth.permissions.rain,false);
    assert.equal(q.wxTruth.permissions.lightning,false);assert.equal(q.wxTruth.activePrecip,false);
    assert.equal(+h.select('.c').style.getPropertyValue('--rain-op'),0);
  });
  await check("all eleven actual shared-smoke weather consumer callbacks reach their required assertions",async()=>{
    const groups=consumerGroups=await consumers();assert.equal(groups.length,11);assert.equal(groups.reduce((n,g)=>n+g.assertions.length,0),66);
    for(const g of groups)assert.equal(g.assertions.length,g.expected,"missing required assertions: "+g.name);
    assert.deepEqual(failures(groups),[],"actual shared-smoke weather failures: "+JSON.stringify(failures(groups)));
  });
  await check("mutant killed: live bridge writes before refusing; useful model positive remains",async()=>{
    const from='if(SIM.wx==null&&!ADVANCING){log("synthetic-refused-live"';assert.equal(wrapper.split(from).length,2);
    const groups=await consumers(wrapper.replace(from,'if(false){log("synthetic-refused-live"'));
    const failed=failures(groups);assert(failed.some(a=>a.label==="refusal occurred before synthetic-state write"));
    assert(groups.find(g=>g.name==="live model wet is useful; local particles off").assertions.every(a=>a.condition));
  });
  await check("mutant killed: synthetic bridge never admits wet; model positives remain",async()=>{
    const from='const result=admitWeatherFixture(raw,currentWeatherTarget(),Date.now());weatherSynthetic=result;';assert.equal(wrapper.split(from).length,2);
    const groups=await consumers(wrapper.replace(from,'const result=admitWeatherFixture(null,currentWeatherTarget(),Date.now());weatherSynthetic=result;'));
    assert(failures(groups).some(a=>a.label==="actual versioned present admission is positive"));
    assert(groups.find(g=>g.name==="live model wet is useful; local particles off").assertions.every(a=>a.condition));
  });
  await check("mutant killed: target generation bridge is a no-op after admitted wet positive",async()=>{
    const from='control.assertOwned(owner);beginRuntimeGeneration();render();';assert.equal(wrapper.split(from).length,2);
    const groups=await consumers(wrapper.replace(from,'control.assertOwned(owner);render();'));
    const target=groups.find(g=>g.name==="synthetic target generation clears permission");
    assert.equal(target.assertions[0].condition,true);assert.equal(target.assertions[1].condition,false);assert.equal(target.assertions[3].condition,false);
  });
  console.log(JSON.stringify({kind:"actual-source R0017 weather oracles; VM boundaries, no browser/native qualification",root,
    sourceSha256:sha(Buffer.from(source)),smokeSha256:sha(Buffer.from(smoke)),wrapperSha256:sha(Buffer.from(wrapper)),fixtureSha256:sha(fs.readFileSync(__filename)),
    required:{groups:declared.length,assertions:declared.reduce((n,g)=>n+g[1],0)},results,consumerGroups},null,2));
  if(results.some(r=>r.result==="FAIL"))process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
