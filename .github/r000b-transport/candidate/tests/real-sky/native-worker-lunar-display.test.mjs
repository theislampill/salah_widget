import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {NativeSkyEngine} from '../../real-sky/native-engine.mjs';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {nativeLunarNightPresentation,nativeSkyPresentation,nativeAtmosphereFields} from '../../real-sky/native-preview.mjs';
import {rasterTransferables} from '../../real-sky/core/src/reference-engine.mjs';
const root=new URL('../../vendor/real-sky/',import.meta.url),read=p=>fs.readFileSync(new URL(p,root),'utf8');
const pack={catalogueText:read('data/bright-stars.json'),manifestText:read('data/registered-starlight/runtime-manifest.json'),assetTexts:{128:read('data/registered-starlight/V-nside128.json')}};
const input={utcMs:Date.parse('2026-09-25T02:00:00Z'),lat:28.5383,lon:-81.3792,heightM:0,generation:0,sceneIdentity:'cost-night',weather:null,lp:0,timeScale:1,reducedMotion:false,camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0}};
const source=fs.readFileSync(new URL('../../real-sky/native-host.mjs',import.meta.url),'utf8');
const accept=source.slice(source.indexOf(' function accept('),source.indexOf('\n function failure('));
test('existing sky worker supplies bit-identical H1 lunar presentation and moves every output buffer',async()=>{
 const engine=new NativeSkyEngine(pack),job=nativeJob(input,true);
 await engine.store.load(job.tier,async()=>pack.assetTexts[128]);engine.loaded=true;
 const raw=engine.bridge.render(job.observer,job.options),step=job.options.backgroundStepCss;
 assert(raw.raster.physicalState.sun.altDeg<-20);
 const expected=nativeLunarNightPresentation(raw.raster,job.options.view,job.options.diffuse.residualNight,Math.ceil(325/step),Math.ceil(530/step));
 const result=await engine.render(job);assert.equal(result.raster.nativeLunarDisplayPrepared,true,'H1 work belongs to the existing worker');
 for(const key of ['linear','skyBackgroundLinear','backgroundLinear','physicalSkyBackgroundLinear','lunarBackgroundLinear','lunarNightDisplayLinear','stellarLinear','diffusePhysicalLinear']){
  const a=result.raster[key],b=expected[key];assert(a&&b,key);
  assert.equal(Buffer.compare(Buffer.from(a.buffer,a.byteOffset,a.byteLength),Buffer.from(b.buffer,b.byteOffset,b.byteLength)),0,key);
 }
 assert.deepEqual(result.raster.lunarDisplayPresentation,expected.lunarDisplayPresentation);
 const buffers=rasterTransferables(result);assert.equal(new Set(buffers).size,buffers.length);
 const transferred=structuredClone(result,{transfer:buffers});assert(buffers.every(b=>b.byteLength===0));
 assert.equal(transferred.raster.nativeLunarDisplayPrepared,true);
 let recalculations=0,compositions=0;
 const scope={result:transferred,request:job,physical:true,lifecycle:{current:()=>true},snapshot:()=>({weather:null}),
  nativeLunarNightPresentation(){recalculations++;throw Error('UI recomputed worker-owned lunar display');},nativeSkyPresentation,nativeAtmosphereFields,
  frame:null,job:null,status:{renders:0},compose:()=>compositions++,publish(){}};
 vm.createContext(scope);vm.runInContext(accept+'\naccept(result,1,request)',scope);
 assert.equal(recalculations,0);assert.equal(compositions,1);assert.equal(scope.frame.raster,transferred.raster);
 engine.dispose();
});
test('deep-night acceptance rejects an unprepared result instead of silently restoring expensive UI work',()=>{
 const scope={result:{status:'ready',raster:{physicalState:{sun:{altDeg:-25}}}},request:{options:{backgroundStepCss:8}},
  lifecycle:{current:()=>true},snapshot:()=>({}),status:{rejections:0},nativeLunarNightPresentation(){throw Error('Unexpected UI computation');}};
 vm.createContext(scope);assert.throws(()=>vm.runInContext(accept+'\naccept(result,1,request)',scope),/worker lunar display/);
});
