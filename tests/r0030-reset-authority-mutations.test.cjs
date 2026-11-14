"use strict";
// R0030 / issue 97 stage 6 (ES30-14): each mutant of tests/r0030-mutants.cjs targets exactly one
// place in the authored and generated page, and a named case of r0030-reset-authority.test.cjs fails
// under it for a behavioural reason (not a bootstrap error). The unmutated suite is the positive control.
const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path"),{spawnSync}=require("node:child_process");
const {MUTANTS}=require("./r0030-mutants.cjs");
const root=path.resolve(__dirname,".."),suite=path.join(__dirname,"r0030-reset-authority.test.cjs");
const KILLERS={
  "keep-pre-dispatch-dirty":"ES30-02 R1: pre-dispatch edit + Reset + close during detection",
  "dirty-cleared-before-clear-result":"ES30-08 denied clear keeps pre-dispatch dirtiness",
  "later-session-rewrite":"ES30-13 Reset apply settling in a later session does not rewrite",
  "close-ends-reset":"ES30-02 R1: pre-dispatch edit + Reset + close during detection",
  "label-ends-reset":"ES30-03 R2: display-name edit during detection then close",
  "coordinate-keeps-reset":"ES30-05 coordinate edit during detection supersedes Reset",
  "candidate-keeps-reset":"ES30-05 D1 a shown place-search candidate supersedes Reset",
  "search-start-ends-reset":"ES30-05 D1 a place search with no match does not end Reset",
  "gps-fix-keeps-reset":"ES30-05 D1 a GPS fix supersedes Reset",
  "gps-click-ends-reset":"F1 Reset, edit, close, reopen, denied GPS click, close",
  "second-reset-drops-before-clear":"F1 a second Reset whose clear fails leaves the first Reset",
  "drop-deferred-edits":"ES30-03 R2: display-name edit during detection then close",
  "close-keeps-dirty":"F2 close during a pending Reset leaves no uncommitted dirtiness behind",
  "failed-owner-kept":"F2 after a closed-panel detection failure the form owns location again",
  "failed-notice-repeats":"F2 the closed-panel failure notice is shown on the next open only",
  "stale-storage-marker":"ES30-06 R3: after a successful clear no surface claims a saved position",
  "drop-apply-catch":"ES30-12 close-save: injected bindConfig fault is observed",
  "stale-success-clears-fault":"F3 a stale successful apply does not withdraw a newer apply's failure line",
  "drop-reset-catch":"ES30-12 Reset apply fault is observed and reported",
  "gps-adoption-ignores-evidence":"N1 an earlier adopted GPS fix does not make a later denied GPS click end a Reset",
  "stale-failure-writes-fault":"F3 symmetric: a stale failed apply does not overwrite a newer apply's success",
  "reset-apply-unordered":"F3 the Reset apply is ordered too",
  "site-line-empty-label":"N3 preferLocal Reset to a hash site without a label",
  "commit-after-reset-fault":"F2 limit: a Reset apply fault with the panel closed drops the owner",
  "unconditional-detect":"ES30-10 N1: preferLocal hash site Reset makes no coarse request",
  "reopen-loses-pending-edits":"F1 Reset, edit, close, reopen, denied GPS click, close",
  "held-never-released":"ES30-13 detection lands while a later session is open",
  "held-no-owner-check":"F2 a held target released by a newer coordinate intent is not applied",
  "failure-reopens-form-authority":"ES30-08a G1-A/G1a(A1): detection fails after close",
};
// Equivalent under the current callers (stated, not counted): every `_dropReset` caller either sets the form
// dirty itself (coordinate input, shown candidate, GPS fix) or clears it by design (a cleared second Reset), so
// removing the `reset.save` -> `_setDirty` re-arm in `_dropReset` is not observable today; it stays as a guard.
// Fresh-review n11 (`_dropReset` keeps the failed-notice flag) is unobservable too: the flag is armed only by a
// close (`_commitSettings`, phase failed) and consumed by the next open, and no drop can happen while closed.
// n01/n03/n17 (redundant adoption guards) and n14 (no-op snapshot) are equivalent under current callers.
test("every R0030 mutant has a killer and every target is unique in authored and generated source",()=>{
  assert.deepEqual(Object.keys(KILLERS).sort(),Object.keys(MUTANTS).sort());
  for(const file of ["src/native/index.html","index.html"]){
    const page=fs.readFileSync(path.join(root,file),"utf8");
    for(const [name,[target,replacement]] of Object.entries(MUTANTS)){
      assert.equal(page.split(target).length-1,1,name+" target occurs exactly once in "+file);
      assert.notEqual(target,replacement,name);
    }
  }
});
for(const [name,killer] of Object.entries(KILLERS)){
  test(`mutant ${name} is killed by "${killer}"`,{timeout:120000},()=>{
    // A fresh runner: drop the parent's NODE_TEST_CONTEXT so the child reports its own TAP lines.
    const env={...process.env,R0030_MUTANT:name,R0030_REF:""};delete env.NODE_TEST_CONTEXT;
    const r=spawnSync(process.execPath,["--test","--test-reporter=tap",suite],{cwd:root,encoding:"utf8",env});
    const out=r.stdout+r.stderr;
    assert.notEqual(r.status,0,name+" must fail the behaviour suite");
    assert.ok(out.split("\n").some(line=>/^not ok \d+ - /.test(line)&&line.includes(killer)),name+" did not reach "+killer+"\n"+out.slice(0,4000));
    assert.doesNotMatch(out,/SyntaxError|ReferenceError|boundary missing/,"bootstrap failure is not mutation evidence");
  });
}
