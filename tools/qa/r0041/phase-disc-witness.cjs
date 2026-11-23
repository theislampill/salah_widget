'use strict';
// R0041 (issue 143), owner decision of 2026-11-17: native witness for the receiver-independent phase disc.
// Native recipe; NOT part of the node glob. Same isolation (iso.cjs), same PNG decoder and the same disc classifier
// arithmetic as witness.cjs. One browser job at a time. Synthetic fixture only (lat 24.47, lon 39.61).
//
// Two page loads per run, both at REAL speed:
//  Load A  the embedded receiver does not decode (start-up failure) and the worker assets are withheld (404), so the
//          phase disc is the only presentation:
//            startup     judged from the first frame in which the sky is visible (stars in a control patch)
//            invalidate  SalahMoonRuntime.invalidate() x3
//            resume      hide 1 s, show, x3
//            pageshow    the back/forward lifecycle synthesised in spec order (pagehide persisted, hidden; 1 s; visible,
//                        pageshow persisted) x3. A real back/forward-cache restore is NOT driven here.
//          then the opacity triple (present, Moon layers hidden, present), then the assets are restored, the worker is
//          retried and the refined result replaces the phase disc (hand-over), then one more invalidation.
//  Load B  healthy start, settled refined Moon:
//            missing     the receiver is removed; invalidate x3 (refined -> phase disc -> refined)
//            exhausted   the receiver throws on every render; invalidate x3 spends the R0033 budget, then x3 more
//
// Pixel-side judgement. A frame is ABSENT when its disc region is more than 4 codes (mean |dY|) from BOTH references
// (phase disc, refined) or holds at least 10 star-like pixels. State flags are auxiliary.
// Fail closed: a cell is INVALID (never a pass) when the fault was not armed, the phase disc was not exercised after
// every forcing event, the disc region is empty or partial, a judged frame has no reference comparison, the deliberate
// hide is not classified absent, no star lies behind the disc in the hidden shot, a segment has too few frames, or the
// receiver was called outside the R0033 budget. --red runs the same recipe on a tree WITHOUT the phase disc (the
// control): rules about the phase disc are skipped and absence is expected.
// --loads=A|B|AB|H selects the loads (H: healthy start, receiver removed, ONE invalidation; reports only the hand-over
// step between the refined Moon and the phase disc for the scene of <startISO>). --short ends Load A after the opacity
// triple (no worker retry, no refined hand-over).
// Usage: node phase-disc-witness.cjs <repoRoot> <outJson> <engine> <dpr> <motion:reduce|full> <startISO> [runs=1] [cropDir] [--red] [--loads=..] [--short]
const fs=require('node:fs'),path=require('node:path');
const {createEnv,launch}=require('./iso.cjs');const {decodePng}=require('./png.cjs');
const argv=process.argv.slice(2),RED=argv.includes('--red'),SHORT=argv.includes('--short'),LOADS=(argv.find(a=>a.startsWith('--loads='))?.slice(8)??'AB').split(''),[root,outFile,engine,dpr,motion,startISO,runsArg,cropDir]=argv.filter(a=>!a.startsWith('--'));
// The Chromium screencast (every compositor frame) is the witness at pixel ratio 1. At other ratios its frames can
// arrive at CSS size, so device-scale screenshots are used there, as in Firefox and WebKit.
const CAST=engine==='chromium'&&+dpr===1;
const RUNS=+(runsArg||1),ASSETS=['/moon/assets/dem.bin.gz','/moon/assets/colour.bin.gz'];
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1'+(motion==='full'?'&motion=full':'');
const SHIFT=`(()=>{const ND=Date,off=${Date.parse(startISO)}-ND.now();class D extends ND{constructor(...a){super(...(a.length?a:[ND.now()+off]));}static now(){return ND.now()+off;}}window.Date=D;})();`;
// Per animation frame: [t, moon-ready, mask-on, current, source index, phase-disc renders, hidden]; a frame is logged
// when any flag changed or 8 ms have passed (headless Firefox runs animation frames every ~3 ms). While a burst is
// open (start-up, and 3 s after every forcing call) a 1 px marker in the card's bottom-right corner is recoloured on
// every animation frame, so the Chromium screencast delivers every compositor frame, not only frames that changed.
const SOURCES=['awaiting-terrain','initial-v5','terrain-preview','refined-terrain','phase-disc'];
const RAF=`(()=>{window.__pd={frames:[],receiverCalls:0};window.__pdBurst=performance.now()+8000;let mk=null,mn=0,m2=null;window.__pdMarkState=null;window.__pdMark=()=>{if(!m2){m2=document.createElement('div');m2.style.cssText='position:fixed;right:2px;bottom:0;width:2px;height:2px;z-index:2147483647;pointer-events:none';document.documentElement.appendChild(m2);}window.__pdMarkState=window.__pdMarkState===1?0:1;m2.style.background=window.__pdMarkState?'#00ff00':'#ff0000';window.__pdBurst=performance.now()+3000;};const S=${JSON.stringify(SOURCES)};const tick=t=>{const c=document.querySelector('.c'),m=document.querySelector('.moon-mask-disc');let o=null;try{o=window.SalahMoonRuntime?.observe?.()??null;}catch(e){}
 const rec=[Math.round(t*10)/10,c&&c.classList.contains('moon-ready')?1:0,m&&m.classList.contains('mask-on')?1:0,o?.current?1:0,S.indexOf(o?.state?.visibleSource),o?.state?.phaseDisc?.renders??-1,document.hidden?1:0],last=window.__pd.frames.at(-1);
 if(!last||rec[0]-last[0]>=8||rec.some((v,i)=>i&&v!==last[i]))window.__pd.frames.push(rec);if(performance.now()<window.__pdBurst&&document.documentElement){if(!mk){mk=document.createElement('div');mk.style.cssText='position:fixed;right:0;bottom:0;width:1px;height:1px;z-index:2147483647;pointer-events:none';document.documentElement.appendChild(mk);}mk.style.background=(mn++&1)?'#010101':'#020202';}requestAnimationFrame(tick);};requestAnimationFrame(tick);})();`;
