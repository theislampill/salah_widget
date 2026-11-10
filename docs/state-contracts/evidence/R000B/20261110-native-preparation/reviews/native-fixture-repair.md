# R000B native observation and oracle repair

**Report state: FINAL — bounded HN1–HN4 implementation and pure verification complete; repaired harness write-frozen. Independent v2 closure review and hosted acquisition remain pending. No native result or product PASS is claimed.**

## Scope and authority

This report records the ordinary implementation repair requested by root after the independent frozen-v1 review. The reviewed findings were read in full from `/workspace/scratch/15b8fb6ac4c2/reviews/native-harness-review.md`, SHA-256 `3416fa2eb2ea30969ea23992a7b13dd19ba414282c9c2bd1ea116d3897a0c60c`. Root retains qualification, acquisition, acceptance, integration and closure authority. This report does not close those findings on behalf of the independent reviewer.

Repository writes were limited to the two reopened harness files and the new focused oracle test. Each edit to an existing repository file used the installed mutation-window wrapper and a previously prepared scratch script. The repair report and bounded evidence are separate scratch artifacts. No product, Moon, generator, shared helper, generated build, ref or external resource was changed by this lane. No browser, listener or worker was acquired; no product script body was executed. All commands completed; this lane leaves no running process.

## Frozen repair identities

Paths in this table are relative to `/workspace/scratch/15b8fb6ac4c2/r000b-work`.

| File | Final SHA-256 | Bytes |
|---|---|---:|
| `tests/rlgwo/r000b-no-timetable-fixture.html` | `5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c` | 34,196 |
| `tools/qa/run_r000b_withdrawal.py` | `73afb4d772e32bd21f2697777914f3db8d2d28c3833271ef669037b079fb28bc` | 65,525 |
| `tests/weather-no-timetable-native-oracles.test.py` | `3d60eec118064858d2294955a690a80d88dcb5021376e5362b5f2f6be44f0f82` | 16,694 |

**These three files are write-frozen.** No further edit is proposed in this lane. `final-identities.json` records these values, the observed product/build checkpoint and the bounded execution scope. The original `native-fixture.md` remains the historical v1 author report; this repair report supersedes its observation/oracle claims addressed by HN1–HN4.

## Repairs and evidence

### HN1 — remove effectful lunar observation and bound error claims

The bridge no longer references `SalahMoonRuntime`. In particular, it does not read `.state`, whose getter can call presentation/adoption/texture synchronization and publish a lunar surface. No replacement Moon state getter was added. Evidence remains the actual DOM `.mphoto` href presence and bounds, `.moon` bounds/opacity, `.moon-ready`, existing `moonSky` geometry, `_skyMoonPresence`, and actual captured foreground bytes. The bridge does not call a render, acquisition, admission, reconciliation, currentness, cloud painter or lunar producer helper.

Error reporting is now expressly limited to observed channels. `observed_sky_error_fields()` records whether refined `errors` and preview `catalogueError` were actually published. A missing field is `observed: false`, `value: null`, with coverage `not-published/uninspected`; it is not an empty error list. The corresponding check is `noErrorsInObservedSkyDiagnosticFields` and requires at least one observed field. Browser/fixture/teardown handling is separately named `noErrorsInObservedBrowserFixtureAndTeardownChannels`.

**Handled Moon worker diagnostic errors remain uninspected.** This limitation is in each snapshot's diagnostic read limit and the driver receipt's `uninspectedDiagnostics`. The static pure tests verify the prohibited runtime reference and helper calls are absent from the bridge, and verify that missing error fields are not reported as observed empty errors.

### HN2 — signed phase and bounded lifecycle continuity

The bridge passively retains the actual native integration timestamp, fixed wind values, population/key/field seed, phase, life and wander. The driver checks all retained full snapshots, the passive trace after the initial healthy snapshot, and post-dispatch visibility boundary samples. These are sorted by actual observation elapsed time.

