/** Serializable CP7.5 reference engine shared by worker and explicit main-thread fallback.
 * Callback modes here are declared test scenarios, not live weather or a second mask owner.
 */
import {DiffuseAssetStore} from './diffuse-assets.mjs';
import {DIFFUSE_MANIFEST_SHA256} from './diffuse-manifest-pin.mjs';
import {ResilientPhysicalSkyBridge} from '../integration/resilient-sky-bridge.mjs';
export class ReferenceSkyEngine{
 #pack;#store;#bridge;#loadKey=null;#disposed=false;
 constructor(pack){this.#pack=pack;this.#store=new DiffuseAssetStore(pack.manifestText,DIFFUSE_MANIFEST_SHA256,pack.catalogueText);this.#bridge=new ResilientPhysicalSkyBridge(this.#store);}
 async render(job){
  if(this.#disposed)throw new Error('Reference engine disposed');
  const start=performance.now(),fault=job.assetFault??'none',revision=job.assetRevision??0;
  if(!['none','missing','corrupt','wrong-version'].includes(fault)||!Number.isSafeInteger(revision)||revision<0)throw new TypeError('Invalid asset scenario/revision');
  if(typeof job.calendarMask!=='boolean'||typeof job.cloudmap!=='boolean')throw new TypeError('Explicit boolean mask/cloud modes required');
  const options={...job.options},wanted=options.diffuse!=null&&options.diffuse!==false&&options.diffuse.enabled!==false;
  if(wanted){
   const key=String(job.tier)+'/'+fault+'/'+revision;
   if(key!==this.#loadKey||this.#store.snapshot.status!=='ready'){
    const reload=this.#loadKey!==null&&(fault!=='none'||this.#loadKey.split('/')[1]!=='none'||Number(this.#loadKey.split('/')[2])!==revision);
    await this.#store.load(job.tier,async()=>{
     if(fault==='missing')throw new Error('Deliberate missing diffuse asset drill');
     const text=this.#pack.assetTexts?.[String(job.tier)];
     if(typeof text!=='string')throw new Error(this.#pack.assetErrors?.[String(job.tier)]??'Requested diffuse asset unavailable');
     if(fault==='corrupt')return text.slice(0,-1);
     if(fault==='wrong-version'){const a=JSON.parse(text);a.schema='unsupported/2';return JSON.stringify(a);}
     return text;
    },{reload});this.#loadKey=key;
   }
  }
  const loadEnd=performance.now(),v=options.view;
  if(job.cloudmap)options.cloudAt=(h,utcMs)=>h.azDeg>=180?.08:1;
  if(job.calendarMask)options.displayTransmissionAt=(x,y)=>Math.hypot(x-v.width*.72,y-v.height*.26)<24?0:1;
  const result=this.#bridge.render(job.observer,options);
  return {...result,timings:{assetLoadMs:loadEnd-start,renderMs:performance.now()-loadEnd,totalMs:performance.now()-start},engineContract:'serialisable accepted inputs; no rendered-frame cache'};
 }
 dispose(){if(this.#disposed)return;this.#disposed=true;this.#store.dispose();this.#pack=null;this.#bridge.last=null;}
}
/** Shared ArrayBuffer aliases must appear once in a transfer list. Metadata is cloned,
 * while these owned buffers are moved, not copied, to the accepting UI. */
export function rasterTransferables(result){
 const seen=new Set(),out=[];
 function walk(v){if(v===null||typeof v!=='object')return;if(ArrayBuffer.isView(v)){if(v.buffer instanceof ArrayBuffer&&!seen.has(v.buffer)){seen.add(v.buffer);out.push(v.buffer);}return;}for(const x of Object.values(v))walk(x);}
 walk(result?.raster);return out;
}
