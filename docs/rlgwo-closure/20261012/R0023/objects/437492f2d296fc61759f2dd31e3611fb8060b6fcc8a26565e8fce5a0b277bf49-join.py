"""Root-only R0023 pre-delivery QUALIFY JOIN. Default is inert and read-only."""
import argparse, collections, datetime as dt, hashlib, json, os
import importlib.util, sys
from pathlib import Path
RUN=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
INSTALL=RUN/'integration/r0023-qualify-exit-join-r2/join.py'
REVIEW=RUN/'workers/r0023_qualify_capture_review_r2/final-r1'
PREP=RUN/'workers/r0023_qualify_join_preparation_r1'
PREP_SEAL='f238f06cafbcae02dff2df1e27a64acfba5a8a24b8c63242dfe09dda4405b271'
PREP_MATERIALIZER='3ff2f3c759c3493aa3d0e29106a32c50128e55ff24270b885ccf5b9d26a124f7'
CANDIDATE=RUN/'integration/r0023-qualify-candidate-r1/reviewed-candidate-certificate.json'
ALIAS=RUN/'integration/r0023-qualify-candidate-r1/documentation.json'
ALIAS_SHA='935fe839cc84f80deb864452dfa7cf074004dd2b87bcc75df760f92e7a9f8f68'
TARGET=RUN/'evidence/R0023/reviewed-candidate-certificate.json'
DOC_TARGET=RUN/'evidence/R0023/documentation.json'
PLAN=Path('C:/Users/theis/Documents/Codex/celestial-startup-repair-20261008/planning-original-21e7a843/docs/rlgwo-execution/20261008')
GRAPH_SHA='9ac372cfcce4df94ee0e678b907e66c131fe49f72cc55106143aa35dbdb0a6e7'
RUNTIME='e718fe9e58f37535de4dc496a2da3bf2b05808153287e1fe328398ea59c0df53'
NODE='R0023-QUALIFY'
REVIEWER='/root/r0023_qualify_capture_review_r2'
ROWS=['R0023-O%02d'%i for i in range(1,26)]
ACCEPTANCE=['R0023-A%02d'%i for i in range(1,10)]

def read(p): return json.loads(Path(p).read_bytes())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p): return {'path':str(p),'bytes':Path(p).stat().st_size,'sha256':sha(p)}
def enc(v): return (json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def save(p,v): Path(p).write_bytes(enc(v))
def refs(v,seen):
    if isinstance(v,dict):
        if isinstance(v.get('path'),str) and 'bytes' in v and 'sha256' in v:
            p=Path(v['path']); assert p.is_absolute(),str(p)
            key=(str(p),v['sha256'])
            if key not in seen:
                assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],str(p)
                seen.add(key)
        for x in v.values(): refs(x,seen)
    elif isinstance(v,list):
        for x in v: refs(x,seen)
def seal(p,expected):
    assert sha(p/'SEAL.json')==expected
    s=read(p/'SEAL.json'); assert sha(p/'MANIFEST.json')==s['manifestSha256']
    m=read(p/'MANIFEST.json'); items=m['files']; assert isinstance(items,list) and items
    names=[]
    for x in items:
        q=(p/x['path']).resolve(); assert q.is_relative_to(p.resolve()) and x['path'] not in names
        assert q.stat().st_size==x['bytes'] and sha(q)==x['sha256'];names.append(x['path'])
    assert 'REPORT.json' in names
    return read(p/'REPORT.json')

