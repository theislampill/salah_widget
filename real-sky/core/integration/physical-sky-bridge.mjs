/** Local integration seam, not an applied actual-widget patch. Caller owns accepted clock,
 * location and scheduling. No timers, geolocation, cloud fetch or scene-ready writes here. */
import {SkyController} from '../src/scene.mjs';
import {projectAllSky,projectPerspective,projectWidgetDome} from '../src/projection.mjs';
import {renderPhysicalSky,resolveSkyInputs} from '../src/physical-sky-renderer.mjs';
export class PhysicalSkyBridge{
 constructor(catalogue){this.controller=new SkyController(catalogue);this.last=null;}
 render(observer,{sceneIdentity=null,view={type:'camera',width:325,height:530},...appearance}={}){
  try{
   if(appearance.diffuse&&appearance.diffuse.enabled!==false&&appearance.diffuse.binding?.catalogue!==this.controller.catalogue)throw new TypeError('Emitter catalogue does not match the verified diffuse catalogue binding');
   const inputs=resolveSkyInputs(observer,appearance.atmosphere??{});observer=inputs.observer;
   const project=view.type==='allsky'?h=>projectAllSky(h,view):view.type==='legacy'?projectWidgetDome:h=>projectPerspective(h,view);
   const scene=this.controller.update(observer,{sceneIdentity,project});
   if(scene.status!=='ready')return this.last={status:scene.status,sceneIdentity,utcMs:observer.utcMs,error:scene.error,raster:null};
   return this.last={status:'ready',sceneIdentity,utcMs:observer.utcMs,observer,raster:renderPhysicalSky(scene.sources,{...appearance,atmosphere:inputs.atmosphere,observer,view})};
  }catch(e){return this.last={status:'unavailable',sceneIdentity,utcMs:observer?.utcMs,error:String(e.message??e),raster:null};}
 }
}
