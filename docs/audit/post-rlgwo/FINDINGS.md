# Post-RLGWO audit: documentary findings

**Documentary only.** This inventory records observations at main `363c3e53`. No GitHub issue
was filed, nothing was remediated, and no repository behaviour was changed. Any engineering in
response needs a separate owner decision. A finding's position is not a priority order for work.

Read with: [REPORT.md](REPORT.md) (method, verification, limits), the registry
[IMPLICIT_STATES.md](../../../IMPLICIT_STATES.md) and [CROSSWALK.md](CROSSWALK.md).

## Conventions

- **Evidence class** is the integrator's, after re-opening every cited `file:line` at the
  baseline and, where marked, re-running the probe or test: **demonstrated** (traced end to end
  and reproduced by an effect-free probe, an existing test, or a recorded native observation),
  **plausible risk** (the code path exists; the trigger is not demonstrated), **speculative**.
  Where the dependency is demonstrated but the trigger is not, both are stated.
- **Sub-labels on "demonstrated".** *injected fault* — the consequence was reproduced by forcing a
  failure that has not been seen to occur naturally (PRA-F-01); *model-parameterised* — the probe
  models cadence or durations with chosen parameters rather than measured ones (PRA-F-03 poll
  timing, PRA-F-10 worker durations). Neither sub-label means "observed in the product"; no browser
  was run in this audit.
