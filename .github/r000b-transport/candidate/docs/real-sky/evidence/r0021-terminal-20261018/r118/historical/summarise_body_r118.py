"""Assert the actual body-error/current-retention/retry/admitted-final chain."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;N=O/'native/body-interruption-r118'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
execution=json.loads((N/'EXECUTION.json').read_bytes())
assert execution['status']=='RETURNED' and execution['leaseReleased'] and execution['runtimeUnchanged'] and execution['harnessUnchanged']
assert not (O/'native-resource.lock').exists()
record={'schema':'r0021-body-interruption-observation/v1','scope':__doc__,'status':'CONTROL_CHAIN_SATISFIED_PENDING_INDEPENDENT_NATIVE_REVIEW','executionSha256':sha(N/'EXECUTION.json'),'derivationSha256':sha(Path(__file__)),'runtime':execution['runtime'],'cases':{},'limits':['Controlled functional check, not startup/callback/wholeS5/continuous-presentation qualification.','HTTP200 body interruption is distinct from status rejection, binary decompression and worker result validation.','Chromium generic network error does not identify an exact read/cancel statement; Firefox explicit truncated-asset error identifies the read byte-count guard.','Existing harness explicitly invokes both Moon and sky-assets retry; no automatic retry or user UI action is claimed.','Delayed-body timeout, actual applicable decoder failure, late stale-result and other listed S5/S6 predicates retain their separate dispositions.']}
for arm in ['chromium','firefox']:
    folder=N/arm;data=json.loads((folder/'results.json').read_bytes());r=data['runs'][0]
    assert data['runtime']['treeSha256']==record['runtime'] and data['runtimeUnchanged'] and not data['errors']
    events=[x for x in r['serverRequests'] if x.get('kind')=='controlled-response-body-interruption']
    assert len(events)==1 and events[0]['httpStatus']==200 and events[0]['declaredBytes']==20137935 and events[0]['sentBytes']==4096
    first=r['at15s']['moon'];final=r['final']['moon']
    assert first['status']=='unavailable' and first['current'] and first['visibleSource']=='initial-v5' and not first['workerAlive'] and first['errors']
    assert r['recovery']['retry']['moon'] is True
    assert final['status']=='ready' and final['current'] and final['visibleSource']=='refined-terrain' and final['workerAlive'] and final['retryCount']==1 and final['rejected']==0
    quality=final['last']['quality'];assert quality['status']=='empirical-adaptive' and quality['unsettled']==0 and quality['projectedMaximumCode']<=quality['projectedGate']==.5
    assert r['final']['sky']['status']=='ready' and len(r['final']['prayerRows'])==6
    assert r['at15s']['card']['width']==r['final']['card']['width']==325 and r['at15s']['card']['height']==r['final']['card']['height']==530
    requests=[x for x in r['serverRequests'] if x.get('url')=='/salah_widget/moon/assets/dem.bin.gz' and not x.get('kind')]
    assert len(requests)>=2 and requests[-1]['absolute']>events[0]['absolute']
    record['cases'][arm]={'resultsSha256':sha(folder/'results.json'),'browser':data['browser'],'event':events[0],'demRequests':requests,'failedState':{k:first.get(k) for k in ['status','current','visibleSource','errors','workerAlive','retainedReason','firstInitial','accepted']},'recovery':r['recovery'],'finalState':{k:final.get(k) for k in ['status','current','visibleSource','retryCount','workerAlive','rejected','errors','accepted']},'quality':quality,'elapsedMs':r['elapsedMs'],'skyStatus':r['final']['sky']['status'],'card':r['final']['card'],'prayerRows':r['final']['prayerRows'],'images':{p.name:sha(p) for p in sorted(folder.glob('*.png'))},'video':{'file':Path(r['video']).name,'sha256':sha(Path(r['video']))} if r.get('video') else None}
out=N/'RESULT.json';assert not out.exists();out.write_bytes((json.dumps(record,indent=2)+'\n').encode())
print(json.dumps({'sha256':sha(out),'cases':{k:{'error':v['failedState']['errors'],'retainedCurrent':v['failedState']['current'],'final':v['finalState']['visibleSource'],'projectedMaximumCode':v['quality']['projectedMaximumCode']}for k,v in record['cases'].items()}}))
