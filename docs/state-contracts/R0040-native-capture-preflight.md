# R0040: revised single-cell native capture preflight

## Disposition and source identities

The six historical inputs and both published patches were materialized and checked
offline. The revised renderer, geometry, gain profile and genuine main match the
unchanged capture pins. **Native capture and native verification are NOT RUN.**
This record authorizes no policy choice, production change, acceptance or custody
claim about the original private packs. See [R0040](R0040.md).

The [complete source and preparation receipt](evidence/R0040/native-capture-preflight.json)
contains each Git blob ID, SHA-256, byte count, both patch stages, the complete
177-file main runtime manifest, controls and the planned native argv. Its source
revisions are:

| Role | Commit |
|---|---|
| Published recipe and patches | `55d1b3edb66d2c35679707120b01ee1d3455e4a3` |
| Historical precipitation inputs | `4029d2f67f5a880c8ad889443bb7557d96022c45` |
| Genuine main | `df644ef60156b67b5c487395176369bcec7a0d7b` |

The first local Git-object attempt found only the helper. The other five blob
reads failed with exit 128, with lazy fetching disabled. Those failures remain in
the receipt. Read-only GitHub file retrieval at the exact historical commit then
returned base64 bytes for all five; recomputed Git blob IDs matched the existing
commit tree. Neither a text reconstruction nor newline normalization was used.

## Exact acquisition population

Acquire these six paths at the historical commit, preserving bytes:

```text
tools/qa/precip_eval_lib.cjs
tools/qa/precip_models_geom.js
tools/qa/precip_declared_gain.json
tools/qa/precip_models.js
tools/qa/precip_models_capture.cjs
tools/qa/precip_models_post.py
```

The last two are required by the complete declared-gain patch. The new capture
recipe does not execute them. Applying only the renderer/profile hunks would not
reproduce this full-patch preparation. The first four supply the new recipe's
actual historical runtime inputs.

For research sparse acquisition, add the exact files below if the current
checkout retains only `phase1-options.patch.gz`. Existing full `tools/` and
`tests/` inclusions already provide the code inputs listed in the receipt.

```text
/docs/state-contracts/evidence/R0040/declared-gain.patch.gz
/docs/state-contracts/evidence/R0040/layer-study.patch.gz
/docs/state-contracts/evidence/R0040/parameter-inventory.json
/docs/state-contracts/evidence/R0040/parameter-source-fixture.json.gz
```

The first two are needed to prepare the capture sources. The latter two support
the unchanged offline parameter controls and independently recorded profile
identity. Acquire this preflight receipt from its reviewed commit separately;
it did not exist at the immutable recipe revision.

## Guarded preparation recipe

Run only offline preparation here. `MANIFEST` is the reviewed receipt above;
`RESEARCH` is the immutable published recipe checkout; `HISTORICAL` is the six-file
acquisition; `MAIN` is the independently prepared, clean genuine main checkout.
`NEW_WORK` must be absent, outside all inputs and outside the private capture.
Keep its `receipts/` in the private capture before removing disposable sources.
This recipe neither builds nor changes main; the common preparation's canonical
two-build/V1 guards remain prerequisites.

