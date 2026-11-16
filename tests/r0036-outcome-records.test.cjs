'use strict';
// R0036 (issue 103) PRA-F-15(d), machine OUT: the weather/radar attempt record separates transport completion (`state`,
// R000D vocabulary, unchanged) from the admission outcome (`admission`, closed vocabulary; docs/state-contracts/R0036.md).
// Real fetchWeather/acquireRadar/wxFetchJson through the accepted r000c source fixture; every transport is a recorded
// double, no provider is contacted. SALAH_WEATHER_SOURCE selects another tree's generated index (the RED run).
const assert=require('node:assert/strict'),{test}=require('node:test');
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),vm=require('node:vm');
const fixturePath=path.join(__dirname,'r000c-weather.test.cjs'),fixtureText=fs.readFileSync(fixturePath,'utf8');
const end=fixtureText.indexOf("test('control: actual fresh acquisition");assert(end>0);
const fixtureModule=new Module(fixturePath,module);fixtureModule.filename=fixturePath;fixtureModule.paths=Module._nodeModulePaths(__dirname);
fixtureModule._compile(fixtureText.slice(0,end)+'\nmodule.exports={fixture,NOW,healthy};',fixturePath);
const {fixture,NOW,healthy}=fixtureModule.exports;
const SEC=NOW/1000,HOST='https://tilecache.rainviewer.com';
const req=(f,kind='weather')=>{const r=f.view().qa.wxTruth.requests[kind];return r?{...r,adopted:r.adopted?{...r.adopted}:r.adopted}:r;};
const respond=body=>async()=>({ok:true,status:200,json:async()=>body});
const outcomes={};
async function weatherCase(name,options,expect,before){
  const f=fixture(options);if(before)await before(f);await f.fetchWeather();
  const r=req(f);outcomes[name]=r&&r.admission;
  assert.equal(r.admission,expect.admission,name+': admission');assert.equal(r.state,expect.state,name+': transport state unchanged');
  if('reason' in expect)assert.equal(r.reason,expect.reason,name+': reason');
  if(expect.adopted)assert.deepEqual(r.adopted,expect.adopted,name+': adopted records');
  return f;
}

test('R36-10 ES36-07 weather: each attempt outcome has its own exact admission value; state keeps the transport meaning',async()=>{
  await weatherCase('admitted',{},{admission:'admitted',state:'received',reason:null,adopted:{current:true,track:true}});
  await weatherCase('provider-error',{payload:{error:true,reason:'x'}},{admission:'provider-error',state:'received'});
  await weatherCase('malformed-body',{payload:[1,2]},{admission:'malformed-body',state:'received'});
  await weatherCase('no-admissible-record',{payload:{latitude:24.47}},{admission:'no-admissible-record',state:'received',adopted:{current:false,track:false}});
  await weatherCase('zone-rejected',{payload:{...healthy(),timezone:'Asia/Tokyo'}},{admission:'zone-rejected',state:'unavailable',reason:'response timezone unavailable or contradicts captured request'});
  await weatherCase('transport-unavailable',{ok:false,status:503},{admission:'transport-unavailable',state:'unavailable',reason:'HTTP unavailable'});
  // Track-only: no admissible current, an admissible hourly track.
  await weatherCase('admitted-track',{payload:{...healthy(),current:{weather_code:999}}},{admission:'admitted-track',state:'received',adopted:{current:false,track:true}});
  // Retained-current: an eligible record is held; a new admissible but stale current is kept out (L1617 rule unchanged).
  const f=await weatherCase('retained-current',{},{admission:'admitted',state:'received'});
  f.set({lastWxAt:0,lastWxTry:0,retry:{weather:null,radar:null}});            // open the retry gate only
  f.context.opts.payload=healthy({time:'2026-09-07T18:00'});
  await f.fetchWeather();const r=req(f);outcomes['retained-current']=r.admission;
  assert.equal(r.admission,'retained-current');assert.deepEqual(r.adopted,{current:false,track:true});
  assert.equal(f.read().weather.currentTime,'2026-09-07T21:00','the eligible record is retained exactly as before');
});

