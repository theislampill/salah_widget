"""Read every immutable published payload object, without browser or product writes."""
import concurrent.futures, datetime, hashlib, json, subprocess, time, urllib.request, zlib
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parents[1]
COMMIT = 'ce46f4ce817320fa823e9b863c24ea59e3ca7d9b'
PREFIX = 'evidence/R000D/'
URL = 'https://raw.githubusercontent.com/theislampill/salah_widget/' + COMMIT + '/' + PREFIX

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    started = now()
    manifest_bytes = (BASE / 'publication/payload-manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    rows = list(manifest['files']) + [{
        'original': 'publication/payload-manifest.json', 'published': 'publication/payload-manifest.json',
        'originalBytes': len(manifest_bytes), 'publishedBytes': len(manifest_bytes),
        'originalSha256': sha(manifest_bytes), 'publishedSha256': sha(manifest_bytes), 'encoding': 'identity'}]
    remote = json.loads(subprocess.check_output([
        'gh', 'api', 'repos/theislampill/salah_widget/git/trees/' + COMMIT + '?recursive=1'], cwd=ROOT))
    if remote.get('truncated') or remote['sha'] != COMMIT:
        # The tree API returns the commit's tree SHA, not the commit identity.
        commit = json.loads(subprocess.check_output(['gh', 'api', 'repos/theislampill/salah_widget/git/commits/' + COMMIT], cwd=ROOT))
        if remote.get('truncated') or commit['sha'] != COMMIT or remote['sha'] != commit['tree']['sha']:
            raise RuntimeError('Remote tree identity or completeness failed')
    objects = {x['path']: x for x in remote['tree'] if x['type'] == 'blob' and x['path'].startswith(PREFIX)}
    expected = {PREFIX + row['published'] for row in rows}
    if set(objects) != expected:
        raise RuntimeError('Remote payload path set differs')
    for row in rows:
        data = (BASE / row['published']).read_bytes()
        git_sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        obj = objects[PREFIX + row['published']]
        if obj['sha'] != git_sha or obj['size'] != len(data) or sha(data) != row['publishedSha256']:
            raise RuntimeError('Committed/local payload identity failed: ' + row['published'])

    def read(row):
        result = {'published': row['published'], 'original': row['original'], 'url': URL + row['published'], 'startedUtc': now()}
        try:
            wire = hashlib.sha256(); original = hashlib.sha256(); size = 0; expanded = 0
            decoder = zlib.decompressobj(16 + zlib.MAX_WBITS) if row['encoding'] == 'gzip' else None
            request = urllib.request.Request(result['url'], headers={'Accept-Encoding': 'identity', 'User-Agent': 'R000D-immutable-evidence-readback'})
            with urllib.request.urlopen(request, timeout=60) as response:
                result['httpStatus'] = response.status
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk: break
                    wire.update(chunk); size += len(chunk)
                    raw = decoder.decompress(chunk) if decoder else chunk
                    original.update(raw); expanded += len(raw)
                if decoder:
                    tail = decoder.flush(); original.update(tail); expanded += len(tail)
                    if not decoder.eof or decoder.unused_data: raise RuntimeError('Incomplete or trailing gzip stream')
            result.update(publishedBytes=size, publishedSha256=wire.hexdigest(), originalBytes=expanded, originalSha256=original.hexdigest())
            result['passed'] = result['httpStatus'] == 200 and all(result[key] == row[key] for key in ('publishedBytes', 'publishedSha256', 'originalBytes', 'originalSha256'))
        except Exception as exc:
            result.update(passed=False, error=repr(exc))
        result['finishedUtc'] = now()
        return result

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(read, rows):
            results.append(result)
            if len(results) % 100 == 0: print(json.dumps({'read': len(results), 'failed': sum(not r['passed'] for r in results)}), flush=True)
    report = {'schema': 'r000d-immutable-publication-readback/v1', 'startedUtc': started, 'finishedUtc': now(),
              'commit': COMMIT, 'remoteTreeSha': remote['sha'], 'payloadManifestSha256': sha(manifest_bytes),
              'scope': 'All 696 payload objects plus their manifest were read through actual immutable raw HTTP URLs. Remote Git tree identities and path set matched. Gzip streams were independently hashed after decompression; no media was transformed or displayed.',
              'remoteTreePathsChecked': len(objects), 'httpObjectsChecked': len(results),
              'passed': all(r['passed'] for r in results), 'failed': [r['published'] for r in results if not r['passed']], 'results': results}
    output = BASE / 'publication/actual-public-readback.json'
    if output.exists(): raise RuntimeError('Refuse to overwrite an existing readback')
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    locations = {'schema': 'r000d-published-receipt-locations/v1', 'evidenceCommit': COMMIT, 'manifestUrl': URL + 'publication/payload-manifest.json',
                 'note': 'Original logical JSON paths in sealed indices resolve to these published gzip files. Decompress to the recorded original SHA-256. A failed receipt is retained evidence, not an accepted case.',
                 'receipts': [dict(row, url=URL + row['published']) for row in rows if row['original'].endswith('/receipt.json') or row['original'] in ('reviewed-candidate-certificate.json', 'native/a02-index.json', 'native/a03-index.json', 'native/a04-index.json')]}
    (BASE / 'publication/receipt-locations.json').write_text(json.dumps(locations, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'results'}), flush=True)
    if not report['passed']: raise SystemExit(1)

if __name__ == '__main__':
    main()
