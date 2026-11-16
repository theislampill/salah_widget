"""R0041: summarise witness.cjs outputs. For event routes, the absence measured is the part AFTER each event
(for resume: after the page becomes visible again; frames while hidden are not shown to anyone).
Usage: python summarise.py <out.json> <in.json> [...]"""
import json, os, sys
out = {}
for f in sys.argv[2:]:
    for key, d in json.load(open(f, encoding='utf-8')).items():
        rows = []
        for r in d.get('runs', []):
            if 'frameLog' not in r:
                rows.append({'error': r.get('error')}); continue
            log = r['frameLog']; ev = [e['tMs'] for e in r.get('events', []) if e['name'] in ('invalidate', 'resume', 'sky-invalidate', 'identity')]
            per = []
            for k, t in enumerate(ev):
                end = ev[k + 1] if k + 1 < len(ev) else float('inf')
                seg = [x for x in log if t <= x[0] < end]
                # absent run starting at or after the event, until the first present frame
                start = next((x[0] for x in seg if x[1]), None)
                stop = next((x[0] for x in seg if start is not None and x[0] > start and not x[1]), None)
                per.append({'eventMs': t, 'absentFrames': sum(x[1] for x in seg), 'absentFromMs': start, 'presentAgainMs': stop,
                            'absentDurationMs': (stop - start) if (start is not None and stop is not None) else (None if start is None else 'open')})
            rows.append({'frames': r['frames'], 'meanFrameIntervalMs': r['meanFrameIntervalMs'], 'absentFramesAfterSettle': r['absentFramesAfterSettle'],
                         'perEvent': per, 'intervals': r['absentIntervals'][:8], 'rafMoonReadyOff': r['rafMoonReadyOff'], 'rafNotCurrent': r['rafNotCurrent'],
                         'startupFirstPresentMs': r.get('startupFirstPresentMs'), 'startupAbsentAfterFirstPresent': r.get('startupAbsentAfterFirstPresent')})
        out[os.path.basename(f) + '|' + key] = {'engine': d['engine'], 'dpr': d['dpr'], 'motion': d['motion'], 'route': d['route'], 'startISO': d['startISO'], 'runs': rows,
                    'isolation': {'allowedExternal': d['isolation']['allowedExternal'], 'totalRequests': d['isolation']['totalRequests']}, 'error': d.get('error')}
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), indent=1)
for k, v in out.items():
    for r in v['runs']:
        pe = [(e['absentFrames'], e['absentDurationMs']) for e in r.get('perEvent', [])]
        print(k.split('|')[:5], 'absentAfterSettle', r.get('absentFramesAfterSettle'), 'perEvent', pe, 'intervals', [i['durationMs'] for i in r.get('intervals', [])][:5])
