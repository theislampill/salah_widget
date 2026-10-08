/** Full terrain implementation MB1: raw source fields, actual WASM intersections
 * and shadows, both finite lights, then the unchanged V5 surface operator.
 * Runs in a Worker (Node worker-compatible). No main-thread fallback.
 */



const MOON_PROFILE=Object.freeze({schema:'lunar-presentation/5',profile_id:'calendar-neutral-v5-01',mode:'calendar',exposure:2.9195482731525044,lift:.003,knee:5.388411226362526e-6,colour_basis:'linear-sRGB',gamut:'luminance-preserving-neutral-axis'});
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const dot=(a,b)=>a.reduce((v,x,i)=>v+x*b[i],0);
const norm=v=>Math.hypot(...v);
const unit=v=>v.map(x=>x/norm(v));
const validVector=v=>(Array.isArray(v)||ArrayBuffer.isView(v))&&v.length===3&&Array.from(v).every(finite);
function canonicalScene({fraction,waxing=false,size=432,diameter=288,outSize=300,tilt=0,profile=MOON_PROFILE}={}){
 if(!finite(fraction)||fraction<0||fraction>1||typeof waxing!=='boolean'||!finite(tilt)||Math.abs(tilt)>180)throw new RangeError('canonical lunar geometry');
 const a=Math.acos(2*fraction-1),t=tilt*Math.PI/180;
 return {size,diameter,outSize,basis:[0,1,0,0,0,1,1,0,0],sun:[Math.cos(a),(waxing?1:-1)*Math.sin(a)*Math.cos(t),Math.sin(a)*Math.sin(t)],earth:[384400,0,0],distance:384400,extent:1.08,profile:{...profile},mode:'calendar-canonical',fraction,waxing,tilt};
}
function admitScene(s){
 if(!s||typeof s!=='object')throw new TypeError('scene');
 const q={...s,profile:admitProfile(s.profile??MOON_PROFILE)};
 if(![s.size,s.outSize].every(x=>Number.isInteger(x)&&x>=8&&x<=768)||!finite(s.diameter)||s.diameter<=0||s.diameter>768)throw new RangeError('scene raster/footprint');
 if(!s.basis||s.basis.length!==9||!Array.from(s.basis).every(finite)||!validVector(s.sun)||!validVector(s.earth)||Math.abs(norm(s.sun)-1)>1e-10)throw new RangeError('body-frame vectors');
 const b=[Array.from(s.basis).slice(0,3),Array.from(s.basis).slice(3,6),Array.from(s.basis).slice(6)];
 for(let i=0;i<3;i++)for(let j=0;j<3;j++)if(Math.abs(dot(b[i],b[j])-(i===j?1:0))>1e-10)throw new RangeError('orthonormal camera basis');
 const cross=[b[0][1]*b[1][2]-b[0][2]*b[1][1],b[0][2]*b[1][0]-b[0][0]*b[1][2],b[0][0]*b[1][1]-b[0][1]*b[1][0]];
 if(dot(cross,b[2])<.999999999)throw new RangeError('right-handed camera basis');
 if(!finite(s.distance)||s.distance<1753||!finite(s.extent)||s.extent<1||s.extent>2||norm(s.earth)<1753+6371)throw new RangeError('source / observer distance');
 if(s.fraction!==undefined&&(!finite(s.fraction)||Math.abs((1+dot(s.sun,b[2]))/2-s.fraction)>1e-7))throw new RangeError('phase/vector mismatch');
 if(!['calendar-canonical','physical-reference'].includes(s.mode))throw new RangeError('explicit view convention required');
 return structuredClone(q);
}
async function digestBytes(bytes){
 if(!(bytes instanceof Uint8Array))bytes=new Uint8Array(bytes);
 if(globalThis.crypto?.subtle){const hash=new Uint8Array(await crypto.subtle.digest('SHA-256',bytes));return Array.from(hash,x=>x.toString(16).padStart(2,'0')).join('');}
 if(bytes.length<=1048576)return sha256Hex(bytes);
 return assetDigest(bytes);
}
async function decodeAsset(bytes,spec){
 if(!(bytes instanceof Uint8Array))bytes=new Uint8Array(bytes);
 if(bytes.length!==spec.bytes||await digestBytes(bytes)!==spec.sha256)throw new Error('Moon asset compressed identity mismatch');
 if(!Array.isArray(spec.shape)||spec.shape.length!==3||!spec.shape.every(x=>Number.isInteger(x)&&x>0&&x<=8192)||![1,3].includes(spec.shape[2]))throw new Error('Moon asset shape');
 const count=spec.shape.reduce((a,b)=>a*b,1);if(count*2!==spec.decodedBytes||count*2>128*1024*1024)throw new Error('Moon decompression size');
 const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip')),reader=stream.getReader();
 const dec=new Uint8Array(count*2);let at=0;
 try{for(;;){const {done,value}=await reader.read();if(done)break;if(at+value.length>dec.length)throw new Error('Oversized Moon asset');dec.set(value,at);at+=value.length;}}finally{await reader.cancel();}
 if(at!==dec.length)throw new Error('Truncated Moon asset');
 const raw=new Uint16Array(count),row=spec.shape[1]*spec.shape[2],ch=spec.shape[2];
 for(let i=0;i<count;i++){const d=dec[i]|(dec[count+i]<<8);raw[i]=(d+(i%row>=ch?raw[i-ch]:0))&65535;}
 if(await digestBytes(new Uint8Array(raw.buffer))!==spec.rawSha256)throw new Error('Decoded Moon asset identity mismatch');
 return raw;
}
// Yield a WORKER task, not a microtask. Nested zero-delay timers add a browser
// clamp after each ~8 ms slice (measured ~300 ms per 640 ms of useful work).
// MessageChannel keeps cancellation/messages serviceable without that delay;
// numerical ordering, sampling, quality gates and elapsed deadlines are unchanged.
const lunarYieldQueue=[],lunarYieldChannel=typeof MessageChannel==='function'?new MessageChannel():null;
if(lunarYieldChannel){
 lunarYieldChannel.port1.onmessage=()=>{const wake=lunarYieldQueue.shift();wake?.();if(!lunarYieldQueue.length)lunarYieldChannel.port1.unref?.();};
 lunarYieldChannel.port1.unref?.();lunarYieldChannel.port2.unref?.();
}
const pause=()=>new Promise(resolve=>{if(!lunarYieldChannel){setTimeout(resolve,0);return;}lunarYieldQueue.push(resolve);lunarYieldChannel.port1.ref?.();lunarYieldChannel.port2.postMessage(0);});
class MoonEngine{
 static async create({wasm,dem,colour,manifest}){
  if(manifest.schema!=='moon-worker-assets/1'||manifest.codec!=='u16le-left-delta-byteplanes-gzip/1')throw new Error('Moon asset contract');
  if(manifest.wasm && await digestBytes(wasm)!==manifest.wasm.sha256)throw new Error('Moon WASM identity mismatch');
  const {instance}=await WebAssembly.instantiate(wasm,{math:Math});const e=instance.exports;
  if(e.kernel_version()!==1)throw new Error('Moon kernel ABI');
  const ptrs=[];for(const [name,blob] of [['dem',dem],['colour',colour]]){
   const a=await decodeAsset(blob,manifest.assets[name]),p=e.alloc_buffer(a.byteLength);if(!p)throw new Error('Moon asset memory limit');new Uint16Array(e.memory.buffer,p,a.length).set(a);ptrs.push(p);
  }
  if(!e.init_assets(ptrs[0],manifest.assets.dem.shape[1],manifest.assets.dem.shape[0],ptrs[1],manifest.assets.colour.shape[1],manifest.assets.colour.shape[0]))throw new Error('Moon numeric asset admission');
  const engine=new MoonEngine();engine.e=e;engine.p=e.alloc_buffer(15*8);engine.cameraKey=null;engine.manifestIdentity=await digestBytes(new TextEncoder().encode(JSON.stringify(manifest)));engine.maskPointer=e.alloc_buffer(768*768);engine.lightKey=null;engine.active=false;return engine;
 }
 async render(scene,{radial=8,azimuth=32,cancelled=()=>false,onProgress=()=>{},diagnostic=false,analytic=true,lightingMask=null,qualityFields=false}={}){
  if(this.active)throw new Error('One owned Moon computation at a time');
  if(!Number.isInteger(radial)||!Number.isInteger(azimuth)||radial<1||radial>64||azimuth<4||azimuth>256||radial*azimuth>8192)throw new RangeError('Source quadrature');
  const s=admitScene(scene),e=this.e,start=performance.now();
  const lightKey=JSON.stringify([s.size,s.basis,s.sun,s.earth,s.distance,s.extent]);
  if(lightingMask!==null&&(!(lightingMask instanceof Uint8Array)||lightingMask.length!==s.size*s.size||lightingMask.some(x=>x>3)||this.lightKey!==lightKey))throw new Error('Sparse source refinement requires the same admitted physical scene');
  if(lightingMask)new Uint8Array(e.memory.buffer,this.maskPointer,lightingMask.length).set(lightingMask);
  this.active=true;
  try{
   const cameraKey=JSON.stringify([s.size,s.basis,s.distance,s.extent]);let arr=new Float64Array(e.memory.buffer,this.p,15);arr.set(s.basis);arr.set(s.sun,9);arr.set(s.earth,12);
   let reused=this.cameraKey===cameraKey;
   if(!reused){if(!e.begin_scene(s.size,this.p,this.p+72,this.p+96,s.distance,s.extent,1e-5,.002,.85,.31873105385527434,.266*Math.PI/180,radial,azimuth))throw new Error('Moon scene refused');this.cameraKey=null;}
   else if(!e.set_lights(this.p+72,this.p+96,radial,azimuth))throw new Error('Moon source refused');
   const N=s.size;let lastYield=performance.now();
   const step=async(stage,first,count)=>{
    if(cancelled())throw new DOMException('Superseded Moon job','AbortError');
    stage==='camera'?e.camera_rows(first,count):(lightingMask?e.light_rows_selected(first,count,3,1,analytic?1:0,this.maskPointer):e.light_rows(first,count,3,1,analytic?1:0));
    if(performance.now()-lastYield>8){onProgress({stage,row:first+count,total:N});await pause();lastYield=performance.now();}
   };
   if(!reused){for(let y=0;y<N;y+=4)await step('camera',y,Math.min(4,N-y));this.cameraKey=cameraKey;}
   const cameraMs=performance.now()-start;
   for(let y=0;y<N;y++)await step('lighting',y,1);
   if(cancelled())throw new DOMException('Superseded Moon job','AbortError');
   this.lightKey=lightKey;
   const litMs=performance.now()-start-cameraMs,pix=new Float64Array(e.memory.buffer,e.get_pixels(),N*N*24),counters=Array.from(new Float64Array(e.memory.buffer,e.get_counters(),8));
   if(counters[7]>0)throw new Error('Unresolved lunar outer contour; current legacy fallback required');
   const solar=new Float32Array(N*N*3),earth=new Float32Array(N*N*3),coverage=new Float64Array(N*N);let known=0,unknown=0,shadowed=0;
   for(let i=0;i<N*N;i++){
    const p=i*24;coverage[i]=pix[p+17];if(pix[p+18]===1)known++;if(pix[p+18]===2)unknown++;
    if(pix[p+14]>1e-8&&pix[p+12]<pix[p+14]*.01)shadowed++;
    for(let k=0;k<3;k++){solar[3*i+k]=pix[p+6+k]*pix[p+12]*e.material_gain();earth[3*i+k]=pix[p+6+k]*pix[p+13]*e.material_gain();}
   }
   const display=renderSurfaceFrame({width:N,height:N,solar,earth,coverage,profile:s.profile,outSize:s.outSize,scale:N/(s.diameter*s.extent),centreX:N/2,centreY:N/2});
   const rgba=new Uint8ClampedArray(s.outSize*s.outSize*4);
   for(let i=0;i<display.coverage.length;i++){for(let k=0;k<3;k++)rgba[4*i+k]=Math.floor(display.straightSrgb[3*i+k]*255+.5);rgba[4*i+3]=Math.floor(display.coverage[i]*255+.5);}
   const result={rgba,width:s.outSize,height:s.outSize,scene:s,profileIdentity:await profileFingerprint(s.profile),physicalIdentity:await digestBytes(new TextEncoder().encode(JSON.stringify([this.manifestIdentity,s.basis,s.sun,s.earth,s.distance,N,s.extent,radial,azimuth]))),diagnostics:{kernel:'metric-radial-terrain-wasm-mb1',cameraReused:reused,cameraMs,lightingMs:litMs,totalMs:performance.now()-start,knownSurfaceSamples:known,unresolvedShading:unknown,unresolvedContour:counters[7],shadowedFacingSamples:shadowed,sourceSamples:radial*azimuth,analyticClearSun:analytic,analyticSamples:counters[3],shadowRays:counters[2],blockerWitnesses:counters[4],memoryBytes:e.memory.buffer.byteLength,model:'V5 nominal lunar-Lambert / grey finite Earth; not calibrated spectroscopy'}};
   if(qualityFields){
    const receiverCodes=new Float32Array(N*N*3),ambiguous=new Uint8Array(N*N),surfaceLinear=new Float32Array(N*N*3);
    for(let i=0;i<N*N;i++){
     const c=mapSurfaceRgb(solar.subarray(3*i,3*i+3),earth.subarray(3*i,3*i+3),s.profile);
     for(let k=0;k<3;k++){receiverCodes[3*i+k]=encodeSrgb(c[k])*255;surfaceLinear[3*i+k]=c[k]*coverage[i];}
     const p=i*24;ambiguous[i]=((pix[p+20]===2&&pix[p+14]>1e-12)?1:0)|((pix[p+21]===2&&pix[p+13]+pix[p+16]>1e-15)?2:0);
    }Object.assign(result,{receiverCodes,ambiguous,surfaceLinear,surfaceCoverage:new Float32Array(coverage),surfaceSize:N,surfaceExtent:s.extent});
    result.qualityImages=[projectSurfaceCodes({size:N,linear:surfaceLinear,coverage,extent:s.extent},312),projectSurfaceCodes({size:N,linear:surfaceLinear,coverage,extent:s.extent},312,[.37,-.21])];
   }
   if(diagnostic)Object.assign(result,{solar,earth,coverage,...(diagnostic==='fields'?{}:{pixels:pix.slice()}),displayLinear:display.premultipliedLinear});
   return result;
  }catch(error){this.lightKey=null;throw error;}finally{this.active=false;}
 }
}