`cloud_motion_continuity()` uses the declared 225° wind and 2 m/s speed, verifies that the consumed wind matches, and checks decreasing signed circular phase modulo 1.25. Phase rates per second are approximately `[0.002149604615, 0.002687005769, 0.003224406922]`. Forward life rates are `[0.018, 0.022, 0.026]` and wander rate is `0.011`, with their native modulo `2^32` wrap. Bounds use actual native integration elapsed time; there is no unsigned 0.03 floor. Numerical allowances are `1e-9` for phase and `1e-5` for life/wander. Identity changes, missing/nonfinite axes, changed wind, changed reduced state, or backwards native integration time fail.

Reduced motion and pairs of paused observations require exact holds of all accumulated axes. Declared hidden intervals are obtained from passive native values immediately after the product's own visibility listeners; those intervals are removed from elapsed bounds so a hidden backlog cannot be accepted. The first resumed sample uses this same predicate. This is a bounded continuity predicate; positive recovered motion and the original 30-second clip remain separate controls.

The exact review reset after 8.9 seconds is preserved. Its old unsigned phase deltas are `[0.019131481071783307, 0.02391435133972908, 0.02869722160767485]`, all below the old 0.03 floor. The repaired predicate rejects all three positive/backwards phase steps, plus the life/wander resets. A separate unchanged-phase/reset-life-or-wander control is also rejected. Healthy signed wrap, native noise wrap, reduced holds, hidden holds and an ordinary visible resume are accepted by the pure controls; hidden backlog and hidden drift are rejected.

### HN3 — independent actual-pixel support and measured rain geometry

The repaired rain predicate no longer takes `_colDens` or normalized density as authority for origin support. Those values remain diagnostic material and existing broad healthy controls. The evidence joins independently decoded native cloud PNG bytes and the independently decoded **published inverse cloud mask** to measured untransformed particle geometry and actual parent/cloud/foreground bounds.

The predicate deliberately implements the accepted **visible source column and declared CSS base origin** contract. It does not introduce an exact cloud-contour requirement at the invisible start of the fall animation. The base must be at the declared 19% of the measured offset parent's client height, and its resolved horizontal percentage and pixel position must agree. Parent borders/client dimensions, actual cloud and foreground registration, and the measured base rectangle participate. The presently visible segment is retained separately as the base plus its current 2D translation. For `fall`, translation must follow `(0,-10px)` to `(rainSlant,132px)`; reduced/no-animation geometry must hold at the base. Rotation, scale, unrecognized animation/slant, missing geometry and displacement fail.

The geometric tolerance is 0.75 CSS px. Published-mask support uses the actual assigned source-column footprint with only half an output pixel for coordinate quantization. The published mask already contains native scaling, blur and vertical masking, so it is **not blurred again** or given another blur halo. The independent raw-cloud association allowance is three times the declared 0.55 px blur plus half a native backing pixel, in addition to the measured particle footprint. For the measured 323 px inner width / 144 px cloud backing, this allowance is about 2.77153 CSS px; the published 325 px mask coordinate allowance is about 0.496923 CSS px. Support means strictly positive alpha bytes; no density-derived threshold substitutes for them.

Both required negative controls retain the old healthy/global and old density-origin passes while the new predicate rejects them: (1) a `0px` base origin instead of 19%; (2) nonzero cloud pixels only in distant column 30 while the assigned source column is 5. A masked-out column also fails. Healthy slanted and reduced controls pass. A control expressly permits same-column support elsewhere within the published masked deck, so invisible animation-start contour coincidence is not accidentally added as a requirement.

**This is not a claim that a native rain scene has passed.** The first visibly nonzero animated segment can differ from the CSS base because the keyframe begins at zero opacity. Actual compositor appearance, visible cloud/rain connection, slant and clipping still require the retained PNGs, card crop and original video. Any native contradiction must remain evidence and a failure where the frozen predicate applies; the tolerance is not to be loosened to fit it.

### HN4 — retain visible pending resume frames before ready recovery

