from pathlib import Path
import datetime as dt
import hashlib
import json
import re

P=Path('C:/Users/theis/Documents/Codex/rlgwo-execution-plan-20261008')
ids={19:'R0013',20:'R0014',21:'R0015',22:'R0016',27:'R001B',28:'R001C'}
records=[]
for number,cid in ids.items():
    paths=[f'REMAINING_RLGWOs/{cid}.md',f'comments/{number:02}.md',f'metadata/{cid}.json']
    doc=(P/paths[0]).read_text(encoding='utf-8')
    references=dict(re.findall(r'^\[(E\d+)\]: (.+)$',doc,re.M))
    used=re.findall(r'\[(E\d+)\]',doc)
    assert all(key in references for key in used)
    published=doc.replace('SPEC_EVIDENCE_COMMIT','0'*40)
    assert len(published)<65536,(number,len(published))
    metadata=json.loads((P/paths[2]).read_text(encoding='utf-8'))
    assert metadata['readiness']=='AWAITING_COLD_REVIEW'
    assert metadata['closure']['deliveryMode']=='docs-merge'
    for path in paths:
        b=(P/path).read_bytes()
        records.append(dict(path=path,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),
                            issue=number,canonicalId=cid))
for name in ['AUTHOR_REVIEW.md','custody.json','artifact-validation.json','author_specs.py','freeze_specs.py']:
    path=f'workers/E/{name}';b=(P/path).read_bytes()
    records.append(dict(path=path,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)))
result=dict(schema='rlgwo.spec.author-freeze.v1',author='E',stage='AUTHOR_FREEZE',
            readiness='AWAITING_COLD_REVIEW',capturedAtUtc=dt.datetime.now(dt.timezone.utc).isoformat(),
            sourceTarget='18ff14860ff41c084b1db5f396bb62aa9c22b1be',
            auditEvidenceCommit='b879573c298f19189d1f2392108b8b9f3b2cda0b',
            checks=dict(referenceDefinitionsComplete=True,commentLimitWithBoundCommit=True,
                        explicitDocsMergeMode=True,noProductOrExternalEffects=True),
            files=records,
            next='Independent F cold-reader reviews exact frozen specs/comments/metadata; primary reconciles global DAG. No publication/execution/readiness claim.')
path=P/'workers/E/AUTHOR_FREEZE.json'
assert path.resolve().is_relative_to((P/'workers/E').resolve())
path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(stage=result['stage'],readiness=result['readiness'],files=len(records),
                      freezeSha256=hashlib.sha256(path.read_bytes()).hexdigest(),checks=result['checks']),indent=2))
