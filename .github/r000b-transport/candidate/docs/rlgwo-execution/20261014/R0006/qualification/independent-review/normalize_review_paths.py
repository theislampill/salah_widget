"""Replace local-only locators in derived notes; never open acquisition payloads for writing."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = str(HERE.parent)


def normalize(value, changed):
    if isinstance(value, dict):
        return {key: normalize(item, changed) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item, changed) for item in value]
    if isinstance(value, str):
        for prefix in (PREFIX + '\\', PREFIX.replace('\\', '/') + '/'):
            if value.startswith(prefix):
                changed.append(True)
                return 'r0006-evidence/' + value[len(prefix):].replace('\\', '/')
    return value


def main():
    records = []
    for path in sorted(HERE.rglob('*.json')):
        if path.name == 'portable-path-review.json':
            continue
        original = path.read_bytes()
        value = json.loads(original)
        changed = []
        normalized = normalize(value, changed)
        if not changed:
            continue
        result = (json.dumps(normalized, indent=2) + '\n').encode('utf-8')
        assert json.loads(result) == normalized
        assert path.resolve().is_relative_to(HERE)
        path.write_bytes(result)
        records.append({'path': path.relative_to(HERE).as_posix(),
                        'locatorCount': len(changed),
                        'beforeSha256': hashlib.sha256(original).hexdigest(),
                        'afterSha256': hashlib.sha256(result).hexdigest()})
    packet = {'schema': 'r0006-independent-portable-locators/v1',
              'scope': 'Only derived review-note JSON locator strings changed. Native acquisitions, traces, media, sample pixels and their hashes are untouched. r0006-evidence references identify original acquisition locations through cases.json.',
              'filesChanged': len(records), 'records': records}
    (HERE / 'portable-path-review.json').write_text(json.dumps(packet, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'filesChanged': len(records), 'locatorsChanged': sum(row['locatorCount'] for row in records)}))


if __name__ == '__main__':
    main()
