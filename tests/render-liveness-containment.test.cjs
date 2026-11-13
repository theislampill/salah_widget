'use strict';
// R002C (issue 93): prayer publication is independent of optional astronomy; the render loop stays live
// and boot/apply/clock continue when an optional stage throws. Every failure here is an INJECTED fault
// (a throwing stub SalahMoonRuntime or a replaced optional painter): these tests prove containment and
// liveness of the source's own call path, never a natural trigger. VM harness over the generated root
// index.html (tests/r001d-harness.cjs): DOM/canvas/clock doubles, network denied except the stubbed
// prayer fixture, no storage or file writes. R2C_SOURCE=<generated index.html> runs the same rows against
// another tree (the RED baseline). Rows refer to docs/state-contracts/R002C.md. The mutation rows at the
// end apply each mutant in memory to the same source and require an actual assertion failure.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {load}=require('./r001d-harness.cjs');
const sourcePath=process.env.R2C_SOURCE?path.resolve(process.env.R2C_SOURCE):path.join(__dirname,'..','index.html');
const SOURCE=fs.readFileSync(sourcePath,'utf8');
const LIVE='#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&seed=1';

// A Moon runtime double. __moonMode: ok | throw | once (next request only) | hook (run __moonHook, then throw)
// | record (remember .cn at the first request). reportError is captured so emissions can be counted.
const MOON_STUB='window.__moonMode="ok";window.__moonCalls=0;window.__reports=[];'
  +'window.reportError=e=>window.__reports.push(String(e&&e.message||e));'
  +'window.SalahMoonRuntime={request(){window.__moonCalls++;const m=window.__moonMode;'
  +'if(m==="throw")throw new Error("injected Moon request failure");'
  +'if(m==="once"){window.__moonMode="ok";throw new Error("injected one-shot Moon failure");}'
  +'if(m==="hook"){window.__moonMode="ok";window.__moonHook();throw new Error("injected in-frame Moon failure");}'
  +'if(m==="record"&&window.__moonSeen==null)window.__moonSeen=document.querySelector(".cn").textContent;return false;},'
  +'surface(){return null},invalidate(){},finishInitialDocument(){},get state(){return {}},get disposed(){return false}};';
function harness(src,opts={}){
  const h=load({source:src,...(opts.hash?{hash:opts.hash}:{})});
  h.run(MOON_STUB);
  return h;
}
const step=h=>{let error=null;try{h.advanceFrame();}catch(e){error=e;}return error;};
const tryRun=(h,code)=>{try{h.run(code);return null;}catch(e){return e;}};
const prayerDom=h=>({cn:h.select('.cn').textContent,nt:h.select('.nt').textContent,left:h.select('.left').innerHTML||h.select('.left').textContent,
  times:h.select('.times').innerHTML,arc:h.select('.arc').innerHTML,ce:h.select('#ce').innerHTML,ah:h.select('#ah').innerHTML,bar:h.select('.bar>i').style.width});
const faults=h=>JSON.parse(h.run('JSON.stringify(typeof qaState==="function"&&qaState().renderFaults||null)'));
const faultCount=(h,name)=>{const f=faults(h);return f&&f[name]?f[name].count:0;};
// render() rethrows ONLY a theme-stage failure (accepted R0021 behaviour), after recording it and writing the receipt;
// every caller's stage boundary contains it. Any other escape is a containment failure.
function contained(h,error){
  if(error===null)return;
  const f=faults(h)||{};
  assert.ok(['theme-atmosphere','theme-paint'].some(k=>f[k]&&f[k].last.message===String(error.message)),'only a recorded theme-stage failure may leave render: '+String(error&&error.message));
}
function blank(h){h.run('document.querySelector(".cn").textContent="SENTINEL";document.querySelector(".times").innerHTML="";document.querySelector("#ce").innerHTML="SENTINEL";');}
const NO_MODEL='today=null;tomorrow=null;lastDate=null;', SIM_INVALID='_simValid=false;_simInvalidTz=tz;';

