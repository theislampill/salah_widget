// Original SolarR2 held-scene controls on the composed source.
// Seed the independent shared Sun publisher directly: the full missing-timetable
// render now also executes the separately exercised Lunar/catalogue initializer.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const html=fs.readFileSync(new URL('../../src/native/index.html',import.meta.url),'utf8');
function section(start,end){
 assert.equal(html.split(start).length,2,'unique native source start');assert.equal(html.split(end).length,2,'unique native source end');
 return html.slice(html.indexOf(start),html.indexOf(end,html.indexOf(start)));
}
const primitives=['const lerp =','const mixRGB=','const rgb  =','const rgba =','const _ss='].map(start=>{
 const lines=html.split('\n').filter(line=>line.startsWith(start));assert.equal(lines.length,1);return lines[0];
}).join('\n');
const weatherCode=section('function wxDrivers(', 'function wxInfo(')+section('function wxClass(', '// tint = sky colour');
const radiometryBlock=html.includes('function nativeSolarRadiometry(')?null:section('  // CORNER-SUN display presentation:','  const moonObservation=Object.freeze(');
const solarCode=html.includes('function nativeSolarRadiometry(')?section('function nativeSolarRadiometry(','function atmosphere('):
 'function nativeSolarRadiometry(e,D,cls){const sm={altDeg:e};'+radiometryBlock+'return {sunCoreRGB,sunMidRGB,sunProfile,sunRadiometry:{airmass:_m,beamTransmission:_Tbeam,displayCctK:_CCT,bodyRadianceScale:_bodyL},sunCloudT:_Tcloud};}';
const ordinarySolarCode=html.includes('  // Existing solar producer/style sink also owns')?
 section('  // Existing solar producer/style sink also owns','  c.style.setProperty("--stars",'):
 section('  // —— CORNER SUN (.suncorner):','  c.style.setProperty("--stars",');
const renderCode=section('function render(){','function updateSimClock(');
const beginCode=section('function beginSkyScene(){','function updateSkySurface(){');
const commitCode=section('function commitSkyScene(A){','// build the animated weather overlay once');
const paintCode=section('function paint(A){','let _lastMoonPaint=');
const preserved=JSON.parse(fs.readFileSync(new URL('./fixtures/native-solar-preservation.json',import.meta.url),'utf8'));
assert.equal(preserved.preimageSha256,'a81b32b46d1153c2cc41f57f6e615f1237a4491774ad383820a18a903013bfcf');
assert.equal(preserved.cases.length,64);
function rig(){
 const properties={},classes=new Set(['sky-pending','sky-initializing']),publication=[];let visibility='';
 const solarStyle={removeProperty(name){if(name==='visibility'){visibility='';publication.push('solar-inherit');}}};
 Object.defineProperty(solarStyle,'visibility',{get:()=>visibility,set:value=>{visibility=value;publication.push('solar-'+value);}});
 const solar={style:solarStyle};
 const c={dataset:{},style:{setProperty:(k,v)=>{properties[k]=v;publication.push(k);},removeProperty:k=>delete properties[k],getPropertyValue:k=>properties[k]??''},classList:{contains:n=>classes.has(n),add:(...n)=>n.forEach(x=>classes.add(x)),remove:(...n)=>n.forEach(x=>classes.delete(x))},getBoundingClientRect:()=>({width:325})};
 const s={clamp:x=>Math.max(0,Math.min(1,x)),identity:'A',solar:60,nativeAvailable:true,simulationValid:true,reduced:false,horizon:164,weather:null,units:'c',weatherReads:0,prayerWithdrawals:0,calendarSelections:0,
  isMotionReduced:()=>s.reduced,simNow:()=>1790355600000,selectedWeather:()=>s.weather,
  weatherDecision(){s.weatherReads++;return {record:s.weather,renderCode:s.weather?.code??null};},
  simulationReady:()=>s.simulationValid,skySceneIdentity:()=>s.identity,model:()=>null,setLocLabel(){},syncWeather(){},withdrawPrayerPresentation(){s.prayerWithdrawals++;},paintWeatherHeader(){},weatherHeader:()=>({}),renderCalendarDates(){s.calendarSelections++;},selectCalendarDisplay:value=>value,
  _skySceneKey:null,_skyCommitted:false,_skyMoonPresence:0,_starProjectionKey:'A',_starsProjected:false,DEBUGLAYERS:false,
  refreshStarAppearance(){},applyCloudState(){},paintClouds(){},tieRainToClouds(){},getComputedStyle:el=>el.style,_cloudReady:false,cloudState:{covLow:0,covMid:0,covHigh:0},_cloudDirty:false,_colDens:null,_cloudCtx:null,_cloudCv:null,updateSkySurface(){},
  $:selector=>selector==='.sun-cloud-mask'?solar:selector==='.arc .horizon'?{getBoundingClientRect:()=>({width:325,top:s.horizon+8})}:selector==='.atmo'?{getBoundingClientRect:()=>({top:8})}:c,
  window:{SalahNativeSkyHost:{cloudLighting:()=>s.nativeAvailable?{sun:{altDeg:s.solar}}:null},SalahMoonRuntime:{invalidate(){},request(){}}}};
 vm.createContext(s);vm.runInContext(primitives+'\n'+weatherCode+'\n'+solarCode+'\n'+beginCode+'\n'+commitCode+'\n'+paintCode+'\n'+renderCode+'\nfunction ordinarySolar(A,c){const _REDUCED=isMotionReduced();'+ordinarySolarCode+'}\n',s);
 return {s,c,solar,properties,classes,publication};
}

