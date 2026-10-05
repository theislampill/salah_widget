import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const modulePath=new URL('../../real-sky/native-contract.mjs',import.meta.url);
let mod;try{mod=await import(modulePath);}catch{}
const state={utcMs:Date.parse('2026-09-07T20:30:00Z'),lat:24.47,lon:39.61,heightM:610,generation:2,sceneIdentity:'accepted-native-A',weather:null,lp:0,reducedMotion:true,camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0}};
test('native contract is implemented',()=>assert.ok(mod,'Native adapter missing'));
test('accepted UTC and generation are retained exactly',()=>{assert.ok(mod);const j=mod.nativeJob(state,false);assert.equal(j.observer.utcMs,state.utcMs);assert.equal(j.observer.latDeg,24.47);assert.equal(j.native.generation,2);assert.equal(j.options.view.type,'camera');assert.equal(j.options.diffuse.enabled,false);});
test('invalid/missing observer or scene is not coerced to a valid sky',()=>{assert.ok(mod);for(const change of [{lat:null},{lon:NaN},{utcMs:NaN},{sceneIdentity:null},{generation:-1},{lat:91},{heightM:Infinity}])assert.throws(()=>mod.nativeJob({...state,...change},false));});
test('weather and camera change invalidate a target even at the same coordinates',()=>{assert.ok(mod);assert.notEqual(mod.nativeIdentity(state),mod.nativeIdentity({...state,weather:{cloud:50}}));assert.notEqual(mod.nativeIdentity(state),mod.nativeIdentity({...state,camera:{...state.camera,azDeg:0}}));});
test('new target rejects a late prior-generation result',()=>{assert.ok(mod);assert.equal(mod.nativeResultCurrent(mod.nativeJob(state,false),{...state,generation:3}),false);assert.equal(mod.nativeResultCurrent(mod.nativeJob(state,false),state),true);});
test('diffuse mode replaces natural night budget and preserves source estimates',()=>{assert.ok(mod);const j=mod.nativeJob(state,true);assert.equal(j.options.diffuse.residualNight.includesRegisteredStarlight,false);assert.equal(j.options.diffuse.allowEstimates,true);assert.equal(j.options.atmosphere.cloudTransmission,1);});
test('actual widget no longer constructs the fictitious stellar population',()=>{const s=fs.readFileSync(new URL('../../index.html',import.meta.url),'utf8');assert.ok(!s.includes('const N=420;'));assert.ok(!s.includes('for(let i=0;i<150;i++)'));assert.ok(s.includes('SalahNativeSkyHost'));assert.ok(s.includes('real-sky/native-sky.js'));});
import {normaliseAtmosphere} from '../../real-sky/core/src/atmosphere.mjs';
test('native visibility assumption actually reaches the CP7 aerosol owner',()=>{const a=normaliseAtmosphere(mod.nativeJob({...state,weather:{vis:2000}},true).options.atmosphere);assert.ok(a.aerosolTau550>.30);});
test('calendar transform includes native CSS scaling and card placement',()=>{assert.equal(typeof mod.nativeDiscMask,'function');const a=mod.nativeDiscMask(10,10,{left:100,top:50,width:20,height:20},{a:2,b:0,c:0,d:2,e:110,f:60},2);assert.equal(a[5*10+5],0);assert.equal(a[0],1);assert.equal(a[9*10+9],1);});
test('calendar cutout changes direct light only, not sky or exposure',()=>{const r={width:1,height:1,linear:new Float64Array([9,9,9]),skyBackgroundLinear:new Float64Array([2,2,2]),stellarLinear:new Float64Array([3,3,3]),diffusePhysicalLinear:new Float64Array([4,4,4]),effectiveExposure:7};assert.deepEqual(Array.from(mod.nativeCalendarComposite(r,new Float64Array([0]))),[2,2,2]);assert.equal(r.effectiveExposure,7);});
test('estimate-support selection is a distinct render identity',()=>assert.notEqual(mod.nativeIdentity(state),mod.nativeIdentity({...state,allowEstimates:false})));
