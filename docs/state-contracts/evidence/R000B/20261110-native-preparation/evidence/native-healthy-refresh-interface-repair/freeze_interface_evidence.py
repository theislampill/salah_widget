"""Freeze the bounded HR1/HR2 handoff; no product/native execution."""
from pathlib import Path
import datetime
import difflib
import hashlib
import json

base = Path('/workspace/scratch/15b8fb6ac4c2')
work = base / 'r000b-work'
evidence = base / 'evidence/native-healthy-refresh-interface-repair'
prior = base / 'evidence/native-harness-v3'
report = base / 'reviews/native-healthy-refresh-interface-repair.md'
expected = {
    'tools/qa/run_r000b_withdrawal.py': '1eeb84e2800231ef74349af2152be5b85df807232403199afa3566e804edfb2c',
    'tests/weather-no-timetable-native-oracles.test.py': '25ee18492a84ca4646d7695b26d81799afe56ba059ddfed3901707f3351af3d4',
    'tests/rlgwo/r000b-no-timetable-fixture.html': '5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c',
}

def record(path):
    data = path.read_bytes()
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

for name, digest in expected.items():
    assert record(work / name)['sha256'] == digest, 'Frozen repair drift: ' + name
for name, digest in json.loads((prior / 'manifest.json').read_text())['files'].items():
    assert record(prior / name)['sha256'] == digest, 'Preserved v3 drift: ' + name
protected = json.loads((evidence / 'protected-inputs.json').read_text())
for name, digest in protected.items():
    assert record(work / name)['sha256'] == digest, 'Protected input drift: ' + name
assert record(evidence / 'prepared-driver.py') == record(work / 'tools/qa/run_r000b_withdrawal.py')
assert record(evidence / 'prepared-tests.py') == record(work / 'tests/weather-no-timetable-native-oracles.test.py')
assert 'Report state: FINAL' in report.read_text()
suite = (evidence / 'native-oracles-final.log').read_text()
assert 'Ran 47 tests' in suite and suite.rstrip().endswith('OK')
preservation = json.loads((evidence / 'static-preservation-final.log').read_text())
assert preservation['unchangedHNFunctions'] == 23 and preservation['unchangedHNTestClasses'] == 4
assert preservation['priorExtensionTestsPreservedWithClockAdapters'] == 15
assert preservation['originalWatchPreserved'] and preservation['protectedInputsUnchanged']
assert not (evidence / 'diff-check-final.log').read_bytes()
assert not (evidence / 'progress-syntax-final.log').read_bytes()
old = json.loads((evidence / 'old-v3-discriminators.json').read_text())
new = json.loads((evidence / 'repair-discriminators-repository.json').read_text())
assert old['oldApiInvocationCompletedWithoutTypeError'] and new['oldFailureUsedOriginalV3SignaturesWithoutTypeError']
assert not old['HR1']['recordSelected'] and not old['HR1']['fullSampleHealthy'] and not old['HR2']['requestMatched']
assert new['newRichRecordSelected'] and new['newRichFullSampleHealthy'] and new['newMonotonicRequestMatched'] and new['newFullProductionShapedVerdict']
review = base / 'reviews/native-harness-review-v3.md'
assert record(review)['sha256'] == '000756008c67be0595ec914a7ded40a1934d7f08b2e3a6a1e1964d64ffa53dce'
for name, filename in [('tools/qa/run_r000b_withdrawal.py', 'driver-v3-repair.delta'),
                       ('tests/weather-no-timetable-native-oracles.test.py', 'tests-v3-repair.delta')]:
    difference = difflib.unified_diff((prior / name).read_text().splitlines(True),
        (work / name).read_text().splitlines(True), fromfile='frozen-v3/' + name, tofile='hr-interface-repair/' + name)
    (evidence / filename).write_text(''.join(difference))
freeze = {
    'schema':'r000b-hr-interface-repair-freeze/v1',
    'status':'FROZEN_PENDING_INDEPENDENT_HR1_HR2_CLOSURE_REVIEW',
    'observedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'harness':{name:record(work / name) for name in expected},
    'report':{'path':str(report), **record(report)},
    'originalIndependentReview':{'path':str(review), **record(review)},
    'protectedInputsUnchanged':protected,
    'verification':{'tests':47,'testExit':0,'unchangedHNFunctions':23,'unchangedHNTestClasses':4,
        'priorMeaningfulExtensionTestsWithCorrectedInterfaces':15,'newInterfaceTests':12,
        'oldFailureUsedOriginalSignaturesWithoutTypeError':True,'correctedActualPredicatesAcceptSameRealisticCase':True,
        'mutationWindowExits':[0,0],'progressSyntaxExit':0,'scopedDiffCheckExit':0},
    'clockConservatism':'Observed integer receipt maps to a one-millisecond native interval; its upper edge must be strictly before deadline, so a valid final-millisecond receipt can be refused.',
    'containedPureSourceExpressionsExecuted':['wxNumber','captureWeatherTarget','_RAFNOW','receipt-target projection','attempt-deadline expression'],
    'productProducersCalled':False,'fullProductRuntimeExecuted':False,'nativeBrowserOrListenerAcquired':False,
    'productSourceOrGeneratedWrites':False,'refOrRemoteEffects':False,'runningProcessOwnedByThisLane':False,
    'nativeAcceptanceOrClosureGranted':False,
}
(evidence / 'final-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
index = {'schema':'r000b-hr-interface-repair-evidence/v1','status':freeze['status'],
    'report':freeze['report'],'harness':freeze['harness'],
    'artifacts':{path.name:record(path) for path in sorted(evidence.iterdir()) if path.is_file() and path.name != 'evidence-index.json'}}
(evidence / 'evidence-index.json').write_text(json.dumps(index,indent=2)+'\n')
print(json.dumps({'report':freeze['report'],'finalFreeze':record(evidence / 'final-freeze.json'),
                  'evidenceIndex':record(evidence / 'evidence-index.json'),'harness':freeze['harness']},indent=2))
