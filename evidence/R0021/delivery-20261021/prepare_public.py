"""Project only selected R0021 delivery evidence; original PNGs remain byte-exact."""
from pathlib import Path
import hashlib,json,re
D=Path(__file__).resolve().parent;O=D.parent
R=Path(r'${REPO_ROOT}')
P=D/'public'
roles=[(str(O),'${WORK_ROOT}'),(str(R),'${REPO_ROOT}'),(r'${BROWSER_CACHE}','${BROWSER_CACHE}'),(r'${TOOL_CACHE}','${TOOL_CACHE}'),(r'${STDLIB_PYTHON}','${STDLIB_PYTHON}'),(r'${QA_TOOLCHAIN}','${QA_TOOLCHAIN}'),(r'${SYSTEM_ROOT}','${SYSTEM_ROOT}')]
roles.append((r'${GITHUB_CLI}','${GITHUB_CLI}'))
def safe(s):
 for a,b in roles:s=s.replace(a,b).replace(a.replace('\\','/'),b).replace(a.replace('\\','\\\\'),b)
 return s
def project(v):
 if isinstance(v,str):return safe(v)
 if isinstance(v,list):return [project(x) for x in v]
 if isinstance(v,dict):return {safe(k):('[WITHHELD: isolated browser command line]' if k in {'command_line','commandLine'} else project(x)) for k,x in v.items()}
 return v
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 assert not P.exists(),'Retain any prior projection; reconcile before replacement'
 sources={n:D/n for n in ['INDEPENDENT-MERGE-PAGES-REVIEW.json','SERVED-RUNTIME-REVIEW.json','served-runtime.json','CONSUMER-METHOD-REVIEW.json','CONSUMER-INPUTS.json','INDEPENDENT-DELIVERY-REVIEW.json','check_consumers.py','read_served.py','prepare_public.py','publish_delivery.py','certificate_effects.py','README.md']}
 sources['OWNER-APPROVAL.json']=O/'intake/EXACT_MERGE_APPROVAL.json'
 sources['FINAL-SOURCE-REVIEW.json']=O/'independent-review/successor-final-merge-remote-review-r1.json'
 for name in ['check_consumers_r2.py','CONSUMER-R2-METHOD-REVIEW.json','CONSUMER-R2-INPUTS.json','CHROMIUM-PUBLIC-CONSUMER-REVIEW.json','native-run.log','native-r2-run.log']:
  sources[name]=D/name
 for folder in ['native','native-r2']:
  for p in sorted((D/folder).rglob('*')):
   if p.is_file():
    assert p.suffix in {'.json','.png'},p
    sources[p.relative_to(D).as_posix()]=p
 assert all(p.is_file() for p in sources.values())
 P.mkdir();rows=[]
 for name,p in sorted(sources.items()):
  raw=p.read_bytes()
  if p.suffix=='.json':stored=(json.dumps(project(json.loads(raw)),indent=2)+'\n').encode();mode='json-path-projection'
  elif p.suffix=='.png':stored=raw;mode='exact-original-pixels'
  else:stored=safe(raw.decode('utf-8')).encode();mode='text-path-projection'
  if p.suffix!='.png':assert not re.search(rb'(?<![A-Za-z0-9])[A-Za-z]:[\\/]',stored),(name,'Unprojected host path')
  q=P/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(stored)
  rows.append({'path':name,'sourceRole':safe(str(p)),'originalSha256':sha(raw),'originalBytes':len(raw),'storedSha256':sha(stored),'storedBytes':len(stored),'projection':mode})
 manifest={'schema':'r0021-delivery-publication/v1','merge':'f71fef6ccf7e4efcb57b5a26688d2360461a3253','runtime':'1b6586d8921a99780b2cefff95821ad90bf39571ef074ccffe4234ec8aa7f02b','scope':'Selected delivery evidence; host paths replaced by documented roles. No profiles, credentials, executable binaries or downloaded product duplicates. Original PNG bytes unchanged; all raw failures and limits preserved.','files':rows}
 (P/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'files':len(rows),'bytes':sum(x['storedBytes'] for x in rows),'manifestSha256':sha((P/'MANIFEST.json').read_bytes())}))
if __name__=='__main__':main()
