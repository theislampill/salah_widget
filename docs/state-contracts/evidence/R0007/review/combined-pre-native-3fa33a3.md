Reviewer attestation:
- reviewer_identity: /root/r0007_candidate_review
- requested_model: gpt-6-astra
- actual_model: gpt-6-astra (self-report: GPT-6 Astra Pro; no separate backend telemetry available)
- authoring_context_reuse: no
- other_reviewer_output_seen: yes — an incidental, out-of-scope publication-template review summary was returned by a status tool after this review's analysis; see independence disclosure below
- base_sha: 5e946fe18a31750cf528bd58210ce79182dcf1e1
- head_sha: 3fa33a3bf07841082da711a89ceff0691c16937e

Report state: FINAL

# Combined pre-native candidate review

## Disposition

**GAP-REVISE for the combined pre-native code/recipe scope.** One important qualification-recipe finding remains: the new font readiness predicate can pass before the nonblocking font stylesheet registers its faces, leaving the font wakeup confounder possible in the complete next-day-wakeup mutant. The collector still rejects a surviving mutant, so this is a qualification reliability and unnecessary-run-cost gap, not a false native PASS or a newly discovered product defect.

The product source acceptance at `5e946fe18a31750cf528bd58210ce79182dcf1e1` carries forward by exact byte comparison. SRC-01 and SRC-02 remain resolved. The other reviewed launcher, observer, capture-accounting, cleanup, currentness, and workflow changes have no concrete critical, important, or minor finding from this review.

Critical findings: **0**. Important findings: **1**. Minor findings: **0**.

This report supplies neither native acceptance nor whole-owner acceptance. Actual first-visible recovery, independent pixels/video, platform/preservation obligations, final integration currentness, the accepted merge order, and owner approval remain pending. The reviewer has no merge or native-dispatch authority.

Candidate tree: `28047019c4dc62a7558c518f33357bcb68594dab`. The original whole-source comparison base remains `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b`; this review evaluates the combined delta from the already reviewed source successor above.

## Important finding QUAL-01: the font barrier admits the pre-stylesheet state

**Owner:** R0007 native recovery recipe author.

**Locations:** `tests/rlgwo/R0007-next-event-recipes.json:1219`, `:1498`, `:3436`, and `:5612`; explanatory claim at `:91`. The relevant unchanged product owners are `src/native/index.html:11` and `:3200`–`:3227`. The supported observer path is `tools/cp9/r0007_browser.py:312` and `:335`–`:343`.

All four new waits use this predicate:

```javascript
document.fonts.status === 'loaded' &&
window.__prayerFixture.readSnapshot().dirty === false
```

The authored Google Fonts stylesheet is intentionally nonblocking: its link starts with `media="print"` and switches to `all` only on its load event. The source's font-fitting owner explicitly accounts for a stylesheet registering faces after the first fit. Consequently, the first actual prayer render and an idle dirty flag do not establish that the font stylesheet has already registered its faces. An empty font set can report `loaded` while that stylesheet is still pending. Neither the new predicate nor the preceding case actions require the existing fixture's terminal LINK asset receipt or any registered-face state.

**Reproduction and consequence:** I evaluated the exact committed predicate in a disposable Node VM with an empty iterable font set, `status: 'loaded'`, and the read-only dirty observation false. It returned true. I then executed the exact `cnFontChanged` function extracted from the committed product source; the dirty flag became true. No browser or product checkout was mutated for this probe.

The corresponding allowed event sequence is:

1. The current prayer record renders while the optional stylesheet is still pending; the frozen loop clears its dirty flag.
2. The new wait passes because no registered face is presently loading. The held tomorrow reply is released.
3. In the complete next-day-wakeup mutant, the reply is admitted but both designated prefetch wakeups have been removed.
4. The delayed stylesheet registers/loads its font faces. The unchanged font completion callback sets `_renderDirty=true`.
5. That unrelated wakeup permits the original loop to render the recovered endpoint before the later capture. The intended mutant assertion can survive, and the collector correctly returns `MUTANT_NOT_QUALIFIED`.

