'use strict';
// R0038 / ISM-MOON-007: the Moon worker's newest-job pump (moon/src/moon-worker.mjs).
// The raw authored fragment is evaluated in a vm realm whose globals (MoonPool,
// adaptiveRender, nativeCalendarResult, the asset manifest) are controllable stubs;
// `self` records every postMessage. Each job's adaptiveRender call is held on a gate
// the test settles, so replacement, cancellation and arrival during execution are
// ordered exactly. Invariants asserted:
//   * at most one top-level pipeline runs (a job sent while another executes waits);
//   * a result, preview or error is published only while its serial is current;
//   * a job that arrives during execution is served after the running one settles;
//   * cancel drops a queued job and silences the running one;
//   * jobs sent before the engine is ready collapse to the newest.
// Mutants edit the shipped text in memory only. Reported outside the suite: removing
// only the `finally` re-pump is an equivalent mutant (see docs/state-contracts/R0038.md).
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const SOURCE=fs.readFileSync(path.join(process.env.SALAH_MOON_SOURCE_DIR||path.join(__dirname,'../src'),'moon-worker.mjs'),'utf8');
const M={
 postToken:['if(token!==serial)return;',''],
 errorToken:["if(token===serial)self.postMessage({kind:'error'","self.postMessage({kind:'error'"],
 runningGuard:['if(running||!latest||!enginePromise)return;running=true;','if(!latest||!enginePromise)return;running=true;'],
 consume:['const job=latest;latest=null;const token=serial;','const job=latest;const token=serial;'],
 cancelDrop:["else if(m.kind==='cancel'){serial++;latest=null;","else if(m.kind==='cancel'){serial++;"],
 drain:['while(latest){','if(latest){'],
 repump:['finally{running=false;if(latest)pump();}','finally{running=false;}'],
};
function mutate(text,[from,to]){assert.equal(text.split(from).length,2,'mutated statement exists exactly once: '+from);return text.replace(from,to);}
const tick=async(n=12)=>{for(let i=0;i<n;i++)await new Promise(setImmediate);};
function rig(edit=s=>s){
 const posted=[],calls=[],cancels=[];
 const self={postMessage(m){posted.push(m);},addEventListener(){}};
 const engine={cancel(){cancels.push(1);}};
 const buf=()=>({buffer:new ArrayBuffer(4)});
 const bundle=()=>({rgba:buf(),surfaceLinear:buf(),surfaceCoverage:buf()});
 const c=vm.createContext({self,URL,Uint8Array,Promise,Map,DOMException,atob,Error,String,
  MOON_ASSET_MANIFEST:{assets:{dem:{path:'dem',bytes:0},colour:{path:'colour',bytes:0}}},MOON_WASM_BASE64:'',
  MoonPool:{create:async()=>engine},
  nativeCalendarResult:()=>({calendarLinear:buf(),calendarRgba:buf()}),
  adaptiveRender:(eng,scene,opts)=>new Promise((resolve,reject)=>{calls.push({scene,opts,resolve:()=>resolve(bundle()),reject,preview:()=>opts.onPreview(bundle())});})});
 vm.runInContext(edit(SOURCE),c);
 const send=m=>self.onmessage({data:m});
 const job=(id)=>({kind:'render',id,identity:{key:'k'+id},scene:{n:id}});
 const boot=async()=>{send({kind:'boot',offline:false,embedded:{dem:'',colour:''},workerSource:'x'});await tick();};
 const published=kind=>posted.filter(m=>m.kind===kind).map(m=>m.id);
 return{posted,calls,cancels,send,job,boot,published};
}
async function newestOnly(edit){
 const r=rig(edit);await r.boot();
 assert.deepEqual(r.posted.map(m=>m.kind),['ready']);
 r.send(r.job(1));await tick();assert.equal(r.calls.length,1,'job 1 started');
 assert.equal(r.calls[0].opts.cancelled(),false);
 r.send(r.job(2));await tick();
 assert.equal(r.calls.length,1,'at most one pipeline: job 2 waits for job 1 to settle');
 assert.equal(r.calls[0].opts.cancelled(),true,'replacement cancels the running job');
 assert.ok(r.cancels.length>=2,'engine.cancel is requested on each render message');
 r.calls[0].preview();await tick();
 assert.deepEqual(r.published('preview'),[],'a stale preview is suppressed');
 r.calls[0].resolve();await tick();
 assert.deepEqual(r.published('result'),[],'a stale result is suppressed');
 assert.equal(r.calls.length,2,'a job that arrived during execution is served (no lost wake-up)');
 assert.equal(r.calls[1].scene.n,2);assert.equal(r.calls[1].opts.cancelled(),false);
 r.calls[1].preview();await tick();r.calls[1].resolve();await tick();
 assert.deepEqual(r.published('preview'),[2]);assert.deepEqual(r.published('result'),[2]);
 assert.equal(r.calls.length,2,'the consumed job is not executed again');
 const done=r.posted.find(m=>m.kind==='result');assert.deepEqual(done.identity,{key:'k2'});
 r.send(r.job(3));await tick();assert.equal(r.calls.length,3,'the pump is reusable after it returns to idle');
}
async function cancellation(edit){
 const r=rig(edit);await r.boot();
 r.send(r.job(10));await tick();r.send(r.job(11));await tick();
 r.send({kind:'cancel'});await tick();
 r.calls[0].resolve();await tick();
 assert.equal(r.calls.length,1,'cancel drops the queued job');
 assert.deepEqual(r.published('result'),[],'a cancelled serial publishes nothing');
 r.send(r.job(12));await tick();assert.equal(r.calls.length,2);
 r.send({kind:'cancel'});await tick();
 r.calls[1].reject(new Error('cancelled run failing late'));await tick();
 assert.deepEqual(r.published('error'),[],'a cancelled job that fails reports nothing');
 r.send(r.job(13));await tick();assert.equal(r.calls.length,3);
 r.calls[2].reject(new Error('current failure'));await tick();
 assert.deepEqual(r.published('error'),[13]);assert.match(r.posted.find(m=>m.kind==='error').error,/current failure/);
 r.send(r.job(14));await tick();assert.equal(r.calls.length,4,'an error does not wedge the pump');
 r.calls[3].resolve();await tick();assert.deepEqual(r.published('result'),[14]);
}
async function beforeReady(edit){
 const r=rig(edit);
 r.send(r.job(1));r.send(r.job(2));await tick();
 assert.equal(r.calls.length,0,'nothing runs before the engine exists');
 await r.boot();
 assert.equal(r.calls.length,1,'only the newest pre-boot job runs');assert.equal(r.calls[0].scene.n,2);
 r.calls[0].resolve();await tick();assert.deepEqual(r.published('result'),[2]);
}
test('ISM-MOON-007: newest-only pump suppresses stale preview/result and serves a job that arrives during execution',()=>newestOnly());
test('ISM-MOON-007: cancel drops the queued job and silences the running one; a current error is reported and does not wedge the pump',()=>cancellation());
test('ISM-MOON-007: jobs sent before the engine is ready collapse to the newest',()=>beforeReady());
const mutants=[
 ['drops the publication serial check',s=>mutate(s,M.postToken),newestOnly],
 ['drops the error serial check',s=>mutate(s,M.errorToken),cancellation],
 ['drops the running guard',s=>mutate(s,M.runningGuard),newestOnly],
 ['does not consume the latest job',s=>mutate(s,M.consume),newestOnly],
 ['keeps the queued job on cancel',s=>mutate(s,M.cancelDrop),cancellation],
 ['removes the drain loop and the finally re-pump together',s=>mutate(mutate(s,M.drain),M.repump),newestOnly],
];
for(const [name,edit,scenario] of mutants)test('ISM-MOON-007 mutant: '+name+' fails the discriminator',async()=>{
 await assert.rejects(()=>scenario(edit),e=>e instanceof assert.AssertionError);
});
