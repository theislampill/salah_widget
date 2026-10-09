"""Join reviewed issue metadata without inventing completed execution evidence."""
from pathlib import Path
import argparse
import collections
import copy
import csv
import json

ROOT = Path(__file__).resolve().parents[1]
TARGET = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
AUDIT = 'b879573c298f19189d1f2392108b8b9f3b2cda0b'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


ALIASES = {
    'single-heavy-browser-queue': 'heavy-browser',
    'single-shared-source-integrator': 'integrator',
    'one-authorized-external-writer': 'github-writer',
    'exclusive-heavy-browser': 'heavy-browser',
    'exclusive-heavy-performance': 'heavy-browser',
    'quiescent-performance': 'heavy-browser',
    'terrain': 'heavy-browser',
    'exclusive-source-integrator': 'integrator',
    'source-integrator': 'integrator',
    'documentation-integrator': 'document-integrator',
    'documentation-writer': 'document-integrator',
    'serialized-external-writer': 'github-writer',
    'public-readback-queue': 'github-writer',
    'read-only-review': 'independent-review',
    'single-heavy-browser-terrain-performance-queue': 'heavy-browser',
    'single-heavy-browser': 'heavy-browser',
    'single-browser-lease': 'heavy-browser',
    'single-heavy-browser-terrain': 'heavy-browser',
    'shared-source-docs-integrator': 'integrator',
    'shared-source-integrator': 'integrator',
    'single-integrator': 'integrator',
    'single-document-integrator': 'document-integrator',
    'docs-integrator': 'document-integrator',
    'external-publication-lease': 'github-writer',
    'serialized-public-readback': 'github-writer',
}


def resource(r):
    return ALIASES.get(r, r)


