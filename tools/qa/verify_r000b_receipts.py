"""Read-only R000B reconciliation, following the delivered R000C verifier.

This validates temporal/acquisition/consumer custody, never pixels or motion.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs,urlsplit


def audit(path):
    r=json.loads(path.read_bytes());case=json.loads((path.parent/'case-input.json').read_bytes());failures=[]
    def require(ok,why):
        if not ok:failures.append(why)
    require(r['id']==case['id'],'case identity')
    require(r['status']=='PASS_ASSERTIONS_PENDING_PIXEL_REVIEW','original assertions')
    require(bool(r['checks']) and all(r['checks'].values()),'all original checks')
    require(r.get('runtimeUnchanged'),'runtime mutated during acquisition')
    f=r.get('fixture') or {};obs={o['stage']:o['state'] for o in r['observations']}
    require(f.get('sourceSha256')==r['sourceSha256'],'actual fetched source')
    require(f.get('storageIsolated') and f.get('clockIsolated') and f.get('fetchIntercepted'),'isolated dependencies')
    require(f.get('initialStorageEntries')==0,'private storage initially empty')
    require(all(e['action']=='consumer-read' for e in f.get('weatherEvents',[])),'bridge has a state mutation')
    require(not r.get('pageErrors') and not f.get('consoleErrors'),'native errors')
    weather=[x for x in f.get('ledger',[]) if 'weatherOrdinal' in x]
    radar=[x for x in f.get('ledger',[]) if 'radarOrdinal' in x]
    require(len(weather)>=3,'initial, failed and healthy weather acquisitions')
    for request in weather:
        q=parse_qs(urlsplit(request['url']).query)
        require(q.get('latitude')==['24.47'] and q.get('longitude')==['39.61'],'captured site')
        require(q.get('timezone')==['Asia/Riyadh'] and q.get('temperature_unit')==['celsius'],'captured zone/units')
        if request.get('status')==200:require(request.get('jsonReads')==1 and request.get('jsonSettled'),'native body consumed once')
    if len(weather)>=3:
        c=weather[0].get('parsedBody',{}).get('current',{})
        require(all(c.get(k)==v for k,v in {'time':'2026-09-07T21:30','interval':900,'weather_code':63,'temperature_2m':24,'precipitation':2,'cloud_cover':70}.items()),'original night CURRENT input')
        require(weather[1].get('status')==503 and weather[1].get('jsonReads')==0,'503 rejected before body')
        require(weather[2].get('status')==200,'ordinary healthy recovery')
        require(all(b['elapsedMs']-a['elapsedMs']>=60000 for a,b in zip(weather,weather[1:])),'weather start-based retry')
    require(bool(radar),'actual radar acquisition')
    if case['ordinaryRadarRecovery']:require(len(radar)>=2,'ordinary radar recovery missing')
    require(all(b['elapsedMs']-a['elapsedMs']>=600000 for a,b in zip(radar,radar[1:])),'radar start-based retry')
    passive=f.get('passive',[])
    before=[s for s in passive if 1788806699000<=s['wallUtcMs']<=1788806700000]
    after=[s for s in passive if 1788806700000<s['wallUtcMs']<1788806701000]
    require(bool(before) and all(s['modelEligible'] and s['radarEligible'] for s in before),'native near-inclusive-boundary positive')
    require(bool(after) and all(not s['modelEligible'] and not s['radarEligible'] for s in after),'native after-boundary unavailable')
    require(all(not s['modelEligible'] for s in passive if s['sourceAgeMs'] is not None and s['sourceAgeMs']>900000),'source expiry cannot be refreshed by receipt')
    for stage in ['current','expired','503','restored','restored-30s']:
        s=obs.get(stage)
        require(s is not None,'missing '+stage)
        if not s:continue
        require(s['card']=={'width':325,'height':530} and 0<=s['footer']['top']<s['footer']['bottom']<=530.1,'card/footer '+stage)
        require(len(s['rows'])==6,'six prayer rows '+stage)
        require(s['clock']=={'TIMESCALE':1,'FOLLOW_WALL_CLOCK':True,'ADVANCING':False},'ordinary 1x clock '+stage)
        require(s['lightning']=='off' and s['qa']['wxTruth']['observedPresent'] is False,'no invented lightning/observation '+stage)
        require(s['radar']['precipMm']==0 and s['qa']['wxTruth']['radarPrecipMm']==0,'no radar quantity '+stage)
        if stage in ['expired','503']:
            require(not s['modelEligible'] and not s['selected'] and s['temperature']=='' and s['icon']=='—' and s['precip']=='off' and s['visibleParticles']==0 and s['rainOpacity']==0,'expired presentation '+stage)
            require(s['qa']['wx']['cloud'] is None and all(s['qa']['clouds'][k]==0 for k in ['low','mid','high']),'expired cloud authority '+stage)
        else:
            require(s['modelEligible'] and s['temperature']=='24°' and s['precip']=='on' and s['visibleParticles']>0,'eligible wet presentation '+stage)
    if 'current' in obs and 'restored-30s' in obs:
        a,b=obs['current'],obs['restored-30s']
        require(abs((b['wallUtcMs']-a['wallUtcMs'])-(b['elapsedMs']-a['elapsedMs']))<10,'native elapsed 1x clock')
        require(all(s['cloudPopulation']==a['cloudPopulation'] for s in obs.values()),'cloud population reseeded')
        require(b['qa']['moonTruth']['phaseFraction']==.5 and b['qa']['moonTruth']['calendarMoonVisible'],'half-Moon state (pixels still required)')
    require(len(r['watches'])==1 and r['watches'][0]['stage']=='restored' and r['watches'][0]['endHostMonotonic']-r['watches'][0]['startHostMonotonic']>=30,'predeclared native 30-second watch')
    video=path.parent/r['video']['file']
    require(hashlib.sha256(video.read_bytes()).hexdigest()==r['video']['sha256'],'original video bytes')
    return {'id':r['id'],'status':'PASS' if not failures else 'FAIL','failures':failures,
            'sourceSha256':r['sourceSha256'],'runtimeSha256':r['runtime']['treeSha256'],
            'wrapperSha256':r['wrapperSha256'],'driverSha256':r['driverSha256'],
            'ordinaryRadarRecovery':case['ordinaryRadarRecovery'],
            'receiptSha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    p.add_argument('--complete',action='store_true',help='Require the exact six-case join and both ordinary radar recoveries')
    args=p.parse_args()
    rows=[audit(p) for p in sorted(args.root.glob('*/receipt.json'))]
    complete=True
    if args.complete:
        expected={f'B16-{b}-{m}' for b in ['chromium','firefox'] for m in ['default','reduced','full']}
        complete=(len(rows)==6 and {r['id'] for r in rows}==expected and
                  all(len({r[k] for r in rows})==1 for k in ['sourceSha256','runtimeSha256','wrapperSha256','driverSha256']) and
                  all(r['ordinaryRadarRecovery'] for r in rows if r['id'].endswith('-default')))
    report={'schema':'r000b-consumer-reconciliation/v1','cases':rows,'completeMatrixRequired':args.complete,
            'completeMatrixMatched':complete if args.complete else None,
            'status':'PASS' if rows and complete and all(r['status']=='PASS' for r in rows) else 'FAIL','limitation':__doc__}
    print(json.dumps(report,indent=2));return 0 if report['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
