# R0007 exact successor qualification review — FINAL

**Disposition: PASS at the bounded qualification-instrument scope.** Candidate `2f2d64c5ee27708937dfcaa1233272f0cfa54ddc` closes this reviewer's QR-B20-01 and QR-B20-02 against the exact committed bytes and the controls below. No new concrete blocker was found in the successor delta. This is a plain engineering review finding, without formal audit-assess, dispatch, integration or closure authority. **Native/platform qualification, independent pixels and first-visible recovery remain pending.**

## Attribution, immutable inputs and review boundary

- model_requested: inherited parent model; no override requested
- model_actual: GPT-6 Astra Pro (self-report from active developer identity; an independent backend model identifier is not exposed)
- authoring_context_reuse: no
- other_reviewer_output_seen: no
- accepted_product_base_commit: `5e946fe18a31750cf528bd58210ce79182dcf1e1`
- accepted_product_base_tree: `6e9eced1194d2463f5090fcdb086e771e1100916`
- prior_reviewed_commit: `b20e3aa64f4cec47a8b025be1b77a9b9c0bb955b`
- prior_reviewed_tree: `1666a919dc9d197e9ff95d28eb013470ba822d5c`
- candidate_commit: `2f2d64c5ee27708937dfcaa1233272f0cfa54ddc`
- candidate_tree: `c8693811c4dfe73b2810e7bb5f6cb81f33019d1a`
- native_executed: no

This review used a clean, detached, sparse local clone under its own review directory. The clone reads local Git objects; no remote operation was performed. All 20 selected materialized inputs were compared byte-for-byte with the exact candidate's Git objects, then reverified after testing. The actual candidate's binder also verified all 147 bound files against committed blob identities. The review does not depend on later changes to the root agent's working tree. `input-manifest.json`, `isolated-checkout.json`, `verification.json` and `actual-bound-packet.json` retain these bindings.

The repository AGENTS and requested audit playbook, including its Finding Row Contract, were read during the preceding review. That reviewer's own report, original counterexample and exact prior inputs were reused for the permitted closure comparison. No other reviewer or Andon report was opened; the permitted contract/ledger contain historical references and terse descriptions, whose linked reports were not followed or used as independent evidence. No agent-list query was made. The separate publication transport repair is outside this assessment.

Only this review directory was written. The target repository, index and refs were not mutated. The repository's pure Git tests create and commit synthetic objects in temporary repositories within this review directory, as expressly permitted for these controls. Their browser/driver tests replace native browser, server and process boundaries with mocks. The actual clean binding probe calls `clean_identity`, `select_cases`, `bind_packet` and `validate_cases` directly; it never calls a main/producer or launches a browser/server. No hosted workflow, target commit, push, merge, deploy, certification or issue closure was performed.

## Exact reviewed-file hashes

| File | SHA-256 |
|---|---|
| `tools/cp9/r0007_font_observer.js` | `ca8fcb547fca54e5edd8ba40c896497c6cda75b38acc7a6e4df276a2eeb21d1b` |
| `tools/cp9/r0007_browser.py` | `ac626e916160ef1359bdddf022483ac5d0602626e29439253fd4ddb253c2a48e` |
| `tools/qualification/r0007_native.py` | `d57416ad259713887ecfe913eed1ed509abbe589ccfe4bd5fae2a4a3722c156e` |
| `tests/r0007-recovery-precondition.test.cjs` | `213f525684ca81b9271cabdba58e6238cde3bf88b02b6d013b52cf4884638e19` |
| `tests/test_r0007_native_qualification.py` | `358cae9819d8ed140327439df28080c1bbeddd406db207b5527697b318543899` |
| `tests/rlgwo/R0007-next-event-recipes.json` | `baf7f41745a5cfde1ee8277caa25afb0c19edbca4f452f21ee248621be3963c6` |
| `.github/workflows/r0007-native.yml` | `1f452298e3bed7572640ffb8a7e3d58392eb32fa1378d6a4ba4dd11e820f54e9` |
| `src/native/index.html` | `e8603192a095cd8682c35416f3ecca00938d772f5152324b37f9928077eac037` |
| `tests/rlgwo/prayer-browser-fixture.cjs` | `12e37a2dc97719c3e05de9095b5aa26833f99bdb09bf664d381373cbf09ea18f` |
| `tools/cp9/browser_runtime.py` | `af7e6376ac8fe3c731ea1e215dac37faadc48f1f766a6bdf32637426e1daa4e0` |

