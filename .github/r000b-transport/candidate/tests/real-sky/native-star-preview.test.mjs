import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {NativeStarPreview,joinNativeStarPreview,nativeStarPreviewRegion} from '../../real-sky/native-star-preview.mjs';
import {renderNativeBackgroundPreview} from '../../real-sky/native-preview.mjs';
import {encodeNativeFrame} from '../../real-sky/native-encoding.mjs';
import {nativeCalendarRegion,nativeForeground,nativeInverseCode} from '../../real-sky/native-composition.mjs';
import * as previewModule from '../../real-sky/native-star-preview.mjs';
import {renderStars} from '../../real-sky/core/src/renderer.mjs';
const read=p=>fs.readFileSync(new URL('../../vendor/real-sky/'+p,import.meta.url),'utf8');
const pack={catalogueText:read('data/bright-stars.json'),manifestText:read('data/registered-starlight/runtime-manifest.json')};
const s=t=>({utcMs:Date.parse(t),lat:28.5383,lon:-81.3792,heightM:0,generation:1,sceneIdentity:'star-preview-test',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:0,code:0,temp:24},units:'c',lp:0});
// Report a bounded assertion if a full-frame negative control differs; dumping
// half a million array entries obscures the failure and can exhaust the runner.
const sameBytes=(a,b,label)=>assert.ok(Buffer.from(a.buffer,a.byteOffset,a.byteLength).equals(Buffer.from(b.buffer,b.byteOffset,b.byteLength)),label);

test('asynchronous catalogue admission keeps exact pinned sources and rejects equal-length tampering',async()=>{
 assert.equal(typeof NativeStarPreview.create,'function');
 const sync=new NativeStarPreview(pack),async=await NativeStarPreview.create(pack);
 assert.deepEqual(async.catalogue,sync.catalogue);assert.deepEqual(async.identity,sync.identity);
 const p=renderNativeBackgroundPreview(s('2026-10-08T00:00:00Z'));
 assert.deepEqual(async.render(p.job,p.raster.physicalState).linear,sync.render(p.job,p.raster.physicalState).linear);
 await assert.rejects(NativeStarPreview.create({...pack,catalogueText:pack.catalogueText.replace('hyg:','xyz:')}),/hash mismatch/);
 await assert.rejects(NativeStarPreview.create({...pack,catalogueText:pack.catalogueText+' '}),/byte size mismatch/);
 await assert.rejects(NativeStarPreview.create({...pack,manifestText:pack.manifestText+' '}),/manifest hash mismatch/i);
});

