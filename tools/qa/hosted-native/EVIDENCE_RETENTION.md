# Supplemental native evidence retention

> For agentic workers: implement the bounded wrappers, then use an independent
> exact-commit review. The continuing owner commission already authorizes this
> work; it does not authorize product acceptance or policy selection.

**Goal:** Retain partial R0040/R0035 native evidence when the original recipe fails.

**Architecture:** Run the exact hash-pinned original drivers and helpers. Wrap
their host-side observation boundaries without copying their loops, changing
their assertions, changing route selection, or writing replacement result files.
Record request actions and acquisition bounds before subsequent calls can fail.

**Tech stack:** Node and Python standard libraries; the original pinned Playwright
packages and original recipes remain the actual browser drivers.

**Spec:** The 25 November continuation handoff sections 1, 6 and 7; the authorized
follow-up diagnosis; immutable research commit
`55d1b3edb66d2c35679707120b01ee1d3455e4a3` and historical helper commit
`4029d2f67f5a880c8ad889443bb7557d96022c45`.

## Boundaries and approach

An unchanged recipe can retain its successful final report but loses useful
intermediate metadata. Editing or copying its loop would introduce a second
recipe whose equivalence would need qualification. This successor instead proxies
the actual browser/context/page/route objects and calls the actual original
oracle/admission functions. Source hashes are checked before import/execution.

R0040's CommonJS module executes unchanged, including its existing catch handler.
R0035's imported original `main` calls its original `trial` through a wrapper.
No browser is launched by these controls. Native invocation requires the existing
admitted namespace receipt before loading the browser package.

## Work and review focus

- [x] Write failing controls for interrupted cells/trials and source drift.
- [x] Implement a source manifest and R0040 wrapper around the actual driver.
- [x] Implement an R0035 wrapper around the actual original functions.
- [x] Prove routes are installed before page creation and unknown external
  continuation is refused; record both requested and completed route actions.
- [x] Prove prior evidence survives an oracle/admission exception, diagnostic
  capture failure does not replace that exception, and original reports remain
  absent when the original recipe did not write them.
- [x] Run focused controls and privacy checks; document command and registration
  recommendations for the coordinator without changing current pilot lanes.
- [x] Freeze and independently review the wrapper implementation at commit
  `52722d77d881603e6d8eefdd528024d7d3f928a4`, tree
  `b28bf10af0f3150cf9f6a341f01dba93cbd8d4ba`. Coordinator integration has a
  separate exact-tree review boundary.

## Interpretation

The separate retention directory is private capture material. It is never an
alternate success report. Original oracle failures, original admission verdicts,
original command arguments and uncompleted populations remain unchanged. An
interrupted journal only establishes events recorded before interruption.

The wrappers add host-side serialization, hashing, fsync, and screenshot-copy
overhead. Every wrapped timing/capture run must be identified as instrumented;
driver durations can include that overhead. Screenshot request/receipt bounds
are not display presentation timestamps. A supplementary failure screenshot is
taken after the fault and cannot be relabeled as the exact failing frame.

No product source, generated delivery, V1, vendor or original recipe is changed.
The initial coordinator integration registered these offline controls and added
optional instrumented commands without changing that initial campaign or the
default invocations. Later campaigns are described in [LANES.md](LANES.md), including
conditional work-order selection and
`--retain-evidence`/campaign `evidenceRetention` controls.

## Invocation and exact binding

The coordinator supplies the existing `SALAH_HOSTED_NATIVE_ISOLATION_RECEIPT`.
Both CLIs require its successful real-browser control, actual nonroot UID and
current distinct network namespace. This remains an admission check of the
coordinator's receipt; it is not a new independent network-boundary experiment.

```bash
node tools/qa/hosted-native/retain_r0040.cjs \
  --driver "$RETENTION_RESEARCH/tools/qa/r0040/native-options.cjs" \
  --evidence "$RETENTION_PRIVATE/r0040-retention" -- \
  "$RETENTION_PLAYWRIGHT" "$RETENTION_HISTORY" "$RETENTION_RAIN_TREE" \
  "$RETENTION_PRIVATE/r0040-original" chromium

python tools/qa/hosted-native/retain_r0035.py \
  --driver "$RETENTION_RESEARCH/tools/r0035/native_trials.py" \
  --evidence "$RETENTION_PRIVATE/r0035-retention" -- \
  "$RETENTION_PLAN" "$RETENTION_PRIVATE/r0035-original" \
  --engine chromium --rounds 1 --seconds 15 --clock ordinary \
  --scene dark --motion normal
```

These examples preserve the initial recipe arguments. A capture invocation adds
the original `--capture` flag and uses fresh original and retention directories.
Engine, scene, motion, round count and duration remain explicit original options;
the wrappers never infer different choices from an observed result.

`retention-pins.json` gives all six exact SHA-256 values: R0040 driver, oracle and
historical helper; R0035 driver, admission and clock helper. R0040 executes its
complete original CommonJS bytes, including its loop, assertions and catch
handler. Only its module dependencies are returned through observer proxies.
R0035 compiles the verified source bytes directly, bypasses cached bytecode, and
calls the original `main`, `trial` and `assess` functions through host wrappers.
The original filenames remain their module filenames, so helper and fixture
resolution and original driver identity fields are preserved. Neither driver is
copied or transformed.

