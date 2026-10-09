"""Reuse the retained native-frame observer and unchanged startup budgets."""
import datetime, hashlib, json, os, pathlib, subprocess, sys, time

R = pathlib.Path(__file__).resolve().parent
W = pathlib.Path(r'C:\Users\theis\.codex\worktrees\pr43-review-revision\salah_widget')
OLD = pathlib.Path(r'C:\Users\theis\Documents\Codex\celestial-startup-repair-20261008')
OUT = R / 'evidence/PR43-review/R1-complete-scene-02'
PY = r'C:\workspace\ai\cp9-integration-20261005\venv\Scripts\python.exe'
NODE = pathlib.Path(r'C:\Users\theis\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe')
DRIVER = OLD / 'capture-driver/cli.js'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(OLD / 'capture-driver/lib/coreBundle.js') == 'c34d9e9d56fe0a8fb0e9e5eac15be4841a11f222bc0c29a2d17ccc6eece8c9f8'
assert DRIVER.is_file() and NODE.is_file()
OUT.mkdir(exist_ok=False)
ledger = R / 'ACTIVE_LEDGER.json'
pin = sha(W / 'tools/cp9/celestial_startup_check.py')
rows = []
record = {'schema': 'pr43-ordinary-complete-scene/1', 'atUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'scope': 'Actual unchanged generated entries; native source-frame receipt upper bounds, not physical-monitor photons. Fixed accepted Orlando observer, synthetic providers, ordinary cold/reload/new-tab HTTP cache. Generic iframe is not the actual extension parent. No app getter or PNG polling in first 15 seconds. No threshold changes.',
          'harnessSha256': pin, 'driverBundleSha256': sha(OLD / 'capture-driver/lib/coreBundle.js'),
          'driverPreparation': str(OLD / 'capture-driver-preparation.log'), 'cases': rows, 'complete': False, 'comparisonBaseline': {'kind':'explicit reuse of immutable earlier exact-main captures; not a fresh matched pair','path':str(R / 'evidence/PR43-review/R1-complete-scene-01'),'receiptSha256':sha(R / 'evidence/PR43-review/R1-complete-scene-01/receipt.json')}}
def save():
    (OUT / 'receipt.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
def lease(**fields):
    d = json.loads(ledger.read_text(encoding='utf-8'))
    q = d['resourceLeases']['heavy-browser']
    assert q['holder'] in (None, 'root')
    q.update(**fields)
    tmp = ledger.with_suffix('.complete-scene.tmp')
    tmp.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    tmp.replace(ledger)
try:
    for engine in ['chromium', 'firefox']:
        for stage, site in [('candidate', R / 'candidates/pr43-r1r2-04')]:
            assert sha(W / 'tools/cp9/celestial_startup_check.py') == pin
            name = f'{engine}-{stage}'
            argv = [PY, '-B', '-X', 'utf8', str(W / 'tools/cp9/celestial_startup_check.py'),
                    '--root', str(site), '--out', str(OUT / name), '--modes', 'cold,warm-reload,new-tab',
                    '--duration', '18', '--entry', 'iframe', '--video', '--video-only',
                    '--driver-cli', str(DRIVER), '--driver-node', str(NODE)]
            lease(holder='root', status='RUNNING', scope='PR43 ordinary complete-scene capture',
                  leaseId='root-pr43-complete-scene-02', currentCase=name, command=argv, completedCases=len(rows), totalCases=2)
            env = {**os.environ, 'SALAH_CAPTURE_NATIVE_FRAMES': '1', 'SALAH_BROWSER': engine,
                   'SALAH_BROWSER_EXECUTABLE': str(pathlib.Path(os.environ['LOCALAPPDATA']) / 'ms-playwright' /
                       ('chromium-1223/chrome-win64/chrome.exe' if engine == 'chromium' else 'firefox-1522/firefox/firefox.exe'))}
            began = time.time()
            with (OUT / (name + '.log')).open('w', encoding='utf-8') as log:
                p = subprocess.run(argv, cwd=W, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=240)
            rawpath = OUT / name / 'results.json'
            raw = json.loads(rawpath.read_text()) if rawpath.exists() else {}
            row = {'case': name, 'argv': argv, 'exit': p.returncode, 'elapsedSeconds': time.time() - began,
                   'receipt': str(rawpath), 'receiptSha256': sha(rawpath) if rawpath.exists() else None,
                   'runtime': raw.get('runtime', {}).get('treeSha256'), 'errors': raw.get('errors'),
                   'runtimeUnchanged': raw.get('runtimeUnchanged'), 'runs': len(raw.get('runs', []))}
            rows.append(row); save(); print(json.dumps(row), flush=True)
            assert p.returncode == 0 and row['runtimeUnchanged'] is True and row['errors'] == [] and row['runs'] == 3
    record['complete'] = True; save()
finally:
    lease(holder=None, status='FREE', currentCase=None, command=None, completedCases=len(rows), lastResult=str(OUT / 'receipt.json'))
