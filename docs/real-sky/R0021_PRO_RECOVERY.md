# R0021: independent Pro recovery and remaining closure decisions

## Disposition

**PR #67 remains a draft and is not eligible for production approval.** This recovery independently inspected the actual source, original R0021 specification, accepted audit, retained evidence, and surviving original images. It found and implemented a small removal of unnecessary lunar layout work, narrowed several misleading interpretations of the remaining gates, and qualified the change with discriminating tests and two canonical builds.

The bounded correction is **implemented and source/build qualified**: 95 affected tests pass, two canonical builds have identical 142-entry runtime inventories, and frozen V1 verification passes. The initial execution-service outage was followed by a working replacement environment; the same branch was restored before implementation. This checkpoint supplies no new native S1 timing or pixel PASS, merge approval, deployment, or closure certificate.

The complete locally committed implementation is preserved in the [verified Git bundle](evidence/r0021-pro-recovery-20261018/BUNDLE.md), commit `2df6a75474f3b0fce2ba72cbf94a7640569bcf2f`, tree `99238730f8dcc37eb66ac9a21cc261fc6067628f`. This commit is contained in the archive; it is not an applied remote commit. Its runtime SHA-256 is `d82bcbd724cee5c0eae3d42c6fdb543150b00541ee73079fb26656bdf41542af`, and generated index SHA-256 is `83ac60da746661338435bf7431f0839fac13edd0d4cbc255f48d4baf4e7e0712`. The [qualification packet](evidence/r0021-empty-surface-20261018/QUALIFICATION.json) binds the actual source, assertion records, builds and limits.

**The PR branch's runnable files still contain r26.** Local Git has no authentication, and the GitHub connector's 64 MiB IPC frame limit cannot carry the 81,693,080-byte generated offline entry. This is a specific publication capability limit, not an approval denial. The complete 25,722-byte Git bundle and exact patch preserve the qualified change on PR #67 without leaving its runnable files out of sync. An authenticated Git environment must apply/push that exact candidate before it can be a remote implementation head.

This is a continuation of issue #33 and PR #67, with the existing canonical contract and source branch. It creates no replacement work order or coordinator.

## 1. Recovered subject and verified custody

| Object | Identity |
| --- | --- |
| Repository / PR / branch | theislampill/salah_widget / PR #67 / codex/r0021-startup-completion |
| Reviewed runtime-changing HEAD | feddf007e537a38972056d7d56243321884ab41f |
| Reviewed tree | 850e9386aa3d8997c6ca777586e7859229158750 |
| Production/base | f270792f39ef8bf4cabffbe6746ac0ea0dd9d3de |
| Base tree | 341ab72c6bcc34f3a6e933d0db7910c270e61cbe |
| Runtime SHA-256 | 7bf73d6b7fc3cc5ae0c6aa3e2276c8a84b5624175fa1c446f85e35bef69334f9 |
| Generated index SHA-256 | 3028b9659f04bb5ae8324040299c1d97699d0f6d0a5126d653d2d92334b7ff57 |
| Immutable specification commit | 21e7a84365fae37a86cae5c7d5e41008c0adc53f |
| Specification Git blob / SHA-256 | cfe7a5c227db9bb42f741e8b1efb4c0d042818fa / eeaff3938de670d7a83756c64f3da5f3d3370d5930e11dec97adbe395500628b |
| Accepted assessment Git blob / SHA-256 | 922ed5bdc61cffd53469e3c9251cb0b7cf05fde4 / 2a13d52f2e8a857c40626f35f0863ccbf2e204d6d42dc67e5ced235bad2e1bc7 |

