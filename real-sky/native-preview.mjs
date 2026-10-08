import {nativeJob} from './native-contract.mjs';
import {physicalSkyState} from './core/src/sky-state.mjs';
import {createSkyModel,patatTwilight,V_ZERO_ILLUMINANCE_LUX} from './core/src/sky-background.mjs';
import {selectSpectrum,spectrumToXYZ,gamutMapXYZ} from './core/src/spectral.mjs';
import {skyProjection} from './core/src/physical-sky-renderer.mjs';
import {projectPerspective} from './core/src/projection.mjs';
import {phaseHG,horizontalDirection} from './core/src/atmosphere.mjs';

// Only rigid pixel geometry is reusable. No UTC, celestial direction, radiance,
// exposure, weather or admitted frame is cached here. At600x the old display
// pass retraced thousands of identical camera rays on each publication and
// could exhaust the unchanged30-second age fence. Keep the exact reference
// arithmetic (including its angular round trip), bounded to four native-sized
// cameras. Camera changes invalidate the key; arbitrary sample positions still
// use the direct inverse projection. Arrays stay private to this module.
const displayGeometryCache=new Map();
function displayGeometry(view){
 const c={type:view.type??'camera',width:view.width??325,height:view.height??530,azDeg:view.azDeg??180,altDeg:view.altDeg??35,fovYDeg:view.fovYDeg??90,rollDeg:view.rollDeg??0};
 const key=JSON.stringify(c),cached=displayGeometryCache.get(key);
 if(c.type==='camera'&&cached)return cached;
 const mapping=skyProjection(view),w=mapping.width,h=mapping.height,reference=mapping.solidAngle(w/2,h/2),bounded=c.type==='camera'&&Number.isInteger(w)&&Number.isInteger(h)&&w*h<=325*530;
 const rays=bounded?new Float64Array(w*h*3):null,scales=bounded?new Float64Array(w*h):null,ready=bounded?new Uint8Array(w*h):null;
 const value={mapping,scale(x,y){const p=(y-.5)*w+x-.5;if(!bounded)return reference/mapping.solidAngle(x,y);return scales[p]||(scales[p]=reference/mapping.solidAngle(x,y));},cosine(x,y,v){
  const px=x-.5,py=y-.5,p=py*w+px;
  if(!bounded||!Number.isInteger(px)||!Number.isInteger(py)||px<0||py<0||px>=w||py>=h){const ray=horizontalDirection(mapping.unproject(x,y));return Math.max(-1,Math.min(1,ray[0]*v[0]+ray[1]*v[1]+ray[2]*v[2]));}
  const i=p*3;if(!ready[p]){rays.set(horizontalDirection(mapping.unproject(x,y)),i);ready[p]=1;}
  return Math.max(-1,Math.min(1,rays[i]*v[0]+rays[i+1]*v[1]+rays[i+2]*v[2]));
 }};
 if(bounded){if(displayGeometryCache.size===4)displayGeometryCache.delete(displayGeometryCache.keys().next().value);displayGeometryCache.set(key,value);}
 return value;
}

