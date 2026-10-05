/** CP5 relative spectral radiometry. The V passband, CIE observer and display encoding
 * are distinct. Spectra describe received extra-atmospheric light: NEVER divide by distance.
 * 5 nm integration and sparse IRAF references are not high-resolution spectral calibration.
 */
import {finite,clamp} from './astronomy.mjs';
import {magnitudeFlux,airmass,opticalDepth,xyzToLinearRgb,luminance} from './photometry.mjs';
import {SPECTRAL_TABLES} from './spectral-tables.mjs';
export const SPECTRAL_GRID=SPECTRAL_TABLES.wavelengthNm;
const sfWeights=SPECTRAL_TABLES.weightsNm,sfXYZ=SPECTRAL_TABLES.cieXYZ,sfCache=new Map(),sfFitCache=new Map();
function sfValidate(samples){if(!Array.isArray(samples)||samples.length!==95||!samples.every(x=>Number.isFinite(x)&&x>=0)||!samples.some(x=>x>0))throw new TypeError('Spectrum must have 95 non-negative finite samples with positive energy');return samples;}
export function passbandIntegral(samples,band='V'){
 sfValidate(samples);const b=SPECTRAL_TABLES.passbands[band];if(!b)throw new RangeError('Unknown passband');
 return samples.reduce((s,v,i)=>s+v*SPECTRAL_GRID[i]*b[i]*sfWeights[i],0);
}
export function cieTableAt(w){finite(w,'wavelength nm',360,830);const p=(w-360)/5,i=Math.min(93,Math.floor(p)),t=p-i;return sfXYZ[i].map((v,k)=>v*(1-t)+sfXYZ[i+1][k]*t);}
function sfNormalise(samples){const v=passbandIntegral(samples);if(!(v>0))throw new RangeError('Spectrum has no V-passband support');return samples.map(s=>s/v);}
const sfVega=SPECTRAL_TABLES.standards[0].samples,sfVegaBV=passbandIntegral(sfVega,'B')/passbandIntegral(sfVega,'V');
const sfObserverScale=1/sfVega.reduce((s,v,i)=>s+v*sfXYZ[i][1]*sfWeights[i],0);
export function syntheticBV(samples){const b=passbandIntegral(samples,'B'),v=passbandIntegral(samples,'V');if(!(b>0&&v>0))throw new RangeError('B and V need positive support');return -2.5*Math.log10(b/v/sfVegaBV);}
export function blackbodyShape(temperatureK){finite(temperatureK,'temperature proxy K',1500,200000);return sfNormalise(SPECTRAL_GRID.map(w=>1/(w**5*Math.expm1(1.438776877e7/(w*temperatureK)))));}
function sfFitColour(bv){if(sfFitCache.has(bv))return sfFitCache.get(bv);let lo=1500,hi=200000;if(bv>syntheticBV(blackbodyShape(lo))||bv<syntheticBV(blackbodyShape(hi)))return null;
 for(let i=0;i<48;i++){const mid=Math.sqrt(lo*hi);if(syntheticBV(blackbodyShape(mid))>bv)lo=mid;else hi=mid;}
 const T=Math.sqrt(lo*hi),fit={samples:blackbodyShape(T),temperatureProxyK:T};sfFitCache.set(bv,fit);return fit;
}
/** Hierarchy: caller spectrum with provenance -> same-identity standard -> strictly matched,
 * colour-compatible standard template -> B-V constrained continuum -> explicitly unknown.
 * Template reuse is opt-in via actual spectralType and never labelled a target measurement.
 */
