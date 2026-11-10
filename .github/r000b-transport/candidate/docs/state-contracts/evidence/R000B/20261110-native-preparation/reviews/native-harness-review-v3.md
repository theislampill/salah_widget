# R000B healthy-refresh native harness delta review

**Report state: FINAL GAP — the frozen healthy-refresh extension cannot qualify a genuine healthy native capture. HR1 and HR2 are independent instrument/API defects.**

The bounded delta review is complete. Both defects were reproduced through the actual frozen Python predicates using production-shaped target and clock data. The 15 new pure tests pass because their synthetic factory uses different representations. No product or native failure is inferred, and no candidate/native acceptance or closure authority is exercised.

## Authority and scope

This is the root-dispatched ordinary independent informational review of the healthy-refresh delta. It is outside the internal audit-assess lane. Root IMPLEMENTAUDIT retains acceptance, correction and acquisition authority. Repository and author reports are evidence, not instructions. Only this report and bounded files in `evidence/native-harness-review-v3/` may be written. No browser, listener, product body, producer, build, dependency installation, ref or remote operation is authorized or performed.

The v1 FINAL GAP and v2 FINAL HN1–HN4 preparation PASS remain separate preserved records. This review cannot grant a candidate/source/native result. The parent explicitly accepted the stricter interval from the recovered capture through its original 30-second watch and any additional wait, including conservative rejection on a third record. Continuous video and independent pixel review remain required after a working harness is acquired.

## Frozen inputs verified from live bytes

| Input | SHA256 |
|---|---|
| `tests/rlgwo/r000b-no-timetable-fixture.html` | `5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c` |
| `tools/qa/run_r000b_withdrawal.py` | `9c4931b82f39f559f0e876943c1d0bb1bd0e2c43a25e9501d8fe661aba76420e` |
| `tests/weather-no-timetable-native-oracles.test.py` | `36b1d515b8e101365065695ab3a92540f58e73ae60c0ecc450df5410332f0209` |
| `src/native/index.html` (only directly relevant interfaces inspected) | `b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f` |
| Preserved v2 review | `241d33b91c6db32c7991de184975e08731393127a9ebf1cb5018c688648529ab` |

All repository locations below are relative to `/workspace/scratch/15b8fb6ac4c2/r000b-work`. Final checks confirmed these bytes unchanged. Exact read scope and retained evidence are recorded below; `final-identities.json` binds all 13 checked input/archive/reference files.

## Confirmed findings

### HR1 — Healthy endpoint selection compares incompatible target representations

