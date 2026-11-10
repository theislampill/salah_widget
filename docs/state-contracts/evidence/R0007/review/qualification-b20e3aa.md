# R0007 independent pre-native qualification review — FINAL

**Disposition: GAP-REVISE at the bounded qualification-instrument scope.** The existing 19 qualification, 5 browser-selector and 9 readiness tests pass. Two gaps remain below. This is evidence for the root to adjudicate, not formal audit-assess authority, an authorization to change source, or native/platform acceptance.

## Attribution and exact binding

- model_requested: inherited parent model; no override requested
- model_actual: GPT-6 Astra Pro (self-report from active developer identity; independent backend model identifier is not exposed)
- authoring_context_reuse: no
- other_reviewer_output_seen: no
- base_commit: `5e946fe18a31750cf528bd58210ce79182dcf1e1`
- base_tree: `6e9eced1194d2463f5090fcdb086e771e1100916`
- candidate_commit: `b20e3aa64f4cec47a8b025be1b77a9b9c0bb955b`
- candidate_tree: `1666a919dc9d197e9ff95d28eb013470ba822d5c`
- review_environment: Linux x86_64; Python 3.12.14; Node v24.22.1
- native_executed: no

The base/head trees were resolved from Git objects. Every exercised candidate input was exported from `git show <candidate>:<path>` to this review's isolated test-input directory and rehashed against both its initial manifest and the exact commit at completion. All 19 exported files still match. No later working-tree bytes are credited. `input-manifest.json`, `protected-identities.json` and `verification.json` retain the machine-readable bindings.

The repository AGENTS and the requested audit playbook, including the Finding Row Contract, were read. The permitted R0007 contract and acceptance ledger were inspected for scope and gate requirements; their historical review references/terse dispositions were not followed to reviewer reports. No prior R0007 review report or author reasoning was opened. A whole-tree **path listing only** was initially too broad and truncated; it provided no content evidence. Subsequent reads were bounded to declared code, tests, inputs and permitted contract/ledger. No target repository files, refs or index were written. Only this review directory contains this review's reports, test inputs, probes and logs. No native browser, server, hosted workflow, commit, push, merge, deploy, certificate or issue closure was performed.

## Exact reviewed-file hashes

| File | SHA-256 |
|---|---|
| `tools/qualification/r0007_native.py` | `c3182108b4852fb4b1c1b72315f5e458e43565a6fa817f73f2e209be51a33124` |
| `tools/cp9/r0007_browser.py` | `40127a417130898107198d342014e7214a2bce70baef71b801b5824152bb9c24` |
| `tests/test_r0007_native_qualification.py` | `8c3b3dd2d1561a6ead2dee94da9ec351b2deaa77b741e9102992aff7e7c00e0f` |
| `tests/r0007-recovery-precondition.test.cjs` | `38cd0bb7b949150e315f8fe59e1eb71c6bfddc0184ff77f8f33bb2fbcf964bdf` |
| `tests/rlgwo/R0007-next-event-recipes.json` | `dd9b1c82e5f758909049cf5b404c759890c4b138fbdeee22326e1a2de0e14ec7` |
| `.github/workflows/r0007-native.yml` | `1f452298e3bed7572640ffb8a7e3d58392eb32fa1378d6a4ba4dd11e820f54e9` |
| `src/native/index.html` | `e8603192a095cd8682c35416f3ecca00938d772f5152324b37f9928077eac037` |
| `tests/rlgwo/prayer-browser-fixture.cjs` | `12e37a2dc97719c3e05de9095b5aa26833f99bdb09bf664d381373cbf09ea18f` |
| `tools/cp9/browser_runtime.py` | `af7e6376ac8fe3c731ea1e215dac37faadc48f1f766a6bdf32637426e1daa4e0` |

All protected trees/blobs compared equal between the accepted source base and candidate: `src`, `index.html`, `offline.html`, `config.js`, `builder.html`, `real-sky`, `moon`, `vendor`, `v1`, shared prayer fixture, shared browser runtime and runtime-identity helper. Git object identities are retained in `protected-identities.json`; directory equality here covers every descendant tracked by that tree.

