// R0033 M6 research record (issue 100, row R33-20; PRA-F-31): effect-free computation of the refined sky's lunar
// light under `simMoon*`. Node only: no browser, no network, no provider, no clock read (every instant is an argument
// or a constant below). It runs the AUTHORED refined-sky boundary and the COPIED core unchanged:
//   real-sky/native-contract.mjs nativeJob()            the job the refined sky receives (observer UTC + location only)
//   real-sky/core/src/sky-state.mjs physicalSkyState()  the real-ephemeris Sun/Moon the core derives from that UTC
//   real-sky/core/src/sky-background.mjs createSkyModel().sample()  KS1991 lunar sky luminance (moonLuminance)
//   real-sky/native-preview.mjs renderNativeBackgroundPreview()     the atmosphere the card actually presents
//   real-sky/native-encoding.mjs encodeNativeFrame()                its display bytes
// and evaluates the native light decision with the function text of src/native/index.html (nativeLunarPresentation),
// extracted verbatim, for the simulated Moon. Nothing here is a product change or a defect fix.
// "Counterfactual" = the same job with the core's Moon placed below the horizon and nothing else changed: the refined
// atmosphere as it would be if it followed a new / below-horizon simulated Moon. The difference between the two
// encoded frames is the refined sky's lunar contribution in display bytes.
// Usage: node tools/qa/r0033_m6_lunar_divergence.mjs [--out <report.json>]     (prints the report; exit 1 on a
//        failed self-check: the local preview assembly must be byte-identical to renderNativeBackgroundPreview).
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {nativeJob} from '../../real-sky/native-contract.mjs';
import {physicalSkyState} from '../../real-sky/core/src/sky-state.mjs';
import {createSkyModel} from '../../real-sky/core/src/sky-background.mjs';
import {resolveSkyInputs,skyProjection} from '../../real-sky/core/src/physical-sky-renderer.mjs';
import {nativeAtmosphereFields,nativeSkyPresentation,renderNativeBackgroundPreview} from '../../real-sky/native-preview.mjs';
import {encodeNativeFrame} from '../../real-sky/native-encoding.mjs';

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..','..');
const args={};for(let i=2;i<process.argv.length;i+=2)args[process.argv[i].slice(2)]=process.argv[i+1];

// Synthetic fixture only (Madinah). Clear fixture weather as in tools/qa/r0033_native_cells.cjs.
const MADINAH={lat:24.47,lon:39.61};
const snapshot=(utc,site=MADINAH)=>({utcMs:Date.parse(utc),lat:site.lat,lon:site.lon,heightM:0,generation:1,sceneIdentity:'r0033-m6',
 camera:{azDeg:180,altDeg:45,fovYDeg:90,rollDeg:0},weather:{src:'fixture',vis:24000,cloud:0,code:0,temp:24},units:'c',lp:0,
 reducedMotion:true,tz:'Asia/Riyadh',timeScale:0,solarAnchor:{x:20,y:216}});

// The native light decision, from the authored source text (no copy to drift).
const source=fs.readFileSync(path.join(ROOT,'src','native','index.html'),'utf8');
const fn=/function nativeLunarPresentation\(moon,solarElevation,surfaceFailed\)\{[\s\S]*?\n\}/.exec(source);
if(!fn)throw new Error('nativeLunarPresentation not found in src/native/index.html');
const nativeLunarPresentation=new Function('clamp',fn[0]+';return nativeLunarPresentation;')(x=>Math.min(1,Math.max(0,x)));
function nativeLight(sim,sunAltDeg){
 const p=nativeLunarPresentation({frac:sim.frac,alt:sim.alt},sunAltDeg,false);
 return {eligible:p.moonLightEligible,reason:p.moonLightReason,moonlight:+p.moonlight.toFixed(4),beam:+(0.6*p.moonlight).toFixed(4),cloudLight:+p.moonlight.toFixed(4),
  localStarWash:+p.moonLocalWash.toFixed(4),localGlow:+p.moonGlow.toFixed(4),calendarGroupOpacity:+p.moonShow.toFixed(3)};
}

