'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.join(__dirname,'..'),units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs','moon-pool.mjs'];
const api=Function(units.map(n=>fs.readFileSync(path.join(root,'src',n),'utf8')).join('\n')+'\nreturn {MoonEngine,MoonPool,canonicalScene,nativeCalendarResult,bridge:typeof moonRowBridge === "function"?moonRowBridge:null};')();
const manifest=JSON.parse(fs.readFileSync(path.join(root,'asset-manifest.json'),'utf8'));
const bytes=n=>new Uint8Array(fs.readFileSync(path.join(root,n)));
async function engine(){return api.MoonEngine.create({wasm:bytes('moon_kernel.wasm'),dem:bytes(manifest.assets.dem.path),colour:bytes(manifest.assets.colour.path),manifest});}
function local(e){return {async render(scene,options){const r=await e.render(scene,{...options,qualityFields:true,diagnostic:'fields'}),N=scene.size,pix=new Float64Array(e.e.memory.buffer,e.e.get_pixels(),N*N*24);r.material=new Float32Array(N*N*3);for(let i=0;i<N*N;i++)for(let k=0;k<3;k++)r.material[3*i+k]=pix[24*i+6+k];return r;},cancel(){}};}
test('row-parallel assembly exactly preserves single-worker numerical fields, global filtering and quality signals',async()=>{
 const reference=await engine();
 for(const count of [2,4]){
 const pool=new api.MoonPool(await Promise.all(Array.from({length:count},async()=>local(await engine()))));
 for(const fraction of [.01,.08,.3,.4509,.5,.92,.98])for(const waxing of [false,true]){
  // Odd size makes the internal boundary cut through the displayed footprint.
  const s=api.canonicalScene({fraction,waxing,size:25,outSize:32,diameter:30.72});
  for(const [radial,azimuth] of [[2,8],[4,16]]){
   const options={radial,azimuth,qualityFields:true,diagnostic:'fields'};
   const a=await reference.render(s,options),b=await pool.render(s,options);
   for(const name of ['solar','earth','coverage','receiverCodes','ambiguous','surfaceLinear','surfaceCoverage','rgba','qualityImages'])assert.deepEqual(b[name],a[name],name+' / '+fraction+' / '+waxing);
   assert.equal(b.physicalIdentity,a.physicalIdentity);assert.equal(b.profileIdentity,a.profileIdentity);
   assert.deepEqual(api.nativeCalendarResult(pool,b),api.nativeCalendarResult(reference,a),'calendar material must join both owned halves');
   for(const field of ['analyticSamples','shadowRays','blockerWitnesses','knownSurfaceSamples','unresolvedShading','unresolvedContour'])assert.equal(b.diagnostics[field],a.diagnostics[field],field);
  }
 }}
});
test('first terrain pass computes only its owned rows without changing the owned numerical result',async()=>{
 const reference=await engine(),owned=await engine(),s=api.canonicalScene({fraction:.01,waxing:true,size:25,outSize:32,diameter:30.72});
 const calls={camera:[],lighting:[]},original=owned.e;
 owned.e={...original,camera_rows(first,count){calls.camera.push([first,count]);return original.camera_rows(first,count);},light_rows(first,count,...rest){calls.lighting.push([first,count]);return original.light_rows(first,count,...rest);}};
 const options={radial:4,azimuth:16,qualityFields:true,diagnostic:'fields'};
 const full=await reference.render(s,options),part=await owned.render(s,{...options,rowOwner:[0,12]});
 assert.equal(calls.camera.reduce((n,[,count])=>n+count,0),12,'duplicate camera work delays first publication');
 assert.equal(calls.lighting.reduce((n,[,count])=>n+count,0),12,'duplicate initial lighting delays first publication');
 assert.ok([...calls.camera,...calls.lighting].every(([first,count])=>first>=0&&first+count<=12));
 for(const [name,stride] of [['solar',3],['earth',3],['coverage',1],['surfaceLinear',3],['surfaceCoverage',1]]){
  assert.deepEqual(part[name].slice(0,12*25*stride),full[name].slice(0,12*25*stride),name);
  assert.ok(part[name].slice(12*25*stride).every(v=>v===0),'unowned '+name+' must not enter publication');
 }
 // A new owner cannot reuse an incomplete camera or sparse-light cache.
 const mask=new Uint8Array(625).fill(3);
 await assert.rejects(owned.render(s,{...options,rowOwner:[12,25],lightingMask:mask}),/Sparse/);
 const moved=await owned.render(s,{...options,rowOwner:[12,25]});
 for(const [name,stride] of [['solar',3],['earth',3],['coverage',1],['surfaceLinear',3]]){
  assert.deepEqual(moved[name].slice(12*25*stride),full[name].slice(12*25*stride),name+' after ownership change');
  assert.ok(moved[name].slice(0,12*25*stride).every(v=>v===0),'previously owned '+name+' must be zero');
 }
});
test('interrupted real camera and lighting work cannot contaminate resumed or reassigned rows',async()=>{
 const reference=await engine(),s=api.canonicalScene({fraction:.3,waxing:true,size:25,outSize:32,diameter:30.72}),options={radial:2,azimuth:8,qualityFields:true,diagnostic:'fields'};
 const expected=await reference.render(s,options);
 for(const stage of ['camera_rows','light_rows']){
  const e=await engine(),original=e.e;let stopped=false,armed=true,calls=0;
  e.e={...original,[stage](...args){const result=original[stage](...args);calls++;if(armed)stopped=true;return result;}};
  await assert.rejects(e.render(s,{...options,rowOwner:[0,12],cancelled:()=>stopped}),x=>x.name==='AbortError');
  assert.ok(calls>0,'cancellation must follow actual kernel work');armed=false;stopped=false;
  for(const rowOwner of [[0,12],[12,25]]){
   const result=await e.render(s,{...options,rowOwner});
   for(const [name,stride] of [['solar',3],['earth',3],['coverage',1],['surfaceLinear',3]]){
    const [lo,hi]=rowOwner.map(x=>x*25*stride);
    assert.deepEqual(result[name].slice(lo,hi),expected[name].slice(lo,hi),stage+' '+name);
    assert.ok(result[name].slice(0,lo).every(x=>x===0)&&result[name].slice(hi).every(x=>x===0));
   }
  }
 }
});
test('row ownership rejects invalid bounds before touching the real kernel',async()=>{
 const e=await engine(),s=api.canonicalScene({fraction:.5,size:8,outSize:8,diameter:7.68});
 for(const rowOwner of [[-1,4],[0,9],[4,4],[5,4],[0,4.5],[0],[],Array(2),[,4],[0,],{},'0,4'])await assert.rejects(e.render(s,{rowOwner}),/row owner/);
});
test('row-parallel work rejects a late result after cancellation',async()=>{
 let release;const wait=new Promise(r=>release=r),scene=api.canonicalScene({fraction:.5,size:8,outSize:8,diameter:7.68});
 const pool=new api.MoonPool([{render:()=>wait,cancel(){}},{render:()=>wait,cancel(){}}]);let cancelled=false;
 const result=pool.render(scene,{cancelled:()=>cancelled});cancelled=true;pool.cancel();release(null);
 await assert.rejects(result,e=>e.name==='AbortError');
});
test('sparse refinement preserves unselected receivers and global projection across all row boundaries',async()=>{
 const reference=await engine(),pool=new api.MoonPool(await Promise.all(Array.from({length:4},async()=>local(await engine()))));
 const s=api.canonicalScene({fraction:.4509,waxing:true,size:25,outSize:32,diameter:30.72});
 await reference.render(s,{radial:2,azimuth:8});await pool.render(s,{radial:2,azimuth:8});
 const mask=new Uint8Array(625);for(let i=0;i<mask.length;i++)mask[i]=i%5===0?3:i%7===0?1:i%11===0?2:0;
 const opts={radial:4,azimuth:16,lightingMask:mask,qualityFields:true,diagnostic:'fields'};
 const a=await reference.render(s,opts),b=await pool.render(s,opts);
 assert.deepEqual(b.diagnostics.rowScheduling.ranges,[[0,6],[6,12],[12,18],[18,25]]);
 for(const field of ['solar','earth','coverage','receiverCodes','ambiguous','surfaceLinear','surfaceCoverage','rgba','qualityImages'])assert.deepEqual(b[field],a[field],field);
});
test('a fourth missing, foreign or corrupted row cannot be published',async()=>{
 const e=await engine(),s=api.canonicalScene({fraction:.3,size:25,outSize:32,diameter:30.72}),valid=[];
 for(const rowOwner of [[0,6],[6,12],[12,18],[18,25]])valid.push(await local(e).render(s,{radial:2,azimuth:8,rowOwner}));
 const from=parts=>new api.MoonPool(parts.map(p=>({render:async()=>structuredClone(p),cancel(){}})));
 assert.ok((await from(valid).render(s)).rgba.some(x=>x>0));
 for(const corrupt of [parts=>parts[3]=null,parts=>parts[3].diagnostics.rowOwner=[12,18],parts=>parts[3].material[18*25*3]=NaN]){
  const parts=structuredClone(valid);corrupt(parts);await assert.rejects(from(parts).render(s),/Moon row (identity mismatch|material shape\/value)/);
 }
});
test('row owner rejects same-identity but wrong-scene, malformed and nonfinite fields',async()=>{
 const s=api.canonicalScene({fraction:.5,size:8,outSize:8,diameter:7.68}),e=await engine();
 const valid=await Promise.all([[0,4],[4,8]].map(async rowOwner=>local(await engine()).render(s,{radial:2,azimuth:8,rowOwner})));
 const from=parts=>new api.MoonPool(parts.map(p=>({render:async()=>structuredClone(p),cancel(){}})));
 assert.deepEqual((await from(valid).render(s)).rgba,(await e.render(s,{radial:2,azimuth:8})).rgba,'positive owned pair reaches actual global presentation');
 const corruptions=[
  [x=>x.scene.fraction=.6,/Moon row identity mismatch/],
  [x=>x.diagnostics.rowOwner=[0,4],/Moon row identity mismatch/],
  [x=>x.surfaceLinear=new Float32Array(4),/Moon row field shape: surfaceLinear/],
  [x=>x.earth[3]=NaN,/Moon row field value: earth/],
  [x=>x.coverage[4]=1.1,/Moon row field value: coverage/],
  [x=>delete x.material,/Moon row material shape\/value/],
  [x=>x.material=new Float32Array(4),/Moon row material shape\/value/],
  [x=>x.material[4*8*3]=NaN,/Moon row material shape\/value/],
  [x=>x.material[4*8*3]=1.1,/Moon row material shape\/value/]
 ];
 for(const [corrupt,guard] of corruptions){
  const parts=structuredClone(valid);corrupt(parts[1]);
  await assert.rejects(from(parts).render(s),guard);
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
test('four-owner failure cancels all siblings and partial boot disposes every worker',async()=>{
 const cancelled=new Set(),waiters=[];
 const pool=new api.MoonPool(Array.from({length:4},(_,i)=>i===0?{render:async()=>{throw Error('row failed');},cancel(){cancelled.add(i);}}:{render:()=>new Promise((_,reject)=>waiters[i]=reject),cancel(){cancelled.add(i);waiters[i]?.(new DOMException('cancelled','AbortError'));}}));
 await assert.rejects(pool.render(api.canonicalScene({fraction:.3,size:8,outSize:8,diameter:7.68})),/row failed/);
 assert.deepEqual([...cancelled].sort(),[0,1,2,3]);
 const original=global.Worker,workers=[];
 global.Worker=class{
  constructor(){this.index=workers.length;workers.push(this);}
  postMessage(m){queueMicrotask(()=>this.onmessage({data:this.index===2?{kind:'shard-error',id:m.id,error:'boot failed'}:{kind:'shard-ready',id:m.id,result:true}}));}
  terminate(){this.terminated=true;}
 };
 try{await assert.rejects(api.MoonPool.create({},'/* worker source */'),/boot failed/);assert.equal(workers.length,4);assert.ok(workers.every(w=>w.terminated));}
 finally{global.Worker=original;}
});
test('row workers get a locally owned Blob instead of reusing an opaque parent URL',async()=>{
 const priorWorker=global.Worker,priorSelf=global.self,urls=[];global.self={location:{href:'blob:null/document-owned'}};
 global.Worker=class{
  constructor(url){assert.notEqual(url,global.self.location.href,'opaque ancestor URL is inaccessible from a file worker');urls.push(url);}
  postMessage(m){if(m.kind==='shard-boot')queueMicrotask(()=>this.onmessage({data:{kind:'shard-ready',id:m.id,result:true}}));}
  terminate(){}
 };
 try{const pool=await api.MoonPool.create({},'/* same authored worker source */');assert.equal(urls.length,4);assert.ok(urls.every(x=>x.startsWith('blob:')));for(const w of pool.workers)w.dispose();}
 finally{global.Worker=priorWorker;global.self=priorSelf;}
});