// Execute the actual render() and composed missing-timetable publisher. Only
// unrelated Moon/time/projection dependencies are inert; currentness inputs,
// the shared Sun sink, class/visibility handoff and withdrawal are literal source.
function composedRig(){
 const r=rig();Object.assign(r.s,{moonSky:{frac:.5,alt:20},_pbrFailed:false,
  nowParts:()=>({h:13,mi:0,s:0}),moonGeometryObservation:()=>({fresh:true}),
  renderMoon(){},projectStars(){},simDate:()=>new Date('2026-09-25T17:00:00Z')});
 return r;
}
function visible(r){return r.solar.style.visibility==='visible'||(r.solar.style.visibility===''&&!r.classes.has('sky-pending'));}
test('actual composed render publishes and retains a valid Sun without timetable data',()=>{
 const r=composedRig();r.s.render();assert.equal(visible(r),true);
 assert.equal(r.properties['--sunbodyamt'],'1.000');assert.equal(r.s._skySceneKey,'A');
 assert.equal(r.classes.has('sky-pending'),false);assert.equal(r.s.weatherReads,1);
 r.s.render();assert.equal(visible(r),true);assert.equal(r.s.weatherReads,2);
});
for(const [name,revoke,restore] of [
 ['observer revocation',r=>r.s.identity=null,r=>r.s.identity='A'],
 ['unavailable native Sun',r=>r.s.nativeAvailable=false,r=>r.s.nativeAvailable=true],
 ['nonfinite native altitude',r=>r.s.solar=NaN,r=>r.s.solar=60],
])test('actual composed render withdraws the published Sun after '+name,()=>{
 const r=composedRig();r.s.render();assert.equal(visible(r),true,'valid precondition must publish');
 revoke(r);r.s.render();const observed={visible:visible(r),visibility:r.solar.style.visibility};
 // Same-state positive control: the unchanged accepted shared Solar publisher
 // must withdraw on the same loss of input authority.
 r.s.paintNativeSunWithoutTimetable();assert.equal(visible(r),false,'shared sink control');
 assert.equal(observed.visible,false,'actual composed caller must withdraw before returning');
 assert.equal(observed.visibility,'hidden');
 restore(r);r.s.render();assert.equal(visible(r),true,'restored valid input republish');
});
