# R000B recovered source review

## PARTIAL — read-only source assessment in progress

This is an independent bounded source review, not final candidate acceptance, native-pixel qualification, whole-RLGWO PASS, or lifecycle authority. No product, documentation, test, Git, network, or shared-browser mutation is authorized or performed. Only this review and any bounded probe artifacts in the assigned scratch directory may be written.

### Assigned and independently observed identity

- Repository: `/workspace/scratch/15b8fb6ac4c2/r000b-work`
- Base: `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b`
- Head: `d124f050ec68fa8608022b1ed5fead426d42dcb9`
- Head tree: `54c61ab27f95adcf0837f737ca3dfd09649fc5c3`
- Source repair: `136f21b1697a5e1e9d9f453464c8250fb9f3e540`
- Prior source checkpoint: `9dabdcf338a7307c0256dcdccac48326b357f0d5`
- Authored `src/native/index.html` SHA-256: `b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f`
- Base/head authored Git blobs: `f610f647cc6c920e0dd528c95c86099f7394e662` / `2d99b5af9c2eee7ffa7d1e3771392f2cfd03b0b0`
- Initial `git status --short` was empty.

### Work performed and current boundary

Read repository AGENTS, the R000B core contract, relevant full-packet protocols, the authored source delta, the affected native composition/capture handoff delta, and the actual source fixtures and focused tests. The current review traces real weather admission, target/generation selection, consumed cloud receipts, no-timetable withdrawal, per-painter/capture revalidation, and async publication guards. Source tests use controlled clocks/DOM/canvas and retained-alpha sentinels; they do not constitute browser-pixel evidence.

The production source separates consumed publication from the selected replacement record and retains the original weather eligibility function. The no-model branch reaches cloud/effect withdrawal, actual raw-raster clearing is present, and no new request loop is introduced. A final conclusion awaits the remaining transition and handoff checks.

No demonstrated product finding is recorded at this partial checkpoint. No historical review verdict has been used to establish correctness. Native execution and rendered inspection remain explicitly unexecuted in this review.

### Remaining review

1. Complete original B01–B18 obligation crosswalk and current ES0B scope.
2. Finish current consumer/capture/async exception paths and evidence-lease edge cases.
3. Run only a bounded probe if a concrete source uncertainty warrants it.
4. Record exact final read set, observations, findings or nonfindings, and residual native limits.

---

## FINAL — NEEDS_REVISION within the bounded source scope

Final identity check: **2026-11-10T05:39:45.639458+00:00**. The assigned HEAD, tree, authored source digest, and empty worktree status remain unchanged. This disposition is an ordinary independent source review returned to the root. It is not a formal `audit-assess` lifecycle disposition, final candidate acceptance, or whole-RLGWO verdict.

The recovered source contains the ordinary live-weather no-timetable withdrawal and the bounded healthy A→B handoff. I found one demonstrated remaining source gap: **an unchanged model record bypasses the separate synthetic-present authority lease, and same-record republication can leave the consumed cloud receipt bound to the previous evidence.** The complete source claim cannot receive a bounded PASS while that counterexample remains unresolved.

### Exact final identities and artifacts

| Object | Identity |
|---|---|
| Base commit / tree | `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b` / `6b94a3933f9d1381b1c2ceaab287c93afb215ecb` |
| Base authored source SHA-256 | `6054f1eb3e7f04aa5975707345810b64fc824bc99e17ce3798369a959a123fad` |
| Candidate commit / tree | `d124f050ec68fa8608022b1ed5fead426d42dcb9` / `54c61ab27f95adcf0837f737ca3dfd09649fc5c3` |
| Candidate authored source SHA-256 | `b17801b33cc99c95710b916016dfd542eddce304145b493c0adecc4c3412e37f` |
| Probe | `/workspace/scratch/d9a9ea2be931/recovery/source-lease-probe.cjs` |
| Probe SHA-256 | `c0500e9cab8cfb39e09037f6de51ab37594f14181d2c17492249f02a1c3fcbc6` |
| Probe output | `/workspace/scratch/d9a9ea2be931/recovery/source-lease-probe.json` |
| Probe output SHA-256 | `439876f6713c6ebaa458e2d12860781160cc374ab3e3234e85dedfae00f1f4be` |
| Read-set / static identity record | `/workspace/scratch/d9a9ea2be931/recovery/source-read-set.json` |

