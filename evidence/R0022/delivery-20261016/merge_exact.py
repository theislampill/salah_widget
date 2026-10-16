"""One owner-approved normal merge, with exact live fences and no blind retry."""
from pathlib import Path
import datetime,json,subprocess
D=Path(__file__).resolve().parent;E=D/'merge-effects';R=Path('C:/Users/theis/.codex/worktrees/r0022-execution/salah_widget')
HEAD='a81644115d951fd3378b0ec738716c71bb4a8673';BASE='fc8d13338f9274a768580cda5a805492f80c510d';TREE='341ab72c6bcc34f3a6e933d0db7910c270e61cbe';REPO='theislampill/salah_widget'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def git(*args):return subprocess.check_output(['git',*args],cwd=R).decode().strip()
def api(path):return json.loads(subprocess.check_output(['gh','api','repos/'+REPO+('/'+path if path else '')]))
def write(name,value):
 with(E/name).open('x',encoding='utf-8')as f:f.write(json.dumps(value,indent=2)+'\n')
def main():
 assert not E.exists(),'Reconcile actual previous effect; do not retry this operation blindly'
 approval=json.loads((D/'OWNER-APPROVAL.json').read_bytes());assert approval['head']==HEAD and approval['base']==BASE and approval['acceptedTree']==TREE
 assert git('rev-parse','HEAD')==HEAD and git('rev-parse','HEAD^{tree}')==TREE and not git('status','--porcelain')
 assert git('remote','get-url','origin')=='https://github.com/'+REPO+'.git'
 subprocess.run(['git','merge-base','--is-ancestor',BASE,HEAD],cwd=R,check=True)
 repo=api('');rules=api('rules/branches/main');branch=api('branches/main');pr=api('pulls/66');issue=api('issues/34');pages=api('pages')
 view=json.loads(subprocess.check_output(['gh','pr','view','66','--repo',REPO,'--json','closingIssuesReferences,statusCheckRollup']))
 assert repo['allow_merge_commit']and repo['default_branch']=='main'and not rules and not branch['protected']
 assert not branch['protection']['required_status_checks']['contexts']and branch['commit']['sha']==BASE
 assert pr['head']['sha']==HEAD and pr['base']['sha']==BASE and pr['head']['ref']=='codex/r0022-lunar-display-h1'and pr['base']['ref']=='main'
 assert pr['state']=='open'and not pr['draft']and pr['merged_at']is None and pr['mergeable']is True and pr['mergeable_state']=='clean'
 assert issue['state']=='open'and not view['closingIssuesReferences']and pages['source']=={'branch':'main','path':'/'}and pages['build_type']=='legacy'
 assert all(c.get('status')=='COMPLETED'and c.get('conclusion')in ['SUCCESS','SKIPPED','NEUTRAL']for c in view['statusCheckRollup'])
 E.mkdir();write('preflight.json',{'atUtc':now(),'head':HEAD,'base':BASE,'tree':TREE,'branch':branch,'rules':rules,'pr':{k:pr[k]for k in ['state','draft','merged_at','mergeable','mergeable_state','head','base']},'issue34':{'state':issue['state'],'state_reason':issue['state_reason']},'view':view,'pages':pages,'normalMergeAllowed':repo['allow_merge_commit']})
 payload={'sha':HEAD,'merge_method':'merge','commit_title':'Merge pull request #66 from theislampill/codex/r0022-lunar-display-h1','commit_message':'Apply the owner-approved bounded H1 lunar display and qualified material-projection cache. Implements #34. Certificate-first completed closure follows independent production delivery verification.\n\nCo-Authored-By: Codex <noreply@openai.com>'}
 write('merge-request.json',payload)
 # Last fresh identity read immediately before the single irreversible request.
 p=api('pulls/66');assert p['head']['sha']==HEAD and p['base']['sha']==BASE and p['mergeable']is True and p['mergeable_state']=='clean'and api('git/ref/heads/main')['object']['sha']==BASE
 write('effect-intent.json',{'atUtc':now(),'head':HEAD,'base':BASE,'method':'merge','ownerApproval':'../OWNER-APPROVAL.json'})
 result=subprocess.run(['gh','api','--method','PUT','repos/'+REPO+'/pulls/66/merge','--input',str(E/'merge-request.json')],capture_output=True)
 write('merge-response.json',{'atUtc':now(),'exitCode':result.returncode,'stdout':result.stdout.decode(),'stderr':result.stderr.decode()});assert result.returncode==0,'Unknown effect must be reconciled from GitHub before retry'
 merged=json.loads(result.stdout);assert merged['merged']is True;sha=merged['sha']
 commit=api('git/commits/'+sha);p=api('pulls/66');ref=api('git/ref/heads/main');issue=api('issues/34')
 assert[p['sha']for p in commit['parents']]==[BASE,HEAD]and commit['tree']['sha']==TREE
 assert p['merged_at']and p['merge_commit_sha']==sha and ref['object']['sha']==sha and issue['state']=='open'
 subprocess.run(['git','fetch','origin','refs/heads/main:refs/remotes/origin/main'],cwd=R,check=True,capture_output=True)
 assert git('rev-parse',sha+'^{tree}')==TREE and git('rev-parse','HEAD')==HEAD and not git('status','--porcelain')
 write('readback.json',{'atUtc':now(),'merge':sha,'parents':[BASE,HEAD],'tree':TREE,'main':ref['object']['sha'],'mergedAt':p['merged_at'],'issue34':{'state':issue['state'],'state_reason':issue['state_reason']},'sourceWorktreeClean':True,'sourceHead':HEAD,'runtime':'558a8b609e2288a90234eaee38ede8847fb38aa8bbece14a692d57610a0799ce'})
 print(json.dumps({'merge':sha,'parents':[BASE,HEAD],'tree':TREE,'issue34':issue['state']}))
if __name__=='__main__':main()