test('separable preview PSF preserves every reference linear sample, including fractional and clipped sources',()=>{
 assert.equal(typeof previewModule.renderPreviewStars,'function');
 const stars=Array.from({length:40},(_,i)=>({x:(i*17.137)%329-2,y:(i*41.371)%534-2,altDeg:i===1?-1:20,visible:i!==2,emission:{enabled:i!==3},rgb:[(i%7)*.07,(i%5)*.031,(i%3)*.9]}));
 const fluxAt=s=>({rgb:s.rgb}),sourceVisibility=s=>s!==stars[4];
 const reference=renderStars(stars,{width:325,height:530,fluxAt,sourceVisibility});
 const actual=previewModule.renderPreviewStars(stars,fluxAt,sourceVisibility);
 assert.deepEqual(actual.linear,reference.linear,'Exact binary64 samples, not only a frame-average tolerance');
 assert.equal(actual.drawn,reference.drawn);
 for(const E of [.0001,.003,1,24])assert.deepEqual(encodeNativeFrame(actual.linear,E),encodeNativeFrame(reference.linear,E));
});
test('current bright-catalogue stars return through apparent contrast, without a solar/prayer switch',()=>{
 const renderer=new NativeStarPreview(pack),rows=[];
 for(const t of ['2026-10-07T23:05:00Z','2026-10-07T23:25:00Z','2026-10-07T23:40:00Z','2026-10-08T00:00:00Z']){
  const p=renderNativeBackgroundPreview(s(t)),stars=renderer.render(p.job,p.raster.physicalState),base=encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure),joined=joinNativeStarPreview(p,base,stars),after=encodeNativeFrame(joined.raster.linear,p.raster.effectiveExposure);
  let visible=0;for(let i=0;i<base.length;i+=4)if(Math.max(...[0,1,2].map(k=>after[i+k]-base[i+k]))>=2)visible++;
  assert.equal(stars.diagnostics.utcMs,s(t).utcMs);assert.ok(stars.sources.every(x=>x.vmag<=4.5));rows.push(visible);
 }
 assert.equal(rows[0],0,'No false daytime stars');assert.ok(rows[2]>0,'Clear late twilight cannot remain starless');assert.ok(rows[3]>rows[2]&&rows[2]>rows[1],'Gradual contrast-driven return: '+rows);
});
test('preview rejects corrupt catalogue and preserves opaque lunar cutout plus once-only clouds',()=>{
 assert.throws(()=>new NativeStarPreview({...pack,catalogueText:pack.catalogueText+' '}),/byte size mismatch/);
 const p=renderNativeBackgroundPreview(s('2026-10-08T00:00:00Z')),renderer=new NativeStarPreview(pack),stars=renderer.render(p.job,p.raster.physicalState),base=encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure),r=joinNativeStarPreview(p,base,stars).raster;
 const mask=new Float64Array(325*530).fill(0),cut=nativeCalendarRegion(r,mask);
 assert.deepEqual(cut,r.skyBackgroundLinear,'Calendar opacity removes distant sources, not foreground air');
 const cloud=new Uint8ClampedArray(325*530*4);for(let i=0;i<cloud.length;i+=4){cloud[i]=100;cloud[i+1]=110;cloud[i+2]=120;cloud[i+3]=255;}
 const covered=encodeNativeFrame(nativeForeground(r.linear,{cloudRGBA:cloud,exposure:r.effectiveExposure}).linear,r.effectiveExposure);
 assert.deepEqual(covered,cloud,'Opaque cloud must cover stars once, without colour amplification');
});

test('sparse preview encoding and moving lunar mask equal the full linear compositor byte for byte',()=>{
 const renderer=new NativeStarPreview(pack);
 for(const time of ['2026-10-07T16:00:00Z','2026-10-07T23:25:00Z','2026-10-08T00:00:00Z']){
  const p=renderNativeBackgroundPreview(s(time)),stars=renderer.render(p.job,p.raster.physicalState),base=encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure),joined=joinNativeStarPreview(p,base,stars),r=joined.raster;
  assert.deepEqual(joined.rgba,encodeNativeFrame(r.linear,r.effectiveExposure));
  const rows=213,mask=new Float64Array(325*rows).fill(1);
  for(let y=30;y<160;y++)for(let x=185;x<320;x++)mask[y*325+x]=x===185?.37:0;
  assert.deepEqual(nativeStarPreviewRegion(joined,mask,rows),encodeNativeFrame(nativeCalendarRegion(r,mask,rows),r.effectiveExposure));
  assert.deepEqual(nativeStarPreviewRegion(joined,null,rows),joined.rgba.subarray(0,325*rows*4));
 }
});

test('daylight work culling uses an encoded contrast bound and preserves the exact displayed result',()=>{
 const renderer=new NativeStarPreview(pack);let culled=0;
 for(const time of ['2026-10-07T16:00:00Z','2026-10-07T22:30:00Z','2026-10-07T23:25:00Z','2026-10-08T00:00:00Z']){
  const p=renderNativeBackgroundPreview(s(time)),base=encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure),full=renderer.render(p.job,p.raster.physicalState),bounded=renderer.render(p.job,p.raster.physicalState,{background:base,exposure:p.raster.effectiveExposure});
  const a=joinNativeStarPreview(p,base,full),b=joinNativeStarPreview(p,base,bounded);
  assert.deepEqual(b.rgba,a.rgba,'No displayed byte changes: '+time);
  culled+=!!bounded.diagnostics.belowByteResolution;
  if(time.endsWith('00:00:00Z'))assert.ok(!bounded.diagnostics.belowByteResolution&&bounded.drawn>0,'No hard twilight or night gate');
 }
 assert.ok(culled>0,'Daylight must avoid provably invisible PSF work');
});

