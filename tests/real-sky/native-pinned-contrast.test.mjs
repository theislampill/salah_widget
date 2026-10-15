import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {createRequire} from 'node:module';
// Generated consumer must preserve the authored timetable policy and geometry.
const require=createRequire(import.meta.url),{rule,composition,mutateTimetable}=require('../../tests/r0018-timetable-contrast.cjs');
const current=fs.readFileSync(new URL('../../index.html',import.meta.url),'utf8'),baseline=fs.readFileSync(new URL('../../src/native/index.html',import.meta.url),'utf8');
test('generated timetable CSS and geometry equal the authored native owner',()=>{for(const selector of ['.times','.p','.p.on','.p.now','.p.past','.p b','.tm'])assert.deepEqual(rule(current,selector),rule(baseline,selector),selector);});
for(const appearance of ['glass','contrast'])for(const state of ['normal','past','on','now'])test(`native ${appearance} ${state} meets the original white-stress 4.5 criterion`,()=>{const c=composition(current,state,[255,255,255],appearance);assert.ok(c.ratio>=4.5);assert.equal(c.opacity,1);});
test('default readability composition is generated from the exact authored policy',()=>{for(const state of ['normal','past','on','now'])assert.deepEqual(composition(current,state),composition(baseline,state));});
for(const [kind,state] of [['default-past','past'],['default-base','normal'],['default-on','on']])test(`native ${kind} loss mutation is detected`,()=>assert.ok(composition(mutateTimetable(current,kind),state,[255,255,255],'glass').ratio<4.5));
