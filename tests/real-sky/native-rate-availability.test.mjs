import test from 'node:test';
import assert from 'node:assert/strict';
import {NativeSkyLifecycle} from '../../real-sky/native-lifecycle.mjs';

const base={utcMs:Date.parse('2026-09-07T20:30Z'),lat:24.47,lon:39.61,heightM:0,generation:1,sceneIdentity:'A',timeScale:10,weather:null,lp:0,reducedMotion:true,paused:false,camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0}};
const settle=async()=>{for(let i=0;i<10;i++)await Promise.resolve();};
function fixture(rate=10){
 let state={...base,timeScale:rate},mono=0;const jobs=[],painted=[],availability=[];
 const c=new NativeSkyLifecycle({capture:()=>state,now:()=>mono,execute:job=>new Promise(resolve=>jobs.push({job,resolve})),onResult:r=>painted.push(r),onAvailability:a=>availability.push(a)});
 return {c,jobs,painted,availability,get state(){return state;},set:p=>{state={...state,...p};},advance:wall=>{mono+=wall;state={...state,utcMs:state.utcMs+wall*state.timeScale};},finish:async()=>{jobs.at(-1).resolve({status:'ready',raster:{}});await settle();}};
}
test('10x cadence refreshes before the accepted frame exhausts its thirty-second age budget',async()=>{
 const h=fixture();h.c.request();h.advance(200);await h.finish();h.advance(1300);h.c.request();
 assert.equal(h.jobs.length,2);h.c.dispose();
});
test('a completed frame outside the rate envelope reports finite unavailability and never publishes',async()=>{
 const h=fixture(600);h.c.request();h.advance(70);await h.finish();
 assert.equal(h.painted.length,0);assert.equal(h.c.state.availability.status,'unavailable');
 assert.equal(h.c.state.availability.reason,'rate-throughput');assert.equal(h.c.state.availability.rate,600);
 assert.equal(h.availability.at(-1).status,'unavailable');h.c.dispose();
});
test('expiration of the displayed frame does not invalidate a newer current refresh',async()=>{
 const h=fixture(10);h.c.request();await h.finish();const first=h.jobs[0].job;
 h.advance(2000);h.c.request();h.advance(1100);
 assert.equal(h.c.current(first),false);await h.finish();
 assert.equal(h.painted.length,2);assert.equal(h.c.state.availability.status,'available');h.c.dispose();
});
test('repeated force notifications coalesce identical in-flight UTC instead of starving completion',async()=>{
 const h=fixture(0);h.c.request();for(let i=0;i<12;i++)h.c.request(true);
 await h.finish();assert.equal(h.painted.length,1);assert.equal(h.jobs.length,1);h.c.dispose();
});
test('an unsupported moving rate recovers at frozen time with fresh identity and no stale error',async()=>{
 const h=fixture(600);h.c.request();h.advance(100);await h.finish();
 h.set({timeScale:0});h.c.request(true);await h.finish();
 assert.equal(h.painted.length,1);assert.equal(h.c.state.availability.status,'available');h.c.dispose();
});
test('A to B to A during a rate change admits only the new generation',async()=>{
 const h=fixture(60);h.c.request();h.set({generation:2,sceneIdentity:'B'});h.c.request(true);
 h.set({generation:3,sceneIdentity:'A',timeScale:0});h.c.request(true);
 h.jobs[0].resolve({status:'ready',raster:{}});await settle();assert.equal(h.painted.length,0);
 await h.finish();assert.equal(h.painted.length,1);assert.equal(h.jobs.at(-1).job.native.generation,3);h.c.dispose();
});
test('a backward seek without generation change clears rate diagnostics and fences completion',async()=>{
 const h=fixture(600);h.c.request();h.advance(100);await h.finish();
 h.c.request(true);h.set({utcMs:base.utcMs-120000,timeScale:0});h.c.request(true);
 h.jobs[1].resolve({status:'ready',raster:{}});await settle();assert.equal(h.painted.length,0);
 await h.finish();assert.equal(h.painted.length,1);assert.equal(h.c.state.availability.status,'available');h.c.dispose();
});

test('source reload during acceleration disposes the old queue before successor acceptance',async()=>{
 const old=fixture(60);old.c.request();old.advance(700);old.c.dispose();
 const next=fixture(60);next.c.request();next.advance(100);await next.finish();
 await old.finish();
 assert.equal(old.painted.length,0);assert.equal(old.c.state.disposed,true);
 assert.equal(next.painted.length,1);assert.equal(next.c.state.availability.status,'available');
 next.c.dispose();
});
