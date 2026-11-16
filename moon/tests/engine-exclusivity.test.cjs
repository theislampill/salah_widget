'use strict';
// R0038 / ISM-MOON-010: one active computation per MoonEngine. The guard
// (`if(this.active)throw ...`) and its release (`finally{this.active=false;}`)
// were the only parts of the machine's invariant with no test. Each mutant below
// edits the shipped moon-engine.mjs text in memory (never on disk) and must fail
// the same discriminator the unmutated engine passes.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..'),units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs','moon-precision.mjs'];
const manifest=JSON.parse(fs.readFileSync(path.join(root,'asset-manifest.json'),'utf8'));
const bytes=n=>new Uint8Array(fs.readFileSync(path.join(root,n)));
const GUARD="if(this.active)throw new Error('One owned Moon computation at a time');";
const RELEASE='finally{this.active=false;}';
function build(mutate){
 let text=units.map(n=>fs.readFileSync(path.join(root,'src',n),'utf8')).join('\n');
 if(mutate){const [from,to]=mutate;assert.equal(text.split(from).length,2,'the mutated statement exists exactly once in the shipped source');text=text.replace(from,to);}
 return Function(text+'\nreturn {MoonEngine,canonicalScene};')();
}
const create=api=>api.MoonEngine.create({wasm:bytes('moon_kernel.wasm'),dem:bytes(manifest.assets.dem.path),colour:bytes(manifest.assets.colour.path),manifest});
const OPTIONS={radial:2,azimuth:8};
const same=(a,b)=>Buffer.compare(Buffer.from(a.buffer,a.byteOffset,a.byteLength),Buffer.from(b.buffer,b.byteOffset,b.byteLength))===0;
// Discriminator shared by the real engine and both mutants.
async function exclusivity(api){
 const e=await create(api),scene=api.canonicalScene({fraction:.5,size:32,outSize:64,diameter:61.44});
 const baseline=await e.render(scene,OPTIONS);
 assert.equal(e.active,false,'a settled render releases the engine');
 const first=e.render(scene,OPTIONS),second=e.render(scene,OPTIONS);
 // Attach the rejection handler in the same turn: the engine is mid-computation here.
 const rejected=assert.rejects(second,/One owned Moon computation at a time/);
 await rejected;
 const firstResult=await first;
 assert.ok(same(firstResult.rgba,baseline.rgba),'the refused second call did not disturb the first result');
 const third=await e.render(scene,OPTIONS);
 assert.ok(same(third.rgba,baseline.rgba),'a render after settlement succeeds with the same result');
 await assert.rejects(e.render(scene,{...OPTIONS,cancelled:()=>true}),x=>x.name==='AbortError');
 assert.equal(e.active,false,'a cancelled render releases the engine');
 const after=await e.render(scene,OPTIONS);
 assert.ok(same(after.rgba,baseline.rgba),'a render after a cancellation succeeds');
}
test('ISM-MOON-010: a second concurrent render is refused, the first completes intact, and the engine is released after success and cancellation',async()=>exclusivity(build()));
test('ISM-MOON-010 mutant: removing the reentry guard fails the discriminator',async()=>{
 const api=build([GUARD,'']); // built outside the rejects: a drifted site text fails this case
 await assert.rejects(()=>exclusivity(api),e=>e instanceof assert.AssertionError);
});
test('ISM-MOON-010 mutant: removing the release in finally fails the discriminator',async()=>{
 const api=build([RELEASE,'']);
 await assert.rejects(()=>exclusivity(api),e=>e instanceof assert.AssertionError||/One owned Moon computation/.test(String(e.message)));
});