The fixture now detects actual foreground display from computed display/visibility/opacity and nonzero dimensions, independent of the diagnostic `ready` label. At the first post-event rAF it takes a full snapshot; at every subsequent observed rAF opportunity with a displayed preview or refined canvas it retains a full snapshot. `visibleForegrounds` records every such layer. The first visible snapshot is selected by display, while `resumeReady` is a separate endpoint. The observer is bounded by 120 callbacks or 5 seconds and fails if ready recovery is not reached; failures preserve retained observations.

The driver writes each retained snapshot and media to a numbered `resume-opportunity-NNN` artifact. First-rAF checks include joined material whenever displayed. `all_visible_joins_empty()` checks every visible layer's actual captured cloud alpha diagnostics, immutable cloud receipt and published-mask alpha without filtering on diagnostic readiness. `resume_visible_sequence()` checks every retained first/visible opportunity before the separate ready endpoint. A later clean ready frame cannot erase an earlier stale pending frame.

The exact stale-visible-pending/clean-ready counterexample retains the old first native guard pass, old omission of the first frame, and old later-ready pass. The repaired first-visible join and sequence both fail. An intervening stale pending frame also fails; clean pending followed by clean ready and a first callback with no displayed foreground followed by clean recovery pass.

The visibility seam remains the declared document-property/event simulation. It is not OS sleep/wake evidence. The fixture's bounded read-only rAF observation is not a new product loop; DOM/canvas reads can consume native time and do not stop or advance the product clock.

## Verification, commands and retained evidence

The focused pure suite finished **20/20, exit 0**. It extracts selected `FunctionDef` AST nodes from the actual repaired driver into memory. It does not import or run driver `main()`, execute a product body, launch a browser, open a listener or install a runtime. Its frozen-v1 predicates preserve the review counterexamples; a second check also extracted the actual archived v1 driver (verified SHA `6f0669ced88030c2dd3b9db40520cf1b5aa68669e019cfc3623b0952494f0e7f`) and reproduced the old-pass/new-fail observations against the final driver hash.

All evidence below is under `/workspace/scratch/15b8fb6ac4c2/evidence/native-harness-repair/`. `evidence-index.json` binds retained artifact hashes and the final report. Earlier intermediate logs remain explicitly retained; `*-final` files and `final-identities.json` are the final-byte evidence.

| Check | Exit / result | Retained artifact |
|---|---|---|
| Focused pure test suite on final bytes | 0; 20/20 | `native-oracles-final.log` |
| Archived-v1/new final-byte counterexamples | 0; HN2 reset, both HN3 controls and HN4 stale pending rejected | `old-new-counterexamples-final.json` |
| Final Python AST / whitespace and ten unchanged helper AST comparisons | 0 | `final-static-checks.log` |
| Final fixture JavaScript `vm.Script` compile | 0; one wrapper script; zero execution | `final-fixture-syntax.log` |
| Scoped `git diff --check` | 0; no output | `final-diff-check.log` |
| Final harness/product/build identity observation | All three harness hashes fixed; observed four generated pins match build 1 | `final-identities.json` |

Exact final test and fixture syntax invocations, from the worktree:

```bash
PYTHONDONTWRITEBYTECODE=1 python tests/weather-no-timetable-native-oracles.test.py -v > /workspace/scratch/15b8fb6ac4c2/evidence/native-harness-repair/native-oracles-final.log 2>&1
node -e 'const fs=require("fs"),vm=require("vm");const text=fs.readFileSync(process.argv[1],"utf8");const bodies=[...text.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)].map(m=>m[1]);if(bodies.length!==1)throw Error("Expected one wrapper script");bodies.forEach((body,i)=>new vm.Script(body,{filename:process.argv[1]+":"+i}));console.log("Final fixture JavaScript syntax: OK (1 wrapper script compiled; zero execution)");' tests/rlgwo/r000b-no-timetable-fixture.html > /workspace/scratch/15b8fb6ac4c2/evidence/native-harness-repair/final-fixture-syntax.log 2>&1
git diff --check -- tests/rlgwo/r000b-no-timetable-fixture.html tools/qa/run_r000b_withdrawal.py tests/weather-no-timetable-native-oracles.test.py > /workspace/scratch/15b8fb6ac4c2/evidence/native-harness-repair/final-diff-check.log 2>&1
```

