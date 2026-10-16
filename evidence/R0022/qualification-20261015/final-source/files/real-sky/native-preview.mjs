import {nativeJob} from './native-contract.mjs';
import {physicalSkyState} from './core/src/sky-state.mjs';
import {createSkyModel,moonSkyLuminance,patatTwilight,V_ZERO_ILLUMINANCE_LUX} from './core/src/sky-background.mjs';
import {selectSpectrum,spectrumToXYZ,gamutMapXYZ} from './core/src/spectral.mjs';
import {skyProjection} from './core/src/physical-sky-renderer.mjs';
import {projectPerspective} from './core/src/projection.mjs';
import {phaseHG,horizontalDirection,rayleighOpticalDepth,aerosolOpticalDepth,cloudTransmissionFor} from './core/src/atmosphere.mjs';
import {angularSeparation} from './core/src/astronomy.mjs';

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

// Owner-accepted R0022-L1-H1-K003-H020-v1 display, not calibrated photometry. The
// original exposure meters the full raw field. Compress only the independently
// sampled lunar RGB share in that E*Y energy domain; never move its direction,
// re-meter the frame or relabel natural/local/solar light as lunar. One RGB scale
// is identity through K, positive and monotone above it, with a C1 soft knee.
function lunarDisplayTarget(z){const K=.003,H=.020,excess=z-K;return z<=K?z:K+H*(excess/(H+excess));}
function lunarDisplayMetadata(E,pixels,nightWeight){const K=.003,H=.020;return {owner:'native lunar atmosphere display',contract:'R0022-L1-H1-K003-H020-v1',policy:'lunar-only E*Y soft shoulder; common RGB scale at original physical direction; existing smooth night blend -18..-12 degrees',kneeEnergy:K,headroomEnergy:H,nightWeight,pixels,physicalExposure:E,scope:'Owner-accepted calendar display bounds, not calibrated radiance; original raw/source, exposure and non-lunar inputs retained'};}

function nativeLunarNightDisplay(raster,nightWeight,composeNight=false){
 const moon=raster.lunarBackgroundLinear;
 if(nightWeight<=0||!moon)return null;
 const source=raster.skyBackgroundLinear??raster.backgroundLinear,E=raster.effectiveExposure,K=.003,H=.020;
 if(!source||moon.length!==source.length||source.length!==raster.linear?.length||source.length%3||!Number.isFinite(E)||E<=0)throw new RangeError('Lunar display requires matched raw fields and original exposure');
 if(!moon.some(v=>v!==0))return null;
 const shown=new Float64Array(moon.length),diffuse=raster.diffuseLinear,solar=raster.solarBackgroundLinear;
 const sky=composeNight?new Float64Array(source.length):null;
 const linear=composeNight?(raster.linear===source?sky:new Float64Array(source.length)):null;
 const background=composeNight?(diffuse?new Float64Array(source.length):sky):null;
 let pixels=0;
 for(let i=0;i<moon.length;i+=3){
  const r=moon[i],g=moon[i+1],b=moon[i+2],sr=source[i],sg=source[i+1],sb=source[i+2];
  if(!Number.isFinite(r)||!Number.isFinite(g)||!Number.isFinite(b)||r<0||g<0||b<0||!Number.isFinite(sr)||!Number.isFinite(sg)||!Number.isFinite(sb)||r>sr-(solar?.[i]??0)||g>sg-(solar?.[i+1]??0)||b>sb-(solar?.[i+2]??0))throw new RangeError('Invalid lunar share of raw non-solar atmosphere');
  const Y=.2126*r+.7152*g+.0722*b,z=E*Y;
  if(!Number.isFinite(z))throw new RangeError('Invalid lunar display energy');
  const target=lunarDisplayTarget(z),scale=z<=K?1:target/z;
  // Algebraically K+excess/(1+excess/H); this form avoids division overflow
  // returning to K at large finite energy. Floating asymptotic ties remain an
  // ordinary number-precision limit, not a hard clip or an erased lunar field.
  shown[i]=r*scale;shown[i+1]=g*scale;shown[i+2]=b*scale;
  // Deep-night assembly consumes the value just computed. This is the same
  // ordered arithmetic as the separate pass, including distinct star/diffuse
  // terms; no physical input is overwritten or moved into preparation.
  if(composeNight){
   sky[i]=sr-r+shown[i];sky[i+1]=sg-g+shown[i+1];sky[i+2]=sb-b+shown[i+2];
   if(linear!==sky){linear[i]=raster.linear[i]-sr+sky[i];linear[i+1]=raster.linear[i+1]-sg+sky[i+1];linear[i+2]=raster.linear[i+2]-sb+sky[i+2];}
   if(background!==sky){background[i]=sky[i]+diffuse[i];background[i+1]=sky[i+1]+diffuse[i+1];background[i+2]=sky[i+2]+diffuse[i+2];}
  }
  if(z>K)pixels++;
 }
 return pixels?{shown,sky,linear,background,presentation:lunarDisplayMetadata(E,pixels,nightWeight)}:null;
}

