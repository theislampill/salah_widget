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
    oracle = root / 'tests/r000c-weather.test.cjs'
    controls = ('^control: actual fresh acquisition|^R000C temperature (zero|negative) '
                '|^R000C negative Fahrenheit|^R000C missing optional arrays and two null endpoints')
    variants = [
        ('temperature-round',
         'const track=admitWeatherTrack(j.hourly,ctx,j.hourly_units), elevation=wxNumber(j.elevation);',
         'if(current){ const cu=j.current; current.temp=Math.round(cu.temperature_2m); }\n'
         '    const track=admitWeatherTrack(j.hourly,ctx,j.hourly_units), elevation=wxNumber(j.elevation);',
         '^R000C temperature null survives'),
        ('http-ok', 'if(r.ok!==true) return finish(null,"HTTP unavailable");',
         '// MUTANT: HTTP status admission removed.', '^R000C HTTP 500 healthy-shaped body'),
        ('cache-normalization',
         'const w=admitWeatherRecord(j.w,{units,zone:tz,retrievedAt:receipt},true);',
         'const w=j.w; // MUTANT: raw cache bypasses admission.',
         '^R000C cache'),
        ('hourly-shape',
         'const a=h[k], required=k==="temperature_2m"||k==="weather_code";\n'
         '    if(!Object.prototype.hasOwnProperty.call(h,k)&&!required){ T[k]=Array(len).fill(null); continue; }\n'
         '    if(!Array.isArray(a)||a.length!==len) return null;',
         'const a=h[k]||[], required=k==="temperature_2m"||k==="weather_code";\n'
         '    if(!Object.prototype.hasOwnProperty.call(h,k)&&!required){ T[k]=Array(len).fill(null); continue; }\n'
         '    // MUTANT: loose hourly arrays without required alignment/shape validation.',
         '^R000C bad hourly mismatched (required|optional) array'),
    ]
    records = []

    def run(label, path, pattern):
        command = [args.node, '--test', '--test-concurrency=1', '--test-name-pattern=' + pattern, str(oracle)]
        env = {**os.environ, 'SALAH_WEATHER_SOURCE': str(path)}
        result = subprocess.run(command, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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
                    and positive['exitCode'] == 0 and '\n# pass 5\n' in positive_text)
        records.append({'id': name, 'beforeSha256': sha(original), 'afterSha256': sha(mutant),
                        'before': before, 'after': after, 'oracleSha256': sha(oracle.read_bytes()),
                        'original': green, 'mutant': red, 'positive': positive,
                        'status': 'KILLED_BY_ORIGINAL_ASSERTION' if accepted else 'FAIL'})
        print(name, records[-1]['status'], flush=True)
    unchanged = source.read_bytes() == original
    report = {'schema': 'r000c-four-source-mutations/v1', 'source': 'index.html',
              'nodeVersion': subprocess.check_output([args.node, '--version'], text=True).strip(),
              'sourceSha256': sha(original), 'oracleSha256': sha(oracle.read_bytes()),
              'candidateUnchanged': unchanged, 'mutations': records,
              'status': 'PASS' if unchanged and all(r['status'] == 'KILLED_BY_ORIGINAL_ASSERTION' for r in records) else 'FAIL'}
    (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
