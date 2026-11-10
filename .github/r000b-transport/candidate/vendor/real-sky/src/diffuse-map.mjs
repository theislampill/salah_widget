import {DEG,finite,wrapDeg,unit,dot,radecVector,vectorRaDec,observationFrame,aberrate,equatorialToHorizontal,refractionDeg} from './astronomy.mjs';
import {cameraGeometry,unprojectPerspective,unprojectAllSky} from './projection.mjs';
/** CP7 PARTIAL: validated diagnostic map sampling + celestial registration.
 * Does not authenticate/permit a scientific survey, apply source proper motion,
 * transport atmosphere/cloud light, occult the Moon or encode a physical frame.
 * Current accepted roles are diagnostic and test fixture ONLY.
 */
const DF_ROLE='finite-catalogue-diagnostic-not-survey';
const DF_SCHEMA='salah-real-sky/diffuse-map/1';
function dfArray(a,n,label){if(!Array.isArray(a)||a.length!==n)throw new TypeError(label+' length mismatch');}
function dfArea(w,h,j){return 2*Math.PI/w*(Math.sin((-90+(j+1)*180/h)*DEG)-Math.sin((-90+j*180/h)*DEG));}
export function createDiagnosticDiffuseSampler(asset){
 if(asset?.schema!==DF_SCHEMA||asset.productionAdmissible!==false||![DF_ROLE,'test-fixture'].includes(asset.role))throw new TypeError('Only explicit non-production diagnostic maps or test fixtures are admitted');
 if(asset.frame!=='mean-equatorial-J2000'||asset.epochJyear!==2000)throw new RangeError('Unsupported diffuse coordinate frame/epoch');
 if(asset.quantity!=='relative-V0-flux-per-steradian')throw new RangeError('Unsupported diagnostic radiance unit');
 if(typeof asset.id!=='string'||!asset.id.length||asset.id.length>256)throw new TypeError('Dataset ID required');
 if(typeof asset.sourceSha256!=='string'||!/^[0-9a-f]{64}$/.test(asset.sourceSha256))throw new TypeError('Source hash required; its presence alone does not authenticate the source');
 const g=asset.grid,w=g?.width,h=g?.height;
 if(g?.type!=='equirectangular-cell-centred'||!Number.isInteger(w)||!Number.isInteger(h)||w<4||h<2||w>4096||h>2048||w*h>2097152)throw new RangeError('Invalid or oversized diagnostic grid');
 finite(g.lonStepDeg,'longitude grid spacing',Number.MIN_VALUE);finite(g.latStepDeg,'latitude grid spacing',Number.MIN_VALUE);
 if(g.lonOriginDeg!==0||g.latOriginDeg!==-90||Math.abs(g.lonStepDeg-360/w)>1e-10||Math.abs(g.latStepDeg-180/h)>1e-10)throw new RangeError('Grid axis/spacing contract mismatch');
 dfArray(asset.values,w*h,'values');dfArray(asset.validMask,w*h,'validMask');
 const a=new Float64Array(w*h),mask=new Uint8Array(w*h);let total=0,correction=0;
 for(let i=0;i<a.length;i++){
  const m=asset.validMask[i];if(m!==0&&m!==1)throw new RangeError('Mask must contain 0 or 1');mask[i]=m;
  const v=asset.values[i];if(m===0){if(v!==null&&v!==0)throw new RangeError('Missing cells must be null or zero, not hidden radiance');a[i]=0;}
  else {finite(v,'map radiance',0,1e12);a[i]=v;}
  const q=a[i]*dfArea(w,h,Math.floor(i/w))-correction,t=total+q;correction=(t-total)-q;total=t;
 }
 if(asset.totalRelativeV0Flux!=null){finite(asset.totalRelativeV0Flux,'declared total',0);if(Math.abs(total-asset.totalRelativeV0Flux)>1e-9*Math.max(1,total))throw new RangeError('Map integrated flux disagrees with its declaration');}
 const cap=j=>{let weighted=0,support=0;for(let x=0;x<w;x++){weighted+=a[j*w+x]/w;support+=mask[j*w+x]/w;}return {weighted,support};};
 const south=cap(0),north=cap(h-1);
 function row(j,x){const ix=Math.floor(x),t=x-ix,l=j*w+((ix%w)+w)%w,r=j*w+((ix+1)%w+w)%w;return {weighted:a[l]*(1-t)+a[r]*t,support:mask[l]*(1-t)+mask[r]*t};}
 function sample(raDeg,decDeg){
  finite(raDeg,'map RA');finite(decDeg,'map declination',-90,90);
  const x=wrapDeg(raDeg)/360*w-.5,y=(decDeg+90)/180*h-.5;let v,s;
  if(y<0){const t=(decDeg+90)/(90/h),b=row(0,x);v=south.weighted*(1-t)+b.weighted*t;s=south.support*(1-t)+b.support*t;}
  else if(y>h-1){const t=(90-decDeg)/(90/h),b=row(h-1,x);v=north.weighted*(1-t)+b.weighted*t;s=north.support*(1-t)+b.support*t;}
  else {const j=Math.floor(y),t=y-j,b=row(j,x),c=row(Math.min(h-1,j+1),x);v=b.weighted*(1-t)+c.weighted*t;s=b.support*(1-t)+c.support*t;}
  const defined=s>=1-1e-12;
  return {value:defined?v:null,defined,supportFraction:s,availableWeightedValue:v,observationalCoverage:null};
 }
 return Object.freeze({id:asset.id,role:asset.role,diagnosticOnly:true,productionAdmissible:false,sourceSha256:asset.sourceSha256,frame:asset.frame,quantity:asset.quantity,width:w,height:h,totalRelativeV0Flux:total,sample});
}
function dfFrame(value){return value?.rotation?value:observationFrame(value);}
function dfApply(columns,v){return [0,1,2].map(i=>columns[0][i]*v[0]+columns[1][i]*v[1]+columns[2][i]*v[2]);}
/** Infinite-distance fixed J2000 direction; no star-dependent propagation is meaningful here. */
export function observeDiffuseDirection(direction,observerOrFrame){
 const f=dfFrame(observerOrFrame),o=f.observer;let v=unit(direction);
 if(f.aberration)v=aberrate(v,f.velocityOverC);v=dfApply(f.rotation,v);
 const eq=vectorRaDec(v),h=equatorialToHorizontal(eq.raDeg,eq.decDeg,f.lstDeg,f.latDeg);let ref=0;
 if(h.altDeg>=-1&&o.pressureHpa>0)ref=refractionDeg(h.altDeg,o.pressureHpa,o.temperatureC);
 const alt=h.altDeg+ref,az=h.azDeg*DEG;
 return {...h,geometricAltDeg:h.altDeg,altDeg:alt,refractionDeg:ref,enuGeometric:h.enu,enu:[Math.cos(alt*DEG)*Math.sin(az),Math.cos(alt*DEG)*Math.cos(az),Math.sin(alt*DEG)],utcMs:o.utcMs};
}
function dfUndoRefraction(apparent,o){
 if(o.pressureHpa===0||apparent>=89.9||apparent< -1)return apparent;
 const minimum=-1+refractionDeg(-1,o.pressureHpa,o.temperatureC);
 if(apparent<minimum)throw new RangeError('Apparent altitude falls in the inherited refraction-model discontinuity');
 let lo=-1,hi=89.9;
 for(let i=0;i<44;i++){const mid=(lo+hi)/2,app=mid+refractionDeg(mid,o.pressureHpa,o.temperatureC);if(app<apparent)lo=mid;else hi=mid;}
 return (lo+hi)/2;
}
/** Geometric altitude for physical occultation of an apparent diffuse ray. */
export function diffuseGeometricAltitude(apparentAltDeg,observerOrFrame){const f=dfFrame(observerOrFrame);return dfUndoRefraction(finite(apparentAltDeg,'apparent altitude',-90,90),f.observer);}
export function horizontalToDiffuseJ2000(horizontal,observerOrFrame){
 const f=dfFrame(observerOrFrame),o=f.observer;finite(horizontal?.altDeg,'horizontal altitude',-90,90);finite(horizontal?.azDeg,'horizontal azimuth');
 const alt=dfUndoRefraction(horizontal.altDeg,o)*DEG,az=horizontal.azDeg*DEG,p=f.latDeg*DEG,t=f.lstDeg*DEG;
 const e=Math.cos(alt)*Math.sin(az),n=Math.cos(alt)*Math.cos(az),u=Math.sin(alt),meridian=u*Math.cos(p)-n*Math.sin(p);
 const date=[meridian*Math.cos(t)-e*Math.sin(t),meridian*Math.sin(t)+e*Math.cos(t),n*Math.cos(p)+u*Math.sin(p)];
 let v=f.rotation.map(c=>dot(c,date));
 if(f.aberration)v=aberrate(v,f.velocityOverC.map(x=>-x));
 return unit(v);
}
export function diffuseRayToMap(xCss,yCss,view,observerOrFrame){
 finite(xCss,'pixel x');finite(yCss,'pixel y');const f=dfFrame(observerOrFrame);let horizontal;
 if(view?.type==='camera')horizontal=unprojectPerspective(xCss,yCss,view);
 else if(view?.type==='allsky')horizontal=unprojectAllSky(xCss,yCss,view);
 else throw new RangeError('Diagnostic view must be camera or allsky');
 if(horizontal.altDeg<0)return {aboveHorizon:false,horizontal,j2000:null,raDeg:null,decDeg:null};
 const v=horizontalToDiffuseJ2000(horizontal,f);
 return {aboveHorizon:true,horizontal,j2000:v,...vectorRaDec(v)};
}
/** Diagnostic surface-brightness raster ONLY, not the CP6 physical linear-light frame.
 * Supersamples the camera footprint. Missing source support is a separate mask, never
 * silently renormalised or converted to measured darkness. No frame/time cache is kept.
 */