// The non-fast branch of renderNativeBackgroundPreview with an optional physical-state override.
function preview(shot,state){
 const job=nativeJob(shot,true),view={...job.options.view,width:325,height:530};
 const fields=nativeAtmosphereFields(state,job.options.atmosphere,view,job.options.diffuse.residualNight,24,40);
 const nominalExposure=job.options.nominalExposure,effectiveExposure=nominalExposure/(1+nominalExposure*fields.mean/.5);
 const raster=nativeSkyPresentation({width:325,height:530,linear:fields.background,backgroundLinear:fields.background,skyBackgroundLinear:fields.background,
  solarAerosolLinear:fields.solarAerosolLinear,solarBackgroundLinear:fields.solarBackgroundLinear,lunarBackgroundLinear:fields.lunarBackgroundLinear,
  twilightDisplay:fields.twilightDisplay,stellarLinear:new Float64Array(fields.background.length),effectiveExposure,nominalExposure,physicalState:state,
  atmosphere:job.options.atmosphere,meanBackgroundY:fields.mean},view,shot.solarAnchor);
 return {job,raster,bytes:encodeNativeFrame(raster.linear,raster.effectiveExposure)};
}
const round=(v,n=6)=>v==null?null:+Number(v).toPrecision(n);
function evaluate(utc,sim,site=MADINAH){
 const shot=snapshot(utc,site),job=nativeJob(shot,true),{observer,atmosphere}=resolveSkyInputs(job.observer,job.options.atmosphere);
 const state=physicalSkyState(observer),sky=createSkyModel(state,atmosphere,{residualNight:job.options.diffuse.residualNight});
 const mapping=skyProjection(job.options.view),gx=24,gy=40;let n=0,moonSum=0,restSum=0,moonMax=0;
 for(let y=0;y<=gy;y++)for(let x=0;x<=gx;x++){const px=x*325/gx,py=y*530/gy;if(!mapping.above(px,py))continue;
  const s=sky.sample(mapping.unproject(px,py));n++;moonSum+=s.moonLuminance;restSum+=s.luminance-s.moonLuminance;moonMax=Math.max(moonMax,s.moonLuminance);}
 const zenith=sky.sample({altDeg:90,azDeg:0}),centre=sky.sample({altDeg:45,azDeg:180});
 const real=preview(shot,state),without=preview(shot,{...state,moon:{...state.moon,altDeg:-30}});
 let pixels=0,delta=0,maxDelta=0,levelReal=0,levelWithout=0;
 for(let y=0;y<530;y++)for(let x=0;x<325;x++){if(!mapping.above(x+.5,y+.5))continue;const at=(y*325+x)*4;pixels++;
  for(let c=0;c<3;c++){const d=Math.abs(real.bytes[at+c]-without.bytes[at+c]);delta+=d;if(d>maxDelta)maxDelta=d;levelReal+=real.bytes[at+c];levelWithout+=without.bytes[at+c];}}
 const light=nativeLight(sim,state.sun.altDeg);
 const refinedLunar=moonSum>0,divergence=refinedLunar&&!light.eligible?'refined sky carries real moonlight; native shows none'
  :!refinedLunar&&light.eligible?'native shows simulated moonlight; refined sky carries none':refinedLunar&&light.eligible?'both lit (magnitudes follow different Moons)':'both unlit';
 return {utc,site,sim,
  realMoon:{altDeg:round(state.moon.altDeg,4),azDeg:round(state.moon.azDeg,4),illuminatedFraction:round(state.moon.illuminatedFraction,4),phaseAngleDeg:round(state.moon.phaseAngleDeg,4)},
  sunAltDeg:round(state.sun.altDeg,4),
  refinedSkyKS1991:{unit:'cd/m2 (photopic-equivalent, core convention)',zenith:round(zenith.moonLuminance),cameraCentre:round(centre.moonLuminance),frameMean:round(moonSum/n),frameMax:round(moonMax),
   nonLunarFrameMean:round(restSum/n),lunarToNonLunarFrameMean:restSum>0?round(moonSum/restSum,4):null,gridNodesAboveHorizon:n},
  presentedAtmosphere:{pixelsAboveHorizon:pixels,effectiveExposure:{real:round(real.raster.effectiveExposure),lunarRemoved:round(without.raster.effectiveExposure)},
   meanByte:{real:round(levelReal/(pixels*3),5),lunarRemoved:round(levelWithout/(pixels*3),5)},meanAbsByteDelta:round(delta/(pixels*3),5),maxAbsByteDelta:maxDelta,
   lunarDisplay:real.raster.lunarDisplayPresentation?{contract:real.raster.lunarDisplayPresentation.contract}:null},
  nativeUnderSim:light,divergence};
}