// ---- R2C-01: prayer is published despite a pre-publication optional throw ----
const R01={
  'Moon geometry (renderMoon)':'window.__moonMode="throw";',
  'weather sync (syncWeather)':'syncWeather=()=>{throw new Error("injected syncWeather failure")};',
  'star projection (projectStars)':'_starsProjected=false;projectStars=()=>{throw new Error("injected projectStars failure")};',
};
function r01(src,inject){
  const ref=harness(src);ref.run('render()');const expected=prayerDom(ref);
  const h=harness(src);blank(h);h.run(inject);
  contained(h,tryRun(h,'render()'));
  assert.deepEqual(prayerDom(h),expected,'prayer DOM equals a healthy render of the same model');
}
// Ordering witnesses (P-1): the optional stage observes prayer already published in this render.
function orderSync(src){const h=harness(src);h.run('window.__seen=null;syncWeather=()=>{window.__seen=document.querySelector(".cn").textContent;};');blank(h);h.run('render()');
  assert.equal(h.run('window.__seen'),'Isha','syncWeather ran before the prayer stage');}
function orderMoon(src){const h=harness(src);blank(h);h.run('window.__moonSeen=null;window.__moonMode="record";lastMoonMin=-1;render()');
  assert.equal(h.run('window.__moonSeen'),'Isha','the Moon request ran before the prayer stage');}
function orderHeader(src,setup){const h=harness(src);
  h.run(setup+'window.__seen=null;const __pwh=paintWeatherHeader;paintWeatherHeader=v=>{window.__seen=document.querySelector("#ce").innerHTML;return __pwh(v);};');
  if(setup===SIM_INVALID)assert.equal(h.run('simulationReady()'),false,'fixture must reach the sim-invalid branch');
  blank(h);h.run('render()');
  assert.notEqual(h.run('window.__seen'),null,'header painted');
  assert.notEqual(h.run('window.__seen'),'SENTINEL','header painted before the calendar');
  assert.equal(h.select('.left').textContent,'Prayer times unavailable');}
function headerFailure(src,setup){
  const ref=harness(src);ref.run(setup+'render()');
  const h=harness(src);h.run(setup);blank(h);h.run('paintWeatherHeader=()=>{throw new Error("injected header failure")};');
  assert.equal(tryRun(h,'render()'),null);
  assert.equal(h.select('#ce').innerHTML,ref.select('#ce').innerHTML,'calendar published');
  assert.equal(h.select('.times').innerHTML,ref.select('.times').innerHTML,'withdrawn rows published');
  assert.ok(faultCount(h,'weather-header')>=1,'the header failure is recorded');
}

// ---- R2C-02: loop survives a one-shot throw, stage-contained and residual (frame level) ----
function loopOneShot(src,arm,stage){
  const h=harness(src);h.run('render();startRenderLoop();');assert.equal(step(h),null);assert.equal(h.rafs.length,1);
  h.run(arm);const error=step(h);
  assert.equal(error,null,'the failure is recorded, not thrown out of the rAF callback');
  assert.equal(h.rafs.length,1,'exactly one pending frame after the faulting frame');
  h.run('document.querySelector(".cn").textContent="SENTINEL";_renderDirty=true;');assert.equal(step(h),null);
  assert.equal(h.select('.cn').textContent,'Isha','the next dirty state is published without a visibility change');
  assert.equal(h.rafs.length,1);assert.equal(faultCount(h,stage),1);
}
const ARM_MOON='window.__moonMode="once";lastMoonMin=-1;_renderDirty=true;';
const ARM_FRAME='window.__np=nowParts;nowParts=()=>{nowParts=window.__np;throw new Error("injected frame failure")};';