The probe executed once with Node and exited 0. It asserts the contrary behavior and writes its observations; exit 0 is **successful reproduction of the gap**, not a product test PASS. No existing suite was rerun merely to reproduce counts. No browser, public provider, builder, network mutation, Git mutation, or product/test edit occurred.

### Finding SR-01 — same-record retention omits consumed present-evidence authority

**Priority:** P2. **Owner:** R000B native cloud-publication consumer, at the N09→N15/N13 join. The existing R0024 evidence-admission/meaning owner is an unchanged dependency; this finding does not authorize a new observation adapter or a policy/TTL change.

**Paths and evidence:**

- `src/native/index.html:2565–2566`: if the consumed and candidate model record objects are identical and non-null, `cloudAuthorityMatches()` returns true before checking the consumed present evidence.
- `src/native/index.html:2570–2572`: present-evidence identity/eligibility is checked only in the different-record handoff branch.
- `src/native/index.html:2576`: receipt deduplication compares state, reason, record, lane, target, scene and mode, but omits the consumed evidence/decision semantics. A changed same-record decision can therefore be painted without updating the stored receipt or `_cloudPublication.decision`.
- `src/native/index.html:3001–3003`: when an otherwise eligible record has no layer fields, cloud layers are derived from the effective condition. Thus present evidence can actually supply the coverage; it is not only an unused diagnostic field.
- `tests/weather-no-timetable-handoff.test.cjs:216–224`: the existing direct-evidence cases explicitly call `startWeather(true)` to replace the model object. They cover the different-record branch and omit the unchanged-record case demonstrated here.

**Demonstrated schedule:** the probe uses the existing full authored-runtime fixture with `simWx=0&simCloud=0`, retains its real SIM record, admits a qualified synthetic wet/rain fixture through `admitWeatherFixture()` with a 1,000 ms lease, and calls the actual `render()` and `paintClouds()` owners. It then advances the controlled wall time to the fixture expiry without replacing the model record, removes prayer availability, and calls the same real render/painter owners.

| Observation | Before expiry | After expiry and actual no-model render/painter |
|---|---:|---:|
| Model record is unchanged | true | true |
| Present evidence currently eligible | true | false |
| Candidate effective code | 63 | 0 |
| Prayer model available | true | false |
| Cloud coverage / targets | `[0.9, 0.85, 0.3]` | `[0.9, 0.85, 0.3]` |
| Cloud readiness | true | true |
| Current header/effect class | rain | clear |
| Old receipt passes `cloudPublicationCurrent()` | true | true |
| Stored cloud receipt condition | simulation-fixture-rain | simulation-fixture-rain |

The painter still emits 169 retained-raster fill commands after expiry and its density remains nonzero. Before removing the genuine model, the actual current `atmosphere(model())` candidate reports layers `[0, 0, 0]`. This isolates the retained rain-derived deck from the current clear SIM record. These are source-state/painter-sentinel observations, not native pixels.

A companion in the same bounded probe admits a new dry fixture over that unchanged record and performs an ordinary full render. Its cloud targets correctly become `[0, 0, 0]` and coverage takes the ordinary easing step to `[0.8280000000000001, 0.782, 0.27599999999999997]`. Nevertheless, the receipt remains the exact previous object, `_cloudPublication.decision` still names code 63 and the old evidence, and the old receipt passes the final guard. This separately demonstrates inaccurate consumed cloud provenance after a real successor publication.

**Consequence:** expired present-derived coverage survives the intended no-model withdrawal boundary, and the consumed-authority receipt can disagree with what a later complete atmosphere consumed. Because the native preview/refined async publication owners use this same final receipt guard, the guard also remains permissive for the old receipt. Re-publication by an actual native decode was not executed in this review; that further sink consequence is inferred from the inspected callers. The demonstrated effects concern B07/B08/B11 and ES0B-02/06/12/13, plus the changed direct-evidence branch of B13/B14's test coverage.

**Countermeasure:** keep the existing weather decision and evidence eligibility owners. Make the unchanged-record retention path enforce the authority of every evidence component actually consumed by that publication, including its original present lease. Bind receipt identity and the private consumed decision to a materially changed consumed publication even when the model record is unchanged. Preserve the accepted healthy full-model A→B lease and ordinary 0.08 easing behavior; do not solve this by reseeding clouds, renewing source time, inventing prayer data, or rejecting all healthy replacements.