function positiveChannel(array){if(array)for(let i=0;i<array.length;i++)if(array[i]>0)return true;return false;}

/** Atmospheric display only. The numerical radiance, catalogue, worker exposure
 * and lunar material stay intact. Mean full-field metering lets a bright horizon
 * or forward-scattering lobe darken open daytime sky. Meter its median instead;
 * tone-map luminance then scale RGB together, preserving spectral chromaticity
 * instead of compressing blue independently toward grey. Twilight additionally
 * uses the explicit reference colour adaptation documented below.
 */
export function nativeSkyPresentation(raster,view,anchor){
 const altitude=raster.physicalState?.sun?.altDeg;
 if(!Number.isFinite(altitude))return raster;
 const source=raster.skyBackgroundLinear??raster.backgroundLinear,E=raster.effectiveExposure;
 const t=Math.min(1,Math.max(0,(altitude+18)/6)),strength=t*t*(3-2*t),deepNight=altitude<=-18&&!positiveChannel(raster.solarBackgroundLinear),lunar=nativeLunarNightDisplay(raster,1-strength,deepNight);
 if(deepNight){
  if(!lunar)return raster;
  return {...raster,linear:lunar.linear,skyBackgroundLinear:lunar.sky,backgroundLinear:lunar.background,physicalSkyBackgroundLinear:source,lunarNightDisplayLinear:lunar.shown,lunarDisplayPresentation:lunar.presentation};
 }
 if(!source||source.length!==raster.linear.length||!Number.isFinite(E)||E<=0)throw new RangeError('Daylight display requires valid atmospheric field');
 const registration=nativeSolarRegistration(raster,view,anchor),w=raster.width,h=raster.height;
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
   const nightSource=lunar?source[i+c]-raster.lunarBackgroundLinear[i+c]+lunar.shown[i+c]:source[i+c];
   const old=-Math.expm1(-E*nightSource),mapped=shown[i+c]*scale/gamut;
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
    // Change only the existing night branch. Original daytime/solar metering,
    // colour, registration and shoulder use the unchanged source/shown fields.
    // Their full mapped term stays exact; the intervention fades with the same
    // (1-strength) smooth weight, full at <=-18 and absent at >=-12, C1 at both.
    const nightNeutral=lunar?neutral-raster.lunarBackgroundLinear[i+c]+lunar.shown[i+c]:neutral;
    const oldNeutral=-Math.expm1(-E*nightNeutral),mappedNeutral=Math.max(0,shown[i+c]-solarShown[i+c])*scale/gamut;
    display=mapped+(oldNeutral-mappedNeutral)*(1-strength);
   }
   sky[i+c]=-Math.log1p(-Math.min(1-1/131072,display))/E;
   linear[i+c]=raster.linear[i+c]-source[i+c]+sky[i+c];
  }
 }
 return {...raster,linear,skyBackgroundLinear:sky,backgroundLinear:Float64Array.from(sky,(v,i)=>v+(raster.diffuseLinear?.[i]??0)),physicalSkyBackgroundLinear:source,...(lunar?{lunarNightDisplayLinear:lunar.shown,lunarDisplayPresentation:lunar.presentation}:{}),
  displayPresentation:{owner:'native atmospheric display',policy:'perspective surface brightness; civil-twilight9% exposure reference; one-stop solar twilight highlight shoulder and directional chroma; luminance tone map and declared twilight colour adaptation; non-solar deep-night blend -18..-12 degrees',twilightColour:colour??null,twilightChroma:{pixels:chromaPixels,scope:'Solar warm chroma outside physical HG forward excess limited to retained twilight reference at fixed luminance; not calibrated directional spectroscopy'},twilightShoulder:{weight:shoulderWeight,kneeMedianMultiple:Math.SQRT2,asymptoticMedianMultiple:2,pixels:shoulderPixels,scope:'display-only solar highlight range; raw radiance and non-solar contributors preserved'},solarAltitudeDeg:altitude,strength,solidAnglePolicy:projection?'reference flux normalized to central-pixel solid angle for display only':'not a perspective raster',medianLuminance:median,adaptationReferenceCdM2,displayExposure,physicalExposure:E,solarRegistration:{active:!!aureole&&registration.active,presence:registration.presence,physical:registration.source,display:registration.target,scope:'twilight through+10deg remains physical; daytime forward excess blends to decorative light over+10..20deg; raw radiance, horizon, Rayleigh, lunar and catalogue projection unchanged'}}};
}

