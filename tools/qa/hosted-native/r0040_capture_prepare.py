#!/usr/bin/env python3
"""Execute the exact guarded offline R0040 capture recipe with private receipts.

This entry prepares historical sources only. It does not build main, import a
browser package, run the native capture, or qualify its lossless cadence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import signal
import stat
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOCUMENT = ROOT/'docs/state-contracts/R0040-native-capture-preflight.md'
DEFAULT_MANIFEST = ROOT/'docs/state-contracts/evidence/R0040/native-capture-preflight.json'
MANIFEST_SHA256 = '267f2fd8ac130c049430ffdaa0fd50b72457c60084b49360346748cc940f6b73'
RECIPE_SHA256 = '9fc26a75cb62c145f9de7bd7aa386ac6714c238f3e08089558d34f02882f9730'
START = b'python - "$MANIFEST" "$RESEARCH" "$HISTORICAL" "$MAIN" "$NEW_WORK" <<\'PY\'\n'
END = b'\nPY\n```'
TIMEOUT_SECONDS = 180


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, body):
    pending = path.with_name(path.name+'.pending')
    with pending.open('x', encoding='utf-8') as stream:
        json.dump(body, stream, indent=2); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    # Publish only fsynced bytes, exclusively. A failed pending write is retained
    # privately and cannot masquerade as the terminal process admission receipt.
    os.link(pending, path)
    pending.unlink()


def load_contract(manifest, document=DOCUMENT):
    """Execute only the recipe bytes independently checked in the preflight."""
    data = Path(manifest).read_bytes()
    if digest(data) != MANIFEST_SHA256:
        raise ValueError('capture preparation manifest digest mismatch')
    source = Path(document).read_bytes()
    if source.count(START) != 1 or END not in source.split(START, 1)[1]:
        raise ValueError('unique guarded preparation recipe required')
    recipe = source.split(START, 1)[1].split(END, 1)[0]
    if digest(recipe) != RECIPE_SHA256:
        raise ValueError('guarded preparation recipe digest mismatch')
    body = json.loads(data)
    if (body.get('protocol') != 'r0040-native-capture-preflight/1'
            or len(body['historical']['files']) != 6 or len(body['patches']) != 2
            or len(body['stages']) != 2 or body['pins']['options'] is not None):
        raise ValueError('incomplete capture preparation contract')
    return body, recipe


def read_regular(root, name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('unsafe prepared source path')
    path = root
    for part in relative.parts:
        path = path/part
        if path.is_symlink():
            raise ValueError('symlink prepared source')
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('regular prepared source required')
    return path.read_bytes()


def inspect_prepared(work, manifest):
    path = work/'receipts/prepared.json'
    data = read_regular(work, 'receipts/prepared.json')
    body = json.loads(data)
    if (body.get('protocol') != 'r0040-capture-preparation/1' or body.get('status') != 'PREPARED'
            or body.get('nativeStatus') != 'NOT_RUN' or body.get('manifestSha256') != MANIFEST_SHA256
            or body.get('pins') != manifest['pins'] or body.get('mainHead') != manifest['main']['head']
            or body.get('historicalPath') != 'historical' or body.get('stages') != manifest['stages']):
        raise ValueError('original preparation receipt is incomplete or has wrong custody')
    historical = work/'historical'; expected = manifest['stages'][-1]['files']
    actual = {p.relative_to(historical).as_posix() for p in historical.rglob('*') if p.is_file() or p.is_symlink()}
    if actual != set(expected):
        raise ValueError('prepared historical file population differs from the six-file contract')
    final = {}
    for name, row in expected.items():
        source = read_regular(historical, name)
        observed = {'bytes': len(source), 'sha256': digest(source),
                    'gitBlob': hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()}
        if observed != row:
            raise ValueError('prepared historical source differs: '+name)
        final[name] = observed
    return {'path': str(path), 'sha256': digest(data)}, final


def run_child(argv, recipe, cwd, stdout, stderr, receipt, timeout):
    """Keep actual child status and both streams, including process-group timeout."""
    started = time.monotonic(); process = None
    receipt.update(returncode=None, timedOut=False)
    with stdout.open('xb') as out, stderr.open('xb') as err:
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                       start_new_session=True)
            try:
                process.communicate(input=recipe, timeout=timeout)
            except subprocess.TimeoutExpired:
                receipt['timedOut'] = True
                try: os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError: pass
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired: pass
            finally:
                # The leader can exit while a descendant still holds its group.
                if receipt['timedOut'] or process.poll() is None:
                    try: os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                process.wait()
        finally:
            if process is not None:
                receipt['returncode'] = process.returncode
            receipt['elapsedSeconds'] = time.monotonic()-started
            out.flush(); os.fsync(out.fileno()); err.flush(); os.fsync(err.fileno())


def prepare(args, timeout=TIMEOUT_SECONDS):
    if not __debug__ or sys.flags.optimize:
        raise RuntimeError('optimized Python is unsupported for guarded preparation')
    os.umask(0o077)
    if args.receipts.exists() or args.receipts.is_symlink():
        raise ValueError('fresh private receipt directory required')
    if args.out.is_symlink():
        raise ValueError('symlink output refused')
    paths = {key: Path(getattr(args, key)).resolve() for key in ('manifest', 'research', 'historical', 'main', 'out')}
    receipts = args.receipts.resolve(); work = paths['out']
    for root in (paths['research'], paths['historical'], paths['main']):
        if any(target == root or root in target.parents for target in (work, receipts)):
            raise ValueError('work and private receipts must be outside every input tree')
    if work == receipts or work in receipts.parents or receipts in work.parents:
        raise ValueError('work and private receipt directories must be separate')
    receipts.mkdir(parents=True, mode=0o700)
    result = {'protocol': 'r0040-capture-preparation-process/1', 'status': 'INCOMPLETE',
              'nativeStatus': 'NOT_RUN', 'returncode': None, 'timedOut': False,
              'inputs': {key: str(value) for key, value in paths.items()},
              'outputPreexisted': work.exists(), 'wrapperSha256': digest(Path(__file__).read_bytes()),
              'expectedManifestSha256': MANIFEST_SHA256, 'expectedRecipeSourceSha256': RECIPE_SHA256,
              'timeoutSeconds': timeout, 'streams': {}}
    write_json(receipts/'attempt.json', result)
    try:
        manifest, recipe = load_contract(paths['manifest'])
        result.update(manifestSha256=MANIFEST_SHA256, recipeSourceSha256=RECIPE_SHA256)
        # A new cache prefix plus -B forces source compilation for pack_design;
        # -I ignores inherited Python loaders without changing the recipe bytes.
        argv = [sys.executable, '-I', '-B', '-X', 'pycache_prefix='+str(receipts/'unused-bytecode-cache'), '-',
                *(str(paths[key]) for key in ('manifest', 'research', 'historical', 'main', 'out'))]
        result['argv'] = argv
        run_child(argv, recipe, receipts, receipts/'recipe.stdout', receipts/'recipe.stderr', result, timeout)
        if result['returncode'] == 0 and not result['timedOut']:
            prepared, final = inspect_prepared(work, manifest)
            result.update(status='PREPARED', preparedReceipt=prepared, finalHistoricalFiles=final,
                          completedStages=len(manifest['stages']), pins=manifest['pins'])
        else:
            result['error'] = {'type': 'RecipeProcessFailure', 'message': 'guarded recipe did not complete normally'}
    except BaseException as error:
        result['error'] = {'type': type(error).__name__, 'message': str(error)}
        raise
    finally:
        # Keep even a partial original receipt without relabeling it as prepared.
        if not result['outputPreexisted'] and 'preparedReceipt' not in result:
            try:
                path = work/'receipts/prepared.json'; data = read_regular(work, 'receipts/prepared.json')
                result['preparedReceipt'] = {'path': str(path), 'sha256': digest(data)}
            except (OSError, ValueError): pass
        for name in ('stdout', 'stderr'):
            path = receipts/('recipe.'+name)
            if path.is_file():
                data = path.read_bytes()
                result['streams'][name] = {'file': path.name, 'path': str(path), 'bytes': len(data), 'sha256': digest(data)}
        write_json(receipts/'process.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'research', 'historical', 'main', 'out', 'receipts'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = prepare(args)
    except Exception as error:
        print('R0040 preparation refused: '+str(error), file=sys.stderr)
        return 2
    print('R0040 preparation '+result['status']+'; inspect private receipts')
    code = result['returncode']
    return 0 if result['status'] == 'PREPARED' else code if isinstance(code, int) and 0 < code < 256 else 2


if __name__ == '__main__': sys.exit(main())
