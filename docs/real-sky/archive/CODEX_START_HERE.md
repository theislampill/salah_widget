# CODEX START HERE — final cumulative Checkpoint 9

## Authority and current state

**Use this archive directly.** `widget/` is the sole authoritative cumulative product. Do not begin from the donor, CP7 viewer, older 8.3 ZIP or a GitHub branch. `CP9_RUNTIME_IDENTITY.json` identifies every widget file and the canonical tree hash; the delivery receipt outside the ZIP identifies the archive bytes. `SOURCE_IDENTITY.json` retains the user-designated native commit and exact parent/donor identities.

The starting parent is CP8.3 SHA-256 `a056d3789cb614355cc27af286907add231293ba42b2288894cdd3edca8d29a3`, native repository `theislampill/salah_widget`, commit `205750350c64b77ebdc3ebcadcc39a6eb949994b`, intended branch `integration/rlgwo-r0001-r0025-20261002`. Local uploaded custody is verified, not newly reauthenticated GitHub. No GitHub writes occurred or are authorised.

**Status: cumulative implementation delivered; expanded qualification PARTIAL.** Loaded CPU×4 response, accelerated-preview continuous availability and actual target-platform/deployment acceptance remain open. This document does not reinterpret those failures as known-limit PASS. Checkpoint 9 remains the final checkpoint. Continue via the implementation DAG, not a new numbered checkpoint.

`baseline/` retains all 162 native files; `real-sky-reference/` retains all 950 scientific reference files unchanged. `reconciliation/` contains a hash-bound comparison capsule and the historical bounded review packet, never another product authority. Older instructions inside retained history/reference/donor material are historical and subordinate to this file.

## Run the actual widget

`widget/index.html` is the normal static-folder entry; keep `config.js` and `real-sky/` adjacent. `widget/offline.html` is the deterministic single-file expansion of the same native app, not the standalone CP7 viewer. No npm/build step is needed to use the shipped candidate. Prayer and weather services still need network access; no fixture date or timetable is inserted into production.

To serve locally from the package root:

```text
python -m http.server 8765 --directory widget
```

Open `http://127.0.0.1:8765/index.html`. Alternatively open the single-file entry in a normal browser. These entry forms are supplied, but direct top-level navigation was administrator-blocked in the qualification container; their native-platform acceptance is CP9-N003, not claimed here.

A controlled native preview fragment is:

```text
#lat=24.47&lon=39.61&tz=Asia/Riyadh&label=Madinah&method=4&simTime=23:30&simWx=2&simCloud=60&simPrecip=0
```

`simTime` alone is frozen; `timeScale=1&motion=full` requests native 1× motion. Native 10×/60×/600× stress has an open availability finding. Default physical camera is 325×530, south 180°, altitude 45°, FOV90°, roll 0°, physics DPR 1. Controls `skyAz`, `skyAlt`, `skyFov`, `skyRoll`, `skyEstimates=off` and native `lp` remain explicit assumptions/settings, not measured weather or permission to move individual stars.

Diagnostics: `realSkyState()`, `realSkyFrame()` and additive `qaState().realSky`. The diagnostic frame is not render authority. Empty legacy synthetic DOM arrays are not catalogue counts. `SalahRealSkyAssets.retry()` restarts optional assets/worker after failure; worker loss explicitly withdraws sky instead of running the physical solver on the prayer event loop.

## Reproduce the sealed baseline first

Test environment recorded in `evidence/cp9/environment.json`: Python 3.13.5, Node 22.16.0, Playwright 1.57.0, Linux Chromium 144.0.7559.96, numpy2.3.5/Pillow12.3.0. These are tested versions, not assertions of unsupported minimum versions. Install `requirements-cp9-test.txt` in an isolated Python environment when needed and provision the desired Playwright browser. The delivered widget does not require these developer dependencies.

Run from this package root. Keep generated qualification evidence **outside** the sealed tree:

```text
python -c "import sys;sys.path.insert(0,'tools');from pathlib import Path;from seal_checkpoint import verify;print(verify(Path('.')))"
python tools/qualify_cp9.py --output ../cp9-local-verification
```

The full runner verifies the manifest, rebuilds integration and native test fixtures/patch, checks every payload again, executes all suites and actual-widget matrices, then verifies the manifest a final time. It expands test filenames itself, avoiding shell-glob differences. It uses controlled browser fixtures clearly separated from production.

