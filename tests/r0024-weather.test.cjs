'use strict';
// Actual source consumer tests. These do not certify a live observation provider or rendered pixels.
const assert = require('node:assert/strict'), { test } = require('node:test');
const fs = require('node:fs'), path = require('node:path'), Module = require('node:module'), vm = require('node:vm');
const fixturePath = path.join(__dirname, 'r000c-weather.test.cjs'), fixtureText = fs.readFileSync(fixturePath, 'utf8');
const end = fixtureText.indexOf("test('control: actual fresh acquisition"); assert(end > 0);
const fixtureModule = new Module(fixturePath, module); fixtureModule.filename = fixturePath;
fixtureModule.paths = Module._nodeModulePaths(__dirname);
fixtureModule._compile(fixtureText.slice(0, end) + '\nmodule.exports={fixture,healthy,NOW};', fixturePath);
const { fixture, healthy, NOW } = fixtureModule.exports;
const strong = cls => ['drizzle','rain','snow','thunder'].includes(cls);
const fixed = () => ({lat:24.47,lon:39.61,source:'hash',locationEvidence:{intent:'fixed-site',source:'hash',accuracyM:null,acquiredAt:null,provider:null,area:null,bounds:null}});
function policyFixture(options={}){
  const f=fixture({config:fixed(),...options});
  vm.runInContext(`globalThis.policy={target:currentWeatherTarget,capture:captureWeatherTarget,
    admit:raw=>admitWeatherFixture(raw,currentWeatherTarget(),Date.now()),
    consume:raw=>(weatherSynthetic=admitWeatherFixture(raw,currentWeatherTarget(),Date.now())),
    install:result=>{weatherSynthetic=result;},decision:weatherDecision,
    reconcile:input=>reconcileWeatherEvidence(input,Date.now())};`,f.context);
  return Object.assign(f,f.context.policy);
}
function present(f,changes={}){
  const now=f.clock.now,t=f.target();
  return {scope:'simulation-fixture',provider:'Synthetic QA',product:'present/nearby contract',policy:'synthetic-present-v1',
    target:{generation:t.generation,lat:t.lat,lon:t.lon},measurementAt:now,validFrom:now,validUntil:now+60000,retrievedAt:now,
    frameAt:now,issuedAt:now,units:'categorical',footprint:{kind:'point',lat:t.lat,lon:t.lon,coverage:'target'},
    quality:{status:'qualified',sampling:'direct',localObservationAt:now,operationalHealth:'operational'},
    present:{state:'wet',type:'rain',lightning:'unavailable',quantity:null},...changes};
}

for (const [code,type] of [[63,'rain'],[73,'snow'],[95,'thunder']]) {
  test('R0024/H5 live model '+type+' presents supported particles without direct-observation authority', async () => {
    const f = fixture({payload:healthy({weather_code:code})}); await f.fetchWeather(); const v=f.view();
    assert.equal(f.read().weather.temp,20); assert.equal(v.qa.cache.currentEligible,true);
    assert.equal(f.gateWeatherCode(code,f.read().weather,0),code); // retained lower model positive
    assert.equal(strong(v.a.cls),true); assert.equal(v.qa.wxTruth.activePrecip,true);
    assert.equal(v.qa.wxTruth.activeThunder,false); assert.ok(v.a.rainOp>0);assert.equal(v.qa.wxTruth.permissions.rain,false);assert.equal(v.qa.wxTruth.observedPresent,false);
  });
}
test('R0024 eligible model-clear chip visibly distinguishes estimate from local observation', async () => {
  const f=fixture({payload:healthy({weather_code:0,precipitation:0,cloud_cover:0})}); await f.fetchWeather(); f.view();
  assert.equal(f.nodes.get('#wi').textContent,'☀️'); assert.match(f.nodes.get('#wi').title,/model estimate/i);
  assert.equal(f.nodes.get('#wt').textContent,'20°');
});
test('R0024 no current data is visible unknown, with no retained weather consumers',()=>{
  const f=fixture(); const v=f.view(); assert.equal(f.nodes.get('#wi').textContent,'—');
  assert.equal(v.a.wxTemp,null); assert.equal(v.a.cloudCover,0); assert.equal(v.a.windSpeed,0);
});
test('control: explicit advancing forecast retains its marked preview positive',async()=>{
  const f=fixture({hash:'timeScale=1'}); await f.fetchWeather(); f.syncWeather();
  assert.equal(f.read().weather.src,'forecast'); assert.equal(f.view().a.cls,'thunder');
});

