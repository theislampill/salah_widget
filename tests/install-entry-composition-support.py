"""NEW R0016 composition instrument; pure receivers plus owned Windows acquisition.

This is a proposal, not recovered historical bytes or an OS sandbox. The direct
and nested-file observations have different meanings and retain separate states.
Every native acquisition needs the caller's reviewed containment. No installer or
PowerShell process is run by importing this module.
"""
import hashlib
import json
import math
import ntpath
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import time

CORE_SHA = 'e5db234866df5fa41862dbb1d67fed4594b77b882823bfd631a9c5bf98525916'
WINDOW_SHA = '05318962698c269fb1d8b873e31b80b3ffe526739e21a49b5cf0459d523dcb83'
PREVIEW_SOURCE_SHA = '7fbe213b8e299d30ccd73f824a5a5d5766ac220ffdd778422cd018d3bc5c8ef4'
TIMEOUT = 60
ACK_TIMEOUT = 20
ORIGINAL_SCENARIOS = ('github', 'cached', 'store', 'ask', 'installed', 'mixed',
    'legacy', 'none', 'missing-preset', 'bad-option', 'positive', 'no-open',
    'readable', 'unreadable', 'invalid-env-source', 'valid-env-store',
    'preview-noopen-github', 'preview-noopen-store')
SCENARIOS = ORIGINAL_SCENARIOS + ('env-source-default', 'explicit-source-override')
FAILURE_SCENARIOS = frozenset(('legacy', 'none', 'bad-option', 'unreadable', 'invalid-env-source'))
ROLE_PATHS = {'subject': 'subject', 'profile': 'host-home', 'modules': 'modules',
              'asset': 'fixture.zip', 'preset': 'canonical-preset.json', 'analysisCache': 'analysis-cache'}
ROW_FIELDS = frozenset(('role', 'path', 'kind', 'mode', 'device', 'inode', 'uid', 'gid',
                        'mtimeNs', 'ctimeNs', 'attributes', 'security', 'bytes', 'sha256', 'links'))
CLONE_FIELDS = frozenset(('device', 'inode', 'ctimeNs'))
PATH_ENV = frozenset(('TEMP', 'TMP', 'LOCALAPPDATA', 'APPDATA', 'PROGRAMFILES', 'PROGRAMFILES(X86)',
    'HOME', 'USERPROFILE', 'PSMODULEANALYSISCACHEPATH', 'INSTALL_READY_FILE', 'INSTALL_PROFILE_ACK',
    'INSTALL_EFFECT_LOG', 'INSTALL_SUBJECT_ROOT', 'INSTALL_BOOTSTRAP_LOG', 'INSTALL_ASSET_ZIP',
    'INSTALL_PRESET_FIXTURE', 'INSTALL_FIXTURE_PF', 'INSTALL_FIXTURE_PF86', 'INSTALL_UNREADABLE_FILE',
    'INSTALL_READABLE_PEER', 'INSTALL_UNREADABLE_PROOF', 'R0016_INPUT_PROBE', 'R0016_MODULE_INPUT_PROOF'))


def require(condition, reason):
    if not condition:
        raise AssertionError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fact(path):
    path = Path(path)
    require(path.is_absolute(), 'Fact path must be absolute')
    for component in [path] + list(path.parents):
        info = component.lstat()
        require(not component.is_symlink() and not (getattr(info, 'st_file_attributes', 0) & 0x400), 'Fact refuses links/reparse ancestors')
    require(stat.S_ISREG(path.lstat().st_mode), 'Fact requires a regular file')
    path = path.resolve(strict=True)
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.partial')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    temporary.replace(path)


def complete_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON member: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise AssertionError('Nonfinite JSON number: ' + value)
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs, parse_constant=constant)


def owned_environment(inherited):
    """Only OS launch inputs; fixture/product settings are assigned by the caller.

    Credentials and unrelated installer defaults cannot silently become inputs.
    Product environment omission is deliberate and later recorded in full.
    """
    allowed = {'SYSTEMROOT', 'WINDIR', 'SYSTEMDRIVE', 'COMSPEC', 'OS', 'PATHEXT',
               'PROCESSOR_ARCHITECTURE', 'PROCESSOR_IDENTIFIER', 'PROCESSOR_LEVEL',
               'PROCESSOR_REVISION', 'NUMBER_OF_PROCESSORS'}
    env = {key: value for key, value in inherited.items() if key.upper() in allowed}
    require(len({key.upper() for key in env}) == len(env), 'Ambiguous OS environment key')
    env.update(POWERSHELL_TELEMETRY_OPTOUT='1', DOTNET_CLI_TELEMETRY_OPTOUT='1', POWERSHELL_UPDATECHECK='Off')
    return env


