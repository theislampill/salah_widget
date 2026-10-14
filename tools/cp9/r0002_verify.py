"""R0002 post-acquisition assertions. Uses the retained R0007 native runner.

This reads original traces and inputs; it neither launches nor calls the widget.
PASS here is semantic evidence only. First-presentation pixels, readability and
the inherited preservation captures still require independent visual review.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

PRAYERS = ('Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha')
DAY = '07-09-2026'
KEY = 'salah:24.47|39.61|UTC|4|0'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise AssertionError(message)


def checkpoint(trace, name):
    rows = [s for s in trace['checkpointSnapshots'] if s.get('checkpoint') == name]
    require(len(rows) == 1, 'missing or duplicate checkpoint ' + name)
    return rows[0]


def timetable(row, expected):
    require(row.get('today') is not None, 'usable current record absent')
    require(row['today']['timings'] == expected, 'wrong admitted timetable')
    html = row['dom']['.times']['html']
    for prayer in PRAYERS:
        require(html.count('data-prayer-key="' + prayer + '"') == 1,
                'missing timetable row ' + prayer)
    values = re.findall(r'<span class="tm">([^<]*)</span>', html)
    require(len(values) == 6 and all(v != '—' for v in values), 'unavailable required clocks')
    clocks = [re.match(r'\s*(\d\d):(\d\d)', expected[p]).groups() for p in PRAYERS]
    expected24 = [h + ':' + m for h, m in clocks]
    expected12 = [f'{int(h) % 12 or 12}:{m} {"PM" if int(h) >= 12 else "AM"}' for h, m in clocks]
    require(values in (expected24, expected12), 'visible clocks differ from supplied input')
    require('<path' in row['dom']['.arc']['html'], 'actual SVG arc absent')


def unavailable(row):
    require(row.get('today') is None and row.get('currentDay') is None, 'rejected record adopted')
    require(row['timezone'] == 'UTC', 'invalid timezone adopted')
    html = row['dom']['.times']['html']
    require(html.count('<span class="tm">—</span>') == 6, 'six required times not withdrawn')
    for prayer in PRAYERS:
        require(html.count('data-prayer-key="' + prayer + '"') == 1, 'unavailable row absent')
    require(row['dom']['.nt']['text'] == '—' and row['dom']['.arc']['html'] == '',
            'invalid ingress rendered precise next time or arc')


def audit(trace, case):
    cid = case['caseId']
    require(trace['caseId'] == cid, 'case identity mismatch')
    require(trace['status'] in ('PASS_ASSERTIONS_PENDING_PIXEL_REVIEW',
                                'PARTIAL_FIRST_PRESENTATION_REVIEW_REQUIRED'),
            'native driver failed: ' + str(trace.get('failure')))
    require(not trace['pageErrors'] and not trace['unexpected'], 'page error or unmatched provider')
    rows = [s for s in trace['snapshots'] if s['stage'] == 'render-completed' and not s.get('checkpoint')]
    current = [s for s in rows if s.get('currentDay')]
    require(current, 'no actual current render')
    day = current[0]['currentDay']
    requests = [r for r in trace['requests'] if r['kind'] == 'prayer' and '/' + day + '?' in r['url']]
    writes = [s for s in trace['storageLog'] if s['operation'] == 'set' and s['key'].startswith('salah:')]
    require(not any(s['operation'] in ('remove', 'clear') and
                    (s.get('key', '').startswith('salah:') or s['operation'] == 'clear')
                    for s in trace['storageLog']), 'prayer cache purged')
    supplied = [r['payload']['data']['timings'] for r in case['responseRules']
                if r.get('payload', {}).get('data', {}).get('timings')]
    seeds = [json.loads(s['value'])['data']['timings'] for s in case['cacheSeeds']
             if s['key'].startswith('salah:') and not any(x in cid for x in ('broken-json', 'null-timings'))]
    for row in rows:
        for selector in ('.nt', '.left', '.times', '#ce', '#ah', '.arc'):
            node = row['dom'][selector]
            require(not any(s in node.get('text', '') + node.get('html', '')
                            for s in ('NaN', 'Infinity', 'undefined')), 'invalid rendered text')
        card = row['dom']['.c']['geometry']
        require(card['width'] == 325 and card['height'] == 530, 'card size changed')
        for selector in ('.times', '.buckle', '.d'):
            g = row['dom'][selector]['geometry']
            require(g['x'] >= card['x'] and g['y'] >= card['y'] and
                    g['x'] + g['width'] <= card['x'] + 325.5 and
                    g['y'] + g['height'] <= card['y'] + 530.5, 'clipped ' + selector)
        if row.get('currentDay'):
            expected = row['today']['timings']
            require(expected in supplied + seeds, 'unsupplied current prayer record')
            timetable(row, expected)
    if cid.startswith('R0002-ingress-'):
        unavailable(checkpoint(trace, 'unavailable'))
        require(checkpoint(trace, 'loading')['today'] is None, 'loading adopted a record')
        require(len(requests) == 4, 'expected three invalid attempts and one recovery attempt')
        require([r['rule'] for r in requests] == ['invalid-loading', 'invalid', 'invalid', 'healthy'],
                'original invalid/healthy request sequence changed')
        owners = [r['owner']['current'] for r in requests]
        require(all(owners) and len({o['operationId'] for o in owners[:3]}) == 1 and
                owners[3]['operationId'] != owners[0]['operationId'], 'operation/attempt ownership conflated')
        fence = requests[0]['cooldown']['current']['nextTry']
        require(trace['startedPerformance'] + requests[3]['realElapsedMs'] >= fence,
                'recovery crossed 60-second eligibility fence early')
        recovery = requests[3]['realElapsedMs']
        for row in trace['snapshots']:
            if row['realElapsedMs'] < recovery:
                require(row['today'] is None and row['timezone'] == 'UTC', 'invalid state before recovery')
        require(not [s for s in writes if s['realElapsedMs'] < recovery], 'invalid cache write')
        require(any(e['type'] == 'error-output' and e['message'] == 'Could not load prayer times'
                    and e['realElapsedMs'] < recovery for e in trace['events']), 'actual failure output absent')
        require(checkpoint(trace, 'first-recovered')['renderOrdinal'] == current[0]['renderOrdinal'],
                'first recovered receipt replaced by later render')
        require(len([r for r in trace['requests'] if r['kind'] == 'prayer' and
                     '/08-09-2026?' in r['url']]) == 1, 'unexpected tomorrow prefetch count')
    elif cid in ('R0002-cache-null-timings', 'R0002-cache-broken-json'):
        require(len(requests) == 1 and requests[0]['rule'] == 'healthy', 'corrupt cache prevented live acquisition')
        require(current[0]['realElapsedMs'] >= requests[0]['realElapsedMs'], 'corrupt cache painted')
        require(len(writes) == 1 and not writes[0]['denied'] and writes[0]['key'] == KEY,
                'healthy recovered cache not persisted')
        stored = next(s['value'] for s in trace['storage'] if s['key'] == KEY)
        require(stored == writes[0]['value'], 'stored cache differs from admitted write')
        require(json.loads(stored)['data']['timings'] == current[0]['today']['timings'], 'wrong persisted timetable')
    elif cid in ('R0002-cache-valid-offline', 'R0002-cache-valid-denied-write', 'R0002-cache-distinct-denied-write') or '-cache' in cid:
        seed = next(s for s in case['cacheSeeds'] if s['key'].startswith('salah:'))
        require(next(s['value'] for s in trace['storage'] if s['key'] == seed['key']) == seed['value'],
                'valid stored bytes changed during failed network/storage operation')
        require(current[0]['realElapsedMs'] <= requests[0]['realElapsedMs'], 'valid cache did not paint before refresh')
        if case.get('storageWriteDenied'):
            require(writes and all(s['denied'] for s in writes), 'denied write not attempted or succeeded')
            require(len(requests) == 1, 'healthy refresh retried after storage denial')
        else:
            require(len(requests) == 3 and not writes, 'failed refresh changed valid cache')
        warm = checkpoint(trace, 'warm-retained')
        require(warm['currentDay'] == day, 'valid memory blanked')
        if cid == 'R0002-cache-distinct-denied-write':
            require(current[0]['today']['timings']['Fajr'] == '04:47' and
                    warm['today']['timings']['Fajr'] == '05:03', 'denied storage confused with admitted memory')
            timetable(warm, warm['today']['timings'])
            require(any(s['today']['timings']['Fajr'] == '05:03' for s in current),
                    'refreshed memory did not reach an actual completed render')
    if cid.startswith('R0002-optional-'):
        footer, dialog = checkpoint(trace, 'footer'), checkpoint(trace, 'disclosure')
        require(len(requests) == 1, 'optional data caused required prayer retries')
        timetable(footer, supplied[0]); timetable(dialog, supplied[0])
        require(dialog['dom']['#dateDialog']['geometry']['width'] > 0, 'date disclosure not open')
        if any(ex.get('equals', {}).get('dom/#dateHijri/text') == 'Hijri date unavailable' for ex in case['expected']):
            require(footer['dom']['#ah']['text'] == 'Hijri date unavailable', 'invented optional footer')
            require(dialog['dom']['#dateHijri']['text'] == 'Hijri date unavailable' and
                    'Hijri date unavailable' in dialog['dom']['#dateReason']['text'], 'missing full unavailable reason')
    return {'caseId': cid, 'status': 'PASS_TRACE_ASSERTIONS_PIXEL_REVIEW_REQUIRED',
            'completedRenders': len(rows), 'currentRenders': len(current),
            'currentAttempts': len(requests), 'prayerWriteAttempts': len(writes),
            'captureMismatches': trace.get('captureMismatches', [])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--case-id', action='append')
    args = parser.parse_args()
    packet = json.loads(args.cases.read_bytes())
    selected = [c for c in packet['cases'] if not args.case_id or c['caseId'] in args.case_id]
    require(selected and (not args.case_id or set(args.case_id) == {c['caseId'] for c in selected}), 'unknown case')
    results = []
    for case in selected:
        folder = args.output / case['caseId']
        require(json.loads((folder / 'case-input.json').read_bytes()) == case, 'case input changed')
        trace_path = folder / 'trace.json'
        result = audit(json.loads(trace_path.read_bytes()), case)
        result['traceSha256'] = sha(trace_path.read_bytes())
        hashes = json.loads((folder / 'document-hashes.json').read_bytes())
        require(hashes['source'] == packet['sourceFiles'][case['entry']], 'runtime source changed')
        require(hashes['fixture'] == packet['sourceFiles']['tests/rlgwo/prayer-browser-fixture.cjs'], 'observer changed')
        videos = list((folder / 'video').glob('*.webm'))
        require(len(videos) == 1 and videos[0].stat().st_size > 0, 'native video absent')
        result['videoSha256'] = sha(videos[0].read_bytes())
        results.append(result)
    report = {'schema': 'r0002-native-trace-review/v1', 'status': 'PASS_TRACE_ASSERTIONS_PIXEL_REVIEW_REQUIRED',
              'caseFileSha256': sha(args.cases.read_bytes()), 'results': results}
    (args.output / 'r0002-trace-review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': report['status'], 'cases': len(results)}))


if __name__ == '__main__':
    main()
