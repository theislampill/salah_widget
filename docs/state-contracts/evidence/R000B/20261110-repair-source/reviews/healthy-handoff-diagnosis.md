# R000B F01 bounded audit-Andon diagnosis

Report state: DIAGNOSIS RETURNED — F01 remains open.

## Entry and authority ceiling

This is the direct return to the actual caller, root, following its explicit bounded cord-pull for observed o15 / F01. The applicable skill is `/home/agent/.codex/skills/remote-skills/skill-6a85962852508191a70c4b0eedbd1928/SKILL.md`, direct-entry envelope: observed abnormality, named caller, diagnosis-only scope, explicit prohibited effects, and no child routing. No controller, currentness, source mutation, release, integration, acceptance, RXX or closure authority is assumed.

The examined product is the root-supplied committed candidate `9dabdcf338a7307c0256dcdccac48326b357f0d5`, tree `916d5d6ad09ae269095187a82b18c64b5684a79a`, in `/workspace/scratch/15b8fb6ac4c2/r000b-work`. The five product sources remain frozen. Root's current source/generated/shared test totals are background evidence, not proof against F01 and not new executions in this diagnosis.

The independent review is [candidate-source-review.md](sandbox:/workspace/scratch/15b8fb6ac4c2/reviews/candidate-source-review.md), reported by root as FINAL BLOCKED, SHA256 `c3c9181012079d9c70ac324679ccc0a6dbad2592a2a4390182570eb8b6fb2798`. I read F01 and Appendix A and reran the exact Appendix A JavaScript body, unchanged, through Node stdin. The probe asserted that its fixture and six declared source inputs matched the committed candidate before exercising either order. Exit code was 0: it asserts setup/eligibility and prints the contrary result; it is not a passing regression test.

- Exact probe JavaScript SHA256: `4b3b760329cd7bf58b7cb976e7c6c52f6f79e5a5bdd8665fd2f0b1e33e4d3b52`.
- Exact probe stdout SHA256: `243465bf3cb84e406926829e02f77997ef74ebf43bc44f42cd4aabe7e15510fc`.
- Only this authorized report was written. The repository-only mutation helper initially refused the external report path before executing a write. Root then explicitly authorized direct replacement of this external report after its G0004 recovery. No helper restriction was bypassed or altered.
- No source/test/harness edit, network, browser, listener, build, ref mutation or additional agent routing was performed.

## Finding and confirmed facts

**Classification: confirmed P2 correctness regression in the shared consumer guard, with a validation coverage gap.** The defect is not an expired-input admission, source-age renewal, cloud reseed or prayer-model fabrication.

At wall UTC `1788901251000` (2026-09-08 21:00:51 UTC), the probe adopted the genuine next-day prayer payload through `adoptPrayerBundle`; `model()` remained non-null. It then admitted same-target B through the actual weather fetch owner. Both records were eligible:

| Attribute | Consumed record A | New candidate B |
|---|---:|---:|
| Target generation | 0 | 0 |
| Latitude / longitude | 24.47 / 39.61 | 24.47 / 39.61 |
| Lane | live | live |
| Code / total cloud | 95 / 95 | 95 / 95 |
| Layer targets | 0.92 / 0.90 / 0.60 | 0.80 / 0.75 / 0.50 |
| Source-valid UTC | 1788900360000 | 1788901200000 |
| Retrieval UTC | 1788901190000 | 1788901251000 |
| A source age at handoff | 891000 ms | Not authority for A |
| A receipt age at handoff | 61000 ms | Not authority for A |

The actual capture owner produced this repeatable ordering difference:

| Order | Coverage at capture | Ready | Capture sentinel alpha | Coverage after ordinary render/painter |
|---|---|---|---:|---|
| Capture, then render | 0 / 0 / 0 | false | 0 | 0.80 / 0.75 / 0.50 |
| Render, then capture | 0.9104 / 0.888 / 0.592 | true | 192 | 0.9104 / 0.888 / 0.592 |

The latter vector is exactly `A + (B - A) * 0.08`. Capture-first changed revision 2 eligible to revision 3 withdrawn, then revision 4 eligible. Render-first changed revision 2 directly to revision 3 eligible. Population remained `11.432099999998172` and phases remained `[0,0,0]` in both orders. These are actual source-state/capture observations at the declared sentinel boundary; they do not measure browser flicker or real cloud opacity.

Sources: Appendix A/F01 in the independent review; [native source](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/src/native/index.html), `weatherEligibility` line 1291, `fetchWeather` 1368, `model` 2219, `applyCloudState` 3080; [capture owner](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/real-sky/native-composition.mjs), `capture` 130.