The supported `--video-only` path makes the missing prerequisite particularly clear: it skips the screenshot call entirely, so no incidental screenshot font wait can establish a stronger barrier. I do not claim to have reproduced this timing in a native engine, or that every current host run will encounter it. The source-level defect is that the predicate does not enforce the documented readiness condition and therefore does not eliminate the stated confounder.

**Required correction:** establish a terminal observation for the actual authored font stylesheet, followed by terminal actual font-loading state and a clear existing dirty flag, before releasing the held reply. Handle a terminal font-service failure consistently with the unchanged optional-font/fallback behavior. Keep this in observation/recipe scope: do not call render, advance the fixture clock, wait for a target value, change the prayer deadline, or replace the scheduler. Add a focused predicate/control case for “stylesheet still pending, empty font set, dirty false”; that state must remain held. A terminal settled font state with a clear dirty flag should release, and dirty true should remain held. The corresponding native healthy/recovery/mutant evidence is still a later gate.

The recipe's `recoveryConstraint` and `docs/state-contracts/R0007.md` should describe the actual enforced barrier rather than saying the present condition removes the font-finalization confounder completely.

## Exact product-source rebind

The following committed files and their working copies were byte-identical between the accepted source successor and the combined candidate. No full product cohort rerun was necessary for this unchanged source after the earlier independent 288-test/V1/parity review.

| File | SHA-256 at the combined candidate |
| --- | --- |
| `src/native/index.html` | `e8603192a095cd8682c35416f3ecca00938d772f5152324b37f9928077eac037` |
| `index.html` | `983f8b609eba48821e8d8c539cca7d0b9e40caf3f35a924514a4e93eb24766e9` |
| `offline.html` | `697ed290d2f71a777b9c1a44c3d7b12350cd51dfc66648e8c8907ff897e9be57` |
| `moon/BUILD.json` | `225938b31cef0136e76a9ca5c9482eeede7b2e52f10f148bea13ecb7d56d1c93` |
| `tests/prayer-next-event-state.test.cjs` | `3671ddda05287150269e58a1ebca5b94cfcbd908965e5db1425364c8c19ff696` |
| `tests/rlgwo/prayer-browser-fixture.cjs` | `12e37a2dc97719c3e05de9095b5aa26833f99bdb09bf664d381373cbf09ea18f` |
| `tools/cp9/browser_runtime.py` | `af7e6376ac8fe3c731ea1e215dac37faadc48f1f766a6bdf32637426e1daa4e0` |

Thus the previously reviewed chronological selector, one-sided gap bounds, canonical small-year dates, unique-inverse endpoint behavior, valid-current/missing-endpoint distinction, completed-render envelope, and protected science/scheduling boundaries are unchanged. This is an exact rebind to the earlier source review, not an inference from a new test count.

## Qualification mechanisms assessed

### Binding, assertions, and mutants

`tools/qualification/r0007_native.py:54`, `:95`, and `:394` enforce a clean exact commit/tree, bind the selected case values and required source/fixture/driver/runtime bytes, check currentness before each producer, and check the identity and hashes again before aggregate success (`:420`). Selection adds declared healthy controls and puts them before expected-failure cases. Binding checks that each selected case is unchanged as a JSON value.

At `:256`, healthy source credit requires a terminal producer, a matching one-case terminal summary and trace, an actual completed-render receipt, matching source/fixture hashes, a concrete selected-engine executable identity, intact declared capture evidence, empty page-error/unexpected-provider lists, and the declared passing status/exit. A mutant additionally requires accepted same-engine healthy controls, exit 1, a FAIL trace, the declared variant, and an `AssertionError` containing the exact intended failure text. A generic failure, timeout, missing anchor, or unrelated assertion does not become a killed-mutant result.

I inspected all nine intended mutant declarations and their healthy controls. All 30 recipe documents instrumented successfully in memory against the exact current generated entry without mutation-anchor drift. Every case has captures. One healthy control intentionally contains the wall-countdown variant and survives under ordinary arithmetic; counting every variant-bearing case as an expected failure would be incorrect.

