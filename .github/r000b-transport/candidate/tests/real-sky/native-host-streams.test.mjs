import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import vm from 'node:vm';
import {encodeNativeFrame,nativeEncodingThresholds} from '../../real-sky/native-encoding.mjs';
import {encodeNativeDisplay,encodeNativeDisplayInto} from '../../real-sky/native-host.mjs';
const words=new BigUint64Array(1),float=new Float64Array(words.buffer),edges=nativeEncodingThresholds();
function adjacent(value,delta){float[0]=value;words[0]+=BigInt(delta);return float[0];}
function stream(){const a=[];for(const sign of [1,-1])for(let n=0;n<255;n++){const i=sign===1?n+1:255-n;for(const d of [-1,0,1]){const v=adjacent(edges[i],d);for(let hit=0;hit<5;hit++)a.push(v,edges[256-i],hit%2?v:0);}}return Float64Array.from(a);}
test('per-call intervals cross all oracle edges forwards/backwards after repeated hits',()=>{
 const raw=stream(),before=raw.slice();
 for(const E of [1,100000,0,.5,12,1e-10,24,1])assert.deepEqual(encodeNativeDisplay(raw,E),encodeNativeFrame(raw,E));
 assert.deepEqual(raw,before);
});
test('private destination writes only its declared region and preserves exact return identity',()=>{
 const raw=stream(),n=raw.length/3*4,bytes=new Uint8ClampedArray(n+20).fill(37),expected=encodeNativeFrame(raw,12);
 assert.equal(encodeNativeDisplayInto(raw,12,bytes,8),bytes);assert.deepEqual(bytes.subarray(8,8+n),expected);
 assert(bytes.subarray(0,8).every(v=>v===37));assert(bytes.subarray(8+n).every(v=>v===37));
 assert.equal(encodeNativeDisplayInto([],12,bytes,bytes.length),bytes);
});
test('finite-product overflow saturation and neutral channels survive an interval hit',()=>{
 const raw=Float64Array.from([0,0,0,.003,.003,.003,.003,.003,.003,Number.MAX_VALUE,Number.MAX_VALUE,Number.MAX_VALUE,0,Number.MAX_VALUE,1,0,0,0]);
 for(const E of [0,1,100000])assert.deepEqual(encodeNativeDisplay(raw,E),encodeNativeFrame(raw,E));
});
test('invalid channels after an interval hit still reject without a successful result',()=>{
 for(let c=0;c<3;c++)for(const bad of [NaN,Infinity,-Infinity]){const raw=new Float64Array(90).fill(.003);raw[87+c]=bad;assert.throws(()=>encodeNativeDisplay(raw,12),RangeError);assert.throws(()=>encodeNativeDisplayInto(raw,12,new Uint8ClampedArray(120)),RangeError);}
});
test('destination alignment/range/type and invalid exposure/dimension reject',()=>{
 for(const dest of [null,[],new Uint8Array(12),new Uint8ClampedArray(3)])assert.throws(()=>encodeNativeDisplayInto([0,0,0],12,dest),RangeError);
 for(const offset of [-4,1,2.5,NaN,Infinity,12])assert.throws(()=>encodeNativeDisplayInto([0,0,0],12,new Uint8ClampedArray(12),offset),RangeError);
 for(const E of [-1,NaN,Infinity,100001])assert.throws(()=>encodeNativeDisplayInto([0,0,0],E,new Uint8ClampedArray(4)),RangeError);
 assert.throws(()=>encodeNativeDisplayInto([0],12,new Uint8ClampedArray(4)),RangeError);
});
test('boundary comparison and destination-offset mutations are killed by exact controls',()=>{
 const source=fs.readFileSync(new URL('../../real-sky/native-host.mjs',import.meta.url),'utf8');
 const fragment=source.slice(source.indexOf('let nativeDisplayEncodeCache='),source.indexOf('// Solar obstruction'));
 const load=s=>{const c={nativeEncodingThresholds,Uint8ClampedArray,Uint8Array,Uint16Array};vm.createContext(c);vm.runInContext(s.replaceAll('export function','function'),c);return c;};
 const upper=load(fragment.replace('y<edges[previous+1]','y<=edges[previous+1]'));
 const input=Float64Array.from([adjacent(edges[1],-1),0,0,edges[1],0,0]);
 assert.throws(()=>assert.deepEqual(upper.encodeNativeDisplay(input,1),encodeNativeFrame(input,1)),assert.AssertionError);
 const offset=load(fragment.replace('let i=0,j=offset','let i=0,j=0')),bytes=new Uint8ClampedArray(12).fill(37);
 offset.encodeNativeDisplayInto([.003,.003,.003],12,bytes,4);
 assert.throws(()=>assert(bytes.subarray(0,4).every(v=>v===37)),assert.AssertionError);
});