```sh
python - "$MANIFEST" "$RESEARCH" "$HISTORICAL" "$MAIN" "$NEW_WORK" <<'PY'
import gzip, hashlib, json, os, pathlib, stat, subprocess, sys
if not __debug__:
    raise RuntimeError('preparation requires enabled assertions')
os.umask(0o077)
manifest, research, historical, main, work = map(pathlib.Path, sys.argv[1:])
m = json.loads(manifest.read_bytes())
research, historical, main = [p.resolve(strict=True) for p in (research, historical, main)]
work = work.absolute()
assert not work.exists() and not work.is_symlink(), 'fresh output required'
assert all(work != p and p not in work.resolve().parents for p in (research, historical, main))
def read(root, name):
    rel = pathlib.PurePosixPath(name)
    assert not rel.is_absolute() and '..' not in rel.parts, 'unsafe input path'
    p = root
    for part in rel.parts:
        p = p / part
        assert not p.is_symlink(), 'symlink input'
    assert stat.S_ISREG(p.stat().st_mode), 'regular input required'
    return p.read_bytes()
def digest(data):
    return hashlib.sha256(data).hexdigest()
def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
git_env = dict(os.environ, GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0')
def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], env=git_env, timeout=30)
assert git(research, 'rev-parse', 'HEAD').decode().strip() == m['researchCommit']
assert git(main, 'rev-parse', 'HEAD').decode().strip() == m['main']['head']
assert not git(main, 'status', '--porcelain=v1', '--untracked-files=all'), 'main must be clean'
for name, row in m['researchInputs'].items():
    data = read(research, name)
    assert len(data) == row['bytes'] and digest(data) == row['sha256'], name
for name, row in m['historical']['files'].items():
    data = read(historical, name)
    assert len(data) == row['bytes'] and digest(data) == row['sha256'] and blob(data) == row['gitBlob'], name
assert digest(read(main, 'index.html')) == m['pins']['productSha']
inventory = read(main, 'GENERATED.json')
assert digest(inventory) == m['main']['generatedInventorySha256']
inventory = json.loads(inventory)
assert len(inventory['files']) == inventory['fileCount'] == m['main']['generatedMembers']
for name, row in inventory['files'].items():
    data = read(main, name)
    assert len(data) == row['bytes'] and digest(data) == row['sha256'], name
for name, row in m['main']['runtimeFiles'].items():
    data = read(main, name)
    assert len(data) == row['bytes'] and digest(data) == row['sha256'] and blob(data) == row['gitBlob'], name
work.mkdir(mode=0o700)
receipts = work / 'receipts'; receipts.mkdir(mode=0o700)
patched = work / 'historical'; patched.mkdir(mode=0o700)
result = {'protocol':'r0040-capture-preparation/1', 'status':'INCOMPLETE', 'stages':[]}
try:
    for name in m['historical']['files']:
        target = patched / name; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f: f.write(read(historical, name))
    for i, (patch, expected) in enumerate(zip(m['patches'], m['stages'], strict=True), 1):
        compressed = read(research, patch['path']); data = gzip.decompress(compressed)
        assert digest(compressed) == patch['compressedSha256'] and digest(data) == patch['expandedSha256']
        for action in ('check', 'apply'):
            argv = ['git', 'apply', '--whitespace=nowarn', *(['--check'] if action == 'check' else []), '-']
            with (receipts / f'{i}-{action}.stdout').open('xb') as stdout, (receipts / f'{i}-{action}.stderr').open('xb') as stderr:
                subprocess.run(argv, cwd=patched, input=data, stdout=stdout, stderr=stderr, check=True, timeout=30)
        for name, row in expected['files'].items():
            data = read(patched, name)
            assert len(data) == row['bytes'] and digest(data) == row['sha256'] and blob(data) == row['gitBlob'], name
        result['stages'].append(expected)
    pins = json.loads(read(research, 'tools/qa/r0040/pins-revised.json'))
    assert pins == m['pins'] and pins['options'] is None
    assert digest(read(patched, 'tools/qa/precip_models.js')) == pins['rendererSha']
    assert digest(read(patched, 'tools/qa/precip_models_geom.js')) == pins['geometrySha']
    sys.path.insert(0, str(research / 'tools/qa/r0040'))
    from pack_design import PROFILE
    assert json.loads(read(patched, 'tools/qa/precip_declared_gain.json')) == PROFILE
    result.update(status='PREPARED', manifestSha256=digest(manifest.read_bytes()), pins=pins,
                  mainHead=m['main']['head'], historicalPath='historical', nativeStatus='NOT_RUN')
except BaseException as error:
    result['error'] = str(error)
    raise
finally:
    (receipts / 'prepared.json').write_text(json.dumps(result, indent=2) + '\n')
PY
```

Input-admission failures stop before creating `NEW_WORK`; retain the caller's
stdout/stderr and process status. Failures after creation retain the partial tree,
each patch stream, and `INCOMPLETE` preparation. No input or previous output is
repaired. The planner must require normal process exit, `PREPARED`, exact source
identities, and completed patch stages; receipt presence alone is insufficient.
The recipe rejects optimized Python so its admission assertions cannot be skipped.
Its [actual execution and refusal controls](evidence/R0040/native-capture-preparation-controls.json)
bind the extracted recipe source and input manifest by SHA-256. The successful
run produced `PREPARED`; changed and symlinked preimages, an existing output, and
optimized Python were refused. No native process was involved.

The actual offline checks used the published controls:

