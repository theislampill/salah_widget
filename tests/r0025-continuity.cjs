const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {root,sha}=require('./r001d-harness.cjs'),{cloudFixture}=require('./r0025-context.cjs');
const sourcePath=process.argv[2]||path.join(root,'index.html');let pass=0,fail=0;
function test(name,fn){try{fn();pass++;console.log('PASS '+name);}catch(e){fail++;console.log('FAIL '+name+' :: '+e.message.split('\n')[0]);}}
const fixture=extraHash=>cloudFixture({sourcePath,extraHash});
function established(h){const before=h.paint();assert.ok(before.trace.length>20,'actual puff gradient production');assert.equal(before.columns.length,144);return before;}
test('actual painter no-op and repeated same instant retain commands/columns',()=>{const h=fixture(),a=established(h),b=h.paint();assert.deepEqual(b.trace,a.trace);assert.deepEqual(b.columns,a.columns);});
for(const [name,patch] of [['speed','weather.wind=3.1'],['heading reversal','weather.windDir=45'],['calm','weather.wind=0']])
  test(name+' refresh at the same instant cannot move established cloud commands',()=>{
    const h=fixture(),a=established(h);h.run(patch+';render();');const b=h.paint();
    for(const k of ['covLow','covMid','covHigh','sunX','sunY','sunUp','moonX','moonY','moonLit'])assert.equal(b.state[k],a.state[k],k);
    assert.deepEqual(b.trace,a.trace);assert.deepEqual(b.columns,a.columns);
  });
test('ordinary UTC boundary preserves procedural population coordinates',()=>{
  const h=fixture('&timeScale=1');h.run('_simBase=Date.parse("2026-09-08T23:59:59.962Z");_rafT0=0;TIMESCALE=1');
  const a=established(h),b=h.step(76);
  const identity=s=>s.noise.filter(n=>n[1]===2||n[1]===3||n[1]===5).map(n=>n.slice(0,2));
  assert.deepEqual(identity(b),identity(a));
});
test('actual positive elapsed interval changes puff geometry and lifecycle',()=>{
  const h=fixture('&timeScale=1');h.run('TIMESCALE=1');const a=established(h);let b;
  for(let i=0;i<15;i++)b=h.step(1000);
  assert.notDeepEqual(b.trace,a.trace);assert.notDeepEqual(b.noise,a.noise);
  assert.ok(b.trace.length>20,'cloud field remains nonempty');
});
test('old velocity integrates before a newly received speed is installed',()=>{
  const a=fixture('&timeScale=1'),b=fixture('&timeScale=1');a.run('TIMESCALE=1');b.run('TIMESCALE=1');established(a);established(b);
  a.clock.now=b.clock.now=1000;a.clock.wall+=1000;b.clock.wall+=1000;
  a.run('weather.wind=3.1;render();');b.run('render();');
  assert.deepEqual(a.paint().trace,b.paint().trace);
});
test('empty deck and visible deck share lifecycle during the same elapsed steps',()=>{
  const a=fixture('&timeScale=1'),b=fixture('&timeScale=1');a.run('TIMESCALE=1');b.run('TIMESCALE=1');established(a);established(b);
  a.run('globalThis.__priorCov=[cloudState.covLow,cloudState.covMid,cloudState.covHigh];cloudState.covLow=cloudState.covMid=cloudState.covHigh=0');
  a.step(1000);b.step(1000);a.run('[cloudState.covLow,cloudState.covMid,cloudState.covHigh]=__priorCov');
  assert.deepEqual(a.paint().trace,b.paint().trace);
});
test('accepted signed target change refreshes the cloud population seed',()=>{
  const h=fixture(),a=established(h);h.run('bindConfig({...CONFIG,lat:-24.47});weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:"c",zone:tz,retrievedAt:Date.now()});render();');const b=h.paint();
  assert.notDeepEqual(b.noise.filter(n=>n[1]===2),a.noise.filter(n=>n[1]===2));
});
console.log(JSON.stringify({sourcePath,sourceSha256:sha(fs.readFileSync(sourcePath)),fixtureSha256:sha(fs.readFileSync(__filename)),pass,fail,limits:'actual source painter commands/noise; no pixels/native elapsed/cost'}));process.exitCode=fail?1:0;
