'use strict';
const assert=require('node:assert/strict'),{test}=require('node:test'),fs=require('node:fs'),path=require('node:path');
const {remainingFixture,healthy,NOW,present,source,vm}=require('./weather-remaining-fixture.cjs');
const isStrong=v=>['drizzle','rain','snow','thunder'].includes(v.a.cls);
const nearby=()=>({state:'nearby-precipitation',distanceKm:[8,12],observedAt:NOW});
const approach=()=>({from:NOW+600000,to:NOW+1800000,derivedFrom:'qualified-fixture-trajectory'});
const dry=()=>({state:'dry',type:null,lightning:'not-observed',quantity:null});
function text(f){const snap=f.snapshot();assert(snap.header.information,'information must reach actual header');return {snap,info:snap.header.information};}

for(const state of ['conflicting','unknown'])test('R0024 qualified '+state+' reaches ordinary information without borrowing model wet effects',async()=>{
  const f=remainingFixture({hash:'timeScale=1'});await f.fetchWeather();
  assert.equal(f.consume(present(f,{present:{state,type:null,lightning:'unavailable',quantity:null}})).ok,true);
  const {snap,info}=text(f);assert.equal(snap.decision.current,state);assert.equal(snap.decision.model.state,'wet');
  assert(info.currentText.includes('Current: SIM '+state));assert.equal(f.nodes.get('#weather-information').textContent,info.summary);
  assert(f.nodes.get('#wi').getAttribute('aria-label').includes(info.summary));assert.equal(isStrong(f.view()),false);
});

