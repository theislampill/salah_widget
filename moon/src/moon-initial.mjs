/* Cold-start V5 receiver representation. This contains no phase image, UTC,
 * observer, previous document or accepted scene. Native supplies each current
 * scene. Full terrain and finite-source refinement remain worker-owned.
 *
 * This initial tier integrates 16 solar samples over precomputed V5 receivers
 * and a canonical-plane terrain horizon. Earth irradiance uses its analytic
 * Lambert sphere integral at each receiver; the full worker resolves its finite
 * angular spread, terrain occlusion and spatial/angular convergence. */
function createInitialMoon(bytes,pin){
 if(!(bytes instanceof Uint8Array)||bytes.length!==pin.bytes||bytes.length>4000000||assetDigest(bytes)!==pin.sha256)throw new Error('Initial Moon identity');
 const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),N=view.getUint16(4,true);
 if(view.getUint32(0,true)!==0x31494d53||N!==pin.size||N<128||N>540||pin.schema!=='moon-initial-receivers/1')throw new Error('Initial Moon schema');
 if(!Number.isSafeInteger(pin.records)||pin.records<1||pin.records>N*N)throw new Error('Initial Moon record count');
 const count=N*N,maskBytes=Math.ceil(count/8),material=new Float32Array(count*3),coverage=new Float32Array(count),records=new Float64Array(pin.records*9),indices=new Uint32Array(pin.records);
 const half=1.08*1737.4/Math.sqrt((384400-1737.4)*(384400+1737.4));let at=6+maskBytes,record=0;
 for(let i=0;i<count;i++)if(bytes[6+(i>>3)]&(1<<(i&7))){
  if(at+20>bytes.length)throw new Error('Initial Moon truncated record');
  const px=view.getFloat32(at,true),py=(384400-px)*(2*(i%N+.5)/N-1)*half,pz=(384400-px)*(1-2*(Math.floor(i/N)+.5)/N)*half;
  const nx=view.getInt16(at+4,true)/32767,ny=view.getInt16(at+6,true)/32767,nz=view.getInt16(at+8,true)/32767,norm=Math.hypot(nx,ny,nz);
  if(!Number.isFinite(px)||Math.abs(px)>1753||Math.abs(norm-1)>.001)throw new Error('Initial Moon receiver geometry');
  const rx=384400-px,ry=-py,rz=-pz,distance=Math.hypot(rx,ry,rz),ax=rx/distance,ay=ry/distance,az=rz/distance;
  const mu=(nx*ax+ny*ay+nz*az)/norm,ratio=6371/distance;
  for(let k=0;k<3;k++)material[3*i+k]=view.getUint16(at+10+k*2,true)/65535;
  if(record>=pin.records)throw new Error('Initial Moon record count');
  // Only the receiver terms used at presentation survive admission. Avoid a
  // per-receiver temporary object and the unused finite-Earth sampling basis.
  const r=9*record;records[r]=nx/norm;records[r+1]=ny/norm;records[r+2]=nz/norm;records[r+3]=mu;records[r+4]=ax;records[r+5]=ay;
  records[r+6]=view.getUint16(at+16,true)*Math.PI/65535;records[r+7]=view.getUint16(at+18,true)*Math.PI/65535;
  records[r+8]=ratio*ratio/(1+Math.sqrt(1-ratio*ratio));
  coverage[i]=1;indices[record++]=i;at+=20;
 }
 if(at!==bytes.length||record!==pin.records)throw new Error('Initial Moon record count');
 const rule=[];for(let j=0;j<2;j++)for(let i=0;i<8;i++){const t=(1+(j?1:-1)/Math.sqrt(3))/2,a=(i+.5*(j%2))*2*Math.PI/8;rule.push([t,Math.cos(a),Math.sin(a),1/16]);}
 const disk=(nu,mu)=>.85*2*nu/(nu+mu)+.15*nu;
 return Object.freeze({identity:Object.freeze({...pin}),render(scene){
  // No substitution for a rotated/physical reference camera or another profile.
  if(scene.mode!=='calendar-canonical'||scene.profile?.mode!=='calendar'||JSON.stringify(scene.basis)!=='[0,1,0,0,0,1,1,0,0]'||scene.distance!==384400||scene.extent!==1.08||scene.tilt!==0||scene.earth?.join(',')!=='384400,0,0')throw new Error('Initial Moon unsupported scene');
  const profile=admitProfile(scene.profile),s=scene.sun;
  if(!Array.isArray(s)||s.length!==3||!s.every(Number.isFinite)||Math.abs(Math.hypot(...s)-1)>1e-10||s[2]!==0||!Number.isFinite(scene.fraction)||Math.abs((1+s[0])/2-scene.fraction)>1e-10||typeof scene.waxing!=='boolean')throw new Error('Initial Moon phase geometry');
  const started=performance.now(),linear=new Float32Array(count*3);
  const rho=.266*Math.PI/180,cosmin=Math.cos(rho),normalizer=1-(1-cosmin)/2,sd=Float64Array.from(rule.flatMap(([t,c,q,w])=>{
   const ct=cosmin+t*(1-cosmin),st=Math.sqrt(1-ct*ct),x=s[0]*ct-s[1]*st*c,y=s[1]*ct+s[0]*st*c,z=st*q;
   return [x,y,z,w/normalizer,Math.atan2((scene.waxing?1:-1)*y,x)];
  }));
  for(let ri=0;ri<indices.length;ri++){
   const i=indices[ri],r=9*ri,nx=records[r],ny=records[r+1],nz=records[r+2],mu=records[r+3];if(mu<=0)continue;
   const ax=records[r+4],ay=records[r+5],horizon=records[r+6+(scene.waxing?1:0)],delta=records[r+8];
   let sun=0;
   for(let q=0;q<sd.length;q+=5){const nu=nx*sd[q]+ny*sd[q+1]+nz*sd[q+2];if(nu>0&&sd[q+4]<horizon)sun+=sd[q+3]*disk(nu,mu);}
   const cosEarthPhase=Math.max(-1,Math.min(1,-ax*s[0]-ay*s[1]));
   const earthPhase=(Math.sqrt(1-cosEarthPhase*cosEarthPhase)+(Math.PI-Math.acos(cosEarthPhase))*cosEarthPhase)/Math.PI;
   const ear=2*delta*.434*earthPhase*(.85+.15*mu);
   // Preserve the full engine's Float32 physical channel admission before V5.
   const j=3*i,m0=material[j]*.31873105385527434,m1=material[j+1]*.31873105385527434,m2=material[j+2]*.31873105385527434;
   mapInitialReceiver(linear,j,Math.fround(m0*sun)+Math.fround(m0*ear),Math.fround(m1*sun)+Math.fround(m1*ear),Math.fround(m2*sun)+Math.fround(m2*ear),profile);
  }
  const size=scene.outSize,table=prefixSurface({size:N,linear,coverage}),rgba=initialReceiverCodes(table,scene,size);
  const result={kind:'initial',rgba,width:size,height:size,scene:{...scene,size:N},surfaceLinear:linear,surfaceCoverage:coverage,surfaceSize:N,surfaceExtent:scene.extent,
   physicalIdentity:pin.sha256+'|'+JSON.stringify([scene.sun,scene.profile]),profileIdentity:JSON.stringify(profile),diagnostics:{kernel:'v5-receiver-initial/1',quality:{status:'initial-v5',solarSamples:16,earth:'Lambert sphere integral; finite angular spread pending',scope:'current canonical display; off-plane terrain and full convergence pending'},totalMs:performance.now()-started,receiverIdentity:pin.sha256}};
  const calendarLinear=calendarProxy(material,coverage,linear);
  result.calendarLinear=calendarLinear;result.calendarRgba=initialReceiverCodes(prefixSurface({size:N,linear:calendarLinear,coverage}),scene,size);
  result.diagnostics.totalMs=performance.now()-started;return result;
 }});
}