// The embedded receiver payload starts with the "SMH1" magic; only that decode is refused.
const DECODE_FAULT=`(()=>{const a=window.atob;window.atob=function(s){if(typeof s==='string'&&s.startsWith('U01IMR'))throw new Error('r0041 witness: injected receiver decode failure');return a.call(this,s);};})();`;
const Y=(d,i)=>.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];
const median=a=>{const s=Array.from(a).sort((p,q)=>p-q);return s[s.length>>1]??0;};
// witness.cjs discOf, plus the outside ring and a sky control patch (stars there = the sky is visible). The patch
// (CSS x 20-110, y 50-110) is clear of the header buckle; the neutral pending card shows no star-like pixel in it.
function measure(img,rect){
  const scale=img.width/325,W=img.width,H=img.height,at=(x,y)=>x<0||y<0||x>=W||y>=H?null:Y(img.data,4*(y*W+x));
  const x0=Math.max(0,Math.floor(rect.x*scale)),y0=Math.max(0,Math.floor(rect.y*scale)),S=Math.floor(Math.min(rect.w,rect.h)*scale),cx=x0+S/2,cy=y0+S/2,disc=[],corner=[],pts=[],pos=[];
  const local=(x,y)=>{let m=0,n=0;for(const [dx,dy] of [[2,0],[-2,0],[0,2],[0,-2],[2,2],[2,-2],[-2,2],[-2,-2]]){const u=at(x+dx,y+dy);if(u!=null){m+=u;n++;}}return n?m/n:null;};
  for(let y=y0;y<y0+S&&y<H;y++)for(let x=x0;x<x0+S&&x<W;x++){const r=Math.hypot(x+.5-cx,y+.5-cy),v=at(x,y);
    if(r<=.47*S){disc.push(v);pos.push(r<=.47*S-3?1:0);const m=local(x,y);pts.push(r<=.47*S-3&&m!=null?v-m:0);}else if(r>=.53*S)corner.push(v);}
  const sky=median(corner),ctrl=[];let ctrlStars=0;
  for(let y=Math.floor(50*scale);y<Math.floor(110*scale);y++)for(let x=Math.floor(20*scale);x<Math.floor(110*scale);x++)ctrl.push(at(x,y));
  const cm=median(ctrl);let k=0;for(let y=Math.floor(50*scale);y<Math.floor(110*scale);y++)for(let x=Math.floor(20*scale);x<Math.floor(110*scale);x++){const v=ctrl[k++],m=local(x,y);if(m!=null&&v-m>12&&v>cm+12)ctrlStars++;}
  // The event marker (2x2 CSS px, recoloured in the SAME task as each forcing call): which side of the event a frame shows.
  const mi=4*(Math.min(H-1,Math.floor(529*scale))*W+Math.min(W-1,Math.floor(322*scale))),mk=img.data[mi]>200&&img.data[mi+1]<80?0:img.data[mi+1]>200&&img.data[mi]<80?1:null;
  return {mk,disc:Float32Array.from(disc),pts:Float32Array.from(pts),inner:Uint8Array.from(pos),corner:Float32Array.from(corner),sky,stars:disc.filter((v,i)=>pts[i]>30&&v>sky+30).length,ctrlStars,S,mean:disc.reduce((p,v)=>p+v,0)/Math.max(1,disc.length)};
}
const dist=(a,b)=>!a||!b||a.length!==b.length?null:a.reduce((p,v,i)=>p+Math.abs(v-b[i]),0)/a.length;
function step(a,b){ // presented state a -> presented state b, disc pixels
  if(!a||!b||a.disc.length!==b.disc.length)return null;let s=0,sa=0,max=0,o8=0,o16=0;
  for(let i=0;i<a.disc.length;i++){const d=b.disc[i]-a.disc[i],q=Math.abs(d);s+=d;sa+=q;max=Math.max(max,q);if(q>8)o8++;if(q>16)o16++;}
  const mean=x=>x.disc.reduce((p,v)=>p+v,0)/x.disc.length;
  return {pixels:a.disc.length,meanFrom:+mean(a).toFixed(2),meanTo:+mean(b).toFixed(2),shareOver16:+(100*o16/a.disc.length).toFixed(1),starLikeFrom:a.stars,starLikeTo:b.stars,meanStep:+(s/a.disc.length).toFixed(2),meanAbs:+(sa/a.disc.length).toFixed(2),max:+max.toFixed(1),over8:o8,over16:o16,ringMeanAbs:+dist(a.corner,b.corner).toFixed(2)};
}
const HIDE=()=>{window.__pdMark();const w=performance.timeOrigin+performance.now();Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'hidden'});document.dispatchEvent(new Event('visibilitychange',{bubbles:true}));return w;};
const SHOW=()=>{window.__pdMark();const w=performance.timeOrigin+performance.now();Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'visible'});document.dispatchEvent(new Event('visibilitychange',{bubbles:true}));return w;};
const PAGEHIDE=()=>{window.__pdMark();const w=performance.timeOrigin+performance.now();window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}));Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'hidden'});document.dispatchEvent(new Event('visibilitychange',{bubbles:true}));return w;};
const PAGESHOW=()=>{window.__pdMark();const w=performance.timeOrigin+performance.now();Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'visible'});document.dispatchEvent(new Event('visibilitychange',{bubbles:true}));window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}));return w;};
const INVALIDATE=()=>{window.__pdMark();const w=performance.timeOrigin+performance.now();window.SalahMoonRuntime.invalidate('r0041-phase-disc-witness');return w;};
const STATE=()=>{const o=window.SalahMoonRuntime?.observe?.(),s=o?.state;return s?{visibleSource:s.visibleSource,current:o.current,initialEligible:s.initialEligible,initialRetry:s.initialRetry,phaseDisc:s.phaseDisc??null,limitation:s.limitation??null,lastAdoption:s.lastAdoption??null,firstInitial:s.firstInitial??null,recovery:s.recovery,status:s.status,constructionError:window.SalahMoonConstructionError??null,initialError:window.SalahMoonInitialError??null,receiverCalls:window.__pd?.receiverCalls??0}:null;};