### Cleanup and serial orchestration

`tools/cp9/r0007_browser.py:371` writes the trace, closes the context and browser, stops Playwright, and shuts down/closes the server before appending the terminal receipt and writing the final summary. A cleanup exception therefore withholds the terminal summary. The collector requires that summary to match the actual case/status/trace path (`tools/qualification/r0007_native.py:274`).

The launcher stops every later case/engine if cleanup is not established (`:416`). An explicit pre-action browser-launch/context failure with established cleanup leaves the rest of that engine unattempted while allowing the other engine to be attempted (`:391`). The aggregate requires all planned cells, no unattempted cells, accepted source assertions, and cleanup on every result (`:422`). This includes the last/only case, where a cleanup failure previously could escape a next-iteration-only check.

The producer retains actual command, PID, terminal state, timeout/containment result, and log. Timeout containment is scoped to its owned process/group and never earns assertion credit. These code properties do not independently prove that any particular native browser actually terminated; that remains an observation obligation.

### Executable and capture identity

`tools/cp9/r0007_browser.py:15` resolves and hashes the selected executable, passes that exact path to launch, and preserves the existing sandbox options. Its identity is written after the real launch, with actual browser version and headed/headless mode. `tools/qualification/r0007_native.py:183` verifies the requested family, host, concrete absolute file, hash, and Chromium sandbox request. Generic prose about a managed browser no longer satisfies executable identity.

Each declared capture now has a separate disposition. The collector checks its metadata, its named actual checkpoint/ordinal, the original video artifact, and a nonempty still when full-viewport capture was requested (`:199`). Missing artifacts, malformed evidence, and mismatches are distinguishable. An ordinal mismatch can retain source assertion credit but remains explicitly unverified; a later/latest capture is `EVENTUAL_STATE_ONLY`. A matching first-render receipt is merely `RECORDED_PENDING_INDEPENDENT_REVIEW`. The overall first-frame/pixel acceptance stays pending even with matching ordinals.

The driver no longer aborts subsequent recovery acquisition solely because an early first-capture association mismatched. It retains the mismatch for every capture name and continues the original assertions/video (`tools/cp9/r0007_browser.py:335`). The change does not turn a later still into a first-visible proof.

## Recipes and Windows scope

JSON comparison against the accepted-source candidate found exactly four changed cases, each adding only the readiness wait before the held reply release: `NE07-recovery24`, `NE07-recovery12`, `NE07-dst-recovery24`, and `NE07-mut-remove-next-dirty`. Their ingress records, fixed clocks, first-render predicates, and expected values are unchanged. QUAL-01 concerns whether that added wait establishes its intended condition, not an oracle substitution.

The own Windows workflow binds checkout to the triggering SHA, uses read-only repository permission and pinned action revisions, avoids persisted checkout credentials, preserves setup command exits/logs, uses private runner paths, and invokes both engines serially. The actual selection expression and launcher selection produce **30 cases per engine, 60 cells total**: 17 default healthy/control cases, 4 conditional preservation cases, and 9 intended mutants. Healthy/control/preservation cases precede the mutants. The four preservation cases are included for this new environment instead of relying on historical equivalence.

The workflow retains setup failures and native artifacts with `if: always()`. Neither the job's success nor the launcher's exit 0 is coded as pixel or whole-owner acceptance. Package availability, the hosted runner's actual browser/compositor behavior, Windows cleanup, and the sufficiency of its actual preservation evidence were not exercised here.

## Independent verification

Performed in the exact candidate checkout, without browser/server/network effects:

