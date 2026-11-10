/** Normalised Gaussian-mixture optical PSFs; deliberate approximations, not stellar discs.
 * Diffraction is represented by a Gaussian core matched approximately to Airy FWHM.
 * It does NOT reproduce diffraction rings/spider spikes. Pixel integration is exact Gaussian
 * CDF quadrature in renderer.mjs. Scatter redistributes a fixed fraction of energy.
 */
import {finite} from './astronomy.mjs';
export function psfComponents({preset='reference',wavelengthNm=550,arcsecPerCssPixel=1200,
 apertureMm=preset==='eye'?6:50,seeingFwhmArcsec=2,pixelSigmaCss=.48,scatterFraction,
 coreSigmaCss=.55,scatterSigmaCss=2.2}={}){
 if(!['reference','camera','eye'].includes(preset))throw new RangeError('Unknown optical preset');
 finite(wavelengthNm,'wavelength nm',360,830);finite(apertureMm,'aperture mm',.1,10000);finite(arcsecPerCssPixel,'angular pixel scale',.01,100000);
 finite(seeingFwhmArcsec,'seeing FWHM arcsec',0,120);finite(pixelSigmaCss,'pixel reconstruction sigma',.1,8);
 finite(coreSigmaCss,'core sigma',.1,8);finite(scatterSigmaCss,'scatter sigma',.1,12);
 const scatter=finite(scatterFraction??(preset==='eye'?.06:preset==='camera'?.015:.035),'scatter fraction',0,.25);
 const diffractionSigma=.437*(wavelengthNm*1e-9/(apertureMm*.001))*206264.806;
 const sigma=preset==='reference'?coreSigmaCss:Math.min(50,Math.hypot(pixelSigmaCss,diffractionSigma/arcsecPerCssPixel,seeingFwhmArcsec/2.35482/arcsecPerCssPixel));
 const wing=Math.max(sigma,scatterSigmaCss*(preset==='eye'?1.4:1));
 return [{sigmaCss:sigma,weight:1-scatter},{sigmaCss:wing,weight:scatter}];
}
