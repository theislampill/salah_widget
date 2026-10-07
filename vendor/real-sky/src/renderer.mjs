/** CPU reference rasterizer. Accumulates sources + supplied sky in LINEAR light, then
 * tone maps and sRGB-encodes once. Output is intentionally opaque: CSS screen blending
 * an encoded transparent canvas with the old sky is NOT the same physical pipeline.
 */
import {finite} from './astronomy.mjs';
import {scintillation,linearToSrgb} from './photometry.mjs';
import {spectralStarFlux} from './spectral.mjs';
import {psfComponents} from './optics.mjs';
export function createLinearBuffer(width,height,background=[0,0,0]){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>8000000)throw new RangeError('invalid/budget-exceeding raster dimensions');
 if(!Array.isArray(background)||background.length!==3||!background.every(x=>Number.isFinite(x)&&x>=0))throw new RangeError('linear RGB background required');
 const b=new Float64Array(width*height*3);if(background.some(x=>x!==0))for(let i=0;i<b.length;i++)b[i]=background[i%3];return b;
}
// Abramowitz/Stegun 7.1.26 approximation; pixel-boundary integration removes subpixel popping.
export function erf(x){const sign=x<0?-1:1,a=Math.abs(x),t=1/(1+.3275911*a);return sign*(1-(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-.284496736)*t+.254829592)*t*Math.exp(-a*a));}
export function splatGaussian(buffer,width,height,x,y,rgb,sigma){
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
export function renderStars(stars,{width=325,height=530,dpr=1,background=[0,0,0],backgroundLinear=null,
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
export function encodeFrame(linear,exposure=12){finite(exposure,'exposure',0,100000);if(linear.length%3)throw new RangeError('RGB buffer required');const bytes=new Uint8ClampedArray(linear.length/3*4);
 for(let i=0,j=0;i<linear.length;i+=3,j+=4){for(let c=0;c<3;c++)bytes[j+c]=Math.round(255*linearToSrgb(-Math.expm1(-exposure*Math.max(0,finite(linear[i+c],'linear channel')))));bytes[j+3]=255;}
 return bytes;
}
