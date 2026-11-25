'use strict';
// R0041 (issue 143), owner decision 2026-11-22 (G8): the synchronous cost of composing the Moon in the restoring event
// task. Native recipe; NOT part of the node glob. Headless, launch through iso.cjs, synthetic fixture, real speed.
// For one tree and engine: healthy start; then, five times each,
//   back/forward  the lifecycle synthesised in spec order (pagehide persisted, hidden; 1 s; visible, pageshow persisted)
//   resume        hide 1 s, show
// and for every restoring event: the duration of the event task (the synchronous dispatch of the restoring events),
// whether the Moon is adopted when that task ends, the time from the event to the START of the first animation frame,
// whether the Moon is adopted when that frame starts, and the time until the first frame has FINISHED its callbacks
// (the earliest moment the restored page can be painted with whatever was composed).
// Run it on the tree before and after the change to see what moved: the work is the same initial render and compose;
// G8 moves it from the first frame's callbacks into the event task on the back/forward sequence.
// Usage: node g8-task-cost.cjs <repoRoot> <outJson> <engine> <startISO> [--fault]
const fs=require('node:fs'),path=require('node:path');
const {createEnv,launch}=require('./iso.cjs');
const argv=process.argv.slice(2),FAULT=argv.includes('--fault'),[root,outFile,engine,startISO]=argv.filter(a=>!a.startsWith('--'));
const FRAG='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&simWx=0&simCloud=0&qa=1';
const SHIFT=`(()=>{const ND=Date,off=${Date.parse(startISO)}-ND.now();class D extends ND{constructor(...a){super(...(a.length?a:[ND.now()+off]));}static now(){return ND.now()+off;}}window.Date=D;})();`;
const DECODE_FAULT=`(()=>{const a=window.atob;window.atob=function(s){if(typeof s==='string'&&s.startsWith('U01IMR'))throw new Error('r0041 witness: injected receiver decode failure');return a.call(this,s);};})();`;
const set=h=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>h});Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>h?'hidden':'visible'});};
const LEAVE=`(bf)=>{(${set})(true);if(bf)window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}));document.dispatchEvent(new Event('visibilitychange',{bubbles:true}));}`;
const RESTORE=`(bf)=>new Promise(done=>{const cur=()=>{const o=window.SalahMoonRuntime.observe();return {adopted:!!o.current,source:o.state.visibleSource,moonReady:document.querySelector('.c').classList.contains('moon-ready')};};
  (${set})(false);const t0=performance.now();document.dispatchEvent(new Event('visibilitychange',{bubbles:true}));if(bf)window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true}));
  const taskMs=performance.now()-t0,end=cur();
  requestAnimationFrame(()=>{const frameStartMs=performance.now()-t0,atFrameStart=cur();
    // registered inside the frame: a macrotask queued here runs after this frame's remaining callbacks
    const mc=new MessageChannel();mc.port1.onmessage=()=>{mc.port1.close();done({taskMs:+taskMs.toFixed(1),adoptedAtTaskEnd:end.adopted,sourceAtTaskEnd:end.source,moonReadyAtTaskEnd:end.moonReady,frameStartMs:+frameStartMs.toFixed(1),adoptedAtFrameStart:atFrameStart.adopted,frameDoneMs:+(performance.now()-t0).toFixed(1),adoptedAfterFrame:cur().adopted});};mc.port2.postMessage(0);});})`;
const stats=a=>{const s=[...a].sort((x,y)=>x-y);return {min:s[0],median:s[s.length>>1],max:s.at(-1)};};
(async()=>{
  const env=await createEnv({root});const L=await launch(env,{engine,mode:'route',reducedMotion:'reduce'});const out={schema:'r0041-g8-task-cost/1',tree:path.basename(path.resolve(root)),engine,startISO,fault:FAULT,headless:true,routes:{}};
  try{await L.context.addInitScript(SHIFT);if(FAULT)await L.context.addInitScript(DECODE_FAULT);const page=await L.context.newPage();
    await page.goto(env.origins.url('127.0.0.1','/index.html')+FRAG,{waitUntil:'load'});
    await page.waitForFunction(()=>window.SalahMoonRuntime?.observe?.().current,null,{timeout:60000,polling:100});await page.waitForTimeout(8000);
    out.before=await page.evaluate(()=>window.SalahMoonRuntime.observe().state.visibleSource);
    for(const [name,bf] of [['backForward',true],['resume',false]]){const ev=[];
      for(let k=0;k<5;k++){await page.evaluate(`(${LEAVE})(${bf})`);await page.waitForTimeout(1000);ev.push(await page.evaluate(`(${RESTORE})(${bf})`));await page.waitForTimeout(2500);}
      out.routes[name]={events:ev,adoptedAtTaskEnd:ev.filter(e=>e.adoptedAtTaskEnd).length+' of '+ev.length,adoptedAtFrameStart:ev.filter(e=>e.adoptedAtFrameStart).length+' of '+ev.length,
        taskMs:stats(ev.map(e=>e.taskMs)),frameStartMs:stats(ev.map(e=>e.frameStartMs)),frameDoneMs:stats(ev.map(e=>e.frameDoneMs))};}
  }catch(e){out.error=String(e.stack||e).slice(0,500);}
  await L.close().catch(()=>{});out.allowedExternal=env.finish().allowedExternal;
  fs.writeFileSync(outFile,JSON.stringify(out,null,1));
  console.log(JSON.stringify({tree:out.tree,engine,fault:FAULT,error:out.error,allowed:out.allowedExternal,...Object.fromEntries(Object.entries(out.routes).map(([k,v])=>[k,{end:v.adoptedAtTaskEnd,frameStart:v.adoptedAtFrameStart,taskMs:v.taskMs,frameStartMs:v.frameStartMs,frameDoneMs:v.frameDoneMs}]))}));
  if(out.error||out.allowedExternal!==0)process.exit(1);
})();
