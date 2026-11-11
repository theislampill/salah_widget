#!/usr/bin/env python3
"""R0015 21-05 native Linux HOME-owner proof; no product/source modifications.

Usage: python3 r0015-linux-owner-proof.py /absolute/install.sh
The supervisor may use existing passwordless sudo. It only changes ownership or
permissions of one newly-created /tmp/r0015-owner-* fixture. Every production
function executes after dropping to the isolated numeric consumer UID/GID with
no supplementary groups. No account, real home, profile, or global path changes.
Without distinct-UID capability, emit a non-passing acquisition receipt plus a
local same-UID positive. A user-namespace root with one mapped UID is insufficient.
Exit 0: native required controls PASS; 1: exercised failure; 2: acquisition/setup gap.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import traceback


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(path):
    p = Path(path)
    s = p.lstat()
    result = dict(path=str(p), uid=s.st_uid, gid=s.st_gid,
                  mode=oct(stat.S_IMODE(s.st_mode)), device=s.st_dev, inode=s.st_ino,
                  symlink=stat.S_ISLNK(s.st_mode), physical=str(p.resolve()))
    if stat.S_ISREG(s.st_mode):
        result.update(bytes=s.st_size, sha256=digest(p.read_bytes()))
    return result


def proc_identity():
    status = Path('/proc/self/status').read_text()
    fields = {line.split(':', 1)[0]: line.split(':', 1)[1].strip()
              for line in status.splitlines()
              if line.startswith(('Uid:', 'Gid:', 'Groups:', 'CapInh:', 'CapPrm:',
                                  'CapEff:', 'CapBnd:', 'NoNewPrivs:'))}
    return dict(uid=os.getuid(), euid=os.geteuid(), gid=os.getgid(), groups=os.getgroups(),
                proc_status=fields,
                uid_map=Path('/proc/self/uid_map').read_text(),
                gid_map=Path('/proc/self/gid_map').read_text())


def mapped(number, filename):
    return any(int(row.split()[0]) <= number < int(row.split()[0]) + int(row.split()[2])
               for row in Path('/proc/self/' + filename).read_text().splitlines())


def command(argv, **kwargs):
    r = subprocess.run(argv, capture_output=True, text=True, timeout=25, **kwargs)
    return dict(command=argv, exit=r.returncode, stdout=r.stdout, stderr=r.stderr)


def function(text, name):
    start = '^' + re.escape(name) + r'\(\) \{'
    match = re.search(start + r'[^\n]*\}\n', text, re.M)
    if not match:
        match = re.search(start + r'\n.*?^\}\n', text, re.M | re.S)
    if not match:
        raise ValueError('Missing exact production function: ' + name)
    return match.group()


def snapshot(paths):
    answer = {}
    for base in paths:
        base = Path(base)
        entries = [base] + sorted(base.rglob('*')) if base.is_dir() and not base.is_symlink() else [base]
        for path in entries:
            if path.exists() or path.is_symlink():
                answer[str(path)] = identity(path)
    return answer


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main(args):
    source_path = Path(args.SourceFile).resolve(strict=True)
    require(source_path.is_file(), 'SourceFile must be a regular file')
    source = source_path.read_bytes()
    text = source.decode('utf-8')
    names = ('need_cmd', 'err', 'warn', 'path_identity', 'trusted_parent',
             'verify_root', 'guard_owned_path', 'initialize_staging', 'cleanup_staging')
    fragments = {name: function(text, name) for name in names}
    helper = fragments['trusted_parent']
    old_guard = '[ "$owner" = "$uid" ] && [ -O "$path" ] && (( (8#$mode & 0022) == 0 ))'
    new_guard = '(( (8#$mode & 0022) == 0 ))'
    require(helper.count(old_guard) == 1, 'Terminal HOME owner guard source drift')
    mutant_helper = helper.replace(old_guard, new_guard, 1)
    library = '\n'.join(fragments.values())
    mutant_library = library.replace(helper, mutant_helper, 1)
    result = dict(schema='r0015-native-owner-proof/v1', source=str(source_path),
                  source_sha256=digest(source), fixture_sha256=digest(Path(__file__).read_bytes()),
                  native_host=dict(system=platform.system(), release=platform.release(),
                                   platform=platform.platform(), machine=platform.machine()),
                  supervisor=proc_identity(), source_functions=list(names),
                  source_fragment_sha256=digest(library.encode()),
                  mutation=dict(original_guard=old_guard, replacement=new_guard,
                                mutant_fragment_sha256=digest(mutant_library.encode()),
                                scope='Only terminal self-owner and -O conjunction removed; mode, ancestor and physical guards preserved'),
                  results=[], observations={}, limits=['Filesystem admission/lifetime fixture only; no browser installation.',
                                      'No real home/account/profile/network/clipboard modification.',
                                      'Retained fixture files intentionally left for evidence.'])
    require(platform.system() == 'Linux', 'This fixture requires actual Linux')
    subject_uid = args.consumer_uid
    subject_gid = args.consumer_gid
    privileged = (os.geteuid() == 0 and subject_uid != 0 and
                  mapped(subject_uid, 'uid_map') and mapped(subject_gid, 'gid_map'))
    result['requested_subject'] = dict(uid=subject_uid, gid=subject_gid)
    result['acquisition'] = dict(privileged_distinct_uid_available=privileged,
                               sudo=shutil.which('sudo'), elevated=args._elevated)

    # Re-execute only this bounded supervisor through existing passwordless sudo.
    # Production source is never executed by the supervisor's root identity.
    if not privileged and not args._elevated and not args.no_sudo and shutil.which('sudo'):
        probe = command([shutil.which('sudo'), '-n', 'true'])
        if probe['exit'] == 0:
            child = command([shutil.which('sudo'), '-n', '--', sys.executable,
                             str(Path(__file__).resolve()), str(source_path),
                             '--consumer-uid', str(subject_uid), '--consumer-gid', str(subject_gid),
                             '--_elevated'])
            try:
                receipt = json.loads(child['stdout'])
                receipt['sudo_acquisition'] = dict(probe=probe, command=child['command'],
                                                   exit=child['exit'], stderr=child['stderr'],
                                                   original_supervisor=result['supervisor'])
                return receipt, child['exit']
            except (ValueError, TypeError):
                result['acquisition']['sudo_child'] = child
        else:
            result['acquisition']['sudo_probe'] = probe

    if not privileged:
        subject_uid, subject_gid = os.getuid(), os.getgid()
        result['limits'].append('Required foreign-owner/matched-pair and owner-mutant controls unavailable here; local same-UID positive is not their substitute.')
    result['executing_subject'] = dict(uid=subject_uid, gid=subject_gid,
                                      matches_requested=(subject_uid == args.consumer_uid and subject_gid == args.consumer_gid))
    fixture_root = Path(tempfile.mkdtemp(prefix='r0015-owner-', dir='/tmp'))
    fixture_root.chmod(0o755)
    result['fixture'] = str(fixture_root)
    fixture_home = fixture_root / 'subject-home'
    fixture_tmp = fixture_root / 'subject-tmp'
    fixture_bin = fixture_root / 'bin'
    fixture_home.mkdir(mode=0o755)
    fixture_tmp.mkdir(mode=0o700)
    fixture_bin.mkdir(mode=0o755)
    events = fixture_root / 'mktemp-events.jsonl'
    events.write_text('')
    events.chmod(0o600)
    victim = fixture_root / 'outside-sentinel.txt'
    victim.write_bytes(b'unchanged outside sentinel\n')
    victim.chmod(0o644)
    if privileged:
        # All subjects below are fresh children; no host account or parent change.
        for path in (fixture_root, fixture_home, fixture_bin, victim):
            os.chown(path, 0, 0)
        for path in (fixture_tmp, events):
            os.chown(path, subject_uid, subject_gid)
    native_mktemp = shutil.which('mktemp')
    native_bash = shutil.which('bash')
    require(native_mktemp and native_bash, 'Required native bash/mktemp missing')
    wrapper = fixture_bin / 'mktemp'
    wrapper.write_text('#!' + sys.executable + '\n' +
                      'import json,os,sys\nfrom pathlib import Path\n' +
                      'root=Path(os.environ["TASK_FIXTURE_ROOT"]).resolve(strict=True)\n' +
                      'target=Path(sys.argv[-1]); parent=target.parent.resolve(strict=True)\n' +
                      'if parent != root and root not in parent.parents: raise SystemExit("fixture mktemp escape refused")\n' +
                      'with open(os.environ["TASK_MKTEMP_EVENTS"],"a") as out: out.write(json.dumps({"argv":sys.argv[1:],"uid":os.getuid(),"gid":os.getgid()})+"\\n")\n' +
                      'os.execv(' + repr(native_mktemp) + ',[' + repr(native_mktemp) + ']+sys.argv[1:])\n')
    wrapper.chmod(0o755)
    result['native_tools'] = {name: shutil.which(name) for name in ('bash', 'stat', 'id', 'mktemp', 'python3', 'curl')}
    result['bash_version'] = command([native_bash, '--version'])
    result['filesystem'] = command(['stat', '-f', '-c', '%T', str(fixture_root)])
    result['parents'] = [identity(p) for p in ('/', '/tmp', fixture_root, fixture_home, fixture_tmp)]
    env = {'PATH': str(fixture_bin) + ':/usr/bin:/bin', 'LANG': 'C.UTF-8',
           'HOME': str(fixture_home), 'TMPDIR': str(fixture_tmp),
           'TASK_FIXTURE_ROOT': str(fixture_root), 'TASK_MKTEMP_EVENTS': str(events)}
    setup = 'set -Eeuo pipefail\nPLATFORM=linux\nDRY_RUN=0\nWORK_ROOT=""; WORK_ID=""; BUNDLE_ROOT=""; BUNDLE_ID=""; DOWNLOAD_ROOT=""; PRESET_ROOT=""\n'

    def drop_subject():
        os.setgroups([])
        os.setgid(subject_gid)
        os.setuid(subject_uid)

    def run(body, mutant=False):
        kwargs = dict(env=env, cwd=fixture_root)
        if privileged:
            kwargs['preexec_fn'] = drop_subject
        return command([native_bash, '--noprofile', '--norc', '-c',
                        setup + (mutant_library if mutant else library) + '\n' + body], **kwargs)

    def check(name, action):
        try:
            detail = action()
            result['results'].append(dict(case=name, pass_=True, status='PASS', executed=True, detail=detail))
        except Exception as error:
            result['results'].append(dict(case=name, pass_=False, status='FAIL', executed=True,
                                          error=str(error)))

    # Record the actual source consumer identity, including post-drop capabilities.
    actor = run('id -u; id -g; id -G; /usr/bin/python3 -c \'import json,os,pathlib; print(json.dumps({"uid":os.getuid(),"gid":os.getgid(),"groups":os.getgroups(),"status":{l.split(":",1)[0]:l.split(":",1)[1].strip() for l in pathlib.Path("/proc/self/status").read_text().splitlines() if l.startswith(("CapEff:","CapPrm:","NoNewPrivs:"))}}))\'\n')
    result['subject_receipt'] = actor
    require(actor['exit'] == 0 and actor['stdout'].splitlines()[0] == str(subject_uid),
            'Subject identity/bootstrap mismatch')
    actor_fields = json.loads(actor['stdout'].splitlines()[-1])
    require(actor_fields['uid'] == subject_uid and actor_fields['gid'] == subject_gid,
            'Actual Python subject UID/GID mismatch')
    if privileged:
        require(actor_fields['groups'] == [] and
                int(actor_fields['status']['CapEff'], 16) == 0 and
                int(actor_fields['status']['CapPrm'], 16) == 0,
                'Native subject retained supplementary groups or capabilities')
    subjects = [fixture_home, fixture_tmp, victim]
    result['legacy_tmp_premise'] = dict(subject_uid=subject_uid, temporary_parent=identity('/tmp'),
                                        comment='Old wrong-owner fixture selected /tmp without checking owner or mode.')
    result['source_guard_parse'] = command([native_bash, '-n', '-c', setup + library])
    result['mutant_guard_parse'] = command([native_bash, '-n', '-c', setup + mutant_library])
    require(result['source_guard_parse']['exit'] == 0 and result['mutant_guard_parse']['exit'] == 0,
            'Source or owner-only mutant has a parse failure')

    def negative():
        before = snapshot(subjects)
        before_events = events.read_bytes()
        actual = run('initialize_staging\n')
        after = snapshot(subjects)
        result['observations']['negative'] = dict(execution=actual, before=before, after=after,
                                                   mktemp_events=events.read_text())
        require(actual['exit'] != 0 and 'Use a private, owned staging parent' in actual['stderr'],
                'Foreign HOME did not reach expected owner refusal: ' + repr(actual))
        require(actual['stdout'] == '', 'Rejected initializer returned usable output')
        require(before == after and before_events == events.read_bytes(), 'Rejected HOME caused an output/mktemp effect')
        return dict(execution=actual, before=before, after=after, mktemp_calls=0)

    def negative_mutant():
        before = snapshot(subjects)
        before_events = events.read_bytes()
        original = run('trusted_parent "$HOME" home\n')
        mutation = run('trusted_parent "$HOME" home\n', mutant=True)
        result['observations']['owner_mutant'] = dict(original=original, mutant=mutation,
                                                       before=before, after=snapshot(subjects),
                                                       mktemp_events=events.read_text())
        require(original['exit'] != 0 and 'Use a private, owned staging parent' in original['stderr'],
                'Original helper did not reject only final HOME owner')
        require(mutation['exit'] == 0 and mutation['stdout'] == str(fixture_home) + '\n',
                'Owner-only mutant did not admit the foreign parent: ' + repr(mutation))
        require(before == snapshot(subjects) and before_events == events.read_bytes(), 'Helper discriminator changed subjects')
        return dict(original=original, mutant=mutation, mutant_rejected_by_oracle=True,
                    oracle='foreign HOME must not be returned by actual trusted_parent; later mktemp is not executed')

    if privileged:
        check('R0015-A05 foreign UID0 HOME mode0755 refused before staging effects', negative)
        check('R0015-A07 terminal owner-only mutant admits foreign HOME; original refuses', negative_mutant)
        # The mandatory positive changes this same HOME's owner only; mode and ancestors remain.
        pair_before = identity(fixture_home)
        os.chown(fixture_home, subject_uid, 0)
        result['matched_pair_change'] = dict(before=pair_before, after=identity(fixture_home),
                                             difference='HOME UID only; same GID0, path, device/inode, mode0755 and ancestors')
    else:
        for name in ('R0015-A05 foreign UID0 HOME mode0755 admission', 'R0015-A07 terminal owner-only mutant'):
            result['results'].append(dict(case=name, pass_=False, status='BLOCKED', executed=False,
                                          reason='No privileged supervisor with mapped distinct subject UID/GID; no qualified foreign-owner fixture'))

    def positive():
        before_victim = identity(victim)
        actual = run('''initialize_staging
guard_owned_path "$BUNDLE_ROOT" "$BUNDLE_ID" "$BUNDLE_ROOT/retained-proof.txt" file
(umask 077; printf 'retained fixture proof\\n' > "$BUNDLE_ROOT/retained-proof.txt")
printf '%s\\n%s\\n%s\\n%s\\n' "$WORK_ROOT" "$WORK_ID" "$BUNDLE_ROOT" "$BUNDLE_ID"
cleanup_staging
''')
        result['observations']['positive'] = dict(execution=actual, mktemp_events=events.read_text())
        require(actual['exit'] == 0, 'Owned HOME positive failed: ' + repr(actual))
        lines = actual['stdout'].splitlines()
        require(len(lines) == 4, 'Positive returned polluted or missing root identities')
        scratch, scratch_id, bundle, bundle_id = lines
        require(Path(scratch).parent == fixture_tmp and not Path(scratch).exists(), 'Scratch scope or actual cleanup incorrect')
        require(Path(bundle).parent == fixture_home, 'Retained bundle is outside fixture HOME')
        bundle_meta = identity(bundle)
        require(bundle_meta['uid'] == subject_uid and bundle_meta['mode'] == '0o700' and not bundle_meta['symlink'],
                'Retained bundle owner/mode/type incorrect')
        fields = bundle_id.split(':')
        require(fields == [str(bundle_meta['device']), str(bundle_meta['inode']), str(subject_uid), '700'],
                'Native retained identity differs from source receipt')
        require(scratch_id.split(':')[-2:] == [str(subject_uid), '700'], 'Native scratch owner/mode not0700')
        fresh_env = dict(env, TASK_RETAINED_PROOF=str(Path(bundle) / 'retained-proof.txt'))
        kwargs = dict(env=fresh_env, cwd=fixture_root)
        if privileged:
            kwargs['preexec_fn'] = drop_subject
        consumer = command([native_bash, '--noprofile', '--norc', '-c',
                            'set -e; id -u; cat "$TASK_RETAINED_PROOF"'], **kwargs)
        result['observations']['positive']['fresh_consumer'] = consumer
        require(consumer['exit'] == 0 and consumer['stdout'] == str(subject_uid) + '\nretained fixture proof\n',
                'Fresh consumer could not read exact retained bytes')
        require(identity(victim) == before_victim, 'Outside sentinel changed')
        helper_positive = run('trusted_parent "$HOME" home\n')
        mutant_positive = run('trusted_parent "$HOME" home\n', mutant=True)
        require(helper_positive['exit'] == 0 and mutant_positive['exit'] == 0 and
                helper_positive['stdout'] == mutant_positive['stdout'] == str(fixture_home) + '\n',
                'Healthy helper or owner-only mutant disabled the positive')
        return dict(execution=actual, scratch_id=scratch_id, bundle_identity=bundle_meta,
                    retained_file=identity(Path(bundle) / 'retained-proof.txt'), fresh_consumer=consumer,
                    original_helper=helper_positive, mutant_helper=mutant_positive,
                    mktemp_events=[json.loads(line) for line in events.read_text().splitlines()])

    check('R0015-A06 matched native owned HOME positive' if privileged else
          'local same-UID owned HOME positive (not matched foreign-owner acceptance)', positive)
    result['post_state'] = snapshot(subjects)
    result['native_distinct_uid_claim'] = privileged
    failed = any(row['status'] == 'FAIL' for row in result['results'])
    result['status'] = 'FAIL' if failed else ('PASS' if privileged else 'BLOCKED_ACQUISITION')
    return result, 1 if failed else (0 if privileged else 2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('SourceFile')
    parser.add_argument('--consumer-uid', type=int, default=1000)
    parser.add_argument('--consumer-gid', type=int, default=1000)
    parser.add_argument('--no-sudo', action='store_true')
    parser.add_argument('--_elevated', action='store_true', help=argparse.SUPPRESS)
    options = parser.parse_args()
    try:
        receipt, exit_code = main(options)
    except Exception as exc:
        receipt = dict(schema='r0015-native-owner-proof/v1', status='ERROR',
                       results=[dict(case='fixture bootstrap', pass_=False, status='ERROR',
                                     executed=False, error=str(exc))], traceback=traceback.format_exc())
        exit_code = 2
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    raise SystemExit(exit_code)
