import sys,json,pathlib,hashlib,datetime,subprocess
sys.stdout.reconfigure(encoding='utf-8')
R=pathlib.Path(r'C:\Users\theis\Documents\Codex\salah-rlgwo-execution-20261009');W=R/'workers/diagnostic_qualification_exit_r1';C=pathlib.Path(r'C:\Users\theis\.codex\worktrees\pr43-review-revision\salah_widget');P=pathlib.Path(r'C:\Users\theis\Documents\Codex\celestial-startup-repair-20261008\planning-original-21e7a843\docs\rlgwo-execution\20261008')
assert not (W/'SEAL.json').exists(),'Already sealed; no further write permitted'
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):p=pathlib.Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def verify(x):a=ref(x['path']);assert a['sha256']==x['sha256'],(a,x);assert a['bytes']==x.get('bytes',a['bytes']);return a
def write(name,v):p=W/name;p.write_text(json.dumps(v,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
node=read(W/'ORIGINAL_NODE.json');q=read(W/'evidence/R001C/qualification.json');report=read(W/'REPORT.json');inputs=read(W/'INPUT_PACKET_READBACK.json')
assert q['node']=='R001C-QUALIFY' and q['interface']=='r001c-qualification/v1';assert q['nodeExitSatisfied'] is True and q['nodeComplete'] is False and q['rootReconciliationPending'] is True;assert q['nodeCredit']==q['parentClosureCredit']==0
assert q['literalEntryCriteria']==node['entryCriteria'] and q['literalExitCriteria']==node['exitCriteria'] and q['literalOutputs']==node['outputs'] and q['literalInputs']==node['inputs']
assert len(q['inputDisposition'])==4 and len(q['acceptanceMap'])==11 and len(q['parentAndChildMap'])==7 and len(q['acceptedRows'])==4
assert q['remainingOwnInputRequirements']==[] and len(q['remainingRequirements'])==3
assert next(x for x in q['acceptanceMap'] if x['acceptance']=='R001C-A11')['status']=='DOWNSTREAM_REQUIRED_NOT_SATISFIED_BY_THIS_NODE'
for key in ['nativeQualified','M0OrCurrentRuntimeCredit','wholeDocumentPASS','wholePRPASS','mergeAuthorityGranted','delivered','issueClosureAuthorized','canonicalStateChangedByReviewer','issueClosed','publicDeliveryQualified']:assert q[key] is False,key
actualTargets=[x['canonicalTarget'] for x in report['outputs']];expectedTargets=[x['artifact'] for x in node['outputs']];assert actualTargets==expectedTargets
for x in report['outputs']:
 verify(x['proposed']);v=read(x['proposed']['path']);assert v['node']=='R001C-QUALIFY' and v['interface']==x['interface'];assert v['nodeCredit']==0 and not v['canonicalStateChangedByReviewer']
checked=[verify(x) for x in inputs['referencesVerified']]
currentRefs=q['sourceDocs']+[q['currentNative'],q['currentGenerated'],q['currentFixture']];sourceReadback=[verify(x) for x in currentRefs]
active=read(R/'ACTIVE_LEDGER.json');preds={x['id']:x['executionStatus'] for x in active['nodes'] if x['id'] in ['R001C-DOCS','R001C-FORCE-FIXTURE','R001C-BROWSER','R001C-RENDER']};assert len(preds)==4 and all(s=='COMPLETE_EXIT_VERIFIED' for s in preds.values())
z=subprocess.run(['git','-C',str(C),'rev-parse','HEAD'],capture_output=True,check=False);assert z.returncode==0 and z.stdout.decode().strip()=='50e46b7ecfde9c8bea9c0cf00b6017afaf27aab9'
assert ref(P/'CLOSURE_DAG.json')['sha256']=='9ac372cfcce4df94ee0e678b907e66c131fe49f72cc55106143aa35dbdb0a6e7'
write('AUTHORITIES.json',{'immutableGraph':ref(P/'CLOSURE_DAG.json'),'actualRLGWO':ref(P/'REMAINING_RLGWOs/R001C.md'),'actualMetadata':ref(P/'metadata/R001C.json'),'RUNBOOK':ref(R/'RUNBOOK.md'),'node':node['id'],'modelConfiguration':'Parent explicitly dispatched fresh independent Sol Max reviewer; this is a session-configuration statement, not provider routing attestation.','privateWriteRoot':str(W),'rootSoleCanonicalIntegrator':True,'formalImplementAuditOrAuditAssessRoute':False})
neg={}
bad=dict(report['outputs'][0]['proposed']);bad['sha256']='0'*64
try:verify(bad)
except AssertionError:neg['wrongOutputDigest']='REJECTED'
else:raise AssertionError('Wrong digest was admitted')
try:assert set(actualTargets[:-1])==set(expectedTargets)
except AssertionError:neg['missingOutput']='REJECTED'
else:raise AssertionError('Missing output was admitted')
try:assert 'R001C-RELEASE-REVIEW'==node['id']
except AssertionError:neg['wrongNode']='REJECTED'
else:raise AssertionError('Wrong node was admitted')
# Every JSON document in the private tree must parse; attempts retain scripts/errors, not malformed outputs.
jsonMembers=list(W.rglob('*.json'))
for p in jsonMembers:read(p)
write('FINAL_READBACK.json',{'schema':'r001c-qualification-final-private-readback/1','atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'node':node['id'],'exactOutputs':report['outputs'],'inputReferencesVerified':len(checked),'currentSourceReadback':sourceReadback,'head':z.stdout.decode().strip(),'predecessors':preds,'privateJSONMembersParsed':len(jsonMembers),'adversarialPacketControls':neg,'freshNativeVmBrowserBuildNetwork':0,'canonicalChangesByReviewer':False,'nodeCredit':0,'rootReconciliationPending':True})
manifest={'schema':'r001c-qualification-private-manifest/1','members':[]}
for p in sorted(W.rglob('*')):
 if p.is_file() and p.name not in ['MANIFEST.json','SEAL.json']:b=p.read_bytes();manifest['members'].append({'path':p.relative_to(W).as_posix(),'bytes':len(b),'sha256':sha(b)})
write('MANIFEST.json',manifest)
for x in manifest['members']:verify({**x,'path':str(W/x['path'])})
seal={'schema':'r001c-qualification-private-seal/1','atUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'/root/diagnostic_qualification_exit','node':'R001C-QUALIFY','manifest':ref(W/'MANIFEST.json'),'memberCount':len(manifest['members']),'report':ref(W/'REPORT.json'),'outputs':report['outputs'],'decision':report['decision'],'nodeExitSatisfied':True,'rootReconciliationPending':True,'nodeCredit':0,'parentClosureCredit':0,'privateWritesOnly':True,'immutableAfterSeal':True,'nativeQualified':False,'M0OrCurrentRuntimeCredit':False,'wholeDocumentPASS':False,'delivered':False,'issueClosed':False,'stopAfterSealedReturn':True}
write('SEAL.json',seal)
# Exact readback after the terminal seal, without adding or altering a file.
sv=read(W/'SEAL.json');verify(sv['manifest']);verify(sv['report'])
for x in read(W/'MANIFEST.json')['members']:verify({**x,'path':str(W/x['path'])})
for x in sv['outputs']:verify(x['proposed'])
print(json.dumps({'sealed':True,'seal':ref(W/'SEAL.json'),'manifest':ref(W/'MANIFEST.json'),'report':ref(W/'REPORT.json'),'membersVerifiedAfterSeal':len(manifest['members']),'ownExitProposed':True,'nodeCredit':0,'issueClosed':False,'stop':True}))
