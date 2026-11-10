"""Reconcile retained R000C acquisition identities without executing browsers."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--evidence', type=Path, required=True)
args = parser.parse_args()
root, evidence = args.root.resolve(), args.evidence.resolve()
current = read(root / 'tests/rlgwo/R000C-cases.json')
for rel, expected in current['sourceFiles'].items():
    assert sha(root / rel) == expected, rel
versions = {}
packets = {}
for folder in ['fixture-preflight', 'fixture-v1', 'fixture-v2', 'fixture-v3', 'fixture-v4', None]:
    packet_path = evidence / folder / 'R000C-cases.json' if folder else root / 'tests/rlgwo/R000C-cases.json'
    driver_path = evidence / folder / 'run_r000c_native.py' if folder else root / 'tools/qa/run_r000c_native.py'
    packet = read(packet_path)
    assert packet['sourceFiles']['tools/qa/run_r000c_native.py'] == sha(driver_path)
    assert packet['runtime'] == current['runtime']
    key = sha(packet_path)
    versions[key] = {
        'packet': f'{folder}/R000C-cases.json' if folder else '../../../../tests/rlgwo/R000C-cases.json',
        'driver': f'{folder}/run_r000c_native.py' if folder else '../../../../tools/qa/run_r000c_native.py',
        'driverSha256': sha(driver_path),
    }
    packets[key] = packet

acquisitions = []
for item in read(evidence / 'selection.json'):
    directory = evidence / item['source']
    results = read(directory / 'results.json')
    packet = packets[results['casesSha256']]
    version = versions[results['casesSha256']]
    assert results['driverSha256'] == version['driverSha256']
    assert results['runtime'] == current['runtime']
    assert results['wrapperSha256'] == current['sourceFiles']['tests/rlgwo/weather-browser-fixture.html']
    row = {
        'acquisition': item['source'], 'resultsSha256': sha(directory / 'results.json'),
        'packetSha256': results['casesSha256'], 'version': version,
        'wrapperSha256': results['wrapperSha256'],
        'servedHtmlSha256': results.get('servedHtmlSha256'),
        'documentMode': results.get('documentMode'),
        'observerMode': results.get('observerMode'),
        'watchWaitMode': results.get('watchWaitMode'),
        'qualification': item['qualification'],
        'reportedRuntimeUnchanged': results.get('runtimeUnchanged'),
        'cases': [],
    }
    for case_dir in sorted(directory.glob('R000C-*')):
        if not case_dir.is_dir():
            continue
        inp = read(case_dir / 'case-input.json')
        assert inp == next(x for x in packet['cases'] if x['id'] == case_dir.name)
        case = {'id': case_dir.name, 'inputSha256': sha(case_dir / 'case-input.json')}
        receipt_path = case_dir / 'receipt.json'
        if receipt_path.is_file():
            receipt = read(receipt_path)
            report_case = next(x for x in results['cases'] if x['id'] == case_dir.name)
            assert report_case['receiptSha256'] == sha(receipt_path)
            video = receipt['video']
            assert video['sha256'] == sha(case_dir / video['file'])
            case.update({'receiptSha256': sha(receipt_path), 'videoSha256': video['sha256'],
                         'browser': receipt['browser'], 'semanticStatus': receipt['status'],
                         'watchCount': len(receipt.get('watches', []))})
        else:
            # Only the explicitly retained reporter abort has no final receipt.
            assert (directory / 'serialization-failure.json').is_file()
            case.update({'receiptSha256': None, 'semanticStatus': 'INCOMPLETE_SERIALIZATION_FAILURE',
                         'partialVideos': [{'path': p.relative_to(case_dir).as_posix(), 'sha256': sha(p)}
                                           for p in sorted((case_dir / 'video').glob('*.webm'))]})
        row['cases'].append(case)
    for name in ['diagnostic-binding.json', 'activity-override-binding.json']:
        if (directory / name).is_file():
            row[name] = {'sha256': sha(directory / name), 'value': read(directory / name)}
    acquisitions.append(row)

result = {
    'schema': 'r000c-fixture-bindings/v2', 'candidateBase': current['sourceCommit'],
    'runtime': current['runtime'], 'sourceFiles': current['sourceFiles'],
    'packetVersions': versions, 'acquisitions': acquisitions,
    'status': 'PASS_IDENTITY_BINDINGS_ONLY',
    'limitations': [
        'Identity reconciliation is not semantic, pixel, motion or acceptance qualification.',
        'Canonical inputs are synthetic native-fetch/Response controls, not live provider observations.',
        'Failed and diagnostic acquisitions retain their original status and zero unsupported credit.',
        'Boundary qaState reads can disturb presentation or adopt a pending lunar preview; no unique render-to-frame join is claimed.',
        'The serialization abort has no completed receipt. Its partial original video is inventoried, not reconstructed.',
        'Activity override affects only the one diagnostic launch; it is not part of the qualification driver or product.',
        'Missing report fields from earlier driver versions remain null here; their actual code and prior independent reviews retain the original mode evidence.',
    ],
}
(evidence / 'fixture-review.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
print('Bound', len(acquisitions), 'acquisitions;', sum(len(x['cases']) for x in acquisitions), 'case directories;', len(versions), 'driver/packet versions')
