/** Constellation regions and aliases are annotations, not physical emissive objects. */
import {finite,wrapDeg,radecVector,vectorRaDec,precessJ2000,unit,DEG} from './astronomy.mjs';
export const B1875_JD=2415020.31352-25*365.242198781;
export function constellationB1875(raDeg,decDeg,data){
 finite(raDeg,'RA');finite(decDeg,'declination',-90,90);
 if(data?.boundaryFrame!=='B1875-mean-equatorial'||!Array.isArray(data.table))throw new TypeError('B1875 Roman table required');
 const h=wrapDeg(raDeg)/15;
 for(const [lo,hi,de,co] of data.table)if(h>=lo&&h<hi&&decDeg>=de)return co;
 throw new RangeError('Constellation table does not cover direction');
}
export function constellationJ2000(raDeg,decDeg,data){const c=vectorRaDec(precessJ2000(radecVector(raDeg,decDeg),B1875_JD));return constellationB1875(c.raDeg,c.decDeg,data);}
export function lookupAlias(name,data){if(typeof name!=='string')throw new TypeError('Alias must be text');const key=name.normalize('NFC').trim().toLowerCase().replace(/\s+/g,' ');return [...(data.index?.[key]??[])];}
/** Transpose of the orthogonal J2000 -> B1875 rotation; no fictitious proper motion. */
export function b1875ToJ2000(v){const columns=[[1,0,0],[0,1,0],[0,0,1]].map(a=>precessJ2000(a,B1875_JD));v=unit(v);return columns.map(a=>a.reduce((s,x,i)=>s+x*v[i],0));}
/** Constant declination boundaries are SMALL circles, not endpoint great-circle chords. */
export function boundarySamples(edge,maxStepDeg=1){
 finite(maxStepDeg,'boundary step',.05,5);for(const p of [edge.a,edge.b]){if(!Array.isArray(p)||p.length!==2)throw new TypeError('boundary point required');finite(p[0],'boundary RA',0,360);finite(p[1],'boundary dec',-90,90);}
 if(edge.a[0]!==edge.b[0]&&edge.a[1]!==edge.b[1])throw new RangeError('B1875 boundary must be meridian or parallel');
 const span=Math.max(Math.abs(edge.b[0]-edge.a[0])*Math.cos(edge.a[1]*DEG),Math.abs(edge.b[1]-edge.a[1]));
 const count=Math.max(1,Math.ceil(span/maxStepDeg));return Array.from({length:count+1},(_,i)=>b1875ToJ2000(radecVector(edge.a[0]+(edge.b[0]-edge.a[0])*i/count,edge.a[1]+(edge.b[1]-edge.a[1])*i/count)));
}
