"use strict";
// R002E (issue 95): prayer presentation residual state. Rows refer to docs/state-contracts/R002E.md.
//   E-02  I-S1 "stale => no model" over clock jumps, seeks, adoption, broad apply and zone change, plus the one
//         counterexample found (a backward wall step across civil midnight between maintainPrayerDay and render).
//   E-03  fit-cache key completeness (noon, declination, runtime generation) with the font gate preserved.
//   E-04  mirror flags (fetchingTomorrow, _rolloverBusy, _rolloverNextTry) equal the authoritative slots/cooldown.
//   E-05  qaState().cache prayerStale / rolloverPendingMs derivation unchanged.
//   E-06  instrument seams retained (model().needTomorrow, model().warmEnd).
//   E-07a the single status-line owner reproduces every row of today's visible status results.
//   E-09  in-memory mutants m1 (mirror write), m2/m3 (fit key), m4 (status bypass) must be killed by an assertion.
// Source-bound VM fixtures (tests/r0003-harness.cjs: actual config, clock, loader, ownership, model, render and rAF
// loop; network is a stub, no storage writes outside the fixture). R2E_SOURCE=<generated index.html> runs the
// rows against another tree (RED baseline); mutation rows then skip (their anchors are this tree's text).
const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const {record,harness,cfg,req,settle}=require("./r0003-harness.cjs");
const SOURCE_PATH=process.env.R2E_SOURCE?path.resolve(process.env.R2E_SOURCE):path.join(__dirname,"..","index.html");
const SOURCE=fs.readFileSync(SOURCE_PATH,"utf8");
const MUTATION_ROWS=!process.env.R2E_SOURCE;
const DAY=86400000;
const text=n=>n.textContent;

// ---- E-02 I-S1 ---------------------------------------------------------------------------------------------
// Every render() call is observed: a render that publishes a model while _prayerStale is true violates I-S1.
function watched(src,options={}){
  const h=harness({source:src,...options});
  h.run('var _wxDecisionCache=null;var __r2eSeen=[];const __r2eRender=render;render=function(){__r2eSeen.push({stale:_prayerStale,model:!!model()});return __r2eRender.apply(this,arguments);};');
  return h;
}
const violations=h=>h.run("JSON.stringify(__r2eSeen.filter(r=>r.stale&&r.model))");
const stalePresentation=h=>h.nodes.get(".c")?.dataset?.stale;
async function frames(h,n=3){for(let i=0;i<n;i++)await h.frame();}
function answerAll(h,tag="ok"){for(const r of h.requests)if(!r.done){r.done=true;const day=/\/timings\/([^?]+)\?/.exec(r.url)[1];r.ok(record(day,"UTC",tag+day));}}
async function seeded(src,epoch="2026-09-07T12:00:00Z"){
  const h=watched(src,{epoch});h.seed(record(undefined,"UTC","day7"));h.run("startRenderLoop()");await h.frame();return h;
}
const SEQUENCES={
  "forward one day, then acquisition":async h=>{h.wallBy(DAY);await frames(h);answerAll(h);await settle();await frames(h);},
  "forward three days, then acquisition":async h=>{h.wallBy(3*DAY);await frames(h);answerAll(h);await settle();await frames(h);},
  "backward one day, then acquisition":async h=>{h.wallBy(-DAY);await frames(h);answerAll(h);await settle();await frames(h);},
  "forward then backward between frames, acquisition held":async h=>{h.wallBy(DAY);await frames(h);h.wallBy(-DAY);await frames(h);h.wallBy(-3*DAY);await frames(h);},
  "failed rollover keeps stale through retries":async h=>{h.wallBy(DAY);await frames(h);for(const r of h.requests)if(!r.done){r.done=true;r.fail();}await settle();for(let t=1000;t<=65000;t+=4000){await h.advance(h.elapsed()+4000);await h.frame();}},
  "SalahClock seek forward and back":async h=>{h.run(`SalahClock.set({utcMs:${Date.parse("2026-09-08T12:00:00Z")},rate:0})`);await frames(h);h.run(`SalahClock.set({utcMs:${Date.parse("2026-09-07T12:00:00Z")},rate:0})`);await frames(h);answerAll(h);await settle();await frames(h);},
  "broad apply while stale":async h=>{h.wallBy(DAY);await frames(h);h.apply(cfg(12,"other"));await settle();await frames(h);answerAll(h);await settle();await frames(h);},
  "zone change by broad apply":async h=>{h.apply(cfg(10,"zone",{lon:10,tz:"Asia/Tokyo"}));await settle();await frames(h);h.wallBy(DAY);await frames(h);answerAll(h);await settle();await frames(h);},
  "prefetch promotion at midnight":async h=>{answerAll(h,"pre");await settle();h.wallBy(12*3600000);await frames(h);answerAll(h);await settle();await frames(h);}
};
for(const [name,steps] of Object.entries(SEQUENCES))test(`E-02 I-S1 holds: ${name}`,async()=>{
  const h=await seeded(SOURCE);await steps(h);
  assert.equal(violations(h),"[]","a render published a model while _prayerStale was true");
  assert.notEqual(stalePresentation(h),"prayer");
  assert.ok(h.run("__r2eSeen.length")>1,"the sequence must exercise render");
});
test("E-02 I-S1 counterexample: a backward wall step across midnight between maintainPrayerDay and render (gate G-E1 Andon)",async()=>{
  // Characterises the one reachable violation found. It lasts one frame: the next maintainPrayerDay clears
  // _prayerStale and the next render writes "". If I-S1 is later enforced in code, this row must be revised
  // together with gate G-E1 (docs/state-contracts/R002E.md §3).
  const h=watched(SOURCE,{epoch:"2026-09-07T23:59:59Z"});h.seed(record(undefined,"UTC","day7"));h.run("render();startRenderLoop()");await h.frame();
  const g=h.run("globalThis");g.__r2eHook=()=>{};
  h.run("const __r2eMaintain=maintainPrayerDay;maintainPrayerDay=function(){__r2eMaintain();__r2eHook();};");
  await h.advance(h.elapsed()+2000);
  g.__r2eHook=()=>{h.wallBy(-2000);g.__r2eHook=()=>{};};
  await h.frame();
  assert.equal(violations(h),'[{"stale":true,"model":true}]');
  assert.equal(stalePresentation(h),"prayer","the desaturated date-row state is reachable for this frame");
  await h.frame();
  assert.equal(h.run("_prayerStale"),false);assert.equal(stalePresentation(h),"");
});

