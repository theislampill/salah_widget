"""Project R0006 originals into a public, hash-bound packet without changing them."""
import gzip,hashlib,json,lzma,shutil
from pathlib import Path
HERE=Path(__file__).parent
ROOT=HERE.parent/'salah_widget'
DEST=ROOT/'docs/rlgwo-execution/20261014/R0006'
def sha(data):return hashlib.sha256(data).hexdigest()
def dump(p,value):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def put(src,dst):
 data=src.read_bytes();dst.parent.mkdir(parents=True,exist_ok=True)
 if src.suffix=='.json' and len(data)>120000:
  dst=dst.with_suffix(dst.suffix+'.xz');cache=HERE/'compression-check'/(sha(data)+'.xz')
  if cache.exists():
   packed=cache.read_bytes();assert sha(lzma.decompress(packed))==sha(data)
  else:packed=lzma.compress(data,preset=6)
  dst.write_bytes(packed)
 else:dst.write_bytes(data)
 return {'path':dst.relative_to(DEST).as_posix(),'sha256':sha(dst.read_bytes()),'originalSha256':sha(data),'originalBytes':len(data),'compression':{'.gz':'gzip','.xz':'xz'}.get(dst.suffix,'none')}
def main():
 selection=json.loads((HERE/'selection.json').read_bytes());cases=[]
 for item in selection:
  source=HERE/item['source'];target=DEST/item['destination'];members=[]
  missing=[]
  for name in ['case-input.json','document-hashes.json','trace.json','browser-identity.json','incomplete.json']:
   if (source/name).exists():members.append(put(source/name,target/name))
   elif name!='incomplete.json':missing.append(name)
  for p in sorted(source.glob('*-presentation.json')):members.append(put(p,target/p.name))
  videos=list((source/'video').glob('*.webm'));assert len(videos)==1
  members.append(put(videos[0],target/'native.webm'))
  if (source/'native-review').exists():
   for p in sorted((source/'native-review').iterdir()):
    if p.is_file():members.append(put(p,target/'native-review'/p.name))
  cases.append({k:v for k,v in item.items() if k!='source'}|{'acquisitionId':item['source'],'caseId':json.loads((source/'case-input.json').read_bytes())['caseId'],'missingArtifacts':missing,'members':members})
 for name in ['currentness.json','preservation-reuse.json','trace-review-selected-chromium.json','trace-review-selected-firefox.json','source-tests.tap','public-baseline-readback.json','native-pixel-review.json','v1.txt','docs-review.json','native-environment.json','acquisition-environments.json','fixture-review.json','preflight-error.json']:
  if (HERE/name).exists():put(HERE/name,DEST/'qualification'/name)
 for name in ['R0006-spec.md','issue-body.md','accepted-audit.md','accepted-assessment.json']:
  put(HERE/'authority'/name,DEST/'authority'/name)
 for name in ['prepare_cases.py','index_video.py','package_evidence.py']:
  put(HERE/name,DEST/'qualification/tools'/name)
 if (HERE/'independent-review').exists():
  for p in sorted((HERE/'independent-review').rglob('*')):
   if p.is_file() and p.suffix in ('.md','.json','.png','.jpg','.tap','.txt','.py'):
    put(p,DEST/'qualification/independent-review'/p.relative_to(HERE/'independent-review'))
 dump(DEST/'cases.json',{'schema':'r0006-native-proof/v1','acquisitions':cases,'nativeInputPacket':'tests/rlgwo/R0006-cases.json','sourceBase':'c431733c57f76e2b441ee8f8cd85a1fa6675de55','runtimeSourceChanged':False})
 manifest=[]
 for p in sorted(DEST.rglob('*')):
  if p.is_file() and p.name!='manifest.json':manifest.append({'path':p.relative_to(DEST).as_posix(),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size})
 dump(DEST/'manifest.json',{'schema':'r0006-artifact-manifest/v1','files':manifest,'fileCount':len(manifest),'totalBytes':sum(x['bytes'] for x in manifest)})
 print('Projected',len(cases),'original acquisitions;',len(manifest),'manifested files;',sum(x['bytes'] for x in manifest),'bytes')
if __name__=='__main__':main()
