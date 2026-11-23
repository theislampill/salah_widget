'use strict';
// R0038 (issue 105) follow-up to finding F-12 / ISM-MOON-010 (test-only).
// MoonEngine.render accepts a sparse lighting refinement (`lightingMask`) only for the
// physical scene whose full lighting it last ACCEPTED; that acceptance is `this.lightKey`.
// A render that is cancelled or fails after it started must withdraw the acceptance
// (`catch(error){this.lightKey=null;throw error;}`), because its lighting rows are partly
// rewritten. Removing that reset survived the whole registered Moon suite. This instrument
// observes the reset only through behaviour: after an interrupted render the same sparse
// refinement that was accepted a moment earlier is refused, and a full render re-admits it.
//
// Subjects, both read from the tree and never re-implemented:
//   * the worker source the shipped entry installs: the string literal passed to
//     `installWorkerSource(...)` in index.html, required to equal moon/moon-worker.js and the
//     literal in moon/moon-host.js (the bytes a browser runs);
//   * the authored units in moon/src (the build input, as moon/tests builds them).
// The real WASM kernel and the real terrain and colour assets are used. Mutants edit the
// shipped worker text in memory only and must fail the same discriminator.
// Call/state behaviour only: no pixels are judged, no browser, no Worker, no network.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..'),moon=path.join(root,'moon');
const manifest=JSON.parse(fs.readFileSync(path.join(moon,'asset-manifest.json'),'utf8'));
const bytes=n=>new Uint8Array(fs.readFileSync(path.join(moon,n)));
const RESET='catch(error){this.lightKey=null;throw error;}',KEPT='catch(error){throw error;}';
const REFUSED=/Sparse source refinement requires the same admitted physical scene/;
const INSTALL='window.SalahMoonRuntime?.installWorkerSource(',GLUE='\n// moon-worker.mjs\n';
// The JSON string literal the generated file passes to installWorkerSource (one line).
function installed(rel){
 const text=fs.readFileSync(path.join(root,rel),'utf8');assert.equal(text.split(INSTALL).length,2,rel+' installs the worker source exactly once');
 const at=text.indexOf(INSTALL)+INSTALL.length,line=text.slice(at,text.indexOf('\n',at)),end=line.lastIndexOf('");');
 assert.ok(end>0,rel+' install call is one complete statement');return JSON.parse(line.slice(0,end+1));
}
function shippedWorker(){
 const source=installed('index.html');
 assert.equal(source,fs.readFileSync(path.join(moon,'moon-worker.js'),'utf8'),'index.html installs exactly moon/moon-worker.js');
 assert.equal(source,installed('moon/moon-host.js'),'moon/moon-host.js installs the same worker source');
 return source;
}
// Everything before the worker message glue: manifest, kernel constant and the engine units.
function shippedApi(edit){
 let text=shippedWorker();assert.equal(text.split(GLUE).length,2,'the worker glue unit starts exactly once');text=text.slice(0,text.indexOf(GLUE));
 if(edit){const [from,to]=edit;assert.equal(text.split(from).length,2,'the mutated statement exists exactly once in the shipped worker');text=text.replace(from,to);}
 return new Function(text+'\nreturn {MoonEngine,canonicalScene};')();
}
function authoredApi(){
 const units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs'];
 return new Function(units.map(n=>fs.readFileSync(path.join(moon,'src',n),'utf8')).join('\n')+'\nreturn {MoonEngine,canonicalScene};')();
}
const create=api=>api.MoonEngine.create({wasm:bytes('moon_kernel.wasm'),dem:bytes(manifest.assets.dem.path),colour:bytes(manifest.assets.colour.path),manifest});
const OPTIONS={radial:2,azimuth:8},SIZE=32;
const same=(a,b)=>Buffer.compare(Buffer.from(a.buffer,a.byteOffset,a.byteLength),Buffer.from(b.buffer,b.byteOffset,b.byteLength))===0;
// Interrupts on the nth cancellation poll; `calls` proves lighting rows ran before it.
function interruptAt(n,raise){const probe={calls:0,cancelled(){probe.calls++;if(probe.calls<n)return false;if(raise)throw raise;return true;}};return probe;}
// Discriminator shared by both real subjects and by the mutant.
async function interruptedLightingIsNotReused(api){
 const e=await create(api),scene=api.canonicalScene({fraction:.5,size:SIZE,outSize:64,diameter:61.44}),other=api.canonicalScene({fraction:.3,size:SIZE,outSize:64,diameter:61.44});
 const mask=new Uint8Array(SIZE*SIZE).fill(1),sparse=()=>e.render(scene,{...OPTIONS,lightingMask:mask});
 const baseline=await e.render(scene,OPTIONS);
 // Positive controls: an accepted scene admits the sparse refinement, and the admission is
 // keyed to the scene (so a later refusal is the key at work, not a mask the engine dislikes).
 const refined=await sparse();assert.equal(refined.width,64,'sparse refinement of the accepted scene is admitted');
 await assert.rejects(e.render(other,{...OPTIONS,lightingMask:mask}),REFUSED,'a different physical scene is refused');
 await sparse();
 // 1. Cancellation part-way through the lighting rows (the camera pass is reused, so every
 //    poll before the interruption is a lighting row that was recomputed).
 const cancel=interruptAt(SIZE/2);
 await assert.rejects(e.render(scene,{...OPTIONS,cancelled:cancel.cancelled}),x=>x.name==='AbortError');
 assert.equal(cancel.calls,SIZE/2,'the render was interrupted after lighting rows had been rewritten');assert.equal(e.active,false);
 await assert.rejects(sparse(),REFUSED,'cancelled lighting is not reused as accepted illumination');
 // Recovery: a completed full render re-admits the scene, with the original result.
 const again=await e.render(scene,OPTIONS);assert.ok(same(again.rgba,baseline.rgba),'a full render after the cancellation reproduces the baseline');
 await sparse();
 // 2. A failure that is not a cancellation, raised at the same point.
 const failure=interruptAt(SIZE/2,new Error('injected lighting failure'));
 await assert.rejects(e.render(scene,{...OPTIONS,cancelled:failure.cancelled}),/injected lighting failure/);
 assert.equal(failure.calls,SIZE/2);assert.equal(e.active,false);
 await assert.rejects(sparse(),REFUSED,'failed lighting is not reused as accepted illumination');
 await e.render(scene,OPTIONS);await sparse();
 // 3. An interrupted SPARSE pass withdraws the acceptance as well.
 const late=interruptAt(SIZE/2);
 await assert.rejects(e.render(scene,{...OPTIONS,lightingMask:mask,cancelled:late.cancelled}),x=>x.name==='AbortError');
 await assert.rejects(sparse(),REFUSED,'an interrupted sparse pass is not refined further');
 const last=await e.render(scene,OPTIONS);assert.ok(same(last.rgba,baseline.rgba));
}
test('ISM-MOON-010 F-12: cancelled or failed lighting is not reused; a full render re-admits it (worker source installed by index.html)',async()=>interruptedLightingIsNotReused(shippedApi()));
test('ISM-MOON-010 F-12: cancelled or failed lighting is not reused; a full render re-admits it (authored moon/src units)',async()=>interruptedLightingIsNotReused(authoredApi()));
test('ISM-MOON-010 F-12 mutant: removing the lightKey reset from the engine catch fails the discriminator',async()=>{
 const api=shippedApi([RESET,KEPT]); // built outside the rejects: a drifted site text fails this case
 await assert.rejects(()=>interruptedLightingIsNotReused(api),e=>e instanceof assert.AssertionError&&/cancelled lighting is not reused as accepted illumination/.test(e.message));
});
test('ISM-MOON-010 F-12: the statement the mutant removes is the one in the authored engine and in the shipped worker',()=>{
 const authored=fs.readFileSync(path.join(moon,'src','moon-engine.mjs'),'utf8'),shipped=shippedWorker();
 assert.equal(authored.split(RESET).length,2);assert.equal(shipped.split(RESET).length,2);
 assert.ok(shipped.includes(authored.replace(/\r\n/g,'\n').trimEnd()),'the shipped worker carries the authored engine unit verbatim');
});
