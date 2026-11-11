"use strict";
// R0003 / issue #3 November increment (ES03-01..16): configuration-effect classification.
// Scenarios run the ACTUAL product applyConfig / resetForNewLocation / request slots / render loop through the
// existing r0003 harness (generated root index.html + config.js), and the actual settings code through the
// r0011 fixture. Each scenario takes {source} so the mutation controls reuse it over an in-memory mutant.
// Provider transport is the harness's deferred fetch double; no live request is ever made.
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const {harness,record,cfg,req,settle,copy,source,sourcePath}=require("./r0003-harness.cjs");
const repo=path.resolve(__dirname,"..");
const authoredPath=path.join(repo,"src/native/index.html");

// ---- the classifier block (pure) ------------------------------------------------------------------------
const BLOCK_START="// ---- R0003 configuration-effect contract",BLOCK_END="\nif(window.SalahConfig)";
function classifierBlock(raw){
  const a=raw.indexOf(BLOCK_START),b=raw.indexOf(BLOCK_END,a);
  if(a<0||b<a)throw new assert.AssertionError({message:"R0003 classifier block missing from product source"});
  return raw.slice(a,b);
}
// Evaluated in an EMPTY realm: if the classifier read any mutable widget global it would throw here.
function isolatedClassifier(raw=source()){
  const realm=vm.createContext({});
  vm.runInContext('"use strict";\n'+classifierBlock(raw)+"\n;globalThis.__api={classifyConfigChange,CONFIG_EFFECTS};",realm);
  return realm.__api;
}

// ---- established widget: A adopted, render loop running ------------------------------------------------
const ZONE="Asia/Riyadh";   // provider-adopted zone; the configuration hint stays UTC
async function established(options={},extra={}){
  const h=harness(options),base=cfg(10,"A",extra),applied=h.apply(base);
  req(h).ok(record(undefined,ZONE,"A"));await settle();await applied;await h.frame();
  return {h,base};
}
// Owned weather/radar attempts and R000D elapsed retry records that a cosmetic edit must leave alone.
function seedOwners(h){
  h.run('lastWxTry=111;lastRadarAt=222;_wxRetry.weather={startedAt:5,clock:"monotonic"};_wxRetry.radar={startedAt:7,clock:"monotonic"};'+
    'var __wxOp=beginRequest("weather"),__radarOp=beginRequest("radar"),__today=today;');
}
function ledger(h){
  return {...copy(h.run(`({generation:_runtimeGeneration,tz,cacheTz:_cacheTz,cacheKey:cacheKey(),sceneKey:_skySceneKey,
    pending:document.querySelector(".c").classList.contains("sky-pending"),todaySame:today===__today,lastWxTry,lastRadarAt,
    retry:{weather:_wxRetry.weather,radar:_wxRetry.radar},wxOwned:requestEligible(__wxOp),radarOwned:requestEligible(__radarOp),
    lastDate,loop:_loopStarted})`)),requests:h.requests.length,writes:h.writes.filter(w=>w.key.startsWith("salah:")).length};
}
const text=(h,sel)=>h.document.querySelector(sel).textContent;
const html=(h,sel)=>h.document.querySelector(sel).innerHTML;
// Never blocks on a broad acquisition: the call settles its synchronous effects and returns {pending}.
async function apply(h,next,opts="{save:false}"){h.run("var __next="+JSON.stringify(next)+";");const pending=h.run("applyConfig(__next,"+opts+")");
  await Promise.race([pending,settle()]);await settle();return {pending};}
async function settingsApply(w,next){w.run("var __n="+JSON.stringify(next)+";");const pending=w.run("applyConfig(__n,{save:true})");
  await Promise.race([pending,settle()]);await settle();return {pending};}

