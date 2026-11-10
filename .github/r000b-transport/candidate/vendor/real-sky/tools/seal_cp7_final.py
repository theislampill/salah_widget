#!/usr/bin/env python3
"""Seal and independently verify cumulative CP7.5 or CP7.6; never write remotely.
Evidence is external to the immutable candidate: rebuild/tests cannot rewrite their own receipt.
"""
from pathlib import Path
import argparse,hashlib,json,platform,re,subprocess,sys,time,zipfile
R=Path(__file__).resolve().parents[1]
SOURCE_SHA='69f3c6ede4a730e0ca4699f5943fca59d0b203f37c4dfc4b7e6927f063250446'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def selected(root):
 out=[]
 for p in root.rglob('*'):
  rel=p.relative_to(root)
  if any(x in rel.parts for x in ['.git','__pycache__','node_modules']):continue
  if p.is_symlink():raise ValueError('Symlink is not a sealed payload: '+str(rel))
  if p.is_file() and p.name not in ['MANIFEST.sha256','hygdata_v40.csv'] and p.suffix.lower() not in ['.ttf','.otf','.woff','.woff2']:out.append(p)
 return sorted(out)
def verify_manifest(root,manifest):
 observed={p.relative_to(root).as_posix() for p in selected(root)}
 missing=sorted(set(manifest)-observed);extra=sorted(observed-set(manifest));changed=[n for n,h in manifest.items() if n in observed and sha(root/n)!=h]
 if missing or changed or extra:raise RuntimeError(json.dumps({'missing':missing,'changed':changed,'unlisted':extra}))
