'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {prayerOnlyCandidate, prayerExperiment, publicationExperiment, retentionExperiment,prepareCandidates} = require('../tools/qa/r002f_a2_architecture.cjs');
const repo = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(repo, 'index.html'), 'utf8');

test('R2FA2-A1: bounded prayer experiment refreshes every fixture without rerunning ordinary weather/theme stages', async () => {
  const receipt = await prayerExperiment(source, 1);
  assert.equal(receipt.baseline.summary.taskEndDifferent, 6);
  assert.equal(receipt.candidate.summary.taskEndDifferent, 0);
  assert.equal(receipt.candidate.summary.firstCallbackDifferent, 0);
  for (const row of receipt.details) {
    assert.equal(row.optionalCallsDuringReturn, 0, row.scenario);
    assert.equal(row.requestCountMatchesBaselineCallback, true, row.scenario);
    assert.equal(row.timerCountMatchesBaselineCallback, true, row.scenario);
    assert.equal(row.requestUrlsMatchBaselineCallback, true, row.scenario);
    assert.equal(row.pendingCallbacks, 1, row.scenario);
    assert.equal(row.moonSawCurrentPrayer, true, row.scenario);
    assert.equal(row.fullRenderReceiptCleared, true, row.scenario);
    assert.equal(row.repeatedVisibleChangedPrayer, false, row.scenario);
    assert.equal(row.repeatedVisibleAddedRequest, false, row.scenario);
    assert.equal(row.repeatedVisibleAddedTimer, false, row.scenario);
  }
});

test('R2FA2-A6: removing the restoring call is detected independently of the retained shared publisher', async () => {
  const {runMatrix}=require('../tools/qa/r002f_a2_resume.cjs');
  const candidate=prayerOnlyCandidate(source);
  const mutant=candidate.replace('runRenderStage("resume-prayer",publishRestoredPrayerResearch); ','');
  assert.notEqual(mutant,candidate);
  const report=await runMatrix({source:mutant,repeats:1});
  assert.equal(report.summary.taskEndDifferent,6);
  assert.equal(report.summary.firstCallbackDifferent,0);
});

test('R2FA2-A7: patches bind every authored preimage and cannot overwrite an existing directory', t => {
  const crypto=require('node:crypto'),os=require('node:os');
  const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'r002f-prepare-'));
  t.after(()=>fs.rmSync(temporary,{recursive:true,force:true}));
  const output=path.join(temporary,'new'),manifest=prepareCandidates(output);
  assert.equal(manifest.changes.length,3);
  for(const entry of manifest.changes){
    assert.equal(entry.preimageSha256,crypto.createHash('sha256').update(fs.readFileSync(path.join(repo,entry.path))).digest('hex'));
    const patch=path.join(output,entry.patch),target=path.join(temporary,entry.path);
    fs.mkdirSync(path.dirname(target),{recursive:true});
    fs.copyFileSync(path.join(repo,entry.path),target);
    assert.equal(crypto.createHash('sha256').update(fs.readFileSync(patch)).digest('hex'),entry.patchSha256);
    require('node:child_process').execFileSync('git',['apply',patch],{cwd:temporary});
    assert.equal(crypto.createHash('sha256').update(fs.readFileSync(target)).digest('hex'),entry.candidateSha256);
  }
  assert.throws(()=>prepareCandidates(output),/EEXIST/);
});

