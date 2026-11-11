'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {fixture,withdrawn,extractAuthored,sourcePath}=require('./weather-no-timetable-fixture.cjs');

test('authored test ingress retains exact runtime bytes and rejects malformed, missing or duplicate owners',()=>{
 const source=fs.readFileSync(sourcePath,'utf8'),runtime=extractAuthored(source);assert(source.includes(runtime));assert.equal(runtime.endsWith('boot();\n'),true);
 const bad=[source.replace('<script src="config.js"></script>',''),source.replace('function render(){','function absentRender(){'),
  source.replace('\nboot();','\nfunction render(){}\nboot();'),source.replace('\nboot();','\n'),source.replace('<script src="config.js"></script>','<script src="wrong.js"></script>')];
 for(const candidate of bad)assert.throws(()=>extractAuthored(candidate),error=>error.code==='SETUP_INCOMPLETE');
});
test('withdrawn painter opportunities do not republish unchanged weather DOM sinks',async()=>{
 const h=await fixture();h.at(901000);h.run('render()');h.paint();withdrawn(h.read());
 let writes=0;const style=h.select('.c').style,write=style.setProperty;style.setProperty=(...args)=>{writes++;return write(...args);};
 for(let i=0;i<6;i++)h.paint();assert.equal(writes,0,'an unchanged withdrawn receipt has no repeated CSS publication');
});
for(const hash of ['&simWx=3&simCloud=95','&timeScale=2'])test('explicit preview lane keeps eligible supported clouds beyond live TTL: '+hash,async()=>{
 const h=await fixture({hash}),initial=h.read();assert(initial.selected);assert(initial.raster.currentFills>0);
 h.at(1901000);h.run('today=null;render()');const next=h.paint();assert(next.selected);assert.equal(next.qa.weatherCandidate.lane,'preview');assert(next.raster.currentFills>0);assert.equal(next.population,initial.population);
});
test('obsolete weather settlement cannot install or clear a published successor after A-to-B-to-A',async()=>{
 let ordinal=0,deliver;
 const h=await fixture({fetch:async(u,init,h,payload)=>{
  if(u.hostname==='api.aladhan.com')return new Promise(()=>{});
  if(u.hostname==='api.open-meteo.com'){
   if(++ordinal===2)return new Promise(resolve=>{deliver=resolve;});
   return {ok:true,json:async()=>payload(ordinal>2?{time:'2026-09-09T00:00'}:{})};
  }
  throw Error('unexpected transport');
 }});
 h.at(951000);const old=h.run('fetchWeather()');assert.equal(typeof deliver,'function');
 h.run('beginRuntimeGeneration();lat=40;lon=-74;resetForNewLocation();beginRuntimeGeneration();lat=24.47;lon=39.61;resetForNewLocation()');
 await h.run('fetchWeather()');assert(h.run('adoptPrayerBundle(__fixtureNextPrayer,"09-09-2026",null,true,false)'));h.run('render()');h.paint();
 const successor=h.run('weather'),before=h.read();assert(before.raster.currentFills>0);deliver({ok:true,json:async()=>h.payload()});await old;
 assert.equal(h.run('weather'),successor);assert.deepEqual(h.read().publication,before.publication);assert.deepEqual(h.read().cov,before.cov);
});

test('actual units reconfiguration revokes the old exact-record target through generation ownership',async()=>{
 const h=await fixture(),prior=h.run('weather'),target=h.run('currentWeatherTarget()');assert(h.read().raster.currentFills>0);
 h.ctx.__oldWeather=prior;h.run('void applyConfig({...CONFIG,units:"f"},{save:false})');
 const next=h.run('currentWeatherTarget()');assert(next.generation>target.generation);assert.equal(next.lat,target.lat);assert.equal(next.lon,target.lon);
 assert.equal(h.run('units'),'f');assert.equal(h.run('weatherEligibility(__oldWeather).eligible'),false);withdrawn(h.read());
});
