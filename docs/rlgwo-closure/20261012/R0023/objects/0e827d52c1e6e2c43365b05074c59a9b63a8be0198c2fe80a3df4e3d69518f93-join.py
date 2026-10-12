"""Root-only reviewed R0023 policy JOIN. Preflight has no writes or native effects."""
import argparse, collections, datetime as dt, hashlib, json, os
from pathlib import Path
RUN=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
REVIEW=RUN/'workers/location_policy_final_actual_review_r1/final-r1'
PLAN=Path('C:/Users/theis/Documents/Codex/celestial-startup-repair-20261008/planning-original-21e7a843/docs/rlgwo-execution/20261008')
RUNTIME='e718fe9e58f37535de4dc496a2da3bf2b05808153287e1fe328398ea59c0df53'
NODE='R0023-POLICY'
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
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--review-seal',required=True);modes=ap.add_mutually_exclusive_group();modes.add_argument('--verify-only',action='store_true');modes.add_argument('--execute',action='store_true');a=ap.parse_args()
    lp=RUN/'ACTIVE_LEDGER.json';ip=RUN/'FINAL_REVIEW_INDEX.json';lb=lp.read_bytes();ib=ip.read_bytes();l=json.loads(lb);index=json.loads(ib)
    assert not (OUT/'receipt.json').exists() and not (OUT/'EFFECTS.json').exists(),'Prior effects: reconcile, never replay'
    lease=l['resourceLeases']['heavy-browser'];assert lease['status']=='FREE' and lease['holder'] is None and not lease.get('unknownChildCompletion') and not lease.get('attentionRequired')
    assert l['coordinator']=='01a11f38-71a4-7be0-b2e0-a2faa9b7cb0b' and l['runRoot']==str(RUN)
    assert l['resourceLeases']['integrator']['capacity']==1 and l['resourceLeases']['integrator']['holder']=='root'
    pol=l['executionGovernance']['closureBoundAutoLoom'];finished=[b for b in pol['activeBundles'] if b['node']==NODE]
    assert len(finished)==1 and finished[0]['owner']=='root' and 'root' in finished[0]['workers'] and len(pol['activeBundles'])<=pol['maximumCompetingClosureBundles']
    review=seal(REVIEW,a.review_seal)
    assert review['reviewer']=='/root/r0008_native_actual_exit_review_r1' and review['node']==NODE
    assert review['status']=='PASS_R0023_POLICY_NODE_LOCAL_EXIT_WITH_LIMITS' and review['nodeLocalEvidenceExitSatisfied'] is True
    assert review['joinScript']==pin(Path(__file__).resolve())
    assert sha(PLAN/'CLOSURE_DAG.json')==l['graphSha256']=='9ac372cfcce4df94ee0e678b907e66c131fe49f72cc55106143aa35dbdb0a6e7'
    graph=read(PLAN/'CLOSURE_DAG.json');assert len(graph['nodes'])==213 and len(graph['edges'])==409
    defs={x['id']:x for x in graph['nodes']};nodes={x['id']:x for x in l['nodes']};n=nodes[NODE]
    assert n['progress']['state'] in ['AWAITING_REVIEW','EXECUTING'] and not n['progress']['exitCriteriaVerified']
    assert all(nodes[e['from']]['progress']['state']=='COMPLETE' for e in graph['edges'] if e['to']==NODE)
    own=review['ownExitDispositions'];assert [x['literal'] for x in own]==defs[NODE]['exitCriteria']
    assert all(x['disposition']=='SATISFIED' and x['supportingArtifactRefs'] for x in own)
    seen=set();refs(review,seen)
    candidate=OUT/'candidate/policy-manifest.json';candidate_bytes=candidate.read_bytes();value=json.loads(candidate_bytes)
    candidate_pin={'path':str(candidate),'bytes':len(candidate_bytes),'sha256':hashlib.sha256(candidate_bytes).hexdigest()}
    assert review['outputDisposition']['proposal']==candidate_pin
    target=RUN/'evidence/R0023/policy-manifest.json'
    assert defs[NODE]['outputs']==[{'id':'r0023-native-policy/v1','contract':'Exact native parent/header/allow/grant/callback matrix without JS geolocation replacement','artifact':'evidence/R0023/policy-manifest.json'}]
    assert review['outputDisposition']['canonicalTarget']==str(target) and review['outputDisposition']['currentCanonicalPreimage'] is None and not target.exists()
    assert review['outputDisposition']['disposition']=='PASS_NODE_LOCAL_POLICY_OUTPUT_WITH_RETAINED_LIMITS'
    assert value['node']==NODE and value['runtimeSha256']==RUNTIME and value['status']=='ASSEMBLED_PENDING_INDEPENDENT_NODE_EXIT'
    original_names=read(RUN/'workers/location_policy_fixture_review_r2/ROOT_COMMAND.json')['caseIds']
    assert len(original_names)==16 and len(set(original_names))==16
    registry=[{'name':name,'acceptance':'R0023-A07' if '-native-' in name else 'R0023-A08'} for name in original_names]
    cases=value['cases'];assert [x['descriptor'] for x in cases]==registry
    assert review['acceptedCases']==16 and review['remainingCases']==0
    assert [x['name'] for x in review['caseDispositions']]==[x['name'] for x in registry]
    assert all(x['disposition']=='ACCEPTED' and x['supportingArtifactRefs'] for x in review['caseDispositions'])
    for x in cases:
        raw=read(Path(x['raw']['path']));assert raw['name']==x['descriptor']['name'] and raw['acceptance']==x['descriptor']['acceptance']
        expected='PASS'
        assert raw['status']==x['rawStatus']==expected
        if expected=='PASS':assert raw['checks'] and all(c['passed'] is True for c in raw['checks'])
    assert value['retainedWidgetReview']['sha256']=='7c51be5e5fbf2d2380231df6354ff97efa490c9026fa45f5d5475e4cdf30cf1b'
    refs(value,seen)
    counts=collections.Counter(x['progress']['state'] for x in l['nodes']);assert counts['COMPLETE']==58
    projection=index['currentExecutionProjection'];assert projection['completeNodes']==counts['COMPLETE'] and type(projection['observedIntervalExits']) is int
    complete_after=counts['COMPLETE']+1
    now=dt.datetime.now(dt.timezone.utc).isoformat();rp=OUT/'receipt.json'
    target_pin={'path':str(target),'bytes':len(candidate_bytes),'sha256':candidate_pin['sha256']}
    criteria=[{'criterion':x['literal'],'disposition':'SATISFIED','evidence':[str(REVIEW/'REPORT.json')]+[y['path'] for y in x['supportingArtifactRefs']]} for x in own]
    receipt={'schema':'root-reviewed-node-exit-join/1','atUtc':now,'node':NODE,'status':'COMPLETE_OWN_EXITS_ONLY','independentReviewer':review['reviewer'],'independentReview':pin(REVIEW/'REPORT.json'),'independentReviewSeal':pin(REVIEW/'SEAL.json'),'joinScript':pin(Path(__file__).resolve()),'sourceRuntimeSha256':RUNTIME,'requiredOutputs':[{'id':'r0023-native-policy/v1',**target_pin}],'requiredOutputReadbackExact':True,'criterionDispositions':criteria,'originalNativeCases':16,'sourceAndReviewPinsVerified':len(seen),'reviewReportToJoinSeconds':(dt.datetime.fromisoformat(now)-dt.datetime.fromisoformat(review['atUtc'])).total_seconds(),'historicalFailureEvidencePreserved':True,'newNativeExecutionByJoin':False,'residualGates':review['residualGates'],'visualLimits':review['visualLimits'],'issueClosed':False,'mergeDeploymentAuthorized':False,'fullRuntimeEquivalenceToCurrent07':False}
    n.update(executionStatus='COMPLETE_EXIT_VERIFIED',lastUpdatedAtUtc=now,independentReviewer=review['reviewer'],nextAction='R0023-QUALIFY, delivery and whole-issue closure retain their separate gates.')
    n.setdefault('outputReceipts',[]).extend([str(target),str(rp)])
    n['progress']['evidence']=list(dict.fromkeys(n['progress']['evidence']+[str(target),str(REVIEW/'REPORT.json'),str(rp)]))
    n['progress'].update(state='COMPLETE',exitCriteriaVerified=True,completedAtUtc=now,runtime=RUNTIME,reason='All16 original controlled policy/error recipes independently accepted; all3literal own exits satisfied; canonical output joined.',exitCriteriaDisposition=criteria,owners=['root',review['reviewer']])
    for x in l['nodes']:
        x['progress']['unmetPredecessors']=[k for k in x['progress'].get('unmetPredecessors',[]) if nodes[k]['progress']['state']!='COMPLETE']
        for inp in x.get('inputs',[]):
            if inp.get('id')=='r0023-native-policy/v1' and inp.get('producerNode')==NODE:
                inp.update(status='SATISFIED',evidence=[str(target),str(rp),str(REVIEW/'REPORT.json')],sourceRuntimeSha256=RUNTIME)
    q=nodes['R0023-QUALIFY']
    if q['progress']['state']=='NOT_STARTED' and not q['progress']['unmetPredecessors']:
        q['progress'].update(state='READY',reason='All own hard predecessor outputs accepted; independent pre-delivery qualification may consume them.')
    c=l['closureDirectedProgress'];c['throughput']['completionReceipts'].append(str(rp));c['throughput']['newVerifiedExits']=list(dict.fromkeys(c['throughput'].get('newVerifiedExits',[])+[NODE]))
    c['reviewJoinQueueMetrics']['consumedReviews'].append({'review':str(REVIEW),'recordedAtUtc':review['atUtc'],'rootConsumedAtUtc':now,'elapsedToRootConsumptionMinutes':receipt['reviewReportToJoinSeconds']/60,'scope':'R0023-POLICY exact final own-exit review to canonical JOIN'})
    pol['activeBundles']=[b for b in pol['activeBundles'] if b['node']!=NODE];pol.setdefault('completedBundles',[]).append({**finished[0],'completedAtUtc':now,'receipt':str(rp),'status':'COMPLETE_OWN_EXITS_ONLY'})
    l['updatedAtUtc']=now;l['nextAction']='Consume prepared R0023-QUALIFY after this verified POLICY exit; preserve deferred and release scopes.'
    projection.update(atUtc=now,completeNodes=complete_after,observedIntervalExits=projection['observedIntervalExits']+1)
    projection['retainedRootExitReceipts'].append({'node':NODE,'atUtc':now,'receipt':{'path':str(rp),'bytes':len(enc(receipt)),'sha256':hashlib.sha256(enc(receipt)).hexdigest()},'independentReviewer':review['reviewer'],'sourceManifest':RUNTIME,'nativeScope':'R0023 controlled policy/error16 original Chromium cases only; no actual extension/new-tab/sensor/public proof','delivered':False});index['updatedAtUtc']=now
    # Build every exact postimage before any canonical or ledger effect.
    la=enc(l);ia=enc(index);ra=enc(receipt)
    assert sum(x['progress']['state']=='COMPLETE' for x in json.loads(la)['nodes'])==complete_after
    if not a.execute:
        print(json.dumps({'status':'PASS_EXACT_JOIN_PREFLIGHT_ONLY','refs':len(seen),'cases':16,'writes':False,'nativeExecuted':False,'nodeCredit':0}));return
    assert lp.read_bytes()==lb and ip.read_bytes()==ib
    (OUT/'ACTIVE_LEDGER.before.json').write_bytes(lb);(OUT/'FINAL_REVIEW_INDEX.before.json').write_bytes(ib)
    (OUT/'ACTIVE_LEDGER.after.json').write_bytes(la);(OUT/'FINAL_REVIEW_INDEX.after.json').write_bytes(ia)
    journal={'atUtc':now,'status':'EFFECTS_STARTED_NO_COMPLETION_CREDIT','node':NODE,'review':pin(REVIEW/'REPORT.json'),'steps':[]}
    save(OUT/'EFFECTS.json',journal)
    try:
        assert lp.read_bytes()==lb and ip.read_bytes()==ib
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(candidate_bytes)
        assert target.read_bytes()==candidate_bytes;journal['steps'].append('canonical-exact-approved-bytes');save(OUT/'EFFECTS.json',journal)
        for dest,old,raw in [(ip,ib,ia),(lp,lb,la)]:
            assert dest.read_bytes()==old,'State drift before staging '+str(dest)
            tmp=dest.with_suffix('.r0023-join.tmp');assert not tmp.exists();tmp.write_bytes(raw)
            assert dest.read_bytes()==old,'State drift immediately before replacement '+str(dest)
            os.replace(tmp,dest);assert dest.read_bytes()==raw
            journal['steps'].append(dest.name+'-replaced-readback');save(OUT/'EFFECTS.json',journal)
        assert lp.read_bytes()==la and ip.read_bytes()==ia and target.read_bytes()==candidate_bytes,'Paired/canonical postimage drift'
        with rp.open('xb') as f:f.write(ra)
        assert rp.read_bytes()==ra and lp.read_bytes()==la and ip.read_bytes()==ia and target.read_bytes()==candidate_bytes
        journal['status']='COMPLETE_WITH_EXACT_READBACK';journal['receipt']=pin(rp);save(OUT/'EFFECTS.json',journal)
    except BaseException as error:
        journal.update(status='PARTIAL_EFFECTS_RECONCILIATION_REQUIRED_NO_RETRY',error=repr(error),completionCredit='UNVERIFIED_UNTIL_ROOT_RECONCILIATION',observedArtifacts=[])
        for path in [lp,ip,target,rp,lp.with_suffix('.r0023-join.tmp'),ip.with_suffix('.r0023-join.tmp')]:
            try:journal['observedArtifacts'].append(pin(path) if path.is_file() else {'path':str(path),'exists':path.exists()})
            except BaseException as observation_error:journal['observedArtifacts'].append({'path':str(path),'observationError':repr(observation_error)})
        save(OUT/'EFFECTS.json',journal);raise
    save(OUT/'READBACK.json',{'receipt':pin(rp),'ledger':pin(lp),'index':pin(ip),'canonicalOutput':pin(target),'counts':dict(collections.Counter(x['progress']['state'] for x in l['nodes']))})
    print(json.dumps({'receipt':pin(rp),'counts':dict(collections.Counter(x['progress']['state'] for x in l['nodes']))}))
if __name__=='__main__':main()
