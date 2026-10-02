"use strict";
const test=require("node:test"),assert=require("node:assert/strict");
const {source,copy,record,harness,cfg,req,settle}=require("./r0003-harness.cjs");
test("R0003 actual applyConfig A then B: obsolete A cannot change current data, zone or B cache",async()=>{
  const h=harness(),a=h.apply(cfg(10,"A")),ar=req(h),b=h.apply(cfg(20,"B")),br=req(h,"07-09-2026",20);
  br.ok(record(undefined,"UTC","B-current"));await settle();await b;
  const before=h.writes.length;ar.ok(record(undefined,"UTC","A-obsolete"));await settle();await a;
  assert.equal(h.state().today.tag,"B-current");assert.equal(h.writes.length,before);assert.equal(h.state().lat,20);
});

test("R0003 positive actual applyConfig: later B succeeds after early A completion",async()=>{
  const h=harness(),a=h.apply(cfg(10,"A")),ar=req(h),b=h.apply(cfg(20,"B")),br=req(h,"07-09-2026",20);
  ar.ok(record(undefined,"UTC","A-early"));await settle();await a;br.ok(record(undefined,"UTC","B-current"));await settle();await b;
  assert.equal(h.state().today.tag,"B-current");assert.equal(h.state().lat,20);
});

test("R0003 ABA identity: original A remains obsolete when coordinates return to A",async()=>{
  const h=harness(),a1=h.apply(cfg(10,"A1")),r1=req(h),b=h.apply(cfg(20,"B")),rb=req(h,undefined,20),a2=h.apply(cfg(10,"A2"));
  const r2=h.requests.filter(r=>r.url.includes("/timings/07-09-2026?")&&new URL(r.url).searchParams.get("latitude")==="10")[1];
  r2.ok(record(undefined,"UTC","A2-current"));await settle();await a2;rb.ok(record(undefined,"UTC","B-obsolete"));await settle();await b;r1.ok(record(undefined,"UTC","A1-obsolete"));await settle();await a1;
  assert.equal(h.state().today.tag,"A2-current");
});

