"""Execute only the owner's exact R000B readiness and merge authorization."""
from pathlib import Path
import datetime, hashlib, json, subprocess, time

E=Path(__file__).resolve().parents[1]
D=E/'delivery'
R=Path(r'C:\Users\theis\.codex\worktrees\r000b-close\salah_widget')
H='573dc2b15af37b5d32faa4364f3e653b65431dfc'
B='16658749209e0c567f49a3fc9dc855f665afa6e4'
T='3656edba44b79ab7216c8cbf3546f4fe085bee9a'
V='885348adc26f9db468b39b65ba2c07cf130d26ca'
PREFIX='docs/rlgwo-execution/20261014/R000B/'
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(name,value):
    (D/name).write_bytes((json.dumps(value,indent=2,ensure_ascii=True)+'\n').encode())
def run(*args):return subprocess.check_output(args,cwd=R).decode().strip()
def api(path):return json.loads(run('gh','api','repos/theislampill/salah_widget'+path))
assert not (D/'merge-response.raw.json').exists(),'Prior merge effect exists; read it before any retry.'
assert not (D/'ready-result.json').exists(),'Prior readiness effect exists; read it before any retry.'
gate=json.loads((E/'owner-gate.json').read_bytes())
pins={
 'independent-review/final-joined-review.json':'6d4ac1a177bf71c617bef15ff2381e4bce8ae7d11cc8c1d748c67e460d93b559',
 'publication-review/prepublication-review.json':'8920157cc9d8a672a0f87f9b6b276c01b9b856d9bee3c07e5f25a129355fc9d9',
 'publication-review/public-head-review.json':'aedec4cb0f977798c88d035cd815b28a7b68ba37db3b8bd8e33a8952a51bcdb3',
 'publication-review/posted-public-review-readback.json':'7d554871ca804a72184cbe8fc43e708c030843c1d25a66ce98f2fa0750ff186a',
}
for path,digest in pins.items():assert sha((E/path).read_bytes())==digest,path
review=json.loads((E/'publication-review/public-head-review.json').read_bytes())
assert not review['decision']['blockingFindings']
assert not json.loads((E/'publication-review/prepublication-review.json').read_bytes())['decision']['localPrepublicationBlockers']
assert run('git','rev-parse','HEAD')==H and run('git','rev-parse','HEAD^{tree}')==T and run('git','rev-parse','HEAD^')==B
assert not run('git','status','--porcelain=v1')
assert run('git','diff','--name-only',B,H).splitlines()==gate['changedFiles']
for item in review['sourceFiles']:
    assert sha((R/item['path']).read_bytes())==item['sha256'],item['path']
assert run('git','ls-tree','-r','--name-only',H,'--',PREFIX).splitlines()==[PREFIX+'README.md',PREFIX+'reference.json']
save('owner-authorization.json',{'schema':'r000b-owner-authorization/v1','recordedAtUtc':now(),
    'source':'Direct human authorization in this conversation on 2026-10-14, OWNER AUTHORISATION - APPROVE PR #61 AND CLOSE R000B',
    'head':H,'reviewedBase':B,'sourceTree':T,'evidenceCommit':V,'method':'merge',
    'authorized':'Mark exact PR ready, merge if the stated conditions hold, verify delivery, publish/read back certificate, close completed and independently verify.',
    'constraints':'No changed head/base/scope; no new blocking finding; obey repository requirements; retain contrary evidence; evidence branch never merged or added to Pages; no Pages configuration change.'})

