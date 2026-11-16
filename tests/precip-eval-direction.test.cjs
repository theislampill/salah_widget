'use strict';
// Precipitation evaluation (research only): wind x camera direction table for rain streaks, from the independent
// verification of the precipitation advisory (2026-11-15, section 5). Exercises tools/qa/precip_models_geom.js, the
// geometry used by the evaluation overlay; it pins NO product behaviour except documenting (as facts) that the
// product's cloud drift ignores the camera azimuth and that its rain slant sign is opposite to its cloud drift.
const test=require('node:test'),assert=require('node:assert/strict');
const G=require('../tools/qa/precip_models_geom.js');
const cam=az=>({az,alt:45,fov:90,W:325,H:530});
const C=[162.5,265],S=5,VT=4;
const lean=(az,from)=>G.screenLean(cam(az),C[0],C[1],from,S,VT);
test('az 180 (default, looking south): W wind leans lower end LEFT, E wind RIGHT, about 60.5 deg at centre',()=>{
  const w=lean(180,270),e=lean(180,90);
  assert(w.deg<0&&Math.abs(Math.abs(w.deg)-60.5)<0.6,`W ${w.deg}`);assert(e.deg>0&&Math.abs(e.deg-60.5)<0.6,`E ${e.deg}`);
  assert(Math.abs(w.deg+e.deg)<1e-9,'opposing winds mirror');
});
test('az 180: N wind (away from viewer) has no lean and faster flow; S wind (toward viewer) no lean, flow rises when S > vt cot e',()=>{
  const calm=G.screenLean(cam(180),C[0],C[1],0,0,VT),n=lean(180,0),s=lean(180,180);
  assert(Math.abs(n.deg)<1e-6);assert(n.speed/calm.speed>2.1&&n.speed/calm.speed<2.3,`ratio ${n.speed/calm.speed}`);
  assert(Math.abs(s.vx)<1e-9);assert(s.vy<0,'S wind 5 m/s > 4 m/s: drops rise on screen');
});
test('az 90 (looking east): N wind -> RIGHT, S wind -> LEFT, W wind away (no lean), E wind toward (rising)',()=>{
  const n=lean(90,0),s=lean(90,180),w=lean(90,270),e=lean(90,90);
  assert(n.deg>0&&Math.abs(n.deg-60.5)<0.6);assert(s.deg<0&&Math.abs(s.deg+60.5)<0.6);
  assert(Math.abs(w.vx)<1e-9&&w.vy>0);assert(Math.abs(e.vx)<1e-9&&e.vy<0);
});
test('rotating the wind by 180 deg flips the lean at every camera azimuth',()=>{
  for(const az of [0,45,90,135,180,225,270,315])for(const from of [0,30,77,120,200,270,333]){
    const a=lean(az,from),b=lean(az,(from+180)%360);if(Math.abs(a.vx)>1e-6)assert.equal(Math.sign(a.vx),-Math.sign(b.vx),`${az} ${from}`);}
});
test('calm air fans from the top-centre edge: centre column vertical, off-centre columns lean outward',()=>{
  const c0=G.screenLean(cam(180),162.5,165,0,0,VT),l=G.screenLean(cam(180),62.5,165,0,0,VT),r=G.screenLean(cam(180),262.5,165,0,0,VT);
  assert(Math.abs(c0.deg)<1e-9);assert(l.deg<0&&r.deg>0&&Math.abs(l.deg+r.deg)<1e-9);assert(Math.abs(r.deg-31)<1.5,`fan ${r.deg}`);
});
test('documented product facts (not assertions about correct behaviour): rain slant sign is opposite to cloud drift; cloud drift ignores azimuth',()=>{
  for(const from of [270,90,240,300])assert.equal(G.productRainSlantSign(from),-G.productCloudDriftSign(from));
  // at az 180 the geometric lean agrees with the product's cloud drift
  for(const from of [270,90])assert.equal(Math.sign(lean(180,from).vx),G.productCloudDriftSign(from));
  // at az 90 a W wind has no cross-view component, yet the product's clouds still drift (fixed convention)
  assert.equal(Math.abs(lean(90,270).vx)<1e-9,true);assert.notEqual(G.productCloudDriftSign(270),0);
});
