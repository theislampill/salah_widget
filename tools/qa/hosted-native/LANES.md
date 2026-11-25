# Native source preparation and initial lane commands

These entries prepare disposable source and emit commands. They never launch a
browser or establish isolation. The coordinator supplies the verified isolated
executor, executes one browser driver at a time, and retains all observations
privately. Software checks and preparation are separate from native evidence,
human judgment, owner selections and work-order acceptance.

## Source preparation

```sh
python tools/qa/hosted-native/prepare.py \
  --research /task/research \
  --baseline /task/baseline \
  --historical /task/historical \
  --out /task/work/prepared
```

`research` must be a clean genuine Git checkout at
`55d1b3edb66d2c35679707120b01ee1d3455e4a3`, tree
`0e626139b28bffe8f308173f806cad21bfeeb7bb`. `baseline` must be a clean
checkout at `df644ef60156b67b5c487395176369bcec7a0d7b`, tree
`11117a0ba83c3db632bf4482c2db8feb5d52a769`. Both need the complete tracked
`src`, `real-sky`, `tools`, `moon`, `vendor`, `v1` and `tests` directories.
Research also needs the R0040 compressed option patch. Baseline needs its root
generated entries and inventory. Sparse checkouts may omit unrelated evidence.
When R002F is enabled, both checkouts also need exactly
`docs/state-contracts/evidence/R002B/config-e11bdd3d/ci-build-pages-payload.json`.
Preparation checks actual source bytes against the pinned Git blobs, including
materialized files whose changes could be hidden by sparse status.

`historical` supplies `tools/qa/precip_eval_lib.cjs` from
`4029d2f67f5a880c8ad889443bb7557d96022c45`. A minimal archive is sufficient:
the helper is checked against SHA-256
`a02358979e9aa2f968c5ca9dde4ec7a8e63db869b871f1c24ce65a68e71497e7`.
It does not need Git metadata.

The output must be absent and outside the input trees. It contains:

| Path | Purpose |
|---|---|
| `receipts/prepared.json` | Terminal `PREPARED` or `INCOMPLETE` disposition, source identities, generated hashes and tree paths |
| `receipts/*` | Exclusive command logs, command status/time/cleanup receipts, source manifests and the lab identity |
| `trees/main` | A real disposable clean baseline checkout, retaining the published star driver's Git guard |
| `trees/r0040` | Disposable authored option patch and canonical generated outputs |
| `trees/r0035` | One materialized lab shared by both experimental write arms |
| `trees/r003f` | Git-blob-verified copy of baseline `index.html`, `config.js`, `moon`, `real-sky` and `tests/r0002-ordinary.json`; every copied body/mode is bound to HEAD and recorded in the private manifest |

The detached baseline worktree shares local Git objects with the supplied baseline checkout;
keep that checkout available through the observation. Preparation builds main
and R0040 twice. R0035's published materializer runs its first canonical build;
preparation runs its second. Every second build must report 0 written, 117
unchanged and 0 removed, and every generated inventory member is hash-checked.
All three trees run frozen V1 verification with its disposable tamper control.
R0040's authored preimage, compressed patch, authored postimage, generated index,
offline entry and inventory match the retained research pins. R0035's generated
index and inventory match its retained pins.

Preparation exits 0 only after all checks. Exit 2 leaves any admitted output and
private failure receipts intact. An existing output is never repaired, removed
or reused. Command timeouts kill the process group and retain their logs. No
native claim follows from `PREPARED`.

Copy `receipts` into the private capture before sealing. The large disposable
public source trees can stay outside that capture and can be removed after the
observations. A failed source tree is retained until its failure has been
inspected; no failed receipt is rewritten.

## Declarative command plan

```sh
python tools/qa/hosted-native/lanes.py --plan-json \
  --prepared /task/work/prepared/receipts/prepared.json \
  --out /task/capture/lanes \
  --python-playwright /task/python-playwright/bin/python \
  --node /task/node/bin/node \
  --node-modules /task/node-dependencies/node_modules \
  --pngjs /task/node-dependencies/node_modules/pngjs \
  > /task/capture/lanes.json
```

The new output directory receives `r0035-plan.json`. Stdout contains only the
JSON command plan; it includes private paths and belongs inside the encrypted
capture. Explicit executable paths are required. The Python venv symlink path
is preserved so it selects the installed Python Playwright. Node package
directories must identify Playwright 1.62.1 and pngjs 7.0.0. Acquisition owns
package integrity, Python Playwright 1.57.0 and browser-binary verification.

