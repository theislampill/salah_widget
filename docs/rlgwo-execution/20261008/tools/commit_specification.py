"""Publish authorized planning documents on existing docs branch via isolated index."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import time

TARGET='18ff14860ff41c084b1db5f396bb62aa9c22b1be'
BRANCH='codex/rlgwo-closure-audit-20261008'
PREFIX='docs/rlgwo-execution/20261008/'


def origin_allowed(url):
    return url.lower().rstrip('/') in {
        'https://github.com/theislampill/salah_widget',
        'https://github.com/theislampill/salah_widget.git',
        'git@github.com:theislampill/salah_widget',
        'git@github.com:theislampill/salah_widget.git',
        'ssh://git@github.com/theislampill/salah_widget',
        'ssh://git@github.com/theislampill/salah_widget.git'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repository',required=True,type=Path);ap.add_argument('--staging',required=True,type=Path)
    ap.add_argument('--parent',required=True);ap.add_argument('--receipt',required=True,type=Path)
    ap.add_argument('--subject',required=True);args=ap.parse_args()
    assert not args.receipt.exists(),'Preserve existing effect receipt; recover its exact effect identity before retry'
    ordinary=subprocess.check_output(['git','status','--porcelain'],cwd=args.repository)
    assert not ordinary,'Reviewed checkout dirty; reconcile instead of overwriting'
    env=dict(os.environ);env['GIT_INDEX_FILE']=str(args.receipt.parent/f'spec-index-{time.time_ns()}')
    def git(*cmd,data=None):
        p=subprocess.run(['git',*cmd],cwd=args.repository,env=env,input=data,capture_output=True)
        if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
        return p.stdout
    def mainref():return json.loads(subprocess.check_output(['gh','api','repos/theislampill/salah_widget/git/ref/heads/main']))['object']['sha']
    fetch_urls=git('remote','get-url','--all','origin').decode().splitlines()
    push_urls=git('remote','get-url','--push','--all','origin').decode().splitlines()
    assert fetch_urls and push_urls and all(origin_allowed(u) for u in fetch_urls+push_urls),'Unexpected origin fetch/push repository; no Git writes performed'
    assert mainref()==TARGET,'Main drift requires reconciliation'
    assert git('ls-remote','--heads','origin',f'refs/heads/{BRANCH}').decode().split()[0]==args.parent
    git('read-tree',args.parent);entries=[]
    for p in sorted(args.staging.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(args.staging).as_posix()
        assert rel.startswith(PREFIX) and '\t' not in rel and '\n' not in rel
        assert '__pycache__' not in p.parts and p.suffix.lower() not in {'.pyc','.ttf','.woff','.woff2','.exe','.zip'}
        blob=git('hash-object','-w','--stdin',data=p.read_bytes()).decode().strip()
        entries.append(f'100644 {blob}\t{rel}\n')
    assert entries
    git('update-index','--index-info',data=''.join(entries).encode())
    tree=git('write-tree').decode().strip();diff=git('diff','--name-status',args.parent,tree).decode()
    assert diff
    for line in diff.splitlines():
        status,path=line.split('\t',1);assert status in {'A','M'} and path.startswith(PREFIX),line
    message=(args.subject+'\n\nExecutable remaining-work specifications for delivered main '+TARGET+'.\n'
             'Documentation and planning only; no runtime, V1, merge, deployment or issue-state change.\n\n'
             'Co-Authored-By: Codex <noreply@openai.com>\n')
    commit=git('commit-tree',tree,'-p',args.parent,data=message.encode()).decode().strip()
    receipt={'branch':BRANCH,'parent':args.parent,'commit':commit,'tree':tree,'sourceTarget':TARGET,'files':len(entries),
             'originFetchUrls':fetch_urls,'originPushUrls':push_urls,
             'diff':diff,'status':'LOCAL_DOCS_COMMIT_CREATED'}
    def save():args.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
    save()
    git('update-ref',f'refs/heads/{BRANCH}',commit,args.parent)
    receipt['status']='LOCAL_DOCS_REF_UPDATED';save()
    git('push','origin',f'{commit}:refs/heads/{BRANCH}')
    assert git('ls-remote','--heads','origin',f'refs/heads/{BRANCH}').decode().split()[0]==commit
    assert mainref()==TARGET
    assert subprocess.check_output(['git','status','--porcelain'],cwd=args.repository)==ordinary
    receipt['status']='PUSHED_READBACK_VERIFIED_MAIN_AND_WORKTREE_UNCHANGED';save()
    print(json.dumps({k:receipt[k] for k in ('commit','tree','files','status')}))


if __name__=='__main__':main()