## Verification and preserved boundaries

| Control | Observed result | Retained evidence |
|---|---|---|
| Exact repository qualification tests | 24/24 pass, exit 0 | `qualification-tests.log` |
| Exact repository font/barrier tests | 16/16 pass, exit 0 | `font-barrier-tests.log` |
| Existing browser selector tests | 5/5 pass, exit 0 | `selector-tests.log` |
| Independent observer scheduling/lifecycle probes | 7/7 pass, exit 0 | `observer-adversarial-probe.cjs`, `observer-adversarial.log` |
| Actual clean committed candidate binding and driver validation | 147 files; 30 cases; 21 healthy before 9 mutants; `PREPARED_NOT_EXECUTED` | `verify-candidate.py`, `candidate-binding.log`, `binding-validation.json`, `actual-bound-packet.json` |
| Protected product/generated/shared object comparison | All 13 selected trees/blobs identical to accepted 5e base | `protected-identities.json` |
| Recipe delta and immutable-input verification | All 30 expected arrays unchanged from accepted base; clocks/ingress unchanged from b20; only four wait predicates changed; all 20 manifest inputs still match exact commit | `recipe-delta.json`, `verification.json` |

Protected equality covers `src`, `index.html`, `offline.html`, `config.js`, `builder.html`, `tools/build_native.py`, `real-sky`, `moon`, `vendor`, `v1`, the shared prayer fixture, browser runtime and runtime-identity helper. A matching directory tree covers all its tracked descendants. No regeneration or product/runtime edit is present in these objects.

The four changed cases are `NE07-recovery24`, `NE07-recovery12`, `NE07-dst-recovery24` and `NE07-mut-remove-next-dirty`. For each, the only changed case field is one existing wait predicate immediately before tomorrow's release. Every other action field, including timeout/deadline, remains identical to b20; clocks, ingress rules and expected results remain identical. The added observer conjunct does not wait for a desired prayer result or cause a product render. All 30 expected arrays also match the accepted product base directly.

## QR-B20-01 — Closure of unobserved font completion-event terminality

