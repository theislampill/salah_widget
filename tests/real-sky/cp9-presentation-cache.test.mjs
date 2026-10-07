import test from 'node:test';import assert from 'node:assert/strict';import * as C from '../../real-sky/native-composition.mjs';
function f(){return {frame:{},rows:2,maskKey:'mask-1',cloudRGBA:new Uint8ClampedArray(16),moonRGBA:new Uint8ClampedArray(16)};}
function same(a,b){assert.equal(typeof C.sameNativePresentation,'function','Native unchanged-input guard must exist');return C.sameNativePresentation(a,b);}
test('CP9 exact same worker frame, geometry and native pixel bytes permit a redundant presentation skip',()=>{let a=f(),b={...a,cloudRGBA:a.cloudRGBA.slice(),moonRGBA:a.moonRGBA.slice()};assert.equal(same(a,b),true);});
test('CP9 new physical frame is never skipped even when the native foreground matches',()=>{let a=f(),b={...a,frame:{}};assert.equal(same(a,b),false);});
test('CP9 changed native cloud opacity or colour is never skipped',()=>{for(let k=0;k<4;k++){let a=f(),b={...a,cloudRGBA:a.cloudRGBA.slice()};b.cloudRGBA[k]=1;assert.equal(same(a,b),false);}});
test('CP9 changed PBR pixel or phase opacity is never skipped',()=>{for(let k=0;k<4;k++){let a=f(),b={...a,moonRGBA:a.moonRGBA.slice()};b.moonRGBA[k]=1;assert.equal(same(a,b),false);}});
test('CP9 moved calendar cutout and changed support rows invalidate the exact presentation cache',()=>{let a=f();assert.equal(same(a,{...a,maskKey:'mask-2'}),false);assert.equal(same(a,{...a,rows:3}),false);});
test('CP9 absent prior presentation and changed capture length are never reused',()=>{let a=f();assert.equal(same(null,a),false);assert.equal(same(a,{...a,moonRGBA:new Uint8ClampedArray(12)}),false);});
