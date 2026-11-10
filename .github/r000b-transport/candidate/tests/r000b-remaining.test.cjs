'use strict';
// R000B residual controls reuse the delivered R000C source-executing fixture.
// Only network/Image/canvas/storage/clocks/DOM are contained; product declarations
// supply acquisition, conversion, admission, selection, header and cloud paint.
const assert=require('node:assert/strict'),{test}=require('node:test');
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),vm=require('node:vm');
const fixturePath=path.join(__dirname,'r000c-weather.test.cjs'),text=fs.readFileSync(fixturePath,'utf8');
const end=text.indexOf("test('control: actual fresh acquisition");assert(end>0);
const mod=new Module(fixturePath,module);mod.filename=fixturePath;mod.paths=Module._nodeModulePaths(__dirname);
mod._compile(text.slice(0,end)+'\nmodule.exports={fixture,healthy,NOW};',fixturePath);
const {fixture,healthy,NOW}=mod.exports;
const evidence=[];
function record(id,f){
  const v=f.view(),s=f.read();
  evidence.push({id,wall:f.clock.now,requests:f.calls.slice(),imageRequests:f.images.slice(),
    admitted:s,diagnostics:v.qa.wxTruth,temperature:f.nodes.get('#wt').textContent,
    icon:f.nodes.get('#wi').textContent,atmosphere:v.a});
  return v;
}
process.on('exit',()=>{if(process.env.R000B_OBSERVATIONS)fs.writeFileSync(process.env.R000B_OBSERVATIONS,
  JSON.stringify(evidence,(_k,v)=>typeof v==='number'&&!Number.isFinite(v)?{$vmNonFinite:String(v)}:v,2)+'\n');});
function manifest(){return {generated:NOW/1000,host:'https://tilecache.rainviewer.com',
  radar:{past:[{time:NOW/1000,path:'/v2/radar/test'}]}};}
function cloudView(f){
  const v=f.view();f.cloudTrace.length=0;
  return {...v,...JSON.parse(vm.runInContext(`paintClouds(simNow()/1000);JSON.stringify({
    selected:!!selectedWeather(),coverage:[cloudState.covLow,cloudState.covMid,cloudState.covHigh],
    targets:[cloudState.tgtLow,cloudState.tgtMid,cloudState.tgtHigh],population:_cloudMotion.population,
    ready:_cloudReady,density:_colDens?Math.max(..._colDens):null})`,f.context)),
    fills:f.cloudTrace.filter(x=>x[0]==='fill').length};
}
function unavailable(f,v=f.view()){
  assert.equal(v.qa.cache.currentEligible,false,'source-invalid weather must remain ineligible');
  assert.equal(f.nodes.get('#wt').textContent,'','unavailable current temperature must be blank');
  assert.equal(f.nodes.get('#wi').textContent,'—','unavailable condition must be an em dash');
  assert.equal(v.a.wxTemp,null);assert.equal(v.a.rainOp,0);
  assert.equal(v.qa.wxTruth.activeThunder,false);
  const c=cloudView(f);assert.deepEqual(c.coverage,[0,0,0]);assert.deepEqual(c.targets,[0,0,0]);assert.equal(c.fills,0);
}

// Removing a raw or derived-epoch admission guard must cause a genuine Image/
// installed-state assertion failure, independently of later authority rejection.
for(const field of ['frame','index'])for(const kind of ['missing','null','numeric-string','negative','json-overflow','max-value','date-overflow','vm-NaN','vm-Infinity']){
  test('B04 '+field+' '+kind+' rejected before Image and admission',async()=>{
    const input=manifest(),owner=field==='frame'?input.radar.past[0]:input,key=field==='frame'?'time':'generated';
    if(kind==='missing')delete owner[key];
    else owner[key]=({'null':null,'numeric-string':'1788814800',negative:-1,'json-overflow':'WIRE_OVERFLOW',
      'max-value':Number.MAX_VALUE,'date-overflow':8640000000001,'vm-NaN':NaN,'vm-Infinity':Infinity})[kind];
    const wire=JSON.stringify(input).replace('"WIRE_OVERFLOW"','1e309');
    const value=kind.startsWith('vm-')?input:JSON.parse(wire);
    const f=fixture({manifest:value});await f.fetchRadar();const v=record('B04/'+field+'/'+kind,f);
    assert.equal(f.images.length,0,'B04 invalid '+field+' epoch must not dispatch Image');
    assert.equal(f.read().weatherRadar,null,'B04 invalid '+field+' metadata must not be installed');
    assert.equal(v.qa.wxTruth.radarAvailable,false);assert.equal(f.radarPrecipNow(),0);
    assert.equal(v.qa.cache.currentEligible,false);assert.equal(v.qa.wxTruth.activeThunder,false);
  });
}
test('positive radar finite clocks remain separate and actual Image is sampled',async()=>{
  const input=manifest();input.radar.past[0].time-=60;input.generated-=30;
  const f=fixture({manifest:input});await f.fetchRadar();const v=record('positive/radar',f),r=f.read().weatherRadar;
  assert.equal(f.images.length,1);assert.equal(r.sample.sampledCount,49);assert.equal(r.sample.returnCount,49);
  assert.equal(r.frameGeneratedAt,NOW-60000);assert.equal(r.indexGeneratedAt,NOW-30000);assert.equal(r.retrievedAt,NOW);
  assert.equal(v.qa.wxTruth.radarAvailable,true);assert.equal(f.radarPrecipNow(),0);assert.equal(v.qa.wxTruth.activeThunder,false);
});

