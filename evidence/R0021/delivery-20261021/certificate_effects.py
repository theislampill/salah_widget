"""Separate reviewed certificate POST and intentional completed-close effects."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys,urllib.request
D=Path(__file__).resolve().parent
MERGE='f71fef6ccf7e4efcb57b5a26688d2360461a3253'
MARKER='<!-- CLOSE-R0021:v1:PR67:'+MERGE+' -->'
INDEX='b4a6831b80439d3002f9cf4fae5bc15943bc9f9f2fa5ab0c4a1fc09f33a57298'
def read(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def api(path,method='GET',body=None):
    cmd=['gh','api','--method',method,'repos/theislampill/salah_widget/'+path]
    if body is not None:cmd+=['--input','-']
    p=subprocess.run(cmd,input=None if body is None else json.dumps(body).encode(),capture_output=True)
    if p.returncode:raise RuntimeError('API failure; reconcile actual effect before retry: '+p.stderr.decode())
    return json.loads(p.stdout)
def paged(path):
    rows=[];page=1
    while True:
        chunk=api(path+('?' if '?' not in path else '&')+'per_page=100&page='+str(page));rows.extend(chunk)
        if len(chunk)<100:return rows
        page+=1

def record(folder,name,value):
    with(folder/name).open('x',encoding='utf-8')as f:f.write(json.dumps(value,indent=2)+'\n')
def delivery_guard():
    assert api('git/ref/heads/main')['object']['sha']==MERGE
    commit=api('git/commits/'+MERGE)
    assert commit['tree']['sha']=='79aedcac840d624b5ea423922314f0832dc3f750'
    assert [p['sha'] for p in commit['parents']]==['f270792f39ef8bf4cabffbe6746ac0ea0dd9d3de','ec53e1a3778f2f73054253a2a28795873f48364c']
    pages=api('pages');assert pages['source']=={'branch':'main','path':'/'} and pages['build_type']=='legacy'
    pr=api('pulls/67');assert pr['merged'] and pr['merge_commit_sha']==MERGE and pr['head']['sha']=='ec53e1a3778f2f73054253a2a28795873f48364c'
    run=api('actions/runs/39670161254');assert run['head_sha']==MERGE and run['status']=='completed' and run['conclusion']=='success'
    with urllib.request.urlopen('https://theislampill.github.io/salah_widget/',timeout=60)as r:body=r.read();assert r.status==200
    assert sha(body)==INDEX
    return {'atUtc':now(),'merge':MERGE,'rootIndexSha256':sha(body),'pagesRun':39670161254,'rootBytes':len(body)}
def post():
    e=D/'certificate-post-effects';assert not e.exists(),'Reconcile previous effect; never blind retry'
    body=(D/'CLOSE-R0021.md').read_text(encoding='utf-8');digest=sha(body.encode())
    review=read(D/'INDEPENDENT-CERTIFICATE-REVIEW.json')
    assert review['status']=='ACCEPTED_CLOSE_R0021_CERTIFICATE_FOR_POSTING' and review['certificateSha256']==digest and review['merge']==MERGE and review['effectScriptSha256']==sha(Path(__file__).read_bytes())
    assert body.startswith(MARKER) and '@@'not in body
    proof=delivery_guard();issue=api('issues/33');assert issue['state']=='open' and issue['state_reason']is None
    comments=paged('issues/33/comments');assert not any(MARKER in c['body']for c in comments),'Existing certificate requires reconciliation'
    e.mkdir();record(e,'intent.json',{'atUtc':now(),'issue':33,'stateBefore':issue['state'],'certificateSha256':digest,'reviewSha256':sha((D/'INDEPENDENT-CERTIFICATE-REVIEW.json').read_bytes()),'delivery':proof})
    # Unique marker and persisted intent make unknown POST outcomes recoverable.
    response=api('issues/33/comments','POST',{'body':body});record(e,'response.json',response)
    actual=api('issues/comments/'+str(response['id']));issue=api('issues/33')
    assert actual['body']==body and issue['state']=='open' and issue['state_reason']is None
    record(e,'readback.json',{'atUtc':now(),'comment':actual,'bodySha256':sha(actual['body'].encode()),'issue':issue,'state':'CERTIFICATE_POSTED_WHILE_OPEN_AWAITING_INDEPENDENT_READBACK'})
    print(json.dumps({'commentUrl':actual['html_url'],'commentId':actual['id'],'bodySha256':digest,'issueState':issue['state']}))
def close():
    e=D/'closure-effects';assert not e.exists(),'Reconcile previous close outcome before retry'
    posted=read(D/'certificate-post-effects/readback.json');review=read(D/'INDEPENDENT-POSTED-CERTIFICATE-READBACK.json')
    assert review['status']=='ACCEPTED_ACTUAL_CERTIFICATE_WHILE_OPEN_AND_IMMUTABLE_LINKS'
    assert review['effectScriptSha256']==sha(Path(__file__).read_bytes())
    assert review['commentId']==posted['comment']['id'] and review['bodySha256']==posted['bodySha256'] and review['merge']==MERGE
    body=(D/'CLOSE-R0021.md').read_text(encoding='utf-8');assert sha(body.encode())==posted['bodySha256']
    actual=api('issues/comments/'+str(posted['comment']['id']));assert actual['body']==body
    proof=delivery_guard();issue=api('issues/33');assert issue['state']=='open' and issue['state_reason']is None
    e.mkdir();record(e,'intent.json',{'atUtc':now(),'issue':33,'from':'open','to':'closed','state_reason':'completed','certificateCommentId':actual['id'],'certificateCreatedAt':actual['created_at'],'bodySha256':posted['bodySha256'],'reviewSha256':sha((D/'INDEPENDENT-POSTED-CERTIFICATE-READBACK.json').read_bytes()),'delivery':proof})
    response=api('issues/33','PATCH',{'state':'closed','state_reason':'completed'});record(e,'response.json',response)
    actual_issue=api('issues/33');timeline=paged('issues/33/timeline')
    assert actual_issue['state']=='closed' and actual_issue['state_reason']=='completed'
    comment_index=next(i for i,x in enumerate(timeline)if x.get('event')=='commented'and x.get('id')==posted['comment']['id'])
    closed_indices=[i for i,x in enumerate(timeline)if x.get('event')=='closed']
    assert closed_indices and comment_index<closed_indices[-1]
    record(e,'readback.json',{'atUtc':now(),'issue':actual_issue,'timeline':timeline,'certificateCommentId':posted['comment']['id'],'certificateBeforeClosure':True,'delivery':delivery_guard()})
    print(json.dumps({'issue33':actual_issue['state']+'/'+actual_issue['state_reason'],'certificateBeforeClosure':True,'closedAt':actual_issue['closed_at']}))
if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1]in{'post','close'}
    {'post':post,'close':close}[sys.argv[1]]()
