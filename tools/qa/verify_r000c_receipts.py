"""Reconcile R000C raw ingress, admission, cache and visible-consumer receipts.

Read-only semantic validation. Pixel and independent qualification remain separate.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit, parse_qs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    args = p.parse_args()
    results = []
    for path in sorted(args.root.glob('**/receipt.json')):
        if 'pixel-review' in path.parts:
            continue
        r = json.loads(path.read_bytes())
        if 'observations' not in r:
            continue
        case = json.loads((path.parent / 'case-input.json').read_bytes())
        failures = []
        def require(value, message):
            if not value:
                failures.append(message)
        require(r['status'] == 'PASS_ASSERTIONS_PENDING_PIXEL_REVIEW', 'original assertions failed')
        require(all(r['checks'].values()), 'failed original check')
        require(bool(r.get('fixture')), 'missing complete fixture trace')
        if not r.get('fixture'):
            results.append({'case': str(path.parent), 'status': 'FAIL', 'failures': failures})
            continue
        weather = [x for x in r['fixture']['ledger'] if 'api.open-meteo.com/v1/forecast' in x['url']]
        require(len(weather) >= (2 if case.get('night') else 1), 'weather request count')
        for request in weather:
            q = parse_qs(urlsplit(request['url']).query)
            require(q.get('latitude') == ['24.47'] and q.get('longitude') == ['39.61'], 'wrong target')
            require(q.get('timezone') == ['Asia/Riyadh'] and q.get('temperature_unit') == ['celsius'], 'wrong captured zone/units')
            require(request.get('jsonReads') == 1 and request.get('jsonSettled'), 'native JSON not consumed exactly once')
        if weather:
            current = weather[0]['parsedBody']['current']
            if case['inputCase'] == '12-absent-temp':
                require('temperature_2m' not in current, 'temperature property was not deleted')
            else:
                require(current.get('temperature_2m') == case['temp'], 'raw temperature differs from fixture')
            require(current.get('precipitation') == ('Infinity' if case['precip'] is None else case['precip']), 'raw amount differs from fixture')
        for observation in r['observations']:
            s = observation['state']
            recovery = observation['stage'].startswith('recovered')
            temp, precip = (20, 2) if recovery else (case['temp'], case['precip'])
            require(s['raw']['temp'] == temp and s['cached']['w']['temp'] == temp, 'admitted/cache temperature')
            require(s['raw']['precip'] == precip and s['cached']['w']['precip'] == precip, 'admitted/cache amount')
            require(s['temperature'] == ('' if temp is None else str(temp) + '°'), 'visible header')
            require(s['fx'] == 'thunder' and s['qa']['weatherHeader']['rawCode'] == 95, 'H5/H8 condition retention')
            require(s['qa']['wxTruth']['lane'] == 'live' and s['qa']['wxTruth']['observedPresent'] is False, 'model live lane must not become observation/preview')
            wet = precip is not None and precip > 0
            require(s['precip'] == ('on' if wet else 'off'), 'quantitative effect dataset')
            require((s['visibleParticles'] > 0) == wet and s['lightning'] == 'off', 'particles/lightning')
        if case.get('night') and weather:
            require(weather[-1]['parsedBody']['current']['precipitation'] == 2, 'recovery did not use healthy ingress')
            require(weather[-1]['elapsedMs'] - weather[0]['elapsedMs'] >= 60000, 'recovery bypassed normal throttle')
            initial, final = r['observations'][0]['state'], r['observations'][-1]['state']
            wall = final['wallUtcMs'] - initial['wallUtcMs']
            elapsed = final['elapsedMs'] - initial['elapsedMs']
            require(abs(wall - elapsed) < 10 and elapsed >= 60000, 'night wall must move at native 1x')
            require(final['qa']['moonTruth']['phaseFraction'] == 0.5, 'half-Moon input')
            require(final['qa']['moonTruth']['calendarMoonVisible'], 'loaded Moon absent')
        require(all(x['action'] == 'consumer-read' for x in r['fixture']['weatherEvents']), 'state-installation helper used')
        video = path.parent / r['video']['file']
        require(hashlib.sha256(video.read_bytes()).hexdigest() == r['video']['sha256'], 'original native video drift')
        results.append({'case': str(path.parent), 'status': 'PASS' if not failures else 'FAIL', 'failures': failures,
                        'receiptSha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    print(json.dumps({'schema': 'r000c-consumer-reconciliation/v1', 'cases': results,
                      'status': 'PASS' if results and all(x['status'] == 'PASS' for x in results) else 'FAIL',
                      'limitation': 'Consumer semantics only; raw native pixels and motion need independent review.'}, indent=2))
    return 0 if results and all(x['status'] == 'PASS' for x in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