## Causal account

1. The normal acquisition owner installs B and marks `_renderDirty`. Installing a candidate does not itself run the complete atmosphere/painter. That is legitimate existing separation.
2. `cloudAuthorityMatches` requires the published record reference to equal the selected record. A and B are distinct admitted objects, so it returns false even though A remains eligible and a genuine complete model exists.
3. `reconcileCloudPublication` treats every failed match as withdrawal. It does not consult `model()` before choosing “complete atmosphere unavailable.” It therefore applies the intended no-timetable replacement policy to a healthy full-model handoff.
4. `withdrawCloudState` performs the intended joined clearing, including `_cloudReady=false`. The clearing operation is correct for an unavailable publication; admission to it is wrong in this case.
5. The next `applyCloudState` sees false readiness and takes the established first-deck snap branch. If ordinary render wins the race, readiness stays true and the 0.08 easing branch runs.

The cause is conflating **the candidate differs from the last consumed record** with **the consumed publication is no longer permitted**. Those coincide under the conservative no-model replacement policy, but not during a healthy full-model handoff while the original record still has authority.

The same strict predicate is used by the pure final-publication fence. Fixing only reconciliation leaves the final fence rejecting a permitted retained A. Fixing only the final fence leaves capture clearing the state first. A repair needs one coherent permit rule shared by reconciliation and final validation, with active receipt identity still mandatory.

Locations: native source `cloudAuthorityMatches` 2560; `withdrawCloudState` 2588; `reconcileCloudPublication` 2600; `cloudPublicationCurrent` 2607. Callers include painter 2676, loop 3707, native capture, clear/handoff and both final publication owners. None of these causal steps requires changing acquisition or motion mathematics.

## Local versus systemic scope

The demonstrated schedule is local and bounded. The mechanism is shared: any eligible A-to-B replacement reaching one of these consumers before normal complete publication can hit the branch. It does not require midnight, code 95, these particular layers, a failed weather request or reseeding. Midnight served the original negative fixture; the confirmed healthy probe supplies a real next-day timetable and still fails.

This is an owner/join defect with a narrow likely repair, not evidence that acquisition, prayer, motion or numerical sky owners need redesign. It affects the N08-to-N15 handoff and N15-to-N13 publication permission.

The validation gap is specific. The asynchronous replacement fixtures intentionally establish `model() === false`. Native companion fixtures supply `cloudsCurrent:()=>true` to isolate other composition contracts. Ordinary healthy controls apply the complete atmosphere before painting/capture. None exercises the conflicting positive order: A remains eligible, M remains genuine, B is newly admitted, and capture gets the first opportunity. Thus green selected suites and F01 are consistent observations.

Hansei: my implementation generalized the no-model equality rule into the shared guard, and my positive controls did not reverse consumer order with a still-complete timetable. The durable correction is a paired positive/negative ordering test at the real consumer, rather than a larger count of unrelated checks.

Sources: [weather-no-timetable-withdrawal.test.cjs](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/tests/weather-no-timetable-withdrawal.test.cjs), warm/replacement case; [native-weather-withdrawal.test.mjs](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/tests/real-sky/native-weather-withdrawal.test.mjs), `boundary` and `replace`; [native-host-composition.test.mjs](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/tests/real-sky/native-host-composition.test.mjs), contained host; [R000B contract](sandbox:/workspace/scratch/15b8fb6ac4c2/r000b-work/docs/state-contracts/R000B.md), healthy refresh statement and ES0B-03/14.

## Live, SIM and ADVANCING implications

These are source-derived implications except for the reproduced live order. No additional lane probe was executed.

| Case | Existing source behavior | Repair constraint |
|---|---|---|
| Live current model | `selectedWeather(now)` uses `weatherEligibility`, including both original ages, interval/code and target. | Revalidate A itself. Checking B or the current decision cannot bound A. |
| Explicit `simWx` | `startWeather` installs a synthetic record without live source/receipt metadata; ordinary fetching and `syncWeather` do not replace it. | Preserve the preview contract. Applying live TTL creates a regression. Its usual absence of replacement does not justify a live-only shared-owner rule. |
| ADVANCING / runtime clock preview | `syncWeather` calls `wxAt`, which allocates a new forecast-shaped object. These have target/provenance, but lack current-weather source/receipt/interval fields. Preview selection uses target matching instead of live TTL. | Object churn is normal. Do not require live metadata or decision-object equality. Preserve ADVANCING's existing gain of 1 and the paused-preview behavior. |
| Simulation-fixture evidence | The lane is distinct; qualified present evidence has its own target/lease through `weatherFixtureEligibility`. | Model eligibility cannot extend a direct-present lease. A narrow handoff may require unchanged independently eligible evidence; recordless replacement need not gain retention. |
| Mode / target change | Config changes advance generation; explicit clock control invalidates native owners and begins a new sky scene. `lane` alone does not identify every clock submode. | Preserve invalidations; never cross a scene/clock transition merely because both decisions say “preview.” |