export function renderDiagnosticDiffuse(sampler,observer,view,{dpr=1,samplesPerAxis=1}={}){
 if(sampler?.diagnosticOnly!==true||typeof sampler.sample!=='function')throw new TypeError('Diagnostic sampler required');
 finite(view?.width,'CSS width',16,2048);finite(view?.height,'CSS height',16,2048);finite(dpr,'DPR',.5,3);
 if(!Number.isInteger(samplesPerAxis)||samplesPerAxis<1||samplesPerAxis>4)throw new RangeError('Footprint samples per axis must be 1..4');
 if(view.type==='camera')cameraGeometry(view);else if(view.type!=='allsky')throw new RangeError('Unsupported view');
 if(view.type==='allsky'&&((view.padding??4)<0||(view.padding??4)>=Math.min(view.width,view.height)/2))throw new RangeError('Invalid all-sky padding');
 const width=Math.round(view.width*dpr),height=Math.round(view.height*dpr),count=width*height;
 if(count>2097152)throw new RangeError('Diagnostic raster exceeds 2,097,152 pixels');
 const frame=observationFrame(observer),radiance=new Float64Array(count),skyFraction=new Float32Array(count),missing=new Uint8Array(count),n=samplesPerAxis,den=n*n;
 let skyPixels=0,missingPixels=0;
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const at=y*width+x;let value=0,sky=0,absent=false;
  for(let sy=0;sy<n;sy++)for(let sx=0;sx<n;sx++){
   // Use the actual rounded raster dimensions, so CSS footprint stays fixed at fractional DPR.
   const ray=diffuseRayToMap((x+(sx+.5)/n)*view.width/width,(y+(sy+.5)/n)*view.height/height,view,frame);
   if(!ray.aboveHorizon)continue;sky++;
   const s=sampler.sample(ray.raDeg,ray.decDeg);if(!s.defined)absent=true;else value+=s.value;
  }
  skyFraction[at]=sky/den;if(sky)skyPixels++;
  if(absent){missing[at]=1;missingPixels++;radiance[at]=0;}else radiance[at]=value/den;
 }
 return {width,height,dpr,radiance,skyFraction,missing,skyPixels,missingPixels,diagnosticOnly:true,productionAdmissible:false,utcMs:observer.utcMs,frameWarnings:[...frame.warnings],sourceId:sampler.id,sourceSha256:sampler.sourceSha256,quantity:sampler.quantity,exposureModel:'not-applied; viewer must label its diagnostic display stretch',physicalComposition:'NOT_IMPLEMENTED_IN_CP7_3'};
}

