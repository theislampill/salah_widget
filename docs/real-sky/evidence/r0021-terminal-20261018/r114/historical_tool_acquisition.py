from pathlib import Path
import datetime, hashlib, json, stat, urllib.request, zipfile

base = Path(__file__).resolve().parent / 'reference-tools-r114'
base.mkdir(exist_ok=True)
archive = base / 'zig-x86_64-windows-0.14.1.zip'
url = 'https://ziglang.org/download/0.14.1/zig-x86_64-windows-0.14.1.zip'
expected = '554f5378228923ffd558eac35e21af020c73789d87afeabf4bfd16f2e6feed2c'
assert not archive.exists(), 'Do not overwrite an earlier tool acquisition'
with urllib.request.urlopen(url, timeout=60) as response, archive.open('xb') as target:
    while chunk := response.read(1024 * 1024):
        target.write(chunk)
assert archive.stat().st_size == 82229343
assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
with zipfile.ZipFile(archive) as package:
    for entry in package.infolist():
        destination = (base / entry.filename).resolve()
        assert destination.is_relative_to(base.resolve())
        assert not stat.S_ISLNK(entry.external_attr >> 16)
    package.extractall(base)
record = {'schema': 'r0021-diagnostic-tool/v1', 'atUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'source': url, 'manifestSource': 'https://ziglang.org/download/index.json',
          'version': '0.14.1', 'archiveSha256': expected, 'bytes': archive.stat().st_size,
          'scope': 'Portable isolated diagnostic C-to-WASM compiler only. No host installation or product dependency.',
          'reason': 'Existing Windows clang20 has no WebAssembly target; Ubuntu has no clang/wasm linker.',
          'exe': str(base / 'zig-x86_64-windows-0.14.1' / 'zig.exe')}
(base / 'TOOL.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