**Check:** add actual-consumer companions that hold the model record fixed while (1) the consumed direct fixture expires, (2) a fresh fixture replaces it with and without a genuine prayer model, and (3) a new complete publication occurs before an old decode completes. Include a positive same-record model-only control and current same-evidence control. Assert readiness/coverage/density/raw raster withdrawal where required, consumed-decision/receipt identity, and rejection of the superseded receipt. Keep the existing different-record own-age and healthy-easing controls.

**Residual risk and limit:** `weatherSynthetic` is a closed, explicit QA lane; there is no normal live setter or qualified deployed observation provider. This is not a demonstrated live-provider incident, nor a finding that ordinary model-only weather expiry is broken. It is nevertheless part of the requested preserved simulation/direct-evidence contract. Root owns its disposition and any bounded repair authorization. The source fast path already existed at the prior R000B checkpoint; this review does not attribute it solely to commit `136f21b`.

### Supported source observations and preservation limits

The no-model `render()` branch captures one decision and passes it to header, cloud/effect reconciliation and independent celestial presentation. Withdrawal zeros coverage and targets, revokes readiness, clears the retained density array and actual backing canvas, and marks the ordinary painter dirty. The painter and native foreground capture both reconcile before reuse. The ordinary frame loop also reconciles before the reduced-motion dirty check, so expiry does not depend on fresh cloud movement. These are inspected code properties, not a claim of newly executed native scenes.

The healthy different-record handoff requires independently eligible A and B, the actual non-null `model()`, matching generation/target/lane/scene/mode, and the exact active receipt. It neither calls a producer nor consumes a new easing step. The native preview/refined owners reject invalid captured cloud receipts before final visible writes and again after fallible lunar detail composition; canceled pending masks lose their context, and fallback retention is conditional on the displayed receipt. The shared predicate defect in SR-01 limits this otherwise explicit fencing.

No new retry, request generation, provider, temporal threshold, cloud advection, or prayer-admission mechanism appears in the changed production source. Withdrawal does not itself call `beginSkyScene`, dispose a renderer, reset cloud population/phases/life/wander, or erase raw weather/cache provenance. The no-model celestial path continues using independent physical solar and lunar owners without `atmosphere(null)` or a fabricated timetable.

Static before/after segment hashes in `source-read-set.json` establish byte identity for the existing weather-eligibility function; the target/cache/acquisition/radar region; forecast synchronization, weather decision and header owners; cloud population/motion integration; the painter body after its added reconciliation call; and rain-origin coupling. This preserves only those source regions. It is not an assertion that every historical B row was freshly executed or that retained metrics qualify motion.

The exact changed selector and cloud-publication fragments occur once in both generated `index.html` and `offline.html`. Their complete SHA-256 values are `604eddd742ea2818520d51d9b16da102e9375e6a88f6b1a2cce4ec8dbf7dbb92` and `03b4ca62b94173a70c9d60c7db51a1b309f8eff4e5ae6d410e67d96ea2d0d29f`. This is bounded static propagation evidence, not a canonical rebuild, full delivery parity certification, served-byte verification or native execution.

### Original B01–B18 crosswalk for this review

| Obligation | Bounded result |
|---|---|
| B01 source/receipt metadata | Existing admission metadata is preserved; selector/receipt consumers inspected. SR-01 concerns separate present evidence, not renewal of model timestamps. |
| B02 radar provenance | Unchanged radar region hash; no new execution or radar observation claim. |
| B03 explicit-zone inverse | No changed inverse/admission implementation; historical scope is not independently re-certified here. |
| B04 hostile radar epochs | Unchanged relevant source region; no bulk historical replay. |
| B05 current freshness | Existing inclusive source/receipt function is byte-identical; own-A age tests inspected. |
| B06 radar/cache retention | Existing radar/retention region byte-identical; no new storage semantics. |
| B07 per-use withdrawal | Ordinary live no-model join is implemented; SR-01 prevents a complete consumer nonfinding. |
| B08 unavailable display/effects | Unknown remains explicitly unavailable; SR-01 identifies a separate consumed-cloud mismatch. |
| B09 legacy cache custody | Cache/admission region is byte-identical; no purge, migration or receipt renewal. |
| B10 acquisition/bookkeeping | Existing request/acquisition implementation unchanged; no new loop. |
| B11 mode/evidence distinctions | Existing decision policy unchanged, but SR-01 misses same-record present-lease withdrawal. |
| B12 target/late ownership | Generation/target/scene/mode and active-receipt guards inspected; late-owner tests read. No new final execution credit. |
| B13 hostile/recovery integration | Actual admission/model/capture fixtures inspected; same-record direct-evidence companion is missing. |
| B14 mutation discrimination | Required consumer mutants and handoff mutants inspected; not rerun for counts. Add SR-01 discriminators. |
| B15 native outage/retry | Unexecuted here; original earned evidence is not replaced by this source review. |
| B16 native pixels/celestial/motion | Unexecuted here; source preservation and sentinels do not qualify visible output. |
| B17 documentation/state map | Current policy read; its consumed-authority account is incomplete for SR-01. |
| B18 integration/delivery/closure | Outside authority and unperformed; root retains exact-candidate and closure decisions. |