// The native Sun is an intentionally enlarged body in a fixed display slot.
// Register its aerosol aureole's angular presentation to that slot as well.
// Rayleigh/path extinction/physical Sun and catalogue remain unchanged. Move
// only the phase-function centre; never drag the horizon or below-ground pixels
// through the card by translating a whole sky texture.
export function nativeSolarRegistration(raster,view={type:'camera',width:325,height:530,azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},anchor=null){
 const sun=raster.physicalState?.sun,source=Number.isFinite(sun?.azDeg)&&view.type==='camera'?projectPerspective(sun,view):null;
 const target=anchor??{x:20,y:40+176*(1-Math.min(1,Math.max(0,(sun?.altDeg??0)/40)))};
 // The native Sun remains visible while its physical direction crosses the
 // camera boundary. A frustum boolean must not switch its display aureole on
 // or off: that produced a second white centre and a 22-code jump at x=0.
 const active=!!(sun?.altDeg>10&&Number.isFinite(sun?.azDeg)&&view.type==='camera'&&target.x>0&&target.y>0&&target.x<raster.width&&target.y<raster.height);
 const presence=Math.min(1,Math.max(0,anchor?.presence??((sun?.altDeg??-90)+1.5)/7));
 const geometry=active?displayGeometry(view):null,physical=active?horizontalDirection(sun):null,display=active?horizontalDirection(geometry.mapping.unproject(target.x,target.y)):null,g=raster.atmosphere?.aerosolG??.76;
 return {active,source,target,presence,gain:(x,y)=>{
  if(!active)return 1;
  const original=phaseHG(geometry.cosine(x,y,physical),g),relocated=phaseHG(geometry.cosine(x,y,display),g),isotropic=1/(4*Math.PI);
  // Only the forward excess above the isotropic phase density belongs to
  // the enlarged Sun's presentation aureole. Relocating the whole HG field
  // also moved its broad non-forward wing, warming open sky and changing
  // its exposure meter. Keep that atmospheric background in camera space.
  // This is an explicit display decomposition, not new measured radiance;
  // the physical field and its full phase function remain untouched.
  // Twilight's entire field stays tied to physical azimuth. Relocating it at
  // +6deg then returning it by0deg made the warm centre migrate across sunset.
  // The existing twilight colour/display domain ends at+10deg. Release into
  // the established daytime decorative aureole over the next10deg with zero
  // endpoint slope. This is a display handoff, never an ephemeris change.
  const u=Math.min(1,Math.max(0,(sun.altDeg-10)/10)),weight=u*u*(3-2*u)*presence;
  return 1+weight*((Math.min(original,isotropic)+Math.max(0,relocated-isotropic))/original-1);
 }};
}

/** Directional native cloud illumination. The painter is a display model;
 * these are camera rays and a cosine facing term, not volumetric photometry.
 * Tangent derivatives avoid projection infinities/flips for an off-camera Sun.
 */
export function nativeCloudSolarLighting(snapshot){
 const job=nativeJob(snapshot,true),sun=physicalSkyState(job.observer).sun,view=job.options.view,mapping=skyProjection(view),s=horizontalDirection(sun);
 const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
 return {sun,utcMs:snapshot.utcMs,camera:view,owner:'accepted physical Sun and rigid sky camera; cosine cloud-facing display approximation',sample(u,v){
  const x=u*view.width,y=v*view.height,ray=mapping.unproject(x,y).enu;
  const dx=dot(mapping.unproject(x+.5,y).enu,s)-dot(mapping.unproject(x-.5,y).enu,s),dy=dot(mapping.unproject(x,y+.5).enu,s)-dot(mapping.unproject(x,y-.5).enu,s),length=Math.hypot(dx,dy);
  return {facing:Math.max(0,dot(ray,s)),dx:length?dx/length:0,dy:length?dy/length:0};
 }};
}

/** Atmospheric display only. The numerical radiance, catalogue, worker exposure
 * and lunar material stay intact. Mean full-field metering lets a bright horizon
 * or forward-scattering lobe darken open daytime sky. Meter its median instead;
 * tone-map luminance then scale RGB together, preserving spectral chromaticity
 * instead of compressing blue independently toward grey. Twilight additionally
 * uses the explicit reference colour adaptation documented below.
 */
