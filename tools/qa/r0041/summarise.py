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
            log = r['frameLog']
            # Re-classification with the run's OWN star baseline: at DPR 2 in Firefox the lit relief yields point-like
            # pixels (46 in frames identical to the reference, dRef < 1). ABSENT = dRef > 4, or point-like pixels at least
            # 10 above the baseline (median count over frames matching the reference, dRef <= 1).
            base = sorted(x[2] for x in log if x[3] is not None and x[3] <= 1)
            b0 = base[len(base) // 2] if base else 0
            log = [[x[0], 1 if ((x[3] is not None and x[3] > 4) or x[2] >= b0 + 10) else 0] + x[2:] for x in log]
            MEASURED = ('invalidate', 'resume', 'sky-invalidate', 'identity')  # noRecv/noRecvResume reuse these names
            allev = sorted(e['tMs'] for e in r.get('events', []))
            ev = [e['tMs'] for e in r.get('events', []) if e['name'] in MEASURED]
            per = []
            for k, t in enumerate(ev):
                # a segment ends at the next forced event of ANY kind (e.g. the next 'hide'), never spills into it
                # minus a 30 ms guard: a shot requested while the NEXT forcing call was executing (its mark is taken when the
                # call returns) shows the next event's state
                end = next((u for u in allev if u > t), float('inf')) - 30
                seg = [x for x in log if t <= x[0] < end]
                # absent run starting at or after the event, until the first present frame
                # Display state AT the event is the last frame produced before it; frames are produced only on change.
                prev = [x for x in log if x[0] < t]
                start = t if (prev and prev[-1][1] and seg and seg[0][1]) else next((x[0] for x in seg if x[1]), None)
                stop = next((x[0] for x in seg if start is not None and x[0] > start and not x[1]), None)
                per.append({'eventMs': t, 'absentFrames': sum(x[1] for x in seg), 'absentFromMs': start, 'presentAgainMs': stop,
                            'absentDurationMs': (stop - start) if (start is not None and stop is not None) else (None if start is None else 'open')})
            dprev = [x[5] for x in log if len(x) > 5 and x[5] is not None and not x[1]]
            rows.append({'valid': r.get('valid'), 'invalidReasons': r.get('invalidReasons'), 'starBaseline': b0, 'absentReclassified': sum(x[1] for x in log), 'maxPresentFrameDeltaY': max(dprev) if dprev else None, 'renderJobsAfterSettle': r.get('renderJobsAfterSettle'), 'frames': r['frames'], 'meanFrameIntervalMs': r['meanFrameIntervalMs'], 'absentFramesAfterSettle': r['absentFramesAfterSettle'],
                         'perEvent': per, 'intervals': r['absentIntervals'][:8], 'rafMoonReadyOff': r['rafMoonReadyOff'], 'rafNotCurrent': r['rafNotCurrent'],
                         'startupFirstPresentMs': r.get('startupFirstPresentMs'), 'startupAbsentAfterFirstPresent': r.get('startupAbsentAfterFirstPresent')})
        out[os.path.basename(f) + '|' + key] = {'engine': d['engine'], 'dpr': d['dpr'], 'motion': d['motion'], 'route': d['route'], 'startISO': d['startISO'], 'runs': rows,
                    'isolation': {'allowedExternal': d['isolation']['allowedExternal'], 'totalRequests': d['isolation']['totalRequests']}, 'error': d.get('error')}
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), indent=1)
for k, v in out.items():
    for r in v['runs']:
        pe = [(e['absentFrames'], e['absentDurationMs']) for e in r.get('perEvent', [])]
        print(k.split('|')[:5], 'absentAfterSettle', r.get('absentFramesAfterSettle'), 'perEvent', pe, 'intervals', [i['durationMs'] for i in r.get('intervals', [])][:5])
