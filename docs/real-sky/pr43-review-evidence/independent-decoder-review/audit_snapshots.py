"""Read-only exact snapshot/embedding audit. No build, browser or benchmark."""
import datetime
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parents[2]
BEFORE = RUN / 'candidates/pr43-r1r2-03'
AFTER = RUN / 'candidates/pr43-r1r2-04'
WORKER = RUN / 'workers/install/pr43-decode-cost'
EXPECTED_RUNTIME = '040192b555fa0db2fad760470ec020a06d86d3e0c7615153062ec5e76c50a2d5'
DECODER = 'moon/src/moon-initial-compact.mjs'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()

def binding(path):
    return {'path': str(path), 'sha256': digest(path), 'bytes': path.stat().st_size}

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')

def tree(root):
    return {path.relative_to(root).as_posix(): {'bytes': path.stat().st_size, 'sha256': digest(path)}
            for path in sorted(root.rglob('*')) if path.is_file() and '.git' not in path.relative_to(root).parts}

def runtime(files):
    selected = {name: value for name, value in files.items()
                if name in {'index.html', 'offline.html', 'config.js', 'builder.html'}
                or name.startswith('real-sky/')
                or (name.startswith('moon/') and name.split('/')[1] not in {'src', 'tests'})}
    canonical = ''.join(value['sha256'] + '  ' + name + '\n' for name, value in sorted(selected.items()))
    return {'schemaVersion': 1, 'treeSha256': hashlib.sha256(canonical.encode()).hexdigest(),
            'algorithm': 'SHA256 of sorted <sha256><two spaces><relative POSIX path><LF> records', 'files': selected}

def replaced_digest(path, old, new):
    """Hash without the sole decoder delta while keeping offline memory bounded."""
    h = hashlib.sha256()
    pending = b''
    found = 0
    length = 0
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            pending += chunk
            # Retain the only possible straddling match until the next chunk.
            cutoff = max(0, len(pending) - len(new) + 1)
            scan = 0
            while True:
                at = pending.find(new, scan)
                if at < 0 or at >= cutoff:
                    break
                segment = pending[scan:at] + old
                h.update(segment)
                length += len(segment)
                found += 1
                scan = at + len(new)
            emit = max(scan, cutoff)
            h.update(pending[scan:emit])
            length += emit - scan
            pending = pending[emit:]
        found += pending.count(new)
        pending = pending.replace(new, old)
        h.update(pending)
        length += len(pending)
    return {'normalizedSha256': h.hexdigest(), 'normalizedBytes': length, 'decoderOccurrences': found}