The top-level protocol is `salah-hosted-native-lanes/1`. `lanes` is an ordered
array. Each entry supplies `id`, `workOrder`, `argv`, `cwd`, `env`, `output`,
`stdout`, `stderr`, `timeoutSeconds`, `result.kind`, `result.path`,
`exitStatuses`, `dependsOn` and `stopScopeOnAndon`. Execute argv directly,
without a shell, under the coordinator's isolation boundary. The coordinator
must create the stream files exclusively, preserve timeout output and clean up
children. Each recipe creates its own fresh `output` directory.

The plan also records `workOrders` and the boolean `evidenceRetention` mode.
`--work-orders` accepts a nonempty list drawn from `R0040 R003F R0035 R002F`.
Identifiers must be distinct and known, and selecting R002F requires `--r002f`;
enabling R002F while excluding it is also rejected. Selection preserves the
canonical order above. Without the selection switch, the existing three work
orders are emitted, plus R002F when enabled. The initial hosted campaign enabled
R002F and contained all four work orders and five command rows. R0035 defaults
to both timing and capture with their original dependency. The checked-in
follow-up selects only R0035 Chromium timing with guard off, all-source replay
scope and explicit preparation-stage observations. Previously obtained native
results remain separate; no other workstream is repeated by this campaign.

Selection limits observation commands. Common source preparation and the
original star-plan validation remain unchanged. The coordinator checks the
exact selected lane identities, including engine/DPR and the selected R0035 rows.
Missing selected rows are retained as `NOT_RUN` with preparation `INCOMPLETE`;
duplicates, unknown rows and unselected work-order commands are rejected before
execution. Earlier failure/Andon evidence remains unchanged when a later
campaign selects independent work orders.

| Initial invocation | Exact scope | Result interpretation |
|---|---|---|
| R0040 Chromium | Nine published option cells: day rain/drizzle/thunder, night, twilight, reduced none/still, motion override and dry; DPR1 | Exit 0 plus all nine `native-options.json` cells establishes that recipe's observations. Exit 1 retains preceding PNGs and failure logs. |
| R003F Chromium DPR1 | Offset, B0, repeat B0 and unboosted reference; original 150 s refinement gates | Exit 0 is `MEASURED`; 2 is `INCOMPLETE`; 3 is isolation failure and stops every lane; 4 is an Andon and stops R003F progression. Original sandbox, refusing proxy, WebSocket guard and assertions remain unchanged. |
| R0035 Chromium timing | One 15 s dark/normal/ordinary-clock round, all three arms, DPR1 | Exit 0 alone proves no admission. Inspect every summary row's `admitted` and `qualification` fields. |
| R0035 Chromium capture | Separate one-round 15 s PNG acquisition after the timing attempt | It has separate output and classification. `dependsOn` requires that timing finished; a capture cannot erase a failed timing result. PNG acquisition bounds are separate from presentation timing. |
| Optional R002F Chromium DPR1 | One round of real offscreen restoration at Fajr/Maghrib/midnight, plus native preview upload-fault retention and clock-discontinuity withdrawal | Exact protocol, observer/source identities and complete requested report population are required. Original `FAIL`, `INCOMPLETE` and `INCONCLUSIVE` are preserved. No presented-frame or elapsed-cost claim. |

The R0035 comparison uses the published `independent-reconstruction` plan.
`main` is clean baseline. `unmodified` and `mitigated` share one lab identity.
Their flags differ only in `r35arm=full` versus `changed`; both have
`r35scope=all&r35amplitude=1&r35glass=0.5&r35margin=4`. Both probe the real
`stars.status == active` field. The existing driver's source/arm checks run
before command emission. These experimental settings select no production
amplitude, glass or magnitude policy.

The planner also accepts `--r0035-guard default|off`,
`--r0035-scope all|preview-members` and `--r0035-mode both|timing|capture`.
The corresponding campaign dictionary is `r0035` with `guard`, `scope` and
`mode`; its defaults are recorded as `r0035Controls` in the plan and observation.
Default controls leave every original lane argument and star-plan entry
unchanged. Nondefault controls require selected R0035 observations, and the
coordinator requires the plan's controls to match the requested campaign.

`guard: off` adds `r35guard=off` symmetrically to the two experimental arms.
The existing lab switch removes suspension and its gain ramp, so the result
is explicitly a diagnostic ablation. It does not change main, source admission,
producer `active` admission, the original 100 ms cadence gate, amplitude,
glass, margin, duration, scene, motion or ordinary clock. Earlier default-guard
failures remain intact and no production guard policy is selected. The existing
`preview-members` scope is another symmetric diagnostic population; it does not
remove all preparation of the accepted full source or establish a magnitude
cutoff. Timing-only selects one timing row; capture-only selects one capture row
without a nonexistent timing dependency. Both retains the original dependency.

