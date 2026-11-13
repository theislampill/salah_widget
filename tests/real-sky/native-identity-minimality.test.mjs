import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {NativeSkyLifecycle} from '../../real-sky/native-lifecycle.mjs';
import {nativeIdentity,nativeJob,nativeResultCurrent} from '../../real-sky/native-contract.mjs';

// R0034 (issue 101) ISM-SKY-006: refined target identity minimality/completeness
// and truthful churn availability. Uses the REAL NativeSkyLifecycle with a fake
// monotonic clock, as the audit probe docs/audit/post-rlgwo/probes/D/
// forecast-identity-probe.mjs does. Worker durations are parameters, not measurements.
// Run: node --test tests/real-sky/native-identity-minimality.test.mjs

const BASE=Date.UTC(2026,10,12,12,0,0);
function scene(rate,weather){
 return {utcMs:BASE,lat:24.47,lon:39.61,heightM:0,generation:1,sceneIdentity:'24.47|39.61|Asia/Riyadh|x:'+rate,tz:'Asia/Riyadh',timeScale:rate,units:'c',lp:0,reducedMotion:false,paused:false,
  camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},allowEstimates:true,weather};
}
// Weather as wxAt() would produce it: refreshed once per simulated second
// (render()/syncWeather()), linearly interpolated within the hour.
const constant=()=>({src:'forecast',temp:20,rh:40,vis:20000,cloud:30,code:2,wind:3});
const unconsumed=f=>({src:'forecast',temp:20,rh:40+10*f,vis:20000,cloud:30+20*f,code:2,wind:3+f});
const visLerp=f=>({src:'forecast',temp:20,rh:40,vis:10000+5000*f,cloud:30,code:2,wind:3});

async function run({rate,weather,workerMs,wallMs=20000,mutate=null}){
 let clock=0;const pending=[],events={accepted:0,invalidations:0,avail:[]};
 const snap=()=>{const sim=BASE+clock*rate,f=((Math.floor(sim/1000)*1000)/3600000)%1;const s={...scene(rate,weather(f)),utcMs:sim};return mutate?mutate(s,clock):s;};
 const lc=new NativeSkyLifecycle({capture:snap,now:()=>clock,physical:true,
  execute:job=>new Promise(res=>pending.push({at:clock+workerMs,res:()=>res({status:'ready',raster:{},utcMs:job.observer.utcMs})})),
  onResult:()=>{events.accepted++;},onInvalidate:()=>{events.invalidations++;},onError:()=>{},onAvailability:v=>events.avail.push({...v,at:clock})});
 for(clock=0;clock<=wallMs;clock+=50){
  lc.current(lc.latest,snap());
  if(clock%500===0)lc.request();
  for(let i=pending.length-1;i>=0;i--)if(pending[i].at<=clock)pending.splice(i,1)[0].res();
  await new Promise(r=>setImmediate(r));
 }
 const state=lc.state;lc.dispose();
 return {accepted:events.accepted,invalidations:state.invalidations,superseded:state.superseded,rejected:state.rejected,avail:events.avail,state};
}

test('ES34-01 interpolated unconsumed weather fields do not starve refinement: equal to the constant-weather control in every cell',async()=>{
 for(const workerMs of [300,800,1200])for(const rate of [1,2,10]){
  const control=await run({rate,weather:constant,workerMs}),lerp=await run({rate,weather:unconsumed,workerMs});
  assert.deepEqual({accepted:lerp.accepted,invalidations:lerp.invalidations,superseded:lerp.superseded,rejected:lerp.rejected},
   {accepted:control.accepted,invalidations:control.invalidations,superseded:control.superseded,rejected:control.rejected},`${workerMs} ms, rate ${rate}`);
  assert.ok(lerp.accepted>0,`${workerMs} ms, rate ${rate} accepts`);
  assert.ok(!lerp.avail.some(a=>a.reason==='target-churn'),'no churn is reported for unconsumed fields');
 }
});

