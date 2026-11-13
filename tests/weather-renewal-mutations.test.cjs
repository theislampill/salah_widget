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
const cases=[
  ['a remove the renewal condition',[[LOOP,'void 0;']],healthyGap],
  ['b renewal due while still selected',[['const dueAt=step+_WX_CURRENT_TTL+_WX_RENEWAL_MARGIN;','const dueAt=step+_WX_CURRENT_TTL-5000;'],
    ['if(now<dueAt||weatherEligibility(record,now).eligible) return out("not-due"','if(now<dueAt) return out("not-due"']],healthyGap],
  ['c margin 0 with the device 1 s ahead',[['_WX_RENEWAL_MARGIN=3000','_WX_RENEWAL_MARGIN=0']],skewGap],
  ['d accept sourceAge <= TTL + m',[['sourceAge>=0&&sourceAge<=_WX_CURRENT_TTL&&receiptAge','sourceAge>=0&&sourceAge<=_WX_CURRENT_TTL+_WX_RENEWAL_MARGIN&&receiptAge']],healthyGap],
  ['f renewal through a timer',[[LOOP,'else setTimeout(()=>renewWeather(),0);']],structure],
  ['f2 renewal timer inside the weather owner',[['function renewWeather(now=Date.now()){','function renewWeather(now=Date.now()){ setTimeout(()=>{},0);']],structure],
];
for(const [name,pairs,discriminator] of cases) test('R2F-15 mutation '+name,async()=>{
  await discriminator(SOURCE);
  const mutant=mutate(pairs);
  await assert.rejects(()=>discriminator(mutant),e=>e instanceof assert.AssertionError,'only an actual assertion failure detects the mutant');
});
