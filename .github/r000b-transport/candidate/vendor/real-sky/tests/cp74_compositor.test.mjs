import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {createHash} from 'node:crypto';
import {renderPhysicalSky,skyProjection} from '../src/physical-sky-renderer.mjs';
import {PhysicalSkyBridge} from '../integration/physical-sky-bridge.mjs';
import {bindRegisteredStarlight} from '../src/diffuse-binding.mjs';
import {createDiffuseTransport} from '../src/diffuse-transport.mjs';
import {encodeFrame} from '../src/renderer.mjs';
const text=fs.readFileSync(new URL('../data/bright-stars.json',import.meta.url),'utf8'),asset=JSON.parse(fs.readFileSync(new URL('../data/registered-starlight/V-nside32.json',import.meta.url),'utf8'));
const binding=bindRegisteredStarlight(text,asset),observer={utcMs:Date.UTC(2026,0,15,2),latDeg:28.54,lonDeg:-81.38};
const physicalState={utcMs:observer.utcMs,source:'test geometric state',sun:{altDeg:-50,azDeg:20,distanceAu:1},moon:{altDeg:-40,azDeg:160,angularRadiusDeg:.25,phaseAngleDeg:180,distanceKm:384400}};
const residualNight={kind:'assumed-nonstellar-residual',zenithCdM2:.00014,source:'test explicit assumption',includesRegisteredStarlight:false};
const view={type:'camera',width:32,height:48,azDeg:180,altDeg:50,fovYDeg:50},diffuse={binding,residualNight,samplesPerAxis:1};
const base={observer,view,physicalState,autoExposure:false,nominalExposure:500,response:'V-monochrome',diffuse};
const close=(a,b,rel=1e-10)=>assert.ok(Math.abs(a-b)<=rel*Math.max(Math.abs(a),Math.abs(b),1e-25),`${a} != ${b}`);
const sum=a=>a.reduce((s,v)=>s+v,0),hash=a=>createHash('sha256').update(Buffer.from(a.buffer,a.byteOffset,a.byteLength)).digest('hex');
test('diffuse-off is bit-identical to all 12 captured CP6 cases',()=>{
 const bridge=new PhysicalSkyBridge(JSON.parse(text));const fixtures=JSON.parse(fs.readFileSync(new URL('../checkpoints/cp74/cp6-baseline-fixtures.json',import.meta.url),'utf8'));
 for(const f of fixtures.cases)for(const extra of [{},{diffuse:{enabled:false}}]){const result=bridge.render(f.observer,{...f.options,...extra});assert.equal(result.status,'ready');const r=result.raster;
 assert.equal(hash(r.linear),f.linear);assert.equal(hash(r.stellarLinear),f.stellar);assert.equal(hash(r.backgroundLinear),f.background);assert.equal(r.effectiveExposure,f.effectiveExposure);assert.equal(r.meanBackgroundY,f.meanBackgroundY);assert.equal(r.detectableSources,f.detectableSources);assert.equal(createHash('sha256').update(JSON.stringify(r.sourceDiagnostics)).digest('hex'),f.diagnosticsHash);}
});
test('real-source light enters the linear frame once, and encoding happens only at the end',()=>{
 const r=renderPhysicalSky([],base);assert.ok(r.diffuseLinear instanceof Float64Array);assert.ok(sum(r.diffuseLinear)>0);
 for(let i=0;i<r.linear.length;i++)close(r.linear[i],r.stellarLinear[i]+r.skyBackgroundLinear[i]+r.diffuseLinear[i]);
 assert.equal(r.effectiveExposure,500);assert.equal(r.diffuseState.sourceSha256,asset.sourceSha256);assert.equal(r.diffuseState.colourModel,'neutral V-equivalent proxy, not measured CIE colour');
 assert.deepEqual(encodeFrame(r.linear,r.effectiveExposure),encodeFrame(r.backgroundLinear,500));
});
test('radiance-to-pixel conversion uses V zero point and the solid angle exactly once',()=>{
 const a={pressureHpa:0,aerosolTau550:0},r=renderPhysicalSky([],{...base,atmosphere:a}),map=skyProjection(view),model=createDiffuseTransport(diffuse,{observer,atmosphere:a,state:physicalState});
 assert.ok(r.diffuseLinear);for(const [x,y] of [[16,24],[4,8],[22,40]]){const px=x+.5,py=y+.5,s=model.sample(map.unproject(px,py)),at=(y*r.width+x)*3;close(r.diffuseLinear[at],s.relativeV0PerSr*map.solidAngle(px,py));}
});
test('gas/cloud transport is once-only in the joined diffuse buffer',()=>{
 const a=renderPhysicalSky([],base),b=renderPhysicalSky([],{...base,atmosphere:{cloudTransmission:.08}}),c=renderPhysicalSky([],{...base,atmosphere:{cloudTransmission:.08},cloudAt:()=>.08});assert.ok(a.diffuseLinear);
 for(let i=0;i<a.diffuseLinear.length;i++){close(b.diffuseLinear[i],a.diffuseLinear[i]*.08);close(c.diffuseLinear[i],b.diffuseLinear[i]);}
});
test('daylight and added local light change contrast but do not delete extraterrestrial flux',()=>{
 const night=renderPhysicalSky([],{...base,autoExposure:true}),day=renderPhysicalSky([],{...base,autoExposure:true,physicalState:{...physicalState,sun:{...physicalState.sun,altDeg:50}}}),urban=renderPhysicalSky([],{...base,autoExposure:true,atmosphere:{lightPollutionCdM2:.02}});
 assert.ok(night.diffuseLinear);assert.equal(hash(night.diffuseLinear),hash(day.diffuseLinear));assert.ok(day.effectiveExposure<night.effectiveExposure);assert.ok(urban.effectiveExposure<night.effectiveExposure);
 assert.ok(day.diffuseState.meanDisplayIncrement<night.diffuseState.meanDisplayIncrement);
});
test('display mask removes direct diffuse light, not sky scattering or physical exposure',()=>{
 const a=renderPhysicalSky([],{...base,autoExposure:true}),b=renderPhysicalSky([],{...base,autoExposure:true,displayTransmissionAt:()=>0});assert.ok(b.diffuseLinear);assert.equal(sum(b.diffuseLinear),0);
 assert.equal(hash(a.skyBackgroundLinear),hash(b.skyBackgroundLinear));assert.equal(hash(a.diffusePhysicalLinear),hash(b.diffusePhysicalLinear));assert.equal(a.effectiveExposure,b.effectiveExposure);assert.deepEqual(a.physicalState,b.physicalState);
});
test('physical Moon occultation masks the map by angular footprint without cutting out atmospheric sky',()=>{
 const moon={...physicalState.moon,altDeg:50,azDeg:180,angularRadiusDeg:.5};const small={...base,view:{...view,fovYDeg:10},diffuse:{...diffuse,samplesPerAxis:2},physicalState:{...physicalState,moon}};
 const r=renderPhysicalSky([],small);assert.ok(r.diffuseMasks);assert.ok(r.diffuseMasks.occultedFraction.some(x=>x>0));assert.ok(r.diffuseMasks.occultedFraction.some(x=>x===1));
 for(let i=0;i<r.diffuseMasks.occultedFraction.length;i++)if(r.diffuseMasks.occultedFraction[i]===1){assert.equal(r.diffuseLinear[i*3],0);assert.ok(r.skyBackgroundLinear[i*3]>0);}
 const full=renderPhysicalSky([],{...small,physicalState:{...small.physicalState,moon:{...moon,phaseAngleDeg:0}}});assert.equal(hash(full.diffuseLinear),hash(r.diffuseLinear));
});
test('strict source support remains missing and flags exposure as incomplete',()=>{
 const r=renderPhysicalSky([],{...base,view:{type:'allsky',width:64,height:64},diffuse:{...diffuse,allowEstimates:false}});assert.ok(r.diffuseState);assert.ok(r.diffuseState.missingPixels>0);assert.equal(r.diffuseState.exposureComplete,false);assert.ok(r.diffuseMasks.missing.some(x=>x===1));
});
test('diffuse light never scintillates; backward seeks reconstruct the same physical field',()=>{
 const a=renderPhysicalSky([],base),b=renderPhysicalSky([],{...base,reducedMotion:false});assert.ok(a.diffuseLinear);assert.equal(hash(a.diffuseLinear),hash(b.diffuseLinear));
 const obs={...observer,utcMs:observer.utcMs+21600000};const future=renderPhysicalSky([],{...base,observer:obs,physicalState:{...physicalState,utcMs:obs.utcMs}});assert.notEqual(hash(future.diffuseLinear),hash(a.diffuseLinear));assert.equal(hash(renderPhysicalSky([],base).diffuseLinear),hash(a.diffuseLinear));
});
test('bridge enforces actual bound catalogue identity, not only a claimed digest',()=>{
 const good=new PhysicalSkyBridge(binding.catalogue).render(observer,{view,diffuse});assert.equal(good.status,'ready');assert.ok(good.raster.diffuseLinear);
 const bad=new PhysicalSkyBridge(JSON.parse(text)).render(observer,{view,diffuse});assert.equal(bad.status,'unavailable');assert.match(bad.error,/catalogue.*binding/i);
});
test('source contrast includes registered background and reports missing support',()=>{
 const h=skyProjection(view).unproject(16,24),star={id:'test',hip:91262,bv:0,vmag:2,x:16,y:24,visible:true,...h};const r=renderPhysicalSky([star],base);assert.ok(r.sourceDiagnostics[0].diffuseBackgroundY>0);assert.equal(r.sourceDiagnostics[0].backgroundComplete,true);assert.ok(r.sourceDiagnostics[0].backgroundY>r.sourceDiagnostics[0].diffuseBackgroundY);
});
test('fractional DPR keeps the same physical footprint and integrated diffuse light',()=>{
 const v={...view,width:31,height:47};const values=[];for(const dpr of [1,1.37,2,3]){const r=renderPhysicalSky([],{...base,view:v,dpr,diffuse:{...diffuse,samplesPerAxis:2}});assert.ok(r.diffuseLinear);values.push(sum(r.diffuseLinear)/(3*dpr*dpr));}
 assert.ok(Math.max(...values)/Math.min(...values)<1.005,JSON.stringify(values));
});
test('zenith readback includes direct diffuse radiance and distinguishes its support',()=>{
 const r=renderPhysicalSky([],base),m=createDiffuseTransport(diffuse,{observer,state:physicalState});assert.ok(r.zenithSky.diffuseLuminance>0);close(r.zenithSky.diffuseLuminance,m.sample({altDeg:90,azDeg:0}).luminance);close(r.zenithSky.luminance,r.zenithSky.atmosphericLuminance+r.zenithSky.diffuseLuminance);assert.equal(r.zenithSky.complete,true);
});
test('unknown zenith diffuse support stays null rather than becoming measured darkness',()=>{
 const unknown={...asset,id:'TEST-ONLY-UNKNOWN-SUPPORT',estimatedFraction:asset.estimatedFraction.map(()=>1)};
 const bound=bindRegisteredStarlight(text,unknown),r=renderPhysicalSky([],{...base,diffuse:{...diffuse,binding:bound,allowEstimates:false}});
 assert.equal(r.zenithSky.complete,false);assert.equal(r.zenithSky.diffuseLuminance,null);assert.equal(r.zenithSky.luminanceIsLowerBound,true);
});
test('active diffuse memory budget is rejected before invoking any sky callbacks',()=>{
 let calls=0;assert.throws(()=>renderPhysicalSky([],{...base,view:{type:'allsky',width:2048,height:2048},cloudAt:()=>{calls++;return 1;}}),/2,097,152/);assert.equal(calls,0);
});
test('custom all-sky padding shares the inverse-projection horizon',()=>{
 const v={type:'allsky',width:120,height:160,padding:15},m=skyProjection(v);assert.equal(m.above(60,125.1),false);assert.ok(Math.abs(m.unproject(60,125).altDeg)<1e-10);assert.equal(m.above(60,124.9),true);
});
