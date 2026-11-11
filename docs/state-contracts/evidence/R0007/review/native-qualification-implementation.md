# R0007 qualification repair implementation

This is the separately commissioned engineering task after the bounded Andon diagnosis. It is not an Andon authority action or a native acceptance report. The root reported source checkpoint `5e946fe18a31750cf528bd58210ce79182dcf1e1`; this task changed only:

- `tools/qualification/r0007_native.py`
- `tools/cp9/r0007_browser.py`
- New `tests/test_r0007_native_qualification.py`

No source HTML, generated entry, recipe, workflow, shared `browser_runtime.py`, sibling branch, Git index or commit was changed by this task. No actual browser, HTTP server, workflow, credential or remote service was used. Temporary tests contain explicitly synthetic evidence and mock only the external browser/server/process boundaries. The tests run the actual collector and driver decisions.

## Behavior changed

**Terminal evidence gates source credit.** Healthy and intended-mutant results now require a single matching terminal summary receipt: case ID, trace status and trace location must agree. Malformed/non-object JSON fails closed. The aggregate additionally requires cleanup to be established for every accepted cell, including the last or sole result. The existing exact intended `AssertionError`, exit-code and named healthy-control checks remain; an absent/non-string failure cannot become a mutant verdict.

**Presentation evidence is per capture.** The collector distinguishes absent native setup, missing artifacts, malformed capture evidence, ordinal mismatch, eventual state, and a recorded association still awaiting independent review. Each association binds its declared capture to its actual named checkpoint and receipt ordinal. Original video, presentation receipt and, when requested, still-image hashes are recorded. Missing/malformed required capture evidence cannot earn source credit. An ordinal mismatch with intact evidence can retain source-assertion credit while its presentation remains explicitly unverified. No automatic result accepts first visible pixels: `firstFrameAcceptance` stays unverified. A 250 ms latest-render recovery capture is `EVENTUAL_STATE_ONLY` when associated correctly.

**All first-capture mismatches continue acquisition.** The driver retains the mismatch, preserves PARTIAL status, and proceeds through release, later actions, trace export and native recording regardless of whether the capture is named `unavailable` or `first-current`. It neither redraws the product nor waits for an expected target. The first visible recovery still needs independent review of the original trace/video and all intervening frames.

**Executable identity is concrete.** The R0007 driver uses the existing runtime-selected executable or the managed `BrowserType.executable_path`, resolves and hashes it before launch, and passes that exact path to launch. This avoids claiming a managed full-Chromium executable hash while Playwright automatically launches a different headless-shell executable. The selected family, requested engine, actual version, platform, executable/hash and headless state are recorded. The collector validates the recorded requested/actual family and the concrete executable/hash on the acquisition host. Existing Chromium sandbox options are preserved. No shared runtime selector change was needed.

**An unchanged setup failure is not replayed across the engine's matrix.** The driver explicitly records browser-launch/context failure stages. After such a failure with established cleanup, the collector marks remaining cases for that engine unattempted, retains the original failed result, and may continue the independently required other engine. Unestablished cleanup still stops all further launches. Navigation, case-action and ordinary product/assertion failures do not become engine incapability merely because an assertion fails. Any skipped cell keeps aggregate success false.

## Test-first evidence

Raw output and command/hash receipts are under `../evidence/native-qualification-repair/`:

| Evidence | Result |
|---|---|
| `red.log`, `red-receipt.json` | Before production edits: 16 tests, 34 failing assertions, actual exit 1. Reproduced cleanup, malformed evidence/identity, no-browser status, capture-name abort and generic executable binding. |
| `red-expanded.log`, `red-expanded-receipt.json` | Added the requested orchestration controls before their implementation: 18 tests, 36 failing assertions, actual exit 1. |
| `green-attempt-1.log`, corresponding receipt | Initial repair: 18 tests passed. |
| `red-capture-binding.log`, corresponding receipt | Review found that a presentation file could claim an ordinal absent from its named trace checkpoint; the new regression failed before the binding repair. |
| `focused-final.log` | Final focused suite: **19 tests passed**, exit 0. |
| `runtime-selector-final.log` | Existing shared-selector compatibility suite: **5 tests passed**, exit 0; shared selector untouched. |
| `diff-check-final.log` | Scoped `git diff --check`: exit 0. |
| `final-verification.json` | Exact commands, timestamps, log/source hashes and explicit non-native scope; all three changed Python files also parsed successfully with `ast.parse`. |

The 19 focused tests cover Q01–Q11 and the added Q12 engine orchestration contract, using actual evidence-file parsing and actual driver action sequencing. The final direct commands were `python -B tests/test_r0007_native_qualification.py` and `python -B tests/real-sky/cp9_browser_runtime_test.py`. No broad product, builder or native campaign was run under this bounded commission.

## Exact final file hashes

| File | SHA-256 |
|---|---|
| `tools/qualification/r0007_native.py` | `c3182108b4852fb4b1c1b72315f5e458e43565a6fa817f73f2e209be51a33124` |
| `tools/cp9/r0007_browser.py` | `40127a417130898107198d342014e7214a2bce70baef71b801b5824152bb9c24` |
| `tests/test_r0007_native_qualification.py` | `8c3b3dd2d1561a6ead2dee94da9ec351b2deaa77b741e9102992aff7e7c00e0f` |

## Remaining boundary

The new metadata checks intentionally require fresh receipts from the updated driver. Historical artifacts are retained evidence of their original execution, not automatically upgraded through the new collector. Root review, exact candidate binding, required Windows/two-engine execution, independent native pixels/first-visible recovery, scoped preservation and later acceptance/approval remain outstanding. These pure tests establish qualification-mechanism behavior only.