test('B13 M1 four-hour current cannot gain authority from new retrieval',async()=>{
  const f=fixture({payload:healthy({time:'2026-09-07T17:00'})});await f.fetchWeather();
  const v=record('B13/old-current',f);unavailable(f,v);
  assert.equal(f.read().weather.currentValidAt,NOW-14400000);assert.equal(f.read().weather.retrievedAt,NOW);
  assert.equal(f.read().lastWxAt,0);assert(f.read().weatherTrack,'valid hourly must remain independent');
});
test('B13 M2 repeated four-hour radar frame cannot gain authority from new retrieval',async()=>{
  const input=manifest();input.radar.past[0].time-=14400;input.generated-=14400;
  const f=fixture({manifest:input});await f.fetchRadar();let v=record('B13/old-radar-first',f);
  assert.equal(v.qa.wxTruth.radarAvailable,false,'old radar source must be unavailable');
  f.clock.now+=600000;await f.fetchRadar();v=record('B13/old-radar-repeat',f);
  assert.equal(v.qa.wxTruth.radarAvailable,false,'repeated old radar frame must remain unavailable');
  assert.equal(f.images.length,2);assert.equal(f.read().weatherRadar.frameGeneratedAt,NOW-14400000);
  assert.equal(f.read().weatherRadar.indexGeneratedAt,NOW-14400000);assert.equal(f.read().weatherRadar.retrievedAt,NOW+600000);
  assert.equal(v.qa.wxTruth.radarFrameAgeSec,15000);assert.equal(v.qa.wxTruth.radarAgeSec,0);assert.equal(f.radarPrecipNow(),0);
});
for(const [name,value] of [['missing',undefined],['null',null],['invalid','invalid'],['NaN-string','NaN'],
  ['calendar-invalid','2026-02-30T21:00'],['vm-NaN',NaN]])test('B13 acquired source time '+name,async()=>{
    const payload=healthy({time:value});if(name==='missing')delete payload.current.time;
    const f=fixture({payload});await f.fetchWeather();const v=record('B13/time/'+name,f);unavailable(f,v);
    assert.equal(f.read().weather.currentValidAt,null);assert.equal(f.read().lastWxAt,0);assert(f.read().weatherTrack);
  });
