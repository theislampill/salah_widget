"""Inspect the primary's retained partial native receipt, without browser replay."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).parent
prior_path = HERE / 'native-all-primary/results.json'
prior = json.loads(prior_path.read_text(encoding='utf-8-sig'))
fixture = HERE / 'r0023-current-native.html'
expected = ['15-builder-coarse-candidates', '15-builder-reverse-search', '15-builder-gps-manual']
assert prior['target'] == '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
assert prior['fixtureSha256'] == hashlib.sha256(fixture.read_bytes()).hexdigest()
valid = []
for name in expected:
    case = next(row for row in prior['cases'] if row['name'] == name)
    assert case['status'] == 'MACHINE_CHECKS_PASS_VISUAL_REVIEW_PENDING' and case['checks'] and all(row['passed'] for row in case['checks'])
    assert not case['pageErrors'] and not case['outsideRequests'] and not case['fixtureRecords']['errors']
    assert case['fixtureIdentity']['state'] == 'ready' and case['fixtureIdentity']['bodiesPreserved']
    picture = prior_path.parent / case['screenshot']
    assert picture.is_file()
    valid.append({'name': name, 'checks': case['checks'], 'fixtureIdentity': case['fixtureIdentity'], 'screenshot': str(picture), 'screenshotSha256': hashlib.sha256(picture.read_bytes()).hexdigest()})
failure = next(row for row in prior['cases'] if row['status'] == 'FAIL')
assert 'EvalError' in failure['error'] and 'unsafe-eval' in failure['error']
receipt = {'status': 'PARTIAL_PRIMARY_NATIVE_THREE_BUILDER_CASES_VERIFIED_REST_PENDING', 'target': prior['target'], 'runtime': prior['runtime'],
    'primaryReceipt': str(prior_path), 'primaryReceiptSha256': hashlib.sha256(prior_path.read_bytes()).hexdigest(),
    'browser': prior['browser'], 'passedCases': valid,
    'counterexample': {'name': failure['name'], 'classification': 'HARNESS_CSP_STRING_EVALUATION_FAILURE_NOT_PRODUCTION_DEFECT', 'exactError': failure['error']},
    'repair': {'scope': 'Harness only: bounded evaluate(function) polling; explicit exact-custody resume/subset; font settle/screenshot deadlines', 'cspUnchanged': True,
        'oldDriverSha256': prior['driverSha256'], 'newDriverSha256': hashlib.sha256((HERE / 'native-consumer-driver.py').read_bytes()).hexdigest(),
        'fixtureSha256Unchanged': prior['fixtureSha256'], 'scriptBodiesPreserved': True, 'rerunNotByD': True},
    'remaining': 'Primary resume-after15-builder-gps-manual with exact prior-results retains three cases and runs remaining14; no assumed pass or native visual claim by D.',
    'visualReview': 'PENDING_PRIMARY_REVIEW'}
(HERE / 'native-bridge-frontier.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': receipt['status'], 'browser': receipt['browser'], 'verifiedCases': len(valid), 'remaining': 14}))
