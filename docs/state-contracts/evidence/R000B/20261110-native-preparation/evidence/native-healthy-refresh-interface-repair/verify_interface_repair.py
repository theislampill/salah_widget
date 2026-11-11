"""Static preservation and pure actual-predicate checks; no driver import/main."""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import sys
import types
import unittest

parser = argparse.ArgumentParser()
parser.add_argument('--prepared', action='store_true')
parser.add_argument('--static-only', action='store_true')
args = parser.parse_args()
base = Path('/workspace/scratch/15b8fb6ac4c2')
work = base / 'r000b-work'
evidence = base / 'evidence/native-healthy-refresh-interface-repair'
v2, v3 = base / 'evidence/native-harness-v2', base / 'evidence/native-harness-v3'
mode = 'prepared' if args.prepared else 'repository'
driver = evidence / 'prepared-driver.py' if args.prepared else work / 'tools/qa/run_r000b_withdrawal.py'
tests = evidence / 'prepared-tests.py' if args.prepared else work / 'tests/weather-no-timetable-native-oracles.test.py'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for archive in (v2, v3):
    for name, expected in json.loads((archive / 'manifest.json').read_text())['files'].items():
        assert sha(archive / name) == expected, 'Archive drift: ' + str(archive / name)
assert sha(work / 'tests/rlgwo/r000b-no-timetable-fixture.html') == '5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c'
assert sha(work / 'src/native/index.html') == 'b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f'
protected_names = ['tests/rlgwo/r000b-no-timetable-fixture.html', 'src/native/index.html',
    'real-sky/native-host-hooks.js', 'real-sky/native-host.mjs', 'real-sky/native-preview-host.mjs', 'real-sky/native-composition.mjs',
    'index.html', 'offline.html', 'real-sky/native-sky.js', 'moon/BUILD.json']
protected = {name: sha(work / name) for name in protected_names}
protected_path = evidence / 'protected-inputs.json'
if protected_path.exists():
    assert json.loads(protected_path.read_text()) == protected, 'Protected product/generated/fixture drift'
else:
    assert args.prepared, 'Protected inputs must be recorded before repository mutation'
    protected_path.write_text(json.dumps(protected, indent=2) + '\n')

old_driver = (v2 / 'tools/qa/run_r000b_withdrawal.py').read_text()
new_driver = driver.read_text()
old_tree, new_tree = ast.parse(old_driver), ast.parse(new_driver)
old_functions = {node.name: node for node in old_tree.body if isinstance(node, ast.FunctionDef)}
new_functions = {node.name: node for node in new_tree.body if isinstance(node, ast.FunctionDef)}
for name, node in old_functions.items():
    if name != 'main':
        assert ast.dump(node) == ast.dump(new_functions[name]), 'Accepted HN function changed: ' + name
        assert ast.get_source_segment(old_driver, node) == ast.get_source_segment(new_driver, new_functions[name])
old_tests = (v2 / 'tests/weather-no-timetable-native-oracles.test.py').read_text()
new_tests = tests.read_text()
old_classes = {node.name: node for node in ast.parse(old_tests).body if isinstance(node, ast.ClassDef)}
new_classes = {node.name: node for node in ast.parse(new_tests).body if isinstance(node, ast.ClassDef)}
for name, node in old_classes.items():
    assert ast.dump(node) == ast.dump(new_classes[name]), 'Accepted HN test class changed: ' + name
    assert ast.get_source_segment(old_tests, node) == ast.get_source_segment(new_tests, new_classes[name])
v3_tests = (v3 / 'tests/weather-no-timetable-native-oracles.test.py').read_text()
v3_class = next(node for node in ast.parse(v3_tests).body if isinstance(node, ast.ClassDef) and node.name == 'HealthyRefreshTests')
adapted_class = ast.get_source_segment(new_tests, new_classes['HealthyRefreshTests'])
adapted_class = adapted_class.replace("ORACLE.healthy_refresh_pair(case['before'], case['after'], case['ledger'], case.get('clock'))",
                                      "ORACLE.healthy_refresh_pair(case['before'], case['after'], case['ledger'])")
adapted_class = adapted_class.replace("case['clock']['started'] + (case['new']['retrievedAt'] - case['clock']['startUtc'])",
                                      "case['new']['retrievedAt']")
