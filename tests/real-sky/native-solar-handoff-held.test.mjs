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
function ordinaryState(r,fresh=false){
 const d=r.s.wxDrivers(r.s.weather),sun=r.s.nativeSolarRadiometry(r.s.solar,d,r.s.wxClass(r.s.weather?.code??null));
 return {...sun,solarElevationDeg:r.s.solar,heat:d.heat,
  accent:[1,2,3],accent2:[1,2,3],text:[1,2,3],skyTop:[1,2,3],skyMid:[1,2,3],skyHorizon:[1,2,3],glow:[1,2,3,0],horizon:[1,2,3,0],sunX:0,sunY:0,
  starOpacity:0,milkyWayOpacity:0,mwTilt:0,starTurb:0,moonOcc:1,starBlur:0,moonDisc:1,moonBeam:0,moonGrp:1,moonSky:[1,2,3],moonGlow:0,aerosolDensity:0,
  warm:0,cool:0,frost:0,windDirSign:1,rainSlant:0,snowSlant:0,rainOp:0,rayIntensity:0,grainStrength:0,antiX:0,belt:0,airglow:[1,2,3,0],aurora:0,
  sunHalo:0,sunDogs:0,sunPillar:0,pillarCol:'rgba(0,0,0,0)',antiCrep:0,moonParhelia:0,lunarHalo:0,lunarCorona:0,
  cls:'clear',info:{},weatherDecision:{conditionState:'unavailable',visualPermissions:{rain:false,snow:false,lightning:false}},moonObservation:{fresh}};
}
function shown(r){return r.solar.style.visibility==='visible'||(r.solar.style.visibility===''&&!r.classes.has('sky-pending'));}
test('actual ordinary paint retains the first Sun while Moon completion is held',()=>{
 const r=rig();r.s.paintNativeSunWithoutTimetable();assert.equal(shown(r),true);r.s.paint(ordinaryState(r,false));
 assert.equal(shown(r),true,'timetable arrival must not withdraw a valid Sun while Moon is held');
 assert.equal(r.solar.style.visibility,'visible');assert.ok(r.classes.has('sky-pending'));assert.ok(r.classes.has('sky-initializing'));assert.equal(r.classes.has('moon-ready'),false);assert.equal(r.s._skyCommitted,false);
});
test('actual ordinary paint retains the first Sun while catalogue completion is held',()=>{
 const r=rig();r.s.paintNativeSunWithoutTimetable();r.s._starProjectionKey='previous';r.s.paint(ordinaryState(r,true));
 assert.equal(shown(r),true,'fresh Moon does not relax the held star/catalogue scene fence');assert.equal(r.solar.style.visibility,'visible');assert.ok(r.classes.has('sky-pending'));assert.equal(r.s._skyCommitted,false);
});
test('completed actual ordinary scene restores inherited Solar visibility after its fence clears',()=>{
 const r=rig();r.s.paintNativeSunWithoutTimetable();r.s.paint(ordinaryState(r,false));r.s.paint(ordinaryState(r,true));
 assert.equal(r.classes.has('sky-pending'),false);assert.equal(r.classes.has('sky-initializing'),false);assert.equal(r.s._skyCommitted,true);assert.equal(r.solar.style.visibility,'');assert.equal(shown(r),true);
});
test('actual ordinary paint cannot re-expose the prior Sun after target revocation',()=>{
 const r=rig();r.s.paintNativeSunWithoutTimetable();r.s.paint(ordinaryState(r,false));r.s.identity=null;r.s.paint(ordinaryState(r,true));
 assert.equal(shown(r),false);assert.equal(r.solar.style.visibility,'hidden');assert.ok(r.classes.has('sky-pending'));assert.equal(r.s._skyCommitted,false);assert.equal(r.s._skySceneKey,null);
});