GitHub fresh readbacks confirmed the PR head, base, draft/open/unmerged state, and OPEN issue. A separate source reviewer independently compared all **142 runtime entries**, including size and SHA-256, and recomputed the runtime digest above against the [r26 inventory](https://github.com/theislampill/salah_widget/blob/feddf007e537a38972056d7d56243321884ab41f/docs/real-sky/evidence/r0021-arc-samples-20261018/runtime.json). The initial checkout was clean. Production main still contains delivered R0022/PR #66.

The full canonical specification and accepted assessment were retrieved from their immutable commit. Initial local text-copy newline transformations were detected and corrected; both final byte streams matched the Git blob and SHA-256 identities above. The original issue and four published comments were read as evidence of the accepted contract and amendments.

Three fresh-context, read-only agents separately inspected startup/source correctness, callback/resource evidence, and S2–S10/Firefox visual evidence. Two subsequently reviewed the changed source and build independently of the author. Their bounded findings are normalised in [REVIEWERS.json](evidence/r0021-pro-recovery-20261018/REVIEWERS.json). They are not final release approvals.

## 2. S1: what the original frames establish

The root inspected original r105 images **15, 16, 23, 24, 26, 27**. Frame 15 shows the truthful neutral acquisition UI. Frame 16 contains the physical sky, the visible calendar Moon and real catalogue stars together. Moon and stars remain visible in both endpoint pairs 23/24 and 26/27; later UI/prayer content appears over that retained celestial content.

Independent metadata analysis consumed all **1,470 timestamp rows**, with strictly increasing source times and consecutive sequence identifiers, covering **15,006.410 ms** between the first and last retained source timestamps. There are exactly two source intervals over 80 ms across that complete sidecar:

| Original endpoint pair | Source interval | Endpoint observation |
| --- | ---: | --- |
| 23 → 24 | 120.217085 ms | Moon/stars visible on both sides; prayer placeholders appear |
| 26 → 27 | 178.081274 ms | Moon/stars visible on both sides; prayer arc/times/weather appear |

The first observed complete scene is frame 16. Its retained nominal receipt is **369.893 ms from navigation**, **162.700 ms after the earliest admitted head capture**. These are receipt-clock measurements, not hardware presentation timestamps. The integer receipt clock requires up to 1 ms conservative quantisation allowance; that changes no current disposition. The interval from the last neutral frame 15 to frame 16 is only **6.709 ms** in the source timestamps.

The complete sidecar SHA-256 was independently recomputed as **2de6e911b1c5c7abfded3ac15835306863dc82335e2960f8b72ca3f144a63dbe**. Its receipt-minus-source offsets range approximately −0.237 to 11.072 ms, another reason not to treat either timestamp as a monitor presentation clock. Existing annotations cover 249 frames through the first 3 seconds; they report both objects present from 16 onwards. Those remain heuristics, not independent visual classification of every original.

**The long intervals demonstrate missing observation coverage. They do not demonstrate celestial withdrawal.** Healthy endpoints also cannot prove uninterrupted presence through an unobserved interval. Both distinctions apply simultaneously.

The actual [S1 checker](https://github.com/theislampill/salah_widget/blob/feddf007e537a38972056d7d56243321884ab41f/tools/cp9/first_complete_scene.py) keeps separate requirements: sufficient early-frame coverage; scene-to-principal-content delay; navigation and accepted-scene budgets; matched-baseline regression; and continued presence. It correctly prevents PASS with uncovered intervals. Its aggregate FAIL must not be reported as a proved Moon-disappearance defect. No threshold or adjudicator was changed.

The governing reference budgets remain Chromium 1000/250/80/250 ms and Firefox 1500/400/80/400 ms for navigation, accepted-to-complete, principal-content gap and added baseline latency respectively. One observed Chromium cold/direct case does not qualify the remaining entry/browser/DPR matrix or provide a matched-baseline result.

See [SOURCE_FRAME_REVIEW.json](evidence/r0021-pro-recovery-20261018/SOURCE_FRAME_REVIEW.json) for all calculated intervals, original sequence/receipt values, source identities and the exact review boundary. Six originals were visually inspected; all 1,470 timestamp rows were analysed. No new recording was acquired, no frame was inserted or interpolated, and no all-frame pixel inspection is claimed.

## 3. Implemented bounded source correction

### Mechanism and responsible owner

At [moon/src/moon-native.mjs](https://github.com/theislampill/salah_widget/blob/feddf007e537a38972056d7d56243321884ab41f/moon/src/moon-native.mjs), surface() always calls capture(), including the .mphoto getBoundingClientRect() measurement. However, presentation() can succeed only through an accepted surface or waitingPreview.

During clear(), waitingPreview becomes null; fallback() then sets accepted=null before re-entering the native fallback hook. That hook calls updateSkySurface(), which calls surface() again. Both candidate roots are absent, so the capture/layout work is necessarily discarded before returning null. Independent review found a material qualification to the initial purity hypothesis: native capture calls skySceneIdentity()/simNow(), and simNow() can initialize or re-anchor the explicit simulation clock. That observation must remain. The final change preserves the host call and its existing exception handling, then omits only the discarded validation and footprint work.

The retained r103 CPU profile directly samples this route. Nodes 105 and 118 identify surface → updateSkySurface → fallback → clear → beginSkyScene during boot/pending paint, with **9.236 + 4.571 = 13.807 ms** of weighted sample attribution to capture. Their position ticks identify the actual generated layout-reading line.

This establishes exercised unnecessary work. It does not establish that those 13.807 ms are recoverable wall time, that all necessary layout disappears, or that this route caused either late source-frame gap. The profile window is relative to profiler start, not navigation.

### Exact correction, negative controls and preservation

In [the qualified source delta](evidence/r0021-pro-recovery-20261018/implementation.patch), capture(withGeometry=true) retains the complete default path. Only surface() supplies a false argument, and only when both accepted and waitingPreview are absent. Even then h.capture() still executes before returning null. Every candidate-present path retains its native authority, currentness, phase/footprint, DPR, profile, paused-state, adoption and texture checks.

The initially proposed direct guard before capture was rejected **before product implementation** because it could remove the lazy native clock observation. Its proposal and test-only negative result are preserved in the [qualification packet](evidence/r0021-empty-surface-20261018/QUALIFICATION.json). No scientific clock exception is needed for the conservative correction.

The three added controls require:

1. An empty read returns null, performs exactly one native capture, and performs no lunar layout read.
2. Two real runtime invalidations through the fallback hook preserve two native captures, skip both layout reads, and still adopt the original initial head exactly once.
3. A current deferred preview without an accepted predecessor can be adopted; a stale generation is rejected.

On the original source, the first two controls fail on one and two unnecessary geometry reads, while the deferred-preview control passes. After the correction all three pass. The full affected host, native lunar admission, composition and preview-host run reports **95 tests passed; zero failures, cancellations, skips or TODOs**. These are assertion and lifecycle results, not production callback-duration measurements.

Two executions of **python -B tools/build_native.py** produced byte-identical 142-entry runtime inventories. Exactly four runtime files changed: index.html, offline.html, moon/moon-host.js and moon/BUILD.json. The first three contain the same owner-generated code change; BUILD.json updates the corresponding hashes. The other 138 runtime files match r26. Separate review checked 273 protected source/data files (169,036,855 bytes) against baseline Git blobs without mismatch. Frozen V1 verification and the diff whitespace check pass.

Falsifiers remain a skipped native observation, lost initial-head/deferred-preview adoption, bypassed candidate-present fence, affected regression or protected-source drift. None appears in the inspected source or affected controls. This establishes removal of the unnecessary geometry query. **No new native timing or pixel comparison was acquired**, and no wall-time saving or S1 continuity improvement is claimed.

### Other source leads

The reviewed initial producer binds the resolved observer/current clock, physical background, same-catalogue stars and Moon join before native boot. Publication uses one CSS rule, with the original head retained through the guarded one-use handoff. This supports coherent ownership and ordering; it does not prove simultaneous browser resource decoding or monitor presentation.

No additional change to prepareNativeFirstPaint, lunar composition, H1, V5, the prayer arc/filter or the renderer is supported by this bounded review. Rejected filter, hidden-arc and compositor-layer variants remain rejected. Distinct prefix preparations serve separate ownership stages; combining them would require a larger lifetime change and is not justified here.

## 4. Callback and resource conclusions

### Preserve genuine credit without widening it

The r76 projection belongs to integrated-r20, runtime e193b433a50b42401735ca36faf44ac02d3ed7687959c48c0b66c5b9da337340. Its measurement is **synchronous exclusive elapsed time**, not a complete CPU/GPU or inclusive callback certificate.

Eleven scopes reportedly pass both first 5 s and full 15 s windows: main.applyTheme, main.atmosphere, main.commitSkyScene, main.paintClouds, main.renderLoop, moon.detailCompose, moon.poll, moon.syncTexture, preview.present, sky.animate and sky.compose. sky.accept and sky.workerMessage pass only the admitted full 15 s supplement, while their first 5 s windows remain sparse. This is the retained **13/24** credit.

The original raw r76 records, acquisition harness, ANALYSIS and independent recomputation are explicitly **local-only** in the [published projection](https://github.com/theislampill/salah_widget/blob/feddf007e537a38972056d7d56243321884ab41f/docs/real-sky/evidence/r0021-moon-request-20261018/QUALIFICATION.json). The projection itself was hash-verified; those raw private originals could not be independently recomputed in this Pro execution. Retain the historical reviewed results with that custody limit.

Relevant r20→recovered-r26 real-sky owners and moon-native.mjs are byte-identical. The earlier native HTML changes affect startup handoff, weather invalidation and arc fitting. The new bounded correction changes capture()/surface() in moon-native.mjs; its exact delta and preserved caller behavior are reviewed, but the 95 assertion tests are not a fresh quantitative callback comparison. Therefore changed startup/weather/lunar-capture paths do not automatically inherit cost acceptance, while unrelated quiescent steady credit should not be discarded wholesale.

### Decision-changing distinctions

| Item | Correct disposition |
| --- | --- |
| Historical sky.accept increase | Retain the r4 increase (~0.10/0.20→24.45/27.20ms exclusive median/p95). Current deep-night code requires the existing worker to prepare H1, avoiding that full UI pass; later r76 reports full 15 s PASS. No current regression is established from the old result alone. Twilight/day and worker cost remain separate. |
| moon.poll | Retain its matched 4 Hz, 480-per-side exclusive result (.043/.049ms medians; .077/.089ms p95). The added initialPresentation child is one-sided A0/B480 and excluded from exclusive time. An applicable inclusive parent comparison is still needed to cover that child; absence is not zero cost. |
| main.paint / main.render | Preserve their variability-based incomplete results. A .330ms paint round spread and .381ms render first-window p95 spread cannot be erased by favourable pooled values. main.render's full 15 s PASS does not make the combined result PASS. |
| Startup-only/inactive labels | No requirement was found that every instrumentation label obtain 20 warmed steady calls. Assign startup work to startup and an extra child to its applicable enclosing callback. Do not manufacture zero baselines or launch steady sampling for functions that do not run there. |
| Late accepted weather | Dirtying the existing render loop repairs a reproduced header problem and creates no new controller. Its newly exercised response needs bounded source/callback qualification; older blocked-provider steady evidence does not measure it. |
| Solar-mask retention | At most two decoded resources **plus one pending candidate**, not two total roots. Existing tests cover displayed A / rejected B / pending C, clear/dispose and late completion. That is bounded owner-reference evidence, not native decoder/Promise/GC lifetime proof. |
| Historical buffer increase | +32,387,380 known bytes is finite added footprint, not a demonstrated leak. The old 55,489,524 → 87,876,904-byte inventory excludes whole heap/native/GPU storage and is not a current-head inventory. No accepted byte ceiling was identified. |
| Firefox cost | Coarse timers, recorder-capacity failure and quarantined interference remain inconclusive measurement results. They are not product-regression findings. No renewed broad Firefox profiling campaign is warranted. |

The adopted median/p95 allowance remains **max(0.25 ms, 10% of that baseline statistic)**. No limit is changed. The canonical contract calls for separate startup/steady evidence, meaningful callback/provider/controller/allocation inventory and no new permanent controller or unbounded allocations. It does not require whole-heap or GPU proof.

The weather correction is also narrower than an instantaneous pre-boot publication guarantee: boot awaits loadPrayerData before starting the ordinary loop. A dirty flag wakes an existing loop; it does not itself create a render opportunity while the initial prayer await is unsettled. No new defect or S1 cause was established there. Overnight Countdown unavailable can correctly await tomorrow's Fajr record.

## 5. S2–S10 acceptance map

These statuses apply to the named component or evidence portion, not an invented full-row PASS.

| Requirement | Preserve now | Actually remaining |
| --- | --- | --- |
| S2 catalogue | Accepted same-catalogue bootstrap/currentness and protected sources | Current first/transition scene consumption, including applicable delayed pack and cloud/rain visibility |
| S3 initial V5 Moon | Bounded receiver/material/source custody | Native first appearance and obvious-swap rejection through current refinement |
| S4 transitions/opacity | Accepted independent coverage, outside-star positive and leak-mutant controls | Continuous initial→preview→admitted-refined full-scene observation |
| S5 recovery | Accepted truthful source semantics and specific held/HTTP503/retry controls | Missing body-stream, Image and decoder modes; timeout distinguished from a hold finishing before deadline; current full recovery observation |
| S6 currentness | Accepted target/generation/clock/profile/phase fences; no new bypass found | Exact-source transfer of affected consumers, keeping source-only and actual native controls distinct |
| S7 entries/parent | Actual Firefox parent access and reviewed refined endpoints; retained ordinary entry cases | Remaining current entry/DPR/valid-date/continuous predicates and the specific failed Firefox refinement case |
| S8 build/data | Two archived-candidate deterministic builds, exact 142-entry runtime identity, all 138 unaffected runtime entries, 273 protected source/data files and frozen V1 check | Apply/publish the exact candidate from its bundle, bind the resulting remote commit and preserve these receipts; native platform/appearance obligations remain separate |
| S9 delivery | Transparent non-closing handoff and preserved failures | Final independent qualification, owner exact-head/base approval and actual production/certificate-first sequence |
| S10 joined H1 | Delivered R0022 H1 .003/.020 owner selection and scoped full-composition handoff | Current startup-stage consumption of that accepted composition; no new H1 selection or R0022 replay |

**Numerical provenance correction:** the old uncompressed 40-case RMS 0.385564/255 belongs to its original receiver. Current compact evidence reports **RMS 2.410503/255, p95=4 and equal paired coverage**, within the unchanged 4/255 and 12/255 limits. Source association and output-preserving row/digest changes do not turn either surface comparison into native continuous appearance proof. See [the preserved execution account](https://github.com/theislampill/salah_widget/blob/feddf007e537a38972056d7d56243321884ab41f/docs/real-sky/R0021_STARTUP_EXECUTION.md).

The separate visual reviewer viewed and hash-verified the four actual Firefox parent originals at r17 (source 7fd98e31d5cd6df9c7193e054048314947675384, Firefox 150.0.2, signed TablissNG 1.8.1). The six-row card, footer, Moon/stars, current prayer/countdown and real contrast/glass/reload route are visible. The captures are soft and do not certify sharpness, timing or continuity. **The parent-access blocker is retired; full parent qualification is not.**

The same reviewer inspected the Firefox frozen-weather before/after and actual settings images. These support the specific accepted-header and weather-preserving mode-switch correction. They are not settled contrast, rain, motion or asset-recovery evidence. Earlier parent unavailable-weather endpoints do not prove that switching caused later recovery.

The retained Firefox failure is **integrated-r3, clear iframe, DPR 2, new tab, 131.468 s**, still showing a current 64-sample preview while 8192-sample work was selected, with rejection of the final quality criterion. Other successful endpoints and later publication bounds do not erase that case. Its original raw failed-case packet was not available here. It needs a source/evidence explanation applicable to that exact rejection or the specific corresponding current refinement observation, not a broad Firefox profiling programme.

Original irregular Sun flicker retains its existing disposition: not independently reproduced, potentially addressed by the verified solar-currentness correction. No extra indefinite flicker gate was added.

## 6. Minimum credible route from this checkpoint

The single supported work-removal correction is complete, tested, built and independently reviewed at its local source/build boundary. First apply/publish its exact six changed product/source/test files from the [verified archive](evidence/r0021-pro-recovery-20261018/BUNDLE.md) in an authenticated Git environment, preserving the PR's documentation checkpoint and checking for newer source. No further product intervention is justified by this evidence alone.

1. **Recover only missing decisive originals where available.** In particular the retained r76 raw/harness/admission/ANALYSIS bundle (ANALYSIS SHA-256 3e1d12ecc2f911e6fdcad7c5784fd957c78aa0b733815bcf1d303eac7129a9ef) and the named r3 Firefox quality-rejection packet. Copying existing records requires neither a new acquisition nor a Codex run. If unavailable, retain those custody limits explicitly.
2. **Resolve the genuinely native residuals on the Windows reference environment.** The current Linux environment cannot certify those timing predicates. Combine the missing continuous initial/preview/admitted-refined scene observation across S2/S3/S4/S7/S10; address the named Firefox quality rejection and only the absent failure/retry modes. Preserve the original budgets, matched-baseline requirement and bounded-repeat rule. No supported source intervention reconstructs the unobserved intervals in the existing S1 recordings.
3. **Close callback gaps at their actual lifetime.** Prefer an applicable inclusive enclosing poll comparison, the changed weather response and meaningful retained-resource inventory over forcing every startup-only label into a steady sample population. Transfer exact unchanged credit only where its assumptions hold; the current guard's assertion timings are not a callback certificate.
4. **Only then consider production.** Freeze the qualifying candidate and obtain exact final independent approval. The owner must explicitly approve that head/base before the normal merge, served-byte/deployment/behavior checks and independent certificate-first completed closure.

No broad relaxation is recommended. The source/build correction does not turn the remaining platform and observation gaps into PASS.

### Smallest prospective owner exception

If Firefox's submillisecond callback comparison remains technically unobtainable, the narrow decision to present is:

> Permit the final shared-code quantitative callback argument to use the applicable Chromium evidence, while recording Firefox quantitative callback cost as unverified. Retain the separate Firefox functional, lifecycle, visual, refinement, parent and all S1 timing/continuity requirements. Keep the Chromium tolerance and all other acceptance criteria unchanged.

**This is a proposed decision, not an exception granted by this review.** Even granting it would not discharge S1, the named Firefox refinement rejection, missing recovery evidence or production approval. A general Firefox waiver or merely increasing 80 ms would not be equivalent.

## 7. Execution and capability record

The initial command service disconnected after source/evidence inspection. That earlier Node host baseline eventually returned exit 0, but its detailed log was lost with the temporary environment and was not promoted to a counted qualification result. No product source was changed during that outage, and no substitute workflow or new coordinator was created.

A later host capability update supplied a working command service with a fresh filesystem. The same PR branch was restored into a disposable checkout; its clean HEAD/tree and original runtime were reverified against feddf007. The exact test-only negative controls, bounded owner correction, 95 affected tests, two canonical builds, V1 preservation and source/build review described above were then completed. The final [qualification packet](evidence/r0021-empty-surface-20261018/QUALIFICATION.json) records the actual commands, environment, hashes and unedited assertion content with temporary checkout prefixes and whitespace-only TAP lines normalized as declared.

The installed Windows reference environment was unavailable throughout. No new native browser acquisition, principal timing run, Firefox profiler campaign or pixel comparison was performed. No personal browser, profile, desktop, credentials or clipboard was used. Codex was not invoked.

The initial skill controller lookup found no controller in the isolated clone. No controller was guessed or created; continuation used the owner's explicit existing-PR authority and verified live source identity. No replacement work order, release claim or lifecycle certificate was created.

The complete implementation archive and evidence are preserved on the existing PR branch. Its runnable files remain r26 until the archived source/build change is applied and pushed. Every production effect remains conditional on later qualification and the owner's explicit approval of the exact head and base.

