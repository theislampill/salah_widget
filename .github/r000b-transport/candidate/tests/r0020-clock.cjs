'use strict';
const assert = require('node:assert/strict');
const {test} = require('node:test');
const {realm, sha256, source, temporal, skySources, lifecycle, modelRealm, loadRender, loadLifecycle, prayerRecord} = require('./r0008-clock-harness.cjs');
console.log(`SOURCE ${sha256(source)} TEMPORAL ${sha256(temporal)}`);
const base=Date.parse('2026-09-07T12:00Z');
for(const step of [0,3600000,-3600000,7200000,-7200000]) {
  test(`ordinary simNow and nowParts follow wall step ${step}`, () => {
    const c=realm({wall:base}); c.run('simNow()');
    c.clock.mono=1000; c.clock.wall=base+1000+step;
    assert.equal(c.run('simNow()'), c.clock.wall);
    assert.equal(c.run('nowParts().h'), 12+step/3600000);
    assert.equal(c.run('simDate().getTime()'), c.clock.wall);
    c.run('tz="Asia/Kathmandu"');
    assert.equal(c.run('simNow()'), c.clock.wall);
  });
}

function boundaryLoop(block=lifecycle) {
  const c=loadLifecycle(loadRender(modelRealm({zone:'UTC',wall:Date.parse('2026-09-07T15:29:59Z'),
    globals:{today:prayerRecord('2026-09-07','UTC'),tomorrow:prayerRecord('2026-09-08','UTC')}})),block);
  c.run('startRenderLoop()'); c.frame();
  assert.equal(c.dom.querySelector('.cn').textContent,'Dhuhr'); assert.equal(c.run('model().nextKey'),'Asr');
  c.clock.wall=Date.parse('2026-09-07T15:30:01Z'); c.frame();
  assert.equal(c.dom.querySelector('.cn').textContent,'Asr'); assert.equal(c.run('model().nextKey'),'Maghrib');
  c.clock.wall=Date.parse('2026-09-07T15:29:59Z'); c.frame();
  return c;
}
test('actual loop renders forward and backward prayer-boundary corrections', () => {
  const c=boundaryLoop();
  assert.equal(c.dom.querySelector('.cn').textContent,'Dhuhr');
  assert(c.dom.querySelector('.left').innerHTML.includes('Asr'));
  assert.equal(c.run('model().leftMin'),1/60); assert.equal(c.calls.requests.length,0);
});

test('actual hidden/resumed loop reads the current wall once without missed-second replay', () => {
  const c=boundaryLoop();
  c.dom.visibilityState='hidden'; c.dom.listeners.get('visibilitychange')(); assert.equal(c.pending.size,0);
  if(skySources){ assert.equal(c.run('_cloudMotion.paused'),true); assert.equal(c.run('_cloudMotion.lastRt'),c.clock.mono); }
  c.clock.mono=120000;
  c.clock.wall=Date.parse('2026-09-07T18:00:01Z');
  c.dom.visibilityState='visible'; c.dom.listeners.get('visibilitychange')(); assert.equal(c.pending.size,1);
  if(skySources){ assert.equal(c.run('_cloudMotion.paused'),false); assert.equal(c.run('_cloudMotion.lastRt'),120000); }
  c.frame();
  assert.equal(c.dom.querySelector('.cn').textContent,'Maghrib'); assert(c.dom.querySelector('.left').innerHTML.includes('Isha'));
  assert.equal(c.pending.size,1); assert.equal(c.calls.requests.length,0);
});

test('anchor-only, broad-default and increasing-only loop mutants fail their independent controls', () => {
  const anchored=temporal.replace('if(FOLLOW_WALL_CLOCK) return Date.now();',''); assert.notEqual(anchored,temporal);
  const c=realm({block:anchored}); assert.equal(c.run('simNow()'),base);
  c.clock.wall=base+3600000; assert.notEqual(c.run('simNow()'),c.clock.wall);
  const broad=temporal.replace('_tsParam==null && SIM.time==null && TIMESCALE===1','_tsParam==null'); assert.notEqual(broad,temporal);
  assert.notEqual(realm({block:broad,query:'simTime=03:30'}).run('simNow()'),Date.parse('2026-09-07T03:30Z'));
  const predicate='if(sec!==_lastSec || _renderDirty)';
  assert.equal(lifecycle.split(predicate).length,2,'one actual combined clock/dirty predicate is required');
  const increasing=lifecycle.replace(predicate,'if(sec>_lastSec || _renderDirty)'); assert.notEqual(increasing,lifecycle);
  assert.equal(boundaryLoop(increasing).dom.querySelector('.cn').textContent,'Asr','mutant visibly retains the future prayer after the reverse correction');
  console.log(`MUTANT anchor-only ${sha256(anchored)} / broad-default ${sha256(broad)} / increasing-only ${sha256(increasing)} rejected`);
});
for(const step of [3600000,-3600000,7200000,-7200000]) {
  for(const [query,anchor,rate,advancing] of [
    ['timeScale=1',base,1,true], ['timeScale=60',base,60,true],
    ['timeScale=0',base,0,false], ['timeScale=',base,0,false],
    ['timeScale=invalid',base,0,false], ['timeScale=-5',base,0,false],
    ['simTime=03:30',Date.parse('2026-09-07T03:30Z'),0,false],
    ['simTime=03:30&timeScale=1',Date.parse('2026-09-07T03:30Z'),1,true],
    ['simTime=03:30&timeScale=60',Date.parse('2026-09-07T03:30Z'),60,true]
  ]) test(`${query} retains anchor/rate after wall step ${step}`, () => {
    const c=realm({query,wall:base}); c.run('simNow()');
    c.clock.mono=1000; c.clock.wall=base+1000+step;
    assert.equal(c.run('simNow()'),anchor+1000*rate);
    assert.equal(c.run('ADVANCING'),advancing);
  });
}
