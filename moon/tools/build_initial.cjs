#!/usr/bin/env node
'use strict';
// Explicit, deterministic derivative build. Ordinary native builds verify and
// embed the retained derivative; they never repeat this terrain investigation.
// Only canonical receiver geometry/material and solar visibility boundaries are
// stored. No observer, clock, phase image or accepted result is cached.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),moon=path.join(root,'moon'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const units=['asset-digest.mjs','surface_v5.mjs','moon-detail.mjs','moon-calendar.mjs','moon-engine.mjs'];
const api=Function(units.map(n=>fs.readFileSync(path.join(moon,'src',n),'utf8')).join('\n')+'\nreturn {MoonEngine,canonicalScene};')();
async function main(){
 const manifestBytes=fs.readFileSync(path.join(moon,'asset-manifest.json')),manifest=JSON.parse(manifestBytes),wasm=new Uint8Array(fs.readFileSync(path.join(moon,'moon_kernel.wasm')));
 const engine=await api.MoonEngine.create({wasm,manifest,...Object.fromEntries(['dem','colour'].map(k=>[k,new Uint8Array(fs.readFileSync(path.join(moon,manifest.assets[k].path)))]))}),e=engine.e;
 const N=540,scene=api.canonicalScene({fraction:.5,waxing:true,size:N,outSize:300,diameter:288}),camera=new Float64Array(e.memory.buffer,engine.p,15);camera.set(scene.basis);camera.set(scene.sun,9);camera.set(scene.earth,12);
 if(!e.begin_scene(N,engine.p,engine.p+72,engine.p+96,scene.distance,scene.extent,1e-5,.002,.85,.31873105385527434,.266*Math.PI/180,2,8))throw Error('Initial camera refused');
 e.camera_rows(0,N);
 const pix=new Float64Array(e.memory.buffer,e.get_pixels(),N*N*24).slice(),counters=new Float64Array(e.memory.buffer,e.get_counters(),8);
 if(counters[6]||counters[7])throw Error('Unresolved initial receiver geometry');
 const p=e.alloc_buffer(24),d=e.alloc_buffer(24),o=e.alloc_buffer(32),arrp=new Float64Array(e.memory.buffer,p,3),arrd=new Float64Array(e.memory.buffer,d,3),arro=new Float64Array(e.memory.buffer,o,4);
 const mask=Buffer.alloc(Math.ceil(N*N/8)),records=[];let uncertain=0,nonmonotone=0,positive=0,negative=0;
 const round=x=>Math.floor(x+.5);
 for(let i=0;i<N*N;i++){
  const at=i*24;if(pix[at+18]!==1)continue;arrp.set(pix.subarray(at,at+3));mask[i>>3]|=1<<(i&7);const horizon=[];
  for(let sense=0;sense<2;sense++){
   const sign=sense?1:-1;
   const visible=alpha=>{
    arrd.set([Math.cos(alpha),sign*Math.sin(alpha),0]);if(arrd[0]*pix[at+3]+arrd[1]*pix[at+4]<=0)return false;
    e.probe_trace(p,d,.002,7000,1e-5,20000,1,o);
    // ABI is [distance, code, visits]. Unresolved terrain is conservatively
    // excluded from this INITIAL visibility boundary, never labelled clear.
    if(arro[1]===2)uncertain++;return arro[1]===0;
   };
   let lo=0,hi=Math.PI;
   for(let n=0;n<12;n++){const middle=(lo+hi)/2;if(visible(middle))lo=middle;else hi=middle;}
   const h=(lo+hi)/2;horizon.push(h);
   // Held-out angles discriminate failures of the single-boundary assumption.
   // Keep the residual counts in the manifest; this is no scientific closure.
   for(let q=1;q<16;q++){const alpha=q*Math.PI/16,v=visible(alpha);v?positive++:negative++;if(v!==(alpha<h))nonmonotone++;}
  }
  const b=Buffer.alloc(20);b.writeFloatLE(pix[at],0);
  for(let k=0;k<3;k++){b.writeInt16LE(round(pix[at+3+k]*32767),4+2*k);b.writeUInt16LE(round(pix[at+6+k]*65535),10+2*k);}
  for(let k=0;k<2;k++)b.writeUInt16LE(round(horizon[k]*65535/Math.PI),16+2*k);records.push(b);
 }
 const header=Buffer.alloc(6);header.writeUInt32LE(0x31494d53,0);header.writeUInt16LE(N,4);const bytes=Buffer.concat([header,mask,...records]);
 const pin={schema:'moon-initial-receivers/1',size:N,records:records.length,bytes:bytes.length,sha256:sha(bytes),
  parent:{manifestSha256:sha(manifestBytes),wasmSha256:sha(wasm),demRawSha256:manifest.assets.dem.rawSha256,colourRawSha256:manifest.assets.colour.rawSha256},
  source:Object.fromEntries([...units,'moon_kernel.c'].map(n=>['moon/src/'+n,sha(fs.readFileSync(path.join(moon,'src',n)))]).concat([['moon/tools/build_initial.cjs',sha(fs.readFileSync(__filename))]])),
  geometry:{basis:scene.basis,distance:scene.distance,extent:scene.extent,materialGain:.31873105385527434,modelK:.85},
  approximation:{horizonBisections:12,maximumHorizonHalfIntervalRadians:Math.PI/8192,normalEncoding:'signed16 normalised at admission',materialEncoding:'linear unorm16',positionEncoding:'float32 camera depth; rigid rays reconstructed',finiteSourceSamples:16,offPlaneTerrain:'full worker refinement required',earthTerrain:'observer-facing approximation; full worker refinement required'},
  probes:{heldOutAnglesPerSense:15,positive,negative,unresolvedTraceCalls:uncertain,singleBoundaryDisagreements:nonmonotone}};
 fs.writeFileSync(path.join(moon,'assets/initial-receivers.bin'),bytes);fs.writeFileSync(path.join(moon,'initial-manifest.json'),JSON.stringify(pin,null,2)+'\n');console.log(JSON.stringify(pin));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
