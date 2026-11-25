'use strict';
// R0041 (R41-PIX, VM part): compare the refinement scene (Sun vector, fraction, lit side: the only inputs that change
// refined and initial V5 bytes) produced by main and by the candidate, every 10 minutes over 30 days, with each tree's
// own sources:
//   main      : nativeLunarSnapshot (index) -> nativeCalendarMoonScene (moon-precision.mjs), as main's runtime does;
//   candidate : nativeLunarSnapshot + nativeLunarPhaseDirection (index, read exactly as SalahMoonHost.capture spreads
//               it) -> directedCalendarScene (moon/src/moon-native.mjs, extracted verbatim) -> nativeCalendarMoonScene.
// Outside the waxing/phase-direction mismatch intervals the scenes must be identical, so the refined and initial
// surfaces are byte-identical by construction (the worker and receiver are pure functions of the scene; the extra
// leadDirection field is inert: bytes-fixed.cjs). Inside the intervals they differ by design (the lead's sense).
// (The first version read phaseDirection from nativeLunarSnapshot; after ba249a5e moved the authority out of it, that
//  version compared main with main and printed 4320/4320. Corrected here.)
// Usage (from the repository root): node tools/qa/r0041/scene-identity.cjs <mainPrecision.mjs> <mainIndex.html>
const fs=require('node:fs'),vm=require('node:vm');
const [mainPrec,mainHtml]=process.argv.slice(2);
const NL=String.fromCharCode(10);
function api(prec,html,native){const a=html.indexOf('const _RAD=Math.PI/180'),b=html.indexOf('// Galactic centre',a);
 const snap=html.slice(html.indexOf('function nativeLunarSnapshot('),html.indexOf(NL+'function renderMoon('));
 let dir='';if(native){const d0=html.indexOf('let _moonDirMemo=');if(d0<0)throw Error('candidate index lacks nativeLunarPhaseDirection');
  dir=html.slice(d0,html.indexOf(NL+'}'+NL,html.indexOf('function nativeLunarPhaseDirection('))+3);}
 let directed='';if(native){const f0=native.indexOf('function directedCalendarScene(');if(f0<0)throw Error('candidate runtime lacks directedCalendarScene');
  directed=native.slice(f0,native.indexOf(NL+' }'+NL,f0)+3);}
 const c={Math,Date,SIM:{},lat:24.47,lon:39.61,moonSky:{}};vm.createContext(c);
 vm.runInContext(html.slice(a,b)+html.match(/const MOON_SCALE_MIN=.*?;/)[0]+html.match(/const clamp\s*=.*?;/)[0]+snap+dir+prec+NL+directed+
  ';this.snap=nativeLunarSnapshot;this.scene='+(native?'directedCalendarScene':'nativeCalendarMoonScene')+';this.pq=phaseQuantum;this.cf=canonicalFraction;'+
  'this.dir=typeof nativeLunarPhaseDirection==="function"?(t,s)=>{moonSky={frac:s.frac,waxing:s.waxing,_epochMin:Math.floor(t.getTime()/60000)};return nativeLunarPhaseDirection();}:()=>({});',c);
 return c;}
const C=api(fs.readFileSync('moon/src/moon-precision.mjs','utf8'),fs.readFileSync('src/native/index.html','utf8'),fs.readFileSync('moon/src/moon-native.mjs','utf8'));
const M=api(fs.readFileSync(mainPrec,'utf8'),fs.readFileSync(mainHtml,'utf8'),null);
const mk=(A,t)=>{const s=A.snap(t,24.47,39.61,{}),D=109;
 const q={fraction:s.frac,waxing:s.waxing,...A.dir(t,s),timeScale:1,phaseDiameter:D,maximumPhaseDiameter:Math.ceil(D*1.13/(1.11+.02*s.up)),phaseQuantum:A.pq(D),physicalFraction:A.cf(s.frac,D)};
 const sc=A.scene(q,{});return JSON.stringify([sc.sun,sc.fraction,sc.waxing]);};
let same=0,directed=0;const diff=[];const start=Date.parse('2026-11-16T00:00:00Z');
for(let i=0;i<30*24*6;i++){const t=new Date(start+i*600000);const s=C.snap(t,24.47,39.61,{});if(C.dir(t,s).phaseDirection!=null)directed++;
 if(mk(M,t)===mk(C,t))same++;else diff.push(t.toISOString());}
if(directed===0)throw Error('vacuous: the candidate supplied no phaseDirection');
console.log(JSON.stringify({samples:30*24*6,candidateSamplesWithDirection:directed,identicalScenes:same,differentScenes:diff.length,differentAt:diff}));
