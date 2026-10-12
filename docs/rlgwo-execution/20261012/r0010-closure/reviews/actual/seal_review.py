"""Assemble only this reviewer's bounded actual-return decision."""
from pathlib import Path
import datetime as dt, hashlib, json, struct

W=Path(__file__).resolve().parent
R=Path(r'C:\Users\theis\Documents\Codex\salah-rlgwo-execution-20261009')
A=R/'workers/r0010_delivered_native_closure_r2/actual-return-r1'
S=A.parent
O=R/'evidence/R0010/preferences-delivered-main-r2'
D=R/'evidence/R0010/preferences-delivered-dispatch-r2'
Q=W.parent/'delivered-native-source-admission-r2'
read=lambda p:json.loads(p.read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def save(n,v):
 with (W/n).open('xb') as f:f.write((json.dumps(v,indent=2)+'\n').encode())

v=read(W/'VERIFICATION.json');assert v['status']=='PASS' and len(v['rows'])==10
cases=[x['case'] for x in v['rows']]
association=read(A/'CASE_ASSOCIATION.json')
association_rows=[]
for c,a in zip(cases,association['rows']):
 row=read(O/c/'result.json'); assert c==a['case'] and row['acceptance']==a['acceptance']
 snapshots={}
 for name,s in row['snapshots'].items():
  r=s['report'];saved=next((val for key,val in r['storage'] if key=='salah_widget:config:v1'),None)
  derived={'config':{k:s['config'].get(k) for k in ['lat','lon','tz','label','method','units','source','savedAt']},'visibleInputValues':{k:s['app']['inputs'][k] for k in ['set-method','set-units']}}
  derived.update({k:r[k] for k in ['sourceSha256','configSha256','runtimeInventorySha256','target','scriptCount','productionScriptBodiesPreserved','storageMode','seedApplied','bytesBeforeSeed']})
  derived.update(savedNativeBytes=saved,savedNativeBytesSha256=sha(saved.encode()) if saved is not None else None,coarseRequestCount=sum('geojs' in x['url'] or 'ipinfo' in x['url'] for x in r['requests']),configKeySetCount=sum(x[0]=='set' and x[1]=='salah_widget:config:v1' for x in r['storageEvents']))
  assert derived==a['snapshots'][name],c+': association snapshot differs'
  snapshots[name]=derived
 images=set()
 for crop in row['crops']:
  assert crop['geometry']['.c']['width']==325 and crop['geometry']['.c']['height']==530
  images.update([crop['file'],crop['cardFile']])
 if row.get('selectedFailureEvidence'):images.add(row['selectedFailureEvidence']['fieldCrop']['file'])
 assert images=={x['path'] for x in a['images']} and all(Path(p).parent==O/c for p in images)
 association_rows.append({'case':c,'snapshotAssociation':'EXACT','imageAssociation':'EXACT','images':len(images)})

native_log=[json.loads(line) for line in (D/'stdout.log').read_text(encoding='utf-8').splitlines()]
assert [(r['name'],r['status']) for r in native_log]==[(r['case'],r['independentDisposition']) for r in v['rows']]
assert (D/'stderr.log').read_bytes()==b''
options=read(O/'launch-options.json');assert options['only']==cases and options['sourceRef']==v['sourceHead'] and options['leaseId']==v['custody']['leaseId'] and options['leaseAuthorized'] is True and options['validateOnly'] is False and options['list'] is False and options['stopOnFailure'] is True
before,active,after=[read(D/('ACTIVE_LEDGER.'+n+'.json')) for n in ['before','active','after']]
changed=[k for k in before if before[k]!=after[k]]
assert set(changed)=={'resourceLeases','updatedAtUtc'}
assert {k:val for k,val in before['resourceLeases'].items() if k!='heavy-browser'}=={k:val for k,val in after['resourceLeases'].items() if k!='heavy-browser'}
save('ASSOCIATION_VERIFICATION.json',{'schema':'r0010-independent-raw-association-review/1','status':'PASS','rows':association_rows,'nativeStdout':ref(D/'stdout.log'),'nativeStderr':ref(D/'stderr.log'),'exactOrderedStdoutRows':10,'launchOptions':ref(O/'launch-options.json'),'beforeAfterChangedTopLevel':changed,'otherResourceLeasesUnchanged':True,'nodeIssueEffectValuesUnchanged':True,'nativeAcquisitionByReviewer':False})

observations=[
 ('fresh-2-f/fresh-selected-card.png','Madinah, ISNA method 2 and degrees F visible; full settings card.'),
 ('fresh-2-c/fresh-selected-card.png','Madinah, ISNA method 2 and degrees C visible; full settings card.'),
 ('fresh-4-f/fresh-selected-card.png','Madinah, Umm al-Qura method 4 and degrees F visible; full settings card.'),
 ('fresh-4-c/fresh-selected-card.png','Madinah, Umm al-Qura method 4 and degrees C visible; full settings card.'),
 ('generic-local/generic-local-card.png','Generic detection shows Madinah, Umm al-Qura method 4 and degrees C.'),
 ('saved-native-reload/saved-first-card.png','First saved boot shows London 51.5/-0.12, Muslim World League method 3 and degrees C.'),
 ('saved-native-reload/saved-reload-card.png','After actual reload and opening settings, London 51.5/-0.12, method 3 and degrees C remain visible.'),
 ('prefer-local-fresh/prefer-fresh-card.png','Fixed fallback coordinates 24.47/39.61, ISNA method 2 and degrees F visible; empty label is retained original input.'),
 ('prefer-local-saved/prefer-saved-card.png','Saved London coordinates, method 3 and degrees C visible.'),
 ('mutant-omitMethod/selected-preference-failure-card.png','Actual consumer visibly has wrong Umm al-Qura method 4, with requested degrees F retained.'),
 ('mutant-omitMethod/wrong-set-method.png','Isolated wrong-method crop visibly reads Umm al-Qura, Makkah.'),
 ('mutant-omitUnits/selected-preference-failure-card.png','Actual consumer visibly has requested ISNA method 2, with wrong degrees C.'),
 ('mutant-omitUnits/wrong-set-units.png','Isolated wrong-unit crop visibly reads degrees C.')]
pixels=[]
for relative,observation in observations:
 p=O/relative;b=p.read_bytes();pixels.append({'image':ref(p),'dimensions':list(struct.unpack('>II',b[16:24])),'review':'PASS_WITHIN_PREFERENCE_SCOPE','observation':observation,'inspection':'Reviewer view_image of retained original PNG; no edit, generation or OCR substitute.'})
save('PIXEL_READBACK.json',{'schema':'r0010-independent-actual-preference-pixels/1','status':'PASS','reviewer':'/root/r0010_isolated_release_review_r1','directlyInspectedImages':13,'observedWidgetStates':11,'allOutputPNGsHashBound':24,'scope':'Visible selected method/units and settings card at fixed original epoch, original viewport and system fallback fonts. Whole renderer, numerical temperature, accessibility tree and speech are outside this review.','images':pixels,'fullViewportImages':'11 full frames are bound and associated; direct visual review used corresponding 11 card crops plus two isolated wrong-field crops.'})

accepted=[{**row,'reason':('Original selected-preference assertion correctly fails after requested omission; actual UTC witnesses and wrong-field crop agree.' if row['independentDisposition']=='CAUGHT' else 'Original consumer and visible-field predicates recomputed from source-bound raw evidence and inspected crop.')} for row in v['rows']]
report={
 'schema':'r0010-delivered-native-actual-review/1','atUtc':dt.datetime.now(dt.timezone.utc).isoformat(),'decision':'PASS','reviewer':'/root/r0010_isolated_release_review_r1',
 'subjectSeal':ref(A/'SEAL.json'),'subjectReport':ref(A/'REPORT.json'),'subjectAssociation':ref(A/'CASE_ASSOCIATION.json'),'authorSourceSeal':ref(S/'SEAL.json'),'independentSourceReviewSeal':ref(Q/'SEAL.json'),'sourceAdmission':ref(Q/'ADMISSION.json'),'ownerAuthority':read(A/'REPORT.json')['ownerAuthority'],
 'sourceHead':v['sourceHead'],'sourceGitTree':'d113e5fb0e121f0079180867cf6109a7f98bee96','runtimeSha256':v['runtimeSha256'],'runtimeFiles':135,'indexSha256':'ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee','configSha256':'91a37863cd85e232e9a63bba9db533b82699e63140086ba4b78fcf9c0581ec81','builderSha256':'66f1cd86cfb3d1e53b75c8840057564ccfa514a46cf1f13b6863673b0d83279e','readmeSha256':'f73a924c9ab855d3e1de79d2ba5e3bb0fda20bc26812f0aa84782d92ead3aa38',
 'dispatch':ref(D/'dispatch.json'),'orderedScope':cases,'acceptanceScope':['R0010-A02','R0010-A03','R0010-A04','R0010-A05'],'acceptedOriginalCaseRows':10,'positivePASS':8,'selectedPreferenceOmissionsCAUGHT':2,'actualAcquisitionBatches':1,'nativeReplay':False,'rows':accepted,
 'checks':{'sourceAdmissionAndReturnPacketPins':'PASS','sourcePacketMembersVerified':85,'readCurrentRetainedRuntimeFiles':135,'actualPostFinallyRuntimeGuard':'PASS_UNCHANGED','outputInventoryAndDispatchExact':'36/36','caseAndImageAssociation':'PASS','rawSemanticPredicates':'10/10','savedSeedOnceAndReloadNativeStorageBytes':'PASS','actualDocumentReplacementReceipt':'PASS','selectedOmissionAssertion':'2/2 CONSUMER_ASSERTION selected preference','actualUTCReadbacks':'Each omission case has builder-Windows, builder-Linux and actual-widget-consumer UTC witnesses before navigation and after production initialization.','directPixelReview':'13 retained PNGs, 11 observed states; all 24 PNGs bound.','offlineAdverseControls':'6/6 refused','custody':'Known returned integer exit 0; source-bound browser/server finally and post-finally runtime/lease guard reached; recorded lease FREE. No independent live process-absence acquisition by reviewer.','canonicalNodeIssueEffectValues':'Unchanged; before/after only resourceLeases and updatedAtUtc differ.'},
 'verification':ref(W/'VERIFICATION.json'),'associationVerification':ref(W/'ASSOCIATION_VERIFICATION.json'),'pixelReadback':ref(W/'PIXEL_READBACK.json'),'findings':[],
 'contraryEvidenceAndLimitations':[
  'Inherited R0019 resource fields remain stale and nonoperative for this batch. Full values are retained in VERIFICATION.custody.inheritedNonoperativeProjection: node, engine, binding, runtime/index/browser-executable hashes, expiry, output path, sourceConsumption, fixtureProducerNode/evidenceTarget, prior release fields and completedCases. Bind actual R0010 solely to source admission, dispatch, operative lease ID/holder/status/capacity/command/delegation and native receipt, not inherited descriptions. Canonical projection reconciliation is root-owned; no replay required.',
  'Saved actual reload snapshot precedes opening settings: CONFIG and persisted bytes are London 3/c, while the hidden unpopulated form still contains 2/f defaults. Source _openSettings populates the form. Subsequent visible-field receipt and independently inspected saved-reload crop show London 3/c. No claim that pre-open hidden defaults are rendered selected settings.',
  'Ten denotes the original selected case rows. Builder/consumer subcontexts and saved reload are within those rows; do not claim only ten calls to browser.newContext.',
  'Chromium 148.0.7778.96 on win32, viewport 1000x900, dpr 1. Original healthy zone assignments, fixed original epoch 1790942400000, synthetic provider responses and system font fallback are retained. Neither provider response timezone nor native metadata alone substitutes for actual UTC readbacks.',
  'No accessibility tree, speech, numerical temperature, real provider/weather, whole renderer, third-party host or cross-browser conclusion.',
  'Original accepted siblings and two Riyadh omission controls remain preserved. This actual batch does not replay them or substitute e718 historical runtime for delivered 88926dd. The source r1 REQUEST_CHANGES and 13 original OTHER whole-document failures remain separate.',
  'Two unsealed reviewer helper diagnostics retained: initial Python JSON ordering did not emulate JavaScript integer-key enumeration; next helper incorrectly required post-open values in the pre-open reload snapshot. Fixed by exact JSON.stringify ordering and the unchanged original temporal predicates. No author source, evidence, native attempts, correction allowance or acceptance threshold was changed.'
 ],
 'reviewerIndependence':{'separateFromExecutor':True,'executor':'/root/r0010_isolated_release_path_r1','sourceAuthoring':False,'nativeAcquisition':False,'writes':'Fresh nested reviewer evidence only','sharedSourceOrCanonicalOrGitHubEffects':False,'ordinaryEvidenceReview':True,'formalImplementAuditLifecycleClaim':False},
 'perOriginalCaseCorrectionReviewCycles':{c:1 for c in cases},'maximumCycles':2,'diagnosticsResetLimit':False,
 'independentActualAcceptance':'PASS','actualNative':'ACCEPTED_WITHIN_EXACT_A02_A05_SCOPE','finalClosureReview':'PENDING','nodeComplete':False,'canonicalJoinAuthorizedByThisReview':False,'publicEffectsAuthorizedByThisReview':False,
 'nextConsumer':'Assemble original A01-A06/O01-O14 with retained accepted siblings, exact delivered-source/public identity and this actual acceptance, then obtain final independent closure review. Root alone validates and performs separately authorized JOIN/publication/closure.'}
save('REPORT.json',report)
save('ACCEPTANCE.json',{'schema':'r0010-delivered-native-actual-acceptance/1','reviewer':report['reviewer'],'authorActualSealSha256':report['subjectSeal']['sha256'],'authorSourceSealSha256':report['authorSourceSeal']['sha256'],'sourceAdmissionSealSha256':report['independentSourceReviewSeal']['sha256'],'independentActualAcceptance':'PASS','actualNative':'ACCEPTED_WITHIN_EXACT_A02_A05_SCOPE','scope':cases,'deliveredHead':report['sourceHead'],'runtimeSha256':report['runtimeSha256'],'positivePASS':8,'selectedPreferenceOmissionsCAUGHT':2,'nativeReplays':0,'finalClosureReview':'PENDING','nodeComplete':False,'canonicalJoinOrPublicEffects':False})
files=[{'path':p.relative_to(W).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in sorted(W.rglob('*')) if p.is_file()]
save('MANIFEST.json',{'schema':'r0010-independent-actual-review-manifest/1','files':files})
save('SEAL.json',{'schema':'r0010-independent-actual-review-seal/1','manifestSha256':sha((W/'MANIFEST.json').read_bytes()),'reportSha256':sha((W/'REPORT.json').read_bytes()),'acceptanceSha256':sha((W/'ACCEPTANCE.json').read_bytes()),'authorActualSealSha256':report['subjectSeal']['sha256'],'decision':'PASS','independentActualAcceptance':'PASS','nodeComplete':False})
print(json.dumps({n:ref(W/n) for n in ['REPORT.json','ACCEPTANCE.json','MANIFEST.json','SEAL.json']}))
