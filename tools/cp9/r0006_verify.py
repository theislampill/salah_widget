"""Read-only checks of R0006 native traces. Native pixels require separate review."""
import argparse, copy, gzip, hashlib, json, lzma, re
from pathlib import Path
from urllib.parse import urlparse

PRAYERS = ('Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha')
CLOCKS = ['05:00', '06:00', '12:00', '15:30', '18:00', '19:30']
def require(value, why):
    if not value: raise AssertionError(why)

def checkpoint(t, name):
    rows = [s for s in t['checkpointSnapshots'] if s.get('checkpoint') == name]
    require(len(rows) == 1, 'missing/duplicate checkpoint '+name)
    return rows[0]

def owner(r):
    day = urlparse(r['url']).path.split('/')[-1]
    ops = [o for k, o in r['owner'].items() if k in ('current','prefetch') and o
           and o.get('attempt') and o['attempt']['requestedDay'] == day]
    require(len(ops) == 1, 'request ownership ambiguous')
    return ops[0]

def audit(t, c):
    name = c['caseId']; require(t['caseId'] == name, 'case mismatch')
    require(t['status'] in ('PASS_ASSERTIONS_PENDING_PIXEL_REVIEW','PARTIAL_FIRST_PRESENTATION_REVIEW_REQUIRED'), 'native acquisition failed')
    require(not t['unexpected'] and not t['pageErrors'], 'unmatched request or native page error')
    require(not any(e['type'] in ('error','unhandledrejection') for e in t['events']), 'unhandled native error')
    rows = [s for s in t['snapshots'] if s['stage'] == 'render-completed' and not s.get('checkpoint')]
    require(rows and [s['renderOrdinal'] for s in rows] == list(range(1,len(rows)+1)), 'missing original completed renders')
    clock={'TIMESCALE':1,'FOLLOW_WALL_CLOCK':True,'ADVANCING':False}
    if name=='R0006-frozen-recovery':clock={'TIMESCALE':0,'FOLLOW_WALL_CLOCK':False,'ADVANCING':False}
    if name=='R0006-accelerated-recovery':clock={'TIMESCALE':120,'FOLLOW_WALL_CLOCK':False,'ADVANCING':True}
    require(all(s['clock']==clock for s in rows),'original clock mode changed')
    require(not t['pending'],'held provider responses not settled')
    if c.get('jsonTraceTransport'):
        require(t['traceTransport']['snapshotCount']==len(t['snapshots'])-len(t['checkpointSnapshots']),'sealed snapshot export incomplete')
    current = [s for s in rows if s.get('currentDay') and not s['flags']['prayerStale']]
    require(current, 'no actual recovered current render')
    for s in rows:
        html = s['dom']['.times']['html']
        require(all(html.count('data-prayer-key="'+p+'"') == 1 for p in PRAYERS), 'six rows absent')
        require(not any(x in html for x in ('NaN','Infinity','undefined')), 'invalid prayer precision')
        clocks = re.findall(r'<span class="tm">([^<]*)</span>', html)
        if not s.get('currentDay'):
            require(clocks == ['—']*6, 'unavailable output fabricated a clock')
        elif not s['flags']['prayerStale']:
            require(clocks == [s['today']['timings'][p] for p in PRAYERS], 'rendered clocks differ from accepted data')
            if name != 'R0006-cache-denied': require(clocks == CLOCKS, 'hostile or unrelated timetable painted')
            require(s['dom']['.arc']['tagName'] == 'svg' and '<path' in s['dom']['.arc']['html'], 'arc absent')
            require(s['render']['timetableDate'] == s['currentDay'], 'render date disagrees with current')
    for s in t['checkpointSnapshots']:
        if s['visibility']['paused']: continue
        require(s['dom']['.c']['geometry']['width'] == 325 and s['dom']['.c']['geometry']['height'] == 530, 'card dimensions drift')
    requests = [r for r in t['requests'] if r['kind'] == 'prayer']
    operations = {}; attempts = []
    for r in requests:
        op = owner(r); a = op['attempt']; tid = a['timer']
        starts = [x for x in t['timerLog'] if x['operation'] == 'start' and x['id'] == tid]
        ends = [x for x in t['timerLog'] if x['operation'] in ('fire','clear') and x['id'] == tid]
        require(len(starts) == 1 and starts[0]['ms'] == 10000, 'full asynchronous deadline changed')
        require(ends and tid not in t['activeTimers'], 'owned timer survived settlement')
        require(a['operationId'] == op['operationId'], 'attempt belongs to another operation')
        group = operations.setdefault(op['operationId'], {'kind':op['kind'],'generation':op['generation'],'requests':[]})
        group['requests'].append(r)
        fired = next((x for x in ends if x['operation']=='fire'),None)
        actual = fired['realElapsedMs']-starts[0]['realElapsedMs'] if fired else None
        if fired: require(actual >= 9990, 'native deadline fired early beyond timer granularity')
        attempts.append({'requestSerial':r['serial'],'operationId':op['operationId'],'kind':op['kind'],'attemptId':a['attemptId'],'prayerAttempts':op['prayerAttempts'],
          'day':a['requestedDay'],'requestElapsedMs':r['realElapsedMs'],'timer':tid,'nominalDeadlineMs':10000,
          'timerStartMs':starts[0]['realElapsedMs'],'timerFireMs':fired['realElapsedMs'] if fired else None,
          'actualTimerDelayMs':actual,'timerSchedulingDelayMs':actual-10000 if fired else None})
    backoffs=[]
    for opid, group in operations.items():
        rs=group['requests']; require(len(rs)<=3,'more than three attempts in an operation')
        for i,(a,b) in enumerate(zip(rs,rs[1:]),1):
            starts=[x for x in t['timerLog'] if x['operation']=='start' and x['ms']==900*i and a['realElapsedMs']<=x['realElapsedMs']<=b['realElapsedMs']]
            # Concurrent current/prefetch retries share the fixture's timer log;
            # it does not label backoff owners. Preserve all qualifying receipts
            # rather than inventing a unique association from timing proximity.
            candidates=[]
            for start in starts:
                fired=[x for x in t['timerLog'] if x['operation']=='fire' and x['id']==start['id'] and x['realElapsedMs']<=b['realElapsedMs']]
                if len(fired)==1:
                    delay=fired[0]['realElapsedMs']-start['realElapsedMs']
                    require(delay>=900*i-10,'backoff fired early')
                    candidates.append({'timer':start['id'],'actualMs':delay,'schedulingDelayMs':delay-900*i})
            require(candidates,'backoff absent or did not complete natively')
            require(len(candidates)==1 or name=='R0006-cache-offline','backoff association ambiguous outside concurrent-cache control')
            require(b['realElapsedMs']-a['realElapsedMs']>=900*i-10,'attempt started before backoff interval')
            backoffs.append({'operationId':opid,'nominalMs':900*i,'association':'unique' if len(candidates)==1 else 'concurrent candidates; no unique owner assertion','candidates':candidates})
    cr=[r for r in requests if owner(r)['kind']=='current' and owner(r)['attempt']['requestedDay']=='07-09-2026']
    recovery=None
    if name in ('R0006-cold-body','R0006-hidden-resume','R0006-frozen-recovery','R0006-accelerated-recovery'):
        require(len(cr)==4,'cold recovery needs exactly four current-day attempts')
        ids=[owner(r)['operationId'] for r in cr]
        require(len(set(ids[:3]))==1 and ids[3]!=ids[0],'attempt/operation conflation')
        fence=cr[0]['cooldown']['current']['nextTry']-t['startedPerformance']
        require(cr[3]['realElapsedMs']>=fence,'recovery before operation-start cooldown')
        restore=[e for e in t['events'] if e['type']=='rule-change' and e['id']=='next-current']
        require(len(restore)==1 and restore[0]['realElapsedMs']<fence,'network restored after eligibility fence')
        require(current[0]['realElapsedMs']>=cr[3]['realElapsedMs'],'recovery painted before healthy response')
        require(all(s['currentDay']=='07-09-2026' for s in current),'recovery required day rollover')
        dead=checkpoint(t,'unavailable');require(dead['slots']['current'] is None and dead['currentDay'] is None,'exhausted current slot stuck')
        owned={owner(r)['attempt']['timer'] for r in cr[:3]}
        for tid in owned:
            require(any(x['id']==tid and x['operation']=='clear' and x['realElapsedMs']<=dead['realElapsedMs'] for x in t['timerLog']),'abandoned attempt timer not cleared before unavailable')
        recovery={'operationStartElapsedMs':fence-60000,'eligibleElapsedMs':fence,'fourthCurrentRequestMs':cr[3]['realElapsedMs'],
          'firstRecoveredRenderMs':current[0]['realElapsedMs'],'eligibleToRequestMs':cr[3]['realElapsedMs']-fence,'exhaustedCheckpointMs':dead['realElapsedMs'],
          'nominalAllTimeoutMs':32700 if name=='R0006-cold-body' else None,'firstRecoveredOrdinal':current[0]['renderOrdinal']}
        if name=='R0006-cold-body':
            for r in cr[:3]:
                key=r['rule']+':'+str(r['occurrence'])
                ev=[e for e in t['events'] if e.get('key')==key]
                require(any(e['type']=='headers' and e['status']==200 for e in ev) and any(e['type']=='json-start' for e in ev),'successful headers/unsettled json not exercised')
                fire=next((x for x in t['timerLog'] if x['id']==owner(r)['attempt']['timer'] and x['operation']=='fire'),None)
                require(fire and not any(e['type']=='json-settle' and e['realElapsedMs']<fire['realElapsedMs'] for e in ev),'body settled before deadline')
                require(any(e['type']=='body-abort' and e['ignoreAbort'] for e in ev),'late-body abort-ignoring control absent')
            before=checkpoint(t,'before-late');after=checkpoint(t,'after-late')
            for k in ('today','tomorrow','timezone','runtimeGeneration','slots','storageLogLength'):require(before[k]==after[k],'late body changed '+k)
            require(len([e for e in t['events'] if e['type']=='release' and e['key'].startswith('stalled:')])==3,'late bodies not released')
            recovery['actualThirdDeadlineElapsedMs']=next(a['timerFireMs'] for a in attempts if a['requestSerial']==cr[2]['serial'])-(fence-60000)
            recovery['allTimeoutSchedulingExcessMs']=recovery['actualThirdDeadlineElapsedMs']-32700
        if name=='R0006-hidden-resume':
            hidden=checkpoint(t,'hidden');end=checkpoint(t,'after-fence-hidden')
            require(hidden['visibility']['paused'] and end['visibility']['paused'] and hidden['realElapsedMs']<fence<=end['realElapsedMs'],'visibility boundary not crossed while paused')
            require(not any(hidden['realElapsedMs']<r['realElapsedMs']<end['realElapsedMs'] for r in requests),'background prayer request while paused')
            require(cr[3]['realElapsedMs']>=end['realElapsedMs'],'recovery before actual resumed opportunity')
            recovery['hiddenAtMs']=hidden['realElapsedMs'];recovery['hiddenAfterFenceMs']=end['realElapsedMs']
            if any(a['type']=='widgetOffscreen' for a in c['orderedActions']):
                require(hidden['visibility']['state']==end['visibility']['state']=='visible','document visibility was substituted for offscreen geometry')
                require(hidden['dom']['.c']['geometry']['y']>=570 and end['dom']['.c']['geometry']['y']>=570,'actual card not offscreen')
                require(checkpoint(t,'settled')['dom']['.c']['geometry']==dead['dom']['.c']['geometry'],'resumed card geometry not restored')
    if name in ('R0006-third-success','R0006-offline-entry'):
        require(len(cr)==3 and len({owner(r)['operationId'] for r in cr})==1,'third success started unnecessary operation')
    if name.startswith('R0006-cache-'):
        key=c['cacheSeeds'][0]['key'];original=c['cacheSeeds'][0]['value'];stored=next(s['value'] for s in t['storage'] if s['key']==key)
        require(stored==original,'selected valid cache bytes lost')
        # Boot may paint loading before selected-cache adoption. Once usable,
        # the cache must remain usable throughout refresh and write failure.
        require(all(s.get('currentDay')=='07-09-2026' for s in rows if s['renderOrdinal']>=current[0]['renderOrdinal']),'valid cache blanked during refresh')
        if name=='R0006-cache-denied':require(any(x['operation']=='set' and x['key']==key and x.get('denied') for x in t['storageLog']),'write-denial path not exercised')
        else:
            require(len(cr)==3,'failed cache refresh attempt count')
            network=t['nativeNetworkReceipts'];require(network,'offline route receipts absent')
            external=[r for r in network if urlparse(r['url']).hostname!='127.0.0.1']
            require(external and all(r['disposition']=='aborted-offline' and r['returned'] for r in external),'external network not actually blocked')
    if name=='R0006-tomorrow-promotion':
        before=checkpoint(t,'matching-tomorrow');after=checkpoint(t,'settled')
        require(before['realElapsedMs']>=65000 and before['tomorrowDay']=='08-09-2026','matching tomorrow not retained past cooldown')
        require(after['currentDay']=='08-09-2026' and after['tomorrowDay']=='09-09-2026','civil-day promotion failed')
        require(len(requests)==3 and [owner(r)['kind'] for r in requests]==['current','prefetch','prefetch'],'redundant current/tomorrow request')
    if name=='R0006-generation-late-cleanup':
        before=checkpoint(t,'B-owning');after=checkpoint(t,'B-after-old')
        require(before['slots']['current'] and before['slots']['current']['lat']==40.71,'B did not own current request')
        for k in ('slots','runtimeGeneration','today','storageLogLength'):require(before[k]==after[k],'old cleanup corrupted successor '+k)
        require(owner(requests[0])['generation']<before['runtimeGeneration'],'no actual generation change')
        require(checkpoint(t,'settled')['slots']['current'] is None,'B did not settle')
    return {'caseId':name,'status':'PASS_NATIVE_TRACE_PIXELS_SEPARATE','completedRenderCount':len(rows),'firstCurrentOrdinal':current[0]['renderOrdinal'],
      'lowLevelPrayerAttempts':len(requests),'highLevelOperations':len(operations),'currentOperations':sum(g['kind']=='current' for g in operations.values()),
      'prefetchOperations':sum(g['kind']=='prefetch' for g in operations.values()),'attempts':attempts,'backoffs':backoffs,'recovery':recovery,
      'retainedCaptureMismatches':t['captureMismatches']}

