'use strict';
// R002F (issue 96): stage-1 discriminator (the baseline facts, measured on the actual runtime with only the renewal
// opportunity removed) and mutation controls R2F-15 a-d, f. Every mutant is an in-memory copy of the authored source;
// nothing is written to disk. A mutant is detected only by an actual assertion failure (setup errors do not count).
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const F=require('./weather-renewal-fixture.cjs'),{B,FRAME}=F,M=3000;
const SOURCE=fs.readFileSync(require('./weather-no-timetable-fixture.cjs').sourcePath,'utf8');
const LOOP='else runRenderStage("weather-renewal",()=>renewWeather());';
function mutate(pairs){ let s=SOURCE; for(const [from,to] of pairs){ assert.equal(s.split(from).length,2,'one declared mutation location: '+from); s=s.replace(from,to); } return s; }
async function boundary(opts){ const s=await F.scene(opts); const frames=await s.run(B+120000); return {s,frames,...F.gap(frames),after:s.requestTimes().filter(t=>t>0)}; }

// ---- stage 1: baseline facts (renewal opportunity removed = the pre-R002F loop) ----
const BASELINE=mutate([[LOOP,'void 0;']]);
test('stage 1 (baseline): no request while selected; withdrawal on the first frame after the step; gap = poll phase',async()=>{
  for(const phaseMs of [1000,10000,25000]){
    const {offAt,onAt,after,s}=await boundary({source:BASELINE,phaseMs});
    assert.equal(offAt,FRAME); assert.equal(onAt,phaseMs,'baseline gap equals the poll phase'); assert.equal(after[0],phaseMs);
    assert.equal(s.requestTimes().filter(t=>t>-120000&&t<=0).length,0,'no request while the record is selected');
  }
});
test('stage 1 (baseline): provider lag 5 s at poll phase 1 s costs one R000D spacing (~61 s)',async()=>{
  const {onAt,after}=await boundary({source:BASELINE,phaseMs:1000,lagMs:5000});
  assert.equal(after[0],1000); assert(after[1]-after[0]>=60000); assert(onAt>60000&&onAt<=61000+30100,'gap '+onAt);
});
test('stage 1 (baseline): wxAt itself still holds the track endpoint (the preview lane now refuses it, see weather-preview-range)',async()=>{
  const s=await F.scene({phaseMs:25000}); const last=s.h.run('weatherTrack.ep[weatherTrack.ep.length-1]');
  assert.equal(s.h.run(`wxAt(${last}+30*86400000).code`),95,'endpoint held 30 days past the end by the interpolator');
});

// ---- mutation controls ----
const healthyGap=async src=>{ const {offAt,onAt,frames}=await boundary({source:src,phaseMs:25000});
  assert.equal(offAt,FRAME,'withdrawn on the first frame after the step'); assert(onAt<=M+2*FRAME,'gap '+onAt);
  for(const f of frames) if(f.sel) assert(!['due','requested'].includes(f.renewal.stage),'renewal never due while selected'); };
