import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {NativeStarPreview} from '../../real-sky/native-star-preview.mjs';
import {renderNativeBackgroundPreview} from '../../real-sky/native-preview.mjs';

const text=fs.readFileSync(new URL('../../vendor/real-sky/data/bright-stars.json',import.meta.url),'utf8');
const catalogue=JSON.parse(text),hash=s=>crypto.createHash('sha256').update(s).digest('hex');
// Lossless numeric/source fields actually consumed by astrometry and spectrum.
// Full record metadata and the complete catalogue remain in the full data pack.
const fields=['hygId','hip','raDeg','decDeg','epochJyear','vmag','bv','pmRaCosDecMasYr','pmDecMasYr','distancePc','radialVelocityKmS','spectralType','sed'];
const selected=catalogue.stars.filter(s=>s.emission?.enabled!==false&&s.vmag<=4.5);
const body={schema:'salah-real-sky/bootstrap/1',parentSha256:hash(text),totalRecords:catalogue.stars.length,maximumMagnitude:4.5,fields,rows:selected.map(s=>fields.map(k=>s[k]??null))};
const payload=JSON.stringify(body),pin={sha256:hash(payload),bytes:Buffer.byteLength(payload),parentSha256:hash(text),records:921};
const fullPack={catalogueText:text,manifestText:fs.readFileSync(new URL('../../vendor/real-sky/data/registered-starlight/runtime-manifest.json',import.meta.url),'utf8')};

test('real bright sources can be admitted without requesting or parsing the full pack',()=>{
 assert.equal(typeof NativeStarPreview.fromBootstrap,'function','compact independent first-scene source is missing');
 const seed=NativeStarPreview.fromBootstrap(payload,pin);
 assert.equal(seed.catalogue.stars.length,921);
 assert.equal(seed.identity.sha256,hash(text));
 assert.equal(seed.identity.bootstrapSha256,pin.sha256);
 assert.ok(Buffer.byteLength(payload)<130000,'startup subset must stay bounded');
 for(let i=0;i<selected.length;i++){
  const a=seed.catalogue.stars[i],b=selected[i];
  assert.equal(a.id,b.id);
  for(const key of fields)assert.deepEqual(a[key]??null,b[key]??null,key);
 }
});

test('bootstrap uses exactly the approved preview photons for independent observer/time controls',()=>{
 assert.equal(typeof NativeStarPreview.fromBootstrap,'function');
 const seed=NativeStarPreview.fromBootstrap(payload,pin),full=new NativeStarPreview(fullPack);
 for(const [lat,lon,utc] of [[28.5383,-81.3792,'2026-09-25T02:00:00Z'],[-33.87,151.21,'2026-10-09T12:00:00Z'],[60,10,'2027-01-15T00:00:00Z']]){
  const s={lat,lon,utcMs:Date.parse(utc),heightM:0,generation:1,sceneIdentity:'bootstrap-control',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:0,code:0,temp:24},units:'c',lp:0};
  const p=renderNativeBackgroundPreview(s),a=seed.render(p.job,p.raster.physicalState),b=full.render(p.job,p.raster.physicalState);
  assert.ok(Buffer.from(a.linear.buffer).equals(Buffer.from(b.linear.buffer)),'astrometry, spectral flux and PSF must remain byte exact');
 }
});

test('independent bootstrap refuses tampering, wrong ancestry, empty and nonfinite records',()=>{
 assert.equal(typeof NativeStarPreview.fromBootstrap,'function');
 assert.throws(()=>NativeStarPreview.fromBootstrap(payload+' ',pin),/identity|size|hash/);
 assert.throws(()=>NativeStarPreview.fromBootstrap(payload,{...pin,parentSha256:'0'.repeat(64)}),/parent|ancestry/);
 for(const mutate of [b=>b.rows.splice(0),b=>b.rows[0][2]=null,b=>b.rows[0][5]=7]){
  const b=structuredClone(body);mutate(b);const p=JSON.stringify(b);
  assert.throws(()=>NativeStarPreview.fromBootstrap(p,{...pin,sha256:hash(p),bytes:Buffer.byteLength(p)}),/record|catalogue|RA|magnitude|finite|empty/);
 }
});