def negative_controls(t,c):
    results=[]
    def reject(name,change):
        mutant=copy.deepcopy(t);change(mutant)
        try:audit(mutant,c)
        except (AssertionError,KeyError,TypeError,StopIteration) as e:results.append({'name':name,'rejected':True,'reason':str(e)})
        else:raise AssertionError('false-green verifier mutant '+name)
    reject('missing-render',lambda m:m['snapshots'].pop(next(i for i,s in enumerate(m['snapshots']) if s['stage']=='render-completed')))
    prayer=next(r for r in t['requests'] if r['kind']=='prayer');tid=owner(prayer)['attempt']['timer']
    reject('unbounded-deadline',lambda m:next(x for x in m['timerLog'] if x['id']==tid and x['operation']=='start').update(ms=999999))
    reject('surviving-owned-timer',lambda m:m['activeTimers'].append(tid))
    reject('changed-clock-mode',lambda m:m['snapshots'][0]['clock'].update(TIMESCALE=999))
    if c['caseId']=='R0006-cold-body':
        reject('early-recovery',lambda m:[r for r in m['requests'] if r['kind']=='prayer' and owner(r)['kind']=='current'][3].update(realElapsedMs=59000))
        reject('headers-only',lambda m:m['timerLog'].__setitem__(slice(None),[x for x in m['timerLog'] if not(x['id']==tid and x['operation']=='fire')]))
        reject('late-cache-write',lambda m:checkpoint(m,'after-late').update(storageLogLength=9999))
    if c['caseId'].startswith('R0006-cache-'):
        reject('blank-after-cache-adoption',lambda m:next(s for s in reversed(m['snapshots']) if s['stage']=='render-completed' and not s.get('checkpoint')).update(currentDay=None))
    return results

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    results=[]
    for path in sorted([*args.input.glob('*/trace.json'),*args.input.glob('*/trace.json.gz'),*args.input.glob('*/trace.json.xz')]):
        data=path.read_bytes()
        if path.suffix=='.gz':data=gzip.decompress(data)
        if path.suffix=='.xz':data=lzma.decompress(data)
        t=json.loads(data);c=json.loads((path.parent/'case-input.json').read_bytes())
        try:result=audit(t,c);result['negativeControls']=negative_controls(t,c)
        except Exception as e:result={'caseId':c['caseId'],'status':'FAIL','reason':repr(e)}
        result['traceSha256']=hashlib.sha256(data).hexdigest();results.append(result)
    require(results,'no native traces')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps({'schema':'r0006-native-trace-review/v1','cases':results},indent=2)+'\n',encoding='utf8')
    for r in results:print(r['caseId'],r['status'],r.get('reason',''),r.get('recovery'))
    return int(any(r['status']=='FAIL' for r in results))
if __name__=='__main__':raise SystemExit(main())