The recipe population is 30 cases. All 30 `expected` arrays are unchanged as parsed JSON from the base. Exactly four cases change, solely by adding one pre-release wait: recovery24, recovery12, dst-recovery24, and mut-remove-next-dirty. Their ingress, clock, other case fields and oracles are unchanged. This verifies preservation of the declared inputs/oracles; it does not execute their native assertions.

## Verification performed

| Invocation | Result | Evidence |
|---|---|---|
| `python tests/test_r0007_native_qualification.py` in exact snapshot | 19/19 pass, exit 0 | `qualification-tests.log` |
| `python tests/real-sky/cp9_browser_runtime_test.py` | 5/5 pass, exit 0 | `selector-tests.log` |
| `node --test tests/r0007-recovery-precondition.test.cjs` | 9/9 pass, exit 0 | `barrier-tests.log` |
| `node --test font-event-order-probe.cjs` | Four intended counterexample failures, four settled positives; exit 1 | `font-event-order-probe.log` |
| `python currentness-selection-probe.py` | Five positive controls, one intended untracked-recipe failure; exit 1 | `currentness-selection-probe.log` |
| Rehash exported inputs against exact Git objects; compare protected objects and all expected arrays | All comparisons pass | `verification.json` |

The first suite mocks all browser/server/process-launch boundaries. The added probes are also pure and deliberately synthetic. Their REDs establish the stated predicate/input-boundary behavior, not native timing, font-service incidence, pixels or actual browser teardown.

## QR-B20-01 — Readiness does not establish that the queued font completion callback has run

