import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const html=fs.readFileSync(new URL('../../src/native/index.html',import.meta.url),'utf8');
const code=html.slice(html.indexOf('function nativeLunarPresentation('),html.indexOf('function atmosphere('));
function rig(){
 const properties={},classes=new Set(['sky-pending','sky-initializing']),events=[];
 const c={style:{setProperty:(k,v)=>properties[k]=v},classList:{remove:(...names)=>names.forEach(n=>classes.delete(n))}};
 const s={_skySceneKey:null,_skyMoonPresence:0,_pbrFailed:false,moonSky:{frac:.5,alt:20},clamp:x=>Math.max(0,Math.min(1,x)),identity:'A',solar:-20,
  skySceneIdentity:()=>s.identity,beginSkyScene(){events.push('epoch');},nowParts:()=>({h:21,mi:0,s:0}),moonGeometryObservation:()=>({fresh:true}),renderMoon(){events.push('geometry');},projectStars(){events.push('stars');},simDate:()=>new Date('2026-09-25T02:00Z'),$:()=>c,updateSkySurface(){events.push('surface');},
  window:{SalahNativeSkyHost:{cloudLighting:()=>({sun:{altDeg:s.solar}})},SalahMoonRuntime:{request(){events.push('initial');}}}};
 vm.createContext(s);vm.runInContext(code,s);return {s,properties,classes,events};
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
test('initial lunar body and moonlight keep the ordinary physical permission expressions',()=>{
 const r=rig();for(const fraction of [0,.01,.08,.5,.92,1])for(const altitude of [-10,0,20])for(const sun of [-20,-6,0,50]){
  r.s.moonSky={frac:fraction,alt:altitude};const a=r.s.lunarPresentation(sun),clamp=r.s.clamp,darkness=clamp(-(sun+3)/9),up=clamp((altitude+2)/6),object=up*darkness*clamp((fraction-.02)/.05);
  assert.equal(a.moonShow,clamp(darkness*1.8));assert.equal(a.moonlight,object*(.35+.65*fraction));
  if(altitude< -2||fraction<=.02||sun>= -3)assert.equal(a.moonlight,0);
 }
 r.s.solar=30;r.s.paintCelestialWithoutTimetable();assert.equal(r.properties['--moongrp'],'0.000');
});