// ---- E-04 mirror consistency, E-05 diagnostics ---------------------------------------------------------------
const MIRROR=`JSON.stringify({prefetch:fetchingTomorrow===(_requestSlots.prefetch!==null),current:_rolloverBusy===(_requestSlots.current!==null),
  nextTry:!_prayerStale||(_prayerCooldown.current!==null&&_rolloverNextTry===_prayerCooldown.current.nextTry),stale:_prayerStale})`;
function mirrorsAfter(h,label,seen){const m=JSON.parse(h.run(MIRROR));seen.push(label);if(!(m.prefetch&&m.current&&m.nextTry))throw new assert.AssertionError({message:`mirror diverged after ${label}: ${JSON.stringify(m)}`});return m;}
async function mirrorSequence(src){
  const seen=[];
  const h=harness({source:src,epoch:"2026-09-07T23:59:00Z"});h.run("var _wxDecisionCache=null;");const boot=(await h.startBoot()).pending;mirrorsAfter(h,"boot begin current",seen);
  req(h,"07-09-2026").ok(record("07-09-2026","UTC","day7"));await settle();await boot;mirrorsAfter(h,"current finish (adopted)",seen);
  await h.frame();mirrorsAfter(h,"prefetch begin",seen);
  req(h,"08-09-2026").fail();await settle();mirrorsAfter(h,"prefetch attempt failed (op retained)",seen);
  await h.advance(h.elapsed()+900);mirrorsAfter(h,"prefetch retry",seen);
  await h.advance(h.elapsed()+60000);await h.frame();mirrorsAfter(h,"midnight: rollover begin while stale",seen);
  for(const r of h.requests)if(!r.done&&/08-09-2026/.test(r.url)){r.done=true;r.fail();}await settle();mirrorsAfter(h,"rollover attempt failed",seen);
  for(let i=0;i<4;i++){await h.advance(h.elapsed()+2000);await h.frame();for(const r of h.requests)if(!r.done){r.done=true;r.fail();}await settle();}
  mirrorsAfter(h,"rollover exhausted, cooldown",seen);
  const stale=JSON.parse(h.run(MIRROR)).stale;
  await h.advance(h.elapsed()+61000);await h.frame();mirrorsAfter(h,"cooldown elapsed: new rollover begin",seen);
  const inflight=h.requests.filter(r=>!r.done);
  h.apply(cfg(20,"broad"));await settle();mirrorsAfter(h,"generation change + reset with in-flight ops",seen);
  for(const r of inflight){r.done=true;r.ok(record("08-09-2026","UTC","obsolete"));}await settle();mirrorsAfter(h,"ineligible finish of an obsolete op",seen);
  for(const r of h.requests)if(!r.done){r.done=true;const day=/\/timings\/([^?]+)\?/.exec(r.url)[1];r.ok(record(day,"UTC","new"+day));}await settle();await h.frame();
  mirrorsAfter(h,"new-generation adoption (day change cooldown reset)",seen);
  for(const r of h.requests)if(!r.done){r.done=true;const day=/\/timings\/([^?]+)\?/.exec(r.url)[1];r.ok(record(day,"UTC","pf"+day));}await settle();mirrorsAfter(h,"prefetch finish (adopted)",seen);
  h.run(`SalahClock.set({utcMs:${Date.parse("2026-09-11T12:00:00Z")},rate:0})`);await settle();mirrorsAfter(h,"SalahClock seek (rollover begin)",seen);
  h.run(`SalahClock.set({utcMs:${Date.parse("2026-09-08T12:00:00Z")},rate:0})`);await settle();await h.frame();mirrorsAfter(h,"SalahClock seek back",seen);
  return {h,seen,stale};
}
test("E-04 mirror flags equal the authoritative slots and the current cooldown after every event",async()=>{
  const {seen,stale}=await mirrorSequence(SOURCE);
  assert.equal(stale,true,"the sequence must reach the stale state the qaState diagnostic reports");
  assert.equal(seen.length,15);
});
test("E-05 qaState cache diagnostics keep their derivation",()=>{
  assert.equal(SOURCE.split("prayerStale: _prayerStale, rolloverPendingMs: (_prayerStale ? Math.max(0, _rolloverNextTry-_RAFNOW()) : null),").length,2,
    "prayerStale/rolloverPendingMs must stay the stale flag and the remaining current cooldown");
});