### Optional preparation-stage diagnostic

`--r0035-stages` (campaign `r0035Stages: true`) is an explicit opt-in. Its absent
or false value preserves the original argv. It requires selected R0035 timing
only, and cannot combine with the per-event `--retain-evidence` wrapper.
The current diagnostic retains one round, 15 seconds, all three arms, ordinary
clock, dark scene and normal motion. It changes no original predicate or cadence
gate and supplies no production guard or replay-scope decision.

After successful common preparation, `r0035_stage_materialize.py` runs as a
separate bounded child. The coordinator retains its actual return code, timeout,
stdout/stderr, exact argv, original source plan, original preparation/process
receipts and original lab identity under private
`capture/r0035-stage-preparation`. The derivative stays under
`work/r0035-stages`. Both its own identity and distinct plan are retained
privately. A failed or incomplete optional preparation emits a blocked stage
row with empty argv; selected independent work orders remain available.

The planner checks actual exit zero, current source hashes, complete original
and derived byte populations, and exact current source flags. Native invocation
passes the expected preparation receipt SHA-256 to
`observe_r0035_stages.py`. That wrapper verifies current namespace and successful
preparation before loading the original driver, and separately re-admits the
original plan plus diagnostic derivative. The original source checker remains
strict; changed bytes never satisfy its original reconstruction receipt.

The original `summary.json` and each `trial.json` are unchanged. Separate stage
receipts bind each raw observation and original trial hash, the final original
summary, source identities, selected argv and preparation receipt. Classification
requires the exact three-arm population, including main's expected absence of
stage instrumentation. Raw prefixes survive stage validation errors; unavailable
page extraction is separately identified. Original failures remain `FAIL`,
timeouts remain incomplete, and veto/outer namespace precedence is unchanged.
Complete original admission plus complete supplemental custody yields only
`OBSERVED_STAGE_DIAGNOSTIC`. All timing is explicitly instrumented, with no
estimated overhead subtraction and no worker/page clock subtraction. See
[R0035_STAGES.md](R0035_STAGES.md).

### Corrected lunar baseline

`--r003f-harness corrected-b0` (campaign `r003fHarness: corrected-b0`) selects
the separately identified correction described in [R003F-HARNESS.md](R003F-HARNESS.md).
Default `published` preserves the original recipe. The corrected selection is
invalid when R003F is unselected. Its disposable source is prepared outside
private capture; only the materialization receipt and process streams enter
private capture. Both actual process success and the exact reviewed receipt are
required. The planner rechecks all seven output helpers, rejects symlinks and
changed bytes, and emits a blocked lane without an executable fallback if
preparation is incomplete.

The existing R003F lane ID, generated runtime, capture paths, original arguments,
900-second budget and exit meanings stay the same. Only the driver source path
changes to the admitted disposable correction. The plan names `r003fHarness`
and the complete expected helper identity; the coordinator rejects a mislabeled
uncorrected lane. A corrected successful report must bind that identity, the
baseline index, engine/DPR and all four expected captures with both UI receipts.
The pinned corrected driver owns semantic UI admission; the coordinator checks
receipt presence/identity and cannot substitute a `MEASURED` status alone.
Original physical assertions precede UI admission, and isolation/Andon outcomes
retain priority over missing or mismatched corrected-report metadata. The raw
earlier B0 report is preserved with its derived harness-faithfulness rejection.

The existing R0040 and R0035 recipes do not persist a detailed request ledger.
Their pre-page fixture/abort routes remain unchanged; the coordinator retains
its independent network-boundary controls. No missing ledger or fixture
consumption evidence may be inferred from kernel isolation. R003F does persist
its request ledger. All outputs and logs remain private, including failures.

### Optional supplemental retention

`--retain-evidence` wraps selected original R0040 option/R0035 commands. The hosted campaign
equivalent is `evidenceRetention: true`; absence means `false`. Both wrappers
come from the coordinator checkout and execute the hash-pinned original drivers
from the immutable research checkout. The unchanged original argument suffix
follows `--`, including `--capture`; the Python venv path is preserved. Original
result kinds, report paths, expected populations and admission rules are unchanged.

