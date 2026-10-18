'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {harness,record,req,settle,source}=require('../r0003-harness.cjs');

// The actual boot, admission, model, render and loop run in the existing source
// fixture. Art/layout doubles cannot establish browser timing or visual PASS.
async function acceptedBoot(options={}){
  const h=harness(options),boot=h.boot();
  await h.paintBoot();req(h).ok(record());await boot;
  assert.equal(h.state()._loopStarted,true);
  assert.equal(h.paints.length,1,'the first admitted timetable was rendered by the loader');
  return h;
}

test('startup handoff does not rebuild an already painted unchanged second',async()=>{
  const h=await acceptedBoot();
  const first=h.run('JSON.stringify(_lastRender)');
  await h.frame();
  assert.equal(h.paints.length,1,'the animation loop must not duplicate the loader render');
  assert.equal(h.run('JSON.stringify(_lastRender)'),first);
  await h.advance(1000);await h.frame();
  assert.equal(h.paints.length,2,'the next live second still renders');
});

test('a next-day result between startup and its first frame still paints',async()=>{
  const h=await acceptedBoot({epoch:'2026-09-07T23:30:00Z'});
  assert.equal(h.run('Number.isFinite(_lastRender.leftMin)'),false);
  req(h,'08-09-2026').ok(record('08-09-2026'));await settle();
  await h.frame();
  assert.equal(h.paints.length,2);
  assert.equal(h.run('Number.isFinite(_lastRender.leftMin)'),true);
  assert.equal(h.run('_lastRender.nextDate'),'08-09-2026');
});

test('a frozen startup still consumes later appearance or data invalidation',async()=>{
  const h=await acceptedBoot({hash:'#lat=10&lon=10&tz=UTC&method=2&simTime=12:00'});
  await h.frame();assert.equal(h.paints.length,1);
  h.run('fmt24=false;_renderDirty=true');await h.frame();
  assert.equal(h.paints.length,2);assert.match(h.nodes.get('.nt').textContent,/AM|PM/);
  await h.frame();assert.equal(h.paints.length,2);
});

test('startup without a completed render still paints its first loop frame',async()=>{
  const h=harness();h.seed(record(),record('08-09-2026'));
  h.run('startRenderLoop()');assert.equal(h.paints.length,0);
  await h.frame();assert.equal(h.paints.length,1);
});

test('an earlier painted second cannot suppress a backward clock correction',async()=>{
  const h=await acceptedBoot();h.wallBy(-1000);await h.frame();
  assert.equal(h.paints.length,2);
  assert.equal(h.run('_lastRender.acceptedUtcMs'),Date.parse('2026-09-07T11:59:59Z'));
});

test('an advancing preview displays its clock even before a slow next simulated second',async()=>{
  const h=harness({hash:'#lat=10&lon=10&tz=UTC&method=2&simTime=12:00&timeScale=0.01'});
  const raw=source(),begin=raw.indexOf('function updateSimClock(n){'),end=raw.indexOf('// QA frame-diff',begin);
  assert.ok(begin>=0&&end>begin);h.run(raw.slice(begin,end));
  const boot=h.boot();await h.paintBoot();req(h).ok(record());await boot;await h.frame();
  assert.equal(h.paints.length,1,'showing the readout must not require another full render');
  assert.equal(h.nodes.get('.simclock').style.display,'block');
  assert.equal(h.nodes.get('.simclock').textContent,'SIM 07-09-2026 12:00:00  ×0.01');
});

for(const [name,mutation] of [
  ['another generation','_lastRender.generation--'],
  ['an invalid timestamp','_lastRender.acceptedUtcMs=NaN']
])test(`a completed render from ${name} cannot suppress the first frame`,async()=>{
  const h=harness();h.seed(record(),record('08-09-2026'));
  h.run('render();_renderDirty=false;'+mutation+';startRenderLoop()');
  await h.frame();assert.equal(h.paints.length,2);
});
