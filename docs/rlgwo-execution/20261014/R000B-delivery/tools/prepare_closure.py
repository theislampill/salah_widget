"""Compose the complete delivered-work certificate from accepted, exact receipts.

Publication/readback and the intentional final close remain subsequent effects.
"""
from pathlib import Path
import copy, datetime, hashlib, json

E=Path(__file__).resolve().parents[1];D=E/'delivery';Q=E/'public-projection'
H='573dc2b15af37b5d32faa4364f3e653b65431dfc';B='16658749209e0c567f49a3fc9dc855f665afa6e4'
M='763a460e98dc23c7f0e95bf346274f1685b3c654';T='3656edba44b79ab7216c8cbf3546f4fe085bee9a'
V='885348adc26f9db468b39b65ba2c07cf130d26ca'
REPO='https://github.com/theislampill/salah_widget'
VP=REPO+'/blob/'+V+'/docs/rlgwo-execution/20261014/R000B/'
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def bind(p,name=None):return {'path':name or p.relative_to(E).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
def dump(p,v):p.write_bytes((json.dumps(v,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode())
assert not (E/'closure-certificate.json').exists(),'Preserve any prior certificate and inspect before revision.'
source=read(D/'source-docs-readback.json');consumer=read(D/'public-consumer/readback.json')
primary=read(D/'primary-public-consumer-review.json');independent=read(E/'independent-review/delivery/delivery-review.json')
assert source['status']=='PASS' and source['mergeCommit']==M and len(source['httpFiles'])==149
assert all(r['exact'] for r in source['httpFiles']) and source['runtimeFiles']==135
assert consumer['status']=='PASS_ASSERTIONS_PENDING_PIXEL_REVIEW'
assert primary['status']=='PASS_BOUNDED_PUBLIC_ENDPOINTS_WITH_RETAINED_LIMITATIONS'
assert independent['status'].startswith('PASS'),independent['status']
assert independent['decision']['deliveryEvidenceAccepted'] is True and independent['decision']['blockers']==[]
assert sha((E/'independent-review/delivery/delivery-review.json').read_bytes())=='d2d4ffa0c321ca8bdc11d6129e3f1ae76a38f1859e398f6816e41869ee1d19e9'
assert len(consumer['results'])==2
assert all(len(r['states'])==5 and all(r['sequenceChecks'].values()) for r in consumer['results'])
assert all(all(s['checks'].values()) for r in consumer['results'] for s in r['states'])
matrix=read(Q/'acceptance-matrix.json');candidate=read(Q/'reviewed-candidate-certificate.json')
stored={r['path'] for r in read(Q/'manifest.json')['files']}|{'manifest.json'}
archive={r['originalPath']:r for r in read(Q/'archive-map.json')['files']}
def public_evidence_path(original):
 path=original if original in stored else archive[original]['path']
 assert path in stored,path
 return VP+path
rows=copy.deepcopy(matrix['rows'])
for row in rows:
 row['qualificationEvidence']=[public_evidence_path(p) for p in row.pop('evidence')]
 if row['id']=='B18':
  row['qualificationStageStatus']=row['status']
  row['status']='JOINED_REVIEW_PUBLIC_HEAD_AUTHORITY_MERGE_AND_DELIVERY_ACCEPTED'
  row['currentLimitations']='This certificate is published before its independent public readback and the authorized intentional completed close. Those subsequent effects require their own actual receipts; no future issue state is asserted here.'
  row['deliveryEvidence']=['publication-review/public-head-review.json','publication-review/posted-public-review-readback.json',
   'delivery/owner-authorization.json','delivery/before-merge-gate.json','independent-review/delivery/merge-review.json',
   'required-delivery-receipt.json','independent-review/delivery/delivery-review.json']
limits=[
 'The original current/expired first-state Moon omissions remain the inherited terrain cold-acquisition limitation. These frames are not complete-Moon PASS and no universal startup deadline is claimed.',
 'Every retained Firefox native video keeps its blank/incomplete-frame failure. The independently qualified original PNG route supplies only its declared state, six-second recovery and thirty-second motion observations; later images never replace failed video frames.',
 'The genuine earlier warm missing-Moon transition and intermediate blue-flash/black-limb frames remain failed contrary evidence. Only the affected repaired candidate and its reviewed observations receive acceptance.',
 'The old ten-minute radar source/receipt expiry and ordinary-retry receipts are reused only for their unchanged relevant inputs/source/interfaces, not old Moon, sky or motion acceptance.',
 'The new actual-Pages consumer confirms ten default-motion endpoints only. It is not a new continuous watch, first-Moon qualification, live-provider test, universal radar-coverage claim, ground-observation promise or offline-app guarantee.',
 'Controlled fixture weather/prayer/Hijri inputs and advancing 2026-09-07 UTC clock are synthetic. Native scheduling/animation/retries remain real; no test helper forces acquisition or installs weather model state.',
 'Source/receipt age depends on client/provider clocks; skew can withhold authority. Weather remains a disclosed current model estimate, and radar coverage can be absent.',
 'No applicable CI checks or branch-protection rules were configured. Their absence is not CI PASS; the successful Pages deployment is a separate observed workflow.',
 'GitHub prematurely auto-closed issue11 after the merge. The assertion detected it, evidence was retained and the issue was reopened before delivery qualification. This mitigated lifecycle failure is not erased or counted as the final closure.'
]
delivery_review=bind(E/'independent-review/delivery/delivery-review.json')
required={'schema':'r000b-required-delivery-receipt/v1','status':'PASS_WITH_DECLARED_SCOPES_AND_RETAINED_LIMITATIONS',
 'approvedHead':H,'reviewedBase':B,'mergeCommit':M,'sourceTree':T,
 'mergeParents':[B,H],'mergeMethod':'merge commit','sourceScopeFiles':17,
 'pagesRun':source['pagesWorkflow']['html_url'],'pagesStatus':'completed/success',
 'pagesSource':{'branch':'main','path':'/'},'pagesConfigurationChanged':False,
 'servedRuntimeFiles':135,'allSelectedServedFiles':149,'bytesRead':source['totalBytesRead'],
 'runtimeSha256':source['runtimeTreeSha256'],'servedMismatchCount':0,
 'sourceAndDocuments':bind(D/'source-docs-readback.json'),
 'publicConsumer':bind(D/'public-consumer/readback.json'),
 'primaryPixelReview':bind(D/'primary-public-consumer-review.json'),
 'independentDeliveryReview':delivery_review,
 'engines':[{'engine':r['engine'],'version':r['version'],'executableSha256':r['executableSha256'],
  'states':[s['stage'] for s in r['states']],'sequenceChecks':r['sequenceChecks']} for r in consumer['results']],
 'qualificationEvidenceCommit':V,'qualificationBulkOnPages':False,
 'scope':'Authorized exact-source merge plus actual delivered source/docs and bounded public consumer endpoints. Original acceptance and contrary-evidence scopes remain unchanged.',
 'limits':limits}
dump(D/'required-delivery-receipt.json',required)
cert={'schema':'r000b-close-certificate/v1','marker':'CLOSE-R000B',
 'status':'QUALIFIED_AND_DELIVERED_FOR_COMPLETED_CLOSURE','canonicalId':'R000B',
 'title':'Expire weather and radar authority using source age as well as retrieval time',
 'certifiedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'issue':REPO+'/issues/11','pullRequest':REPO+'/pull/61',
 'specification':{'commit':'21e7a84365fae37a86cae5c7d5e41008c0adc53f','url':REPO+'/blob/21e7a84365fae37a86cae5c7d5e41008c0adc53f/docs/rlgwo-execution/20261008/REMAINING_RLGWOs/R000B.md'},
 'approvedHead':H,'reviewedBase':B,'reviewedSourceTree':T,'mergeCommit':M,'mergeParents':[B,H],
 'mergeUrl':REPO+'/commit/'+M,'runtimeSha256':source['runtimeTreeSha256'],'runtimeFiles':135,
 'exactHeadAuthority':bind(D/'owner-authorization.json'),
 'preMergeConditions':bind(D/'before-merge-gate.json'),
 'changedScope':{'fileCount':17,'authoredRuntimeOwners':2,'generatedConsumers':3,'existingDocs':3,'testsFixturesQa':7,'compactEvidenceIndexes':2,
  'candidateFileSha256':candidate['candidateFiles'],'additionalIndexes':['docs/rlgwo-execution/20261014/R000B/README.md','docs/rlgwo-execution/20261014/R000B/reference.json']},
 'runtimeImpact':candidate['runtimeImpact'],
 'temporalPolicy':{'weatherSourceAndReceiptLimitMs':900000,'radarFrameAndReceiptLimitMs':1200000,'boundaries':'inclusive','futureAllowanceMs':0,
  'weatherFields':'source-valid/current time, positive interval seconds, captured request timezone, source age and receipt time remain distinct',
  'radarFields':'raw numeric frame seconds, raw numeric index seconds, each valid finite derived Date epoch and receipt time remain distinct; missing frame time never borrows index time',
  'unavailable':'Expired/invalid authority clears current weather values and disables unsupported weather effects; retained cache bytes do not confer live authority.',
  'modelPolicy':'Preserve eligible current MODEL ESTIMATE conditions without a direct ground-observation requirement; optional unavailable precipitation does not alone suppress an otherwise valid current model condition.'},
 'qualification':{'originalRows':18,'sourceControls':{'B04_B13Passed':57,'retainedBaselineAdmissionFailures':4,'mutantsKilledByIntendedAssertions':4,'mutationSyntaxCrashesCountAsDetection':False},
  'affectedSkyControlsPassed':53,'affectedInheritedPassed':245,'affectedInheritedFailed':0,'unchangedInheritedTodo':4,
  'native':'Original serial Chromium/Firefox default, reduced preference and motion=full cases; native1x source boundary, controlled503 and ordinary recovery; original clips/PNG alternative reviewed within declared scopes.',
  'priorAcceptedRowsPreserved':['B01','B02','B03','B05','B06','B07','B08','B09','B10','B11','B12','B15'],
  'originalMatrixUrl':VP+'acceptance-matrix.json','rows':rows},
 'immutableQualificationEvidence':{'commit':V,'manifestUrl':VP+'manifest.json','manifestSha256':'54d4272917e4e68fe42bc2e07ee2b3dee49552cbba6e559413e9d7ff6d593bc5',
  'storedFiles':619,'storedBytes':1307142979,'logicalOriginals':8810,'nativeAcquisitions':21,'originalWebms':21,'originalImages':8435,'losslessArchives':34,
  'branch':'codex/r000b-evidence-20261014','nonDeploying':True,'mergedIntoMain':False,
  'contraryEvidenceUrl':VP+'contrary-evidence.json','independentJoinedReviewUrl':VP+'independent-review/final-joined-review.json'},
 'publicHeadReview':{'url':REPO+'/pull/61#issuecomment-6177218895','sha256':'aedec4cb0f977798c88d035cd815b28a7b68ba37db3b8bd8e33a8952a51bcdb3',
  'publicFilesRead':636,'description':'Independent exact public PR head/base/tree and all619 evidence/17source raw artifact readback; no mismatch.'},
 'independentReviewer':{'agent':'/root/r000b_independent_review','model':'GPT-6 Astra','reasoning':'Max','readOnly':True},
 'independentDeliveryReview':delivery_review,
 'delivery':required,
 'deliveryEvidenceLocation':'This certificate and its relative delivery/review paths are in one immutable appended evidence commit. Its full commit URL and manifest hash are supplied in the issue certificate publication; the commit cannot contain its own hash.',
 'deliveryReceipt':bind(D/'required-delivery-receipt.json','required-delivery-receipt.json'),
 'retainedLifecycleFinding':{'id':'R000B-MERGE-LIFECYCLE-01','severity':'P2','status':'MITIGATED_OPEN_STATE_RESTORED_HISTORY_RETAINED',
  'prematureClosedEvent':33265433588,'reopenedEvent':33265528618,'review':'independent-review/delivery/merge-review.json',
  'causalLimit':'GitHub closing relation and timing observed; close event commit_id was null, so the exact keyword/UI creation mechanism is not asserted.'},
 'limitations':limits,'rollback':candidate['rollback'],
 'publicationAndClosureOrder':{'certificatePublicReadback':'Must occur after publishing this exact certificate; no future readback is asserted here.',
  'intentionalCompletedClose':'Owner authorized after independent certificate readback.',
  'finalClosedStateVerification':'Independent live readback must confirm CLOSED/completed and certificate/evidence links after the close.'},
 'primaryReconciliation':'The exact authorized delivered source preserves accepted B01-B03/B05-B12/B15. The remaining source, mutation, bounded native, documentation, independent public-head and delivery obligations are accepted only in the scopes stated here. No failed original or pending effect is promoted to PASS.'}
dump(E/'closure-certificate.json',cert)
print(json.dumps({'certificate':bind(E/'closure-certificate.json'),'requiredDelivery':bind(D/'required-delivery-receipt.json'),'originalRows':len(rows)}))