def validate_core(core,value,candidate_pin,alias_pin,literal):
    assert core['schema']=='r0023-independent-qualification-decision-core/1' and core['node']==NODE
    assert core['reviewer']==REVIEWER and core['status']=='PASS_R0023_PRE_DELIVERY_QUALIFICATION_WITH_LIMITS'
    assert core['stage']=='PRE_DELIVERY_CANDIDATE' and core['sourceRuntimeSha256']==RUNTIME
    assert core['materializedCandidate']==candidate_pin and core['documentationAlias']==alias_pin
    assert [x['id'] for x in value['all25OriginalRows']]==core['originalRowIds']==ROWS
    assert core['originalAcceptanceIds']==value['originalAcceptanceIds']==ACCEPTANCE
    assert core['additionalDocAcceptanceId']==value['additionalDocAcceptanceId']=='R0023-A11'
    assert core['laterDeliveredClosureAcceptanceId']==value['laterDeliveredClosureAcceptanceId']=='R0023-A10'
    assert sorted(value['acceptanceMap'])==sorted(ACCEPTANCE+['R0023-A11'])
    own=core['ownExitDispositions'];assert [x['literal'] for x in own]==literal['exitCriteria']
    assert all(x['disposition']=='SATISFIED' and x['supportingArtifactRefs'] for x in own)
    rows=core['rowDispositions'];assert [x['id'] for x in rows]==ROWS
    assert all(x['disposition']=='ACCEPTED_EXACT_CANDIDATE_SCOPE_WITH_LIMITS' and x['supportingArtifactRefs'] for x in rows)
    assert core['downstreamGates']==value['downstreamGates']
    assert all(x['disposition']=='PENDING' and x['blocksQualificationOwnExit'] is False for x in core['downstreamGates'])
    assert core['newDOCNodeCredit']==0 and core['docsCanonicalPreimage'] is None and core['certificateCanonicalPreimage'] is None
    assert core['delivered'] is False and core['issueClosed'] is False and core['wholeRuntimeEquivalenceToCurrent07'] is False
    assert all(x in core['preservedLimits'] for x in value['preservedLimits'])
    assert all(value['o25Preservation'][x] is True for x in ['noPrivateURLLeak','conservativeDowngrade','rollbackPreservesUsableCoordinatesAndPreferences','noDestructiveMigrationOrContinuousTracking'])
    assert value['o25Preservation']['finalDeliveredEndToEndProof']=='PENDING_R0023_A10_AND_CLOSURE'

def build_certificate(core,value):
    """Acyclic: final REPORT/SEAL hashes are bound by the root receipt only."""
    return {'schema':'r0023-reviewed-candidate/v1','interfaceId':'r0023-reviewed-candidate/v1','node':NODE,
        'stage':'PRE_DELIVERY_CANDIDATE','status':'REVIEWED_PRE_DELIVERY_CANDIDATE_WITH_RETAINED_LIMITS',
        'acceptedImmutableCandidate':core['materializedCandidate'],'materializedProducerMetadataRetainedAsHistorical':True,
        'independentDecisionCore':core,'independentDecisionCoreSha256':hashlib.sha256(enc(core)).hexdigest(),
        'independentFinalReviewRecordPath':str(REVIEW/'REPORT.json'),'finalReviewSealBoundExternallyByRootReceipt':True,
        'all25OriginalRows':value['all25OriginalRows'],'acceptedPartialSubobligations':value['acceptedPartialSubobligations'],
        'originalAcceptanceIds':value['originalAcceptanceIds'],'additionalDocAcceptanceId':'R0023-A11',
        'laterDeliveredClosureAcceptanceId':'R0023-A10','acceptanceMap':value['acceptanceMap'],
        'laterDeliveredClosureAcceptance':value['laterDeliveredClosureAcceptance'],
        'sourceFreeze':pin(PREP/'FINAL_SOURCE_FREEZE.json'),'sourceNamespaceProvenance':{
            'historicalMain':value['sourceNamespaces']['historicalMain'],
            'evidenceSubject':value['sourceNamespaces']['evidenceSubject'],
            'revisionDocsAndSource':value['sourceNamespaces']['revisionDocsAndSource'],
            'rootContext':value['sourceNamespaces']['rootContext'],'current07Context':value['sourceNamespaces']['current07Context'],
            'wholeE718Current07OrRootEquivalenceClaimed':False},
        'acceptedDOC':{'interfaceId':'r0023-documentation/v1','approvedAlias':core['documentationAlias'],
            'canonicalTarget':str(DOC_TARGET),'canonicalPostimage':{k:core['documentationAlias'][k] for k in ['bytes','sha256']},
            'acceptedAdmission':value['docsInput']['actualAcceptedAdmission'],'historicalCanonicalFileClaimed':False,'newDOCNodeCredit':0},
        'acceptedMETADATA':value['metadataInput'],'acceptedPOLICY':value['policyInput'],
        'currentness':value['currentness'],'o25Preservation':value['o25Preservation'],
        'ownExitDispositions':core['ownExitDispositions'],'rowDispositions':core['rowDispositions'],
        'downstreamGates':core['downstreamGates'],'preservedLimits':core['preservedLimits'],
        'delivered':False,'issueClosed':False,'mergeDeploymentAuthorized':False,'wholeRuntimeEquivalenceToCurrent07':False}

