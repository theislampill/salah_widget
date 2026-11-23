'use strict';
// R0038 (issue 105) follow-up to finding F-1 / ISM-SKY-010 (test-only).
// ReferenceRenderClient.dispose() must settle a render that is already in flight on the
// worker: the pending promise rejects with `Render client disposed`. The census mutant W4
// (the rejecting loop removed from dispose) survived every registered test, because the
// existing cases only submit after disposal. This instrument holds a request in flight on a
// controllable worker, disposes, and requires the rejection.
//
// Subjects, all read from the tree and never re-implemented:
//   * the class text inside the shipped bundle real-sky/native-sky.js (what the page runs);
//   * the module real-sky/core/src/reference-worker-client.mjs (generated copy; what
//     real-sky/native-host.mjs imports and what the Node suites import);
//   * the upstream build input in the vendor tree (read only).
// Timers are the node:test mock, so the client's own deadlines neither fire by themselves nor
// keep the process alive; a control case shows the mock does drive the client's deadline.
// Mutants edit the bundle's class text in memory only and must fail the same discriminator.
// Call/state behaviour only: no browser, no real Worker, no network.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
const root=path.join(__dirname,'..');
const TIMEOUT=60000,DISPOSED='Render client disposed';
const LOOP="for(const p of this.#pending.values()){clearTimeout(p.timer);p.reject(new Error('Render client disposed'));}";
const REJECT="p.reject(new Error('Render client disposed'));";
function bundleClass(edit){
 const text=fs.readFileSync(path.join(root,'real-sky/native-sky.js'),'utf8'),head='class ReferenceRenderClient{';
 assert.equal(text.split(head).length,2,'the shipped bundle defines the client exactly once');
 const start=text.indexOf(head),end=text.indexOf('\n// ',start);assert.ok(end>start,'the next bundled unit follows the client');
 let source=text.slice(start,end);
 if(edit){const [from,to]=edit;assert.equal(source.split(from).length,2,'the mutated statement exists exactly once in the shipped class');source=source.replace(from,to);}
 return new Function('"use strict";'+source+'\nreturn ReferenceRenderClient;')();
}
const moduleClass=async rel=>(await import(pathToFileURL(path.join(root,rel)).href)).ReferenceRenderClient;
const settle=async(n=8)=>{for(let i=0;i<n;i++)await new Promise(setImmediate);};
// Boots on request; a render is recorded and answered only when the test says so.
class HeldWorker{
 constructor(){this.renders=[];this.terminated=0;}
 postMessage(m){if(m.kind==='boot')queueMicrotask(()=>this.onmessage({data:{kind:'ready'}}));else if(m.kind==='render')this.renders.push(m);}
 answer(m){this.onmessage({data:{kind:'result',id:m.id,result:{value:m.job.n}}});}
 terminate(){this.terminated++;}
}
async function inFlight(C){
 const w=new HeldWorker(),fallback={built:0,renders:0,disposed:0};
 const c=new C({},{workerFactory:()=>w,timeoutMs:TIMEOUT,fallbackFactory:()=>{fallback.built++;return {render:async job=>{fallback.renders++;return {value:job.n};},dispose(){fallback.disposed++;}};}});
 let outcome=null;c.run({n:41}).then(value=>{outcome={value};},error=>{outcome={error};});
 await settle();
 // Precondition: the request really is in flight on the worker and unsettled.
 assert.equal(c.mode,'worker','the client booted its worker');
 assert.equal(w.renders.length,1,'exactly one render reached the worker');
 assert.equal(outcome,null,'the render is unsettled while the worker holds it');
 return {c,w,fallback,outcome:()=>outcome};
}
// Discriminator shared by the three real subjects and by both mutants.
async function disposeRejectsInFlight(C,t){
 t.mock.timers.enable({apis:['setTimeout']});
 const {c,w,fallback,outcome}=await inFlight(C);
 c.dispose();
 await settle();
 const o=outcome();
 assert.ok(o,'dispose settles the in-flight render (it is not left pending)');
 assert.ok(o.error instanceof Error,'the in-flight render rejects; it does not resolve');
 assert.equal(o.error.message,DISPOSED);
 assert.notEqual(o.error.code,'WORKER_UNAVAILABLE','a disposal is not reported as a worker failure');
 assert.equal(c.mode,'disposed');assert.equal(w.terminated,1,'the worker is terminated once');
 assert.equal(fallback.built,0,'the disposed job is not retried on a main-thread fallback');
 // Nothing later revives it: a late worker answer, the elapsed deadline, a second dispose.
 assert.doesNotThrow(()=>w.answer(w.renders[0]));
 t.mock.timers.tick(TIMEOUT+1);await settle();c.dispose();
 assert.equal(outcome(),o,'the settled outcome is final');assert.equal(c.mode,'disposed');
 assert.equal(fallback.built,0);assert.equal(w.terminated,1);assert.deepEqual(c.warnings,[],'no worker failure was recorded');
 await assert.rejects(c.run({n:42}),new RegExp(DISPOSED));assert.equal(w.renders.length,1,'no render is posted after disposal');
}
const SUBJECTS=[
 ['shipped bundle real-sky/native-sky.js',async()=>bundleClass()],
 ['module real-sky/core/src/reference-worker-client.mjs',()=>moduleClass('real-sky/core/src/reference-worker-client.mjs')],
 ['build input vendor/real-sky/src/reference-worker-client.mjs',()=>moduleClass('vendor/real-sky/src/reference-worker-client.mjs')],
];
for(const [name,get] of SUBJECTS){
 test(`ISM-SKY-010 F-1: dispose rejects a render in flight on the worker (${name})`,async t=>disposeRejectsInFlight(await get(),t));
 // Positive controls: the same held request is a real, answerable request, and the mocked
 // deadline is the client's own. Without them the rejection could come from a broken rig.
 test(`ISM-SKY-010 F-1 control: the same held render resolves when the worker answers (${name})`,async t=>{
  t.mock.timers.enable({apis:['setTimeout']});
  const {c,w,fallback,outcome}=await inFlight(await get());
  w.answer(w.renders[0]);await settle();
  assert.equal(outcome().value.value,41);assert.equal(outcome().value.execution.mode,'worker');assert.equal(fallback.built,0);
  c.dispose();await settle();assert.equal(outcome().value.value,41,'a later dispose does not disturb a delivered result');
 });
 test(`ISM-SKY-010 F-1 control: without dispose the held render ends by the worker deadline, not by a disposal (${name})`,async t=>{
  t.mock.timers.enable({apis:['setTimeout']});
  const {c,w,fallback,outcome}=await inFlight(await get());
  t.mock.timers.tick(TIMEOUT-1);await settle();assert.equal(outcome(),null,'still in flight just before the deadline');
  t.mock.timers.tick(1);await settle();t.mock.timers.tick(1);await settle();
  assert.equal(outcome().value.execution.mode,'main-thread-fallback');assert.equal(outcome().value.value,41);
  assert.match(c.warnings.join(' '),/Worker render timeout/);assert.equal(fallback.renders,1);assert.equal(w.terminated,1);
  c.dispose();assert.equal(fallback.disposed,1);
 });
}
test('ISM-SKY-010 F-1 mutant W4: removing the rejecting loop from dispose fails the discriminator',async t=>{
 const C=bundleClass([LOOP,'']); // built outside the rejects: a drifted site text fails this case
 await assert.rejects(()=>disposeRejectsInFlight(C,t),e=>e instanceof assert.AssertionError&&/dispose settles the in-flight render/.test(e.message));
});
test('ISM-SKY-010 F-1 mutant: keeping the loop but not rejecting fails the discriminator',async t=>{
 const C=bundleClass([REJECT,'']);
 await assert.rejects(()=>disposeRejectsInFlight(C,t),e=>e instanceof assert.AssertionError&&/dispose settles the in-flight render/.test(e.message));
});
test('ISM-SKY-010 F-1: the three copies under test carry the same client class text',()=>{
 const read=rel=>fs.readFileSync(path.join(root,rel),'utf8').replace(/\r\n/g,'\n'),cut=s=>s.slice(s.indexOf('class ReferenceRenderClient{')).trimEnd();
 const core=read('real-sky/core/src/reference-worker-client.mjs'),vendor=read('vendor/real-sky/src/reference-worker-client.mjs'),bundle=read('real-sky/native-sky.js');
 assert.equal(core,vendor,'the generated core copy equals the build input');
 assert.ok(cut(core).startsWith('class ReferenceRenderClient{')&&bundle.includes(cut(core)),'the bundle carries that class text verbatim');
 assert.equal(cut(core).split(LOOP).length,2,'the statement the mutants remove is the shipped one');
});
