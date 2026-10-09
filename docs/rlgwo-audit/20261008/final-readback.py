"""Read every initial issue/comment after effects and assemble the final ledger."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, subprocess

R=Path(__file__).resolve().parent
REPO='theislampill/salah_widget'
TARGET='18ff14860ff41c084b1db5f396bb62aa9c22b1be'
def gh(*a):
    p=subprocess.run(['gh',*a],capture_output=True,text=True,encoding='utf-8')
    if p.returncode: raise RuntimeError(p.stderr)
    return json.loads(p.stdout)
def pages(path):
    result=gh('api',path+('&' if '?' in path else '?')+'per_page=100','--paginate','--slurp')
    return [x for p in result for x in p]
def dump(p,x): p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

approval=json.loads((R/'approved-publication.json').read_text(encoding='utf-8'))
inventory=json.loads((R/'initial-inventory.json').read_text(encoding='utf-8'))
recon=json.loads((R/'primary-reconciliation.json').read_text(encoding='utf-8'))
assert len(approval['issues'])==37 and all(x['approved'] for x in approval['issues'])
for a in approval['issues']:
    p=R/f'workers/{a["reviewer"]}/{a["number"]:02d}-publication.json'
    assert p.is_file() and json.loads(p.read_text(encoding='utf-8'))['status']=='VERIFIED',p

main=gh('api',f'repos/{REPO}/git/ref/heads/main')['object']['sha']
assert main==TARGET
out=R/'final-readback'
assert not out.exists(), 'Preserve any prior final readback; reconcile before a retry'
out.mkdir()
items=pages(f'repos/{REPO}/issues?state=all')
issues={x['number']:x for x in items if 'pull_request' not in x}
dump(out/'all-items.json',items)
def read_one(a):
    n=a['number']; issue=gh('api',f'repos/{REPO}/issues/{n}')
    comments=pages(f'repos/{REPO}/issues/{n}/comments')
    original=json.loads((R/f'issues/{n:02d}.json').read_text(encoding='utf-8'))
    assert issue['id']==original['issue']['id']
    assert hashlib.sha256(issue['body'].encode()).hexdigest()==a['bodySha256']
    expected=(R/a['commentPath']).read_text(encoding='utf-8')
    marker=f'<!-- RLGWO-AUDIT:{TARGET}:{a["canonicalId"]}:2026-10-08 -->'
    own=[x for x in comments if marker in x['body']]
    assert len(own)==1 and own[0]['body'].replace('\r\n','\n')==expected.replace('\r\n','\n')
    receipt=json.loads((R/f'workers/{a["reviewer"]}/{n:02d}-publication.json').read_text(encoding='utf-8'))
    assert issue['state']==receipt['finalState'] and issue.get('state_reason')==receipt['finalStateReason']
    if a['disposition'].startswith('CLOSE'):
        assert issue['state']=='closed' and issue['state_reason']=='completed'
    dump(out/f'{n:02d}.json',{'issue':issue,'comments':comments,'publicationReceipt':receipt})
    rr=next(x for x in recon['issues'] if x['number']==n)
    return {'number':n,'canonicalId':a['canonicalId'],'title':issue['title'],'reviewer':a['reviewer'],
            'AUDIT_SHA':TARGET,'bodySha256':a['bodySha256'],'disposition':a['disposition'],
            'publishedCommentUrl':own[0]['html_url'],'commentSha256':a['commentSha256'],
            'closedByAudit':receipt['closedByAudit'],'independentlyOrAlreadyClosed':receipt.get('independentlyOrAlreadyClosed',False),
            'finalState':issue['state'],'finalStateReason':issue.get('state_reason'),
            'matrixRows':rr['matrixRows'],'evidence':rr['assessment'],
            'remainingWorkHandoff':None if a['disposition'].startswith('CLOSE') else own[0]['html_url'],
            'additionalDiscussionIds':[x['id'] for x in comments if x['id'] not in a['reviewedCommentIds'] and x['id']!=own[0]['id']]}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    rows=sorted(pool.map(read_one,approval['issues']),key=lambda x:x['number'])
new=[x for n,x in issues.items() if n not in inventory['initialNumbers']]
counts={'reviewed':len(rows),'evidenceCommented':sum(bool(x['publishedCommentUrl']) for x in rows),
        'closedByAudit':sum(x['closedByAudit'] for x in rows),
        'independentlyOrAlreadyClosed':sum(x['independentlyOrAlreadyClosed'] for x in rows),
        'remainingOpen':sum(x['finalState']=='open' for x in rows),'newIssuesOutsideInitialSet':len(new)}
ledger={'repository':REPO,'auditDate':'2026-10-08','AUDIT_SHA':TARGET,'initialInventory':'initial-inventory.json',
        'completedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'counts':counts,'issues':rows,
        'newIssues':new,'primaryReconciliation':'Astra; requirement-by-requirement public dispositions, no pending model escalation',
        'evidenceCommit':approval['evidenceCommit'],'productionRuntimeChangedDuringAudit':False}
dump(R/'ledger.json',ledger)
dump(out/'main.json',{'sha':main})
pr38=gh('api',f'repos/{REPO}/pulls/38'); dump(out/'pr38.json',pr38)
assert pr38['state']=='open' and not pr38['merged']
report=['# Astra reconciled remaining-work report','',
    f'Audited delivered main: `{TARGET}`. All37 initial issues have one published, read-back disposition. '
    f'{counts["closedByAudit"]} were closed completed by this audit; {counts["remainingOpen"]} remain open. '
    'The open increments preserve completed work and require separately authorized implementation/review; this audit did not implement them.','',
    'The model-current precipitation amendment is explicitly reconciled on #36: presentation may show supported current model rain/snow without direct-observation authority. '
    'The new immediate complete-celestial startup requirement stays on #33/R0021; the existing rollout acquisition/replacement checks do not satisfy it. '
    'Native Apple Bash3.2/macOS gaps are evidence gaps, not invented runtime defects. N001/N002 PARTIAL and N003 BLOCKED retain their scoped meanings.','',
    '| Issue / canonical ID | Reviewer | Final state | Published proof / next increment |','|---|---|---|---|']
for row in rows:
    report.append(f'| #{row["number"]} / {row["canonicalId"]} | {row["reviewer"]} | {row["finalState"]} | [Individual disposition]({row["publishedCommentUrl"]}) |')
report+=['','## Remaining obligations','']
for row in recon['issues']:
    if row['disposition'].startswith('CLOSE'):continue
    done=next(x for x in rows if x['number']==row['number'])
    report.extend([f'### #{row["number"]} — {row["canonicalId"]}','',
        f'[Binding matrix and bounded next increment]({done["publishedCommentUrl"]}).',''])
    for gap in row['gaps']:
        report.append('- '+(gap if isinstance(gap,str) else json.dumps(gap,ensure_ascii=False)))
    report.append('')
report+=['No unresolved authority disagreement has been silently converted into a closure. '
         'Historical tests, failed harness attempts, superseded mechanisms and unmet native/documentation cells remain individually identifiable in the linked matrices.','']
(R/'ASTRA_RECONCILIATION.md').write_text('\n'.join(report),encoding='utf-8')
print(json.dumps(counts))