// qaState().moonTruth as the page reports it (the non-adopting diagnostic path, R0036).
const TRUTH=()=>{const t=window.qaState?.().moonTruth;return t?{limitation:t.limitation??null,slotState:t.slotState??null,reason:t.reason??null,displayMode:t.displayMode,surfaceStatus:t.surface?.status,moonlightOpacity:t.moonlightOpacity}:null;};
async function load(L,env,kind,run){
  const page=await L.context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e).slice(0,200)));
  if(kind==='A'){await page.addInitScript(DECODE_FAULT);for(const p of ASSETS)env.origins.policy[p]='404';}else for(const p of ASSETS)delete env.origins.policy[p];
  const raw=[],frames=[],kept={};let rect=null,cdp=null,capturing=true,busy=false;const t0=Date.now();
  // Frames are reduced to their disc measurement as they arrive; PNG bytes are kept only for named crops.
  const drain=()=>{if(busy||!rect)return;busy=true;try{while(raw.length){const s=raw.shift();let img;try{img=decodePng(s.png);}catch(e){continue;}const m=measure(img,rect);frames.push({t:s.t,done:s.done??s.t,tag:s.tag??null,disc:Uint8ClampedArray.from(m.disc),stars:m.stars,ctrlStars:m.ctrlStars,S:m.S,mean:m.mean,mk:m.mk,png:frames.length<60?s.png:null});if(s.tag)kept[s.tag]={png:s.png,m};}}finally{busy=false;}};
  if(CAST){cdp=await L.context.newCDPSession(page);
    cdp.on('Page.screencastFrame',async f=>{raw.push({t:f.metadata.timestamp*1000,done:f.metadata.timestamp*1000,png:Buffer.from(f.data,'base64')});try{await cdp.send('Page.screencastFrameAck',{sessionId:f.sessionId});}catch(e){}drain();});}
  await page.goto(`http://127.0.0.1:${env.origins.ports['127.0.0.1']}/index.html${FRAG}`,{waitUntil:'commit',timeout:120000});
  if(cdp)await cdp.send('Page.startScreencast',{format:'png',everyNthFrame:1,maxWidth:Math.round(325*+dpr),maxHeight:Math.round(530*+dpr)});
  const shot=async tag=>{const t=Date.now();const png=await page.screenshot({scale:'device',animations:'allow',caret:'initial'});raw.push({t,done:Date.now(),png,tag});drain();};
  const loop=(async()=>{if(cdp)return;while(capturing){try{await shot(null);}catch(e){await page.waitForTimeout(20);}}})();
  // The Moon's rectangle is native geometry (set by the first native paint), independent of any Moon renderer.
  await page.waitForFunction(()=>{const g=document.querySelector('.moon'),r=document.querySelector('.mphoto')?.getBoundingClientRect();return g&&g.getAttribute('transform')!=='translate(250 64) scale(0.62)'&&r&&r.width>0;},null,{timeout:60000,polling:50});
  rect=await page.evaluate(()=>{const r=document.querySelector('.mphoto').getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height};});drain();
  const events=[];
  // Screencast timestamps share the page wall clock; screenshots are timed on this process's
  // clock, so their event instant is this clock when the forcing call has returned (as in witness.cjs).
  const ev=async (route,name,fn)=>{const idx=await page.evaluate(()=>window.__pd.frames.length),wall=await page.evaluate(fn);events.push({route,name,wall:CAST?wall:Date.now(),pageWall:wall,rafIndex:idx,mark:await page.evaluate(()=>window.__pdMarkState),state:await page.evaluate(STATE)});};
  const tagged=async tag=>{if(cdp){await page.waitForTimeout(120);}await shot(tag);};
  const out={kind,errors,events,notes:[]};
  if(kind==='A'){
    await page.waitForFunction(RED?()=>!!window.SalahMoonRuntime&&document.querySelector('.c')?.classList.contains('real-sky-preview-ready'):()=>window.SalahMoonRuntime?.observe?.().state?.visibleSource==='phase-disc',null,{timeout:90000,polling:100}).catch(()=>out.notes.push('start-up wait timed out'));
    await page.waitForTimeout(3000);out.armed=await page.evaluate(STATE);out.settleWall=CAST?await page.evaluate(()=>performance.timeOrigin+performance.now()):Date.now();
    out.reportPresented=await page.evaluate(TRUTH);
    await tagged('refPD');
    for(let k=0;k<3;k++){await ev('invalidate','invalidate',INVALIDATE);await page.waitForTimeout(4000);}
    for(let k=0;k<3;k++){await ev('resume','hide',HIDE);await page.waitForTimeout(k?1000:700);if(!k){out.reportHidden=await page.evaluate(TRUTH);await page.waitForTimeout(300);}await ev('resume','resume',SHOW);await page.waitForTimeout(4000);}
    for(let k=0;k<3;k++){await ev('pageshow','hide',PAGEHIDE);await page.waitForTimeout(1000);await ev('pageshow','resume',PAGESHOW);await page.waitForTimeout(4000);}
    // Opacity triple: stars are located in the shot with the Moon layers hidden and read back in the present shots.
    await ev('opacity','opacity-begin',()=>performance.timeOrigin+performance.now());
    await tagged('present1');
    await page.addStyleTag({content:'.moon-detail-canvas,.sky .moon{visibility:hidden!important}'}).then(h=>h.evaluate(n=>n.id='r41-hide'));
    await page.waitForTimeout(400);await tagged('hidden');
    await page.evaluate(()=>document.getElementById('r41-hide')?.remove());await page.waitForTimeout(400);await tagged('present2');
    await ev('opacity','opacity-end',()=>performance.timeOrigin+performance.now());
    out.renderMs=await page.evaluate(()=>{const s=window.SalahMoonRuntime?.observe?.().state;return s?{phaseDisc:s.phaseDisc?.lastMs??null,adoptionTotal:s.lastAdoption?.totalMs??null,adoptionPrefix:s.lastAdoption?.prefixMs??null,source:s.lastAdoption?.source??null}:null;});
    if(!SHORT){
    // Restore the assets and retry the worker: the refined result replaces the phase disc.
    for(const p of ASSETS)delete env.origins.policy[p];
    await ev('handover','retry',()=>{const w=performance.timeOrigin+performance.now();window.SalahMoonRuntime.retry();return w;});
    const refined=await page.waitForFunction(()=>window.SalahMoonRuntime?.observe?.().state?.visibleSource==='refined-terrain',null,{timeout:200000,polling:100}).then(()=>true).catch(()=>false);
    if(!refined)out.notes.push('refined result did not arrive after retry');
    await ev('handover','refined',()=>performance.timeOrigin+performance.now());await page.waitForTimeout(3000);await tagged('refRefined');
    await ev('refinedInvalidate','invalidate',INVALIDATE);await page.waitForTimeout(7000);
    }
  }else{
    const refined=await page.waitForFunction(()=>window.SalahMoonRuntime?.observe?.().state?.visibleSource==='refined-terrain',null,{timeout:240000,polling:250}).then(()=>true).catch(()=>false);
    if(!refined)out.notes.push('healthy start did not reach the refined Moon');
    await page.waitForTimeout(3000);out.settleWall=CAST?await page.evaluate(()=>performance.timeOrigin+performance.now()):Date.now();await tagged('refRefined');
    // The V5 initial tier's own render time for comparison (rendered by the first-paint head on a healthy start).
    out.initialRenderMs=await page.evaluate(()=>{const f=window.SalahMoonRuntime?.observe?.().state?.firstInitial;return f?(f.headHandoff?f.headRenderMs:f.renderMs)??null:null;});
    await page.evaluate(()=>{window.__pdKeep=window.SalahMoonInitial;window.SalahMoonInitial=null;});out.armed=await page.evaluate(STATE);
    for(let k=0;k<(kind==='H'?1:3);k++){await ev('missing','invalidate',INVALIDATE);if(k===0){await page.waitForTimeout(CAST?350:150);await tagged('refPD');}await page.waitForTimeout(6000);}
    out.renderMs=await page.evaluate(()=>{const s=window.SalahMoonRuntime?.observe?.().state;return s?{phaseDisc:s.phaseDisc?.lastMs??null}:null;});
    if(kind!=='H'){
    await page.evaluate(()=>{const k=window.__pdKeep;window.SalahMoonInitial={identity:k.identity,render(){window.__pd.receiverCalls++;throw new Error('r0041 witness: injected receiver failure');}};});
    for(let k=0;k<3;k++){await ev('exhausted','invalidate',INVALIDATE);await page.waitForTimeout(6000);}
    out.armedExhausted=await page.evaluate(STATE);
    for(let k=0;k<3;k++){await ev('exhausted','invalidate',INVALIDATE);await page.waitForTimeout(6000);}
    out.endState=await page.evaluate(STATE);
    }
  }
  capturing=false;await loop;if(cdp)await cdp.send('Page.stopScreencast').catch(()=>{});await page.waitForTimeout(200);drain();
  out.raf=await page.evaluate(()=>window.__pd.frames);out.perfOrigin=await page.evaluate(()=>performance.timeOrigin);out.endState??=await page.evaluate(STATE);
  await page.close();
  return {...out,frames:frames.sort((a,b)=>a.t-b.t),kept,rect,t0};
}

