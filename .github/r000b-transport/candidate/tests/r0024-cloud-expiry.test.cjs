'use strict';
// Actual admission -> atmosphere -> paint -> cloud writer/painter/columns.
// DOM/canvas boundaries are controlled; no native pixels or elapsed motion are certified.
const assert=require('node:assert/strict'),{test}=require('node:test');
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),vm=require('node:vm');
const fixturePath=path.join(__dirname,'r000c-weather.test.cjs'),text=fs.readFileSync(fixturePath,'utf8');
const end=text.indexOf("test('control: actual fresh acquisition");assert(end>0);
const mod=new Module(fixturePath,module);mod.filename=fixturePath;mod.paths=Module._nodeModulePaths(__dirname);
mod._compile(text.slice(0,end)+'\nmodule.exports={fixture,healthy,NOW};',fixturePath);
const {fixture,healthy,NOW}=mod.exports;
const full={weather_code:3,precipitation:0,cloud_cover:100,cloud_cover_low:100,cloud_cover_mid:100,cloud_cover_high:100,wind_speed_10m:7};
function cloudView(f){
  const v=f.view();f.cloudTrace.length=0;
  const state=JSON.parse(vm.runInContext(`paintClouds(simNow()/1000);JSON.stringify({
    selected:!!selectedWeather(),decision:weatherDecision(),cov:[cloudState.covLow,cloudState.covMid,cloudState.covHigh],
    tgt:[cloudState.tgtLow,cloudState.tgtMid,cloudState.tgtHigh],ready:_cloudReady,density:_colDens?Math.max(..._colDens):null,
    population:_cloudMotion.population,phase:_cloudMotion.phase,life:_cloudMotion.life})`,f.context));
  return {...v,...state,fills:f.cloudTrace.filter(x=>x[0]==='fill').length};
}
function withdrawn(v){
  assert.equal(v.selected,false);assert.deepEqual(v.tgt,[0,0,0]);assert.deepEqual(v.cov,[0,0,0]);
  assert.equal(v.ready,false);assert.equal(v.fills,0);assert.equal(v.density,0);
  assert.equal(v.a.wxTemp,null);assert.equal(v.a.windSpeed,0);assert.equal(v.a.rainOp,0);
}
function current(clock,overrides={}){return healthy({...full,time:new Date(clock.now).toISOString().slice(0,16),...overrides});}

test('R0024 actual cloud consumer withdraws at first source-expired paint after inclusive TTL',async()=>{
  const f=fixture({payload:healthy(full)});await f.fetchWeather();const fresh=cloudView(f);
  assert(fresh.selected);assert.deepEqual(fresh.cov,[1,1,1]);assert(fresh.fills>0);assert(fresh.density>0);
  f.clock.now=NOW+900000;const boundary=cloudView(f);assert(boundary.selected);assert.deepEqual(boundary.cov,[1,1,1]);assert(boundary.fills>0);
  f.clock.now++;const expired=cloudView(f);withdrawn(expired);assert.equal(expired.population,fresh.population);
  const repeated=cloudView(f);withdrawn(repeated);assert.deepEqual(repeated.phase,expired.phase);assert.deepEqual(repeated.life,expired.life);
});

test('R0024 actual expired-source outage clears painter and cannot renew accepted cache or timestamp',async()=>{
  let count=0;const f=fixture({fetch:async()=>{if(count++)throw Error('controlled outage');return {ok:true,json:async()=>healthy(full)};}});
  await f.fetchWeather();assert(cloudView(f).fills>0);const cached=f.storage.get('salahwx:24.47|39.61|c'),old=f.read().weather;
  f.clock.now=NOW+900001;await f.fetchWeather();withdrawn(cloudView(f));
  assert.equal(f.read().weather,old);assert.equal(f.read().lastWxAt,NOW);assert.equal(f.storage.get('salahwx:24.47|39.61|c'),cached);
});

test('R0024 returning healthy source establishes its first cloud deck promptly without population reset',async()=>{
  let unavailable=false;const f=fixture({fetch:async(url,clock)=>{if(unavailable)throw Error('controlled outage');return {ok:true,json:async()=>current(clock)};}});
  await f.fetchWeather();const fresh=cloudView(f);unavailable=true;f.clock.now=NOW+900001;await f.fetchWeather();withdrawn(cloudView(f));
  unavailable=false;f.clock.now+=60000;await f.fetchWeather();const back=cloudView(f);
  assert(back.selected);assert.deepEqual(back.cov,[1,1,1]);assert.equal(back.ready,true);assert(back.fills>0);assert(back.density>0);
  assert.equal(back.a.wxTemp,20);assert.equal(back.population,fresh.population);assert.equal(f.read().lastWxAt,f.clock.now);
});

