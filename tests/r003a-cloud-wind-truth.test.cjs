'use strict';
// R003A R3A-02 (CI-06): executable form of the documented wind facts. `cloudState.wy` is retained (a pinned R000B
// native fixture records it and an accepted r0025 mutation anchors on its assignment), but it is not a drift input.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {fixture,sourcePath}=require('./weather-no-timetable-fixture.cjs');
const source=fs.readFileSync(sourcePath,'utf8');

test('R3A-02 production source writes cloudState.wy once and never reads it',()=>{
 const uses=[...source.matchAll(/\b(?:CS|S|cloudState)\.wy\b/g)].map(m=>source.slice(m.index,m.index+12));
 assert.deepEqual(uses,['CS.wy=A.wind'],'one assignment in applyCloudState, no reader');
 assert.equal((source.match(/\bwy:0\.2\b/g)||[]).length,1,'one initialiser');
});
test('R3A-02 drift uses only the horizontal component: changing wy moves no cloud phase (negative control)',async()=>{
 const advance=async(wx,wy)=>{const h=await fixture();h.at(890500);h.run('advanceCloudMotion(simNow()/1000)');
  h.run(`cloudState.wx=${wx};cloudState.wy=${wy};cloudState.wspd=0.3`);h.at(891500);h.run('advanceCloudMotion(simNow()/1000)');
  return h.run('JSON.stringify(_cloudMotion.phase)');};
 const base=await advance(0.7,-1);
 assert.equal(await advance(0.7,1),base,'wy has no effect on travel');
 assert.notEqual(await advance(-0.7,-1),base,'control: the probe is sensitive to wx');
});
test('R3A-02 calm and missing-direction fallbacks keep a decorative drift with opposite signs',async()=>{
 const h=await fixture();
 const none=JSON.parse(h.run('JSON.stringify(wxDrivers(null))'));
 assert.equal(none.windX,-0.7);assert.equal(none.wind,0);
 const noDir=JSON.parse(h.run('JSON.stringify(wxDrivers({wind:0.3}))'));
 assert(Math.abs(noDir.windX-Math.SQRT1_2)<1e-12,'225 degree fallback gives +sin 45');assert.equal(noDir.wind,0,'below 0.5 m/s is calm');
 const live=JSON.parse(h.run('JSON.stringify({d:wxDrivers(),wx:cloudState.wx,wspd:cloudState.wspd})'));
 assert.equal(live.wx,live.d.windX,'applyCloudState installs wxDrivers windX');
 assert.equal(live.wspd,0.06+0.6*live.d.wind,'wspd = 0.06 + 0.6 * wind, so calm air still drifts at 0.06');
});
