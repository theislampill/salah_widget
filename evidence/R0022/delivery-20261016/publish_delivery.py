"""Append reviewed delivery evidence on the existing non-deploying evidence branch."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, urllib.request
D=Path(__file__).resolve().parent
R=Path('C:/Users/theis/.codex/worktrees/r0022-execution/salah_widget')
E=D/'publication-effects'
HEAD='a81644115d951fd3378b0ec738716c71bb4a8673'
MERGE='f270792f39ef8bf4cabffbe6746ac0ea0dd9d3de'
PARENT='3b1606a9b21508fd1e1c5a949ae1140de76391e9'
BRANCH='codex/r0022-evidence-20261015'
PREFIX='evidence/R0022/delivery-20261016/'
def read(p):return json.loads(p.read_bytes())
def digest(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def git(*a,env=None):return subprocess.check_output(['git',*a],cwd=R,env=env)
def api(p):return json.loads(subprocess.check_output(['gh','api','repos/theislampill/salah_widget/'+p]))
def record(name,v):
    with (E/name).open('x',encoding='utf-8')as f:f.write(json.dumps(v,indent=2)+'\n')
def guards():
    assert git('rev-parse','HEAD').decode().strip()==HEAD and not git('status','--porcelain')
    assert git('remote','get-url','origin').decode().strip()=='https://github.com/theislampill/salah_widget.git'
    assert api('git/ref/heads/main')['object']['sha']==MERGE
    issue=api('issues/34');assert issue['state']=='open' and issue['state_reason']is None
    pr=api('pulls/66');assert pr['merged'] and pr['head']['sha']==HEAD and pr['merge_commit_sha']==MERGE
    pages=api('pages');assert pages['source']=={'branch':'main','path':'/'} and pages['build_type']=='legacy'
    run=api('actions/runs/38932765174');assert run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==MERGE
def main():
    assert not E.exists(),'Reconcile any prior publication outcome before retry'
    review=read(D/'INDEPENDENT-DELIVERY-REVIEW.json')
    assert review['status']=='ACCEPTED_DELIVERED_NATIVE_AND_PUBLIC_IDENTITY' and review['merge']==MERGE
    assert review['summarySha256']==digest((D/'native/summary.json').read_bytes())
    approval=read(D/'PUBLICATION-METHOD-REVIEW.json')
    assert approval['status']=='ACCEPTED_BOUNDED_PUBLICATION_METHOD' and approval['scriptSha256']==digest(Path(__file__).read_bytes())
    inventory_path=D/'DELIVERY-PUBLICATION-PINS.json'
    assert approval['inputManifestSha256']==digest(inventory_path.read_bytes())
    inventory=read(inventory_path)['files']
    assert isinstance(inventory,list) and inventory
    approved={}
    for item in inventory:
        rel=item['path']
        assert isinstance(rel,str) and rel and '\\'not in rel and not rel.startswith('/') and ':'not in rel
        assert all(part not in {'','.','..'}for part in rel.split('/')) and rel not in approved
        approved[rel]=item
    guards()
    assert api('git/ref/heads/'+BRANCH)['object']['sha']==PARENT and git('rev-parse','refs/heads/'+BRANCH).decode().strip()==PARENT
    assert not git('ls-tree','-r','--name-only',PARENT,'--',PREFIX)
    names=['OWNER-APPROVAL.json','INDEPENDENT-MERGE-REVIEW.json','INDEPENDENT-PAGES-REVIEW.json','INDEPENDENT-DELIVERY-REVIEW.json','CONSUMER-METHOD-REVIEW.json','CONSUMER-R3-METHOD-REVIEW.json','CONSUMED-SOURCE-PINS.json','served-runtime.json','retained-preflight-failure.json','check_consumers.py','check_consumers_r2.py','check_consumers_r3.py','merge_exact.py','read_served.py','publish_delivery.py']
    files={name:D/name for name in names}
    for folder in ['merge-effects','native','native-r3']:
        for p in sorted((D/folder).rglob('*')):
            if p.is_file():
                assert p.suffix in {'.json','.png'},str(p)
                files[p.relative_to(D).as_posix()]=p
    assert all(p.is_file()for p in files.values())
    assert set(files)==set(approved), 'Missing/extra selected delivery input'
    for rel,p in files.items():
        b=p.read_bytes();assert len(b)==approved[rel]['bytes'] and digest(b)==approved[rel]['sha256'],rel
    # The independently accepted manifest has its own digest above; no circular
    # self-entry is invented. The review itself is retained for final readback.
    files['DELIVERY-PUBLICATION-PINS.json']=inventory_path
    E.mkdir();env=os.environ.copy();env['GIT_INDEX_FILE']=str(E/'temporary-evidence-index');git('read-tree',PARENT,env=env)
    rows=[]
    for rel,p in sorted(files.items()):
        b=p.read_bytes();assert len(b)<15*1024*1024
        if rel in approved:assert len(b)==approved[rel]['bytes'] and digest(b)==approved[rel]['sha256'],rel
        else:assert rel=='DELIVERY-PUBLICATION-PINS.json' and digest(b)==approval['inputManifestSha256']
        blob=git('hash-object','-w','--',str(p)).decode().strip()
        assert digest(git('cat-file','blob',blob))==digest(b),rel
        git('update-index','--add','--cacheinfo','100644,'+blob+','+PREFIX+rel,env=env)
        rows.append({'path':PREFIX+rel,'sha256':digest(b),'bytes':len(b),'blobSha':blob})
    tree=git('write-tree',env=env).decode().strip()
    assert set(git('diff-tree','--no-commit-id','--name-only','-r',PARENT,tree).decode().splitlines())=={x['path']for x in rows}
    msg=E/'message.txt';msg.write_text('Record R0022 approved production delivery and native readback\n\nBind the exact normal merge, successful Pages deployment, served bytes and bounded original native observations. Preserve prior method failures and their dispositions.\n\nCo-Authored-By: Codex <noreply@openai.com>\n',encoding='utf-8')
    commit=git('commit-tree',tree,'-p',PARENT,'-F',str(msg)).decode().strip()
    record('intent.json',{'atUtc':now(),'commit':commit,'tree':tree,'parent':PARENT,'files':rows,'sourceHead':HEAD,'merge':MERGE})
    guards();assert api('git/ref/heads/'+BRANCH)['object']['sha']==PARENT
    git('update-ref','refs/heads/'+BRANCH,commit,PARENT)
    effect=subprocess.run(['git','push','origin',commit+':refs/heads/'+BRANCH],cwd=R,capture_output=True)
    record('push-result.json',{'atUtc':now(),'exitCode':effect.returncode,'stdout':effect.stdout.decode(),'stderr':effect.stderr.decode()})
    assert effect.returncode==0,'Reconcile actual remote outcome; never blind retry'
    assert api('git/ref/heads/'+BRANCH)['object']['sha']==commit
    c=api('git/commits/'+commit);assert c['tree']['sha']==tree and[p['sha']for p in c['parents']]==[PARENT]
    for row in rows:
        assert digest(git('cat-file','blob',row['blobSha']))==row['sha256']
        url='https://raw.githubusercontent.com/theislampill/salah_widget/'+commit+'/'+row['path']
        with urllib.request.urlopen(url,timeout=60)as response:b=response.read();assert response.status==200
        assert len(b)==row['bytes'] and digest(b)==row['sha256']
    guards()
    record('readback.json',{'atUtc':now(),'commit':commit,'tree':tree,'parent':PARENT,'files':rows,'allGitHttpBytesMatch':True,'sourceHead':HEAD,'main':MERGE,'issue34':'OPEN/null'})
    print(json.dumps({'commit':commit,'files':len(rows),'bytes':sum(x['bytes']for x in rows),'allGitHttpBytesMatch':True}))
if __name__=='__main__':main()
