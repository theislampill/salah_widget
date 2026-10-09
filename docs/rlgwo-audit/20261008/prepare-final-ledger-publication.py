"""Stage final effect readbacks after all37 individual writes are verified."""
from pathlib import Path
import hashlib, json

R=Path(__file__).resolve().parent
out=R/'public-ledger-01'
assert not out.exists(), 'Preserve previous publication staging'
prefix=Path('docs/rlgwo-audit/20261008')
ledger=json.loads((R/'ledger.json').read_text(encoding='utf-8'))
assert ledger['counts']['reviewed']==37 and ledger['counts']['evidenceCommented']==37
assert len(ledger['issues'])==37
assert all(not x['additionalDiscussionIds'] for x in ledger['issues']), 'New discussion needs reconciliation'
readme=(R/'README.md').read_text(encoding='utf-8')
intro=(f'\n**Completed audit:**37 reviewed and individually evidence-commented; '
       f'{ledger["counts"]["closedByAudit"]} closed completed by this audit, '
       f'{ledger["counts"]["independentlyOrAlreadyClosed"]} independently/already closed, '
       f'{ledger["counts"]["remainingOpen"]} remaining open. '
       '[Final ledger](ledger.json) · [Astra remaining-work report and all37 comment links](ASTRA_RECONCILIATION.md) · '
       '[Independent final issue/comment/state readbacks](final-readback) · [Final public root/V1 currentness](final-public-currentness.json).\n')
lines=readme.split('\n',2);readme=lines[0]+'\n'+intro+'\n'+lines[2]
readme+='\nThe immutable original source/receipt packet is commit `'+ledger['evidenceCommit']+'`. The present commit adds final approved comment copies and actual effect readbacks. Prior pre-publication recommendations remain historical; final states are in the ledger.\n'
files=[R/x for x in ['ledger.json','ASTRA_RECONCILIATION.md','approved-publication.json','primary-reconciliation.json',
    'public-evidence-readback.json','evidence-publication-01.json','final-public-currentness.json',
    'publication-link-check.json','bind-comments.py','final-readback.py','final-public-currentness.py',
    'prepare-final-ledger-publication.py','commit-evidence.py','verify-evidence-public.py']]
files+=sorted((R/'approved-comments').glob('*.md'))
files+=sorted((R/'workers').glob('*/*-publication.json'))
files+=sorted((R/'final-readback').glob('*.json'))
records=[]
for src in files:
    rel=src.relative_to(R);raw=src.read_bytes();dest=out/prefix/rel
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    records.append({'path':str(prefix/rel).replace('\\','/'),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
dest=out/prefix/'README.md';raw=readme.encode();dest.write_bytes(raw)
records.append({'path':str(prefix/'README.md').replace('\\','/'),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
manifest={'AUDIT_SHA':ledger['AUDIT_SHA'],'evidenceCommit':ledger['evidenceCommit'],'purpose':'Final individual publication/closure effects and remaining-work reconciliation','files':records}
(out/prefix/'FINAL_AUDIT_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'out':str(out),'files':len(records)+1,'counts':ledger['counts']}))
