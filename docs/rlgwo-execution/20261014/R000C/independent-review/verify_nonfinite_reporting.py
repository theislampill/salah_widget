"""Offline comparison of the reporter-only successor; no browser imports or effects."""
from pathlib import Path
import ast, copy, hashlib, json, math

OUT = Path(__file__).resolve().parent
EV = OUT.parent
ROOT = EV.parent / 'salah_widget'
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_bytes())

old = EV / 'fixture-v4/run_r000c_native.py'
new = ROOT / 'tools/qa/run_r000c_native.py'
assert sha(old.read_bytes()) == 'ef71a7d4fb7079b67de7a79dabbd43363577f2b3bf852fb24f8b323a784ee58e'
assert sha(new.read_bytes()) == '76cdd0cc607a4c1df85d69a492c7d4994dfeda26d9cf55b2ce0b278914f9ffce'
assert sha((ROOT / 'tests/rlgwo/R000C-cases.json').read_bytes()) == '268d820ff632135eb86ed92f3650b619cac71440eef2e282605d00dcd4749f67'
before, after = ast.parse(old.read_text(encoding='utf8')), ast.parse(new.read_text(encoding='utf8'))
def retained(tree):
    return ast.Module(body=[n for n in tree.body if not (
        isinstance(n, ast.FunctionDef) and n.name in ['dump', 'json_evidence']
        or isinstance(n, ast.Import) and len(n.names) == 1 and n.names[0].name == 'math'
    )], type_ignores=[])
assert ast.dump(retained(before), include_attributes=False) == ast.dump(retained(after), include_attributes=False)
for name, digest in read(EV / 'fixture-v4/manifest.json')['files'].items():
    assert sha((EV / 'fixture-v4' / name).read_bytes()) == digest
packet = read(ROOT / 'tests/rlgwo/R000C-cases.json')
prior_packet = read(EV / 'fixture-v4/R000C-cases.json')
prior_packet['sourceFiles']['tools/qa/run_r000c_native.py'] = packet['sourceFiles']['tools/qa/run_r000c_native.py']
assert prior_packet == packet
for path, digest in packet['sourceFiles'].items():
    assert sha((ROOT / path).read_bytes()) == digest, path

# Execute only the isolated helper and original checker, without main or imports.
funcs = [n for n in after.body if isinstance(n, ast.FunctionDef) and n.name in ['json_evidence', 'dump', 'check']]
ns = {'math': math, 'json': json}
exec(compile(ast.Module(body=funcs, type_ignores=[]), str(new), 'exec'), ns)
source = {'numbers': [None, False, True, 0, -3.5, 20, 'NaN', 'Infinity', '-Infinity'],
          'nested': {'diagnostics': [float('nan'), float('inf'), -float('inf')]}}
encoded = ns['json_evidence'](source)
assert encoded['numbers'] == source['numbers']
assert encoded is not source and encoded['numbers'] is not source['numbers']
assert encoded['nested'] is not source['nested'] and encoded['nested']['diagnostics'] is not source['nested']['diagnostics']
assert encoded['nested']['diagnostics'] == [{'$nativeNonFiniteNumber': x} for x in ['NaN', 'Infinity', '-Infinity']]
assert math.isnan(source['nested']['diagnostics'][0]) and source['nested']['diagnostics'][1:] == [float('inf'), -float('inf')]
assert json.loads(json.dumps(encoded, allow_nan=False)) == encoded

receipt = read(EV / 'native/firefox-boundary-preferences/R000C-night-reduced/receipt.json')
state = copy.deepcopy(receipt['observations'][0]['state'])
checks = ns['check'](state, receipt['fixture'], 20, None, packet['sourceFiles']['index.html'])
assert all(checks.values())
state['reviewOnlyDiagnostic'] = float('nan')
assert ns['check'](state, receipt['fixture'], 20, None, packet['sourceFiles']['index.html']) == checks
ns['dump'](OUT / 'nonfinite-serialized-control.json', state)
assert math.isnan(state['reviewOnlyDiagnostic'])
assert read(OUT / 'nonfinite-serialized-control.json')['reviewOnlyDiagnostic'] == {'$nativeNonFiniteNumber': 'NaN'}
state['raw']['temp'] = float('nan')
assert ns['check'](state, receipt['fixture'], 20, None, packet['sourceFiles']['index.html'])['temperatureAdmitted'] is False
ns['dump'](OUT / 'nonfinite-required-field-control.json', state)
assert ns['check'](state, receipt['fixture'], 20, None, packet['sourceFiles']['index.html'])['temperatureAdmitted'] is False

failed = EV / 'native/firefox-reduced-host-wait'
inventory = read(failed / 'serialization-failure.json')
for f in inventory['files']:
    data = (failed / f['path']).read_bytes()
    assert len(data) == f['bytes'] and sha(data) == f['sha256']
results = read(failed / 'results.json')
assert results['status'] == 'FAIL' and results['cases'] == [] and results['runtimeUnchanged'] is True
assert results['driverSha256'] == sha(old.read_bytes())
assert results['casesSha256'] == sha((EV / 'fixture-v4/R000C-cases.json').read_bytes())
assert not (failed / 'R000C-night-reduced/receipt.json').exists()
assert not (failed / 'R000C-night-reduced/initial.json').exists()
stderr = (failed / 'stderr.txt').read_text(encoding='utf8')
assert 'Out of range float values are not JSON compliant: nan' in stderr
report = {
    'schema': 'r000c-independent-nonfinite-reporting/v1',
    'priorDriverSha256': sha(old.read_bytes()),
    'successorDriverSha256': sha(new.read_bytes()),
    'successorPacketSha256': sha((ROOT / 'tests/rlgwo/R000C-cases.json').read_bytes()),
    'allOtherDriverAstIdentical': True,
    'casePacketOnlyDriverPinChanged': True,
    'allSourcePinsMatch': True,
    'priorVersionPreserved': True,
    'freshTreeAndRawValuesUnmutated': True,
    'finiteNullBooleanStringControlsUnchanged': True,
    'nativeNonFiniteTagsCorrect': True,
    'requiredFieldNaNStillFailsOriginalCheck': True,
    'abortedAttemptInventoryVerified': True,
    'abortedAttemptHasNoReceiptOrWatchCredit': True,
    'unknown': 'The exact native NaN field in the aborted attempt was never saved and remains unknown.',
    'decision': 'Reporter-only repair is bounded and justified. One still-uncompleted reduced control may run with this pinned successor and original input/assertions/watch boundaries. No native or pixel qualification follows from this serialization control.'
}
(OUT / 'nonfinite-reporting-check.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
print(json.dumps(report, indent=2))
