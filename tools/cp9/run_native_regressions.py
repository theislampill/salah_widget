#!/usr/bin/env python3
"""Run source contracts with separate setup, execution, output and verdict state.

No provider/platform/pixel claim. See docs/state-contracts/R0017.md for schema
and compatibility. Each invocation requires a new receipt directory.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
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
    'r0021-reveal': ('18ff14860ff41c084b1db5f396bb62aa9c22b1be:index.html',),
    'r0022-baseline-balance': tuple(sha + ':index.html' for sha in (
        'fd2972ba64225fe9d6848e92497e6d0ed20ea624', '8b83df029966c203a503ab217d121c48b8ee6e8a',
        '18ff14860ff41c084b1db5f396bb62aa9c22b1be', 'f71fef6ccf7e4efcb57b5a26688d2360461a3253')),
    'r0023-metadata': tuple('fd2972ba64225fe9d6848e92497e6d0ed20ea624:' + path
                          for path in ('index.html', 'config.js')),
}
SCHEMA = 'salah-native-regressions/2'
FIELDS = ('tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo')
SETUP_MARKER = 'SETUP_INCOMPLETE: '
# These names are retained obligations, not a green waiver. See the contract map
# for observed partial replacement coverage and the exact residual per case.
CASE_RESIDUALS = {
    'ordinary held star positions remain stable across a healthy render':
        ('r0021-reveal', 'R17-STAR-01', 'actual ordinary host publication with accepted catalogue geometry'),
    'first accepted target cannot retain the unresolved-coordinate projection':
        ('r0021-reveal', 'R17-STAR-02', 'unavailable-to-first-valid target through real catalogue publication'),
    'same-day explicit preview anchor correction reprojects accepted stars':
        ('r0021-reveal', 'R17-STAR-03', 'explicit host anchor seek and stale-completion rejection with real catalogue output'),
    'glints release wash with held star projection':
        ('r0022-lunar-consumers', 'R17-STAR-04', 'physical lunar background reaches stellar contrast without stale wash'),
    'ordinary render refreshes star appearance while held projection stays fixed':
        ('r0022-lunar-consumers', 'R17-STAR-05', 'ordinary host propagates physical lunar-light changes into current stellar appearance'),
    'R0003 join: obsolete acquisition cannot install/persist or clear successor attempt':
        ('native-test-glob', 'R0003', 'retained TODO: obsolete acquisition join is not implemented by this evaluator repair'),
    'R000D join: unresolving JSON and image bodies settle within accepted deadline':
        ('native-test-glob', 'R000D', 'retained TODO: body deadline join remains unexecuted'),
    'R0024 join: fresh current model eligibility remains positive while final live strong-particle permission is withheld':
        ('native-test-glob', 'R0024', 'retained TODO: model eligibility and particle-permission join remains unexecuted'),
    'native/browser qualification: fixture chip/data-fx, zero-axis consumer, layout/moon/motion pixel evidence':
        ('native-test-glob', 'R0017-native', 'retained TODO: browser/pixel observations require their own qualified native run'),
}

# R0028: registered population beyond NAMED and the exact expected-failure ledger.
# Both are repository data reviewed like source (docs/state-contracts/R0028.md). A root
# that carries this runner (the repository) must carry the population manifest; isolated
# fixture roots without either file keep the R0017 behaviour unchanged.
POPULATION_FILE = 'tests/regression-population.json'
LEDGER_FILE = 'tests/expected-failures.json'
POPULATION_SCHEMA = 'salah-regression-population/1'
LEDGER_SCHEMA = 'salah-expected-failures/1'
DECLARED = 'PASS_WITH_DECLARED_FAILURES'
CAUSE_CLASSES = ('harness-gap', 'stale-pin', 'stale-expectation-vs-accepted-contract',
                 'unadopted-contract', 'undetermined')
ENTRY_KINDS = ('case-fail', 'case-not-executed', 'command-incomplete')
ENTRY_FIELDS = ('id', 'status', 'kind', 'command', 'case', 'messagePrefix', 'firstRed', 'causeClass',
                'evidence', 'owner', 'disposition', 'trigger')
CONDITIONS = ('symlink-unavailable',)
EXTENDED_PROTOCOLS = ('case-lines', 'json-lines', 'json-cases', 'unittest-cases', 'scientific')
# Completion reasons that prove the classified output is a whole terminal population.
COMPLETE_REASONS = ('complete TAP terminal', 'complete named result array',
                    'complete case lines and matching JSON terminal')
CENSUS_PATTERNS = ('tests/*.cjs', 'tests/*.js', 'tests/*.mjs', 'tests/*.py', 'tests/**/*.test.cjs',
                   'tests/**/*.test.mjs', 'tests/**/*_test.py', 'tests/**/*.cjs', 'moon/tests/*.test.cjs',
                   'moon/tests/*.py', 'tools/**/test_*.py')


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


def build_plan(root, selected=None, out=None, manifest=None):
    glob = tuple(str(path.relative_to(root)) for path in sorted((root / 'tests').glob('*.test.cjs')))
    specs = [('native-test-glob', ('node', '--test', '--test-reporter=tap',
              '--test-concurrency=1', *glob), glob, 'auto', None)]
    overrides = (manifest or {}).get('protocols', {})
    for filename in NAMED:
        argv = ('node', '--test-reporter=tap', 'tests/' + filename)
        if filename in SNAPSHOT_ONLY:
            argv += ('--cp8-snapshot-only',)
        override = overrides.get(Path(filename).stem, {})
        specs.append((Path(filename).stem, argv, ('tests/' + filename, 'index.html', 'config.js'),
                      override.get('protocol', 'auto'), HISTORICAL.get(filename),
                      {key: override[key] for key in ('expectedCases',) if key in override}))
    if manifest:
        specs.extend(population_specs(manifest, out))
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
    # Never salvage a nested success object from a truncated outer envelope,
    # including an indented envelope after a textual prefix.
    offsets = [m.end() - 1 for m in re.finditer(r'(?m)^[ \t]*\{', text)]
    if text.lstrip().startswith('{'):
        offsets = sorted(set([len(text) - len(text.lstrip()), *offsets]))
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON property')
            result[key] = value
        return result

    def diagnostic(value):
        # These two existing callers print non-verdict metadata before their
        # terminal summary. Admit their exact shapes, never an earlier result.
        if set(value) == {'realElapsedMs', 'instrument'}:
            elapsed = value['realElapsedMs']
            return type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed >= 0 and isinstance(value['instrument'], str)
        return (set(value) == {'consumer', 'storedSource', 'storedOrigin', 'title', 'bytesUnchanged', 'native'}
                and type(value['bytesUnchanged']) is bool and value['native'] == 'NOT_RUN'
                and all(isinstance(value[key], str) for key in ('consumer', 'storedSource', 'storedOrigin', 'title')))

    decoder = json.JSONDecoder(object_pairs_hook=unique_object)
    consumed = 0
    for json_offset in offsets:
        if json_offset < consumed:
            continue
        try:
            value, consumed = decoder.raw_decode(text, json_offset)
        except (ValueError, TypeError, RecursionError):
            return None
        if not isinstance(value, dict):
            return None
        if not text[consumed:].strip():
            return value
        if not diagnostic(value) or text[consumed:].split('\n', 1)[0].strip():
            return None
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
        cases = list(re.finditer(r'^( *)(ok|not ok) (\d+)\b[^\n]*', text, re.M))
        top = [int(case[3]) for case in cases if not case[1]]
        suites = re.findall(r'^# suites (\d+)$', text, re.M)
        suite_count = int(suites[0]) if len(suites) == 1 else 0
        leaves = []
        setup_failures = []
        observed_suites = 0
        for index, case in enumerate(cases):
            end = cases[index + 1].start() if index + 1 < len(cases) else len(text)
            diagnostic = text[case.end():end]
            if re.search(r'^' + case[1] + r"  type: ['\"]suite['\"]$", diagnostic, re.M):
                observed_suites += 1
            else:
                leaves.append(case)
                if case[2] == 'not ok' and re.search(r'^' + case[1] + r"  code: ['\"]SETUP_INCOMPLETE['\"]$", diagnostic, re.M):
                    error = re.search(r'^' + case[1] + r'  error: (.+)$', diagnostic, re.M)
                    setup_failures.append(case[0] + ': ' + (error[1] if error else SETUP_MARKER + 'adapter setup failed'))
        directives = [re.search(r' # (TODO|SKIP)\b', case[0], re.I) for case in leaves]
        ordinary = [case for case, directive in zip(leaves, directives) if not directive]
        observed = {field: sum(bool(directive and directive[1].lower() == field)
                               for directive in directives) for field in ('skip', 'todo')}
        if (len(plan) != 1 or not top or top != list(range(1, int(plan[0]) + 1))
                or len(suites) > 1 or observed_suites != suite_count
                or len(leaves) != counts['tests'] or counts['tests'] < 1
                or sum(counts[field] for field in FIELDS[1:]) != counts['tests']
                or observed['skip'] != counts['skipped'] or observed['todo'] != counts['todo']
                or sum(case[2] == 'ok' for case in ordinary) != counts['pass']
                or sum(case[2] == 'not ok' for case in ordinary) != counts['fail'] + counts['cancelled']):
            return output_result('tap', counts=counts, reason='TAP population/completion mismatch',
                                 exclusions=exclusions)
        status = 'FAIL' if counts['fail'] > len(setup_failures) else 'INCOMPLETE' if setup_failures or counts['cancelled'] or not counts['pass'] else 'PASS'
        result = output_result('tap', status, counts, 'complete TAP terminal', exclusions)
        if setup_failures:
            result['setupFailure'] = '; '.join(setup_failures)
        return result

    payload = terminal_json(text)
    pass_lines = re.findall(r'^PASS\s+(.+)$', text, re.M)
    fail_lines = re.findall(r'^FAIL\s+(.+)$', text, re.M)
    if payload is None:
        return output_result('unparsed', counts={'passLines': len(pass_lines),
                             'failLines': len(fail_lines), 'unparsedOutput': True}, exclusions=exclusions)
    if payload.get('status') not in (None, 'PASS', 'FAIL', 'INCOMPLETE'):
        return output_result('json', reason='unknown outer result status', exclusions=exclusions)
    if any(first in payload and second in payload and payload[first] != payload[second]
           for first, second in (('pass', 'passed'), ('fail', 'failed'))):
        return output_result('json', reason='conflicting summary aliases', exclusions=exclusions)
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
        supplied_counts = {'pass': states.count('PASS'), 'passed': states.count('PASS'),
                           'fail': states.count('FAIL'), 'failed': states.count('FAIL'), 'cases': len(states)}
        if any(field in payload and (type(payload[field]) is not int or payload[field] != expected)
               for field, expected in supplied_counts.items()):
            return output_result('json-results', reason='supplied counts contradict named case population',
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
    name, _, inputs, _, _ = spec[:5]
    files = [file_input(root, path) for path in inputs]
    history = [history_input(root, locator) for locator in HISTORY_INPUTS.get(name, ())]
    ready = bool(inputs) and all(row['available'] for row in files + history)
    return {'status': 'READY' if ready else 'INCOMPLETE', 'files': files, 'history': history,
            'reason': None if ready else 'required source/test or exact historical input unavailable'}


def case_dispositions(command, exclusions):
    records = []
    for line in exclusions:
        if line.lstrip().startswith(('ok ', 'not ok ')):
            name = re.sub(r'^\s*(?:not )?ok \d+\s*-?\s*', '', line).split(' # ', 1)[0]
        else:
            name = line.split(' ', 1)[1].split(' — ', 1)[0]
        known = CASE_RESIDUALS.get(name)
        scoped = known and known[0] == command
        records.append({'name': name, 'scope': command, 'status': 'INCOMPLETE',
                        'reason': 'retained unexecuted observation' if scoped else 'unregistered exclusion',
                        'residual': known[2] if scoped else 'required observation has no admitted replacement evidence',
                        'reference': 'docs/state-contracts/R0017.md#' + known[1].lower() if scoped else None,
                        'reported': line})
    return records


def strict_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON property ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique)


def load_population(root):
    """Return (manifest or None, setup errors). Never selects by outcome."""
    path = root / POPULATION_FILE
    if not path.exists():
        required = (root / 'tools/cp9/run_native_regressions.py').exists()
        return None, ['population manifest missing: ' + POPULATION_FILE] if required else []
    try:
        manifest = strict_json(path)
    except (OSError, ValueError) as error:
        return None, ['population manifest unreadable: ' + str(error)]
    errors = []
    if manifest.get('schema') != POPULATION_SCHEMA:
        errors.append('population schema must be ' + POPULATION_SCHEMA)
    seen = set()
    for entry in manifest.get('commands', []):
        name = entry.get('name')
        if not isinstance(name, str) or not name or name in seen:
            errors.append('population command name missing or duplicated: ' + repr(name))
        seen.add(name)
        if (not isinstance(entry.get('argv'), list) or not entry['argv']
                or not all(isinstance(arg, str) and arg for arg in entry['argv'])):
            errors.append(str(name) + ': argv must be a nonempty string list')
        protocol = entry.get('protocol')
        if protocol not in ('auto', 'unittest') + EXTENDED_PROTOCOLS:
            errors.append(str(name) + ': unknown terminal protocol ' + repr(protocol))
        if protocol == 'case-lines' and (type(entry.get('expectedCases')) is not int or entry['expectedCases'] < 1):
            errors.append(str(name) + ': case-lines requires a positive declared expectedCases')
        if not isinstance(entry.get('covers', []), list) or not isinstance(entry.get('inputs', []), list):
            errors.append(str(name) + ': covers/inputs must be lists')
    for key in ('modules', 'exclusions'):
        for entry in manifest.get(key, []):
            if not isinstance(entry.get('path'), str) or not entry.get('reason') or (key == 'exclusions' and not entry.get('owner')):
                errors.append(key + ' entry needs path, reason' + (' and owner' if key == 'exclusions' else '') + ': ' + repr(entry))
    for name, override in manifest.get('protocols', {}).items():
        if name.replace('.cjs', '') + '.cjs' not in NAMED or override.get('protocol') not in ('auto',) + EXTENDED_PROTOCOLS:
            errors.append('protocol override must name a NAMED command and a known protocol: ' + name)
        if override.get('protocol') == 'case-lines' and (type(override.get('expectedCases')) is not int or override['expectedCases'] < 1):
            errors.append(name + ': case-lines requires a positive declared expectedCases')
    return manifest, errors


def resolve(arg, out):
    replacements = {'{python}': sys.executable, '{receipt}': str(out) if out else '{receipt}'}
    for key, value in replacements.items():
        arg = arg.replace(key, value)
    return arg


def population_specs(manifest, out):
    specs = []
    for entry in manifest.get('commands', []):
        options = {key: entry[key] for key in ('env', 'timeout', 'expectedCases', 'resultsDir') if key in entry}
        if 'resultsDir' in options:
            options['resultsDir'] = resolve(options['resultsDir'], out)
        argv = tuple(resolve(arg, out) for arg in entry['argv'])
        specs.append((entry['name'], argv, tuple(entry.get('inputs', [])), entry['protocol'], None, options))
    return specs


def census(root, plan, manifest):
    """Every instrument-shaped file is selected, a declared module, or a registered exclusion."""
    covered = set()
    for command in plan:
        covered.update(arg.replace('\\', '/') for arg in command[1] if not str(arg).startswith('-'))
        covered.update(command[2])
    for entry in manifest.get('commands', []):
        covered.update(entry.get('covers', []))
    declared = {entry['path'] for key in ('modules', 'exclusions') for entry in manifest.get(key, [])}
    found = sorted({path.relative_to(root).as_posix() for pattern in CENSUS_PATTERNS
                    for path in root.glob(pattern) if path.is_file()})
    errors = ['unregistered instrument (neither selected, module nor exclusion): ' + path
              for path in found if path not in covered and path not in declared]
    errors += ['registered module/exclusion path does not exist: ' + path
               for path in sorted(declared) if not (root / path).is_file()]
    errors += ['path is both selected and declared module/exclusion: ' + path
               for path in sorted(declared & covered)]
    # The glob command is derived from disk; the manifest pins its expected members so a
    # deleted (or silently added) glob file is a setup error, not a smaller green population.
    expected = manifest.get('nativeTestGlob')
    glob = sorted(path.relative_to(root).as_posix() for path in (root / 'tests').glob('*.test.cjs'))
    if not isinstance(expected, list):
        errors.append('population manifest must list nativeTestGlob members')
    else:
        errors += ['registered glob member missing: ' + path for path in sorted(set(expected) - set(glob))]
        errors += ['glob member not registered in nativeTestGlob: ' + path for path in sorted(set(glob) - set(expected))]
    return errors


def load_ledger(root, known, excluded):
    """Exact per-case expected-failure entries. Malformed input is a setup error, never a pass."""
    path = root / LEDGER_FILE
    if not path.exists():
        return [], [], []
    try:
        ledger = strict_json(path)
    except (OSError, ValueError) as error:
        return [], [], ['ledger unreadable: ' + str(error)]
    errors, active, retired, ids, keys = [], [], [], set(), set()
    if ledger.get('schema') != LEDGER_SCHEMA:
        errors.append('ledger schema must be ' + LEDGER_SCHEMA)
    for entry in ledger.get('entries', []):
        label = repr(entry.get('id'))
        missing = [field for field in ENTRY_FIELDS if field not in entry or (field != 'case' and not entry[field])]
        if missing:
            errors.append(label + ': missing field(s) ' + ', '.join(missing))
            continue
        if set(entry) - set(ENTRY_FIELDS) - {'condition', 'notes', 'discriminator', 'retiredBy'}:
            errors.append(label + ': unknown field(s) ' + ', '.join(sorted(set(entry) - set(ENTRY_FIELDS))))
        if entry['id'] in ids:
            errors.append(label + ': duplicate id')
        ids.add(entry['id'])
        if entry['status'] not in ('active', 'retired') or entry['kind'] not in ENTRY_KINDS:
            errors.append(label + ': status must be active|retired and kind one of ' + '|'.join(ENTRY_KINDS))
        if entry['causeClass'] not in CAUSE_CLASSES:
            errors.append(label + ': unknown causeClass ' + repr(entry['causeClass']))
        if not re.fullmatch(r'R[0-9A-Z]{4}|pending-owner-decision', str(entry['owner'])):
            errors.append(label + ': owner must be Rxxxx or pending-owner-decision')
        if entry['causeClass'] == 'undetermined' and not entry.get('discriminator'):
            errors.append(label + ': undetermined entry needs a named discriminator')
        if entry.get('condition') is not None and entry['condition'] not in CONDITIONS:
            errors.append(label + ': unknown condition ' + repr(entry['condition']))
        case, prefix = entry['case'], entry['messagePrefix']
        if entry['kind'] == 'command-incomplete':
            if case is not None:
                errors.append(label + ': command-incomplete entries name no case')
        elif not isinstance(case, str) or not case:
            errors.append(label + ': exact case name required')
        for value in (case, prefix):
            if isinstance(value, str) and ('*' in value or value != value.strip()):
                errors.append(label + ': wildcards and padded names are not exact identities')
        if not isinstance(prefix, str) or not prefix:
            errors.append(label + ': exact first-failure message prefix required')
        if entry['status'] == 'retired':
            retired.append(entry)
            continue
        key = (entry['command'], case, entry.get('condition'))
        if key in keys:
            errors.append(label + ': duplicate active entry for one command/case')
        keys.add(key)
        if entry['command'] in excluded:
            errors.append(label + ': command is a registered exclusion, not an executed instrument')
        elif entry['command'] not in known:
            errors.append(label + ': command is outside the registered population')
        active.append(entry)
    return active, retired, errors


def probe_capabilities(directory):
    """Host facts a conditional entry may depend on; probed, never assumed."""
    directory.mkdir(parents=True, exist_ok=True)
    link, target = directory / 'symlink-probe', directory / 'symlink-target'
    target.write_text('probe', encoding='utf-8')
    try:
        link.symlink_to(target.name)
        available = True
    except OSError:
        available = False
    finally:
        for path in (link, target):
            try:
                path.unlink()
            except OSError:
                pass
    return {'symlink-unavailable': not available}


def first_line(text):
    return next((line.strip() for line in str(text or '').splitlines() if line.strip()), '')


def extended_result(format_name, cases, complete, reason, exclusions=()):
    counts = {'passCases': sum(case['state'] == 'pass' for case in cases),
              'failCases': sum(case['state'] == 'fail' for case in cases),
              'notExecutedCases': sum(case['state'] == 'not-executed' for case in cases)}
    if not complete:
        result = output_result(format_name, counts=counts, reason=reason, exclusions=exclusions)
    else:
        status = 'FAIL' if counts['failCases'] else 'INCOMPLETE' if counts['notExecutedCases'] else 'PASS'
        result = output_result(format_name, status, counts, reason, exclusions)
    result['complete'] = bool(complete)
    result['cases'] = cases
    return result


def unittest_cases(text):
    """(cases, complete) from a verbose unittest log; failure identities come from its blocks."""
    ran = re.findall(r'^Ran (\d+) tests? in [\d.]+s$', text, re.M)
    terms = re.findall(r'^(OK|FAILED)(?: \(([^)]*)\))?[ \t]*$', text, re.M)
    if len(ran) != 1 or len(terms) != 1 or int(ran[0]) < 1:
        return [], False
    detail = {}
    for part in filter(None, terms[0][1].split(', ')):
        key, _, value = part.partition('=')
        detail[key] = int(value) if value.isdigit() else -1
    failures = detail.get('failures', 0) + detail.get('errors', 0)
    skipped = detail.get('skipped', 0)
    body = text[:text.rfind('\nRan ' + ran[0] + ' test')]
    cases, failing = [], set()
    for block in re.split(r'^={60,}\n', body, flags=re.M)[1:]:
        header = re.match(r'(FAIL|ERROR): (test\w*) \(([\w.]+)\)( \([^\n]*\))?\n-{60,}\n', block)
        if not header:
            return cases, False
        base = header[2] + ' (' + header[3] + ')'
        trace = [line for line in block[header.end():].splitlines() if line.strip() and not re.match(r'-{60,}$', line)]
        message = next((line.strip() for line in reversed(trace) if not line.startswith((' ', '\t'))), '')
        cases.append({'name': base + (header[4] or ''), 'state': 'fail', 'message': message})
        failing.add(base)
    for match in re.finditer(r'^(test\w*) \(([\w.]+)\)[^\n]*? \.\.\. skipped (.*)$', text, re.M):
        base = match[1] + ' (' + match[2] + ')'
        cases.append({'name': base, 'state': 'not-executed', 'message': match[3].strip()})
        failing.add(base)
    seen = sorted({match[1] + ' (' + match[2] + ')' for match in re.finditer(r'^(test\w*) \(([\w.]+)\)', text, re.M)})
    cases += [{'name': base, 'state': 'pass', 'message': ''} for base in seen if base not in failing]
    complete = (failures >= 0 and skipped >= 0 and sum(case['state'] == 'fail' for case in cases) == failures
                and sum(case['state'] == 'not-executed' for case in cases) == skipped
                and (terms[0][0] == 'OK') == (failures == 0))
    return cases, complete


def classify_extended(text, protocol, options):
    exclusions = re.findall(r'^SKIP_(?:HISTORICAL|SUPERSEDED|EXPLICIT) .+$', text, re.M)
    if protocol == 'case-lines':
        cases = []
        for match in re.finditer(r'^(PASS|DETECTED|FAIL)(?::\s*|\s+)(.+?)(?: :: (.*))?$', text, re.M):
            cases.append({'name': match[2].strip(), 'state': 'fail' if match[1] == 'FAIL' else 'pass',
                          'message': (match[3] or '').strip()})
        for line in exclusions:
            name, _, why = line.split(' ', 1)[1].partition(' — ')
            cases.append({'name': name.strip(), 'state': 'not-executed', 'message': why.strip()})
        names = [case['name'] for case in cases]
        complete = len(names) == len(set(names)) and len(names) == options.get('expectedCases')
        return extended_result('case-lines', cases, complete,
                               'complete declared case lines' if complete else 'case lines do not match the declared population')
    if protocol == 'json-lines':
        cases, summary = [], None
        for line in text.splitlines():
            if not line.startswith('{'):
                continue
            try:
                value = json.loads(line)
            except ValueError:
                return extended_result('json-lines', cases, False, 'invalid JSON line')
            if isinstance(value.get('summary'), dict):
                summary = value['summary']
            elif isinstance(value.get('name'), str) and value.get('status') in ('PASS', 'FAIL'):
                cases.append({'name': value['name'], 'state': 'pass' if value['status'] == 'PASS' else 'fail',
                              'message': first_line(value.get('error'))})
        names = [case['name'] for case in cases]
        complete = (summary is not None and len(names) == len(set(names)) and summary.get('cases') == len(cases)
                    and summary.get('failed') == sum(case['state'] == 'fail' for case in cases))
        return extended_result('json-lines', cases, complete,
                               'complete JSON case lines and summary' if complete else 'JSON case lines disagree with summary')
    if protocol == 'json-cases':
        try:
            value = json.loads(text)
            cases = [{'name': item['case'], 'state': 'pass' if item['passed'] is True else 'fail',
                      'message': first_line(item.get('error'))} for item in value['cases']]
            complete = (bool(cases) and type(value.get('allPassed')) is bool
                        and value['allPassed'] == all(case['state'] == 'pass' for case in cases)
                        and len({case['name'] for case in cases}) == len(cases))
        except (ValueError, KeyError, TypeError):
            return extended_result('json-cases', [], False, 'JSON case object not proved')
        return extended_result('json-cases', cases, complete,
                               'complete JSON case object' if complete else 'JSON case object inconsistent')
    if protocol == 'unittest-cases':
        cases, complete = unittest_cases(text)
        return extended_result('unittest-cases', cases, complete,
                               'complete unittest terminal' if complete else 'unittest completion not proved')
    if protocol == 'scientific':
        directory = Path(options['resultsDir'])
        try:
            receipt = strict_json(directory / 'results.json')
        except (OSError, ValueError):
            return extended_result('scientific', [], False, 'scientific results.json not produced')
        rows = receipt.get('commands', [])
        names = [row.get('name') for row in rows]
        if names != ['viewer-build', 'scientific-js', 'scientific-python'] or receipt.get('oracleUnchanged') is not True:
            return extended_result('scientific', [], False, 'scientific receipt incomplete or oracle changed')
        cases, complete = [], True
        for row in rows:
            log = (directory / (row['name'] + '.log')).read_text(encoding='utf-8')
            if row['name'] == 'viewer-build':
                cases.append({'name': 'viewer-build', 'state': 'pass' if row['exitCode'] == 0 else 'fail',
                              'message': 'exit ' + str(row['exitCode'])})
                continue
            if row['name'] == 'scientific-js':
                tap = classify_output(log, 'auto')
                sub = extract_cases(log, tap) if tap['reason'] in COMPLETE_REASONS else None
            else:
                sub, done = unittest_cases(log)
                sub = sub if done else None
            if sub is None:
                complete = False
                continue
            cases += [dict(case, name=row['name'] + ': ' + case['name']) for case in sub]
            if row['exitCode'] != 0 and not any(case['state'] == 'fail' for case in sub):
                complete = False
        return extended_result('scientific', cases, complete,
                               'complete scientific receipt and logs' if complete else 'scientific logs incomplete')
    raise ValueError('unknown extended protocol ' + str(protocol))


def extract_cases(text, output):
    """Per-case identities for the R0017 protocols; used only by the ledger adjudication."""
    if output.get('cases') is not None:
        return output['cases']
    cases = []
    if output['format'] == 'tap':
        lines = list(re.finditer(r'^( *)(ok|not ok) (\d+)(?: - )?([^\n]*)$', text, re.M))
        for index, match in enumerate(lines):
            end = lines[index + 1].start() if index + 1 < len(lines) else len(text)
            block = text[match.end():end]
            if re.search(r'^' + match[1] + r"  type: ['\"]suite['\"]$", block, re.M):
                continue
            name, _, directive = match[4].partition(' # ')
            if directive and re.match(r'(TODO|SKIP)\b', directive, re.I):
                cases.append({'name': name.strip(), 'state': 'not-executed', 'message': '# ' + directive.strip()})
                continue
            message = ''
            error = re.search(r'^' + match[1] + r"  error: (.*)$", block, re.M)
            if error:
                value = error[1].strip()
                if value in ('|-', '|', '>-', '>'):
                    rest = block[error.end():].splitlines()
                    value = next((line.strip() for line in rest if line.strip()), '')
                message = value.strip('\'"')
            cases.append({'name': name.strip(), 'state': 'pass' if match[2] == 'ok' else 'fail', 'message': message})
    elif output['format'] == 'json-results':
        payload = terminal_json(text)
        for item in payload['results']:
            state = item.get('status', item.get('result'))
            cases.append({'name': item['name'], 'state': 'pass' if state == 'PASS' else 'fail',
                          'message': first_line(item.get('error'))})
    elif output['format'] == 'json-summary':
        for match in re.finditer(r'^(PASS|FAIL)\s+(.+?)(?: :: (.*))?$', text, re.M):
            cases.append({'name': match[2].strip(), 'state': 'pass' if match[1] == 'PASS' else 'fail',
                          'message': (match[3] or '').strip()})
    for line in re.findall(r'^SKIP_(?:HISTORICAL|SUPERSEDED|EXPLICIT) .+$', text, re.M):
        name, _, why = line.split(' ', 1)[1].partition(' — ')
        cases.append({'name': name.strip(), 'state': 'not-executed', 'message': why.strip()})
    return cases


def adjudicate(row, out, entries, capabilities):
    """Apply exact ledger entries to one terminal command row (R0028 section 4.1)."""
    applicable = [entry for entry in entries if entry['command'] == row['name']
                  and (entry.get('condition') is None or capabilities.get(entry['condition']))]
    report = {'expectedFail': [], 'declaredNotExecuted': [], 'declaredIncomplete': [], 'unexpectedFail': [],
              'unexpectedNotExecuted': [], 'unexpectedPass': [], 'notExecuted': [], 'notAdjudicated': []}
    row['ledger'] = report
    output = row.get('output', {})
    exited = row['execution']['state'] == 'exited'
    complete = exited and (output.get('complete') is True or output.get('reason') in COMPLETE_REASONS)
    if row['status'] in ('HISTORICAL_EXCLUDED', 'NOT_APPLICABLE'):
        return row
    log = out / row['log']
    text = log.read_text(encoding='utf-8') if log.exists() else ''
    if not complete or row['setup']['status'] != 'READY':
        lines = set(line.strip() for line in text.splitlines())
        for entry in applicable:
            if entry['kind'] == 'command-incomplete' and row['status'] == 'INCOMPLETE' and entry['messagePrefix'] in lines:
                report['declaredIncomplete'].append(entry['id'])
            else:
                report['notAdjudicated'].append(entry['id'])
        if report['declaredIncomplete'] and len(report['declaredIncomplete']) == len(applicable):
            row['status'] = DECLARED
            row['reason'] = 'declared whole-command incompletion: ' + ', '.join(report['declaredIncomplete'])
        return row
    cases = extract_cases(text, output)
    by_name = {}
    for case in cases:
        by_name.setdefault(case['name'], []).append(case)
    matched = set()
    for name, group in by_name.items():
        for case in group:
            if case['state'] == 'pass':
                continue
            kind = 'case-fail' if case['state'] == 'fail' else 'case-not-executed'
            hits = [entry for entry in applicable if entry['kind'] == kind and entry['case'] == name]
            hit = hits[0] if len(hits) == 1 and len(group) == 1 and case['message'].startswith(hits[0]['messagePrefix']) else None
            if hit:
                matched.add(hit['id'])
                (report['expectedFail'] if kind == 'case-fail' else report['declaredNotExecuted']).append(
                    {'case': name, 'id': hit['id']})
            else:
                target = report['unexpectedFail'] if kind == 'case-fail' else report['unexpectedNotExecuted']
                target.append({'case': name, 'message': case['message'][:300],
                               'entryMismatch': [entry['id'] for entry in hits]})
    for entry in applicable:
        if entry['id'] in matched:
            continue
        group = by_name.get(entry['case']) if entry['case'] is not None else None
        if entry['kind'] == 'command-incomplete' or (group and any(case['state'] == 'pass' for case in group)):
            report['unexpectedPass'].append(entry['id'])
        elif not group:
            report['notExecuted'].append(entry['id'])
    if not applicable:
        return row  # Without entries the R0017 verdict stands; failures are listed above.
    if report['unexpectedFail'] or report['unexpectedPass'] or report['notExecuted']:
        row['status'] = 'FAIL'
        row['reason'] = 'ledger: unexpected failure, unexpected pass or absent ledgered case'
    elif report['unexpectedNotExecuted']:
        row['status'] = 'INCOMPLETE'
        row['reason'] = 'selected observations remain unexecuted without a ledger entry'
    elif row['status'] in ('FAIL', 'INCOMPLETE') and (report['expectedFail'] or report['declaredNotExecuted']):
        # A failure exit must be the ordinary failure code; any other exit stays FAIL.
        if row['exitCode'] == (1 if report['expectedFail'] else 0):
            row['status'] = DECLARED
            row['reason'] = 'every failure/unexecuted case is an exact ledger entry'
        else:
            row['status'] = 'FAIL'
            row['reason'] = 'declared failures but unexpected exit code ' + str(row['exitCode'])
    return row


def command_env(out, name, options):
    """Children inherit the environment, with temporary files bound inside the receipt (R0028 G-17)."""
    temp = out / 'tmp' / name
    temp.mkdir(parents=True, exist_ok=True)
    return dict(os.environ, **options.get('env', {}), TMP=str(temp), TEMP=str(temp), TMPDIR=str(temp))


def execute_command(root, out, spec, timeout, stop_reason=None):
    name, argv, _, protocol, disposition = spec[:5]
    options = spec[5] if len(spec) > 5 else {}
    timeout = options.get('timeout', timeout)
    log = out / (name + '.log')
    row = {'name': name, 'command': list(argv), 'exitCode': None, 'seconds': 0.0,
           'counts': {}, 'log': log.name, 'explicitExclusions': [], 'caseExclusions': [], 'status': 'INCOMPLETE',
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
                                       stderr=subprocess.STDOUT, timeout=timeout, env=command_env(out, name, options))
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
            output = (classify_extended(text, protocol, options) if protocol in EXTENDED_PROTOCOLS
                      else classify_output(text, protocol))
        except UnicodeError:
            text = ''
            output = output_result('unparsed', reason='output is not valid UTF-8; raw log retained')
        except KeyboardInterrupt:
            text = ''
            row['interrupted'] = True
            output = output_result('unparsed', reason='classification cancelled; observed process exit and raw log retained')
        row['output'] = output
        row['counts'] = output['counts']
        row['explicitExclusions'] = output['exclusions']
        row['caseExclusions'] = case_dispositions(name, output['exclusions'])
        if row['execution']['state'] == 'exited':
            setup_exception = re.search(r'^(?:SetupError: )?SETUP_INCOMPLETE: .+$', text, re.M)
            setup_failure = output.get('setupFailure') or (setup_exception[0] if setup_exception else None)
            if setup_failure:
                row['setup']['status'] = 'INCOMPLETE'
                row['setup']['reason'] = setup_failure
                row['reason'] = setup_failure
                row['status'] = 'FAIL' if output['status'] == 'FAIL' else 'INCOMPLETE'
            else:
                row['status'] = 'FAIL' if row['exitCode'] != 0 else output['status']
                row['reason'] = 'nonzero child exit' if row['exitCode'] != 0 else output['reason']
        if row['caseExclusions'] and row['status'] == 'PASS':
            row['status'] = 'INCOMPLETE'
            row['reason'] = 'selected observations remain unexecuted; see caseExclusions'
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
    if 'INCOMPLETE' in statuses or not ('PASS' in statuses or DECLARED in statuses):
        return 'INCOMPLETE'
    if any(status not in ('PASS', DECLARED, 'HISTORICAL_EXCLUDED', 'NOT_APPLICABLE') for status in statuses):
        raise ValueError('unknown terminal status')
    return DECLARED if DECLARED in statuses else 'PASS'


def run(root, out, *, selected=None, timeout=180):
    root, out = Path(root).resolve(), Path(out).resolve()
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be finite and positive')
    manifest, setup_errors = load_population(root)
    plan = build_plan(root, selected, out, manifest)
    full = build_plan(root, None, out, manifest)
    if manifest is not None:
        setup_errors += census(root, full, manifest)
    excluded = {Path(entry['path']).stem for entry in (manifest or {}).get('exclusions', [])}
    entries, retired, ledger_errors = load_ledger(root, {spec[0] for spec in full}, excluded)
    setup_errors += ledger_errors
    selected_names = {spec[0] for spec in plan}
    entries = [entry for entry in entries if entry['command'] in selected_names]
    # Existing receipts are immutable input, never an output slot to overwrite.
    out.mkdir(parents=True, exist_ok=False)
    capabilities = probe_capabilities(out / 'tmp' / 'runner-capabilities')
    source = source_identity(root, excluded=(out,))
    records = []
    result = {'schema': SCHEMA, 'status': 'RUNNING', 'commands': records,
              'plannedCommands': [{'name': spec[0], 'command': list(spec[1])} for spec in plan],
              'identity': {'invocation': str(uuid.uuid4()), 'startedAt': datetime.now(timezone.utc).isoformat(),
                           'source': source, 'runnerSha256': digest(__file__), 'host': host_identity()},
              'continuationPolicy': 'continue after terminal fixture results; stop later launches after timeout, launch failure or cancellation',
              'notRunHistorical': HISTORICAL,
              'population': {'manifest': POPULATION_FILE if manifest is not None else None,
                             'sha256': digest(root / POPULATION_FILE) if manifest is not None else None,
                             'exclusions': (manifest or {}).get('exclusions', []),
                             'modules': len((manifest or {}).get('modules', []))},
              'ledger': {'file': LEDGER_FILE, 'sha256': digest(root / LEDGER_FILE) if (root / LEDGER_FILE).exists() else None,
                         'active': len(entries), 'retired': [entry['id'] for entry in retired],
                         'capabilities': capabilities},
              'setupErrors': setup_errors,
              'scope': 'Only explicitly selected source-contract commands. Counts are descriptive; exclusions are not passes. No native pixels, live provider, platform, performance or delivery certification.'}

    def save():
        temporary = out / 'results.json.tmp'
        temporary.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        temporary.replace(out / 'results.json')

    save()
    stop_reason = None
    for spec in plan:
        row = adjudicate(execute_command(root, out, spec, timeout, stop_reason), out, entries, capabilities)
        records.append(row)
        if row['execution']['state'] in ('timed-out', 'launch-failed', 'cancelled') or row.get('interrupted'):
            stop_reason = 'not launched after ' + row['name'] + ': ' + row.get('reason', row['execution']['state'])
        save()
        print(row['name'], row['exitCode'], row['status'], row['counts'], flush=True)
    result['status'] = summarize(plan, records)
    if setup_errors and result['status'] != 'FAIL':
        result['status'] = 'INCOMPLETE'  # A malformed ledger/population is never a pass.
    declared = sorted({hit['id'] for row in records for key in ('expectedFail', 'declaredNotExecuted')
                       for hit in row.get('ledger', {}).get(key, [])}
                      | {hit for row in records for hit in row.get('ledger', {}).get('declaredIncomplete', [])})
    result['ledger']['declared'] = declared
    result['sourceUnchanged'] = source == source_identity(root, excluded=(out,))
    if not result['sourceUnchanged'] or source.get('available') is False:
        if result['status'] != 'FAIL':
            result['status'] = 'INCOMPLETE'
        result['identityError'] = 'source identity changed or was unavailable during invocation'
    result['verdict'] = result['status'] + (' (' + str(len(declared)) + ')' if result['status'] == DECLARED else '')
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
    print('VERDICT', result.get('verdict', result['status']), flush=True)
    # 0 PASS; 3 PASS_WITH_DECLARED_FAILURES (never reported as PASS); 1 otherwise.
    return 0 if result['status'] == 'PASS' else 3 if result['status'] == DECLARED else 1


if __name__ == '__main__':
    sys.exit(main())
