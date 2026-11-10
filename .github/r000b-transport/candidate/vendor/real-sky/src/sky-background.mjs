/** CP6 radiance model: spectral spherical single scattering + a measured-site twilight
 * residual, empirical moonlight, and a parameterised natural/local background.
 * Units are photopic-equivalent cd/m² under the documented V-to-luminance convention.
 * Not a full multiple-scattering solver, measured local weather, or diffuse star map.
 */
import {finite,DEG,clamp,wrapDeg,dot,angularSeparation} from './astronomy.mjs';
import {normaliseAtmosphere,rayleighOpticalDepth,aerosolOpticalDepth,cloudTransmissionFor,phaseRayleigh,phaseHG,horizontalDirection} from './atmosphere.mjs';
import {SPECTRAL_GRID,blackbodyShape,spectrumToXYZ,gamutMapXYZ,selectSpectrum} from './spectral.mjs';
import {luminance} from './photometry.mjs';
export const V_ZERO_ILLUMINANCE_LUX=2.54e-6;
export const ARCSEC_PER_RADIAN=206264.80624709636;
const bgMagnitudeZero=V_ZERO_ILLUMINANCE_LUX*ARCSEC_PER_RADIAN**2,bgEarthRadius=6371000,bgTopRadius=6471000;
const bgSmooth=x=>{x=clamp(x,0,1);return x*x*(3-2*x);};
const bgSolarBase=blackbodyShape(5778),bgSolarY=spectrumToXYZ(bgSolarBase)[1],bgSolarShape=bgSolarBase.map(x=>x/bgSolarY),bgCoeff=new WeakMap();
export function surfaceMagnitudeToLuminance(m){return bgMagnitudeZero*10**(-.4*finite(m,'V magnitude per arcsec2',-30,60));}
export function luminanceToSurfaceMagnitude(L){finite(L,'luminance',Number.MIN_VALUE);return -2.5*Math.log10(L/bgMagnitudeZero);}
/** An explicit assumed NON-STELLAR residual replaces the historical aggregate floor.
 * It is never inferred by subtracting a map from a total or called measured airglow.
 * Its supplied zenith value is already at the observer (pre-cloud), like the CP6 floor.
 */
export function validateResidualNight(input){
 if(!input||input.kind!=='assumed-nonstellar-residual'||input.includesRegisteredStarlight!==false||typeof input.source!=='string'||!input.source.trim())throw new TypeError('Explicit labelled non-stellar residual night assumption required');
 return Object.freeze({kind:input.kind,zenithCdM2:finite(input.zenithCdM2,'residual night zenith cd/m2',0,1),source:input.source,includesRegisteredStarlight:false,measured:false});
}
/** Patat et al. (2006) Table 1: fitted TOTAL zenith background, solar depression 5..15°.
 * Subtract reference night V=21.6/B=22.6 before adding our own natural background.
 * A tapered continuation to 20° is an explicit engineering extension, not published data.
 */
export function patatTwilight(sunAltDeg){finite(sunAltDeg,'solar altitude',-90,90);const depression=-sunAltDeg,x=clamp(depression,3,15)-5;
 const totalVMag=11.84+1.518*x-.057*x*x,totalBMag=11.84+1.411*x-.041*x*x;
 let v=Math.max(0,10**(-.4*totalVMag)-10**(-.4*21.6)),b=Math.max(0,10**(-.4*totalBMag)-10**(-.4*22.6));
 const tail=depression<=15?1:Math.exp(-.4*Math.LN10*.378*(depression-15))*(1-bgSmooth((depression-15)/5));v*=tail;b*=tail;
 return {totalVMag,totalBMag,excessLuminance:bgMagnitudeZero*v,bv:v>0&&b>0?-2.5*Math.log10(b/v):null,inMeasuredDomain:depression>=5&&depression<=15,reference:'Patat2006Table1; night floor removed',extension:depression<5||depression>15};
}
/** Original KS1991 equations, nL converted to cd/m² (1 nL=1e-5/pi cd/m²).
 * Near aureole uses their rho^-2 term; blend only 8..12° to avoid a branch jump.
 * No opposition boost, eclipse, instrument glare or calendar-Moon position is inferred.
 */
