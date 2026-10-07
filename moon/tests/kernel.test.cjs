'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.join(__dirname,'..'),units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs','moon-quality.mjs','moon-precision.mjs'];
const api=Function(units.map(n=>fs.readFileSync(path.join(root,'src',n),'utf8')).join('\n')+'\nreturn {MoonEngine,canonicalScene,admitScene,decodeAsset,prefixSurface,boxSurface,joinLunarPixel,canonicalFraction,admitProfile,mapSurfaceRgb,MOON_PROFILE};')();
const manifest=JSON.parse(fs.readFileSync(path.join(root,'asset-manifest.json'),'utf8'));
let engine;
const bytes=n=>new Uint8Array(fs.readFileSync(path.join(root,n)));
async function get(){if(!engine)engine=await api.MoonEngine.create({wasm:bytes('moon_kernel.wasm'),dem:bytes(manifest.assets.dem.path),colour:bytes(manifest.assets.colour.path),manifest});return engine;}
test('WASM checksum matches the bound original kernel',()=>{const h=crypto.createHash('sha256').update(bytes('moon_kernel.wasm')).digest('hex');assert.equal(h,manifest.wasm.sha256);});
test('truncated material is rejected before decompression',async()=>{const b=bytes(manifest.assets.colour.path);await assert.rejects(()=>api.decodeAsset(b.subarray(0,b.length-1),manifest.assets.colour),/identity mismatch/);});
test('corrupt terrain of correct length is rejected',async()=>{const b=bytes(manifest.assets.dem.path);b[32]^=1;await assert.rejects(()=>api.decodeAsset(b,manifest.assets.dem),/identity mismatch/);});
test('WASM corruption is rejected',async()=>{const w=bytes('moon_kernel.wasm');w[8]^=1;await assert.rejects(()=>api.MoonEngine.create({wasm:w,dem:bytes(manifest.assets.dem.path),colour:bytes(manifest.assets.colour.path),manifest}),/WASM identity/);});
test('same material coordinates are used for waxing and waning',()=>{const a=api.canonicalScene({fraction:.12,waxing:false}),b=api.canonicalScene({fraction:.12,waxing:true});assert.deepEqual(a.basis,b.basis);assert.equal(a.sun[0],b.sun[0]);assert.equal(a.sun[1],-b.sun[1]);});
test('scene rejects handedness reversal',()=>{const s=api.canonicalScene({fraction:.5});s.basis[1]=-1;assert.throws(()=>api.admitScene(s),/right-handed/);});
test('phase vector mismatch refused',()=>{const s=api.canonicalScene({fraction:.5});s.fraction=.9;assert.throws(()=>api.admitScene(s),/phase\/vector/);});
test('phase precision preserves endpoints and declared geometric bound',()=>{for(let i=0;i<=10000;i++){const f=i/10000;assert.ok(Math.abs(api.canonicalFraction(f)-f)*416<=.041600001);}assert.equal(api.canonicalFraction(0),0);assert.equal(api.canonicalFraction(1),1);});

test('display-aware phase preserves the original .0416 device-pixel angular displacement bound',()=>{
 assert.notEqual(api.canonicalFraction(.0815410407195768,104),api.canonicalFraction(.0815410407195768,416));
 // Independent rotation/chord bound, including endpoint caps and both phase senses.
 for(const diameter of [52,104,130,208,312,416,624])for(let i=0;i<=20000;i++){
  const alpha=Math.PI*i/20000,f=(1+Math.cos(alpha))/2,q=api.canonicalFraction(f,diameter),beta=Math.acos(2*q-1);
  const displacement=diameter*Math.sin(Math.abs(alpha-beta)/2);
  assert.ok(displacement<=.04160001,`${diameter} / ${alpha}: ${displacement}`);
  assert.ok(diameter*Math.abs(q-f)<=.04160001);
 }
});
test('black opaque Moon suppresses stars even during calendar fade',()=>{for(const opacity of [0,.5,1]){const r=api.joinLunarPixel({gas:[0,0,0],direct:[1,1,1],premult:[0,0,0],coverage:1,opacity,cloud:[0,0,0,0],exposure:12});assert.deepEqual(r,[0,0,0]);}});
test('zero coverage leaves direct sky intact',()=>{const r=api.joinLunarPixel({gas:[.1,.2,.3],direct:[1,1,1],premult:[0,0,0],coverage:0,opacity:1,cloud:[0,0,0,0],exposure:12});assert.deepEqual(r,[1.1,1.2,1.3]);});
test('cloud foreground is applied once',()=>{const r=api.joinLunarPixel({gas:[1,1,1],direct:[0,0,0],premult:[0,0,0],coverage:0,opacity:1,cloud:[.2,.2,.2,.5],exposure:12});for(const x of r)assert.equal(x,.6);});
test('fractional area filtering retains constant field and coverage',()=>{const p=api.prefixSurface({size:4,linear:new Float32Array(48).fill(.25),coverage:new Float32Array(16).fill(.5)});const v=api.boxSurface(p,.37,.21,3.1,2.8);v.forEach((x,k)=>assert.ok(Math.abs(x-(k===3?.5:.25))<1e-12));});
test('unknown NaN lighting never becomes an alpha hole',()=>{const a=new Float32Array(12);a[0]=NaN;assert.throws(()=>api.prefixSurface({size:2,linear:a,coverage:new Float32Array(4).fill(1)}));});
test('real assets decode, actual terrain renders and cancels',async()=>{const e=await get(),s=api.canonicalScene({fraction:.5,size:32,outSize:64,diameter:61.44});const a=await e.render(s,{radial:2,azimuth:8,diagnostic:true});assert.equal(a.diagnostics.kernel,'metric-radial-terrain-wasm-mb1');assert.equal(a.rgba.length,64*64*4);assert.ok(a.rgba.some(x=>x>0));await assert.rejects(()=>e.render(s,{cancelled:()=>true}),e=>e.name==='AbortError');});
test('V5 grey remains neutral over weak and strong Earthlight',()=>{for(const x of [0,1e-12,1e-8,1e-6,.001,.1,1,10]){const r=api.mapSurfaceRgb([0,0,0],[x,x,x],api.MOON_PROFILE);assert.equal(r[0],r[1]);assert.equal(r[1],r[2]);assert.ok(r.every(v=>Number.isFinite(v)&&v>=0&&v<=1));}});
test('V5 display does not depend on Sun/Earth partition of identical light',()=>{const c=[.125,.25,.5],a=api.mapSurfaceRgb(c,[0,0,0],api.MOON_PROFILE),b=api.mapSurfaceRgb([0,0,0],c,api.MOON_PROFILE);assert.deepEqual(a,b);});
test('V5 luminance does not fall when neutral illumination increases',()=>{let prior=-1;for(let i=0;i<100;i++){const x=10**(-10+i/10),r=api.mapSurfaceRgb([x,x,x],[0,0,0],api.MOON_PROFILE);const y=.2126*r[0]+.7152*r[1]+.0722*r[2];assert.ok(y>=prior);prior=y;}});
