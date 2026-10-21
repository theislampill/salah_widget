"""Append reviewed delivery payload to the existing non-deploying evidence branch."""
from pathlib import Path
import datetime,hashlib,json,subprocess,urllib.request
D=Path(__file__).resolve().parent;P=D/'public';E=D/'publication-effects'
R=Path(r'${REPO_ROOT}')
W=D.parent/'publication-copy-r1'
HEAD='ec53e1a3778f2f73054253a2a28795873f48364c'
MERGE='f71fef6ccf7e4efcb57b5a26688d2360461a3253'
PARENT='ded62f32bd15f38c7f9ab9f7fd774f1ee5468775'
BRANCH='codex/r0021-evidence-20261016';PREFIX='evidence/R0021/delivery-20261021/'
def read(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def git(repo,*a):return subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0',*a],cwd=repo)
def api(p):return json.loads(subprocess.check_output(['gh','api','repos/theislampill/salah_widget/'+p]))
def record(name,v):
 with (E/name).open('x',encoding='utf-8') as f:f.write(json.dumps(v,indent=2)+'\n')
def guards():
 assert not (D.parent/'native-resource.lock').exists(),'Native resource must be released before publication'
 assert git(R,'rev-parse','HEAD').decode().strip()==HEAD and not git(R,'status','--porcelain')
 assert git(W,'remote','get-url','origin').decode().strip()=='https://github.com/theislampill/salah_widget.git'
 assert api('git/ref/heads/main')['object']['sha']==MERGE
 issue=api('issues/33');assert issue['state']=='open' and issue['state_reason'] is None
 pr=api('pulls/67');assert pr['merged'] and pr['head']['sha']==HEAD and pr['merge_commit_sha']==MERGE
 run=api('actions/runs/39670161254');assert run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==MERGE
def main():
 assert not E.exists(),'Reconcile prior publication outcome; never blind retry'
 review=read(D/'INDEPENDENT-DELIVERY-REVIEW.json')
 assert review['status']=='ACCEPTED_DELIVERED_NATIVE_AND_PUBLIC_IDENTITY' and review['merge']==MERGE
 assert review['summarySha256']==sha((D/'native-r2/summary.json').read_bytes())
 approval=read(D/'PUBLICATION-METHOD-REVIEW.json')
 assert approval['status']=='ACCEPTED_BOUNDED_PUBLICATION_METHOD' and approval['scriptSha256']==sha(Path(__file__).read_bytes())
 assert approval['inputManifestSha256']==sha((P/'MANIFEST.json').read_bytes())
 manifest=read(P/'MANIFEST.json');files={};rows=[]
 for item in manifest['files']:
  rel=item['path'];assert rel and not rel.startswith('/') and '\\' not in rel and ':' not in rel
  assert all(x not in {'','.','..'} for x in rel.split('/')) and rel not in files
  p=P/rel;b=p.read_bytes();assert len(b)==item['storedBytes'] and sha(b)==item['storedSha256']
  files[rel]=p
 assert set(files)|{'MANIFEST.json'}=={p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file()}
 files['MANIFEST.json']=P/'MANIFEST.json'
 helper=next(x for x in manifest['files'] if x['path']=='prepare_public.py')
 assert helper['originalSha256']==sha((D/'prepare_public.py').read_bytes())
 from prepare_public import project
 review_bytes=(json.dumps(project(approval),indent=2)+'\n').encode()
 guards();assert api('git/ref/heads/'+BRANCH)['object']['sha']==PARENT
 assert git(W,'branch','--show-current').decode().strip()==BRANCH and git(W,'rev-parse','HEAD').decode().strip()==PARENT
 assert not git(W,'status','--porcelain') and not (W/PREFIX).exists()
 E.mkdir();record('intent.json',{'atUtc':now(),'parent':PARENT,'branch':BRANCH,'prefix':PREFIX,'manifestSha256':approval['inputManifestSha256'],'sourceHead':HEAD,'merge':MERGE})
 for rel,p in sorted(files.items()):
  b=p.read_bytes();q=W/PREFIX/rel;q.parent.mkdir(parents=True,exist_ok=True)
  with q.open('xb') as f:f.write(b)
  rows.append({'path':PREFIX+rel,'sha256':sha(b),'bytes':len(b)})
 q=W/PREFIX/'PUBLICATION-METHOD-REVIEW.json'
 with q.open('xb') as f:f.write(review_bytes)
 rows.append({'path':PREFIX+'PUBLICATION-METHOD-REVIEW.json','sha256':sha(review_bytes),'bytes':len(review_bytes)})
 git(W,'add','--',PREFIX)
 assert set(git(W,'diff','--cached','--name-only').decode().splitlines())=={x['path'] for x in rows}
 for row in rows:assert sha(git(W,'show',':'+row['path']))==row['sha256']
 msg=E/'message.txt';msg.write_text('Preserve R0021 approved production delivery evidence\n\nBind exact merge and Pages bytes to bounded Chromium/Firefox public and file consumers. Retain acquisition limitations and independent conclusions.\n\nCo-Authored-By: Codex <noreply@openai.com>\n',encoding='utf-8')
 git(W,'commit','--file',str(msg));commit=git(W,'rev-parse','HEAD').decode().strip();tree=git(W,'rev-parse','HEAD^{tree}').decode().strip()
 assert git(W,'rev-list','--parents','-n','1','HEAD').decode().split()==[commit,PARENT]
 assert not git(W,'status','--porcelain');record('commit.json',{'commit':commit,'tree':tree,'parent':PARENT,'files':rows})
 guards();assert api('git/ref/heads/'+BRANCH)['object']['sha']==PARENT
 pushed=subprocess.run(['git','-c','maintenance.auto=false','-c','gc.auto=0','push','origin','HEAD:refs/heads/'+BRANCH],cwd=W,capture_output=True)
 record('push-result.json',{'atUtc':now(),'exitCode':pushed.returncode,'stdout':pushed.stdout.decode(),'stderr':pushed.stderr.decode()})
 assert pushed.returncode==0,'Unknown/failed push: reconcile actual effect before retry'
 assert api('git/ref/heads/'+BRANCH)['object']['sha']==commit
 c=api('git/commits/'+commit);assert c['tree']['sha']==tree and [x['sha'] for x in c['parents']]==[PARENT]
 for row in rows:
  with urllib.request.urlopen('https://raw.githubusercontent.com/theislampill/salah_widget/'+commit+'/'+row['path'],timeout=60) as response:
   b=response.read();assert response.status==200
  assert len(b)==row['bytes'] and sha(b)==row['sha256'],row['path']
 guards();record('readback.json',{'atUtc':now(),'commit':commit,'tree':tree,'parent':PARENT,'files':rows,'allGitHttpBytesMatch':True,'sourceHead':HEAD,'main':MERGE,'issue33':'OPEN/null'})
 print(json.dumps({'commit':commit,'files':len(rows),'bytes':sum(x['bytes'] for x in rows),'allGitHttpBytesMatch':True}))
if __name__=='__main__':main()
