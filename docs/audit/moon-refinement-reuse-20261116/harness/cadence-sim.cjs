'use strict';
// Moon-reuse feasibility audit (2026-11-16): steady-state refinement cadence MODEL (no browser, no network).
// It loads the product's own lunar ephemeris (src/native/index.html L2064-2087: _toDays.._moonCoords, moonIllum,
// moonAltAz) and the product's precision constants (moon/src/moon-precision.mjs), and replays the host's poll
// decision (moon/src/moon-native.mjs L43-49 key/scope/phaseDrift, L166-187 poll) at the 250 ms poll period for one visible,
// never-hidden tab. Refinement durations are inputs (measured in determinism.json). This is a faithful re-
// implementation of the decision rule, not the product running: it is checked against live.cjs observations.
// Usage: node cadence-sim.cjs <repoRoot> <startISO> <days> <durationsJson> <outJson>
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const [root,startISO,daysArg,durArg,outFile]=process.argv.slice(2);
const html=fs.readFileSync(path.join(root,'src/native/index.html'),'utf8');
const grab=(from,to)=>{const a=html.indexOf(from),b=html.indexOf(to,a);if(a<0||b<0)throw new Error('anchor '+from);return html.slice(a,b);};
const astro=grab('const _RAD=Math.PI/180','// Galactic centre');
const prec=fs.readFileSync(path.join(root,'moon/src/moon-precision.mjs'),'utf8');
const ctx={Math,Date};vm.createContext(ctx);
vm.runInContext(astro+'\n'+prec+'\nthis.moonIllum=moonIllum;this.moonAltAz=moonAltAz;this._sunCoords=_sunCoords;this._toDays=_toDays;this._sid=_sid;this._RAD=_RAD;this.B=PHASE_POSITION_BUDGET;',ctx);
const {moonIllum,moonAltAz,_sunCoords,_toDays,_sid,_RAD,B}=ctx;
const LAT=24.47,LON=39.61;
function sunAlt(date){const d=_toDays(date),s=_sunCoords(d),lw=_RAD*-LON,ph=_RAD*LAT;const H=_sid(d,lw)-s.ra;return Math.asin(Math.sin(ph)*Math.sin(s.dec)+Math.cos(ph)*Math.cos(s.dec)*Math.cos(H))/_RAD;}
const durations=JSON.parse(durArg); // {engine:{renderMs, previewMs}}
const start=Date.parse(startISO),DAYS=+daysArg,STEP=250; // the host polls at 4 Hz (moon-native.mjs L344)
// Precompute ephemeris once per second.
const N=Math.round(DAYS*86400000/STEP),alpha=new Float64Array(N),wax=new Uint8Array(N),up=new Float32Array(N),sun=new Float32Array(N);
// The host's lunar snapshot (moonSky: frac, waxing, up) is refreshed at the native minute cadence (index.html L3841,
// renderMoon L2302-2314), so the poll sees a phase that steps once per (simulated) minute.
for(let i=0;i<N;i++){const t=new Date(Math.floor((start+i*STEP)/60000)*60000),il=moonIllum(t);alpha[i]=Math.acos(2*il.fraction-1);wax[i]=il.waxing?1:0;const aa=moonAltAz(t,LAT,LON);up[i]=Math.max(0,Math.min(1,(aa.alt+2)/6));sun[i]=sunAlt(t);}
let rate=[];for(let i=2400;i<N;i+=2400)rate.push(Math.abs(alpha[i]-alpha[i-2400])/(2400*STEP/1000));
const result={model:'moon-native poll replay',start:startISO,days:DAYS,location:'fixture Madinah 24.47,39.61 (only for day/below-horizon accounting and the up-dependent leading edge)',
  phaseRateRadPerS:{min:Math.min(...rate),max:Math.max(...rate),mean:rate.reduce((a,b)=>a+b,0)/rate.length},cases:{}};
