import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

// R0034 (issue 101) ISM-CFG-010 renderer-literal census (PRA-F-37 item 4). The
// 325x530 card geometry is a literal in many concatenated renderer modules; no
// shared constant is introduced (non-goal). Instead this census pins every
// occurrence against the card geometry in src/native/index.html: changing,
// adding or removing one renderer literal, or the card size, fails here and must
// be reconciled deliberately (update the card and every literal together).
// Run: node --test tests/real-sky/native-geometry-census.test.mjs
const ROOT=new URL('../../',import.meta.url),W=325,H=530;
const CENSUS={ // file: [occurrences of 325, occurrences of 530]
 'native-composition.mjs':[15,14],'native-contract.mjs':[1,1],'native-engine.mjs':[1,1],'native-first-paint.mjs':[2,2],
 'native-host-hooks.js':[1,1],'native-host.mjs':[11,14],'native-preview-host.mjs':[9,8],'native-preview.mjs':[8,11],'native-star-preview.mjs':[10,11]};
// A literal is the bare number, including '325x530' / '325×530' prose and '325px'; never part of a longer number or identifier.
const literal=n=>new RegExp(`(?:(?<![\\w.])|(?<=\\dx))${n}(?![\\d.])`,'g');
const renderer=()=>fs.readdirSync(new URL('real-sky/',ROOT)).filter(f=>/^native-.*\.mjs$/.test(f)||f==='native-host-hooks.js').sort()
 .map(f=>[f,fs.readFileSync(new URL('real-sky/'+f,ROOT),'utf8')]);

test('ES34-12 card geometry is 325x530 in the native source',()=>{
 const html=fs.readFileSync(new URL('src/native/index.html',ROOT),'utf8');
 const rule=html.match(/\n\.c\{[\s\S]*?\n\}/)?.[0]??'';
 assert.match(rule,new RegExp(`position:relative;width:${W}px;height:${H}px;`),'the .c card rule');
});
test('ES34-12 every renderer geometry literal agrees with the card (pinned census)',()=>{
 const found={};
 for(const [file,text] of renderer()){const a=(text.match(literal(W))??[]).length,b=(text.match(literal(H))??[]).length;if(a||b)found[file]=[a,b];}
 assert.deepEqual(found,CENSUS);
});
test('ES34-12 no near-miss card dimension literal exists in renderer modules',()=>{
 for(const [file,text] of renderer()){
  const near=(text.match(/(?<![\w.])(3[23]\d|5[23]\d)(?![\w.])/g)??[]).filter(x=>+x!==W&&+x!==H);
  assert.deepEqual(near,[],file);
 }
});
