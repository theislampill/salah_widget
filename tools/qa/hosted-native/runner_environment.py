#!/usr/bin/env python3
"""Bind an exact source-selected runner across the dispatcher and observation jobs.

This module inspects source and host metadata only. It does not launch a browser,
change kernel policy, install a package, or assert native observation success.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys

import r002f_bfcache_tools as tools

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROTOCOL = 'salah-native-runner-dispatch/1'
ADMISSION = 'salah-native-runner-admission/1'
REPOSITORY = 'theislampill/salah_widget'
REF = 'refs/heads/chatgpt/hosted-native-research-20261125'
WORKFLOW = REPOSITORY + '/.github/workflows/research-native-pilot.yml@' + REF
ENVIRONMENT_FILE = 'runner-environment.json'
LIMIT = 512 * 1024
need = tools.need


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def selection(path=None):
    from observe import read_campaign
    from r002f_bfcache_central import campaign_selected
    path = HERE / 'campaign.json' if path is None else Path(path)
    identity = tools.file_record(path)
    value = read_campaign(path)
    bfcache = campaign_selected(value)
    tools.require_record(identity)
    return {'runner': 'ubuntu-24.04' if bfcache else 'ubuntu-22.04',
            'version': '24.04' if bfcache else '22.04', 'suite': 'noble' if bfcache else 'jammy',
            'imageOS': 'ubuntu24' if bfcache else 'ubuntu22',
            'scope': 'R002F_BFCACHE_UBUNTU24_DIAGNOSTIC' if bfcache else 'ORIGINAL_UBUNTU22_ENVIRONMENT',
            'historicalUbuntu22Comparability': False if bfcache else None,
            'campaign': {key: identity[key] for key in ('sha256', 'bytes', 'mode')}}


def source_files(campaign=None):
    """Common closure plus data actually read by the selected dispatcher.

    Original leaf preparation/currentness remains separate authority. In
    particular this does not replace the R003F central manifest or native bodies.
    """
    from r002f_bfcache_central import source_files as shared_source_files
    value = tools.load(HERE / 'campaign.json') if campaign is None else campaign
    names = shared_source_files()
    if value.get('r003fHarness') == 'corrected-matrix':
        names += ['tools/qa/hosted-native/r003f-matrix-catalogue.json']
    return sorted(set(names))


def producer_source_files(campaign):
    return [os.path.relpath(ROOT / name, HERE) for name in source_files(campaign)]


def source_snapshot(root=None, names=None):
    """Check actual materialized bytes/modes against HEAD, including skip-worktree files."""
    root = ROOT if root is None else Path(root).absolute()
    records = None
    if names is None:
        from r002f_bfcache_central import source_identity
        identity = source_identity()
        need(root == ROOT and identity['root'] == str(ROOT), 'source root differs')
        names = source_files()
        records = {**identity['files'], **{name: tools.file_record(root / name) for name in names if name not in identity['files']}}
    else:
        need(type(names) in (list, tuple) and names and len(set(names)) == len(names), 'source population differs')
    need(all(type(name) is str and not Path(name).is_absolute() and '..' not in Path(name).parts for name in names),
         'source path must remain inside the exact repository')
    if records is None:
        records = {name: tools.file_record(root / name) for name in names}
    def git(*args):
        return subprocess.run(['/usr/bin/git', '-c', 'protocol.allow=never', '-C', str(root), *args],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, timeout=10).stdout
    need(not git('status', '--porcelain'), 'dispatcher source is not clean')
    commit = git('rev-parse', 'HEAD').decode().strip()
    tree = git('rev-parse', 'HEAD^{tree}').decode().strip()
    tracked = {}
    for entry in git('ls-tree', '-rz', '--full-tree', 'HEAD', '--', *names).split(b'\0'):
        if not entry: continue
        meta, name = entry.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        need(kind == 'blob' and mode in ('100644', '100755'), 'non-regular source tree entry')
        tracked[name.decode()] = (mode, oid)
    need(set(tracked) == set(names), 'complete dispatch source population is not tracked')
    files = {}
    for name in sorted(names):
        record = records[name]
        raw = (root / name).read_bytes()
        tools.require_record(record)
        mode, oid = tracked[name]
        actual_blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        need(actual_blob == oid and record['mode'] == (0o755 if mode == '100755' else 0o644)
             and hashlib.sha256(raw).hexdigest() == record['sha256'], 'source bytes/mode differ from exact HEAD: ' + name)
        files[name] = {'mode': mode, 'gitBlob': oid, 'bytes': len(raw), 'sha256': record['sha256']}
    need(not git('status', '--porcelain') and git('rev-parse', 'HEAD').decode().strip() == commit,
         'source changed during dispatch inspection')
    return {'commit': commit, 'tree': tree, 'files': files}


def workflow_context(job, environment=None):
    env = os.environ if environment is None else environment
    need(job in ('select_runner', 'observe') and env.get('GITHUB_JOB') == job, 'actual workflow job differs')
    values = {key: env.get(key) for key in ('GITHUB_REPOSITORY', 'GITHUB_REF', 'GITHUB_SHA',
        'GITHUB_WORKFLOW_REF', 'GITHUB_WORKFLOW_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT', 'GITHUB_EVENT_NAME')}
    need(values['GITHUB_REPOSITORY'] == REPOSITORY and values['GITHUB_REF'] == REF
         and values['GITHUB_WORKFLOW_REF'] == WORKFLOW, 'unadmitted repository/ref/workflow')
    need(re.fullmatch(r'[0-9a-f]{40}', values['GITHUB_SHA'] or '')
         and values['GITHUB_WORKFLOW_SHA'] == values['GITHUB_SHA'], 'workflow/source commit differs')
    need(all(re.fullmatch(r'[1-9][0-9]*', values[key] or '') for key in ('GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT'))
         and values['GITHUB_EVENT_NAME'] in ('push', 'workflow_dispatch'), 'actual workflow run identity differs')
    need(env.get('GITHUB_ACTIONS') == 'true' and env.get('RUNNER_ENVIRONMENT') == 'github-hosted'
         and env.get('RUNNER_OS') == 'Linux' and env.get('RUNNER_ARCH') == 'X64', 'official Linux X64 hosted runner required')
    runner = env.get('RUNNER_NAME', '')
    need(type(runner) is str and 0 < len(runner) <= 256 and not any(c in runner for c in '\r\n\0'), 'runner identity absent')
    return {'workflow': values, 'job': {'id': job, 'runnerName': runner, 'environment': 'github-hosted',
                                      'os': 'Linux', 'architecture': 'X64'}}


def host_snapshot(environment=None):
    env = os.environ if environment is None else environment
    release = tools.file_record('/etc/os-release', system=True, limit=65536)
    fields = {}
    for line in Path(release['path']).read_text().splitlines():
        if not line or line.startswith('#'): continue
        key, separator, text = line.partition('=')
        need(separator and re.fullmatch(r'[A-Z0-9_]+', key) and key not in fields, 'OS release field differs')
        parsed = shlex.split(text, comments=False, posix=True)
        need(len(parsed) == 1, 'OS release value differs')
        fields[key] = parsed[0]
    tools.require_record(release)
    policy = {}
    for name in ('/proc/sys/kernel/unprivileged_userns_clone', '/proc/sys/user/max_user_namespaces',
                 '/proc/sys/kernel/apparmor_restrict_unprivileged_userns', '/sys/module/apparmor/parameters/enabled',
                 '/proc/self/attr/current'):
        path = Path(name)
        if not path.exists(): policy[name] = {'present': False}; continue
        with path.open('rb') as stream: raw = stream.read(4097)
        need(len(raw) <= 4096, 'kernel policy metadata exceeded bound')
        policy[name] = {'present': True, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                        'text': raw.decode()}
    uname = os.uname()
    return {'releaseRecord': release, 'release': fields,
            'kernel': {key: getattr(uname, key) for key in ('sysname', 'release', 'version', 'machine')},
            'imageOS': env.get('ImageOS'), 'imageVersion': env.get('ImageVersion'), 'kernelPolicy': policy}


def admit_host(host, version):
    need(type(host) is dict and host.get('release', {}).get('ID') == 'ubuntu'
         and host['release'].get('VERSION_ID') == version
         and host['release'].get('VERSION_CODENAME') == ('noble' if version == '24.04' else 'jammy')
         and host.get('imageOS') == ('ubuntu24' if version == '24.04' else 'ubuntu22'), 'actual Ubuntu runner differs')
    need(host.get('kernel', {}).get('sysname') == 'Linux' and host['kernel'].get('machine') == 'x86_64'
         and type(host.get('imageVersion')) is str and 0 < len(host['imageVersion']) <= 128,
         'actual kernel/image identity differs')
    return host


def dispatch():
    selected = selection(); sources = source_snapshot(); context = workflow_context('select_runner')
    need(context['workflow']['GITHUB_SHA'] == sources['commit'], 'dispatcher checkout does not match workflow head')
    host = admit_host(host_snapshot(), '22.04')
    return {'protocol': PROTOCOL, 'sourceOnly': True, 'nativeObservation': False,
            'selection': selected, 'sources': sources, 'context': context, 'host': host}


def encode_dispatch(value):
    raw = canonical(value); need(len(raw) <= LIMIT, 'dispatcher payload exceeded bound')
    return base64.b64encode(raw).decode(), hashlib.sha256(raw).hexdigest()


def decode_dispatch(encoded, digest):
    need(type(encoded) is str and 0 < len(encoded) <= (LIMIT + 2) // 3 * 4
         and type(digest) is str and re.fullmatch(r'[0-9a-f]{64}', digest), 'dispatcher output absent or malformed')
    try:
        raw = base64.b64decode(encoded, validate=True)
        value = json.loads(raw)
    except (ValueError, UnicodeError) as error: raise ValueError('dispatcher encoding differs') from error
    need(len(raw) <= LIMIT and hashlib.sha256(raw).hexdigest() == digest and canonical(value) == raw,
         'dispatcher digest or canonical population differs')
    return value


def validate_dispatch(value, selected, sources, context, host):
    need(type(value) is dict and set(value) == {'protocol', 'sourceOnly', 'nativeObservation', 'selection', 'sources', 'context', 'host'}
         and value.get('protocol') == PROTOCOL and value.get('sourceOnly') is True and value.get('nativeObservation') is False,
         'dispatcher protocol/scope differs')
    need(value['selection'] == selected and value['sources'] == sources, 'dispatcher campaign/source no longer current')
    original = value['context']
    need(original.get('workflow') == context['workflow'] and context['workflow']['GITHUB_SHA'] == sources['commit'],
         'dispatcher workflow/head/run/attempt differs')
    for item, expected in ((original, 'select_runner'), (context, 'observe')):
        job = item.get('job', {})
        need(job.get('id') == expected and job.get('environment') == 'github-hosted'
             and job.get('os') == 'Linux' and job.get('architecture') == 'X64'
             and type(job.get('runnerName')) is str and job['runnerName'], 'dispatcher/worker job identity differs')
        rebuilt = workflow_context(expected, {**item['workflow'], 'GITHUB_JOB': expected, 'GITHUB_ACTIONS': 'true',
            'RUNNER_ENVIRONMENT': job['environment'], 'RUNNER_OS': job['os'], 'RUNNER_ARCH': job['architecture'],
            'RUNNER_NAME': job['runnerName']})
        need(rebuilt == item, 'saved workflow context has an unadmitted population')
    admit_host(value['host'], '22.04'); admit_host(host, selected['version'])
    return True


def task_paths(task):
    task = Path(task).absolute()
    need(task.resolve() == task and '..' not in task.parts and not any(p.is_symlink() for p in (task, *task.parents)),
         'literal task root required')
    capture = task / 'capture'
    need(capture.is_dir() and not capture.is_symlink(), 'private capture root missing or redirected')
    return task, task / 'capture' / ENVIRONMENT_FILE


def workflow_files(task, context):
    workflow = context['workflow']
    expected = {'workflow-commit.txt': workflow['GITHUB_SHA'] + '\n',
                'workflow-run.txt': workflow['GITHUB_RUN_ID'] + '/' + workflow['GITHUB_RUN_ATTEMPT'] + '\n'}
    records = {}
    for name, text in expected.items():
        record = tools.file_record(task / 'capture' / name, limit=4096)
        need(Path(record['path']).read_text() == text, 'actual capture workflow identity differs')
        tools.require_record(record); records[name] = record
    return records


def admit_worker(task):
    task, path = task_paths(task)
    result = {'protocol': ADMISSION, 'status': 'INCOMPLETE', 'task': str(task), 'nativeObservation': False}
    try:
        value = decode_dispatch(os.environ.get('SALAH_RUNNER_DISPATCH'), os.environ.get('SALAH_RUNNER_DISPATCH_SHA256'))
        result.update(dispatch=value, dispatchSha256=hashlib.sha256(canonical(value)).hexdigest())
        selected = selection(); sources = source_snapshot(); context = workflow_context('observe'); host = host_snapshot()
        result.update(selection=selected, sources=sources, context=context, host=host)
        validate_dispatch(value, selected, sources, context, host)
        result['workflowFiles'] = workflow_files(task, context)
        result['status'] = 'COMPLETE'
    except Exception as error: result['error'] = type(error).__name__ + ': ' + str(error)
    tools.save(path, result)
    return result


def current(task):
    task, path = task_paths(task); value = tools.load(path)
    need(value.get('protocol') == ADMISSION and value.get('status') == 'COMPLETE'
         and value.get('task') == str(task) and value.get('nativeObservation') is False and not value.get('error'),
         'actual runner admission is incomplete')
    selected = selection(); sources = source_snapshot()
    # Namespace children deliberately have no inherited GitHub environment.
    # Their authority is the original capture identity plus this exact saved pair of jobs.
    context = value['context']; host = host_snapshot({'ImageOS': value['host']['imageOS'], 'ImageVersion': value['host']['imageVersion']})
    need(host == value['host'] and selected == value['selection'] and sources == value['sources'],
         'actual runner/source environment changed')
    need(hashlib.sha256(canonical(value['dispatch'])).hexdigest() == value['dispatchSha256'], 'saved dispatcher digest differs')
    validate_dispatch(value['dispatch'], selected, sources, context, host)
    need(workflow_files(task, context) == value['workflowFiles'], 'capture workflow files changed')
    tools.current_records({'host': host, 'workflowFiles': value['workflowFiles']})
    return {'receipt': tools.file_record(path), 'selection': selected, 'workflow': context['workflow'],
            'jobs': [value['dispatch']['context']['job'], context['job']]}


def append_outputs(path, values):
    data = ''.join(key + '=' + value + '\n' for key, value in values.items()).encode()
    fd = os.open(path, os.O_RDWR | os.O_APPEND | os.O_NOFOLLOW)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= LIMIT,
             'bounded regular workflow output file required')
        need(os.write(fd, data) == len(data), 'partial workflow output write')
        os.fsync(fd)
        need(os.fstat(fd).st_size == before.st_size + len(data)
             and os.pread(fd, len(data), before.st_size) == data, 'actual workflow output bytes differ')
    finally: os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('dispatch', 'admit')); parser.add_argument('--task')
    args = parser.parse_args()
    if args.phase == 'dispatch':
        need(args.task is None, 'dispatcher cannot operate on a private task')
        value = dispatch(); encoded, digest = encode_dispatch(value)
        append_outputs(os.environ['GITHUB_OUTPUT'], {'runner': value['selection']['runner'], 'payload': encoded, 'sha256': digest})
        print('EXACT_SOURCE_RUNNER_SELECTED'); return 0
    need(args.task is not None, 'worker task required')
    value = admit_worker(args.task)
    print(json.dumps({'protocol': ADMISSION, 'status': value['status']}))
    return 0 if value['status'] == 'COMPLETE' else 2


if __name__ == '__main__': sys.exit(main())
