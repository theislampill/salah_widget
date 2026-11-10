import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {physicalSkyState} from '../../real-sky/core/src/sky-state.mjs';
import {nativeAtmosphereFields,nativeLunarAtmosphereField,nativeSkyPresentation,nativeLunarNightPresentation} from '../../real-sky/native-preview.mjs';
const base={utcMs:Date.parse('2026-09-25T02:00:00Z'),lat:28.5383,lon:-81.3792,heightM:0,generation:2,sceneIdentity:'lunar-cache-controls',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:0,code:0,temp:28},units:'c',lp:0,timeScale:1};
const bytes=v=>Buffer.from(v.buffer,v.byteOffset,v.byteLength);
function fixture(change={},grid=[41,67]){
 const request=nativeJob({...base,...change},true),state=physicalSkyState(request.observer),view=request.options.view;
 const fields=nativeAtmosphereFields(state,request.options.atmosphere,view,request.options.diffuse.residualNight,...grid),source=fields.background;
 return {raster:{width:325,height:530,linear:source,backgroundLinear:source,skyBackgroundLinear:source,physicalState:state,atmosphere:request.options.atmosphere,effectiveExposure:24/(1+24*fields.mean/.5)},view,residual:request.options.diffuse.residualNight,grid};
}
function compare(f){
 const raw=Buffer.from(bytes(f.raster.linear));
 const moon=nativeLunarAtmosphereField(f.raster.physicalState,f.raster.atmosphere,f.view,f.residual,...f.grid);
 const expected=nativeSkyPresentation({...f.raster,lunarBackgroundLinear:moon},f.view),actual=nativeLunarNightPresentation(f.raster,f.view,f.residual,...f.grid);
 assert.deepEqual(Object.keys(actual).sort(),Object.keys(expected).sort());
 for(const key of Object.keys(expected))if(ArrayBuffer.isView(expected[key]))assert(bytes(actual[key]).equals(bytes(expected[key])),key);else assert.deepEqual(actual[key],expected[key],key);
 assert(bytes(f.raster.linear).equals(raw));
 if(actual.lunarDisplayPresentation){assert.notEqual(actual.linear,f.raster.linear);assert.equal(actual.physicalSkyBackgroundLinear,f.raster.skyBackgroundLinear);assert.notEqual(actual.lunarBackgroundLinear.buffer,actual.lunarNightDisplayLinear.buffer);}
 return actual;
}
test('fused admission retains exact fields through geometry keys, eviction and current physical changes',()=>{
 const first=fixture(),initial=compare(first);
 compare(fixture({utcMs:Date.parse('2026-09-25T03:00:00Z')}));
 compare(fixture({utcMs:Date.parse('2026-09-18T07:00:00Z')}));
 compare(fixture({weather:{vis:6000,cloud:65,code:63,temp:20}}));
 for(const camera of [{...base.camera,azDeg:195},{...base.camera,altDeg:0},{...base.camera,fovYDeg:80},{...base.camera,rollDeg:15}])compare(fixture({camera}));
 compare(fixture({},[24,40]));compare(fixture({},[68,68]));
 const returned=compare(first);assert(bytes(returned.linear).equals(bytes(initial.linear)));
 compare({...first,raster:{...first.raster,effectiveExposure:1e-20}});
});
test('fused admission refuses invalid geometry, raw fields and solar domain',()=>{
 const f=fixture(),invoke=(r=f.raster,v=f.view,grid=f.grid)=>nativeLunarNightPresentation(r,v,f.residual,...grid);
 assert.throws(()=>invoke({...f.raster,physicalState:{...f.raster.physicalState,sun:{...f.raster.physicalState.sun,altDeg:-20}}}),RangeError);
 assert.throws(()=>invoke({...f.raster,solarBackgroundLinear:new Float64Array([1])}),RangeError);
 const raw=f.raster.skyBackgroundLinear.slice();raw[100]=NaN;
 assert.throws(()=>invoke({...f.raster,skyBackgroundLinear:raw}),RangeError);
 assert.throws(()=>invoke({...f.raster,effectiveExposure:Infinity}),RangeError);
 assert.throws(()=>invoke(f.raster,{...f.view,fovYDeg:NaN}),RangeError);
 assert.throws(()=>invoke(f.raster,{...f.view,width:326}),RangeError);
 for(const grid of [[69,67],[41.5,67]])assert.throws(()=>invoke(f.raster,f.view,grid),RangeError);
});
