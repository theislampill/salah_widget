"""Update the retained projection's final metadata without recompressing original images."""
from pathlib import Path
import hashlib
import json
import lzma

E = Path(__file__).parent
P = E / 'public-projection'
sha = lambda b: hashlib.sha256(b).hexdigest()
old = json.loads((P / 'manifest.json').read_bytes())
mapping = json.loads((P / 'archive-map.json').read_bytes())
rows = {r['originalPath']: r for r in mapping['files']}
changed = []

def put(source, relative):
    data = source.read_bytes()
    target = Path(relative)
    packed = data
    if source.suffix == '.json' and len(data) > 100000:
        packed = lzma.compress(data, preset=6)
        assert lzma.decompress(packed) == data
        target = target.with_suffix('.json.xz')
    key = Path(relative).as_posix()
    path = target.as_posix()
    if key in rows:
        assert rows[key]['path'] == path, 'Changed compression requires explicit disposition.'
    output = P / path
    if not output.exists() or output.read_bytes() != packed:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(packed)
        changed.append(path)
    rows[key] = {'originalPath': key, 'path': path, 'sha256': sha(packed),
                 'originalSha256': sha(data), 'originalBytes': len(data),
                 'compression': 'xz' if target.suffix == '.xz' else 'none'}

names = ['acceptance-matrix.json', 'reviewed-candidate-certificate.json',
         'contrary-evidence.json', 'pixel-review.json', 'final-native-dispositions.json',
         'evidence-placement.json']
for name in names:
    put(E / name, name)
for file in sorted((E / 'independent-review').rglob('*')):
    if file.is_file() and file.suffix in {'.json', '.py', '.md', '.html', '.js', '.mjs', '.cjs', '.tap', '.txt', '.patch', '.png', '.jpg'}:
        put(file, file.relative_to(E))
put(E / 'public-README.md', 'README.md')
put(E / 'package_evidence.py', 'qualification/tools/package_evidence.py')
put(E / 'sync_final_metadata.py', 'qualification/tools/sync_final_metadata.py')
(P / 'cases.json').write_text(json.dumps({'schema': 'r000b-native-evidence/v1',
    'acquisitions': json.loads((E / 'selection.json').read_bytes())}, indent=2) + '\n', encoding='utf-8')
mapping['files'] = list(rows.values())
(P / 'archive-map.json').write_text(json.dumps(mapping, indent=2) + '\n', encoding='utf-8')
expected = {r['path'] for r in rows.values()} | {'.gitattributes', 'cases.json', 'archive-map.json'}
actual = {f.relative_to(P).as_posix() for f in P.rglob('*') if f.is_file()} - {'manifest.json'}
assert actual == expected, (sorted(actual - expected), sorted(expected - actual))
files = [{'path': p, 'bytes': (P / p).stat().st_size, 'sha256': sha((P / p).read_bytes())} for p in sorted(actual)]
manifest = {'schema': old['schema'], 'files': files, 'fileCount': len(files),
            'totalBytes': sum(r['bytes'] for r in files)}
(P / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
receipt = {'status': 'METADATA_SYNCHRONIZED_FULL_VERIFICATION_REQUIRED', 'changed': changed,
           'manifestSha256': sha((P / 'manifest.json').read_bytes()),
           'files': len(files), 'totalBytes': manifest['totalBytes']}
(E / 'metadata-sync.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt))
