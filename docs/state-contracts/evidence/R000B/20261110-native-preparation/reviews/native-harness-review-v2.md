# R000B native harness repaired candidate review

**Report state: FINAL — PASS for bounded HN1–HN4 harness preparation only.**

This is root's ordinary bounded informational HN1–HN4 repair review. Root retains acceptance and mutation authority. The v1 report remains preserved as FINAL GAP; this report assesses only the repaired bytes below. The separate F01 product regression/repair at checkpoint `9dabdcf` is outside this verdict. No source PASS, native PASS, pixel acceptance, integration or issue closure is claimed.

## Exact repaired identities checked at entry

| File under `r000b-work` | SHA-256 |
|---|---|
| `tests/rlgwo/r000b-no-timetable-fixture.html` | `5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c` |
| `tools/qa/run_r000b_withdrawal.py` | `73afb4d772e32bd21f2697777914f3db8d2d28c3833271ef669037b079fb28bc` |
| `tests/weather-no-timetable-native-oracles.test.py` | `3d60eec118064858d2294955a690a80d88dcb5021376e5362b5f2f6be44f0f82` |

All three matched the supplied write freeze. The complete actual fixture/driver diffs against `evidence/native-harness-v1` were inspected, as was the complete new pure test source. The retained v1 driver hash was independently checked against `6f0669ced88030c2dd3b9db40520cf1b5aa68669e019cfc3623b0952494f0e7f`.

## Per-finding disposition

| Finding | Actual repair / checked location | Final bounded disposition |
|---|---|---|
| **HN1 — PASS** | Fixture 115–264 no longer reads any Moon runtime state/surface/presentation API. Moon evidence is direct DOM/geometry plus foreground pixels (194–219). Remaining preview/refined state getters were re-read and remain passive. Driver 362–372 and 884–889 records observed error-field presence and expressly lists uninspected handled Moon worker diagnostics. | Original effectful path removed; no replacement producer path found. Pure absence/error-coverage controls passed. Missing diagnostics are labelled unobserved rather than treated as empty error lists. |
| **HN2 — PASS** | Driver 401–483 checks signed phase, forward bounded life/wander, actual native integration timestamps, fixed velocity, identity and reduced state. Hidden intervals use direct post-dispatch motion values (fixture 317–322). Driver 892–898 combines retained snapshots, passive trace and visibility receipts. | Original 8.9-second reset and independent life/wander resets retain actual-v1 passes and are rejected by repaired predicates. Healthy default/full movement, wraps, reduced holds and hidden/resume controls pass. Hidden drift/backlog fails. |
| **HN3 — PASS** | Driver 139–176 decodes actual saved native/mask PNG bytes; 243–355 joins support to measured CSS base/parent/cloud/foreground geometry and fall translation. Fixture 167–181 captures the untransformed origin separately from the visible segment. | Density is no longer the origin oracle. Wrong base, distant-only pixels and masked-out pixels fail; healthy slanted/reduced and same-column/no-exact-contour controls pass. The declared geometric/pixel allowances remain bounded. Actual native pixel/DOM agreement is still unexecuted. |
| **HN4 — PASS** | Fixture 239–264 records the first rAF and every actually displayed foreground opportunity before a separate ready endpoint. Driver 375–398 checks all visible layers without status filtering; 760–784 retains numbered artifacts and validates the whole observed prefix. | Original pending-stale/later-ready counterexample and an intervening stale frame fail; clean pending/recovery and initially absent foreground controls pass. The first actual visible opportunity can no longer be skipped merely because its diagnostic status is pending. |

## Verification retained

`python -B tests/weather-no-timetable-native-oracles.test.py -v` completed **20 tests, exit 0**. It extracts real driver function AST nodes without importing/running `main()` or product bodies. Python AST syntax and the single fixture script's `node --check` passed. The test log and syntax record are under `evidence/native-harness-review-v2/`.

Ten pre-existing codec/material/identity predicates were independently AST-compared with the actual retained v1 file and are unchanged: `png_rgba`, `png_summary`, `decode_png_url`, `script_identities`, `actual_empty`, `joined_empty`, `healthy_cloud`, `unknown_weather`, `effects_off`, `independent_celestial`.

