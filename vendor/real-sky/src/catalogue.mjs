import {finite} from './astronomy.mjs';
export function validateCatalogue(c){
 if(!['salah-real-sky/catalogue/1','salah-real-sky/catalogue/2'].includes(c?.schema)||!Array.isArray(c.stars)||!c.stars.length)throw new TypeError('unsupported or empty catalogue');
 const v2=c.schema.endsWith('/2'),seen=new Set(),hips=new Set();
 for(const s of c.stars){
  if(v2){
   if(typeof s.id!=='string'||!/^hyg:[1-9][0-9]*$/.test(s.id)||s.id!==`hyg:${s.hygId}`||!Number.isSafeInteger(s.hygId)||seen.has(s.id))throw new Error('invalid or duplicate stable identity');
   seen.add(s.id);
  }
  if(!v2||s.hip!==null){if(!Number.isSafeInteger(s.hip)||s.hip<=0||hips.has(s.hip))throw new Error('invalid or duplicate HIP identity');hips.add(s.hip);}
  finite(s.raDeg,'RA',0,360);if(s.raDeg>=360)throw new RangeError('RA must be below 360 degrees');
  finite(s.decDeg,'declination',-90,90);finite(s.vmag,'V magnitude',-2,25);finite(s.epochJyear,'epoch',1800,2200);
  if(s.bv!==null)finite(s.bv,'B-V',-.5,5);
  for(const k of ['pmRaCosDecMasYr','pmDecMasYr','distancePc','radialVelocityKmS'])if(s[k]!=null)finite(s[k],k);
  if(s.distancePc!=null&&s.distancePc<=0)throw new RangeError('distance must be positive');
 }
 return c;
}
/** Fetch with explicit generation ownership in SkyController; never substitute random stars. */
export async function loadCatalogue(url,{signal,fetchImpl=globalThis.fetch}={}){
 const r=await fetchImpl(url,{signal,credentials:'omit',cache:'no-cache'});if(!r.ok)throw new Error(`catalogue HTTP ${r.status}`);
 return validateCatalogue(await r.json());
}
