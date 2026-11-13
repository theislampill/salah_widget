#!/usr/bin/env python3
"""R002A qualification gate jobs (issue 91, docs/state-contracts/R002A.md). Python stdlib only.

One subcommand per gate job. Each writes `<out>/<job>.json` (a new directory), prints `VERDICT <string>`,
appends a Markdown summary to $GITHUB_STEP_SUMMARY when that is set, and exits:

  0  pass, or pass-with-declared-failures / pass-with-declared-divergence (the verdict string says which)
  1  fail or incomplete
  2  usage error

The check colour of a GitHub job cannot carry a third state, so `pass-with-declared-failures` is never
reported as a plain pass: the verdict string is in the receipt, the job summary and a notice annotation.

  parity  (J1)  build twice with tools/build_native.py; the tree must stay clean (status and diff)
  suites  (J2, J3)  the R0028 runner over the registered population, judged by the exact ledger;
                J2 = node instruments and the docs contract, J3 = Python instruments
  v1      (J4)  tools/verify_v1.py --negative-control and --check-pages
  pins    (J5)  (a) docs-receipt SHA-256 pins equal README/builder/config; (b) README review-first
                installer pins equal the checked-out installers or a valid declared divergence record

The gate never writes to the repository, deploys, pushes or comments; `parity` runs the builder in the
(disposable) checkout it is given and reports what it changed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = 'salah-qualification-gate/1'
RUNNER = 'tools/cp9/run_native_regressions.py'
DECLARED = 'PASS_WITH_DECLARED_FAILURES'
DOCS_PINS_FILE = 'tools/qualification/installer_preview_docs.cjs'
DOCS_PINNED = ('README.md', 'src/native/builder.html', 'src/native/config.js')
DIVERGENCE_FILE = 'tools/qualification/installer-pin-divergence.json'
DIVERGENCE_SCHEMA = 'salah-installer-pin-divergence/1'
DIVERGENCE_FIELDS = ('pinnedCommit', 'path', 'pinnedBlob', 'currentBlob', 'reason', 'owner', 'date', 'trigger')
# README review-first route variables (README "Review a pinned file first"): variable -> installer path.
README_PINS = (("INSTALL_COMMIT='", 'install.sh'), ("$InstallCommit = '", 'install.ps1'))
EXIT = {'PASS': 0, 'DECLARED': 0, 'FAIL': 1, 'INCOMPLETE': 1}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_id(data):
    """The Git blob ID of exact bytes (no clean filter), as `git hash-object --no-filters` computes it."""
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def git(root, *args, check=True):
    result = subprocess.run(['git', *args], cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        raise RuntimeError('git ' + ' '.join(args) + ' failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    return result


def head_identity(root):
    head = git(root, 'rev-parse', '--verify', 'HEAD', check=False)
    tree = git(root, 'rev-parse', '--verify', 'HEAD^{tree}', check=False)
    return {'head': head.stdout.decode().strip() or None, 'tree': tree.stdout.decode().strip() or None,
            'githubSha': os.environ.get('GITHUB_SHA'), 'githubRef': os.environ.get('GITHUB_REF'),
            'githubEvent': os.environ.get('GITHUB_EVENT_NAME'), 'runId': os.environ.get('GITHUB_RUN_ID'),
            'runAttempt': os.environ.get('GITHUB_RUN_ATTEMPT')}


def verdict_string(status, count=None):
    if status == 'DECLARED':
        return DECLARED + ' (' + str(count) + ')'
    return status


def emit(out, job, receipt, summary_lines):
    """Write the receipt, the step summary and the verdict line; return the exit code."""
    receipt['schema'] = SCHEMA
    receipt['job'] = job
    (out / (job + '.json')).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    text = '\n'.join(['### ' + job + ': `' + receipt['verdict'] + '`', ''] + summary_lines) + '\n'
    (out / (job + '-summary.md')).write_text(text, encoding='utf-8')
    target = os.environ.get('GITHUB_STEP_SUMMARY')
    if target:
        with open(target, 'a', encoding='utf-8') as stream:
            stream.write(text + '\n')
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        level = 'notice' if EXIT[receipt['status']] == 0 else 'error'
        print('::' + level + ' title=' + job + ' verdict::' + receipt['verdict'], flush=True)
    print('VERDICT', receipt['verdict'], flush=True)
    return EXIT[receipt['status']]


# --- J1 parity -------------------------------------------------------------------------------------

def build_report(text):
    """The builder's final JSON object (its stdout ends with one indented object)."""
    start = text.rfind('\n{')
    start = 0 if text.startswith('{') and start < 0 else start + 1
    try:
        return json.loads(text[start:])
    except ValueError:
        return None


