(function(){"use strict";
// real-sky/core/src/time-scales.mjs
/** Time policy: USNO TAI-UTC table, IERS Bulletin C72 (2026-07-06), NASA historical DeltaT.
 * See docs/CHECKPOINT_4.md. Numeric POSIX milliseconds cannot represent a leap-second label.
 * No host clock or time zone is read. Future offsets are explicitly uncertain, not predicted.
 */
const TS_DAY=86400000;
const TS_LEAPS=[[1972,1,10],[1972,7,11],[1973,1,12],[1974,1,13],[1975,1,14],[1976,1,15],[1977,1,16],[1978,1,17],[1979,1,18],[1980,1,19],[1981,7,20],[1982,7,21],[1983,7,22],[1985,7,23],[1988,1,24],[1990,1,25],[1991,1,26],[1992,7,27],[1993,7,28],[1994,7,29],[1996,1,30],[1997,7,31],[1999,1,32],[2006,1,33],[2009,1,34],[2012,7,35],[2015,7,36],[2017,1,37]].map(([y,m,n])=>[Date.UTC(y,m-1,1),n]);
const TS_DRIFTS=[[1961,1,1.422818,37300,.001296],[1961,8,1.372818,37300,.001296],[1962,1,1.845858,37665,.0011232],[1963,11,1.945858,37665,.0011232],[1964,1,3.240130,38761,.001296],[1964,4,3.340130,38761,.001296],[1964,9,3.440130,38761,.001296],[1965,1,3.540130,38761,.001296],[1965,3,3.640130,38761,.001296],[1965,7,3.740130,38761,.001296],[1965,9,3.840130,38761,.001296],[1966,1,4.313170,39126,.002592],[1968,2,4.213170,39126,.002592]].map(([y,m,a,b,c])=>[Date.UTC(y,m-1,1),a,b,c]);
function tsNumber(x,label,min=-Infinity,max=Infinity){if(typeof x!=='number'||!Number.isFinite(x)||x<min||x>max)throw new RangeError(label+' out of range');return x;}
function historicDeltaT(y){let t;if(y<1920){t=y-1900;return -2.79+1.494119*t-.0598939*t*t+.0061966*t**3-.000197*t**4;}if(y<1941){t=y-1920;return 21.2+.84493*t-.0761*t*t+.0020936*t**3;}t=y-1950;return 29.07+.407*t-t*t/233+t**3/2547;}
function timeScales(observer){
 const ms=tsNumber(observer.utcMs,'UTC milliseconds'),date=new Date(ms),year=date.getUTCFullYear();
 if(!Number.isFinite(year)||year<1900||year>2100)throw new RangeError('supported dates: Gregorian1900–2100');
 const jdUtc=ms/TS_DAY+2440587.5,dut1=tsNumber(observer.dut1Seconds??0,'UT1-UTC',-1,1),warnings=[];let offset;
 if(observer.dut1Seconds==null)warnings.push('UT1-assumed-UTC');
 if(observer.ttMinusUtcSeconds!=null)offset=tsNumber(observer.ttMinusUtcSeconds,'TT-UTC',-200,1000);
 else if(ms>=TS_LEAPS[0][0]){offset=32.184+TS_LEAPS.filter(r=>r[0]<=ms).at(-1)[1];if(ms>=Date.UTC(2027,0,1))warnings.push('future-TAI-UTC-assumed-last-confirmed');}
 else if(ms>=TS_DRIFTS[0][0]){const r=TS_DRIFTS.filter(r=>r[0]<=ms).at(-1);offset=32.184+r[1]+(jdUtc-2400000.5-r[2])*r[3];}
 else{offset=historicDeltaT(year+(date.getUTCMonth()+.5)/12)+dut1;warnings.push('pre1961-proleptic-time-with-estimated-deltaT');}
 return {jdUtc,jdUt1:jdUtc+dut1/86400,jdTt:jdUtc+offset/86400,dut1Seconds:dut1,ttMinusUtcSeconds:offset,warnings};
}

// real-sky/core/src/astronomy.mjs

/** Astronomical geometry. Degrees externally; vectors and rotations in radians internally.
 * Sources/accuracy: docs/RESEARCH.md. This is a bounded widget model, not a SOFA replacement.
 * No Date.now(), local civil-time parser, random position, or browser geolocation is used here.
 */
const DEG=Math.PI/180, ARCSEC=DEG/3600, MAS=ARCSEC/1000;
const clamp=(x,lo=-1,hi=1)=>Math.max(lo,Math.min(hi,x));
const wrapDeg=x=>((x%360)+360)%360;
function finite(x,name,min=-Infinity,max=Infinity){if(typeof x!=='number'||!Number.isFinite(x)||x<min||x>max)throw new RangeError(`${name} must be finite in [${min}, ${max}]`);return x;}
const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
function unit(v){if(!Array.isArray(v)||v.length!==3||!v.every(Number.isFinite))throw new TypeError('finite 3-vector required');const n=Math.hypot(...v);if(n===0)throw new RangeError('zero direction');return v.map(x=>x/n);}
function radecVector(raDeg,decDeg){finite(raDeg,'RA');finite(decDeg,'declination',-90,90);const r=raDeg*DEG,d=decDeg*DEG;return [Math.cos(d)*Math.cos(r),Math.cos(d)*Math.sin(r),Math.sin(d)];}
function vectorRaDec(v){const u=unit(v);return {raDeg:wrapDeg(Math.atan2(u[1],u[0])/DEG),decDeg:Math.asin(clamp(u[2]))/DEG};}
function julianDate(utc){const ms=utc instanceof Date?utc.getTime():utc;finite(ms,'UTC milliseconds',-8640000000000000,8640000000000000);return ms/86400000+2440587.5;}
const julianYear=jd=>2000+(finite(jd,'Julian day')-2451545)/365.25;
function gmstDeg(jdUt1){const d=finite(jdUt1,'UT1 Julian day')-2451545,T=d/36525;return wrapDeg(280.46061837+360.98564736629*d+.000387933*T*T-T*T*T/38710000);}
const rz=(v,a)=>[v[0]*Math.cos(a)-v[1]*Math.sin(a),v[0]*Math.sin(a)+v[1]*Math.cos(a),v[2]];
const ry=(v,a)=>[v[0]*Math.cos(a)+v[2]*Math.sin(a),v[1],-v[0]*Math.sin(a)+v[2]*Math.cos(a)];
const rx=(v,a)=>[v[0],v[1]*Math.cos(a)-v[2]*Math.sin(a),v[1]*Math.sin(a)+v[2]*Math.cos(a)];
/** IAU 1976 precession from mean equinox J2000 to mean equinox of date. */
function precessJ2000(v,jdTt){const t=(finite(jdTt,'TT Julian day')-2451545)/36525;
 const zeta=(2306.2181*t+.30188*t*t+.017998*t*t*t)*ARCSEC;
 const z=(2306.2181*t+1.09468*t*t+.018203*t*t*t)*ARCSEC;
 const theta=(2004.3109*t-.42665*t*t-.041833*t*t*t)*ARCSEC;
 return rz(ry(rz(unit(v),zeta),-theta),z);
}
/** Four dominant nutation terms: an explicitly truncated model, NOT IAU 2000A. */
function nutation(jdTt){const t=(jdTt-2451545)/36525;
 const O=(125.04452-1934.136261*t)*DEG,L=(280.4665+36000.7698*t)*DEG,M=(218.3165+481267.8813*t)*DEG;
 const dpsi=(-17.20*Math.sin(O)-1.32*Math.sin(2*L)-.23*Math.sin(2*M)+.21*Math.sin(2*O))*ARCSEC;
 const deps=(9.20*Math.cos(O)+.57*Math.cos(2*L)+.10*Math.cos(2*M)-.09*Math.cos(2*O))*ARCSEC;
 const eps=(23.439291111-.013004167*t-.000000164*t*t+.000000504*t*t*t)*DEG;
 return {dpsi,deps,eps};
}
function nutate(v,jdTt){const n=nutation(jdTt);return rx(rz(rx(unit(v),-n.eps),n.dpsi),n.eps+n.deps);}
/** muAlphaStar, NOT dRA/dt. Missing motion remains flagged by observeStar. */
function propagateJ2000(star,jyear){
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
function aberrate(v,observerVelocityOverC){const u=unit(v),b=checkedVector(observerVelocityOverC,'observer velocity/c',.01);const bm1=Math.sqrt(1-dot(b,b)),ub=dot(u,b),w=1+ub/(1+bm1);return unit(u.map((x,i)=>bm1*x+w*b[i]));}
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
function earthState(jdTt){finite(jdTt,'TT Julian day');const step=.02,a=earthPosition(jdTt-step),b=earthPosition(jdTt+step);return {positionAu:earthPosition(jdTt),velocityAuDay:a.map((v,i)=>(b[i]-v)/(2*step)),frame:'mean-J2000',origin:'heliocentric',model:'USNO-low-order-with-central-difference'};}
function spaceState(star,jyear){
 const u=radecVector(star.raDeg,star.decDeg),dt=jyear-finite(star.epochJyear??2000,'epoch'),distance=star.distancePc==null?null:finite(star.distancePc,'distancePc',Number.MIN_VALUE)*PC_AU;
 if(distance==null)return {direction:propagateJ2000(star,jyear),positionAu:null};
 const ra=star.raDeg*DEG,de=star.decDeg*DEG,hasMotion=star.pmRaCosDecMasYr!=null&&star.pmDecMasYr!=null;
 const p=hasMotion?finite(star.pmRaCosDecMasYr,'muAlphaStar')*MAS:0,q=hasMotion?finite(star.pmDecMasYr,'muDelta')*MAS:0;
 const er=[-Math.sin(ra),Math.cos(ra),0],ed=[-Math.cos(ra)*Math.sin(de),-Math.sin(ra)*Math.sin(de),Math.cos(de)];
 const rv=star.radialVelocityKmS==null?0:finite(star.radialVelocityKmS,'RV')*31557600/AU_KM;
 const positionAu=u.map((x,i)=>x*distance+dt*(distance*(p*er[i]+q*ed[i])+rv*x));return {direction:unit(positionAu),positionAu};
}
function equatorialToHorizontal(raDeg,decDeg,lstDeg,latDeg){
 finite(raDeg,'RA');finite(decDeg,'declination',-90,90);finite(lstDeg,'sidereal angle');finite(latDeg,'latitude',-90,90);
 const H=(lstDeg-raDeg)*DEG,d=decDeg*DEG,p=latDeg*DEG;
 const east=-Math.cos(d)*Math.sin(H),north=Math.sin(d)*Math.cos(p)-Math.cos(d)*Math.cos(H)*Math.sin(p),up=Math.sin(d)*Math.sin(p)+Math.cos(d)*Math.cos(H)*Math.cos(p);
 return {altDeg:Math.asin(clamp(up))/DEG,azDeg:Math.hypot(east,north)<1e-14?0:wrapDeg(Math.atan2(east,north)/DEG),enu:[east,north,up]};
}
/** Saemundsson standard-atmosphere refraction; local anomalies/ducting are not modelled. */
function refractionDeg(altDeg,pressureHpa=0,temperatureC=10){
 finite(altDeg,'geometric altitude',-1,90);finite(pressureHpa,'pressure',0,1100);finite(temperatureC,'temperature',-90,70);
 if(pressureHpa===0||altDeg>=89.9)return 0;
 return Math.max(0,(1.02/Math.tan((altDeg+10.3/(altDeg+5.11))*DEG))/60*(pressureHpa/1010)*(283/(273+temperatureC)));
}
/** Immutable shared frame. UT1 controls Earth rotation; TT controls ephemeris/axes.
 * Missing DUT1/polar motion cannot be promoted to measured precision. Explicit meanOnly
 * is a geometric mean-axes test profile: aberration/parallax default off in that profile. */
function observationFrame(observer){
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
function observeStar(star,observerOrFrame){
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
function angularSeparation(a,b){a=unit(a);b=unit(b);return Math.atan2(Math.hypot(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]),clamp(dot(unit(a),unit(b))))/DEG;}
function slerp(a,b,t){finite(t,'interpolation',0,1);a=unit(a);b=unit(b);const c=clamp(dot(a,b));if(c>1-1e-12)return unit(a.map((v,i)=>v*(1-t)+b[i]*t));if(c< -1+1e-9)throw new RangeError('antipodal annotation endpoints are ambiguous');const w=Math.acos(c),s=Math.sin(w);return unit(a.map((v,i)=>(v*Math.sin((1-t)*w)+b[i]*Math.sin(t*w))/s));}

// real-sky/core/src/projection.mjs

/** All-sky map: north up, east LEFT, zenith centred. This is a sky chart seen from inside.
 * Set eastLeft:false only for an explicitly labelled ENU diagram, not silently.
 */
function projectAllSky(h,{width=325,height=325,eastLeft=true,padding=4}={}){
 finite(width,'width',1);finite(height,'height',1);finite(h.altDeg,'altitude',-90,90);finite(h.azDeg,'azimuth');
 finite(padding,'padding',0,Math.min(width,height)/2-Number.EPSILON);const R=Math.min(width,height)/2-padding;if(R<=0)throw new RangeError('No all-sky radius');const r=(90-h.altDeg)/90*R,a=h.azDeg*DEG;
 return {x:width/2+(eastLeft?-1:1)*r*Math.sin(a),y:height/2-r*Math.cos(a),visible:h.altDeg>=0};
}
function unprojectAllSky(x,y,{width=325,height=325,eastLeft=true,padding=4}={}){
 finite(width,'width',1);finite(height,'height',1);finite(x,'x');finite(y,'y');finite(padding,'padding',0,Math.min(width,height)/2-Number.EPSILON);const R=Math.min(width,height)/2-padding;if(R<=0)throw new RangeError('No all-sky radius');const dx=(x-width/2)*(eastLeft?-1:1),dy=height/2-y,r=Math.hypot(dx,dy);
 return {altDeg:90-r/R*90,azDeg:r<1e-12?0:wrapDeg(Math.atan2(dx,dy)/DEG)};
}
/** Exact legacy PR38 geometry, expressed in north-zero/east-positive azimuth.
 * It is an anisotropically compressed crop, NOT a camera with a physical field of view.
 */
function projectWidgetDome(h){finite(h.altDeg,'altitude',-90,90);finite(h.azDeg,'azimuth');const r=(90-h.altDeg)/90*270,a=h.azDeg*DEG;
 const x=162-r*Math.sin(a),y=-30+.8*r*Math.cos(a);
 return {x,y,visible:h.altDeg>=0&&x>=-24&&x<=349&&y>=-24&&y<=250};
}
/** Perspective camera. True azimuth north0/east90; positive roll rotates camera right
 * towards the unrolled up axis. Altitude/azimuth always describe one rigid camera. */
function cameraBasis(c={}){
 const width=finite(c.width??325,'width',1,16384),height=finite(c.height??530,'height',1,16384),az=finite(c.azDeg??180,'camera azimuth'),alt=finite(c.altDeg??35,'camera altitude',-90,90),fov=finite(c.fovYDeg??90,'vertical FOV',1,170),roll=finite(c.rollDeg??0,'camera roll')*DEG;
 const a=az*DEG,e=alt*DEG,fw=[Math.cos(e)*Math.sin(a),Math.cos(e)*Math.cos(a),Math.sin(e)],rt=[Math.cos(a),-Math.sin(a),0],up=[-Math.sin(e)*Math.sin(a),-Math.sin(e)*Math.cos(a),Math.cos(e)];
 return {width,height,f:height/(2*Math.tan(fov*DEG/2)),fw,rt:rt.map((v,i)=>v*Math.cos(roll)+up[i]*Math.sin(roll)),up:up.map((v,i)=>v*Math.cos(roll)-rt[i]*Math.sin(roll)),fovXDeg:2*Math.atan(width/height*Math.tan(fov*DEG/2))/DEG};
}
function cameraGeometry(c={}){const b=cameraBasis(c);return {width:b.width,height:b.height,focalPixels:b.f,fovXDeg:b.fovXDeg};}
function projectPerspective(h,c={}){
 finite(h.altDeg,'altitude',-90,90);finite(h.azDeg,'azimuth');const b=cameraBasis(c),ha=h.azDeg*DEG,he=h.altDeg*DEG,v=[Math.cos(he)*Math.sin(ha),Math.cos(he)*Math.cos(ha),Math.sin(he)];
 const d=(u,w)=>u.reduce((s,x,i)=>s+x*w[i],0),z=d(v,b.fw);if(z<=0)return null;
 const x=b.width/2+b.f*d(v,b.rt)/z,y=b.height/2-b.f*d(v,b.up)/z,inFrame=x>=0&&x<=b.width&&y>=0&&y<=b.height;
 return {x,y,inFrame,visible:h.altDeg>=0&&inFrame};
}
function unprojectPerspective(x,y,c={}){
 finite(x,'x');finite(y,'y');const b=cameraBasis(c),u=(x-b.width/2)/b.f,w=(b.height/2-y)/b.f,v=b.fw.map((a,i)=>a+u*b.rt[i]+w*b.up[i]),len=Math.hypot(...v),r=Math.hypot(v[0],v[1]);
 return {altDeg:Math.atan2(v[2],r)/DEG,azDeg:r<1e-14?0:wrapDeg(Math.atan2(v[0],v[1])/DEG),enu:v.map(a=>a/len)};
}

/** CP7.5: hoist rigid camera constants once per render, NOT once per UTC/location.
 * The per-ray arithmetic remains identical to the public reference functions.
 * No approximate ray grid, frame cache, or new celestial coordinate system.
 */
function prepareInverseProjection(view={}){
 const c={...view},type=c.type??'camera';
 if(type==='camera'){
  const b=cameraBasis(c);
  return (x,y)=>{finite(x,'x');finite(y,'y');const u=(x-b.width/2)/b.f,w=(b.height/2-y)/b.f,v=b.fw.map((a,i)=>a+u*b.rt[i]+w*b.up[i]),len=Math.hypot(...v),r=Math.hypot(v[0],v[1]);
   return {altDeg:Math.atan2(v[2],r)/DEG,azDeg:r<1e-14?0:wrapDeg(Math.atan2(v[0],v[1])/DEG),enu:v.map(a=>a/len)};};
 }
 if(type==='allsky'){
  const width=finite(c.width??325,'width',1),height=finite(c.height??325,'height',1),padding=finite(c.padding??4,'padding',0,Math.min(width,height)/2-Number.EPSILON),eastLeft=c.eastLeft??true,R=Math.min(width,height)/2-padding;
  if(R<=0)throw new RangeError('No all-sky radius');
  return (x,y)=>{finite(x,'x');finite(y,'y');const dx=(x-width/2)*(eastLeft?-1:1),dy=height/2-y,r=Math.hypot(dx,dy);return {altDeg:90-r/R*90,azDeg:r<1e-12?0:wrapDeg(Math.atan2(dx,dy)/DEG)};};
 }
 throw new RangeError('Prepared projection must be camera or allsky');
}

// real-sky/core/src/photometry.mjs
/** Relative stellar photometry and spectral transport. Not absolute display calibration.
 * V magnitude -> exact relative V-band flux; using it as photopic Y is an explicit
 * passband approximation. B-V -> blackbody colour proxy is NOT a measured SED or Teff.
 * See docs/RESEARCH.md and provenance/sources.json for methods and limitations.
 */

const luminance=rgb=>.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];
function magnitudeFlux(m){return 10**(-.4*finite(m,'V magnitude',-30,40));}
function colourTemperature(bv){if(bv==null)return null;finite(bv,'B-V',-.5,5);
 // Values outside the useful blackbody-colour interval are not extrapolated.
 if(bv<-.4||bv>2.0)return null;
 return 4600*(1/(.92*bv+1.7)+1/(.92*bv+.62));
}
/** Wyman/Sloan/Shirley 2013, equation 4/table 1, 1931 2-degree observer. */
function cie1931(w){finite(w,'wavelength nm',360,830);
 const g=(c,a,b)=>Math.exp(-.5*((w-c)*(w<c?a:b))**2);
 return [.362*g(442,.0624,.0374)+1.056*g(599.8,.0264,.0323)-.065*g(501.1,.049,.0382),.821*g(568.8,.0213,.0247)+.286*g(530.9,.0613,.0322),1.217*g(437,.0845,.0278)+.681*g(459,.0385,.0725)];
}
function airmass(apparentAltDeg){finite(apparentAltDeg,'apparent altitude',0,90);return 1/(Math.sin(apparentAltDeg*DEG)+.50572*(apparentAltDeg+6.07995)**-1.6364);}
function transmission(X,tau){finite(X,'airmass',0,1000);finite(tau,'optical depth',0,1000);return Math.exp(-X*tau);}
function opticalDepth(w,{rayleighTau550=.10,aerosolTau550=.06,angstromExponent=1.3,greyTau=0}={}){
 finite(w,'wavelength',360,830);finite(rayleighTau550,'Rayleigh optical depth',0,100);finite(aerosolTau550,'aerosol optical depth',0,100);finite(angstromExponent,'Angstrom exponent',0,4);finite(greyTau,'grey optical depth',0,100);
 return rayleighTau550*(550/w)**4.08+aerosolTau550*(550/w)**angstromExponent+greyTau;
}
function xyzToLinearRgb([x,y,z]){return [3.2404542*x-1.5371385*y-.4985314*z,-.969266*x+1.8760108*y+.041556*z,.0556434*x-.2040259*y+1.0572252*z];}
const bins=Array.from({length:95},(_,i)=>{const w=360+i*5;return {w,xyz:cie1931(w),weight:i===0||i===94?2.5:5};});
const spectra=new Map();
/** A normalised shape, integral against ybar = 1 before terrestrial extinction. */
function spectrumForColour(bv){const key=bv==null?'unknown':String(bv);if(spectra.has(key))return spectra.get(key);
 const T=colourTemperature(bv),fallback=T==null;
 // An unknown source gets a declared neutral-display proxy, not an invented catalogue colour.
 const temperature=T??6500,base=bins.map(({w})=>1/(w**5*Math.expm1(1.438776877e7/(w*temperature))));
 const Y=base.reduce((a,s,i)=>a+s*bins[i].xyz[1]*bins[i].weight,0);
 const value={samples:base.map(x=>x/Y),temperatureProxyK:T,fallback};
 if(spectra.size<2048)spectra.set(key,value);return value;
}
/** Caller may supply a measured 95-bin SED, normalised to Y=1 on the same 360..830/5nm grid.
 * This optional route is not used by the bundled catalogue and must carry its own provenance.
 */
function starRgbFlux(star,altDeg,atmosphere={}){
 if(altDeg<0)return {rgb:[0,0,0],colourFallback:star.bv==null,model:'below-horizon'};
 const X=airmass(altDeg),cloud=finite(atmosphere.cloudTransmission??1,'cloud transmission',0,1);
 const proxy=spectrumForColour(star.bv),samples=star.sedYNormalised??proxy.samples;
 if(!Array.isArray(samples)||samples.length!==bins.length||!samples.every(x=>Number.isFinite(x)&&x>=0))throw new TypeError('SED must be 95 finite non-negative samples');
 const xyz=[0,0,0];for(let i=0;i<bins.length;i++){const b=bins[i],p=samples[i]*transmission(X,opticalDepth(b.w,atmosphere))*b.weight;for(let k=0;k<3;k++)xyz[k]+=p*b.xyz[k];}
 let rgb=xyzToLinearRgb(xyz);
 // Gamut mapping: clip negative channels, rescale to retain the XYZ-Y flux, never re-normalise extinction.
 const before=xyz[1];rgb=rgb.map(x=>Math.max(0,x));const y=luminance(rgb);if(y>0)rgb=rgb.map(x=>x*before/y);
 const scale=magnitudeFlux(star.vmag)*cloud;
 return {rgb:rgb.map(x=>x*scale),colourFallback:!star.sedYNormalised&&proxy.fallback,temperatureProxyK:proxy.temperatureProxyK,
 model:star.sedYNormalised?'provided-SED-relative-Y':'B-V-blackbody-proxy; V-as-Y approximation'};
}
function linearToSrgb(x){finite(x,'linear channel',0);return x<=.0031308?12.92*x:1.055*x**(1/2.4)-.055;}
function srgbToLinear(x){finite(x,'sRGB channel',0);return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;}
/** Zero-mean, bounded, deterministic display surrogate; not a forecast of real turbulence.
 * Never changes star position, diameter, catalogue magnitude or identity. Default amplitude=0.
 */
function scintillation(hip,tSeconds,altDeg,amplitude=0){finite(amplitude,'scintillation amplitude',0,.3);if(amplitude===0)return 1;
 const phase=(hip*.61803398875)%1*2*Math.PI,altFactor=.25+.75*(1-Math.sin(clamp(altDeg,0,90)*DEG));
 return 1+amplitude*altFactor*(.6*Math.sin(2*Math.PI*.73*tSeconds+phase)+.4*Math.sin(2*Math.PI*1.17*tSeconds+phase*2.13));
}

// real-sky/core/src/spectral-tables.mjs
// Generated; see vendor/spectral and provenance/cp5-spectral-acquisition.json.
const SPECTRAL_TABLES={"schema":"salah-spectral-tables/1","wavelengthNm":[360,365,370,375,380,385,390,395,400,405,410,415,420,425,430,435,440,445,450,455,460,465,470,475,480,485,490,495,500,505,510,515,520,525,530,535,540,545,550,555,560,565,570,575,580,585,590,595,600,605,610,615,620,625,630,635,640,645,650,655,660,665,670,675,680,685,690,695,700,705,710,715,720,725,730,735,740,745,750,755,760,765,770,775,780,785,790,795,800,805,810,815,820,825,830],"weightsNm":[2.5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,2.5],"cieXYZ":[[0.0001299,3.917e-06,0.0006061],[0.0002321,6.965e-06,0.001086],[0.0004149,1.239e-05,0.001946],[0.0007416,2.202e-05,0.003486],[0.001368,3.9e-05,0.006450001],[0.002236,6.4e-05,0.01054999],[0.004243,0.00012,0.02005001],[0.00765,0.000217,0.03621],[0.01431,0.000396,0.06785001],[0.02319,0.00064,0.1102],[0.04351,0.00121,0.2074],[0.07763,0.00218,0.3713],[0.13438,0.004,0.6456],[0.21477,0.0073,1.0390501],[0.2839,0.0116,1.3856],[0.3285,0.01684,1.62296],[0.34828,0.023,1.74706],[0.34806,0.0298,1.7826],[0.3362,0.038,1.77211],[0.3187,0.048,1.7441],[0.2908,0.06,1.6692],[0.2511,0.0739,1.5281],[0.19536,0.09098,1.28764],[0.1421,0.1126,1.0419],[0.09564,0.13902,0.8129501],[0.05795001,0.1693,0.6162],[0.03201,0.20802,0.46518],[0.0147,0.2586,0.3533],[0.0049,0.323,0.272],[0.0024,0.4073,0.2123],[0.0093,0.503,0.1582],[0.0291,0.6082,0.1117],[0.06327,0.71,0.07824999],[0.1096,0.7932,0.05725001],[0.1655,0.862,0.04216],[0.2257499,0.9148501,0.02984],[0.2904,0.954,0.0203],[0.3597,0.9803,0.0134],[0.4334499,0.9949501,0.008749999],[0.5120501,1.0,0.005749999],[0.5945,0.995,0.0039],[0.6784,0.9786,0.002749999],[0.7621,0.952,0.0021],[0.8425,0.9154,0.0018],[0.9163,0.87,0.001650001],[0.9786,0.8163,0.0014],[1.0263,0.757,0.0011],[1.0567,0.6949,0.001],[1.0622,0.631,0.0008],[1.0456,0.5668,0.0006],[1.0026,0.503,0.00034],[0.9384,0.4412,0.00024],[0.8544499,0.381,0.00019],[0.7514,0.321,0.0001],[0.6424,0.265,4.999999e-05],[0.5419,0.217,3e-05],[0.4479,0.175,2e-05],[0.3608,0.1382,1e-05],[0.2835,0.107,0.0],[0.2187,0.0816,0.0],[0.1649,0.061,0.0],[0.1212,0.04458,0.0],[0.0874,0.032,0.0],[0.0636,0.0232,0.0],[0.04677,0.017,0.0],[0.0329,0.01192,0.0],[0.0227,0.00821,0.0],[0.01584,0.005723,0.0],[0.01135916,0.004102,0.0],[0.008110916,0.002929,0.0],[0.005790346,0.002091,0.0],[0.004109457,0.001484,0.0],[0.002899327,0.001047,0.0],[0.00204919,0.00074,0.0],[0.001439971,0.00052,0.0],[0.0009999493,0.0003611,0.0],[0.0006900786,0.0002492,0.0],[0.0004760213,0.0001719,0.0],[0.0003323011,0.00012,0.0],[0.0002348261,8.48e-05,0.0],[0.0001661505,6e-05,0.0],[0.000117413,4.24e-05,0.0],[8.307527e-05,3e-05,0.0],[5.870652e-05,2.12e-05,0.0],[4.150994e-05,1.499e-05,0.0],[2.935326e-05,1.06e-05,0.0],[2.067383e-05,7.4657e-06,0.0],[1.455977e-05,5.2578e-06,0.0],[1.025398e-05,3.7029e-06,0.0],[7.221456e-06,2.6078e-06,0.0],[5.085868e-06,1.8366e-06,0.0],[3.581652e-06,1.2934e-06,0.0],[2.522525e-06,9.1093e-07,0.0],[1.776509e-06,6.4153e-07,0.0],[1.251141e-06,4.5181e-07,0.0]],"passbands":{"B":[0.0,0.015,0.03,0.082,0.134,0.3505,0.567,0.7435,0.92,0.9490000000000001,0.978,0.989,1.0,0.989,0.978,0.9565,0.935,0.894,0.853,0.7965,0.74,0.69,0.64,0.5880000000000001,0.536,0.48,0.424,0.3745,0.325,0.28,0.235,0.1925,0.15,0.1225,0.095,0.069,0.043,0.026,0.009,0.0045,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],"V":[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.015,0.03,0.0965,0.163,0.3105,0.458,0.619,0.78,0.8734999999999999,0.967,0.9835,1.0,0.9864999999999999,0.973,0.9355,0.898,0.845,0.792,0.738,0.684,0.629,0.574,0.5175,0.461,0.41000000000000003,0.359,0.3145,0.27,0.2335,0.197,0.166,0.135,0.10800000000000001,0.081,0.063,0.045,0.035,0.025,0.021,0.017,0.015,0.013,0.011,0.009,0.0045,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]},"passbandConvention":"photon-weighted response integral of f_lambda * wavelength * response; constant hc cancels","vegaZeroColour":0,"standards":[{"id":"IRAF-HR7001","hip":91262,"hr":7001,"templateClass":"A0V","catalogueBV":-0.001,"spectralType":"A0Vvar","kind":"observed-spectrophotometric-shape","source":"vendor/spectral/hr7001.dat","resolution":"29 sparse continuum bandpasses; log-flux interpolation on 5 nm grid is reconstruction, not 95 measured bins","samples":[1.7511758248027455e-05,1.815819472389263e-05,1.8365527181365837e-05,2.4303141873099898e-05,3.292090241196057e-05,4.4594473474947244e-05,4.82281483397661e-05,4.857794715348742e-05,4.893028305839504e-05,4.8750009842424014e-05,4.722576765610432e-05,4.574918318821525e-05,4.4323675308420595e-05,4.294503537803981e-05,4.172727600006642e-05,4.05568070131552e-05,3.9419170211343206e-05,3.8313444636971214e-05,3.693683153273581e-05,3.5497130342632564e-05,3.43157810423795e-05,3.3266150494018265e-05,3.224862541592712e-05,3.12622237852193e-05,3.0305198296958672e-05,2.9375671220520665e-05,2.8474654783655558e-05,2.760127450234953e-05,2.675468271493639e-05,2.5995862352223207e-05,2.525856376754798e-05,2.4542176556982982e-05,2.3846107628968968e-05,2.3169780713299318e-05,2.255303698704301e-05,2.1966543906223672e-05,2.1395302613181188e-05,2.08389164842587e-05,2.0296999210021473e-05,1.9769174527034782e-05,1.9233771236468064e-05,1.8710043399519125e-05,1.8200576460436913e-05,1.7704982100721655e-05,1.7222882575629562e-05,1.6755070027635462e-05,1.6304477526097446e-05,1.5866002765763042e-05,1.543931986537273e-05,1.5024111707560859e-05,1.4677555315982021e-05,1.4346668048308571e-05,1.4023240223406825e-05,1.3707103677397741e-05,1.339809403744822e-05,1.3096050636306598e-05,1.2800816428765067e-05,1.251634436869122e-05,1.2248524975088798e-05,1.1986436266539215e-05,1.1729955620290125e-05,1.1478963037418448e-05,1.12333410866869e-05,1.0992974849601673e-05,1.075572554968895e-05,1.0515669933721518e-05,1.0280972087296556e-05,1.0051512431064296e-05,9.827174054550677e-06,9.607842656590924e-06,9.393406487093014e-06,9.181988828890803e-06,8.975329553737502e-06,8.773321564574919e-06,8.575860174781357e-06,8.382843053919688e-06,8.194170174706867e-06,8.00974376117654e-06,7.829468238008839e-06,7.65325018100013e-06,7.498288594991164e-06,7.346464642349789e-06,7.1977147928592506e-06,7.051976802650769e-06,6.918167631857956e-06,6.800130298838276e-06,6.684106911234177e-06,6.570063107237962e-06,6.457965111320917e-06,6.3477797242302415e-06,6.238807143133598e-06,6.129083132877339e-06,6.021288875881668e-06,5.915390432923649e-06,5.811354461680924e-06]},{"id":"IRAF-HR3982","hip":49669,"hr":3982,"templateClass":"B7V","catalogueBV":-0.087,"spectralType":"B7V","kind":"observed-spectrophotometric-shape","source":"vendor/spectral/hr3982.dat","resolution":"29 sparse continuum bandpasses; log-flux interpolation on 5 nm grid is reconstruction, not 95 measured bins","samples":[3.0026943133144153e-05,2.9613669655369702e-05,2.9830343324204946e-05,3.539118347028792e-05,4.2590426558368675e-05,5.1254133277194844e-05,5.351113333212724e-05,5.341640711439401e-05,5.3321848582444405e-05,5.270443505011586e-05,5.078803432869502e-05,4.894131639054611e-05,4.7184509076628306e-05,4.550207336730564e-05,4.4077209648811276e-05,4.2718283725174736e-05,4.1401254275490345e-05,4.012482960718002e-05,3.862699841166936e-05,3.708791436518579e-05,3.578693126018242e-05,3.4612148052858364e-05,3.3475929638200635e-05,3.237701004370961e-05,3.1304891398819874e-05,3.0247363212069362e-05,2.922555998125377e-05,2.8238274861494218e-05,2.7284341777018984e-05,2.6431701989300685e-05,2.5605707323298825e-05,2.4805525114948754e-05,2.403034872106319e-05,2.3279396706175968e-05,2.2610624877152276e-05,2.1981136992110674e-05,2.136917427497422e-05,2.077424881879934e-05,2.0195886300146e-05,1.9633625600908683e-05,1.9089396861544756e-05,1.856056907927228e-05,1.8046391252958654e-05,1.7546457539309003e-05,1.7060373337982348e-05,1.658768766464782e-05,1.612783672557582e-05,1.568073397000242e-05,1.524602598735743e-05,1.4823369164469222e-05,1.4461442408605057e-05,1.4114885431739026e-05,1.3776633417463939e-05,1.3446487343950053e-05,1.312425295876769e-05,1.2809740664592308e-05,1.2502765407648524e-05,1.2207675811135457e-05,1.193093018187255e-05,1.1660458322039714e-05,1.1396118006507822e-05,1.1137770234363632e-05,1.0885279155817538e-05,1.0638512000768148e-05,1.0396849924348232e-05,1.0158765716022708e-05,9.926133552370936e-06,9.698828583486561e-06,9.476728818482121e-06,9.259715060018583e-06,9.047670840334163e-06,8.833180454004017e-06,8.623774926157303e-06,8.419333711597434e-06,8.219739122856154e-06,8.024876262446262e-06,7.834632956720504e-06,7.648899691298137e-06,7.467569548022655e-06,7.290538143413823e-06,7.14435101625834e-06,7.001095178361015e-06,6.8607118526127915e-06,6.723143440481091e-06,6.590880944937177e-06,6.464968219684591e-06,6.341460941368891e-06,6.2203131561363234e-06,6.101479788039238e-06,5.9849166222645915e-06,5.8710426699674114e-06,5.761150069095259e-06,5.653314408430364e-06,5.547497186718046e-06,5.443660623359729e-06]}],"rejectedStandards":[{"hr":4534,"hip":57632,"source":"vendor/spectral/hr4534.dat","reason":"Unexplained red excursions at 7550 and 7780 A. Full source retained; no silent repair."}]};

// real-sky/core/src/spectral.mjs
/** CP5 relative spectral radiometry. The V passband, CIE observer and display encoding
 * are distinct. Spectra describe received extra-atmospheric light: NEVER divide by distance.
 * 5 nm integration and sparse IRAF references are not high-resolution spectral calibration.
 */



const SPECTRAL_GRID=SPECTRAL_TABLES.wavelengthNm;
const sfWeights=SPECTRAL_TABLES.weightsNm,sfXYZ=SPECTRAL_TABLES.cieXYZ,sfCache=new Map(),sfFitCache=new Map();
function sfValidate(samples){if(!Array.isArray(samples)||samples.length!==95||!samples.every(x=>Number.isFinite(x)&&x>=0)||!samples.some(x=>x>0))throw new TypeError('Spectrum must have 95 non-negative finite samples with positive energy');return samples;}
function passbandIntegral(samples,band='V'){
 sfValidate(samples);const b=SPECTRAL_TABLES.passbands[band];if(!b)throw new RangeError('Unknown passband');
 return samples.reduce((s,v,i)=>s+v*SPECTRAL_GRID[i]*b[i]*sfWeights[i],0);
}
function cieTableAt(w){finite(w,'wavelength nm',360,830);const p=(w-360)/5,i=Math.min(93,Math.floor(p)),t=p-i;return sfXYZ[i].map((v,k)=>v*(1-t)+sfXYZ[i+1][k]*t);}
function sfNormalise(samples){const v=passbandIntegral(samples);if(!(v>0))throw new RangeError('Spectrum has no V-passband support');return samples.map(s=>s/v);}
const sfVega=SPECTRAL_TABLES.standards[0].samples,sfVegaBV=passbandIntegral(sfVega,'B')/passbandIntegral(sfVega,'V');
const sfObserverScale=1/sfVega.reduce((s,v,i)=>s+v*sfXYZ[i][1]*sfWeights[i],0);
function syntheticBV(samples){const b=passbandIntegral(samples,'B'),v=passbandIntegral(samples,'V');if(!(b>0&&v>0))throw new RangeError('B and V need positive support');return -2.5*Math.log10(b/v/sfVegaBV);}
function blackbodyShape(temperatureK){finite(temperatureK,'temperature proxy K',1500,200000);return sfNormalise(SPECTRAL_GRID.map(w=>1/(w**5*Math.expm1(1.438776877e7/(w*temperatureK)))));}
function sfFitColour(bv){if(sfFitCache.has(bv))return sfFitCache.get(bv);let lo=1500,hi=200000;if(bv>syntheticBV(blackbodyShape(lo))||bv<syntheticBV(blackbodyShape(hi)))return null;
 for(let i=0;i<48;i++){const mid=Math.sqrt(lo*hi);if(syntheticBV(blackbodyShape(mid))>bv)lo=mid;else hi=mid;}
 const T=Math.sqrt(lo*hi),fit={samples:blackbodyShape(T),temperatureProxyK:T};sfFitCache.set(bv,fit);return fit;
}
/** Hierarchy: caller spectrum with provenance -> same-identity standard -> strictly matched,
 * colour-compatible standard template -> B-V constrained continuum -> explicitly unknown.
 * Template reuse is opt-in via actual spectralType and never labelled a target measurement.
 */
function sfTiltTemplate(samples,bv){let lo=-4,hi=4,p=0,shape;for(let i=0;i<40;i++){p=(lo+hi)/2;shape=samples.map((x,j)=>x*(SPECTRAL_GRID[j]/550)**p);if(syntheticBV(shape)<bv)lo=p;else hi=p;}return {samples:sfNormalise(shape),colourTiltExponent:p};}
function selectSpectrum(star){
 if(star.sed){const d=star.sed;if(typeof d.source!=='string'||!d.source.trim())throw new TypeError('Provided spectrum requires source provenance');return {samples:sfNormalise(sfValidate(d.samples)),kind:d.kind??'provided-spectrum',source:d.source,measuredForThisSource:d.measuredForThisSource===true,temperatureProxyK:null,colourFallback:false};}
 const key=[star.hip??'',star.spectralType??'',star.bv??'unknown'].join('|');if(sfCache.has(key))return sfCache.get(key);
 let value;const own=SPECTRAL_TABLES.standards.find(s=>s.hip===star.hip);
 if(own)value={samples:own.samples,kind:own.kind,source:own.source,measuredForThisSource:true,resolution:own.resolution,temperatureProxyK:null,colourFallback:false};
 const bv=star.bv;
 if(!value&&bv!=null){finite(bv,'B-V',-.5,5);const template=SPECTRAL_TABLES.standards.find(s=>s.templateClass===star.spectralType&&Math.abs(bv-s.catalogueBV)<=.08);
  if(template)value={...sfTiltTemplate(template.samples,bv),kind:'observed-standard-template',source:template.source,measuredForThisSource:false,temperatureProxyK:null,colourFallback:false,templateColourResidualMag:syntheticBV(template.samples)-bv};
  else if(bv>=-.4&&bv<=2){const fitted=sfFitColour(bv);if(fitted)value={...fitted,kind:'B-V-constrained-continuum',source:'catalogue B-V; Planck family solved in declared Bessell B/V convention',measuredForThisSource:false,colourFallback:false};}
 }
 if(!value)value={samples:blackbodyShape(6500),kind:'unknown-neutral-display',source:'no admissible measured colour/spectrum; grey display proxy only',measuredForThisSource:false,temperatureProxyK:null,colourFallback:true};
 Object.freeze(value.samples);Object.freeze(value);if(sfCache.size<12000)sfCache.set(key,value);return value;
}
function spectrumToXYZ(samples){return [0,1,2].map(k=>samples.reduce((s,v,i)=>s+v*sfXYZ[i][k]*sfWeights[i]*sfObserverScale,0));}
function gamutMapXYZ(xyz){let rgb=xyzToLinearRgb(xyz).map(x=>Math.max(0,x));const y=luminance(rgb);return y>0?rgb.map(x=>x*xyz[1]/y):[0,0,0];}
/** transportAt receives wavelength nm and returns TOTAL direct terrestrial transmission.
 * If supplied, it owns aerosol/gas/cloud attenuation; the atmosphere object is not reapplied.
 */
function spectralStarFlux(star,altDeg,atmosphere={},options={}){
 finite(altDeg,'altitude',-90,90);const spectrum=selectSpectrum(star),scale=magnitudeFlux(star.vmag);
 if(altDeg<0)return {rgb:[0,0,0],xyz:[0,0,0],vFlux:0,kind:spectrum.kind,colourFallback:spectrum.colourFallback};
 const X=airmass(altDeg),cloud=finite(atmosphere.cloudTransmission??1,'cloud transmission',0,1);
 const samples=spectrum.samples.map((v,i)=>{const w=SPECTRAL_GRID[i],t=options.transportAt?finite(options.transportAt(w),'total spectral transmission',0,1):Math.exp(-X*opticalDepth(w,atmosphere))*cloud;return v*t*scale;});
 const xyz=spectrumToXYZ(samples),vFlux=passbandIntegralSafeZero(samples),response=options.response??'CIE1931';let rgb;
 if(response==='CIE1931')rgb=spectrum.colourFallback?[xyz[1],xyz[1],xyz[1]]:gamutMapXYZ(xyz);
 else if(response==='V-monochrome')rgb=[vFlux,vFlux,vFlux];else throw new RangeError('Unknown response model');
 return {rgb,xyz,vFlux,kind:spectrum.kind,model:spectrum.kind,source:spectrum.source,colourFallback:spectrum.colourFallback,temperatureProxyK:spectrum.temperatureProxyK,response,transportOwner:options.transportAt?'caller-total-transmission':'spectral-module'};
}
function passbandIntegralSafeZero(samples){return samples.some(x=>x>0)?passbandIntegral(samples):0;}

// real-sky/core/src/optics.mjs
/** Normalised Gaussian-mixture optical PSFs; deliberate approximations, not stellar discs.
 * Diffraction is represented by a Gaussian core matched approximately to Airy FWHM.
 * It does NOT reproduce diffraction rings/spider spikes. Pixel integration is exact Gaussian
 * CDF quadrature in renderer.mjs. Scatter redistributes a fixed fraction of energy.
 */

function psfComponents({preset='reference',wavelengthNm=550,arcsecPerCssPixel=1200,
 apertureMm=preset==='eye'?6:50,seeingFwhmArcsec=2,pixelSigmaCss=.48,scatterFraction,
 coreSigmaCss=.55,scatterSigmaCss=2.2}={}){
 if(!['reference','camera','eye'].includes(preset))throw new RangeError('Unknown optical preset');
 finite(wavelengthNm,'wavelength nm',360,830);finite(apertureMm,'aperture mm',.1,10000);finite(arcsecPerCssPixel,'angular pixel scale',.01,100000);
 finite(seeingFwhmArcsec,'seeing FWHM arcsec',0,120);finite(pixelSigmaCss,'pixel reconstruction sigma',.1,8);
 finite(coreSigmaCss,'core sigma',.1,8);finite(scatterSigmaCss,'scatter sigma',.1,12);
 const scatter=finite(scatterFraction??(preset==='eye'?.06:preset==='camera'?.015:.035),'scatter fraction',0,.25);
 const diffractionSigma=.437*(wavelengthNm*1e-9/(apertureMm*.001))*206264.806;
 const sigma=preset==='reference'?coreSigmaCss:Math.min(50,Math.hypot(pixelSigmaCss,diffractionSigma/arcsecPerCssPixel,seeingFwhmArcsec/2.35482/arcsecPerCssPixel));
 const wing=Math.max(sigma,scatterSigmaCss*(preset==='eye'?1.4:1));
 return [{sigmaCss:sigma,weight:1-scatter},{sigmaCss:wing,weight:scatter}];
}

// real-sky/core/src/renderer.mjs
/** CPU reference rasterizer. Accumulates sources + supplied sky in LINEAR light, then
 * tone maps and sRGB-encodes once. Output is intentionally opaque: CSS screen blending
 * an encoded transparent canvas with the old sky is NOT the same physical pipeline.
 */




function createLinearBuffer(width,height,background=[0,0,0]){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>8000000)throw new RangeError('invalid/budget-exceeding raster dimensions');
 if(!Array.isArray(background)||background.length!==3||!background.every(x=>Number.isFinite(x)&&x>=0))throw new RangeError('linear RGB background required');
 const b=new Float64Array(width*height*3);if(background.some(x=>x!==0))for(let i=0;i<b.length;i++)b[i]=background[i%3];return b;
}
// Abramowitz/Stegun 7.1.26 approximation; pixel-boundary integration removes subpixel popping.
function erf(x){const sign=x<0?-1:1,a=Math.abs(x),t=1/(1+.3275911*a);return sign*(1-(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-.284496736)*t+.254829592)*t*Math.exp(-a*a));}
function splatGaussian(buffer,width,height,x,y,rgb,sigma){
 finite(x,'x');finite(y,'y');finite(sigma,'PSF sigma',.05,100);
 if(buffer.length!==width*height*3||!Array.isArray(rgb)||rgb.length!==3||!rgb.every(v=>Number.isFinite(v)&&v>=0))throw new RangeError('invalid splat buffer/flux');
 const support=Math.ceil(6*sigma)+1,ix=Math.floor(x),iy=Math.floor(y),inv=1/(sigma*Math.SQRT2);
 const xs=Math.max(0,ix-support),xe=Math.min(width-1,ix+support),ys=Math.max(0,iy-support),ye=Math.min(height-1,iy+support);
 for(let j=ys;j<=ye;j++){const wy=.5*(erf((j+1-y)*inv)-erf((j-y)*inv));for(let i=xs;i<=xe;i++){
 const wx=.5*(erf((i+1-x)*inv)-erf((i-x)*inv)),w=Math.max(0,wx*wy),k=(j*width+i)*3;
 for(let c=0;c<3;c++)buffer[k+c]+=rgb[c]*w;
 }}
}
/** Unit: integrated source contribution per CSS pixel area. DPR therefore scales integral
 * by dpr^2 and PSF width by dpr; the displayed radiance/area stays invariant.
 */
function renderStars(stars,{width=325,height=530,dpr=1,background=[0,0,0],backgroundLinear=null,
 atmosphere={},sigmaCss=.55,haloFraction=.035,haloSigmaCss=2.2,utcMs=0,reducedMotion=true,scintillationAmplitude=0,
 transmissionAt=()=>1,pixelTransmissionAt=null,sourceVisibility=()=>true,
 fluxAt=null,opticalPreset='reference',optics={},response='CIE1931'}={}){
 finite(dpr,'DPR',.5,4);finite(sigmaCss,'PSF sigma CSS',.1,8);finite(haloFraction,'halo fraction',0,.25);finite(haloSigmaCss,'halo sigma',.1,12);
 const w=Math.round(width*dpr),h=Math.round(height*dpr),linear=createLinearBuffer(w,h,background);
 if(backgroundLinear){if(backgroundLinear.length!==linear.length||!backgroundLinear.every(x=>Number.isFinite(x)&&x>=0))throw new RangeError('invalid linear sky buffer');linear.set(backgroundLinear);}
 let drawn=0,colourFallbacks=0;const spectralKinds={};
 for(const s of stars){if(s.emission?.enabled===false||s.altDeg<0||s.visible===false||!sourceVisibility(s))continue;
 const mask=finite(transmissionAt(s.x,s.y,s),'source transmission',0,1);if(mask===0)continue;
 const f=fluxAt?fluxAt(s):spectralStarFlux(s,s.altDeg,atmosphere,{response}),tw=scintillation(s.hip??(1000000+(s.hygId??0)),utcMs/1000,s.altDeg,reducedMotion?0:scintillationAmplitude);
 const rgb=f.rgb.map(x=>x*mask*tw*dpr*dpr);if(rgb.every(x=>x===0))continue;
 const wavelengths=[610,550,460];
 for(let channel=0;channel<3;channel++){const psf=psfComponents({preset:opticalPreset,wavelengthNm:wavelengths[channel],coreSigmaCss:sigmaCss,scatterSigmaCss:haloSigmaCss,...(opticalPreset==='reference'?{scatterFraction:haloFraction}:{}),...optics});
  for(const part of psf)if(part.weight>0){const energy=[0,0,0];energy[channel]=rgb[channel]*part.weight;splatGaussian(linear,w,h,s.x*dpr,s.y*dpr,energy,part.sigmaCss*dpr);}
 }
 drawn++;if(f.colourFallback)colourFallbacks++;const kind=f.kind??'caller-flux';spectralKinds[kind]=(spectralKinds[kind]??0)+1;
 }
 if(pixelTransmissionAt){for(let y=0;y<h;y++)for(let x=0;x<w;x++){
  const m=finite(pixelTransmissionAt((x+.5)/dpr,(y+.5)/dpr),'pixel transmission',0,1),i=(y*w+x)*3;
  for(let k=0;k<3;k++){const base=backgroundLinear?backgroundLinear[i+k]:background[k];linear[i+k]=base+Math.max(0,linear[i+k]-base)*m;}
 }}
 return {linear,width:w,height:h,drawn,colourFallbacks,spectralKinds,representation:'linear V-anchored spectral response relative to Vega; display exposure is not absolute W/m²/sr'};
}
function encodeFrame(linear,exposure=12){finite(exposure,'exposure',0,100000);if(linear.length%3)throw new RangeError('RGB buffer required');const bytes=new Uint8ClampedArray(linear.length/3*4);
 for(let i=0,j=0;i<linear.length;i+=3,j+=4){for(let c=0;c<3;c++)bytes[j+c]=Math.round(255*linearToSrgb(-Math.expm1(-exposure*Math.max(0,finite(linear[i+c],'linear channel')))));bytes[j+3]=255;}
 return bytes;
}

// real-sky/core/src/atmosphere.mjs
/** CP6 explicit local atmospheric assumptions. Optical depths are vertical at the site.
 * Pressure is station pressure, NOT sea-level-corrected pressure. A supplied pressure wins
 * over elevation: do not reduce it a second time. Cloud transmission is a separate owner.
 */


const atmValidated=new WeakSet();
function normaliseAtmosphere(input={}){
 if(input&&atmValidated.has(input))return input;
 if(input===null||typeof input!=='object')throw new TypeError('Atmosphere must be an object');
 const elevationM=finite(input.elevationM??0,'elevation metres',-500,10000);
 if(input.cloudTransmission!=null&&input.cloudOpticalDepth!=null)throw new RangeError('Supply cloud transmission OR vertical cloud optical depth, not both');
 const pressureHpa=finite(input.pressureHpa??1013.25*(1-2.25577e-5*elevationM)**5.25588,'station pressure hPa',0,1100);
 const result=Object.freeze({__cp6Atmosphere:true,elevationM,pressureHpa,pressureSource:input.pressureHpa==null?'standard-atmosphere-estimate':'caller-supplied-station-pressure',
 aerosolTau550:finite(input.aerosolTau550??.06,'aerosol optical depth 550nm',0,3),angstromExponent:finite(input.angstromExponent??1.3,'Angstrom exponent',0,4),
 greyTau:finite(input.greyTau??0,'grey absorbing optical depth',0,3),aerosolAlbedo:finite(input.aerosolAlbedo??.9,'aerosol single-scattering albedo',0,1),
 aerosolG:finite(input.aerosolG??.76,'aerosol asymmetry',0,.95),rayleighScaleHeightM:finite(input.rayleighScaleHeightM??8000,'molecular scale height',4000,12000),aerosolScaleHeightM:finite(input.aerosolScaleHeightM??1200,'aerosol scale height',100,6000),
 cloudTransmission:input.cloudOpticalDepth!=null?null:finite(input.cloudTransmission??1,'cloud transmission',0,1),cloudOpticalDepth:input.cloudOpticalDepth==null?null:finite(input.cloudOpticalDepth,'cloud vertical optical depth',0,100),
 cloudGlowCdM2:finite(input.cloudGlowCdM2??0,'fully opaque cloud glow cd/m2',0,100000),lightPollutionCdM2:finite(input.lightPollutionCdM2??0,'local pollution radiance cd/m2',0,100000),
 nightZenithVMag:finite(input.nightZenithVMag??21.8,'night zenith magnitude/arcsec2',10,30),twilightScale:finite(input.twilightScale??1,'empirical twilight site scale',0,10)});
 atmValidated.add(result);return result;
}
function rayleighOpticalDepth(wavelengthNm,atmosphere={}){const a=normaliseAtmosphere(atmosphere),l=finite(wavelengthNm,'wavelength nm',360,830)/1000;return .008569*l**-4*(1+.0113*l**-2+.00013*l**-4)*a.pressureHpa/1013.25;}
function aerosolOpticalDepth(wavelengthNm,atmosphere={}){const a=normaliseAtmosphere(atmosphere);finite(wavelengthNm,'wavelength nm',360,830);return a.aerosolTau550*(550/wavelengthNm)**a.angstromExponent;}
function cloudTransmissionFor(direction,atmosphere={},cloudAt=null,utcMs=0){const a=normaliseAtmosphere(atmosphere),alt=finite(direction.altDeg,'cloud sightline altitude',-90,90);finite(direction.azDeg,'cloud sightline azimuth');
 if(cloudAt!=null){if(typeof cloudAt!=='function')throw new TypeError('cloudAt must return total sightline cloud transmission');return finite(cloudAt(direction,utcMs),'total cloud-map transmission',0,1);}
 return a.cloudOpticalDepth==null?a.cloudTransmission:Math.exp(-a.cloudOpticalDepth*airmass(Math.max(0,alt)));
}
function directTransmission(wavelengthNm,altDeg,atmosphere={},totalCloudTransmission=null){const a=normaliseAtmosphere(atmosphere);finite(altDeg,'source altitude',-90,90);if(altDeg<0)return 0;
 const cloud=totalCloudTransmission==null?cloudTransmissionFor({altDeg,azDeg:0},a):finite(totalCloudTransmission,'total cloud transmission',0,1);
 return cloud*Math.exp(-airmass(altDeg)*(rayleighOpticalDepth(wavelengthNm,a)+aerosolOpticalDepth(wavelengthNm,a)+a.greyTau));
}
function phaseRayleigh(cosine){finite(cosine,'phase cosine',-1,1);return 3/(16*Math.PI)*(1+cosine*cosine);}
/** cosine=1 means looking TOWARDS the illuminator, hence forward scattering peaks there.
 * This sign convention differs from pbrt's two-away-vector convention. */
function phaseHG(cosine,g=.76){finite(cosine,'phase cosine',-1,1);finite(g,'asymmetry',-.99,.99);return (1-g*g)/(4*Math.PI*(1+g*g-2*g*cosine)**1.5);}
function horizontalDirection(h){const a=finite(h.altDeg,'altitude',-90,90)*DEG,z=finite(h.azDeg,'azimuth')*DEG;return [Math.cos(a)*Math.sin(z),Math.cos(a)*Math.cos(z),Math.sin(a)];}

// real-sky/core/src/sky-state.mjs
/** Low-order Sun/Moon for sky illumination, NOT a lunar material or prayer calculator.
 * Schlyter orbital elements and ALL his listed lunar perturbations, independently written.
 * Uses CP4 TT for orbital time, UT1 sidereal rotation, ellipsoidal topocentric subtraction.
 * No claim of CP4 stellar sub-arcsecond precision for this separate lunar approximation.
 */


const skSin=x=>Math.sin(x*DEG),skCos=x=>Math.cos(x*DEG);
function skOrbit(M,e,a,N=0,i=0,w=0){let E=wrapDeg(M)*DEG;const m=E;for(let k=0;k<8;k++)E-=(E-e*Math.sin(E)-m)/(1-e*Math.cos(E));const x=a*(Math.cos(E)-e),y=a*Math.sqrt(1-e*e)*Math.sin(E),v=Math.atan2(y,x)/DEG,r=Math.hypot(x,y);return {r,longitude:wrapDeg(v+w),vector:[r*(skCos(N)*skCos(v+w)-skSin(N)*skSin(v+w)*skCos(i)),r*(skSin(N)*skCos(v+w)+skCos(N)*skSin(v+w)*skCos(i)),r*skSin(v+w)*skSin(i)]};}
function skEquatorial(v,e){return [v[0],v[1]*skCos(e)-v[2]*skSin(e),v[1]*skSin(e)+v[2]*skCos(e)];}
function physicalSkyState(observer){
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

// real-sky/core/src/visibility.mjs
/** Visibility is a display/observer RESPONSE, not an extra extinction coefficient. */


/** Modelled central CSS-pixel display contrast. No catalogue or physical flux is changed.
 * This is an 8-bit display diagnostic, not a physiological limiting-magnitude prediction. */
function displayVisibility(sourceY,backgroundY,exposure,{thresholdSrgb=2/255,sigmaCss=.55}={}){
 finite(sourceY,'source flux',0);finite(backgroundY,'background flux per CSS pixel',0);finite(exposure,'display exposure',0,100000);finite(thresholdSrgb,'contrast threshold',0,1);finite(sigmaCss,'PSF sigma',.1,50);
 const peak=sourceY/(2*Math.PI*sigmaCss*sigmaCss),encode=x=>linearToSrgb(-Math.expm1(-x*exposure)),deltaSrgb=encode(backgroundY+peak)-encode(backgroundY);
 return {deltaSrgb,thresholdSrgb,detectable:deltaSrgb>=thresholdSrgb,criterion:'modelled central CSS-pixel contrast; not human acuity'};
}
/** Bounded zero-mean deterministic surrogate. Turbulence parameters are NOT measured.
 * Box-exposure averages the two temporal modes analytically (sinc); no frame random draws.
 * Optional modulation never moves a source or changes its catalogue record. */
function scintillationFactor(id,tSeconds,altDeg,{strength=.04,exposureSec=.1,apertureMm=6,reducedMotion=false}={}){
 finite(strength,'scintillation strength',0,.3);finite(exposureSec,'exposure seconds',0,3600);finite(apertureMm,'aperture mm',.1,10000);finite(tSeconds,'time seconds');finite(altDeg,'altitude',-90,90);
 if(reducedMotion||strength===0||altDeg<0)return 1;
 let hash=2166136261;for(const c of String(id))hash=Math.imul(hash^c.charCodeAt(0),16777619)>>>0;
 const phase=hash/4294967296*2*Math.PI,sinc=x=>Math.abs(x)<1e-12?1:Math.sin(x)/x,amp=strength*(.25+.75*(1-Math.sin(altDeg*DEG)))*Math.min(1,(6/apertureMm)**(2/3));
 return 1+amp*(.6*Math.sin(2*Math.PI*.73*tSeconds+phase)*sinc(Math.PI*.73*exposureSec)+.4*Math.sin(2*Math.PI*1.17*tSeconds+2.13*phase)*sinc(Math.PI*1.17*exposureSec));
}

// real-sky/core/src/sky-background.mjs
/** CP6 radiance model: spectral spherical single scattering + a measured-site twilight
 * residual, empirical moonlight, and a parameterised natural/local background.
 * Units are photopic-equivalent cd/m² under the documented V-to-luminance convention.
 * Not a full multiple-scattering solver, measured local weather, or diffuse star map.
 */




const V_ZERO_ILLUMINANCE_LUX=2.54e-6;
const ARCSEC_PER_RADIAN=206264.80624709636;
const bgMagnitudeZero=V_ZERO_ILLUMINANCE_LUX*ARCSEC_PER_RADIAN**2,bgEarthRadius=6371000,bgTopRadius=6471000;
const bgSmooth=x=>{x=clamp(x,0,1);return x*x*(3-2*x);};
const bgSolarBase=blackbodyShape(5778),bgSolarY=spectrumToXYZ(bgSolarBase)[1],bgSolarShape=bgSolarBase.map(x=>x/bgSolarY),bgCoeff=new WeakMap();
function surfaceMagnitudeToLuminance(m){return bgMagnitudeZero*10**(-.4*finite(m,'V magnitude per arcsec2',-30,60));}
function luminanceToSurfaceMagnitude(L){finite(L,'luminance',Number.MIN_VALUE);return -2.5*Math.log10(L/bgMagnitudeZero);}
/** An explicit assumed NON-STELLAR residual replaces the historical aggregate floor.
 * It is never inferred by subtracting a map from a total or called measured airglow.
 * Its supplied zenith value is already at the observer (pre-cloud), like the CP6 floor.
 */
function validateResidualNight(input){
 if(!input||input.kind!=='assumed-nonstellar-residual'||input.includesRegisteredStarlight!==false||typeof input.source!=='string'||!input.source.trim())throw new TypeError('Explicit labelled non-stellar residual night assumption required');
 return Object.freeze({kind:input.kind,zenithCdM2:finite(input.zenithCdM2,'residual night zenith cd/m2',0,1),source:input.source,includesRegisteredStarlight:false,measured:false});
}
/** Patat et al. (2006) Table 1: fitted TOTAL zenith background, solar depression 5..15°.
 * Subtract reference night V=21.6/B=22.6 before adding our own natural background.
 * A tapered continuation to 20° is an explicit engineering extension, not published data.
 */
function patatTwilight(sunAltDeg){finite(sunAltDeg,'solar altitude',-90,90);const depression=-sunAltDeg,x=clamp(depression,3,15)-5;
 const totalVMag=11.84+1.518*x-.057*x*x,totalBMag=11.84+1.411*x-.041*x*x;
 let v=Math.max(0,10**(-.4*totalVMag)-10**(-.4*21.6)),b=Math.max(0,10**(-.4*totalBMag)-10**(-.4*22.6));
 const tail=depression<=15?1:Math.exp(-.4*Math.LN10*.378*(depression-15))*(1-bgSmooth((depression-15)/5));v*=tail;b*=tail;
 return {totalVMag,totalBMag,excessLuminance:bgMagnitudeZero*v,bv:v>0&&b>0?-2.5*Math.log10(b/v):null,inMeasuredDomain:depression>=5&&depression<=15,reference:'Patat2006Table1; night floor removed',extension:depression<5||depression>15};
}
/** Original KS1991 equations, nL converted to cd/m² (1 nL=1e-5/pi cd/m²).
 * Near aureole uses their rho^-2 term; blend only 8..12° to avoid a branch jump.
 * No opposition boost, eclipse, instrument glare or calendar-Moon position is inferred.
 */
function moonSkyLuminance({moonAltDeg,targetAltDeg,separationDeg,phaseAngleDeg,extinctionMag,distanceKm=384400,angularRadiusDeg=.25}){
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
function singleScatteredSun(direction,state,atmosphere={},options={}){
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
function createSkyModel(state,atmosphere={},options={}){
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

// real-sky/core/src/catalogue.mjs

function validateCatalogue(c){
 if(!['salah-real-sky/catalogue/1','salah-real-sky/catalogue/2'].includes(c?.schema)||!Array.isArray(c.stars)||!c.stars.length)throw new TypeError('unsupported or empty catalogue');
 const v2=c.schema.endsWith('/2'),seen=new Set(),hips=new Set();
 for(const s of c.stars){
  if(v2){
   if(typeof s.id!=='string'||!/^hyg:[1-9][0-9]*$/.test(s.id)||s.id!==`hyg:${s.hygId}`||!Number.isSafeInteger(s.hygId)||seen.has(s.id))throw new Error('invalid or duplicate stable identity');
   seen.add(s.id);
  }
  if(!v2||s.hip!==null){if(!Number.isSafeInteger(s.hip)||s.hip<=0||hips.has(s.hip))throw new Error('invalid or duplicate HIP identity');hips.add(s.hip);}
  finite(s.raDeg,'RA',0,360);if(s.raDeg>=360)throw new RangeError('RA must be below 360 degrees');
  finite(s.decDeg,'declination',-90,90);finite(s.vmag,'V magnitude',-2,25);finite(s.epochJyear,'epoch',1800,2200);
  if(s.bv!==null)finite(s.bv,'B-V',-.5,5);
  for(const k of ['pmRaCosDecMasYr','pmDecMasYr','distancePc','radialVelocityKmS'])if(s[k]!=null)finite(s[k],k);
  if(s.distancePc!=null&&s.distancePc<=0)throw new RangeError('distance must be positive');
 }
 return c;
}
/** Fetch with explicit generation ownership in SkyController; never substitute random stars. */
async function loadCatalogue(url,{signal,fetchImpl=globalThis.fetch}={}){
 const r=await fetchImpl(url,{signal,credentials:'omit',cache:'no-cache'});if(!r.ok)throw new Error(`catalogue HTTP ${r.status}`);
 return validateCatalogue(await r.json());
}

// real-sky/core/src/scene.mjs
/** Stateful integration boundary. Scene readiness and ticking astronomical time are DIFFERENT keys.
 * The host owns scheduling, clock, geolocation, Moon and weather. This module owns none of them.
 */



function projectCatalogue(catalogue,observer,project=projectWidgetDome){
 const f=observationFrame(observer);
 return catalogue.stars.map(s=>{const h=observeStar(s,f),p=project(h);return {...s,...h,x:p?.x??0,y:p?.y??0,visible:!!p&&p.visible!==false&&h.aboveHorizon};});
}
class SkyController{
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
function horizontalVector(h){const a=h.azDeg*DEG,e=h.altDeg*DEG;return [Math.cos(e)*Math.sin(a),Math.cos(e)*Math.cos(a),Math.sin(e)];}
function fromVector(v){v=unit(v);return {altDeg:Math.asin(Math.max(-1,Math.min(1,v[2])))/DEG,azDeg:wrapDeg(Math.atan2(v[0],v[1])/DEG)};}
/** A geometrical occulting disc is opaque even at new Moon. Caller must supply PHYSICAL
 * apparent sky coordinates/radius, never the widget's calendar Moon placement or illumination.
 */
function discOccults(star,disc){finite(disc.radiusDeg,'angular radius',0,90);return angularSeparation(horizontalVector(star),horizontalVector(disc))<=disc.radiusDeg;}
/** Great-circle chart strokes, segmented then clipped. They are annotations, never light sources.
 * Entirely hidden edges yield no strokes; partial paths are honestly clipped rather than connected
 * through the card from one visible end to an unrelated point. No boundary assignment is implied.
 */
function annotationSegments(annotations,sources,project=projectWidgetDome,{maxStepDeg=1,maxPixelStep=80}={}){
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

// real-sky/core/src/sha256.mjs
/** Portable byte digest for offline asset identity (SHA-256, FIPS 180-4).
 * This is NOT a signature or a claim of upstream authenticity. No I/O or dependency.
 * Tests compare against the independent Node/OpenSSL implementation.
 */
const shK=new Uint32Array([
 0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
 0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
 0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
 0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
 0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
 0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
 0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
 0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]);
const shRotate=(x,n)=>(x>>>n)|(x<<(32-n));
function sha256Hex(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length>67108864)throw new TypeError('SHA256 requires at most 64 MiB of bytes');
 const padded=new Uint8Array(Math.ceil((bytes.length+9)/64)*64);padded.set(bytes);padded[bytes.length]=128;
 const dv=new DataView(padded.buffer);dv.setUint32(padded.length-8,Math.floor(bytes.length/536870912));dv.setUint32(padded.length-4,(bytes.length*8)>>>0);
 const h=new Uint32Array([0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]),w=new Uint32Array(64);
 for(let offset=0;offset<padded.length;offset+=64){
  for(let i=0;i<16;i++)w[i]=dv.getUint32(offset+i*4);
  for(let i=16;i<64;i++){const x=w[i-15],y=w[i-2];w[i]=(w[i-16]+(shRotate(x,7)^shRotate(x,18)^(x>>>3))+w[i-7]+(shRotate(y,17)^shRotate(y,19)^(y>>>10)))>>>0;}
  let [a,b,c,d,e,f,g,z]=h;
  for(let i=0;i<64;i++){const t1=(z+(shRotate(e,6)^shRotate(e,11)^shRotate(e,25))+((e&f)^(~e&g))+shK[i]+w[i])>>>0,t2=((shRotate(a,2)^shRotate(a,13)^shRotate(a,22))+((a&b)^(a&c)^(b&c)))>>>0;
   z=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;
  }
  const v=[a,b,c,d,e,f,g,z];for(let i=0;i<8;i++)h[i]=(h[i]+v[i])>>>0;
 }
 return Array.from(h,x=>x.toString(16).padStart(8,'0')).join('');
}

// real-sky/core/src/diffuse-map.mjs


/** CP7 PARTIAL: validated diagnostic map sampling + celestial registration.
 * Does not authenticate/permit a scientific survey, apply source proper motion,
 * transport atmosphere/cloud light, occult the Moon or encode a physical frame.
 * Current accepted roles are diagnostic and test fixture ONLY.
 */
const DF_ROLE='finite-catalogue-diagnostic-not-survey';
const DF_SCHEMA='salah-real-sky/diffuse-map/1';
function dfArray(a,n,label){if(!Array.isArray(a)||a.length!==n)throw new TypeError(label+' length mismatch');}
function dfArea(w,h,j){return 2*Math.PI/w*(Math.sin((-90+(j+1)*180/h)*DEG)-Math.sin((-90+j*180/h)*DEG));}
function createDiagnosticDiffuseSampler(asset){
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
function observeDiffuseDirection(direction,observerOrFrame){
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
function diffuseGeometricAltitude(apparentAltDeg,observerOrFrame){const f=dfFrame(observerOrFrame);return dfUndoRefraction(finite(apparentAltDeg,'apparent altitude',-90,90),f.observer);}
function horizontalToDiffuseJ2000(horizontal,observerOrFrame){
 const f=dfFrame(observerOrFrame),o=f.observer;finite(horizontal?.altDeg,'horizontal altitude',-90,90);finite(horizontal?.azDeg,'horizontal azimuth');
 const alt=dfUndoRefraction(horizontal.altDeg,o)*DEG,az=horizontal.azDeg*DEG,p=f.latDeg*DEG,t=f.lstDeg*DEG;
 const e=Math.cos(alt)*Math.sin(az),n=Math.cos(alt)*Math.cos(az),u=Math.sin(alt),meridian=u*Math.cos(p)-n*Math.sin(p);
 const date=[meridian*Math.cos(t)-e*Math.sin(t),meridian*Math.sin(t)+e*Math.cos(t),n*Math.cos(p)+u*Math.sin(p)];
 let v=f.rotation.map(c=>dot(c,date));
 if(f.aberration)v=aberrate(v,f.velocityOverC.map(x=>-x));
 return unit(v);
}
function diffuseRayToMap(xCss,yCss,view,observerOrFrame){
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
function renderDiagnosticDiffuse(sampler,observer,view,{dpr=1,samplesPerAxis=1}={}){
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
function prepareHorizontalToDiffuseJ2000(observerOrFrame){
 const f=dfFrame(observerOrFrame),o={...f.observer},p=f.latDeg*DEG,t=f.lstDeg*DEG;
 const cp=Math.cos(p),sp=Math.sin(p),ct=Math.cos(t),st=Math.sin(t),rotation=f.rotation.map(c=>[...c]),aberration=f.aberration,velocity=f.velocityOverC.map(x=>-x);
 return horizontal=>{
  finite(horizontal?.altDeg,'horizontal altitude',-90,90);finite(horizontal?.azDeg,'horizontal azimuth');
  const alt=dfUndoRefraction(horizontal.altDeg,o)*DEG,az=horizontal.azDeg*DEG,e=Math.cos(alt)*Math.sin(az),n=Math.cos(alt)*Math.cos(az),u=Math.sin(alt),meridian=u*cp-n*sp;
  const date=[meridian*ct-e*st,meridian*st+e*ct,n*cp+u*sp];let v=rotation.map(c=>dot(c,date));
  if(aberration)v=aberrate(v,velocity);return unit(v);
 };
}

// real-sky/core/src/registered-starlight.mjs



/** Admitted, corrected V-component. ICRS axes share the existing mean-J2000
 * geometry within a declared 0.1-arcsecond frame-bias allowance. No epoch-2016
 * precession, star-dependent proper motion, atmosphere or display encoding here. */
const RS_SHA='69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446';
const RS_F0=3.62708e-11;
function rsN(n){if(!Number.isInteger(n)||n<1||n>256||(n&(n-1)))throw new RangeError('NESTED nside must be a power of two in 1..256');return n;}
function healpixIndex(nside,raDeg,decDeg){
 const n=rsN(nside);finite(raDeg,'ICRS longitude');finite(decDeg,'ICRS latitude',-90,90);
 const tt=wrapDeg(raDeg)/90,z=Math.sin(decDeg*DEG),za=Math.abs(z);let f,ix,iy;
 if(za<=2/3){const jp=Math.floor(n*(.5+tt-.75*z)),jm=Math.floor(n*(.5+tt+.75*z)),fp=Math.floor(jp/n),fm=Math.floor(jm/n);f=fp===fm?(fp%4)+4:fp<fm?fp%4:(fm%4)+8;ix=jm%n;iy=n-(jp%n)-1;}
 else{const nt=Math.min(3,Math.floor(tt)),tp=tt-nt,t=n*Math.sqrt(3*(1-za)),a=Math.min(n-1,Math.floor(tp*t)),b=Math.min(n-1,Math.floor((1-tp)*t));f=z>=0?nt:nt+8;ix=z>=0?n-b-1:a;iy=z>=0?n-a-1:b;}
 let p=f*n*n;for(let bit=0;(1<<bit)<n;bit++)p|=((ix>>bit)&1)<<(2*bit)|((iy>>bit)&1)<<(2*bit+1);return p;
}
function healpixCentre(nside,pixel){
 const n=rsN(nside);if(!Number.isInteger(pixel)||pixel<0||pixel>=12*n*n)throw new RangeError('Invalid NESTED address');
 const f=Math.floor(pixel/(n*n)),q=pixel%(n*n);let x=0,y=0;
 for(let b=0;(1<<b)<n;b++){x|=((q>>(2*b))&1)<<b;y|=((q>>(2*b+1))&1)<<b;}
 const j=[2,2,2,2,3,3,3,3,4,4,4,4][f]*n-x-y-1,r=j<n?j:j>3*n?4*n-j:n,z=j<n?1-r*r/(3*n*n):j>3*n?-1+r*r/(3*n*n):(2*n-j)*2/(3*n);
 return {raDeg:wrapDeg(([1,3,5,7,0,2,4,6,1,3,5,7][f]*r+x-y)*45/r),decDeg:Math.asin(Math.max(-1,Math.min(1,z)))/DEG};
}
function rsRing(n,j){
 const r=j<n?j:j>3*n?4*n-j:n,z=j<n?1-r*r/(3*n*n):j>3*n?-1+r*r/(3*n*n):(2*n-j)*2/(3*n),count=4*r,step=360/count;
 const origin=(j<n||j>3*n)?step/2:((j+n)&1)?0:step/2;
 const lat=Math.asin(z)/DEG,indices=new Uint32Array(count);
 for(let i=0;i<count;i++)indices[i]=healpixIndex(n,origin+i*step,lat);
 return {theta:Math.acos(z),origin,step,indices};
}
function createRegisteredStarlightSampler(asset,{catalogueSha256=null}={}){
 if(asset?.schema!=='salah-real-sky/registered-starlight/1'||asset.dataAdmitted!==true||asset.component!=='unresolved-integrated-starlight-V')throw new TypeError('Corrected admitted integrated-starlight asset required');
 if(asset.frame!=='ICRS'||asset.grid?.type!=='HEALPix'||asset.grid.order!=='NESTED')throw new TypeError('Unsupported frame/pixel order');
 if(asset.quantity!=='passband-averaged-spectral-radiance-W-m-2-sr-1-nm-1'||asset.band!=='V'||asset.zeroPointWm2nm!==RS_F0)throw new TypeError('V-band spectral-radiance contract mismatch');
 if(asset.sourceSha256!==RS_SHA||!/^[0-9a-f]{64}$/.test(asset.catalogueSha256??'')||(catalogueSha256!==null&&asset.catalogueSha256!==catalogueSha256))throw new TypeError('Source or emitter-catalogue binding mismatch');
 if(asset.fillPolicy!=='median16-nonexcluded-native-cells-before-coarsening'||asset.positionToleranceDeg!==.1||asset.rawAdditiveCompositionAllowed!==false)throw new TypeError('Unrecognised source-removal policy');
 if(typeof asset.id!=='string'||!asset.id.length||asset.id.length>256)throw new TypeError('Asset ID required');
 const n=rsN(asset.grid.nside),count=12*n*n;
 for(const field of ['values','estimatedFraction'])if(!Array.isArray(asset[field])||asset[field].length!==count)throw new TypeError(field+' shape mismatch');
 const a=new Float64Array(count),m=new Float64Array(count);let sum=0,c=0;
 for(let i=0;i<count;i++){a[i]=finite(asset.values[i],'radiance',0,1);m[i]=finite(asset.estimatedFraction[i],'estimated fraction',0,1);const v=a[i]-c,t=sum+v;c=(t-sum)-v;sum=t;}
 const integrated=sum*(4*Math.PI/count);finite(asset.integratedWm2nm,'integrated flux',0);
 if(Math.abs(integrated-asset.integratedWm2nm)>1e-8*Math.max(integrated,1e-300))throw new RangeError('Integrated radiance mismatch');
 const rings=Array.from({length:4*n-1},(_,i)=>rsRing(n,i+1));
 function cap(r){let v=0,e=0;for(const p of r.indices){v+=a[p]/r.indices.length;e+=m[p]/r.indices.length;}return [v,e];}
 const north=cap(rings[0]),south=cap(rings.at(-1));
 function row(r,ra){const x=(wrapDeg(ra)-r.origin)/r.step,i=Math.floor(x),f=x-i,k=r.indices.length,p=r.indices[((i%k)+k)%k],q=r.indices[(((i+1)%k)+k)%k];return [a[p]*(1-f)+a[q]*f,m[p]*(1-f)+m[q]*f];}
 function blend(a,b,t){return [a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t];}
 function sample(raDeg,decDeg,{filter='linear',allowEstimates=true}={}){
  finite(raDeg,'ICRS longitude');finite(decDeg,'ICRS latitude',-90,90);if(!['linear','nearest'].includes(filter)||typeof allowEstimates!=='boolean')throw new TypeError('Invalid sampling policy');let q;
  if(filter==='nearest'){const p=healpixIndex(n,raDeg,decDeg);q=[a[p],m[p]];}
  else{const t=(90-decDeg)*DEG,first=rings[0],last=rings.at(-1);
   if(t<=first.theta)q=blend(north,row(first,raDeg),t/first.theta);
   else if(t>=last.theta)q=blend(south,row(last,raDeg),(Math.PI-t)/(Math.PI-last.theta));
   else{let lo=0,hi=rings.length-1;while(hi-lo>1){const j=(lo+hi)>>1;if(rings[j].theta<=t)lo=j;else hi=j;}q=blend(row(rings[lo],raDeg),row(rings[hi],raDeg),(t-rings[lo].theta)/(rings[hi].theta-rings[lo].theta));}
  }
  const estimated=Math.max(0,Math.min(1,q[1])),defined=allowEstimates||estimated<=1e-12;
  return {value:defined?q[0]:null,defined,estimatedFraction:estimated,retainedSourceFraction:1-estimated,relativeV0PerSr:defined?q[0]/RS_F0:null,observationalCompleteness:null};
 }
 return Object.freeze({id:asset.id,nside:n,dataAdmitted:true,band:'V',quantity:asset.quantity,frame:asset.frame,sourceSha256:RS_SHA,catalogueSha256:asset.catalogueSha256,integratedWm2nm:integrated,zeroPointWm2nm:RS_F0,sample});
}
/** Source-coordinate diagnostic raster; output is mean radiance, NOT radiant pixel flux.
 * Pixel footprint antialiasing precedes the explicitly labelled viewer stretch.
 * A future physical compositor must use its pixel solid angle and transport once. */
function renderRegisteredStarlight(sampler,observer,view,{dpr=1,samplesPerAxis=1,allowEstimates=true,filter='linear'}={}){
 if(sampler?.dataAdmitted!==true||typeof sampler.sample!=='function')throw new TypeError('Admitted sampler required');
 finite(view?.width,'CSS width',16,2048);finite(view?.height,'CSS height',16,2048);finite(dpr,'DPR',.5,3);
 if(!Number.isInteger(samplesPerAxis)||samplesPerAxis<1||samplesPerAxis>4)throw new RangeError('Footprint sampling must be 1..4');
 if(typeof allowEstimates!=='boolean'||!['linear','nearest'].includes(filter))throw new TypeError('Invalid sampling policy');
 if(view.type==='camera')cameraGeometry(view);else if(view.type==='allsky')finite(view.padding??4,'all-sky padding',0,Math.min(view.width,view.height)/2-1e-9);else throw new RangeError('Unsupported view');
 const width=Math.round(view.width*dpr),height=Math.round(view.height*dpr),count=width*height;
 if(count>2097152)throw new RangeError('Raster allocation budget exceeded');
 const frame=observationFrame(observer),radiance=new Float64Array(count),estimatedFraction=new Float32Array(count),skyFraction=new Float32Array(count),missing=new Uint8Array(count),n=samplesPerAxis,den=n*n;let skyPixels=0,missingPixels=0;
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  let value=0,estimate=0,sky=0,absent=false;const at=y*width+x;
  for(let sy=0;sy<n;sy++)for(let sx=0;sx<n;sx++){
   const q=diffuseRayToMap((x+(sx+.5)/n)*view.width/width,(y+(sy+.5)/n)*view.height/height,view,frame);if(!q.aboveHorizon)continue;sky++;
   const s=sampler.sample(q.raDeg,q.decDeg,{filter,allowEstimates});estimate+=s.estimatedFraction;if(!s.defined)absent=true;else value+=s.value;
  }
  skyFraction[at]=sky/den;estimatedFraction[at]=sky?estimate/sky:0;if(sky)skyPixels++;
  if(absent){missing[at]=1;missingPixels++;}else radiance[at]=value/den;
 }
 return {width,height,radiance,estimatedFraction,skyFraction,missing,skyPixels,missingPixels,dataAdmitted:true,diagnosticExposureOnly:true,physicalComposition:false,sourceId:sampler.id,sourceSha256:RS_SHA,utcMs:observer.utcMs,frameWarnings:[...frame.warnings],quantity:sampler.quantity};
}

// real-sky/core/src/diffuse-binding.mjs



const dsBindings=new WeakSet();
function dsDeepFreeze(value){if(value&&typeof value==='object'&&!Object.isFrozen(value)){for(const v of Object.values(value))dsDeepFreeze(v);Object.freeze(value);}return value;}
/** Verify EXACT catalogue bytes named by the corrected source-removal asset, then
 * parse a private frozen catalogue. The physical bridge must use binding.catalogue.
 * Asset admission/photometric uncertainty remain CP7.3's. A hash is not a signature.
 */
function bindRegisteredStarlight(catalogueText,asset){
 if(typeof catalogueText!=='string')throw new TypeError('Unmodified catalogue UTF-8 text required');
 const catalogueSha256=sha256Hex(new TextEncoder().encode(catalogueText));
 if(catalogueSha256!==asset?.catalogueSha256)throw new TypeError('Diffuse emitter catalogue byte hash mismatch');
 const catalogue=dsDeepFreeze(validateCatalogue(JSON.parse(catalogueText)));
 const sampler=createRegisteredStarlightSampler(asset,{catalogueSha256});
 const binding=Object.freeze({catalogue,catalogueSha256,sampler,sourceSha256:sampler.sourceSha256,kind:'verified-catalogue-bound-starlight'});dsBindings.add(binding);return binding;
}
function isBoundRegisteredStarlight(value){return !!value&&dsBindings.has(value);}

// real-sky/core/src/diffuse-transport.mjs
/** CP7.4 direct extra-atmospheric V integrated starlight -> observer.
 * No spectrum is inferred from one band. Effective V transmission uses the SAME
 * CP5 Bessell photon-counting passband and retained Vega weighting as a declared
 * IN-BAND ASSUMPTION. Do not call the resulting neutral channel measured RGB.
 */







const DIFFUSE_TRANSPORT_ASSUMPTION='Vega-weighted effective Bessell V transmission; assumed in-band SED, neutral V-equivalent output';
/** 0.1-degree lookup; exact() is retained for independent comparisons and controls. */
function createVBandTransmission(atmosphere={}){
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
function createDiffuseTransport(diffuse,{observer,atmosphere={},state,cloudAt=null}={}){
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
function renderDiffuseLayer(model,mapping,{widthPx,heightPx,dpr=1,displayTransmissionAt=null}={}){
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

// real-sky/core/src/physical-sky-renderer.mjs
/** Joined REFERENCE compositor: atmospheric direct source transport, additive sky radiance,
 * explicit physical occultation, separate calendar/foreground mask, one display transform.
 * This is not a patch applied to the real widget. Host cloud maps must be pure functions
 * of the supplied direction/time and return total LOS transmission, never another alpha pass.
 */










function skyProjection(view={}){
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
function resolveSkyInputs(observer,atmosphere={}){
 if(!observer||typeof observer!=='object')throw new TypeError('Observer is required');
 if(!atmosphere||typeof atmosphere!=='object')throw new TypeError('Atmosphere must be an object');
 const site=observer.heightM??observer.elevationM??atmosphere.elevationM??0;
 finite(site,'site elevation metres',-500,10000);
 if(observer.heightM!=null&&observer.elevationM!=null&&observer.heightM!==observer.elevationM)throw new RangeError('Conflicting observer elevations');
 if(atmosphere.elevationM!=null&&atmosphere.elevationM!==site)throw new RangeError('Observer and atmospheric elevation disagree');
 return {observer:{...observer,heightM:site},atmosphere:normaliseAtmosphere(atmosphere.elevationM===site?atmosphere:{...atmosphere,elevationM:site})};
}
function renderPhysicalSky(sources,{observer,view={},atmosphere={},physicalState=null,dpr=1,nominalExposure=24,autoExposure=true,opticalPreset='reference',response='CIE1931',cloudAt=null,displayTransmissionAt=null,reducedMotion=true,scintillation={},backgroundStepCss=6,diffuse=null}={}){
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

// real-sky/core/integration/physical-sky-bridge.mjs
/** Local integration seam, not an applied actual-widget patch. Caller owns accepted clock,
 * location and scheduling. No timers, geolocation, cloud fetch or scene-ready writes here. */



class PhysicalSkyBridge{
 constructor(catalogue){this.controller=new SkyController(catalogue);this.last=null;}
 render(observer,{sceneIdentity=null,view={type:'camera',width:325,height:530},...appearance}={}){
  try{
   if(appearance.diffuse&&appearance.diffuse.enabled!==false&&appearance.diffuse.binding?.catalogue!==this.controller.catalogue)throw new TypeError('Emitter catalogue does not match the verified diffuse catalogue binding');
   const inputs=resolveSkyInputs(observer,appearance.atmosphere??{});observer=inputs.observer;
   const project=view.type==='allsky'?h=>projectAllSky(h,view):view.type==='legacy'?projectWidgetDome:h=>projectPerspective(h,view);
   const scene=this.controller.update(observer,{sceneIdentity,project});
   if(scene.status!=='ready')return this.last={status:scene.status,sceneIdentity,utcMs:observer.utcMs,error:scene.error,raster:null};
   return this.last={status:'ready',sceneIdentity,utcMs:observer.utcMs,observer,raster:renderPhysicalSky(scene.sources,{...appearance,atmosphere:inputs.atmosphere,observer,view})};
  }catch(e){return this.last={status:'unavailable',sceneIdentity,utcMs:observer?.utcMs,error:String(e.message??e),raster:null};}
 }
}

// real-sky/core/src/diffuse-assets.mjs
/** CP7.5: bounded, content-addressed diffuse admission and asynchronous selection.
 * The trusted shipped manifest hash pins runtime bytes; it is NOT a new signature
 * authenticating Gaia. Provenance/admission remain in the retained CP7.1–7.3 record.
 * No observer, camera, atmosphere or rendered frame is cached here.
 */



const DA_SOURCE='69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446';
function daFreeze(x){if(x&&typeof x==='object'&&!Object.isFrozen(x)){for(const v of Object.values(x))daFreeze(v);Object.freeze(x);}return x;}
function daHash(text){return sha256Hex(new TextEncoder().encode(text));}
function daCheckText(text,descriptor,label){if(typeof text!=='string')throw new TypeError(label+' must be exact UTF-8 text');const b=new TextEncoder().encode(text);if(b.byteLength!==descriptor.bytes)throw new RangeError(label+' byte size mismatch');if(sha256Hex(b)!==descriptor.sha256)throw new TypeError(label+' content hash mismatch');}
function daDescriptor(d,path,nside){if(!d||d.path!==path||!/^[0-9a-f]{64}$/.test(d.sha256??'')||!Number.isSafeInteger(d.bytes)||d.bytes<1||d.bytes>12000000)throw new TypeError('Invalid pinned asset descriptor');if(nside&&(d.nside!==nside||typeof d.id!=='string'||!d.id.length))throw new TypeError('Tier grid/identity mismatch');}
function parseDiffuseManifest(text,expectedSha256){
 if(typeof text!=='string'||text.length>65536||!/^[0-9a-f]{64}$/.test(expectedSha256??'')||daHash(text)!==expectedSha256)throw new TypeError('Diffuse manifest hash mismatch');
 const m=JSON.parse(text);if(m.schema!=='salah-real-sky/diffuse-runtime-manifest/1'||m.sourceSha256!==DA_SOURCE)throw new TypeError('Unsupported diffuse manifest version/source');
 daDescriptor(m.catalogue,'data/bright-stars.json');
 if(!m.assets||Object.keys(m.assets).sort().join(',')!=='128,32,64')throw new TypeError('Expected exactly three runtime tiers');
 for(const tier of ['32','64','128'])daDescriptor(m.assets[tier],'data/registered-starlight/V-nside'+tier+'.json',Number(tier));
 return daFreeze(m);
}
class DiffuseAssetStore{
 #cache=new Map();#serial=0;#controller=null;#disposed=false;#state;#text;
 constructor(manifestText,expectedManifestSha256,catalogueText){
  this.manifest=parseDiffuseManifest(manifestText,expectedManifestSha256);daCheckText(catalogueText,this.manifest.catalogue,'catalogue');
  this.catalogue=daFreeze(validateCatalogue(JSON.parse(catalogueText)));this.#text=catalogueText;
  this.#state=Object.freeze({status:'idle',generation:0,tier:null,binding:null,error:null});
  Object.defineProperty(this,'manifest',{writable:false,configurable:false});Object.defineProperty(this,'catalogue',{writable:false,configurable:false});
 }
 get snapshot(){return this.#state;}
 get cacheEntries(){return this.#cache.size;}
 async load(tier,readText,{reload=false}={}){
  if(this.#disposed)return this.#state;
  const generation=++this.#serial;this.#controller?.abort();const control=new AbortController();this.#controller=control;
  tier=String(tier);this.#state=Object.freeze({status:'loading',generation,tier,binding:null,error:null});
  try{
   const d=this.manifest.assets[tier];if(!d)throw new RangeError('Unsupported diffuse tier');
   if(typeof readText!=='function'||typeof reload!=='boolean')throw new TypeError('Reader and boolean reload required');
   if(reload)this.#cache.delete(d.sha256);
   let binding=this.#cache.get(d.sha256),cacheHit=!!binding;
   if(!binding){
    const text=await readText(d.path,{signal:control.signal,maxBytes:d.bytes});
    if(generation!==this.#serial||this.#disposed)return Object.freeze({status:'superseded',generation,tier,binding:null});
    daCheckText(text,d,'diffuse tier '+tier);const asset=JSON.parse(text);
    if(asset.grid?.nside!==d.nside||asset.id!==d.id)throw new TypeError('Manifest and decoded grid/identity disagree');
    binding=bindRegisteredStarlight(this.#text,asset);
   }
   if(generation!==this.#serial||this.#disposed)return Object.freeze({status:'superseded',generation,tier,binding:null});
   this.#cache.set(d.sha256,binding); // at most the three pinned manifest entries
   return this.#state=Object.freeze({status:'ready',generation,tier,binding,cacheHit,error:null,assetSha256:d.sha256});
  }catch(e){
   if(generation!==this.#serial||this.#disposed)return Object.freeze({status:'superseded',generation,tier,binding:null});
   return this.#state=Object.freeze({status:'unavailable',generation,tier,binding:null,error:String(e?.message??e)});
  }
 }
 dispose(){if(this.#disposed)return;this.#disposed=true;this.#serial++;this.#controller?.abort();this.#controller=null;this.#cache.clear();this.#text='';this.#state=Object.freeze({status:'disposed',generation:this.#serial,tier:null,binding:null,error:null});}
}
/** Bounded streaming UTF-8 read. A host may replace this with its authorised local
 * loader; cancellation/generation checks remain in the store even if a loader ignores abort.
 */
async function readDiffuseAssetText(url,{signal,maxBytes=12000000}={}){
 if(!Number.isSafeInteger(maxBytes)||maxBytes<1||maxBytes>12000000)throw new RangeError('Asset byte budget required');
 const response=await fetch(url,{signal});if(!response.ok){await response.body?.cancel().catch(()=>{});throw new Error('Asset HTTP '+response.status);}
 const declared=response.headers.get('content-length');if(declared!==null&&Number(declared)>maxBytes){await response.body?.cancel().catch(()=>{});throw new RangeError('Asset exceeds byte budget');}
 if(!response.body)throw new Error('Asset response body missing');
 const reader=response.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let total=0,text='';
 try{for(;;){const {done,value}=await reader.read();if(done)break;total+=value.byteLength;if(total>maxBytes)throw new RangeError('Asset exceeds byte budget');text+=decoder.decode(value,{stream:true});}text+=decoder.decode();return text;}
 catch(e){await reader.cancel().catch(()=>{});throw e;}finally{reader.releaseLock();}
}

// real-sky/core/src/diffuse-manifest-pin.mjs
// Generated by tools/build_cp75_manifest.py. Integrity anchor, not an upstream signature.
const DIFFUSE_MANIFEST_SHA256="630f169f30b617d947b5e3199eb854e8027a34540dde008da57b925577b777f6";

// real-sky/core/integration/resilient-sky-bridge.mjs
/** CP7.5 reference host wrapper; NOT actual-widget readiness integration.
 * A failed requested diffuse tier yields a NEW CP6 frame at the accepted observer.
 * Invalid physics/observer is never rescued by relabelling it an asset failure.
 */


class ResilientPhysicalSkyBridge{
 #store;#base;#bridges=new WeakMap();
 constructor(store){if(!(store instanceof DiffuseAssetStore))throw new TypeError('Verified diffuse asset store required');this.#store=store;this.#base=new PhysicalSkyBridge(store.catalogue);this.last=null;}
 render(observer,options={}){
  const state=this.#store.snapshot,wanted=options.diffuse!=null&&options.diffuse!==false&&options.diffuse.enabled!==false;
  const active=wanted&&state.status==='ready',binding=active?state.binding:null;let bridge=this.#base;
  if(active){bridge=this.#bridges.get(binding);if(!bridge){bridge=new PhysicalSkyBridge(binding.catalogue);this.#bridges.set(binding,bridge);}}
  const diffuse=active?{...options.diffuse,binding}:{enabled:false};
  const result=bridge.render(observer,{...options,diffuse});
  return this.last={...result,diffuseAsset:{mode:active?'registered':wanted?'cp6-fallback':'disabled',status:state.status,tier:state.tier,generation:state.generation,assetSha256:state.assetSha256??null,error:state.error??null,cacheEntries:this.#store.cacheEntries}};
 }
}

// real-sky/core/src/reference-engine.mjs
/** Serializable CP7.5 reference engine shared by worker and explicit main-thread fallback.
 * Callback modes here are declared test scenarios, not live weather or a second mask owner.
 */



class ReferenceSkyEngine{
 #pack;#store;#bridge;#loadKey=null;#disposed=false;
 constructor(pack){this.#pack=pack;this.#store=new DiffuseAssetStore(pack.manifestText,DIFFUSE_MANIFEST_SHA256,pack.catalogueText);this.#bridge=new ResilientPhysicalSkyBridge(this.#store);}
 async render(job){
  if(this.#disposed)throw new Error('Reference engine disposed');
  const start=performance.now(),fault=job.assetFault??'none',revision=job.assetRevision??0;
  if(!['none','missing','corrupt','wrong-version'].includes(fault)||!Number.isSafeInteger(revision)||revision<0)throw new TypeError('Invalid asset scenario/revision');
  if(typeof job.calendarMask!=='boolean'||typeof job.cloudmap!=='boolean')throw new TypeError('Explicit boolean mask/cloud modes required');
  const options={...job.options},wanted=options.diffuse!=null&&options.diffuse!==false&&options.diffuse.enabled!==false;
  if(wanted){
   const key=String(job.tier)+'/'+fault+'/'+revision;
   if(key!==this.#loadKey||this.#store.snapshot.status!=='ready'){
    const reload=this.#loadKey!==null&&(fault!=='none'||this.#loadKey.split('/')[1]!=='none'||Number(this.#loadKey.split('/')[2])!==revision);
    await this.#store.load(job.tier,async()=>{
     if(fault==='missing')throw new Error('Deliberate missing diffuse asset drill');
     const text=this.#pack.assetTexts?.[String(job.tier)];
     if(typeof text!=='string')throw new Error(this.#pack.assetErrors?.[String(job.tier)]??'Requested diffuse asset unavailable');
     if(fault==='corrupt')return text.slice(0,-1);
     if(fault==='wrong-version'){const a=JSON.parse(text);a.schema='unsupported/2';return JSON.stringify(a);}
     return text;
    },{reload});this.#loadKey=key;
   }
  }
  const loadEnd=performance.now(),v=options.view;
  if(job.cloudmap)options.cloudAt=(h,utcMs)=>h.azDeg>=180?.08:1;
  if(job.calendarMask)options.displayTransmissionAt=(x,y)=>Math.hypot(x-v.width*.72,y-v.height*.26)<24?0:1;
  const result=this.#bridge.render(job.observer,options);
  return {...result,timings:{assetLoadMs:loadEnd-start,renderMs:performance.now()-loadEnd,totalMs:performance.now()-start},engineContract:'serialisable accepted inputs; no rendered-frame cache'};
 }
 dispose(){if(this.#disposed)return;this.#disposed=true;this.#store.dispose();this.#pack=null;this.#bridge.last=null;}
}
/** Shared ArrayBuffer aliases must appear once in a transfer list. Metadata is cloned,
 * while these owned buffers are moved, not copied, to the accepting UI. */
function rasterTransferables(result){
 const seen=new Set(),out=[];
 function walk(v){if(v===null||typeof v!=='object')return;if(ArrayBuffer.isView(v)){if(v.buffer instanceof ArrayBuffer&&!seen.has(v.buffer)){seen.add(v.buffer);out.push(v.buffer);}return;}for(const x of Object.values(v))walk(x);}
 walk(result?.raster);return out;
}

// real-sky/native-contract.mjs
/** CP8 native boundary. All astronomical time comes from the accepted host snapshot. */
function nativeFinite(v,name,min=-Infinity,max=Infinity){if(typeof v!=='number'||!Number.isFinite(v)||v<min||v>max)throw new RangeError('Invalid native '+name);return v;}
function nativeIdentity(s){
 if(!s||typeof s!=='object')throw new TypeError('Native snapshot required');
 nativeFinite(s.utcMs,'UTC',-8640000000000000,8640000000000000);nativeFinite(s.lat,'latitude',-90,90);nativeFinite(s.lon,'longitude',-180,180);nativeFinite(s.heightM,'height',-500,10000);
 if(typeof s.sceneIdentity!=='string'||!s.sceneIdentity||!Number.isSafeInteger(s.generation)||s.generation<0)throw new TypeError('Accepted native scene/generation required');
 const c=s.camera??{};nativeFinite(c.azDeg,'camera azimuth',-360,360);nativeFinite(c.altDeg,'camera altitude',-90,90);nativeFinite(c.fovYDeg,'camera field of view',10,150);nativeFinite(c.rollDeg,'camera roll',-180,180);
 return JSON.stringify([s.sceneIdentity,s.generation,s.lat,s.lon,s.heightM,s.camera,s.weather,s.lp,s.reducedMotion,s.allowEstimates!==false,s.units,s.tz??null,s.timeScale??1,s.elevationSource??null,s.elevationOwner??null]);
}
function nativeJob(s,physical=false){
 const identity=nativeIdentity(s),w=s.weather;
 const visibility=typeof w?.vis==='number'&&Number.isFinite(w.vis)?Math.max(0,w.vis):20000;
 // Visibility is not an aerosol optical-depth measurement: this bounded mapping is an explicit scenario assumption.
 const aerosol=physical?.06+.3*Math.max(0,Math.min(1,1-visibility/20000)):.06;
 const temperature=typeof w?.temp==='number'&&Number.isFinite(w.temp)?(s.units==='f'?(w.temp-32)*5/9:w.temp):10;
 const lp=typeof s.lp==='number'&&Number.isFinite(s.lp)?Math.max(0,Math.min(1,s.lp)):0;
 return {observer:{utcMs:s.utcMs,latDeg:s.lat,lonDeg:s.lon,heightM:s.heightM,temperatureC:Math.max(-90,Math.min(70,temperature)),pressureHpa:0},
 native:{identity,generation:s.generation,sceneIdentity:s.sceneIdentity,weatherSource:w?.src??'unavailable',weatherAccepted:!!w,cloudOwner:physical?'native-linear-foreground':'native-interim-overlay',assumptions:{elevation:s.elevationSource??'explicit caller elevation; provenance not supplied',aerosol:'0.06 + 0.30*(1-visibility/20000), clamped; not measured AOD',pressure:'standard atmosphere from accepted elevation; astrometry remains geometric',localLight:'LPOLL × 0.003 cd/m² assumed non-stellar local light',cloud:'native painted total opacity, not measured optical depth'}},
 tier:128,
 options:{sceneIdentity:identity,view:{type:'camera',width:325,height:530,...s.camera},dpr:1,nominalExposure:24,autoExposure:true,backgroundStepCss:8,reducedMotion:!!s.reducedMotion,scintillation:{strength:0},
 atmosphere:{elevationM:s.heightM,aerosolTau550:aerosol,cloudTransmission:1,cloudGlowCdM2:0,lightPollutionCdM2:physical?lp*.003:0},
 diffuse:physical?{enabled:true,allowEstimates:s.allowEstimates!==false,samplesPerAxis:2,residualNight:{kind:'assumed-nonstellar-residual',zenithCdM2:.00014,source:'CP8 explicit non-stellar residual assumption; not measured airglow',includesRegisteredStarlight:false}}:{enabled:false}}};
}
// A numerical frame older than 30 accepted-UTC seconds is unavailable, not a current sky.
function nativeResultCurrent(job,current){try{return job.native.identity===nativeIdentity(current)&&Number.isFinite(job.observer.utcMs)&&Math.abs(current.utcMs-job.observer.utcMs)<=30000;}catch{return false;}}
/** Native calendar mask removes only direct astronomical light, never atmospheric sky. */
function nativeCalendarComposite(raster,mask=null){
 const out=new Float64Array(raster.linear.length),sky=raster.skyBackgroundLinear??raster.backgroundLinear,diffuse=raster.diffusePhysicalLinear;
 if(mask&&mask.length!==raster.width*raster.height)throw new RangeError('Calendar mask dimensions');
 for(let i=0;i<out.length;i++){const m=mask?mask[Math.floor(i/3)]:1;out[i]=sky[i]+(raster.stellarLinear[i]+(diffuse?.[i]??0))*m;}return out;
}

/** Map logical physics pixels through actual CSS bounds and the native SVG screen transform. */
function nativeDiscMask(width,height,rect,m,radius){
 // DOMMatrix coefficients are native getters. Read each exactly once; all
 // arithmetic and the one-pixel antialias ramp are identical to the CP8.3 mask.
 const {a,b,c,d,e,f}=m,det=a*d-b*c;if(!Number.isFinite(det)||Math.abs(det)<1e-12)throw new RangeError('Singular native Moon transform');
 const mask=new Float64Array(width*height),sx=rect.width/width,sy=rect.height/height;
 const aa=Math.max(1e-9,.5*(Math.hypot(d*sx,b*sx)+Math.hypot(c*sy,a*sy))/Math.abs(det));
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){
  const px=rect.left+(x+.5)*sx-e,py=rect.top+(y+.5)*sy-f;
  const xx=(d*px-c*py)/det,yy=(-b*px+a*py)/det;
  mask[y*width+x]=Math.max(0,Math.min(1,(Math.hypot(xx,yy)-radius)/aa+.5));
 }
 return mask;
}

// real-sky/native-engine.mjs





/** Real CP7 renderer with native inputs; none of the reference viewer's diagnostic masks. */
class NativeSkyEngine{
 constructor(pack){this.pack=pack;this.store=new DiffuseAssetStore(pack.manifestText,DIFFUSE_MANIFEST_SHA256,pack.catalogueText);this.bridge=new ResilientPhysicalSkyBridge(this.store);this.loaded=false;}
 async render(job){
  const start=performance.now();if(!this.pack)throw new Error('Native engine disposed');
  if(job.options.atmosphere.cloudTransmission!==1||job.options.atmosphere.cloudGlowCdM2!==0)throw new Error('Native foreground owns cloud transmission and colour exactly once');
  if(job.options.diffuse.enabled&&!this.loaded){await this.store.load(job.tier,async()=>{const t=this.pack.assetTexts?.[String(job.tier)];if(typeof t!=='string')throw new Error('Native diffuse asset missing');return t;});this.loaded=true;}
  const begin=performance.now(),result=this.bridge.render(job.observer,job.options);
  let sources=[];
  if(result.status==='ready')sources=projectCatalogue(this.store.catalogue,job.observer,h=>projectPerspective(h,job.options.view)).filter(s=>s.visible&&s.emission?.enabled!==false).map(s=>({id:s.id,hip:s.hip,hygId:s.hygId,name:s.properName??s.name??null,vmag:s.vmag,x:s.x,y:s.y,altDeg:s.altDeg,azDeg:s.azDeg}));
  return {...result,native:job.native,sources,timings:{assetMs:begin-start,renderMs:performance.now()-begin,totalMs:performance.now()-start},catalogue:{id:this.store.catalogue.id,records:this.store.catalogue.stars.length,emitters:this.store.catalogue.stars.filter(s=>s.emission?.enabled!==false).length,sha256:this.store.manifest.catalogue.sha256}};
 }
 dispose(){this.store.dispose();this.pack=null;this.bridge.last=null;}
}

// real-sky/core/src/reference-worker-client.mjs
/** RPC is sequential (the LatestRenderQueue owns replacement/coalescing).
 * Worker startup/crash/timeouts recover with an explicitly labelled main-thread
 * engine; scientific/render errors never silently choose a different sky.
 */

class ReferenceRenderClient{
 #pack;#worker=null;#fallback=null;#fallbackFactory;#ready;#readyResolve;#bootTimer;#timeout;#serial=0;#pending=new Map();#disposed=false;#mode='starting';#warnings=[];
 constructor(pack,{workerFactory=null,fallbackFactory=p=>new ReferenceSkyEngine(p),timeoutMs=120000}={}){
  if(!Number.isFinite(timeoutMs)||timeoutMs<1||timeoutMs>600000)throw new RangeError('Bounded worker timeout required');
  this.#pack=pack;this.#timeout=timeoutMs;this.#fallbackFactory=fallbackFactory;this.#ready=new Promise(resolve=>{this.#readyResolve=resolve;});
  try{
   if(typeof workerFactory!=='function')throw new Error('Web Worker unavailable or explicitly disabled');
   const w=workerFactory();this.#worker=w;
   w.onmessage=e=>this.#receive(e.data);w.onerror=e=>{e.preventDefault?.();this.#failWorker(e.message??'Worker error');};w.onmessageerror=()=>this.#failWorker('Worker message could not be decoded');
   this.#bootTimer=setTimeout(()=>this.#failWorker('Worker startup timeout'),timeoutMs);w.postMessage({kind:'boot',pack});
  }catch(e){this.#failWorker(e.message??String(e));}
 }
 get mode(){return this.#mode;}
 get warnings(){return [...this.#warnings];}
 #receive(m){
  if(this.#disposed)return;
  if(m?.kind==='fatal'){this.#failWorker(m.error??'Unhandled worker rejection');return;}
  if(m?.kind==='ready'&&this.#worker){clearTimeout(this.#bootTimer);this.#mode='worker';this.#readyResolve(true);return;}
  if(m?.kind==='error'&&m.id==null){this.#failWorker(m.error??'Worker startup failed');return;}
  const p=this.#pending.get(m?.id);if(!p)return;clearTimeout(p.timer);this.#pending.delete(m.id);
  if(m.kind==='result')p.resolve(m.result);else p.reject(new Error(m.error??'Invalid worker response'));
 }
 #failWorker(reason){
  if(this.#disposed)return;this.#warnings.push(String(reason));this.#mode='main-thread-fallback';clearTimeout(this.#bootTimer);
  this.#worker?.terminate();this.#worker=null;this.#readyResolve(false);
  for(const p of this.#pending.values()){clearTimeout(p.timer);const e=new Error(String(reason));e.code='WORKER_UNAVAILABLE';p.reject(e);}this.#pending.clear();
 }
 async run(job){
  if(this.#disposed)throw new Error('Render client disposed');await this.#ready;if(this.#disposed)throw new Error('Render client disposed');
  if(this.#worker){
   if(this.#pending.size)throw new Error('Worker client requires the latest-only sequential queue');
   try{
    const result=await new Promise((resolve,reject)=>{const id=++this.#serial,timer=setTimeout(()=>this.#failWorker('Worker render timeout'),this.#timeout);this.#pending.set(id,{resolve,reject,timer});try{this.#worker.postMessage({kind:'render',id,job});}catch(e){this.#failWorker(e.message??String(e));}});
    return {...result,execution:{mode:'worker',warnings:this.warnings}};
   }catch(e){if(e.code!=='WORKER_UNAVAILABLE')throw e;}
  }
  if(this.#disposed)throw new Error('Render client disposed');
  this.#fallback??=this.#fallbackFactory(this.#pack);await new Promise(resolve=>setTimeout(resolve,0));
  if(this.#disposed)throw new Error('Render client disposed');const result=await this.#fallback.render(job);
  return {...result,execution:{mode:'main-thread-fallback',warnings:this.warnings}};
 }
 /** Reference-viewer fault drill, never invoked by scientific calculation. */
 crashForTest(){this.#worker?.postMessage({kind:'crash-test'});}
 dispose(){
  if(this.#disposed)return;this.#disposed=true;this.#mode='disposed';clearTimeout(this.#bootTimer);this.#readyResolve(false);this.#worker?.terminate();this.#worker=null;
  for(const p of this.#pending.values()){clearTimeout(p.timer);p.reject(new Error('Render client disposed'));}this.#pending.clear();this.#fallback?.dispose();this.#fallback=null;this.#pack=null;
 }
}

// real-sky/core/src/latest-render-queue.mjs
/** One in-flight render + one latest replacement. No timer or observer-time cache.
 * The UI is invalidated immediately on submission, and only the latest ID publishes.
 * execute() may be a worker RPC or the explicitly labelled synchronous fallback.
 */
class LatestRenderQueue{
 #execute;#hooks;#next=0;#busy=false;#pending=null;#disposed=false;
 constructor(execute,hooks={}){if(typeof execute!=='function')throw new TypeError('Render executor required');this.#execute=execute;this.#hooks=hooks;}
 submit(request){
  if(this.#disposed)return Promise.resolve({status:'disposed'});
  const id=++this.#next;
  if(this.#pending){this.#pending.resolve({status:'superseded',id:this.#pending.id});this.#pending=null;}
  let snapshot;
  try{snapshot=structuredClone(request);}catch(e){this.#hooks.onPending?.(id);this.#hooks.onError?.(e,id);return Promise.resolve({status:'error',id,error:String(e.message??e)});}
  this.#hooks.onPending?.(id);
  const promise=new Promise(resolve=>{this.#pending={id,request:snapshot,resolve};});this.#drain();return promise;
 }
 async #drain(){
  if(this.#busy||!this.#pending||this.#disposed)return;
  this.#busy=true;const job=this.#pending;this.#pending=null;
  try{const result=await this.#execute(job.request,job.id);
   if(this.#disposed)job.resolve({status:'disposed',id:job.id});
   else if(job.id!==this.#next)job.resolve({status:'superseded',id:job.id});
   else{this.#hooks.onResult?.(result,job.id,job.request);job.resolve({status:'ready',id:job.id,result});}
  }catch(e){
   if(this.#disposed)job.resolve({status:'disposed',id:job.id});
   else if(job.id!==this.#next)job.resolve({status:'superseded',id:job.id});
   else{this.#hooks.onError?.(e,job.id);job.resolve({status:'error',id:job.id,error:String(e?.message??e)});}
  }finally{this.#busy=false;this.#drain();}
 }
 dispose(){if(this.#disposed)return;this.#disposed=true;this.#next++;if(this.#pending){this.#pending.resolve({status:'disposed',id:this.#pending.id});this.#pending=null;}}
}

// real-sky/native-encoding.mjs


// N001: the immutable encoder is monotone and quantizes to 256 byte values.
// Locate its exact binary64 transition points using that SAME numerical oracle
// on this JS engine. No approximate LUT/interpolation, new exposure or tolerance.
// The multiplication exposure*max(0,channel) keeps the reference's evaluation order.
let nativeEncodeEdges=null;
const nativeOracleCode=y=>Math.round(255*linearToSrgb(-Math.expm1(-y)));
function nativeEncodingThresholds(){
 if(!nativeEncodeEdges){
  const edges=new Float64Array(256);
  for(let code=1;code<256;code++){
   let low=0,high=32;
   for(;;){
    const middle=low+(high-low)/2;
    if(middle===low||middle===high)break;
    if(nativeOracleCode(middle)<code)low=middle;else high=middle;
   }
   edges[code]=high;
  }
  nativeEncodeEdges=edges;
 }
 // Diagnostic callers cannot corrupt the private encoding table.
 return nativeEncodeEdges.slice();
}
function encodeNativeFrame(linear,exposure=12){
 finite(exposure,'exposure',0,100000);
 if(linear.length%3)throw new RangeError('RGB buffer required');
 if(!nativeEncodeEdges)nativeEncodingThresholds();
 const edges=nativeEncodeEdges,bytes=new Uint8ClampedArray(linear.length/3*4);
 for(let i=0,j=0;i<linear.length;i+=3,j+=4){
  for(let c=0;c<3;c++){
   const y=exposure*Math.max(0,finite(linear[i+c],'linear channel'));
   let low=0,high=256;
   while(high-low>1){const middle=(low+high)>>>1;if(y<edges[middle])high=middle;else low=middle;}
   bytes[j+c]=low;
  }
  bytes[j+3]=255;
 }
 return bytes;
}

// real-sky/native-cloud-transfer.mjs
/** Native clouds are an 8-bit display-referred painting, not HDR radiance.
 * Canvas unpremultiplication can return code 255 at alpha 1/255. Inverting that
 * colour BEFORE coverage interprets rounding as a nearly infinite emitter.
 * Join bounded display-linear colour after the sky/lunar tone map, then return
 * to the existing shared encoder's input space. No second cloud application.
 */
const nativeCloudDisplay=Float64Array.from({length:256},(_,i)=>{
 const s=i/255;return s<=.04045?s/12.92:((s+.055)/1.055)**2.4;
});
function nativeCloudChannel(base,code,alpha,exposure){
 if(!Number.isFinite(base)||base<0||!Number.isInteger(code)||code<0||code>255||!Number.isFinite(alpha)||alpha<0||alpha>1||!Number.isFinite(exposure)||exposure<=0||exposure>100000)throw new RangeError('Invalid native cloud channel');
 if(alpha===0)return base;
 const display=-Math.expm1(-exposure*base)*(1-alpha)+nativeCloudDisplay[code]*alpha;
 return -Math.log1p(-Math.min(1-1/131072,display))/exposure;
}
function validateNativeRGBA(data,pixels){
 if(!data||data.length!==pixels*4)throw new RangeError('Native foreground dimensions');
 // getImageData owns a complete byte snapshot. Test/adaptor arrays must obey
 // the same contract; NaN must never silently become black in an output byte.
 if(!(data instanceof Uint8ClampedArray))for(const v of data)
  if(!Number.isInteger(v)||v<0||v>255)throw new RangeError('Invalid native RGBA');
 return data;
}

// real-sky/native-composition.mjs

/** Native foreground operator.
 * Input sky has received molecular/aerosol transport, NOT cloud attenuation.
 * Painted native cloud alpha is the sole total cloud transmission owner. Native
 * RGB/PBR are display-referred presentations, not measured radiance. Clouds join
 * in bounded display-linear light; opaque lunar material retains its transfer.
 */
function nativeInverseCode(code,exposure){
 if(!Number.isFinite(exposure)||exposure<=0||exposure>100000)throw new RangeError('Positive shared native exposure required');
 if(!Number.isFinite(code)||code<0||code>255)throw new RangeError('Native sRGB code out of range');
 const s=code/255,l=s<=.04045?s/12.92:((s+.055)/1.055)**2.4;
 // Code 255 denotes saturation, not infinite radiance. Clip at one half 16-bit step;
 // encoding this endpoint returns 255. The censoring assumption is explicit.
 return -Math.log1p(-Math.min(1-1/131072,l))/exposure;
}
function nativeCloudMaskAt(y){if(!Number.isFinite(y))throw new RangeError('Cloud mask coordinate');return y<=0||y>=.34?0:y<.03?y/.03:y<=.24?1:(.34-y)/.10;}
function nativeForeground(base,{cloudRGBA=null,moonRGBA=null,exposure}={}){
 if(!base||base.length%3)throw new RangeError('Native linear RGB input required');
 const pixels=base.length/3;for(const a of [cloudRGBA,moonRGBA])if(a)validateNativeRGBA(a,pixels);
 const inv=Float64Array.from({length:256},(_,i)=>nativeInverseCode(i,exposure)),out=new Float64Array(base.length);
 let cloudAlphaSum=0,maxAlpha=0,moonPixels=0;
 for(let p=0;p<pixels;p++){
  const ci=p*4,li=p*3,ma=moonRGBA?moonRGBA[ci+3]/255:0,ca=cloudRGBA?cloudRGBA[ci+3]/255:0;
  cloudAlphaSum+=ca;maxAlpha=Math.max(maxAlpha,ca);if(ma>0)moonPixels++;
  for(let k=0;k<3;k++){
   const v=base[li+k];if(!Number.isFinite(v)||v<0)throw new RangeError('Nonphysical native base channel');
   const lunar=ma? v*(1-ma)+inv[moonRGBA[ci+k]]*ma:v;
   out[li+k]=ca?nativeCloudChannel(lunar,cloudRGBA[ci+k],ca,exposure):lunar;
  }
 }
 return {linear:out,diagnostics:{cloudApplications:1,meanCloudAlpha:cloudAlphaSum/Math.max(1,pixels),maxCloudAlpha:maxAlpha,moonPixels,cloudTransmissionOwner:'1 - native painted alpha after native blur and vertical mask',order:'gas-transported sky → calendar direct-light cutout → native PBR material → bounded display-linear cloud screen → shared encode',cloudColour:'display-referred native painter; coverage before inverse tone map; not measured cloud radiance',exposureOwner:'CP7 sky+diffuse meter before calendar/foreground; native foreground excluded',saturation:'bounded cloud display energy; native lunar code 255 uses 1 - 1/131072'}};
}
/** Exact leading-row restriction of the calendar/direct-light join. */
function nativeCalendarRegion(raster,mask=null,rows=raster.height){
 if(!Number.isInteger(rows)||rows<1||rows>raster.height)throw new RangeError('Native region rows');
 const pixels=raster.width*rows;if(mask&&mask.length!==pixels)throw new RangeError('Native regional mask dimensions');
 const out=new Float64Array(pixels*3),sky=raster.skyBackgroundLinear??raster.backgroundLinear,diffuse=raster.diffusePhysicalLinear;
 for(let i=0;i<out.length;i++){const m=mask?mask[Math.floor(i/3)]:1;out[i]=sky[i]+(raster.stellarLinear[i]+(diffuse?.[i]??0))*m;}return out;
}
/** Cover the moving Moon's old and new bounds, and the native cloud support.
 * Two logical-pixel padding covers antialiasing; never crop the physical frame. */
function nativeForegroundRows(height,currentBottom=0,previousBottom=0){
 if(!Number.isInteger(height)||height<1||!Number.isFinite(currentBottom)||!Number.isFinite(previousBottom))throw new RangeError('Native foreground bounds');
 return Math.max(1,Math.min(height,Math.ceil(Math.max(.34*height,currentBottom,previousBottom)+2)));
}
/** Capture DOM pixels without a second sky/clock/weather owner. Uses the native
 * 300px backing canvas directly (the SVG image path adds an avoidable resample):
 * no re-lit Moon, no new texture and no asynchronous PNG/phase race.
 */
class NativeForegroundCapture{
 constructor(canvas){this.canvas=canvas;this.cloud=document.createElement('canvas');this.moon=document.createElement('canvas');for(const c of [this.cloud,this.moon]){c.width=325;c.height=530;}this.cx=this.cloud.getContext('2d',{willReadFrequently:true});this.mx=this.moon.getContext('2d',{willReadFrequently:true});if(!this.cx||!this.mx)throw new Error('Native foreground capture unavailable');}
 bottom(){
  const p=document.querySelector('.mphoto'),m=p?.getScreenCTM(),r=this.canvas.getBoundingClientRect();
  if(!m||!(r.height>0))return 0;
  const x=Number(p.getAttribute('x')),y=Number(p.getAttribute('y')),w=Number(p.getAttribute('width')),h=Number(p.getAttribute('height'));
  return Math.max(...[[x,y],[x+w,y],[x,y+h],[x+w,y+h]].map(([a,b])=>(m.b*a+m.d*b+m.f-r.top)*530/r.height));
 }
 capture(rows=530){
  if(!Number.isInteger(rows)||rows<1||rows>530)throw new RangeError('Native capture rows');
  for(const c of [this.cloud,this.moon])if(c.height!==rows)c.height=rows;
  const cloud=document.querySelector('.cloudcanvas'),photo=document.querySelector('.mphoto'),group=document.querySelector('.moon'),features=document.querySelector('.mfeatures'),card=document.querySelector('.c');
  const rect=this.canvas.getBoundingClientRect();if(!(rect.width>0&&rect.height>0))throw new Error('Native canvas has no drawable bounds');
  const cx=this.cx,mx=this.mx;cx.resetTransform();cx.clearRect(0,0,325,530);cx.globalCompositeOperation='source-over';cx.globalAlpha=1;
  if(cloud){const filter=getComputedStyle(cloud).filter;const blur=/^blur\(([\d.]+)px\)$/.exec(filter);if(filter!=='none'&&!blur)throw new Error('Unsupported native cloud filter');cx.filter=blur?'blur('+(Number(blur[1])*325/rect.width)+'px)':'none';cx.drawImage(cloud,0,0,325,530);cx.filter='none';
   // Native mask-image is explicitly bound by the source-preservation test. Mask after filtering.
   const grad=cx.createLinearGradient(0,0,0,530);grad.addColorStop(0,'rgba(0,0,0,0)');grad.addColorStop(.03,'#000');grad.addColorStop(.24,'#000');grad.addColorStop(.34,'rgba(0,0,0,0)');grad.addColorStop(1,'rgba(0,0,0,0)');cx.globalCompositeOperation='destination-in';cx.fillStyle=grad;cx.fillRect(0,0,325,530);cx.globalCompositeOperation='source-over';
  }
  mx.resetTransform();mx.clearRect(0,0,325,530);mx.globalAlpha=1;
  const surface=window.SalahNativeSkyHost.lunarSurface();
  // A current device-resolution join owns the complete lunar footprint. Leaving
  // a resampled copy below it exposes a second edge outside its covered pixels.
  // Loading, failure and unsupported detail geometry retain the native path.
  const detail=!!window.SalahMoonRuntime?.detailEnabled;
  const ready=!!(!detail&&card?.classList.contains('moon-ready')&&photo?.getAttribute('href')&&surface);
  let moonAlpha=0;
  if(ready){const t=photo.getScreenCTM();if(!t)throw new Error('Native Moon transform unavailable');moonAlpha=Math.max(0,Math.min(1,Number(getComputedStyle(group).opacity)*Number(getComputedStyle(features).opacity)));
   if(moonAlpha>0){const sx=325/rect.width,sy=530/rect.height;mx.setTransform(t.a*sx,t.b*sy,t.c*sx,t.d*sy,(t.e-rect.left)*sx,(t.f-rect.top)*sy);mx.globalAlpha=moonAlpha;
    mx.drawImage(surface,Number(photo.getAttribute('x')),Number(photo.getAttribute('y')),Number(photo.getAttribute('width')),Number(photo.getAttribute('height')));mx.resetTransform();mx.globalAlpha=1;
   }
  }
  return {cloudRGBA:cx.getImageData(0,0,325,rows).data,moonRGBA:mx.getImageData(0,0,325,rows).data,native:{moonSurface:detail?'device-resolution-owned':ready?'native-300px-backing-canvas':'unavailable',moonAlpha,cloudBuffer:cloud?{width:cloud.width,height:cloud.height}:null,maskStops:[0,.03,.24,.34,1],cloudSource:getComputedStyle(cloud).visibility}};
 }
}

/** Exact dirty-input guard adapted from the donor's cloud-only reuse check.
 * Our native Moon is inside the joined framebuffer, so cloud equality alone
 * is insufficient. Capture arrays are owned snapshots from getImageData.
 */
function sameNativePresentation(a,b){
 if(!a||!b||!a.frame||a.frame!==b.frame||a.rows!==b.rows||a.maskKey!==b.maskKey)return false;
 for(const key of ['cloudRGBA','moonRGBA']){
  const x=a[key],y=b[key];if(!x||!y||x.length!==y.length)return false;
  for(let i=0;i<x.length;i++)if(x[i]!==y[i])return false;
 }
 return true;
}

// real-sky/native-worker-policy.mjs
/** CP9 donor-derived responsiveness invariant: optional physical rendering may not
 * occupy the prayer/settings UI thread when worker execution is unavailable.
 * CP7's reference client remains unchanged; this is the native host policy only.
 */
function requireNativeWorker(_pack){
 throw new Error('Native physical-sky worker unavailable; visual withdrawn to preserve prayer responsiveness. Retry real-sky assets to restart the worker.');
}

// real-sky/native-lifecycle.mjs


/** Native-only scheduling/fencing. Never supplies or advances astronomical time.
 * One active execution and one newest pending request belong to the retained queue.
 * Monotonic time detects wall-clock discontinuities; it is never a render UTC.
 */
class NativeSkyLifecycle {
 constructor({capture,execute,onResult=()=>{},onInvalidate=()=>{},onError=()=>{},onAvailability=()=>{},now=()=>performance.now(),physical=true,intervalMs=4000}) {
  this.capture=capture;this.now=now;this.physical=physical;this.intervalMs=intervalMs;
  this.hooks={onResult,onInvalidate,onError,onAvailability};this.epoch=0;this.identity=null;this.observed=null;
  this.availability={status:'pending',reason:'initial'};this.durations=new WeakMap();
  this.displayed=null;this.latest=null;this.pending=null;this.lastSubmit=-Infinity;this.disposed=false;
  this.counts={requests:0,accepted:0,superseded:0,rejected:0,invalidations:0};
  this.queue=new LatestRenderQueue(async(job,id)=>{
   const started=this.now(),result=await execute(job,id);this.durations.set(job,this.now()-started);return result;
  },{
   onResult:(result,id,job)=>{
    const state=this.capture();
    if(!this.current(job,state)){
     this.counts.rejected++;
     // Only the still-owned request may report a throughput limitation. A late
     // result from another target/epoch never overwrites successor diagnostics.
     if(!this.disposed&&!state.paused&&job.native.lifecycleEpoch===this.epoch&&job.native.identity===nativeIdentity(state)&&Math.abs(state.timeScale)>1&&Math.abs(state.utcMs-job.observer.utcMs)>30000){
      this.setAvailability({status:'unavailable',reason:'rate-throughput',rate:state.timeScale,wallBudgetMs:30000/Math.abs(state.timeScale),executionMs:this.durations.get(job)});
     }
     return;
    }
    if(result.status!=='ready'||!result.raster)throw new Error(result.error??'Native real sky unavailable');
    this.setAvailability({status:'available',reason:'current-frame',rate:state.timeScale??1,executionMs:this.durations.get(job)});
    this.displayed=job;this.hooks.onResult(result,id,job);this.counts.accepted++;
   },
   onError:(error,id)=>{if(this.current(this.latest))this.hooks.onError(error,id);else this.counts.rejected++;}
  });
 }
 get state(){return {...this.counts,epoch:this.epoch,disposed:this.disposed,pending:!!this.pending,paused:!!this.observed?.paused,availability:{...this.availability}};}
 setAvailability(value){this.availability=value;this.hooks.onAvailability({...value});}
 invalidate(reason='native invalidation') {
  if(this.disposed)return;
  this.epoch++;this.displayed=null;this.counts.invalidations++;this.setAvailability({status:'pending',reason});this.hooks.onInvalidate(reason);
 }
 observe(state=this.capture()) {
  if(this.disposed)return null;
  let key;
  try{key=nativeIdentity(state);}catch(error){
   if(this.identity!==null||this.observed!==null)this.invalidate('invalid accepted native input');
   this.identity=null;this.observed=null;return null;
  }
  const now=this.now(),rate=Number.isFinite(state.timeScale)?state.timeScale:1,prior=this.observed;
  // Native explicit preview anchors are already part of sceneIdentity. This also
  // catches host wall-clock corrections without inventing a private wall clock.
  const jump=prior&&Math.abs((state.utcMs-prior.utcMs)-(now-prior.now)*prior.rate)>1000;
  let reason=null;
  if(key!==this.identity)reason='new accepted native scene';
  else if(prior&&!!state.paused!==prior.paused)reason=state.paused?'native hidden/paused':'native visible/resumed';
  else if(jump)reason='native clock discontinuity';
  else if(this.displayed&&!nativeResultCurrent(this.displayed,state)){
   // Expiration withdraws the visible frame, not a newer in-flight computation
   // of the same accepted scene. Its own UTC/identity/epoch is checked at publish.
   this.displayed=null;this.hooks.onInvalidate('native frame expired');
  }
  this.identity=key;this.observed={now,utcMs:state.utcMs,rate,paused:!!state.paused};
  if(reason)this.invalidate(reason);
  return state;
 }
 current(job,state) {
  if(this.disposed||!job)return false;
  let current;
  try{current=this.observe(state??this.capture());}catch{return false;}
  return !!current&&!current.paused&&job.native.lifecycleEpoch===this.epoch&&nativeResultCurrent(job,current);
 }
 request(force=false) {
  if(this.disposed)return Promise.resolve({status:'disposed'});
  let state;
  try{state=this.observe();}catch(error){this.invalidate('host capture failed');this.hooks.onError(error);return Promise.resolve({status:'invalid'});}
  if(!state){this.hooks.onError(new Error('Invalid accepted native input'));return Promise.resolve({status:'invalid'});}
  if(state.paused)return Promise.resolve({status:'paused'});
  const changed=!this.latest||this.latest.native.lifecycleEpoch!==this.epoch;
  if(!changed&&this.pending?.observer.utcMs===state.utcMs)return Promise.resolve({status:'pending'});
  if(!force&&!changed&&this.pending)return Promise.resolve({status:'pending'});
  if(!force&&!changed&&this.displayed?.observer.utcMs===state.utcMs)return Promise.resolve({status:'unchanged'});
  const interval=Math.min(this.intervalMs,15000/Math.max(1,Math.abs(state.timeScale??1)));
  if(!force&&!changed&&this.now()-this.lastSubmit<interval)return Promise.resolve({status:'throttled'});
  const job=nativeJob(state,this.physical);job.native.lifecycleEpoch=this.epoch;
  this.latest=job;this.pending=job;this.lastSubmit=this.now();this.counts.requests++;
  return this.queue.submit(job).then(result=>{
   if(this.pending===job)this.pending=null;
   if(result.status==='superseded')this.counts.superseded++;
   return {status:result.status,id:result.id};
  });
 }
 dispose(){if(this.disposed)return;this.invalidate('disposed');this.disposed=true;this.queue.dispose();this.pending=null;this.latest=null;this.observed=null;}
}

// real-sky/native-assets.mjs
/** Optional native asset acquisition: bounded, retryable, latest-generation only.
 * Byte/hash admission remains in the retained engine, not this acquisition layer.
 */
class NativeAssetLoader {
 constructor({load,start,onState=()=>{},onReset=()=>{},timeoutMs=15000}) {
  if(!Number.isFinite(timeoutMs)||timeoutMs<1||timeoutMs>120000)throw new RangeError('Bounded native asset deadline required');
  this.load=load;this.start=start;this.onState=onState;this.onReset=onReset;this.timeoutMs=timeoutMs;
  this.generation=0;this.controller=null;this.disposed=false;this.suspended=false;this.value={status:'idle',generation:0,error:null};
 }
 get state(){return {...this.value};}
 publish(status,error=null){this.value={status,generation:this.generation,error};this.onState(this.state);}
 async retry() {
  if(this.disposed)return {status:'disposed'};
  if(this.suspended)return this.state;
  const generation=++this.generation;this.controller?.abort();this.onReset();
  const controller=new AbortController();this.controller=controller;this.publish('loading');let timer;
  try {
   const deadline=new Promise((_,reject)=>{timer=setTimeout(()=>{reject(new Error('Native sky asset timeout'));controller.abort();},this.timeoutMs);});
   const pack=await Promise.race([this.load(controller.signal,generation),deadline]);
   if(this.disposed||generation!==this.generation)return {status:'superseded'};
   this.start(pack);this.publish('ready');
  }catch(error){
   if(this.disposed||generation!==this.generation)return {status:'superseded'};
   this.onReset();this.publish('unavailable',String(error?.message??error));
  }finally{clearTimeout(timer);if(this.controller===controller)this.controller=null;}
  return this.state;
 }
 // Page lifecycle is reversible; explicit disposal is not. Invalidate before abort
 // so even a loader that ignores AbortSignal cannot publish after pagehide.
 suspend(){if(this.disposed||this.suspended)return;this.suspended=true;this.generation++;this.controller?.abort();this.controller=null;this.onReset();this.publish('suspended');}
 resume(){if(this.disposed||!this.suspended)return Promise.resolve(this.state);this.suspended=false;return this.retry();}
 dispose(){if(this.disposed)return;this.disposed=true;this.generation++;this.controller?.abort();this.controller=null;this.onReset();this.publish('disposed');}
}

/** Ordinary static-folder script path and the same app's inline expansion.
 * Retry refetches the pinned local script; no network source substitution exists.
 */
function startNativeSkyAssets(start,scriptUrl) {
 const inline=window.__SALAH_REAL_SKY_PACK__;delete window.__SALAH_REAL_SKY_PACK__;
 let badge=null,loader;
 const reset=()=>{window.SalahRealSky?.dispose();window.SalahRealSky=null;window.realSkyFrame=()=>null;};
 const state=asset=>{
  if(asset.status==='ready'){badge?.remove();badge=null;return;}
  window.realSkyState=()=>({checkpoint:'9',status:loader.state.status,assets:loader.state,errors:loader.state.error?[loader.state.error]:[],last:null});
  if(asset.status==='disposed'||asset.status==='suspended'){badge?.remove();badge=null;return;}
  if(!badge){badge=document.createElement('span');badge.className='real-sky-status real-sky-asset-status';badge.setAttribute('role','status');document.querySelector('.c')?.append(badge);}
  badge.textContent=asset.status==='loading'?'Real sky loading…':'Real sky unavailable';badge.title=asset.error??'Optional astronomy does not gate prayer readiness';
 };
 const load=(signal,generation)=>{
  if(inline)return Promise.resolve(inline);
  return new Promise((resolve,reject)=>{
   const el=document.createElement('script');
   const cleanup=()=>{signal.removeEventListener('abort',abort);el.onload=null;el.onerror=null;el.remove();};
   const abort=()=>{cleanup();reject(new Error('Native sky asset load aborted'));};
   el.onload=()=>{const pack=window.__SALAH_REAL_SKY_PACK__;delete window.__SALAH_REAL_SKY_PACK__;cleanup();if(pack)resolve(pack);else reject(new Error('Native sky asset script supplied no pack'));};
   el.onerror=()=>{cleanup();reject(new Error('Local native-data.js unavailable'));};
   if(signal.aborted){abort();return;}signal.addEventListener('abort',abort,{once:true});
   // A removed script may leave a pending network request alive. Distinct local
   // attempt URLs prevent browser request coalescing; exact bytes stay pinned.
   try{const url=new URL('native-data.js',scriptUrl);url.searchParams.set('nativeSkyGeneration',String(generation));el.src=url.href;document.head.append(el);}catch(error){cleanup();reject(error);}
  });
 };
 loader=new NativeAssetLoader({load,start,onState:state,onReset:reset});
 const pagehide=()=>loader.suspend(),pageshow=event=>{if(event.persisted)loader.resume();};
 window.addEventListener('pagehide',pagehide);window.addEventListener('pageshow',pageshow);
 window.SalahRealSkyAssets={retry:()=>loader.retry(),dispose:()=>{window.removeEventListener('pagehide',pagehide);window.removeEventListener('pageshow',pageshow);loader.dispose();},get state(){return loader.state;}};
 loader.retry();return loader;
}

// real-sky/native-host.mjs






/** DOM ownership adapter; native PBR/calendar/weather remain native source code. */
function startNativeSky(pack,workerSource,physical){
 window.SalahRealSky?.dispose();
 const host=window.SalahNativeSkyHost,card=document.querySelector('.c');if(!host||!card)throw new Error('Native host/card missing');
 const canvas=document.createElement('canvas');canvas.className='real-sky-canvas';canvas.width=325;canvas.height=530;canvas.setAttribute('aria-hidden','true');card.prepend(canvas);
 const ctx=canvas.getContext('2d',{alpha:false});if(!ctx)throw new Error('Canvas 2D unavailable');
 const badge=document.createElement('span');badge.className='real-sky-status';badge.setAttribute('role','status');card.append(badge);
 const foreground=physical?new NativeForegroundCapture(canvas):null;
 const status={checkpoint:physical?'9':'8.1',workerFailurePolicy:'withdraw optional sky; never synchronous physical rendering on the prayer UI thread',status:'loading',renders:0,presentationDraws:0,presentationSkips:0,presentationRejections:0,presentationUtcMs:null,rejections:0,errors:[],physical,dprPolicy:'325×530 physics raster at DPR 1; browser scales canvas; no high-DPR certification',last:null};
 let client,lifecycle,frame=null,job=null,disposed=false,paintedFrame=null,paintedJob=null,previousPresentation=null,previousMoonBottom=0,lastCompose=-Infinity,animationId=null,workerUrl=null;
 function publish(){badge.textContent=status.status==='ready'?(status.last?.diffuseAsset?.mode==='cp6-fallback'?'Diffuse unavailable — CP6 sky':status.last?.diffuseState?.exposureComplete===false?'Diffuse support incomplete':''):status.status==='loading'?'Real sky loading…':status.status==='pending'?'Real sky updating…':status.availability?.reason==='rate-throughput'?`Real sky unavailable at ${status.availability.rate}×`:'Real sky unavailable';badge.title=status.errors.at(-1)??'Optional astronomy; prayer readiness is independent';canvas.dataset.status=status.status;}
 function clear(reason='invalidated'){window.SalahMoonDetail?.clear();card.classList.remove('real-sky-composed');frame=null;job=null;status.last=null;paintedFrame=null;paintedJob=null;status.presentationUtcMs=null;previousPresentation=null;previousMoonBottom=0;ctx.clearRect(0,0,325,530);canvas.style.visibility='hidden';status.status='pending';status.reason=reason;publish();}
 function snapshot(){return host.capture();}
 function calendarGeometry(rows=530){
  if(window.SalahMoonRuntime?.detailEnabled)return {key:'separate-device-resolution-moon',mask:()=>null};
  const disc=document.querySelector('.moon-mask-disc'),matrix=disc?.getScreenCTM();
  if(!matrix||!disc.classList.contains('mask-on')||+getComputedStyle(disc).opacity===0)return {key:null,mask:()=>null};
  const r=canvas.getBoundingClientRect(),{a,b,c,d,e,f}=matrix,m={a,b,c,d,e,f},radius=Number(disc.getAttribute('r'));
  const rect={left:r.left,top:r.top,width:r.width,height:r.height*rows/530};
  return {key:JSON.stringify([rows,rect,a,b,c,d,e,f,radius]),mask:()=>nativeDiscMask(325,rows,rect,m,radius)};
 }
 function compose(){
  if(!frame||disposed)return;
  try{
   const current=snapshot();if(!lifecycle.current(job,current)){clear('host target changed or expired');return;}
   const started=performance.now();
   if(foreground){
    // Full physical frames change only on worker acceptance. Native clouds/Moon
    // can move independently; repaint their entire old/new support, not all 530 rows.
    const bottom=foreground.bottom(),rows=nativeForegroundRows(530,bottom,previousMoonBottom);
    const capture=foreground.capture(rows),geometry=calendarGeometry(rows);
    const presentation={frame,rows,maskKey:geometry.key,cloudRGBA:capture.cloudRGBA,moonRGBA:capture.moonRGBA};
    // Unlike the donor cloud-only guard, this also fences physical frame, PBR
    // bytes, native cutout geometry and old/new foreground support dimensions.
    if(sameNativePresentation(previousPresentation,presentation)){
     status.presentationSkips++;lastCompose=performance.now();
     Object.assign(status.last.composition,capture.native,{lastComposeMs:lastCompose-started});
     card.classList.add('real-sky-composed');canvas.style.visibility='visible';window.SalahMoonDetail?.compose(frame,encodeNativeFrame);return;
    }
    const base=nativeCalendarRegion(frame.raster,geometry.mask(),rows);
    const joined=nativeForeground(base,{...capture,exposure:frame.raster.effectiveExposure});
    // Prepare/validate the entire update before touching the visible framebuffer.
    // A failed capture must not expose an uncomposed base (or partial cloud data).
    const region=new ImageData(encodeNativeFrame(joined.linear,frame.raster.effectiveExposure),325,rows);
    const full=paintedFrame!==frame?new ImageData(encodeNativeFrame(frame.raster.linear,frame.raster.effectiveExposure),325,530):null;
    if(full)ctx.putImageData(full,0,0);
    ctx.putImageData(region,0,0);
    paintedFrame=frame;paintedJob=job;status.presentationUtcMs=job.observer.utcMs;previousMoonBottom=bottom;
    previousPresentation=presentation;status.presentationDraws++;
    status.last.composition={...joined.diagnostics,meanCloudAlpha:joined.diagnostics.meanCloudAlpha*rows/530,...capture.native,updatedRows:rows,totalRows:530};card.classList.add('real-sky-composed');
   }else{
    const bytes=encodeNativeFrame(nativeCalendarComposite(frame.raster,calendarGeometry().mask()),frame.raster.effectiveExposure);ctx.putImageData(new ImageData(bytes,325,530),0,0);
   }
   canvas.style.visibility='visible';window.SalahMoonDetail?.compose(frame,encodeNativeFrame);lastCompose=performance.now();
   if(status.last.composition)status.last.composition.lastComposeMs=lastCompose-started;
  }catch(e){
   // Retention is allowed only under the ORIGINAL visible job's fences and
   // 30-second age limit. A seek/configuration/epoch change still clears now.
   if(paintedJob&&lifecycle.current(paintedJob)){
    status.presentationRejections++;status.lastPresentationError=String(e?.message??e);lastCompose=performance.now();return;
   }
   failure(e);
  }
 }

 function accept(result,_id,request){
  const current=snapshot();if(!lifecycle.current(request,current)){status.rejections++;return;}
  if(result.status!=='ready'||!result.raster)throw new Error(result.error??'Native real sky unavailable');
  frame=result;job=request;status.status='ready';status.renders++;status.last={utcMs:result.utcMs,observer:result.observer,native:result.native,catalogue:result.catalogue,sources:result.sources,drawn:result.raster.drawn,detectableSources:result.raster.detectableSources,diffuseAsset:result.diffuseAsset,diffuseState:result.raster.diffuseState??null,physicalState:result.raster.physicalState,exposure:result.raster.effectiveExposure,atmosphere:result.raster.atmosphere,visibilityScope:physical?'CP7 contrast diagnostics are before native cloud foreground; final pixel/operator evidence is separate':'CP7 pre-native-overlay contrast diagnostic',weather:current.weather,view:request.options.view,execution:result.execution,timings:result.timings,warnings:result.raster.modelWarnings};compose();publish();
 }
 function failure(e){if(disposed)return;clear('render failure');status.status='unavailable';const message=String(e?.message??e);if(status.errors.at(-1)!==message)status.errors.push(message);status.errors=status.errors.slice(-12);publish();}
 client=new ReferenceRenderClient(pack,{workerFactory:()=>{workerUrl=URL.createObjectURL(new Blob([workerSource],{type:'text/javascript'}));return new Worker(workerUrl);},fallbackFactory:requireNativeWorker,timeoutMs:15000});
 lifecycle=new NativeSkyLifecycle({capture:snapshot,physical,execute:request=>client.run(request),onResult:accept,onInvalidate:clear,onError:failure,onAvailability:value=>{status.availability=value;if(value.status==='unavailable'&&!frame){status.status='unavailable';status.reason=value.reason;publish();}}});
 const request=(force=false)=>lifecycle.request(force);
 // Presentation sampling is not an astronomical clock. It samples native painter
 // output and native SVG transforms; only accepted host UTC drives physics jobs.
 const timer=setInterval(()=>request(),500);
 function animate(now){if(disposed)return;try{const state=snapshot();if(frame&&!lifecycle.current(job,state))clear('host target changed or expired');if(frame&&!state.paused&&now-lastCompose>=(state.reducedMotion?250:50))compose();}catch(e){failure(e);}animationId=requestAnimationFrame(animate);}
 animationId=requestAnimationFrame(animate);
 const visibility=()=>request(true);document.addEventListener('visibilitychange',visibility);
 const readState=()=>({...structuredClone(status),lifecycle:lifecycle.state});
 window.SalahRealSky={request,compose,invalidate:reason=>lifecycle.invalidate(reason),get state(){return readState();},dispose(){if(disposed)return;lifecycle.dispose();disposed=true;clearInterval(timer);cancelAnimationFrame(animationId);document.removeEventListener('visibilitychange',visibility);client.dispose();if(workerUrl)URL.revokeObjectURL(workerUrl);card.classList.remove('real-sky-composed');frame=null;job=null;previousPresentation=null;status.last=null;status.status='disposed';canvas.remove();badge.remove();}};
 window.realSkyState=readState;window.realSkyFrame=()=>frame; // Diagnostics, not render authority.
 publish();request(true);
}

startNativeSkyAssets(pack=>startNativeSky(pack,"// real-sky/core/src/time-scales.mjs\n/** Time policy: USNO TAI-UTC table, IERS Bulletin C72 (2026-07-06), NASA historical DeltaT.\n * See docs/CHECKPOINT_4.md. Numeric POSIX milliseconds cannot represent a leap-second label.\n * No host clock or time zone is read. Future offsets are explicitly uncertain, not predicted.\n */\nconst TS_DAY=86400000;\nconst TS_LEAPS=[[1972,1,10],[1972,7,11],[1973,1,12],[1974,1,13],[1975,1,14],[1976,1,15],[1977,1,16],[1978,1,17],[1979,1,18],[1980,1,19],[1981,7,20],[1982,7,21],[1983,7,22],[1985,7,23],[1988,1,24],[1990,1,25],[1991,1,26],[1992,7,27],[1993,7,28],[1994,7,29],[1996,1,30],[1997,7,31],[1999,1,32],[2006,1,33],[2009,1,34],[2012,7,35],[2015,7,36],[2017,1,37]].map(([y,m,n])=>[Date.UTC(y,m-1,1),n]);\nconst TS_DRIFTS=[[1961,1,1.422818,37300,.001296],[1961,8,1.372818,37300,.001296],[1962,1,1.845858,37665,.0011232],[1963,11,1.945858,37665,.0011232],[1964,1,3.240130,38761,.001296],[1964,4,3.340130,38761,.001296],[1964,9,3.440130,38761,.001296],[1965,1,3.540130,38761,.001296],[1965,3,3.640130,38761,.001296],[1965,7,3.740130,38761,.001296],[1965,9,3.840130,38761,.001296],[1966,1,4.313170,39126,.002592],[1968,2,4.213170,39126,.002592]].map(([y,m,a,b,c])=>[Date.UTC(y,m-1,1),a,b,c]);\nfunction tsNumber(x,label,min=-Infinity,max=Infinity){if(typeof x!=='number'||!Number.isFinite(x)||x<min||x>max)throw new RangeError(label+' out of range');return x;}\nfunction historicDeltaT(y){let t;if(y<1920){t=y-1900;return -2.79+1.494119*t-.0598939*t*t+.0061966*t**3-.000197*t**4;}if(y<1941){t=y-1920;return 21.2+.84493*t-.0761*t*t+.0020936*t**3;}t=y-1950;return 29.07+.407*t-t*t/233+t**3/2547;}\nfunction timeScales(observer){\n const ms=tsNumber(observer.utcMs,'UTC milliseconds'),date=new Date(ms),year=date.getUTCFullYear();\n if(!Number.isFinite(year)||year<1900||year>2100)throw new RangeError('supported dates: Gregorian1900\u20132100');\n const jdUtc=ms/TS_DAY+2440587.5,dut1=tsNumber(observer.dut1Seconds??0,'UT1-UTC',-1,1),warnings=[];let offset;\n if(observer.dut1Seconds==null)warnings.push('UT1-assumed-UTC');\n if(observer.ttMinusUtcSeconds!=null)offset=tsNumber(observer.ttMinusUtcSeconds,'TT-UTC',-200,1000);\n else if(ms>=TS_LEAPS[0][0]){offset=32.184+TS_LEAPS.filter(r=>r[0]<=ms).at(-1)[1];if(ms>=Date.UTC(2027,0,1))warnings.push('future-TAI-UTC-assumed-last-confirmed');}\n else if(ms>=TS_DRIFTS[0][0]){const r=TS_DRIFTS.filter(r=>r[0]<=ms).at(-1);offset=32.184+r[1]+(jdUtc-2400000.5-r[2])*r[3];}\n else{offset=historicDeltaT(year+(date.getUTCMonth()+.5)/12)+dut1;warnings.push('pre1961-proleptic-time-with-estimated-deltaT');}\n return {jdUtc,jdUt1:jdUtc+dut1/86400,jdTt:jdUtc+offset/86400,dut1Seconds:dut1,ttMinusUtcSeconds:offset,warnings};\n}\n\n// real-sky/core/src/astronomy.mjs\n\n/** Astronomical geometry. Degrees externally; vectors and rotations in radians internally.\n * Sources/accuracy: docs/RESEARCH.md. This is a bounded widget model, not a SOFA replacement.\n * No Date.now(), local civil-time parser, random position, or browser geolocation is used here.\n */\nconst DEG=Math.PI/180, ARCSEC=DEG/3600, MAS=ARCSEC/1000;\nconst clamp=(x,lo=-1,hi=1)=>Math.max(lo,Math.min(hi,x));\nconst wrapDeg=x=>((x%360)+360)%360;\nfunction finite(x,name,min=-Infinity,max=Infinity){if(typeof x!=='number'||!Number.isFinite(x)||x<min||x>max)throw new RangeError(`${name} must be finite in [${min}, ${max}]`);return x;}\nconst dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];\nfunction unit(v){if(!Array.isArray(v)||v.length!==3||!v.every(Number.isFinite))throw new TypeError('finite 3-vector required');const n=Math.hypot(...v);if(n===0)throw new RangeError('zero direction');return v.map(x=>x/n);}\nfunction radecVector(raDeg,decDeg){finite(raDeg,'RA');finite(decDeg,'declination',-90,90);const r=raDeg*DEG,d=decDeg*DEG;return [Math.cos(d)*Math.cos(r),Math.cos(d)*Math.sin(r),Math.sin(d)];}\nfunction vectorRaDec(v){const u=unit(v);return {raDeg:wrapDeg(Math.atan2(u[1],u[0])/DEG),decDeg:Math.asin(clamp(u[2]))/DEG};}\nfunction julianDate(utc){const ms=utc instanceof Date?utc.getTime():utc;finite(ms,'UTC milliseconds',-8640000000000000,8640000000000000);return ms/86400000+2440587.5;}\nconst julianYear=jd=>2000+(finite(jd,'Julian day')-2451545)/365.25;\nfunction gmstDeg(jdUt1){const d=finite(jdUt1,'UT1 Julian day')-2451545,T=d/36525;return wrapDeg(280.46061837+360.98564736629*d+.000387933*T*T-T*T*T/38710000);}\nconst rz=(v,a)=>[v[0]*Math.cos(a)-v[1]*Math.sin(a),v[0]*Math.sin(a)+v[1]*Math.cos(a),v[2]];\nconst ry=(v,a)=>[v[0]*Math.cos(a)+v[2]*Math.sin(a),v[1],-v[0]*Math.sin(a)+v[2]*Math.cos(a)];\nconst rx=(v,a)=>[v[0],v[1]*Math.cos(a)-v[2]*Math.sin(a),v[1]*Math.sin(a)+v[2]*Math.cos(a)];\n/** IAU 1976 precession from mean equinox J2000 to mean equinox of date. */\nfunction precessJ2000(v,jdTt){const t=(finite(jdTt,'TT Julian day')-2451545)/36525;\n const zeta=(2306.2181*t+.30188*t*t+.017998*t*t*t)*ARCSEC;\n const z=(2306.2181*t+1.09468*t*t+.018203*t*t*t)*ARCSEC;\n const theta=(2004.3109*t-.42665*t*t-.041833*t*t*t)*ARCSEC;\n return rz(ry(rz(unit(v),zeta),-theta),z);\n}\n/** Four dominant nutation terms: an explicitly truncated model, NOT IAU 2000A. */\nfunction nutation(jdTt){const t=(jdTt-2451545)/36525;\n const O=(125.04452-1934.136261*t)*DEG,L=(280.4665+36000.7698*t)*DEG,M=(218.3165+481267.8813*t)*DEG;\n const dpsi=(-17.20*Math.sin(O)-1.32*Math.sin(2*L)-.23*Math.sin(2*M)+.21*Math.sin(2*O))*ARCSEC;\n const deps=(9.20*Math.cos(O)+.57*Math.cos(2*L)+.10*Math.cos(2*M)-.09*Math.cos(2*O))*ARCSEC;\n const eps=(23.439291111-.013004167*t-.000000164*t*t+.000000504*t*t*t)*DEG;\n return {dpsi,deps,eps};\n}\nfunction nutate(v,jdTt){const n=nutation(jdTt);return rx(rz(rx(unit(v),-n.eps),n.dpsi),n.eps+n.deps);}\n/** muAlphaStar, NOT dRA/dt. Missing motion remains flagged by observeStar. */\nfunction propagateJ2000(star,jyear){\n const u=radecVector(star.raDeg,star.decDeg),dt=finite(jyear,'Julian year')-finite(star.epochJyear??2000,'catalogue epoch');\n const ra=star.raDeg*DEG,dec=star.decDeg*DEG;\n const eRa=[-Math.sin(ra),Math.cos(ra),0],eDec=[-Math.cos(ra)*Math.sin(dec),-Math.sin(ra)*Math.sin(dec),Math.cos(dec)];\n const p=star.pmRaCosDecMasYr,q=star.pmDecMasYr;\n if(p==null||q==null)return u; // explicit constant-direction assumption; NOT a measured zero\n finite(p,'muAlphaStar');finite(q,'muDelta');\n const tangent=u.map((_,i)=>(p*eRa[i]+q*eDec[i])*MAS);\n // Perspective acceleration is meaningful only with a measured positive distance and RV.\n if(star.distancePc!=null&&star.radialVelocityKmS!=null){const dist=finite(star.distancePc,'distance pc',Number.MIN_VALUE)*206264.806247096;\n  const rv=finite(star.radialVelocityKmS,'radial velocity')*31557600/149597870.7;\n  return unit(u.map((x,i)=>x*dist+dt*(tangent[i]*dist+rv*x)));\n }\n return unit(u.map((x,i)=>x+dt*tangent[i]));\n}\n/** Special-relativistic aberration. Both direction and observer velocity/c use J2000 axes. */\nfunction aberrate(v,observerVelocityOverC){const u=unit(v),b=checkedVector(observerVelocityOverC,'observer velocity/c',.01);const bm1=Math.sqrt(1-dot(b,b)),ub=dot(u,b),w=1+ub/(1+bm1);return unit(u.map((x,i)=>bm1*x+w*b[i]));}\nfunction checkedVector(v,name,maxNorm){if(!Array.isArray(v)||v.length!==3||!v.every(Number.isFinite)||Math.hypot(...v)>maxNorm)throw new RangeError('Invalid '+name);return [...v];}\nconst applyColumns=(columns,v)=>v.map((_,i)=>columns[0][i]*v[0]+columns[1][i]*v[1]+columns[2][i]*v[2]);\nconst inverseColumns=(columns,v)=>columns.map(c=>dot(c,v));\nconst PC_AU=206264.806247096,AU_KM=149597870.7,C_AU_DAY=173.1446326846693;\nfunction precessionColumns(jdTt){return [[1,0,0],[0,1,0],[0,0,1]].map(v=>precessJ2000(v,jdTt));}\n/** Low-order heliocentric Earth, not a DE barycentric ephemeris. USNO solar formula;\n * undo the approximate solar aberration before inverting to geometric Earth position.\n * Position and central-difference velocity are both mean J2000 equatorial AU, AU/day. */\nfunction earthPosition(jdTt){\n const d=jdTt-2451545,g=wrapDeg(357.529+.98560028*d)*DEG,q=wrapDeg(280.459+.98564736*d);\n const r=1.00014-.01671*Math.cos(g)-.00014*Math.cos(2*g);\n const l=(q+1.915*Math.sin(g)+.020*Math.sin(2*g)+20.4898/(3600*r))*DEG,e=nutation(jdTt).eps;\n return inverseColumns(precessionColumns(jdTt),[-r*Math.cos(l),-r*Math.sin(l)*Math.cos(e),-r*Math.sin(l)*Math.sin(e)]);\n}\nfunction earthState(jdTt){finite(jdTt,'TT Julian day');const step=.02,a=earthPosition(jdTt-step),b=earthPosition(jdTt+step);return {positionAu:earthPosition(jdTt),velocityAuDay:a.map((v,i)=>(b[i]-v)/(2*step)),frame:'mean-J2000',origin:'heliocentric',model:'USNO-low-order-with-central-difference'};}\nfunction spaceState(star,jyear){\n const u=radecVector(star.raDeg,star.decDeg),dt=jyear-finite(star.epochJyear??2000,'epoch'),distance=star.distancePc==null?null:finite(star.distancePc,'distancePc',Number.MIN_VALUE)*PC_AU;\n if(distance==null)return {direction:propagateJ2000(star,jyear),positionAu:null};\n const ra=star.raDeg*DEG,de=star.decDeg*DEG,hasMotion=star.pmRaCosDecMasYr!=null&&star.pmDecMasYr!=null;\n const p=hasMotion?finite(star.pmRaCosDecMasYr,'muAlphaStar')*MAS:0,q=hasMotion?finite(star.pmDecMasYr,'muDelta')*MAS:0;\n const er=[-Math.sin(ra),Math.cos(ra),0],ed=[-Math.cos(ra)*Math.sin(de),-Math.sin(ra)*Math.sin(de),Math.cos(de)];\n const rv=star.radialVelocityKmS==null?0:finite(star.radialVelocityKmS,'RV')*31557600/AU_KM;\n const positionAu=u.map((x,i)=>x*distance+dt*(distance*(p*er[i]+q*ed[i])+rv*x));return {direction:unit(positionAu),positionAu};\n}\nfunction equatorialToHorizontal(raDeg,decDeg,lstDeg,latDeg){\n finite(raDeg,'RA');finite(decDeg,'declination',-90,90);finite(lstDeg,'sidereal angle');finite(latDeg,'latitude',-90,90);\n const H=(lstDeg-raDeg)*DEG,d=decDeg*DEG,p=latDeg*DEG;\n const east=-Math.cos(d)*Math.sin(H),north=Math.sin(d)*Math.cos(p)-Math.cos(d)*Math.cos(H)*Math.sin(p),up=Math.sin(d)*Math.sin(p)+Math.cos(d)*Math.cos(H)*Math.cos(p);\n return {altDeg:Math.asin(clamp(up))/DEG,azDeg:Math.hypot(east,north)<1e-14?0:wrapDeg(Math.atan2(east,north)/DEG),enu:[east,north,up]};\n}\n/** Saemundsson standard-atmosphere refraction; local anomalies/ducting are not modelled. */\nfunction refractionDeg(altDeg,pressureHpa=0,temperatureC=10){\n finite(altDeg,'geometric altitude',-1,90);finite(pressureHpa,'pressure',0,1100);finite(temperatureC,'temperature',-90,70);\n if(pressureHpa===0||altDeg>=89.9)return 0;\n return Math.max(0,(1.02/Math.tan((altDeg+10.3/(altDeg+5.11))*DEG))/60*(pressureHpa/1010)*(283/(273+temperatureC)));\n}\n/** Immutable shared frame. UT1 controls Earth rotation; TT controls ephemeris/axes.\n * Missing DUT1/polar motion cannot be promoted to measured precision. Explicit meanOnly\n * is a geometric mean-axes test profile: aberration/parallax default off in that profile. */\nfunction observationFrame(observer){\n for(const k of [\"meanOnly\",\"parallax\",\"aberration\"])if(observer[k]!=null&&typeof observer[k]!==\"boolean\")throw new TypeError(k+\" must be a boolean\");\n const t=timeScales(observer),lat=finite(observer.latDeg,'latitude',-90,90),lon=finite(observer.lonDeg,'longitude',-180,180);\n const pressure=finite(observer.pressureHpa??0,'pressure',0,1100),temp=finite(observer.temperatureC??10,'temperature',-90,70),height=finite(observer.heightM??0,'height metres',-500,100000);\n const n=nutation(t.jdTt),mean=observer.meanOnly===true,warnings=[...t.warnings,'polar-motion-not-applied','solar-gravitational-deflection-not-applied'];\n const gast=wrapDeg(gmstDeg(t.jdUt1)+(mean?0:n.dpsi*Math.cos(n.eps+n.deps)/DEG)),lst=wrapDeg(gast+lon);\n const rotation=precessionColumns(t.jdTt).map(v=>mean?v:nutate(v,t.jdTt));\n const parallax=observer.parallax??!mean,aberration=observer.aberration??!mean;let earth;\n if(observer.earthBarycentric!=null){const e=observer.earthBarycentric;finite(e.jdTt,'external ephemeris timestamp');if(Math.abs(e.jdTt-t.jdTt)>1e-7||!['ICRS','mean-J2000'].includes(e.frame))throw new RangeError('External Earth state must match current TT and declared J2000/ICRS axes');earth={positionAu:checkedVector(e.positionAu,'barycentric position',2),velocityAuDay:checkedVector(e.velocityAuDay,'barycentric velocity',.03)};if(e.frame==='ICRS')warnings.push('ICRS-frame-bias-not-applied');}\n else {earth=earthState(t.jdTt);warnings.push('heliocentric-earth-approximation');}\n const la=lat*DEG,theta=lst*DEG,e2=6.6943799901413165e-3,N=6378137/Math.sqrt(1-e2*Math.sin(la)**2);\n const siteDate=[(N+height)*Math.cos(la)*Math.cos(theta),(N+height)*Math.cos(la)*Math.sin(theta),(N*(1-e2)+height)*Math.sin(la)].map(x=>x/(AU_KM*1000));\n const site=inverseColumns(rotation,siteDate),diurnal=inverseColumns(rotation,[-siteDate[1],siteDate[0],0]).map(x=>x*2*Math.PI*1.00273781191135448);\n const positionAu=earth.positionAu.map((x,i)=>x+site[i]);\n const velocityOverC=observer.velocityOverC!=null?checkedVector(observer.velocityOverC,'observer velocity/c',.01):earth.velocityAuDay.map((x,i)=>(x+diurnal[i])/C_AU_DAY);\n if(observer.velocityOverC!=null)warnings.push('explicit-total-observer-velocity-no-auto-diurnal-addition');\n const snapshot=Object.freeze({utcMs:observer.utcMs,latDeg:lat,lonDeg:lon,pressureHpa:pressure,temperatureC:temp,heightM:height});\n return Object.freeze({observer:snapshot,...t,jyear:julianYear(t.jdTt),latDeg:lat,lstDeg:lst,meanOnly:mean,rotation:Object.freeze(rotation.map(Object.freeze)),positionAu:Object.freeze(positionAu),velocityOverC:Object.freeze(velocityOverC),parallax:!!parallax,aberration:!!aberration,warnings:Object.freeze(warnings)});\n}\nfunction observeStar(star,observerOrFrame){\n const f=observerOrFrame.rotation?observerOrFrame:observationFrame(observerOrFrame),o=f.observer,state=spaceState(star,f.jyear),warnings=[...f.warnings];\n const parallaxApplied=f.parallax&&state.positionAu!==null;let v=parallaxApplied?unit(state.positionAu.map((x,i)=>x-f.positionAu[i])):state.direction;\n if(f.parallax&&!parallaxApplied)warnings.push('distance-unavailable-parallax-not-applied');\n if(star.radialVelocityKmS==null&&star.distancePc!=null)warnings.push('radial-velocity-unavailable-no-radial-perspective');\n if(f.aberration)v=aberrate(v,f.velocityOverC);v=applyColumns(f.rotation,v);\n const eq=vectorRaDec(v),h=equatorialToHorizontal(eq.raDeg,eq.decDeg,f.lstDeg,f.latDeg);\n let ref=0;if(h.altDeg>=-1&&o.pressureHpa>0)ref=refractionDeg(h.altDeg,o.pressureHpa,o.temperatureC);const app=h.altDeg+ref,az=h.azDeg*DEG,al=app*DEG;\n if(star.pmRaCosDecMasYr==null||star.pmDecMasYr==null)warnings.push('proper-motion-unavailable');\n return {...h,enuGeometric:h.enu,enu:[Math.cos(al)*Math.sin(az),Math.cos(al)*Math.cos(az),Math.sin(al)],geometricAltDeg:h.altDeg,altDeg:app,refractionDeg:ref,aboveHorizon:app>=0,aboveGeometricHorizon:h.altDeg>=0,parallaxApplied,aberrationApplied:f.aberration,raOfDateDeg:eq.raDeg,decOfDateDeg:eq.decDeg,utcMs:o.utcMs,warnings};\n}\nfunction angularSeparation(a,b){a=unit(a);b=unit(b);return Math.atan2(Math.hypot(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]),clamp(dot(unit(a),unit(b))))/DEG;}\nfunction slerp(a,b,t){finite(t,'interpolation',0,1);a=unit(a);b=unit(b);const c=clamp(dot(a,b));if(c>1-1e-12)return unit(a.map((v,i)=>v*(1-t)+b[i]*t));if(c< -1+1e-9)throw new RangeError('antipodal annotation endpoints are ambiguous');const w=Math.acos(c),s=Math.sin(w);return unit(a.map((v,i)=>(v*Math.sin((1-t)*w)+b[i]*Math.sin(t*w))/s));}\n\n// real-sky/core/src/projection.mjs\n\n/** All-sky map: north up, east LEFT, zenith centred. This is a sky chart seen from inside.\n * Set eastLeft:false only for an explicitly labelled ENU diagram, not silently.\n */\nfunction projectAllSky(h,{width=325,height=325,eastLeft=true,padding=4}={}){\n finite(width,'width',1);finite(height,'height',1);finite(h.altDeg,'altitude',-90,90);finite(h.azDeg,'azimuth');\n finite(padding,'padding',0,Math.min(width,height)/2-Number.EPSILON);const R=Math.min(width,height)/2-padding;if(R<=0)throw new RangeError('No all-sky radius');const r=(90-h.altDeg)/90*R,a=h.azDeg*DEG;\n return {x:width/2+(eastLeft?-1:1)*r*Math.sin(a),y:height/2-r*Math.cos(a),visible:h.altDeg>=0};\n}\nfunction unprojectAllSky(x,y,{width=325,height=325,eastLeft=true,padding=4}={}){\n finite(width,'width',1);finite(height,'height',1);finite(x,'x');finite(y,'y');finite(padding,'padding',0,Math.min(width,height)/2-Number.EPSILON);const R=Math.min(width,height)/2-padding;if(R<=0)throw new RangeError('No all-sky radius');const dx=(x-width/2)*(eastLeft?-1:1),dy=height/2-y,r=Math.hypot(dx,dy);\n return {altDeg:90-r/R*90,azDeg:r<1e-12?0:wrapDeg(Math.atan2(dx,dy)/DEG)};\n}\n/** Exact legacy PR38 geometry, expressed in north-zero/east-positive azimuth.\n * It is an anisotropically compressed crop, NOT a camera with a physical field of view.\n */\nfunction projectWidgetDome(h){finite(h.altDeg,'altitude',-90,90);finite(h.azDeg,'azimuth');const r=(90-h.altDeg)/90*270,a=h.azDeg*DEG;\n const x=162-r*Math.sin(a),y=-30+.8*r*Math.cos(a);\n return {x,y,visible:h.altDeg>=0&&x>=-24&&x<=349&&y>=-24&&y<=250};\n}\n/** Perspective camera. True azimuth north0/east90; positive roll rotates camera right\n * towards the unrolled up axis. Altitude/azimuth always describe one rigid camera. */\nfunction cameraBasis(c={}){\n const width=finite(c.width??325,'width',1,16384),height=finite(c.height??530,'height',1,16384),az=finite(c.azDeg??180,'camera azimuth'),alt=finite(c.altDeg??35,'camera altitude',-90,90),fov=finite(c.fovYDeg??90,'vertical FOV',1,170),roll=finite(c.rollDeg??0,'camera roll')*DEG;\n const a=az*DEG,e=alt*DEG,fw=[Math.cos(e)*Math.sin(a),Math.cos(e)*Math.cos(a),Math.sin(e)],rt=[Math.cos(a),-Math.sin(a),0],up=[-Math.sin(e)*Math.sin(a),-Math.sin(e)*Math.cos(a),Math.cos(e)];\n return {width,height,f:height/(2*Math.tan(fov*DEG/2)),fw,rt:rt.map((v,i)=>v*Math.cos(roll)+up[i]*Math.sin(roll)),up:up.map((v,i)=>v*Math.cos(roll)-rt[i]*Math.sin(roll)),fovXDeg:2*Math.atan(width/height*Math.tan(fov*DEG/2))/DEG};\n}\nfunction cameraGeometry(c={}){const b=cameraBasis(c);return {width:b.width,height:b.height,focalPixels:b.f,fovXDeg:b.fovXDeg};}\nfunction projectPerspective(h,c={}){\n finite(h.altDeg,'altitude',-90,90);finite(h.azDeg,'azimuth');const b=cameraBasis(c),ha=h.azDeg*DEG,he=h.altDeg*DEG,v=[Math.cos(he)*Math.sin(ha),Math.cos(he)*Math.cos(ha),Math.sin(he)];\n const d=(u,w)=>u.reduce((s,x,i)=>s+x*w[i],0),z=d(v,b.fw);if(z<=0)return null;\n const x=b.width/2+b.f*d(v,b.rt)/z,y=b.height/2-b.f*d(v,b.up)/z,inFrame=x>=0&&x<=b.width&&y>=0&&y<=b.height;\n return {x,y,inFrame,visible:h.altDeg>=0&&inFrame};\n}\nfunction unprojectPerspective(x,y,c={}){\n finite(x,'x');finite(y,'y');const b=cameraBasis(c),u=(x-b.width/2)/b.f,w=(b.height/2-y)/b.f,v=b.fw.map((a,i)=>a+u*b.rt[i]+w*b.up[i]),len=Math.hypot(...v),r=Math.hypot(v[0],v[1]);\n return {altDeg:Math.atan2(v[2],r)/DEG,azDeg:r<1e-14?0:wrapDeg(Math.atan2(v[0],v[1])/DEG),enu:v.map(a=>a/len)};\n}\n\n/** CP7.5: hoist rigid camera constants once per render, NOT once per UTC/location.\n * The per-ray arithmetic remains identical to the public reference functions.\n * No approximate ray grid, frame cache, or new celestial coordinate system.\n */\nfunction prepareInverseProjection(view={}){\n const c={...view},type=c.type??'camera';\n if(type==='camera'){\n  const b=cameraBasis(c);\n  return (x,y)=>{finite(x,'x');finite(y,'y');const u=(x-b.width/2)/b.f,w=(b.height/2-y)/b.f,v=b.fw.map((a,i)=>a+u*b.rt[i]+w*b.up[i]),len=Math.hypot(...v),r=Math.hypot(v[0],v[1]);\n   return {altDeg:Math.atan2(v[2],r)/DEG,azDeg:r<1e-14?0:wrapDeg(Math.atan2(v[0],v[1])/DEG),enu:v.map(a=>a/len)};};\n }\n if(type==='allsky'){\n  const width=finite(c.width??325,'width',1),height=finite(c.height??325,'height',1),padding=finite(c.padding??4,'padding',0,Math.min(width,height)/2-Number.EPSILON),eastLeft=c.eastLeft??true,R=Math.min(width,height)/2-padding;\n  if(R<=0)throw new RangeError('No all-sky radius');\n  return (x,y)=>{finite(x,'x');finite(y,'y');const dx=(x-width/2)*(eastLeft?-1:1),dy=height/2-y,r=Math.hypot(dx,dy);return {altDeg:90-r/R*90,azDeg:r<1e-12?0:wrapDeg(Math.atan2(dx,dy)/DEG)};};\n }\n throw new RangeError('Prepared projection must be camera or allsky');\n}\n\n// real-sky/core/src/photometry.mjs\n/** Relative stellar photometry and spectral transport. Not absolute display calibration.\n * V magnitude -> exact relative V-band flux; using it as photopic Y is an explicit\n * passband approximation. B-V -> blackbody colour proxy is NOT a measured SED or Teff.\n * See docs/RESEARCH.md and provenance/sources.json for methods and limitations.\n */\n\nconst luminance=rgb=>.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];\nfunction magnitudeFlux(m){return 10**(-.4*finite(m,'V magnitude',-30,40));}\nfunction colourTemperature(bv){if(bv==null)return null;finite(bv,'B-V',-.5,5);\n // Values outside the useful blackbody-colour interval are not extrapolated.\n if(bv<-.4||bv>2.0)return null;\n return 4600*(1/(.92*bv+1.7)+1/(.92*bv+.62));\n}\n/** Wyman/Sloan/Shirley 2013, equation 4/table 1, 1931 2-degree observer. */\nfunction cie1931(w){finite(w,'wavelength nm',360,830);\n const g=(c,a,b)=>Math.exp(-.5*((w-c)*(w<c?a:b))**2);\n return [.362*g(442,.0624,.0374)+1.056*g(599.8,.0264,.0323)-.065*g(501.1,.049,.0382),.821*g(568.8,.0213,.0247)+.286*g(530.9,.0613,.0322),1.217*g(437,.0845,.0278)+.681*g(459,.0385,.0725)];\n}\nfunction airmass(apparentAltDeg){finite(apparentAltDeg,'apparent altitude',0,90);return 1/(Math.sin(apparentAltDeg*DEG)+.50572*(apparentAltDeg+6.07995)**-1.6364);}\nfunction transmission(X,tau){finite(X,'airmass',0,1000);finite(tau,'optical depth',0,1000);return Math.exp(-X*tau);}\nfunction opticalDepth(w,{rayleighTau550=.10,aerosolTau550=.06,angstromExponent=1.3,greyTau=0}={}){\n finite(w,'wavelength',360,830);finite(rayleighTau550,'Rayleigh optical depth',0,100);finite(aerosolTau550,'aerosol optical depth',0,100);finite(angstromExponent,'Angstrom exponent',0,4);finite(greyTau,'grey optical depth',0,100);\n return rayleighTau550*(550/w)**4.08+aerosolTau550*(550/w)**angstromExponent+greyTau;\n}\nfunction xyzToLinearRgb([x,y,z]){return [3.2404542*x-1.5371385*y-.4985314*z,-.969266*x+1.8760108*y+.041556*z,.0556434*x-.2040259*y+1.0572252*z];}\nconst bins=Array.from({length:95},(_,i)=>{const w=360+i*5;return {w,xyz:cie1931(w),weight:i===0||i===94?2.5:5};});\nconst spectra=new Map();\n/** A normalised shape, integral against ybar = 1 before terrestrial extinction. */\nfunction spectrumForColour(bv){const key=bv==null?'unknown':String(bv);if(spectra.has(key))return spectra.get(key);\n const T=colourTemperature(bv),fallback=T==null;\n // An unknown source gets a declared neutral-display proxy, not an invented catalogue colour.\n const temperature=T??6500,base=bins.map(({w})=>1/(w**5*Math.expm1(1.438776877e7/(w*temperature))));\n const Y=base.reduce((a,s,i)=>a+s*bins[i].xyz[1]*bins[i].weight,0);\n const value={samples:base.map(x=>x/Y),temperatureProxyK:T,fallback};\n if(spectra.size<2048)spectra.set(key,value);return value;\n}\n/** Caller may supply a measured 95-bin SED, normalised to Y=1 on the same 360..830/5nm grid.\n * This optional route is not used by the bundled catalogue and must carry its own provenance.\n */\nfunction starRgbFlux(star,altDeg,atmosphere={}){\n if(altDeg<0)return {rgb:[0,0,0],colourFallback:star.bv==null,model:'below-horizon'};\n const X=airmass(altDeg),cloud=finite(atmosphere.cloudTransmission??1,'cloud transmission',0,1);\n const proxy=spectrumForColour(star.bv),samples=star.sedYNormalised??proxy.samples;\n if(!Array.isArray(samples)||samples.length!==bins.length||!samples.every(x=>Number.isFinite(x)&&x>=0))throw new TypeError('SED must be 95 finite non-negative samples');\n const xyz=[0,0,0];for(let i=0;i<bins.length;i++){const b=bins[i],p=samples[i]*transmission(X,opticalDepth(b.w,atmosphere))*b.weight;for(let k=0;k<3;k++)xyz[k]+=p*b.xyz[k];}\n let rgb=xyzToLinearRgb(xyz);\n // Gamut mapping: clip negative channels, rescale to retain the XYZ-Y flux, never re-normalise extinction.\n const before=xyz[1];rgb=rgb.map(x=>Math.max(0,x));const y=luminance(rgb);if(y>0)rgb=rgb.map(x=>x*before/y);\n const scale=magnitudeFlux(star.vmag)*cloud;\n return {rgb:rgb.map(x=>x*scale),colourFallback:!star.sedYNormalised&&proxy.fallback,temperatureProxyK:proxy.temperatureProxyK,\n model:star.sedYNormalised?'provided-SED-relative-Y':'B-V-blackbody-proxy; V-as-Y approximation'};\n}\nfunction linearToSrgb(x){finite(x,'linear channel',0);return x<=.0031308?12.92*x:1.055*x**(1/2.4)-.055;}\nfunction srgbToLinear(x){finite(x,'sRGB channel',0);return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;}\n/** Zero-mean, bounded, deterministic display surrogate; not a forecast of real turbulence.\n * Never changes star position, diameter, catalogue magnitude or identity. Default amplitude=0.\n */\nfunction scintillation(hip,tSeconds,altDeg,amplitude=0){finite(amplitude,'scintillation amplitude',0,.3);if(amplitude===0)return 1;\n const phase=(hip*.61803398875)%1*2*Math.PI,altFactor=.25+.75*(1-Math.sin(clamp(altDeg,0,90)*DEG));\n return 1+amplitude*altFactor*(.6*Math.sin(2*Math.PI*.73*tSeconds+phase)+.4*Math.sin(2*Math.PI*1.17*tSeconds+phase*2.13));\n}\n\n// real-sky/core/src/spectral-tables.mjs\n// Generated; see vendor/spectral and provenance/cp5-spectral-acquisition.json.\nconst SPECTRAL_TABLES={\"schema\":\"salah-spectral-tables/1\",\"wavelengthNm\":[360,365,370,375,380,385,390,395,400,405,410,415,420,425,430,435,440,445,450,455,460,465,470,475,480,485,490,495,500,505,510,515,520,525,530,535,540,545,550,555,560,565,570,575,580,585,590,595,600,605,610,615,620,625,630,635,640,645,650,655,660,665,670,675,680,685,690,695,700,705,710,715,720,725,730,735,740,745,750,755,760,765,770,775,780,785,790,795,800,805,810,815,820,825,830],\"weightsNm\":[2.5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,2.5],\"cieXYZ\":[[0.0001299,3.917e-06,0.0006061],[0.0002321,6.965e-06,0.001086],[0.0004149,1.239e-05,0.001946],[0.0007416,2.202e-05,0.003486],[0.001368,3.9e-05,0.006450001],[0.002236,6.4e-05,0.01054999],[0.004243,0.00012,0.02005001],[0.00765,0.000217,0.03621],[0.01431,0.000396,0.06785001],[0.02319,0.00064,0.1102],[0.04351,0.00121,0.2074],[0.07763,0.00218,0.3713],[0.13438,0.004,0.6456],[0.21477,0.0073,1.0390501],[0.2839,0.0116,1.3856],[0.3285,0.01684,1.62296],[0.34828,0.023,1.74706],[0.34806,0.0298,1.7826],[0.3362,0.038,1.77211],[0.3187,0.048,1.7441],[0.2908,0.06,1.6692],[0.2511,0.0739,1.5281],[0.19536,0.09098,1.28764],[0.1421,0.1126,1.0419],[0.09564,0.13902,0.8129501],[0.05795001,0.1693,0.6162],[0.03201,0.20802,0.46518],[0.0147,0.2586,0.3533],[0.0049,0.323,0.272],[0.0024,0.4073,0.2123],[0.0093,0.503,0.1582],[0.0291,0.6082,0.1117],[0.06327,0.71,0.07824999],[0.1096,0.7932,0.05725001],[0.1655,0.862,0.04216],[0.2257499,0.9148501,0.02984],[0.2904,0.954,0.0203],[0.3597,0.9803,0.0134],[0.4334499,0.9949501,0.008749999],[0.5120501,1.0,0.005749999],[0.5945,0.995,0.0039],[0.6784,0.9786,0.002749999],[0.7621,0.952,0.0021],[0.8425,0.9154,0.0018],[0.9163,0.87,0.001650001],[0.9786,0.8163,0.0014],[1.0263,0.757,0.0011],[1.0567,0.6949,0.001],[1.0622,0.631,0.0008],[1.0456,0.5668,0.0006],[1.0026,0.503,0.00034],[0.9384,0.4412,0.00024],[0.8544499,0.381,0.00019],[0.7514,0.321,0.0001],[0.6424,0.265,4.999999e-05],[0.5419,0.217,3e-05],[0.4479,0.175,2e-05],[0.3608,0.1382,1e-05],[0.2835,0.107,0.0],[0.2187,0.0816,0.0],[0.1649,0.061,0.0],[0.1212,0.04458,0.0],[0.0874,0.032,0.0],[0.0636,0.0232,0.0],[0.04677,0.017,0.0],[0.0329,0.01192,0.0],[0.0227,0.00821,0.0],[0.01584,0.005723,0.0],[0.01135916,0.004102,0.0],[0.008110916,0.002929,0.0],[0.005790346,0.002091,0.0],[0.004109457,0.001484,0.0],[0.002899327,0.001047,0.0],[0.00204919,0.00074,0.0],[0.001439971,0.00052,0.0],[0.0009999493,0.0003611,0.0],[0.0006900786,0.0002492,0.0],[0.0004760213,0.0001719,0.0],[0.0003323011,0.00012,0.0],[0.0002348261,8.48e-05,0.0],[0.0001661505,6e-05,0.0],[0.000117413,4.24e-05,0.0],[8.307527e-05,3e-05,0.0],[5.870652e-05,2.12e-05,0.0],[4.150994e-05,1.499e-05,0.0],[2.935326e-05,1.06e-05,0.0],[2.067383e-05,7.4657e-06,0.0],[1.455977e-05,5.2578e-06,0.0],[1.025398e-05,3.7029e-06,0.0],[7.221456e-06,2.6078e-06,0.0],[5.085868e-06,1.8366e-06,0.0],[3.581652e-06,1.2934e-06,0.0],[2.522525e-06,9.1093e-07,0.0],[1.776509e-06,6.4153e-07,0.0],[1.251141e-06,4.5181e-07,0.0]],\"passbands\":{\"B\":[0.0,0.015,0.03,0.082,0.134,0.3505,0.567,0.7435,0.92,0.9490000000000001,0.978,0.989,1.0,0.989,0.978,0.9565,0.935,0.894,0.853,0.7965,0.74,0.69,0.64,0.5880000000000001,0.536,0.48,0.424,0.3745,0.325,0.28,0.235,0.1925,0.15,0.1225,0.095,0.069,0.043,0.026,0.009,0.0045,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],\"V\":[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.015,0.03,0.0965,0.163,0.3105,0.458,0.619,0.78,0.8734999999999999,0.967,0.9835,1.0,0.9864999999999999,0.973,0.9355,0.898,0.845,0.792,0.738,0.684,0.629,0.574,0.5175,0.461,0.41000000000000003,0.359,0.3145,0.27,0.2335,0.197,0.166,0.135,0.10800000000000001,0.081,0.063,0.045,0.035,0.025,0.021,0.017,0.015,0.013,0.011,0.009,0.0045,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]},\"passbandConvention\":\"photon-weighted response integral of f_lambda * wavelength * response; constant hc cancels\",\"vegaZeroColour\":0,\"standards\":[{\"id\":\"IRAF-HR7001\",\"hip\":91262,\"hr\":7001,\"templateClass\":\"A0V\",\"catalogueBV\":-0.001,\"spectralType\":\"A0Vvar\",\"kind\":\"observed-spectrophotometric-shape\",\"source\":\"vendor/spectral/hr7001.dat\",\"resolution\":\"29 sparse continuum bandpasses; log-flux interpolation on 5 nm grid is reconstruction, not 95 measured bins\",\"samples\":[1.7511758248027455e-05,1.815819472389263e-05,1.8365527181365837e-05,2.4303141873099898e-05,3.292090241196057e-05,4.4594473474947244e-05,4.82281483397661e-05,4.857794715348742e-05,4.893028305839504e-05,4.8750009842424014e-05,4.722576765610432e-05,4.574918318821525e-05,4.4323675308420595e-05,4.294503537803981e-05,4.172727600006642e-05,4.05568070131552e-05,3.9419170211343206e-05,3.8313444636971214e-05,3.693683153273581e-05,3.5497130342632564e-05,3.43157810423795e-05,3.3266150494018265e-05,3.224862541592712e-05,3.12622237852193e-05,3.0305198296958672e-05,2.9375671220520665e-05,2.8474654783655558e-05,2.760127450234953e-05,2.675468271493639e-05,2.5995862352223207e-05,2.525856376754798e-05,2.4542176556982982e-05,2.3846107628968968e-05,2.3169780713299318e-05,2.255303698704301e-05,2.1966543906223672e-05,2.1395302613181188e-05,2.08389164842587e-05,2.0296999210021473e-05,1.9769174527034782e-05,1.9233771236468064e-05,1.8710043399519125e-05,1.8200576460436913e-05,1.7704982100721655e-05,1.7222882575629562e-05,1.6755070027635462e-05,1.6304477526097446e-05,1.5866002765763042e-05,1.543931986537273e-05,1.5024111707560859e-05,1.4677555315982021e-05,1.4346668048308571e-05,1.4023240223406825e-05,1.3707103677397741e-05,1.339809403744822e-05,1.3096050636306598e-05,1.2800816428765067e-05,1.251634436869122e-05,1.2248524975088798e-05,1.1986436266539215e-05,1.1729955620290125e-05,1.1478963037418448e-05,1.12333410866869e-05,1.0992974849601673e-05,1.075572554968895e-05,1.0515669933721518e-05,1.0280972087296556e-05,1.0051512431064296e-05,9.827174054550677e-06,9.607842656590924e-06,9.393406487093014e-06,9.181988828890803e-06,8.975329553737502e-06,8.773321564574919e-06,8.575860174781357e-06,8.382843053919688e-06,8.194170174706867e-06,8.00974376117654e-06,7.829468238008839e-06,7.65325018100013e-06,7.498288594991164e-06,7.346464642349789e-06,7.1977147928592506e-06,7.051976802650769e-06,6.918167631857956e-06,6.800130298838276e-06,6.684106911234177e-06,6.570063107237962e-06,6.457965111320917e-06,6.3477797242302415e-06,6.238807143133598e-06,6.129083132877339e-06,6.021288875881668e-06,5.915390432923649e-06,5.811354461680924e-06]},{\"id\":\"IRAF-HR3982\",\"hip\":49669,\"hr\":3982,\"templateClass\":\"B7V\",\"catalogueBV\":-0.087,\"spectralType\":\"B7V\",\"kind\":\"observed-spectrophotometric-shape\",\"source\":\"vendor/spectral/hr3982.dat\",\"resolution\":\"29 sparse continuum bandpasses; log-flux interpolation on 5 nm grid is reconstruction, not 95 measured bins\",\"samples\":[3.0026943133144153e-05,2.9613669655369702e-05,2.9830343324204946e-05,3.539118347028792e-05,4.2590426558368675e-05,5.1254133277194844e-05,5.351113333212724e-05,5.341640711439401e-05,5.3321848582444405e-05,5.270443505011586e-05,5.078803432869502e-05,4.894131639054611e-05,4.7184509076628306e-05,4.550207336730564e-05,4.4077209648811276e-05,4.2718283725174736e-05,4.1401254275490345e-05,4.012482960718002e-05,3.862699841166936e-05,3.708791436518579e-05,3.578693126018242e-05,3.4612148052858364e-05,3.3475929638200635e-05,3.237701004370961e-05,3.1304891398819874e-05,3.0247363212069362e-05,2.922555998125377e-05,2.8238274861494218e-05,2.7284341777018984e-05,2.6431701989300685e-05,2.5605707323298825e-05,2.4805525114948754e-05,2.403034872106319e-05,2.3279396706175968e-05,2.2610624877152276e-05,2.1981136992110674e-05,2.136917427497422e-05,2.077424881879934e-05,2.0195886300146e-05,1.9633625600908683e-05,1.9089396861544756e-05,1.856056907927228e-05,1.8046391252958654e-05,1.7546457539309003e-05,1.7060373337982348e-05,1.658768766464782e-05,1.612783672557582e-05,1.568073397000242e-05,1.524602598735743e-05,1.4823369164469222e-05,1.4461442408605057e-05,1.4114885431739026e-05,1.3776633417463939e-05,1.3446487343950053e-05,1.312425295876769e-05,1.2809740664592308e-05,1.2502765407648524e-05,1.2207675811135457e-05,1.193093018187255e-05,1.1660458322039714e-05,1.1396118006507822e-05,1.1137770234363632e-05,1.0885279155817538e-05,1.0638512000768148e-05,1.0396849924348232e-05,1.0158765716022708e-05,9.926133552370936e-06,9.698828583486561e-06,9.476728818482121e-06,9.259715060018583e-06,9.047670840334163e-06,8.833180454004017e-06,8.623774926157303e-06,8.419333711597434e-06,8.219739122856154e-06,8.024876262446262e-06,7.834632956720504e-06,7.648899691298137e-06,7.467569548022655e-06,7.290538143413823e-06,7.14435101625834e-06,7.001095178361015e-06,6.8607118526127915e-06,6.723143440481091e-06,6.590880944937177e-06,6.464968219684591e-06,6.341460941368891e-06,6.2203131561363234e-06,6.101479788039238e-06,5.9849166222645915e-06,5.8710426699674114e-06,5.761150069095259e-06,5.653314408430364e-06,5.547497186718046e-06,5.443660623359729e-06]}],\"rejectedStandards\":[{\"hr\":4534,\"hip\":57632,\"source\":\"vendor/spectral/hr4534.dat\",\"reason\":\"Unexplained red excursions at 7550 and 7780 A. Full source retained; no silent repair.\"}]};\n\n// real-sky/core/src/spectral.mjs\n/** CP5 relative spectral radiometry. The V passband, CIE observer and display encoding\n * are distinct. Spectra describe received extra-atmospheric light: NEVER divide by distance.\n * 5 nm integration and sparse IRAF references are not high-resolution spectral calibration.\n */\n\n\n\nconst SPECTRAL_GRID=SPECTRAL_TABLES.wavelengthNm;\nconst sfWeights=SPECTRAL_TABLES.weightsNm,sfXYZ=SPECTRAL_TABLES.cieXYZ,sfCache=new Map(),sfFitCache=new Map();\nfunction sfValidate(samples){if(!Array.isArray(samples)||samples.length!==95||!samples.every(x=>Number.isFinite(x)&&x>=0)||!samples.some(x=>x>0))throw new TypeError('Spectrum must have 95 non-negative finite samples with positive energy');return samples;}\nfunction passbandIntegral(samples,band='V'){\n sfValidate(samples);const b=SPECTRAL_TABLES.passbands[band];if(!b)throw new RangeError('Unknown passband');\n return samples.reduce((s,v,i)=>s+v*SPECTRAL_GRID[i]*b[i]*sfWeights[i],0);\n}\nfunction cieTableAt(w){finite(w,'wavelength nm',360,830);const p=(w-360)/5,i=Math.min(93,Math.floor(p)),t=p-i;return sfXYZ[i].map((v,k)=>v*(1-t)+sfXYZ[i+1][k]*t);}\nfunction sfNormalise(samples){const v=passbandIntegral(samples);if(!(v>0))throw new RangeError('Spectrum has no V-passband support');return samples.map(s=>s/v);}\nconst sfVega=SPECTRAL_TABLES.standards[0].samples,sfVegaBV=passbandIntegral(sfVega,'B')/passbandIntegral(sfVega,'V');\nconst sfObserverScale=1/sfVega.reduce((s,v,i)=>s+v*sfXYZ[i][1]*sfWeights[i],0);\nfunction syntheticBV(samples){const b=passbandIntegral(samples,'B'),v=passbandIntegral(samples,'V');if(!(b>0&&v>0))throw new RangeError('B and V need positive support');return -2.5*Math.log10(b/v/sfVegaBV);}\nfunction blackbodyShape(temperatureK){finite(temperatureK,'temperature proxy K',1500,200000);return sfNormalise(SPECTRAL_GRID.map(w=>1/(w**5*Math.expm1(1.438776877e7/(w*temperatureK)))));}\nfunction sfFitColour(bv){if(sfFitCache.has(bv))return sfFitCache.get(bv);let lo=1500,hi=200000;if(bv>syntheticBV(blackbodyShape(lo))||bv<syntheticBV(blackbodyShape(hi)))return null;\n for(let i=0;i<48;i++){const mid=Math.sqrt(lo*hi);if(syntheticBV(blackbodyShape(mid))>bv)lo=mid;else hi=mid;}\n const T=Math.sqrt(lo*hi),fit={samples:blackbodyShape(T),temperatureProxyK:T};sfFitCache.set(bv,fit);return fit;\n}\n/** Hierarchy: caller spectrum with provenance -> same-identity standard -> strictly matched,\n * colour-compatible standard template -> B-V constrained continuum -> explicitly unknown.\n * Template reuse is opt-in via actual spectralType and never labelled a target measurement.\n */\nfunction sfTiltTemplate(samples,bv){let lo=-4,hi=4,p=0,shape;for(let i=0;i<40;i++){p=(lo+hi)/2;shape=samples.map((x,j)=>x*(SPECTRAL_GRID[j]/550)**p);if(syntheticBV(shape)<bv)lo=p;else hi=p;}return {samples:sfNormalise(shape),colourTiltExponent:p};}\nfunction selectSpectrum(star){\n if(star.sed){const d=star.sed;if(typeof d.source!=='string'||!d.source.trim())throw new TypeError('Provided spectrum requires source provenance');return {samples:sfNormalise(sfValidate(d.samples)),kind:d.kind??'provided-spectrum',source:d.source,measuredForThisSource:d.measuredForThisSource===true,temperatureProxyK:null,colourFallback:false};}\n const key=[star.hip??'',star.spectralType??'',star.bv??'unknown'].join('|');if(sfCache.has(key))return sfCache.get(key);\n let value;const own=SPECTRAL_TABLES.standards.find(s=>s.hip===star.hip);\n if(own)value={samples:own.samples,kind:own.kind,source:own.source,measuredForThisSource:true,resolution:own.resolution,temperatureProxyK:null,colourFallback:false};\n const bv=star.bv;\n if(!value&&bv!=null){finite(bv,'B-V',-.5,5);const template=SPECTRAL_TABLES.standards.find(s=>s.templateClass===star.spectralType&&Math.abs(bv-s.catalogueBV)<=.08);\n  if(template)value={...sfTiltTemplate(template.samples,bv),kind:'observed-standard-template',source:template.source,measuredForThisSource:false,temperatureProxyK:null,colourFallback:false,templateColourResidualMag:syntheticBV(template.samples)-bv};\n  else if(bv>=-.4&&bv<=2){const fitted=sfFitColour(bv);if(fitted)value={...fitted,kind:'B-V-constrained-continuum',source:'catalogue B-V; Planck family solved in declared Bessell B/V convention',measuredForThisSource:false,colourFallback:false};}\n }\n if(!value)value={samples:blackbodyShape(6500),kind:'unknown-neutral-display',source:'no admissible measured colour/spectrum; grey display proxy only',measuredForThisSource:false,temperatureProxyK:null,colourFallback:true};\n Object.freeze(value.samples);Object.freeze(value);if(sfCache.size<12000)sfCache.set(key,value);return value;\n}\nfunction spectrumToXYZ(samples){return [0,1,2].map(k=>samples.reduce((s,v,i)=>s+v*sfXYZ[i][k]*sfWeights[i]*sfObserverScale,0));}\nfunction gamutMapXYZ(xyz){let rgb=xyzToLinearRgb(xyz).map(x=>Math.max(0,x));const y=luminance(rgb);return y>0?rgb.map(x=>x*xyz[1]/y):[0,0,0];}\n/** transportAt receives wavelength nm and returns TOTAL direct terrestrial transmission.\n * If supplied, it owns aerosol/gas/cloud attenuation; the atmosphere object is not reapplied.\n */\nfunction spectralStarFlux(star,altDeg,atmosphere={},options={}){\n finite(altDeg,'altitude',-90,90);const spectrum=selectSpectrum(star),scale=magnitudeFlux(star.vmag);\n if(altDeg<0)return {rgb:[0,0,0],xyz:[0,0,0],vFlux:0,kind:spectrum.kind,colourFallback:spectrum.colourFallback};\n const X=airmass(altDeg),cloud=finite(atmosphere.cloudTransmission??1,'cloud transmission',0,1);\n const samples=spectrum.samples.map((v,i)=>{const w=SPECTRAL_GRID[i],t=options.transportAt?finite(options.transportAt(w),'total spectral transmission',0,1):Math.exp(-X*opticalDepth(w,atmosphere))*cloud;return v*t*scale;});\n const xyz=spectrumToXYZ(samples),vFlux=passbandIntegralSafeZero(samples),response=options.response??'CIE1931';let rgb;\n if(response==='CIE1931')rgb=spectrum.colourFallback?[xyz[1],xyz[1],xyz[1]]:gamutMapXYZ(xyz);\n else if(response==='V-monochrome')rgb=[vFlux,vFlux,vFlux];else throw new RangeError('Unknown response model');\n return {rgb,xyz,vFlux,kind:spectrum.kind,model:spectrum.kind,source:spectrum.source,colourFallback:spectrum.colourFallback,temperatureProxyK:spectrum.temperatureProxyK,response,transportOwner:options.transportAt?'caller-total-transmission':'spectral-module'};\n}\nfunction passbandIntegralSafeZero(samples){return samples.some(x=>x>0)?passbandIntegral(samples):0;}\n\n// real-sky/core/src/optics.mjs\n/** Normalised Gaussian-mixture optical PSFs; deliberate approximations, not stellar discs.\n * Diffraction is represented by a Gaussian core matched approximately to Airy FWHM.\n * It does NOT reproduce diffraction rings/spider spikes. Pixel integration is exact Gaussian\n * CDF quadrature in renderer.mjs. Scatter redistributes a fixed fraction of energy.\n */\n\nfunction psfComponents({preset='reference',wavelengthNm=550,arcsecPerCssPixel=1200,\n apertureMm=preset==='eye'?6:50,seeingFwhmArcsec=2,pixelSigmaCss=.48,scatterFraction,\n coreSigmaCss=.55,scatterSigmaCss=2.2}={}){\n if(!['reference','camera','eye'].includes(preset))throw new RangeError('Unknown optical preset');\n finite(wavelengthNm,'wavelength nm',360,830);finite(apertureMm,'aperture mm',.1,10000);finite(arcsecPerCssPixel,'angular pixel scale',.01,100000);\n finite(seeingFwhmArcsec,'seeing FWHM arcsec',0,120);finite(pixelSigmaCss,'pixel reconstruction sigma',.1,8);\n finite(coreSigmaCss,'core sigma',.1,8);finite(scatterSigmaCss,'scatter sigma',.1,12);\n const scatter=finite(scatterFraction??(preset==='eye'?.06:preset==='camera'?.015:.035),'scatter fraction',0,.25);\n const diffractionSigma=.437*(wavelengthNm*1e-9/(apertureMm*.001))*206264.806;\n const sigma=preset==='reference'?coreSigmaCss:Math.min(50,Math.hypot(pixelSigmaCss,diffractionSigma/arcsecPerCssPixel,seeingFwhmArcsec/2.35482/arcsecPerCssPixel));\n const wing=Math.max(sigma,scatterSigmaCss*(preset==='eye'?1.4:1));\n return [{sigmaCss:sigma,weight:1-scatter},{sigmaCss:wing,weight:scatter}];\n}\n\n// real-sky/core/src/renderer.mjs\n/** CPU reference rasterizer. Accumulates sources + supplied sky in LINEAR light, then\n * tone maps and sRGB-encodes once. Output is intentionally opaque: CSS screen blending\n * an encoded transparent canvas with the old sky is NOT the same physical pipeline.\n */\n\n\n\n\nfunction createLinearBuffer(width,height,background=[0,0,0]){\n if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>8000000)throw new RangeError('invalid/budget-exceeding raster dimensions');\n if(!Array.isArray(background)||background.length!==3||!background.every(x=>Number.isFinite(x)&&x>=0))throw new RangeError('linear RGB background required');\n const b=new Float64Array(width*height*3);if(background.some(x=>x!==0))for(let i=0;i<b.length;i++)b[i]=background[i%3];return b;\n}\n// Abramowitz/Stegun 7.1.26 approximation; pixel-boundary integration removes subpixel popping.\nfunction erf(x){const sign=x<0?-1:1,a=Math.abs(x),t=1/(1+.3275911*a);return sign*(1-(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-.284496736)*t+.254829592)*t*Math.exp(-a*a));}\nfunction splatGaussian(buffer,width,height,x,y,rgb,sigma){\n finite(x,'x');finite(y,'y');finite(sigma,'PSF sigma',.05,100);\n if(buffer.length!==width*height*3||!Array.isArray(rgb)||rgb.length!==3||!rgb.every(v=>Number.isFinite(v)&&v>=0))throw new RangeError('invalid splat buffer/flux');\n const support=Math.ceil(6*sigma)+1,ix=Math.floor(x),iy=Math.floor(y),inv=1/(sigma*Math.SQRT2);\n const xs=Math.max(0,ix-support),xe=Math.min(width-1,ix+support),ys=Math.max(0,iy-support),ye=Math.min(height-1,iy+support);\n for(let j=ys;j<=ye;j++){const wy=.5*(erf((j+1-y)*inv)-erf((j-y)*inv));for(let i=xs;i<=xe;i++){\n const wx=.5*(erf((i+1-x)*inv)-erf((i-x)*inv)),w=Math.max(0,wx*wy),k=(j*width+i)*3;\n for(let c=0;c<3;c++)buffer[k+c]+=rgb[c]*w;\n }}\n}\n/** Unit: integrated source contribution per CSS pixel area. DPR therefore scales integral\n * by dpr^2 and PSF width by dpr; the displayed radiance/area stays invariant.\n */\nfunction renderStars(stars,{width=325,height=530,dpr=1,background=[0,0,0],backgroundLinear=null,\n atmosphere={},sigmaCss=.55,haloFraction=.035,haloSigmaCss=2.2,utcMs=0,reducedMotion=true,scintillationAmplitude=0,\n transmissionAt=()=>1,pixelTransmissionAt=null,sourceVisibility=()=>true,\n fluxAt=null,opticalPreset='reference',optics={},response='CIE1931'}={}){\n finite(dpr,'DPR',.5,4);finite(sigmaCss,'PSF sigma CSS',.1,8);finite(haloFraction,'halo fraction',0,.25);finite(haloSigmaCss,'halo sigma',.1,12);\n const w=Math.round(width*dpr),h=Math.round(height*dpr),linear=createLinearBuffer(w,h,background);\n if(backgroundLinear){if(backgroundLinear.length!==linear.length||!backgroundLinear.every(x=>Number.isFinite(x)&&x>=0))throw new RangeError('invalid linear sky buffer');linear.set(backgroundLinear);}\n let drawn=0,colourFallbacks=0;const spectralKinds={};\n for(const s of stars){if(s.emission?.enabled===false||s.altDeg<0||s.visible===false||!sourceVisibility(s))continue;\n const mask=finite(transmissionAt(s.x,s.y,s),'source transmission',0,1);if(mask===0)continue;\n const f=fluxAt?fluxAt(s):spectralStarFlux(s,s.altDeg,atmosphere,{response}),tw=scintillation(s.hip??(1000000+(s.hygId??0)),utcMs/1000,s.altDeg,reducedMotion?0:scintillationAmplitude);\n const rgb=f.rgb.map(x=>x*mask*tw*dpr*dpr);if(rgb.every(x=>x===0))continue;\n const wavelengths=[610,550,460];\n for(let channel=0;channel<3;channel++){const psf=psfComponents({preset:opticalPreset,wavelengthNm:wavelengths[channel],coreSigmaCss:sigmaCss,scatterSigmaCss:haloSigmaCss,...(opticalPreset==='reference'?{scatterFraction:haloFraction}:{}),...optics});\n  for(const part of psf)if(part.weight>0){const energy=[0,0,0];energy[channel]=rgb[channel]*part.weight;splatGaussian(linear,w,h,s.x*dpr,s.y*dpr,energy,part.sigmaCss*dpr);}\n }\n drawn++;if(f.colourFallback)colourFallbacks++;const kind=f.kind??'caller-flux';spectralKinds[kind]=(spectralKinds[kind]??0)+1;\n }\n if(pixelTransmissionAt){for(let y=0;y<h;y++)for(let x=0;x<w;x++){\n  const m=finite(pixelTransmissionAt((x+.5)/dpr,(y+.5)/dpr),'pixel transmission',0,1),i=(y*w+x)*3;\n  for(let k=0;k<3;k++){const base=backgroundLinear?backgroundLinear[i+k]:background[k];linear[i+k]=base+Math.max(0,linear[i+k]-base)*m;}\n }}\n return {linear,width:w,height:h,drawn,colourFallbacks,spectralKinds,representation:'linear V-anchored spectral response relative to Vega; display exposure is not absolute W/m\u00b2/sr'};\n}\nfunction encodeFrame(linear,exposure=12){finite(exposure,'exposure',0,100000);if(linear.length%3)throw new RangeError('RGB buffer required');const bytes=new Uint8ClampedArray(linear.length/3*4);\n for(let i=0,j=0;i<linear.length;i+=3,j+=4){for(let c=0;c<3;c++)bytes[j+c]=Math.round(255*linearToSrgb(-Math.expm1(-exposure*Math.max(0,finite(linear[i+c],'linear channel')))));bytes[j+3]=255;}\n return bytes;\n}\n\n// real-sky/core/src/atmosphere.mjs\n/** CP6 explicit local atmospheric assumptions. Optical depths are vertical at the site.\n * Pressure is station pressure, NOT sea-level-corrected pressure. A supplied pressure wins\n * over elevation: do not reduce it a second time. Cloud transmission is a separate owner.\n */\n\n\nconst atmValidated=new WeakSet();\nfunction normaliseAtmosphere(input={}){\n if(input&&atmValidated.has(input))return input;\n if(input===null||typeof input!=='object')throw new TypeError('Atmosphere must be an object');\n const elevationM=finite(input.elevationM??0,'elevation metres',-500,10000);\n if(input.cloudTransmission!=null&&input.cloudOpticalDepth!=null)throw new RangeError('Supply cloud transmission OR vertical cloud optical depth, not both');\n const pressureHpa=finite(input.pressureHpa??1013.25*(1-2.25577e-5*elevationM)**5.25588,'station pressure hPa',0,1100);\n const result=Object.freeze({__cp6Atmosphere:true,elevationM,pressureHpa,pressureSource:input.pressureHpa==null?'standard-atmosphere-estimate':'caller-supplied-station-pressure',\n aerosolTau550:finite(input.aerosolTau550??.06,'aerosol optical depth 550nm',0,3),angstromExponent:finite(input.angstromExponent??1.3,'Angstrom exponent',0,4),\n greyTau:finite(input.greyTau??0,'grey absorbing optical depth',0,3),aerosolAlbedo:finite(input.aerosolAlbedo??.9,'aerosol single-scattering albedo',0,1),\n aerosolG:finite(input.aerosolG??.76,'aerosol asymmetry',0,.95),rayleighScaleHeightM:finite(input.rayleighScaleHeightM??8000,'molecular scale height',4000,12000),aerosolScaleHeightM:finite(input.aerosolScaleHeightM??1200,'aerosol scale height',100,6000),\n cloudTransmission:input.cloudOpticalDepth!=null?null:finite(input.cloudTransmission??1,'cloud transmission',0,1),cloudOpticalDepth:input.cloudOpticalDepth==null?null:finite(input.cloudOpticalDepth,'cloud vertical optical depth',0,100),\n cloudGlowCdM2:finite(input.cloudGlowCdM2??0,'fully opaque cloud glow cd/m2',0,100000),lightPollutionCdM2:finite(input.lightPollutionCdM2??0,'local pollution radiance cd/m2',0,100000),\n nightZenithVMag:finite(input.nightZenithVMag??21.8,'night zenith magnitude/arcsec2',10,30),twilightScale:finite(input.twilightScale??1,'empirical twilight site scale',0,10)});\n atmValidated.add(result);return result;\n}\nfunction rayleighOpticalDepth(wavelengthNm,atmosphere={}){const a=normaliseAtmosphere(atmosphere),l=finite(wavelengthNm,'wavelength nm',360,830)/1000;return .008569*l**-4*(1+.0113*l**-2+.00013*l**-4)*a.pressureHpa/1013.25;}\nfunction aerosolOpticalDepth(wavelengthNm,atmosphere={}){const a=normaliseAtmosphere(atmosphere);finite(wavelengthNm,'wavelength nm',360,830);return a.aerosolTau550*(550/wavelengthNm)**a.angstromExponent;}\nfunction cloudTransmissionFor(direction,atmosphere={},cloudAt=null,utcMs=0){const a=normaliseAtmosphere(atmosphere),alt=finite(direction.altDeg,'cloud sightline altitude',-90,90);finite(direction.azDeg,'cloud sightline azimuth');\n if(cloudAt!=null){if(typeof cloudAt!=='function')throw new TypeError('cloudAt must return total sightline cloud transmission');return finite(cloudAt(direction,utcMs),'total cloud-map transmission',0,1);}\n return a.cloudOpticalDepth==null?a.cloudTransmission:Math.exp(-a.cloudOpticalDepth*airmass(Math.max(0,alt)));\n}\nfunction directTransmission(wavelengthNm,altDeg,atmosphere={},totalCloudTransmission=null){const a=normaliseAtmosphere(atmosphere);finite(altDeg,'source altitude',-90,90);if(altDeg<0)return 0;\n const cloud=totalCloudTransmission==null?cloudTransmissionFor({altDeg,azDeg:0},a):finite(totalCloudTransmission,'total cloud transmission',0,1);\n return cloud*Math.exp(-airmass(altDeg)*(rayleighOpticalDepth(wavelengthNm,a)+aerosolOpticalDepth(wavelengthNm,a)+a.greyTau));\n}\nfunction phaseRayleigh(cosine){finite(cosine,'phase cosine',-1,1);return 3/(16*Math.PI)*(1+cosine*cosine);}\n/** cosine=1 means looking TOWARDS the illuminator, hence forward scattering peaks there.\n * This sign convention differs from pbrt's two-away-vector convention. */\nfunction phaseHG(cosine,g=.76){finite(cosine,'phase cosine',-1,1);finite(g,'asymmetry',-.99,.99);return (1-g*g)/(4*Math.PI*(1+g*g-2*g*cosine)**1.5);}\nfunction horizontalDirection(h){const a=finite(h.altDeg,'altitude',-90,90)*DEG,z=finite(h.azDeg,'azimuth')*DEG;return [Math.cos(a)*Math.sin(z),Math.cos(a)*Math.cos(z),Math.sin(a)];}\n\n// real-sky/core/src/sky-state.mjs\n/** Low-order Sun/Moon for sky illumination, NOT a lunar material or prayer calculator.\n * Schlyter orbital elements and ALL his listed lunar perturbations, independently written.\n * Uses CP4 TT for orbital time, UT1 sidereal rotation, ellipsoidal topocentric subtraction.\n * No claim of CP4 stellar sub-arcsecond precision for this separate lunar approximation.\n */\n\n\nconst skSin=x=>Math.sin(x*DEG),skCos=x=>Math.cos(x*DEG);\nfunction skOrbit(M,e,a,N=0,i=0,w=0){let E=wrapDeg(M)*DEG;const m=E;for(let k=0;k<8;k++)E-=(E-e*Math.sin(E)-m)/(1-e*Math.cos(E));const x=a*(Math.cos(E)-e),y=a*Math.sqrt(1-e*e)*Math.sin(E),v=Math.atan2(y,x)/DEG,r=Math.hypot(x,y);return {r,longitude:wrapDeg(v+w),vector:[r*(skCos(N)*skCos(v+w)-skSin(N)*skSin(v+w)*skCos(i)),r*(skSin(N)*skCos(v+w)+skCos(N)*skSin(v+w)*skCos(i)),r*skSin(v+w)*skSin(i)]};}\nfunction skEquatorial(v,e){return [v[0],v[1]*skCos(e)-v[2]*skSin(e),v[1]*skSin(e)+v[2]*skCos(e)];}\nfunction physicalSkyState(observer){\n const t=timeScales(observer),lat=finite(observer.latDeg,'latitude',-90,90),lon=finite(observer.lonDeg,'longitude',-180,180),height=finite(observer.heightM??observer.elevationM??0,'height metres',-500,10000);\n const d=t.jdTt-2451543.5,eps=23.4393-3.563e-7*d,Ms=wrapDeg(356.0470+.9856002585*d),ws=282.9404+4.70935e-5*d;\n const sunOrbit=skOrbit(Ms,.016709-1.151e-9*d,1,0,0,ws),N=wrapDeg(125.1228-.0529538083*d),w=wrapDeg(318.0634+.1643573223*d),Mm=wrapDeg(115.3654+13.0649929509*d),moonOrbit=skOrbit(Mm,.0549,60.2666,N,5.1454,w);\n const v=moonOrbit.vector,ls=Ms+ws,lm=Mm+w+N,D=lm-ls,F=lm-N;\n let ml=Math.atan2(v[1],v[0])/DEG,mb=Math.atan2(v[2],Math.hypot(v[0],v[1]))/DEG;\n ml+=-1.274*skSin(Mm-2*D)+.658*skSin(2*D)-.186*skSin(Ms)-.059*skSin(2*Mm-2*D)-.057*skSin(Mm-2*D+Ms)+.053*skSin(Mm+2*D)+.046*skSin(2*D-Ms)+.041*skSin(Mm-Ms)-.035*skSin(D)-.031*skSin(Mm+Ms)-.015*skSin(2*F-2*D)+.011*skSin(Mm-4*D);\n mb+=-.173*skSin(F-2*D)-.055*skSin(Mm-F-2*D)-.046*skSin(Mm+F-2*D)+.033*skSin(F+2*D)+.017*skSin(2*Mm+F);\n const mr=moonOrbit.r-.58*skCos(Mm-2*D)-.46*skCos(2*D),moonEcl=[mr*skCos(ml)*skCos(mb),mr*skSin(ml)*skCos(mb),mr*skSin(mb)],sunKm=skEquatorial(sunOrbit.vector,eps).map(x=>x*149597870.7),moonKm=skEquatorial(moonEcl,eps).map(x=>x*6378.137);\n const lst=wrapDeg(gmstDeg(t.jdUt1)+lon),e2=.0066943799901413165,nn=6378.137/Math.sqrt(1-e2*skSin(lat)**2),site=[(nn+height/1000)*skCos(lat)*skCos(lst),(nn+height/1000)*skCos(lat)*skSin(lst),(nn*(1-e2)+height/1000)*skSin(lat)];\n const body=(p)=>{const top=p.map((x,i)=>x-site[i]),eq=vectorRaDec(top),h=equatorialToHorizontal(eq.raDeg,eq.decDeg,lst,lat);return {...h,...eq,distanceKm:Math.hypot(...top),frame:'topocentric-mean-equator-of-date',geometric:true};};\n const phaseAngleDeg=angularSeparation(sunKm.map((x,i)=>x-moonKm[i]),moonKm.map(x=>-x));\n const sun={...body(sunKm),distanceAu:sunOrbit.r},moon={...body(moonKm),geocentricDistanceKm:mr*6378.137,phaseAngleDeg,illuminatedFraction:(1+skCos(phaseAngleDeg))/2,angularRadiusDeg:Math.asin(1737.4/Math.hypot(...moonKm.map((x,i)=>x-site[i])))/DEG};\n return {utcMs:observer.utcMs,jdTt:t.jdTt,sun,moon,model:'Schlyter-perturbed-low-order; TT/UT1 and ellipsoid topocentre',warnings:[...t.warnings,'Sun/Moon nutation-aberration-light-time not applied','No eclipse attenuation or terrain/refraction in illumination ephemeris']};\n}\n\n// real-sky/core/src/visibility.mjs\n/** Visibility is a display/observer RESPONSE, not an extra extinction coefficient. */\n\n\n/** Modelled central CSS-pixel display contrast. No catalogue or physical flux is changed.\n * This is an 8-bit display diagnostic, not a physiological limiting-magnitude prediction. */\nfunction displayVisibility(sourceY,backgroundY,exposure,{thresholdSrgb=2/255,sigmaCss=.55}={}){\n finite(sourceY,'source flux',0);finite(backgroundY,'background flux per CSS pixel',0);finite(exposure,'display exposure',0,100000);finite(thresholdSrgb,'contrast threshold',0,1);finite(sigmaCss,'PSF sigma',.1,50);\n const peak=sourceY/(2*Math.PI*sigmaCss*sigmaCss),encode=x=>linearToSrgb(-Math.expm1(-x*exposure)),deltaSrgb=encode(backgroundY+peak)-encode(backgroundY);\n return {deltaSrgb,thresholdSrgb,detectable:deltaSrgb>=thresholdSrgb,criterion:'modelled central CSS-pixel contrast; not human acuity'};\n}\n/** Bounded zero-mean deterministic surrogate. Turbulence parameters are NOT measured.\n * Box-exposure averages the two temporal modes analytically (sinc); no frame random draws.\n * Optional modulation never moves a source or changes its catalogue record. */\nfunction scintillationFactor(id,tSeconds,altDeg,{strength=.04,exposureSec=.1,apertureMm=6,reducedMotion=false}={}){\n finite(strength,'scintillation strength',0,.3);finite(exposureSec,'exposure seconds',0,3600);finite(apertureMm,'aperture mm',.1,10000);finite(tSeconds,'time seconds');finite(altDeg,'altitude',-90,90);\n if(reducedMotion||strength===0||altDeg<0)return 1;\n let hash=2166136261;for(const c of String(id))hash=Math.imul(hash^c.charCodeAt(0),16777619)>>>0;\n const phase=hash/4294967296*2*Math.PI,sinc=x=>Math.abs(x)<1e-12?1:Math.sin(x)/x,amp=strength*(.25+.75*(1-Math.sin(altDeg*DEG)))*Math.min(1,(6/apertureMm)**(2/3));\n return 1+amp*(.6*Math.sin(2*Math.PI*.73*tSeconds+phase)*sinc(Math.PI*.73*exposureSec)+.4*Math.sin(2*Math.PI*1.17*tSeconds+2.13*phase)*sinc(Math.PI*1.17*exposureSec));\n}\n\n// real-sky/core/src/sky-background.mjs\n/** CP6 radiance model: spectral spherical single scattering + a measured-site twilight\n * residual, empirical moonlight, and a parameterised natural/local background.\n * Units are photopic-equivalent cd/m\u00b2 under the documented V-to-luminance convention.\n * Not a full multiple-scattering solver, measured local weather, or diffuse star map.\n */\n\n\n\n\nconst V_ZERO_ILLUMINANCE_LUX=2.54e-6;\nconst ARCSEC_PER_RADIAN=206264.80624709636;\nconst bgMagnitudeZero=V_ZERO_ILLUMINANCE_LUX*ARCSEC_PER_RADIAN**2,bgEarthRadius=6371000,bgTopRadius=6471000;\nconst bgSmooth=x=>{x=clamp(x,0,1);return x*x*(3-2*x);};\nconst bgSolarBase=blackbodyShape(5778),bgSolarY=spectrumToXYZ(bgSolarBase)[1],bgSolarShape=bgSolarBase.map(x=>x/bgSolarY),bgCoeff=new WeakMap();\nfunction surfaceMagnitudeToLuminance(m){return bgMagnitudeZero*10**(-.4*finite(m,'V magnitude per arcsec2',-30,60));}\nfunction luminanceToSurfaceMagnitude(L){finite(L,'luminance',Number.MIN_VALUE);return -2.5*Math.log10(L/bgMagnitudeZero);}\n/** An explicit assumed NON-STELLAR residual replaces the historical aggregate floor.\n * It is never inferred by subtracting a map from a total or called measured airglow.\n * Its supplied zenith value is already at the observer (pre-cloud), like the CP6 floor.\n */\nfunction validateResidualNight(input){\n if(!input||input.kind!=='assumed-nonstellar-residual'||input.includesRegisteredStarlight!==false||typeof input.source!=='string'||!input.source.trim())throw new TypeError('Explicit labelled non-stellar residual night assumption required');\n return Object.freeze({kind:input.kind,zenithCdM2:finite(input.zenithCdM2,'residual night zenith cd/m2',0,1),source:input.source,includesRegisteredStarlight:false,measured:false});\n}\n/** Patat et al. (2006) Table 1: fitted TOTAL zenith background, solar depression 5..15\u00b0.\n * Subtract reference night V=21.6/B=22.6 before adding our own natural background.\n * A tapered continuation to 20\u00b0 is an explicit engineering extension, not published data.\n */\nfunction patatTwilight(sunAltDeg){finite(sunAltDeg,'solar altitude',-90,90);const depression=-sunAltDeg,x=clamp(depression,3,15)-5;\n const totalVMag=11.84+1.518*x-.057*x*x,totalBMag=11.84+1.411*x-.041*x*x;\n let v=Math.max(0,10**(-.4*totalVMag)-10**(-.4*21.6)),b=Math.max(0,10**(-.4*totalBMag)-10**(-.4*22.6));\n const tail=depression<=15?1:Math.exp(-.4*Math.LN10*.378*(depression-15))*(1-bgSmooth((depression-15)/5));v*=tail;b*=tail;\n return {totalVMag,totalBMag,excessLuminance:bgMagnitudeZero*v,bv:v>0&&b>0?-2.5*Math.log10(b/v):null,inMeasuredDomain:depression>=5&&depression<=15,reference:'Patat2006Table1; night floor removed',extension:depression<5||depression>15};\n}\n/** Original KS1991 equations, nL converted to cd/m\u00b2 (1 nL=1e-5/pi cd/m\u00b2).\n * Near aureole uses their rho^-2 term; blend only 8..12\u00b0 to avoid a branch jump.\n * No opposition boost, eclipse, instrument glare or calendar-Moon position is inferred.\n */\nfunction moonSkyLuminance({moonAltDeg,targetAltDeg,separationDeg,phaseAngleDeg,extinctionMag,distanceKm=384400,angularRadiusDeg=.25}){\n finite(moonAltDeg,'Moon altitude',-90,90);finite(targetAltDeg,'target altitude',-90,90);finite(separationDeg,'Moon separation',0,180);finite(phaseAngleDeg,'lunar phase angle',0,180);finite(extinctionMag,'extinction mag/airmass',0,10);finite(distanceKm,'lunar distance km',100000,1000000);finite(angularRadiusDeg,'lunar angular radius',.01,2);\n if(targetAltDeg<0||moonAltDeg<=-angularRadiusDeg||extinctionMag===0)return 0;\n const u=clamp(moonAltDeg/angularRadiusDeg,-1,1),visibleDisc=(Math.acos(-u)+u*Math.sqrt(Math.max(0,1-u*u)))/Math.PI,rho=Math.max(angularRadiusDeg,separationDeg),c=Math.cos(rho*DEG),a=phaseAngleDeg;\n const X=alt=>(1-.96*Math.cos(Math.max(0,alt)*DEG)**2)**(-.5),near=6.2e7/(rho*rho),far=10**(6.15-rho/40),blend=bgSmooth((rho-8)/4);\n const f=10**5.36*(1.06+c*c)+near*(1-blend)+far*blend,I=10**(-.4*(3.84+.026*a+4e-9*a**4));\n return (1e-5/Math.PI)*f*I*10**(-.4*extinctionMag*X(moonAltDeg))*(-Math.expm1(-.4*Math.LN10*extinctionMag*X(targetAltDeg)))*(384400/distanceKm)**2*visibleDisc;\n}\nfunction bgCoefficients(a){if(bgCoeff.has(a))return bgCoeff.get(a);const result=SPECTRAL_GRID.map(w=>[rayleighOpticalDepth(w,a)/a.rayleighScaleHeightM,aerosolOpticalDepth(w,a)/a.aerosolScaleHeightM]);bgCoeff.set(a,result);return result;}\nfunction bgExit(p,v,radius){const b=dot(p,v),c=dot(p,p)-radius*radius;return -b+Math.sqrt(Math.max(0,b*b-c));}\nfunction bgSunColumns(p,sun,groundRadius,a,steps){const b=dot(p,sun),r2=dot(p,p);if(b<0&&r2-b*b<groundRadius*groundRadius)return null;\n const end=bgExit(p,sun,bgTopRadius);let R=0,A=0;for(let j=0;j<steps;j++){const left=end*(j/steps)**2,right=end*((j+1)/steps)**2,t=(left+right)/2,h=Math.sqrt(r2+2*b*t+t*t)-groundRadius;R+=Math.exp(-h/a.rayleighScaleHeightM)*(right-left);A+=Math.exp(-h/a.aerosolScaleHeightM)*(right-left);}return [R,A];}\n/** 95 wavelength bins; 24 non-uniform view cells x 12 solar-column cells by default.\n * Solid Earth shadow is checked for every scatter point. Density is exponential above\n * the local spherical ground; this is a flat-altitude-site model, not global terrain.\n */\nfunction singleScatteredSun(direction,state,atmosphere={},options={}){\n const a=normaliseAtmosphere(atmosphere),view=horizontalDirection(direction),sun=horizontalDirection(state.sun),vSteps=options.viewSteps??24,sSteps=options.sunSteps??12;\n if(!Number.isInteger(vSteps)||vSteps<4||vSteps>256||!Number.isInteger(sSteps)||sSteps<4||sSteps>256)throw new RangeError('Invalid scattering quadrature');\n if(direction.altDeg<0||state.sun.altDeg<-20||(a.pressureHpa===0&&a.aerosolTau550===0))return {rgb:[0,0,0],luminance:0};\n const ground=bgEarthRadius+a.elevationM,p0=[0,0,ground],end=bgExit(p0,view,bgTopRadius),cosine=clamp(dot(view,sun)),pr=phaseRayleigh(cosine),pa=phaseHG(cosine,a.aerosolG)*a.aerosolAlbedo,coeff=bgCoefficients(a),grey=a.greyTau/a.rayleighScaleHeightM;\n const samples=new Array(95).fill(0);let R=0,A=0;\n for(let j=0;j<vSteps;j++){const left=end*(j/vSteps)**2,right=end*((j+1)/vSteps)**2,t=(left+right)/2,ds=right-left,p=[view[0]*t,view[1]*t,ground+view[2]*t],h=Math.hypot(...p)-ground,dr=Math.exp(-h/a.rayleighScaleHeightM),da=Math.exp(-h/a.aerosolScaleHeightM),rMid=R+dr*ds/2,aMid=A+da*ds/2,solar=bgSunColumns(p,sun,ground,a,sSteps);\n  if(solar){const rPath=rMid+solar[0],aPath=aMid+solar[1];for(let k=0;k<95;k++){const [br,ba]=coeff[k];samples[k]+=(br*dr*pr+ba*da*pa)*Math.exp(-(br+grey)*rPath-ba*aPath)*ds;}}\n  R+=dr*ds;A+=da*ds;\n }\n const distance=finite(state.sun.distanceAu??1,'Sun distance AU',.9,1.1),illuminance=127500/(distance*distance),xyz=spectrumToXYZ(samples.map((x,i)=>x*bgSolarShape[i]*illuminance));\n return {rgb:gamutMapXYZ(xyz),luminance:xyz[1],model:'spherical spectral single scattering',viewSteps:vSteps,sunSteps:sSteps};\n}\n/** Solar lookup is per physical sky state; 5\u00b0 altitude /10\u00b0 azimuth interpolation.\n * Lunar aureole and total cloud transmission are evaluated at the requested direction,\n * not baked into that coarse solar grid. No persistent cache can freeze sky time.\n */\nfunction createSkyModel(state,atmosphere={},options={}){\n horizontalDirection(state.sun);horizontalDirection(state.moon);finite(state.moon.phaseAngleDeg,'physical lunar phase',0,180);finite(state.utcMs,'sky UTC');\n const nightSpec=options.residualNight==null?null:validateResidualNight(options.residualNight);\n const a=normaliseAtmosphere(atmosphere),grid=new Map(),sun=horizontalDirection(state.sun),tw=patatTwilight(state.sun.altDeg),twilightWeight=bgSmooth((-state.sun.altDeg-3)/2),\n twilightSpectrum=selectSpectrum({bv:tw.bv}).samples,twilightXYZ=spectrumToXYZ(twilightSpectrum),twilightRgb=gamutMapXYZ(twilightXYZ).map(x=>x/twilightXYZ[1]);\n // A first-order site-rescaling assumption, not a calibrated multiple-scattering law.\n const twilightDepthScale=(rayleighOpticalDepth(550,a)+aerosolOpticalDepth(550,a)*a.aerosolAlbedo)/(rayleighOpticalDepth(550,{})+.06*.9);\n const tauR=rayleighOpticalDepth(550,a),tauA=aerosolOpticalDepth(550,a),totalTau=tauR+tauA+a.greyTau,\n // KS uses empirical total extinction. Extend with an effective scattering albedo so\n // explicitly absorbing-only opacity cannot become a fictitious lunar source term.\n lunarScatteringAlbedo=totalTau>0?(tauR+tauA*a.aerosolAlbedo)/totalTau:0,\n k=1.0857362047581296*totalTau,night=nightSpec?nightSpec.zenithCdM2:surfaceMagnitudeToLuminance(a.nightZenithVMag);\n const angularShape=h=>{const v=horizontalDirection(h),c=clamp(dot(v,sun));return (.75*phaseRayleigh(c)+.25*phaseHG(c,a.aerosolG))*(1+.25*(1-Math.sin(h.altDeg*DEG)));},zenithShape=angularShape({altDeg:90,azDeg:0});\n function solarNode(ia,iz){iz=(iz+36)%36;const key=ia*36+iz;if(grid.has(key))return grid.get(key);const h={altDeg:ia*5,azDeg:iz*10},ss=singleScatteredSun(h,state,a,options.quadrature),empirical=a.twilightScale*twilightDepthScale*tw.excessLuminance*angularShape(h)/zenithShape,\n extra=twilightWeight*Math.max(0,empirical-ss.luminance),rgb=ss.rgb.map((x,i)=>x+extra*twilightRgb[i]);grid.set(key,rgb);return rgb;}\n function solarAt(h){if(state.sun.altDeg<-20)return [0,0,0];const aa=clamp(h.altDeg/5,0,18),zz=wrapDeg(h.azDeg)/10,ia=Math.min(17,Math.floor(aa)),iz=Math.floor(zz),ta=aa-ia,tz=zz-iz,\n nodes=[solarNode(ia,iz),solarNode(ia,iz+1),solarNode(ia+1,iz),solarNode(ia+1,iz+1)];return [0,1,2].map(c=>(nodes[0][c]*(1-tz)+nodes[1][c]*tz)*(1-ta)+(nodes[2][c]*(1-tz)+nodes[3][c]*tz)*ta);}\n function sample(h){const v=horizontalDirection(h);if(h.altDeg<0)return {rgb:[0,0,0],luminance:0,solarLuminance:0,moonLuminance:0,naturalLuminance:0,cloudTransmission:0,ground:true};\n const X=(1-.96*Math.cos(h.altDeg*DEG)**2)**-.5,natural=night*X*Math.exp(-k/1.0857362047581296*(X-1)),rho=angularSeparation(v,horizontalDirection(state.moon)),moon=moonSkyLuminance({moonAltDeg:state.moon.altDeg,targetAltDeg:h.altDeg,separationDeg:rho,phaseAngleDeg:state.moon.phaseAngleDeg,extinctionMag:k,distanceKm:state.moon.distanceKm??384400,angularRadiusDeg:state.moon.angularRadiusDeg??.25})*lunarScatteringAlbedo,solar=solarAt(h),cloud=cloudTransmissionFor(h,a,options.cloudAt,state.utcMs),local=a.lightPollutionCdM2+a.cloudGlowCdM2*(1-cloud);\n // Lunar and night spectra not measured: explicitly neutral luminous display proxies.\n const rgb=solar.map(x=>(x+moon+natural)*cloud+local);\n return {rgb,luminance:luminance(rgb),solarLuminance:luminance(solar)*cloud,moonLuminance:moon*cloud,naturalLuminance:natural*cloud,...(nightSpec?{residualNightLuminance:natural*cloud,legacyNightLuminance:0}:{}),localLuminance:local,cloudTransmission:cloud,moonSeparationDeg:rho,colourModel:'spectral solar; B-V twilight continuum; neutral night/lunar proxy'};\n }\n return {state,atmosphere:a,sample,...(nightSpec?{nightBudget:{mode:'nonstellar-residual-replaces-legacy-floor',residual:nightSpec,ignoredLegacyNightZenithVMag:a.nightZenithVMag}}:{}),solarNodeCount:()=>grid.size,models:{solar:'spherical single scattering plus Patat-site twilight residual',moon:'Krisciunas-Schaefer1991 with finite aureole',night:nightSpec?'explicit assumed non-stellar residual + inherited angular law':'parameterised zenith + empirical scattering air mass',cloud:'total direct transmission plus explicit local glow'},warnings:['No full multiple scattering, polarisation, ozone bands, eclipses, global terrain or measured local weather','Twilight fit measured near zenith at Paranal; angular continuation and other sites approximate','Moon/night colours are neutral proxies, not measured spectra','Brightness zero point is photopic-equivalent V approximation']};\n}\n\n// real-sky/core/src/catalogue.mjs\n\nfunction validateCatalogue(c){\n if(!['salah-real-sky/catalogue/1','salah-real-sky/catalogue/2'].includes(c?.schema)||!Array.isArray(c.stars)||!c.stars.length)throw new TypeError('unsupported or empty catalogue');\n const v2=c.schema.endsWith('/2'),seen=new Set(),hips=new Set();\n for(const s of c.stars){\n  if(v2){\n   if(typeof s.id!=='string'||!/^hyg:[1-9][0-9]*$/.test(s.id)||s.id!==`hyg:${s.hygId}`||!Number.isSafeInteger(s.hygId)||seen.has(s.id))throw new Error('invalid or duplicate stable identity');\n   seen.add(s.id);\n  }\n  if(!v2||s.hip!==null){if(!Number.isSafeInteger(s.hip)||s.hip<=0||hips.has(s.hip))throw new Error('invalid or duplicate HIP identity');hips.add(s.hip);}\n  finite(s.raDeg,'RA',0,360);if(s.raDeg>=360)throw new RangeError('RA must be below 360 degrees');\n  finite(s.decDeg,'declination',-90,90);finite(s.vmag,'V magnitude',-2,25);finite(s.epochJyear,'epoch',1800,2200);\n  if(s.bv!==null)finite(s.bv,'B-V',-.5,5);\n  for(const k of ['pmRaCosDecMasYr','pmDecMasYr','distancePc','radialVelocityKmS'])if(s[k]!=null)finite(s[k],k);\n  if(s.distancePc!=null&&s.distancePc<=0)throw new RangeError('distance must be positive');\n }\n return c;\n}\n/** Fetch with explicit generation ownership in SkyController; never substitute random stars. */\nasync function loadCatalogue(url,{signal,fetchImpl=globalThis.fetch}={}){\n const r=await fetchImpl(url,{signal,credentials:'omit',cache:'no-cache'});if(!r.ok)throw new Error(`catalogue HTTP ${r.status}`);\n return validateCatalogue(await r.json());\n}\n\n// real-sky/core/src/scene.mjs\n/** Stateful integration boundary. Scene readiness and ticking astronomical time are DIFFERENT keys.\n * The host owns scheduling, clock, geolocation, Moon and weather. This module owns none of them.\n */\n\n\n\nfunction projectCatalogue(catalogue,observer,project=projectWidgetDome){\n const f=observationFrame(observer);\n return catalogue.stars.map(s=>{const h=observeStar(s,f),p=project(h);return {...s,...h,x:p?.x??0,y:p?.y??0,visible:!!p&&p.visible!==false&&h.aboveHorizon};});\n}\nclass SkyController{\n constructor(catalogue=null){this.catalogue=catalogue?validateCatalogue(catalogue):null;this.generation=0;this.last=null;this.error=null;}\n clear(){this.last=null;this.catalogue=null;this.generation++;}\n /** A late network callback cannot re-paint a superseded target. Failure is empty, never fictional. */\n async replaceAsync(load){const generation=++this.generation;this.catalogue=null;this.last=null;try{const c=validateCatalogue(await load());if(generation!==this.generation)return false;this.catalogue=c;this.error=null;return true;}catch(e){if(generation===this.generation){this.catalogue=null;this.error=String(e.message??e);}return false;}}\n update(observer,{sceneIdentity=null,appearanceVersion=0,project=projectWidgetDome}={}){\n  if(!this.catalogue)return this.last={status:'unavailable',sources:[],sceneIdentity,appearanceVersion,error:this.error??'catalogue-unavailable'};\n  try{const sources=projectCatalogue(this.catalogue,observer,project);return this.last={status:'ready',sources,sceneIdentity,appearanceVersion,utcMs:observer.utcMs,catalogueId:this.catalogue.id};}\n  catch(e){return this.last={status:'unavailable',sources:[],sceneIdentity,appearanceVersion,error:String(e.message??e)};}\n }\n}\nfunction horizontalVector(h){const a=h.azDeg*DEG,e=h.altDeg*DEG;return [Math.cos(e)*Math.sin(a),Math.cos(e)*Math.cos(a),Math.sin(e)];}\nfunction fromVector(v){v=unit(v);return {altDeg:Math.asin(Math.max(-1,Math.min(1,v[2])))/DEG,azDeg:wrapDeg(Math.atan2(v[0],v[1])/DEG)};}\n/** A geometrical occulting disc is opaque even at new Moon. Caller must supply PHYSICAL\n * apparent sky coordinates/radius, never the widget's calendar Moon placement or illumination.\n */\nfunction discOccults(star,disc){finite(disc.radiusDeg,'angular radius',0,90);return angularSeparation(horizontalVector(star),horizontalVector(disc))<=disc.radiusDeg;}\n/** Great-circle chart strokes, segmented then clipped. They are annotations, never light sources.\n * Entirely hidden edges yield no strokes; partial paths are honestly clipped rather than connected\n * through the card from one visible end to an unrelated point. No boundary assignment is implied.\n */\nfunction annotationSegments(annotations,sources,project=projectWidgetDome,{maxStepDeg=1,maxPixelStep=80}={}){\n finite(maxStepDeg,'angular annotation step',.1,5);const byHip=new Map(sources.map(s=>[s.hip,s])),result=[];\n for(const pattern of annotations.patterns)for(const path of pattern.paths)for(let i=1;i<path.length;i++){\n  const a=byHip.get(path[i-1]),b=byHip.get(path[i]);if(!a||!b)continue;\n  const av=horizontalVector(a),bv=horizontalVector(b),count=Math.max(1,Math.ceil(angularSeparation(av,bv)/maxStepDeg));let prev=null;\n  for(let j=0;j<=count;j++){const h=fromVector(slerp(av,bv,j/count)),p=project(h),curr=p&&h.altDeg>=0&&p.visible!==false?{...p,visible:true}:null;\n   if(prev&&curr&&Math.hypot(curr.x-prev.x,curr.y-prev.y)<=maxPixelStep)result.push({id:pattern.id,a:prev,b:curr});prev=curr;\n  }\n }\n return result;\n}\n\n// real-sky/core/src/sha256.mjs\n/** Portable byte digest for offline asset identity (SHA-256, FIPS 180-4).\n * This is NOT a signature or a claim of upstream authenticity. No I/O or dependency.\n * Tests compare against the independent Node/OpenSSL implementation.\n */\nconst shK=new Uint32Array([\n 0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,\n 0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,\n 0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,\n 0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,\n 0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,\n 0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,\n 0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,\n 0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]);\nconst shRotate=(x,n)=>(x>>>n)|(x<<(32-n));\nfunction sha256Hex(bytes){\n if(!(bytes instanceof Uint8Array)||bytes.length>67108864)throw new TypeError('SHA256 requires at most 64 MiB of bytes');\n const padded=new Uint8Array(Math.ceil((bytes.length+9)/64)*64);padded.set(bytes);padded[bytes.length]=128;\n const dv=new DataView(padded.buffer);dv.setUint32(padded.length-8,Math.floor(bytes.length/536870912));dv.setUint32(padded.length-4,(bytes.length*8)>>>0);\n const h=new Uint32Array([0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]),w=new Uint32Array(64);\n for(let offset=0;offset<padded.length;offset+=64){\n  for(let i=0;i<16;i++)w[i]=dv.getUint32(offset+i*4);\n  for(let i=16;i<64;i++){const x=w[i-15],y=w[i-2];w[i]=(w[i-16]+(shRotate(x,7)^shRotate(x,18)^(x>>>3))+w[i-7]+(shRotate(y,17)^shRotate(y,19)^(y>>>10)))>>>0;}\n  let [a,b,c,d,e,f,g,z]=h;\n  for(let i=0;i<64;i++){const t1=(z+(shRotate(e,6)^shRotate(e,11)^shRotate(e,25))+((e&f)^(~e&g))+shK[i]+w[i])>>>0,t2=((shRotate(a,2)^shRotate(a,13)^shRotate(a,22))+((a&b)^(a&c)^(b&c)))>>>0;\n   z=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;\n  }\n  const v=[a,b,c,d,e,f,g,z];for(let i=0;i<8;i++)h[i]=(h[i]+v[i])>>>0;\n }\n return Array.from(h,x=>x.toString(16).padStart(8,'0')).join('');\n}\n\n// real-sky/core/src/diffuse-map.mjs\n\n\n/** CP7 PARTIAL: validated diagnostic map sampling + celestial registration.\n * Does not authenticate/permit a scientific survey, apply source proper motion,\n * transport atmosphere/cloud light, occult the Moon or encode a physical frame.\n * Current accepted roles are diagnostic and test fixture ONLY.\n */\nconst DF_ROLE='finite-catalogue-diagnostic-not-survey';\nconst DF_SCHEMA='salah-real-sky/diffuse-map/1';\nfunction dfArray(a,n,label){if(!Array.isArray(a)||a.length!==n)throw new TypeError(label+' length mismatch');}\nfunction dfArea(w,h,j){return 2*Math.PI/w*(Math.sin((-90+(j+1)*180/h)*DEG)-Math.sin((-90+j*180/h)*DEG));}\nfunction createDiagnosticDiffuseSampler(asset){\n if(asset?.schema!==DF_SCHEMA||asset.productionAdmissible!==false||![DF_ROLE,'test-fixture'].includes(asset.role))throw new TypeError('Only explicit non-production diagnostic maps or test fixtures are admitted');\n if(asset.frame!=='mean-equatorial-J2000'||asset.epochJyear!==2000)throw new RangeError('Unsupported diffuse coordinate frame/epoch');\n if(asset.quantity!=='relative-V0-flux-per-steradian')throw new RangeError('Unsupported diagnostic radiance unit');\n if(typeof asset.id!=='string'||!asset.id.length||asset.id.length>256)throw new TypeError('Dataset ID required');\n if(typeof asset.sourceSha256!=='string'||!/^[0-9a-f]{64}$/.test(asset.sourceSha256))throw new TypeError('Source hash required; its presence alone does not authenticate the source');\n const g=asset.grid,w=g?.width,h=g?.height;\n if(g?.type!=='equirectangular-cell-centred'||!Number.isInteger(w)||!Number.isInteger(h)||w<4||h<2||w>4096||h>2048||w*h>2097152)throw new RangeError('Invalid or oversized diagnostic grid');\n finite(g.lonStepDeg,'longitude grid spacing',Number.MIN_VALUE);finite(g.latStepDeg,'latitude grid spacing',Number.MIN_VALUE);\n if(g.lonOriginDeg!==0||g.latOriginDeg!==-90||Math.abs(g.lonStepDeg-360/w)>1e-10||Math.abs(g.latStepDeg-180/h)>1e-10)throw new RangeError('Grid axis/spacing contract mismatch');\n dfArray(asset.values,w*h,'values');dfArray(asset.validMask,w*h,'validMask');\n const a=new Float64Array(w*h),mask=new Uint8Array(w*h);let total=0,correction=0;\n for(let i=0;i<a.length;i++){\n  const m=asset.validMask[i];if(m!==0&&m!==1)throw new RangeError('Mask must contain 0 or 1');mask[i]=m;\n  const v=asset.values[i];if(m===0){if(v!==null&&v!==0)throw new RangeError('Missing cells must be null or zero, not hidden radiance');a[i]=0;}\n  else {finite(v,'map radiance',0,1e12);a[i]=v;}\n  const q=a[i]*dfArea(w,h,Math.floor(i/w))-correction,t=total+q;correction=(t-total)-q;total=t;\n }\n if(asset.totalRelativeV0Flux!=null){finite(asset.totalRelativeV0Flux,'declared total',0);if(Math.abs(total-asset.totalRelativeV0Flux)>1e-9*Math.max(1,total))throw new RangeError('Map integrated flux disagrees with its declaration');}\n const cap=j=>{let weighted=0,support=0;for(let x=0;x<w;x++){weighted+=a[j*w+x]/w;support+=mask[j*w+x]/w;}return {weighted,support};};\n const south=cap(0),north=cap(h-1);\n function row(j,x){const ix=Math.floor(x),t=x-ix,l=j*w+((ix%w)+w)%w,r=j*w+((ix+1)%w+w)%w;return {weighted:a[l]*(1-t)+a[r]*t,support:mask[l]*(1-t)+mask[r]*t};}\n function sample(raDeg,decDeg){\n  finite(raDeg,'map RA');finite(decDeg,'map declination',-90,90);\n  const x=wrapDeg(raDeg)/360*w-.5,y=(decDeg+90)/180*h-.5;let v,s;\n  if(y<0){const t=(decDeg+90)/(90/h),b=row(0,x);v=south.weighted*(1-t)+b.weighted*t;s=south.support*(1-t)+b.support*t;}\n  else if(y>h-1){const t=(90-decDeg)/(90/h),b=row(h-1,x);v=north.weighted*(1-t)+b.weighted*t;s=north.support*(1-t)+b.support*t;}\n  else {const j=Math.floor(y),t=y-j,b=row(j,x),c=row(Math.min(h-1,j+1),x);v=b.weighted*(1-t)+c.weighted*t;s=b.support*(1-t)+c.support*t;}\n  const defined=s>=1-1e-12;\n  return {value:defined?v:null,defined,supportFraction:s,availableWeightedValue:v,observationalCoverage:null};\n }\n return Object.freeze({id:asset.id,role:asset.role,diagnosticOnly:true,productionAdmissible:false,sourceSha256:asset.sourceSha256,frame:asset.frame,quantity:asset.quantity,width:w,height:h,totalRelativeV0Flux:total,sample});\n}\nfunction dfFrame(value){return value?.rotation?value:observationFrame(value);}\nfunction dfApply(columns,v){return [0,1,2].map(i=>columns[0][i]*v[0]+columns[1][i]*v[1]+columns[2][i]*v[2]);}\n/** Infinite-distance fixed J2000 direction; no star-dependent propagation is meaningful here. */\nfunction observeDiffuseDirection(direction,observerOrFrame){\n const f=dfFrame(observerOrFrame),o=f.observer;let v=unit(direction);\n if(f.aberration)v=aberrate(v,f.velocityOverC);v=dfApply(f.rotation,v);\n const eq=vectorRaDec(v),h=equatorialToHorizontal(eq.raDeg,eq.decDeg,f.lstDeg,f.latDeg);let ref=0;\n if(h.altDeg>=-1&&o.pressureHpa>0)ref=refractionDeg(h.altDeg,o.pressureHpa,o.temperatureC);\n const alt=h.altDeg+ref,az=h.azDeg*DEG;\n return {...h,geometricAltDeg:h.altDeg,altDeg:alt,refractionDeg:ref,enuGeometric:h.enu,enu:[Math.cos(alt*DEG)*Math.sin(az),Math.cos(alt*DEG)*Math.cos(az),Math.sin(alt*DEG)],utcMs:o.utcMs};\n}\nfunction dfUndoRefraction(apparent,o){\n if(o.pressureHpa===0||apparent>=89.9||apparent< -1)return apparent;\n const minimum=-1+refractionDeg(-1,o.pressureHpa,o.temperatureC);\n if(apparent<minimum)throw new RangeError('Apparent altitude falls in the inherited refraction-model discontinuity');\n let lo=-1,hi=89.9;\n for(let i=0;i<44;i++){const mid=(lo+hi)/2,app=mid+refractionDeg(mid,o.pressureHpa,o.temperatureC);if(app<apparent)lo=mid;else hi=mid;}\n return (lo+hi)/2;\n}\n/** Geometric altitude for physical occultation of an apparent diffuse ray. */\nfunction diffuseGeometricAltitude(apparentAltDeg,observerOrFrame){const f=dfFrame(observerOrFrame);return dfUndoRefraction(finite(apparentAltDeg,'apparent altitude',-90,90),f.observer);}\nfunction horizontalToDiffuseJ2000(horizontal,observerOrFrame){\n const f=dfFrame(observerOrFrame),o=f.observer;finite(horizontal?.altDeg,'horizontal altitude',-90,90);finite(horizontal?.azDeg,'horizontal azimuth');\n const alt=dfUndoRefraction(horizontal.altDeg,o)*DEG,az=horizontal.azDeg*DEG,p=f.latDeg*DEG,t=f.lstDeg*DEG;\n const e=Math.cos(alt)*Math.sin(az),n=Math.cos(alt)*Math.cos(az),u=Math.sin(alt),meridian=u*Math.cos(p)-n*Math.sin(p);\n const date=[meridian*Math.cos(t)-e*Math.sin(t),meridian*Math.sin(t)+e*Math.cos(t),n*Math.cos(p)+u*Math.sin(p)];\n let v=f.rotation.map(c=>dot(c,date));\n if(f.aberration)v=aberrate(v,f.velocityOverC.map(x=>-x));\n return unit(v);\n}\nfunction diffuseRayToMap(xCss,yCss,view,observerOrFrame){\n finite(xCss,'pixel x');finite(yCss,'pixel y');const f=dfFrame(observerOrFrame);let horizontal;\n if(view?.type==='camera')horizontal=unprojectPerspective(xCss,yCss,view);\n else if(view?.type==='allsky')horizontal=unprojectAllSky(xCss,yCss,view);\n else throw new RangeError('Diagnostic view must be camera or allsky');\n if(horizontal.altDeg<0)return {aboveHorizon:false,horizontal,j2000:null,raDeg:null,decDeg:null};\n const v=horizontalToDiffuseJ2000(horizontal,f);\n return {aboveHorizon:true,horizontal,j2000:v,...vectorRaDec(v)};\n}\n/** Diagnostic surface-brightness raster ONLY, not the CP6 physical linear-light frame.\n * Supersamples the camera footprint. Missing source support is a separate mask, never\n * silently renormalised or converted to measured darkness. No frame/time cache is kept.\n */\nfunction renderDiagnosticDiffuse(sampler,observer,view,{dpr=1,samplesPerAxis=1}={}){\n if(sampler?.diagnosticOnly!==true||typeof sampler.sample!=='function')throw new TypeError('Diagnostic sampler required');\n finite(view?.width,'CSS width',16,2048);finite(view?.height,'CSS height',16,2048);finite(dpr,'DPR',.5,3);\n if(!Number.isInteger(samplesPerAxis)||samplesPerAxis<1||samplesPerAxis>4)throw new RangeError('Footprint samples per axis must be 1..4');\n if(view.type==='camera')cameraGeometry(view);else if(view.type!=='allsky')throw new RangeError('Unsupported view');\n if(view.type==='allsky'&&((view.padding??4)<0||(view.padding??4)>=Math.min(view.width,view.height)/2))throw new RangeError('Invalid all-sky padding');\n const width=Math.round(view.width*dpr),height=Math.round(view.height*dpr),count=width*height;\n if(count>2097152)throw new RangeError('Diagnostic raster exceeds 2,097,152 pixels');\n const frame=observationFrame(observer),radiance=new Float64Array(count),skyFraction=new Float32Array(count),missing=new Uint8Array(count),n=samplesPerAxis,den=n*n;\n let skyPixels=0,missingPixels=0;\n for(let y=0;y<height;y++)for(let x=0;x<width;x++){\n  const at=y*width+x;let value=0,sky=0,absent=false;\n  for(let sy=0;sy<n;sy++)for(let sx=0;sx<n;sx++){\n   // Use the actual rounded raster dimensions, so CSS footprint stays fixed at fractional DPR.\n   const ray=diffuseRayToMap((x+(sx+.5)/n)*view.width/width,(y+(sy+.5)/n)*view.height/height,view,frame);\n   if(!ray.aboveHorizon)continue;sky++;\n   const s=sampler.sample(ray.raDeg,ray.decDeg);if(!s.defined)absent=true;else value+=s.value;\n  }\n  skyFraction[at]=sky/den;if(sky)skyPixels++;\n  if(absent){missing[at]=1;missingPixels++;radiance[at]=0;}else radiance[at]=value/den;\n }\n return {width,height,dpr,radiance,skyFraction,missing,skyPixels,missingPixels,diagnosticOnly:true,productionAdmissible:false,utcMs:observer.utcMs,frameWarnings:[...frame.warnings],sourceId:sampler.id,sourceSha256:sampler.sourceSha256,quantity:sampler.quantity,exposureModel:'not-applied; viewer must label its diagnostic display stretch',physicalComposition:'NOT_IMPLEMENTED_IN_CP7_3'};\n}\n\n/** CP7.5: same inverse frame arithmetic with fixed lat/LST/velocity hoisted.\n * A private observer/frame snapshot is compiled afresh for every physical render.\n * Refraction's inherited inverse and aberration algorithms are unchanged.\n */\nfunction prepareHorizontalToDiffuseJ2000(observerOrFrame){\n const f=dfFrame(observerOrFrame),o={...f.observer},p=f.latDeg*DEG,t=f.lstDeg*DEG;\n const cp=Math.cos(p),sp=Math.sin(p),ct=Math.cos(t),st=Math.sin(t),rotation=f.rotation.map(c=>[...c]),aberration=f.aberration,velocity=f.velocityOverC.map(x=>-x);\n return horizontal=>{\n  finite(horizontal?.altDeg,'horizontal altitude',-90,90);finite(horizontal?.azDeg,'horizontal azimuth');\n  const alt=dfUndoRefraction(horizontal.altDeg,o)*DEG,az=horizontal.azDeg*DEG,e=Math.cos(alt)*Math.sin(az),n=Math.cos(alt)*Math.cos(az),u=Math.sin(alt),meridian=u*cp-n*sp;\n  const date=[meridian*ct-e*st,meridian*st+e*ct,n*cp+u*sp];let v=rotation.map(c=>dot(c,date));\n  if(aberration)v=aberrate(v,velocity);return unit(v);\n };\n}\n\n// real-sky/core/src/registered-starlight.mjs\n\n\n\n/** Admitted, corrected V-component. ICRS axes share the existing mean-J2000\n * geometry within a declared 0.1-arcsecond frame-bias allowance. No epoch-2016\n * precession, star-dependent proper motion, atmosphere or display encoding here. */\nconst RS_SHA='69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446';\nconst RS_F0=3.62708e-11;\nfunction rsN(n){if(!Number.isInteger(n)||n<1||n>256||(n&(n-1)))throw new RangeError('NESTED nside must be a power of two in 1..256');return n;}\nfunction healpixIndex(nside,raDeg,decDeg){\n const n=rsN(nside);finite(raDeg,'ICRS longitude');finite(decDeg,'ICRS latitude',-90,90);\n const tt=wrapDeg(raDeg)/90,z=Math.sin(decDeg*DEG),za=Math.abs(z);let f,ix,iy;\n if(za<=2/3){const jp=Math.floor(n*(.5+tt-.75*z)),jm=Math.floor(n*(.5+tt+.75*z)),fp=Math.floor(jp/n),fm=Math.floor(jm/n);f=fp===fm?(fp%4)+4:fp<fm?fp%4:(fm%4)+8;ix=jm%n;iy=n-(jp%n)-1;}\n else{const nt=Math.min(3,Math.floor(tt)),tp=tt-nt,t=n*Math.sqrt(3*(1-za)),a=Math.min(n-1,Math.floor(tp*t)),b=Math.min(n-1,Math.floor((1-tp)*t));f=z>=0?nt:nt+8;ix=z>=0?n-b-1:a;iy=z>=0?n-a-1:b;}\n let p=f*n*n;for(let bit=0;(1<<bit)<n;bit++)p|=((ix>>bit)&1)<<(2*bit)|((iy>>bit)&1)<<(2*bit+1);return p;\n}\nfunction healpixCentre(nside,pixel){\n const n=rsN(nside);if(!Number.isInteger(pixel)||pixel<0||pixel>=12*n*n)throw new RangeError('Invalid NESTED address');\n const f=Math.floor(pixel/(n*n)),q=pixel%(n*n);let x=0,y=0;\n for(let b=0;(1<<b)<n;b++){x|=((q>>(2*b))&1)<<b;y|=((q>>(2*b+1))&1)<<b;}\n const j=[2,2,2,2,3,3,3,3,4,4,4,4][f]*n-x-y-1,r=j<n?j:j>3*n?4*n-j:n,z=j<n?1-r*r/(3*n*n):j>3*n?-1+r*r/(3*n*n):(2*n-j)*2/(3*n);\n return {raDeg:wrapDeg(([1,3,5,7,0,2,4,6,1,3,5,7][f]*r+x-y)*45/r),decDeg:Math.asin(Math.max(-1,Math.min(1,z)))/DEG};\n}\nfunction rsRing(n,j){\n const r=j<n?j:j>3*n?4*n-j:n,z=j<n?1-r*r/(3*n*n):j>3*n?-1+r*r/(3*n*n):(2*n-j)*2/(3*n),count=4*r,step=360/count;\n const origin=(j<n||j>3*n)?step/2:((j+n)&1)?0:step/2;\n const lat=Math.asin(z)/DEG,indices=new Uint32Array(count);\n for(let i=0;i<count;i++)indices[i]=healpixIndex(n,origin+i*step,lat);\n return {theta:Math.acos(z),origin,step,indices};\n}\nfunction createRegisteredStarlightSampler(asset,{catalogueSha256=null}={}){\n if(asset?.schema!=='salah-real-sky/registered-starlight/1'||asset.dataAdmitted!==true||asset.component!=='unresolved-integrated-starlight-V')throw new TypeError('Corrected admitted integrated-starlight asset required');\n if(asset.frame!=='ICRS'||asset.grid?.type!=='HEALPix'||asset.grid.order!=='NESTED')throw new TypeError('Unsupported frame/pixel order');\n if(asset.quantity!=='passband-averaged-spectral-radiance-W-m-2-sr-1-nm-1'||asset.band!=='V'||asset.zeroPointWm2nm!==RS_F0)throw new TypeError('V-band spectral-radiance contract mismatch');\n if(asset.sourceSha256!==RS_SHA||!/^[0-9a-f]{64}$/.test(asset.catalogueSha256??'')||(catalogueSha256!==null&&asset.catalogueSha256!==catalogueSha256))throw new TypeError('Source or emitter-catalogue binding mismatch');\n if(asset.fillPolicy!=='median16-nonexcluded-native-cells-before-coarsening'||asset.positionToleranceDeg!==.1||asset.rawAdditiveCompositionAllowed!==false)throw new TypeError('Unrecognised source-removal policy');\n if(typeof asset.id!=='string'||!asset.id.length||asset.id.length>256)throw new TypeError('Asset ID required');\n const n=rsN(asset.grid.nside),count=12*n*n;\n for(const field of ['values','estimatedFraction'])if(!Array.isArray(asset[field])||asset[field].length!==count)throw new TypeError(field+' shape mismatch');\n const a=new Float64Array(count),m=new Float64Array(count);let sum=0,c=0;\n for(let i=0;i<count;i++){a[i]=finite(asset.values[i],'radiance',0,1);m[i]=finite(asset.estimatedFraction[i],'estimated fraction',0,1);const v=a[i]-c,t=sum+v;c=(t-sum)-v;sum=t;}\n const integrated=sum*(4*Math.PI/count);finite(asset.integratedWm2nm,'integrated flux',0);\n if(Math.abs(integrated-asset.integratedWm2nm)>1e-8*Math.max(integrated,1e-300))throw new RangeError('Integrated radiance mismatch');\n const rings=Array.from({length:4*n-1},(_,i)=>rsRing(n,i+1));\n function cap(r){let v=0,e=0;for(const p of r.indices){v+=a[p]/r.indices.length;e+=m[p]/r.indices.length;}return [v,e];}\n const north=cap(rings[0]),south=cap(rings.at(-1));\n function row(r,ra){const x=(wrapDeg(ra)-r.origin)/r.step,i=Math.floor(x),f=x-i,k=r.indices.length,p=r.indices[((i%k)+k)%k],q=r.indices[(((i+1)%k)+k)%k];return [a[p]*(1-f)+a[q]*f,m[p]*(1-f)+m[q]*f];}\n function blend(a,b,t){return [a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t];}\n function sample(raDeg,decDeg,{filter='linear',allowEstimates=true}={}){\n  finite(raDeg,'ICRS longitude');finite(decDeg,'ICRS latitude',-90,90);if(!['linear','nearest'].includes(filter)||typeof allowEstimates!=='boolean')throw new TypeError('Invalid sampling policy');let q;\n  if(filter==='nearest'){const p=healpixIndex(n,raDeg,decDeg);q=[a[p],m[p]];}\n  else{const t=(90-decDeg)*DEG,first=rings[0],last=rings.at(-1);\n   if(t<=first.theta)q=blend(north,row(first,raDeg),t/first.theta);\n   else if(t>=last.theta)q=blend(south,row(last,raDeg),(Math.PI-t)/(Math.PI-last.theta));\n   else{let lo=0,hi=rings.length-1;while(hi-lo>1){const j=(lo+hi)>>1;if(rings[j].theta<=t)lo=j;else hi=j;}q=blend(row(rings[lo],raDeg),row(rings[hi],raDeg),(t-rings[lo].theta)/(rings[hi].theta-rings[lo].theta));}\n  }\n  const estimated=Math.max(0,Math.min(1,q[1])),defined=allowEstimates||estimated<=1e-12;\n  return {value:defined?q[0]:null,defined,estimatedFraction:estimated,retainedSourceFraction:1-estimated,relativeV0PerSr:defined?q[0]/RS_F0:null,observationalCompleteness:null};\n }\n return Object.freeze({id:asset.id,nside:n,dataAdmitted:true,band:'V',quantity:asset.quantity,frame:asset.frame,sourceSha256:RS_SHA,catalogueSha256:asset.catalogueSha256,integratedWm2nm:integrated,zeroPointWm2nm:RS_F0,sample});\n}\n/** Source-coordinate diagnostic raster; output is mean radiance, NOT radiant pixel flux.\n * Pixel footprint antialiasing precedes the explicitly labelled viewer stretch.\n * A future physical compositor must use its pixel solid angle and transport once. */\nfunction renderRegisteredStarlight(sampler,observer,view,{dpr=1,samplesPerAxis=1,allowEstimates=true,filter='linear'}={}){\n if(sampler?.dataAdmitted!==true||typeof sampler.sample!=='function')throw new TypeError('Admitted sampler required');\n finite(view?.width,'CSS width',16,2048);finite(view?.height,'CSS height',16,2048);finite(dpr,'DPR',.5,3);\n if(!Number.isInteger(samplesPerAxis)||samplesPerAxis<1||samplesPerAxis>4)throw new RangeError('Footprint sampling must be 1..4');\n if(typeof allowEstimates!=='boolean'||!['linear','nearest'].includes(filter))throw new TypeError('Invalid sampling policy');\n if(view.type==='camera')cameraGeometry(view);else if(view.type==='allsky')finite(view.padding??4,'all-sky padding',0,Math.min(view.width,view.height)/2-1e-9);else throw new RangeError('Unsupported view');\n const width=Math.round(view.width*dpr),height=Math.round(view.height*dpr),count=width*height;\n if(count>2097152)throw new RangeError('Raster allocation budget exceeded');\n const frame=observationFrame(observer),radiance=new Float64Array(count),estimatedFraction=new Float32Array(count),skyFraction=new Float32Array(count),missing=new Uint8Array(count),n=samplesPerAxis,den=n*n;let skyPixels=0,missingPixels=0;\n for(let y=0;y<height;y++)for(let x=0;x<width;x++){\n  let value=0,estimate=0,sky=0,absent=false;const at=y*width+x;\n  for(let sy=0;sy<n;sy++)for(let sx=0;sx<n;sx++){\n   const q=diffuseRayToMap((x+(sx+.5)/n)*view.width/width,(y+(sy+.5)/n)*view.height/height,view,frame);if(!q.aboveHorizon)continue;sky++;\n   const s=sampler.sample(q.raDeg,q.decDeg,{filter,allowEstimates});estimate+=s.estimatedFraction;if(!s.defined)absent=true;else value+=s.value;\n  }\n  skyFraction[at]=sky/den;estimatedFraction[at]=sky?estimate/sky:0;if(sky)skyPixels++;\n  if(absent){missing[at]=1;missingPixels++;}else radiance[at]=value/den;\n }\n return {width,height,radiance,estimatedFraction,skyFraction,missing,skyPixels,missingPixels,dataAdmitted:true,diagnosticExposureOnly:true,physicalComposition:false,sourceId:sampler.id,sourceSha256:RS_SHA,utcMs:observer.utcMs,frameWarnings:[...frame.warnings],quantity:sampler.quantity};\n}\n\n// real-sky/core/src/diffuse-binding.mjs\n\n\n\nconst dsBindings=new WeakSet();\nfunction dsDeepFreeze(value){if(value&&typeof value==='object'&&!Object.isFrozen(value)){for(const v of Object.values(value))dsDeepFreeze(v);Object.freeze(value);}return value;}\n/** Verify EXACT catalogue bytes named by the corrected source-removal asset, then\n * parse a private frozen catalogue. The physical bridge must use binding.catalogue.\n * Asset admission/photometric uncertainty remain CP7.3's. A hash is not a signature.\n */\nfunction bindRegisteredStarlight(catalogueText,asset){\n if(typeof catalogueText!=='string')throw new TypeError('Unmodified catalogue UTF-8 text required');\n const catalogueSha256=sha256Hex(new TextEncoder().encode(catalogueText));\n if(catalogueSha256!==asset?.catalogueSha256)throw new TypeError('Diffuse emitter catalogue byte hash mismatch');\n const catalogue=dsDeepFreeze(validateCatalogue(JSON.parse(catalogueText)));\n const sampler=createRegisteredStarlightSampler(asset,{catalogueSha256});\n const binding=Object.freeze({catalogue,catalogueSha256,sampler,sourceSha256:sampler.sourceSha256,kind:'verified-catalogue-bound-starlight'});dsBindings.add(binding);return binding;\n}\nfunction isBoundRegisteredStarlight(value){return !!value&&dsBindings.has(value);}\n\n// real-sky/core/src/diffuse-transport.mjs\n/** CP7.4 direct extra-atmospheric V integrated starlight -> observer.\n * No spectrum is inferred from one band. Effective V transmission uses the SAME\n * CP5 Bessell photon-counting passband and retained Vega weighting as a declared\n * IN-BAND ASSUMPTION. Do not call the resulting neutral channel measured RGB.\n */\n\n\n\n\n\n\n\nconst DIFFUSE_TRANSPORT_ASSUMPTION='Vega-weighted effective Bessell V transmission; assumed in-band SED, neutral V-equivalent output';\n/** 0.1-degree lookup; exact() is retained for independent comparisons and controls. */\nfunction createVBandTransmission(atmosphere={}){\n const a=normaliseAtmosphere(atmosphere),t=SPECTRAL_TABLES,w=[],tau=[];\n let weightSum=0;\n for(let i=0;i<t.wavelengthNm.length;i++){\n  const weight=t.standards[0].samples[i]*t.wavelengthNm[i]*t.passbands.V[i]*t.weightsNm[i];\n  if(weight<=0)continue;const lambda=t.wavelengthNm[i];w.push(weight);weightSum+=weight;tau.push(rayleighOpticalDepth(lambda,a)+aerosolOpticalDepth(lambda,a)+a.greyTau);\n }\n for(let i=0;i<w.length;i++)w[i]/=weightSum;\n function exact(altDeg){finite(altDeg,'V transport altitude',-90,90);if(altDeg<0)return 0;const X=airmass(altDeg);let T=0;for(let i=0;i<w.length;i++)T+=w[i]*Math.exp(-X*tau[i]);return Math.max(0,Math.min(1,T));}\n const lut=Float64Array.from({length:901},(_,i)=>exact(i/10));\n function sample(altDeg){finite(altDeg,'V transport altitude',-90,90);if(altDeg<0)return 0;const u=altDeg*10,i=Math.min(899,Math.floor(u)),f=u-i;return lut[i]*(1-f)+lut[i+1]*f;}\n function spectralEnvelope(altDeg){finite(altDeg,'V transport altitude',0,90);const X=airmass(altDeg);return {minimum:Math.exp(-X*Math.max(...tau)),maximum:Math.exp(-X*Math.min(...tau)),meaning:'possible in-band weighting bounds, not a statistical confidence interval'};}\n return Object.freeze({sample,exact,spectralEnvelope,assumption:DIFFUSE_TRANSPORT_ASSUMPTION,lookupStepDeg:.1});\n}\nfunction createDiffuseTransport(diffuse,{observer,atmosphere={},state,cloudAt=null}={}){\n if(!isBoundRegisteredStarlight(diffuse?.binding))throw new TypeError('Verified bound registered-starlight context required');\n const residualNight=validateResidualNight(diffuse.residualNight),a=normaliseAtmosphere(atmosphere),sampler=diffuse.binding.sampler;\n const allowEstimates=diffuse.allowEstimates??true,filter=diffuse.filter??'linear',samplesPerAxis=diffuse.samplesPerAxis??2;\n if(typeof allowEstimates!=='boolean'||!['linear','nearest'].includes(filter)||!Number.isInteger(samplesPerAxis)||samplesPerAxis<1||samplesPerAxis>4)throw new TypeError('Invalid physical diffuse sampling policy');\n if(!state||state.utcMs!==observer?.utcMs)throw new RangeError('Diffuse physical state UTC must match accepted observer UTC');\n if(state.moon?.geometric===false)throw new TypeError('Diffuse occultation requires geometric physical Moon directions');\n const frame=observationFrame(observer),toJ2000=prepareHorizontalToDiffuseJ2000(frame),moonVector=horizontalDirection(state.moon),radius=finite(state.moon.angularRadiusDeg??.25,'physical lunar radius',.01,2),moonCos=Math.cos(radius*DEG),moonAbove=state.moon.altDeg+radius>=0,gas=createVBandTransmission(a);\n function occulted(h){if(!moonAbove)return false;const alt=h.geometricAltDeg??diffuseGeometricAltitude(h.altDeg,frame);return dot(horizontalDirection({altDeg:alt,azDeg:h.azDeg}),moonVector)>=moonCos;}\n function sample(h){\n  horizontalDirection(h);\n  if(h.altDeg<0)return {defined:true,sourceDefined:true,incomingRelativeV0PerSr:0,relativeV0PerSr:0,luminance:0,gasTransmission:0,cloudTransmission:0,estimatedFraction:0,occulted:false,ground:true};\n  const eq=vectorRaDec(toJ2000(h)),s=sampler.sample(eq.raDeg,eq.decDeg,{filter,allowEstimates}),T=gas.sample(h.altDeg),C=cloudTransmissionFor(h,a,cloudAt,state.utcMs),occ=occulted(h);\n  const known=occ||T*C===0||s.defined,value=known?(occ||T*C===0?0:s.relativeV0PerSr*T*C):null;\n  return {defined:known,sourceDefined:s.defined,incomingRelativeV0PerSr:s.relativeV0PerSr,relativeV0PerSr:value,luminance:value===null?null:value*V_ZERO_ILLUMINANCE_LUX,gasTransmission:T,cloudTransmission:C,estimatedFraction:s.estimatedFraction,occulted:occ,raDeg:eq.raDeg,decDeg:eq.decDeg};\n }\n return Object.freeze({sample,occulted,gas,residualNight,samplesPerAxis,allowEstimates,filter,sourceId:sampler.id,sourceSha256:sampler.sourceSha256,catalogueSha256:sampler.catalogueSha256,utcMs:observer.utcMs,frameWarnings:frame.warnings,transportAssumption:DIFFUSE_TRANSPORT_ASSUMPTION,colourModel:'neutral V-equivalent proxy, not measured CIE colour'});\n}\n/** Integrate L/F0 over each actual raster-pixel solid angle, then multiply by DPR\u00b2\n * to match CP5's integrated point-flux convention. Never multiply the radiance by\n * solid angle again during composition. Missing rays are omitted without renormalising\n * remaining support and are carried as a separate incomplete-pixel mask.\n */\nfunction renderDiffuseLayer(model,mapping,{widthPx,heightPx,dpr=1,displayTransmissionAt=null}={}){\n const count=widthPx*heightPx;if(!Number.isInteger(widthPx)||!Number.isInteger(heightPx)||widthPx<1||heightPx<1||count>2097152)throw new RangeError('Physical diffuse raster exceeds 2,097,152-pixel budget');\n finite(dpr,'diffuse DPR',.5,4);if(displayTransmissionAt!=null&&typeof displayTransmissionAt!=='function')throw new TypeError('Display transmission must be a pure callback');\n const physicalLinear=new Float64Array(count*3),linear=new Float64Array(count*3),skyFraction=new Float32Array(count),estimatedFraction=new Float32Array(count),occultedFraction=new Float32Array(count),missing=new Uint8Array(count);\n const n=model.samplesPerAxis,den=n*n,dx=mapping.width/widthPx,dy=mapping.height/heightPx,scale=dx*dy*dpr*dpr/den;\n const budget={incoming:0,afterGas:0,afterCloud:0,afterPhysicalMoon:0,afterDisplayMask:0,units:'integrated relative V0 flux over the view',complete:true};\n let skyPixelsEquivalent=0,missingPixels=0,estimatedPixels=0;\n for(let y=0;y<heightPx;y++)for(let x=0;x<widthPx;x++){\n  const pixel=y*widthPx+x;let pre=0,post=0,sky=0,est=0,occ=0,absent=false;\n  for(let sy=0;sy<n;sy++)for(let sx=0;sx<n;sx++){\n   const px=(x+(sx+.5)/n)*dx,py=(y+(sy+.5)/n)*dy;\n   if(!mapping.above(px,py))continue;\n   const h=mapping.unproject(px,py);if(h.altDeg<0)continue;sky++;\n   const s=model.sample(h),weight=mapping.solidAngle(px,py)*scale;\n   const display=displayTransmissionAt?finite(displayTransmissionAt(px,py),'display mask',0,1):1;\n   est+=s.estimatedFraction;occ+=s.occulted?1:0;\n   if(!s.sourceDefined)budget.complete=false;\n   if(s.sourceDefined){const incoming=s.incomingRelativeV0PerSr*weight;budget.incoming+=incoming;budget.afterGas+=incoming*s.gasTransmission;budget.afterCloud+=incoming*s.gasTransmission*s.cloudTransmission;}\n   if(!s.defined){absent=true;continue;}\n   const transmitted=s.relativeV0PerSr*weight;pre+=transmitted;post+=transmitted*display;\n  }\n  for(let c=0;c<3;c++){physicalLinear[pixel*3+c]=pre;linear[pixel*3+c]=post;}\n  skyFraction[pixel]=sky/den;estimatedFraction[pixel]=sky?est/sky:0;occultedFraction[pixel]=occ/den;\n  skyPixelsEquivalent+=sky/den;if(est>0)estimatedPixels++;\n  if(absent){missing[pixel]=1;missingPixels++;}\n  budget.afterPhysicalMoon+=pre;budget.afterDisplayMask+=post;\n }\n for(const k of ['incoming','afterGas','afterCloud','afterPhysicalMoon','afterDisplayMask'])budget[k]/=dpr*dpr;\n return {physicalLinear,linear,masks:{skyFraction,estimatedFraction,occultedFraction,missing},skyPixelsEquivalent,missingPixels,estimatedPixels,budget};\n}\n\n// real-sky/core/src/physical-sky-renderer.mjs\n/** Joined REFERENCE compositor: atmospheric direct source transport, additive sky radiance,\n * explicit physical occultation, separate calendar/foreground mask, one display transform.\n * This is not a patch applied to the real widget. Host cloud maps must be pure functions\n * of the supplied direction/time and return total LOS transmission, never another alpha pass.\n */\n\n\n\n\n\n\n\n\n\n\nfunction skyProjection(view={}){\n const width=finite(view.width??325,'width CSS',8,4096),height=finite(view.height??530,'height CSS',8,4096),type=view.type??'camera',c={...view,width,height};\n if(type==='camera'){const unproject=prepareInverseProjection({...c,type});const f=cameraGeometry(c).focalPixels,cx=width/2,cy=height/2,fw=unprojectPerspective(cx,cy,c).enu,right=unprojectPerspective(cx+f,cy,c).enu.map((x,i)=>x*Math.SQRT2-fw[i]),up=unprojectPerspective(cx,cy-f,c).enu.map((x,i)=>x*Math.SQRT2-fw[i]);return {width,height,unproject,solidAngle:(x,y)=>f/(f*f+(x-cx)**2+(y-cy)**2)**1.5,above:(x,y)=>{\n  // Reconstructed basis roundoff must not zero an exact-horizon grid row.\n  // The uncertainty band selects the exact existing ray test, not an altitude tolerance.\n  const z=fw[2]+(x-cx)/f*right[2]+(cy-y)/f*up[2];\n  return Math.abs(z)>1e-12?z>0:unproject(x,y).altDeg>=0;\n }};}\n if(type==='allsky'){const unproject=prepareInverseProjection({...c,type});const padding=finite(view.padding??4,'all-sky padding',0,Math.min(width,height)/2-1e-9),R=Math.min(width,height)/2-padding,k=Math.PI/2/R;return {width,height,unproject,solidAngle:(x,y)=>{const t=Math.hypot(x-width/2,y-height/2)*k;return k*k*(t<1e-10?1:Math.sin(t)/t);},above:(x,y)=>Math.hypot(x-width/2,y-height/2)<=R};}\n if(type==='legacy'){if(width!==325||height!==530)throw new RangeError('Legacy crop requires 325x530');const k=Math.PI/2/270;return {width,height,unproject:(x,y)=>{const dx=162-x,dy=(y+30)/.8,r=Math.hypot(dx,dy);return {altDeg:90-r/270*90,azDeg:wrapDeg(Math.atan2(dx,dy)/DEG)};},solidAngle:(x,y)=>{const t=Math.hypot(x-162,(y+30)/.8)*k;return k*k/.8*(t<1e-10?1:Math.sin(t)/t);},above:(x,y)=>Math.hypot(x-162,(y+30)/.8)<=270};}\n throw new RangeError('Unknown sky projection');\n}\n/** Single site-height owner for stellar astrometry, atmosphere and illumination.\n * Missing weather elevation inherits the observer; contradictory explicit values fail. */\nfunction resolveSkyInputs(observer,atmosphere={}){\n if(!observer||typeof observer!=='object')throw new TypeError('Observer is required');\n if(!atmosphere||typeof atmosphere!=='object')throw new TypeError('Atmosphere must be an object');\n const site=observer.heightM??observer.elevationM??atmosphere.elevationM??0;\n finite(site,'site elevation metres',-500,10000);\n if(observer.heightM!=null&&observer.elevationM!=null&&observer.heightM!==observer.elevationM)throw new RangeError('Conflicting observer elevations');\n if(atmosphere.elevationM!=null&&atmosphere.elevationM!==site)throw new RangeError('Observer and atmospheric elevation disagree');\n return {observer:{...observer,heightM:site},atmosphere:normaliseAtmosphere(atmosphere.elevationM===site?atmosphere:{...atmosphere,elevationM:site})};\n}\nfunction renderPhysicalSky(sources,{observer,view={},atmosphere={},physicalState=null,dpr=1,nominalExposure=24,autoExposure=true,opticalPreset='reference',response='CIE1931',cloudAt=null,displayTransmissionAt=null,reducedMotion=true,scintillation={},backgroundStepCss=6,diffuse=null}={}){\n finite(dpr,'DPR',.5,4);finite(nominalExposure,'nominal exposure',0,100000);finite(backgroundStepCss,'background sample step CSS',1,16);\n const mapping=skyProjection(view),width=mapping.width,height=mapping.height,w=Math.round(width*dpr),h=Math.round(height*dpr);if(w*h>8000000)throw new RangeError('Reference raster exceeds memory budget');\n if(diffuse!=null&&diffuse!==false&&diffuse.enabled!==false&&w*h>2097152)throw new RangeError('Physical diffuse raster exceeds 2,097,152-pixel budget');\n const resolved=resolveSkyInputs(observer,atmosphere);observer=resolved.observer;const a=resolved.atmosphere,state=physicalState??physicalSkyState(observer);\n if(physicalState&&(physicalState.utcMs!==observer.utcMs||typeof physicalState.source!=='string'||!physicalState.source.trim()))throw new RangeError('External physical sky state requires matching UTC and source provenance');\n const diffuseModel=diffuse!=null&&diffuse!==false&&diffuse.enabled!==false?createDiffuseTransport(diffuse,{observer,atmosphere:a,state,cloudAt}):null;\n if(diffuseModel&&!['V-monochrome','CIE1931'].includes(response))throw new RangeError('Unknown physical response model');\n const sky=createSkyModel(state,a,{cloudAt,...(diffuseModel?{residualNight:diffuseModel.residualNight}:{})}),gx=Math.ceil(width/backgroundStepCss),gy=Math.ceil(height/backgroundStepCss),grid=new Float64Array((gx+1)*(gy+1)*3);\n for(let j=0;j<=gy;j++)for(let i=0;i<=gx;i++){const x=i*width/gx,y=j*height/gy;if(!mapping.above(x,y))continue;const direction=mapping.unproject(x,y),sample=sky.sample(direction),omega=mapping.solidAngle(x,y),off=(j*(gx+1)+i)*3;for(let c=0;c<3;c++)grid[off+c]=(response==='V-monochrome'?sample.luminance:sample.rgb[c])*omega/V_ZERO_ILLUMINANCE_LUX;}\n const background=new Float64Array(w*h*3),densityScale=diffuseModel?width/w*height/h*dpr*dpr:1;let meanY=0,skyPixels=0;\n for(let j=0;j<h;j++)for(let i=0;i<w;i++){const x=diffuseModel?(i+.5)*width/w:(i+.5)/dpr,y=diffuseModel?(j+.5)*height/h:(j+.5)/dpr;if(!mapping.above(x,y))continue;const u=x/width*gx,v=y/height*gy,ix=Math.min(gx-1,Math.floor(u)),iy=Math.min(gy-1,Math.floor(v)),tx=u-ix,ty=v-iy,off=(j*w+i)*3,tl=(iy*(gx+1)+ix)*3,bl=tl+(gx+1)*3;\n  for(let c=0;c<3;c++)background[off+c]=(grid[tl+c]*(1-tx)+grid[tl+3+c]*tx)*(1-ty)+(grid[bl+c]*(1-tx)+grid[bl+3+c]*tx)*ty;\n  if(diffuseModel)for(let c=0;c<3;c++)background[off+c]*=densityScale;\n  meanY+=.2126*background[off]+.7152*background[off+1]+.0722*background[off+2];skyPixels++;\n }\n let diffuseRaster=null,totalBackground=background;\n if(diffuseModel){\n  diffuseRaster=renderDiffuseLayer(diffuseModel,mapping,{widthPx:w,heightPx:h,dpr,displayTransmissionAt});totalBackground=new Float64Array(background.length);\n  for(let i=0;i<background.length;i++){totalBackground[i]=background[i]+diffuseRaster.linear[i];if(i%3===0)meanY+=diffuseRaster.physicalLinear[i];}\n  skyPixels=diffuseRaster.skyPixelsEquivalent;\n }\n meanY/=Math.max(1,skyPixels);const effectiveExposure=autoExposure?nominalExposure/(1+nominalExposure*meanY/.5):nominalExposure,diagnostics=[],moonVector=horizontalDirection(state.moon);\n const raster=renderStars(sources,{width,height,dpr,opticalPreset,response,utcMs:observer.utcMs,reducedMotion:true,scintillationAmplitude:0,\n  sourceVisibility:s=>diffuseModel?!diffuseModel.occulted(s):state.moon.altDeg+(state.moon.angularRadiusDeg??.25)<0||angularSeparation(horizontalDirection(s),moonVector)>(state.moon.angularRadiusDeg??.25),\n  fluxAt:s=>{const cloud=cloudTransmissionFor(s,a,cloudAt,state.utcMs),f=spectralStarFlux(s,s.altDeg,{}, {response,transportAt:lambda=>directTransmission(lambda,s.altDeg,a,cloud)}),displayMask=displayTransmissionAt?finite(displayTransmissionAt(s.x,s.y),'display mask',0,1):1,ds=diffuseModel?.sample(s),diffuseBackgroundY=ds?(ds.relativeV0PerSr??0)*mapping.solidAngle(s.x,s.y)*displayMask:0,backgroundY=sky.sample(s).luminance*mapping.solidAngle(s.x,s.y)/V_ZERO_ILLUMINANCE_LUX+diffuseBackgroundY,\n   visibility=displayVisibility(luminance(f.rgb)*displayMask,backgroundY,effectiveExposure),tw=scintillationFactor(s.id??s.hip,observer.utcMs/1000,s.altDeg,{...scintillation,reducedMotion});\n   diagnostics.push({id:s.id??s.hip,hip:s.hip,vmag:s.vmag,vFlux:f.vFlux,cloudTransmission:cloud,backgroundY,scintillationFactor:tw,...visibility,...(ds?{diffuseBackgroundY,backgroundComplete:ds.defined||displayMask===0,diffuseSourceDefined:ds.sourceDefined,diffuseEstimatedFraction:ds.estimatedFraction}:{})});return {...f,rgb:f.rgb.map(x=>x*tw)};},pixelTransmissionAt:displayTransmissionAt});\n const stellarLinear=raster.linear,linear=new Float64Array(stellarLinear.length);for(let i=0;i<linear.length;i++)linear[i]=stellarLinear[i]+totalBackground[i];\n let diffuseFields={};\n if(diffuseModel){\n  let increment=0,visiblePixels=0;const weights=[.2126,.7152,.0722];\n  for(let i=0;i<background.length;i+=3){let delta=0;for(let c=0;c<3;c++)delta+=weights[c]*(linearToSrgb(-Math.expm1(-effectiveExposure*totalBackground[i+c]))-linearToSrgb(-Math.expm1(-effectiveExposure*background[i+c])));increment+=delta;if(delta>=2/255)visiblePixels++;}\n  diffuseFields={skyBackgroundLinear:background,diffuseLinear:diffuseRaster.linear,diffusePhysicalLinear:diffuseRaster.physicalLinear,diffuseMasks:diffuseRaster.masks,diffuseState:{enabled:true,sourceId:diffuseModel.sourceId,sourceSha256:diffuseModel.sourceSha256,catalogueSha256:diffuseModel.catalogueSha256,utcMs:observer.utcMs,transportAssumption:diffuseModel.transportAssumption,colourModel:diffuseModel.colourModel,allowEstimates:diffuseModel.allowEstimates,samplesPerAxis:diffuseModel.samplesPerAxis,missingPixels:diffuseRaster.missingPixels,estimatedPixels:diffuseRaster.estimatedPixels,exposureComplete:diffuseRaster.missingPixels===0,exposureMetering:'sky plus direct diffuse BEFORE calendar/display mask; excludes point sources as in CP6',meanDisplayIncrement:increment/Math.max(1,skyPixels),displayVisiblePixels:visiblePixels,budget:diffuseRaster.budget,nightBudget:sky.nightBudget,frameWarnings:diffuseModel.frameWarnings},provisionalSourceDiagnostics:diagnostics.filter(d=>d.backgroundComplete===false).length};\n }\n const zenithBase=sky.sample({altDeg:90,azDeg:0}),zenithDiffuse=diffuseModel?.sample({altDeg:90,azDeg:0}),zenithSky=zenithDiffuse?{...zenithBase,atmosphericLuminance:zenithBase.luminance,diffuseLuminance:zenithDiffuse.luminance,luminanceIsLowerBound:!zenithDiffuse.defined,luminance:zenithBase.luminance+(zenithDiffuse.luminance??0),rgb:zenithBase.rgb.map(x=>x+(zenithDiffuse.luminance??0)),complete:zenithDiffuse.defined,diffuseEstimatedFraction:zenithDiffuse.estimatedFraction}:zenithBase;\n return {...raster,...diffuseFields,linear,stellarLinear,backgroundLinear:totalBackground,effectiveExposure,nominalExposure,meanBackgroundY:meanY,detectableSources:diagnostics.filter(x=>x.detectable&&x.backgroundComplete!==false).length,sourceDiagnostics:diagnostics,physicalState:state,atmosphere:a,zenithSky,skyModels:diffuseModel?{...sky.models,diffuse:'registered V starlight; one effective-V direct transport + physical occultation'}:sky.models,modelWarnings:diffuseModel?[...sky.warnings,diffuseModel.transportAssumption,'Diffuse output is a neutral V-equivalent channel; source estimates/absences retained','No diffuse in-scattering or independently calibrated nonstellar night spectrum']:sky.warnings,solarNodes:sky.solarNodeCount(),representation:'V-anchored stellar flux + photopic-equivalent sky radiance in CSS-pixel solid angle; encode once'};\n}\n\n// real-sky/core/integration/physical-sky-bridge.mjs\n/** Local integration seam, not an applied actual-widget patch. Caller owns accepted clock,\n * location and scheduling. No timers, geolocation, cloud fetch or scene-ready writes here. */\n\n\n\nclass PhysicalSkyBridge{\n constructor(catalogue){this.controller=new SkyController(catalogue);this.last=null;}\n render(observer,{sceneIdentity=null,view={type:'camera',width:325,height:530},...appearance}={}){\n  try{\n   if(appearance.diffuse&&appearance.diffuse.enabled!==false&&appearance.diffuse.binding?.catalogue!==this.controller.catalogue)throw new TypeError('Emitter catalogue does not match the verified diffuse catalogue binding');\n   const inputs=resolveSkyInputs(observer,appearance.atmosphere??{});observer=inputs.observer;\n   const project=view.type==='allsky'?h=>projectAllSky(h,view):view.type==='legacy'?projectWidgetDome:h=>projectPerspective(h,view);\n   const scene=this.controller.update(observer,{sceneIdentity,project});\n   if(scene.status!=='ready')return this.last={status:scene.status,sceneIdentity,utcMs:observer.utcMs,error:scene.error,raster:null};\n   return this.last={status:'ready',sceneIdentity,utcMs:observer.utcMs,observer,raster:renderPhysicalSky(scene.sources,{...appearance,atmosphere:inputs.atmosphere,observer,view})};\n  }catch(e){return this.last={status:'unavailable',sceneIdentity,utcMs:observer?.utcMs,error:String(e.message??e),raster:null};}\n }\n}\n\n// real-sky/core/src/diffuse-assets.mjs\n/** CP7.5: bounded, content-addressed diffuse admission and asynchronous selection.\n * The trusted shipped manifest hash pins runtime bytes; it is NOT a new signature\n * authenticating Gaia. Provenance/admission remain in the retained CP7.1\u20137.3 record.\n * No observer, camera, atmosphere or rendered frame is cached here.\n */\n\n\n\nconst DA_SOURCE='69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446';\nfunction daFreeze(x){if(x&&typeof x==='object'&&!Object.isFrozen(x)){for(const v of Object.values(x))daFreeze(v);Object.freeze(x);}return x;}\nfunction daHash(text){return sha256Hex(new TextEncoder().encode(text));}\nfunction daCheckText(text,descriptor,label){if(typeof text!=='string')throw new TypeError(label+' must be exact UTF-8 text');const b=new TextEncoder().encode(text);if(b.byteLength!==descriptor.bytes)throw new RangeError(label+' byte size mismatch');if(sha256Hex(b)!==descriptor.sha256)throw new TypeError(label+' content hash mismatch');}\nfunction daDescriptor(d,path,nside){if(!d||d.path!==path||!/^[0-9a-f]{64}$/.test(d.sha256??'')||!Number.isSafeInteger(d.bytes)||d.bytes<1||d.bytes>12000000)throw new TypeError('Invalid pinned asset descriptor');if(nside&&(d.nside!==nside||typeof d.id!=='string'||!d.id.length))throw new TypeError('Tier grid/identity mismatch');}\nfunction parseDiffuseManifest(text,expectedSha256){\n if(typeof text!=='string'||text.length>65536||!/^[0-9a-f]{64}$/.test(expectedSha256??'')||daHash(text)!==expectedSha256)throw new TypeError('Diffuse manifest hash mismatch');\n const m=JSON.parse(text);if(m.schema!=='salah-real-sky/diffuse-runtime-manifest/1'||m.sourceSha256!==DA_SOURCE)throw new TypeError('Unsupported diffuse manifest version/source');\n daDescriptor(m.catalogue,'data/bright-stars.json');\n if(!m.assets||Object.keys(m.assets).sort().join(',')!=='128,32,64')throw new TypeError('Expected exactly three runtime tiers');\n for(const tier of ['32','64','128'])daDescriptor(m.assets[tier],'data/registered-starlight/V-nside'+tier+'.json',Number(tier));\n return daFreeze(m);\n}\nclass DiffuseAssetStore{\n #cache=new Map();#serial=0;#controller=null;#disposed=false;#state;#text;\n constructor(manifestText,expectedManifestSha256,catalogueText){\n  this.manifest=parseDiffuseManifest(manifestText,expectedManifestSha256);daCheckText(catalogueText,this.manifest.catalogue,'catalogue');\n  this.catalogue=daFreeze(validateCatalogue(JSON.parse(catalogueText)));this.#text=catalogueText;\n  this.#state=Object.freeze({status:'idle',generation:0,tier:null,binding:null,error:null});\n  Object.defineProperty(this,'manifest',{writable:false,configurable:false});Object.defineProperty(this,'catalogue',{writable:false,configurable:false});\n }\n get snapshot(){return this.#state;}\n get cacheEntries(){return this.#cache.size;}\n async load(tier,readText,{reload=false}={}){\n  if(this.#disposed)return this.#state;\n  const generation=++this.#serial;this.#controller?.abort();const control=new AbortController();this.#controller=control;\n  tier=String(tier);this.#state=Object.freeze({status:'loading',generation,tier,binding:null,error:null});\n  try{\n   const d=this.manifest.assets[tier];if(!d)throw new RangeError('Unsupported diffuse tier');\n   if(typeof readText!=='function'||typeof reload!=='boolean')throw new TypeError('Reader and boolean reload required');\n   if(reload)this.#cache.delete(d.sha256);\n   let binding=this.#cache.get(d.sha256),cacheHit=!!binding;\n   if(!binding){\n    const text=await readText(d.path,{signal:control.signal,maxBytes:d.bytes});\n    if(generation!==this.#serial||this.#disposed)return Object.freeze({status:'superseded',generation,tier,binding:null});\n    daCheckText(text,d,'diffuse tier '+tier);const asset=JSON.parse(text);\n    if(asset.grid?.nside!==d.nside||asset.id!==d.id)throw new TypeError('Manifest and decoded grid/identity disagree');\n    binding=bindRegisteredStarlight(this.#text,asset);\n   }\n   if(generation!==this.#serial||this.#disposed)return Object.freeze({status:'superseded',generation,tier,binding:null});\n   this.#cache.set(d.sha256,binding); // at most the three pinned manifest entries\n   return this.#state=Object.freeze({status:'ready',generation,tier,binding,cacheHit,error:null,assetSha256:d.sha256});\n  }catch(e){\n   if(generation!==this.#serial||this.#disposed)return Object.freeze({status:'superseded',generation,tier,binding:null});\n   return this.#state=Object.freeze({status:'unavailable',generation,tier,binding:null,error:String(e?.message??e)});\n  }\n }\n dispose(){if(this.#disposed)return;this.#disposed=true;this.#serial++;this.#controller?.abort();this.#controller=null;this.#cache.clear();this.#text='';this.#state=Object.freeze({status:'disposed',generation:this.#serial,tier:null,binding:null,error:null});}\n}\n/** Bounded streaming UTF-8 read. A host may replace this with its authorised local\n * loader; cancellation/generation checks remain in the store even if a loader ignores abort.\n */\nasync function readDiffuseAssetText(url,{signal,maxBytes=12000000}={}){\n if(!Number.isSafeInteger(maxBytes)||maxBytes<1||maxBytes>12000000)throw new RangeError('Asset byte budget required');\n const response=await fetch(url,{signal});if(!response.ok){await response.body?.cancel().catch(()=>{});throw new Error('Asset HTTP '+response.status);}\n const declared=response.headers.get('content-length');if(declared!==null&&Number(declared)>maxBytes){await response.body?.cancel().catch(()=>{});throw new RangeError('Asset exceeds byte budget');}\n if(!response.body)throw new Error('Asset response body missing');\n const reader=response.body.getReader(),decoder=new TextDecoder('utf-8',{fatal:true});let total=0,text='';\n try{for(;;){const {done,value}=await reader.read();if(done)break;total+=value.byteLength;if(total>maxBytes)throw new RangeError('Asset exceeds byte budget');text+=decoder.decode(value,{stream:true});}text+=decoder.decode();return text;}\n catch(e){await reader.cancel().catch(()=>{});throw e;}finally{reader.releaseLock();}\n}\n\n// real-sky/core/src/diffuse-manifest-pin.mjs\n// Generated by tools/build_cp75_manifest.py. Integrity anchor, not an upstream signature.\nconst DIFFUSE_MANIFEST_SHA256=\"630f169f30b617d947b5e3199eb854e8027a34540dde008da57b925577b777f6\";\n\n// real-sky/core/integration/resilient-sky-bridge.mjs\n/** CP7.5 reference host wrapper; NOT actual-widget readiness integration.\n * A failed requested diffuse tier yields a NEW CP6 frame at the accepted observer.\n * Invalid physics/observer is never rescued by relabelling it an asset failure.\n */\n\n\nclass ResilientPhysicalSkyBridge{\n #store;#base;#bridges=new WeakMap();\n constructor(store){if(!(store instanceof DiffuseAssetStore))throw new TypeError('Verified diffuse asset store required');this.#store=store;this.#base=new PhysicalSkyBridge(store.catalogue);this.last=null;}\n render(observer,options={}){\n  const state=this.#store.snapshot,wanted=options.diffuse!=null&&options.diffuse!==false&&options.diffuse.enabled!==false;\n  const active=wanted&&state.status==='ready',binding=active?state.binding:null;let bridge=this.#base;\n  if(active){bridge=this.#bridges.get(binding);if(!bridge){bridge=new PhysicalSkyBridge(binding.catalogue);this.#bridges.set(binding,bridge);}}\n  const diffuse=active?{...options.diffuse,binding}:{enabled:false};\n  const result=bridge.render(observer,{...options,diffuse});\n  return this.last={...result,diffuseAsset:{mode:active?'registered':wanted?'cp6-fallback':'disabled',status:state.status,tier:state.tier,generation:state.generation,assetSha256:state.assetSha256??null,error:state.error??null,cacheEntries:this.#store.cacheEntries}};\n }\n}\n\n// real-sky/core/src/reference-engine.mjs\n/** Serializable CP7.5 reference engine shared by worker and explicit main-thread fallback.\n * Callback modes here are declared test scenarios, not live weather or a second mask owner.\n */\n\n\n\nclass ReferenceSkyEngine{\n #pack;#store;#bridge;#loadKey=null;#disposed=false;\n constructor(pack){this.#pack=pack;this.#store=new DiffuseAssetStore(pack.manifestText,DIFFUSE_MANIFEST_SHA256,pack.catalogueText);this.#bridge=new ResilientPhysicalSkyBridge(this.#store);}\n async render(job){\n  if(this.#disposed)throw new Error('Reference engine disposed');\n  const start=performance.now(),fault=job.assetFault??'none',revision=job.assetRevision??0;\n  if(!['none','missing','corrupt','wrong-version'].includes(fault)||!Number.isSafeInteger(revision)||revision<0)throw new TypeError('Invalid asset scenario/revision');\n  if(typeof job.calendarMask!=='boolean'||typeof job.cloudmap!=='boolean')throw new TypeError('Explicit boolean mask/cloud modes required');\n  const options={...job.options},wanted=options.diffuse!=null&&options.diffuse!==false&&options.diffuse.enabled!==false;\n  if(wanted){\n   const key=String(job.tier)+'/'+fault+'/'+revision;\n   if(key!==this.#loadKey||this.#store.snapshot.status!=='ready'){\n    const reload=this.#loadKey!==null&&(fault!=='none'||this.#loadKey.split('/')[1]!=='none'||Number(this.#loadKey.split('/')[2])!==revision);\n    await this.#store.load(job.tier,async()=>{\n     if(fault==='missing')throw new Error('Deliberate missing diffuse asset drill');\n     const text=this.#pack.assetTexts?.[String(job.tier)];\n     if(typeof text!=='string')throw new Error(this.#pack.assetErrors?.[String(job.tier)]??'Requested diffuse asset unavailable');\n     if(fault==='corrupt')return text.slice(0,-1);\n     if(fault==='wrong-version'){const a=JSON.parse(text);a.schema='unsupported/2';return JSON.stringify(a);}\n     return text;\n    },{reload});this.#loadKey=key;\n   }\n  }\n  const loadEnd=performance.now(),v=options.view;\n  if(job.cloudmap)options.cloudAt=(h,utcMs)=>h.azDeg>=180?.08:1;\n  if(job.calendarMask)options.displayTransmissionAt=(x,y)=>Math.hypot(x-v.width*.72,y-v.height*.26)<24?0:1;\n  const result=this.#bridge.render(job.observer,options);\n  return {...result,timings:{assetLoadMs:loadEnd-start,renderMs:performance.now()-loadEnd,totalMs:performance.now()-start},engineContract:'serialisable accepted inputs; no rendered-frame cache'};\n }\n dispose(){if(this.#disposed)return;this.#disposed=true;this.#store.dispose();this.#pack=null;this.#bridge.last=null;}\n}\n/** Shared ArrayBuffer aliases must appear once in a transfer list. Metadata is cloned,\n * while these owned buffers are moved, not copied, to the accepting UI. */\nfunction rasterTransferables(result){\n const seen=new Set(),out=[];\n function walk(v){if(v===null||typeof v!=='object')return;if(ArrayBuffer.isView(v)){if(v.buffer instanceof ArrayBuffer&&!seen.has(v.buffer)){seen.add(v.buffer);out.push(v.buffer);}return;}for(const x of Object.values(v))walk(x);}\n walk(result?.raster);return out;\n}\n\n// real-sky/native-contract.mjs\n/** CP8 native boundary. All astronomical time comes from the accepted host snapshot. */\nfunction nativeFinite(v,name,min=-Infinity,max=Infinity){if(typeof v!=='number'||!Number.isFinite(v)||v<min||v>max)throw new RangeError('Invalid native '+name);return v;}\nfunction nativeIdentity(s){\n if(!s||typeof s!=='object')throw new TypeError('Native snapshot required');\n nativeFinite(s.utcMs,'UTC',-8640000000000000,8640000000000000);nativeFinite(s.lat,'latitude',-90,90);nativeFinite(s.lon,'longitude',-180,180);nativeFinite(s.heightM,'height',-500,10000);\n if(typeof s.sceneIdentity!=='string'||!s.sceneIdentity||!Number.isSafeInteger(s.generation)||s.generation<0)throw new TypeError('Accepted native scene/generation required');\n const c=s.camera??{};nativeFinite(c.azDeg,'camera azimuth',-360,360);nativeFinite(c.altDeg,'camera altitude',-90,90);nativeFinite(c.fovYDeg,'camera field of view',10,150);nativeFinite(c.rollDeg,'camera roll',-180,180);\n return JSON.stringify([s.sceneIdentity,s.generation,s.lat,s.lon,s.heightM,s.camera,s.weather,s.lp,s.reducedMotion,s.allowEstimates!==false,s.units,s.tz??null,s.timeScale??1,s.elevationSource??null,s.elevationOwner??null]);\n}\nfunction nativeJob(s,physical=false){\n const identity=nativeIdentity(s),w=s.weather;\n const visibility=typeof w?.vis==='number'&&Number.isFinite(w.vis)?Math.max(0,w.vis):20000;\n // Visibility is not an aerosol optical-depth measurement: this bounded mapping is an explicit scenario assumption.\n const aerosol=physical?.06+.3*Math.max(0,Math.min(1,1-visibility/20000)):.06;\n const temperature=typeof w?.temp==='number'&&Number.isFinite(w.temp)?(s.units==='f'?(w.temp-32)*5/9:w.temp):10;\n const lp=typeof s.lp==='number'&&Number.isFinite(s.lp)?Math.max(0,Math.min(1,s.lp)):0;\n return {observer:{utcMs:s.utcMs,latDeg:s.lat,lonDeg:s.lon,heightM:s.heightM,temperatureC:Math.max(-90,Math.min(70,temperature)),pressureHpa:0},\n native:{identity,generation:s.generation,sceneIdentity:s.sceneIdentity,weatherSource:w?.src??'unavailable',weatherAccepted:!!w,cloudOwner:physical?'native-linear-foreground':'native-interim-overlay',assumptions:{elevation:s.elevationSource??'explicit caller elevation; provenance not supplied',aerosol:'0.06 + 0.30*(1-visibility/20000), clamped; not measured AOD',pressure:'standard atmosphere from accepted elevation; astrometry remains geometric',localLight:'LPOLL \u00d7 0.003 cd/m\u00b2 assumed non-stellar local light',cloud:'native painted total opacity, not measured optical depth'}},\n tier:128,\n options:{sceneIdentity:identity,view:{type:'camera',width:325,height:530,...s.camera},dpr:1,nominalExposure:24,autoExposure:true,backgroundStepCss:8,reducedMotion:!!s.reducedMotion,scintillation:{strength:0},\n atmosphere:{elevationM:s.heightM,aerosolTau550:aerosol,cloudTransmission:1,cloudGlowCdM2:0,lightPollutionCdM2:physical?lp*.003:0},\n diffuse:physical?{enabled:true,allowEstimates:s.allowEstimates!==false,samplesPerAxis:2,residualNight:{kind:'assumed-nonstellar-residual',zenithCdM2:.00014,source:'CP8 explicit non-stellar residual assumption; not measured airglow',includesRegisteredStarlight:false}}:{enabled:false}}};\n}\n// A numerical frame older than 30 accepted-UTC seconds is unavailable, not a current sky.\nfunction nativeResultCurrent(job,current){try{return job.native.identity===nativeIdentity(current)&&Number.isFinite(job.observer.utcMs)&&Math.abs(current.utcMs-job.observer.utcMs)<=30000;}catch{return false;}}\n/** Native calendar mask removes only direct astronomical light, never atmospheric sky. */\nfunction nativeCalendarComposite(raster,mask=null){\n const out=new Float64Array(raster.linear.length),sky=raster.skyBackgroundLinear??raster.backgroundLinear,diffuse=raster.diffusePhysicalLinear;\n if(mask&&mask.length!==raster.width*raster.height)throw new RangeError('Calendar mask dimensions');\n for(let i=0;i<out.length;i++){const m=mask?mask[Math.floor(i/3)]:1;out[i]=sky[i]+(raster.stellarLinear[i]+(diffuse?.[i]??0))*m;}return out;\n}\n\n/** Map logical physics pixels through actual CSS bounds and the native SVG screen transform. */\nfunction nativeDiscMask(width,height,rect,m,radius){\n // DOMMatrix coefficients are native getters. Read each exactly once; all\n // arithmetic and the one-pixel antialias ramp are identical to the CP8.3 mask.\n const {a,b,c,d,e,f}=m,det=a*d-b*c;if(!Number.isFinite(det)||Math.abs(det)<1e-12)throw new RangeError('Singular native Moon transform');\n const mask=new Float64Array(width*height),sx=rect.width/width,sy=rect.height/height;\n const aa=Math.max(1e-9,.5*(Math.hypot(d*sx,b*sx)+Math.hypot(c*sy,a*sy))/Math.abs(det));\n for(let y=0;y<height;y++)for(let x=0;x<width;x++){\n  const px=rect.left+(x+.5)*sx-e,py=rect.top+(y+.5)*sy-f;\n  const xx=(d*px-c*py)/det,yy=(-b*px+a*py)/det;\n  mask[y*width+x]=Math.max(0,Math.min(1,(Math.hypot(xx,yy)-radius)/aa+.5));\n }\n return mask;\n}\n\n// real-sky/native-engine.mjs\n\n\n\n\n\n/** Real CP7 renderer with native inputs; none of the reference viewer's diagnostic masks. */\nclass NativeSkyEngine{\n constructor(pack){this.pack=pack;this.store=new DiffuseAssetStore(pack.manifestText,DIFFUSE_MANIFEST_SHA256,pack.catalogueText);this.bridge=new ResilientPhysicalSkyBridge(this.store);this.loaded=false;}\n async render(job){\n  const start=performance.now();if(!this.pack)throw new Error('Native engine disposed');\n  if(job.options.atmosphere.cloudTransmission!==1||job.options.atmosphere.cloudGlowCdM2!==0)throw new Error('Native foreground owns cloud transmission and colour exactly once');\n  if(job.options.diffuse.enabled&&!this.loaded){await this.store.load(job.tier,async()=>{const t=this.pack.assetTexts?.[String(job.tier)];if(typeof t!=='string')throw new Error('Native diffuse asset missing');return t;});this.loaded=true;}\n  const begin=performance.now(),result=this.bridge.render(job.observer,job.options);\n  let sources=[];\n  if(result.status==='ready')sources=projectCatalogue(this.store.catalogue,job.observer,h=>projectPerspective(h,job.options.view)).filter(s=>s.visible&&s.emission?.enabled!==false).map(s=>({id:s.id,hip:s.hip,hygId:s.hygId,name:s.properName??s.name??null,vmag:s.vmag,x:s.x,y:s.y,altDeg:s.altDeg,azDeg:s.azDeg}));\n  return {...result,native:job.native,sources,timings:{assetMs:begin-start,renderMs:performance.now()-begin,totalMs:performance.now()-start},catalogue:{id:this.store.catalogue.id,records:this.store.catalogue.stars.length,emitters:this.store.catalogue.stars.filter(s=>s.emission?.enabled!==false).length,sha256:this.store.manifest.catalogue.sha256}};\n }\n dispose(){this.store.dispose();this.pack=null;this.bridge.last=null;}\n}\n\nlet nativeWorkerEngine=null;\nself.onmessage=async e=>{const m=e.data;try{if(m.kind==='boot'){nativeWorkerEngine=new NativeSkyEngine(m.pack);self.postMessage({kind:'ready'});}else if(m.kind==='render'){const result=await nativeWorkerEngine.render(m.job);self.postMessage({kind:'result',id:m.id,result},rasterTransferables(result));}}catch(e){self.postMessage({kind:'error',id:m.id,error:String(e.message??e)});}};\nself.addEventListener('unhandledrejection',e=>{self.postMessage({kind:'fatal',error:String(e.reason)});});\n",true),document.currentScript?.src);

})();
