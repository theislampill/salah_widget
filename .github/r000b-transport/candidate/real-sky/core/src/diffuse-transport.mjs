/** CP7.4 direct extra-atmospheric V integrated starlight -> observer.
 * No spectrum is inferred from one band. Effective V transmission uses the SAME
 * CP5 Bessell photon-counting passband and retained Vega weighting as a declared
 * IN-BAND ASSUMPTION. Do not call the resulting neutral channel measured RGB.
 */
import {finite,DEG,dot,observationFrame,vectorRaDec} from './astronomy.mjs';
import {horizontalToDiffuseJ2000,diffuseGeometricAltitude,prepareHorizontalToDiffuseJ2000} from './diffuse-map.mjs';
import {normaliseAtmosphere,rayleighOpticalDepth,aerosolOpticalDepth,cloudTransmissionFor,horizontalDirection} from './atmosphere.mjs';
import {airmass} from './photometry.mjs';
import {SPECTRAL_TABLES} from './spectral-tables.mjs';
import {validateResidualNight,V_ZERO_ILLUMINANCE_LUX} from './sky-background.mjs';
import {isBoundRegisteredStarlight} from './diffuse-binding.mjs';
export const DIFFUSE_TRANSPORT_ASSUMPTION='Vega-weighted effective Bessell V transmission; assumed in-band SED, neutral V-equivalent output';
/** 0.1-degree lookup; exact() is retained for independent comparisons and controls. */
export function createVBandTransmission(atmosphere={}){
 const a=normaliseAtmosphere(atmosphere),t=SPECTRAL_TABLES,w=[],tau=[];
 let weightSum=0;
 for(let i=0;i<t.wavelengthNm.length;i++){
  const weight=t.standards[0].samples[i]*t.wavelengthNm[i]*t.passbands.V[i]*t.weightsNm[i];
  if(weight<=0)continue;const lambda=t.wavelengthNm[i];w.push(weight);weightSum+=weight;tau.push(rayleighOpticalDepth(lambda,a)+aerosolOpticalDepth(lambda,a)+a.greyTau);
 }
 for(let i=0;i<w.length;i++)w[i]/=weightSum;
 function exact(altDeg){finite(altDeg,'V transport altitude',-90,90);if(altDeg<0)return 0;const X=airmass(altDeg);let T=0;for(let i=0;i<w.length;i++)T+=w[i]*Math.exp(-X*tau[i]);return Math.max(0,Math.min(1,T));}
 const lut=Float64Array.from({length:901},(_,i)=>exact(i/10));
 function sample(altDeg){finite(altDeg,'V transport altitude',-90,90);if(altDeg<0)return 0;const u=altDeg*10,i=Math.min(899,Math.floor(u)),f=u-i;return lut[i]*(1-f)+lut[i+1]*f;}
 function spectralEnvelope(altDeg){finite(altDeg,'V transport altitude',0,90);const X=airmass(altDeg);return {minimum:Math.exp(-X*Math.max(...tau)),maximum:Math.exp(-X*Math.min(...tau)),meaning:'possible in-band weighting bounds, not a statistical confidence interval'};}
 return Object.freeze({sample,exact,spectralEnvelope,assumption:DIFFUSE_TRANSPORT_ASSUMPTION,lookupStepDeg:.1});
}
export function createDiffuseTransport(diffuse,{observer,atmosphere={},state,cloudAt=null}={}){
 if(!isBoundRegisteredStarlight(diffuse?.binding))throw new TypeError('Verified bound registered-starlight context required');
 const residualNight=validateResidualNight(diffuse.residualNight),a=normaliseAtmosphere(atmosphere),sampler=diffuse.binding.sampler;
 const allowEstimates=diffuse.allowEstimates??true,filter=diffuse.filter??'linear',samplesPerAxis=diffuse.samplesPerAxis??2;
 if(typeof allowEstimates!=='boolean'||!['linear','nearest'].includes(filter)||!Number.isInteger(samplesPerAxis)||samplesPerAxis<1||samplesPerAxis>4)throw new TypeError('Invalid physical diffuse sampling policy');
 if(!state||state.utcMs!==observer?.utcMs)throw new RangeError('Diffuse physical state UTC must match accepted observer UTC');
 if(state.moon?.geometric===false)throw new TypeError('Diffuse occultation requires geometric physical Moon directions');
 const frame=observationFrame(observer),toJ2000=prepareHorizontalToDiffuseJ2000(frame),moonVector=horizontalDirection(state.moon),radius=finite(state.moon.angularRadiusDeg??.25,'physical lunar radius',.01,2),moonCos=Math.cos(radius*DEG),moonAbove=state.moon.altDeg+radius>=0,gas=createVBandTransmission(a);
 function occulted(h){if(!moonAbove)return false;const alt=h.geometricAltDeg??diffuseGeometricAltitude(h.altDeg,frame);return dot(horizontalDirection({altDeg:alt,azDeg:h.azDeg}),moonVector)>=moonCos;}
 function sample(h){
  horizontalDirection(h);
  if(h.altDeg<0)return {defined:true,sourceDefined:true,incomingRelativeV0PerSr:0,relativeV0PerSr:0,luminance:0,gasTransmission:0,cloudTransmission:0,estimatedFraction:0,occulted:false,ground:true};
  const eq=vectorRaDec(toJ2000(h)),s=sampler.sample(eq.raDeg,eq.decDeg,{filter,allowEstimates}),T=gas.sample(h.altDeg),C=cloudTransmissionFor(h,a,cloudAt,state.utcMs),occ=occulted(h);
  const known=occ||T*C===0||s.defined,value=known?(occ||T*C===0?0:s.relativeV0PerSr*T*C):null;
  return {defined:known,sourceDefined:s.defined,incomingRelativeV0PerSr:s.relativeV0PerSr,relativeV0PerSr:value,luminance:value===null?null:value*V_ZERO_ILLUMINANCE_LUX,gasTransmission:T,cloudTransmission:C,estimatedFraction:s.estimatedFraction,occulted:occ,raDeg:eq.raDeg,decDeg:eq.decDeg};
 }
 return Object.freeze({sample,occulted,gas,residualNight,samplesPerAxis,allowEstimates,filter,sourceId:sampler.id,sourceSha256:sampler.sourceSha256,catalogueSha256:sampler.catalogueSha256,utcMs:observer.utcMs,frameWarnings:frame.warnings,transportAssumption:DIFFUSE_TRANSPORT_ASSUMPTION,colourModel:'neutral V-equivalent proxy, not measured CIE colour'});
}
/** Integrate L/F0 over each actual raster-pixel solid angle, then multiply by DPR²
 * to match CP5's integrated point-flux convention. Never multiply the radiance by
 * solid angle again during composition. Missing rays are omitted without renormalising
 * remaining support and are carried as a separate incomplete-pixel mask.
 */
