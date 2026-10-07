/** Native clouds are an 8-bit display-referred painting, not HDR radiance.
 * Canvas unpremultiplication can return code 255 at alpha 1/255. Inverting that
 * colour BEFORE coverage interprets rounding as a nearly infinite emitter.
 * Join bounded display-linear colour after the sky/lunar tone map, then return
 * to the existing shared encoder's input space. No second cloud application.
 */
const nativeCloudDisplay=Float64Array.from({length:256},(_,i)=>{
 const s=i/255;return s<=.04045?s/12.92:((s+.055)/1.055)**2.4;
});
export function nativeCloudChannel(base,code,alpha,exposure){
 if(!Number.isFinite(base)||base<0||!Number.isInteger(code)||code<0||code>255||!Number.isFinite(alpha)||alpha<0||alpha>1||!Number.isFinite(exposure)||exposure<=0||exposure>100000)throw new RangeError('Invalid native cloud channel');
 if(alpha===0)return base;
 const display=-Math.expm1(-exposure*base)*(1-alpha)+nativeCloudDisplay[code]*alpha;
 return -Math.log1p(-Math.min(1-1/131072,display))/exposure;
}
export function validateNativeRGBA(data,pixels){
 if(!data||data.length!==pixels*4)throw new RangeError('Native foreground dimensions');
 // getImageData owns a complete byte snapshot. Test/adaptor arrays must obey
 // the same contract; NaN must never silently become black in an output byte.
 if(!(data instanceof Uint8ClampedArray))for(const v of data)
  if(!Number.isInteger(v)||v<0||v>255)throw new RangeError('Invalid native RGBA');
 return data;
}
