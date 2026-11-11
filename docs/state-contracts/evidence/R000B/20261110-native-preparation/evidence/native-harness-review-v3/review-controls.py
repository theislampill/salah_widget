"""Bounded independent v3 review: syntax/AST/diffs and pure oracle data only.
No driver import/main(), product execution, browser, listener, build, or network.
"""
from pathlib import Path
from copy import deepcopy
import ast
import difflib
import hashlib
import json
import re
import runpy
import subprocess
import sys

ROOT = Path('/workspace/scratch/15b8fb6ac4c2')
REPO = ROOT / 'r000b-work'
OLD = ROOT / 'evidence/native-harness-v2'
OUT = ROOT / 'evidence/native-harness-review-v3'
EXPECTED = {
    'tests/rlgwo/r000b-no-timetable-fixture.html': '5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c',
    'tools/qa/run_r000b_withdrawal.py': '9c4931b82f39f559f0e876943c1d0bb1bd0e2c43a25e9501d8fe661aba76420e',
    'tests/weather-no-timetable-native-oracles.test.py': '36b1d515b8e101365065695ab3a92540f58e73ae60c0ecc450df5410332f0209',
}
OLD_EXPECTED = {
    'tests/rlgwo/r000b-no-timetable-fixture.html': EXPECTED['tests/rlgwo/r000b-no-timetable-fixture.html'],
    'tools/qa/run_r000b_withdrawal.py': '73afb4d772e32bd21f2697777914f3db8d2d28c3833271ef669037b079fb28bc',
    'tests/weather-no-timetable-native-oracles.test.py': '3d60eec118064858d2294955a690a80d88dcb5021376e5362b5f2f6be44f0f82',
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

identities = []
for base, expected in [(REPO, EXPECTED), (OLD, OLD_EXPECTED)]:
    for rel, expected_sha in expected.items():
        data = (base / rel).read_bytes()
        actual = sha(data)
        identities.append({'path': str(base / rel), 'bytes': len(data), 'sha256': actual,
                           'expectedSha256': expected_sha, 'matches': actual == expected_sha})
assert all(row['matches'] for row in identities)
save('initial-identities.json', identities)

new_driver = (REPO / 'tools/qa/run_r000b_withdrawal.py').read_text()
old_driver = (OLD / 'tools/qa/run_r000b_withdrawal.py').read_text()
new_tests = (REPO / 'tests/weather-no-timetable-native-oracles.test.py').read_text()
old_tests = (OLD / 'tests/weather-no-timetable-native-oracles.test.py').read_text()
new_ast, old_ast = ast.parse(new_driver), ast.parse(old_driver)
new_test_ast, old_test_ast = ast.parse(new_tests), ast.parse(old_tests)
compile(new_ast, 'frozen-v3-driver', 'exec')
compile(new_test_ast, 'frozen-v3-tests', 'exec')

def declarations(parsed, kind):
    return {node.name: node for node in parsed.body if isinstance(node, kind)}

old_funcs, new_funcs = declarations(old_ast, ast.FunctionDef), declarations(new_ast, ast.FunctionDef)
unchanged_functions = []
for name, old in old_funcs.items():
    if name == 'main':
        continue
    new = new_funcs.get(name)
    unchanged_functions.append({'name': name, 'astIdentical': new is not None and ast.dump(old) == ast.dump(new),
        'sourceIdentical': new is not None and ast.get_source_segment(old_driver, old) == ast.get_source_segment(new_driver, new)})
old_classes, new_classes = declarations(old_test_ast, ast.ClassDef), declarations(new_test_ast, ast.ClassDef)
unchanged_classes = [{'name': name, 'astIdentical': name in new_classes and ast.dump(old) == ast.dump(new_classes[name]),
    'sourceIdentical': name in new_classes and ast.get_source_segment(old_tests, old) == ast.get_source_segment(new_tests, new_classes[name])}
    for name, old in old_classes.items()]
watch_start = "            watch = {'stage': 'recovered',"
old_watch = old_driver[old_driver.index(watch_start):old_driver.index('\n        fixture = page.evaluate(FIXTURE)')].rstrip()
new_watch = new_driver[new_driver.index(watch_start):new_driver.index('\n            # R000B_F01_REQUIRED_ORDINARY_HEALTHY_REFRESH_V1')].rstrip()
preservation = {
    'syntaxCompileOnly': True,
    'fixtureBytesIdentical': (REPO / 'tests/rlgwo/r000b-no-timetable-fixture.html').read_bytes() == (OLD / 'tests/rlgwo/r000b-no-timetable-fixture.html').read_bytes(),
    'oldTopLevelFunctionsOutsideMain': unchanged_functions,
    'oldTestClasses': unchanged_classes,
    'newTopLevelFunctionNames': sorted(set(new_funcs) - set(old_funcs)),
    'newTestClassNames': sorted(set(new_classes) - set(old_classes)),
    'originalRecoveredWatchSourceIdentical': old_watch == new_watch,
    'originalRecoveredWatchSha256': sha(old_watch.encode()),
}
assert preservation['fixtureBytesIdentical']
assert all(row['astIdentical'] and row['sourceIdentical'] for row in unchanged_functions + unchanged_classes)
assert old_watch == new_watch
save('preservation.json', preservation)
for name, before, after in [('driver-v2-v3.diff', old_driver, new_driver), ('tests-v2-v3.diff', old_tests, new_tests)]:
    (OUT / name).write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='frozen-v2', tofile='frozen-v3')))

