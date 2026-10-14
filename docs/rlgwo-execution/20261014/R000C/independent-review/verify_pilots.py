"""Read-only original-media and source binding check. Outputs stay beside this script."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess

OUT = Path(__file__).resolve().parent
EVIDENCE = OUT.parent
ROOT = EVIDENCE.parent / 'salah_widget'
FFMPEG = Path(r'C:\Users\theis\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe')
FFPROBE = FFMPEG.with_name('ffprobe.exe')

def sha(data):
    return hashlib.sha256(data).hexdigest()

report = {'schema': 'r000c-independent-pilot-binding/v1', 'source': {}, 'lanes': [], 'limits': 'No browser execution. Frame hashes establish identity, not visual acceptance. PTS and host monotonic values have no unique association in these acquisitions.'}
packet = json.loads((ROOT / 'tests/rlgwo/R000C-cases.json').read_bytes())
for rel, expected in packet['sourceFiles'].items():
    observed = sha((ROOT / rel).read_bytes())
    report['source'][rel] = {'sha256': observed, 'matches': observed == expected}
    assert observed == expected, rel

spec = importlib.util.spec_from_file_location('r000c_single_document', ROOT / 'tools/qa/r000c_single_document.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
html, binding = module.prepare((ROOT / 'index.html').read_bytes(), (ROOT / 'tests/rlgwo/weather-browser-fixture.html').read_bytes())
original_binding = json.loads((EVIDENCE / 'native/firefox-single-pilot/single-document-binding.json').read_bytes())
assert binding == original_binding
report['regeneratedSingleDocumentBindingIdentical'] = True
report['singleDocument'] = binding

for lane in ['firefox-day', 'firefox-headed-pilot', 'firefox-single-pilot']:
    case = EVIDENCE / 'native' / lane / 'R000C-invalid-precip'
    receipt_bytes = (case / 'receipt.json').read_bytes()
    receipt = json.loads(receipt_bytes)
    index = json.loads((case / 'pixel-review/index.json').read_bytes())
    video = case / receipt['video']['file']
    assert sha(video.read_bytes()) == receipt['video']['sha256'] == index['videoSha256']
    assert sha(receipt_bytes) == index['receiptSha256']
    probe = json.loads(subprocess.check_output([str(FFPROBE), '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:frame=best_effort_timestamp_time', '-of', 'json', str(video)]))
    assert probe['streams'][0]['width'] == 390 and probe['streams'][0]['height'] == 600
    process = subprocess.Popen([str(FFMPEG), '-v', 'error', '-i', str(video), '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    count = 0
    while True:
        data = process.stdout.read(390 * 600 * 3)
        if not data:
            break
        assert len(data) == 390 * 600 * 3
        frame = index['frames'][count]
        assert frame['ordinal'] == count and frame['decodedRgbSha256'] == sha(data)
        assert frame['ptsSeconds'] == float(probe['frames'][count]['best_effort_timestamp_time'])
        count += 1
    assert process.wait() == 0 and count == len(index['frames']) == len(probe['frames'])
    suspects = [s for s in index['samples'] if s['suspect']]
    report['lanes'].append({'lane': lane, 'video': receipt['video'], 'receiptSha256': sha(receipt_bytes), 'indexSha256': sha((case / 'pixel-review/index.json').read_bytes()), 'allDecodedFrameHashesAndPtsMatch': True, 'frameCount': count, 'lastPts': index['durationPts'], 'candidateCount': len(suspects), 'lastCandidate': suspects[-1], 'navToInitialHostSeconds': receipt['observations'][0]['hostMonotonic'] - receipt['navigationHostMonotonic'], 'initialFixtureElapsedMs': receipt['observations'][0]['state']['elapsedMs'], 'browser': receipt['browser']})
    # Independent original extraction, unfiltered; selected timestamps retain failure and healthy counterevidence.
    wanted = {'firefox-day': [100, 104, 105], 'firefox-headed-pilot': [296], 'firefox-single-pilot': [95, 96, 100, 304]}[lane]
    for ordinal in wanted:
        target = OUT / f'{lane}-frame-{ordinal:05d}.png'
        subprocess.run([str(FFMPEG), '-v', 'error', '-i', str(video), '-vf', f'select=eq(n\\,{ordinal})', '-frames:v', '1', '-fps_mode', 'passthrough', str(target)], check=True)

reference = ROOT / 'docs/rlgwo-execution/20261014/R0007/headed-replacement/firefox/shared-preservation-no-preference'
report['referenceR0007'] = {name: {'sha256': sha((reference / name).read_bytes())} for name in ['native.webm', 'case-input.json', 'browser-identity.json', 'document-hashes.json', 'live-start-presentation.json']}
report['referenceR0007']['documentHashes'] = json.loads((reference / 'document-hashes.json').read_bytes())
report['referenceR0007']['browserIdentity'] = json.loads((reference / 'browser-identity.json').read_bytes())
report['referenceR0007']['presentation'] = json.loads((reference / 'live-start-presentation.json').read_bytes())
report['referenceFiles'] = {}
for rel in ['tests/rlgwo/prayer-browser-fixture.cjs', 'tools/cp9/r0007_browser.py']:
    current = (ROOT / rel).read_bytes()
    prior = subprocess.check_output(['git', '--no-optional-locks', 'show', '87c3a19ff275197e1a49bebd7abc30ad2849137e:' + rel], cwd=ROOT)
    report['referenceFiles'][rel] = {'currentRawSha256': sha(current), 'currentLfSha256': sha(current.replace(b'\r\n', b'\n')), 'priorCandidateBlobSha256': sha(prior), 'sameAfterLfNormalization': current.replace(b'\r\n', b'\n') == prior.replace(b'\r\n', b'\n')}

(OUT / 'pilot-binding-check.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
print(json.dumps({'sourcePins': len(report['source']), 'singleDocumentRegeneration': True, 'allFramesReDecoded': sum(x['frameCount'] for x in report['lanes']), 'lanes': [{k: row[k] for k in ['lane', 'frameCount', 'candidateCount', 'lastCandidate']} for row in report['lanes']], 'referenceFiles': report['referenceFiles']}, indent=2))
