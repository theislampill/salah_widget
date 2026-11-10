"""Lossless public projection of R000C originals; no source/recording mutation."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    args = p.parse_args()
    evidence = args.evidence.resolve()
    dest = args.root.resolve() / 'docs/rlgwo-execution/20261014/R000C'
    dest.mkdir(parents=True, exist_ok=True)
    acquisitions = []
    originals = []

    def put(source, relative):
        data = source.read_bytes()
        target = dest / relative
        if source.suffix == '.json' and len(data) > 100000:
            packed = lzma.compress(data, preset=6)
            assert lzma.decompress(packed) == data
            target = target.with_suffix('.json.xz')
        else:
            packed = data
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(packed)
        entry = {'path': target.relative_to(dest).as_posix(), 'sha256': sha(packed),
                 'originalSha256': sha(data), 'originalBytes': len(data),
                 'compression': 'xz' if target.suffix == '.xz' else 'none'}
        originals.append({'originalPath': Path(relative).as_posix(), **entry})
        return entry

    selection = json.loads((evidence / 'selection.json').read_bytes())
    for item in selection:
        source = evidence / item['source']
        members = []
        for file in sorted(source.rglob('*')):
            if file.is_file() and file.suffix in {'.json', '.webm', '.png', '.jpg', '.md', '.txt'}:
                members.append(put(file, Path(item['destination']) / file.relative_to(source)))
        acquisitions.append({**item, 'members': members})
    for folder in ['authority', 'fixture-preflight', 'fixture-v1', 'fixture-v2', 'fixture-v3', 'fixture-v4',
                   'independent-review', 'native-activity-logs', 'native-active-logs']:
        for file in sorted((evidence / folder).rglob('*')):
            # The owner order is private execution authority, not public evidence.
            if folder == 'authority' and file.name == 'owner-order.txt':
                continue
            if file.is_file() and file.suffix in {'.json', '.py', '.md', '.html', '.cjs', '.png', '.jpg', '.tap', '.txt', '.moz_log'}:
                put(file, Path(folder) / file.relative_to(evidence / folder))
    # Official browser source remains at the immutable URLs; retain acquisition
    # digests and installed comparison limits without duplicating third-party code.
    for name in ['sources.json', 'inspection.json']:
        put(evidence / 'firefox-source-inspection' / name, Path('firefox-source-inspection') / name)
    for name in ['visibility_probe.py', 'activity_override_probe.py', 'refresh_bindings.py', 'verify_projection.py']:
        file = evidence / name
        if file.exists():
            put(file, Path('qualification/tools') / name)
    for file in sorted((evidence / 'mutants').glob('*')):
        if file.suffix in {'.json', '.tap'}:
            put(file, Path('mutants') / file.name)
    names = ['.gitattributes', 'currentness.json', 'preservation-reuse.json', 'fixture-adaptation.json', 'native-environment.json',
             'baseline-weather.tap', 'baseline-hotfix.tap', 'original-related-controls.tap', 'v1.txt',
             'authored-weather.tap', 'authored-test-limitation.json', 'firefox-headless-rejection.json',
             'firefox-headed-rejection.json', 'firefox-single-document-rejections.json',
             'firefox-night-rejections.json', 'single-document-driver.diff', 'boundary-observer.diff', 'host-watch-wait.diff',
             'nonfinite-reporting.diff', 'nonfinite-encoding-control.json',
             'consumer-reconciliation-chromium.json',
             'consumer-reconciliation-firefox.json', 'consumer-reconciliation-firefox-day.json',
             'consumer-reconciliation-firefox-night.json',
             'consumer-reconciliation-firefox-boundary-pilot.json',
             'consumer-reconciliation-firefox-boundary-preferences.json',
             'boundary-pilot-primary-review.json', 'boundary-preferences-primary-review.json',
             'final-source-preflight.json',
             'docs-review.json', 'pixel-review.json', 'fixture-review.json',
             'acceptance-matrix.json', 'reviewed-candidate-certificate.json']
    for name in names:
        file = evidence / name
        if file.exists():
            put(file, Path(name))
    put(Path(__file__), Path('qualification/tools/package_evidence.py'))
    if (evidence / 'public-README.md').is_file():
        put(evidence / 'public-README.md', Path('README.md'))
    (dest / 'cases.json').write_text(json.dumps({'schema': 'r000c-native-evidence/v1', 'acquisitions': acquisitions}, indent=2) + '\n', encoding='utf8')
    (dest / 'archive-map.json').write_text(json.dumps({'schema': 'r000c-lossless-original-map/v1',
        'files': originals}, indent=2) + '\n', encoding='utf8')
    files = [{'path': f.relative_to(dest).as_posix(), 'bytes': f.stat().st_size, 'sha256': sha(f.read_bytes())}
             for f in sorted(dest.rglob('*')) if f.is_file() and f != dest / 'manifest.json']
    (dest / 'manifest.json').write_text(json.dumps({'schema': 'r000c-public-manifest/v1', 'files': files,
        'fileCount': len(files), 'totalBytes': sum(x['bytes'] for x in files)}, indent=2) + '\n', encoding='utf8')
    print('Projected', len(acquisitions), 'acquisitions;', len(files), 'files;', sum(x['bytes'] for x in files), 'bytes')


if __name__ == '__main__':
    main()
