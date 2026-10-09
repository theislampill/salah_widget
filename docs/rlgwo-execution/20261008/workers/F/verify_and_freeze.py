"""Validate authored planning documents and bind their hashes. No product execution."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

P = Path('C:/Users/theis/Documents/Codex/rlgwo-execution-plan-20261008')
A = Path('C:/Users/theis/Documents/Codex/pr42-rlgwo-closure-20261008')
W = Path('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget')
TARGET = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
AUDIT = 'b879573c298f19189d1f2392108b8b9f3b2cda0b'
ISSUES = {23:'R0017',24:'R0018',33:'R0021',34:'R0022',37:'R0025'}
now = datetime.now(timezone.utc).isoformat()
freeze_path = P / 'workers/F/AUTHOR_FREEZE.json'
previous_bytes = freeze_path.read_bytes() if freeze_path.exists() else b''
previous_sha = hashlib.sha256(previous_bytes).hexdigest() if previous_bytes else None
previous = json.loads(previous_bytes) if previous_bytes else {}
previous_files = {x['path']:x['sha256'] for x in previous.get('files',[])}
errors, files, checks = [], [], []
def bound(path):
    data = (P/path).read_bytes()
    return {'path':path, 'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data)}
for issue, cid in ISSUES.items():
    spec_path, comment_path, metadata_path = f'REMAINING_RLGWOs/{cid}.md', f'comments/{issue}.md', f'metadata/{cid}.json'
    spec = (P/spec_path).read_text(encoding='utf-8')
    comment = (P/comment_path).read_text(encoding='utf-8')
    metadata = json.loads((P/metadata_path).read_text(encoding='utf-8'))
    packet = json.loads((P/f'issues/{issue}.json').read_text(encoding='utf-8'))
    old = json.loads((A/f'workers/F/{issue:02}-assessment.json').read_text(encoding='utf-8'))
    assert spec == comment and len(comment) < 65536
    assert spec.startswith(f'RLGWO remaining-work specification — {cid} — revision 1\nPriority:')
    assert f'<!-- RLGWO-SPEC:{TARGET}:{cid}:rev1:2026-10-08 -->' in spec
    assert len(re.findall(r'^## [A-H]\.', spec, re.M)) == 8
    assert metadata['sourceTarget'] == TARGET and metadata['auditEvidenceCommit'] == AUDIT
    assert metadata['bodySha256'] == hashlib.sha256(packet['issue']['body'].encode()).hexdigest() == packet['contract']['bodySha256']
    old_rows = {x['id']:x for x in old['requirementMatrix']}
    residual = {x['id']:x for x in metadata['remainingObligations']}
    accepted = {x['id']:x for x in metadata['acceptedObligations']}
    for row_id, row in old_rows.items():
        if row['status'] in ('satisfied','validly superseded'):
            assert row_id in accepted
        else:
            assert row_id in residual, (cid, row_id)
            assert residual[row_id]['parentText'] == row['obligation']
    for row in residual.values():
        assert row['acceptance']
        for acceptance in row['acceptance']:
            assert all(acceptance.get(k) for k in ('fixture','consumer','assertion','environment','expected','artifact','reviewGate'))
    for sha, path in re.findall(r'https://github\.com/theislampill/salah_widget/blob/([0-9a-f]{40}|SPEC_EVIDENCE_COMMIT)/([^\s)<>|]+)', spec):
        path = path.split('#')[0].rstrip('.,;')
        if sha == TARGET:
            target = W/path
        elif sha == AUDIT and path.startswith('docs/rlgwo-audit/20261008/'):
            target = A/path.removeprefix('docs/rlgwo-audit/20261008/')
        elif sha == 'SPEC_EVIDENCE_COMMIT' and path.startswith('docs/rlgwo-execution/20261008/'):
            target = P/path.removeprefix('docs/rlgwo-execution/20261008/')
        else:
            continue
        if not target.exists():
            errors.append({'issue':issue,'urlPath':path,'localTarget':str(target)})
    files.extend(bound(x) for x in (spec_path,comment_path,metadata_path))
    checks.append({'issue':issue,'canonicalId':cid,'residualParents':list(residual),'nodes':len(metadata['nodes']),
                   'deliveryMode':metadata['closure']['deliveryMode'],'readiness':metadata['readiness'],'commentCharacters':len(comment)})
assert not errors, errors
all_nodes = {}
for path in sorted((P/'metadata').glob('*.json')):
    for task in json.loads(path.read_text(encoding='utf-8')).get('nodes',[]):
        all_nodes[task['id']] = task
visiting, visited = set(), set()
def visit(key):
    if key in visiting:
        raise AssertionError('Dependency cycle at '+key)
    if key in visited:
        return
    visiting.add(key)
    for predecessor in all_nodes[key].get('dependsOn',[]):
        if predecessor['node'] in all_nodes:
            visit(predecessor['node'])
    visiting.remove(key)
    visited.add(key)
for key in all_nodes:
    visit(key)
result = {'schema':'F-author-self-review-v1','capturedAtUtc':now,
          'kind':'Documentation parse/coverage/literal/local-link/dependency inspection only; no product tests/build/browser/source effect',
          'checks':checks,'files':files,'localLinkErrors':errors,'graphNodesInspected':len(all_nodes),'dependencyCycles':[], 'status':'PASS'}
(P/'workers/F/SELF_REVIEW.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
changed_issues = [issue for issue,cid in ISSUES.items() if any(previous_files.get(x) != bound(x)['sha256'] for x in (f'REMAINING_RLGWOs/{cid}.md',f'comments/{issue}.md',f'metadata/{cid}.json'))]
files.extend(bound(x) for x in ('workers/F/AUTHOR_REVIEW.md','workers/F/SELF_REVIEW.json'))
freeze = {'schema':'rlgwo-author-freeze-v1','author':'F','capturedAtUtc':now,
          'status':'AWAITING_TARGETED_COLD_REVIEW_DEFINITE_PLANNING_INTAKE','issues':list(ISSUES),'provisionalIssues':[],
          'planningHandoffStatus':'DEFINITE_ACTIVE_NOT_COMPLETE',
          'planningSealEligibleAfterTargetedReview':True,'productSealAllowed':False,
          'remainingGate':'Exact active startup successor/source consumption/lease release, timing/Firefox/native-parent/callback-cost/L1/full-appearance and delivered-runtime gates remain execution obligations.',
          'previousFreezeSha256':previous_sha,
          'targetedFindingIds':['E-F-33-001','E-F-33-002','E-F-34-001','E-F-34-002','E-F-37-001'],
          'changedIssues':changed_issues, 'files':files,'productEffects':False}
freeze_path.write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'status':'PASS','freezeSha256':hashlib.sha256(freeze_path.read_bytes()).hexdigest(),'files':files,'graphNodes':len(all_nodes)},ensure_ascii=False,indent=2))