const ref={...scene(2,{src:'forecast',temp:20,rh:40,vis:12000,cloud:30,code:2,wind:3}),elevationSource:'e',elevationOwner:null};
test('ES34-02 identity completeness: each consumed input changing alone changes identity and the job',()=>{
 const changes={
  'visibility below 20000':s=>({...s,weather:{...s.weather,vis:11000}}),
  temperature:s=>({...s,weather:{...s.weather,temp:21}}),
  units:s=>({...s,units:'f'}),
  'weather source':s=>({...s,weather:{...s.weather,src:'model'}}),
  'weather presence':s=>({...s,weather:null}),
  'light pollution':s=>({...s,lp:.5}),
  camera:s=>({...s,camera:{...s.camera,azDeg:170}}),
  elevation:s=>({...s,heightM:12}),
  'reduced motion':s=>({...s,reducedMotion:true}),
  'estimates flag':s=>({...s,allowEstimates:false}),
  generation:s=>({...s,generation:2}),
  sceneIdentity:s=>({...s,sceneIdentity:'other'})};
 const id=nativeIdentity(ref);
 for(const [name,change] of Object.entries(changes)){
  const next=change(ref);
  assert.notEqual(nativeIdentity(next),id,name);
  assert.equal(nativeResultCurrent(nativeJob(ref,true),next),false,name+' fences an old result');
 }
 // Every job field derived from weather is a function of the identity's weather element.
 const job=nativeJob(ref,true);
 assert.equal(job.observer.temperatureC,20);assert.equal(job.native.weatherSource,'forecast');assert.equal(job.native.weatherAccepted,true);
 assert.ok(Math.abs(job.options.atmosphere.aerosolTau550-(.06+.3*(1-12000/20000)))<1e-15);
});

test('ES34-03 identity minimality: rh, cloud, code or wind alone leave identity, currentness, epoch and displayed unchanged',async()=>{
 const id=nativeIdentity(ref),job=nativeJob(ref,true);
 for(const field of ['rh','cloud','code','wind']){
  const next={...ref,weather:{...ref.weather,[field]:ref.weather[field]+17}};
  assert.equal(nativeIdentity(next),id,field);assert.equal(nativeResultCurrent(job,next),true,field);
  assert.deepEqual({...nativeJob(next,true),native:{...nativeJob(next,true).native,identity:null}},{...job,native:{...job.native,identity:null}},field+' leaves the job identical');
 }
 // Saturated visibility is one aerosol term: a vis change above 20000 m is not a job change.
 assert.equal(nativeIdentity({...ref,weather:{...ref.weather,vis:25000}}),nativeIdentity({...ref,weather:{...ref.weather,vis:40000}}));
 let state={...ref,timeScale:0},mono=0;const painted=[],invalidated=[];
 const lc=new NativeSkyLifecycle({capture:()=>state,now:()=>mono,execute:async()=>({status:'ready',raster:{}}),onResult:r=>painted.push(r),onInvalidate:r=>invalidated.push(r)});
 await lc.request();for(let i=0;i<10;i++)await Promise.resolve();
 const epoch=lc.epoch,displayed=lc.displayed;assert.ok(displayed);
 for(const field of ['rh','cloud','code','wind']){state={...state,weather:{...state.weather,[field]:state.weather[field]+1}};lc.observe();}
 assert.equal(lc.epoch,epoch);assert.equal(lc.displayed,displayed);assert.deepEqual(invalidated,['new accepted native scene']);
 assert.equal(lc.current(displayed),true);
 state={...state,weather:{...state.weather,vis:13000}};lc.observe();
 assert.equal(lc.epoch,epoch+1,'a consumed change still withdraws');assert.equal(lc.displayed,null);lc.dispose();
});

test('ES34-04 residual churn of a consumed input is reported within two drops, never as refining, and clears on acceptance',async()=>{
 const r=await run({rate:2,weather:visLerp,workerMs:1200});
 assert.equal(r.accepted,0,'the model predicts starvation in this cell');
 const first=r.avail.findIndex(a=>a.reason==='target-churn');
 assert.ok(first>=0,'churn reported');
 assert.equal(r.avail[first].status,'unavailable');assert.ok(r.avail[first].drops<=2);assert.deepEqual(r.avail[first].inputs,['weather']);
 assert.ok(r.avail[first].at<=4000,'reported within the first two submission windows');
 const after=r.avail.slice(first).filter(a=>a.reason!=='disposed');
 assert.ok(after.every(a=>a.reason==='target-churn'),'a further identity move keeps the report instead of flipping back to pending');
 // Recovery: inputs stop changing after 10 s; the next result is accepted and the reason clears.
 const rec=await run({rate:2,weather:visLerp,workerMs:1200,mutate:(s,clock)=>clock>=10000?{...s,weather:visLerp(.25)}:s});
 const i=rec.avail.findIndex(a=>a.reason==='target-churn'),j=rec.avail.findIndex(a=>a.reason==='current-frame');
 assert.ok(i>=0&&j>i,'available after churn');assert.ok(rec.accepted>0);
 assert.deepEqual(rec.state.churn,{drops:0,inputs:[]});
});

