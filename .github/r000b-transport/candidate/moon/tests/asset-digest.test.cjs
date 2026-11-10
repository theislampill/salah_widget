'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=process.env.SALAH_TEST_ROOT?path.resolve(process.env.SALAH_TEST_ROOT):path.resolve(__dirname,'../..');
const source=fs.readFileSync(path.join(root,'moon/src/asset-digest.mjs'),'utf8');
const digest=Function(source+';return assetDigest;')();
const oracle=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');

test('portable asset identity agrees with independent published SHA-256 vectors',()=>{
 for(const [text,want]of [
  ['', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'],
  ['abc','ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'],
  ['abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq','248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1']
 ])assert.equal(digest(new Uint8Array(Buffer.from(text))),want);
});

test('padding and block carry agree with OpenSSL on both sides of boundaries',()=>{
 for(const length of [1,3,55,56,63,64,65,119,120,127,128,129,4095,4096,4097]){
  const bytes=Uint8Array.from({length},(_,i)=>(i*173+(i>>>3)*31)&255);
  assert.equal(digest(bytes),oracle(bytes),'length '+length);
 }
});

test('digest uses only a nonzero-offset byte view and leaves caller storage intact',()=>{
 const backing=Uint8Array.from({length:300},(_,i)=>(i*43+19)&255),before=backing.slice(),view=backing.subarray(11,140);
 assert.equal(digest(view),oracle(view));assert.deepEqual(backing,before);
 backing[0]^=255;backing[299]^=255;assert.equal(digest(view),oracle(before.subarray(11,140)));
 backing[55]^=1;assert.notEqual(digest(view),oracle(before.subarray(11,140)),'an in-view change must change asset identity');
});

test('receiver and compressed terrain assets retain OpenSSL identities across many blocks',()=>{
 for(const name of ['initial-receivers.bin','initial-compact.bin','dem.bin.gz','colour.bin.gz']){
  const bytes=new Uint8Array(fs.readFileSync(path.join(root,'moon/assets',name)));
  assert.equal(digest(bytes),oracle(bytes),name);
 }
});

test('the maximum supported byte length retains its OpenSSL identity',()=>{
 const bytes=new Uint8Array(67108864).fill(0x61);
 assert.equal(digest(bytes),oracle(bytes));
});

test('digest rejects unsupported input types and an oversized byte payload',()=>{
 for(const bytes of [null,undefined,[],new ArrayBuffer(1),new Uint16Array(1),new Int8Array(1),new Uint8Array(67108865)]){
  assert.throws(()=>digest(bytes),TypeError);
 }
});
