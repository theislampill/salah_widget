# PR #43 independent review — request changes before merging

**Repository:** `theislampill/salah_widget`  
**PR:** https://github.com/theislampill/salah_widget/pull/43  
**Reviewed product commit:** `e3b042f17048fce8577cd08140f306cbce2d7f3c`  
**Latest checked PR head:** `f0647b44e10c9ce4f80895b52861893c347512fd`  
**Checked base/main:** `18ff14860ff41c084b1db5f396bb62aa9c22b1be`  
**Declared runtime SHA-256:** `4c764068d0d19afe4d440376ed765a373c7afead594b5d16ef22402dd02ef799`  
**Declared root SHA-256:** `51c09cfdd0bb535018ba76c02878c7bb8574b82a957de0c62392ed379f4834ef`  
**Review date:** 9 October 2026.

## Decision

**Do not manually merge this head yet. Request changes.**

This is a source-and-focused-browser-probe review, not a certification of every changed file or a rerun of the complete scientific/browser campaign. It establishes a new critical-path coupling that needs correction and complete-entry qualification, and a reproducible font/layout cache defect. These are separate from the already disclosed S1 timing/coverage and R0022-L1/S10 lighting gaps.

The useful startup implementation should be retained. The recommendation is a bounded revision, not a restart of V5, CP9, the original issue audit, or the completed DAG planning programme.

The PR advanced during review from `e3b042f` to `f0647b44`. GitHub's commit comparison lists only the reconciliation documents and `.gitattributes` in that increment, with no runtime source or generated runtime changes. The product findings below therefore still apply to the latest checked head. GitHub reported the PR open, draft, unmerged and mergeable. Mergeable is not an acceptance verdict.

No GitHub files, comments, reviews, branches, issues, deployment or owner worktrees were modified by this review.

## Finding R1 — P1: the initial Moon payload now blocks execution of the core app

### Source locations

- `tools/build_moon.py`, `initial_boot`, `host`, and the `boundary='\nboot();'` injection.
- `tools/build_native.py`, head first-paint construction and subsequent Moon expansion.
- `real-sky/native-first-paint.mjs`, `prepareNativeFirstPaint()`.
- `src/native/index.html`, the main classic script, `boot()` and `enableSettingsAffordance()`.

