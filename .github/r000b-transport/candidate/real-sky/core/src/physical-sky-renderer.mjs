/** Joined REFERENCE compositor: atmospheric direct source transport, additive sky radiance,
 * explicit physical occultation, separate calendar/foreground mask, one display transform.
 * This is not a patch applied to the real widget. Host cloud maps must be pure functions
 * of the supplied direction/time and return total LOS transmission, never another alpha pass.
 */
import {finite,DEG,wrapDeg,angularSeparation} from './astronomy.mjs';
import {unprojectAllSky,unprojectPerspective,cameraGeometry,prepareInverseProjection} from './projection.mjs';
import {normaliseAtmosphere,directTransmission,cloudTransmissionFor,horizontalDirection} from './atmosphere.mjs';
import {physicalSkyState} from './sky-state.mjs';
import {createSkyModel,V_ZERO_ILLUMINANCE_LUX} from './sky-background.mjs';
import {spectralStarFlux} from './spectral.mjs';
import {scintillationFactor,displayVisibility} from './visibility.mjs';
import {renderStars} from './renderer.mjs';
import {luminance,linearToSrgb} from './photometry.mjs';
import {createDiffuseTransport,renderDiffuseLayer} from './diffuse-transport.mjs';
export function skyProjection(view={}){
 const width=finite(view.width??325,'width CSS',8,4096),height=finite(view.height??530,'height CSS',8,4096),type=view.type??'camera',c={...view,width,height};
 if(type==='camera'){const unproject=prepareInverseProjection({...c,type});const f=cameraGeometry(c).focalPixels,cx=width/2,cy=height/2,fw=unprojectPerspective(cx,cy,c).enu,right=unprojectPerspective(cx+f,cy,c).enu.map((x,i)=>x*Math.SQRT2-fw[i]),up=unprojectPerspective(cx,cy-f,c).enu.map((x,i)=>x*Math.SQRT2-fw[i]);return {width,height,unproject,solidAngle:(x,y)=>f/(f*f+(x-cx)**2+(y-cy)**2)**1.5,above:(x,y)=>{
  // Reconstructed basis roundoff must not zero an exact-horizon grid row.
  // The uncertainty band selects the exact existing ray test, not an altitude tolerance.
  const z=fw[2]+(x-cx)/f*right[2]+(cy-y)/f*up[2];
  return Math.abs(z)>1e-12?z>0:unproject(x,y).altDeg>=0;
 }};}
 if(type==='allsky'){const unproject=prepareInverseProjection({...c,type});const padding=finite(view.padding??4,'all-sky padding',0,Math.min(width,height)/2-1e-9),R=Math.min(width,height)/2-padding,k=Math.PI/2/R;return {width,height,unproject,solidAngle:(x,y)=>{const t=Math.hypot(x-width/2,y-height/2)*k;return k*k*(t<1e-10?1:Math.sin(t)/t);},above:(x,y)=>Math.hypot(x-width/2,y-height/2)<=R};}
 if(type==='legacy'){if(width!==325||height!==530)throw new RangeError('Legacy crop requires 325x530');const k=Math.PI/2/270;return {width,height,unproject:(x,y)=>{const dx=162-x,dy=(y+30)/.8,r=Math.hypot(dx,dy);return {altDeg:90-r/270*90,azDeg:wrapDeg(Math.atan2(dx,dy)/DEG)};},solidAngle:(x,y)=>{const t=Math.hypot(x-162,(y+30)/.8)*k;return k*k/.8*(t<1e-10?1:Math.sin(t)/t);},above:(x,y)=>Math.hypot(x-162,(y+30)/.8)<=270};}
 throw new RangeError('Unknown sky projection');
}
/** Single site-height owner for stellar astrometry, atmosphere and illumination.
 * Missing weather elevation inherits the observer; contradictory explicit values fail. */