The decision cache is not a publication receipt. It keys selected record, track, synthetic evidence, preview flag and target reference, with expiry boundaries. A live replacement changes its record key. Preview decisions may be re-created while their record stays unchanged; forecast synchronization allocates records even at an unchanged simulated epoch. Neither a cache hit nor decision-object equality proves the retained record's currentness.

Sources: native source `selectedWeather` 1301; `wxAt` 1481; `syncWeather` 1498; `weatherFixtureEligibility` 1602; `weatherDecision` 1643; clock flags 870–874; `startWeather` 3479; `SalahClock.set` 3593. Normal loop sequencing at 3704 renders before its own painter, but independent captures/handoffs and asynchronous settlements are separate opportunities. A live-only exception leaves preview contracts unexamined.

## Countermeasure comparison

| Option | Benefit | Risk / disposition |
|---|---|---|
| Run the real full render from capture/reconciliation when M exists | Could publish B before sampling. | Adds a producer at a consumer boundary. `render` synchronizes forecast objects, updates prayer/UI/Moon state and may prefetch. Repeated callers can add easing and change cadence. `applyCloudState(atmosphere(M))` alone does not repaint the backing raster; atomic state/raster publication needs more coupling and reentrancy proof. Not preferred. |
| Retain consumed A during a bounded healthy full-model handoff | Preserves deck, readiness and one ordinary easing application. Uses the existing private decision/record/receipt, without a coverage cache or producer call. | Must independently validate A, require genuine M for the exception, and share the permit rule with final fences. Preferred below. |
| Skip reconciliation whenever M exists or B is fresh | Small patch. | Lets B lend time/permission to expired A; fails true expiry and late-publication requirements. Reject. |
| Fix only capture or only the live lane | Small immediate diff. | Painter/clear/final callers remain inconsistent; preview semantics stay wrong or uncovered. Reject as incomplete. |
| Clear raster but preserve readiness/hidden coverage for later easing | Avoids a later numeric snap. | Still creates an empty publication and split recovery state; conflicts with joined withdrawal. Reject. |

## Preferred narrow permit rule

Root should separately authorize a repair distinguishing **continued permission for consumed A** from **admission/publication of B**. It should not invoke `render`, `atmosphere`, `paint` or another producer from the guard.

Keep the current exact-record path for ordinary warm retention. Add only a healthy replacement handoff whose conditions all hold:

1. The active receipt is an existing `eligible-published` receipt from a real complete atmosphere. Uninitialised, withdrawn and superseded receipts cannot enter.
2. Private consumed A and selected candidate B are actual non-null records with different identities. This path does not invent recordless weather authority.
3. A's consumed target and lane match the current target/lane, with existing scene/config/clock invalidations intact. No latitude-only, label-only or generation-agnostic matching.
4. A remains eligible **under its own original contract at the current time**. Live A uses its own source-valid time, retrieval time, interval/code and target through the unchanged weather rule. B's ages, selection, publication time or fetch success cannot answer this.
5. B is eligible in the current decision. An unavailable candidate is not a healthy handoff.
6. Actual `model()` is non-null now. A `today` pointer, prior `_lastRender`, guessed day or fabricated M is insufficient. Put this model check only in the mismatch exception, not every ordinary same-record painter call.
7. Any consumed independent evidence required by the lane retains its own lease and target. For a bounded fix, unchanged independently eligible evidence is safer than enlarging evidence-replacement or recordless semantics.

A practical narrow design is to parameterize or factor the **existing per-record selection rule** so exactly the same live/preview logic can examine A without overwriting global `weather`, manufacturing a decision against substituted state, or duplicating a TTL policy. A pure record argument could default to current `weather` for existing calls. This is a design recommendation, not an authorized patch; exact extraction dependencies and lane behavior require tests.

If permitted, return A's **unchanged existing receipt** and leave coverage, targets, readiness, density, raster, wind and motion untouched. Do not publish a receipt carrying B's timestamps. The next ordinary successful `applyCloudState` consumes B, applies the original gain once and replaces A's receipt. QA continues to show consumed A separately from candidate B during the gap.

