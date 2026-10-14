from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
import json,hashlib,subprocess
E=Path(__file__).resolve().parent;P=E/'planning-original-21e7a843/docs/rlgwo-execution/20261008';O=E/'dag-reconciliation-r1'
W=Path(r'C:\Users\theis\.codex\worktrees\celestial-startup-repair\salah_widget')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
g=read(P/'CLOSURE_DAG.json');baseline=read(P/'BASELINE_OBLIGATIONS.json');inventory=read(P/'INVENTORY.json')
expected=set(inventory['actualOpen']);closed={1,5,9,10,14,15,18,26,29,30,31}
assert len(expected)==26 and len(closed)==11 and expected|closed==set(range(1,38)) and not expected&closed
assert len(baseline['remainingMandatory'])==111 and len(baseline['acceptedOrSuperseded'])==280
by={n['id']:n for n in g['nodes']};parents=defaultdict(set)
for edge in g['edges']:parents[edge['to']].add(edge['from'])
seen=set();visiting=set()
def visit(n):
    assert n in by,n
    assert n not in visiting,('cycle',n)
    if n in seen:return
    visiting.add(n)
    for a in parents[n]:visit(a)
    visiting.remove(n);seen.add(n)
for n in by:visit(n)
def ancestors(n):
    result=set(parents[n])
    for a in parents[n]:result.update(ancestors(a))
    return result
assert len(seen)==213 and len(g['edges'])==409
closure={n['id'] for n in g['nodes'] if n['kind']=='closure'}
assert closure=={'CLOSE-'+x['canonicalId'] for x in inventory['issues']}
assert all(not f'CLOSE-R{x:04X}' in closure for x in closed)
assert {c['issue'] for c in g['coverage']}==expected
assert sum(len(c['acceptance']) for c in g['coverage'])==189
assert {a['id'] for c in g['coverage'] if c['issue']==33 for a in c['acceptance']}=={'R0021-A01',*(f'R0021-S{i}' for i in range(1,11))}
assert any(c['issue']==34 and c['obligationId']=='22-L1' for c in g['coverage'])
assert {'R0021-TIMING','R0022-L1-REPAIR'}<=ancestors('R0021-COST')
assert 'R0022-L1-REPAIR' in ancestors('R0022-COST')
assert {'R0022-L1-QUALIFY','R0021-PARENT','R0021-TIMING'}<=ancestors('R0021-QUALIFY')
assert 'CLOSE-R0022' not in ancestors('CLOSE-R0021') and 'CLOSE-R0021' not in ancestors('CLOSE-R0022')
priorities=Counter(read(f)['priority'] for f in (P/'metadata').glob('*.json'))
assert priorities=={'P1':21,'P2':5}
resources={r['id']:r['capacity'] for r in g['resources']}
assert resources['heavy-browser']==resources['integrator']==resources['document-integrator']==resources['github-writer']==1
assert resources['independent-review']==6
for n in g['nodes']:
    if n['kind']=='delivery':
        assert any(by[a]['kind']=='independent-review' for a in parents[n['id']])
        if n.get('deliveryMode') in ['docs-merge','runtime-merge']:assert any(by[a]['kind']=='authority' for a in parents[n['id']])
    assert n['status'] not in ['PASS','COMPLETE','CLOSED'] or n['kind']=='retained-baseline'
# Review-to-publication delta must be only the permitted package-relative links.
reviewed=read(P/'workers/C/package-review-final-v2/CLOSURE_DAG.json')
prefix='https://github.com/theislampill/salah_widget/blob/SPEC_EVIDENCE_COMMIT/docs/rlgwo-execution/20261008/'
count=0
def normalize(v):
    global count
    if isinstance(v,str) and v.startswith(prefix):count+=1;return v[len(prefix):]
    if isinstance(v,list):return [normalize(x) for x in v]
    if isinstance(v,dict):return {k:normalize(x) for k,x in v.items()}
    return v
