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
 let value=null,baseBytes=null,previewFrame=null,previousMoonBottom=0,disposed=false,lastPaint=-Infinity,raf,catalogue=null,nativeDriven=false;
 const status={status:'pending',quality:'physical-background-preview',utcMs:null,reason:null,draws:0};
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
  const current=host.capture(false);if(current.paused||!nativeResultCurrent(next.job,current)){clear('preview target changed, hidden or expired');return;}
  try{
   const {bottom,rows,capture,mask,solarMask}=prepared??prepareForeground(),base=pixels?pixels.data:baseBytes;
   let region=base.subarray(0,325*rows*4);
   if(next.raster.starPreview)region=nativeStarPreviewRegion(next,mask,rows);
   const bytes=nativeCloudDisplayFrame(region,capture.cloudRGBA,capture.moonRGBA);
   if(!nativeResultCurrent(next.job,host.capture(false))){clear('preview superseded during cloud composition');return;}
   // Prepare both buffers before publication: invalid foreground cannot expose
   // a half-composed new background. Retain only the old, still-current image.
   if(pixels)ctx.putImageData(pixels,0,0);
   ctx.putImageData(new ImageData(bytes,325,rows),0,0);
   card.style.setProperty('--native-sun-cloud-mask',solarMask);
   previousMoonBottom=bottom;if(pixels||!previewFrame)previewFrame={preview:true,raster:next.raster,current:()=>nativeResultCurrent(next.job,host.capture(false))};
   value=next;baseBytes=base;Object.assign(status,{status:'ready',quality:next.quality,retained:false,utcMs:next.utcMs,native:next.native,solarAltitudeDeg:next.raster.physicalState.sun.altDeg,display:next.raster.displayPresentation,diagnostics:next.diagnostics,reason:null});
   canvas.style.visibility='visible';retireFirstPaint();card.classList.add('real-sky-preview-ready');window.SalahMoonDetail?.compose(previewFrame,encodeNativeFrame);
   // Device-resolution detail work and final canvas publication also consume
   // real time. Check the ORIGINAL job again before this JS turn can present.
   // A late join must not leave an expired base visible until the next rAF.
   const published=host.capture(false);
   if(!nativeResultCurrent(next.job,published)){clear('preview superseded during final publication');return;}
   status.publication={utcMs:published.utcMs,ageMs:published.utcMs-next.utcMs,at:performance.now()};
   status.composition={...capture.native,updatedRows:rows,atmosphere:'foreground path retained',cloudApplications:1};status.draws++;lastPaint=performance.now();
  }catch(e){
   // Readback may itself consume the remaining age budget. Retain only the
   // ORIGINAL displayed target while it still qualifies after that failure.
   const reason=String(e.message??e);
   if(value&&nativeResultCurrent(value.job,host.capture(false))){status.retained=true;status.reason=reason;}
   else clear(reason);
  }
 }
 function update(){
  if(disposed)return;
  const s=host.capture(false);
  if(!s.sceneIdentity||s.lat==null||s.lon==null||s.paused){clear('accepted target unavailable or hidden');card.classList.add('real-sky-awaiting-input');return;}
  card.classList.remove('real-sky-awaiting-input');
  if(card.classList.contains('real-sky-composed'))return;
  try{
   if(value&&!nativeResultCurrent(value.job,s))clear('preview target changed or expired');
   // Fast playback needs room for calculation AND the next compositor turn
   // inside the unchanged 30 accepted-second fence. Do not wait until 20s old.
   if(!value||!nativeResultCurrent(value.job,s)||Math.abs(s.utcMs-value.utcMs)>(Math.abs(s.timeScale??1)>10?10000:20000)){
    // Read native foreground/layout BEFORE starting the numerical job. These
    // synchronous presentation snapshots cannot change target in this turn,
    // and must not consume its30s accepted-UTC budget at accelerated rates.
    // Keep the job's real accepted UTC; never post-date an old calculation.
    const prepared=prepareForeground(),anchor=host.capture().solarAnchor,fresh=host.capture(false);
    const first=window.SalahFirstPaint?.value;
    let next=first&&nativeResultCurrent(first.job,fresh)?first:renderNativeBackgroundPreview({...fresh,solarAnchor:anchor});
    if(!nativeResultCurrent(next.job,host.capture(false))){clear('preview superseded before publication');return;}
    const image=new ImageData(encodeNativeFrame(next.raster.linear,next.raster.effectiveExposure),next.raster.width,next.raster.height);
    const tile=document.createElement('canvas');tile.width=image.width;tile.height=image.height;tile.getContext('2d').putImageData(image,0,0);
    back.drawImage(tile,0,0,325,530);let pixels=back.getImageData(0,0,325,530);
    if(catalogue){const stars=catalogue.render(next.job,next.raster.physicalState,{background:pixels.data,exposure:next.raster.effectiveExposure});next=joinNativeStarPreview(next,pixels.data,stars);pixels=new ImageData(next.rgba,325,530);}
    if(!nativeResultCurrent(next.job,host.capture(false))){clear('preview superseded during display preparation');return;}
    paint(next,pixels,prepared);return;
   }
   paint();
  }catch(e){const reason=String(e.message??e);if(value&&nativeResultCurrent(value.job,host.capture(false))){status.retained=true;status.reason=reason;}else clear(reason);}
 }
 function present(now){if(disposed)return;const s=host.capture(false);if(!card.classList.contains('real-sky-composed')&&(Math.abs(s.timeScale??1)>10||!value||!nativeResultCurrent(value.job,s)||now-lastPaint>100))update();}
 function tick(now){if(disposed||nativeDriven)return;present(now);raf=requestAnimationFrame(tick);}
 window.SalahSkyPreview={update,clear,present(now){
  // Native's final paint opportunity follows its UI and cloud updates. Once
  // available it owns ongoing presentation; independent bootstrap rAF must
  // not run before native paint and spend the current sky's remaining age.
  if(!nativeDriven){nativeDriven=true;cancelAnimationFrame(raf);}present(now);
 },admitCatalogue(pack){catalogue=null;clear('catalogue admission changed');if(pack)catalogue=new NativeStarPreview(pack);status.catalogue=catalogue?.identity??null;update();},get frame(){return previewFrame;},get state(){return structuredClone(status);},dispose(){disposed=true;catalogue=null;cancelAnimationFrame(raf);canvas.remove();card.classList.remove('real-sky-preview-ready');}};
 update();raf=requestAnimationFrame(tick);
}
