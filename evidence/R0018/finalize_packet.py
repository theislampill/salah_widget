"""Bind already-completed R0018 evidence to the committed source, without reruns."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess

OUT=Path(__file__).resolve().parent
ROOT=Path(r'C:\Users\theis\.codex\worktrees\r0018-readability\salah_widget')
HEAD='859bdf245ee5e9777a4bb7dd074a9eb3616c6a71'
BASE='ed5e7afbd2fcf7a59050817e2a561bcdbfa9043d'
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(rel,value):
    p=OUT/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def copy_verified(source,destination,expected=None):
    data=source.read_bytes()
    if expected:assert sha(data)==expected,source
    dst=OUT/destination;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
    return {'path':destination,'bytes':len(data),'sha256':sha(data)}

assert git('rev-parse','HEAD').decode().strip()==HEAD
assert git('rev-parse','HEAD^').decode().strip()==BASE
assert not git('status','--porcelain')
files=read(OUT/'candidate-files.json')
for row in files['files']:assert sha(git('show',HEAD+':'+row['path']))==row['sha256']
write('candidate-identity.json',{'schema':'r0018-default-css/v1','head':HEAD,'base':BASE,'tree':git('rev-parse','HEAD^{tree}').decode().strip(),'files':files['files'],'runtimeSha256':files['runtimeSha256'],'rootSha256':'917a3c26176c4326319fcdc01ad814500569106ce016d02667336e486b472761','authoredOwner':'src/native/index.html','builder':'tools/build_native.py','sourceDiff':'production.patch','build':'final-build-identity.json'})
(OUT/'production.patch').write_bytes(git('diff',BASE,HEAD,'--'))

q=read(OUT/'qualification-index.json')
assert q['complete'] and len(q['cases'])==38 and len(q['mutants'])==6
write('reviews/geometry-and-continuity.json',{'recording':'Executor transcription of actual independent returns; original reviewer messages are the primary return. No fabricated native signature or lifecycle receipt.','reviewer':'/root/r0018_independent_review','requestedModel':'gpt-6-astra','requestedReasoning':'max','effectiveBackend':'not independently exposed','geometry':{'verdict':'PASS_SCOPED','resultSha256':'3dbfb70367978287e2d58a28df651d822e111c8cd1a20544877fb17098eb4ba8','driverSha256':'503bc293263c304def159b4b6521dc3d8f039dea677d177a8ff39c66d4e99668','observations':['All five exact-rule reversal phases preserve geometry, typography, strings, fit key and inline focus style; 48 control checks pass.','Reviewer viewed all five images. Candidate phases are byte-identical, baseline phases are byte-identical; differences confined to prayer cells (7,286)-(318,494).','Keep all nine cross-load .cn.y differences and 29 exact comparisons; precise original boot cause remains unestablished. No tolerance or .cn exclusion.'],'acceptance':'Executor accepts this bounded CSS-no-movement result for A05, subject to final whole-candidate independent review.'},'continuation':{'observedAtUtc':'2026-10-15T10:00:12Z','loadedSkillSha256':'f1b614a213b652e7159e7e91c924987f10cb8e57519b10a3e9c9420720f1bdd4','findings':'Same base, nine files, 38 GREEN, six expected FAIL mutants, 78 source controls; summaries were stale/incomplete, no replay needed.','executorAcceptance':'Accepted bounded findings for evidence sealing and exact-head review frontier.','limits':'Same reviewer per owner limit. No fresh-context/native lifecycle/currentness-epoch/pending-consumer qualification or effect authority.'}})
write('contrary/reconciliation.json',{'scope':'Retained observations and proportional mechanical countermeasures; no original failure relabelled as PASS.','items':[
 {'case':'Original paired-raster collector failures','evidence':['andon-pair-01.json','collector-correction.json','collector-custody.json','reviews/collector-review.json'],'disposition':'Original failures retained; separately reviewed two independent text/background pairs and strict scene/style/geometry/renderer/runtime predicates qualify subsequent controls. Raster variation mechanism unestablished.'},
 {'case':'Cross-document Firefox geometry','evidence':['qualification-index.json','geometry-firefox-noon-desktop-dpr1/results.json','reviews/geometry-and-continuity.json'],'originalCheck':'assert geometry(baseline)==geometry(candidate)','observed':'Nine .cn.y differences only; 29 exact recorded geometry comparisons. Original strict comparison failed at Firefox noon desktop DPR1 compact.','disposition':'Exact old/new rule reversal in the same settled native page shows no geometry movement. Original cross-load cause remains unestablished; no tolerance/excluded field.'},
 {'case':'Early RED schema lacks row.boxStyle','observed':'A summary extension raised KeyError before writing an index. Original RED row/text rectangles and font/style/background/opacity records remain; row boxStyle was added for GREEN.','disposition':'Index explicitly marks absent RED fields, compares recorded pairs where available, and maps row padding/gap/border/radius preservation to exact source guards plus the native original-rule reversal. No invented baseline values.'},
 {'case':'Canonical builder invoked with -I','evidence':['build-import-andon.json','build-r2.log','final-build-identity.json'],'disposition':'Initial sibling-import failure occurred before writes; use the canonical non-isolated builder invocation.'},
 {'case':'Old appearance mutation seam','evidence':['source-tests/r0018-appearance-mutations.cjs.stderr','source-tests/r0018-appearance-mutations-r2.json'],'disposition':'Historical test demanded default contrast below 4.5; replace that inverted predicate and stale seam with the original default >=4.5 loss control. Six controls pass.'},
 {'case':'Optional V1 Pages preflight','evidence':['final-v1.json','baseline-v1-pages.json','v1-pages-preflight-reconciliation.json','v1-current-public-readback.json'],'disposition':'Same pre-existing rejection of any Jekyll config at exact base and candidate. Keep FAIL; frozen payload check and actual current public V1 bytes pass. No checker/config/product changes.'}
 ],'causalDiscipline':'Mechanical import/schema/seam faults use the cheap path. Geometry/raster causal deepening stops at supported settled-page and source controls; no unsupported boot/raster cause or broader campaign.','hansei':'Bind collector schema and original required predicate explicitly, retain raw failures, and use actual consumer controls before asserting a cause.','kaizen':'Executed collector/import bytes are retained; paired scenes/renderer validity/runtime identity gate every result; summary lists absent fields and exact differences rather than converting them to a false green.'})

previous=Path(r'C:\Users\theis\.codex\worktrees\r000d-close\salah_widget\evidence\R000D')
reuse=[]
for rel in ['qualification/runtime-identity.json','qualification/currentness.json']:
    source=previous/rel;data=source.read_bytes()
    assert git('show','8a102dfbed5559c266bf108003c617d0f4350c72:evidence/R000D/'+rel)==data
    reuse.append(copy_verified(source,'reuse/R000D/'+Path(rel).name))
assert read(previous/'qualification/runtime-identity.json')==read(OUT/'baseline-runtime.json')
write('reuse/identity.json',{'sourceEvidenceCommit':'8a102dfbed5559c266bf108003c617d0f4350c72','productionBase':BASE,'receipts':reuse,'exactRuntimeBeforeRepair':'5ff3fdf5a13cd3a798addfef972ed9a2c865f87cce531a23847015dcdc8a7d46','candidateUnchangedRuntimeFiles':133,'changedRuntimePaths':['index.html','offline.html'],'scriptBodiesExact':'source-build-currentness.json records authored/root/offline script equality','reuseScope':'Accepted scientific/weather/Moon/motion interfaces only, by exact source/runtime identity. Fresh timetable native pixels qualify the changed local composition. No new whole-CP9, lunar, real-time motion, extension-parent or continuous-video claim.'})

old=Path(r'C:\Users\theis\Documents\Codex\salah-rlgwo-execution-20261009\workers\persistent-R0018-20261013\font-target-r1')
historical=old/'asset-owner-boundary-c1/native-once-r2/chromium-desktop-dpr2-stale-green/result.json'
receipt=copy_verified(historical,'contrary/historical-transport/result.json','53bb8f894f5da1fb1a169a0072950609f936a8e5026c49d37000800fffd42b44')
review=Path(r'C:\Users\theis\Documents\Codex\salah-rlgwo-execution-20261009\workers\persistent-R0019-20261013\r0018-c1-r2-actual-review-r1\REPORT.json')
rr=copy_verified(review,'contrary/historical-transport/review.json','b6b1833a85464e822c32d1a8f6f853b5ad54e0d3c45c99ca5b81f3903341b916')
write('contrary/historical-transport/retention.json',{'result':receipt,'review':rr,'originalStatus':'27/28 strict FAIL; no-network-failures on colour.bin.gz net::ERR_ABORTED','disposition':'Retained historical diagnostic, zero original/case/closure credit. Exact consumer success did not absolve earlier failures. Transport mechanism remains UNESTABLISHED. Earlier DEM failure and full historical campaign stay in original custody; neither replayed nor promoted.','currentQualification':'All new 2026-10-15 matrix receipts retain native transport events and reject invalid runtime/renderer/consumer states; no network failures were recorded in these new cases.'})

outputs={'r0018-red/v1':{'status':'SOURCE_BOUND_RED_RETAINED','artifacts':['baseline-runtime.json','red-chromium-noon-desktop-dpr1/results.json','red-firefox-noon-desktop-dpr1/results.json','red-chromium-white-desktop-dpr1/results.json','red-firefox-white-constrained-dpr2/results.json','qualification-index.json']},'r0018-default-css/v1':{'status':'IMPLEMENTED_AND_BUILT','artifacts':['candidate-identity.json','production.patch','final-build-identity.json']},'r0018-native-readability/v1':{'status':'QUALIFIED_PENDING_FINAL_INDEPENDENT_REVIEW','artifacts':['qualification-index.json','collector-custody.json','visible-pixel-groups.json','contrary/reconciliation.json']},'r0018-docs/v1':{'status':'UPDATED_PENDING_FINAL_INDEPENDENT_REVIEW','artifacts':['docs/compatibility.json']},'r0018-delivery/v1':{'status':'PENDING_OWNER_EXACT_HEAD_BASE_APPROVAL_THEN_DELIVERY','artifacts':['delivery.json']}}
write('outputs.json',{'outputs':outputs,'acceptance':{'R0018-A01':'38 native case styles/ancestor opacity; all 12 texts opacity 1','R0018-A02':'Native minimum intended contrast 4.8591556626432935; threshold 4.5 unchanged; independent pixels required','R0018-A03':'Fresh source-bound frozen noon RED before CSS, matched GREEN and two hidden-background pairs','R0018-A04':'Six scenes, white stress, optional contrast, both engines; six reached semantic loss controls','R0018-A05':'29 exact geometry comparisons plus nine retained .cn.y differences and exact-rule same-page control; 133 runtime files/script bodies unchanged','R0018-A06':'DESIGN policy and 19 exact interface files; V1/public preflight limitation retained','R0018-A07':'Final immutable-head review and owner approval/public delivery/certificate-first closure pending'},'acceptedOriginalRow':'18-01 retained; original accepted audit stays authoritative within its scope.'})
write('delivery.json',{'schema':'r0018-delivery/v1','status':'PENDING','candidateHead':HEAD,'base':BASE,'remaining':['Independent exact-head/base review','Owner approval of these exact merge refs','Authorized merge/deployment and public native/source readback','Independent CLOSE-R0018 reconciliation','Certificate comment while issue OPEN','Verified intentional CLOSED/completed readback'],'issueClosed':False})
execution=read(OUT/'execution.json')
write('execution-pre-seal-history.json',execution)
execution.update(frontier='38 native GREEN, six reached mutants, 78 source controls, scoped geometry reconciliation and deterministic build complete. Candidate committed; immutable packet/final independent review, non-deploy publication/PR, and exact-head/base owner merge approval pending.',candidateHead=HEAD)
write('execution.json',execution)
print(json.dumps({'head':HEAD,'base':BASE,'cases':38,'mutants':6,'sourceControls':78,'delivery':'PENDING'}))