function sfTiltTemplate(samples,bv){let lo=-4,hi=4,p=0,shape;for(let i=0;i<40;i++){p=(lo+hi)/2;shape=samples.map((x,j)=>x*(SPECTRAL_GRID[j]/550)**p);if(syntheticBV(shape)<bv)lo=p;else hi=p;}return {samples:sfNormalise(shape),colourTiltExponent:p};}
export function selectSpectrum(star){
 if(star.sed){const d=star.sed;if(typeof d.source!=='string'||!d.source.trim())throw new TypeError('Provided spectrum requires source provenance');return {samples:sfNormalise(sfValidate(d.samples)),kind:d.kind??'provided-spectrum',source:d.source,measuredForThisSource:d.measuredForThisSource===true,temperatureProxyK:null,colourFallback:false};}
 const key=[star.hip??'',star.spectralType??'',star.bv??'unknown'].join('|');if(sfCache.has(key))return sfCache.get(key);
 let value;const own=SPECTRAL_TABLES.standards.find(s=>s.hip===star.hip);
 if(own)value={samples:own.samples,kind:own.kind,source:own.source,measuredForThisSource:true,resolution:own.resolution,temperatureProxyK:null,colourFallback:false};
 const bv=star.bv;
 if(!value&&bv!=null){finite(bv,'B-V',-.5,5);const template=SPECTRAL_TABLES.standards.find(s=>s.templateClass===star.spectralType&&Math.abs(bv-s.catalogueBV)<=.08);
  if(template)value={...sfTiltTemplate(template.samples,bv),kind:'observed-standard-template',source:template.source,measuredForThisSource:false,temperatureProxyK:null,colourFallback:false,templateColourResidualMag:syntheticBV(template.samples)-bv};
  else if(bv>=-.4&&bv<=2){const fitted=sfFitColour(bv);if(fitted)value={...fitted,kind:'B-V-constrained-continuum',source:'catalogue B-V; Planck family solved in declared Bessell B/V convention',measuredForThisSource:false,colourFallback:false};}
 }
 if(!value)value={samples:blackbodyShape(6500),kind:'unknown-neutral-display',source:'no admissible measured colour/spectrum; grey display proxy only',measuredForThisSource:false,temperatureProxyK:null,colourFallback:true};
 Object.freeze(value.samples);Object.freeze(value);if(sfCache.size<12000)sfCache.set(key,value);return value;
}
export function spectrumToXYZ(samples){return [0,1,2].map(k=>samples.reduce((s,v,i)=>s+v*sfXYZ[i][k]*sfWeights[i]*sfObserverScale,0));}
export function gamutMapXYZ(xyz){let rgb=xyzToLinearRgb(xyz).map(x=>Math.max(0,x));const y=luminance(rgb);return y>0?rgb.map(x=>x*xyz[1]/y):[0,0,0];}
/** transportAt receives wavelength nm and returns TOTAL direct terrestrial transmission.
 * If supplied, it owns aerosol/gas/cloud attenuation; the atmosphere object is not reapplied.
 */
export function spectralStarFlux(star,altDeg,atmosphere={},options={}){
 finite(altDeg,'altitude',-90,90);const spectrum=selectSpectrum(star),scale=magnitudeFlux(star.vmag);
 if(altDeg<0)return {rgb:[0,0,0],xyz:[0,0,0],vFlux:0,kind:spectrum.kind,colourFallback:spectrum.colourFallback};
 const X=airmass(altDeg),cloud=finite(atmosphere.cloudTransmission??1,'cloud transmission',0,1);
 const samples=spectrum.samples.map((v,i)=>{const w=SPECTRAL_GRID[i],t=options.transportAt?finite(options.transportAt(w),'total spectral transmission',0,1):Math.exp(-X*opticalDepth(w,atmosphere))*cloud;return v*t*scale;});
 const xyz=spectrumToXYZ(samples),vFlux=passbandIntegralSafeZero(samples),response=options.response??'CIE1931';let rgb;
 if(response==='CIE1931')rgb=spectrum.colourFallback?[xyz[1],xyz[1],xyz[1]]:gamutMapXYZ(xyz);
 else if(response==='V-monochrome')rgb=[vFlux,vFlux,vFlux];else throw new RangeError('Unknown response model');
 return {rgb,xyz,vFlux,kind:spectrum.kind,model:spectrum.kind,source:spectrum.source,colourFallback:spectrum.colourFallback,temperatureProxyK:spectrum.temperatureProxyK,response,transportOwner:options.transportAt?'caller-total-transmission':'spectral-module'};
}
function passbandIntegralSafeZero(samples){return samples.some(x=>x>0)?passbandIntegral(samples):0;}
