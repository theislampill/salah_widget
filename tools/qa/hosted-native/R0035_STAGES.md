# R0035 preparation-stage observations

This is a separately identified diagnostic derivative of the disposable R0035
lab. It observes source replacement, preparation and the first publication of
each epoch. It does not alter the product, select an owner policy, relax an
admission predicate, or replace an original native report. No native result is
claimed by the offline controls described here.

## Why a distinct derivative is needed

The original lab already exposes owner, status and publication events during a
trial. Those events delimit preparation as a whole, but not the work inside the
worker. The original `beginTrial` also starts its event history after warmup.
Polling the existing state more often would add main-thread work while still
leaving the internal stages unidentified.

The new materializer adds a bounded, separate event history at lab installation
and small worker marks on the existing preparation replies. In the original
refined path, catalogue/projected-source/transport checks and `prepareStars`
precede `prepareReplay`. The replay scope option therefore does not skip that
upstream stellar preparation. This ordering is a source finding; measurements
from different acquisitions do not establish a controlled cost comparison.

## Source admission

`r0035-stage-pins.json` binds all 24 original `tools/r0035` files at research
commit `55d1b3edb66d2c35679707120b01ee1d3455e4a3`. Its SHA-256 is
`26a180b7aad4d54fa139eb20484e95efdc2e9cb759a77b2eaa5c175996a7233e`.

`r0035_stage_materialize.py` first executes the unchanged original plan checker
against the intact independently reconstructed lab and clean main checkout. It
also checks the original flag symmetry and the complete original source pins.
It rejects traversal and symlink members before the original checker reads the
lab receipt. It then copies the lab to a fresh, separate directory.

Only these two standalone lab modules change:

| Module | Original SHA-256 | Instrumented SHA-256 |
| --- | --- | --- |
| `tools/r0035/live_lab.mjs` | `11717de894a630f99b5d661ff35c4200b355f4486c533e0e31dbc39e67a6a02a` | `cdc4c55173b143b3522caad22daebc114b0c7d662346e7674f683ec40891d003` |
| `tools/r0035/lab_worker.mjs` | `80707cfb05233478f974a0b0e1fd209400790cba3a8616812f4f98f63d1f4458` | `3ce8d0a50a543437729d274cb9f9255ea83f92330054070a6e8c6dff3763fac7` |

Each literal seam must occur exactly once. Reversing all seven main-thread and
eleven worker seams must reproduce the full original bytes exactly. The receipt
records the seam hashes, module preimages/postimages, materializer hash, source
plan, original lab identity and complete before/after file populations. Runtime
admission recomputes the population and the exact two-file delta, even if someone
has rehashed a receipt describing an extra transformation.

The derivative retains the original lab identity bytes unchanged. Asking the
original checker to admit it as `independent-reconstruction` fails on its changed
modules. A separate `r0035-stage-identity/1` receipt and
`instrumented-r0035-stages/1` plan admit the diagnostic transformation. Main,
producer flags, probes and all other plan fields retain their original values;
only the plan kind, two experimental root paths and explicit diagnostic identity
are changed. Original report `scope` consequently identifies this new plan kind.

`observe_r0035_stages.py` verifies the existing admitted isolation receipt before
loading the original driver. It also requires the coordinator's actual successful
stage-preparation process receipt and its expected digest. That receipt binds
the original preparation and process receipts, source plan and lab identity,
actual materializer argv/source, derivative identity and plan. Changed receipts,
nonzero exit, timeout or retention error refuse before original-driver loading.
It uses the reviewed, hash-bound retention loader
to compile the unchanged driver and admission helper from source bytes, avoiding
cached bytecode. The clock helper remains hash-bound. It does not use the
retention wrapper's per-evaluation journals or screenshot copies.

The wrapper admits the separate plan before invoking original `main`. Its
explicit plan dispatcher then requires the plan reread by original `main` to
equal the admitted plan. The original checker has already run on the intact
source plan; it is neither weakened nor asked to certify altered bytes as
unmodified. Original `trial`, `assess`, argument parsing and loop order execute
unchanged. The source plan still receives the original reconstruction flag
symmetry check even though the new plan kind has a distinct name.

## What is observed

The page history starts inside `installLab`, after configuration validation and
before worker construction. It is retained across original `beginTrial` and
`endTrial`. It does not observe navigation or module loading before installation.
The original trial's start/end timestamps permit pretrial and measured-window
interpretation; no new polling or warmup-boundary call is added.