Each instrumented lane adds an `evidenceRetention` object with its original
argv, distinct private `<lane-id>-retention` output, and explicit timing/capture
overhead. Host serialization, hashing, fsync and copying affect observations.
These measurements cannot be treated as uninstrumented performance evidence.
No supplemental journal replaces an original success report, and an actual
nonzero child exit remains nonzero even if the original report is complete.
The direct native CLIs and source/partial-evidence protocol are documented in
[EVIDENCE_RETENTION.md](EVIDENCE_RETENTION.md).

Instrumented lanes declare `stopAllOnExit: [86]`. This means
`EXTERNAL_CONTINUATION_VETOED`: an attempted external continuation was prevented
before the real action, not an observed network escape. The coordinator writes
the inner verdict with actual child exit 86 and then exits normally; its admitted
receipt stops every later lane. Actual namespace exit 86, timeout, abnormal exit
or missing receipt still takes precedence. R003F's separate isolation exit 3
and workstream Andon exit 4 remain unchanged.

The revised R0040 capture mode below always uses its own final-state wrapper,
independently of `evidenceRetention`. Setting that flag as well does not wrap it
twice. The current follow-up leaves generic retention disabled. Further
selections and instrumentation remain conditional on inspecting actual results.

`--engine firefox` or `--engine webkit` emits the same bounded initial plan for
that installed engine. `--r003f-dpr 2` changes only R003F; the other two existing
drivers fix DPR1. These switches acquire separate observations rather than
expanding the claimed coverage of the first run. Meaningful next work includes
engine counterparts, B0 DPR2 and initial/refined comparisons, R0035 nine-round
WebKit timing with native reduced/full-motion and phase/glass coverage, and
R0040's remaining motion/lossless-capture rows. Admission failures require
diagnosis before credit; R003F Andon stops its progression. None of these rows
supplies physical-device or human evaluation.

## Optional revised R0040 capture

`--r0040-mode options|capture` is available in both planner and observer;
`campaign.json` uses `r0040Mode`. The absent-field/CLI default is `options`, with
the unchanged nine-cell invocation above. `capture` requires selected R0040 and
Chromium. It names only `chromium / bday / moderate / M1 / common`, DPR1, genuine
main. It does not select a different model, engine, dispersion or product arm.

After successful common preparation, the coordinator executes the exact entry
in [R0040_CAPTURE_PREPARATION.md](R0040_CAPTURE_PREPARATION.md). Disposable
patched sources are under `/task/work/r0040-capture`, outside private capture.
The two preparation layers are deliberately separate:

| Private path | Custody |
|---|---|
| `r0040-preparation-entry.json` | Coordinator-observed **entry** return code, timeout, source hash and command |
| `r0040-preparation.stdout`, `.stderr` | Actual entry streams, including failed/late finalization |
| `r0040-preparation/process.json` | Guarded-recipe **child** status and exact source/preparation receipt binding |
| `r0040-preparation/recipe.stdout`, `.stderr` | Guarded-recipe streams and partial exceptions |
| `r0040-preparation-original/*` | Unmodified original recipe receipt and patch logs, including completed stages of a failed attempt |

The planner receives these additional arguments:

```sh
--r0040-mode capture \
--r0040-work /task/work/r0040-capture \
--r0040-process /task/capture/r0040-preparation/process.json \
--r0040-entry-process /task/capture/r0040-preparation-entry.json
```

It requires actual entry exit zero, child exit zero, no timeout or receipt-copy
failure, and matching input paths. It then calls the reviewed capture wrapper's
read-only `verifySources` export, without importing a browser. That function
checks all **six** patched historical sources, **12** immutable research inputs,
the **116** generated main members and **177** main runtime files, complete patch
stages, hashes, actual clean main HEAD and the original preparation receipt.
The native wrapper repeats its source check before importing the driver.
Failed or missing optional preparation yields an explicit `NOT_RUN` rain lane
with preparation `INCOMPLETE`; the other selected prepared lanes may continue.
No option-driver fallback is substituted for a failed capture request.

The original positional capture command is preserved behind
`retain_r0040_capture.cjs`; see [R0040_CAPTURE_RETENTION.md](R0040_CAPTURE_RETENTION.md)
for the full CLI and source hashes. The lane ID is `r0040-chromium-capture`.
`R0040_DISPERSION=common` is the only added environment value, and
`R0040_OPTIONS` is removed from the actual child environment. Original
`capture.json` and PNGs stay under that lane's fresh output; the journal and
`final-admission.json` are separate in `r0040-chromium-capture-retention`.
Every path remains private. The capture process-group bound is **180 seconds**;
preparation entry is bounded to **240 seconds**, containing its unchanged
180-second recipe bound. Read-only planner verification has a 90-second child
bound within a 120-second planner bound. The overall observation ceiling still
applies, and unreached selected lanes remain `NOT_RUN`.

