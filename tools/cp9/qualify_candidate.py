"""Run CP9 observations serially and bind every command to unchanged runtime bytes.

Use explicit browser environment variables; CPU controls require Chromium.
This executes evidence work, never closes a DAG node or publishes a release.
"""
import argparse,json,subprocess,sys,time
from pathlib import Path
from runtime_identity import ROOT,runtime_identity
COMMANDS={
 'integration':['node','--test','--test-reporter=tap','--test-concurrency=1','tests/real-sky/*.test.mjs'],
 'collector':[sys.executable,'tests/real-sky/platform_acceptance_test.py'],
 'native':[sys.executable,'tools/cp9/run_native_regressions.py'],
 'science':[sys.executable,'tools/cp9/run_scientific_regressions.py'],
 'oracles':[sys.executable,'tools/cp9/cp9_science_check.py'],
 'scenes':[sys.executable,'tools/cp9/native_browser_check.py','--scenes','tests/real-sky/native-scenes-82.json'],
 'seasonal':[sys.executable,'tools/cp9/cp9_seasonal_check.py'],
 'lifecycle':[sys.executable,'tools/cp9/native_lifecycle_check.py','--group','all'],
 'mutations':[sys.executable,'tools/cp9/native_lifecycle_mutations.py'],
 'native-controls':[sys.executable,'tools/cp9/cp9_native_controls.py'],
 'controls':[sys.executable,'tools/cp9/native_controls_check.py'],
 'material':[sys.executable,'tools/cp9/native_material_check.py'],
 'composition':[sys.executable,'tools/cp9/native_composition_check.py'],
 'presentation':[sys.executable,'tools/cp9/cp9_presentation_check.py'],
 'motion':[sys.executable,'tools/cp9/native_motion_check.py'],
 'live-watch':[sys.executable,'tools/cp9/native_live_watch.py'],
 'memory':[sys.executable,'tools/cp9/cp9_memory_check.py'],
 'profile':[sys.executable,'tools/cp9/cp9_profile.py'],
 'performance':[sys.executable,'tools/cp9/cp9_performance.py','--trials','5'],
 'rates':[sys.executable,'tools/cp9/cp9_temporal_rates.py'],
 'responsiveness':[sys.executable,'tools/cp9/cp9_responsiveness.py'],
 'smoke':[sys.executable,'tools/cp9/native_smoke_check.py'],
 'platform':[sys.executable,'tools/cp9/platform_widget_check.py'],
}
def run(root,out,groups):
 out=out.resolve();out.mkdir(parents=True,exist_ok=True);before=runtime_identity(root);rows=[]
 for name in groups:
  cmd=COMMANDS[name].copy()
  if name=='integration':cmd=cmd[:-1]+[str(p.relative_to(root)) for p in sorted((root/'tests/real-sky').glob('*.test.mjs'))]
  elif name!='collector':cmd+=['--output',str(out/name)]
  start=time.monotonic()
  with (out/(name+'.log')).open('w',encoding='utf-8') as f:
   try:code=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=1200).returncode
   except subprocess.TimeoutExpired:code=124
  unchanged=runtime_identity(root)==before
  row={'name':name,'command':cmd,'exitCode':code,'runtimeTreeSha256':before['treeSha256'],'runtimeUnchanged':unchanged,'seconds':time.monotonic()-start};rows.append(row)
  (out/'command-receipts.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(name,code,round(row['seconds'],2),flush=True)
  if not unchanged:raise RuntimeError('Runtime changed during qualification; do not bind subsequent observations')
 (out/'runtime-identity.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--output',type=Path,required=True);p.add_argument('--groups',nargs='+',choices=COMMANDS,required=True);a=p.parse_args();rows=run(a.root,a.output,a.groups);sys.exit(1 if any(r['exitCode'] for r in rows) else 2)
