"""Offline consumer checks for retained R0003 native traces; never drives a browser."""
import argparse, hashlib, json
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from r0007_browser import check_expected

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def source_association(folder,c,h):
    observed=(folder/'observed.html').read_text(encoding='utf-8').replace('\r\n','\n')
    start=observed.index('<head><script>')+len('<head>');end=observed.index('</script>',start)+len('</script>')
    preload=observed[start:end]
    embedded=preload.split('const spec=',1)[1].split(', NativeDate=Date',1)[0]
    assert json.loads(embedded)==c,'executed preload input differs from retained case'
    stripped=observed[:start]+observed[end:]
    anchor='\n// TEST-ONLY read-only completed-render receipt; never computes product diagnostics.'
    a=stripped.index(anchor);b=stripped.index('\nboot();',a)
    hook=stripped[a:b];stripped=stripped[:a]+stripped[b:]
    source=(Path(__file__).resolve().parents[2]/c['entry']).read_bytes()
    assert hashlib.sha256(source).hexdigest()==h['source'],'source changed after qualification'
    expected=source.decode().replace('\r\n','\n')
    if c.get('variant')=='no-abort':expected=expected.replace('controller:typeof AbortController!=="undefined"?new AbortController():null','controller:null')
    elif c.get('variant')=='unconditional-finally':expected=expected.replace('if(!requestEligible(op)) return false;\n  _requestSlots[op.kind]=null; return true;','_requestSlots[op.kind]=null; return true;')
    assert stripped==expected,'source outside admitted observer/variant changed'
    return {'preloadSha256':hashlib.sha256(preload.encode()).hexdigest(),'renderHookSha256':hashlib.sha256(hook.encode()).hexdigest(),'originalSourceOutsideHookAndVariantIdentical':True}
