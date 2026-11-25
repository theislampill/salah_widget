"""R0041: summarise witness.cjs outputs. For event routes, the absence measured is the part AFTER each event
(for resume: after the page becomes visible again; frames while hidden are not shown to anyone).
Usage: python summarise.py <out.json> <in.json> [...]"""
import json, os, sys
out = {}
def retro_validity(r, route, absent):
    """Runs recorded before the witness carried its own validity verdict (review finding 2): apply the same fail-closed
    rules to the raw frame log. A run with no frame, with a judged frame that has no reference comparison, or whose
    hidden interval is not classified absent is INVALID. The disc size was not recorded then and cannot be checked."""
    log, reasons = r['frameLog'], []
    ev = sorted(r.get('events', []), key=lambda e: e['tMs'])
    if not log: reasons.append('no frames')
    if route != 'startup':
        first = ev[0]['tMs'] if ev else None
        judged = [x for x in log if first is None or x[0] >= first]
        if all(x[3] is None for x in log) or any(x[3] is None for x in judged):
            reasons.append('frames without a reference comparison')
    if route in ('resume', 'pageshow', 'noRecvResume'):
        for k, e in enumerate(ev):
            if e['name'] != 'hide': continue
            t1, t2 = e['tMs'] + 30, (ev[k + 1]['tMs'] if k + 1 < len(ev) else float('inf')) - 30
            inside = [a for x, a in zip(log, absent) if t1 <= x[0] < t2]
            if inside and not any(inside): reasons.append('hidden state not classified absent')
    return reasons
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
            valid, reasons = r.get('valid'), r.get('invalidReasons')
            if valid is None:
                reasons = retro_validity(r, d['route'], [x[1] for x in log]); valid = False if reasons else 'retro'
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
            rows.append({'valid': valid, 'invalidReasons': reasons, 'starBaseline': b0, 'absentReclassified': sum(x[1] for x in log), 'maxPresentFrameDeltaY': max(dprev) if dprev else None, 'renderJobsAfterSettle': r.get('renderJobsAfterSettle'), 'frames': r['frames'], 'meanFrameIntervalMs': r['meanFrameIntervalMs'], 'absentFramesAfterSettle': r['absentFramesAfterSettle'],
                         'perEvent': per, 'intervals': r['absentIntervals'][:8], 'rafMoonReadyOff': r['rafMoonReadyOff'], 'rafNotCurrent': r['rafNotCurrent'],
                         'startupFirstPresentMs': r.get('startupFirstPresentMs'), 'startupAbsentAfterFirstPresent': r.get('startupAbsentAfterFirstPresent')})
        out[os.path.basename(f) + '|' + key] = {'engine': d['engine'], 'dpr': d['dpr'], 'motion': d['motion'], 'route': d['route'], 'startISO': d['startISO'], 'runs': rows,
                    'isolation': {'allowedExternal': d['isolation']['allowedExternal'], 'totalRequests': d['isolation']['totalRequests']}, 'error': d.get('error')}
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), indent=1)
for k, v in out.items():
    for r in v['runs']:
        pe = [(e['absentFrames'], e['absentDurationMs']) for e in r.get('perEvent', [])]
        print(k.split('|')[:5], 'absentAfterSettle', r.get('absentFramesAfterSettle'), 'perEvent', pe, 'intervals', [i['durationMs'] for i in r.get('intervals', [])][:5])
