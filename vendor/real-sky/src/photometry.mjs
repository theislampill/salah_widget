/** Relative stellar photometry and spectral transport. Not absolute display calibration.
 * V magnitude -> exact relative V-band flux; using it as photopic Y is an explicit
 * passband approximation. B-V -> blackbody colour proxy is NOT a measured SED or Teff.
 * See docs/RESEARCH.md and provenance/sources.json for methods and limitations.
 */
import {DEG,finite,clamp} from './astronomy.mjs';
export const luminance=rgb=>.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];
export function magnitudeFlux(m){return 10**(-.4*finite(m,'V magnitude',-30,40));}
export function colourTemperature(bv){if(bv==null)return null;finite(bv,'B-V',-.5,5);
 // Values outside the useful blackbody-colour interval are not extrapolated.
 if(bv<-.4||bv>2.0)return null;
 return 4600*(1/(.92*bv+1.7)+1/(.92*bv+.62));
}
/** Wyman/Sloan/Shirley 2013, equation 4/table 1, 1931 2-degree observer. */
export function cie1931(w){finite(w,'wavelength nm',360,830);
 const g=(c,a,b)=>Math.exp(-.5*((w-c)*(w<c?a:b))**2);
 return [.362*g(442,.0624,.0374)+1.056*g(599.8,.0264,.0323)-.065*g(501.1,.049,.0382),.821*g(568.8,.0213,.0247)+.286*g(530.9,.0613,.0322),1.217*g(437,.0845,.0278)+.681*g(459,.0385,.0725)];
}
export function airmass(apparentAltDeg){finite(apparentAltDeg,'apparent altitude',0,90);return 1/(Math.sin(apparentAltDeg*DEG)+.50572*(apparentAltDeg+6.07995)**-1.6364);}
export function transmission(X,tau){finite(X,'airmass',0,1000);finite(tau,'optical depth',0,1000);return Math.exp(-X*tau);}
export function opticalDepth(w,{rayleighTau550=.10,aerosolTau550=.06,angstromExponent=1.3,greyTau=0}={}){
 finite(w,'wavelength',360,830);finite(rayleighTau550,'Rayleigh optical depth',0,100);finite(aerosolTau550,'aerosol optical depth',0,100);finite(angstromExponent,'Angstrom exponent',0,4);finite(greyTau,'grey optical depth',0,100);
 return rayleighTau550*(550/w)**4.08+aerosolTau550*(550/w)**angstromExponent+greyTau;
}
export function xyzToLinearRgb([x,y,z]){return [3.2404542*x-1.5371385*y-.4985314*z,-.969266*x+1.8760108*y+.041556*z,.0556434*x-.2040259*y+1.0572252*z];}
const bins=Array.from({length:95},(_,i)=>{const w=360+i*5;return {w,xyz:cie1931(w),weight:i===0||i===94?2.5:5};});
const spectra=new Map();
/** A normalised shape, integral against ybar = 1 before terrestrial extinction. */
export function spectrumForColour(bv){const key=bv==null?'unknown':String(bv);if(spectra.has(key))return spectra.get(key);
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
export function starRgbFlux(star,altDeg,atmosphere={}){
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
export function linearToSrgb(x){finite(x,'linear channel',0);return x<=.0031308?12.92*x:1.055*x**(1/2.4)-.055;}
export function srgbToLinear(x){finite(x,'sRGB channel',0);return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;}
/** Zero-mean, bounded, deterministic display surrogate; not a forecast of real turbulence.
 * Never changes star position, diameter, catalogue magnitude or identity. Default amplitude=0.
 */
export function scintillation(hip,tSeconds,altDeg,amplitude=0){finite(amplitude,'scintillation amplitude',0,.3);if(amplitude===0)return 1;
 const phase=(hip*.61803398875)%1*2*Math.PI,altFactor=.25+.75*(1-Math.sin(clamp(altDeg,0,90)*DEG));
 return 1+amplitude*altFactor*(.6*Math.sin(2*Math.PI*.73*tSeconds+phase)+.4*Math.sin(2*Math.PI*1.17*tSeconds+phase*2.13));
}
