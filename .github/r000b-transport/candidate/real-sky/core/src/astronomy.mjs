import {timeScales} from './time-scales.mjs';
/** Astronomical geometry. Degrees externally; vectors and rotations in radians internally.
 * Sources/accuracy: docs/RESEARCH.md. This is a bounded widget model, not a SOFA replacement.
 * No Date.now(), local civil-time parser, random position, or browser geolocation is used here.
 */
export const DEG=Math.PI/180, ARCSEC=DEG/3600, MAS=ARCSEC/1000;
export const clamp=(x,lo=-1,hi=1)=>Math.max(lo,Math.min(hi,x));
export const wrapDeg=x=>((x%360)+360)%360;
export function finite(x,name,min=-Infinity,max=Infinity){if(typeof x!=='number'||!Number.isFinite(x)||x<min||x>max)throw new RangeError(`${name} must be finite in [${min}, ${max}]`);return x;}
export const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
export function unit(v){if(!Array.isArray(v)||v.length!==3||!v.every(Number.isFinite))throw new TypeError('finite 3-vector required');const n=Math.hypot(...v);if(n===0)throw new RangeError('zero direction');return v.map(x=>x/n);}
export function radecVector(raDeg,decDeg){finite(raDeg,'RA');finite(decDeg,'declination',-90,90);const r=raDeg*DEG,d=decDeg*DEG;return [Math.cos(d)*Math.cos(r),Math.cos(d)*Math.sin(r),Math.sin(d)];}
export function vectorRaDec(v){const u=unit(v);return {raDeg:wrapDeg(Math.atan2(u[1],u[0])/DEG),decDeg:Math.asin(clamp(u[2]))/DEG};}
export function julianDate(utc){const ms=utc instanceof Date?utc.getTime():utc;finite(ms,'UTC milliseconds',-8640000000000000,8640000000000000);return ms/86400000+2440587.5;}
export const julianYear=jd=>2000+(finite(jd,'Julian day')-2451545)/365.25;
export function gmstDeg(jdUt1){const d=finite(jdUt1,'UT1 Julian day')-2451545,T=d/36525;return wrapDeg(280.46061837+360.98564736629*d+.000387933*T*T-T*T*T/38710000);}
const rz=(v,a)=>[v[0]*Math.cos(a)-v[1]*Math.sin(a),v[0]*Math.sin(a)+v[1]*Math.cos(a),v[2]];
const ry=(v,a)=>[v[0]*Math.cos(a)+v[2]*Math.sin(a),v[1],-v[0]*Math.sin(a)+v[2]*Math.cos(a)];
const rx=(v,a)=>[v[0],v[1]*Math.cos(a)-v[2]*Math.sin(a),v[1]*Math.sin(a)+v[2]*Math.cos(a)];
/** IAU 1976 precession from mean equinox J2000 to mean equinox of date. */
export function precessJ2000(v,jdTt){const t=(finite(jdTt,'TT Julian day')-2451545)/36525;
 const zeta=(2306.2181*t+.30188*t*t+.017998*t*t*t)*ARCSEC;
 const z=(2306.2181*t+1.09468*t*t+.018203*t*t*t)*ARCSEC;
 const theta=(2004.3109*t-.42665*t*t-.041833*t*t*t)*ARCSEC;
 return rz(ry(rz(unit(v),zeta),-theta),z);
}
/** Four dominant nutation terms: an explicitly truncated model, NOT IAU 2000A. */
export function nutation(jdTt){const t=(jdTt-2451545)/36525;
 const O=(125.04452-1934.136261*t)*DEG,L=(280.4665+36000.7698*t)*DEG,M=(218.3165+481267.8813*t)*DEG;
 const dpsi=(-17.20*Math.sin(O)-1.32*Math.sin(2*L)-.23*Math.sin(2*M)+.21*Math.sin(2*O))*ARCSEC;
 const deps=(9.20*Math.cos(O)+.57*Math.cos(2*L)+.10*Math.cos(2*M)-.09*Math.cos(2*O))*ARCSEC;
 const eps=(23.439291111-.013004167*t-.000000164*t*t+.000000504*t*t*t)*DEG;
 return {dpsi,deps,eps};
}
export function nutate(v,jdTt){const n=nutation(jdTt);return rx(rz(rx(unit(v),-n.eps),n.dpsi),n.eps+n.deps);}
/** muAlphaStar, NOT dRA/dt. Missing motion remains flagged by observeStar. */
export function propagateJ2000(star,jyear){
 const u=radecVector(star.raDeg,star.decDeg),dt=finite(jyear,'Julian year')-finite(star.epochJyear??2000,'catalogue epoch');
 const ra=star.raDeg*DEG,dec=star.decDeg*DEG;
 const eRa=[-Math.sin(ra),Math.cos(ra),0],eDec=[-Math.cos(ra)*Math.sin(dec),-Math.sin(ra)*Math.sin(dec),Math.cos(dec)];
 const p=star.pmRaCosDecMasYr,q=star.pmDecMasYr;
 if(p==null||q==null)return u; // explicit constant-direction assumption; NOT a measured zero
 finite(p,'muAlphaStar');finite(q,'muDelta');
 const tangent=u.map((_,i)=>(p*eRa[i]+q*eDec[i])*MAS);
 // Perspective acceleration is meaningful only with a measured positive distance and RV.
 if(star.distancePc!=null&&star.radialVelocityKmS!=null){const dist=finite(star.distancePc,'distance pc',Number.MIN_VALUE)*206264.806247096;
  const rv=finite(star.radialVelocityKmS,'radial velocity')*31557600/149597870.7;
  return unit(u.map((x,i)=>x*dist+dt*(tangent[i]*dist+rv*x)));
 }
 return unit(u.map((x,i)=>x+dt*tangent[i]));
}
/** Special-relativistic aberration. Both direction and observer velocity/c use J2000 axes. */
export function aberrate(v,observerVelocityOverC){const u=unit(v),b=checkedVector(observerVelocityOverC,'observer velocity/c',.01);const bm1=Math.sqrt(1-dot(b,b)),ub=dot(u,b),w=1+ub/(1+bm1);return unit(u.map((x,i)=>bm1*x+w*b[i]));}
function checkedVector(v,name,maxNorm){if(!Array.isArray(v)||v.length!==3||!v.every(Number.isFinite)||Math.hypot(...v)>maxNorm)throw new RangeError('Invalid '+name);return [...v];}
const applyColumns=(columns,v)=>v.map((_,i)=>columns[0][i]*v[0]+columns[1][i]*v[1]+columns[2][i]*v[2]);
const inverseColumns=(columns,v)=>columns.map(c=>dot(c,v));
const PC_AU=206264.806247096,AU_KM=149597870.7,C_AU_DAY=173.1446326846693;
function precessionColumns(jdTt){return [[1,0,0],[0,1,0],[0,0,1]].map(v=>precessJ2000(v,jdTt));}
/** Low-order heliocentric Earth, not a DE barycentric ephemeris. USNO solar formula;
 * undo the approximate solar aberration before inverting to geometric Earth position.
 * Position and central-difference velocity are both mean J2000 equatorial AU, AU/day. */
