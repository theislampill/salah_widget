'use strict';
// F01: real admission, complete native owners and actual foreground capture.
// DOM/transport/time and retained-alpha readback are controlled boundaries;
// this is source-state ordering evidence, not browser pixel qualification.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {fixture,copy,sourcePath,sourceValid}=require('./weather-no-timetable-fixture.cjs');
const native=import('../real-sky/native-composition.mjs');
const read=h=>copy(h.run(`({model:!!model(),selected:!!selectedWeather(),lane:weatherDecision().lane,
 cov:[cloudState.covLow,cloudState.covMid,cloudState.covHigh],targets:[cloudState.tgtLow,cloudState.tgtMid,cloudState.tgtHigh],ready:_cloudReady,
 density:_colDens?Math.max(..._colDens):0,population:_cloudMotion.population,phase:_cloudMotion.phase,life:_cloudMotion.life,wander:_cloudMotion.wander,
 receipt:cloudPublicationReceipt(),effects:_lastWeatherEffects?.receipt,scene:skySceneIdentity()})`));
async function healthyReplacement(source){
 const h=await fixture({source,fetch:async(u,init,h,payload)=>u.hostname==='api.open-meteo.com'?
  {ok:true,json:async()=>payload({time:'2026-09-08T23:46'})}:new Promise(()=>{})});
 h.ctx.__recordA=h.run('weather');h.at(951000);
 assert(h.run('adoptPrayerBundle(__fixtureNextPrayer,"09-09-2026",null,true,false)'),'real next-day prayer admission');
 h.run('render();paintClouds(simNow()/1000);tieRainToClouds()');
 assert(read(h).model,'actual next-day model is complete');
 assert(h.run('weatherEligibility(__recordA).eligible'),'A remains independently current');
 const before=read(h);h.ctx.__receiptA=h.run('cloudPublicationReceipt()');
 await h.refresh({time:'2026-09-09T00:00',cloud_cover_low:80,cloud_cover_mid:75,cloud_cover_high:50});
 h.ctx.__recordB=h.run('weather');
 assert.notEqual(h.ctx.__recordB,h.ctx.__recordA,'actual fetch replaces the admitted object');
 assert(h.run('selectedWeather()===__recordB'),'B is independently selected');
 assert(read(h).model,'prayer admission remains available after acquisition');
 return {h,before};
}
async function captureBoundary(h,run){
 const {NativeForegroundCapture}=await native;
 const makeCanvas=()=>{let alpha=0;const c={width:325,height:530,getBoundingClientRect:()=>({left:0,top:0,width:325,height:530})};
  c.getContext=()=>({resetTransform(){},clearRect(){alpha=0;},createLinearGradient:()=>({addColorStop(){}}),fillRect(){},setTransform(){},
   drawImage(source){if(source===h.select('.cloudcanvas'))alpha=h.raster.currentFills?192:0;},
   getImageData(x,y,w,height){const data=new Uint8ClampedArray(w*height*4);data[3]=alpha;return {data};}});return c;};
 const saved={document:globalThis.document,window:globalThis.window,getComputedStyle:globalThis.getComputedStyle};
 globalThis.document={createElement:makeCanvas,querySelector:q=>q==='.c'||q==='.cloudcanvas'?h.select(q):null};
 globalThis.window={SalahNativeSkyHost:{reconcileClouds:()=>h.run('reconcileCloudPublication()'),lunarSurface:()=>null}};
 globalThis.getComputedStyle=()=>({filter:'none',visibility:'hidden',opacity:'1'});
 try{return await run(new NativeForegroundCapture(makeCanvas()));}
 finally{for(const [k,v]of Object.entries(saved))if(v===undefined)delete globalThis[k];else globalThis[k]=v;}
}
function sameDeck(actual,expected){
 for(const key of ['cov','targets','ready','density','population','phase','life','wander','receipt','effects'])assert.deepEqual(actual[key],expected[key],key+' must remain consumed A');
}
function eased(actual,before,gain=.08){
 const expected=before.cov.map((v,i)=>v+([.8,.75,.5][i]-v)*gain);
 actual.cov.forEach((v,i)=>assert(Math.abs(v-expected[i])<1e-12,'one ordinary healthy easing step at layer '+i));
 assert.equal(actual.ready,true);assert.deepEqual(actual.targets,[.8,.75,.5]);
 assert.equal(actual.population,before.population);assert.deepEqual(actual.phase,before.phase);
}
for(const order of ['capture-before-render','render-before-capture'])test('F01 healthy full-model refresh keeps normal easing: '+order,async()=>{
 const {h,before}=await healthyReplacement();
 if(order==='render-before-capture')h.run('render()');
 const preCapture=read(h);
 await captureBoundary(h,async capture=>{
  const frame=capture.capture(183);
  assert.equal(frame.cloudRGBA[3],192,'an eligible active A deck cannot disappear before normal full render');
  sameDeck(read(h),preCapture);
 });
 if(order==='capture-before-render')h.run('render()');
 h.run('paintClouds(simNow()/1000);tieRainToClouds()');
 eased(read(h),before);
 assert.equal(h.run('cloudPublicationCurrent(__receiptA)'),false,'B publication supersedes A callback identity');
 assert.equal(h.run('_cloudPublication.record===__recordB'),true);
});


