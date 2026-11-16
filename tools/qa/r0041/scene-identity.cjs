'use strict';
// R0041 (R41-PIX, VM part): compare the refinement scene (Sun vector and fraction: the only inputs that change refined
// and initial V5 bytes) produced by main 47faae32 and by the candidate, every 10 minutes over 30 days, with the
// product's own snapshot. Outside the waxing/phase-direction mismatch intervals the scenes must be identical, so the
// refined and initial surfaces are byte-identical by construction (the worker is a pure function of the scene).
// Usage (from the repository root): node tools/qa/r0041/scene-identity.cjs <mainPrecision.mjs> <mainIndex.html>
const fs=require('node:fs'),vm=require('node:vm');
const [mainPrec,mainHtml]=process.argv.slice(2);
function api(prec,html){const a=html.indexOf('const _RAD=Math.PI/180'),b=html.indexOf('// Galactic centre',a);
 const snap=html.slice(html.indexOf('function nativeLunarSnapshot('),html.indexOf('\nfunction renderMoon('));
 const c={Math,Date};vm.createContext(c);
 vm.runInContext(html.slice(a,b)+html.match(/const MOON_SCALE_MIN=.*?;/)[0]+html.match(/const clamp\s*=.*?;/)[0]+snap+prec+';this.snap=nativeLunarSnapshot;this.scene=nativeCalendarMoonScene;this.pq=phaseQuantum;this.cf=canonicalFraction;',c);return c;}
const M=api(fs.readFileSync(mainPrec,'utf8'),fs.readFileSync(mainHtml,'utf8')),C=api(fs.readFileSync('moon/src/moon-precision.mjs','utf8'),fs.readFileSync('src/native/index.html','utf8'));
const mk=(A,t)=>{const s=A.snap(t,24.47,39.61,{}),D=109;const q={fraction:s.frac,waxing:s.waxing,timeScale:1,phaseDiameter:D,maximumPhaseDiameter:Math.ceil(D*1.13/(1.11+.02*s.up)),phaseQuantum:A.pq(D),physicalFraction:A.cf(s.frac,D)};
 if(s.phaseDirection!=null)q.phaseDirection=s.phaseDirection;const sc=A.scene(q,{});return JSON.stringify([sc.sun,sc.fraction,sc.waxing]);};
let same=0;const diff=[];const start=Date.parse('2026-11-16T00:00:00Z');
for(let i=0;i<30*24*6;i++){const t=new Date(start+i*600000);if(mk(M,t)===mk(C,t))same++;else diff.push(t.toISOString());}
console.log(JSON.stringify({samples:30*24*6,identicalScenes:same,differentScenes:diff.length,differentAt:diff}));
