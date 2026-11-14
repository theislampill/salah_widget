"use strict";
// R0030 mutation controls (issue 97 stage 6). Each mutant is one exact edit of the settings source
// [target, replacement]; tests/r0030-reset-authority-mutations.test.cjs proves that every target
// occurs exactly once in the authored and generated page and that the named case kills it.
const MUTANTS={
  "keep-pre-dispatch-dirty":['reset=_setReset={prefOwner,session:_setSession,phase:"detecting",save:false,release:null};\n  _setDirty=false;','reset=_setReset={prefOwner,session:_setSession,phase:"detecting",save:false,release:null};'],
  "dirty-cleared-before-clear-result":['_invalidateSetLocation(); _dropReset(); const prefOwner={..._setPrefVersions};','_invalidateSetLocation(); _dropReset(); _setDirty=false; const prefOwner={..._setPrefVersions};'],
  "later-session-rewrite":["if(_setSession!==reset.session) return;                    // never rewrite","if(false) return;                    // never rewrite"],
  "close-ends-reset":["_setOpen=false; _setSession++; _invalidateSetLocation(); clearTimeout","_setOpen=false; _setSession++; _invalidateSetLocation(); _dropReset(); clearTimeout"],
  "label-ends-reset":['if(id!=="set-label"){                                      // a display-name edit','_dropReset(); if(id!=="set-label"){                                      // a display-name edit'],
  "coordinate-keeps-reset":["      _dropReset();\n      _setLocationEvidence=","      _setLocationEvidence="],
  "search-keeps-reset":["  _dropReset();                                                // a place search","  // a place search"],
  "pin-keeps-reset":['_byId("set-pin").addEventListener("click",_dropReset);',""],
  "drop-deferred-edits":['if(reset.save) _applySettings({...CONFIG,..._newerSetPrefs(reset.prefOwner)},reset.phase==="applied");','if(false) _applySettings({...CONFIG,..._newerSetPrefs(reset.prefOwner)},reset.phase==="applied");'],
  "stale-storage-marker":['if(CONFIG&&CONFIG.source==="localStorage"&&CONFIG.origin) CONFIG={...CONFIG,source:CONFIG.origin,savedAt:null};',""],
  "drop-apply-catch":["applyConfig(cfg,{save}).then(()=>_settleSettingsApply(null),_settleSettingsApply);","applyConfig(cfg,{save}).then(()=>_settleSettingsApply(null));"],
  "drop-reset-catch":["try{ await applyConfig(c,{save:false,reset:true}); }catch(e){ fault=e; }","await applyConfig(c,{save:false,reset:true});"],
  "unconditional-detect":["if(policy&&policy.cfg&&!policy.needsDetect){","if(false){"],
  "reopen-loses-pending-edits":["if(pending){ for(const key in pending)","if(false){ for(const key in pending)"],
  "held-never-released":['if(reset.phase!=="applied"&&reset.phase!=="failed"){ if(reset.release) reset.release(); return; }','if(reset.phase!=="applied"&&reset.phase!=="failed"){ return; }'],
  "failure-reopens-form-authority":['else { reset.phase="failed"; if(!_setOpen) _commitSettings(); }','else { _setReset=null; }'],
};
module.exports={MUTANTS};