// ---- E-06 instrument seams -----------------------------------------------------------------------------------
test("E-06 model keeps the instrument-observed fields needTomorrow and warmEnd",async()=>{
  const h=harness({source:SOURCE,epoch:"2026-09-07T12:00:00Z"});h.seed(record(undefined,"UTC","day7"),record("08-09-2026","UTC","day8"));
  const m=JSON.parse(h.run("JSON.stringify({needTomorrow:model().needTomorrow,warmEnd:model().warmEnd})"));
  assert.equal(m.needTomorrow,false);assert.ok(Number.isFinite(m.warmEnd));
  h.wallBy(10*3600000);   // 22:00 UTC: past Isha, next is tomorrow's Fajr
  const n=JSON.parse(h.run("JSON.stringify({needTomorrow:model().needTomorrow,warmEnd:model().warmEnd,next:model().nextKey})"));
  assert.deepEqual([n.needTomorrow,n.next],[true,"Fajr"]);assert.ok(Number.isFinite(n.warmEnd));
});

// ---- E-07a status owner --------------------------------------------------------------------------------------
const nativeScript=src=>[...src.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)].find(m=>!m[1].trim()&&m[2].includes("async function boot(){"))[2];
function statusWriters(src){
  const body=nativeScript(src),writes=[...body.matchAll(/(?:\$|document\.querySelector)\(\s*"\.(?:nt|left)"\s*\)\s*\.(?:textContent|innerHTML)\s*=/g)];
  const owner=/function writePrayerStatus\([^)]*\)\{[\s\S]*?\n\}/.exec(body);
  return {count:writes.length,outside:owner?writes.filter(w=>w.index<owner.index||w.index>owner.index+owner[0].length).length:writes.length,owner:!!owner};
}
function assertSingleOwner(src){
  const w=statusWriters(src);
  assert.ok(w.owner,"writePrayerStatus owner missing");
  assert.equal(w.outside,0,"a .nt/.left write bypasses the status owner");
  assert.equal(w.count,3,"the owner holds the .nt write and the .left text/markup writes");
}
test("E-07a one status owner writes .nt/.left",()=>{ assertSingleOwner(SOURCE); });
test("E-07a row: initial markup is Loading…",()=>{
  assert.match(SOURCE,/<div class="left">Loading…<\/div>/);assert.match(SOURCE,/<div class="nt">—<\/div>/);
});
async function statusRows(src){
  const rows={};
  { const h=harness({source:src,hash:"#method=2"});await h.startBoot();rows.bare=text(h.nodes.get(".left")); }
  // Invalid explicit scene at boot: boot returns before the loop starts, so a direct render() result stays.
  { const h=harness({source:src,epoch:"2026-03-08T12:00:00Z",hash:"#lat=40.7128&lon=-74.006&tz=America/New_York&method=2&simTime=02:30"});
    await h.startBoot();await frames(h,2);rows.simBoot=text(h.nodes.get(".left"));rows.simNt=h.nodes.get(".nt").textContent;
    h.run("render()");rows.simBootRender=text(h.nodes.get(".left"));await frames(h,2);rows.simBootNext=text(h.nodes.get(".left")); }
  // A running loop whose scene becomes invalid (02:30 does not exist in New York on 2026-03-08): each loop frame
  // republishes the simulation text; a direct render() writes the withdrawal until the next frame.
  { const h=harness({source:src,epoch:"2026-03-08T12:00:00Z",hash:"#lat=10&lon=10&tz=UTC&method=2&simTime=02:30"});h.run("var _wxDecisionCache=null;");
    const boot=(await h.startBoot()).pending;answerAll(h);await settle();await boot;await frames(h,2);rows.simValid=text(h.nodes.get(".left"))!=="Simulation time unavailable";
    h.apply(cfg(40.7128,"ny",{lon:-74.006,tz:"America/New_York"}));await settle();await frames(h,2);rows.simLoop=text(h.nodes.get(".left"));
    h.run("render()");rows.simRender=text(h.nodes.get(".left"));await h.frame();rows.simNext=text(h.nodes.get(".left")); }
  { const h=harness({source:src,offline:true}),boot=(await h.startBoot()).pending;for(const at of [900,2700,6000])await h.advance(at);await boot;
    rows.loadFail=text(h.nodes.get(".left"));rows.loadFailNt=h.nodes.get(".nt").textContent;await h.frame();rows.loadFailNext=text(h.nodes.get(".left")); }
  { const h=harness({source:src,epoch:"2026-09-08T12:00:00Z"});h.seed(record(undefined,"UTC","day7"));h.run("startRenderLoop()");await frames(h,2);
    rows.stale=text(h.nodes.get(".left"));rows.staleNt=h.nodes.get(".nt").textContent; }
  { const h=harness({source:src,epoch:"2026-09-07T22:00:00Z"});h.seed(record(undefined,"UTC","day7"));h.run("render()");
    rows.noTarget=text(h.nodes.get(".left"));rows.noTargetNt=h.nodes.get(".nt").textContent; }
  { const h=harness({source:src,epoch:"2026-09-07T12:00:00Z"});h.seed(record(undefined,"UTC","day7"),record("08-09-2026","UTC","day8"));h.run("render()");
    rows.countdown=h.nodes.get(".left").innerHTML;rows.countdownNt=h.nodes.get(".nt").textContent; }
  return rows;
}
test("E-07a every D.5 row yields today's visible text, including the replacement sequences",async()=>{
  const r=await statusRows(SOURCE);
  assert.equal(r.bare,"Add lat & lon to the URL");
  assert.deepEqual([r.simBoot,r.simNt,r.simBootRender,r.simBootNext],["Simulation time unavailable","—","Prayer times unavailable","Prayer times unavailable"]);
  assert.deepEqual([r.simValid,r.simLoop,r.simRender,r.simNext],[true,"Simulation time unavailable","Prayer times unavailable","Simulation time unavailable"]);
  assert.deepEqual([r.loadFail,r.loadFailNt,r.loadFailNext],["Could not load prayer times","—","Prayer times unavailable"]);
  assert.deepEqual([r.stale,r.staleNt],["Prayer times unavailable","—"]);
  assert.deepEqual([r.noTarget,r.noTargetNt],["Countdown unavailable","—"]);
  assert.equal(r.countdown,'<span class="until-time">3h 30m</span> <span class="until-label">left</span> <span class="until-label">until</span> <span class="until-prayer">Asr</span>');
  assert.equal(r.countdownNt,"15:30");
});

