'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {fixture,loopDriver,withdrawn,sourcePath,sourceValid,sha}=require('./weather-no-timetable-fixture.cjs');
console.log('R000B authored source '+sourcePath+' SHA256 '+sha(fs.readFileSync(sourcePath)));

test('healthy current model establishes the actual cloud deck and full-model expiry still withdraws',async()=>{
 const h=await fixture(),fresh=h.read();assert(fresh.model&&fresh.selected);assert.deepEqual(fresh.cov,[.92,.9,.6]);assert(fresh.raster.currentFills>0&&fresh.density>0);
 h.at(901000);assert(h.run('adoptPrayerBundle(__fixtureNextPrayer,"09-09-2026",null,true,false)'));h.run('render()');withdrawn(h.paint());assert.equal(h.read().population,fresh.population);
});
test('midnight missing timetable at 901s withdraws joined cloud state and retained raster before another painter',async()=>{
 const h=await fixture(),fresh=h.read(),raw=h.run('weather'),cache=[...h.storage];h.at(900000);h.run('render()');const boundary=h.read();
 assert.equal(boundary.model,false);assert.equal(boundary.selected,true);assert.deepEqual(boundary.cov,fresh.cov);assert.equal(boundary.scene,fresh.scene);
 h.at(901000);h.run('render()');const gone=h.read();withdrawn(gone);assert.equal(gone.selected,false);assert.equal(gone.header.icon,'—');assert.equal(gone.fx,'unavailable');assert.equal(gone.precip,'off');
 assert.equal(h.run('weather'),raw);assert.deepEqual([...h.storage],cache);assert.equal(gone.raw.currentValidAt,sourceValid);assert.equal(gone.population,fresh.population);
 assert.equal(gone.publication.state,'withdrawn-unavailable');assert.equal(gone.independent.pending,false);assert.equal(gone.independent.geometry,true);assert.equal(gone.independent.stars,gone.scene);
});
test('actual loop painter at 900077ms withdraws after inclusive expiry within the same rendered second',async()=>{
 const h=await fixture();h.at(900000);const loop=loopDriver(h);loop.frame();const boundary=h.read();assert(boundary.selected);assert(boundary.raster.currentFills>0);
 h.at(900077);loop.frame();const gone=h.read();assert(!gone.selected);withdrawn(gone);assert.equal(loop.frames.size,1);
});
for(const reduced of [false,true])test('hidden expiry resumes once with immediate withdrawal and held axes; reduced='+reduced,async()=>{
 const h=await fixture({reduced});h.at(900000);const loop=loopDriver(h);loop.frame();const before=h.read();loop.visibility('hidden');assert.equal(loop.frames.size,0);
 h.at(901000);loop.visibility('visible');loop.visibility('visible');loop.frame();const gone=h.read();withdrawn(gone);assert.equal(loop.frames.size,1);
 assert.equal(gone.population,before.population);assert.deepEqual(gone.phase,before.phase);assert.deepEqual(gone.life,before.life);assert.equal(h.calls.filter(c=>c.host==='api.open-meteo.com').length,1);
});
test('warm exact-record fresh no-model retains; cold and fresh replacement no-model withhold until real prayer recovery',async()=>{
 const cold=await fixture({cold:true});assert(cold.read().selected);withdrawn(cold.read());
 const h=await fixture(),fresh=h.read();h.run('today=null;render()');assert.deepEqual(h.read().cov,fresh.cov);assert(h.read().raster.currentFills>0);
 h.at(951000);h.freshAtNow();await h.refresh();h.run('render()');const withheld=h.read();assert(withheld.selected);withdrawn(withheld);assert.equal(withheld.header.code,95);
 assert(h.run('adoptPrayerBundle(__fixtureNextPrayer,"09-09-2026",null,true,false)'));h.run('render()');const recovered=h.paint();assert(recovered.selected&&recovered.model);assert(recovered.raster.currentFills>0);assert.deepEqual(recovered.cov,[.92,.9,.6]);assert.equal(recovered.population,fresh.population);
});
test('consumed cloud and effect diagnostics stay honest without repairing state or adopting a pending candidate',async()=>{
 const h=await fixture();h.run('today=null;render()');const warm=h.read();assert.deepEqual([warm.qa.clouds.low,warm.qa.clouds.mid,warm.qa.clouds.high],warm.cov);assert.equal(warm.qa.wxTruth.activePrecip,false);
 const authority=warm.publication,clears=h.raster.clears;h.at(901000);const before=h.read();assert.deepEqual(before.publication,authority);assert.equal(h.raster.clears,clears);assert.equal(before.qa.weatherCandidate.conditionState,'unavailable');
 h.run('render()');withdrawn(h.read());
});
test('repeated expired render and paint are idempotent for authority, population, axes and retained resources',async()=>{
 const h=await fixture();h.at(901000);h.run('render()');h.paint();const first=h.read(),canvas=h.run('_cloudCv'),columns=h.run('_colDens');
 for(let i=0;i<8;i++){h.run('render()');h.paint();withdrawn(h.read());}
 const last=h.read();assert.deepEqual(last.publication,first.publication);assert.equal(last.population,first.population);assert.deepEqual(last.phase,first.phase);assert.deepEqual(last.life,first.life);
 assert.equal(h.run('_cloudCv'),canvas);assert.equal(h.run('_colDens'),columns);assert.equal(last.requests,first.requests);
});
for(const key of ['currentValidAt','retrievedAt'])for(const [age,eligible] of [[899999,true],[900000,true],[900001,false],[-1,false]])test(key+' preserves inclusive and zero-future bounds at actual no-model consumer: '+age,async()=>{
 const h=await fixture();h.run('today=null;weather.'+key+'=Date.now()-('+age+');render()');const v=h.read();assert.equal(v.selected,eligible);if(eligible)assert(v.raster.currentFills>0);else withdrawn(v);
});
test('same coordinates in a new generation and A-to-B-to-A cannot retain old coverage',async()=>{
 const h=await fixture();for(const target of [[24.47,39.61],[40,-74],[24.47,39.61]]){h.run('beginRuntimeGeneration();lat='+target[0]+';lon='+target[1]+';render()');withdrawn(h.read());assert.equal(h.read().selected,false);}
});
test('unknown weather cannot become an observed clear condition and gated overlays withdraw',async()=>{
 const h=await fixture();for(const name of ['--ray','--anticrep','--heat','--warm','--cool','--frost'])h.select('.c').style.setProperty(name,'.5');
 h.at(901000);h.run('render()');const v=h.read();assert.equal(v.header.icon,'—');assert.match(v.header.label,/Weather unavailable/);assert.equal(v.qa.wxTruth.displayCondition,'unavailable');
 for(const name of ['--ray','--anticrep','--heat','--warm','--cool','--frost'])assert.equal(+h.select('.c').style.getPropertyValue(name),0,name);
});
// R003A R3A-01 (CI-07). The no-timetable celestial painter owns withdrawing every prior-scene solar optic itself,
// so a failed effects withdrawal cannot leave crepuscular or anticrepuscular light from an earlier scene shown.
const SOLAR_OPTICS=['--ray','--anticrep','--sunhalo','--sundogs','--sunpillar'];
function recordOpticWrites(h,failKey){
 const style=h.select('.c').style,original=style.setProperty,writes=[],faults={count:0};
 style.setProperty=function(key,value){if(key===failKey){faults.count++;throw Error('R003A injected effects-withdrawal fault');}
  if(SOLAR_OPTICS.includes(key))writes.push([key,String(value)]);return original.call(this,key,value);};
 return {writes,faults,restore(){style.setProperty=original;}};
}
test('R3A-01 no-timetable celestial paint withdraws crepuscular and anticrepuscular optics even when the effects withdrawal fails',async()=>{
 const h=await fixture();for(const name of SOLAR_OPTICS)h.select('.c').style.setProperty(name,'.5');
 h.at(901000);const probe=recordOpticWrites(h,'--rain-op');h.run('render()');probe.restore();
 assert(probe.faults.count>=2,'the effects withdrawal and its bounded retry both failed');
 for(const name of SOLAR_OPTICS)assert.equal(+h.select('.c').style.getPropertyValue(name),0,name);
 for(const [key,value] of probe.writes)assert.equal(+value,0,'no non-zero solar-optic write while withdrawn: '+key+'='+value);
 assert.equal(h.read().independent.pending,false,'the independent bodies were still published');
});
test('R3A-01 the healthy no-timetable sequence writes only zero solar optics, never transient light',async()=>{
 const h=await fixture();for(const name of SOLAR_OPTICS)h.select('.c').style.setProperty(name,'.5');
 h.at(901000);const probe=recordOpticWrites(h,null);h.run('render()');probe.restore();
 assert(probe.writes.length>0,'the withdrawn sequence wrote solar optics');
 for(const [key,value] of probe.writes)assert.equal(+value,0,key+'='+value);
 for(const name of SOLAR_OPTICS)assert.equal(+h.select('.c').style.getPropertyValue(name),0,name);
});
test('R3A-01 a healthy timetable scene keeps its computed crepuscular and anticrepuscular values',async()=>{
 const h=await fixture({hash:'&simWx=2&simCloud=50&simHumid=80'});
 h.run('window.SalahNativeSkyHost={cloudLighting:()=>({sun:{altDeg:20,azDeg:120},utcMs:simNow(),sample:()=>null})}');
 h.run('render()');assert(h.read().model,'timetable rendered');const style=h.select('.c').style;
 const A=JSON.parse(h.run('JSON.stringify((({rayIntensity,antiCrep})=>({rayIntensity,antiCrep}))(atmosphere(model())))'));
 assert(A.rayIntensity>0&&A.antiCrep>0,'control: a broken-cloud low-ish Sun computes visible shafts');
 assert.equal(style.getPropertyValue('--ray'),A.rayIntensity.toFixed(3));
 assert.equal(style.getPropertyValue('--anticrep'),(0.8*A.antiCrep).toFixed(3));
});
test('R3A-01 the no-timetable reset zeroes exactly the listed optics and leaves the solar presentation intact',async()=>{
 const h=await fixture();h.at(901000);h.run('withdrawWeatherEffects(weatherDecision(),"r003a probe")');
 const style=h.select('.c').style,original=style.setProperty,writes=[];
 style.setProperty=function(key,value){writes.push([key,String(value)]);return original.call(this,key,value);};
 try{h.run('paintCelestialWithoutTimetable(weatherDecision())');}finally{style.setProperty=original;}
 assert.deepEqual(writes.filter(([,value])=>value==='0').map(([key])=>key).sort(),
  ['--anticrep','--mcorona','--mhalo','--mparhelia','--ray','--sundogs','--sunhalo','--sunpillar']);
 const last=key=>writes.filter(([k])=>k===key).at(-1)?.[1];
 for(const key of ['--sunvx','--sunvy','--sunray','--sunlift','--sundisc'])assert.equal(style.getPropertyValue(key),last(key),key+' is the solar presentation value');
 assert.match(style.getPropertyValue('--sunvx'),/^[0-9.]+%$/);assert(+style.getPropertyValue('--sunray')>0,'--sunray keeps its transmittance value');
});
test('R3A-01 a rendered timetable never enters the no-timetable celestial painter',async()=>{
 const h=await fixture();h.run('globalThis.__r003aCelestial=0;const __r003aPaint=paintCelestialWithoutTimetable;paintCelestialWithoutTimetable=function(...a){__r003aCelestial++;return __r003aPaint.apply(this,a);}');
 h.run('render()');assert(h.read().model);assert.equal(h.run('__r003aCelestial'),0);
 h.at(901000);h.run('render()');assert.equal(h.run('__r003aCelestial'),1,'control: the wrapped painter is reachable');
});