The AST/archived-v1 proof was an in-memory `PYTHONDONTWRITEBYTECODE=1 python -` invocation, exit 0, with retained result JSON and stdout; it did not execute module imports/main or mutate source. The portable 20-test source is retained as the third frozen repository file. The final archived-v1 result SHA is `b5505edc3e223e49d4fc3943ba88e80d894013436a19ecb876941f6544ebc479`.

### Four governed mutation windows

Every window returned command exit 0 and an `anchor=absent-to-present` receipt at unchanged head `9dabdcf338a7307c0256dcdccac48326b357f0d5`. Prepared scripts are copied into the repair evidence directory. Existing-file edits were not made through stdin.

```bash
bash /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/check-evidence-anchor.sh --mutation-window tests/rlgwo/r000b-no-timetable-fixture.html --expect 'anchor:R000B_HN1_HN4_READ_ONLY_OBSERVER_V2' -- python /workspace/scratch/15b8fb6ac4c2/repair_native_fixture_hn.py
bash /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/check-evidence-anchor.sh --mutation-window tools/qa/run_r000b_withdrawal.py --expect 'anchor:R000B_HN2_HN3_HN4_NATIVE_ORACLES_V2' -- python /workspace/scratch/15b8fb6ac4c2/repair_native_driver_hn.py
bash /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/check-evidence-anchor.sh --mutation-window tests/rlgwo/r000b-no-timetable-fixture.html --expect 'anchor:R000B_HN_GEOMETRY_CONSTRUCTOR_V2_1' -- python /workspace/scratch/15b8fb6ac4c2/finalize_native_harness_hn.py fixture
bash /home/agent/.codex/skills/remote-skills/skill-6a85962852788191bb717a1a61592b58/scripts/check-evidence-anchor.sh --mutation-window tools/qa/run_r000b_withdrawal.py --expect 'anchor:R000B_HN_ERROR_CHANNELS_V2_1' -- python /workspace/scratch/15b8fb6ac4c2/finalize_native_harness_hn.py driver
```

| Receipt log | Before SHA-256 | After SHA-256 |
|---|---|---|
| `fixture-mutation-window.log` | `77f5221280705cf9f4a9de760007a6b49ac25c12b8f53412c23661af32b3be09` | `d142fcf74612e82003a365d84d7316773f008a74a72f5da82b056b9dac50edef` |
| `driver-mutation-window.log` | `6f0669ced88030c2dd3b9db40520cf1b5aa68669e019cfc3623b0952494f0e7f` | `82b65b459dd1122fd13a8d204c16192b88cde740541f1e540a29bfd40bfc5144` |
| `fixture-final-mutation-window.log` | `d142fcf74612e82003a365d84d7316773f008a74a72f5da82b056b9dac50edef` | `5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c` |
| `driver-final-mutation-window.log` | `82b65b459dd1122fd13a8d204c16192b88cde740541f1e540a29bfd40bfc5144` | `73afb4d772e32bd21f2697777914f3db8d2d28c3833271ef669037b079fb28bc` |

## Preserved campaign boundaries

The repair leaves the independent expected-manifest gate, separate product/fixture roots, per-file runtime serving pins, before/after source identities, exact six generated script-body verification, private storage and provider interception intact. The initial Riyadh 2026-09-08 23:59:50 offset still advances with native elapsed 1×; no clock seek, forced owner call or artificial midnight tick was added. Ten existing codec, identity and material predicates were AST-compared against v1 and remained identical: `png_rgba`, `png_summary`, `decode_png_url`, `script_identities`, `actual_empty`, `joined_empty`, `healthy_cloud`, `unknown_weather`, `effects_off`, `independent_celestial`.

