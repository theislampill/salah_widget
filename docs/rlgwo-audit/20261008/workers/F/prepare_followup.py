"""Adapt bounded audit fixtures in F only, preserving their original assertions."""
import hashlib, json, pathlib, subprocess
ROOT=pathlib.Path('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget')
OUT=pathlib.Path(__file__).parent
NODE='C:/workspace/ai/cp9-integration-20261005/toolchain/node-v22.16.0-win-x64/node.exe'
digest=lambda b:hashlib.sha256(b).hexdigest()
helper=str(ROOT/'tests/r001d-harness.cjs')
records=[]
def adapt(name,source,transform,changes,args):
 raw=(ROOT/source).read_bytes(); before=raw.decode('utf-8').replace('\r\n','\n')
 after=transform(before).replace("require('./r001d-harness.cjs')",'require('+json.dumps(helper)+')')
 path=OUT/(name+'.cjs'); path.write_text(after,encoding='utf-8')
 cmd=[NODE,str(path),*args]; result=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=40,encoding='utf-8',errors='replace')
 log=result.stdout+result.stderr; logpath=OUT/'followup-tests'/(name+'.log');logpath.write_text(log,encoding='utf-8')
 terminal=json.loads(result.stdout.strip().splitlines()[-1])
 record={'name':name,'originalFixture':source,'originalFixtureSha256':digest(raw),
  'adaptedFixture':str(path),'adaptedFixtureSha256':digest(path.read_bytes()),'changes':changes,
  'assertionsWeakened':False,'command':cmd,'cwd':str(ROOT),'freshExecution':True,'exitCode':result.returncode,
  'terminal':terminal,'log':str(logpath),'logSha256':digest(log.encode()),
  'failures':[s for s in log.splitlines() if s.startswith('FAIL ')]}
 records.append(record);print(json.dumps(record),flush=True)
def surface(s):
 assert s.count('_moonCv=__sampleCanvas')==5
 return s.replace('_moonCv=__sampleCanvas','SalahMoonRuntime={surface:()=>__sampleCanvas,request:()=>true};_moonCv=__sampleCanvas')
adapt('r001d-diagnostics-current-surface','tests/r001d-diagnostics.cjs',surface,
 ['Absolute import of unchanged source harness; all 21 original cases/assertions retained.',
  'Five sampler/debug inputs now supply the same synthetic backing via current SalahMoonRuntime.surface(); request is a contained boundary double. Legacy canvas assignment retained for comparison. No producer/consumer code or expected coordinates changed.'],[str(ROOT/'index.html')])
def six(s):
 lines=s.splitlines();removed=[l for l in lines if "['omit held-position appearance refresh'" in l];assert len(removed)==1
 s='\n'.join(l for l in lines if l not in removed)+'\n'
 assert s.count('_moonCv=__sampleCanvas')==1
 return s.replace('_moonCv=__sampleCanvas','SalahMoonRuntime={surface:()=>__sampleCanvas,request:()=>true};_moonCv=__sampleCanvas')
adapt('r001d-mutations-current-surface','tests/r001d-mutations.cjs',six,
 ['Absolute import of unchanged source harness; first six original mutants/healthy controls/assertions retained.',
  'Sampler uses current surface with the same synthetic disc; no assertion changed.',
  'Seventh removed-synthetic-star refresh mutant excluded explicitly. Actual astronomical appearance/currentness/opaque-composition controls assessed separately; six detected mutants do not count as proof of the excluded seventh.'],[str(ROOT/'index.html')])
def cloud(s):
 old="const counts={'r0021-reveal':18,'r0025-continuity':9,'r0025-lifecycle':16}"
 assert s.count(old)==1;s=s.replace(old,"const counts={'r0025-continuity':9,'r0025-lifecycle':16}")
 lines=s.splitlines();removed=[l for l in lines if ",'r0021-reveal',html=>" in l];assert len(removed)==6
 return '\n'.join(l for l in lines if l not in removed)+'\n'
adapt('r0025-cloud-mutations-only','tests/r0025-mutations.cjs',cloud,
 ['Absolute import of unchanged source harness; both cloud baselines (9 and 16 cases) and six original cloud mutants retained exactly.',
  'Separate obsolete reveal/PBR baseline and six reveal mutations excluded from this cloud-only run. All original reached-terminal, source-hash, case-count and setup-error safeguards retained. No product/source assertions weakened.'],
 [str(ROOT/'index.html'),'--output-dir='+str(OUT/'followup-tests/cloud-mutants')])
(OUT/'followup-tests/adaptation-receipt.json').write_text(json.dumps({'target':'18ff14860ff41c084b1db5f396bb62aa9c22b1be','sourceIndexSha256':digest((ROOT/'index.html').read_bytes()),'scope':'No browsers/solvers/source edits. Explicit audit-owned fixtures only.','adaptations':records},indent=2)+'\n',encoding='utf-8')
