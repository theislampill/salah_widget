import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {physicalSkyState} from '../../real-sky/core/src/sky-state.mjs';
import {nativeAtmosphereFields,nativeSkyPresentation,renderNativeBackgroundPreview} from '../../real-sky/native-preview.mjs';

const snapshot=utc=>({utcMs:Date.parse(utc),lat:28.5383,lon:-81.3792,heightM:0,generation:2,sceneIdentity:'R0022-Orlando',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:0,code:0,temp:28},units:'c',lp:0});
const bytes=v=>Buffer.from(v.buffer,v.byteOffset,v.byteLength);
function physical(utc,change={}){
 const job=nativeJob(snapshot(utc),true),state=physicalSkyState(job.observer),view={...job.options.view,width:65,height:106};
 const fields=nativeAtmosphereFields(state,{...job.options.atmosphere,...change},view,job.options.diffuse.residualNight,12,20);
 // Match the real fast-preview per-reference-pixel flux normalization.
 for(const a of [fields.background,fields.solarAerosolLinear,fields.solarBackgroundLinear,fields.lunarBackgroundLinear])for(let i=0;i<a.length;i++)a[i]/=25;
 const E=24/(1+24*(fields.mean/25)/.5);
 const raster={width:65,height:106,linear:fields.background,backgroundLinear:fields.background,skyBackgroundLinear:fields.background,solarAerosolLinear:fields.solarAerosolLinear,solarBackgroundLinear:fields.solarBackgroundLinear,lunarBackgroundLinear:fields.lunarBackgroundLinear,twilightDisplay:fields.twilightDisplay,effectiveExposure:E,nominalExposure:24,physicalState:state,atmosphere:job.options.atmosphere};
 return {raster,view,fields};
}
function preservation(r,out,saved){
 assert.equal(out.effectiveExposure,r.effectiveExposure);
 for(const [k,b] of Object.entries(saved))assert(bytes(r[k]).equals(b),`mutated raw ${k}`);
 if(out!==r)assert.equal(out.physicalSkyBackgroundLinear,r.skyBackgroundLinear);
 if(out!==r){assert.notEqual(out.linear.buffer,r.linear.buffer);assert.notEqual(out.skyBackgroundLinear.buffer,r.lunarBackgroundLinear.buffer);}
}