def check(folder):
    t=read(folder/'trace.json');c=read(folder/'case-input.json');h=read(folder/'document-hashes.json')
    assert sha(folder/'observed.html')==h['observed'],'observed document identity'
    association=source_association(folder,c,h)
    assert not t.get('pageErrors'),'native page error'
    assert not t.get('unexpected'),'unexpected provider'
    assert not [e for e in t['events'] if e['type'] in ('error','unhandledrejection')],'native error event'
    checks=['observed-document','no-native-error','no-unmatched-provider']
    if c.get('expectedFailure'):
        assert t['status']=='FAIL','mutant did not fail'
        try:check_expected(t,c['expected'])
        except AssertionError as e:
            assert str(e)=='flags/currentOwnerLat: expected 40.71, observed None',str(e)
        else:raise AssertionError('reached replacement-owner oracle did not fail')
        rows=[s for s in t['snapshots'] if s.get('checkpoint')=='successor-slot']
        assert rows and rows[-1]['runtimeGeneration']==1
        assert any(r['rule']=='B' for r in t['requests']) and 'B:1' in [e.get('key') for e in t['events'] if e['type']=='body-hold']
        checks.append('REACHED_EXPECTED_MUTANT_FAILURE')
    else:
        assert t['status'] in ('PASS_ASSERTIONS_PENDING_PIXEL_REVIEW','PARTIAL_FIRST_PRESENTATION_REVIEW_REQUIRED'),t.get('error',t['status'])
        check_expected(t,c['expected']);checks.append('original-case-assertions')
    # Request URL, captured owner and timer must agree independently of the later DOM.
    owners=[]
    for r in t['requests']:
        q=parse_qs(urlsplit(r['url']).query)
        if r['kind']=='prayer':
            day=urlsplit(r['url']).path.split('/')[-1]
            matching=[o for k,o in r['owner'].items() if k in ('current','prefetch') and o and o['requestedDay']==day and o.get('attempt')]
            assert len(matching)==1,(r['serial'],matching)
            o=matching[0]
            assert q['method']==[str(o['method'])] and q['school']==[str(o['school'])]
        else:o=r['owner'][r['kind']]
        assert o and o['attempt'],r
        if r['kind']!='radar':
            assert float(q['latitude'][0])==o['lat'] and float(q['longitude'][0])==o['lon']
        if r['kind']=='weather':
            assert q['timezone']==[o['requestZone']]
            assert q['temperature_unit']==['fahrenheit' if o['units']=='f' else 'celsius']
        a=o['attempt'];timer=a['timer']
        assert a['operationId']==o['operationId']
        assert len([e for e in t['timerLog'] if e['operation']=='start' and e['id']==timer])==1
        assert timer not in t['activeTimers'],('request timer survived final checkpoint',timer)
        owners.append({k:o[k] for k in ('generation','operationId','kind','requestedDay','lat','lon','method','school','units','requestZone','cacheKey','weatherCacheKey')})
    checks.append('request-url-owner-attempt-and-final-timer-cleanup')
    stages={s['checkpoint']:s for s in t['snapshots'] if s.get('checkpoint')}
    if c.get('variant')=='no-abort':
        assert all(o['attempt']['aborted'] is None for r in t['requests'] for o in r['owner'].values() if o and o.get('attempt'))
        assert not any(e['type'].endswith('-abort') for e in t['events'])
        checks.append('ownership-without-owner-abort')
    if 'radar-' in c['caseId']:
        requests=[r for r in t['nativeImageReceipts'] if r['stage']=='native-image-request']
        b=[r for r in requests if r['rule']=='IB'];assert len(b)==1 and '/fixture-radar-B/256/6/32/26/2/1_1.png' in b[0]['url']
        if c['caseId'].endswith('manifest'):
            assert not [r for r in requests if r['rule']=='IA'],'obsolete manifest launched Image'
        else:
            a=[r for r in requests if r['rule']=='IA'];assert len(a)==1 and '/256/6/37/32/' in a[0]['url']
            stale=[i for i in stages['B-after-A']['imageStates'] if 'fixture-radar-A' in i['src']]
            assert len(stale)==1 and stale[0]['complete'] and stale[0]['naturalWidth']==256 and stale[0]['naturalHeight']==256
            assert not stale[0]['onloadPresent'] and not stale[0]['onerrorPresent'],'obsolete native handlers retained'
        pending=stages['B-after-A']['slots']['radar'];assert pending['lat']==30 and pending['lon']==0 and pending['generation']==1
        timer=pending['attempt']['timer'];assert timer not in t['activeTimers']
        final=stages['B-radar'];assert final['slots']['radar'] is None
        loaded=[i for i in t['imageEvents'] if i['event']=='load' and 'fixture-radar-B' in i['src']]
        assert len(loaded)==1 and loaded[0]['naturalWidth']==256 and loaded[0]['naturalHeight']==256
        assert final['weatherRadar']['quantitativeAuthority']=='unavailable (uncalibrated palette/alpha)'
        checks.extend(['exact-B-tile-zero-axis','native-256x256-image','stale-image-or-manifest-no-effect','image-owner-timer-cleanup','no-quantitative-radar-authority'])
    if c.get('cacheSeedsFromCase'):
        seeds={x['key']:x['value'] for x in c['cacheSeeds']};after={x['key']:x['value'] for x in t['storage']}
        assert set(seeds)==set(c['cacheSeedKeys']) and seeds==after,'reload changed seed bytes'
        assert all('24.47' not in e.get('key','') for e in t['storageLog']),'old A storage accessed'
        assert not [e for e in t['storageLog'] if e['operation'] in ('set','remove','clear') and not e.get('key','').startswith('salah_config_probe_')],'reload wrote storage'
        checks.append('winner-only-normal-reload-exact-bytes-no-A-access')
    for s in stages.values():
        rect=s['dom']['.c']['geometry'];assert rect['width']==325 and rect['height']==530
    return {'caseId':c['caseId'],'status':'EXPECTED_MUTANT_REJECTED' if c.get('expectedFailure') else 'PASS_RAW_CONSUMER_CHECKS',
        'checks':checks,'traceSha256':sha(folder/'trace.json'),'caseSha256':sha(folder/'case-input.json'),
        'observedSha256':h['observed'],'sourceSha256':h['source'],'sourceAssociation':association,'capturedOwners':owners,
        'firstStillMismatches':t.get('captureMismatches',[]),'visualDisposition':'INDEPENDENT_ORIGINAL_PIXELS_REQUIRED'}

def main():
    p=argparse.ArgumentParser();p.add_argument('roots',nargs='+',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    rows=[]
    for root in a.roots:
        for path in sorted(root.glob('*/trace.json')):
            try:rows.append(check(path.parent))
            except Exception as e:rows.append({'caseId':path.parent.name,'status':'FAIL_OFFLINE_CHECK','error':repr(e),'traceSha256':sha(path)})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps({'schema':'r0003-offline-consumer-checks/v1','rows':rows},indent=2)+'\n',encoding='utf-8')
    print(json.dumps([(r['caseId'],r['status'],r.get('error')) for r in rows]));return int(any(r['status']=='FAIL_OFFLINE_CHECK' for r in rows))
if __name__=='__main__':raise SystemExit(main())
