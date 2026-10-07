import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {validateCatalogue} from '../src/catalogue.mjs';
const cat=JSON.parse(fs.readFileSync(new URL('./fixtures/checkpoint1-catalogue.json',import.meta.url)));
test('520 unique measured HIP catalogue sources, no Sun',()=>{validateCatalogue(cat);assert.equal(cat.stars.length,520);assert.equal(new Set(cat.stars.map(s=>s.hip)).size,520);assert.ok(cat.stars.every(s=>s.hip>0&&s.vmag<=4.06&&s.vmag>-2));});
test('known positions and measured colour contrasts retained',()=>{const s=id=>cat.stars.find(x=>x.hip===id);assert.equal(s(32349).raDeg,101.287);assert.equal(s(32349).decDeg,-16.716);assert.equal(s(32349).vmag,-1.44);assert.equal(s(27989).bv,1.5);assert.equal(s(24436).bv,-.03);});
test('upstream substituted colour is explicitly unknown',()=>{assert.equal(cat.stars.find(s=>s.hip===81693).bv,null);});
test('motion and distances absent from derivative are not manufactured',()=>{assert.ok(cat.stars.every(s=>s.pmRaCosDecMasYr===null&&s.pmDecMasYr===null&&s.distancePc===null));});
test('duplicate identities and NaNs reject, no silent catalogue repairs',()=>{const c=structuredClone(cat);c.stars.push(c.stars[0]);assert.throws(()=>validateCatalogue(c));const d=structuredClone(cat);d.stars[0].raDeg=NaN;assert.throws(()=>validateCatalogue(d));});
test('RA=360 is rejected at the schema boundary',()=>{const c=structuredClone(cat);c.stars[0].raDeg=360;assert.throws(()=>validateCatalogue(c));});
