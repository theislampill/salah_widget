/** Two independent row owners, the SAME kernel and one global quality/display
 * decision. This changes scheduling, not quadrature, geometry or pixel order.
 * Each kernel owns its camera/cache; only its assigned lighting rows are joined.
 */
function moonRowBridge(worker){
 const waiting=new Map();let serial=0,failure=null;
 const fail=error=>{failure??=error;for(const p of waiting.values())p.reject(failure);waiting.clear();};
 const call=(kind,data={},onProgress=()=>{})=>new Promise((resolve,reject)=>{
  if(failure){reject(failure);return;}
  const id=++serial;waiting.set(id,{resolve,reject,onProgress,expected:kind==='shard-boot'?'shard-ready':'shard-result'});
  try{worker.postMessage({kind,id,...data});}catch(error){fail(error);}
 });
 worker.onmessage=e=>{
  const m=e.data;if(!m||typeof m!=='object'||m.kind==='boot-error'){fail(new Error(m?.error||'Moon row message contract'));return;}
  const p=waiting.get(m.id);if(!p)return; // An already revoked request has no authority.
  if(m.kind==='shard-progress'){p.onProgress(m.progress);return;}
  if(m.kind==='shard-error'){
   const error=Object.assign(new Error(m.error),{name:m.name??'Error'});waiting.delete(m.id);p.reject(error);
   if(error.name!=='AbortError')fail(error);return;
  }
  if(m.kind!==p.expected){fail(new Error('Moon row reply kind'));return;}
  waiting.delete(m.id);p.resolve(m.result);
 };
 worker.onerror=e=>fail(new Error(e.message||'Moon row worker failed'));worker.onmessageerror=()=>fail(new Error('Moon row message decode failed'));
 return {worker,boot:assets=>call('shard-boot',{assets}),render(scene,options){const {onProgress,cancelled,...plain}=options;return call('shard-render',{scene,options:plain},onProgress);},cancel(){if(!failure)try{worker.postMessage({kind:'shard-cancel'});}catch(error){fail(error);}},dispose(){worker.terminate();fail(new Error('Moon row worker disposed'));}};
}
class MoonPool {
 constructor(workers){if(workers.length!==2)throw new RangeError('Two lunar row owners required');this.workers=workers;this.lightKey=null;this.material=null;this.serial=0;}
 static async create(assets,workerSource){
  if(typeof workerSource!=='string'||!workerSource.length)throw new Error('Owned lunar worker source required');
  // A file document's blob URL belongs to its opaque origin. A nested worker
  // cannot reuse that ancestor URL; create an identical source Blob owned by
  // this worker instead. No network fetch or relaxed browser security.
  const bridges=[],url=URL.createObjectURL(new Blob([workerSource],{type:'text/javascript'}));
  try{
   for(let i=0;i<2;i++){
    const bridge=moonRowBridge(new Worker(url));bridge.ready=bridge.boot(assets);bridges.push(bridge);
   }
   await Promise.all(bridges.map(b=>b.ready));return new MoonPool(bridges);
  }catch(error){for(const b of bridges)b.dispose();throw error;}
  finally{URL.revokeObjectURL(url);}
 }
 cancel(){this.serial++;for(const w of this.workers)w.cancel();}
 async render(scene,options={}){
  const s=admitScene(scene),start=performance.now(),token=this.serial,cancelled=()=>token!==this.serial||options.cancelled?.();
  if(cancelled())throw new DOMException('Superseded Moon rows','AbortError');
  const N=s.size,key=JSON.stringify([N,s.basis,s.sun,s.earth,s.distance,s.extent]),first=this.lightKey!==key;
  if(options.lightingMask!=null&&(!(options.lightingMask instanceof Uint8Array)||options.lightingMask.length!==N*N||options.lightingMask.some(x=>x>3)||first))throw new Error('Sparse row refinement requires the same admitted physical scene');
  const ranges=[[0,Math.floor(N/2)],[Math.floor(N/2),N]];
  // The first rule initializes the existing kernel's full receiver cache. Later
  // rules partition its supported sparse mask. No uninitialized row is read.
  let failed=null;
  const work=this.workers.map((w,i)=>{
   const [lo,hi]=ranges[i],mask=first?null:new Uint8Array(N*N);
   if(mask){if(options.lightingMask)mask.set(options.lightingMask.subarray(lo*N,hi*N),lo*N);else mask.fill(3,lo*N,hi*N);}
   return w.render(s,{...options,lightingMask:mask,rowOwner:[lo,hi],onProgress:p=>options.onProgress?.({...p,rowOwner:i})}).catch(error=>{failed??=error;for(const sibling of this.workers)sibling.cancel();throw error;});
  });
  const replies=await Promise.allSettled(work);
  if(cancelled()){this.lightKey=null;throw new DOMException('Superseded Moon rows','AbortError');}
  if(failed){this.lightKey=null;throw failed;}
  const parts=replies.map(x=>x.value),a=parts[0];
  const profileIdentity=await profileFingerprint(s.profile);
  if(!a||typeof a.physicalIdentity!=='string'||!a.physicalIdentity||parts.some(p=>!p||p.physicalIdentity!==a.physicalIdentity||p.profileIdentity!==profileIdentity||p.surfaceSize!==N||JSON.stringify(p.scene)!==JSON.stringify(s)))throw new Error('Moon row identity mismatch');
  const fields={solar:[Float32Array,3],earth:[Float32Array,3],coverage:[Float64Array,1],receiverCodes:[Float32Array,3],ambiguous:[Uint8Array,1],surfaceLinear:[Float32Array,3],surfaceCoverage:[Float32Array,1]};
  const result={...a};
  for(const [name,[Type,stride]] of Object.entries(fields)){
   const joined=new Type(N*N*stride);
   for(let j=0;j<parts.length;j++){
    const source=parts[j][name],[lo,hi]=ranges[j];if(!(source instanceof Type)||source.length!==joined.length)throw new Error('Moon row field shape: '+name);
    // Reject the whole reply, including dormant cache rows; they can become
    // owned after a future scene. No partially validated shard is published.
    const limit=name==='coverage'||name==='surfaceCoverage'||name==='surfaceLinear'?1.000001:name==='ambiguous'?3:Infinity;
    for(const value of source)if(!Number.isFinite(value)||value<0||value>limit)throw new Error('Moon row field value: '+name);
    joined.set(source.subarray(lo*N*stride,hi*N*stride),lo*N*stride);
   }
   result[name]=joined;
  }
  if(!(a.material instanceof Float32Array)||a.material.length!==N*N*3||a.material.some(v=>!Number.isFinite(v)||v<0))throw new Error('Moon row material shape/value');this.material=a.material;
  // Filter AFTER joining receiver fields, including taps crossing the internal
  // boundary. Concatenating already-filtered half images would create a seam.
  const display=renderSurfaceFrame({width:N,height:N,solar:result.solar,earth:result.earth,coverage:result.coverage,profile:s.profile,outSize:s.outSize,scale:N/(s.diameter*s.extent),centreX:N/2,centreY:N/2});
  result.rgba=new Uint8ClampedArray(s.outSize*s.outSize*4);
  for(let i=0;i<display.coverage.length;i++){for(let k=0;k<3;k++)result.rgba[4*i+k]=Math.floor(display.straightSrgb[3*i+k]*255+.5);result.rgba[4*i+3]=Math.floor(display.coverage[i]*255+.5);}
  result.qualityImages=[projectSurfaceCodes({size:N,linear:result.surfaceLinear,coverage:result.coverage,extent:s.extent},312),projectSurfaceCodes({size:N,linear:result.surfaceLinear,coverage:result.coverage,extent:s.extent},312,[.37,-.21])];
  result.diagnostics={...a.diagnostics,totalMs:performance.now()-start,cameraMs:Math.max(...parts.map(p=>p.diagnostics.cameraMs)),lightingMs:Math.max(...parts.map(p=>p.diagnostics.lightingMs)),memoryBytes:parts.reduce((n,p)=>n+p.diagnostics.memoryBytes,0),shadowedFacingSamples:parts.every(p=>Number.isInteger(p.diagnostics.ownedShadowedFacingSamples))?parts.reduce((n,p)=>n+p.diagnostics.ownedShadowedFacingSamples,0):null,rowScheduling:{workers:2,ranges,initialCacheRule:first,globalQuality:true,globalFiltering:true,workerTimes:parts.map(p=>p.diagnostics.totalMs)}};
  // These are actual compute counters (including the duplicated first rule),
  // whereas knownSurfaceSamples describes the one assembled camera surface.
  for(const field of ['analyticSamples','shadowRays','blockerWitnesses'])result.diagnostics[field]=parts.reduce((n,p)=>n+p.diagnostics[field],0);
  delete result.diagnostics.ownedShadowedFacingSamples;
  delete result.material;this.lightKey=key;return result;
 }
}
