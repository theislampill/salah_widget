"""Verify membership, bytes and lossless custody of the bounded R000B packet."""
import hashlib
import json
import lzma
from pathlib import Path
import sys
import tarfile

root = Path(sys.argv[1])
manifest = json.loads((root / 'manifest.json').read_bytes())
actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()} - {'manifest.json'}
assert actual == {r['path'] for r in manifest['files']}
assert len(actual) == manifest['fileCount']
assert sum(r['bytes'] for r in manifest['files']) == manifest['totalBytes']
for row in manifest['files']:
    data = (root / row['path']).read_bytes()
    assert len(data) == row['bytes']
    assert hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
archive = json.loads((root / 'archive-map.json').read_bytes())
assert len({r['originalPath'] for r in archive['files']}) == len(archive['files'])
packed_images={}
for row in archive['files']:
    if row['compression']=='tar.xz':packed_images.setdefault(row['path'],[]).append(row)
for path,rows in packed_images.items():
    data=(root/path).read_bytes();digest=hashlib.sha256(data).hexdigest()
    assert all(row['sha256']==digest for row in rows),path
    expected={row['member']:row for row in rows};assert len(expected)==len(rows)
    with tarfile.open(root/path,'r:xz') as packed:
        members=packed.getmembers()
        assert len(members)==len(expected) and {m.name for m in members}==set(expected),path
        for member in members:
            assert member.isfile() and not member.name.startswith('/') and '..' not in Path(member.name).parts
            original=packed.extractfile(member).read();row=expected[member.name]
            assert len(original)==row['originalBytes']
            assert hashlib.sha256(original).hexdigest()==row['originalSha256'],row['originalPath']
for row in archive['files']:
    if row['compression']=='tar.xz':continue
    data = (root / row['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == row['sha256']
    original = lzma.decompress(data) if row['compression'] == 'xz' else data
    assert len(original) == row['originalBytes']
    assert hashlib.sha256(original).hexdigest() == row['originalSha256'], row['path']
print(json.dumps({'status': 'PASS', 'files': len(actual), 'originals': len(archive['files']),
                  'manifestSha256': hashlib.sha256((root / 'manifest.json').read_bytes()).hexdigest()}))