assert ast.dump(ast.parse(adapted_class).body[0]) == ast.dump(v3_class), 'Prior extension assertions changed beyond approved clock adapters'
watch_start = "            watch = {'stage': 'recovered'"
watch_end = '\n        fixture = page.evaluate(FIXTURE)'
watch = old_driver[old_driver.index(watch_start):old_driver.index(watch_end)]
assert watch in new_driver and new_driver.count('page.wait_for_timeout(30000)') == 1
assert "refresh_progress['maxElapsedMs'] != 240000" in new_driver
assert "'captureDeadlineElapsedMs': 235000" in new_driver
for path in (driver, tests):
    assert all(line == line.rstrip() for line in path.read_text().splitlines())
progress = next(ast.literal_eval(node.value) for node in new_tree.body if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == 'HEALTHY_REFRESH_PROGRESS' for target in node.targets))
assert 'clockOrigin:{started:f.started,startUtc:f.startUtc}' in progress
(evidence / ('progress-expression-' + mode + '.js')).write_text('const readHealthyRefreshProgress = ' + progress + ';\n')

source = new_tests
if args.prepared:
    original = "DRIVER = ROOT / 'tools/qa/run_r000b_withdrawal.py'"
    assert source.count(original) == 1
    source = source.replace(original, 'DRIVER = Path(' + repr(str(driver)) + ')')
module = types.ModuleType('r000b_healthy_refresh_interface_controls')
module.__file__ = str(work / 'tests/weather-no-timetable-native-oracles.test.py')
sys.modules[module.__name__] = module
exec(compile(source, str(tests), 'exec'), module.__dict__)
interfaces = json.loads((evidence / 'source-interface-shapes.json').read_text())
factory = module.healthy_refresh_case()
assert factory['before']['target'] == interfaces['richTarget']
assert factory['before']['actualCloud']['publication']['target'] == interfaces['receiptTarget']
assert factory['clock'] == interfaces['observedClock']
assert factory['ledger'][-1]['nativeOwner']['deadlineAt'] == interfaces['monotonicDeadline']
old_case = json.loads((evidence / 'old-v3-realistic-case.json').read_text())
clock = interfaces['observedClock']
new_record = module.ORACLE.healthy_refresh_record(old_case['after'])
new_sample = module.ORACLE._healthy_refresh_sample(old_case['before'], [old_case['old'], old_case['new']], full=True)
new_request = module.ORACLE._healthy_refresh_request(new_record, old_case['after'], old_case['ledger'], clock)
new_verdict = module.ORACLE.healthy_refresh_evidence(old_case['before'], old_case['after'], old_case['passive'],
                                                   old_case['full'], old_case['ledger'], old_case['mode'], clock)
assert new_record is not None and new_sample is True and new_request is not None and new_verdict['ok'] is True
old_proof = json.loads((evidence / 'old-v3-discriminators.json').read_text())
assert old_proof['oldApiInvocationCompletedWithoutTypeError'] is True
assert old_proof['HR1']['recordSelected'] is False and old_proof['HR1']['fullSampleHealthy'] is False
assert old_proof['HR2']['recordSelected'] is True and old_proof['HR2']['requestMatched'] is False
proof = {'schema':'r000b-hr-interface-repair-discriminators/v1', 'mode':mode,
    'driverSha256':sha(driver), 'testsSha256':sha(tests), 'sourceInterfaceShapesSha256':sha(evidence / 'source-interface-shapes.json'),
    'oldV3DiscriminatorsSha256':sha(evidence / 'old-v3-discriminators.json'),
    'oldFailureUsedOriginalV3SignaturesWithoutTypeError':True,
    'newRichRecordSelected':new_record is not None, 'newRichFullSampleHealthy':new_sample,
    'newMonotonicRequestMatched':new_request is not None, 'newFullProductionShapedVerdict':new_verdict['ok'],
    'matchedRequest':new_request, 'scope':'Contained source-interface and pure predicate controls only; no native result'}
(evidence / ('repair-discriminators-' + mode + '.json')).write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'mode':mode,'driverSha256':sha(driver),'testsSha256':sha(tests),
    'unchangedFixtureSha256':protected['tests/rlgwo/r000b-no-timetable-fixture.html'],
    'unchangedHNFunctions':len(old_functions)-1,'unchangedHNTestClasses':len(old_classes),
    'priorExtensionTestsPreservedWithClockAdapters':15,'originalWatchPreserved':True,
    'newActualPredicatesAcceptPreservedProductionShapedCounterpart':True,
    'protectedInputsUnchanged':True},indent=2),flush=True)
if not args.static_only:
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    raise SystemExit(0 if result.wasSuccessful() else 1)