test('R36-11 ES36-07 weather: an early-renewal miss and a superseded attempt are labelled, and only their own record',async()=>{
  const f=fixture();await f.fetchWeather({outcome:null,step:NOW+900e3,generation:0});
  const miss=req(f);outcomes['early-renewal-miss']=miss.admission;assert.equal(miss.admission,'early-renewal-miss');
  // Supersession: a new runtime generation cancels the in-flight attempt; its record (and only its record) says so.
  let release;const g=fixture({fetch:()=>new Promise(r=>{release=r;})});
  const p=g.fetchWeather();await new Promise(r=>setImmediate(r));
  assert.equal(req(g).state,'fetch');assert.equal(req(g).admission,'pending');
  g.beginRuntimeGeneration();release({ok:true,status:200,json:async()=>healthy()});await p;
  const s=req(g);outcomes.superseded=s.admission;
  assert.equal(s.admission,'superseded');assert.equal(s.state,'fetch','R000D state is not rewritten by an ineligible attempt');
  assert.equal(g.read().weather,null,'nothing was admitted');
});

test('R36-12 ES36-07 radar (retained test path): manifest outcomes are distinct; R0032 rejections keep their state and reasons',async()=>{
  const radar=async(name,options,expect)=>{const f=fixture(options);await f.fetchRadar();const r=req(f,'radar');outcomes['radar-'+name]=r.admission;
    assert.equal(r.admission,expect.admission,name);assert.equal(r.state,expect.state,name+' state');if(expect.reason)assert.equal(r.reason,expect.reason);};
  await radar('admitted',{},{admission:'admitted',state:'received'});
  await radar('malformed',{manifest:{generated:SEC,host:HOST,radar:{}}},{admission:'malformed-manifest',state:'received'});
  await radar('malformed-frame',{manifest:{generated:SEC,host:HOST,radar:{past:[{time:'x',path:'/v2/radar/1'}]}}},{admission:'malformed-manifest',state:'received'});
  await radar('no-frame',{manifest:{generated:SEC,host:HOST,radar:{past:[]}}},{admission:'no-frame',state:'received'});
  await radar('rejected',{manifest:{generated:SEC,radar:{past:[{time:SEC,path:'/v2/radar/'+SEC}]}}},{admission:'rejected',state:'rejected',reason:'radar tile host not admitted'});
  await radar('image-unavailable',{imageError:true},{admission:'transport-unavailable',state:'unavailable',reason:'image unavailable'});
});

// Review A2: an attempt whose own absolute deadline passed is "expired", never "superseded" (that label is for an
// attempt replaced by a newer operation/generation); a radar manifest record is never left "pending".
test('R36-15 a late body past the attempt deadline is labelled expired; a newer generation is superseded',async()=>{
  let release;const f=fixture({fetch:()=>new Promise(r=>{release=r;})});
  const p=f.fetchWeather();await new Promise(r=>setImmediate(r));
  f.clock.now+=10001;                                                      // the attempt's absolute deadline has passed
  release({ok:true,status:200,json:async()=>healthy()});await p;
  const r=req(f);assert.equal(r.admission,'expired');assert.equal(r.state,'unavailable');assert.equal(r.reason,'obsolete or expired fetch');
  assert.equal(f.read().weather,null);
});
test('R36-16 a radar image attempt that cannot begin leaves a terminal manifest record, not pending',async()=>{
  const f=fixture();
  vm.runInContext('{const begin=beginAttempt;let n=0;beginAttempt=function(op,t){return ++n===2?null:begin(op,t);};}',f.context);
  await f.fetchRadar();const r=req(f,'radar');
  assert.equal(r.state,'received');assert.equal(r.admission,'superseded');assert.deepEqual(f.images,[]);
});
// Review A1 (mutant M21): wxAdmission labels only the record its own operation and attempt wrote.
test('R36-17 wxAdmission never relabels a newer attempt\'s or another operation\'s record',()=>{
  const f=fixture();
  vm.runInContext('_wxRequests.weather={generation:0,operationId:9,attemptId:9,state:"received",reason:null,admission:"admitted"};',f.context);
  vm.runInContext('wxAdmission({kind:"weather",operationId:9},{attemptId:3},"superseded");wxAdmission({kind:"weather",operationId:4},{attemptId:9},"superseded");',f.context);
  assert.equal(req(f).admission,'admitted');
  vm.runInContext('wxAdmission({kind:"weather",operationId:9},{attemptId:9},"no-admissible-record");',f.context);
  assert.equal(req(f).admission,'no-admissible-record','the owning attempt may label its own record');
});

test('R36-13 §5.4: the seven contracted outcomes map to pairwise distinct admission values',()=>{
  const seven=['admitted','provider-error','no-admissible-record','zone-rejected','retained-current','radar-malformed','superseded'];
  for(const k of seven)assert.ok(typeof outcomes[k]==='string','outcome recorded for '+k);
  assert.equal(new Set(seven.map(k=>outcomes[k])).size,7,JSON.stringify(outcomes));
});