// Exactly the existing boxSurface/integral arithmetic, with the shared axis
// clipping/indices prepared once instead of sixteen times per output pixel.
// Only initial backing-image sampling uses this path. The full terrain worker,
// receiver fields, device-resolution join and approved body footprint are unchanged.
function initialReceiverCodes(table,scene,size){
 const N=table.size,scale=N/(scene.diameter*scene.extent),origin=N/2-size*scale/2,d=table.data,stride=table.stride;
 const axis=Array.from({length:size+1},(_,i)=>{
  const original=origin+i*scale,clipped=Math.max(0,Math.min(N,original)),index=Math.min(N-1,Math.floor(clipped));
  return {original,index,fraction:clipped-index};
 });
 const integralAt=(x,y,k)=>{
  const ix=x.index,iy=y.index,fx=x.fraction,fy=y.fraction;
  return d[4*(iy*stride+ix)+k]*(1-fx)*(1-fy)+d[4*(iy*stride+ix+1)+k]*fx*(1-fy)+d[4*((iy+1)*stride+ix)+k]*(1-fx)*fy+d[4*((iy+1)*stride+ix+1)+k]*fx*fy;
 };
 const rgba=new Uint8ClampedArray(size*size*4),c=new Float64Array(4);
 for(let y=0;y<size;y++)for(let x=0;x<size;x++){
  const x0=axis[x],x1=axis[x+1],y0=axis[y],y1=axis[y+1],area=(x1.original-x0.original)*(y1.original-y0.original);
  if(!Number.isFinite(area)||area<=0)throw new RangeError('Initial surface box');
  for(let k=0;k<4;k++)c[k]=Math.max(0,(integralAt(x1,y1,k)-integralAt(x0,y1,k)-integralAt(x1,y0,k)+integralAt(x0,y0,k))/area);
  if(c[3]>1+1e-8)throw new Error('Initial area coverage');const a=Math.min(1,c[3]),i=4*(y*size+x);
  for(let k=0;k<3;k++)rgba[i+k]=Math.floor(255*encodeSrgb(a?c[k]/a:0)+.5);rgba[i+3]=Math.floor(255*a+.5);
 }return rgba;
}

// Same V5 mapAdmitted arithmetic/order, with a previously admitted profile and
// caller-owned output. Avoid four tiny arrays per receiver in the first turn.
// This allocation optimisation never changes the worker's surface operator.
function mapInitialReceiver(out,i,r,g,b,p){
 const y=r*.2126+g*.7152+b*.0722;
 if(!Number.isFinite(y)||y<0)throw new Error('Initial Moon luminance');
 if(y===0){out[i]=out[i+1]=out[i+2]=0;return;}
 const t=-Math.expm1(-p.exposure*(y+p.lift*y/(y+p.knee))),d0=t*(r/y-1),d1=t*(g/y-1),d2=t*(b/y-1),hi=Math.max(d0,d1,d2),lo=Math.min(d0,d1,d2);
 const k=Math.min(1,hi>0?(1-t)/hi:1,lo<0?t/-lo:1);
 out[i]=Math.max(0,Math.min(1,t+k*d0));out[i+1]=Math.max(0,Math.min(1,t+k*d1));out[i+2]=Math.max(0,Math.min(1,t+k*d2));
}
