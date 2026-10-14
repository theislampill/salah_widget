"""Read-only R0004 native trace assertions; original-video pixel review is separate."""
import argparse
import datetime
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

KEY = 'salah:35.68|139.69|America/New_York|2|0'
PRAYERS = ('Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha')
CLOCKS = ['05:00', '06:00', '12:00', '15:30', '18:00', '19:30']

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def checkpoint(trace, name):
    rows = [s for s in trace['checkpointSnapshots'] if s.get('checkpoint') == name]
    require(len(rows) == 1, 'missing/duplicate checkpoint ' + name)
    return rows[0]

def request_owner(request):
    day = urlparse(request['url']).path.split('/')[-1]
    owners = [o for k, o in request['owner'].items() if k in ('current', 'prefetch')
              and o and o.get('attempt') and o['attempt']['requestedDay'] == day]
    require(len(owners) == 1, 'ambiguous request owner')
    return owners[0]

def audit(trace, case):
    cid = case['caseId']
    require(trace['caseId'] == cid, 'wrong case identity')
    require(trace['status'] in ('PASS_ASSERTIONS_PENDING_PIXEL_REVIEW',
                                'PARTIAL_FIRST_PRESENTATION_REVIEW_REQUIRED'),
            'native acquisition failed: ' + str(trace.get('failure')))
    require(not trace['unexpected'] and not trace['pageErrors'], 'unmatched ingress or page error')
    rows = [s for s in trace['snapshots'] if s['stage'] == 'render-completed' and not s.get('checkpoint')]
    require(rows and [s['renderOrdinal'] for s in rows] == list(range(1, len(rows)+1)),
            'original earlier render missing or duplicated')
    current = [s for s in rows if s.get('currentDay') and not s['flags']['prayerStale']]
    for s in rows:
        require(s['dom']['.c']['geometry']['width'] == 325 and
                s['dom']['.c']['geometry']['height'] == 530, 'card size drift')
        html = s['dom']['.times']['html']
        require(all(html.count('data-prayer-key="'+p+'"') == 1 for p in PRAYERS), 'six rows missing')
        require(not any(x in html for x in ('NaN', 'Infinity', 'undefined')), 'invalid clock precision')
        if not s.get('currentDay'):
            require(html.count('<span class="tm">—</span>') == 6, 'unavailable rows invented clocks')
            continue
        # The controlled instants are in September 2026: Tokyo +09, New York -04.
        # General DST/civil-boundary qualification stays in the original source suite.
        zone = s['timezone']
        require(zone in ('Asia/Tokyo', 'America/New_York'), 'untrusted zone adopted')
        offset = 9 if zone == 'Asia/Tokyo' else -4
        civil = datetime.datetime.fromtimestamp(s['wallUtcMs']/1000, datetime.timezone.utc)
        civil += datetime.timedelta(hours=offset)
        day = civil.strftime('%d-%m-%Y')
        require(s['currentDay'] == day and not s['flags']['prayerStale'], 'false-current timetable')
        require(s['today']['date']['gregorian']['date'] == day and s['today']['meta']['timezone'] == zone,
                'current state identity differs from resolved day')
        require(s['render']['timetableDate'] == day and s['render']['zone'] == zone,
                'completed render differs from accepted identity')
        require(re.findall(r'<span class="tm">([^<]*)</span>', html) == CLOCKS,
                'actual six clocks differ from controlled input')
        require(civil.strftime('%Y-%m-%d') in s['dom']['#ce']['text'], 'wrong Gregorian footer')
        require(s['dateTruth']['loadedGregorianDay'] == day and s['dateTruth']['timezone'] == zone,
                'date presentation identity drift')
        require(s['dom']['.arc']['tagName'] == 'svg' and '<path' in s['dom']['.arc']['html'],
                'actual prayer arc missing')

    requests = [r for r in trace['requests'] if r['kind'] == 'prayer']
    operations = {}
    for r in requests:
        op = request_owner(r)
        group = operations.setdefault(op['operationId'], {'kind': op['kind'], 'requests': [], 'generation': op['generation']})
        group['requests'].append(r)
        timer = op['attempt']['timer']
        starts = [t for t in trace['timerLog'] if t['operation'] == 'start' and t['id'] == timer]
        require(len(starts) == 1 and starts[0]['ms'] == 10000, 'native prayer deadline altered')
        require(timer not in trace['activeTimers'], 'owned attempt timer not settled')
        require(op['attempt']['operationId'] == op['operationId'], 'attempt ownership mismatch')
    for group in operations.values():
        days = [urlparse(r['url']).path.split('/')[-1] for r in group['requests']]
        require(len(days) <= 3, 'operation exceeded shared three-attempt budget')
        require(len(set(days)) <= (2 if group['kind'] == 'current' else 1), 'extra corrected current-day request')
    writes = [s for s in trace['storageLog'] if s['operation'] == 'set' and s['key'].startswith('salah:')]
    require(not any(s['operation'] == 'clear' or s['operation'] == 'remove' and
                    s.get('key', '').startswith('salah:') for s in trace['storageLog']), 'legacy cache removed')
    reads = [s['key'] for s in trace['storageLog'] if s['operation'] == 'get' and s['key'].startswith('salah:')]
    explicit = 'tz=Asia%2FTokyo' in case['hash']
    selected = KEY.replace('America/New_York', 'Asia/Tokyo') if explicit else KEY
    if 'held-settings' not in cid:
        require(reads and set(reads) == {selected}, 'unselected cache read')
        require(all(s['key'] == selected for s in writes), 'cache migrated to another key')
    if case.get('offline'):
        require(trace['storage'] == case['cacheSeeds'], 'offline legacy bytes changed')
        require(not writes, 'offline cache written')

    unavailable = cid.endswith(('cache-wrong', 'cache-zone-free', 'mutant-early-filter', 'mutant-day-check'))
    require(bool(current) != unavailable, 'expected first-current availability missing or fabricated')
    if current:
        first = current[0]
        expected_day = '09-09-2026' if cid.endswith('held-midnight') else ('07-09-2026' if cid.endswith(('omitted-zone12', 'held-settings')) else '08-09-2026')
        require(first['currentDay'] == expected_day, 'first accepted current timetable wrong')
        require(all(not s.get('currentDay') for s in rows if s['renderOrdinal'] < first['renderOrdinal']),
                'earlier current paint hidden by eventual correction')
    if 'bootstrap' in [r['id'] for r in case['responseRules']]:
        bootstrap = [r for r in requests if r['rule'] == 'bootstrap']
        corrected = [r for r in requests if r['rule'] == 'corrected']
        require(len(bootstrap) == len(corrected) == 1, 'bootstrap/correction count wrong')
        require(request_owner(bootstrap[0])['operationId'] == request_owner(corrected[0])['operationId'],
                'correction escaped original operation')
        known = checkpoint(trace, 'zone-known')
        require(known['timezone'] == 'Asia/Tokyo' and known['currentDay'] is None, 'zone discovery painted wrong day')
        require(known['dom']['.times']['html'].count('<span class="tm">—</span>') == 6,
                'zone-known stage shows bootstrap clocks')
        correction_release = next(e for e in trace['events'] if e['type'] == 'release' and e['key'] == 'corrected:1')
        if not cid.endswith('held-settings'):
            require(not any(s.get('currentDay') for s in rows if s['realElapsedMs'] < correction_release['realElapsedMs']),
                    'current painted before corrected response release')
    if cid.endswith(('explicit-zone22', 'omitted-zone12')):
        current_requests = [r for r in requests if request_owner(r)['kind'] == 'current']
        require(len(current_requests) == 1, 'unnecessary correction in direct/same-day control')
    if cid.endswith('cache-wrong'):
        require(checkpoint(trace, 'offline-settled')['timezone'] == 'Asia/Tokyo', 'valid wrong-day metadata lost')
        require(all('/08-09-2026?' in r['url'] for r in requests), 'wrong cached metadata request day')
    if cid.endswith('cache-zone-free'):
        require(checkpoint(trace, 'offline-settled')['timezone'] == 'America/New_York', 'zone-free cache trusted')
    if 'cache-' in cid and any(x in cid for x in ('broken-json', 'null-timings', 'invalid-zone', 'envelope-date')):
        loading = checkpoint(trace, 'loading')
        require(loading['timezone'] == 'America/New_York' and loading['currentDay'] is None, 'corrupt cache trusted')
    if '-ingress-' in cid:
        rejected = checkpoint(trace, 'invalid-rejected')
        require(rejected['timezone'] == 'America/New_York' and rejected['currentDay'] is None, 'hostile provider trusted')
        require(not any(w['realElapsedMs'] < rejected['realElapsedMs'] for w in writes), 'hostile provider persisted')
    if cid.endswith('held-midnight'):
        late = checkpoint(trace, 'after-late')
        require(late['currentDay'] is None and late['slots']['current'] is None, 'late correction kept current/busy')
        original = request_owner(next(r for r in requests if r['rule'] == 'bootstrap'))
        recovery = next(r for r in requests if r['rule'] == 'recovery')
        require(request_owner(recovery)['operationId'] != original['operationId'], 'recovery mistaken for extra correction')
        fence = next(r for r in requests if r['rule'] == 'bootstrap')['cooldown']['current']['nextTry']
        require(trace['startedPerformance'] + recovery['realElapsedMs'] >= fence, 'recovery started before native cooldown')
    if cid.endswith('held-settings'):
        before, after = checkpoint(trace, 'B-before-old'), checkpoint(trace, 'B-after-old')
        for field in ('timezone', 'runtimeGeneration', 'today', 'tomorrow'):
            require(before[field] == after[field], 'obsolete A overwrote B '+field)
        require(after['runtimeGeneration'] > checkpoint(trace, 'zone-known')['runtimeGeneration'], 'no actual settings generation change')
        require(not any(w['key'] == KEY for w in writes), 'obsolete A wrote its legacy cache')
        require(all(w['key'] == 'salah:40.71|-74.01|America/New_York|2|0' for w in writes), 'B cache ownership wrong')
        require(any(e['type'] == 'body-abort' and e['ignoreAbort'] for e in trace['events']), 'race did not retain late A completion')
    return {'caseId': cid, 'status': 'PASS_TRACE_ASSERTIONS_PIXEL_REVIEW_SEPARATE',
            'originalRenders': len(rows), 'firstCurrentOrdinal': current[0]['renderOrdinal'] if current else None,
            'firstCurrentDay': current[0]['currentDay'] if current else None,
            'currentOperations': {str(k): {'kind': g['kind'], 'generation': g['generation'],
                'days': [urlparse(r['url']).path.split('/')[-1] for r in g['requests']]}
                for k, g in operations.items()}, 'cacheReadKeys': sorted(set(reads)), 'cacheWrites': len(writes),
            'rawNativeStatus': trace['status'], 'mutationControl': case.get('mutationControl', False)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    results = []
    for path in sorted(args.input.glob('*/trace.json')):
        trace = json.loads(path.read_bytes())
        case = json.loads((path.parent/'case-input.json').read_bytes())
        result = audit(trace, case)
        result['traceSha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        results.append(result)
    require(results, 'no trace input')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps({'status': 'PASS_TRACES_ONLY', 'results': results}, indent=2)+'\n').encode())
    print(json.dumps({'status': 'PASS_TRACES_ONLY', 'cases': len(results)}))

if __name__ == '__main__':
    main()
