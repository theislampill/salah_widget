'use strict';
// R0033 (issue 100) §11 item 11: single-gate negative controls for native moonlight.
// The authored native moon object (nativeLunarPresentation) withholds physical
// moonlight through two independent gates: G-alt (moonUp, Moon below the horizon)
// and G-new (phaseVis, near-new Moon). Smoke case 21 catches removing BOTH; this
// instrument catches removing EITHER alone. It loads the whole generated native
// runtime (root index.html, built from src/native/index.html) in the R001D VM
// harness, with a stub Moon runtime that presents a current surface, so the
// surface gate is open and only the gate under test can withhold light. Each
// scene isolates ONE gate: a well-lit phase below the horizon (only G-alt
// applies) and a near-new Moon high in the sky (only G-new applies); a lit,
// above-horizon positive control keeps the test from passing vacuously.
// Call/state behaviour only: no pixels, compositing or browser proof.
const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path');
const {load,root}=require('./r001d-harness.cjs');
const sourcePath=process.env.SALAH_R0033_ENTRY||path.join(root,'index.html');
const CONSUMERS=['illumination','beam','cloudLight','localStarWash','localGlow','halo','corona','paraselenae'];
const css=(h,k,sel='.c')=>+h.select(sel).style.getPropertyValue(k);

// A registered runtime that presents a current surface (the R001D / R33-16 stub pattern).
function presenting(h){
 h.run(`{ const cv=document.createElement('canvas');
  window.SalahMoonRuntime={get presentable(){return true;},surface(){return cv;},request(){return true;},
   get state(){return {status:'ready',visibleSource:'refined-terrain',quality:'empirical-adaptive',accepted:{identity:'stub'}};},
   get detailEnabled(){return false;},invalidate(){},finishInitialDocument(){},presentationUp:1,disposed:false}; }
  document.querySelector('.mphoto').setAttribute('href','data:image/png;base64,STUB');`);
 return h;
}
const BASE='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&seed=1&simTime=22:00&simWax=1&simMoonH=42';
function scene(moon,alt){
 const h=presenting(load({sourcePath,hash:`${BASE}&simMoon=${moon}&simMoonAlt=${alt}`}));
 h.run('render();render();');
 return {h,light:h.run('qaState().moonTruth.lunarLight'),direct:h.run('lunarPresentation(-40)'),
  beam:css(h,'--moonbeam'),opacity:h.run('qaState().moonTruth.moonlightOpacity'),
  A:h.run('(()=>{const A=atmosphere(model());return {wash:A.moonLocalWash,intensity:A.moonlightIntensity};})()')};
}
function assertDark(s,reason){
 assert.ok(s.light,'a completed moon paint published its light observation');
 assert.equal(s.light.eligible,false,'lunarLight.eligible');assert.equal(s.light.eligibility,0,'lunarLight.eligibility');
 assert.equal(s.light.reason,reason,'lunarLight.reason');
 for(const key of CONSUMERS)assert.equal(s.light[key],0,'lunarLight.'+key);
 assert.equal(s.direct.moonObject,0,'moonObject');assert.equal(s.direct.moonlight,0,'moonlight');
 assert.equal(s.direct.moonLightEligible,false,'moonLightEligible');
 assert.equal(s.beam,0,'--moonbeam');assert.equal(s.opacity,0,'qaState().moonTruth.moonlightOpacity');
 assert.equal(s.A.wash,0,'atmosphere moonLocalWash');assert.equal(s.A.intensity,0,'atmosphere moonlightIntensity');
 assert.equal(css(s.h,'--moongrp'),1,'the opaque calendar disc is kept (presence never depends on light)');
}

test('R33-NC0 positive control: a lit (0.6), above-horizon (40 deg) Moon with a presented surface casts moonlight',()=>{
 const s=scene(0.6,40);
 assert.equal(s.light.eligible,true);assert.equal(s.light.reason,'eligible');assert.ok(s.light.eligibility>0);
 assert.ok(s.direct.moonlight>0,'moonlight > 0');assert.ok(s.beam>0,'--moonbeam > 0');assert.ok(s.opacity>0,'moonlightOpacity > 0');
 assert.ok(s.light.cloudLight>0&&s.light.localStarWash>0);
});

test('R33-NC1 G-alt control: a well-lit (0.6) Moon at -20 deg casts no moonlight (reason below-horizon)',()=>{
 const s=scene(0.6,-20);
 assert.ok(s.direct.phaseVis===1,'scene isolates G-alt: the phase gate is fully open');
 assertDark(s,'below-horizon');
});

test('R33-NC2 G-new control: a near-new (0.01) Moon at +40 deg casts no moonlight (reason near-new)',()=>{
 const s=scene(0.01,40);
 assert.ok(s.direct.moonUp===1,'scene isolates G-new: the horizon gate is fully open');
 assertDark(s,'near-new');
});