The reviewer has not used a browser/listener, executed a product producer, installed dependencies, built, fetched providers, touched refs/remotes or changed product/harness code. Writes are limited to this report and the designated bounded evidence directory. The author repair report was read only after direct source inspection and the independent suite run; it is evidence about the author's work, not authority or substitute verification.

## Independent archived-v1/new controls

The reviewer additionally wrote and ran `evidence/native-harness-review-v2/independent-probes.py`. It verifies both driver hashes before extraction. It extracts the actual old/new `FunctionDef` nodes and, for motion population/bounded-step and resume checks, the exact assignment expressions from each driver's `main()` AST. It does **not** execute `main()`, imports from either driver, or product code. This avoids relying solely on copied old predicates or a mock that restates the repaired implementation.

**Fourteen bounded controls completed with every expected outcome matched.** Exact inputs, outputs, violations and image-construction descriptors are retained in `independent-counterexamples.json`.

| Control group | Actual retained-v1 result | Repaired result |
|---|---|---|
| Exact 8.9-second phase/life/wander reset | `boundedPhaseSteps=True`; `populationAndSeedRetained=True` | Continuity rejected, including wrong signed phase direction and lifecycle/wander resets. |
| Life-only and wander-only reset while phase stays held | Both old continuity checks pass | Each reset rejected independently. |
| Healthy one-second default/full motion | Positive repaired control | Both modes accepted. |
| Base moved from declared 19% to 0 px | Old healthy material and density-origin predicates both pass | Rejected for displaced CSS base. |
| Cloud pixels only at native column 30 / published-mask column 70, assigned rain column 5 | Old healthy material and density-origin predicates both pass | Native and published pixel support both rejected. |
| Healthy slanted visible segment and reduced held segment | Old predicates pass | Both accepted using the actual untransformed origin. |
| Published support moved several pixels away while native backing remains associated | Old predicates pass | Rejected; no extra blur halo is applied to the already-blurred published mask. |
| Declared geometric allowance boundary | Old predicates pass regardless | A 0.76 CSS-px base displacement is rejected; 0.74 CSS px is permitted by the explicit 0.75 bound. This records the allowance rather than concealing it. |
| First visibly stale pending frame, followed by clean ready frame | Actual old first-native check and later-ready check both pass | Actual new first-native-and-displayed check and whole-prefix check both fail. |
| Clean pending, then stale pending, then clean ready | The old stopping/filter design does not qualify the prefix | Repaired whole-prefix check rejects the intervening stale frame. |
| Clean pending followed by clean ready | Positive repaired control | Accepted. |

The focused 20-test suite also covers exact reduced holds, drift rejection, phase/noise wraps, a full hidden interval with an ordinary resume, hidden backlog rejection, masked-out native pixels, incorrect slant/nontranslation transforms, a first callback with no visible foreground, and the deliberate absence of an exact invisible-start contour requirement. These remain pure proof of the predicates and static observer ordering, not native execution results.

## Why the repaired observations support the bounded claims

### HN1: observation is passive and its error coverage is honest

The effectful Moon runtime getter is absent rather than hidden behind another accessor. Direct `.mphoto` href presence/bounds, `.moon` opacity/bounds, existing geometry/presence fields and captured canvas bytes do not invoke lunar adoption. The remaining `realSkyState` path copies status and reads the lifecycle's passive state getter; the preview getter clones status. Their file hashes remain identical to the v1-inspected interfaces. No new call to a renderer, acquisition, atmosphere, cloud reconciliation/currentness, foreground capture or lunar producer was introduced in the diff.

Handled Moon worker errors remain explicitly uninspected. The new error field records distinguish missing/unpublished diagnostics from observed empty arrays and keep browser/fixture/teardown errors as a separate channel. A no-error assertion for observed channels is not being presented as exhaustive renderer error coverage.

### HN2: continuity is checked through withdrawal, not inferred from recovery

Signed phase deltas now reject the original small backwards reset that unsigned circular distance admitted. The independent life/wander controls mean leaving phase unchanged cannot hide reset of the other accumulated axes. Identity, wind, reduced-mode state and monotonic integration timestamps must also be observed and consistent. Every retained full snapshot, relevant passive sample and visibility boundary joins the ordered continuity input.

