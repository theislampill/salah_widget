import {DEG,finite,wrapDeg,observationFrame} from './astronomy.mjs';
import {cameraGeometry} from './projection.mjs';
import {diffuseRayToMap} from './diffuse-map.mjs';
/** Admitted, corrected V-component. ICRS axes share the existing mean-J2000
 * geometry within a declared 0.1-arcsecond frame-bias allowance. No epoch-2016
 * precession, star-dependent proper motion, atmosphere or display encoding here. */
const RS_SHA='69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446';
const RS_F0=3.62708e-11;
function rsN(n){if(!Number.isInteger(n)||n<1||n>256||(n&(n-1)))throw new RangeError('NESTED nside must be a power of two in 1..256');return n;}
export function healpixIndex(nside,raDeg,decDeg){
 const n=rsN(nside);finite(raDeg,'ICRS longitude');finite(decDeg,'ICRS latitude',-90,90);
 const tt=wrapDeg(raDeg)/90,z=Math.sin(decDeg*DEG),za=Math.abs(z);let f,ix,iy;
 if(za<=2/3){const jp=Math.floor(n*(.5+tt-.75*z)),jm=Math.floor(n*(.5+tt+.75*z)),fp=Math.floor(jp/n),fm=Math.floor(jm/n);f=fp===fm?(fp%4)+4:fp<fm?fp%4:(fm%4)+8;ix=jm%n;iy=n-(jp%n)-1;}
 else{const nt=Math.min(3,Math.floor(tt)),tp=tt-nt,t=n*Math.sqrt(3*(1-za)),a=Math.min(n-1,Math.floor(tp*t)),b=Math.min(n-1,Math.floor((1-tp)*t));f=z>=0?nt:nt+8;ix=z>=0?n-b-1:a;iy=z>=0?n-a-1:b;}
 let p=f*n*n;for(let bit=0;(1<<bit)<n;bit++)p|=((ix>>bit)&1)<<(2*bit)|((iy>>bit)&1)<<(2*bit+1);return p;
}
export function healpixCentre(nside,pixel){
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
export function createRegisteredStarlightSampler(asset,{catalogueSha256=null}={}){
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
export function renderRegisteredStarlight(sampler,observer,view,{dpr=1,samplesPerAxis=1,allowEstimates=true,filter='linear'}={}){
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
