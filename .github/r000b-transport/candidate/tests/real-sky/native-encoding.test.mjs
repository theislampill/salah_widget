import test from 'node:test';
import assert from 'node:assert/strict';
import {encodeFrame} from '../../real-sky/core/src/renderer.mjs';
import {encodeNativeFrame,nativeEncodingThresholds} from '../../real-sky/native-encoding.mjs';

function adjacent(value,direction){
 const view=new DataView(new ArrayBuffer(8));view.setFloat64(0,value);
 view.setBigUint64(0,view.getBigUint64(0)+BigInt(direction));return view.getFloat64(0);
}
test('native encoder exactly matches all 255 quantization boundaries and adjacent doubles',()=>{
 const thresholds=nativeEncodingThresholds();assert.equal(thresholds.length,256);
 for(let code=1;code<=255;code++){
  const edge=thresholds[code],values=Float64Array.of(adjacent(edge,-1),edge,adjacent(edge,1));
  const actual=encodeNativeFrame(values,1);assert.deepEqual(actual,encodeFrame(values,1));
  assert.equal(actual[0],code-1);assert.equal(actual[1],code);assert.equal(actual[2],code);
 }
});
test('native encoder matches the oracle across exposures, negative channels, saturation and random doubles',()=>{
 let seed=91237;const random=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/2**32);
 const values=new Float64Array(180000);
 for(let i=0;i<values.length;i++)values[i]=(random()-.01)*10**(random()*616-308);
 for(const exposure of [0,1e-12,.001,.37,1,24,100000])assert.deepEqual(encodeNativeFrame(values,exposure),encodeFrame(values,exposure));
});
test('native encoder keeps boundary equality after rounded exposure multiplication',()=>{
 for(const exposure of [.003,.1,.7,24,99,100000])for(const edge of nativeEncodingThresholds().slice(1)){
  const x=edge/exposure,values=Float64Array.of(adjacent(x,-1),x,adjacent(x,1));
  assert.deepEqual(encodeNativeFrame(values,exposure),encodeFrame(values,exposure));
 }
});
test('native encoder retains invalid-buffer/channel/exposure rejection',()=>{
 for(const [buffer,exposure] of [[Float64Array.of(1),1],[Float64Array.of(1,NaN,3),1],[Float64Array.of(1,Infinity,3),1],[Float64Array.of(1,2,3),-1],[Float64Array.of(1,2,3),100001],[Float64Array.of(1,2,3),NaN]]){
  assert.throws(()=>encodeFrame(buffer,exposure));assert.throws(()=>encodeNativeFrame(buffer,exposure));
 }
 assert.deepEqual(encodeNativeFrame(new Float64Array(0),24),encodeFrame(new Float64Array(0),24));
});
