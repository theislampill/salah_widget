"""Planning schema/coverage/interface/path checks, not product tests."""
from pathlib import Path
import hashlib,json,re,subprocess
P=Path('C:/Users/theis/Documents/Codex/rlgwo-execution-plan-20261008')
A=Path('C:/Users/theis/Documents/Codex/pr42-rlgwo-closure-20261008')
W=Path('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget')
REQUIRED=set('issue canonicalId revision author sourceTarget auditEvidenceCommit bodySha256 specPath commentPath priority residualClasses priorityAssessment readiness acceptedObligations remainingObligations nodes closure documentationFacts affectedRegressionSet reuseRules sharedFileRisks decisions nonGoals'.split())
NODE_REQUIRED=set('id issueObligations priority kind owner scope sourceRevision inputs outputs entryCriteria exitCriteria tests resources sharedFiles dependsOn estimate status'.split())
ACCEPT_REQUIRED=set('id fixture consumer assertion environment expected artifact reviewGate'.split())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(W),*args],text=True).strip()
checks=[];files=[];counts={'accepted':0,'remaining':0,'nodes':0};all_ids=set();links=set()
for num,cid in [(8,'R0008'),(25,'R0019'),(32,'R0020')]:
    meta=P/'metadata'/f'{cid}.json';m=json.loads(meta.read_text(encoding='utf-8'));assert REQUIRED<=m.keys()
    audit=json.loads((A/'workers/B'/f'{num:02d}-assessment.json').read_text(encoding='utf-8-sig'))
    rows=audit['fullRequirementMatrix'];accepted={r['id'] for r in rows if r['disposition'] in ['satisfied','superseded']}
    rem={r['id'] for r in rows if r['disposition'] in ['unmet','unverified'] and r['mandatory']}
    assert accepted=={r['id'] for r in m['acceptedObligations']};assert rem=={r['id'] for r in m['remainingObligations']}
    assert m['readiness']=='AWAITING_COLD_REVIEW';assert m['deliveryMode']==m['closure']['deliveryMode']=='docs-merge'
    assert m['revision']==2
    assert m['closure']['conditionalDeliveryMode']=='runtime-merge-if-changed'
    assert m['closure']['requiredDeliveryReceipt']['id']==cid+'-DELIVERY-RECEIPT'
    assert m['closure']['requiredDeliveryReceipt']['status']=='PENDING_DOWNSTREAM'
    nodes={n['id']:n for n in m['nodes']};outputs={};artifacts=set()
    for n in nodes.values():
        assert NODE_REQUIRED<=n.keys();assert n['status']=='AWAITING_COLD_REVIEW'
        if n['kind']=='qualification':
            assert any('Qualification can finish before merge/public delivery' in x for x in n['exitCriteria'])
            candidate=[o for o in n['outputs'] if o['artifact'].endswith('closure-certificate.json')]
            assert len(candidate)==1 and candidate[0]['stage']=='PRE_DELIVERY_CANDIDATE'
            assert candidate[0]['requiredDownstreamReceipt']==cid+'-DELIVERY-RECEIPT'
        assert n['id'] not in all_ids;all_ids.add(n['id'])
        for o in n['outputs']:
            assert o['id'] not in outputs;assert o['artifact'] not in artifacts
            outputs[o['id']]=(n['id'],o['artifact']);artifacts.add(o['artifact'])
    for n in nodes.values():
        assert all(d['node'] in nodes for d in n['dependsOn'])
        for i in n['inputs']:
            if 'producerNode' in i:
                assert i['id'] in outputs
                assert outputs[i['id']]==(i['producerNode'],i['artifact'])
                assert i['status']=='PENDING_INTERNAL'
    required=m['closure']['requiredOutputs'];assert len(required)==len(set(required));assert set(required)==set(outputs)
    assert m['closure']['requiredArtifacts']=={k:v[1] for k,v in outputs.items()}
    visited=set();active=set()
    def visit(k):
        assert k not in active
        if k in visited:return
        active.add(k)
        for d in nodes[k]['dependsOn']:visit(d['node'])
        active.remove(k);visited.add(k)
    for k in nodes:visit(k)
    byid={r['id']:r for r in rows};spec=P/m['specPath'];comment=P/m['commentPath']
    assert spec.read_bytes()==comment.read_bytes();text=spec.read_text(encoding='utf-8')
    assert len(text)<65536;assert all(f'## {c}.' in text for c in 'ABCDEFGH')
    for r in m['remainingObligations']:
        assert r['parentText']==byid[r['id']]['obligation'];assert r['id'] in text
        assert all(n in nodes for n in r['nodeIds']);assert r['closureGate']=='CLOSE-'+cid
        for a in r['acceptance']:
            assert ACCEPT_REQUIRED<=a.keys();assert a['artifact'] in artifacts
        assert any(cid+':'+r['id'] in n['issueObligations'] for n in nodes.values())
    for f in [spec,comment,meta]:files.append({'path':f.relative_to(P).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size})
    for content in [text,json.dumps(m)]:
        links.update(re.findall(r'https://github\.com/theislampill/salah_widget/blob/([^/#\s)]+?)/([^\s)\"\]]+)',content))
    counts['accepted']+=len(accepted);counts['remaining']+=len(rem);counts['nodes']+=len(nodes)
    checks.append({'issue':num,'canonicalId':cid,'schema':'PASS','exactResidualCoverage':'PASS','outputInputIdentity':'PASS','uniqueClosureOutputIdsAndArtifactPaths':'PASS','acyclicLocalDependencies':'PASS','specCommentIdentity':'PASS','commentCharacters':len(text),'status':'AWAITING_COLD_REVIEW'})
