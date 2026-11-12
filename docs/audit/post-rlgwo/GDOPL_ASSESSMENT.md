# GDOPL Post-RLGWO Assessment

GDOPL means **Gradient Descent Over the Project Lagrangian**. This assessment applies it, as a
discipline for comparing project configurations, to main `363c3e53` against the original audit's
projection at `f71fef6c`. It is documentary: no change is proposed for adoption here (see
[Authorization boundary](#authorization-boundary)).

Inputs: lane GDOPL sections ([lanes/](lanes/)), the second omission pass, the registry
([IMPLICIT_STATES.md](../../../IMPLICIT_STATES.md)), [FINDINGS.md](FINDINGS.md), and the original
`GDOPL_PROJECTION.md` / `GDOPL_FINAL.md` inside the archived
[original audit](../../state-contracts/evidence/R0017/original/ORIGINAL_STATE_MACHINE_AUDIT.zip).

## 1. Schematic formulation

    minimize   f_T(q)
    subject to q ∈ F_hard,  g_j(q) ≤ 0  (j = 1…m)

    L(q, λ) = f_T(q) + Σ_j λ_j g_j(q),   λ_j ≥ 0

- `q` is a project configuration: source, ownership, generated outputs, qualification process.
- `f_T(q)` is the project objective over a horizon `T`. It is **vector-valued and only partially
  ordered** (below); no scalarisation is defined.
- `g_j(q) ≤ 0` are modelled soft constraints (bounds, budgets, cadences); `λ_j` are notional
  multipliers.
- `F_hard` is the hard feasibility domain; it is never traded against `f_T`.

**This formulation is schematic.** There are no measured weights, no differentiable objective,
no solver, no optimum and no convergence claim. "Gradient" means only the direction of a discrete,
evidence-checked variation `q' = apply(q, η)`; no lane produced measured values with units, so
no finite-difference or differentiable-gradient statement is made anywhere in this document.

## 2. Objective dimensions

`f_T` components (each compared separately; "better" on one may be "worse" on another):
stale exposure; time to useful prayer presentation; redundant acquisition and recomputation;
wasted worker/UI-thread work; status and evidence truthfulness gap; ownership complexity;
verification burden; documentation drift; deployment payload and risk.

Modelled constraints `g_j` named by the lanes: retry spacing ≥ 60 s weather / 600 s radar;
attempt deadline 10 s; weather TTL 900 s; refined frame age ≤ 30 s accepted UTC; ≤ 1 pending
mask decode and ≤ 2 decoded masks per instance; spectral fit retention ≤ 12,000; no orphan
canvas/worker after failed construction; cloud pixels only under a current receipt; Pages payload
≤ 1 GB (the R0017-qualified bound); Moon render deadline 240 s / boot 120 s.

<a id="hard-feasibility-domain"></a>
## 3. Hard feasibility domain and current evidence

| Hard constraint | Evidence that it holds | Finding that bears on it |
|---|---|---|
| Prayer, date, timezone and countdown correctness | next-event selection explicit and mutation-tested (ISM-PRAY-005, NF01 resolved); admission rejects wrong-day/zone records (ISM-PRAY-003) | PRA-F-02 (invalid hint zone → permanent unavailability; fails closed truthfully but never recovers); PRA-F-05 (builder can flip the calculation method); PRA-F-21 (unreachable stale attribute) |
| Rejection of unauthorised late results | generation/operation/attempt fences (ISM-PRAY-002), refined lifecycle epoch (ISM-SKY-006), Moon serial (ISM-MOON-003), builder/settings owner checks | PRA-F-04 (a stale form commit after Reset is an authorised but out-of-date intent, not a late provider result) |
| Truthful weather and location provenance | model estimates labelled; receipt is not freshness; radar grants nothing (ISM-WX-002); external coordinates admitted before normalisation (ISM-WX-010) | PRA-F-03 (truthful withdrawal, continuity cost); PRA-F-17 (unbound elevation, retained caches); PRA-F-04 (OM-04 stale "Saved" label); PRA-F-38 (diagnostic `sim*` overrides from any URL, SIM marker only in the accessible label) |
| Separation of accepted from displayed state | refined host keeps accepted vs painted jobs (ISM-SKY-015); Moon host authority vs `.mphoto` (ISM-MOON-003); cloud receipt re-checked at final publication (ISM-WX-005) | PRA-F-04 (runtime ≠ form ≠ storage); PRA-F-08 (displayed scene torn down by a zone write); PRA-F-15 (getters publish) |
| Optional astronomy never blocks prayer | separate `<script>` elements isolate wrapper and tail failures (lane E) | **PRA-F-01**: a throw from `SalahMoonRuntime.request()` inside `render()` aborts prayer publication and stops the loop (injected-fault probe); no natural trigger found |
| Instance-owned disposal and cancellation | R0021 custody/unwind for the refined sky and Moon (ISM-SKY-015, ISM-MOON-016); request slots cancelled by generation | PRA-F-22 (healthy preview `dispose` keeps the registry slot; latent) |
| Canonical source and mutation ownership | generated parity holds at baseline (build twice, §12 of the report); digest-guarded core transforms | PRA-F-19 (partial build states, `assert` guards); PRA-F-09 (no gate on main) |
| Truthful evidence claims | certificates bind SHAs; failing sets compared differentially | PRA-F-06, PRA-F-07, PRA-F-11, PRA-F-15, PRA-F-18, PRA-F-27, PRA-F-35 |
| Safety, privacy and authority boundaries | installer preview effect boundary and staging trust (ISM-INST-001…004) within recorded scopes | PRA-F-16 (radar location to a third party, no consumer); PRA-F-05 (local-mode coordinates to BigDataCloud); PRA-F-17 |

## 4. Optimisation level supported by the evidence

Only **project-level, discrete, local variational comparisons** are supported: a current
configuration `q`, a neighbouring `q' = apply(q, η)` that changes one owner, guard or process
step, the hard constraints it must respect, and the before/after source or test evidence (if any)
that distinguishes them. "Demonstrated" requires before/after source or test evidence from
`f71fef6c` → `363c3e53`. Counterfactuals below are grounded in source but are not observed
results.

**Concolic discipline** (applied in full to I-1…I-4, the four most material interactions):
(1) concrete evidence bound to source and a run; (2) the symbolic guard/ownership relation that
decides the transition; (3) a grounded counterfactual `q'`; (4) the comparison on each `f_T`
component and each hard constraint; (5) the refined uncertainty.

## 5. INNER GDOPL — implementations and cross-machine transitions

<a id="i-1"></a>
### I-1 Optional astronomy on the prayer path (retry/cancel/cleanup; conflicting ownership)

1. *Concrete.* `loop` (S:3869–3889) calls `render()`; `render` calls `renderMoon()` (S:3494)
   before prayer writes (S:3499–3518); probe E (re-run) with a throwing `request()` leaves
   `.cn`="SENTINEL", `.times` empty; `_raf` stays non-null so `start()` cannot reschedule.
2. *Symbolic.* Prayer publication ⇐ ¬throw(Moon.request) ∧ ¬throw(applyTheme) ∧ …; loop liveness
   ⇐ reaching S:3888. The refined host has the opposite relation (catch and reschedule,
   `real-sky/native-host.mjs` ~L253).
3. *Counterfactual.* η1: isolate optional Moon/sky calls with a receipt of the failure; η2: order
   `renderMoon` after prayer publication; η3: reschedule before work (or in `finally`).
4. *Comparison.* Benefit: removes a hard-constraint dependency on "Moon never throws". Cost: a
   masked error needs a truthful receipt; η2 may change the minute stamp freshness consumed by
   `paint` (ISM-MOON-002); η3 could hide repeated failures.
5. *Uncertainty.* No natural trigger found; materiality conditional. Class:
   **plausible improvement requiring verification**.

<a id="i-2"></a>
### I-2 Configuration change → invalidation fan-out (redundant invalidation/recomputation)

1. *Concrete.* `classifyConfigChange` (S:721–741) and three-path `applyConfig` (S:3729–3760);
   probe A P4: label+time change keeps requests 2 / generation 0; RED 16/34 → GREEN on R0003.
2. *Symbolic.* broad ⇐ any of {target, calculation, tz, units, lp, seed, evidence, unknown key,
   Reset}; broad ⇒ generation++ ⇒ all four request slots cancelled ⇒ prayer, weather, radar and
   scene restart.
3. *Counterfactual.* η: `units` → weather-only path (keep prayer and radar); `seed` → renderer
   reads `CONFIG` or `seed` leaves the persisted config.
4. *Comparison.* Display-only fields: **demonstrated improvement** (before/after tests and
   probe). Units/seed: fewer restarts vs new partial-invalidation rules and mixed-unit records.
5. *Uncertainty.* Owner deferred (D3/D4). Class for I-2 (display-only narrowing):
   **demonstrated improvement**; the units path is I-23.

<a id="i-3"></a>
### I-3 Clock/date/timezone transitions across consumers (OM-01; redundant invalidation)

1. *Concrete.* `skySceneIdentity` includes `tz` (S:2219); `boot` ends the initial document
   (S:3827) before the loader writes `tz` (S:3676/S:3691); probe G: a builder embed boots on
   `America/New_York` and flips to `Asia/Riyadh`; probe A P2: the same write discards a
   `SalahClock` preview; P1: an invalid hint halts prayer.
2. *Symbolic.* Any `tz` write ⇒ {formatter re-key, explicit-clock re-anchor, civil-day change,
   new sky identity ⇒ `beginSkyScene` ⇒ Moon invalidate (non-initial) + cloud receipt withdrawn}.
   There is no validity guard on the hint and the builder never emits one.
3. *Counterfactual.* η1: an ordinary wall-clock sky identity without `tz` (UTC and lat/lon
   determine the sky); η2: the builder emits the resolved zone; η3: validate the hint at
   normalisation; η4: keep a `SalahClock` anchor in UTC across zone adoption.
4. *Comparison.* Benefit: one scene per boot, preserved initial Moon head, recoverable prayer,
   truthful previews. Cost: η1 must prove no consumer needs zone-keyed identity (explicit-clock
   anchors do); η2 changes the portable embed format and README; η3 could silently replace a
   user-intended zone.
5. *Uncertainty.* Visual effect of the second scene unobserved; first-paint tests use the default
   zone. Class: **plausible improvement requiring verification**.

<a id="i-4"></a>
### I-4 Stale async results and accepted vs displayed state in weather → clouds → refined sky

1. *Concrete.* `retryGate` S:1276 holds the refresh while the record is selected; probe B: no
   eligible record from 06:30:00.001 to the 06:30:20 poll; on expiry `reconcileCloudPublication`
   withdraws the deck (S:2730–2741), which snaps back (S:3233); the R000B certificate recorded the
   header gap on the delivered page. Separately, probe D: in `ADVANCING`/`_clockPreview` modes only,
   interpolated preview weather re-keys the refined identity every simulated second and no result is
   accepted once one render exceeds 1000/rate ms (worker durations are probe parameters).
2. *Symbolic.* Displayed clouds ⇐ receipt current ⇐ decision available ⇐ `sourceAge ≤ TTL`;
   replacement request ⇐ ¬selected. Refined acceptance ⇐ epoch and identity unchanged during one
   render; identity ⊇ {rh, cloud, code, wind} ⊄ job inputs.
3. *Counterfactual.* η1: open the weather gate at `sourceAge ≥ TTL − margin` keeping every fence;
   η1′ (rejected): hold the deck past TTL — violates `F_hard`; η2: refined identity carries only
   job-consumed fields, or preview weather is quantised for the snapshot; η3: report identity
   churn as its own availability state.
4. *Comparison.* Benefit: fewer truthful-but-visible withdrawals; refined sky can be accepted at
   moderate rates; truthful status. Cost: an extra request per interval and a provider-cadence
   assumption; η2 must keep every physics input.
5. *Uncertainty.* Provider cadence and worker durations are not measured. Class: **plausible
   improvement requiring verification** (both). NF02 (withdrawal independent of the timetable)
   is I-26 below.

### Other interactions (summary)

| # | Interaction | Current `q` | Neighbour `η` | Benefit / regression cost | Evidence | Class |
|---|---|---|---|---|---|---|
| I-5 | Wall-clock correction vs retry spacing (XF02) | elapsed `_wxRetry` | — (taken) | removes stranded reacquisition / degraded wall fallback remains | RED 18 fail → GREEN 23/23, mutations 12/12, native ×2 | demonstrated improvement |
| I-6 | Backward clock vs source age (PRA-F-24) | refetch each 60 s, never admitted | skew tolerance state | could restore weather / risks blessing future data (hard) | source only | insufficient evidence |
| I-7 | Reset continuation vs dirty close (PRA-F-04) | continuation dropped; stale form committed | clear `_setDirty` at dispatch; name edits keep the continuation | Reset intent kept / may drop genuine pre-Reset edits | VM probes | plausible improvement requiring verification |
| I-8 | Builder reverse geocode vs method (PRA-F-05) | any JSON adopted | HTTP gate, require `continentCode`, deadline | no silent method flip / fewer auto-fills | VM probe | plausible improvement requiring verification |
| I-9 | External coordinate admission (CF04/CF06) | admit before normalise; detailed outcomes | — (taken) | invalid data advances fallback | before/after tests + delivery review | demonstrated improvement |
| I-10 | Builder preview identity (CF05) | issued-identity record | — (taken) | 0 vs 3 navigations | native control | demonstrated improvement |
| I-11 | Overlapping weather-currency representations | decision cache + cloud receipt + effects receipt + retry record + refined identity | one documented map of which receipt governs which consumer | review clarity / doc only | source | plausible improvement requiring verification |
| I-12 | Diagnostics vs presentation (PRA-F-15) | `qaState` writes storage; Moon getters publish; capture reconciles | pure-read diagnostics | truthful QA / preview handoff timing (`host.test.cjs` L94 contract) | source + test | plausible improvement requiring verification |
| I-13 | Moon worker failure → recovery (PRA-F-12) | terminal; `retry()` unowned; `force-cache` | bounded automatic retry; revalidating fetch | recovers transients / CPU, traffic; cached 404 defeats retry alone | trace + R0021 b20/b21 | plausible improvement requiring verification |
| I-14 | Runtime absent → reveal (PRA-F-13) | no disc | admit the calendar fallback | AGENTS "never empty slot" / conflicts with "no legacy substitution" | R0021 §F | incomparable alternatives |
| I-15 | Light eligibility vs visible surface | `_pbrFailed` | `!SalahMoonRuntime?.surface()` | "no light without a disc" / flicker in transitions | trace | insufficient evidence |
| I-16 | Moon replay vs live runtime (RF01) | refusal + captured detail | — (taken) | single live pair / hot replay unsupported (owner) | before/after source, tests, mutants, native | demonstrated improvement |
| I-17 | Failed refined construction vs DOM (RF02) | custody + unwind | — (taken) | no orphans | before/after + native census | demonstrated improvement |
| I-18a | Spectral retention bound (RF03) | inner FIFO 12,000 | — (taken) | retention bounded | ES27-08 | demonstrated improvement |
| I-18b | Spectral recomputation | ~0 hit rate for continuous B–V | uncached path | removes cache churn / must stay bit-identical | ES27-06; no timing | insufficient evidence |
| I-19 | Page lifecycle across owners | refined suspended; preview/loop by visibility; Moon by visibility only | preview and Moon participate in pagehide | consistent lifecycle / bfcache untestable headless | R0021: no persisted restore obtained | insufficient evidence |
| I-20 | Mask decode settlement (RF04) | no deadline | wall-clock cancellation | liveness / owner decided against | none native | no-change (retention) recommendation |
| I-21 | Hidden tab vs refined Moon | discard on hide | retain and recheck on resume | avoids re-render / stale authority after a hidden seek | trace + test | no-change (retention) recommendation |
| I-22 | Accepted vs displayed refined frame | `frame/job` vs `paintedFrame/paintedJob` | — | — | R0021 tests | no-change (retention) recommendation |
| I-23 | Unit change vs radar/prayer | broad | weather-only path | see I-2 | `CONFIG_EFFECTS` S:707 | plausible improvement requiring verification |
| I-25 | Chronological next-event selection (NF01) | explicit `selectPrayerEvent` | — (taken) | consistent midnight transitions | before probe at `f71fef6c`; P3 + ES07 mutants | demonstrated improvement |
| I-26 | Weather expiry vs missing timetable (NF02) | receipt withdrawal in the no-model branch | — (taken) | no stale deck without a timetable | before/after source + tests + hosted Chromium | demonstrated improvement |
| I-27 | Diagnostic overrides vs truthful provenance (PRA-F-38) | `sim*`/`debugOptic`/`qa` read from any fragment; visible header has no SIM marker | visible SIM marker, or honour overrides only with an explicit debug flag | truthful display / changes documented AGENTS recipes | source trace | plausible improvement requiring verification |
| I-24 | Write-only legacy retry fields | `lastWxTry`/`lastRadarAt` write-only | remove | less state / harness rebinding | R000D | no-change (retention) recommendation |

## 6. OUTER GDOPL — project architecture and engineering method

| # | Direction | Current `q` (facts) | Neighbour `η` | Benefit / cost | Evidence | Class |
|---|---|---|---|---|---|---|
| O-1 | Ownership boundaries: single authored file for prayer, weather, settings, native sky, Moon host | `src/native/index.html` holds all of them; one loop; `tz` multi-writer | domain-owned transition functions with explicit cross-owner contracts (the original projection's architecture choice) | smaller blast radius / large diff across the generated boundary | registry ISM-PRAY-009/010 | plausible improvement requiring verification |
| O-2 | Authored source vs generated outputs | in-place generation; `assert` guards; no staging; parity by executor discipline (build-twice clean at baseline) | stage outputs and swap after the Moon stage; `raise` instead of `assert`; count-check replacements (original G01) | removes partial states / small builder diff | lane F probes A–D; source | plausible improvement requiring verification (G01 not taken) |
| O-3 | Qualification process | 32 workflows, 30 on named work-order branches, 6 dispatchable, 1 PR-to-main job locked to PR 62, **none on `push` to main**; merge = deploy | a main/PR gate running the registered suites, build twice with a diff and `verify_v1` | earlier detection / needs an explicit expected-failure manifest; CI minutes | trigger census | plausible improvement requiring verification |
| O-4a | Committed publishable bytes | git-blob sum after the `_config.yml` exclusion: 0.898 GB (PR 62) → 1.771 GB (`f71fef6c`) → 1.910 GB (baseline); retained evidence 16,119 files / 1,878.8 MB (85 % of the tree) | — | — | `git ls-tree` sums at three commits (exactly what is demonstrated: growth of committed blob bytes that Jekyll would publish under the stated exclusion rule) | **demonstrated regression** of the committed-bytes input only |
| O-4b | Built Pages payload versus the ≤ 1 GB modelled bound | no `_site` was built; GitHub's enforcement unverified | — | — | estimate only | insufficient evidence |
| O-4c | Evidence off the deployed payload | evidence under deployed `docs/` | extend `_config.yml` exclusions, or move evidence off the deployed branch | smaller payload / github.io evidence links break | estimate | plausible improvement requiring verification |
| O-5 | Stale instruments | 7 red instruments; 3 regressed by R000B, 1 case by R0007; failing sets compared in prose | per-case expected-failure ledger; retire side-branch-only docs checks | restores signal / risk of hiding real regressions | integrator runs at 10 commits | O-5a EF01 runner repair: demonstrated improvement; O-5b date harnesses: **demonstrated regression** (green at `eebba178`, red from `da126880`); O-5c remainder: insufficient evidence |
| O-6 | Hash-pinned receipts | exact pins in many receipts; re-pin protocol | bind receipts through one manifest | fewer cascades / weaker locality | R0027 protocol | incomparable alternatives |
| O-7 | Closure authority | final state in issue certificates; contracts can contradict (R0015) | contract records its own superseding certificate | coherent record / extra commit per closure | PRA-F-27 | plausible improvement requiring verification |
| O-8 | Installer transactional admission (CF01–CF03) | per-attempt roots, records, one admission predicate | — (taken) | defects removed / `install.ps1` 614 → 1,741 lines; 22 installer workflows | diff, tests, native runs | demonstrated improvement |
| O-9 | Frozen v1 truthfulness | bytes frozen and served; limitations unrecorded; `--check-pages` fails | document CF07–CF09 and the check status without byte change | truthful record / none to runtime | source + run | plausible improvement requiring verification |
| O-10 | Whole-widget budget (original "budgeting across bounded workers") | none; Moon 4 shards ≤ 512 MiB each; compose up to 20 Hz | a measured priority contract (prayer > first celestial > refinement) | protects prayer responsiveness / needs native measurement first | model estimates only | insufficient evidence |

## 7. Historical comparison with the original projection

| Projected direction (`GDOPL_PROJECTION.md` / `GDOPL_FINAL.md`) | Taken? | Before → after evidence (`f71fef6c` → `363c3e53`) |
|---|---|---|
| One chronological prayer-boundary selector | taken | R0007: NF01 probe at `f71fef6c` vs probe P3 and ES07 mutants |
| Independent weather-to-cloud permission transition | taken | R000B: no-model bypass at `f71fef6c` vs S:3491 reconcile; withdrawal tests; hosted Chromium |
| Selective config invalidation (effect matrix) | partly | R0003: label/time/date/appearance narrowed (RED 16/34 → GREEN); units, lp, seed, method/school still broad (D3/D4) |
| Separate builder draft/output/preview revisions | taken | R000F: native control 3 navigations vs 0 |
| Instance-owned construction/disposal | taken | R0021: RF01 (refusal + captured detail), RF02 (custody + unwind) with native cells and mutants |
| Explicit artifact staging/admission | taken (PowerShell); partly (Bash) | R0015: CF01–CF03 tests and runs; Bash residuals in ISM-INST-006 |
| Bounded cache across both spectral layers | taken (inner layer; outer already bounded) | R0027: ES27 tests; recomputation unchanged |
| Separate freshness time from retry scheduling | taken | R000D: RED 18 fail → GREEN 23/23 |
| Bound optional decode progress | not taken | RF04 retained UNVERIFIED by owner decision (R0021) |
| Repair evaluator source boundaries | partly | R0017 fixed extraction and duration; R000B later re-broke three date harnesses |
| Shared priority contract / whole-widget budget | not taken | no measurement; PRA-F-01 is its concrete instance |
| Build staging and preflight (G01, lane F) | not taken | `tools/build_native.py` still writes in place |

## 8. Final classification of directions

Each direction (I-1…I-27 with I-18 split into a/b; O-1…O-10 with O-4 and O-5 split into a/b/c) appears exactly once.

| Direction | Classification |
|---|---|
| I-2, I-5, I-9, I-10, I-16, I-17, I-18a, I-25, I-26, O-5a, O-8 | **demonstrated improvement** |
| O-4a, O-5b | **demonstrated regression** |
| I-1, I-3, I-4, I-7, I-8, I-11, I-12, I-13, I-23, I-27, O-1, O-2, O-3, O-4c, O-7, O-9 | **plausible improvement requiring verification** |
| I-14, O-6 | **incomparable alternatives** |
| I-6, I-15, I-18b, I-19, O-4b, O-5c, O-10 | **insufficient evidence** |
| I-20, I-21, I-22, I-24 | **no-change (retention) recommendation** |

<a id="authorization-boundary"></a>
## Authorization boundary

An apparent improving direction above is an analytical result, not permission to change the
repository. Every "plausible improvement" names the verification it would need; every change to
the native, builder, Moon, generated, vendored or frozen-v1 boundaries also needs the owner
authority that `AGENTS.md` requires. No weights, gradients, optima or convergence are claimed.