const skewGap=async src=>{ const {onAt}=await boundary({source:src,phaseMs:25000,skewMs:1000}); assert(onAt<=M+2*FRAME,'device 1 s ahead: gap '+onAt); };
const structure=async src=>{
  const region=src.slice(src.indexOf('// ---- weather (Open-Meteo:'),src.indexOf('// ---- accurate Moon position'));
  assert.equal((region.match(/setTimeout\(/g)||[]).length,2,'no timer added to the weather owner');
  const calls=src.split('\n').filter(l=>/renewWeather\(/.test(l)&&!/function renewWeather/.test(l));
  assert.equal(calls.length,1); assert.match(calls[0],/^    else runRenderStage\("weather-renewal",\(\)=>renewWeather\(\)\);/);
};
// Early-renewal miss discriminators (owner option D).
const missGap=async src=>{ const s=await F.scene({source:src,phaseMs:20000,lagMs:6000}); const held=s.h.run('weather.retrievedAt');
  const frames=await s.run(B+19000); assert.equal(s.h.run('weather.retrievedAt'),held,'the miss record is not adopted');
  for(const f of frames.filter(f=>f.t>0)){ assert.equal(f.sel,false,'nothing presented after the miss ('+f.t+')'); assert.equal(f.header.state,'unavailable'); }
  await s.run(B+21000); assert.deepEqual(s.requestTimes().filter(t=>t>0),[M,20000],'the ordinary poll proceeds'); assert.equal(s.h.run('!!selectedWeather()'),true); };
const failureSpacing=async src=>{ const s=await F.scene({source:src,phaseMs:20000,fail:h=>h.clock.wall>=B&&h.clock.wall<B+5000}); await s.run(B+50000);
  assert.deepEqual(s.requestTimes().filter(t=>t>0),[M],'a failed renewal keeps R000D spacing: no request at the B + 20 s poll'); };
const oncePerStep=async src=>{ const s=await F.scene({source:src,phaseMs:29000,lagMs:40000}); await s.run(B+28000);
  assert.deepEqual(s.requestTimes().filter(t=>t>0),[M],'one renewal per step'); };
const cases=[
  ['a remove the renewal condition',[[LOOP,'void 0;']],healthyGap],
  ['b renewal due while still selected',[['const dueAt=step+_WX_CURRENT_TTL+_WX_RENEWAL_MARGIN;','const dueAt=step+_WX_CURRENT_TTL-5000;'],
    ['if(now<dueAt||weatherEligibility(record,now).eligible) return out("not-due"','if(now<dueAt) return out("not-due"']],healthyGap],
  ['c margin 0 with the device 1 s ahead',[['_WX_RENEWAL_MARGIN=3000','_WX_RENEWAL_MARGIN=0']],skewGap],
  ['d accept sourceAge <= TTL + m',[['sourceAge>=0&&sourceAge<=_WX_CURRENT_TTL&&receiptAge','sourceAge>=0&&sourceAge<=_WX_CURRENT_TTL+_WX_RENEWAL_MARGIN&&receiptAge']],healthyGap],
  ['g exemption applied to failures',[['const priorSpacing=_wxRetry.weather;','const priorSpacing=_wxRetry.weather; if(renewal) Promise.resolve().then(()=>{ _wxRetry.weather=priorSpacing; });']],failureSpacing],
  ['h exemption more than once per step',[['if(miss){ renewal.outcome="early-renewal-miss"; ','if(miss){ ']],oncePerStep],
  ['i miss treated as acquisition',[['if(current&&!miss&&attemptEligible(op,a)','if(current&&attemptEligible(op,a)']],missGap],
  ['j stale record published after a miss',[['if(miss){ renewal.outcome="early-renewal-miss"; ','if(miss){ current.currentValidAt=ctx.retrievedAt-1000; weather=current; lastWxAt=ctx.retrievedAt; renewal.outcome="early-renewal-miss"; ']],missGap],
  ['k renewal evaluated in preview',[['  if(SIM.wx!=null||ADVANCING||_clockPreview) return out("suppressed-by-mode"','  if(SIM.wx!=null) return out("suppressed-by-mode"']],async src=>{ const s=await F.scene({source:src,phaseMs:25000}); s.h.run('SalahClock.set({rate:0})');
    const frames=await s.run(B+20000); assert(frames.every(f=>f.renewal.stage==='suppressed-by-mode')); }],
  ['l renewal ignores the busy slot',[['const r=weatherRenewal(now); if(!r.due||wxBusy) return false;','const r=weatherRenewal(now); if(!r.due) return false;']],async src=>{
    let release=null; const s=await F.scene({source:src,phaseMs:2900,hold:r=>release===true?new Promise(res=>{release=()=>res(r);}):r});
    await s.run(B+2900-FRAME); release=true; await s.run(B+6000); assert.equal(s.h.run('_wxRenewal'),null); release(); await F.flush(); }],
  ['n6 a failed renewal (no admitted current: unit mismatch) treated as a miss',[[
    'const miss=!!(renewal&&current&&renewal.outcome===null&&wxNumber(current.currentValidAt)!=null&&current.currentIntervalSec>0&&\n      current.currentValidAt<=renewal.step&&',
    'const miss=!!(renewal&&renewal.outcome===null&&(!current||wxNumber(current.currentValidAt)!=null&&current.currentIntervalSec>0&&\n      current.currentValidAt<=renewal.step)&&']],
    async src=>{ const win=h=>h.clock.wall>=B&&h.clock.wall<B+5000;
      for(const mutate of [(h,b)=>win(h)?{...b,current_units:{temperature_2m:'°F'}}:undefined,(h,b)=>win(h)?{...b,current:undefined}:undefined]){
        const s=await F.scene({source:src,phaseMs:17000,mutate}); await s.run(B+50000);
        assert.deepEqual(s.requestTimes().filter(t=>t>0),[M],'a failed renewal keeps R000D spacing'); } }],
  ['f renewal through a timer',[[LOOP,'else setTimeout(()=>renewWeather(),0);']],structure],
  ['f2 renewal timer inside the weather owner',[['function renewWeather(now=Date.now()){','function renewWeather(now=Date.now()){ setTimeout(()=>{},0);']],structure],
];
for(const [name,pairs,discriminator] of cases) test('R2F-15 mutation '+name,async()=>{
  await discriminator(SOURCE);
  const mutant=mutate(pairs);
  await assert.rejects(()=>discriminator(mutant),e=>e instanceof assert.AssertionError,'only an actual assertion failure detects the mutant');
});