The driver still requires an independently supplied `r000b-native-expected/v1` manifest. It does not approve its own inputs. Root must pin the reviewed `authoredSources` and `fixtureSources` inventories as well as the mandatory runtime tree/index/script identities; optional inventories are not inferred as approved when absent. Root will generate new native manifests only after its final source/build and this harness are frozen.

The initial healthy scene, naturally elapsed 901-second source expiry with actual null prayer model, replacement weather before prayer recovery, ordinary retry recovery, and recovered 30-second default/reduced/full watch remain the intended hosted campaign. The exact inclusive 900,000 ms/midnight overlap can remain `NOT_NATURALLY_REACHED`. The card remains 325×530 with six rows and footer. Screenshots, card crops, original video, native cloud/foreground PNGs, mask bytes, consumed diagnostics and request/identity records remain retained.

Successful candidate numeric execution still reports only `PASS_ASSERTIONS_PENDING_PIXEL_REVIEW`. A baseline demonstration has the separate `BASELINE_DEFECT_DEMONSTRATED_PENDING_PIXEL_REVIEW` status and cannot produce a product success label. Neither status has been produced by a native run in this lane.

### F01 coverage limit: healthy full-model weather replacement is not required

The frozen driver requires a fresh weather record **before** prayer recovery, while `modelIsNull` is true. It then waits for recovery, takes the `recovered` snapshot, watches for 30 seconds and takes `recovered-30s`. It does not wait for or assert another weather record after the genuine prayer model is available. With recovery around 130 seconds and an ordinary weather request cadence around 60–90 seconds, the watch can finish before the next such record; these timings are scheduler expectations, not an executed trace.

The retained passive trace records `modelIsNull`, `candidate.sourceValidAt`, the consumed receipt and motion, and the request ledger records weather attempts/consumption. If a record transition happens incidentally during the recovered interval, those artifacts can establish the recorded transition and sampled continuity. The current campaign does **not guarantee** that this event occurs and does not require paired full cloud/foreground captures at that healthy replacement. Therefore its passing assertions cannot be cited as native qualification of the F01 healthy-refresh capture-before-render continuity case. Root may separately authorize a narrow observation of the next ordinary weather record after recovery within the existing 240-second budget, without a forced producer or capture ordering. No such extension was made to these frozen harness bytes.

## Observed product checkpoint and remaining dependencies

At `2026-11-10T02:39:09.691451+00:00`, `final-identities.json` recorded the five product owner hashes and the four generated artifacts. The generated files in the worktree and build-1 checkout matched the prior `build-receipt-complete.json` pins:

| Generated artifact | Observed SHA-256 |
|---|---|
| `index.html` | `d865b246f2a53d5d7a5b1bd958bf7cf5d858a7b2cc5c237f13f4fe9ea8408f99` |
| `offline.html` | `c3ce5d1097a396c35aef0b09a5614bfe937bf8041571f186419a1b7ffc0d7980` |
| `real-sky/native-sky.js` | `426754834c6c116c4521ad5067bb1e37a9845830fc07ebbb62dd22fcdc757d66` |
| `moon/BUILD.json` | `c2cec8e2b0f57f7a86f59a8bba0c7f59e3cbb7ecdbd749d1d3dae3386a613bd6` |

These are observations of the then-current checkpoint, not a qualification of root's separately diagnosed F01 healthy-refresh capture-before-render continuity repair or a future regenerated build. Product test counts and build successes supplied by other lanes were not rerun here and are not adopted as native proof.

The next root-owned step is an independent review of these exact repaired bytes. After that and the final product/build freeze, root owns reviewed manifests and isolated hosted acquisition. Native geometry/alpha agreement, first-visible behavior, actual motion, ordinary recovery, browser errors and the original clip remain unexecuted here. Handled Moon worker diagnostics are expressly uninspected. Controlled visibility is not OS sleep/wake. Pure counterexample success establishes that the identified predicates no longer accept those counterexamples; it does not establish a complete native campaign, pixel PASS, product readiness or issue closure.
