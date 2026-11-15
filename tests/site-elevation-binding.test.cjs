'use strict';
// R0032 (issue 99) machine EL — legacy site elevation bound to its location (ISM-WX-008, PRA-F-17a).
// Complete authored runtime (tests/r0032-fixture.cjs). The legacy native atmosphere reads the elevation through
// one bound reader; the CP9 elevation lease (real-sky/native-host-hooks.js) is untouched and has its own test.
// Readers observed: the &debugLayers=1 read-out ("elev Nm") and the atmosphere's star/haze outputs.
const assert=require('node:assert/strict'),{test}=require('node:test');
const {runtime,weatherBody}=require('./r0032-fixture.cjs');
const HASH='#lat=24.47&lon=39.61&label=Madinah&tz=Asia%2FRiyadh&units=c&method=4&debugLayers=1';
const cfg=(lat,lon,extra={})=>({lat,lon,tz:'Asia/Riyadh',label:'L'+lat,method:'4',school:'0',time:'24',units:'c',datefmt:'YYYY-MM-DD',source:'manual',...extra});
// Per-coordinate weather route: elevation by latitude, or an HTTP 503 for a failing location.
function route(table){return (u,h)=>{if(u.hostname!=='api.open-meteo.com')return undefined;const e=table[u.searchParams.get('latitude')];
  if(e==='fail')return {ok:false,status:503,json:async()=>({error:true})};return {ok:true,status:200,json:async()=>weatherBody(h.clock.wall,{elevation:e})};};}
async function drive(r,code){let done=false;const p=r.run(code);Promise.resolve(p).then(()=>{done=true;},()=>{done=true;});
  for(let i=0;i<200&&!done;i++){await r.flush(2);if(!r.advanceTask()&&!r.advanceFrame())r.advanceTimer();}assert.ok(done,code+' settled');return p;}
// From here on every weather answer fails; prayer and other routes are unchanged.
function failWeather(r){const f=r.ctx.fetch;r.ctx.fetch=async u=>new URL(String(u)).hostname==='api.open-meteo.com'?{ok:false,status:503,json:async()=>({error:true})}:f(u);}
async function apply(r,c){r.ctx.__cfg=c;await drive(r,'applyConfig(__cfg)');await r.flush();}
const readout=r=>{r.run('render()');const m=/elev (-?\d+)m/.exec(r.select('.dbglayers').textContent||'');assert.ok(m,'debug read-out painted');return +m[1];};
// Admit a fresh weather answer for the current target after the 60 s spacing (the loop's ordinary opportunity).
async function refetch(r){r.clock.now+=61000;r.clock.wall+=61000;await drive(r,'fetchWeather()');}

test('R32-06 control: the elevation admitted at A is read at A',async()=>{
  const r=runtime({hash:HASH,route:route({'24.47':2500})});await r.boot();assert.equal(readout(r),2500);
});
test('R32-06 A → B with B weather failing: readers see the documented default 0 m at B, never A\'s value',async()=>{
  const r=runtime({hash:HASH,route:route({'24.47':2500,'21.42':'fail'})});await r.boot();assert.equal(readout(r),2500);
  await apply(r,cfg(21.42,39.83));assert.equal(r.run('lat'),21.42);assert.equal(readout(r),0);
  assert.equal(r.run('weather'),null,'B has no admitted weather');
});
test('R32-06 B admitted → B\'s value',async()=>{
  const r=runtime({hash:HASH,route:route({'24.47':2500,'21.42':40})});await r.boot();
  await apply(r,cfg(21.42,39.83));assert.equal(readout(r),40);
});
test('R32-06 P2: a units change at unchanged coordinates keeps A\'s value (no reset on a broad change)',async()=>{
  // Admit A once with a known value, then fail every later answer so only the binding decides the reader.
  const ok=runtime({hash:HASH,route:route({'24.47':2500})});await ok.boot();assert.equal(readout(ok),2500);
  failWeather(ok);
  await apply(ok,cfg(24.47,39.61,{units:'f'}));assert.equal(ok.run('units'),'f');assert.equal(readout(ok),2500);
});
test('R32-06 binding rule A → B (failing) → A: A\'s own admitted value is read again at A',async()=>{
  const r=runtime({hash:HASH,route:route({'24.47':2500,'21.42':'fail'})});await r.boot();
  failWeather(r);
  await apply(r,cfg(21.42,39.83));assert.equal(readout(r),0);
  await apply(r,cfg(24.47,39.61));assert.equal(readout(r),2500);
});
test('R32-06 binding rule A → B (admitted) → A (failing): 0 m until A is admitted again',async()=>{
  const r=runtime({hash:HASH,route:route({'24.47':2500,'21.42':40})});await r.boot();
  await apply(r,cfg(21.42,39.83));assert.equal(readout(r),40);
  failWeather(r);
  await apply(r,cfg(24.47,39.61));assert.equal(readout(r),0);
});
test('R32-06 atmosphere: A → B with B served from its cache and B\'s refresh failing equals a cold B load',async()=>{
  // B's cached weather is admitted from storage (haze present), its refresh fails: only the elevation can differ.
  const bKey='salahwx:21.42|39.83|c';
  const tableA={'24.47':2500,'21.42':'fail'},HASHB='#lat=21.42&lon=39.83&label=L21.42&tz=Asia%2FRiyadh&units=c&method=4&debugLayers=1';
  const warm=runtime({hash:HASH,route:route(tableA)});await warm.boot();
  // Store B's admitted record exactly as the authored writer would (receipt = now) before switching.
  warm.ctx.__b=weatherBody(warm.clock.wall,{elevation:40}).current;
  warm.run("localStorage.setItem('"+bKey+"',JSON.stringify({w:admitWeatherRecord(__b,{lat:21.42,lon:39.83,units:'c',zone:'Asia/Riyadh',retrievedAt:Date.now()}),ts:Date.now()}))");
  const bytes=warm.storage.get(bKey);assert.ok(bytes);
  await apply(warm,cfg(21.42,39.83));assert.ok(warm.run('weather&&weather.temp')!=null,'B weather admitted from cache');
  const cold=runtime({hash:HASHB,route:route(tableA),storage:[[bKey,bytes]]});
  cold.clock.wall=warm.clock.wall;cold.clock.now=warm.clock.now;await cold.boot();
  // Same instant on both runtimes for the comparison.
  for(const r of [warm,cold]){r.clock.wall=Math.max(warm.clock.wall,cold.clock.wall);r.clock.now=Math.max(warm.clock.now,cold.clock.now);}
  const pick=r=>JSON.parse(r.run('(()=>{const A=atmosphere(model());return JSON.stringify({stars:A.starOpacity,haze:A.aerosolDensity,blur:A.starBlur??null});})()'));
  assert.equal(readout(warm),readout(cold));assert.deepEqual(pick(warm),pick(cold));
});
test('R32-06 the binding uses both coordinates: a longitude-only move with failing weather reads 0 m',async()=>{
  const r=runtime({hash:HASH,route:route({'24.47':2500})});await r.boot();assert.equal(readout(r),2500);
  failWeather(r);await apply(r,cfg(24.47,40.5));assert.equal(r.run('lon'),40.5);assert.equal(readout(r),0);
});
test('R32-06 the binding uses both coordinates: a latitude-only move with failing weather reads 0 m',async()=>{
  const r=runtime({hash:HASH,route:route({'24.47':2500})});await r.boot();
  failWeather(r);await apply(r,cfg(25.5,39.61));assert.equal(readout(r),0);
});
