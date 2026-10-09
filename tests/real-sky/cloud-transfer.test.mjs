import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeForeground} from '../../real-sky/native-composition.mjs';
import {encodeNativeFrame} from '../../real-sky/native-encoding.mjs';
import {nativeCloudDisplayFrame} from '../../real-sky/native-cloud-transfer.mjs';
import * as cloudTransfer from '../../real-sky/native-cloud-transfer.mjs';

const draw=(rgba,base=[0,0,0])=>[...encodeNativeFrame(nativeForeground(new Float64Array(base),{cloudRGBA:new Uint8ClampedArray(rgba),exposure:12}).linear,12)];
test('display-byte quantization preserves the independent sRGB transfer at every code boundary',()=>{
 assert.equal(typeof cloudTransfer.nativeDisplayCode,'function');
 const reference=v=>Math.round(255*(v<=.0031308?12.92*v:1.055*v**(1/2.4)-.055));
 for(let i=0;i<=131072;i++)assert.equal(cloudTransfer.nativeDisplayCode(i/131072),reference(i/131072));
 for(let i=0;i<255;i++){
  const s=(i+.5)/255,v=s<=.04045?s/12.92:((s+.055)/1.055)**2.4;
  for(const d of [-1e-12,-Number.EPSILON,0,Number.EPSILON,1e-12])assert.equal(cloudTransfer.nativeDisplayCode(v+d),reference(v+d));
 }
});

test('every byte-valued cloud colour and alpha matches the original bounded display join',()=>{
 // Independent, direct sRGB expression; no shared lookup or encoder. Cover
 // 256 cubed foreground/background/alpha combinations, including tiny alpha.
 const linear=c=>c/255<=.04045?c/255/12.92:((c/255+.055)/1.055)**2.4;
 for(let base=0;base<256;base++){
  const bg=new Uint8ClampedArray(256*256*4),cloud=new Uint8ClampedArray(bg.length);
  for(let c=0;c<256;c++)for(let a=0;a<256;a++){const i=4*(256*c+a);bg.set([base,base,base,255],i);cloud.set([c,c,c,a],i);}
  const actual=nativeCloudDisplayFrame(bg,cloud);
  for(let c=0;c<256;c++)for(let a=0;a<256;a++){
   const v=linear(base)*(1-a/255)+linear(c)*a/255,code=Math.round(255*(v<=.0031308?12.92*v:1.055*v**(1/2.4)-.055)),i=4*(256*c+a);
   assert.equal(actual[i],code);assert.equal(actual[i+1],code);assert.equal(actual[i+2],code);assert.equal(actual[i+3],255);
  }
 }
});
test('one-byte coloured cloud fringe cannot expand into a bright HDR spark',()=>{
 // Canvas unpremultiplication at alpha=1 can return saturated channels. This
 // captured failure is display colour, not evidence of infinite cloud radiance.
 assert.deepEqual(draw([255,0,255,1]),[13,0,13,255]);
});
test('cloud opacity is applied once in bounded display-linear light',()=>{
 // Half opaque black over a display-white background: linear display 127/255,
 // independently calculated sRGB code 187, not an almost-white HDR remnant.
 assert.deepEqual(draw([0,0,0,128],[100,100,100]),[187,187,187,255]);
});
test('malformed cloud channels are rejected before publication',()=>{
 for(const cloudRGBA of [[NaN,0,0,20],[256,0,0,20],[0,0,0,-1]])
  assert.throws(()=>nativeForeground(new Float64Array([0,0,0]),{cloudRGBA,exposure:12}));
});
test('preview cloud transfer agrees with independent display endpoints and the refined join',()=>{
 assert.deepEqual([...nativeCloudDisplayFrame([255,255,255,255],[0,0,0,128])],[187,187,187,255]);
 assert.deepEqual([...nativeCloudDisplayFrame([0,0,0,255],[255,0,255,1])],[13,0,13,255]);
 for(const code of [0,1,13,68,127,188,254,255])for(const alpha of [0,1,2,32,128,254,255]){
  const base=new Float64Array([.01,.04,.1]),encoded=encodeNativeFrame(base,12),cloud=[code,255-code,code,alpha];
  const actual=nativeCloudDisplayFrame(encoded,cloud),ref=draw(cloud,[...base]);
  for(let k=0;k<4;k++)assert.ok(Math.abs(actual[k]-ref[k])<=1,'One background byte quantization, no second exposure or coverage');
 }
});
test('preview rejects incomplete, non-opaque base and malformed cloud buffers atomically',()=>{
 for(const [base,cloud] of [[[0,0,0],[0,0,0]],[[0,0,0,254],[0,0,0,0]],[[0,0,0,255],[0,0,0]],[[0,0,0,255],[NaN,0,0,1]]])
  assert.throws(()=>nativeCloudDisplayFrame(base,cloud));
});

test('preview opaque Moon preserves atmospheric pixels and agrees with the gas-aware refined join',()=>{
 for(const alpha of [1,64,128,255]){
  const gas=new Float64Array([.03,.05,.08]),bg=encodeNativeFrame(gas,12),black=new Uint8ClampedArray([0,0,0,alpha]);
  assert.deepEqual(nativeCloudDisplayFrame(bg,new Uint8ClampedArray(4),black),bg);
  const moon=new Uint8ClampedArray([35,45,65,alpha]),cloud=new Uint8ClampedArray([180,170,160,40]);
  const preview=nativeCloudDisplayFrame(bg,cloud,moon),refined=encodeNativeFrame(nativeForeground(gas,{atmosphereLinear:gas,moonRGBA:moon,cloudRGBA:cloud,exposure:12}).linear,12);
  for(let k=0;k<4;k++)assert.ok(Math.abs(preview[k]-refined[k])<=1);
 }
});