test('R2FA2-A2: shared publisher retains full rows, progress, arc, truthful withdrawal and fault containment', async () => {
  const receipt = await prayerExperiment(source, 1);
  for(const row of receipt.details) {
    assert.deepEqual(row.baselineCallbackGroupDifferences,[],row.scenario);
    assert.deepEqual(row.groupDifferences,[],row.scenario);
    assert.equal(row.restoreEntries,1,row.scenario);
    assert.equal(row.publisherEntries,1,row.scenario);
    assert.equal(row.repeatRestoreEntries,0,row.scenario);
    assert.equal(row.repeatPublisherEntries,0,row.scenario);
  }
  assert.deepEqual(receipt.repeatedPublicationControl,{publisherEntries:1,groupChanged:false});
  assert.deepEqual(receipt.groupCorruptionDifferences,['rows','progressWidth','arcSha256','markers']);
  assert.deepEqual(receipt.prayerFault.groupDifferences,[]);
  assert.equal(receipt.prayerFault.gregorian,'Gregorian date unavailable');
  assert.equal(receipt.prayerFault.hijri,'Hijri date unavailable');
  assert.equal(receipt.prayerFault.current, '—');
  assert.equal(receipt.prayerFault.next, '—');
  assert.equal(receipt.prayerFault.countdown, 'Prayer times unavailable');
  assert.equal(receipt.prayerFault.faults, 1);
  assert.equal(receipt.prayerFault.pendingCallbacks, 1);
  assert.equal(receipt.prayerFault.optionalCallsDuringReturn, 0);
});

test('R2FA2-A3: preparation fails closed on missing or ambiguous authored owners', () => {
  for (const wrong of ['', source + source, source.replace('  let M=null, prayerPublished=false, modelDone=false;', '  let M=null;')]) {
    assert.throws(() => prayerOnlyCandidate(wrong), /unique|owner|anchor/);
  }
  const candidate = prayerOnlyCandidate(source);
  assert.throws(() => prayerOnlyCandidate(candidate), /unique|owner|anchor|already/);
  assert.equal((candidate.match(/M=model\(\); modelDone=true;/g) || []).length, 1);
});

test('R2FA2-A4: preview experiment distinguishes currentness, preparation, upload and cross-owner publication', async () => {
  const r = await publicationExperiment();
  assert.equal(r.currentness.unchanged, true);
  for (const key of ['authorityLost','visibilityChanged','temperatureChanged','generationChanged','expired']) assert.equal(r.currentness[key], false, key);
  assert.equal(r.currentness.sameInputsRenewed, true);
  assert.equal(r.currentness.cloudOnlyChanged, true);
  assert.equal(r.baselineUpload.failedWriteChangedVisibleBytes, true);
  assert.equal(r.singleUpload.failedWriteChangedVisibleBytes, false);
  assert.equal(r.singleUpload.successMatchesBaseline, true);
  assert.equal(r.singleUpload.partialForegroundMatchesBaseline, true);
  assert.equal(r.singleUpload.omittedForegroundMutantDetected, true);
  assert.equal(r.singleUpload.visibleUploadsPerNewBackground, 1);
  const {full,partial,controls,expiry}=r.singleUpload;
  assert.equal(r.singleUpload.retainedOldIdentity,true);
  assert.equal(r.singleUpload.retainedFlag,true);
  assert.equal(full.matches,true);
  assert.equal(partial.matches,true);
  assert.deepEqual(partial.belowRegion,[106,150,46,255]);
  assert.deepEqual(partial.finalPixel,[25,84,19,255]);
  assert.equal(partial.tailChanged,true);
  assert.equal(partial.regionalRows,64);
  assert.equal(partial.regionalTailPreserved,true);
  for(const key of ['omittedForeground','misplacedRegion'])assert.equal(controls[key].headMatches,false,key);
  for(const key of ['fabricatedBlack','previousTail'])assert.equal(controls[key].tailMatches,false,key);
  assert.equal(expiry.misses[0].ageMs,36600);
  assert.equal(expiry.retries,1);
  assert.equal(expiry.ready,true);
  assert.equal(expiry.allWritesCurrent,true);
  assert.deepEqual(expiry.writes,[{utcMs:37200,jobUtc:36600,rows:530}]);
  assert.equal(controls.latePreparation.allWritesCurrent,false);
  assert.equal(r.crossOwnerTransactionProven, false);
});

