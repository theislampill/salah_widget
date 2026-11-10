"""Offline reconciliation of the completed, unsuccessful activity override diagnostic."""
from pathlib import Path
import hashlib, json, subprocess
OUT=Path(__file__).resolve().parent; EV=OUT.parent; ROOT=EV.parent/'salah_widget'
ACQ=EV/'native/firefox-headed-active-probe'; CASE=ACQ/'R000C-night-reduced'; LOGS=EV/'native-active-logs'
FFMPEG=Path(r'C:\Users\theis\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe')
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
manifest=read(LOGS/'manifest.json')
for f in manifest['files']:
    data=(LOGS/f['path']).read_bytes();assert len(data)==f['bytes'] and sha(data)==f['sha256']
env=read(LOGS/'environment.json');assert env['MOZ_LOG']=='timestamp,sync,PresShell:5,nsRefreshDriver:5'
b=read(ACQ/'activity-override-binding.json');assert b['preference']=={'layout.testing.top-level-always-active':True}
assert b['wrapperSha256']==sha((EV/'activity_override_probe.py').read_bytes())=='af609107a12d81ee3cdd2c93a3d211412758bf44273b07877bd745f0c1a7f98e'
assert b['probeSha256']==sha((EV/'visibility_probe.py').read_bytes())
r=read(CASE/'receipt.json');results=read(ACQ/'results.json');index=read(CASE/'pixel-review/index.json')
assert r['status']==results['status']=='FAIL' and results['runtimeUnchanged'] is True
assert r['observations']==[] and r['checks']=={} and r['watches']==[] and not r['pageErrors']
assert results['driverSha256']==sha((ROOT/'tools/qa/run_r000c_native.py').read_bytes())
assert results['casesSha256']==sha((ROOT/'tests/rlgwo/R000C-cases.json').read_bytes())
assert sha(Path(r['browser']['executable']).read_bytes())==r['browser']['executableSha256']
samples=read(ACQ/'passive-visibility.json')['samples'];assert len(samples)==21
for sample in samples:
    s=sample['state'];assert s['visibility']=='visible' and s['hidden'] is False and s['paused'] is False
    assert s['lastRenderAtMs']==687 and s['rect']=={'x':0,'y':0,'width':325,'height':530}
log_path=LOGS/'refresh.log.child-6.moz_log';log=log_path.read_text(encoding='utf8');lines=log.splitlines()
exact=[i for i,s in enumerate(lines) if 'ComputeActiveness('+r['url']+', 1)' in s]
assert len(exact)>=2 and all('Activeness overridden by pref' in lines[i+2] for i in exact)
assert '[2544ab66e00] Allocating transaction id 6' in log and '[2544ab66e00] Allocating transaction id 7' in log
assert '[2544ab66e00] Hit max pending transaction limit, entering wait mode' in log
assert '[2544ab66e00] Over max pending transaction limit when trying to paint, skipping' in log
assert '[2544ab66e00] Completed transaction id 6' not in log and '[2544ab66e00] Completed transaction id 7' not in log
video=CASE/r['video']['file'];assert sha(video.read_bytes())==r['video']['sha256']==index['videoSha256']
assert sha((CASE/'receipt.json').read_bytes())==index['receiptSha256']==results['cases'][0]['receiptSha256']
probe=json.loads(subprocess.check_output([str(FFMPEG.with_name('ffprobe.exe')),'-v','error','-select_streams','v:0','-show_entries','stream=width,height:frame=best_effort_timestamp_time','-of','json',str(video)]))
assert [probe['streams'][0]['width'],probe['streams'][0]['height']]==[390,600]
proc=subprocess.Popen([str(FFMPEG),'-v','error','-i',str(video),'-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
n=0
while True:
    frame=proc.stdout.read(390*600*3)
    if not frame:break
    assert len(frame)==390*600*3 and sha(frame)==index['frames'][n]['decodedRgbSha256']
    assert index['frames'][n]['ptsSeconds']==float(probe['frames'][n]['best_effort_timestamp_time']);n+=1
assert proc.wait()==0 and n==len(index['frames'])==len(probe['frames'])==541
assert len(index['samples'])==541 and all(x['suspect'] for x in index['samples'])
dest=OUT/'activity-override-original-00500.png'
subprocess.run([str(FFMPEG),'-v','error','-i',str(video),'-vf','select=eq(n\\,500)','-frames:v','1','-fps_mode','passthrough',str(dest)],check=True)
report={'schema':'r000c-independent-activity-override-failure/v1','environmentSha256':sha((LOGS/'environment.json').read_bytes()),'logManifestSha256':sha((LOGS/'manifest.json').read_bytes()),'childLogSha256':sha(log_path.read_bytes()),'exactFixtureOverrideLines':[i+1 for i in exact],'nativeRefreshDriver':'2544ab66e00','nativePendingTransactionIds':[6,7],'completionOfThoseIdsInRetainedLog':False,'sampleCount':21,'lastRenderAtMsAllSamples':687,'video':r['video'],'frames':n,'durationPts':index['durationPts'],'allFrameHashesAndPtsMatch':True,'lowInformationCandidates':541,'extractedOriginal':{'ordinal':500,'ptsSeconds':index['frames'][500]['ptsSeconds'],'file':dest.name,'sha256':sha(dest.read_bytes())},'diagnosticCriteria':{'nativeActivityOverride':True,'ordinaryRenderProgress':False,'readableOriginalCard':False},'qualificationCredit':'NONE','decision':'The override is not a useful qualified recording route. Do not run a full headed replay or another experiment under this finding.'}
(OUT/'activity-override-failure-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