export function moonSkyLuminance({moonAltDeg,targetAltDeg,separationDeg,phaseAngleDeg,extinctionMag,distanceKm=384400,angularRadiusDeg=.25}){
 finite(moonAltDeg,'Moon altitude',-90,90);finite(targetAltDeg,'target altitude',-90,90);finite(separationDeg,'Moon separation',0,180);finite(phaseAngleDeg,'lunar phase angle',0,180);finite(extinctionMag,'extinction mag/airmass',0,10);finite(distanceKm,'lunar distance km',100000,1000000);finite(angularRadiusDeg,'lunar angular radius',.01,2);
 if(targetAltDeg<0||moonAltDeg<=-angularRadiusDeg||extinctionMag===0)return 0;
 const u=clamp(moonAltDeg/angularRadiusDeg,-1,1),visibleDisc=(Math.acos(-u)+u*Math.sqrt(Math.max(0,1-u*u)))/Math.PI,rho=Math.max(angularRadiusDeg,separationDeg),c=Math.cos(rho*DEG),a=phaseAngleDeg;
 const X=alt=>(1-.96*Math.cos(Math.max(0,alt)*DEG)**2)**(-.5),near=6.2e7/(rho*rho),far=10**(6.15-rho/40),blend=bgSmooth((rho-8)/4);
 const f=10**5.36*(1.06+c*c)+near*(1-blend)+far*blend,I=10**(-.4*(3.84+.026*a+4e-9*a**4));
 return (1e-5/Math.PI)*f*I*10**(-.4*extinctionMag*X(moonAltDeg))*(-Math.expm1(-.4*Math.LN10*extinctionMag*X(targetAltDeg)))*(384400/distanceKm)**2*visibleDisc;
}
function bgCoefficients(a){if(bgCoeff.has(a))return bgCoeff.get(a);const result=SPECTRAL_GRID.map(w=>[rayleighOpticalDepth(w,a)/a.rayleighScaleHeightM,aerosolOpticalDepth(w,a)/a.aerosolScaleHeightM]);bgCoeff.set(a,result);return result;}
function bgExit(p,v,radius){const b=dot(p,v),c=dot(p,p)-radius*radius;return -b+Math.sqrt(Math.max(0,b*b-c));}
function bgSunColumns(p,sun,groundRadius,a,steps){const b=dot(p,sun),r2=dot(p,p);if(b<0&&r2-b*b<groundRadius*groundRadius)return null;
 const end=bgExit(p,sun,bgTopRadius);let R=0,A=0;for(let j=0;j<steps;j++){const left=end*(j/steps)**2,right=end*((j+1)/steps)**2,t=(left+right)/2,h=Math.sqrt(r2+2*b*t+t*t)-groundRadius;R+=Math.exp(-h/a.rayleighScaleHeightM)*(right-left);A+=Math.exp(-h/a.aerosolScaleHeightM)*(right-left);}return [R,A];}
/** 95 wavelength bins; 24 non-uniform view cells x 12 solar-column cells by default.
 * Solid Earth shadow is checked for every scatter point. Density is exponential above
 * the local spherical ground; this is a flat-altitude-site model, not global terrain.
 */
