"""Bind the exact bounded extension handoff; no product/browser execution."""
from pathlib import Path
import datetime
import difflib
import hashlib
import json

base = Path('/workspace/scratch/15b8fb6ac4c2')
work = base / 'r000b-work'
evidence = base / 'evidence/native-healthy-refresh-extension'
prior = base / 'evidence/native-harness-v2'
report = base / 'reviews/native-healthy-refresh-extension.md'
expected = {
    'tools/qa/run_r000b_withdrawal.py': '9c4931b82f39f559f0e876943c1d0bb1bd0e2c43a25e9501d8fe661aba76420e',
    'tests/weather-no-timetable-native-oracles.test.py': '36b1d515b8e101365065695ab3a92540f58e73ae60c0ecc450df5410332f0209',
    'tests/rlgwo/r000b-no-timetable-fixture.html': '5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c',
}

def record(path):
    data = path.read_bytes()
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

for relative, digest in expected.items():
    assert record(work / relative)['sha256'] == digest, 'Frozen extension drift: ' + relative
old = json.loads((prior / 'manifest.json').read_text())
for relative, digest in old['files'].items():
    assert record(prior / relative)['sha256'] == digest, 'Archived v2 drift: ' + relative
assert record(evidence / 'prepared-driver.py') == record(work / 'tools/qa/run_r000b_withdrawal.py')
assert record(evidence / 'prepared-tests.py') == record(work / 'tests/weather-no-timetable-native-oracles.test.py')
assert 'Report state: FINAL' in report.read_text()
test_log = (evidence / 'native-oracles-final.log').read_text()
assert 'Ran 35 tests' in test_log and test_log.rstrip().endswith('OK')
preservation = json.loads((evidence / 'static-preservation-final.log').read_text())
assert preservation['unchangedAcceptedV2Functions'] == 23 and preservation['unchangedAcceptedV2TestClasses'] == 4
assert preservation['original30SecondWatchPreserved'] and preservation['fixture240SecondCapPreserved']
assert not (evidence / 'diff-check-final.log').read_bytes()
assert not (evidence / 'progress-expression-syntax.log').read_bytes()
for relative, name in [('tools/qa/run_r000b_withdrawal.py', 'driver-v2-delta.patch'),
                       ('tests/weather-no-timetable-native-oracles.test.py', 'tests-v2-delta.patch')]:
    delta = difflib.unified_diff((prior / relative).read_text().splitlines(True),
        (work / relative).read_text().splitlines(True), fromfile='accepted-v2/' + relative, tofile='extension/' + relative)
    (evidence / name).write_text(''.join(delta))
freeze = {
    'schema': 'r000b-healthy-refresh-extension-freeze/v1',
    'status': 'FROZEN_PENDING_INDEPENDENT_DELTA_REVIEW',
    'observedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'harness': {relative: record(work / relative) for relative in expected},
    'acceptedV2Manifest': {'path': str(prior / 'manifest.json'), **record(prior / 'manifest.json')},
    'report': {'path': str(report), **record(report)},
    'verification': {'pureTests': 35, 'testExit': 0, 'unchangedV2TopLevelFunctionsExcludingMain': 23,
        'unchangedV2TestClasses': 4, 'original30SecondWatchPreserved': True, 'fixture240SecondCapPreserved': True,
        'mutationWindowExits': [0, 0], 'progressExpressionSyntaxExit': 0, 'scopedDiffCheckExit': 0},
    'intervalChoice': 'Keep recovered pre-capture across the original watch and extra wait; require exact A/B identities throughout retained samples and reject a third record. Conservative failure possible.',
    'limitations': ['No forced capture-before-render ordering; deterministic source test supplies that race',
        'Passive samples have no raster bytes; every retained full snapshot checks actual alpha and the original clip remains required',
        'Handled Moon worker diagnostic errors remain uninspected under accepted HN1 boundary'],
    'nativeRun': False, 'productBodiesExecuted': False, 'browserOrListenerAcquired': False,
    'productSourceOrGeneratedWrites': False, 'runningProcessOwnedByThisLane': False,
}
(evidence / 'final-freeze.json').write_text(json.dumps(freeze, indent=2) + '\n')
index = {'schema': 'r000b-healthy-refresh-extension-evidence/v1', 'status': freeze['status'],
         'report': freeze['report'], 'harness': freeze['harness'],
         'artifacts': {path.name: record(path) for path in sorted(evidence.iterdir())
                       if path.is_file() and path.name != 'evidence-index.json'}}
(evidence / 'evidence-index.json').write_text(json.dumps(index, indent=2) + '\n')
print(json.dumps({'report': freeze['report'], 'finalFreeze': record(evidence / 'final-freeze.json'),
                  'evidenceIndex': record(evidence / 'evidence-index.json'), 'harness': freeze['harness']}, indent=2))
