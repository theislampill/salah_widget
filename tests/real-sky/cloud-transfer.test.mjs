import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeForeground} from '../../real-sky/native-composition.mjs';
import {encodeNativeFrame} from '../../real-sky/native-encoding.mjs';

const draw=(rgba,base=[0,0,0])=>[...encodeNativeFrame(nativeForeground(new Float64Array(base),{cloudRGBA:new Uint8ClampedArray(rgba),exposure:12}).linear,12)];
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