/** Lunar component of the already accepted worker atmosphere. Evaluate the
 * unchanged physical model at the worker's exact nodes, then interpolate its
 * neutral lunar flux with the same arithmetic. No approximate subtraction,
 * cached physical values, or second cloud transmission. The other raw fields
 * remain owned by the worker; this does not rebuild them for display admission.
 */
export function nativeLunarAtmosphereField(state,atmosphere,view,residualNight,gx=24,gy=40){
 const mapping=skyProjection(view),width=view.width,height=view.height,sky=createSkyModel(state,atmosphere,{residualNight});
 const grid=new Float64Array((gx+1)*(gy+1));
 for(let y=0;y<=gy;y++)for(let x=0;x<=gx;x++){
  const px=x*width/gx,py=y*height/gy;if(!mapping.above(px,py))continue;
  const sample=sky.sample(mapping.unproject(px,py)),omega=mapping.solidAngle(px,py)/V_ZERO_ILLUMINANCE_LUX;
  grid[y*(gx+1)+x]=sample.moonLuminance*omega;
 }
 const lunar=new Float64Array(width*height*3);
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  if(!mapping.above(x+.5,y+.5))continue;
  const u=(x+.5)/width*gx,v=(y+.5)/height*gy,ix=Math.min(gx-1,Math.floor(u)),iy=Math.min(gy-1,Math.floor(v)),tx=u-ix,ty=v-iy,at=(y*width+x)*3,tl=iy*(gx+1)+ix,bl=tl+gx+1;
  const value=(grid[tl]*(1-tx)+grid[tl+1]*tx)*(1-ty)+(grid[bl]*(1-tx)+grid[bl+1]*tx)*ty;
  lunar[at]=value;lunar[at+1]=value;lunar[at+2]=value;
 }
 return lunar;
}

/** Bounded first-paint background, before catalogue/assets/worker readiness.
 * Same accepted observer, spherical spectral atmosphere and display owner as
 * the refined frame. Only spatial sampling is reduced; no private UTC, named
 * phase palette, point sources or claimed refined lunar/diffuse result.
 */