/** CP7.5: same inverse frame arithmetic with fixed lat/LST/velocity hoisted.
 * A private observer/frame snapshot is compiled afresh for every physical render.
 * Refraction's inherited inverse and aberration algorithms are unchanged.
 */
export function prepareHorizontalToDiffuseJ2000(observerOrFrame){
 const f=dfFrame(observerOrFrame),o={...f.observer},p=f.latDeg*DEG,t=f.lstDeg*DEG;
 const cp=Math.cos(p),sp=Math.sin(p),ct=Math.cos(t),st=Math.sin(t),rotation=f.rotation.map(c=>[...c]),aberration=f.aberration,velocity=f.velocityOverC.map(x=>-x);
 return horizontal=>{
  finite(horizontal?.altDeg,'horizontal altitude',-90,90);finite(horizontal?.azDeg,'horizontal azimuth');
  const alt=dfUndoRefraction(horizontal.altDeg,o)*DEG,az=horizontal.azDeg*DEG,e=Math.cos(alt)*Math.sin(az),n=Math.cos(alt)*Math.cos(az),u=Math.sin(alt),meridian=u*cp-n*sp;
  const date=[meridian*ct-e*st,meridian*st+e*ct,n*cp+u*sp];let v=rotation.map(c=>dot(c,date));
  if(aberration)v=aberrate(v,velocity);return unit(v);
 };
}
