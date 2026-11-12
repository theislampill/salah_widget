#!/usr/bin/env python3
"""Direct lexer mutation controls, retaining the redundant Index-only survivor."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source', type=Path)
    ap.add_argument('powershell', type=Path)
    ap.add_argument('--baseline', type=Path, required=True)
    args = ap.parse_args()
    source = args.source.resolve(strict=True)
    baseline = args.baseline.resolve(strict=True)
    text = source.read_text(encoding='utf-8')
    fixture = Path(__file__).resolve().with_name('install-json-lexer.ps1')
    root = Path(tempfile.mkdtemp(prefix='r0013-lexer-mutants-')).resolve()
    results, applicability = [], []
    env = dict(os.environ)
    for key in list(env):
        if key.lower() == 'psmodulepath':
            del env[key]

    def replace_once(body, old, new):
        if body.count(old) != 1:
            raise RuntimeError('Mutant source boundary drift: ' + old)
        return body.replace(old, new, 1)

    coverage = '$position -eq $Json.Length -and '
    guard = '            if (-not $tokenMatch.Success -or $tokenMatch.Index -ne $position) { return $false }\n'
    incomplete = replace_once(text, coverage, '')
    # The G anchor, exact Index check and final cumulative coverage overlap.
    # Disable all three for this explicit scan-ahead fault; do not pretend that
    # deleting a redundant Index check alone must loosen the language.
    loose = replace_once(replace_once(incomplete, "[regex]'\\G", "[regex]'"), guard, '')
    redundant = replace_once(text, guard, '')
    mutations = [
        ('missing-final-coverage', incomplete, ['strict lexer trailing garbage after root',
                                             'strict lexer trailing garbage after space']),
        ('skip-contiguous-coverage', loose, ['strict lexer gap before first token',
                                           'strict lexer gap between tokens',
                                           'strict lexer gap between array values',
                                           'strict lexer trailing garbage after root']),
    ]

    def run(name, body):
        path = root / (name + '.ps1')
        path.write_text(body, encoding='utf-8', newline='\n')
        report_path = root / (name + '.json')
        command = [str(args.powershell.resolve(strict=True)), '-NoLogo', '-NoProfile', '-NonInteractive',
                   '-File', str(fixture), '-SourceFile', str(path), '-BaselineFile', str(baseline),
                   '-Suite', 'Equivalence', '-ReportPath', str(report_path)]
        with (root / (name + '.stdout.txt')).open('xb') as so, (root / (name + '.stderr.txt')).open('xb') as se:
            process = subprocess.run(command, env=env, stdout=so, stderr=se, timeout=30)
        report = json.loads(report_path.read_text(encoding='utf-8-sig'))
        rows = report['results']
        if (report['source'] != hashlib.sha256(path.read_bytes()).hexdigest()
                or report['fixture'] != hashlib.sha256(fixture.read_bytes()).hexdigest()
                or report['suite'] != 'Equivalence' or len(rows) != 51
                or len({row['case'] for row in rows}) != 51):
            raise RuntimeError('Mutant receipt identity or denominator failure')
        return process.returncode, report, path, command

    healthy_exit, healthy, _, _ = run('healthy', text)
    healthy_ok = healthy_exit == 0 and all(row['pass'] is True for row in healthy['results'])
    results.append({'case': 'exact-source direct healthy corpus', 'pass': healthy_ok})
    if healthy_ok:
        positive_names = {row['case'] for row in healthy['results'] if row['observation']['expected'] is True}
        for name, body, required in mutations:
            code, report, path, command = run(name, body)
            failed = [row for row in report['results'] if row['pass'] is not True]
            failed_names = {row['case'] for row in failed}
            positives_ok = all(row['pass'] is True for row in report['results'] if row['case'] in positive_names)
            # Each failure must be the direct Boolean language oracle. Parse,
            # import, output-shape or baseline errors cannot kill a mutant.
            language_failures = all(row.get('error', '').startswith('Wrong strict result for ') for row in failed)
            detected = code == 1 and set(required) <= failed_names and positives_ok and language_failures
            results.append({'case': name, 'pass': detected, 'detected': detected, 'fixtureExit': code,
                            'requiredFailures': required, 'actualFailures': sorted(failed_names),
                            'positiveControlsPassed': positives_ok, 'mutant': str(path), 'command': command,
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        code, report, path, command = run('redundant-index-check-only', redundant)
        survived = code == 0 and all(row['pass'] is True for row in report['results'])
        applicability.append({'case': 'redundant-index-check-only', 'survived': survived,
                              'fixtureExit': code, 'mutant': str(path), 'command': command,
                              'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                              'disposition': 'Redundant guard: G anchor and final coverage still enforce contiguity; no mutation-kill credit'})
        if not survived:
            raise RuntimeError('Redundant-control outcome changed; investigate instead of claiming a kill')
    value = {'source': hashlib.sha256(source.read_bytes()).hexdigest(), 'fixtureRoot': str(root),
             'results': results, 'applicability': applicability, 'nativeHost': healthy['host'],
             'platform': healthy['platform'], 'runtime': healthy['runtime']}
    (root / 'mutation-summary.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(value, indent=2))
    return 0 if all(row['pass'] for row in results) and len(results) == 3 else 1


if __name__ == '__main__':
    raise SystemExit(main())