def direct_parameters(command, host, source):
    require(type(host) is str and (ntpath.isabs(host) or Path(host).is_absolute()), 'Host must be an explicit absolute executable')
    require(type(str(source)) is str and (ntpath.isabs(str(source)) or Path(source).is_absolute()), 'Source path must be absolute')
    require(type(command) is list and all(type(value) is str for value in command), 'Command is not a string argv')
    require(command[:4] == [str(host), '-NoProfile', '-File', str(source)], 'Wrong exact direct entry')
    arguments, rows = command[4:], []
    for name in ('PresetUrl', 'WidgetHash'):
        require(len(arguments) >= 2 and arguments[0] == '-' + name, 'Missing ordered string parameter: ' + name)
        rows.append({'name': name, 'type': 'string', 'value': arguments[1]})
        arguments = arguments[2:]
    if arguments[:1] == ['-InstallSource']:
        require(len(arguments) >= 2, 'Missing InstallSource scalar')
        rows.append({'name': 'InstallSource', 'type': 'string', 'value': arguments[1]})
        arguments = arguments[2:]
    for name in ('DryRun', 'NoOpen'):
        if arguments[:1] == ['-' + name]:
            rows.append({'name': name, 'type': 'switch', 'value': True})
            arguments = arguments[1:]
    require(not arguments, 'Unexpected, duplicated or reordered direct arguments')
    return rows


def exact_exit(direct_exit, held, scenario):
    require(scenario in SCENARIOS and scenario not in ('positive', 'no-open'), 'Unknown paired scenario')
    expected = 1 if scenario in FAILURE_SCENARIOS else 0
    require(type(direct_exit) is int and direct_exit == expected, 'Wrong exact direct process exit')
    require(type(held.get('entryExit')) is int and held['entryExit'] == direct_exit, 'Held semantic exit differs from direct exit')
    completion = held.get('sourceCompletion')
    require(completion in ('fallthrough', 'exit-code-observed', 'terminating-exception'), 'Missing source completion')
    if completion == 'fallthrough':
        require(held['entryExit'] == 0 and held.get('sourceExitCode') is None and held.get('sourceException') is None, 'Invalid fallthrough receipt')
    elif completion == 'exit-code-observed':
        require(type(held.get('sourceExitCode')) is int and held['sourceExitCode'] == held['entryExit'] and held.get('sourceException') is None, 'Invalid explicit source exit')
    else:
        require(held['entryExit'] == 1 and held.get('sourceExitCode') is None and type(held.get('sourceException')) is str and bool(held['sourceException']), 'Invalid source exception')


def validate_rows(rows):
    require(type(rows) is list and rows, 'Empty full inventory')
    keyed = {}
    for row in rows:
        require(type(row) is dict and set(row) == ROW_FIELDS, 'Incomplete or unknown inventory fields')
        require(row['role'] in ROLE_PATHS and type(row['path']) is str, 'Unknown input role/path')
        relative = Path(row['path'])
        require(not relative.is_absolute() and '..' not in relative.parts and '\\' not in row['path'], 'Invalid relative inventory path')
        require(row['kind'] in ('absent', 'file', 'directory'), 'Unknown input kind')
        if row['kind'] == 'absent':
            require(all(row[field] is None for field in ROW_FIELDS - {'role', 'path', 'kind'}), 'Absent input carries invented metadata')
        else:
            require(all(type(row[field]) is int and row[field] >= 0 for field in ('mode', 'device', 'inode', 'uid', 'gid', 'mtimeNs', 'ctimeNs')), 'Missing or ambiguous input identity/timestamps')
            require(row['attributes'] is None or type(row['attributes']) is int, 'Invalid input attributes')
            require(row['security'] is None or type(row['security']) is str and bool(row['security']), 'Invalid security facts')
            if row['kind'] == 'file':
                require(type(row['bytes']) is int and row['bytes'] >= 0 and type(row['links']) is int and row['links'] >= 1 and type(row['sha256']) is str and re.fullmatch(r'[0-9a-f]{64}', row['sha256']), 'Incomplete file input facts')
            else:
                require(all(row[field] is None for field in ('bytes', 'sha256', 'links')), 'Directory carries file metadata')
        key = (row['role'], row['path'])
        require(key not in keyed, 'Duplicate inventory entry')
        keyed[key] = row
    require({row['role'] for row in rows} == set(ROLE_PATHS), 'Missing input root')
    for role in ROLE_PATHS:
        require((role, '.') in keyed, 'Missing input root fact')
        if keyed[role, '.']['kind'] == 'absent':
            require(role == 'analysisCache' and sum(row['role'] == role for row in rows) == 1, 'Unexpected absent input')
    return keyed


