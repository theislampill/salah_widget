import {DiffuseAssetStore} from './core/src/diffuse-assets.mjs';
import {DIFFUSE_MANIFEST_SHA256} from './core/src/diffuse-manifest-pin.mjs';
import {ResilientPhysicalSkyBridge} from './core/integration/resilient-sky-bridge.mjs';
import {projectCatalogue} from './core/src/scene.mjs';
import {projectPerspective} from './core/src/projection.mjs';
/** Real CP7 renderer with native inputs; none of the reference viewer's diagnostic masks. */
export class NativeSkyEngine{
 constructor(pack){this.pack=pack;this.store=new DiffuseAssetStore(pack.manifestText,DIFFUSE_MANIFEST_SHA256,pack.catalogueText);this.bridge=new ResilientPhysicalSkyBridge(this.store);this.loaded=false;}
 async render(job){
  const start=performance.now();if(!this.pack)throw new Error('Native engine disposed');
  if(job.options.atmosphere.cloudTransmission!==1||job.options.atmosphere.cloudGlowCdM2!==0)throw new Error('Native foreground owns cloud transmission and colour exactly once');
  if(job.options.diffuse.enabled&&!this.loaded){await this.store.load(job.tier,async()=>{const t=this.pack.assetTexts?.[String(job.tier)];if(typeof t!=='string')throw new Error('Native diffuse asset missing');return t;});this.loaded=true;}
  const begin=performance.now(),result=this.bridge.render(job.observer,job.options);
  let sources=[];
  if(result.status==='ready')sources=projectCatalogue(this.store.catalogue,job.observer,h=>projectPerspective(h,job.options.view)).filter(s=>s.visible&&s.emission?.enabled!==false).map(s=>({id:s.id,hip:s.hip,hygId:s.hygId,name:s.properName??s.name??null,vmag:s.vmag,x:s.x,y:s.y,altDeg:s.altDeg,azDeg:s.azDeg}));
  return {...result,native:job.native,sources,timings:{assetMs:begin-start,renderMs:performance.now()-begin,totalMs:performance.now()-start},catalogue:{id:this.store.catalogue.id,records:this.store.catalogue.stars.length,emitters:this.store.catalogue.stars.filter(s=>s.emission?.enabled!==false).length,sha256:this.store.manifest.catalogue.sha256}};
 }
 dispose(){this.store.dispose();this.pack=null;this.bridge.last=null;}
}
