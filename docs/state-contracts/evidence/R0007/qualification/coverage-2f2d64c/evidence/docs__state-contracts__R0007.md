# R0007 date-aware next-event implementation plan and state contract

> Agentic execution: use the approved completion-v2 commission, IMPLEMENTAUDIT ordinary full-run protocol, and inline test-first implementation with independently attributed review. This is the single source-linked plan/contract; the local run root owns execution state.

**Goal:** Select the earliest supported future event from admitted civil-day records and publish one coherent target across countdown, time, highlight and diagnostics.

**Architecture:** Native `src/native/index.html` owns the N06 derived selection. Bounded immutable candidate records reuse the existing R0008 unique-zone inverse. The existing N05 acquisition/adoption and dirty-render loop remain the sole producers and recovery path.

**Tech stack:** Existing inline JavaScript, Node source/consumer fixtures, Python deterministic builder and Playwright native qualification. No new product dependency.

**Spec:** [original issue #7](https://github.com/theislampill/salah_widget/issues/7), [ES07 extension](https://github.com/theislampill/salah_widget/issues/7#issuecomment-6700178193), and owner-forwarded `02_R0007_EXECUTE.md`, completion-v2, archive SHA256 `46a76bca2024402392a761d4d2b36534b00fe63762713d63dc287b01b7f87bb7`.

## Authority and currentness

Baseline: `eebba178172f96b3ffe5ab3845bc0fffd57c6e1b`, tree `6b94a3933f9d1381b1c2ceaab287c93afb215ecb`. Branch: `pro/r0007-explicit-next-event-state-20261106`.

The owner expressly authorizes isolated independent R0017, R0007 and R000B engineering concurrently. Required accepted merge order remains **R0017 corrective work → R0007 → R000B**. R0017 is not declared complete. This branch owns only R0007 source/tests/docs and generated consequences. Reconcile against latest accepted main, including preceding R0017, before final acceptance or merge; resolve actual conflicts and rerun affected qualification. Do not overwrite another owner's branch, claim its Windows resources or merge it. Local Linux test profiles/listeners are private to this worktree. Preserve durable candidate progress if integration is temporarily blocked.

Implementation, local commits, own-branch push, scoped evidence and non-closing `Implements #7` PR are commissioned. Exact head/base/tree merge approval remains the owner gate. Only after that approval: approved merge, normal deployment consequence, required public readbacks, certificate and deliberate issue closure.

## Global constraints

- Admitted Gregorian record identity is its civil date; bare HH:mm does not declare another prayer-day convention.
- Preserve equal/reordered clocks and Sunrise as an astronomical event.
- Use `epochForTzTime(y,mo,d,h,mi,zone)`; a gap/fold/unsupported inverse never becomes precise.
- Capture one current epoch. Select strictly future epochs; ties use declared `prayers` rank.
- No additional scheduler, fetch horizon, local prayer calculator, adhan, timezone package or inverse repair.
- Preserve current timetable/calendar, 325×530 geometry, ordinary wall arc/progress, Forenoon, opaque Moon and supported motion. Requalify affected consumers; do not replay untouched science campaigns.
- Edit authored source; generate root/offline through `python tools/build_native.py`; preserve frozen V1 and immutable scientific/vendor assets.
- Disposable fixtures only; no actual owner location, clipboard/profile/settings or live provider effects.

## Approaches and selected design

The commissioned design is a small date-aware selector at the model owner. A Fajr/Isha special case cannot handle arbitrary admitted reorderings; rejecting those records conflicts with ingress; a scheduler or alternate inverse expands scope. The selector is therefore the only compatible repair route.

`prayerEventCandidates(record, generation)` derives six frozen candidate records with key, source clock, civil date, source zone, minute, tie rank, generation, source-record object identity, exact epoch or unavailable reason. Candidates are ephemeral derived state; no persisted history or mutable status cache is introduced. The inverse's existing bounded day-profile cache remains its owner.

`selectPrayerEvent(currentRecord, nextRecord, nowEpoch, wallParts)` returns a frozen result with one of `current-record-unavailable`, `same-day-target`, `next-day-target`, `next-day-required`, `endpoint-unresolved`. It validates date/zone/generation eligibility and selects resolved future epochs by epoch then rank. Consult only the matching next civil day when needed. An unresolved candidate which could occur before the proposed target blocks precision.

For unresolved ordering, the existing inverse's `zoneDay` profile may provide conservative bounds only: ambiguous entries retain their full range; a gap retains each available neighboring supported-minute bound, with an absent day-edge neighbor leaving only that side unbounded; an unsupported profile has unknown bounds. Bounds can prove an uncertainty already elapsed or strictly later than a target. They never choose a fold alternative or synthesize an endpoint. A gap before the current epoch must not suppress an ordinary later event forever. No new timezone search or conversion algorithm is introduced.

`model()` derives compatibility fields from that selected result. `nextKey`, `nextTime`, `nextDateStr`, `nextZone`, `nextEpoch`, countdown, next row and substituted next-day marker have one target. With no supported target, these precise target fields are absent and no row/marker claims a known next event. The valid current timetable/calendar stays readable.

Current label/past rows remain the existing current-day wall schedule presentation, including Forenoon and the before-first Isha display convention; it is not observed previous-day history. Stable wall ordering makes the last declared rank current at an exact equal-clock boundary; strictly future ties select the first declared rank. Progress and the arc remain wall based. A supported next-day target supplies its own minute and key to the interval and marker substitution. If the endpoint is unavailable, a separately labelled decorative current-record wall interval remains finite and keeps the old ordinary visual behavior without becoming a precise target. Before the first current-day event, progress is explicitly `decorative-before-first` even when the next target is precise: preserve the existing last current-day clock minus 1440 convention, but expose no invented previous civil date or epoch. An unresolved previous endpoint is also decorative. Expose `prevMin`, `nextMin`, progress kind and selection state in the completed-render receipt. Guard zero/invalid spans explicitly. These diagnostic fields copy the completed model's captured instant and result; they never recompute selection or the current clock.

## Pre-implementation whole-owner census

The normative acceptance ledger is [evidence/R0007/acceptance-ledger.md](evidence/R0007/acceptance-ledger.md), committed with this plan revision. Complete its initial 7.01–7.16, A01–A09, ES07-01–15 and terminal-gate dispositions **before Task 1**. Task 3 updates that same ledger with final evidence. Historical acceptance is bounded to its recorded tree, inputs, platform and observer; new selector/model/render consumers require fresh affected qualification. Linux native runs establish Linux Chromium/Firefox observations only. They cannot silently replace a still-applicable Windows requirement; the ledger retains the exact historical platform binding or an explicit remaining gate.

Native acquisitions are written outside this checkout under `/workspace/scratch/8726e3e6def5/r0007-native/`, with a distinct immutable directory per attempt. The existing `tools/cp9/r0007_browser.py` recipe receives a rebound case packet, exact source-file hashes and root-issued capacity-one lease for **this private local Linux process only**, with matching `sourceCommit`. It does not assert a shared/Windows lease. Reviewed durable evidence is then copied to `docs/state-contracts/evidence/R0007`. Failed acquisitions remain evidence. The ledger names the required native cases, source controls and unchanged-owner reuse conditions.

## Review focus

1. A fold event with an apparently elapsed wall clock can still have a future possible epoch; the uncertainty test must use bounds and block false precision.
2. A past gap and an unresolved event later than a healthy earlier target must not blanket-disable useful supported output.
3. Equal clocks at an exact event must advance strictly and keep deterministic rank and finite decorative progress.
4. Missing/wrong-zone/wrong-day next data must not inherit today's source clock or create a highlighted target.
5. A late old-generation next-day completion and an A→B→A change cannot leak into the current selected envelope or frozen rendered frame.

## Task 1: selector and real source consumers

Files: modify `src/native/index.html`, `tests/r0007-countdown.cjs`; create `tests/prayer-next-event-state.test.cjs`; update scoped mutation anchors in `tests/rlgwo/prayer-browser-fixture.cjs` only if needed. Existing shared runtime adapters remain unchanged unless a proven in-scope dependency repair is required and attributed.

Interfaces: consume `prayers`, `prayerDayFields`, `epochForTzTime`, `zoneDay`, runtime generation and admitted current/next records. Produce `prayerEventCandidates`, `selectPrayerEvent`, and `M.selection` with legacy fields derived from its target. The actual renderer and completed-render receipt consume this same result.

Fixture input profile: the existing clock/request harnesses consume generated root `index.html`/`config.js`, including the builder's native star adapter. Authored-template overrides failed at setup before product assertions. Run the actual builder after source changes and prove model/render/inverse/adoption region equality before their generated-root consumer tests. Preserve the setup failures separately from the behavioral NF01 RED; do not rewrite shared R0017 adapters to add an uncommissioned input profile.

- [x] Run scoped baseline and retain the ordinary/reordered real-admission RED witness.
- [x] Write tests for Isha 00:31 on 08-09-2026 = `2026-09-08T00:31:00Z`, 91 minutes, and ordinary Fajr05:00 = 360 minutes; observe the intended baseline failure.
- [x] Add tie/polar, exact, Forenoon, unavailable/recovery, DST, fold/gap/unsupported ordering, month/year/leap, wall correction and generation controls from the complete ledger.
- [x] Implement the bounded selector and coherent model/render/receipt fields, retaining ordinary arc/progress assertions.
- [x] Adapt old model-specific mutant anchors to the new owner; preserve independent expected results and healthy positives. Verify all affected source suites, not only the new helper.
- [x] Execute required mechanism mutations through the actual consumer and retain each discriminating result.

## Task 2: generated and native qualification

Files: generated `index.html`/`offline.html`; necessary R0007 case packet/runner extensions under `tests/rlgwo` and `tools/cp9`; evidence under `docs/state-contracts/evidence/R0007`.

- [ ] Build in this disposable worktree, verify V1 and exact protected-source/generated identities.
- [ ] Bind the existing actual native observer and synthetic ingress to the exact candidate; retain native timers/rAF, fonts/layout and real rendered receipts.
- [ ] Qualify ordinary/reordered, unavailable/recovered/frozen12/24h, DST150/fall270/ordinary210 and scoped arc/geometry/preservation in available required Chromium/Firefox routes.
- [ ] Classify setup failures separately, retain failed attempts, and fix supported evaluator/fixture drift without relaxing product oracles.

## Task 3: whole-owner acceptance, independent review and publication

- [ ] Update the pre-implementation [whole-owner ledger](evidence/R0007/acceptance-ledger.md) for every original 7.01–7.16, applicable A01–A09 and ES07-01–15 row, with final source/surface bindings and historical limits.
- [ ] Update this source map, README precision/selection text and DESIGN next-event description.
- [ ] Bind independent exact-candidate source/consumer review and resolve actionable findings.
- [ ] Publish coherent source plus all generated changes and evidence to this branch; open/read back a non-closing ready PR and check current main/checks.
- [ ] Prepare exact post-merge deployment/public-source/consumer/certificate/closure sequence. Request the single exact-candidate merge decision only when all executable readiness work is accepted.

## Task 4: owner-approved integration and truthful closure

- [ ] After exact approval, recheck head/base/tree/reviews and merge the approved candidate.
- [ ] Verify actual main, configured deployment, served source and affected public consumer in fresh disposable contexts.
- [ ] Publish/read back the full certificate, deliberately close #7 as completed and verify the state.
- [ ] Close the ordinary audit lifecycle only after its actual terminal gates. A ready PR is not whole-RLGWO completion.

## Source-linked ownership map

| Catalogue | Owner / symbols | Boundary |
|---|---|---|
| N06 | Native candidate/selection/model/render/last-render receipt | This repair; one selected target and explicit unavailable/recovery |
| N02 | `simNow`, `epochForTzTime`, `zoneDay` | Existing clock/inverse; conservative order bounds do not authorize an endpoint |
| N04 | `admitPrayerRecord`, current generation | Existing ingress; equal/reordered inputs remain valid |
| N05 | `adoptPrayerBundle`, `prefetchPrayerDay`, `maintainPrayerDay`, dirty loop | Existing eligibility/recovery; no second fetch or timer |
| N07 | `selectCalendarDisplay`, `renderCalendarDates` | Valid current calendar independent of endpoint absence |
| N18 | `fitCn` and native fixed geometry | Existing layout; actual native crops required |

## Rollback and completion boundary

Rollback selector, consumers and generated artifacts coherently while retaining the failing regression and disclosing restored NF01. Leave converter/clock/protected science intact. No force-push or direct-main rescue. The continuation record and full acceptance matrix identify actual remaining gates; this plan is not an acceptance certificate.

## Enforced state contract and current source evidence

Engineering state: the initial source checkpoint passed278 controls; independent review then found two availability regressions. The corrected successor passes288 affected controls at the exact hashes in [review-successor-summary.json](evidence/R0007/source/review-successor-summary.json). Native, independent successor/final review, preceding accepted main, merge approval and delivery remain open. [Initial source execution receipts](evidence/R0007/source/source-summary.json) retain the baseline failures, NF01 RED, successful initial controls and their historical owner hashes. Source tests do not certify native pixels.

| Authoritative value | Producer and guard | Consumers / invalid transition |
|---|---|---|
| Admitted current/next record and generation | Existing `admitPrayerRecord`, `adoptPrayerBundle`, `maintainPrayerDay`; matching civil day/zone and live operation generation | Selector only derives from current-generation eligible records; late A→B→A responses cannot restore old target state. |
| Immutable candidate | `prayerEventCandidates`: key, original clock, actual record civil date/zone, declared rank, source object, generation, unique epoch or unavailable reason/bounds | Six ephemeral records per consulted day; no event history/cache or alternate clock. Bounds can exclude an uncertainty from consideration, never create an epoch. |
| Immutable selection | `selectPrayerEvent`: one captured now, eligible current day, strict future epoch then rank; matching civil successor only when needed | `model` derives every next key/time/date/zone/epoch alias, countdown and marker from `selection.target`. No separate Fajr policy survives. |
| Wall presentation interval | `model`: last elapsed current-record wall clock and selected target minute, or explicit decorative fallback | Bar/arc/current label remain wall based. Before-first or unresolved prior endpoint exposes no observed predecessor date/epoch. Zero/invalid spans use finite decorative zero. |
| Completed-render receipt | `render` copies the model's accepted instant, selection state/target and progress kind | `_lastRender` never recalculates a next label/endpoint or rereads the clock for its `sim` value. Actual native observer copies this receipt. |

| Selection state | Entry condition | Actual presentation |
|---|---|---|
| `current-record-unavailable` | Current day/zone/generation ineligible | `model` is unavailable; existing full prayer withdrawal remains separate from weather/calendar independence. |
| `same-day-target` | Earliest strictly future unique current-day epoch, no potentially earlier unresolved candidate | Selected source clock/key/date/zone/epoch drives countdown, row and marker. |
| `next-day-target` | No eligible future current-day event; matching successor has a supported earliest epoch | Same envelope; selected next-day clock/key also supplies the boundary interval and marker position. |
| `next-day-required` | Current day exhausted, matching valid successor absent | No precise target or next highlight; current timetable/calendar remain; central em dash and `Countdown unavailable`. |
| `endpoint-unresolved` | A relevant gap/fold/unsupported inverse can precede the proposed target, or no supported future endpoint | Same endpoint-only unavailable presentation; a bounded elapsed or later uncertainty does not blanket-disable a healthy earlier target. |

A matching late next-day adoption transitions unavailable→supported through the existing dirty loop, including frozen12/24h. Both adoption and request finalization can mark that loop dirty. Removing only the adoption hook survives as an explicit redundancy control. The complete missing-next-wakeup mutation removes both next-day wakeups, retains successful actual adoption, and fails the first frozen rendered-target check. Product redundancy is preserved.

The current invoked source cohort contains288 passing tests: selector44, countdown23, inverse/timezone37, adoption16, day-return6, admission62, clock44, row status27, marker25 and arc sampling4. The old unavailable-tomorrow row test is reconciled to ES07: it now expects no claimed next event while retaining all current rows. Old projection cost changes from one to six bounded candidate checks per warm same-day model, with the no-profile-rebuild invariant retained. The +24h mutant is rebound to the new candidate owner, and the native fixture uses that same uniquely anchored mechanism.

Independent review of `d641741df1397659da6ef817fa41aa975f7f3930` returned GAP-REVISE for SRC-01 (lost one-sided day-edge gap bounds) and SRC-02 (unpadded Gregorian years). The successor keeps each justified bound while the gap endpoint remains nonfinite, and matches admission's four-digit civil date in candidate eligibility and the captured model/receipt. Actual admitted Santiago and Nuuk controls prove Sunrise240 and Fajr30 respectively. Years0001/0099/0999 retain Fajr210 and a small-year next-day selection; years1000/2026 and ordinary zone companions stay healthy. The ten controls reproduce six behavior failures on the reviewed generated source and pass on the successor. The local test fixture's initially unpadded composite date caused earlier admission-only failures; those attempts are retained separately and are not credited as behavioral RED. No clock, inverse or admission owner was changed.

Protected owners remain unchanged: inverse/clock, admission/adoption/dirty-loop, calendar, physical arc/solar geometry, Moon/motion/scientific owners and V1. The generated Moon build manifest changes only its authored-native-source digest. Actual source/generated region parity and V1 verification are recorded; neither is native or delivery acceptance.

## Qualification mechanism and review checkpoint

Independent source review accepted the corrected source at `5e946fe18a31750cf528bd58210ce79182dcf1e1` / tree `6e9eced1194d2463f5090fcdb086e771e1100916`, resolving SRC-01/SRC-02 and independently reproducing the288-test cohort, V1 and protected/generated boundaries. Its [report](evidence/R0007/review/candidate-source-successor-5e946fe.md) excludes subsequent qualification edits and actual native acceptance. A small [Git bundle](evidence/R0007/source/r0007-source-history.bundle), with its [manifest](evidence/R0007/source/r0007-source-history.json), preserves the exact reviewed local commit objects against the accepted base when connector publication later reanchors an identical tree under a different commit.

The qualification launcher owns one immutable candidate binding and serial private-process frontier. Each case moves from planned to producer-started to terminal observed or unattempted. Healthy and intended-mutant source credit require matching terminal summary/trace identity, verified selected executable and source/fixture hashes, an actual completed-render receipt, intact capture artifacts, and the original assertion/exit rules. Missing cleanup stops every later launch. An explicit browser-launch/context failure with established cleanup leaves remaining same-engine cases unattempted while the other engine remains eligible. No skipped cell permits aggregate success.

Capture associations are separate: absent setup/artifacts, malformed binding, ordinal mismatch, eventual-state-only, or recorded pending independent review. No automatic state accepts first-visible pixels. Every first-capture mismatch is retained while subsequent acquisition continues; a capture name does not waive or abort its association. The actual requested browser executable path and hash are bound before launch, passed to that launch, and checked afterward; existing sandbox options remain unchanged. Nineteen focused pure qualification controls and five existing browser-selector controls pass, with original failing controls retained in [qualification](evidence/R0007/qualification/final-verification.json). These are checker tests, not native observations.

The three healthy frozen recovery recipes and the complete next-day-wakeup mutant hold the response until the authored optional font stylesheet has an actual LINK load/error receipt, its media activation is applied after load, read-only layout exposes pending font work, the actual `FontFaceSet.ready` promise settles, actual relevant font completion events have returned, and the existing loop's dirty flag clears. Terminal stylesheet/font failures retain native fallback behavior. This bounds the known unrelated font-finalization wakeup without calling render, advancing time, waiting for the expected target or replacing the scheduler. Expected product values, ingress records and deadlines are unchanged. The subsequent250ms observation remains eventual-state acquisition; all-render traces and actual video still must establish earliest eligible/visible recovery independently.

The earlier font-status-only barrier at `3fa33a3` admitted an empty loaded font set while the nonblocking stylesheet was pending. The [QUAL-01 review](evidence/R0007/review/combined-pre-native-3fa33a3.md) and original failing predicate controls are retained. Its incidental exposure to an unrelated reviewer summary is disclosed in that report; it is not presented as an unqualified cold final review. The corrected predicate controls are browser-free setup checks and supply no native recovery or pixel acceptance.

The fresh [b20e3aa review](evidence/R0007/review/qualification-b20e3aa.md) additionally identified a spec-permitted ordering in which readiness precedes the product's set-wide completion callback. Retrieved engine implementations supply contrary evidence for incidence; no targeted native reproduction is claimed. The bounded [audit-Andon diagnosis](evidence/R0007/review/font-settlement-andon-b20e3aa.md) recommends direct event observation. The R0007-only pre-document observer records actual face identity and terminal type, then credits a receipt in a captured native zero-delay task after event dispatch. That one-shot observer task neither calls product rendering nor wakes the product; its receipts are exported separately from the product timer ledger in success and failure traces. Failed faces need `loadingerror`, successful faces need `loadingdone`, and admission also requires zero pending observer receipts. Missing receipts or observed removal/restart/descriptor changes fail diagnostically under the explicit static authored-font lifecycle; no timing-only or cached-face exception is inferred.

Sixteen focused setup controls pass, including both event/readiness orders, mixed success/error, deferred dispatch, replacement identity and optional-font fallback. Four predecessor counterexamples and eleven positives are retained. The launcher also verifies every bound source/recipe against an actual regular Git blob in the captured commit during the same byte-hash read. Ignored recipes and `assume-unchanged` content cannot gain committed provenance merely from a clean status. Twenty-four pure qualification/driver/real-disposable-Git controls pass; the original failures are retained. None supplies native pixels or whole-owner acceptance.

## Publication transport checkpoint

The first hosted materialization run42754815319 reproduced the exact b20e3aa target tree, then its first `offline.html` Git Database upload returned HTTP422. No blob upload was verified and the job performed no ref update. The [original artifact and receipt](evidence/R0007/publication/materialization-42754815319/receipt.json) retain this failure. The response body was not retained by that helper, so the API-side cause remains unknown. A smaller byte-preserving UTF-8 request and bounded error diagnostics are under separate review; no failed upload is counted as publication or native qualification. The owned remote seed contains the coherent accepted application baseline and only four transport files until an exact complete candidate tree is finalized.
