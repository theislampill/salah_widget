#!/usr/bin/env python3
"""Bounded native Windows core and unchanged normal/NoOpen qualification route.

The existing Job Object helper owns process lifetime, not filesystem/network
containment. The original producer, receiver, and native entry assertions remain
unchanged. Imports and pure validators never start a native process.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import sys
import tarfile
import threading
import time

sys.dont_write_bytecode = True

SUPPORT_SHA = '9becda7102411dbef9a29efe5e5be95b9e02711563f3b845d496597011ff871b'
HELPER_SHA = '6776bc7b3d4e88d04f1dd811f5b7df0ea1553a7b8824f1f3e921c649c1aae9df'
RECEIVER_SHA = 'c0f1dccae4a0e7f73867a6aa8c8d2ef8a76cd59e27e4edfcb6f4499d317e7978'
CORE_SECONDS = 4200
COMPANION_SECONDS = 3300
ENTRY_SECONDS = 300
ROOT_PREFIX = 'r16-core-'
PINNED_INPUTS = {
    'install.ps1': '7fbe213b8e299d30ccd73f824a5a5d5766ac220ffdd778422cd018d3bc5c8ef4',
    'presets/salah-widget.tablissng.json': '9197c9bcfaf34ff06505963862e4e9280d3ad521e1ed287183f5d71cbce6b95f',
    'tests/install-preview.ps1': 'e5db234866df5fa41862dbb1d67fed4594b77b882823bfd631a9c5bf98525916',
    'tests/install-preview-acquire-timed.ps1': 'b7938e602fcf3864462f08b4748a139e894b8c4802d8643840d4439894a0ffd1',
    'tests/install-preview-window.ps1': '05318962698c269fb1d8b873e31b80b3ffe526739e21a49b5cf0459d523dcb83',
    'tests/install-preview-native-controls.py': RECEIVER_SHA,
    'tests/install-entry-native.py': '223b8ed54b342c23e7d0380bc669072a5fd87f2e42eeadb276b024aa8aa29819',
    'tools/qualification/installer_preview_host_probe.py': HELPER_SHA,
    'tools/qualification/installer_preview_windows_carrier.py': SUPPORT_SHA,
}
MUTATIONS = (
    'eager-staging', 'cleanup-in-preview', 'cached-path-return',
    'copy-success-when-suppressed', 'copy-null-array-truthiness',
    'clipboard-attempt-during-preview', 'native-api-load-before-guard',
    'swallowed-direct-transport',
)
HELPERS = tuple('helper-' + name for name in (
    'compiler-native-api-load', 'compiler-path-facts', 'compiler-directory-lease', 'compiler-output-lease',
    'compiler-context-allocation', 'compiler-cleanup-compiled', 'compiler-cleanup-failed', 'compiler-invocation',
    'native-api-load', 'user-sid', 'directory-lease', 'path-info', 'private-directory', 'private-file',
    'trusted-parent', 'owned-path', 'owned-file', 'digest', 'owned-enumeration', 'admitted-asset',
    'admitted-unpacked', 'admitted-preset', 'initialize', 'cleanup', 'begin-artifact', 'publication',
    'archive-validation', 'archive-extraction', 'metadata-cache', 'selector', 'download-cache',
    'unpacked-cache', 'preset-cache', 'copy-false', 'open', 'install-ask', 'import',
))
WRAPPERS = tuple('wrapper-' + name for name in (
    'github', 'store', 'ask', 'installed', 'mixed-legacy', 'mixed-unknown', 'none', 'legacy', 'unknown',
    'malformed', 'absent', 'wrong-case', 'missing-preset', 'invalid-option', 'invalid-environment-source',
    'empty-environment-default-source', 'valid-environment-store-source',
    'explicit-source-overrides-invalid-environment', 'noopen-github', 'noopen-store',
))
CONTROLS = tuple('control-' + kind + '-' + denied for kind in
                 ('outside-subject-method-write', 'direct-loopback-transport') for denied in ('False', 'True'))
CARRIERS = tuple('carrier-control-' + name for name in
                 ('fallthrough', 'exit-zero', 'exit-nonzero', 'throw', 'finally-exit', 'parameter-failure'))
CORE_CASES = frozenset((*HELPERS, *WRAPPERS, *CONTROLS, *CARRIERS,
                       *('mutant-discriminator-' + name for name in MUTATIONS)))
PAIR_CASES = ('base-normal-and-no-open', *MUTATIONS)


def load_exact_python(path, digest, name):
    """Import only an exact locally supplied Python instrument."""
    import hashlib
    path = Path(path)
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError('Pinned Python instrument differs: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# This exact module contributes pure custody/JSON helpers only. Its main,
# source-free acquisition function, and native carrier validator are never called.
R = load_exact_python(Path(__file__).with_name('installer_preview_windows_carrier.py'), SUPPORT_SHA, 'r0016_core_route_support')
Rejected = R.Rejected
require, save, file_fact, verify_fact = R.require, R.save, R.file_fact, R.verify_fact
checked_path, strict_json, utc = R.checked_path, R.strict_json, R.utc


def load_helper(path):
    checked_path(path)
    return load_exact_python(path, HELPER_SHA, 'r0016_core_host_helper')


def build_commands(inputs, powershell, python, host, core_output, core_receipt, companion_output):
    require(host in ('ps51', 'ps7'), 'Unexpected core host selector')
    source = lambda name: inputs[name]['path']
    return {
        'core': [str(powershell), '-NoProfile', '-File', source('tests/install-preview.ps1'),
                 '-SourceFile', source('install.ps1'), '-FixtureLibrary', source('tests/install-preview-acquire-timed.ps1'),
                 '-WindowLibrary', source('tests/install-preview-window.ps1'), '-OutputRoot', str(core_output), '-Suite', 'All'],
        'companion': [str(python), '-B', source('tests/install-preview-native-controls.py'),
                      '--input', str(core_receipt), '--source', source('install.ps1'),
                      '--preview-harness', source('tests/install-preview.ps1'), '--entry-harness', source('tests/install-entry-native.py'),
                      '--preset', source('presets/salah-widget.tablissng.json'), '--host', host,
                      '--output-root', str(companion_output), '--entry-budget', str(ENTRY_SECONDS)],
    }


def validate_terminal(process, command, root, budget):
    require(isinstance(process, dict) and process.get('command') == command, 'Stage command differs from its exact launch')
    require(type(process.get('exit')) is int and process['exit'] == 0, 'Stage did not return integer exit zero')
    for name in ('exitObserved', 'jobAssignedBeforeResume', 'jobClosedKillOnClose'):
        require(process.get(name) is True, 'Stage is missing terminal/lifetime proof: ' + name)
    require(process.get('timedOut') is False and 'error' in process and process['error'] is None, 'Stage timeout or process error')
    require(type(process.get('timeoutSeconds')) is int and process['timeoutSeconds'] == budget and
            R.finite_elapsed(process.get('elapsedSeconds'), budget), 'Stage deadline observation differs')
    require(type(process.get('processId')) is int and process['processId'] > 0, 'Stage PID is missing or invalid')
    require(process.get('capture') == 'direct files; no redirected pipe drain' and process.get('drain') == 'not applicable',
            'Stage capture differs from the exact helper protocol')
    return [verify_fact(process.get(kind), root / ('observer.' + kind + '.raw'), root) for kind in ('stdout', 'stderr')]


def unique_rows(rows, names, field='case'):
    require(isinstance(rows, list) and len(rows) == len(names), 'Required case denominator is incomplete')
    observed = [row.get(field) if isinstance(row, dict) else None for row in rows]
    require(all(isinstance(value, str) for value in observed) and len(set(observed)) == len(names) and
            set(observed) == set(names), 'Case identity is missing, duplicated, or unexpected')
    return {row[field]: row for row in rows}


def one_fixture(value, parent, pattern):
    parent = checked_path(parent, directory=True)
    fixture = checked_path(value, parent, directory=True)
    require(fixture.parent == parent and re.fullmatch(pattern, fixture.name), 'Fixture is not the expected direct owned child')
    candidates = [path for path in parent.iterdir() if re.fullmatch(pattern, path.name)]
    require(candidates == [fixture], 'Multiple or replayed producer fixtures exist')
    return fixture


def validate_core_header(core, inputs, host, executable, output_parent):
    require(core.get('schema') == 'r0016-preview-powershell-core.v2' and core.get('suite') == 'All' and core.get('pass') is True,
            'Core schema, complete suite, or aggregate disposition differs')
    require(core.get('nativeWindows') is True, 'Core is not a native Windows observation')
    version = core.get('host')
    require(isinstance(version, str) and ((host == 'ps51' and re.fullmatch(r'5\.1\.\d+\.\d+', version)) or
            (host == 'ps7' and version == '7.6.6')), 'Core host version differs')
    require(core.get('source') == inputs['install.ps1']['path'] and core.get('sourceSha256') == inputs['install.ps1']['sha256'],
            'Core source path or digest differs from the launched copy')
    for field in ('sourceUnchanged', 'testUnchanged', 'fixtureLibraryUnchanged', 'windowLibraryUnchanged'):
        require(core.get(field) is True, 'Core input stability is missing: ' + field)
    for field, role in (('testSha256', 'tests/install-preview.ps1'), ('fixtureLibrarySha256', 'tests/install-preview-acquire-timed.ps1'),
                        ('windowLibrarySha256', 'tests/install-preview-window.ps1')):
        require(core.get(field) == inputs[role]['sha256'], 'Core fixture input digest differs: ' + role)
    fixture = one_fixture(core.get('fixture'), output_parent, r'r0016-preview-ps-[0-9a-f]{32}')
    rows = unique_rows(core.get('results'), CORE_CASES)
    for name, row in rows.items():
        require(row.get('pass') is True and row.get('classification') == 'PASS' and row.get('error') is None, 'Core row did not pass: ' + name)
    unique_rows(core.get('mutants'), MUTATIONS, 'name')
    return fixture, rows


def verify_case_identity(row, core_root, name, mode, source, nonces):
    """Join each row to the exact case directory and spec the producer creates."""
    require(row.get('case') == name, 'Case row was relabelled')
    expected = core_root / (name + '-unicode-' + chr(0x0635))
    observed = row.get('fixture') if mode != 'control' else row.get('process', {}).get('fixture')
    require(observed == str(expected), 'Case fixture path differs from the exact producer case')
    checked_path(expected, core_root, directory=True)
    path = checked_path(expected / 'host-control/case.json', core_root)
    value = strict_json(path)
    require(value.get('caseName') == name and value.get('mode') == mode and
            value.get('subject') == str(expected / 'subject'), 'Case spec identity or subject differs')
    require(value.get('source') == source['path'] and value.get('sourceSha256') == source['sha256'], 'Case spec source differs')
    verify_fact(source, Path(source['path']), core_root)
    nonce = value.get('nonce')
    require(isinstance(nonce, str) and re.fullmatch(r'[0-9a-f]{32}', nonce) and nonce not in nonces, 'Case nonce is missing or replayed')
    nonces.add(nonce)
    return file_fact(path, core_root)


def validate_core_report(core, inputs, host, executable, output_parent, owner, receiver):
    fixture, rows = validate_core_header(core, inputs, host, executable, output_parent)
    path = checked_path(fixture / 'results.json', fixture)
    require(strict_json(path) == core, 'Core raw report differs from complete captured stdout')
    args = argparse.Namespace(input=path, core_receipt=None, source=Path(inputs['install.ps1']['path']),
        preview_harness=Path(inputs['tests/install-preview.ps1']['path']), entry_harness=Path(inputs['tests/install-entry-native.py']['path']),
        preset=Path(inputs['presets/salah-widget.tablissng.json']['path']), host=host)
    plan = receiver.preflight(args)
    require(plan.get('producerExecutable') == str(executable) and plan.get('producerNativeWindows') is True and
            plan.get('requestedHostMatchesProducer') is True and plan.get('producerHost') == core['host'], 'Core receiver host association differs')
    require(plan.get('coreAggregatePass') is True, 'Receiver did not preserve complete core PASS')
    facts = list(plan['custodyFiles'])
    frozen = file_fact(fixture / 'actual-source.ps1', fixture)
    require(core.get('frozenSource') == frozen['path'] and frozen['sha256'] == inputs['install.ps1']['sha256'], 'Frozen source identity differs')
    nonces = set()
    for name in CONTROLS:
        facts.append(verify_case_identity(rows[name], fixture, name, 'control', frozen, nonces))
    for name in CARRIERS:
        facts.append(verify_case_identity(rows[name], fixture, name, 'wrapper', file_fact(rows[name]['source'], fixture), nonces))
    for variant in plan['variants']:
        name = variant['name']; discriminator = rows['mutant-discriminator-' + name]
        mode = receiver.RECIPES[name][2]
        require(discriminator['healthy'].get('error') is None, 'Matched healthy mutation case reports an error')
        facts.append(verify_case_identity(discriminator['healthy'], fixture, 'matched-' + name, mode, frozen, nonces))
        facts.append(verify_case_identity(discriminator['mutant'], fixture, 'mutant-' + name, mode, file_fact(variant['source'], fixture), nonces))
    for name in (*HELPERS, *WRAPPERS):
        row = rows[name]
        facts.append(verify_case_identity(row, fixture, name, 'helper' if name.startswith('helper-') else 'wrapper', frozen, nonces))
        require(row.get('sourceSha256') == inputs['install.ps1']['sha256'], 'Ordinary case source hash differs')
        proof = receiver.verify_case_files(row, fixture, inputs['install.ps1']['sha256'],
            'helper' if name.startswith('helper-') else 'wrapper', require_window=True, native_windows=True,
            expected_host=str(executable), expected_driver=plan['producerDriver'])
        require(not proof['events'] and row.get('observation') is not None, 'Passing ordinary case lacks a completed effect-free observation')
        facts.extend(proof['files'])
    unique = {fact['path']: fact for fact in facts}
    for record in unique.values(): verify_fact(record, Path(record['path']), owner)
    return dict(report=file_fact(path, owner), fixture=str(fixture), host=core['host'], expectedHost=host,
        commandHost=str(executable), counts=dict(helpers=37, wrappers=20, mutations=8, carriers=6, guards=4, total=75),
        receiverPlan=plan, custodyFiles=list(unique.values()), source=inputs['install.ps1'])


def validate_companion_header(value, host, output_parent):
    require(value.get('schema') == 'r0016-native-positive-companion.v1' and value.get('mode') == 'native' and
            value.get('nativeExecution') is True and value.get('host') == host and value.get('status') == 'PASS' and value.get('pass_') is True,
            'Native companion disposition, mode, or host differs')
    require(value.get('custodyUnchanged') is True and value.get('allRequiredNativeSurvivalEstablished') is True,
            'Complete normal survival or stable custody is missing')
    require(value.get('selectedVariants') == list(MUTATIONS), 'Companion did not select the exact complete mutation inventory')
    coverage = value.get('coverage', {})
    require(coverage.get('requiredVariants') == list(MUTATIONS) and coverage.get('completeDenominatorSelected') is True and
            type(coverage.get('nativeCasesPlanned')) is int and coverage['nativeCasesPlanned'] == 18 and
            type(coverage.get('harnessInvocationsPlanned')) is int and coverage['harnessInvocationsPlanned'] == 9,
            'Companion case denominator differs')
    fixture = one_fixture(value.get('fixture'), output_parent, r'p-[0-9a-f]{16}')
    rows = unique_rows(value.get('results'), PAIR_CASES)
    for name, row in rows.items():
        require(row.get('pass_') is True and row.get('classification') == 'PASS' and 'error' in row and row['error'] is None,
                'Native normal pair did not pass: ' + name)
    return fixture, rows


def preflight_identity(plan):
    """Ignore enumeration order only in the nine admitted file-fact arrays."""
    require(type(plan) is dict and type(plan.get('variants')) is list,
            'Malformed companion preflight')
    variants = plan['variants']
    require(len(variants) == len(MUTATIONS) and all(type(row) is dict for row in variants) and
            len({row.get('name') for row in variants}) == len(MUTATIONS) and
            {row.get('name') for row in variants} == set(MUTATIONS),
            'Companion preflight variant inventory differs')

    def file_multiset(records):
        require(type(records) is list, 'Preflight file facts are not an array')
        for record in records:
            require(type(record) is dict and set(record) == {'path', 'bytes', 'sha256'} and
                    type(record['path']) is str and bool(record['path']) and
                    type(record['bytes']) is int and record['bytes'] >= 0 and
                    type(record['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', record['sha256']),
                    'Malformed complete preflight file fact')
        # Sorting canonical full records retains every duplicate occurrence.
        return sorted(json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False)
                      for record in records)

    normalized = dict(plan)
    normalized['custodyFiles'] = file_multiset(plan.get('custodyFiles'))
    normalized['variants'] = []
    for variant in variants:
        row = dict(variant)
        row['priorEvidence'] = file_multiset(variant.get('priorEvidence'))
        normalized['variants'].append(row)
    # Every other value, scalar type, field and array order remains significant.
    return json.dumps(normalized, sort_keys=True, separators=(',', ':'), allow_nan=False)


def validate_companion_report(value, inputs, core, executable, python, output_parent, owner):
    host = core['expectedHost']
    fixture, rows = validate_companion_header(value, host, output_parent)
    result_path = checked_path(fixture / 'results.json', fixture)
    require(strict_json(result_path) == value, 'Companion raw report differs from captured stdout')
    require(value.get('test') == inputs['tests/install-preview-native-controls.py'], 'Companion receiver input identity differs')
    require(preflight_identity(value.get('preflight')) == preflight_identity(core['receiverPlan']), 'Companion preflight differs from the admitted same-host core')
    identity = value.get('nativeHost', {})
    require(identity.get('installerExecuted') is False and identity.get('version') == core['host'], 'Companion host acquisition differs')
    verify_fact(identity.get('executable'), executable)
    require(identity.get('command') == [str(executable), '-NoProfile', '-NonInteractive', '-Command',
            '[Console]::Write($PSVersionTable.PSVersion.ToString())'], 'Companion host query command differs')
    expected_custody = value['preflight']['custodyFiles']
    copies = value.get('retainedCustodyFiles')
    require(isinstance(copies, list) and len(copies) == len(expected_custody), 'Companion retained custody inventory differs')
    facts = [file_fact(result_path, owner)]
    host_stdout, host_stderr = fixture / 'host-version/stdout.txt', fixture / 'host-version/stderr.txt'
    facts.extend([file_fact(host_stdout, owner), file_fact(host_stderr, owner)])
    require(host_stdout.read_text(encoding='utf-8-sig').strip() == core['host'], 'Companion raw host version differs')
    for index, (record, expected) in enumerate(zip(copies, expected_custody)):
        require(isinstance(record, dict) and set(record) == {'path', 'bytes', 'sha256', 'retainedCopy'}, 'Malformed retained custody role')
        original = {key: record[key] for key in ('path', 'bytes', 'sha256')}
        require(original == expected, 'Retained custody source association differs')
        facts.append(verify_fact(original, Path(original['path']), owner))
        retained_path = fixture / 'inputs' / 'prior-evidence' / (str(index).zfill(3) + '.bin')
        require(record['retainedCopy'] == str(retained_path), 'Retained custody copy path differs')
        retained = file_fact(retained_path, fixture)
        require((retained['bytes'], retained['sha256']) == (expected['bytes'], expected['sha256']), 'Retained custody copy bytes differ')
        facts.append(retained)
    variants = {row['name']: row for row in core['receiverPlan']['variants']}
    for index, name in enumerate(PAIR_CASES):
        row = rows[name]
        source = inputs['install.ps1'] if index == 0 else file_fact(Path(variants[name]['source']), owner)
        require(row.get('source') == source['path'] and row.get('sourceSha256') == source['sha256'] and
                row.get('sourceAndHarnessUnchanged') is True, 'Native pair source or harness identity differs')
        if index:
            require(row.get('normalSurvival') == 'PASS' and row.get('priorPreviewAssertion') == variants[name]['priorAssertion'],
                    'Normal pair is not joined to its exact prior preview discriminator')
        carrier = checked_path(fixture / 'c' / str(index), fixture, directory=True)
        require(row.get('retainedCarrierRoot') == str(carrier), 'Native pair carrier path differs')
        observation = row.get('observation', {})
        command = [str(python), inputs['tests/install-entry-native.py']['path'], source['path'], '--host', host,
                   '--scenario', 'positive', '--scenario', 'no-open', '--preset', inputs['presets/salah-widget.tablissng.json']['path']]
        require(observation.get('command') == command and observation.get('caseLabel') == name and
                type(observation.get('carrierIndex')) is int and observation['carrierIndex'] == index, 'Native pair command or index differs')
        require(type(observation.get('exit')) is int and observation['exit'] == 0 and
                type(observation.get('carrierPid')) is int and observation['carrierPid'] > 0 and
                type(observation.get('timeoutSeconds')) is int and observation['timeoutSeconds'] == ENTRY_SECONDS and
                R.finite_elapsed(observation.get('elapsedSeconds'), ENTRY_SECONDS) and 'timedOut' not in observation,
                'Native pair terminal is missing, late, or failed')
        require(observation.get('ownedCarrierRoot') == str(carrier) and observation.get('ownedTempParent') == str(carrier / 't') and
                observation.get('outputCapture') == 'owned regular files; no companion output pipes', 'Native pair capture owner differs')
        out_path, err_path = carrier / 'stdout.json', carrier / 'stderr.txt'
        require(observation.get('stdout') == str(out_path) and observation.get('stderr') == str(err_path), 'Native pair capture path differs')
        facts.extend([file_fact(out_path, owner), file_fact(err_path, owner)])
        terminal_path, launch_path = carrier / 'terminal.json', carrier / 'launch.json'
        require(strict_json(terminal_path) == observation, 'Native pair raw terminal differs')
        launch = strict_json(launch_path)
        expected_launch = {key: observation[key] for key in ('command', 'startedUtc', 'timeoutSeconds', 'stdout', 'stderr',
            'ownedCarrierRoot', 'caseLabel', 'carrierIndex', 'ownedTempParent', 'outputCapture')}
        require(launch == expected_launch, 'Native pair raw launch differs from its terminal binding')
        facts.extend([file_fact(terminal_path, owner), file_fact(launch_path, owner)])
        native = strict_json(out_path)
        require(native == row.get('nativeReceipt') and native.get('source') == source['sha256'] and
                native.get('preset') == inputs['presets/salah-widget.tablissng.json']['sha256'] and
                native.get('selectedHosts') == [host] and native.get('selectedScenarios') == ['positive', 'no-open'],
                'Native pair raw receipt, source, preset, or selection differs')
        native_fixture = checked_path(native.get('fixture'), carrier / 't', directory=True)
        require(native_fixture.parent == carrier / 't' and native_fixture.name.startswith('salah native entry-') and
                row.get('fixture') == str(native_fixture), 'Native entry fixture differs from its owned carrier')
        entries = unique_rows(native.get('results'), ('positive', 'no-open'))
        for scenario, entry in entries.items():
            observed = entry.get('observation', {})
            require(entry.get('host') == host and entry.get('pass_') is True and observed.get('interceptionLoaded') is True and
                    type(observed.get('entryExit')) is int and observed['entryExit'] == 0, 'Original native entry assertion/readiness failed')
            actual_command = observed.get('command')
            expected_tail = ['-NoProfile', '-File', source['path'], '-PresetUrl', 'https://example.invalid/preset',
                             '-InstallSource', 'github', '-WidgetHash', 'lat=24.47&lon=39.61&method=4']
            if scenario == 'no-open': expected_tail.append('-NoOpen')
            require(isinstance(actual_command, list) and len(actual_command) == 1 + len(expected_tail) and
                    Path(actual_command[0]).resolve(strict=True) == executable and actual_command[1:] == expected_tail,
                    'Original native entry command differs from its exact normal/NoOpen source')
            # The original field is recorded after capture and snapshot work,
            # not at process exit. Its unchanged subprocess budget is 60 seconds;
            # the complete pair has the independently observed 300-second bound.
            require(type(observed.get('timeoutSeconds')) is int and observed['timeoutSeconds'] == 60 and
                    R.finite_elapsed(observed.get('elapsedSeconds'), observation['elapsedSeconds']),
                    'Original native entry budget or retained elapsed observation differs')
            entry_fixture = checked_path(native_fixture / (host + '-' + scenario), native_fixture, directory=True)
            require(observed.get('fixture') == str(entry_fixture), 'Original native case fixture differs')
            nonce = observed.get('readinessNonce')
            require(isinstance(nonce, str) and re.fullmatch(r'[0-9a-f]{32}', nonce), 'Original native readiness nonce is invalid')
            ready = checked_path(entry_fixture / 'ready', owner)
            ready_fields = ready.read_text(encoding='utf-8-sig').split('\t')
            require(len(ready_fields) == 2 and ready_fields[0].isdigit() and int(ready_fields[0]) > 0 and
                    ready_fields[1] == nonce, 'Original native raw readiness PID/nonce differs')
            for kind in ('stdout', 'stderr'):
                path = entry_fixture / (kind + '.txt')
                require(observed.get(kind) == str(path), 'Original native capture path differs')
                facts.append(file_fact(path, owner))
            facts.append(file_fact(ready, owner))
    for record in facts: verify_fact(record, Path(record['path']), owner)
    return dict(report=file_fact(result_path, owner), fixture=str(fixture), host=host,
                pairedCarriers=9, nativeEntries=18, cases=list(PAIR_CASES), custodyFiles=facts)


def prepare_stage_environment(helper, state, executable, inherited, host):
    environment = helper.environment_for(state, executable, inherited, False)
    environment['POWERSHELL_UPDATECHECK'] = 'Off'
    if host == 'ps7': environment['INSTALL_TEST_PS7'] = str(executable)
    require(not any(key.upper() == 'COMPLUS_MULTICOREJITNOPROFILEGATHER' for key in environment), 'Default gather behavior changed')
    helper.prepare_environment(environment)
    return environment


def run_phase(helper, name, command, environment, stage, budget):
    """The exact helper owns its Job; heartbeats disclose progress only."""
    helper.save_required_snapshot(stage / 'state', stage / 'state.before.json')
    print(json.dumps(dict(event='phase-start', phase=name, timeoutSeconds=budget, utc=utc())), flush=True)
    finished, outcome = threading.Event(), {}
    def worker():
        try: outcome['process'] = helper.run_observer(command, environment, stage, budget)
        except BaseException as error: outcome['error'] = error
        finally: finished.set()
    thread = threading.Thread(target=worker, name='r0016-' + name, daemon=True)
    start = time.monotonic(); thread.start()
    while not finished.wait(60):
        print(json.dumps(dict(event='phase-running', phase=name, elapsedSeconds=round(time.monotonic() - start, 3), timeoutSeconds=budget)), flush=True)
    thread.join()
    # Keep the unchanged whole-state observations. No equality or exclusions are
    # introduced around host startup, normal installation, or fixture activity.
    helper.save_required_snapshot(stage / 'state', stage / 'state.after.json')
    if 'error' in outcome: raise outcome['error']
    print(json.dumps(dict(event='phase-terminal', phase=name, exit=outcome['process'].get('exit'),
                          elapsedSeconds=outcome['process'].get('elapsedSeconds'))), flush=True)
    return outcome['process']


def archive_owned_root(parent, archive_path):
    parent = checked_path(parent, directory=True)
    roots = list(parent.glob(ROOT_PREFIX + '*'))
    require(len(roots) == 1, 'Exactly one owned core route root is required')
    root = checked_path(roots[0], parent, directory=True)
    archive_path = Path(archive_path)
    require(archive_path.is_absolute() and archive_path.parent == parent and not archive_path.exists(), 'Invalid or occupied archive destination')
    with tarfile.open(archive_path, 'w:gz', dereference=False) as archive:
        pending = [root]
        while pending:
            path = pending.pop(); info = path.lstat()
            name = 'installer-evidence' if path == root else 'installer-evidence/' + path.relative_to(root).as_posix()
            if stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400):
                entry = tarfile.TarInfo(name); entry.type = tarfile.SYMTYPE; entry.linkname = os.readlink(path)
                entry.mode, entry.mtime = stat.S_IMODE(info.st_mode), int(info.st_mtime); archive.addfile(entry)
            else:
                require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode), 'Unsupported special entry in owned evidence')
                archive.add(path, arcname=name, recursive=False)
                if stat.S_ISDIR(info.st_mode): pending.extend(sorted(path.iterdir(), reverse=True))
    return str(archive_path)


def is_native_windows():
    return os.name == 'nt'


def finish_input_custody(result, facts):
    try:
        require(bool(facts), 'Complete launch input custody was not established')
        for record in facts: verify_fact(record, Path(record['path']))
        result['sourceAndInputsUnchanged'] = True
        return True
    except Exception as error:
        result['admissionBeforeCustodyFailure'] = {
            key: result.get(key) for key in ('status', 'nativeCoreAccepted', 'normalVariantsAccepted')}
        result.update(status='INPUT_CUSTODY_FAILED', sourceAndInputsUnchanged=False,
                      nativeCoreAccepted=False, normalVariantsAccepted=False,
                      custodyError=type(error).__name__ + ': ' + str(error))
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=('ps51', 'ps766'))
    parser.add_argument('--powershell', type=Path)
    parser.add_argument('--output-parent', type=Path, required=True)
    parser.add_argument('--source-commit')
    parser.add_argument('--archive-only', action='store_true')
    parser.add_argument('--archive', type=Path)
    args = parser.parse_args(argv)
    if not is_native_windows(): parser.error('Native Windows required; no native process was started')
    if args.archive_only:
        require(args.archive is not None and args.host is None and args.powershell is None and args.source_commit is None,
                'Archive-only mode accepts only parent and archive paths')
        print(archive_owned_root(args.output_parent, args.archive)); return 0
    require(args.host is not None and args.powershell is not None and args.archive is None and
            isinstance(args.source_commit, str) and re.fullmatch(r'[0-9a-f]{40}', args.source_commit), 'Exact host and source commit are required')
    host = 'ps7' if args.host == 'ps766' else 'ps51'
    executable = checked_path(args.powershell); python = checked_path(Path(sys.executable).resolve())
    parent = checked_path(args.output_parent, directory=True)
    root = parent / (ROOT_PREFIX + secrets.token_hex(8)); root.mkdir()
    result = dict(schema='r0016-windows-core-acquisition.v1', status='ACQUISITION_INCOMPLETE', fixture=str(root),
        sourceCommit=args.source_commit, expectedHost=host, nativeCoreAccepted=False, normalVariantsAccepted=False,
        independentHardContainment='NOT_ACQUIRED', phases={}, scope='All75 helper/wrapper/mutation core and 18 normal/NoOpen entries; no direct-preview qualification')
    originals, copied, fixed_facts = [], {}, []
    status = 2
    try:
        source = Path(__file__).resolve(); repository = source.parents[2]
        control = root / 'control'; control.mkdir()
        roles = dict(PINNED_INPUTS); roles['tools/qualification/installer_preview_windows_core.py'] = file_fact(source)['sha256']
        for name, digest in roles.items():
            original = file_fact(repository / name)
            require(original['sha256'] == digest, 'Input digest differs from the reviewed role: ' + name)
            destination = control / name; destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original['path'], destination)
            copied[name] = file_fact(destination, root)
            require((copied[name]['bytes'], copied[name]['sha256']) == (original['bytes'], original['sha256']), 'Copied input differs')
            originals.append(original)
        fixed_facts = originals + list(copied.values()) + [file_fact(executable), file_fact(python)]
        helper = load_helper(Path(copied['tools/qualification/installer_preview_host_probe.py']['path']))
        receiver = load_exact_python(copied['tests/install-preview-native-controls.py']['path'], RECEIVER_SHA, 'r0016_core2_receiver')
        core_stage, companion_stage = root / 'core', root / 'n'
        core_stage.mkdir(); companion_stage.mkdir()
        core_env = prepare_stage_environment(helper, core_stage / 'state', executable, os.environ, host)
        companion_env = prepare_stage_environment(helper, companion_stage / 'state', executable, os.environ, host)
        core_output = core_stage / 'fixtures'; core_output.mkdir()
        companion_output = Path(companion_env['TEMP'])
        # The exact core report path is obtained only after its complete owned
        # fixture is acquired; no earlier receipt or guessed path is accepted.
        initial_command = build_commands(copied, executable, python, host, core_output, core_output / 'not-yet-acquired.json', companion_output)['core']
        plan = dict(schema='r0016-windows-core-plan.v1', preparedUtc=utc(), sourceCommit=args.source_commit,
            root=str(root), expectedHost=host, host=file_fact(executable), python=file_fact(python), originals=originals, copiedInputs=copied,
            stages=dict(core=dict(command=initial_command, environment=core_env, timeoutSeconds=CORE_SECONDS),
                        companion=dict(environment=companion_env, timeoutSeconds=COMPANION_SECONDS, entryBudgetSeconds=ENTRY_SECONDS)),
            jobScope='Suspended creation, assignment before resume and kill-on-close lifetime management; no filesystem/network sandbox',
            noGatherOverride=False, expectedCoreCases=sorted(CORE_CASES), expectedNativeEntries=18)
        save(root / 'plan.json', plan)
        result['phases']['core'] = dict(status='STARTING', command=initial_command)
        save(root / 'route-result.json', result)
        process = run_phase(helper, 'core', initial_command, core_env, core_stage, CORE_SECONDS)
        result['phases']['core']['process'] = process; save(root / 'route-result.json', result)
        validate_terminal(process, initial_command, core_stage, CORE_SECONDS)
        core_report = strict_json(core_stage / 'observer.stdout.raw')
        core = validate_core_report(core_report, copied, host, executable, core_output, root, receiver)
        result['phases']['core'].update(status='ADMITTED', association=core)
        result['nativeCoreAccepted'] = True
        for record in fixed_facts: verify_fact(record, Path(record['path']))
        commands = build_commands(copied, executable, python, host, core_output, Path(core['report']['path']), companion_output)
        require(commands['core'] == initial_command, 'Core command drifted during companion planning')
        plan['stages']['companion']['command'] = commands['companion']; plan['stages']['companion']['coreReceipt'] = core['report']
        save(root / 'plan.json', plan)
        result['phases']['companion'] = dict(status='STARTING', command=commands['companion'])
        save(root / 'route-result.json', result)
        process = run_phase(helper, 'companion', commands['companion'], companion_env, companion_stage, COMPANION_SECONDS)
        result['phases']['companion']['process'] = process; save(root / 'route-result.json', result)
        validate_terminal(process, commands['companion'], companion_stage, COMPANION_SECONDS)
        companion_report = strict_json(companion_stage / 'observer.stdout.raw')
        companion = validate_companion_report(companion_report, copied, core, executable, python, companion_output, root)
        for record in core['custodyFiles']: verify_fact(record, Path(record['path']), root)
        result['phases']['companion'].update(status='ADMITTED', association=companion)
        result.update(status='ACQUIRED_WINDOWS_CORE_AND_NORMAL_VARIANTS', normalVariantsAccepted=True)
        status = 0
    except Exception as error:
        result['error'] = type(error).__name__ + ': ' + str(error)
        result['status'] = 'ACQUISITION_OR_RECEIPT_NOT_ADMITTED'
        for phase in result['phases'].values():
            if phase.get('status') == 'STARTING': phase['status'] = 'NOT_ADMITTED'
    finally:
        if not finish_input_custody(result, fixed_facts): status = 2
        save(root / 'route-result.json', result)
    print(json.dumps(dict(status=result['status'], fixture=str(root), nativeCoreAccepted=result['nativeCoreAccepted'],
                         normalVariantsAccepted=result['normalVariantsAccepted']), ensure_ascii=True), flush=True)
    return status


if __name__ == '__main__':
    raise SystemExit(main())