def parity(root, out, python=sys.executable):
    receipt = {'identity': head_identity(root), 'builds': []}
    lines = []
    status = 'PASS'
    reasons = []
    for index in (1, 2):
        started = time.monotonic()
        child = subprocess.run([python, 'tools/build_native.py'], cwd=root, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        text = child.stdout.decode('utf-8', 'replace')
        (out / ('build-' + str(index) + '.log')).write_text(text, encoding='utf-8')
        report = build_report(text)
        receipt['builds'].append({'run': index, 'exitCode': child.returncode,
                                  'seconds': round(time.monotonic() - started, 3),
                                  'report': {k: report.get(k) for k in ('phase', 'written', 'unchanged', 'removed',
                                                                        'removedPaths', 'inventorySha256',
                                                                        'indexSha256')} if report else None})
        if child.returncode != 0 or report is None:
            status = 'FAIL'
            reasons.append('build ' + str(index) + ' exited ' + str(child.returncode)
                           + ('' if report else ' without its JSON report'))
            break
    porcelain = git(root, 'status', '--porcelain', '--untracked-files=all', check=False)
    diff = git(root, 'diff', '--exit-code', '--stat', check=False)
    changed = [line for line in porcelain.stdout.decode('utf-8', 'replace').splitlines() if line.strip()]
    receipt['statusPorcelain'] = changed
    receipt['diffExitCode'] = diff.returncode
    receipt['diffStat'] = diff.stdout.decode('utf-8', 'replace').splitlines()[-50:]
    if porcelain.returncode != 0 or changed:
        status = 'FAIL'
        reasons.append('tree not clean after building twice: ' + str(len(changed)) + ' path(s)')
    if diff.returncode != 0:
        status = 'FAIL'
        reasons.append('git diff --exit-code returned ' + str(diff.returncode))
    # R0029 G-08 (determinism on this host): the second build writes and removes nothing.
    second = receipt['builds'][1]['report'] if len(receipt['builds']) == 2 else None
    receipt['secondBuildWroteNothing'] = bool(second) and second.get('written') == 0 and second.get('removed') == 0
    first = receipt['builds'][0]['report'] if receipt['builds'] else None
    receipt['firstBuildWroteNothing'] = bool(first) and first.get('written') == 0 and first.get('removed') == 0
    if second is not None and not receipt['secondBuildWroteNothing']:
        status = 'FAIL'
        reasons.append('second build wrote or removed files')
    receipt['status'] = status
    receipt['reasons'] = reasons
    receipt['verdict'] = verdict_string(status)
    for build in receipt['builds']:
        r = build['report'] or {}
        lines.append('- build ' + str(build['run']) + ': exit ' + str(build['exitCode']) + ', written '
                     + str(r.get('written')) + ', unchanged ' + str(r.get('unchanged')) + ', removed '
                     + str(r.get('removed')) + ' (' + str(build['seconds']) + ' s)')
    lines.append('- `git status --porcelain`: ' + (str(len(changed)) + ' path(s)' if changed else 'empty'))
    lines.extend('  - `' + line + '`' for line in changed[:40])
    lines.append('- `git diff --exit-code`: ' + str(diff.returncode))
    lines.extend('- ' + reason for reason in reasons)
    return emit(out, 'parity', receipt, lines)


# --- J2/J3 suites ----------------------------------------------------------------------------------

def is_python_command(command, python):
    argv = command.get('command') or []
    return bool(argv) and (argv[0] == python or Path(argv[0]).name.startswith('python'))


def partition_status(rows, setup_errors):
    statuses = [row.get('status') for row in rows]
    if 'FAIL' in statuses:
        return 'FAIL'
    if setup_errors or 'INCOMPLETE' in statuses or not rows:
        return 'INCOMPLETE'
    if any(status not in ('PASS', DECLARED, 'HISTORICAL_EXCLUDED', 'NOT_APPLICABLE') for status in statuses):
        return 'INCOMPLETE'
    return 'DECLARED' if DECLARED in statuses else 'PASS'


def declared_ids(rows):
    found = set()
    for row in rows:
        ledger = row.get('ledger', {})
        for key in ('expectedFail', 'declaredNotExecuted'):
            found.update(hit['id'] for hit in ledger.get(key, []))
        found.update(ledger.get('declaredIncomplete', []))
    return sorted(found)


def summarize_suites(results, python, ledger_entries=()):
    """Partition one runner receipt into J2 (node/docs) and J3 (Python) verdicts."""
    rows = results.get('commands', [])
    setup = results.get('setupErrors', [])
    parts = {'J2': [r for r in rows if not is_python_command(r, python)],
             'J3': [r for r in rows if is_python_command(r, python)]}
    jobs = {}
    for name, group in parts.items():
        status = partition_status(group, setup)
        ids = declared_ids(group)
        jobs[name] = {'status': status, 'verdict': verdict_string(status, len(ids)), 'declared': ids,
                      'commands': len(group),
                      'notPass': [{'name': r['name'], 'status': r['status'], 'reason': r.get('reason'),
                                   'unexpected': {k: v for k, v in r.get('ledger', {}).items()
                                                  if (k.startswith('unexpected') or k in ('notExecuted', 'notAdjudicated'))
                                                  and v}}
                                  for r in group if r.get('status') not in ('PASS',)]}
    capabilities = results.get('ledger', {}).get('capabilities', {})
    conditional = []
    by_name = {r['name']: r for r in rows}
    for entry in ledger_entries:
        if entry.get('status') != 'active' or not entry.get('condition'):
            continue
        row = by_name.get(entry['command'], {})
        ledger = row.get('ledger', {})
        applicable = bool(capabilities.get(entry['condition']))
        observed = 'command not run'
        if row:
            hits = [h for k in ('expectedFail', 'declaredNotExecuted') for h in ledger.get(k, []) if h.get('id') == entry['id']]
            bad = [h for k in ('unexpectedFail', 'unexpectedNotExecuted') for h in ledger.get(k, [])
                   if h.get('case') == entry['case']]
            if hits:
                observed = 'declared (' + ('fail' if entry['kind'] == 'case-fail' else 'not-executed') + ')'
            elif bad:
                observed = 'case did not pass: ' + bad[0].get('message', '')[:160]
            elif row.get('status') in ('PASS', DECLARED):
                observed = 'case passed (entry inert on this host)' if not applicable else 'entry not matched'
            else:
                observed = 'command ' + str(row.get('status'))
        conditional.append({'id': entry['id'], 'command': entry['command'], 'case': entry['case'],
                            'condition': entry['condition'], 'conditionHolds': applicable, 'observed': observed})
    overall = results.get('status')
    status = {'PASS': 'PASS', DECLARED: 'DECLARED', 'FAIL': 'FAIL'}.get(overall, 'INCOMPLETE')
    return {'runnerVerdict': results.get('verdict', overall), 'status': status, 'jobs': jobs,
            'setupErrors': setup, 'capabilities': capabilities, 'conditionalEntries': conditional,
            'sourceUnchanged': results.get('sourceUnchanged'), 'declared': results.get('ledger', {}).get('declared', [])}


def suites(root, out, python=sys.executable, timeout=None):
    runner_out = out / 'runner'
    argv = [python, RUNNER, '--output', str(runner_out)]
    if timeout:
        argv += ['--timeout', str(timeout)]
    started = time.monotonic()
    child = subprocess.run(argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = child.stdout.decode('utf-8', 'replace')
    (out / 'runner.log').write_text(text, encoding='utf-8')
    receipt = {'identity': head_identity(root), 'runnerArgv': argv[1:], 'runnerExitCode': child.returncode,
               'seconds': round(time.monotonic() - started, 3)}
    results_path = runner_out / 'results.json'
    try:
        results = json.loads(results_path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as error:
        results = None
        receipt['error'] = 'runner receipt unreadable: ' + str(error)
    if results is None:
        receipt.update(status='INCOMPLETE', verdict='INCOMPLETE', runnerVerdict=None)
        return emit(out, 'suites', receipt, ['- runner receipt unreadable (exit ' + str(child.returncode) + ')'])
    try:
        entries = json.loads((root / 'tests/expected-failures.json').read_text(encoding='utf-8')).get('entries', [])
    except (OSError, ValueError):
        entries = []
    summary = summarize_suites(results, python, entries)
    receipt.update(summary)
    # The runner's exit code and verdict must agree; any disagreement is never a pass.
    expected_exit = {'PASS': 0, 'DECLARED': 3}.get(summary['status'], 1)
    if child.returncode != expected_exit:
        receipt['status'] = 'INCOMPLETE' if summary['status'] != 'FAIL' else 'FAIL'
        receipt['reason'] = 'runner exit ' + str(child.returncode) + ' disagrees with verdict ' + str(summary['runnerVerdict'])
    receipt['verdict'] = summary['runnerVerdict'] if receipt['status'] == summary['status'] else receipt['status']
    lines = ['- runner verdict (verbatim): `' + str(summary['runnerVerdict']) + '`, exit ' + str(child.returncode),
             '- J2 node instruments and docs contract: `' + summary['jobs']['J2']['verdict'] + '` ('
             + str(summary['jobs']['J2']['commands']) + ' commands)',
             '- J3 Python instruments: `' + summary['jobs']['J3']['verdict'] + '` ('
             + str(summary['jobs']['J3']['commands']) + ' commands)',
             '- declared ledger entries: ' + (', '.join(summary['declared']) or 'none'),
             '- setup errors: ' + (str(len(summary['setupErrors'])) if summary['setupErrors'] else '0'),
             '- host capabilities: `' + json.dumps(summary['capabilities']) + '`']
    for name in ('J2', 'J3'):
        for row in summary['jobs'][name]['notPass']:
            lines.append('  - ' + name + ' `' + row['name'] + '`: ' + str(row['status']) + ' - ' + str(row['reason'])
                         + ((' ' + json.dumps(row['unexpected'])[:400]) if row['unexpected'] else ''))
    for entry in summary['conditionalEntries']:
        lines.append('- condition-gated `' + entry['id'] + '` (' + entry['condition'] + ' = '
                     + str(entry['conditionHolds']).lower() + '): ' + entry['observed'])
    for error in summary['setupErrors'][:20]:
        lines.append('  - setup error: ' + str(error)[:300])
    return emit(out, 'suites', receipt, lines)


# --- J4 v1 -----------------------------------------------------------------------------------------

def v1(root, out, python=sys.executable):
    receipt = {'identity': head_identity(root), 'checks': []}
    status = 'PASS'
    for flags in (['--negative-control'], ['--check-pages']):
        child = subprocess.run([python, 'tools/verify_v1.py', *flags], cwd=root, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        text = child.stdout.decode('utf-8', 'replace')
        receipt['checks'].append({'argv': ['tools/verify_v1.py', *flags], 'exitCode': child.returncode,
                                  'output': text.splitlines()[-20:]})
        if child.returncode != 0:
            status = 'FAIL'
    receipt['status'] = status
    receipt['verdict'] = status
    lines = ['- `verify_v1.py ' + ' '.join(c['argv'][1:]) + '`: exit ' + str(c['exitCode']) + ' - '
             + '; '.join(c['output'][-3:]) for c in receipt['checks']]
    return emit(out, 'v1', receipt, lines)


# --- J5 pin coherence ------------------------------------------------------------------------------

DOCS_PIN_RE = re.compile(r"bindings\['([^']+)'\]\.sha256!=='([0-9a-f]{64})'")


def docs_pins(root):
    """J5(a): the three docs-receipt pins must equal the current files. No divergence path (issue 91 §4.3)."""
    text = (root / DOCS_PINS_FILE).read_text(encoding='utf-8')
    found = DOCS_PIN_RE.findall(text)
    rows, errors = [], []
    names = [name for name, _ in found]
    if sorted(names) != sorted(DOCS_PINNED) or len(set(names)) != len(names):
        errors.append(DOCS_PINS_FILE + ': expected exactly one SHA-256 pin each for ' + ', '.join(DOCS_PINNED)
                      + '; found ' + repr(names))
    for name, pinned in found:
        path = root / name
        actual = sha256(path.read_bytes()) if path.is_file() else None
        ok = actual == pinned
        rows.append({'path': name, 'pinned': pinned, 'actual': actual, 'equal': ok})
        if not ok:
            errors.append(name + ' SHA-256 ' + str(actual) + ' differs from the docs-receipt pin ' + pinned
                          + ' in ' + DOCS_PINS_FILE + ' (re-pin and produce the successor receipt in the same change)')
    return rows, errors


def readme_pins(text):
    """{installer path: [pinned commit, ...]} from README's review-first variables."""
    pins = {}
    for prefix, path in README_PINS:
        pins[path] = re.findall(re.escape(prefix) + r"([0-9a-f]{40})'", text)
    return pins


def load_divergence(root):
    path = root / DIVERGENCE_FILE
    errors = []
    if not path.is_file():
        return [], [DIVERGENCE_FILE + ' is missing (an empty record list is required)']
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except ValueError as error:
        return [], [DIVERGENCE_FILE + ' is not JSON: ' + str(error)]
    if not isinstance(data, dict) or data.get('schema') != DIVERGENCE_SCHEMA or not isinstance(data.get('records'), list):
        return [], [DIVERGENCE_FILE + ': expected {"schema": "' + DIVERGENCE_SCHEMA + '", "records": [...]}']
    records = []
    seen = set()
    for index, record in enumerate(data['records']):
        label = DIVERGENCE_FILE + ' record ' + str(index)
        if not isinstance(record, dict) or set(record) - set(DIVERGENCE_FIELDS) - {'notes'}:
            errors.append(label + ': unknown fields or not an object')
            continue
        missing = [field for field in DIVERGENCE_FIELDS if not isinstance(record.get(field), str) or not record[field].strip()]
        if missing:
            errors.append(label + ': missing ' + ', '.join(missing))
            continue
        if record['path'] not in dict((p, None) for _, p in README_PINS):
            errors.append(label + ': path must be install.sh or install.ps1')
            continue
        if not all(re.fullmatch(r'[0-9a-f]{40}', record[k]) for k in ('pinnedCommit', 'pinnedBlob', 'currentBlob')):
            errors.append(label + ': pinnedCommit, pinnedBlob and currentBlob must be full 40-hex IDs')
            continue
        if record['path'] in seen:
            errors.append(label + ': duplicate record for ' + record['path'])
            continue
        seen.add(record['path'])
        records.append(record)
    return records, errors


def installer_pins(root):
    """J5(b): README pinned installer blobs vs checked-out installers, or a valid divergence record."""
    readme = (root / 'README.md').read_text(encoding='utf-8')
    pins = readme_pins(readme)
    records, errors = load_divergence(root)
    by_path = {record['path']: record for record in records}
    rows, declared, used = [], [], set()
    for path, commits in pins.items():
        if len(set(commits)) != 1:
            errors.append('README.md: expected one review-first pin for ' + path + ', found ' + repr(sorted(set(commits))))
            continue
        commit = commits[0]
        pinned = git(root, 'rev-parse', '--verify', '--quiet', commit + ':' + path, check=False)
        pinned_blob = pinned.stdout.decode().strip() if pinned.returncode == 0 else None
        current_file = root / path
        current_blob = git_blob_id(current_file.read_bytes()) if current_file.is_file() else None
        row = {'path': path, 'pinnedCommit': commit, 'pinnedBlob': pinned_blob, 'currentBlob': current_blob}
        record = by_path.get(path)
        if pinned_blob is None:
            row['state'] = 'unresolved'
            errors.append('README.md pins ' + path + ' to ' + commit + ', which is not resolvable here '
                          '(fetch history; never a pass)')
        elif current_blob is None:
            row['state'] = 'missing'
            errors.append(path + ' is missing from the checkout')
        elif pinned_blob == current_blob:
            row['state'] = 'equal'
        elif record is None:
            row['state'] = 'diverged'
            errors.append(path + ' blob ' + current_blob + ' differs from the README review-first pin ' + commit + ':'
                          + path + ' (' + pinned_blob + ') and no divergence record covers it: re-pin README or add a '
                          'record to ' + DIVERGENCE_FILE)
        else:
            row['state'] = 'declared-divergence'
        if record is not None:
            used.add(path)
            stale = [k for k, v in (('pinnedCommit', commit), ('pinnedBlob', pinned_blob), ('currentBlob', current_blob))
                     if record[k] != v]
            if pinned_blob is not None and pinned_blob == current_blob:
                stale.append('no divergence remains (the record outlived its trigger)')
            if stale:
                row['state'] = 'stale-record'
                errors.append(DIVERGENCE_FILE + ' record for ' + path + ' is stale: ' + ', '.join(stale)
                              + ' (expected pinnedCommit ' + commit + ', pinnedBlob ' + str(pinned_blob)
                              + ', currentBlob ' + str(current_blob) + ')')
            elif row['state'] == 'declared-divergence':
                declared.append(path)
        rows.append(row)
    for path in sorted(set(by_path) - used):
        errors.append(DIVERGENCE_FILE + ' record for ' + path + ' matches no README pin')
    return rows, declared, errors


def pins(root, out):
    receipt = {'identity': head_identity(root)}
    a_rows, a_errors = docs_pins(root)
    b_rows, declared, b_errors = installer_pins(root)
    receipt['docsReceipt'] = {'rows': a_rows, 'errors': a_errors}
    receipt['installerPins'] = {'rows': b_rows, 'declaredDivergence': declared, 'errors': b_errors}
    errors = a_errors + b_errors
    status = 'FAIL' if errors else ('DECLARED' if declared else 'PASS')
    receipt['status'] = status
    receipt['verdict'] = ('PASS_WITH_DECLARED_DIVERGENCE (' + str(len(declared)) + ')') if status == 'DECLARED' else status
    lines = ['- J5(a) docs-receipt pins (`' + DOCS_PINS_FILE + '`):']
    lines += ['  - `' + r['path'] + '` ' + ('equal' if r['equal'] else 'DIFFERS: ' + str(r['actual'])) for r in a_rows]
    lines.append('- J5(b) README review-first installer pins:')
    lines += ['  - `' + r['path'] + '` at `' + r['pinnedCommit'][:12] + '`: ' + r.get('state', '?') for r in b_rows]
    lines += ['- ' + error for error in errors]
    return emit(out, 'pins', receipt, lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('job', choices=('parity', 'suites', 'v1', 'pins'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--out', type=Path, required=True, help='new receipt directory; an existing one is refused')
    parser.add_argument('--timeout', type=float, help='suites: per-command seconds passed to the runner')
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        args.out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error('receipt directory exists: ' + str(args.out))
    out = args.out.resolve()
    if args.job == 'parity':
        return parity(root, out)
    if args.job == 'suites':
        return suites(root, out, timeout=args.timeout)
    if args.job == 'v1':
        return v1(root, out)
    return pins(root, out)


if __name__ == '__main__':
    sys.exit(main())
