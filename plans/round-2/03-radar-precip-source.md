# Plan R2-03 — CORS-safe radar/nowcast precip source to upgrade weather-truthfulness gate from conservative to ground-truth

> **Status:** ✅ DONE (2026-06-16) — user accepted the third-party dependency; **RainViewer** true radar wired as an INDEPENDENT observed-precip sensor. `fetchRadar()` pulls `weather-maps.json`, builds the web-mercator tile (z=6) for the site's lat/lon, loads it `crossOrigin="anonymous"` (RainViewer tiles ARE CORS-readable — verified live), samples a 7×7 pixel neighbourhood (alpha + density → a coarse mm proxy; ≥3 return pixels required to ignore clutter). `gateWeatherCode(raw,w,radarMm)` uses `max(nowcast, radar)` as observed evidence — **CONFIRM-ONLY** (the gate only ever gates DOWN precip codes, so radar can keep a code the model missed but never fabricates rain) and **FAIL-CLOSED** (error / coverage gap / stale >20min / sim → 0 → today's nowcast-only behaviour). Verified live: Hong Kong (raining) → radar 4.3mm, `effectivePrecipMm` 4.3, rain kept; Madinah (clear) → 0, no false precip; sim ignores radar. `qaState().wxTruth` exposes `radarSource`/`radarPrecipMm`/`radarAgeSec`/`radarConfirming`/`effectivePrecipMm`. 5 pure radar-gate smokes (confirm-only / never-fabricate / thunder threshold) → **40/40**.  ·  **Class:** research → feature  ·  **Priority:** P1  ·  **Effort:** L  ·  **Risk:** low
> **Do now?** Yes — recommended soon  ·  **Plan-review verdict:** `needs-fixes` (8 required fixes — see end)  ·  **Depends/notes:** see "Dependencies / notes"
>
> Read-only round-2 plan from `/implementaudit` (workflow `wf_3f9f2919-894`, investigate → adversarial critique). Grounded against the **current working tree** (`index.html` with the 2026-06-16 uncommitted pass applied; HEAD `91d0fc1`). **No source was changed.** Re-verify anchors before editing.

## Problem
The widget's weather-truthfulness gate currently depends on Open-Meteo's `current.precipitation` (a model nowcast, not observed radar). The documented Remaining Risk (ARCHITECTURE.md:195) states: "Weather 'current' is an Open-Meteo nowcast, NOT radar — the gate is conservative, not ground-truth." This means the widget downgrades precip/thunder codes when observed precip is missing, but lacks a true radar feed to confirm actual rain. A CORS-safe, keyless radar/nowcast source would allow the gate to CONFIRM rain visuals (upgrade from "no evidence → downgrade" to "evidence found → confirm"), making the widget a ground-truth instrument rather than a conservative fail-safe.

## Root cause
Open-Meteo's nowcast is a model forecast (interpolated from coarse forecast grids), not real-time radar reflectivity or satellite-sensed precipitation. The gate (gateWeatherCode, lines 1245–1257) requires `observed.precip ≥ 0.05 mm` to honor rain/thunder codes; without radar evidence, it downgrades to cloud-cover-implied states. The design is intentionally conservative (fail-closed), but this leaves a gap: the widget never CONFIRMS precip from a real sensor, only avoids claiming rain without evidence.

## Current behavior
- `fetchWeather()` (lines 615–646) pulls Open-Meteo's `current={code, precip, rain, showers, snow, …}` (~15-min refresh).
- `gateWeatherCode(raw, w)` (lines 1245–1257) checks: if precip code (rain/thunder/snow) and `w.precip < 0.05 mm`, downgrade to cloud state inferred from `cloud_cover`.
- `qaState().wxTruth.observedPrecipMm` reports the source precip value (Open-Meteo nowcast only).
- No radar source; weather class stuck in conservative mode.
- Smoke tests pass (31/31) because they QA the downgrade logic, not the absence of radar.

