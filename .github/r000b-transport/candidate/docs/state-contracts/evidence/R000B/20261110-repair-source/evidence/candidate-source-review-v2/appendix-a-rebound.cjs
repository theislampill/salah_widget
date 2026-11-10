'use strict';
const fs=require('node:fs'),cp=require('node:child_process'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=process.cwd(),head='9dabdcf338a7307c0256dcdccac48326b357f0d5';
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
for(const p of ['tests/weather-no-timetable-fixture.cjs','tests/r001d-harness.cjs','tests/native-script-contract.js','src/native/index.html','src/native/config.js','real-sky/native-composition.mjs'])assert.equal(sha(fs.readFileSync(p)),p==='src/native/index.html'?'b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f':sha(cp.execFileSync('git',['show',head+':'+p])),'explicit repaired source / otherwise frozen 9dab fixture input '+p);
const {fixture}=require('./tests/weather-no-timetable-fixture.cjs');
(async()=>{
 const {NativeForegroundCapture}=await import('./real-sky/native-composition.mjs');
 async function scenario(order){
  const h=await fixture({fetch:async(u,init,h,payload)=>u.hostname==='api.open-meteo.com'?{ok:true,json:async()=>payload({time:'2026-09-08T23:46'})}:new Promise(()=>{})});
  const firstRecord=h.run('weather');h.ctx.__oldRecord=firstRecord;
  h.at(951000);assert(h.run('adoptPrayerBundle(__fixtureNextPrayer,"09-09-2026",null,true,false)'));h.run('render()');h.paint();
  assert(h.read().model);assert(h.run('weatherEligibility(__oldRecord).eligible'));
  const before=h.read();await h.refresh({time:'2026-09-09T00:00',cloud_cover_low:80,cloud_cover_mid:75,cloud_cover_high:50});
  assert.notEqual(h.run('weather'),firstRecord);assert(h.read().model);assert(h.read().selected);
  const state=()=>({model:!!h.run('model()'),oldEligible:h.run('weatherEligibility(__oldRecord)'),selected:h.read().selected,cov:h.read().cov,targets:h.read().targets,ready:h.read().ready,raster:h.read().raster.currentFills,receipt:h.read().publication,population:h.read().population,phase:h.read().phase});
  const preCapture=state();if(order==='render-before-capture')h.run('render()');
  const makeCanvas=()=>{let alpha=0;const c={width:325,height:530,getBoundingClientRect:()=>({left:0,top:0,width:325,height:530})};const ctx={resetTransform(){},clearRect(){alpha=0;},createLinearGradient:()=>({addColorStop(){}}),fillRect(){},setTransform(){},drawImage(source){if(source===h.select('.cloudcanvas'))alpha=h.raster.currentFills?192:0;},getImageData(x,y,w,height){const data=new Uint8ClampedArray(w*height*4);data[3]=alpha;return {data};}};c.getContext=()=>ctx;return c;};
  const save={document:globalThis.document,window:globalThis.window,getComputedStyle:globalThis.getComputedStyle};
  globalThis.document={createElement:makeCanvas,querySelector:q=>q==='.c'?h.select(q):q==='.cloudcanvas'?h.select(q):null};
  globalThis.window={SalahNativeSkyHost:{reconcileClouds:()=>h.run('reconcileCloudPublication()'),lunarSurface:()=>null}};
  globalThis.getComputedStyle=()=>({filter:'none',visibility:'hidden',opacity:'1'});
  let captured;try{captured=new NativeForegroundCapture(makeCanvas()).capture(183);}finally{for(const [k,v]of Object.entries(save))if(v===undefined)delete globalThis[k];else globalThis[k]=v;}
  const afterCapture=state();if(order==='capture-before-render')h.run('render()');
  h.paint();const afterRenderPaint=state();
  const pick=w=>({code:w.code,cloud:w.cloud,cloudLow:w.cloudLow,cloudMid:w.cloudMid,cloudHigh:w.cloudHigh,currentValidAt:w.currentValidAt,retrievedAt:w.retrievedAt,target:w.target});
  console.log(JSON.stringify({order,clock:h.clock,recordA:pick(firstRecord),recordB:pick(h.run('weather')),beforeReplacement:{cov:before.cov,ready:before.ready,model:before.model},preCapture,afterCapture,capturedAlpha:captured.cloudRGBA[3],afterRenderPaint,expectedHealthyEase:before.cov.map((v,i)=>v+([.8,.75,.5][i]-v)*.08)},null,2));
 }
 await scenario('capture-before-render');await scenario('render-before-capture');
})().catch(e=>{console.error(e);process.exitCode=1;});
