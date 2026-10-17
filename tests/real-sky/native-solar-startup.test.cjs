const test=require('node:test');
const assert=require('node:assert/strict');
const path=require('node:path');
const {load}=require('../r001d-harness.cjs');
const sourcePath=process.env.SALAH_SOLAR_SOURCE||path.join(__dirname,'../../src/native/index.html');
const create=()=>load({sourcePath,hash:'#lat=24.47&lon=39.61&tz=Asia/Riyadh&units=c&method=4'});
const acceptedSun=(h,e)=>h.run(`window.SalahNativeSkyHost={cloudLighting:()=>({sun:{altDeg:${e},azDeg:90},utcMs:simNow(),sample:()=>null})}`);
const keys=['--sunamt','--sunbodyamt','--suncore','--sunmid','--sunprofile','--sunlift','--sunx2','--sunvx','--sunvy','--sundisc','--sunflat','--sunray','--sunpulse','--sunlow'];
const properties=h=>Object.fromEntries(keys.map(k=>[k,h.select('.c').style.getPropertyValue(k)]));

test('fresh accepted daytime scene publishes its Sun while the timetable is absent',()=>{
 const h=create();acceptedSun(h,5.5);h.run('today=null;tomorrow=null;beginSkyScene(true);render()');
 assert.equal(h.run('model()'),null);
 assert.equal(h.select('.c').classList.contains('sky-pending'),false);
 assert.equal(+h.select('.c').style.getPropertyValue('--sunbodyamt'),1,'publish Sun before exposing current sky');
 assert.ok(h.select('.c').style.getPropertyValue('--suncore'),'publish current physical colour');
 assert.ok(h.select('.c').style.getPropertyValue('--sunprofile'),'publish resolved low-Sun profile');
});

test('accepted night target cannot expose the previous daytime Sun without a timetable',()=>{
 const h=create();acceptedSun(h,40);h.run('paint(atmosphere(model()))');
 assert.equal(+h.select('.c').style.getPropertyValue('--sunbodyamt'),1);
 h.run('beginRuntimeGeneration();lat=40;lon=-74;tz="America/New_York";resetForNewLocation()');acceptedSun(h,-20);h.run('render()');
 assert.equal(h.run('model()'),null);
 assert.equal(h.select('.c').classList.contains('sky-pending'),false);
 assert.equal(+h.select('.c').style.getPropertyValue('--sunbodyamt'),0,'withdraw old daytime Sun');
 assert.equal(+h.select('.c').style.getPropertyValue('--sunamt'),0);
});

test('pending and settled prayer data publish the same solar vector and horizon placement',()=>{
 const h=create(),query=h.ctx.document.querySelector;let linePresent=true;
 const arc=h.select('.arc'),line=h.select('.arc .horizon'),atmo=h.select('.atmo');
 arc.getBoundingClientRect=()=>({top:52,width:295,height:180});
 line.getBoundingClientRect=()=>({top:156,width:292.4,height:0});
 atmo.getBoundingClientRect=()=>({top:0,width:325,height:530});
 h.ctx.document.querySelector=s=>s==='.arc .horizon'&&!linePresent?null:query(s);
 for(const reduced of [false,true])for(const [code,cloud] of [[0,0],[2,35],[3,100]])for(const elevation of [-20,-1.5,0,5.5,39.9,40,65]){
  acceptedSun(h,elevation);
  h.ctx.matchMedia=()=>({matches:reduced});
  h.run(`__fixtureWeatherCurrent.weather_code=${code};__fixtureWeatherCurrent.cloud_cover=${cloud};weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:'c',zone:tz,retrievedAt:Date.now()})`);
  linePresent=true;h.run('paint(atmosphere(model()))');const settled=properties(h);
  for(const k of keys)h.select('.c').style.removeProperty(k);
  linePresent=false;h.run('paintCelestialWithoutTimetable()');
  assert.deepEqual(properties(h),settled,`solar mismatch at elevation=${elevation}, cloud=${cloud}, reduced=${reduced}`);
 }
});

for(const lunar of [false,true])test('pending celestial scene withdraws old cloud-gated '+(lunar?'lunar':'solar')+' optics',()=>{
  const h=create();acceptedSun(h,lunar?-20:2);
  h.run('__fixtureWeatherCurrent.weather_code=2;__fixtureWeatherCurrent.cloud_cover=35;__fixtureWeatherCurrent.cloud_cover_low=0;__fixtureWeatherCurrent.cloud_cover_mid=20;__fixtureWeatherCurrent.cloud_cover_high=30;__fixtureWeatherCurrent.apparent_temperature=-5;weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:"c",zone:tz,retrievedAt:Date.now()});moonSky={frac:.8,alt:10,H:0};paint(atmosphere(model()))');
  const optics=lunar?['--mhalo','--mcorona','--mparhelia']:['--sunhalo','--sundogs','--sunpillar'];
  for(const key of optics)assert.ok(+h.select('.c').style.getPropertyValue(key)>0,'positive prior-scene control '+key);
  h.run('beginRuntimeGeneration();lat=40;lon=-74;tz="America/New_York";resetForNewLocation()');acceptedSun(h,lunar?40:-20);h.run('render()');
  for(const key of optics)assert.equal(+h.select('.c').style.getPropertyValue(key),0,'old cloud/geometry permission survived: '+key);
});