## Desired behavior
- Identify ONE primary CORS-safe, keyless radar/nowcast source with broad coverage (not geographically limited).
- Fetch real-time or near-real-time precipitation from that source (either in mm reflectivity or dBZ reflectivity, convertible to mm).
- Wire it into `gateWeatherCode` as a SECOND, independently-fetched evidence feed: if the radar says "raining" but Open-Meteo nowcast says "dry", the gate can now confirm the precip code.
- Preserve FAIL-CLOSED behavior: missing radar (coverage gap, network error, rate-limited) → fall back to Open-Meteo evidence alone (no worse than today).
- Update `qaState().wxTruth` to expose the radar source and its observed precip (radar vs nowcast reconciliation).
- No new npm dependencies, secrets, or build steps. Keep the single-file static character.

## Code anchors (re-verify line numbers before editing)
**`index.html:615–646`**
Current fetch pulls Open-Meteo only. A radar fetch would run in parallel or sequentially, storing results in a separate variable (e.g., `weatherRadar`) so both sources are independently tracked.

````js
async function fetchWeather(){ … weather={code:cu.weather_code, precip:cu.precipitation, …}; … }
````

**`index.html:1245–1257`**
Gate currently accepts ONE `w.precip` source. A radar-aware gate would check BOTH `w.precip` (nowcast) and `w.radarPrecip` (if available), using the MORE SUPPORTIVE evidence (prefer 'raining' over 'dry').

