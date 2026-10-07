"""Sequential affected checks after the requested CP9 horizon correction."""
from pathlib import Path
import sys,os,json,subprocess,time,hashlib
E=Path(__file__).resolve().parent;O=E/'post-horizon';O.mkdir(exist_ok=True)
R=Path(r'C:\Users\theis\.codex\worktrees\cp9-moon-v5-integration\salah_widget')
P=r'C:\workspace\ai\cp9-integration-20261005\venv\Scripts\python.exe'
sys.path.insert(0,str(R/'tools/cp9'));from runtime_identity import runtime_identity
os.environ.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',SALAH_BROWSER='chromium',SALAH_BROWSER_EXECUTABLE=r'C:\Users\theis\AppData\Local\ms-playwright\chromium-1223\chrome-win64\chrome.exe')
before=runtime_identity(R);(O/'runtime-identity.json').write_text(json.dumps(before,indent=2)+'\n')
records=[]
def check(name,cmd,expected=0):
    start=time.monotonic()
    with (O/(name+'.log')).open('wb') as f:r=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
    record=dict(name=name,command=cmd,exitCode=r.returncode,expectedExit=expected,seconds=time.monotonic()-start,runtimeUnchanged=runtime_identity(R)==before)
    records.append(record);(O/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
    print(name,r.returncode,round(record['seconds'],2),flush=True)
    assert r.returncode==expected and record['runtimeUnchanged'],record
old=json.loads((E/'final-checks/commands.json').read_text())
for v in old:
    if v['name']=='verify-installed':continue
    cmd=[s.replace(str(E/'final-checks'),str(O)) for s in v['command']]
    if v['name']=='integration':cmd.append(str(R/'tests/real-sky/native-horizon.test.mjs'))
    check(v['name'],cmd)
check('horizon-build-guard',[sys.executable,'-B','tests/real-sky/native_horizon_build_test.py'])
pin=json.loads((E/'Salah_Moon_CP9_Integration/INSTALL.json').read_text())
expected={**pin['preimages'],**pin['payload'],**pin['outputs']}
drift={p:{'donorSha256':s,'currentSha256':hashlib.sha256((R/p).read_bytes()).hexdigest()} for p,s in expected.items() if hashlib.sha256((R/p).read_bytes()).hexdigest()!=s}
assert set(drift)=={'tools/build_native.py','real-sky/core/src/physical-sky-renderer.mjs','real-sky/native-worker.js','real-sky/native-sky.js','offline.html'},drift
(O/'post-donor-delta.json').write_text(json.dumps({'scope':'Initial guarded apply and original 189 postimages passed before this separately requested horizon fix. These five deliberate postimage differences are generated from the authored correction; no installer guard was bypassed.','files':drift},indent=2)+'\n')
check('original-postimage-expected-drift',[sys.executable,'-B',str(E/'Salah_Moon_CP9_Integration/install.py'),'--repo',str(R),'--verify-installed'],1)
check('horizon-browser',[P,'-B','tools/cp9/horizon_browser_check.py','--root',str(R),'--parent',r'C:\Users\theis\.codex\worktrees\cp9-real-sky-integration\salah_widget','--output',str(O/'horizon-browser')])
for name,tool in [('cp9-composition','native_composition_check'),('cp9-material','native_material_check'),('cp9-presentation','cp9_presentation_check'),('cp9-controls','cp9_native_controls'),('native-smoke','native_smoke_check'),('cp9-lifecycle','native_lifecycle_check')]:
    check(name,[P,'-B','tools/cp9/'+tool+'.py','--root',str(R),'--output',str(O/name)])
for name,entry in [('moon-http','http'),('moon-file','file-offline')]:
    check(name,[P,'-B','tools/cp9/moon_receiving_check.py','--root',str(R),'--output',str(O/name),'--entry',entry,'--no-phase-series'])
print('POST_HORIZON_CHECKS_PASS',flush=True)
