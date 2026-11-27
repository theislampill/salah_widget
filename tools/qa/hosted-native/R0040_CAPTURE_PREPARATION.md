# Guarded R0040 capture preparation entry

`r0040_capture_prepare.py` executes the unchanged Python recipe in
[`R0040-native-capture-preflight.md`](../../../docs/state-contracts/R0040-native-capture-preflight.md).
It adds process bounds, private stream retention and a separate admission
receipt. It does not build or change main, launch a browser, run the capture or
certify native cadence. No package beyond Python's standard library and Git is
needed for this preparation.

## Exact source binding

| Input | SHA-256 |
|---|---|
| Documented recipe, exactly 4,708 bytes with no appended newline | `9fc26a75cb62c145f9de7bd7aa386ac6714c238f3e08089558d34f02882f9730` |
| Full preflight manifest | `267f2fd8ac130c049430ffdaa0fd50b72457c60084b49360346748cc940f6b73` |

The entry extracts the one delimited recipe from the document, verifies that
digest and sends those exact bytes to a separate Python process. The original
assertions, source population, patch commands and original `prepared.json`
writer are unchanged. Optimized Python is refused. The child uses `-I -B` and a
new private bytecode-cache prefix so cached `pack_design` bytecode cannot replace
the verified source.

The recipe verifies all six historical preimages, every declared research input,
both compressed and expanded patch hashes, and all six source identities after
each complete patch stage. It requires genuine main at the pinned HEAD, clean
status, the main product pin, the generated inventory and its members, and the
177-file main runtime manifest. It applies the declared-gain patch before the
layer-study patch. Revised pins must have `options: null`; the declared profile
must match the actual source `PROFILE`.

The entry then checks the original successful receipt, both exact stages and
the actual final six-file population again. These checks provide preparation
custody, not a native result or a promise that an input cannot subsequently change.
The native admission wrapper must recheck the inputs before importing its driver.

## Invocation and output

```sh
python tools/qa/hosted-native/r0040_capture_prepare.py \
  --manifest "$CAPTURE_MANIFEST" \
  --research "$CAPTURE_RESEARCH" \
  --historical "$CAPTURE_HISTORICAL_INPUTS" \
  --main "$CAPTURE_CLEAN_MAIN" \
  --out "$CAPTURE_NEW_WORK" \
  --receipts "$CAPTURE_PRIVATE_PREPARATION"
```

`--out` is the fresh disposable source directory expected by the original
recipe. `--receipts` is a separate fresh private directory. Both must be outside
all input trees and must not contain each other. The coordinator places the
disposable work outside its enclosing private capture, and the separate receipts
inside that capture. The source entry verifies disjointness from the supplied
receipt directory; it is not given the enclosing capture-root path.

| Retained path | Meaning |
|---|---|
| `--out/historical` | Six disposable historical files after the two full patches, or the partial failed attempt |
| `--out/receipts/prepared.json` | The untouched original recipe receipt, protocol `r0040-capture-preparation/1` |
| `--out/receipts/1-*`, `2-*` | Original patch check/apply stdout and stderr, including failed stages |
| `--receipts/attempt.json` | Initial wrapper identity, exact inputs, expected contract hashes and incomplete disposition |
| `--receipts/recipe.stdout`, `recipe.stderr` | Unmodified guarded-recipe streams, including input-admission exceptions |
| `--receipts/process.json` | Supplemental terminal process and preparation-admission receipt |

Receipts are written to exclusive `.pending` files, flushed and fsynced, and
published under their final names only afterward without replacing an existing
file. A failed pending file remains private evidence and is not an admitted
terminal receipt. Actual coordinator-observed process status still takes
precedence over any readable file; the coordinator must require the preparation
entry's actual exit zero as well as its receipts. A data-fsync failure cannot
publish `process.json`, and a later publication/cleanup error propagates nonzero.

The wrapper bounds the recipe process group to 180 seconds; the original
individual Git timeouts remain unchanged. Timeout retains streams and partial
work, then terminates the child process group. Existing work is refused by the
original recipe and retained unchanged; a retry needs a new private receipt
directory. Existing receipts are never rewritten. If receipt-path admission
itself fails, the caller must retain the entry's stdout/stderr and actual status.

The entry exits zero only for `PREPARED`. It preserves a positive nonzero recipe
exit where available and returns 2 for a wrapper admission/finalization failure
or a timed-out/signaled child. No failed attempt is repaired or reused.

## Terminal receipt contract

The protocol is `r0040-capture-preparation-process/1`. Fields required by the
native admission wrapper are:

- `inputs`: absolute normalized `manifest`, `research`, `historical`, `main` and
  `out` paths. Patched historical input is exactly `inputs.out/historical`.
- `returncode`: actual guarded-recipe child exit, or null if no child started;
  `timedOut` is a boolean. The outer entry's actual exit is admitted separately.
- `status`: `PREPARED` only after normal child completion and all postchecks;
  otherwise `INCOMPLETE`. `nativeStatus` always remains `NOT_RUN`.
- `manifestSha256`, `recipeSourceSha256` and `wrapperSha256`: identities for this
  attempt. Expected contract digests are also retained when admission fails.
- `preparedReceipt`: original receipt path and SHA-256 when one was produced by
  this attempt. A partial original receipt is retained without changing status.
- `completedStages`, `pins`, `finalHistoricalFiles`: present on preparation
  success, binding both exact stages and all six actual final source files.
- `argv`, `timeoutSeconds`, `elapsedSeconds`, `outputPreexisted`, and `streams`:
  command/progress custody and both stream file names, paths, sizes and hashes.

The wrapper never copies a previous attempt's prepared receipt into a fresh
success claim. An outer nonzero exit, missing terminal receipt, nonzero child,
timeout, incomplete status, wrong contract hash or changed source blocks native
admission. The separate capture wrapper and unchanged lossless verifier decide
their own bounded admission; this process receipt cannot supply their results.

## Offline controls and registration handoff

```sh
python tools/qa/hosted-native/r0040_capture_preparation_controls.py -v
```

The **10** controls run the exact extracted recipe on small genuine Git fixtures
with test-only manifest pins. They exercise complete two-stage preparation,
source drift, missing and symlinked inputs, reversed patches, a wrong second
postimage, preservation of the first completed stage, output/receipt reuse,
poisoned bytecode, optimized Python refusal, timeout/descendant cleanup, and final
receipt-fsync failure. The actual production manifest and recipe digests are also
checked independently. Fixture results are offline controls, not native evidence.

The registry includes `hosted-native-r0040-capture-preparation-controls` with argv
`{python} tools/qa/hosted-native/r0040_capture_preparation_controls.py -v`, protocol
`unittest-cases`, expectedCases `10`, and `covers` containing that control file.
The complete command input closure is:

```text
tools/qa/hosted-native/r0040_capture_preparation_controls.py
tools/qa/hosted-native/r0040_capture_prepare.py
docs/state-contracts/R0040-native-capture-preflight.md
docs/state-contracts/evidence/R0040/native-capture-preflight.json
```

The command uses `PYTHONUTF8=1` and `PYTHONDONTWRITEBYTECODE=1`. Selected input
paths are not also classified as modules or exclusions. Central wiring is
documented in [LANES.md](LANES.md): `--r0040-mode capture` retains the actual
entry process separately in `r0040-preparation-entry.json`, copies original
patch receipts even on failure, and requires both process layers before running
the reviewed read-only source guard. The common preparation is unchanged.
