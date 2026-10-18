from pathlib import Path
import datetime, hashlib, json, os, subprocess

o = Path(__file__).resolve().parent
root = Path(r'${REPO_ROOT}')
build = o / 'reference-tools-r114/build'
node = Path(r'${NODE22}')
script = o / 'reference_quadrature_r114.cjs'
scene = o / 'independent-review/firefox-dpr2-quality-source-r69-review.json'
prior = o / 'numerical/quadrature-r112'
out = o / 'numerical/reference-r114'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(script) == '3dcc434f96ac589b87aaf4ba4d5eca56f0fba0e6bf5806c1e63fd311c994a201'
assert sha(build / 'PLAN-r2.json') == '850f1b2d72fce4f26708810602948cdb63def441a2a93ad8502f60519c9fb796'
plan = json.loads((build / 'PLAN-r2.json').read_bytes())
assert sha(plan['command'][0]) == '1ddf230367e07738c4a769eae66c1db7469e37bd520e81c86356453d0db2b9fd'
assert sha(build / 'moon_kernel_reference.c') == plan['diagnosticKernelSha256']
assert sha(build / 'moon-engine-reference.mjs') == plan['diagnosticEngineSha256']
assert sha(root / 'moon/src/moon_kernel.c') == plan['originalKernelSha256']
assert sha(root / 'moon/src/moon-engine.mjs') == plan['originalEngineSha256']
assert sha(scene) == 'fd09050a8d0bcb0d4300c03f64e13b9686c08754eeb810582faef7c376e62e64'
assert not out.exists() and not (build / 'moon_kernel_reference.wasm').exists()
product_wasm = sha(root / 'moon/moon_kernel.wasm')
env = os.environ.copy()
env['ZIG_GLOBAL_CACHE_DIR'] = str(o / 'reference-tools-r114/global-cache')
env['ZIG_LOCAL_CACHE_DIR'] = str(o / 'reference-tools-r114/local-cache')
lock = o / 'native-resource.lock'
with lock.open('x') as handle:
    handle.write('reference-r114')
record = {'schema': 'r0021-reference-execution/v1', 'status': 'RUNNING', 'startedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'sourceHead': plan['sourceHead'], 'harnessSha256': sha(script), 'planSha256': sha(build / 'PLAN-r2.json'),
          'compilerSha256': sha(plan['command'][0]), 'productWasmSha256': product_wasm,
          'compileTimeoutSeconds': 120, 'numericalTimeoutSeconds': 600, 'commands': [],
          'ownerApproval': 'Approve one diagnostic reference', 'errors': []}
termination_unverified = False

def run(command, log_path, timeout):
    global termination_unverified
    record['commands'].append(command)
    with log_path.open('xb') as log:
        process = subprocess.Popen(command, cwd=build, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            return process.wait(timeout=timeout)
        except BaseException as error:
            # Retain the lease after any interrupted operation. A taskkill exit
            # alone does not independently prove that every descendant is gone.
            termination_unverified = True
            record['interruptedOperation'] = {'pid': process.pid, 'reason': type(error).__name__}
            try:
                killed = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=15, check=False)
                record['interruptedOperation']['taskkillExitCode'] = killed.returncode
            except BaseException as cleanup_error:
                record['interruptedOperation']['taskkillError'] = str(cleanup_error)
            try:
                record['interruptedOperation']['parentExitCode'] = process.wait(timeout=15)
            except BaseException as cleanup_error:
                record['interruptedOperation']['parentWaitError'] = str(cleanup_error)
            raise

try:
    record['compileExitCode'] = run(plan['command'], o / 'reference-r114b-compile.log', 120)
    assert record['compileExitCode'] == 0, 'Diagnostic compilation failed; no numerical attempt'
    record['diagnosticWasmSha256'] = sha(build / 'moon_kernel_reference.wasm')
    command = [str(node), str(script), str(root), str(out), str(scene), str(prior), str(build)]
    record['numericalExitCode'] = run(command, o / 'reference-r114b.log', 600)
    record['status'] = 'RETURNED' if record['numericalExitCode'] == 0 else 'INCOMPLETE'
except BaseException as error:
    record['status'] = 'INCOMPLETE'
    record['errors'].append(type(error).__name__ + ': ' + str(error))
finally:
    record['productUnchanged'] = (sha(root / 'moon/src/moon_kernel.c') == plan['originalKernelSha256']
                                  and sha(root / 'moon/src/moon-engine.mjs') == plan['originalEngineSha256']
                                  and sha(root / 'moon/moon_kernel.wasm') == product_wasm)
    if not record['productUnchanged']:
        record['status'] = 'INCOMPLETE'
        record['errors'].append('Product drift')
    record['finishedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert lock.read_text() == 'reference-r114'
    if not termination_unverified:
        lock.unlink()
    record['lockReleased'] = not termination_unverified
    record['terminationUnverified'] = termination_unverified
    (o / 'reference-r114b-execution.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
raise SystemExit(0 if record['status'] == 'RETURNED' else 1)
