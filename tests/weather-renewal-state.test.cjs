'use strict';
// R002F (issue 96) machine RN — current-weather renewal at the provider-step boundary, driven through the ACTUAL
// authored runtime and its ACTUAL render loop (tests/weather-renewal-fixture.cjs). Rows R2F-02..R2F-09, R2F-11.
// Margin m = 3 000 ms is the owner's ASSUMED parameter (D-2F-7 a); these rows verify behaviour GIVEN m against a
// contained floor-to-15-min provider stub with chosen lag/skew and zero latency. They do not show that m suits the
// live provider (unverified), and nothing contacts a provider. RED: on the R002E source (no renewal) the gap rows
// fail with an actual assertion (run with SALAH_WITHDRAWAL_SOURCE=<that src/native/index.html>).
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const F=require('./weather-renewal-fixture.cjs'),{B,STEP,FRAME}=F,M=3000;
const wxRequestsIn=(s,from,to)=>s.requestTimes().filter(t=>t>from&&t<=to).length;
// Per-frame truth while the record is not selected: nothing weather-driven is presented.
function assertWithdrawn(frames,from,to){
  for(const f of frames.filter(f=>f.t>from&&f.t<to)){
    assert.equal(f.sel,false,'unselected at '+f.t);assert.equal(f.ready,false,'deck withdrawn at '+f.t);assert.equal(f.density,0,'no column density at '+f.t);
    assert.deepEqual(f.cov,[0,0,0],'no coverage at '+f.t);assert.equal(f.precip,'off','no particles at '+f.t);assert.equal(f.lightning,'off','no strike at '+f.t);
    assert.equal(f.header.state,'unavailable','header unavailable at '+f.t);assert.equal(f.header.temperature,null);assert.equal(f.header.icon,'—');
  }
}
async function boundary(opts){ const s=await F.scene(opts); const frames=await s.run(B+120000); return {s,frames,...F.gap(frames)}; }