Exit 0 means every collected mandatory gate passed; **exit 2 means executable checks passed but expanded qualification remains partial**, which is the expected CP9 disposition; exit 1 means a test/execution/invariant failure that must be investigated. `MEASURED`, engine launch, missing executables, synthetic page events and environment-blocked navigation do not count as PASS. Read `qualification.json` and each raw log, not only the exit code. The platform gate deliberately remains unqualified until CP9-N003 supplies its actual collector and accepted evidence.

For focused iteration:

```text
python tools/build_native.py
python tools/adapt_native_tests.py
python tools/build_native_patch.py
python -m unittest discover -s tests -p "cp9_*_test.py"
python tools/validate_post_cp9_dag.py
python tools/run_native_regressions.py --output ../cp9-native
python tools/cp9_performance.py --trials 5 --output ../cp9-performance
python tools/cp9_temporal_rates.py --output ../cp9-rates
```

All integration JavaScript cases are run by the full runner; on a shell with glob expansion, `node --test tests/*.test.mjs` is equivalent. Scientific commands, from `real-sky-reference/`, are `node tools/test.mjs` and `python -m unittest discover -s tests -p '*_test.py'`. Reference tests may write ignored caches, but must not change any manifest-listed byte. Do not conflate baseline fixture repairs with original native test success: read `docs/CP8_3_REGRESSION_SCOPE.md` for the four existing TODOs, unavailable historical Git comparisons and five superseded synthetic-array assertions.

## Exact files to edit — avoid generated-file loss

Readable native owners are `widget/real-sky/native-host-hooks.js`, `native-contract.mjs`, `native-engine.mjs`, `native-host.mjs`, `native-lifecycle.mjs`, `native-assets.mjs`, `native-composition.mjs` and `native-worker-policy.mjs`. `tools/build_native.py` generates `widget/index.html` from the untouched baseline plus exact adapter insertions; it also copies the retained science into `widget/real-sky/core/` and generates `native-worker.js`, `native-sky.js`, `native-data.js`, CSS and `offline.html`.

**Do not hand-edit those generated outputs or the copied core.** A new optimisation of a reference computation must live in an authored native module with oracle tests and an explicit deterministic builder import; do not modify the immutable scientific snapshot. A justified native-index change must be made through the builder, bounded to the semantic owner and accompanied by an exact preservation exception plus native tests—not a blanket source-range exclusion.

`NATIVE_TRACKED_CHANGES.patch` covers inherited native text changes; `CP83_TO_CP9_SOURCE.patch` explains readable CP9 source/harness additions and changes. Neither patch alone installs the runtime. Use the complete widget tree and rebuild it.

## Execute the actual remaining DAG

Read `docs/CP9_REPORT.md`, `docs/CP9_CROSS_FORK_DISPOSITIONS.md`, then the three required handoff files:

```text
POST_CP9_IMPLEMENTATION_DAG.md
POST_CP9_FINDINGS.json
POST_CP9_ACCEPTANCE_MATRIX.json
```

Validate the graph before work. CP9-N001 (loaded presentation) and CP9-N002 (accelerated availability) are independently ready. They may coordinate shared host interfaces but must not overwrite each other. CP9-N003's platform runner can be prepared early; final platform acceptance depends on the combined N001/N002 runtime. Each node specifies exact evidence, current owners, scope, invariants, forbidden shortcuts, tests and closure. Do not re-open closed elevation, worker-loss, mask or metadata work merely because an older review asks for it.

Keep a per-node ledger with source hashes and RED→GREEN evidence. New asynchronous presentation results must carry accepted identity/epoch and be rechecked at publication. Source failures, unknown height, strict support and unsupported performance remain explicit; no fabricated stars, silent source/coarsening fallback, private clock, donor parameter mixing or lowered test thresholds.

## Completion is evidence, not a label

Before final closure, run the full combined suites and affected native browser controls from a newly sealed/fresh-extracted tree, verify deterministic rebuild and every payload hash, collect the additional node-specific evidence and obtain independent review. All mandatory acceptance conditions must hold on that same tree. Native material/operator/motion/currentness/prayer/config invariants must survive. The provided author's self-review is not independent merge approval.

The final CP9 archive is delivered despite open qualification gates, with their implementation work-orders ready to execute. Do not rename this work Checkpoint 9.5/10, create a competing 8.3, overlay the donor or make GitHub writes without separate authorisation.