The private `sources` event identifies these inputs, wrapper/manifest digests,
original arguments and admitted isolation receipt. The package/browser/build
identities continue to come from the enclosing acquisition/preparation receipt.

## Retained evidence and status

`events.jsonl` is append-only, flushed and fsynced per event; copied PNG files are
also flushed and fsynced before a receipt event refers to them. Each record has a
sequence and host timestamp. On abrupt interruption, inspect only the complete
JSONL prefix; an absent final event is incomplete acquisition, never success.
This does not promise a final record after process kill or host loss.

Always combine journal interpretation with the **actual child exit status**.
A readable `driver-process-ended` row can precede failure of its own fsync or of
later journal close; its embedded exit code is not sufficient. Terminal
retention failure makes an otherwise successful process nonzero. R0040 appends a
best-effort `retention-finalization-failed` correction when possible, without
rewriting the failed attempt. Both wrappers also retain finalization diagnostics
in the coordinator's private stderr when the journal may be unavailable.
Retention cleanup preserves a pending original Python exception and reserved
exit 86. A standalone cleanup failure remains an error. The original recipes'
own context-close behavior is unchanged.

R0040 records original scene inputs, the actually installed options, readiness,
the exact original oracle input and return/exception, two original postconditions,
the helper's scene log, original PNG receipts, and completed cell bodies. It
retains earlier cells if a later cell fails. R0035 records original evaluations,
admission inputs/verdicts, completed original trial results, per-PNG receipts, and
original acquisition metadata present when its context-finally boundary runs.
Unexpected trial exceptions retain accessible original frame locals and rethrow.
The unchanged original timeout path remains indeterminate. Explicit failed
admissions remain failed. Neither wrapper writes an original report file.

`request`, `request-action`, `request-action-completed` and
`request-action-failed` records correlate each routed request with its actual
action. The original callback still decides fixture fulfillment or abort. The
observer additionally vetoes any attempted external continuation before invoking
the real continue action. Such a veto is recorded as
`external-continuation-vetoed` and returns **exit 86**, even if a callback error is
otherwise swallowed. It is a prevented request-policy violation, **not evidence
of an actual network escape**. The coordinator stops all subsequent observations
on 86 and preserves `EXTERNAL_CONTINUATION_VETOED` and the actual child exit in
the inner receipt. It completes normally only after writing that receipt;
abnormal outer namespace completion still dominates. Ordinary original R0040
failures remain exit 1; original R0035 result semantics still require reading
every admission rather than trusting process exit zero.

This ledger covers requests seen by the original browser-context catch-all
route. It does not claim browser-process/WebSocket coverage beyond that route;
the enclosing verified namespace remains the common network boundary.

`requestNs` is the wrapper's pre-journal acquisition attempt time; `rawCallNs` and
`receiptNs` bound the original screenshot API call. The separate original R0035
`startMs`/`endMs` are retained under their original names and can include wrapper
I/O. All these bounds are host-side acquisition observations. The journal neither
subtracts guessed overhead nor converts them into display timestamps. Added
failure screenshots are explicitly `failure-diagnostic`, after the fault, and
their acquisition failures remain secondary diagnostics.

## Offline controls and coordinator registration

```bash
node --test --test-reporter=tap tools/qa/hosted-native/retention_controls.cjs
python tools/qa/hosted-native/retention_controls.py -v
```

The Node control runs the complete unchanged original driver with controlled
browser/helper doubles, forcing its second real oracle to fail. Supplying
`R0040_HISTORICAL_CONTROL` as the exact historical checkout repeats that control
with the actual source-pinned historical helper and only browser doubles. The
Python controls execute the original `trial` and `assess`, including a failed
admission, its expected timeout, and an unexpected admission exception following
a timed original screenshot acquisition. All such outputs are synthetic controls;
no browser was launched and no native/product acceptance follows.

Registry command `hosted-native-r0040-retention-controls` uses the Node argv above,
protocol `auto`, owner R0040, covers the CJS control. Its input closure is the CJS
control and wrapper, pins JSON, original R0040 driver/oracle, and
`tests/r0002-ordinary.json`. The optional actual historical-helper repetition is
a separately recorded control using the already admitted checkout.

Registry command `hosted-native-r0035-retention-controls` uses the Python argv
above (use `{python}`), protocol `unittest-cases`, expectedCases **14**, owner
R0035, covers the Python control. Inputs are that control and wrapper, pins JSON,
and original `native_trials.py`, `trial_admission.py`, `trial_clock.js`. Use
`PYTHONUTF8=1` and `PYTHONDONTWRITEBYTECODE=1` as for existing controls.

These command input closures are the census classification for their wrappers,
helpers and original source inputs. Do not also declare those same paths as
modules or exclusions. R0040's original driver is now an executed source input
to the offline control, so its former duplicate exclusion is removed. Its native
role remains documented in the original lane CLI and the direct invocations
above; offline execution with doubles does not qualify the native recipe.
No verification-level promotion or failure-ledger change follows.
