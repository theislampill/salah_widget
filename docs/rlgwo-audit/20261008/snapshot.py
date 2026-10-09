from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,hashlib,re,datetime
R=Path(__file__).parent;W=Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget');REPO='theislampill/salah_widget'
def gh(*a):
 p=subprocess.run(['gh',*a],cwd=W,capture_output=True,text=True,encoding='utf-8');
 if p.returncode:raise RuntimeError(p.stderr)
 return json.loads(p.stdout)
def pages(endpoint):return [x for page in gh('api',endpoint+('&' if '?' in endpoint else '?')+'per_page=100','--paginate','--slurp') for x in page]
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def digest(v):return hashlib.sha256(v.encode()).hexdigest()
assert not (R/'initial-inventory.json').exists(),'Never overwrite the initial inventory'
items=pages(f'repos/{REPO}/issues?state=open');issues=sorted([x for x in items if 'pull_request' not in x],key=lambda x:x['number']);prs=[x['number'] for x in items if 'pull_request' in x]
started=datetime.datetime.now(datetime.timezone.utc).isoformat();save(R/'raw-open-items.json',items)
def issue_packet(i):
 comments=pages(i['comments_url']);events=pages(i['events_url'])
 canonical=re.search(r'R[0-9A-Fa-f]{4}',i['title'])
 if not canonical:canonical=re.search(r'R[0-9A-Fa-f]{4}',i['body'] or '')
 assert canonical,i['number']
 packet={'capturedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'issue':i,'comments':comments,'events':events,'contract':{'canonicalId':canonical[0].upper(),'bodySha256':digest(i['body'] or ''),'updatedAt':i['updated_at'],'commentRevisions':[{'id':c['id'],'updatedAt':c['updated_at'],'bodySha256':digest(c['body'])} for c in comments]}}
 save(R/f'issues/{i["number"]:02}.json',packet)
 return {'number':i['number'],'canonicalId':canonical[0].upper(),'id':i['id'],'node_id':i['node_id'],'title':i['title'],'url':i['html_url'],'state':i['state'],'bodySha256':packet['contract']['bodySha256'],'updatedAt':i['updated_at'],'comments':len(comments),'packet':f'issues/{i["number"]:02}.json'}
with ThreadPoolExecutor(max_workers=6) as pool:rows=list(pool.map(issue_packet,issues))
partition={'A':[2,3,4,5,6,7],'B':[1,8,9,10,25,32],'C':[11,12,13,14,30,36],'D':[15,16,17,18,31,35],'E':[19,20,21,22,27,28],'F':[23,24,26,29,33,34,37]}
assert sorted(n for ns in partition.values() for n in ns)==[r['number'] for r in rows],('Inventory differs',rows)
for r in rows:r.update(reviewer=next(k for k,ns in partition.items() if r['number'] in ns),AUDIT_SHA=None,disposition='PENDING_AUDIT',publishedCommentUrl=None,closedByAudit=False)
snapshot={'repository':REPO,'startedAtUtc':started,'completedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pagination':'GitHub REST per_page100, --paginate --slurp for every list','initialIssueCount':len(rows),'excludedPullRequests':prs,'initialNumbers':[r['number'] for r in rows],'expectedDifference':sorted(set(range(1,38))^set(r['number'] for r in rows)),'partition':partition,'issues':rows}
save(R/'initial-inventory.json',snapshot);save(R/'ledger.json',snapshot)
for name,path in [('pr42','pulls/42'),('reviews','pulls/42/reviews'),('review-comments','pulls/42/comments'),('pr-comments','issues/42/comments'),('pr-commits','pulls/42/commits'),('main','branches/main'),('rulesets','rulesets'),('pages','pages')]:
 data=pages(f'repos/{REPO}/{path}') if name in ['reviews','review-comments','pr-comments','pr-commits','rulesets'] else gh('api',f'repos/{REPO}/{path}')
 save(R/'starting-state'/f'{name}.json',data)
print(json.dumps({'issues':len(rows),'numbers':snapshot['initialNumbers'],'excludedPRs':prs,'comments':sum(r['comments'] for r in rows),'partition':partition},indent=2))
