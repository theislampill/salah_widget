"""Independent offline final-candidate reconciliation; writes only beside this script."""
from pathlib import Path
import ast
import hashlib
import json
import lzma
import subprocess

REVIEW = Path(__file__).resolve().parent
EVIDENCE = REVIEW.parent
ROOT = EVIDENCE.parent / 'salah_widget'
PUBLIC = ROOT / 'docs/rlgwo-execution/20261014/R000C'
BASE = '7827099dff3c9bc5ecb1b7a67dc4c25414bcfb69'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def digest(path):
    return sha(path.read_bytes())

def strict(raw):
    def reject(value):
        raise ValueError('Non-JSON number: ' + value)
    def pairs(rows):
        result = {}
        for key, value in rows:
            assert key not in result, ('duplicate JSON key', key)
            result[key] = value
        return result
    return json.loads(raw, parse_constant=reject, object_pairs_hook=pairs)

def read(path):
    return strict(path.read_bytes())

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

def contained(path, directory):
    result = path.resolve()
    assert result.is_relative_to(directory.resolve()), path
    return result

manifest = read(PUBLIC / 'manifest.json')
archive = read(PUBLIC / 'archive-map.json')
cases = read(PUBLIC / 'cases.json')
expected = {r['path'] for r in manifest['files']} | {'manifest.json'}
actual = {p.relative_to(PUBLIC).as_posix() for p in PUBLIC.rglob('*') if p.is_file()}
assert expected == actual
assert len(manifest['files']) == len(expected) - 1 == manifest['fileCount']
assert manifest['totalBytes'] == sum(r['bytes'] for r in manifest['files'])
for row in manifest['files']:
    data = contained(PUBLIC / row['path'], PUBLIC).read_bytes()
    assert len(data) == row['bytes'] and sha(data) == row['sha256'], row['path']
assert len(archive['files']) == len({r['originalPath'] for r in archive['files']})
assert len(archive['files']) == len({r['path'] for r in archive['files']})
assert {r['path'] for r in archive['files']} | {'cases.json', 'archive-map.json', 'manifest.json'} == actual

mapping = {r['originalPath']: r for r in archive['files']}
raw_hashes = {}
json_count = compressed = local_path_count = 0
owner = (EVIDENCE / 'authority/owner-order.txt').read_bytes()
private_title = b'OWNER EXECUTION' + b' ORDER'
for logical, row in mapping.items():
    packed = contained(PUBLIC / row['path'], PUBLIC).read_bytes()
    assert sha(packed) == row['sha256']
    assert row['compression'] in ('xz', 'none')
    raw = lzma.decompress(packed) if row['compression'] == 'xz' else packed
    compressed += row['compression'] == 'xz'
    assert sha(raw) == row['originalSha256'] and len(raw) == row['originalBytes']
    assert private_title not in raw and owner not in raw, logical
    assert 'authority/owner-order.txt' != logical
    if logical == 'README.md':
        original = EVIDENCE / 'public-README.md'
    elif logical.startswith('qualification/tools/'):
        original = EVIDENCE / Path(logical).name
    else:
        original = contained(EVIDENCE / logical, EVIDENCE)
    assert original.is_file(), ('missing private original', logical)
    assert raw == original.read_bytes(), ('public/private byte mismatch', logical)
    if logical.endswith('.json'):
        strict(raw)
        json_count += 1
    if logical.endswith(('.json', '.md', '.py', '.txt', '.tap', '.diff', '.moz_log')):
        local_path_count += b'C:\\Users\\' in raw or b'C:\\\\Users\\\\' in raw
    raw_hashes[logical] = sha(raw)

selection = read(EVIDENCE / 'selection.json')
assert len(selection) == 15 == len(cases['acquisitions'])
selected_sources = {r['source'] for r in selection}
discovered_sources = {p.relative_to(EVIDENCE).as_posix() for parent in ('native', 'native-initial')
                      for p in (EVIDENCE / parent).iterdir() if p.is_dir() and (p / 'results.json').is_file()}
assert selected_sources == discovered_sources
native_extensions = {'.json', '.webm', '.png', '.jpg', '.md', '.txt'}
acquisition_rows = []
for selected, published in zip(selection, cases['acquisitions']):
    assert {k: published[k] for k in selected} == selected
    directory = EVIDENCE / selected['source']
    all_files = [p for p in directory.rglob('*') if p.is_file()]
    excluded = [p.relative_to(directory).as_posix() for p in all_files if p.suffix not in native_extensions]
    assert not excluded, (selected['source'], excluded)
    originals = {str(Path(selected['destination']) / p.relative_to(directory)).replace('\\', '/')
                 for p in all_files}
    members = {r['path']: r for r in published['members']}
    assert {mapping[logical]['path'] for logical in originals} == set(members)
    for logical in originals:
        expected_member = {k: v for k, v in mapping[logical].items() if k != 'originalPath'}
        assert members[expected_member['path']] == expected_member
    acquisition_rows.append({'path': selected['source'], 'files': len(all_files),
                             'qualification': selected['qualification']})

