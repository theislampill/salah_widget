import test from 'node:test';
import assert from 'node:assert/strict';
import {encodeNativeFrame,nativeEncodingThresholds} from '../../real-sky/native-encoding.mjs';
import {encodeNativeDisplay} from '../../real-sky/native-host.mjs';

const words=new BigUint64Array(1),float=new Float64Array(words.buffer);
function adjacent(value,delta){float[0]=value;words[0]+=BigInt(delta);return float[0];}
function exact(values,exposure){
 while(values.length%3)values.push(0);
 const input=Float64Array.from(values),before=input.slice();
 assert.deepEqual(encodeNativeDisplay(input,exposure),encodeNativeFrame(input,exposure));
 assert.deepEqual(input,before);
}
test('host encoding preserves every oracle transition and surrounding binary64 values',()=>{
 const edges=nativeEncodingThresholds();
 for(const exposure of [0,1e-10,.5,1,12,24,100000]){
  const values=[-Number.MAX_VALUE,-1,-0,0,Number.MIN_VALUE,Number.MAX_VALUE];
  for(const edge of edges.subarray(1))for(const delta of [-1,0,1]){
   const value=adjacent(edge,delta)/Math.max(exposure,Number.MIN_VALUE);
   if(Number.isFinite(value))values.push(value);
  }
  // Coloured/mixed pixels and overflowing finite channel*exposure products.
  let seed=12345;
  for(let i=0;i<24000;i++){seed=(Math.imul(seed,1664525)+1013904223)>>>0;values.push(seed/4294967296*12/Math.max(exposure,1e-10));}
  exact(values,exposure);
 }
});
test('host buckets retain exact codes on both sides of every search boundary',()=>{
 const scale=8192/nativeEncodingThresholds()[255],values=[];
 for(let bucket=1;bucket<8192;bucket++)for(const delta of [-2,-1,0,1,2]){
  const value=adjacent(bucket/scale,delta);values.push(value,value,value);
 }
 exact(values,1);exact([],1);
});
test('host encoder rejects each invalid channel and exposure before publication',()=>{
 for(const values of [[NaN,0,0],[0,Infinity,0],[0,0,-Infinity]])assert.throws(()=>encodeNativeDisplay(values,1),RangeError);
 for(const exposure of [-1,NaN,Infinity,100001])assert.throws(()=>encodeNativeDisplay([0,0,0],exposure),RangeError);
 assert.throws(()=>encodeNativeDisplay([1],1),RangeError);
});
