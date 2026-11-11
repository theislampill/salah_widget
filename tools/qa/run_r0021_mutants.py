"""R0021 temporary actual-source mutation controls; never modify the candidate.

Each mutant copies the authored owners into a disposable directory, applies one
exact textual mutation and runs the focused suite against that copy (the suites
read SALAH_REAL_SKY_SOURCE_DIR / SALAH_MOON_SOURCE_DIR). A mutant is KILLED only
when its named test fails while the healthy-construction control still passes.

  python tools/qa/run_r0021_mutants.py --out <new-dir>
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKY_TEST = 'tests/real-sky/native-construction-ownership.test.mjs'
MOON_TEST = 'moon/tests/native-instance-retirement.test.cjs'
SKY_HEALTHY = 'ES21-03 healthy construction'
MOON_HEALTHY = 'ES21-06 first boot installs one runtime'

# (id, owner, file, before, after, killer test-name prefix, healthy control)
MUTANTS = [
    ('m1-orphan-canvas-on-throw', 'sky', 'native-host.mjs',
     "card.prepend(canvas);own(()=>canvas.remove());", "card.prepend(canvas);",
     'ES21-02 failure at badge', SKY_HEALTHY),
    ('m2-interval-not-released-on-failure', 'sky', 'native-host.mjs',
     "const timer=setInterval(()=>request(),500);own(()=>clearInterval(timer));", "const timer=setInterval(()=>request(),500);",
     'ES21-02 failure at raf', SKY_HEALTHY),
    ('m2b-listener-not-released-on-failure', 'sky', 'native-host.mjs',
     "document.addEventListener('visibilitychange',visibility);own(()=>document.removeEventListener('visibilitychange',visibility));",
     "document.addEventListener('visibilitychange',visibility);",
     'ES21-02 failure at registered', SKY_HEALTHY),
    ('m3-object-url-not-released', 'sky', 'native-host.mjs',
     "workerUrl=url;own(()=>URL.revokeObjectURL(url));", "workerUrl=url;",
     'ES21-02 failure at interval', SKY_HEALTHY),
    ('m3b-worker-not-released', 'sky', 'native-host.mjs',
     "timeoutMs:15000});own(()=>client.dispose());", "timeoutMs:15000});",
     'ES21-02 failure at interval', SKY_HEALTHY),
    ('m4-module-global-retirement-state', 'sky', 'native-host.mjs',
     "if(disposed||status.retirement)return;const owner=window.SalahRealSky===instance;status.retirement={previewHandoff};",
     "if(disposed||globalThis.__r0021Retiring)return;const owner=window.SalahRealSky===instance;status.retirement=globalThis.__r0021Retiring={previewHandoff};",
     'ES21-04 retirement is instance-owned', SKY_HEALTHY),
    ('m5-late-frame-of-disposed-instance-runs', 'sky', 'native-host.mjs',
     " function animate(now){if(disposed)return;", " function animate(now){",
     'ES21-07 dispose is idempotent', SKY_HEALTHY),
    ('m6-retirement-publishes-preview', 'sky', 'native-host.mjs',
     "if(status.retirement?.previewHandoff!==false&&!previewOwnsDetail)", "if(!previewOwnsDetail)",
     'asset pagehide retires', SKY_HEALTHY),
    ('m7-live-handoff-suppressed-on-dispose', 'sky', 'native-host.mjs',
     "if(status.retirement?.previewHandoff!==false&&!previewOwnsDetail)", "if(!status.retirement&&!previewOwnsDetail)",
     'default direct disposal retains', SKY_HEALTHY),
    ('m7b-active-retry-handoff-suppressed', 'sky', 'native-assets.mjs',
     "sky?.dispose({previewHandoff:!loader.suspended&&!loader.disposed});", "sky?.dispose({previewHandoff:false});",
     'active asset retry preserves', SKY_HEALTHY),
    # Idempotence needs BOTH the retirement guard and the consuming unwinder;
    # removing only the guard is an equivalent mutant (the owned list is empty).
    ('m8-dispose-not-idempotent', 'sky', 'native-host.mjs',
     "while(owned.length){try{owned.pop()();}catch(error){failure??=error;}}return failure;}",
     "for(const r of owned){try{r();}catch(error){failure??=error;}}return failure;}",
     'ES21-07 dispose is idempotent', SKY_HEALTHY,
     ("if(disposed||status.retirement)return;const owner", "const owner")),
    ('m11-preview-retry-duplicates-canvas', 'sky', 'native-preview-host.mjs',
     "card.prepend(canvas);own(()=>canvas.remove());", "card.prepend(canvas);",
     'preview construction failure at preview-foreground', SKY_HEALTHY),
    ('m12-delayed-cleanup-registration', 'sky', 'native-host.mjs',
     "card.prepend(canvas);own(()=>canvas.remove());", "card.prepend(canvas);Promise.resolve().then(()=>own(()=>canvas.remove()));",
     'ES21-02 failure at badge', SKY_HEALTHY),
    # Independent-review mutants (ef6549c9 review; survived before the follow-up tests).
    ('m15-unwind-in-acquisition-order', 'sky', 'native-host.mjs',
     "while(owned.length){try{owned.pop()();}", "while(owned.length){try{owned.shift()();}",
     'ES21-02 a release that throws during unwind', SKY_HEALTHY),
    ('m16-rethrow-cleanup-instead-of-primary', 'sky', 'native-host.mjs',
     "const cleanup=release();if(cleanup&&error&&typeof error==='object')try{error.cleanupError=cleanup;}catch{/* frozen cause */}\n  throw error;",
     "const cleanup=release();throw cleanup??error;",
     'ES21-02 a release that throws during unwind', SKY_HEALTHY),
    ('m17-handoff-suppressed-while-hidden', 'sky', 'native-host.mjs',
     "if(status.retirement?.previewHandoff!==false&&!previewOwnsDetail)", "if(status.retirement?.previewHandoff!==false&&!document.hidden&&!previewOwnsDetail)",
     'handoff is not suppressed for a live instance', SKY_HEALTHY),
    ('m18-unconditional-registry-release', 'sky', 'native-host.mjs',
     "own(()=>{if(window.SalahRealSky===instance){window.SalahRealSky=null;", "own(()=>{if(true){window.SalahRealSky=null;",
     'ES21-04 retirement never clears a registry slot', SKY_HEALTHY),
    ('m19-replay-allowed-without-detail-slot', 'moon', 'moon-install-guard.mjs',
     "if(window.SalahMoonRuntime&&!window.SalahMoonRuntime.disposed)throw", "if(window.SalahMoonDetail&&window.SalahMoonRuntime&&!window.SalahMoonRuntime.disposed)throw",
     'ES21-05 replay is refused for a live runtime even when the detail slot is empty', MOON_HEALTHY),
    ('m20-moon-failed-construction-keeps-detail', 'moon', 'moon-native.mjs',
     "  if(window.SalahMoonDetail===detail)window.SalahMoonDetail=null;detail.dispose();\n  throw error;",
     "  throw error;",
     'ES21-02 Moon wrapper failure at interval', MOON_HEALTHY),
    ('m9-moon-replay-proceeds-over-live-runtime', 'moon', 'moon-install-guard.mjs',
     "if(window.SalahMoonRuntime&&!window.SalahMoonRuntime.disposed)throw", "if(false)throw",
     'ES21-05 full-wrapper replay over a live runtime', MOON_HEALTHY),
    ('m10-adopt-after-dispose-accepted', 'moon', 'moon-native.mjs',
     "adopt(s){if(retired)return false;return inner.adopt(s);}", "adopt(s){return inner.adopt(s);}",
     'ES21-07 detail disposal is idempotent', MOON_HEALTHY),
    ('m13-dispose-current-global-detail', 'moon', 'moon-native.mjs',
     "closeWorker();if(window.SalahMoonDetail===detail)window.SalahMoonDetail=null;detail.dispose();status.status='disposed';",
     "closeWorker();window.SalahMoonDetail?.dispose();status.status='disposed';",
     'ES21-04 conditional registry cleanup', MOON_HEALTHY),
    ('m14-clear-shared-detail-slot-unconditionally', 'moon', 'moon-native.mjs',
     "closeWorker();if(window.SalahMoonDetail===detail)window.SalahMoonDetail=null;detail.dispose();status.status=", "closeWorker();window.SalahMoonDetail=null;detail.dispose();status.status=",
     'ES21-04 conditional registry cleanup', MOON_HEALTHY),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative(text, path, label):
    # Evidence carries no local absolute paths: every spelling of `path`.
    for form in {str(path), str(path).replace('\\', '\\\\'), path.as_posix(), 'file:///' + path.as_posix()}:
        text = text.replace(form, label)
    return text


def outcome(tap, name):
    for line in tap.splitlines():
        m = re.match(r'^(not ok|ok) \d+ - (.*)$', line)
        if m and m.group(2).startswith(name):
            return 'fail' if m.group(1) == 'not ok' else 'pass'
    return 'missing'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--node', default='node')
    args = p.parse_args()
    root, out = args.root.resolve(), args.out
    out.mkdir(parents=True, exist_ok=False)
    records = []
    for mid, owner, name, before, after, killer, healthy, *extra in MUTANTS:
        source_dir = root / ('real-sky' if owner == 'sky' else 'moon/src')
        text = (source_dir / name).read_text(encoding='utf-8')
        for b, a in [(before, after)] + list(extra):
            count = text.count(b)
            assert count == 1, (mid, 'anchor count', count)
            text = text.replace(b, a)
        with tempfile.TemporaryDirectory(prefix='r0021-mutant-') as tmp:
            tmp = Path(tmp)
            for f in source_dir.glob('*.mjs'):
                shutil.copy2(f, tmp / f.name)
            (tmp / name).write_text(text, encoding='utf-8', newline='\n')
            env = dict(os.environ)
            env['SALAH_REAL_SKY_SOURCE_DIR' if owner == 'sky' else 'SALAH_MOON_SOURCE_DIR'] = str(tmp)
            test = SKY_TEST if owner == 'sky' else MOON_TEST
            command = [args.node, '--test', '--test-reporter=tap', '--test-concurrency=1', test]
            result = subprocess.run(command, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        tap = result.stdout.decode('utf-8', 'replace')
        (out / (mid + '.tap')).write_text(relative(relative(tap, root, '<worktree>'), tmp, '<mutant-copy>'), encoding='utf-8')
        killed, control = outcome(tap, killer), outcome(tap, healthy)
        records.append({'id': mid, 'file': ('real-sky/' if owner == 'sky' else 'moon/src/') + name,
                        'killerTest': killer, 'killer': killed, 'healthyControl': control,
                        'verdict': 'KILLED' if killed == 'fail' and control == 'pass' else 'SURVIVED',
                        'command': ['node', '--test', '--test-reporter=tap', '--test-concurrency=1', test],
                        'exitCode': result.returncode})
        print(mid, records[-1]['verdict'], 'killer=' + killed, 'healthy=' + control)
    (out / 'mutants.json').write_text(json.dumps({'schema': 'r0021-mutants/1', 'records': records}, indent=1) + '\n', encoding='utf-8')
    return 0 if all(r['verdict'] == 'KILLED' for r in records) else 1


if __name__ == '__main__':
    raise SystemExit(main())