test('B13 literal NaN wire is body rejection, not a JSON timestamp',async()=>{
  const f=fixture({fetch:async()=>({ok:true,status:200,json:async()=>JSON.parse('{"current":{"time":NaN}}')})});
  await f.fetchWeather();unavailable(f,record('B13/malformed-json',f));assert.equal(f.read().weather,null);assert.equal(f.read().lastWxAt,0);
});
for(const interval of [undefined,null,0,-1,'900',NaN,Infinity])test('B13 invalid interval '+String(interval),async()=>{
  const f=fixture({payload:healthy({interval})});await f.fetchWeather();unavailable(f,record('B13/interval/'+String(interval),f));assert.equal(f.read().lastWxAt,0);
});
for(const offset of [1,86400000]){
  test('B13 future source +'+offset+'ms is ineligible',async()=>{
    const f=fixture();f.clock.now=NOW-offset;await f.fetchWeather();unavailable(f,record('B13/future-source/'+offset,f));assert.equal(f.read().lastWxAt,0);
  });
  test('B13 future cache receipt +'+offset+'ms is ineligible',async()=>{
    const seed=fixture();await seed.fetchWeather();const envelope=seed.cache();envelope.ts+=offset;envelope.w.retrievedAt+=offset;
    const bytes=JSON.stringify(envelope),f=fixture({storage:[['salahwx:24.47|39.61|c',bytes]]});f.loadWx();
    unavailable(f,record('B13/future-cache/'+offset,f));assert.equal(f.storage.get('salahwx:24.47|39.61|c'),bytes);
  });
  test('B13 future radar frame +'+offset+'ms is ineligible',async()=>{
    const input=manifest();input.radar.past[0].time+=offset/1000;const f=fixture({manifest:input});await f.fetchRadar();
    assert.equal(record('B13/future-radar/'+offset,f).qa.wxTruth.radarAvailable,false);assert.equal(f.radarPrecipNow(),0);
  });
}
for(const [age,eligible] of [[899999,true],[900000,true],[900001,false]])for(const clock of ['source','receipt'])test('B13 weather '+clock+' boundary '+age,async()=>{
  const f=fixture();if(clock==='source')f.clock.now=NOW+age;await f.fetchWeather();
  if(clock==='receipt'){f.read().weather.retrievedAt=NOW-age;f.read().weather.currentValidAt=NOW;}
  const v=record('B13/weather-'+clock+'/'+age,f);assert.equal(v.qa.cache.currentEligible,eligible);
  if(!eligible)unavailable(f,v);else assert.equal(f.nodes.get('#wt').textContent,'20°');
});
for(const [age,eligible] of [[1199999,true],[1200000,true],[1200001,false]])for(const clock of ['frame','receipt'])test('B13 radar '+clock+' boundary '+age,async()=>{
  const input=manifest();if(clock==='frame')input.radar.past[0].time=(NOW-age)/1000;
  const f=fixture({manifest:input});await f.fetchRadar();if(clock==='receipt')f.read().weatherRadar.retrievedAt=NOW-age;
  assert.equal(record('B13/radar-'+clock+'/'+age,f).qa.wxTruth.radarAvailable,eligible);assert.equal(f.radarPrecipNow(),0);
});
test('B13 M3 per-use expiry withdraws header temperature clouds and effects before outage recovery',async()=>{
  let stage='fresh';const f=fixture({fetch:async(_url,clock)=>stage==='offline'?{ok:false,status:503,json:async()=>healthy()}:
    {ok:true,status:200,json:async()=>healthy({time:new Date(clock.now).toISOString().slice(0,16),cloud_cover_low:70,cloud_cover_mid:70,cloud_cover_high:70})}});
  await f.fetchWeather();const first=cloudView(f);assert(first.a.rainOp>0);assert(first.fills>0);record('B13/outage-fresh',f);
  const raw=f.read().weather,cache=f.storage.get('salahwx:24.47|39.61|c');f.clock.now=NOW+900000;
  assert.equal(f.view().qa.cache.currentEligible,true);f.clock.now++;stage='offline';await f.fetchWeather();
  record('B13/outage-expired',f);
  // Consumer assertion first: M3 leaves the admission/diagnostic function intact.
  assert.equal(f.nodes.get('#wt').textContent,'','expired header must withdraw before recovery');
  unavailable(f);assert.equal(f.read().weather,raw);assert.equal(f.storage.get('salahwx:24.47|39.61|c'),cache);
  f.clock.now+=60000;stage='healthy';await f.fetchWeather();const back=cloudView(f);record('B13/outage-restored',f);
  assert.equal(back.qa.cache.currentEligible,true);assert(back.a.rainOp>0);assert(back.fills>0);
  assert.equal(back.population,first.population);assert.equal(f.nodes.get('#wt').textContent,'20°');assert.equal(back.qa.wxTruth.activeThunder,false);
});
async function zoneAcquisition(change){
  let deliver;const f=fixture({zone:'America/New_York',fetch:()=>new Promise(r=>{deliver=r;})});
  f.clock.now=Date.parse('2026-03-08T07:30:00Z');const pending=f.fetchWeather();if(change)f.set({zone:'Asia/Riyadh'});
  const data=healthy({time:'2026-03-08T03:30'});data.hourly.time=['2026-03-08T03:30','2026-03-08T04:30'];
  deliver({ok:true,status:200,json:async()=>data});await pending;record('zone/'+change,f);return f;
}
test('B14 M4 captured New York request zone survives mutable global Riyadh',async()=>{
  const f=await zoneAcquisition(true);assert.equal(f.read().weather.currentValidAt,Date.parse('2026-03-08T07:30:00Z'),'captured New York wall time must resolve to 07:30Z');
  assert.equal(f.read().weather.currentZone,'America/New_York');assert.equal(f.read().weatherTrack.ep[0],Date.parse('2026-03-08T07:30:00Z'));
});
test('positive unchanged New York request-zone control',async()=>{
  const f=await zoneAcquisition(false);assert.equal(f.read().weather.currentValidAt,Date.parse('2026-03-08T07:30:00Z'));
  assert.equal(f.view().qa.cache.currentEligible,true);
});
test('positive healthy CURRENT model and optional-missing precipitation preserve condition policy',async()=>{
  for(const precip of [2,undefined]){const f=fixture({payload:healthy({weather_code:63,precipitation:precip})});await f.fetchWeather();
    const v=record('positive/model/'+String(precip),f);assert.equal(v.qa.cache.currentEligible,true);
    assert.equal(f.nodes.get('#wt').textContent,'20°');assert.equal(v.a.cls,'rain');assert.equal(v.qa.wxTruth.observedPresent,false);
    assert.equal(v.a.rainOp>0,precip===2);assert.equal(v.qa.wxTruth.activeThunder,false);
  }
});