// F01 bounded authority controls use passive reads; qaState() is not called.
function clearDeck(h){
 const state=read(h);assert.deepEqual(state.cov,[0,0,0]);assert.deepEqual(state.targets,[0,0,0]);
 assert.equal(state.ready,false);assert.equal(state.density,0);assert.equal(h.raster.currentFills,0);
}
async function refused(h){
 const before=read(h),raster={...h.raster};
 assert.equal(h.run('cloudPublicationCurrent(__receiptA)'),false,'pure final guard refuses the old authority');
 sameDeck(read(h),before);assert.deepEqual(h.raster,raster,'final guard does not repair raster');
 await captureBoundary(h,capture=>assert.equal(capture.capture(183).cloudRGBA[3],0));
 clearDeck(h);
}
test('F01 repeated captures and final checks retain A without a producer, timestamp or easing mutation',async()=>{
 const {h,before}=await healthyReplacement(),raster={...h.raster},requests=h.calls.length;
 h.run(`globalThis.__producerCounts={};for(const name of ['render','atmosphere','paint','applyCloudState','paintClouds','syncWeather','fetchWeather','fetchRadar']){
  const actual=globalThis[name];if(typeof actual!=='function')throw Error('missing actual producer '+name);
  __producerCounts[name]=0;globalThis[name]=function(...args){__producerCounts[name]++;return actual.apply(this,args);};
 }`);
 await captureBoundary(h,capture=>{
  for(let i=0;i<8;i++){
   const frame=capture.capture(183);
   assert.equal(frame.cloudRGBA[3],192);assert.equal(frame.cloudAuthority,h.ctx.__receiptA);
   assert.equal(h.run('cloudPublicationCurrent(__receiptA)'),true);
  }
 });
 sameDeck(read(h),before);assert.deepEqual(h.raster,raster);assert.equal(h.calls.length,requests);
 for(const count of Object.values(h.ctx.__producerCounts))assert.equal(count,0,'consumer guard cannot invoke a producer');
 assert.equal(h.run('_cloudPublication.record===__recordA&&weather===__recordB'),true,'candidate B does not replace consumed A');
 assert.equal(h.run('__recordA.currentValidAt===__receiptA.sourceValidAt&&__recordA.retrievedAt===__receiptA.retrievedAt'),true);
});
test('F01 fresh B cannot retain A after the genuine model becomes unavailable',async()=>{
 const {h}=await healthyReplacement();h.run('today=null;');
 assert.equal(read(h).model,false);assert(h.run('weatherEligibility(__recordA).eligible'));assert(read(h).selected);
 await refused(h);
});
for(const kind of ['cold','already-withdrawn'])test('F01 '+kind+' consumer cannot restore a deck from weather and model availability alone',async()=>{
 const h=kind==='cold'?await fixture({cold:true}):(await healthyReplacement()).h;
 if(kind==='cold')assert(h.run('adoptPrayerBundle(__fixturePrayer,"08-09-2026",null,true,false)'));
 else h.run('withdrawCloudState(weatherDecision(),"controlled prior withdrawal")');
 assert(read(h).model&&read(h).selected);assert.notEqual(read(h).receipt.state,'eligible-published');
 await captureBoundary(h,capture=>assert.equal(capture.capture(183).cloudRGBA[3],0));
 clearDeck(h);h.run('render();paintClouds(simNow()/1000)');assert(read(h).ready);assert(h.raster.currentFills>0);
});
async function ageCase(key,age,source){
 const h=await fixture({source});
 // Original admission metadata is supplied once through the real record owner,
 // including a future-source/receipt rollback case; no retained record is edited.
 const checkAt=key==='currentValidAt'?sourceValid+60000+age:sourceValid+951000;
 const sourceAt=key==='currentValidAt'?sourceValid+60000:sourceValid+900000;
 const retrievedAt=key==='retrievedAt'?checkAt-age:checkAt-1000;
 const publishAt=age===900001?checkAt-1:age===-1?checkAt+1:checkAt;
 h.at(publishAt-sourceValid);
 const nextDay=publishAt>=sourceValid+900000;
 assert(h.run(nextDay?'adoptPrayerBundle(__fixtureNextPrayer,"09-09-2026",null,true,false)':'adoptPrayerBundle(__fixturePrayer,"08-09-2026",null,true,false)'));
 h.ctx.__caseCurrent=h.payload({time:new Date(sourceAt+3*3600000).toISOString().slice(0,16)}).current;
 h.ctx.__caseRetrievedAt=retrievedAt;
 h.run('weather=admitWeatherRecord(__caseCurrent,{units,zone:tz,retrievedAt:__caseRetrievedAt,target:currentWeatherTarget()});');
 h.ctx.__recordA=h.run('weather');assert(h.run('weatherEligibility(__recordA).eligible'),'A is eligible when its real full atmosphere publishes');
 h.run('render();paintClouds(simNow()/1000)');h.ctx.__receiptA=h.run('cloudPublicationReceipt()');assert(h.raster.currentFills>0);
 h.at(checkAt-sourceValid);
 h.ctx.__freshCurrent=h.payload({time:new Date(checkAt+3*3600000).toISOString().slice(0,16),cloud_cover_low:80,cloud_cover_mid:75,cloud_cover_high:50}).current;
 h.run('weather=admitWeatherRecord(__freshCurrent,{units,zone:tz,retrievedAt:Date.now(),target:currentWeatherTarget()});');
 h.ctx.__recordB=h.run('weather');
 assert.notEqual(h.ctx.__recordA,h.ctx.__recordB);assert(read(h).model&&read(h).selected);
 const own=copy(h.run('weatherEligibility(__recordA)'));
 assert.equal(own[key==='currentValidAt'?'sourceAgeMs':'receiptAgeMs'],age);
 const other=own[key==='currentValidAt'?'receiptAgeMs':'sourceAgeMs'];assert(other>=0&&other<=900000,'other A age remains eligible');
 assert(h.run('weatherEligibility(__recordB).eligible'),'fresh B cannot supply A age');
 return h;
}
for(const key of ['currentValidAt','retrievedAt'])for(const [age,eligible]of [[899999,true],[900000,true],[900001,false],[-1,false]])
 test('F01 owns A '+key+' boundary with fresh B: '+age,async()=>{
  const h=await ageCase(key,age);
  if(!eligible)return refused(h);
  const before=read(h);assert.equal(h.run('cloudPublicationCurrent(__receiptA)'),true);
  await captureBoundary(h,capture=>assert.equal(capture.capture(183).cloudRGBA[3],192));
  sameDeck(read(h),before);
 });
