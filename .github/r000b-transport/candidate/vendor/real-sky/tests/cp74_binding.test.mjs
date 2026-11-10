import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
const api=await import('../src/diffuse-binding.mjs').catch(()=>({}));
const sha=await import('../src/sha256.mjs').catch(()=>({}));
const text=fs.readFileSync(new URL('../data/bright-stars.json',import.meta.url),'utf8');
const asset=JSON.parse(fs.readFileSync(new URL('../data/registered-starlight/V-nside32.json',import.meta.url),'utf8'));
test('portable SHA256 matches independent Node crypto, padding boundaries and unicode',()=>{
 assert.equal(typeof sha.sha256Hex,'function');
 for(const s of ['', 'abc','\u0645\u062c\u0631\u0629 🌌',text,...[55,56,63,64,65,127,128,4097].map(n=>'a'.repeat(n))])
  assert.equal(sha.sha256Hex(new TextEncoder().encode(s)),createHash('sha256').update(s).digest('hex'));
});
test('binding verifies the actual catalogue bytes and freezes catalogue identity',()=>{
 assert.equal(typeof api.bindRegisteredStarlight,'function');const b=api.bindRegisteredStarlight(text,asset);
 assert.equal(b.catalogueSha256,asset.catalogueSha256);assert.equal(b.catalogue.stars.length,8921);
 assert.ok(Object.isFrozen(b.catalogue.stars[0]));assert.ok(api.isBoundRegisteredStarlight(b));
 assert.throws(()=>{b.catalogue.stars[0].vmag=99;});
 assert.throws(()=>api.bindRegisteredStarlight(text+' ',asset),/catalogue.*hash/i);
});
test('binding does not accept a forged descriptor or old HYG diagnostic',()=>{
 assert.equal(typeof api.isBoundRegisteredStarlight,'function');assert.equal(api.isBoundRegisteredStarlight({catalogueSha256:asset.catalogueSha256}),false);
 assert.throws(()=>api.bindRegisteredStarlight(text,{...asset,dataAdmitted:false}));
});
