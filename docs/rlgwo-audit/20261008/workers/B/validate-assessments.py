import json, subprocess, hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent
REPO=Path('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget')
SHA='18ff14860ff41c084b1db5f396bb62aa9c22b1be'
cache={};errors=[];seen=set();counts={}
for number in [1,8,9,10,25,32]:
    doc=json.loads((OUT/f'{number:02}-assessment.json').read_text(encoding='utf-8'))
    expected_verdict='CLOSE — SATISFIED' if number in [1,9,10] else 'LEAVE OPEN'
    assert doc['issueNumber']==number and doc['target']['commit']==SHA and doc['verdict']==expected_verdict
    text=(OUT/f'{number:02}-comment.md').read_text(encoding='utf-8')
    assert f'<!-- RLGWO-AUDIT:{SHA}:{doc["canonicalId"]}:2026-10-08 -->' in text
    reconciled=doc.get('publicationTextStatus')=='PRIMARY_RECONCILED_AWAITING_IMMUTABLE_SHA_BINDING'
    if reconciled:
        assert doc['primaryReconciliation']['status']=='APPROVED'
        assert 'Primary Astra reconciled' in text or 'Primary Astra read the complete mandatory matrix' in text
        assert 'AUDIT_EVIDENCE_COMMIT/docs/rlgwo-audit/20261008/' in text
        assert 'unposted proposal' not in text and 'not yet primary-reconciled' not in text and 'This comment is proposed' not in text
    if number in [1,9,10]:
        assert not doc['gaps'] and not doc['missingChecksRequested']
        if reconciled:assert 'This proof precedes manual closure' in text
        else:assert 'Publication hold' in text and 'not posted' in text
        assert all(r['disposition'] in {'satisfied','validly superseded'} for r in doc['fullRequirementMatrix'])
        assert doc['primaryNativeExecution']['uniqueCases']=={1:12,9:14,10:4}[number]
    else:
        assert 'Next RLGWO increment required for closure' in text
        if not reconciled:assert 'not yet primary-reconciled or posted' in text
    for row in doc['fullRequirementMatrix']:
        assert row['mandatory'] and row['disposition'] in {'satisfied','validly superseded','unmet','unverified'}
        assert row['id'] not in seen;seen.add(row['id'])
        for field in ['authoredOwner','deliveredConsumer','discriminator']:
            ref=row[field];path=ref['path']
            if path not in cache:
                data=subprocess.check_output(['git','-C',str(REPO),'show',SHA+':'+path]);current=(REPO/path).read_bytes()
                assert data==current,(path,'not identical target bytes')
                cache[path]=data.decode('utf-8-sig').splitlines()
            if not 1<=ref['start']<=ref['end']<=len(cache[path]):errors.append({'issue':number,'row':row['id'],'field':field,'ref':ref,'actualLines':len(cache[path])})
            assert SHA in ref['url'] and f'#L{ref["start"]}' in ref['url']
    counts[str(number)]={'obligations':len(doc['fullRequirementMatrix']),'states':{s:sum(r['disposition']==s for r in doc['fullRequirementMatrix']) for s in ['satisfied','validly superseded','unmet','unverified']}}
assert json.loads((OUT/'summary.json').read_text())['freshChecks']['sourceCases']==157
result={'schema':'rlgwo-B-output-validation/1','target':SHA,'filesChecked':len(cache),'obligationCounts':counts,'errors':errors,'allStructuredFilesParsed':True,'sourceTargetBytesMatched':True,'stableMarkersChecked':True}
(OUT/'output-validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));raise SystemExit(bool(errors))
