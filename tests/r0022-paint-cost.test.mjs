import assert from 'node:assert/strict';
import test from 'node:test';
import {collectCostScope,collectR0022PaintCost,nativePaintCostAdapters,admissionCostAdapter} from './r0022-paint-cost.mjs';

// Synthetic clock/callbacks test custody and ordering. No wall-clock benchmark,
// browser, physical solver, native CPU or pixel qualification runs here.
function setup(failAt=Infinity){
 let clock=0,calls=0;const saved=[],counter={pendingJobs:0,rafChains:1};
 const adapter={snapshot:()=>({...counter}),run(){calls++;clock++;if(calls===failAt)throw new Error('original failure');}};
 return {A:adapter,B:adapter,adapterSha256:'a'.repeat(64),name:'admission',
  now:()=>clock,pulse:async()=>{clock+=1000;},persist:async record=>saved.push(record),saved};
}
test('retains four exact ABBA blocks and raw call durations',async()=>{
 const options=setup(),result=await collectCostScope(options);
 assert.equal(result.status,'RAW_BATCHES_RETURNED');
 assert.deepEqual(result.slots.map(s=>s.side),[...'ABBA'.repeat(4)]);
 assert.ok(Object.values(result.warmMs).every(ms=>ms>=5000));
 assert.ok(result.slots.every(s=>s.elapsedMs>=5000&&s.durationsMs.every(v=>v===1)&&s.exceptions.length===0));
 assert.equal(options.saved.at(-1).status,'RAW_BATCHES_RETURNED');
});
test('original callback failure retains the affected partial slot and stops',async()=>{
 const options=setup(11),result=await collectCostScope(options);
 assert.equal(result.status,'INCOMPLETE');assert.equal(result.slots.length,1);
 assert.ok(result.slots[0].exceptions[0].includes('original failure'));
 assert.equal(result.slots[0].durationsMs.length,1);
 assert.equal(options.saved.at(-1).status,'INCOMPLETE');
});
test('missing state remains visible instead of a zero-valued substitute',async()=>{
 const options=setup();options.A.snapshot=()=>{throw new Error('inventory absent');};
 const result=await collectCostScope(options);assert.equal(result.status,'INCOMPLETE');
 assert.equal(result.slots[0].startState,null);assert.equal(result.slots[0].endState,null);
 assert.equal(result.slots[0].exceptions.length,2);
});
test('raw custody sink failure prevents a returned complete batch',async()=>{
 const options=setup();let writes=0;options.persist=async()=>{if(++writes===2)throw new Error('custody sink failed');};
 const result=await collectCostScope(options);assert.equal(result.status,'INCOMPLETE');
 assert.ok(result.error.includes('custody sink failed'));assert.equal(result.slots.length,1);
});
test('native adapter retains the actual function references and argument owners',()=>{
 const seen=[],functions={renderMoon:()=>seen.push('geometry'),model:()=>({native:true}),
  atmosphere:m=>{assert.ok(m.native);seen.push('atmosphere');return {actual:true};},
  paint:a=>{assert.ok(a.actual);seen.push('paint');}};
 const adapters=nativePaintCostAdapters({eval:n=>functions[n]},()=>({actualInventory:true}));
 adapters.paint.prepare();adapters.paint.run();assert.deepEqual(seen,['geometry','atmosphere','paint']);
 assert.throws(()=>nativePaintCostAdapters({eval:()=>undefined},()=>({})),/unavailable/);
});
test('admission adapter invokes the actual closure with independent raw copies',()=>{
 const rawResult={raster:{linear:new Float64Array([1,2,3])}},request={id:7,observer:{utcMs:123}};let captured;
 const state={status:'ready',renders:1,presentationDraws:1,rejections:0,presentationRejections:0,presentationUtcMs:123};
 const adapter=admissionCostAdapter({accept:(r,id,q)=>{captured={r,id,q};r.raster.linear[0]=99;state.renders++;state.presentationDraws++;},rawResult,request,snapshot:()=>({}),readState:()=>({...state}),current:()=>true});
 adapter.prepare();adapter.run();adapter.verify();assert.equal(captured.id,7);assert.equal(captured.q,request);
 assert.equal(rawResult.raster.linear[0],1);
 adapter.prepare();adapter.run();adapter.verify();assert.equal(rawResult.raster.linear[0],1);
 assert.throws(()=>admissionCostAdapter({accept:()=>{},snapshot:()=>({})}),/raw admission/);
});
test('silent stale/malformed/presentation rejection cannot produce cheap accepted samples',()=>{
 const input={accept:()=>{},rawResult:{raster:{}},request:{observer:{utcMs:123}},
  snapshot:()=>({}),readState:()=>({status:'ready',renders:1,rejections:0,presentationRejections:0,presentationUtcMs:123}),current:()=>false};
 const stale=admissionCostAdapter(input);assert.throws(()=>stale.prepare(),/currentness fence/);
 const silent=admissionCostAdapter({...input,current:()=>true});silent.prepare();silent.run();
 assert.throws(()=>silent.verify(),/did not complete/);
});
test('accepted render without a real presentation draw cannot earn cheap admission time',()=>{
 const state={status:'ready',renders:1,presentationDraws:1,rejections:0,presentationRejections:0,presentationUtcMs:123};
 const adapter=admissionCostAdapter({accept:()=>{state.renders++;},rawResult:{raster:{}},request:{observer:{utcMs:123}},snapshot:()=>({}),readState:()=>({...state}),current:()=>true});
 adapter.prepare();adapter.run();assert.throws(()=>adapter.verify(),/did not complete/);
});
test('native batch API refuses a nonbrowser caller before acquisition',async()=>{
 await assert.rejects(collectR0022PaintCost({}),/Actual browser fixture/);
});
test('aborted synthetic browser shell preserves its partial scope and stops',async()=>{
 const priorWindow=globalThis.window,priorRAF=globalThis.requestAnimationFrame;
 globalThis.window={};globalThis.requestAnimationFrame=()=>{throw new Error('No browser/frames run in this control');};
 try{
  const controller=new AbortController();controller.abort();const saved=[];
  const scopes=['atmosphere','paint','renderMoon','admission'].map(name=>({
   name,adapterSha256:'a'.repeat(64),A:{run:()=>{},snapshot:()=>({})},B:{run:()=>{},snapshot:()=>({})}}));
  const raw=await collectR0022PaintCost({binding:{changedScopes:['admission']},scopes,
   signal:controller.signal,persist:async r=>saved.push(r)});
  assert.equal(raw.status,'INCOMPLETE');assert.equal(raw.scopes.length,1);
  assert.equal(raw.scopes[0].status,'INCOMPLETE');assert.ok(raw.scopes[0].error.includes('interrupted'));
  assert.equal(saved.at(-1).status,'INCOMPLETE');
 }finally{
  if(priorWindow===undefined)delete globalThis.window;else globalThis.window=priorWindow;
  if(priorRAF===undefined)delete globalThis.requestAnimationFrame;else globalThis.requestAnimationFrame=priorRAF;
 }
});