def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['7.5','7.6'],required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--fresh',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);p.add_argument('--parent-sha',required=True);a=p.parse_args()
 out=a.out.resolve();fresh=a.fresh.resolve();evidence=a.evidence.resolve();parent=a.parent.resolve()
 if out.exists() or fresh.exists():raise FileExistsError('Candidate ZIP and fresh directory must not exist')
 if sha(parent)!=a.parent_sha:raise RuntimeError('Parent archive hash mismatch')
 pre=json.loads((R/'checkpoints/cp75/worktree-validation.json').read_text());assert pre['status']=='PASS'
 if a.stage=='7.6':assert json.loads((R/'checkpoints/cp76/PREFLIGHT.json').read_text())['status']=='READY_FOR_INDEPENDENT_SEAL'
 evidence.mkdir(parents=True,exist_ok=True);start=time.monotonic();files=selected(R);manifest={p.relative_to(R).as_posix():sha(p) for p in files}
 (R/'MANIFEST.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in manifest.items()))
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for file in files+[R/'MANIFEST.sha256']:
   info=zipfile.ZipInfo('salah-real-sky/'+file.relative_to(R).as_posix(),(2026,10,5,0,0,0));info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,file.read_bytes(),compresslevel=6)
 print('ZIP_WRITTEN',out.name,flush=True)
 with zipfile.ZipFile(out) as z:
  assert z.testzip() is None;assert len(z.namelist())==len(manifest)+1;z.extractall(fresh)
 root=fresh/'salah-real-sky';verify_manifest(root,manifest)
 receipt={'stage':a.stage,'archive':out.name,'bytes':out.stat().st_size,'sha256':sha(out),'status':'VERIFYING','parentArchive':parent.name,'parentArchiveSha256':a.parent_sha,'sourceSha256':SOURCE_SHA,'manifestFiles':len(manifest),'zipMembers':len(manifest)+1,'zipCRC':'PASS','freshExtractionManifest':'PASS','githubWrites':0,'tests':{},'checks':[],'runtime':{'node':subprocess.check_output(['node','--version'],text=True).strip(),'python':sys.version.split()[0],'platform':platform.platform()}}
 receipt_path=out.with_suffix('.verification.json')
 def save():receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
 def run(name,cmd,timeout=900):
  print('RUN',name,flush=True);begin=time.monotonic()
  with (evidence/(name+'.log')).open('w') as f:r=subprocess.run(cmd,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
  text=(evidence/(name+'.log')).read_text();record={'name':name,'exitCode':r.returncode,'seconds':time.monotonic()-begin,'command':cmd}
  if r.returncode:raise RuntimeError(name+' failed:\n'+text[-3500:])
  receipt['checks'].append(record);save();return text,record
 try:
  for name,cmd,pattern in [('JavaScript',['node','tools/test.mjs'],r'# tests (\d+)'),('Python',[sys.executable,'-m','unittest','discover','-s','tests','-p','*_test.py'],r'Ran (\d+) tests')]:
   text,record=run(name,cmd);receipt['tests'][name]={'status':'PASS','count':int(re.search(pattern,text)[1]),**record};save()
  run('offline-cumulative-rebuild',[sys.executable,'tools/rebuild_cp75.py'],1500);verify_manifest(root,manifest);receipt['allFilesByteIdenticalAfterRebuild']='PASS';receipt['filesChangedByRebuild']=[];receipt['unlistedPayloadAfterRebuild']=[];save()
  run('parent-frame-parity',['node','--expose-gc','tools/cp75_benchmark.mjs','--compare='+str(root/'checkpoints/cp75/parent-benchmark.json'),'--out='+str(evidence/'parent-frame-parity.json')]);parity=json.loads((evidence/'parent-frame-parity.json').read_text());assert parity['exactParity'];receipt['parentFrameParity']={'status':'PASS','exactFixtures':len(parity['exactFixtures'])}
  run('physical-numerics',['node','tools/validate_cp74_numerics.mjs',str(evidence/'physical-numerics.json')]);receipt['physicalNumerics']=json.loads((evidence/'physical-numerics.json').read_text())
  run('diffuse-quality-matrix',['node','tools/validate_cp75_quality.mjs',str(evidence/'quality-and-matrix.json')]);d=json.loads((evidence/'quality-and-matrix.json').read_text());assert d['status']=='PASS';receipt['diffuseQuality']={'status':d['status'],'qualityComparisons':len(d['quality']),'observerSeasonProjectionCases':len(d['observerSeason']),'edgeCases':len(d['edges']),'dprComparisons':len(d['dpr']),'samplingSeams':len(d['samplingSeams'])}
  receipt['mutations']={}
  for stage in ['74','75']:
   run('cp'+stage+'-mutations',[sys.executable,'tools/cp'+stage+'_mutation_controls.py','--out',str(evidence/('cp'+stage+'-mutations'))]);m=json.loads((evidence/('cp'+stage+'-mutations/report.json')).read_text());assert m['status']=='PASS';receipt['mutations']['cp'+stage]={'status':'PASS','detected':m['detected']}
  viewer=root/'dist/accepted-physical-sky-viewer.html';receipt['viewer']={'sha256':sha(viewer),'bytes':viewer.stat().st_size,'sameBytesAsWorktree':sha(viewer)==sha(R/'dist/accepted-physical-sky-viewer.html'),'groups':[]}
  for group in (['smoke','fallback'] if a.stage=='7.5' else ['smoke','controls','scenes','wide','fallback']):
   run('extracted-viewer-'+group,[sys.executable,'tools/cp75_browser_qa.py','--group',group,'--html',str(viewer),'--out',str(evidence/('browser-'+group))]);b=json.loads((evidence/('browser-'+group+'/report.json')).read_text());assert b['status']=='PASS' and b['htmlSha256']==sha(viewer);receipt['viewer']['groups'].append({'group':group,'status':'PASS','scenes':len(b['scenes']),'controls':len(b['controls']),'browserVersion':b['browserVersion'],'platform':b['platform'],'pageErrors':b['pageErrors'],'externalRequests':b['externalRequests']});save()
  run('browser-platform-and-file-policy',[sys.executable,'tools/cp75_platform_probe.py','--out',str(evidence/'platform.json')]);receipt['browserScope']=json.loads((evidence/'platform.json').read_text())
  run('cp6-compatibility-viewer',[sys.executable,'tools/cp74_compatibility_smoke.py','--out',str(evidence/'compatibility-viewer.json')]);receipt['compatibilityViewer']=json.loads((evidence/'compatibility-viewer.json').read_text())
  verify_manifest(root,manifest);assert sha(out)==receipt['sha256'];receipt['postVerificationManifest']='PASS';receipt['status']='PASS';receipt['seconds']=time.monotonic()-start
  receipt['boundaries']=['CP7 reference implementation sealed; actual-widget CP8 and joined CP9 remain separate','Neutral V-equivalent direct integrated starlight, with retained estimated-support masks; not measured full RGB spectra','Assumed within-V SED and non-stellar residual; no full diffuse in-/multiple-scattering solution','CPU reference rendering is not real-time animation; a worker preserves UI responsiveness, not frame-rate throughput','Native Windows/Firefox and WebKit untested; file navigation policy is separately recorded']
  save();out.with_suffix('.sha256').write_text(receipt['sha256']+'  '+out.name+'\n');print('SEALED_PASS',out.name,receipt['sha256'],flush=True)
 except BaseException as e:receipt['status']='FAIL';receipt['error']=str(e);save();raise
if __name__=='__main__':main()