[Current Moon builder](https://github.com/theislampill/salah_widget/blob/e3b042f17048fce8577cd08140f306cbce2d7f3c/tools/build_moon.py) · [Baseline Moon builder](https://github.com/theislampill/salah_widget/blob/18ff14860ff41c084b1db5f396bb62aa9c22b1be/tools/build_moon.py) · [First-paint owner](https://github.com/theislampill/salah_widget/blob/e3b042f17048fce8577cd08140f306cbce2d7f3c/real-sky/native-first-paint.mjs).

### What changed

The baseline appends the Moon host as a separate script after the native application's script. The native `boot()` has already run before that optional Moon script is encountered.

The PR instead embeds the entire host, including a base64 representation of the 3,965,156-byte initial receiver data, **inside the native application's existing classic script, immediately before `boot()`**. A classic script cannot execute its preceding native declarations and initialise the app while the trailing script text is still arriving. Moving a function declaration earlier within that same script does not remove this dependency.

The author reports that the HTTP root grows from **547,654 to 6,082,431 bytes**. This is an unconditional delivery cost, including documents whose daytime presentation does not need an initial Moon. These are document sizes, not measured compressed wire sizes.

Separately, `prepareNativeFirstPaint()` still runs in the head and can prepare a CSS sky background with catalogue stars. It does not render the initial lunar surface. Consequently a progressively delivered document can have card markup and a prepared background while the core native script—including settings wiring, current native geometry, provider dispatch and lunar initialisation—has not executed.

This changes the dependency from “optional Moon refinement takes time” to “the core app must receive the newly enlarged inline astronomy script first.” It also leaves another route to a background appearing before its principal Moon content. Faster local terrain replacement does not prove that this cold-entry route is acceptable.

### Independent discriminator

`probes/browser_probes.py` models the two **actual script-order structures**, using the transcribed candidate `boot()` with deterministic boundary stubs. It uses incremental `document.write()` in isolated Chromium to withhold the end of the inline payload and its closing script tag. It is not a full-widget HTTP performance test.

While the corresponding Moon tail was withheld:

| Structural arrangement | Card layout present | Main native script executed | Settings stub wired | Prayer request stub dispatched |
|---|---:|---:|---:|---:|
| Baseline — native script completes before optional Moon work | Yes | Yes | Yes | Yes |
| Candidate — Moon tail is inside native script | Yes | **No** | **No** | **No** |

Releasing the tail permits the candidate script and boot sequence to execute. This confirms the causal parser/execution coupling. The deliberately small synthetic filler isolates ordering; it is not a replica of the production receiver binary and is not used to calculate latency.

**Evidence confidence:** high for the source dependency and parser mechanism. The incidence, compressed transfer cost and complete-widget visual delay on the owner's production network were not measured here. The PR itself explicitly marks throttled initial-document loading unqualified.

### Required revision and proof

Make first-scene delivery genuinely bounded without forcing the entire multi-megabyte astronomy representation ahead of core native execution. The exact approach needs source-aware engineering: a more compact equivalent representation, an appropriately bounded initial path, or another demonstrated design may be suitable. Preserve current phase, source identity, approved size, opacity, Earthshine, numerical bounds and full V5 refinement.

Simply externalising the same seed and allowing the Moon to pop in later is not sufficient. Hiding the whole widget until it arrives also fails the owner's requirement. Do not solve the issue by lowering final quality, introducing a legacy Moon, or replacing the real stars.

Add tests that control **the actual initial HTML response**, not only `native-data.js`, terrain assets or fonts. Include a held/streamed tail before the native script terminator, cold compressed transfer, normal foreground entry, and documented cache-warm/new-document controls. Use a known accepted observer/time so acquisition is not a confounder. Verify actual settings interactivity and prayer/provider readiness in addition to first-scene pixels. Retain the reviewed head as the failing control and show the revised full entry meets the applicable, explicitly scoped acceptance contract.

Any proposed amendment to network/entry acceptance must be visible and owner-approved; it cannot silently turn this release gap into a pass.

## Finding R2 — P2: nonblocking font CSS can permanently cache fallback layout

### Source locations

- `src/native/index.html:11`: font stylesheet changed to `media="print"` with `onload="this.media='all'"`.
- The same file, `fitCn()`: `_cnFit` key, early return and final `document.fonts.check(...)` cache admission.
- `tests/real-sky/native-startup-critical-path.test.mjs`: font test checks nonblocking link activation, not subsequent layout correction.

[Native source](https://github.com/theislampill/salah_widget/blob/e3b042f17048fce8577cd08140f306cbce2d7f3c/src/native/index.html) · [Critical-path tests](https://github.com/theislampill/salah_widget/blob/e3b042f17048fce8577cd08140f306cbce2d7f3c/tests/real-sky/native-startup-critical-path.test.mjs).

### Failure mechanism

The nonblocking stylesheet permits the first prayer-name fit to happen before Fraunces has even been registered in the document's font set. The existing guard assumes that `document.fonts.check('600 24px "Fraunces"')` being true establishes that fitting against the intended display font is safe to cache.

That assumption is false when the face is absent. The method can return true for a nonexistent/unregistered family. [MDN's API documentation](https://developer.mozilla.org/en-US/docs/Web/API/FontFaceSet/check) explicitly describes this behaviour.

`fitCn()` then caches only the current prayer key, sunrise and sunset. When the stylesheet and face later arrive, normal `fitCn()` calls return at the cached-key check. The previously calculated font size, top position and spacing remain tied to the earlier metrics until some other event changes that key. The font can change while the fitting remains stale.

The underlying guard predates this PR, but changing stylesheet delivery exposes a new absent-font-before-first-fit state that the former blocking stylesheet did not ordinarily permit on successful loading. Keeping font CSS nonblocking is desirable; its arrival must invalidate or re-key the affected measurement cache correctly.

### Independent discriminator

The Chromium probe executes the transcribed `fitCn()` on a controlled SVG rail/text DOM. Initially no face is registered under Fraunces. A late `@font-face` registration uses a locally installed test font under that family name. **It is intentionally not the real Fraunces font** and the measurements are not product screenshot metrics.

| Probe stage | Font set | Cached size | Measured text width |
|---|---|---:|---:|
| First fit before the face exists | Empty; `fonts.check()` nevertheless true | 23.7 px | 96.953 px |
| Face arrives; ordinary `fitCn()` called | Face loaded | **23.7 px, unchanged** | **114.094 px** |
| Same state; explicitly clear `_cnFit` and fit | Face loaded | 20.2 px | 97.234 px |

The stale-cache path and its explicit-invalidation control are reproduced. This establishes the cache defect, not the exact visual magnitude with the owner's font delivery or every prayer name.

### Required revision and proof

Keep font loading nonblocking. Track the relevant stylesheet/font readiness or a font-metric generation and perform an actual bounded refit when the real face becomes available. Do not use `fonts.check()` alone as proof that an absent family has loaded. Handle stylesheet/font failure with a stable fallback, without continuous expensive refitting or blocking astronomy/prayer readiness.

Test delayed CSS registration, delayed font bytes after CSS registration, successful arrival, permanent failure and warm-cache loading. In a real browser use the actual authored widget and supplied display font, check at least Forenoon and long prayer labels, and retain captures demonstrating rail clearance, baseline positioning and hero-time alignment. The reviewed source must fail the relevant regression control; the correction must pass without reverting the nonblocking stylesheet.

## Existing residuals — not new attribution by this review

The author's records honestly keep these open:

- **S1:** Chromium cold accepted-to-receipt 289.1 ms versus 250 ms, reload added time 276.5 ms versus 250 ms, plus capture-coverage gaps. Captured co-appearance does not qualify every earlier frame. These are retained author measurements, not new timings measured here.
- **R0022-L1/S10:** the excessive bright-Moon atmospheric hotspot and grey wash. Baseline/candidate attribution is already retained. PR43 does not fix it; do not repeat its investigation just to discover the same owner.
- Actual extension/new-tab-parent coverage and original callback-cost qualification remain separate obligations.

[Qualification and measurements](https://github.com/theislampill/salah_widget/blob/e3b042f17048fce8577cd08140f306cbce2d7f3c/docs/real-sky/CELESTIAL_STARTUP_QUALIFICATION.md) · [Startup specification](https://github.com/theislampill/salah_widget/blob/e3b042f17048fce8577cd08140f306cbce2d7f3c/docs/real-sky/CELESTIAL_STARTUP_RLGWO.md).

An incremental merge could eventually be judged separately from complete closure of #33/#34. Neither a documents-only DAG compatibility receipt nor the fact that a pre-existing defect has a future owner waives acceptance of a newly introduced regression. This review does not require every unrelated DAG task to finish before PR43 can be reconsidered.

## Work worth preserving

Source inspection supports the intended separation of an explicitly labelled current initial tier from full adaptive refinement. The initial Moon path rechecks native authority before adoption. The bootstrap stars use the same source catalogue rather than random replacements. Existing source/scope/phase controls remain visible in the reviewed admission code. The copied scientific core, V1 and full scientific asset paths were not listed as changed in the product diff.

The author reports 679 passing focused tests, 40 numerical initial/final comparisons, retained lifecycle/recovery evidence and deterministic builds. Those are useful supplied evidence, **not tests independently executed by this reviewer**. A passing local suite does not cover a scenario its fixtures do not exercise. In particular, the new font test checks the media switch and the new boot test exercises queued turns using stubs; neither tests the two findings above end-to-end.

## Review execution and limits

Fresh checks here used installed Chromium **144.0.7559.96**, Playwright and an isolated browser context. `probe-results.json` binds the local excerpt and harness hashes and records the successful reproduction of R1's structural coupling and R2's font-cache race.

The current repo was accessible through the GitHub connector. A full clone/served-widget run was not available in this environment: Git transport failed, and the attempted local HTTP browser navigation was rejected by the environment's administrator policy. That rejection is retained in `localhost-probe-environment-limit.log`; no browser security policy was bypassed. The final probes therefore use in-memory documents and an installed local font, with no production requests or real user profile.

The included native functions were manually transcribed from the connected head source with comments omitted, not obtained from an independently checked-out full source tree. Their hashes are evidence of the included probe inputs, not proof that an entire repository checkout was reproduced. The probe accepts `--native-source` so the executor can rerun the actual authored file slices. Stubbed provider/UI boundaries and structural filler are clearly marked.

An additional candidate hypothesis—deferred provider dispatch stalling in a `display:none` iframe—**did not reproduce** in this Chromium fixture. It is not a finding. Background-tab and other-engine scheduling remain outside this probe's coverage.

This review did not independently run Firefox, the actual owner extension, the complete 679-test suite, full V5 numerical qualification or the production network. Runtime hashes above are supplied/published identities; the full generated runtime was not independently rebuilt here. These limits are not silently converted into passes.

## Handoff to the DAG executor

Use the existing planning package at `21e7a84365fae37a86cae5c7d5e41008c0adc53f` and its PR43 supplement at `f0647b44`. Incorporate R1 into the current startup/entry/critical-path obligations and R2 into the appropriate existing startup/native-layout obligation. These are **local review finding labels**, not new canonical RLGWO IDs.

Add the necessary dependency/acceptance amendments to the active execution ledger with review provenance. Keep the historical plan immutable. The supplement's assertion that only retained timing/coverage work remains in the startup lane must now be expanded to account for the new findings.

Independent DAG tasks may continue. The startup PR remains unmerged until these findings are resolved and the actual resulting head is reviewed. A complete proof for an issue must still cover every mandatory obligation; review readiness, draft publication and graph compatibility are not closure.