| Page-clock interval or event | Meaning |
| --- | --- |
| Source replacement | Records old/new epoch and reference-change flags for raster, canvas, disc key, cloud, moon and mask. Reference inequality is not a pixel-difference claim. |
| Owner to dispatch | Includes waiting for the original single preparation slot. An epoch superseded before dispatch remains explicitly unmeasured. |
| Message construction | Bounds the original factory, including its existing readback and padding. The factory still executes once. |
| `postMessage` call | Bounds the original call returning to the page; it is not worker receipt time. |
| Dispatch to reply | An inclusive page-clock interval, covering work and scheduling between those events. |
| Reply to first request | Includes the original opportunity to request a sample, subject to its unchanged guard. |
| First request to first publication | Ends at the original publication event after the original writer call. It is not a display scanout timestamp. |

Worker traces have their own `worker-performance-now-ms` clock. Their ordered
marks identify receipt; catalogue start/ready; projected and transport source
verification; stellar preparation; replay preparation; nominal-byte checking;
census completion; candidate return; and ready-post. Catalogue time includes the
original cached promise or fetch, decode and digest checks as applicable. The
source-verification interval after catalogue-ready covers the remaining
projected-membership and transport checks.

The small worker trace is attached only to the existing `ready` or `failed`
reply. There are no extra progress messages or sample-message fields. A failure
contains the completed prefix and original failure reason. Concurrent catalogue
awaits use distinct local traces. The original generation guard still discards a
superseded successful candidate without sending a reply; absent worker data is
not synthesized from a different epoch.

All intervals subtract timestamps within one page clock or one worker
preparation trace. The extractor never subtracts worker time from page time,
and never labels their difference as measured transfer latency. Ready replies
require the complete ordered worker sequence; failed replies require its valid
prefix. Missing marks yield no invented duration. The bounded page history holds
at most 2048 events; overflow makes the supplemental observation incomplete.

## Overhead, retention and failure semantics

Every invocation is **instrumented stage observation**. Added `performance.now`
calls, small objects, branches and reply serialization have uncalibrated cost.
The original measurements are retained as acquired, without an estimated
overhead subtraction or a claim of equivalence to an uninstrumented run.

The page records owner/status/withdraw events and only the first sample request
and first publication for each epoch. It does not copy pixels, hash pixels,
append a new per-frame history, or fsync while the original trial is measuring.
All original guard calls, resets, thresholds, source assertions, sample replies,
transfers, image reads and writer calls remain present and in their original
order. The instrument does not reset a guard to obtain a preferred outcome.

At original context cleanup, the wrapper makes one dedicated read of
`observeStages`. On the normal path this follows the original measurement end
and `trial.json` write. It forwards original context close, then writes separate
private trial observations with the original report hash and measured window.
An early exception permits extraction of the available prefix; a destroyed page
may make that extraction impossible. A retrieved raw trace is retained before
validation: overflow, missing startup or malformed worker marks produce
`INCOMPLETE` plus that trace and a `validationError`. A failed page evaluation is
separately `UNAVAILABLE` with an `extractionError`. This is not durable crash-time
tracing.

Separate receipts use fresh exclusive pending files, flush/fsync, then an
exclusive hardlink. Failed materialization leaves its partial tree and separate
failure receipt. Pending files are retained. No failure path rewrites an
original trial report or erases a previous attempt.

The final private driver receipt describes acquisition, not native acceptance.
`OBSERVED` means the supplemental extraction completed. Read every unchanged
original qualification and the actual child exit separately. Observation failure
makes an otherwise successful child nonzero; an original nonzero status or
exception takes precedence over a secondary observation failure. Final receipt
construction/write faults are included in that rule. A routing continuation
veto takes precedence as exit **86**, with the prevented request retained when
the evidence sink is available. This is prevention, not evidence of network
escape. The original catch-all route must be installed before page creation,
service workers remain blocked, and the enclosing verified namespace remains
the common network boundary.

## Explicit invocation

These commands do not select a campaign. All paths below refer to fresh private
outputs and already admitted original inputs supplied by the coordinator.