Hidden boundaries are taken after the product's own visibility listeners through direct field reads. Hidden elapsed intervals are subtracted before forward-motion bounds are computed. Pairs of paused observations and reduced-motion samples require exact axis holds. Numerical allowances are limited to `1e-9` for phase and `1e-5` for large modulo life/wander values; the old visual-size 0.03 floor is gone. The predicate is a direction/upper-bound continuity test, not a claim of perceptible motion. The real recovered watch and pixel review remain separate positive-motion requirements.

### HN3: actual column support is independent of the density gate

`retain_media` decodes the captured native PNG and the actual published inverse-alpha PNG before calling the origin oracle. The existing PNG decoder is unchanged from v1. The native `nativeSolarTransmission` interface was checked: published alpha is exactly `255 - cloud alpha`, so inverse-alpha readback is the correct support quantity. The raw painter is hidden by the native compositor CSS; its bytes are an association witness, while the published masked cloud column is the primary display support witness.

The origin is reconstructed from the measured offset parent, client border/dimensions and resolved CSS position. The visible rectangle must match the base plus the actual translation. Its fall displacement is checked against the declared `(-10px)` to `132px` vertical path and the captured horizontal slant; reduced/no-animation mode must be held at the base. The inspected source CSS supplies `top:19%`, the declared 0.55 px blur and that fall path. The actual native stylesheet aligns foreground layers with the card and hides the obsolete preview via `display:none` when the refined owner is composed.

The tolerances are explicit and finite: 0.75 CSS px for layout registration, half an output pixel for published-column coordinate quantization, and three times the declared blur plus half a backing pixel for raw-cloud association. For the supplied 323 px inner width, these pixel allowances are approximately 0.496923 px and 2.771528 px respectively. The already-blurred published mask receives no second blur allowance. The independent probes confirm that a larger geometric displacement or distant-only mask support is rejected. No tolerance was altered during this review.

The accepted condition is visible column support and the declared base origin. Alpha may lie elsewhere in that same already-masked column. The repair does not invent a cloud contour at the animation's opacity-zero starting instant. The predicate can admit a subpixel difference within its declared geometric allowance, and any positive alpha byte supplies support; it does not certify the perceptual strength of the visual connection. That remains the purpose of native screenshots and video.

### HN4: readiness cannot erase visible stale history

The observer checks computed display, visibility, opacity and dimensions before inspecting readiness. It records the first rAF even if no foreground is displayed and every later displayed foreground opportunity until the separately declared ready endpoint. The driver's numbered artifacts retain the observed prefix. Every visible layer must have clear published mask bytes, zero captured cloud-alpha diagnostics and the matching withdrawn publication receipt, regardless of its status label. The first-rAF guard now includes the displayed join. The actual-v1/new AST controls demonstrate that the original pending-stale/later-ready escape is rejected.

This remains a bounded read-only rAF observer, with native elapsed time continuing during DOM/canvas reads. It is not an OS sleep/wake experiment or a claim about an unobserved monitor presentation between callbacks. Browser execution must still establish that the captured opportunities and actual composed pixels agree.

## Preserved campaign boundaries and residuals

The inspected diffs retain the six generated bodies, initial offset/native 1× clock, private storage, synthetic provider interception, independent expected-manifest gate, request ownership/spacing controls, ordinary missing-prayer/replacement/recovery sequence, original video retention and separate baseline-defect status. Ten existing material/codec/identity predicates were confirmed unchanged. There is no self-generated source approval manifest or new product-control seam.

The actual hosted expected manifest is outside this review and remains root-owned. Its reviewed source/harness/helper inventories need to be pinned as previously identified; optional absent inventories are not an independent approval of those bytes. Handled Moon worker diagnostics remain uninspected. All native/browser modes, layout/geometry measurements, mask decoding on the real engine, first-visible behavior, original videos and pixel judgments remain unexecuted by this reviewer. Static and pure successes cannot replace those gates.

**F01 remains separate and open.** Root identified that the current recovered 30-second stage need not observe a full-model healthy weather replacement. That new native control is required for the separate F01 product repair. Root plans a narrow passive wait with pre/post healthy-refresh captures after this harness freeze. This review neither qualifies F01 nor claims that the existing 30-second stage supplies that evidence. Such a later driver delta needs its own bounded review, without implying failure of the unchanged HN1–HN4 repairs.