test('F01 successive fresh B/C records do not renew A or its cached decision lifetime',async()=>{
 const {h,before}=await healthyReplacement();
 await captureBoundary(h,capture=>assert.equal(capture.capture(183).cloudRGBA[3],192));
 h.at(954000);h.ctx.__thirdCurrent=h.payload({time:'2026-09-09T00:00',cloud_cover_low:70}).current;
 h.run('weather=admitWeatherRecord(__thirdCurrent,{units,zone:tz,retrievedAt:Date.now(),target:currentWeatherTarget()});');
 const third=h.run('weather');assert.notEqual(third,h.ctx.__recordB);assert(read(h).selected);
 await captureBoundary(h,capture=>assert.equal(capture.capture(183).cloudRGBA[3],192));
 sameDeck(read(h),before);const decision=h.run('weatherDecision()');h.ctx.__candidateDecision=decision;
 h.at(960001);assert.equal(h.run('weatherDecision()===__candidateDecision'),true,'candidate decision remains cached across A expiry');
 assert(read(h).model&&read(h).selected);assert.equal(h.run('weatherEligibility(__recordA).eligible'),false);
 assert.equal(h.run('cloudPublicationReceipt()'),h.ctx.__receiptA);await refused(h);
 assert.equal(h.ctx.__recordA.currentValidAt,before.receipt.sourceValidAt);assert.equal(h.ctx.__recordA.retrievedAt,before.receipt.retrievedAt);
});
function setNativePreview(h){
 // The source fixture has no background renderer; only its optional notify sink is contained.
 h.ctx.SalahNativeSkyHost.notify=()=>{};
 h.run('window.SalahClock.set({rate:2,utcMs:Date.now()})');
}
for(const kind of ['generation','coordinates','scene','mode'])test('F01 '+kind+' replacement cannot reuse the old active receipt',async()=>{
 const {h,before}=await healthyReplacement();
 if(kind==='generation')h.run('beginRuntimeGeneration()');
 if(kind==='coordinates')h.run('beginRuntimeGeneration();lat=40;lon=-74;');
 if(kind==='scene')h.run('beginSkyScene()');
 if(kind==='mode')setNativePreview(h);
 assert.equal(h.run('cloudPublicationCurrent(__receiptA)'),false);
 if(kind!=='mode')await captureBoundary(h,capture=>assert.equal(capture.capture(183).cloudRGBA[3],0));
 else{
  assert.notEqual(read(h).scene,before.scene);assert.notEqual(h.run('cloudPublicationReceipt()'),h.ctx.__receiptA);
  assert.equal(h.run('weatherDecision().lane'),'preview');
 }
});
async function previewReplacement(kind,source){
 const forecast=kind==='forecast';
 const h=await fixture({source,hash:forecast?'&timeScale=2':'&simWx=3&simCloud=95',
  ...(forecast?{fetch:async(u,init,h,payload)=>{
   if(u.hostname!=='api.open-meteo.com')return new Promise(()=>{});
   return {ok:true,json:async()=>({...payload(),hourly:{time:['2026-09-08T22:00','2026-09-09T01:00'],
    temperature_2m:[24,24],weather_code:[3,3],cloud_cover:[95,95],cloud_cover_low:[92,92],cloud_cover_mid:[90,90],cloud_cover_high:[60,60],
    wind_speed_10m:[7,7],wind_direction_10m:[225,225],is_day:[0,0]}})};
  }}:{})});
 assert(read(h).model&&read(h).ready);assert(h.raster.currentFills>0);
 if(forecast){
  assert(h.run('weatherTrack&&weatherTrack.provider==="Open-Meteo"'));
  setNativePreview(h);h.run('paintClouds(simNow()/1000)');
 }
 h.ctx.__recordA=h.run('weather');h.ctx.__receiptA=h.run('cloudPublicationReceipt()');const before=read(h);
 assert.equal(h.ctx.__recordA.src,forecast?'forecast':'sim');
 for(const key of ['currentValidAt','retrievedAt','currentIntervalSec'])assert.equal(Object.hasOwn(h.ctx.__recordA,key),false,'preview has no fabricated '+key);
 h.run(forecast?'syncWeather()':'startWeather(true)');h.ctx.__recordB=h.run('weather');
 assert.notEqual(h.ctx.__recordA,h.ctx.__recordB,'the real preview producer replaces its record object');
 assert.equal(h.ctx.__recordB.src,h.ctx.__recordA.src);assert(read(h).selected&&read(h).model);
 assert.equal(h.run('weatherEligibility(__recordA).eligible'),false,'preview retains its own non-live rule');
 return {h,before};
}
for(const kind of ['simulation','forecast'])for(const missingModel of [false,true])test('F01 genuine '+kind+' object turnover; missing model='+missingModel,async()=>{
 const {h,before}=await previewReplacement(kind);
 if(missingModel){h.run('today=null;');await refused(h);return;}
 await captureBoundary(h,capture=>{assert.equal(capture.capture(183).cloudRGBA[3],192);assert.equal(h.run('cloudPublicationCurrent(__receiptA)'),true);});
 sameDeck(read(h),before);
 h.run('render();paintClouds(simNow()/1000)');assert(read(h).ready);assert(h.raster.currentFills>0);assert.equal(h.run('cloudPublicationCurrent(__receiptA)'),false);
});
function installPresent(h,leaseMs){
 const t=copy(h.run('currentWeatherTarget()')),now=h.clock.wall;
 h.ctx.__presentInput={scope:'simulation-fixture',provider:'Synthetic QA',product:'present/nearby contract',policy:'synthetic-present-v1',
  target:{generation:t.generation,lat:t.lat,lon:t.lon},measurementAt:now,validFrom:now,validUntil:now+leaseMs,retrievedAt:now,
  frameAt:now,issuedAt:now,units:'categorical',footprint:{kind:'point',lat:t.lat,lon:t.lon,coverage:'target'},
  quality:{status:'qualified',sampling:'direct',localObservationAt:now,operationalHealth:'operational'},
  present:{state:'wet',type:'rain',lightning:'unavailable',quantity:null}};
 assert(h.run('(weatherSynthetic=admitWeatherFixture(__presentInput,currentWeatherTarget(),Date.now())).ok'));
}
for(const renewedCandidate of [false,true])test('F01 consumed direct evidence lease cannot be replaced by candidate evidence; renewed='+renewedCandidate,async()=>{
 const h=await fixture({hash:'&simWx=3&simCloud=95'});installPresent(h,1000);
 h.run('render();paintClouds(simNow()/1000)');h.ctx.__recordA=h.run('weather');h.ctx.__receiptA=h.run('cloudPublicationReceipt()');
 const consumed=h.run('_cloudPublication.decision.present.evidence');assert(consumed);assert(h.raster.currentFills>0);
 h.run('startWeather(true)');assert.notEqual(h.run('weather'),h.ctx.__recordA);assert.equal(h.run('cloudPublicationCurrent(__receiptA)'),true);
 h.at(891000);if(renewedCandidate)installPresent(h,60000);
 assert(read(h).model&&read(h).selected);assert.equal(read(h).lane,'simulation-fixture');
 if(renewedCandidate)assert.notEqual(h.run('weatherDecision().present.evidence'),consumed);
 await refused(h);
});
for(const publishesB of [false,true])test('F01 pending actual solar decode respects active receipt; B published='+publishesB,async()=>{
 const {h}=await healthyReplacement(),{NativeSolarMaskPublication}=await native;
 const images=[],writes=[],errors=[];
 const publication=new NativeSolarMaskPublication(()=>{const image={decode:()=>new Promise(resolve=>image.resolve=resolve)};images.push(image);return image;});
 await captureBoundary(h,capture=>{
  const frame=capture.capture(183);assert.equal(frame.cloudRGBA[3],192);assert.equal(frame.cloudAuthority,h.ctx.__receiptA);
  publication.publish('url("data:image/png;base64,F01")',()=>{
   if(!h.run('cloudPublicationCurrent(__receiptA)'))return false;
   writes.push(frame.cloudRGBA[3]);return true;
  },e=>errors.push(e),{cloudAuthority:frame.cloudAuthority});
 });
 if(publishesB)h.run('render()');
 const before=read(h),raster={...h.raster};images[0].resolve();for(let i=0;i<6;i++)await Promise.resolve();
 assert.deepEqual(errors,[]);assert.equal(writes.length,publishesB?0:1);
 sameDeck(read(h),before);assert.deepEqual(h.raster,raster);
 assert.equal(publication.displayed!==null,!publishesB);publication.dispose();
});
