# salah_widget — Architecture & Readiness

A maintainer's map of the widget: who owns what, where state flows, where patches are risky, and the
contracts a future change must honor. Produced by a read-only multi-pass investigation (responsibility/GRASP,
SOLID/CUPID, control-flow, data-lineage/SSA, BASE stale-state, ACID write-safety, normal-form/contracts,
observability) — then a *minimal, justified* hardening pass. **Guardrails:** no rewrite, no abstraction-for-its-
own-sake, preserve the static / no-build / no-dependency / single-file character. Line refs are approximate.

## Two artifacts, one contract

- **`index.html`** — the runtime widget (one self-contained file: CSS + JS + the atmospheric renderer).
- **`builder.html`** — the embed-code generator (separate page, **shares no JS** with the widget).

The *only* coupling between them is the **URL-hash parameter contract**: the builder *writes*
`#lat&lon&label&method&school[&time][&datefmt][&units]` (fixed key order; no `tz` — the widget derives the zone
from the coordinates), and the widget *reads* `location.hash` only. This is correct separation — **do not merge
them.** (The builder forces an iframe re-run with a throwaway `?r=` query because a hash-only change does not
re-run the widget's boot.)

## Runtime pipeline — Physics → State → Render

```
URL hash (immutable config consts)  ─┐
simNow()  [single temporal source]  ─┤
fetchTimings → today/tomorrow → model()                ─┐  DRIVERS (physical truth)
fetchWeather → weather (current/nowcast) + weatherTrack ─┤
   syncWeather() [ADVANCING-gated] / wxAt() / wxDrivers()┤
moonNow()/renderMoon() → moonSky (shared)               ─┘
                         │
              atmosphere(M)   ── ONE pure state vector (~50 named fields, touches NO DOM)
                         │
              paint(A)        ── the ONLY writer of the sky/light CSS custom props + data-fx
                         │
   render() orchestrates: prayer-UI DOM + renderMoon + projectStars + applyTheme(=paint∘atmosphere) + lightning
boot() → ONE requestAnimationFrame loop (~1 Hz) + visibility/IntersectionObserver lifecycle (pauses offscreen)
```

Layer z-order is **implicit in DOM markup order** and relied on for occlusion (sky/stars → cloud deck → moon → arc
→ text; cloud deck paints *over* the moon, which is how heavy cloud hides it). There is one rAF clock; no
independent time loops (a convention, not an enforced boundary).

## Responsibility map (information-expert owners)

| Responsibility | Owner | ~Lines |
|---|---|---|
| Config (parse URL hash → consts) | top-level `q`/`SIM`/`LPOLL`/`DEBUG*` | 435–503 |
| Temporal source of truth | `simNow`/`simDate`/`nowParts`/`partsInTz`/`epochForTzTime` | 517–550 |
| Prayer-time fetch + cache | `fetchTimings`/`loadCache`/`saveCache` | 553–576 |
| Weather fetch + cache | `fetchWeather`/`loadWx` | 586–620 |
| Forecast-track interpolation | `wxAt`/`syncWeather` | 624–646 |
| Weather → 0..1 drivers | `wxDrivers` | 648–664 |
| **Weather truthfulness gate** | `gateWeatherCode` (+ `wxClass`/`_coverCode`/`WX`) | 1213–1251 |
| Moon ephemeris + PBR + position | `renderMoonPBR`/`moonNow`/`renderMoon` (writes shared `moonSky`) | 744–855 |
| Stars (catalog + projection + twinkle) | `buildStars`/`projectStars` | 865–946 |
| Prayer model (current/next/progress) | `model` | 977–1001 |
| Solar-prayer arc (SVG) | `drawArc` | 1004–1147 |
| Sun geometry | `sunAltAt`/`sunMetrics` | 1153–1158 / 1153 |
| Sky colour (sole source) | `skyLum`/`physSky` | 1167–1200 |
| Clouds (canvas density field) | `paintClouds`/`tieRainToClouds` | 1306–1367 |
| **Atmosphere state vector** (pure) | `atmosphere` | 1376–1559 |
| **Sky DOM writes** (sole sky writer) | `paint` | 1535–1700 |
| Lightning channel | `genLightning`/`_midDisp` | 1686–1701 |
| Render orchestration | `render` | 1703–1807 |
| QA / observability | `window.qaState` | 1817+ |
| Boot + rAF loop + lifecycle + motion telemetry | `boot` (closures) | 1772+ |

### Responsibility tangles (SRP), ranked
1. **`paint(A)` does derivation, not just DOM writes.** The corner-sun block computes Kasten–Young airmass,
   Beer–Lambert + cloud transmittance, a CCT blackbody colour and an ACES tone-map *inline*, and it also mutates
   `cloudState`. So "the only place state reaches the DOM" is true *for the sky*, but `paint` is no longer pure
   presentation. *Deferred follow-up:* lift the sun tone-map math into `atmosphere` (state) so `paint` only writes.
2. **`render()` mixes prayer-UI DOM writes with atmosphere orchestration.** "paint is the only DOM writer" holds
   only for the *sky*; prayer-list/arc/date DOM is written directly in `render`. (Correctly scoped in DESIGN.)
3. **`boot()` carries the whole motion-telemetry subsystem** (`updateMotionDbg`/`_cloudAlphaNow`/`_starSampleNow`)
   as inner closures. *Deferred:* extract to top-level `DEBUGMOTION`-gated helpers in a debug-tooling pass.

**Deliberately NOT split (anti-over-engineering):** `atmosphere(M)` (one cohesive state vector) and `drawArc(M)`
(one cohesive SVG output). Splitting these would add indirection without removing drift.

### High-risk mutation points (shared mutable state)
- **`moonSky`** (written by `renderMoon`, read by `atmosphere`/`projectStars`/`qaState`): **temporal coupling —
  `renderMoon` must run before `atmosphere` in a tick**, so `atmosphere` is "pure" only given that ordering.
- **`cloudState`** (mutated in `paint` ease-vs-snap branch, read in `paintClouds`): the no-slideshow continuity
  invariant lives here — easy to break with a careless reseed.
- **`tz`** (`let`, reassigned from the Aladhan response): `cacheKey`/`wxKey` are captured once at load, so a wrong
  URL `tz` hint causes a benign one-time cache miss + a small clock re-anchor near t0.
- **`_REDUCED` (paint) vs `_RM` (loop) vs the CSS `prefers-reduced-motion` block** — *three* places that must
  agree on reduced motion (cleared together by `?motion=full`). A known cross-scope drift surface; keep in sync.

## Control-flow (CFG) findings
- **Boot:** DOM scaffold builds before data; a hard `if(!lat||!lon){ showError; return }` means **the rAF loop
  never starts without coordinates**. Cached times render first so the card isn't blank during the prayer fetch.
- **Prayer fetch has three call-sites with three error policies:** boot (`await`, shows error if no `today`),
  tomorrow-prefetch (swallowed), and **day-rollover (swallowed, no retry, no stale signal)** — see Remaining risks.
- **`fetchWeather` guards, in order:** `SIM.wx` → reentrancy (`wxBusy`) → 15-min freshness (needs *both*
  `weather` and `weatherTrack`) → 60-s try-throttle; `finally` always clears `wxBusy`; network/parse errors are
  swallowed and the last good state is held (Basically Available).
- **Render loop:** `render()` runs once per sim-second; the cloud canvas repaints ~13 fps; reduced-motion paints
  one frozen cloud frame; the loop stops entirely when hidden/offscreen.

## Data-lineage (SSA) — classification of key values
- **raw → never to render policy:** `weather.code` (raw current), `weatherTrack.weather_code` (raw forecast).
  These must pass through `gateWeatherCode` before any precip/thunder visual. *Verified:* `data-fx`, the chip, and
  precip visuals all consume the **gated** code, never the raw one.
- **normalized:** `wxDrivers()` 0..1 (heat/cold/wind/humid/cloud/haze), the `atmosphere(M)` state vector.
- **live (real-time):** `weather` (current/nowcast block), `model()` prayer state, `simNow()`.
- **simulated:** anything under `SIM.*` (`simWx`/`simTime`/`simMoon`/…) and `ADVANCING` forecast-derived weather.
- **cached/stale:** `today`/`tomorrow` (per-day localStorage), `weather`/`weatherTrack` (15-min), `cloudState`
  (eased), `_starsProjected`. See BASE below.
- **identity:** `_cloudFieldSeed` (lat+lon+day+`?seed`) — stable per location+day; never reseeded on refresh.

## Canonical contracts (documented, already implied by the code — no new layers added)
- **WeatherCurrent** = the `current=` block on `weather` (`{code,temp,feels,rh,dew,wind,windDir,gust,cloud,
  cloudLow,cloudMid,cloudHigh,precip,rain,showers,snow,vis,isDay, src:"current"|"sim"}`).
- **WeatherForecastTrack** = `weatherTrack` (`{ep:[…], <hourly field>:[…]}`), interpolated by `wxAt(ms)`.
- **WeatherDisplayState** = the *gated* condition: `wxClass(gateWeatherCode(raw, weather))` → `data-fx`.
- **AtmosphereState** = the object `atmosphere(M)` returns (the renderer's whole input contract).
- **QAState** = `window.qaState()` (`{sim,sunEl,wx,wxTruth,cache,render,clouds,stars,sky,moonTruth}`).
The hash param order is canonical (builder emits a fixed order). One name per concept: prefer **current /
nowcast / observed** for the live block and **forecast / track** for the projection — never interchange them.

## BASE — soft state & convergence
| Stale thing | Refreshes | Replaced by | Must NOT assume while stale |
|---|---|---|---|
| Prayer cache (`today`/`tomorrow`) | day rollover; boot re-fetch | fresh Aladhan day | that times are for *today* after a failed rollover |
| Weather current (`weather`) | every ~15 min / 30 s loop tick | fresh `current=` block | that it is "now" to the second |
| Forecast track (`weatherTrack`) | same fetch | fresh 3-day hourly | that it is observed (it is a forecast) |
| Display condition (`data-fx`) | each render from gated code | recomputed | n/a (derived, not stored) |
| Cloud identity (`_cloudFieldSeed`) | only on new day / `?seed` | same-day stable | n/a |
**Non-negotiable, upheld:** stale **forecast** is never shown as live observed — `syncWeather` early-returns
unless `ADVANCING`, and the precip gate fails safe to the cloud state. `qaState().cache` now exposes ages +
`weatherStale`, and `qaState().wxTruth` the source chain.

## ACID — write/output safety
- **builder output** is generated atomically per `update()` (string built, then assigned to the textarea +
  iframe `src`); no partial mutation, no cross-contamination of widget runtime state (separate page). Durability
  is trivial (it regenerates from the form). No file writes.
- **localStorage** writes (`saveCache`, weather cache) are single `setItem` calls wrapped in try/catch.

## Observability (added this pass — Stage 1, no visual change)
`window.qaState()` now reports the full required surface: `wxTruth` (currentWeatherSource, forecastTrackSource,
rawCode, **rawForecastCode**, observedPrecipMm, activePrecip, activeThunder, displayCondition, **finalDataFx**,
downgradeReason, advancing, cloudFieldSeed); **`cache`** (weatherSource, weatherAgeSec, weatherStale,
lastWeatherRefresh, forecastTrackLoaded, prayerDate, prayerLoaded, tomorrowLoaded, simulated); **`render`** (a
real last-rendered summary: currentKey/nextKey/leftMin/progress/fx); plus `clouds`/`stars`/`sky`/`moonTruth`.
On-card debug overlays: `?debugLayers=1`, `?debugMoon=1`, `?debugMotion=1` (rAF/cloud rates, cloud/star Δ).

## Characterization smokes (added: `tests/smoke.html`, no-build, browser-runnable)
Pure-function smokes call the global gate directly (deterministic, no network): dry forecast-thunder downgrades;
heavy-precip thunder kept; rain-without-precip downgrades; precip-supported rain kept; clear/cloud codes not
precip-gated; `wxClass` mapping. Integration smokes (sim weather) read `qaState()`: dry-thunder downgrade +
reason + `data-fx`; precip-supported rain; fog ≠ rain; new/below-horizon moon = opaque calendar disc with **zero
moonlight**; physical moon up = `--moongrp`/`--moonocc` ~1 + moonlight on; **no `.falsedawn`/`.truedawn`
elements**; cloud identity stable across reads; observability surface present + not-stale under sim.

## Exact changes made this pass
1. **FIX (correctness):** `sunAltAt`'s declination clamp `24°` → **`27.5°`** to match `drawArc` — they are
   documented to "match exactly," but the differing clamp let the sky-sun elevation diverge from the arc when the
   day-length-fitted declination lands in 24°–27.5° (near solstice). Now consistent.
2. **Observability (Stage 1):** added `qaState().cache`, `qaState().render`, and `wxTruth.rawForecastCode` +
   `wxTruth.finalDataFx`; `debugMotion` `starΔ` samples a *visible* twinkling star.
3. **Coherence:** removed the dead `corona` atmosphere scalar (computed + diagnosed but painted nothing; the real
   aureole is `lunarCorona`→`--mcorona`) and its `qaState`/debug refs (now report `lunarCorona`).
4. **Truthfulness gate:** Belt of Venus no longer shows (`0.25`→`0`) under overcast/precip/fog (it needs a
   clear-ish anti-solar sky).
5. **Tests:** added `tests/smoke.html`.
(Prior, already in place and confirmed load-bearing: weather current-vs-forecast separation + the precip/thunder
truthfulness gate, cloud continuity/advection, painted-dawn removal, opaque/calendar moon, qaState/debugMotion.)

## Deferred follow-ups (documented, intentionally not done — out of minimal scope / higher risk)
- **Shared `solarElevationDeg(M,a)` helper** for `drawArc` + `sunAltAt` (now clamp-aligned; the duplicated math
  remains a small drift surface). Refactors the sacrosanct arc — defer to a dedicated pass.
- **Lift the corner-sun tone-map** out of `paint` into `atmosphere` (purity of the render boundary).
- **Day-rollover robustness:** a failed rollover fetch with no new-day cache silently shows the previous day's
  times. Repro: cross sim-midnight offline with an empty cache for the new day. Root cause: `loop()` advances
  `_lastDateStr` before confirming the new day's data, and the `.catch` is empty. Fix needs a throttled retry or a
  subtle stale indicator — left as a follow-up to avoid a half-fix.
- **Reduced-motion single source:** unify `_REDUCED`/`_RM` and the CSS media query behind one flag.
- **File splits (Stage 5):** NOT justified — the investigation did not show index.html is too fragile to patch;
  splitting would break the single-file static character. Keep as one file.

## Remaining risks
- The `moonSky` ordering coupling (renderMoon-before-atmosphere) is convention, not enforced.
- Reduced-motion correctness depends on three sites staying in agreement.
- Weather "current" is an Open-Meteo nowcast, **not radar** — the gate is conservative, not ground-truth.