def reviewed_input(value,seen):
    assert value['nodeId']==NODE and value['nodeCredit']==0 and value['nodeExitSatisfied'] is False
    assert value['finalIndependentReview'] is None and value['delivered'] is False
    assert sha(PREP/'materialize.py')==PREP_MATERIALIZER
    sys.dont_write_bytecode=True
    s=importlib.util.spec_from_file_location('r0023_preparation_guard',PREP/'verify_packet.py')
    guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
    guard.verify(PREP_SEAL,read_current=True)
    s=importlib.util.spec_from_file_location('r0023_materializer',PREP/'materialize.py')
    materializer=importlib.util.module_from_spec(s);s.loader.exec_module(materializer)
    policy=value['policyInput'];assert policy['canonicalPin'] and policy['rootJoin'] and policy['independentActualReview']
    expected=materializer.after_policy_join(policy['rootJoin']['path'],policy['rootJoin']['sha256'])
    expected['materializedAtUtc']=value['materializedAtUtc']
    expected['docsInput']['exactMaterializedAliasPostimage']=pin(ALIAS)
    assert value==expected,'Only admitted materializer deltas may replace the immutable template'
    assert sha(ALIAS)==ALIAS_SHA and ALIAS.read_bytes()==(PREP/'proposed/evidence/R0023/documentation.json').read_bytes()
    refs(value,seen)