export function nativeAtmosphereFields(state,atmosphere,view,residualNight,gx=24,gy=40){
 const mapping=skyProjection(view),width=view.width,height=view.height,sky=createSkyModel(state,atmosphere,{residualNight}),withoutAerosol=state.sun.altDeg>10?createSkyModel(state,{...atmosphere,aerosolAlbedo:0},{residualNight}):null;
 const grid=new Float64Array((gx+1)*(gy+1)*3),ag=new Float64Array(grid.length),sg=new Float64Array(grid.length),mg=new Float64Array(grid.length);
 let neutralGrid=true,solarPresent=false,aerosolPresent=false;
 for(let y=0;y<=gy;y++)for(let x=0;x<=gx;x++){
  const px=x*width/gx,py=y*height/gy;if(!mapping.above(px,py))continue;
  const dir=mapping.unproject(px,py),sample=sky.sample(dir),ray=withoutAerosol?.sample(dir),omega=mapping.solidAngle(px,py)/V_ZERO_ILLUMINANCE_LUX,at=(y*(gx+1)+x)*3;
  const neutral=sample.moonLuminance+sample.naturalLuminance+sample.localLuminance;
  for(let k=0;k<3;k++){grid[at+k]=sample.rgb[k]*omega;sg[at+k]=Math.max(0,sample.rgb[k]-neutral)*omega;ag[at+k]=ray?Math.max(0,sample.rgb[k]-ray.rgb[k]-(sample.moonLuminance-ray.moonLuminance))*omega:0;mg[at+k]=sample.moonLuminance*omega;}
  neutralGrid&&=grid[at]===grid[at+1]&&grid[at]===grid[at+2];
  solarPresent||=sg[at]!==0||sg[at+1]!==0||sg[at+2]!==0;
  aerosolPresent||=ag[at]!==0||ag[at+1]!==0||ag[at+2]!==0;
 }
 const background=new Float64Array(width*height*3),solarAerosolLinear=new Float64Array(background.length),solarBackgroundLinear=new Float64Array(background.length),lunarBackgroundLinear=new Float64Array(background.length);let mean=0,pixels=0;
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  if(!mapping.above(x+.5,y+.5))continue;
  const u=(x+.5)/width*gx,v=(y+.5)/height*gy,ix=Math.min(gx-1,Math.floor(u)),iy=Math.min(gy-1,Math.floor(v)),tx=u-ix,ty=v-iy,at=(y*width+x)*3,tl=(iy*(gx+1)+ix)*3,bl=tl+(gx+1)*3;
  // Interpolate identical neutral channels once, and leave proven all-zero
  // component grids at their allocated zero values. These decisions inspect
  // the actual sampled grid: no phase, altitude, weather or epsilon shortcut.
  if(neutralGrid){const v=(grid[tl]*(1-tx)+grid[tl+3]*tx)*(1-ty)+(grid[bl]*(1-tx)+grid[bl+3]*tx)*ty;background[at]=v;background[at+1]=v;background[at+2]=v;}
  else for(let k=0;k<3;k++)background[at+k]=(grid[tl+k]*(1-tx)+grid[tl+3+k]*tx)*(1-ty)+(grid[bl+k]*(1-tx)+grid[bl+3+k]*tx)*ty;
  if(aerosolPresent)for(let k=0;k<3;k++)solarAerosolLinear[at+k]=(ag[tl+k]*(1-tx)+ag[tl+3+k]*tx)*(1-ty)+(ag[bl+k]*(1-tx)+ag[bl+3+k]*tx)*ty;
  if(solarPresent)for(let k=0;k<3;k++)solarBackgroundLinear[at+k]=(sg[tl+k]*(1-tx)+sg[tl+3+k]*tx)*(1-ty)+(sg[bl+k]*(1-tx)+sg[bl+3+k]*tx)*ty;
  // moonLuminance is the accepted neutral proxy and populated all three grid
  // channels identically above. Preserve the exact interpolation arithmetic.
  const lunar=(mg[tl]*(1-tx)+mg[tl+3]*tx)*(1-ty)+(mg[bl]*(1-tx)+mg[bl+3]*tx)*ty;
  lunarBackgroundLinear[at]=lunar;lunarBackgroundLinear[at+1]=lunar;lunarBackgroundLinear[at+2]=lunar;
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
 return {background,solarAerosolLinear,solarBackgroundLinear,lunarBackgroundLinear,twilightDisplay,mean:mean/Math.max(1,pixels),solarNodes:sky.solarNodeCount(),grid:[gx,gy]};
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
 if(fast)for(const array of [fields.background,fields.solarAerosolLinear,fields.solarBackgroundLinear,fields.lunarBackgroundLinear])for(let i=0;i<array.length;i++)array[i]/=divisor*divisor;
 if(fast)fields.mean/=divisor*divisor;
 const {background,solarAerosolLinear,mean}=fields,nominalExposure=job.options.nominalExposure,effectiveExposure=nominalExposure/(1+nominalExposure*mean/.5);
 const anchor=snapshot.solarAnchor??{x:20,y:40+176*(1-Math.min(1,Math.max(0,state.sun.altDeg/40)))};
 const raster=nativeSkyPresentation({width,height,linear:background,backgroundLinear:background,skyBackgroundLinear:background,solarAerosolLinear,solarBackgroundLinear:fields.solarBackgroundLinear,lunarBackgroundLinear:fields.lunarBackgroundLinear,twilightDisplay:fields.twilightDisplay,stellarLinear:new Float64Array(background.length),effectiveExposure,nominalExposure,physicalState:state,atmosphere:job.options.atmosphere,meanBackgroundY:mean},view,{...anchor,x:anchor.x/divisor,y:anchor.y/divisor});
 return {utcMs:snapshot.utcMs,native:job.native,job,quality:'physical-background-preview',raster,diagnostics:{grid:fields.grid,raster:[width,height],referencePixels:[325,530],solarNodes:fields.solarNodes,buildMs:performance.now()-started,scope:'atmosphere only; catalogue/diffuse/Moon refinement pending'}};
}

