"""Publish authorized audit documents using an isolated Git index, never a checkout."""
from pathlib import Path
import argparse, json, os, subprocess, time

ROOT = Path(__file__).resolve().parent
WORKTREE = Path(r'C:\Users\theis\.codex\worktrees\hotfix-startup-clouds\salah_widget')
TARGET = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
BRANCH = 'codex/rlgwo-closure-audit-20261008'
PREFIX = 'docs/rlgwo-audit/20261008/'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--staging', type=Path, required=True)
    ap.add_argument('--parent', default=TARGET)
    ap.add_argument('--receipt', type=Path, required=True)
    ap.add_argument('--subject', required=True)
    args = ap.parse_args()
    assert not args.receipt.exists(), 'Preserve prior publication receipt'
    env = dict(os.environ)
    index = ROOT / f'evidence-index-{time.time_ns()}'
    env['GIT_INDEX_FILE'] = str(index)
    def git(*cmd, data=None):
        proc = subprocess.run(['git', *cmd], cwd=WORKTREE, env=env, input=data, capture_output=True)
        if proc.returncode:
            raise RuntimeError(proc.stderr.decode('utf-8', errors='replace'))
        return proc.stdout
    # Use ordinary index for custody check; isolated index is not initialized yet.
    ordinary = subprocess.check_output(['git', 'status', '--porcelain'], cwd=WORKTREE).decode()
    assert ordinary == '', 'Unexpected working-tree drift'
    mainref = json.loads(subprocess.check_output(['gh', 'api', 'repos/theislampill/salah_widget/git/ref/heads/main'], text=True))['object']['sha']
    assert mainref == TARGET
    remote = git('ls-remote', '--heads', 'origin', f'refs/heads/{BRANCH}').decode().strip()
    if args.parent == TARGET:
        assert not remote, 'Existing audit branch must be reconciled, never overwritten'
    else:
        assert remote.split()[0] == args.parent, 'Audit branch moved'
    git('read-tree', args.parent)
    entries = []
    for file in sorted(args.staging.rglob('*')):
        if not file.is_file():
            continue
        relative = file.relative_to(args.staging).as_posix()
        assert relative.startswith(PREFIX) and '\t' not in relative and '\n' not in relative
        blob = git('hash-object', '-w', '--stdin', data=file.read_bytes()).decode().strip()
        entries.append(f'100644 {blob}\t{relative}\n')
    assert entries
    git('update-index', '--index-info', data=''.join(entries).encode())
    tree = git('write-tree').decode().strip()
    changes = git('diff', '--name-status', args.parent, tree).decode()
    for line in changes.splitlines():
        status, path = line.split('\t', 1)
        assert status in {'A', 'M'} and path.startswith(PREFIX), line
    assert changes, 'No evidence change'
    message = (args.subject + '\n\nRecord issue-specific evidence for delivered main ' + TARGET + '.\n'
               'Documentation only; no widget, frozen V1 or deployment change.\n\n'
               'Co-Authored-By: Codex <noreply@openai.com>\n')
    commit = git('commit-tree', tree, '-p', args.parent, data=message.encode()).decode().strip()
    receipt = {'branch': BRANCH, 'parent': args.parent, 'commit': commit, 'tree': tree,
               'AUDIT_SHA': TARGET, 'files': len(entries), 'diff': changes, 'status': 'LOCAL_COMMIT_CREATED'}
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    # A normal ref update and normal push only. No checkout, force, main write or PR.
    git('update-ref', f'refs/heads/{BRANCH}', commit, args.parent if remote else '0' * 40)
    receipt['pushOutput'] = git('push', 'origin', f'{commit}:refs/heads/{BRANCH}').decode()
    readback = git('ls-remote', '--heads', 'origin', f'refs/heads/{BRANCH}').decode().split()[0]
    assert readback == commit
    assert json.loads(subprocess.check_output(['gh', 'api', 'repos/theislampill/salah_widget/git/ref/heads/main'], text=True))['object']['sha'] == TARGET
    assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=WORKTREE).decode() == ''
    receipt['status'] = 'PUSHED_REMOTE_HEAD_VERIFIED_MAIN_UNCHANGED'
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: receipt[k] for k in ['commit', 'tree', 'files', 'status']}))

if __name__ == '__main__':
    main()
