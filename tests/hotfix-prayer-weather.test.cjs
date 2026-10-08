const {test}=require('node:test');
const assert=require('node:assert/strict');
const {load,prayerForDate}=require('./r001d-harness.cjs');
const path=require('node:path');
const sourcePath=process.env.SALAH_HOTFIX_SOURCE||path.join(__dirname,'../src/native/index.html');
const make=()=>load({sourcePath,hash:'#lat=24.47&lon=39.61&tz=Asia/Riyadh&units=c&method=4'});

test('native celestial presence follows the accepted physical Sun, not timetable-fitted altitude',()=>{
 const h=make(),before=h.run('JSON.stringify(model())');
 // Deliberately inconsistent timetable fit: real provider prayer events need
 // not be geometric 0-degree crossings. The arc retains that timetable; the
 // luminous body, atmosphere and lunar day fade must use accepted astronomy.
 h.run('sunMetrics=()=>({x:20,y:20,altN:.1,altDeg:5})');
 for(const elevation of [-8,-2,0,5.5,40]){
  h.run(`window.SalahNativeSkyHost={cloudLighting:()=>({sun:{altDeg:${elevation},azDeg:268},utcMs:simNow(),owner:'accepted physical fixture'})}`);
  const a=h.run('atmosphere(model())');
  assert.equal(a.solarElevationDeg,elevation);
  assert.equal(a.cloudElevation,elevation);
  h.run('paint(atmosphere(model()))');
  const style=h.select('.c').style;
  if(elevation<=-1.5){assert.equal(+style.getPropertyValue('--sunamt'),0);assert.equal(+style.getPropertyValue('--sunbodyamt'),0);}
  assert.equal(h.run('JSON.stringify(model())'),before,'Celestial geometry must not rewrite the prayer timetable');
 }
});

