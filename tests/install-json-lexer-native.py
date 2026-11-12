#!/usr/bin/env python3
"""Receive bounded original/candidate R0013 lexer observations on native Windows.

An original-source run is diagnostic acquisition, never product qualification.
The launcher retains original streams, exact sources, deadline and cleanup facts.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import statistics
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_direct(report, expected, source_sha, fixture_sha, host):
    budget = 30 if host['version'].startswith('5.1.') else 5
    if (report.get('schema') != 'r0013-json-lexer-v2' or report.get('source') != source_sha
            or report.get('fixture') != fixture_sha or expected['fixtureSha256'] != fixture_sha
            or report.get('functionSha256') != expected['functionSha256']
            or report.get('baselineFunctionSha256') != expected['baselineFunctionSha256']
            or report.get('host') != host['version'] or report.get('edition') != host['edition']
            or report.get('platform') != 'Win32NT' or report.get('runtime') != host['runtime']
            or report.get('suite') != 'All' or report.get('performanceBudgetSeconds') != budget):
        raise RuntimeError('Candidate report source, fixture, function or native association differs')
    rows = report.get('results', [])
    names = [r.get('case') for r in rows]
    required = {r['case']: r['observation'] for r in expected['directCases']}
    performance = 'linear metadata lexer budgets and scaling'
    if (len(names) != 52 or len(set(names)) != 52 or set(names) != set(required) | {performance}
            or not all(r.get('pass') is True for r in rows)):
        raise RuntimeError('Candidate direct case partition differs')
    for row in rows:
        if row['case'] in required:
            observation = row.get('observation', {})
            if (observation != required[row['case']]
                    or any(type(observation.get(k)) is not bool for k in ['expected', 'actual', 'baseline'])):
                raise RuntimeError('Candidate direct input or Boolean evidence differs: ' + row['case'])
    samples = report.get('samples', [])
    slots = [(s.get('round'), s.get('kilobytes')) for s in samples]
    wanted = {(r, k) for r in [1, 2, 3] for k in [200, 400, 512, 1024]}
    if len(slots) != 12 or len(set(slots)) != 12 or set(slots) != wanted:
        raise RuntimeError('Candidate performance sample partition differs')
    for sample in samples:
        target = expected['performanceInputs'][str(sample['kilobytes'])]
        seconds = sample.get('seconds')
        if (type(sample.get('round')) is not int or type(sample.get('kilobytes')) is not int
                or sample.get('characters') != target['characters']
                or sample.get('inputSha256') != target['inputSha256'] or sample.get('valid') is not True
                or type(seconds) not in [int, float] or not math.isfinite(seconds) or not 0 < seconds <= budget):
            raise RuntimeError('Candidate actual performance sample differs')
    medians = {k: statistics.median(s['seconds'] for s in samples if s['kilobytes'] == k)
               for k in [200, 400, 512, 1024]}
    expected_performance = {'budgetSeconds': budget, 'maximumRatio': 3.0,
                            'ratio400over200': medians[400] / medians[200],
                            'ratio1024over512': medians[1024] / medians[512],
                            **{'median' + str(k): v for k, v in medians.items()}}
    actual = next(r['observation'] for r in rows if r['case'] == performance)
    if (expected_performance['ratio400over200'] > 3 or expected_performance['ratio1024over512'] > 3
            or set(actual) != set(expected_performance)
            or any(type(actual[k]) not in [int, float] or not math.isfinite(actual[k])
                   or not math.isclose(actual[k], v, rel_tol=1e-10, abs_tol=1e-12)
                   for k, v in expected_performance.items())):
        raise RuntimeError('Candidate timing medians or scaling differ from original samples')


def validate_lexer_mutations(value, host, expected):
    rows = value.get('results', [])
    applicability = value.get('applicability', [])
    if (value.get('nativeHost') != host['version'] or value.get('platform') != 'Win32NT'
            or value.get('runtime') != host['runtime']
            or [r.get('case') for r in rows] != ['exact-source direct healthy corpus', 'missing-final-coverage', 'skip-contiguous-coverage']
            or not all(r.get('pass') is True for r in rows)):
        raise RuntimeError('Direct lexer mutation identity or healthy corpus differs')
    required = {
        'missing-final-coverage': ['strict lexer trailing garbage after root', 'strict lexer trailing garbage after space'],
        'skip-contiguous-coverage': ['strict lexer gap before first token', 'strict lexer gap between tokens',
                                     'strict lexer gap between array values', 'strict lexer trailing garbage after root'],
    }
    negative_names = {r['case'] for r in expected['directCases'] if r['observation']['expected'] is False}
    for row in rows[1:]:
        failed = row.get('actualFailures', [])
        if (row.get('detected') is not True or row.get('positiveControlsPassed') is not True
                or type(row.get('fixtureExit')) is not int or row['fixtureExit'] != 1
                or row.get('requiredFailures') != required[row['case']]
                or not failed or len(failed) != len(set(failed))
                or not set(required[row['case']]) <= set(failed) <= negative_names):
            raise RuntimeError('Direct lexer mutation lacks the named actual failure: ' + row['case'])
    if (len(applicability) != 1 or applicability[0].get('case') != 'redundant-index-check-only'
            or applicability[0].get('survived') is not True
            or type(applicability[0].get('fixtureExit')) is not int or applicability[0]['fixtureExit'] != 0):
        raise RuntimeError('Redundant Index-only control lacks a complete surviving exit')


DISCOVERY_MUTATIONS = {
    'catch-to-absence': ['actual parser malformed', 'actual unknown only refuses before staging'],
    'wildcard-profile-probe': ['literal bracketed Firefox profile name'],
    'singleton-root-array-admitted': ['unsupported shape root-singleton-empty', 'unsupported shape root-singleton-new', 'actual singleton root array held with known peer'],
    'drop-builder-knowledge': ['actual target builder keeps states source and safe peers'],
    'default-all-admits-unknown': ['actual all mixed selection keeps known peer', 'actual unknown only refuses before staging'],
    'known-both-becomes-safe-new': ['actual parser both', 'actual both refuses before staging'],
    'held-summary-erased': ['actual all mixed selection keeps known peer'],
    'diagnostic-on-object-stream': ['actual parser malformed'],
    'insufficient-identity-proves-absence': ['insufficient identity empty-object', 'actual insufficient identity held with known peer'],
    'addons-key-case-folded': ['unsupported shape addons-key-case', 'actual wrong-case addons cannot certify absence'],
    'identity-key-case-folded': ['unsupported shape id-key-case', 'unsupported shape name-key-case', 'unsupported shape locale-key-case', 'actual wrong-case identity held with known peer'],
    'locale-name-case-folded': ['unsupported shape locale-name-key-case'],
    'strict-json-guard-bypassed': ['strict JSON trailing-comma', 'strict JSON trailing-comment', 'strict JSON single-quotes', 'strict JSON bare-key', 'actual duplicate keys cannot hide legacy from selection'],
    'duplicate-json-keys-admitted': ['strict JSON duplicate-addons', 'strict JSON escaped-duplicate-name', 'actual duplicate keys cannot hide legacy from selection'],
    'trailing-separators-admitted': ['actual strict validator object-trailing-comma', 'actual strict validator array-trailing-comma', 'strict JSON trailing-comma', 'strict JSON array-trailing-comma'],
}


def validate_discovery_mutations(value, native_version):
    rows = value.get('results', [])
    applicability = value.get('applicability', [])
    facts = value.get('hostParserCapabilities', {})
    capabilities = facts.get('accepts', {})
    if (facts.get('version') != native_version
            or type(facts.get('singletonIsArray')) is not bool
            or any(type(capabilities.get(k)) is not bool for k in
                   ['trailing-comma', 'array-trailing-comma', 'trailing-comment', 'single-quotes', 'bare-key'])):
        raise RuntimeError('Missing actual native parser capabilities')
    healthy_name = 'exact-source paired controls and assertions'
    names = [r.get('case') for r in rows + applicability]
    if (len(names) != 16 or len(set(names)) != 16
            or set(names) != set(DISCOVERY_MUTATIONS) | {healthy_name}):
        raise RuntimeError('Discovery mutation case partition differs')
    healthy = next(r for r in rows if r.get('case') == healthy_name)
    if healthy.get('pass_') is not True or type(healthy.get('fixtureExit')) is not int or healthy['fixtureExit'] != 0:
        raise RuntimeError('Discovery mutation healthy control failed')
    survivor = native_version.startswith('5.1.') and facts['singletonIsArray'] is True
    if [r.get('case') for r in applicability] != (['singleton-root-array-admitted'] if survivor else []):
        raise RuntimeError('Native applicability partition differs')
    for row in applicability:
        if (row.get('executed') is not True or row.get('detected') is not False
                or type(row.get('syntaxExit')) is not int or row['syntaxExit'] != 0
                or type(row.get('fixtureExit')) is not int or row['fixtureExit'] != 0
                or row.get('pairedControlsPass') is not True or row.get('failedCases') != []):
            raise RuntimeError('Singleton survivor lacks complete actual non-detection evidence')
    for row in rows:
        if row['case'] == healthy_name:
            continue
        required = DISCOVERY_MUTATIONS[row['case']]
        if row['case'] in ['strict-json-guard-bypassed', 'trailing-separators-admitted']:
            required = [name for name in required if not name.startswith('strict JSON ')
                        or capabilities[name[len('strict JSON '):]]]
        protected = [name for name in DISCOVERY_MUTATIONS[row['case']] if name not in required]
        if (not required or row.get('detected') is not True or row.get('pairedControlsPass') is not True
                or type(row.get('syntaxExit')) is not int or row['syntaxExit'] != 0
                or type(row.get('fixtureExit')) is not int or row['fixtureExit'] != 1
                or row.get('failedCases') != required or row.get('requiredFailedCases') != required
                or row.get('downstreamProtectedCases') != protected):
            raise RuntimeError('Discovery mutation evidence differs: ' + row['case'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--powershell', type=Path, required=True)
    ap.add_argument('--version', choices=['5.1', '7.6.6', '7.6.9'], required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if platform.system() != 'Windows':
        raise RuntimeError('This receipt requires native Windows')
    repo = args.repo.resolve(strict=True)
    baseline = args.baseline.resolve(strict=True)
    exe = args.powershell.resolve(strict=True)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    temp = out / 'temp'
    temp.mkdir()
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp), POWERSHELL_TELEMETRY_OPTOUT='1')
    for key in list(env):
        if key.lower() == 'psmodulepath':
            del env[key]
    sources = {
        'installer': repo / 'install.ps1',
        'baseline': baseline,
        'fixture': repo / 'tests/install-json-lexer.ps1',
        'reproducer': repo / 'tests/install-json-lexer-repro.ps1',
        'launcher': Path(__file__).resolve(),
        'lexerMutations': repo / 'tests/install-json-lexer-mutations.py',
        'discovery': repo / 'tests/install-discovery.ps1',
        'discoveryMutations': repo / 'tests/install-discovery-mutations.py',
        'expected': repo / 'tests/install-json-lexer-native-expected.json',
    }
    records = []
    facts = {'schema': 'r0013-lexer-native-v1', 'host': platform.platform(),
             'expectedVersion': args.version, 'powershellPath': str(exe),
             'powershellSha256': digest(exe), 'githubSha': env.get('GITHUB_SHA'),
             'githubRunId': env.get('GITHUB_RUN_ID'), 'githubRunAttempt': env.get('GITHUB_RUN_ATTEMPT'),
             'runnerImage': env.get('ImageVersion'), 'sources': {}, 'runs': records,
             'complete': False, 'disposition': 'incomplete', 'error': None}
    inputs = out / 'inputs'
    inputs.mkdir()
    for role, path in sources.items():
        raw = path.read_bytes()
        saved = inputs / (role + path.suffix)
        saved.write_bytes(raw)
        facts['sources'][role] = {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(),
                                  'bytes': len(raw), 'retained': str(saved)}
    if digest(baseline) != '56d91d484643b82a72e5714c678d2fe8640eb2b66e1d5350dd59889924d62471':
        raise RuntimeError('Original R0013 installer identity mismatch')
    if digest(sources['reproducer']) != '37e3081d92337fb1f799a7cabd423b36876c778d217eaadcdb844ed4676e2c7e':
        raise RuntimeError('Exact handoff reproducer identity mismatch')
    expected = json.loads(sources['expected'].read_text(encoding='utf-8'))
    if expected['discoveryFixtureSha256'] != digest(sources['discovery']):
        raise RuntimeError('Discovery expected-case fixture identity mismatch')

    def save():
        (out / 'receipt.json').write_text(json.dumps(facts, indent=2) + '\n', encoding='utf-8')

    def run(name, command, seconds):
        record = {'name': name, 'args': command, 'timeoutSeconds': seconds,
                  'startedUtc': time.time(), 'pid': None, 'exitCode': None,
                  'timedOut': False, 'cleanup': None, 'cleanupError': None}
        records.append(record)
        save()
        start = time.monotonic()
        stdout, stderr = out / (name + '.stdout.txt'), out / (name + '.stderr.txt')
        with stdout.open('xb') as so, stderr.open('xb') as se:
            child = subprocess.Popen(command, cwd=repo, env=env, stdin=subprocess.DEVNULL,
                                     stdout=so, stderr=se)
            record['pid'] = child.pid
            save()
            try:
                record['exitCode'] = child.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                record['timedOut'] = True
                try:
                    killed = subprocess.run(['taskkill.exe', '/PID', str(child.pid), '/T', '/F'],
                                            capture_output=True, timeout=15)
                    (out / (name + '.cleanup.stdout.txt')).write_bytes(killed.stdout)
                    (out / (name + '.cleanup.stderr.txt')).write_bytes(killed.stderr)
                    record['cleanup'] = {'command': 'taskkill /T /F', 'exitCode': killed.returncode}
                except Exception as error:
                    record['cleanupError'] = repr(error)
                try:
                    record['exitCode'] = child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    # Retain the abnormal tree-kill outcome; a root-only fallback
                    # is cleanup, never a complete or qualified receipt.
                    child.kill()
                    record['exitCode'] = child.wait(timeout=15)
                    record['cleanupError'] = (record['cleanupError'] or '') + '; root-only fallback required'
        record['elapsedSeconds'] = time.monotonic() - start
        record['stdout'] = {'path': str(stdout), 'bytes': stdout.stat().st_size, 'sha256': digest(stdout)}
        record['stderr'] = {'path': str(stderr), 'bytes': stderr.stat().st_size, 'sha256': digest(stderr)}
        save()
        return record

    prefix = [str(exe), '-NoLogo', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass']
    try:
        identity = run('identity', prefix + ['-Command',
            '[pscustomobject]@{version=$PSVersionTable.PSVersion.ToString();edition=$PSVersionTable.PSEdition;platform=[Environment]::OSVersion.Platform.ToString();runtime=[Environment]::Version.ToString();pshome=$PSHOME}|ConvertTo-Json -Compress'], 30)
        if identity['exitCode'] != 0 or identity['timedOut']:
            raise RuntimeError('Native host identity acquisition failed')
        host = json.loads((out / 'identity.stdout.txt').read_text(encoding='utf-8-sig'))
        facts['nativeIdentity'] = host
        version_ok = host['version'].startswith('5.1.') if args.version == '5.1' else host['version'] == args.version
        if not version_ok or host['platform'] != 'Win32NT':
            raise RuntimeError('Wrong native PowerShell host')
        original_repro = run('original-reproducer', prefix + ['-File', str(sources['reproducer']),
                             '-Installer', str(baseline), '-SizesKB', '20,50,100'], 150)
        original = run('original-regression', prefix + ['-File', str(sources['fixture']),
                       '-SourceFile', str(baseline), '-BaselineFile', str(baseline),
                       '-ReportPath', str(out / 'original-report.json')], 180)
        facts['originalResult'] = 'timeout' if original['timedOut'] else ('pass' if original['exitCode'] == 0 else 'failed')
        if digest(sources['installer']) == digest(baseline):
            facts['disposition'] = 'original-source diagnostic acquisition only'
        else:
            current = run('candidate-regression', prefix + ['-File', str(sources['fixture']),
                          '-SourceFile', str(sources['installer']), '-BaselineFile', str(baseline),
                          '-ReportPath', str(out / 'candidate-report.json')], 180)
            if current['exitCode'] != 0 or current['timedOut']:
                raise RuntimeError('Candidate regression fixture did not pass')
            report = json.loads((out / 'candidate-report.json').read_text(encoding='utf-8-sig'))
            validate_direct(report, expected, digest(sources['installer']), digest(sources['fixture']), host)
            checks = [
                ('lexer-mutations', [os.sys.executable, '-B', str(sources['lexerMutations']),
                                    str(sources['installer']), str(exe), '--baseline', str(baseline)], 90),
                ('discovery', prefix + ['-File', str(sources['discovery']), '-SourceFile', str(sources['installer'])], 180),
                ('discovery-mutations', [os.sys.executable, '-B', str(sources['discoveryMutations']),
                                        str(sources['installer']), str(exe)], 300),
            ]
            for name, command, deadline in checks:
                observed = run(name, command, deadline)
                if observed['exitCode'] != 0 or observed['timedOut']:
                    raise RuntimeError('Candidate integration control failed: ' + name)
                value = json.loads((out / (name + '.stdout.txt')).read_text(encoding='utf-8-sig'))
                if value.get('source') != digest(sources['installer']):
                    raise RuntimeError('Integration source association differs: ' + name)
                rows = value.get('results', [])
                if name == 'lexer-mutations':
                    validate_lexer_mutations(value, host, expected)
                elif name == 'discovery':
                    if (len(rows) != 79 or len({r.get('case') for r in rows}) != 79
                            or {r.get('case') for r in rows} != set(expected['discoveryCases'])
                            or not all(r.get('pass') is True for r in rows) or value.get('host') != host['version']
                            or value.get('platform') != 'Win32NT'):
                        raise RuntimeError('Original discovery receipt incomplete')
                else:
                    validate_discovery_mutations(value, host['version'])
            facts['disposition'] = 'candidate direct lexer, performance, discovery and mutation controls passed; wider integration separate'
        if any(r['cleanupError'] or (r['cleanup'] and r['cleanup']['exitCode'] != 0) for r in records):
            raise RuntimeError('Unresolved timeout cleanup outcome')
        if original_repro['exitCode'] != 0 and not original_repro['timedOut']:
            raise RuntimeError('Original reproducer failed before complete timing capture')
        for role, path in sources.items():
            if digest(path) != facts['sources'][role]['sha256']:
                raise RuntimeError('Input drift during native observation: ' + role)
        facts['complete'] = True
    except Exception as error:
        facts['error'] = repr(error)
    finally:
        save()
    print(json.dumps(facts, indent=2))
    return 0 if facts['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
