"""Decisive old failures through the actual frozen v3 signatures, before edits."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import runpy

base = Path('/workspace/scratch/15b8fb6ac4c2')
work = base / 'r000b-work'
archive = base / 'evidence/native-harness-v3'
out = base / 'evidence/native-healthy-refresh-interface-repair'
manifest = json.loads((archive / 'manifest.json').read_text())
for relative, expected in manifest['files'].items():
    for root in (archive, work):
        assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == expected, str(root / relative)
interfaces = json.loads((out / 'source-interface-shapes.json').read_text())
loaded = runpy.run_path(str(archive / 'tests/weather-no-timetable-native-oracles.test.py'))
old, factory = loaded['ORACLE'], loaded['healthy_refresh_case']

def verdict(case):
    # Original six-argument API. No new origin argument or new helper is supplied.
    return old.healthy_refresh_evidence(case['before'], case['after'], case['passive'], case['full'], case['ledger'], case['mode'])

def rich_targets(case):
    for state in [case['before'], case['after'], *case['full'], *case['passive']]:
        if 'target' in state:
            state['target'] = deepcopy(interfaces['richTarget'])
        if 'raw' in state:
            state['raw']['target'] = deepcopy(interfaces['richTarget'])

def monotonic_clock(case):
    clock = interfaces['observedClock']
    for state in [case['before'], case['after'], *case['full'], *case['passive']]:
        for motion in [state.get('motion'), state.get('actualCloud', {}).get('motion')]:
            if motion is not None:
                motion['lastRt'] = clock['started'] + motion['elapsedRtMs']
    for request in case['ledger']:
        request['nativeOwner']['deadlineAt'] = clock['started'] + request['elapsedMs'] + interfaces['weatherAttemptBudgetMs']

positive = factory(); assert verdict(positive)['ok'] is True
hr1 = factory(); rich_targets(hr1)
hr1_record = old.healthy_refresh_record(hr1['before'])
hr1_sample = old._healthy_refresh_sample(hr1['before'], [hr1['old'], hr1['new']], full=True)
hr1_verdict = verdict(hr1)
assert hr1_record is None and hr1_sample is False and hr1_verdict['ok'] is False
hr2 = factory(); monotonic_clock(hr2)
hr2_record = old.healthy_refresh_record(hr2['after'])
assert hr2_record is not None
# Original three-argument API; a TypeError cannot masquerade as HR2 detection.
hr2_request = old._healthy_refresh_request(hr2_record, hr2['after'], hr2['ledger'])
hr2_pair = old.healthy_refresh_pair(hr2['before'], hr2['after'], hr2['ledger'])
assert hr2_request is None and hr2_pair['ok'] is False
request = hr2['ledger'][-1]
clock = interfaces['observedClock']
json_native = clock['started'] + request['jsonElapsedMs']
receipt_lower = clock['started'] + hr2_record['retrievedAt'] - clock['startUtc']
assert json_native < request['nativeOwner']['deadlineAt'] and receipt_lower + 1 < request['nativeOwner']['deadlineAt']
combined = factory(); rich_targets(combined); monotonic_clock(combined)
assert verdict(combined)['ok'] is False
record = {'schema':'r000b-hr1-hr2-frozen-v3-discriminators/v1',
    'frozenDriverSha256':manifest['files']['tools/qa/run_r000b_withdrawal.py'],
    'sourceInterfacesSha256':hashlib.sha256((out / 'source-interface-shapes.json').read_bytes()).hexdigest(),
    'oldApiInvocationCompletedWithoutTypeError':True,
    'inventedV3FactoryPositive':True,
    'HR1':{'richSnapshotTarget':hr1['before']['target'], 'compactReceiptTarget':hr1['before']['actualCloud']['publication']['target'],
           'recordSelected':hr1_record is not None, 'fullSampleHealthy':hr1_sample, 'verdict':hr1_verdict['ok']},
    'HR2':{'origin':clock,'compactTargetsUsedOnlyToIsolateClock':True,'recordSelected':True,
           'jsonCompletedPerformanceMs':json_native,'retrievalPerformanceInterval':[receipt_lower,receipt_lower+1],
           'deadlinePerformanceMs':request['nativeOwner']['deadlineAt'],'epochRetrievedAt':hr2_record['retrievedAt'],
           'requestMatched':hr2_request is not None,'pairQualified':hr2_pair['ok']},
    'combinedProductionShapedCaseQualified':False,
    'scope':'Pure predicate and isolated source-interface controls; no native/browser execution'}
(out / 'old-v3-discriminators.json').write_text(json.dumps(record,indent=2)+'\n')
(out / 'old-v3-realistic-case.json').write_text(json.dumps({key:value for key,value in combined.items() if not callable(value)},indent=2)+'\n')
review = base / 'evidence/native-harness-review-v3/independent-counterexamples.json'
(out / 'independent-v3-counterexamples-preserved.json').write_bytes(review.read_bytes())
print(json.dumps(record,indent=2))
