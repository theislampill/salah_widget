"""Seal the bounded delivery extension on the existing nondeploying evidence branch.

No push, no worktree/source changes, no mutation of the immutable qualification packet.
"""
from pathlib import Path
import datetime, hashlib, json, os, re, shutil, subprocess

E=Path(__file__).resolve().parents[1]
R=Path(r'C:\Users\theis\.codex\worktrees\r000b-close\salah_widget')
D=E/'delivery'; P=E/'delivery-projection'
H='573dc2b15af37b5d32faa4364f3e653b65431dfc'
B='16658749209e0c567f49a3fc9dc855f665afa6e4'
M='763a460e98dc23c7f0e95bf346274f1685b3c654'
T='3656edba44b79ab7216c8cbf3546f4fe085bee9a'
Q='885348adc26f9db468b39b65ba2c07cf130d26ca'
BRANCH='codex/r000b-evidence-20261014'
PREFIX='docs/rlgwo-execution/20261014/R000B-delivery/'
sha=lambda b:hashlib.sha256(b).hexdigest()
def dump(p,v):p.write_bytes((json.dumps(v,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode())
def command(*a,**kw):return subprocess.check_output(a,cwd=R,**kw)
def git(*a,**kw):return command('git',*a,**kw)
def api(p):return json.loads(command('gh','api','repos/theislampill/salah_widget'+p))
assert not P.exists(),'Preserve any existing delivery projection; inspect before a new seal.'
assert git('rev-parse','HEAD').decode().strip()==H and not git('status','--porcelain').strip()
assert api('/git/ref/heads/main')['object']['sha']==M
assert git('rev-parse',M+'^{tree}').decode().strip()==T
assert git('rev-parse','refs/heads/'+BRANCH).decode().strip()==Q
assert api('/git/ref/heads/'+BRANCH)['object']['sha']==Q
assert api('/pages')['source']=={'branch':'main','path':'/'}
assert json.loads((D/'source-docs-readback.json').read_bytes())['status']=='PASS'
consumer=json.loads((D/'public-consumer/readback.json').read_bytes())
assert consumer['status']=='PASS_ASSERTIONS_PENDING_PIXEL_REVIEW'
assert len(consumer['results'])==2 and sum(len(r['states']) for r in consumer['results'])==10
primary=json.loads((D/'primary-public-consumer-review.json').read_bytes())
assert primary['status']=='PASS_BOUNDED_PUBLIC_ENDPOINTS_WITH_RETAINED_LIMITATIONS'
review=E/'independent-review/delivery/delivery-review.json'
independent=json.loads(review.read_bytes())
assert independent['status'].startswith('PASS'),independent['status']
assert independent['decision']['deliveryEvidenceAccepted'] is True and independent['decision']['blockers']==[]
assert sha(review.read_bytes())=='d2d4ffa0c321ca8bdc11d6129e3f1ae76a38f1859e398f6816e41869ee1d19e9'
certificate=E/'closure-certificate.json'
cert=json.loads(certificate.read_bytes())
assert cert['status']=='QUALIFIED_AND_DELIVERED_FOR_COMPLETED_CLOSURE'
assert cert['independentDeliveryReview']['sha256']==sha(review.read_bytes())

files={};local_diagnostics=[]
def include(p,name=None):
 assert p.is_file(),str(p)
 key=name or p.relative_to(E).as_posix()
 assert key not in files and not key.startswith('../')
 files[key]=p
for name in ['owner-authorization.json','before-ready-gate.json','ready-result.json','before-merge-gate.json',
 'merge-request.json','merge-response.raw.json','merged-pr.json','merged-main.json','merge-commit.json',
 'merge-verification.json','fetch-merged-main.json','premature-closure-observed.json',
 'premature-closure-reconciliation.json','reopen-result.json','deployment-observed.json',
 'deployment-polls.jsonl','source-docs-readback.json','verify_public_delivery.py','public_consumer.py',
 'merge_r000b.py','primary-public-consumer-review.json']:
 include(D/name)
for root in [D/'public-consumer',E/'independent-review/delivery']:
 for p in sorted(root.rglob('*')):
  if p.is_file():
   if p.suffix=='.txt':
    local_diagnostics.append({'path':p.relative_to(E).as_posix(),'bytes':p.stat().st_size,
     'sha256':sha(p.read_bytes()),'reason':'HTTP diagnostic headers and stderr retained locally; parsed API bodies and substantive verification receipts are included.'})
   else:include(p)
for name in ['public-head-review.json','posted-public-review-readback.json','prepublication-review.json']:
 include(E/'publication-review'/name)
include(certificate)
include(D/'required-delivery-receipt.json','required-delivery-receipt.json')
include(D/'package_delivery.py','tools/package_delivery.py')
include(D/'prepare_closure.py','tools/prepare_closure.py')
P.mkdir()
patterns={'github_token':rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{60,})',
 'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
 'openai_key':rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}'}
rows=[];findings=[]
for name,p in sorted(files.items()):
 data=p.read_bytes();assert len(data)<25_000_000,(name,len(data))
 assert p.suffix.lower() in {'.json','.jsonl','.md','.py','.js','.html','.mjs','.png'},name
 assert p.name.lower() not in {'.env','credentials','cookies.json'}
 if p.suffix!='.png':
  for kind,pattern in patterns.items():
   if re.search(pattern,data):findings.append({'path':name,'kind':kind})
 dst=P/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
 rows.append({'path':name,'bytes':len(data),'sha256':sha(data)})
assert not findings,findings
manifest={'schema':'r000b-delivery-extension-manifest/v1','approvedHead':H,'reviewedBase':B,
 'mergeCommit':M,'sourceTree':T,'qualificationEvidenceCommit':Q,'prefix':PREFIX,
 'independentDeliveryReviewSha256':sha(review.read_bytes()),'files':rows,
 'fileCount':len(rows),'totalBytes':sum(r['bytes'] for r in rows),
 'localDiagnosticExclusions':local_diagnostics,
 'privacyCheck':{'highConfidenceCredentialFindings':findings,'scope':'Bounded explicit delivery records, original PNGs and read-only review receipts. Local tool paths are intentional provenance, not a universal privacy guarantee.'},
 'publicationScope':'Append-only evidence extension; never merge this branch or its artifacts into main/Pages. Original qualification commit remains immutable.'}
dump(P/'manifest.json',manifest)
index=D/'delivery.git-index';assert not index.exists()
env=dict(os.environ,GIT_INDEX_FILE=str(index))
def staged(*a,**kw):return git(*a,env=env,**kw)
staged('read-tree',Q)
paths=sorted([r['path'] for r in rows]+['manifest.json'])
oids=staged('hash-object','-w','--no-filters','--stdin-paths',input=('\n'.join((P/p).as_posix() for p in paths)+'\n').encode()).decode().splitlines()
assert len(oids)==len(paths)
staged('update-index','-z','--index-info',input=''.join(f'100644 {oid}\t{PREFIX}{p}\0' for p,oid in zip(paths,oids)).encode())
delta=staged('diff','--cached',Q,'--name-only','-z').decode().rstrip('\0').split('\0')
assert set(delta)=={PREFIX+p for p in paths}
tree=staged('write-tree').decode().strip()
message=D/'delivery-commit-message.txt'
message.write_bytes(b'test: preserve R000B authorized merge and Pages delivery receipts\n\nAppend bounded public consumer, independent delivery review and closure certificate evidence outside the deploying branch. Preserve prior qualification and contrary evidence.\n\nCo-Authored-By: Codex <noreply@openai.com>\n')
commit=git('commit-tree',tree,'-p',Q,'-F',str(message)).decode().strip()
git('update-ref','refs/heads/'+BRANCH,commit,Q)
assert git('rev-parse','HEAD').decode().strip()==H and not git('status','--porcelain').strip()
out={'schema':'r000b-delivery-evidence-commit/v1','status':'SEALED_LOCAL_NOT_YET_PUSHED',
 'commit':commit,'tree':tree,'parent':Q,'branch':BRANCH,'prefix':PREFIX,
 'sourceHead':H,'sourceTree':T,'mergeCommit':M,'manifestSha256':sha((P/'manifest.json').read_bytes()),
 'certificateSha256':sha(certificate.read_bytes()),'files':len(paths),'totalBytes':sum((P/p).stat().st_size for p in paths),
 'sealedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'changedPaths':delta,'mainChanged':False,'pagesConfigurationChanged':False,'pushed':False}
dump(D/'delivery-evidence-commit.json',out)
print(json.dumps({k:v for k,v in out.items() if k!='changedPaths'}))
