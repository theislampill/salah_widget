"""R0041: aggregate summarise.py outputs into one table per (tree, route, engine, DPR, motion).
For event routes: events, events whose post-event segment had an ABSENT frame (re-classified with the run's own star
baseline; 30 ms guard before the next forcing call), and the largest absent duration. For natural/startup/no-successor
routes: absent frames after settle as the witness classified them (rolling reference for 'natural').
Usage: python aggregate.py <out.json> <tree>=<summary.json>[,<summary.json>...]:<route>[+<route>...]:<engines> ..."""
import json, sys
out = {}
for spec in sys.argv[2:]:
    tree, rest = spec.split('=', 1)
    files, routes, engines = rest.rsplit(':', 2)
    routes = routes.split('+'); engines = engines.split('+')
    for f in files.split(','):
        for k, v in json.load(open(f, encoding='utf-8')).items():
            if v['route'] not in routes or v['engine'] not in engines:
                continue
            key = '|'.join([tree, v['route'], v['startISO'], v['engine'], str(v['dpr']), v['motion']])
            row = out.setdefault(key, {'runs': 0, 'events': 0, 'eventsWithAbsence': 0, 'maxAbsentMs': 0, 'absentFramesAfterSettle': 0,
                                       'renderJobs': [], 'allowedExternal': 0, 'errors': [], 'invalidRuns': 0, 'uncheckedRuns': 0, 'retroRuns': 0, 'invalidReasons': []})
            row['allowedExternal'] += v['isolation']['allowedExternal']
            if v.get('error'): row['errors'].append(str(v['error'])[:120])
            for r in v['runs']:
                if 'error' in r and len(r) == 1: row['errors'].append(str(r['error'])[:120]); continue
                row['runs'] += 1; row['renderJobs'].append(r.get('renderJobsAfterSettle'))
                if r.get('valid') is False: row['invalidRuns'] += 1; row['invalidReasons'] += r.get('invalidReasons') or []
                elif r.get('valid') == 'retro': row['retroRuns'] += 1
                elif r.get('valid') is None: row['uncheckedRuns'] += 1
                row['absentFramesAfterSettle'] += r.get('absentFramesAfterSettle') or 0
                for e in r.get('perEvent', []):
                    row['events'] += 1
                    if e['absentFrames']:
                        row['eventsWithAbsence'] += 1
                        d = e['absentDurationMs']
                        if isinstance(d, (int, float)) and row['maxAbsentMs'] != 'open': row['maxAbsentMs'] = max(row['maxAbsentMs'], round(d))
                        elif d == 'open': row['maxAbsentMs'] = 'open'
EVENT_ROUTES = {'invalidate', 'resume', 'pageshow', 'sky', 'identity', 'identity12', 'noRecv', 'noRecvResume'}
for k, r in out.items():
    route = k.split('|')[1]; r['invalidReasons'] = sorted(set(r['invalidReasons']))
    # Fail-closed: a cell that measured nothing FAILS; it never passes by default.
    if r['runs'] == 0 or r['invalidRuns'] or r['errors'] or r['allowedExternal']: r['verdict'] = 'FAIL (measured nothing / invalid / isolation)'
    # A run with no validity verdict at all (a summary made before the witness asserted validity) is never a pass and
    # never merely "unchecked": the cell FAILS until its raw logs are re-summarised (summarise.py) or it is re-run.
    elif r['uncheckedRuns']: r['verdict'] = 'FAIL (runs without a validity verdict: pre-validity log)'
    elif route in EVENT_ROUTES and r['events'] == 0: r['verdict'] = 'FAIL (no forced event measured)'
    elif r['eventsWithAbsence'] or (route not in EVENT_ROUTES and r['absentFramesAfterSettle']): r['verdict'] = 'ABSENCE'
    else:
        r['verdict'] = 'NO ABSENCE' + (' (validity applied retroactively to the raw frame log; disc size not recorded)' if r['retroRuns'] else '')
        if route == 'natural' and all(j == 0 for j in r['renderJobs']): r['verdict'] += ' — by avoidance: 0 refinement jobs (main: 1 per run); the presenter is not exercised'
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), indent=1)
for k, r in sorted(out.items()):
    print(k, 'runs', r['runs'], 'events', r['events'], 'withAbsence', r['eventsWithAbsence'], 'max', r['maxAbsentMs'],
          'absentAfterSettle', r['absentFramesAfterSettle'], 'jobs', r['renderJobs'], 'iso', r['allowedExternal'], 'retro', r['retroRuns'], 'invalid', r['invalidRuns'], r['invalidReasons'][:2], '=>', r['verdict'])
# Exit status: 1 when any cell FAILS, so a void or pre-validity log cannot pass a scripted check unnoticed.
sys.exit(1 if any(r['verdict'].startswith('FAIL') for r in out.values()) else 0)