- **Hard constraint**: one of the non-tradeable invariants listed in
  [GDOPL_ASSESSMENT.md](GDOPL_ASSESSMENT.md#hard-feasibility-domain).
- **Origin**: predates the campaign / introduced during it / unknown, with the commit evidence.
  "Predates" means the cited lines are unchanged in `git diff f71fef6c 363c3e53` and exist at
  `f71fef6c` (the original audit); it does not mean earlier than every RLGWO.
- **Order.** By severity and materiality. PRA-F-01 is listed first for its severity *if* triggered; it
  is a conditional structural violation with no natural trigger found. REPORT.md §10 states the
  ranking rule that puts demonstrated natural triggers (PRA-F-02 onward) ahead of it for remaining risk.
- Line numbers are approximate baseline anchors in the authored source; `S:` is
  `src/native/index.html`.

## Summary

| Evidence class | Count |
|---|---|
| demonstrated | 27 |
| plausible risk | 7 |
| speculative | 4 |
| **Total** | 38 |

| ID | Title | Class | Severity | Hard constraint |
|---|---|---|---|---|
| [PRA-F-01](#pra-f-01) | Optional Moon exception aborts prayer publication and strands the render loop | demonstrated — injected fault (dependency); trigger speculative | high if triggered | optional astronomy never blocks prayer |
| [PRA-F-02](#pra-f-02) | Invalid timezone hint makes prayer permanently unavailable | demonstrated | medium | prayer/timezone correctness |
| [PRA-F-03](#pra-f-03) | Quarter-hour weather authority gap withdraws and snaps the cloud deck (previously recorded by the R000B certificate) | demonstrated — model-parameterised poll; header gap also observed on the delivered page; deck snap plausible | medium | truthful weather (holds); continuity gate |
| [PRA-F-04](#pra-f-04) | Settings Reset authority lost on a dirty close | demonstrated (VM) | medium-low | accepted vs displayed state; truthful persistence/provenance |
| [PRA-F-05](#pra-f-05) | Builder reverse geocode adopts error bodies and flips the calculation method | demonstrated (VM) | medium-low | prayer correctness; privacy |
| [PRA-F-06](#pra-f-06) | Red regression instruments retained as an undeclared known-failure set | demonstrated | medium (evidence) | truthful evidence claims |
| [PRA-F-07](#pra-f-07) | Pages payload estimate doubled past the qualified bound; verifier inert | demonstrated (estimate) | medium | truthful evidence; deployment safety |
| [PRA-F-08](#pra-f-08) | Timezone adoption rebuilds the sky/Moon scene on routine boots; builder never emits `tz` | demonstrated (source + probe); visual effect unobserved | medium | accepted vs displayed state |
| [PRA-F-09](#pra-f-09) | No automated gate on main; merge is deploy | demonstrated | medium (architecture) | truthful evidence; canonical source |
| [PRA-F-10](#pra-f-10) | In `timeScale`/clock-preview modes, forecast interpolation churns the refined-sky identity; stall unreported | demonstrated — model-parameterised: mechanism demonstrated; real worker durations unmeasured | medium-low | truthful evidence/status |
| [PRA-F-11](#pra-f-11) | Shipped app has no star-scintillation producer; docs and telemetry describe the old one | demonstrated | medium (documentation) | truthful evidence claims |
| [PRA-F-12](#pra-f-12) | Moon worker failure is terminal for the page; retry unowned; cached 404 | demonstrated | medium | AGENTS gate D (Moon every night) |
| [PRA-F-13](#pra-f-13) | Empty Moon slot after a wrapper failure; light not bound to the visible surface | demonstrated (injected, native) | medium (fault path) | AGENTS gate D; no faked light |
| [PRA-F-14](#pra-f-14) | `SalahClock` preview discarded on zone adoption | demonstrated | low | truthful evidence |
| [PRA-F-15](#pra-f-15) | Diagnostics with side effects or misreported outcomes | demonstrated | low | truthful evidence |
| [PRA-F-16](#pra-f-16) | Radar acquired with no product consumer; manifest host unvalidated | demonstrated / plausible | low | privacy |
| [PRA-F-17](#pra-f-17) | Location data retention: unbound `siteElev`; per-location caches never evicted | demonstrated | low-medium | truthful provenance; privacy |
| [PRA-F-18](#pra-f-18) | Frozen v1 limitations undocumented; `--check-pages` fails; README V1 snippet 330×534 | demonstrated | low-medium | truthful evidence; 325×530 contract |
| [PRA-F-19](#pra-f-19) | Generator partial states, `assert` guards and stale chunks | demonstrated | low-medium | canonical source ownership |
| [PRA-F-20](#pra-f-20) | Units/lp/seed stay broad; `seed` has two authorities | demonstrated (efficiency) | low | — |
| [PRA-F-21](#pra-f-21) | Unreachable `data-stale="prayer"`; mirror flags; unused model fields | demonstrated | low | accepted vs displayed state |
| [PRA-F-22](#pra-f-22) | Preview host lifecycle asymmetries | demonstrated (source) | low | instance-owned disposal |
| [PRA-F-23](#pra-f-23) | Countdown fit key incomplete (NH01) | plausible risk | low | — |
| [PRA-F-24](#pra-f-24) | Backward device clock: weather refetched each minute but never admitted | plausible risk | low | truthful weather |
| [PRA-F-25](#pra-f-25) | Preview forecast substitution has no track-age bound | plausible risk | low | — |
| [PRA-F-26](#pra-f-26) | Moon refinement cadence, hide/show discard and resource footprint | plausible risk | low-medium (efficiency) | — |
| [PRA-F-27](#pra-f-27) | Closure state split between repository and issue comments | demonstrated | low | truthful evidence |
| [PRA-F-28](#pra-f-28) | README pin ↔ installer ↔ docs-receipt coupling | demonstrated | low (architecture) | — |
| [PRA-F-29](#pra-f-29) | GPS adoption awaits an unbounded `permissions.query` | speculative | low | — |
| [PRA-F-30](#pra-f-30) | Nominatim `class`/`category` naming may make place preference inert | speculative | low | — |
| [PRA-F-31](#pra-f-31) | Two lunar-light producers can diverge under `simMoon*` | speculative | low | — |
| [PRA-F-32](#pra-f-32) | Header shows a model condition while clouds are withheld without a timetable | plausible risk | low | — |
| [PRA-F-33](#pra-f-33) | `_commitSettings` fires `applyConfig` without a rejection handler | plausible risk | low | — |
| [PRA-F-34](#pra-f-34) | Per-compose allocations and PNG mask encode | speculative (performance) | optimisation only | — |
| [PRA-F-35](#pra-f-35) | R0007 native acceptance rests on cross-run reuse | demonstrated (documentary) | low | truthful evidence |
| [PRA-F-36](#pra-f-36) | Mask decode has no wall-clock bound (RF04) | plausible risk | low | — |
| [PRA-F-37](#pra-f-37) | Duplicated renderer-boundary formulas and geometry literals | demonstrated (source) | low | — |
| [PRA-F-38](#pra-f-38) | Diagnostic `sim*` overrides accepted from any embed URL; visible header carries no SIM marker | demonstrated (source trace); reachability needs a hand-written fragment | low | truthful weather provenance |

---

<a id="pra-f-01"></a>
## PRA-F-01 — Optional Moon exception aborts prayer publication and strands the render loop

- **Registry:** [ISM-PRAY-010](../../../IMPLICIT_STATES.md#ism-pray-010), [ISM-MOON-002](../../../IMPLICIT_STATES.md#ism-moon-002), [ISM-MOON-004](../../../IMPLICIT_STATES.md#ism-moon-004), [ISM-SKY-005](../../../IMPLICIT_STATES.md#ism-sky-005). Lane IDs merged: A-F06 and NH02 (lane A), D-F03 (lane D), EF-E01 (lane E).
- **Evidence class:** demonstrated — *injected fault* — as a dependency (code trace plus an injected-fault probe re-run by the integrator); the trigger is speculative (no natural throw found in `request()`/`poll()`). Lanes A (speculative), D (plausible risk) and E (demonstrated) described the same structure; this entry reconciles them by separating the dependency from the trigger.
- **Severity / materiality:** high if triggered — the prayer name, countdown and rows stop updating and the loop stops until a hide/show; materiality is conditional on a throw.
- **Hard constraint:** "optional astronomy never blocks prayer".
- **Origin:** predates the campaign: `loop`, `_raf` handling and the `renderMoon` call order are unchanged since `f71fef6c`; R000B added per-frame work (`reconcileCloudPublication`, S:3880) without containment.
- **Trace:** S:3877 `render()` is called from `loop` without `try`; S:3494 `renderMoon()` runs before the prayer DOM writes at S:3499–3518; S:1954 `renderMoonPBR` → `window.SalahMoonRuntime.request()` (`moon/src/moon-native.mjs` ~L261–273, not try-wrapped apart from `initialPresentation` and `capture`); a throw skips S:3888 `_raf=requestAnimationFrame(loop)`, so `_raf` keeps the consumed id and `start()` (S:3890, `if(!_raf)`) is a no-op until `stop()` on hide. `applyTheme` deliberately rethrows (S:3336). Contrast: `real-sky/native-host.mjs` ~L253 catches and always reschedules.
- **Probe:** [probes/E/moon-throw-blocks-prayer.cjs](probes/E/moon-throw-blocks-prayer.cjs) — control: `.cn`="Isha" and `.times` repopulated; injected `request()` throw: `render()` throws, `.cn` stays "SENTINEL", `.times` empty.
- **Open questions:** candidate natural throw sites (lane E, unproven): `ImageData` size mismatch in `syncTexture`, a `detail.adopt` RangeError, unwrapped `worker.postMessage`, `toDataURL` under memory pressure. Whether isolation or reordering is wanted is an owner decision.

<a id="pra-f-02"></a>
## PRA-F-02 — Invalid timezone hint makes prayer permanently unavailable

- **Registry:** [ISM-PRAY-001](../../../IMPLICIT_STATES.md#ism-pray-001), [ISM-PRAY-003](../../../IMPLICIT_STATES.md#ism-pray-003), [ISM-PRAY-004](../../../IMPLICIT_STATES.md#ism-pray-004), [ISM-PRAY-009](../../../IMPLICIT_STATES.md#ism-pray-009). Lane IDs: A-F01, A-F05.
- **Evidence class:** demonstrated (probe A P1 re-run; probe G `tz-hint-probe` independently gives `prayerCivilDay=null` for `Asia/Riyad`).
- **Severity:** medium. It fails closed and truthfully ("Prayer times unavailable"), but never recovers, although the provider would return a valid zone.
- **Hard constraint:** prayer/date/timezone correctness (liveness side).
- **Origin:** predates the campaign (`src/native/config.js` `c.tz` normalisation and the loader unchanged since `f71fef6c`); contradicts the original N02 statement that no ordinary invalid-zone counterexample was established.
- **Trace:** `src/native/config.js` L145 accepts any non-empty string; `bindConfig` S:686; `prayerCivilDay` S:1170–1176 returns `null` when `zoneFormatter` throws; `loadPrayerData` S:3671 then `fetchTimings(null)`; the URL at S:1132 becomes `/v1/timings/null` (3 attempts); admission rejects; `tz` is never replaced because the transport throws before S:3691; `maintainPrayerDay` S:1248 returns on `!day`; `partsInTz` S:943–946 silently uses the host zone.
- **Probe:** [probes/A/lane-a-probes.cjs](probes/A/lane-a-probes.cjs) P1: 3 requests `…/timings/null`, `today=null`, `tz="Bogus/Zone"` after 180 simulated seconds.
- **Open questions:** reachability — the builder never emits `tz` (PRA-F-08), so the path needs a hand-written `#tz=` or a stored record; the provider's response to `null` was not contacted.

<a id="pra-f-03"></a>
## PRA-F-03 — Quarter-hour weather authority gap withdraws and snaps the cloud deck

- **Registry:** [ISM-WX-001](../../../IMPLICIT_STATES.md#ism-wx-001), [ISM-WX-003](../../../IMPLICIT_STATES.md#ism-wx-003), [ISM-WX-005](../../../IMPLICIT_STATES.md#ism-wx-005), [ISM-SKY-003](../../../IMPLICIT_STATES.md#ism-sky-003). Lane ID: BF01.
- **Previously known:** the repository's own R000B certificate ([issue 11 certificate comment](https://github.com/theislampill/salah_widget/issues/11#issuecomment-6788969371), §3, a root observation) recorded this on the delivered page as a "delivered-behaviour finding for the owner": the widget shows "weather unavailable" at each quarter hour until its next request lands. This audit adds the cloud-deck consequence and the source trace; it is not a new discovery.
- **Evidence class:** demonstrated — *model-parameterised* (30 s poll modelled) — for the authority gap (probe re-run with a modelled 30 s poll; the R000B certificate independently records a header gap of about 2 s and about 23 s on the delivered page); the visible deck disappearance under cloud is plausible, not observed (the certificate's page was clear-sky).
- **Severity:** medium. Under cloudy or rainy weather it predicts a deck withdrawal and precipitation stop every 15 minutes with a snap re-establishment.
- **Hard constraint:** truthful weather provenance holds (the withdrawal is truthful); the AGENTS continuity rule ("no slideshow") is at risk. Extending the TTL would breach the hard constraint and is not a remedy.
- **Origin:** predates the campaign (at `f71fef6c` `applyCloudState` zeroed coverage on `modelCode==null`); R000B made the withdrawal explicit.
- **Trace:** eligibility S:1374–1375 (`sourceAge` and `receiptAge` both within 0…900 000 ms); `retryGate` S:1276 returns `fresh-data-satisfied` while the record is selected; poll every ~30 s S:3875; on expiry the next frame's `reconcileCloudPublication` (S:3880) withdraws (S:2730–2741); the first admitted deck snaps (S:3233).
- **Probe:** [probes/B/wx-quarter-gap-probe.cjs](probes/B/wx-quarter-gap-probe.cjs): no fetch while selected; unselected at 06:30:00.001 and 06:45:00.001; first polls finding nothing eligible at 06:30:20 and 06:45:20.
- **Open questions:** the provider's real `current.time` cadence; whether the owner accepts the gap as truthful withdrawal.

<a id="pra-f-04"></a>
## PRA-F-04 — Settings Reset authority lost on a dirty close

- **Registry:** [ISM-CFG-003](../../../IMPLICIT_STATES.md#ism-cfg-003), [ISM-CFG-004](../../../IMPLICIT_STATES.md#ism-cfg-004), [ISM-CFG-005](../../../IMPLICIT_STATES.md#ism-cfg-005), [ISM-WX-007](../../../IMPLICIT_STATES.md#ism-wx-007). Lane IDs: F-C01, F-C04 (lane C); OM-04 (second pass).
- **Evidence class:** demonstrated in the repository's VM fixture (probes re-run); the fixture stubs `applyConfig`, so the real `_publishPersistence` on close is not exercised. OM-04 demonstrated by source trace.
- **Severity:** medium-low. A user-intended Reset is silently undone and re-persisted; it needs a dirty form plus close or typing inside a window of up to about 6 s.
- **Hard constraint:** separation of accepted (runtime) and displayed (form) state; truthful persistence and location provenance.
- **Origin:** predates the campaign (lines unchanged since `f71fef6c` except R0003's `reset:true`); not in the original audit.
- **Trace:** `_resetLocal` S:4122–4144 never clears `_setDirty` and repopulates the form only after both awaits; the label input calls `_invalidateSetLocation` (S:4064–4065) despite the S:4063 comment "Name edits preserve acquisition"; `_closeSettings` → `_commitSettings` S:4097–4104 commits the stale form. After a successful clear with the continuation abandoned, `CONFIG.source` stays `"localStorage"`, so `_setLocationSaved` (S:4038) makes `_setPin` say "Saved browser position" (S:3966) although nothing is saved (OM-04).
- **Probes:** [probes/C/reset-close-probe.cjs](probes/C/reset-close-probe.cjs) (close re-persists lat 24.4672, method 3; runtime ≠ storage with status "Saved settings cleared. / Detecting your area…"), [probes/C/reset-label-probe.cjs](probes/C/reset-label-probe.cjs) (typing a name during Reset's apply await reverts runtime 40.7 → 24.4672).
- **Open questions:** should Reset discard pre-Reset dirtiness; should name edits invalidate the Reset continuation.

<a id="pra-f-05"></a>
## PRA-F-05 — Builder reverse geocode adopts error bodies and flips the calculation method

- **Registry:** [ISM-CFG-008](../../../IMPLICIT_STATES.md#ism-cfg-008), [ISM-CFG-007](../../../IMPLICIT_STATES.md#ism-cfg-007). Lane IDs: F-C02, F-C05.
- **Evidence class:** demonstrated (VM probe re-run) for the method flip and for the local-mode request; the real provider error-body shape is not verified.
- **Severity:** medium-low: the prayer calculation method baked into a portable embed changes silently; an error is represented as success.
- **Hard constraint:** prayer correctness (calculation method); privacy (local-mode coordinates sent to BigDataCloud, disclosed at `src/native/builder.html` ~L193).
- **Origin:** predates the campaign (the same line is at `f71fef6c` `builder.html` L339).
- **Trace:** `src/native/builder.html` L383–398: no `r.ok` check, no timeout or abort, any JSON adopted; L395 `(j.continentCode==="NA")?"2":"4"`; failures swallowed L397; the lat/lon input listener L399 schedules the lookup even for dimmed local-mode fields.
- **Probe:** [probes/C/reverse-error-probe.cjs](probes/C/reverse-error-probe.cjs): a `{status:429}` reply changes the export from `method=2` to `method=4`.

<a id="pra-f-06"></a>
## PRA-F-06 — Red regression instruments retained as an undeclared known-failure set

- **Registry:** [ISM-BLD-007](../../../IMPLICIT_STATES.md#ism-bld-007), [ISM-BLD-009](../../../IMPLICIT_STATES.md#ism-bld-009), [ISM-PRAY-006](../../../IMPLICIT_STATES.md#ism-pray-006), [ISM-SKY-002](../../../IMPLICIT_STATES.md#ism-sky-002). Lane IDs: A-F03, D-F07, FND-F-07; original EF01.
- **Evidence class:** demonstrated (the integrator ran all seven instruments at the baseline and nine historical commits; see [REPORT.md](REPORT.md#registered-instruments-and-their-history)).
- **Severity:** medium for evidence. Exactly the no-model calendar assertions are lost; a new failure inside an already-red command is masked at command level; no machine-readable expected-failure manifest exists.
- **Hard constraint:** truthful evidence claims.
- **Origin:** mixed. The three date harnesses were green after R0017 (`eebba178`, `539c1366`, `dbf3370f`) and became red at the **R000B merge `da126880`** (issue 11): the no-model branch now calls `withdrawWeatherEffects` → `paintLunarOptic` (S:3491 → S:2727 → S:3007 `el.style.getPropertyValue`), which `tests/r0009-calendar-harness.cjs` does not stub; R000B's `d6500a09` patched the r0008 and r0011 harnesses for the same owners but not these. One `r0022-baseline-balance` case ("London shallow night actual solar path/horizon/marker geometry matches baseline") became red at the **R0007 merge `dbf3370f`** (issue 7); the cause within that merge's 29 commits was not isolated. The other six `r0022-baseline-balance` failures, the `r0021-reveal` byte-pin failure, the two `r0022-lunar-consumers` failures and the 14 `rlgwo-docs-contract` failures predate `f71fef6c` (identical failing sets there).
- **Trace:** `tools/cp9/run_native_regressions.py` ~L22–29 selects the date harnesses with no residual entry; known-failure prose in `docs/state-contracts/R0003.md` ~L364, `R000F.md` ~L349, `R0021.md` ~L449, `R0026.md` ~L310, `R0027.md` ~L341.
- **Correction to a lane claim:** R0017's claim of healthy date-harness passes was true when made (green at `eebba178`); R000B later regressed them.
- **Script:** [probes/integrator/date_instruments.sh](probes/integrator/date_instruments.sh), results [instrument_results.txt](probes/integrator/instrument_results.txt).

<a id="pra-f-07"></a>
## PRA-F-07 — Pages payload estimate doubled past the qualified bound; verifier inert

- **Registry:** [ISM-BLD-003](../../../IMPLICIT_STATES.md#ism-bld-003), [ISM-BLD-004](../../../IMPLICIT_STATES.md#ism-bld-004). Lane ID: FND-F-01.
- **Evidence class:** demonstrated as an **estimate** (sum of git blob sizes minus the single `_config.yml` exclusion and dot/underscore paths — not a `_site` measurement): 0.898 GB at `06772824` (PR 62), 1.771 GB at `f71fef6c`, 1.910 GB at the baseline (9,686 files); re-derived by the integrator with [pages_payload_estimate.sh](probes/integrator/pages_payload_estimate.sh). The verifier's inertness is demonstrated from source. Lane F's served-evidence check (HTTP 200 for a 53 MB evidence ZIP) was not repeated. How GitHub enforces its published-site size limit is not verified.
- **Severity:** medium: deployment risk and an evidence-scope regression; Pages builds still succeed today (latest build `363c3e53` `built`).
- **Hard constraint:** truthful evidence claims (the ≤ 1 GB qualification is no longer re-measured); safety of the deploy path.
- **Origin:** introduced during the campaign: growth both before and after `f71fef6c`, mostly retained evidence (`docs/real-sky/evidence` 952.6 MB, `docs/rlgwo-execution` 748.2 MB, `docs/state-contracts/evidence` 133.5 MB, the last all added after `f71fef6c`).
- **Trace:** `.github/workflows/r0017-pages-payload.yml` L14 `if: github.event.pull_request.number == 62`; `tools/verify_r0017_pages_payload.py` ~L11–23 (`APPROVED`, `ALLOWED`) and ~L106 (bound); `_config.yml` excludes only `docs/rlgwo-execution/20261014/R000C/native`.

<a id="pra-f-08"></a>
## PRA-F-08 — Timezone adoption rebuilds the sky/Moon scene on routine boots; builder never emits `tz`

- **Registry:** [ISM-PRAY-009](../../../IMPLICIT_STATES.md#ism-pray-009), [ISM-SKY-001](../../../IMPLICIT_STATES.md#ism-sky-001), [ISM-MOON-002](../../../IMPLICIT_STATES.md#ism-moon-002), [ISM-MOON-005](../../../IMPLICIT_STATES.md#ism-moon-005), [ISM-CFG-007](../../../IMPLICIT_STATES.md#ism-cfg-007). Second-pass IDs: OM-01, OM-02.
- **Evidence class:** demonstrated by source trace and probe G `tz-identity-probe` (re-run): the builder hash for a Madinah draft has no `tz`, resolves to `America/New_York`, and the identity moves from `24.47|39.61|America/New_York|wall` to `24.47|39.61|Asia/Riyadh|wall` on adoption. The visible effect (re-pending or flash) is unobserved.
- **Severity:** medium. No prayer value changes. Cost: one redundant scene teardown per boot for every site whose zone differs from the hint, plus a discarded Moon/refined job and retirement of the one-shot initial Moon head.
- **Hard constraint:** separation of accepted and displayed state; the boot-presentation contract protected by the R0021 first-paint work.
- **Origin:** predates the campaign for the identity formula; `serialize` has never written `tz` (`src/native/config.js` L182–206 contain no `tz`).
- **Trace:** `skySceneIdentity` S:2217–2220 includes `tz`; `paint` S:3246 and `paintCelestialWithoutTimetable` S:3020 call `beginSkyScene(_skyInitialDocument)` on any identity change; `beginSkyScene` S:2225–2232 invalidates the Moon runtime, re-adds pending classes, removes `moon-ready` and withdraws the cloud receipt; `boot` calls `finishInitialSkyDocument()` at S:3827 before `loadPrayerData` (S:3846) writes `tz` (S:3676/S:3691); the warm cache is read after the yield too. The same `tz` enters `moonGeometryObservation` (S:2031), `SalahMoonHost.capture` (S:4171), `real-sky/native-host-hooks.js` ~L42 and the first-paint identity `real-sky/native-first-paint.mjs` ~L18 (`c.tz||'America/New_York'`). A broad `applyConfig` resets `tz` to the hint the form carries (S:686, S:4026), then adoption flips it again. Boot tests use a site whose zone equals the hint (`tests/real-sky/native-first-paint.test.mjs` ~L20, ~L61).
- **Open questions:** whether lifecycle coalescing hides the second scene; whether an ordinary wall-clock identity needs `tz` at all (UTC plus lat/lon determine the sky).

<a id="pra-f-09"></a>
## PRA-F-09 — No automated gate on main; merge is deploy

- **Registry:** [ISM-BLD-004](../../../IMPLICIT_STATES.md#ism-bld-004), [ISM-BLD-005](../../../IMPLICIT_STATES.md#ism-bld-005), [ISM-BLD-008](../../../IMPLICIT_STATES.md#ism-bld-008). Lane ID: FND-F-02.
- **Evidence class:** demonstrated (integrator trigger census: 32 workflow files; 30 `push` triggers on named work-order branches, 6 `workflow_dispatch`, one `pull_request` to main gated to PR 62; none on `push` to main).
- **Severity:** medium (architecture, observability).
- **Hard constraint:** truthful evidence; canonical source ownership (generated-file parity is not checked on main).
- **Origin:** introduced during the campaign in the sense that workflows grew from 1 (at `f71fef6c`) to 32 without a main gate.
- **Trace:** `.github/workflows/*.yml` `on:` blocks.

<a id="pra-f-10"></a>
## PRA-F-10 — In `timeScale`/clock-preview modes, forecast interpolation churns the refined-sky identity; stall unreported

- **Registry:** [ISM-WX-009](../../../IMPLICIT_STATES.md#ism-wx-009), [ISM-SKY-006](../../../IMPLICIT_STATES.md#ism-sky-006), [ISM-SKY-015](../../../IMPLICIT_STATES.md#ism-sky-015), [ISM-SKY-017](../../../IMPLICIT_STATES.md#ism-sky-017). Lane IDs: D-F01, D-F02.
- **Scope:** only when `syncWeather` substitutes forecast values, i.e. in `ADVANCING` (`timeScale`) or `_clockPreview` (`SalahClock` preview) modes (S:1573–1581; `selectedWeather` S:1380). Default real-time mode never substitutes (S:1579 returns unless `ADVANCING` or `_clockPreview`), so the churn described here does **not** occur in ordinary live use; D-F02's unused identity fields still withdraw the refined frame on each live weather adoption.
- **Evidence class:** demonstrated — *model-parameterised*: mechanism demonstrated with the real `NativeSkyLifecycle` module (probe re-run); real worker durations unmeasured (probe durations are parameters): with interpolated weather, 0 accepted results at rate 10 for 300 ms renders, at rates 2 and 10 for 800 ms, at every rate for 1200 ms; constant weather is accepted at every rate; `rate-throughput` is never reported. D-F02 (identity fields `rh`, `cloud`, `code`, `wind` not consumed by `nativeJob`, which reads only `vis`, `temp`, `src`) demonstrated from source.
- **Severity:** medium-low, confined to diagnostic and preview modes: optional astronomy only (prayer unaffected); in those modes the status shows "refining…" indefinitely and worker work is wasted.
- **Hard constraint:** truthful evidence/status claims.
- **Origin:** predates the campaign (`native-contract.mjs`, `native-lifecycle.mjs`, `wxAt`, `syncWeather` unchanged since `f71fef6c`). R0021/R0027 native runs used `simWx` or a current-only record, which bypass `syncWeather` (S:1574).
- **Trace:** `render` S:3485 → `syncWeather` S:1573–1581 → `wxAt` S:1556–1570 (new object each render); `real-sky/native-host-hooks.js` ~L42; `real-sky/native-contract.mjs` ~L8 (identity), ~L10–23 (job); `real-sky/native-lifecycle.mjs` ~L20–27 (rate-throughput only for the same epoch and identity).
- **Probe:** [probes/D/forecast-identity-probe.mjs](probes/D/forecast-identity-probe.mjs).

<a id="pra-f-11"></a>
## PRA-F-11 — Shipped app has no star-scintillation producer; docs and telemetry describe the old one

- **Registry:** [ISM-SKY-002](../../../IMPLICIT_STATES.md#ism-sky-002), [ISM-SKY-031](../../../IMPLICIT_STATES.md#ism-sky-031). Lane IDs: D-F06, NEW-D-05.
- **Evidence class:** demonstrated (source): `tools/build_native.py` L51–67 replaces the source starfield with a stub that empties `.stars/.starglints/.milkyway`; L84 hides them; `real-sky/native-contract.mjs` L20 sets `scintillation:{strength:0}`; no `scintill`/`twinkl` token in `native-star-preview.mjs`, `native-preview*.mjs` or `native-host.mjs`. `docs/real-sky/QUALIFICATION.md` ~L130–132 discloses that registered-star scintillation stays at the CP9 setting.
- **Severity:** medium for documentation and evidence truthfulness: AGENTS gate I ("anchors + their glints scintillate") and `DESIGN.md` L438–450 describe CSS twinkle; the `&debugMotion=1` star telemetry samples `.stars circle` (S:3631, S:3637), empty in the generated app, so it always reports `starΔ 0.000`. The visual effect was not observed in this audit.
- **Hard constraint:** truthful evidence claims.
- **Origin:** predates the campaign (`strength:0` since 2026-10-05).

<a id="pra-f-12"></a>
## PRA-F-12 — Moon worker failure is terminal for the page; retry unowned; cached 404

- **Registry:** [ISM-MOON-004](../../../IMPLICIT_STATES.md#ism-moon-004), [ISM-MOON-005](../../../IMPLICIT_STATES.md#ism-moon-005), [ISM-MOON-007](../../../IMPLICIT_STATES.md#ism-moon-007), [ISM-MOON-008](../../../IMPLICIT_STATES.md#ism-moon-008), [ISM-MOON-018](../../../IMPLICIT_STATES.md#ism-moon-018). Lane IDs: EF-E02, NEW-E-03, EF-E10, EF-E11.
- **Evidence class:** demonstrated: `retry()` (`moon/src/moon-native.mjs` L282) has no product caller (integrator `git grep`: only `tools/cp9/*_check.py` and `tools/qa/run_r0021_native.py`); `failed()` closes the worker; `moon/src/moon-worker.mjs` L6 fetches with `cache:'force-cache'`; R0021 contract G item 4 records Firefox 153 serving a cached 404 to every retry (cell b21). EF-E10 (sticky `initialError`) and EF-E11 (240 s deadline against a 169 s observed Firefox run) are plausible risks.
- **Severity:** medium: a quality degradation that is silent to the user; if the initial V5 tier also fails, the slot is empty.
- **Hard constraint:** AGENTS gate D (Moon meaningfully present every night) in the fault path.
- **Origin:** predates the campaign (`force-cache` since 2026-10-07; no product retry caller at `f71fef6c`).

<a id="pra-f-13"></a>
## PRA-F-13 — Empty Moon slot after a wrapper failure; light not bound to the visible surface

- **Registry:** [ISM-MOON-016](../../../IMPLICIT_STATES.md#ism-moon-016), [ISM-MOON-017](../../../IMPLICIT_STATES.md#ism-moon-017), [ISM-MOON-020](../../../IMPLICIT_STATES.md#ism-moon-020), [ISM-MOON-001](../../../IMPLICIT_STATES.md#ism-moon-001), [ISM-MOON-014](../../../IMPLICIT_STATES.md#ism-moon-014). Lane IDs: EF-E03, EF-E04, EF-E05, EF-E07.
- **Evidence class:** demonstrated for an injected failure natively (R0021 contract §F, `moon-construction` cells, Chromium and Firefox) and by trace: `moon-native.mjs` L298 clears the slot; S:2238 requires `SalahMoonRuntime.surface()`; the rethrow skips `SalahMoonHead`/`SalahPrepareFirstPaint` (`tools/build_moon.py` ~L120–129) and the refinement tail's `installWorkerSource` (`tools/build_moon.py` ~L130) throws a TypeError. EF-E05 (light eligibility uses `_pbrFailed`, unreachable while a runtime exists, S:2990–3003, S:1898) is a plausible risk.
- **Severity:** medium (fault path only); prayer is unaffected (separate scripts).
- **Hard constraint:** AGENTS forbidden regressions "empty moon slot" and "never faked light".
- **Origin:** unknown — recorded during R0021 (issue 33); pre-R0021 behaviour under the same injected failure was not compared.

<a id="pra-f-14"></a>
## PRA-F-14 — `SalahClock` preview discarded on zone adoption

- **Registry:** [ISM-PRAY-001](../../../IMPLICIT_STATES.md#ism-pray-001), [ISM-PRAY-009](../../../IMPLICIT_STATES.md#ism-pray-009). Lane ID: A-F02.
- **Evidence class:** demonstrated (probe A P2 re-run: requested 2026-12-25T03:00Z, observed 2026-09-07T12:00Z, `_clockPreview:true`).
- **Severity:** low (diagnostic API), but `tools/cp9/celestial_lifecycle_check.py` ~L37 and `daytime_composition_check.py` ~L56 use it; whether they pass an explicit `tz` was not checked.
- **Hard constraint:** truthful evidence claims.
- **Origin:** predates the campaign.
- **Trace:** `SalahClock.set` S:3769–3770 sets `_simBase=utcMs`, `_simTz=tz`; a loader `tz` write (S:3691 / S:1213); `simNow` S:1014 sees `_simTz!==tz` → `initSim` S:999–1008 uses `Date.now()` when there is no `simTime`.

<a id="pra-f-15"></a>
## PRA-F-15 — Diagnostics with side effects or misreported outcomes

- **Registry:** [ISM-SKY-031](../../../IMPLICIT_STATES.md#ism-sky-031), [ISM-SKY-020](../../../IMPLICIT_STATES.md#ism-sky-020), [ISM-MOON-003](../../../IMPLICIT_STATES.md#ism-moon-003), [ISM-WX-001](../../../IMPLICIT_STATES.md#ism-wx-001), [ISM-CFG-005](../../../IMPLICIT_STATES.md#ism-cfg-005). Lane IDs: F-C08, EF-E06, D-F08, BF02; OM-05.
- **Evidence class:** demonstrated: (a) `qaState()` calls `storageAvailable()` (S:3587 → `src/native/config.js` L211–218), a `setItem/removeItem` write; (b) the Moon getters `surface()`, `state` and `detailEnabled` call `presentation()`, which adopts a waiting preview and publishes (`moon-native.mjs` L89, L275–283; `moon/tests/host.test.cjs` ~L94 asserts it), and `qaState().moonTruth` reads them (S:3608); (c) `reconcileClouds()` used as a renderer capture step can withdraw cloud state and repaint the header (S:2730–2747, `real-sky/native-composition.mjs` ~L132); (d) `wxFetchJson` records `received` for any parsed body (S:1428) while `fetchWeather` silently returns on `error:true`, missing records or nothing admitted (S:1458–1473) — the probe B outcome re-run shows `state:"received", reason:null` for `{error:true}`, `{}` and an invalid current; (e) `_autoDetectStatus` stays `pending` when a newer generation supersedes boot detection (S:3794–3796), Reset's detection never updates it, and `_geoLastError` is cleared only by a successful GPS read (OM-05).
- **Severity:** low; observability only — admission stays correct.
- **Hard constraint:** truthful evidence claims (`qaState` is cited as qualification evidence).
- **Origin:** predates the campaign for (a), (b), (d); (c) introduced by R000B (`ea9f8300`).

<a id="pra-f-16"></a>
## PRA-F-16 — Radar acquired with no product consumer; manifest host unvalidated

- **Registry:** [ISM-WX-004](../../../IMPLICIT_STATES.md#ism-wx-004). Lane ID: BF04.
- **Evidence class:** demonstrated for the consumers (only `radarEvidence` S:1482–1488 and `qaState` S:3554–3559 read `weatherRadar`); plausible risk for the host (S:1530, S:1541 concatenate the manifest `host`; the probe dispatched an image to an `http://` host; no meta CSP).
- **Severity:** low. A manifest plus a zoom-6 tile request every 10 minutes sends the tile location to a third party with no product benefit.
- **Hard constraint:** privacy boundary.
- **Origin:** predates the campaign.

<a id="pra-f-17"></a>
## PRA-F-17 — Location data retention: unbound `siteElev`; per-location caches never evicted

- **Registry:** [ISM-WX-008](../../../IMPLICIT_STATES.md#ism-wx-008), [ISM-SKY-028](../../../IMPLICIT_STATES.md#ism-sky-028), [ISM-CFG-002](../../../IMPLICIT_STATES.md#ism-cfg-002), [ISM-WX-001](../../../IMPLICIT_STATES.md#ism-wx-001). Lane ID: BF03; second-pass OM-03.
- **Evidence class:** demonstrated (source): the `siteElev` writer S:1467 needs no eligible current or target binding and `resetForNewLocation` (S:3717–3726) does not reset it (readers S:3083, S:3192); the CP9 copy is fenced. The only `removeItem` calls are `clearLocal` (`config.js` L247, config key only) and the storage probe (L215), so `salah:<lat>|<lon>|…` and `salahwx:<lat>|<lon>|<units>` keys accumulate and survive Reset. Quota coupling with config persistence is speculative.
- **Severity:** low-medium: privacy (coordinates in key names; the README discloses that Reset leaves caches) and a small visual carry-over of elevation.
- **Hard constraint:** truthful location provenance; privacy.
- **Origin:** predates the campaign.

<a id="pra-f-18"></a>
## PRA-F-18 — Frozen v1 limitations undocumented; `--check-pages` fails; README V1 snippet 330×534

- **Registry:** [ISM-V1-002](../../../IMPLICIT_STATES.md#ism-v1-002), [ISM-V1-006](../../../IMPLICIT_STATES.md#ism-v1-006), [ISM-BLD-010](../../../IMPLICIT_STATES.md#ism-bld-010), [ISM-CFG-010](../../../IMPLICIT_STATES.md#ism-cfg-010). Lane IDs: F-C09, FND-F-08, F-C03; original CF07–CF09.
- **Evidence class:** demonstrated: `git diff f71fef6c 363c3e53 -- v1` is empty; v1 is served under the root Pages build and advertised (README ~L556–575); neither `docs/V1_PRESERVATION.md` nor `v1/VERSION.json` records CF07–CF09; `python tools/verify_v1.py --check-pages` prints "FAIL: New Jekyll configuration requires V1 inclusion review" while `docs/V1_PRESERVATION.md` L93 prescribes it (`_config.yml` added in `02ab7a93`, R0017); README L570 has `width:330px;height:534px` and L575 says "For the current version, change only `src`".
- **Severity:** low-medium. CF08 (v1 Reset claims deletion after removal fails) is a control-truth issue on a live surface; the snippet contradicts the AGENTS 325×530 rule for the current version.
- **Hard constraint:** truthful evidence claims; the 325×530 embed contract; frozen-v1 authority (any byte change needs owner authority).
- **Origin:** the v1 limitations predate the campaign; the `--check-pages` failure was introduced during it (R0017, `02ab7a93`); the snippet predates it (since `37084ae7`).

<a id="pra-f-19"></a>
## PRA-F-19 — Generator partial states, `assert` guards and stale chunks

- **Registry:** [ISM-BLD-001](../../../IMPLICIT_STATES.md#ism-bld-001), [ISM-BLD-002](../../../IMPLICIT_STATES.md#ism-bld-002). Lane IDs: FND-F-03, FND-F-04, FND-F-05, FND-F-06; original projection G01.
- **Evidence class:** demonstrated: write order confirmed by the integrator (`tools/build_native.py` writes `index.html` at L83 and `offline.html` at L109 before `build_moon` at L113, which can raise); `assert` guards at `tools/build_native.py` L70 and `tools/native_star_bootstrap.py` L14, L18, L26 (lane F cited L16/L21/L28; corrected); lane F probes in a disposable copy showed that `-O` turns a manifest-drift failure into rc 0 and that a Moon failure leaves unexpanded entries (not re-run by the integrator). Unguarded `replace(...,1)` no-ops (~L72–82) are a plausible risk.
- **Severity:** low-medium: a commit of a partial state would deploy a Moon-less widget (see PRA-F-09: no gate).
- **Hard constraint:** canonical source and mutation ownership.
- **Origin:** predates the campaign (the original G01 direction was never taken).

<a id="pra-f-20"></a>
## PRA-F-20 — Units/lp/seed stay broad; `seed` has two authorities

- **Registry:** [ISM-CFG-001](../../../IMPLICIT_STATES.md#ism-cfg-001), [ISM-CFG-006](../../../IMPLICIT_STATES.md#ism-cfg-006). Lane IDs: BF06, F-C06; XF01 residual.
- **Evidence class:** demonstrated (source): `CONFIG_EFFECTS.units` has `path:"broad"` (S:707), which restarts prayer, weather and radar; renderer seeds read the fragment (S:2190, S:2759, S:2772), not `CONFIG.seed`.
- **Severity:** low (efficiency); owner-deferred (R0003 D3/D4). Not a defect claim.
- **Origin:** XF01 partly resolved by R0003; the residual predates it.

<a id="pra-f-21"></a>
## PRA-F-21 — Unreachable `data-stale="prayer"`; mirror flags; unused model fields

- **Registry:** [ISM-PRAY-004](../../../IMPLICIT_STATES.md#ism-pray-004), [ISM-PRAY-005](../../../IMPLICIT_STATES.md#ism-pray-005). Lane ID: A-F04.
- **Evidence class:** demonstrated (probe A P5 re-run; source). The only writer, S:3518, is on the model branch, unreachable while stale (S:2329–2331 → `!M` branch); the staletag still discloses staleness; `warmEnd`/`needTomorrow` (S:2386, S:2392) have no reader; `_rolloverBusy`/`_rolloverNextTry`/`fetchingTomorrow` duplicate slot state and feed only `qaState` (S:3577).
- **Severity:** low; redundant state raises drift risk. Any visual change needs owner approval.
- **Disposition (R002E, issue 95, amendment R002E-A2).** The stale marker is **reachable in one clock-step-back interleaving; retained**: when the device wall clock steps back across civil midnight between `maintainPrayerDay` and `render` within one loop frame, `render` publishes the model with `data-stale="prayer"` for that frame and the next frame clears it ([R002E](../../state-contracts/R002E.md) §1.1; pinned by `tests/prayer-presentation-residuals.test.cjs`). The rule and its writer are kept unchanged. "Unreachable" above is corrected accordingly. The mirror-flag part is kept and enforced consistent by test; `warmEnd`/`needTomorrow` are kept as instrument seams (not unused by instruments).

<a id="pra-f-22"></a>
## PRA-F-22 — Preview host lifecycle asymmetries

- **Registry:** [ISM-SKY-017](../../../IMPLICIT_STATES.md#ism-sky-017), [ISM-SKY-030](../../../IMPLICIT_STATES.md#ism-sky-030), [ISM-SKY-009](../../../IMPLICIT_STATES.md#ism-sky-009). Lane IDs: D-F04, D-F05, NEW-D-03.
- **Evidence class:** demonstrated (source, read by the integrator at `real-sky/native-preview-host.mjs` ~L120–128 and ~L164–190): in bare mode the preview's own `tick` calls `present` → `update` → `clear` (cloud reconcile, Moon detail clear, class writes) every frame; a healthy `dispose` does not run its `owned` releases, leaving `window.SalahSkyPreview` set (only the constructor `catch` releases; no shipped caller); the preview has no pagehide/pageshow participation.
- **Severity:** low.
- **Hard constraint:** instance-owned disposal (latent).
- **Origin:** the per-frame clear predates; the dispose asymmetry arose with R0021's custody pattern (issue 33).

<a id="pra-f-23"></a>
## PRA-F-23 — Countdown fit key incomplete (NH01)

- **Registry:** [ISM-PRAY-007](../../../IMPLICIT_STATES.md#ism-pray-007). Lane ID: A-F07.
- **Evidence class:** plausible risk. The key (S:3407) omits rail `d`, noon and declination; `resetForNewLocation` does not clear `_cnFit`. Visual magnitude unmeasured.
- **Origin:** predates.

<a id="pra-f-24"></a>
## PRA-F-24 — Backward device clock: weather refetched each minute but never admitted

- **Registry:** [ISM-WX-003](../../../IMPLICIT_STATES.md#ism-wx-003). Lane ID: A-F08.
- **Evidence class:** plausible risk. `weatherEligibility` requires `sourceAge>=0` (S:1375); `retryGate` opens every 60 s of elapsed time (S:1272–1279). Bounded and truthful; whether it is intended is unknown.
- **Origin:** introduced by R000D's elapsed spacing, which resolved XF02's stranded retry.

<a id="pra-f-25"></a>
## PRA-F-25 — Preview forecast substitution has no track-age bound

- **Registry:** [ISM-WX-009](../../../IMPLICIT_STATES.md#ism-wx-009). Lane ID: BF08.
- **Evidence class:** plausible risk. `wxAt` checks only the target (S:1557); fetches are suppressed while ADVANCING (S:3875). The output stays labelled as a preview.

<a id="pra-f-26"></a>
## PRA-F-26 — Moon refinement cadence, hide/show discard and resource footprint

- **Registry:** [ISM-MOON-019](../../../IMPLICIT_STATES.md#ism-moon-019), [ISM-MOON-012](../../../IMPLICIT_STATES.md#ism-moon-012), [ISM-MOON-015](../../../IMPLICIT_STATES.md#ism-moon-015). Lane IDs: EF-E08, EF-E09.
- **Evidence class:** plausible risk. EF-E08 (each hide/show discards a valid refined surface and re-runs the adaptive pipeline; `host.test.cjs` ~L289 asserts it, intentionally truth-first) is demonstrated as behaviour; EF-E09's restart interval (about 4–12 min) is a model estimate only; four WASM shards per worker, each with a ≤ 512 MiB ceiling and non-shrinking pages (`moon/src/moon_kernel.c` ~L25). Nothing was measured.
- **Severity:** low-medium efficiency; no whole-widget budget exists.

<a id="pra-f-27"></a>
## PRA-F-27 — Closure state split between repository and issue comments

- **Registry:** [ISM-BLD-005](../../../IMPLICIT_STATES.md#ism-bld-005). Lane ID: FND-F-09.
- **Evidence class:** demonstrated: `docs/state-contracts/R0015.md` L221, L335 and L450 say `wholeContractComplete` remains false, while certificate 6828391831 (binding `363c3e53`) records ES15-18 met and says the in-repository ledger describes the state at its commit; R0015 was auto-closed by a merge keyword and reopened (6816192574); an R0017 certificate was withdrawn (6703510170); R000D has a post-closure correction (6792330574). Lane F cited R0015.md L449; the line is L450.
- **Severity:** low (observability).

<a id="pra-f-28"></a>
## PRA-F-28 — README pin ↔ installer ↔ docs-receipt coupling

- **Registry:** [ISM-BLD-006](../../../IMPLICIT_STATES.md#ism-bld-006). Lane ID: FND-F-10.
- **Evidence class:** demonstrated: README L92–117 pins `a4c617eb`; `tools/qualification/installer_preview_docs.cjs` L18–20 pins the README, builder and config hashes; the README L59/L63 pipe routes follow `main` unpinned.
- **Severity:** low (architecture): any installer change cascades into re-pins and a new documentation receipt.

<a id="pra-f-29"></a>
## PRA-F-29 — GPS adoption awaits an unbounded `permissions.query`

- **Registry:** [ISM-WX-012](../../../IMPLICIT_STATES.md#ism-wx-012). Lane ID: BF07. **Speculative**: S:4111 awaits `permissionState()` (`config.js` ~L321–327, no timeout) before applying a fix; no known browser leaves it unsettled.

<a id="pra-f-30"></a>
## PRA-F-30 — Nominatim `class`/`category` naming may make place preference inert

- **Registry:** [ISM-WX-011](../../../IMPLICIT_STATES.md#ism-wx-011). Lane ID: BF09. **Speculative**: `_nomCands` filters on `r.class` (`config.js` ~L374); the R0026 contract (~L239–240) leaves the naming unresolved; no provider was contacted.

<a id="pra-f-31"></a>
## PRA-F-31 — Two lunar-light producers can diverge under `simMoon*`

- **Registry:** [ISM-MOON-020](../../../IMPLICIT_STATES.md#ism-moon-020). Lane ID: D-F10. **Speculative**: native `lunarPresentation` honours `simMoon*`; the worker's physical Moon uses the real ephemeris; `nativeJob` carries no lunar override. Diagnostic scenes only.

<a id="pra-f-32"></a>
## PRA-F-32 — Header shows a model condition while clouds are withheld without a timetable

- **Registry:** [ISM-WX-002](../../../IMPLICIT_STATES.md#ism-wx-002), [ISM-WX-005](../../../IMPLICIT_STATES.md#ism-wx-005). Lane ID: BF05. **Plausible risk**: S:3488 paints the header from the decision; S:2703 retains clouds only with `model()!==null`; the R000B certificate §5 records "Rain 24°" with no clouds and leaves its materiality unknown. This is cross-consumer divergence, not a false claim (the header is labelled a model estimate).

<a id="pra-f-33"></a>
## PRA-F-33 — `_commitSettings` fires `applyConfig` without a rejection handler

- **Registry:** [ISM-CFG-001](../../../IMPLICIT_STATES.md#ism-cfg-001). Lane ID: F-C07. **Plausible risk**: S:4103; an exception after `saveLocal` becomes an unhandled rejection with prayer/weather possibly half-reset.

<a id="pra-f-34"></a>
## PRA-F-34 — Per-compose allocations and PNG mask encode

- **Registry:** [ISM-SKY-015](../../../IMPLICIT_STATES.md#ism-sky-015), [ISM-SKY-016](../../../IMPLICIT_STATES.md#ism-sky-016). Lane ID: D-F09. **Speculative as a performance problem**: the allocation pattern is visible in source (`real-sky/native-host.mjs` ~L181, ~L193, ~L253; `native-composition.mjs` ~L74, ~L127–128, ~L154–156), but nothing was measured. An optimisation opportunity is not evidence of poor performance.

<a id="pra-f-35"></a>
## PRA-F-35 — R0007 native acceptance rests on cross-run reuse

- **Registry:** [ISM-PRAY-005](../../../IMPLICIT_STATES.md#ism-pray-005). Lane ID: A-F09. **Demonstrated (documentary)**: hosted Firefox run 42953929662 concluded FAILURE/PARTIAL (2 healthy cells `OBSERVATION_NOT_ACCEPTED`, 3 mutants `MUTANT_NOT_QUALIFIED`); the certificate accepts those rows by cross-run reuse (`docs/state-contracts/R0007.md` ~L230, ~L240). Disclosed; not a product defect.

<a id="pra-f-36"></a>
## PRA-F-36 — Mask decode has no wall-clock bound (RF04)

- **Registry:** [ISM-SKY-016](../../../IMPLICIT_STATES.md#ism-sky-016). Lane ID: D-F11. **Plausible risk**, retained UNVERIFIED by owner decision in R0021; no never-settling decode was reproduced.

<a id="pra-f-37"></a>
## PRA-F-37 — Duplicated renderer-boundary formulas and geometry literals

- **Registry:** [ISM-SKY-019](../../../IMPLICIT_STATES.md#ism-sky-019), [ISM-CFG-010](../../../IMPLICIT_STATES.md#ism-cfg-010). Second-pass IDs: OM-06, OM-07.
- **Evidence class:** demonstrated (source): `real-sky/native-first-paint.mjs` ~L15 uses `Number(params.get(k))` (a blank `#skyAz=` becomes 0) while the native `cameraNumber` makes it `NaN` and `nativeIdentity` throws; `simDate` (not a native parameter) suppresses first paint; reduced-motion and identity formats are re-derived; the 325×530 geometry is a literal in many modules (S:482–554, S:2072, S:2088, S:2986; `real-sky/native-contract.mjs` ~L20 and others) with no shared constant. Values agree at the baseline; impact speculative.
- **Severity:** low (maintainability; diagnostic parameters).

<a id="pra-f-38"></a>
## PRA-F-38 — Diagnostic `sim*` overrides accepted from any embed URL; visible header carries no SIM marker

- **Registry:** [ISM-CFG-011](../../../IMPLICIT_STATES.md#ism-cfg-011), [ISM-WX-002](../../../IMPLICIT_STATES.md#ism-wx-002), [ISM-WX-003](../../../IMPLICIT_STATES.md#ism-wx-003). Found by the independent review; derived and traced by the integrator.
- **Evidence class:** demonstrated by source trace for the mechanism; reachability requires a hand-written fragment (the builder never emits these parameters). Not observed in a browser.
- **Severity:** low. `AGENTS.md` documents `simWx`, `simTime`, `simMoon*`, `debugOptic` and `qa=1` as intended debugging recipes; the concern is only that nothing confines them to debugging.
- **Hard constraint:** truthful weather provenance; separation of accepted and displayed state.
- **Origin:** predates the campaign (the `SIM` object and its consumers exist at `f71fef6c`).
- **Trace:** `SIM` is read from the fragment of any load (S:769–784); with `simWx` set, `startWeather` installs a synthetic record `src:"sim"` (S:3654–3665), `retryGate` returns `suppressed-by-mode` (S:1273) so no real weather is fetched, and `selectedWeather` returns the record without age checks (S:1380). The header's accessible label reads "SIM weather preview: …" (S:1823), but the visible text is only the icon (`#wi`) and temperature (`#wt`, S:1833); the `.simclock` read-out appears only in explicit clock modes (S:3774). An embed whose `src` carries `#…&simWx=95` would therefore show a thunder condition indefinitely with provenance only in the tooltip/ARIA label.
- **Open questions:** whether any deployed embed carries these parameters; whether the owner wants them gated (an owner decision; AGENTS.md treats them as features).