verified_links=[]
for ref,path in sorted(links):
    path=path.split('#')[0]
    if ref=='SPEC_EVIDENCE_COMMIT':continue
    subprocess.check_call(['git','-C',str(W),'cat-file','-e',ref+':'+path],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    verified_links.append({'commit':ref,'path':path,'check':'local immutable Git object exists; not a new remote availability claim'})
state={'worktreeHead':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'dirty':git('status','--short'),
       'root':git('rev-parse','--show-toplevel'),'remote':git('remote','get-url','origin')}
assert state['tree']=='35208181eea714c17f5e77b2644e76434345db60';assert state['dirty']==''
report={'schema':'B-spec-final-validation/1','scope':'Planning structural/schema/coverage/immutable path checks only; no product test/browser/GitHub effect.',
        'counts':counts,'issues':checks,'sourceReanchor':state,'immutableGitPaths':verified_links,
        'findings':'No missing mandatory field/row, dangling internal interface ID, duplicate output artifact, local DAG cycle or spec/comment mismatch.'}
out=P/'workers/B/final-validation.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['AUTHOR_REVIEW.md','author-validation.json','final-validation.json','write_metadata.py','validate_and_freeze.py','repair_cold_contracts.py','cold-corrections-rev2.json']:
    f=P/'workers/B'/name;files.append({'path':f.relative_to(P).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size})
freeze={'schema':'B-author-freeze/1','readiness':'AWAITING_COLD_REVIEW','issues':[8,25,32],
        'sourceTarget':'18ff14860ff41c084b1db5f396bb62aa9c22b1be','auditEvidenceCommit':'b879573c298f19189d1f2392108b8b9f3b2cda0b',
        'files':files,'counts':counts,'nextAction':'Independent reviewer A cold-read; no publication/readiness promotion by author.'}
f=P/'workers/B/AUTHOR_FREEZE.json';f.write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'checks':'PASS_PLANNING_STRUCTURAL','counts':counts,'immutableGitPaths':len(verified_links),
                  'freeze':str(f),'freezeSha256':sha(f),'readiness':'AWAITING_COLD_REVIEW'},indent=2))
