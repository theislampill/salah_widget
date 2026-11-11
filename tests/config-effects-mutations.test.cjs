"use strict";
// R0003 mutation controls. Each mutant is a disposable in-memory edit of the ACTUAL generated product
// (root index.html, never written to disk) and must fail a named healthy scenario from
// config-effects-fixture.cjs for its intended reason (asserted by the failure message). The healthy runs of
// the same scenarios are the GREEN cases in config-effects-state.test.cjs.
const test=require("node:test"),assert=require("node:assert/strict");
const F=require("./config-effects-fixture.cjs");
const T={timeout:10000};
function edit(raw,needle,replacement){
  assert.equal(raw.split(needle).length-1,1,"mutation site must be unique: "+needle);
  return raw.replace(needle,replacement);
}
const PRESENTATION="    setLocLabel();                                  // directly owned header text\n";
const MUTANTS={
  m1_label_broad:[r=>edit(r,'label:{kind:"label",path:"presentation"}','label:{kind:"label",path:"broad"}'),
    raw=>F.cosmeticPreserves("label",{source:raw}),/label: no generation/],
  m2_time_broad:[r=>edit(r,'time:{kind:"time-format",path:"presentation"}','time:{kind:"time-format",path:"broad"}'),
    raw=>F.cosmeticPreserves("time12",{source:raw}),/time12: no generation/],
  m3_datefmt_broad:[r=>edit(r,'datefmt:{kind:"date-format",path:"presentation"}','datefmt:{kind:"date-format",path:"broad"}'),
    raw=>F.cosmeticPreserves("dateLong",{source:raw}),/dateLong: no generation/],
  m4_identical_is_change:[r=>edit(r,'if(change.path==="none"){ CONFIG=cfg; return; }','if(false){ CONFIG=cfg; return; }'),
    raw=>F.cosmeticPreserves("identical",{source:raw}),/identical: no generation/],
  m5_coordinates_cosmetic:[r=>edit(r,'lat:{kind:"location-target",path:"broad"}, lon:{kind:"location-target",path:"broad"}','lat:{kind:"location-target",path:"presentation"}, lon:{kind:"location-target",path:"presentation"}'),
    raw=>F.genuineBroad("lat",{source:raw}),/lat: broad path begins a new generation/],
  m6_method_school_cosmetic:[r=>edit(r,'method:{kind:"calculation",path:"broad"}, school:{kind:"calculation",path:"broad"}','method:{kind:"calculation",path:"presentation"}, school:{kind:"calculation",path:"presentation"}'),
    raw=>F.genuineBroad("method",{source:raw}),/method: broad path begins a new generation/],
  m7_evidence_ignored_compare_coordinates_only:[r=>edit(r,'else if(row.compare==="evidence") differs=!sameConfigEvidence(accepted[key],proposed[key]);','else if(row.compare==="evidence") differs=false;'),
    raw=>F.genuineBroad("evidencePlace",{source:raw}),/evidencePlace: broad path begins a new generation/],
  m8a_reset_swallowed_by_equality:[r=>edit(r,'if(intent&&intent.reset) return','if(false) return'),
    raw=>F.explicitResetEqual({source:raw}),/explicit Reset is a real reset/],
  m8b_reset_control_drops_intent:[r=>edit(r,'await applyConfig(c,{save:false,reset:true});','await applyConfig(c,{save:false});'),
    raw=>F.settingsResetEqual({source:raw}),/Reset owns a real broad reset/],
  m9_save_retry_restarts:[r=>edit(r,'if(change.path==="none"){ CONFIG=cfg; return; }','if(change.path==="none"&&!opts.save){ CONFIG=cfg; return; }'),
    raw=>F.failedSaveRetry({source:raw}),/failed retry restarts nothing/],
  m10_cosmetic_bumps_generation:[r=>edit(r,PRESENTATION,"    beginRuntimeGeneration();\n"+PRESENTATION),
    raw=>F.cosmeticPreserves("label",{source:raw}),/label: no generation/],
  m11_cosmetic_clears_throttles_and_retry:[r=>edit(r,PRESENTATION,"    lastWxTry=0;lastRadarAt=0;_wxRetry.weather=null;_wxRetry.radar=null;\n"+PRESENTATION),
    raw=>F.cosmeticPreserves("label",{source:raw}),/label: no generation/],
  m12_unknown_field_cosmetic:[r=>edit(r,"    if(!row) differs=true;\n","    if(!row) continue;\n"),
    raw=>F.genuineBroad("unknownField",{source:raw}),/unknownField: broad path begins a new generation/],
  m13_cosmetic_skips_render_dirty:[r=>edit(r,"    _renderDirty=true;                              // time/date strings on the next eligible (visible) frame\n",""),
    raw=>F.hiddenThenResumed({source:raw}),/first resumed frame shows the pending time format/],
  m14_table_row_missing:[r=>edit(r,', seed:{kind:"seed",path:"broad"}',''),
    raw=>F.tableCoverage(raw,{source:raw}),/config field without an effect row: seed/],
  // Issue mutants not covered above.
  m15_stale_timezone_via_bindConfig:[r=>edit(r,PRESENTATION,"    bindConfig(cfg);\n"+PRESENTATION),
    raw=>F.cosmeticPreserves("label",{source:raw}),/label: no generation/],
  m16_renew_acquiredAt_on_save:[r=>edit(r,'if(r.ok){ cfg.origin=cfg.origin||cfg.source;','if(r.ok){ cfg.locationEvidence={...cfg.locationEvidence,acquiredAt:Date.now()}; cfg.origin=cfg.origin||cfg.source;'),
    raw=>F.evidenceSurvivesSave({source:raw}),/acquisition source\/time\/accuracy unchanged/],
  // Ownership by target VALUE instead of identity (and no expiry of superseded attempts): first A, whose
  // coordinates equal the current A2, would be accepted again. A single-fence mutant is inert (3.11), so the
  // supersession loop that expires/cancels/aborts old attempts is removed as well.
  m17_revive_oldA_by_equality:[r=>edit(edit(r,"return !!op && op.generation===_runtimeGeneration && _requestSlots[op.kind]===op;",
      "const s=_requestSlots[op&&op.kind]; return !!op && !!s && s.lat===op.lat && s.lon===op.lon;"),"    const a=op&&op.attempt; if(!a) continue;\n","    continue;\n"),
    raw=>F.abaWithCosmetic({source:raw}),/obsolete first A and B cannot commit by value equality/],
  m18_suppress_storage_warning:[r=>edit(r,'    _publishPersistence("save",r);                 // publish before any awaited provider work','    if(r.ok)_publishPersistence("save",r);'),
    raw=>F.failedSaveRetry({source:raw}),/session-only|Cannot read properties of null/],
  // Reconciliation onto R0026 (7f2e8d16): the evidence seam must classify every field R0026's delivered
  // place evidence carries. Dropping `provider` fails closed (an identical copy turns broad).
  m19_evidence_field_unclassified:[r=>edit(r,'["intent","source","accuracyM","acquiredAt","provider","area","bounds"]','["intent","source","accuracyM","acquiredAt","area","bounds"]'),
    raw=>F.admittedEvidenceSeam(raw),/every delivered evidence key is classified: place\/Nominatim/],
};
for(const [name,[mutate,scenario,reason]] of Object.entries(MUTANTS))test("mutant "+name+" is killed",T,async()=>{
  const raw=mutate(F.source());
  await assert.rejects(()=>Promise.resolve().then(()=>scenario(raw)),e=>{assert.match(String(e&&e.message),reason);return true;});
});
test("healthy control: every mutated scenario passes on the actual product source",{timeout:60000},async()=>{
  const raw=F.source();
  for(const [,[,scenario]] of Object.entries(MUTANTS))await scenario(raw);
});
