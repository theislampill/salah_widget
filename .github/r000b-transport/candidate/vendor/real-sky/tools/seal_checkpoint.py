#!/usr/bin/env python3
"""Seal a cumulative snapshot, reopen it, verify every member, then run its tests.
No source/runtime network access. Does not include carrier binaries, fonts or uncompressed source duplicates.
"""
import argparse,hashlib,json,zipfile,tempfile,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('checkpoint',type=int);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--out',type=Path,default=Path('/mnt/data'));a=p.parse_args();r=a.root
 files=sorted(f for f in r.rglob('*') if f.is_file() and '.git' not in f.parts and '__pycache__' not in f.parts and f.name!='MANIFEST.sha256' and f.name!='hygdata_v40.csv')
 manifest=''.join(f'{sha(f.read_bytes())}  {f.relative_to(r).as_posix()}\n' for f in files)
 (r/'MANIFEST.sha256').write_text(manifest);files.append(r/'MANIFEST.sha256')
 out=a.out/f'Salah_Real_Sky_Checkpoint_{a.checkpoint}.zip';a.out.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for f in sorted(files):
   zi=zipfile.ZipInfo('salah-real-sky/'+f.relative_to(r).as_posix(),date_time=(2026,10,4,0,0,0));zi.external_attr=0o100644<<16;zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,f.read_bytes())
 with tempfile.TemporaryDirectory(prefix='real-sky-reopen-') as d:
  with zipfile.ZipFile(out) as z:
   if z.testzip():raise RuntimeError('ZIP CRC failure')
   z.extractall(d)
  e=Path(d)/'salah-real-sky'
  for line in (e/'MANIFEST.sha256').read_text().splitlines():
   h,n=line.split('  ',1)
   if sha((e/n).read_bytes())!=h:raise RuntimeError('Reopen mismatch: '+n)
  runs={}
  for name,cmd in [('node',['node','tools/test.mjs']),('python',[sys.executable,'-m','unittest','discover','-s','tests','-p','*_test.py'])]:
   c=subprocess.run(cmd,cwd=e,text=True,capture_output=True,timeout=90);runs[name]={'exitCode':c.returncode,'tail':(c.stdout+c.stderr)[-1800:]}
   if c.returncode:raise RuntimeError(name+' failed on extracted ZIP\n'+c.stdout+c.stderr)
  # Deterministic generated files must reproduce, not merely survive packaging.
  before={str(f.relative_to(e)):sha(f.read_bytes()) for f in (e/'data').glob('*.json')}
  cmd=[sys.executable,'tools/rebuild.py'] if (e/'tools/rebuild.py').exists() else [sys.executable,'tools/build_authenticated_catalogue.py']
  c=subprocess.run(cmd,cwd=e,text=True,capture_output=True,timeout=90)
  if c.returncode:raise RuntimeError('Rebuild failed: '+c.stdout+c.stderr)
  after={str(f.relative_to(e)):sha(f.read_bytes()) for f in (e/'data').glob('*.json')}
  if before!=after:raise RuntimeError('Rebuild not deterministic: '+repr([n for n in before if before[n]!=after.get(n)]))
 receipt={'checkpoint':a.checkpoint,'archive':out.name,'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'members':len(files),'manifestMembers':len(files)-1,'freshExtraction':'PASS','CRC':'PASS','manifest':'PASS','deterministicDataRebuild':'PASS','testsFromExtractedArchive':runs,'githubWrites':0}
 out.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');out.with_suffix('.sha256').write_text(receipt['sha256']+'  '+out.name+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
