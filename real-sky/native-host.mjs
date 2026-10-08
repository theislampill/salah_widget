import {nativeJob,nativeIdentity,nativeResultCurrent,nativeCalendarComposite,nativeDiscMask} from './native-contract.mjs';
import {requireNativeWorker} from './native-worker-policy.mjs';
import {ReferenceRenderClient} from './core/src/reference-worker-client.mjs';
import {NativeSkyLifecycle} from './native-lifecycle.mjs';
import {encodeNativeFrame} from './native-encoding.mjs';
import {nativeAtmosphereFields,nativeSkyPresentation} from './native-preview.mjs';
import {NativeForegroundCapture,nativeForeground,nativeCalendarRegion,nativeForegroundRows,sameNativePresentation} from './native-composition.mjs';
/** DOM ownership adapter; native PBR/calendar/weather remain native source code. */
export function startNativeSky(pack,workerSource,physical){
 window.SalahRealSky?.dispose();
 const host=window.SalahNativeSkyHost,card=document.querySelector('.c');if(!host||!card)throw new Error('Native host/card missing');
 const canvas=document.createElement('canvas');canvas.className='real-sky-canvas';canvas.width=325;canvas.height=530;canvas.setAttribute('aria-hidden','true');card.prepend(canvas);
 const ctx=canvas.getContext('2d',{alpha:false});if(!ctx)throw new Error('Canvas 2D unavailable');
 const badge=document.createElement('span');badge.className='real-sky-status';badge.setAttribute('role','status');card.append(badge);
 const foreground=physical?new NativeForegroundCapture(canvas):null;
 const status={checkpoint:physical?'9':'8.1',workerFailurePolicy:'withdraw optional sky; never synchronous physical rendering on the prayer UI thread',status:'loading',renders:0,presentationDraws:0,presentationSkips:0,presentationRejections:0,presentationUtcMs:null,rejections:0,errors:[],physical,dprPolicy:'325×530 physics raster at DPR 1; browser scales canvas; no high-DPR certification',last:null};
 let client,lifecycle,frame=null,job=null,disposed=false,paintedFrame=null,paintedJob=null,previousPresentation=null,previousMoonBottom=0,lastCompose=-Infinity,animationId=null,workerUrl=null;
 function publish(){const preview=window.SalahSkyPreview?.state.status==='ready';badge.textContent=status.status==='ready'?(status.last?.diffuseAsset?.mode==='cp6-fallback'?'Diffuse unavailable — CP6 sky':status.last?.diffuseState?.exposureComplete===false?'Diffuse support incomplete':''):status.availability?.reason==='rate-throughput'?`${preview?'Sky preview · r':'R'}efinement unavailable at ${status.availability.rate}×`:preview?'Sky preview · refining…':status.status==='loading'?'Real sky loading…':status.status==='pending'?'Real sky updating…':'Real sky unavailable';badge.title=status.errors.at(-1)??'Optional astronomy; prayer readiness is independent. A current preview is distinct from registered diffuse refinement.';canvas.dataset.status=status.status;}
 function clear(reason='invalidated'){if(card.classList.contains('real-sky-composed'))card.style.removeProperty('--native-sun-cloud-mask');window.SalahMoonDetail?.clear();card.classList.remove('real-sky-composed');frame=null;job=null;status.last=null;paintedFrame=null;paintedJob=null;status.presentationUtcMs=null;status.displayed=null;previousPresentation=null;previousMoonBottom=0;ctx.clearRect(0,0,325,530);canvas.style.visibility='hidden';status.status='pending';status.reason=reason;publish();}
 // Identity/age fences do not consume decorative solar geometry. Measure the
 // presented body only for an accepted atmospheric display, not every guard.
 function snapshot(){return host.capture(false);}
 function calendarGeometry(rows=530){
  if(window.SalahMoonRuntime?.detailEnabled)return {key:'separate-device-resolution-moon',mask:()=>null};
  const disc=document.querySelector('.moon-mask-disc'),matrix=disc?.getScreenCTM();
  if(!matrix||!disc.classList.contains('mask-on')||+getComputedStyle(disc).opacity===0)return {key:null,mask:()=>null};
  const r=canvas.getBoundingClientRect(),{a,b,c,d,e,f}=matrix,m={a,b,c,d,e,f},radius=Number(disc.getAttribute('r'));
  const rect={left:r.left,top:r.top,width:r.width,height:r.height*rows/530};
  return {key:JSON.stringify([rows,rect,a,b,c,d,e,f,radius]),mask:()=>nativeDiscMask(325,rows,rect,m,radius)};
 }
 function compose(){
  if(!frame||disposed)return;
  try{
   const current=snapshot();if(!lifecycle.current(job,current)){clear('host target changed or expired');return;}
   const started=performance.now();
   if(foreground){
    // Full physical frames change only on worker acceptance. Native clouds/Moon
    // can move independently; repaint their entire old/new support, not all 530 rows.
    const bottom=foreground.bottom(),rows=nativeForegroundRows(530,bottom,previousMoonBottom);
    const capture=foreground.capture(rows),geometry=calendarGeometry(rows);
    const presentation={frame,rows,maskKey:geometry.key,cloudRGBA:capture.cloudRGBA,moonRGBA:capture.moonRGBA};
    // Unlike the donor cloud-only guard, this also fences physical frame, PBR
    // bytes, native cutout geometry and old/new foreground support dimensions.
    if(sameNativePresentation(previousPresentation,presentation)){
     status.presentationSkips++;lastCompose=performance.now();
     Object.assign(status.last.composition,capture.native,{lastComposeMs:lastCompose-started});
     card.classList.add('real-sky-composed');canvas.style.visibility='visible';window.SalahMoonDetail?.compose(frame,encodeNativeFrame);return;
    }
    const base=nativeCalendarRegion(frame.raster,geometry.mask(),rows);
    const joined=nativeForeground(base,{...capture,atmosphereLinear:(frame.raster.skyBackgroundLinear??frame.raster.backgroundLinear).subarray(0,base.length),exposure:frame.raster.effectiveExposure});
    // Prepare/validate the entire update before touching the visible framebuffer.
    // A failed capture must not expose an uncomposed base (or partial cloud data).
    const region=new ImageData(encodeNativeFrame(joined.linear,frame.raster.effectiveExposure),325,rows);
    const solarMask=foreground.prepareSolarMask(capture.cloudRGBA,rows);
    const full=paintedFrame!==frame?new ImageData(encodeNativeFrame(frame.raster.linear,frame.raster.effectiveExposure),325,530):null;
    if(!lifecycle.current(job,snapshot())){clear('superseded during composition');return;}
    if(full)ctx.putImageData(full,0,0);
    ctx.putImageData(region,0,0);
    card.style.setProperty('--native-sun-cloud-mask',solarMask);
    paintedFrame=frame;paintedJob=job;status.presentationUtcMs=job.observer.utcMs;previousMoonBottom=bottom;
    status.displayed={utcMs:job.observer.utcMs,identity:job.native.identity,exposure:frame.raster.effectiveExposure,presentation:frame.raster.displayPresentation??null,retained:false};
    previousPresentation=presentation;status.presentationDraws++;
    status.last.composition={...joined.diagnostics,meanCloudAlpha:joined.diagnostics.meanCloudAlpha*rows/530,...capture.native,updatedRows:rows,totalRows:530};card.classList.add('real-sky-composed');
   }else{
    const bytes=encodeNativeFrame(nativeCalendarComposite(frame.raster,calendarGeometry().mask()),frame.raster.effectiveExposure);ctx.putImageData(new ImageData(bytes,325,530),0,0);
   }
   canvas.style.visibility='visible';window.SalahMoonDetail?.compose(frame,encodeNativeFrame);lastCompose=performance.now();
   if(status.last.composition)status.last.composition.lastComposeMs=lastCompose-started;
  }catch(e){
   // Retention is allowed only under the ORIGINAL visible job's fences and
   // 30-second age limit. A seek/configuration/epoch change still clears now.
   if(paintedJob&&lifecycle.current(paintedJob)){
    status.presentationRejections++;status.lastPresentationError=String(e?.message??e);if(status.displayed)status.displayed={...status.displayed,retained:true,reason:status.lastPresentationError};lastCompose=performance.now();return;
   }
   failure(e);
  }
 }

 function accept(result,_id,request){
  const current=snapshot();if(!lifecycle.current(request,current)){status.rejections++;return;}
  if(result.status!=='ready'||!result.raster)throw new Error(result.error??'Native real sky unavailable');
  if(result.raster.physicalState?.sun?.altDeg>-18){
   // Twilight's solar-only shoulder needs the SAME spatial nodes as the raw
   // worker background, so removing solar cannot accidentally remove neutral
   // lunar/natural/local light through a differently interpolated decomposition.
   const step=request.options.backgroundStepCss,grid=result.raster.physicalState.sun.altDeg<-3?[Math.ceil(325/step),Math.ceil(530/step)]:[24,40];
   const fields=nativeAtmosphereFields(result.raster.physicalState,result.raster.atmosphere,request.options.view,request.options.diffuse.residualNight,...grid);
   result={...result,raster:nativeSkyPresentation({...result.raster,solarAerosolLinear:fields.solarAerosolLinear,solarBackgroundLinear:fields.solarBackgroundLinear,twilightDisplay:fields.twilightDisplay},request.options.view,host.capture().solarAnchor)};
  }
  frame=result;job=request;status.status='ready';status.renders++;status.last={utcMs:result.utcMs,observer:result.observer,native:result.native,catalogue:result.catalogue,sources:result.sources,drawn:result.raster.drawn,detectableSources:result.raster.detectableSources,diffuseAsset:result.diffuseAsset,diffuseState:result.raster.diffuseState??null,physicalState:result.raster.physicalState,exposure:result.raster.effectiveExposure,atmosphere:result.raster.atmosphere,visibilityScope:physical?'CP7 contrast diagnostics are before native cloud foreground; final pixel/operator evidence is separate':'CP7 pre-native-overlay contrast diagnostic',weather:current.weather,view:request.options.view,execution:result.execution,timings:result.timings,warnings:result.raster.modelWarnings};compose();publish();
 }
 function failure(e){if(disposed)return;clear('render failure');status.status='unavailable';const message=String(e?.message??e);if(status.errors.at(-1)!==message)status.errors.push(message);status.errors=status.errors.slice(-12);publish();}
 client=new ReferenceRenderClient(pack,{workerFactory:()=>{workerUrl=URL.createObjectURL(new Blob([workerSource],{type:'text/javascript'}));return new Worker(workerUrl);},fallbackFactory:requireNativeWorker,timeoutMs:15000});
 lifecycle=new NativeSkyLifecycle({capture:snapshot,physical,execute:request=>client.run(request),onResult:accept,onInvalidate:clear,onError:failure,onAvailability:value=>{status.availability=value;if(value.status==='unavailable'&&!frame){status.status='unavailable';status.reason=value.reason;publish();}}});
 const request=(force=false)=>lifecycle.request(force);
 // Presentation sampling is not an astronomical clock. It samples native painter
 // output and native SVG transforms; only accepted host UTC drives physics jobs.
 const timer=setInterval(()=>request(),500);
 function animate(now){if(disposed)return;try{const state=snapshot();if(frame&&!lifecycle.current(job,state))clear('host target changed or expired');if(frame&&!state.paused&&now-lastCompose>=(state.reducedMotion?250:50))compose();}catch(e){failure(e);}animationId=requestAnimationFrame(animate);}
 animationId=requestAnimationFrame(animate);
 const visibility=()=>request(true);document.addEventListener('visibilitychange',visibility);
 const readState=()=>({...structuredClone(status),lifecycle:lifecycle.state});
 window.SalahRealSky={request,compose,invalidate:reason=>lifecycle.invalidate(reason),get state(){return readState();},dispose(){if(disposed)return;lifecycle.dispose();disposed=true;clearInterval(timer);cancelAnimationFrame(animationId);document.removeEventListener('visibilitychange',visibility);client.dispose();if(workerUrl)URL.revokeObjectURL(workerUrl);card.classList.remove('real-sky-composed');card.style.removeProperty('--native-sun-cloud-mask');frame=null;job=null;previousPresentation=null;status.last=null;status.status='disposed';canvas.remove();badge.remove();}};
 window.realSkyState=readState;window.realSkyFrame=()=>frame; // Diagnostics, not render authority.
 publish();request(true);
}