// Rigid camera geometry only: no sky sample, UTC, radiance, atmosphere or
// exposure survives a call. Four native-size camera/grid entries bound state.
const lunarGeometryCache=new Map();
function lunarGeometry(view,gx,gy){
 const mapping=skyProjection(view),width=mapping.width,height=mapping.height;
 const key=JSON.stringify([view.type??'camera',width,height,view.azDeg??180,view.altDeg??35,view.fovYDeg??90,view.rollDeg??0,gx,gy]);
 const bounded=(view.type??'camera')==='camera'&&width===325&&height===530&&Number.isInteger(gx)&&gx>0&&gx<=68&&Number.isInteger(gy)&&gy>0&&gy<=68;
 if(!bounded)throw new RangeError('Lunar admission geometry must be a bounded native camera/grid');
 if(lunarGeometryCache.has(key))return lunarGeometryCache.get(key);
 const directions=new Array((gx+1)*(gy+1)),vectors=new Array(directions.length),omega=new Float64Array(directions.length),above=new Uint8Array(width*height);
 const ix=new Uint16Array(width),tx=new Float64Array(width),iy=new Uint32Array(height),ty=new Float64Array(height);
 for(let y=0;y<=gy;y++)for(let x=0;x<=gx;x++){
  const px=x*width/gx,py=y*height/gy,i=y*(gx+1)+x;if(!mapping.above(px,py))continue;
  directions[i]=mapping.unproject(px,py);vectors[i]=horizontalDirection(directions[i]);omega[i]=mapping.solidAngle(px,py)/V_ZERO_ILLUMINANCE_LUX;
 }
 for(let x=0;x<width;x++){const u=(x+.5)/width*gx,j=Math.min(gx-1,Math.floor(u));ix[x]=j;tx[x]=u-j;}
 for(let y=0;y<height;y++){
  const v=(y+.5)/height*gy,j=Math.min(gy-1,Math.floor(v));iy[y]=j*(gx+1);ty[y]=v-j;
  for(let x=0;x<width;x++)above[y*width+x]=mapping.above(x+.5,y+.5)?1:0;
 }
 const geometry={width,height,gx,gy,directions,vectors,omega,above,ix,tx,iy,ty};
 if(lunarGeometryCache.size===4)lunarGeometryCache.delete(lunarGeometryCache.keys().next().value);
 lunarGeometryCache.set(key,geometry);return geometry;
}

/** Same deep-night physical samples and H1 formula, with expansion and display
 * assembly in one pass. The lunar proxy is neutral at every original model
 * node; interpolate it once and explicitly retain all three raw RGB channels.
 * Camera geometry is reusable. Every physical sample remains current-call work.
 */
