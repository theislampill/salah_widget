#!/usr/bin/env python3
"""R0029 generation machine: fail-loud guards and all-or-nothing publication of generated outputs.

Phases (ISM-BLD-001/002, docs/state-contracts/R0029.md):
  planning -> computed -> validated -> publishing -> published
  any guard failure            -> failed-before-publish (zero in-tree writes)
  an I/O error while replacing -> failed-during-publish (replaced paths printed; re-run recovers)

The builders compute every output in memory (`Outputs`) and run every guard before
`publish` touches the tree. Guards are explicit exceptions, never `assert` (removed
by `python -O`). Anchored text substitutions go through `replace_exact`, which requires
the stated occurrence count and names the anchor on failure.

The builder owns only the declared generated-path set below. A rebuild removes owned
files it no longer produces and writes the inventory (`GENERATED.json`) last.
Two concurrent builds on one tree are unsupported (R0029 DG-1: one build per tree).
"""
from pathlib import Path
import errno, hashlib, json, os, re, shutil, sys, tempfile

INVENTORY = 'GENERATED.json'
INVENTORY_SCHEMA = 'salah-generated-inventory/1'

# The declared generated-path set. Nothing outside it is ever written or removed.
DECLARED_EXACT = frozenset([
    'index.html', 'offline.html', 'config.js', 'builder.html', INVENTORY,
    'real-sky/native-worker.js', 'real-sky/native-sky.js', 'real-sky/native-data.js', 'real-sky/native-sky.css',
    'real-sky/notices/LICENSE-CODE.txt', 'real-sky/notices/LICENSE-DATA.md', 'real-sky/notices/THIRD_PARTY_NOTICES.md',
    'real-sky/notices/upstream/ASTROPY_LICENSE.rst', 'real-sky/notices/vendor/spectral/IRAF-LICENSE.txt',
    'real-sky/notices/vendor/spectral/MITSUBA-LICENSE.txt', 'real-sky/notices/vendor/spectral/SPECLITE-LICENSE.txt',
    'real-sky/notices/provenance/cp7/admitted/ASTROGO-LICENSE.txt',
    'moon/moon-worker.js', 'moon/moon-host.js', 'moon/BUILD.json',
    'moon/assets/initial-compact.bin', 'moon/initial-compact-manifest.json',
])
# Generator-exclusive directories: files matching these patterns are owned even when
# no inventory lists them (a stale chunk from an older build or a hand-added copy).
DECLARED_PATTERNS = (
    re.compile(r'real-sky/core/(?:src|integration)/[A-Za-z0-9_.-]+\.mjs'),
    re.compile(r'moon/file-data/[A-Za-z0-9_.-]+\.js'),
)
SWEPT_DIRECTORIES = ('real-sky/core', 'moon/file-data')


class GenerationError(ValueError):
    """A detected generation failure. Raised before any in-tree write."""


def require(condition, message):
    if not condition:
        raise GenerationError(message)


def replace_exact(text, anchor, replacement, owner, count=1):
    """Replace every occurrence of `anchor`, which must occur exactly `count` times."""
    found = text.count(anchor)
    if found != count:
        raise GenerationError(f'{owner}: anchor {anchor[:80]!r} expected {count} occurrence(s), found {found}')
    return text.replace(anchor, replacement)


def declared(path):
    return path in DECLARED_EXACT or any(p.fullmatch(path) for p in DECLARED_PATTERNS)


