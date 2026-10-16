"""Publish exact reviewed completed-closure records on the evidence branch only."""
from pathlib import Path
import datetime,hashlib,importlib.util,json,os,subprocess,urllib.request
D=Path(__file__).resolve().parent
E=D/'final-publication-effects'
MERGE='f270792f39ef8bf4cabffbe6746ac0ea0dd9d3de'
BRANCH='codex/r0022-evidence-20261015'
PREFIX='evidence/R0022/closure-20261016/'
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def record(name,v):
    with(E/name).open('x',encoding='utf-8')as f:f.write(json.dumps(v,indent=2)+'\n')
def main():
    assert not E.exists(),'Reconcile prior publication outcome before retry'
    helper=D/'publish_delivery.py'
    assert digest(helper.read_bytes())=='5d8adca74a0c73a9eb468b0b1335a424150226786ccab2c99c2a26668099a974'
    spec=importlib.util.spec_from_file_location('delivery_helpers',helper);h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    approval=read(D/'FINAL-PUBLICATION-METHOD-REVIEW.json')
    assert approval['status']=='ACCEPTED_BOUNDED_FINAL_PUBLICATION' and approval['scriptSha256']==digest(Path(__file__).read_bytes())
    manifest=D/'CLOSURE-PUBLICATION-PINS.json';assert digest(manifest.read_bytes())==approval['inputManifestSha256']
    rows=read(manifest)['files'];assert rows
    parent=read(D/'publication-effects/readback.json')['commit'];assert approval['parent']==parent
    closure=read(D/'INDEPENDENT-CLOSURE-READBACK.json')
    assert closure['status']=='ACCEPTED_ACTUAL_COMPLETED_CLOSURE_AND_PUBLIC_DELIVERY' and closure['merge']==MERGE
    cert=read(D/'certificate-post-effects/readback.json')
    def guards():
        assert h.git('rev-parse','HEAD').decode().strip()==h.HEAD and not h.git('status','--porcelain')
        assert h.git('remote','get-url','origin').decode().strip()=='https://github.com/theislampill/salah_widget.git'
        assert h.api('git/ref/heads/main')['object']['sha']==MERGE
        issue=h.api('issues/34');assert issue['state']=='closed' and issue['state_reason']=='completed'
        actual=h.api('issues/comments/'+str(cert['comment']['id']));assert digest(actual['body'].encode())==cert['bodySha256']
        pages=h.api('pages');assert pages['source']=={'branch':'main','path':'/'} and pages['build_type']=='legacy'
        run=h.api('actions/runs/38932765174');assert run['head_sha']==MERGE and run['status']=='completed' and run['conclusion']=='success'
    guards();assert h.api('git/ref/heads/'+BRANCH)['object']['sha']==parent and h.git('rev-parse','refs/heads/'+BRANCH).decode().strip()==parent
    assert not h.git('ls-tree','-r','--name-only',parent,'--',PREFIX)
    allowed={'CLOSE-R0022.md','INDEPENDENT-CERTIFICATE-REVIEW.json','INDEPENDENT-POSTED-CERTIFICATE-READBACK.json','INDEPENDENT-CLOSURE-READBACK.json','INDEPENDENT-PUBLICATION-READBACK.json','PUBLICATION-METHOD-REVIEW.json','FINAL-READBACK.json','FINAL-READBACK.md','S10-HANDOFF.json','S10-HANDOFF.md','certificate_effects.py','publish_closure.py'}
    for folder in ['certificate-post-effects','closure-effects']:
        allowed.update(p.relative_to(D).as_posix()for p in(D/folder).rglob('*.json'))
    for name in ['intent.json','push-result.json','readback.json']:allowed.add('publication-effects/'+name)
    paths=set()
    for row in rows:
        rel=row['path'];assert isinstance(rel,str) and rel and '\\'not in rel and ':'not in rel and not rel.startswith('/') and all(x not in {'','.','..'}for x in rel.split('/')) and rel not in paths
        paths.add(rel);b=(D/rel).read_bytes();assert len(b)==row['bytes'] and digest(b)==row['sha256'] and len(b)<5*1024*1024
    assert paths==allowed,'Exact closure input selection required'
    files=[*rows,{'path':manifest.name,'bytes':manifest.stat().st_size,'sha256':digest(manifest.read_bytes())}]
    E.mkdir();env=os.environ.copy();env['GIT_INDEX_FILE']=str(E/'temporary-evidence-index');h.git('read-tree',parent,env=env);published=[]
    for row in files:
        p=D/row['path'];b=p.read_bytes();assert len(b)==row['bytes'] and digest(b)==row['sha256']
        blob=h.git('hash-object','-w','--',str(p)).decode().strip();assert digest(h.git('cat-file','blob',blob))==row['sha256']
        path=PREFIX+row['path'];h.git('update-index','--add','--cacheinfo','100644,'+blob+','+path,env=env);published.append({**row,'path':path,'blobSha':blob})
    tree=h.git('write-tree',env=env).decode().strip();assert set(h.git('diff-tree','--no-commit-id','--name-only','-r',parent,tree).decode().splitlines())=={x['path']for x in published}
    msg=E/'message.txt';msg.write_text('Record R0022 certificate-first completed closure and scoped S10 handoff\n\nRetain actual posted certificate, independent comment/closure/public readbacks and the current37issue census. This evidence branch does not deploy.\n\nCo-Authored-By: Codex <noreply@openai.com>\n',encoding='utf-8')
    commit=h.git('commit-tree',tree,'-p',parent,'-F',str(msg)).decode().strip();record('intent.json',{'atUtc':now(),'commit':commit,'tree':tree,'parent':parent,'files':published,'merge':MERGE})
    guards();assert h.api('git/ref/heads/'+BRANCH)['object']['sha']==parent
    h.git('update-ref','refs/heads/'+BRANCH,commit,parent)
    p=subprocess.run(['git','push','origin',commit+':refs/heads/'+BRANCH],cwd=h.R,capture_output=True);record('push-result.json',{'atUtc':now(),'exitCode':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode()});assert p.returncode==0,'Reconcile actual remote effect; no blind retry'
    assert h.api('git/ref/heads/'+BRANCH)['object']['sha']==commit
    c=h.api('git/commits/'+commit);assert c['tree']['sha']==tree and[x['sha']for x in c['parents']]==[parent]
    for row in published:
        url='https://raw.githubusercontent.com/theislampill/salah_widget/'+commit+'/'+row['path']
        with urllib.request.urlopen(url,timeout=60)as response:b=response.read();assert response.status==200
        assert len(b)==row['bytes'] and digest(b)==row['sha256']
    guards();record('readback.json',{'atUtc':now(),'commit':commit,'tree':tree,'parent':parent,'files':published,'allGitHttpBytesMatch':True,'main':MERGE,'issue34':'CLOSED/completed','certificateUrl':cert['comment']['html_url']})
    print(json.dumps({'commit':commit,'files':len(published),'bytes':sum(x['bytes']for x in published),'allGitHttpBytesMatch':True}))
if __name__=='__main__':main()
