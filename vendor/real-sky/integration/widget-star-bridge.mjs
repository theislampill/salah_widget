/** Tested integration seam, NOT an automatically applied patch to PR38.
 * Read CODEX_START_HERE.md before adopting. In particular, raster.linear must join
 * the host's linear sky pipeline; an opaque reference frame must not cover the Moon.
 */
import {SkyController,discOccults} from '../src/scene.mjs';
import {projectWidgetDome} from '../src/projection.mjs';
import {renderStars} from '../src/renderer.mjs';
export class WidgetStarBridge{
 constructor(catalogue,{onTerminal=()=>{}}={}){this.controller=new SkyController(catalogue);this.onTerminal=onTerminal;this.scene=null;}
 /** Call with the existing temporal owner's accepted UTC and the existing scene ID.
  * This method always consumes the supplied time, even if the scene ID is unchanged.
  */
 project(observer,sceneIdentity,{project=projectWidgetDome,appearanceVersion=0}={}){
  this.scene=this.controller.update(observer,{sceneIdentity,project,appearanceVersion});
  // Only the host is allowed to write _starProjectionKey / _skySceneKey or commitSkyScene.
  // Geometry terminal only! Do NOT reveal sky-pending until the matching raster is published.
  // Both ready and explicitly unavailable are terminal; no random-star fallback.
  this.onTerminal({sceneIdentity,status:this.scene.status,utcMs:observer?.utcMs,error:this.scene.error??null});
  return this.scene;
 }
 sourceVisibility({physicalMoon=null,terrainAltitudeAtAz=()=>0}={}){
  return s=>s.altDeg>=terrainAltitudeAtAz(s.azDeg)&&(!physicalMoon||physicalMoon.altDeg+physicalMoon.radiusDeg<0||!discOccults(s,physicalMoon));
 }
 /** displayTransmissionAt is a SEPARATE screen-space host mask for the existing calendar
  * Moon / foreground. It must not be reinterpreted as astronomical Moon coordinates.
  * Cloud transmission must be applied exactly once, in this mask or the later cloud pass.
  */
 render({width=325,height=530,dpr=1,backgroundLinear=null,background=[0,0,0],atmosphere={},
  physicalMoon=null,terrainAltitudeAtAz=()=>0,displayTransmissionAt=null,sourceTransmissionAt=()=>1,reducedMotion=true,
  scintillationAmplitude=0,sigmaCss=.55,haloFraction=.035}={}){
  return renderStars(this.scene?.sources??[],{width,height,dpr,backgroundLinear,background,atmosphere,
   utcMs:this.scene?.utcMs??0,reducedMotion,scintillationAmplitude,sigmaCss,haloFraction,
   sourceVisibility:this.sourceVisibility({physicalMoon,terrainAltitudeAtAz}),transmissionAt:sourceTransmissionAt,pixelTransmissionAt:displayTransmissionAt});
 }
}
