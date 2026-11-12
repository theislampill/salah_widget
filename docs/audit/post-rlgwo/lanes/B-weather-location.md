> **Lane working paper.** This is supporting detail produced by one census lane of the post-RLGWO audit at baseline `363c3e53`. It is superseded by [IMPLICIT_STATES.md](../../../../IMPLICIT_STATES.md), [REPORT.md](../REPORT.md), [CROSSWALK.md](../CROSSWALK.md) and [FINDINGS.md](../FINDINGS.md) wherever they differ; the integrator's corrections are listed in REPORT.md. Probe paths `probes/<lane>/` refer to [../probes/](../probes/README.md).

# Lane B — weather, radar, location/geocoding and their async request ownership

Baseline audited: `363c3e53` (worktree `post-rlgwo-audit`). Historical reference: `f71fef6c`. Authored sources
`src/native/index.html`, `src/native/config.js`. Generated parity: root `config.js` is byte-identical to
`src/native/config.js`; in root `index.html` the weather region (`// ---- weather (Open-Meteo:` … `// ---- accurate Moon position`)
differs from the authored one only by the CP9 `acceptedElevation` hook injected by `tools/build_native.py:69-71`; the
gate/cloud-authority, `startWeather`, `resetForNewLocation`, settings and `startRenderLoop` regions are identical.
Line numbers below are `src/native/index.html` unless prefixed `config.js:` (authored = generated for config.js).
Request/attempt ownership (N03, `beginRequest`/`beginAttempt`/`beginRuntimeGeneration` L1068-1112) is treated as an
interface owned by another lane; it is used here as evidence.

## 1. Machine census

### N08 — Weather acquisition, current/hourly records and persistent cache
- **Scope / decision:** whether a current-model record and an hourly track exist for the current target, and whether a provider request is issued.
- **Sources:** `weather`,`lastWxAt`,`lastWxTry`,`wxBusy` L1263; admission `wxValue`/`wxUnitsMatch`/`wxResponseZoneMatches`/`wxEpoch`/`admitWeatherRecord`/`admitWeatherTrack` L1300-1368; `weatherEligibility`/`selectedWeather` L1369-1383; `loadWx` L1405-1413; `wxFetchJson` L1414-1445; `fetchWeather` L1446-1476; `startWeather` L3652-3667; `resetForNewLocation` L3717-3726; loop poll L3875. Generated: same + CP9 elevation hook.
- **State dimensions:** current record {none, admitted-eligible, admitted-ineligible(expired/future/other target), sim, forecast-derived}; track {none, admitted}; request slot {free, owned}; attempt stage {fetch, body, settled}; cache envelope {absent, within 6 h retention, rejected}; `_wxRetry.weather` (NEW-B-01).
- **Events/transitions:**

| Event | Guard | Effect |
|---|---|---|
| boot/apply `startWeather` | — | `loadWx` re-admits cached `{w,ts}` (receipt ≥0, <6 h, `w.retrievedAt===ts`) under current target; sets `lastWxAt` only if eligible (L1407-1411) |
| ~30 s visible poll (L3875), boot (L3845), apply (L3666) | `retryGate==="eligible"` | `beginRequest("weather")` → `beginAttempt(10 s)` → fetch |
| body received | `attemptEligible` after fetch and after `json()` (L1437,1441) | admission of current and track independently (L1462-1463) |
| admitted current | eligible, or old record not eligible (L1468) | replace `weather`, cache write under captured key (L1471) |
| admitted track | `attemptEligible` (L1473) | replace `weatherTrack` |
| timeout/abort/HTTP/parse | one-shot `finish` (L1424-1431) | attempt expired, slot released in `finally` (L1475) |
| generation change | `beginRuntimeGeneration` (L1101-1112) | old attempt cancelled+aborted, slots cleared, `wxBusy=false` |
| location/broad config change | `resetForNewLocation` (L3719-3720) | clears records, receipts, retry records (not `siteElev`, see NEW-B-05) |

