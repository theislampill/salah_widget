"""Independent bounded-memory, read-only R0006 trace reconciliation."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
PRAYERS = ('Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha')


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


class Reader:
    def __init__(self, path):
        self.stream = path.open('r', encoding='utf-8')
        self.buffer = ''
        self.pos = 0
        self.eof = False
        self.decoder = json.JSONDecoder()

    def fill(self):
        self.buffer = self.buffer[self.pos:]
        self.pos = 0
        part = self.stream.read(262144)
        self.buffer += part
        self.eof = not part

    def token(self, expected=None):
        while True:
            while self.pos < len(self.buffer) and self.buffer[self.pos].isspace():
                self.pos += 1
            if self.pos < len(self.buffer):
                break
            if self.eof:
                raise ValueError('unexpected end')
            self.fill()
        result = self.buffer[self.pos]
        if expected is not None:
            assert result == expected, (result, expected)
            self.pos += 1
        return result

    def value(self):
        self.token()
        while True:
            try:
                result, self.pos = self.decoder.raw_decode(self.buffer, self.pos)
                return result
            except json.JSONDecodeError:
                if self.eof:
                    raise
                self.fill()


def review(path):
    inputs = json.loads((path.parent / 'case-input.json').read_bytes())
    case = inputs['caseId']
    expected_clock = {'TIMESCALE': 1, 'FOLLOW_WALL_CLOCK': True, 'ADVANCING': False}
    if case == 'R0006-frozen-recovery':
        expected_clock = {'TIMESCALE': 0, 'FOLLOW_WALL_CLOCK': False, 'ADVANCING': False}
    elif case == 'R0006-accelerated-recovery':
        expected_clock = {'TIMESCALE': 120, 'FOLLOW_WALL_CLOCK': False, 'ADVANCING': True}
    raw = {}
    counts = Counter()
    errors = []
    first = None
    last = None
    first_cached = None
    checkpoints = {}
    min_elapsed = None
    max_elapsed = None
    current_dates = Counter()
    generation_values = set()
    all_snapshot_count = 0

    def check(ok, message):
        if not ok and message not in errors:
            errors.append(message)

    def snapshot(s):
        nonlocal all_snapshot_count, first, last, first_cached, min_elapsed, max_elapsed
        all_snapshot_count += 1
        counts[s['stage']] += 1
        generation_values.add(s['runtimeGeneration'])
        elapsed = s['realElapsedMs']
        min_elapsed = elapsed if min_elapsed is None else min(min_elapsed, elapsed)
        max_elapsed = elapsed if max_elapsed is None else max(max_elapsed, elapsed)
        if s.get('checkpoint'):
            checkpoints[s['checkpoint']] = s
            return
        if s['stage'] != 'render-completed':
            return
        counts['original-completed'] += 1
        ordinal = counts['original-completed']
        check(s['renderOrdinal'] == ordinal, 'non-consecutive completed render ordinal')
        check(s['clock'] == expected_clock, 'original clock mode differs')
        html = s['dom']['.times']['html']
        check(all(html.count('data-prayer-key="' + k + '"') == 1 for k in PRAYERS), 'missing or duplicate prayer row')
        check(not any(x in html for x in ('undefined', 'NaN', 'Infinity')), 'non-finite prayer output')
        clocks = re.findall(r'<span class="tm">([^<]*)</span>', html)
        usable = s.get('currentDay') and not s['flags']['prayerStale']
        if not s.get('currentDay'):
            check(clocks == ['—'] * 6, 'unavailable render invented prayer time')
        if usable:
            current_dates[s['currentDay']] += 1
            check(clocks == [s['today']['timings'][p] for p in PRAYERS], 'visible timetable differs from accepted provider data')
            check(s['render']['timetableDate'] == s['currentDay'], 'rendered date differs from adopted current date')
            check(s['dom']['.arc']['tagName'] == 'svg' and '<path' in s['dom']['.arc']['html'], 'current arc absent')
            if first is None:
                first = s
                first_cached = ordinal
        if case.startswith('R0006-cache-') and first_cached is not None:
            check(s.get('currentDay') == '07-09-2026' and not s['flags']['prayerStale'], 'cache blanked after usable adoption')
        for kind in ('current', 'prefetch'):
            owner = s['slots'].get(kind)
            if owner:
                check(owner['kind'] == kind and owner['generation'] == s['runtimeGeneration'], 'slot owner generation/kind mismatch')
        last = s

    reader = Reader(path)
    reader.token('{')
    while reader.token() != '}':
        key = reader.value()
        reader.token(':')
        if key == 'snapshots':
            reader.token('[')
            while reader.token() != ']':
                snapshot(reader.value())
                if reader.token() != ']':
                    reader.token(',')
            reader.token(']')
        else:
            raw[key] = reader.value()
        if reader.token() != '}':
            reader.token(',')
    reader.token('}')
    reader.stream.close()
    check(raw.get('caseId') == case, 'case identity differs')
    check(raw.get('status') in ('PASS_ASSERTIONS_PENDING_PIXEL_REVIEW', 'PARTIAL_FIRST_PRESENTATION_REVIEW_REQUIRED'), 'acquisition incomplete or failed')
    check(first is not None, 'no original completed current render')
    if 'rawOnFailure' in raw:
        return {'caseId': case, 'trace': str(path), 'traceSha256': sha(path), 'errors': errors, 'status': 'INCOMPLETE', 'failure': raw.get('failure')}
    check(not raw.get('pageErrors'), 'native page error')
    check(not raw.get('unexpected'), 'unexpected provider request')
    check(not raw.get('pending'), 'held response remained at observation cut')
    check(not any(e['type'] in ('error', 'unhandledrejection') for e in raw['events']), 'unhandled native event')
    if inputs.get('jsonTraceTransport'):
        check(raw['traceTransport']['snapshotCount'] == all_snapshot_count - len(raw['checkpointSnapshots']), 'sealed snapshot count differs')
    reqs = []
    for r in raw['requests']:
        if r['kind'] != 'prayer':
            continue
        day = urlparse(r['url']).path.split('/')[-1]
        owners = [r['owner'].get(k) for k in ('current', 'prefetch')]
        owners = [o for o in owners if o and o.get('attempt') and o['attempt']['requestedDay'] == day]
        check(len(owners) == 1, 'ambiguous request owner')
        if len(owners) != 1:
            continue
        o = owners[0]
        timer = o['attempt']['timer']
        starts = [e for e in raw['timerLog'] if e['id'] == timer and e['operation'] == 'start']
        ends = [e for e in raw['timerLog'] if e['id'] == timer and e['operation'] in ('fire', 'clear')]
        check(len(starts) == 1 and starts[0]['ms'] == 10000, 'attempt full-body deadline absent')
        check(bool(ends) and timer not in raw['activeTimers'], 'owned deadline timer survived')
        check(o['attempt']['operationId'] == o['operationId'], 'attempt/operation owner mismatch')
        reqs.append({'requestSerial': r['serial'], 'kind': o['kind'], 'operationId': o['operationId'], 'generation': o['generation'],
                     'prayerAttempts': o['prayerAttempts'], 'day': day, 'atMs': r['realElapsedMs'], 'timer': timer,
                     'deadlineStart': starts[0] if starts else None, 'deadlineEnds': ends,
                     'cooldown': r['cooldown']['current'], 'rule': r['rule'], 'occurrence': r['occurrence']})
    operations = Counter((r['generation'], r['operationId'], r['kind']) for r in reqs)
    check(all(c <= 3 for c in operations.values()), 'more than three attempts per operation')
    backoffs=[]
    for identity in operations:
        group=[r for r in reqs if (r['generation'],r['operationId'],r['kind'])==identity]
        for index,(a,b) in enumerate(zip(group,group[1:]),1):
            delay=900*index
            starts=[e for e in raw['timerLog'] if e['operation']=='start' and e['ms']==delay and a['atMs']<=e['realElapsedMs']<=b['atMs']]
            candidates=[]
            for start in starts:
                fires=[e for e in raw['timerLog'] if e['id']==start['id'] and e['operation']=='fire' and e['realElapsedMs']<=b['atMs']]
                if len(fires)==1:
                    actual=fires[0]['realElapsedMs']-start['realElapsedMs']
                    check(actual>=delay-10,'native backoff fired early')
                    candidates.append({'timer':start['id'],'actualDelayMs':actual})
            check(bool(candidates),'no native backoff completion between attempts')
            check(len(candidates)==1 or case=='R0006-cache-offline','ambiguous native backoff outside concurrent cache case')
            check(b['atMs']-a['atMs']>=delay-10,'next attempt before native backoff')
            backoffs.append({'operationId':identity[1],'nominalMs':delay,'candidates':candidates,
                             'uniqueAssociation':len(candidates)==1})
    current = [r for r in reqs if r['kind'] == 'current' and r['day'] == '07-09-2026']
    recovery = None
    if case in ('R0006-cold-body', 'R0006-hidden-resume', 'R0006-frozen-recovery', 'R0006-accelerated-recovery'):
        check(len(current) == 4, 'current-day attempts not exactly three exhausted plus one recovery')
        if len(current) == 4:
            fence = current[0]['cooldown']['nextTry'] - raw['startedPerformance']
            check(len({r['operationId'] for r in current[:3]}) == 1 and current[3]['operationId'] != current[0]['operationId'], 'recovery operation boundary differs')
            check(current[3]['atMs'] >= fence, 'request before native operation-start cooldown')
            check(first['realElapsedMs'] >= current[3]['atMs'], 'current render precedes healthy request')
            check(set(current_dates) == {'07-09-2026'}, 'same-day recovery date differs')
            check(not checkpoints['unavailable']['slots']['current'], 'exhausted owner slot survived')
            recovery = {'operationStartMs': fence - 60000, 'eligibleMs': fence, 'recoveryRequestMs': current[3]['atMs'],
                        'firstCompletedCurrentOrdinal': first['renderOrdinal'], 'firstCompletedCurrentMs': first['realElapsedMs']}
            if case == 'R0006-cold-body':
                for r in current[:3]:
                    events = [e for e in raw['events'] if e.get('key') == r['rule'] + ':' + str(r['occurrence'])]
                    check(any(e['type'] == 'headers' and e['status'] == 200 for e in events), 'no successful headers')
                    check(any(e['type'] == 'json-start' for e in events), 'body not awaited')
                    fires = [e for e in r['deadlineEnds'] if e['operation'] == 'fire']
                    check(len(fires) == 1, 'native full-body deadline did not fire')
                    if fires:
                        check(fires[0]['realElapsedMs'] - r['deadlineStart']['realElapsedMs'] >= 9990, 'native deadline fired prematurely')
                        check(not any(e['type'] == 'json-settle' and e['realElapsedMs'] < fires[0]['realElapsedMs'] for e in events), 'body settled before deadline')
                for key in ('today', 'tomorrow', 'timezone', 'runtimeGeneration', 'slots', 'storageLogLength'):
                    check(checkpoints['before-late'][key] == checkpoints['after-late'][key], 'late body changed ' + key)
            if case == 'R0006-hidden-resume':
                a, b = checkpoints['hidden'], checkpoints['after-fence-hidden']
                check(a['visibility']['paused'] and b['visibility']['paused'] and a['realElapsedMs'] < fence <= b['realElapsedMs'], 'hidden window did not straddle cooldown')
                check(not any(a['realElapsedMs'] < r['atMs'] < b['realElapsedMs'] for r in reqs), 'hidden request launched')
                check(current[3]['atMs'] >= b['realElapsedMs'], 'recovery before resume')
                if any(x['type']=='widgetOffscreen' for x in inputs['orderedActions']):
                    check(a['dom']['.c']['geometry']['y']==1200 and b['dom']['.c']['geometry']['y']==1200,'actual card not offscreen')
                    final=checkpoints['settled']['dom']['.c']['geometry']
                    check(final['x']==0 and final['y']==0 and final['width']==325 and final['height']==530,'original card geometry not restored')
    if case == 'R0006-generation-late-cleanup':
        a, b = checkpoints['B-owning'], checkpoints['B-after-old']
        for key in ('slots', 'runtimeGeneration', 'today', 'storageLogLength'):
            check(a[key] == b[key], 'late old generation changed successor ' + key)
        check(a['slots']['current']['lat'] == 40.71 and a['runtimeGeneration'] > reqs[0]['generation'], 'successor generation not exercised')
    if case == 'R0006-tomorrow-promotion':
        a, b = checkpoints['matching-tomorrow'], checkpoints['settled']
        check(a['realElapsedMs'] >= 65000 and a['tomorrowDay'] == '08-09-2026', 'matching tomorrow not retained past fence')
        check(b['currentDay'] == '08-09-2026' and b['tomorrowDay'] == '09-09-2026', 'day promotion absent')
        check([(r['kind'], r['day']) for r in reqs] == [('current', '07-09-2026'), ('prefetch', '08-09-2026'), ('prefetch', '09-09-2026')], 'redundant promotion acquisition')
    if case.startswith('R0006-cache-'):
        key, value = inputs['cacheSeeds'][0]['key'], inputs['cacheSeeds'][0]['value']
        check(next(x['value'] for x in raw['storage'] if x['key'] == key) == value, 'selected cache bytes changed')
        if case == 'R0006-cache-denied':
            check(any(e['operation'] == 'set' and e['key'] == key and e.get('denied') for e in raw['storageLog']), 'cache write not denied')
        else:
            external = [e for e in raw['nativeNetworkReceipts'] if urlparse(e['url']).hostname != '127.0.0.1']
            check(bool(external) and all(e['disposition'] == 'aborted-offline' and e['returned'] for e in external), 'offline transport not exercised')
    if case in ('R0006-third-success', 'R0006-offline-entry'):
        check(len(current) == 3 and len({r['operationId'] for r in current}) == 1, 'third success not within same budget')
    return {'caseId': case, 'trace': str(path), 'traceSha256': sha(path), 'traceBytes': path.stat().st_size,
            'caseInputSha256': sha(path.parent / 'case-input.json'), 'status': 'PASS_TRACE_ONLY' if not errors else 'FAIL', 'errors': errors,
            'snapshotCount': all_snapshot_count, 'counts': dict(counts), 'traceTransport': raw.get('traceTransport'),
            'expectedClock': expected_clock, 'generationValues': sorted(generation_values), 'currentDates': dict(current_dates),
            'firstCurrent': {'ordinal': first['renderOrdinal'], 'elapsedMs': first['realElapsedMs'], 'clock': first['clock']} if first else None,
            'snapshotElapsedRangeMs': [min_elapsed, max_elapsed], 'checkpointNames': sorted(checkpoints),
            'requestCount': len(reqs), 'requests': reqs, 'operationAttemptCounts': [{'generation': k[0], 'operationId': k[1], 'kind': k[2], 'attempts': v} for k,v in operations.items()],
            'recovery': recovery, 'backoffs':backoffs, 'captureMismatches': raw['captureMismatches'],
            'limits': ['Native trace only; original video pixels reviewed separately.', 'No unique render ordinal to native frame association is inferred.', 'Concurrent cache backoff owner association remains observationally ambiguous.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('traces', type=Path, nargs='+')
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    reports = []
    for path in args.traces:
        report = review(path)
        reports.append(report)
        print(report['caseId'], report['status'], report.get('counts'), report.get('errors'))
    target = HERE / (args.name + '.json')
    assert target.parent == HERE
    target.write_text(json.dumps({'schema': 'independent-r0006-trace-review/v1', 'traces': reports}, indent=2) + '\n', encoding='utf-8')
    return int(any(r['status'] != 'PASS_TRACE_ONLY' for r in reports))


if __name__ == '__main__':
    raise SystemExit(main())