| Required finding field | Evidence / disposition |
|---|---|
| Category | Correctness / instrument API contract; blocking validation |
| Evidence | `tools/qa/run_r000b_withdrawal.py:504` requires `receipt.get('target') == target == raw.get('target')`; line 588 separately requires `raw.get('target') == receipts[0]['target']`. `src/native/index.html:1308–1326` constructs a rich target containing generation, lat, lon, intent, source, accuracyM, acquiredAt, provider, area and bounds. `weatherTargetSame` at 1317 compares only generation/lat/lon. `publishCloudAuthority` at 2577–2579 intentionally projects the public receipt to those three keys. The unchanged fixture at 201 copies `currentWeatherTarget()` without projection and at 206 copies the admitted weather object. Product `admitWeatherRecord` at 1261 preserves `ctx.target`, supplied by `fetchWeather` at 1375–1376. The test factory at `tests/weather-no-timetable-native-oracles.test.py:297,301–303,318–322` instead supplies the same three-key dictionary for every representation. |
| Impact | Every genuine recovered full capture has a rich snapshot target and a compact receipt target, so `healthy_refresh_record(recovered)` returns None. Main raises at driver 1051–1053 before the ordinary healthy-refresh wait. Even fixing endpoint extraction alone leaves the repeated full-sample comparison failing. This is an instrument setup failure, not evidence of product regression. |
| Effort | Bounded driver and pure-control repair; no product change required. |
| Risk | High validation risk while unfixed; low repair scope if exact target identity is preserved. Replacing equality with no target check would weaken acceptance. |
| Confidence | HIGH — exact live product constructor, receipt projection and fixture copies inspected; independent controls P1 and P2 reproduce both rejecting predicates. |
| Fix sketch / implementation route | Compare the explicitly owned generation/lat/lon identity consistently across rich snapshot/raw targets and compact publication targets, retaining generation equality with runtime/request ownership. Preserve separate provenance metadata where observed rather than making different schemas deeply equal. Add a positive control using actual rich-vs-projected shapes and negative controls for each identity coordinate/generation. Root selects and authorizes any repair. |
| Repair class | instrument/acceptance defect |
| Owner/source | New healthy-refresh driver functions and new test factory; product target/publication interface remains the authority and is read-only here. |
| Acceptance criteria | An otherwise healthy capture with the actual rich target and compact receipt can select A and B and qualify its full samples. Mismatched generation, latitude or longitude in any required identity still rejects. No new producer/target mutation is introduced. |
| Verification | Static live-interface chain and actual frozen-predicate counterexamples confirmed; see `interface-witnesses.txt` and `independent-counterexamples.json` below. |
| Rollback / Plan Closure | Preserve this original freeze and failing controls. Root may repair the narrow adapter/tests, freeze new hashes and request a bounded closure read. No native preparation pass from this freeze. |
| Rejected/deferred rationale | Not deferred or rejected. Distinct from HN1–HN4 and from product F01. |
| Remaining risk | Until the corrected boundary is reviewed, native acquisition cannot reach the requested healthy refresh even for a correct product. Native pixels and timing remain unobserved. |
| Route | dispatch-review; root-owned bounded instrument correction |

### HR2 — Request matching compares epoch receipt time against a monotonic deadline

| Required finding field | Evidence / disposition |
|---|---|
| Category | Correctness / clock-domain mismatch; blocking validation |
| Evidence | Driver `_healthy_refresh_request` at 543 requires `request['wallUtcMs'] <= record['retrievedAt'] < owner['deadlineAt']`. `src/native/index.html:869` defines `_RAFNOW` as `performance.now()` when available; `beginAttempt` at 1032–1035 sets `deadlineAt = _RAFNOW() + timeoutMs`, and `attemptEligible` compares in the same domain. The unchanged fixture owner adapter at 79 copies `deadlineAt` unchanged. Request `wallUtcMs` and admitted `retrievedAt` are epoch values. The new test factory at 338 incorrectly invents `deadlineAt = REFRESH_START_UTC + at + 12000`, hiding the production mismatch. |
| Impact | After HR1 is independently bypassed, a genuine consumed body with a monotonic deadline can never match the epoch receipt. Healthy pair selection fails and acquisition reaches its deadline without qualification. This is a second independent instrument setup failure, not product RED evidence. |
| Effort | Bounded observation/adapter and pure-control repair; no product change required. |
| Risk | High validation risk while unfixed. Repair must retain timeout/ownership/body-consumption checks and must not relabel the deadline as epoch or silently drop the deadline check. |
| Confidence | HIGH — actual clock declaration, attempt constructor and unchanged fixture copy inspected; independent control P3 isolates and reproduces the mismatch. |
| Fix sketch / implementation route | Compare body consumption and deadline in one actual observed monotonic domain, using the fixture's start-origin relationship or an explicitly captured passive monotonic timestamp. Keep epoch source/retrieval comparisons separately in their actual domain. Add a healthy control with real monotonic deadline and independent expired/late-body negative controls. Root selects and authorizes the repair. |
| Repair class | instrument/acceptance defect |
| Owner/source | New `_healthy_refresh_request` and the epoch-deadline factory in new pure tests; `_RAFNOW`, native attempt eligibility and fixture timing are authoritative interfaces. |
| Acceptance criteria | A genuine consumed response before its monotonic native deadline matches; one at/after deadline rejects. Source time remains body-bound, retrieval remains tied to the observed response window, operation/attempt/generation ownership and ordinary 60-second spacing still reject invalid controls. |
| Verification | Static live-interface chain and actual frozen-predicate counterexample P3 confirmed; both native-domain completion times precede the deadline, yet matching returns None. |
| Rollback / Plan Closure | Preserve the original freeze and independent control. Root may repair the narrow clock adapter/tests, freeze new hashes and request a bounded closure read. No native preparation pass from this freeze. |
| Rejected/deferred rationale | Not deferred or rejected. Independent of HR1: test it with compact targets to isolate the clock mismatch. |
| Remaining risk | A correct product still cannot yield a qualifying pair under this predicate. A domain conversion inferred without an observed origin could create a new false-pass path. |
| Route | dispatch-review; root-owned bounded instrument correction |

