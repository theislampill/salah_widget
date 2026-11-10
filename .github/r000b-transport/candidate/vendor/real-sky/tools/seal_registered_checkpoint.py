#!/usr/bin/env python3
"""Immutable completed-7.3 archive, full fresh-extraction verification, external receipt.
This seals the requested 7.1–7.3 boundary, NOT the separately scoped whole CP7.6.
"""
import argparse,hashlib,json,os,re,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def files(root):
 return sorted(p for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ['.git','__pycache__','node_modules']) and p.name not in ['MANIFEST.sha256','hygdata_v40.csv'] and p.suffix.lower() not in ['.ttf','.otf','.woff','.woff2'])
def main():
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a.add_argument('--fresh',type=Path,required=True);args=a.parse_args();out=args.out.resolve();fresh=args.fresh.resolve();root=ROOT
 if out.exists() or fresh.exists():raise FileExistsError('Never overwrite a sealed archive or verification extraction')
 status=json.loads((root/'checkpoints/cp7_completion/status.json').read_text());assert all(v['status']=='PASS' for v in status['originalGates'].values())
 listed=files(root);manifest={p.relative_to(root).as_posix():sha(p) for p in listed};(root/'MANIFEST.sha256').write_text(''.join(h+'  '+n+'\n' for n,h in manifest.items()))
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in listed+[root/'MANIFEST.sha256']:
   zi=zipfile.ZipInfo('salah-real-sky/'+p.relative_to(root).as_posix(),(2026,10,5,0,0,0));zi.external_attr=0o100644<<16;zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,p.read_bytes())
 print('ARCHIVE_WRITTEN',out.name,flush=True)
 with zipfile.ZipFile(out) as z:
  assert z.testzip() is None;z.extractall(fresh)
 e=fresh/'salah-real-sky';assert all(sha(e/n)==h for n,h in manifest.items());print('CRC_MANIFEST_PASS',flush=True)
 evidence=out.parent/'Salah_Real_Sky_CP7_Completed_Verification_Evidence';evidence.mkdir(exist_ok=True)
 receipt={'archive':out.name,'bytes':out.stat().st_size,'sha256':sha(out),'stage':'7.3','originalGates':{'7.1':'PASS','7.2':'PASS','7.3':'PASS'},'checkpoint7Status':'OPEN: 7.4–7.6 remain separately scoped','manifestFiles':len(manifest),'zipMembers':len(manifest)+1,'parentArchive':status['parentArchive'],'parentSha256':status['parentSha256'],'sourceSha256':status['sourceSha256'],'githubWrites':0,'zipCRC':'PASS','freshExtractionManifest':'PASS','tests':{},'rebuilds':[]}
 def run(name,cmd,timeout=150,env=None):
  print('RUN',name,flush=True);p=subprocess.run(cmd,cwd=e,capture_output=True,text=True,timeout=timeout,env=env);text=p.stdout+p.stderr;(evidence/(name+'.log')).write_text(text)
  if p.returncode:raise RuntimeError(name+' failed: '+text[-3000:])
  return text
 for name,cmd,pattern in [('JavaScript',['node','tools/test.mjs'],r'# tests (\d+)'),('Python',[sys.executable,'-m','unittest','discover','-s','tests','-p','*_test.py'],r'Ran (\d+) tests')]:
  text=run(name,cmd);receipt['tests'][name]={'status':'PASS','count':int(re.search(pattern,text)[1]),'exitCode':0}
 for name,script in [('legacy-offline-rebuild','rebuild_cp7.py'),('admitted-source-offline-rebuild','rebuild_registered_starlight.py')]:
  run(name,[sys.executable,'tools/'+script]);receipt['rebuilds'].append({'name':name,'exitCode':0})
 changed=[n for n,h in manifest.items() if sha(e/n)!=h]
 if changed:raise RuntimeError('Rebuild changed manifest entries: '+repr(changed))
 receipt['offlineRebuildAllManifestFiles']='PASS';receipt['filesChangedByRebuild']=[];print('ALL_REBUILD_BYTES_IDENTICAL',flush=True)
 # Validation may write numerical reports. They must remain deterministic too.
 for name,cmd in [('actual-source-controls',[sys.executable,'tools/validate_registered_source.py']),('independent-registration',['node','tools/validate_registered_starlight.mjs']),('runtime-source-controls',['node','tools/validate_registered_runtime.mjs'])]:run(name,cmd)
 env=os.environ.copy();env['CP7_QA_OUTPUT']=str(evidence/'fresh-viewer');run('fresh-viewer',[sys.executable,'tools/registered_starlight_browser_qa.py'],env=env)
 b=json.loads((evidence/'fresh-viewer/browser-validation.json').read_text());receipt['extractedViewer']={'status':b['status'],'platform':b['platform'],'browser':b['browser'],'scenes':len(b['scenes']),'pageErrors':b['pageErrors'],'externalRequests':b['externalRequests'],'localFileNavigation':b['localFileNavigation']['status'],'viewerSha256':b['viewerSha256']}
 changed=[n for n,h in manifest.items() if sha(e/n)!=h]
 if changed:raise RuntimeError('Verification mutated manifest entries: '+repr(changed))
 receipt['postVerificationManifest']='PASS';receipt['status']='PASS';receipt['runtimeVersion']={'python':sys.version.split()[0],'node':subprocess.check_output(['node','--version'],text=True).strip()};receipt['evidenceDirectory']=evidence.name
 receipt_path=out.with_suffix('.verification.json');receipt_path.write_text(json.dumps(receipt,indent=2)+'\n');out.with_suffix('.sha256').write_text(receipt['sha256']+'  '+out.name+'\n');print(json.dumps(receipt,indent=2),flush=True)
if __name__=='__main__':main()
