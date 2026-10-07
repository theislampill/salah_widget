import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {createRequire} from 'node:module';
// Current supplied snapshot comparison, not the unavailable historical Git audit.
const require=createRequire(import.meta.url),{rule,composition,mutateTimetable}=require('../../tests/r0018-timetable-contrast.cjs');
const current=fs.readFileSync(new URL('../../index.html',import.meta.url),'utf8'),baseline=fs.readFileSync(new URL('../../src/native/index.html',import.meta.url),'utf8');
test('timetable CSS and geometry equal the user-supplied 2057503 snapshot',()=>{for(const selector of ['.times','.p','.p.on','.p.now','.p.past','.p b','.tm'])assert.deepEqual(rule(current,selector),rule(baseline,selector),selector);});
for(const state of ['normal','past','on'])test(`native opt-in contrast ${state} retains the existing white-backdrop 4.5 bound`,()=>{const c=composition(current,state,[255,255,255],'contrast');assert.ok(c.ratio>=4.5);assert.equal(c.opacity,1);});
test('glass comparison preserves the pinned aesthetic without inventing an accessibility claim',()=>{for(const state of ['normal','past','on','now'])assert.deepEqual(composition(current,state),composition(baseline,state));assert.ok(composition(current,'normal').ratio<4.5);});
for(const state of ['past','on'])test(`native contrast ${state} attenuation mutation is detected`,()=>assert.ok(composition(mutateTimetable(current,state),state,[255,255,255],'contrast').ratio<4.5));
