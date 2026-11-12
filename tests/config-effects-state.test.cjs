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
test("ES03-01..05/09/13 classifier decisions per field class",T,()=>F.classifierDecisions());
test("ES03-14 table covers every field of every real configuration producer, and nothing else",T,()=>F.tableCoverage());
test("ES03-07/09 D2 evidence seam consumes R0026's delivered admission and evidence contract",T,()=>F.admittedEvidenceSeam());
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
    assert.equal(raw.split("applyConfig(").length-1,3,"definition, settings close-save and Reset: no other caller");
  }
});
