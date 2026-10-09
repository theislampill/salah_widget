
/** Explicit BELOW-HORIZON CALENDAR TOKEN, not physical Earthlight or an
 * astronomical irradiance floor. Preserve the refined phase/relief at no more
 * than the old .020 x material token's integrated display luminance. This is
 * one scalar emphasis change, not albedo substituted for terrain lighting.
 * Above-horizon reference pixels remain exact; coverage stays opaque.
 */
function calendarProxy(material,coverage,refined){
 if(material.length!==coverage.length*3||refined?.length!==material.length)throw new RangeError('calendar material');
 const out=new Float32Array(material.length),Y=[.2126,.7152,.0722];let ceiling=0,total=0;
 for(let i=0;i<coverage.length;i++){
  const a=coverage[i];if(!Number.isFinite(a)||a<0||a>1)throw new RangeError('calendar coverage');
  for(let k=0;k<3;k++){const c=material[3*i+k],v=refined[3*i+k];if(!Number.isFinite(c)||c<0||c>1||!Number.isFinite(v)||v<0||v>a+1e-6)throw new RangeError('calendar colour');ceiling+=Y[k]*.020*c*a;total+=Y[k]*v;}
 }
 const gain=total>0?Math.min(1,ceiling/total):0;
 for(let i=0;i<out.length;i++)out[i]=refined[i]*gain;
 return out;
}
function blendCalendarBytes(upper,lower,up){
 if(!Number.isFinite(up)||up<0||up>1||upper.length!==lower.length||upper.length%4)throw new RangeError('calendar blend');
 const result=new Uint8ClampedArray(upper.length),decode=new Float64Array(256);
 for(let i=0;i<256;i++){const c=i/255;decode[i]=c<=.04045?c/12.92:((c+.055)/1.055)**2.4;}
 for(let i=0;i<result.length;i+=4){
  if(upper[i+3]!==lower[i+3])throw new RangeError('calendar alpha');result[i+3]=upper[i+3];
  for(let k=0;k<3;k++){
   if(up===1)result[i+k]=upper[i+k];else if(up===0)result[i+k]=lower[i+k];
   else{const c=up*decode[upper[i+k]]+(1-up)*decode[lower[i+k]];result[i+k]=Math.floor(255*(c<=.0031308?12.92*c:1.055*c**(1/2.4)-.055)+.5);}
  }
 }return result;
}
/** Adds a display-only native calendar token without touching V5 source fields,
 * primary surface, or quality images. Called only at worker publication. */
function nativeCalendarResult(engine,result){
 const N=result.surfaceSize,material=engine.material??new Float32Array(N*N*3);
 if(!engine.material){const pix=new Float64Array(engine.e.memory.buffer,engine.e.get_pixels(),N*N*24);for(let i=0;i<N*N;i++)for(let k=0;k<3;k++)material[3*i+k]=pix[24*i+6+k];}
 const linear=calendarProxy(material,result.surfaceCoverage,result.surfaceLinear),table=prefixSurface({size:N,linear,coverage:result.surfaceCoverage}),M=result.width,scale=N/(result.scene.diameter*result.surfaceExtent),o=N/2-M*scale/2,rgba=new Uint8ClampedArray(result.rgba.length);
 for(let y=0;y<M;y++)for(let x=0;x<M;x++){
  const i=y*M+x,c=boxSurface(table,o+x*scale,o+y*scale,o+(x+1)*scale,o+(y+1)*scale),a=c[3];rgba[4*i+3]=result.rgba[4*i+3];
  for(let k=0;k<3;k++){const v=a?c[k]/a:0;rgba[4*i+k]=Math.floor(255*(v<=.0031308?12.92*v:1.055*v**(1/2.4)-.055)+.5);}
 }return {calendarLinear:linear,calendarRgba:rgba};
}