// ---- R2C-03: persistent fault for 60 simulated seconds ----
function persistent(src){
  const h=harness(src);h.run('TIMESCALE=1;_rafT0=0;window.__moonMode="throw";');tryRun(h,'render()');
  h.run('startRenderLoop()');
  const left=[];
  for(let i=0;i<60;i++){
    h.clock.now+=1000;h.clock.wall+=1000;
    assert.equal(h.rafs.length,1,'one pending frame before simulated second '+i);
    step(h);left.push(h.run('_lastRender&&_lastRender.leftMin'));
  }
  for(let i=1;i<left.length;i++)assert.ok(Math.abs(left[i-1]-left[i]-1/60)<1e-9,'countdown receipt advances one second per frame at '+i);
  assert.match(h.select('.left').innerHTML,/until-time/);
  const f=faults(h);
  assert.ok(f&&f['moon-geometry']&&f['moon-geometry'].count>=60,'every faulting frame is counted (Moon geometry)');
  assert.ok(f['theme-paint']&&f['theme-paint'].count>=60,'every faulting frame is counted (paint)');
  assert.equal(f.render,undefined,'the rethrown theme failure is not counted a second time by the loop boundary');
  const reports=JSON.parse(h.run('JSON.stringify(window.__reports)'));
  const distinct=new Set(Object.entries(f).map(([k,v])=>k+'\n'+v.last.message));
  assert.ok(reports.length>=1,'the failure is reported, not silent');
  assert.ok(reports.length<=distinct.size,'reported at most once per distinct stage and message');
}

// ---- R2C-04: boot continuation ----
async function bootContinues(src){
  const h=harness(src,{hash:LIVE});h.run('today=null;tomorrow=null;lastDate=null;TIMESCALE=1;window.__moonMode="throw";'
    +'window.__sw=0;const __s=startWeather;startWeather=(...a)=>{window.__sw++;return __s(...a);};');
  h.run('window.__boot=boot();window.__boot.catch(()=>{});window.__handoff=_skyInitialDocument;');
  assert.equal(h.run('window.__handoff'),false,'the initial-head handoff ran before the first await');
  await h.complete(h.run('window.__boot'),{turns:200});
  assert.ok(h.requests.length>=1,'prayer acquisition started');
  assert.equal(h.run('window.__sw'),1,'weather start invoked');
  assert.equal(h.run('_loopStarted'),true);assert.equal(h.rafs.length,1);
  assert.equal(h.run('!!today'),true);assert.equal(h.select('.cn').textContent,'Isha');
  assert.ok(faultCount(h,'moon-geometry')>=1,'the contained failure is recorded');
}

// ---- R2C-05: receipt truth after a paint-stage failure ----
function paintReceipt(src){
  const h=harness(src);h.run('render();window.__r1=_lastRender;');
  assert.equal(h.run('_lastRender.fx'),'cloud','healthy receipt carries the painted fx');
  h.run('_simBase+=1000;window.__moonMode="throw";');
  const error=tryRun(h,'render()');assert.ok(error,'the theme failure keeps its accepted render error behaviour');contained(h,error);
  assert.equal(h.run('_lastRender!==window.__r1'),true,'an earlier receipt cannot survive a newer published frame');
  assert.equal(h.run('_lastRender.acceptedUtcMs-window.__r1.acceptedUtcMs'),1000);
  assert.equal(h.run('_lastRender.fx'),null,'fx is marked unavailable for this frame');
  assert.equal(h.run('_lastMoonPaint.status+"/"+_lastMoonPaint.stage'),'failed/paint');
  assert.equal(faultCount(h,'theme-paint'),1);
}

// ---- R2C-06: no-model branch under a persistent optional failure ----
function noModel(src,target){
  const ref=harness(src);ref.run(NO_MODEL+'render()');
  const h=harness(src);h.run(NO_MODEL+target+'=()=>{throw new Error("injected '+target+' failure")};');blank(h);
  tryRun(h,'render()');
  assert.equal(h.select('#ce').innerHTML,ref.select('#ce').innerHTML,'calendar written');
  assert.equal(h.select('.left').textContent,'Prayer times unavailable');
  h.run('startRenderLoop()');step(h);assert.equal(h.rafs.length,1,'loop alive on no-model frames');
  h.run('today=__fixturePrayer;tomorrow=__fixtureNextPrayer;lastDate="08-09-2026";_renderDirty=true;');step(h);
  assert.equal(h.select('.cn').textContent,'Isha','a later admitted timetable is rendered by the next frame');
}

