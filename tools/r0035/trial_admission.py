"""Qualification of a measured native interval. Missing observations cannot pass."""
import math
import re
from urllib.parse import parse_qs


def producer_flags(label, raw, reconstructed, allowed=None):
    flags=parse_qs(raw.lstrip('&'),keep_blank_values=True,strict_parsing=True)
    if any(len(values)!=1 or not values[0] for values in flags.values()):
        raise ValueError('Duplicate or empty producer flag')
    values={k:v[0] for k,v in flags.items()}
    if label=='main':
        if values: raise ValueError('Main accepts no arm flags')
        return values
    if not reconstructed:
        if any(not re.fullmatch(r'r35[A-Za-z0-9_]+',k) or v not in (allowed or {}).get(k,[]) for k,v in values.items()):
            raise ValueError('Historical flags need explicitly enumerated producer-only r35 options')
        return values
    enums={'r35arm':{'full','changed'},'r35scope':{'all','preview-members'},'r35amplitude':{'1','2','3','4'},
           'r35tile':{'8','16','32','64','128','530'},'r35guard':{'on','off'}}
    required={'r35arm','r35scope','r35amplitude','r35glass','r35margin'}
    if not required<=values.keys() or values.keys()-required-{'r35tile','r35guard'} or any(k in values and values[k] not in opts for k,opts in enums.items()):
        raise ValueError('Missing or invalid reconstruction flag')
    if any(not re.fullmatch(r'(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?',values[k]) for k in ('r35glass','r35margin')):
        raise ValueError('Invalid numeric producer flag')
    glass,margin=float(values['r35glass']),float(values['r35margin'])
    if not 0<=glass<=1 or not math.isfinite(margin) or margin<0:
        raise ValueError('Invalid glass controls')
    return values


def max_gap(times,start,end):
    edges=[start,*times,end]
    if any(b<a for a,b in zip(edges,edges[1:])): return float('inf')
    return max(b-a for a,b in zip(edges,edges[1:]))


def scene_ok(s,scene,limits,motion,clock,probe):
    def inside(b):
        return bool(b and len(b)==4 and b[2]>0 and b[3]>0 and b[0]>=-1 and b[1]>=-1
                    and b[0]+b[2]<=326 and b[1]+b[3]<=531)
    phase={'crescent':.08,'half':.5,'gibbous':.9,'full':.99}.get(scene)
    moon=s.get('calendarMoon') or {}
    alpha=s.get('cloudAlpha')
    return (s['composed'] and s['identity'] and not s['paused'] and s['reduced']==(motion=='reduced')
        and s['rate']==1 and s['clock']=={'wall':clock=='ordinary','advancing':clock=='simulation',
            'preview':clock=='simulation','fast':clock=='simulation','chrome':clock=='simulation'}
        and abs(s['utcMs']-s['expectedUtc'])<=100 and s['sunAlt'] is not None and limits[0]<s['sunAlt']<limits[1]
        and s['dimensions']==[325,530] and all(inside(s[k]) for k in ['header','footer','buckle'])
        and s['prayerKeys']==['Fajr','Sunrise','Dhuhr','Asr','Maghrib','Isha'] and s['prayersReady']
        and len(s['rowBoxes'])==6 and all(inside(b) for b in s['rowBoxes'])
        and s['cloudCurrent'] and s['cloudPublication']=='eligible-published'
        and (s['fixtureWx']['cloud'],s['fixtureWx']['code'])==((50,2) if scene=='broken' else (0,0))
        and s['catalogue'] and s['cloudSource'] in ('visible','hidden') and alpha is not None
        and (alpha>0 if scene=='broken' else alpha==0)
        and (scene!='moonlit' or (s.get('realMoon') or {}).get('altDeg',-90)>0 and moon.get('physicalMoonVisible'))
        and (phase is None or moon.get('calendarMoonVisible') and abs(moon.get('phaseFraction',-1)-phase)<=.002)
        and (not probe or s.get('predicate') is None or s['predicate']==probe['equals']))


