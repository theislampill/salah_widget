'use strict';
// R002F (issue 96) ISM-SKY-004 — precipitation population, cloud-origin gating and the lightning bucket, written as an
// explicit contract and VERIFIED AS IT IS (no behaviour change; gate D-2F-6 not opened). Row R2F-19. The particle
// gate runs the actual tieRainToClouds region; permissions, the renewal withdrawal and the strike bucket run the
// actual authored runtime (tests/weather-renewal-fixture.cjs). Contained doubles only; no provider is contacted.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const F=require('./weather-renewal-fixture.cjs'),{B,FRAME}=F;
const SOURCE=fs.readFileSync(require('./weather-no-timetable-fixture.cjs').sourcePath,'utf8');

function particles(densities,fx='rain'){
  const node=left=>({style:{left,removeProperty(k){delete this[k];}}}), lefts=densities.map((_,i)=>((i+0.5)/densities.length*100)+'%');
  const drops=lefts.map(node), card={dataset:{fx}};
  const ctx=vm.createContext({$:()=>card,_colDens:new Float32Array(densities),document:{querySelectorAll:()=>drops}});
  const a=SOURCE.indexOf('let _rainTiedFx="";'),b=SOURCE.indexOf('// ---- ATMOSPHERE STATE',a); assert(a>0&&b>a);
  vm.runInContext(SOURCE.slice(a,b),ctx); vm.runInContext('tieRainToClouds()',ctx); return drops.map(d=>d.style.display);
}
test('R2F-19 particles are shown only where column density > 0.16 x max (and max >= 2); no profile is ungated',()=>{
  assert.deepEqual(particles([12.5,2,2.01,0]),['','none','','none'],'ratio exactly 0.16 hidden, 0.1608 shown, 0 hidden');
  assert.deepEqual(particles([1.9,0,0.1]),[undefined,undefined,undefined],'max < 2: no real cloud profile, not gated');
  assert.deepEqual(particles([10,0.5],'snow'),['','none'],'snow uses the same columns');
  assert.deepEqual(particles([10,0.5],'clear'),[undefined,undefined],'dry: nothing gated or shown by the tie');
});
test('R2F-19 a renewal withdrawal turns particles and strikes off on the same frame as the deck; none until a current decision',async()=>{
  const s=await F.scene({phaseMs:25000}); const frames=await s.run(B+10000), {onAt}=F.gap(frames);
  for(const f of frames.filter(f=>f.t>0&&f.t<onAt)){ assert.equal(f.ready,false); assert.equal(f.precip,'off',f.t+' particles'); assert.equal(f.lightning,'off',f.t+' strike'); }
  const first=frames.find(f=>f.t===FRAME); assert.equal(first.ready,false); assert.equal(first.precip,'off');
  assert(frames.some(f=>f.t>onAt&&f.precip==='on'),'particles return only with the re-established current decision');
});
test('R2F-19 lightning permission: SIM thunder may strike; live model thunder and forecast-preview thunder never do',async()=>{
  const sim=await F.scene({phaseMs:25000,hash:'&simWx=95&simPrecip=5'}); await sim.run(B-50000);
  assert.equal(sim.h.run('weatherDecision().visualPermissions.lightning'),true); assert.equal(sim.look().lightning,'on','documented recipe &simWx=95&simPrecip=5 keeps thunder');
  const dry=await F.scene({phaseMs:25000,hash:'&simWx=95&simPrecip=0'}); await dry.run(B-50000);
  assert.equal(dry.h.run('weatherDecision().visualPermissions.lightning'),false,'&simWx=95&simPrecip=0 downgrades'); assert.equal(dry.look().lightning,'off');
  const live=await F.scene({phaseMs:25000}); const lf=await live.run(B-50000);
  assert.equal(live.h.run('weatherDecision().lane'),'live'); assert.equal(live.h.run('weatherDecision().visualPermissions.lightning'),false);
  assert(lf.every(f=>f.lightning==='off'),'live model thunder never strikes');
  const fc=await F.scene({phaseMs:25000,hash:'&timeScale=2'}); const ff=await fc.run(B-50000);
  assert.equal(fc.h.run('weather.src'),'forecast'); assert.equal(fc.h.run('weatherDecision().visualPermissions.lightning'),false);
  assert(ff.every(f=>f.lightning==='off'),'forecast thunder in a preview never strikes');
});
test('R2F-19 one strike path per 2.6 s bucket of the scene clock',async()=>{
  const s=await F.scene({phaseMs:25000,hash:'&simWx=95&simPrecip=5'}); await s.run(B-60000);
  const path=s.h.run('document.querySelector(".bolt path")'), set=path.setAttribute.bind(path), writes=[];
  path.setAttribute=(k,v)=>{ if(k==='d') writes.push(v); return set(k,v); };
  const buckets=new Set(); await s.run(B-60000+13000,{onFrame:()=>buckets.add(Math.floor(s.h.run('simNow()')/2600))});
  assert(buckets.size>=5,'the window spans several buckets');
  assert(writes.length>=buckets.size-1&&writes.length<=buckets.size,'one new strike path per bucket ('+writes.length+' for '+buckets.size+' buckets)');
  assert.equal(new Set(writes).size,writes.length,'each bucket draws its own path');
});
