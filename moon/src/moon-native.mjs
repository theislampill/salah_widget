/* The existing native host alone owns phase, UTC, observer intent and generation.
 * A bounded V5 receiver tier supplies the first scene; full terrain stays in its
 * worker. Initial availability grants no authority to stale or reference views. */
(function(){'use strict';
 // A predecessor runtime here has already retired (moon-install-guard.mjs refuses
 // replay over a live one) and released its own captured detail. This runtime
 // owns exactly the detail it creates; the global slot is a registry pointer.
 window.SalahMoonRuntime?.dispose();
 const script=document.currentScript;
 // A fully embedded document has no relative assets, including in an opaque iframe.
 const base=window.__SALAH_MOON_EMBEDDED__?(document.baseURI||'about:blank'):new URL(window.__SALAH_MOON_INLINE__?'moon/':'.',script?.src||document.baseURI).href;
 const canvas=document.createElement('canvas');canvas.width=300;canvas.height=300;
 let worker=null,url=null,disposed=false,ready=false,pending=null,accepted=null,serial=0,epoch=0,retryCount=0,clock=null,referenceScene=null,profileMode='calendar';
 let timer=null,deadline=null,startFrame=null,lastError=null,stopOffline=null,upperBytes=null,calendarBytes=null,textureUp=null,waitingPreview=null;
 let initialHeadEligible=true,bootCache='force-cache',adoptions=0,publishedToken=null;
 // R0033 M1: the one recovery owner. Only the runtime starts workers (start()); at most
 // three automatic attempts per page lifetime at 30 s, 2 min, 10 min after each failure,
 // never while hidden, disposed, without a worker source or with a live worker. The QA
 // drivers' explicit retry() keeps its own separate bound. Deterministic classes
 // (contract, transport identity) never retry. The budget is not restored by success.
 const RECOVERY_BACKOFF=[30000,120000,600000],RETRYABLE=new Set(['boot','crash','deadline','render','transport','start']);
 const recovery={state:'idle',attempts:0,limit:RECOVERY_BACKOFF.length,nextAt:null,lastClass:null,outcome:null};
 // R0033 M2: the initial-tier error RECORD (status.initialError) is separate from its
 // eligibility. A missing receiver or decode failure is permanent; a render throw is
 // re-attempted at most once per eligibility event (a new epoch, or 60 s), three throws
 // per page at most, never per frame.
 const initialRetry={count:0,notBefore:0,epoch:-1,state:window.SalahMoonInitialError!=null||!window.SalahMoonInitial?'permanent':'idle'};
 const status={status:'loading',backend:'metric-terrain-wasm-mb1',renders:0,rejected:0,cancelled:0,errors:[],legacyFallback:false,quality:'pending',visibleSource:'awaiting-terrain',initialError:window.SalahMoonInitialError??null};
 const profile=()=>profileMode==='reference'?{...MOON_DEFAULT_PROFILE,profile_id:'unboosted-v5-01',mode:'reference',lift:0}:{...MOON_DEFAULT_PROFILE};
 function capture(withGeometry=true){
  const h=window.SalahMoonHost;if(!h)return null;let s;try{s=h.capture();}catch{return null;}
  // Native observation can initialize the explicit clock. Preserve it even
  // when an empty surface query has no candidate needing geometric validation.
  if(!withGeometry)return null;
  if(!s||typeof s.sceneIdentity!=='string'||!Number.isSafeInteger(s.generation)||s.generation<0||!Number.isFinite(s.utcMs)||!Number.isFinite(s.fraction)||s.fraction<0||s.fraction>1||typeof s.waxing!=='boolean'||(s.phaseDirection!==undefined&&![-1,0,1].includes(s.phaseDirection))||!Number.isFinite(s.up)||!Number.isFinite(s.dpr))return null;
  // The image rectangle encloses the lunar disc. Round up, so subpixel layout
  // noise cannot understate the bound; translation never changes this identity.
  const rect=document.querySelector('.mphoto')?.getBoundingClientRect();
  const phaseDiameter=rect&&rect.width>0&&rect.height>0?Math.ceil(Math.max(rect.width,rect.height)*s.dpr):416;
  const maximumPhaseDiameter=Math.ceil(phaseDiameter*Math.max(1,Number.isFinite(s.maximumPresentationRatio)?s.maximumPresentationRatio:1));
  return {...s,phaseDiameter,maximumPhaseDiameter,phaseQuantum:phaseQuantum(phaseDiameter),physicalFraction:canonicalFraction(s.fraction,phaseDiameter),profileMode,referenceIdentity:referenceScene?JSON.stringify(referenceScene):null};
 }
 const key=s=>JSON.stringify([s.generation,s.sceneIdentity,s.physicalFraction,s.waxing,s.dpr,s.profileMode,s.referenceIdentity,s.phaseDiameter]);
 // Geometry reuse and target authority are different predicates. A CSS-sized
 // footprint crossing an integer or a phase bucket is not a location/seek epoch.
 // Every read still proves the ORIGINAL .0416-device-pixel displacement bound.
 const scope=s=>JSON.stringify([s.generation,s.sceneIdentity,s.waxing,s.dpr,s.profileMode,s.referenceIdentity]);
 // R0041: signed by the RECORD's own lead direction (the motion it was created ahead of); unsigned when centred (0).
 const phaseDrift=(record,s)=>record?.scene?.mode==='calendar-canonical'?(d=>{const x=s.phaseDiameter/2*(Math.acos(2*s.fraction-1)-Math.acos(2*record.scene.fraction-1));return d===0?Math.abs(x):-d*x;})(record.scene.leadDirection??(s.waxing?1:-1)):0;
 const phaseError=(record,s)=>Math.abs(phaseDrift(record,s));
 function syncTexture(s){
  if(!accepted||!upperBytes||!s)return false;const up=profileMode==='reference'?1:Math.max(0,Math.min(1,s.up));
  // This backing surface is immediately read by the native material sampler
  // and PNG publication. Keep its identical bytes in CPU-backed storage.
  if(textureUp===up)return false;textureUp=up;
  // R0041 (review finding 5): the host may keep the presented vector texture until its replacement decodes ONLY when
  // both are the SAME adopted record (a re-blend of the current surface for a new altitude weight), never across
  // records: a withdrawn or expired predecessor is replaced at once, so no expired surface is retained.
  // R0033 M7: a blend/ImageData/publication throw withdraws this presentation and is
  // recorded; it never escapes request()/surface() and leaves nothing presentable.
  try{const rgba=blendCalendarBytes(upperBytes,calendarBytes,up);canvas.getContext('2d',{willReadFrequently:true}).putImageData(new ImageData(rgba,canvas.width,canvas.height),0,0);const same=publishedToken!==null&&publishedToken===accepted.token;publishedToken=accepted.token;window.SalahMoonHost?.publish(canvas,same);}
  catch(error){note(error);fallback('texture publication failure');return false;}
  return true;
 }
 function note(error){const message=String(error?.message??error);if(status.errors.at(-1)!==message)status.errors.push(message);status.errors=status.errors.slice(-8);return message;}
 const clockDiscontinuous=(s,now=performance.now())=>!!clock&&Math.abs((s.utcMs-clock.utcMs)-(now-clock.now)*clock.rate)>1000;
 // Check at publication/read time as well as polling: a seek cannot slip an
 // otherwise identical result through the interval before the next host poll.
 const sameScope=(record,s)=>!!record&&!!s&&!s.paused&&!clockDiscontinuous(s)&&record.epoch===epoch&&record.scope===scope(s);
 const matches=(record,s)=>sameScope(record,s)&&phaseError(record,s)<=PHASE_POSITION_BUDGET;
 // R0033 M4 presence predicate (named so the diagnostic observation reuses it; no second predicate).
 const presentableAt=s=>!!s&&(matches(accepted,s)||(!!waitingPreview&&matches(waitingPreview.record,s)));
 function fallback(reason){accepted=null;upperBytes=null;calendarBytes=null;textureUp=null;status.legacyFallback=false;status.quality='pending';status.visibleSource='awaiting-terrain';status.reason=reason;try{window.SalahMoonHost?.fallback();}catch(error){note(error);}detail.clear();}
 function revokeInitialHead(){initialHeadEligible=false;if(window.SalahFirstPaint?.moon)window.SalahFirstPaint.moon.result=null;}
 // R0041 presenter: withdraw the record's AUTHORITY without touching what is presented (detail canvas, reveal
 // classes). Used only where a successor for the SAME identity is adopted in this same task.
 function withdrawAuthority(reason){accepted=null;upperBytes=null;calendarBytes=null;textureUp=null;status.legacyFallback=false;status.quality='pending';status.visibleSource='awaiting-terrain';status.reason=reason;}
 function clear(reason,initialDocument=false){
  if(!initialDocument)revokeInitialHead();
  const presented=accepted?.scope??null;
  epoch++;serial++;pending=null;waitingPreview=null;clearTimeout(deadline);deadline=null;try{worker?.postMessage({kind:'cancel'});}catch(error){note(error);/* A crashed worker cannot veto withdrawal. */}status.cancelled++;
  // R0041 presenter guarantee: when the identity is unchanged (same scope, continuous clock, visible, unpaused), the
  // successor tier for the current scene is adopted and composed in this task BEFORE anything presented is withdrawn;
  // the host is then notified as before. A genuine identity, clock, epoch-source or visibility change keeps the
  // truthful withdrawal below (never retain an invalid Moon).
  if(presented&&!disposed&&!document.hidden){
   const s=capture();
   if(s&&!s.paused&&scope(s)===presented&&!clockDiscontinuous(s)){
    withdrawAuthority(reason);initialPresentation(s,performance.now());
    if(accepted){try{window.SalahMoonHost?.fallback();}catch(error){note(error);}return;}
   }
  }
  fallback(reason);
 }
 function closeWorker(){
  stopOffline?.();stopOffline=null;
  ready=false;worker?.terminate();worker=null;if(url)URL.revokeObjectURL(url);url=null;
 }
 function failed(error,cls='crash'){
  if(disposed)return;
  revokeInitialHead();
  // Failure revokes the job/worker, not a previously validated surface's native
  // authority. Retention still checks its original scope and geometric budget
  // on every read; a target change or expired geometry cannot use this path.
  serial++;pending=null;waitingPreview=null;clearTimeout(deadline);deadline=null;
  if(!matches(accepted,capture()))fallback('worker failure');
  else status.retainedReason='replacement worker failure; original current surface';
  status.status='unavailable';lastError=note(error);closeWorker();
  // Any later attempt after a failure revalidates cached assets (DG-3): a cached
  // error or stale-identity body must not make recovery impossible.
  bootCache='no-cache';schedule(cls);
 }
 function schedule(cls){
  if(recovery.state==='scheduled')return;
  recovery.lastClass=cls;recovery.outcome=null;
  if(!RETRYABLE.has(cls)||recovery.attempts>=recovery.limit){recovery.state='exhausted';recovery.nextAt=null;return;}
  recovery.state='scheduled';recovery.nextAt=performance.now()+RECOVERY_BACKOFF[recovery.attempts];
 }
 // Driven by the existing 4 Hz poll and the visible transition: no extra timer resource.
 function recoverIfDue(now){
  if(recovery.state!=='scheduled'||disposed||worker||document.hidden||now<recovery.nextAt||typeof MOON_WORKER_SOURCE!=='string')return;
  recovery.attempts++;start();
 }
 // R0041: the leading edge follows the PHASE-DIRECTION authority; the lit limb (Sun y sign, scene.waxing) stays on
 // waxing. nativeCalendarMoonScene (accepted V5 source) is called with the lead's sense, then the lit side is restored;
 // the scene records leadDirection so phaseDrift signs by the record's own lead. Without a direction (override, no
 // location, dead band) the historical scene is returned unchanged.
 function directedCalendarScene(s,p){
  const d=s.phaseDirection;if((s.timeScale??1)<=0||(d!==1&&d!==-1))return nativeCalendarMoonScene(s,p);
  const out=nativeCalendarMoonScene({...s,waxing:d===1},p);out.sun=[out.sun[0],(s.waxing?1:-1)*Math.abs(out.sun[1]),out.sun[2]];out.waxing=s.waxing;out.leadDirection=d;return out;
 }
 function scene(s){
  if(referenceScene)return {...structuredClone(referenceScene),profile:profile()};
  return directedCalendarScene(s,profile());
 }
 function adopt(m,record){
  const began=performance.now();
  detail.adopt({linear:m.surfaceLinear,calendarLinear:m.calendarLinear,coverage:m.surfaceCoverage,size:m.surfaceSize,extent:m.surfaceExtent,identity:m.physicalIdentity});
  const prefixMs=performance.now()-began;
  canvas.width=m.width;canvas.height=m.height;upperBytes=m.rgba;calendarBytes=m.calendarRgba;textureUp=null;
  accepted={token:++adoptions,id:record.id,key:record.key,scope:record.scope,epoch:record.epoch,scene:m.scene,physicalIdentity:m.physicalIdentity,profileIdentity:m.profileIdentity,initial:m.kind==='initial'};
  status.quality=m.diagnostics.quality.status;status.legacyFallback=false;status.visibleSource=m.kind==='result'?'refined-terrain':m.kind==='initial'?'initial-v5':'terrain-preview';status.last=m.diagnostics;status.phase=m.scene.fraction;
  syncTexture(capture());status.lastAdoption={at:began,prefixMs,totalMs:performance.now()-began,source:status.visibleSource};
 }
 function presentation(s){
  if(matches(accepted,s)&&!(accepted.initial&&waitingPreview&&matches(waitingPreview.record,s)))return true;
  // A current full-spatial V5 terrain preview may bridge computation. It uses
  // identical DEM/material/profile/coverage, never the legacy normal-map image,
  // and is explicitly NOT labelled a final angular refinement.
  if(waitingPreview&&matches(waitingPreview.record,s)){const p=waitingPreview;waitingPreview=null;
   try{adopt(p.message,p.record);}catch(error){note(error);fallback('presentation adoption failure');return false;}
   return !!accepted;}
  return false;
 }
 function takeInitialHead(s,now){
  const first=window.SalahFirstPaint,head=first?.moon,result=head?.result,eligible=initialHeadEligible;
  revokeInitialHead();
  if(!eligible||!head?.visible||!result||result.kind!=='initial'||s.generation!==0||s.timeScale!==1||s.paused||profileMode!=='calendar'||referenceScene)return null;
  const original={...head.capture,profileMode:'calendar',referenceIdentity:null};
  // This is a one-time lifecycle handoff, not a cache keyed by matching end
  // points. Every real invalidation irrevocably revokes it, including A-B-A.
  // Preserve the original scene and its leading-edge .0416-device-pixel bound.
  if(original.generation!==0||original.timeScale!==1||original.paused||scope(original)!==scope(s)||
   !Number.isFinite(first.capturedAt)||first.capturedAt>now||!Number.isFinite(original.utcMs)||
   Math.abs((s.utcMs-original.utcMs)-(now-first.capturedAt))>1000||
   result.diagnostics?.receiverIdentity!==window.SalahMoonInitial.identity?.sha256||
   JSON.stringify(result.scene.profile)!==JSON.stringify(profile()))return null;
  const record={id:'initial-head',key:key(original),scope:scope(original),epoch,scene:result.scene};
  return matches(record,s)?{result,record,capturedAt:first.capturedAt}:null;
 }
 function initialPresentation(s,capturedAt){
  if(presentation(s)||s.presentationReady===false||s.initialWarranted===false||profileMode!=='calendar'||referenceScene||!window.SalahMoonInitial||!initialEligible(capturedAt))return;
  try{
   const head=takeInitialHead(s,capturedAt),geometry=head?.result.scene??scene(s);
   const record=head?.record??{id:'initial',key:key(s),scope:scope(s),epoch,scene:geometry};
   const result=head?.result??window.SalahMoonInitial.render(geometry);
   // Calculation cannot rebind an old scene. Re-read its authority and original
   // phase bound before publication, including accelerated native time.
   if(matches(record,capture())){
    adopt(result,record);if(!accepted)return;
    // R0041 presenter: the successor is composed in this task (as the preview and result paths do), so the
    // device-resolution disc never waits for the sky's next compose after any withdrawal or resume. A host that is
    // composing right now (presentForCompose) is not re-entered: its own compose follows this adoption. While the
    // refined sky has no frame, the published atmospheric preview owns the sky (its ready class hides the SVG Moon), so
    // it re-composes now; otherwise its sky (stars) would show through the slot until its next paint (R0041 identity
    // route, witnessed in all three engines).
    if(!hostComposing){
     try{window.SalahRealSky?.compose();}catch(error){note(error);}
     try{const c=document.querySelector('.c');if(c&&c.classList.contains('real-sky-preview-ready')&&!c.classList.contains('real-sky-composed'))window.SalahSkyPreview?.update?.();}catch(error){note(error);}
    }
    // Retain stage timing for later diagnostics; no polling is needed during
    // the first presented frames. Publication is distinct from visible pixels.
    status.firstInitial??={capturedAt,publishedAt:performance.now(),generation:s.generation,sceneIdentity:s.sceneIdentity,renderMs:head?0:result.diagnostics.totalMs,headHandoff:!!head,headCapturedAt:head?.capturedAt??null,headRenderMs:head?result.diagnostics.totalMs:null};
   }else status.initialRejected=(status.initialRejected??0)+1;
  }catch(error){
   status.initialError=String(error.message??error);initialRetry.count++;initialRetry.epoch=epoch;
   initialRetry.notBefore=capturedAt+60000;initialRetry.state=initialRetry.count>=3?'exhausted':'waiting';
  }
 }
 // R0041 resume (owner decision 1, issue 143): every sky host composes the Moon only through this runtime's handle.
 // Before a host composes a frame, the presenter brings its presentation current with the same poll the 4 Hz timer
 // runs, so a sky frame published on resume (or after any withdrawal) carries the current successor, never an empty
 // slot. It acts only when nothing is presentable, so a steady presented state is untouched. Hidden: nothing (the
 // accepted hide withdrawal, ISM-MOON-019, is unchanged); the pre-hide surface was withdrawn and is never retained.
 let hostComposing=false;
 function presentForCompose(){
  if(disposed||hostComposing||document.hidden||presentableAt(capture(!!(accepted||waitingPreview))))return;
  hostComposing=true;try{poll();}catch(error){note(error);}finally{hostComposing=false;}
 }
 function initialEligible(now){
  if(initialRetry.state==='permanent'||initialRetry.state==='exhausted')return false;
  return initialRetry.count===0||initialRetry.epoch!==epoch||now>=initialRetry.notBefore;
 }
 function poll(force=false){
  if(disposed)return;const s=capture(),now=performance.now();recoverIfDue(now);
  if(!s){revokeInitialHead();if(accepted||pending)clear('invalid native lunar scene');clock=null;status.status='waiting-native';return;}
  const jump=clockDiscontinuous(s,now);
  if(jump)clear('native clock discontinuity');clock={utcMs:s.utcMs,now,rate:s.timeScale??1};
  if(s.paused){revokeInitialHead();if(pending||accepted)clear('native paused');status.status='paused';return;}
  if((accepted&&!sameScope(accepted,s))||(pending&&!sameScope(pending,s)))clear('native lunar target changed');
  if(pending&&!matches(pending,s)){
   serial++;pending=null;waitingPreview=null;clearTimeout(deadline);deadline=null;
   try{worker?.postMessage({kind:'cancel'});}catch(error){note(error);}status.cancelled++;status.reason='lunar geometry exceeded unchanged display bound';
  }
  // R0041 presenter guarantee (same-scope expiry): a presented Moon is not withdrawn before its successor is presented.
  // The expired record leaves authority at once, but the presented layers (detail canvas, reveal classes) are kept
  // until the successor tier is adopted in this same task and a compose is requested; only when no successor can be
  // adopted does the historical full fallback (detail hidden, host fallback) run. Scope/epoch/clock changes never get
  // here: they already ran clear() above and keep their truthful withdrawal.
  if(accepted&&!presentation(s)){
   withdrawAuthority('lunar geometry exceeded unchanged display bound');
   initialPresentation(s,now);
   if(!accepted)fallback('lunar geometry exceeded unchanged display bound');
  }else initialPresentation(s,now);
  // A dead worker never reads 'paused' in a visible document (the hide path set it).
  if(!ready||!worker){status.status=lastError?'unavailable':typeof MOON_WORKER_SOURCE==='string'?'loading':'waiting-refinement-source';return;}
  if(matches(accepted,s))syncTexture(s);
  if(matches(pending,s)||(!force&&matches(accepted,s)&&!accepted.initial&&phaseDrift(accepted,s)<PHASE_POSITION_BUDGET/4))return;
  const id=++serial,geometry=scene(s);pending={id,key:key(s),scope:scope(s),epoch};
  const own=pending;own.scene=geometry;status.status='rendering';status.quality=accepted?status.quality:'pending';
  try{worker.postMessage({kind:'render',id,identity:{id,key:own.key,epoch},scene:geometry});}catch(error){failed(error,'start');return;}
  clearTimeout(deadline);deadline=setTimeout(()=>{if(pending?.id===id)failed(new Error('Moon worker refinement deadline exceeded'),'deadline');},240000);
 }
 function offlineTransport(w){
  let at=0,seen=-1,chunkScript=null,nextTimer=null;
  const releaseScript=()=>{
   if(!chunkScript)return;
   chunkScript.onload=null;chunkScript.onerror=null;delete chunkScript.SalahMoonAssetChunk;
   chunkScript.remove();chunkScript=null;
  };
  const accept=(name,index,data,last)=>{
   if(worker!==w||disposed)return;const expected=MOON_OFFLINE_CHUNKS[at];
   if(seen===at||!expected||name!==expected.name||index!==expected.index||last!==expected.last||typeof data!=='string'){failed(new Error('Offline Moon transport identity'),'transport-identity');return;}
   seen=at;w.postMessage({kind:'asset-chunk',name,index,data,last});
  };
  const schedule=()=>{nextTimer=setTimeout(()=>{nextTimer=null;next();},0);};
  const next=()=>{
   if(worker!==w||disposed)return;
   document.removeEventListener('DOMContentLoaded',next);
   if(at>=MOON_OFFLINE_CHUNKS.length){stopOffline=null;return;}
   const spec=MOON_OFFLINE_CHUNKS[at];
   if(window.__SALAH_MOON_EMBEDDED__){
    const node=document.getElementById('moon-embedded-'+at);
    if(!node){failed(new Error('Embedded Moon payload missing'),'transport-identity');return;}
    accept(spec.name,spec.index,node.textContent.trim(),spec.last);
    // Retain inert source payloads: a terminal worker failure must be retryable.
    // They already belong to the self-contained document, not an additional copy.
    if(worker===w&&!disposed){at++;schedule();}return;
   }
   const el=document.createElement('script');chunkScript=el;
   // A removed asynchronous script can still execute. Its payload belongs to
   // this exact script and worker, never a global callback replaced by retry.
   el.SalahMoonAssetChunk=(...args)=>{if(worker===w&&!disposed&&chunkScript===el&&document.currentScript===el)accept(...args);};
   el.src=new URL(spec.path,base).href;el.async=true;
   el.onerror=()=>{if(worker===w&&!disposed&&chunkScript===el)failed(new Error('Offline Moon asset script unavailable'),'transport');};
   el.onload=()=>{if(worker!==w||disposed||chunkScript!==el)return;if(seen!==at){failed(new Error('Offline Moon script omitted its payload'),'transport-identity');return;}releaseScript();at++;schedule();};document.head.append(el);
  };
  stopOffline=()=>{clearTimeout(nextTimer);nextTimer=null;document.removeEventListener('DOMContentLoaded',next);releaseScript();};
  if(window.__SALAH_MOON_EMBEDDED__&&document.readyState==='loading')document.addEventListener('DOMContentLoaded',next,{once:true});else next();
 }
 function start(){
  if(startFrame!==null){cancelAnimationFrame(startFrame);startFrame=null;}
  if(disposed||worker)return;
  // The compact current surface is already usable. HTML delivery of the
  // independent refinement script cannot delay native settings/prayer boot.
  if(typeof MOON_WORKER_SOURCE!=='string'){status.status='waiting-refinement-source';return;}
  ready=false;lastError=null;status.status='loading';
  if(recovery.state==='scheduled'){recovery.state='idle';recovery.nextAt=null;}
  try{
   url=URL.createObjectURL(new Blob([MOON_WORKER_SOURCE],{type:'text/javascript'}));const w=new Worker(url);worker=w;
   w.onerror=e=>{if(worker===w)failed(new Error(e.message||'Moon worker error'),'crash');};
   w.onmessageerror=()=>{if(worker===w)failed(new Error('Moon worker message decode'),'crash');};
   w.onmessage=e=>{
    if(worker!==w||disposed)return;try{const m=e.data;
    if(!m||typeof m!=='object')throw new Error('Moon message contract');
    if(m.kind==='ready'){clearTimeout(deadline);deadline=null;ready=true;status.status='ready-for-scene';poll(!!accepted);return;}
    if(m.kind==='boot-error'){failed(new Error(m.error),'boot');return;}
    if(!pending||m.id!==pending.id||!matches(pending,capture())){status.rejected++;return;}
    if(m.kind==='progress'){status.progress={stage:m.stage,row:m.row,total:m.total,sourceSamples:m.sourceSamples,selected:m.selected};return;}
    if(m.kind==='error'){failed(new Error(m.error),'render');return;}
    const expected={id:pending.id,key:pending.key,epoch:pending.epoch};
    if(!['preview','result'].includes(m.kind)||JSON.stringify(m.identity)!==JSON.stringify(expected)){status.rejected++;return;}
    if(!(m.rgba instanceof Uint8ClampedArray)||m.rgba.length!==m.width*m.height*4||m.width!==m.height||m.width!==pending.scene.outSize||m.surfaceExtent!==pending.scene.extent||m.width<8||m.width>768||m.diagnostics?.kernel!=='metric-radial-terrain-wasm-mb1'||JSON.stringify(m.scene)!==JSON.stringify(pending.scene)){
     failed(new Error('Moon result contract'),'contract');return;
    }
    if(!(m.surfaceLinear instanceof Float32Array)||!(m.surfaceCoverage instanceof Float32Array)||m.surfaceSize!==pending.scene.size||m.surfaceLinear.length!==m.surfaceSize*m.surfaceSize*3||m.surfaceCoverage.length!==m.surfaceSize*m.surfaceSize){failed(new Error('Moon linear surface shape'),'contract');return;}
    if(!(m.calendarLinear instanceof Float32Array)||m.calendarLinear.length!==m.surfaceLinear.length||!(m.calendarRgba instanceof Uint8ClampedArray)||m.calendarRgba.length!==m.rgba.length){failed(new Error('Calendar presentation contract'),'contract');return;}
    // A deferred preview is still an admitted buffer. Validate it before it can
    // be queued for a later read-time handoff, not only when detail.adopt runs.
    for(let i=0;i<m.surfaceCoverage.length;i++){
     const a=m.surfaceCoverage[i];if(!Number.isFinite(a)||a<0||a>1)throw new Error('Moon surface coverage');
     for(let k=0;k<3;k++){
      const x=m.surfaceLinear[3*i+k],y=m.calendarLinear[3*i+k];
      if(!Number.isFinite(x)||!Number.isFinite(y)||x<0||y<0||x>a+1e-6||y>a+1e-6)throw new Error('Moon nonfinite/premultiplied surface');
     }
    }
    if(m.kind==='preview'){
     status.status='refining';status.progressQuality=m.diagnostics.quality;
     waitingPreview={message:m,record:{...pending}};
     presentation(capture());window.SalahMoonHost?.fallback();window.SalahRealSky?.compose();return;
    }
    if(m.diagnostics.quality?.status!=='empirical-adaptive'){failed(new Error('Moon refinement did not meet the admitted quality criterion'),'contract');return;}
    adopt(m,pending);status.status='ready';status.renders++;waitingPreview=null;if(recovery.lastClass)recovery.outcome='recovered';
    clearTimeout(deadline);deadline=null;pending=null;
    syncTexture(capture());window.SalahRealSky?.compose();
    }catch(error){failed(error,'contract');}
   };
   const offline=!!window.__SALAH_MOON_OFFLINE__;
   w.postMessage({kind:'boot',base,offline,workerSource:MOON_WORKER_SOURCE,cache:bootCache});if(offline)offlineTransport(w);
   clearTimeout(deadline);deadline=setTimeout(()=>{if(worker===w&&!ready)failed(new Error('Moon asset startup deadline exceeded'),'deadline');},120000);
  }catch(e){failed(e,'start');}
 }
 function admitReference(s){
  if(!s||s.mode!=='physical-reference'||!Array.isArray(s.basis)||s.basis.length!==9||!Array.isArray(s.sun)||s.sun.length!==3||!Array.isArray(s.earth)||s.earth.length!==3||![...s.basis,...s.sun,...s.earth,s.distance,s.extent].every(Number.isFinite))throw new RangeError('Explicit finite Moon-fixed geometry required');
  if(Math.abs(Math.hypot(...s.sun)-1)>1e-10||!Number.isInteger(s.size)||s.size<8||s.size>768||!Number.isInteger(s.outSize)||s.outSize<8||s.outSize>768||s.distance<1753||Math.hypot(...s.earth)<8124)throw new RangeError('Moon geometry domain');
  const b=[s.basis.slice(0,3),s.basis.slice(3,6),s.basis.slice(6)];for(let i=0;i<3;i++)for(let j=0;j<3;j++)if(Math.abs(b[i].reduce((a,x,k)=>a+x*b[j][k],0)-(i===j?1:0))>1e-10)throw new RangeError('Moon basis');
  return structuredClone(s);
 }
 // R0041 resume: the native host clears its own pause after this listener may already have run; one frame callback
 // (before the next paint) presents the successor when this turn could not, so the vector Moon is never left empty.
 const visibility=()=>{if(document.hidden){clear('document hidden');status.status='paused';}else{clock=null;poll();if(!accepted)requestAnimationFrame(()=>{if(!document.hidden)presentForCompose();});}};
 // The handle is idempotent and refuses adoption once retired (ES21-07). It is
 // a pass-through: moon-detail.mjs stays byte-identical because it is a pinned
 // initial-receiver source (tools/build_moon.py validate_initial_sources).
 // It is acquired at the registration boundary; a throw before the runtime is
 // complete releases exactly this wrapper's detail, slot, listener and timers.
 const detail=(inner=>{let retired=false;return {adopt(s){if(retired)return false;return inner.adopt(s);},clear(){inner.clear();},compose(frame,encode){if(!retired)presentForCompose();return inner.compose(frame,encode);},get available(){return !retired&&inner.available;},get state(){return inner.state;},dispose(){if(retired)return;retired=true;inner.dispose();}};})(startMoonDetail());
 let registered=null;
 try{
 document.addEventListener('visibilitychange',visibility);
 window.SalahMoonDetail=detail;
 window.SalahMoonRuntime={
  installWorkerSource(source){
   if(disposed)return false;
   if(typeof source!=='string'||source.length>MOON_WORKER_PIN.bytes)throw Error('Moon worker source identity');
   const bytes=new TextEncoder().encode(source);
   if(bytes.length!==MOON_WORKER_PIN.bytes||assetDigest(bytes)!==MOON_WORKER_PIN.sha256)throw Error('Moon worker source identity');
   if(MOON_WORKER_SOURCE===source)return true;
   MOON_WORKER_SOURCE=source;
   if(!worker&&startFrame===null)startFrame=requestAnimationFrame(()=>{startFrame=requestAnimationFrame(start);});
   return true;
  },
  request(){
   // A settled refined surface needs one fresh authority/footprint read, not
   // another poll followed by a duplicate capture on every native paint.
   // All startup, pending, refresh and invalidation paths retain full polling.
   if(status.status==='ready'&&status.visibleSource==='refined-terrain'&&!pending){
    const s=capture();
    if(matches(accepted,s)&&phaseDrift(accepted,s)<PHASE_POSITION_BUDGET/4){
     // Publishing calls the native host back; preserve the original read-time
     // decision after that work, including a clock jump during texture upload.
     return syncTexture(s)?presentation(capture()):!!accepted;
    }
   }
   poll();return presentation(capture());
  },
  surface(){const s=capture(!!(accepted||waitingPreview));if(!presentation(s))return null;syncTexture(s);return accepted?canvas:null;},
  // R0033 M4: the pure presence predicate. True iff presentation() would return true
  // (a matching accepted surface or a matching queued preview), computed from capture()
  // WITHOUT presentation(), adopt, syncTexture or publish. Native light eligibility
  // reads only this; diagnostics (R0036) may reuse it.
  get presentable(){if(disposed)return false;return presentableAt(capture(!!(accepted||waitingPreview)));},
  // R0036 I-D2: the side-effect-free diagnostic observation (qaState().moonTruth, the CP9 wrapper, smoke). It reuses
  // the presence predicate above and never calls presentation(), adopt, syncTexture or publish, so a reader cannot
  // advance a reveal. current = the accepted surface is presented now; wouldPresent = presentable (a matching queued
  // preview would be adopted by the next production read). surface is the backing canvas only when current, unsynced.
  // Geometry (and so layout) is read only when a candidate surface exists.
  observe(){const s=disposed?null:capture(!!(accepted||waitingPreview)),current=!!s&&matches(accepted,s),wouldPresent=!disposed&&presentableAt(s);
   return {accepted:!!accepted,waitingPreview:!!waitingPreview,current,wouldPresent,detailAvailable:wouldPresent&&!!detail.available,surface:current?canvas:null,state:snapshot(s,current)};},
  get presentationUp(){return profileMode==='reference'?1:Math.max(0,Math.min(1,capture()?.up??1));},
  get detailEnabled(){return presentation(capture())&&!!detail.available;},get disposed(){return disposed;},
  invalidate(reason='native invalidation',options){clear(reason,options?.initialDocument===true);},
  finishInitialDocument(){revokeInitialHead();},refresh(){poll(true);},
  setProfile(mode){if(!['calendar','reference'].includes(mode))throw new RangeError('Moon profile');if(mode===profileMode)return;profileMode=mode;clear('profile changed');poll();},
  setReferenceScene(value){referenceScene=value===null?null:admitReference(value);clear('reference view changed');poll();},
  retry(){if(disposed||worker||typeof MOON_WORKER_SOURCE!=='string'||retryCount>=3)return false;retryCount++;start();return true;},
  get state(){const s=capture(),current=presentation(s);return snapshot(s,current);},
  dispose(){if(disposed)return;clear('disposed');disposed=true;recovery.state='idle';recovery.nextAt=null;clearInterval(timer);clearTimeout(deadline);if(startFrame!==null)cancelAnimationFrame(startFrame);startFrame=null;document.removeEventListener('visibilitychange',visibility);closeWorker();if(window.SalahMoonDetail===detail)window.SalahMoonDetail=null;detail.dispose();status.status='disposed';}
 };
 function snapshot(s,current){const target=(accepted??pending)?.scene;return structuredClone({...status,quality:current?status.quality:'pending',visibleSource:current?status.visibleSource:'awaiting-terrain',current,epoch,generation:s?.generation,pending:!!pending,accepted:accepted?{identity:accepted.physicalIdentity,profile:accepted.profileIdentity,scene:accepted.scene}:null,retryCount,workerAlive:!!worker,recovery:{...recovery},initialRetry:{...initialRetry},initialEligible:!!window.SalahMoonInitial&&initialEligible(performance.now()),currentNativeFraction:s?.fraction,phasePrecision:s?{diameterDevicePixels:s.phaseDiameter,quantumRadians:s.phaseQuantum,bucket:Math.round(Math.acos(2*s.fraction-1)/s.phaseQuantum),maximumPositionErrorDevicePixels:PHASE_POSITION_BUDGET,refreshThresholdDevicePixels:PHASE_POSITION_BUDGET/4,maximumNativePresentationDiameter:s.maximumPhaseDiameter,signedPositionDrift:accepted?phaseDrift(accepted,s):null,targetPositionErrorBound:target?.mode==='calendar-canonical'?s.phaseDiameter/2*Math.abs(Math.acos(2*target.fraction-1)-Math.acos(2*s.fraction-1)):null}:null,maximumCanonicalPhasePositionErrorAtD416:.0416,calendarProxyWeight:1-(s?.up??1),calendarProxy:'refined phase/relief scaled to at most the former .020×material mean luminance; zero physical moonlight'});}
 registered=window.SalahMoonRuntime;
 timer=setInterval(()=>poll(),250);
 // Full asset/decode/row preparation must not compete with the synchronous
 // first surface. Give its already-published scene a browser paint opportunity;
 // explicit retry and disposal revoke this deferred start. No readiness gate.
 startFrame=requestAnimationFrame(()=>{startFrame=requestAnimationFrame(start);});
 }catch(error){
  // construction-failed -> cleaned: the half-built runtime reports disposed and
  // its registry slot clears while it still holds this runtime.
  disposed=true;recovery.state='idle';recovery.nextAt=null;clearInterval(timer);if(startFrame!==null)cancelAnimationFrame(startFrame);startFrame=null;
  document.removeEventListener('visibilitychange',visibility);closeWorker();
  if(window.SalahMoonDetail===detail)window.SalahMoonDetail=null;detail.dispose();
  status.status='disposed';if(registered&&window.SalahMoonRuntime===registered)window.SalahMoonRuntime=null;
  throw error;
 }
})();