- **Category / severity:** Tests and validation; medium qualification-precondition gap. The narrow API-contract counterexample is confirmed; incidence in the future pinned Windows binaries remains unverified.
- **Evidence:** The four inserted predicates, at recipe lines 1217–1220, 1496–1499, 3434–3437 and 5610–5613, await `document.fonts.ready`, then accept `document.fonts.status==='loaded'&&snapshot.dirty===false`. They observe stylesheet LINK terminality and active media, but no FontFaceSet terminal-event receipt. Exact product source lines 3207 and 3222–3227 sets dirty from both `loadingdone` and `loadingerror`. The independent probe extracts those exact callbacks and all four exact predicates. It resolves ready after a prior face callback's dirty work has been consumed, leaves the set-wide completion event queued, and observes all four predicates return true. The queued callback can then supply the dirty wake removed from the mutant. Four settled-callback positives still pass.
- **Primary semantic basis:** [CSS Font Loading Level 3 §3.1](https://drafts.csswg.org/css-font-loading/#font-face-set-events), “switch the FontFaceSet to loaded,” steps 3–5, sets loaded status, fulfills the readiness promise, then queues terminal-event work. [§3.4](https://drafts.csswg.org/css-font-loading/#font-face-set-ready) also limits a fulfilled promise to the relevant loading cycle. The synthetic sequence follows that API ordering.
- **Counterargument / limits:** This is **not a native reproduction**. [Blink code](https://chromium.googlesource.com/chromium/src/+/b388e927ed4f5c9ef43c899eae909195636af496/third_party/blink/renderer/core/css/font_face_set.cc), `FireDoneEvent`, dispatches terminal events before resolving ready. [Gecko main](https://searchfox.org/firefox-main/source/layout/style/FontFaceSet.cpp), observed revision `d4a99233` dated 2026-11-09, `MaybeResolve`, resolves and synchronously dispatches in the same method. Those are contrary evidence for incidence on those implementations. They were not bound to the workflow's exact future browser executables; attempts to retrieve exact release-tag source were unavailable. No claim is made that Chromium or the pinned Firefox actually exhibits the synthetic schedule.
- **Impact:** The precondition does not, at API-contract scope, prove the asserted absence of a later font wake. A recovery observation may be confounded; a remove-next-dirty mutant can survive for an unrelated reason. The collector would reject that surviving mutant rather than falsely record it killed, so this is not an aggregate mutant PASS bypass. Default healthy-only observations could still overstate which wake caused recovery.
- **Effort:** Small, bounded driver/recipe/test repair; no product algorithm change is indicated.
- **Risk:** A poorly designed replacement could miss already-fired terminal events or block terminal-error/no-face fallback indefinitely. Counting only loading starts without associating completions with faces/cycles can introduce another race.
- **Confidence:** High for the exact synthetic predicate gap and specification ordering; limited/unverified for pinned-host incidence. Do not upgrade the latter without native or exact executable/source evidence.
- **Fix sketch / implementation route:** Establish a read-only observer before document scripts can begin font loading; retain actual loading and terminal-event receipts; require relevant terminal callbacks plus actual CSS/font/layout settlement and consumed dirty work. Preserve the native font service, clocks, ingress, deadlines and expected oracles. The root has selected an R0007-owned driver observer as its proposed route; no proposed successor bytes were read in this review.
- **Repair class:** instrument/acceptance defect.
- **Owner/source:** R0007 driver/recipe readiness instrumentation; `tools/cp9/r0007_browser.py`, the four recipe waits, associated pure controls. The product callback is evidence of the competing wake, not a requested product repair.
- **Acceptance criteria:** A completion event queued after ready cannot release the held reply; settled success and terminal failure/no-face paths remain live; delayed stylesheet registration and layout-exposed loads remain held; product clocks/state and expected results remain unchanged. Actual first eligible visible recovery remains independently reviewed.
- **Verification:** Preserve this RED plus settled positives; add actual observer sequencing controls, rerun the bounded suites, bind exact successor hashes and obtain independent successor review. Native collection later must retain observed event timing and raw all-render/video evidence.
- **Rollback / Plan Closure:** Revert only the instrumentation repair if it causes setup failure; retain both the counterexample and contrary implementation evidence. Close this row only against the exact revised precondition and its discriminator, not a historical pass.
- **Rejected/deferred rationale:** Rejected the stronger claim “a pinned Chromium/Firefox failure has been reproduced.” Host incidence remains deferred to the actual native gate. Root adjudication, not this row, decides dispatch authority.
- **Remaining risk:** Optional asset callbacks outside font finalization and actual scheduling remain native-evidence concerns. No JavaScript barrier alone accepts first visible pixels.
- **Route:** default runtime pressure / dispatch-review.

## QR-B20-02 — An ignored custom recipe is not required to belong to the claimed commit

- **Category / severity:** Provenance and input contracts; medium for the supported custom-recipe path, with no demonstrated effect on the fixed Windows workflow recipe.
- **Evidence:** `r0007_native.py:54–60` accepts clean `git status --porcelain --untracked-files=normal`; ignored files are outside that status. Candidate `.gitignore:2` ignores `__pycache__/`. `main:359–362` only requires the resolved recipe to be inside the root, while its error text declares committed recipes. `bind_packet:95–125` hashes current filesystem inputs and attaches the commit/tree without checking recipe membership or comparing its bytes with `HEAD:<recipe>`. The independent probe models the clean ignored-file Git interface and supplies an ignored `__pycache__/uncommitted-recipe.json`; binding accepts it and attaches the clean commit/tree. The only tracked-file census performed is for `real-sky` and `moon`.
- **Impact:** A supported explicit `--recipe` can supply uncommitted/unreviewed cases while carrying the commit provenance intended for a committed qualification packet. It is still SHA-bound, so the bytes are not lost or silently mutable; the specific false claim is membership in the reviewed commit.
- **Effort:** Small membership/blob comparison at the input boundary, with one negative and tracked positive control.
- **Risk:** Checking only index membership is insufficient if the index/working tree are allowed to diverge; comparing against the declared immutable commit gives the intended boundary. Avoid platform newline normalization ambiguities by comparing actual expected bytes/hashes deliberately.
- **Confidence:** High for the missing membership guard and pure function acceptance. The Git interface in the probe is explicitly mocked; no target repository or temporary commit was mutated to demonstrate it.
- **Fix sketch / implementation route:** Require the resolved recipe path to identify a tracked blob at the captured commit, and compare the read bytes with that committed blob before binding. Apply equivalent requirements to any additional source paths advertised as part of that commit, or clearly separate extra hash-bound inputs from committed source identity.
- **Repair class:** instrument/acceptance defect.
- **Owner/source:** `tools/qualification/r0007_native.py`, `clean_identity`, recipe resolution, and `bind_packet`.
- **Acceptance criteria:** An ignored/untracked recipe is rejected before a producer launches; a committed matching recipe and an explicitly selected subset still bind; ordinary case/healthy-control ordering stays unchanged; drift still fails.
- **Verification:** `currentness-selection-probe.py` is the retained negative. Its five positives verify all nine mutant dependency closures/order, exact hosted 30-case selection, unsafe/duplicate/unknown names, cross-case seeding/mutant-as-control rejection, and dirty-source rejection.
- **Rollback / Plan Closure:** Revert the narrow guard coherently if it breaks supported committed recipes; retain the failed negative. Close after an exact successor rejects the negative and accepts the committed positive.
- **Rejected/deferred rationale:** No bypass of the **current hosted invocation** is alleged: it uses the existing tracked default recipe. No malicious repository author or Git-index tampering scenario is needed for, or added to, this finding.
- **Remaining risk:** The receipt is still a source assertion rather than native acceptance. Final source hashes/currentness and independent review remain mandatory.
- **Route:** default runtime pressure / dispatch-review.

## Other assessed boundaries and dismissed observations

**Cleanup and failure credit.** Driver summary emission is after context/browser/Playwright/server teardown calls (`r0007_browser.py:371–379`). A thrown teardown prevents that terminal summary, which the collector requires and binds to exactly one named trace (`r0007_native.py:266–278`). Timeout containment remains unverified and stops further launches. Aggregate completion also requires cleanup on every result (`422–425`). The pure tests verify those control decisions, not that real OS processes have disappeared. No repair finding is raised on that declared limitation; a native surviving process or terminal summary emitted before teardown would falsify it.

**Capture association.** Captures bind name, kind, predicate and receipt ordinal to a named checkpoint and retained files (`199–253`). An ordinal mismatch may coexist with accepted **source assertions**, but remains explicitly unverified for presentation. Latest recovery capture is eventual-state-only; first-frame/pixel fields never become PASS. This is deliberate separation, not a rejected-mismatch loophole. Missing files/malformed evidence fail source credit. Decodability and first visible pixels remain independent review work.

**Executable binding.** `bound_launch` resolves and hashes the file actually passed as `executable_path`; managed Chromium's alternative headless shell cannot be hashed while another path is launched. The collector checks requested family, platform, nonempty version, absolute extant file/hash and Chromium sandbox request. The shared selector is unchanged. Four mocked launch modes are tested. Actual process identity/version and executable stability are still native observations; none is invented here.

**Selection and workflow.** Every selected mutant adds its declared healthy controls, executes healthy cases first and requires accepted controls in the same engine. The workflow selects 17 default cases, 4 bounded preservation cases and 9 mutants: 30 unique cases, serially in Chromium and Firefox (60 planned observations). The four preservation cases are justified by the new environment; they do not replay a full science campaign. The pinned checkout, restricted branch/path trigger, private dependency directories, read-only contents permission, uncancelled concurrency group, 45-minute collection limit and 55-minute job limit remain scoped. No workflow was triggered during review.

**Deadlines.** The new font barrier has a 15,000 ms wait while the already-held prayer attempt retains its 10,000 ms product deadline (`src/native/index.html:1083–1087`; fixture abort propagation at `49–55`). A sufficiently slow font service can therefore end the attempt before release, producing an acquisition failure. This does not falsely kill a mutant: missing settlement/action failure cannot satisfy the collector's setup, capture and exact oracle requirements. Preserve such failures as host/input-boundary evidence rather than product failure. No timeout relaxation is requested by this report.

## Handoff boundary

Both findings are delivered for root disposition with exact code/probe evidence. Root has stated that b20 publication/native dispatch remains held while it prepares a narrow observer repair and exact successor review. This statement is context about the handoff, not a review of future code or authority to perform effects.

Independent rendered pixels, actual first eligible visible recovery and the required Windows two-engine qualification remain pending. Source tests and synthetic probes cannot replace them. Required merge order remains **R0017 → R0007 → R000B**. Preceding accepted-main reconciliation, exact owner head/base/tree approval and all terminal delivery/certification/closure gates remain binding.
