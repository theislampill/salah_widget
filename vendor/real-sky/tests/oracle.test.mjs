import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import * as A from '../src/astronomy.mjs';
const f=JSON.parse(fs.readFileSync(new URL('./fixtures/swiss-reference.json',import.meta.url)));
const delta=(x,y)=>Math.abs(((x-y+540)%360)-180);
const errors={precessionArcsec:0,precessionNutationArcsec:0,gastArcsec:0,horizontalArcsec:0};
for(const r of f.rotation){const v=A.radecVector(...r.j2000),p=A.precessJ2000(v,r.jdTt),n=A.nutation(r.jdTt);
 errors.precessionArcsec=Math.max(errors.precessionArcsec,3600*A.angularSeparation(p,A.radecVector(...r.meanOfDate)));
 errors.precessionNutationArcsec=Math.max(errors.precessionNutationArcsec,3600*A.angularSeparation(A.nutate(p,r.jdTt),A.radecVector(...r.trueOfDate)));
 errors.gastArcsec=Math.max(errors.gastArcsec,3600*delta(A.gmstDeg(r.jdUt1)+n.dpsi*Math.cos(n.eps+n.deps)/A.DEG,r.gastDeg));
}
for(const r of f.horizontal){const h=A.equatorialToHorizontal(r.ra,r.dec,r.lstDeg,r.lat);errors.horizontalArcsec=Math.max(errors.horizontalArcsec,3600*Math.abs(h.altDeg-r.altDeg),3600*delta(h.azDeg,r.azDeg));}
console.log('Independent Swiss Ephemeris residual maxima:',JSON.stringify(errors));
test('72 independent rotation samples: precession <=0.5 arcsec over 1901–2099',()=>assert.ok(errors.precessionArcsec<.5,JSON.stringify(errors)));
test('72 independent rotation samples: truncated nutation+precession <=2 arcsec',()=>assert.ok(errors.precessionNutationArcsec<2,JSON.stringify(errors)));
test('independent GAST sampled agreement <=3 arcsec (long-term oracle model differs)',()=>assert.ok(errors.gastArcsec<3,JSON.stringify(errors)));
test('105 independent horizon samples <=0.0001 arcsec',()=>assert.ok(errors.horizontalArcsec<.0001,JSON.stringify(errors)));

test("2026 GAST samples independently agree within 0.3 arcsec",()=>{for(const r of f.rotation.filter(r=>A.julianYear(r.jdUt1)>=2026&&A.julianYear(r.jdUt1)<2027)){const n=A.nutation(r.jdTt);assert.ok(3600*delta(A.gmstDeg(r.jdUt1)+n.dpsi*Math.cos(n.eps+n.deps)/A.DEG,r.gastDeg)<.3);}});
