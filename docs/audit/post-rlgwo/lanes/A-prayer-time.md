> **Lane working paper.** This is supporting detail produced by one census lane of the post-RLGWO audit at baseline `363c3e53`. It is superseded by [IMPLICIT_STATES.md](../../../../IMPLICIT_STATES.md), [REPORT.md](../REPORT.md), [CROSSWALK.md](../CROSSWALK.md) and [FINDINGS.md](../FINDINGS.md) wherever they differ; the integrator's corrections are listed in REPORT.md. Probe paths `probes/<lane>/` refer to [../probes/](../probes/README.md).

# Lane A — prayer, time and calendar (application core)

Baseline: main `363c3e53` (worktree `post-rlgwo-audit`). Historical reference: original audit at `f71fef6c` (2026-10-21).
Authored owner: `src/native/index.html` (cited as `S:<line>`). Generated counterpart: root `index.html` (`G:<line>`).
Parity: every audited function (39 symbols plus `window.SalahClock`) is byte-identical between the two (probe `probes/A/parity.cjs`).
Line numbers are approximate baseline anchors. Probe outputs are in `probes/A/probe-results.json` and `probes/A/probe-results.txt`. Test logs are in `probes/A/logs/`.

Timing context: R0001, R0002, R0004–R000A, R0019 and R0020 were closed before `f71fef6c` (2026-10-09 to 10-14), so their code was already part of the audited baseline. After the audit, only the following touched this lane:
- R0007: PR #73, merge `dbf3370f`; font gate `58fc4afc`/`ec69edf8`.
- R0003: PR #79, merge `a4766a1b`, `a06957c6`.
- R000D: PR #74, merge `645b53cc`, `ba0851ae`.
- R000B (`ea9f8300`) and R0026 (`fbd08aa1`), both incidental.
- R0017: instruments (`7214a2c8`).

---

## 1. Machine census

Enforcement status is given as **Doc / Impl / Verif**.

### N01 — Configuration resolution, boot and apply generation (incl. R0003 effect classifier)

- **Scope / decision.** Decides how much a proposed configuration may invalidate, from nothing to everything. Also decides when the first scene and the provider work start.
- **Sources.**
  - `S:677-761`: `q`, live `let` bindings, `bindConfig` (`S:683`), resolver fallback.
  - `S:697-741`: `CONFIG_EFFECTS`, `sameConfigEvidence`, `classifyConfigChange` (`G:4250`).
  - `S:3711-3760`: `buildSceneOnce`, `resetForNewLocation`, `applyConfig` (`G:7162`).
  - `S:3779-3849`: `boot` (`G:7212`).
  - `S:4122-4140`: `_resetLocal` (reset intent).
- **State dimensions.**
  - `CONFIG` (accepted) vs live scalars (`lat, lon, tz, label, method, school, fmt24, units, datefmtStr, LPOLL`).
  - `_cacheTz`.
  - `_cfgMode` ∈ {bare, hardcoded, local, preferLocal}.
  - `_needsDetect`, `_autoDetectStatus` ∈ {idle, pending, ok, failed}.
  - `_sceneBuilt`.
  - `_runtimeGeneration` (int).
  - Change path ∈ {none, presentation, broad}.
  - Boot phase: {scene-begun, invalid-sim, awaiting-detect, first-render, yielded (2×rAF + MessageChannel), providers-started, loop-started}.
- **Events and transitions.**

| Event | Guard | Effect |
|---|---|---|
| script eval | `window.SalahConfig` present | `resolve` → `bindConfig`; otherwise legacy hash parse (`S:746-760`) |
| `applyConfig(cfg)` | `classifyConfigChange(CONFIG,cfg,{reset})` (`S:3734`) | before any mutation; save/persist publication (`S:3735-3739`) |
| path `none` | all classified keys equal | `CONFIG=cfg` only (`S:3740`) |
| path `presentation` | only label/time/datefmt/appearance differ | rebinds 4 scalars + `setLocLabel` + `_renderDirty`; no generation, `bindConfig`, reset or provider work (`S:3741-3748`) |
| path `broad` | any target/calculation/tz/units/lp/seed/evidence/provenance/unknown key differs, or explicit Reset, or no accepted config | `beginRuntimeGeneration` → `bindConfig` → `resetForNewLocation` → `startWeather` → `await loadPrayerData` → generation recheck → `startRenderLoop` (`S:3750-3759`) |
| boot awaits (detect, yield, prayer) | `generation!==_runtimeGeneration` | abandon continuation (`S:3796, 3841, 3847`) |
| stale/duplicate apply | A→B→A | three generations; the old continuation exits at its recheck |

- **Guards.** The classifier is pure and frozen. An unknown key or unknown evidence field fails closed to `broad` (`S:713, 729`).
- **Actors.** URL hash, settings panel close-save (`S:4103`), Reset (`S:4136`), coarse detect (config lane).
- **Effects.** Generation bump cancels all four request slots (N03). `resetForNewLocation` withdraws prayer and weather presentation and begins a new sky scene.
- **Invariants.** A display-only edit preserves the provider-adopted `tz`, `_cacheTz`, request owners, throttles and sky. Reset is always broad.
- **Failure and recovery.**
  - An incomplete target renders unavailable (`S:3754`).
  - A failed coarse detect opens settings and starts the loop (`S:3804-3808`).
  - Bare mode shows "Add lat & lon" and does not start the loop.
- **Risks.**
  - The presentation path relies on the loop for its repaint (`_renderDirty`). Before the loop starts, the boot or loader render covers it.
  - `units`, `lp` and `seed` stay broad by owner decisions D3/D4 (`docs/state-contracts/R0003.md:36-37`).
