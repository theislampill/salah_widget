from pathlib import Path
import hashlib,json,shutil,subprocess,sys
O=Path(__file__).resolve().parent
R=Path(r'${REPO_ROOT}')
B=O/'builds/integrated-r31-file-transport'
sys.path.insert(0,str(B/'tools/cp9'))
from runtime_identity import runtime_identity
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
first=runtime_identity(B)
assert len(first['files'])==142
(B/'RUNTIME-FIRST.json').write_text(json.dumps(first,indent=2)+'\n')
run=subprocess.run([sys.executable,'-B',str(B/'tools/build_native.py')],cwd=B,capture_output=True,text=True,timeout=180)
(B/'BUILD-SECOND-LOG.txt').write_text(run.stdout+run.stderr)
assert run.returncode==0,run.stderr
second=runtime_identity(B)
assert first==second
(B/'RUNTIME.json').write_text(json.dumps(second,indent=2)+'\n')
old=json.loads((O/'builds/integrated-r30-owner-callbacks/RUNTIME.json').read_bytes())
changed=[p for p,v in second['files'].items() if v!=old['files'][p]]
assert all(p in ['index.html','offline.html','moon/moon-host.js','moon/BUILD.json'] or p.startswith('moon/file-data/') for p in changed),changed
authored=['moon/src/moon-native.mjs','tools/build_moon.py','moon/tests/host.test.cjs']
assert all(sha(R/p)==sha(B/p) for p in authored)
for p in changed:shutil.copyfile(B/p,R/p)
assert runtime_identity(R)==second
protected={}
for rel in ['moon/assets','v1','vendor/real-sky']:
 for p in (B/rel).rglob('*'):
  if p.is_file():
   rp=p.relative_to(B).as_posix();assert sha(p)==sha(R/rp);protected[rp]=sha(p)
for rel in ['moon/moon_kernel.wasm','moon/src/surface_v5.mjs','moon/src/moon-quality.mjs','moon/src/moon-worker.mjs','src/native/index.html']:
 assert sha(B/rel)==sha(R/rel);protected[rel]=sha(B/rel)
record={'schema':'r0021-file-transport-build/v1','parent':'4afeeb30d0415dbd6008e84d3fb80248e8ddef95','runtime':second['treeSha256'],'runtimeFiles':142,'twoCanonicalBuildsIdentical':True,'changedRuntimePaths':changed,'unchangedRuntimeFiles':142-len(changed),'authoredSha256':{p:sha(R/p) for p in authored},'protectedSha256':protected}
(O/'intake/file-transport-r127-build.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ['protectedSha256','authoredSha256','changedRuntimePaths']}))
prior=O/'run_recovery_r121_r122.py';source=prior.read_text()
replacements=[("integrated-r30-owner-callbacks","integrated-r31-file-transport"),("'file-atob-r122'","'file-atob-r127'"),('3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821',second['treeSha256']),('fault=sys.argv[1];dest=',"fault=sys.argv[1];assert fault=='file-atob','r127 covers only the affected file decoder';dest=")]
for before,after in replacements:
 assert source.count(before)==1,(before,source.count(before));source=source.replace(before,after)
target=O/'run_file_atob_r127.py';assert not target.exists();target.write_text(source,encoding='utf-8',newline='\n')
(O/'intake/file-transport-r127-runner-transfer.json').write_text(json.dumps({'priorRunnerSha256':sha(prior),'currentRunnerSha256':sha(target),'changes':replacements,'harnessChanged':False,'measurementSemanticsChanged':False},indent=2)+'\n')
