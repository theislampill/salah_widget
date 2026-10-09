import {nativeResultCurrent,nativeDiscMask} from './native-contract.mjs';
import {renderNativeBackgroundPreview} from './native-preview.mjs';
import {NativeForegroundCapture,nativeForegroundRows} from './native-composition.mjs';
import {encodeNativeFrame} from './native-encoding.mjs';
import {nativeCloudDisplayFrame} from './native-cloud-transfer.mjs';
import {NativeStarPreview,joinNativeStarPreview,nativeStarPreviewRegion} from './native-star-preview.mjs';

/** Immediate atmospheric owner; expensive catalogue/diffuse work stays in its
 * existing worker. A preview is never reported as a refined physical frame. */
export function startNativeSkyPreview(){
 const card=document.querySelector('.c'),host=window.SalahNativeSkyHost;
 if(!card||!host)return;
 const canvas=document.createElement('canvas');canvas.className='real-sky-preview';canvas.width=325;canvas.height=530;canvas.setAttribute('aria-hidden','true');card.prepend(canvas);
 const ctx=canvas.getContext('2d',{alpha:false}),foreground=new NativeForegroundCapture(canvas);
 const background=document.createElement('canvas'),back=background.getContext('2d');background.width=325;background.height=530;
 let value=null,baseBytes=null,previewFrame=null,previousMoonBottom=0,disposed=false,lastPaint=-Infinity,raf,catalogue=window.SalahStarBootstrap??null,nativeDriven=false,catalogueRevision=0,paintedCatalogueRevision=0,catalogueRequest=0;
 // The retained final-rAF observer measured up to3.3ms after publication.
 // Reserve5ms of wall time inside (never beyond) the30 accepted-second fence.
 // This is admission headroom, not a guarantee under arbitrary OS stalls.
 const publicationReserveMs=5;
 const status={status:'pending',quality:'physical-background-preview',utcMs:null,reason:null,draws:0,publicationReserveMs,deadlineRetries:0,deadlineMisses:[]};
 const publishable=(next,s)=>nativeResultCurrent(next.job,s)&&Math.abs(s.utcMs-next.utcMs)+publicationReserveMs*Math.abs(s.timeScale??1)<=30000;
 function missed(next,reason,current=host.capture(false)){
  status.deadlineMisses.push({reason,originalUtcMs:next.utcMs,acceptedUtcMs:current.utcMs,ageMs:Math.abs(current.utcMs-next.utcMs),at:performance.now()});
  if(status.deadlineMisses.length>8)status.deadlineMisses.shift();return false;
 }
 function retain(reason,s){status.retained=true;status.reason=reason;status.publication={utcMs:s.utcMs,ageMs:Math.abs(s.utcMs-value.utcMs),at:performance.now(),retained:true};}
 function retireFirstPaint(){document.querySelector('#native-first-paint')?.remove();window.SalahFirstPaint=null;}
 function clear(reason){if(!card.classList.contains('real-sky-composed'))card.style.removeProperty('--native-sun-cloud-mask');value=null;previewFrame=null;window.SalahMoonDetail?.clear();retireFirstPaint();status.status='pending';status.retained=false;status.reason=reason;card.classList.remove('real-sky-preview-ready');canvas.style.visibility='hidden';}
 function prepareForeground(){
  const bottom=foreground.bottom(),rows=nativeForegroundRows(530,bottom,previousMoonBottom),capture=foreground.capture(rows);
  let mask=null;
  if(catalogue){
   const disc=document.querySelector('.moon-mask-disc'),matrix=disc?.getScreenCTM();
   if(matrix&&disc.classList.contains('mask-on')&&+getComputedStyle(disc).opacity>0){const r=canvas.getBoundingClientRect();mask=nativeDiscMask(325,rows,{left:r.left,top:r.top,width:r.width,height:r.height*rows/530},matrix,Number(disc.getAttribute('r')));}
  }
  return {bottom,rows,capture,mask,solarMask:foreground.prepareSolarMask(capture.cloudRGBA,rows)};
 }
 function paint(next=value,pixels=null,prepared=null){
  if(!next||disposed)return;
  const current=host.capture(false);if(current.paused||!nativeResultCurrent(next.job,current))return missed(next,'preview target changed, hidden or expired',current);
  try{
   const {bottom,rows,capture,mask,solarMask}=prepared??prepareForeground(),base=pixels?pixels.data:baseBytes;
   let region=base.subarray(0,325*rows*4);
   if(next.raster.starPreview)region=nativeStarPreviewRegion(next,mask,rows);
   const bytes=nativeCloudDisplayFrame(region,capture.cloudRGBA,capture.moonRGBA);
   if(!nativeResultCurrent(next.job,host.capture(false)))return missed(next,'preview superseded during cloud composition');
   // Prepare both buffers before publication: invalid foreground cannot expose
   // a half-composed new background. Retain only the old, still-current image.
   if(pixels)ctx.putImageData(pixels,0,0);
   ctx.putImageData(new ImageData(bytes,325,rows),0,0);
   card.style.setProperty('--native-sun-cloud-mask',solarMask);
   previousMoonBottom=bottom;if(pixels||!previewFrame)previewFrame={preview:true,raster:next.raster,current:()=>nativeResultCurrent(next.job,host.capture(false))};
   value=next;baseBytes=base;if(pixels)paintedCatalogueRevision=catalogueRevision;
   Object.assign(status,{status:'ready',quality:next.quality,retained:false,utcMs:next.utcMs,native:next.native,solarAltitudeDeg:next.raster.physicalState.sun.altDeg,display:next.raster.displayPresentation,diagnostics:next.diagnostics,catalogue:next.raster.starPreview??null,reason:null});
   canvas.style.visibility='visible';retireFirstPaint();card.classList.add('real-sky-preview-ready');window.SalahMoonDetail?.compose(previewFrame,encodeNativeFrame);
   // Device-resolution detail work and final canvas publication also consume
   // real time. Check the ORIGINAL job again before this JS turn can present.
   // A late join must not leave an expired base visible until the next rAF.
   const published=host.capture(false);
   if(!publishable(next,published))return missed(next,'preview final publication lacks currentness headroom',published);
   status.publication={utcMs:published.utcMs,ageMs:published.utcMs-next.utcMs,at:performance.now()};
   status.composition={...capture.native,updatedRows:rows,atmosphere:'foreground path retained',cloudApplications:1};status.draws++;lastPaint=performance.now();
  }catch(e){
   // Readback may itself consume the remaining age budget. Retain only the
   // ORIGINAL displayed target while it still qualifies after that failure.
   const reason=String(e.message??e);
   if(value){const retained=host.capture(false);if(publishable(value,retained))retain(reason,retained);else return missed(value,'preview exception lacks currentness headroom: '+reason,retained);}
   else clear(reason);
  }
 }
 function update(retried=false){
  if(disposed)return;
  const s=host.capture(false);
  if(!s.sceneIdentity||s.lat==null||s.lon==null||s.paused){clear('accepted target unavailable or hidden');card.classList.add('real-sky-awaiting-input');return;}
  card.classList.remove('real-sky-awaiting-input');
  if(card.classList.contains('real-sky-composed'))return;
  // A transient layout/readback stall must not expose an intermediate blank
  // frame. Retry once in this SAME synchronous presentation turn, with a fresh
  // complete native snapshot and its real UTC. Never relabel the old result.
  // If the second attempt also fails, the existing fail-closed policy applies.
  const retry=()=>{if(!retried){status.deadlineRetries++;update(true);}else clear(status.deadlineMisses.at(-1)?.reason??'preview deadline');};
  try{
   if(value&&!nativeResultCurrent(value.job,s))clear('preview target changed or expired');
   // Fast playback needs room for calculation AND the next compositor turn
   // inside the unchanged 30 accepted-second fence. Do not wait until 20s old.
   if(!value||catalogueRevision!==paintedCatalogueRevision||!nativeResultCurrent(value.job,s)||Math.abs(s.utcMs-value.utcMs)>(Math.abs(s.timeScale??1)>10?10000:20000)){
    // Read native foreground/layout BEFORE starting the numerical job. These
    // synchronous presentation snapshots cannot change target in this turn,
    // and must not consume its30s accepted-UTC budget at accelerated rates.
    // Keep the job's real accepted UTC; never post-date an old calculation.
    const prepared=prepareForeground(),anchor=host.capture().solarAnchor,fresh=host.capture(false);
    const first=window.SalahFirstPaint?.value;
    let next=first&&nativeResultCurrent(first.job,fresh)?first:renderNativeBackgroundPreview({...fresh,solarAnchor:anchor});
    if(!nativeResultCurrent(next.job,host.capture(false))){missed(next,'preview superseded before publication');retry();return;}
    const image=new ImageData(next.rgba??encodeNativeFrame(next.raster.linear,next.raster.effectiveExposure),next.raster.width,next.raster.height);
    // The ordinary raster is already at the card footprint. Preserve its
    // encoded bytes directly; a canvas upload/readback adds no information.
    // Accelerated-clock rasters still use the existing resampling path.
    let pixels=image;
    if(image.width!==325||image.height!==530){
     const tile=document.createElement('canvas');tile.width=image.width;tile.height=image.height;tile.getContext('2d').putImageData(image,0,0);
     back.drawImage(tile,0,0,325,530);pixels=back.getImageData(0,0,325,530);
    }
    if(catalogue&&!next.raster.starPreview){const stars=catalogue.render(next.job,next.raster.physicalState,{background:pixels.data,exposure:next.raster.effectiveExposure});next=joinNativeStarPreview(next,pixels.data,stars);pixels=new ImageData(next.rgba,325,530);}
    if(!nativeResultCurrent(next.job,host.capture(false))){missed(next,'preview superseded during display preparation');retry();return;}
    if(paint(next,pixels,prepared)===false)retry();return;
   }
   if(paint()===false)retry();
  }catch(e){const reason=String(e.message??e);if(value){const retained=host.capture(false);if(publishable(value,retained))retain(reason,retained);else{missed(value,'preview preparation exception lacks currentness headroom: '+reason,retained);retry();}}else clear(reason);}
 }
 function present(now){if(disposed)return;const s=host.capture(false);if(!card.classList.contains('real-sky-composed')&&(catalogueRevision!==paintedCatalogueRevision||Math.abs(s.timeScale??1)>10||!value||!nativeResultCurrent(value.job,s)||now-lastPaint>100))update();}
 function tick(now){if(disposed||nativeDriven)return;present(now);raf=requestAnimationFrame(tick);}
 window.SalahSkyPreview={update,clear,present(now){
  // Native's final paint opportunity follows its UI and cloud updates. Once
  // available it owns ongoing presentation; independent bootstrap rAF must
  // not run before native paint and spend the current sky's remaining age.
  if(!nativeDriven){nativeDriven=true;cancelAnimationFrame(raf);}present(now);
 },async admitCatalogue(pack){
  // Validation/parsing and first stellar composition must not occupy the same
  // startup task. Keep the ORIGINAL current atmosphere until the next native
  // paint atomically replaces it; that paint rechecks target/epoch/30s age.
  // Clearing the preview here both stalled controls and caused a needless gap.
   const revision=++catalogueRequest;status.catalogueError=null;
  try{
   const next=pack?await NativeStarPreview.create(pack):window.SalahStarBootstrap??null;
   if(disposed||revision!==catalogueRequest)return;
   // Asset reset revokes pending admission, but the same bootstrap is not a
   // new displayed catalogue. Avoid rebuilding a current sky before first paint.
   if(catalogue!==next){catalogue=next;catalogueRevision++;}
  }catch(error){if(!disposed&&revision===catalogueRequest)status.catalogueError=String(error.message??error);}
 },get frame(){return previewFrame;},get state(){return structuredClone(status);},dispose(){disposed=true;catalogue=null;cancelAnimationFrame(raf);canvas.remove();card.classList.remove('real-sky-preview-ready');}};
 update();raf=requestAnimationFrame(tick);
}