def main():
    files_before, files_after = tree(BEFORE), tree(AFTER)
    runtime_before, runtime_after = runtime(files_before), runtime(files_after)
    build_bindings = []
    for name, root, observed in [('pr43-r1r2-03', BEFORE, runtime_before), ('pr43-r1r2-04', AFTER, runtime_after)]:
        base = RUN / 'evidence/PR43-review' / name / 'build'
        receipt = read(base / 'receipt.json')
        r1, r2 = read(base / 'runtime-1.json'), read(base / 'runtime-2.json')
        build_bindings.append({'candidate': str(root), 'receipt': binding(base / 'receipt.json'),
                               'runtime1': binding(base / 'runtime-1.json'), 'runtime2': binding(base / 'runtime-2.json'),
                               'receiptData': receipt, 'runtimeEqualsBothRetainedBuilds': observed == r1 == r2,
                               'runtimeMatchesReceipt': observed['treeSha256'] == receipt['runtimeSha256'],
                               'indexMatchesReceipt': observed['files']['index.html']['sha256'] == receipt['indexSha256'],
                               'logBindings': [binding(base / f) for f in ['build-1.log', 'build-2.log', 'v1.log']],
                               'inputManifest': binding(base / 'inputs.json')})
    shared = set(files_before) & set(files_after)
    changed = [{'relativePath': name, 'before': files_before[name], 'after': files_after[name]}
               for name in sorted(shared) if files_before[name] != files_after[name]]
    added = [{'relativePath': name, **files_after[name]} for name in sorted(set(files_after) - set(files_before))]
    removed = [{'relativePath': name, **files_before[name]} for name in sorted(set(files_before) - set(files_after))]
    old = (BEFORE / DECODER).read_bytes()
    new = (AFTER / DECODER).read_bytes()
    embeddings = []
    for name in ('index.html', 'offline.html', 'moon/moon-host.js'):
        item = replaced_digest(AFTER / name, old, new)
        item.update(relativePath=name, before=files_before[name], after=files_after[name],
                    onlyExactDecoderDelta=item['decoderOccurrences'] > 0 and item['normalizedSha256'] == files_before[name]['sha256'] and item['normalizedBytes'] == files_before[name]['bytes'])
        embeddings.append(item)
    build_old = read(BEFORE / 'moon/BUILD.json')
    build_new = read(AFTER / 'moon/BUILD.json')
    expected_build = json.loads(json.dumps(build_old))
    expected_build['source'][DECODER] = digest(AFTER / DECODER)
    expected_build['hostSha256'] = digest(AFTER / 'moon/moon-host.js')
    integration = read(RUN / 'evidence/PR43-review/R1-decoder-integration-01/receipt.json')
    protected = []
    for raw_path, expected in integration['protectedUnchanged'].items():
        name = raw_path.replace('\\', '/')
        protected.append({'relativePath': name, 'expectedSha256': expected, 'before': files_before[name], 'after': files_after[name],
                          'unchangedAndMatchesIntegration': files_before[name]['sha256'] == files_after[name]['sha256'] == expected})
    # Keep every protected source owner, immutable scientific/V1 asset and numerical consumer bound.
    protected_classes = {}
    for prefix in ('src/', 'tools/', 'real-sky/', 'moon/src/', 'moon/assets/', 'moon/file-data/', 'moon/chunks/', 'vendor/', 'v1/', 'config.js', 'presets/'):
        names = {name for name in set(files_before) | set(files_after) if name.startswith(prefix)}
        delta = [name for name in sorted(names) if files_before.get(name) != files_after.get(name)]
        protected_classes[prefix] = {'count': len(names), 'changed': delta}
    return_report = read(WORKER / 'REPORT.json')
    worker_bindings = []
    for key in ('production', 'candidate', 'unchangedDigest', 'unchangedPayload', 'unchangedEncoding', 'patch', 'benchmark'):
        record = return_report[key]
        item = binding(Path(record['path']))
        worker_bindings.append({'kind': key, **item, 'matchesReturn': item['sha256'] == record['sha256'] and item['bytes'] == record['bytes']})
    for record in return_report['scripts'] + [return_report['controls']['report'], return_report['controls']['command']['stdout'], return_report['controls']['command']['stderr']]:
        item = binding(Path(record['path']))
        worker_bindings.append({**item, 'matchesReturn': item['sha256'] == record['sha256'] and item['bytes'] == record['bytes']})
    diff = ''.join(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True), fromfile='candidate03/' + DECODER, tofile='candidate04/' + DECODER))
    (HERE / 'DECODER_SOURCE_DIFF.patch').write_text(diff, encoding='utf-8')
    output = {'schema': 'pr43-decoder-independent-snapshot-audit/v1', 'atUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'writeScope': str(HERE), 'beforeCandidate': str(BEFORE), 'afterCandidate': str(AFTER),
              'expectedRuntime04': EXPECTED_RUNTIME, 'runtime04MatchesExpected': runtime_after['treeSha256'] == EXPECTED_RUNTIME,
              'runtimeBefore': runtime_before, 'runtimeAfter': runtime_after,
              'wholeTreeBefore': files_before, 'wholeTreeAfter': files_after,
              'changed': changed, 'added': added, 'removed': removed, 'buildBindings': build_bindings,
              'generatedEmbeddings': embeddings, 'moonBuildMetadataExactlyDerivedDecoderDelta': expected_build == build_new,
              'protectedIntegrationOwners': protected, 'protectedClasses': protected_classes,
              'workerReturn': binding(WORKER / 'REPORT.json'), 'workerBindings': worker_bindings,
              'workerProposalEqualsCandidate04': (AFTER / DECODER).read_bytes() == Path(return_report['candidate']['path']).read_bytes(),
              'workerProductionEqualsCandidate03': (BEFORE / DECODER).read_bytes() == Path(return_report['production']['path']).read_bytes(),
              'integrationReceipt': binding(RUN / 'evidence/PR43-review/R1-decoder-integration-01/receipt.json'),
              'buildNotRepeated': True, 'benchmarksNotRunOrValidated': True, 'browserExecuted': False, 'terrainExecuted': False}
    write('SNAPSHOT_AUDIT.json', output)
    write('RUNTIME_DELTA.json', {'before': runtime_before['treeSha256'], 'after': runtime_after['treeSha256'],
                               'changes': [item for item in changed if item['relativePath'] in runtime_after['files']],
                               'added': [item for item in added if item['relativePath'] in runtime_after['files']],
                               'removed': [item for item in removed if item['relativePath'] in runtime_before['files']]})
    print(json.dumps({'wholeTreeFilesBefore': len(files_before), 'wholeTreeFilesAfter': len(files_after),
                      'changed': [item['relativePath'] for item in changed], 'addedCount': len(added), 'removedCount': len(removed),
                      'runtime03': runtime_before['treeSha256'], 'runtime04': runtime_after['treeSha256'],
                      'runtimeFiles': len(runtime_after['files']), 'exactDecoderEmbeddings': embeddings,
                      'derivedBuildMetadata': expected_build == build_new,
                      'protectedOwnerChanges': {prefix: value['changed'] for prefix, value in protected_classes.items() if value['changed']}}))
    assert all(item['runtimeEqualsBothRetainedBuilds'] and item['runtimeMatchesReceipt'] and item['indexMatchesReceipt'] for item in build_bindings)
    assert runtime_after['treeSha256'] == EXPECTED_RUNTIME
    assert all(item['unchangedAndMatchesIntegration'] for item in protected)
    assert all(item['matchesReturn'] for item in worker_bindings)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
