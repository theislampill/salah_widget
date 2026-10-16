'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-initial.mjs'];
const api=Function(units.map(n=>fs.readFileSync(path.join(root,'src',n),'utf8')).join('\n')+'\nreturn {createInitialMoon,canonicalScene,mapInitialReceiver,mapAdmitted,MOON_PROFILE,prefixSurface,boxSurface,encodeSrgb,initialReceiverCodes:typeof initialReceiverCodes===\'function\'?initialReceiverCodes:null};')();
const bytes=new Uint8Array(fs.readFileSync(path.join(root,'assets/initial-receivers.bin'))),pin=JSON.parse(fs.readFileSync(path.join(root,'initial-manifest.json')));
test('initial scalar V5 operator is exactly equal after Float32 admission',()=>{
 const out=new Float32Array(3);
 for(const mode of ['calendar','reference'])for(let i=0;i<5000;i++){
  const p={...api.MOON_PROFILE,mode,lift:mode==='calendar'?.003:0},c=[(i%173)/137,(i%97)/151,(i%41)/83].map(x=>Math.fround(x*10**(-8+i%10)));
  api.mapInitialReceiver(out,0,...c,p);assert.deepEqual(out,new Float32Array(api.mapAdmitted(c,p)));
 }
});
test('initial receiver refuses altered bytes and invalid geometry before publication',()=>{
 const bad=bytes.slice();bad[40]^=1;assert.throws(()=>api.createInitialMoon(bad,pin),/identity/);
 assert.throws(()=>api.createInitialMoon(bytes.subarray(0,100),pin),/identity/);
 const seed=api.createInitialMoon(bytes,pin),scene=api.canonicalScene({fraction:.08,waxing:true,size:540,outSize:108,diameter:103.68});
 assert.throws(()=>seed.render({...scene,mode:'physical-reference'}),/unsupported/);
 assert.throws(()=>seed.render({...scene,sun:[NaN,0,0]}),/phase/);
 assert.throws(()=>seed.render({...scene,fraction:.6}),/phase/);
 const v=seed.render(scene);assert.equal(v.diagnostics.quality.status,'initial-v5');assert.equal(v.surfaceSize,540);
 assert.ok(v.surfaceCoverage.every(x=>x===0||x===1));assert.ok(v.surfaceLinear.every(Number.isFinite));
});

test('prepared initial sampling is byte exact to the approved box filter, including clipped edge coverage',()=>{
 assert.equal(typeof api.initialReceiverCodes,'function');
 const N=37,linear=new Float32Array(N*N*3),coverage=new Float32Array(N*N);
 for(let i=0;i<N*N;i++){const a=i%13===0?0:i%7===0?.4:1;coverage[i]=a;for(let k=0;k<3;k++)linear[3*i+k]=a*((i*(k+3)%31)/31);}
 const table=api.prefixSurface({size:N,linear,coverage});
 for(const size of [108,300])for(const extent of [.8,1.08]){
  const scene={diameter:size*.96,extent},actual=api.initialReceiverCodes(table,scene,size),scale=N/(scene.diameter*extent),origin=N/2-size*scale/2,expected=new Uint8ClampedArray(size*size*4);
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
   const c=api.boxSurface(table,origin+x*scale,origin+y*scale,origin+(x+1)*scale,origin+(y+1)*scale),a=c[3],i=4*(y*size+x);
   for(let k=0;k<3;k++)expected[i+k]=Math.floor(255*api.encodeSrgb(a?c[k]/a:0)+.5);expected[i+3]=Math.floor(255*a+.5);
  }
  assert.deepEqual(actual,expected,`size ${size}, extent ${extent}`);
 }
});