test('R0024 qualified area no-echo and none-supported horizon reach ordinary information',async()=>{
  const f=remainingFixture({hash:'timeScale=1'});await f.fetchWeather();f.set({weatherTrack:null});
  assert.equal(f.consume(present(f,{present:dry(),spatial:{state:'observed-area-no-echo',distanceKm:[0,10],observedAt:NOW}})).ok,true);
  const {snap,info}=text(f);assert.equal(snap.decision.horizon.state,'none-supported');assert.equal(snap.decision.horizon.arrival,null);
  assert.match(info.spatialText,/Nearby: SIM observed area has no echo \(0–10 km\)/);assert.match(info.horizonText,/Approach: SIM none supported/);
  assert.equal(f.nodes.get('#weather-information').textContent,info.summary);assert(f.nodes.get('#wi').title.includes(info.summary));assert.equal(isStrong(f.view()),false);
});
test('R0024 C dry nearby approach reaches actual title name and accessible description',async()=>{
  const f=remainingFixture({hash:'timeScale=1'});await f.fetchWeather();assert.equal(f.consume(present(f,{present:dry(),spatial:nearby(),approach:approach()})).ok,true);
  const {snap,info}=text(f);assert.match(info.currentText,/Current: SIM supported dry/);assert.match(info.spatialText,/Nearby: SIM precipitation 8–12 km/);
  assert.match(info.horizonText,/qualified SIM interval/);assert.match(info.horizonText,/2026-09-07 21:10/);assert.match(info.horizonText,/2026-09-07 21:30 UTC/);
  assert.equal(f.nodes.get('#weather-information').textContent,info.summary);assert(f.nodes.get('#wi').title.includes(info.summary));
  assert.equal(f.nodes.get('#wi').getAttribute('aria-label'),snap.header.label);assert.match(f.nodes.get('#wi').getAttribute('aria-describedby'),/\bweather-information\b/);
  assert.equal(isStrong(f.view()),false);assert.equal(snap.decision.permissions.rain,false);
});
for(const derivation of [null,'current-wind'])test('R0024 nearby '+String(derivation)+' cannot invent an arrival interval',async()=>{
  const f=remainingFixture({hash:'timeScale=1'});await f.fetchWeather();f.consume(present(f,{present:dry(),spatial:nearby(),approach:derivation?{...approach(),derivedFrom:derivation}:null}));
  const {info}=text(f);assert.match(info.spatialText,/8–12 km/);assert.match(info.horizonText,/no supported arrival interval/);assert.doesNotMatch(info.horizonText,/21:10|21:30/);
  assert.equal(isStrong(f.view()),false);
});
test('R0024 current wet plus later approach information coexist without changing permissions',async()=>{
  const f=remainingFixture({hash:'timeScale=1',payload:healthy({weather_code:0,precipitation:0})});await f.fetchWeather();f.consume(present(f,{spatial:nearby(),approach:approach()}));
  const before=f.decision(),{info,snap}=text(f);assert.equal(snap.decision,before);assert.match(info.currentText,/SIM supported wet/);assert.match(info.horizonText,/qualified SIM interval/);
  assert.equal(f.view().a.cls,'rain');assert.equal(snap.decision.permissions.rain,true);
});
for(const [precip,want] of [[null,'amount unavailable'],[0,'0 mm'],[0.4,'0.4 mm']])test('R0024 live model amount '+String(precip)+' retains null zero and preceding interval',async()=>{
  const f=remainingFixture({payload:healthy({precipitation:precip})});await f.fetchWeather();const {info,snap}=text(f);
  assert.match(info.currentText,/Open-Meteo CURRENT MODEL ESTIMATE/);assert(info.currentText.includes(want));assert.match(info.currentText,/direct local observation unavailable/);
  assert.match(info.spatialText,/unavailable/);assert.match(info.horizonText,/no supported arrival interval/);assert.equal(snap.header.rawCode,95);assert.equal(snap.header.temperature,20);
  assert.equal(snap.decision.observedPresent,false);assert.equal(snap.decision.permissions.lightning,false);
  if(precip===0.4){assert.match(info.currentText,/preceding interval/);assert.match(info.currentText,/20:45/);assert.match(info.currentText,/21:00 UTC/);assert.match(info.currentText,/1.6 mm\/h interval average/);}
});
test('R0024 actual production hourly forecast stays forecast only with unavailable probability',async()=>{
  const payload=healthy({time:'invalid'});payload.hourly.precipitation=[0,2];const f=remainingFixture({payload});await f.fetchWeather();const {info}=text(f);
  assert.match(info.currentText,/Current: unknown/);assert.match(info.horizonText,/numerical forecast only/);assert.match(info.forecastText,/Open-Meteo.*hourly weather model/);
  assert.match(info.forecastText,/2 mm/);assert.match(info.forecastText,/probability unavailable/);assert.match(info.forecastText,/native\/interpolated provenance unavailable/);
  assert.equal(f.view().qa.wxTruth.activePrecip,false);
});
function forecastFixture(options={}){
  const f=remainingFixture(options),owner={run:'r0024-information',document:'contained-'+Math.random()};
  f.context.__smokeWeather={};f.context.__weatherFixtureControl={assertOwned(value){assert.equal(value,owner,'wrong owner refused');}};
  const bridge=fs.readFileSync(path.join(__dirname,'weather-forecast-fixture.js'),'utf8');vm.runInContext(bridge,f.context,{filename:'weather-forecast-fixture.js'});
  const raw=()=>({scope:'simulation-fixture',policy:'synthetic-forecast-v1',provider:'Synthetic QA',product:'probability contract',target:f.target(),
    issuedAt:NOW,retrievedAt:NOW,validFrom:NOW+600000,validUntil:NOW+1800000,amount:{kind:'interval-amount',value:2,units:'mm'},
    probability:null,probabilityEvent:null,resolution:'synthetic fixture; calibration unavailable'});
  return {f,owner,raw,api:f.context.__smokeWeather};
}
for(const probability of [null,0])test('R0024 owned forecast dependency '+String(probability)+' reaches real decision header sink',()=>{
  const {f,owner,raw,api}=forecastFixture({hash:'timeScale=1'});const input=raw();input.probability=probability;
  if(probability===0)input.probabilityEvent={event:'precipitation',from:NOW+600000,to:NOW+1800000};
  api.installSyntheticForecast(owner,input);const {info,snap}=text(f);assert.equal(snap.decision.forecast.probability,probability);
  assert.match(info.forecastText,/SIM Synthetic QA.*probability contract/);assert.match(info.forecastText,/interval amount 2 mm/);
  assert(info.forecastText.includes(probability===0?'0% for precipitation':'probability unavailable'));assert.match(info.forecastText,/calibration unavailable/);
  assert.equal(f.view().qa.wxTruth.activePrecip,false);assert.equal(f.nodes.get('#weather-information').textContent,info.summary);
});
test('R0024 ordinary live or invalid owner/window forecast leaves dependency unchanged',()=>{
  const live=forecastFixture();assert.throws(()=>live.api.installSyntheticForecast(live.owner,live.raw()),/ordinary live lane/);assert.equal(live.f.decision().forecast,null);
  const {f,owner,raw,api}=forecastFixture({hash:'timeScale=1'});const input=raw();api.installSyntheticForecast(owner,input);const prior=f.decision().forecast;
  assert.throws(()=>api.installSyntheticForecast({},input),/wrong owner/);assert.throws(()=>api.installSyntheticForecast(owner,{...input,probability:0}),/probability event/);
  assert.equal(f.decision().forecast,prior);f.clock.now=NOW+1800000;assert.equal(f.decision().forecast,null);
  api.clearSyntheticForecast(owner);assert.equal(f.decision().forecast,null);
});
test('R0024 local buckle retains settings name warning role and existing description tokens',async()=>{
  const f=remainingFixture();await f.fetchWeather();f.setMode('local');const buckle=f.context.document.querySelector('.buckle'),wi=f.context.document.querySelector('#wi');
  buckle.classList.add('interactive');buckle.querySelector=()=>null;buckle.setAttribute('role','button');buckle.setAttribute('tabindex','0');
  buckle.setAttribute('aria-describedby','settings-persistence-status existing-help');wi.setAttribute('aria-describedby','icon-help');
  const start=source.indexOf('function _renderPersistenceAffordance(){'),end=source.indexOf('function _publishPersistence(',start);assert(start>=0&&end>start);
  vm.runInContext('let _persistOutcome={status:"session-only"};'+source.slice(start,end)+'globalThis.repaintPersistence=_renderPersistenceAffordance;',f.context);
  f.context.repaintPersistence();const name=buckle.getAttribute('aria-label');assert.match(name,/Widget settings.*changes not saved/);
  text(f);text(f);f.context.repaintPersistence();assert.equal(buckle.getAttribute('aria-label'),name);assert.equal(buckle.title,name);
  assert.equal(buckle.getAttribute('role'),'button');assert.equal(buckle.getAttribute('tabindex'),'0');
  assert.equal(buckle.getAttribute('aria-describedby'),'settings-persistence-status existing-help weather-information');
  assert.equal(wi.getAttribute('aria-describedby'),'icon-help weather-information');
});
test('R0024 information cache uses exact decision day zone and updates at eligibility boundaries',async()=>{
  const f=remainingFixture();await f.fetchWeather();assert.equal(typeof f.information,'function','actual formatter required');
  const decision=f.decision(),a=f.information(decision,true);assert.equal(f.information(decision,true),a);
  const calls=f.calls.length;f.clock.now+=100;assert.equal(f.decision(),decision);assert.equal(f.information(f.decision(),true),a);assert.equal(f.calls.length,calls);
  f.set({zone:'Asia/Riyadh'});const z=f.information(decision,true);assert.notEqual(z,a);assert.match(z.currentText,/2026-09-07 23:45/);assert.match(z.currentText,/Asia\/Riyadh/);
  f.clock.now=NOW+900001;const expired=text(f);assert.notEqual(expired.snap.decision,decision);assert.match(expired.info.currentText,/Current: unknown/);assert.equal(expired.snap.header.temperature,null);
});