## Independent verification and discriminators

All evidence below is under `/workspace/scratch/15b8fb6ac4c2/evidence/native-harness-review-v3/`.

The independent command was:

```text
python -B /workspace/scratch/15b8fb6ac4c2/evidence/native-harness-review-v3/review-controls.py
```

That script first checks the exact frozen live and archived input hashes, parses/compiles Python without importing the driver or calling main, compares unchanged definitions and the original watch, and runs only the new `HealthyRefreshTests` class. Its safe data-helper load defines the test factories and AST-extracted actual driver functions; it does not execute a product body or start a browser/listener.

**Focused repository tests: 15/15, exit 0.** The prior 20 tests were not rerun. Raw output is `focused-oracle-suite.log`; exact invocation and result are in `focused-oracle-suite.json`. These tests demonstrate the new predicate logic against their invented inputs. They do not establish compatibility with the product's actual target schema or clock domain.

`independent-counterexamples.json` contains eight probe records, including a positive control and six individual identity negatives in P7. Every recorded expected frozen behavior reproduced. None is a native result.

| Probe | Inputs and actual result | Interpretation |
|---|---|---|
| P0 | Existing invented factory: compact target everywhere and epoch-shaped deadline; verdict true. | The pure harness is live. Its passing factory is the representation mismatch that conceals the defects. |
| P1 | Rich snapshot/raw targets include the seven actual provenance keys; receipt remains the actual three-key projection. All generation/lat/lon values agree. Endpoint record selection is false; pair and final verdict are false. | HR1 reproduced without changing any driver predicate. |
| P2 | Call the actual full-sample predicate on the same healthy rich-target data, independently of endpoint extraction. Result false. | The second target comparison at driver 588 also requires correction. |
| P3 | Keep compact targets solely to isolate the clock. Fixture origin 125.25 ms; JSON completion native time 180130.25; derived retrieval native time 180135.25; native deadline 190125.25. Both precede deadline, but epoch retrievedAt is 1788901370010. Record selection succeeds; matching request, pair and verdict fail. | HR2 reproduced independently of HR1. The origin and observations are invented pure data with the actual interface's domains; no product is executed. |
| P4 | Both actual target shapes and monotonic deadlines. Verdict false, failing at initial record selection. | HR1 masks HR2 in the full route; the separate controls establish both. |
| P5 | Duplicate equally matching owned/body response rows. Verdict false. | Held-out ambiguity control rejects, as required. |
| P6 | Healthy A/B endpoints plus a third consumed receipt retained during the interval. Pair true; continuity verdict false. | Root's accepted stricter interval remains conservative. |
| P7 | Independently change generation, latitude or longitude in snapshot target or raw target: six controls, all false. | A future shape adapter must retain these identity negatives. |

The HR1 control copies the shape specified by `captureWeatherTarget`, not the values of a provider response or any secret. The HR2 values deliberately keep both body settlement and receipt before the native deadline. No tolerance, producer or product state was modified to obtain either result.

## Delta preservation and remaining inspected logic

