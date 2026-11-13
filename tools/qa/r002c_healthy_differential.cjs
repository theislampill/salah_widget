'use strict';
// R002C R2C-10: healthy (no-fault) behaviour is unchanged. Runs the same scene matrix through the
// repository VM harness (tests/r001d-harness.cjs) for a BASELINE and a CANDIDATE generated index.html
// and compares the final state byte for byte: every written element's text/HTML/dataset, every
// style property, attribute and class write (instrumented at the element double), the star and glint
// pools, the receipts and the complete qaState() (minus the one field R002C adds, renderFaults, which
// must be empty on the candidate). No network (the harness denies it; prayer data is its fixture),
// no storage, no file writes. This is DOM/state evidence, not pixels: R2C-14 is the native pixel gate.
// Usage: node tools/qa/r002c_healthy_differential.cjs <baseline index.html> <candidate index.html>
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {load}=require(path.join(__dirname,'..','..','tests','r001d-harness.cjs'));
const [baselinePath,candidatePath]=process.argv.slice(2).map(p=>path.resolve(p));
if(!baselinePath||!candidatePath){console.error('usage: r002c_healthy_differential.cjs <baseline> <candidate>');process.exit(2);}
const RIYADH='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&seed=1';
const utc=hm=>{const [h,m]=hm.split(':').map(Number);return Date.UTC(2026,8,8,h-3,m);};   // Riyadh is UTC+3
const SCENES=[
  ['night with Moon (frozen simTime)',RIYADH+'&simTime=22:00&simMoon=0.5&simWax=1&simMoonAlt=20&simMoonH=42',{at:'22:00'}],
  ['crescent Moon',RIYADH+'&simTime=21:00&simMoon=0.08&simWax=1&simMoonAlt=20&simMoonH=42',{at:'21:00'}],
  ['clear day apex',RIYADH+'&simTime=12:30',{at:'12:30'}],
  ['sunrise',RIYADH+'&simTime=05:50',{at:'05:50'}],
  ['sunset',RIYADH+'&simTime=18:55',{at:'18:55'}],
  ['overcast',RIYADH+'&simTime=12:30&simWx=3&simCloud=100',{at:'12:30'}],
  ['broken cloud',RIYADH+'&simTime=16:00&simWx=2&simCloud=50',{at:'16:00'}],
  ['rain',RIYADH+'&simTime=14:00&simWx=63',{at:'14:00'}],
  ['thunder',RIYADH+'&simTime=14:00&simWx=95&simPrecip=5',{at:'14:00'}],
  ['fog',RIYADH+'&simTime=06:30&simWx=45',{at:'06:30'}],
  ['no timetable (no-model)',RIYADH+'&simTime=22:00',{at:'22:00',noModel:true}],
  ['sim-invalid scene',RIYADH+'&simTime=22:00',{at:'22:00',simInvalid:true}],
  ['timeScale fast-forward',RIYADH+'&simTime=12:00&timeScale=1800',{at:'12:00',timeScale:1800}],
  ['real-time 1x',RIYADH,{at:'22:00',timeScale:1}],
];
function instrument(el){
  if(!el||el.__r2c)return;el.__r2c=true;el.__st=new Map();el.__at=new Map();el.__cl=new Map();
  const st=el.style,sp=st.setProperty,rp=st.removeProperty,sa=el.setAttribute,ra=el.removeAttribute,cl=el.classList;
  st.setProperty=function(k,v){el.__st.set(k,String(v));return sp.call(this,k,v);};
  st.removeProperty=function(k){el.__st.set(k,null);return rp.call(this,k);};
  el.setAttribute=function(k,v){el.__at.set(k,String(v));return sa.call(this,k,v);};
  el.removeAttribute=function(k){el.__at.set(k,null);return ra.call(this,k);};
  const add=cl.add,rem=cl.remove,tog=cl.toggle;
  cl.add=function(...s){s.forEach(v=>el.__cl.set(v,true));return add.apply(this,s);};
  cl.remove=function(...s){s.forEach(v=>el.__cl.set(v,false));return rem.apply(this,s);};
  cl.toggle=function(s,on){el.__cl.set(s,!!on);return tog.call(this,s,on);};
}
const PLAIN_STYLE=['display','opacity','width','visibility','transition','fontSize','top','marginBottom','transform'];
function elementState(el){
  return {text:el.textContent,html:el._html,dataset:{...el.dataset},hidden:el.hidden??null,
    style:[...el.__st].sort(),plain:PLAIN_STYLE.map(k=>[k,el.style[k]??null]),attrs:[...el.__at].sort(),classes:[...el.__cl].sort()};
}
const STAR_POOLS='typeof _glintEls!=="undefined"?[..._starEls,..._glintEls]:[..._starEls]';
function runScene(sourcePath,[name,hash,o]){
  const h=load({source:fs.readFileSync(sourcePath,'utf8'),hash});
  const set=h.elements.set.bind(h.elements);
  h.elements.set=(k,el)=>{instrument(el);return set(k,el);};
  for(const el of h.elements.values())instrument(el);
  for(const el of h.run(STAR_POOLS))instrument(el);
  h.run(`_simBase=${utc(o.at)};_simTz=tz;_rafT0=0;TIMESCALE=${o.timeScale||0};ADVANCING=${(o.timeScale||0)>1};`
    +(/simWx=/.test(hash)?'startWeather(true);':'')+(o.noModel?'today=null;tomorrow=null;lastDate=null;':'')+(o.simInvalid?'_simValid=false;_simInvalidTz=tz;':''));
  h.run('render()');
  h.clock.now+=1000;h.clock.wall+=1000;h.run('render()');
  h.run('startRenderLoop()');
  for(let i=0;i<4;i++){h.clock.now+=1000;h.clock.wall+=1000;h.advanceFrame();}
  const elements={};for(const [k,el] of [...h.elements].sort((a,b)=>a[0]<b[0]?-1:1))elements[k]=elementState(el);
  const stars=h.run(STAR_POOLS).map(elementState);
  const qa=JSON.parse(h.run('JSON.stringify(qaState())'));const faults=qa.renderFaults;delete qa.renderFaults;
  const receipts=JSON.parse(h.run('JSON.stringify({lastRender:_lastRender,moonSky,lastMoonMin,moonPaint:_lastMoonPaint&&{status:_lastMoonPaint.status,stage:_lastMoonPaint.stage,fresh:_lastMoonPaint.fresh},starKey:_starProjectionKey,starsProjected:_starsProjected,dateTruth:_lastDateTruth,cloudDirty:_cloudDirty,pending:null})'));
  return {snapshot:JSON.stringify({elements,stars,qa,receipts,warnings:h.warnings,pendingFrames:h.rafs.length}),faults,elementCount:Object.keys(elements).length};
}
let failures=0;const rows=[];
for(const scene of SCENES){
  const a=runScene(baselinePath,scene),b=runScene(candidatePath,scene);
  const equal=a.snapshot===b.snapshot,noFaults=b.faults!=null&&Object.keys(b.faults).length===0;
  if(!equal||!noFaults)failures++;
  let firstDiff=null;
  if(!equal){const x=a.snapshot,y=b.snapshot;let i=0;while(i<x.length&&x[i]===y[i])i++;firstDiff={at:i,baseline:x.slice(Math.max(0,i-120),i+120),candidate:y.slice(Math.max(0,i-120),i+120)};}
  rows.push({scene:scene[0],identical:equal,candidateFaults:b.faults,elements:b.elementCount,bytes:b.snapshot.length,...(firstDiff?{firstDiff}:{})});
}
const sha=p=>require('node:crypto').createHash('sha256').update(fs.readFileSync(p)).digest('hex');
console.log(JSON.stringify({baselineSha256:sha(baselinePath),candidateSha256:sha(candidatePath),scenes:rows.length,failures,rows},null,1));
process.exitCode=failures?1:0;