- **Enforcement.** Doc: state contract `docs/state-contracts/R0003.md` + comments / Impl: classifier explicit and enforced; boot phase implicit / Verif: unit + mutation (`tests/config-effects-state.test.cjs` 35/35, `config-effects-mutations.test.cjs` 21/21, `r0003-ownership.test.cjs` 24/24, `native-appearance-currentness.test.cjs` 15/15, all run here), native local headless observation and independent delivery review per the R0003 certificate (issue #3).
- **Tests.** The R0003 suites assert classification per key, no requests or generation change on the presentation path, and broad behaviour for genuine change. Probe P4 reproduces this: label+time change leaves requests at 2 and generation at 0; an equal config does the same; Reset gives generation 1 and +1 request.
- **Observed facts.** The classification happens before the save mutation of `source`/`savedAt`. The presentation path never calls `bindConfig`. Reset passes `{reset:true}`.
- **Hypotheses.** If the document is hidden at first load, boot's double-rAF yield (`S:3832-3840`) defers the first network prayer acquisition until it becomes visible. This is by design ("paint opportunity") and is not measured.
- **Unknowns.**
  - Whether the builder or settings can emit keys outside `CONFIG_EFFECTS` in ordinary use (config lane).
  - Browser rAF throttling for offscreen cross-origin iframes.

### N02 — Civil/simulation clock, timezone inverse, invalid-scene recovery, diagnostic clock control

- **Sources.**
  - `S:924-1043`: `_RAFNOW`, `TIMESCALE/ADVANCING/FOLLOW_WALL_CLOCK/_clockPreview`, `partsInTz` (`S:935`), `utcFields`, `zoneFormatter`, `projectInZone`, `zoneDay` (4-entry Map, `S:971-991`), `epochForTzTime` (`S:992`), `initSim` (`S:999`), `simNow` (`S:1011`, `G:4540`), `simulationReady` + `_simHidden` (`S:1020-1035`), `tomorrowStr`.
  - `S:3766-3777`: `window.SalahClock.set` (`G:7199`).
  - No change since `f71fef6c` in these functions (diff `f71fef6c..363c3e53`).
- **State dimensions.**
  - Clock mode ∈ {live-wall (`FOLLOW_WALL_CLOCK`), frozen explicit (`TIMESCALE=0`), advancing explicit, runtime preview (`_clockPreview`)}.
  - Anchor `(_simBase, _rafT0, _simTz)`.
  - Validity `(_simValid, _simInvalidTz)`.
  - Formatter caches.
  - `_zoneDays` profile LRU (≤4).
  - `_simHidden` visibility memo.
- **Events and transitions.**

| Event | Effect |
|---|---|
| live mode | `simNow()=Date.now()`; follows wall corrections (R0020) |
| explicit mode, first call or `_simTz!==tz` | `initSim()` re-anchors to `simTime` on today's date in `tz` **or to `Date.now()`** and resets `_rafT0` |
| gap/fold for the `simTime` | `_simValid=false`, sticky until `tz` changes; `simulationReady` hides 8 layers and shows "SIM unavailable" |
| `SalahClock.set({rate,utcMs,live})` | validates, then sets mode, anchors `_simTz=tz`, invalidates sky/preview, `maintainPrayerDay`, `render` |
| `tz` change after `SalahClock.set` preview | `simNow` sees `_simTz!==tz` → `initSim()` → **preview `utcMs` discarded and replaced by wall now; `_clockPreview` stays true** (finding A-F02) |

- **Invariants.**
  - One epoch feeds prayer, calendar, sky and moon.
  - Deadlines use `_RAFNOW` (monotonic).
  - A gap or fold time is never shifted.
- **Failure.** `partsInTz` falls back silently to the host-local zone when the `Intl` formatter throws (`S:943-946`). This is reachable with an invalid `tz` (finding A-F01: the probe returned host-local hour 08 for 12:00Z).
- **Enforcement.** Doc: comments; issue contracts R0008/R0020 (no state-contract file) / Impl: partly explicit / Verif: unit tests (`r0020-clock.cjs` 44/44, `r0008-timezone.cjs` 37/37, `r0007-countdown.cjs` 23/23, run here). There are no negative controls for "preview survives zone adoption".
- **Observed facts.** Probe P2:
  - `SalahClock.set({utcMs:2026-12-25T03:00Z,rate:0})` with hint New York, then a Tokyo adoption, gives `simNow`=2026-09-07T12:00Z (wall).
  - `_clockPreview` stays true.
- **Hypotheses.** An advancing `timeScale` preview restarts from `simTime` whenever the zone is adopted. This is intended per the comment at `S:1010` ("re-anchor when the timezone settles").
- **Unknowns.**
  - Cross-browser `Intl` historical offsets.
  - Cold `zoneDay` cost (4,321 projections) in native timing.

### N03 — Request ownership and bounded attempt leases

- **Sources.**
  - `S:1067-1112`: `cacheKey`, `_requestSlots` {current, prefetch, weather, radar}, `beginRequest` (`G:4602`), `requestEligible`, `finishRequest`, `beginAttempt`, `attemptEligible`, `finishAttempt`, `beginRuntimeGeneration`.
  - `S:1128-1164`: `fetchTimings` (3 attempts, 10 s deadline, 900·n ms backoff).
  - `S:1194-1197`: `prayerResultEligible`.
- **State dimensions.** Slot per kind (null or op); op `{generation, operationId, captured lat/lon/method/school/units/requestZone/cacheKey, attempt}`; attempt `{attemptId, controller, deadlineAt, timer, cancel, expired}`; `prayerAttempts`; `completedAttempt`.
- **Transitions.**
  - `beginRequest` claims only an empty slot of its own kind.
  - An attempt is eligible only if the op is current, the attempt identity is exact, it is not expired, and `_RAFNOW()<deadline`.
  - A generation change clears the slots and then aborts the attempts.
  - An old `finally` cannot release a successor's slot.
- **Changes since audit.** Prayer side unchanged. The weather and radar retry spacing moved to the elapsed clock (NEW-A-02).
- **Risks.** Backoff `sleep` is not cancellable but rechecks eligibility (`S:1136`).
- **Enforcement.** Doc: comments + R0003 contract table (`R0003.md:60`) / Impl: explicit and enforced / Verif: unit (`r0003-ownership` 24/24, `r0005-adoption` 16/16, `r0006-recovery` 18/18, `r0004-currentness-controls` 3/3, run here), independent review (R0003 cert).
- **Observed facts.** No defect found.
- **Unknowns.** Native fetch abort and body-settlement timing.

### N04 — Current prayer acquisition, admission/cache, adopted-zone reconciliation

- **Sources.**
  - `S:1048-1066`: `admitPrayerRecord`.
  - `S:1114-1127`: `readPrayerCache`, `loadCache`, `saveCache` (single envelope per `cacheKey`).
  - `S:1170-1176`: `prayerCivilDay`.
  - `S:1184-1193`: `prayerRecordReady` (WeakMap memo).
  - `S:1200-1223`: `adoptPrayerBundle` (`G:4729`).
  - `S:3669-3708`: `loadPrayerData` (`G:7102`).
  - Unchanged since audit.
- **States.** No current; cache candidate; cache current; network candidate; zone adopted / day re-derived; one corrected-day request; current admitted; unavailable; superseded.
- **Transitions.**
  - A cache hit sets `tz=cached.timezone` before the day filter (`S:3676`).
  - A network result sets `tz=data.meta.timezone` (`S:3691, 3697`).
  - If the civil day differs after adoption, one corrected request is made within the same 3-attempt budget (`S:3694-3695`).
  - `adoptPrayerBundle` publishes `today` only for the exact current day. Otherwise it sets `tomorrow` (same zone), or does nothing.
- **Guards.** Strict clocks (Sunset optional), exact Gregorian date and its padded string, a valid IANA `meta.timezone`, and malformed AH → `hijri:null`.
- **Invariants.**
  - No wrong-day, wrong-zone or old-generation record becomes current.
  - Equal or reordered clocks are admissible.
- **Failure.** If `prayerCivilDay()` returns `null` (invalid live `tz`), the loader requests `/timings/null`. Admission rejects every response (`dateStr` is not a string). `tz` is never corrected from provider metadata, and `maintainPrayerDay` returns early on `!day`, so it is never retried (finding A-F01, probe P1).
- **Enforcement.** Doc: comments; issue contracts R0002/R0004/R0005 / Impl: partly explicit / Verif: unit (`r0002-admission` 62/62, `r0004-boot-day` 8/8, `r0005-day-return` 6/6, `hotfix-prayer-weather` 21/21, run here).
- **Observed facts.**
  - `tz` is written by 4 sites (NEW-A-03).
  - The cache holds one day per key, so a backward civil-day correction finds no cache for the earlier day.
- **Unknowns.**
  - Provider behaviour for `timings/null` (not contacted).
  - Whether the builder rejects invalid zones (config lane).

### N05 — Prayer day rollover, next-day prefetch, cooldown, stale state

- **Sources.**
  - `S:1166-1169`: `_prayerCooldown`, `_renderDirty`.
  - `S:1177-1183`: `prayerNextDay`.
  - `S:1224-1260`: `beginPrayerRequest`, `finishPrayerRequest`, `prefetchPrayerDay`, `maintainPrayerDay` (`G:4775`).
  - `S:2271-2274`: `today/tomorrow/lastDate/fetchingTomorrow`, `_prayerStale`, `_rolloverBusy`, `_rolloverNextTry`, `_ROLLOVER_RETRY_MS=60000`.
  - Unchanged since audit.
- **State dimensions.**
  - Current region {ready, stale, absent} × recovery {idle, owned, cooldown(day, nextTry)}.
  - Prefetch region {idle, owned, cooldown, tomorrow-ready}.
  - Mirror flags `fetchingTomorrow`, `_rolloverBusy` and `_rolloverNextTry`, which shadow the slots and cooldowns and are read only by `qaState().rolloverPendingMs` (`S:3577`).
- **Transitions** (per visible loop frame and per render):
  - Promote an exact `tomorrow`, else adopt the exact cache.
  - Drop a non-matching `tomorrow`.
  - Recompute `_prayerStale`.
  - Start `loadPrayerData` if not ready and the current slot is free; cooldown 60 s elapsed per day.
  - The prefetch starts from `render()` (`S:3498`).
- **Invariants.**
  - Civil midnight is an ownership event.
  - A next-day record cannot change the present zone (`S:1203`).
- **Observed facts.** Probe P5: with a yesterday record, `_prayerStale=true` and `model()===null`, `.c[data-stale]` stays `""`, and the AH footer shows the "stale" tag. `data-stale="prayer"` (CSS `S:458`) is written only on the model-present branch (`S:3518`), which is unreachable while stale (finding A-F04).
- **Enforcement.** Doc: comments / Impl: implicit (parallel regions encoded by slots plus mirror flags) / Verif: unit (`r0005-day-return`, `r0006-recovery`, `prayer-next-event-state` recovery cases).
- **Hypotheses.** A prefetch whose provider zone differs from `tz` is rejected and retried every 60 s for the page lifetime (`S:1203, 1228`). This is speculative; a stable provider zone makes it unlikely.
- **Unknowns.** Native multi-day clock jumps.

### N06 — Prayer model, explicit next-event selection (R0007), countdown and DOM publication

- **Sources.**
  - `S:2286-2291`: `prayerDayFields`.
  - `S:2294-2319`: `prayerEventCandidates`.
  - `S:2320-2351`: `selectPrayerEvent` (`G:5752`).
  - `S:2352-2394`: `model` (`G:5784`).
  - `S:2397-2500`: `drawArc` markers.
  - `S:3477-3529`: `withdrawPrayerPresentation`, `render`, `_lastRender`.
- **Selection state** (frozen result): `current-record-unavailable` | `same-day-target` | `next-day-target` | `next-day-required` | `endpoint-unresolved`.
- **Progress kind:** `wall-interval` | `decorative-endpoint-unavailable` | `decorative-before-first` | `decorative-previous-unresolved` | `decorative-degenerate`.
- **Transitions.**
  - One captured `nowEpoch`.
  - Eligible current day (date, zone and generation) → earliest strictly future unique epoch, then declared rank.
  - Only the matching civil successor is consulted when needed.
  - A gap, fold or unsupported candidate that could precede the target blocks precision (bounds only from `zoneDay`).
  - `model` derives `nextKey`/`nextTime`/`nextDateStr`/`nextZone`/`nextEpoch`/countdown/marker from `selection.target`.
  - `render` publishes the texts, rows, arc and receipt.
- **Invariants.**
  - One target drives the countdown, the row highlight, the marker and the receipt.
  - Without a target, `.nt`="—" and "Countdown unavailable" (`showError`, `S:2278`).
  - The receipt copies the model's instant and does not recompute.
- **Observed facts.** Probe P3 at 23:00 UTC:
  - Reordered today Isha 00:30 / tomorrow Isha 00:31 → `next-day-target` Isha 00:31, 91 min.
  - Ordinary control → Fajr 360 min.
  - NF01 is fixed.
- **Residual.**
  - `warmEnd` and `needTomorrow` are produced but have no consumer.
  - `drawArc` reads method params from the global `today`, not from the selected target's record (`S:2476`). A next-day marker substitution uses today's method angle and today's solar range (speculative, minor).
- **Enforcement.** Doc: state contract `docs/state-contracts/R0007.md` + acceptance ledger / Impl: explicit and enforced / Verif: unit + mutation (`prayer-next-event-state.test.cjs` 44/44 incl. ES07 mutants; `r0018-prayer-row-status` 27/27; `r000a-markers` 25/25; run here), independent source review, native hosted cohort.
- **Verification caveat.** The final hosted Firefox run 42953929662 concluded **FAILURE/PARTIAL**: 2 healthy cells were `OBSERVATION_NOT_ACCEPTED` and 3 mutants were `MUTANT_NOT_QUALIFIED`. The certificate accepts those rows by cross-run reuse (`R0007.md:230, 240`; issue #7 certificate).
- **Unknowns.**
  - Native pixel acceptance on Windows.
  - Behaviour under real provider reordering incidence.

### N07 — Calendar publication, Hijri provenance/rollover, date disclosure

- **Sources.**
  - `S:830-850`: `calendarFields`, `fmtDate`, `escHtml`.
  - `S:854-917`: `_lastDateTruth`, `calendarRecordDay`, `selectCalendarDisplay` (`G:4390`), `bindDateDisclosure`, `renderCalendarDates`.
  - Markup and dialog CSS (`S:436-445`).
  - Changes since audit: four-digit year padding in `prayerDayFields` (R0007 SRC-02) and dialog fonts via `var(--font-*)`.
- **States.** Unavailable; before Maghrib (current AH); after Maghrib with next AH applied; after Maghrib with next unavailable ("Sunset date update unavailable"); preview day; dialog {closed, open}; initiator focus held.
- **Guards.**
  - `currentContext` requires the loaded day = requested day and the zone = `tz`.
  - Next AH only from the admitted matching `tomorrow`.
  - No arithmetic roll-forward.
  - Provenance: `calendarSource:"Aladhan"` and `hijriMethod` from the record (R0009).
- **Enforcement.** Doc: comments; issue contracts R0001/R0009/R0019 / Impl: implicit (derived projection plus a one-value receipt) / Verif: unit. The **three date harnesses are each red at baseline**: `r0001-date-sinks` 12P/1F, `r0009-date-selection` 21P/1F, `r0019-date-disclosure` 15P/1F, all with `el.style.getPropertyValue is not a function`, on the no-model and missing-date cases (finding A-F03).
- **Observed facts.** The calendar code is unchanged in logic. The failing cases are exactly the no-model/unavailable presentation paths. Since R000B, those paths call `withdrawWeatherEffects` → `paintLunarOptic` (`S:3491` → `S:2722` → `S:3004-3007`).
- **Unknowns.** Native modal focus and footer pixels.

### N18 — Countdown font readiness, rail sampling and geometry-fit cache

- **Sources.**
  - `S:3374-3402`: `_cnFit`, `_cnFontLoads`, `cnRelevantFont`, `cnFontChanged`, `cnFontSignature`, FontFaceSet listeners.
  - `S:3403-3447`: `fitCn` (`G:6836`).
  - Font gate: see NEW-A-01.
- **State.**
  - Fit key = `currentKey|round(sunrise)|round(sunset)|faceStatusSignature`.
  - `fitCn._arcSamples` keyed by the exact rail `d`.
  - Measurement context.
- **Transitions.**
  - A relevant face settles (success or failure) → `cnFontChanged` (`_cnFit=""` and dirty).
  - An equal key returns early.
  - A new key measures and fits.
- **Risks (NH01, unchanged).** The key omits the rail `d`, noon and declination. `resetForNewLocation` (`S:3717-3726`) does not clear `_cnFit`, so a broad location change with an equal key reuses the prior fit. Magnitude is unmeasured.
- **Enforcement.** Doc: comments + R0007 font section / Impl: implicit cache; readiness partly explicit / Verif: unit for the font gate only (`r0007-font-gate` 5/5, `r0007-font-use` 3/3, `r0007-async-observation` 5/5, `r0007-recovery-precondition` 21/21). No fit-key test.
- **Unknowns.** Native text and rail collision under an equal key.

### N19 — Singleton render loop, visibility, provider cadence, motion lifecycle

- **Sources.**
  - `S:3648`: `_loopStarted`.
  - `S:3855-3898`: `startRenderLoop` (`G:7288`); `loop`, `start`, `stop`, `setVis`, IntersectionObserver.
  - Since the audit: `reconcileCloudPublication()` per frame (`S:3880`, R000B).
- **State.**
  - `_loopStarted`.
  - Closure `_raf`, `_onScreen`, `_lastSec` (seeded from `_lastRender`), `_lastWx`, `_lastCloud`.
  - Motion counters.
- **Per-frame order.**
  1. Readiness.
  2. `maintainPrayerDay`.
  3. Weather and radar opportunity every 30 s elapsed (not while advancing).
  4. Render on a sim-second change or dirty.
  5. Cloud reconcile and paint.
  6. Preview present.
  7. Reschedule.
- **Invariants.**
  - One loop and one listener set per document.
  - Hidden time does not jump clouds.
  - Retry clocks are independent of the simulation rate.
- **Risks (NH02, unchanged).** There is no `try/finally`. A throw after `_raf` was consumed leaves `_raf` non-null, so `start()` is a no-op until a visibility or intersection change. The per-frame body grew since the audit.
- **Enforcement.** Doc: comments / Impl: implicit / Verif: unit (`r001d-lifecycle` 1/1 and `r0025-lifecycle` 1/1 as script-level tests; `r0020-clock` loop boundary cases).
- **Unknowns.** Real-browser rAF suspension and exception recovery.

### NEW-A-01 — Optional web-typography activation gate (R0007)

- **Sources.**
  - `S:7-26`: `#webfont-css` print→all, fallback `--font-*`, `html.webfonts`.
  - `S:3340-3368`: `WEBFONT_FACES`, `_webfontsRequested`, `requestWebfonts`, link load hook.
- **States.** not-requested → requested-pending → applied (`html.webfonts`), or failed-closed (rejected or empty load; no retry for the page lifetime). A stylesheet that never loads stays in not-requested.
- **Transitions.**
  - The stylesheet reaches `media==="all"` (now, or on its `load` event).
  - `fonts.load` runs for 3 faces.
  - `Promise.all`: every set non-empty → add the class + `cnFontChanged`. Otherwise no effect.
- **Invariants.**
  - It never blocks prayer or sky.
  - One-shot.
  - The fit is invalidated on application.
- **Enforcement.** Doc: comments + `R0007.md:208-238` / Impl: explicit one-shot / Verif: unit 5/5 + 3/3, hosted Firefox cohort with 0 text-loss frames in 20 cells (one run), local Windows recordings.
- **Unknowns.** On-demand non-Latin subsets can still blank briefly (disclosed at `R0007.md:238`).

### NEW-A-02 — Weather/radar retry spacing clock (R000D; clock-ownership side only)

- **Sources.** `S:1264-1279`: `_WX_RETRY`, `_wxRetry`, `retryClockDomain`, `retryGate`, `retryDiagnostics`. Reset in `resetForNewLocation` (`S:3720`).
- **State.**
  - `_wxRetry[kind]` = null or `{startedAt: elapsed, clock}`.
  - Gate ∈ {suppressed-by-mode, target-ineligible, active-owned-attempt, fresh-data-satisfied, cooldown, eligible}.
- **Invariant.** Spacing uses `_RAFNOW` and is immune to wall corrections. The `Date.now` fallback is disclosed as degraded.
- **Enforcement.** Doc: comments + R000D issue / Impl: explicit / Verif: `weather-retry-clock-state` 23/23, `weather-retry-clock-mutations` 12/12 (run here).
- **Residual.** See A-F08. The weather lane owns the acquisition semantics.

### NEW-A-03 — Live timezone authority `tz` (multi-writer) and its simulation-rebase side effect

- **Sources.**
  - Writers: `bindConfig` `S:686`; `loadPrayerData` `S:3676, 3691, 3697`; `adoptPrayerBundle` `S:1213`.
  - Readers: `partsInTz` `S:937`, `prayerCivilDay` `S:1170`, `simNow` `S:1014`, `beginRequest` `S:1076`, `selectPrayerEvent` `S:2324`, `selectCalendarDisplay` `S:865`, `prayerRecordReady` `S:1185`, weather URL (`requestZone`).
- **States.** Hint (config) → provider-adopted (cache or network metadata) → current-record zone. `_cacheTz` is frozen separately for the cache key.
- **Transitions.** Any write that changes `tz`:
  - re-keys formatter caches;
  - in explicit-clock modes, re-anchors `simNow` through `initSim` and discards a `SalahClock` preview (A-F02);
  - changes `prayerCivilDay` and therefore the requested day.
- **Guards.** Network writes occur only after `prayerResultEligible(op)`. Cache writes occur only after `requestEligible(op)` and admission. There is no validity guard on the config hint (A-F01).
- **Enforcement.** Doc: comments (`S:680, 3676, 3691`) / Impl: implicit / Verif: unit for the adoption order (`r0004-boot-day`, `r0005-*`). There is no test of the hint-validity or preview interactions.

---

## 2. Historical-to-current reconciliation

| Original | RLGWO / commit | What changed (diff `f71fef6c..363c3e53`) | Disposition | Evidence |
|---|---|---|---|---|
| N01 | R0003 (#3; PR #79 `a4766a1b`; `a06957c6`); R0026 `fbd08aa1` (settings search only) | `appearanceOnly` heuristic replaced by `CONFIG_EFFECTS`/`classifyConfigChange` (`S:697-741`); 3-way dispatch (`S:3734-3749`); Reset intent (`S:4136`); `_wxRetry` reset (`S:3720`) | implemented but not fully verified | Suites 35+21+24+15 pass here; P4 reproduces the no-request presentation path; native local only (certificate §4) |
| N02 | none after audit (R0008/R0020 pre-audit) | no change in clock/inverse/`SalahClock` | still implicit or vulnerable | r0020 44/44, r0008 37/37 pass; new A-F01 (`partsInTz` host fallback reachable) and A-F02 (preview discarded) |
| N03 | R000D (#13; PR #74 `645b53cc`; `ba0851ae`) weather/radar only | prayer leases unchanged; weather/radar `lastWxTry`/`lastRadarAt` gating → elapsed `_wxRetry` | implemented but not fully verified | ownership suites pass; native abort timing unproved |
| N04 | none after audit | unchanged | still implicit or vulnerable | A-F01 demonstrates an unrecoverable path that the original audit said was not established |
| N05 | none after audit | unchanged | still implicit or vulnerable | mirror flags remain; P5 shows the dead `data-stale` state (A-F04) |
| N06 | R0007 (#7; PR #73 `dbf3370f`) | `prayerEventCandidates`/`selectPrayerEvent`; model derives all next fields from one target; explicit progress kinds; receipt fields (`S:2294-2394, 3523-3526`) | resolved and independently verified (source scope); native acceptance partly by cross-run reuse | 44/44 incl. mutants; P3; independent source review `5e946fe`; hosted final run FAILURE/PARTIAL |
| N07 | R0007 SRC-02 year padding; R0007 font var | logic unchanged | implemented but not fully verified | date harnesses red 1 case each (A-F03) |
| N18 | R0007 font gate (`58fc4afc`, `ec69edf8`) | late `html.webfonts` gate + explicit invalidation; fit key unchanged | partly resolved | font-gate tests pass; NH01 untouched |
| N19 | R000B (`ea9f8300`) per-frame cloud reconcile; R000D cadence side | added `reconcileCloudPublication()` per frame; no exception handling added | partly resolved | XF02 liveness repaired; NH02 open |
| NF01 | R0007 | hardcoded `tomorrow.Fajr` (old `S:2291-2292`) removed; chronological epoch selection | resolved and independently verified | P3: Isha 91 min vs Fajr 360 min control; ES07 `hardcoded-fajr` mutant fails as intended |
| XF01 | R0003 | label/time/datefmt/appearance → presentation; equal → none; units/lp/seed broad by decision (D3/D4); weather-units/radar separation **not done** | partly resolved | P4; `R0003.md:36-37, 130-132` |
| XF02 | R000D | retry gates moved to the elapsed clock; loop already elapsed | resolved and independently verified (gate scope) | weather-retry-clock suites 35 pass; residual A-F08 (source-age rejection persists under skew) |
| EF01 | R0017 (#23; `7214a2c8`) | single-runtime extraction replaced by `native-script-contract.js`; runner uses `time.monotonic()` (`tools/cp9/run_native_regressions.py:372-392`) | partly resolved | Original failures ("exactly one native inline runtime") gone; 3 date harnesses red again from a later R000B change (A-F03); R0003 records them as "pre-existing" (`R0003.md:220, 364`) |
| NH01 | none | none | still implicit or vulnerable (unverified) | key at `S:3407`; reset path does not clear `_cnFit` |
| NH02 | none | loop body grew; no recovery added | still implicit or vulnerable (unverified) | `S:3869-3889` |

Proposals from the original audit that were never carried out:
- Separating weather units from the radar and prayer dependencies (XF01 smallest-safe-change), deferred as D4.
- A complete semantic fit key, or explicit invalidation on rail change (NH01).
- An explicit loop restart transition (NH02); not done, which is consistent with the audit's own "only if a reachable throw is established".
- Encoding recovery and prefetch as parallel regions without mirror flags (N05 architecture note).

---

## 3. Findings (documentary only)

| ID | Title | Machines | Evidence class | Severity / materiality |
|---|---|---|---|---|
| A-F01 | Invalid timezone hint makes prayer acquisition permanently unavailable and issues `timings/null` requests | N02, N04, N05, NEW-A-03 | demonstrated (probe P1) | medium: hard constraint (prayer/timezone correctness, liveness); reachable via `#tz=`; fails closed truthfully but never recovers, although the provider would supply a valid zone |
| A-F02 | `SalahClock` explicit preview is silently replaced by wall time on zone adoption while `_clockPreview` stays true | N02, NEW-A-03 | demonstrated (probe P2) | low: diagnostic API, but used by `tools/cp9/*_check.py` qualification; touches the truthful-evidence constraint |
| A-F03 | Date regression instruments red at baseline since R000B; no-model calendar cases unexercised | N07, N06 | demonstrated (tests run) | medium (evidence): three harnesses lose exactly the unavailable/no-model calendar assertions; R0017 ES17-07 had claimed healthy passes |
| A-F04 | Unreachable `data-stale="prayer"` presentation; redundant mirror flags and unused model fields | N05, N06 | demonstrated (P5) for `data-stale`; source-traced for the rest | low: dead CSS state (the staletag still discloses staleness); redundant state increases drift risk |
| A-F05 | `tz` has four writers; loader writes it before the record becomes current, and each write has clock side effects | NEW-A-03, N02, N04 | plausible risk | low–medium architecture: the root mechanism behind A-F01/A-F02; ordering is guarded by eligibility today |
| A-F06 | Render-loop exception recovery (NH02) still absent; per-frame work grew | N19 | speculative (no reachable throw found) | low until a throw is shown |
| A-F07 | Fit-key incompleteness (NH01) plus `resetForNewLocation` not clearing `_cnFit` | N18, N01 | plausible risk | low; visual magnitude unmeasured |
| A-F08 | After a backward device-clock change, weather is refetched every 60 s but each response's negative source age keeps it ineligible | NEW-A-02, N19 | plausible risk | low: bounded (1/min) and truthful unavailability; owned by the weather lane |
| A-F09 | R0007 native acceptance rests on cross-run reuse; the final hosted run is FAILURE/PARTIAL | N06 | demonstrated (documentary) | low: disclosed in the contract and certificate; not a product defect |

**A-F01 trace.**
1. `src/native/config.js:145` accepts any non-empty string as `tz`.
2. `bindConfig` `S:686` binds it.
3. `prayerCivilDay` `S:1170-1176` returns `null` (`zoneFormatter` throws).
4. `loadPrayerData` `S:3671` gives `beginPrayerRequest("current",null)`, and `S:3687-3689` gives `fetchTimings(null)`.
5. The URL at `S:1132` becomes `/v1/timings/null` (3 attempts).
6. `admitPrayerRecord` `S:1056` rejects (`dateStr` is not a string). `tz` is never replaced by `meta.timezone` because the transport throws before `S:3691`.
7. `maintainPrayerDay` `S:1248` returns on `!day`, so there is no retry.
8. `partsInTz` `S:943-946` uses the host zone silently.
- P1 result: 3 requests, all `/timings/null`; after 180 simulated seconds of frames `today=null` and `tz="Bogus/Zone"`; the error shows "Prayer times unavailable".
- Pre-existing at `f71fef6c`: `config.js:115` has the same normalisation and the clock/loader are unchanged. This contradicts the original N02 statement that "no ordinary invalid-zone counterexample was established".
- Open: whether the builder or settings can emit such a zone, and the provider's response to `null`.

**A-F02 trace.**
1. `SalahClock.set` `S:3769-3770` sets `_simBase=utcMs` and `_simTz=tz`.
2. The prayer loader changes `tz` (`S:3691` / `S:1213`).
3. `simNow` `S:1014` sees `_simTz!==tz`, calls `initSim` `S:999-1008`, and uses `base=Date.now()` when there is no `simTime`.
- P2 result: requested 2026-12-25T03:00Z, observed 2026-09-07T12:00Z, `_clockPreview:true`.
- Consumers: `tools/cp9/celestial_lifecycle_check.py:37`, `daytime_composition_check.py:56` (they may avoid it with an explicit `tz`; not checked).

**A-F03 trace.**
- The calendar no-model branch `S:3487-3492` calls `withdrawWeatherEffects` (`S:2722`, added by R000B), which calls `paintLunarOptic` `S:3004-3007` → `el.style.getPropertyValue`.
- `tests/r0009-calendar-harness.cjs:46` stubs only `getComputedStyle`. `tests/r0003-harness.cjs:54` was patched for the same helper.
- Logs: `probes/A/logs/r0001-date-sinks.cjs.log`, `r0009-date-selection.cjs.log`, `r0019-date-disclosure.cjs.log`.
- Failing case names:
  - "missing dates expose explicit successor unavailable output"
  - "wrong current context withholds the model and never relabels old AH as current"
  - "missing invalid and no-model values clear previously hidden full dates"
- `tools/cp9/run_native_regressions.py:22-29` selects all three. There is no `CASE_RESIDUALS` entry, so the aggregate runner is FAIL at baseline.

**A-F04 trace.**
- `_prayerStale` is set at `S:1258`.
- `model()` → `selectPrayerEvent` returns `current-record-unavailable` for a day mismatch (`S:2329-2331`), so `render` takes the `!M` branch, and `S:3518` (the only `data-stale` writer) is skipped.
- `warmEnd`/`needTomorrow` (`S:2386, 2392`) have no reader (grep).
- `_rolloverBusy`/`_rolloverNextTry`/`fetchingTomorrow` duplicate the slot and cooldown state (`S:1229-1236`) and feed only `qaState` `S:3577`.

**A-F08 trace.** `weatherEligibility` `S:1369-1378` requires `sourceAge>=0`. `retryGate` `S:1272-1279` now opens every 60 s elapsed. A device clock behind provider time produces a repeated rejection rather than recovery. This is bounded and truthful; whether that is intended policy is unknown.

---

## 4. GDOPL inputs (Gradient Descent Over the Project Lagrangian)

The model is schematic only. `q` is the current source configuration. `f_T(q)` is the typed vector {stale exposure, time to useful prayer presentation, redundant acquisition, ownership complexity, verification burden}. Constraints `g_j(q) ≤ 0` are the modelled soft limits. `F_hard` contains:
- prayer, date, timezone and countdown correctness;
- rejection of late unauthorised results;
- accepted state kept separate from displayed state;
- optional astronomy never blocking prayer;
- truthful evidence.

No weights, gradients or optima are claimed.

| # | Interaction | Current q | Constraints | Neighbour `q' = apply(q, η)` | Anticipated benefit / regression cost | Supporting evidence | Classification |
|---|---|---|---|---|---|---|---|
| G1 | Chronological next-event across midnight (N04→N06) | explicit `selectPrayerEvent` | F_hard prayer/countdown correctness | — (already taken) | — | before: NF01 probe at `f71fef6c`; after: P3 + ES07 mutants | demonstrated improvement |
| G2 | Config change → prayer/weather/sky invalidation (N01→N03/N04) | 3-way classifier; units/lp/seed broad | F_hard stale-result rejection; adopted-tz preservation | η = weather-only path for `units` (D4) | fewer prayer refetches on a unit edit / risk of mixed-unit weather records | P4 + R0003 suites; no `units` experiment | demonstrated improvement (label/time/datefmt); `units` path: plausible improvement requiring verification |
| G3 | Invalid hint zone vs provider zone (N01→N02→N04) | hint trusted; `prayerCivilDay` null halts | F_hard timezone correctness; truthful provenance | η1 = validate `tz` at normalisation (fallback to default or Intl zone); η2 = when the hint is unusable, request a provider-zone bootstrap day and adopt `meta.timezone` | recovery instead of a permanent outage / risk of silently replacing a user-intended zone | A-F01 (P1); no candidate tested | plausible improvement requiring verification |
| G4 | Zone adoption vs explicit clock (NEW-A-03→N02) | any `tz` write re-anchors explicit clocks | truthful evidence; preview/live separation | η = keep a `SalahClock` anchor in UTC across zone changes (re-anchor only `simTime`-derived anchors) | qualification tools observe the requested instant / risk of a frozen `simTime` recipe semantics change | A-F02 (P2) | plausible improvement requiring verification |
| G5 | Wall-clock rollback vs weather (N02→NEW-A-02→weather) | elapsed retry spacing | truthful weather provenance; bounded retries | η = treat negative source age within a tolerance as a clock-skew state | could restore weather under skew / risk of accepting future-dated data (hard constraint) | before/after gate suites (XF02 → R000D); A-F08 untested | demonstrated improvement (liveness); skew handling: insufficient evidence |
| G6 | Stale presentation vs model withdrawal (N05→N06/N07) | withdraw the model; staletag in AH; dead `data-stale` | separation of accepted vs displayed state | η = remove the dead CSS/flags, or write `data-stale` on the withdrawal branch | less redundant state / a visual change requires owner approval (visual conservatism) | P5 | retain (visual change not authorised); cleanup: plausible improvement requiring verification |
| G7 | Font readiness vs countdown fit (NEW-A-01→N18) | late gate + key without rail geometry | layout correctness (native-only proof) | η = include rail `d` (or noon+decl) in the key; clear `_cnFit` on reset | removes NH01 / negligible cost | no native measurement | insufficient evidence |
| G8 | Loop liveness vs exceptions (N19) | no `try/finally` | instance-owned cancellation; truthful failure publication | η = restore `_raf` scheduling in a `finally` without swallowing | resilience / could hide truth-publication failures | none (no reachable throw) | insufficient evidence |
| G9 | Instruments vs product changes (EF01→A-F03) | three date harnesses red | truthful evidence claims | η = patch the date harness style stub as `r0003-harness.cjs:54` did | restores 3 assertions / risk of masking a real DOM dependency | test logs here; R0003 doc lists them as pre-existing | plausible improvement requiring verification |

Projection comparison (`GDOPL_PROJECTION.md:42-59, 69-71, 89-100`):
- Taken, with evidence: the "one chronological prayer-boundary selector" (G1) and the "configuration effect matrix" (G2, initial narrow branches as advised: label/time/date preserved; method/school/coordinates broad).
- Not taken: the matrix row for temperature units ("Preserve prayer"), and lp/seed ("Preserve prayer/weather"); both remain broad by owner decision.
- Taken: "Repair evaluator source boundaries". It was then partially undone by a later product change (A-F03).
- Taken: monotonic retry spacing (XF02).

---

## 5. Coverage statement

**Read fully.**
- `src/native/index.html` lines 640–1280, 2271–2400, 2462–2500, 3338–3540, 3640–3940.
- The full `src/native/index.html` diff `f71fef6c..363c3e53` (683 lines).
- `docs/state-contracts/R0007.md`.
- Original catalogue entries N01–N07, N18, N19, NF01, XF01, XF02, EF01, NH01 and NH02.
- `GDOPL_PROJECTION.md` §§ time domains, config matrix, schedules, candidates.
- `tests/r0003-harness.cjs`.

**Sampled.**
- `docs/state-contracts/R0003.md` (grep: D1–D4, effect table, known failures) and `R0017.md` (grep: previously red commands).
- `tools/cp9/run_native_regressions.py` lines 1–80 and 372–392.
- `src/native/config.js` tz normalisation.
- `weatherEligibility`, `paintLunarOptic`.
- Issue #3/#7 final certificates; issue list closure dates.
- Heads of `r0004-boot-day`, `r0009-date-selection`, `r0020-clock` and `r000a-markers`.

**Not examined.**
- Generated root beyond function-level parity.
- `offline.html`.
- Settings/builder UI internals (config lane).
- Weather decision and cloud internals (weather lane).
- Sky/moon renderers.
- `R0017.md` in full.
- Native/browser behaviour (no browser launched).
- `GDOPL_FINAL.md`.
- Python native qualification tests (`tests/test_r0007_*.py`).
- Evidence directories under `docs/state-contracts/evidence/`.

**Tests run** with Node v24.14.0, `node --test <file>`, cwd = worktree, no tree writes (`git status` clean afterwards):
- Passing: prayer-next-event-state 44/44, r0007-countdown 23/23, r000a-markers 25/25, r0020-clock 44/44, r0003-ownership 24/24, config-effects-state 35/35, config-effects-mutations 21/21, r0007-font-gate 5/5, r0007-font-use 3/3, r0007-async-observation 5/5, r0007-recovery-precondition 21/21, weather-retry-clock-state 23/23, weather-retry-clock-mutations 12/12, r0004-boot-day 8/8, r0005-day-return 6/6, r0006-recovery 18/18, r0008-timezone 37/37, r0002-admission 62/62, r0004-currentness-controls 3/3, r0005-adoption 16/16, native-appearance-currentness 15/15, r0018-prayer-row-status 27/27, r0017-adapters 11/11, hotfix-prayer-weather 21/21, r001d-lifecycle 1/1, r0025-lifecycle 1/1.
- Failing at case level: r0009-date-selection (21 pass / 1 fail), r0019-date-disclosure (15/1), r0001-date-sinks (12/1).

**Probes** (`probes/A/lane-a-probes.cjs`, `parity.cjs`; repository VM harness with stubbed fetch, storage and timers; no network or browser):
- P1 invalid zone: demonstrated.
- P2 preview rebase: demonstrated.
- P3 NF01 fixed: demonstrated.
- P4 presentation path: demonstrated.
- P5 dead `data-stale`: demonstrated.
- Parity: 40/40 identical.
