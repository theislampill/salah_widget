from pathlib import Path
import hashlib,json,sys
O=Path(__file__).resolve().parent
R=Path(r'${REPO_ROOT}')
N=O/'native/firefox-lunar-rule-r115'
sys.path.insert(0,str(R/'tools/cp9'))
from runtime_identity import runtime_identity
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=json.loads((N/'results.json').read_bytes());run=j['runs'][0];f=run['final'];m=f['moon']
ref=json.loads((O/'numerical/reference-r114/RESULT.json').read_bytes())
reply=[x for x in f['workerPublication']['rows'] if x.get('kind')=='result']
assert len(reply)==1
reply=reply[0]
assert reply['scene']==reply['sent']['scene']==m['accepted']['scene']==ref['scene']
assert reply['physicalIdentity']==m['accepted']['identity']
assert reply['profileIdentity']==m['accepted']['profile']
assert m['current'] and m['visibleSource']=='refined-terrain' and m['status']=='ready'
assert m['quality']=='empirical-adaptive' and m['last']['quality']['projectedMaximumCode']==0.12836551666259766
assert f['sky']['status']=='ready' and not j['errors'] and not m['errors']
assert not f['workerPublication']['errors'] and not f['workerPublication']['overflow']
assert runtime_identity(R)==j['runtime']==runtime_identity(O/'builds/integrated-r29-lunar-rule')
assert not (O/'native-resource.lock').exists()
record={'schema':'r0021-lunar-rule-result/v1','sourceParent':'9df79b98d8dda7a0286b1b287dc03d1b4d760bdb','runtime':j['runtime']['treeSha256'],'nativeResultSha256':sha(N/'results.json'),'nativeExecutionSha256':sha(N/'EXECUTION.json'),'referenceSha256':sha(O/'numerical/reference-r114/RESULT.json'),'sourceReviewSha256':sha(O/'independent-review/moon-rule-r115-source-preflight-review-r1.json'),'claim':'Named retained numerical scene is now admitted and current in native Firefox; independent native review is separate. No S1, performance or global phase qualification.','mechanism':'Terminal8192 sample allocation64x128->32x256; same empirical gate, ceiling, kernel/material/assets/geometry.','quality':m['last']['quality'],'requestReplyAcceptedSceneEqualReference':True,'physicalIdentity':reply['physicalIdentity'],'profileIdentity':reply['profileIdentity'],'native':{'family':j['browser']['family'],'version':j['browser']['version'],'entry':j['entry'],'dpr':j['dpr'],'mode':run['mode'],'firstInitial':m['firstInitial'],'lastAdoption':m['lastAdoption'],'finalAtMs':f['at'],'elapsedMs':run['elapsedMs'],'status':m['status'],'visibleSource':m['visibleSource'],'current':m['current'],'rejected':m['rejected'],'skyStatus':f['sky']['status'],'card':f['card'],'prayerRows':f['prayerRows']},'images':{p.name:sha(p) for p in sorted(N.glob('*.png'))},'controls':{'red':'2 PASS/1 expected limit-reached failure','componentRun':'117 PASS/1 filesystem readFileSync UNKNOWN error before assertion','affectedHostRepeat':'55 PASS/0 FAIL; original error retained','originalFailureDisposition':'The failed host source bytes were unchanged; exact transient OS cause not established. No broad repeat.','build':'Two identical canonical142-entry builds; five expected generated paths changed,137 unchanged.'},'limits':['Sparse82 receiver diagnostic, not dense absolute accuracy.','Reference-versus4096 projected0.5844449997 and original17/.87832355499 rejection remain.','Native r115 is one traced functional case; not submillisecond performance or S1 timing evidence.','Historical rejected-job identity absent; retained accepted-preview scene recovered and compared exactly.']}
(O/'intake/moon-rule-r115-result.json').write_bytes((json.dumps(record,indent=2)+'\n').encode())
print(json.dumps({'resultSha256':sha(O/'intake/moon-rule-r115-result.json'),'images':len(record['images']),'runtime':record['runtime'],'sceneExact':True,'quality':m['quality'],'current':m['current']}))
