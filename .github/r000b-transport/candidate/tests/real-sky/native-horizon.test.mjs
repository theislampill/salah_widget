import test from 'node:test';
import assert from 'node:assert/strict';
import {skyProjection,renderPhysicalSky} from '../../real-sky/core/src/physical-sky-renderer.mjs';
import {skyProjection as originalProjection} from '../../vendor/real-sky/src/physical-sky-renderer.mjs';

const view={type:'camera',width:325,height:530,azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0};
test('default bottom horizon follows the authoritative inverse projection',()=>{
 const p=skyProjection(view),old=originalProjection(view);
 assert.equal(old.above(162.5,530),false,'retained donor reproduces the reported centre boundary defect');
 for(const x of [0,31.7,162.5,293.3,325]){
  assert.equal(p.unproject(x,530).altDeg,0);
  assert.equal(p.above(x,530),true,'horizon grid nodes must not become zero radiance');
  assert.equal(p.above(x,530-1e-8),true);
  assert.equal(p.above(x,530+1e-8),false,'no below-horizon admission tolerance');
 }
});
test('camera predicate agrees with inverse projection across rotations and boundary rays',()=>{
 for(const azDeg of [0,90,180,275])for(const altDeg of [0,35,45,80])for(const rollDeg of [-30,0,90]){
  const p=skyProjection({...view,azDeg,altDeg,rollDeg});
  for(const x of [0,162.5,325])for(const y of [0,265,530-1e-8,530,530+1e-8])
   assert.equal(p.above(x,y),p.unproject(x,y).altDeg>=0,JSON.stringify({azDeg,altDeg,rollDeg,x,y}));
 }
});
test('bright sky retains radiance to the bottom pixel without altering projection or exposure policy',()=>{
 const observer={utcMs:Date.parse('2026-09-07T09:30:00Z'),latDeg:24.47,lonDeg:39.61,heightM:0};
 const r=renderPhysicalSky([],{observer,view,diffuse:false,backgroundStepCss:8});
 const value=y=>r.backgroundLinear[3*(y*325+162)];
 assert.ok(value(529)>.8*value(522),JSON.stringify({y522:value(522),y529:value(529)}));
 assert.ok(Number.isFinite(r.effectiveExposure)&&r.effectiveExposure>0);
});
