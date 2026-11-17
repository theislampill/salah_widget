/* R0041 (issue 143), owner decision of 2026-11-17: the receiver-independent PHASE DISC.
 * A producer, never a presenter: it returns one message of the shape the Moon runtime's adopt() already takes
 * and touches nothing else. It is the accepted V5 initial operator (moon-initial.mjs render) applied to a smooth
 * sphere of the mean lunar radius with ONE uniform material: the same canonical camera, 16-sample finite Sun,
 * Lommel-Seeliger/Lambert law, analytic Lambert Earth integral, V5 display mapping, calendar token and box coding.
 * It reads no receiver bytes, no terrain normals or horizons, no albedo map, no clock, no ephemeris and no document,
 * and it has no retry state. It invents no lunar detail: the surface carries no markings at all. The Moon runtime
 * uses it only while the start-up receiver cannot serve the current scene (moon-native.mjs initialPresentation).
 * This is not the deprecated legacy renderer (ISM-MOON-001): none of its maps, law, canvas or write path is used. */
// Disc mean of the accepted V5 receiver material (linear, before the material gain); a statistic of accepted data,
// recomputed from moon/assets/initial-receivers.bin by moon/tests/r0041-phase-disc.test.cjs (R41-PD-ALB).
const PHASE_DISC_MATERIAL=Object.freeze([.413235,.393423,.384153]);
function renderPhaseDisc(scene,consumeTables){
 // No substitution for a rotated/physical reference camera or another profile (the receiver's own admission).
 if(scene?.mode!=='calendar-canonical'||scene.profile?.mode!=='calendar'||JSON.stringify(scene.basis)!=='[0,1,0,0,0,1,1,0,0]'||scene.distance!==384400||scene.extent!==1.08||scene.tilt!==0||scene.earth?.join(',')!=='384400,0,0')throw new Error('Phase disc unsupported scene');
 const profile=admitProfile(scene.profile),s=scene.sun,N=scene.size;
 if(!Number.isInteger(N)||N<128||N>540||!Array.isArray(s)||s.length!==3||!s.every(Number.isFinite)||Math.abs(Math.hypot(...s)-1)>1e-10||s[2]!==0||!Number.isFinite(scene.fraction)||Math.abs((1+s[0])/2-scene.fraction)>1e-10||typeof scene.waxing!=='boolean')throw new Error('Phase disc phase geometry');
 const started=performance.now(),count=N*N,linear=new Float32Array(count*3),coverage=new Float32Array(count),flat=new Float32Array(count*3);
 // The receiver's own projection: rays from the Earth point through the canonical image plane, here onto a sphere.
 const D=384400,R=1737.4,half=1.08*R/Math.sqrt((D-R)*(D+R)),gain=.31873105385527434,material=PHASE_DISC_MATERIAL;
 const rule=[];for(let j=0;j<2;j++)for(let i=0;i<8;i++){const t=(1+(j?1:-1)/Math.sqrt(3))/2,a=(i+.5*(j%2))*2*Math.PI/8;rule.push([t,Math.cos(a),Math.sin(a),1/16]);}
 const rho=.266*Math.PI/180,cosmin=Math.cos(rho),normalizer=1-(1-cosmin)/2,sd=Float64Array.from(rule.flatMap(([t,c,q,w])=>{
  const ct=cosmin+t*(1-cosmin),st=Math.sqrt(1-ct*ct);return [s[0]*ct-s[1]*st*c,s[1]*ct+s[0]*st*c,st*q,w/normalizer];}));
 const disk=(nu,mu)=>.85*2*nu/(nu+mu)+.15*nu,m0=material[0]*gain,m1=material[1]*gain,m2=material[2]*gain;
 for(let y=0;y<N;y++)for(let x=0;x<N;x++){
  const u=2*(x+.5)/N-1,v=1-2*(y+.5)/N,k2=half*half*(u*u+v*v),q=D*D-(1+k2)*(D*D-R*R);if(q<0)continue;
  const i=y*N+x,j=3*i,t=(D-Math.sqrt(q))/(1+k2),py=t*u*half,pz=t*v*half,nx=(D-t)/R,ny=py/R,nz=pz/R,distance=t*Math.sqrt(1+k2),ax=t/distance,ay=-py/distance,az=-pz/distance;
  // Coverage is binary and complete inside the limb: an opaque body, lit or dark.
  coverage[i]=1;flat[j]=material[0];flat[j+1]=material[1];flat[j+2]=material[2];
  const mu=nx*ax+ny*ay+nz*az;if(mu<=0)continue;
  let sun=0;for(let k=0;k<sd.length;k+=4){const nu=nx*sd[k]+ny*sd[k+1]+nz*sd[k+2];if(nu>0)sun+=sd[k+3]*disk(nu,mu);}
  const ratio=6371/distance,delta=ratio*ratio/(1+Math.sqrt(1-ratio*ratio)),ce=Math.max(-1,Math.min(1,-ax*s[0]-ay*s[1]));
  const ear=2*delta*.434*((Math.sqrt(1-ce*ce)+(Math.PI-Math.acos(ce))*ce)/Math.PI)*(.85+.15*mu);
  mapInitialReceiver(linear,j,Math.fround(m0*sun)+Math.fround(m0*ear),Math.fround(m1*sun)+Math.fround(m1*ear),Math.fround(m2*sun)+Math.fround(m2*ear),profile);
 }
 const size=scene.outSize,table=prefixSurface({size:N,linear,coverage}),calendarLinear=calendarProxy(flat,coverage,linear),calendarTable=prefixSurface({size:N,linear:calendarLinear,coverage});
 const result={kind:'phase-disc',rgba:initialReceiverCodes(table,scene,size),width:size,height:size,scene:{...scene,size:N},surfaceLinear:linear,surfaceCoverage:coverage,surfaceSize:N,surfaceExtent:scene.extent,
  calendarLinear,calendarRgba:initialReceiverCodes(calendarTable,scene,size),
  physicalIdentity:'phase-disc/1|'+JSON.stringify([scene.sun,scene.profile,material]),profileIdentity:JSON.stringify(profile),
  diagnostics:{kernel:'v5-phase-disc/1',quality:{status:'phase-disc',solarSamples:16,earth:'Lambert sphere integral',scope:'uniform sphere of the mean lunar radius; no terrain, no albedo map, no lunar detail'},totalMs:0}};
 result.diagnostics.totalMs=performance.now()-started;
 if(consumeTables)consumeTables(table,calendarTable);
 return result;
}
