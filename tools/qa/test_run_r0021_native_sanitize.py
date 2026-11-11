"""Unit check: tools/qa/run_r0021_native.py never writes local absolute prefixes into reports or logs.

Run: python tools/qa/test_run_r0021_native_sanitize.py   (no browser; Playwright is stubbed for the import)
"""
import importlib.util, json, sys, types
from pathlib import Path

stub = types.ModuleType('playwright.sync_api'); stub.sync_playwright = None
sys.modules.setdefault('playwright', types.ModuleType('playwright')); sys.modules['playwright.sync_api'] = stub
here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('driver', here / 'run_r0021_native.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)

failures = []
root = Path.home() / 'some-control-checkout'
for base, tag in ((d.REPO, '<repo>'), (Path(sys.prefix), '<python>'), (Path.home(), '<home>'), (root, '<root>')):
    raw = str(base.resolve())
    for form in (raw, raw.replace('\\', '/'), json.dumps(raw)[1:-1], raw[0].lower() + raw[1:]):
        sample = f'File "{form}{"/" if "/" in form else chr(92)}x.py", line 1'
        out = d.sanitize(sample, [(root, '<root>')])
        if raw.replace('\\', '/').lower() in out.replace('\\\\', '/').replace('\\', '/').lower():
            failures.append(f'{tag}: {out}')
        if tag not in out and not (tag == '<home>' and base != Path.home()):
            failures.append(f'missing {tag}: {out}')
# The init script must parse (a syntax error there silently disables every page-level instrument).
import shutil, subprocess, tempfile
if shutil.which('node'):
    with tempfile.TemporaryDirectory() as t:
        f = Path(t) / 'init.js'; f.write_text(d.INIT, encoding='utf-8')
        r = subprocess.run(['node', '--check', str(f)], capture_output=True, text=True)
        if r.returncode:
            failures.append('INIT does not parse: ' + d.sanitize(r.stderr.replace(str(f), '<init.js>'))[:300])
else:
    print('note: node not found; INIT syntax not checked')
if failures:
    print('FAIL', *failures, sep='\n'); sys.exit(1)
print('PASS sanitize: repository, Python install, home and served-root prefixes replaced in raw, POSIX, JSON-escaped and lower-case drive forms')