### ES0B-01–15 crosswalk for this review

| Obligation | Bounded result |
|---|---|
| ES0B-01 | Ordinary 901s no-model withdrawal has actual-owner tests and inspected state/raster joining. No fresh native verdict. |
| ES0B-02 | Painter/capture/final sink fences exist; SR-01 leaves one declared lane's expired material current. |
| ES0B-03 | Full-model withdrawal and healthy A→B source paths/tests inspected; static numerical continuity preserved. |
| ES0B-04 | Independent no-model celestial path remains; no fake timetable/global blanking introduced by withdrawal. Native usability remains open. |
| ES0B-05 | Missing weather uses unavailable header/effect semantics and retains raw provenance. The SR-01 clear SIM record is actually supported clear, not an unknown-to-clear coercion. |
| ES0B-06 | Warm/cold/replacement no-model policy is explicit; same-record present-expiry edge remains a gap. |
| ES0B-07 | Fresh restoration is through complete atmosphere publication; warm/cold/replacement tests inspected. |
| ES0B-08 | Existing visibility rebasing and single loop retained; reconciliation occurs on resumed opportunity before painter reuse. Native resume unexecuted. |
| ES0B-09 | Exact target/generation/scene/mode and receipt guards inspected; SR-01 limits same-record receipt supersession. |
| ES0B-10 | Withdrawal keeps population/phase owners and bounded objects; unchanged withdrawn receipt avoids repeated effect/header writes. |
| ES0B-11 | Original model-age bounds are byte-identical; no threshold change. |
| ES0B-12 | SIM/forecast/model policy remains separate, but same-record direct-evidence expiry fails the consumer guard. |
| ES0B-13 | Candidate/effect/coverage diagnostics are separated; SR-01 demonstrates stale cloud consumed-decision/receipt metadata after new full publication. |
| ES0B-14 | Motion/rain-origin arithmetic and held-axis mechanisms are preserved; native motion/column pixels remain unexecuted. |
| ES0B-15 | Assigned identity and bounded generated fragment propagation checked; a new source gap and unexecuted native/final-delivery gates prevent completion. |

### Read set and independence

`source-read-set.json` records full-file digests for every explicitly read source, test, policy or contract input. A digest does not imply a line-by-line review of the whole file. Scope was:

- Complete base→head authored diff and prior-checkpoint→repair authored/policy diff; current weather admission/selection/decision/header, scene/model, cloud authority/motion/painter, no-model/full atmosphere, effect/diagnostic, weather-start and frame/visibility owners.
- Current native composition/capture/solar-mask owner, host hooks, preview host and refined host; generated bundle diff and bounded generated-fragment checks.
- Complete new source fixture, no-timetable withdrawal, handoff, authority and mutation test files, plus actual native-weather-withdrawal tests; changed fixture/adapter portions in the shared source, sky, motion and native composition suites.
- Repository AGENTS; R000B CORE; selected explicit-state, historical protocol/interface and acceptance portions of R000B FULL; current `R000B.md` and the B01–B18/current-gate rows of `R000B_ACCEPTANCE.md`.

Production code and actual tests were inspected before the acceptance ledger. No prior independent review report was consulted or used to establish this finding. The acceptance ledger supplied original obligation labels and disclosed boundaries; its prior PASS/test totals were not adopted as fresh evidence.

**Return to root:** retain SR-01 and its exact reproducer, adjudicate the bounded consumer repair, and requalify the changed predicate/receipt branch plus affected native capture/decode joins. All actual rendered native evidence remains separate and unexecuted by this reviewer. No whole-owner acceptance, merge, release, publication or closure is authorized by this report.

