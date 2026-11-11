#!/usr/bin/env python3
"""Rebind the R000B hosted-assembly manifest and native expectations to accepted main.

Re-runnable. Identities are computed with the repository's own owners:
tools/qa/r000b_assemble_candidate.py (pins, write sets, digest, delta),
tools/cp9/runtime_identity.py (runtime tree) and tools/qa/run_r000b_withdrawal.py
(identities / script_identities). The path lists for authored and fixture
sources are taken from the previous expected manifests, unchanged.

usage: python rebind_r000b_ci.py --baseline-root <clean checkout of BASELINE_COMMIT>
Writes the two native expectations, their runtime inventories and a receipt,
stages them, then writes docs/state-contracts/r000b-generated-manifest.json from
the staged delta against BASELINE_COMMIT. Nothing is committed or pushed.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
REL = HERE.relative_to(ROOT).as_posix()


def module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


sys.path[:0] = [str(ROOT / 'tools/qa'), str(ROOT / 'tools/cp9')]
assembly = module('r000b_assembly', 'tools/qa/r000b_assemble_candidate.py')
driver = module('r000b_driver', 'tools/qa/run_r000b_withdrawal.py')
from runtime_identity import runtime_identity  # noqa: E402


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


def dump(path, value):
    (ROOT / path).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def expectation(label, product_root, previous):
    runtime = runtime_identity(product_root)
    index = (product_root / 'index.html').read_bytes()
    return runtime, {
        'schema': 'r000b-native-expected/v1', 'label': label,
        'runtimeTreeSha256': runtime['treeSha256'], 'indexSha256': driver.sha(index),
        'scriptBodies': driver.script_identities(index),
        'authoredSources': driver.identities(product_root, list(previous['authoredSources'])),
        'fixtureSources': driver.identities(ROOT, list(previous['fixtureSources']))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-root', type=Path)
    parser.add_argument('--manifest-only', action='store_true',
                        help='Keep the native expectations and receipt; recompute only the assembly manifest')
    args = parser.parse_args()
    if args.manifest_only:
        return write_manifest()
    assembly.require(args.baseline_root is not None, '--baseline-root is required')
    base = args.baseline_root.resolve()
    assembly.require(git('rev-parse', 'HEAD', cwd=base) == assembly.BASELINE_COMMIT, 'baseline root is not BASELINE_COMMIT')
    assembly.require(git('rev-parse', 'HEAD^{tree}', cwd=base) == assembly.BASELINE_TREE, 'baseline tree mismatch')
    assembly.require(not git('status', '--porcelain', '--untracked-files=all', cwd=base), 'baseline root is not clean')

    receipt = {'schema': 'r000b-ci-rebind/v1', 'baseline': {'commit': assembly.BASELINE_COMMIT, 'tree': assembly.BASELINE_TREE},
               'sourceHead': git('rev-parse', 'HEAD'), 'previous': {}, 'current': {}}
    for product, product_root, label in [
            ('baseline', base, 'R000B-baseline-main-dbf3370f-native-pending'),
            ('candidate', ROOT, 'R000B-candidate-reconciled-main-dbf3370f-native-pending')]:
        path = f'docs/state-contracts/r000b-native-{product}.json'
        previous_bytes = (ROOT / path).read_bytes()
        previous = json.loads(previous_bytes)
        receipt['previous'][path] = {'sha256': driver.sha(previous_bytes), 'label': previous['label'],
                                     'runtimeTreeSha256': previous['runtimeTreeSha256'], 'indexSha256': previous['indexSha256']}
        runtime, expected = expectation(label, product_root, previous)
        inventory = f'{REL}/r000b-native-{product}-runtime-inventory.json'
        dump(inventory, runtime)
        dump(path, expected)
        receipt['current'][path] = {'sha256': driver.sha((ROOT / path).read_bytes()), 'label': label,
                                    'runtimeTreeSha256': runtime['treeSha256'], 'runtimeFiles': len(runtime['files']),
                                    'indexSha256': expected['indexSha256'], 'inventory': inventory}
    previous_manifest_bytes = (ROOT / assembly.MANIFEST).read_bytes()
    previous_manifest = json.loads(previous_manifest_bytes)
    receipt['previous'][assembly.MANIFEST] = {'sha256': driver.sha(previous_manifest_bytes),
                                              'baseline': previous_manifest['baseline'],
                                              'approvedChanges': len(previous_manifest['approvedChanges'])}
    dump(f'{REL}/rebind-receipt.json', receipt)
    subprocess.run(['git', 'add', '--', 'docs/state-contracts/r000b-native-baseline.json',
                    'docs/state-contracts/r000b-native-candidate.json', REL], cwd=ROOT, check=True)
    write_manifest(receipt['current'])


def write_manifest(native=None):
    manifest_path = ROOT / assembly.MANIFEST
    previous_manifest = json.loads(manifest_path.read_bytes())
    assembly.require(not git('diff', '--name-only'), 'unstaged changes would escape the staged delta')
    assembly.require(not git('ls-files', '--others', '--exclude-standard', '--', 'docs', 'tests', 'tools', 'src', 'real-sky'),
                     'untracked files would escape the staged delta')
    approved = sorted(assembly.changed_paths('--cached', assembly.BASELINE_COMMIT, '--') | {assembly.MANIFEST})
    extras = (set(previous_manifest['inputs']) - set(previous_manifest['approvedChanges'])) | assembly.REQUIRED_INPUTS
    inputs = {rel: assembly.digest(ROOT / rel)
              for rel in sorted((set(approved) - assembly.GENERATED - {assembly.MANIFEST}) | extras)}
    generated = {rel: assembly.digest(ROOT / rel) for rel in sorted(assembly.GENERATED)}
    manifest = {'schema': 'r000b-generated-candidate/v1', 'branch': assembly.BRANCH,
                'baseline': {'commit': assembly.BASELINE_COMMIT, 'tree': assembly.BASELINE_TREE},
                'approvedChanges': approved, 'inputs': inputs, 'generated': generated}
    assembly.validate_manifest(manifest)
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    subprocess.run(['git', 'add', '--', assembly.MANIFEST], cwd=ROOT, check=True)
    print(json.dumps({'manifestSha256': assembly.digest(manifest_path), 'approvedChanges': len(approved),
                      'inputs': len(inputs), 'generated': generated, 'native': native}, indent=2))


if __name__ == '__main__':
    main()
