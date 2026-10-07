/** V5 surface-only donor. This module does NOT compute lunar terrain or ephemerides.
 * Linear physical inputs -> one luminance display mapping -> geometric coverage
 * -> linear-display area filtering -> explicitly linear background composition.
 */
const WEIGHTS=[.2126,.7152,.0722];
const KEYS=['schema','profile_id','mode','exposure','lift','knee','colour_basis','gamut'].sort();
const finiteNumber=x=>typeof x==='number'&&Number.isFinite(x);
const Y=x=>x[0]*WEIGHTS[0]+x[1]*WEIGHTS[1]+x[2]*WEIGHTS[2];
function admitProfile(p){
 if(!p||typeof p!=='object'||Array.isArray(p)||Object.keys(p).sort().join('|')!==KEYS.join('|'))throw new TypeError('exact V5 profile keys required');
 if(p.schema!=='lunar-presentation/5'||!['calendar','reference'].includes(p.mode)||typeof p.profile_id!=='string'||!p.profile_id||p.colour_basis!=='linear-sRGB'||p.gamut!=='luminance-preserving-neutral-axis')throw new RangeError('profile contract');
 if(!['exposure','lift','knee'].every(k=>finiteNumber(p[k]))||p.exposure<=0||p.lift<0||p.knee<=0||(p.mode==='reference'&&p.lift!==0))throw new RangeError('display parameters');
 return {...p};
}
function tone(y,p){return -Math.expm1(-p.exposure*(y+p.lift*y/(y+p.knee)));}
function toneY(y,profile){const p=admitProfile(profile);if(!finiteNumber(y)||y<0)throw new RangeError('luminance');return tone(y,p);}
function mapAdmitted(c,p){
 const y=Y(c);if(!Number.isFinite(y))throw new RangeError('luminance overflow');if(y===0)return [0,0,0];
 const t=tone(y,p),d=c.map(x=>t*(x/y-1));const hi=Math.max(...d),lo=Math.min(...d);
 const k=Math.min(1,hi>0?(1-t)/hi:1,lo<0?t/-lo:1);
 const r=d.map(x=>t+k*x);
 if(r.some(x=>x< -2e-14||x>1+2e-14))throw new Error('gamut solve failed');
 return r.map(x=>Math.max(0,Math.min(1,x)));
}
function mapSurfaceRgb(solar,earth,profile){
 const p=admitProfile(profile);
 if(solar?.length!==3||earth?.length!==3||![...solar,...earth].every(x=>finiteNumber(x)&&x>=0))throw new RangeError('finite nonnegative RGB required');
 const c=Array.from(solar,(x,i)=>x+earth[i]);if(c.some(x=>!Number.isFinite(x)))throw new RangeError('source overflow');
 return mapAdmitted(c,p);
}
const decodeSrgb=x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4;
const encodeSrgb=x=>x<=.0031308?12.92*x:1.055*x**(1/2.4)-.055;
function weights(n,out,scale,centre){
 const rows=[];
 for(let j=0;j<out;j++){
  const lo=(j-out/2)*scale+centre,hi=lo+scale,a=[];
  for(let i=Math.max(0,Math.floor(lo));i<Math.min(n,Math.ceil(hi));i++){
   const w=Math.max(0,Math.min(hi,i+1)-Math.max(lo,i))/scale;if(w>0)a.push([i,w]);
  }rows.push(a);
 }return rows;
}
function renderSurfaceFrame(frame){
 const {width:W,height:H,solar,earth,coverage:a,profile,outSize:N,scale,centreX:cx,centreY:cy,background=[0,0,0]}=frame;
 const p=admitProfile(profile);
 if(![W,H,N].every(x=>Number.isSafeInteger(x)&&x>0&&x<=4096)||![scale,cx,cy].every(finiteNumber)||scale<=0)throw new RangeError('sampling dimensions');
 const count=W*H;if(solar?.length!==count*3||earth?.length!==count*3||a?.length!==count)throw new RangeError('field shape');
 if(background?.length!==3||!Array.from(background).every(x=>finiteNumber(x)&&x>=0&&x<=1))throw new RangeError('background colour');
 const src=new Float64Array(count*3),alpha=new Float64Array(count);
 for(let i=0;i<count;i++){
  if(!finiteNumber(a[i])||a[i]< -1e-12||a[i]>1+1e-12)throw new RangeError('coverage');alpha[i]=Math.max(0,Math.min(1,a[i]));
  const c=[0,0,0];for(let k=0;k<3;k++){const x=solar[3*i+k],y=earth[3*i+k];if(!finiteNumber(x)||!finiteNumber(y)||x<0||y<0||!Number.isFinite(x+y))throw new RangeError('light');c[k]=x+y;}
  const r=mapAdmitted(c,p);for(let k=0;k<3;k++)src[3*i+k]=r[k]*alpha[i];
 }
 const wx=weights(W,N,scale,cx),wy=weights(H,N,scale,cy),tmp=new Float64Array(N*W*4);
 for(let y=0;y<N;y++)for(const [sy,w] of wy[y])for(let x=0;x<W;x++){
  const dest=4*(y*W+x),si=sy*W+x;for(let k=0;k<3;k++)tmp[dest+k]+=w*src[3*si+k];tmp[dest+3]+=w*alpha[si];
 }
 const premultipliedLinear=new Float64Array(N*N*3),cov=new Float64Array(N*N),rgb=new Float64Array(N*N*3),straightSrgb=new Float64Array(N*N*3);
 for(let y=0;y<N;y++)for(let x=0;x<N;x++){
  const i=y*N+x;for(const [sx,w] of wx[x]){const si=4*(y*W+sx);for(let k=0;k<3;k++)premultipliedLinear[3*i+k]+=w*tmp[si+k];cov[i]+=w*tmp[si+3];}
  if(cov[i]< -1e-12||cov[i]>1+1e-12)throw new Error('filtered coverage');cov[i]=Math.max(0,Math.min(1,cov[i]));
  for(let k=0;k<3;k++){
   const v=premultipliedLinear[3*i+k];straightSrgb[3*i+k]=cov[i]>0?encodeSrgb(Math.max(0,Math.min(1,v/cov[i]))):0;
   rgb[3*i+k]=encodeSrgb(Math.max(0,Math.min(1,v+(1-cov[i])*decodeSrgb(background[k]))));
  }
 }
 return {width:N,height:N,rgb,straightSrgb,premultipliedLinear,coverage:cov};
}
async function profileFingerprint(profile){
 const p=admitProfile(profile),stable={};
 for(const k of Object.keys(p).sort()){
  if(['exposure','lift','knee'].includes(k)){
   const bytes=new Uint8Array(8);new DataView(bytes.buffer).setFloat64(0,p[k],false);
   stable[k]={f64:Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('')};
  }else stable[k]=p[k];
 }
 return sha256Hex(new TextEncoder().encode(JSON.stringify(stable)));
}

