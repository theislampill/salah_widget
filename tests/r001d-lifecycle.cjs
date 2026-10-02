const assert=require('node:assert/strict');
const fs=require('node:fs');
const {load,sha}=require('./r001d-harness.cjs');
const sourcePath=process.argv.slice(2).find(arg=>!arg.startsWith('--'));
const stallFirst=process.argv.includes('--stall-first'),retryFirst=process.argv.includes('--retry-first');
const declared=11;let pass=0,fail=0,terminal=false;
process.on('beforeExit',()=>{if(!terminal){console.error('INCOMPLETE: lifecycle terminal missing; declared='+declared+' executed='+(pass+fail));process.exitCode=1;}});
async function test(name,fn){try{await fn();pass++;console.log('PASS '+name);}catch(e){fail++;console.log('FAIL '+name+' :: '+e.message);}}
if(process.argv.includes('--missing-terminal-control'))return;
(async()=>{
  await test('actual boot direct producer and first paint own coherent stamp',async()=>{
    const h=load({sourcePath,prayerMode:stallFirst?'stall':'healthy',prayerFailures:retryFirst?1:0});
    h.run('today=null;tomorrow=null;');await h.complete(h.run('boot()'));
    assert.ok(h.requests.some(r=>r.dateStr==='08-09-2026'));
    assert.equal(h.run('today.date.gregorian.date'),'08-09-2026');
    if(retryFirst){assert.ok(h.requests.length>=2);assert.equal(h.timerEvents[0].at,900);}
    assert.equal(h.run('qaState().moonTruth.moonSkyFresh'),true);
    assert.equal(h.run('_loopStarted'),true);assert.ok(h.rafs.length>0);
  });
  await test('actual runtime applyConfig resets location then consumes new coherent stamp',async()=>{
    const h=load({sourcePath});h.run('render()');
    await h.complete(h.run('applyConfig({...CONFIG,lat:51.5,lon:-.12,label:"Fixture London",tz:"Asia/Riyadh"},{save:false})'));
    const q=h.run('qaState().moonTruth');assert.equal(q.moonSkyFresh,true);
    assert.equal(q.lastConsumed.observation.produced.context,'51.5|-0.12|Asia/Riyadh');
    assert.equal(q.lastConsumed.observation.expected.context,'51.5|-0.12|Asia/Riyadh');
  });
  for(const cached of [true,false])await test('actual rAF '+(cached?'cache':'network')+' day adoption keeps producer stamp',async()=>{
    const h=load({sourcePath});h.run('render();startRenderLoop();');
    if(cached){h.run('(()=>{const d=JSON.parse(JSON.stringify(__fixtureNextPrayer));d.timings.Fajr="04:51";saveCache("09-09-2026",d);})()');assert.equal(h.run('loadCache("09-09-2026").timings.Fajr'),'04:51');}
    // Remove the prefetched seed in both rows: otherwise promotion bypasses the
    // cache/network boundary. The distinct cached Fajr proves which record wins.
    h.run('tomorrow=null;');assert.equal(h.run('tomorrow'),null);
    h.run('_simBase+=86400000;');h.clock.now=50; // below the independent 76ms cloud raster tick; lunar/day consumers still run
    h.rafs.shift()();await h.drain();
    assert.equal(h.run('lastDate'),'09-09-2026');
    assert.equal(h.run('today.date.gregorian.date'),'09-09-2026');
    if(cached){assert.equal(h.run('today.timings.Fajr'),'04:51');assert.equal(h.requests.some(r=>r.dateStr==='09-09-2026'),false);}
    else assert.ok(h.requests.some(r=>r.dateStr==='09-09-2026'));
    h.run('applyTheme(model())');assert.equal(h.run('qaState().moonTruth.moonSkyFresh'),true);
    assert.equal(h.run('qaState().moonTruth.lastConsumed.observation.produced.epochMinute'),29816340);
    assert.equal(h.run('_prayerStale'),false);
  });
  for(const [label,reason] of [['null',null],['undefined',undefined],['false',false],['zero',0],['empty string',''],['Error',new Error('fixture-error-positive')]])
    await test('completion preserves actual applyConfig rejection: '+label,async()=>{
      const h=load({sourcePath});h.ctx.__fixtureRejection=reason;
      const operation=h.run('applyConfig(Object.defineProperty({...CONFIG},"lat",{enumerable:true,get(){throw __fixtureRejection;}}),{save:false})');
      let rejected=false,caught;
      try{await h.complete(operation);}catch(e){rejected=true;caught=e;}
      assert.equal(rejected,true,'rejection cannot become fulfillment');assert.equal(caught,reason,'exact rejection reason');
    });
  await test('completion preserves normal actual applyConfig undefined resolution',async()=>{
    const h=load({sourcePath});
    const result=await h.complete(h.run('applyConfig({...CONFIG,lat:51.5,lon:-.12,label:"Fixture London",tz:"Asia/Riyadh"},{save:false})'));
    assert.equal(result,undefined);assert.equal(h.run('qaState().moonTruth.moonSkyFresh'),true);
  });
  const h=load({sourcePath});terminal=true;
  const executed=pass+fail,missing=declared-executed;
  console.log(JSON.stringify({terminal:true,declared,executed,missing,sourcePath:h.sourcePath,sourceSha256:h.sourceHash,fixtureSha256:sha(fs.readFileSync(__filename)),pass,fail,stallFirst,retryFirst,limits:'real source lifecycle/loop with contained boundary doubles; no browser'}));
  process.exitCode=fail||missing?1:0;
})().catch(e=>{console.error('INCOMPLETE: '+e.stack);process.exitCode=1;});
