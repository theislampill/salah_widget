/** CP6 explicit local atmospheric assumptions. Optical depths are vertical at the site.
 * Pressure is station pressure, NOT sea-level-corrected pressure. A supplied pressure wins
 * over elevation: do not reduce it a second time. Cloud transmission is a separate owner.
 */
import {finite,DEG,clamp} from './astronomy.mjs';
import {airmass} from './photometry.mjs';
const atmValidated=new WeakSet();
export function normaliseAtmosphere(input={}){
 if(input&&atmValidated.has(input))return input;
 if(input===null||typeof input!=='object')throw new TypeError('Atmosphere must be an object');
 const elevationM=finite(input.elevationM??0,'elevation metres',-500,10000);
 if(input.cloudTransmission!=null&&input.cloudOpticalDepth!=null)throw new RangeError('Supply cloud transmission OR vertical cloud optical depth, not both');
 const pressureHpa=finite(input.pressureHpa??1013.25*(1-2.25577e-5*elevationM)**5.25588,'station pressure hPa',0,1100);
 const result=Object.freeze({__cp6Atmosphere:true,elevationM,pressureHpa,pressureSource:input.pressureHpa==null?'standard-atmosphere-estimate':'caller-supplied-station-pressure',
 aerosolTau550:finite(input.aerosolTau550??.06,'aerosol optical depth 550nm',0,3),angstromExponent:finite(input.angstromExponent??1.3,'Angstrom exponent',0,4),
 greyTau:finite(input.greyTau??0,'grey absorbing optical depth',0,3),aerosolAlbedo:finite(input.aerosolAlbedo??.9,'aerosol single-scattering albedo',0,1),
 aerosolG:finite(input.aerosolG??.76,'aerosol asymmetry',0,.95),rayleighScaleHeightM:finite(input.rayleighScaleHeightM??8000,'molecular scale height',4000,12000),aerosolScaleHeightM:finite(input.aerosolScaleHeightM??1200,'aerosol scale height',100,6000),
 cloudTransmission:input.cloudOpticalDepth!=null?null:finite(input.cloudTransmission??1,'cloud transmission',0,1),cloudOpticalDepth:input.cloudOpticalDepth==null?null:finite(input.cloudOpticalDepth,'cloud vertical optical depth',0,100),
 cloudGlowCdM2:finite(input.cloudGlowCdM2??0,'fully opaque cloud glow cd/m2',0,100000),lightPollutionCdM2:finite(input.lightPollutionCdM2??0,'local pollution radiance cd/m2',0,100000),
 nightZenithVMag:finite(input.nightZenithVMag??21.8,'night zenith magnitude/arcsec2',10,30),twilightScale:finite(input.twilightScale??1,'empirical twilight site scale',0,10)});
 atmValidated.add(result);return result;
}
export function rayleighOpticalDepth(wavelengthNm,atmosphere={}){const a=normaliseAtmosphere(atmosphere),l=finite(wavelengthNm,'wavelength nm',360,830)/1000;return .008569*l**-4*(1+.0113*l**-2+.00013*l**-4)*a.pressureHpa/1013.25;}
export function aerosolOpticalDepth(wavelengthNm,atmosphere={}){const a=normaliseAtmosphere(atmosphere);finite(wavelengthNm,'wavelength nm',360,830);return a.aerosolTau550*(550/wavelengthNm)**a.angstromExponent;}
export function cloudTransmissionFor(direction,atmosphere={},cloudAt=null,utcMs=0){const a=normaliseAtmosphere(atmosphere),alt=finite(direction.altDeg,'cloud sightline altitude',-90,90);finite(direction.azDeg,'cloud sightline azimuth');
 if(cloudAt!=null){if(typeof cloudAt!=='function')throw new TypeError('cloudAt must return total sightline cloud transmission');return finite(cloudAt(direction,utcMs),'total cloud-map transmission',0,1);}
 return a.cloudOpticalDepth==null?a.cloudTransmission:Math.exp(-a.cloudOpticalDepth*airmass(Math.max(0,alt)));
}
export function directTransmission(wavelengthNm,altDeg,atmosphere={},totalCloudTransmission=null){const a=normaliseAtmosphere(atmosphere);finite(altDeg,'source altitude',-90,90);if(altDeg<0)return 0;
 const cloud=totalCloudTransmission==null?cloudTransmissionFor({altDeg,azDeg:0},a):finite(totalCloudTransmission,'total cloud transmission',0,1);
 return cloud*Math.exp(-airmass(altDeg)*(rayleighOpticalDepth(wavelengthNm,a)+aerosolOpticalDepth(wavelengthNm,a)+a.greyTau));
}
export function phaseRayleigh(cosine){finite(cosine,'phase cosine',-1,1);return 3/(16*Math.PI)*(1+cosine*cosine);}
/** cosine=1 means looking TOWARDS the illuminator, hence forward scattering peaks there.
 * This sign convention differs from pbrt's two-away-vector convention. */
export function phaseHG(cosine,g=.76){finite(cosine,'phase cosine',-1,1);finite(g,'asymmetry',-.99,.99);return (1-g*g)/(4*Math.PI*(1+g*g-2*g*cosine)**1.5);}
export function horizontalDirection(h){const a=finite(h.altDeg,'altitude',-90,90)*DEG,z=finite(h.azDeg,'azimuth')*DEG;return [Math.cos(a)*Math.sin(z),Math.cos(a)*Math.cos(z),Math.sin(a)];}