// The cosmetic edits of ES03-01..05. Each returns the presentation check it must satisfy.
const COSMETIC={
  label:{patch:{label:"A renamed"},immediate:h=>assert.equal(text(h,"#loc"),"A renamed","label is the directly owned header text")},
  time12:{patch:{time:"12"},frame:h=>{assert.match(text(h,".nt"),/^\d{1,2}:\d{2} (AM|PM)$/);
    for(const tm of html(h,".times").match(/class="tm">[^<]*/g))assert.match(tm,/(AM|PM)$/);}},
  dateLong:{patch:{datefmt:"DD MMMM YYYY"},frame:h=>assert.match(text(h,"#ce"),/^07 September 2026/)},
  appearance:{patch:{appearance:"contrast"},immediate:h=>assert.equal(h.document.querySelector(".c").dataset.appearance,"contrast")},
  identical:{patch:{}},
  mixedCosmetic:{patch:{label:"A mixed",time:"12",datefmt:"DD MMMM YYYY",appearance:"contrast"},
    immediate:h=>assert.equal(text(h,"#loc"),"A mixed"),frame:h=>{assert.match(text(h,"#ce"),/^07 September 2026/);assert.match(text(h,".nt"),/(AM|PM)$/);}},
};
async function cosmeticPreserves(name,options={}){
  const c=COSMETIC[name],{h,base}=await established(options);seedOwners(h);
  const before=ledger(h),nt=text(h,".nt");
  await apply(h,{...base,...c.patch});
  const after=ledger(h);
  assert.deepEqual(after,before,name+": no generation, request, zone/cache-key rollback, sky restart, throttle or retry-record reset");
  if(c.immediate)c.immediate(h);
  if(c.frame){
    assert.equal(h.run("_renderDirty"),true,name+": presentation is marked dirty for the next eligible frame");
    await h.frame();c.frame(h);
  }else if(name==="identical")assert.equal(text(h,".nt"),nt);
  assert.deepEqual(ledger(h),before,name+": the presentation frame adds no acquisition");
  return h;
}

// Genuine target/calculation/intent/evidence changes keep the existing broad path (ES03-08/09).
const GENUINE={
  lat:{patch:{lat:20}},lon:{patch:{lon:20}},method:{patch:{method:"3"}},school:{patch:{school:"1"}},
  tzHint:{patch:{tz:"America/New_York"}},units:{patch:{units:"c"}},lp:{patch:{lp:0.5}},seed:{patch:{seed:2}},
  evidencePlace:{patch:{locationEvidence:{source:"place",provider:"Nominatim",area:"Somewhere"}}},
  evidenceDevice:{patch:{source:"browser-geolocation",locationEvidence:{source:"browser-geolocation",accuracyM:12,acquiredAt:Date.parse("2026-09-07T11:00:00Z")}}},
  provenance:{patch:{source:"place"}},
  mixed:{patch:{label:"B",lat:20}},
  unknownField:{patch:{label:"A unknown",futureField:1}},
};
async function genuineBroad(name,options={},opts="{save:false}"){
  const g=GENUINE[name],{h,base}=await established(options);seedOwners(h);
  const before=ledger(h);
  const {pending:applying}=await apply(h,{...base,...g.patch},opts);
  const after=ledger(h);
  assert.equal(after.generation,before.generation+1,name+": broad path begins a new generation");
  assert.equal(after.wxOwned,false,name+": obsolete weather owner invalidated");assert.equal(after.radarOwned,false);
  assert.deepEqual(after.retry,{weather:null,radar:null});assert.equal(after.lastWxTry,0);assert.equal(after.lastRadarAt,0);
  assert.equal(after.todaySame,false);assert.equal(after.requests,before.requests+1,name+": a new prayer acquisition is issued");
  h.requests.at(-1).ok(record(undefined,ZONE,"new"));await settle();await applying;
  return h;
}
async function explicitResetEqual(options={}){
  const {h,base}=await established(options);seedOwners(h);const before=ledger(h);
  const {pending:applying}=await apply(h,{...base},"{save:false,reset:true}");
  const after=ledger(h);
  assert.equal(after.generation,before.generation+1,"explicit Reset is a real reset even with equal values");
  assert.equal(after.requests,before.requests+1);assert.equal(after.wxOwned,false);
  h.requests.at(-1).ok(record(undefined,ZONE,"reset"));await settle();await applying;return h;
}