def main():
    if sys.flags.optimize!=0: raise ValueError('Assertions must be enabled; do not invoke with -O')
    ap=argparse.ArgumentParser();ap.add_argument('--review-seal');ap.add_argument('--consumer')
    ap.add_argument('--ledger-before-sha256');ap.add_argument('--index-before-sha256')
    modes=ap.add_mutually_exclusive_group();modes.add_argument('--verify-only',action='store_true');modes.add_argument('--execute',action='store_true');a=ap.parse_args()
    if not (a.verify_only or a.execute):
        print(json.dumps({'status':'INERT_READ_ONLY_QUALIFY_JOIN_PROPOSAL','writes':0,'nodeCredit':0}));return
    assert a.review_seal and a.ledger_before_sha256 and a.index_before_sha256,'Exact final review and fresh paired CAS pins required'
    assert not a.execute or (a.consumer=='root' and Path(__file__).resolve()==INSTALL.resolve()),'Only installed root consumer may execute'
    lp=RUN/'ACTIVE_LEDGER.json';ip=RUN/'FINAL_REVIEW_INDEX.json';lb=lp.read_bytes();ib=ip.read_bytes();l=json.loads(lb);index=json.loads(ib)
    assert hashlib.sha256(lb).hexdigest()==a.ledger_before_sha256 and hashlib.sha256(ib).hexdigest()==a.index_before_sha256,'Fresh paired CAS identity mismatch'
    assert OUT.resolve().is_relative_to(RUN.resolve()) and TARGET.resolve().is_relative_to(RUN.resolve()) and DOC_TARGET.resolve().is_relative_to(RUN.resolve())
    for name in ['receipt.json','EFFECTS.json','READBACK.json','ACTIVE_LEDGER.before.json','FINAL_REVIEW_INDEX.before.json','ACTIVE_LEDGER.after.json','FINAL_REVIEW_INDEX.after.json']:
        assert not (OUT/name).exists(),'Prior/partial effects: reconcile, never replay'
    assert not TARGET.exists() and not DOC_TARGET.exists(),'Canonical preimages must both be absent'
    for path in [lp.with_suffix('.r0023-qualify-join.tmp'),ip.with_suffix('.r0023-qualify-join.tmp')]:assert not path.exists(),'Retained partial state staging'
    lease=l['resourceLeases']['heavy-browser'];assert lease['status']=='FREE' and lease['holder'] is None and not lease.get('unknownChildCompletion') and not lease.get('attentionRequired')
    assert l['coordinator']=='01a11f38-71a4-7be0-b2e0-a2faa9b7cb0b' and l['runRoot']==str(RUN)
    assert l['resourceLeases']['integrator']['capacity']==1 and l['resourceLeases']['integrator']['holder']=='root' and l['executionGovernance']['soleSharedIntegrator']=='root'
    pol=l['executionGovernance']['closureBoundAutoLoom'];finished=[b for b in pol['activeBundles'] if b['node']==NODE]
    assert len(finished)==1 and finished[0]['owner']=='root' and 'root' in finished[0]['workers'] and len(pol['activeBundles'])<=pol['maximumCompetingClosureBundles']
    review=seal(REVIEW,a.review_seal)
    assert review['schema']=='r0023-final-qualification-review/1' and review['reviewer']==REVIEWER and review['node']==NODE
    assert review['status']=='PASS_R0023_PRE_DELIVERY_QUALIFICATION_OWN_EXIT_WITH_LIMITS' and review['nodeLocalEvidenceExitSatisfied'] is True
    assert review['joinScript']==pin(Path(__file__).resolve())
    assert sha(PLAN/'CLOSURE_DAG.json')==l['graphSha256']==GRAPH_SHA
    graph=read(PLAN/'CLOSURE_DAG.json');assert len(graph['nodes'])==len(l['nodes'])==213 and len(graph['edges'])==409
    defs={x['id']:x for x in graph['nodes']};nodes={x['id']:x for x in l['nodes']};assert set(defs)==set(nodes);n=nodes[NODE]
    doc_progress_before=enc(nodes['R0023-DOC']['progress'])
    assert n['progress']['state'] in ['READY','EXECUTING'] and not n['progress']['exitCriteriaVerified'] and not n['progress']['unmetPredecessors']
    assert all(nodes[e['from']]['progress']['state']=='COMPLETE' and nodes[e['from']]['progress']['exitCriteriaVerified'] for e in graph['edges'] if e['to']==NODE)
    assert defs[NODE]['inputs']==n['inputs']==[],'No invented graph input fields'
    seen=set();refs(review,seen)
    value=read(CANDIDATE);reviewed_input(value,seen)
    core=review['decisionCore'];assert core['atUtc']==review['atUtc']
    validate_core(core,value,pin(CANDIDATE),pin(ALIAS),defs[NODE])
    assert [x['id'] for x in defs[NODE]['outputs']]==['r0023-reviewed-candidate/v1']
    assert defs[NODE]['outputs'][0]['artifact']=='evidence/R0023/reviewed-candidate-certificate.json'
    output=review['outputDispositions'];assert len(output)==2
    expected_ids=['r0023-reviewed-candidate/v1','r0023-documentation/v1']
    targets=[TARGET,DOC_TARGET];bodies=[];canonical=[]
    expected_dispositions=['APPROVED_REVIEWED_PRE_DELIVERY_CANDIDATE_ENVELOPE','APPROVED_ZERO_CREDIT_DOC_ALIAS_BOOKKEEPING']
    for item,ident,target,disposition in zip(output,expected_ids,targets,expected_dispositions):
        proposal=Path(item['proposal']['path']).resolve()
        assert item['id']==ident and item['canonicalTarget']==str(target) and item['currentCanonicalPreimage'] is None and not target.exists()
        assert item['disposition']==disposition and item['postimage']=={k:item['proposal'][k] for k in ['bytes','sha256']}
        captured=proposal.read_bytes()
        captured_postimage={'bytes':len(captured),'sha256':hashlib.sha256(captured).hexdigest()}
        assert captured_postimage==item['postimage'],'Captured output differs from independently approved postimage'
        captured_pin={'path':str(proposal),**captured_postimage}
        if ident=='r0023-reviewed-candidate/v1':
            assert proposal.is_relative_to(REVIEW.resolve()) and item['proposal']==captured_pin
            assert captured==enc(build_certificate(core,value)),'Certificate must be the exact independently approved acyclic derivation'
        else:
            assert proposal==ALIAS.resolve() and item['proposal']==captured_pin and item['newDOCNodeCredit']==0 and captured_postimage['sha256']==ALIAS_SHA
        bodies.append(captured);canonical.append({'id':ident,'path':str(target),**item['postimage']})
    counts=collections.Counter(x['progress']['state'] for x in l['nodes']);assert counts['COMPLETE']==59
    projection=index['currentExecutionProjection'];assert projection['completeNodes']==59 and projection['totalNodes']==213 and type(projection['observedIntervalExits']) is int
    now=dt.datetime.now(dt.timezone.utc).isoformat();rp=OUT/'receipt.json'
    elapsed=(dt.datetime.fromisoformat(now)-dt.datetime.fromisoformat(review['atUtc'])).total_seconds();assert elapsed>=0
    own=core['ownExitDispositions']
    criteria=[{'criterion':x['literal'],'disposition':'SATISFIED','evidence':[str(REVIEW/'REPORT.json')]+[y['path'] for y in x['supportingArtifactRefs']]} for x in own]
    receipt={'schema':'root-reviewed-node-exit-join/1','atUtc':now,'node':NODE,'status':'COMPLETE_OWN_EXITS_ONLY','stage':'PRE_DELIVERY_CANDIDATE',
        'independentReviewer':REVIEWER,'independentReview':pin(REVIEW/'REPORT.json'),'independentReviewSeal':pin(REVIEW/'SEAL.json'),
        'joinScript':pin(Path(__file__).resolve()),'sourceRuntimeSha256':RUNTIME,'sourceFreeze':pin(PREP/'FINAL_SOURCE_FREEZE.json'),
        'acceptedImmutableCandidate':pin(CANDIDATE),'independentDecisionCoreSha256':hashlib.sha256(enc(core)).hexdigest(),
        'requiredOutputs':[canonical[0]],'documentationAliasBookkeeping':{'output':canonical[1],'newDOCNodeCredit':0,'historicalCanonicalPreimageAbsent':True},
        'requiredOutputReadbackExact':True,'criterionDispositions':criteria,'originalObligationRows':25,'originalAcceptanceIds':ACCEPTANCE,
        'additionalDocAcceptanceId':'R0023-A11','laterDeliveredClosureAcceptanceId':'R0023-A10',
        'acceptedMETADATAJoin':value['metadataInput']['rootJoin'],'acceptedPOLICYJoin':value['policyInput']['rootJoin'],
        'sourceAndReviewPinsVerified':len(seen),'beforeCompleteCount':59,'afterCompleteCount':60,'completionDelta':1,
        'ledgerBeforeSha256':a.ledger_before_sha256,'indexBeforeSha256':a.index_before_sha256,'reviewReportToJoinSeconds':elapsed,
        'historicalFailureEvidencePreserved':True,'newNativeExecutionByJoin':False,'residualGates':core['downstreamGates'],
        'preservedLimits':core['preservedLimits'],'issueClosed':False,'mergeDeploymentAuthorized':False,'delivered':False,'fullRuntimeEquivalenceToCurrent07':False}
    n.update(executionStatus='COMPLETE_EXIT_VERIFIED',lastUpdatedAtUtc=now,independentReviewer=REVIEWER,nextAction='Separate approved merge/public delivery/evidence comment/manual issue35 closure remain PENDING.')
    n.setdefault('outputReceipts',[]).extend([str(TARGET),str(rp)])
    n['progress']['evidence']=list(dict.fromkeys(n['progress']['evidence']+[str(TARGET),str(REVIEW/'REPORT.json'),str(rp)]))
    n['progress'].update(state='COMPLETE',exitCriteriaVerified=True,completedAtUtc=now,runtime=RUNTIME,
        reason='All25 original rows and all3 literal exits independently accepted PRE_DELIVERY; canonical certificate and zero-credit DOC alias joined.',exitCriteriaDisposition=criteria,owners=['root',REVIEWER])
    doc=nodes['R0023-DOC'];assert doc['progress']['state']=='COMPLETE' and doc['progress']['exitCriteriaVerified']
    doc['outputReceipts']=list(dict.fromkeys(doc['outputReceipts']+[str(DOC_TARGET),str(rp)]))
    doc['canonicalAliasBookkeeping']={'atUtc':now,'canonicalOutput':canonical[1],'review':pin(REVIEW/'REPORT.json'),'rootReceipt':str(rp),'newNodeCredit':0,'historicalCanonicalPreimageAbsent':True}
    for x in l['nodes']:
        x['progress']['unmetPredecessors']=[k for k in x['progress'].get('unmetPredecessors',[]) if nodes[k]['progress']['state']!='COMPLETE']
        for inp in x.get('inputs',[]):
            for producer,ident,target in [('R0023-DOC','r0023-documentation/v1',DOC_TARGET),(NODE,'r0023-reviewed-candidate/v1',TARGET)]:
                if inp.get('id')==ident and inp.get('producerNode')==producer:
                    inp.update(status='SATISFIED',evidence=[str(target),str(rp),str(REVIEW/'REPORT.json')],stage='PRE_DELIVERY_CANDIDATE',delivered=False)
    c=l['closureDirectedProgress'];c['throughput']['completionReceipts'].append(str(rp));assert NODE not in c['throughput'].get('newVerifiedExits',[])
    c['throughput']['newVerifiedExits']=list(dict.fromkeys(c['throughput'].get('newVerifiedExits',[])+[NODE]))
    c['reviewJoinQueueMetrics']['consumedReviews'].append({'review':str(REVIEW),'recordedAtUtc':review['atUtc'],'rootConsumedAtUtc':now,'elapsedToRootConsumptionMinutes':elapsed/60,'scope':'R0023-QUALIFY exact final own-exit review and zero-credit DOC alias to canonical JOIN'})
    pol['activeBundles']=[b for b in pol['activeBundles'] if b['node']!=NODE];pol.setdefault('completedBundles',[]).append({**finished[0],'completedAtUtc':now,'receipt':str(rp),'status':'COMPLETE_OWN_EXITS_ONLY'})
    l['updatedAtUtc']=now;l['nextAction']='R0023 pre-delivery qualification complete; actual delivery/owner authority/issue closure remain PENDING.'
    projection.update(atUtc=now,completeNodes=60,observedIntervalExits=projection['observedIntervalExits']+1)
    projection['activeClosureNextGates']=[x for x in projection.get('activeClosureNextGates',[]) if x['node']!=NODE]
    projection['retainedRootExitReceipts'].append({'node':NODE,'atUtc':now,'receipt':{'path':str(rp),'bytes':len(enc(receipt)),'sha256':hashlib.sha256(enc(receipt)).hexdigest()},'independentReviewer':REVIEWER,'sourceManifest':RUNTIME,'nativeScope':'Exact DOC/METADATA/POLICY producer scopes and25-row PRE_DELIVERY candidate only; no delivery or whole-runtime qualification','delivered':False});index['updatedAtUtc']=now
    # Build every exact postimage before any canonical or ledger effect.
    la=enc(l);ia=enc(index);ra=enc(receipt)
    assert sum(x['progress']['state']=='COMPLETE' for x in json.loads(la)['nodes'])==60
    assert enc(doc['progress'])==doc_progress_before,'DOC progress/earned criteria must stay unchanged; alias adds zero credit'
    if not a.execute:
        print(json.dumps({'status':'PASS_EXACT_JOIN_PREFLIGHT_ONLY','refs':len(seen),'originalRows':25,'writes':False,'nativeExecuted':False,'nodeCredit':0,'prospectiveCounts':[59,60],'canonicalPostimages':canonical}));return
    assert lp.read_bytes()==lb and ip.read_bytes()==ib
    (OUT/'ACTIVE_LEDGER.before.json').write_bytes(lb);(OUT/'FINAL_REVIEW_INDEX.before.json').write_bytes(ib)
    (OUT/'ACTIVE_LEDGER.after.json').write_bytes(la);(OUT/'FINAL_REVIEW_INDEX.after.json').write_bytes(ia)
    journal={'atUtc':now,'status':'EFFECTS_STARTED_NO_COMPLETION_CREDIT','node':NODE,'review':pin(REVIEW/'REPORT.json'),'steps':[]}
    save(OUT/'EFFECTS.json',journal)
    try:
        assert lp.read_bytes()==lb and ip.read_bytes()==ib
        for target,raw in zip(targets,bodies):
            assert lp.read_bytes()==lb and ip.read_bytes()==ib
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as f:f.write(raw)
            assert target.read_bytes()==raw;journal['steps'].append('canonical-exact-approved-bytes:'+target.name);save(OUT/'EFFECTS.json',journal)
        for dest,old,raw in [(ip,ib,ia),(lp,lb,la)]:
            assert dest.read_bytes()==old,'State drift before staging '+str(dest)
            tmp=dest.with_suffix('.r0023-qualify-join.tmp');assert not tmp.exists();tmp.write_bytes(raw)
            assert dest.read_bytes()==old,'State drift immediately before replacement '+str(dest)
            os.replace(tmp,dest);assert dest.read_bytes()==raw
            journal['steps'].append(dest.name+'-replaced-readback');save(OUT/'EFFECTS.json',journal)
        assert lp.read_bytes()==la and ip.read_bytes()==ia and all(t.read_bytes()==b for t,b in zip(targets,bodies)),'Paired/canonical postimage drift'
        with rp.open('xb') as f:f.write(ra)
        assert rp.read_bytes()==ra and lp.read_bytes()==la and ip.read_bytes()==ia and all(t.read_bytes()==b for t,b in zip(targets,bodies))
        journal['status']='COMPLETE_WITH_EXACT_READBACK';journal['receipt']=pin(rp);save(OUT/'EFFECTS.json',journal)
    except BaseException as error:
        journal.update(status='PARTIAL_EFFECTS_RECONCILIATION_REQUIRED_NO_RETRY',error=repr(error),completionCredit='UNVERIFIED_UNTIL_ROOT_RECONCILIATION',observedArtifacts=[])
        for path in [lp,ip,TARGET,DOC_TARGET,rp,lp.with_suffix('.r0023-qualify-join.tmp'),ip.with_suffix('.r0023-qualify-join.tmp')]:
            try:journal['observedArtifacts'].append(pin(path) if path.is_file() else {'path':str(path),'exists':path.exists()})
            except BaseException as observation_error:journal['observedArtifacts'].append({'path':str(path),'observationError':repr(observation_error)})
        save(OUT/'EFFECTS.json',journal);raise
    save(OUT/'READBACK.json',{'receipt':pin(rp),'ledger':pin(lp),'index':pin(ip),'canonicalOutputs':[pin(TARGET),pin(DOC_TARGET)],'counts':dict(collections.Counter(x['progress']['state'] for x in l['nodes'])),'DOCNodeCredit':0,'QUALIFYCompletionDelta':1})
    print(json.dumps({'receipt':pin(rp),'counts':dict(collections.Counter(x['progress']['state'] for x in l['nodes']))}))
if __name__=='__main__':main()