export function nativeSkyPresentation(raster,view,anchor){
 const altitude=raster.physicalState?.sun?.altDeg;
 if(!Number.isFinite(altitude)||(altitude<=-18&&!raster.solarBackgroundLinear?.some(v=>v>0)))return raster;
 const source=raster.skyBackgroundLinear??raster.backgroundLinear,E=raster.effectiveExposure;
 if(!source||source.length!==raster.linear.length||!Number.isFinite(E)||E<=0)throw new RangeError('Daylight display requires valid atmospheric field');
 const t=Math.min(1,Math.max(0,(altitude+18)/6)),strength=t*t*(3-2*t),registration=nativeSolarRegistration(raster,view,anchor),w=raster.width,h=raster.height;
 // Register only solar aerosol scattering. Moving the whole field would drag
 // the neutral horizon into blue open sky. Rayleigh, night and lunar fields
 // retain their original camera coordinates. This decomposition uses the SAME
 // scattering integrator and extinction, differing only in source albedo.
 const aureole=raster.solarAerosolLinear,shown=Float64Array.from(source),colour=raster.twilightDisplay;
 const solarShown=raster.solarBackgroundLinear?Float64Array.from(raster.solarBackgroundLinear):null;
 if(aureole&&registration.active)for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  const gain=registration.gain(x+.5,y+.5),i=(y*w+x)*3;
  for(let c=0;c<3;c++)shown[i+c]=Math.max(0,source[i+c]+aureole[i+c]*(gain-1));
 }
 // The reference background is integrated FLUX per perspective pixel. The
 // widget presents surface brightness, not a lens with solid-angle vignetting.
 // Normalize this display copy to the central pixel's solid angle before
 // metering. Keep raw flux, point-source photometry and camera rays intact.
 const metered=Float64Array.from(source),camera=view??{type:'camera',width:w,height:h,azDeg:180,altDeg:45,fovYDeg:90},geometry=w>=8&&h>=8&&camera.type==='camera'?displayGeometry({...camera,width:w,height:h}):null,projection=geometry?.mapping;
 if(projection){
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){const gain=geometry.scale(x+.5,y+.5),i=(y*w+x)*3;for(let c=0;c<3;c++){shown[i+c]*=gain;metered[i+c]*=gain;if(solarShown)solarShown[i+c]*=gain;}}
 }
 // CP6's empirical twilight fills a luminance deficit only. When spherical
 // single scattering already meets that V luminance, its much redder colour
 // dominates despite CP6's retained near-zenith B-V reference. This calendar
 // DISPLAY adaptation uses that existing reference as a white-point ratio,
 // retaining directional differences and luminance. It is not extra radiance,
 // a local observation, or a repair/claim of a multiple-scattering solver.
 if(colour)for(let i=0;i<shown.length;i+=3){
  const y=.2126*shown[i]+.7152*shown[i+1]+.0722*shown[i+2];
  for(let k=0;k<3;k++){shown[i+k]*=colour.gains[k];if(solarShown)solarShown[i+k]*=colour.gains[k];}
  const y2=.2126*shown[i]+.7152*shown[i+1]+.0722*shown[i+2];
  if(y2>0)for(let k=0;k<3;k++){shown[i+k]*=y/y2;if(solarShown)solarShown[i+k]*=y/y2;}
 }
 // Meter the accepted physical atmosphere, before decorative registration.
 // An enlarged Sun's display lobe is not a change in ambient illumination.
 const ys=[];for(let i=0;i<metered.length;i+=3){const y=.2126*metered[i]+.7152*metered[i+1]+.0722*metered[i+2];if(!Number.isFinite(y)||y<0)throw new RangeError('Invalid sky luminance');if(y>0)ys.push(y);}
 if(!ys.length)return raster;
 ys.sort((a,b)=>a-b);const median=ys[Math.floor(ys.length/2)],nominal=raster.nominalExposure??24;
 // A fixed-midgrey auto meter compensated almost all of the falling twilight
 // radiance: the Sun disappeared while the remaining warm field got brighter.
 // Below the civil-twilight display adaptation reference, allow only half
 // that gain change (geometric mean in exposure stops). Reference: the retained
 // -5 degree zenith fit maps to9% display grey (one stop below photographic
 // middle grey), not daylight's fixed50% meter target. The matched V1 clear
 // open-sky control is6.6% linear Y; joined acceptance bounds are2.5..14%.
 // This is an explicit calendar readability/exposure choice, not a physical
 // radiance adjustment. It replaces the rejected arbitrary1000 cd/m² trial.
 // This display convention is NOT a change to measured/reference radiance. Bright
 // daytime above this reference and deep night retain their existing mapping.
 // Flux units use the native325x530 reference pixel even for a reduced preview.
 const referenceOmega=4*Math.tan((camera.fovYDeg??90)*Math.PI/360)**2/(530*530);
 const adaptationReferenceCdM2=patatTwilight(-5).excessLuminance*(.5/.09)**2;
 const adaptationReference=adaptationReferenceCdM2*referenceOmega/V_ZERO_ILLUMINANCE_LUX;
 const meter=Math.max(median,Math.sqrt(median*adaptationReference)),displayExposure=nominal/(1+nominal*meter/.5);
 // The single-scatter twilight field can contain a >10x median warm highlight
 // beside a dark field. The previous nearly linear low-light display mapped
 // that to an amber spotlight under the panel. Use a smooth photographic
 // shoulder, not a screen mask or a change to scientific radiance. Above the
 // half a stop over the field median it asymptotes to one stop; value and derivative
 // meet continuously. Remove ONLY solar light: natural/local/lunar background
 // cannot be relabelled as solar afterglow or reduced to satisfy this limit.
 // The existing empirical twilight activation (-3..-5deg) supplies a smooth
 // geometry-based weight. Daylight is byte-identical; deep night uses the
 // existing -18..-12 display blend. This is a declared calendar display range,
 // not calibrated horizon photometry. Stars and lunar surface are untouched.
 // The former two-stop ceiling retained a visibly concentrated lower-corner
 // patch even after its amber chroma was corrected. The one-stop display
 // range is a declared calendar contrast limit, not calibrated sky luminance.
 const sw=Math.min(1,Math.max(0,(-altitude-3)/2)),shoulderWeight=sw*sw*(3-2*sw),knee=Math.SQRT2*median,headroom=(2-Math.SQRT2)*median;
 let shoulderPixels=0;
 if(solarShown&&shoulderWeight>0)for(let i=0;i<shown.length;i+=3){
  const Y=.2126*shown[i]+.7152*shown[i+1]+.0722*shown[i+2];if(Y<=knee)continue;
  const excess=Y-knee,target=knee+excess/(1+excess/headroom);
  const S=.2126*solarShown[i]+.7152*solarShown[i+1]+.0722*solarShown[i+2];if(S<=0)continue;
  const removed=Math.min(S,(Y-target)*shoulderWeight)/S;
  for(let k=0;k<3;k++){shown[i+k]=Math.max(0,shown[i+k]-solarShown[i+k]*removed);solarShown[i+k]*=1-removed;}
  shoulderPixels++;
 }
 // The retained single-scattering horizon colour is not a calibrated
 // off-Sun twilight spectrum. A zenith-only white-point ratio left its red
 // grazing-path wing as an amber pool >60 degrees from the Sun. Preserve
 // luminance/direction and the solar-side warm lobe, but limit that *solar*
 // chroma to the existing twilight reference outside the forward excess.
 // This is a declared display gamut policy, not a new radiance model. Its
 // support is the physical camera ray / Sun angle, never a screen corner.
 // Non-solar sources, lunar material and daylight are unchanged.
 let chromaPixels=0;
 if(solarShown&&colour?.referenceRGB&&projection&&shoulderWeight>0){
  const sun=horizontalDirection(raster.physicalState.sun),g=raster.atmosphere?.aerosolG??.76,white=colour.referenceRGB;
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
   const i=3*(y*w+x),S=.2126*solarShown[i]+.7152*solarShown[i+1]+.0722*solarShown[i+2];
   if(S<=0||solarShown[i]*white[2]<=solarShown[i+2]*white[0])continue;
   const cos=geometry.cosine(x+.5,y+.5,sun);
   const forward=phaseHG(cos,g),weight=shoulderWeight*Math.min(1,1/(4*Math.PI*forward));
   for(let k=0;k<3;k++){
    const delta=weight*(S*white[k]-solarShown[i+k]);
    shown[i+k]=Math.max(0,shown[i+k]+delta);solarShown[i+k]=Math.max(0,solarShown[i+k]+delta);
   }
   chromaPixels++;
  }
 }
 const sky=new Float64Array(source.length),linear=new Float64Array(source.length);
 for(let i=0;i<source.length;i+=3){
  const Y=.2126*shown[i]+.7152*shown[i+1]+.0722*shown[i+2],scale=Y>0?-Math.expm1(-displayExposure*Y)/Y:0;
  const gamut=Math.max(1,shown[i]*scale,shown[i+1]*scale,shown[i+2]*scale);
  for(let c=0;c<3;c++){
   const old=-Math.expm1(-E*source[i+c]),mapped=shown[i+c]*scale/gamut;
   let display=old+(mapped-old)*strength;
   if(solarShown&&strength<1){
    // Recover the established natural/local/lunar night background, not the
    // uncorrected solar highlight. Blending the WHOLE raw field back over
    // -12..-18deg relit a falling western twilight lobe as an amber spotlight.
    // Keep solar light on the same continuous display path until it is absent;
    // only the independently owned non-solar contribution uses night mapping.
    // The resulting change is display-only; stars and lunar material are not
    // included. At strength1 (all accepted daylight/early-twilight) bytes match.
    const neutral=Math.max(0,source[i+c]-raster.solarBackgroundLinear[i+c]);
    const oldNeutral=-Math.expm1(-E*neutral),mappedNeutral=Math.max(0,shown[i+c]-solarShown[i+c])*scale/gamut;
    display=mapped+(oldNeutral-mappedNeutral)*(1-strength);
   }
   sky[i+c]=-Math.log1p(-Math.min(1-1/131072,display))/E;
   linear[i+c]=raster.linear[i+c]-source[i+c]+sky[i+c];
  }
 }
 return {...raster,linear,skyBackgroundLinear:sky,backgroundLinear:Float64Array.from(sky,(v,i)=>v+(raster.diffuseLinear?.[i]??0)),physicalSkyBackgroundLinear:source,
  displayPresentation:{owner:'native atmospheric display',policy:'perspective surface brightness; civil-twilight9% exposure reference; one-stop solar twilight highlight shoulder and directional chroma; luminance tone map and declared twilight colour adaptation; non-solar deep-night blend -18..-12 degrees',twilightColour:colour??null,twilightChroma:{pixels:chromaPixels,scope:'Solar warm chroma outside physical HG forward excess limited to retained twilight reference at fixed luminance; not calibrated directional spectroscopy'},twilightShoulder:{weight:shoulderWeight,kneeMedianMultiple:Math.SQRT2,asymptoticMedianMultiple:2,pixels:shoulderPixels,scope:'display-only solar highlight range; raw radiance and non-solar contributors preserved'},solarAltitudeDeg:altitude,strength,solidAnglePolicy:projection?'reference flux normalized to central-pixel solid angle for display only':'not a perspective raster',medianLuminance:median,adaptationReferenceCdM2,displayExposure,physicalExposure:E,solarRegistration:{active:!!aureole&&registration.active,presence:registration.presence,physical:registration.source,display:registration.target,scope:'twilight through+10deg remains physical; daytime forward excess blends to decorative light over+10..20deg; raw radiance, horizon, Rayleigh, lunar and catalogue projection unchanged'}}};
}

