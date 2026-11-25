// Opt-in only in the transformed research build. Each attempt has distinct
// detached nodes. Readers can identify a committed receipt inside the selector
// write itself, even if the writer throws immediately after selecting it.
const selector='data-r002f-preview';
const sequence=Symbol.for('salah.r002f.previewResearchSequence');
const records=new Map();
let transactionRevision=0, previousMoon=null, withdrawalStyle=null;
function selected(){return records.size?records.get(card.getAttribute(selector)):null;}
function synchronizeSelection(){
 const slot=selected();
 if(slot&&!slot.adopted){slot.adopted=true;slot.adopt();}
}
function priorMoonCurrent(){try{return !previousMoon||previousMoon.current();}catch{return false;}}
function revokeIfStale(cloudReceipt){
 const slot=selected();
 if(!slot||withdrawingResearch||window.SalahSkyPreview!==preview)return false;
 let authorized=false;
 try{authorized=slot.frame.current();}catch{ /* unavailable evidence withdraws */ }
 if(authorized||selected()!==slot)return false;
 clear('research selected generation lost authority',false,cloudReceipt);return true;
}
// Retire publication before invoking another owner. Keep one small CSS guard
// until the next withdrawal or disposal, so even a throwing detail cleanup
// cannot reveal the obsolete ordinary preview canvases underneath the slot.
function withdrawSlot(slot,reason,all,cloudReceipt){
 const revision=++transactionRevision;
 const owner=window.SalahMoonDetail;
 const stillWithdrawn=()=>transactionRevision===revision&&window.SalahSkyPreview===preview&&!value&&!card.classList.contains('real-sky-preview-ready')&&!card.classList.contains('real-sky-composed');
 const guard=slot.style;
 card.setAttribute('data-r002f-withdrawn',slot.id);
 canvas.style.visibility='hidden';card.classList.remove('real-sky-preview-ready');
 if(!card.classList.contains('real-sky-composed'))card.style.removeProperty('--native-sun-cloud-mask');
 card.removeAttribute(selector);value=null;previewFrame=null;pendingValue=null;previousMoon=null;
 status.status='pending';status.retained=false;status.reason=reason;
 status.publication=null;status.composition=null;status.utcMs=null;status.researchGeneration=null;
 withdrawalStyle?.remove();withdrawalStyle=guard;slot.style=null;
 releaseSlot(slot);
 const errors=[];
 try{solarPublication.cancel();}catch(e){errors.push(String(e.message??e));}
 if(stillWithdrawn()&&window.SalahMoonDetail===owner){
  try{if(all||!owner?.clearFor)owner?.clear();else owner.clearFor('atmospheric-preview');}catch(e){errors.push(String(e.message??e));}
 }
 if(stillWithdrawn()){
  try{const receipt=cloudReceipt??host.reconcileClouds();if(stillWithdrawn())clearedReceipt=receipt;}catch(e){errors.push(String(e.message??e));}
 }
 if(errors.length&&stillWithdrawn())status.reason=reason+'; cleanup: '+errors.join(', ');
}
function releaseSlot(slot){
 if(!slot)return;
 records.delete(slot.id);
 for(const node of [slot.background,slot.detail,slot.style])node?.remove();
}
function dropSlots(){
 transactionRevision++; previousMoon=null;
 if(records.size){if(selected())card.removeAttribute(selector);for(const slot of Array.from(records.values()))releaseSlot(slot);}
}
function stageCurrent(next,moon,capture,revisionAtEntry){
 if(disposed||transactionRevision!==revisionAtEntry||window.SalahSkyPreview!==preview||card.classList.contains('real-sky-composed')||!card.classList.contains('real-sky-preview-ready'))return false;
 if(!moon.current()||!host.cloudsCurrent(capture.cloudAuthority))return false;
 const now=host.capture(false);
 return !disposed&&transactionRevision===revisionAtEntry&&!card.classList.contains('real-sky-composed')&&!now.paused&&publishable(next,now)?now:false;
}
function publishSlot(next,pixels,base,image,solarMask,capture,bottom,rows,revisionAtEntry,moon,preparedCatalogue){
 const id=String(card[sequence]=(card[sequence]??0)+1), previous=selected(), maskRevision=solarPublication.revision;
 const slot={id,background:null,detail:null,style:null};
 try{
  const bytes=new Uint8ClampedArray(pixels?pixels.data:base);bytes.set(image.data,0);
  const background=slot.background=document.createElement('canvas');
  background.width=325;background.height=530;background.className='r002f-sky-'+id;
  Object.assign(background.style,{position:'absolute',inset:'0',width:'100%',height:'100%',zIndex:'0',borderRadius:'inherit',pointerEvents:'none',visibility:'hidden'});
  background.setAttribute('aria-hidden','true');
  background.getContext('2d',{alpha:false}).putImageData(new ImageData(bytes,325,530),0,0);
  const frame={preview:true,raster:next.raster,current:()=>nativeResultCurrent(next.job,host.capture(false))};
  const detail=moon.prepare(frame,encodeNativeFrame);
  slot.detail=detail.node;slot.detail.className='r002f-moon-'+id;
  const scope='.c.real-sky-preview-ready:not(.real-sky-composed)['+selector+'="'+id+'"]';
  const style=slot.style=document.createElement('style');
  style.textContent=scope+' .real-sky-preview,'+scope+' .moon-detail-canvas{visibility:hidden!important}'+
   scope+' .r002f-sky-'+id+','+scope+' .r002f-moon-'+id+'{visibility:visible!important}'+
   scope+' .sun-cloud-mask{--native-sun-cloud-mask:'+solarMask+'}'+
   '.c:not(.real-sky-preview-ready):not(.real-sky-composed)[data-r002f-withdrawn="'+id+'"] .real-sky-preview,'+
   '.c:not(.real-sky-preview-ready):not(.real-sky-composed)[data-r002f-withdrawn="'+id+'"] .moon-detail-canvas{visibility:hidden!important}';
  const sky=card.querySelector('.sky');if(!sky)throw Error('native lunar stacking anchor missing');
  document.head.append(style);card.prepend(background);sky.after(slot.detail);
  if(!stageCurrent(next,detail,capture,revisionAtEntry))throw Error('preview preparation lost authority');
  const published=host.capture(false), at=performance.now();
  const receipt={...status,status:'ready',quality:next.quality,retained:false,utcMs:next.utcMs,native:next.native,solarAltitudeDeg:next.raster.physicalState.sun.altDeg,display:next.raster.displayPresentation,diagnostics:next.diagnostics,catalogue:next.raster.starPreview??null,reason:null,
   publication:{utcMs:published.utcMs,ageMs:published.utcMs-next.utcMs,at},composition:{...capture.native,updatedRows:rows,atmosphere:'foreground path retained',cloudApplications:1},draws:status.draws+1,
   researchGeneration:id,researchAdoption:moon.token};
  slot.receipt=Object.freeze(structuredClone(receipt));slot.frame={...frame,current:()=>{if(disposed||!detail.current()||!host.cloudsCurrent(capture.cloudAuthority))return false;const state=host.capture(false);return !state.paused&&publishable(next,state);}};slot.moon=detail;
  slot.adopt=()=>{
   previewFrame=frame;value=next;baseBytes=base;previousMoonBottom=bottom;previousMoon=detail;
   if(pixels)paintedCatalogueRevision=preparedCatalogue;
   Object.assign(status,receipt);lastPaint=at;
  };
  records.set(id,slot);
  const admitted=stageCurrent(next,detail,capture,revisionAtEntry);
  if(!admitted||catalogueRevision!==preparedCatalogue||solarPublication.revision!==maskRevision)throw Error('preview final admission failed');
  slot.receipt.publication.utcMs=receipt.publication.utcMs=admitted.utcMs;slot.receipt.publication.ageMs=receipt.publication.ageMs=admitted.utcMs-next.utcMs;
  Object.freeze(slot.receipt.publication);
  try{card.setAttribute(selector,id);}catch(error){if(selected()!==slot)throw error;}
  if(selected()!==slot||disposed)return false;
  synchronizeSelection();return true;
 }finally{
  const winner=selected();
  if(winner!==slot)releaseSlot(slot);
  if(previous&&previous!==winner)releaseSlot(previous);
 }
}
