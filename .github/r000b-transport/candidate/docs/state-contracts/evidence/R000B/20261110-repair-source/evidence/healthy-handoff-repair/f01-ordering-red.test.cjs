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
