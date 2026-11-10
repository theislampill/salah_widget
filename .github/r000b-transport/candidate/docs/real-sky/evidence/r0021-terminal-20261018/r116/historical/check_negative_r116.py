"""Offline use of the unchanged r52 pixel discriminator on retained originals."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
R=Path(r'${REPO_ROOT}')
N=O/'native/chromium-pipeline-stream-r19'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
annotation=N/'source-annotations-r52.json'
j=json.loads(annotation.read_bytes());run=j['runs'][0];rows=run['rows']
selected=[x for x in rows if 9<=x['seq']<=24]
assert [x['seq'] for x in selected]==list(range(9,25))
assert all(x['classification']=='HEURISTIC_ONLY' and x['size']==[390,600] for x in selected)
missing=[x for x in selected if not x['moon']]
assert [x['seq'] for x in missing]==list(range(11,24))
assert all(x['moon'] for x in selected if x['seq'] in [9,10,24])
span=(missing[-1]['sourceTimeSeconds']-missing[0]['sourceTimeSeconds'])*1000
intervals=[(b['sourceTimeSeconds']-a['sourceTimeSeconds'])*1000 for a,b in zip(missing,missing[1:])]
assert span>80 and max(intervals)<80
v=Path(run['video']);frame_root=Path(str(v)+'.frames')
for row in selected:assert sha(frame_root/row['file'])==row['sha256']
positive=R/'docs/real-sky/evidence/r0021-arc-samples-20261018/r105-annotations.json'
p=json.loads(positive.read_bytes())['runs'][0];first=p['firstCompleteHeuristic']['seq'];positive_rows=[x for x in p['rows'] if x['seq']>=first]
assert positive_rows and all(x.get('moon') for x in positive_rows)
record={'schema':'r0021-retained-negative-control/v1','status':'DETECTED_RETAINED_NEGATIVE_REQUIRES_INDEPENDENT_EQUIVALENCE_REVIEW','scope':__doc__,'detectorSha256':sha(O/'annotate_direct_source_r52.py'),'annotationsSha256':sha(annotation),'nativeResultsSha256':sha(N/'results.json'),'originalObservationSha256':sha(N/'MOON-GAP-OBSERVATION-r22.json'),'sourceControlSha256':sha(O/'independent-review/worker-lunar-r20/MOON-STAGED-CONTROL.json'),'candidateSourceParent':'fd309d10598a89ce3700550a71abc6bac25e9052','candidateDetailSourceSha256':sha(R/'moon/src/moon-detail.mjs'),'historicalRuntime':json.loads((N/'results.json').read_bytes())['runtime']['treeSha256'],'selected':selected,'missingSourceFrameCount':len(missing),'missingSourceClockSpanMs':span,'maximumInternalSourceIntervalMs':max(intervals),'thresholdMs':80,'positiveControl':{'record':'docs/real-sky/evidence/r0021-arc-samples-20261018/r105-annotations.json','sha256':sha(positive),'firstCoherentSeq':first,'reviewedClassifiedFrameCount':len(positive_rows),'allClassifiedMoonPresent':True,'gapsRemainUnobserved':p['gapsOver80']},'claim':'The unchanged pixel discriminator detects the known native missing-Moon case over13 consecutive source images spanning>80ms, with present-before/present-after controls. No source clocks or missing images are manufactured.','limits':['Human original-pixel and warranted-scene/clock review required for equivalence underTA1.','Source-frame span is not uninterrupted physical display timing; gaps remain unobserved.','This is the historical r11 failure, not a new current-candidate defect or current S1 PASS.','Positive r105 observations do not transfer timing or fill its acquisition gaps.']}
(O/'intake/ta1-negative-r116.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
print(json.dumps({'sha256':sha(O/'intake/ta1-negative-r116.json'),'missingFrames':len(missing),'sourceSpanMs':span,'maxInternalGapMs':max(intervals),'positiveFrames':len(positive_rows)}))
