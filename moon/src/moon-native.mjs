window.SalahMoonDetail?.dispose();window.SalahMoonDetail=startMoonDetail();
/* MB1 optional full lunar terrain worker. The existing native host alone owns
 * phase, UTC, observer intent and generation. No UI-thread terrain fallback. */
(function(){'use strict';
 window.SalahMoonRuntime?.dispose();
 const script=document.currentScript;
 // A fully embedded document has no relative assets, including in an opaque iframe.
 const base=window.__SALAH_MOON_EMBEDDED__?(document.baseURI||'about:blank'):new URL('.',script?.src||document.baseURI).href;
 const canvas=document.createElement('canvas');canvas.width=300;canvas.height=300;
 let worker=null,url=null,disposed=false,ready=false,pending=null,accepted=null,serial=0,epoch=0,retryCount=0,clock=null,referenceScene=null,profileMode='calendar';
 let timer=null,deadline=null,lastError=null,chunkScript=null,upperBytes=null,calendarBytes=null,textureUp=null;
 const status={status:'loading',backend:'metric-terrain-wasm-mb1',renders:0,rejected:0,cancelled:0,errors:[],legacyFallback:true,quality:'pending'};
 const profile=()=>profileMode==='reference'?{...MOON_DEFAULT_PROFILE,profile_id:'unboosted-v5-01',mode:'reference',lift:0}:{...MOON_DEFAULT_PROFILE};
 function capture(){
  const h=window.SalahMoonHost;if(!h)return null;let s;try{s=h.capture();}catch{return null;}
  if(!s||typeof s.sceneIdentity!=='string'||!Number.isSafeInteger(s.generation)||s.generation<0||!Number.isFinite(s.utcMs)||!Number.isFinite(s.fraction)||s.fraction<0||s.fraction>1||typeof s.waxing!=='boolean'||!Number.isFinite(s.up)||!Number.isFinite(s.dpr))return null;
  // The image rectangle encloses the lunar disc. Round up, so subpixel layout
  // noise cannot understate the bound; translation never changes this identity.
  const rect=document.querySelector('.mphoto')?.getBoundingClientRect();
  const phaseDiameter=rect&&rect.width>0&&rect.height>0?Math.ceil(Math.max(rect.width,rect.height)*s.dpr):416;
  return {...s,phaseDiameter,phaseQuantum:phaseQuantum(phaseDiameter),physicalFraction:canonicalFraction(s.fraction,phaseDiameter),profileMode,referenceIdentity:referenceScene?JSON.stringify(referenceScene):null};
 }
 const key=s=>JSON.stringify([s.generation,s.sceneIdentity,s.physicalFraction,s.waxing,s.dpr,s.profileMode,s.referenceIdentity,s.phaseDiameter]);
 function syncTexture(s){
  if(!accepted||!upperBytes||!s)return;const up=profileMode==='reference'?1:Math.max(0,Math.min(1,s.up));
  if(textureUp===up)return;textureUp=up;const rgba=blendCalendarBytes(upperBytes,calendarBytes,up);canvas.getContext('2d').putImageData(new ImageData(rgba,canvas.width,canvas.height),0,0);window.SalahMoonHost?.publish(canvas);
 }
 const clockDiscontinuous=(s,now=performance.now())=>!!clock&&Math.abs((s.utcMs-clock.utcMs)-(now-clock.now)*clock.rate)>1000;
 // Check at publication/read time as well as polling: a seek cannot slip an
 // otherwise identical result through the interval before the next host poll.
 const matches=(record,s)=>!!record&&!!s&&!s.paused&&!clockDiscontinuous(s)&&record.epoch===epoch&&record.key===key(s);
 function fallback(reason){accepted=null;upperBytes=null;calendarBytes=null;textureUp=null;status.legacyFallback=true;status.reason=reason;window.SalahMoonHost?.fallback();window.SalahMoonDetail?.clear();}
 function clear(reason){
  epoch++;serial++;pending=null;clearTimeout(deadline);deadline=null;try{worker?.postMessage({kind:'cancel'});}catch{/* A crashed worker cannot veto withdrawal. */}status.cancelled++;fallback(reason);
 }
 function closeWorker(){
  ready=false;worker?.terminate();worker=null;if(url)URL.revokeObjectURL(url);url=null;
  if(chunkScript){chunkScript.remove();chunkScript=null;}delete window.SalahMoonAssetChunk;
 }
 function failed(error){
  if(disposed)return;const message=String(error?.message??error);clear('worker failure');status.status='unavailable';lastError=message;
  if(status.errors.at(-1)!==message)status.errors.push(message);status.errors=status.errors.slice(-8);closeWorker();
 }
 function scene(s){
  if(referenceScene)return {...structuredClone(referenceScene),profile:profile()};
  const alpha=Math.acos(2*s.physicalFraction-1);
  return {size:540,outSize:300,diameter:288,basis:[0,1,0,0,0,1,1,0,0],sun:[Math.cos(alpha),(s.waxing?1:-1)*Math.sin(alpha),0],earth:[384400,0,0],distance:384400,extent:1.08,profile:profile(),mode:'calendar-canonical',fraction:s.physicalFraction,waxing:s.waxing,tilt:0,requestedNativeFraction:s.fraction,phaseQuantumRadians:s.phaseQuantum,phaseDisplayDiameter:s.phaseDiameter,geometryConvention:'display-bounded canonical Sun-angle buckets; native UTC unchanged'};
 }
 function poll(force=false){
  if(disposed)return;const s=capture(),now=performance.now();
  if(!s){if(accepted||pending)clear('invalid native lunar scene');clock=null;status.status='waiting-native';return;}
  const jump=clockDiscontinuous(s,now);
  if(jump)clear('native clock discontinuity');clock={utcMs:s.utcMs,now,rate:s.timeScale??1};
  if(s.paused){if(pending||accepted)clear('native paused');status.status='paused';return;}
  if(accepted&&!matches(accepted,s))clear('native lunar target changed');
  if(pending&&!matches(pending,s))clear('superseded native lunar request');
  if(!ready||!worker){if(!lastError)status.status='loading';return;}
  if(matches(accepted,s))syncTexture(s);
  if(matches(pending,s)||(!force&&matches(accepted,s)))return;
  const id=++serial,geometry=scene(s);pending={id,key:key(s),epoch};
  const own=pending;own.scene=geometry;status.status='rendering';status.quality=accepted?status.quality:'pending';
  worker.postMessage({kind:'render',id,identity:{id,key:own.key,epoch},scene:geometry});
  clearTimeout(deadline);deadline=setTimeout(()=>{if(pending?.id===id)failed(new Error('Moon worker refinement deadline exceeded'));},240000);
 }
 function offlineTransport(w){
  let at=0,seen=-1;
  window.SalahMoonAssetChunk=(name,index,data,last)=>{
   if(worker!==w||disposed)return;const expected=MOON_OFFLINE_CHUNKS[at];
   if(!expected||name!==expected.name||index!==expected.index||last!==expected.last||typeof data!=='string'){failed(new Error('Offline Moon transport identity'));return;}
   seen=at;w.postMessage({kind:'asset-chunk',name,index,data,last});
  };
  const next=()=>{
   if(worker!==w||disposed)return;
   if(chunkScript){chunkScript.remove();chunkScript=null;}
   if(at>=MOON_OFFLINE_CHUNKS.length)return;
   const spec=MOON_OFFLINE_CHUNKS[at];
   if(window.__SALAH_MOON_EMBEDDED__){
    const node=document.getElementById('moon-embedded-'+at);
    if(!node){failed(new Error('Embedded Moon payload missing'));return;}
    window.SalahMoonAssetChunk(spec.name,spec.index,node.textContent.trim(),spec.last);
    // Retain inert source payloads: a terminal worker failure must be retryable.
    // They already belong to the self-contained document, not an additional copy.
    at++;setTimeout(next,0);return;
   }
   const el=document.createElement('script');chunkScript=el;
   el.src=new URL(spec.path,base).href;el.async=true;el.onerror=()=>failed(new Error('Offline Moon asset script unavailable'));
   el.onload=()=>{if(worker!==w)return;if(seen!==at){failed(new Error('Offline Moon script omitted its payload'));return;}at++;setTimeout(next,0);};document.head.append(el);
  };next();
 }
 function start(){
  if(disposed)return;ready=false;lastError=null;status.status='loading';
  try{
   url=URL.createObjectURL(new Blob([MOON_WORKER_SOURCE],{type:'text/javascript'}));const w=new Worker(url);worker=w;
   w.onerror=e=>{if(worker===w)failed(new Error(e.message||'Moon worker error'));};
   w.onmessageerror=()=>{if(worker===w)failed(new Error('Moon worker message decode'));};
   w.onmessage=e=>{
    if(worker!==w||disposed)return;try{const m=e.data;
    if(!m||typeof m!=='object')throw new Error('Moon message contract');
    if(m.kind==='ready'){clearTimeout(deadline);deadline=null;ready=true;status.status='ready-for-scene';poll();return;}
    if(m.kind==='boot-error'){failed(new Error(m.error));return;}
    if(!pending||m.id!==pending.id||!matches(pending,capture())){status.rejected++;return;}
    if(m.kind==='progress'){status.progress={stage:m.stage,row:m.row,total:m.total,sourceSamples:m.sourceSamples,selected:m.selected};return;}
    if(m.kind==='error'){failed(new Error(m.error));return;}
    const expected={id:pending.id,key:pending.key,epoch:pending.epoch};
    if(!['preview','result'].includes(m.kind)||JSON.stringify(m.identity)!==JSON.stringify(expected)){status.rejected++;return;}
    if(!(m.rgba instanceof Uint8ClampedArray)||m.rgba.length!==m.width*m.height*4||m.width!==m.height||m.width!==pending.scene.outSize||m.surfaceExtent!==pending.scene.extent||m.width<8||m.width>768||m.diagnostics?.kernel!=='metric-radial-terrain-wasm-mb1'||JSON.stringify(m.scene)!==JSON.stringify(pending.scene)){
     failed(new Error('Moon result contract'));return;
    }
    if(!(m.surfaceLinear instanceof Float32Array)||!(m.surfaceCoverage instanceof Float32Array)||m.surfaceSize!==pending.scene.size||m.surfaceLinear.length!==m.surfaceSize*m.surfaceSize*3||m.surfaceCoverage.length!==m.surfaceSize*m.surfaceSize){failed(new Error('Moon linear surface shape'));return;}
    if(!(m.calendarLinear instanceof Float32Array)||m.calendarLinear.length!==m.surfaceLinear.length||!(m.calendarRgba instanceof Uint8ClampedArray)||m.calendarRgba.length!==m.rgba.length){failed(new Error('Calendar presentation contract'));return;}
    window.SalahMoonDetail?.adopt({linear:m.surfaceLinear,calendarLinear:m.calendarLinear,coverage:m.surfaceCoverage,size:m.surfaceSize,extent:m.surfaceExtent,identity:m.physicalIdentity});
    // Validate/adopt the whole surface before advancing its publication state.
    canvas.width=m.width;canvas.height=m.height;upperBytes=m.rgba;calendarBytes=m.calendarRgba;textureUp=null;
    accepted={id:pending.id,key:pending.key,epoch:pending.epoch,scene:m.scene,physicalIdentity:m.physicalIdentity,profileIdentity:m.profileIdentity};
    status.status=m.kind==='preview'?'refining':'ready';status.quality=m.diagnostics.quality?.status??'unqualified';status.legacyFallback=false;status.renders++;status.last=m.diagnostics;status.phase=m.scene.fraction;

    if(m.kind==='result'){clearTimeout(deadline);deadline=null;pending=null;}
    syncTexture(capture());window.SalahRealSky?.compose();
    }catch(error){failed(error);}
   };
   const offline=!!window.__SALAH_MOON_OFFLINE__;
   w.postMessage({kind:'boot',base,offline});if(offline)offlineTransport(w);
   clearTimeout(deadline);deadline=setTimeout(()=>{if(worker===w&&!ready)failed(new Error('Moon asset startup deadline exceeded'));},120000);
  }catch(e){failed(e);}
 }
 function admitReference(s){
  if(!s||s.mode!=='physical-reference'||!Array.isArray(s.basis)||s.basis.length!==9||!Array.isArray(s.sun)||s.sun.length!==3||!Array.isArray(s.earth)||s.earth.length!==3||![...s.basis,...s.sun,...s.earth,s.distance,s.extent].every(Number.isFinite))throw new RangeError('Explicit finite Moon-fixed geometry required');
  if(Math.abs(Math.hypot(...s.sun)-1)>1e-10||!Number.isInteger(s.size)||s.size<8||s.size>768||!Number.isInteger(s.outSize)||s.outSize<8||s.outSize>768||s.distance<1753||Math.hypot(...s.earth)<8124)throw new RangeError('Moon geometry domain');
  const b=[s.basis.slice(0,3),s.basis.slice(3,6),s.basis.slice(6)];for(let i=0;i<3;i++)for(let j=0;j<3;j++)if(Math.abs(b[i].reduce((a,x,k)=>a+x*b[j][k],0)-(i===j?1:0))>1e-10)throw new RangeError('Moon basis');
  return structuredClone(s);
 }
 const visibility=()=>{if(document.hidden){clear('document hidden');status.status='paused';}else{clock=null;poll();}};
 document.addEventListener('visibilitychange',visibility);
 window.SalahMoonRuntime={
  request(){poll();return matches(accepted,capture());},
  surface(){const s=capture();if(!matches(accepted,s))return null;syncTexture(s);return canvas;},
  get presentationUp(){return profileMode==='reference'?1:Math.max(0,Math.min(1,capture()?.up??1));},
  get detailEnabled(){return matches(accepted,capture())&&!!window.SalahMoonDetail?.available;},
  invalidate(reason='native invalidation'){clear(reason);},refresh(){poll(true);},
  setProfile(mode){if(!['calendar','reference'].includes(mode))throw new RangeError('Moon profile');if(mode===profileMode)return;profileMode=mode;clear('profile changed');poll();},
  setReferenceScene(value){referenceScene=value===null?null:admitReference(value);clear('reference view changed');poll();},
  retry(){if(disposed||worker||retryCount>=3)return false;retryCount++;start();return true;},
  get state(){const s=capture(),target=(accepted??pending)?.scene;return structuredClone({...status,epoch,pending:!!pending,accepted:accepted?{identity:accepted.physicalIdentity,profile:accepted.profileIdentity,scene:accepted.scene}:null,retryCount,workerAlive:!!worker,currentNativeFraction:s?.fraction,phasePrecision:s?{diameterDevicePixels:s.phaseDiameter,quantumRadians:s.phaseQuantum,bucket:Math.round(Math.acos(2*s.fraction-1)/s.phaseQuantum),maximumPositionErrorDevicePixels:PHASE_POSITION_BUDGET,targetPositionErrorBound:target?.mode==='calendar-canonical'?s.phaseDiameter/2*Math.abs(Math.acos(2*target.fraction-1)-Math.acos(2*s.fraction-1)):null}:null,maximumCanonicalPhasePositionErrorAtD416:.0416,calendarProxyWeight:1-(s?.up??1),calendarProxy:'native below-horizon display token .020×material; not physical irradiance'});},
  dispose(){if(disposed)return;clear('disposed');disposed=true;clearInterval(timer);clearTimeout(deadline);document.removeEventListener('visibilitychange',visibility);closeWorker();window.SalahMoonDetail?.dispose();status.status='disposed';}
 };
 timer=setInterval(()=>poll(),250);start();
})();
