import {finite} from './core/src/astronomy.mjs';
import {linearToSrgb} from './core/src/photometry.mjs';

// N001: the immutable encoder is monotone and quantizes to 256 byte values.
// Locate its exact binary64 transition points using that SAME numerical oracle
// on this JS engine. No approximate LUT/interpolation, new exposure or tolerance.
// The multiplication exposure*max(0,channel) keeps the reference's evaluation order.
let nativeEncodeEdges=null;
const nativeOracleCode=y=>Math.round(255*linearToSrgb(-Math.expm1(-y)));
export function nativeEncodingThresholds(){
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
export function encodeNativeFrame(linear,exposure=12){
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
