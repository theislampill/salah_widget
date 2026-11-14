'use strict';
// R002F (issue 96) — the EARLY-RENEWAL MISS (owner decision: option D with a 3 s margin; narrow amendment of R000D's
// retry-spacing rule authorised on issues 96 and 13). A renewal answered with the same provider step is neither an
// acquisition nor a failure: it is not adopted and the 60 s spacing it opened is restored, so the next ORDINARY poll
// proceeds. Everything else keeps R000D spacing. Actual authored runtime and actual loop
// (tests/weather-renewal-fixture.cjs); contained provider stubs only.
const test=require('node:test'),assert=require('node:assert/strict');
const F=require('./weather-renewal-fixture.cjs'),{B,STEP,FRAME}=F,M=3000;
const after=(s,t)=>s.requestTimes().filter(x=>x>t);
async function boundary(opts){ const s=await F.scene(opts); const frames=await s.run(opts.until||B+120000); return {s,frames,...F.gap(frames)}; }

test('miss -> the next ordinary poll proceeds and succeeds; the miss record is never presented',async()=>{
  const {s,frames,onAt}=await boundary({phaseMs:20000,lagMs:6000});
  assert.deepEqual(after(s,0),[M,20000]); assert.equal(onAt,20000);
  for(const f of frames.filter(f=>f.t>0&&f.t<onAt)){ assert.equal(f.sel,false); assert.equal(f.header.state,'unavailable'); assert.equal(f.ready,false); }
  assert.equal(frames.find(f=>f.t===M+FRAME).step,B-STEP,'the held record is unchanged by the miss (not adopted)');
  const back=frames.find(f=>f.t===onAt); assert.equal(back.step,B,'the ordinary poll adopted the next step');
  assert.equal(back.renewal.stage,'not-due');
});
test('provider that never advances: miss, then old steps at R000D spacing — bounded over two simulated hours',async()=>{
  const s=await F.scene({phaseMs:20000,maxStep:B-STEP,frame:1000}); await s.run(B+2*3600000);
  const t=after(s,0); assert.equal(t[0],M,'one renewal (miss)'); assert.equal(t[1],20000,'the ordinary poll right after the miss');
  for(let i=2;i<t.length;i++) assert(t[i]-t[i-1]>=60000,'R000D 60 s spacing between ordinary attempts');
  assert(t.length<=2+120,'no storm: '+t.length+' requests in 2 h'); assert.equal(s.h.run('retryDiagnostics().renewal.stage'),'disagreement-fallback');
  assert.equal(s.h.run('!!selectedWeather()'),false,'never presented');
});
test('genuine failure at renewal keeps the 60 s spacing (HTTP 503 at B + m)',async()=>{
  const failWindow=h=>h.clock.wall>=B&&h.clock.wall<B+5000;
  const {s,onAt}=await boundary({phaseMs:20000,fail:failWindow}); const t=after(s,0);
  assert.equal(t[0],M); assert(t[1]-t[0]>=60000,'the poll at B + 20 s is held by R000D spacing: '+t[1]); assert(onAt>=60000);
  assert.equal(s.h.run('retryDiagnostics().renewal.stage'),'not-due');
});
test('only one exemption per provider step: after a miss the stage stays early-renewal-miss and renews nothing more',async()=>{
  const s=await F.scene({phaseMs:29000,lagMs:40000}); const frames=await s.run(B+28000);
  assert.deepEqual(after(s,0),[M],'exactly one renewal request before the ordinary poll');
  assert(frames.filter(f=>f.t>M).every(f=>f.renewal.stage==='early-renewal-miss'));
  const more=await s.run(B+120000); const t=after(s,0);
  assert.equal(t[1],29000); for(let i=2;i<t.length;i++) assert(t[i]-t[i-1]>=60000); assert(more.length>0);
});
test('hidden card: a step that ends while hidden makes no renewal request; resume uses the ordinary poll',async()=>{
  const s=await F.scene({phaseMs:20000,lagMs:6000}); await s.run(B-1000); const before=s.requests();
  s.L.visibility('hidden'); await s.run(B+10000,{hidden:true}); assert.equal(s.requests(),before);
  s.L.visibility('visible'); await s.run(B+70000); assert(s.requests()-before<=2,'resume: ordinary poll (and at most the renewal opportunity)');
});
test('generation/target change between a miss and the poll: no exemption carries over',async()=>{
  const s=await F.scene({phaseMs:20000,lagMs:6000}); await s.run(B+M+5*FRAME);
  assert.equal(s.h.run('_wxRenewal.outcome'),'early-renewal-miss');
  s.h.run('beginRuntimeGeneration();lat=21.42;lon=39.83;resetForNewLocation()');
  assert.equal(s.h.run('retryDiagnostics().renewal.stage'),'no-record');
  assert.equal(s.h.run('_wxRenewal.generation===currentWeatherTarget().generation'),false);
  await s.run(B+60000); assert(s.h.run('!!weather&&weather.target.lat')===21.42,'the new target acquires through the ordinary path');
});
test('no duplicated in-flight acquisition: a pending renewal blocks the ordinary poll and further renewals',async()=>{
  let release=null; const s=await F.scene({phaseMs:5000,hold:r=>release===true?new Promise(res=>{release=()=>res(r);}):r});
  await s.run(B+M-FRAME); release=true; await s.run(B+9000);       // inside the 10 s attempt deadline
  assert.deepEqual(after(s,0),[M],'one request while the renewal is pending (the poll at B + 5 s found it busy)');
  release(); await F.flush(); await s.run(B+9500); assert.equal(s.h.run('!!selectedWeather()'),true,'the pending renewal then adopts the next step');
});
test('an ordinary poll in flight when the renewal becomes due: no second request and no renewal attributed',async()=>{
  let release=null; const s=await F.scene({phaseMs:2900,hold:r=>release===true?new Promise(res=>{release=()=>res(r);}):r});
  await s.run(B+2900-FRAME); release=true; await s.run(B+6000);
  assert.deepEqual(after(s,0),[2900],'only the ordinary poll'); assert.equal(s.h.run('_wxRenewal'),null,'the in-flight poll is not counted as a renewal');
  assert.equal(s.h.run('retryDiagnostics().renewal.stage'),'due','renewal stays due while another attempt owns the slot');
  release(); await F.flush(); await s.run(B+6500); assert.equal(s.h.run('!!selectedWeather()'),true);
});
