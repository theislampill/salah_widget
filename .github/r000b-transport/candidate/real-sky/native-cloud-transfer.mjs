/** Native clouds are an 8-bit display-referred painting, not HDR radiance.
 * Canvas unpremultiplication can return code 255 at alpha 1/255. Inverting that
 * colour BEFORE coverage interprets rounding as a nearly infinite emitter.
 * Join bounded display-linear colour after the sky/lunar tone map, then return
 * to the existing shared encoder's input space. No second cloud application.
 */
const nativeCloudDisplay=Float64Array.from({length:256},(_,i)=>{
 const s=i/255;return s<=.04045?s/12.92:((s+.055)/1.055)**2.4;
});
const displayRound=v=>Math.round(255*(v<=.0031308?12.92*v:1.055*v**(1/2.4)-.055));
const displayGuess=Uint8Array.from({length:4097},(_,i)=>displayRound(i/4096));
const displayBoundary=Float64Array.from({length:256},(_,i)=>{
 const s=(i+.5)/255;return s<=.04045?s/12.92:((s+.055)/1.055)**2.4;
});
/** Exact byte quantization, not a coarser colour curve. A table supplies only
 * a bracket; the actual linear value decides the sRGB half-code boundary.
 * At binary64 inverse/forward rounding ties use the original expression.
 * This removes three pow calls per cloud pixel from the publication deadline. */
export function nativeDisplayCode(v){
 let c=displayGuess[Math.min(4096,Math.max(0,Math.floor(v*4096)))];
 if(c<255&&v>=displayBoundary[c])c++;
 if(c>0&&v<displayBoundary[c-1])c--;
 if(Math.abs(v-displayBoundary[c])<1e-12||c>0&&Math.abs(v-displayBoundary[c-1])<1e-12)return displayRound(v);
 return c;
}
export function nativeCloudChannel(base,code,alpha,exposure){
 if(!Number.isFinite(base)||base<0||!Number.isInteger(code)||code<0||code>255||!Number.isFinite(alpha)||alpha<0||alpha>1||!Number.isFinite(exposure)||exposure<=0||exposure>100000)throw new RangeError('Invalid native cloud channel');
 if(alpha===0)return base;
 const display=-Math.expm1(-exposure*base)*(1-alpha)+nativeCloudDisplay[code]*alpha;
 return -Math.log1p(-Math.min(1-1/131072,display))/exposure;
}
export function validateNativeRGBA(data,pixels){
 if(!Number.isSafeInteger(pixels)||pixels<0||!data||data.length!==pixels*4)throw new RangeError('Native foreground dimensions');
 // getImageData owns a complete byte snapshot. Test/adaptor arrays must obey
 // the same contract; NaN must never silently become black in an output byte.
 if(!(data instanceof Uint8ClampedArray))for(const v of data)
  if(!Number.isInteger(v)||v<0||v>255)throw new RangeError('Invalid native RGBA');
 return data;
}
/** Preview already holds display bytes. Evaluate the SAME display-linear
 * coverage directly, avoiding a redundant HDR inverse/encode round trip. */
export function nativeCloudDisplayFrame(base,cloud,moon=null){
 validateNativeRGBA(base,base?.length/4);validateNativeRGBA(cloud,base.length/4);
 if(moon)validateNativeRGBA(moon,base.length/4);
 const out=new Uint8ClampedArray(base);
 for(let i=0;i<base.length;i+=4){
  if(base[i+3]!==255)throw new RangeError('Preview background must be opaque');
  const a=cloud[i+3]/255,ma=moon?moon[i+3]/255:0;if(a===0&&ma===0)continue;
  for(let k=0;k<3;k++){
   const gas=nativeCloudDisplay[base[i+k]],surface=ma?Math.min(1-1/131072,nativeCloudDisplay[moon[i+k]]):0;
   // Exponential shared encoding turns additive foreground gas + native
   // surface radiance into this display-linear screen. Surface alpha never
   // erases foreground atmosphere. The caller has already cut catalogue
   // sources with the opaque calendar geometry when stars are available.
   const lunar=ma?1-(1-gas)*Math.pow(1-surface,ma):gas;
   const v=lunar*(1-a)+nativeCloudDisplay[cloud[i+k]]*a;
   out[i+k]=nativeDisplayCode(v);
  }
 }
 return out;
}
