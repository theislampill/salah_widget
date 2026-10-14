from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import subprocess,json,hashlib
E=Path(__file__).resolve().parent;O=E/'dag-reconciliation-r1';P=E/'planning-original-21e7a843/docs/rlgwo-execution/20261008'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda t:hashlib.sha256(t.encode()).hexdigest()
def api(endpoint):
    r=subprocess.run(['gh','api','--paginate','--slurp',endpoint],capture_output=True,check=True)
    return json.loads(r.stdout)
allissues=[x for page in api('repos/theislampill/salah_widget/issues?state=all&per_page=100') for x in page]
live={x['number']:x for x in allissues if 'pull_request' not in x}
inventory=read(P/'INVENTORY.json');final=read(P/'FINAL_ISSUE_READBACK.json')
before={x['number']:x for x in inventory['issues']};published={x['issue']:x for x in final['issues']}
closed=[1,5,9,10,14,15,18,26,29,30,31];expected=set(inventory['actualOpen'])
assert len(expected)==26 and len(closed)==11
rows=[];errors=[]
def comments(n):return n,[x for page in api(f'repos/theislampill/salah_widget/issues/{n}/comments?per_page=100') for x in page]
with ThreadPoolExecutor(max_workers=4) as pool:discussion=dict(pool.map(comments,sorted(expected)))
raw=O/'live-readback';raw.mkdir(exist_ok=True)
for n in range(1,38):
    x=live[n];r={'issue':n,'state':x['state'],'stateReason':x['state_reason'],'url':x['html_url'],'bodySha256':sha(x['body']),'updatedAt':x['updated_at']}
    if n in expected:
        r['originalBodyUnchanged']=r['bodySha256']==before[n]['bodySha256']
        # Github transports authored Markdown using CRLF. Preserve the body;
        # compare its logical LF text exactly as the publication manifest did.
        match=next((c for c in discussion[n] if c['html_url']==published[n]['commentUrl']),None)
        r['publishedCommentUrl']=published[n]['commentUrl']
        r['publishedCommentPresent']=match is not None
        r['publishedCommentSha256']=sha(match['body'].replace('\r\n','\n')) if match else None
        r['publishedCommentUnchanged']=r['publishedCommentSha256']==published[n]['commentSha256']
        r['discussionCount']=len(discussion[n]);r['discussionReadBack']=True
        r['laterComments']=[{'url':c['html_url'],'createdAt':c['created_at'],'bodySha256':sha(c['body'])} for c in discussion[n] if match and c['id']>match['id']]
        (raw/f'{n:02}.json').write_text(json.dumps({'issue':x,'comments':discussion[n]},indent=2)+'\n',encoding='utf-8')
        if x['state']!='open' or not r['originalBodyUnchanged'] or not r['publishedCommentUnchanged']:errors.append(r)
    elif x['state']!='closed' or x['state_reason']!='completed':errors.append(r)
    rows.append(r)
pr=api('repos/theislampill/salah_widget/pulls/43')[0]
main=api('repos/theislampill/salah_widget/git/ref/heads/main')[0]
report={'capturedAtUtc':datetime.now(timezone.utc).isoformat(),'specCommit':'21e7a84365fae37a86cae5c7d5e41008c0adc53f','liveMain':main['object']['sha'],'draftPR':{'url':pr['html_url'],'head':pr['head']['sha'],'base':pr['base']['sha'],'draft':pr['draft'],'state':pr['state']},'issues':rows,'newIssuesOutsideScope':[n for n in live if n>37],'open26Preserved':sum(x['state']=='open' for x in rows)==26,'accepted11Preserved':all(live[n]['state']=='closed' for n in closed),'errors':errors,'result':'FAIL' if errors else 'PASS'}
(O/'LIVE_CURRENTNESS.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='issues'},indent=2))
