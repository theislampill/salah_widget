#!/usr/bin/env python3
"""Staging-parent environment observation (Linux / macOS).

Records the host's temporary-directory facts, then evaluates the installer's
own staging functions, loaded unmodified from each supplied install.sh up to
its wizard entry exactly as the repository's staging-native test does. Each
call runs under /bin/bash with a private fixture HOME. The installer entry is
never reached: no terminal prompt, no network, no browser. Roots created by
the installer's own initialize_staging are removed by its own cleanup_staging;
the retained bundle in the fixture HOME is removed with the fixture.
This is an observation, not a gate: it always exits 0.
"""
import argparse, hashlib, json, os, pathlib, platform, shutil, stat, subprocess, sys, tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--source', action='append', required=True, help='label=path to an install.sh to evaluate')
parser.add_argument('--repo-root', required=True, type=pathlib.Path)
parser.add_argument('--fixture-parent', required=True, type=pathlib.Path)
parser.add_argument('--output', required=True, type=pathlib.Path)
args = parser.parse_args()

BASH = '/bin/bash'
BOUNDARY = "\nprintf '\\nSalah Widget Installer\\n\\n'"
SYSTEM = platform.system()


def run(command, env=None, timeout=240, cwd=None):
    try:
        r = subprocess.run(command, env=env, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return {'rc': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'rc': None, 'error': str(error)}


def ancestors(path):
    rows = []
    if not path:
        return rows
    parts = pathlib.PurePosixPath(path).parts
    current = pathlib.PurePosixPath('/')
    for part in parts:
        current = current / part if part != '/' else current
        try:
            info = os.lstat(str(current))
            row = {'path': str(current), 'uid': info.st_uid, 'gid': info.st_gid, 'mode': oct(stat.S_IMODE(info.st_mode)),
                   'symlink': stat.S_ISLNK(info.st_mode), 'directory': stat.S_ISDIR(info.st_mode)}
            if row['symlink']:
                row['target'] = os.readlink(str(current))
        except OSError as error:
            row = {'path': str(current), 'error': str(error)}
        rows.append(row)
    return rows


def physical(path):
    if not path:
        return None
    r = run([BASH, '-c', 'cd "$1" && pwd -P', '_', path])
    return r.get('stdout', '').strip() if r.get('rc') == 0 else None


fixture_parent = args.fixture_parent.resolve()
report = {'schema': 'staging-parent-environment-observation.posix.v1', 'system': SYSTEM,
          'platform': platform.platform(), 'python': sys.version.split()[0],
          'bash': run([BASH, '--version']).get('stdout', '').splitlines()[:1],
          'uid': os.getuid(), 'imageVersion': os.environ.get('ImageVersion') or os.environ.get('IMAGEVERSION'),
          'environment': {'TMPDIR': os.environ.get('TMPDIR'), 'TMPDIR_set': 'TMPDIR' in os.environ,
                          'HOME': os.environ.get('HOME'), 'RUNNER_TEMP': os.environ.get('RUNNER_TEMP')},
          'facts': {}, 'versions': [], 'stagingNative': []}
facts = report['facts']
darwin_default = None
if SYSTEM == 'Darwin':
    r = run(['/usr/bin/getconf', 'DARWIN_USER_TEMP_DIR'])
    darwin_default = r.get('stdout', '').strip() or None
    facts['getconf_DARWIN_USER_TEMP_DIR'] = r
    facts['sw_vers'] = run(['/usr/bin/sw_vers'])
facts['ls_ld'] = run(['/bin/ls', '-ld', '/var', '/tmp', '/private/var', '/private/tmp'])
env_tmp = os.environ.get('TMPDIR')
candidates = []
if env_tmp:
    candidates.append(('environment TMPDIR as provided', env_tmp))
if darwin_default and darwin_default != env_tmp:
    candidates.append(('getconf DARWIN_USER_TEMP_DIR (login-shell default)', darwin_default))
for label, value in list(candidates):
    phys = physical(value)
    if phys and phys.rstrip('/') != value.rstrip('/'):
        candidates.append(('physical of: ' + label, phys))
candidates.append(('/tmp', '/tmp'))
if SYSTEM == 'Darwin':
    candidates.append(('/private/tmp', '/private/tmp'))
facts['candidates'] = [{'label': l, 'path': p, 'physical': physical(p), 'ancestors': ancestors(p.rstrip('/') or '/')} for l, p in candidates]

base = pathlib.Path(tempfile.mkdtemp(prefix='envobs-posix-', dir=str(fixture_parent))).resolve()
base.chmod(0o700)


def private_home(name):
    home = base / name
    home.mkdir(mode=0o700)
    return home


for spec in args.source:
    label, _, source = spec.partition('=')
    data = pathlib.Path(source).read_bytes()
    text = data.decode('utf-8')
    version = {'label': label, 'sha256': hashlib.sha256(data).hexdigest(),
               'gitBlob': run(['git', 'hash-object', source]).get('stdout', '').strip(),
               'boundaryCount': text.count(BOUNDARY), 'trustedParent': [], 'initializeStaging': []}
    report['versions'].append(version)
    if text.count(BOUNDARY) != 1:
        version['error'] = 'entry boundary not found exactly once; not evaluated'
        continue
    lib = base / (label + '-lib.sh')
    lib.write_text(text.split(BOUNDARY)[0] + '\n', encoding='utf-8')
    for cand_label, path in candidates:
        home = private_home('home-tp-' + label + '-' + str(len(version['trustedParent'])))
        env = dict(os.environ, HOME=str(home), DRY_RUN='0', NO_OPEN='1')
        env.pop('BASH_ENV', None)
        r = run([BASH, '-c', 'L=$1; P=$2; set --; source "$L"; trusted_parent "$P" temp', '_', str(lib), path], env=env)
        version['trustedParent'].append({'candidate': cand_label, 'path': path, 'result': 'accepted' if r.get('rc') == 0 else 'refused', **r})
    tmp_cases = [(l, p) for l, p in candidates] + [('TMPDIR unset (installer default /tmp)', None)]
    for cand_label, path in tmp_cases:
        home = private_home('home-init-' + label + '-' + str(len(version['initializeStaging'])))
        env = dict(os.environ, HOME=str(home), DRY_RUN='0', NO_OPEN='1')
        env.pop('BASH_ENV', None)
        if path is None:
            env.pop('TMPDIR', None)
        else:
            env['TMPDIR'] = path
        script = ('L=$1; set --; source "$L"; DRY_RUN=0; initialize_staging || exit $?; '
                  'printf "WORK=%s\\nBUNDLE=%s\\n" "$WORK_ROOT" "$BUNDLE_ROOT"; w="$WORK_ROOT"; cleanup_staging; '
                  'if [ -e "$w" ]; then echo WORK_REMAINS; else echo WORK_REMOVED; fi')
        r = run([BASH, '-c', script, '_', str(lib)], env=env)
        bundles = sorted(p.name for p in home.iterdir())
        version['initializeStaging'].append({'candidate': cand_label, 'TMPDIR': path,
                                             'result': 'initialized' if r.get('rc') == 0 else 'refused',
                                             'bundleEntriesInFixtureHome': bundles, **r})

suite = args.repo_root / 'tests/install-staging-native.py'
tree_source = dict(s.partition('=')[::2] for s in args.source).get('tree')
suite_runs = [('TMPDIR as provided by the environment', env_tmp)]
if darwin_default and darwin_default != env_tmp:
    suite_runs.append(('TMPDIR = getconf DARWIN_USER_TEMP_DIR', darwin_default))
if not env_tmp:
    suite_runs = [('TMPDIR unset', None)]
for run_label, value in suite_runs:
    env = dict(os.environ, SALAH_TEST_BASH=BASH)
    if value is None:
        env.pop('TMPDIR', None)
    else:
        env['TMPDIR'] = value
    r = run([sys.executable, str(suite), tree_source], env=env, timeout=600, cwd=str(args.repo_root))
    summary = None
    try:
        decoder = json.JSONDecoder()
        out = r.get('stdout', '')
        for offset in range(len(out)):
            if out[offset] == '{':
                try:
                    value_obj, end = decoder.raw_decode(out[offset:])
                    if not out[offset + end:].strip():
                        rows = value_obj.get('results', [])
                        summary = {'rows': len(rows), 'passing': sum(1 for x in rows if isinstance(x, dict) and x.get('pass_', x.get('pass')) is True),
                                   'failing': [{k: x.get(k) for k in ('case', 'name', 'error', 'reason') if x.get(k) is not None} for x in rows if isinstance(x, dict) and x.get('pass_', x.get('pass')) is not True][:12]}
                        break
                except ValueError:
                    continue
    except Exception as error:
        summary = {'parseError': str(error)}
    report['stagingNative'].append({'run': run_label, 'TMPDIR': value, 'rc': r.get('rc'), 'summary': summary,
                                    'stderrTail': (r.get('stderr') or '')[-2000:]})

shutil.rmtree(base, ignore_errors=True)
report['fixtureRemoved'] = not base.exists()
args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
for version in report['versions']:
    print(version['label'], version['gitBlob'][:8], [(t['candidate'], t['result']) for t in version['trustedParent']])
    print('   initialize_staging', [(t['candidate'], t['result']) for t in version['initializeStaging']])
print('staging-native', [(s['run'], s['rc'], (s['summary'] or {}).get('passing'), (s['summary'] or {}).get('rows')) for s in report['stagingNative']])
sys.exit(0)
