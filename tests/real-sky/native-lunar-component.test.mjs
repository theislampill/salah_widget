import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as display from '../../real-sky/native-preview.mjs';
import {physicalSkyState} from '../../real-sky/core/src/sky-state.mjs';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {NativeSkyEngine} from '../../real-sky/native-engine.mjs';

// Compare the actual lunar-only consumer with the existing complete physical
// decomposition, using exact sampled nodes/flux and every original output byte.
const bytes=a=>Buffer.from(a.buffer,a.byteOffset,a.byteLength);
for(const stamp of ['2026-09-25T02:00:00Z','2026-09-18T07:00:00Z','2026-09-25T10:00:00Z'])test('lunar-only decomposition retains complete-model field: '+stamp,()=>{
 const s={utcMs:Date.parse(stamp),lat:28.5383,lon:-81.3792,heightM:0,generation:3,sceneIdentity:'exact-lunar-component',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:35,code:2,temp:28},units:'c',lp:0,timeScale:1};
 const job=nativeJob(s,true),state=physicalSkyState(job.observer),view=job.options.view;
 const full=display.nativeAtmosphereFields(state,job.options.atmosphere,view,job.options.diffuse.residualNight,41,67);
 assert.equal(typeof display.nativeLunarAtmosphereField,'function');
 const lunar=display.nativeLunarAtmosphereField(state,job.options.atmosphere,view,job.options.diffuse.residualNight,41,67);
 assert(bytes(lunar).equals(bytes(full.lunarBackgroundLinear)));
 assert.equal(lunar.length,325*530*3);
 if(state.moon.altDeg>0)assert(lunar.some(v=>v>0));else assert(lunar.every(v=>v===0));
 const wrongGrid=display.nativeLunarAtmosphereField(state,job.options.atmosphere,view,job.options.diffuse.residualNight,24,40);
 if(state.moon.altDeg>0)assert(!bytes(lunar).equals(bytes(wrongGrid)),'different sampled nodes must not masquerade as exact decomposition');
});

// Exercise the authored admission body at the model's actual solar-source
// boundary. Synthetic positive star/diffuse terms distinguish accidental loss;
// catalogue/material qualification is covered by the separate native evidence.
const hostSource=fs.readFileSync(new URL('../../real-sky/native-host.mjs',import.meta.url),'utf8');
const accept=hostSource.slice(hostSource.indexOf(' function accept('),hostSource.indexOf('\n function failure('));
for(const sunAltitude of [-20.0001,-20,-19.9999])test('actual refined admission preserves fields across solar-zero boundary: '+sunAltitude,async()=>{
 const snapshot={utcMs:Date.parse('2026-09-25T02:00:00Z'),lat:28.5383,lon:-81.3792,heightM:0,generation:3,sceneIdentity:'admission-boundary',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:35,code:2,temp:28},units:'c',lp:0,timeScale:1};
 const request=nativeJob(snapshot,true),physical=physicalSkyState(request.observer),state={...physical,sun:{...physical.sun,altDeg:sunAltitude}},view=request.options.view;
 const all=display.nativeAtmosphereFields(state,request.options.atmosphere,view,request.options.diffuse.residualNight,41,67),source=all.background;
 const stellar=Float64Array.from(source,(_,i)=>i%79===0?.001:0),diffuse=Float64Array.from(source,(_,i)=>(i%3+1)/100000);
 const raster={width:325,height:530,linear:Float64Array.from(source,(v,i)=>v+stellar[i]+diffuse[i]),backgroundLinear:Float64Array.from(source,(v,i)=>v+diffuse[i]),skyBackgroundLinear:source,stellarLinear:stellar,diffuseLinear:diffuse,physicalState:state,atmosphere:request.options.atmosphere,effectiveExposure:24/(1+24*all.mean/.5),nominalExposure:24};
 const raw=Object.fromEntries(Object.entries(raster).filter(([,v])=>ArrayBuffer.isView(v)).map(([k,v])=>[k,Buffer.from(bytes(v))]));
 const expected=display.nativeSkyPresentation({...raster,solarAerosolLinear:all.solarAerosolLinear,solarBackgroundLinear:all.solarBackgroundLinear,lunarBackgroundLinear:all.lunarBackgroundLinear,twilightDisplay:all.twilightDisplay},view);
 // Drive the real worker-side owner before UI admission. Only the physical
 // bridge is substituted to hit both sides of the exact solar boundary.
 const workerResult=await NativeSkyEngine.prototype.render.call({pack:{},loaded:true,
  bridge:{render:()=>({status:'ready',raster})},
  store:{catalogue:{id:'boundary-fixture',stars:[]},manifest:{catalogue:{sha256:'boundary-fixture'}}}},request);
 assert.equal(workerResult.raster.nativeLunarDisplayPrepared,sunAltitude<-20?true:undefined);
 const calls={lunar:0,full:0},context={frame:null,job:null,snapshot:()=>snapshot,lifecycle:{current:()=>true},status:{rejections:0,renders:0},physical:true,host:{capture:()=>({})},compose(){},publish(){},nativeSkyPresentation:display.nativeSkyPresentation,
  nativeLunarNightPresentation(...args){calls.lunar++;return display.nativeLunarNightPresentation(...args);},nativeAtmosphereFields(...args){calls.full++;return display.nativeAtmosphereFields(...args);},result:workerResult,request};
 vm.createContext(context);vm.runInContext(accept+'\naccept(result,1,request);',context);const out=context.frame.raster;
 assert.deepEqual(calls,sunAltitude<-20?{lunar:0,full:0}:{lunar:0,full:1});
 for(const key of ['linear','backgroundLinear','skyBackgroundLinear','physicalSkyBackgroundLinear','lunarBackgroundLinear','lunarNightDisplayLinear','stellarLinear','diffuseLinear'])assert(bytes(out[key]).equals(bytes(expected[key])),key);
 for(const [key,b]of Object.entries(raw))assert(bytes(raster[key]).equals(b),'raw mutation: '+key);
 assert.equal(out.stellarLinear,stellar);assert.equal(out.diffuseLinear,diffuse);
 if(sunAltitude<-20){
  assert(all.solarAerosolLinear.every(v=>v===0)&&all.solarBackgroundLinear.every(v=>v===0));assert.equal(all.twilightDisplay.weight,0);
  for(const key of ['solarAerosolLinear','solarBackgroundLinear','twilightDisplay'])assert.equal(out[key],undefined);
 }else assert(bytes(out.solarBackgroundLinear).equals(bytes(all.solarBackgroundLinear)));
 // A stale result must never enter either physical sampling path.
 context.lifecycle.current=()=>false;vm.runInContext('accept(result,2,request);',context);assert.equal(context.status.rejections,1);assert.equal(calls.lunar+calls.full,sunAltitude<-20?0:1);
});
