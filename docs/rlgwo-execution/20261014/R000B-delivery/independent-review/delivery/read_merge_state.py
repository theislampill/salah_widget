"""Independent read-only exact-merge and restored-issue-state inspection."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,subprocess,time,urllib.request,urllib.error

E=Path(r'C:\workspace\ai\r000b-execution-20261014')
W=Path(r'C:\Users\theis\.codex\worktrees\r000b-close\salah_widget')
O=E/'independent-review/delivery'
O.mkdir(exist_ok=True)
A=O/'merge-api';A.mkdir(exist_ok=True)
repo='https://api.github.com/repos/theislampill/salah_widget'
M='763a460e98dc23c7f0e95bf346274f1685b3c654';H='573dc2b15af37b5d32faa4364f3e653b65431dfc';B='16658749209e0c567f49a3fc9dc855f665afa6e4';T='3656edba44b79ab7216c8cbf3546f4fe085bee9a';V='885348adc26f9db468b39b65ba2c07cf130d26ca'
sha=lambda b:hashlib.sha256(b).hexdigest()
receipts=[];data={}
def save_attempt(row):
    receipts.append(row)
    with (A/'attempts.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row)+'\n')

for key,tail in [('pr','/pulls/61'),('main','/git/ref/heads/main'),('merge-commit','/git/commits/'+M),('evidence-ref','/git/ref/heads/codex/r000b-evidence-20261014'),('issue11','/issues/11'),('issue11-events','/issues/11/events?per_page=100'),('pr-files','/pulls/61/files?per_page=100')]:
    url=repo+tail;success=False
    for attempt in range(1,3):
        row={'key':key,'url':url,'method':'GET','authorizationSent':False,'attempt':attempt,'startedAtUtc':datetime.now(timezone.utc).isoformat()};start=time.monotonic()
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'R000B-independent-merge-readback','Accept':'application/vnd.github+json','Accept-Encoding':'identity','X-GitHub-Api-Version':'2022-11-28'})
            with urllib.request.urlopen(req,timeout=25) as resp:
                b=resp.read(8*1024*1024+1);assert len(b)<=8*1024*1024
                row.update({'status':resp.status,'finalUrl':resp.url,'headers':dict(resp.headers.items()),'bytes':len(b),'sha256':sha(b)});assert resp.status==200
            data[key]=json.loads(b);(A/(key+'.json')).write_bytes(b);row['result']='ACQUIRED';success=True
        except urllib.error.HTTPError as err:
            b=err.read();row.update({'result':'HTTP_ACQUISITION_FAILURE','status':err.code,'error':str(err),'bytes':len(b),'sha256':sha(b)});(A/(key+'-error-'+str(attempt)+'.bin')).write_bytes(b)
        except Exception as err:row.update({'result':'ACQUISITION_FAILURE','error':str(err),'errorType':type(err).__name__})
        row['elapsedSeconds']=time.monotonic()-start;save_attempt(row)
        if success:break
        if row.get('status') in {401,403} or attempt==2:break
        time.sleep(2)
    if not success:
        (O/'merge-readback-receipt.json').write_text(json.dumps({'status':'BLOCKED_ACQUISITION','failedKey':key,'receipts':receipts},indent=2)+'\n',encoding='utf-8');raise SystemExit(2)

# These are authenticated, read-only administrative metadata GETs, never mutations.
for key,tail,expected_status in [('pages','/pages',200),('main-branch','/branches/main',200),('main-rules','/rules/branches/main',200),('main-protection','/branches/main/protection',404)]:
    args=['gh','api','--include','repos/theislampill/salah_widget'+tail]
    start=time.monotonic();result=subprocess.run(args,cwd=W,capture_output=True)
    (A/(key+'-http.txt')).write_bytes(result.stdout);(A/(key+'-stderr.txt')).write_bytes(result.stderr)
    match=re.match(rb'HTTP/[^\s]+\s+(\d+)',result.stdout);assert match,(key,result.stdout[:200])
    http=int(match.group(1));parts=re.split(rb'\r?\n\r?\n',result.stdout,maxsplit=1);assert len(parts)==2
    body=parts[1];data[key]=json.loads(body);(A/(key+'.json')).write_bytes(body)
    row={'key':key,'url':repo+tail,'method':'GET','transport':'gh api --include','authenticated':True,'status':http,'returncode':result.returncode,'responseSha256':sha(result.stdout),'responseBytes':len(result.stdout),'bodySha256':sha(body),'bodyBytes':len(body),'elapsedSeconds':time.monotonic()-start,'result':'EXPECTED_BRANCH_UNPROTECTED_RESPONSE' if expected_status==404 and http==404 else 'ACQUIRED'}
    save_attempt(row);assert http==expected_status,(key,http)

args=['gh','pr','view','61','--repo','theislampill/salah_widget','--json','number,state,isDraft,mergeCommit,mergedAt,closingIssuesReferences,headRefOid,baseRefOid']
result=subprocess.run(args,cwd=W,capture_output=True);assert result.returncode==0,result.stderr
(A/'closing-issues.json').write_bytes(result.stdout);data['closing-issues']=json.loads(result.stdout)
save_attempt({'key':'closing-issues','transport':'gh pr view --json (read-only GraphQL)','method':'query','authenticated':True,'returncode':result.returncode,'responseBytes':len(result.stdout),'responseSha256':sha(result.stdout),'result':'ACQUIRED'})

pr=data['pr'];commit=data['merge-commit'];events=data['issue11-events'];issue=data['issue11'];pages=data['pages']
stage=json.loads((E/'staged-candidate-check.json').read_bytes());expected_files={r['path']:r['gitBlob'] for r in stage['files']}
actual_files={r['filename']:r['sha'] for r in data['pr-files']}
closed=[r for r in events if r['id']==33265433588];reopened=[r for r in events if r['id']==33265528618]
checks={
 'approvedPrHead':pr['head']['sha']==H,
 'prMerged':pr['merged'] and pr['state']=='closed' and pr['draft'] is False and pr['merge_commit_sha']==M,
 'mainExactMerge':data['main']['object']['sha']==M,
 'mergeParentsExact':[r['sha'] for r in commit['parents']]==[B,H],
 'mergeTreeExact':commit['tree']['sha']==T,
 'same17ReviewedFilesAndBlobs':actual_files==expected_files and len(actual_files)==17,
 'evidenceBranchUnchanged':data['evidence-ref']['object']['sha']==V,
 'pagesConfigurationUnchanged':pages['source']=={'branch':'main','path':'/'} and pages['build_type']=='legacy',
 'currentMainUnprotected':data['main-branch']['protected'] is False and data['main-branch']['commit']['sha']==M,
 'currentApplicableRulesNone':data['main-rules']==[],
 'protectionExpected404':data['main-protection'].get('status')=='404' and data['main-protection'].get('message')=='Branch not protected',
 'issue11CurrentlyOpen':issue['state']=='open' and issue['closed_at'] is None,
 'issueBodyUnchanged':sha(issue['body'].encode())=='f83c4f3516b63a068dc768b16d64e14cb970cf41ea074e240e73dcffda6d0bcc',
 'prematureClosedEventRetained':len(closed)==1 and closed[0]['event']=='closed',
 'reopenedEventRetained':len(reopened)==1 and reopened[0]['event']=='reopened',
 'closedBeforeReopened':len(closed)==1 and len(reopened)==1 and closed[0]['created_at']<reopened[0]['created_at'],
 'closingIssueRelationPresent':any(r['number']==11 for r in data['closing-issues']['closingIssuesReferences']),
}
summary={'schema':'r000b-independent-merge-state-readback/v1','status':'PASS' if all(checks.values()) else 'FAIL','checkedAtUtc':datetime.now(timezone.utc).isoformat(),'checks':checks,'pr':{'url':pr['html_url'],'head':pr['head']['sha'],'reportedCurrentBase':pr['base']['sha'],'state':pr['state'],'draft':pr['draft'],'merged':pr['merged'],'mergedAt':pr['merged_at'],'mergeCommit':pr['merge_commit_sha']},'main':data['main']['object']['sha'],'mergeTree':commit['tree']['sha'],'mergeParents':[r['sha'] for r in commit['parents']],'evidenceRef':data['evidence-ref']['object']['sha'],'pages':pages,'issue':{'state':issue['state'],'stateReason':issue.get('state_reason'),'closedAt':issue['closed_at'],'bodySha256':sha(issue['body'].encode())},'events':[{'id':x['id'],'event':x['event'],'createdAt':x['created_at'],'actor':x['actor']['login'],'stateReason':x.get('state_reason'),'intent':x.get('intent'),'commitId':x.get('commit_id')} for x in closed+reopened],'receipts':receipts,'deliveryComplete':False,'closureComplete':False}
(O/'merge-readback-receipt.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='receipts'}),flush=True)
if not all(checks.values()):raise SystemExit(3)