- **Category / severity:** Tests and validation; prior medium qualification-precondition gap. **Disposition: closed for this exact successor's instrumentation scope; PASS.** No pinned-native incidence claim is added.
- **Evidence:** The original four predicates admitted a synthetic schedule with `ready` fulfilled and dirty clear while the exact product's terminal callback remained queued. The successor installs the bound observer using `context.add_init_script` before creating the page (`r0007_browser.py:225–230`), and validation requires the observer in the source binding (`41–48`). The observer captures the native timer before document scripts (`r0007_font_observer.js:5`), records actual event type and face identity, increments pending work during dispatch, and grants typed receipts only in that captured one-shot task (`32–47`). `settled` requires loaded set status, zero pending receipts, no observed lifecycle error, and the proper receipt for each loaded/error relevant face (`27–30`). All four predicates retain actual stylesheet receipt/media, layout, `fonts.ready` and dirty-clear requirements and add this observer condition.
- **Counterargument tested:** An early observer's own listener or a microtask continuation between listeners cannot establish that later product listeners have run. The independent probe explicitly executes a predicate at an inter-listener microtask checkpoint. It remains false while `pendingDeferred` is one; the later product listener sets dirty, and even after terminal credit the predicate stays false until that dirty work clears. The test also replaces the public timer after initialization with a throwing wrapper: the observer still uses its captured native timer, without entering the fixture/product timer ledger.
- **Impact / resulting behavior:** The previous queued-terminal counterexample now discriminates correctly for all four exact predicates: b20 returns true under that schedule, the successor returns false, then returns true only after terminal dispatch, deferred receipt and dirty clearance. Missing receipts do not gain acceptance merely from readiness or status. Mixed success/error needs distinct typed receipts. Empty/wrong-type terminal events do not create credit; descriptor changes, observed reloads and replacements invalidate the static-lifecycle claim.
- **Effort:** Small completed change confined to R0007 instrumentation, recipe predicates and their tests; no product or shared runtime repair was needed.
- **Risk:** A native engine that exposes a relevant already-loaded face without an observable terminal event will fail this setup gate rather than receive guessed credit. The actual engines must establish whether that availability issue occurs. The lifecycle diagnostics cover observed changes under the explicitly static authored-font startup scope, not arbitrary future font manipulation or every possible unseen mutation.
- **Confidence:** High for exact code binding, pre-document installation in the driver control path, typed/deferred observer behavior and the synthetic discriminator. Native scheduling, font-service availability and exact Windows-engine behavior remain unverified.
- **Fix sketch / implementation route:** Implemented as an R0007-owned read-only observer installed by the R0007 driver; four recipes require its result. Event records, face metadata, lifecycle diagnostics and pending work are exported on success and on captured failures (`r0007_browser.py:349,371`). No product-state, clock, font-load or DOM mutation is introduced by the observer. Its native one-shot receipt tasks are separate from the product loop.
- **Repair class:** instrument/acceptance defect.
- **Owner/source:** `tools/cp9/r0007_font_observer.js`, `tools/cp9/r0007_browser.py`, the four recipe waits and `tests/r0007-recovery-precondition.test.cjs`.
- **Acceptance criteria:** Queued terminal events cannot release a held reply; terminal success/error and no-face stylesheet-error fallback remain usable; delayed stylesheet registration/layout-discovered work remains held; expected prayer values, clocks, ingress and deadlines remain unchanged. All criteria are satisfied at the pure-instrument level by the exact candidate and tests. Actual first-visible recovery remains a separate pending criterion.
- **Verification:** Sixteen repository setup controls pass, including both event/readiness orders, mixed outcomes and fallback. Seven independent probe groups additionally cover the b20/successor discriminator for all four predicates, inter-listener checkpoints, multiple pending tasks, captured-timer independence, descriptor/reload diagnostics, empty events and reverse wrong-type credit. The original own b20 RED remains retained unchanged in the preceding review directory. No real font service or browser timing was observed.
- **Rollback / Plan Closure:** Closure applies only to the named committed successor. Reverting or bypassing the observer/predicate binding reopens this row; preserve the prior RED and current probes. Any rollback should remain confined to this instrumentation and must retain the native gate as pending.
- **Rejected/deferred rationale:** The earlier stronger assertion of a pinned Chromium/Firefox failure remains rejected: the original finding was a specification-permitted synthetic ordering, with contrary retrieved engine implementation evidence and no exact pinned-native reproduction. This successor removes that ordering assumption without resolving the historical incidence question. No new browser-source archaeology was performed.
- **Remaining risk:** Native first-eligible/first-visible recovery, real font callback behavior, optional assets and host scheduling still require retained native evidence. The static startup barrier does not promise that no later action can initiate a new font load.
- **Route:** default runtime pressure / dispatch-review; evidence returned for root disposition, with no dispatch authority conferred.

## QR-B20-02 — Closure of uncommitted source claiming committed provenance

