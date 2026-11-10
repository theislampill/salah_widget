"""Bounded read-only review of a frozen draft; never launches inherited suites."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import uuid

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE / 'inputs/tools/cp9/run_native_regressions.py'
spec = importlib.util.spec_from_file_location('reviewed_runner_snapshot', SNAPSHOT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
RUN = HERE / ('probe-run-' + uuid.uuid4().hex[:12])
RUN.mkdir()
OBSERVED = []

JSON_PASS = '{"results":[{"name":"real case","status":"PASS"}]}'
JSON_FAIL = '{"results":[{"name":"real case","status":"FAIL"}]}'
TAP_PASS = ('TAP version 13\nok 1 - real case\n1..1\n# tests 1\n# suites 0\n'
            '# pass 1\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n# duration_ms 1\n')


def classifier(label, text):
    payload = RUN / (label + '.txt')
    payload.write_text(text)
    record = {'probe': label, 'input': str(payload)}
    try:
        record['observed'] = runner.classify_output(text)
    except Exception as error:
        record['exception'] = type(error).__name__
        record['error'] = str(error)
    OBSERVED.append(record)


def run_probe(label, text, *, classify_interrupt=False, mutate=False):
    base = RUN / label
    root = base / 'source'
    root.mkdir(parents=True)
    (root / 'input.txt').write_text('original source bytes\n')
    out = base / 'receipt'
    plan = tuple((name, ('controlled-child', name), ('input.txt',), 'auto', None)
                 for name in ('first', 'later'))
    calls = []
    record = {'probe': label, 'receipt': str(out), 'input': text[:180],
              'inputLength': len(text)}

    def child(command, **kwargs):
        calls.append(command)
        if mutate and len(calls) == 1:
            (root / 'input.txt').write_text('changed during first child\n')
        kwargs['stdout'].write(text)
        kwargs['stdout'].flush()
        return subprocess.CompletedProcess(command, 0)

    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(runner, 'build_plan', return_value=plan))
        stack.enter_context(patch.object(runner, 'HISTORY_INPUTS', {}))
        stack.enter_context(patch.object(runner, 'capture', return_value=None))
        stack.enter_context(patch.object(runner, 'host_identity', return_value={
            'python': 'review-controlled', 'node': 'no real child launched'}))
        stack.enter_context(patch.object(runner.subprocess, 'run', side_effect=child))
        stack.enter_context(patch.object(runner.time, 'monotonic', side_effect=range(100, 200)))
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        if classify_interrupt:
            stack.enter_context(patch.object(runner, 'classify_output', side_effect=KeyboardInterrupt))
        try:
            result = runner.run(root, out)
            record['returnedStatus'] = result['status']
        except (Exception, KeyboardInterrupt) as error:
            record['exception'] = type(error).__name__
            record['error'] = str(error)
    record['childCalls'] = calls
    receipt = out / 'results.json'
    record['receiptExists'] = receipt.is_file()
    if receipt.is_file():
        saved = json.loads(receipt.read_text())
        record['savedStatus'] = saved['status']
        record['plannedNames'] = [row['name'] for row in saved['plannedCommands']]
        record['recordedNames'] = [row['name'] for row in saved['commands']]
        record['commandStatuses'] = [row['status'] for row in saved['commands']]
        record['terminalCounts'] = [row['lifecycle'].count('terminal') for row in saved['commands']]
        record['sourceUnchanged'] = saved.get('sourceUnchanged')
        record['identityError'] = saved.get('identityError')
    record['logs'] = {p.name: p.read_text()[:200] for p in out.glob('*.log')}
    OBSERVED.append(record)


classifier('healthy-json-control', JSON_PASS)
classifier('healthy-tap-control', TAP_PASS)
classifier('duplicate-json-results-hides-fail',
           '{"results":[{"name":"real case","status":"FAIL"}],'
           '"results":[{"name":"real case","status":"PASS"}]}')
classifier('conflicting-summary-aliases',
           'PASS real case\n{"pass":1,"passed":0,"fail":0,"failed":1}')
classifier('zero-tap-plan-positive-totals', TAP_PASS.replace('ok 1 - real case\n', '').replace('1..1', '1..0'))
classifier('tap-skip-counted-as-pass', TAP_PASS.replace('ok 1 - real case', 'ok 1 - real case # SKIP historical input absent'))
run_probe('healthy-run-control', JSON_PASS)
deep = '{"padding":' + '[' * 1200 + '0' + ']' * 1200 + ',"results":[{"name":"real case","status":"PASS"}]}'
(RUN / 'deep-json.txt').write_text(deep)
run_probe('deep-json-drops-terminals', deep)
run_probe('interrupt-during-classification', JSON_PASS, classify_interrupt=True)
run_probe('source-change-overwrites-aggregate-fail', JSON_FAIL, mutate=True)

# Check actual prerequisites without lazy fetch, then prove the observed setup
# disposition suppresses the selected command without launching its suite.
live = Path('/workspace/scratch/7a8daf93afaa/r0017-explicit-work')
selected = runner.build_plan(live, selected=['r0021-reveal'])[0]
setup = runner.check_setup(live, selected)
out = RUN / 'mixed-history-command-preflight'
out.mkdir()
with patch.object(runner, 'check_setup', return_value=setup), \
        patch.object(runner.subprocess, 'run', side_effect=AssertionError('suite launch forbidden')) as child:
    if setup['status'] != 'READY':
        row = runner.execute_command(live, out, selected, timeout=1)
        (out / 'row.json').write_text(json.dumps(row, indent=2) + '\n')
        observed = {'status': row['status'], 'execution': row['execution'],
                    'lifecycle': row['lifecycle'], 'childCalls': child.call_count}
    else:
        observed = {'status': 'NOT_PROBED', 'reason': 'exact history is currently available; no suite launched'}
OBSERVED.append({'probe': 'mixed-history-command-preflight', 'name': selected[0],
                 'command': list(selected[1]), 'setup': setup, 'observed': observed})

report = {'runnerSnapshot': str(SNAPSHOT),
          'runnerSha256': hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(),
          'probeDirectory': str(RUN), 'observations': OBSERVED}
output = RUN / 'observations.json'
output.write_text(json.dumps(report, indent=2) + '\n')
(HERE / 'latest-probe-run.txt').write_text(str(RUN) + '\n')
print(json.dumps(report, indent=2))