Acquisition requires actual capture child exit zero, the original report with
the pinned source/cell metadata, its exact final-receipt hash, successful
context/browser/server cleanup, and the final wrapper receipt. The resulting
status is **`ADMITTED_FOR_OFFLINE_VERIFICATION`**, with native qualification
`NOT_VERIFIED` and human acceptance `OUTSTANDING`. Overall `OBSERVED` can contain
this acquisition status alongside other admitted observations; it never means
the lossless verifier passed. A missing or partial receipt is `INCOMPLETE`, a
recorded acquisition/original failure stays `FAIL`, and timeout retains partial
originals. Prevented continuation retains exit 86 and stops all later lanes;
actual abnormal outer namespace completion retains precedence.

After private retrieval, the coordinator runs the unchanged
`lossless_pack.py cell <capture.json> --pins <pins-revised.json>` with its existing
Pillow/cryptography environment. No new hosted package is acquired. The exact
frame count, gap, average-rate, audit-match, pixel, geometry and visibility gates
remain the original verifier's responsibility. No cadence tolerance is widened.

## Optional R002F preparation and command

The coordinator first runs the unchanged common preparation, then separately
runs the guarded `r002f_prepare.py` wrapper. It retains the optional process
result even if the build fails or times out. The planner receives
`--r002f --r002f-prepared /task/work/r002f-prepared/build-result.json`
and `--r002f-process /task/capture/r002f-preparation-process.json`, plus
`--r002f-dpr`, `--r002f-rounds` and `--r002f-section`. See [R002F.md](R002F.md) for
the full builder and native CLI, immutable hashes and source contract.

Before emitting a runnable R002F command, the planner checks successful process
completion, build receipt custody, both actual generated inventories and the
reviewed probe SHA-256. It adds a 900-second lane using explicit Playwright,
baseline/candidate and output paths, with `--timeout-ms 60000`. All output and
streams are beneath the private lane directory; both disposable source arms
remain outside capture. Failed or missing optional preparation adds an explicit
blocked row with an empty argv, while the existing four command rows remain
unchanged under the default selection. The coordinator never executes that blocked row and never hides it
from the campaign result.

The workflow reads validated `campaign.json` directly. Its engine and R003F DPR,
and the R002F enable/DPR/round/section values, are propagated into each isolated
phase, together with selected work orders, stage diagnostic controls and
supplemental-retention mode.
A later engine or DPR observation can therefore use a new campaign
without editing the probe or published recipes. Each such observation still
requires its own actual native admission.

The original R0040 cover option remains 85/86 against the original fixtures;
the separate input-keyed reference fixture's 86/86 does not replace it. R0035's
original producer remains unavailable, and this lab is an independent
reconstruction. R003F's full matrix, strict native DB3, owner thresholds, tone
waiver, human viewing and adoption remain open. No registry verification level
or original requirement changes here.

## Offline controls

```sh
python tools/qa/hosted-native/test_lanes.py
```

The controls reject wrong/dirty source identity, changed generated bytes,
reapplication of the real pinned option patch and reuse of failed output.
They check actual recipe argv, the unchanged star flag parser, shared lab
identity, the active producer probe, separate timing/capture outputs and the
engine/DPR distinction without importing Playwright or launching a browser.
They also verify optional-preparation failure retention, the frozen R002F
command/hash, its exact private paths and the R002B sparse-checkout inclusion.
The source materialization command above is the separate real-build check.
The registered capture preparation and retention commands contribute 10 and 16
additional controls. Central controls run an actual guarded-recipe child on
small pinned fixtures, reject its second-stage postimage, preserve the successful
first stage and both original/final logs, and keep independent lanes runnable.
They also reject absent/status-only capture receipts, altered metadata, changed
CLI/environment, missing source population and late outer failures. These are
offline instrument controls, not native capture evidence.

The registered retention controls run the actual source-pinned recipe functions
with browser doubles. The coordinator controls additionally prove campaign
option propagation, unchanged default invocations, distinct instrumented outputs,
selected-population completeness and veto/outer-failure precedence. None of those
controls launches a native browser or supplies a product acceptance result.

The registered stage controls execute 15 Python cases and 12 Node cases against
the actual original sources. Central controls additionally run the actual
materializer on bounded source/Git fixtures and the original native driver with
explicit browser doubles. They bind preparation status, source flags, native
receipt population and original reports through final classification; exit zero
with a failed original admission remains failed. These controls do not observe
native rendering or measure instrumentation overhead.
