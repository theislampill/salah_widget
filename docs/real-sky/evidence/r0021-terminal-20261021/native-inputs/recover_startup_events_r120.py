"""Read archived native event intervals; no new acquisition or performance verdict."""
from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent;C=O/'cost';N=C/'runs/chromium-native-v5-r76'
sys.path.insert(0,str(C))
from native_profile_v5 import read_marks,decode,select_export_prefix
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((N/'RESULTS.json').read_bytes());analysis=json.loads((N/'ANALYSIS.json').read_bytes())
out={'schema':'r0021-archived-startup-event-transfer/v1','source':str(N),'sourceSha256':sha(N/'RESULTS.json'),
 'analysisSha256':sha(N/'ANALYSIS.json'),'runtime':record['runtime'],'status':'ARCHIVED_ACTUAL_LIFETIME_ONLY_NO_NEW_PASS',
 'currentRuntime':'3e18b2fa83d0cbfce0a4360d789f7927aef5c064f963e8c18acb430507995821',
 'sourceDisposition':'r76 predates final startup/publication changes. Unchanged dependencies transfer only after final owner review; no blanket final-candidate timing credit.',
 'startupCallbacks':analysis['startupCallbacks'],'slots':[]}
for slot in record['slots']:
    rawpath=N/slot['rawFile'];profilepath=N/slot['nativeProfileFile']
    assert sha(rawpath)==slot['callsSha256'] and sha(profilepath)==slot['nativeProfileSha256']
    raw=json.loads(rawpath.read_bytes());marks=read_marks(json.loads(profilepath.read_bytes()),'chromium')
    marks,document,excluded=select_export_prefix(marks,raw,slot['documentReadback'],slot['documentMarkerLabel'],'CrRendererMain')
    index,calls=decode(marks,raw,document['documentId'],'CrRendererMain')
    bound=index[slot['warmStart']['name']]['at']
    startup=[x for x in calls if x['startMs']<bound and not x['scope'].startswith('probe.')]
    out['slots'].append({'id':slot['id'],'side':slot['side'],'callsSha256':slot['callsSha256'],
      'profileSha256':slot['nativeProfileSha256'],'originalWarmStartNativeMs':bound,'document':document,'excludedSuffix':excluded,'startupCalls':startup})
    print(slot['id'],len(startup),flush=True)
out['actualOwnerMap']={
 'startup':['head.prepareNativeFirstPaint','preview.update','preview.paint','moon.initialPresentation','main.firstTaskYield'],
 'minuteTargetGeometry':['main.render','main.commitSkyScene','preview.update','sky.accept','sky.compose'],
 'workerAdoption':['sky.workerMessage','sky.accept','moon.workerMessage','moon.adopt','moon.syncTexture','moon.detailCompose'],
 'warmed':['main.paint and main.render proof excepted by TA5 only','moon.poll archived inclusive result by exact dependency'],
 'changedWeatherMask':['main.applyTheme','main.atmosphere','main.paintClouds','preview.paint/publishPreview','sky.compose/publishComposition','NativeSolarMaskPublication.publish/finish','mask preparation/PNG export, real decode initiation and completion/rejection/commit'],
 'shiftedWorker':['H1 foreground preparation below solar altitude -20 degrees; actual worker CPU retained','twilight/day preparation remains separate missing dependency']}
out['retainedContrary']={'historicalSkyAcceptExclusiveMedianP95Ms':{'baseline':[.10,.20],'candidate':[24.45,27.20]},
 'historicalSkyAcceptInclusiveMedianP95Ms':{'baseline':[19.40,20.60],'candidate':[41.20,46.30]},'historicalCounts':[9,8],
 'caution':'These historical values are concerning, not a qualified final-runtime regression. Deep-night routing does not establish twilight/day equivalence or erase worker cost.'}
out['remainingAcquisition']='One finite matched Chromium event group only: actual startup, preview, target/minute/geometry, adoption/detail/syncTexture, twilight/day sky.accept and shifted worker, admitted late-weather plus unchanged control, and positive solar masks on both owners including async completion. Preserve all counts/errors/rates, max(.25ms,10%) tolerance and uncertainty; no artificial warmed population or fresh steady ABBA campaign. Firefox submillisecond exception remains TA2.'
p=O/'intake/startup-events-r120-transfer.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'output':str(p),'sha256':sha(p),'slots':len(out['slots']),'startupCalls':sum(len(s['startupCalls']) for s in out['slots'])}))