// ES03-10/11: A -> B -> cosmetic edit of B -> late A. B commits; A stays rejected; the edit shows.
async function cosmeticDuringB(options={},late="ok"){
  const h=harness(options),a=h.apply(cfg(10,"A")),ar=req(h,undefined,10),b=h.apply(cfg(20,"B")),br=req(h,undefined,20);
  const generation=h.run("_runtimeGeneration"),requests=h.requests.length;
  await apply(h,{...cfg(20,"B"),label:"B renamed",time:"12"});
  assert.equal(h.run("_runtimeGeneration"),generation,"cosmetic edit keeps B's generation");
  assert.equal(h.requests.length,requests,"cosmetic edit issues no request");
  assert.equal(h.run("_requestSlots.current&&_requestSlots.current.lat"),20,"B still owns the current slot");
  if(late==="ok")ar.ok(record(undefined,"UTC","A-obsolete"));else ar.fail();
  await settle();await a;
  assert.equal(h.run("_requestSlots.current&&_requestSlots.current.lat"),20,"A's success/error/finally cannot release B");
  assert.equal(h.state().today,null,"A cannot commit");
  br.ok(record(undefined,"UTC","B-current"));await settle();await b;await h.frame();
  assert.equal(h.state().today.tag,"B-current","the legitimate in-flight B response still commits");
  assert.equal(h.run("_requestSlots.current"),null);
  assert.equal(text(h,"#loc"),"B renamed");assert.match(text(h,".nt"),/(AM|PM)$/);
  return h;
}
// ES03-10 A -> B -> A (new A2) with a cosmetic edit during A2: A1 stays obsolete by identity, not by value.
async function abaWithCosmetic(options={}){
  const h=harness(options),a1=h.apply(cfg(10,"A1")),r1=req(h,undefined,10),b=h.apply(cfg(20,"B")),rb=req(h,undefined,20),a2=h.apply(cfg(10,"A2"));
  const r2=h.requests.filter(r=>new URL(r.url).searchParams.get("latitude")==="10")[1];
  await apply(h,{...cfg(10,"A2"),label:"A2 renamed"});
  r1.ok(record(undefined,"UTC","A1-obsolete"));rb.ok(record(undefined,"UTC","B-obsolete"));await settle();await Promise.race([Promise.all([a1,b]),settle()]);
  assert.equal(h.state().today,null,"obsolete first A and B cannot commit by value equality");assert.equal(h.run("_requestSlots.current&&_requestSlots.current.lat"),10);
  r2.ok(record(undefined,"UTC","A2-current"));await settle();await Promise.race([a2,settle()]);await h.frame();
  assert.equal(h.state().today?.tag,"A2-current","the current A2 response commits");assert.equal(text(h,"#loc"),"A2 renamed");
  return h;
}
// D8: a hidden/paused widget is not rendered in the background; its first resumed frame shows the change.
async function hiddenThenResumed(options={}){
  const {h,base}=await established(options);seedOwners(h);const before=ledger(h),nt=text(h,".nt"),ce=text(h,"#ce");
  h.hide();assert.equal(h.frames.size,0);
  await apply(h,{...base,time:"12",datefmt:"DD MMMM YYYY"});
  assert.equal(h.frames.size,0,"no background frame is forced while hidden");
  assert.equal(text(h,".nt"),nt,"hidden widget is not re-rendered");assert.equal(text(h,"#ce"),ce);
  h.show();assert.equal(h.frames.size,1);await h.frame();
  assert.match(text(h,".nt"),/(AM|PM)$/,"first resumed frame shows the pending time format");
  assert.match(text(h,"#ce"),/^07 September 2026/,"first resumed frame shows the pending date format");
  assert.deepEqual(ledger(h),before);
  return h;
}
// ---- actual settings route (r0011 fixture: real settings form + applyConfig + persistence publisher) -----
const {widget}=require("./r0011-fixture.cjs");
const SAVED={v:1,lat:21.42,lon:39.83,tz:"Asia/Riyadh",label:"Makkah",method:"4",school:"0",time:"24",datefmt:"YYYY-MM-DD",units:"c",
  appearance:"glass",lp:0,seed:null,source:"manual",savedAt:null,locationEvidence:null};
