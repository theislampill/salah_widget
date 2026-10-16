"""One serialized isolated native acquisition. No personal browser surfaces."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys

O = Path(__file__).resolve().parent
R = O / 'solar-probe-tools-r2'
name, build, family, *options = sys.argv[1:]
out = O / 'native' / name
assert not out.exists(), 'Preserve the original acquisition'
out.mkdir(parents=True)
dependencies=['tools/cp9/celestial_startup_check.py','tools/cp9/celestial_lifecycle_check.py',
              'tools/cp9/celestial_layer_controls.js','tools/cp9/browser_runtime.py',
              'tools/cp9/runtime_identity.py','tests/v1_browser.py','tools/cp9/solar_trace.js']
harness_inputs={}
for rel in dependencies:
    source=R/rel;data=source.read_bytes();target=out/'harness-source'/rel
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    harness_inputs[rel]=hashlib.sha256(data).hexdigest()
node = Path(r'<runtime-install>\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.15.0-win-x64\node.exe')
executable = {'chromium':r'<browser-install>\chromium-1223\chrome-win64\chrome.exe',
              'firefox':r'<browser-install>\firefox-1522\firefox\firefox.exe'}[family]
command = [r'<toolchain>\venv\Scripts\python.exe', '-I', '-B',
           str(R / 'tools/cp9/celestial_startup_check.py'), '--root', str(O / 'builds' / build),
           '--out', str(out), '--driver-cli', str(O / 'capture-driver/cli.js'), '--driver-node', str(node), *options]
env = dict(os.environ, SALAH_BROWSER=family, SALAH_BROWSER_EXECUTABLE=executable, SALAH_CAPTURE_NATIVE_FRAMES='1')
record = {'command':command, 'browser':executable, 'createdAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'sourceHarnessSha256':hashlib.sha256((R / 'tools/cp9/celestial_startup_check.py').read_bytes()).hexdigest(),
          'harnessInputSha256':harness_inputs,
          'purpose':'Bounded solar-strobe diagnostic: first30s ordinary, next15s CSS/state sampling. No S1/cost/closure credit.', 'status':'PREPARED'}
lock = O / 'native-resource.lock'
with lock.open('x') as f:
    f.write(name)
try:
    (out / 'EXECUTION.json').write_text(json.dumps(record, indent=2)+'\n')
    with (out / 'RUN-LOG.txt').open('w', encoding='utf-8') as log:
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    record.update(status='RETURNED', exitCode=result.returncode)
finally:
    record['returnedAtUtc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record['harnessUnchangedDuringRun']=all(hashlib.sha256((R/rel).read_bytes()).hexdigest()==pin for rel,pin in harness_inputs.items())
    (out / 'EXECUTION.json').write_text(json.dumps(record, indent=2)+'\n')
    assert lock.read_text() == name
    lock.unlink()
print(json.dumps(record))
sys.exit(result.returncode)
