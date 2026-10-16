import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {physicalSkyState} from '../../real-sky/core/src/sky-state.mjs';
const owner=new URL('../../real-sky/native-preview.mjs',import.meta.url);
const source=fs.readFileSync(owner,'utf8');
async function inspectable(mutated=false){
 let s=source.replace(/from '(\.\/[^']+)'/g,(_,v)=>'from '+JSON.stringify(new URL(v,owner).href));
 if(mutated){const rule='if(lunarGeometryCache.size===4)lunarGeometryCache.delete(lunarGeometryCache.keys().next().value);';assert.equal(s.split(rule).length,2);s=s.replace(rule,'');}
 s+='\nexport const inspectCache=()=>[...lunarGeometryCache].map(([key,g])=>({key,directions:g.directions.length,vectors:g.vectors.filter(Boolean).length,finiteVectors:g.vectors.filter(Boolean).every(v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite)),bytes:[g.omega,g.above,g.ix,g.tx,g.iy,g.ty].reduce((n,a)=>n+a.byteLength,0)}));';
 return import('data:text/javascript;base64,'+Buffer.from(s).toString('base64'));
}
const snapshot={utcMs:Date.parse('2026-09-25T02:00:00Z'),lat:28.5383,lon:-81.3792,heightM:0,generation:2,sceneIdentity:'bounded-lunar-cache',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:0,code:0,temp:28},units:'c',lp:0,timeScale:1};
function exercise(m){
 let initialKey;
 for(let i=0;i<6;i++){
  const job=nativeJob({...snapshot,camera:{...snapshot.camera,azDeg:180+i}},true),state=physicalSkyState(job.observer),v=job.options.view;
  const fields=m.nativeAtmosphereFields(state,job.options.atmosphere,v,job.options.diffuse.residualNight,41,67),raw=fields.background;
  m.nativeLunarNightPresentation({width:325,height:530,linear:raw,backgroundLinear:raw,skyBackgroundLinear:raw,physicalState:state,atmosphere:job.options.atmosphere,effectiveExposure:1},v,job.options.diffuse.residualNight,41,67);
  if(i===0)initialKey=m.inspectCache()[0].key;
 }
 return{rows:m.inspectCache(),initialKey};
}
function bounded(result){assert.equal(result.rows.length,4);assert(!result.rows.some(r=>r.key===result.initialKey));for(const r of result.rows){assert(r.directions<=4761&&r.vectors<=4761&&r.finiteVectors);assert(r.bytes<=219948);}}
test('actual lunar geometry cache evicts its oldest key and retains at most four finite geometries',async()=>bounded(exercise(await inspectable())));
test('removing actual eviction fails the same resource-bound discriminator',async()=>{const mutant=await inspectable(true);assert.throws(()=>bounded(exercise(mutant)),assert.AssertionError);});