// ---- R2C-07: apply / SalahClock continuation ----
async function applyContinues(src){
  const h=harness(src,{hash:LIVE});h.run('TIMESCALE=1;window.__moonMode="throw";');
  const before=h.requests.length;
  await h.complete(h.run('applyConfig(SalahConfig.normalize({lat:21.42,lon:39.83,tz:"Asia/Riyadh",label:"Makkah",method:"4",units:"c",source:"manual"}),{save:false})'),{turns:200});
  assert.ok(h.requests.length>before,'the new location is acquired');
  assert.equal(h.run('_loopStarted'),true);assert.equal(h.run('!!today'),true);
}
function clockContinues(src){
  const h=harness(src);h.run('window.__notified=0;window.SalahNativeSkyHost={notify(){window.__notified++;}};window.__moonMode="throw";');
  const target=h.run('_simBase')+3600000;
  const result=JSON.parse(h.run('(()=>{try{return JSON.stringify(SalahClock.set({rate:0,utcMs:'+target+'}))}catch(e){return JSON.stringify({threw:String(e.message)})}})()'));
  assert.deepEqual(result,{utcMs:target,rate:0,live:false});assert.equal(h.run('window.__notified'),1,'notify still runs');
  const ts=h.run('TIMESCALE'),base=h.run('_simBase');
  assert.equal(h.run('(()=>{try{SalahClock.set({rate:-1});return "no throw"}catch(e){return e.name}})()'),'RangeError');
  assert.equal(h.run('TIMESCALE'),ts);assert.equal(h.run('_simBase'),base);
}

// ---- R2C-08: prayer-stage failure is truthful (P-2) ----
function prayerFault(src){
  const h=harness(src);h.run('render();window.__theme=0;window.__celestial=0;const __at=applyTheme;applyTheme=M=>{window.__theme++;return __at(M);};'
    +'const __pc=paintCelestialWithoutTimetable;paintCelestialWithoutTimetable=d=>{window.__celestial++;return __pc(d);};'
    +'drawArc=()=>{throw new Error("injected prayer-stage failure")};');
  assert.equal(tryRun(h,'render()'),null);
  assert.equal(h.select('.left').textContent,'Prayer times unavailable');assert.equal(h.select('.cn').textContent,'—');
  assert.equal(h.run('_lastRender'),null);assert.equal(faultCount(h,'prayer'),1);
  assert.equal(h.run('window.__theme'),0,'applyTheme never runs with a partial prayer stage');
  assert.equal(h.run('window.__celestial'),1,'the no-model optional stages ran');
  h.run('startRenderLoop()');step(h);assert.equal(h.rafs.length,1);
}

// ---- R2C-09: no double scheduling across hide/show ----
function visibilityHarness(src){
  const h=harness(src);h.run('window.__ls={};document.addEventListener=(t,f)=>{window.__ls[t]=f;};'
    +'window.__hide=()=>{document.visibilityState="hidden";window.__ls.visibilitychange();};window.__show=()=>{document.visibilityState="visible";window.__ls.visibilitychange();};');
  h.run('render();startRenderLoop();');assert.equal(step(h),null);assert.equal(h.rafs.length,1);return h;
}
function hideInFault(src){
  const h=visibilityHarness(src);h.run('window.__moonHook=()=>window.__hide();window.__moonMode="hook";lastMoonMin=-1;_renderDirty=true;');
  step(h);assert.equal(h.rafs.length,0,'hidden: none pending');
  h.run('window.__show()');assert.equal(h.rafs.length,1);h.run('window.__show()');assert.equal(h.rafs.length,1,'repeated show: still one');
}
function hideShowInFrame(src,faulting){
  const h=visibilityHarness(src);
  h.run('window.__moonHook=()=>{window.__hide();window.__show();};'+(faulting?'window.__moonMode="hook";'
    :'SalahMoonRuntime.request=function(){if(!window.__done){window.__done=1;window.__moonHook();}return false;};')+'lastMoonMin=-1;_renderDirty=true;');
  step(h);assert.equal(h.rafs.length,1,'exactly one pending frame');h.run('window.__show()');assert.equal(h.rafs.length,1);
}