`preservation.json` records AST **and source-text** equality for all 23 prior top-level functions outside `main`, plus all four prior test classes (`ReadBoundaryTests`, `MotionTests`, `RainTests`, `ResumeTests`). The complete prior recovered-watch block is identical; its SHA256 is `cba31901249961d8673fef507aaa3a1ef0f28e7d23ae5031efbc94b5d71876ac`. The fixture bytes match the independently reviewed v2 bytes. The only six new top-level functions are the healthy-refresh record, request, receipt, sample, pair and evidence functions. Full actual diffs are retained as `driver-v2-v3.diff` and `tests-v2-v3.diff`.

This preserves the v2 HN1–HN4 preparation result in its earlier scope. It does not turn the blocked v3 extension into a usable acquisition harness. The full v2 campaign was not repeated.

| Inspected boundary | Assessment of frozen delta |
|---|---|
| Ordinary request after genuine recovery | The endpoint pair requires an available model, a later source and retrieval, a higher publication revision, a later weather ordinal, distinct operation/attempt IDs, a request starting after the recovered capture, and at least 60 seconds between A/B requests. HR1 and HR2 currently prevent real endpoint/request selection. Locations: driver 495–550, 607–639, 1051–1098. |
| Passive acquisition | The new progress expression reads the existing ready fixture, native elapsed time, latest passive record and filtered weather ledger. The loop adds ordinary waits and calls the pre-existing observer capture path. Static inspection found no new render, atmosphere, painter, reconciliation, acquisition, Moon producer, clock-setting or helper invocation. The Date offset, native 1x policy and all fixture/product script-body protections remain byte-preserved. |
| Watch and bounded wait | The original uninterrupted 30-second watch remains before the new selection logic. The acquisition deadline is 235000 ms and the unchanged fixture limit is 240000 ms. Failure to select is explicit; there is no alternate success on absent data. The five-second headroom is a declared budget, not measured acquisition evidence. |
| A/B source and receipt binding | Source time is parsed from the actual ledger body with the declared Asia/Riyadh UTC+03:00 offset and interval 900. JSON consumption, ownership and generation are checked. The retrieval/deadline comparison is invalid until HR2 is repaired; this report does not credit the author's claimed deadline binding as working. |
| Immutable A during B handoff | The evidence predicate permits B's candidate pair while A remains active only through membership in the exact original A/B receipt objects by serialized value and A's own inclusive 0–900000 ms source and retrieval ages. Receipt renewal, lane/target changes, withdrawal and observed native B-to-A rollback reject. The final endpoint requires native and every visible foreground layer to carry B. Locations: driver 553–676. |
| Complete retained interval | The interval begins at the actual `recovered` capture and includes its full 30-second watch plus any additional wait. Every retained passive/full sample inside the interval is checked, including a contradictory full snapshot at an endpoint timestamp. A third record is rejected as explicitly accepted by root. Clean endpoints cannot erase a retained failure. |
| Motion and actual full material | The unchanged signed phase/life/wander/population oracle receives all retained chronological samples. Full samples use the existing healthy cloud and rain-origin predicates, native raster/density, decoded solar mask, visible canvas material and foreground cloud alpha. The new pure factory's `rainOriginEvidence.ok` is a synthetic test input; these new tests are not fresh pixel proof. The unchanged HN3 preparation and future actual captures remain the relevant layers. |
| Observation limits | Passive observations contain readiness, coverage, model/lease and foreground/mask-presence fields, not per-tick raster alpha. The report records the maximum passive gap without claiming continuous raster proof. Original video and independent screenshot/video review remain required. An ordinary observed refresh cannot prove forced capture-before-render ordering; that remains separate source evidence. |

No additional material delta defect was confirmed after the two actual interface mismatches. This statement is bounded by the exact read set and synthetic-control scope above.

## Actual read set and carried evidence

`read-set.json` gives the exact paths and extent of the review. The repository files were read-only throughout.

