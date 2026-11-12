#!/usr/bin/env python3
"""Staging-parent admission on the host's real default temporary directories.

Evaluates the supplied install.sh up to its wizard entry under /bin/bash (or
SALAH_TEST_BASH) with a private fixture HOME. Positives use TMPDIR exactly as
the operating system provides it (trailing slash included), TMPDIR unset,
/tmp and, on macOS, /private/tmp: each must pass trusted_parent and a real
initialize_staging/cleanup_staging round trip. Negatives cover noncanonical
spellings, symlinks that a non-root user could replace, writable or foreign
ancestors, an unowned final directory, an unsafe HOME and a link swapped after
resolution. Cases that need a root-owned fixture use passwordless sudo inside
the private fixture and are reported BLOCKED_PRIVILEGE without it. No network,
browser or terminal prompt is reached.

Usage: install-staging-parent.py INSTALL_SH [--report PATH]
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

SOURCE = Path(sys.argv[1]).resolve()
REPORT = Path(sys.argv[sys.argv.index('--report') + 1]) if '--report' in sys.argv else None
TEXT = SOURCE.read_text(encoding='utf-8')
BOUNDARY = "\nprintf '\\nSalah Widget Installer\\n\\n'"
if TEXT.count(BOUNDARY) != 1:
    raise SystemExit('Actual source entry boundary changed')
BASH = os.environ.get('SALAH_TEST_BASH', '/bin/bash')
DARWIN = platform.system() == 'Darwin'
PROVIDED_TMPDIR = os.environ.get('TMPDIR')
# The fixture lives under the physical temporary directory, never a drive root.
BASE = Path(tempfile.mkdtemp(prefix='salah-parent-', dir=os.path.realpath(PROVIDED_TMPDIR or '/tmp'))).resolve()
BASE.chmod(0o700)
LIB = BASE / 'lib.sh'
LIB.write_text(TEXT.split(BOUNDARY)[0] + '\n', encoding='utf-8')
SUDO = shutil.which('sudo') and subprocess.run(['sudo', '-n', 'true'], capture_output=True).returncode == 0
RESULTS = []
ROOT_PATHS = []


def sudo(*args):
    subprocess.run(['sudo', '-n', *args], check=True, capture_output=True)


def bash(script, env_extra=None, unset=()):
    home = Path(tempfile.mkdtemp(prefix='home-', dir=str(BASE)))
    home.chmod(0o700)
    env = dict(os.environ, HOME=str(home), DRY_RUN='0', NO_OPEN='1', SALAH_INSTALL_SOURCE='github')
    env.pop('BASH_ENV', None)
    for key in unset:
        env.pop(key, None)
    env.update(env_extra or {})
    r = subprocess.run([BASH, '--noprofile', '--norc', '-c', 'L=$1; shift; source "$L"; ' + script, '_', str(LIB)],
                       env=env, capture_output=True, text=True, timeout=60)
    return {'rc': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr.strip()[-600:], 'home': str(home)}


def parent(path, kind='temp'):
    return bash('trusted_parent "$P" ' + kind, {'P': path})


ROUND_TRIP = ('DRY_RUN=0; initialize_staging || exit $?; w="$WORK_ROOT"; b="$BUNDLE_ROOT"; '
              'printf "WORK=%s\\nBUNDLE=%s\\n" "$w" "$b"; cleanup_staging; '
              'if [ -e "$w" ]; then echo WORK_REMAINS; else echo WORK_REMOVED; fi; [ -d "$b" ] && echo BUNDLE_RETAINED')


def record(name, status, detail):
    RESULTS.append({'case': name, 'status': status, 'pass': status == 'PASS', 'detail': detail})


def positive(name, tmpdir):
    env, unset = ({}, ('TMPDIR',)) if tmpdir is None else ({'TMPDIR': tmpdir}, ())
    tp = parent(tmpdir if tmpdir is not None else '/tmp')
    init = bash(ROUND_TRIP, env, unset)
    ok = tp['rc'] == 0 and init['rc'] == 0 and 'WORK_REMOVED' in init['stdout'] and 'BUNDLE_RETAINED' in init['stdout']
    work = next((l[5:] for l in init['stdout'].splitlines() if l.startswith('WORK=')), '')
    ok = ok and work == os.path.realpath(work)
    record(name, 'PASS' if ok else 'FAIL', {'TMPDIR': tmpdir, 'trusted_parent': tp, 'round_trip': init})


def negative(name, path, kind='temp', expect=None, needs_root=False, blocked=False):
    if blocked or (needs_root and not SUDO):
        record(name, 'BLOCKED_PRIVILEGE', {'path': path})
        return
    r = parent(path, kind)
    expects = [expect] if isinstance(expect, str) else (expect or [])
    ok = r['rc'] != 0 and r['stdout'] == '' and (not expects or any(e in r['stderr'] for e in expects))
    record(name, 'PASS' if ok else 'FAIL', {'path': path, 'kind': kind, 'expect': expect, 'observed': r})


def mkdir(path, mode=0o700):
    path.mkdir()
    path.chmod(mode)
    return path


def root_dir(path, mode=0o755):
    sudo('mkdir', str(path))
    sudo('chmod', oct(mode)[2:], str(path))
    ROOT_PATHS.append(path)
    return path


def root_link(link, target):
    sudo('ln', '-s', str(target), str(link))
    ROOT_PATHS.append(link)
    return link


try:
    # --- Positives on the real defaults -------------------------------------
    if PROVIDED_TMPDIR is not None:
        positive('TMPDIR exactly as provided', PROVIDED_TMPDIR)
    positive('TMPDIR unset (default /tmp)', None)
    positive('/tmp', '/tmp')
    if DARWIN:
        positive('/private/tmp', '/private/tmp')
        if PROVIDED_TMPDIR:
            positive('TMPDIR as provided without trailing slash', PROVIDED_TMPDIR.rstrip('/'))

    owned = mkdir(BASE / 'owned')
    # --- Noncanonical spellings ----------------------------------------------
    negative('relative path', 'tmp', expect='absolute path')
    negative('newline in path', str(owned) + '\nx', expect='newline')
    negative('dot component', str(BASE) + '/./owned', expect='Noncanonical')
    negative('dot-dot component', str(owned) + '/../owned', expect='Noncanonical')

    # --- Symlinks a non-root user could replace -----------------------------
    os.symlink(str(owned), str(BASE / 'user-link'))
    negative('user-owned symlink in the spelling', str(BASE / 'user-link'), expect='Untrusted staging ancestor')
    if SUDO:
        user_writable = mkdir(BASE / 'user-writable', 0o700)
        root_link(user_writable / 'root-link', owned)
        negative('root-owned symlink in a user-owned directory', str(user_writable / 'root-link'), expect='Untrusted staging ancestor')
        sticky = root_dir(BASE / 'root-sticky', 0o1777)
        root_link(sticky / 'root-link', owned)
        negative('root-owned symlink in a sticky world-writable directory', str(sticky / 'root-link'), expect='Untrusted staging ancestor')
        locked = root_dir(BASE / 'root-locked', 0o755)
        link = root_link(locked / 'root-link', owned)
        r = parent(str(link))
        record('root-owned symlink in a root-owned 0755 directory resolves to its physical target',
               'PASS' if r['rc'] == 0 and r['stdout'].strip() == str(owned) else 'FAIL', r)
        # Swap after resolution: the admitted root stays on the original physical
        # target, and the swapped spelling is judged afresh.
        swapped = mkdir(BASE / 'swapped-target', 0o777)
        script = (ROUND_TRIP.replace('cleanup_staging;', '') + '; sudo -n ln -sfn "$S" "$T"; '
                  'verify_root "$WORK_ROOT" "$WORK_ID" && echo ROOT_STILL_VERIFIED; '
                  'case "$WORK_ROOT" in "$O"/*) echo ROOT_ON_ORIGINAL ;; esac; '
                  'trusted_parent "$T" temp && echo SWAPPED_ACCEPTED; cleanup_staging; '
                  'n=$(ls -A "$S" | wc -l); echo "SWAPPED_ENTRIES=${n// /}"')
        r = bash(script, {'TMPDIR': str(link), 'S': str(swapped), 'T': str(link), 'O': str(owned)})
        out = r['stdout']
        ok = all(m in out for m in ('ROOT_STILL_VERIFIED', 'ROOT_ON_ORIGINAL', 'SWAPPED_ENTRIES=0')) and 'SWAPPED_ACCEPTED' not in out
        record('symlink swapped after resolution', 'PASS' if ok else 'FAIL', r)
    else:
        for name in ('root-owned symlink in a user-owned directory', 'root-owned symlink in a sticky world-writable directory',
                     'root-owned symlink in a root-owned 0755 directory resolves to its physical target', 'symlink swapped after resolution'):
            record(name, 'BLOCKED_PRIVILEGE', {})

    # --- Writable / foreign ancestors and final directory --------------------
    ww = mkdir(BASE / 'world-writable', 0o777)
    negative('world-writable non-sticky ancestor', str(mkdir(ww / 'child')), expect='Writable staging ancestor')
    gw = mkdir(BASE / 'group-writable', 0o770)
    negative('group-writable non-sticky ancestor', str(mkdir(gw / 'child')), expect='Writable staging ancestor')
    us = mkdir(BASE / 'user-sticky', 0o1777)
    negative('sticky world-writable ancestor not owned by root', str(mkdir(us / 'child')), expect='Writable staging ancestor')
    if SUDO:
        foreign = root_dir(BASE / 'foreign', 0o755)
        sudo('chown', 'nobody', str(foreign))
        sudo('install', '-d', '-o', str(os.getuid()), '-m', '700', str(foreign / 'child'))
        ROOT_PATHS.append(foreign / 'child')
        negative('foreign-owned ancestor', str(foreign / 'child'), expect='Untrusted ancestor owner')
        negative('final directory not owned by the user', str(root_dir(BASE / 'root-final', 0o755)), expect='private, owned staging parent')
        foreign_home = root_dir(BASE / 'foreign-home', 0o700)
        negative('HOME not owned by the user', str(foreign_home), kind='home')
    else:
        for name in ('foreign-owned ancestor', 'final directory not owned by the user', 'HOME not owned by the user'):
            record(name, 'BLOCKED_PRIVILEGE', {})
    # A writable HOME is already refused by the component walk (its last component
    # is walked too), before the final ownership rule; either refusal is correct.
    home_writable = ['Writable staging ancestor', 'private, owned staging parent']
    negative('HOME with group write', str(mkdir(BASE / 'home-group', 0o770)), kind='home', expect=home_writable)
    negative('HOME with other write', str(mkdir(BASE / 'home-other', 0o707)), kind='home', expect=home_writable)
    negative('missing staging parent', str(BASE / 'does-not-exist'))
except Exception as error:  # setup failures are failures
    record('fixture/bootstrap', 'SETUP_ERROR', {'error': repr(error)})
finally:
    for p in reversed(ROOT_PATHS):
        subprocess.run(['sudo', '-n', 'rm', '-rf', str(p)], capture_output=True)
    shutil.rmtree(BASE, ignore_errors=True)

report = {'schema': 'staging-parent-defaults.posix.v1', 'source': str(SOURCE),
          'sourceSha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'system': platform.system(),
          'bash': subprocess.run([BASH, '--version'], capture_output=True, text=True).stdout.splitlines()[:1],
          'providedTMPDIR': PROVIDED_TMPDIR, 'sudo': bool(SUDO), 'fixtureRemoved': not BASE.exists(), 'results': RESULTS}
text = json.dumps(report, indent=2, ensure_ascii=False)
if REPORT:
    REPORT.write_text(text + '\n', encoding='utf-8')
print(text)
for row in RESULTS:
    print(row['status'], row['case'], file=sys.stderr)
sys.exit(1 if any(r['status'] in ('FAIL', 'SETUP_ERROR') for r in RESULTS) else (2 if any(r['status'] != 'PASS' for r in RESULTS) else 0))
