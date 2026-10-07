import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {validateCatalogue} from '../src/catalogue.mjs';
const c=JSON.parse(fs.readFileSync(new URL('../data/bright-stars.json',import.meta.url)));
test('schema 2 retains 8920 magnitude-selected records, one faint endpoint, fifty without HIP',()=>{assert.equal(validateCatalogue(c),c);assert.equal(c.stars.length,8921);assert.equal(c.stars.filter(s=>s.vmag<=6.5).length,8920);assert.equal(c.stars.filter(s=>s.hip===null).length,50)});
test('duplicate stable identities are rejected even without a HIP',()=>{const d=structuredClone(c);d.stars.push(d.stars.find(s=>s.hip===null));assert.throws(()=>validateCatalogue(d),/identity/)});
test('duplicate HIP remains rejected when HYG keys differ',()=>{const d=structuredClone(c);d.stars[1].hip=d.stars[0].hip;assert.throws(()=>validateCatalogue(d),/HIP/)});
test('partial/malformed motion and missing B-V never default to synthetic colours',()=>{const d=structuredClone(c);d.stars[0].bv=NaN;assert.throws(()=>validateCatalogue(d));d.stars[0].bv=null;d.stars[0].pmRaCosDecMasYr=Infinity;assert.throws(()=>validateCatalogue(d));});
test('real source preserves proper motions and contemporary-relevant reference photometry',()=>{const s=c.stars.find(s=>s.hip===32349);assert.equal(s.pmRaCosDecMasYr,-546.01);assert.equal(s.pmDecMasYr,-1223.08);assert.equal(s.radialVelocityKmS,-9.4);assert.ok(Math.abs(s.raDeg-101.287215)<1e-8);});