command = [sys.executable, '-B', str(REPO / 'tests/weather-no-timetable-native-oracles.test.py'), 'HealthyRefreshTests', '-v']
completed = subprocess.run(command, cwd=REPO, capture_output=True, text=True, check=False)
log = completed.stdout + completed.stderr
(OUT / 'focused-oracle-suite.log').write_text(log)
matched = re.search(r'Ran (\d+) tests?', log)
suite = {'command': command, 'exitCode': completed.returncode,
         'testsReported': int(matched.group(1)) if matched else None, 'log': 'focused-oracle-suite.log'}
save('focused-oracle-suite.json', suite)
assert completed.returncode == 0 and suite['testsReported'] == 15

# Loading this reviewed test module only defines helpers and AST-extracted actual
# driver pure functions. Its unittest.main() guard is not entered.
ns = runpy.run_path(str(REPO / 'tests/weather-no-timetable-native-oracles.test.py'), run_name='independent_review_data')
oracle, make_case, verdict = ns['ORACLE'], ns['healthy_refresh_case'], ns['refresh_verdict']
probes = []

def record(name, observed, expected, detail):
    probes.append({'id': name, 'observed': observed, 'expectedFrozenBehavior': expected,
                   'reproduced': observed == expected, 'detail': detail})
    assert observed == expected, name

base = make_case()
record('P0-factory-positive', verdict(base)['ok'], True,
       {'scope': 'Invented existing factory, compact targets and epoch deadlines; positive control only, not a production-shaped success.'})

rich_fields = {'intent': 'fixed-site', 'source': 'hash', 'accuracyM': None,
               'acquiredAt': None, 'provider': None, 'area': None, 'bounds': None}
rich_case = make_case()
for frame in rich_case['full']:
    frame['target'].update(rich_fields)
    frame['raw']['target'].update(rich_fields)
left = oracle.healthy_refresh_record(rich_case['before'])
rich_verdict = verdict(rich_case)
record('P1-HR1-production-target-shapes', {'recordSelected': left is not None, 'pairOk': rich_verdict['pair']['ok'], 'verdictOk': rich_verdict['ok']},
       {'recordSelected': False, 'pairOk': False, 'verdictOk': False},
       {'expectedForHealthyActualInterfaces': 'The same owned generation/lat/lon identity should be accepted despite richer provenance metadata.',
        'snapshotTarget': rich_case['before']['target'], 'rawTarget': rich_case['before']['raw']['target'],
        'receiptTarget': rich_case['before']['actualCloud']['publication']['target'],
        'reason': rich_verdict['pair']['reason'], 'defect': 'HR1'})
record('P2-HR1-full-sample-repeat', oracle._healthy_refresh_sample(rich_case['full'][1], [rich_case['old'], rich_case['new']], full=True), False,
       {'expectedForHealthyActualInterfaces': True, 'defect': 'HR1',
        'scope': 'Actual full-sample predicate tested independently of record selection; no predicate repair or mock.'})

mono_case = make_case()
fixture_started = 125.25
for request in mono_case['ledger']:
    request['nativeOwner']['deadlineAt'] = fixture_started + request['elapsedMs'] + 10000
