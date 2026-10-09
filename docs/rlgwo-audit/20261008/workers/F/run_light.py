"""Bounded source-level controls only. No browsers, solvers, or source writes."""
import datetime, hashlib, json, pathlib, subprocess

ROOT = pathlib.Path('C:/Users/theis/.codex/worktrees/hotfix-startup-clouds/salah_widget')
OUT = pathlib.Path(__file__).parent / 'followup-tests'
NODE = pathlib.Path('C:/workspace/ai/cp9-integration-20261005/toolchain/node-v22.16.0-win-x64/node.exe')
TARGET = '18ff14860ff41c084b1db5f396bb62aa9c22b1be'
TREE = '35208181eea714c17f5e77b2644e76434345db60'
INDEX = 'ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee'
digest = lambda b: hashlib.sha256(b).hexdigest()
git = lambda *args: subprocess.check_output(['git', '--no-optional-locks', *args], cwd=ROOT, text=True).strip()
assert git('rev-parse', TARGET + '^{tree}') == TREE == git('rev-parse', 'HEAD^{tree}')
assert git('status', '--porcelain') == ''
assert digest((ROOT / 'index.html').read_bytes()) == INDEX
OUT.mkdir(exist_ok=True)
definitions = [
 (23, 'r0017-contract', ['tests/r0017-contract.cjs']),
 (23, 'r0017-transport', ['tests/r0017-transport.cjs']),
 (24, 'r0018-timetable-contrast', ['tests/r0018-timetable-contrast.cjs']),
 (26, 'r001a-radio', ['tests/r001a-radio.cjs']),
 (26, 'r001a-mutations', ['tests/r001a-mutations.cjs']),
 (29, 'r001d-diagnostics-original', ['tests/r001d-diagnostics.cjs']),
 (29, 'r001d-lifecycle', ['tests/r001d-lifecycle.cjs']),
 (33, 'r0021-reveal-current-boundary', ['tests/r0021-reveal.cjs', '--cp8-snapshot-only']),
 (34, 'r0022-lunar-consumers-current-boundary', ['tests/r0022-lunar-consumers.cjs', '--cp8-snapshot-only']),
 (37, 'r0025-continuity', ['tests/r0025-continuity.cjs']),
 (37, 'r0025-lifecycle', ['tests/r0025-lifecycle.cjs']),
]
receipt = {'createdAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'target': TARGET, 'tree': TREE, 'indexSha256': INDEX, 'requestedBy': 'primary lightweight controls follow-up',
 'runtimeSha256': 'f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260',
 'sourceHead': git('rev-parse', 'HEAD'), 'environment': {'node': str(NODE), 'nodeVersion': subprocess.check_output([str(NODE), '--version'], text=True).strip(), 'os': 'Windows', 'pythonMode': '-I -S -B'},
 'scope': 'Actual current source in VM/command controls; no browsers/native default actions/pixels/solver/cost proof.', 'commands': []}
for issue, name, args in definitions:
 command = [str(NODE), *args]
 started = datetime.datetime.now(datetime.timezone.utc)
 try:
  result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=45, encoding='utf-8', errors='replace')
  log = result.stdout + result.stderr
  lines = result.stdout.strip().splitlines()
  try: terminal = json.loads(lines[-1]) if lines else None
  except json.JSONDecodeError: terminal = None
  exitcode = result.returncode
  error = None
 except subprocess.TimeoutExpired as e:
  log = (e.stdout or b'').decode('utf-8', 'replace') + (e.stderr or b'').decode('utf-8', 'replace')
  terminal, exitcode, error = None, None, 'bounded 45 second timeout; no completion credit'
 path = OUT / (name + '.log')
 path.write_text(log, encoding='utf-8')
 item = {'issue': issue, 'name': name, 'command': command, 'cwd': str(ROOT),
  'fixtureSha256': digest((ROOT / args[0]).read_bytes()), 'freshExecution': True,
  'seconds': (datetime.datetime.now(datetime.timezone.utc)-started).total_seconds(), 'exitCode': exitcode,
  'terminal': terminal, 'failures': [l for l in log.splitlines() if l.startswith('FAIL ')],
  'log': str(path), 'logSha256': digest(log.encode('utf-8')), 'error': error}
 receipt['commands'].append(item)
 print(json.dumps({k:item[k] for k in ['issue','name','seconds','exitCode','terminal','failures','error']}), flush=True)
receipt['sourcePostStateClean'] = git('status', '--porcelain') == ''
assert receipt['sourcePostStateClean']
(OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
