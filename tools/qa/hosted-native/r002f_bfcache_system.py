#!/usr/bin/env python3
"""Explicit official-Ubuntu system dependencies inside the selected tool ceiling.

The caller owns the existing 180-second aggregate timer. No browser is launched;
package success never replaces the original decoder/ELF/mapping capability gate.
"""
import hashlib
import math
import os
from pathlib import Path
import re
import shlex
import tempfile
import time

import r002f_bfcache_tools as tools
import runner_environment as runner
import r002f_bfcache_privileged as privileged

PROTOCOL = 'r002f-bfcache-system-provision/1'
INSTALL_PACKAGES = ('ffmpeg', 'xvfb', 'binutils', 'libc-bin', 'dpkg', 'iproute2', 'util-linux')
BOOTSTRAP_PACKAGES = ('sudo', 'openssl', 'git', 'bash', 'coreutils', 'apt', 'gpgv', 'ubuntu-keyring', 'ca-certificates')
PACKAGES = INSTALL_PACKAGES + BOOTSTRAP_PACKAGES
ENV = {**tools.ENV, 'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'DEBIAN_FRONTEND': 'noninteractive',
       'APT_LISTCHANGES_FRONTEND': 'none', 'NEEDRESTART_MODE': 'l'}
KEYRING = '/usr/share/keyrings/ubuntu-archive-keyring.gpg'
BOOTSTRAP = {'sudo': '/usr/bin/sudo', 'env': '/usr/bin/env', 'aptGet': '/usr/bin/apt-get',
             'aptCache': '/usr/bin/apt-cache', 'aptConfig': '/usr/bin/apt-config', 'gpgv': '/usr/bin/gpgv', 'git': '/usr/bin/git',
             'bash': '/bin/bash', 'openssl': '/usr/bin/openssl', 'archiveKeyring': KEYRING,
             'caCertificates': '/etc/ssl/certs/ca-certificates.crt', 'timeout': '/usr/bin/timeout',
             'unshare': '/usr/bin/unshare', 'systemPython': '/usr/bin/python3'}
REQUIRED = {**BOOTSTRAP, 'decoder': '/usr/bin/ffmpeg', 'probe': '/usr/bin/ffprobe',
            'xvfb': '/usr/bin/Xvfb', 'dpkg': '/usr/bin/dpkg', 'dpkgQuery': '/usr/bin/dpkg-query',
            'ldd': '/usr/bin/ldd', 'readelf': '/usr/bin/readelf', 'ip': '/usr/sbin/ip',
            'unshare': '/usr/bin/unshare', 'setpriv': '/usr/bin/setpriv'}
PACKAGE_FORMAT = '${Package}\t${Status}\t${Version}\t${Architecture}\n'
SOURCES = ''.join('deb [arch=amd64 signed-by=' + KEYRING + '] https://' + host + '/ubuntu ' + suite + ' main universe\n'
                  for host, suite in (('archive.ubuntu.com', 'noble'), ('archive.ubuntu.com', 'noble-updates'),
                                      ('security.ubuntu.com', 'noble-security')))
RELEASES = {'archive.ubuntu.com_ubuntu_dists_noble_InRelease',
            'archive.ubuntu.com_ubuntu_dists_noble-updates_InRelease',
            'security.ubuntu.com_ubuntu_dists_noble-security_InRelease'}
LIMITS = {'apt-effective-config': 5, 'apt-update': 60, 'decoder-policy': 5, 'decoder-madison': 5,
          'apt-install': 60, 'system-packages': 5, 'decoder-package-verify': 5}
need = tools.need