for(const [amount,state] of [[0,'dry'],[2,'wet']])test('R0024 rejected synthetic evidence preserves model-estimated '+state+' information',async()=>{
  const f=remainingFixture({hash:'timeScale=1',payload:healthy({precipitation:amount})});await f.fetchWeather();
  const raw=present(f);raw.quality.status='ambiguous';assert.equal(f.consume(raw).ok,false);
  const {snap,info}=text(f);assert.equal(snap.decision.current,'model-estimated-'+state);
  assert.match(info.currentText,new RegExp('Current: SIM model-estimated '+state));
  assert.match(info.currentText,/Open-Meteo.*model estimate/);assert(info.currentText.includes(amount+' mm'));
  assert.match(info.currentText,/present evidence unavailable/);assert.equal(snap.decision.permissions.rain,false);
  assert.equal(snap.decision.visualPermissions.rain,false);assert.equal(isStrong(f.view()),false);
});

test('R0024 stale forecast installation refuses before changing the dependency',()=>{
  const {f,owner,raw,api}=forecastFixture({hash:'timeScale=1'});const original=vm.runInContext('weatherForecast',f.context);
  const stale={...raw(),issuedAt:NOW-21600001,retrievedAt:NOW-21600001};
  assert.throws(()=>api.installSyntheticForecast(owner,stale),/time window/);
  assert.equal(vm.runInContext('weatherForecast',f.context),original);assert.equal(f.decision().forecast,null);
});
test('R0024 existing icon name and title preserve condition provenance and append information',async()=>{
  const f=remainingFixture({payload:healthy({precipitation:null})});await f.fetchWeather();const {info}=text(f);
  const wi=f.nodes.get('#wi'),name=wi.getAttribute('aria-label'),description=f.nodes.get('#weather-information').textContent;
  assert.match(name,/^Thunderstorm — Open-Meteo current model estimate; direct local observation unavailable \(unobserved\)/);
  assert.equal(description,info.summary);assert.match(description,/amount unavailable/);assert.match(description,/quantitative effect decision:/);
  assert.equal(name,wi.title);assert(name.includes(info.summary));
  assert.equal(wi.getAttribute('aria-describedby').split(/\s+/).filter(t=>t==='weather-information').length,1);
});