/** SHA-256 for small identity records in non-secure file/opaque-origin workers.
 * No cryptographic keys or signatures. The byte digest is checked against
 * independent Python hashlib and Node crypto; this is content identity only.
 */
function sha256Hex(data){
 if(!(data instanceof Uint8Array)||data.length>1048576)throw new RangeError('identity byte buffer must be at most one MiB');
 const K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
 const H=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
 const n=Math.ceil((data.length+9)/64)*64,padded=new Uint8Array(n);padded.set(data);padded[data.length]=0x80;
 const view=new DataView(padded.buffer);view.setUint32(n-4,data.length*8,false);const w=new Uint32Array(64),rotr=(x,n)=>(x>>>n)|(x<<(32-n));
 for(let off=0;off<n;off+=64){
  for(let i=0;i<16;i++)w[i]=view.getUint32(off+4*i,false);
  for(let i=16;i<64;i++){const x=w[i-15],y=w[i-2];w[i]=(w[i-16]+(rotr(x,7)^rotr(x,18)^(x>>>3))+w[i-7]+(rotr(y,17)^rotr(y,19)^(y>>>10)))>>>0;}
  let [a,b,c,d,e,f,g,h]=H;
  for(let i=0;i<64;i++){const t1=(h+(rotr(e,6)^rotr(e,11)^rotr(e,25))+((e&f)^(~e&g))+K[i]+w[i])>>>0,t2=((rotr(a,2)^rotr(a,13)^rotr(a,22))+((a&b)^(a&c)^(b&c)))>>>0;h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;}
  const last=[a,b,c,d,e,f,g,h];for(let i=0;i<8;i++)H[i]=(H[i]+last[i])>>>0;
 }
 return H.map(x=>x.toString(16).padStart(8,'0')).join('');
}