## Actual read set

| Source | Actual inspection in this v2 review |
|---|---|
| Three repaired files in the identity table | Complete fixture/driver unified diffs against retained v1, direct new/changed source regions, whole-file AST parsing, complete new test source; hashes at entry and final closure. Unchanged fixture/driver regions retain the prior v1 inspection through the exact diffs. |
| Archived v1 fixture and driver under `evidence/native-harness-v1` | Actual bytes for complete diffs; independently checked original hashes; selected actual driver function/check-expression ASTs executed only in pure controls. |
| `reviews/native-harness-review.md` | Preserved original review context and final hash verification; unchanged at `3416fa2eb2ea30969ea23992a7b13dd19ba414282c9c2bd1ea116d3897a0c60c`. |
| `reviews/native-fixture-repair.md` | Full author report, read after source inspection and independent suite run; treated only as evidence. Observed SHA-256 `15bbf6af8e5e787cd75023dda53e8f1ce28039d53770c9beaaaf224a8ab86b79`. Other author evidence files were not used as verification. |
| `real-sky/native-host.mjs` | Getter/visibility section 235–243, plus filename discovery; unchanged hash checked. |
| `real-sky/native-preview-host.mjs` | Getter section 172–178; unchanged hash checked. |
| `real-sky/native-lifecycle.mjs` | Passive state getter section 32–39; unchanged hash checked. |
| `real-sky/native-composition.mjs` | Inverse-alpha interface 14–31 and mask/capture symbol searches; unchanged hash checked. |
| `real-sky/native-sky.css` | Complete 16-line stylesheet: actual foreground display and raw-cloud suppression. |
| `src/native/index.html` | Targeted card/rain/blur/reduced-motion CSS searches and card geometry lines 17–36; existing receipt/reconciliation region 2585–2608. These interface reads do not qualify the changing F01 product candidate. |
| `moon/src/moon-native.mjs`, `moon/src/moon-detail.mjs` | Hash-only confirmation that prior inspected interfaces remain unchanged; no Moon producer/getter executed. |
| `tools/qa/run_r000c_native.py`, `tools/cp9/browser_runtime.py`, `tools/cp9/runtime_identity.py` | Hash-only confirmation of unchanged v1-inspected helper files; none imported/executed by this review. |
| `real-sky/*.mjs`, CSS discovery | Path-only search for foreground class definitions, followed by the targeted reads above; no broader implementation review. |
| This report and designated v2 evidence | Initial PARTIAL stub, own report, own probe script/logs/results/identities/diffs. No unrelated review or product-test suite was opened. |

## Final hash closure and evidence custody

At `2026-11-10T02:48:26.036041+00:00`, the three repaired hashes still matched the supplied freeze, and both retained-v1 hashes matched their original freeze. `identity-checks.json` records bytes, hashes and the supporting read-set identities. The v1 report remains unchanged. Supporting passive getter/helper files match their v1 hashes. The native stylesheet hash is `298a11d0d91a801de2e8f63b7e4997ff33d7a7423ebd0e4c8a0bbd5710f68f31`.

All reviewer evidence is under `/workspace/scratch/15b8fb6ac4c2/evidence/native-harness-review-v2/`:

- `oracle-suite.log`: independent 20-test run, exit 0.
- `syntax-check.json`: Python AST and fixture Node syntax result.
- `independent-probes.py`: reproducible pure actual-v1/new predicates and check expressions.
- `independent-counterexamples.json`: fourteen controls, exact inputs/results and expected outcomes.
- `fixture-v1-v2.diff`, `driver-v1-v2.diff`: exact reviewed deltas.
- `identity-checks.json`: repaired, retained-v1 and supporting hashes.
- `artifact-manifest.json`: final evidence-file and report hashes; provenance only, not a product approval manifest.

## Final bounded disposition

**FINAL PASS — HN1, HN2, HN3 and HN4 repairs are supported for harness preparation on the exact three hashes above.** No additional material defect was found within this closure scope. Root owns reconciliation and acceptance of this report and any later change. Native acquisition, pixels/video, handled Moon worker diagnostics, F01 source/native qualification, integration and issue closure remain outside this verdict. This reviewer changed only the designated v2 report and bounded v2 evidence.
