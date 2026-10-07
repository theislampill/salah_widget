'use strict';
// R0003 supplied response-zone boundary. Clock conversion and acquisition come from actual source.
const assert=require('node:assert/strict'),{test}=require('node:test');
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const p=path.join(__dirname,'r000c-weather.test.cjs'),text=fs.readFileSync(p,'utf8'),end=text.indexOf("test('control: actual fresh acquisition");
assert(end>0); const m=new Module(p,module); m.filename=p; m.paths=Module._nodeModulePaths(__dirname);
m._compile(text.slice(0,end)+'\nmodule.exports={fixture,healthy};',p); const {fixture,healthy}=m.exports;
const NOW=Date.parse('2026-03-08T07:30:00Z');
function body(zone,provided=true){
  const b=healthy({time:'2026-03-08T03:30',interval:900,weather_code:0,temperature_2m:20,precipitation:0}); b.elevation=120;
  b.hourly.time=['2026-03-08T03:30','2026-03-08T04:30']; b.hourly.temperature_2m=[20,19]; b.hourly.weather_code=[0,3];
  if(provided)b.timezone=zone; return b;
}
for(const [name,returned] of [['contradictory Riyadh','Asia/Riyadh'],['invalid IANA','Not/A_Zone'],['empty',''],['null',null],['non-string',42]]){
  test('R0003 response zone '+name+' cannot mutate current, track, elevation, accepted time or cache',async()=>{
    const f=fixture({lat:40.71,lon:-74.01,zone:'America/New_York',payload:body(returned)}); f.clock.now=NOW; await f.fetchWeather();
    assert.equal(f.read().weather,null); assert.equal(f.read().weatherTrack,null); assert.equal(f.read().siteElev,0);
    assert.equal(f.read().lastWxAt,0); assert.equal(f.cache(),null); assert.equal(f.read().wxBusy,false);
  });
}
for(const [name,returned,provided] of [['absent',undefined,false],['matching','America/New_York',true],['canonical alias','US/Eastern',true]]){
  test('control: R0003 '+name+' New York response metadata preserves captured DST conversion',async()=>{
    const f=fixture({lat:40.71,lon:-74.01,zone:'America/New_York',payload:body(returned,provided)}); f.clock.now=NOW; await f.fetchWeather();
    assert.equal(f.read().weather.currentValidAt,NOW); assert.equal(f.read().weatherTrack.ep[0],NOW);
    assert.equal(f.read().weather.currentZone,'America/New_York'); assert.equal(f.read().siteElev,120); assert.equal(f.cache().w.temp,20);
    assert.equal(f.view().qa.cache.currentEligible,true); assert.equal(f.read().wxBusy,false);
  });
}
test('control: R0003 Etc/UTC canonical alias preserves a UTC request',async()=>{
  const b=body('Etc/UTC'); b.current.time='2026-03-08T07:30'; b.hourly.time=['2026-03-08T07:30','2026-03-08T08:30'];
  const f=fixture({zone:'UTC',payload:b}); f.clock.now=NOW; await f.fetchWeather(); assert.equal(f.read().weather.currentValidAt,NOW);
  assert.equal(f.cache().w.currentZone,'UTC');
});