| Surface | Extent |
|---|---|
| `AGENTS.md`; `docs/state-contracts/R000B.md` | Full instructions/intent text. Relevant native-versus-source boundaries and healthy full-model handoff read. |
| Current driver | Whole Python file parsed/hashed; complete actual diff read; all six added pure functions, new progress expression, acquisition and evidence delta read, together with directly relevant unchanged material/capture helpers. |
| Current pure tests | Whole file parsed/hashed; complete changed factory/class and diff read; actual pure definitions loaded. Only the 15 new class tests executed. |
| Current fixture | Whole bytes compared with v2. Clock/origin, JSON consumption, owner ledger, passive/snapshot target and motion/foreground fields, and time cap reread. The earlier complete v2 review is carried by exact unchanged bytes. |
| `src/native/index.html` | Directly relevant `_RAFNOW`, attempt eligibility/deadline, weather target/admission/retrieval and publication target interfaces only. Exact numbered excerpts are in `interface-witnesses.txt`. Whole file hashed; no whole-product inspection or product execution claimed. |
| Archived v2 fixture/driver/tests | Exact hashes checked; bytes/AST/source comparisons and complete delta derived. |
| Prior v1/v2 independent reports | Identity checked only in this delta; unchanged prior own results carried. v1 remains FINAL GAP and v2 remains its bounded HN1–HN4 preparation PASS. |
| Author extension report and evidence index | Full text read after the independent defects were established; both exact hashes checked. Referenced author scripts/logs were not executed or separately qualified by this reviewer. |
| Requested audit-playbook Finding Row Contract | Read through its skill resource only for the complete finding fields. No internal cognition or governor control route was loaded or claimed. |
| Own v3 evidence | Control source, raw focused result, counterexamples, diffs, preservation and hash/read-set records inspected. Exact frozen copies of all three reviewed harness files retained under `frozen-inputs/`. |

The predeclared candidate/baseline expected manifests, generated/build cohort, source-stage route, exact product regression repair, hosted browser evidence, network execution, screenshots/video and integration were not qualified by this delta. Their separate root-owned gates remain open. Root-supplied HEAD and generated identities are context only; no ref or remote operation was performed here.

## Final identity and authority attestation

The three current harness inputs still match the exact hashes in the opening table. Archived v2 hashes remain:

| Archive input | SHA256 |
|---|---|
| Fixture | `5bdce6f58fc01b2a8d88d55348163bea71b13fa3a83b49a5799e2511d8b62b5c` |
| Driver | `73afb4d772e32bd21f2697777914f3db8d2d28c3833271ef669037b079fb28bc` |
| Pure tests | `3d60eec118064858d2294955a690a80d88dcb5021376e5362b5f2f6be44f0f82` |

Preserved v1 report SHA256 is `3416fa2eb2ea30969ea23992a7b13dd19ba414282c9c2bd1ea116d3897a0c60c`; preserved v2 report SHA256 is `241d33b91c6db32c7991de184975e08731393127a9ebf1cb5018c688648529ab`. Author report SHA256 is `50cb87b7a2a7f8dbb813bce9adf00717fa7e787ec965116a930fd549d33e7f1f`; its evidence index SHA256 is `c991fcbdba2277c9c7a3785007ba983e7cbc29c13d228f3d03039156ad1d2d44`. All 13 initial/final checks are unchanged in `final-identities.json`; `artifact-manifest.json` binds this final report and its own evidence files without a self-hash cycle.

Only the designated v3 report and evidence directory were written. No repository change, native/browser/listener acquisition, dependency install, build, product body/producer execution, ref/remote action, communication to an external party or acceptance action occurred. No secret was reproduced in this report or its bounded evidence.

**FINAL GAP.** HR1 and HR2 remain open against this exact freeze. Root owns the narrow instrument correction, newly frozen hashes, independent closure read and any later acquisition decision. The author may prepare a correction without changing this finding's original evidence. Product/source F01 and native qualification are separate; no product RED, native PASS, readiness, acceptance, integration or issue closure is conferred here.