for(const phaseMs of [1000,10000,25000])test(`R2F-02/03 renewal at the boundary: poll phase ${phaseMs/1000} s, zero lag — gap <= m + 2 frames, one request`,async()=>{
  const {s,frames,offAt,onAt}=await boundary({phaseMs});
  assert.equal(offAt,FRAME,'withdrawn on the first frame after the step ends (R000B order unchanged)');
  assert(onAt!=null&&onAt<=Math.min(phaseMs,M)+2*FRAME,`selected again within m + 2 frames (got ${onAt} ms)`);
  assert.equal(wxRequestsIn(s,0,120000),1,'exactly one request for this boundary');
  assert.equal(wxRequestsIn(s,-120000,0),0,'no request while the record was selected');
  assertWithdrawn(frames,0,onAt);
  const back=frames.find(f=>f.t>=onAt+2*FRAME);   // the header repaints on the next render; the deck re-establishes
  assert(back.sel&&back.ready&&back.density>0&&back.precip==='on'&&back.header.state==='model-estimated-thunder','re-established after renewal');
  assert.equal(back.lightning,'off','live model thunder never strikes (SKY-004)');
  for(const f of frames) if(f.sel) assert(!['due','requested'].includes(f.renewal.stage),'renewal is never due while the record is selected ('+f.t+')');
});
test('R2F-03 freshness unchanged: 900 000 ms selected, 900 001 ms not; a +1 ms future record is ineligible',async()=>{
  const s=await F.scene({phaseMs:25000}); const r=s.h.run('weather');
  assert.equal(s.h.run(`!!selectedWeather(${B})`),true); assert.equal(s.h.run(`!!selectedWeather(${B+1})`),false);
  const now=B-120000;                                            // the scene's receipt instant
  assert.equal(s.h.run(`weatherEligibility({...weather,currentValidAt:${now}+1,retrievedAt:${now}},${now}).eligible`),false,'source 1 ms in the future');
  assert.equal(s.h.run(`weatherEligibility({...weather,retrievedAt:${now}+1},${now}).eligible`),false,'receipt 1 ms in the future');
  assert.equal(r.currentValidAt,B-STEP);
  assert.equal(s.h.run(`weatherRenewal(${B+M-1}).stage`),'not-due'); assert.equal(s.h.run(`weatherRenewal(${B+M}).stage`),'due');
});
test('R2F-04 lag or device-ahead skew below m: one request, gap <= m + 2 frames',async()=>{
  for(const opts of [{lagMs:1000},{skewMs:1000},{lagMs:2000,skewMs:900}]){
    const {s,onAt}=await boundary({phaseMs:25000,...opts});
    assert(onAt<=M+2*FRAME,JSON.stringify(opts)+' gap '+onAt); assert.equal(wxRequestsIn(s,0,120000),1,JSON.stringify(opts));
  }
});
test('R2F-04 lag or device-ahead skew above m: early-renewal miss, then the ordinary poll proceeds (owner option D)',async()=>{
  for(const opts of [{lagMs:5000},{skewMs:5000}]){
    const {s,frames,onAt}=await boundary({phaseMs:25000,...opts}), times=s.requestTimes().filter(t=>t>0);
    assert.deepEqual(times,[M,25000],JSON.stringify(opts)+': renewal at B + m (miss), then the ordinary poll at B + phase');
    assert.equal(onAt,25000,JSON.stringify(opts)+': gap equals the poll phase, as on main (no 60 s penalty)');
    const after=frames.find(f=>f.t===M+FRAME);
    assert.equal(after.renewal.stage,'early-renewal-miss'); assert.match(after.renewal.lastOutcome,/^early-renewal-miss/);
    assert.equal(after.renewal.clockAgreement,'agreeing','the miss record was not adopted: the held (agreeing) record remains');
    assertWithdrawn(frames,0,onAt);
  }
});
test('R2F-05 provider step contract guard: interval 3600 or an off-grid current.time falls back to the baseline poll',async()=>{
  const {s,onAt}=await boundary({phaseMs:10000,interval:3600});
  assert.equal(onAt,10000,'baseline poll phase, not renewal'); assert.equal(s.requestTimes().filter(t=>t>0)[0],10000);
  const off=await F.scene({phaseMs:25000,offsetMs:-7*60000});    // current.time 7 min before the 15-min grid
  const r=off.h.run('retryDiagnostics().renewal'); assert.equal(r.stage,'contract-fallback'); assert.match(r.reason,/step contract not met/);
  const frames=await off.run(B-7*60000+60000);                  // its own expiry (B - 7 min) plus a minute
  assert(frames.every(f=>f.renewal.stage==='contract-fallback'||f.renewal.stage==='not-due'),'never due');
  assert.equal(off.h.run('_wxRenewal'),null,'no renewal request was ever issued');
});
test('R2F-06 hidden card: no renewal request while hidden; one request on resume, not one per missed boundary',async()=>{
  const s=await F.scene({phaseMs:25000}); await s.run(B-60000);
  const before=s.requests(); s.L.visibility('hidden'); await s.run(B+3*STEP+60000,{hidden:true});
  assert.equal(s.requests(),before,'nothing requested while hidden across three boundaries');
  s.L.visibility('visible'); const frames=await s.run(B+3*STEP+60000+120000);
  assert.equal(s.requests()-before,1,'exactly one request after resume'); assert(frames.find(f=>f.sel),'resumed record selected');
});
test('R2F-06 reduced motion: same renewal timing',async()=>{
  const {onAt,s}=await boundary({phaseMs:25000,reduced:true});
  assert(onAt<=M+2*FRAME,'gap '+onAt); assert.equal(wxRequestsIn(s,0,120000),1);
});
for(const [name,hash,setup] of [['SIM weather','&simWx=3&simCloud=95',null],['fast-forward preview','&timeScale=60',null],['frozen clock preview','','SalahClock.set({rate:0})']])
  test('R2F-07 '+name+': renewal suppressed, zero renewal requests',async()=>{
    const s=await F.scene({phaseMs:25000,hash}); if(setup) s.h.run(setup);
    const frames=await s.run(B+20000);
    assert(frames.every(f=>f.renewal.stage==='suppressed-by-mode'),'suppressed on every frame');
    assert.equal(s.h.run('_wxRenewal'),null,'no renewal request'); assert.equal(wxRequestsIn(s,0,20000),0,'no request in the renewal window');
  });
