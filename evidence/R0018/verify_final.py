"""Final source/build/interface reconciliation; no browser rerun or Git effects."""
from pathlib import Path
import datetime, hashlib, json, re, subprocess, sys

ROOT=Path(r'C:\Users\theis\.codex\worktrees\r0018-readability\salah_widget')
OUT=Path(__file__).resolve().parent
BASE='ed5e7afbd2fcf7a59050817e2a561bcdbfa9043d'
sys.path.insert(0,str(ROOT/'tools/cp9'))
from runtime_identity import runtime_identity

def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def command(name,args,expected=0,cwd=ROOT):
    p=subprocess.run(args,cwd=cwd,capture_output=True)
    (OUT/(name+'.stdout')).write_bytes(p.stdout);(OUT/(name+'.stderr')).write_bytes(p.stderr)
    row={'command':args,'cwd':str(cwd),'returncode':p.returncode,'stdout':name+'.stdout','stdoutSha256':sha(p.stdout),'stderr':name+'.stderr','stderrSha256':sha(p.stderr)}
    write(OUT/(name+'.json'),row)
    assert p.returncode==expected,row
    return row

before=runtime_identity(ROOT)
assert before['treeSha256']=='67fd9c8f122100506bef93473a1e335b8b441ac7bf55f540c099d2e34e5c970c'
build=command('final-build-r2',[sys.executable,'-B','tools/build_native.py'])
after=runtime_identity(ROOT)
assert before==after,'Canonical rebuild changed qualified runtime'
v1=command('final-v1-payload',[sys.executable,'-B','tools/verify_v1.py'])
baseline_pages=command('baseline-v1-pages',[sys.executable,'-B','tools/verify_v1.py','--check-pages'],expected=1,cwd=Path(r'C:\Users\theis\.codex\worktrees\r0018-evidence\salah_widget'))
write(OUT/'v1-pages-preflight-reconciliation.json',{'retainedCandidateFailure':read(OUT/'final-v1.json'),'exactBaseFailure':baseline_pages,'cause':'The existing optional --check-pages preflight rejects any _config.yml without .nojekyll. Main already has a reviewed R000C recording-only exclusion; this repair changes neither configuration nor V1. The checker itself is unchanged.','scope':'Payload manifest verification passes; actual premerge public V1 bytes match all three frozen files. Retain the optional preflight failure; no claim it passed. Postmerge public V1 readback remains required.','actualPublicEvidence':'v1-current-public-readback.json'})
diff=command('final-diff-check',['git','diff','--check'])
baseline=read(OUT/'baseline-runtime.json')
changed=[p for p in sorted(set(before['files'])|set(baseline['files'])) if before['files'].get(p)!=baseline['files'].get(p)]
assert changed==['index.html','offline.html'],changed
write(OUT/'final-build-identity.json',{'base':BASE,'atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'build':build,'v1':v1,'diffCheck':diff,'before':before,'after':after,'deterministic':before==after,'changedRuntimePaths':changed,'unchangedRuntimeFiles':len(before['files'])-len(changed)})

paths=git('ls-tree','-r','--name-only',BASE).decode().splitlines()
interfaces=[p for p in paths if p in ['README.md','HANDOFF.md','AGENTS.md','_config.yml','config.js','builder.html','install.sh','install.ps1','tools/build_native.py','tools/build_moon.py','tools/native_core_horizon.py','src/native/config.js','src/native/builder.html'] or p.startswith(('presets/','v1/'))]
records=[]
for p in interfaces:
    old=git('show',BASE+':'+p);new=(ROOT/p).read_bytes()
    assert old==new,'Interface changed: '+p
    records.append({'path':p,'bytes':len(new),'sha256':sha(new),'equalToBase':True})
write(OUT/'docs/compatibility.json',{'schema':'r0018-docs/v1','base':BASE,'designSha256':sha((ROOT/'DESIGN.md').read_bytes()),'interfaces':records,'sourceOwnership':'src/native/index.html; canonical tools/build_native.py regenerates index.html and offline.html','policy':'Default information opacity 1; local .74 backing and quieter elapsed decoration; opaque NEXT/dark text and separate CURRENT preserved; optional contrast remains optional','card':'325x530 unchanged','productionWrapper':'330x534 unchanged and separate from native card; existing 325x530 builder/copy snippets unchanged','scope':'Only DESIGN requires a new readability claim. README, installers, calendar/weather/science documentation and interfaces are unchanged.'})

controls=[]
for rel,count in [('green-authored-contrast.json',15),('source-tests/r0018-appearance.cjs.stdout',17),('source-tests/r0018-appearance-mutations-r2.json',6)]:
    p=OUT/rel;r=read(p);entries=r.get('results',r.get('checks'))
    assert entries is not None and len(entries)==count,(rel,list(r),len(entries or []))
    assert all(x.get('status')=='PASS' for x in entries),(rel,entries)
    controls.append({'path':rel,'sha256':sha(p.read_bytes()),'passed':count,'kind':'source-consumer-controls'})
for rel,count in [('source-tests/r0018-prayer-row-status.test.cjs.stdout',27),('source-tests/real-sky-native-pinned-contrast.test.mjs.stdout',13)]:
    p=OUT/rel;text=p.read_text(encoding='utf-8')
    assert re.search(r'^# pass '+str(count)+r'\s*$',text,re.M) and re.search(r'^# fail 0\s*$',text,re.M),rel
    controls.append({'path':rel,'sha256':sha(p.read_bytes()),'passed':count,'kind':'node-tap'})
write(OUT/'source-tests/summary.json',{'passed':sum(x['passed'] for x in controls),'failed':0,'controls':controls,'retainedFailedAttempt':'r0018-appearance-mutations.cjs.stderr records old mutation seam after source correction. The corrected control enforces original default >=4.5; it does not grandfather historical failure.'})
modified=git('diff','--name-only').decode().splitlines()+git('ls-files','--others','--exclude-standard').decode().splitlines()
assert len(modified)==9,modified
write(OUT/'candidate-files.json',{'base':BASE,'headBeforeCommit':git('rev-parse','HEAD').decode().strip(),'files':[{'path':p,'bytes':(ROOT/p).stat().st_size,'sha256':sha((ROOT/p).read_bytes())} for p in sorted(modified)],'runtimeSha256':after['treeSha256'],'commit':'PENDING'})
print(json.dumps({'deterministicRuntime':after['treeSha256'],'unchangedRuntimeFiles':133,'sourceControls':78,'changedFiles':len(modified),'interfaces':len(records),'v1':'PASS'}))