preflight = read(EVIDENCE / 'final-source-preflight.json')
certificate = read(EVIDENCE / 'reviewed-candidate-certificate.json')
packet = read(ROOT / 'tests/rlgwo/R000C-cases.json')
bindings = read(EVIDENCE / 'fixture-review.json')
assert git('rev-parse', 'HEAD').decode().strip() == BASE
assert git('branch', '--show-current').decode().strip() == 'codex/r000c-close-20261014'
assert preflight['base'] == certificate['sourceBase'] == packet['sourceCommit'] == bindings['candidateBase'] == BASE
assert certificate['candidateFiles'] == preflight['files']
assert preflight['runtime'] == packet['runtime'] == bindings['runtime']
assert certificate['runtimeSha256'] == packet['runtime']['treeSha256']
assert len(packet['runtime']['files']) == 135 == certificate['runtimeFiles']
runtime_records = []
for rel, identity in sorted(packet['runtime']['files'].items()):
    raw = (ROOT / rel).read_bytes()
    assert len(raw) == identity['bytes'] and sha(raw) == identity['sha256'], rel
    assert git('show', BASE + ':' + rel) == raw, ('base runtime drift', rel)
    runtime_records.append(identity['sha256'] + '  ' + rel + '\n')
assert sha(''.join(runtime_records).encode()) == packet['runtime']['treeSha256']
for rel, expected_sha in preflight['files'].items():
    assert digest(ROOT / rel) == expected_sha, rel
for rel, expected_sha in packet['sourceFiles'].items():
    assert digest(ROOT / rel) == expected_sha, rel