function earthPosition(jdTt){
 const d=jdTt-2451545,g=wrapDeg(357.529+.98560028*d)*DEG,q=wrapDeg(280.459+.98564736*d);
 const r=1.00014-.01671*Math.cos(g)-.00014*Math.cos(2*g);
 const l=(q+1.915*Math.sin(g)+.020*Math.sin(2*g)+20.4898/(3600*r))*DEG,e=nutation(jdTt).eps;
 return inverseColumns(precessionColumns(jdTt),[-r*Math.cos(l),-r*Math.sin(l)*Math.cos(e),-r*Math.sin(l)*Math.sin(e)]);
}
export function earthState(jdTt){finite(jdTt,'TT Julian day');const step=.02,a=earthPosition(jdTt-step),b=earthPosition(jdTt+step);return {positionAu:earthPosition(jdTt),velocityAuDay:a.map((v,i)=>(b[i]-v)/(2*step)),frame:'mean-J2000',origin:'heliocentric',model:'USNO-low-order-with-central-difference'};}
function spaceState(star,jyear){
 const u=radecVector(star.raDeg,star.decDeg),dt=jyear-finite(star.epochJyear??2000,'epoch'),distance=star.distancePc==null?null:finite(star.distancePc,'distancePc',Number.MIN_VALUE)*PC_AU;
 if(distance==null)return {direction:propagateJ2000(star,jyear),positionAu:null};
 const ra=star.raDeg*DEG,de=star.decDeg*DEG,hasMotion=star.pmRaCosDecMasYr!=null&&star.pmDecMasYr!=null;
 const p=hasMotion?finite(star.pmRaCosDecMasYr,'muAlphaStar')*MAS:0,q=hasMotion?finite(star.pmDecMasYr,'muDelta')*MAS:0;
 const er=[-Math.sin(ra),Math.cos(ra),0],ed=[-Math.cos(ra)*Math.sin(de),-Math.sin(ra)*Math.sin(de),Math.cos(de)];
 const rv=star.radialVelocityKmS==null?0:finite(star.radialVelocityKmS,'RV')*31557600/AU_KM;
 const positionAu=u.map((x,i)=>x*distance+dt*(distance*(p*er[i]+q*ed[i])+rv*x));return {direction:unit(positionAu),positionAu};
}
export function equatorialToHorizontal(raDeg,decDeg,lstDeg,latDeg){
 finite(raDeg,'RA');finite(decDeg,'declination',-90,90);finite(lstDeg,'sidereal angle');finite(latDeg,'latitude',-90,90);
 const H=(lstDeg-raDeg)*DEG,d=decDeg*DEG,p=latDeg*DEG;
 const east=-Math.cos(d)*Math.sin(H),north=Math.sin(d)*Math.cos(p)-Math.cos(d)*Math.cos(H)*Math.sin(p),up=Math.sin(d)*Math.sin(p)+Math.cos(d)*Math.cos(H)*Math.cos(p);
 return {altDeg:Math.asin(clamp(up))/DEG,azDeg:Math.hypot(east,north)<1e-14?0:wrapDeg(Math.atan2(east,north)/DEG),enu:[east,north,up]};
}
/** Saemundsson standard-atmosphere refraction; local anomalies/ducting are not modelled. */
export function refractionDeg(altDeg,pressureHpa=0,temperatureC=10){
 finite(altDeg,'geometric altitude',-1,90);finite(pressureHpa,'pressure',0,1100);finite(temperatureC,'temperature',-90,70);
 if(pressureHpa===0||altDeg>=89.9)return 0;
 return Math.max(0,(1.02/Math.tan((altDeg+10.3/(altDeg+5.11))*DEG))/60*(pressureHpa/1010)*(283/(273+temperatureC)));
}
/** Immutable shared frame. UT1 controls Earth rotation; TT controls ephemeris/axes.
 * Missing DUT1/polar motion cannot be promoted to measured precision. Explicit meanOnly
 * is a geometric mean-axes test profile: aberration/parallax default off in that profile. */
