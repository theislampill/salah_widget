"use strict";
// R0003 / issue #3 November increment, ES03-01..16 source controls (docs/state-contracts/R0003.md).
// Scenarios live in config-effects-fixture.cjs (shared with config-effects-mutations.test.cjs). They run the
// actual generated product applyConfig/settings code; the classifier unit cases run the actual product block
// in an empty realm. Source-consumer evidence only; native qualification is tools/qa/run_r0003_native.py.
const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm"),path=require("node:path");
const F=require("./config-effects-fixture.cjs");
const T={timeout:10000};
const deepFreeze=o=>{if(o&&typeof o==="object"){Object.freeze(o);Object.values(o).forEach(deepFreeze);}return o;};

// ---- ES03-01/02/03/04/05/06: cosmetic edits through the actual applyConfig ----
for(const name of Object.keys(F.COSMETIC))test(`ES03-0x cosmetic ${name}: no generation/request/zone/scene/throttle/retry effect; presentation updates`,T,()=>F.cosmeticPreserves(name));
// ---- ES03-08/09/13 and D2/D3/D4: genuine changes keep the broad path ----
for(const name of Object.keys(F.GENUINE))test(`ES03-08/09/13 genuine ${name}: broad path invalidates obsolete owners and reacquires`,T,()=>F.genuineBroad(name));
test("D1 explicit Reset with values equal to the current configuration is a real broad reset (applyConfig intent)",T,()=>F.explicitResetEqual());
test("D1 actual settings Reset control passes the explicit reset intent (equal detected values still reset)",T,()=>F.settingsResetEqual());
// ---- ES03-10/11 ----
for(const late of ["ok","fail"])test(`ES03-10/11 cosmetic edit during A->B: B commits, late A ${late} rejected, edit shows`,T,()=>F.cosmeticDuringB({},late));
test("ES03-10 A->B->A with a cosmetic edit during the second A: first A and B stay obsolete",T,()=>F.abaWithCosmetic());
// ---- D8 ----
test("D8 hidden/paused widget: no background render; the first resumed frame shows the pending formats",T,()=>F.hiddenThenResumed());
// ---- ES03-07 ----
test("ES03-07 acquisition source/time/accuracy survive an unrelated saved edit; savedAt separate",T,()=>F.evidenceSurvivesSave());
// ---- ES03-05/12 and D1 retry ----
test("ES03-05/12 D1 failed-save retry: persistence executed and reported, warning kept, nothing restarted",T,()=>F.failedSaveRetry());
for(const edit of ["label","time","none"])test(`ES03-01/02/05 actual settings close-save (${edit}) takes the no-restart path`,T,()=>F.settingsCloseCosmetic({},edit));

// ---- ES03-13/14 D7: the pure classifier and its production-consumed table ----
test("D7 classifier is pure: runs in an empty realm, deterministic, does not mutate its inputs",T,()=>{
  const {classifyConfigChange:classify}=F.isolatedClassifier();
  const a=deepFreeze(F.copy({...F.SAVED,label:"x"})),b=deepFreeze(F.copy({...F.SAVED,label:"y"}));
  const r1=classify(a,b,{reset:false}),r2=classify(a,b,{reset:false});
  assert.deepEqual(r1,r2);assert.equal(r1.path,"presentation");assert.deepEqual([...r1.changed],["label"]);
  // The same realm-free text is what production runs (authored and generated agree byte for byte).
  assert.equal(F.classifierBlock(fs.readFileSync(F.authoredPath,"utf8")),F.classifierBlock(F.source()));
});
test("ES03-01..05/09/13 classifier decisions per field class",T,()=>{
  const {classifyConfigChange:classify}=F.isolatedClassifier(),A=F.copy(F.SAVED),c=(patch,intent={reset:false},base=A)=>classify(base,{...base,...patch},intent);
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
});
test("ES03-14 table covers every field of every real configuration producer, and nothing else",T,async()=>{
  const {CONFIG_EFFECTS}=F.isolatedClassifier(),keys=new Set();
  const realm=vm.createContext({URLSearchParams,Intl,AbortController,setTimeout,clearTimeout,console});realm.window=realm;
  vm.runInContext(fs.readFileSync(path.join(__dirname,"..","config.js"),"utf8"),realm);
  const S=realm.SalahConfig,add=o=>Object.keys(o).forEach(k=>keys.add(k));
  add(S.normalize({}));add(S.resolve("#lat=1&lon=2&tz=UTC&label=x&method=4&school=1&time=12&datefmt=long&units=c&appearance=contrast&lp=0.3&seed=4").cfg);
  const store=new Map(),storage={getItem:k=>store.get(k)??null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)};
  S.saveLocal({...F.SAVED,origin:"place"},storage);add(S.loadLocal(storage));
  realm.fetch=async()=>({ok:true,status:200,json:async()=>({latitude:"21.4",longitude:"39.8",city:"Makkah",region:"Makkah",country:"SA",country_code:"SA",timezone:"Asia/Riyadh",accuracy:20})});
  const det=await S.coarseDetect({timeoutMs:1000});assert.equal(det.ok,true);add(det.cfg);add(S.applyHashPrefs(det.cfg,{label:"y"}));
  const w=F.settingsWidget();add(w.json("_settingsFormToConfig()"));
  const table=new Set(Object.keys(CONFIG_EFFECTS));
  for(const k of keys)assert(table.has(k),"config field without an effect row: "+k);
  for(const k of table)assert(keys.has(k),"effect row without a real producer: "+k);
  for(const [k,row] of Object.entries(CONFIG_EFFECTS))assert(["none","presentation","broad"].includes(row.path),k);
});
test("ES03-14 D7 production consumes the table: applyConfig is the sole dispatcher, Reset passes explicit intent",T,()=>{
  for(const raw of [fs.readFileSync(F.authoredPath,"utf8"),F.source()]){
    const apply=raw.slice(raw.indexOf("async function applyConfig("),raw.indexOf("// Diagnostic control of the EXISTING native clock"));
    assert.equal(raw.split("classifyConfigChange(").length-1,2,"one definition and one call");
    assert.match(apply,/const change=classifyConfigChange\(CONFIG,cfg,\{reset:!!opts\.reset\}\);/);
    assert.ok(apply.indexOf("classifyConfigChange(")<apply.indexOf("SalahConfig.saveLocal("),"classified before persistence rewrites source/savedAt");
    assert.doesNotMatch(apply,/appearanceOnly/);
    assert.match(F.classifierBlock(raw),/CONFIG_EFFECTS\[key\]/);
    const reset=raw.slice(raw.indexOf("async function _resetLocal("),raw.indexOf("function _openSettings("));
    assert.match(reset,/await applyConfig\(c,\{save:false,reset:true\}\);/);
    assert.equal(raw.split("applyConfig(").length-1,4,"definition, settings close, Reset and nothing else");
  }
});
