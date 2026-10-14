"""R000C actual Pages delivery readback; no source or public mutation."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, subprocess, urllib.request
E=Path(__file__).resolve().parents[1]; R=E.parent/'salah_widget'; D=E/'delivery'
H='9ae80bc6e729325320002d46d324a0b4aafc8f01'; B='7827099dff3c9bc5ecb1b7a67dc4c25414bcfb69'
M='16658749209e0c567f49a3fc9dc855f665afa6e4'; T='6ff810cd8337cf7cf80c5c6511320ebacc8ea103'
U='https://theislampill.github.io/salah_widget/'
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
sha=lambda b:hashlib.sha256(b).hexdigest()
def command(a):return subprocess.check_output(a,cwd=R)
def api(p):return json.loads(command(['gh','api','repos/theislampill/salah_widget'+p]))
def save(n,v):(D/n).write_text(json.dumps(v,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
assert not (D/'source-docs-readback.json').exists(),'Retain prior delivery attempt; inspect before any repeat.'
pr=api('/pulls/60');branch=api('/branches/main');commit=api('/git/commits/'+M)
assert pr['merged'] and not pr['draft'] and pr['merge_commit_sha']==M and pr['head']['sha']==H
assert branch['commit']['sha']==M
assert [p['sha'] for p in commit['parents']]==[B,H] and commit['tree']['sha']==T
pages=api('/pages/builds/latest');runs=api('/actions/runs?head_sha='+M)['workflow_runs']
matched=[r for r in runs if r['name']=='pages build and deployment' and r['head_sha']==M]
ready=pages['commit']==M and pages['status']=='built' and len(matched)==1 and matched[0]['status']=='completed' and matched[0]['conclusion']=='success'
save('deployment-observed.json',{'readAtUtc':now(),'mergeCommit':M,'ready':ready,'pages':pages,'matchedRuns':matched})
assert ready,'Await exact merge deployment; no HTTP acquisition started'
runtime=json.loads((R/'tests/rlgwo/R000C-cases.json').read_bytes())['runtime']
prior=json.loads((E/'independent-review/public-head-readback-01/receipt-index.json').read_bytes())
paths=sorted(set(runtime['files'])|{r['path'] for r in prior['raw']}|{'v1/index.html','README.md','DESIGN.md'})
rows=[]
receipt={'schema':'r000c-delivered-proof/v1','readAtUtc':now(),'status':'RUNNING','approvedHead':H,'reviewedBase':B,
 'mergeCommit':M,'tree':T,'pr':pr,'main':branch,'commit':commit,'pagesBuild':pages,'pagesWorkflow':matched[0],
 'runtimeFiles':135,'runtimeTreeSha256':runtime['treeSha256'],'httpFiles':rows,
 'scope':'All 135 production runtime files plus V1, delivered README/DESIGN and the independently selected original evidence/fixture set are read from actual Pages HTTPS and compared to the exact merged Git objects. Public consumer and original qualification remain separate. Historical pending lifecycle fields are preserved.'}
save('source-docs-readback.json',receipt)
def read(path):
 expected=command(['git','show',M+':'+path]);expected_sha=sha(expected);expected_size=len(expected)
 if path in runtime['files']:
  assert expected_sha==runtime['files'][path]['sha256'] and expected_size==runtime['files'][path]['bytes'],path
 req=urllib.request.Request(U+path,headers={'Cache-Control':'no-cache','Accept-Encoding':'identity','User-Agent':'R000C-owner-authorized-delivery-readback'})
 row={'path':path,'url':U+path,'expectedSha256':expected_sha,'expectedBytes':expected_size,'readAtUtc':now()}
 try:
  with urllib.request.urlopen(req,timeout=45) as response:
   h=hashlib.sha256();count=0
   while chunk:=response.read(1024*1024):h.update(chunk);count+=len(chunk)
   row.update({'resolvedUrl':response.url,'httpStatus':response.status,'bytes':count,'sha256':h.hexdigest(),
     'exact':response.status==200 and count==expected_size and h.hexdigest()==expected_sha,
     'etag':response.headers.get('ETag'),'lastModified':response.headers.get('Last-Modified')})
 except Exception as error:row.update({'exact':False,'error':repr(error)})
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 futures=[pool.submit(read,p) for p in paths]
 for future in concurrent.futures.as_completed(futures):
  rows.append(future.result());save('source-docs-readback.json',receipt)
  if len(rows)%25==0:print(json.dumps({'filesRead':len(rows),'total':len(paths),'mismatches':sum(not r['exact'] for r in rows)}),flush=True)
rows.sort(key=lambda r:r['path'])
after=api('/branches/main');receipt['mainAfter']=after['commit']['sha']
receipt['status']='PASS' if all(r['exact'] for r in rows) and after['commit']['sha']==M else 'FAIL'
receipt['completedAtUtc']=now();receipt['totalBytesRead']=sum(r.get('bytes',0) for r in rows)
save('source-docs-readback.json',receipt)
assert receipt['status']=='PASS',[r for r in rows if not r['exact']]
print(json.dumps({'status':receipt['status'],'mergeCommit':M,'tree':T,'filesVerified':len(rows),'runtimeFiles':135,'bytes':receipt['totalBytesRead'],'pagesRun':matched[0]['html_url']}))
