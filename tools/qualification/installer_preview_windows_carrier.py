#!/usr/bin/env python3
"""NEW source-free Windows carrier route; no installer source is acquired.

The exact existing host helper owns suspended creation, Job assignment, resume,
and direct-file capture. Its Job Object manages process lifetime; it is not a
filesystem or network sandbox. Pure receipt validators remain importable without
loading Windows APIs or starting PowerShell.
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
import shutil
import stat
import sys
import tarfile
import tempfile
from datetime import datetime, timezone


HELPER_SHA256 = '6776bc7b3d4e88d04f1dd811f5b7df0ea1553a7b8824f1f3e921c649c1aae9df'
OUTER_SECONDS = 600
JSON_LIMIT = 64 * 1024 * 1024
ROOT_PREFIX = 'r0016-windows-carrier-'
PS_INPUTS = (
    'install-preview.ps1', 'install-preview-acquire-timed.ps1',
    'install-preview-window.ps1', 'install-preview-carrier-controls.ps1',
)
EXPECTED_CASES = frozenset((
    'control-outside-subject-method-write-False', 'control-outside-subject-method-write-True',
    'control-direct-loopback-transport-False', 'control-direct-loopback-transport-True',
    'carrier-control-fallthrough', 'carrier-control-exit-zero', 'carrier-control-exit-nonzero',
    'carrier-control-throw', 'carrier-control-finally-exit', 'carrier-control-parameter-failure',
))


class Rejected(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Rejected(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + '\n', encoding='utf-8')


def checked_path(value, owner=None, directory=False):
    path = Path(value)
    require(path.is_absolute(), 'An absolute evidence path is required')
    resolved = path.resolve(strict=True)
    require(str(path) == str(resolved), 'Evidence path is not its exact resolved path')
    if owner is not None:
        root = Path(owner).resolve(strict=True)
        require(path == root or path.is_relative_to(root), 'Evidence path escaped its owned root')
    for part in (path, *path.parents):
        info = part.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 0x400,
                'Evidence path has a symbolic-link or reparse ancestor')
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode), 'Unexpected evidence path type')
    return path


def file_fact(value, owner=None):
    path = checked_path(value, owner)
    before = path.stat()
    require(before.st_size <= JSON_LIMIT, 'Evidence file exceeds the bounded reader size')
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns), 'Evidence file changed while read')
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def verify_fact(record, expected_path, owner=None):
    require(isinstance(record, dict) and set(record) == {'path', 'bytes', 'sha256'}, 'Malformed exact file fact')
    require(isinstance(record['path'], str) and type(record['bytes']) is int and record['bytes'] >= 0 and
            isinstance(record['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', record['sha256']), 'Malformed file fact fields')
    require(record['path'] == str(expected_path), 'Evidence file fact names a different path')
    require(record == file_fact(expected_path, owner), 'Evidence file length or SHA256 differs')
    return record


def strict_json(path):
    def pairs(values):
        result = {}
        for key, value in values:
            require(key not in result, 'JSON contains a duplicate object key')
            result[key] = value
        return result

    def constant(value):
        raise Rejected('JSON contains a non-finite numeric constant: ' + value)

    raw = Path(path).read_bytes()
    require(len(raw) <= JSON_LIMIT, 'JSON exceeds the bounded reader size')
    try:
        value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise Rejected('Capture is not one complete UTF-8 JSON document') from error
    require(isinstance(value, dict), 'Expected a JSON object')
    return value


def finite_elapsed(value, ceiling):
    return type(value) in (int, float) and math.isfinite(value) and 0 <= value <= ceiling


def validate_terminal(process, command, root):
    require(isinstance(process, dict) and process.get('command') == command, 'Outer command does not match the exact launch')
    require(type(process.get('exit')) is int and process['exit'] == 0, 'Outer terminal is not integer exit zero')
    for field in ('exitObserved', 'jobAssignedBeforeResume', 'jobClosedKillOnClose'):
        require(process.get(field) is True, 'Outer process lacks ' + field)
    require(process.get('timedOut') is False and 'error' in process and process['error'] is None, 'Outer process timed out or failed')
    require(type(process.get('timeoutSeconds')) is int and process['timeoutSeconds'] == OUTER_SECONDS and
            finite_elapsed(process.get('elapsedSeconds'), OUTER_SECONDS), 'Outer deadline observation is invalid')
    require(type(process.get('processId')) is int and process['processId'] > 0, 'Outer process identity is invalid')
    require(process.get('capture') == 'direct files; no redirected pipe drain' and process.get('drain') == 'not applicable',
            'Outer capture does not match the exact helper protocol')
    return [verify_fact(process.get(kind), root / ('observer.' + kind + '.raw'), root) for kind in ('stdout', 'stderr')]


def validate_header(value, schema, expected_host, executable):
    require(value.get('schema') == schema and value.get('pass') is True and value.get('classification') == 'PASS', 'Carrier schema or disposition differs')
    require('error' in value and value['error'] is None and value.get('installerExecuted') is False, 'Carrier reports an error or installer execution')
    require(value.get('nativeWindows') is True and value.get('expectedHost') == expected_host and
            value.get('commandHost') == str(executable), 'Carrier host association differs')
    version = value.get('host')
    require(isinstance(version, str) and ((expected_host == 'ps51' and re.fullmatch(r'5\.1\.\d+\.\d+', version)) or
            (expected_host == 'ps7' and version == '7.6.6')), 'Carrier native host version differs')
    require(type(value.get('casesExpected')) is int and value['casesExpected'] == 10 and
            type(value.get('casesObserved')) is int and value['casesObserved'] == 10, 'Carrier case count differs')


def validate_inputs(values, launched_inputs, fixture, root):
    require(isinstance(values, list) and len(values) == 4 and set(launched_inputs) == set(PS_INPUTS), 'Carrier needs exactly four input roles')
    names = [item.get('name') if isinstance(item, dict) else None for item in values]
    require(all(isinstance(name, str) for name in names) and len(set(names)) == 4 and set(names) == set(PS_INPUTS),
            'Carrier input role is duplicated or missing')
    facts = []
    for item in values:
        require(set(item) == {'name', 'original', 'retained'}, 'Carrier input role shape differs')
        expected = launched_inputs[item['name']]
        require(item['original'] == expected, 'Carrier original input differs from the exact launched copy')
        facts.append(verify_fact(item['original'], Path(expected['path']), root))
        retained = verify_fact(item['retained'], fixture / 'inputs' / item['name'], fixture)
        require(retained['bytes'] == expected['bytes'] and retained['sha256'] == expected['sha256'], 'Retained input bytes differ from launch')
        facts.append(retained)
    return facts


def validate_controls(report, fixture, executable):
    rows = report.get('results')
    require(isinstance(rows, list) and len(rows) == 10, 'Carrier does not contain ten result rows')
    names = [row.get('case') if isinstance(row, dict) else None for row in rows]
    require(all(isinstance(name, str) for name in names) and len(set(names)) == 10 and set(names) == EXPECTED_CASES,
            'Carrier control row is duplicated, missing, or unexpected')
    driver = fixture / 'actual-embedded-driver.ps1'
    extraction = report.get('extraction')
    require(isinstance(extraction, dict), 'Carrier extraction custody is missing')
    facts = [verify_fact(extraction.get('embeddedDriver'), driver, fixture)]
    expected_arguments = '-NoProfile -File "' + str(driver).replace('"', '\\"') + '"'
    case_roots, nonces = set(), set()
    for row in rows:
        require(row.get('pass') is True and row.get('classification') == 'PASS' and row.get('commandHost') == str(executable),
                'Carrier control failed or used a different host')
        process = row.get('process')
        require(isinstance(process, dict), 'Carrier control process is missing')
        case_root = checked_path(process.get('fixture', ''), fixture, directory=True)
        require(case_root.parent == fixture and case_root not in case_roots, 'Carrier control reused another case fixture')
        case_roots.add(case_root)
        label = 'carrier-control' if row['case'].startswith('carrier-control-') else 'guard-control'
        launch_path = case_root / (label + '.launch.json')
        facts.append(verify_fact(row.get('rawLaunch'), launch_path, fixture))
        launch = strict_json(launch_path)
        require(launch.get('host') == str(executable) and launch.get('nativeFile') == str(driver) == process.get('nativeFile'),
                'Carrier raw control launch host or driver differs')
        require(launch.get('arguments') == expected_arguments,
                'Carrier raw control arguments differ from the exact retained driver command')
        require(type(process.get('processId')) is int and process['processId'] > 0 and
                type(launch.get('processId')) is int and launch['processId'] == process['processId'], 'Carrier raw launch PID differs')
        nonce = launch.get('nonce')
        require(isinstance(nonce, str) and re.fullmatch(r'[0-9a-f]{32}', nonce) and nonce not in nonces, 'Carrier control nonce is invalid or replayed')
        nonces.add(nonce)
        require(type(process.get('budgetSeconds')) is int and process['budgetSeconds'] == 60 and
                type(launch.get('budgetSeconds')) is int and launch['budgetSeconds'] == 60, 'Carrier child budget differs')
        require(process.get('preparation') == 'COMPLETED' and process.get('timedOut') is False and process.get('killGraceExpired') is False and
                process.get('stdoutDrainCompleted') is True and process.get('stderrDrainCompleted') is True, 'Carrier control capture is incomplete')
        elapsed = process.get('terminalObservedElapsedMs' if label == 'carrier-control' else 'processExitObservedElapsedMs')
        require(finite_elapsed(elapsed, 60000) and elapsed < 60000, 'Carrier child terminal was late or missing')
        require(type(process.get('exit')) is int, 'Carrier child lacks an integer terminal status')
        if label == 'carrier-control' or row['case'].endswith('-False'):
            require(process['exit'] == 0, 'Normally completed carrier control exited abnormally')
    return facts


def validate_acquisition(process, command, root, outputs, executable, expected_host, launched_inputs):
    """Read-only association validation; this function never launches a process."""
    root = checked_path(root, directory=True)
    outputs = checked_path(outputs, root, directory=True)
    executable = checked_path(executable)
    require(expected_host in ('ps51', 'ps7') and command[0] == str(executable), 'Expected host or executable differs from launch')
    facts = validate_terminal(process, command, root)
    envelope = strict_json(root / 'observer.stdout.raw')
    validate_header(envelope, 'r0016-source-free-native-carrier-result.v1', expected_host, executable)
    report_fact = envelope.get('report')
    require(isinstance(report_fact, dict) and isinstance(report_fact.get('path'), str), 'Carrier envelope lacks its full report fact')
    report_path = checked_path(report_fact['path'], outputs)
    fixture = report_path.parent
    require(report_path.name == 'carrier-report.json' and fixture.parent == outputs and
            re.fullmatch(r'r0016-source-free-carrier-[0-9a-f]{32}', fixture.name), 'Carrier full report is not the owned fixture child report')
    require(list(outputs.iterdir()) == [fixture], 'Carrier output parent contains a second or replayed fixture')
    facts.append(verify_fact(report_fact, report_path, outputs))
    report = strict_json(report_path)
    validate_header(report, 'r0016-source-free-native-carrier.v1', expected_host, executable)
    require(report.get('fixture') == str(fixture) and report.get('host') == envelope['host'], 'Carrier report fixture or version association differs')
    require(report.get('inputs') == envelope.get('inputs'), 'Carrier envelope and full report input associations differ')
    facts.extend(validate_inputs(report.get('inputs'), launched_inputs, fixture, root))
    facts.extend(validate_controls(report, fixture, executable))
    for fact in facts:
        verify_fact(fact, Path(fact['path']), root)
    return dict(report=report_fact, fixture=str(fixture), host=report['host'], expectedHost=expected_host,
                commandHost=str(executable), controls=sorted(EXPECTED_CASES), custodyFiles=facts,
                scope='Complete carrier association and ten source-free control receipts; no installer qualification.')


def load_helper(path):
    require(file_fact(path)['sha256'] == HELPER_SHA256, 'Published host helper digest differs')
    spec = importlib.util.spec_from_file_location('r0016_exact_host_helper', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def archive_owned_root(parent, archive_path):
    """Archive every owned entry without recursing through links or junctions."""
    parent = checked_path(parent, directory=True)
    roots = list(parent.glob(ROOT_PREFIX + '*'))
    require(len(roots) == 1, 'Exactly one owned carrier root is required for archival')
    root = checked_path(roots[0], parent, directory=True)
    archive_path = Path(archive_path)
    require(archive_path.is_absolute() and archive_path.parent == parent and not archive_path.exists(), 'Archive destination is occupied or outside its parent')
    with tarfile.open(archive_path, 'w:gz', dereference=False) as archive:
        pending = [root]
        while pending:
            path = pending.pop()
            info = path.lstat()
            name = 'installer-evidence' if path == root else 'installer-evidence/' + path.relative_to(root).as_posix()
            link = stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)
            if link:
                entry = tarfile.TarInfo(name)
                entry.type, entry.linkname = tarfile.SYMTYPE, os.readlink(path)
                entry.mode, entry.mtime = stat.S_IMODE(info.st_mode), int(info.st_mtime)
                archive.addfile(entry)
            else:
                require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), 'Owned fixture contains an unsupported special entry')
                archive.add(path, arcname=name, recursive=False)
                if stat.S_ISDIR(info.st_mode):
                    pending.extend(sorted(path.iterdir(), reverse=True))
    return str(archive_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=('ps51', 'ps766'))
    parser.add_argument('--powershell', type=Path)
    parser.add_argument('--output-parent', type=Path, required=True)
    parser.add_argument('--archive-only', action='store_true')
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args()
    if os.name != 'nt':
        parser.error('Native Windows required; no PowerShell process was started')
    if args.archive_only:
        require(args.archive is not None and args.host is None and args.powershell is None, 'Archive mode requires only parent and archive paths')
        print(archive_owned_root(args.output_parent, args.archive))
        return 0
    require(args.host is not None and args.powershell is not None and args.archive is None, 'Native acquisition requires an exact host executable')
    host = checked_path(args.powershell)
    parent = checked_path(args.output_parent, directory=True)
    expected_host = 'ps7' if args.host == 'ps766' else 'ps51'
    source = Path(__file__).resolve()
    helper_source = source.with_name('installer_preview_host_probe.py')
    require(file_fact(helper_source)['sha256'] == HELPER_SHA256, 'Published host helper digest differs')
    root = Path(tempfile.mkdtemp(prefix=ROOT_PREFIX, dir=parent)).resolve()
    result = dict(schema='r0016-source-free-windows-carrier-acquisition.v1', status='ACQUISITION_INCOMPLETE',
                  fixture=str(root), installerExecuted=False, productQualificationRows=0, nativeCarrierAccepted=False)
    try:
        control = root / 'control'; control.mkdir()
        outputs = root / 'carrier-fixtures'; outputs.mkdir()
        copied = {}
        originals = []
        for original in (source, helper_source, *(source.parents[2] / 'tests' / name for name in PS_INPUTS)):
            before = file_fact(original)
            destination = control / original.name
            shutil.copyfile(original, destination)
            after = file_fact(destination, root)
            require((before['bytes'], before['sha256']) == (after['bytes'], after['sha256']), 'Launch input copy differs')
            copied[original.name] = after
            originals.append(before)
        helper = load_helper(control / helper_source.name)
        environment = helper.environment_for(root / 'outer-state', host, os.environ, False)
        # Microsoft about_Environment_Variables documents Off and requires this
        # variable before process startup; do not set it inside PowerShell.
        environment['POWERSHELL_UPDATECHECK'] = 'Off'
        require('COMPlus_MultiCoreJitNoProfileGather' not in environment, 'Default noGather behavior changed')
        helper.prepare_environment(environment)
        launched_inputs = {name: copied[name] for name in PS_INPUTS}
        command = [str(host), '-NoProfile', '-File', copied['install-preview-carrier-controls.ps1']['path'],
                   '-ExpectedHost', expected_host, '-OutputRoot', str(outputs),
                   '-PreviewHarness', copied['install-preview.ps1']['path'],
                   '-FixtureLibrary', copied['install-preview-acquire-timed.ps1']['path'],
                   '-WindowLibrary', copied['install-preview-window.ps1']['path']]
        plan = dict(schema='r0016-source-free-windows-carrier-plan.v1', preparedUtc=utc(), root=str(root),
                    hostKind=args.host, expectedHost=expected_host, host=file_fact(host), command=command,
                    environment=environment, noGatherOverride=False, launchedInputs=launched_inputs,
                    originals=originals, copiedInputs=copied, outerTimeoutSeconds=OUTER_SECONDS,
                    jobScope='Suspended creation, assignment before resume, kill-on-close lifetime management; not filesystem or network containment.')
        save(root / 'plan.json', plan)
        helper.save_required_snapshot(root / 'outer-state', root / 'outer-state.before.json')
        process = helper.run_observer(command, environment, root, OUTER_SECONDS)
        result['process'] = process
        helper.save_required_snapshot(root / 'outer-state', root / 'outer-state.after.json')
        for fact in originals + list(copied.values()) + [plan['host']]:
            verify_fact(fact, Path(fact['path']))
        result['association'] = validate_acquisition(process, command, root, outputs, host, expected_host, launched_inputs)
        result.update(status='ACQUIRED_SOURCE_FREE_CARRIER_ONLY', nativeCarrierAccepted=True,
                      independentHardContainment='NOT_ACQUIRED', sourceUnchanged=True)
    except Exception as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
    save(root / 'route-result.json', result)
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0 if result['nativeCarrierAccepted'] else 2


if __name__ == '__main__':
    sys.exit(main())
