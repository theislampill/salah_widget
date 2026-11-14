"use strict";
// R0030 mutation controls (issue 97 stage 6, review F1-F3/D1). Each mutant is one exact edit of the settings
// source [target, replacement]; tests/r0030-reset-authority-mutations.test.cjs proves that every target
// occurs exactly once in the authored and generated page and that the named case kills it.
const MUTANTS={
  "keep-pre-dispatch-dirty":['reset=_setReset={prefOwner,session:_setSession,phase:"detecting",save:false,release:null};\n  _setDirty=false;','reset=_setReset={prefOwner,session:_setSession,phase:"detecting",save:false,release:null};'],
  "dirty-cleared-before-clear-result":['_invalidateSetLocation(); const prefOwner={..._setPrefVersions};','_invalidateSetLocation(); _setDirty=false; const prefOwner={..._setPrefVersions};'],
  "later-session-rewrite":["if(_setSession!==reset.session) return;                    // never rewrite","if(false) return;                    // never rewrite"],
  "close-ends-reset":["_setOpen=false; _setSession++; _invalidateSetLocation(); clearTimeout","_setOpen=false; _setSession++; _invalidateSetLocation(); _dropReset(); clearTimeout"],
  "label-ends-reset":['if(id!=="set-label"){                                      // a display-name edit','_dropReset(); if(id!=="set-label"){                                      // a display-name edit'],
  "coordinate-keeps-reset":["      _dropReset();\n      _setLocationEvidence=","      _setLocationEvidence="],
  "candidate-keeps-reset":["  _dropReset();                                                // a shown candidate","  // a shown candidate"],
  "search-start-ends-reset":["  const owner=_captureSetLookup(), bias=_setHomeCC;","  _dropReset(); const owner=_captureSetLookup(), bias=_setHomeCC;"],
  "gps-fix-keeps-reset":['_setLocationOrigin==="browser-geolocation") _dropReset(); });','_setLocationOrigin==="browser-geolocation") {} });'],
  "gps-click-ends-reset":["const evidence=_setLocationEvidence, done=_usePrecise()","_dropReset(); const evidence=_setLocationEvidence, done=_usePrecise()"],
  // (Removing the post-clear drop is equivalent: the new owner replaces `_setReset` and clears `_setDirty`.)
  "second-reset-drops-before-clear":['_invalidateSetLocation(); const prefOwner={..._setPrefVersions};','_invalidateSetLocation(); _dropReset(); const prefOwner={..._setPrefVersions};'],
  "drop-deferred-edits":['if(reset.save&&Object.keys(fields).length) _applySettings({...CONFIG,...fields},reset.phase==="applied");','if(false) _applySettings({...CONFIG,...fields},reset.phase==="applied");'],
  "close-keeps-dirty":["    if(_setDirty) reset.save=true;\n    _setDirty=false;\n","    if(_setDirty) reset.save=true;\n"],
  "failed-owner-kept":['_setReset=null; if(reset.phase==="failed") _setResetFailed=true;','if(reset.phase!=="failed") _setReset=null; if(reset.phase==="failed") _setResetFailed=true;'],
  "failed-notice-repeats":['if(_setResetFailed){ _setResetFailed=false; _setStatus(','if(_setResetFailed){ _setStatus('],
  "stale-storage-marker":['if(CONFIG&&CONFIG.source==="localStorage"&&CONFIG.origin) CONFIG={...CONFIG,source:CONFIG.origin,savedAt:null};',""],
  "drop-apply-catch":["applyConfig(cfg,{save}).then(()=>_settleSettingsApply(null,id),e=>_settleSettingsApply(e,id));","applyConfig(cfg,{save}).then(()=>_settleSettingsApply(null,id));"],
  "stale-success-clears-fault":["  if(id!==_setApplySeq) return;\n",""],
  // Fresh review (05a91ab1) survivors n02, n08, n07, n10:
  "gps-adoption-ignores-evidence":['_ownsSetLookup(owner)&&_setLocationEvidence!==evidence&&_setLocationOrigin==="browser-geolocation"','_ownsSetLookup(owner)&&_setLocationOrigin==="browser-geolocation"'],
  "stale-failure-writes-fault":["  if(id!==_setApplySeq) return;\n","  if(id!==_setApplySeq&&error==null) return;\n"],
  "reset-apply-unordered":["const applyId=++_setApplySeq;","const applyId=_setApplySeq;"],
  "site-line-empty-label":['(c.label?": "+c.label:".")','": "+(c.label||"")'],
  // Owner clarification of G2(i) (2026-11-14): an unresolved search query is not a display-name edit.
  "query-not-recorded":['  _setUnresolved={text:_byId("set-label").value};',"  "],
  "retype-keeps-query":['    if(id==="set-label") _setUnresolved=null;',"    "],
  // Equivalent, not counted: clearing the marker on Shift+Enter or on a shown candidate is redundant because both
  // also set _setLabelBase to the field text, so a still-matching marker yields the same name.
  "base-ignores-candidate":["_setLabelBase=_setCandOwner.label;","_setLabelBase=_setLabelBase;"],
  "form-commit-keeps-query":['  if(_unresolvedLabel(_byId("set-label").value)) cfg.label=_setLabelBase.trim();',""],
  "reset-commit-keeps-query":["if(_unresolvedLabel(fields.label)) delete fields.label;",""],
  "target-named-by-query":["    if(_unresolvedLabel(c.label)) c.label=targetLabel;",""],
  "landing-restores-query":["if(_unresolvedLabel(prefs.label)) delete prefs.label;",""],
  "drop-reset-catch":["try{ await applyConfig(c,{save:false,reset:true}); }catch(e){ fault=e; }","await applyConfig(c,{save:false,reset:true});"],
  "commit-after-reset-fault":["if(!_setOpen){ if(fault) _setReset=null; else _commitSettings(); return; }","if(!_setOpen){ _commitSettings(); return; }"],
  "unconditional-detect":['if(policy&&policy.mode==="preferLocal"&&policy.cfg&&!policy.needsDetect){',"if(false){"],
  "reopen-loses-pending-edits":["if(pending){ for(const key in pending)","if(false){ for(const key in pending)"],
  "held-never-released":['if(reset.phase!=="applied"&&reset.phase!=="failed"){ if(reset.release) reset.release(); return; }','if(reset.phase!=="applied"&&reset.phase!=="failed"){ return; }'],
  "held-no-owner-check":["await new Promise(go=>{ reset.release=go; }); if(_setReset!==reset) return; }","await new Promise(go=>{ reset.release=go; }); }"],
  "failure-reopens-form-authority":['else { reset.phase="failed"; if(!_setOpen) _commitSettings(); }','else { _setReset=null; }'],
};
module.exports={MUTANTS};
