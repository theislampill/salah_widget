"""Publish one primary-approved remaining-work revision; never change issue state."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = 'theislampill/salah_widget'
TARGET = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'


def gh(*args, payload=None):
    p = subprocess.run(['gh', *args], input=json.dumps(payload) if payload is not None else None,
                       text=True, encoding='utf-8', capture_output=True)
    if p.returncode:
        raise RuntimeError(f'GitHub command failed ({p.returncode}): {p.stderr}')
    return p.stdout


def api(path, payload=None):
    # Only this module's explicit issue-comment POST is permitted; no PATCH,
    # closure, issue-body edit, merge, label, branch or production write path.
    return json.loads(gh('api', path, *(['--method', 'POST', '--input', '-'] if payload is not None else []), payload=payload))


def pages(path):
    return [item for page in json.loads(gh('api', path + '?per_page=100', '--paginate', '--slurp')) for item in page]


def dump(path, obj):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    tmp.replace(path)


def norm(s):
    return s.replace('\r\n', '\n')


def receipt_identity_matches(receipt, expected):
    return all(receipt.get(k)==v for k,v in expected.items())


def poststate_errors(target, packet, current, comments, marker, body, posted_id):
    errors=[]
    if target!=TARGET:errors.append('Main drift after publication')
    original=packet['issue']
    for key in ('id','title','body','state'):
        if norm(str(current.get(key)))!=norm(str(original.get(key))):errors.append(f'Issue {key} changed after publication')
    expected={x['id']:norm(x['body']) for x in packet['comments']}
    expected[posted_id]=norm(body)
    if {x['id']:norm(x['body']) for x in comments}!=expected:errors.append('Discussion added/deleted/edited after publication')
    owners=[x for x in comments if marker in x['body']]
    if len(owners)!=1 or owners[0]['id']!=posted_id or norm(owners[0]['body'])!=norm(body):errors.append('Exact publication marker/identity mismatch')
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--issue', required=True, type=int)
    parser.add_argument('--approval', required=True, type=Path)
    args = parser.parse_args()
    approval = json.loads(args.approval.read_text(encoding='utf-8'))
    assert approval['sourceTarget'] == TARGET
    item = next(x for x in approval['issues'] if x['number'] == args.issue)
    assert item['primaryApproved'] is True and item['coldReadDisposition'] == 'PASS'
    content = (ROOT / item['commentPath']).read_bytes()
    assert hashlib.sha256(content).hexdigest() == item['commentSha256']
    body = content.decode('utf-8')
    canonical, revision = item['canonicalId'], item['revision']
    marker = f'<!-- RLGWO-SPEC:{TARGET}:{canonical}:rev{revision}:2026-10-08 -->'
    assert body.count(marker) == 1 and len(body) < 65536
    assert f'RLGWO remaining-work specification — {canonical} — revision {revision}' in body
    assert 'SPEC_EVIDENCE_COMMIT' not in body
    packet = json.loads((ROOT / f'issues/{args.issue:02d}.json').read_text(encoding='utf-8'))
    directory = ROOT / 'publication'
    directory.mkdir(exist_ok=True)
    path = directory / f'{args.issue:02d}-rev{revision}.json'
    receipt = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {
        'number': args.issue, 'canonicalId': canonical, 'revision': revision,
        'sourceTarget': TARGET, 'specificationCommit': approval['specificationCommit'],
        'author': item['author'], 'coldReviewer': item['coldReviewer'],
        'mechanicalPublisher': 'primary coordinator', 'commentSha256': item['commentSha256'],
        'issueStateMutationAuthorized': False, 'steps': []}
    expected_identity={'number':args.issue,'canonicalId':canonical,'revision':revision,
                       'sourceTarget':TARGET,'specificationCommit':approval['specificationCommit'],
                       'commentSha256':item['commentSha256']}
    assert receipt_identity_matches(receipt,expected_identity),'Existing receipt belongs to different effect identity; preserve and reconcile before retry'

    def record(kind, value):
        receipt['steps'].append({'atUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'kind': kind, 'value': value})
        dump(path, receipt)

    assert api(f'repos/{REPO}/git/ref/heads/main')['object']['sha'] == TARGET, 'Main drift requires reconciliation'
    current = api(f'repos/{REPO}/issues/{args.issue}')
    assert 'pull_request' not in current and current['id'] == packet['issue']['id']
    assert current['title']==packet['issue']['title'], 'Issue title/identity changed; reconcile'
    assert current['state'] == packet['issue']['state'] == 'open', 'Issue state changed; reconcile individually'
    assert hashlib.sha256(current['body'].encode()).hexdigest() == item['bodySha256'], 'Issue contract changed'
    comments = pages(f'repos/{REPO}/issues/{args.issue}/comments')
    own = [x for x in comments if marker in x['body']]
    assert len(own) <= 1, 'Duplicate marker requires reconciliation'
    known = {x['id']: x for x in packet['comments']}
    assert {x['id'] for x in comments if marker not in x['body']}==set(known), 'Discussion added/deleted; reconcile before publication'
    for comment in comments:
        if marker in comment['body']:
            continue
        assert comment['id'] in known, f'Intervening discussion: {comment["html_url"]}'
        assert norm(comment['body']) == norm(known[comment['id']]['body']), f'Edited discussion: {comment["html_url"]}'
    record('preconditions-verified', {'bodySha256': item['bodySha256'], 'state': current['state'], 'commentIds': [x['id'] for x in comments]})
    if own:
        posted = own[0]
        assert norm(posted['body']) == norm(body), 'Existing revision differs; do not edit another comment'
        record('existing-identical-revision', {'id': posted['id'], 'url': posted['html_url']})
    else:
        posted = api(f'repos/{REPO}/issues/{args.issue}/comments', {'body': body})
        record('revision-posted', {'id': posted['id'], 'url': posted['html_url']})
    readback = api(f'repos/{REPO}/issues/comments/{posted["id"]}')
    assert norm(readback['body']) == norm(body)
    final = api(f'repos/{REPO}/issues/{args.issue}')
    final_comments=pages(f'repos/{REPO}/issues/{args.issue}/comments')
    final_main=api(f'repos/{REPO}/git/ref/heads/main')['object']['sha']
    drift=poststate_errors(final_main,packet,final,final_comments,marker,body,posted['id'])
    if drift:
        receipt.update({'status':'PUBLISHED_REQUIRES_RECONCILIATION','commentUrl':readback['html_url'],
                        'commentId':readback['id'],'finalState':final['state'],'postconditionDrift':drift})
        record('postconditions-drift',{'errors':drift,'main':final_main,'commentIds':[x['id'] for x in final_comments]})
        raise RuntimeError('Publication occurred; preserve it and reconcile drift: '+str(drift))
    receipt.update({'status': 'PUBLISHED_READBACK_VERIFIED', 'commentUrl': readback['html_url'],
                    'commentId': readback['id'], 'finalState': final['state'], 'stateChangedByThisProgramme': False})
    record('readback-verified', {'commentSha256Normalized': hashlib.sha256(norm(readback['body']).encode()).hexdigest(), 'state': final['state']})
    print(json.dumps({k: receipt[k] for k in ('number', 'canonicalId', 'revision', 'status', 'commentUrl', 'finalState')}))


if __name__ == '__main__':
    main()
