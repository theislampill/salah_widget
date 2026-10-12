"""Actual independent reviewer decision and private seal, after manual source/diff review."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(__file__).resolve().parent
RUN=OUT.parent.parent
REV=Path('C:/Users/theis/.codex/worktrees/pr43-review-revision/salah_widget')
REVIEWER='/root/diagnostic_release_exit'
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def ref(p):
    p=Path(p);b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def write(n,o):
    p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),p
    b=o if isinstance(o,bytes) else (json.dumps(o,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
    p.write_bytes(b);return ref(p)

node=load(OUT/'ORIGINAL_NODE.json')
freeze=load(OUT/'FINAL_SOURCE_FREEZE.json')
selection=load(OUT/'SELECTED_DIFF.json')
required=load(OUT/'REQUIRED_ASSERTIONS.json')
reuse=load(OUT/'REUSE_READBACK.json')
public=load(OUT/'PUBLIC_SCOPE_READBACK.json')
metadata=load(OUT/'inputs/R001C.metadata.json')
native=(OUT/'inputs/final/src/native/index.html').read_text(encoding='utf-8').splitlines(keepends=True)
additional=[]
for ident,a,b in [('calendar-earthshine-source',1880,1885),('shared-initial-paint-permission',2693,2740),
                  ('calendar-body-opaque-source',2768,2772),('body-occ-light-separation',2910,2914),('glow-independent-of-body',3025,3031)]:
    s=''.join(native[a-1:b])
    additional.append({'id':ident,'file':'src/native/index.html','startLine':a,'endLine':b,'text':s,'sha256':hashlib.sha256(s.encode()).hexdigest(),
                       'claimCeiling':'Source architecture only; no new pixels or V5 surface qualification.'})
write('ADDITIONAL_SOURCE_BINDINGS.json',{'native':ref(REV/'src/native/index.html'),'regions':additional})

claims=[
 {'id':'C01','assertion':'Diagnostics use the fragment q; positive & flags append inside it.','sourceRegions':['parser','flags-and-reduced-motion'],
  'retainedProof':'R001C-A01/A05 and 37 PASS + 1 REUSED; original actual parser receipt remains at its own source/base.'},
 {'id':'C02','assertion':'The complete query-only example is an explicitly labelled negative; both motion flags are absent from its fragment.','sourceRegions':['parser','flags-and-reduced-motion'],
  'retainedProof':'Actual query-negative parser control and accepted e718 browser query-negative case, not current-runtime requalification.'},
 {'id':'C03','assertion':'The complete real-time recipe has no simTime/timeScale. Full-motion sets the exact full opt-in and the default respects native reduced motion.','sourceRegions':['parser','flags-and-reduced-motion','time-scale','full-class-and-loop'],
  'retainedProof':'Accepted default/reduced/full browser cases use genuine BrowserContext media; historical Chromium148 and exact e718 environment stay explicit.'},
 {'id':'C04','assertion':'The noon recipe requests simTime=12:30 and halo. It diagnoses solar force activation and is not a live-motion recipe.','sourceRegions':['parser','time-scale','physical-and-force-block'],
  'retainedProof':'Required literal and actual halo branch/source VM; no fresh solar pixels.'},
 {'id':'C05','assertion':'Exactly halo, sundogs, pillar, anticrep, paraselene and lunarhalo have dedicated force branches. The DESIGN enum and amended forceability sentence name exactly these six.','sourceRegions':['flags-and-reduced-motion','physical-and-force-block'],
  'retainedProof':'Actual six force rows, unsupported-string/corona and enum controls. Lunar flags retain permission; six names are not proof of six correct optical images.'},
 {'id':'C06','assertion':'Corona, Earthshine, refraction and crepuscular ray are physical-input cases with no dedicated debugOptic force branch.','sourceRegions':['physical-and-force-block','calendar-earthshine-source'],
  'retainedProof':'Branch enumeration excludes all four; raw unsupported corona control retains zero force outputs. Physical corona and ray expressions are separate from the force block.'},
 {'id':'C07','assertion':'A simTime anchor without timeScale sets TIMESCALE=0. The required real-time recipe is retained for a 15–60 second watch.','sourceRegions':['time-scale','full-class-and-loop'],
  'retainedProof':'Current actual source scale selection; diagnostic docs explicitly distinguish frozen scene from live watch.'},
 {'id':'C08','assertion':'Activation does not establish visible motion or correct optical pixels. Crops, physical conditions and real watch remain required; cloud hash is not motion proof.','sourceRegions':['overlay-and-loop'],
  'retainedProof':'Exact required caveat and inherited 28-07. Neither counters nor local Markdown legibility are promoted to M0 or physical optics.'},
 {'id':'C09','assertion':'Current nativeLunarPresentation computes moonLightEligible from phase, lunar-altitude, solar-darkness and surfaceFailed. Its named noneligible reasons withdraw atmospheric light, and lunar force branches consume that permission.','sourceRegions':['lunar-permission','physical-and-force-block','shared-initial-paint-permission'],
  'retainedProof':'Actual current helper/force source; retained frac .01/.02, alt -10, sun alt20, _pbrFailed:true controls. The prose refers to named helper reasons and does not invent a new numerical boundary or prove V5 surface readiness.'},
 {'id':'C10','assertion':'Calendar-body Earthshine and stellar cutout are separate from atmospheric moonlight permission. This source gate does not establish current V5 surface availability or optical pixels.','sourceRegions':['calendar-earthshine-source','calendar-body-opaque-source','body-occ-light-separation','glow-independent-of-body'],
  'retainedProof':'Current source separately constructs body/occ, moonlight and local glow. This is architecture/fact review only, not new opacity/Earthshine pixel qualification.'},
 {'id':'C11','assertion':'All required diagnostic text, copied complete URLs and DESIGN enum have exact final-source and scoped local rendering/copy proof.','sourceRegions':[],
  'retainedProof':'Canonical completed R001C-RENDER result and root join; final adopted manifest, actual paragraph capture/admission/pixel review and independent exact final-byte adoption. No whole-document or final full-raster equivalence.'},
 {'id':'C12','assertion':'Remaining & diagnostic references retain their fragment-append meaning and existing physical/watch/layout constraints. Mixed lines grant no review of peer-owned cloud/weather/clock text.','sourceRegions':['parser','flags-and-reduced-motion','physical-and-force-block'],
  'retainedProof':'Every selected changed line/subclause mapped below. Unchanged accepted siblings and peer source reviews are retained; no broad documentation or renderer verdict.'},
 {'id':'C13','assertion':'The issue stays OPEN. Existing immutable public facts/base docs are reachable; the dirty candidate is not claimed publicly delivered or qualified.','sourceRegions':[],
  'retainedProof':'Fresh eight read-only public reads: #28, PR43, immutable original assessment/contract/native, and committed-base AGENTS/DESIGN/OPTICS equal local Git base bytes.'},
]
for c in claims:c['disposition']='PASS_IN_LITERAL_DOCS_ONLY_SCOPE'

def claim_ids(x):
    l=x['text'];out=['C11','C12']
    if l.startswith('Configuration and diagnostics'):out+=['C01','C02','C05','C06']
    elif 'nativeLunarPresentation' in l:out+=['C09','C10','C08']
    elif l.startswith('Lunar force checks'):out+=['C09','C08']
    elif l.startswith('simTime without'):out+=['C07','C08']
    elif l.startswith('index.html?') or l.startswith('Query-only negative'):out+=['C02']
    elif 'simTime=12:30' in l or l.startswith('Solar noon'):out+=['C04']
    elif l.startswith('Real-time motion'):out+=['C03']
    elif 'debugOptic' in l or 'six supported forces' in l or 'Dedicated diagnostic forcing' in l:out+=['C05','C09']
    if 'motion=full' in l or l.startswith('Full-motion override'):out+=['C03']
    if 'debugMotion' in l:out+=['C01','C08']
    return list(dict.fromkeys(out))

line_verdicts=[]
for i,x in enumerate(selection['selectedChangedLines'],1):
    live=(REV/x['file']).read_text(encoding='utf-8').splitlines()[x['line']-1]
    assert live==x['text'] and hashlib.sha256(live.encode()).hexdigest()==x['sha256']
    line_verdicts.append({'id':f'R001C-L{i:02}',**x,'claimIds':claim_ids(x),'disposition':'PASS_DIAGNOSTIC_CLAUSE_ONLY',
                          'reviewer':REVIEWER,'reviewScope':x['ownerScope']})
assert len(line_verdicts)==55
assert any(x['file']=='DESIGN.md' and x['line']==617 and 'C05' in x['claimIds'] for x in line_verdicts)
write('CLAIM_REVIEW.json',{'schema':'independent-r001c-line-fact-review/1','reviewer':REVIEWER,'atUtc':now(),
                          'claims':claims,'lineByLineVerdicts':line_verdicts,'requiredLiteralAssertions':required['literalAssertions'],
                          'base':load(OUT/'GIT_IDENTITY.json'),'selection':ref(OUT/'SELECTED_DIFF.json'),
                          'wholeDocsApproved':False,'freshRuntimeOrPixelClaims':False})

old_review=load(RUN/'workers/diagnostic_a10_final_consumer_r1/INDEPENDENT_REUSE_REVIEW.json')
exact_review=load(RUN/'workers/diagnostic_a10_final_consumer_r1/EXACT_FINAL_BYTE_ADOPTION_DECISION.json')
paragraph=load(RUN/'workers/diagnostic_a10_final_consumer_r1/INDEPENDENT_PARAGRAPH_PIXEL_REVIEW.json')
write('ADVERSE_AND_BOUNDARY_REVIEW.json',{
 'retainedSourceVm':'37 PASS + 1 REUSED; no fresh runner/VM execution.',
 'retainedHelper':load(OUT/'ACCEPTED_VM_READBACK.json')['helper'],
 'retainedNativeFailure':{'report':ref(RUN/'workers/diagnostic_actual_review_r1/REPORT.json'),
    'decision':'Actual earlier native FAIL remains; no PNG/M0 from that failure. Later accepted diagnostic four-case scope does not relabel it.'},
 'retainedDesignFailure':'Whole-page SEMANTIC_FAIL/repeated raster and earlier failed force/context attempts remain immutable. The scoped admitted required sections do not close whole pages.',
 'regionalConsumerNegatives':old_review['independentAdverseControls'],
 'exactByteAdoptionNegatives':exact_review['adverseReadbackControls'],
 'actualParagraphNegatives':paragraph['adverseControls'],
 'originalAcceptedRows':[{'id':x['id'],'status':x['status'],'parentText':x['parentText']} for x in metadata['acceptedObligations']],
 'originalRemainingParentRows':[{'id':x['id'],'parentText':x['parentText'],'closureGate':x.get('closureGate'),'disposition':'RETAINED_SEPARATE_PARENT_QUALIFY_DELIVERY_CLOSE_GATE_NO_ISSUE_CREDIT'} for x in metadata['remainingObligations']],
 'sourceVsGenerated':'Current native cbd5/current generated c773 are separately fixed identities. No automatic e718/current07 or historical ec59/51c09 whole-runtime equivalence.',
 'currentPlatformAndM0':'Not rerun or qualified in this review.',
 'publicCandidate':'Not delivered; A11/downstream public readback remains pending.',
 'nativeQualification':'Incomplete separate QUALIFY/CLOSE obligations remain explicit.'})

git=['C:/Program Files/Git/cmd/git.exe','-C',str(REV)]
final_head=subprocess.run(git+['rev-parse','HEAD'],capture_output=True,timeout=15,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
assert final_head.returncode==0 and final_head.stdout.decode().strip()==freeze['identity']['baseHead']
final_diff=subprocess.run(git+['diff','--no-ext-diff','--no-color','--binary','HEAD','--','AGENTS.md','DESIGN.md','OPTICS.md'],capture_output=True,timeout=15,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
assert final_diff.returncode==0 and final_diff.stdout==(OUT/'documentation.diff').read_bytes()
final_files=[]
for f in freeze['files']:
    current=ref(f['path']);assert current['sha256']==f['sha256'] and current['bytes']==f['bytes'];final_files.append(current)
for x in reuse['exactReferencesVerified']:
    current=ref(x['path']);assert current==x,(current,x)
write('FINAL_READBACK.json',{'schema':'r001c-release-review-final-readback/1','atUtc':now(),'head':final_head.stdout.decode().strip(),
                           'headExitCode':final_head.returncode,'documentationDiffExitCode':final_diff.returncode,
                           'documentationDiffUnchanged':True,'sourceFiles':final_files,'applicableReferencesUnchanged':len(reuse['exactReferencesVerified']),
                           'all55FinalChangedLinesStillExact':True,'sourceSharedMutation':False})

issue=next(x for x in public['readbacks'] if x['kind']=='issue-28')
independence={'rootAuthorIntegrator':'/root','reviewerIsAuthorOrIntegrator':False,
 'identity':REVIEWER,'statement':'I did not author or integrate the source, docs, fixture, render consumer, row map, prior reviews or root controller. This fresh task read existing evidence and authored only this new private review directory.',
 'delegatedChildren':0,'sharedWrites':0,'newBrowserNativeBuildVmExecutions':0,
 'workflow':'Ordinary explicitly dispatched RLGWO independent review. No internal audit-assess governor-envelope or lifecycle authority is claimed.'}
evidence={key:ref(OUT/path) for key,path in {
 'acquisition':'ACQUISITION.json','identity':'GIT_IDENTITY.json','frozenSource':'FINAL_SOURCE_FREEZE.json',
 'selectedDiff':'SELECTED_DIFF.json','exactContextualThreeDocDiff':'documentation.diff','lineFacts':'CLAIM_REVIEW.json',
 'sourceRegions':'SOURCE_FACT_BINDINGS.json','additionalSourceRegions':'ADDITIONAL_SOURCE_BINDINGS.json',
 'requiredAssertions':'REQUIRED_ASSERTIONS.json','acceptedVmReadback':'ACCEPTED_VM_READBACK.json',
 'acceptedProofReuse':'REUSE_READBACK.json','adverseBoundaries':'ADVERSE_AND_BOUNDARY_REVIEW.json',
 'publicScope':'PUBLIC_SCOPE_READBACK.json','finalReadback':'FINAL_READBACK.json','originalNode':'ORIGINAL_NODE.json'}.items()}
decision={'schema':'independent-docs-only-release-review/1','atUtc':now(),'node':node['id'],'priority':node['priority'],
 'issue':28,'interface':'r001c-reviewed-release/v1','decision':'PASS_EXACT_DIAGNOSTIC_DOCS_ONLY_OWN_EXIT',
 'nodeExitSatisfied':True,'recommendExecutionStatus':'COMPLETE_EXIT_VERIFIED','canonicalStateChangedByReviewer':False,
 'reviewer':REVIEWER,'reviewerIndependence':independence,'literalScope':node['scope'],
 'literalEntryCriteria':node['entryCriteria'],'literalExitCriteria':node['exitCriteria'],'literalTests':node['tests'],
 'literalInputs':node['inputs'],'literalOutputs':node['outputs'],
 'entryCriteriaDisposition':[{'criterion':c,'disposition':'SATISFIED','evidence':[evidence['frozenSource'],evidence['sourceRegions'],evidence['lineFacts']]} for c in node['entryCriteria']],
 'exitCriteriaDisposition':[{'criterion':c,'disposition':'SATISFIED','evidence':[evidence['lineFacts'],evidence['adverseBoundaries'],evidence['publicScope'],evidence['finalReadback']]} for c in node['exitCriteria']],
 'inputDisposition':[{'id':i['id'],'contract':i['contract'],'disposition':'SATISFIED_EXACT_FINAL_DIAGNOSTIC_OWNER_FACTS_AND_APPLICABLE_RETAINED_PROOF'} for i in node['inputs']],
 'entryDecision':{'fixedExactDocsCandidate':True,'candidateIdentity':freeze['identity'],'sourceFactsFixed':evidence['sourceRegions'],
  'fixedDirtyDocsDiff':evidence['exactContextualThreeDocDiff'],'diagnosticOwnerDiff':evidence['selectedDiff'],'unsupportedPlatformOrRuntimeClaims':False,
  'reason':'Exact dirty documentation bytes/diff on a verified public base head satisfy the literal docs-only head/diff output. No new final commit, full native exit, M0 or public delivery is a predecessor for this own exit.'},
 'exitDecision':{'everyChangedDiagnosticClaimAccurateAndIndependentlyReviewed':True,'changedDiagnosticLinesOrClauses':55,
  'claimIds':[c['id'] for c in claims],'literalAssertions':19,'incompleteNativeAndEvidenceExplicit':True,'issueState':'OPEN','issueStateProof':issue,
  'retainedAcceptedRows':['28-07','28-08','28-11'],'narrowSupersededRow':'28-10 outer-wrapper amendment only',
  'noReauditOfAcceptedSiblingExits':True},
 'testsDecision':{'sourceAndRawOutputsRead':True,'currentRelevantOldExcerptsMatchExactlyOnce':3,'applicableExactReferencesVerified':60,
  'acceptedPacketMembersVerified':15,'retainedSourceVm':'37 PASS + 1 REUSED; 16 helper contexts, held-out -0.2 differs',
  'requiredPixelsApplicability':'Canonical completed R001C-RENDER scoped text/copy and final exact-byte adoption reused through fixed final source/layout-input and actual added-paragraph consumer. No new current-runtime/M0/optical/whole-page pixels.',
  'publicEvidenceReachability':{'decision':'PASS_APPLICABLE_READ_ONLY_PUBLIC_SCOPE','receipt':evidence['publicScope'],'reads':8,'newDiagnosticProsePublicLinks':0,'dirtyCandidatePublished':False},
  'finalSourceHashesAndDirtyDiffUnchanged':True,'nativeRerun':False,'newTests':False,'broaderResearch':False},
 'evidenceBindings':evidence,
 'remainingRequirements':{'thisReleaseReviewNode':[],
  'parentNativeQualification':'INCOMPLETE: preserve historical failures and separate current-runtime/native/M0/physical evidence, QUALIFY/CLOSE.',
  'delivery':'PENDING: separately authorized exact-head/effects scope and actual documentation delivery/readback.',
  'closure':'PENDING: all original mandatory obligations, A11 public/delivered proof and separately authorized closure; #28 remains OPEN.',
  'affectedDrift':'Later changes to reviewed diagnostic clauses/source regions/diff require only affected reassociation.'},
 'wholeDocumentPASS':False,'wholeREADMEPASS':False,'wholePRPASS':False,'nativeQualified':False,'mergeAuthorityGranted':False,
 'delivered':False,'issueClosureAuthorized':False,'parentClosureCredit':0,'nodeCredit':0,
 'nextAction':'Root independently resolves this exact sealed PASS packet, joins only execution/R001C/release-review.json and reconciles the named own release-review exit. Preserve all separate delivery/QUALIFY/CLOSE and issue gates.'}
write('execution/R001C/release-review.json',decision)
write('REPORT.json',{'schema':'r001c-independent-release-exit-return/1','reviewer':REVIEWER,'atUtc':now(),
 'decision':decision['decision'],'node':node['id'],'nodeExitSatisfied':True,'releaseReview':ref(OUT/'execution/R001C/release-review.json'),
 'reviewerIndependence':independence,'checks':{'requiredLiterals':19,'changedDiagnosticClauses':55,'exactReusedReferences':60,'reusedPacketMembers':15,'publicReads':8},
 'canonicalStateMutation':False,'nativeQualified':False,'wholeDocumentPASS':False,'delivered':False,'issueClosed':False,'rootReconciliationPending':True,
 'noRemainingOwnExitRequirements':True,'nextAction':decision['nextAction']})
write('REPORT.md',('PASS: R001C-RELEASE-REVIEW exact diagnostic docs-only own exit.\n\n'
 'Reviewer: '+REVIEWER+'. Current base/head 50e46b7ecfde9c8bea9c0cf00b6017afaf27aab9; exact dirty AGENTS/DESIGN/OPTICS source and diff frozen. 55 changed diagnostic clauses, 19 literal assertions, 60 exact applicable references and 15 final A10 packet members verified; eight public readbacks. #28 is OPEN.\n\n'
 'Historical native FAIL, DESIGN SEMANTIC_FAIL/repeated raster and force/context failures remain; 37 PASS + 1 REUSED and 16 helper contexts stay bounded, with fraction -0.2 divergent. No automatic e718/current07 equivalence. Accepted required local copy/pixel evidence is reused through the final adopted source/layout-input and actual paragraph consumer proof. No native/M0/whole-document/public/delivery/issue closure credit. Root alone reconciles the canonical node.\n').encode('utf-8'))

members={str(p.relative_to(OUT)).replace('\\','/'):ref(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ('MANIFEST.json','SEAL.json')}
manifest=write('MANIFEST.json',{'schema':'r001c-release-exit-private-manifest/1','files':members})
seal=write('SEAL.json',{'schema':'r001c-release-exit-private-seal/1','atUtc':now(),'reviewer':REVIEWER,
 'manifestSha256':manifest['sha256'],'reportSha256':ref(OUT/'REPORT.json')['sha256'],
 'releaseReviewSha256':ref(OUT/'execution/R001C/release-review.json')['sha256'],'nodeExitSatisfied':True,
 'rootReconciliationPending':True,'nodeCredit':0,'privateWritesOnly':True,'immutableAfterSeal':True,
 'wholeDocumentPASS':False,'nativeQualified':False,'M0OrCurrentRuntimeCredit':False,'delivered':False,'issueClosed':False})
print(json.dumps({'seal':seal,'manifest':manifest,'releaseReview':ref(OUT/'execution/R001C/release-review.json'),
                  'privatePayloadFiles':len(members),'nodeExitSatisfied':True,'rootReconciliationPending':True}))
