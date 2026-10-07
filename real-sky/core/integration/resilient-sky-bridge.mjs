/** CP7.5 reference host wrapper; NOT actual-widget readiness integration.
 * A failed requested diffuse tier yields a NEW CP6 frame at the accepted observer.
 * Invalid physics/observer is never rescued by relabelling it an asset failure.
 */
import {DiffuseAssetStore} from '../src/diffuse-assets.mjs';
import {PhysicalSkyBridge} from './physical-sky-bridge.mjs';
export class ResilientPhysicalSkyBridge{
 #store;#base;#bridges=new WeakMap();
 constructor(store){if(!(store instanceof DiffuseAssetStore))throw new TypeError('Verified diffuse asset store required');this.#store=store;this.#base=new PhysicalSkyBridge(store.catalogue);this.last=null;}
 render(observer,options={}){
  const state=this.#store.snapshot,wanted=options.diffuse!=null&&options.diffuse!==false&&options.diffuse.enabled!==false;
  const active=wanted&&state.status==='ready',binding=active?state.binding:null;let bridge=this.#base;
  if(active){bridge=this.#bridges.get(binding);if(!bridge){bridge=new PhysicalSkyBridge(binding.catalogue);this.#bridges.set(binding,bridge);}}
  const diffuse=active?{...options.diffuse,binding}:{enabled:false};
  const result=bridge.render(observer,{...options,diffuse});
  return this.last={...result,diffuseAsset:{mode:active?'registered':wanted?'cp6-fallback':'disabled',status:state.status,tier:state.tier,generation:state.generation,assetSha256:state.assetSha256??null,error:state.error??null,cacheEntries:this.#store.cacheEntries}};
 }
}