function settingsWidget(options={}){
  const w=widget({seed:SAVED,...options});
  w.run('bindConfig(SalahConfig.loadLocal())');
  return w;
}
function blockStorage(w){const s=w.sandbox.localStorage,set=s.setItem;s.setItem=()=>{throw Object.assign(new Error("fixture denied"),{name:"SecurityError"});};return ()=>{s.setItem=set;};}
function effects(w){return {generation:w.run("_runtimeGeneration"),prayer:w.calls.prayer.length,weather:w.calls.weather,loop:w.calls.loop};}
// D1: an ordinary retry of a failed save with unchanged semantic configuration executes and reports the
// persistence attempt but restarts nothing; the R0011 session-only warning is preserved while storage fails.
async function failedSaveRetry(options={}){
  const w=settingsWidget(options),restore=blockStorage(w),next={...SAVED,label:"Makkah edit"};
  await settingsApply(w,next);
  assert.equal(w.run("_persistOutcome.status"),"session-only");
  const before=effects(w);
  await settingsApply(w,next);   // retry, still failing
  assert.equal(w.run("_persistOutcome.status"),"session-only","failed retry still reports the real outcome");
  assert.equal(w.json("document.querySelector('.buckle').classList.contains('persist-warning')"),true,"R0011 warning kept");
  assert.deepEqual(effects(w),before,"failed retry restarts nothing");
  restore();
  await settingsApply(w,next);   // retry, storage recovered
  assert.equal(w.run("_persistOutcome.status"),"saved","successful retry is executed and reported");
  assert.equal(w.json("document.querySelector('.buckle').classList.contains('persist-warning')"),false);
  assert.equal(w.run("SalahConfig.loadLocal().label"),"Makkah edit");
  assert.equal(w.run("CONFIG.source"),"localStorage");assert.equal(w.run("CONFIG.origin"),"manual");
  assert.deepEqual(effects(w),before,"successful retry restarts nothing");
  return w;
}
// ES03-07: acquisition evidence survives an unrelated saved edit through the actual settings close-save;
// savedAt is the storage receipt only (R0023 semantics).
async function evidenceSurvivesSave(options={}){
  const now=Date.now(),acquiredAt=now-3600000;
  const w=settingsWidget({now,seed:{...SAVED,source:"browser-geolocation",locationEvidence:{source:"browser-geolocation",accuracyM:12,acquiredAt}},...options});
  const evidence=w.json("CONFIG.locationEvidence"),before=effects(w);
  assert.equal(evidence.acquiredAt,acquiredAt);assert.equal(evidence.accuracyM,12);
  w.now(now+60000);
  w.run("_openSettings()");w.run('_byId("set-label").value="Makkah saved";_recordSetEdit({target:_byId("set-label")});');
  w.run("_closeSettings()");await settle();
  assert.deepEqual(w.json("CONFIG.locationEvidence"),evidence,"acquisition source/time/accuracy unchanged by the save");
  assert.deepEqual(w.json("SalahConfig.loadLocal().locationEvidence"),evidence);
  assert.equal(w.run("CONFIG.savedAt"),now+60000,"savedAt is the storage receipt");
  assert.equal(w.run("label"),"Makkah saved");
  assert.deepEqual(effects(w),before,"label save restarts nothing");
  return w;
}
// D1 through the actual Reset control: detected values equal to the current configuration still reset.
async function settingsResetEqual(options={}){
  const w=settingsWidget(options),before=effects(w);
  const resetting=w.run("_resetLocal()");
  assert.equal(w.calls.coarse.length,1);
  w.calls.coarse[0].resolve({ok:true,cfg:w.run("SalahConfig.normalize(CONFIG)"),source:"coarse-ip",provider:"fixture"});
  await settle();await settle();
  assert.equal(w.run("_runtimeGeneration"),before.generation+1,"Reset owns a real broad reset");
  assert.equal(w.calls.prayer.length,before.prayer+1);assert.equal(w.calls.weather,before.weather+1);
  w.calls.prayer.at(-1).resolve();await resetting;
  return w;
}
// ES03-01..03/05 through the real settings UI: open, edit, close (auto-save) -> presentation/no-op paths.
async function settingsCloseCosmetic(options={},edit="label"){
  const w=settingsWidget(options);const before=effects(w);
  w.run("_openSettings()");
  if(edit==="label"){w.run('_byId("set-label").value="Makkah al-Mukarramah";_recordSetEdit({target:_byId("set-label")});');}
  if(edit==="time"){w.run('_byId("set-time").value="12";_recordSetEdit({target:_byId("set-time")});');}
  if(edit==="none"){w.run('_recordSetEdit({target:_byId("set-label")});');}
  w.run("_closeSettings()");await settle();
  assert.deepEqual(effects(w),before,edit+": settings close-save restarts nothing");
  assert.equal(w.run("_persistOutcome.status"),"saved");
  if(edit==="label")assert.equal(w.run("label"),"Makkah al-Mukarramah");
  if(edit==="time")assert.equal(w.run("fmt24"),false);
  return w;
}

