"""Bounded static/pure extension verification; never imports the native driver."""
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
evidence = base / 'evidence/native-healthy-refresh-extension'
v2 = base / 'evidence/native-harness-v2'
manifest = json.loads((v2 / 'manifest.json').read_text())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

for relative, expected in manifest['files'].items():
    assert digest(v2 / relative) == expected, 'Archived v2 drift: ' + relative
fixture = work / 'tests/rlgwo/r000b-no-timetable-fixture.html'
assert digest(fixture) == manifest['files']['tests/rlgwo/r000b-no-timetable-fixture.html']
driver = evidence / 'prepared-driver.py' if args.prepared else work / 'tools/qa/run_r000b_withdrawal.py'
tests = evidence / 'prepared-tests.py' if args.prepared else work / 'tests/weather-no-timetable-native-oracles.test.py'
old_driver = (v2 / 'tools/qa/run_r000b_withdrawal.py').read_text()
new_driver = driver.read_text()
old_ast, new_ast = ast.parse(old_driver), ast.parse(new_driver)
old_functions = {node.name: node for node in old_ast.body if isinstance(node, ast.FunctionDef)}
new_functions = {node.name: node for node in new_ast.body if isinstance(node, ast.FunctionDef)}
for name, node in old_functions.items():
    if name != 'main':
        assert ast.dump(node) == ast.dump(new_functions[name]), 'Accepted v2 predicate changed: ' + name
old_tests = ast.parse((v2 / 'tests/weather-no-timetable-native-oracles.test.py').read_text())
new_tests = ast.parse(tests.read_text())
old_classes = {node.name: node for node in old_tests.body if isinstance(node, ast.ClassDef)}
new_classes = {node.name: node for node in new_tests.body if isinstance(node, ast.ClassDef)}
for name, node in old_classes.items():
    assert ast.dump(node) == ast.dump(new_classes[name]), 'Accepted v2 test class changed: ' + name
watch_start = "            watch = {'stage': 'recovered'"
watch_end = '\n        fixture = page.evaluate(FIXTURE)'
old_watch = old_driver[old_driver.index(watch_start):old_driver.index(watch_end)]
assert old_watch in new_driver, 'Original uninterrupted30-second watch changed'
assert new_driver.count('page.wait_for_timeout(30000)') == 1
for name in ('READ', 'FIXTURE', 'LATEST', 'EXPECTED_COVERAGE', 'INITIAL_SOURCE_UTC'):
    def assigned(tree):
        return next(node.value for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))
    assert ast.dump(assigned(old_ast)) == ast.dump(assigned(new_ast)), 'Accepted constant changed: ' + name
assert "'fixtureMaxElapsedMs': refresh_progress['maxElapsedMs'], 'captureDeadlineElapsedMs': 235000," in new_driver
assert "refresh_progress['maxElapsedMs'] != 240000" in new_driver
for path in (driver, tests):
    assert all(line == line.rstrip() for line in path.read_text().splitlines()), 'Trailing whitespace: ' + str(path)
print(json.dumps({'mode': 'prepared' if args.prepared else 'repository', 'driverSha256': digest(driver),
    'testsSha256': digest(tests), 'unchangedFixtureSha256': digest(fixture),
    'unchangedAcceptedV2Functions': len(old_functions) - 1, 'unchangedAcceptedV2TestClasses': len(old_classes),
    'original30SecondWatchPreserved': True, 'fixture240SecondCapPreserved': True}, indent=2), flush=True)

if not args.static_only:
    source = tests.read_text()
    if args.prepared:
        old = "DRIVER = ROOT / 'tools/qa/run_r000b_withdrawal.py'"
        assert source.count(old) == 1
        source = source.replace(old, 'DRIVER = Path(' + repr(str(driver)) + ')')
    module = types.ModuleType('r000b_native_extension_controls')
    module.__file__ = str(work / 'tests/weather-no-timetable-native-oracles.test.py')
    sys.modules[module.__name__] = module
    exec(compile(source, str(tests), 'exec'), module.__dict__)
    outcome = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
