"""Moon-reuse audit, Job 2: summarise defect.cjs records (one or more JSON files) into one table-ready JSON.
Model frame analysis of captured frames, NOT human perception.
Usage: python defect-summary.py <out.json> <in1.json> [<in2.json> ...]"""
import json, sys
out = {}
for f in sys.argv[2:]:
    for label, d in json.load(open(f, encoding='utf-8')).items():
        w = d.get('workerLog') or []
        jobs = [x for x in w if x['kind'] == 'render']
        res = [x for x in w if x['kind'] == 'result']
        prev = [x for x in w if x['kind'] == 'preview']
        canc = [x for x in w if x['kind'] == 'cancel']
        st = d.get('states') or []
        first_ref = next((s['t'] for s in st if s['tier'] == 'refined-terrain'), None)
        after = [s for s in st if first_ref is not None and s['t'] >= first_ref]
        tiers = {}
        for s in after: tiers[s['tier']] = tiers.get(s['tier'], 0) + 1
        below = sum(1 for s in after if s['tier'] != 'refined-terrain')
        fr = d.get('frames') or []
        big = [x for x in fr if x.get('changed', 0) >= 200]
        blanks = [x for x in fr if x.get('meanAbsDeltaLuma', 0) > 25]
        # blank intervals: pairs of large luma jumps (disappear, reappear)
        blank_ms = []
        for i in range(0, len(blanks) - 1):
            a, b = blanks[i], blanks[i + 1]
            if b['t'] - a['t'] < 2000 and i % 2 == 0: blank_ms.append(round(b['t'] - a['t']))
        swaps = [{'t': round(x['t'] / 1000, 2), 'changed': x['changed'], 'over3': x['over3'], 'over8': x['over8'], 'maxDelta': x['maxDelta'], 'meanAbsDeltaLuma': round(x['meanAbsDeltaLuma'], 2)} for x in big]
        g = d.get('gate') or {}
        late_runs = [r for r in g.get('runs', []) if r['t'] > 15000]
        mo = [s['moonlightOpacity'] for s in after if s.get('moonlightOpacity') is not None]
        out[label] = {
            'engine': d['engine'], 'dpr': d['dpr'], 'seconds': d['seconds'], 'startISO': d['startISO'], 'error': d.get('error'), 'pageErrors': d.get('pageErrors'),
            'jobs': len(jobs), 'jobStartsS': [round(x['t'] / 1000, 1) for x in jobs], 'results': len(res), 'resultMs': [round(x['ms']) for x in res if x.get('ms')],
            'previews': len(prev), 'cancels': len(canc),
            'reachedRefined': first_ref is not None, 'firstRefinedS': round(first_ref / 1000, 1) if first_ref else None,
            'tierSamplesAfterFirstRefined': tiers, 'secondsBelowRefinedAfterFirst': below, 'samplesAfterFirstRefined': len(after),
            'frameCount': d['frameSummary']['count'], 'meanFrameIntervalMs': round(d['frameSummary']['meanIntervalMs'] or 0, 1),
            'bigChangeEvents': len(big), 'blankDiscEvents': len(blanks), 'blankDurationsMs': blank_ms, 'swaps': swaps[:40],
            'gateFrames': g.get('frames'), 'gateNotReadyFrames': g.get('notReady'), 'gateMaskOffFrames': g.get('maskOff'), 'gateRunsAfter15s': late_runs[:20],
            'moonlightOpacityRange': [min(mo), max(mo)] if mo else None,
            'displayModes': sorted({s.get('displayMode') for s in after if s.get('displayMode')}),
            'lightStates': sorted({str(s.get('light')) for s in after}),
            'moonSkyOpacityMin': min((s['moonSkyOpacity'] for s in after if s.get('moonSkyOpacity') is not None), default=None),
            'moonFeatureOpacityMin': min((s['moonFeatureOpacity'] for s in after if s.get('moonFeatureOpacity') is not None), default=None),
            'moonAltitudeDeg': after[-1].get('alt') if after else None,
            'cpu': d.get('cpu'), 'crops': d.get('crops'),
            'isolation': {'totalRequests': d['isolation']['totalRequests'], 'externalByLayerHostOutcome': d['isolation']['externalByLayerHostOutcome'], 'allowedExternal': d['isolation']['allowedExternal']},
        }
json.dump(out, open(sys.argv[1], 'w', encoding='utf-8'), indent=1)
for k, v in out.items():
    cpu = v['cpu'] and round(v['cpu']['browserTreeCpuSeconds'] / v['cpu']['wallSeconds'], 2)
    print(k, 'jobs', v['jobs'], 'res', v['resultMs'], 'canc', v['cancels'], 'refined?', v['reachedRefined'], 'below', v['secondsBelowRefinedAfterFirst'], '/', v['samplesAfterFirstRefined'],
          'fps-int', v['meanFrameIntervalMs'], 'blanks', v['blankDiscEvents'], v['blankDurationsMs'], 'big', v['bigChangeEvents'], 'gateLate', len(v['gateRunsAfter15s']),
          'light', v['moonlightOpacityRange'], v['displayModes'], 'cpuPerWall', cpu, 'err', (v['error'] or '')[:80])
