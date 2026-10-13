'use strict';
// Controlled non-terrain source contracts. No browser, native acquisition, real
// asset decode, performance measurement, or renewed scientific qualification.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const candidate=path.resolve(__dirname,'../src');
const base=process.env.SALAH_MOON_BASE_SOURCE?path.resolve(process.env.SALAH_MOON_BASE_SOURCE):candidate;
const independentBase=base!==candidate;
const units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs','moon-pool.mjs'];
function api(variant='candidate',worker=false){
 const messages=[],self={postMessage(m){messages.push(m);},addEventListener(){}};
 const source=units.map(n=>fs.readFileSync(variant==='candidate'&&['moon-engine.mjs','surface_v5.mjs'].includes(n)?path.join(candidate,n):path.join(base,n),'utf8')).join('\n');
 const counters='const profileWork={calls:0},originalProfile=admitProfile;admitProfile=(...a)=>{profileWork.calls++;return originalProfile(...a);};const outputWork={display:0,quality:0};const originalDisplay=renderSurfaceFrame,originalQuality=projectSurfaceCodes;renderSurfaceFrame=(...a)=>{outputWork.display++;return originalDisplay(...a);};projectSurfaceCodes=(...a)=>{outputWork.quality++;return originalQuality(...a);};';
 const workerSource=worker?fs.readFileSync(path.join(variant==='candidate'?candidate:base,'moon-worker.mjs'),'utf8'):'';
 return {...Function('performance','MessageChannel','self',source+'\n'+counters+'\n'+workerSource+'\nreturn {MoonEngine,MoonPool,canonicalScene,outputWork,profileWork,mapSurfaceRgb,preparedMapper:typeof createSurfaceRgbMapper==="function"?createSurfaceRgbMapper:null,profile:MOON_PROFILE,bridge:moonRowBridge,dispatch:self.onmessage};')({now:()=>0},undefined,self),messages};
}
function engine(a){
 const memory={buffer:new ArrayBuffer(262144)},pixPointer=4096,counterPointer=256,maskPointer=1024,trace=[];
 let size=0,radial=0,azimuth=0;
 const counters=()=>new Float64Array(memory.buffer,counterPointer,8);
 function camera(first,count){
  trace.push(['camera',first,count]);const pix=new Float64Array(memory.buffer,pixPointer,size*size*24);
  for(let y=first;y<first+count;y++)for(let x=0;x<size;x++){
   const p=(y*size+x)*24;pix[p+6]=.15+.02*y;pix[p+7]=.12+.01*x;pix[p+8]=.09+.005*(x+y);
   pix[p+17]=(x===0||y===0||x===size-1||y===size-1)?.5:1;pix[p+18]=1;pix[p+14]=1;pix[p+16]=.1;
  }
 }
 function lighting(first,count,mask){
  trace.push([mask?'sparse':'lighting',first,count,radial,azimuth]);const pix=new Float64Array(memory.buffer,pixPointer,size*size*24);
  for(let y=first;y<first+count;y++)for(let x=0;x<size;x++){
   const i=y*size+x,p=i*24,select=mask?new Uint8Array(memory.buffer,maskPointer,size*size)[i]:3;
   if(select&1)pix[p+12]=.1+.007*y+.001*radial;if(select&2)pix[p+13]=.005+.001*x+.00001*azimuth;
   pix[p+20]=x%3===0?2:1;pix[p+21]=y%4===0?2:1;
  }
 }
 const e={memory,begin_scene(N,_p,_sun,_earth,_d,_extent,_a,_b,_c,_gain,_angle,r,z){size=N;radial=r;azimuth=z;trace.push(['begin',N,r,z]);return 1;},
  set_lights(_sun,_earth,r,z){radial=r;azimuth=z;trace.push(['lights',r,z]);return 1;},
  camera_rows:camera,light_rows(first,count){lighting(first,count,false);},light_rows_selected(first,count){lighting(first,count,true);},
  get_pixels:()=>pixPointer,get_counters:()=>counterPointer,material_gain:()=>1};
 const result=new a.MoonEngine();Object.assign(result,{e,p:0,maskPointer,cameraKey:null,lightKey:null,manifestIdentity:'CONTROLLED_NON_TERRAIN_MANIFEST',active:false});
 result.trace=trace;result.counters=counters;return result;
}
const scene=a=>a.canonicalScene({fraction:.4509,waxing:true,size:9,outSize:12,diameter:10.24});
const opts={radial:2,azimuth:32,qualityFields:true,diagnostic:'fields'};
function stable(value){
 if(ArrayBuffer.isView(value))return {type:value.constructor.name,bytes:Buffer.from(value.buffer,value.byteOffset,value.byteLength).toString('hex')};
 if(Array.isArray(value))return value.map(stable);
 if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,stable(v)]));
 return value;
}
test('default and explicit false preserve the accepted complete result and kernel calls',async()=>{
 const old=api('base'),next=api(),a=engine(old),b=engine(next),s=scene(old);
 const x=await a.render(s,opts),y=await b.render(s,{...opts,fieldsOnly:false});
 assert.deepEqual(stable(y),stable(x));assert.deepEqual(b.trace,a.trace);
 assert.deepEqual(next.outputWork,{display:1,quality:2});
});
test('standalone omitted options and full diagnostics retain their original output contracts',async()=>{
 for(const options of [{},{diagnostic:true},{qualityFields:true},{analytic:false,diagnostic:'fields'}]){
  const old=api('base'),next=api(),a=engine(old),b=engine(next),s=scene(old);
  const x=await a.render(s,options),y=await b.render(s,options);
  assert.deepEqual(stable(y),stable(x));assert.deepEqual(b.trace,a.trace);
  assert.ok(y.rgba instanceof Uint8ClampedArray);assert.equal(y.rgba.length,12*12*4);
  if(options.diagnostic===true)assert.ok(y.pixels instanceof Float64Array);
 }
});
test('fields-only preserves all retained data and initialization while avoiding discarded output work',async()=>{
 const old=api('base'),next=api(),a=engine(old),b=engine(next),s=scene(old);
 const x=await a.render(s,opts),y=await b.render(s,{...opts,fieldsOnly:true});
 for(const k of ['rgba','qualityImages','displayLinear']){assert.equal(Object.hasOwn(y,k),false,k);delete x[k];}
 assert.deepEqual(stable(y),stable(x));assert.deepEqual(b.trace,a.trace);
 assert.equal(b.trace.filter(x=>x[0]==='lighting').length,9,'initial full64 rule must initialize every row');
 assert.equal(b.trace.some(x=>x[0]==='sparse'),false,'cold physical key must not use sparse initialization');
 assert.deepEqual(next.outputWork,{display:0,quality:0});
});
test('internal option rejects wrong type or non-shard contracts before physical work',async()=>{
 const a=api(),e=engine(a),s=scene(a);
 for(const options of [{fieldsOnly:1},{fieldsOnly:true},{fieldsOnly:true,qualityFields:true,diagnostic:true}])
  await assert.rejects(e.render(s,options),/fields-only|Fields-only/);
 assert.equal(e.trace.length,0);assert.equal(e.active,false);
});
function row(e,fieldsOnly){return {
 async render(scene,options){
  const r=await e.render(scene,{...options,qualityFields:true,diagnostic:'fields',fieldsOnly}),N=scene.size;
  const pix=new Float64Array(e.e.memory.buffer,e.e.get_pixels(),N*N*24);r.material=new Float32Array(N*N*3);
  let ownedShadowed=0;for(let i=0;i<N*N;i++){for(let k=0;k<3;k++)r.material[3*i+k]=pix[24*i+6+k];
   if(options.rowOwner&&i>=options.rowOwner[0]*N&&i<options.rowOwner[1]*N&&pix[24*i+14]>1e-8&&pix[24*i+12]<pix[24*i+14]*.01)ownedShadowed++;
  }
  if(options.rowOwner)r.diagnostics.ownedShadowedFacingSamples=ownedShadowed;
  delete r.rgba;delete r.qualityImages;delete r.displayLinear;return r;
 },cancel(){}};}