function observed(h){return {state:h.state(),writes:copy(h.writes),cache:[...h.storage],errors:copy(h.errors)};}
for(const [name,extra]of [["method-only",{method:"3"}],["school-only",{school:"1"}]]) test(`R0003 same coordinates ${name} owns its captured request and cache`,async()=>{
  const h=harness(),a=h.apply(cfg(10,"old")),old=req(h),b=h.apply(cfg(10,"new",extra));
  const current=h.requests.filter(r=>r.url.includes("/timings/07-09-2026?"))[1],url=new URL(current.url);
  assert.equal(url.searchParams.get("method"),extra.method||"2");assert.equal(url.searchParams.get("school"),extra.school||"0");
  current.ok(record(undefined,"UTC","selected"));await settle();await b;const before=observed(h);
  old.ok(record(undefined,"UTC","old"));await settle();await a;assert.deepEqual(observed(h),before);
  assert.ok(h.writes.some(w=>w.key===`salah:10|10|UTC|${extra.method||2}|${extra.school||0}`));
});
test("R0003 obsolete rejection and retained old timer cannot release or report over B",async()=>{
  const h=harness(),a=h.apply(cfg(10,"A")),old=req(h),oldTimer=[...h.timers.values()][0].fn,b=h.apply(cfg(20,"B")),current=req(h,undefined,20);
  await settle();assert.equal(h.run("_requestSlots.current.lat"),20);const before=observed(h);
  oldTimer();old.fail();await settle();await a;assert.deepEqual(observed(h),before);assert.equal(h.run("_requestSlots.current.lat"),20);
  current.ok(record(undefined,"UTC","B-current"));await settle();await b;assert.equal(h.state().today.tag,"B-current");assert.equal(h.run("_requestSlots.current"),null);
});
test("R0003 obsolete tomorrow body cannot enter new selection or its cache",async()=>{
  const h=harness();h.seed(record(undefined,"UTC","A"));h.run("render()");const old=req(h,"08-09-2026");
  old.headers.resolve({ok:true,status:200,json:()=>old.body.promise});await settle();const b=h.apply(cfg(20,"B"));req(h,undefined,20).ok(record(undefined,"UTC","B"));await settle();await b;
  const before=observed(h);old.body.resolve({code:200,status:"OK",data:record("08-09-2026","UTC","A-next")});await settle();assert.deepEqual(observed(h),before);
});
test("R0003 winning response persists and reloads through actual selected-cache loader",async()=>{
  const h=harness(),a=h.apply(cfg(10,"A")),old=req(h),b=h.apply(cfg(20,"B"));req(h,undefined,20).ok(record(undefined,"UTC","B"));await settle();await b;old.ok(record(undefined,"UTC","A"));await settle();await a;
  const reload=harness({hash:"#lat=20&lon=20&tz=UTC&method=2",offline:true});for(const [k,v]of h.storage)reload.storage.set(k,v);
  const boot=reload.boot();await reload.advance(2700);await boot;assert.equal(reload.state().today.tag,"B");assert.equal(reload.writes.length,0);assert.ok(reload.paints.length>0);
});
test("R0003 independent central slots retain B owners after A cleanup for all remote kinds",()=>{
  const h=harness();
  for(const kind of ["current","prefetch","weather","radar"]){
    h.run(`var old_${kind}=beginRequest('${kind}','07-09-2026')`);
  }
  h.run("beginRuntimeGeneration()");
  for(const kind of ["current","prefetch","weather","radar"]){
    assert.equal(h.run(`beginRequest('${kind}','08-09-2026')!==null`),true);
    assert.equal(h.run(`finishRequest(old_${kind})`),false);assert.equal(h.run(`_requestSlots.${kind}.requestedDay`),"08-09-2026");
  }
});
test("R0003 abort removal leaves stale rejection and healthy B commitment intact",async()=>{
  const before='controller:typeof AbortController!=="undefined"?new AbortController():null';assert.equal(source().split(before).length-1,1);
  const h=harness({source:source().replace(before,"controller:null")}),a=h.apply(cfg(10,"A")),old=req(h),b=h.apply(cfg(20,"B"));
  req(h,undefined,20).ok(record(undefined,"UTC","B"));await settle();await b;const state=observed(h);old.ok(record(undefined,"UTC","A"));await settle();await a;
  assert.deepEqual(observed(h),state);assert.equal(h.state().today.tag,"B");assert.ok(h.requests.every(r=>!r.init.signal));
});
test("R0003 mutant unconditional finally is killed by replacement-slot ownership",async()=>{
  const before="if(!requestEligible(op)) return false;\n  _requestSlots[op.kind]=null; return true;";assert.equal(source().split(before).length-1,1);
  const h=harness({source:source().replace(before,"_requestSlots[op.kind]=null; return true;")});h.apply(cfg(10,"A"));h.apply(cfg(20,"B"));await settle();
  assert.throws(()=>assert.equal(h.run("_requestSlots.current && _requestSlots.current.lat"),20));
});
test("R0003 historical Madinah/Riyadh to New York race preserves exact winning zone and Asr",async()=>{
  // Accepted CLOCK computes model parts from the epoch; 16Z is actual New York noon.
  const h=harness({epoch:"2026-09-07T16:00:00Z"});
  const madinah=cfg(24.47,"Madinah",{lon:39.61,method:"4"}),newYork=cfg(40.71,"New York",{lon:-74.01});
  const dataA=record(undefined,"Asia/Riyadh","A"),dataB=record(undefined,"America/New_York","B");
  Object.assign(dataA.timings,{Fajr:"04:46",Sunrise:"06:00",Dhuhr:"12:00",Asr:"15:49",Maghrib:"18:00",Sunset:"18:00",Isha:"19:30"});
  Object.assign(dataB.timings,{Fajr:"05:00",Sunrise:"06:00",Dhuhr:"12:00",Asr:"15:30",Maghrib:"18:00",Sunset:"18:00",Isha:"19:30"});
  const a=h.apply(madinah),old=req(h,undefined,24.47),b=h.apply(newYork);req(h,undefined,40.71).ok(dataB);await settle();await b;
  const before=observed(h);old.ok(dataA);await settle();await a;assert.deepEqual(observed(h),before);assert.equal(h.state().tz,"America/New_York");assert.equal(h.run("model().nextTime"),"15:30");
  assert.equal(JSON.parse(h.storage.get("salah:40.71|-74.01|UTC|2|0")).data.meta.timezone,"America/New_York");
});
test("R0003 equator/prime-meridian current acquisition preserves numeric zero coordinates",async()=>{
  const h=harness(),applied=h.apply(cfg(0,"zero"));req(h,undefined,0).ok(record(undefined,"UTC","zero"));await settle();await applied;
  assert.equal(h.state().lat,0);assert.equal(h.state().lon,0);assert.equal(h.state().today.tag,"zero");assert.ok(h.writes.some(w=>w.key==="salah:0|0|UTC|2|0"));
});

