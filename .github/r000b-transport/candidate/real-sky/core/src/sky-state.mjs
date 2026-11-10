/** Low-order Sun/Moon for sky illumination, NOT a lunar material or prayer calculator.
 * Schlyter orbital elements and ALL his listed lunar perturbations, independently written.
 * Uses CP4 TT for orbital time, UT1 sidereal rotation, ellipsoidal topocentric subtraction.
 * No claim of CP4 stellar sub-arcsecond precision for this separate lunar approximation.
 */
import {finite,DEG,clamp,wrapDeg,gmstDeg,vectorRaDec,equatorialToHorizontal,angularSeparation,unit} from './astronomy.mjs';
import {timeScales} from './time-scales.mjs';
const skSin=x=>Math.sin(x*DEG),skCos=x=>Math.cos(x*DEG);
function skOrbit(M,e,a,N=0,i=0,w=0){let E=wrapDeg(M)*DEG;const m=E;for(let k=0;k<8;k++)E-=(E-e*Math.sin(E)-m)/(1-e*Math.cos(E));const x=a*(Math.cos(E)-e),y=a*Math.sqrt(1-e*e)*Math.sin(E),v=Math.atan2(y,x)/DEG,r=Math.hypot(x,y);return {r,longitude:wrapDeg(v+w),vector:[r*(skCos(N)*skCos(v+w)-skSin(N)*skSin(v+w)*skCos(i)),r*(skSin(N)*skCos(v+w)+skCos(N)*skSin(v+w)*skCos(i)),r*skSin(v+w)*skSin(i)]};}
function skEquatorial(v,e){return [v[0],v[1]*skCos(e)-v[2]*skSin(e),v[1]*skSin(e)+v[2]*skCos(e)];}
export function physicalSkyState(observer){
 const t=timeScales(observer),lat=finite(observer.latDeg,'latitude',-90,90),lon=finite(observer.lonDeg,'longitude',-180,180),height=finite(observer.heightM??observer.elevationM??0,'height metres',-500,10000);
 const d=t.jdTt-2451543.5,eps=23.4393-3.563e-7*d,Ms=wrapDeg(356.0470+.9856002585*d),ws=282.9404+4.70935e-5*d;
 const sunOrbit=skOrbit(Ms,.016709-1.151e-9*d,1,0,0,ws),N=wrapDeg(125.1228-.0529538083*d),w=wrapDeg(318.0634+.1643573223*d),Mm=wrapDeg(115.3654+13.0649929509*d),moonOrbit=skOrbit(Mm,.0549,60.2666,N,5.1454,w);
 const v=moonOrbit.vector,ls=Ms+ws,lm=Mm+w+N,D=lm-ls,F=lm-N;
 let ml=Math.atan2(v[1],v[0])/DEG,mb=Math.atan2(v[2],Math.hypot(v[0],v[1]))/DEG;
 ml+=-1.274*skSin(Mm-2*D)+.658*skSin(2*D)-.186*skSin(Ms)-.059*skSin(2*Mm-2*D)-.057*skSin(Mm-2*D+Ms)+.053*skSin(Mm+2*D)+.046*skSin(2*D-Ms)+.041*skSin(Mm-Ms)-.035*skSin(D)-.031*skSin(Mm+Ms)-.015*skSin(2*F-2*D)+.011*skSin(Mm-4*D);
 mb+=-.173*skSin(F-2*D)-.055*skSin(Mm-F-2*D)-.046*skSin(Mm+F-2*D)+.033*skSin(F+2*D)+.017*skSin(2*Mm+F);
 const mr=moonOrbit.r-.58*skCos(Mm-2*D)-.46*skCos(2*D),moonEcl=[mr*skCos(ml)*skCos(mb),mr*skSin(ml)*skCos(mb),mr*skSin(mb)],sunKm=skEquatorial(sunOrbit.vector,eps).map(x=>x*149597870.7),moonKm=skEquatorial(moonEcl,eps).map(x=>x*6378.137);
 const lst=wrapDeg(gmstDeg(t.jdUt1)+lon),e2=.0066943799901413165,nn=6378.137/Math.sqrt(1-e2*skSin(lat)**2),site=[(nn+height/1000)*skCos(lat)*skCos(lst),(nn+height/1000)*skCos(lat)*skSin(lst),(nn*(1-e2)+height/1000)*skSin(lat)];
 const body=(p)=>{const top=p.map((x,i)=>x-site[i]),eq=vectorRaDec(top),h=equatorialToHorizontal(eq.raDeg,eq.decDeg,lst,lat);return {...h,...eq,distanceKm:Math.hypot(...top),frame:'topocentric-mean-equator-of-date',geometric:true};};
 const phaseAngleDeg=angularSeparation(sunKm.map((x,i)=>x-moonKm[i]),moonKm.map(x=>-x));
 const sun={...body(sunKm),distanceAu:sunOrbit.r},moon={...body(moonKm),geocentricDistanceKm:mr*6378.137,phaseAngleDeg,illuminatedFraction:(1+skCos(phaseAngleDeg))/2,angularRadiusDeg:Math.asin(1737.4/Math.hypot(...moonKm.map((x,i)=>x-site[i])))/DEG};
 return {utcMs:observer.utcMs,jdTt:t.jdTt,sun,moon,model:'Schlyter-perturbed-low-order; TT/UT1 and ellipsoid topocentre',warnings:[...t.warnings,'Sun/Moon nutation-aberration-light-time not applied','No eclipse attenuation or terrain/refraction in illumination ephemeris']};
}
