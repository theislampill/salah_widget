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
            key = '|'.join([tree, v['route'], v['engine'], str(v['dpr']), v['motion']])
            row = out.setdefault(key, {'runs': 0, 'events': 0, 'eventsWithAbsence': 0, 'maxAbsentMs': 0, 'absentFramesAfterSettle': 0,
                                       'renderJobs': [], 'allowedExternal': 0, 'errors': []})
            row['allowedExternal'] += v['isolation']['allowedExternal']
            if v.get('error'): row['errors'].append(v['error'][:120])
            for r in v['runs']:
                if 'error' in r and len(r) == 1: row['errors'].append(str(r['error'])[:120]); continue
                row['runs'] += 1; row['renderJobs'].append(r.get('renderJobsAfterSettle'))
                row['absentFramesAfterSettle'] += r.get('absentFramesAfterSettle') or 0
                for e in r.get('perEvent', []):
                    row['events'] += 1
                    if e['absentFrames']:
                        row['eventsWithAbsence'] += 1
                        d = e['absentDurationMs']
                        if isinstance(d, (int, float)): row['maxAbsentMs'] = max(row['maxAbsentMs'], round(d))
                        elif d == 'open': row['maxAbsentMs'] = 'open'
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), indent=1)
for k, r in sorted(out.items()):
    print(k, 'runs', r['runs'], 'events', r['events'], 'withAbsence', r['eventsWithAbsence'], 'max', r['maxAbsentMs'],
          'absentAfterSettle', r['absentFramesAfterSettle'], 'jobs', r['renderJobs'], 'iso', r['allowedExternal'], r['errors'][:1])