test('display preparation does not allocate unused full raw sky planes',()=>{
 const p=renderNativeBackgroundPreview(s('2026-10-08T00:00:00Z')),base=encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure),stars=new NativeStarPreview(pack).render(p.job,p.raster.physicalState);
 const Original=globalThis.Float64Array,n=325*530*3;let planes=0,joined;
 globalThis.Float64Array=new Proxy(Original,{construct(target,args){const value=Reflect.construct(target,args);if(value.length===n)planes++;return value;}});
 try{joined=joinNativeStarPreview(p,base,stars);}finally{globalThis.Float64Array=Original;}
 // One owned stellar snapshot is allowed; gas/combined full raw planes are
 // unnecessary to prepare displayed bytes. Read consumers still get them.
 assert.ok(planes<=1,`Prepared ${planes} full raw planes before any consumer read`);
 const decode=Float64Array.from({length:256},(_,c)=>nativeInverseCode(c,p.raster.effectiveExposure)),gas=new Float64Array(n),linear=new Float64Array(n);
 for(let i=0;i<n;i++){gas[i]=decode[base[4*Math.floor(i/3)+i%3]];linear[i]=gas[i]+stars.linear[i];}
 sameBytes(joined.raster.skyBackgroundLinear,gas,'exact raw foreground atmosphere');assert.strictEqual(joined.raster.backgroundLinear,joined.raster.skyBackgroundLinear);
 sameBytes(joined.raster.linear,linear,'exact combined raw field');sameBytes(joined.rgba,encodeNativeFrame(linear,p.raster.effectiveExposure),'exact displayed bytes');
 assert.strictEqual(joined.raster.linear,joined.raster.linear,'A raw consumer receives one stable per-frame field');
});

test('prepared sky owns its source bytes and stars; later inputs cannot alter lunar masks or raw fields',()=>{
 const p=renderNativeBackgroundPreview(s('2026-10-08T00:00:00Z')),base=encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure),stars=new NativeStarPreview(pack).render(p.job,p.raster.physicalState),savedBase=base.slice(),savedStars=stars.linear.slice(),joined=joinNativeStarPreview(p,base,stars);
 base.fill(0);stars.linear.fill(NaN);
 sameBytes(joined.atmosphereRGBA,savedBase,'prepared atmosphere cannot alias later input');sameBytes(joined.raster.stellarLinear,savedStars,'prepared stars cannot alias later input');
 const rows=181,mask=new Float64Array(325*rows).fill(1);for(let i=0;i<mask.length;i+=17)mask[i]=i%3/2;
 sameBytes(nativeStarPreviewRegion(joined,mask,rows),encodeNativeFrame(nativeCalendarRegion(joined.raster,mask,rows),joined.raster.effectiveExposure),'fractional lunar mask exact reference');
 assert.ok(joined.raster.linear.every(Number.isFinite));
});

test('unused malformed stellar tail is rejected before any displayed frame can be prepared',()=>{
 const p=renderNativeBackgroundPreview(s('2026-10-07T16:00:00Z')),base=encodeNativeFrame(p.raster.linear,p.raster.effectiveExposure);
 for(const bad of [NaN,Infinity,-.1,null,'1']){
  const linear=typeof bad==='number'?new Float64Array(325*530*3):Array(325*530*3).fill(0);linear[linear.length-1]=bad;
  assert.throws(()=>joinNativeStarPreview(p,base,{linear,diagnostics:{belowByteResolution:true}}),/Catalogue preview channel/);
 }
});