function pendingSky(h){
  const card=h.document.querySelector(".c"),mask=h.document.querySelector(".moon-mask-disc");
  assert.equal(card.classList.contains("sky-pending"),true);assert.equal(card.classList.contains("sky-initializing"),true);
  assert.equal(card.classList.contains("moon-ready"),false);assert.equal(mask.classList.contains("mask-on"),false);
  assert.equal(h.run("_skySceneKey"),null);assert.equal(h.run("_skyCommitted"),false);assert.equal(h.run("_skyMoonPresence"),0);
  assert.equal(h.run("_starsProjected"),false);assert.equal(h.run("_cloudReady"),false);
  assert.deepEqual(copy(h.run("[cloudState.covLow,cloudState.covMid,cloudState.covHigh]")),[0,0,0]);
}
function previousSky(h){
  // Explicit prior-scene input at the owned boundary, not a natural cold boot or
  // native paint witness. Its card has already left the authored pending state.
  h.document.querySelector(".c").classList.remove("sky-pending","sky-initializing");
  h.document.querySelector(".mphoto").setAttribute("href","fixture:decoded-map");
  h.run('_pbrReady=true;_skySceneKey="old";_skyCommitted=true;_skyMoonPresence=1;_starProjectionKey="old";_starsProjected=true;_cloudReady=true;cloudState.covLow=30;cloudState.covMid=40;cloudState.covHigh=50;_colDens=new Float32Array([0.4,0.8]);_cloudCv={width:325,height:185};_cloudCtx={clearRect:recordCloudClear};updateSkySurface();');
  assert.equal(h.document.querySelector(".moon-mask-disc").classList.contains("mask-on"),true);
}
function ownerEdit(raw,begin,end,needle,replacement){
  const a=raw.indexOf(begin),b=raw.indexOf(end,a+begin.length);assert.ok(a>=0&&b>a);const part=raw.slice(a,b);assert.ok(part.includes(needle));
  return raw.slice(0,a)+part.replace(needle,replacement)+raw.slice(b);
}

test("R0003 recording DOM seeds actual SKY markup classes before source callers",()=>{
  const raw=source(),authored=raw.match(/<div\s+class="([^"]*\bc\b[^"]*)"/);assert.ok(authored);
  const h=harness(),card=h.document.querySelector(".c");
  assert.equal(card.getAttribute("class"),authored[1]);assert.equal(card.classList.contains("c"),true);
  assert.equal(h.document.querySelector(".mphoto").tagName,"IMAGE");assert.equal(h.document.querySelector(".mphoto").getAttribute("href"),"");
  assert.equal(h.document.querySelector(".moon-mask-disc").getAttribute("fill"),"black");
});