mono_record = oracle.healthy_refresh_record(mono_case['after'])
actual_match = oracle._healthy_refresh_request(mono_record, mono_case['after'], mono_case['ledger'])
request = mono_case['ledger'][-1]
body_rt = fixture_started + request['jsonElapsedMs']
receipt_rt = fixture_started + mono_record['retrievedAt'] - ns['REFRESH_START_UTC']
mono_result = verdict(mono_case)
record('P3-HR2-monotonic-native-deadline', {'recordSelected': mono_record is not None, 'requestMatched': actual_match is not None,
        'pairOk': mono_result['pair']['ok'], 'verdictOk': mono_result['ok']},
       {'recordSelected': True, 'requestMatched': False, 'pairOk': False, 'verdictOk': False},
       {'expectedForHealthyActualInterfaces': 'Consumed owned response and retrieval both precede native monotonic deadline; matching should succeed.',
        'fixtureStarted': fixture_started, 'requestElapsedMs': request['elapsedMs'], 'jsonElapsedMs': request['jsonElapsedMs'],
        'nativeDeadlineAt': request['nativeOwner']['deadlineAt'], 'bodySettledRt': body_rt,
        'derivedReceiptRtForControlOnly': receipt_rt, 'receiptEpoch': mono_record['retrievedAt'],
        'bodyAndReceiptBeforeDeadline': body_rt < request['nativeOwner']['deadlineAt'] and receipt_rt < request['nativeOwner']['deadlineAt'],
        'reason': mono_result['pair']['reason'], 'defect': 'HR2',
        'scope': 'Compact targets retained solely to isolate HR2. The finite native origin is invented data of the actual interface shape; no product executed.'})
assert body_rt < request['nativeOwner']['deadlineAt'] and receipt_rt < request['nativeOwner']['deadlineAt']

both_case = make_case()
for frame in both_case['full']:
    frame['target'].update(rich_fields); frame['raw']['target'].update(rich_fields)
for request in both_case['ledger']:
    request['nativeOwner']['deadlineAt'] = fixture_started + request['elapsedMs'] + 10000
both_result = verdict(both_case)
record('P4-both-production-interfaces', both_result['ok'], False,
       {'expectedForHealthyActualInterfaces': True, 'reason': both_result['pair']['reason'],
        'scope': 'HR1 prevents selection before HR2 can match requests. P1/P3 isolate each independently.'})

ambiguous = make_case()
ambiguous['ledger'].append(deepcopy(ambiguous['ledger'][-1]))
record('P5-duplicate-response-ambiguity', verdict(ambiguous)['ok'], False,
       {'scope': 'Held-out negative; duplicate equally matching owner/body rows must not prove one ordinary response.'})

third = make_case()
extra = deepcopy(third['old'])
extra['revision'] += 100
extra['sourceValidAt'] += 1
extra['retrievedAt'] += 1
third['passive'].append(third['passiveFrame'](150500, extra))
third_result = verdict(third)
record('P6-third-consumed-record-conservatively-rejected', {'pairOk': third_result['pair']['ok'], 'verdictOk': third_result['ok']},
       {'pairOk': True, 'verdictOk': False}, {'scope': 'Accepted stricter interval: a third receipt within retained observations cannot disappear behind healthy A/B endpoints.'})

record('P7-projected-target-identity-mismatch', None, None,
       {'scope': 'The six exact-coordinate/generation mutations below all reject the isolated current factory; replacement shape adapter must preserve these negatives.'})
identity_controls = []
for location in ['target', 'raw']:
    for field, delta in [('generation', 1), ('lat', 1), ('lon', 1)]:
        changed = make_case()
        target = changed['before']['target'] if location == 'target' else changed['before']['raw']['target']
        target[field] += delta
        ok = verdict(changed)['ok']
        assert ok is False
        identity_controls.append({'location': location, 'field': field, 'verdictOk': ok})
probes[-1]['detail']['negativeControls'] = identity_controls
save('independent-counterexamples.json', {'driverSha256': EXPECTED['tools/qa/run_r000b_withdrawal.py'],
     'fixtureSha256': EXPECTED['tests/rlgwo/r000b-no-timetable-fixture.html'],
     'sourceInterfaceSha256': sha((REPO / 'src/native/index.html').read_bytes()),
     'probes': probes, 'allExpectedFrozenBehaviorsReproduced': all(probe['reproduced'] for probe in probes),
     'limit': 'Pure synthetic observations through actual frozen predicates; neither product execution nor native evidence. Passing tests do not rebut HR1/HR2.'})
print(json.dumps({'focusedTests': suite['testsReported'], 'oldFunctionsPreserved': len(unchanged_functions),
                  'oldTestClassesPreserved': len(unchanged_classes), 'originalWatchPreserved': old_watch == new_watch,
                  'probes': len(probes), 'allProbeBehaviorsReproduced': all(probe['reproduced'] for probe in probes)}))
