from pathlib import Path
import datetime, hashlib, json, subprocess

o = Path(__file__).resolve().parent
root = Path(r'${REPO_ROOT}')
node = Path(r'${NODE22}')
script = o / 'compare_quadrature_r112.cjs'
out = o / 'numerical' / 'quadrature-r112'
scene = o / 'independent-review' / 'firefox-dpr2-quality-source-r69-review.json'
assert hashlib.sha256(script.read_bytes()).hexdigest() == '97ad1b0fc9d210b1b53e01c68e158973b05137260afa44a6fd157f645dcf9a15'
assert hashlib.sha256(scene.read_bytes()).hexdigest() == 'fd09050a8d0bcb0d4300c03f64e13b9686c08754eeb810582faef7c376e62e64'
assert not out.exists()
lock = o / 'native-resource.lock'
with lock.open('x') as handle:
    handle.write('quadrature-r112')
record = {'schema': 'r0021-numerical-execution/v1', 'status': 'RUNNING', 'hostTimeoutSeconds': 600, 'startedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'sourceHead': 'f35ccd403bbb04a613cc13aa8f91556561f20c4c', 'command': [str(node), str(script), str(root), str(out), str(scene)]}
try:
    with (o / 'quadrature-r112.log').open('wb') as log:
        result = subprocess.run(record['command'], stdout=log, stderr=subprocess.STDOUT, timeout=600, check=False)
    record['exitCode'] = result.returncode
    record['status'] = 'RETURNED' if result.returncode == 0 else 'INCOMPLETE'
except subprocess.TimeoutExpired:
    record['status'] = 'INCOMPLETE'
    record['error'] = 'Host600s deadline: subprocess.run killed and waited for its owned Node child.'
finally:
    record['finishedAt'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert lock.read_text() == 'quadrature-r112'
    lock.unlink()
    record['lockReleased'] = True
    (o / 'quadrature-r112-execution.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
