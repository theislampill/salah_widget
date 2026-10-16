import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';import {pathToFileURL}from'node:url';
const owner=new URL('../../real-sky/native-preview.mjs',import.meta.url);
const sha=v=>crypto.createHash('sha256').update(v).digest('hex'),bytes=v=>Buffer.from(v.buffer,v.byteOffset,v.byteLength);
const reference=await import(owner),source=fs.readFileSync(owner,'utf8').replace(/from '(\.\/[^']+)'/g,(_,v)=>'from '+JSON.stringify(new URL(v,owner).href));
const inspect='\nexport const inspectCache=()=>[...lunarGeometryCache].map(([key,g])=>({key,nodeCount:g.directions.length,vectorCount:g.vectors.filter(Boolean).length,finiteVectors:g.vectors.filter(Boolean).every(v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite)),typedBytes:Object.values(g).filter(ArrayBuffer.isView).reduce((n,v)=>n+v.byteLength,0)}));';
const load=s=>import('data:text/javascript;base64,'+Buffer.from(s+inspect).toString('base64'));
const candidate=await load(source);
const {nativeJob}=await import('../../real-sky/native-contract.mjs'),{physicalSkyState}=await import('../../real-sky/core/src/sky-state.mjs');
const oracle=(raster,view,residual,gx,gy)=>reference.nativeSkyPresentation({...raster,lunarBackgroundLinear:reference.nativeLunarAtmosphereField(raster.physicalState,raster.atmosphere,view,residual,gx,gy)},view);
const snapshot={utcMs:Date.parse('2026-09-25T02:00:00Z'),lat:28.5383,lon:-81.3792,heightM:0,generation:2,sceneIdentity:'component-r5',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:0,code:0,temp:28},units:'c',lp:0,timeScale:1};
const job=nativeJob(snapshot,true),state=physicalSkyState(job.observer),view=job.options.view,residual=job.options.diffuse.residualNight;
function fixture(atmosphere={},moon={},v=view){
 const physical={...state,moon:{...state.moon,...moon}},fields=reference.nativeAtmosphereFields(physical,atmosphere,v,residual,41,67),background=fields.background;
 return {raster:{width:325,height:530,linear:background,skyBackgroundLinear:background,backgroundLinear:background,effectiveExposure:24/(1+24*fields.mean/.5),physicalState:physical,atmosphere},view:v};
}
const cases=[['zero-extinction',{pressureHpa:0,aerosolTau550:0,greyTau:0},{}],['absorbing-only',{pressureHpa:0,aerosolTau550:0,greyTau:1},{}],['absorbing-aerosol',{pressureHpa:0,aerosolTau550:.2,aerosolAlbedo:0},{}],['cloud-zero',{cloudTransmission:0},{}],['cloud-one',{cloudTransmission:1},{}],['cloud-fraction',{cloudTransmission:.37},{}],['cloud-depth',{cloudOpticalDepth:.3},{}],['distance-radius-defaults',{}, {distanceKm:undefined,angularRadiusDeg:undefined}],['distance-min',{}, {distanceKm:100000}],['distance-max',{}, {distanceKm:1000000}],['radius-min',{}, {angularRadiusDeg:.01}],['radius-max',{}, {angularRadiusDeg:2}]];
function compare(label,f,m=candidate){
 const raw=bytes(f.raster.linear).slice(),a=oracle(f.raster,f.view,residual,41,67),b=m.nativeLunarNightPresentation(f.raster,f.view,residual,41,67);
 assert.deepEqual(Object.keys(a).sort(),Object.keys(b).sort(),label);
 for(const [key,v]of Object.entries(a)){if(ArrayBuffer.isView(v))assert(bytes(v).equals(bytes(b[key])),label+'/'+key);else assert.deepEqual(v,b[key],label+'/'+key);}
 assert(bytes(f.raster.linear).equals(raw),label+' physical input unchanged');
 if(a.lunarNightDisplayLinear){assert.notEqual(b.lunarBackgroundLinear.buffer,b.lunarNightDisplayLinear.buffer);assert.equal(b.physicalSkyBackgroundLinear,f.raster.skyBackgroundLinear);}
 return {label,rawMoonSha256:sha(bytes(a.lunarBackgroundLinear)),positive:a.lunarBackgroundLinear.some(v=>v>0),mapped:!!a.lunarNightDisplayLinear};
}
const rows=cases.map(([name,atm,moon])=>compare(name,fixture(atm,moon)));
for(const r of rows.slice(0,4))assert(!r.positive,r.label+' must not generate lunar light');
assert(rows.slice(4).every(r=>r.positive));
const base=fixture(),bad=[];
for(const [name,change]of [
 ['invalid-UTC',r=>({...r,physicalState:{...r.physicalState,utcMs:NaN}})],
 ...[['altDeg',91],['azDeg',NaN],['phaseAngleDeg',181],['distanceKm',99999],['distanceKm',1000001],['angularRadiusDeg',.009],['angularRadiusDeg',2.001]].map(([k,v])=>['invalid-moon-'+k+'-'+v,r=>({...r,physicalState:{...r.physicalState,moon:{...r.physicalState.moon,[k]:v}}})]),
 ...[null,{pressureHpa:-1},{cloudTransmission:1.01},{cloudTransmission:.5,cloudOpticalDepth:1},{aerosolAlbedo:2},{greyTau:NaN}].map((atm,i)=>['invalid-atmosphere-'+i,r=>({...r,atmosphere:atm})])
]){
 const raster=change(base.raster),errors=[];
 for(const m of [{nativeLunarNightPresentation:oracle},candidate])try{m.nativeLunarNightPresentation(raster,view,residual,41,67);errors.push(null);}catch(e){errors.push({name:e.name,message:e.message});}
 assert(errors[0]&&errors[1],name);assert.deepEqual(errors[0],errors[1],name);bad.push({name,error:errors[0]});
}
for(const invalid of [{},{...residual,zenithCdM2:-1},{...residual,includesRegisteredStarlight:true}]){
 const errors=[];for(const m of [{nativeLunarNightPresentation:oracle},candidate])try{m.nativeLunarNightPresentation(base.raster,view,invalid,41,67);errors.push(null);}catch(e){errors.push({name:e.name,message:e.message});}
 assert(errors[0]&&errors[1]);assert.deepEqual(errors[0],errors[1]);bad.push({name:'invalid-residual',error:errors[0]});
}
const mutations=[['cloud-once',source.replace('moon*cloudTransmissionFor(h,a,null,state.utcMs)*omega[i]','moon*omega[i]'),fixture({cloudTransmission:.37})],['absorbing-gate',source.replace('})*lunarScatteringAlbedo;','})*1;'),fixture({pressureHpa:0,aerosolTau550:0,greyTau:1})]];
const killed=[];for(const [name,code,f]of mutations){assert.notEqual(code,source);const m=await load(code);assert.throws(()=>compare(name,f,m));killed.push(name);}
let firstKey;
for(let i=0;i<6;i++){const v={...view,azDeg:180+i};compare('camera-'+i,fixture({}, {},v));if(i===0)firstKey=candidate.inspectCache()[0].key;}
const inventory=candidate.inspectCache();assert.equal(inventory.length,4);assert(!inventory.some(v=>v.key===firstKey));
assert(inventory.every(v=>v.nodeCount<=4761&&v.vectorCount<=4761&&v.finiteVectors&&v.typedBytes<=219948));
console.log(JSON.stringify({componentCases:rows.length,negativeCases:bad.length,killedMutations:killed,cache:inventory}));
