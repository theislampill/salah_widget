"""One issue, approved immutable comment, durable readback-before-close sequence."""
from pathlib import Path
import argparse, hashlib, json, subprocess, datetime

ROOT = Path(__file__).resolve().parent
REPO = 'theislampill/salah_widget'
TARGET = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'

def gh(*args, data=None):
    command = ['gh', *args]
    p = subprocess.run(command, input=json.dumps(data) if data is not None else None,
                       text=True, encoding='utf-8', capture_output=True)
    if p.returncode:
        raise RuntimeError(f'{command}: {p.returncode}: {p.stderr}')
    return p.stdout

def api(path, method=None, data=None):
    args = ['api', path]
    if method:
        args += ['--method', method]
    if data is not None:
        args += ['--input', '-']
    return json.loads(gh(*args, data=data))

def pages(path):
    result = json.loads(gh('api', path + ('&' if '?' in path else '?') + 'per_page=100', '--paginate', '--slurp'))
    return [item for page in result for item in page]

def dump(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(path)

def textnorm(value):
    return value.replace('\r\n', '\n')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--issue', type=int, required=True)
    ap.add_argument('--reviewer', choices=list('ABCDEF'), required=True)
    ap.add_argument('--approval', type=Path, required=True)
    args = ap.parse_args()
    approvals = json.loads(args.approval.read_text(encoding='utf-8'))
    approved = next(x for x in approvals['issues'] if x['number'] == args.issue)
    assert approvals['AUDIT_SHA'] == TARGET and approved['approved'] is True
    assert approved['reviewer'] == args.reviewer
    comment = ROOT / approved['commentPath']
    raw = comment.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == approved['commentSha256'], 'Approved comment changed'
    body = raw.decode('utf-8')
    marker = f'<!-- RLGWO-AUDIT:{TARGET}:{approved["canonicalId"]}:2026-10-08 -->'
    assert body.count(marker) == 1
    assert len(body) < 65536
    assert 'RLGWO closure ' in body
    packet = json.loads((ROOT / f'issues/{args.issue:02d}.json').read_text(encoding='utf-8'))
    receipt_path = ROOT / f'workers/{args.reviewer}/{args.issue:02d}-publication.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.exists() else {
        'number': args.issue, 'reviewer': args.reviewer, 'mechanicalPublisher': f'worker {args.reviewer}',
        'AUDIT_SHA': TARGET, 'commentSha256': approved['commentSha256'], 'closedByAudit': False, 'steps': []}
    def record(kind, data):
        receipt['steps'].append({'atUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'kind': kind, 'data': data})
        dump(receipt_path, receipt)
    mainref = api(f'repos/{REPO}/git/ref/heads/main')['object']['sha']
    assert mainref == TARGET, f'Audit target changed: {mainref}'
    issue = api(f'repos/{REPO}/issues/{args.issue}')
    assert 'pull_request' not in issue
    assert issue['id'] == packet['issue']['id']
    current_body_hash = hashlib.sha256(issue['body'].encode('utf-8')).hexdigest()
    assert current_body_hash == approved['bodySha256'], 'Issue contract changed; primary reconciliation required'
    comments = pages(f'repos/{REPO}/issues/{args.issue}/comments')
    own = [x for x in comments if marker in x['body']]
    assert len(own) <= 1, 'Duplicate stable marker requires reconciliation'
    known = set(approved.get('reviewedCommentIds', []))
    new = [x for x in comments if x['id'] not in known and marker not in x['body']]
    assert not new, f'New discussion needs reconciliation: {[x["html_url"] for x in new]}'
    record('fresh-preconditions', {'main': mainref, 'bodySha256': current_body_hash, 'state': issue['state'],
                                  'stateReason': issue.get('state_reason'), 'commentIds': [x['id'] for x in comments]})
    if own:
        posted = own[0]
        assert textnorm(posted['body']) == textnorm(body), 'Prior stable-marker comment differs'
        record('reuse-existing-proof', {'id': posted['id'], 'url': posted['html_url']})
    else:
        posted = api(f'repos/{REPO}/issues/{args.issue}/comments', 'POST', {'body': body})
        record('proof-posted', {'id': posted['id'], 'url': posted['html_url']})
    readback = api(f'repos/{REPO}/issues/comments/{posted["id"]}')
    assert textnorm(readback['body']) == textnorm(body), 'Posted proof readback mismatch'
    receipt['publishedCommentUrl'] = readback['html_url']
    receipt['publishedCommentId'] = readback['id']
    receipt['disposition'] = approved['disposition']
    record('proof-readback-verified', {'id': readback['id'], 'url': readback['html_url'], 'bodySha256': hashlib.sha256(textnorm(readback['body']).encode()).hexdigest()})
    current = api(f'repos/{REPO}/issues/{args.issue}')
    assert hashlib.sha256(current['body'].encode('utf-8')).hexdigest() == approved['bodySha256'], 'Contract changed during publication'
    if approved['disposition'].startswith('CLOSE'):
        if current['state'] == 'open':
            assert api(f'repos/{REPO}/git/ref/heads/main')['object']['sha'] == TARGET
            close_comments = pages(f'repos/{REPO}/issues/{args.issue}/comments')
            assert all(x['id'] in known or x['id'] == posted['id'] for x in close_comments), 'Intervening discussion before closure'
            record('close-request-started', {'reason': 'completed'})
            output = gh('issue', 'close', str(args.issue), '--repo', REPO, '--reason', 'completed')
            receipt['closedByAudit'] = True
            record('close-command-returned', {'output': output})
        elif not receipt.get('closedByAudit'):
            receipt['independentlyOrAlreadyClosed'] = True
    final = api(f'repos/{REPO}/issues/{args.issue}')
    if approved['disposition'].startswith('CLOSE'):
        assert final['state'] == 'closed' and final.get('state_reason') == 'completed'
    receipt['finalState'] = final['state']
    receipt['finalStateReason'] = final.get('state_reason')
    receipt['finalUpdatedAt'] = final['updated_at']
    receipt['status'] = 'VERIFIED'
    record('final-readback', {'state': final['state'], 'reason': final.get('state_reason'), 'closedAt': final.get('closed_at')})
    print(json.dumps({k: receipt.get(k) for k in ['number', 'disposition', 'publishedCommentUrl', 'closedByAudit', 'finalState', 'finalStateReason', 'status']}))

if __name__ == '__main__':
    main()
