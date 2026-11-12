#!/usr/bin/env python3
"""Source-free Bash startup discriminator with unchanged transport denial.

This diagnostic adds raw syscall arguments and phase facts to a private copy of
the published observer prefix. It never executes installer source and never
filters or excuses a recorded syscall. Default and explicit native shell
environment controls remain distinct observations.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import secrets
import socket
import subprocess
import sys
import time

sys.dont_write_bytecode = True
SUPPORT_SHA = '8051d53a6dfdd64a86171c8e1c0cedb0b8da1b843cf30066af99c39e194c7328'
HARNESS_SHA = '0b420c20e3eb1ec2670713975ceeb54b7af03d1df50a507093d343816786af00'
PREPARATION_SHA = 'adb7c47a6416b51bf96b6647e500bfba4e2d206a50a408a0e331f16d61ea9161'
SECONDS, CLEANUP_SECONDS, CAPTURE_BYTES = 30, 5, 1024 * 1024
OLD_ROW = "row = {'pid': request.pid, 'syscall': names.get(request.data.nr, request.data.nr), 'decision': 'DENIED_EPERM'}"
NEW_ROW = """row = {'pid': request.pid, 'syscall': names.get(request.data.nr, request.data.nr), 'decision': 'DENIED_EPERM',
                           'arguments': [int(arg) for arg in request.data.args], 'monotonicNs': time.monotonic_ns(),
                           'initialChildPid': child}
                    for key, part in (('processStat', 'stat'), ('commandLine', 'cmdline')):
                        try:
                            with open('/proc/' + str(request.pid) + '/' + part, 'rb') as stream:
                                raw_fact = stream.read(8193)
                            if len(raw_fact) > 8192: raise RuntimeError('Process fact exceeds bound')
                            row[key] = {'bytesHex': raw_fact.hex(), 'sha256': hashlib.sha256(raw_fact).hexdigest()}
                        except OSError as problem: row[key] = {'error': str(problem)}
                    try: row['executable'] = os.readlink('/proc/' + str(request.pid) + '/exe')
                    except OSError as problem: row['executable'] = {'error': str(problem)}
                    try:
                        with open(os.environ['R0016_READY'], 'rb') as stream: ready_fact = stream.read(8193)
                        if len(ready_fact) > 8192: raise RuntimeError('Readiness fact exceeds bound')
                        row['readinessAtNotification'] = {'exists': True, 'bytesHex': ready_fact.hex()}
                    except FileNotFoundError: row['readinessAtNotification'] = {'exists': False, 'bytesHex': ''}"""
BOOTSTRAP = 'printf "%s\\t%s\\n" "$$" "$R0016_NONCE" >> "$R0016_READY"\n'
NEUTRAL = 'printf "R0016_NEUTRAL\\t%s\\t%s\\n" "$$" "$R0016_NONCE"'
CONTROL = '''import errno, json, os, pathlib, socket
rows=[]
for name,family,kind in [('unix',socket.AF_UNIX,socket.SOCK_STREAM),('tcp',socket.AF_INET,socket.SOCK_STREAM),('udp',socket.AF_INET,socket.SOCK_DGRAM)]:
    try:
        s=socket.socket(family,kind);s.close();rows.append({'kind':name,'denied':False})
    except OSError as e:rows.append({'kind':name,'denied':e.errno==errno.EPERM,'errno':e.errno})
outside=pathlib.Path(os.environ['R0016_OUTSIDE'])
try:outside.write_bytes(b'forbidden');outside_denied=False
except OSError as e:outside_denied=e.errno in (errno.EROFS,errno.EACCES,errno.EPERM)
inside=pathlib.Path(os.environ['HOME'])/'allowed-write';inside.write_bytes(os.environ['R0016_NONCE'].encode('ascii'))
print(json.dumps({'pid':os.getpid(),'transports':rows,'outsideDenied':outside_denied,'insideWriteAllowed':inside.read_bytes()==os.environ['R0016_NONCE'].encode('ascii')}))
raise SystemExit(0 if outside_denied and all(r['denied'] for r in rows) else 2)
'''


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load_support(path):
    assert path.is_file() and not path.is_symlink() and digest(path.read_bytes()) == SUPPORT_SHA
    spec = importlib.util.spec_from_file_location('r0016_linux_startup_support', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def derive_observer(raw):
    assert digest(raw) == HARNESS_SHA
    text = raw.decode('utf-8')
    # Stop immediately after the early --sandbox-child dispatch. No CLI, source
    # extraction, fixture campaign or installer function can run from this file.
    anchor = 'if len(sys.argv) > 1 and sys.argv[1] == "--positive-child":'
    assert text.count(anchor) == 1
    prefix = text.split(anchor)[0]
    assert prefix.count(OLD_ROW) == 1
    derived = prefix.replace(OLD_ROW, NEW_ROW, 1)
    ast.parse(derived)
    return derived.encode('utf-8')


def validate_controlled_transport(record, control):
    """Require raw, source-free socket telemetry; never filter retained rows."""
    probe = record['controlledProbe']
    pid, bash_pid = probe['pid'], record['bashPid']
    assert type(pid) is int and pid > 0 and type(bash_pid) is int and bash_pid > 0
    physical = record['pythonBinding']['physical']
    assert type(physical) is str and physical.startswith('/')
    raw_rows = record['transportAttempts']
    assert isinstance(raw_rows, list) and all(isinstance(row, dict) for row in raw_rows)
    # Bash can exec the last Python command without changing PID. Its earlier
    # executable observations remain intact; only the exact Python image can
    # establish this controlled telemetry proof.
    selected = [(i, row) for i, row in enumerate(raw_rows)
                if row.get('pid') == pid and row.get('executable') == physical]
    assert len(selected) == 3, 'Controlled Python socket telemetry missing or unexpected'
    expected = [(int(socket.AF_UNIX), int(socket.SOCK_STREAM), 0),
                (int(socket.AF_INET), int(socket.SOCK_STREAM), 0),
                (int(socket.AF_INET), int(socket.SOCK_DGRAM), 0)]
    expected_command = ('/usr/bin/python3\0' + str(control) + '\0').encode('utf-8')
    expected_ready = (str(bash_pid) + '\t' + record['nonce'] + '\n').encode('ascii')
    start_ticks = []
    for (_, row), (family, kind, protocol) in zip(selected, expected):
        assert row['syscall'] == 'socket' and row['decision'] == 'DENIED_EPERM'
        assert type(row['pid']) is int and row['pid'] == pid
        assert type(row['initialChildPid']) is int and row['initialChildPid'] == bash_pid
        args = row['arguments']
        assert isinstance(args, list) and len(args) == 6
        assert all(type(value) is int and 0 <= value < (1 << 64) for value in args)
        assert args[0] == family and args[2] == protocol
        assert args[1] in (kind, kind | int(socket.SOCK_CLOEXEC)), 'Unexpected socket type flags'
        assert type(row['monotonicNs']) is int
        assert record['startedMonotonicNs'] <= row['monotonicNs'] <= record['terminalObservedMonotonicNs']
        ready = row['readinessAtNotification']
        assert ready['exists'] is True and bytes.fromhex(ready['bytesHex']) == expected_ready
        command = row['commandLine']
        assert bytes.fromhex(command['bytesHex']) == expected_command and command['sha256'] == digest(expected_command)
        stat_fact = row['processStat']; raw_stat = bytes.fromhex(stat_fact['bytesHex'])
        assert stat_fact['sha256'] == digest(raw_stat) and int(raw_stat.split(b' ', 1)[0]) == pid
        start_ticks.append(int(raw_stat.rsplit(b') ', 1)[1].split()[19]))
    assert len(set(start_ticks)) == 1, 'Controlled process start identity differs'
    return {'pid': pid, 'rawRowIndexes': [i for i, _ in selected],
            'rawRowsRetained': len(raw_rows), 'processStartTicks': start_ticks[0],
            'pythonPhysical': physical, 'socketTupleOrder': expected,
            'readinessSha256': digest(expected_ready), 'commandSha256': digest(expected_command)}


def run_case(N, label, output, fixture, outside, observer, control, explicit, readiness, transport):
    case = output / label; case.mkdir(mode=0o700)
    owned = fixture / label; owned.mkdir(mode=0o700)
    subject = owned / 'subject'; subject.mkdir(mode=0o700)
    (subject / 'home').mkdir(); (subject / 'tmp').mkdir()
    bootstrap = owned / 'bootstrap.sh'; bootstrap.write_text(BOOTSTRAP, encoding='ascii')
    nonce = secrets.token_hex(16)
    env = {'HOME':str(subject / 'home'), 'TMPDIR':str(subject / 'tmp'), 'LANG':'C.UTF-8',
           'PATH':'/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE':'1',
           'R0016_NONCE':nonce, 'R0016_READY':str(owned / 'ready.txt'),
           'R0016_TRANSPORT_LOG':str(owned / 'network.jsonl'), 'R0016_OUTSIDE':str(outside / 'sentinel')}
    if readiness: env['BASH_ENV'] = str(bootstrap)
    if explicit: env.update(USER='root', LOGNAME='root', SHELL='/bin/bash')
    # Reuse the exact reviewed namespace/binding/environment constructor, then
    # replace only its source-free child argv after the explicit child boundary.
    template, common = N.build_command('original-unshare', fixture, owned, env, observer, control, case / 'unused-spec.json')
    boundary = template.index('--sandbox-child')
    script = NEUTRAL
    if transport: script += '\n/usr/bin/python3 "$R0016_CONTROL"'
    if transport:
        env['R0016_CONTROL'] = str(control)
        template, common = N.build_command('original-unshare', fixture, owned, env, observer, control, case / 'unused-spec.json')
        boundary = template.index('--sandbox-child')
    command = template[:boundary+1] + ['/bin/bash','--noprofile','--norc','-c',script]
    before = N.inventory(subject); outside_before = N.inventory(outside)
    N.save(case / 'subject.before.json',before); N.save(case / 'outside.before.json',outside_before)
    record = {'case':label,'nonce':nonce,'command':command,'commonFilesystemAndEnvironment':common,
              'environment':env,'subjectSeconds':SECONDS,'cleanupSeconds':CLEANUP_SECONDS,
              'captureLimitBytes':CAPTURE_BYTES,'productRowsExecuted':0,'classification':'INCOMPLETE',
              'pythonBinding':N.binding(Path('/usr/bin/python3'))}
    N.save(case / 'launch.json',record)
    process=None; start=time.monotonic_ns(); record['startedMonotonicNs']=start
    deadline=start+SECONDS*1000000000; record['deadlineMonotonicNs']=deadline
    try:
        with (case / 'stdout.raw').open('wb') as stdout, (case / 'stderr.raw').open('wb') as stderr:
            process=subprocess.Popen(command,cwd=owned,env=env,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,start_new_session=True)
            record['launchPid']=process.pid
            while True:
                code=process.poll(); clock=time.monotonic_ns()
                if any((case / (kind+'.raw')).stat().st_size>CAPTURE_BYTES for kind in ('stdout','stderr')):
                    raise RuntimeError('Capture limit exceeded')
                if code is not None:
                    record.update(returncode=code,terminalObservedMonotonicNs=clock)
                    if clock>=deadline: raise TimeoutError('Terminal first observed after deadline')
                    break
                if clock>=deadline: raise TimeoutError('Source-free subject deadline reached')
                time.sleep(0.01)
    except Exception as error:
        record['error']=type(error).__name__+': '+str(error)
    finally:
        if process is not None: record['cleanup']=N.cleanup(process,time.monotonic()+CLEANUP_SECONDS)
        after=N.inventory(subject);outside_after=N.inventory(outside)
        N.save(case / 'subject.after.json',after);N.save(case / 'outside.after.json',outside_after)
        record['elapsedSeconds']=(time.monotonic_ns()-start)/1000000000
        record['captures']={kind:N.binding(case / (kind+'.raw')) for kind in ('stdout','stderr')}
        log=owned/'network.jsonl';ready=owned/'ready.txt'
        record['transportAttempts']=[json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        record['transportLog']=N.binding(log) if log.exists() else None
        record['readiness']=N.fact(ready)
        record['subjectSnapshotUnchanged']=before['complete'] and after['complete'] and before['passes'][0]['rows']==after['passes'][0]['rows']
        record['outsideSnapshotUnchanged']=outside_before['complete'] and outside_after['complete'] and outside_before['passes'][0]['rows']==outside_after['passes'][0]['rows']
        try:
            lines=(case/'stdout.raw').read_text(encoding='utf-8').splitlines()
            assert len(lines)==(2 if transport else 1)
            marker=lines[0].split('\t')
            assert len(marker)==3 and marker[0]=='R0016_NEUTRAL' and marker[1].isdigit() and int(marker[1])>0 and marker[2]==nonce
            record['bashPid']=int(marker[1])
            assert ready.read_text()==marker[1]+'\t'+nonce+'\n' if readiness else not ready.exists()
            if transport:
                probe=json.loads(lines[1]);record['controlledProbe']=probe
                assert probe['outsideDenied'] is True and probe['insideWriteAllowed'] is True
                assert [row['kind'] for row in probe['transports']]==['unix','tcp','udp']
                assert all(row['denied'] is True and row['errno']==1 for row in probe['transports'])
                record['controlledTransportProof']=validate_controlled_transport(record,control)
            else:
                assert record['subjectSnapshotUnchanged']
            assert not (case/'stderr.raw').read_bytes()
            assert N.binding(Path('/usr/bin/python3'))==record['pythonBinding']
            assert record['captures']=={kind:N.binding(case/(kind+'.raw')) for kind in ('stdout','stderr')}
            assert not record.get('cleanup',{}).get('signals') and not record.get('cleanup',{}).get('errors')
            record['semanticCaptureComplete']=True
        except Exception as error:
            record['semanticCaptureComplete']=False
            record['semanticCaptureError']=type(error).__name__+': '+str(error)
        record['acquisitionComplete']=bool(record.get('returncode')==0 and 'error' not in record and record.get('cleanup',{}).get('complete') and record['outsideSnapshotUnchanged'] and record['semanticCaptureComplete'])
        record['classification']='SOURCE_FREE_OBSERVATION_ACQUIRED' if record['acquisitionComplete'] else 'SOURCE_FREE_ACQUISITION_FAILED'
        N.save(case / 'result.json',record)
    return record


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--preparation',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    repo=args.repo.resolve(strict=True); output=args.output.absolute()
    assert platform.system()=='Linux' and os.getuid()==os.geteuid()!=0
    output.mkdir(mode=0o700,exist_ok=False)
    N=load_support(repo/'tools/qualification/installer_preview_linux_namespace_successor.py')
    report={'schema':'r0016-linux-bash-startup.v1','productRowsExecuted':0,'scope':'Source-free startup/control observations only; all transport denials preserved','cases':[]}
    try:
        report['subreaper']=N.enable_subreaper()
        report['commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
        report['host']={'platform':platform.platform(),'uid':os.getuid(),'gid':os.getgid(),'controller':N.proc_identity(os.getpid()),'osRelease':N.fact('/etc/os-release')}
        prep=json.loads((args.preparation/'result.json').read_text())
        assert prep['complete'] is True and prep['osRelease']['VERSION_CODENAME']=='jammy'
        helper=repo/'tools/qualification/installer_preview_linux22_prerequisites.py'
        assert digest(helper.read_bytes())==PREPARATION_SHA
        report['preparation']=N.binding(args.preparation/'result.json')
        report['sourceBindings']={str(p.relative_to(repo)):N.binding(p) for p in (Path(__file__).resolve(),helper,repo/'tests/install-preview.py',repo/'tools/qualification/installer_preview_linux_namespace_successor.py')}
        report['executables']={name:N.binding(Path('/usr/bin')/name) for name in ('bash','bwrap','unshare','python3')}
        report['namespaceRootPasswd']=[line for line in Path('/etc/passwd').read_text().splitlines() if line.split(':')[2:3]==['0']]
        assert len(report['namespaceRootPasswd'])==1 and report['namespaceRootPasswd'][0].startswith('root:')
        frozen=output/'frozen';frozen.mkdir(mode=0o700)
        original=repo/'tests/install-preview.py';(frozen/'original-harness.py').write_bytes(original.read_bytes())
        observer=frozen/'diagnostic-observer.py';observer.write_bytes(derive_observer(original.read_bytes()))
        control=frozen/'transport-control.py';control.write_text(CONTROL,encoding='ascii')
        report['derivedObserver']=N.binding(observer);report['control']=N.binding(control)
        fixture=output/'fixture';fixture.mkdir(mode=0o700)
        outside=output/'outside';outside.mkdir(mode=0o700);(outside/'sentinel').write_bytes(b'original negative sentinel\n')
        for label,explicit,readiness,transport in [('default-no-ready',False,False,False),('default-ready',False,True,False),('explicit-ready',True,True,False),('explicit-transport',True,True,True)]:
            report['cases'].append(run_case(N,label,output,fixture,outside,observer,control,explicit,readiness,transport))
        for value in list(report['sourceBindings'].values())+[report['derivedObserver'],report['control']]:
            assert N.binding(Path(value['path']))==value
        report['sourceBindingsUnchanged']=True
        report['complete']=all(row['acquisitionComplete'] for row in report['cases'])
        report['inferenceLimit']='Raw syscall arguments and process/readiness facts do not automatically classify a call as host or installer; no event is excluded.'
    except Exception as error:
        report['complete']=False;report['error']=type(error).__name__+': '+str(error)
    N.save(output/'result.json',report)
    return 0 if report['complete'] else 2


if __name__=='__main__':
    raise SystemExit(main())