const SCALE_MIN=1.11,SCALE_MAX=1.13;
for(const [engine,dur] of Object.entries(durations))for(const [dprLabel,Dcss] of Object.entries({dpr1:1,dpr2:2})){
  const baseRect=dur.rectCss; // css px of .mphoto at scale=SCALE_MIN+..*up, measured; scales with the group transform
  let accepted=null,pending=null,waitingPreview=null,events=[],busy=0,busyDay=0,busyBelow=0,refinedT=0,previewT=0,initialT=0,noneT=0,starts=0,startsDay=0,startsBelow=0,completes=0,cancels=0,scopeClears=0,expiries=0,initialRenders=0,lastWax=wax[0];
  const perDay=new Array(Math.ceil(DAYS)).fill(0);
  for(let i=0;i<N;i++){
    const tS=i*STEP/1000,w=wax[i]===1,scale=SCALE_MIN+(SCALE_MAX-SCALE_MIN)*up[i];
    const D=Math.ceil(baseRect*(scale/SCALE_MIN)*Dcss),ratio=SCALE_MAX/(SCALE_MIN+(SCALE_MAX-SCALE_MIN)*up[i]),Dmax=Math.ceil(D*Math.max(1,ratio));
    const drift=r=>D/2*(alpha[i]-r.alpha)*(w?-1:1),matches=r=>!!r&&Math.abs(drift(r))<=B;
    if(wax[i]!==lastWax){lastWax=wax[i];accepted=null;pending=null;waitingPreview=null;scopeClears++;} // waxing is in scope(): clear()
    if(pending&&!matches(pending)){pending=null;waitingPreview=null;cancels++;}
    if(pending&&tS>=pending.previewAt&&!pending.previewDone){pending.previewDone=true;waitingPreview={alpha:pending.alpha,tier:'preview'};}
    if(pending&&tS>=pending.doneAt){if(matches(pending)){accepted={alpha:pending.alpha,tier:'refined'};completes++;}pending=null;waitingPreview=null;}
    if(accepted&&!matches(accepted)){expiries++;accepted=null;if(waitingPreview&&matches(waitingPreview)){accepted=waitingPreview;waitingPreview=null;}}
    // initialPresentation() (moon-native.mjs L143-161): the initial V5 tier, rendered on the MAIN thread for the
    // same leading-edge scene as the worker job (L146: geometry = scene(s)).
    // It is withheld while initialWarranted is false (_skyMoonPresence = clamp(darkness*1.8) = 0 for solar e >= -3 deg,
    // index.html L3241-3243, L4696); the slot then has no presentation at all ('none').
    if(!accepted&&sun[i]<-3){accepted={alpha:Math.max(0,Math.min(Math.PI,alpha[i]+(w?-1:1)*(2*B/Dmax)*(1-1e-9))),tier:'initial'};initialRenders++;}
    const tier=accepted?accepted.tier:'none';
    if(!(pending&&matches(pending))&&!(accepted&&accepted.tier!=='initial'&&drift(accepted)<B/4)){
      const a=Math.max(0,Math.min(Math.PI,alpha[i]+(w?-1:1)*(2*B/Dmax)*(1-1e-9)));
      pending={alpha:a,startAt:tS,previewAt:tS+dur.previewMs/1000,doneAt:tS+dur.renderMs/1000,previewDone:false};starts++;perDay[Math.floor(tS/86400)]++;
      if(sun[i]>=-3)startsDay++;if(up[i]===0)startsBelow++;
    }
    if(pending){busy++;if(sun[i]>=-3)busyDay++;if(up[i]===0)busyBelow++;}
    if(tier==='refined')refinedT++;else if(tier==='preview')previewT++;else if(tier==='initial')initialT++;else noneT++;
  }
  result.cases[engine+'-'+dprLabel]={renderMs:dur.renderMs,previewMs:dur.previewMs,rectCss:baseRect,
    rendersStarted:starts,rendersPerDayList:perDay,rendersPerDay:{median:[...perDay].sort((a,b)=>a-b)[Math.floor(perDay.length/2)],mean:starts/DAYS,min:Math.min(...perDay.slice(0,Math.floor(DAYS))),max:Math.max(...perDay.slice(0,Math.floor(DAYS)))},meanIntervalS:DAYS*86400/starts,
    completed:completes,mainThreadInitialRenders:initialRenders,cancelledPending:cancels,acceptedExpiries:expiries,waxingFlipClears:scopeClears,
    workerBusyFraction:busy/N,busyWhileDaySuppressedFraction:busy?busyDay/busy:0,busyWhileBelowHorizonFraction:busy?busyBelow/busy:0,
    startsWhileDaySuppressed:startsDay,startsWhileBelowHorizon:startsBelow,
    visibleTierFraction:{refined:refinedT/N,preview:previewT/N,initial:initialT/N,none:noneT/N},
    estWorkerCpuSecondsPerDay_4shards:4*busy*STEP/1000/DAYS};
}
fs.writeFileSync(outFile,JSON.stringify(result,null,1));console.log(JSON.stringify(result,null,1));
