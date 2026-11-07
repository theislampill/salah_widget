#!/usr/bin/env python3
"""Run source contracts with separate setup, execution, output and verdict state.

No provider/platform/pixel claim. See docs/state-contracts/R0017.md for schema
and compatibility. Each invocation requires a new receipt directory.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
NAMED = [
    'r0001-date-sinks.cjs', 'r0007-countdown.cjs', 'r0008-timezone.cjs', 'r0009-date-selection.cjs',
    'r000f-intent.cjs', 'r000f-reset.cjs', 'r0010-preferences.cjs', 'r0011-storage.cjs',
    'r0012-clipboard.cjs', 'r0012-effects.cjs', 'r0017-cloud-visibility.cjs', 'r0017-contract.cjs',
    'r0017-transport.cjs', 'r0017-weather.cjs', 'r0018-appearance.cjs', 'r0018-timetable-contrast.cjs',
    'r0019-date-disclosure.cjs', 'r001a-radio.cjs', 'r001d-lifecycle.cjs', 'r001f-deadline.cjs',
    'r0020-clock.cjs', 'r0021-reveal.cjs', 'r0022-baseline-balance.cjs', 'r0022-lunar-consumers.cjs',
    'r0023-metadata.cjs', 'r0025-continuity.cjs', 'r0025-lifecycle.cjs',
]
# Compatibility mapping: entries are dispositions, never a selection filter.
HISTORICAL = {}
SNAPSHOT_ONLY = {'r0021-reveal.cjs', 'r0022-lunar-consumers.cjs'}
INSTRUMENT = ('native-runner-contract', (sys.executable, '-m', 'unittest', 'discover',
              '-s', 'tests', '-p', 'test_native_regression_runner.py', '-v'))
HISTORY_INPUTS = {
    'r0018-timetable-contrast': ('ed5e7afbd2fcf7a59050817e2a561bcdbfa9043d:index.html',),
    'r0021-reveal': ('47c0fa0c6e32618f22b43b6a18717908b0de5f5e:index.html',),
    'r0022-baseline-balance': tuple(sha + ':index.html' for sha in (
        'fd2972ba64225fe9d6848e92497e6d0ed20ea624', '8b83df029966c203a503ab217d121c48b8ee6e8a',
        '18ff14860ff41c084b1db5f396bb62aa9c22b1be')),
    'r0023-metadata': tuple('fd2972ba64225fe9d6848e92497e6d0ed20ea624:' + path
                          for path in ('index.html', 'config.js')),
}
SCHEMA = 'salah-native-regressions/2'
FIELDS = ('tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo')
SETUP_MARKER = 'SETUP_INCOMPLETE: '


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def capture(command, root=None):
    """Bounded metadata read. No credential prompts, lazy fetch or mutation."""
    try:
        result = subprocess.run(command, cwd=root, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=10, check=False,
                                env=dict(os.environ, GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0'))
        if result.returncode == 0:
            return result.stdout.decode('utf-8').strip()
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        pass
    return None


def file_input(root, name):
    try:
        return {'path': name, 'available': True, 'sha256': digest(root / name)}
    except OSError as error:
        return {'path': name, 'available': False, 'reason': str(error)}


def source_identity(root, excluded=()):
    """Git tree plus actual modified/untracked bytes, or an unversioned snapshot.

    Unmaterialized unchanged paths retain Git identity; required command inputs
    are independently checked on disk. Output directories are not source.
    """
    head = capture(['git', 'rev-parse', '--verify', 'HEAD'], root)
    tree = capture(['git', 'rev-parse', '--verify', 'HEAD^{tree}'], root) if head else None
    if head:
        changed = capture(['git', 'diff', '--name-only', '-z', 'HEAD'], root)
        untracked = capture(['git', 'ls-files', '--others', '--exclude-standard', '-z'], root)
        if changed is None or untracked is None:
            return {'head': head, 'tree': tree, 'available': False,
                    'reason': 'working source census unavailable'}
        paths = sorted(set(filter(None, (changed + '\0' + untracked).split('\0'))))
    else:
        paths = sorted(str(path.relative_to(root)) for path in root.rglob('*') if path.is_file())
    excluded = tuple(Path(path).resolve() for path in excluded)
    paths = [name for name in paths
             if not any((root / name).resolve().is_relative_to(path) for path in excluded)]
    return {'head': head, 'tree': tree, 'available': True,
            'kind': 'git-tree-with-working-overlay' if head else 'unversioned-file-snapshot',
            'workingChanges': [file_input(root, name) for name in paths]}


def host_identity():
    return {'platform': platform.platform(), 'python': platform.python_version(),
            'pythonExecutable': sys.executable, 'node': capture(['node', '--version'])}


def history_input(root, locator):
    # Exact acquisition is a separate action. Current source is never a fallback.
    kind = capture(['git', 'cat-file', '-t', locator], root)
    blob = capture(['git', 'rev-parse', '--verify', locator], root) if kind == 'blob' else None
    return {'locator': locator, 'available': kind == 'blob' and blob is not None,
            'blob': blob, 'reason': None if blob else 'exact Git object/path unavailable'}


def build_plan(root, selected=None):
    glob = tuple(str(path.relative_to(root)) for path in sorted((root / 'tests').glob('*.test.cjs')))
    specs = [('native-test-glob', ('node', '--test', '--test-reporter=tap',
              '--test-concurrency=1', *glob), glob, 'auto', None)]
    for filename in NAMED:
        argv = ('node', '--test-reporter=tap', 'tests/' + filename)
        if filename in SNAPSHOT_ONLY:
            argv += ('--cp8-snapshot-only',)
        specs.append((Path(filename).stem, argv, ('tests/' + filename, 'index.html', 'config.js'),
                      'auto', HISTORICAL.get(filename)))
    if INSTRUMENT:
        specs.insert(0, (*INSTRUMENT, ('tests/test_native_regression_runner.py',
                      'tools/cp9/run_native_regressions.py'), 'unittest', None))
    names = [spec[0] for spec in specs]
    if len(names) != len(set(names)):
        raise ValueError('duplicate command identity in selected population')
    if selected is not None:
        if not selected or len(selected) != len(set(selected)) or set(selected) - set(names):
            raise ValueError('selection must contain distinct known command names')
        specs = [spec for spec in specs if spec[0] in set(selected)]
    # Freeze selection before setup, execution or outcomes can influence it.
    return tuple(specs)


def output_result(format_name, status='INCOMPLETE', counts=None,
                  reason='unparsed or incomplete output', exclusions=()):
    return {'format': format_name, 'status': status, 'executionProven': status in ('PASS', 'FAIL'),
            'counts': counts or {}, 'reason': reason, 'exclusions': list(exclusions)}


def terminal_json(text):
    """Admit a complete final object. JSON offsets never own elapsed timing."""
    # A leading object must be complete in its entirety. Never salvage a nested
    # success object from a truncated outer envelope. Prefixed summaries start
    # at column zero in the retained fixtures.
    offsets = [0] if text.lstrip().startswith('{') else [m.start() for m in re.finditer(r'(?m)^\{', text)]
    for json_offset in offsets:
        try:
            value = json.loads(text[json_offset:])
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict):
            return value
    return None


def classify_output(text, protocol='auto'):
    exclusions = re.findall(r'^SKIP_(?:HISTORICAL|SUPERSEDED|EXPLICIT) .+$', text, re.M)
    exclusions += re.findall(r'^\s*(?:ok|not ok) .+ # (?:SKIP|TODO)\b.*$', text, re.M | re.I)
    if protocol == 'unittest':
        ran = re.search(r'^Ran (\d+) tests? in [\d.]+s$', text, re.M)
        if ran and int(ran[1]) > 0 and re.search(r'^OK\s*$', text, re.M):
            return output_result('unittest', 'PASS', {'tests': int(ran[1])},
                                 'complete unittest terminal')
        return output_result('unittest', reason='unittest completion not proved')

    tap = {field: re.findall(r'^# ' + field + r' (\d+)$', text, re.M) for field in FIELDS}
    if any(tap.values()):
        if any(len(values) != 1 for values in tap.values()):
            return output_result('tap', reason='missing/ambiguous TAP totals', exclusions=exclusions)
        counts = {field: int(values[0]) for field, values in tap.items()}
        plan = re.findall(r'^1\.\.(\d+)\s*$', text, re.M)
        cases = re.findall(r'^(?:ok|not ok) (\d+)\b', text, re.M)
        failed_cases = [line for line in text.splitlines() if re.match(r'^\s*not ok \d+\b', line)
                        and not re.search(r' # (?:TODO|SKIP)\b', line, re.I)]
        if (len(plan) != 1 or list(map(int, cases)) != list(range(1, int(plan[0]) + 1))
                or counts['tests'] < 1 or sum(counts[field] for field in FIELDS[1:]) != counts['tests']
                or len(exclusions) < counts['skipped'] + counts['todo']
                or (failed_cases and not counts['fail'])):
            return output_result('tap', counts=counts, reason='TAP population/completion mismatch',
                                 exclusions=exclusions)
        status = 'FAIL' if counts['fail'] else 'INCOMPLETE' if counts['cancelled'] or not counts['pass'] else 'PASS'
        return output_result('tap', status, counts, 'complete TAP terminal', exclusions)

    payload = terminal_json(text)
    pass_lines = re.findall(r'^PASS\s+(.+)$', text, re.M)
    fail_lines = re.findall(r'^FAIL\s+(.+)$', text, re.M)
    if payload is None:
        return output_result('unparsed', counts={'passLines': len(pass_lines),
                             'failLines': len(fail_lines), 'unparsedOutput': True}, exclusions=exclusions)
    if isinstance(payload.get('results'), list):
        items = payload['results']
        if not items or any(not isinstance(item, dict) for item in items):
            return output_result('json-results', reason='empty/invalid case population', exclusions=exclusions)
        names = [item.get('name') for item in items]
        states = [item.get('status', item.get('result')) for item in items]
        if (any(not isinstance(name, str) or not name for name in names) or len(set(names)) != len(names)
                or any(state not in ('PASS', 'FAIL', 'INCOMPLETE') for state in states)
                or any('status' in item and 'result' in item and item['status'] != item['result'] for item in items)):
            return output_result('json-results', reason='invalid/duplicate case identities or states',
                                 exclusions=exclusions)
        setup_failures = [item for item, state in zip(items, states)
                          if state != 'PASS' and SETUP_MARKER in str(item.get('error', ''))]
        failures = states.count('FAIL') - sum(item.get('status', item.get('result')) == 'FAIL'
                                              for item in setup_failures)
        counts = {'passCases': states.count('PASS'), 'failCases': states.count('FAIL')}
        status = 'FAIL' if failures or fail_lines else 'INCOMPLETE' if setup_failures or 'INCOMPLETE' in states else 'PASS'
        result = output_result('json-results', status, counts, 'complete named result array', exclusions)
        if setup_failures:
            result['setupFailure'] = '; '.join(str(item['error']) for item in setup_failures)
    else:
        passed, failed = payload.get('pass', payload.get('passed')), payload.get('fail', payload.get('failed'))
        integer = lambda value: type(value) is int and value >= 0
        if not integer(passed) or not integer(failed) or passed + failed == 0:
            return output_result('json-summary', reason='no completed assertion population', exclusions=exclusions)
        if (passed != len(pass_lines) or failed != len(fail_lines)
                or len(set(pass_lines + fail_lines)) != passed + failed):
            return output_result('json-summary', reason='case lines disagree with terminal counts', exclusions=exclusions)
        if 'cases' in payload and (not integer(payload['cases']) or payload['cases'] != passed + failed):
            return output_result('json-summary', reason='declared case count mismatch', exclusions=exclusions)
        counts = {'passLines': passed, 'failLines': failed}
        setup_lines = [line for line in fail_lines if SETUP_MARKER in line]
        status = 'FAIL' if failed > len(setup_lines) else 'INCOMPLETE' if setup_lines else 'PASS'
        result = output_result('json-summary', status, counts, 'complete case lines and matching JSON terminal', exclusions)
        if setup_lines:
            result['setupFailure'] = '; '.join(setup_lines)
    if any(field in payload for field in ('terminal', 'declared', 'executed', 'missing')):
        total = sum(result['counts'].values())
        if (payload.get('terminal') is not True or type(payload.get('declared')) is not int
                or payload['declared'] != total or payload.get('executed') != total or payload.get('missing') != 0):
            return output_result(result['format'], counts=result['counts'],
                                 reason='declared execution is incomplete/inconsistent', exclusions=exclusions)
    if payload.get('status') == 'FAIL' or (payload.get('status') == 'INCOMPLETE' and result['status'] != 'FAIL'):
        result['status'] = payload['status']
        result['executionProven'] = result['status'] == 'FAIL'
    return result


def check_setup(root, spec):
    name, _, inputs, _, _ = spec
    files = [file_input(root, path) for path in inputs]
    history = [history_input(root, locator) for locator in HISTORY_INPUTS.get(name, ())]
    ready = bool(inputs) and all(row['available'] for row in files + history)
    return {'status': 'READY' if ready else 'INCOMPLETE', 'files': files, 'history': history,
            'reason': None if ready else 'required source/test or exact historical input unavailable'}


def execute_command(root, out, spec, timeout, stop_reason=None):
    name, argv, _, protocol, disposition = spec
    log = out / (name + '.log')
    row = {'name': name, 'command': list(argv), 'exitCode': None, 'seconds': 0.0,
           'counts': {}, 'log': log.name, 'explicitExclusions': [], 'status': 'INCOMPLETE',
           'execution': {'state': 'not-started', 'returnCode': None}, 'lifecycle': ['selected']}
    row['setup'] = check_setup(root, spec)
    row['lifecycle'].append('setup-checked')
    if disposition:
        if (not isinstance(disposition, dict) or not disposition.get('reason')
                or not (disposition.get('replacement') or disposition.get('residual'))):
            row['reason'] = 'exclusion lacks reason and replacement/residual'
        else:
            row['status'] = 'HISTORICAL_EXCLUDED'
            row['reason'] = disposition['reason']
            row['applicability'] = disposition
            row['explicitExclusions'] = [disposition['reason']]
    elif stop_reason or row['setup']['status'] != 'READY':
        row['reason'] = stop_reason or row['setup']['reason']
    else:
        row['lifecycle'].append('running')
        started_elapsed = time.monotonic()
        with log.open('w', encoding='utf-8') as stream:
            try:
                child = subprocess.run(list(argv), cwd=root, stdout=stream,
                                       stderr=subprocess.STDOUT, timeout=timeout)
                row['exitCode'] = child.returncode
                row['execution'] = {'state': 'exited', 'returnCode': child.returncode}
            except subprocess.TimeoutExpired:
                row['exitCode'] = 124  # Compatibility sentinel, not an observed return code.
                row['execution']['state'] = 'timed-out'
                row['reason'] = 'child exceeded ' + str(timeout) + ' second bound; completion unproved'
            except OSError as error:
                row['exitCode'] = 127
                row['execution']['state'] = 'launch-failed'
                row['reason'] = str(error)
                stream.write('\nRUNNER launch-failed: ' + str(error) + '\n')
            except KeyboardInterrupt:
                row['exitCode'] = 130
                row['execution']['state'] = 'cancelled'
                row['reason'] = 'invocation cancelled; completion unproved'
        row['seconds'] = time.monotonic() - started_elapsed
        row['lifecycle'].append(row['execution']['state'])
        try:
            text = log.read_text(encoding='utf-8')
            output = classify_output(text, protocol)
        except UnicodeError:
            text = ''
            output = output_result('unparsed', reason='output is not valid UTF-8; raw log retained')
        row['output'] = output
        row['counts'] = output['counts']
        row['explicitExclusions'] = output['exclusions']
        if row['execution']['state'] == 'exited':
            setup_exception = re.search(r'^(?:SetupError: )?SETUP_INCOMPLETE: .+$', text, re.M)
            setup_failure = output.get('setupFailure') or (setup_exception[0] if setup_exception else None)
            if setup_failure and output['status'] != 'FAIL':
                row['setup']['status'] = 'INCOMPLETE'
                row['setup']['reason'] = setup_failure
                row['reason'] = setup_failure
            else:
                row['status'] = 'FAIL' if row['exitCode'] != 0 else output['status']
                row['reason'] = 'nonzero child exit' if row['exitCode'] != 0 else output['reason']
    if not log.exists():
        log.write_text(row['reason'] + '\n', encoding='utf-8')
    if 'output' not in row:
        row['output'] = output_result('not-run', reason=row['reason'])
    row['lifecycle'].extend(['output-classified', 'terminal'])
    return row


def summarize(plan, records):
    if [(spec[0], list(spec[1])) for spec in plan] != [(row['name'], row['command']) for row in records]:
        raise ValueError('selected population does not have exactly one ordered terminal record')
    if any(row['lifecycle'].count('terminal') != 1 or row['lifecycle'][-1] != 'terminal' for row in records):
        raise ValueError('invalid command terminal lifecycle')
    statuses = [row['status'] for row in records]
    if 'FAIL' in statuses:
        return 'FAIL'
    if 'INCOMPLETE' in statuses or 'PASS' not in statuses:
        return 'INCOMPLETE'
    if any(status not in ('PASS', 'HISTORICAL_EXCLUDED', 'NOT_APPLICABLE') for status in statuses):
        raise ValueError('unknown terminal status')
    return 'PASS'


def run(root, out, *, selected=None, timeout=180):
    root, out = Path(root).resolve(), Path(out).resolve()
    if timeout <= 0:
        raise ValueError('timeout must be positive')
    plan = build_plan(root, selected)
    # Existing receipts are immutable input, never an output slot to overwrite.
    out.mkdir(parents=True, exist_ok=False)
    source = source_identity(root, excluded=(out,))
    records = []
    result = {'schema': SCHEMA, 'status': 'RUNNING', 'commands': records,
              'plannedCommands': [{'name': spec[0], 'command': list(spec[1])} for spec in plan],
              'identity': {'invocation': str(uuid.uuid4()), 'startedAt': datetime.now(timezone.utc).isoformat(),
                           'source': source, 'runnerSha256': digest(__file__), 'host': host_identity()},
              'continuationPolicy': 'continue after terminal fixture results; stop later launches after timeout, launch failure or cancellation',
              'notRunHistorical': HISTORICAL,
              'scope': 'Only explicitly selected source-contract commands. Counts are descriptive; exclusions are not passes. No native pixels, live provider, platform, performance or delivery certification.'}

    def save():
        temporary = out / 'results.json.tmp'
        temporary.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        temporary.replace(out / 'results.json')

    save()
    stop_reason = None
    for spec in plan:
        row = execute_command(root, out, spec, timeout, stop_reason)
        records.append(row)
        if row['execution']['state'] in ('timed-out', 'launch-failed', 'cancelled'):
            stop_reason = 'not launched after ' + row['name'] + ': ' + row['execution']['state']
        save()
        print(row['name'], row['exitCode'], row['status'], row['counts'], flush=True)
    result['status'] = summarize(plan, records)
    result['sourceUnchanged'] = source == source_identity(root, excluded=(out,))
    if not result['sourceUnchanged'] or source.get('available') is False:
        result['status'] = 'INCOMPLETE'
        result['identityError'] = 'source identity changed or was unavailable during invocation'
    save()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True,
                        help='new receipt directory; existing directories are refused')
    parser.add_argument('--select', nargs='+',
                        help='explicit names; default is retained population plus evaluator controls')
    parser.add_argument('--timeout', type=float, default=180, help='per-command seconds, default 180')
    args = parser.parse_args(argv)
    try:
        result = run(args.root, args.output, selected=args.select, timeout=args.timeout)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