export function singleScatteredSun(direction,state,atmosphere={},options={}){
 const a=normaliseAtmosphere(atmosphere),view=horizontalDirection(direction),sun=horizontalDirection(state.sun),vSteps=options.viewSteps??24,sSteps=options.sunSteps??12;
 if(!Number.isInteger(vSteps)||vSteps<4||vSteps>256||!Number.isInteger(sSteps)||sSteps<4||sSteps>256)throw new RangeError('Invalid scattering quadrature');
 if(direction.altDeg<0||state.sun.altDeg<-20||(a.pressureHpa===0&&a.aerosolTau550===0))return {rgb:[0,0,0],luminance:0};
 const ground=bgEarthRadius+a.elevationM,p0=[0,0,ground],end=bgExit(p0,view,bgTopRadius),cosine=clamp(dot(view,sun)),pr=phaseRayleigh(cosine),pa=phaseHG(cosine,a.aerosolG)*a.aerosolAlbedo,coeff=bgCoefficients(a),grey=a.greyTau/a.rayleighScaleHeightM;
 const samples=new Array(95).fill(0);let R=0,A=0;
 for(let j=0;j<vSteps;j++){const left=end*(j/vSteps)**2,right=end*((j+1)/vSteps)**2,t=(left+right)/2,ds=right-left,p=[view[0]*t,view[1]*t,ground+view[2]*t],h=Math.hypot(...p)-ground,dr=Math.exp(-h/a.rayleighScaleHeightM),da=Math.exp(-h/a.aerosolScaleHeightM),rMid=R+dr*ds/2,aMid=A+da*ds/2,solar=bgSunColumns(p,sun,ground,a,sSteps);
  if(solar){const rPath=rMid+solar[0],aPath=aMid+solar[1];for(let k=0;k<95;k++){const [br,ba]=coeff[k];samples[k]+=(br*dr*pr+ba*da*pa)*Math.exp(-(br+grey)*rPath-ba*aPath)*ds;}}
  R+=dr*ds;A+=da*ds;
 }
 const distance=finite(state.sun.distanceAu??1,'Sun distance AU',.9,1.1),illuminance=127500/(distance*distance),xyz=spectrumToXYZ(samples.map((x,i)=>x*bgSolarShape[i]*illuminance));
 return {rgb:gamutMapXYZ(xyz),luminance:xyz[1],model:'spherical spectral single scattering',viewSteps:vSteps,sunSteps:sSteps};
}
/** Solar lookup is per physical sky state; 5° altitude /10° azimuth interpolation.
 * Lunar aureole and total cloud transmission are evaluated at the requested direction,
 * not baked into that coarse solar grid. No persistent cache can freeze sky time.
 */
