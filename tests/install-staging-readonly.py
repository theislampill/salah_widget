#!/usr/bin/env python3
"""Apple Bash staging admission must not need an implicit temporary file.

Run the exact source prefix and trusted_parent under a native sandbox denying
all filesystem writes and network. This is a read-only helper qualification,
not a full installer invocation. Each single-site here-string revert must fail
the same /tmp admission oracle. Keep all raw streams and mutant bytes.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import stat
import subprocess
import sys
import tempfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def snapshot(root):
    rows = []
    for path in [root, *sorted(root.rglob('*'))]:
        info = path.lstat()
        row = dict(path=path.relative_to(root).as_posix(), mode=info.st_mode,
                   uid=info.st_uid, gid=info.st_gid, size=info.st_size,
                   mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns)
        if stat.S_ISREG(info.st_mode):
            row['sha256'] = sha(path.read_bytes())
        elif stat.S_ISLNK(info.st_mode):
            row['target'] = os.readlink(path)
        rows.append(row)
    return rows


def main():
    source = Path(sys.argv[1]).resolve(strict=True)
    raw = source.read_bytes()
    text = raw.decode('utf-8')
    boundary = "\nprintf '\\nSalah Widget Installer\\n\\n'"
    require(text.count(boundary) == 1, 'Actual source entry boundary changed')
    prefix = text.split(boundary)[0] + '\n'
    shell, sandbox = Path('/bin/bash'), Path('/usr/bin/sandbox-exec')
    version = subprocess.check_output([str(shell), '--version'], text=True).splitlines()[0]
    require(platform.system() == 'Darwin' and 'version 3.2.' in version,
            'Native macOS Apple /bin/bash 3.2 is required; no fallback')
    require(sandbox.is_file() and os.access(sandbox, os.X_OK), 'Native sandbox-exec unavailable')
    require(Path('/tmp').is_symlink() and Path('/tmp').resolve(strict=True) == Path('/private/tmp'),
            'The required native /tmp -> /private/tmp premise differs')
    root = Path(tempfile.mkdtemp(prefix='salah-staging-readonly-')).resolve()
    root.chmod(0o700)
    subject, evidence = root / 'subject', root / 'evidence'
    subject.mkdir(mode=0o700)
    evidence.mkdir(mode=0o700)
    for name in ('home', 'temp'):
        (subject / name).mkdir(mode=0o700)
    policy = root / 'sandbox.sb'
    policy.write_text('(version 1)\n(allow default)\n(deny network*)\n'
                      '(deny file-write*)\n(allow file-write-data (literal "/dev/null"))\n', encoding='utf-8')
    env = dict(os.environ, HOME=str(subject/'home'), TMPDIR=str(subject/'temp'),
               DRY_RUN='0', NO_OPEN='1', SALAH_INSTALL_SOURCE='github')
    env.pop('BASH_ENV', None)
    # PATH and native stat/id/uname identities are not replaced.
    env.pop('ENV', None)
    runs, results = [], []

    def run(name, library, command, argument):
        script = subject / (name + '.sh')
        script.write_text(library + '\n' + command + '\n', encoding='utf-8')
        before = snapshot(subject)
        # The prefix refuses positional arguments; use the environment for the
        # helper parameter and give the source the same zero-argument premise.
        argv = [str(sandbox), '-f', str(policy), str(shell), '--noprofile', '--norc', str(script)]
        child_env = dict(env, READONLY_STAGING_ARGUMENT=argument)
        observed = dict(name=name, command=argv, argument=argument,
                        script_sha256=sha(script.read_bytes()), before=before)
        process = subprocess.Popen(argv, env=child_env, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=True)
        try:
            stdout, stderr = process.communicate(timeout=30)
            observed.update(exit=process.returncode, timedOut=False, cleanupSignal=None)
        except subprocess.TimeoutExpired as error:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate(timeout=5)
            observed.update(exit=process.returncode, timedOut=True, cleanupSignal='SIGKILL owned process group')
        after = snapshot(subject)
        observed.update(after=after, unchanged=before == after,
                        stdout=stdout.decode('utf-8', errors='replace'),
                        stderr=stderr.decode('utf-8', errors='replace'),
                        stdout_sha256=sha(stdout), stderr_sha256=sha(stderr))
        (evidence/(name+'.stdout.bin')).write_bytes(stdout)
        (evidence/(name+'.stderr.bin')).write_bytes(stderr)
        (evidence/(name+'.json')).write_text(json.dumps(observed, indent=2)+'\n', encoding='utf-8')
        runs.append(observed)
        return observed

    def admission_ok(row):
        return (row['exit'] == 0 and not row['timedOut'] and row['unchanged']
                and row['stdout'] == '/private/tmp\n' and row['stderr'] == '')

    def record(name, ok, detail):
        results.append(dict(case=name, pass_=bool(ok), detail=detail))

    deny = run('write-denial', '', ': > "$READONLY_STAGING_ARGUMENT"', str(subject/'forbidden'))
    record('native sandbox denies a real write',
           deny['exit'] not in (None, 0) and not deny['timedOut'] and deny['unchanged']
           and not (subject/'forbidden').exists() and bool(deny['stderr']), 'write-denial')
    command = 'trusted_parent "$READONLY_STAGING_ARGUMENT" temp'
    for name, path in (('os-symlink', '/tmp'), ('physical-path', '/private/tmp')):
        row = run(name, prefix, command, path)
        record('read-only trusted_parent '+path, admission_ok(row), name)
    # Only the two spelling-walk reads are mutated. The physical walk and all
    # ownership/mode/symlink checks remain byte-for-byte the supplied source.
    pattern = re.compile(r'^      IFS=: read -r dev inode owner mode (?:<<< "\$fields"|< <\(printf \'%s\\n\' "\$fields"\))$', re.M)
    matches = list(pattern.finditer(prefix))
    require(len(matches) == 2, 'Two exact B2 spelling-walk read sites are required')
    for number, match in enumerate(matches, 1):
        changed = prefix[:match.start()] + '      IFS=: read -r dev inode owner mode <<< "$fields"' + prefix[match.end():]
        row = run('here-string-'+str(number), changed, command, '/tmp')
        record('single-site here-string '+str(number)+' is killed',
               not admission_ok(row) and row['exit'] not in (None, 0) and not row['timedOut']
               and row['unchanged'] and 'cannot create temp file for here document:' in row['stderr'], 'here-string-'+str(number))
    record('supplied source bytes remain unchanged', source.read_bytes() == raw, str(source))
    report = dict(schema='r0016-staging-readonly.apple-bash.v1', source=str(source),
                  source_sha256=sha(raw), test_sha256=sha(Path(__file__).read_bytes()),
                  fixture=str(root), host=dict(system=platform.system(), platform=platform.platform(),
                      bash=str(shell), bash_version=version, bash_sha256=sha(shell.read_bytes()),
                      sandbox=str(sandbox), sandbox_sha256=sha(sandbox.read_bytes())),
                  policy_sha256=sha(policy.read_bytes()), results=results, observations=runs,
                  scope='Exact trusted_parent helper only; all-file-write denial and two revert mutants. No full-entry or global transport observation claim.')
    print(json.dumps(report, indent=2))
    return 0 if all(row['pass_'] for row in results) else 1


if __name__ == '__main__':
    sys.exit(main())