- **Guards:** finite in-range coordinates (L1300); captured units/zone/target; response timezone must resolve equal (L1321-1326); hourly epochs strictly increasing (L1357); codes in closed set (L1294).
- **Actors/ownership:** request slot + attempt (N03); `fetchWeather` sole network writer; `loadWx` sole cache reader; `syncWeather` (NEW-B-06) and `startWeather` SIM branch (L3654-3665) also write `weather`.
- **Effects:** `weather`, `weatherTrack`, `siteElev`, `lastWxAt`, localStorage `salahwx:lat|lon|units`, `_renderDirty`, `_wxRequests.weather` diagnostic.
- **Invariants:** receipt is not freshness (source and receipt ages both 0…900 000 ms, L1374-1375); forecast never overwrites live current in real time (L1579); cache uses the same admission (L1410); missing quantities stay null with an `admission` reason (L1344).
- **Failure/retry:** 10 s absolute elapsed deadline per attempt; 60 s elapsed retry spacing; existing record retained only if still eligible.
- **Stale/concurrent risks:** late body after generation change rejected by `attemptEligible`; a replacement is only requested after the current record has already expired (BF01); rejected 200 bodies are recorded as `received` (BF02).
- **Enforcement:** documentation — state contracts R000B, R000D + comments; implementation — partly explicit (slots/attempts explicit, record lifecycle implicit); verification — unit tests + mutation controls + native (R000D Chromium/Firefox; R000B hosted Chromium).
- **Tests:** `tests/r000c-weather.test.cjs` (admission, malformed values), `tests/r000d-weather.test.cjs` (deadlines, supersession), `tests/r0024-response-zone.test.cjs` (zone), `tests/r0024-weather.test.cjs`, `tests/weather-retry-clock-*.test.cjs`.
- **Observed facts:** both ages checked with zero future allowance (L1374-1375); retry shortcut requires the current record to be selected (L1276); no refresh can start while the record is selected (probe `wx-quarter-gap-probe`).
- **Hypotheses:** provider `current.time` advances in 15-min steps equal to the 900 s TTL, so every record lapses at a quarter-hour boundary (corroborated by the R000B certificate's delivered-page sampling).
- **Unknowns:** provider response-size bound; real CORS/storage partitioning behaviour; behaviour of `_RAFNOW` across OS sleep (R000D limit).

### N09 — Weather truth/decision, information text and header publication
- **Scope / decision:** what condition, permissions (rain/snow/lightning) and header text the widget claims.
- **Sources:** `wxInfo` L1601-1614; fixture lane `weatherPointTarget`/`admitWeatherFixture`/`weatherFixtureEligibility` L1619-1681; `weatherForecast` L1682-1688; `reconcileWeatherEvidence` L1690-1717; `weatherDecision` + `_wxDecisionCache` L1718-1745; `weatherInformation` L1747-1811; `weatherHeader`/`paintWeatherHeader` L1818-1838; model gate `gateWeatherCode`/`wxClass` L2609-2637.
- **State dimensions:** lane {live, preview, simulation-fixture}; condition {unavailable, model-estimated-*, preview-*, supported-*/conflicting/unknown (fixture)}; decision cache {valid until earliest warrant, recompute}; header sink {painted value}.
- **Transitions:** decision recomputed when target/current/track/synthetic/preview identity changes or `now` leaves `[at,until)` (L1721); `until` = min(current source+TTL+1, receipt+TTL+1, fixture/spatial/approach/forecast bounds) (L1740-1743). Header painted from one decision in `render` (L3483, L3488), in `paint` (L3310) and on withdrawal (L2739).
- **Guards:** live lane present-evidence adapter is closed (`weatherSynthetic` is null in production; no setter outside tests) (L1620,1700); lightning only from qualified fixture or explicit `simWx` thunder (L1713); live rain/snow visual only with model interval amount ≥0.05 mm, thunder ≥0.8 mm (L2609-2624, L1731-1733).
- **Effects:** `#wi`/`#wt`/`#weather-information` text and ARIA (L1832-1836); `_lastWeatherHeader`.
- **Invariants:** model estimate always labelled as such with "direct local observation unavailable" (L1779, L1822); unavailable is not clear (L1738, L1821); radar grants nothing.
- **Failure/recovery:** expiry is evaluated on every decision (no acquisition dependency); the header recovers independently of prayer data (L3488).
- **Risks:** header can say a model condition (e.g. Rain) while clouds/particles are withheld without a timetable (BF05).
- **Enforcement:** documentation — R000B, R0024 contracts, `AGENTS.md` truth rules; implementation — partly explicit (pure decision + receipt objects); verification — unit + mutation + native (Chromium withdrawal cells; delivered-page natural expiry observed by root only).
- **Tests:** `tests/r0024-information.test.cjs`, `tests/r0024-weather.test.cjs`, `tests/weather-withdrawal-authority.test.cjs`, `tests/weather-withdrawal-mutations.test.cjs`, `tests/weather-no-timetable-*.test.cjs`, `tests/hotfix-prayer-weather.test.cjs`.
- **Observed facts:** `_wxDecisionCache` rejects `now<cache.at`, so a backward wall correction forces recomputation (L1721).
- **Hypotheses:** none beyond BF05.
- **Unknowns:** native readability of the long accessible label (not examined).

### NEW-B-01 — Weather/radar elapsed retry eligibility (R000D)
- **Scope:** when a replacement request may start.
- **Sources:** `_WX_RETRY`, `_wxRetry`, `retryClockDomain`, `retryGate`, `retryDiagnostics` L1264-1286; stamps L1453, L1526; reset L3720; poll L3875.
- **States:** per source `_wxRetry[kind]` {null = never attempted, {startedAt elapsed, clock}}; derived gate {suppressed-by-mode, target-ineligible, active-owned-attempt, fresh-data-satisfied (weather), cooldown, eligible}.
- **Transitions:** attempt start stamps elapsed; gate opens at `elapsed-startedAt >= 60 000 / 600 000` (inclusive); location/broad change clears both; reload starts unset (never persisted).
- **Guards:** order SIM → target → busy → shortcut → spacing → slot (R000D "Protected invariants").
- **Invariants:** wall corrections do not move spacing when `performance.now` exists; UTC source/receipt ages unchanged; `lastWxTry`/`lastRadarAt` are write-only compatibility fields.
- **Failure:** without `performance.now`, degraded wall fallback disclosed in `qaState().wxTruth.retry` (L1284-1285).
- **Risks:** shortcut still compares wall `now-lastWxAt` (L1276) but only while the record is selected, so a backward step cannot hold it (selection fails on negative age).
- **Enforcement:** documentation — `docs/state-contracts/R000D.md`; implementation — explicit and enforced; verification — unit 23 + mutation 12 + native Chromium 148/Firefox 153 + independent delta review (R000D.md L154-205).
- **Tests:** `tests/weather-retry-clock-state.test.cjs`, `tests/weather-retry-clock-mutations.test.cjs`.
- **Observed facts / Hypotheses / Unknowns:** facts as above; no hypotheses; OS sleep/background resume unknown (R000D.md L188-189).

### N10 — Radar diagnostic transport, image lease and expiry
- **Scope:** acquisition of a RainViewer mosaic sample that is diagnostic only.
- **Sources:** `weatherRadar`,`lastRadarAt`,`radarBusy`,`_RADAR_*` L1477-1481; `radarEvidence` L1482-1488; `radarPrecipNow` (constant 0) L1489; `wxRadarSample` L1490-1519; `fetchRadar` L1520-1552; consumer `qaState().wxTruth` L3554-3559.
- **States:** manifest {fetching, body, settled}; image {loading, decoded, timeout/error/cancelled}; sample {none, available (frame and receipt ≤20 min, same target), stale}; retry (NEW-B-01).
- **Transitions:** manifest attempt (10 s) → `finishAttempt` → new image attempt (10 s) (L1543) → canvas 7×7 sample → `weatherRadar` replaced; any failure keeps the prior frame, which then expires by TTL.
- **Guards:** finite frame/index seconds and Date-range check (L1533-1536); Web-Mercator finite tile (L1539); `attemptEligible` at load, after canvas (L1506,1512).
- **Effects:** `weatherRadar` record only; no header, ARIA, `data-*`, particle or permission consumer (grep: only L1482-1488 and L3554-3559 read it; nothing in `real-sky/` or `moon/src/`).
- **Invariants:** alpha is never precipitation/lightning evidence (L1477-1479, L1489).
- **Failure:** image handlers detached on finish (L1497); physical download may continue (comment L1490).
- **Risks:** manifest `host` accepted as any string — no scheme/host allowlist, no page CSP (BF04); rejected manifests recorded as `received` (BF02).
- **Enforcement:** documentation — comments + R000D (ES0D-14 consumer scope); implementation — partly explicit (gate explicit; sample lifecycle implicit); verification — unit tests + native admitted-state only (no visible consumer exists).
- **Tests:** `tests/r000d-weather.test.cjs`, `tests/r000c-weather.test.cjs`, `tests/r0017-transport.cjs`.
- **Observed facts:** radar refresh runs every 10 min in live mode with zero product consumers. **Hypotheses:** retained for a future qualified decoder. **Unknowns:** browser reclamation of detached images.

### NEW-B-02 — Cloud publication authority receipt (weather → cloud consumer, R000B)
- **Scope:** whether weather-derived cloud coverage/raster/effects may remain published. (Cloud engine N15 itself is rendering-lane; this entry covers only the authority receipt.)
- **Sources:** `_cloudPublication`, `cloudAuthorityMode`, `cloudAuthorityMatches`, `publishCloudAuthority`, `rememberWeatherEffects`, `withdrawWeatherEffects`, `withdrawCloudState`, `reconcileCloudPublication`, `cloudPublicationCurrent` L2685-2752; publisher `applyCloudState` L3222-3241; no-model branch `render` L3486-3492; per-frame reconcile L3880, painter L2818; scene supersession L2230; host hooks `real-sky/native-host-hooks.js` L13-14.
- **States:** `uninitialised`, `eligible-published`, `withdrawn-unavailable`, `superseded` (R000B.md L34-39); receipt revision.
- **Transitions:** complete atmosphere with available decision → `eligible-published`; unavailable decision or authority mismatch → `withdrawn-unavailable` (zero targets/coverage, `_cloudReady=false`, column density and raster cleared, effects off, header repainted) (L2730-2741); scene replacement → `superseded`; healthy A→B handoff retained only while A still selected and `model()!==null` (L2700-2704).
- **Invariants:** fresh weather alone cannot revive old cloud material; same record cannot renew a separately consumed present-evidence lease (L2696-2697); population/motion phases preserved across withdrawal.
- **Risks:** every quarter-hour expiry (BF01) drives a full withdrawal and a snap re-establishment (L3233); with no timetable a fresh record is withheld (BF05).
- **Enforcement:** documentation — `docs/state-contracts/R000B.md` (+ ACCEPTANCE/INTEGRATION); implementation — explicit and enforced; verification — unit + 7 named mutation discriminators + hosted native Chromium cells + independent review (certificate #11 §4-5). Firefox/WebKit withdrawal not observed.
- **Tests:** `tests/weather-no-timetable-handoff.test.cjs`, `tests/weather-no-timetable-withdrawal.test.cjs`, `tests/r000b-remaining.test.cjs`, `tests/r000b-sky-withdrawal.test.mjs`, `tests/r0024-cloud-expiry.test.cjs`.
- **Observed facts:** no-model branch now reconciles and withdraws (L3491), closing NF02. **Hypotheses:** none. **Unknowns:** hidden-card retention of old deck until resume (certificate #11 §5, cause not established).

### NEW-B-03 — Weather target capture and location provenance (R0023)
- **Scope:** the immutable target a weather/radar record belongs to, carrying location intent, source, accuracy and original fix time.
- **Sources:** `captureWeatherTarget` L1384-1395; `weatherTargetSame` L1396; `_wxTargetCache`/`currentWeatherTarget` L1397-1404; `weatherPointTarget` L1621-1629 (fixture lane only).
- **States:** cached target keyed by CONFIG identity, evidence identity, generation, lat, lon.
- **Transitions:** any of those changes → new captured target (copy of primitives only; future `acquiredAt` → null L1393).
- **Invariants:** storage/save never renews a fix; identity comparison = generation+lat+lon (evidence changes are broad config changes, so they always bump generation via R0003 `CONFIG_EFFECTS.locationEvidence` L702).
- **Risks:** none found; precision/age only matters to the closed fixture lane.
- **Enforcement:** documentation — comments, R0023 issue; implementation — partly explicit; verification — unit + mutation (`tests/r0023-metadata.cjs` 31/31, `tests/r0023-mutations.cjs`).
- **Facts/Hypotheses/Unknowns:** live lane never uses device precision; no hypotheses; none.

### NEW-B-04 — Location evidence normalization and persistence provenance (config.js)
- **Scope:** how acquisition evidence survives normalize/save/load without being renewed or upgraded.
- **Sources:** `config.js:56-85` (`normalizeLocationEvidence`, `browserLocationEvidence`, `placeLocationEvidence`), `config.js:219-245` (`loadLocal` origin preservation, `saveLocal` browser→`manual` source with `origin` kept), `config.js:357-362` (`applyHashPrefs`).
- **States:** source {hash, manual, place, browser-geolocation, coarse-ip, legacy, unknown}; intent {fixed-site, device-position, coarse-area, unknown}; accuracy/acquiredAt only for browser evidence.
- **Transitions:** browser claim without matching raw evidence → `legacy` (L64); future/non-positive fix time → null (L72); save keeps raw evidence and origin; load restores `origin`.
- **Invariants:** coordinates select a target; evidence never asserts "here now".
- **Enforcement:** documentation — comments; implementation — partly explicit; verification — unit (`tests/r0023-*.cjs`, `tests/location-admission-*.test.cjs`).
- **Facts/Hypotheses/Unknowns:** a backward wall correction demotes a saved browser fix to unknown time on every normalize (fail-closed); none; none.

### NEW-B-05 — Site elevation dual custody
- **Scope:** surface elevation from the weather response, used by the native atmosphere and the CP9 renderer.
- **Sources:** legacy `siteElev` L1291 (writer L1467; readers L3083 `altClarity`, L3192 `starBlur`, debug L3321); CP9 `_cp9SiteElevation` `real-sky/native-host-hooks.js:5-9,23`, injected writer `tools/build_native.py:69-71`.
- **States:** legacy scalar {0 default, last response elevation}; CP9 {null, frozen {heightM, generation, lat, lon}}.
- **Transitions:** legacy updated by any accepted-attempt response carrying current or track (no eligibility, no target binding); CP9 updated only after eligible adoption and bound to generation/coordinates.
- **Invariants:** CP9 consumption requires generation+coordinate match and a selected current record (hooks L23).
- **Risks:** legacy scalar is never reset by `resetForNewLocation` (L3717-3726) — BF03.
- **Enforcement:** documentation — comments only; implementation — legacy implicit, CP9 partly explicit; verification — CP9 `tests/real-sky/cp9-elevation.test.mjs` (not run here); legacy none.
- **Facts/Hypotheses/Unknowns:** fact as above; hypothesis that the stale value is visually small (only star haze/blur factors); visual magnitude unknown.

### NEW-B-06 — Forecast-track preview substitution and live return
- **Scope:** in explicit preview (`ADVANCING`/`_clockPreview`) the current record is replaced by an interpolated forecast object.
- **Sources:** `wxAt` L1553-1570; `syncWeather` L1571-1581 (called from `render` L3485); live return `SalahClock.set` L3766-3777 (`weather=null;loadWx();fetchWeather()` when `src==="forecast"`, L3772).
- **States:** `weather.src` {current, sim, forecast}.
- **Transitions:** each render in preview overwrites `weather` from the track at `simNow()`; explicit live return clears forecast and reloads cache.
- **Guards:** track target must match (L1557); real time never substitutes (L1579).
- **Risks:** no age bound on the in-memory track for this path (preview labelled) — BF08.
- **Enforcement:** documentation — comments; implementation — implicit; verification — unit (`tests/r0024-weather.test.cjs`, `tests/hotfix-prayer-weather.test.cjs`).
- **Facts/Hypotheses/Unknowns:** fetches are suppressed during ADVANCING (L3875) so the track is never refreshed in a long timeScale run; none; none.

### C02 — Coarse location provider cascade and whole-body deadline
- **Scope:** permission-free area detection at boot (local/preferLocal without saved config) and on Reset.
- **Sources:** `config.js:251-304` `coarseDetect`; admission `config.js:87-115`; callers `index.html` L3792-3809 (boot), L4130 (reset).
- **States:** provider i ∈ {GeoJS, ipinfo}; attempt {pending, ok, transport, http, parse, admission, timeout}; result {ok, failed} with bounded `attempts`.
- **Transitions:** per provider `Promise.race(work, deadline 6 s)`; failure of any stage (incl. admission) advances to next; exhaustion → `{ok:false,status:"failed"}`.
- **Guards:** `admitCoordinates` before `normalize` (L291-293): finite number or complete decimal string in range; no clamping.
- **Invariants:** exactly one adopted result per invocation; deadline owns headers+body+parse.
- **Failure:** timer cleared on settlement; late work cannot trigger a second fallback; no caller cancellation (callers fence by generation/owner).
- **Risks:** a provider that reports `0,0` for unknown IPs would be admitted (speculative; no provider contacted); `label`/`area` not type-checked (object → string coercion via `normalize`).
- **Enforcement:** documentation — `docs/state-contracts/R0026.md`; implementation — explicit and enforced; verification — unit + mutation + native (stubbed, Chromium 148/Firefox 153) + independent delivery review (#68 §2).
- **Tests:** `tests/location-admission-outcomes.test.cjs`, `tests/location-admission-mutations.test.cjs`, `tests/r001f-deadline.cjs` 13/13, `tests/r001f-mutations.cjs`.
- **Unknowns:** GeoJS `accuracy` unit (stored as `cfg.accuracy`, consumed by nothing in index/builder).

### C03 — Forward geocoder aggregate completion
- **Sources:** `config.js:364-457` (`_nomCands`, `_zipCand`, `_dedupeCands`, `geocodeSearchDetailed`, lossy `geocodeSearch`).
- **States:** status {not-requested, matches, no-match, unavailable}; coverage {null, complete, partial, none}; per-provider attempt.
- **Transitions:** Nominatim (+ Zippopotam for Canadian FSA) each raced against one shared 8 s rejecting deadline; HTTP 404 on Zippopotam = no-match (owner A1); any failure prevents a no-match conclusion.
- **Invariants:** caller owns adoption; no query/body persisted.
- **Risks:** superseded lookups keep running until their deadline (bounded); Nominatim `class` vs `category` naming may make the place/boundary preference inert (R0026.md L239-240, unknown).
- **Enforcement:** documentation — R0026; implementation — explicit; verification — unit + mutation + native + independent delivery review (Zippopotam not covered publicly).
- **Tests:** `tests/location-admission-*.test.cjs`, `tests/r000f-intent.cjs` 21/21.

### C04 — Browser location and permission request completion
- **Sources:** `config.js:306-327` (`geolocate`, `permissionState`); evidence `config.js:78-82`.
- **States:** unsupported, requesting, fix admitted, invalid coordinates, error(code); permission {granted, prompt, denied, unknown}.
- **Transitions:** browser callback → `admitCoordinates` → evidence with original `pos.timestamp`/accuracy; `maximumAge` 10 min, timeout 10 s.
- **Invariants:** a cached fix keeps its original age; no renewal.
- **Risks:** caller awaits `permissionState()` after a successful fix before applying it (BF07, speculative).
- **Enforcement:** documentation — R0026, comments; implementation — partly explicit; verification — unit + native with stubbed geolocation (no real permission prompt).

### N21 — Settings place search, GPS, candidate cycling, reset (location acquisition part)
- **Sources:** state L3907-3911; ownership `_invalidateSetLocation`/`_captureSetLookup`/`_ownsSetLookup` L3942-3946; `_runSetSearch` L3976-3989; `_showSetCand` L3990-4003; field handlers L4063-4093; `_usePrecise` L4105-4121; `_resetLocal` L4122-4144; open/close L4145-4164; `applyConfig` L3729-3760.
- **States:** session, edit, seq counters; candidate set + owner; location evidence/origin/saved flags; `_geoPermission`, `_geoLastError`; pref versions.
- **Transitions:** coordinate edit → manual evidence; label edit preserves evidence; Enter → lookup owned by {session,edit,seq}; repeat Enter cycles only while owner and label match (L4089); GPS: two awaits each followed by owner check (L4110,4112); Reset: clear storage → stop on failure → coarse detect → owner check → merge newer prefs → `applyConfig(...,{reset:true})` (broad by explicit intent, R0003) → owner check → repopulate.
- **Invariants:** last explicit location intent wins; stale success/error never touches the form; GPS save does not renew acquisition.
- **Risks:** closing the panel during Reset's detect leaves storage cleared and the runtime on the old location (by design per `tests/r000f-reset.cjs`; message remains "Saved settings cleared.").
- **Enforcement:** documentation — R000F, R0026, R0003 contracts; implementation — partly explicit; verification — unit + mutation + native stubbed (R0026 ES26-13).
- **Tests:** `tests/r000f-intent.cjs` 21/21, `tests/r000f-reset.cjs` 9/9, `tests/config-effects-*.test.cjs`, `tests/r0003-ownership.test.cjs`.

## 2. Historical-to-current reconciliation

| Original | RLGWO / commit | What changed (diff f71fef6c→363c3e53) | Disposition | Evidence |
|---|---|---|---|---|
| N08 | R000D #13 `ba0851ae`; R000B #11 `ea9f8300`→merge `da126880` | wall `now-lastWxTry` gate replaced by `retryGate` + elapsed `_wxRetry` (old L1366-1381 → L1446-1453); `selectedWeather(now,record)` per-record | partly resolved | XF02 closed; quarter-hour lapse-before-refresh unchanged (BF01, probe) |
| N09 | R000B #11; R0024 #36 (before window) | consumers bound to one decision; header withdrawal on cloud withdrawal (L2739) | implemented but not fully verified | native withdrawal Chromium only (#11 §5) |
| N10 | R000D #13; R000E #14 (Oct) | radar gate → `retryGate("radar")` (old L1446-1451 → L1520-1526) | partly resolved | spacing verified natively; still no consumer, host not allowlisted |
| C02 | R0026 #68 `fbd08aa1` (merge `7f2e8d16`); R001F #31 (Oct) | `admitCoordinates` before `normalize`, attempt records, stage errors | resolved and independently verified | independent delivery review rejected 999/999, hex, exponent, Infinity (#68 §2) |
| C03 | R0026 #68 | `geocodeSearchDetailed` with status/coverage/attempts; shared rejecting deadline | resolved and independently verified | delivery review: HTTP 503 → unavailable, `[]` → no-match; Zippopotam path not publicly covered |
| C04 | R0026 #68 | `admitCoordinates` on `pos.coords` (config.js:312-313) | implemented but not fully verified | stubbed geolocation only; no real permission prompt |
| N21 | R0026 #68; R0003 #3 `a06957c6`; R000F | settings consumes detailed statuses (L3982-3986); Reset passes explicit `reset:true` (L4136) | implemented but not fully verified | source + stubbed native; real geocoder/permission untested |
| NF02 | R000B #11 | no-model branch calls `reconcileCloudPublication` + `withdrawWeatherEffects` (L3491); per-frame reconcile L3880 | resolved and independently verified | 7 mutation discriminators pass (run here); hosted native Chromium + independent review |
| CF04 | R0026 #68 | see C02 | resolved and independently verified | as C02 |
| CF06 | R0026 #68 | see C03 | resolved and independently verified | as C03 |
| XF02 (weather side) | R000D #13 | elapsed retry record; D2 wall fallback disclosed | resolved and independently verified | RED on main 18 fail → GREEN 23/23, mutations 12/12, native two engines, independent delta review |
| XF01 / root F01 (weather side) | R0003 #3 `a06957c6` | `classifyConfigChange` + `CONFIG_EFFECTS` (L697-741): label/time/datefmt/appearance → presentation path | partly resolved | `units` still broad (L707) → prayer, weather **and radar** restart; GDOPL "separate weather units from radar" not done (R000D ES0D-13 deferred it) |
| R0003 title "bind async prayer/weather/radar commits" | #3 | implemented as effect classification; async commit binding relies on pre-existing N03 generation/slot fences | superseded by a different implementation | fences at L1080-1112 predate the window |
| Original N08 "response-size cap" risk | — | unchanged | still implicit or vulnerable | no length cap on hourly arrays (L1355-1366) |
| Original N10 "manifest host not allowlisted" | — | unchanged | still implicit or vulnerable | L1530, L1541; probe dispatched image to an `http://` host |

## 3. Findings

| ID | Title | Machines | Evidence class | Severity |
|---|---|---|---|---|
| BF01 | Current weather always lapses before a replacement can be requested (quarter-hour authority gap) | N08, NEW-B-01, N09, NEW-B-02 | demonstrated | medium |
| BF02 | Rejected or unadmittable 200 responses recorded as `received` in request diagnostics | N08, N10 | demonstrated | low |
| BF03 | Legacy `siteElev` is neither target-bound nor reset on location change | NEW-B-05, N08 | demonstrated (source trace) | low |
| BF04 | Radar acquisition runs with no product consumer; manifest host unvalidated | N10 | demonstrated (consumers) / plausible risk (host) | low |
| BF05 | Without a timetable, fresh weather header shows a precipitation condition while clouds/particles are withheld | N09, NEW-B-02 | plausible risk | low |
| BF06 | Units change still takes the broad path (prayer and radar restart) | N08, N10 | demonstrated | low |
| BF07 | GPS adoption waits on an unbounded `permissions.query` | C04, N21 | speculative | low |
| BF08 | Preview forecast substitution has no track age bound | NEW-B-06 | plausible risk | low |
| BF09 | Nominatim place/boundary preference may be inert (`class` vs `category`) | C03 | speculative | low |

**BF01 — quarter-hour authority gap.** Trace: eligibility requires `sourceAge<=900 000` (L1374-1375). The weather
gate returns `fresh-data-satisfied` while the record is selected (L1276), so no request can start before expiry.
Refresh opportunities arrive every ~30 s (L3875). Each time the record expires, the next frame's `reconcileCloudPublication`
(L3880) withdraws the cloud deck: coverage goes to zero, `_cloudReady=false`, density and raster are cleared, effects go off
and the header shows "—" (L2730-2739). Recovery comes at the next poll plus request latency, and the deck snaps back
rather than easing (L3233). Probe `probes/B/wx-quarter-gap-probe.cjs` runs the exact authored regions with a modelled 30 s poll:
there is no fetch while the record is selected, the record is unselected at 06:30:00.001 and 06:45:00.001, and the first
poll that finds no eligible record is at 06:30:20 and 06:45:20. The R000B certificate (#11 §3) independently records the
header gap on the delivered page: about 2 s, and about 23 s in the reviewer's window. It was "recorded, not judged a
defect". That page had a clear sky, so the cloud pop was not observed. Materiality: under cloudy or rainy weather this
predicts a visible deck disappearance and a precipitation stop every 15 min. That touches the `AGENTS.md` "no
slideshow" and continuity gates. The gap existed in pre-window code too (f71fef6c `applyCloudState` zeroed coverage
on `modelCode==null`). Open questions: the provider's real `current.time` cadence, and whether the owner accepts the
gap as truthful withdrawal. Do not fix it by extending TTL; that would break the hard constraint.

**BF02.** `wxFetchJson` marks `received` on any parsed body (L1428). `fetchWeather` then silently returns on
`j.error===true`, on a missing current/track, or with nothing admitted (L1458, L1462-1473). `fetchRadar` does the same
for a missing host or frame (L1531-1533). The only override is the zone mismatch at L1460. The probe
`wx-outcome-probe.cjs` shows `state:"received", reason:null` with nothing admitted for `{error:true}`, `{}` and an
invalid current. HTTP 503 correctly shows `unavailable`. Impact: `qaState().wxTruth.requests` presents a failure as
success. Observability only; admission stays correct.

**BF03.** The only writer is L1467. It accepts `current||track` from an eligible attempt, but needs no eligible current
and no target binding. `resetForNewLocation` (L3717-3726) does not reset it. Readers: L3083 and L3192 (star
haze/blur). After A→B with B's weather failing, A's elevation persists for B. The CP9 copy is fenced
(`native-host-hooks.js:6-9,23`), so there are two elevation representations with different custody. The visual effect
is likely small. Unchanged since f71fef6c.

**BF04.** Only `radarEvidence` (L1482-1488) and `qaState` (L3554-3559) read `weatherRadar` (grep; R000D ES0D-14).
Still, a manifest request plus a zoom-6 tile request goes out every 10 min (L1520-1552), which sends the tile
location to a third party with no product benefit. The manifest `host` is concatenated unchecked (L1530, L1541). The
probe dispatched an image to an `http://` host, and the source has no meta CSP. This is trust in the provider, not a
demonstrated exploit.

**BF05.** In the no-model branch the header is painted from the decision (L3488). Clouds are withheld for any record
other than the one already published (L2703 requires `model()!==null`). The R000B certificate §5 records the
"Rain 24°" header with no clouds drawn and says "whether that is a product defect is unknown". This is
cross-consumer divergence, not a false claim. The header is labelled as a model estimate.

**BF06.** `CONFIG_EFFECTS.units` has `path:"broad"` (L707). In `applyConfig` (L3750-3757) that means a new
generation, withdrawal of prayer presentation, and restarted prayer, weather and radar requests, although radar and
prayer do not depend on units. Efficiency only. The fences are correct.

**BF07.** `_usePrecise` awaits `SalahConfig.permissionState()` (L4111) before applying a successful fix (L4114). The
`permissions.query` promise has no timeout (config.js:321-327). If it never settles, the fix is never applied. No
known browser does this.

**BF08.** `wxAt` checks only the target (L1557). `weatherForecast` bounds the track to 6 h (L1683), but the preview
substitution path (`syncWeather`, L1580) does not, and fetches are suppressed while ADVANCING (L3875). The track can be
arbitrarily old in a long fast-forward. The output stays labelled SIM/forecast preview.

**BF09.** The R0026 contract (L239-240) notes that Nominatim jsonv2 naming is unresolved. `_nomCands` filters on
`r.class` (config.js:374). If the provider emits `category`, the preference always falls back to every admitted
item. Unknown, because no provider was contacted.

## 4. GDOPL inputs (Gradient Descent Over the Project Lagrangian)

Schematic: `q` = current configuration of the weather/location machines; `f_T(q)` = staleness, false claims, gaps
and wasted work; `g_j(q) ≤ 0` = modelled bounds (retry spacing, deadlines, TTLs); `F_hard` = truthful weather and
location provenance, rejection of unauthorised late results, separation of accepted and displayed state,
instance-owned cancellation, and privacy. No weights, gradients or optima are claimed.

| # | Interaction | Current q | Constraints | Neighbour q' = apply(q, η) | Benefit / regression cost | Evidence | Class |
|---|---|---|---|---|---|---|---|
| G1 | wall-clock correction vs retry spacing (XF02) | elapsed `_wxRetry` | freshness must leave a recovery route; never bless future data | — (taken) | removes stranded reacquisition / degraded fallback remains | before RED 18 fail → after GREEN 23/23, mutations 12/12, native ×2 (R000D.md L127-171) | demonstrated improvement |
| G2 | weather expiry vs missing timetable (NF02) | reconcile in no-model branch | no fabricated prayer model; preserve motion | — (taken) | no stale deck / none observed | f71fef6c L3247-3262 bypass vs L3491; withdrawal tests pass; hosted Chromium | demonstrated improvement |
| G3 | source-age TTL vs refresh shortcut (BF01) | refresh only after expiry | truthful expiry (hard); retry ≤ 1/60 s | η1: open the gate when `sourceAge ≥ TTL − margin` (or at the provider's next interval) keeping all fences; η2 (rejected): hold the deck past TTL — violates `F_hard` | fewer 15-min withdrawals/pops / extra request per interval, provider-cadence assumption | probe + certificate observation; counterfactual not executed | plausible improvement requiring verification |
| G4 | units change vs radar/prayer (XF01 residual) | broad | accepted tz/generation fences | η: `units` → weather-only path (new weather slot, keep prayer/radar) | fewer restarts / new partial-invalidation rules | `CONFIG_EFFECTS` L707; original GDOPL_FINAL L54 projected this | plausible improvement requiring verification |
| G5 | radar acquisition vs no consumer (BF04) | periodic radar | privacy; truthful diagnostics | η: acquire radar only under `qa`/diagnostic flag, or host allowlist | less traffic and exposure / loses passive diagnostics | grep of consumers; R000D ES0D-14 | plausible improvement requiring verification |
| G6 | elevation custody (BF03) | legacy unbound + CP9 bound | stale location data must not persist | η: reset `siteElev` in `resetForNewLocation` or derive it from the CP9 bound copy | no cross-location carry-over / tiny visual change needs pixel check | source trace | plausible improvement requiring verification |
| G7 | external coordinate admission (CF04) | admit before normalize | truthful provenance | — (taken) | invalid provider data advances fallback | before: clamp at config.js:258-264 (f71fef6c); after: L291-293; tests + delivery review | demonstrated improvement |
| G8 | geocoder outcome (CF06) | detailed status | truthful UI | — (taken) | distinct failure vs no-match | before `.catch→[]`; after status/coverage; tests + delivery review | demonstrated improvement |
| G9 | attempt diagnostics (BF02) | `received` on rejection | truthful evidence claims | η: record `unavailable` + reason on every non-admission return | truthful qaState / test pin churn | probe | plausible improvement requiring verification |
| G10 | overlapping retry representations | `_wxRetry` + write-only `lastWxTry`/`lastRadarAt` | compatibility | η: remove write-only fields | less state / harness rebinding | R000D.md L190 | retain (documented) |

Comparison with the original projection: the directions "independent weather-to-cloud permission transition"
(GDOPL_FINAL L71-73, L110) and "owned elapsed scheduling bound" (L93-95) were taken with before/after evidence. The
"configuration effect matrix" (L48-63) was taken only partly, because units and radar are still coupled. BF01 was not
anticipated by the original projection.

## 5. Coverage statement

- **Read fully:** `src/native/config.js`; `src/native/index.html` L697-761, L1060-1120, L1255-1870, L2600-2770,
  L3010-3060, L3218-3245, L3478-3500, L3540-3590, L3630-4189; `docs/state-contracts/R000D.md`;
  `docs/state-contracts/R000B.md` L1-117; `docs/state-contracts/R0026.md` L14-60 and L237-256;
  `real-sky/native-host-hooks.js` L1-40; `tools/build_native.py` L60-80; the original catalogue entries
  N08/N09/N10/N21/C02/C03/C04, findings NF02/CF04/CF06/XF01/XF02, `root_findings.json` titles and the GDOPL
  weather/location sections.
- **Read from GitHub (read-only):** the final certificates of #3, #11 and #68, plus titles and states of #12, #13,
  #14, #30, #31, #35 and #36.
- **Sampled:** the diff hunks f71fef6c→363c3e53 for weather, radar and settings, and the commit list for both
  authored files.
- **Not examined:** `src/native/builder.html` (C05-C07 builder geolocation/search consumers);
  `R000B_ACCEPTANCE.md` / `INTEGRATION.md`; the R0003.md body; the N15/N13 renderer consumption of the cloud
  receipt; `v1/` (C18-C20); native/browser behaviour of any kind.
- **Tests run (Node v24, VM-based, no network, no tree writes; `git status` clean before and after):**
  - `node --test` on 20 files, 618 tests: 614 pass, 0 fail, 4 todo. Files: r000c-weather, r000d-weather,
    r0024-{cloud-expiry, information, particle-origin, response-zone, weather}, weather-retry-clock-{state,
    mutations}, weather-withdrawal-{authority, mutations}, weather-no-timetable-{handoff, withdrawal},
    r000b-remaining, location-admission-{mutations, outcomes}, r0003-ownership, hotfix-prayer-weather,
    config-effects-{state, mutations}.
  - Script tests: `node tests/r0023-metadata.cjs` 31/31, `r0023-mutations.cjs` all mutants caught,
    `r001f-deadline.cjs` 13/13, `r001f-mutations.cjs` caught, `r000f-intent.cjs` 21/21, `r000f-reset.cjs` 9/9,
    `r0017-weather.cjs` exit 0.
- **Probes (effect-free, stubbed fetch/Image/clock, exact authored regions):**
  - `probes/B/wx-outcome-probe.cjs` → `wx-outcome-probe.out.json` (BF02, BF04 host).
  - `probes/B/wx-quarter-gap-probe.cjs` → `wx-quarter-gap-probe.out.json` (BF01).
