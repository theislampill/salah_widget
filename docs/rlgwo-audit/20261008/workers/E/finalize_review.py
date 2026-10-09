"""Validate local review artifacts and tailor inline receipts to each issue."""
import hashlib
import json
import pathlib
import re
import runpy

root = pathlib.Path(__file__).resolve().parent
runpy.run_path(str(root/'polish_review.py'), run_name='__main__')
old = pathlib.Path('C:/Users/theis/.codex/work-products/salah-rlgwo-execution-20261002/evidence/install')
expected = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
keep = {
 19: {'Linux','Apple'}, 20: {'Windows'}, 21: {'Linux','DAC','Apple'}, 22: {'Windows','Linux','Apple'},
}
hash_keep = {
 19: {'bash-helper-archived-source.json','bash-entry-archived-source.json'},
 20: {'final-r0014-ps51.txt','final-r0014-ps7.txt','direct-native-final.json'},
 21: {'bash-helper-archived-source.json','crossuid-nonlogin/result.json'},
 22: {'final-r0014-ps51.txt','final-r0014-ps7.txt','direct-native-final.json','bash-helper-archived-source.json','bash-entry-archived-source.json'},
}
for n in (19,20,21,22,27,28):
    path = root/f'{n}-assessment.json'
    assessment = json.loads(path.read_text(encoding='utf-8'))
    assert assessment['issue'] == n and assessment['target']['commit'] == expected
    assert assessment['verdict'] == 'LEAVE OPEN'
    assert assessment['publicationStatus'] == 'PROPOSED_ONLY_NOT_RECONCILED_NOT_POSTED'
    assert len(assessment['requirementMatrix']) >= 10
    assert all(r['status'] in ('satisfied','validly superseded','unmet','unverified') for r in assessment['requirementMatrix'])
    if n == 20: assessment['historicalCommands'] = assessment['historicalCommands'][:1]
    if n == 19: assessment['historicalCommands'] = assessment['historicalCommands'][1:2]
    if n == 21: assessment['historicalCommands'] = assessment['historicalCommands'][1:]
    if n == 22: assessment['historicalCommands'] = assessment['historicalCommands'][:2]
    path.write_text(json.dumps(assessment,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    path = root/f'{n}-comment.md'
    text = path.read_text(encoding='utf-8')
    assert f'<!-- RLGWO-AUDIT:{expected}:{assessment["canonicalId"]}:2026-10-08 -->' in text
    assert 'Next RLGWO increment required for closure' in text
    if n in keep:
        match = re.search(r'```json\n(.*?)\n```',text,re.S)
        core = json.loads(match[1])
        core['reused_native']={k:v for k,v in core['reused_native'].items() if k in keep[n]}
        core['receipt_hashes']={k:v for k,v in core['receipt_hashes'].items() if k in hash_keep[n]}
        if n == 20:
            core['limits'] = ['Retained exact-source observations, not newly executed native suites.',
                              'Filename tiers do not authenticate signatures or prove Firefox ZIP installability; no real browser installation/import is claimed.',
                              'Actual Apple evidence is not a requirement of this Windows issue.']
        text=text[:match.start(1)]+json.dumps(core,indent=2)+text[match.end(1):]
    path.write_text(text,encoding='utf-8')

native = json.loads((root/'native-rebind.json').read_text(encoding='utf-8'))
assert native['target']['checkoutStatus'] == ''
assert native['target']['examinedCheckoutTree'] == native['target']['tree']
assert all(r.get('source_or_fixture_identical',True) for r in native['sourceObjects'])
assert all(hashlib.sha256(pathlib.Path(r['path']).read_bytes()).hexdigest()==r['sha256'] for r in native['retainedReceipts'])
direct = json.loads((old/'direct-native-final.json').read_text(encoding='utf-8'))
assert len(direct['results']) == 24 and all(r['pass_'] for r in direct['results'])
for r in direct['results']:
    if r['case'] not in ('positive','no-open'):
        assert r['observation']['snapshotUnchanged'] and not r['observation']['effects']
peer = json.loads((old/'crossuid-nonlogin/result.json').read_text(encoding='utf-8'))['peer']['result']
operations=peer['boundaries']+peer['fileProbes']+peer['positives']
assert len(operations)==49 and all(r['pass'] for r in operations)
assert sum(r['outcome']=='denied' and r['errno']==13 for r in operations)==30
assert sum(r['outcome']=='allowed' for r in operations)==19
summary = json.loads((root/'summary.json').read_text(encoding='utf-8'))
assert len(summary['results']) == 6
validation = dict(scope='Local review serialization and retained-receipt consistency only; no product/native test execution.',
                  assignedIssues=[19,20,21,22,27,28],issueArtifactsParse=True,stableMarkersMatch=True,
                  mandatoryRows=sum(r['mandatoryRows'] for r in summary['results']),
                  nativeObjectEquivalence=True,retainedReceiptHashesMatch=True,
                  retainedWindowsRows=24,retainedLinuxDAC=dict(total=49,denied13=30,allowed=19),
                  sourceMutation='NONE',publication='NONE')
(root/'artifact-validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8')
print(json.dumps(validation))