test("R0003 SKY natural cold boot retains authored pending state through builders and acquisition",{timeout:5000},async()=>{
  const h=harness(),boot=h.boot();await Promise.race([boot,settle()]);pendingSky(h);
  assert.deepEqual(h.skyBuilders.map(b=>[b.kind,b.pending,b.sceneKey,b.projected]),[["stars",true,null,false],["weather",true,null,false]]);
  assert.equal(h.requests.length,1);req(h).ok(record(undefined,"UTC","boot-current"));await boot;
  assert.equal(h.state().today.tag,"boot-current");assert.equal(h.state()._loopStarted,true);
});

test("R0003 SKY invalid boot reentry drops explicitly seeded prior-scene permission before its guard",{timeout:5000},async()=>{
  const h=harness({hash:"#lat=10&lon=10&tz=UTC&method=2&simTime=12:99"});previousSky(h);await h.boot();pendingSky(h);
  assert.equal(h.requests.length,0);assert.equal(h.skyBuilders.length,0);assert.deepEqual(h.cloudClears,[[0,0,325,185]]);
  assert.deepEqual(Array.from(h.run("_colDens")),[0,0]);assert.equal(h.run("_pbrReady"),true);
});

test("R0003 SKY accepted reset clears old scene after config and generation change",{timeout:5000},async()=>{
  const h=harness();previousSky(h);const applied=h.apply(cfg(20,"B"));await Promise.race([applied,settle()]);pendingSky(h);
  assert.equal(h.run("_runtimeGeneration"),1);assert.equal(h.state().lat,20);assert.equal(h.state().today,null);
  assert.deepEqual(h.skyBuilders.map(b=>[b.lat,b.generation,b.pending]),[[20,1,true],[20,1,true]]);
  assert.deepEqual(h.cloudClears,[[0,0,325,185]]);assert.deepEqual(Array.from(h.run("_colDens")),[0,0]);
  req(h,undefined,20).ok(record(undefined,"UTC","B"));await applied;assert.equal(h.state().today.tag,"B");
});

test("R0003 SKY actual visibility rebases real elapsed cloud time and preserves held axes",{timeout:5000},async()=>{
  const h=harness();h.seed(record(),record("08-09-2026"));h.run("startRenderLoop()");await h.frame();
  h.run("_cloudMotion.phase=[0.2,0.3,0.4];_cloudMotion.life=[2,3,4];_cloudMotion.wander=5;");
  await h.advance(1500);h.hide();assert.equal(h.run("_cloudMotion.paused"),true);assert.equal(h.run("_cloudMotion.lastRt"),1500);assert.equal(h.frames.size,0);
  await h.advance(6500);h.show();assert.equal(h.run("_cloudMotion.paused"),false);assert.equal(h.run("_cloudMotion.lastRt"),6500);assert.equal(h.frames.size,1);
  assert.deepEqual(copy(h.run("[_cloudMotion.phase,_cloudMotion.life,_cloudMotion.wander]")),[[0.2,0.3,0.4],[2,3,4],5]);
  h.run('window.matchMedia=()=>({matches:true});');await h.frame();assert.equal(h.run("_cloudMotion.reduced"),true);assert.equal(h.run("_cloudMotion.lastRt"),6500);
});

test("R0003 SKY same-day provider-zone reanchor reaches the actual projection identity guard",{timeout:5000},async()=>{
  const h=harness({hash:"#lat=10&lon=10&tz=UTC&method=2&simTime=12:00"});h.seed(record(),record("08-09-2026"));
  h.run('_starCat=[{ra:0,sd:0,cd:1,b:1,tw:false,bright:false}];_starEls=[document.querySelector(".fixture-star")];projectStars(simDate());');
  const old=h.run("_starProjectionKey");assert.equal(h.run("_starsProjected"),true);
  const loaded=h.run("loadPrayerData()");req(h).ok(record(undefined,"Asia/Tokyo","same-day-Tokyo"));await loaded;
  assert.equal(h.state().lastDate,"07-09-2026");assert.equal(h.state().tz,"Asia/Tokyo");
  assert.notEqual(h.run("_starProjectionKey"),old);assert.match(h.run("_starProjectionKey"),/Asia\/Tokyo/);assert.equal(h.run("_starsProjected"),true);
});

