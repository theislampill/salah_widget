import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {bindRegisteredStarlight} from '../src/diffuse-binding.mjs';
import {createSkyModel} from '../src/sky-background.mjs';
import {directTransmission} from '../src/atmosphere.mjs';
import {spectralStarFlux} from '../src/spectral.mjs';
import {refractionDeg} from '../src/astronomy.mjs';
const api=await import('../src/diffuse-transport.mjs').catch(()=>({}));
const text=fs.readFileSync(new URL('../data/bright-stars.json',import.meta.url),'utf8'),asset=JSON.parse(fs.readFileSync(new URL('../data/registered-starlight/V-nside32.json',import.meta.url),'utf8'));
const binding=bindRegisteredStarlight(text,asset),observer={utcMs:Date.UTC(2026,0,15,2),latDeg:28.54,lonDeg:-81.38,pressureHpa:0};
const state={utcMs:observer.utcMs,source:'test geometric state',sun:{altDeg:-50,azDeg:20,distanceAu:1},moon:{altDeg:-40,azDeg:160,angularRadiusDeg:.25,phaseAngleDeg:180,distanceKm:384400}};
const residualNight={kind:'assumed-nonstellar-residual',zenithCdM2:.00014,source:'test-only explicit residual assumption',includesRegisteredStarlight:false};
const make=(extra={},atmosphere={},sky=state,obs=observer)=>{assert.equal(typeof api.createDiffuseTransport,'function');const {cloudAt=null,...rest}=extra;return api.createDiffuseTransport({binding,residualNight,...rest},{observer:obs,atmosphere,state:sky,cloudAt});};
const close=(a,b,rel=1e-10)=>assert.ok(Math.abs(a-b)<=rel*Math.max(Math.abs(a),Math.abs(b),1e-30),`${a} != ${b}`);
test('V transport is a declared in-band assumption and equals CP5 Vega V transport',()=>{
 assert.equal(typeof api.createVBandTransmission,'function');const atmosphere={aerosolTau550:.19,greyTau:.03};const tr=api.createVBandTransmission(atmosphere);
 for(const alt of [0,.05,1,7.34,25,60,90]){const f=spectralStarFlux({hip:91262,vmag:0,bv:0},alt,{}, {response:'V-monochrome',transportAt:w=>directTransmission(w,alt,atmosphere,1)});close(tr.exact(alt),f.vFlux,1e-12);assert.ok(Math.abs(tr.sample(alt)-f.vFlux)<.0001);}
 assert.match(tr.assumption,/Vega/);assert.equal(api.createVBandTransmission({pressureHpa:0,aerosolTau550:0}).exact(30),1);
});
test('directional cloud transmission replaces rather than multiplies the scalar cloud',()=>{
 const h={altDeg:55,azDeg:72},clear=make().sample(h),scalar=make({}, {cloudTransmission:.08}).sample(h),mapped=make({cloudAt:()=>.08},{cloudTransmission:.08}).sample(h);
 close(scalar.relativeV0PerSr/clear.relativeV0PerSr,.08);close(mapped.relativeV0PerSr/clear.relativeV0PerSr,.08);assert.equal(mapped.cloudTransmission,.08);
});
test('zero transmission is known darkness; strict missing support remains explicitly missing',()=>{
 const strict=make({allowEstimates:false});let missing;
 for(let alt=5;alt<=85&&!missing;alt+=5)for(let az=0;az<360;az+=5){const s=strict.sample({altDeg:alt,azDeg:az});if(!s.sourceDefined){missing={altDeg:alt,azDeg:az};assert.equal(s.defined,false);assert.equal(s.relativeV0PerSr,null);break;}}
 assert.ok(missing);const blocked=make({allowEstimates:false,cloudAt:()=>0}).sample(missing);assert.equal(blocked.defined,true);assert.equal(blocked.relativeV0PerSr,0);assert.equal(blocked.sourceDefined,false);
});
test('angular physical Moon blocks all direct light independent of lunar phase',()=>{
 const h={altDeg:50,azDeg:210};for(const phase of [0,180]){const s=make({}, {},{...state,moon:{...state.moon,...h,phaseAngleDeg:phase}}).sample(h);assert.equal(s.occulted,true);assert.equal(s.relativeV0PerSr,0);}
 const a=make({}, {},{...state,moon:{...state.moon,altDeg:50,azDeg:210}});assert.ok(a.sample({altDeg:51,azDeg:210}).relativeV0PerSr>0);
});
test('physical Moon compares geometric directions even when map rays are refracted',()=>{
 const geo=3,app=geo+refractionDeg(geo,1013.25,10),moon={...state.moon,altDeg:geo,azDeg:210,angularRadiusDeg:.02,geometric:true};
 const s=make({}, {},{...state,moon},{...observer,pressureHpa:1013.25,temperatureC:10}).sample({altDeg:app,azDeg:210});assert.equal(s.occulted,true);
});
test('the old night floor is replaced, not added to the nonstellar residual',()=>{
 // Fails before the CP7.4 sky-model extension: CP6 still uses nightZenithVMag.
 const a=createSkyModel(state,{nightZenithVMag:10},{residualNight}),b=createSkyModel(state,{nightZenithVMag:30},{residualNight});
 close(a.sample({altDeg:90,azDeg:0}).luminance,residualNight.zenithCdM2);close(a.sample({altDeg:90,azDeg:0}).luminance,b.sample({altDeg:90,azDeg:0}).luminance);
 assert.match(a.models.night,/residual/);
});
test('an unlabelled or overlapping night residual is rejected',()=>{
 assert.throws(()=>createSkyModel(state,{}, {residualNight:{zenithCdM2:.00014}}),/residual/i);
 assert.throws(()=>make({residualNight:{...residualNight,includesRegisteredStarlight:true}}),/residual/i);
 assert.throws(()=>make({residualNight:null}),/residual/i);
});
test('invalid sampling settings, fake binding and non-geometric lunar state fail',()=>{
 assert.throws(()=>make({binding:{...binding}}),/bound/i);assert.throws(()=>make({samplesPerAxis:8}));assert.throws(()=>make({allowEstimates:'false'}));
 assert.throws(()=>make({}, {},{...state,moon:{...state.moon,geometric:false}}),/geometric/i);
});
test('grey optical depth is used once in the actual direct diffuse path',()=>{
 const alt=30,h={altDeg:alt,azDeg:80},clear=make({}, {pressureHpa:0,aerosolTau550:0}).sample(h),grey=make({}, {pressureHpa:0,aerosolTau550:0,greyTau:.2}).sample(h);
 const X=1/(Math.sin(alt*Math.PI/180)+.50572*(alt+6.07995)**-1.6364);close(grey.relativeV0PerSr/clear.relativeV0PerSr,Math.exp(-.2*X),1e-12);
});
