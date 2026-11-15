'use strict';
// R0036 (issue 103) PRA-F-15(e) / OM-05: acquisition flags describe the latest attempt of their kind. Actual config
// resolution, boot, applyConfig and settings source through the r0011 fixture; providers (coarse detection, GPS,
// prayer) are recorded deferreds, never contacted. R0036_ROOT=<dir> reads that tree's index.html (RED/mutation runs).
const assert=require('node:assert/strict'),{test}=require('node:test');
const {widget,drain}=require('./r0011-fixture.cjs');
const fs=require('node:fs'),path=require('node:path');
const source=process.env.R0036_ROOT?fs.readFileSync(path.join(process.env.R0036_ROOT,'index.html'),'utf8'):undefined;
const seed={lat:51.5,lon:-.12,label:'London',method:'3',units:'f',source:'manual'};
const detected={ok:true,provider:'ipapi',cfg:{lat:24.47,lon:39.61,label:'Madinah',area:'Madinah, SA',method:'4',units:'c',source:'coarse-ip'}};

test('R36-20 boot detection abandoned by a newer generation ends "superseded", not "pending"',async()=>{
  const f=widget({source,open:false});const p=f.boot();await drain();
  assert.equal(f.run('_autoDetectStatus'),'pending');assert.equal(f.calls.coarse.length,1);
  // A settings close-save of manual coordinates begins a new generation while boot detection is in flight.
  f.run('_cfgMode="local"; _enableSettingsAffordance(); _openSettings();');
  f.input('set-lat','40.7');f.input('set-lon','-74');f.input('set-label','New York');f.click('setClose');await drain();
  assert.ok(f.run('_runtimeGeneration')>=1,'the save began a new generation');
  await f.resolveCall('coarse',0,detected);await p;
  assert.equal(f.run('_autoDetectStatus'),'superseded');assert.equal(f.run('_autoDetectSource'),null);
  assert.equal(f.config().lat,40.7,'the newer manual location is retained');
});

test('R36-21 Reset-driven detection keeps its own record: ok with source, failed, and owned by the newer of two Resets',async()=>{
  const ok=widget({source,seed});ok.click('set-reset');await drain();
  assert.equal(ok.json('_resetDetect').status,'pending');
  await ok.resolveCall('coarse',0,detected);
  const r=ok.json('_resetDetect');assert.equal(r.status,'ok');assert.equal(r.source,'ipapi');assert.equal(typeof r.at,'number');
  assert.equal(ok.run('_autoDetectStatus'),'idle','boot flag untouched by Reset detection');
  const failed=widget({source,seed});failed.click('set-reset');await failed.resolveCall('coarse',0,{ok:false});
  assert.equal(failed.json('_resetDetect').status,'failed');assert.equal(failed.json('_resetDetect').source,null);
  const twice=widget({source,seed});twice.click('set-reset');await drain();const first=twice.json('_resetDetect').attempt;
  twice.storage.set(twice.sandbox.SalahConfig.KEY,JSON.stringify({...seed,v:1}));   // a saved record to clear again
  twice.click('set-reset');await drain();
  await twice.resolveCall('coarse',0,detected);
  const now=twice.json('_resetDetect');assert.notEqual(now.attempt,first);assert.equal(now.status,'pending','only the newer Reset owns the record');
  await twice.resolveCall('coarse',1,{ok:false});assert.equal(twice.json('_resetDetect').status,'failed');
});

test('R36-22 a GPS error is scoped to its attempt: superseded once a newer location intent replaces it',async()=>{
  const f=widget({source,seed});f.click('set-pin');await drain();
  f.calls.gps[0].reject({code:1,message:'denied'});await drain();
  assert.equal(f.run('_geoLastError'),'denied');
  const live=f.json('geolocationAttemptView()');assert.equal(live.outcome,'error');assert.equal(live.error,'denied');assert.equal(live.superseded,false);
  // Manual coordinates typed and the panel closed: the error no longer describes the current location intent.
  f.input('set-lat','40.7');f.input('set-lon','-74');f.click('setClose');await drain();
  const after=f.json('geolocationAttemptView()');assert.equal(after.superseded,true);assert.equal(after.attempt,live.attempt);
  assert.equal(f.run('_geoLastError'),'denied','the compatibility string is retained; currentness is reported beside it');
});
