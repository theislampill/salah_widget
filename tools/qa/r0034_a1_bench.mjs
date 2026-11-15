// R0034-A1 performance witness (node, single thread): wall time of the host-side daytime decomposition
// (nativeAtmosphereFields + nativeSkyPresentation) at the former daytime lattice [24,40] and the worker lattice
// [41,67], owner scene. Reports median/p90 over N runs after 3 warm-up runs. Usage: node tools/qa/r0034_a1_bench.mjs [N]
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {renderPhysicalSky} from '../../real-sky/core/src/physical-sky-renderer.mjs';
import {nativeSkyPresentation,nativeAtmosphereFields} from '../../real-sky/native-preview.mjs';
import {luminanceToSurfaceMagnitude} from '../../real-sky/core/src/sky-background.mjs';
const N=+(process.argv[2]||15);
const s={utcMs:Date.parse('2026-11-14T15:26:00Z'),lat:28.54,lon:-81.38,heightM:0,generation:2,sceneIdentity:'bench',camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{vis:20000,cloud:100,code:3,temp:51},units:'f',lp:0};
const j=nativeJob(s,true);
const raw=renderPhysicalSky([],{...j.options,observer:j.observer,diffuse:null,atmosphere:{...j.options.atmosphere,nightZenithVMag:luminanceToSurfaceMagnitude(.00014)}});
const anchor={x:20.12,y:49.32,presence:1},out={};
for(const g of [[24,40],[41,67]]){const t=[];for(let i=0;i<N+3;i++){const a=performance.now();const f=nativeAtmosphereFields(raw.physicalState,raw.atmosphere,j.options.view,undefined,...g);
 nativeSkyPresentation({...raw,solarAerosolLinear:f.solarAerosolLinear,solarBackgroundLinear:f.solarBackgroundLinear,lunarBackgroundLinear:f.lunarBackgroundLinear,twilightDisplay:f.twilightDisplay},j.options.view,anchor);if(i>=3)t.push(performance.now()-a);}
 t.sort((a,b)=>a-b);out[g.join('x')]={nodes:(g[0]+1)*(g[1]+1),medianMs:+t[t.length>>1].toFixed(1),p90Ms:+t[Math.floor(t.length*.9)].toFixed(1)};}
console.log(JSON.stringify(out));