export function observationFrame(observer){
 for(const k of ["meanOnly","parallax","aberration"])if(observer[k]!=null&&typeof observer[k]!=="boolean")throw new TypeError(k+" must be a boolean");
 const t=timeScales(observer),lat=finite(observer.latDeg,'latitude',-90,90),lon=finite(observer.lonDeg,'longitude',-180,180);
 const pressure=finite(observer.pressureHpa??0,'pressure',0,1100),temp=finite(observer.temperatureC??10,'temperature',-90,70),height=finite(observer.heightM??0,'height metres',-500,100000);
 const n=nutation(t.jdTt),mean=observer.meanOnly===true,warnings=[...t.warnings,'polar-motion-not-applied','solar-gravitational-deflection-not-applied'];
 const gast=wrapDeg(gmstDeg(t.jdUt1)+(mean?0:n.dpsi*Math.cos(n.eps+n.deps)/DEG)),lst=wrapDeg(gast+lon);
 const rotation=precessionColumns(t.jdTt).map(v=>mean?v:nutate(v,t.jdTt));
 const parallax=observer.parallax??!mean,aberration=observer.aberration??!mean;let earth;
 if(observer.earthBarycentric!=null){const e=observer.earthBarycentric;finite(e.jdTt,'external ephemeris timestamp');if(Math.abs(e.jdTt-t.jdTt)>1e-7||!['ICRS','mean-J2000'].includes(e.frame))throw new RangeError('External Earth state must match current TT and declared J2000/ICRS axes');earth={positionAu:checkedVector(e.positionAu,'barycentric position',2),velocityAuDay:checkedVector(e.velocityAuDay,'barycentric velocity',.03)};if(e.frame==='ICRS')warnings.push('ICRS-frame-bias-not-applied');}
 else {earth=earthState(t.jdTt);warnings.push('heliocentric-earth-approximation');}
 const la=lat*DEG,theta=lst*DEG,e2=6.6943799901413165e-3,N=6378137/Math.sqrt(1-e2*Math.sin(la)**2);
 const siteDate=[(N+height)*Math.cos(la)*Math.cos(theta),(N+height)*Math.cos(la)*Math.sin(theta),(N*(1-e2)+height)*Math.sin(la)].map(x=>x/(AU_KM*1000));
 const site=inverseColumns(rotation,siteDate),diurnal=inverseColumns(rotation,[-siteDate[1],siteDate[0],0]).map(x=>x*2*Math.PI*1.00273781191135448);
 const positionAu=earth.positionAu.map((x,i)=>x+site[i]);
 const velocityOverC=observer.velocityOverC!=null?checkedVector(observer.velocityOverC,'observer velocity/c',.01):earth.velocityAuDay.map((x,i)=>(x+diurnal[i])/C_AU_DAY);
 if(observer.velocityOverC!=null)warnings.push('explicit-total-observer-velocity-no-auto-diurnal-addition');
 const snapshot=Object.freeze({utcMs:observer.utcMs,latDeg:lat,lonDeg:lon,pressureHpa:pressure,temperatureC:temp,heightM:height});
 return Object.freeze({observer:snapshot,...t,jyear:julianYear(t.jdTt),latDeg:lat,lstDeg:lst,meanOnly:mean,rotation:Object.freeze(rotation.map(Object.freeze)),positionAu:Object.freeze(positionAu),velocityOverC:Object.freeze(velocityOverC),parallax:!!parallax,aberration:!!aberration,warnings:Object.freeze(warnings)});
}
export function observeStar(star,observerOrFrame){
 const f=observerOrFrame.rotation?observerOrFrame:observationFrame(observerOrFrame),o=f.observer,state=spaceState(star,f.jyear),warnings=[...f.warnings];
 const parallaxApplied=f.parallax&&state.positionAu!==null;let v=parallaxApplied?unit(state.positionAu.map((x,i)=>x-f.positionAu[i])):state.direction;
 if(f.parallax&&!parallaxApplied)warnings.push('distance-unavailable-parallax-not-applied');
 if(star.radialVelocityKmS==null&&star.distancePc!=null)warnings.push('radial-velocity-unavailable-no-radial-perspective');
 if(f.aberration)v=aberrate(v,f.velocityOverC);v=applyColumns(f.rotation,v);
 const eq=vectorRaDec(v),h=equatorialToHorizontal(eq.raDeg,eq.decDeg,f.lstDeg,f.latDeg);
 let ref=0;if(h.altDeg>=-1&&o.pressureHpa>0)ref=refractionDeg(h.altDeg,o.pressureHpa,o.temperatureC);const app=h.altDeg+ref,az=h.azDeg*DEG,al=app*DEG;
 if(star.pmRaCosDecMasYr==null||star.pmDecMasYr==null)warnings.push('proper-motion-unavailable');
 return {...h,enuGeometric:h.enu,enu:[Math.cos(al)*Math.sin(az),Math.cos(al)*Math.cos(az),Math.sin(al)],geometricAltDeg:h.altDeg,altDeg:app,refractionDeg:ref,aboveHorizon:app>=0,aboveGeometricHorizon:h.altDeg>=0,parallaxApplied,aberrationApplied:f.aberration,raOfDateDeg:eq.raDeg,decOfDateDeg:eq.decDeg,utcMs:o.utcMs,warnings};
}
export function angularSeparation(a,b){a=unit(a);b=unit(b);return Math.atan2(Math.hypot(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]),clamp(dot(unit(a),unit(b))))/DEG;}
export function slerp(a,b,t){finite(t,'interpolation',0,1);a=unit(a);b=unit(b);const c=clamp(dot(a,b));if(c>1-1e-12)return unit(a.map((v,i)=>v*(1-t)+b[i]*t));if(c< -1+1e-9)throw new RangeError('antipodal annotation endpoints are ambiguous');const w=Math.acos(c),s=Math.sin(w);return unit(a.map((v,i)=>(v*Math.sin((1-t)*w)+b[i]*Math.sin(t*w))/s));}
