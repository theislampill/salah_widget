'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..'),units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs','moon-pool.mjs'];
const api=Function(units.map(n=>fs.readFileSync(path.join(root,'src',n),'utf8')).join('\n')+'\nreturn {MoonEngine,MoonPool,canonicalScene,bridge:typeof moonRowBridge === "function"?moonRowBridge:null};')();
const manifest=JSON.parse(fs.readFileSync(path.join(root,'asset-manifest.json'),'utf8'));
const bytes=n=>new Uint8Array(fs.readFileSync(path.join(root,n)));
async function engine(){return api.MoonEngine.create({wasm:bytes('moon_kernel.wasm'),dem:bytes(manifest.assets.dem.path),colour:bytes(manifest.assets.colour.path),manifest});}
function local(e){return {async render(scene,options){const r=await e.render(scene,{...options,qualityFields:true,diagnostic:'fields'}),N=scene.size,pix=new Float64Array(e.e.memory.buffer,e.e.get_pixels(),N*N*24);r.material=new Float32Array(N*N*3);for(let i=0;i<N*N;i++)for(let k=0;k<3;k++)r.material[3*i+k]=pix[24*i+6+k];return r;},cancel(){}};}
test('row-parallel assembly exactly preserves single-worker numerical fields, global filtering and quality signals',async()=>{
 const reference=await engine(),pool=new api.MoonPool([local(await engine()),local(await engine())]);
 for(const fraction of [.08,.4509,.5,.92,.98])for(const waxing of [false,true]){
  // Odd size makes the internal boundary cut through the displayed footprint.
  const s=api.canonicalScene({fraction,waxing,size:25,outSize:32,diameter:30.72});
  for(const [radial,azimuth] of [[2,8],[4,16]]){
   const options={radial,azimuth,qualityFields:true,diagnostic:'fields'};
   const a=await reference.render(s,options),b=await pool.render(s,options);
   for(const name of ['solar','earth','coverage','receiverCodes','ambiguous','surfaceLinear','surfaceCoverage','rgba','qualityImages'])assert.deepEqual(b[name],a[name],name+' / '+fraction+' / '+waxing);
   assert.equal(b.physicalIdentity,a.physicalIdentity);assert.equal(b.profileIdentity,a.profileIdentity);
  }
 }
});
test('row-parallel work rejects a late result after cancellation',async()=>{
 let release;const wait=new Promise(r=>release=r),scene=api.canonicalScene({fraction:.5,size:8,outSize:8,diameter:7.68});
 const pool=new api.MoonPool([{render:()=>wait,cancel(){}},{render:()=>wait,cancel(){}}]);let cancelled=false;
 const result=pool.render(scene,{cancelled:()=>cancelled});cancelled=true;pool.cancel();release(null);
 await assert.rejects(result,e=>e.name==='AbortError');
});
test('sparse refinement preserves unselected receivers and global projection across the row boundary',async()=>{
 const reference=await engine(),pool=new api.MoonPool([local(await engine()),local(await engine())]);
 const s=api.canonicalScene({fraction:.4509,waxing:true,size:25,outSize:32,diameter:30.72});
 await reference.render(s,{radial:2,azimuth:8});await pool.render(s,{radial:2,azimuth:8});
 const mask=new Uint8Array(625);for(let i=0;i<mask.length;i++)mask[i]=i%5===0?3:i%7===0?1:i%11===0?2:0;
 const opts={radial:4,azimuth:16,lightingMask:mask,qualityFields:true,diagnostic:'fields'};
 const a=await reference.render(s,opts),b=await pool.render(s,opts);
 for(const field of ['solar','earth','coverage','receiverCodes','ambiguous','surfaceLinear','surfaceCoverage','rgba','qualityImages'])assert.deepEqual(b[field],a[field],field);
});
test('row owner rejects same-identity but wrong-scene, malformed and nonfinite fields',async()=>{
 const s=api.canonicalScene({fraction:.5,size:8,outSize:8,diameter:7.68}),e=await engine();
 const valid=await local(e).render(s,{radial:2,azimuth:8});
 for(const corrupt of [x=>x.scene.fraction=.6,x=>x.surfaceLinear=new Float32Array(4),x=>x.earth[3]=NaN,x=>x.coverage[4]=1.1]){
  const b=structuredClone(valid);corrupt(b);
  const pool=new api.MoonPool([{render:async()=>structuredClone(valid),cancel(){}},{render:async()=>b,cancel(){}}]);
  await assert.rejects(pool.render(s));
 }
});
test('an idle row-worker failure is terminal and cannot leave a later request waiting forever',async()=>{
 assert.equal(typeof api.bridge,'function');let terminated=false;
 const worker={postMessage(){},terminate(){terminated=true;}};
 const bridge=api.bridge(worker);worker.onerror({message:'controlled idle failure'});
 await assert.rejects(bridge.render({},{}),/controlled idle failure/);
 bridge.dispose();assert.equal(terminated,true);
});
test('a failed row cancels its sibling before waiting for the joined result',async()=>{
 let release,cancelled=false;const wait=new Promise((_,reject)=>release=reject);
 const pool=new api.MoonPool([{render:async()=>{throw new Error('controlled row failure');},cancel(){}},{render:()=>wait,cancel(){cancelled=true;release(new DOMException('cancelled','AbortError'));}}]);
 const task=pool.render(api.canonicalScene({fraction:.5,size:8,outSize:8,diameter:7.68}));
 const result=await Promise.race([task.then(()=>null,e=>e),new Promise(r=>setTimeout(()=>r('hung'),150))]);
 if(result==='hung')release(new Error('test cleanup'));
 assert.equal(cancelled,true);assert.match(result.message,/controlled row failure/);
});
