from pathlib import Path
import hashlib, json, shutil, subprocess, sys
R = Path(r'${REPO_ROOT}')
O = Path(__file__).resolve().parent
sys.path.insert(0, str(R/'tools/cp9'))
from runtime_identity import runtime_identity
parent = '9df79b98d8dda7a0286b1b287dc03d1b4d760bdb'
git = ['git', '-c', 'maintenance.auto=false', '-c', 'gc.auto=0']
assert subprocess.check_output(git+['rev-parse','HEAD'],cwd=R,text=True).strip()==parent
before = json.loads((O/'builds/integrated-r28-retention/RUNTIME.json').read_bytes())
assert runtime_identity(R)==before, 'Unexpected pre-build runtime delta'
protected = ['v1','src/native','real-sky','moon/src','moon/assets','moon/moon_kernel.wasm','moon/asset-manifest.json','moon/initial-manifest.json','moon/initial-source-association.json']
changed = subprocess.check_output(git+['diff','--name-only',parent,'--',*protected],cwd=R,text=True).splitlines()
assert changed==['moon/src/moon-quality.mjs'], changed
records=[]
for n in [1,2]:
    p=subprocess.run([sys.executable,'-B','tools/build_native.py'],cwd=R,capture_output=True)
    (O/f'intake/moon-rule-r115-build{n}.log').write_bytes(p.stdout+p.stderr)
    assert p.returncode==0
    records.append(runtime_identity(R))
assert records[0]==records[1], 'Canonical builds differ'
runtime=records[1]
changedRuntime=[p for p in runtime['files'] if runtime['files'][p]!=before['files'][p]]
assert set(changedRuntime)=={'index.html','offline.html','moon/BUILD.json','moon/moon-host.js','moon/moon-worker.js'}, changedRuntime
dest=O/'builds/integrated-r29-lunar-rule'
assert not dest.exists()
for name in runtime['files']:
    target=dest/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,target)
assert runtime_identity(dest)==runtime
(dest/'RUNTIME.json').write_bytes((json.dumps(runtime,indent=2)+'\n').encode())
receipt={'schema':'r0021-lunar-rule-build/v1','sourceParent':parent,'runtime':runtime['treeSha256'],'fileCount':len(runtime['files']),'twoBuildsIdentical':True,'frozenCopyVerified':True,'changedRuntime':changedRuntime,'protectedPaths':protected,'onlyProtectedSourceDelta':'moon/src/moon-quality.mjs','unchangedRuntimeEntries':len(runtime['files'])-len(changedRuntime),'source':{p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ['moon/src/moon-quality.mjs','moon/tests/quality.test.cjs','moon/src/moon-engine.mjs','moon/src/moon_kernel.c','moon/moon_kernel.wasm','tools/build_native.py','tools/build_moon.py']}}
(O/'intake/moon-rule-r115-build.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
print(json.dumps(receipt))