test('R2FA2-A5: quarantined Moon data is considered only under the source admission predicates', async () => {
  const r = await retentionExperiment();
  assert.equal(r.rows.find(x => x.name === 'continuous-short-hide').reusable, true);
  for (const row of r.rows.filter(x => !['continuous-short-hide','same-scope-altitude-change'].includes(x.name))) assert.equal(row.reusable, false, row.name);
  assert.equal(r.rows.find(x => x.name === 'same-scope-altitude-change').reusable, true);
  assert.equal(r.existingRecordAfterHideMatches, false);
  assert.equal(r.presentationRetained, false);
  assert.equal(r.productionMutation, false);
});

test('R2FA2-A8: actual lunar join reveals mixed preview publication at upload failure and cloud revocation',async()=>{
  const {crossOwnerExperiment}=require('../tools/qa/r002f_a2_architecture.cjs');
  const r=await crossOwnerExperiment(),last=arm=>arm.events.at(-1);
  const initial=r.singleUploadSuccess.events.find(e=>e.event==='initial-settled'),next=last(r.singleUploadSuccess);
  assert.notEqual(initial.detailBytes,next.detailBytes);
  assert.notEqual(initial.backgroundBytes,next.backgroundBytes);
  assert.notEqual(initial.mask,next.mask);
  assert.equal(next.detailOwner,'atmospheric-preview');assert.equal(next.detailRenders,2);
  assert.equal(next.previewReceiptUtc,21000);
  for(const key of ['detailBytes','backgroundBytes','previewReceiptUtc','mask'])assert.equal(last(r.baselineSuccess)[key],next[key],key);
  for(const arm of [r.baselineFailure,r.singleUploadFailure]){
    const rejected=arm.events.find(e=>e.event==='background-rejected'),settled=last(arm);
    assert.equal(arm.reason,'controlled preview canvas rejection');assert.equal(arm.retries,0);
    assert.equal(arm.events.filter(e=>e.candidateUtc===21000&&e.event==='background-write').length,0);
    for(const row of [rejected,settled]){
      assert.equal(row.detailBytes,next.detailBytes);assert.equal(row.detailRenders,2);
      assert.equal(row.detailOwner,'atmospheric-preview');assert.equal(row.detailVisible,true);assert.equal(row.previewVisible,true);
      assert.equal(row.previewFrameUtc,0);assert.equal(row.previewReceiptUtc,0);
      assert.equal(row.backgroundBytes,initial.backgroundBytes);assert.equal(row.mask,initial.mask);
    }
    assert.equal(settled.retained,true);
  }
  for(const arm of [r.baselineRevocation,r.singleUploadRevocation]){
    assert.equal(arm.misses.length,1);assert.match(arm.misses[0].reason,/cloud authority superseded during detail composition/);
    assert.equal(arm.retries,1);
    const revoked=arm.events.find(e=>e.event==='cloud-authority-revoked'),settled=last(arm);
    assert.equal(revoked.authority,3);assert.equal(revoked.receiptAuthority,1);
    assert.equal(revoked.detailVisible,true);assert.equal(revoked.detailBytes,next.detailBytes);
    assert.equal(revoked.backgroundBytes,initial.backgroundBytes);
    assert.ok(arm.events.filter(e=>e.candidateUtc===21000&&e.event==='background-write').every(e=>e.authority===3));
    assert.equal(settled.detailRenders,3);assert.notEqual(settled.detailBytes,revoked.detailBytes);
    assert.notEqual(settled.backgroundBytes,next.backgroundBytes);assert.notEqual(settled.backgroundBytes,initial.backgroundBytes);
    assert.equal(settled.receiptAuthority,3);assert.equal(settled.frameAuthority,3);assert.equal(settled.previewReceiptUtc,21000);
    assert.equal(settled.retained,false);
  }
  const backgroundWrites=arm=>arm.events.filter(e=>e.candidateUtc===21000&&e.event==='background-write').length;
  assert.equal(backgroundWrites(r.baselineSuccess),2);assert.equal(backgroundWrites(r.singleUploadSuccess),1);
  assert.equal(backgroundWrites(r.baselineRevocation),2);assert.equal(backgroundWrites(r.singleUploadRevocation),1);
});