/** Bounded first-paint background, before catalogue/assets/worker readiness.
 * Same accepted observer, spherical spectral atmosphere and display owner as
 * the refined frame. Only spatial sampling is reduced; no private UTC, named
 * phase palette, point sources or claimed refined lunar/diffuse result.
 */
export function nativeAtmosphereFields(state,atmosphere,view,residualNight,gx=24,gy=40){
 const mapping=skyProjection(view),width=view.width,height=view.height,sky=createSkyModel(state,atmosphere,{residualNight}),withoutAerosol=state.sun.altDeg>10?createSkyModel(state,{...atmosphere,aerosolAlbedo:0},{residualNight}):null;
 const grid=new Float64Array((gx+1)*(gy+1)*3),ag=new Float64Array(grid.length),sg=new Float64Array(grid.length);
 for(let y=0;y<=gy;y++)for(let x=0;x<=gx;x++){
  const px=x*width/gx,py=y*height/gy;if(!mapping.above(px,py))continue;
  const dir=mapping.unproject(px,py),sample=sky.sample(dir),ray=withoutAerosol?.sample(dir),omega=mapping.solidAngle(px,py)/V_ZERO_ILLUMINANCE_LUX,at=(y*(gx+1)+x)*3;
  const neutral=sample.moonLuminance+sample.naturalLuminance+sample.localLuminance;
  for(let k=0;k<3;k++){grid[at+k]=sample.rgb[k]*omega;sg[at+k]=Math.max(0,sample.rgb[k]-neutral)*omega;ag[at+k]=ray?Math.max(0,sample.rgb[k]-ray.rgb[k]-(sample.moonLuminance-ray.moonLuminance))*omega:0;}
 }
 const background=new Float64Array(width*height*3),solarAerosolLinear=new Float64Array(background.length),solarBackgroundLinear=new Float64Array(background.length);let mean=0,pixels=0;
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  if(!mapping.above(x+.5,y+.5))continue;
  const u=(x+.5)/width*gx,v=(y+.5)/height*gy,ix=Math.min(gx-1,Math.floor(u)),iy=Math.min(gy-1,Math.floor(v)),tx=u-ix,ty=v-iy,at=(y*width+x)*3,tl=(iy*(gx+1)+ix)*3,bl=tl+(gx+1)*3;
  for(let k=0;k<3;k++){background[at+k]=(grid[tl+k]*(1-tx)+grid[tl+3+k]*tx)*(1-ty)+(grid[bl+k]*(1-tx)+grid[bl+3+k]*tx)*ty;solarAerosolLinear[at+k]=(ag[tl+k]*(1-tx)+ag[tl+3+k]*tx)*(1-ty)+(ag[bl+k]*(1-tx)+ag[bl+3+k]*tx)*ty;solarBackgroundLinear[at+k]=(sg[tl+k]*(1-tx)+sg[tl+3+k]*tx)*(1-ty)+(sg[bl+k]*(1-tx)+sg[bl+3+k]*tx)*ty;}
  mean+=.2126*background[at]+.7152*background[at+1]+.0722*background[at+2];pixels++;
 }
 let twilightDisplay=null;
 if(state.sun.altDeg<10){
  const referenceAltitude=Math.max(-15,Math.min(-5,state.sun.altDeg)),fit=patatTwilight(referenceAltitude),bv=fit.totalBMag-fit.totalVMag;
  const xyz=spectrumToXYZ(selectSpectrum({bv}).samples),referenceRGB=gamutMapXYZ(xyz).map(v=>v/xyz[1]),zenith=sky.sample({altDeg:90,azDeg:0});
  const u=Math.min(1,Math.max(0,(10-state.sun.altDeg)/15)),weight=u*u*(3-2*u)*zenith.solarLuminance/Math.max(1e-20,zenith.luminance);
  const gains=referenceRGB.map((v,k)=>1+weight*(v*zenith.luminance/Math.max(1e-20,zenith.rgb[k])-1));
  twilightDisplay={gains,weight,bv,referenceAltitude,referenceRGB,rawZenithRGB:zenith.rgb,scope:'Display-only Patat2006 total zenith B-V; geographic/angular use approximate. Held -5-degree colour smoothly releases to raw daylight at +10; -15 held to deep-night blend. Not measured local spectrum.'};
 }
 return {background,solarAerosolLinear,solarBackgroundLinear,twilightDisplay,mean:mean/Math.max(1,pixels),solarNodes:sky.solarNodeCount(),grid:[gx,gy]};
}
export function renderNativeBackgroundPreview(snapshot){
 const started=performance.now(),job=nativeJob(snapshot,true),state=physicalSkyState(job.observer);
 // Fast clock previews have a short real-time age budget. Reduce only this
 // explicitly non-refined atmosphere's spatial sampling; the numerical model,
 // worker tier, catalogue and terrain quality are unchanged in both engines.
 const fast=Math.abs(snapshot.timeScale??1)>10,divisor=fast?5:1,width=325/divisor,height=530/divisor;
 const view={...job.options.view,width,height},grid=fast?[12,20]:[24,40],fields=nativeAtmosphereFields(state,job.options.atmosphere,view,job.options.diffuse.residualNight,...grid);
 // The reference field represents flux per 325x530 physics pixel, not per
 // larger preview texel. Keep those units when reducing the display raster.
 if(fast)for(const array of [fields.background,fields.solarAerosolLinear,fields.solarBackgroundLinear])for(let i=0;i<array.length;i++)array[i]/=divisor*divisor;
 if(fast)fields.mean/=divisor*divisor;
 const {background,solarAerosolLinear,mean}=fields,nominalExposure=job.options.nominalExposure,effectiveExposure=nominalExposure/(1+nominalExposure*mean/.5);
 const anchor=snapshot.solarAnchor??{x:20,y:40+176*(1-Math.min(1,Math.max(0,state.sun.altDeg/40)))};
 const raster=nativeSkyPresentation({width,height,linear:background,backgroundLinear:background,skyBackgroundLinear:background,solarAerosolLinear,solarBackgroundLinear:fields.solarBackgroundLinear,twilightDisplay:fields.twilightDisplay,stellarLinear:new Float64Array(background.length),effectiveExposure,nominalExposure,physicalState:state,atmosphere:job.options.atmosphere,meanBackgroundY:mean},view,{...anchor,x:anchor.x/divisor,y:anchor.y/divisor});
 return {utcMs:snapshot.utcMs,native:job.native,job,quality:'physical-background-preview',raster,diagnostics:{grid:fields.grid,raster:[width,height],referencePixels:[325,530],solarNodes:fields.solarNodes,buildMs:performance.now()-started,scope:'atmosphere only; catalogue/diffuse/Moon refinement pending'}};
}
