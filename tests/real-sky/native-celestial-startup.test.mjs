import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const html=fs.readFileSync(new URL('../../src/native/index.html',import.meta.url),'utf8');
function section(start,end){
 assert.equal(html.split(start).length,2,'unique native source start');assert.equal(html.split(end).length,2,'unique native source end');
 return html.slice(html.indexOf(start),html.indexOf(end,html.indexOf(start)));
}
const code=html.slice(html.indexOf('function nativeSolarRadiometry('),html.indexOf('function atmosphere('));
const primitives=['const lerp =','const mixRGB=','const rgb  =','const _ss='].map(start=>{
 const lines=html.split('\n').filter(line=>line.startsWith(start));assert.equal(lines.length,1);return lines[0];
}).join('\n');
const weatherCode=section('function wxDrivers(', 'function wxInfo(')+section('function wxClass(', '// tint = sky colour');
const ordinarySolarCode=section('  // Existing solar producer/style sink also owns','  c.style.setProperty("--stars",');
const solarPreservation=JSON.parse(fs.readFileSync(new URL('./fixtures/native-solar-preservation.json',import.meta.url),'utf8'));
assert.equal(solarPreservation.preimageSha256,'a81b32b46d1153c2cc41f57f6e615f1237a4491774ad383820a18a903013bfcf');
assert.equal(solarPreservation.cases.length,64);
function rig(){
 const properties={},classes=new Set(['sky-pending','sky-initializing']),events=[],publication=[];
 const c={style:{setProperty:(k,v)=>{properties[k]=v;publication.push(k);},removeProperty:k=>delete properties[k],getPropertyValue:k=>properties[k]??''},classList:{contains:n=>classes.has(n),remove:(...names)=>{names.forEach(n=>classes.delete(n));publication.push(...names);}}};
 const s={_skySceneKey:null,_skyMoonPresence:0,_pbrFailed:false,moonSky:{frac:.5,alt:20},clamp:x=>Math.max(0,Math.min(1,x)),identity:'A',solar:-20,
  reduced:false,horizon:164,weather:null,units:'c',weatherReads:0,isMotionReduced:()=>s.reduced,simNow:()=>1790355600000,selectedWeather:()=>s.weather,
  weatherDecision(){s.weatherReads++;return {record:s.weather,renderCode:s.weather?.code??null};},
  skySceneIdentity:()=>s.identity,beginSkyScene(){events.push('epoch');},nowParts:()=>({h:21,mi:0,s:0}),moonGeometryObservation:()=>({fresh:true}),renderMoon(){events.push('geometry');},projectStars(){events.push('stars');},simDate:()=>new Date('2026-09-25T02:00Z'),
  $:selector=>selector==='.arc .horizon'?{getBoundingClientRect:()=>({width:325,top:s.horizon+8})}:selector==='.atmo'?{getBoundingClientRect:()=>({top:8})}:c,updateSkySurface(){events.push('surface');},
  window:{SalahNativeSkyHost:{cloudLighting:()=>({sun:{altDeg:s.solar}})},SalahMoonRuntime:{request(){events.push('initial');}}}};
 vm.createContext(s);vm.runInContext(primitives+'\n'+weatherCode+'\n'+code+'\nfunction ordinarySolar(A,c){const _REDUCED=isMotionReduced();'+ordinarySolarCode+'}\n',s);return {s,c,properties,classes,events,publication};
}
test('known celestial scene publishes independently of absent prayer data',()=>{
 const r=rig();r.s.paintCelestialWithoutTimetable();assert.deepEqual(r.events,['epoch','stars','initial','surface']);
 assert.equal(r.properties['--moongrp'],'1.000');assert.equal(r.s._skySceneKey,'A');
 assert.equal(r.classes.has('sky-pending'),false);assert.equal(r.classes.has('sky-initializing'),true,'first palette must still hydrate without a fade');
 r.s.paintCelestialWithoutTimetable();assert.equal(r.events.filter(e=>e==='epoch').length,1);
});
test('unknown observer or nonfinite Sun cannot authorize initial celestial publication',()=>{
 for(const mutate of [r=>r.s.identity=null,r=>r.s.solar=NaN]){const r=rig();mutate(r);r.s.paintCelestialWithoutTimetable();assert.deepEqual(r.events,[]);assert.ok(r.classes.has('sky-pending'));}
});
test('a known daytime scene publishes its Sun body before the timetable arrives',()=>{
 const r=rig();r.s.solar=60;r.s.paintCelestialWithoutTimetable();
 assert.equal(r.properties['--sunbodyamt'],'1.000','the exposed daytime scene must already contain the radiant body');
 assert.equal(r.properties['--sunamt'],'1.000');
 assert.equal(r.properties['--sunlift'],'40.0px');
 assert.equal(r.properties['--sunx2'],'20.0px');
 assert.equal(r.classes.has('sky-pending'),false);
 assert.ok(r.publication.indexOf('--sunbodyamt')<r.publication.indexOf('sky-pending'),'solar publication precedes the existing visibility handoff');
 assert.equal(r.s.weatherReads,1,'one admitted native weather snapshot supplies the first body');
});
test('the timetable-independent path withdraws a previous daytime Sun at night',()=>{
 const r=rig();r.s.solar=60;r.s.paintCelestialWithoutTimetable();r.s.solar=-20;r.s.paintCelestialWithoutTimetable();
 assert.equal(r.properties['--sunamt'],'0.000');assert.equal(r.properties['--sunbodyamt'],'0.000');assert.equal(r.properties['--moongrp'],'1.000');
});
for(const row of solarPreservation.cases)test('preserves ordinary native solar output '+row.name,()=>{
 const r=rig(),input=row.input;r.s.solar=input.solarElevationDeg;r.s.weather=input.record;r.s.horizon=input.horizon;r.s.reduced=input.reduced;
 const driver=r.s.wxDrivers(input.record),radiometry=r.s.nativeSolarRadiometry(input.solarElevationDeg,driver,input.cls);
 assert.deepEqual(JSON.parse(JSON.stringify(driver)),row.expected.driver);
 assert.deepEqual(JSON.parse(JSON.stringify(radiometry)),row.expected.radiometry);
 r.s.paintCelestialWithoutTimetable();
 const first=Object.fromEntries(Object.entries(r.properties).filter(([name])=>name.startsWith('--sun')));
 assert.deepEqual(first,row.expected.properties,'actual first celestial publisher preserves the established solar sink');
 const ordinary={};r.s.ordinarySolar({...radiometry,solarElevationDeg:input.solarElevationDeg,heat:driver.heat},
  {classList:{contains:()=>false},style:{setProperty:(k,v)=>ordinary[k]=v,removeProperty:k=>delete ordinary[k]}});
 assert.deepEqual(ordinary,row.expected.properties,'actual ordinary paint call uses the same preserved sink');
});
test('initial lunar body and moonlight keep the ordinary physical permission expressions',()=>{
 const r=rig();for(const fraction of [0,.01,.08,.5,.92,1])for(const altitude of [-10,0,20])for(const sun of [-20,-6,0,50]){
  r.s.moonSky={frac:fraction,alt:altitude};const a=r.s.lunarPresentation(sun),clamp=r.s.clamp,darkness=clamp(-(sun+3)/9),up=clamp((altitude+2)/6),object=up*darkness*clamp((fraction-.02)/.05);
  assert.equal(a.moonShow,clamp(darkness*1.8));assert.equal(a.moonlight,object*(.35+.65*fraction));
  if(altitude< -2||fraction<=.02||sun>= -3)assert.equal(a.moonlight,0);
 }
 r.s.solar=30;r.s.paintCelestialWithoutTimetable();assert.equal(r.properties['--moongrp'],'0.000');
});
