/** Visibility is a display/observer RESPONSE, not an extra extinction coefficient. */
import {finite,DEG,clamp} from './astronomy.mjs';
import {linearToSrgb} from './photometry.mjs';
/** Modelled central CSS-pixel display contrast. No catalogue or physical flux is changed.
 * This is an 8-bit display diagnostic, not a physiological limiting-magnitude prediction. */
export function displayVisibility(sourceY,backgroundY,exposure,{thresholdSrgb=2/255,sigmaCss=.55}={}){
 finite(sourceY,'source flux',0);finite(backgroundY,'background flux per CSS pixel',0);finite(exposure,'display exposure',0,100000);finite(thresholdSrgb,'contrast threshold',0,1);finite(sigmaCss,'PSF sigma',.1,50);
 const peak=sourceY/(2*Math.PI*sigmaCss*sigmaCss),encode=x=>linearToSrgb(-Math.expm1(-x*exposure)),deltaSrgb=encode(backgroundY+peak)-encode(backgroundY);
 return {deltaSrgb,thresholdSrgb,detectable:deltaSrgb>=thresholdSrgb,criterion:'modelled central CSS-pixel contrast; not human acuity'};
}
/** Bounded zero-mean deterministic surrogate. Turbulence parameters are NOT measured.
 * Box-exposure averages the two temporal modes analytically (sinc); no frame random draws.
 * Optional modulation never moves a source or changes its catalogue record. */
export function scintillationFactor(id,tSeconds,altDeg,{strength=.04,exposureSec=.1,apertureMm=6,reducedMotion=false}={}){
 finite(strength,'scintillation strength',0,.3);finite(exposureSec,'exposure seconds',0,3600);finite(apertureMm,'aperture mm',.1,10000);finite(tSeconds,'time seconds');finite(altDeg,'altitude',-90,90);
 if(reducedMotion||strength===0||altDeg<0)return 1;
 let hash=2166136261;for(const c of String(id))hash=Math.imul(hash^c.charCodeAt(0),16777619)>>>0;
 const phase=hash/4294967296*2*Math.PI,sinc=x=>Math.abs(x)<1e-12?1:Math.sin(x)/x,amp=strength*(.25+.75*(1-Math.sin(altDeg*DEG)))*Math.min(1,(6/apertureMm)**(2/3));
 return 1+amp*(.6*Math.sin(2*Math.PI*.73*tSeconds+phase)*sinc(Math.PI*.73*exposureSec)+.4*Math.sin(2*Math.PI*1.17*tSeconds+2.13*phase)*sinc(Math.PI*1.17*exposureSec));
}
