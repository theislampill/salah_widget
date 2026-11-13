// Effect-free injected-fault discriminators for PRA-F-01 (R002C drafting).
// Uses the repository's r001d VM harness over the generated root index.html (network denied
// except the stubbed prayer provider; no storage/file writes). The throwing Moon runtime is an
// INJECTED stub: these observations show propagation, never a natural trigger.
// Usage: node liveness-probe.cjs <repo-root>
const path=require('node:path');
const root=path.resolve(process.argv[2]);
const {load}=require(path.join(root,'tests','r001d-harness.cjs'));
const stub=mode=>'window.__moonMode='+JSON.stringify(mode)+';window.__moonCalls=0;window.SalahMoonRuntime={request(){window.__moonCalls++;if(window.__moonMode==="throw")throw new Error("injected Moon request failure");if(window.__moonMode==="once"){window.__moonMode="ok";throw new Error("injected one-shot Moon failure");}return false;},surface(){return null},invalidate(){},finishInitialDocument(){},get state(){return {}},get disposed(){return false}};';
async function bootCase(mode){
  // Live wall-clock hash without simTime so boot follows its ordinary path.
  const h=load({hash:'#lat=24.47&lon=39.61&label=Madinah&method=4&tz=Asia%2FRiyadh&units=c&seed=1'});
  h.run('today=null;tomorrow=null;lastDate=null;TIMESCALE=1;');
  h.run(stub(mode));
  let rejected=null;
  try{ await h.complete(h.run('boot()'),{turns:200}); }catch(e){ rejected=String(e&&e.message||e); }
  return {mode,bootRejected:rejected,prayerRequests:h.requests.length,loopStarted:h.run('_loopStarted'),
    todayLoaded:h.run('!!today'),left:h.select('.left').textContent,cn:h.select('.cn').textContent,pendingFrames:h.rafs.length,moonCalls:h.run('window.__moonCalls')};
}
function loopCase(){
  // Frozen admitted scene from the harness defaults; start the real loop, then inject one failure.
  const h=load({});
  h.run(stub('ok'));
  h.run('render();startRenderLoop();');
  const step=()=>{let err=null;try{h.advanceFrame();}catch(e){err=String(e.message||e);}return err;};
  const framesBefore=h.rafs.length; const e1=step(); const healthyQueued=h.rafs.length;
  h.run('window.__moonMode="once";lastMoonMin=-1;_renderDirty=true;');
  const e2=step(); const afterThrowQueued=h.rafs.length;
  // Recovery opportunity without visibility/intersection change: new admitted state and dirty flag.
  h.run('_renderDirty=true;document.querySelector(".cn").textContent="SENTINEL";');
  const e3=step();
  return {framesQueuedAtStart:framesBefore,firstFrameError:e1,queuedAfterHealthyFrame:healthyQueued,
    injectedFrameError:e2,queuedAfterInjectedFrame:afterThrowQueued,laterFrameError:e3,
    cnAfterDirtyWithoutFrame:h.select('.cn').textContent,lastMoonPaint:h.run('_lastMoonPaint&&_lastMoonPaint.status')};
}
function paintStageCase(){
  // Same minute and fresh geometry: renderMoon() is skipped, so the first request() is paint()'s.
  const h=load({});
  h.run(stub('ok'));h.run('render();');
  const before=h.run('_lastRender&&_lastRender.atMs');
  h.run('document.querySelector(".cn").textContent="SENTINEL";window.__moonMode="throw";window.__moonCalls=0;');
  let err=null;try{h.run('render();');}catch(e){err=String(e.message||e);}
  return {threw:err,cnAfter:h.select('.cn').textContent,timesLen:h.select('.times').innerHTML.length,
    lastMoonPaint:h.run('_lastMoonPaint&&_lastMoonPaint.status+"/"+_lastMoonPaint.stage'),lastRenderUnchanged:h.run('_lastRender&&_lastRender.atMs')===before,moonCalls:h.run('window.__moonCalls')};
}
(async()=>{
  const out={boot:[await bootCase('ok'),await bootCase('throw')],loop:loopCase(),paintStage:paintStageCase()};
  console.log(JSON.stringify(out,null,1));
})().catch(e=>{console.error('PROBE-ERROR',e&&e.stack);process.exitCode=1;});