test('whole joined global output and shifted quality projections keep exact seam pixels',async()=>{
 const old=api('base'),next=api(),oa=[engine(old),engine(old)],na=[engine(next),engine(next)],s=scene(old);
 const before=new old.MoonPool(oa.map(e=>row(e,false))),after=new next.MoonPool(na.map(e=>row(e,true)));
 const a=await before.render(s,opts),b=await after.render(s,opts);
 assert.deepEqual(stable(b),stable(a));assert.deepEqual(next.outputWork,{display:1,quality:2},'one global display/quality pass remains');
 assert.deepEqual(old.outputWork,{display:3,quality:6},'old discarded shard work reproduced');
 for(let i=0;i<2;i++){
  assert.deepEqual(na[i].trace,oa[i].trace);
  assert.equal(na[i].trace.filter(t=>t[0]==='lighting').length,9,'each initial row owner keeps a FULL64 cache');
 }
 const mask=new Uint8Array(81);for(let i=0;i<mask.length;i++)mask[i]=i%5===0?3:i%7===0?1:i%11===0?2:0;
 const options={...opts,radial:4,azimuth:64,lightingMask:mask};
 const refinedA=await before.render(s,options),refinedB=await after.render(s,options);
 assert.deepEqual(stable(refinedB),stable(refinedA));
 for(let i=0;i<2;i++)assert.deepEqual(na[i].trace,oa[i].trace,'same camera/cache/selected-light calls');
 assert.equal(refinedB.diagnostics.rowScheduling.initialCacheRule,false);
});
test('physical key cannot admit sparse cold or changed-scene data in fields-only mode',async()=>{
 const a=api(),e=engine(a),s=scene(a),mask=new Uint8Array(81).fill(3);
 await assert.rejects(e.render(s,{...opts,fieldsOnly:true,lightingMask:mask}),/same admitted physical scene/);
 assert.equal(e.trace.length,0);
 await e.render(s,{...opts,fieldsOnly:true});
 const changed=a.canonicalScene({fraction:.92,waxing:true,size:9,outSize:12,diameter:10.24});
 await assert.rejects(e.render(changed,{...opts,fieldsOnly:true,lightingMask:mask}),/same admitted physical scene/);
});
test('cancelled physical work and malformed contour/coverage/light never get a fields result',async()=>{
 for(const fieldsOnly of [false,true])for(const fault of ['cancel','contour','coverage','light']){
  const a=api(),e=engine(a),s=scene(a);
  if(fault==='contour')e.counters()[7]=1;
  if(fault==='coverage'){
   const original=e.e.camera_rows;e.e.camera_rows=(...v)=>{original(...v);new Float64Array(e.e.memory.buffer,e.e.get_pixels(),81*24)[17]=2;};
  }
  if(fault==='light'){
   const original=e.e.light_rows;e.e.light_rows=(...v)=>{original(...v);new Float64Array(e.e.memory.buffer,e.e.get_pixels(),81*24)[12]=NaN;};
  }
  await assert.rejects(e.render(s,{...opts,fieldsOnly,cancelled:()=>fault==='cancel'&&e.trace.filter(t=>t[0]==='lighting').length>=3}));
  assert.equal(e.active,false);assert.equal(e.lightKey,null);
 }
});
test('global row validation rejects nonfinite or malformed dormant fields and stale identity',async()=>{
 const a=api(),s=scene(a),v=await row(engine(a),true).render(s,opts);
 for(const corrupt of [r=>r.physicalIdentity='stale',r=>r.scene.fraction=.92,r=>r.surfaceLinear=new Float32Array(4),
                      r=>r.earth[3]=NaN,r=>r.coverage[4]=1.1,r=>r.solar[r.solar.length-1]=NaN]){
  const bad=structuredClone(v);corrupt(bad);
  const p=new a.MoonPool([{render:async()=>structuredClone(v),cancel(){}},{render:async()=>bad,cancel(){}}]);
  await assert.rejects(p.render(s,opts));
 }
});
test('pool cancellation rejects a late fields-only reply',async()=>{
 const a=api(),s=scene(a);let release;const wait=new Promise(r=>release=r);
 const p=new a.MoonPool([{render:()=>wait,cancel(){}},{render:()=>wait,cancel(){}}]);
 const result=p.render(s,opts);p.cancel();release(null);await assert.rejects(result,e=>e.name==='AbortError');
});
test('one failed shard cancels its sibling and an idle worker failure stays terminal',async()=>{
 const a=api(),s=scene(a);let rejectWait,cancelled=false;const wait=new Promise((_,reject)=>rejectWait=reject);
 const p=new a.MoonPool([{render:async()=>{throw new Error('controlled shard failure');},cancel(){}},
  {render:()=>wait,cancel(){cancelled=true;rejectWait(new DOMException('revoked sibling','AbortError'));}}]);
 await assert.rejects(p.render(s,opts),/controlled shard failure/);assert.equal(cancelled,true);assert.equal(p.lightKey,null);
 let terminated=false;const worker={postMessage(){},terminate(){terminated=true;}};
 const bridge=a.bridge(worker);worker.onerror({message:'controlled idle worker failure'});
 await assert.rejects(bridge.render({},{}),/controlled idle worker failure/);bridge.dispose();assert.equal(terminated,true);
});
test('actual shard message selects fields-only and retains exactly the old transport payload',async()=>{
 async function actual(variant){
  const a=api(variant,true),e=engine(a),s=scene(a);a.MoonEngine.create=async()=>e;
  a.dispatch({data:{kind:'shard-boot',id:1,assets:{}}});
  for(let n=0;n<20&&!a.messages.some(m=>m.kind==='shard-ready');n++)await new Promise(r=>setImmediate(r));
  assert.ok(a.messages.some(m=>m.kind==='shard-ready'));
  a.dispatch({data:{kind:'shard-render',id:2,scene:s,options:{...opts,rowOwner:[0,4],fieldsOnly:false}}});
  for(let n=0;n<30&&!a.messages.some(m=>m.kind==='shard-result'||m.kind==='shard-error');n++)await new Promise(r=>setImmediate(r));
  const reply=a.messages.find(m=>m.kind==='shard-result');assert.ok(reply,JSON.stringify(a.messages));
  return {reply,calls:a.outputWork,trace:e.trace};
 }
 let old;if(independentBase)old=await actual('base');else{
  const a=api('base'),e=engine(a),result=await row(e,false).render(scene(a),{...opts,rowOwner:[0,4]});
  old={reply:{kind:'shard-result',id:2,result},calls:a.outputWork,trace:e.trace};
 }
 const next=await actual('candidate');
 assert.deepEqual(stable(next.reply),stable(old.reply));assert.deepEqual(next.trace,old.trace);
 assert.deepEqual(next.calls,{display:0,quality:0});
 // An independent baseline now denotes accepted fields-only850425. The portable
 // old-row witness still constructs discarded standalone products explicitly.
 assert.deepEqual(old.calls,independentBase?{display:0,quality:0}:{display:1,quality:2});
});
test('actual shard route rejects cancelled and malformed-owner replies without publication',async()=>{
 for(const fault of ['cancel','owner']){
  const a=api('candidate',true),e=engine(a),s=scene(a);a.MoonEngine.create=async()=>e;
  a.dispatch({data:{kind:'shard-boot',id:1,assets:{}}});
  for(let n=0;n<20&&!a.messages.some(m=>m.kind==='shard-ready');n++)await new Promise(r=>setImmediate(r));
  a.dispatch({data:{kind:'shard-render',id:2,scene:s,options:{...opts,rowOwner:fault==='owner'?[0,10]:[0,4]}}});
  if(fault==='cancel')a.dispatch({data:{kind:'shard-cancel'}});
  for(let n=0;n<30&&!a.messages.some(m=>m.kind==='shard-error');n++)await new Promise(r=>setImmediate(r));
  assert.equal(a.messages.some(m=>m.kind==='shard-result'),false);
  const error=a.messages.find(m=>m.kind==='shard-error');assert.ok(error);
  if(fault==='cancel')assert.equal(error.name,'AbortError');else assert.match(error.error,/row range/);
 }
});