def write_bytes(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        need(os.write(fd, raw) == len(raw), 'partial dependency metadata write')
        os.fsync(fd)
    finally: os.close(fd)
    record = tools.file_record(path)
    need(record['bytes'] == len(raw) and record['sha256'] == hashlib.sha256(raw).hexdigest(),
         'actual dependency metadata bytes differ')
    return record


def apt_settings(work, source=None):
    work = Path(work); source = work / 'sources.list' if source is None else Path(source)
    return [('Dir::Etc::sourcelist', str(source)), ('Dir::Etc::sourceparts', str(work / 'empty.conf.d')),
             ('Dir::Etc::main', str(work / 'empty.conf')), ('Dir::Etc::parts', str(work / 'empty.conf.d')),
             ('Dir::Etc::preferences', str(work / 'empty.conf')), ('Dir::Etc::preferencesparts', str(work / 'empty.conf.d')),
             ('Dir::Etc::netrc', str(work / 'empty.conf')), ('Dir::Etc::netrcparts', str(work / 'empty.conf.d')),
             ('Dir::State::lists', str(work / 'lists')),
             ('Dir::Cache', str(work / 'cache')), ('Dir::Cache::archives', str(work / 'cache/archives')),
             ('Dir::State::status', '/var/lib/dpkg/status'), ('Acquire::Languages', 'none'),
             ('Acquire::Retries', '0'), ('Acquire::http::Timeout', '20'), ('Acquire::https::Timeout', '20'),
             ('DPkg::Lock::Timeout', '0'), ('APT::Update::Error-Mode', 'any'), ('APT::Get::List-Cleanup', '0'),
             ('APT::Sandbox::User', '_apt'), ('APT::Get::AllowUnauthenticated', 'false'),
             ('Acquire::AllowInsecureRepositories', 'false'), ('Acquire::AllowDowngradeToInsecureRepositories', 'false'),
             ('Acquire::Check-Valid-Until', 'true')]


def apt_options(work, source=None):
    return [part for key, value in apt_settings(work, source) for part in ('-o', key + '=' + value)]


def config_text(work):
    # APT_CONFIG is read before fragments and the main configuration. Command
    # line Dir::Etc overrides alone are too late to suppress already loaded hooks.
    work = Path(work)
    need(work.parent == Path('/tmp') and re.fullmatch(r'salah-bfcache-apt-[A-Za-z0-9_-]{8,64}', work.name),
         'literal generated package configuration path required')
    return ''.join(key + ' "' + value + '";\n' for key, value in apt_settings(work))


def command_environment(work):
    return {**ENV, 'APT_CONFIG': str(Path(work) / 'apt.conf')}


def admit_effective_config(text, work):
    rows = {}; languages = []
    for line in text.splitlines():
        need(line.endswith(';'), 'actual APT effective configuration syntax differs')
        parts = shlex.split(line[:-1]); need(len(parts) == 2, 'actual APT effective configuration row differs')
        key, value = parts
        need(not re.search(r'(?:pre|post)-invoke|pre-install-pkgs', key, re.IGNORECASE), 'host APT/dpkg hook survived private configuration')
        need(not key.lower().startswith(('binary::apt-get::', 'binary::apt-cache::', 'binary::apt-config::')),
             'binary-specific APT override is outside the explicit configuration')
        if key == 'Acquire::Languages::': languages.append(value)
        if key in dict(apt_settings(work)):
            need(key not in rows, 'ambiguous effective APT configuration'); rows[key] = value
    if rows.get('Acquire::Languages') == '' and languages == ['none']: rows['Acquire::Languages'] = 'none'
    else: need(not languages, 'unexpected translated package index population')
    need(rows == dict(apt_settings(work)), 'actual private APT authentication/sandbox/source configuration differs')
    return True


def workspace_current(work, owner):
    work = Path(work)
    need(work.is_absolute() and work.parent == Path('/tmp') and re.fullmatch(r'salah-bfcache-apt-[A-Za-z0-9_-]{8,64}', work.name)
         and work.resolve() == work and not any(path.is_symlink() for path in (work, *work.parents)),
         'bound public package workspace differs')
    for path in (work, work / 'lists', work / 'cache', work / 'cache/archives'):
        need(path.is_dir() and not path.is_symlink() and path.stat().st_uid == owner
             and path.stat().st_mode & 0o777 == 0o755, 'public package traversal/ownership differs')
    need(all(path.stat().st_mode & 0o001 for path in work.parents), 'package sandbox cannot traverse workspace ancestors')
    parts = work / 'empty.conf.d'
    need(parts.is_dir() and not parts.is_symlink() and parts.stat().st_uid == owner
         and parts.stat().st_mode & 0o777 == 0o555 and not list(parts.iterdir()), 'private empty APT fragment/source directory changed')
    for name, text in (('sources.list', SOURCES), ('apt.conf', config_text(work)), ('empty.conf', '')):
        row = tools.file_record(work / name)
        need(row['uid'] == owner and row['mode'] == 0o644 and (work / name).read_text() == text, 'public immutable APT configuration differs')
        tools.require_record(row)
    return True


def create_workspace(folder):
    folder = Path(folder); work = Path(tempfile.mkdtemp(prefix='salah-bfcache-apt-', dir='/tmp')); work.chmod(0o755)
    for name in ('lists', 'lists/partial', 'cache', 'cache/archives', 'cache/archives/partial', 'empty.conf.d'):
        (work / name).mkdir(mode=0o755)
        (work / name).chmod(0o700 if name.endswith('/partial') else 0o555 if name == 'empty.conf.d' else 0o755)
    retained = {}
    for name, text in (('sources.list', SOURCES), ('apt.conf', config_text(work)), ('empty.conf', '')):
        write_bytes(work / name, text.encode()); (work / name).chmod(0o644)
        retained[name] = {'actual': tools.file_record(work / name),
                          'retained': write_bytes(folder / ('apt-' + name), text.encode())}
    workspace_current(work, os.getuid())
    return work, retained


def command(label, work, source, version=None):
    options = apt_options(work, source)
    package = ['/usr/bin/apt-get', *options]
    if label == 'apt-effective-config': return ['/usr/bin/apt-config', *options, 'dump']
    if label == 'apt-update': return package + ['update']
    if label == 'decoder-policy': return ['/usr/bin/apt-cache', *options, 'policy', 'ffmpeg']
    if label == 'decoder-madison': return ['/usr/bin/apt-cache', *options, 'madison', 'ffmpeg']
    if label == 'apt-install':
        need(type(version) is str and re.fullmatch(r'[0-9A-Za-z.+:~_-]+', version), 'exact official decoder version absent')
        return package + ['install', '--yes', '--no-install-recommends', '--reinstall',
                             'ffmpeg=' + version, *INSTALL_PACKAGES[1:]]
    if label == 'system-packages': return ['/usr/bin/dpkg-query', '-W', '-f=' + PACKAGE_FORMAT, *PACKAGES]
    if label == 'decoder-package-verify': return ['/usr/bin/dpkg', '--verify', 'ffmpeg']
    raise ValueError('unknown acquisition command')


def decoder_candidate(policy, madison):
    candidates = re.findall(r'^\s*Candidate:\s*(\S+)\s*$', policy, re.MULTILINE)
    need(len(candidates) == 1 and re.fullmatch(r'[0-9A-Za-z.+:~_-]+', candidates[0]), 'one actual decoder candidate required')
    candidate = candidates[0]
    major = re.match(r'^(?:[0-9]+:)?([0-9]+)\.', candidate)
    need(major is not None and int(major.group(1)) >= 5, 'official decoder candidate predates original fps_mode option')
    versions = set()
    for line in madison.splitlines():
        if not line.strip(): continue
        parts = [part.strip() for part in line.split('|')]
        need(len(parts) == 3 and parts[0] == 'ffmpeg' and re.fullmatch(r'[0-9A-Za-z.+:~_-]+', parts[1]),
             'unrecognized decoder package population')
        need(re.fullmatch(r'https://(?:archive\.ubuntu\.com/ubuntu noble(?:-updates)?|security\.ubuntu\.com/ubuntu noble-security)/(?:main|universe) amd64 Packages', parts[2]),
             'decoder candidate is not from the declared official Noble archive')
        versions.add(parts[1])
    need(candidate in versions, 'selected installed/candidate version has no official archive row')
    return candidate


def records(literals):
    result = {name: tools.file_record(literal, system=True) for name, literal in literals.items()}
    need(all(row['uid'] == 0 and not row['mode'] & 0o022 and (name in ('archiveKeyring', 'caCertificates') or row['mode'] & 0o111)
             for name, row in result.items()), 'root-owned system executable/keyring identity differs')
    return result


def process_current(value, argv, folder, limit, environment):
    need(type(value) is dict and value.get('argv') == argv and value.get('cwd') == str(folder)
         and value.get('environment') == environment and value.get('complete') is True
         and type(value.get('returncode')) is int and value['returncode'] == 0
         and value.get('timedOut') is False and value.get('overflow') is False and value.get('groupStopped') is True
         and type(value.get('pid')) is int and value['pid'] > 0 and not value.get('error'),
         'actual dependency command did not complete')
    timeout = value.get('timeoutSeconds'); elapsed = value.get('elapsedSeconds')
    need(type(timeout) in (float, int) and math.isfinite(timeout) and 0 < timeout <= limit
         and type(elapsed) in (float, int) and math.isfinite(elapsed) and 0 <= elapsed <= timeout,
         'actual dependency command bound differs')
    for key in ('stdout', 'stderr'):
        row = value['streams'][key]; tools.require_record(row)
        need(row['path'] == str(folder / (value['label'] + '.' + key))
             and all(type(value[field][key]) is int for field in ('observedBytes', 'retainedBytes', 'maxBytes'))
             and value['observedBytes'][key] == value['retainedBytes'][key] == row['bytes']
             and 0 <= row['bytes'] <= value['maxBytes'][key] == 4 * 1024 * 1024,
             'dependency stream byte accounting differs')
    if value['label'] in privileged.LABELS:
        body = privileged.admit(value.get('privilegedController', {}), argv, folder, value['label'])
        actual = {key: item for key, item in value.items() if key not in ('label', 'environment', 'privilegedController')}
        need(actual == body['command'], 'integrated and root command receipts differ')


def installed_rows(text, version):
    rows = [line.split('\t') for line in text.splitlines()]
    need(len(rows) == len(PACKAGES) and {row[0] for row in rows if len(row) == 4} == set(PACKAGES)
         and all(len(row) == 4 and row[1] == 'install ok installed' and row[2] and row[3] in ('amd64', 'all') for row in rows),
         'complete installed system package population differs')
    need(next(row[2] for row in rows if row[0] == 'ffmpeg') == version, 'installed decoder differs from official selected version')
    return rows


def provision(task, folder, deadline, *, execute=None):
    task = Path(task); folder = Path(folder)
    work = None; source = None; environment = None
    result = {'protocol': PROTOCOL, 'status': 'INCOMPLETE', 'scope': 'SELECTED_ROUTE_OFFICIAL_UBUNTU_DEPENDENCIES',
              'nativeObservation': False, 'task': str(task), 'commands': [],
              'aggregateTimerOwnedByCallerSeconds': 180, 'retries': 0, 'fallbackDecoder': False}
    began = time.monotonic()
    def run(label, version=None):
        remaining = deadline - time.monotonic(); need(remaining > 0, 'selected tool ceiling reached before dependency command')
        seconds = min(LIMITS[label], remaining); argv = command(label, work, source, version)
        row = {'label': label, 'argv': argv, 'cwd': str(folder), 'timeoutSeconds': seconds,
               'environment': dict(environment), 'complete': False, 'returncode': None}
        result['commands'].append(row)
        try:
            kwargs = {'max_stdout': 4 * 1024 * 1024, 'max_stderr': 4 * 1024 * 1024, 'env': dict(environment), 'cwd': folder}
            if execute is not None: actual = execute(argv, folder, label, seconds, **kwargs)
            elif label in privileged.LABELS: actual = privileged.execute(argv, folder, label, seconds, work=work, version=version, **kwargs)
            else: actual = tools.run_bounded(argv, folder, label, seconds, **kwargs)
            row.update(actual)
        except Exception as error:
            row['error'] = type(error).__name__ + ': ' + str(error)
            row['streams'] = {key: tools.file_record(folder / (label + '.' + key)) for key in ('stdout', 'stderr')
                              if (folder / (label + '.' + key)).is_file()}
            raise
        process_current(row, argv, folder, LIMITS[label], environment)
        need(not any(b'unsandboxed as root' in Path(row['streams'][key]['path']).read_bytes().lower() for key in ('stdout', 'stderr')),
             'APT abandoned its nonroot downloader sandbox')
        return Path(row['streams']['stdout']['path']).read_text()
    try:
        result['runner'] = runner.current(task)
        need(result['runner']['selection']['scope'] == 'R002F_BFCACHE_UBUNTU24_DIAGNOSTIC'
             and result['runner']['selection']['runner'] == 'ubuntu-24.04', 'system provision requires exact BFCache Ubuntu24 admission')
        need(os.getuid() > 0, 'original nonroot hosted worker required')
        # util-linux is deliberately reinstalled below; unshare's old inode is
        # historical launcher input, not a falsely current post-install record.
        result['bootstrapBefore'] = {'scope': 'HISTORICAL_PRE_PROVISION_SYSTEM_FILES',
            'receipt': tools.save(folder / 'bootstrap-before.json', records(BOOTSTRAP))}
        work, result['configuration'] = create_workspace(folder)
        result['work'] = str(work); source = work / 'sources.list'; environment = command_environment(work)
        result['effectiveConfig'] = run('apt-effective-config'); admit_effective_config(result['effectiveConfig'], work)
        run('apt-update')
        release_folder = folder / 'official-release'; release_folder.mkdir(mode=0o700)
        found = {path.name for path in (work / 'lists').iterdir() if path.name.endswith('_InRelease')}
        need(found == RELEASES, 'complete authenticated official release population differs')
        result['officialReleases'] = {}
        for name in sorted(RELEASES):
            original = tools.file_record(work / 'lists' / name, limit=2 * 1024 * 1024)
            copied = write_bytes(release_folder / name, Path(original['path']).read_bytes())
            tools.require_record(original)
            need(copied['sha256'] == original['sha256'], 'official release retention differs')
            result['officialReleases'][name] = {'original': original, 'retained': copied}
        policy = run('decoder-policy'); madison = run('decoder-madison')
        result['decoderVersion'] = decoder_candidate(policy, madison)
        run('apt-install', result['decoderVersion'])
        result['installedPackages'] = installed_rows(run('system-packages'), result['decoderVersion'])
        need(run('decoder-package-verify') == '', 'official decoder installed bytes failed package verification')
        result['requiredFiles'] = records(REQUIRED)
        result['bootstrap'] = records(BOOTSTRAP)
        result['packageStatus'] = tools.file_record('/var/lib/dpkg/status', system=True, limit=64 * 1024 * 1024)
        result['decoderPackageFiles'] = tools.file_record('/var/lib/dpkg/info/ffmpeg.md5sums', system=True, limit=1024 * 1024)
        tools.current_records(result)
        need(runner.current(task) == result['runner'], 'runner/source changed during dependency provision')
        result['status'] = 'COMPLETE'
    except Exception as error: result['error'] = type(error).__name__ + ': ' + str(error)
    result['elapsedSeconds'] = time.monotonic() - began
    tools.save(folder / 'system-provision.json', result)
    return result


def current(value, task, folder):
    """Re-admit every actual provision command before any native preparation."""
    task = Path(task); folder = Path(folder); work = Path(value.get('work', '/missing')); source = work / 'sources.list'
    need(value.get('protocol') == PROTOCOL and value.get('status') == 'COMPLETE'
         and value.get('scope') == 'SELECTED_ROUTE_OFFICIAL_UBUNTU_DEPENDENCIES'
         and value.get('nativeObservation') is False and value.get('task') == str(task)
         and value.get('aggregateTimerOwnedByCallerSeconds') == 180 and value.get('retries') == 0
         and value.get('fallbackDecoder') is False and not value.get('error'), 'selected system provision incomplete')
    need(type(value.get('elapsedSeconds')) in (int, float) and math.isfinite(value['elapsedSeconds'])
         and 0 <= value['elapsedSeconds'] <= 180, 'actual system acquisition aggregate exceeded original ceiling')
    need(value.get('bootstrapBefore', {}).get('scope') == 'HISTORICAL_PRE_PROVISION_SYSTEM_FILES'
         and value['bootstrapBefore']['receipt']['path'] == str(folder / 'bootstrap-before.json'),
         'historical bootstrap snapshot is missing or rebound')
    need(value['runner'] == runner.current(task), 'current selected runner differs from system provision')
    workspace_current(work, os.getuid())
    need(set(value['configuration']) == {'sources.list', 'apt.conf', 'empty.conf'}, 'complete APT configuration population missing')
    for name, pair in value['configuration'].items():
        need(pair['actual']['path'] == str(work / name) and pair['retained']['path'] == str(folder / ('apt-' + name))
             and pair['actual']['sha256'] == pair['retained']['sha256'], 'actual and retained APT configuration differ')
    rows = value['commands']; need([row.get('label') for row in rows] == list(LIMITS), 'actual dependency command population/order differs')
    outputs = {}
    for row in rows:
        label = row['label']; process_current(row, command(label, work, source, value['decoderVersion']), folder, LIMITS[label], command_environment(work))
        outputs[label] = Path(row['streams']['stdout']['path']).read_text()
        need(not any(b'unsandboxed as root' in Path(row['streams'][key]['path']).read_bytes().lower() for key in ('stdout', 'stderr')),
             'APT downloader sandbox failure retained')
    need(outputs['apt-effective-config'] == value['effectiveConfig'], 'effective APT configuration record differs')
    admit_effective_config(value['effectiveConfig'], work)
    need(decoder_candidate(outputs['decoder-policy'], outputs['decoder-madison']) == value['decoderVersion']
         and installed_rows(outputs['system-packages'], value['decoderVersion']) == value['installedPackages']
         and outputs['decoder-package-verify'] == '', 'actual package selection/status/verification differs')
    need(set(value['officialReleases']) == RELEASES and value['requiredFiles'] == records(REQUIRED)
         and value['bootstrap'] == records(BOOTSTRAP), 'complete current system dependency population differs')
    for name, row in value['officialReleases'].items():
        need(row['original']['path'] == str(work / 'lists' / name)
             and row['retained']['path'] == str(folder / 'official-release' / name)
             and row['original']['sha256'] == row['retained']['sha256'], 'official release custody differs')
    tools.current_records(value)
    receipt = tools.load(folder / 'system-provision.json')
    need(receipt == value, 'standalone and integrated system receipts differ')
    return {'receipt': tools.file_record(folder / 'system-provision.json'), 'decoderVersion': value['decoderVersion']}