def preconditions(stage,draft):
    repo=api('');branch=api('/branches/main');rules=api('/rules/branches/main')
    protection_result=subprocess.run(['gh','api','repos/theislampill/salah_widget/branches/main/protection'],cwd=R,capture_output=True,text=True)
    protection=json.loads(protection_result.stdout)
    checks=api('/commits/'+H+'/check-runs?per_page=100')
    status=api('/commits/'+H+'/status?per_page=100')
    files=api('/pulls/61/files?per_page=100');reviews=api('/pulls/61/reviews?per_page=100')
    comments=api('/issues/61/comments?per_page=100');pages=api('/pages');issue=api('/issues/11')
    commit=api('/git/commits/'+H);evidence=api('/git/ref/heads/codex/r000b-evidence-20261014')
    assert repo['full_name']=='theislampill/salah_widget' and repo['allow_merge_commit'] and not repo['archived'] and not repo['disabled']
    assert branch['commit']['sha']==B and not branch['protected'] and rules==[]
    assert protection_result.returncode!=0 and protection.get('status')=='404' and protection.get('message')=='Branch not protected'
    assert checks['total_count']==0 and checks['check_runs']==[] and status['statuses']==[]
    assert sorted(f['filename'] for f in files)==gate['changedFiles'] and len(files)==17
    assert {f['filename']:f['sha'] for f in files}=={r['path']:r['gitBlob'] for r in review['sourceFiles']}
    assert reviews==[], 'New review requires reconciliation before effect'
    assert {c['id'] for c in comments}=={6177021137,6177218895},'New public comment requires reconciliation'
    for cid,filename in [(6177021137,'prepublication-review-comment.md'),(6177218895,'public-head-review-comment.md')]:
        assert next(c for c in comments if c['id']==cid)['body'].encode()==(E/filename).read_bytes()
    assert pages['source']=={'branch':'main','path':'/'} and pages['build_type']=='legacy'
    assert issue['state']=='open' and sha(issue['body'].encode())=='f83c4f3516b63a068dc768b16d64e14cb970cf41ea074e240e73dcffda6d0bcc'
    assert commit['tree']['sha']==T and [p['sha'] for p in commit['parents']]==[B]
    assert evidence['object']['sha']==V
    # Last reads immediately precede the effect; merge API also enforces exact head.
    main=api('/git/ref/heads/main');pr=api('/pulls/61')
    for _ in range(3):
        if pr['mergeable'] is not None:break
        time.sleep(2);pr=api('/pulls/61')
    assert pr['head']['sha']==H and pr['base']['sha']==main['object']['sha']==B
    assert pr['base']['repo']['full_name']==pr['head']['repo']['full_name']=='theislampill/salah_widget'
    assert pr['state']=='open' and not pr['merged'] and pr['draft']==draft and pr['mergeable'] and pr['mergeable_state']=='clean' and pr['auto_merge'] is None
    value={'status':'PASS_EXACT_OWNER_CONDITIONS','checkedAtUtc':now(),'stage':stage,'head':H,'base':B,'tree':T,'evidenceCommit':V,
       'reviewHashes':pins,'sourceClean':True,'sourceFiles':17,'noUnreviewedBytes':True,
       'branch':branch,'applicableRules':rules,'protectionResponse':protection,'checkRuns':checks,'commitStatus':status,
       'ciInterpretation':'No configured required checks, check runs or status contexts. This is not a CI PASS.',
       'pr':pr,'pages':pages,'issueState':issue['state'],'reviewCount':len(reviews),'commentIds':[c['id'] for c in comments]}
    save('before-'+stage+'-gate.json',value)

preconditions('ready',True)
result=subprocess.run(['gh','pr','ready','61','--repo','theislampill/salah_widget'],cwd=R,capture_output=True,text=True)
save('ready-result.json',{'atUtc':now(),'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
assert result.returncode==0,'Readiness result requires state readback before any retry.'
preconditions('merge',False)
request={'sha':H,'merge_method':'merge','commit_title':'Merge PR #61: validate radar epochs and preserve recovery sky',
 'commit_message':'Merge the exact independently reviewed R000B source candidate under owner authorization. Preserve its separate immutable evidence branch.\n\nCo-Authored-By: Codex <noreply@openai.com>'}
save('merge-request.json',request)
result=subprocess.run(['gh','api','--method','PUT','repos/theislampill/salah_widget/pulls/61/merge','--input',str(D/'merge-request.json')],cwd=R,capture_output=True)
(D/'merge-response.raw.json').write_bytes(result.stdout)
(D/'merge-response.stderr.txt').write_bytes(result.stderr)
assert result.returncode==0,'Merge outcome ambiguous or rejected; read actual PR/main before retry.'
response=json.loads(result.stdout);assert response['merged'] is True,response
M=response['sha'];pr=api('/pulls/61');main=api('/git/ref/heads/main');commit=api('/git/commits/'+M);issue=api('/issues/11')
save('merged-pr.json',pr);save('merged-main.json',main);save('merge-commit.json',commit)
assert pr['merged'] and pr['state']=='closed' and not pr['draft'] and pr['head']['sha']==H and pr['merge_commit_sha']==M
assert main['object']['sha']==M and commit['tree']['sha']==T and [p['sha'] for p in commit['parents']]==[B,H]
assert issue['state']=='open','Issue must remain open until delivery and certificate verification.'
fetch=subprocess.run(['git','-c','maintenance.auto=false','-c','gc.auto=0','fetch','origin','main'],cwd=R,capture_output=True,text=True)
save('fetch-merged-main.json',{'returncode':fetch.returncode,'stdout':fetch.stdout,'stderr':fetch.stderr});assert fetch.returncode==0
assert run('git','rev-parse','origin/main')==M and run('git','rev-parse',M+'^{tree}')==T
save('merge-verification.json',{'status':'PASS_AUTHORIZED_EXACT_MERGE','checkedAtUtc':now(),'pr':pr['html_url'],'approvedHead':H,'reviewedBase':B,
 'mergeCommit':M,'mergeParents':[B,H],'tree':T,'main':M,'evidenceCommit':V,'issue11State':'open','deliveryComplete':False})
print(json.dumps({'status':'PASS_AUTHORIZED_EXACT_MERGE','mergeCommit':M,'tree':T,'parents':[B,H],'issue11':'open'}),flush=True)