test("R0003 SKY cold boot hook omission is non-discriminating with authored initial classes",{timeout:5000},async()=>{
  const raw=source(),omitted=ownerEdit(raw,"async function boot(){","// SINGLE rAF render clock","  beginSkyScene();\n","");
  const healthy=harness({source:raw}),mutant=harness({source:omitted}),boots=[healthy.boot(),mutant.boot()];await settle();
  const consumed=h=>({cardClass:h.document.querySelector(".c").getAttribute("class"),maskClass:h.document.querySelector(".moon-mask-disc").getAttribute("class"),
    ...copy(h.run("({sceneKey:_skySceneKey,committed:_skyCommitted,moonPresence:_skyMoonPresence,projected:_starsProjected,cloudReady:_cloudReady,coverage:[cloudState.covLow,cloudState.covMid,cloudState.covHigh]})")),
    builders:copy(h.skyBuilders),cloudClears:copy(h.cloudClears),requestUrls:h.requests.map(r=>r.url)});
  pendingSky(healthy);pendingSky(mutant);assert.deepEqual(consumed(mutant),consumed(healthy));
  req(healthy).ok(record(undefined,"UTC","cold-current"));req(mutant).ok(record(undefined,"UTC","cold-current"));await Promise.all(boots);
  assert.deepEqual(mutant.state(),healthy.state());assert.equal(healthy.state().today.tag,"cold-current");
});

for(const target of ["reset-begin","surface-drop","elapsed-rebase","projection-identity"]){
  test(`R0003 SKY ${target} mutation is killed by the actual boundary effect`,{timeout:5000},async()=>{
    let raw=source();
    if(target==="reset-begin")raw=ownerEdit(raw,"function resetForNewLocation(){","async function applyConfig(cfg, opts){","  beginSkyScene();\n","");
    if(target==="surface-drop")raw=ownerEdit(raw,"function beginSkyScene(){","function updateSkySurface(){","  updateSkySurface();\n","");
    if(target==="elapsed-rebase")raw=ownerEdit(raw,"function rebaseCloudMotion(paused){","function advanceCloudMotion(civilSeconds){","_cloudMotion.lastRt=_RAFNOW();","_cloudMotion.lastRt=0;");
    if(target==="projection-identity")raw=ownerEdit(raw,"function render(){","function updateSimClock(n){"," || _starProjectionKey!==skySceneIdentity()","");
    const h=harness({source:raw,...(target==="projection-identity"?{hash:"#lat=10&lon=10&tz=UTC&method=2&simTime=12:00"}:{})});
    if(target==="projection-identity"){
      h.seed(record(),record("08-09-2026"));h.run('_starCat=[{ra:0,sd:0,cd:1,b:1,tw:false,bright:false}];_starEls=[document.querySelector(".fixture-star")];projectStars(simDate());');
      const old=h.run("_starProjectionKey"),loaded=h.run("loadPrayerData()");req(h).ok(record(undefined,"Asia/Tokyo","same-day-Tokyo"));await loaded;
      assert.throws(()=>assert.notEqual(h.run("_starProjectionKey"),old),assert.AssertionError);return;
    }
    if(target==="elapsed-rebase"){
      h.seed(record(),record("08-09-2026"));h.run("startRenderLoop()");await h.advance(1500);h.hide();
      assert.throws(()=>assert.equal(h.run("_cloudMotion.lastRt"),1500),assert.AssertionError);return;
    }
    previousSky(h);
    const pending=target==="reset-begin"?h.apply(cfg(20,"B")):h.boot();await Promise.race([pending,settle()]);
    assert.throws(()=>pendingSky(h),assert.AssertionError);req(h,undefined,target==="reset-begin"?20:null).ok(record());await pending;
  });
}