test('R0024 A qualified synthetic present wet reaches actual rain with model dry disagreement',async()=>{
  const f=policyFixture({hash:'timeScale=1',payload:healthy({weather_code:0,precipitation:0})}); await f.fetchWeather();
  const raw=present(f), admitted=f.consume(raw); assert.equal(admitted.ok,true);
  const v=f.view(); assert.equal(v.qa.wxTruth.current,'supported-wet'); assert.equal(v.qa.wxTruth.disagreement,true);
  assert.equal(v.a.cls,'rain'); assert.equal(v.qa.wxTruth.finalDataFx,'rain'); assert.equal(v.qa.wxTruth.activePrecip,true);
  assert.equal(v.qa.wxTruth.activeThunder,false); assert(v.a.rainOp>0); assert.equal(v.qa.wxTruth.permissions.expiresAt,NOW+60000);
  assert.equal(v.qa.wxTruth.observedPrecipMm,null); assert.match(f.nodes.get('#wi').title,/SIM supported-wet/);
});
test('R0024 qualified synthetic present snow and observed lightning have separate actual positives',async()=>{
  for(const [type,lightning,want] of [['snow','unavailable','snow'],['rain','observed','thunder'],['rain','not-observed','rain']]){
    const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather();
    assert.equal(f.consume(present(f,{present:{state:'wet',type,lightning,quantity:null}})).ok,true);
    const v=f.view(); assert.equal(v.a.cls,want); assert.equal(v.qa.wxTruth.activeThunder,want==='thunder');
  }
});
test('R0024 synthetic input cannot upgrade the ordinary live lane',async()=>{
  const f=policyFixture(); await f.fetchWeather(); const admitted=f.admit(present(f)); assert.equal(admitted.ok,true); f.install(admitted);
  const v=f.view(); assert.equal(v.qa.wxTruth.lane,'live'); assert.equal(v.qa.wxTruth.current,'model-estimated-wet');
  assert.equal(v.qa.wxTruth.present.available,false); assert.equal(strong(v.a.cls),true);assert.equal(v.qa.wxTruth.permissions.rain,false);assert.equal(v.qa.wxTruth.observedPresent,false);
});
test('R0024 source-bound positive expires at its exact lease end without cloud smoothing',async()=>{
  const f=policyFixture({hash:'timeScale=1',payload:healthy({weather_code:0,precipitation:0})}); await f.fetchWeather(); f.consume(present(f));
  assert.equal(f.view().a.cls,'rain'); f.clock.now=NOW+59999; assert.equal(f.view().a.cls,'rain');
  f.clock.now++; const v=f.view(); assert.equal(strong(v.a.cls),false); assert.equal(v.a.rainOp,0);
  assert.equal(v.qa.wxTruth.present.available,false); assert.equal(v.qa.wxTruth.activePrecip,false);
  assert.match(v.qa.wxTruth.present.reason,/expired/);
});
test('R0024 rain end, source outage and target supersession each withdraw the actual wet consumer',async()=>{
  const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather(); f.consume(present(f)); assert.equal(f.view().a.cls,'rain');
  f.consume(present(f,{present:{state:'dry',type:null,lightning:'not-observed',quantity:null}}));
  assert.equal(f.view().qa.wxTruth.current,'supported-dry'); assert.equal(strong(f.view().a.cls),false); assert.equal(f.view().a.rainOp,0);
  f.consume(present(f)); assert.equal(f.view().a.cls,'rain'); f.consume(null);
  assert.equal(strong(f.view().a.cls),false); assert.match(f.view().qa.wxTruth.present.reason,/source unavailable/);
  f.consume(present(f)); f.beginRuntimeGeneration(); const v=f.view();
  assert.equal(v.qa.wxTruth.present.available,false); assert.equal(strong(v.a.cls),false); assert.equal(v.a.rainOp,0);
});
test('R0024 B operational qualified negative retains model rain as disagreement with no particles',async()=>{
  const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather(); f.consume(present(f,{present:{state:'dry',type:null,lightning:'not-observed',quantity:null}}));
  const v=f.view(); assert.equal(v.qa.wxTruth.current,'supported-dry'); assert.equal(v.qa.wxTruth.disagreement,true);
  assert.equal(v.qa.wxTruth.model.state,'wet'); assert.equal(strong(v.a.cls),false);
});
test('R0024 C dry point plus qualified nearby arrival stays independent and cannot rain locally',async()=>{
  const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather();
  const raw=present(f,{present:{state:'dry',type:null,lightning:'not-observed',quantity:null},spatial:{state:'nearby-precipitation',distanceKm:[8,12],observedAt:NOW},
    approach:{from:NOW+600000,to:NOW+1800000,derivedFrom:'qualified-fixture-trajectory'}}); f.consume(raw);
  const v=f.view(); assert.equal(v.qa.wxTruth.current,'supported-dry'); assert.equal(v.qa.wxTruth.spatial.state,'nearby-precipitation');
  assert.equal(v.qa.wxTruth.horizon.state,'approaching'); assert.equal(v.qa.wxTruth.horizon.arrival.from,NOW+600000); assert.equal(strong(v.a.cls),false);
  raw.approach.derivedFrom='current-wind'; f.consume(raw); assert.equal(f.view().qa.wxTruth.horizon.state,'nearby-without-arrival');
  assert.equal(f.view().qa.wxTruth.horizon.arrival,null);
});
test('R0024 current synthetic rain and later approach coexist without WMO veto',async()=>{
  const f=policyFixture({hash:'timeScale=1',payload:healthy({weather_code:0,precipitation:0})}); await f.fetchWeather();
  f.consume(present(f,{spatial:{state:'nearby-precipitation',distanceKm:[8,12],observedAt:NOW},approach:{from:NOW+600000,to:NOW+1800000,derivedFrom:'qualified-fixture-trajectory'}}));
  const v=f.view(); assert.equal(v.qa.wxTruth.current,'supported-wet'); assert.equal(v.qa.wxTruth.horizon.state,'approaching'); assert.equal(v.a.cls,'rain');
});
test('R0024 missing or invalid surrounding quality cannot veto separately qualified present wet',async()=>{
  const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather(); f.consume(present(f,{spatial:{state:'nearby-precipitation',distanceKm:null,observedAt:NOW}}));
  const v=f.view(); assert.equal(v.a.cls,'rain'); assert.equal(v.qa.wxTruth.spatial.state,'unavailable'); assert.equal(v.qa.wxTruth.horizon.arrival,null);
});
test('R0024 D no decoded radar observation plus model rain is estimated wet, never confirmed dry',async()=>{
  const f=policyFixture(); await f.fetchWeather(); await f.fetchRadar(); const v=f.view();
  assert.equal(v.qa.wxTruth.radarAvailable,true); assert.equal(v.qa.wxTruth.current,'model-estimated-wet');
  assert.equal(v.qa.wxTruth.present.available,false); assert.equal(v.qa.wxTruth.localOperationalHealth,'unknown');
  assert.equal(v.qa.wxTruth.localObservationAgeMs,null); assert.equal(v.qa.wxTruth.spatial.state,'unavailable'); assert.equal(v.qa.wxTruth.horizon.arrival,null);
  assert.equal(strong(v.a.cls),true);assert.equal(v.qa.wxTruth.permissions.rain,false);
});
test('R0024 E 18-minute mosaic remains diagnostic while fresh receipt grants no local observation or ETA',async()=>{
  const f=policyFixture({frameSec:NOW/1000-1080}); await f.fetchWeather(); await f.fetchRadar(); const v=f.view();
  assert.equal(v.qa.wxTruth.radarAvailable,true); assert.equal(v.qa.wxTruth.radarFrameAgeSec,1080); assert.equal(v.qa.wxTruth.radarAgeSec,0);
  assert.equal(v.qa.wxTruth.present.available,false); assert.equal(v.qa.wxTruth.horizon.arrival,null); assert.equal(strong(v.a.cls),true);assert.equal(v.qa.wxTruth.permissions.rain,false);
});
for(const [name,quality] of [['no coverage',{footprint:{kind:'point',lat:24.47,lon:39.61,coverage:'outside'}}],
  ['unknown health',{quality:{status:'qualified',sampling:'direct',localObservationAt:NOW,operationalHealth:'unknown'}}],
  ['stale underlying observation',{quality:{status:'qualified',sampling:'direct',localObservationAt:NOW-1080000,operationalHealth:'operational'}}],
  ['unknown underlying age',{quality:{status:'qualified',sampling:'direct',localObservationAt:null,operationalHealth:'operational'}}],
  ['weak returns',{quality:{status:'ambiguous',sampling:'direct',localObservationAt:NOW,operationalHealth:'operational'}}],
  ['interpolated returns',{quality:{status:'qualified',sampling:'interpolated',localObservationAt:NOW,operationalHealth:'operational'}}]]){
  test('R0024 G '+name+' cannot acquire present wet or strong negative from a fresh composite',async()=>{
    for(const state of ['wet','dry']){
      const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather();
      const a=f.consume(present(f,{...quality,present:{state,type:state==='wet'?'rain':null,lightning:'unavailable',quantity:null}})); assert.equal(a.ok,false);
      assert.equal(f.view().qa.wxTruth.present.available,false); assert.equal(strong(f.view().a.cls),false); assert.equal(f.view().qa.wxTruth.horizon.arrival,null);
      assert.notEqual(f.view().qa.wxTruth.current,'supported-dry');
    }
  });
}
for(const [name,e,want] of [['fixed site unknown precision',{intent:'fixed-site',source:'manual',accuracyM:null,acquiredAt:null},true],
  ['recent precise device',{intent:'device-position',source:'browser-geolocation',accuracyM:20,acquiredAt:NOW-60000},true],
  ['device accuracy boundary',{intent:'device-position',source:'browser-geolocation',accuracyM:250,acquiredAt:NOW},true],
  ['broad device fix',{intent:'device-position',source:'browser-geolocation',accuracyM:250.01,acquiredAt:NOW},false],
  ['coarse IP unknown accuracy',{intent:'coarse-area',source:'coarse-ip',accuracyM:null,acquiredAt:null},false],
  ['saved device unknown original fix',{intent:'device-position',source:'legacy',accuracyM:null,acquiredAt:null},false],
  ['expired original device fix',{intent:'device-position',source:'browser-geolocation',accuracyM:20,acquiredAt:NOW-300001},false],
  ['unknown intent',{intent:'unknown',source:'legacy',accuracyM:null,acquiredAt:null},false]]){
  test('R0024 F '+name+' has honest point admission',()=>{
    const cfg=fixed(); cfg.locationEvidence={...cfg.locationEvidence,...e}; cfg.savedAt=NOW; cfg.accuracy=1;
    const f=policyFixture({config:cfg,hash:'timeScale=1'}); const a=f.consume(present(f)); assert.equal(a.ok,want);
    if(want) assert.match(a.evidence.pointPolicy,e.intent==='fixed-site'?/not a device/:/actual recent/);
    else assert.equal(f.view().qa.wxTruth.present.available,false);
    assert.equal(f.target().accuracyM,e.accuracyM); assert.equal(f.target().acquiredAt,e.acquiredAt);
  });
}
test('R0024 original device fix lease expires independently of a fresh weather download',async()=>{
  const cfg=fixed(); cfg.source='localStorage'; cfg.savedAt=NOW;
  cfg.locationEvidence={...cfg.locationEvidence,intent:'device-position',source:'browser-geolocation',accuracyM:10,acquiredAt:NOW-299999};
  const f=policyFixture({hash:'timeScale=1',config:cfg}); await f.fetchWeather(); assert.equal(f.consume(present(f)).ok,true);
  assert.equal(f.view().a.cls,'rain'); f.clock.now=NOW+2; assert.equal(strong(f.view().a.cls),false);
  assert.equal(f.view().qa.wxTruth.target.fixAgeMs,300001);
});
for(const [name,change] of [['future valid interval',{validFrom:NOW+1,validUntil:NOW+60001}],['future measurement',{measurementAt:NOW+1}],
  ['future receipt',{retrievedAt:NOW+1}],['future frame',{frameAt:NOW+1}],['future issue',{issuedAt:NOW+1}],['expired valid interval',{validUntil:NOW}],['unbounded lease',{validUntil:NOW+300001}],
  ['null source time',{measurementAt:null}],['wrong source/product',{provider:'Open-Meteo',trusted:true}],['unitless amount',{units:'mm',trusted:true}],
  ['wrong target generation',{target:{generation:999,lat:24.47,lon:39.61}}]]){
  test('R0024 '+name+' rejects an apparent current fixture before the actual renderer',async()=>{
    const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather(); assert.equal(f.consume(present(f,change)).ok,false);
    assert.equal(strong(f.view().a.cls),false);
  });
}
test('R0024 model amount keeps its preceding interval and average rate, never instantaneous onset',async()=>{
  const f=policyFixture({payload:healthy({precipitation:0.4})}); await f.fetchWeather(); const q=f.view().qa.wxTruth.model.quantity;
  assert.equal(q.kind,'preceding-interval-amount'); assert.equal(q.units,'mm'); assert.equal(q.value,0.4);
  assert.equal(q.from,NOW-900000); assert.equal(q.to,NOW); assert.equal(q.averageRateMmH,1.6); assert.equal(q.instantaneous,false);
  assert.equal(f.view().qa.wxTruth.observedPrecipMm,null); assert.equal(f.view().qa.wxTruth.horizon.arrival,null);
});
test('R0024 qualified measured rate and interval amount retain different physical quantities',async()=>{
  for(const quantity of [{kind:'rate',units:'mm/h',value:1.6,from:NOW,to:NOW},{kind:'amount',units:'mm',value:0.4,from:NOW-900000,to:NOW}]){
    const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather(); assert.equal(f.consume(present(f,{present:{state:'wet',type:'rain',lightning:'unavailable',quantity}})).ok,true);
    const v=f.view(); assert.equal(v.a.cls,'rain'); assert.equal(v.qa.wxTruth.present.evidence.present.quantity.kind,quantity.kind);
    assert.equal(v.qa.wxTruth.observedPrecipMm,quantity.kind==='amount'?0.4:null);
  }
});
test('R0024 future forecast amount is stepped with its own window, no interpolated onset or fabricated probability',async()=>{
  const payload=healthy(); payload.hourly.precipitation=[0,2]; payload.hourly.precipitation_probability=[0,90];
  const f=policyFixture({payload}); await f.fetchWeather(); f.clock.now=NOW+1800000;
  const v=f.view(), fc=v.qa.wxTruth.forecast; assert.equal(f.wxAt(f.clock.now).precip,1);
  assert.equal(fc.amount.value,2); assert.equal(fc.amount.kind,'preceding-hour-amount'); assert.equal(fc.validFrom,NOW); assert.equal(fc.validUntil,NOW+3600000);
  assert.equal(fc.probability,null); assert.equal(fc.probabilityEvent,null); assert.equal(fc.issuedAt,null);
  assert.equal(v.qa.wxTruth.horizon.state,'numerical-forecast-only'); assert.equal(v.qa.wxTruth.horizon.arrival,null); assert.equal(strong(v.a.cls),false);
});
test('R0024 null precipitation is unknown while actual zero remains an estimated dry model value',async()=>{
  for(const [precipitation,want] of [[null,'unknown'],[0,'model-estimated-dry']]){
    const f=policyFixture({payload:healthy({weather_code:0,precipitation})}); await f.fetchWeather(); const v=f.view();
    assert.equal(v.qa.wxTruth.current,want); assert.equal(v.qa.wxTruth.present.available,false); assert.equal(v.qa.wxTruth.permissions.rain,false);
  }
});
test('R0024 new target generation excludes retained current, track and radar diagnostics',async()=>{
  const f=policyFixture(); await f.fetchWeather(); await f.fetchRadar(); const old=f.read().weather.target.generation;
  f.beginRuntimeGeneration(); const v=f.view(); assert.notEqual(v.qa.wxTruth.target.generation,old);
  assert.equal(v.a.wxTemp,null); assert.equal(v.a.cloudCover,0); assert.equal(v.qa.wxTruth.forecast,null); assert.equal(v.qa.wxTruth.radarAvailable,false);
});
test('R0024 synchronous acquisition captures original evidence primitives before the body can mutate config',async()=>{
  const cfg=fixed(); cfg.locationEvidence={...cfg.locationEvidence,intent:'device-position',source:'browser-geolocation',accuracyM:12,acquiredAt:NOW-50000,
    bounds:{south:24,north:25,west:39,east:40}}; let release;
  const f=policyFixture({config:cfg,fetch:()=>new Promise(resolve=>{release=resolve;})}); const pending=f.fetchWeather();
  cfg.locationEvidence.accuracyM=999; cfg.locationEvidence.acquiredAt=NOW; cfg.locationEvidence.bounds.south=-90;
  release({ok:true,json:async()=>healthy()}); await pending; const t=f.read().weather.target;
  assert.equal(t.accuracyM,12); assert.equal(t.acquiredAt,NOW-50000); assert.equal(t.bounds.south,24);
  assert.equal(f.read().weatherTrack.target.acquiredAt,NOW-50000); assert.equal(f.cache().w.target.accuracyM,12);
});
test('R0024 provider trusted flags and dense/empty/sparse palette input have no production permission path',async()=>{
  for(const options of [{rgba:[82,147,196,255]},{rgba:[0,0,0,0]},{sparse:true}]){
    const payload=healthy(); payload.current.trusted=true; payload.current.observed=true; payload.present={trusted:true,state:'wet'};
    const f=policyFixture({...options,payload}); await f.fetchWeather(); await f.fetchRadar(); const v=f.view();
    assert.equal(v.qa.wxTruth.observedPrecipMm,null); assert.equal(v.qa.wxTruth.current,'model-estimated-wet'); assert.equal(v.qa.wxTruth.activePrecip,true);assert.equal(v.qa.wxTruth.permissions.rain,false);assert.equal(v.qa.wxTruth.observedPresent,false);
  }
});
test('R0024 stable inputs reuse pure reconciliation until the next eligibility boundary',async()=>{
  const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather(); f.consume(present(f)); const first=f.decision();
  f.clock.now+=1000; assert.equal(f.decision(),first); f.clock.now=NOW+60000; assert.notEqual(f.decision(),first); assert.equal(f.decision().permissions.rain,false);
});
test('R0024 browser source with missing original fix time cannot borrow a recent settings savedAt',()=>{
  const cfg=fixed(); cfg.source='localStorage'; cfg.savedAt=NOW; cfg.locationEvidence={...cfg.locationEvidence,
    intent:'device-position',source:'browser-geolocation',accuracyM:10,acquiredAt:null};
  const f=policyFixture({hash:'timeScale=1',config:cfg}); assert.equal(f.target().acquiredAt,null);
  assert.equal(f.consume(present(f)).ok,false); assert.equal(f.view().qa.wxTruth.target.fixAgeMs,null);
});
test('R0024 conflict or unknown present states cannot borrow wet model permission',async()=>{
  for(const [state,want] of [['conflicting','conflicting'],['unknown','unknown']]){
    const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather(); f.consume(present(f,{present:{state,type:null,lightning:'unavailable',quantity:null}}));
    const v=f.view(); assert.equal(v.qa.wxTruth.current,want); assert.equal(v.qa.wxTruth.model.state,'wet'); assert.equal(strong(v.a.cls),false);
  }
});
test('R0024 qualified area negative and invalid approach remain independent from current phase',async()=>{
  const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather(); f.set({weatherTrack:null});
  f.consume(present(f,{present:{state:'dry',type:null,lightning:'not-observed',quantity:null},spatial:{state:'observed-area-no-echo',distanceKm:[0,10],observedAt:NOW},
    approach:{from:NOW+600000,to:NOW+1800000,derivedFrom:'qualified-fixture-trajectory'}}));
  const v=f.view(); assert.equal(v.qa.wxTruth.current,'supported-dry'); assert.equal(v.qa.wxTruth.spatial.state,'observed-area-no-echo');
  assert.equal(v.qa.wxTruth.horizon.state,'none-supported'); assert.equal(v.qa.wxTruth.horizon.arrival,null); assert.equal(strong(v.a.cls),false);
});
test('R0024 earlier surrounding expiry cannot withdraw a still-qualified current wet point',async()=>{
  const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather();
  f.consume(present(f,{spatial:{state:'nearby-precipitation',distanceKm:[1,2],observedAt:NOW-299999}}));
  assert.equal(f.view().qa.wxTruth.spatial.state,'nearby-precipitation'); assert.equal(f.view().a.cls,'rain');
  f.clock.now+=2; const v=f.view(); assert.equal(v.qa.wxTruth.spatial.state,'unavailable'); assert.equal(v.a.cls,'rain');
});
test('R0024 reversed time cannot resurrect a future local observation and future forecast is never current',async()=>{
  const f=policyFixture({hash:'timeScale=1'}); await f.fetchWeather(); f.consume(present(f)); assert.equal(f.view().a.cls,'rain');
  f.clock.now--; const v=f.view(); assert.equal(v.qa.wxTruth.present.available,false); assert.equal(strong(v.a.cls),false);
});
test('R0024 model data expiring after resume removes every current atmosphere input and keeps forecast separate',async()=>{
  const f=policyFixture(); await f.fetchWeather(); const first=f.decision(); f.clock.now=NOW+900001;
  const v=f.view(); assert.notEqual(f.decision(),first); assert.equal(v.qa.wxTruth.current,'unknown'); assert.equal(v.a.wxTemp,null);
  assert.equal(v.a.cloudCover,0); assert.equal(v.a.cloudLayerLow,0); assert.equal(v.a.windSpeed,0);
  assert.equal(v.qa.wxTruth.forecast.amount.value,0); assert.equal(v.qa.wxTruth.horizon.state,'numerical-forecast-only'); assert.equal(v.a.rainOp,0);
});
test('R0024 unrepresentable derived average or interval stays null rather than infinity',async()=>{
  for(const [interval,value] of [[1e-300,1e308],[1e308,0.4]]){
    const f=policyFixture({payload:healthy({interval,precipitation:value})}); await f.fetchWeather(); const q=f.view().qa.wxTruth.model.quantity;
    assert(q); assert.equal(q.averageRateMmH==null||Number.isFinite(q.averageRateMmH),true); assert.equal(q.from==null||Number.isFinite(q.from),true);
    assert.equal(f.view().qa.wxTruth.activePrecip,true);assert.equal(f.view().qa.wxTruth.observedPresent,false);
  }
});
test('R0024 caller-provided synthetic probability zero stays distinct from unavailable and grants no current condition',()=>{
  const f=policyFixture(), target=f.target();
  for(const probability of [null,0]){
    const forecast={provider:'Synthetic QA',product:'probability contract',validFrom:NOW+600000,validUntil:NOW+1800000,
      amount:{kind:'interval-amount',value:2,units:'mm'},probability,probabilityEvent:probability==null?null:{event:'precipitation',from:NOW+600000,to:NOW+1800000}};
    const d=f.reconcile({target,model:null,modelCategory:'clear',present:null,forecast,lane:'live'});
    assert.equal(d.forecast.probability,probability); assert.equal(d.current,'unknown'); assert.equal(d.horizon.state,'numerical-forecast-only');
    assert.equal(d.permissions.rain,false); assert.equal(d.horizon.arrival,null);
  }
});
test('R0024 dry centre with three wet palette neighbours remains estimated dry with unknown local evidence',async()=>{
  const f=policyFixture({sparse:true,payload:healthy({weather_code:0,precipitation:0})}); await f.fetchWeather(); await f.fetchRadar(); const v=f.view();
  assert.equal(v.qa.wxTruth.radarDiagnostic.returnCount,3); assert.equal(v.qa.wxTruth.current,'model-estimated-dry');
  assert.equal(v.qa.wxTruth.present.available,false); assert.equal(v.qa.wxTruth.spatial.state,'unavailable'); assert.equal(strong(v.a.cls),false);
});
test('R0024 explicit SIM wet positives and dry negatives retain their own source label',()=>{
  for(const [code,precip,want] of [[95,5,'thunder'],[95,0,'overcast'],[73,1,'snow'],[73,0,'overcast']]){
    const f=policyFixture({sim:{wx:code}}); f.set({weather:{code,precip,cloud:95,temp:20,src:'sim'}}); const v=f.view();
    assert.equal(v.a.cls,want); assert.equal(v.qa.wxTruth.lane,'preview'); assert.equal(v.qa.wxTruth.model.provider,'Synthetic preview');
    assert.match(f.nodes.get('#wi').title,/SIM weather preview/); assert.equal(v.qa.wxTruth.model.quantity.kind,'synthetic-preview-amount');
  }
});
test('R0024 actual accepted CONFIG hash parser supplies a configured site without manufactured fix precision',async()=>{
  const f=policyFixture({hash:'timeScale=1'}), cfg=f.context.SalahConfig.resolve('#lat=24.47&lon=39.61&tz=UTC&units=c').cfg;
  assert.equal(cfg.locationEvidence.intent,'fixed-site'); assert.equal(cfg.locationEvidence.accuracyM,null); assert.equal(cfg.locationEvidence.acquiredAt,null);
  f.set({config:cfg}); await f.fetchWeather(); const captured=f.read().weather.target;
  assert.equal(captured.intent,'fixed-site'); assert.equal(captured.source,'hash'); assert.equal(captured.accuracyM,null); assert.equal(captured.acquiredAt,null);
  assert.equal(f.consume(present(f)).ok,true); assert.equal(f.view().a.cls,'rain');
});
test('R0024 actual accepted CONFIG save/load preserves original browser epoch while WEATHER declines an expired device claim',async()=>{
  const f=policyFixture({hash:'timeScale=1'}), C=f.context.SalahConfig;
  const cfg=C.normalize({lat:24.47,lon:39.61,tz:'UTC',units:'c',source:'browser-geolocation',origin:'browser-geolocation',
    locationEvidence:{intent:'device-position',source:'browser-geolocation',accuracyM:12,acquiredAt:NOW-600000,provider:null,area:null,bounds:null}});
  assert.equal(C.saveLocal(cfg).ok,true); const saved=C.loadLocal(); assert(saved); assert.equal(saved.source,'localStorage');
  assert.equal(saved.savedAt,NOW); assert.equal(saved.locationEvidence.acquiredAt,NOW-600000);
  f.set({config:saved}); await f.fetchWeather(); const captured=f.read().weather.target;
  assert.equal(captured.source,'browser-geolocation'); assert.equal(captured.acquiredAt,NOW-600000); assert.equal(captured.accuracyM,12);
  assert.equal(f.consume(present(f)).ok,false); assert.equal(f.view().qa.wxTruth.target.fixAgeMs,600000);
});