export function renderDiffuseLayer(model,mapping,{widthPx,heightPx,dpr=1,displayTransmissionAt=null}={}){
 const count=widthPx*heightPx;if(!Number.isInteger(widthPx)||!Number.isInteger(heightPx)||widthPx<1||heightPx<1||count>2097152)throw new RangeError('Physical diffuse raster exceeds 2,097,152-pixel budget');
 finite(dpr,'diffuse DPR',.5,4);if(displayTransmissionAt!=null&&typeof displayTransmissionAt!=='function')throw new TypeError('Display transmission must be a pure callback');
 const physicalLinear=new Float64Array(count*3),linear=new Float64Array(count*3),skyFraction=new Float32Array(count),estimatedFraction=new Float32Array(count),occultedFraction=new Float32Array(count),missing=new Uint8Array(count);
 const n=model.samplesPerAxis,den=n*n,dx=mapping.width/widthPx,dy=mapping.height/heightPx,scale=dx*dy*dpr*dpr/den;
 const budget={incoming:0,afterGas:0,afterCloud:0,afterPhysicalMoon:0,afterDisplayMask:0,units:'integrated relative V0 flux over the view',complete:true};
 let skyPixelsEquivalent=0,missingPixels=0,estimatedPixels=0;
 for(let y=0;y<heightPx;y++)for(let x=0;x<widthPx;x++){
  const pixel=y*widthPx+x;let pre=0,post=0,sky=0,est=0,occ=0,absent=false;
  for(let sy=0;sy<n;sy++)for(let sx=0;sx<n;sx++){
   const px=(x+(sx+.5)/n)*dx,py=(y+(sy+.5)/n)*dy;
   if(!mapping.above(px,py))continue;
   const h=mapping.unproject(px,py);if(h.altDeg<0)continue;sky++;
   const s=model.sample(h),weight=mapping.solidAngle(px,py)*scale;
   const display=displayTransmissionAt?finite(displayTransmissionAt(px,py),'display mask',0,1):1;
   est+=s.estimatedFraction;occ+=s.occulted?1:0;
   if(!s.sourceDefined)budget.complete=false;
   if(s.sourceDefined){const incoming=s.incomingRelativeV0PerSr*weight;budget.incoming+=incoming;budget.afterGas+=incoming*s.gasTransmission;budget.afterCloud+=incoming*s.gasTransmission*s.cloudTransmission;}
   if(!s.defined){absent=true;continue;}
   const transmitted=s.relativeV0PerSr*weight;pre+=transmitted;post+=transmitted*display;
  }
  for(let c=0;c<3;c++){physicalLinear[pixel*3+c]=pre;linear[pixel*3+c]=post;}
  skyFraction[pixel]=sky/den;estimatedFraction[pixel]=sky?est/sky:0;occultedFraction[pixel]=occ/den;
  skyPixelsEquivalent+=sky/den;if(est>0)estimatedPixels++;
  if(absent){missing[pixel]=1;missingPixels++;}
  budget.afterPhysicalMoon+=pre;budget.afterDisplayMask+=post;
 }
 for(const k of ['incoming','afterGas','afterCloud','afterPhysicalMoon','afterDisplayMask'])budget[k]/=dpr*dpr;
 return {physicalLinear,linear,masks:{skyFraction,estimatedFraction,occultedFraction,missing},skyPixelsEquivalent,missingPixels,estimatedPixels,budget};
}
