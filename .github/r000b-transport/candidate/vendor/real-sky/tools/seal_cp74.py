#!/usr/bin/env python3
"""Seal cumulative CP7.4 and verify the extracted archive, without remote writes."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,sys,time,zipfile
R=Path(__file__).resolve().parents[1]
PARENT_SHA='b54ac210ef46f7728eaff41d910b7ae51676dce3746b6d9498020dbbf950e4c8'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def selected(root):
 return sorted(p for p in root.rglob('*') if p.is_file() and not any(k in p.parts for k in ['.git','__pycache__','node_modules']) and p.name not in ['MANIFEST.sha256','hygdata_v40.csv'] and p.suffix.lower() not in ['.ttf','.otf','.woff','.woff2'])
def verify_manifest(root,manifest):
 missing=[n for n in manifest if not (root/n).is_file()]
 changed=[n for n,h in manifest.items() if (root/n).is_file() and sha(root/n)!=h]
 if missing or changed:raise RuntimeError(json.dumps({'missing':missing,'changed':changed}))
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--fresh',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();out=a.out.resolve();fresh=a.fresh.resolve();evidence=a.evidence.resolve()
 if out.exists() or fresh.exists():raise FileExistsError('Archive and fresh destination must not exist')
 pre=json.loads((R/'checkpoints/cp74/worktree-validation.json').read_text());assert pre['status']=='PASS'
 evidence.mkdir(parents=True,exist_ok=True);start=time.monotonic()
 files=selected(R);manifest={p.relative_to(R).as_posix():sha(p) for p in files}
 (R/'MANIFEST.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in manifest.items()))
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files+[R/'MANIFEST.sha256']:
   info=zipfile.ZipInfo('salah-real-sky/'+p.relative_to(R).as_posix(),(2026,10,5,0,0,0));info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes(),compresslevel=6)
 print('ZIP_WRITTEN',out.name,flush=True)
 with zipfile.ZipFile(out) as z:
  assert z.testzip() is None;assert len(z.namelist())==len(manifest)+1
  z.extractall(fresh)
 root=fresh/'salah-real-sky';verify_manifest(root,manifest)
 receipt={'stage':'7.4','archive':out.name,'bytes':out.stat().st_size,'sha256':sha(out),'status':'VERIFYING','parentArchiveSha256':PARENT_SHA,'sourceSha256':'69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446','manifestFiles':len(manifest),'zipMembers':len(manifest)+1,'zipCRC':'PASS','freshExtractionManifest':'PASS','githubWrites':0,'tests':{},'rebuilds':[],'runtime':{'node':subprocess.check_output(['node','--version'],text=True).strip(),'python':sys.version.split()[0]}}
 receipt_path=out.with_suffix('.verification.json')
 def save():receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
 def run(name,cmd,timeout=300):
  print('RUN',name,flush=True);begin=time.monotonic()
  with (evidence/(name+'.log')).open('w') as f:result=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  text=(evidence/(name+'.log')).read_text();record={'name':name,'exitCode':result.returncode,'seconds':time.monotonic()-begin}
  if result.returncode:raise RuntimeError(name+' failed:\n'+text[-3000:])
  return text,record
 try:
  for name,cmd,pattern in [('JavaScript',['node','tools/test.mjs'],r'# tests (\d+)'),('Python',[sys.executable,'-m','unittest','discover','-s','tests','-p','*_test.py'],r'Ran (\d+) tests')]:
   text,record=run(name,cmd);receipt['tests'][name]={'status':'PASS','count':int(re.search(pattern,text)[1]),**record};save()
  _,record=run('offline-cumulative-rebuild',[sys.executable,'tools/rebuild_cp74.py'],1200);receipt['rebuilds'].append(record);verify_manifest(root,manifest);receipt['allFilesByteIdenticalAfterRebuild']='PASS';receipt['filesChangedByRebuild']=[];save()
  _,record=run('numeric-reference-controls',['node','tools/validate_cp74_numerics.mjs',str(evidence/'numeric-reference-controls.json')]);receipt['numericControls']=record
  _,record=run('mutation-controls',[sys.executable,'tools/cp74_mutation_controls.py','--out',str(evidence/'mutations')]);receipt['mutationControls']={'detected':json.loads((evidence/'mutations/report.json').read_text())['detected'],**record};save()
  _,record=run('extracted-physical-viewer',[sys.executable,'tools/cp74_browser_qa.py','--smoke','--out',str(evidence/'physical-viewer')],180)
  report=json.loads((evidence/'physical-viewer/browser-report.json').read_text());work=json.loads((root/'checkpoints/cp74/browser/browser-report.json').read_text());viewer=root/'dist/physical-diffuse-sky-viewer.html'
  receipt['extractedViewer']={'status':'PASS','sha256':sha(viewer),'bytes':viewer.stat().st_size,'browser':report['browserVersion'],'platform':report['platform'],'pageErrors':report['pageErrors'],'externalRequests':report['externalRequests'],'sealedSmokeScenes':len(report['scenes']),'sameBytesAsWorktreeViewer':sha(viewer)==sha(R/'dist/physical-diffuse-sky-viewer.html'),'worktreeSceneRenders':len(work['scenes']),'worktreeControlGroups':len(work['controls'])};save()
  # Independently exercise the regenerated CP6 compatibility viewer and attempt
  # local file navigation. Failure by browser policy is reported, never hidden.
  _,record=run('compatibility-and-local-file-viewers',[sys.executable,'tools/cp74_compatibility_smoke.py','--out',str(evidence/'compatibility-viewer.json')],180);receipt['compatibilityViewer']=json.loads((evidence/'compatibility-viewer.json').read_text())
  verify_manifest(root,manifest);receipt['postVerificationManifest']='PASS';receipt['status']='PASS';receipt['seconds']=time.monotonic()-start;receipt['boundaries']=['Full CP7.5/7.6 and actual-widget CP8 remain separate','Neutral V-equivalent direct component; assumed within-band SED and non-stellar residual','No independent diffuse in-scattering solution or native Windows/Firefox certification'];save()
  out.with_suffix('.sha256').write_text(receipt['sha256']+'  '+out.name+'\n');print(json.dumps(receipt,indent=2),flush=True)
 except BaseException as e:
  receipt['status']='FAIL';receipt['error']=str(e);save();raise
if __name__=='__main__':main()