| Check | Observed result |
| --- | --- |
| `python -B tests/test_r0007_native_qualification.py` | 19 tests passed, no failures/errors |
| `python -B tests/real-sky/cp9_browser_runtime_test.py` | 5 tests passed |
| Current 19 qualification tests with exact `5e946fe` helper modules loaded only in memory | 37 failing assertions/subtests, 0 errors; demonstrates discrimination against the prior helper behavior |
| Additional production-driver cleanup exception probes at context close, browser close, Playwright stop, and server shutdown | All four retained the trace, withheld final summary, and received no collector acceptance/cleanup credit |
| Additional removal of the synthetic video's actual file or the synthetic PNG | Both rejected capture/source credit as `UNVERIFIED_NO_CAPTURE_ARTIFACT` |
| Recipe instrumentation and case/control selection | All 30 instrumented; no anchor drift; 60 planned workflow cells; all declared controls ordered before mutants |
| Exact new font predicate with empty font set, followed by actual source font callback | Predicate passed before registration; later callback dirtied the renderer, supporting QUAL-01 |
| Source and raw-evidence hashes | Final verification source hashes/log hashes and recipe-precondition digest matched the committed files |

The tests explicitly use synthetic temporary evidence and mock native side-effect boundaries. They are meaningful tests of collector parsing and production driver sequencing, not real application rendering, actual process cleanup, or pixels. The earlier raw RED logs preserve 16/18-test stages and the single capture-binding failure; the final logs accurately report 19/5 passing tests. I independently checked their SHA-256 bindings and reran the final suites. No author report was used as a substitute for these checks.

A broad base-to-head `git diff --check` reported trailing spaces in the preserved raw unittest RED output. Those are raw log bytes, not executable source defects; the recorded final diff check correctly identifies its narrower three-source-file scope. I did not rewrite the evidence to hide its original output.

Reviewed mechanism digests:

| File | SHA-256 |
| --- | --- |
| `tools/qualification/r0007_native.py` | `c3182108b4852fb4b1c1b72315f5e458e43565a6fa817f73f2e209be51a33124` |
| `tools/cp9/r0007_browser.py` | `40127a417130898107198d342014e7214a2bce70baef71b801b5824152bb9c24` |
| `tests/test_r0007_native_qualification.py` | `8c3b3dd2d1561a6ead2dee94da9ec351b2deaa77b741e9102992aff7e7c00e0f` |
| `tests/rlgwo/R0007-next-event-recipes.json` | `0c878d11d368137a9171ec1abeeb63cc687d7bfc50fca27455f59029c3c591ea` |
| `.github/workflows/r0007-native.yml` | `1f452298e3bed7572640ffb8a7e3d58392eb32fa1378d6a4ba4dd11e820f54e9` |

## Declined judgments and pending gates

I did not launch or inspect a native browser, use a hosted resource, dispatch CI, publish anything, mutate Git/index/HEAD/branches, inspect native-Andon material, read another review report, or change implementation. The report is the only retained reviewer artifact written in the repository. Temporary pure-test fixtures were disposed of by their test cleanup.

I decline to judge actual native setup, final rendering/pixels, actual first eligible visible recovery, native font timing, platform delivery, and real process cleanup because no permitted native observation was supplied or performed in this scope. Source receipt and still ordinal equality cannot settle those questions. I also decline final latest-accepted-main reconciliation and whole-owner closure: this local code review cannot supply either authority or current integration evidence.

The accepted merge order remains R0017 → R0007 → R000B. Concurrent isolated engineering does not change that order. Resolve QUAL-01, review the exact successor delta, and preserve the independent native/platform/preservation and owner-approval gates. This report does not authorize a merge or claim merge readiness.

## Independence disclosure

The assigned analysis, all mechanism test results, and the QUAL-01 source finding were developed without seeing another reviewer's output. After communicating that finding to the parent, I called the team status tool. It unexpectedly returned a completed final summary from the separate publication-template reviewer. I did not open that report or use its conclusions; its template work is outside this candidate qualification review. I immediately disclosed the incidental exposure to the parent. Because that summary was visible, the requested unqualified `other_reviewer_output_seen: no` would be inaccurate, so the attestation above records the exposure explicitly. A governor requiring the literal no-exposure invariant must treat that reviewer-provenance condition as unmet rather than silently accepting a false attestation.

The checkout was clean at `3fa33a3bf07841082da711a89ceff0691c16937e` / tree `28047019c4dc62a7558c518f33357bcb68594dab` at the initial and last read-only identity checks. All conclusions in this report bind those exact committed bytes, regardless of later parent-owned changes.
