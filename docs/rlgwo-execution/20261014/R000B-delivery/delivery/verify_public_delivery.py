"""R000B actual Pages delivery readback; no source or public mutation."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, subprocess, urllib.request
E=Path(__file__).resolve().parents[1]; R=Path(r'C:\Users\theis\.codex\worktrees\r000b-close\salah_widget'); D=E/'delivery'
H='573dc2b15af37b5d32faa4364f3e653b65431dfc'; B='16658749209e0c567f49a3fc9dc855f665afa6e4'
M='763a460e98dc23c7f0e95bf346274f1685b3c654'; T='3656edba44b79ab7216c8cbf3546f4fe085bee9a'
U='https://theislampill.github.io/salah_widget/'
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
sha=lambda b:hashlib.sha256(b).hexdigest()
def command(a):return subprocess.check_output(a,cwd=R)
def api(p):return json.loads(command(['gh','api','repos/theislampill/salah_widget'+p]))
def save(n,v):(D/n).write_text(json.dumps(v,indent=2,ensure_ascii=True)+'\n',encoding='utf8')
assert not (D/'source-docs-readback.json').exists(),'Retain prior delivery attempt; inspect before any repeat.'
pr=api('/pulls/61');branch=api('/branches/main');commit=api('/git/commits/'+M)
assert pr['merged'] and not pr['draft'] and pr['merge_commit_sha']==M and pr['head']['sha']==H
assert branch['commit']['sha']==M
assert [p['sha'] for p in commit['parents']]==[B,H] and commit['tree']['sha']==T
pages=api('/pages/builds/latest');runs=api('/actions/runs?head_sha='+M)['workflow_runs']
matched=[r for r in runs if r['name']=='pages build and deployment' and r['head_sha']==M]
ready=pages['commit']==M and pages['status']=='built' and len(matched)==1 and matched[0]['status']=='completed' and matched[0]['conclusion']=='success'
save('deployment-observed.json',{'readAtUtc':now(),'mergeCommit':M,'ready':ready,'pages':pages,'matchedRuns':matched})
with (D/'deployment-polls.jsonl').open('ab') as log:log.write((json.dumps({'readAtUtc':now(),'ready':ready,'commit':pages['commit'],'buildStatus':pages['status'],'workflowStates':[(r['status'],r['conclusion']) for r in matched]})+'\n').encode())
if not ready:
 print(json.dumps({'status':'NOT_READY','mergeCommit':M,'buildStatus':pages['status']}));raise SystemExit(3)
runtime=json.loads((E/'public-projection/recovery-handoff-source/flash-counterexample/candidate.json').read_bytes())['runtime']
assert runtime['treeSha256']=='c2753a21c337ff0bc09cea05f15bfc7729dcc2295a924c11284399fdab6e9ea2' and len(runtime['files'])==135
review=json.loads((E/'publication-review/public-head-review.json').read_bytes())
paths=sorted(set(runtime['files'])|{r['path'] for r in review['sourceFiles']}|{'v1/index.html','README.md','DESIGN.md','HANDOFF.md'})
rows=[]
receipt={'schema':'r000b-delivered-proof/v1','readAtUtc':now(),'status':'RUNNING','approvedHead':H,'reviewedBase':B,
 'mergeCommit':M,'tree':T,'pr':pr,'main':branch,'commit':commit,'pagesBuild':pages,'pagesWorkflow':matched[0],
 'runtimeFiles':135,'runtimeTreeSha256':runtime['treeSha256'],'httpFiles':rows,
 'scope':'All 135 production runtime files plus frozen V1 entry and all17 reviewed PR files including delivered README/DESIGN/HANDOFF are read from actual Pages HTTPS and compared to the exact merged Git objects. Public consumer and original qualification remain separate. Historical pending lifecycle fields are preserved.'}
save('source-docs-readback.json',receipt)
def read(path):
 expected=command(['git','show',M+':'+path]);expected_sha=sha(expected);expected_size=len(expected)
 if path in runtime['files']:
  assert expected_sha==runtime['files'][path]['sha256'] and expected_size==runtime['files'][path]['bytes'],path
 req=urllib.request.Request(U+path,headers={'Cache-Control':'no-cache','Accept-Encoding':'identity','User-Agent':'R000B-owner-authorized-delivery-readback'})
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
