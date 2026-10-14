"""Narrow currentness reconciliation after the demonstrated sky-publication fix."""
from pathlib import Path
import hashlib,json,sys

ROOT=Path(r'C:\Users\theis\.codex\worktrees\r000b-close\salah_widget')
OUT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'tools/cp9'))
from runtime_identity import runtime_identity

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((OUT/name).read_bytes())
previous=read('runtime.json'); candidate=read('recovery-handoff-source/flash-counterexample/candidate.json')
now=runtime_identity(ROOT)
assert now==candidate['runtime']
assert set(now['files'])==set(previous['files'])
changed=[p for p in sorted(now['files']) if now['files'][p]!=previous['files'][p]]
assert changed==['offline.html','real-sky/native-host.mjs','real-sky/native-sky.js']
accepted=read('accepted-currentness.json');source=(ROOT/'index.html').read_text(encoding='utf-8')
regions=[]
for row in accepted['regions']:
    a=source.index(row['startAnchor']);b=source.index(row['endAnchor'],a)
    actual=hashlib.sha256(source[a:b].encode()).hexdigest()
    assert actual==row['candidateSha256'],row['id']
    regions.append({'id':row['id'],'sha256':actual,'matchesPreviouslyReviewedCandidate':True})
prior_files=read('final-source-preflight.json')['files']
pins=[]
for row in prior_files:
    path=row['path'];actual=digest(ROOT/path)
    if path not in ['offline.html','HANDOFF.md']:assert actual==row['sha256'],path
    pins.append({'path':path,'previousSha256':row['sha256'],'currentSha256':actual,
        'unchanged':actual==row['sha256']})
radar=[]
for browser in ['chromium','firefox']:
    name=f'native-qualified/{browser}-default/receipt.json';r=read(name)
    assert r['runtime']==previous and r['runtimeUnchanged']
    assert r['sourceSha256']==now['files']['index.html']['sha256']
    assert r['wrapperSha256']==digest(ROOT/'tests/rlgwo/r000b-weather-fixture.html')
    assert r['driverSha256']==digest(ROOT/'tools/qa/run_r000b_native.py')
    assert any(o['stage']=='radar-restored' for o in r['observations'])
    radar.append({'receipt':name,'receiptSha256':digest(OUT/name),
        'reuse':'Ordinary radar acquisition, 20-minute source/receipt expiry and ten-minute retry only.',
        'excluded':'No post-repair sky-withdrawal, Moon, cloud-pixel or motion credit.'})
result={'schema':'r000b-post-handoff-currentness/v1','status':'SCOPED_SOURCE_CURRENTNESS_PASS',
    'reviewedBase':accepted['reviewedBase'],'previousRuntimeSha256':previous['treeSha256'],
    'currentRuntimeSha256':now['treeSha256'],'runtimeFileCount':len(now['files']),
    'changedRuntimeFiles':changed,'unchangedRuntimeFiles':[p for p in sorted(now['files']) if p not in changed],
    'acceptedRows':accepted['acceptedRows'],'regions':regions,'pins':pins,'radarReuse':radar,
    'sourceControlReuse':'B04/B13/B14 source, tests and mutation driver bytes are unchanged. The 57 source controls, four semantic mutants, accepted authority consumers and V45 source equivalence remain current within their original scope.',
    'affectedQualification':'Sky withdrawal and generated sky/standalone consumers require the new source controls and six native-atomic-qualified cases. The intermediate native-handoff-qualified cases are retained, including the recovery flash failure. Pixel review is a separate gate.',
    'bindings':{p:digest(OUT/p) for p in ['runtime.json','accepted-currentness.json','final-source-preflight.json','recovery-handoff-source/flash-counterexample/candidate.json','green.tap','mutants/receipt.json','native-reconciliation.json']}}
(OUT/'post-handoff-currentness.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(f"PASS: {len(regions)} unchanged reviewed regions; {len(now['files'])-len(changed)} unchanged runtime entries; two narrowly reused radar receipts")
