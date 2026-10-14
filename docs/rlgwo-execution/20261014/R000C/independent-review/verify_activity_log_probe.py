"""Offline native log, passive trace and original-video association checks."""
from pathlib import Path
import hashlib, json, subprocess

OUT = Path(__file__).resolve().parent
EV = OUT.parent
ROOT = EV.parent / 'salah_widget'
ACQ = EV / 'native/firefox-headed-activity-probe'
CASE = ACQ / 'R000C-night-reduced'
LOGS = EV / 'native-activity-logs'
DEST = OUT / 'firefox-headed-activity-probe/R000C-night-reduced'
DEST.mkdir(parents=True, exist_ok=True)
FFMPEG = Path(r'C:\Users\theis\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe')
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_bytes())
manifest = read(LOGS / 'manifest.json')
for f in manifest['files']:
    data = (LOGS / f['path']).read_bytes()
    assert len(data) == f['bytes'] and sha(data) == f['sha256']
assert manifest['environment']['MOZ_LOG'] == 'timestamp,PresShell:5,nsRefreshDriver:5'
b = read(ACQ / 'diagnostic-binding.json')
assert b['probeSha256'] == sha((EV / 'visibility_probe.py').read_bytes())
assert b['driverSha256'] == sha((ROOT / 'tools/qa/run_r000c_native.py').read_bytes())
assert b['diagnosticOnly'] and b['status'] == 'DIAGNOSTIC_COMPLETE' and b['driverExitCode'] == 1
r = read(CASE / 'receipt.json')
results = read(ACQ / 'results.json')
assert r['status'] == results['status'] == 'FAIL' and results['runtimeUnchanged'] is True
assert r['observations'] == [] and r['checks'] == {} and r['watches'] == []
assert not r['pageErrors'] and 'DIAGNOSTIC_COMPLETE' in r['exception']
assert r['browser']['headless'] is False
assert sha(Path(r['browser']['executable']).read_bytes()) == r['browser']['executableSha256']
packet = read(ROOT / 'tests/rlgwo/R000C-cases.json')
assert read(CASE / 'case-input.json') == next(c for c in packet['cases'] if c['id'] == r['id'])
assert results['casesSha256'] == sha((ROOT / 'tests/rlgwo/R000C-cases.json').read_bytes())
for path, digest in packet['sourceFiles'].items(): assert sha((ROOT / path).read_bytes()) == digest

log_path = LOGS / 'refresh.log.child-6.moz_log'
log = log_path.read_text(encoding='utf8')
lines = log.splitlines()
first = next(i for i, s in enumerate(lines) if f'ComputeActiveness({r["url"]}, 1)' in s)
second = next(i for i, s in enumerate(lines) if f'ComputeActiveness({r["url"]}, 0)' in s)
block = lines[first:second+3]
assert first + 1 == 84 and second + 1 == 90
assert all('[Child 33140: Main Thread]' in s for s in block)
expected = [
    'BrowsingContext 20135295b00  active: 0',
    'BrowserChild 20135241800 is visible and preserving layers',
    '[2013b66ed00] RemoveRefreshDriver 20135098400',
    '[2013502c3c0] AddRefreshDriver 20135098400',
    '[2013502c3c0] inactive timer got new refresh driver 20135098400, resetting rate',
]
assert all(want in line for want, line in zip(expected, lines[first+1:first+6]))
assert not any('is not visible' in s or 'not preserving layers' in s for s in block)
assert not log.endswith('\n') and 'inactive timer next tick' not in log
samples = read(ACQ / 'passive-visibility.json')['samples']
assert len(samples) == 21
renders = []
for sample in samples:
    s = sample['state']
    assert s['visibility'] == 'visible' and s['hidden'] is False and s['paused'] is False and s['loopStarted'] is True
    assert s['visibilityEvents'] == [] and s['rect'] == {'x':0,'y':0,'width':325,'height':530}
    if not renders or renders[-1] != s['lastRenderAtMs']: renders.append(s['lastRenderAtMs'])
assert renders == [602, 1376, 3226, 7233, 15482]

index = read(CASE / 'pixel-review/index.json')
video = CASE / r['video']['file']
assert sha(video.read_bytes()) == r['video']['sha256'] == index['videoSha256']
assert sha((CASE / 'receipt.json').read_bytes()) == index['receiptSha256'] == results['cases'][0]['receiptSha256']
probe = json.loads(subprocess.check_output([str(FFMPEG.with_name('ffprobe.exe')), '-v','error','-select_streams','v:0','-show_entries','stream=width,height:frame=best_effort_timestamp_time','-of','json',str(video)]))
assert [probe['streams'][0]['width'], probe['streams'][0]['height']] == [390,600]
proc = subprocess.Popen([str(FFMPEG),'-v','error','-i',str(video),'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'], stdout=subprocess.PIPE)
n = 0
while True:
    frame = proc.stdout.read(390*600*3)
    if not frame: break
    assert len(frame) == 390*600*3 and sha(frame) == index['frames'][n]['decodedRgbSha256']
    assert index['frames'][n]['ptsSeconds'] == float(probe['frames'][n]['best_effort_timestamp_time'])
    n += 1
assert proc.wait() == 0 and n == len(index['frames']) == len(probe['frames']) == 543
assert len(index['samples']) == 543 and all(s['suspect'] for s in index['samples'])
extractions = []
for ordinal in [250, n-1]:
    dest = DEST / f'original-{ordinal:05d}.png'
    subprocess.run([str(FFMPEG),'-v','error','-i',str(video),'-vf',f'select=eq(n\\,{ordinal})','-frames:v','1','-fps_mode','passthrough',str(dest)], check=True)
    extractions.append({'ordinal':ordinal,'ptsSeconds':index['frames'][ordinal]['ptsSeconds'],'file':str(dest.relative_to(OUT)),'sha256':sha(dest.read_bytes())})
report = {
    'schema':'r000c-independent-native-activity-log/v1',
    'logManifestSha256':sha((LOGS/'manifest.json').read_bytes()),
    'childLogSha256':sha(log_path.read_bytes()),'fixtureUrl':r['url'],
    'nativeAssociation':{'pid':33140,'thread':'Main Thread','firstFixtureLine':84,'secondFixtureLine':90,'browsingContext':'20135295b00','browserChild':'20135241800','refreshDriver':'20135098400','regularTimer':'2013b66ed00','inactiveTimer':'2013502c3c0','finding':'Exact fixture activity becomes false through visible/preserving-layers plus inactive browsing-context branch, corroborated by refresh-driver transfer and subsequent old state0.'},
    'logLimit':'The child log is truncated at startup; no native tick series or end-of-watch activity is proved.',
    'contentVisibilityAllVisibleUnpaused':True,'observedRenderTimesMs':renders,
    'video':r['video'],'frames':n,'durationPts':index['durationPts'],'allFrameHashesAndPtsMatch':True,'lowInformationCandidates':543,
    'extractions':extractions,'qualificationCredit':'NONE',
    'proposedWrapperSha256':sha((EV/'activity_override_probe.py').read_bytes()),
    'decision':'One separately bound20s isolated-launch top-level-always-active diagnostic is justified; no full qualification retry or reduced-motion override is granted.'
}
(OUT/'activity-log-probe-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
