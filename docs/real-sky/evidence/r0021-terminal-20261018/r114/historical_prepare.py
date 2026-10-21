from pathlib import Path
import hashlib, json

o = Path(__file__).resolve().parent
root = Path(r'${REPO_ROOT}')
build = o / 'reference-tools-r114' / 'build'
assert not build.exists()
build.mkdir()
sha = lambda data: hashlib.sha256(data).hexdigest()
c = (root / 'moon/src/moon_kernel.c').read_bytes()
engine = (root / 'moon/src/moon-engine.mjs').read_bytes()
assert sha(c) == '919bf0b0a17ceb1ce3d3d7e0b5d9958bba3835b96e8558d6b518e7db1137f57f'
prior = json.loads((o / 'numerical/quadrature-r112/RESULT.json').read_bytes())
assert sha(engine) == prior['sources']['moon-engine.mjs']
assert c.count(b'[8192]') == 6 and c.count(b'radial*azimuth>8192') == 1
assert engine.count(b'radial*azimuth>8192') == 1
diagnostic_c = c.replace(b'[8192]', b'[16384]').replace(b'radial*azimuth>8192', b'radial*azimuth>16384')
diagnostic_engine = engine.replace(b'radial*azimuth>8192', b'radial*azimuth>16384')
(build / 'moon_kernel_reference.c').write_bytes(diagnostic_c)
(build / 'moon-engine-reference.mjs').write_bytes(diagnostic_engine)
zig = o / 'reference-tools-r114/zig-x86_64-windows-0.14.1/zig.exe'
command = [str(zig), 'cc', '-target', 'wasm32-freestanding', '-O2', '-fno-fast-math',
           '-ffp-contract=off', '-fno-builtin', '-nostdlib', '-Wl,--no-entry',
           '-Wl,--export-all', '-Wl,--allow-undefined', '-Wl,--initial-memory=4194304',
           '-Wl,--max-memory=536870912', str(build / 'moon_kernel_reference.c'),
           '-o', str(build / 'moon_kernel_reference.wasm')]
record = {'schema': 'r0021-diagnostic-build-plan/v1', 'sourceHead': '9df79b98d8dda7a0286b1b287dc03d1b4d760bdb',
          'originalKernelSha256': sha(c), 'originalEngineSha256': sha(engine),
          'diagnosticKernelSha256': sha(diagnostic_c), 'diagnosticEngineSha256': sha(diagnostic_engine),
          'changes': ['Six finite-source arrays8192->16384', 'C and isolated JS sample-product guard8192->16384'],
          'unchanged': 'Quality owner, material, geometry, assets, product files and shipped WASM',
          'command': command, 'compileTimeoutSeconds': 120,
          'control': 'Fail closed before reference if any64/256/1024/4096 receiver/coverage/projection hash or final input mask differs from r112.'}
(build / 'PLAN.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record))