function judge(r,run){
  const res={kind:r.kind,invalid:[],routes:{},notes:r.notes,pageErrors:r.errors};const bad=x=>res.invalid.push(x);
  const refPD=r.kept.refPD?.m??null,refR=r.kept.refRefined?.m??null;
  if(!r.frames.length){bad('no frames');return res;}
  const S=r.frames[0].S,need=.9*Math.PI*(.47*S)**2;if(r.frames.some(f=>f.disc.length<need))bad('empty or partial disc region');
  if(!RED&&!refPD)bad('no phase-disc reference');if(r.kind!=='A'&&!refR)bad('no refined reference');
  // The phase-disc reference must itself be a Moon (not a blank) and must differ from the refined one.
  if(refPD&&refR){const d=dist(refPD.disc,refR.disc);res.referenceDistance=+d.toFixed(2);if(!RED&&(refPD.stars>=10||Math.abs(refPD.mean-refR.mean)>12||d<.5))bad('phase-disc reference is not a distinct presented Moon');}
  const classify=f=>{const dP=RED?null:dist(f.disc,refPD?.disc),dR=dist(f.disc,refR?.disc),ds=[dP,dR].filter(v=>v!=null);return {dP,dR,none:!ds.length,absent:f.stars>=10||(ds.length>0&&Math.min(...ds)>4)};};
  const J=r.frames.map(f=>({t:f.t,done:f.done,tag:f.tag,mk:f.mk,mean:f.mean,stars:f.stars,ctrlStars:f.ctrlStars,png:f.png,...classify(f)}));
  // ATTRIBUTION RULE. A capture belongs to an event when it SHOWS THAT EVENT'S MARKER (the marker is recoloured in the
  // same task as the forcing call, so the capture shows the post-event document), it was completed at or after the call
  // and it was requested before the next event. The request instant is NOT required to follow the call: a screenshot
  // requested a few milliseconds before the forcing call returned and completed after it shows the post-event page and
  // counts (review 2, R2-3; the earlier rule dropped exactly those captures). A capture timed after the call that still
  // shows the previous marker is a frame composed before the call (counted separately as preEventFrames, not judged).
  // straddling = counted captures whose request preceded the call.
  const segment=(from,to,label,mark)=>{const timed=J.filter(f=>f.t>=from&&f.t<to&&!f.tag),fr=mark==null?timed:J.filter(f=>!f.tag&&f.mk===mark&&f.done>=from&&f.t<to),abs=fr.filter(f=>f.absent);let max=0,open=null;
    for(const f of fr){if(f.absent&&open==null)open=Math.max(from,f.t);if(!f.absent&&open!=null){max=Math.max(max,f.done-open);open=null;}}if(open!=null)max=Math.max(max,to-open);
    if(fr.some(f=>f.none))bad(label+': frames without a reference comparison');
    return {frames:fr.length,preEventFrames:mark==null?0:timed.filter(f=>f.mk!==mark).length,straddling:mark==null?0:fr.filter(f=>f.t<from).length,blank:abs.length,blankAt:abs.slice(0,4).map(f=>[Math.round(f.t-from),Math.round(f.done-from)]),maxAbsentMs:Math.round(max),minMean:fr.length?+Math.min(...fr.map(f=>f.mean)).toFixed(1):null};};
  const E=r.events,minFrames=CAST?20:5;
  const routeOf=name=>{const forcing=E.filter(e=>e.route===name&&(e.name==='invalidate'||e.name==='resume'));if(!RED&&forcing.some(e=>e.mark==null))bad(name+': event marker missing');const o={events:forcing.length,blank:0,maxAbsentMs:0,frames:0,eventsWithBlank:0,exercised:0};
    for(const e of forcing){const i=E.indexOf(e),end=Math.min((E[i+1]?.wall??Infinity)-30,e.wall+4000),s=segment(e.wall,end,name,e.mark);o.frames+=s.frames;o.preEventFrames=(o.preEventFrames??0)+s.preEventFrames;o.straddling=(o.straddling??0)+s.straddling;if(s.blank)(o.blankAt??=[]).push(s.blankAt);o.blank+=s.blank;o.maxAbsentMs=Math.max(o.maxAbsentMs,s.maxAbsentMs);if(s.blank)o.eventsWithBlank++;
      if(s.frames<minFrames)bad(name+': too few frames after an event ('+s.frames+')');
      // exercised: an animation frame within 3 s of the forcing call reports the phase disc as the current
      // source, and the phase-disc render count rose above its value before the call
      // (by record order: an animation-frame timestamp is the frame's begin time and can precede a task that ran before it)
      const t=e.pageWall-r.perfOrigin,prior=r.raf[e.rafIndex-1],win=r.raf.slice(e.rafIndex).filter(x=>x[0]<t+3000);
      if(win.some(x=>x[4]===4&&x[3]===1)&&prior&&Math.max(...win.map(x=>x[5]))>prior[5])o.exercised++;}
    if(!forcing.length)bad(name+': no forced event');if(!RED&&o.exercised!==forcing.length)bad(name+': the phase disc was not exercised after every event ('+o.exercised+'/'+forcing.length+')');
    return o;};
  // hidden intervals must classify absent (the classifier sees a withdrawn Moon)
  for(const e of E.filter(e=>e.name==='hide')){const i=E.indexOf(e),inside=J.filter(f=>f.t>=e.wall+60&&f.done<(E[i+1]?.wall??Infinity)-60&&!f.tag&&(e.mark==null||f.mk===e.mark));if(inside.length&&!inside.some(f=>f.absent))bad('hidden state not classified absent');}
  if(r.kind==='A'){
    if(!RED){const a=r.armed;if(!a||a.constructionError!=null||a.initialError==null||a.initialEligible!==false||a.initialRetry?.state!=='permanent'||a.visibleSource!=='phase-disc')bad('fault not armed (start-up decode failure)');
      // The report on the diagnostic path: no limitation while presented or hidden; the disc is named as a phase disc.
      const p=r.reportPresented,h=r.reportHidden;res.report={presented:p,hidden:h};
      if(!p||p.limitation!==null||p.slotState!=='presented'||p.surfaceStatus!=='phase-disc')bad('report while presented: '+JSON.stringify(p));
      if(!h||h.limitation!==null||h.slotState!=='withheld-hidden-or-paused'||/no truthful Moon/.test(h.reason??''))bad('report while hidden: '+JSON.stringify(h));}
    // start-up: from the first frame with a visible sky to the settle instant
    const firstSky=J.find(f=>f.ctrlStars>=3),sk=firstSky?segment(firstSky.t,r.settleWall,'startup'):null;
    if(!firstSky)bad('startup: the sky control patch never shows stars');
    const early=J.filter(f=>f.t<r.settleWall&&!f.tag).slice(0,60);res.startupLog=early.map(f=>[Math.round(f.t-early[0].t),f.absent?1:0,f.ctrlStars,f.stars,+f.mean.toFixed(1),f.dP==null?null:+f.dP.toFixed(1)]);
    {const a=early.find(f=>f.absent&&f.ctrlStars>=3&&f.png);if(a&&cropDir){fs.mkdirSync(cropDir,{recursive:true});fs.writeFileSync(path.join(cropDir,`${RED?'red-':''}${engine}-dpr${dpr}-${motion}-run${run}-startup-first-absent.png`),a.png);}}
    res.routes.startup={events:1,firstSkyMs:firstSky?Math.round(firstSky.t-r.t0):null,frames:sk?.frames??0,blank:sk?.blank??0,maxAbsentMs:sk?.maxAbsentMs??0,framesBeforeSky:firstSky?J.filter(f=>f.t<firstSky.t).length:J.length};
    if(sk&&sk.frames<(CAST?10:2))bad('startup: too few frames with a visible sky ('+sk.frames+')');
    for(const n of ['invalidate','resume','pageshow'])res.routes[n]=routeOf(n);
    // opacity triple
    const p1=r.kept.present1,h=r.kept.hidden,p2=r.kept.present2;
    if(!p1||!h||!p2)bad('opacity triple incomplete');else{
      const behind=[];for(let i=0;i<h.m.disc.length;i++)if(h.m.inner[i]&&h.m.pts[i]>12&&h.m.disc[i]>h.m.sky+12)behind.push(i);
      const through=behind.filter(i=>p1.m.pts[i]>8||p2.m.pts[i]>8).length,hc=classify(h.m);
      res.opacity={starsBehind:behind.length,starsThrough:through,hiddenClassifiedAbsent:hc.absent,hiddenDistance:hc.dP==null?null:+hc.dP.toFixed(2),starLikeInPresent:[p1.m.stars,p2.m.stars]};
      if(!hc.absent)bad('the deliberate hide was not classified absent');if(behind.length<1)bad('no star behind the disc in the hidden shot (opacity not proven)');}
    // hand-over, phase disc <-> refined, and the refined -> phase disc -> refined invalidation
    res.handover=step(refPD,refR);const ri=E.find(e=>e.route==='refinedInvalidate');
    if(ri){const s=segment(ri.wall,ri.wall+6500,'refinedInvalidate',ri.mark);res.routes.refinedInvalidate={events:1,...s,phaseDiscAfterEvent:ri.state?.visibleSource==='phase-disc'};}
    const rt=E.find(e=>e.name==='retry'),rf=E.find(e=>e.name==='refined');if(rt&&rf){const s=segment(rt.wall,rf.wall+2500,'handover');res.routes.handover={events:1,...s,waitMs:Math.round(rf.wall-rt.wall)};}
    res.renderMs=r.renderMs;
  }else{
    if(!RED){const a=r.armed;if(!a||a.constructionError!=null||a.initialEligible!==false)bad('fault not armed (receiver removed)');
      const x=r.armedExhausted;if(r.kind==='B')if(!x||x.initialRetry?.state!=='exhausted'||x.receiverCalls!==3)bad('fault not armed (budget not exhausted: '+JSON.stringify(x?.initialRetry)+', calls '+x?.receiverCalls+')');
      if(r.kind==='B'&&r.endState?.receiverCalls!==3)bad('receiver called outside the R0033 budget ('+r.endState?.receiverCalls+')');}
    for(const n of r.kind==='H'?['missing']:['missing','exhausted'])res.routes[n]=routeOf(n);
    res.handover=step(refR,refPD);res.renderMs=r.renderMs;res.initialRenderMs=r.initialRenderMs;res.receiverCalls=r.endState?.receiverCalls??null;
  }
  // Auxiliary state view: animation frames that began without a current Moon while the document was visible, after settle.
  const vis=r.raf.filter(x=>x[0]+r.perfOrigin>=r.settleWall&&!x[6]);res.raf={frames:vis.length,notCurrent:vis.filter(x=>!x[3]).length,moonReadyOff:vis.filter(x=>!x[1]).length,phaseDiscFrames:vis.filter(x=>x[4]===4).length};
  res.totalFrames=J.length;res.valid=res.invalid.length===0;res.invalid=[...new Set(res.invalid)];
  if(cropDir&&run===0){fs.mkdirSync(cropDir,{recursive:true});for(const [k,v] of Object.entries(r.kept))fs.writeFileSync(path.join(cropDir,`${RED?'red-':''}${engine}-dpr${dpr}-${motion}-load${r.kind}-${k}.png`),v.png);}
  return res;
}