test('ES34-04 badge: churn shows a truthful unavailable string, never "refining…"',()=>{
 const src=fs.readFileSync(new URL('../../real-sky/native-host.mjs',import.meta.url),'utf8');
 const publish=src.slice(src.indexOf(' function publish(){'),src.indexOf(' function clear(reason='));
 const text=(availability,preview=true,status='pending')=>{const s={window:{SalahSkyPreview:{state:{status:preview?'ready':'pending'}}},status:{status,availability,errors:[]},badge:{},canvas:{dataset:{}}};vm.createContext(s);vm.runInContext(publish+'\npublish();',s);return s.badge.textContent;};
 assert.equal(text({status:'unavailable',reason:'target-churn',inputs:['weather']}),'Sky preview · refinement unavailable while weather keeps changing');
 assert.equal(text({status:'unavailable',reason:'target-churn',inputs:['weather']},false,'unavailable'),'Refinement unavailable while weather keeps changing');
 assert.equal(text({status:'unavailable',reason:'target-churn',inputs:['camera']}),'Sky preview · refinement unavailable while sky inputs keep changing');
 assert.equal(text({status:'pending',reason:'new accepted native scene'}),'Sky preview · refining…','ordinary pending is unchanged');
 assert.equal(text({status:'unavailable',reason:'rate-throughput',rate:120}),'Sky preview · refinement unavailable at 120×','throughput wording unchanged');
});

test('ES34-05 no false churn: constant inputs for 300 s at 1x; 120x constant still reports rate-throughput, not churn',async()=>{
 const live=await run({rate:1,weather:constant,workerMs:800,wallMs:300000});
 assert.ok(!live.avail.some(a=>a.reason==='target-churn'));assert.ok(live.accepted>0);
 const fast=await run({rate:120,weather:constant,workerMs:1200,wallMs:20000});
 assert.ok(fast.avail.some(a=>a.reason==='rate-throughput'));assert.ok(!fast.avail.some(a=>a.reason==='target-churn'));
 // Forecast lerp under 120x: churn may coexist, but an active rate-throughput report is never overwritten by churn.
 let state={...scene(120,constant()),utcMs:BASE},mono=0;const jobs=[];
 const lc=new NativeSkyLifecycle({capture:()=>state,now:()=>mono,execute:job=>new Promise(resolve=>jobs.push(resolve))});
 lc.request();mono+=1000;state={...state,utcMs:state.utcMs+120000};jobs[0]({status:'ready',raster:{}});for(let i=0;i<10;i++)await Promise.resolve();
 assert.equal(lc.availability.reason,'rate-throughput');
 for(const job of [{native:{sceneIdentity:state.sceneIdentity,identity:'moved-1'}},{native:{sceneIdentity:state.sceneIdentity,identity:'moved-2'}}])lc.dropped(job,'superseded');
 assert.equal(lc.availability.reason,'rate-throughput','churn does not overwrite rate-throughput');lc.dispose();
});

test('ES34-05 guards: another scene, a paused owner or a disposed lifecycle never report churn',async()=>{
 let state={...scene(2,constant())},mono=0;
 const lc=new NativeSkyLifecycle({capture:()=>state,now:()=>mono,execute:()=>new Promise(()=>{})});
 lc.observe();
 const foreign={native:{sceneIdentity:'another-scene',identity:'x'}};
 lc.dropped(foreign,'rejected');lc.dropped(foreign,'rejected');lc.dropped(foreign,'rejected');
 assert.notEqual(lc.availability.reason,'target-churn','late results of another sceneIdentity');
 const own={native:{sceneIdentity:state.sceneIdentity,identity:'moved'}};
 state={...state,paused:true};lc.observe();lc.dropped(own,'superseded');lc.dropped(own,'superseded');
 assert.notEqual(lc.availability.reason,'target-churn','paused owner');
 state={...state,paused:false};lc.observe();lc.dropped(own,'superseded');lc.dropped(own,'superseded');
 assert.equal(lc.availability.reason,'target-churn','positive control');
 state={...state,sceneIdentity:'B',generation:2};lc.observe();
 assert.equal(lc.availability.status,'pending','a sceneIdentity change clears it');assert.equal(lc.state.churn.drops,0);
 lc.dispose();lc.dropped({native:{sceneIdentity:'B',identity:'m'}},'rejected');lc.dropped({native:{sceneIdentity:'B',identity:'m'}},'rejected');
 assert.equal(lc.availability.reason,'disposed','disposed lifecycle');
});