test('control: healthy admitted-clear cloud refresh retains ordinary .08 easing and useful model data',async()=>{
  let count=0;const f=fixture({fetch:async(url,clock)=>({ok:true,json:async()=>current(clock,count++?{weather_code:0,cloud_cover:0,cloud_cover_low:0,cloud_cover_mid:0,cloud_cover_high:0,wind_speed_10m:2}:{})})});
  await f.fetchWeather();const initial=cloudView(f);assert.deepEqual(initial.cov,[1,1,1]);f.clock.now=NOW+900001;await f.fetchWeather();const clear=cloudView(f);
  assert(clear.selected);assert.equal(clear.decision.modelCode,0);assert.equal(clear.a.wxTemp,20);assert.deepEqual(clear.tgt,[0,0,0]);
  assert.deepEqual(clear.cov,[.92,.92,.92]);assert.equal(clear.ready,true);assert(clear.fills>0);assert(clear.density>0);assert.equal(clear.population,initial.population);
  const next=cloudView(f);assert.deepEqual(next.cov,[.8464,.8464,.8464]);assert.deepEqual(next.phase,clear.phase);
});

test('control: unavailable temperature does not erase clouds from an eligible current model',async()=>{
  const f=fixture({payload:healthy({...full,temperature_2m:null})});await f.fetchWeather();const v=cloudView(f);
  assert(v.selected);assert.equal(v.a.wxTemp,null);assert.deepEqual(v.cov,[1,1,1]);assert(v.fills>0);assert(v.density>0);
});

for(const change of ['same coordinates','changed coordinates'])test('R0024 actual cloud painter excludes obsolete generation with '+change,async()=>{
  const f=fixture({payload:healthy(full)});await f.fetchWeather();const initial=cloudView(f);assert(initial.fills>0);
  if(change==='changed coordinates')f.set({lat:0,lon:0});f.beginRuntimeGeneration();const gone=cloudView(f);withdrawn(gone);
  f.clock.now+=60000; // Honor the existing retry throttle; this fixture drives generation, not applyConfig/reset.
  await f.fetchWeather();const back=cloudView(f);assert(back.selected);assert.deepEqual(back.cov,[1,1,1]);assert(back.fills>0);
  assert.equal(back.decision.target.generation,initial.decision.target.generation+1);
});

test('control: explicit advancing forecast preview keeps its admitted cloud painter positive',async()=>{
  const f=fixture({hash:'timeScale=2',payload:healthy(full)});await f.fetchWeather();assert(cloudView(f).fills>0);
  f.clock.now=NOW+900001;f.syncWeather();const v=cloudView(f);assert(v.selected);assert.equal(v.decision.lane,'preview');assert(v.fills>0);assert(v.density>0);
});

test('control: raw qualified SIM wet and its exact rain expiry preserve explicit model clouds',()=>{
  const f=fixture({sim:{wx:'0'},config:{lat:24.47,lon:39.61,source:'hash',locationEvidence:{intent:'fixed-site',source:'hash',accuracyM:null,acquiredAt:null}}});const rawCurrent=healthy({...full,weather_code:0}).current;
  vm.runInContext(`weather=admitWeatherRecord(${JSON.stringify(rawCurrent)},{units,zone:tz,retrievedAt:Date.now(),target:currentWeatherTarget()});
    {const t=currentWeatherTarget(),n=Date.now();weatherSynthetic=admitWeatherFixture({scope:'simulation-fixture',provider:'Synthetic QA',product:'present/nearby contract',policy:'synthetic-present-v1',target:{generation:t.generation,lat:t.lat,lon:t.lon},measurementAt:n,validFrom:n,validUntil:n+60000,retrievedAt:n,frameAt:n,issuedAt:n,units:'categorical',footprint:{kind:'point',lat:t.lat,lon:t.lon,coverage:'target'},quality:{status:'qualified',sampling:'direct',localObservationAt:n,operationalHealth:'operational'},present:{state:'wet',type:'rain',lightning:'unavailable',quantity:null}},t,n);}`,f.context);
  assert.equal(vm.runInContext('weatherSynthetic.ok',f.context),true);
  const wet=cloudView(f);assert.equal(wet.decision.lane,'simulation-fixture');assert.equal(wet.decision.permissions.rain,true);assert(wet.a.rainOp>0);assert(wet.fills>0);
  f.clock.now+=60000;const expired=cloudView(f);assert.equal(expired.decision.permissions.rain,false);assert.equal(expired.a.rainOp,0);assert.deepEqual(expired.cov,[1,1,1]);assert(expired.fills>0);
});