def map_inputs(direct_rows, held_rows):
    left, right = validate_rows(direct_rows), validate_rows(held_rows)
    require(left.keys() == right.keys(), 'Input names or complete role inventory differ')
    mapping = []
    for key in sorted(left):
        original, copied = left[key], right[key]
        for field in ROW_FIELDS - CLONE_FIELDS:
            require(original[field] == copied[field], 'Input association differs: %s/%s:%s' % (*key, field))
        mapping.append({'role': key[0], 'path': key[1], 'direct': original, 'held': copied,
                        'cloneIdentity': {field: {'direct': original[field], 'held': copied[field]} for field in sorted(CLONE_FIELDS)}})
    return mapping


def verify_input_mapping(mapping, direct_rows, held_rows):
    require(mapping == map_inputs(direct_rows, held_rows), 'Mapping omits, replays or misstates input facts')


def inventory(root, support, locks=None):
    root, rows, locks = Path(root), [], locks or {}
    for role, relative in ROLE_PATHS.items():
        entry = root / relative
        if not entry.exists() and not entry.is_symlink():
            rows.append(dict.fromkeys(ROW_FIELDS))
            rows[-1].update(role=role, path='.', kind='absent')
            continue
        paths, pending = [], [entry]
        while pending:
            path = pending.pop()
            item = path.lstat()
            require(not path.is_symlink() and not (getattr(item, 'st_file_attributes', 0) & 0x400), 'Input inventory refuses links/reparse entries before descent')
            paths.append(path)
            if stat.S_ISDIR(item.st_mode):
                pending.extend(reversed(sorted(path.iterdir())))
        for path in paths:
            info = path.lstat()
            require(not path.is_symlink() and not (getattr(info, 'st_file_attributes', 0) & 0x400), 'Input inventory refuses links/reparse entries')
            directory = stat.S_ISDIR(info.st_mode)
            require(directory or stat.S_ISREG(info.st_mode), 'Input inventory refuses special entries')
            held = locks.get(os.path.normcase(str(path.absolute())))
            observed = held.observe() if held is not None else None
            if held is not None:
                require(observed == held.initial, 'Held unreadable metadata changed')
                info = held.path_stat
            row = dict(role=role, path=path.relative_to(entry).as_posix(), kind='directory' if directory else 'file',
                mode=info.st_mode, device=info.st_dev, inode=info.st_ino, uid=info.st_uid, gid=info.st_gid,
                mtimeNs=info.st_mtime_ns, ctimeNs=info.st_ctime_ns, attributes=getattr(info, 'st_file_attributes', None),
                security=observed['security'] if held is not None else support.native_security(path=path) if os.name == 'nt' else None,
                bytes=None, sha256=None, links=None)
            if not directory:
                raw = None if held is not None else path.read_bytes()
                row.update(bytes=observed['bytes'] if held is not None else len(raw),
                    sha256=observed['sha256'] if held is not None else sha(raw), links=info.st_nlink)
                after = path.lstat()
                require((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) ==
                        (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'Input changed during inventory')
            rows.append(row)
    validate_rows(rows)
    return rows


def double_inventory(root, support, path, locks=None):
    first = inventory(root, support, locks)
    second = inventory(root, support, locks)
    value = {'schema': 'r0016-entry-full-input-inventory.v1', 'root': str(root),
             'complete': first == second, 'passes': [first, second], 'rows': second}
    save(path, value)
    require(value['complete'], 'Consecutive full input inventories disagree')
    return value


def extract_instrument(core, window, control):
    require(fact(core)['sha256'] == CORE_SHA and fact(window)['sha256'] == WINDOW_SHA, 'Unreviewed guard/window library bytes')
    text = Path(core).read_text(encoding='ascii')
    drivers = re.findall(r"(?m)^\$DriverText=@'\n(.*?)\n'@\s*$", text, re.S)
    helpers = re.findall(r"(?m)^\$EffectHelpers=@\(\n(.*?)\n\)\s*$", text, re.S)
    require(len(drivers) == len(helpers) == 1, 'Ambiguous embedded guard driver/helper inventory')
    target = control / 'original-guard-driver.ps1'
    target.write_bytes(drivers[0].encode('ascii'))
    window_copy = control / 'original-window-support.ps1'
    shutil.copy2(window, window_copy)
    return target, window_copy, re.findall(r"'([^']+)'", helpers[0])


def mapped_environment(env, direct_root, held_root, nonce):
    require(len({key.upper() for key in env}) == len(env), 'Ambiguous environment key')
    result = {}
    prefix = str(direct_root) + os.sep
    for key, value in env.items():
        if key == 'INSTALL_EXPECTED_PID':
            continue  # Parent observation, never a child launch input.
        upper = key.upper()
        if upper in PATH_ENV:
            require(value.startswith(prefix), 'Fixture environment path escaped direct root: ' + key)
            result[key] = str(held_root / value[len(prefix):])
        elif upper == 'PSMODULEPATH':
            entries = value.split(';')
            require(len(entries) == 2 and entries[0] == str(direct_root / 'modules'), 'Ambiguous module input roots')
            result[key] = str(held_root / 'modules') + ';' + entries[1]
        elif upper == 'INSTALL_READY_NONCE':
            result[key] = nonce
        elif upper == 'R0016_INPUT_PHASE':
            result[key] = 'held-module-startup'
        else:
            result[key] = value
    return result


def prepare_pair(root, env, command, host_name, host, native_modules, source, core, window, driver, support, protect):
    require(os.name == 'nt', 'BLOCKED_NATIVE_HOST: fixture preparation requires native Windows')
    require(fact(source)['sha256'] == PREVIEW_SOURCE_SHA, 'Preview relation is pinned to the reviewed complete source')
    root = Path(root).resolve(strict=True)
    paired = root / 'held-leg'
    paired.mkdir()
    for name in ('subject', 'subject/temp', 'host-home'):
        (paired / name).mkdir(parents=True, exist_ok=True)
    protect(paired, host, native_modules, [paired, paired / 'subject', paired / 'subject/temp', paired / 'host-home'])
    control = paired / 'control'
    control.mkdir()
    before = double_inventory(root, support, control / 'direct-prepared.json')
    for relative in ROLE_PATHS.values():
        original, copied = root / relative, paired / relative
        if original.is_dir():
            shutil.copytree(original, copied, dirs_exist_ok=True, copy_function=shutil.copy2)
        elif original.is_file():
            shutil.copy2(original, copied)
    # Parent/child creation changed destination directory mtimes; copytree's
    # final copystat restores those times. Identities/creation times stay explicit.
    copied = double_inventory(paired, support, control / 'held-prepared.json')
    mapping = map_inputs(before['rows'], copied['rows'])
    nonce = secrets.token_hex(16)
    held_env = mapped_environment(env, root, paired, nonce)
    copied_driver = control / 'held-driver.ps1'
    shutil.copy2(driver, copied_driver)
    probe = control / 'input-probe.ps1'
    shutil.copy2(env['R0016_INPUT_PROBE'], probe)
    guard, window_copy, helpers = extract_instrument(core, window, control)
    parameters = direct_parameters(command, host, source)
    require(any(row == {'name': 'DryRun', 'type': 'switch', 'value': True} for row in parameters), 'Held product call requires actual preview argv')
    spec = {'schema': 'r0016-entry-held-spec.v1', 'scenario': root.name, 'expectedHost': host_name,
            'scope': 'product', 'guardMode': 'deny', 'inputProbe': str(probe), 'probeFact': fact(probe),
            'beforeInputProof': str(control / 'held-before-inputs.json'),
            'host': str(host), 'nonce': nonce, 'source': str(source), 'sourceFact': fact(source),
            'driverFact': fact(copied_driver), 'guardSource': str(guard), 'guardFact': fact(guard),
            'windowSupport': str(window_copy), 'windowFact': fact(window_copy), 'effectHelpers': helpers,
            'parameters': parameters, 'events': str(control / 'events.jsonl'), 'result': str(control / 'result.json'),
            'beforeSignal': str(control / 'before.signal'), 'beforeAck': str(control / 'before.ack'),
            'afterSignal': str(control / 'after.signal'), 'afterAck': str(control / 'after.ack')}
    spec_path = control / 'spec.json'
    save(spec_path, spec)
    held_env['R0016_COMPOSITION_SPEC'] = str(spec_path)
    association = {'schema': 'r0016-entry-input-association.v1', 'directRoot': str(root), 'heldRoot': str(paired),
        'source': fact(source), 'directCommand': command, 'heldCommand': [str(host), '-NoProfile', '-File', str(copied_driver)],
        'sourceInventory': support.profile_snapshot(source),
        'parameters': parameters, 'cwd': str(Path.cwd().resolve()),
        'directEnvironment': dict(env), 'heldEnvironment': held_env, 'entries': mapping,
        'scope': 'All six prepared input roles; clone identity/creation facts explicitly mapped, all other fields equal.'}
    save(control / 'association.json', association)
    return {'root': paired, 'control': control, 'env': held_env, 'spec': spec, 'specPath': spec_path,
            'association': association, 'directPrepared': before, 'heldPrepared': copied}


def validate_held(receipt, result, expected):
    require(receipt.get('schema') == 'r0016-entry-held-observation.v1', 'Wrong held observation schema')
    require(receipt.get('command') == expected['command'] and receipt.get('cwd') == expected['cwd'], 'Wrong held command or working directory')
    require(receipt.get('environment') == expected['heldEnvironment'], 'Wrong complete held launch environment')
    require(type(receipt.get('pid')) is int and receipt['pid'] > 0, 'Missing actual held PID')
    require(receipt.get('nonce') == expected['nonce'] and re.fullmatch(r'[0-9a-f]{32}', receipt['nonce']) is not None, 'Wrong held nonce')
    require(type(receipt.get('exit')) is int and receipt['exit'] == 0, 'Wrong wrapper process exit')
    require(receipt.get('exitObserved') is True and receipt.get('timedOut') is False and receipt.get('error') is None, 'Incomplete held process')
    elapsed = receipt.get('elapsedSeconds')
    require(type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed < TIMEOUT and receipt.get('timeoutSeconds') == TIMEOUT, 'Unbounded or late held terminal receipt')
    require(receipt.get('capture') == 'direct files; no redirected pipe drain', 'Unproved capture completion')
    for field in ('sourceFact', 'driverFact', 'guardFact', 'windowFact', 'specFact', 'stdout', 'stderr', 'resultFact', 'eventsFact'):
        require(receipt.get(field) == expected[field], 'Unbound held file fact: ' + field)
    for phase in ('prelaunch', 'before', 'after', 'postexit'):
        observed = receipt.get(phase)
        require(type(observed) is dict and observed.get('complete') is True and len(observed.get('passes', [])) == 2 and observed['passes'][0] == observed['passes'][1] == observed.get('rows'), 'Incomplete held ' + phase + ' inventory')
        require(observed.get('root') == expected['heldRoot'], 'Replayed or wrong full inventory root')
        validate_rows(observed['rows'])
    for phase in ('before', 'after'):
        require(receipt.get(phase + 'Token') == str(receipt['pid']) + '\t' + expected['nonce'] + '\t' + phase + '-invocation', 'Held phase token mismatch')
        require(receipt.get(phase + 'Acknowledged') is True, 'Held phase not acknowledged')
        for kind in ('SignalFact', 'AckFact'):
            require(receipt.get(phase + kind) == expected[phase + kind], 'Unbound phase signal/ack bytes')
    require(receipt['before']['rows'] == receipt['after']['rows'], 'Full held invocation changed owned inputs')
    require(receipt['prelaunch']['rows'] == expected['heldPreparedRows'], 'Prelaunch inputs differ from the prepared clone')
    require(receipt['before']['rows'] == expected['heldPreparedRows'], 'Held source-entry inputs differ from the complete prepared mapping')
    require(result.get('schema') == 'r0016-entry-held-result.v1' and type(result.get('pid')) is int and result['pid'] == receipt['pid'] and result.get('nonce') == expected['nonce'], 'Unbound held result')
    require(result.get('nativeWindows') is True and result.get('expectedHost') == expected['hostName'] and result.get('commandHost') == expected['host'], 'Wrong native host')
    if expected['hostName'] == 'ps51':
        require(result.get('hostEdition') == 'Desktop' and type(result.get('hostVersion')) is str and re.fullmatch(r'5\.1(?:\.\d+){0,2}', result['hostVersion']), 'Wrong Windows PowerShell version')
    else:
        require(expected['hostName'] == 'ps7' and result.get('hostEdition') == 'Core' and result.get('hostVersion') == '7.6.6', 'Wrong native PowerShell version')
    require(result.get('sourceFact') == expected['sourceFact'] and result.get('parameters') == expected['parameters'], 'Wrong source or typed invocation inputs')
    require(result.get('guardEstablished') is True and result.get('preparationError') is None and result.get('events') == [], 'Unproved denial or observed effects')
    require(type(result.get('methodInventory')) is list and bool(result['methodInventory']), 'Missing source breakpoint inventory')


def finish_owned_acquisition(process, locks, root, control, support, receipt, primary_failure, receipt_path=None):
    """Try each owned cleanup step independently; preserve the original failure.

    Only the Popen object and lock objects acquired by this invocation are used.
    A failed kill is never evidence that a process has exited. Final persistence
    is always attempted; an I/O failure cannot guarantee a file can be written.
    """
    cleanup = {'processStarted': process is not None, 'steps': [], 'terminalObserved': False,
               'terminalExit': None, 'receiptWriteAttempted': False}
    receipt['cleanup'] = cleanup
    first_error = None

    def attempt(name, operation):
        nonlocal first_error
        row = {'step': name, 'completed': False, 'error': None}
        cleanup['steps'].append(row)
        try:
            value = operation()
            row['completed'] = True
            return True, value
        except BaseException as error:
            row['error'] = {'type': type(error).__name__, 'message': str(error),
                            'errno': getattr(error, 'errno', None), 'winerror': getattr(error, 'winerror', None)}
            first_error = first_error or error
            return False, None

    if process is not None:
        polled, status = attempt('poll-owned-process', process.poll)
        if not polled or status is None:
            attempt('kill-owned-process', process.kill)
        waited, status = attempt('wait-owned-process', lambda: process.wait(timeout=5))
        if waited and type(status) is int:
            cleanup['terminalObserved'], cleanup['terminalExit'] = True, status
        elif waited:
            attempt('validate-owned-terminal', lambda: require(False, 'Owned process wait returned no integer terminal exit'))
        if not cleanup['terminalObserved']:
            receipt['terminationUnconfirmed'] = True
    if 'postexit' not in receipt:
        name = 'postexit' if cleanup['terminalObserved'] else 'cleanupInventory'
        filename = 'full-after-exit.json' if cleanup['terminalObserved'] else 'termination-unconfirmed-inventory.json'
        observed, value = attempt('observe-owned-state-' + name,
            lambda: double_inventory(root, support, control / filename, locks))
        if observed:
            receipt[name] = value
    # Capture files are direct child handles. Even a failed acquisition must
    # retain their bytes; terminal confirmation is a separate, mandatory fact.
    for stream in ('stdout', 'stderr'):
        capture_path = control / (stream + '.raw')
        if process is not None or capture_path.exists():
            captured, value = attempt('capture-owned-' + stream, lambda path=capture_path: fact(path))
            if captured:
                receipt[stream] = value
    receipt['captureCompletion'] = ('closed-after-observed-exit' if cleanup['terminalObserved']
                                    else 'termination-unconfirmed')
    for index, locked in enumerate(locks.values()):
        restored, value = attempt('restore-owned-lock-' + str(index), locked.restore)
        if restored:
            name = 'unreadable-restoration.json' if index == 0 else 'unreadable-restoration-' + str(index) + '.json'
            attempt('save-owned-restoration-' + str(index), lambda name=name, value=value: save(control / name, value))
        else:
            attempt('close-owned-lock-' + str(index), locked.close_after_failure)
    if primary_failure is None and first_error is not None:
        receipt['error'] = type(first_error).__name__ + ': ' + str(first_error)
    cleanup['receiptWriteAttempted'] = True
    try:
        save(receipt_path or control / 'held-observation.json', receipt)
    except BaseException as error:
        cleanup['receiptWriteError'] = {'type': type(error).__name__, 'message': str(error)}
        first_error = first_error or error
    failure = primary_failure or first_error
    if failure is not None:
        try:
            failure.r0016_cleanup_receipt = receipt
        except BaseException:
            pass  # Preserve the original failure even if it cannot take metadata.
    return first_error


def invoke_pair(pair, support):
    """Observe exact NEW driver with full snapshots. Native execution is caller-owned."""
    require(os.name == 'nt', 'BLOCKED_NATIVE_HOST: held acquisition requires native Windows')
    root, control, env, spec = pair['root'], pair['control'], pair['env'], pair['spec']
    association = pair['association']
    expected_environment = mapped_environment(association['directEnvironment'], Path(association['directRoot']), root, spec['nonce'])
    expected_environment['R0016_COMPOSITION_SPEC'] = str(pair['specPath'])
    require(env == association['heldEnvironment'] == expected_environment, 'Launch environment differs from exhaustive mapping')
    require(direct_parameters(association['directCommand'], spec['host'], spec['source']) == spec['parameters'] == association['parameters'], 'Typed invocation differs from actual direct argv')
    require(support.profile_snapshot(spec['source']) == association['sourceInventory'], 'Source metadata changed before held launch')
    locks = {}
    receipt = {'schema': 'r0016-entry-held-observation.v1', 'command': association['heldCommand'],
        'cwd': association['cwd'], 'nonce': spec['nonce'], 'timeoutSeconds': TIMEOUT,
        'environment': dict(env),
        'capture': 'direct files; no redirected pipe drain', 'exitObserved': False,
        'timedOut': False, 'error': None, 'exit': None, 'before': None, 'after': None}
    started, process, failure = time.monotonic(), None, None
    try:
        if spec['scenario'].endswith('-unreadable'):
            locked = support.NativeReadLock(env['INSTALL_UNREADABLE_FILE'], root)
            locks[os.path.normcase(str(locked.path))] = locked
            save(control / 'unreadable-held-before.json', locked.initial)
        receipt['prelaunch'] = double_inventory(root, support, control / 'full-before-launch.json', locks)
        require(receipt['prelaunch']['rows'] == pair['heldPrepared']['rows'], 'Prepared held inputs changed before launch')
        for field in ('sourceFact', 'driverFact', 'guardFact', 'windowFact', 'probeFact'):
            require(fact(spec[field]['path']) == spec[field], 'Instrument/source changed before launch')
            receipt[field] = spec[field]
        receipt['specFact'] = fact(pair['specPath'])
        out, err = control / 'stdout.raw', control / 'stderr.raw'
        with out.open('wb') as stdout, err.open('wb') as stderr:
            process = subprocess.Popen(association['heldCommand'], cwd=association['cwd'], env=env,
                stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr)
            receipt['pid'] = process.pid
            while True:
                elapsed = time.monotonic() - started
                if elapsed >= TIMEOUT:
                    receipt['timedOut'] = True
                    raise TimeoutError('Child or first terminal observation exceeded 60 seconds')
                terminal = process.poll()
                if terminal is not None:
                    receipt.update(exit=terminal, exitObserved=True, elapsedSeconds=elapsed)
                    break
                # Original Utility module startup has a distinct late-ready gate;
                # accepting it never establishes the source invocation boundary.
                ready = Path(env['INSTALL_READY_FILE'])
                ack = Path(env['INSTALL_PROFILE_ACK'])
                token = str(process.pid) + '\t' + env['INSTALL_READY_NONCE']
                if ready.exists() and not ack.exists():
                    require(ready.read_text(encoding='utf-8-sig') == token, 'Original ready PID/nonce mismatch')
                    ready_clock = time.monotonic()
                    receipt['originalReady'] = double_inventory(root, support, control / 'full-at-original-ready.json', locks)
                    require(process.poll() is None and time.monotonic() - started < TIMEOUT
                            and time.monotonic() - ready_clock < 10, 'Original Utility ready observation exceeded its ACK deadline')
                    ack.write_text(token, encoding='utf-8')
                    receipt['originalReadyToken'] = token
                    receipt['originalReadyFact'], receipt['originalAckFact'] = fact(ready), fact(ack)
                    receipt['originalReadyAcknowledged'] = True
                phase = 'before' if receipt['before'] is None else 'after'
                signal = Path(spec[phase + 'Signal'])
                if receipt[phase] is None and signal.exists():
                    token = str(process.pid) + '\t' + spec['nonce'] + '\t' + phase + '-invocation'
                    require(signal.read_text(encoding='utf-8-sig') == token, 'Held phase PID/nonce mismatch')
                    gate_clock = time.monotonic()
                    receipt[phase] = double_inventory(root, support, control / (phase + '-invocation.json'), locks)
                    require(process.poll() is None and time.monotonic() - started < TIMEOUT and time.monotonic() - gate_clock < ACK_TIMEOUT, 'Child exited or held observation exceeded deadline')
                    ack_path = Path(spec[phase + 'Ack'])
                    temporary = ack_path.with_name(ack_path.name + '.partial')
                    temporary.write_text(token, encoding='utf-8')
                    temporary.replace(ack_path)
                    receipt[phase + 'Token'] = token
                    receipt[phase + 'Acknowledged'] = True
                    receipt[phase + 'SignalFact'] = fact(signal)
                    receipt[phase + 'AckFact'] = fact(ack_path)
                time.sleep(0.02)
        receipt['stdout'], receipt['stderr'] = fact(out), fact(err)
        receipt['postexit'] = double_inventory(root, support, control / 'full-after-exit.json', locks)
        receipt['eventsFact'] = fact(spec['events'])
        if spec['scope'] == 'source-free-diagnostic' and not Path(spec['result']).exists():
            # A causal debugger Stop may end a denied-effect child before the
            # semantic writer runs. Only the separate denied-control receiver
            # can interpret this absence; every healthy result requires it.
            receipt['resultFact'], receipt['resultMissing'] = None, True
            result = None
        else:
            receipt['resultFact'] = fact(spec['result'])
            result = complete_json(Path(spec['result']).read_bytes())
        if spec['scope'] != 'source-free-diagnostic':
            require(Path(spec['events']).read_bytes() == b'', 'Raw effects log is nonempty')
        if 'INSTALL_UNREADABLE_FILE' in env:
            proof_path = Path(env['INSTALL_UNREADABLE_PROOF'])
            proof = complete_json(proof_path.read_bytes())
            require(type(proof.get('pid')) is int and proof['pid'] == process.pid and proof.get('nonce') == spec['nonce'] and proof.get('path') == env['INSTALL_UNREADABLE_FILE'], 'Held metadata proof has wrong PID/nonce/path')
            require(proof.get('exists') is True and proof.get('peerReadable') is True and proof.get('peerSha256') == env['INSTALL_METADATA_SHA'], 'Held metadata existence/readable peer control failed')
            if locks:
                require(proof.get('readSucceeded') is False and proof.get('nativeCode') == 32 and proof.get('exceptionType') == 'System.IO.IOException', 'Held child did not prove native read refusal')
            else:
                require(proof.get('readSucceeded') is True and proof.get('nativeCode') is None and proof.get('targetSha256') == env['INSTALL_METADATA_SHA'], 'Held readable counterpart failed')
            receipt['metadataProof'], receipt['metadataProofFact'] = proof, fact(proof_path)
        expected = dict(receipt, command=association['heldCommand'], cwd=association['cwd'], nonce=spec['nonce'],
            hostName=spec['expectedHost'], host=spec['host'], parameters=spec['parameters'], heldEnvironment=expected_environment, heldRoot=str(root), heldPreparedRows=pair['heldPrepared']['rows'])
        # Expected facts above come from actual closed capture files and frozen
        # prelaunch inputs, not from self-declared report values.
        for field in ('sourceFact', 'driverFact', 'guardFact', 'windowFact', 'probeFact'):
            require(fact(spec[field]['path']) == spec[field], 'Instrument/source changed while child ran')
        require(fact(pair['specPath']) == receipt['specFact'], 'Invocation spec changed while child ran')
        require(support.profile_snapshot(spec['source']) == association['sourceInventory'], 'Source metadata changed while child ran')
        if spec['scope'] != 'source-free-diagnostic':
            validate_held(receipt, result, expected)
        return {'observation': receipt, 'result': result, 'association': association}
    except BaseException as error:
        failure = error
        receipt['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        cleanup_error = finish_owned_acquisition(process, locks, root, control, support, receipt, failure)
        if cleanup_error is not None and failure is None:
            raise cleanup_error


def require_positive_confinement(observation, support):
    require(observation.get('normalConfinementValidated') is True, 'Normal/NoOpen confinement is mandatory')
    require(type(observation.get('normalConfinement')) is dict and observation['normalConfinement'].get('expectedRetainedPaths'), 'Normal retained inventory proof is missing')
    require(type(observation.get('entryExit')) is int and observation['entryExit'] == 0, 'Normal direct exit is not integer zero')
    window = observation.get('profileWindow')
    require(type(window) is dict and type(window.get('before')) is list and type(window.get('after')) is list, 'Missing full normal profile snapshots')
    confinement = observation['normalConfinement']
    retained = confinement.get('retainedRelative')
    require(type(retained) is str and retained.startswith('SalahWidgetBundle-') and '/' not in retained and '\\' not in retained, 'Missing or invalid actual normal bundle name')
    expected_paths = confinement['expectedRetainedPaths']
    require(type(expected_paths) is list and len(expected_paths) == 8 and all(type(path) is str for path in expected_paths) and len(set(expected_paths)) == 8, 'Incomplete original eight-entry normal inventory')
    require(retained in expected_paths and retained + '/downloads' in expected_paths and retained + '/presets' in expected_paths, 'Missing normal bundle structure')
    support.assert_profile_window(window['before'], window['after'], confinement.get('retainedRelative'), confinement['expectedRetainedPaths'])
