const assert=require('node:assert/strict');
const fs=require('node:fs');
const {load,sha}=require('./r001d-harness.cjs');
const sourcePath=process.argv[2];
let pass=0,fail=0;
async function test(name,fn){try{await fn();pass++;console.log('PASS '+name);}catch(e){fail++;console.log('FAIL '+name+' :: '+e.message);}}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  await test('actual boot direct producer and first paint own coherent stamp',async()=>{
    const h=load({sourcePath});await h.run('boot()');
    assert.equal(h.run('qaState().moonTruth.moonSkyFresh'),true);
    assert.equal(h.run('_loopStarted'),true);assert.ok(h.rafs.length>0);
  });
  await test('actual runtime applyConfig resets location then consumes new coherent stamp',async()=>{
    const h=load({sourcePath});h.run('render()');
    await h.run('applyConfig({...CONFIG,lat:51.5,lon:-.12,label:"Fixture London",tz:"Asia/Riyadh"},{save:false})');
    const q=h.run('qaState().moonTruth');assert.equal(q.moonSkyFresh,true);
    assert.equal(q.lastConsumed.observation.produced.context,'51.5|-0.12|Asia/Riyadh');
    assert.equal(q.lastConsumed.observation.expected.context,'51.5|-0.12|Asia/Riyadh');
  });
  for(const cached of [true,false])await test('actual rAF '+(cached?'cache':'network')+' day adoption keeps producer stamp',async()=>{
    const h=load({sourcePath});h.run('render();startRenderLoop();');
    if(cached)h.run('saveCache("09-09-2026",__fixturePrayer)');
    h.run('_simBase+=86400000;');h.clock.now=50; // below the independent 76ms cloud raster tick; lunar/day consumers still run
    h.rafs.shift()();await tick();await tick();
    assert.equal(h.run('lastDate'),'09-09-2026');
    h.run('applyTheme(model())');assert.equal(h.run('qaState().moonTruth.moonSkyFresh'),true);
    assert.equal(h.run('qaState().moonTruth.lastConsumed.observation.produced.epochMinute'),29816340);
    assert.equal(h.run('_prayerStale'),false);
  });
  const h=load({sourcePath});console.log(JSON.stringify({sourcePath:h.sourcePath,sourceSha256:h.sourceHash,fixtureSha256:sha(fs.readFileSync(__filename)),pass,fail,limits:'real source lifecycle/loop with contained boundary doubles; no browser'}));
  process.exitCode=fail?1:0;
})();
