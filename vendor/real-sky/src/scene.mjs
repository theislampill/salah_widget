/** Stateful integration boundary. Scene readiness and ticking astronomical time are DIFFERENT keys.
 * The host owns scheduling, clock, geolocation, Moon and weather. This module owns none of them.
 */
import {validateCatalogue} from './catalogue.mjs';
import {observationFrame,observeStar,DEG,unit,slerp,angularSeparation,finite,wrapDeg} from './astronomy.mjs';
import {projectWidgetDome} from './projection.mjs';
export function projectCatalogue(catalogue,observer,project=projectWidgetDome){
 const f=observationFrame(observer);
 return catalogue.stars.map(s=>{const h=observeStar(s,f),p=project(h);return {...s,...h,x:p?.x??0,y:p?.y??0,visible:!!p&&p.visible!==false&&h.aboveHorizon};});
}
export class SkyController{
 constructor(catalogue=null){this.catalogue=catalogue?validateCatalogue(catalogue):null;this.generation=0;this.last=null;this.error=null;}
 clear(){this.last=null;this.catalogue=null;this.generation++;}
 /** A late network callback cannot re-paint a superseded target. Failure is empty, never fictional. */
 async replaceAsync(load){const generation=++this.generation;this.catalogue=null;this.last=null;try{const c=validateCatalogue(await load());if(generation!==this.generation)return false;this.catalogue=c;this.error=null;return true;}catch(e){if(generation===this.generation){this.catalogue=null;this.error=String(e.message??e);}return false;}}
 update(observer,{sceneIdentity=null,appearanceVersion=0,project=projectWidgetDome}={}){
  if(!this.catalogue)return this.last={status:'unavailable',sources:[],sceneIdentity,appearanceVersion,error:this.error??'catalogue-unavailable'};
  try{const sources=projectCatalogue(this.catalogue,observer,project);return this.last={status:'ready',sources,sceneIdentity,appearanceVersion,utcMs:observer.utcMs,catalogueId:this.catalogue.id};}
  catch(e){return this.last={status:'unavailable',sources:[],sceneIdentity,appearanceVersion,error:String(e.message??e)};}
 }
}
export function horizontalVector(h){const a=h.azDeg*DEG,e=h.altDeg*DEG;return [Math.cos(e)*Math.sin(a),Math.cos(e)*Math.cos(a),Math.sin(e)];}
function fromVector(v){v=unit(v);return {altDeg:Math.asin(Math.max(-1,Math.min(1,v[2])))/DEG,azDeg:wrapDeg(Math.atan2(v[0],v[1])/DEG)};}
/** A geometrical occulting disc is opaque even at new Moon. Caller must supply PHYSICAL
 * apparent sky coordinates/radius, never the widget's calendar Moon placement or illumination.
 */
export function discOccults(star,disc){finite(disc.radiusDeg,'angular radius',0,90);return angularSeparation(horizontalVector(star),horizontalVector(disc))<=disc.radiusDeg;}
/** Great-circle chart strokes, segmented then clipped. They are annotations, never light sources.
 * Entirely hidden edges yield no strokes; partial paths are honestly clipped rather than connected
 * through the card from one visible end to an unrelated point. No boundary assignment is implied.
 */
export function annotationSegments(annotations,sources,project=projectWidgetDome,{maxStepDeg=1,maxPixelStep=80}={}){
 finite(maxStepDeg,'angular annotation step',.1,5);const byHip=new Map(sources.map(s=>[s.hip,s])),result=[];
 for(const pattern of annotations.patterns)for(const path of pattern.paths)for(let i=1;i<path.length;i++){
  const a=byHip.get(path[i-1]),b=byHip.get(path[i]);if(!a||!b)continue;
  const av=horizontalVector(a),bv=horizontalVector(b),count=Math.max(1,Math.ceil(angularSeparation(av,bv)/maxStepDeg));let prev=null;
  for(let j=0;j<=count;j++){const h=fromVector(slerp(av,bv,j/count)),p=project(h),curr=p&&h.altDeg>=0&&p.visible!==false?{...p,visible:true}:null;
   if(prev&&curr&&Math.hypot(curr.x-prev.x,curr.y-prev.y)<=maxPixelStep)result.push({id:pattern.id,a:prev,b:curr});prev=curr;
  }
 }
 return result;
}
