import test from 'node:test';import assert from 'node:assert/strict';
import {nativeDiscMask} from '../../real-sky/native-contract.mjs';
import {nativeDiscMask as legacy} from '../../tools/cp9/fixtures/native-disc-mask-cp83.mjs';
test('CP9 Moon mask reads each native matrix coefficient once, not per raster sample',()=>{
 let reads=0;const m={};for(const [k,v] of Object.entries({a:1,b:.1,c:-.1,d:1,e:30,f:50}))Object.defineProperty(m,k,{get(){reads++;return v;}});
 nativeDiscMask(325,183,{left:4,top:8,width:325,height:183},m,50);assert.equal(reads,6);
});
test('CP9 hoisted mask is bit-identical to the CP8.3 equation across affine transforms and display scales',()=>{
 for(const dpr of [1,1.37,2,3])for(const m of [{a:1,b:0,c:0,d:1,e:162,f:70},{a:.8,b:.3,c:-.2,d:1.1,e:100,f:120},{a:-1,b:.2,c:.1,d:1,e:150,f:-40}])for(const radius of [0,1,50,100]){
  const rect={left:3.2,top:-9.7,width:325*dpr,height:183*dpr},a=nativeDiscMask(325,183,rect,m,radius),b=legacy(325,183,rect,m,radius);assert.deepEqual(new Uint8Array(a.buffer),new Uint8Array(b.buffer));
 }
});
test('CP9 mask hoisting does not cache across moved Moon transforms or swallow singular input',()=>{
 const r={left:0,top:0,width:50,height:50},m={a:1,b:0,c:0,d:1,e:10,f:10};const first=nativeDiscMask(50,50,r,m,6);m.e=30;assert.notDeepEqual(nativeDiscMask(50,50,r,m,6),first);assert.throws(()=>nativeDiscMask(50,50,r,{...m,d:0},6),/Singular/);
});
