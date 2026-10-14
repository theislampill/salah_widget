"""Read-only reconciliation of completed delivery acquisition. No browser/test run."""
from pathlib import Path
import datetime, hashlib, json, struct
E=Path(r'C:\workspace\ai\r000b-execution-20261014')
O=E/'delivery/public-consumer'
sha=lambda b:hashlib.sha256(b).hexdigest()
def bind(path):
    b=path.read_bytes()
    return {'path':str(path),'bytes':len(b),'sha256':sha(b)}
receipt=O/'readback.json';raw=receipt.read_bytes()
assert sha(raw)=='d81ccf9cdcee55692d17ff5fcc512d9635ada47b5aadea2edb54ad24629074a0'
r=json.loads(raw)
assert r['status']=='PASS_ASSERTIONS_PENDING_PIXEL_REVIEW'
assert r['mergeCommit']=='763a460e98dc23c7f0e95bf346274f1685b3c654'
assert r['procedureSha256']==sha((E/'delivery/public_consumer.py').read_bytes())=='0c95357fe42643ac9bf839d11b55776031d9fd6633fe3d3b74cb768748ce1b6e'
assert r['playwrightVersion']=='1.60.0'
assert r['preloadSha256']==r['storedPreloadSha256']==sha((O/'preload.js').read_bytes())
assert r['caseInputsSha256']==sha((O/'case-input.json').read_bytes())
assert r['controlledTileSha256']==sha((O/'controlled-tile.png').read_bytes())
assert r['viewport']=={'width':390,'height':600} and r['deviceScaleFactor']==1
assert not r['productionResponseRewritten'] and not r['sourceObserverInserted'] and not r['qaStateCalled']
assert [e['engine'] for e in r['results']]==['chromium','firefox']
reports=[];image_bindings=[];docs=[]
for ordinal,e in enumerate(r['results'],1):
    assert e['status']=='PASS_ASSERTIONS_PENDING_PIXEL_REVIEW' and e['headless']
    assert e['sourceExact'] and e['sourceSha256']=='d4e3f084aea7d264a5c790268a21aa015b5e565e1feb9ad853d953c1c8a7b26f' and e['httpStatus']==200
    assert not e['pageErrors'] and not e['networkErrors']
    assert e['url'].startswith('https://theislampill.github.io/salah_widget/?')
    assert [s['stage'] for s in e['states']]==['current','expired','503','restored','settled']
    visualpath=E/('independent-review/delivery/consumer-'+e['engine']+'-pixels.json')
    visual=json.loads(visualpath.read_bytes())
    assert sha(json.dumps(e,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode())==visual['engineSnapshotCanonicalSha256']
    identity=None; rows=[]
    for index,s in enumerate(e['states']):
        o=s['observed'];f=o['fixture']
        assert f['state']=='ready' and f['error'] is None
        assert f['storageIsolated'] and f['clockIsolated'] and f['fetchIntercepted'] and f['initialStorageEntries']==0
        assert f['clockPolicy']=='advancing-1x' and f['attempt']==ordinal and f['run']=='R000B-delivery-20261014'
        assert f['sourceSha256']==e['sourceSha256'] and not o['productObserverPresent']
        thisidentity=(f['documentId'],f['attempt'],f['run'],f['hash'],f['sourceSha256'])
        if identity is None:identity=thisidentity
        assert identity==thisidentity
        assert all(x['result']!='unexpected-request' for x in f['ledger'])
        assert len(o['weatherCache'])==1
        w=o['weatherCache'][0]['value']['w']
        assert w['currentIntervalSec']==900 and w['currentZone']=='Asia/Riyadh' and w['temp']==24 and w['precip']==2
        assert w['retrievedAt']>w['currentValidAt']
        source_age=o['wallUtcMs']-w['currentValidAt'];receipt_age=o['wallUtcMs']-w['retrievedAt']
        assert abs(source_age-s['sourceAgeMs'])<.1 and abs(receipt_age-s['receiptAgeMs'])<.1
        wet=s['stage'] in ['current','restored','settled']
        assert o['temperature']==('24\u00b0' if wet else '')
        assert o['precip']==('on' if wet else 'off') and o['lightning']=='off'
        assert (o['visibleParticles']>0 if wet else o['visibleParticles']==0)
        assert (o['rainOpacity']>0 if wet else o['rainOpacity']==0)
        assert o['fx']==('rain' if wet else 'unavailable')
        if wet:
            assert 0<=source_age<=900000 and 0<=receipt_age<=900000
            assert 'current model estimate' in o['headerLabel'] and 'direct local observation unavailable' in o['headerLabel']
        else:
            assert source_age>900000 and 0<=receipt_age<900000 and o['icon']=='\u2014'
        assert o['card']=={'width':325,'height':530} and o['rows']==6
        assert 0<=o['footer']['top']<o['footer']['bottom']<=530.1 and o['browserTimezone']=='Asia/Riyadh'
        assert abs((o['wallUtcMs']-1788806690000)-o['elapsedMs'])<10
        assert o['elapsedMs']<=s['captureStart']['elapsedMs']<=s['captureEnd']['elapsedMs']
        for c in ['captureStart','captureEnd']:
            assert abs((s[c]['wallUtcMs']-1788806690000)-s[c]['elapsedMs'])<10
        weather=[x for x in f['ledger'] if 'weatherOrdinal'in x]
        radar=[x for x in f['ledger'] if 'radarOrdinal'in x]
        assert len(weather)==[1,1,2,3,3][index] and [x['weatherOrdinal'] for x in weather]==list(range(1,len(weather)+1))
        assert weather[0]['status']==200 and weather[0]['jsonReads']==1 and weather[0]['jsonSettled']
        if len(weather)>=2:assert weather[1]['status']==503 and weather[1]['jsonReads']==0 and not weather[1].get('jsonSettled')
        if len(weather)==3:assert weather[2]['status']==200 and weather[2]['jsonReads']==1 and weather[2]['jsonSettled'] and weather[2]['jsonElapsedMs']<=o['elapsedMs']
        assert len(radar)==1 and radar[0]['status']==200 and radar[0]['jsonReads']==1 and radar[0]['jsonSettled']
        assert radar[0]['parsedBody']['generated']==1788806670 and radar[0]['parsedBody']['radar']['past'][0]['time']==1788805500
        p=O/s['screenshot'];b=p.read_bytes()
        assert sha(b)==s['pngSha256'] and b[:8]==b'\x89PNG\r\n\x1a\n'
        assert list(struct.unpack('!II',b[16:24]))==[390,600]
        assert all(s['checks'].values())
        image_bindings.append(bind(p))
        rows.append({'stage':s['stage'],'elapsedMs':o['elapsedMs'],'sourceAgeMs':source_age,'receiptAgeMs':receipt_age,
                     'currentValidAt':w['currentValidAt'],'retrievedAt':w['retrievedAt'],
                     'weatherRequestCount':len(weather),'captureStart':s['captureStart'],'captureEnd':s['captureEnd'],
                     'imageSha256':sha(b),'rawReconciliation':'PASS'})
    states=e['states']
    assert states[0]['observed']['elapsedMs']<10000 and states[0]['observed']['weatherCache'][0]['value']['w']['currentValidAt']==1788805800000
    assert states[0]['observed']['weatherCache'][0]['value']==states[1]['observed']['weatherCache'][0]['value']==states[2]['observed']['weatherCache'][0]['value']
    assert states[3]['observed']['weatherCache'][0]['value']['w']['currentValidAt']>1788805800000
    assert states[3]['observed']['weatherCache'][0]['value']==states[4]['observed']['weatherCache'][0]['value']
    weather=[x for x in states[-1]['observed']['fixture']['ledger'] if 'weatherOrdinal' in x]
    gaps=[b['elapsedMs']-a['elapsedMs'] for a,b in zip(weather,weather[1:])]
    assert all(x>=60000 for x in gaps)
    assert abs((states[-1]['observed']['wallUtcMs']-states[0]['observed']['wallUtcMs'])-(states[-1]['observed']['elapsedMs']-states[0]['observed']['elapsedMs']))<10
    assert states[-1]['observed']['elapsedMs']-states[-2]['observed']['elapsedMs']>=2200
    assert all(e['sequenceChecks'].values()) and e['controlledTileRequests']
    assert all(x['sha256']==r['controlledTileSha256'] for x in e['controlledTileRequests'])
    docs.append(identity[0])
    reports.append({'engine':e['engine'],'version':e['version'],'executableSha256':e['executableSha256'],
       'documentId':identity[0],'attempt':ordinal,'sourceExact':True,'rawReconciliation':'PASS',
       'requestDispatchElapsedMs':[x['elapsedMs'] for x in weather],'requestIntervalsMs':gaps,
       'native1xClockConsistent':True,'cacheRetainedThroughExpiryAnd503':True,'newEligibleSourceThroughOrdinaryRetry':True,
       'states':rows,'pixelReview':bind(visualpath)})
assert len(set(docs))==2
out={'schema':'r000b-independent-delivery-consumer-reconciliation/v1','status':'PASS','reviewedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'receipt':bind(receipt),'procedure':bind(E/'delivery/public_consumer.py'),'preload':bind(O/'preload.js'),
 'caseInputs':bind(O/'case-input.json'),'controlledTile':bind(O/'controlled-tile.png'),'engines':reports,'originalPngs':image_bindings,
 'observations':['All raw retained state/cache/ledger/clock/image fields were independently reconciled, not accepted solely from PASS booleans.',
 'The completed Chromium element exactly matches its earlier canonically bound review; Firefox also matches its pixel report.',
 'The preserved post-screenshot check covers temperature and precip equality; full after-read DOM/cache is not retained, so no broader after-state identity is inferred.',
 'Date/performance consistency is checked within the declared advancing1x fixture; unchanged native timer/retry paths were statically reviewed. No new host/video continuous-watch claim.',
 'Four cold current/expired Moon omissions remain. Ten original native390x600 PNGs were actually viewed. No between-capture pixels inferred.'],
 'browserExecutedByReviewer':False,'blockingFindings':[]}
p=E/'independent-review/delivery/consumer-reconciliation.json';p.write_bytes((json.dumps(out,indent=2)+'\n').encode())
print(json.dumps({'status':out['status'],'engines':len(reports),'originalPngs':len(image_bindings),'receipt':bind(p)}))