```bash
python -B tools/qa/hosted-native/r0035_stage_materialize.py \
  --driver "$R35_RESEARCH/tools/r0035/native_trials.py" \
  --plan "$R35_ORIGINAL_PLAN" --out "$R35_DERIVED_LAB" \
  --receipt "$R35_STAGE_IDENTITY" --plan-out "$R35_STAGE_PLAN"

python -B tools/qa/hosted-native/observe_r0035_stages.py \
  --driver "$R35_RESEARCH/tools/r0035/native_trials.py" \
  --preparation-process "$R35_STAGE_PROCESS" \
  --preparation-sha256 "$R35_STAGE_PROCESS_SHA256" \
  --identity "$R35_STAGE_IDENTITY" --evidence "$R35_STAGE_EVIDENCE" -- \
  "$R35_STAGE_PLAN" "$R35_ORIGINAL_OUTPUT" \
  --engine chromium --rounds 1 --seconds 15 --clock ordinary \
  --scene dark --motion normal
```

Original options after the two positional paths pass through unchanged. These
examples do not authorize a new scope, amplitude, guard, scene, engine or timing
policy. The source plan supplies such decisions explicitly. The original
`--capture` option remains available in the standalone driver, but the integrated
stage option is bounded to timing only and adds no hosted Python package.
The materializer CLI alone does not supply the coordinator's process receipt;
native invocation needs the actual retained coordinator preparation attempt.
The selected campaign must receive review of its exact integrated source tree.

## Offline controls and coordinator integration

```bash
python -B tools/qa/hosted-native/r0035_stage_controls.py -v
node --experimental-vm-modules --test --test-reporter=tap \
  tools/qa/hosted-native/r0035_stage_source_controls.cjs
```

The Python suite has **15 unittest cases**. It executes the actual pinned
original trial/assessor with bounded dependencies, compares unchanged original
passed/failed reports, extracts an experimental trace after the report write,
checks exception and finalization precedence, and refuses missing isolation,
unrouted page creation and external continuation. Real Git fixtures and all 24
original source files exercise derivative admission, untouched original checks,
source/plan/receipt drift, receipt rebinding, failed partial copies and reversible
seams. Actual context cleanup retains rejected raw prefixes and distinguishes
unavailable extraction without replacing an original exception. Synthetic clocks
test missing/overflowed traces, worker sequence and clock domain separation.

The Node suite has **12 tests**. It evaluates complete original and transformed
module bodies with bounded dependencies. Paired controls compare original
calls, state, trial events, ready/sample fields and transfer counts. They cover
startup/warmup, unchanged renewal, stale ready/failed replies and queue order,
bounded overflow, worker preparation failures and concurrent catalogue awaits.
They launch no browser and do not measure native performance or prove a visual
verdict.

Command `hosted-native-r0035-stage-controls` registers the Python argv with
protocol `unittest-cases`, `expectedCases: 15`, and owner R0035. Its input closure is the
Python control, observer, materializer, stage pins, existing
`retention_controls.py` fixtures, `retain_r0035.py`, `retention-pins.json`, and
all original paths enumerated in `r0035-stage-pins.json`.
`hosted-native-r0035-stage-source-controls` registers the Node argv with protocol
`auto`, expected count 12, owner R0035 and its test file covered; its input closure is
the Node control, materializer, stage pins and the two original lab modules.
Node's control invokes Python for the actual transformation. Use the normal
`PYTHONUTF8=1` and `PYTHONDONTWRITEBYTECODE=1` environment and preserve both runtime
identities.

Those command input closures classify their included source files, without
duplicate module/exclusion entries. Native roles remain documented through these
explicit CLIs. Central lane/coordinator commands include their complete imported
stage-source closure. Focused control status is separate from actual native
admission and from the full registered population.

The opt-in campaign field is `r0035Stages`; absent/false retains every original
argv. The selected campaign uses only Chromium R0035 guard-off/all/timing, one
round and the existing 15-second interval. Stage preparation failure blocks that
lane without an uninstrumented fallback. Original sources, preparation/build
code, namespace, recipient and envelope remain unchanged.

The final driver receipt hashes the complete three-trial observation population
and original summary. The coordinator verifies each observation's original
report, source flags and measured window, main's absence of stage markers, and
both experimental raw traces. Original failures stay failed. Complete original
admission plus supplemental custody yields only `OBSERVED_STAGE_DIAGNOSTIC`,
with explicit instrumented timing and no owner acceptance.