test('R2F-08 location change while a renewal is in flight: late body rejected; the new generation starts without a due renewal',async()=>{
  let release=null;
  const s=await F.scene({phaseMs:25000,hold:r=>release?new Promise(res=>{release=()=>res(r);}):r});
  await s.run(B+M-FRAME); release=true; const frames=await s.run(B+M+FRAME);
  assert.equal(typeof release,'function','the renewal request is pending'); assert.equal(frames.at(-1).renewal.stage,'requested');
  const old=s.h.run('weather'); s.h.run('beginRuntimeGeneration();lat=21.42;lon=39.83;resetForNewLocation()');
  release(); await F.flush(); await F.flush();
  assert.equal(s.h.run('weather'),null,'late body of the superseded generation not adopted'); assert.notEqual(s.h.run('weather'),old);
  assert.equal(s.h.run('retryDiagnostics().renewal.stage'),'no-record','the new generation has no record to renew');
  assert.equal(s.h.run('_wxRenewal&&_wxRenewal.generation===currentWeatherTarget().generation'),false,'the old renewal does not belong to the new generation');
});
test('R2F-09 continuity of identity: cloud field seed, population and scene identity equal before and after the blink',async()=>{
  const {frames,onAt}=await boundary({phaseMs:25000}), before=frames.find(f=>f.t===-FRAME), after=frames.find(f=>f.t>=onAt+2*FRAME);
  assert(before.ready&&after.ready); assert.equal(after.seed,before.seed,'field seed'); assert.equal(after.population,before.population,'population key');
});
test('R2F-11 (D-2F-3 option A) clock disagreement is diagnosed by sign; renewal adds no request; spacing stays R000D',async()=>{
  const cases=[[-20*60000,'disagreeing-future'],[20*60000,'disagreeing-expired-at-receipt'],[3000,'agreeing']];
  for(const [skewMs,want] of cases){
    const s=await F.scene({phaseMs:25000,skewMs,fetchAt:-50*60000,frame:1000});
    assert.equal(s.h.run('retryDiagnostics().renewal.clockAgreement'),want,'skew '+skewMs);
    await s.run(B+9*60000); const times=s.requestTimes();
    for(let i=1;i<times.length;i++) assert(times[i]-times[i-1]>=60000,'skew '+skewMs+': R000D spacing');
    if(want!=='agreeing'){ assert.equal(s.h.run('_wxRenewal'),null,'no renewal request under disagreement (baseline poll only)');
      assert(times.length>=55&&times.length<=60,'skew '+skewMs+': about one request per 60 s (baseline rate), got '+times.length); }
    else assert(times.length<=6,'agreeing: one request per step plus the initial ('+times.length+')');
  }
});
test('R2F-15f no new timer: the renewal is evaluated by the existing loop line only',()=>{
  const src=fs.readFileSync(require('./weather-no-timetable-fixture.cjs').sourcePath,'utf8');
  const region=src.slice(src.indexOf('// ---- weather (Open-Meteo:'),src.indexOf('// ---- accurate Moon position'));
  assert.equal((region.match(/setTimeout\(/g)||[]).length,2,'only the two existing attempt deadlines'); assert(!/setInterval|requestAnimationFrame/.test(region));
  const calls=src.split('\n').filter(l=>/renewWeather\(/.test(l)&&!/function renewWeather/.test(l));
  assert.equal(calls.length,1,'one caller'); assert.match(calls[0],/^    else runRenderStage\("weather-renewal",\(\)=>renewWeather\(\)\);/,'the else branch of the existing loop poll');
  assert.equal(src.split('if(!ADVANCING && rt-_lastWx>30000){ _lastWx=rt; fetchWeather(); fetchRadar(); }').length,2,'the existing poll line is unchanged');
});
test('diagnostics: the renewal readout names m, its assumed basis and the stage, as a pure read',async()=>{
  const s=await F.scene({phaseMs:25000}); const before=s.requests(), w=s.h.run('weather');
  const r=s.h.run('retryDiagnostics().renewal');
  assert.equal(r.marginMs,M); assert.match(r.marginBasis,/assumed/); assert.match(r.marginBasis,/unverified/);
  assert.equal(r.stage,'not-due'); assert.equal(r.dueAt,B+M); assert.equal(r.clockAgreement,'agreeing');
  for(let i=0;i<5;i++) s.h.run('qaState()'); assert.equal(s.requests(),before); assert.equal(s.h.run('weather'),w,'no adoption by a read');
});
