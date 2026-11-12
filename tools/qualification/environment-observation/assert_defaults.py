#!/usr/bin/env python3
"""Qualification gate over the staging-parent observations and owner controls.

The observation scripts always exit 0; this gate turns their JSON into a
pass/fail result. It requires that the runner's REAL default environment is
admitted (Windows: real USERPROFILE and TEMP accepted by the production
staging-parent function, the helper compiles under the real TEMP, a real
staging initialisation succeeds, and the normal-mode entry reaches the manual
browser step; POSIX: every candidate default TMPDIR is accepted and
initialised by this tree's install.sh and the native staging suite passes).
With --owner-new/--owner-old it also requires that the owner-control positives
pass on the corrected bytes and fail on the pre-correction bytes.
"""
import argparse, json, pathlib, sys

parser = argparse.ArgumentParser()
parser.add_argument('--windows-functions', action='append', default=[])
parser.add_argument('--windows-entry', action='append', default=[])
parser.add_argument('--posix', action='append', default=[])
parser.add_argument('--owner-new', action='append', default=[])
parser.add_argument('--owner-old', action='append', default=[])
parser.add_argument('--output', required=True)
args = parser.parse_args()

checks = []


def check(label, ok, detail=None):
    checks.append({'check': label, 'pass': bool(ok), 'detail': detail})


def load(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))


for path in args.windows_functions:
    data = load(path)
    rows = {row.get('label'): row for row in data.get('admission', [])}
    for label in ('real USERPROFILE', 'real TEMP'):
        row = rows.get(label) or {}
        check(path + ': ' + label + ' accepted', row.get('result') == 'accepted', {k: row.get(k) for k in ('result', 'message', 'inspect')})
    check(path + ': helper compiles under the real TEMP', (data.get('compile') or {}).get('result') == 'loaded', data.get('compile'))
    check(path + ': real staging initialisation', (data.get('staging') or {}).get('result') == 'initialized', data.get('staging'))
    check(path + ': no observation load errors', not data.get('errors'), data.get('errors'))

for path in args.windows_entry:
    data = load(path)
    remaining = data.get('remainingAfterObserverCleanup') or {}
    check(path + ': interception loaded', data.get('interceptionLoaded') is True)
    check(path + ': normal mode reaches the manual browser step', data.get('classification') == 'manual-action-pending',
          {k: data.get(k) for k in ('exit', 'classification', 'createdAfterRun')} | {'stderrTail': (data.get('stderr') or '')[-1500:]})
    check(path + ': nothing left behind', not remaining.get('temp') and not remaining.get('profile'), remaining)

for path in args.posix:
    data = load(path)
    tree = [v for v in data.get('versions', []) if v.get('label') == 'tree']
    check(path + ': tree install.sh evaluated', len(tree) == 1 and not tree[0].get('error'))
    for version in tree:
        for row in version.get('trustedParent', []):
            check(path + ': trusted_parent ' + row['candidate'], row.get('result') == 'accepted', {'path': row.get('path'), 'stderr': row.get('stderr')})
        for row in version.get('initializeStaging', []):
            check(path + ': initialize_staging ' + row['candidate'], row.get('result') == 'initialized' and 'WORK_REMOVED' in (row.get('stdout') or ''),
                  {'TMPDIR': row.get('TMPDIR'), 'stderr': row.get('stderr')})
    for run in data.get('stagingNative', []):
        check(path + ': staging-native suite with ' + run['run'], run.get('rc') == 0, run.get('summary'))

POSITIVES = ('system-owned clean: staging predicate', 'system-owned clean: compiler predicate',
             'administrators-owned clean: staging predicate', 'administrators-owned clean: compiler predicate',
             'system/administrators-owned parents: Initialize-Staging', 'real USERPROFILE: staging predicate')
for new_path, old_path in zip(args.owner_new, args.owner_old):
    new = {r['case']: r for r in load(new_path)['results']}
    old = {r['case']: r for r in load(old_path)['results']}
    check(new_path + ': every owner control passes', all(r['status'] == 'PASS' for r in new.values()),
          [r['case'] + '=' + r['status'] for r in new.values() if r['status'] != 'PASS'])
    for case in POSITIVES:
        check(case + ' passes on corrected bytes', (new.get(case) or {}).get('status') == 'PASS')
        check(case + ' fails on pre-correction bytes', (old.get(case) or {}).get('status') == 'FAIL')
    negatives = [c for c, r in new.items() if c.startswith(('trustedinstaller', 'localservice', 'users', 'everyone', 'authenticatedusers')) and not c.startswith('mutant')]
    check(old_path + ': owner negatives still refused on pre-correction bytes', negatives and all((old.get(c) or {}).get('status') == 'PASS' for c in negatives),
          [c + '=' + (old.get(c) or {}).get('status', 'MISSING') for c in negatives])

report = {'schema': 'staging-parent-default-gate.v1', 'pass': bool(checks) and all(c['pass'] for c in checks), 'checks': checks}
pathlib.Path(args.output).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
for c in checks:
    print(('PASS ' if c['pass'] else 'FAIL ') + c['check'])
sys.exit(0 if report['pass'] else 1)