test('lunar display preserves distinct positive stellar/diffuse contributions and raw ownership',()=>{
 const {raster:r,view}=physical('2026-09-25T02:00:00Z'),n=r.linear.length;
 const stellar=Float64Array.from({length:n},(_,i)=>i%17===0?.001:0),diffuse=Float64Array.from({length:n},(_,i)=>.0002+(i%3)*.0001);
 const linear=Float64Array.from(r.linear,(v,i)=>v+stellar[i]+diffuse[i]);
 const input={...r,linear,stellarLinear:stellar,diffuseLinear:diffuse},saved=Object.fromEntries(Object.entries(input).filter(([,v])=>ArrayBuffer.isView(v)).map(([k,v])=>[k,Buffer.from(bytes(v))]));
 const out=nativeSkyPresentation(input,view);preservation(input,out,saved);
 assert.equal(out.stellarLinear,stellar);assert.equal(out.diffuseLinear,diffuse);
 for(let i=0;i<n;i++){
  assert.equal(out.linear[i],linear[i]-r.skyBackgroundLinear[i]+out.skyBackgroundLinear[i]);
  assert.equal(out.backgroundLinear[i],out.skyBackgroundLinear[i]+diffuse[i]);
 }
});
test('approved H1 acts on actual lunar atmosphere, retains every raw sample and angular order',()=>{
 const {raster:r,view}=physical('2026-09-25T02:00:00Z');
 const saved=Object.fromEntries(Object.entries(r).filter(([,v])=>ArrayBuffer.isView(v)).map(([k,v])=>[k,Buffer.from(bytes(v))]));
 const out=nativeSkyPresentation(r,view),pairs=[];
 assert.equal(out.lunarDisplayPresentation.contract,'R0022-L1-H1-K003-H020-v1');
 assert.equal(out.lunarDisplayPresentation.kneeEnergy,.003);assert.equal(out.lunarDisplayPresentation.headroomEnergy,.020);
 assert(r.physicalState.moon.altDeg>0&&r.physicalState.sun.altDeg<-18);
 preservation(r,out,saved);
 let positive=0,compressed=0,rawPeak=0,mappedPeak=0;
 for(let i=0;i<r.linear.length;i+=3){
  const l=r.lunarBackgroundLinear,Y=.2126*l[i]+.7152*l[i+1]+.0722*l[i+2],z=r.effectiveExposure*Y;
  const target=z<=.003?z:.003+.020*(z-.003)/(.020+z-.003),scale=z?target/z:1;
  if(z>0){positive++;assert(out.lunarNightDisplayLinear[i]>0,'supported broad moonlight extinguished');}
  if(z>.003)compressed++;
  if(l[i]>l[rawPeak])rawPeak=i;
  if(out.lunarNightDisplayLinear[i]>out.lunarNightDisplayLinear[mappedPeak])mappedPeak=i;
  for(let c=0;c<3;c++){
   assert(Math.abs(out.lunarNightDisplayLinear[i+c]-l[i+c]*scale)<=64*Number.EPSILON);
   assert(Math.abs(out.skyBackgroundLinear[i+c]-(r.skyBackgroundLinear[i+c]-l[i+c]+out.lunarNightDisplayLinear[i+c]))<=64*Number.EPSILON);
  }
  pairs.push([z,r.effectiveExposure*out.lunarNightDisplayLinear[i]]);
 }
 assert(positive>1000&&compressed>1000);assert.equal(rawPeak,mappedPeak);
 pairs.sort((a,b)=>a[0]-b[0]);for(let i=1;i<pairs.length;i++)assert(pairs[i][1]>=pairs[i-1][1]-64*Number.EPSILON);
 // A wrong-unit component must reach and fail the real consumer.
 assert.throws(()=>nativeSkyPresentation({...r,lunarBackgroundLinear:Float64Array.from(r.lunarBackgroundLinear,v=>v*1e12)},view),RangeError);
});
test('low-energy lunar contribution is identity; zero lunar input cannot dim another channel',()=>{
 const {raster:r,view}=physical('2026-09-25T02:00:00Z');
 const low=Float64Array.from(r.lunarBackgroundLinear,v=>v*1e-10),zero=new Float64Array(low.length);
 assert.equal(nativeSkyPresentation({...r,lunarBackgroundLinear:low},view).linear,r.linear);
 assert.equal(nativeSkyPresentation({...r,lunarBackgroundLinear:zero},view).linear,r.linear);
 const invalid=low.slice();invalid[10]=-1;assert.throws(()=>nativeSkyPresentation({...r,lunarBackgroundLinear:invalid},view),RangeError);
});
for(const stamp of ['2026-09-25T10:00:00Z','2026-09-25T10:40:00Z','2026-09-25T11:30:00Z','2026-09-25T12:00:00Z','2026-09-25T17:00:00Z'])test('actual twilight/day raw channels and no intervention above -12: '+stamp,()=>{
 const {raster:r,view}=physical(stamp),saved=Object.fromEntries(Object.entries(r).filter(([,v])=>ArrayBuffer.isView(v)).map(([k,v])=>[k,Buffer.from(bytes(v))]));
 const out=nativeSkyPresentation(r,view),baseline=nativeSkyPresentation({...r,lunarBackgroundLinear:null},view);
 preservation(r,out,saved);
 if(r.physicalState.sun.altDeg>=-12){assert(bytes(out.linear).equals(bytes(baseline.linear)));assert.equal(out.lunarDisplayPresentation,undefined);}
 else {assert(out.linear.every(v=>Number.isFinite(v)&&v>=0));}
});
test('ordinary and fast native preview both consume H1 with their actual reference-pixel flux normalization',()=>{
 const s=snapshot('2026-09-25T02:00:00Z'),ordinary=renderNativeBackgroundPreview(s),fast=renderNativeBackgroundPreview({...s,timeScale:60});
 assert.deepEqual([ordinary.raster.width,ordinary.raster.height],[325,530]);
 assert.deepEqual([fast.raster.width,fast.raster.height],[65,106]);
 for(const p of [ordinary,fast]){
  assert.equal(p.raster.lunarDisplayPresentation.contract,'R0022-L1-H1-K003-H020-v1');
  assert(p.raster.lunarBackgroundLinear.some(v=>v>0));
 }
 const actual=physical('2026-09-25T02:00:00Z');
 assert(bytes(fast.raster.lunarBackgroundLinear).equals(bytes(actual.raster.lunarBackgroundLinear)));
});