The bound is the earliest of A losing its own authority; genuine M disappearing while B differs; target/lane/scene invalidation; withdrawal; or the next ordinary complete publication. Live time is bounded by A's original deadlines. Preview lanes retain their existing preview time contract rather than acquiring an invented 15-minute deadline: their bound is scene/lane/model ownership and the ordinary publication lifecycle. Adding an arbitrary preview grace clock is a policy change for root, not an inferred repair detail.

### Final-publication requirement

The pure fence must require both the **exact captured receipt still being active** and the **same consumed-authority permit rule still holding at final publication**.

An A decode can finish while A is still the deliberately retained, eligible active publication. That is continuation of its owner, not revival. Once B is fully published, A expires, M disappears with replacement pending, or withdrawal/supersession occurs, captured A must fail. Never reissue or reactivate that receipt. Preserve cancellation, clear-successor publication, and checks before and after detail.

A candidate-only guard or “A is still fresh” test alone is insufficient: active receipt identity prevents former A returning after a newer publication even while A's raw times remain within bounds.

## Follow-up evidence obligations

These are obligations for a separately authorized repair, not executions or acceptance claims from this diagnosis.

| Evidence | Required discriminator |
|---|---|
| Exact positive paired order | Genuine M and admitted A/B from F01: capture-first retains A's original receipt/coverage; one ordinary render yields 0.9104 / 0.888 / 0.592. Render-first yields the same final vector. Readiness, density, population and phase remain coherent. |
| No extra producer/cadence | Repeated captures/guards before render do not call render/atmosphere/paint, advance easing, reseed, add requests or create a loop. A receipt identity and all its times stay unchanged. |
| Negative paired order | Change only real M availability: missing timetable plus fresh B still clears before capture. Cold and withdrawn consumers stay empty until ordinary complete publication. |
| A's own deadlines | Keep B fresh while A's source age and, separately, receipt age are 899999, 900000, 900001 and future. Retention follows A. Repeated B/C replacements cannot renew it. |
| Target/mode | Same coordinates/new generation, A→B→A, units/config, live→preview→live and explicit preview anchor transitions cannot retain/revive the old receipt. |
| Preview contracts | Explicit SIM same-record control; genuine ADVANCING/paused-preview forecast object turnover and normal gain; full-model handoff and no-model replacement. Do not add fake live metadata to forecasts to make tests pass. |
| Independent evidence | Expired/replaced direct-present leases cannot borrow model eligibility; existing fixture/live lane separation survives. |
| Async order | Pending A may finish only while A is permitted and active. B full publication, A expiry, missing M, target change or withdrawal rejects late A. No old decode blocks a clear successor. Include post-detail and same-byte reuse. |
| Failure/handoff | Actual failure, direct clear, hidden/resume and reduced-motion paths retain joined clearing when permission is absent. A throwing full-atmosphere producer cannot renew A; original expiry still clears it. |
| Delivery/review | Root rebuilds canonical outputs, explicitly rebinds affected source/generated evidence, reruns affected cohorts, obtains native healthy-refresh and no-model continuity evidence, then fresh exact-candidate review. |

The paired regression must fail against the frozen F01 candidate and pass after the narrow repair. Useful targeted negative controls remove the genuine-model condition, substitute B's age for A's, or drop captured-receipt identity; each must fail at its intended consumer assertion rather than setup.

## Escalation recommendation and return

Return F01 to root as a confirmed bounded product defect requiring explicit repair authorization. Prefer the consumed-A handoff rule, shared by reconciliation and pure final publication. Preserve the source freeze until root selects and authorizes the change. No broad prayer, Moon, science, acquisition, motion, provider or scheduling repair is justified.

Keep F01 open and retain the contrary probe after repair. Correct the healthy-refresh continuity claim using paired evidence; test totals do not discharge it. The appropriate response is a narrow owner/join countermeasure, affected generated/native requalification and fresh review of the new exact candidate. Root owns all consequential decisions and lifecycle state.

## Read set and limits

Read: audit-Andon skill; independent review and Appendix A; diagnosis stub; relevant native source for admission/selection, decision caching, forecast interpolation, real model, cloud state/guard, render/paint and clock/loop; native capture/publication/clear interfaces; R000B plan/contract; source/native fixture and companion boundaries.

Executed: only the exact authorized Appendix A Node probe with committed-input assertions. No extra mode sweep or proposed remedy was executed. Mode implications and the permit design are source-derived reasoning requiring follow-up verification. Native pixels, scheduling frequency, performance, correctness of a future patch, generated currentness and acceptance remain unjudged.