changed = set(git('diff', '--name-only', BASE).decode().splitlines())
untracked = set(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
non_projection = {p for p in changed | untracked if not p.startswith('docs/rlgwo-execution/20261014/R000C/')}
assert non_projection == set(preflight['files']), non_projection

versions = {}
for packet_hash, version in bindings['packetVersions'].items():
    current = version['packet'].startswith('../../../../')
    packet_path = ROOT / 'tests/rlgwo/R000C-cases.json' if current else EVIDENCE / version['packet']
    driver_path = ROOT / 'tools/qa/run_r000c_native.py' if current else EVIDENCE / version['driver']
    assert digest(packet_path) == packet_hash
    assert digest(driver_path) == version['driverSha256']
    data = read(packet_path)
    assert data['sourceFiles']['tools/qa/run_r000c_native.py'] == version['driverSha256']
    assert data['runtime'] == packet['runtime']
    if not current:
        assert raw_hashes[version['packet']] == packet_hash
        assert raw_hashes[version['driver']] == version['driverSha256']
    ast.parse(driver_path.read_text(encoding='utf8'))
    versions[packet_hash] = data
assert len(versions) == 6

case_count = receipts = videos = indexes = 0
for acquisition in bindings['acquisitions']:
    directory = EVIDENCE / acquisition['acquisition']
    results = read(directory / 'results.json')
    assert digest(directory / 'results.json') == acquisition['resultsSha256']
    assert results['casesSha256'] == acquisition['packetSha256']
    assert results['driverSha256'] == acquisition['version']['driverSha256']
    assert results['runtime'] == packet['runtime']
    assert results['wrapperSha256'] == packet['sourceFiles']['tests/rlgwo/weather-browser-fixture.html']
    used_packet = versions[acquisition['packetSha256']]
    declared = {r['id']: r for r in used_packet['cases']}
    for case in acquisition['cases']:
        case_count += 1
        case_dir = directory / case['id']
        assert read(case_dir / 'case-input.json') == declared[case['id']]
        assert digest(case_dir / 'case-input.json') == case['inputSha256']
        if case['receiptSha256']:
            receipts += 1
            receipt_path = case_dir / 'receipt.json'
            assert digest(receipt_path) == case['receiptSha256']
            receipt = read(receipt_path)
            assert receipt['status'] == case['semanticStatus']
            assert receipt['browser'] == case['browser']
            assert receipt['video']['sha256'] == case['videoSha256']
            assert digest(case_dir / receipt['video']['file']) == case['videoSha256']
            videos += 1
            index_path = case_dir / 'pixel-review/index.json'
            if index_path.is_file():
                index = read(index_path)
                assert index['videoSha256'] == case['videoSha256']
                assert index['receiptSha256'] == case['receiptSha256']
                assert index['frameCount'] == len(index['frames'])
                indexes += 1
        else:
            assert acquisition['acquisition'] == 'native/firefox-reduced-host-wait'
            assert case['semanticStatus'] == 'INCOMPLETE_SERIALIZATION_FAILURE'
            for video in case['partialVideos']:
                assert digest(case_dir / video['path']) == video['sha256']
                videos += 1
assert case_count == 30 and receipts == 29 and videos == 30

assessment = read(EVIDENCE / 'authority/accepted-assessment.json')
matrix = read(EVIDENCE / 'acceptance-matrix.json')
assert matrix['originalRequirementMatrix'] == assessment['requirementMatrix']
assert matrix['originalMatrixSha256'] == digest(EVIDENCE / 'authority/accepted-assessment.json')
assert [r['id'] for r in matrix['dispositions']] == ['C%02d' % i for i in range(1, 19)]
currentness = read(EVIDENCE / 'currentness.json')
assert len(currentness['acceptedRows']) == 13 and len(currentness['tests']) == 5
for test in currentness['tests']:
    assert digest(ROOT / test['path']) == test['priorSha256'] == test['currentSha256']
preserved_files = 0
for control in read(EVIDENCE / 'preservation-reuse.json')['controls']:
    for rel, expected_sha in control['files'].items():
        assert digest(ROOT / rel) == expected_sha, rel
        preserved_files += 1

mutants = read(EVIDENCE / 'mutants/receipt.json')
root_bytes = (ROOT / 'index.html').read_bytes()
assert mutants['sourceSha256'] == sha(root_bytes)
assert mutants['oracleSha256'] == digest(ROOT / 'tests/r000c-weather.test.cjs')
for mutation in mutants['mutations']:
    before, after = mutation['before'].encode(), mutation['after'].encode()
    assert root_bytes.count(before) == 1
    assert sha(root_bytes.replace(before, after, 1)) == mutation['afterSha256']
    assert mutation['status'] == 'KILLED_BY_ORIGINAL_ASSERTION'
    for role, code in [('original', 0), ('mutant', 1), ('positive', 0)]:
        assert mutation[role]['exitCode'] == code
        assert digest(EVIDENCE / 'mutants' / mutation[role]['log']) == mutation[role]['sha256']
assert len(mutants['mutations']) == 4

check = {
    'schema': 'r000c-independent-final-candidate-integrity/v1',
    'status': 'PASS_OFFLINE_IDENTITIES_AND_LOSSLESS_PROJECTION',
    'base': BASE,
    'branch': 'codex/r000c-close-20261014',
    'sourceFiles': preflight['files'],
    'runtimeSha256': packet['runtime']['treeSha256'],
    'runtimeFilesEqualBase': 135,
    'projection': {'manifestSha256': digest(PUBLIC / 'manifest.json'),
        'archiveMapSha256': digest(PUBLIC / 'archive-map.json'),
        'files': len(actual), 'manifestPayloadFiles': manifest['fileCount'],
        'bytesExcludingManifest': manifest['totalBytes'], 'originalsByteEqualPrivate': len(mapping),
        'strictJsonOriginals': json_count, 'compressedOriginals': compressed,
        'completeAcquisitions': len(acquisition_rows), 'caseDirectories': case_count,
        'completeReceipts': receipts, 'originalVideosIncludingAbort': videos,
        'receiptBoundFrameIndexes': indexes, 'fixturePacketDriverVersions': len(versions)},
    'privacy': {'privateOwnerOriginalExcluded': True,
        'privateOwnerTitleAndFullBytesAbsent': True,
        'localPathBearingTextFilesRetained': local_path_count,
        'limit': 'Original execution paths remain deliberately visible in receipts/scripts. This checks owner-order exclusion, not anonymization.'},
    'originalMatrixRowsUnchanged': 18,
    'originalRegressionFilesUnchanged': 5,
    'retainedPreservationFilesVerified': preserved_files,
    'mutantsReconstructExactAfterHashes': 4,
    'acquisitions': acquisition_rows,
    'limits': ['No browser replay, new frame decode, source edit, Git mutation or network call.',
               'Prior independent source/pixel/motion judgments are reused at verified unchanged identities.',
               'All failed declared watches remain failed; no whole-video or clean reduced30s claim.',
               'Local evidence review is not exact public PR-head, authority, delivery or closure proof.']
}
(REVIEW / 'final-candidate-integrity.json').write_text(json.dumps(check, indent=2) + '\n', encoding='utf8')
print(json.dumps({k: v for k, v in check.items() if k not in ('sourceFiles', 'acquisitions')}, indent=2))