def release_stages(metadata, nodes, edges, edge_keys, edge):
    """Separate independently reviewed candidate, authorized delivery and closure.

    These nodes do not assert that approval, a merge or future evidence exists.
    Existing delivery nodes keep their issue-specific public-consumer contract.
    """
    for m in metadata:
        cid = m['canonicalId']
        close = next(n for n in nodes if n['id'] == m['closure']['id'])
        mode = m['closure'].get('deliveryMode')
        if not mode:
            # Binding issue contracts, not inference that every proof needs code.
            mode = ('runtime-merge' if m['issue'] in (24,33,34,36) else
                    'evidence-publication-and-existing-runtime-readback' if m['issue'] in (3,37) else 'docs-merge')
        close['deliveryMode'] = mode
        required_merge = mode in ('runtime-merge', 'docs-merge')
        deliveries = [n for n in nodes if n['parentIssues'] == [m['issue']] and n['kind']=='delivery']
        assert len(deliveries) <= 1, f'Multiple ungrouped delivery nodes for {cid}'
        docs_outputs=[o for n in nodes if n['parentIssues']==[m['issue']] and n['kind'] in {'docs','documentation'} for o in n['outputs']]
        if mode=='docs-merge':
            assert docs_outputs, f'Docs-only release has no concrete documentation producer: {cid}'
        confirmation=None
        if mode=='docs-merge' and deliveries:
            delivery=deliveries[0]
            confirmation=copy.deepcopy(delivery)
            confirmation['id']=cid+'-DELIVERY-CONFIRM'
            confirmation['kind']='qualification'
            confirmation['scope']='Confirm the complete original issue evidence and already-authorized docs delivery. '+confirmation['scope']
            confirmation['stageExpansion']='The authored combined distribution/proof stage is split: accurate docs can deliver before independent native proof, while this full confirmation and CLOSE retain every original proof requirement. No second merge is implied.'
            old_id=delivery['id']
            for e in edges:
                if e['from']==old_id:e['from']=confirmation['id']
                if e['to']==old_id:e['to']=confirmation['id']
            edge_keys.clear();edge_keys.update((e['from'],e['to'],e['type']) for e in edges)
            delivery['outputs']=[{'id':cid.lower()+'-docs-delivery/v1','contract':'Actual authorized documentation commit/files and raw/public readback; native evidence and issue closure remain pending separately.','artifact':f'execution/{cid}/docs-delivery.json'}]
            delivery['inputs']=[]
            confirmation['inputs']=[i for i in confirmation['inputs'] if i['id']!='future-delivery-authority/v1']
            confirmation['inputs'].append({'id':delivery['outputs'][0]['id'],'contract':'Re-use the exact independently reviewed and authorized documentation delivery, without a duplicate merge request.'})
            nodes.append(confirmation)
        base = dict(parentIssues=[m['issue']], issueObligations=[cid+':'+r['id'] for r in m['remainingObligations']],
                    priority=m['priority'], specification={'path':m['specPath'],'revision':m['revision']},
                    status='WAITING_INPUTS_AND_AUTHORITY', resources=['coordinator'],
                    estimate={'activeHours':[0.25,0.75],'exclusiveMachineMinutes':[0,0], 'confidence':'medium',
                              'basis':'Bounded candidate/effect identity reconciliation; excludes repairs, owner waiting and duplicated issue-specific tests.'})
        # Review takes only pre-delivery producer outputs. A delivery output is
        # deliberately excluded to avoid a review/delivery dependency cycle.
        delivery_output_ids={o['id'] for n in deliveries for o in n['outputs']}
        produced = {o['id']:o for n in nodes for o in n['outputs']}
        review_inputs=([{'id':o['id'],'contract':o['contract']} for o in docs_outputs] if mode=='docs-merge' else
                       [{'id':i,'contract':produced[i]['contract']} for i in m['closure']['requiredOutputs'] if i not in delivery_output_ids])
        rid=cid+'-RELEASE-REVIEW'; rout=cid.lower()+'-reviewed-release/v1'
        review={**copy.deepcopy(base),'id':rid,'kind':'independent-review','owner':'different reviewer plus primary reconciler',
                'scope':'Approve exact pre-delivery candidate/evidence and original plus amended contract; reject missing controls, source drift, unpublished proof or unqualified consumer claims.',
                'inputs':review_inputs,'outputs':[{'id':rout,'contract':'Exact reviewed head/tree/runtime/docs and evidence manifest; original/residual matrix reconciled, permission request prepared only if a merge is required.','artifact':f'execution/{cid}/release-review.json'}],
                'entryCriteria':['All assigned candidate evidence exists; exact artifacts fixed; reviewer differs from implementer.'],
                'exitCriteria':['No unresolved mandatory implementation/evidence row; review records future delivery as pending, not already passed.'],
                'tests':['Read actual source, negative controls, raw outputs and required pixels; check scope and applicable old receipts, final hashes and public evidence reachability.'],
                'resources':['independent-review','coordinator']}
        nodes.append(review)
        if mode=='docs-merge':
            review['scope']='Independently approve only the exact documentation facts/diff against accepted source and required documentation assertions. Unrelated native proof remains on QUALIFY/CLOSE and is not required to deliver accurate docs.'
            review['entryCriteria']=['Exact docs candidate and its source/fact proof fixed; reviewer differs from author; no claimed unsupported platform/runtime result.']
            review['exitCriteria']=['Every changed documentation claim accurate and independently reviewed; incomplete native/evidence rows remain explicit and the issue remains open.']
            review['outputs'][0]['contract']='Exact independently reviewed docs-only head/diff and source/fact evidence; full native and other residual proof explicitly pending until QUALIFY/CLOSE.'
        if deliveries:
            delivery=deliveries[0]
            delivery['inputs']=[i for i in delivery['inputs'] if i['id']!='future-delivery-authority/v1']
            delivery['inputs'].append({'id':rout,'contract':'Consume independently approved exact candidate; this does not grant merge authority.'})
        else:
            delivery={**copy.deepcopy(base),'id':cid+'-DELIVER','kind':'delivery','owner':'primary integration owner',
                'scope':'Deliver only the reviewed required docs/runtime change after exact-head owner authority, or publish proof and reverify the unchanged delivered consumer for an evidence-only issue.',
                'inputs':[{'id':rout,'contract':'Exact independently reviewed candidate and evidence.'}],
                'outputs':[{'id':cid.lower()+'-delivery/v1','contract':'Actual delivered commit/tree/runtime/docs, public/evidence readback and required consumer identity; no unmerged branch substitute.','artifact':f'execution/{cid}/delivery.json'}],
                'entryCriteria':['Review complete; exact-head merge authorization present when required; main/target/checks/protections freshly rechecked.'],
                'exitCriteria':['Required consumer and reachable evidence demonstrably match the reviewed target; stop on drift/failure without unreviewed production rewrite.'],
                'tests':['For docs-merge read merged pinned/raw documentation; for runtime-merge wait exact successful deployment and verify affected public consumer; for evidence-only verify unchanged delivered runtime and published proof without fictional runtime merge.'],
                'resources':['integrator','github-writer']}
            nodes.append(delivery)
        delivery['deliveryMode']=mode
        if mode=='docs-merge':
            delivery['scope']='Deliver independently reviewed documentation only after exact-head authority, then verify merged/raw/public documentation and unchanged runtime identity. Full original native/evidence proof is a separate issue-closure gate.'
            delivery['entryCriteria']=['Exact docs-only review passed; owner authorized this reviewed documentation head; freshly check branch/main/protections and scope.']
            delivery['exitCriteria']=['The actual merged documentation and reachable raw/public bytes match the approved facts; record other issue rows as still pending without claiming native qualification.']
            delivery['tests']=['Verify exact merged docs files, public/raw required consumer and unchanged runtime/V1; do not run or claim unrelated native-platform evidence as part of this docs-only effect.']
            delivery['resources']=['document-integrator','github-writer']
            delivery['estimate']['exclusiveMachineMinutes']=[0,0]
        if mode=='runtime-merge' and 'heavy-browser' not in delivery['resources']:
            delivery['resources']=sorted(set(delivery['resources']+['heavy-browser']))
            delivery['estimate']['exclusiveMachineMinutes']=[5,30]
            delivery['estimate']['confidence']='low'
            delivery['estimate']['basis']+=' Public affected Chromium/Firefox consumer scenes require the same exclusive browser lease; 5–30 minutes is a planning range, not a pass threshold or owner-wait ETA.'
        edge(rid,delivery['id'],'review','Independent exact-candidate approval precedes delivery.',rout)
        if required_merge:
            aid=cid+'-MERGE-AUTHORITY'; aout=cid.lower()+'-exact-head-authority/v1'
            auth={**copy.deepcopy(base),'id':aid,'kind':'authority','owner':'owner decision, primary records exact scope',
                'scope':'Obtain explicit owner approval for the specific reviewed docs/runtime head and release sequence; PR42 permission is not inherited.',
                'inputs':[{'id':rout,'contract':'Concrete reviewed candidate with complete pre-delivery proof and requested exact effects.'}],
                'outputs':[{'id':aout,'contract':'Owner-authorized exact head/base/merge/deployment scope; absent approval remains pending.','artifact':f'execution/{cid}/merge-authority.json'}],
                'entryCriteria':['Exact review completed; repository protections and intended merge/deploy effects enumerated.'],
                'exitCriteria':['Actual owner authority recorded, or node remains blocked; no timeout means consent.'],
                'tests':['Check exact head/base immediately before effect and honor protection failures without bypass.'],
                'estimate':{'activeHours':[0,0.25],'exclusiveMachineMinutes':[0,0],'confidence':'low','basis':'Preparation only; owner response latency unknown and excluded.'}}
            nodes.append(auth)
            delivery['inputs'].append({'id':aout,'contract':'Exact authorized merge/deployment scope, rechecked before effect.'})
            edge(rid,aid,'authority','Concrete exact-head request follows independent review.',rout)
            edge(aid,delivery['id'],'authority','No new merge/deployment authorized by this planning programme.',aout)
        dout=delivery['outputs'][0]['id']
        if not any(i['id']==dout for i in close['inputs']):
            close['inputs'].append({'id':dout,'contract':'Actual required delivery and readback precede completed issue closure.'})
        edge(delivery['id'],close['id'],'closure','Issue-specific delivered-consumer proof is mandatory before closure.',dout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--final', action='store_true')
    parser.add_argument('--allow-incomplete', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    inventory = load(root/'INVENTORY.json')
    baseline = load(root/'BASELINE_OBLIGATIONS.json')
    metadata = sorted([load(f) for f in (root/'metadata').glob('R*.json')], key=lambda m:m['issue'])
    actual = [m['issue'] for m in metadata]
    if not args.allow_incomplete:
        assert sorted(actual) == sorted(inventory['actualOpen']), 'Missing or unexpected metadata'
    assert len(actual) == len(set(actual))
    nodes, edges, external, coverage = [], [], {}, []
    edge_keys = set()

    def edge(a, b, kind, reason, interface=None):
        key = (a,b,kind)
        if key not in edge_keys:
            edges.append({'from':a,'to':b,'type':kind,'reason':reason,**({'interface':interface} if interface else {})})
            edge_keys.add(key)

    intake = {'id':'INTAKE-DRIFT','parentIssues':actual,'issueObligations':[], 'priority':'P1',
              'kind':'coordination','owner':'primary executor',
              'scope':'Reacquire delivered source/contracts, package identity, active startup ownership, pending effects and resource leases before node execution.',
              'specification':{'path':'THIRD_THREAD_EXECUTION_PROMPT.md','revision':1},
              'inputs':[{'id':'approved-execution-launch/v1','contract':'Owner submits/approves this bounded third-thread execution scope; new merges remain separate.'}],
              'outputs':[{'id':'reconciled-execution-target/v1','contract':'Exact current source/spec/contract drift and pending-work/resource ledger; only affected proof invalidated.','artifact':'execution/INTAKE.json'}],
              'entryCriteria':['Owner authorizes the bounded execution prompt; current worktree and uncertain external effects inspected without destructive reset.'],
              'exitCriteria':['Current targets, contract revisions, surviving processes and exclusive resource ownership reconciled; graph still valid.'],
              'tests':['Run package manifest and DAG validator; read current GitHub source/issue/PR state and existing process/ledger receipts.'],
              'resources':['coordinator'],'estimate':{'activeHours':[0.5,1.5],'exclusiveMachineMinutes':[0,0],'confidence':'medium','basis':'Bounded drift/readback over preserved inventory; excludes newly discovered changes.'},
              'status':'READY_ON_AUTHORIZED_LAUNCH'}
    nodes.append(intake)
    external['approved-execution-launch/v1']={'id':'approved-execution-launch/v1','status':'PENDING_OWNER_LAUNCH',
        'contract':'Planning publication is authorized now; bounded implementation/closure execution requires owner launch of the proposed third-thread prompt. New merges/deployments remain separately gated.',
        'localArtifacts':['RESOURCE_AND_AUTHORITY.md','THIRD_THREAD_EXECUTION_PROMPT.md'],'evidence':[]}

    for m in metadata:
        assert m['sourceTarget'] == TARGET and m['auditEvidenceCommit'] == AUDIT
        for original in m['nodes']:
            n = copy.deepcopy(original)
            n['parentIssues'] = [m['issue']]
            n['specification'] = {'path':m['specPath'],'revision':m['revision']}
            n['author'] = m['author']
            n['resources'] = sorted(set(resource(r) for r in n['resources']))
            n['authoredPlanningStatus'] = n['status']
            n['status'] = 'WAITING_INPUTS_AND_INTAKE'
            n['inputMetadataPath'] = f'metadata/{m["canonicalId"]}.json'
            n.setdefault('sharedFiles',[])
            for d in n.pop('dependsOn',[]):
                edge(d['node'],n['id'],d['type'],d['reason'])
            nodes.append(n)
        close = m['closure']
        if not any(n['id']==close['id'] for n in nodes):
            n={'id':close['id'],'parentIssues':[m['issue']],
               'issueObligations':[m['canonicalId']+':'+r['id'] for r in m['remainingObligations']],
               'priority':m['priority'],'kind':'closure','owner':'primary plus designated issue publisher',
               'scope':'Fresh contract/currentness readback, independent certificate reconciliation, full evidence comment/readback then justified completed closure and final state readback.',
               'specification':{'path':m['specPath'],'revision':m['revision']},
               'inputs':[{'id':x,'contract':'Consume the exact independently reconciled output; no branch-only substitute for required delivery.'} for x in close['requiredOutputs']],
               'outputs':[{'id':m['canonicalId'].lower()+'-github-closure/v1','contract':'Exact reviewed closure comment URL/readback, final issue state/reason, delivered identity and retained limits.','artifact':f'execution/issues/{m["issue"]:02d}-closure.json'}],
               'entryCriteria':close['conditions'],
               'exitCriteria':['Comment published and read back before closure; final GitHub state completed verified, or explicit smallest remaining gap recorded without closing.'],
               'tests':['Re-read complete current issue and stable publication marker; verify exact comment hash, reachable evidence, final source and delivered consumers; read back final state.'],
               'resources':['coordinator','github-writer'],
               'estimate':{'activeHours':[0.25,0.75],'exclusiveMachineMinutes':[0,0],'confidence':'medium','basis':'Per-issue final reconciliation and serial idempotent publication; excludes new review defects.'},
               'status':'WAITING_QUALIFICATION_DELIVERY_AND_AUTHORITY', 'authority':close['authority'],
               'requiresDelivery':close['requiresDelivery'],'deliveryMode':close.get('deliveryMode',m.get('deliveryMode','SEE_SPECIFICATION'))}
            nodes.append(n)
        for r in m['remainingObligations']:
            is_old = any(x['issue']==m['issue'] and x['id']==r['id'] for x in baseline['remainingMandatory'])
            artifacts = [a['artifact'] for a in r['acceptance']]
            coverage.append({'issue':m['issue'],'canonicalId':m['canonicalId'],'obligationId':r['id'],
                             'basis':'audit-residual' if is_old else 'explicit-owner-successor',
                             'parentText':r['parentText'],'residualClass':r['class'],'priority':r['priority'],
                             'nodeIds':r['nodeIds'],'acceptanceEvidence':artifacts,'acceptance':r['acceptance'],
                             'closureGate':r['closureGate'],'specification':m['specPath']})

    release_stages(metadata,nodes,edges,edge_keys,edge)
    interface_aliases=[]
    for m in metadata:
        cid=m['canonicalId']
        aliases={cid+'-exact-head-authority/v1':cid.lower()+'-exact-head-authority/v1',
                 cid+'-required-delivery/v1':cid.lower()+'-delivery/v1'}
        for n in nodes:
            for i in n['inputs']:
                if i['id'] in aliases:
                    old=i['id'];i['id']=aliases[old];i['authoredInterfaceId']=old
                    interface_aliases.append({'consumer':n['id'],'authoredId':old,'producedId':i['id'],
                        'contract':i['contract'],'reconciliation':'Primary expands authored closure receipt requirement into explicit exact-head authority and delivery stages; same contract, one actual producer. Artifact path is producer.outputs[].artifact.'})
    by_id = {n['id']:n for n in nodes}
    assert len(by_id)==len(nodes), 'Duplicate node IDs'
    producers = {}
    for n in nodes:
        for o in n['outputs']:
            assert o['id'] not in producers, f'Duplicate output {o["id"]}'
            producers[o['id']]=n['id']
    for n in nodes:
        for i in n['inputs']:
            iid=i['id']
            if iid in producers:
                a=producers[iid]
                if a!=n['id']:
                    existing=[e for e in edges if e['from']==a and e['to']==n['id']]
                    if not existing:
                        edge(a,n['id'],'closure' if n['kind']=='closure' else 'hard-interface',f'Consumes named produced interface {iid}.',iid)
                    else:
                        existing[0].setdefault('interface',iid)
            elif iid not in external:
                external[iid]={'id':iid,'status':i.get('status','UNVERIFIED'), 'contract':i['contract'],
                               'evidence':i.get('evidence',[]),'consumerViews':[{'node':n['id'],'contract':i['contract']}]}
            elif iid != 'approved-execution-launch/v1':
                e=external[iid]
                assert e['status']==i.get('status','UNVERIFIED'), f'Interface status mismatch {iid}'
                e.setdefault('consumerViews',[]).append({'node':n['id'],'contract':i['contract']})
                e['evidence']=sorted(set(e['evidence']+i.get('evidence',[])))
                if e['contract'] != i['contract']:
                    e['contractViewsRequireReconciliation']=True
        if n['id']!='INTAKE-DRIFT' and not any(e['to']==n['id'] for e in edges):
            n['inputs'].append({'id':'reconciled-execution-target/v1','contract':intake['outputs'][0]['contract']})
            edge('INTAKE-DRIFT',n['id'],'qualification','Entry identity/contract/resource reconciliation; this is not a prerequisite issue closure.','reconciled-execution-target/v1')

    reconcile_path=root/'INTERFACE_RECONCILIATION.json'
    reconciliations=load(reconcile_path) if reconcile_path.exists() else {}
    for iid,record in reconciliations.items():
        if iid in external:
            external[iid]['reconciliation']=record
            external[iid]['contractViewsRequireReconciliation']=False
    all_resources=sorted(set(r for n in nodes for r in n['resources']))
    resource_defs=[]
    for r in all_resources:
        count=6 if r in {'independent-review','read-only-analysis','fixture-authoring'} else 1
        resource_defs.append({'id':r,'capacity':count,
            'availability':'ACTIVE_STARTUP_LEASE' if r=='heavy-browser' else 'UNAVAILABLE_ACQUIRE_NATIVE_PLATFORM' if r in {'native-apple-host','actual-extension-parent','native-linux-fixture-queue'} else 'TO_VERIFY_AT_EXECUTION_INTAKE',
            'policy':'One serial expensive browser/terrain/performance queue; no latency evidence under competing solvers.' if r=='heavy-browser' else 'Disjoint ownership and explicit lease; resource contention is not a semantic edge.'})
    pairs=set((e['from'],e['to']) for e in edges)
    ins=collections.Counter(b for a,b in pairs)
    outs=collections.defaultdict(list)
    for a,b in pairs:
        assert a in by_id and b in by_id, f'Dangling edge {a}->{b}'
        outs[a].append(b)
    q=sorted(x for x in by_id if not ins[x]);topo=[]
    while q:
        a=q.pop(0);topo.append(a)
        for b in sorted(outs[a]):
            ins[b]-=1
            if ins[b]==0:q.append(b);q.sort()
    assert len(topo)==len(nodes), 'Cyclic graph'
    graph={'schemaVersion':1,'planRevision':1,'status':'FINAL_EXECUTABLE_HANDOFF_WITH_EXPLICIT_GATES' if args.final else 'PROVISIONAL',
           'identities':{'sourceTarget':TARGET,'sourceTree':'35208181eea714c17f5e77b2644e76434345db60','auditEvidenceCommit':AUDIT,
                         'runtimeSha256':'f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260'},
           'initialIssues':inventory['actualOpen'],'metadataIssues':actual,'resources':resource_defs,
           'interfaceAliases':interface_aliases,
           'externalInputs':list(external.values()),'nodes':nodes,'edges':edges,'coverage':coverage,'topologicalOrder':topo,
           'executionState':'No planned production implementation, test result, merge or closure is completed by this graph.',
           'resourceConstraintsAreNotHardEdges':True}
    save(root/'CLOSURE_DAG.json',graph)
    with (root/'OBLIGATION_COVERAGE.csv').open('w',encoding='utf-8',newline='') as f:
        fields=['issue','canonicalId','obligationId','basis','residualClass','priority','nodeIds','acceptanceEvidence','closureGate','specification']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for c in coverage:
            row={k:c[k] for k in fields}
            for k in ('nodeIds','acceptanceEvidence'):row[k]=' | '.join(row[k])
            writer.writerow(row)
    with (root/'ACCEPTANCE_COVERAGE.csv').open('w',encoding='utf-8',newline='') as f:
        fields=['issue','canonicalId','obligationId','acceptanceId','fixture','consumer','assertion','environment','expected','artifact','reviewGate','closureGate']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for c in coverage:
            for a in c['acceptance']:
                row={k:c[k] for k in ('issue','canonicalId','obligationId','closureGate')}
                row['acceptanceId']=a.get('id','')
                for k in fields[4:-1]:
                    value=a.get(k,'')
                    row[k]=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
                writer.writerow(row)
    names={n['id']:f'n{i:03d}' for i,n in enumerate(nodes)}
    diagram=['flowchart TD','%% Full graph generated from CLOSURE_DAG.json; resources are capacity constraints, not edges.']
    for n in nodes:
        label=f'{n["id"]}<br/>{n["kind"]} / {n["priority"]}'
        diagram.extend([f'%% NODE {n["id"]}',f'  {names[n["id"]]}["{label}"]'])
    for e in edges:
        diagram.extend([f'%% EDGE {e["from"]} {e["to"]} {e["type"]}',f'  {names[e["from"]]} -->|{e["type"]}| {names[e["to"]]}'])
    (root/'CLOSURE_DAG.mmd').write_text('\n'.join(diagram)+'\n',encoding='utf-8')
    print(json.dumps({'status':graph['status'],'issues':len(actual),'nodes':len(nodes),'edges':len(edges),'coverage':len(coverage),
                      'interfaceViewsNeedingReconciliation':[x['id'] for x in external.values() if x.get('contractViewsRequireReconciliation')]}))


if __name__=='__main__':
    main()