// Self-check: the local assembly is the product's (byte-identical frame for the unmodified state).
const probe=snapshot('2026-09-26T19:00:00Z'),mine=preview(probe,physicalSkyState(nativeJob(probe,true).observer)),theirs=renderNativeBackgroundPreview(probe);
const theirBytes=encodeNativeFrame(theirs.raster.linear,theirs.raster.effectiveExposure);
const selfCheck=mine.bytes.length===theirBytes.length&&mine.bytes.every((v,i)=>v===theirBytes[i])&&mine.raster.effectiveExposure===theirs.raster.effectiveExposure;

const NEW={frac:0.01,waxing:true,alt:20,H:42};
const report={schema:'r0033-m6-lunar-divergence/1',fixture:{lat:24.47,lon:39.61,label:'Madinah (synthetic)',camera:snapshot('2026-01-01T00:00:00Z').camera,weather:'clear fixture, visibility 24 km'},
 selfCheck:{previewAssemblyByteIdenticalToProduct:selfCheck},
 // M6 step 2: a fixed UTC with a bright real Moon while the native SIM shows a new Moon.
 step2:[evaluate('2026-09-26T19:00:00Z',NEW),evaluate('2026-09-26T19:00:00Z',{frac:0.01,waxing:true,alt:-20,H:0})],
 // M6 step 3: the instants of the recorded lunar evidence, each with the simulated Moon it used.
 step3:[
  ...[['crescent',0.08],['half',0.5],['gibbous',0.92],['full',0.98],['new',0.01]].map(([name,frac])=>({record:'R0033 native cells (tools/qa/r0033_native_cells.cjs), scene '+name,...evaluate('2026-09-08T19:00:00Z',{frac,waxing:true,alt:20,H:42})})),
  {record:'docs/moon/evidence moon-visual-*, clock-20261007, rim-20261007/phase-acceptance (simTime=23:30)',...evaluate('2026-09-07T20:30:00Z',{frac:0.12,waxing:true,alt:20,H:42})},
  {record:'docs/moon/evidence moon-file/receipt, rim-20261007/before (simTime=23:30)',...evaluate('2026-09-07T20:30:00Z',{frac:0.5,waxing:false,alt:20,H:42})},
  {record:'tests/smoke.html case 21 (simTime=01:00) as recorded with zone Asia/Riyadh in docs/moon/evidence/rim-20261007/native-smoke and the R0017 acceptance',...evaluate('2026-09-06T22:00:00Z',{frac:0.01,waxing:true,alt:-20,H:0})},
  {record:'tests/smoke.html case 22 (simTime=01:00), same records',...evaluate('2026-09-06T22:00:00Z',{frac:0.6,waxing:true,alt:40,H:8})},
  {record:'tests/smoke.html orientation cases (simTime=02:00), same records',...evaluate('2026-09-06T23:00:00Z',{frac:0.3,waxing:true,alt:55,H:0})}],
 // Other work orders' retained records that used simMoon* (sampled, NOT exhaustive; outside M6's AGENTS/QUALIFICATION scope).
 otherRecordsSampled:[
  {record:'R0007/R0002 case R0007-warm-ashen-below-horizon (New York fixture, fixed clock 2026-03-08T06:30Z, simTime=01:30)',...evaluate('2026-03-08T06:30:00Z',{frac:0.01,waxing:true,alt:-20,H:42},{lat:40.71,lon:-74.01})},
  {record:'R0021 completion b1 (tz=UTC, fixed clock 2026-11-11T12:00Z, simTime=23:30), half Moon',...evaluate('2026-11-11T23:30:00Z',{frac:0.5,waxing:true,alt:40,H:180})},
  {record:'R0021 completion b1 (tz=UTC, fixed clock 2026-11-11T12:00Z, simTime=23:30), new Moon',...evaluate('2026-11-11T23:30:00Z',{frac:0.01,waxing:true,alt:40,H:180})}]};
const text=JSON.stringify(report,null,1)+'\n';
if(args.out)fs.writeFileSync(path.resolve(args.out),text);
process.stdout.write(text);
if(!selfCheck)process.exitCode=1;