// ---- E-03 fit key ---------------------------------------------------------------------------------------------
// The fitCn region runs against layout doubles (as tests/real-sky/native-prayer-arc-samples.test.cjs); a fit is
// counted by its canvas text measurement.
function fitFixture(src){
  const code=nativeScript(src);const body=code.slice(code.indexOf('let _cnFit="";'),code.indexOf("// PROCEDURAL BRANCHING LIGHTNING"));
  let measurements=0;const cn={style:{fontSize:"30px",top:"100px",marginBottom:"0px",fontFamily:"serif"},textContent:"Dhuhr"},nt={};
  const rail={getAttribute:()=>"rail",getTotalLength:()=>200,getPointAtLength:l=>({x:20+l*1.4,y:200-100*Math.sin(l*Math.PI/200)}),getScreenCTM:()=>({a:1,b:0,c:0,d:1,e:0,f:0}),
    ownerSVGElement:{createSVGPoint:()=>({matrixTransform(m){return {x:this.x*m.a+m.e,y:this.y*m.d+m.f};}})}};
  const els={".cn":cn,".nt":nt,".arc .rail":rail,".arc .horizon":{getBoundingClientRect:()=>({top:200})},".bar":{getBoundingClientRect:()=>({top:260})}};
  const scope={_renderDirty:false,Math,isFinite,parseFloat,Symbol,WeakMap,$:s=>els[s],getComputedStyle:e=>e.style,
    document:{fonts:{addEventListener(){}},querySelector:s=>els[s],createRange:()=>({selectNodeContents(e){this.e=e;},getBoundingClientRect(){return this.e===cn?{left:120,right:200,width:80,bottom:190}:{top:200,bottom:250};}}),
      createElement:()=>({getContext:()=>({measureText(){measurements++;return {actualBoundingBoxAscent:21,fontBoundingBoxDescent:7.2};}})})}};
  vm.createContext(scope);vm.runInContext(body,scope);
  return {fit:M=>scope.fitCn(M),count:()=>measurements,invalidate:()=>scope.cnFontChanged()};
}
const BASE_M=Object.freeze({currentKey:"Dhuhr",sunrise:367,sunset:1093,noon:730,decl:0.0123,selection:Object.freeze({generation:1})});
function fitKeyRows(src){
  const f=fitFixture(src),rows={};
  f.fit(BASE_M);f.fit(BASE_M);rows.same=f.count();
  f.fit({...BASE_M,selection:{generation:2}});rows.generation=f.count();
  f.fit({...BASE_M,selection:{generation:2},decl:0.0161});rows.decl=f.count();
  f.fit({...BASE_M,selection:{generation:2},decl:0.0161,noon:731});rows.noon=f.count();
  f.invalidate();f.fit({...BASE_M,selection:{generation:2},decl:0.0161,noon:731});rows.font=f.count();
  f.fit({...BASE_M,selection:{generation:2},decl:0.0161,noon:731});rows.settled=f.count();
  return rows;
}
test("E-03 a cached .cn fit is reused only when noon, declination, generation and font state are equal",()=>{
  assert.deepEqual(fitKeyRows(SOURCE),{same:1,generation:2,decl:3,noon:4,font:5,settled:5});
});

