"""Create primary-approved publication bodies; do not mutate worker proposals."""
from pathlib import Path
import argparse, hashlib, json, re

R = Path(__file__).resolve().parent
TARGET = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
PREFIX = 'docs/rlgwo-audit/20261008/'
ap = argparse.ArgumentParser()
ap.add_argument('--staging', type=Path, required=True)
ap.add_argument('--evidence-sha', default='AUDIT_EVIDENCE_COMMIT')
args = ap.parse_args()
manifest = json.loads((args.staging/PREFIX/'EVIDENCE_MANIFEST.json').read_text(encoding='utf-8'))
recon = json.loads((R/'primary-reconciliation.json').read_text(encoding='utf-8'))
out = R/'approved-comments'
out.mkdir(exist_ok=True)
base = 'https://github.com/theislampill/salah_widget/blob/'
approval = {'AUDIT_SHA':TARGET, 'evidenceCommit':args.evidence_sha,
            'primary':'Astra', 'issues':[]}
for row in recon['issues']:
    n, worker = row['number'], row['reviewer']
    original = R/f'workers/{worker}/{n:02d}-comment.md'
    body = original.read_text(encoding='utf-8')
    # Gzip is lossless custody; links must name the published representation.
    for rec in manifest['records']:
        if rec['compression']:
            old = base+'AUDIT_EVIDENCE_COMMIT/'+PREFIX+rec['source']
            body = body.replace(old, base+'AUDIT_EVIDENCE_COMMIT/'+rec['published'])
    body = body.replace('AUDIT_EVIDENCE_COMMIT', args.evidence_sha)
    common = base+args.evidence_sha+'/'+PREFIX
    body += ('\n\nPrimary publication reconciliation: the complete mandatory matrix and verdict above were reviewed by Astra against the delivered target. '
             'Reviewer '+worker+' performed the independent issue audit; the designated worker mechanically publishes this approved body. '
             'This proof is posted and read back before any justified completed closure.\n\n'
             '- [Exact original issue and discussion]('+common+f'issues/{n:02d}.json'+') · '
             '[Audited release]('+common+'release.json) · [Public runtime/V1 readback]('+common+'public-runtime.json).\n'
             '- [539-row primary reconciliation]('+common+'primary-reconciliation.json) · '
             '[Six reviewer configuration receipts]('+common+'reviewer-model-settings.json) · '
             '[Evidence custody manifest]('+common+'EVIDENCE_MANIFEST.json).\n')
    marker = f'<!-- RLGWO-AUDIT:{TARGET}:{row["canonicalId"]}:2026-10-08 -->'
    assert body.count(marker) == 1, n
    assert len(body) < 65536, (n,len(body))
    assert row['canonicalId'] in body and TARGET in body
    if row['disposition'].startswith('CLOSE'):
        assert 'RLGWO closure proof' in body and not row['gaps']
    else:
        assert 'REMAINS OPEN' in body and 'Next RLGWO increment required for closure' in body
    packet = json.loads((R/f'issues/{n:02d}.json').read_text(encoding='utf-8'))
    bodyhash = hashlib.sha256(packet['issue']['body'].encode('utf-8')).hexdigest()
    dest = out/f'{n:02d}.md'
    dest.write_text(body,encoding='utf-8',newline='\n')
    approval['issues'].append({'number':n,'reviewer':worker,'canonicalId':row['canonicalId'],
        'approved':args.evidence_sha != 'AUDIT_EVIDENCE_COMMIT', 'commentPath':dest.relative_to(R).as_posix(),
        'commentSha256':hashlib.sha256(dest.read_bytes()).hexdigest(), 'bodySha256':bodyhash,
        'disposition':row['disposition'], 'reviewedCommentIds':[x['id'] for x in packet.get('comments',[])],
        'workerOriginalSha256':hashlib.sha256(original.read_bytes()).hexdigest()})
(R/'approved-publication.json').write_text(json.dumps(approval,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'comments':len(approval['issues']),'approved':args.evidence_sha!='AUDIT_EVIDENCE_COMMIT',
                  'maxCharacters':max(len(p.read_text(encoding='utf-8')) for p in out.glob('*.md'))}))
