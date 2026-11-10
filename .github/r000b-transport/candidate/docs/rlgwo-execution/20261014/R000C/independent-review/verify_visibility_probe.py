"""Read-only reconciliation of the bounded passive diagnostic and existing controls."""
from pathlib import Path
import hashlib, json

OUT = Path(__file__).resolve().parent
EV = OUT.parent
ROOT = EV.parent / 'salah_widget'
ACQ = EV / 'native/firefox-headed-visibility-probe'
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_bytes())
b = read(ACQ / 'diagnostic-binding.json')
assert b['diagnosticOnly'] and b['status'] == 'DIAGNOSTIC_COMPLETE' and b['driverExitCode'] == 1
assert b['probeSha256'] == sha((EV / 'visibility_probe.py').read_bytes()) == '9d4b7cc44a888aed71224f7566763aeee36e0edccf48cefb09e5005716679e90'
assert b['driverSha256'] == sha((ROOT / 'tools/qa/run_r000c_native.py').read_bytes()) == '76cdd0cc607a4c1df85d69a492c7d4994dfeda26d9cf55b2ce0b278914f9ffce'
r = read(ACQ / 'R000C-night-reduced/receipt.json')
results = read(ACQ / 'results.json')
packet = read(ROOT / 'tests/rlgwo/R000C-cases.json')
assert results['status'] == r['status'] == 'FAIL'
assert results['runtimeUnchanged'] is True
assert results['casesSha256'] == sha((ROOT / 'tests/rlgwo/R000C-cases.json').read_bytes())
assert r['checks'] == {} and r['observations'] == [] and r['watches'] == []
assert 'DIAGNOSTIC_COMPLETE' in r['exception'] and not r['pageErrors']
assert results['cases'][0]['receiptSha256'] == sha((ACQ / 'R000C-night-reduced/receipt.json').read_bytes())
assert sha((ACQ / 'R000C-night-reduced' / r['video']['file']).read_bytes()) == r['video']['sha256']
assert sha(Path(r['browser']['executable']).read_bytes()) == r['browser']['executableSha256']
assert read(ACQ / 'R000C-night-reduced/case-input.json') == next(c for c in packet['cases'] if c['id'] == r['id'])
for path, digest in packet['sourceFiles'].items(): assert sha((ROOT / path).read_bytes()) == digest
p = read(ACQ / 'passive-visibility.json')
samples = p['samples']
assert p['diagnosticOnly'] is True and len(samples) == 21
assert samples[-1]['hostMonotonic'] - samples[0]['hostMonotonic'] == 20
renders = []
for sample in samples:
    s = sample['state']
    assert s['visibility'] == 'visible' and s['hidden'] is False
    assert s['paused'] is False and s['loopStarted'] is True and s['visibilityEvents'] == []
    assert s['rect'] == {'x': 0, 'y': 0, 'width': 325, 'height': 530}
    assert s['viewport'] == {'width': 390, 'height': 600}
    assert s['precip'] is None and s['wxBusy'] is False
    wx = [q for q in s['requests'] if 'api.open-meteo.com' in q['url']]
    assert len(wx) == 1 and wx[0]['jsonReads'] == 1 and wx[0]['jsonSettled'] is True
    if not renders or renders[-1] != s['lastRenderAtMs']: renders.append(s['lastRenderAtMs'])
assert renders == [551, 1224, 3279, 7287, 15344]
controls = []
for lane in ['firefox-night', 'firefox-boundary-preferences']:
    rp = EV / 'native' / lane / 'R000C-night-reduced/receipt.json'
    prior = read(rp)
    assert prior['browser']['headless'] is True and prior['browser']['executableSha256'] == r['browser']['executableSha256']
    assert all(o['state']['motion'] == {'reduced': True, 'full': False} for o in prior['observations'])
    rows = []
    for o in prior['observations']:
        s = o['state']
        rows.append({'stage': o['stage'], 'fixtureElapsedMs': s['elapsedMs'], 'fixtureStartedPerformanceMs': prior['fixture']['started'], 'lastRenderPerformanceMs': s['qa']['render']['atMs'], 'renderAgeMs': s['elapsedMs'] + prior['fixture']['started'] - s['qa']['render']['atMs']})
    controls.append({'lane': lane, 'receiptSha256': sha(rp.read_bytes()), 'observations': rows, 'limit': 'Existing failed reduced native recordings; these state comparisons do not rescue their pixels.'})
report = {
    'schema': 'r000c-independent-passive-visibility/v1',
    'probeSha256': b['probeSha256'], 'driverSha256': b['driverSha256'],
    'samplesSha256': sha((ACQ / 'passive-visibility.json').read_bytes()),
    'bindingSha256': sha((ACQ / 'diagnostic-binding.json').read_bytes()),
    'receiptSha256': sha((ACQ / 'R000C-night-reduced/receipt.json').read_bytes()),
    'video': r['video'], 'sampleCount': 21, 'hostSpanSeconds': 20,
    'allVisibleUnpausedWithFullCard': True, 'visibilityChangeEvents': 0,
    'distinctObservedRenderTimesMs': renders,
    'observedRenderGapsMs': [z-a for a,z in zip(renders,renders[1:])],
    'lastRenderAgeMs': samples[-1]['state']['nativeElapsedMs'] - renders[-1],
    'headlessReducedControls': controls,
    'qualificationCredit': 'NONE; no acceptance assertions or watches executed.',
    'finding': 'Persistent sampled product visibility pause is contradicted. Native scheduling/compositor cause remains unknown; no raw rAF callback or native paint association was captured.'
}
(OUT / 'visibility-probe-check.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
print(json.dumps({k:report[k] for k in ['sampleCount','hostSpanSeconds','allVisibleUnpausedWithFullCard','visibilityChangeEvents','distinctObservedRenderTimesMs','observedRenderGapsMs','lastRenderAgeMs','qualificationCredit','finding']}, indent=2))
