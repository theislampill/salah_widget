"""Offline source binding check for the single headed host-wait control."""
from pathlib import Path
import ast,hashlib,json,subprocess
OUT=Path(__file__).resolve().parent;EV=OUT.parent;ROOT=EV.parent/'salah_widget'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
old=EV/'fixture-v3/run_r000c_native.py';new=ROOT/'tools/qa/run_r000c_native.py'
assert sha(old.read_bytes())=='ed610a2ce09ebdfce661b563338d0cf31f89162676b9f03de40544f59e350737'
assert sha(new.read_bytes())=='ef71a7d4fb7079b67de7a79dabbd43363577f2b3bf852fb24f8b323a784ee58e'
a,b=ast.parse(old.read_text(encoding='utf8')),ast.parse(new.read_text(encoding='utf8'))
def fn(t,n):return next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n)
def val(t,n):return next(x.value.value for x in t.body if isinstance(x,ast.Assign) and any(isinstance(y,ast.Name) and y.id==n for y in x.targets))
for name in ['check','wait','tile_png','sha','dump']:assert ast.dump(fn(a,name),include_attributes=False)==ast.dump(fn(b,name),include_attributes=False)
for name in ['READ','READY','RECOVERED_PASSIVE']:assert val(a,name)==val(b,name)
for name,digest in read(EV/'fixture-v3/manifest.json')['files'].items():assert sha((EV/'fixture-v3'/name).read_bytes())==digest
previous=read(EV/'fixture-v3/R000C-cases.json');current=read(ROOT/'tests/rlgwo/R000C-cases.json')
previous['sourceFiles']['tools/qa/run_r000c_native.py']=current['sourceFiles']['tools/qa/run_r000c_native.py'];assert previous==current
for path,digest in current['sourceFiles'].items():assert sha((ROOT/path).read_bytes())==digest
ref=subprocess.check_output(['git','--no-optional-locks','show','87c3a19ff275197e1a49bebd7abc30ad2849137e:tools/cp9/r0007_browser.py'],cwd=ROOT)
assert b'elif kind=="sleep":time.sleep(action["ms"]/1000)' in ref
pre=read(EV/'fixture-preflight/manifest.json')
assert sha((EV/'fixture-preflight/run_r000c_native.py').read_bytes())==pre['driverSha256']
assert sha((EV/'fixture-preflight/R000C-cases.json').read_bytes())==pre['casesSha256']
report={'schema':'r000c-independent-host-watch-delta/v1','priorDriverSha256':sha(old.read_bytes()),'successorDriverSha256':sha(new.read_bytes()),'successorPacketSha256':sha((ROOT/'tests/rlgwo/R000C-cases.json').read_bytes()),'priorVersionPreserved':True,'checkWaitReadReadyRecoveryUnchanged':True,'casePacketOnlyDriverPinChanged':True,'allSourcePinsMatch':True,'referenceDriverBlobSha256':sha(ref),'referenceHostSleepVerified':True,'preflightReconstructedBytesMatchManifest':True,'review':'Minimal two watch-wait substitutions inspected. One reduced-only headed/boundary-observer/host-wait acquisition is justified; no product, clock, readiness, retry, oracle, duration or recorder change. Outcome and causality remain unqualified.'}
(OUT/'host-watch-wait-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
