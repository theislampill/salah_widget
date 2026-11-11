#!/usr/bin/env python3
"""Original R0015 native staging lifetime and guard mutation qualification.

Only a fresh private fixture is used. Exact production source is evaluated up to
the wizard entry; real native stat/mktemp/permissions and cleanup remain intact.
This is filesystem retention evidence, not browser installation or reboot proof.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import stat
import subprocess
import sys
import tempfile

SOURCE = Path(sys.argv[1]).resolve()
SOURCE_BYTES = SOURCE.read_bytes()
TEXT = SOURCE_BYTES.decode('utf-8')
BOUNDARY = "\nprintf '\\nSalah Widget Installer\\n\\n'"
if TEXT.count(BOUNDARY) != 1:
    raise SystemExit('Actual source entry boundary changed')
LIB = TEXT.split(BOUNDARY)[0]
BASH = os.environ.get('SALAH_TEST_BASH', '/bin/bash')
ROOT = Path(tempfile.mkdtemp(prefix='salah-staging-native-')).resolve()
ROOT.chmod(0o700)
RESULTS = []
RUNS = []


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def metadata(path):
    path = Path(path)
    info = path.lstat()
    row = dict(path=str(path), device=info.st_dev, inode=info.st_ino, uid=info.st_uid,
               gid=info.st_gid, mode=oct(stat.S_IMODE(info.st_mode)), symlink=stat.S_ISLNK(info.st_mode))
    if stat.S_ISREG(info.st_mode):
        row['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    return row


def fixture(name):
    root = ROOT / name
    root.mkdir(mode=0o700)
    home = root / 'home with space مدينة'
    scratch = root / 'scratch'
    home.mkdir(mode=0o700)
    scratch.mkdir(mode=0o700)
    victim = root / 'outside-sentinel'
    victim.write_bytes(b'unchanged outside sentinel\n')
    env = dict(os.environ, HOME=str(home), TMPDIR=str(scratch), DRY_RUN='0', NO_OPEN='1', SALAH_INSTALL_SOURCE='github')
    env.pop('BASH_ENV', None)
    return root, home, scratch, victim, env


def run(name, code, env, library=LIB):
    script = library + '\n' + code + '\n'
    parser = subprocess.run([BASH, '-n'], input=script, text=True, capture_output=True)
    require(parser.returncode == 0, 'Invalid mutant/fixture syntax: ' + parser.stderr)
    result = subprocess.run([BASH, '--noprofile', '--norc', '-c', script], env=env, text=True,
                            capture_output=True, timeout=25, start_new_session=True)
    observation = dict(name=name, exit=result.returncode, stdout=result.stdout, stderr=result.stderr,
                       script_sha256=hashlib.sha256(script.encode()).hexdigest(), syntax_exit=parser.returncode)
    RUNS.append(observation)
    (ROOT / (name + '.sh')).write_text(script, encoding='utf-8')
    (ROOT / (name + '.json')).write_text(json.dumps(observation, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return observation


def check(name, action):
    try:
        detail = action()
        RESULTS.append(dict(case=name, pass_=True, detail=detail))
    except Exception as error:
        RESULTS.append(dict(case=name, pass_=False, error=str(error)))


ROOTS = 'printf "%s\\n%s\\n%s\\n%s\\n" "$WORK_ROOT" "$WORK_ID" "$BUNDLE_ROOT" "$BUNDLE_ID"\n'


def roots(observation):
    lines = observation['stdout'].splitlines()
    require(len(lines) == 4, 'Expected exactly native root/identity output: ' + repr(observation))
    return lines


def verify_retained(observation, scratch_parent, home, victim_before, victim, expected_exit):
    require(observation['exit'] == expected_exit, 'Unexpected source process exit: ' + repr(observation))
    scratch, scratch_id, bundle, bundle_id = roots(observation)
    require(Path(scratch).parent == scratch_parent and not Path(scratch).exists(), 'Owned scratch not cleaned within fixture')
    require(Path(bundle).parent == home and Path(bundle).is_dir(), 'Retained manual bundle missing or escaped')
    meta = metadata(bundle)
    require(meta['uid'] == os.getuid() and meta['mode'] == '0o700' and not meta['symlink'], 'Native retained root custody mismatch')
    require(bundle_id == ':'.join(str(x) for x in (meta['device'], meta['inode'], meta['uid'], '700')), 'Returned root identity does not match actual native stat')
    require(scratch_id.split(':')[-2:] == [str(os.getuid()), '700'], 'Scratch native identity was not owned0700')
    consumer = subprocess.run([sys.executable, '-c', 'import pathlib,sys; p=pathlib.Path(sys.argv[1]); assert p.read_bytes()==b"retained manual bytes\\n"; print(p.read_text(),end="")',
                               str(Path(bundle) / 'manual-proof')], capture_output=True, text=True, timeout=10)
    require(consumer.returncode == 0 and consumer.stdout == 'retained manual bytes\n', 'Fresh process cannot consume retained bytes: ' + repr(consumer))
    require(metadata(victim) == victim_before, 'Outside sentinel changed')
    return dict(scratch_identity=scratch_id, retained=meta, fresh_consumer=dict(exit=consumer.returncode, stdout=consumer.stdout), source_exit=observation['exit'])


def lifetime(kind, library=LIB, prefix='healthy'):
    root, home, scratch, victim, env = fixture(prefix + '-' + kind)
    before = metadata(victim)
    tail = {'exit':'exit 0', 'failure':'false', 'INT':'kill -INT $$', 'TERM':'kill -TERM $$'}[kind]
    expected = {'exit':0, 'failure':1, 'INT':130, 'TERM':143}[kind]
    code = '''initialize_staging
guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$BUNDLE_ROOT/manual-proof" file
(umask 077; printf 'retained manual bytes\\n' > "$BUNDLE_ROOT/manual-proof")
''' + ROOTS + tail
    actual = run(prefix + '-' + kind, code, env, library)
    return verify_retained(actual, scratch, home, before, victim, expected)


def attempt_roots(name, library=LIB):
    root, home, scratch, victim, env = fixture(name)
    before = metadata(victim)
    first = run(name + '-first', 'initialize_staging\n' + ROOTS, env, library)
    second = run(name + '-second', 'initialize_staging\n' + ROOTS, env, library)
    require(first['exit'] == second['exit'] == 0, 'Root acquisition bootstrap failed: ' + repr((first, second)))
    a, b = roots(first), roots(second)
    require(metadata(victim) == before, 'Outside sentinel changed')
    require(not Path(a[0]).exists() and not Path(b[0]).exists(), 'Scratch cleanup missing')
    require(Path(a[2]).is_dir() and Path(b[2]).is_dir(), 'Retained root missing')
    return a, b


def same_attempt():
    root, home, scratch, victim, env = fixture('same-attempt')
    actual = run('same-attempt', 'initialize_staging\n' + ROOTS + 'initialize_staging\n' + ROOTS, env)
    lines = actual['stdout'].splitlines()
    require(actual['exit'] == 0 and len(lines) == 8 and lines[:4] == lines[4:], 'Same-attempt root identity changed: ' + repr(actual))
    require(not Path(lines[0]).exists(), 'Scratch was not cleaned after actual exit')
    require(metadata(lines[2])['mode'] == '0o700', 'Manual root not private on actual native filesystem')
    return dict(first=lines[:4], second=lines[4:])


def distinct_attempt():
    a, b = attempt_roots('fresh-attempts')
    require(a[0] != b[0] and a[2] != b[2], 'New invocation reused scratch/manual root')
    return dict(first=a, second=b)


def replace_once(text, old, new):
    require(text.count(old) == 1, 'Actual mutant boundary changed: ' + old)
    return text.replace(old, new, 1)


def predictable_mutant():
    changed = LIB
    for parent, prefix in (('temp_parent', 'salah-widget-download'), ('home_parent', 'salah-widget-install')):
        old = 'created="$(umask 077; mktemp -d "$' + parent + '/' + prefix + '.XXXXXXXX")" || return 1'
        new = 'created="$(umask 077; mkdir -p "$' + parent + '/' + prefix + '.fixed"; printf "%s\\n" "$' + parent + '/' + prefix + '.fixed")" || return 1'
        changed = replace_once(changed, old, new)
    # Recreate the historical reusable-tree mechanism coherently: its existing
    # child directories must be accepted, not fail before the freshness oracle.
    changed = replace_once(changed, '(umask 077; mkdir "$DOWNLOAD_ROOT" "$PRESET_ROOT") || return 1', '(umask 077; mkdir -p "$DOWNLOAD_ROOT" "$PRESET_ROOT") || return 1')
    a, b = attempt_roots('predictable-mutant', changed)
    require(a[0] == b[0] and a[2] == b[2], 'Freshness mutant did not reproduce both reused roots')
    return dict(mutant_processes=[0, 0], observed_reused_scratch=a[0], observed_reused_manual=a[2], oracle='Both fresh-attempt paths must differ')


def symlink_mutant():
    changed = replace_once(LIB, '    [ ! -L "$current" ] || { err "Symlink in staged path: $current"; return 1; }',
                           '    : # mutant drops component symlink rejection')
    observations = []
    for name, library in (('symlink-healthy', LIB), ('symlink-mutant', changed)):
        root, home, scratch, victim, env = fixture(name)
        before = metadata(victim)
        code = 'initialize_staging\nln -s ' + shlex.quote(str(victim)) + ' "$PRESET_ROOT/foreign-link"\n'
        code += 'guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$PRESET_ROOT/foreign-link" file\n'
        actual = run(name, code, env, library)
        require(metadata(victim) == before, 'Guard discriminator changed victim')
        observations.append(actual)
    require(observations[0]['exit'] != 0 and 'Symlink in staged path' in observations[0]['stderr'], 'Healthy actual guard did not refuse symlink')
    require(observations[1]['exit'] == 0, 'Mutant did not reach actual unsafe guard admission')
    return dict(healthy_exit=observations[0]['exit'], mutant_exit=observations[1]['exit'], oracle='Actual owned-path helper must reject foreign symlink before callers')


def retention_mutant():
    changed = replace_once(LIB, 'cleanup_staging() {\n  [ "$DRY_RUN" = 0 ] && [ -n "$WORK_ROOT" ] || return 0',
                           'cleanup_staging() {\n  [ "$DRY_RUN" = 0 ] && [ -n "$WORK_ROOT" ] || return 0\n  if verify_root "$BUNDLE_ROOT" "$BUNDLE_ID"; then rm -rf -- "$BUNDLE_ROOT"; fi')
    root, home, scratch, victim, env = fixture('retained-delete-mutant')
    before = metadata(victim)
    code = 'initialize_staging\n(umask 077; printf "retained manual bytes\\n" > "$BUNDLE_ROOT/manual-proof")\n' + ROOTS
    actual = run('retained-delete-mutant', code, env, changed)
    require(actual['exit'] == 0, 'Retention mutant did not complete original process: ' + repr(actual))
    paths = roots(actual)
    require(not Path(paths[2]).exists() and not Path(paths[0]).exists(), 'Retention mutant did not reproduce lost manual directory')
    require(metadata(victim) == before, 'Retention mutant escaped owned fixture')
    return dict(mutant_exit=0, missing_manual_directory=paths[2], oracle='Fresh consumer must still read manual bytes after normal process exit')


check('actual native same-attempt root/identity reuse', same_attempt)
check('actual native next-attempt scratch and manual roots differ', distinct_attempt)
for boundary in ('exit', 'failure', 'INT', 'TERM'):
    check('actual native retained consumer after ' + boundary, lambda k=boundary: lifetime(k))
check('parse-valid predictable roots complete twice and fail freshness', predictable_mutant)
check('parse-valid symlink-admission mutant reaches wrong actual guard result', symlink_mutant)
check('parse-valid retained-delete mutant completes but loses consumer bytes', retention_mutant)
print(json.dumps(dict(source=str(SOURCE), source_sha256=hashlib.sha256(SOURCE_BYTES).hexdigest(),
                      test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), fixture=str(ROOT),
                      host=dict(system=platform.system(), platform=platform.platform(), uid=os.getuid(), bash=BASH,
                                bash_version=subprocess.check_output([BASH, '--version'], text=True).splitlines()[0]),
                      claims='native filesystem lifetime and admission only; no browser/installation/reboot claim',
                      results=RESULTS, observations=RUNS), indent=2, ensure_ascii=False))
sys.exit(0 if RESULTS and all(row['pass_'] for row in RESULTS) else 1)