export function nativeLunarNightPresentation(raster,view,residualNight,gx,gy){
 if(!(raster.physicalState?.sun?.altDeg<-20)||positiveChannel(raster.solarBackgroundLinear))throw new RangeError('Lunar fused admission requires the physical solar-zero domain');
 const source=raster.skyBackgroundLinear??raster.backgroundLinear,E=raster.effectiveExposure;
 if(!source||source.length!==325*530*3||source.length!==raster.linear?.length||!Number.isFinite(E)||E<=0)throw new RangeError('Lunar display requires matched raw fields and original exposure');
 const geometry=lunarGeometry(view,gx,gy),{width,height,directions,vectors,omega,above,ix,tx,iy,ty}=geometry;
 const model=createSkyModel(raster.physicalState,raster.atmosphere,{residualNight}),grid=new Float64Array(directions.length);
 // The immutable sky model still validates this current physical state and
 // normalises its atmosphere. Extract only its lunar term using the SAME
 // exported core functions and operation order; unused natural/solar RGB and
 // per-sample metadata do not belong to this component admission.
 const state=raster.physicalState,a=model.atmosphere,moonVector=horizontalDirection(state.moon);
 const tauR=rayleighOpticalDepth(550,a),tauA=aerosolOpticalDepth(550,a),totalTau=tauR+tauA+a.greyTau;
 const lunarScatteringAlbedo=totalTau>0?(tauR+tauA*a.aerosolAlbedo)/totalTau:0,k=1.0857362047581296*totalTau;
 for(let i=0;i<directions.length;i++)if(directions[i]){
  const h=directions[i],rho=angularSeparation(vectors[i],moonVector);
  const moon=moonSkyLuminance({moonAltDeg:state.moon.altDeg,targetAltDeg:h.altDeg,separationDeg:rho,phaseAngleDeg:state.moon.phaseAngleDeg,extinctionMag:k,distanceKm:state.moon.distanceKm??384400,angularRadiusDeg:state.moon.angularRadiusDeg??.25})*lunarScatteringAlbedo;
  grid[i]=moon*cloudTransmissionFor(h,a,null,state.utcMs)*omega[i];
 }
 const moon=new Float64Array(source.length),shown=new Float64Array(source.length),sky=new Float64Array(source.length);
 const linear=raster.linear===source?sky:new Float64Array(source.length),diffuse=raster.diffuseLinear,background=diffuse?new Float64Array(source.length):sky;
 let pixels=0;
 const rawLinear=raster.linear,assembleLinear=linear!==sky,assembleBackground=background!==sky;
 for(let y=0;y<height;y++){
  const top=iy[y],lower=top+gx+1,u=ty[y],oneMinusU=1-u;
  for(let x=0;x<width;x++){
   const p=y*width+x,i=p*3;
   let r=0;
   if(above[p]){
    const tl=top+ix[x],bl=lower+ix[x],t=tx[x],oneMinusT=1-t;
    r=(grid[tl]*oneMinusT+grid[tl+1]*t)*oneMinusU+(grid[bl]*oneMinusT+grid[bl+1]*t)*u;
   }
   moon[i]=r;moon[i+1]=r;moon[i+2]=r;
   const sr=source[i],sg=source[i+1],sb=source[i+2];
   if(!Number.isFinite(r)||r<0||!Number.isFinite(sr)||!Number.isFinite(sg)||!Number.isFinite(sb)||r>sr||r>sg||r>sb)throw new RangeError('Invalid lunar share of raw non-solar atmosphere');
   const z=E*(.2126*r+.7152*r+.0722*r);
   if(!Number.isFinite(z))throw new RangeError('Invalid lunar display energy');
   const scale=z<=.003?1:lunarDisplayTarget(z)/z,s=r*scale;
   shown[i]=s;shown[i+1]=s;shown[i+2]=s;
   const vr=sr-r+s,vg=sg-r+s,vb=sb-r+s;
   sky[i]=vr;sky[i+1]=vg;sky[i+2]=vb;
   if(assembleLinear){linear[i]=rawLinear[i]-sr+vr;linear[i+1]=rawLinear[i+1]-sg+vg;linear[i+2]=rawLinear[i+2]-sb+vb;}
   if(assembleBackground){background[i]=vr+diffuse[i];background[i+1]=vg+diffuse[i+1];background[i+2]=vb+diffuse[i+2];}
   if(z>.003)pixels++;
  }
 }
 if(!pixels)return {...raster,lunarBackgroundLinear:moon};
 return {...raster,linear,skyBackgroundLinear:sky,backgroundLinear:background,physicalSkyBackgroundLinear:source,lunarBackgroundLinear:moon,lunarNightDisplayLinear:shown,lunarDisplayPresentation:lunarDisplayMetadata(E,pixels,1)};
}
