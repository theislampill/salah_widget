# salah_widget — Architecture & Readiness

A maintainer's map of the widget: who owns what, where state flows, where patches are risky, and the
contracts a future change must honor. The current contract below incorporates the bounded 2026-10-02 source
composition; dated June notes are historical changes, not qualification of current bytes. **Guardrails:** no
rewrite, no abstraction-for-its-own-sake, preserve the static / no-build / no-dependency character. Function
names identify owners; source checks do not establish native pixels, motion, installation or public state.

## Three artifacts, one config contract

- **`index.html`** — the runtime widget (self-contained CSS + JS + atmospheric renderer; reads `location.hash`).
- **`builder.html`** — the embed-code generator (portable **and** self-configuring snippets).
- **`config.js`** — `window.SalahConfig`, the **shared** `WidgetConfig` module (parse / validate / normalize /
  serialize / load-save-clear-local / coarse-detect / precedence). Loaded as a classic same-origin `<script>`
  **before** the inline script of both pages.
- **Install wizard** (`install.sh` / `install.ps1` + `presets/salah-widget.tablissng.json`) — a *separate, optional*
  CLI flow (not part of the runtime) that stages the TablissNG extension + preset for **manual** import (never a
  silent install). The builder's **Install widget** button copies the one-liner and, when the builder's config
  differs from the plain `#local=1` default, carries it via a `SALAH_WIDGET_HASH` env var that the wizard bakes into
  the preset's iframe (replacing `#local=1`). The copied command fetches published `main`; candidate checks use
  reviewed local files. Both offline preview switches branch before prompts/staging/artifact consumers.
  Normal Bash execution owns fresh private scratch plus a retained home bundle; Windows retains its TEMP-based
  staging path. Browser installation and dashboard-replacing preset import remain manual. Usage, terminal and
  retained-file boundaries are in [README](README.md#one-line-install-optional-setup-wizard).

**Embed-size invariant:** the iframe wrapper **must equal the widget card** (`index.html` `.c` = **325×530**). The
builder preview, the copy snippet, `README.md`, and the preset all use `325×530`; an oversized wrapper only adds
invisible transparent margin (a `330×534` wrapper around the 325×530 card was the cause of a 4px builder misalign).

**2026-06-16 — the single-file rule was deliberately relaxed (by maintainer decision)** so config logic can never
fork between widget and builder (the local-mode task's "do not fork config logic" requirement). `config.js` is the
*only* extracted module; everything else stays inline. `index.html` keeps a one-line **legacy fallback** (hash-only
parse) if `config.js` fails to load, so a 404 degrades instead of white-screening.

The coupling is the **`WidgetConfig` contract in `config.js`**: the builder serializes a fixed-site portable
fragment or `#local=1` with explicit method/units/appearance preferences. Both builder modes include the selected
appearance, including default `appearance=glass`; a generic `#local=1` retains automatic defaults. Portable
fragments omit private acquisition evidence. The widget resolves `location.hash` through the same module;
saved preferences take precedence in local/prefer-local mode. (The builder still forces an
iframe re-run with a throwaway `?r=` query because a hash-only change does not re-run the widget's boot.)
Persistence: `salah_widget:config:v1` (separate from prayer/weather caches). Original fix time/accuracy remain
private and survive preference saves without renewed acquisition age. Refused save retains session choices;
refused Reset retains the selected config and stops before detection. **Stale localStorage never overrides a
hardcoded embed.** Runtime re-config (`applyConfig`) is in-memory (no reload); `cacheKey`/`wxKey` are functions so
they track config changes. See DESIGN.md “Config resolution & local mode” for precedence and feedback.

## Runtime pipeline — Physics → State → Render

```
resolved config → runtime generation/target           ─┐
simNow() [wall by default; explicit anchored preview] ─┤
admitted prayer records → today/tomorrow → model()     ─┤  DRIVERS
eligible model current / ADVANCING forecast track     ─┤
   selectedWeather() / weatherDecision() / wxDrivers() ┤
renderMoon() → fresh moonSky + matching projectStars()─┘
                         │
              atmosphere(M)   ── ONE pure state vector (~50 named fields, touches NO DOM)
                         │
              paint(A)        ── sky/light CSS custom props + data-fx + explicit cloud-state step
                         │
render() → prayer/arc/calendar writers + lunar/stellar geometry + applyTheme + initial reveal
boot/applyConfig → ONE requestAnimationFrame loop + accepted dirty-state adoption
cloud canvas → bounded monotonic visual elapsed; lifecycle pauses hidden/offscreen
```

Layer composition relies on markup/CSS: the cloud deck can cover the Moon, while the filtered stellar
background has an independent luminance cutout registered to the lunar image/transform. Stars, glints and
Milky Way remain masked through lunar twilight fade; daylight withdraws the surface/cutout. Initial decorations
start hidden over a neutral card and reveal on consumed lunar geometry plus matching stellar projection.
Decoded PBR texture readiness is separate; pending/failed texture is unavailable, not a successful calendar
disc. Native first-frame/edge/day-no-hole evidence is still required. One existing rAF loop coordinates scene
updates; CSS animations remain explicit consumers of the same lifecycle/reduced-motion state.

## Responsibility map (information-expert owners)

| Responsibility | Owner |
|---|---|
| Config, private fix evidence, persistence outcomes | `SalahConfig`, `bindConfig`, settings handlers |
| Generation/operation/attempt identity | `beginRuntimeGeneration`, `beginRequest`, `beginAttempt`, eligibility/finish helpers |
| Civil authority and zoned inverse | `simNow`/`simDate`/`nowParts`/`partsInTz`/`epochForTzTime` |
| Prayer admission/cache/day adoption/recovery | `admitPrayerRecord`, `fetchTimings`, `adoptPrayerBundle`, `maintainPrayerDay`, `loadPrayerData` |
| Model endpoints, provider calendar selection/access | `model`, `selectCalendarDisplay`, `renderCalendarDates` |
| Weather admission/current expiry/captured target | `admitWeatherRecord`, `weatherEligibility`, `selectedWeather`, `captureWeatherTarget`, `fetchWeather` |
| Model forecast and bounded radar diagnostics | `wxAt`, `syncWeather`, `wxFetchJson`, `fetchRadar`, `wxRadarSample` |
| Weather permissions and synthetic QA | `admitWeatherFixture`, `reconcileWeatherEvidence`, `weatherDecision` |
| Moon ephemeris/PBR/fresh observation | `moonNow`, `renderMoonPBR`, `renderMoon`, `moonGeometryObservation` |
| Stars, glints and projection/appearance | `buildStars`, `projectStars`, `refreshStarAppearance` |
| Initial scene/surface/reveal | `beginSkyScene`, `updateSkySurface`, `commitSkyScene` |
| Solar-prayer arc and shared solar elevation | `drawArc`, `solarElevationDeg`, `sunAltAt`, `sunMetrics` |
| Sky colour and pure atmosphere vector | `skyLum`, `physSky`, `atmosphere` |
| Cloud identity/visual interval/wind/coverage | `cloudSceneIdentity`, `advanceCloudMotion`, `applyCloudState`, `paintClouds` |
| Sky writes and permitted weather particles | `paint`, `tieRainToClouds`, `genLightning` |
| Render, single loop, lifecycle and telemetry | `render`, `startRenderLoop`, `updateMotionDbg` |
| Actual consumed/painted diagnostics | `window.qaState` |

### Responsibility tangles (SRP), ranked
1. ~~`paint(A)` mutates `cloudState` + does tone-map derivation~~ **RESOLVED (2026-06-16):** the corner-sun tone-map
   was lifted into `atmosphere` (returns `sunCoreRGB`/`sunMidRGB`/`sunCloudT`; `paint` writes them), and the
   `cloudState` ease/snap mutation was extracted into `applyCloudState(A)` (called by `paint` as a clearly-separated
   side-effect step). `paint` is now sky-CSS writes + that one explicit call.
2. **`render()` mixes prayer-UI DOM writes with atmosphere orchestration.** "paint is the only DOM writer" holds
   only for the *sky*; prayer-list/arc/date DOM is written directly in `render`. (Correctly scoped in DESIGN.)
3. ~~`boot()` carries the motion-telemetry subsystem as inner closures~~ **RESOLVED (2026-06-16):**
   `updateMotionDbg`/`_cloudAlphaNow`/`_starSampleNow`/`_motHist` are now top-level (`DEBUGMOTION`-gated); the loop's
   rate counters stay in `boot` and are passed into `updateMotionDbg(rafPS,cloudPS,cEl)` — boot lifecycle untouched.

**Deliberately NOT split (anti-over-engineering):** `atmosphere(M)` (one cohesive state vector) and `drawArc(M)`
(one cohesive SVG output). Splitting these would add indirection without removing drift.

### High-risk mutation points (shared mutable state)
- **`moonSky`** (written by `renderMoon`, read by `atmosphere`/`projectStars`/`qaState`): **temporal coupling —
  `renderMoon` must run before `atmosphere` in a tick**, so `atmosphere` is "pure" only given that ordering.
- **`cloudState`** (eased by `applyCloudState`, read in `paintClouds`): integrate the preceding interval with old
  wind before replacing drivers. Population survives ordinary day/zone/weather changes; accepted target or
  explicit preview identity replacement reconstructs deterministically.
- **`tz`** (adopted from admitted Aladhan data): dynamic keys and the captured selected-cache timezone precede
  day selection. Corrected-day fetches share the operation budget; obsolete generations cannot adopt them.
- **Reduced motion** — the two duplicated JS `matchMedia` checks are unified behind one **live** helper
  `isMotionReduced()` (`paint`'s `_REDUCED` and the loop's `_RM` both call it; `&motion=full` overrides). The CSS
  `@media (prefers-reduced-motion)` blocks read the SAME native signal gated by the `.motionfull` class — they are
  the live native signal, not duplicated logic. One decision, consulted by JS and CSS.

## Control-flow (CFG) findings
- **Boot/apply:** validate finite bounded coordinates (zero is valid), establish generation/target and build the
  scaffold once. Admitted selected cache can render before network success. Explicit invalid clock anchors
  preserve card/Settings access while withdrawing clock-dependent output.
- **Request ownership:** capture config/target/day/cache identity. Attempts remain eligible through headers,
  body, parse and adoption under real elapsed deadlines. Generation replacement invalidates slot identities
  before cancellation; obsolete completion/finally cannot overwrite or release a replacement owner.
- **Prayer recovery:** at most three ten-second attempts, 900/1800ms backoff and at most one corrected-day fetch
  within that budget. Matching tomorrow can become current; accepted state/completion marks render dirty. The
  existing visible loop provides sixty-second elapsed recovery starts; hidden/offscreen is not background work.
- **Weather/radar:** bounded complete JSON and image operations retain eligible model data on rejected refresh.
  Current expiry withdraws render authority even if readable cache/track remain. Weather inputs ease cloud
  appearance, but expired/outage synthetic evidence withdraws particles immediately.
- **Render loop:** changed civil seconds or dirty state call `render`; cloud canvas cadence is about 13 fps.
  Reduced-motion holds a cloud frame, and hidden/offscreen pauses/rebases visual elapsed. A missing-frame gap
  over two seconds is discarded as suspension. These bounds cannot preempt blocked JavaScript.

## Data-lineage (SSA) — classification of key values
- **raw → admitted → reconciled → painted:** `weather.code` and hourly codes are model inputs, not local
  observation. `weatherDecision` consumes eligible model/present/forecast states; raw/gated WMO or radar alpha
  alone grants no strong live effect. The chip retains useful model estimates while particles stay off.
- **normalized:** `wxDrivers()` 0..1 (heat/cold/wind/humid/cloud/haze), the `atmosphere(M)` state vector.
- **ordinary wall view:** eligible Open-Meteo model current, `model()` prayer state and default `Date.now()`.
  Explicit `timeScale=1` remains an anchored ADVANCING preview, not the default wall authority.
- **simulated:** anything under `SIM.*` (`simWx`/`simTime`/`simMoon`/…) and `ADVANCING` forecast-derived weather.
- **cached/stale:** `today`/`tomorrow` (per-day localStorage), `weather`/`weatherTrack` (15-min), `cloudState`
  (eased), `_starsProjected`. See BASE below.
- **identity:** signed accepted coordinates, explicit seed and preview anchor/rate; initial day contribution is
  captured once. Ordinary day/month/year/weather refresh retains population. An explicit seek reconstructs
  with zero initial displacement. Actual monotonic elapsed, not changed civil probe arguments, advances travel.

## Canonical contracts (documented, already implied by the code — no new layers added)
- **WeatherCurrent** = the `current=` block on `weather` (`{code,temp,feels,rh,dew,wind,windDir,gust,cloud,
  cloudLow,cloudMid,cloudHigh,precip,rain,showers,snow,vis,isDay, src:"current"|"sim"}` plus admission/quantity/target metadata).
- **WeatherForecastTrack** = admitted `weatherTrack` (`{ep:[…], <hourly field>:[…]}`); `wxAt(ms)` interpolates
  eligible continuous fields, while preceding-hour precipitation remains stepped.
- **WeatherDisplayState** = reconciled `weatherDecision` → atmosphere/`data-fx`, model cue and separate permissions.
- **SyntheticPresent** = `synthetic-present-v1` admitted fixture with exact identity, target generation, qualified
  coverage/health, underlying observation time and exclusive lease. It is not a live provider/hash switch.
- **AtmosphereState** = the object `atmosphere(M)` returns (the renderer's whole input contract).
- **QAState** = `window.qaState()` (`{sim,sunEl,wx,wxTruth,cache,render,clouds,stars,sky,moonTruth}`).
The hash param order is canonical (builder emits a fixed order). **Model current**, **model forecast** and
**qualified synthetic present** have different authority. Current amounts describe a preceding interval;
hourly amounts describe a preceding hour, not instantaneous intensity/onset/probability.

## BASE — soft state & convergence
| Stale thing | Refreshes | Replaced by | Must NOT assume while stale |
|---|---|---|---|
| Prayer cache (`today`/`tomorrow`) | selected day/zone/config re-adoption; visible recovery | admitted matching record | that retained prior-day timings are today's after failed rollover |
| Weather model current (`weather`) | bounded refresh; source and receipt eligibility each consumption | eligible `current=` record | that readable expired cache grants current inputs or local observation |
| Forecast track (`weatherTrack`) | bounded refresh | admitted 3-day hourly | that it is observed or live particle authority |
| Display condition (`data-fx`) | each render from reconciliation | recomputed | that cloud easing may delay withdrawal of particle permission |
| Cloud population (`_cloudFieldSeed`) | accepted target/seed/explicit preview replacement | deterministic population | that ordinary midnight or timezone/weather refresh requires reseeding |
`syncWeather` is ADVANCING-gated. Live model conditions keep an ≈ estimate cue; absent/expired current becomes
unknown. Nearby precipitation/arrival remain unavailable. Unknown observation is not observed dry. Current
source and receipt times must both be no older than fifteen minutes; rejected records never renew that age.

## ACID — write/output safety
- **builder output** is generated atomically per `update()` (string built, then assigned to the textarea +
  iframe `src`); no partial mutation, no cross-contamination of widget runtime state (separate page). Durability
  is trivial (it regenerates from the form). No file writes.
- **localStorage** writes (`saveCache`, weather cache) are single `setItem` calls wrapped in try/catch.

## Observability (added this pass — Stage 1, no visual change)
`window.qaState()` reports the actual target/fix age, model/present/disagreement, source/receipt/quantity,
spatial/horizon/forecast, lane and particle permissions in `wxTruth`. Its legacy `observedPrecipMm` field refers
only to qualified synthetic amount, not live model authority. `cache` includes eligibility, prayer staleness,
recovery and request ownership; `render`, calendar, clouds, stars, sky and moon diagnostics expose consumed/
painted state. A fresh diagnostic recomputation is not automatically a last-painted or native-pixel observation.
On-card debug overlays: `&debugLayers=1`, `&debugMoon=1`, `&debugMotion=1` (rAF/cloud rates, cloud/star Δ).
Append these suffixes to the configuration fragment after `#`; see [complete recipes](DESIGN.md#url--hash--debug-parameters).

## Characterization smoke contract (`tests/smoke.html`, no-build)

The instrument runs **automatically on navigation**. Its private injected config stores and preparse wrapper
storage isolation prevent real configuration/cache mutation. Controlled/frozen Date and suppressed fonts make
this a contained correctness instrument, not normal-entry appearance, default live M0 or public-safety proof.
PASS requires every declared group/assertion; assertion/bootstrap errors are FAIL. Missing callback, assertions
or readiness is INCOMPLETE, with declared/executed/missing names retained. The wrapper binds run, attempt, UUID,
hash and source hash; changed source within a run fails. See HANDOFF for the reviewed successor identity and
its still-separate native qualification. No source-test total can substitute for that native ledger.

## Historical hardening changes (2026-06-16)
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
(The old code-only weather gate and radar confirmation model were subsequently superseded by the model-only
live policy above; these dated records are not current observation authority.)

## Deferred follow-ups (documented, intentionally not done — out of minimal scope / higher risk)
- ~~**Shared `solarElevationDeg(M,a)` helper** for `drawArc` + `sunAltAt`~~ **DONE (2026-06-16):** extracted as a
  pure, bit-identical refactor (`sunAltAt` is now an alias; `drawArc.elevDeg` calls it) — verified by before/after
  hash equality of `drawArc(model())` + a `sunAltAt` grid across refinement/phi≈0/polar paths. The duplication
  drift surface is closed.
- ~~**Lift the corner-sun tone-map** out of `paint` into `atmosphere`~~ **DONE (2026-06-16):** byte-identical move;
  `atmosphere` returns `sunCoreRGB`/`sunMidRGB`/`sunCloudT`, `paint` only writes them.
- ~~**Day-rollover robustness**~~ **DONE (2026-06-16):** the rollover branch advances the day only on confirmed
  data (cache-hit or fetch-success), throttles the refetch (`_ROLLOVER_RETRY_MS`), exposes `prayerStale`/
  `rolloverPendingMs` in `qaState().cache`, and shows a quiet worded "stale" cue by the Hijri date.
- ~~**Reduced-motion single source**~~ **DONE (2026-06-16):** one live `isMotionReduced()` consulted by `paint` and
  the loop; CSS keeps the native `@media`/`.motionfull`. (`moonParallactic` + the unused `chi` return were also
  removed as dead code after the moon-upright fix.)
- **File splits (Stage 5):** NOT justified — the investigation did not show index.html is too fragile to patch;
  splitting would break the single-file static character. Keep as one file. *(Two smaller SRP extractions were
  done — `applyCloudState` out of `paint`, and the debugMotion telemetry out of `boot` — but these are not a file
  split; the widget stays one self-contained file.)*

## Remaining risks
- The `moonSky` ordering coupling (renderMoon-before-atmosphere) has a consumed observation binding epoch
  minute, local minute and target/zone context. `applyTheme` records actual paint status/observation and warns
  once on explicitly stale consumed geometry. Missing provenance is unavailable; paint failure preserves the
  failed status and ordinary error behavior. This diagnosis/initial-reveal guard is not general reorder
  enforcement or native pixel evidence; later diagnostic recomputation must not overwrite consumption history.
- Reduced-motion is unified behind one live `isMotionReduced()` (JS) + the native `@media`/`.motionfull` (CSS);
  both read the same signal, so the old three-site drift surface is closed.
- The selected live adapters provide useful model estimates and diagnostic tiles, not qualified local wet/dry/
  lightning/nearby/arrival evidence. Strong live effects remain off. Qualified synthetic positives exercise
  admission/withdrawal consumers but establish no provider skill. No new provider is added.
- Calendar convention/anomalies and ambiguous temporal inverses remain explicitly unavailable/neutral where
  source records cannot establish them. Retained provider/cache data alone earns no current-day claim.
- Native first entry, real decoded PBR, stellar-mask edges, real-font/default-glass/contrast readability, OS
  reduced/full motion and final composed browser smokes remain separate evidence requirements. The round-4
  adaptive-performance governor is held; no comparative CPU/battery or public qualification is implied.
