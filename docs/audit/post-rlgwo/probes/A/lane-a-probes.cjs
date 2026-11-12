"use strict";
// Lane A effect-free probes. Uses the repository's own r0003 VM harness (stubbed fetch/storage/timers,
// no network, no browser, no writes). Run from anywhere: node lane-a-probes.cjs <worktree-root>
const path=require("node:path");
const root=process.argv[2];
const {harness,record,settle,copy}=require(path.join(root,"tests","r0003-harness.cjs"));
const out={};
async function P1_invalidHintZone(){
  // config.js normalize accepts any non-empty tz string; does prayer acquisition recover from provider meta?
  const h=harness({epoch:"2026-09-07T12:00:00Z",hash:"#lat=24.47&lon=39.61&tz=Bogus%2FZone&method=4"});
  const civil=h.run("prayerCivilDay()"), parts=h.run("JSON.stringify(partsInTz(Date.now()))");
  const boot=(await h.startBoot()).pending;
  const urls=()=>h.requests.map(r=>r.url.replace(/\?.*/,""));
  const first=urls();
  for(const r of h.requests) r.ok(record("07-09-2026","Asia/Riyadh","provider"));
  await settle(); await h.advance(1000); for(const r of h.requests.slice(first.length)) r.ok(record("07-09-2026","Asia/Riyadh","provider")); await h.advance(3000);
  for(const r of h.requests) try{r.ok(record("07-09-2026","Asia/Riyadh","provider"));}catch(e){}
  await h.advance(5000);
  // Give the loop many frames over 3 minutes of elapsed time: does maintainPrayerDay ever retry?
  for(let i=0;i<180;i++){ h.elapse(1000); await h.frame(); }
  return {prayerCivilDay:civil,partsInTzFallback:JSON.parse(parts),requestPaths:urls(),requestCount:h.requests.length,
    state:{today:h.state().today?.tag??null,tz:h.state().tz,loop:h.state()._loopStarted},errors:h.errors.map(e=>e.text).slice(-2)};
}
async function P2_clockPreviewRebase(){
  // SalahClock.set explicit preview, then a provider-adopted zone differing from the hint.
  const h=harness({epoch:"2026-09-07T12:00:00Z",hash:"#lat=35.68&lon=139.69&method=2"});
  const boot=(await h.startBoot()).pending;
  const target=Date.parse("2026-12-25T03:00:00Z");
  h.run("var _wxDecisionCache=null;"); h.run(`window.__r=SalahClock.set({utcMs:${target},rate:0})`);
  const before=h.run("simNow()"), tzBefore=h.state().tz;
  const pending=h.requests.filter(r=>r.url.includes("/timings/"));
  for(const r of pending) r.ok(record(r.url.match(/timings\/([^?]+)/)[1],"Asia/Tokyo","tokyo"));
  await settle(); await h.advance(500);
  for(const r of h.requests.filter(r=>!pending.includes(r))) try{r.ok(record(r.url.match(/timings\/([^?]+)/)[1],"Asia/Tokyo","tokyo"));}catch(e){}
  await h.advance(500);
  const after=h.run("simNow()");
  return {requestedPreviewUtc:new Date(target).toISOString(),simNowBeforeAdoption:new Date(before).toISOString(),tzBefore,
    tzAfter:h.state().tz,simNowAfterAdoption:new Date(after).toISOString(),clockPreview:h.run("_clockPreview"),
    previewRetained:Math.abs(after-target)<60000,requestPaths:h.requests.map(r=>r.url.replace(/\?.*/,""))};
}
function rec(day,zone,timings){const r=record(day,zone,day);Object.assign(r.timings,timings);return r;}
async function P3_reorderedNextEvent(){
  const h=harness({epoch:"2026-09-07T23:00:00Z",hash:"#lat=10&lon=10&tz=UTC&method=2"});
  const base={Fajr:"05:00",Sunrise:"06:00",Dhuhr:"12:00",Asr:"15:30",Maghrib:"18:00"};
  const today=rec("07-09-2026","UTC",{...base,Isha:"00:30"}), next=rec("08-09-2026","UTC",{...base,Isha:"00:31"});
  h.seed(today,next); h.run("_prayerRecordsGeneration=_runtimeGeneration");
  const M=h.run("(()=>{const M=model();return M&&{nextKey:M.nextKey,nextTime:M.nextTime,leftMin:M.leftMin,state:M.selection.state,nextDate:M.nextDateStr,progressKind:M.progressKind};})()");
  const h2=harness({epoch:"2026-09-07T23:00:00Z",hash:"#lat=10&lon=10&tz=UTC&method=2"});
  h2.seed(rec("07-09-2026","UTC",{...base,Isha:"19:30"}),rec("08-09-2026","UTC",{...base,Isha:"19:31"})); h2.run("_prayerRecordsGeneration=_runtimeGeneration");
  const C=h2.run("(()=>{const M=model();return M&&{nextKey:M.nextKey,nextTime:M.nextTime,leftMin:M.leftMin,state:M.selection.state};})()");
  return {reordered:copy(M),ordinaryControl:copy(C)};
}
async function P4_presentationNoRequests(){
  // R0003 presentation path: label/time change must not issue requests or bump generation.
  const h=harness({epoch:"2026-09-07T12:00:00Z",hash:"#lat=10&lon=10&tz=UTC&method=2&label=A"});
  const boot=(await h.startBoot()).pending;
  for(const r of h.requests) r.ok(record("07-09-2026","UTC","a")); await settle(); await h.advance(100);
  const n0=h.requests.length,g0=h.run("_runtimeGeneration");
  h.run("window.__c={...CONFIG,label:'B',time:'12'}"); await Promise.race([h.run("applyConfig(window.__c,{save:false})"),settle()]);
  const n1=h.requests.length,g1=h.run("_runtimeGeneration"),label=h.run("label"),dirty=h.run("_renderDirty");
  h.run("window.__c2={...CONFIG}"); await Promise.race([h.run("applyConfig(window.__c2,{save:false})"),settle()]);
  const n2=h.requests.length,g2=h.run("_runtimeGeneration");
  await Promise.race([h.run("applyConfig(window.__c2,{save:false,reset:true})"),settle()]);
  return {before:{requests:n0,generation:g0},afterPresentation:{requests:n1,generation:g1,label,renderDirty:dirty},
    afterEqual:{requests:n2,generation:g2},afterReset:{requests:h.requests.length,generation:h.run("_runtimeGeneration")}};
}
const keep=setInterval(()=>{},1000);
(async()=>{
  for(const [k,f] of Object.entries({P1_invalidHintZone,P2_clockPreviewRebase,P3_reorderedNextEvent,P4_presentationNoRequests})){
    try{ out[k]=await f(); }catch(e){ out[k]={probeError:String(e&&e.stack||e).split("\n").slice(0,4).join(" | ")}; }
  }
  console.log(JSON.stringify(out,null,1)); clearInterval(keep);
})();
// P5 (appended): is the .c[data-stale="prayer"] presentation reachable when today is a stale (yesterday) record?
(async()=>{
  const keep2=setInterval(()=>{},1000);
  try{
    const h=harness({epoch:"2026-09-08T09:00:00Z",hash:"#lat=10&lon=10&tz=UTC&method=2",offline:true});
    h.seed(record("08-09-2026","UTC","fresh")); h.run("_prayerRecordsGeneration=_runtimeGeneration"); h.run("render()");
    const freshStale=h.run("document.querySelector('.c').dataset.stale");
    h.seed(record("07-09-2026","UTC","yesterday")); h.run("_prayerRecordsGeneration=_runtimeGeneration");
    h.run("maintainPrayerDay()"); await settle(); h.run("render()");
    console.log(JSON.stringify({P5_staleAttribute:{afterFresh:freshStale,prayerStale:h.run("_prayerStale"),modelNull:h.run("model()===null"),
      dataStaleAfterStaleRender:h.run("document.querySelector('.c').dataset.stale"),ahHtml:h.nodes.get("#ah")?.innerHTML??null}},null,1));
  }catch(e){console.log(JSON.stringify({P5_error:String(e.stack).split("\n").slice(0,3).join(" | ")}));}
  clearInterval(keep2);
})();
