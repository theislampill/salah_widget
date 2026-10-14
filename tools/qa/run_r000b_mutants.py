"""Four temporary actual-source RED controls; never modify the candidate or oracle."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--node', required=True)
    args = p.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = root / 'index.html'
    original = source.read_bytes()
    text = original.decode('utf-8')
    oracle = root / 'tests/r000b-remaining.test.cjs'
    controls = "^positive "
    variants = [('weather-source-as-receipt', 'const sourceAge=w&&wxNumber(w.currentValidAt)!=null?now-w.currentValidAt:null;', 'const sourceAge=w&&wxNumber(w.retrievedAt)!=null?now-w.retrievedAt:null;', '^B13 M1 '), ('radar-frame-as-receipt', 'const frameAge=weatherRadar&&wxNumber(weatherRadar.frameGeneratedAt)!=null?now-weatherRadar.frameGeneratedAt:null;', 'const frameAge=weatherRadar&&wxNumber(weatherRadar.retrievedAt)!=null?now-weatherRadar.retrievedAt:null;', '^B13 M2 '), ('per-use-expiry-bypass', 'return weatherEligibility(weather,now).eligible?weather:null;', 'return weather; // MUTANT: admission remains intact; per-use expiry bypassed.', '^B13 M3 '), ('mutable-global-zone', 'const ctx={...captured,retrievedAt:Date.now()}, current=', 'const ctx={...captured,zone:tz,retrievedAt:Date.now()}, current=', '^B14 M4 ')]
    records = []

    def run(label, path, pattern):
        command = [args.node, '--test', '--test-concurrency=1', '--test-name-pattern=' + pattern, str(oracle)]
        env = {**os.environ, 'SALAH_WEATHER_SOURCE': str(path)}
        result = subprocess.run(command, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
        log = out / (label + '.tap')
        log.write_bytes(result.stdout)
        return {'command': command, 'environment': {'SALAH_WEATHER_SOURCE': str(path)},
                'exitCode': result.returncode, 'log': log.name, 'sha256': sha(result.stdout)}, result.stdout.decode('utf-8')

    for name, before, after, pattern in variants:
        assert text.count(before) == 1, (name, 'source anchor count', text.count(before))
        mutant = text.replace(before, after, 1).encode('utf-8')
        path = out / (name + '.html')
        path.write_bytes(mutant)
        green, green_text = run(name + '-original', source, pattern)
        red, red_text = run(name + '-mutant', path, pattern)
        positive, positive_text = run(name + '-positive', path, controls)
        accepted = (green['exitCode'] == 0 and '\n# pass 0\n' not in green_text
                    and red['exitCode'] == 1 and 'ERR_ASSERTION' in red_text
                    and 'not ok ' in red_text and 'SyntaxError' not in red_text
                    and positive['exitCode'] == 0 and '\n# pass 3\n' in positive_text)
        records.append({'id': name, 'beforeSha256': sha(original), 'afterSha256': sha(mutant),
                        'before': before, 'after': after, 'line': text[:text.index(before)].count('\n')+1, 'oracleSha256': sha(oracle.read_bytes()),
                        'original': green, 'mutant': red, 'positive': positive,
                        'status': 'KILLED_BY_ORIGINAL_ASSERTION' if accepted else 'FAIL'})
        print(name, records[-1]['status'], flush=True)
    unchanged = source.read_bytes() == original
    report = {'schema': 'r000b-four-source-mutations/v1', 'source': 'index.html',
              'nodeVersion': subprocess.check_output([args.node, '--version'], text=True).strip(),
              'sourceSha256': sha(original), 'oracleSha256': sha(oracle.read_bytes()),
              'candidateUnchanged': unchanged, 'mutations': records,
              'status': 'PASS' if unchanged and all(r['status'] == 'KILLED_BY_ORIGINAL_ASSERTION' for r in records) else 'FAIL'}
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