(async()=>{
  const env=await createEnv({root});const out={engine,dpr:+dpr,motion,startISO,fragment:FRAG,red:RED,runs:[]};
  let L=null;
  try{
    L=await launch(env,{engine,mode:'route',deviceScaleFactor:+dpr,reducedMotion:motion==='full'?'no-preference':'reduce'});
    await L.context.addInitScript(SHIFT);await L.context.addInitScript(RAF);
    for(let run=0;run<RUNS;run++)for(const kind of LOADS){
      const r=await load(L,env,kind,run),j=judge(r,run);out.runs.push({run,...j});
      console.log(engine,dpr,motion,'run',run,'load',kind,j.valid?'VALID':'INVALID '+JSON.stringify(j.invalid),JSON.stringify(j.routes),'opacity',JSON.stringify(j.opacity??null),'handover',JSON.stringify(j.handover??null),'renderMs',JSON.stringify(j.renderMs??null));
    }
  }catch(e){out.error=String(e&&e.message||e).replace(/[A-Za-z]:[\\/][^\s'"]+/g,'<path>');console.error(out.error);}
  finally{try{await L?.close();}catch(e){}}
  out.isolation=env.finish();
  const all=fs.existsSync(outFile)?JSON.parse(fs.readFileSync(outFile,'utf8')):{};all[[RED?'red':'candidate',engine,dpr,motion,startISO].join('|')]=out;fs.writeFileSync(outFile,JSON.stringify(all,null,1));
  console.log('isolation allowed',out.isolation.allowedExternal,JSON.stringify(out.isolation.totalRequests));
})().catch(e=>{console.error(e);process.exit(1);});