test('lunar droplet corona needs admitted water cloud or fog, not humidity alone',()=>{
 const h=make();h.run('sunMetrics=()=>({x:20,y:20,altN:0,altDeg:-20});moonSky={frac:.5,alt:25,H:42};_pbrFailed=false;');
 for(const [code,mid,expect] of [[0,0,false],[2,35,true],[45,0,true]]){
  h.run(`__fixtureWeatherCurrent.weather_code=${code};__fixtureWeatherCurrent.relative_humidity_2m=95;__fixtureWeatherCurrent.dew_point_2m=23;__fixtureWeatherCurrent.cloud_cover_low=0;__fixtureWeatherCurrent.cloud_cover_mid=${mid};__fixtureWeatherCurrent.cloud_cover_high=0;weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:'c',zone:tz,retrievedAt:Date.now()});`);
  const a=h.run('atmosphere(model())');
  assert.equal(a.lunarCorona>0,expect,`WMO ${code}, mid cloud ${mid}`);
 }
});
test('solar body has one radiometric colour profile, without a brighter independent orange collar',()=>{
 const h=make();
 for(const elevation of [0,1,3,5.5,10,40]){
  h.run(`sunMetrics=()=>({x:20,y:20,altN:0,altDeg:${elevation}})`);
  const a=h.run('atmosphere(model())'),rgb=s=>s.match(/[\d.]+/g).map(Number),core=rgb(a.sunCoreRGB),limb=rgb(a.sunMidRGB);
  for(let k=0;k<3;k++)assert.ok(limb[k]<=core[k],`independent collar at ${elevation}: ${core} / ${limb}`);
 }
 const source=require('node:fs').readFileSync(sourcePath,'utf8'),body=source.match(/\.atmo \.suncorner \.disc,\.atmo \.sunbody \.disc\{([\s\S]+?)\}/)[1];
 assert.ok(body.includes('circle closest-side'),'body profile must terminate at its declared radius');
 assert.doesNotMatch(body,/#fff(?:\s|,)/,'no unconditional white filament bypassing admitted attenuation');
});
test('enlarged solar body does not inflate at the horizon; high Sun and horizon presence stay independent',()=>{
 const h=make();let previous=null;
 for(const elevation of [-2,-1.5,0,1,3,5.5,10,40,65]){
  h.run(`{const a=atmosphere(model());a.solarElevationDeg=${elevation};paint(a);}`);
  const style=h.select('.c').style,diameter=240*Number(style.getPropertyValue('--sundisc'));
  assert.ok(diameter>=206&&diameter<=265,`body diameter at ${elevation}: ${diameter}`);
  if(elevation<=5.5)assert.ok(diameter>=250,'low Sun retains the declared broad body');
  if(previous!==null)assert.ok(diameter<=previous+.25,'emergence must not inflate the body');
  if(elevation<=-1.5){assert.equal(+style.getPropertyValue('--sunamt'),0);assert.equal(+style.getPropertyValue('--sunbodyamt'),0);}
  if(elevation>=40)assert.equal(diameter,206.4,'established high-Sun footprint');
  previous=diameter;
 }
});

test('low solar body has a resolved continuous radiance profile instead of a flat central fill',()=>{
 const h=make();
 for(const elevation of [0,1,5.5]){
  h.run(`sunMetrics=()=>({x:20,y:20,altN:0,altDeg:${elevation}})`);
  const a=h.run('atmosphere(model())');
  assert.ok(Array.isArray(a.sunProfile)&&a.sunProfile.length>=6,'Missing resolved body profile');
  const rgb=s=>s.match(/[\d.]+/g).map(Number),a0=rgb(a.sunProfile[0].colour),a6=rgb(a.sunProfile.find(p=>p.radius===.6).colour);
  assert.ok(a0.some((x,k)=>x>a6[k]),'Centre60% cannot be a uniform paper-lantern fill');
 }
});

test('clear low-Sun colour recovers with atmospheric beam transmission before noon',()=>{
 const h=make();h.run('sunMetrics=()=>({x:20,y:20,altN:0,altDeg:5.5})');
 const a=h.run('atmosphere(model())'),rgb=a.sunCoreRGB.match(/[\d.]+/g).map(Number);
 assert.ok(rgb[2]/rgb[0]>.4,'The clear +5.5deg body is still trapped in the2000K collar colour: '+rgb);
});

test('cloud twilight colour follows solar geometry, never the binary timetable day flag',()=>{
 const h=make();h.run('_airDrift=()=>.5');
 for(const e of [-8,-5,-.85,0,1,5.5,40]){
  h.run(`sunMetrics=()=>({x:20,y:20,altN:0,altDeg:${e}});isDayNow=()=>false`);
  const a=h.run('atmosphere(model())');h.run('isDayNow=()=>true');const b=h.run('atmosphere(model())');
  assert.deepEqual(a.cloudTint,b.cloudTint,'Timetable sunrise switches cloud ambient colour at '+e);
  assert.deepEqual(a.cloudSunCol,b.cloudSunCol,'Timetable sunrise switches direct cloud lighting at '+e);
 }
});

test('predawn clouds retain cool ambient light and low-Sun cloud colour evolves continuously',()=>{
 const h=make();h.run('isDayNow=()=>false;_airDrift=()=>.5');
 const sample=e=>{h.run(`sunMetrics=()=>({x:20,y:20,altN:0,altDeg:${e}})`);return h.run('atmosphere(model())').cloudTint;};
 for(const e of [-8,-5]){const c=sample(e);assert.ok(c[2]>c[0]+10,'Predawn orange ambient cloud tint at '+e+': '+c);}
 for(const e of [-8,-1.5,0,2,5.5,18]){
  const a=sample(e-.01),b=sample(e+.01);
  assert.ok(Math.max(...a.map((v,k)=>Math.abs(v-b[k])))<1,'Cloud palette step at '+e);
 }
});
function paintAt(h,day,hour,min,second=0){h.clock.wall=h.run(`epochForTzTime(2026,9,${day},${hour},${min},tz)+${second}*1000`);h.run('_simBase=Date.now();_rafT0=performance.now();TIMESCALE=0;render();');return h.run('model()');}
function rows(h){return [...h.select('.times').innerHTML.matchAll(/<div class="p ([^"]*)"[^>]*><b>([^<]+)<\/b><span class="tm">([^<]+)<\/span>/g)].map(m=>({cls:m[1].trim().split(/\s+/),key:m[2],time:m[3]}));}
function agree(h,m){const r=rows(h),on=r.filter(r=>r.cls.includes('on')),now=r.filter(r=>r.cls.includes('now'));assert.equal(r.length,6);assert.deepEqual(on.map(r=>r.key),[m.nextKey]);assert.deepEqual(now.map(r=>r.key),m.currentKey==='Forenoon'?[]:[m.currentKey]);assert.ok(h.select('.left').innerHTML.includes('>'+m.nextKey+'<'));assert.equal(on[0].time,h.run('fmt(model().nextTime)'));assert.ok(h.select('.arc').innerHTML.includes('data-prayer-key="'+m.nextKey+'"'));}
test('second-level boundaries for every event and Sunrise to Forenoon retain independent current/next',()=>{
 const h=make(),events=[['Fajr',4,46,'Isha','Sunrise'],['Sunrise',6,5,'Fajr','Dhuhr'],['Dhuhr',12,19,'Forenoon','Asr'],['Asr',15,48,'Dhuhr','Maghrib'],['Maghrib',18,33,'Asr','Isha'],['Isha',20,3,'Maghrib','Fajr']];
 for(const [key,hr,min,before,next] of events)for(const offset of [-1,0,1]){const m=paintAt(h,8,hr,min,offset);assert.equal(m.currentKey,offset<0?before:key);assert.equal(m.nextKey,offset<0?key:next);agree(h,m);}
 for(const offset of [-1,0,1]){const m=paintAt(h,8,6,25,offset);assert.equal(m.currentKey,offset<0?'Sunrise':'Forenoon');assert.equal(m.nextKey,'Dhuhr');agree(h,m);}
});
test('overnight next row uses tomorrow Fajr, same target as countdown and arc',()=>{const h=make(),m=paintAt(h,8,23,59,59);assert.equal(m.nextTime,'04:47');assert.equal(m.nextDateStr,'09-09-2026');agree(h,m);});
test('new target withdraws old prayer rows, countdown and weather together before provider settlement',()=>{
 const h=make();paintAt(h,8,16,0);h.run('beginRuntimeGeneration();lat=40;lon=-74;tz="America/New_York";resetForNewLocation();render();');
 assert.deepEqual(rows(h).filter(r=>r.cls.includes('on')||r.cls.includes('now')),[]);assert.equal(h.select('.arc').innerHTML,'');assert.equal(h.select('#wt').textContent,'');assert.equal(h.select('#wi').textContent,'—');assert.equal(h.ctx.qaState().render,null);
});
test('yesterday cannot nominate a current next prayer at midnight; eligible tomorrow promotion restores it',()=>{
 const h=make();paintAt(h,8,23,59,59);const stale=paintAt(h,9,0,0);assert.equal(stale,null);assert.equal(rows(h).filter(r=>r.cls.includes('on')).length,0);
 h.run('maintainPrayerDay();render();');const m=h.run('model()');assert.equal(m.nextDateStr,'09-09-2026');agree(h,m);
});
test('live current categories keep condition icons and model-supported precipitation without observed strikes',()=>{
 for(const [code,amount,icon,category] of [[0,0,'🌙','clear'],[2,0,'☁️','cloud'],[3,0,'☁️','overcast'],[45,0,'🌫️','fog'],[51,.3,'🌦️','drizzle'],[63,2,'🌧️','rain'],[73,2,'🌨️','snow'],[95,5,'⛈️','thunder']]){
  const h=make();h.run(`__fixtureWeatherCurrent.weather_code=${code};__fixtureWeatherCurrent.precipitation=${amount};weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:'c',zone:tz,retrievedAt:Date.now()});render();`);
  const q=h.ctx.qaState();assert.equal(h.select('#wi').textContent,icon);assert.equal(h.select('#wt').textContent,'24°');assert.equal(h.select('.c').dataset.fx,category);assert.match(h.select('#wi').title,/Open-Meteo current model estimate/);assert.equal(q.wxTruth.observedPresent,false);assert.equal(q.wxTruth.conditionState,'model-estimated-'+category);assert.equal(q.wxTruth.activePrecip,amount>0);assert.equal(q.wxTruth.activeThunder,false);assert.equal(h.select('.c').dataset.lightning,'off');assert.equal(q.weatherHeader.code,code);assert.equal(q.weatherHeader.temperature,24);assert.equal(q.weatherHeader.generation,q.wxTruth.target.generation);
 }
});
test('weather unavailable, expired and wrong target never retains old temperature/icon pair',()=>{
 for(const change of ['weather=null','__advance=900001','beginRuntimeGeneration()']){
  const h=make();h.run('render()');if(change.startsWith('__'))h.clock.wall+=900001;else h.run(change);h.run('render()');
  assert.equal(h.select('#wi').textContent,'—');assert.equal(h.select('#wt').textContent,'');assert.equal(h.ctx.qaState().weatherHeader.conditionState,'unavailable');assert.equal(h.ctx.qaState().wxTruth.activePrecip,false);
  assert.equal(h.select('.c').dataset.fx,'unavailable');assert.equal(h.ctx.qaState().wxTruth.displayCondition,'unavailable');
 }
});
test('missing or contradictory amounts retain a model condition without inventing rain effects',()=>{
 for(const amount of ['null','0','-1']){
  const h=make();h.run(`__fixtureWeatherCurrent.weather_code=63;__fixtureWeatherCurrent.precipitation=${amount};__fixtureWeatherCurrent.rain=null;__fixtureWeatherCurrent.showers=null;weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:'c',zone:tz,retrievedAt:Date.now()});render();`);
  assert.equal(h.select('#wi').textContent,'🌧️');assert.equal(h.select('.c').dataset.fx,'rain');assert.equal(h.select('.c').dataset.precip,'off');assert.equal(h.ctx.qaState().wxTruth.observedPresent,false);
 }
});
test('missing temperature does not discard an eligible model condition or retain an old value',()=>{
 const h=make();h.run('render();__fixtureWeatherCurrent.weather_code=63;__fixtureWeatherCurrent.temperature_2m=null;weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:"c",zone:tz,retrievedAt:Date.now()});render();');
 assert.equal(h.select('#wi').textContent,'🌧️');assert.equal(h.select('#wt').textContent,'');
});
test('every supported provider WMO code retains its category in the live condition lane',()=>{
 const h=make(),codes=h.run('[..._WX_CODES]');
 for(const code of codes){
  const category=code<=0?'clear':code<=2?'cloud':code===3?'overcast':code<=48?'fog':code<=57?'drizzle':code<=67?'rain':code<=77?'snow':code<=82?'rain':code<=86?'snow':'thunder';
  h.run(`__fixtureWeatherCurrent.weather_code=${code};__fixtureWeatherCurrent.precipitation=2;weather=admitWeatherRecord(__fixtureWeatherCurrent,{lat,lon,units:'c',zone:tz,retrievedAt:Date.now()});render();`);
  assert.equal(h.select('.c').dataset.fx,category,`WMO ${code}`);assert.equal(h.ctx.qaState().weatherHeader.rawCode,code);assert.equal(h.ctx.qaState().wxTruth.observedPresent,false);
 }
});
test('new-generation tomorrow adoption cannot re-admit old-generation current rows',()=>{
 const h=make();h.run('beginRuntimeGeneration();adoptPrayerBundle(__fixtureNextPrayer,"09-09-2026");render();');assert.equal(h.run('model()'),null);assert.equal(rows(h).filter(r=>r.cls.includes('on')).length,0);
});
test('native clock controls pause, seek, change rate and return to the live current-weather lane',()=>{
 const h=make(),t=h.clock.wall;
 h.run(`SalahClock.set({utcMs:${t},rate:600})`);assert.equal(h.run('ADVANCING'),true);assert.equal(h.run('FOLLOW_WALL_CLOCK'),false);
 h.clock.now+=1000;assert.equal(h.run('simNow()'),t+600000);
 h.run('SalahClock.set({rate:0})');const paused=h.run('simNow()');h.clock.now+=1000;assert.equal(h.run('simNow()'),paused);
 h.run(`SalahClock.set({utcMs:${t-10000},rate:10})`);assert.equal(h.run('simNow()'),t-10000);
 h.run('weather={...weather,src:"forecast"};SalahClock.set({live:true})');assert.equal(h.run('simNow()'),h.clock.wall);assert.equal(h.run('ADVANCING'),false);assert.equal(h.run('TIMESCALE'),1);assert.notEqual(h.run('selectedWeather()?.src'),'forecast');
 assert.throws(()=>h.run('SalahClock.set({rate:NaN})'));assert.equal(h.run('FOLLOW_WALL_CLOCK'),true);
});
test('pausing an explicit forecast playback retains preview provenance instead of dropping its weather',()=>{
 const h=make();h.run('SalahClock.set({rate:60});weather={code:63,temp:24,precip:2,target:currentWeatherTarget(),src:"forecast"};render();');
 assert.equal(h.select('.c').dataset.fx,'rain');
 h.run('SalahClock.set({rate:0});');assert.equal(h.select('.c').dataset.fx,'rain');assert.equal(h.ctx.qaState().wxTruth.lane,'preview');assert.equal(h.ctx.qaState().wxTruth.observedPresent,false);
 h.run('SalahClock.set({live:true});');assert.notEqual(h.run('selectedWeather()?.src'),'forecast');
});

test('hourly thunder model in time-lapse does not invent lightning observations or flashes',()=>{
 const h=make();h.run('SalahClock.set({rate:60});weather={code:95,temp:24,precip:3,target:currentWeatherTarget(),src:"forecast"};render();');
 assert.equal(h.select('.c').dataset.fx,'thunder');assert.equal(h.select('#wi').textContent,'⛈️');
 assert.equal(h.select('.c').dataset.precip,'on');assert.equal(h.select('.c').dataset.lightning,'off');
 assert.equal(h.ctx.qaState().wxTruth.permissions.lightning,false);assert.equal(h.ctx.qaState().wxTruth.observedPresent,false);
});