export function createSkyModel(state,atmosphere={},options={}){
 horizontalDirection(state.sun);horizontalDirection(state.moon);finite(state.moon.phaseAngleDeg,'physical lunar phase',0,180);finite(state.utcMs,'sky UTC');
 const nightSpec=options.residualNight==null?null:validateResidualNight(options.residualNight);
 const a=normaliseAtmosphere(atmosphere),grid=new Map(),sun=horizontalDirection(state.sun),tw=patatTwilight(state.sun.altDeg),twilightWeight=bgSmooth((-state.sun.altDeg-3)/2),
 twilightSpectrum=selectSpectrum({bv:tw.bv}).samples,twilightXYZ=spectrumToXYZ(twilightSpectrum),twilightRgb=gamutMapXYZ(twilightXYZ).map(x=>x/twilightXYZ[1]);
 // A first-order site-rescaling assumption, not a calibrated multiple-scattering law.
 const twilightDepthScale=(rayleighOpticalDepth(550,a)+aerosolOpticalDepth(550,a)*a.aerosolAlbedo)/(rayleighOpticalDepth(550,{})+.06*.9);
 const tauR=rayleighOpticalDepth(550,a),tauA=aerosolOpticalDepth(550,a),totalTau=tauR+tauA+a.greyTau,
 // KS uses empirical total extinction. Extend with an effective scattering albedo so
 // explicitly absorbing-only opacity cannot become a fictitious lunar source term.
 lunarScatteringAlbedo=totalTau>0?(tauR+tauA*a.aerosolAlbedo)/totalTau:0,
 k=1.0857362047581296*totalTau,night=nightSpec?nightSpec.zenithCdM2:surfaceMagnitudeToLuminance(a.nightZenithVMag);
 const angularShape=h=>{const v=horizontalDirection(h),c=clamp(dot(v,sun));return (.75*phaseRayleigh(c)+.25*phaseHG(c,a.aerosolG))*(1+.25*(1-Math.sin(h.altDeg*DEG)));},zenithShape=angularShape({altDeg:90,azDeg:0});
 function solarNode(ia,iz){iz=(iz+36)%36;const key=ia*36+iz;if(grid.has(key))return grid.get(key);const h={altDeg:ia*5,azDeg:iz*10},ss=singleScatteredSun(h,state,a,options.quadrature),empirical=a.twilightScale*twilightDepthScale*tw.excessLuminance*angularShape(h)/zenithShape,
 extra=twilightWeight*Math.max(0,empirical-ss.luminance),rgb=ss.rgb.map((x,i)=>x+extra*twilightRgb[i]);grid.set(key,rgb);return rgb;}
 function solarAt(h){if(state.sun.altDeg<-20)return [0,0,0];const aa=clamp(h.altDeg/5,0,18),zz=wrapDeg(h.azDeg)/10,ia=Math.min(17,Math.floor(aa)),iz=Math.floor(zz),ta=aa-ia,tz=zz-iz,
 nodes=[solarNode(ia,iz),solarNode(ia,iz+1),solarNode(ia+1,iz),solarNode(ia+1,iz+1)];return [0,1,2].map(c=>(nodes[0][c]*(1-tz)+nodes[1][c]*tz)*(1-ta)+(nodes[2][c]*(1-tz)+nodes[3][c]*tz)*ta);}
 function sample(h){const v=horizontalDirection(h);if(h.altDeg<0)return {rgb:[0,0,0],luminance:0,solarLuminance:0,moonLuminance:0,naturalLuminance:0,cloudTransmission:0,ground:true};
 const X=(1-.96*Math.cos(h.altDeg*DEG)**2)**-.5,natural=night*X*Math.exp(-k/1.0857362047581296*(X-1)),rho=angularSeparation(v,horizontalDirection(state.moon)),moon=moonSkyLuminance({moonAltDeg:state.moon.altDeg,targetAltDeg:h.altDeg,separationDeg:rho,phaseAngleDeg:state.moon.phaseAngleDeg,extinctionMag:k,distanceKm:state.moon.distanceKm??384400,angularRadiusDeg:state.moon.angularRadiusDeg??.25})*lunarScatteringAlbedo,solar=solarAt(h),cloud=cloudTransmissionFor(h,a,options.cloudAt,state.utcMs),local=a.lightPollutionCdM2+a.cloudGlowCdM2*(1-cloud);
 // Lunar and night spectra not measured: explicitly neutral luminous display proxies.
 const rgb=solar.map(x=>(x+moon+natural)*cloud+local);
 return {rgb,luminance:luminance(rgb),solarLuminance:luminance(solar)*cloud,moonLuminance:moon*cloud,naturalLuminance:natural*cloud,...(nightSpec?{residualNightLuminance:natural*cloud,legacyNightLuminance:0}:{}),localLuminance:local,cloudTransmission:cloud,moonSeparationDeg:rho,colourModel:'spectral solar; B-V twilight continuum; neutral night/lunar proxy'};
 }
 return {state,atmosphere:a,sample,...(nightSpec?{nightBudget:{mode:'nonstellar-residual-replaces-legacy-floor',residual:nightSpec,ignoredLegacyNightZenithVMag:a.nightZenithVMag}}:{}),solarNodeCount:()=>grid.size,models:{solar:'spherical single scattering plus Patat-site twilight residual',moon:'Krisciunas-Schaefer1991 with finite aureole',night:nightSpec?'explicit assumed non-stellar residual + inherited angular law':'parameterised zenith + empirical scattering air mass',cloud:'total direct transmission plus explicit local glow'},warnings:['No full multiple scattering, polarisation, ozone bands, eclipses, global terrain or measured local weather','Twilight fit measured near zenith at Paranal; angular continuation and other sites approximate','Moon/night colours are neutral proxies, not measured spectra','Brightness zero point is photopic-equivalent V approximation']};
}
