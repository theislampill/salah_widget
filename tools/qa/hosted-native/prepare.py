#!/usr/bin/env python3
"""Prepare pinned disposable native trees; never launch a browser.

All command output and source manifests remain in OUT/receipts. OUT/trees is
disposable public source and must not be uploaded as a plaintext capture artifact.
Existing output is refused, including after a failed or interrupted preparation.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import signal
import subprocess
import sys
import tarfile
import time

RESEARCH = '55d1b3edb66d2c35679707120b01ee1d3455e4a3'
RESEARCH_TREE = '0e626139b28bffe8f308173f806cad21bfeeb7bb'
BASELINE = 'df644ef60156b67b5c487395176369bcec7a0d7b'
BASELINE_TREE = '11117a0ba83c3db632bf4482c2db8feb5d52a769'
HISTORICAL = '4029d2f67f5a880c8ad889443bb7557d96022c45'
HELPER = 'tools/qa/precip_eval_lib.cjs'
HELPER_SHA256 = 'a02358979e9aa2f968c5ca9dde4ec7a8e63db869b871f1c24ce65a68e71497e7'
RAIN_PATCH = 'docs/state-contracts/evidence/R0040/phase1-options.patch.gz'
RAIN_PATCH_SHA256 = '69e5bd1d19e084cb6c5e1dd6f4157a53dff17834d5ba8ada8c190dba383e4b2a'
RAIN_PREIMAGE = '7f9eb1514f8d96097273d1ce9be6607b82ccb0c6df41a5094508dab787401249'
RAIN_POSTIMAGE = 'f83c4a729d0f0798bd234fb7b531c0a5bf2b767194b50de7a0b6bc71a6e07084'
SOURCE_DIRS = ('src', 'real-sky', 'tools', 'moon', 'vendor', 'v1', 'tests')
RUNTIME_PATHS = ('index.html', 'config.js', 'moon', 'real-sky', 'tests/r0002-ordinary.json')
BASE_PINS = {
    'index.html': '88411488017ea590e6b4c5a21adc143977c0907089eabb80b0cbe8f0ba18a8a1',
    'offline.html': '4a992602ac0c80ef3d2df59e1a0f346c8342502b5503d05783f94d5c2b13f2c6',
    'GENERATED.json': 'cbce31ba3a018b99e4259c192902442db421b2d8b8b65e48e143acf19bcaf4f2',
}
PINS = {
    'main': BASE_PINS,
    'r0040': {
        'index.html': '4b31c1177826c20e184ad3636642cef046d147fbd16f4ef946bb33e36b7318df',
        'offline.html': 'e4e7fa4ad49a07cffd39b554491aea11fa69e4fccf68d079d7d1d987d1d3108f',
        'GENERATED.json': '1e1c8b3a4712bec13257e2805df71d9d0a24dabeaa10b9ac1596cd998460ccd5',
    },
    'r0035': {
        'index.html': '74a2d263cc92600a1582f84d4c78f45f7cdecf0c14998ed6edfbd00f6c543851',
        'GENERATED.json': '8bbd701871b710f31af7f2dae8287daca4a40075d582f4e14583459715df4d86',
    },
}


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def git(root, *args):
    try:
        return subprocess.check_output(['git', '-C', str(root), *args], text=True, stderr=subprocess.PIPE).strip()
    except subprocess.CalledProcessError as error:
        raise ValueError('source Git command failed: ' + error.stderr) from error


def git_identity(root, commit, tree):
    """Require a genuine clean checkout, not an archive labelled with a commit."""
    if git(root, 'rev-parse', 'HEAD') != commit or git(root, 'rev-parse', 'HEAD^{tree}') != tree:
        raise ValueError('source commit/tree identity mismatch')
    if git(root, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('source checkout is not clean')
    return {'root': str(root.resolve()), 'commit': commit, 'tree': tree}


def checked_files(root, paths, destination=None):
    """Bind actual bytes to HEAD blobs, including files hidden by sparse status."""
    records = subprocess.check_output(['git', '-C', str(root), 'ls-tree', '-rz', 'HEAD', '--', *paths])
    rows = {}
    for item in records.split(b'\0'):
        if not item:
            continue
        meta, raw_name = item.split(b'\t', 1)
        mode, kind, blob = meta.decode('ascii').split()
        name = raw_name.decode('utf-8')
        p = root / name
        if kind != 'blob' or mode not in ('100644', '100755') or p.is_symlink() or not p.is_file():
            raise ValueError('missing or nonregular pinned source: ' + name)
        content = p.read_bytes()
        observed = hashlib.sha1(b'blob ' + str(len(content)).encode('ascii') + b'\0' + content).hexdigest()
        if observed != blob:
            raise ValueError('source blob mismatch: ' + name)
        rows[name] = {'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(), 'gitBlob': blob, 'mode': mode}
        if destination is not None:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(content)
            target.chmod(0o755 if mode == '100755' else 0o644)
    if not rows or any(not any(n == p or n.startswith(p + '/') for n in rows) for p in paths):
        raise ValueError('required source paths were absent from the commit')
    return rows


def verify_files(root, rows):
    for name, record in rows.items():
        parts = PurePosixPath(name)
        if parts.is_absolute() or '..' in parts.parts:
            raise ValueError('unsafe file receipt path')
        p = root / name
        if p.is_symlink() or not p.is_file() or p.stat().st_size != record['bytes'] or digest(p) != record['sha256']:
            raise ValueError('file identity mismatch: ' + name)


def verify_generated(root, pins):
    for name, expected in pins.items():
        p = root / name
        if p.is_symlink() or not p.is_file() or digest(p) != expected:
            raise ValueError('recorded build hash mismatch: ' + name)
    body = json.loads((root / 'GENERATED.json').read_text())
    if body.get('schema') != 'salah-generated-inventory/1' or body.get('generator') != 'tools/build_native.py':
        raise ValueError('invalid generated inventory')
    files = body['files']
    if body['fileCount'] != len(files) or body['byteCount'] != sum(row['bytes'] for row in files.values()):
        raise ValueError('inconsistent generated inventory totals')
    verify_files(root, files)
    return {'root': str(root), 'sha256': {name: digest(root / name) for name in pins},
            'fileCount': body['fileCount'], 'byteCount': body['byteCount']}


def apply_rain_patch(root, patch):
    owner = root / 'src/native/index.html'
    if digest(owner) != RAIN_PREIMAGE or digest(patch) != RAIN_PATCH_SHA256:
        raise ValueError('R0040 authored preimage or compressed patch identity mismatch')
    payload = gzip.decompress(patch.read_bytes())
    headers = [line for line in payload.splitlines() if line.startswith((b'--- ', b'+++ '))]
    if headers != [b'--- a/src/native/index.html', b'+++ b/src/native/index.html']:
        raise ValueError('R0040 patch exceeds its authored owner')
    for args in (['--check'], []):
        try:
            subprocess.run(['git', '-C', str(root), 'apply', *args, '-'], input=payload,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError as error:
            raise ValueError('R0040 patch command failed: ' + error.stderr.decode('utf-8', errors='replace')) from error
    if digest(owner) != RAIN_POSTIMAGE:
        raise ValueError('R0040 authored postimage identity mismatch')


class Commands:
    """Exclusive private logs, bounded children, and a receipt for every attempt."""
    def __init__(self, directory):
        self.directory = directory
        self.count = 0

    def run(self, tag, argv, cwd, timeout=600):
        self.count += 1
        prefix = self.directory / f'{self.count:02}-{tag}'
        record = {'argv': list(map(str, argv)), 'cwd': str(cwd), 'timeoutSeconds': timeout,
                  'startedUnixSeconds': time.time(), 'status': 'INCOMPLETE'}
        started = time.monotonic()
        stdout, stderr = Path(str(prefix) + '.stdout'), Path(str(prefix) + '.stderr')
        record.update(stdout=str(stdout), stderr=str(stderr))
        process = None
        try:
            with stdout.open('xb') as out, stderr.open('xb') as err:
                process = subprocess.Popen(record['argv'], cwd=cwd, stdout=out, stderr=err,
                                           start_new_session=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
                try:
                    record['returncode'] = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    record.update(status='TIMEOUT', childrenKilled=True, returncode=process.returncode)
                    raise
            record['status'] = 'PASS' if record['returncode'] == 0 else 'FAIL'
            if record['returncode']:
                raise RuntimeError('preparation command failed: ' + tag)
            return stdout
        except BaseException as error:
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                record['childrenKilled'] = True
            record['error'] = str(error)
            raise
        finally:
            record['elapsedSeconds'] = time.monotonic() - started
            write_json(Path(str(prefix) + '.json'), record)


def build(root, label, commands, second=False):
    stdout = commands.run(label, [sys.executable, '-B', 'tools/build_native.py'], root)
    result = json.loads(stdout.read_text())
    if result.get('stage') != 'complete-native-and-moon':
        raise ValueError('canonical builder did not finish')
    if second and (result['written'] != 0 or result['removed'] != 0 or result['unchanged'] != 117):
        raise ValueError('second canonical build was not 0 written / 117 unchanged')
    return result


def archive_runtime(source, destination, commands):
    archive = destination.with_suffix('.tar')
    commands.run('r003f-archive', ['git', '-C', str(source), 'archive', '--format=tar',
                                '--output=' + str(archive), BASELINE, *RUNTIME_PATHS], source)
    destination.mkdir()
    seen = set()
    with tarfile.open(archive, 'r:') as packed:
        for member in packed:
            name = PurePosixPath(member.name)
            if name.is_absolute() or '..' in name.parts or member.name in seen or not (member.isdir() or member.isfile()):
                raise ValueError('unsafe runtime archive member')
            seen.add(member.name)
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with packed.extractfile(member) as src, target.open('xb') as dst:
                    shutil.copyfileobj(src, dst)
                target.chmod(member.mode & 0o777)
    archive.unlink()
    rows = checked_files(source, RUNTIME_PATHS)
    verify_files(destination, rows)
    return rows


def prepare(research, baseline, historical, out):
    roots = [p.resolve(strict=True) for p in (research, baseline, historical)]
    if out.exists() or out.is_symlink():
        raise ValueError('fresh output required')
    out = out.resolve()
    if any(out == root or root in out.parents for root in roots):
        raise ValueError('output must be outside source trees')
    out.mkdir(mode=0o700, parents=True)
    receipts, trees = out / 'receipts', out / 'trees'
    receipts.mkdir(mode=0o700)
    trees.mkdir(mode=0o700)
    research, baseline, historical = roots
    report = {'schemaVersion': 1, 'protocol': 'salah-hosted-native-preparation/1', 'status': 'INCOMPLETE',
              'sources': {}, 'trees': {}, 'cleanup': 'Retained; never reuse this output. Disposable trees may be removed after observation.'}
    commands = Commands(receipts)
    try:
        report['sources']['research'] = git_identity(research, RESEARCH, RESEARCH_TREE)
        report['sources']['baseline'] = git_identity(baseline, BASELINE, BASELINE_TREE)
        if digest(historical / HELPER) != HELPER_SHA256:
            raise ValueError('historical helper identity mismatch')
        report['sources']['historical'] = {'root': str(historical), 'commit': HISTORICAL,
            'identityScope': 'pinned helper bytes; archive need not contain Git metadata', 'sha256': {HELPER: HELPER_SHA256}}
        research_files = checked_files(research, (*SOURCE_DIRS, RAIN_PATCH))
        baseline_files = checked_files(baseline, (*SOURCE_DIRS, 'index.html', 'offline.html', 'config.js', 'builder.html', 'GENERATED.json'))
        write_json(receipts / 'research-files.json', research_files)
        write_json(receipts / 'baseline-files.json', baseline_files)

        main = trees / 'main'
        commands.run('baseline-clone', ['git', '-c', 'core.hooksPath=/dev/null', 'clone', '--shared', '--no-checkout',
                                      '--no-hardlinks', str(baseline), str(main)], out)
        patterns = ['/' + p + '/' for p in SOURCE_DIRS] + ['/' + p for p in ('index.html', 'offline.html', 'config.js', 'builder.html', 'GENERATED.json', '.gitignore')]
        commands.run('baseline-sparse', ['git', '-C', str(main), 'sparse-checkout', 'set', '--no-cone', *patterns], out)
        commands.run('baseline-checkout', ['git', '-c', 'core.hooksPath=/dev/null', '-C', str(main), 'checkout', '--detach', BASELINE], out)
        build(main, 'baseline-build-1', commands)
        first = verify_generated(main, PINS['main'])
        build(main, 'baseline-build-2', commands, second=True)
        if first != verify_generated(main, PINS['main']):
            raise ValueError('baseline build inventories differ')
        commands.run('baseline-v1', [sys.executable, '-B', 'tools/verify_v1.py', '--negative-control'], main)
        git_identity(main, BASELINE, BASELINE_TREE)
        report['trees']['main'] = first

        rain = trees / 'r0040'
        rain.mkdir()
        checked_files(baseline, SOURCE_DIRS, rain)
        apply_rain_patch(rain, research / RAIN_PATCH)
        write_json(receipts / 'r0040-patch.json', {'preimage': RAIN_PREIMAGE, 'patch': RAIN_PATCH_SHA256, 'postimage': digest(rain / 'src/native/index.html')})
        build(rain, 'r0040-build-1', commands)
        first = verify_generated(rain, PINS['r0040'])
        build(rain, 'r0040-build-2', commands, second=True)
        if first != verify_generated(rain, PINS['r0040']):
            raise ValueError('R0040 build inventories differ')
        commands.run('r0040-v1', [sys.executable, '-B', 'tools/verify_v1.py', '--negative-control'], rain)
        report['trees']['r0040'] = first

        lab = trees / 'r0035'
        commands.run('r0035-materialize-and-build-1', [sys.executable, '-B', str(research / 'tools/r0035/materialize_lab.py'), str(lab)], research)
        first = verify_generated(lab, PINS['r0035'])
        identity = json.loads((lab / 'r0035-lab-identity.json').read_text())
        if identity['sourceHead'] != RESEARCH:
            raise ValueError('R0035 materializer source head mismatch')
        for name, expected in identity['sha256'].items():
            if digest(lab / name) != expected:
                raise ValueError('R0035 lab identity mismatch: ' + name)
        write_json(receipts / 'r0035-lab-identity.json', identity)
        build(lab, 'r0035-build-2', commands, second=True)
        if first != verify_generated(lab, PINS['r0035']):
            raise ValueError('R0035 build inventories differ')
        commands.run('r0035-v1', [sys.executable, '-B', 'tools/verify_v1.py', '--negative-control'], lab)
        report['trees']['r0035'] = first

        b0 = trees / 'r003f'
        files = archive_runtime(baseline, b0, commands)
        write_json(receipts / 'r003f-runtime-files.json', files)
        report['trees']['r003f'] = {'root': str(b0), 'sha256': {'index.html': digest(b0 / 'index.html')},
                                   'manifest': str(receipts / 'r003f-runtime-files.json'),
                                   'manifestSha256': digest(receipts / 'r003f-runtime-files.json')}
        verify_files(research, research_files)
        verify_files(baseline, baseline_files)
        git_identity(research, RESEARCH, RESEARCH_TREE)
        git_identity(baseline, BASELINE, BASELINE_TREE)
        report['status'] = 'PREPARED'
        return report
    except BaseException as error:
        report['error'] = str(error)
        raise
    finally:
        write_json(receipts / 'prepared.json', report)


def validate_prepared(receipt):
    """Recheck served files and inputs before emitting any execution command."""
    data = json.loads(receipt.read_text())
    if data.get('protocol') != 'salah-hosted-native-preparation/1' or data.get('schemaVersion') != 1 or data.get('status') != 'PREPARED':
        raise ValueError('preparation is not complete')
    research, baseline = (Path(data['sources'][k]['root']) for k in ('research', 'baseline'))
    git_identity(research, RESEARCH, RESEARCH_TREE)
    git_identity(baseline, BASELINE, BASELINE_TREE)
    for label, pins in PINS.items():
        verify_generated(Path(data['trees'][label]['root']), pins)
    git_identity(Path(data['trees']['main']['root']), BASELINE, BASELINE_TREE)
    if digest(Path(data['sources']['historical']['root']) / HELPER) != HELPER_SHA256:
        raise ValueError('historical helper changed')
    b0 = data['trees']['r003f']
    manifest = Path(b0['manifest'])
    if manifest.parent != receipt.parent or digest(manifest) != b0['manifestSha256']:
        raise ValueError('runtime manifest identity mismatch')
    verify_files(Path(b0['root']), json.loads(manifest.read_text()))
    if digest(Path(b0['root']) / 'index.html') != BASE_PINS['index.html']:
        raise ValueError('B0 index is not the baseline')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('research', 'baseline', 'historical', 'out'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        prepare(args.research, args.baseline, args.historical, args.out)
    except Exception:
        print('PREPARATION INCOMPLETE; private receipts retained when output was admitted', file=sys.stderr)
        return 2
    print('PREPARATION READY')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
