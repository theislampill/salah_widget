"""Verify the lossless R000C public projection without running its consumers."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def invalid(value):
        raise ValueError('Non-JSON numeric constant: ' + value)
    return json.loads(data, parse_constant=invalid)


p = argparse.ArgumentParser(description=__doc__)
p.add_argument('artifact', type=Path)
p.add_argument('--receipt', type=Path, required=True)
args = p.parse_args()
root, receipt = args.artifact.resolve(), args.receipt.resolve()
assert not receipt.is_relative_to(root), 'Write verification receipt outside the artifact'
manifest = strict_json((root / 'manifest.json').read_bytes())
mapping = strict_json((root / 'archive-map.json').read_bytes())
actual_paths = {f.relative_to(root).as_posix() for f in root.rglob('*') if f.is_file()}
expected_paths = {f['path'] for f in manifest['files']} | {'manifest.json'}
assert actual_paths == expected_paths, 'Manifest membership mismatch'
for row in manifest['files']:
    path = (root / row['path']).resolve()
    assert path.is_relative_to(root)
    data = path.read_bytes()
    assert len(data) == row['bytes'] and sha(data) == row['sha256'], row['path']
assert manifest['fileCount'] == len(manifest['files'])
assert manifest['totalBytes'] == sum(f['bytes'] for f in manifest['files'])
assert {f['path'] for f in mapping['files']} | {'cases.json', 'archive-map.json', 'manifest.json'} == actual_paths
assert len({f['originalPath'] for f in mapping['files']}) == len(mapping['files'])
json_count = 0
for row in mapping['files']:
    path = (root / row['path']).resolve()
    assert path.is_relative_to(root)
    stored = path.read_bytes()
    assert sha(stored) == row['sha256']
    raw = lzma.decompress(stored) if row['compression'] == 'xz' else stored
    assert len(raw) == row['originalBytes'] and sha(raw) == row['originalSha256'], row['originalPath']
    private_title = b'OWNER EXECUTION' + b' ORDER'
    assert private_title not in raw, 'Private owner authority was copied'
    if row['originalPath'].endswith('.json'):
        strict_json(raw)
        json_count += 1
result = {'schema': 'r000c-public-projection-verification/v1', 'status': 'PASS',
          'manifestSha256': sha((root / 'manifest.json').read_bytes()),
          'archiveMapSha256': sha((root / 'archive-map.json').read_bytes()),
          'fileCount': len(actual_paths), 'originalsVerified': len(mapping['files']),
          'strictJsonOriginals': json_count,
          'scope': 'Exact file membership, hashes, lossless decompression, strict JSON and private owner-order exclusion; no semantic or visual qualification.'}
receipt.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
print(json.dumps(result))