def assess(before,after,trace,publication,scene,limits,motion,clock,probe,label,active):
    start,end=trace['start'],trace['end']
    samples=[before,*trace['states'],after]
    reasons=[];missing=[]
    if end<=start or not trace['frames']: missing.append('no measured frame interval')
    if not all(scene_ok(s,scene,limits,motion,clock,probe) for s in samples): reasons.append('scene, chrome, prayer, clock or predicate')
    if len({s['identity'] for s in samples})!=1: reasons.append('scene identity changed')
    if not trace['states'] or max_gap([s['t'] for s in trace['states']],start,end)>1250: missing.append('interior scene coverage')
    deliveries=[];changed=[];events=[]
    delivery='indeterminate' if label!='main' and active else 'not applicable'
    encoded='indeterminate' if label!='main' else 'not applicable'
    nonempty_count=None
    if label!='main':
        if not publication or not {'events','start','end','overflow','initial'}<=publication.keys() or publication['overflow']: missing.append('missing or truncated publication history')
        else:
            covered=publication['start']<=start<end<=publication['end']
            if not covered: missing.append('publication interval coverage')
            events=[e for e in publication['events'] if start<=e['at']<=end]
            deliveries=[e for e in events if e['kind']=='publication']
            encoded_known=all(isinstance(e.get('nonempty'),bool) and isinstance(e.get('changed'),bool) for e in deliveries)
            if encoded_known:
                changed=[e for e in deliveries if e['changed']]
                nonempty_count=sum(e['nonempty'] for e in deliveries)
                if covered and deliveries:
                    encoded=('no observed transitions' if not changed else
                             'at least 10 Hz' if max_gap([e['at'] for e in changed],start,end)<=100 else 'below 10 Hz')
            else:
                missing.append('missing presented pixel state')
            initial=publication['initial']
            if initial['tier']!='refined' or initial['identity']!=before['identity']: reasons.append('initial tier or identity')
            if any(e['tier']!='refined' or e['identity']!=before['identity'] for e in events if e['kind'] in ('owner','publication')):
                reasons.append('wrong tier or identity')
            if any(e['kind']=='withdraw' for e in events): reasons.append('owner withdrew')
            if active:
                if initial['status']!='active': reasons.append('initial producer status')
                if any(e['kind']=='status' and e['reason'] not in
                       ('active','prepared','preparing accepted frame','no encoded stellar change') for e in events):
                    reasons.append('suspension or invalidation')
                cadence_failures=[]
                if any(not 0<=e['ageMs']<=100 or not math.isfinite(e['utcMs']) for e in deliveries): cadence_failures.append('invalid delivered sample')
                if any(b['utcMs']<=a['utcMs'] or abs((b['utcMs']-a['utcMs'])-(b['at']-a['at']))>100
                       for a,b in zip(deliveries,deliveries[1:])): cadence_failures.append('discontinuous accepted sample clock')
                if covered and (not deliveries or max_gap([e['at'] for e in deliveries],start,end)>100):
                    cadence_failures.append('publication cadence below 10 Hz')
                delivery='failed' if cadence_failures else 'passed' if covered else 'indeterminate'
                reasons.extend(cadence_failures)
            elif deliveries or any(e['kind']=='status' and e['reason']=='active' for e in events):
                reasons.append('inactive control delivered stellar output')
    if probe and any(s.get('predicate') is None for s in samples): missing.append('missing producer predicate')
    handoffs=[b['at']-a['at'] for a,b in zip(deliveries,deliveries[1:]) if a['epoch']!=b['epoch']]
    status_events=[e for e in events if e['kind']=='status']
    suspended=sum(nxt-e['at'] for e,nxt in zip(status_events,[x['at'] for x in status_events[1:]]+[end])
                  if e['reason']=='performance guard suspended')
    return {'verdict':'failed' if reasons else 'indeterminate' if missing else 'passed','failures':reasons,'missing':missing,
            'deliveryCadence':delivery,'encodedChangeCadence':encoded,'nonemptyPublicationCount':nonempty_count,
            'pixelEvidence':('encoded variation observed' if encoded in ('at least 10 Hz','below 10 Hz') else
                             'no encoded variation demonstrated' if encoded=='no observed transitions' else 'unavailable'),
            'publicationCount':len(deliveries),'changedCount':len(changed),'maxPublicationGapMs':max_gap([e['at'] for e in deliveries],start,end) if deliveries else None,
            'maxChangedGapMs':max_gap([e['at'] for e in changed],start,end) if changed else None,
            'handoffGapsMs':handoffs,'guardSuspendedMs':suspended,'maxAgeMs':max((e['ageMs'] for e in deliveries),default=None),
            'eventCount':len(events),'humanVisualVerdict':None}