// Classifier decisions per field class, over the product source text raw.
function classifierDecisions(raw=source()){
  const {classifyConfigChange:classify}=isolatedClassifier(raw),A=copy(SAVED),c=(patch,intent={reset:false},base=A)=>classify(base,{...base,...patch},intent);
  for(const patch of [{label:"n"},{time:"12"},{datefmt:"DD MMMM YYYY"},{appearance:"contrast"},{label:"n",time:"12",datefmt:"MM/DD/YYYY",appearance:"contrast"}])
    assert.equal(c(patch).path,"presentation",JSON.stringify(patch));
  for(const patch of [{},{savedAt:123},{source:"localStorage",origin:"manual"}])assert.equal(c(patch).path,"none",JSON.stringify(patch));
  for(const patch of [{lat:1},{lon:1},{method:"2"},{school:"1"},{tz:"UTC"},{units:"f"},{lp:0.2},{seed:3},{source:"place"},{label:"n",lat:1},{futureField:true}])
    assert.equal(c(patch).path,"broad",JSON.stringify(patch));
  assert.equal(c({},{reset:true}).path,"broad","explicit reset intent is not swallowed by equality");
  assert.equal(classify(null,A,{reset:false}).path,"broad","no accepted configuration");
  assert.equal(c({lat:-0},{reset:false},{...A,lat:0}).path,"none","signed zero is the same coordinate");
  // D2: same coordinates, any evidence difference.
  const ev={intent:"device-position",source:"browser-geolocation",accuracyM:12,acquiredAt:1000,provider:null,area:null,bounds:null},E={...A,locationEvidence:ev};
  for(const [k,v] of [["intent","fixed-site"],["source","legacy"],["accuracyM",13],["acquiredAt",2000],["provider","P"],["area","Z"],
    ["bounds",{south:1,north:2,west:3,east:4}],["extra",1]])
    assert.equal(c({locationEvidence:{...ev,[k]:v}},{reset:false},E).path,"broad","evidence "+k);
  assert.equal(c({locationEvidence:null},{reset:false},E).path,"broad");
  const B={...E,locationEvidence:{...ev,bounds:{south:1,north:2,west:3,east:4}}};
  assert.equal(c({locationEvidence:{...ev,bounds:{south:1,north:2,west:3,east:5}}},{reset:false},B).path,"broad");
  assert.equal(c({locationEvidence:{...ev,bounds:{south:1,north:2,west:3,east:4}}},{reset:false},B).path,"none");
  // Coarse acquisition inputs: omitted by the settings form (carried by locationEvidence) vs truly changed.
  const C={...A,source:"coarse-ip",detectProvider:"GeoJS",area:"Makkah, SA",accuracy:20};
  const omitted={...C};delete omitted.detectProvider;delete omitted.area;delete omitted.accuracy;
  assert.equal(classify(C,omitted,{reset:false}).path,"none");
  assert.equal(classify(C,{...omitted,label:"n"},{reset:false}).path,"presentation");
  for(const [k,v] of [["detectProvider","ipinfo"],["area","Elsewhere"],["accuracy",5]])assert.equal(c({[k]:v},{reset:false},C).path,"broad",k);
}
// Every key of every real configuration producer has a row, and every row has a producer.
async function tableCoverage(raw=source(),options={}){
  const {CONFIG_EFFECTS}=isolatedClassifier(raw),keys=new Set();
  const realm=vm.createContext({URLSearchParams,Intl,AbortController,setTimeout,clearTimeout,console});realm.window=realm;
  vm.runInContext(fs.readFileSync(path.join(repo,"config.js"),"utf8"),realm);
  const S=realm.SalahConfig,add=o=>Object.keys(o).forEach(k=>keys.add(k));
  add(S.normalize({}));add(S.resolve("#lat=1&lon=2&tz=UTC&label=x&method=4&school=1&time=12&datefmt=long&units=c&appearance=contrast&lp=0.3&seed=4").cfg);
  const store=new Map(),storage={getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)};
  S.saveLocal({...SAVED,origin:"place"},storage);add(S.loadLocal(storage));
  realm.fetch=async()=>({ok:true,status:200,json:async()=>({latitude:"21.4",longitude:"39.8",city:"Makkah",region:"Makkah",country:"SA",country_code:"SA",timezone:"Asia/Riyadh",accuracy:20})});
  const det=await S.coarseDetect({timeoutMs:1000});assert.equal(det.ok,true);add(det.cfg);add(S.applyHashPrefs(det.cfg,{label:"y"}));
  const w=settingsWidget(options);add(w.json("_settingsFormToConfig()"));
  const table=new Set(Object.keys(CONFIG_EFFECTS));
  for(const k of keys)assert(table.has(k),"config field without an effect row: "+k);
  for(const k of table)assert(keys.has(k),"effect row without a real producer: "+k);
  for(const [k,row] of Object.entries(CONFIG_EFFECTS))assert(["none","presentation","broad"].includes(row.path),k);
}

module.exports={classifierDecisions,tableCoverage,harness,record,cfg,req,settle,copy,source,sourcePath,authoredPath,classifierBlock,isolatedClassifier,established,seedOwners,
  ledger,apply,text,COSMETIC,GENUINE,cosmeticPreserves,genuineBroad,explicitResetEqual,cosmeticDuringB,abaWithCosmetic,hiddenThenResumed,
  evidenceSurvivesSave,settingsWidget,failedSaveRetry,settingsResetEqual,settingsCloseCosmetic,SAVED,BLOCK_START};