// Mutation discriminator: restoring profile admission in the receiver loop
// restores N*N admissions. Full physical calls/fields remain covered above.
test('quality-field mapping admits one stable profile per render instead of per receiver',async()=>{
 for(const fieldsOnly of [true,false]){
  const a=api(),e=engine(a);await e.render(scene(a),{...opts,fieldsOnly});
  assert.equal(a.profileWork.calls,fieldsOnly?3:4,'scene + fingerprint + prepared mapper (+ standalone display), independent of receiver count');
  assert.equal(e.trace.filter(x=>x[0]==='lighting').length,9,'original full receiver initialization retained');
 }
});
test('prepared mapping preserves exact accepted V5 values across calendar and reference profiles',()=>{
 const old=api('base'),next=api();assert.equal(typeof next.preparedMapper,'function');
 const profiles=[old.profile,{...old.profile,profile_id:'unboosted-v5-01',mode:'reference',lift:0},
  {...old.profile,profile_id:'controlled-rgb',exposure:1.75,lift:.002,knee:.000013}];
 const inputs=[[[0,0,0],[0,0,0]],[[1e-18,2e-8,.006],[.009,0,1e-8]],[[1,0,0],[0,.25,.5]],[[1e308,0,0],[0,0,0]]];
 let seed=12345;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
 for(let i=0;i<128;i++)inputs.push([Array.from({length:3},()=>10**(-14+random()*16)),Array.from({length:3},()=>10**(-14+random()*16))]);
 for(const p of profiles){const mapped=next.preparedMapper(p);for(const [solar,earth]of inputs)
  assert.deepEqual(mapped(solar,earth),old.mapSurfaceRgb(solar,earth,p));}
 assert.deepEqual(next.preparedMapper(old.profile)([0,0,0],[0,0,0]),[0,0,0]);
});
test('prepared mapper keeps original profile and per-RGB rejection boundaries',()=>{
 const old=api('base'),next=api();assert.equal(typeof next.preparedMapper,'function');
 const badProfiles=[null,{...old.profile,extra:true},{...old.profile,exposure:0},{...old.profile,knee:NaN},{...old.profile,mode:'reference',lift:.003}];
 const failure=f=>{try{f();assert.fail('accepted malformed input');}catch(e){return [e.constructor.name,e.message];}};
 for(const p of badProfiles)assert.deepEqual(failure(()=>next.preparedMapper(p)),failure(()=>old.mapSurfaceRgb([0,0,0],[0,0,0],p)));
 const mapped=next.preparedMapper(old.profile);
 for(const [solar,earth]of [[null,[0,0,0]],[[1,2],[0,0,0]],[[NaN,0,0],[0,0,0]],[[0,0,0],[-1,0,0]],[[Infinity,0,0],[0,0,0]],[[1e308,0,0],[1e308,0,0]]])
  assert.deepEqual(failure(()=>mapped(solar,earth)),failure(()=>old.mapSurfaceRgb(solar,earth,old.profile)));
});
test('prepared profile is private to the admitted render and cannot follow later caller mutation',()=>{
 const old=api('base'),next=api(),p={...old.profile},before={...p};assert.equal(typeof next.preparedMapper,'function');
 const mapped=next.preparedMapper(p),solar=[.03,.01,.02],earth=[.001,.002,.001];p.exposure=10;p.profile_id='caller-changed';
 assert.deepEqual(mapped(solar,earth),old.mapSurfaceRgb(solar,earth,before));
 assert.notDeepEqual(mapped(solar,earth),old.mapSurfaceRgb(solar,earth,p));
});
