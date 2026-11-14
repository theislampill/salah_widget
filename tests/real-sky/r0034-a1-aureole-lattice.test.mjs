// R0034-A1: the daytime display decomposition must sample the removed solar aureole on the SAME lattice as the
// worker background it is removed from. Executes the authored host's actual accept() body (real-sky/native-host.mjs)
// in a VM with the real nativeAtmosphereFields / nativeSkyPresentation; only lifecycle, capture and publication are
// replaced by owned stubs. RED on origin/main 516d8cc8 (daytime uses [24,40]); GREEN when every solar altitude uses
// the worker lattice [ceil(325/step), ceil(530/step)].
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {renderPhysicalSky} from '../../real-sky/core/src/physical-sky-renderer.mjs';
import {encodeNativeFrame} from '../../real-sky/native-encoding.mjs';
import {nativeSkyPresentation,nativeAtmosphereFields} from '../../real-sky/native-preview.mjs';
import {luminanceToSurfaceMagnitude} from '../../real-sky/core/src/sky-background.mjs';

const source=fs.readFileSync(new URL('../../real-sky/native-host.mjs',import.meta.url),'utf8');
const acceptBody=source.slice(source.indexOf(' function accept('),source.indexOf('\n function failure('));
assert.ok(acceptBody.startsWith(' function accept(')&&acceptBody.length>200,'accept() body located');

// Run the authored accept() once. `fields` lets a test observe the lattice actually requested.
function runAccept(result,request,{fields=nativeAtmosphereFields,present=nativeSkyPresentation,anchor={x:20.12,y:49.32,presence:1}}={}){
 const calls=[];
 const s={snapshot:()=>({}),lifecycle:{current:()=>true},status:{rejections:0,renders:0,errors:[]},physical:true,
  host:{capture:()=>({solarAnchor:anchor})},frame:null,job:null,compose(){},publish(){},
  nativeAtmosphereFields:(...a)=>{calls.push(a.slice(4));return fields(...a);},nativeSkyPresentation:present,Error,Number,Math};
 vm.createContext(s);vm.runInContext(acceptBody+'\naccept(__result,1,__request);',Object.assign(s,{__result:result,__request:request}));
 return {frame:s.frame,calls};
}
const fakeRaster=altDeg=>({physicalState:{sun:{altDeg,azDeg:150}},atmosphere:{},nativeLunarDisplayPrepared:true,width:325,height:530});
const fakeRequest=step=>({options:{backgroundStepCss:step,view:{type:'camera',width:325,height:530,azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},diffuse:{residualNight:null},atmosphere:{aerosolTau550:.06}},observer:{},native:{}});

test('every non-deep-night solar altitude decomposes on the worker background lattice (step 8 and step 6)',()=>{
 for(const step of [8,6]){
  const expected=[Math.ceil(325/step),Math.ceil(530/step)];
  for(const alt of [60,36.8,20,14.5,10.01,10,9.99,5,0,-2.99,-3,-3.01,-10,-19.99]){
   const {calls}=runAccept({status:'ready',raster:fakeRaster(alt)},fakeRequest(step),{fields:()=>({}),present:r=>r});
   assert.equal(calls.length,1,`alt ${alt}: one decomposition`);
   assert.deepEqual(calls[0],expected,`alt ${alt}, step ${step}: decomposition lattice must equal the worker lattice`);
  }
 }
});

test('deep night (below -20 degrees) still uses the worker-prepared lunar display and no host decomposition',()=>{
 const {calls}=runAccept({status:'ready',raster:fakeRaster(-25)},fakeRequest(8),{fields:()=>({}),present:r=>r});
 assert.equal(calls.length,0);
});

// Pixel witness at the owner-reported scene: Central Florida, 2026-11-14 10:26 America/New_York, default camera.
// The physical Sun projects to card (~41, 282). Fingerprint: luminance column profile over card rows 284-290 of the
// encoded display, ridge(x) = P(x) - (P(x-9) + P(x+9)) / 2, maximum |ridge| over card x 30..140.
function ownerScene(utc='2026-11-14T15:26:00Z',vis=20000){
 const s={utcMs:Date.parse(utc),lat:28.54,lon:-81.38,heightM:0,generation:2,sceneIdentity:'r0034-a1',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis,cloud:100,code:3,temp:51},units:'f',lp:0};
 const j=nativeJob(s,true);
 const raw=renderPhysicalSky([],{...j.options,observer:j.observer,diffuse:null,atmosphere:{...j.options.atmosphere,nightZenithVMag:luminanceToSurfaceMagnitude(.00014)}});
 return {request:j,raw};
}
export function ridge(bytes){
 const P=x=>{let t=0;for(let y=284;y<=290;y++){const i=4*(y*325+x);t+=.2126*bytes[i]+.7152*bytes[i+1]+.0722*bytes[i+2];}return t/7;};
 let m=0;for(let x=30;x<=140;x++)m=Math.max(m,Math.abs(P(x)-(P(x-9)+P(x+9))/2));return m;
}
test('owner scene: no lattice crosshatch near the physical Sun in the accepted refined display',()=>{
 const {request,raw}=ownerScene();
 assert.ok(raw.physicalState.sun.altDeg>30,'Sun high and in view');
 const {frame}=runAccept({status:'ready',raster:raw},request);
 const r=ridge(encodeNativeFrame(frame.raster.linear,frame.raster.effectiveExposure));
 assert.ok(r<=1.5,`ridge ${r.toFixed(2)} levels exceeds 1.5 (origin/main 516d8cc8 measured 10.11)`);
});
