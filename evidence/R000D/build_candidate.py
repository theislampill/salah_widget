"""Join existing issue evidence without changing raw receipts or their verdicts."""
import hashlib,json
from pathlib import Path

BASE=Path(__file__).resolve().parent
def read(p):return json.loads((BASE/p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256((BASE/p).read_bytes()).hexdigest()
def dump(p,v):(BASE/p).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')

night=[]
for engine in ('chromium','firefox'):
    for mode in ('reduced','full'):
        folder=f'native/{engine}/D-preserve-weather-body-night-{mode}-r1'
        path=folder+'/receipt.json';r=read(path)
        assert r['sourceUnchanged'] and r['checks'] and all(v is True for v in r['checks'].values())
        assert r['status']=='EXECUTED_PENDING_NATIVE_PIXEL_REVIEW'
        observation=r['originalMotionObservation']
        night.append({'engine':engine,'mode':mode,'receipt':path,'sha256':sha(path),'checks':r['checks'],
          'actualWatchMs':observation['elapsedMs'],'sourceExpiry':r['sourceAgeExpiry'],
          'cloudCanvasDelta':observation['cloudCanvasDelta'],'visibleSkyDelta':observation['visibleSkyDelta'],
          'warmMoon':r['recovered']['preservation']['moonTruth'],
          'clock':'real1x; initially aged synthetic source; no wall offset or fifteen-minute receipt-age proof',
          'pixels':'Original held/expired-current/terminal/recovered and0/10/20/30 PNGs in same folder; independent pixel review governs',
          'continuousVideoClaim':'Only separately reviewed original Chromium160-190PTS interval may qualify. Entire videos/checkpoint-containing full interval are not claimed continuously intact. Firefox uses original PNG and render/canvas observations.'})
dump('native/a04-index.json',{'scope':'Original night state and motion evidence index; telemetry never overrides pixels. Independent disposition is separate.','cases':night})

audit=read('intake/accepted-audit.json')
matrix=[]
for row in audit['requirementMatrix']:
    item={'id':row['id'],'obligation':row['obligation'],'originalAuditStatus':row['status']}
    number=int(row['id'][1:])
    if number<=10:
        item.update(candidateDisposition='PRESERVED_CURRENT_SOURCE_AND_CONTROLS',proof=['qualification/currentness.json','qualification/runtime-identity.json','qualification/source-since-accepted-audit.patch','regression/receipt.json','A01/receipt.json'])
    elif number==11:item.update(candidateDisposition='THREE_REACHED_MUTANTS_ACCEPTED',proof=['A01/receipt.json','qualification/review-progress.json'])
    elif number==12:item.update(candidateDisposition='NATIVE_QUALIFICATION_SUBMITTED',proof=['native/a02-index.json','native/a03-index.json'])
    elif number==13:item.update(candidateDisposition='ORIGINAL_PIXELS_AND_MOTION_SUBMITTED',proof=['native/a04-index.json','contrary/historical-firefox/retention.json'])
    elif number==14:item.update(candidateDisposition='DOCS_CONTENT_ACCEPTED_DELIVERY_PENDING_MERGE',proof=['docs/candidate-identity.json','docs/source-facts-and-diff.md','qualification/review-progress.json'])
    elif number==15:item.update(candidateDisposition='INDEPENDENT_JOIN_AND_POST_MERGE_CLOSURE_REQUIRED',proof=['qualification/review-progress.json','delivery/premerge-public-bytes.json'])
    matrix.append(item)
candidate={
 'schema':'r000d-pre-delivery-candidate/v1','status':'PRE_DELIVERY_CANDIDATE_FOR_COMPLETE_INDEPENDENT_REVIEW',
 'issue':'https://github.com/theislampill/salah_widget/issues/13','workOrder':'R000D',
 'immutableSpecCommit':'21e7a84365fae37a86cae5c7d5e41008c0adc53f','acceptedAuditCommit':'b879573c298f19189d1f2392108b8b9f3b2cda0b',
 'sourceCommit':'06772824a159cd2bc42a1d9f79a3fb22fa46e49d','docsHead':'94b5ddf5d61feb4c166050bed1460c6940eb20ad',
 'deliveryMode':'docs-merge','runtimeChanged':False,'runtimeIdentity':read('qualification/currentness.json'),
 'requirements':matrix,
 'acceptance':{'A01':'A01/receipt.json','A02':'native/a02-index.json','A03':'native/a03-index.json','A04':'native/a04-index.json','A05':'docs/candidate-identity.json','A06':'Independent complete candidate/exact-head review and actual post-merge delivery/closure required'},
 'reusedR0003':{'evidenceCommit':'e10c574dba17077640bb1bfc5683098ffad73ce3','deliveryCommit':'94811a62959cd64522e2a39e30ee83468ecd39f6','finalReadbackCommit':'2fd2fceee90b91233796b43f17191bca7c9a6fe5','scope':'Exact135-file runtime identity, source ownership interfaces, fixture and public-reader components. Different R0003 viewport/input/motion is not relabelled as R000D native or night proof.'},
 'pending':['Complete independent exact-candidate and actual PR head acceptance','Owner approval of exact-head PR merge','Normal merge without auto-closing issue references','Actual merged/document/runtime/public consumer readback','Exact CLOSE-R000D independent acceptance','Post certificate while issue OPEN and independently read actual comment/references','Intentionally close issue completed and independently verify order/state','Publish compact final readback receipt'],
 'retainedLimits':['Four original TODOs remain TODO','Normal abort cancellation is not delivered late JSON; ignored-abort controls are separately labelled','No physical network cancellation, memory reclamation, suspended-process recovery or exact-millisecond native timer guarantee','Radar throttle uses disclosed600001ms wall offset only after real monotonic timeout, not a ten-minute real watch','Night source TTL starts aged; no real fifteen-minute receipt/cache-age watch','No continuous Firefox screencast claim; historical blank frames retained','Chromium whole-run/checkpoint-containing crop disturbances retained; separate original30s interval review required','Controlled provider data are synthetic model estimates, not observed precipitation or provider health','No new broad sky-science qualification; frozenV1 and runtime unchanged'],
 'authority':'Owner already authorized evidence/PR preparation and post-approval certificate-first closure. Exact-head production merge remains reserved. This file is not a completed closure certificate.'}
dump('reviewed-candidate-certificate.json',candidate)
print(json.dumps({'nightCases':len(night),'mandatoryRows':len(matrix),'status':candidate['status']}))
