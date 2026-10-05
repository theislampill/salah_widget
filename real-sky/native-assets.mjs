/** Optional native asset acquisition: bounded, retryable, latest-generation only.
 * Byte/hash admission remains in the retained engine, not this acquisition layer.
 */
export class NativeAssetLoader {
 constructor({load,start,onState=()=>{},onReset=()=>{},timeoutMs=15000}) {
  if(!Number.isFinite(timeoutMs)||timeoutMs<1||timeoutMs>120000)throw new RangeError('Bounded native asset deadline required');
  this.load=load;this.start=start;this.onState=onState;this.onReset=onReset;this.timeoutMs=timeoutMs;
  this.generation=0;this.controller=null;this.disposed=false;this.suspended=false;this.value={status:'idle',generation:0,error:null};
 }
 get state(){return {...this.value};}
 publish(status,error=null){this.value={status,generation:this.generation,error};this.onState(this.state);}
 async retry() {
  if(this.disposed)return {status:'disposed'};
  if(this.suspended)return this.state;
  const generation=++this.generation;this.controller?.abort();this.onReset();
  const controller=new AbortController();this.controller=controller;this.publish('loading');let timer;
  try {
   const deadline=new Promise((_,reject)=>{timer=setTimeout(()=>{reject(new Error('Native sky asset timeout'));controller.abort();},this.timeoutMs);});
   const pack=await Promise.race([this.load(controller.signal,generation),deadline]);
   if(this.disposed||generation!==this.generation)return {status:'superseded'};
   this.start(pack);this.publish('ready');
  }catch(error){
   if(this.disposed||generation!==this.generation)return {status:'superseded'};
   this.onReset();this.publish('unavailable',String(error?.message??error));
  }finally{clearTimeout(timer);if(this.controller===controller)this.controller=null;}
  return this.state;
 }
 // Page lifecycle is reversible; explicit disposal is not. Invalidate before abort
 // so even a loader that ignores AbortSignal cannot publish after pagehide.
 suspend(){if(this.disposed||this.suspended)return;this.suspended=true;this.generation++;this.controller?.abort();this.controller=null;this.onReset();this.publish('suspended');}
 resume(){if(this.disposed||!this.suspended)return Promise.resolve(this.state);this.suspended=false;return this.retry();}
 dispose(){if(this.disposed)return;this.disposed=true;this.generation++;this.controller?.abort();this.controller=null;this.onReset();this.publish('disposed');}
}

/** Ordinary static-folder script path and the same app's inline expansion.
 * Retry refetches the pinned local script; no network source substitution exists.
 */
export function startNativeSkyAssets(start,scriptUrl) {
 const inline=window.__SALAH_REAL_SKY_PACK__;delete window.__SALAH_REAL_SKY_PACK__;
 let badge=null,loader;
 const reset=()=>{window.SalahRealSky?.dispose();window.SalahRealSky=null;window.realSkyFrame=()=>null;};
 const state=asset=>{
  if(asset.status==='ready'){badge?.remove();badge=null;return;}
  window.realSkyState=()=>({checkpoint:'9',status:loader.state.status,assets:loader.state,errors:loader.state.error?[loader.state.error]:[],last:null});
  if(asset.status==='disposed'||asset.status==='suspended'){badge?.remove();badge=null;return;}
  if(!badge){badge=document.createElement('span');badge.className='real-sky-status real-sky-asset-status';badge.setAttribute('role','status');document.querySelector('.c')?.append(badge);}
  badge.textContent=asset.status==='loading'?'Real sky loading…':'Real sky unavailable';badge.title=asset.error??'Optional astronomy does not gate prayer readiness';
 };
 const load=(signal,generation)=>{
  if(inline)return Promise.resolve(inline);
  return new Promise((resolve,reject)=>{
   const el=document.createElement('script');
   const cleanup=()=>{signal.removeEventListener('abort',abort);el.onload=null;el.onerror=null;el.remove();};
   const abort=()=>{cleanup();reject(new Error('Native sky asset load aborted'));};
   el.onload=()=>{const pack=window.__SALAH_REAL_SKY_PACK__;delete window.__SALAH_REAL_SKY_PACK__;cleanup();if(pack)resolve(pack);else reject(new Error('Native sky asset script supplied no pack'));};
   el.onerror=()=>{cleanup();reject(new Error('Local native-data.js unavailable'));};
   if(signal.aborted){abort();return;}signal.addEventListener('abort',abort,{once:true});
   // A removed script may leave a pending network request alive. Distinct local
   // attempt URLs prevent browser request coalescing; exact bytes stay pinned.
   try{const url=new URL('native-data.js',scriptUrl);url.searchParams.set('nativeSkyGeneration',String(generation));el.src=url.href;document.head.append(el);}catch(error){cleanup();reject(error);}
  });
 };
 loader=new NativeAssetLoader({load,start,onState:state,onReset:reset});
 const pagehide=()=>loader.suspend(),pageshow=event=>{if(event.persisted)loader.resume();};
 window.addEventListener('pagehide',pagehide);window.addEventListener('pageshow',pageshow);
 window.SalahRealSkyAssets={retry:()=>loader.retry(),dispose:()=>{window.removeEventListener('pagehide',pagehide);window.removeEventListener('pageshow',pageshow);loader.dispose();},get state(){return loader.state;}};
 loader.retry();return loader;
}