````js
function gateWeatherCode(raw,w){ … const precip=(w&&w.precip!=null)?+w.precip:null, has=precip!=null&&precip>=_PRECIP_MIN; if(!has){ … return dc; }
````

**`index.html:1242`**
Thresholds for active precip / storm evidence. Radar reflectivity (dBZ) thresholds differ from mm (e.g., 20 dBZ ≈ 0.05 mm light rain); if radar returns dBZ, a conversion function is needed.

````js
const _PRECIP_MIN=0.05, _THUNDER_MIN=0.8;
````

**`index.html:1844–1848`**
Diagnostics surface. Radar source should add `radarPrecipMm`, `radarSource`, and reconcile downgradeReason (e.g., 'nowcast dry but radar wet → confirmed' or 'radar unavailable, nowcast dry → downgrade').

````js
wxTruth:(()=>{ … observedPrecipMm: p, activePrecip: p!=null&&p>=_PRECIP_MIN, … downgradeReason: _wxDowngrade||null
````

**`index.html:1414`**
atmosphere() uses gated code only. The gated code is deterministic given (rawCode, weather) — a radar-aware gate needs to pass both nowcast AND radar evidence into gateWeatherCode.

````js
const code=gateWeatherCode(rawCode, weather);
````

## Approach
**Phase 1: Survey (READ-ONLY RESEARCH)**
1. Identify 4–6 candidate CORS-safe, keyless, no-auth precipitation radar/nowcast sources:
   - **RainViewer public API** — free, CORS-friendly tile-based radar reflectivity, global coverage, ~50-country resolution, no key (freemium tier). Returns reflectivity (dBZ), needs conversion to mm.
   - **Open-Meteo minutely_15** — already trusted, free CORS, 15-min nowcast precipitation `precipitation` (mm). Available in existing fetch; just needs integration into the gate.
   - **MET Norway Nowcast (Nowcastxml / Nowcast JSON)** — Nordic/European coverage, free public data, CORS-enabled. ~2 km resolution. Requires coordinate-to-grid lookup.
   - **National Weather Service (US only)** — free, CORS-safe grid, very high resolution. Geographic limitation.
   - **KNMI (Royal Netherlands Meteorological Institute)** — European coverage, free public radar tiles.
   - **Vortex (if public tier exists)** — satellite-sensed precip, may be restricted.

2. For each, document:
   - CORS policy (preflight allowed? credentials? proxy required?).
   - Coverage (global? regional? data gaps?).
   - Key requirement (none? API key? rate limits?).
   - Data shape (reflectivity dBZ vs. estimated mm? How to query at widget location?).
   - Refresh rate (real-time? 5 min? 15 min?).
   - Error handling (graceful fallback? data gaps covered?).

3. Design integration pathway:
   - Add a parallel fetch (`fetchRadar()` or extend `fetchWeather()`).
   - Store radar result in a new module-level `weatherRadar` variable (shape: `{source, precip, reflectivity, fetchedAt, …}`).
   - Modify `gateWeatherCode(raw, w, radarW?)` to accept a second weather object.
   - Logic: if `radarW.precip >= PRECIP_MIN` but `w.precip < PRECIP_MIN`, the radar overrides the downgrade; report "radar confirms precip" in the downgrade reason.
   - Fail-closed: missing/stale radar → use nowcast evidence only.

4. Reconciliation rule:
   - Nowcast says rain, radar says dry → still downgrade (prefer observed radar, avoid false positives).
   - Nowcast says dry, radar says rain → confirm the precip (upgrade from downgrade).
   - Both say rain → confirm (strongest evidence).
   - Both say dry → downgrade to cloud state.

**Phase 2: Prototype & QA (for the implementer)**
- Test each source in isolation (curl/fetch in console).
- Prototype the radar fetch in a `?debugRadar=1` mode (log fetched data, no DOM change).
- QA: define test cases (e.g., `?simWx=63&simPrecip=0&radarPrecip=2` → confirm rain despite nowcast dry).
- Smoke-test the gate with both sources present + missing radar scenarios.

**Phase 3: Integration spec (for the implementer)**
- Add `fetchRadar()` to run after `fetchWeather()` (or during, if parallel).
- Store: `let weatherRadar=null, lastRadarAt=0, radarBusy=false;` (mirroring weather state vars).
- Modify `gateWeatherCode(raw, w, rw?)` to reconcile precip from `w` and `rw`.
- Update `paint(A)` / `atmosphere(M)` to use the reconciled gate output (no change needed; the gate does the work).
- Expose in `qaState().wxTruth`: `{radarSource, radarPrecipMm, reconciliationNote, …}`.
- Cache & stale-state: `qaState().cache` should report radar age (`radarAgeSec`, `radarStale`).

**Phase 4: Fallback & bounds**
- If radar source is unavailable (rate-limited, CORS block, geographic coverage gap), the widget silently holds the last good `weather` state and the gate operates on nowcast only (current behavior) — no error, no UI change.
- If radar and nowcast disagree sharply (radar raining, nowcast clear for >30 min), log a diagnostic (no visual change; contradictions are possible in sparse ground-truth).
- Radar refresh rate: 5–15 min (match or slightly faster than nowcast refresh, ~15 min).

**Recommendation:**
- **Primary:** Open-Meteo `minutely_15` (if available in the current contract) — already CORS-safe, no new dependencies. Check if the existing fetch can include `minutely` precip and fold it into the gate.
- **Secondary:** RainViewer public API (reflectivity → mm conversion, larger footprint for users outside Nordic/US). Requires dBZ→mm calibration (e.g., Marshall–Palmer Z = 200R^1.6, solve for R).
- **Fallback:** NWS/KNMI for regions where the primary is unavailable; fail gracefully (no radar) rather than requiring a geo-aware pick.

## Alternatives considered (and rejected)
- **Upgrade to a third-party weather API (Dark Sky, WeatherAPI, Meteomatics) with built-in radar** — Breaks the no-key, no-secret, no-cost constraint. Dark Sky is behind Apple; WeatherAPI / Meteomatics require API keys. The widget's design ethos is free + embedded-safe, and adding auth breaks the static single-file character and introduces secrets management.
- **Parse real-time radar imagery from public tile servers (e.g., Rainviewer WMS tiles)** — Feasible but complex: requires image-to-reflectivity decoding, geolocation lookup within tile grid, and real-time tile polling. Adds latency and client-side compute. The tabular API approach (JSON precip estimate) is simpler and faster.
- **Use satellite-sensed precip (NOAA IMERG, JAXA GPM)** — Excellent global coverage and ground-truth, but latency is high (24-48 hr delay for IMERG final products; near-real-time is available but less accurate). For a live prayer widget, 15-min-old data is acceptable; 24-hr-old is not.
- **Implement a user-provided radar source (URL + method as a config param)** — Flexibility is appealing, but it trades complexity for rare use. Most users benefit from a single, reliable default. Deferred as a Phase 2 enhancement if local-radar users request it.
- **Cache radar for >6 hours to reduce API calls** — Stale radar is worse than no radar (false-positive rain claims). Keep the 15-min refresh horizon short; network cost is negligible for a single user widget.

## Owner / source touchpoints
- fetchWeather() + new fetchRadar() (lines 615–646) — the data-fetch layer
- gateWeatherCode(raw, w, radarW?) (lines 1245–1257) — the truthfulness gate (CORE)
- atmosphere(M) (line 1414) — passes the gated code to the renderer (no change needed if gate is extended)
- paint(A) / applyTheme(M) (lines 1703–1704) — renders the outcome (no change needed)
- qaState().wxTruth (lines 1844–1848) — diagnostics surface
- qaState().cache (lines 1850–1855) — stale-state tracking
- tests/smoke.html (lines 61–95) — extend smokes to cover radar reconciliation scenarios

## Regression risks (forbidden-regression guardrails)
- **FORBIDDEN: Claiming rain without evidence.** A radar source that is stale, geographically out-of-coverage, or returns stale data must NEVER cause the widget to show precip if the nowcast says dry. Rule: radar supports a downgrade reversal ONLY if radar is fresh (<15 min old) AND no data gaps at the widget's location. Missing radar → hold to nowcast behavior (current, fail-closed).
- **Optics must stay tied to --sunvx/--sunvy.** A radar-confirmed rain condition does not change how the sun is positioned or the optics are registered. Only the precip code class (rain vs cloud) changes; no new behavior branches in atmosphere() or paint().
- **The moon must stay opaque.** Radar rain does not add translucency or layer effects. The moon's opacity is tied to darkness/moonlight, not weather.
- **Static file / no build / no dependency.** The radar fetch must use native fetch(), not a new library. No npm, no bundler. Keep it under 50 lines of new code.
- **Smoke tests must still pass 31/31 (baseline).** Adding radar detection must not break the existing 13-test pure-gate tests or the 18-test integration tests. Define 2–3 new radar-aware smokes (e.g., 'dry nowcast + wet radar → confirm') and verify the baseline suite still passes.
- **Cloud continuity & field identity.** The radar precip does NOT affect cloud generation (cloudFieldSeed, paintClouds). Clouds evolve from Open-Meteo cloud_cover & wind only; radar only gates the precip-code display, not cloud physics.
- **No new URL params / querystring explosion.** A ?radarSource= override may be useful for QA (`?radarSource=off` to disable radar testing), but it is deferred to Phase 2. The primary source choice is hardcoded in fetchRadar().

## Smoke A — capture BEFORE any change
- Dry nowcast (precip=0, code=63 rain), wet radar (precip=2) → gate outputs rain code, wxTruth shows 'radar confirms precip' note
- Wet nowcast (precip=2), dry radar (precip=0) → gate outputs rain code (nowcast wins), wxTruth shows 'nowcast supported, radar unavailable/dry'
- Both dry (nowcast precip=0, radar=0, code=63) → gate outputs overcast (downgrade), wxTruth shows downgrade reason
- Radar source unavailable / CORS error → gate falls back to nowcast logic, qaState().cache reports radarStale=true and radarAgeSec=null
- Thunder code (95) with dry nowcast (precip=0.3) and dry radar (precip=0) → gate outputs overcast (downgrade below 0.8 mm), wxTruth clear
- Thunder code (95) with dry nowcast (precip=0.3) and wet radar (precip=1.5) → gate outputs thunder (radar confirms >0.8 mm), wxTruth shows 'radar confirms storm'

## Smoke B — verify AFTER the change
- At real noon, with real weather, check that qaState().wxTruth.radarSource is non-null and radarPrecipMm is populated (or null if unavailable)
- Set ?simWx=95&simPrecip=0 (dry-forecast-thunder), then override with ?radarPrecip=1.5 → observe data-fx=thunder (not cloud/overcast), confirm gate used radar evidence
- Zoom time forward 30 min with ?timeScale=120 (fast-forward), watching qaState().cache.radarAgeSec increment. At >900 sec (15 min), radarStale should flip to true; gate should hold to nowcast behavior
- Inspect the downgradeReason field in wxTruth across scenarios: 'nowcast + radar both dry → cloud', 'nowcast dry, radar wet → confirmed precip', 'radar unavailable, nowcast dry → cloud'
- Cross-check that the rendered sky colours and precipitation animations respect the final (gated) code, not the raw code or the radar code independently — radar is only an evidence input, not a direct visual driver
- Verify that the footer emoji (moon phase) and all moon-related opacity are unaffected by radar precip detection — radar does not influence moonlight or moon visibility

## Acceptance criteria (falsifiable)
- Baseline smoke suite (31/31 tests in tests/smoke.html) passes without regression
- Define and document ONE primary CORS-safe, keyless radar source in the code comments (e.g., 'RainViewer' or 'Open-Meteo minutely' with URL structure and rate limits)
- gateWeatherCode() signature extended to accept optional radar evidence; reconciliation logic is clear (prefer radar if fresh, fallback to nowcast if unavailable)
- qaState().wxTruth includes radarSource (string or null), radarPrecipMm (number or null), and reconciliationNote (string explaining which source won)
- qaState().cache includes radarAgeSec (number or null), radarStale (boolean reflecting >15-min age or network error)
- At least 2 new radar-aware smoke tests pass (e.g., 'dry nowcast + wet radar → rain confirmed', 'radar unavailable → fall back to nowcast')
- No new npm dependencies, no secrets in the repo, no build step required
- Code is under 100 lines of net-new logic (fetchRadar + radar-aware gateWeatherCode + qaState updates); terse, single-letter locals, inline math (match surrounding style)
- Screenshots (live preview at ~noon UTC with real weather) show no visual regression: sun colour, moon opacity, cloud motion, precipitation animations, star visibility, and header readability unchanged
- Git diff shows ONLY the implementation: no dead code, no commented-out radar attempts, clean commit message referencing this plan key (radar-precip-source)

## Rollback
`git revert <commit-hash>`; the radar fetch is entirely in the `fetchRadar()` function (can be deleted); the gate change is in gateWeatherCode() (signature extended but fallback to current behavior if rw=undefined); qaState additions are purely diagnostic (no rendering change). All changes are localized and non-invasive. No data-structure rewrites, no forced file reorganizations. The widget reverts cleanly to the last committed state with zero side effects.

## Dependencies / notes
- DESIGN.md › Weather truthfulness is current and accurate (read already)
- ARCHITECTURE.md › Responsibility map + remaining risks (read already)
- tests/smoke.html › smoke test runner is operational and baseline passes 31/31 (pre-verify)
- URL hash contract is immutable (lat/lon/method/school/label; no new params for radar source yet)

## Open questions
- **Which radar source to pick as PRIMARY?** RainViewer (global, reflectivity), Open-Meteo minutely (already trusted), or MET Norway (Nordic-centric)? This is the research deliverable; a recommendation memo with CORS/coverage/latency trade-offs should inform the choice.
- **dBZ → mm conversion:** If RainViewer is chosen (reflectivity-only), which empirical relation should we use? Marshall–Palmer Z = 200R^1.6 is standard but site-dependent; alternatives (Hydrometeor-class calibrations) exist. This needs a brief lit-review or conservative choice (e.g., Z=20 dBZ → 0.05 mm floor, Z=40 dBZ → 2 mm).
- **Failure mode:** Should a radar-source network error (CORS block, rate-limit, JSON parse failure) surface a console warning, or fail silently? Silent (current design) is safer; loud (console.warn) is better for debugging. Recommend silent, with qaState().cache.radarStale as the signal.
- **Geographic fallback:** Some users are in zones with no radar coverage (maritime, Antarctica). Should the widget emit a soft deprecation note if radar is unavailable, or accept no-coverage silently (status quo)? Recommend silent for now (no UI noise); a diagnostic in qaState is enough.
- **Rate-limit recovery:** If the radar source rate-limits, how many retries before giving up? Recommend: no retries (fail-closed immediately); next 15-min refresh will try again. Simplest, least risky.
- **Radar-only precip (no nowcast):** Edge case: what if the radar source is available but nowcast is not (network error, stale >15 min)? Should the radar precip alone be trusted? Recommend: no. Require both sources to have some evidence before confirming precip. Radar alone is weaker than reconciled evidence.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. FIX-1 (BLOCKING): Correct the test baseline. Plan states '31/31 baseline' but the current uncommitted state has 29 tests (and HEAD has 26). Revise acceptance criterion to 'Baseline smoke suite (29/31 tests) passes without regression, plus 2-3 new radar-aware tests (≥31 total)' OR 'Baseline suite remains at 26 tests (no regression); 5+ new radar-aware tests are added (≥31 total).' Choose one and align the smokeA/smokeB test examples to it.
2. FIX-2 (BLOCKING): Choose the PRIMARY RADAR SOURCE before finalizing the plan. The 'research deliverable' in Phase 1 cannot be deferred into implementation. The plan must name: ONE primary (e.g., 'RainViewer public API'), specify its CORS policy (e.g., 'Allows CORS preflight, no auth required'), give an example query URL, state coverage limits (e.g., '50-country resolution, data gaps over water'), refresh rate, and reflectivity→mm calibration method (if used). Without this, the implementation task is vague and over-scoped.
3. FIX-3 (REQUIRED): Clarify the '>30 min contradiction detection' logic. If it's essential (not phase-2 future-work), specify: (a) where the time-tracking state lives (module-level variable, qaState, or inside atmosphere?), (b) how it's initialized/reset, (c) whether it resets on each fetchRadar() success, (d) what 'log a diagnostic' means (console.warn? qaState flag?). If it's defensive/logging-only, move it to Phase 2 and remove from the core reconciliation rule.
4. FIX-4 (REQUIRED): Verify Open-Meteo minutely_15 availability. The plan names it as a candidate but states 'Check if the existing fetch can include `minutely` precip.' RUN A TEST: call the current Open-Meteo URL (line 623) with `minutely_15=precipitation` added and confirm (a) the API returns minutely data WITHOUT breaking the existing `current=` / `hourly=` fetch, (b) the response payload size is acceptable for a 15-min refresh loop, (c) no NEW API key/secret is required. If (a) fails, REMOVE Open-Meteo minutely from the primary-source list. If (b) or (c) fail, document the trade-off.
5. FIX-5 (REQUIRED): Add explicit moon-regression smoke tests. The smokeA/smokeB lists do NOT include tests for moon opacity/earthshine unchanged by radar. ADD: 'Radar unavailable → moon remains opaque at night' (test that --moongrp and --moonocc stay 1.0 when radar fetch fails), and 'Radar wet but nowcast dry → moon still unlit if new' (confirm that radar-sourced rain does not cause a false moonlight). These verify the render-boundary is not crossed.
6. FIX-6 (REQUIRED): Clarify the stale-state and caching semantics. When radar is available (fresh), should it reset the nowcast's weatherStale clock? If radar is stale (>15 min), should the gate ignore it or hold the last value? Define: 'radarStale' boolean (same as weatherStale logic? independent 15-min clock?), how weatherStale + radarStale combine (both stale ⇒ downgrade? radar fresh, nowcast stale ⇒ radar wins?), and whether qaState.cache reports them independently.
7. FIX-7 (REQUIRED): Set a concrete LOC budget. Plan states 'under 100 lines of net-new logic' but the breakdown is not provided. Estimate: fetchRadar() ~25 lines, gateWeatherCode() signature + radar reconciliation ~15 lines, dBZ→mm conversion (if needed) ~10–20 lines, qaState updates ~10 lines. If the primary source is complex (grid lookup, coordinate transform), add 20–30 more. Recommend: 'Net-new code ≤80 lines (excluding comments); refactoring of existing gateWeatherCode() signature is internal to that function.'
8. FIX-8 (RECOMMENDED): Split the plan into (A) Research/Survey (read-only, choose the primary source), then (B) Implementation (add fetchRadar, integrate gate, qaState). Currently this plan mixes discovery and build, making acceptance ambiguous. A cleaner workflow: Part A recommends ONE source + documents its API contract, Part B implements fetchRadar() + gate logic against that contract.

**Missing risks the spec omitted:**
- MOON REGRESSION RISK (HIGH): Plan adds a new `gateWeatherCode(raw, w, radarW?)` signature extending to three parameters. The moon must stay OPAQUE and non-spinning. The plan correctly prohibits this (FORBIDDEN list includes 'the moon SPINNING/rotating' and 'transparent or empty-slot moon'), but acceptance criteria do NOT mention a smoke test verifying the moon remains opaque after radar integration. If radar code is merged but the moon's opacity is accidentally shared with radar state, a regression is possible. REQUIRED: add explicit smoke tests that moon opacity/earthshine are unchanged by radar presence/absence (e.g., 'moon opaque with radar unavailable', 'moon unlit when radar wet but nowcast dry').
- PAINT BOUNDARY RISK (MEDIUM): Plan modifies `gateWeatherCode()` to accept optional `radarW` parameter and changes reconciliation logic. The plan correctly states 'paint is sole sky-DOM writer' and 'atmosphere is pure', but the reconciliation rule 'radar raining, nowcast clear for >30 min → log diagnostic' introduces implicit time-state tracking (`>30 min`) that lives where? If it's in atmosphere (stateless), how does it count time? If it's module-level state, is it reset properly? REQUIRED: clarify where the '>30 min' timer lives and confirm it does NOT mutate atmosphere or add hidden side effects.
- CLOUD CONTINUITY RISK (LOW): Plan preserves 'Cloud continuity & field identity' via `_cloudFieldSeed`. No changes to cloud generation, only to the gateWeatherCode output. However, if radar evidence causes a rapid code flip (rain ↔ cloud), the `tieRainToClouds()` function may flicker because it reads `data-fx` from the gated code. REQUIRED: verify that rapid code oscillation (radar rain, nowcast dry, radar/nowcast disagree for minutes) does not produce visible flicker in rain display.
- RENDER ORDER RISK (LOW): Plan adds a new `fetchRadar()` function running after (or parallel to) `fetchWeather()`. The plan states 'late fetch → hold state on miss' (fail-closed). But what if `fetchRadar()` resolves AFTER atmosphere() has already sampled the OLD `weatherRadar`? The plan does not specify a transaction/mutation ordering. REQUIRED: clarify that `weatherRadar` is sampled by atmosphere() and gateWeatherCode() only AFTER a successful fetchRadar() completes, not in a race condition.

**Weak acceptance criteria (a broken change could still pass):**
- Acceptance criterion: 'Baseline smoke suite (31/31 tests) passes without regression' — 31/31 is factually wrong (current is 29). A broken implementation that happens to run on the wrong test count could claim acceptance falsely.
- Criterion: 'No new npm dependencies' — verified. But 'Code is under 100 lines of net-new logic' — no line count given for fetchRadar() + gateWeatherCode signature extension + qaState.wxTruth radar fields. Easy to exceed 100 lines if the dBZ→mm conversion is inline (needs calibration logic, fallback). Need a concrete LOC bound.
- Criterion: 'qaState().wxTruth includes radarSource (string or null), radarPrecipMm (number or null), and reconciliationNote' — reconciliationNote is named in the criterion but the smokeA tests don't verify this field. The 'Radar source unavailable / CORS error → gate falls back to nowcast logic' test checks radarStale, but not the content of the reconciliationNote field itself.
- Criterion: 'Define and document ONE primary CORS-safe, keyless radar source in the code comments' — plan lists 6 candidates (RainViewer, Open-Meteo minutely, MET Norway, NWS, KNMI, Vortex) but defers the choice to the 'research deliverable'. A plan is not complete if the PRIMARY SOURCE is not chosen. The implementer will face ambiguity: should I hardcode RainViewer? Should I try all 6 in sequence? The acceptance gate cannot pass until the PRIMARY SOURCE is named.

**Scope concerns:**
- FEATURE CREEP (MEDIUM): The plan includes a '>30 min' reconciliation rule ('if radar and nowcast disagree sharply (radar raining, nowcast clear for >30 min), log a diagnostic'). This adds time-tracking state, a delta-checking loop, and logging logic. The original scope (upgrade gate from conservative to ground-truth) is cleaner: 'if radar says yes and nowcast says no, confirm.' The '>30 min contradiction' clause feels like defensive logging (nice-to-have) not essential. RECOMMENDATION: remove the '>30 min' clause from the core plan and defer logging/diagnostics to Phase 2.
- PHASE SPLIT (MEDIUM): The plan lumps 'Phase 1: Survey (research)' and 'Phase 2: Prototype & QA' and 'Phase 3: Integration' and 'Phase 4: Fallback & bounds' into one spec. But THIS PLAN IS THE RESEARCH OUTPUT — the survey is supposed to CHOOSE the primary source and recommend fallbacks. The spec conflates discovery (Phase 1, which should happen FIRST, in READ-ONLY mode) with implementation (Phases 2–4, which should happen in a SECOND task). RECOMMENDATION: split this into (a) a research-only plan to identify the primary source + document CORS/coverage/latency, and (b) a separate implementation plan once the primary is chosen.
- FALLBACK COMPLEXITY (MEDIUM): Plan lists 'Fallback & bounds: missing radar → hold to nowcast behavior (current, fail-closed).' But also: 'If radar source is unavailable (rate-limited, CORS block, geographic coverage gap), the widget silently holds the last good `weather` state.' What if the last-good state is from 3 hours ago? Current code has `weatherStale` logic at 15 min. Does radar stale reset the 15-min clock or hold independent? The plan doesn't specify. REQUIRED: clarify the stale-state semantics when radar is partially available (fresh sometimes, missing others).
- UNVERIFIED ASSUMPTION: The plan assumes Open-Meteo `minutely_15` is 'already CORS-safe, no new dependencies. Check if the existing fetch can include `minutely` precip.' But the current `fetchWeather()` at line 615–646 does NOT fetch `minutely_15` — it only fetches `current=` and `hourly=`. The plan defers verification to the implementer ('Check if…'). REQUIRED: the research phase MUST verify whether Open-Meteo minutely is available in the existing API call or requires a NEW fetch call (which breaks the 'no new dependencies' / 'single-file' mandate if it adds network latency).

**Grounding issues (claims to re-check against current code):**
- Plan cites 'baseline smoke suite (31/31 tests)' — WRONG. Current uncommitted state has 29 tests (newly added: moonSkyFresh guard + moon orientation + prayer staleness tests). HEAD baseline was 26 tests. The plan must be revised to 29/31 or 26/31 depending on whether the new tests are accepted.
- Plan cites 'tests pass 31/31' as acceptance criterion — this number is unverifiable and creates false confidence. Must be fixed to match actual current test count (29 tests as of uncommitted pass, 26 as of HEAD commit).

**Reviewer notes:** SUMMARY: The plan is WELL-MOTIVATED (upgrade from conservative to ground-truth is a real win) and mostly SOUND (fail-closed behavior, correct render-boundary preservation, moon/cloud immutability), but it has THREE CRITICAL BLOCKERS: (1) test count is wrong (31 vs actual 29/26), (2) the primary radar source is unspecified (6 candidates listed, none chosen), and (3) the '>30 min' contradiction rule adds state-tracking complexity that needs clarification. Once these are fixed, the plan is implementable. VERIFY AGAINST HARD CONSTRAINTS: Moon is OPAQUE (good, explicitly guarded in acceptance), Moon never spins (good, new smoke tests added), no painted dawn (good, plan doesn't touch dawn), static/no-build (good, fetchRadar uses native fetch), render-boundary integrity (good, but missing moon-regression tests), fail-closed (good, missing radar → fallback to nowcast). GROUND AGAINST CURRENT CODE: All line refs verified correct (fetchWeather 615–646, gateWeatherCode 1245–1257, _PRECIP_MIN 1242, atmosphere 1411, qaState 1844–1870, paint 1599). The current uncommitted pass (2026-06-16, round-1 + moon fix) is the baseline — plan correctly references the corner-sun tone-map lift into atmosphere() (done), single isMotionReduced() (done), moonSky._min guard (done), upright moon (done). No conflicts with current state.
