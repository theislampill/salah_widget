#!/usr/bin/env python3
"""Prospective native acquisition of the unchanged eight PowerShell caller routes.

The existing helper owns suspended creation, Job assignment, resume, deadlines,
and direct-file capture. Its Job manages process lifetime, not network/filesystem
containment. Importing this module and using its validators never starts a host.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import sys
import tarfile

sys.dont_write_bytecode = True
SUPPORT_SHA = '9becda7102411dbef9a29efe5e5be95b9e02711563f3b845d496597011ff871b'
HELPER_SHA = '6776bc7b3d4e88d04f1dd811f5b7df0ea1553a7b8824f1f3e921c649c1aae9df'
PS7_SHA = 'bfb46af89433268872ddb43d1ca7a3f433452ee91ed356a9786940f90118e285'
ROOT_PREFIX = 'r16-routes-'
SECONDS = 240
JSON_LIMIT = 4 * 1024 * 1024
INPUTS = {
    'install.ps1': '07671cb9e6a0afb8eb9051a0a5f378d12e577877453a773860b3cf94d5e2951a',
    'tests/install-powershell-routes.ps1': '2f5aea77b909b0a1b735616a25e305f1df65e4f0565e0fea99e09e5a81e9f4fc',
    'tools/qualification/installer_preview_host_probe.py': HELPER_SHA,
    'tools/qualification/installer_preview_windows_carrier.py': SUPPORT_SHA,
}
ROUTES = (
    ('explicit-store', 'store', None, 'store'),
    ('ask-store', 'ask', '2', 'store'),
    ('ask-github', 'ask', '1', 'github'),
    ('ask-default-github', 'ask', '', 'github'),
)
CASES = tuple('route ' + family + ' ' + row[0]
              for family in ('chromium', 'firefox') for row in ROUTES)


def require(value, message):
    if not value:
        raise ValueError(message)


def load_exact(path, digest, name):
    require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest,
            'Pinned Python instrument differs')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command_for(executable, test, source):
    quote = lambda value: "'" + str(value).replace("'", "''") + "'"
    # Capture adapter only: the maintained fixture is invoked byte-for-byte.
    # UTF-8 preserves its deliberate Arabic path on Windows PowerShell 5.1.
    code = ('[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false); & '
            + quote(test) + ' -SourceFile ' + quote(source) + ' -RoutesOnly')
    return [str(executable), '-NoProfile', '-NonInteractive', '-Command', code]


def terminal_receipt(raw):
    require(len(raw) <= JSON_LIMIT, 'Route capture exceeds the bounded reader size')
    text = raw.decode('utf-8-sig')
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, 'Duplicate JSON key')
            value[key] = item
        return value
    def constant(value):
        raise ValueError('Non-finite JSON constant: ' + value)
    decoder = json.JSONDecoder(object_pairs_hook=pairs, parse_constant=constant)
    candidates = []
    for match in re.finditer(r'(?m)^\{', text):
        try:
            value, end = decoder.raw_decode(text, match.start())
        except ValueError:
            continue
        if isinstance(value, dict) and value.get('schema') == 'r0016-install-route-caller.v1':
            candidates.append((value, end))
    require(len(candidates) == 1 and not text[candidates[0][1]:].strip(),
            'Exactly one terminal route receipt is required')
    return candidates[0][0]


def validate_lifecycle(process, command):
    require(isinstance(process, dict) and process.get('command') == command,
            'Exact launch command differs')
    require(type(process.get('exit')) is int and process['exit'] == 0,
            'Native route process did not return integer exit zero')
    for field in ('exitObserved', 'jobAssignedBeforeResume', 'jobClosedKillOnClose'):
        require(process.get(field) is True, 'Missing native lifetime observation: ' + field)
    require(process.get('timedOut') is False and process.get('error', 'missing') is None,
            'Native route timeout or process error')
    elapsed = process.get('elapsedSeconds')
    require(type(process.get('timeoutSeconds')) is int and process['timeoutSeconds'] == SECONDS
            and type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed <= SECONDS,
            'Native route deadline observation differs')
    require(type(process.get('processId')) is int and process['processId'] > 0,
            'Native process identity missing')
    require(process.get('capture') == 'direct files; no redirected pipe drain'
            and process.get('drain') == 'not applicable', 'Capture protocol differs')


def validate_receipt(value, host, source_sha, test_sha, fixture_path):
    require(isinstance(value, dict) and value.get('schema') == 'r0016-install-route-caller.v1',
            'Wrong fixture receipt schema')
    version = value.get('host')
    require(host in ('ps51', 'ps766') and isinstance(version, str)
            and (bool(re.fullmatch(r'5\.1\.\d+\.\d+', version)) if host == 'ps51' else version == '7.6.6'),
            'Wrong native PowerShell version')
    require(value.get('nativeWindows') is True and value.get('routesOnly') is True,
            'Native Windows RoutesOnly observation required')
    require(type(value.get('fileErrors')) is int and value['fileErrors'] == 0,
            'Exact-file native parser failed')
    require(value.get('source') == value.get('sourceBefore') == source_sha
            and value.get('sourceUnchanged') is True and value.get('testSha256') == test_sha,
            'Source or maintained-fixture custody differs')
    rows, observations = value.get('results'), value.get('routeObservations')
    for label, entries in (('results', rows), ('observations', observations)):
        require(isinstance(entries, list) and len(entries) == len(CASES)
                and all(isinstance(row, dict) for row in entries)
                and tuple(row.get('case') for row in entries) == CASES,
                'Missing, duplicate or unexpected route ' + label)
    require(all(row.get('pass') is True and 'error' not in row for row in rows),
            'A maintained route assertion failed')
    for index, (family, route) in enumerate((family, route)
            for family in ('chromium', 'firefox') for route in ROUTES):
        name, requested, choice, resolved = route
        row = observations[index]
        require((row.get('family'), row.get('requestedSource'), row.get('choice'), row.get('expectedRoute'))
                == (family, requested, choice, resolved), 'Route premise or choice differs')
        require(row.get('eligibility') == 'eligible-known'
                and type(row.get('remainingAnswers')) is int and row['remainingAnswers'] == 0,
                'Eligibility or required prompt consumption differs')
        events = ['prompt:Choose [1/2] (default 1)'] if requested == 'ask' else []
        downloads, admissions = [], []
        if resolved == 'store':
            events += ['open:https://store.invalid']
            release_calls = 0
        else:
            asset = 'tabliss-chromium.zip' if family == 'chromium' else 'tabliss-firefox-signed.xpi'
            downloads = [{'name': asset, 'browser_download_url': 'https://example.invalid/' + asset}]
            events += ['download:' + asset]
            admissions = [{'Path': fixture_path, 'Kind': 'asset',
                           'State': 'published' if family == 'chromium' else 'handed-off'}]
            if family == 'chromium':
                copy_path = fixture_path + ' unpacked'
                events += ['extract', 'copy:' + copy_path,
                           'warning:Keep this unpacked folder while the browser uses it. This wizard never deletes an earlier manual bundle.']
                admissions += [{'Path': copy_path, 'Kind': 'unpacked', 'State': 'handed-off'}]
            else:
                events += ['copy:' + fixture_path]
            events += ['open:fixture://manager']
            release_calls = 1
        events += ['prompt:Press Enter after TablissNG is installed']
        require(type(row.get('releaseCalls')) is int and row['releaseCalls'] == release_calls
                and row.get('downloadedAssets') == downloads and row.get('admissionCalls') == admissions
                and row.get('events') == events,
                'Actual route effects, selected asset, admission or handoff sequence differs: ' + name)


def archive_owned_root(support, parent, archive):
    roots = list(parent.glob(ROOT_PREFIX + '*'))
    require(len(roots) == 1 and re.fullmatch(ROOT_PREFIX + r'[0-9a-f]{16}', roots[0].name),
            'Exactly one owned route root required')
    root = support.checked_path(roots[0], parent, directory=True)
    require(archive.is_absolute() and archive.parent == parent and not archive.exists(),
            'Invalid or occupied evidence archive destination')
    with tarfile.open(archive, 'x:gz', dereference=False) as output:
        pending = [root]
        while pending:
            path = pending.pop()
            info = path.lstat()
            name = 'installer-evidence' + ('' if path == root else '/' + path.relative_to(root).as_posix())
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                member = tarfile.TarInfo(name)
                member.type, member.linkname = tarfile.SYMTYPE, os.readlink(path)
                member.mode, member.mtime = stat.S_IMODE(info.st_mode), int(info.st_mtime)
                output.addfile(member)
            else:
                require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), 'Special evidence member')
                output.add(path, arcname=name, recursive=False)
                if stat.S_ISDIR(info.st_mode):
                    pending.extend(sorted(path.iterdir(), reverse=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=('ps51', 'ps766'))
    parser.add_argument('--powershell', type=Path)
    parser.add_argument('--source-commit')
    parser.add_argument('--output-parent', type=Path, required=True)
    parser.add_argument('--archive-only', action='store_true')
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args(argv)
    if os.name != 'nt':
        parser.error('Native Windows required; no host or installer was started')
    repo = Path(__file__).resolve().parents[2]
    support = load_exact(repo / 'tools/qualification/installer_preview_windows_carrier.py',
                         SUPPORT_SHA, 'r16_routes_support')
    parent = support.checked_path(args.output_parent, directory=True)
    require(parent == support.checked_path(os.environ['USERPROFILE'], directory=True)
            and parent.drive.lower() == 'c:', 'Actual system-volume runner profile parent required')
    if args.archive_only:
        require(args.archive is not None and args.host is None and args.powershell is None
                and args.source_commit is None, 'Invalid archive-only arguments')
        archive_owned_root(support, parent, args.archive)
        return 0
    require(args.host is not None and args.powershell is not None and args.archive is None
            and isinstance(args.source_commit, str) and re.fullmatch(r'[0-9a-f]{40}', args.source_commit),
            'Exact source association and host required')
    executable = support.checked_path(args.powershell)
    host_fact = support.file_fact(executable)
    if args.host == 'ps766':
        require(host_fact['bytes'] == 301368 and host_fact['sha256'] == PS7_SHA,
                'Exact portable PowerShell 7.6.6 executable differs')
    else:
        expected = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
        require(executable == expected.resolve(strict=True), 'Wrong Windows PowerShell executable')
    root = parent / (ROOT_PREFIX + secrets.token_hex(8))
    root.mkdir()
    result = dict(schema='r0016-windows-eight-caller-routes.v1', status='ACQUISITION_INCOMPLETE',
                  sourceCommit=args.source_commit, host=args.host, fixture=str(root), rowsAcquired=0,
                  sourceAndInputsUnchanged=False, fallbackRowsExecuted=0,
                  scope='Actual-function store/ask route semantics only. Original18 selector/fallback, preview mutants, archive admission and whole-entry evidence remain separate.')
    support.save(root / 'route-result.json', result)
    fixed, copied = [], {}
    status = 2
    try:
        control = root / 'control'
        control.mkdir()
        roles = dict(INPUTS)
        roles['tools/qualification/installer_preview_windows_routes.py'] = support.file_fact(Path(__file__).resolve())['sha256']
        for role, digest in roles.items():
            original = support.file_fact(repo / role)
            require(original['sha256'] == digest, 'Pinned input differs: ' + role)
            target = control / role
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original['path'], target)
            copied[role] = support.file_fact(target, root)
            require((copied[role]['bytes'], copied[role]['sha256']) == (original['bytes'], original['sha256']),
                    'Retained launch input differs')
            fixed.extend([original, copied[role]])
        fixed.extend([host_fact, support.file_fact(Path(sys.executable).resolve())])
        helper = load_exact(copied['tools/qualification/installer_preview_host_probe.py']['path'],
                            HELPER_SHA, 'r16_routes_host_helper')
        state, capture = root / 'state', root / 'run'
        capture.mkdir()
        environment = helper.environment_for(state, executable, os.environ, False)
        environment['POWERSHELL_UPDATECHECK'] = 'Off'
        helper.prepare_environment(environment)
        command = command_for(executable, copied['tests/install-powershell-routes.ps1']['path'], copied['install.ps1']['path'])
        support.save(root / 'plan.json', dict(sourceCommit=args.source_commit, host=host_fact, inputs=copied,
                     originalsAndCopies=fixed, command=command, environment=environment, timeoutSeconds=SECONDS,
                     noGatherOverride=False, fixtureUnchanged=True,
                     captureAdapter='Only Console.OutputEncoding=UTF8 before invoking the unchanged fixture'))
        for fact in fixed:
            support.verify_fact(fact, Path(fact['path']))
        helper.save_required_snapshot(state, capture / 'state.before.json')
        process = helper.run_observer(command, environment, capture, SECONDS)
        result['process'] = process
        support.save(root / 'route-result.json', result)
        helper.save_required_snapshot(state, capture / 'state.after.json')
        validate_lifecycle(process, command)
        for kind in ('stdout', 'stderr'):
            support.verify_fact(process.get(kind), capture / ('observer.' + kind + '.raw'), root)
        require((capture / 'observer.stderr.raw').read_bytes() == b'', 'Native route stderr is nonempty')
        receipt = terminal_receipt((capture / 'observer.stdout.raw').read_bytes())
        fixture_path = str(Path(environment['TEMP']) / 'fixture path \u0645 asset.zip')
        validate_receipt(receipt, args.host, INPUTS['install.ps1'], INPUTS['tests/install-powershell-routes.ps1'], fixture_path)
        support.save(root / 'routes.receipt.json', receipt)
        result.update(status='ACQUIRED_EIGHT_CALLER_ROUTE_ROWS', rowsAcquired=8,
                      nativeVersion=receipt['host'], receipt=support.file_fact(root / 'routes.receipt.json', root))
        status = 0
    except Exception as error:
        result.update(status='ACQUISITION_OR_ROUTE_ASSERTION_NOT_ADMITTED', error=type(error).__name__ + ': ' + str(error))
    finally:
        try:
            require(len(fixed) == 2 * (len(INPUTS) + 1) + 2, 'Complete launch custody was not established')
            for fact in fixed:
                support.verify_fact(fact, Path(fact['path']))
            result['sourceAndInputsUnchanged'] = True
        except Exception as error:
            result.update(status='INPUT_CUSTODY_FAILED', sourceAndInputsUnchanged=False,
                          custodyError=type(error).__name__ + ': ' + str(error))
            status = 2
        support.save(root / 'route-result.json', result)
    print(json.dumps(result, indent=2))
    return status


if __name__ == '__main__':
    raise SystemExit(main())