// ---------------------------------------------------------------- rows
for(const [name,inject] of Object.entries(R01))test('R2C-01 prayer published despite '+name+' failure',()=>r01(SOURCE,inject));
test('R2C-01 order: weather sync runs after the prayer stage',()=>orderSync(SOURCE));
test('R2C-01 order: Moon geometry runs after the prayer stage',()=>orderMoon(SOURCE));
test('R2C-01 order: no-model header after withdrawal and calendar',()=>orderHeader(SOURCE,NO_MODEL));
test('R2C-01 order: sim-invalid header after withdrawal and calendar',()=>orderHeader(SOURCE,SIM_INVALID));
test('R2C-01 no-model header failure still publishes withdrawal and calendar',()=>headerFailure(SOURCE,NO_MODEL));
test('R2C-01 sim-invalid header failure still publishes withdrawal and calendar',()=>headerFailure(SOURCE,SIM_INVALID));
test('R2C-02 loop survives a one-shot Moon failure',()=>loopOneShot(SOURCE,ARM_MOON,'moon-geometry'));
test('R2C-02 loop survives a one-shot residual frame failure',()=>loopOneShot(SOURCE,ARM_FRAME,'frame'));
test('R2C-03 persistent Moon failure: countdown advances each second, faults counted, reported once',()=>persistent(SOURCE));
test('R2C-04 boot continuation under a throwing Moon runtime',()=>bootContinues(SOURCE));
test('R2C-05 paint-stage failure: fresh receipt, fx unavailable, fault recorded',()=>paintReceipt(SOURCE));
for(const target of ['paintCelestialWithoutTimetable','withdrawWeatherEffects'])test('R2C-06 no-model '+target+' failure every frame',()=>noModel(SOURCE,target));
test('R2C-07 applyConfig continues to acquisition and the loop under a throwing Moon runtime',()=>applyContinues(SOURCE));
test('R2C-07 SalahClock.set completes its transition; invalid input still throws before mutation',()=>clockContinues(SOURCE));
test('R2C-08 prayer-stage failure publishes the withdrawal, skips the theme, keeps the loop',()=>prayerFault(SOURCE));
test('R2C-08 a failed no-timetable withdrawal is recorded once and not retried within the frame',()=>{
  const h=harness(SOURCE);h.run(NO_MODEL+'window.__cal=0;renderCalendarDates=()=>{window.__cal++;throw new Error("injected calendar failure")};');
  assert.equal(tryRun(h,'render()'),null);
  assert.equal(h.run('window.__cal'),1,'no retry inside the frame');assert.equal(faultCount(h,'prayer'),1);assert.equal(faultCount(h,'prayer-withdrawal'),0);
  assert.equal(h.select('.left').textContent,'Prayer times unavailable');assert.equal(h.run('_lastRender'),null);
});
test('R2C-09 hide during a faulting frame leaves none pending; show schedules exactly one',()=>hideInFault(SOURCE));
test('R2C-09 hide+show inside a faulting frame leaves exactly one pending',()=>hideShowInFrame(SOURCE,true));
test('R2C-09 hide+show inside a healthy frame leaves exactly one pending',()=>hideShowInFrame(SOURCE,false));
test('R2C-03 bounded record: qaState().renderFaults is a frozen pure read',()=>{
  const h=harness(SOURCE);h.run('window.__moonMode="throw";');tryRun(h,'render()');
  const a=h.run('JSON.stringify(qaState().renderFaults)'),b=h.run('JSON.stringify(qaState().renderFaults)');assert.equal(a,b,'reading twice changes nothing');
  assert.equal(h.run('Object.isFrozen(qaState().renderFaults)&&Object.isFrozen(qaState().renderFaults["moon-geometry"])&&Object.isFrozen(qaState().renderFaults["moon-geometry"].first)'),true);
  h.run('window.__moonMode="ok";');h.run('render()');assert.equal(h.run('qaState().renderFaults["moon-geometry"].count'),1,'a healthy frame adds nothing');
  h.run('window.__moonMode="throw";SalahMoonRuntime.request=()=>{throw new Error("x".repeat(5000))};lastMoonMin=-1;');tryRun(h,'render()');
  assert.equal(h.run('qaState().renderFaults["moon-geometry"].last.message.length'),200,'message truncated');
});

