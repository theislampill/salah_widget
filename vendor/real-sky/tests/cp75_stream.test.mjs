import test from 'node:test';import assert from 'node:assert/strict';import {readDiffuseAssetText} from '../src/diffuse-assets.mjs';
async function mock(response,fn){const original=globalThis.fetch;globalThis.fetch=async()=>response;try{return await fn();}finally{globalThis.fetch=original;}}
test('streamed UTF-8 rejects invalid encoding and enforces actual bytes even without Content-Length',async()=>{
 await mock(new Response(new Uint8Array([0xff])),()=>assert.rejects(()=>readDiffuseAssetText('local',{maxBytes:2}),/encoded|encoding/i));
 await mock(new Response('abc'),()=>assert.rejects(()=>readDiffuseAssetText('local',{maxBytes:2}),/budget/));
 await mock(new Response('αβ'),async()=>assert.equal(await readDiffuseAssetText('local',{maxBytes:4}),'αβ'));
});
test('oversized declared body is cancelled immediately, not left downloading after rejection',async()=>{
 let cancelled=false;const body=new ReadableStream({start(c){c.enqueue(new TextEncoder().encode('abc'));},cancel(){cancelled=true;}});
 await mock(new Response(body,{headers:{'content-length':'100'}}),()=>assert.rejects(()=>readDiffuseAssetText('local',{maxBytes:2}),/budget/));assert.equal(cancelled,true);
});
test('HTTP errors and absent bodies fail explicitly',async()=>{
 await mock(new Response('',{status:404}),()=>assert.rejects(()=>readDiffuseAssetText('local'),/404/));
 await mock({ok:true,headers:new Headers(),body:null},()=>assert.rejects(()=>readDiffuseAssetText('local'),/body missing/));
});
