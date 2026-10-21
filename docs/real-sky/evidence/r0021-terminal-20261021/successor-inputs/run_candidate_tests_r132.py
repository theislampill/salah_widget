"""Final-source regression: reuse the canonical serial suite and retained affected controls."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
O=Path(__file__).resolve().parent;R=Path(r'${REPO_ROOT}');OUT=O/'intake/candidate-tests-r132';OUT.mkdir()
node=Path(r'${QA_TOOLCHAIN}\toolchain\node-v22.16.0-win-x64\node.exe')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted(p for p in(R/'tests').rglob('*')if p.name.endswith(('.test.mjs','.test.cjs','.test.js')))
lock=O/'native-resource.lock'
with lock.open('x')as f:f.write(OUT.name)
sys.path.insert(0,str(R/'tools/cp9'));from runtime_identity import runtime_identity
identity=runtime_identity(R);assert identity['treeSha256']=='1b6586d8921a99780b2cefff95821ad90bf39571ef074ccffe4234ec8aa7f02b'
report={'scope':__doc__,'startedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':identity,'testFiles':[{'path':p.relative_to(R).as_posix(),'sha256':sha(p)}for p in files],'commands':[],'acceptedAffectedTransfer':'r127 exact unchanged source: 58host tests,8build guards,2assets; two matching canonical builds. No duplicate lunar numerical/native campaign.'}
try:
 commands=[('canonical-node',[str(node),'--test','--test-concurrency=1',*[str(p)for p in files]]),('head-handoff',[str(node),str(R/'tests/real-sky/native-head-handoff.cjs')]),('frozen-v1',[sys.executable,'-I','-S','-B',str(R/'tools/verify_v1.py')]),('native-entry-order',[sys.executable,'-I','-S','-B',str(R/'tests/real-sky/native_entry_order_test.py')])]
 for name,cmd in commands:
  path=OUT/(name+'.txt')
  with path.open('xb')as f:r=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=180)
  report['commands'].append({'name':name,'command':cmd,'exitCode':r.returncode,'log':path.name,'sha256':sha(path)})
  print(json.dumps({'name':name,'exitCode':r.returncode,'tail':path.read_text(encoding='utf-8').splitlines()[-10:]}),flush=True)
  if r.returncode:raise RuntimeError(name+' failed')
 report['status']='RETURNED'
except Exception as e:report.update(status='FAILED',error=repr(e))
finally:
 report['runtimeUnchanged']=runtime_identity(R)==identity
 report['finishedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(OUT/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');assert lock.read_text()==OUT.name;lock.unlink()
print(json.dumps({'status':report['status'],'testFiles':len(files)}))