class Outputs(dict):
    """Ordered map of repository-relative POSIX path -> exact bytes. Writes nothing."""

    def add(self, path, data):
        require(declared(path) and path != INVENTORY, 'Undeclared generated path: ' + path)
        require(path not in self, 'Generated path produced twice: ' + path)
        # str outputs are LF text; encoding them equals write_text(..., newline='\n').
        self[path] = data.encode('utf-8') if isinstance(data, str) else bytes(data)

    def text(self, path):
        return self[path].decode('utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory_bytes(outputs):
    files = {path: {'bytes': len(data), 'sha256': sha(data)} for path, data in sorted(outputs.items())}
    body = {'schema': INVENTORY_SCHEMA, 'generator': 'tools/build_native.py', 'fileCount': len(files),
            'byteCount': sum(row['bytes'] for row in files.values()), 'files': files}
    return (json.dumps(body, indent=1, sort_keys=False) + '\n').encode('utf-8')


def prior_inventory(root):
    """G0: owned paths named by the previous inventory, else the built-in declared list."""
    path = root / INVENTORY
    if not path.is_file():
        return set(DECLARED_EXACT) - {INVENTORY}, []
    try:
        body = json.loads(path.read_bytes())
        names = list(body['files']) if body.get('schema') == INVENTORY_SCHEMA else None
    except (ValueError, KeyError, TypeError, AttributeError):
        names = None
    require(isinstance(names, list) and all(isinstance(n, str) for n in names),
            f'Unreadable generated inventory {INVENTORY}; remove it and rebuild (nothing was written)')
    # A stale or forged inventory can never widen deletion beyond the declared set.
    return {n for n in names if declared(n)} - {INVENTORY}, sorted(n for n in names if not declared(n))


def swept(root):
    found = set()
    for directory in SWEPT_DIRECTORIES:
        base = root / directory
        if base.is_dir():
            for p in base.rglob('*'):
                rel = p.relative_to(root).as_posix()
                if p.is_file() and declared(rel):
                    found.add(rel)
    return found


def _replace(staged, target):
    try:
        os.replace(staged, target)
        return False
    except OSError as error:
        if error.errno != errno.EXDEV and getattr(error, 'winerror', None) != 17:
            raise
    # Staging is on another volume: copy beside the target, then replace atomically.
    sibling = target.with_name(target.name + '.generated-tmp')
    try:
        shutil.copyfile(staged, sibling)
        os.replace(sibling, target)
    finally:
        if sibling.exists():
            sibling.unlink()
    return True


def publish(root, outputs, inventory=True):
    """Publish validated outputs: stage, replace changed files, remove stale owned files, inventory last.

    Returns the diagnostic report. On an I/O error after the first in-tree change the
    replaced/removed paths are printed to stderr (failed-during-publish) and the error re-raised.
    """
    root = Path(root).resolve()
    for path in outputs:
        require(declared(path) and path != INVENTORY, 'Undeclared generated path: ' + path)
    prior, ignored = prior_inventory(root) if inventory else (set(), [])
    stale = sorted(p for p in ((prior | swept(root)) if inventory else set()) - set(outputs)
                   if declared(p) and p != INVENTORY and (root / p).is_file())
    plan = dict(outputs)
    if inventory:
        plan[INVENTORY] = inventory_bytes(outputs)
    report = {'phase': 'validated', 'written': 0, 'unchanged': 0, 'removed': 0, 'crossVolumeCopies': 0}
    if ignored:
        report['ignoredInventoryPaths'] = ignored
    replaced, removed = [], []
    staging = Path(tempfile.mkdtemp(prefix='salah-generated-'))
    try:
        changed = []
        for index, (path, data) in enumerate(plan.items()):
            target = root / path
            if target.is_file() and target.stat().st_size == len(data) and target.read_bytes() == data:
                report['unchanged'] += 1
                continue
            staged = staging / f'{index:05d}'
            staged.write_bytes(data)
            changed.append((path, staged))
        report['phase'] = 'publishing'

        def put(path, staged):
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            report['crossVolumeCopies'] += _replace(staged, target)
            replaced.append(path)

        for path, staged in changed:
            if path != INVENTORY:
                put(path, staged)
        for gone in stale:
            (root / gone).unlink()
            removed.append(gone)
        # The inventory is written last, after every replacement and removal.
        for path, staged in changed:
            if path == INVENTORY:
                put(path, staged)
        report.update(phase='published', written=len(replaced), removed=len(removed))
        if inventory:
            report['inventorySha256'] = sha(plan[INVENTORY])
        if removed:
            report['removedPaths'] = removed
        return report
    except BaseException as error:
        if replaced or removed:
            print(json.dumps({'phase': 'failed-during-publish', 'error': repr(error), 'replaced': replaced,
                              'removed': removed, 'recovery': 'python tools/build_native.py'}, indent=1),
                  file=sys.stderr)
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