assert normalize(reviewed)==g
readiness=read(P/'SPECIFICATION_READINESS.json')['issues']
assert len(readiness)==26 and all(x['primaryReconciled'] and x['coldRead']['disposition']=='PASS' and x['author']!=x['coldRead']['reviewer'] for x in readiness)
live=read(O/'LIVE_CURRENTNESS.json');assert live['result']=='PASS' and live['open26Preserved'] and live['accepted11Preserved']
assert not any(x.get('laterComments') for x in live['issues']), 'Later comments require human contract reconciliation'
pr=live['draftPR'];head='e3b042f17048fce8577cd08140f306cbce2d7f3c';base='18ff14860ff41c084b1db5f396bb62aa9c22b1be'
assert pr['draft'] and pr['head']==head and pr['base']==base and live['liveMain']==base
subprocess.run(['git','merge-base','--is-ancestor',base,head],cwd=W,check=True)
paths=subprocess.check_output(['git','diff','--name-only',base,head],cwd=W).decode().splitlines()
assert not any(x.startswith(('v1/','vendor/','real-sky/core/','moon/assets/dem.','moon/assets/colour.')) for x in paths)
identity=read(W/'docs/real-sky/startup-evidence/RUNTIME_IDENTITY_FINAL.json')
assert identity['treeSha256']=='4c764068d0d19afe4d440376ed765a373c7afead594b5d16ef22402dd02ef799'
affected=[
 {'owners':['src/native/index.html'],'changes':['prayer-independent celestial paint','render/task boundary before fresh weather/prayer transport','immutable timezone formatter reuse','one arc CTM read'],'obligations':['R0003','R0004','R0006','R0007','R0008','R0020','R0021'],'rule':'Reuse unchanged arithmetic/admission proof, retain helper negatives; qualify changed scheduling/currentness at actual consumer before joined-source closure. No closure credit from 679-test aggregate.'},
 {'owners':['real-sky/native-star-preview.mjs','real-sky/native-first-paint.mjs','real-sky/native-preview-host.mjs','real-sky/native-assets.mjs','real-sky/native-composition.mjs'],'changes':['same-catalogue bootstrap','independent initial admission','less redundant raster/readback','full preparation after paint opportunity'],'obligations':['R0021','R0022-L1','R0018','R0024','R0025'],'rule':'S2 source equivalence and scoped continuity evidence reusable; first-frame, contrast, weather, currentness and callback costs require exact relevant joined-source evidence. Physical lunar display field remains unchanged.'},
 {'owners':['moon/src/moon-initial.mjs','moon/src/moon-native.mjs','moon/tools/build_initial.cjs','moon/tools/qualify_initial.cjs','moon/initial-manifest.json','moon/assets/initial-receivers.bin'],'changes':['current V5-derived initial receiver tier','admission/currentness/recovery preserved','separate full terrain result'],'obligations':['R0021','R0022'],'rule':'Consume deterministic derivative and 40 retained-reference comparisons; do not repeat terrain research or revive rejected coarse/no-shadow variants. Initial is not final science or full-scene acceptance.'},
 {'owners':['tools/build_native.py','tools/build_moon.py','tools/native_star_bootstrap.py','index.html','offline.html','real-sky/native-sky.js','moon/moon-host.js'],'changes':['deterministic initial-tier embedding','root 6082431 bytes','offline 86133190 bytes'],'obligations':['R0010','R0013','R0014','R0015','R0016','R0017','R0021'],'rule':'Installers/config/builder are unchanged; exact delivered-file/entry claims use the actual approved source. Package enlargement and native-parent/slow-initial-document limits remain explicit.'},
 {'owners':['tests/r0003-harness.cjs','tests/r0003-ownership.test.cjs','tests/r0004-boot-day.test.cjs','tests/r0005-day-return.test.cjs','tests/r0006-recovery.test.cjs','tests/r000c-weather.test.cjs'],'changes':['fixtures explicitly advance production rAF/task boundary','retained ownership and mutation assertions'],'obligations':['R0003','R0004','R0005 accepted closure protection','R0006','R000C'],'rule':'Use the current harness when consuming exact PR source; do not interpret old synchronous fixture failure as a new runtime defect or alter existing closure status.'}
]
report={'schema':'startup-dag-compatibility/1','capturedAtUtc':datetime.now(timezone.utc).isoformat(),'verdict':'COMPATIBLE_WITH_VERSIONED_EXECUTION_BINDINGS','specCommit':'21e7a84365fae37a86cae5c7d5e41008c0adc53f','specGraphSha256':sha(P/'CLOSURE_DAG.json'),'repairCodeCommit':head,'repairPR':pr['url'],'runtime':identity['treeSha256'],'sourceBase':base,'auditEvidenceCommit':'b879573c298f19189d1f2392108b8b9f3b2cda0b','counts':{'nodes':213,'typedEdges':409,'openIssues':26,'protectedClosures':11,'originalResidualRows':111,'acceptedSupersededRows':280,'detailedAcceptanceEntries':189,'priorities':dict(priorities)},'independentStructuralChecks':'PASS','reviewedGraphDelta':{'permittedPackageRelativeLinkRewrites':count,'otherChanges':0},'graphStructuralAmendmentRequired':False,'externalBindingAmendmentRequired':True,'changedFiles':paths,'semanticOwnerReconciliation':affected,'unclosed':['R0021-S1 timing and native presentation coverage','R0021 original callback cost','actual extension/new-tab parent','R0022 original balance/paint-cost obligations','R0022-L1 display contract, bounded repair and owner full-scene acceptance / R0021-S10','independent PR review, exact joined-source qualification, owner-authorized merge/deployment and served readback'],'checks':{'packageManifest':'manifest.log','suppliedGraphValidator':'DAG_VALIDATION.json','graphMutants':'DAG_NEGATIVE_CONTROLS.json','publicationGuards':'PUBLICATION_GUARD_CONTROLS.json','references':'REFERENCE_VALIDATION.json','liveCurrentness':'LIVE_CURRENTNESS.json','historicalCustody':'PLANNING_CUSTODY.json'},'sourceEffect':'Read-only independent review; no issue disposition, main merge, deployment or product alteration.'}
(O/'COMPATIBILITY.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['verdict','counts','reviewedGraphDelta','graphStructuralAmendmentRequired','externalBindingAmendmentRequired']},indent=2))
