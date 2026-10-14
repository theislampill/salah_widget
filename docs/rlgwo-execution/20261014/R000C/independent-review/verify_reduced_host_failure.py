"""Independent custody and observed-state review of the failed headed control."""
from pathlib import Path
import hashlib, json, subprocess

OUT = Path(__file__).resolve().parent
EV = OUT.parent
ROOT = EV.parent / 'salah_widget'
ACQ = EV / 'native/firefox-reduced-host-wait-encoded'
CASE = ACQ / 'R000C-night-reduced'
DEST = OUT / 'firefox-reduced-host-wait-encoded/R000C-night-reduced'
DEST.mkdir(parents=True, exist_ok=True)
FFMPEG = Path(r'C:\Users\theis\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe')
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_bytes())
r, index, results = read(CASE / 'receipt.json'), read(CASE / 'pixel-review/index.json'), read(ACQ / 'results.json')
packet = read(ROOT / 'tests/rlgwo/R000C-cases.json')
assert read(CASE / 'case-input.json') == next(c for c in packet['cases'] if c['id'] == r['id'])
assert results['driverSha256'] == sha((ROOT / 'tools/qa/run_r000c_native.py').read_bytes()) == '76cdd0cc607a4c1df85d69a492c7d4994dfeda26d9cf55b2ce0b278914f9ffce'
assert results['casesSha256'] == sha((ROOT / 'tests/rlgwo/R000C-cases.json').read_bytes()) == '268d820ff632135eb86ed92f3650b619cac71440eef2e282605d00dcd4749f67'
for path, digest in packet['sourceFiles'].items(): assert sha((ROOT / path).read_bytes()) == digest
for path, f in results['runtime']['files'].items():
    data = (ROOT / path).read_bytes()
    assert len(data) == f['bytes'] and sha(data) == f['sha256']
assert results['runtimeUnchanged'] is True
assert results['status'] == r['status'] == 'FAIL'
assert len(results['cases']) == 1 and results['cases'][0]['receiptSha256'] == sha((CASE / 'receipt.json').read_bytes()) == index['receiptSha256']
assert r['browser']['family'] == 'firefox' and r['browser']['headless'] is False
assert sha(Path(r['browser']['executable']).read_bytes()) == r['browser']['executableSha256']
assert r['observerMode'] == 'full-diagnostic-boundaries-passive-recovery' and r['watchWaitMode'] == 'host-monotonic-sleep'
assert all(r['checks'].values()) and not r['pageErrors']
assert [o['stage'] for o in r['observations']] == ['initial', 'initial-30s']
assert len(r['watches']) == 1 and r['watches'][0]['stage'] == 'initial'
w = r['watches'][0]
assert w['requiredSeconds'] == 30 and w['endHostMonotonic'] - w['startHostMonotonic'] >= 30
assert 'TimeoutError' in r['exception'] and 'weather?.precip===2' in r['exception']
assert 'fixture' not in r  # Failure occurred before the final ledger capture.
observations = []
for o in r['observations']:
    s = o['state']
    assert s['raw']['temp'] == s['cached']['w']['temp'] == 20
    assert s['raw']['precip'] is None and s['cached']['w']['precip'] is None
    assert s['raw']['admission']['precip'] == 'invalid measurement'
    assert s['temperature'] == '20°' and s['precip'] == 'off' and s['visibleParticles'] == 0
    assert s['motion'] == {'reduced': True, 'full': False}
    assert s['card'] == {'width': 325, 'height': 530}
    observations.append({'stage': o['stage'], 'hostMonotonic': o['hostMonotonic'], 'elapsedMs': s['elapsedMs'], 'wallUtcMs': s['wallUtcMs'], 'lastRenderAtMs': s['qa']['render']['atMs']})
tags = []
def enumerate_tags(value, path='$'):
    if isinstance(value, dict):
        if '$nativeNonFiniteNumber' in value: tags.append({'path': path, 'value': value})
        for k, v in value.items(): enumerate_tags(v, path + '.' + k)
    elif isinstance(value, list):
        for n, v in enumerate(value): enumerate_tags(v, path + '[' + str(n) + ']')
enumerate_tags(r)
assert [t['path'] for t in tags] == ['$.observations[0].state.qa.render.leftMin', '$.observations[0].state.qa.render.nextEpoch']
assert all(t['value'] == {'$nativeNonFiniteNumber': 'NaN'} for t in tags)
video = CASE / r['video']['file']
assert sha(video.read_bytes()) == r['video']['sha256'] == index['videoSha256'] == 'b088e77e071a195989024b493b89c77146e52acc87eee346ca96f91ef37c14f8'
probe = json.loads(subprocess.check_output([str(FFMPEG.with_name('ffprobe.exe')), '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:frame=best_effort_timestamp_time', '-of', 'json', str(video)]))
assert [probe['streams'][0]['width'], probe['streams'][0]['height']] == [390, 600]
proc = subprocess.Popen([str(FFMPEG), '-v', 'error', '-i', str(video), '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
n = 0
unique = set()
while True:
    frame = proc.stdout.read(390 * 600 * 3)
    if not frame: break
    digest = sha(frame)
    assert len(frame) == 390 * 600 * 3 and digest == index['frames'][n]['decodedRgbSha256']
    assert index['frames'][n]['ptsSeconds'] == float(probe['frames'][n]['best_effort_timestamp_time'])
    unique.add(digest)
    n += 1
assert proc.wait() == 0 and n == len(index['frames']) == len(probe['frames']) == 2420
assert len(index['samples']) == 2420 and all(s['suspect'] for s in index['samples'])
extractions = []
for ordinal in [0, 750, n-1]:
    dest = DEST / f'original-{ordinal:05d}.png'
    subprocess.run([str(FFMPEG), '-v', 'error', '-i', str(video), '-vf', f'select=eq(n\\,{ordinal})', '-frames:v', '1', '-fps_mode', 'passthrough', str(dest)], check=True)
    extractions.append({'ordinal': ordinal, 'ptsSeconds': index['frames'][ordinal]['ptsSeconds'], 'file': str(dest.relative_to(OUT)), 'sha256': sha(dest.read_bytes())})
report = {
    'schema': 'r000c-independent-headed-reduced-failure/v1',
    'video': r['video'], 'receiptSha256': sha((CASE / 'receipt.json').read_bytes()),
    'indexSha256': sha((CASE / 'pixel-review/index.json').read_bytes()),
    'frames': n, 'durationPts': index['durationPts'], 'uniqueDecodedFrameHashes': len(unique),
    'allFrameHashesAndPtsMatch': True, 'lowInformationCandidates': 2420,
    'initialStateChecksTrue': True, 'observations': observations, 'watches': r['watches'],
    'nonFiniteTags': tags, 'nativeRecovery': 'NOT_OBSERVED_TIMEOUT', 'recoveredWatch': 'NOT_EXECUTED',
    'finalFixtureLedger': 'NOT_CAPTURED_AFTER_EXCEPTION',
    'runtimeAndSourcePinsUnchanged': True, 'extractions': extractions,
    'qualification': 'FAIL: original video is unreadable; no recovered control exists. Visual confirmation is recorded in the accompanying review.',
    'cause': 'UNKNOWN; no saved visibility/paused history or uniquely joined native-source witness.'
}
(OUT / 'reduced-host-failure-check.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
print(json.dumps(report, indent=2))
