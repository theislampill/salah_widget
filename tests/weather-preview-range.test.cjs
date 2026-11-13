'use strict';
// R002F (issue 96) machine PV — explicit-preview substitution range (owner default D-2F-4 A, fail closed). Rows
// R2F-12, R2F-12a, R2F-12b and mutation R2F-15e, on the ACTUAL authored runtime (tests/weather-renewal-fixture.cjs).
// Inside the admitted hourly track the substitute is wxAt's interpolation, unchanged; before the first or after the
// last point the preview current record is UNAVAILABLE (never a held endpoint). Identity churn of the substitute
// stays with R0034 (#101). No provider is contacted.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const F=require('./weather-renewal-fixture.cjs'),{B,FRAME}=F;
const SOURCE=fs.readFileSync(require('./weather-no-timetable-fixture.cjs').sourcePath,'utf8');
const copy=v=>JSON.parse(JSON.stringify(v));
async function preview(source){
  const s=await F.scene({phaseMs:25000,source}); await s.run(B-60000);
  const ep=copy(s.h.run('weatherTrack.ep')); return {s,first:ep[0],last:ep[ep.length-1],ep};
}
const state=s=>copy(s.h.run(`({sim:simNow(),sel:selectedWeather(),raw:weather,range:typeof wxTrackRange==='function'?wxTrackRange(simNow()):null,
  header:_lastWeatherHeader&&{icon:_lastWeatherHeader.icon,temperature:_lastWeatherHeader.temperature,state:_lastWeatherHeader.conditionState},
  decision:weatherDecision().conditionState,ready:_cloudReady,precip:document.querySelector('.c').dataset.precip,lightning:document.querySelector('.c').dataset.lightning})`));
function assertUnavailable(v,range){
  assert.equal(v.sel,null,'not selected in the preview lane'); assert.equal(v.raw.previewRange,range); assert.equal(v.raw.src,'forecast'); assert.equal(v.raw.code,null);
  assert.equal(v.decision,'unavailable'); assert.equal(v.header.state,'unavailable'); assert.equal(v.header.temperature,null); assert.equal(v.header.icon,'—');
  assert.equal(v.precip,'off'); assert.equal(v.lightning,'off');
}
test('R2F-12 inside the track: the substitute is wxAt\'s interpolation, unchanged and presented',async()=>{
  const {s,first,last}=await preview();
  for(const at of [first,first+1800000,last-1,last]){
    s.h.run(`SalahClock.set({rate:0,utcMs:${at}})`); const v=state(s);
    assert.equal(v.range,'inside'); assert(v.sel,'presented at '+at); assert.equal(v.raw.src,'forecast'); assert.equal(v.raw.previewRange,undefined);
    assert.deepEqual(v.raw,{...copy(s.h.run(`wxAt(${at})`)),src:'forecast'},'bit-identical interpolation at '+at);
    assert.equal(v.header.state,'preview-thunder');
  }
});
test('R2F-12 outside the track: before-first and after-last are unavailable and preview clouds withdraw',async()=>{
  const {s,first,last}=await preview();
  for(const [at,range] of [[last+1,'after-last'],[last+30*86400000,'after-last'],[first-1,'before-first'],[first-86400000,'before-first']]){
    s.h.run(`SalahClock.set({rate:0,utcMs:${first+1}})`); await s.run(s.h.clock.wall+5*FRAME); assert(state(s).ready,'in-track preview deck established');
    s.h.run(`SalahClock.set({rate:0,utcMs:${at}})`); await s.run(s.h.clock.wall+2*FRAME);
    const v=state(s); assertUnavailable(v,range); assert.equal(v.ready,false,'preview deck withdrawn at '+range);
  }
});
test('R2F-12 a running fast-forward that passes the track end becomes unavailable instead of holding the last hour',async()=>{
  const {s,last}=await preview(); s.h.run(`SalahClock.set({rate:2,utcMs:${last}-1000})`);
  const seen=[]; await s.run(s.h.clock.wall+3000,{onFrame:()=>seen.push(state(s))});
  assert(seen.some(v=>v.range==='inside'&&v.sel),'presented while inside: '+JSON.stringify(seen.map(v=>[v.sim-last,v.range,!!v.sel])));
  // The substitute is re-evaluated by render, once per simulated second (or when dirty): the value at the last point
  // stays presented until the next render (< 1 simulated second); from then on every frame is unavailable.
  const out=seen.filter(v=>v.sim>=last+1000); assert(out.length>0); for(const v of out) assertUnavailable(v,'after-last');
});
test('R2F-12a explicit live return from an out-of-track preview reloads the cache and requests in the same call',async()=>{
  for(const outside of [true,false]){
    const {s,first,last}=await preview(); s.h.run(`SalahClock.set({rate:0,utcMs:${outside?last+7200000:first+1}})`);
    assert.equal(state(s).raw.src,'forecast'); s.elapse(61000);   // past the R000D spacing of the scene's own request
    const before=s.requests(); s.h.run('SalahClock.set({live:true})');
    assert.equal(s.requests(),before+1,(outside?'out-of-track':'in-track')+' live return requests in the same call');
    assert.equal(s.h.run('weather&&weather.src'),'current','the cached live record was reloaded (loadWx)');
  }
});
test('R2F-12b frozen out-of-track preview: no frame presents a condition for 2 min while live records are fetched',async()=>{
  const {s,last}=await preview(); s.h.run(`SalahClock.set({rate:0,utcMs:${last+3600000}})`);
  const before=s.requests(); let adopted=0;
  await s.run(s.h.clock.wall+120000,{onFrame:v=>{
    // Painted sinks after every frame: header, deck and effects stay unavailable (no flicker).
    assert.equal(v.header.state,'unavailable',v.t+' header'); assert.equal(v.header.temperature,null); assert.equal(v.ready,false,v.t+' deck');
    assert.equal(v.precip,'off'); assert.equal(v.lightning,'off');
    // A live record fetched by the frozen preview's poll can sit in `weather` until the next frame; that frame's
    // render re-substitutes the unavailable marker before any header/cloud/effects stage reads it.
    if(s.h.run('weather&&weather.src')==='current'){ adopted++; s.L.frame(); assert.equal(s.h.run('weather.previewRange'),'after-last','re-substituted by the next render'); }
    s.h.run('lastWxAt=0'); }});   // keep the fresh-data shortcut off so live records keep arriving
  assert(s.requests()-before>=2,'live records were fetched during the frozen preview ('+(s.requests()-before)+')'); assert(adopted>=1,'a live record was adopted between frames');
});
test('R2F-15e mutation: restoring the endpoint hold in the preview lane is detected',async()=>{
  const from='if(range==="before-first"||range==="after-last"){'; assert.equal(SOURCE.split(from).length,2);
  const discriminator=async src=>{ const {s,last}=await preview(src); s.h.run(`SalahClock.set({rate:0,utcMs:${last+86400000}})`); assertUnavailable(state(s),'after-last'); };
  await discriminator(); await assert.rejects(()=>discriminator(SOURCE.replace(from,'if(false){')),e=>e instanceof assert.AssertionError);
});
