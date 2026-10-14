"""Lossless R000B projection using the delivered R000C packaging convention."""
import hashlib
import io
import json
import lzma
from pathlib import Path
import tarfile

ROOT = Path(r'C:\Users\theis\.codex\worktrees\r000b-close\salah_widget')
EVIDENCE = Path(__file__).parent
DEST = EVIDENCE / 'public-projection'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    originals = []
    expected = set()

    def put(source, relative):
        data = source.read_bytes()
        target = DEST / relative
        packed = data
        if source.suffix == '.json' and len(data) > 100000:
            packed = lzma.compress(data, preset=6)
            assert lzma.decompress(packed) == data
            target = target.with_suffix('.json.xz')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(packed)
        path = target.relative_to(DEST).as_posix()
        expected.add(path)
        originals.append({'originalPath': Path(relative).as_posix(), 'path': path,
            'sha256': sha(packed), 'originalSha256': sha(data), 'originalBytes': len(data),
            'compression': 'xz' if target.suffix == '.xz' else 'none'})

    def put_image_archive(sources, relative):
        # Lossless deterministic chunks keep the evidence file count bounded.
        # Every original image and hash remains public.
        chunks=[];chunk=[];size=0
        for source,member in sources:
            if chunk and size+source.stat().st_size>48*1024*1024:
                chunks.append(chunk);chunk=[];size=0
            chunk.append((source,member));size+=source.stat().st_size
        if chunk:chunks.append(chunk)
        for i,chunk in enumerate(chunks):
            path=(relative/f'original-images-{i+1:02d}.tar.xz').as_posix()
            target=DEST/path;target.parent.mkdir(parents=True,exist_ok=True)
            rows=[]
            with lzma.open(target,'wb',preset=6) as packed:
                with tarfile.open(fileobj=packed,mode='w') as archive:
                    for source,member in chunk:
                        data=source.read_bytes();info=tarfile.TarInfo(member)
                        info.size=len(data);info.mtime=0;info.mode=0o644
                        archive.addfile(info,io.BytesIO(data))
                        rows.append({'originalPath':(relative/member).as_posix(),
                            'path':path,'member':member,'originalSha256':sha(data),
                            'originalBytes':len(data),'compression':'tar.xz'})
            digest=sha(target.read_bytes())
            for row in rows:row['sha256']=digest
            originals.extend(rows);expected.add(path)

    selection = json.loads((EVIDENCE / 'selection.json').read_bytes())
    for item in selection:
        source = EVIDENCE / item['source']
        assert source.is_dir(), source
        archived_images=[]
        for file in sorted(source.rglob('*')):
            if file.is_file() and file.suffix in {'.json', '.webm', '.png', '.jpg', '.txt', '.tap'}:
                relative=file.relative_to(source)
                if file.suffix in {'.png','.jpg'} and len(relative.parts)>1:
                    archived_images.append((file,relative.as_posix()))
                else:put(file, Path(item['destination']) / relative)
        put_image_archive(archived_images,Path(item['destination']))
    for folder in ['authority', 'fixture-v1', 'state-capture-fixture', 'motion-capture-fixture', 'recovery-diagnostic-fixture', 'recovery-handoff-source', 'handoff-capture-fixture', 'independent-review']:
        for file in sorted((EVIDENCE / folder).rglob('*')):
            if file.is_file() and file.suffix in {'.json', '.py', '.md', '.html', '.js', '.mjs', '.cjs', '.tap', '.txt', '.patch', '.png', '.jpg'}:
                put(file, Path(folder) / file.relative_to(EVIDENCE / folder))
    # Mutant source copies never enter the candidate; exact spans and hashes do.
    for file in sorted((EVIDENCE / 'mutants').glob('*')):
        if file.suffix in {'.json', '.tap'}:
            put(file, Path('mutants') / file.name)
    names = ['currentness.json', 'runtime.json', 'pre-native-candidate.json', 'native-toolchain.json',
        'v45-receipt-readback.json', 'test-receipts.json', 'historical-source-equivalence.json',
        'baseline-red.tap', 'baseline-observations.json', 'red.tap', 'red-observations.json',
        'red-qualified.tap', 'red-qualified-observations.json', 'green.tap', 'green-observations.json',
        'affected-regression.tap', 'independent-source-review.json', 'independent-b16-first-state-review.json', 'native-reconciliation.json',
        'native-verifier-negative-control.json', 'pixel-review.json', 'contrary-evidence.json',
        'accepted-currentness.json', 'acceptance-matrix.json', 'reviewed-candidate-certificate.json',
        'final-source-preflight.json', 'post-handoff-currentness.json', 'handoff-native-reconciliation.json',
        'qualified-candidate-preflight.json', 'final-native-dispositions.json', 'evidence-placement.json',
        'v1.txt', 'pre-recovery-investigation.patch']
    for name in names:
        file = EVIDENCE / name
        if file.exists():
            put(file, Path(name))
    for name in ['package_evidence.py', 'verify_projection.py', 'reconcile_handoff_currentness.py', 'verify_handoff_cases.py']:
        put(EVIDENCE / name, Path('qualification/tools') / name)
    for name in ['README.md', 'DESIGN.md', 'HANDOFF.md']:
        put(ROOT / name, Path('qualified-documents') / name)
    put(EVIDENCE / 'public-README.md', Path('README.md'))
    # Exact evidence bytes and raw TAP whitespace survive Git on Windows.
    attributes = b'* -text\n*.tap -whitespace\n*.diff -whitespace\n'
    (DEST / '.gitattributes').write_bytes(attributes)
    expected.add('.gitattributes')
    for name, obj in [('cases.json', {'schema': 'r000b-native-evidence/v1', 'acquisitions': selection}),
                      ('archive-map.json', {'schema': 'r000b-lossless-original-map/v1', 'files': originals})]:
        (DEST / name).write_text(json.dumps(obj, indent=2) + '\n', encoding='utf-8')
        expected.add(name)
    actual = {f.relative_to(DEST).as_posix() for f in DEST.rglob('*') if f.is_file()} - {'manifest.json'}
    assert actual == expected, {'unexpected': sorted(actual - expected), 'missing': sorted(expected - actual)}
    files = [{'path': p, 'bytes': (DEST / p).stat().st_size, 'sha256': sha((DEST / p).read_bytes())}
             for p in sorted(expected)]
    manifest = {'schema': 'r000b-public-manifest/v1', 'files': files,
        'fileCount': len(files), 'totalBytes': sum(x['bytes'] for x in files)}
    (DEST / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'files'}))


if __name__ == '__main__':
    main()
