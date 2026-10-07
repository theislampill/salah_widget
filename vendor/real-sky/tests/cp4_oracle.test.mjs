import test from 'node:test';import assert from 'node:assert/strict';
import {validateCP4} from '../tools/validate_cp4.mjs';
const r=validateCP4();
for(const [name,limit] of Object.entries(r.limits))test(`Independent CP4 ${name} <= ${limit}`,()=>assert.ok(r[name].max<=limit,JSON.stringify(r[name])));
test('Independent matrix covers every current catalogue source at three epochs',()=>assert.equal(r.wholeCatalogueEquatorialArcsec.count,8921*3));
test('Independent selected-source matrix covers24epochs×8sites×72sources',()=>assert.equal(r.horizontalArcsec.count,24*8*72));