```sh
R0040_LAYER_STUDY=1 R0040_INSPECT_PARAMETERS=1 \
  node "$RESEARCH/tests/r0040-gain-controls.cjs" "$NEW_WORK/historical"
node --test "$RESEARCH/tests/r0040-parameters.test.cjs"
```

The gain/layer controls passed the strict cap, retry, cache, width, light-kernel,
shell, column, motion-cohort and parameter checks. The revised audit matched all
33 named parameters and 182 expressions in 48 declarations. The parameter test
passed its actual-source mutations. Separate preflight negatives rejected layer
patch application before the gain patch, a missing legacy capture input, and a
changed renderer preimage. The actual authored option entry had SHA `4b31c117…`
and failed equality with the unchanged main product pin `88411488…`.

## Planned native cell and report admission

After independent review and coordinator isolation checks, the exact original
driver argv is:

```sh
R0040_DISPERSION=common \
  "$NODE" "$RESEARCH/tools/qa/r0040/capture.cjs" \
  "$PLAYWRIGHT_MODULE" "$NEW_WORK/historical" "$MAIN" \
  "$PRIVATE_NEW_CELL" chromium bday moderate M1

"$PYTHON_WITH_PILLOW_AND_CRYPTOGRAPHY" \
  "$RESEARCH/tools/qa/r0040/lossless_pack.py" cell \
  "$PRIVATE_NEW_CELL/capture.json" \
  --pins "$RESEARCH/tools/qa/r0040/pins-revised.json"
```

The coordinator must remove inherited `R0040_OPTIONS`; setting it to an empty
string in a cleared environment is also inert in the original driver. It must
set `R0040_DISPERSION=common`, preserve the explicit Node module directory, and
run with the immutable research checkout as cwd. Use the reviewed installed
Playwright build and corresponding Chromium browser. Python needs **Pillow and
cryptography even for `cell`**, because the verifier imports them at startup;
NumPy, FFmpeg and signing keys are not inputs of this single-cell verifier.

The unchanged driver fixes DPR 1 and requests 3.3 seconds of capture. An initial
outer child-process bound of 180 seconds is proposed; timeout means incomplete
evidence. Raw PNG size is host-dependent. At 60 fps, 198 decoded 325×530 RGBA
frames occupy 136,422,000 bytes before PNG compression; this is a sizing estimate,
not an observed frame count. Keep source trees outside the private capture.

The expected report is schema 3, `native-controlled-capture`, Chromium,
`bday/moderate/M1`, revised/common dispersion, options null, compositor PNG,
browser-native epoch clock, UTC `1790154360000`, code 63, amount 1.25 mm over
900 seconds, and current-source permission on. The effective interval-average
rate is 5 mm/h. Require all these values and the exact source/option pins.

Capture exit 0 writes `capture.json` and PNGs. It does not decide cadence. The
unchanged verifier exits 0 only after its complete checks and emits JSON with
`evidence: cell`, `sourceAuthority: external pins`, log and ordered RGBA digests,
and frame count `n`. It requires at least 180 frames spanning about three seconds,
no disallowed frame gaps, uniquely matched native audit samples, advancing
source/renderer clocks, stable source and geometry, and exact image inventory.
Retain a nonzero verifier result with all original capture bytes. A successful
cell is not a signed pack, appearance verdict, human judgment or work-order PASS.

The original helper blocks service workers and fulfills or aborts fixture requests.
The native driver itself has no isolation-receipt gate and writes its report
before final context cleanup. The coordinator's independently reviewed launch
boundary and final request/error ledger remain required; this preflight does not
implement or qualify them.

## Registry and integration handoff

This commit adds a preparation document and two evidence receipts, with no new
instrument. The existing
registry already excludes `capture.cjs` as an explicit native recipe and
`r0040-gain-controls.cjs` as a separate historical-source control. It already
selects `r0040-parameters.test.cjs` in the native test glob. No central workflow,
planner, observer, registry, product or pin is edited here.

The receipt lists the full source closure for the original driver, verifier,
parameter audit and controls. A new coordinator wrapper or admission control
needs its own registration; include its actual source inputs and avoid also
classifying selected input paths as modules/exclusions. The native child requires
the four historical runtime inputs, complete main runtime, `capture.cjs`, and
explicit Playwright module. Verification additionally requires `lossless_pack.py`,
`pack_design.py`, `pins-revised.json`, Pillow and cryptography. Frozen V1 and main
build admission remain with the common preparation.
