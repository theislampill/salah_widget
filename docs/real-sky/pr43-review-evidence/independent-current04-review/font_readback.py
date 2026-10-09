"""Narrow readback of the newly returned current04 native font observations."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
RUN=HERE.parents[2]
ROOT=RUN/'evidence/PR43-review/R2-font-final-04'
DRIVER=RUN/'workers/clock_date/font-driver-r5'
TREE='040192b555fa0db2fad760470ec020a06d86d3e0c7615153062ec5e76c50a2d5'
INDEX='67e2ff84eb1e7422bfc390f98b641c8e3f93f76a77400401681be10676eb8d3d'
checks=[];inputs={};rows=[];images=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
    b=p.read_bytes();inputs[str(p)]={'bytes':len(b),'sha256':sha(b)};return json.loads(b)
def check(name,ok,**details):checks.append({'name':name,'pass':bool(ok),**details})
def count(s):return len(s['fitMeasurements'])
def forced(s):return sum(x.get('event')=='explicit-fit-invalidation-control' for x in s['trace'])
def bounds(s):return {k:s['typography'][k] for k in ('currentInk','heroInk','heroCenterError')}
seal=read(DRIVER/'SEAL.json')
check('r5 seal pin',inputs[str(DRIVER/'SEAL.json')]['sha256']=='bea77450459950c2a66b9bcf0662a79037c3570da5150b7ca92ef39da1f08160'
      and seal['sourceIndexSha256']==INDEX and seal['runtimeTreeSha256']==TREE)
for name,pin in seal['files'].items():
    b=(DRIVER/name).read_bytes();check('r5 sealed file '+name,len(b)==pin['bytes'] and sha(b)==pin['sha256'])
check('r5 Python observations unchanged from r4',(DRIVER/'rlgwo_native_checks.py').read_bytes()==(DRIVER.parent/'font-driver-r4/rlgwo_native_checks.py').read_bytes())
receipt=read(ROOT/'receipt.json')
check('18 current cases returned',receipt['complete'] is True and len(receipt['jobs'])==2
      and sum(len(j['results']) for j in receipt['jobs'])==18
      and {j['engine'] for j in receipt['jobs']}=={'chromium','firefox'})
runtime=read(ROOT/'chromium-green/font-runtime-identity.json')
canonical=''.join(f"{runtime['files'][n]['sha256']}  {n}\n" for n in sorted(runtime['files']))
check('font runtime canonical identity',runtime['treeSha256']==TREE and sha(canonical.encode())==TREE)
for job in receipt['jobs']:
    engine=job['engine'];out=ROOT/(engine+'-green');manifest=read(out/'manifest.json')
    check('actual engine/job binding '+engine,job['exitCode']==0 and len(job['results'])==9
          and manifest['driverSha256']==seal['files']['rlgwo_native_checks.py']['sha256']
          and manifest['adapterSha256']==seal['files']['rlgwo-clock-date-fixture.cjs']['sha256']
          and read(out/'font-runtime-identity.json')==runtime)
    for case in job['results']:
        variant=case['variant'];folder=out/('font--'+variant);r=read(folder/'result.json');identity=r['source']
        check('font exact source '+engine+'/'+variant,identity['sourceSha256']==INDEX
              and identity['effectiveSourceSha256']==INDEX and identity['sourceMutation'] is None
              and identity['runtimeTreeSha256']==TREE and identity['scriptLayout']['id']=='combined_r1r2_04'
              and identity['scriptLayout']['nativeOrdinal']==3)
        check('font returned mechanics '+engine+'/'+variant,case['status']==r['status']=='PARTIAL_NATIVE_SCOPE'
              and not r['pageErrors'] and r['checks'] and all(c['result']=='PASS' for c in r['checks']))
        state_by_name={s['name']:s['state'] for s in r['states']}
        state_rows=[{'name':s['name'],'fitCount':count(s['state']),'forcedClearCount':forced(s['state']),
                     'fontSet':s['state']['fonts']['status'],'FrauncesCheck':s['state']['fonts'].get('fraunces'),
                     'bounds':bounds(s['state'])} for s in r['states']]
        metric={}
        if variant=='split-face-forenoon':
            arrived=state_by_name['split-Fraunces-loaded-Inter-still-held']
            natural=state_by_name['split-three-natural-fits-before-Inter-completion']
            both=state_by_name['split-both-real-families-registered-bytes-held']
            check('split-face actual natural fit '+engine,arrived['fonts']['status']==natural['fonts']['status']=='loading'
                  and arrived['fonts']['fraunces'] is True and natural['fonts']['fraunces'] is True
                  and count(natural)==count(both)+1 and count(both)<=count(arrived)<=count(natural)
                  and not forced(natural)
                  and all(not forced(s['state']) for s in r['states']))
            metric={'arrivalFitCount':count(arrived),'naturalBeforeInterFitCount':count(natural),
                    'forcedClearCount':forced(natural),'heroCenterError':natural['typography']['heroCenterError']}
        else:
            arrival=state_by_name['font-terminal-state-before-next-native-fit']
            natural=state_by_name['font-after-three-natural-fit-calls']
            control=state_by_name['explicit-cache-invalidation-control']
            check('stable natural cache and reached diagnostic '+engine+'/'+variant,
                  count(natural)==count(arrival) and not forced(natural)
                  and count(control)==count(natural)+1 and forced(control)==forced(natural)+1)
            diffs=[abs(natural['typography'][k][n]-control['typography'][k][n])
                   for k in ('currentInk','heroInk') for n in natural['typography'][k]]
            metric={'stableAdditionalMeasurements':count(natural)-count(arrival),
                    'explicitAdditionalMeasurements':count(control)-count(natural),
                    'maximumNaturalControlRangeBoxDelta':max(diffs),
                    'heroCenterError':natural['typography']['heroCenterError']}
        rows.append({'engine':engine,'variant':variant,'status':r['status'],'checks':r['checks'],
                     'states':state_rows,'metric':metric,'fontRoutingDisablesCache':r['fontRoutingDisablesCache'],
                     'cacheAttribution':r['cacheAttribution'],'limits':r['limits']})
        if variant in ('split-face-forenoon','delayed-css-forenoon','permanent-bytes-forenoon','loaded-sunrise','loaded-maghrib'):
            name='split-three-natural-fits-before-Inter-completion.png' if variant=='split-face-forenoon' else 'font-after-three-natural-fit-calls.png'
            p=folder/name;b=p.read_bytes();images.append({'kind':'font-current-natural','engine':engine,'variant':variant,
                                                       'path':str(p),'bytes':len(b),'sha256':sha(b)})
result={'schema':'independent-current04-font-readback/1',
        'status':'PASS_CURRENT_FONT_MECHANICS_PIXELS_REQUIRE_REVIEW' if all(c['pass'] for c in checks) else 'FONT_READBACK_FAILURE',
        'scope':'Native typography only; old RED retained, no new execution by reviewer',
        'runtime':TREE,'index':INDEX,'driverSealSha256':inputs[str(DRIVER/'SEAL.json')]['sha256'],
        'checks':checks,'inputs':inputs,'rows':rows,'images':images}
(HERE/'FONT_READBACK.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[c for c in checks if not c['pass']],
                  'metrics':[{'engine':r['engine'],'variant':r['variant'],**r['metric']} for r in rows]},indent=2))
assert all(c['pass'] for c in checks)
