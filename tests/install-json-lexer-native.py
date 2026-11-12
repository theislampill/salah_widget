#!/usr/bin/env python3
"""Receive bounded original/candidate R0013 lexer observations on native Windows.

An original-source run is diagnostic acquisition, never product qualification.
The launcher retains original streams, exact sources, deadline and cleanup facts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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
            if (report['source'] != digest(sources['installer']) or report['fixture'] != digest(sources['fixture'])
                    or report['host'] != host['version'] or report['suite'] != 'All'
                    or len(report['results']) != 52 or not all(r['pass'] is True for r in report['results'])
                    or len(report['samples']) != 12):
                raise RuntimeError('Candidate report association or completeness failure')
            facts['disposition'] = 'candidate direct lexer semantics and performance passed; integration suites separate'
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
