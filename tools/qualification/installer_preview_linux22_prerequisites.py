#!/usr/bin/env python3
"""Acquire required containment from signed official Ubuntu repositories.

Preparation runs on the disposable hosted runner before measured installer
fixtures. It never changes APT source configuration or relaxes containment.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from urllib.parse import urlsplit
import re


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(mode=0o755, parents=False, exist_ok=False)
    facts = {'schema': 'r0016-linux-prerequisites.v1', 'scope':
             'Disposable runner preparation before installer observation; no product acceptance',
             'host': platform.platform(), 'commands': [], 'complete': False}

    def record():
        (root / 'result.json').write_text(json.dumps(facts, indent=2) + '\n')

    def command(name, argv, seconds=120):
        row = {'name': name, 'command': argv, 'timeoutSeconds': seconds}
        facts['commands'].append(row)
        record()
        start = time.monotonic()
        with (root / (name + '.stdout.txt')).open('wb') as out, (root / (name + '.stderr.txt')).open('wb') as err:
            try:
                result = subprocess.run(argv, stdout=out, stderr=err, timeout=seconds)
                row.update(exit=result.returncode, timedOut=False)
            except subprocess.TimeoutExpired:
                row.update(exit=None, timedOut=True, cleanup='Outer process ended; privileged command completion unverified. No retry authorized by this receipt.')
        row['elapsedSeconds'] = time.monotonic() - start
        row['captureSha256'] = {kind: digest(root / (name + '.' + kind + '.txt')) for kind in ('stdout', 'stderr')}
        record()
        if row['timedOut'] or row['exit'] != 0:
            raise RuntimeError('Runner prerequisite command failed: ' + name)

    try:
        if platform.system() != 'Linux':
            raise RuntimeError('Native Linux required')
        release = dict(line.split('=', 1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
        facts['osRelease'] = {key: value.strip('"') for key, value in release.items()}
        if facts['osRelease'].get('ID') != 'ubuntu' or facts['osRelease'].get('VERSION_CODENAME') != 'jammy':
            raise RuntimeError('This prerequisite acquisition is scoped to Ubuntu 22.04 jammy')
        if platform.machine() != 'x86_64':
            raise RuntimeError('This signed repository route is scoped to amd64')
        keyring = Path('/usr/share/keyrings/ubuntu-archive-keyring.gpg')
        if not keyring.is_file():
            raise RuntimeError('Ubuntu archive keyring absent')
        facts['archiveKeyring'] = {'path': str(keyring), 'sha256': digest(keyring)}
        paths = [Path('/etc/apt/sources.list')]
        paths += sorted(Path('/etc/apt/sources.list.d').glob('*.list'))
        paths += sorted(Path('/etc/apt/sources.list.d').glob('*.sources'))
        facts['originalSourceIdentities'] = [
            {'path': str(path), 'sha256': digest(path),
             'hosts': sorted({urlsplit(uri).hostname for uri in re.findall(r'https?://[^\s]+', path.read_text()) if urlsplit(uri).hostname})}
            for path in paths if path.is_file()]
        facts['beforeTools'] = {name: shutil.which(name) for name in ('bwrap', 'unshare')}
        source = root / 'official-ubuntu.sources'
        source.write_text(
            'Types: deb\nURIs: https://archive.ubuntu.com/ubuntu\nSuites: jammy jammy-updates\n'
            'Components: main universe\nArchitectures: amd64\nSigned-By: ' + str(keyring) + '\n\n'
            'Types: deb\nURIs: https://security.ubuntu.com/ubuntu\nSuites: jammy-security\n'
            'Components: main universe\nArchitectures: amd64\nSigned-By: ' + str(keyring) + '\n')
        facts['selectedSources'] = {'path': str(source), 'sha256': digest(source)}
        lists, cache = root / 'apt-lists', root / 'apt-cache'
        lists.mkdir(mode=0o755)
        (lists / 'partial').mkdir(mode=0o755)
        (cache / 'archives' / 'partial').mkdir(mode=0o755, parents=True)
        empty = root / 'empty-config-parts'
        empty.mkdir(mode=0o755)
        config = root / 'apt-isolated.conf'
        bindings = {
            'Dir::Etc::main': '/dev/null', 'Dir::Etc::parts': str(empty),
            'Dir::Etc::sourcelist': str(source), 'Dir::Etc::sourceparts': str(empty),
            'Dir::Etc::Trusted': '/dev/null', 'Dir::Etc::TrustedParts': str(empty),
            'Dir::State::lists': str(lists), 'Dir::Cache': str(cache),
            'APT::Update::Error-Mode': 'any', 'Acquire::Retries': '0',
            'Acquire::https::Timeout': '25', 'Acquire::https::Verify-Peer': 'true',
            'Acquire::https::Verify-Host': 'true', 'Acquire::Check-Valid-Until': 'true',
            'Acquire::AllowInsecureRepositories': 'false',
            'Acquire::AllowDowngradeToInsecureRepositories': 'false',
            'APT::Get::AllowUnauthenticated': 'false',
        }
        if any(any(c in value for c in ('\n', '\r', '"', '\\')) for value in bindings.values()):
            raise RuntimeError('Unrepresentable APT configuration path')
        config.write_text(''.join(key + ' "' + value + '";\n' for key, value in bindings.items()))
        facts['earlyAptConfig'] = {'path': str(config), 'sha256': digest(config),
                                  'bindings': bindings, 'scope': 'APT_CONFIG read before empty main/parts; explicit env after sudo'}
        prefix = ['env', 'APT_CONFIG=' + str(config)]
        command('apt-effective-config', prefix + ['apt-config', 'dump'], 20)
        command('apt-update', ['sudo', '-n'] + prefix + ['timeout', '--signal=TERM', '--kill-after=5s', '180s', 'apt-get', 'update'], 190)
        command('apt-policy', prefix + ['apt-cache', 'policy', 'bubblewrap'], 20)
        command('apt-install', ['sudo', '-n'] + prefix + ['timeout', '--signal=TERM', '--kill-after=5s', '120s', 'apt-get', 'install', '-y', '--no-install-recommends', 'bubblewrap'], 130)
        for name, argv in [('dpkg-bubblewrap', ['dpkg-query', '-W', 'bubblewrap']),
                           ('bwrap-version', ['bwrap', '--version']),
                           ('unshare-version', ['unshare', '--version'])]:
            command(name, argv, 20)
        facts['tools'] = {name: {'path': shutil.which(name), 'sha256': digest(shutil.which(name))}
                          for name in ('bwrap', 'unshare')}
        facts['complete'] = True
        record()
        return 0
    except Exception as error:
        facts['error'] = str(error)
        record()
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
