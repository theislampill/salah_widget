#!/usr/bin/env python3
"""Assemble only the sealed R000B generated outputs on its owned branch.

The connector cannot transport the large offline entry. This bounded hosted
step runs the normal builder, verifies locally declared SHA-256 outputs, and
publishes one ordinary fast-forward commit. It never accepts or merges R000B.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


REPOSITORY = 'theislampill/salah_widget'
BRANCH = 'pro/r000b-explicit-weather-withdrawal-20261106'
# Reconciliation with preceding accepted owners requires an explicit reviewed
# update to both these pins and the manifest, never automatic moving-main reuse.
BASELINE_COMMIT = 'eebba178172f96b3ffe5ab3845bc0fffd57c6e1b'
BASELINE_TREE = '6b94a3933f9d1381b1c2ceaab287c93afb215ecb'
MANIFEST = 'docs/state-contracts/r000b-generated-manifest.json'
GENERATED = {'index.html', 'offline.html', 'real-sky/native-sky.js', 'moon/BUILD.json'}
AUTHORED = {'src/native/index.html', 'real-sky/native-host-hooks.js',
            'real-sky/native-composition.mjs', 'real-sky/native-host.mjs',
            'real-sky/native-preview-host.mjs'}
REQUIRED_INPUTS = AUTHORED | {'src/native/config.js', 'src/native/builder.html',
    'tools/build_native.py', 'tools/build_moon.py', 'tools/native_core_horizon.py',
    'tools/native_star_bootstrap.py'}
ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def changed_paths(*args):
    # Authorization accounts for both endpoints of a rename.
    return set(filter(None, git('diff', '--no-renames', '--name-only', *args).splitlines()))


def digest(path):
    with path.open('rb') as stream:
        return stream_digest(stream)


def stream_digest(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def allowed_change(rel):
    return (rel in AUTHORED | GENERATED | {'README.md', 'DESIGN.md', 'HANDOFF.md',
            'tests/native-script-contract.js', 'tests/r000c-weather.test.cjs',
            'tests/r0003-harness.cjs', 'tests/r000b-sky-withdrawal.test.mjs',
            'tests/real-sky/native-head-handoff.cjs',
            'tests/r0025-context.cjs', 'tests/r0025-continuity.cjs',
            'tests/r0025-lifecycle.cjs',
            'tests/real-sky/native-host-composition.test.mjs',
            'tests/real-sky/native-preview-host.test.mjs',
            'tests/real-sky/native-weather-withdrawal.test.mjs',
            'tests/weather-withdrawal-authority.test.cjs',
            'tests/weather-withdrawal-mutations.test.cjs',
            '.github/workflows/r000b-weather-withdrawal.yml',
            'tools/qa/r000b_assemble_candidate.py', 'tools/qa/run_r000b_withdrawal.py',
            'tests/rlgwo/r000b-no-timetable-fixture.html',
            'docs/state-contracts/r000b-native-baseline.json',
            'docs/state-contracts/r000b-native-candidate.json', MANIFEST}
        or rel.startswith(('docs/state-contracts/R000B', 'docs/state-contracts/evidence/R000B/',
                           'tests/weather-no-timetable', 'tests/real-sky/native-cloud-authority')))


def safe_path(rel):
    return (isinstance(rel, str) and rel and not Path(rel).is_absolute()
            and '..' not in Path(rel).parts and '\n' not in rel and '\r' not in rel
            and (ROOT / rel).resolve().is_relative_to(ROOT))


def validate_manifest(manifest):
    require(isinstance(manifest, dict) and manifest.get('schema') == 'r000b-generated-candidate/v1',
            'Unknown manifest schema')
    require(manifest.get('branch') == BRANCH, 'Manifest branch mismatch')
    require(manifest.get('baseline') == {'commit': BASELINE_COMMIT, 'tree': BASELINE_TREE},
            'Baseline must match the exact reviewed commit and tree')
    require(isinstance(manifest.get('generated'), dict) and set(manifest['generated']) == GENERATED,
            'Generated write set changed')
    require(isinstance(manifest.get('inputs'), dict) and REQUIRED_INPUTS <= set(manifest['inputs']),
            'Required authored/builder input inventory is incomplete')
    approved = manifest.get('approvedChanges')
    require(isinstance(approved, list) and len(set(approved)) == len(approved)
            and all(safe_path(rel) and allowed_change(rel) for rel in approved),
            'Approved change set contains an undeclared or unsafe path')
    require((set(approved) - GENERATED - {MANIFEST}) <= set(manifest['inputs']),
            'Approved source/test/doc changes lack input hashes')
    for files in [manifest['inputs'], manifest['generated']]:
        require(all(safe_path(rel) and isinstance(value, str)
                    and re.fullmatch(r'[0-9a-f]{64}', value) for rel, value in files.items()),
                'Invalid file path or SHA-256 inventory')


def verify_files(files, label):
    for rel, expected in files.items():
        path = ROOT / rel
        require(not path.is_symlink() and path.is_file() and digest(path) == expected,
                f'{label} drift: {rel}')


def verify_git_files(commit, files):
    for rel, expected in files.items():
        process = subprocess.Popen(['git', 'show', f'{commit}:{rel}'], cwd=ROOT,
                                   stdout=subprocess.PIPE)
        actual = stream_digest(process.stdout)
        process.stdout.close()
        require(process.wait() == 0 and actual == expected, 'Committed blob drift: ' + rel)


def remote_head():
    lines = git('ls-remote', '--heads', 'origin', 'refs/heads/' + BRANCH).splitlines()
    require(len(lines) == 1, 'Owned remote branch absent or ambiguous')
    sha, ref = lines[0].split()
    require(ref == 'refs/heads/' + BRANCH and re.fullmatch(r'[0-9a-f]{40}', sha),
            'Unexpected remote identity')
    return sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    receipt = args.receipt.resolve()
    require(not receipt.is_relative_to(ROOT), 'Evidence must stay outside the checkout')
    receipt.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = args.manifest.resolve()
    require(manifest_path == ROOT / MANIFEST, 'Manifest must use the reviewed repository path')
    manifest = json.loads(manifest_path.read_text())
    row = {'schema': 'r000b-hosted-assembly/v1', 'status': 'FAIL',
           'manifestSha256': digest(manifest_path), 'published': False}
    try:
        validate_manifest(manifest)
        source = git('rev-parse', 'HEAD')
        row.update(sourceCommit=source, sourceTree=git('rev-parse', 'HEAD^{tree}'),
                   baseline=manifest['baseline'])
        require(not git('status', '--porcelain', '--untracked-files=all'), 'Checkout is not clean')
        verify_files(manifest['inputs'], 'input')
        if args.publish:
            require(os.environ.get('GITHUB_ACTIONS') == 'true', 'Publication requires the hosted action')
            require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY, 'Wrong repository')
            require(os.environ.get('GITHUB_EVENT_NAME') == 'push', 'Only the owned push event is supported')
            require(os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH, 'Wrong publication ref')
            require(os.environ.get('GITHUB_SHA') == source, 'Checkout differs from the triggering SHA')
            require(remote_head() == source, 'Remote advanced before assembly')
        exists = subprocess.run(['git', 'cat-file', '-e', BASELINE_COMMIT + '^{commit}'], cwd=ROOT,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        if not exists:
            subprocess.run(['git', 'fetch', '--depth=1', '--no-tags', '--no-write-fetch-head',
                            'origin', BASELINE_COMMIT], cwd=ROOT, check=True)
        require(git('rev-parse', BASELINE_COMMIT + '^{tree}') == BASELINE_TREE, 'Baseline tree mismatch')
        source_delta = changed_paths(BASELINE_COMMIT, 'HEAD', '--')
        require(source_delta - GENERATED == set(manifest['approvedChanges']) - GENERATED,
                'Source-stage delta differs from reviewed inventory')
        row['approvedSourceDelta'] = sorted(source_delta)
        with (receipt.parent / 'build.log').open('w') as log:
            subprocess.run([sys.executable, 'tools/build_native.py'], cwd=ROOT,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
            subprocess.run([sys.executable, 'tools/verify_v1.py'], cwd=ROOT,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        verify_files(manifest['inputs'], 'input after build')
        verify_files(manifest['generated'], 'generated')
        changed = changed_paths('HEAD', '--')
        require(changed <= GENERATED, 'Builder changed an undeclared path: ' + ', '.join(sorted(changed - GENERATED)))
        require(not git('ls-files', '--others', '--exclude-standard'), 'Builder left untracked files')
        require(not changed_paths('--cached'), 'Unexpected staged changes')
        row['generated'] = manifest['generated']
        row['changed'] = sorted(changed)
        if args.publish and changed:
            require(remote_head() == source, 'Remote advanced during assembly')
            subprocess.run(['git', 'add', '--', *sorted(changed)], cwd=ROOT, check=True)
            require(changed_paths('--cached') == changed,
                    'Staged set differs from the generated set')
            verify_git_files(git('write-tree'), manifest['generated'])
            message = ('build: assemble sealed R000B weather withdrawal candidate\n\n'
                       f'Source stage: {source}\n'
                       f'Manifest SHA-256: {row["manifestSha256"]}\n\n'
                       'Implements #11; engineering candidate only. Integration order and exact owner approval remain required.\n\n'
                       'Co-Authored-By: ChatGPT <noreply@openai.com>')
            subprocess.run(['git', '-c', 'user.name=github-actions[bot]', '-c',
                            'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                            'commit', '-m', message], cwd=ROOT, check=True)
            require(git('rev-parse', 'HEAD^') == source, 'Generated commit lost source parent')
            verify_git_files('HEAD', manifest['generated'])
            require(remote_head() == source, 'Remote advanced before push')
            subprocess.run(['git', 'push', 'origin', 'HEAD:refs/heads/' + BRANCH], cwd=ROOT, check=True)
            row['published'] = True
        row.update(candidateCommit=git('rev-parse', 'HEAD'), candidateTree=git('rev-parse', 'HEAD^{tree}'))
        if args.publish:
            verify_git_files(row['candidateCommit'], manifest['generated'])
            require(remote_head() == row['candidateCommit'], 'Published ref readback mismatch')
            require(not git('status', '--porcelain', '--untracked-files=all'), 'Candidate checkout is not clean')
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
                    output.write('candidate=' + row['candidateCommit'] + '\n')
                    output.write('baseline=' + BASELINE_COMMIT + '\n')
        row['status'] = 'ASSEMBLED_PENDING_QUALIFICATION' if args.publish else 'VERIFIED_BUILD_NOT_PUBLISHED'
    except Exception as error:
        row['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        receipt.write_text(json.dumps(row, indent=2) + '\n')
        print(json.dumps(row), flush=True)


if __name__ == '__main__':
    main()
