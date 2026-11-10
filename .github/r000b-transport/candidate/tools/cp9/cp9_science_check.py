#!/usr/bin/env python3
"""Re-execute retained independent oracle fixtures without changing the scientific snapshot."""
from pathlib import Path
import argparse,subprocess,shutil,tempfile,json
ROOT=Path(__file__).resolve().parents[2]
def run(root,out):
 out.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='cp9-oracle-') as directory:
  t=Path(directory);s=root/'vendor/real-sky'
  for d in ['src','tests/fixtures']:shutil.copytree(s/d,t/d)
  for d in ['data','tools','checkpoints/cp6']:(t/d).mkdir(parents=True,exist_ok=True)
  for file in ['tools/validate_cp4.mjs','tools/validate_cp6.mjs','data/catalogue-v6_5.json']:shutil.copy2(s/file,t/file)
  rows=[]
  for name,cmd in [('astrometry',['node','tools/validate_cp4.mjs',str((out/'astrometry.json').resolve())]),('illumination',['node','tools/validate_cp6.mjs'])]:
   with (out/(name+'.log')).open('w') as f:p=subprocess.run(cmd,cwd=t,stdout=f,stderr=subprocess.STDOUT,timeout=120)
   rows.append({'name':name,'exitCode':p.returncode})
  if (t/'checkpoints/cp6/illumination-validation.json').exists():shutil.copy2(t/'checkpoints/cp6/illumination-validation.json',out/'illumination.json')
 result={'status':'PASS' if all(x['exitCode']==0 for x in rows) else 'FAIL','commands':rows,'scope':'Retained matched-UT1/TT/vacuum astrometry and separate low-order Sun/Moon fixture comparisons. Not newly acquired ephemerides, live conditions or observer-device calibration.'};(out/'results.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=ROOT);a.add_argument('--output',type=Path,required=True);x=a.parse_args();raise SystemExit(0 if run(x.root,x.output)['status']=='PASS' else 1)