// ---------------------------------------------------------------- R2C-12 mutation discrimination
// Each mutant edits one exact anchor of this source in memory; the discriminator must fail with an
// actual assertion (a setup error or an unapplied anchor is not a kill).
const MOON_LINE=SOURCE.split('\n').find(s=>s.includes('runRenderStage("moon-geometry",()=>{ const mm=Math.floor(M.nowMin);'));
const SYNC_LINE=SOURCE.split('\n').find(s=>s.startsWith('  runRenderStage("weather-sync",syncWeather);'));
const MUTANTS=[
  ['m1 renderMoon back before the prayer writes',[[MOON_LINE+'\n',''],['    if(M){\n','    if(M){\n'+MOON_LINE+'\n']],src=>orderMoon(src)],
  ['m2 drop the guaranteed reschedule',[['    finally{ _running=false; if(_wanted) _raf=requestAnimationFrame(loop); }','    finally{ _running=false; }'],
    ['    runRenderStage("sky-preview",()=>window.SalahSkyPreview?.present(_RAFNOW()));\n','    runRenderStage("sky-preview",()=>window.SalahSkyPreview?.present(_RAFNOW()));\n    _raf=requestAnimationFrame(loop);\n']],src=>loopOneShot(src,ARM_FRAME,'frame')],
  ['m3 stage guard swallows without a record',[['catch(e){ recordRenderFault(name,e); return false; }','catch(e){ return false; }']],src=>persistent(src)],
  ['m4 prayer catch-all without the withdrawal',[['if(M || !modelDone) runRenderStage("prayer-withdrawal",withdrawnPrayerStage);','void modelDone;']],src=>prayerFault(src)],
  ['m5 boot Moon guard removed',[['  try{ renderMoon(); }catch(e){ recordRenderFault("moon-geometry",e); }\n\n','  renderMoon();\n\n']],src=>bootContinues(src)],
  ['m6 start guard reads a consumed id',[['    _raf=null; _running=true;','    _running=true;'],['if(_raf===null && !_running) _raf=requestAnimationFrame(loop);','if(!_raf) _raf=requestAnimationFrame(loop);']],src=>hideShowInFrame(src,true)],
  ['m7a syncWeather back ahead of the prayer writes',[[SYNC_LINE+'\n',''],['  let M=null, prayerPublished=false, modelDone=false;\n',SYNC_LINE+'\n  let M=null, prayerPublished=false, modelDone=false;\n']],src=>orderSync(src)],
  ['m7b sim-invalid header ahead of the calendar',[['runRenderStage("prayer",withdrawnPrayerStage);runRenderStage("weather-header",()=>paintWeatherHeader(weatherHeader(weatherDecision(),false)));',
    'withdrawPrayerPresentation();runRenderStage("weather-header",()=>paintWeatherHeader(weatherHeader(weatherDecision(),false)));renderCalendarDates(selectCalendarDisplay(null));']],src=>orderHeader(src,SIM_INVALID)],
  ['m7c no-model header ahead of the calendar',[['    }else withdrawnPrayerStage();','    }else withdrawPrayerPresentation();'],
    ['    runRenderStage("celestial",()=>paintCelestialWithoutTimetable(d));return;','    runRenderStage("celestial",()=>paintCelestialWithoutTimetable(d));renderCalendarDates(selectCalendarDisplay(null));return;']],src=>orderHeader(src,NO_MODEL)],
];
function mutate(edits){
  let out=SOURCE;
  for(const [from,to] of edits){
    assert.ok(typeof from==='string'&&from.length>0,'mutation anchor resolved');
    assert.equal(out.split(from).length,2,'exactly one mutation anchor: '+from.slice(0,60));
    out=out.replace(from,()=>to);
  }
  assert.notEqual(out,SOURCE);return out;
}
const MUTATION_ROWS=!process.env.R2C_SOURCE;   // anchors are this candidate's own text
for(const [name,edits,discriminate] of MUTANTS)test('R2C-12 mutant '+name+' is killed',{skip:!MUTATION_ROWS&&'mutation anchors belong to the candidate source'},async()=>{
  await discriminate(SOURCE);
  const mutant=mutate(edits);
  await assert.rejects(async()=>discriminate(mutant),error=>error instanceof assert.AssertionError,'only an actual assertion failure detects the mutant');
});