export function resolveSkyInputs(observer,atmosphere={}){
 if(!observer||typeof observer!=='object')throw new TypeError('Observer is required');
 if(!atmosphere||typeof atmosphere!=='object')throw new TypeError('Atmosphere must be an object');
 const site=observer.heightM??observer.elevationM??atmosphere.elevationM??0;
 finite(site,'site elevation metres',-500,10000);
 if(observer.heightM!=null&&observer.elevationM!=null&&observer.heightM!==observer.elevationM)throw new RangeError('Conflicting observer elevations');
 if(atmosphere.elevationM!=null&&atmosphere.elevationM!==site)throw new RangeError('Observer and atmospheric elevation disagree');
 return {observer:{...observer,heightM:site},atmosphere:normaliseAtmosphere(atmosphere.elevationM===site?atmosphere:{...atmosphere,elevationM:site})};
}
export function renderPhysicalSky(sources,{observer,view={},atmosphere={},physicalState=null,dpr=1,nominalExposure=24,autoExposure=true,opticalPreset='reference',response='CIE1931',cloudAt=null,displayTransmissionAt=null,reducedMotion=true,scintillation={},backgroundStepCss=6,diffuse=null}={}){
 finite(dpr,'DPR',.5,4);finite(nominalExposure,'nominal exposure',0,100000);finite(backgroundStepCss,'background sample step CSS',1,16);
 const mapping=skyProjection(view),width=mapping.width,height=mapping.height,w=Math.round(width*dpr),h=Math.round(height*dpr);if(w*h>8000000)throw new RangeError('Reference raster exceeds memory budget');
 if(diffuse!=null&&diffuse!==false&&diffuse.enabled!==false&&w*h>2097152)throw new RangeError('Physical diffuse raster exceeds 2,097,152-pixel budget');
 const resolved=resolveSkyInputs(observer,atmosphere);observer=resolved.observer;const a=resolved.atmosphere,state=physicalState??physicalSkyState(observer);
 if(physicalState&&(physicalState.utcMs!==observer.utcMs||typeof physicalState.source!=='string'||!physicalState.source.trim()))throw new RangeError('External physical sky state requires matching UTC and source provenance');
 const diffuseModel=diffuse!=null&&diffuse!==false&&diffuse.enabled!==false?createDiffuseTransport(diffuse,{observer,atmosphere:a,state,cloudAt}):null;
 if(diffuseModel&&!['V-monochrome','CIE1931'].includes(response))throw new RangeError('Unknown physical response model');
 const sky=createSkyModel(state,a,{cloudAt,...(diffuseModel?{residualNight:diffuseModel.residualNight}:{})}),gx=Math.ceil(width/backgroundStepCss),gy=Math.ceil(height/backgroundStepCss),grid=new Float64Array((gx+1)*(gy+1)*3);
 for(let j=0;j<=gy;j++)for(let i=0;i<=gx;i++){const x=i*width/gx,y=j*height/gy;if(!mapping.above(x,y))continue;const direction=mapping.unproject(x,y),sample=sky.sample(direction),omega=mapping.solidAngle(x,y),off=(j*(gx+1)+i)*3;for(let c=0;c<3;c++)grid[off+c]=(response==='V-monochrome'?sample.luminance:sample.rgb[c])*omega/V_ZERO_ILLUMINANCE_LUX;}
 const background=new Float64Array(w*h*3),densityScale=diffuseModel?width/w*height/h*dpr*dpr:1;let meanY=0,skyPixels=0;
 for(let j=0;j<h;j++)for(let i=0;i<w;i++){const x=diffuseModel?(i+.5)*width/w:(i+.5)/dpr,y=diffuseModel?(j+.5)*height/h:(j+.5)/dpr;if(!mapping.above(x,y))continue;const u=x/width*gx,v=y/height*gy,ix=Math.min(gx-1,Math.floor(u)),iy=Math.min(gy-1,Math.floor(v)),tx=u-ix,ty=v-iy,off=(j*w+i)*3,tl=(iy*(gx+1)+ix)*3,bl=tl+(gx+1)*3;
  for(let c=0;c<3;c++)background[off+c]=(grid[tl+c]*(1-tx)+grid[tl+3+c]*tx)*(1-ty)+(grid[bl+c]*(1-tx)+grid[bl+3+c]*tx)*ty;
  if(diffuseModel)for(let c=0;c<3;c++)background[off+c]*=densityScale;
  meanY+=.2126*background[off]+.7152*background[off+1]+.0722*background[off+2];skyPixels++;
 }
 let diffuseRaster=null,totalBackground=background;
 if(diffuseModel){
  diffuseRaster=renderDiffuseLayer(diffuseModel,mapping,{widthPx:w,heightPx:h,dpr,displayTransmissionAt});totalBackground=new Float64Array(background.length);
  for(let i=0;i<background.length;i++){totalBackground[i]=background[i]+diffuseRaster.linear[i];if(i%3===0)meanY+=diffuseRaster.physicalLinear[i];}
  skyPixels=diffuseRaster.skyPixelsEquivalent;
 }
 meanY/=Math.max(1,skyPixels);const effectiveExposure=autoExposure?nominalExposure/(1+nominalExposure*meanY/.5):nominalExposure,diagnostics=[],moonVector=horizontalDirection(state.moon);
 const raster=renderStars(sources,{width,height,dpr,opticalPreset,response,utcMs:observer.utcMs,reducedMotion:true,scintillationAmplitude:0,
  sourceVisibility:s=>diffuseModel?!diffuseModel.occulted(s):state.moon.altDeg+(state.moon.angularRadiusDeg??.25)<0||angularSeparation(horizontalDirection(s),moonVector)>(state.moon.angularRadiusDeg??.25),
  fluxAt:s=>{const cloud=cloudTransmissionFor(s,a,cloudAt,state.utcMs),f=spectralStarFlux(s,s.altDeg,{}, {response,transportAt:lambda=>directTransmission(lambda,s.altDeg,a,cloud)}),displayMask=displayTransmissionAt?finite(displayTransmissionAt(s.x,s.y),'display mask',0,1):1,ds=diffuseModel?.sample(s),diffuseBackgroundY=ds?(ds.relativeV0PerSr??0)*mapping.solidAngle(s.x,s.y)*displayMask:0,backgroundY=sky.sample(s).luminance*mapping.solidAngle(s.x,s.y)/V_ZERO_ILLUMINANCE_LUX+diffuseBackgroundY,
   visibility=displayVisibility(luminance(f.rgb)*displayMask,backgroundY,effectiveExposure),tw=scintillationFactor(s.id??s.hip,observer.utcMs/1000,s.altDeg,{...scintillation,reducedMotion});
   diagnostics.push({id:s.id??s.hip,hip:s.hip,vmag:s.vmag,vFlux:f.vFlux,cloudTransmission:cloud,backgroundY,scintillationFactor:tw,...visibility,...(ds?{diffuseBackgroundY,backgroundComplete:ds.defined||displayMask===0,diffuseSourceDefined:ds.sourceDefined,diffuseEstimatedFraction:ds.estimatedFraction}:{})});return {...f,rgb:f.rgb.map(x=>x*tw)};},pixelTransmissionAt:displayTransmissionAt});
 const stellarLinear=raster.linear,linear=new Float64Array(stellarLinear.length);for(let i=0;i<linear.length;i++)linear[i]=stellarLinear[i]+totalBackground[i];
 let diffuseFields={};
 if(diffuseModel){
  let increment=0,visiblePixels=0;const weights=[.2126,.7152,.0722];
  for(let i=0;i<background.length;i+=3){let delta=0;for(let c=0;c<3;c++)delta+=weights[c]*(linearToSrgb(-Math.expm1(-effectiveExposure*totalBackground[i+c]))-linearToSrgb(-Math.expm1(-effectiveExposure*background[i+c])));increment+=delta;if(delta>=2/255)visiblePixels++;}
  diffuseFields={skyBackgroundLinear:background,diffuseLinear:diffuseRaster.linear,diffusePhysicalLinear:diffuseRaster.physicalLinear,diffuseMasks:diffuseRaster.masks,diffuseState:{enabled:true,sourceId:diffuseModel.sourceId,sourceSha256:diffuseModel.sourceSha256,catalogueSha256:diffuseModel.catalogueSha256,utcMs:observer.utcMs,transportAssumption:diffuseModel.transportAssumption,colourModel:diffuseModel.colourModel,allowEstimates:diffuseModel.allowEstimates,samplesPerAxis:diffuseModel.samplesPerAxis,missingPixels:diffuseRaster.missingPixels,estimatedPixels:diffuseRaster.estimatedPixels,exposureComplete:diffuseRaster.missingPixels===0,exposureMetering:'sky plus direct diffuse BEFORE calendar/display mask; excludes point sources as in CP6',meanDisplayIncrement:increment/Math.max(1,skyPixels),displayVisiblePixels:visiblePixels,budget:diffuseRaster.budget,nightBudget:sky.nightBudget,frameWarnings:diffuseModel.frameWarnings},provisionalSourceDiagnostics:diagnostics.filter(d=>d.backgroundComplete===false).length};
 }
 const zenithBase=sky.sample({altDeg:90,azDeg:0}),zenithDiffuse=diffuseModel?.sample({altDeg:90,azDeg:0}),zenithSky=zenithDiffuse?{...zenithBase,atmosphericLuminance:zenithBase.luminance,diffuseLuminance:zenithDiffuse.luminance,luminanceIsLowerBound:!zenithDiffuse.defined,luminance:zenithBase.luminance+(zenithDiffuse.luminance??0),rgb:zenithBase.rgb.map(x=>x+(zenithDiffuse.luminance??0)),complete:zenithDiffuse.defined,diffuseEstimatedFraction:zenithDiffuse.estimatedFraction}:zenithBase;
 return {...raster,...diffuseFields,linear,stellarLinear,backgroundLinear:totalBackground,effectiveExposure,nominalExposure,meanBackgroundY:meanY,detectableSources:diagnostics.filter(x=>x.detectable&&x.backgroundComplete!==false).length,sourceDiagnostics:diagnostics,physicalState:state,atmosphere:a,zenithSky,skyModels:diffuseModel?{...sky.models,diffuse:'registered V starlight; one effective-V direct transport + physical occultation'}:sky.models,modelWarnings:diffuseModel?[...sky.warnings,diffuseModel.transportAssumption,'Diffuse output is a neutral V-equivalent channel; source estimates/absences retained','No diffuse in-scattering or independently calibrated nonstellar night spectrum']:sky.warnings,solarNodes:sky.solarNodeCount(),representation:'V-anchored stellar flux + photopic-equivalent sky radiance in CSS-pixel solid angle; encode once'};
}
