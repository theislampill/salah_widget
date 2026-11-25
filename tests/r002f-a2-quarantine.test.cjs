'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {quarantineExperiment, quarantineCandidate: archived, canonicalQuarantineCandidate} = require('../tools/qa/r002f_a2_quarantine.cjs');
const quarantineCandidate=process.env.R002F_HISTORICAL_QUARANTINE==='1'?archived:canonicalQuarantineCandidate;
let observed;
const report=()=>observed??=quarantineExperiment(quarantineCandidate);

test('R2FA2-Q1: experimental data quarantine preserves withdrawal and reuses only a newly admitted current record', () => {
  const r = report();
  assert.equal(r.baseline.initialRecomputationsOnReturn, 1);
  assert.equal(r.continuous.initialRecomputationsOnReturn, 0);
  assert.equal(r.continuous.reuses, 1);
  assert.equal(r.continuous.currentAfterReturn, true);
  assert.equal(r.continuous.sourceAfterReturn, 'refined-terrain');
  assert.equal(r.continuous.hiddenPresentable, false);
  assert.equal(r.continuous.hiddenDetailAvailable, false);
  assert.equal(r.continuous.hiddenFallbacks, 1);
  assert.equal(r.continuous.quarantinedRecords, 1);
  assert.equal(r.continuous.quarantinedAfterReturn, 0);
  assert.equal(r.continuous.newWorkerRenders, 0);
  assert.equal(r.continuous.pendingTimersAfterReturn, 0);
});

test('R2FA2-Q2: scope, clock, phase, invalidation, and disposal reject the quarantined bytes', () => {
  const r = report();
  for (const row of r.rejections) {
    assert.equal(row.reuses, 0, row.name);
    assert.equal(row.quarantinedAfterReturn, 0, row.name);
    assert.equal(row.extraPublicationsOverBaseline, 0, row.name);
  }
  assert.equal(r.disposed.presentable, false);
  assert.equal(r.disposed.quarantined, 0);
  assert.equal(r.disposed.workerTerminated, true);
});

test('R2FA2-Q5: reentrant preparation can publish only a current record and leaves a valid successor intact', () => {
  const r=report();
  for(const row of r.preparation) {
    assert.equal(row.reuses,0,row.change);
    assert.equal(row.writes.length,1,row.change);
    assert.equal(row.writes[0].current,true,row.change);
    assert.equal(row.writes[0].source,'initial-v5',row.change);
    assert.equal(row.retiredStages,1,row.change);
    assert.equal(row.activeDetailIdentity,row.writes[0].identity,row.change);
  }
  for(const name of ['successor','successor-then-throw'])assert.equal(r.preparation.find(x=>x.change===name).successorPreserved,true,name);
  assert.ok(r.controls.droppedFinalFence.writes.some(x=>!x.current));
});
test('R2FA2-Q6: observed hidden round trips irrevocably withdraw custody before paused listener returns', () => {
  const r=report();
  for(const row of r.trips) {
    assert.equal(row.first,0,row.key);assert.equal(row.second,0,row.key);
    assert.equal(row.hiddenOrPausedWrites,0,row.key);
    assert.equal(row.pausedPresentable,false,row.key);
    assert.equal(row.reuses,0,row.key);
  }
  assert.equal(r.controls.skippedHiddenObservation.reuses,1);
  assert.equal(r.pairedReturn.stillPaused.presentable,false);
  assert.equal(r.pairedReturn.stillPaused.records,1);
  assert.equal(r.pairedReturn.stillPaused.newWrites,0);
  assert.equal(r.pairedReturn.reuses,1);
});
test('R2FA2-Q7: five dedicated views, both texture envelopes and origin identities survive new admission', () => {
  const r=report(),p=r.payload;
  assert.equal(p.reuses,1);
  assert.equal(p.records.length,1);
  assert.deepEqual(p.records[0].keys,['bytes','calendarLinear','calendarRgba','height','record','rgba','surfaceCoverage','surfaceExtent','surfaceLinear','surfaceSize','width']);
  assert.equal(p.records[0].distinctViews,true);
  assert.equal(p.records[0].bytes,8884800);
  assert.equal(p.surplusBytes,9331200);
  assert.equal(p.records[0].surplusReachable,false);
  assert.equal(r.controls.retainedEnvelope[0].surplusReachable,true);
  assert.equal(p.detail.length,2);assert.equal(p.blends.length,2);
  assert.equal(new Set(Object.values(p.originals)).size,5);
  for(const d of p.detail){
    assert.equal(d.sameViews,true);assert.equal(d.identity,p.originalIdentity);
    for(const key of ['surfaceLinear','calendarLinear','surfaceCoverage'])assert.equal(d[key],p.originals[key],key);
  }
  for(const b of p.blends){
    assert.equal(b.sameViews,true);
    for(const key of ['rgba','calendarRgba'])assert.equal(b[key],p.originals[key],key);
  }
  assert.deepEqual(p.writes.map(w=>w.hash),[p.originals.rgba,p.originals.calendarRgba]);
  for(const w of p.writes){assert.equal(w.current,true);assert.equal(w.identity,p.originalIdentity);assert.equal(w.profile,p.originalProfile);}
  for(const row of r.invalidPayloads){assert.equal(row.records,0,row.name);assert.equal(row.reuses,0,row.name);}
});

test('R2FA2-Q3: revoked worker replies cannot revive authority and a failed re-adoption is contained', () => {
  const r = report();
  assert.equal(r.lateReply.currentWhileHidden, false);
  assert.equal(r.lateReply.rejectedDelta, 1);
  assert.equal(r.lateReply.reusesAfterReturn, 1);
  assert.equal(r.adoptionFailure.threw, false);
  assert.equal(r.adoptionFailure.current, false);
  assert.equal(r.adoptionFailure.reuses, 0);
  assert.match(r.adoptionFailure.errors.join(' '), /quarantine adoption failure/);
});

test('R2FA2-Q4: transformation rejects an unrecognized or twice-transformed runtime', () => {
  assert.throws(() => quarantineCandidate(''), /unique|anchor/);
});

test('R2FA2-Q8: diagnostic reads during a hidden reversal affect neither work nor bytes and require no layout', () => {
  const r=report(),{none,...withReads}=r.diagnosticRoundTrips;
  assert.equal(none.current,true);assert.equal(none.reuses,1);
  assert.equal(none.initialRenders,1);assert.equal(none.workerRenders,1);
  assert.equal(none.finalDigest,none.originalDigest);
  for(const [name,row] of Object.entries(withReads)){
    assert.equal(row.hiddenLayoutReads,0,name);
    assert.deepEqual(row,none,name);
  }
  const impure=r.controls.impureObservation;
  assert.ok(impure.hiddenLayoutReads>0);assert.equal(impure.reuses,0);
  assert.equal(impure.initialRenders,2);assert.equal(impure.workerRenders,2);
  assert.notEqual(impure.finalDigest,none.originalDigest);
});