- **Category / severity:** Provenance and input contracts; prior medium supported-custom-recipe gap. **Disposition: closed for this exact successor's stable candidate input boundary; PASS.**
- **Evidence:** `bind_packet` reads the immutable captured commit's recursive tree, requires each bound path to be a regular file blob with mode `100644` or `100755`, and supplies that blob identity to the same streaming read that calculates the file's SHA-256 (`r0007_native.py:103–149`). The Git blob hash includes the actual byte length and contents; a mismatch raises before binding (`35–48`). Thus clean status alone cannot supply commit membership, and an ignored source or changed assume-unchanged path cannot acquire provenance merely from its filesystem hash. The mandatory observer is included in this mechanism.
- **Impact / resulting behavior:** An ignored custom recipe or declared extra source is rejected; changed tracked recipe/driver bytes concealed by assume-unchanged are rejected. The actual clean candidate still binds successfully: 147 files, exact candidate commit/tree, unchanged selected case values, and `BOUND_CANDIDATE_NOT_EXECUTED`/`BOUND_NOT_EXECUTED` status. Driver validation independently accepts those actual hashes for all 30 cases and returns `PREPARED_NOT_EXECUTED`.
- **Effort:** Small completed source-membership/blob comparison and real-Git controls.
- **Risk:** Byte-changing checkout normalization will cause a rejection. This is consistent with the exact-byte contract, and the unchanged Windows workflow explicitly disables `core.autocrlf`. The reviewed repository uses SHA-1 Git object identifiers; the comparison is scoped to this repository, without a portability claim for other object formats. No transactional protection against an adversarial concurrent writer is asserted.
- **Confidence:** High. The new negative controls use isolated actual Git repositories and real commit/index semantics, and the positive check uses the exact complete bound inputs from the reviewed commit rather than placeholder sources.
- **Fix sketch / implementation route:** Implemented at the launcher input boundary: immutable tree membership plus actual committed-blob byte verification, covering every recipe/source claimed in the packet. Existing path containment/symlink checks and subsequent driver SHA validation remain present.
- **Repair class:** instrument/acceptance defect.
- **Owner/source:** `tools/qualification/r0007_native.py`, `sha`, `bind_packet` and `tests/test_r0007_native_qualification.py`.
- **Acceptance criteria:** Reject ignored/untracked recipes and sources before any producer; reject concealed changed committed bytes; accept a clean committed recipe and its valid case selection; preserve healthy-before-mutant order and source drift rejection. Exact-candidate binding plus the repository controls satisfy these criteria.
- **Verification:** Real disposable-Git tests q13–q16 cover committed positives, ignored recipes, assume-unchanged recipe and driver drift, and ignored declared extras. All pass within the 24-test qualification suite. The independent clean-candidate probe verifies all 147 bindings and all 30 cases, including the observer's expected SHA-256. The original own ignored-recipe RED remains retained unchanged in the b20 review directory.
- **Rollback / Plan Closure:** Closure is bound to the exact membership/hash guards in this candidate. Removing either guard reopens the row; keep the real-Git negatives and actual-candidate positive. Any future packaging/normalization change needs equivalent exact-byte evidence.
- **Rejected/deferred rationale:** The prior finding did not allege that the fixed hosted default recipe was already uncommitted. This closure establishes the supported boundary without asserting hostile writer/race immunity or native evidence acceptance.
- **Remaining risk:** Committed source membership is only provenance. Actual producer execution, current final source hashes, native results and independent acceptance still need their own receipts.
- **Route:** default runtime pressure / dispatch-review; evidence returned for root disposition.

## Unchanged qualification controls and open gates

The successor changes no cleanup, capture-association, executable-selection, healthy/mutant adjudication or hosted-workflow policy. The rerun qualification controls continue to exercise rejection of missing terminal summaries and malformed evidence, capture ordinal mismatches without pixel credit, actual selected executable binding, launch-failure classification and cleanup-dependent launch progression. These mocked tests verify checker decisions; they do not establish real process teardown or native executable behavior.

The workflow blob is identical to b20: its branch/path restrictions, exact checkout, read-only contents permission, private dependency/evidence directories, pinned Playwright package, serial Chromium/Firefox plan, collection/job limits and artifact retention are unchanged. Its selection remains 17 default plus 4 conditional preservation cases and 9 mutants, giving 30 cases per engine. No native workflow ran in this review, and the new observer adds no shared browser or host process. Its work is limited to event records, scans and one-shot tasks in each owned page.

The previous deadline limitation remains: the unchanged font wait can outlast the already-held product request's deadline. A slow or failing native asset environment can therefore fail acquisition. That is not mutant-kill credit or permission to relax a deadline. The retained source checks also still distinguish eventual-state captures from first visible recovery; no passing checker status accepts pixels.

**Required handoff:** native event receipts, all-render traces and retained video must still establish actual first eligible/visible recovery and preservation, with independent review and the required Windows two-engine qualification. Required merge order remains **R0017 → R0007 → R000B**. Preceding accepted-main reconciliation, exact owner approval of head/base/tree and all delivery/certification/issue-closure gates remain binding. This bounded PASS closes only the two reviewed instrumentation findings against `2f2d64c5ee27708937dfcaa1233272f0cfa54ddc`.