// ---- E-09 mutants ----------------------------------------------------------------------------------------------
function mutate(edits){
  let out=SOURCE;
  for(const [from,to] of edits){assert.equal(out.split(from).length,2,"exactly one mutation anchor: "+from.slice(0,70));out=out.replace(from,()=>to);}
  assert.notEqual(out,SOURCE);return out;
}
const MUTANTS=[
  ["m1 a mirror write removed from the prefetch finish",[['  if(op.kind==="prefetch") fetchingTomorrow=false;\n','\n']],async src=>{await mirrorSequence(src);}],
  ["m2 fit key without noon and declination",[['+"|"+M.noon+"|"+M.decl+"|"+','+"|"+']],src=>{assert.deepEqual(fitKeyRows(src),{same:1,generation:2,decl:3,noon:4,font:5,settled:5});}],
  ["m3 fit key without the runtime generation (broad location change)",[['+"|"+(M.selection&&M.selection.generation)+"|"+','+"|"+']],src=>{assert.deepEqual(fitKeyRows(src),{same:1,generation:2,decl:3,noon:4,font:5,settled:5});}],
  ["m4 status owner bypassed by a direct .left write",[['  $(".cn").textContent="—";writePrayerStatus("—","Prayer times unavailable");','  $(".cn").textContent="—";$(".nt").textContent="—";$(".left").textContent="Prayer times unavailable";']],src=>{assertSingleOwner(src);}]
];
for(const [name,edits,discriminate] of MUTANTS)test("E-09 mutant "+name+" is killed",{skip:!MUTATION_ROWS&&"mutation anchors belong to this tree's source"},async()=>{
  await discriminate(SOURCE);
  const mutant=mutate(edits);
  await assert.rejects(async()=>discriminate(mutant),e=>e instanceof assert.AssertionError,"only an actual assertion failure detects the mutant");
});
