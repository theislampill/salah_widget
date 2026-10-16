# salah_widget — DESIGN

A static Islamic prayer-times widget embedded as an iframe (e.g. in TablissNG).
The CP9/V5 renderer and subsequent native repairs retain frozen V1. Native authoring
lives in `src/native/`; `python tools/build_native.py` generates the root entries,
worker and offline expansion. See [current ownership and qualification](docs/real-sky/INTEGRATION.md).
The native design below predates CP9: synthetic star/glint producers are
superseded by the admitted catalogue and registered diffuse field. Historical
motion claims do not qualify the new renderer.

The unmerged R0021 startup candidate evaluates a compact V5 receiver tier and
real-catalogue anchors for the current native scene while full sources refine.
It preserves the delivered R0022 H1 mapping and the approved Moon footprint,
opacity and Earthshine. Its initial tier is not completed terrain refinement;
strict startup/continuous-frame qualification remains open. See the
[current execution record](docs/real-sky/R0021_STARTUP_EXECUTION.md).

The deployed renderer includes the supplied V5 terrain Moon on CP9. Native phase,
prayer and settings ownership is retained; a WebAssembly worker produces a
terrain preview and then angular refinement. The received PR42 repair withholds the
earlier PBR loading/failure substitution, retains
an independently current refined surface during replacement, and can bridge
with the same full-spatial V5 terrain's explicitly labelled angular preview.
The preview uses the same material, relief, Earthshine and display mapping;
it is not called completed adaptive refinement. The fixed V5 profile,
metric data and kernel are unchanged. A current terrain result supplies the device-resolution detail canvas;
the base excludes the duplicate Moon and the legacy SVG surface is hidden while
the detail result is current. Final visual acceptance requires a current surface
meeting the completed adaptive quality criterion, with worker-to-pixel evidence;
a pending replacement does not invalidate an otherwise eligible full surface.
Loading and preview screenshots are not final qualification. Target, seek and
epoch fences and the original 0.0416-device-pixel geometric limit still apply.
See [Moon integration](docs/moon/INTEGRATION.md) and the
[receiving qualification](docs/moon/QUALIFICATION.md) for measured latency,
opaque composition, file entry and remaining limits. Final refinement takes
seconds to minutes depending on browser; it is not a 60fps renderer.

PR42's immediate atmosphere and final sky share one explicit display policy:
median atmospheric luminance metering and chromaticity-preserving compression.
Twilight limits automatic exposure around a declared 9% civil-twilight display
reference; it does not normalize falling radiance into a constant bright card.
A display-only colour ratio uses CP6's retained Patat near-zenith B/V reference,
preserving directional variation and luminance. Applying that site/zenith fit at
other locations and angles is a presentation approximation, not local spectral
calibration or a replacement multiple-scattering model. Its influence smoothly
releases into the established daytime path by +10 degrees. Prayer names have
no authority over this mapping. Physical twilight remains after the body sets.
Only the solar aerosol forward excess above isotropic phase density registers
to the native corner Sun; the non-forward atmospheric wing stays in camera space.
Perspective background flux is converted to display surface brightness before
metering. Raw reference radiance, physical observer/Sun, Rayleigh/path
extinction, horizon, Moon and star projection remain unchanged. This is a calendar
presentation adaptation, not a new calibrated radiance model. The head computes
the bounded atmosphere before static markup paints, from the shared accepted
saved/manual configuration and native wall clock; no optional catalogue, diffuse
asset or Moon solve gates prayer controls. Cached and network prayer bootstrap
must also republish the accepted atmosphere before yielding after native scene
adoption; ordinary animation still has one final presentation opportunity.
See the H1–H8 repair record in
[STARTUP_CLOUD_HOTFIX.md](docs/real-sky/STARTUP_CLOUD_HOTFIX.md).

The selected R0022 lunar display contract applies a lunar-only soft shoulder
at the original physical direction, with knee 0.003 and shoulder 0.020 in the
original exposure-times-luminance domain. Raw lunar and atmospheric fields stay
separate from mapped output. Non-lunar contributions, V5 material/body geometry,
catalogue, weather transmission and currentness remain independently owned.
The owner accepted the canonical clear full card; remaining qualification and
delivery are recorded in [LUNAR_DISPLAY.md](docs/real-sky/LUNAR_DISPLAY.md).

**Companion docs:** [`ARCHITECTURE.md`](ARCHITECTURE.md) — the maintainer's responsibility/data-flow/contract map
and risk list. [`OPTICS.md`](OPTICS.md) — the per-phenomenon physical-family taxonomy + gating. [`AGENTS.md`](AGENTS.md)
— how to work here + PASS/FAIL gates. [`tests/smoke.html`](tests/smoke.html) — no-build characterization smokes.

## Purpose & design philosophy

Show the day's prayer times truthfully and beautifully, with a **living sky** that reflects the real sun, moon,
and weather at the configured location — without ever lying about conditions. Physics is the *source of truth*;
the art is "realism-adjacent" (believable, never random). Two standing rules:

- **Truthfulness over drama.** The widget never claims a condition (rain, thunderstorm) it cannot support with
  evidence. See "Weather truthfulness".
- **Screenshots override metrics.** A passing number means nothing if the rendered pixels look wrong.

## Visual hierarchy

1. **Hero**: the current-period name + the large next-prayer time + countdown — always the most readable element.
2. **Solar-prayer arc**: the sun's elevation curve with the prayer markers and the live "eye-of-needle" position.
3. **Prayer list**: the six rows, with the current row bordered and the next row accent-coloured.
4. **Header belt** (top) and **date footer** (bottom) — secondary.
5. **Sky/atmosphere**: behind everything (z-index 0), never competing with the foreground for legibility.

## Fixed layout invariants (do not regress)

- Card is a fixed **325×530** with `overflow:hidden`. Margins, the prayer panel, the arc, the list grid, and the
  **date footer must stay fully visible** (the footer was clipped once when the header grew — never again).

Either CE or AH is a stable native button that opens the same labeled Calendar dates dialog. The compact footer, accessible names and complete values consume one last-painted calendar projection, including any preview, unavailable/stale explanation and provider convention. Opening and closing this read-only view do not format or select another date, apply settings, save storage or request providers. Stable dialog/Close nodes survive ticks; unchanged text and attributes are not rewritten. Native modal behavior supplies background containment, Escape and focus return to the connected initiating trigger. Browser UI focus transfer is allowed; no custom circular focus trap or unmeasured assistive-technology speech behavior is promised.

Complete values keep their 14px font, normal whitespace, anywhere wrapping and selectable literal text. The dialog scrolls vertically within viewport−28px height and at most 297px width, with horizontal overflow hidden. Very long values must remain obtainable through scrolling/selection and a usable Close route. The inner card and the current builder preview/copy iframe are 325×530. The owner clarification for #25 keeps the public builder preview/copy iframe at 325×530, equal to the inner card; the optional 330×534 personal TablissNG comparison is separate. Declared supported engines require actual native modal capability/input qualification; an unsupported declared host needs an approved tested fallback or resolved support policy before compatibility closure.
- **Header belt**: a bare `1fr auto 1fr` grid (no background of its own) holding two **content-fit** glass straps
  — location (left) and temperature (right) — flanking a **~25px circular icon "buckle"** that is *centred on the
  widget* and **cuts** the belt. The three children are **explicitly column-pinned** (`.e`→1, `.buckle`→2,
  `.wt`→3) so the buckle stays centred **even when the location strap is absent** (no `label` → `#loc` is
  `display:none`; without explicit columns, grid auto-placement would collapse and shove the buckle left). The straps tuck ~7px under it (negative margin) AND each strap's inner end is
  physically **masked with a circular cut-out** matching the buckle (`mask-image` radial-gradient, header vars
  `--buckle-r/--belt-tuck/--belt-cut-center/--belt-cut-r`). This is required because the straps and buckle are both
  **translucent / backdrop-filtered glass** — z-index alone can't hide a strap behind translucent glass (the
  underlying pixels show through), so the strap pixels under the buckle are *removed*, and the buckle (`isolation`
  + `overflow:hidden`) composites over sky/glass, never over belt geometry. Straps are **thinner** than the buckle;
  subtle inner-glass only, no heavy drop shadow. The belt has a fixed height so it never moves the content stack.
- Large **moon** lives in the **top-right** (mostly **in-frame** — the disc sits in the pocket *below* the
  temperature strap and *above* the arc so its right limb shows and the lunar phase is readable; only a sliver of
  the right edge clips the card). Large clipped **sun** in the **top-left**.

## Prayer-time logic & arc semantics

- Times come from the **Aladhan API** (`fetchTimings`), cached in `localStorage`. The Islamic (Hijri) day rolls
  over at **Maghrib**, not midnight; the AH date and the moon-phase preview update accordingly.
- **Day rollover:** cached-to-fresh promotion must admit the requested civil date,
  zone and target generation. While the next day's timetable is unavailable,
  old rows cannot nominate a current next prayer: values/highlights/countdown
  withdraw to an explicit unavailable state. Calendar source disclosure remains
  independent. `qaState().cache` exposes `prayerStale` and `rolloverPendingMs`.
- **Next and current:** `.p.on` is the next event and uses a stable accent plate
  with dark text; `.p.now` independently outlines the current prayer. Future rows
  stay readable glass, elapsed rows are subdued, and Forenoon has no current row.
  Tomorrow's Fajr row, countdown and next arc marker use the same admitted target.
- **Default timetable readability:** names and times retain full informational
  opacity through their ancestors. Ordinary cells place `rgba(9,17,28,.74)` beneath
  the decorative glass tint; elapsed rows use a quieter tint and border instead
  of fading the text. NEXT keeps its opaque accent and dark foreground, and CURRENT
  keeps its separate inset. The optional contrast appearance remains optional.
  Native Chromium/Firefox pairs with a controlled 7 September 2026 Madinah clock verify
  intended foreground/background contrast of at least 4.5:1 at noon, sunrise,
  sunset, night, broken cloud, overcast and local white stress, with Inter/Fraunces
  loaded and DPR 1/2 coverage. This is bounded timetable evidence, not whole-widget
  accessibility certification; antialiasing/shadow changed-pixel ratios are only
  diagnostics. The historical noon capture had no pinned date. Fonts, row geometry,
  the 325×530 card, header/footer, and the separate embed interfaces are preserved.
- The arc (`drawArc`) is **one continuous solar-elevation curve** built from real solar motion (hour angle +
  declination), NOT from prayer-to-prayer interpolation. Prayer events are *sampled onto* it. The declination is
  fit so elevation crosses **0° exactly at this date's sunrise/sunset** (the fit may slightly exceed the real
  declination because it absorbs refraction; the clamp is 27.5° to admit the near-solstice fit).
- **Sunrise is NOT a prayer** → its marker is a **hollow ring** sitting exactly on the dashed 0° horizon line (so
  is Maghrib/sunset). The five prayers are filled dots.
- **Dhuhr is NOT solar noon.** The apex of the arc *is* solar noon (zawāl, the sun's highest point); Dhuhr begins
  just **after** the meridian crossing, so its dot is held a hair *past* the apex, never on it. On dates where its
  time already falls further past noon, its own time carries it along.
- The "eye-of-needle" ring is the live sun position; the warm dash-revealed arc draws over it.

## False dawn vs true dawn (Fajr semantics)

Islamically distinct — and represented honestly. **Neither false nor true dawn is a painted overlay** (fail-closed):

- **True dawn** (al-fajr al-ṣādiq) is the real **physical twilight sky** — the `skyLum` astronomical→nautical→civil
  brightening plus the warm horizon scatter at the sun's azimuth — together with the **Fajr marker/time** on the arc
  and the countdown. There is no separate horizontal "true-dawn band" (that would be a fake duplicate of what the
  sky engine already renders). Around Fajr (solar depression ~−15° to −18°) the sky stays genuinely **dark**,
  brightening steeply only in the last few degrees before sunrise.
- **False dawn** (al-fajr al-kādhib, the zodiacal light) is **NOT rendered.** A generic CSS cone was tried and
  removed: unmodeled, it read as a decorative lens-flare/godray slash and (wrongly) showed under a bright moon.
  Rather than ship an inaccurate cue, the widget **fails closed** — it shows nothing for false dawn.
- **Future work (only):** a faithful zodiacal-light cue would require a real ecliptic-tilt projection, strict
  dark-sky gating, low/no moonlight, low light-pollution, clear sky / minimal low cloud, very faint opacity, no
  foreground-crossing streak, and it must never imply Fajr has entered. Until all of those hold, it stays unbuilt.
- `trueDawnTwilight` exists only as a 0..1 **diagnostic scalar** (qaState); it paints nothing.
- Debug: `?debugDawn=…` is a **deprecated no-op** — there is no painted dawn layer to force.

## Atmosphere state model

There is one temporal API, `simNow()` / `simDate()` / `nowParts()`, with two authorities. With neither `simTime` nor `timeScale`, `simNow()` reads the current device `Date.now()` on every call; a timezone change reformats that instant. Explicit previews use a validated anchor plus independent elapsed time multiplied by `TIMESCALE`. An explicit `timeScale=1` remains a 1× anchored preview with ADVANCING, forecast weather, star reprojection and the SIM readout. `timeScale=60` advances 60×; `simTime=HH:MM` without a scale is frozen. Existing scale parsing preserves frozen behavior for zero, empty, invalid and clamped negative values. Independent elapsed behavior assumes a supported native `performance.now()` host; the existing `Date.now()` fallback has no separate wall-step guarantee. Injected wall corrections do not establish native sleep/wake or NTP behavior.

**Clock correction direction:** In ordinary direct-wall mode, forward and backward device wall corrections are followed by the next `Date.now()` read. An explicit `timeScale=1` is an anchored preview, not ordinary wall-clock mode. Independent elapsed behavior still has the stated native-host assumption and wall-clock fallback limitation; this source distinction does not qualify sleep/wake or NTP behavior.

Explicit local times and prayer/weather endpoints use the same minute-precision inverse. Inputs are finite integer Gregorian fields, positive years representable by Date and Intl, hours 0–23 and minutes 0–59 in an Intl-supported zone. A profile exhaustively projects each UTC minute from the strict UTC midnight coordinate U−24 hours through U+48 hours, inclusive: 4,321 projections. Gregorian/Latin/h23 projection must show whole-minute offsets whose magnitude is at most 24 hours throughout that window. A final full-field round trip accepts exactly one inverse; gaps, folds, invalid dates/zones and unsupported representations are unavailable. This does not certify historical second offsets or arbitrary IANA history. At most four exact zone/day profiles, including unsupported profiles, are retained in memory and reused; the inverse adds no persistent cache schema.

An invalid explicit scene clears its numeric anchor and withdraws clock-dependent sky, arc, prayer and calendar output, shows `Simulation time unavailable` / `SIM unavailable`, and keeps configuration recovery reachable. Valid configuration recovery restores the prior visibility. An unavailable scene does not qualify normal night appearance or live motion. Ordinary loads without clock overrides keep their direct-wall authority.
Each render tick:

1. `atmosphere(M)` derives **one pure state vector** from the physical drivers (solar elevation, lunar geometry/
   phase, gated weather) in a fixed order — colours, opacities, light directions, optics strengths. It touches no
   DOM.
2. `paint(A)` is the **only** place that writes to the DOM (typed `@property` custom props that interpolate, plus
   a few SVG nodes and the canvas cloud state).

The CP9 spectral atmosphere plus the declared native display policy owns broad
sky colour. The retained `physSky()` state still supplies native foreground
lighting; its former broad CSS background/veil layers are not painted twice.

## Sun layers & optical phenomena

- `.atmo .sunbody` owns one enlarged, partly clipped solar body. Its restored V1
  diameter is `240*(1.10-.24*clamp(elevation/40))`:264px at the horizon and206.4px
  at high Sun. Presence, position, refraction flattening and clipping are separate;
  a rising Sun does not inflate from a small button. `.suncorner` supplies the
  retained corona/rays, with its duplicate disc disabled throughout the handoff.
- The whole body shares one attenuated spectrum with a modest limb falloff:
  Kasten–Young airmass, Beer–Lambert beam response, elevation-dependent CCT and
  ACES display mapping. No unconditional white CSS centre bypasses attenuation,
  and no independently orange collar bypasses the body spectrum. Natural low-Sun
  warming/dimming remain; this enlarged display treatment is not calibrated
  angular solar radiance. The approved body size does not change with glow size.
- Body and corona/rays join the existing atmospheric light group, retaining
  foreground air instead of replacing it with a flat orange surface. One mask
  from the **same painted cloud alpha** obstructs these light contributions;
  it paints no second cloud colour. An opaque cloud can hide the body completely.
  The old category multiplier no longer attenuates direct light a second time.
- **Optics coordinate (important):** the **discrete** solar optics that ring/emanate from the sun — 22° halo,
  sundogs, sun pillar, the `.sun` bloom, `.wfx .godray` crepuscular shafts, `.sunhaze` — are registered to the
  **visible corner-sun** screen position (`--sunvx/--sunvy`, the corner-sun disc centre), so e.g. the halo arcs
  *around the sun you can see*. (Previously they bound to the arc-sun azimuth `--sunx/--suny`, which sweeps
  mid-card, so the halo rendered detached center-screen — that was a bug.) Only the **diffuse, azimuthal** cues
  stay on `--sunx`/`--antix`: the **horizon scatter** band (`.scatter`, pools under the sun's azimuth — left at
  dawn, right at dusk) and the anti-solar **Belt of Venus** (`.belt`) / **anticrepuscular** rays.
- **Optical phenomena are condition-gated, never random** (ice-crystal vs water-droplet, low-sun + broken-cloud,
  etc.). See "Known approximations". *Known stylization:* the corner-sun body stays top-left in all states (the
  moon owns top-right and the header owns the centre); at dusk the warm directional glow correctly pools on the
  right (west) via the azimuthal scatter while the sun body remains the top-left luminary.

## Moon — PBR, earthshine, halo/corona

The accepted device-resolution terrain layer follows the native SVG optical
background. The older SVG photo was opaque over those optics; placing its
replacement canvas before the SVG instead overlaid the bright corona centre
on Earthshine. Keep this order through preview/refined handoffs. Native cloud
foreground remains composed once by the shared display-linear join. A high
dew point alone is not a water-droplet column and cannot enable a corona.


- The Moon is an **OPAQUE body — you never see stars through it.** The disc (`.mphoto`) and its star-occluder
  (`.moccluder`) share **one opacity** (`--moongrp = moonShow = clamp(darkness·1.8)`): **full at night**, fading
  out only by day (no daytime ghost). It is never a translucent "hologram." (Heavy cloud hides the Moon by drawing
  the cloud deck *over* it — layer order — not by fading the disc, so partial cloud never makes it see-through.)
- **Physical vs calendar moon.** This widget is also a **lunar-calendar** instrument, so the Moon stays
  meaningfully present **every night** — even when the physical Moon is below the horizon or near-new — by rendering
  the real **opaque phase disc** (a new moon is a *dark ashen disc*, not a blank slot or a transparent one). The
  physical-vs-calendar distinction lives entirely in **moonlight** (`--moonbeam` / cloud moon-lighting), which is
  **physical-only** — 0 below the horizon / new / day, **never faked** for the calendar moon. So the calendar moon
  informs the date **without lying about light**. `qaState().moonTruth` reports phase fraction, altitude,
  physical-vs-calendar visibility, displayMode, opacities, moonlight, and the reason any layer is dim.
- `.mphoto` is a **physically-lit** disc: real LRO albedo + LOLA normals, Lommel-Seeliger + lunar-Lambert
  reflectance with an opposition surge, rendered to a **300px supersampled** backing canvas with **coverage-AA**
  on the limb (no jaggies/stroke). **Orientation: one steady UPRIGHT face** — `renderMoonPBR(frac, waxing)` lights
  the bright limb on the **right** (waxing) or **left** (waning) with the maria **fixed**, so the terminator just
  sweeps across; the disc never rotates and its lit side matches the footer phase emoji. (It previously rotated to
  the parallactic bright-limb angle `χ−q`, which made the disc visibly **spin** over time and mismatch the emoji —
  removed 2026-06-16. The trade-off is the moon is the upright N-hemisphere view, not tilted "as seen from your
  exact location" — consistent with the upright emoji, and the right call for a corner widget.)
- **Earthshine**: a smooth curve `es = 0.09 + 0.34·(1−frac)^1.7` (steeper-than-linear toward full) × albedo —
  moderate ashen glow at thin crescent (the lit crescent still dominates), faint **textured** terrain at gibbous
  (never a black cutout), a small floor at full.
- **Two distinct lunar optics**, gated by admitted cloud type/fog: a **22° ice halo** (`.mhalo`, a discrete ring with
  a dark inner gap, red-inner/blue-outer, from cirrus) vs a **droplet corona** (`.mcorona`, a small near-white
  aureole with pastel rings hugging the disc, from altostratus/fog, not humidity alone). The generic `.mglow` is subtle and
  breathes gently with simTime/haze — it is **not** the dominant element and does not flatten the whole sky.

## Cloud & weather engine

- Clouds are **clusters of overlapping soft puffs** (stacked circles drawn with canvas radial gradients) — a
  cumulus base + lit rounded top, **geometry-gradient soft-but-defined edges**, a noise-driven **lifecycle**
  (grow/erode, no popping) and **wind advection**. Coverage decides how many clusters are active (broken → a few
  puffs with gaps; overcast → many overlapping into a solid deck). Clusters live **around/above the dashed 0°
  horizon**, above the hero.
- **Perceptible live motion (calibrated).** Advection and lifecycle are tuned so the deck **visibly drifts/morphs
  in a 15–60s real-time glance** — a moderate wind carries a cluster ~25–30% of the card width per minute (≈70
  screen-px/min; gentle in calm air, fast in a gale), with a slower in-place grow/erode on top. (Earlier rates
  were ~100× too slow → the deck read as a frozen wallpaper even though the QA hash "changed" every frame — see
  "Live motion".) The fragment's `timeScale` sets the explicit scene clock rate; `timeScale=1` remains an anchored 1× preview. A query-only `?timeScale=` is ignored. reduced-motion paints one frozen frame.
- **Lighting**: warm sun rim / silver lining on the sun-facing side, cool moonlit edges at night, leaden
  undersides in storm, lit tops / shaded bases for volume; rain/fog diffuse.
- **Continuity**: the cloud field has a **stable identity** (`_cloudFieldSeed` = location + day + optional
  `?seed`) and is never reseeded on a weather refresh or render. Live coverage **eases** toward its target so a
  15-minute refetch grows/erodes the existing deck smoothly (snapping only on first establishment and under
  fast-forward) — no "slideshow".
- **Rain** originates from the actual cloud columns (`_colDens`), fading before the prayer list, and scales by
  WMO code / amount (drizzle → showers → steady → heavy → thunder).
- **Lightning** is a **procedural branching channel** (midpoint-displacement stepped leader + forks from the
  cloud base, sometimes reaching the lower third), regenerated each strike, with a persistent storm-glow so the
  storm reads between strikes — not a symbolic bolt.

### Weather truthfulness (critical)

Open-Meteo `current=` is a current MODEL ESTIMATE, not a direct local observation.
The owner's PR42 policy supersedes both the old observed/nowcast wording and the
later policy that suppressed all model precipitation when no observation adapter
was connected. One admitted decision supplies icon, temperature, condition,
effect permissions and provenance. A usable condition survives a missing
temperature or amount; no old temperature survives a rejected record.

Optional measurements retain the distinction between unavailable and zero through
admission, cache and display. A missing, null or invalid temperature leaves the
temperature text empty; genuine numerical zero displays `0°`. Finite negative
temperatures remain valid in the requested Celsius or Fahrenheit units. Missing
or invalid precipitation stays unavailable and cannot authorize wet effects;
numerical `0` is a valid dry amount, not missing data. A valid condition can still
appear with its model/uncertainty disclosure when an optional measurement is
unavailable. These rules use the existing provider, configuration and cache
schema; they do not retroactively distinguish a legacy coerced zero from a
genuine recorded zero.

Temporal authority keeps `currentTime` (provider `current.time`), `currentZone`
(the captured request timezone), `currentValidAt`, `currentIntervalSec` and
`retrievedAt` separate. Calendar-invalid or ambiguous/unresolvable wall times and
nonpositive/nonfinite intervals are unavailable. The interval describes the
preceding aggregation period; it is not an extra freshness allowance. Provider
`generationtime_ms` is processing duration, not a source epoch. Current source
and receipt ages must each satisfy **0 through 900000 ms inclusive** (15 minutes),
evaluated again at each real-time use. There is no future-skew allowance: +1 ms
is ineligible. A skewed client clock can therefore withhold otherwise useful data.

RainViewer `past[].time` becomes `frameGeneratedAt`, `generated` becomes
`indexGeneratedAt`, and completed acquisition has its own `retrievedAt`.
Both seconds inputs must be raw finite nonnegative numbers whose derived
milliseconds are valid Date epochs before Image dispatch or metadata installation.
Index generation never substitutes for a missing frame timestamp. Frame and
receipt ages each satisfy **0 through 1200000 ms inclusive** (20 minutes);
downloading the same stale frame again cannot renew its source age. Index time
is retained separately, not used as the frame freshness clock. Mosaic generation
does not date every contributing radar measurement or certify selected-site
coverage, rain amount or direct observation.

Six-hour weather-cache retention is distinct from live authority. Compatible
legacy cache bytes may remain without usable source metadata; acquisition can
replace them, while failed refreshes cannot renew them. Expired or invalid current
authority yields an em dash, blank temperature, and no unsupported cloud,
precipitation or lightning effects. The neutral sky remains decorative; hourly
data cannot substitute for live current. Prayer-cache stale state remains separate,
and cache retention is not an offline-app guarantee.

- Fresh, correct-target `current` WMO categories supply condition emojis and
  `data-fx`. Titles/accessible labels/QA disclose provider, model status and the
  absence of direct local observation. Unknown weather is an em dash with no
  temperature, not a sunny substitute or epistemic glyph in the condition slot.
- Supported current-model quantities can enable bounded model-estimated rain
  or snow in ordinary real time. Missing, invalid or contradictory amounts leave
  the condition visible with explicit uncertainty but do not invent particles.
  `visualPermissions` are distinct from observed-present `permissions`.
- Thunder codes do not authorize observed strikes. Lightning retains its
  independent evidence and reduced-motion/flash gates; the live adapter remains
  unqualified. `observedPresent` is false for the current model lane.
- Hourly forecasts remain forecast/preview data, never a live-current replacement.
  Existing source-age, receipt-age, unit, target and generation fences remain.
- RainViewer palette alpha is unitless imagery, never millimetres or local
  observation authority. A newly fetched mosaic cannot renew old source evidence.

`weatherInformation(decision, day)` formats one admitted decision into cached
`summary`, `currentText`, `spatialText`, `horizonText` and `forecastText` strings.
The existing weather icon name/title append the summary. The clipped, accessible
`#weather-information` description contains that same snapshot; `#wi` references
it through `aria-describedby`. Local settings adds this reference without replacing
existing description tokens, action name, persistence warning, role or focus behaviour.
No live region, new control, provider request or weather permission is introduced.

Current model estimates, qualified SIM present wet/dry/conflict, and unknown
conditions remain distinct. Rejected synthetic quality retains any eligible model
classification and quantity, with the rejection disclosed and present effects
withheld. Qualified SIM nearby precipitation is a range, not an arrival time.
Only a qualified synthetic trajectory supplies an approach interval. Current wet
and future approach may coexist; distance, wind, WMO code, hourly forecast and
radar alpha never imply an ETA. Live local observation, nearby and arrival adapters
remain unavailable.

Source validity, approach and forecast intervals use absolute target-zone times.
Current model precipitation describes the preceding declared interval; mm/h is
labelled an interval average, never an instantaneous measurement. Null and zero
remain distinct. Forecast text retains provider/product, amount kind/units and
valid interval. Probability requires the exact precipitation event/window; actual
production hourly metadata supplies neither probability nor qualified event data.
The separate `r0024-forecast-fixture/v1` decorator exercises this contract only in
an owned preview and refuses live, wrong-owner/target, expired or malformed input.
It is not a live prediction service or an accuracy claim.

For diagnostics, enable `qa=1` and compare `qaState().wxTruth` with
`qaState().weatherHeader.information` and `#weather-information.textContent`.
The native fixture runner in `tools/qa/run_r0024_native.py` records the actual
decision, accessible presentation, particles and pixels; QA fields alone cannot
prove browser presentation or visible motion.

`qaState().wxTruth.requests.weather` and `.radar` retain the last small attempt
diagnostic: `generation`, `operationId`, `attemptId`, `state` and `reason`.
The active stages are `fetch`, `body` and, for radar, `image`; an `unavailable`
result with `fetch timeout`, `body timeout` or `image timeout` identifies the
bounded stage. `received` describes wrapper completion, not freshness or provider
health. Slot release, retry eligibility and a healthy replacement consumer are
separate facts; the README's Weather retry description gives their timing limits.
The diagnostic is the latest attempt record, not a history or a provider health
check. Compare `generation`, `operationId` and `attemptId` when following a
replacement: a released old attempt must not clear the active successor or
replace its diagnostic. HTTP 200 headers can still lead to `body timeout`;
`received` alone does not establish that weather passed admission, that an Image
sample is usable, or that the rendered consumer recovered. Check the accepted
record's eligibility and the actual temperature/presentation, or the radar
frame/sample and `radarAvailable`, separately. Radar recovery still provides
unitless imagery and cannot authorise rain amounts or lightning.
For freshness inspection, `qaState().cache.weatherSourceAgeSec` and
`weatherAgeSec` report source and receipt ages, with `currentEligible`,
`weatherStale` and `currentUnavailableReason`. `wxTruth.model.sourceValidAt`,
`retrievedAt` and `quantity.from`/`to` describe the selected model and preceding
interval when available. `wxTruth.radarFrameAgeSec` and `radarAgeSec` are frame
and receipt ages; `radarAvailable` concerns unitless imagery, not rain authority.
The raw record retains its index epoch separately; the QA age summary does not
expose an index-age field. Displayed ages are rounded seconds; exact eligibility
uses milliseconds, so the rounded age alone cannot decide a boundary.

## Star / night-sky system

- A synthetic **catalog** projected to the local dome by sidereal time + latitude. In real-time the **positions
  are fixed** (no record-player spin); life comes from per-star CSS **scintillation**, haze, and moonlight. Under
  `timeScale` the sky re-projects coherently.
- **Families**: a faint dust bed, medium field stars, and rare **bright anchors** with coloured halos + 4-ray
  glints; colour temperature varies (blue/white/amber/red). A bright moon **washes its neighbourhood** (local
  star suppression) without flattening the whole sky. Humidity/haze/cloud reduce/soften stars; dry/high sites
  sharpen them. The Milky Way / airglow appear only when plausible.
- **Twinkle (the visible life):** per-star CSS scintillation (`@keyframes tw`, independent phase/rate, amplitude
  from live air turbulence `--star-turb`). **All bright anchors twinkle** (the eye tracks them) ~1.5× deeper than
  the dust bed, and their **4-ray glints scintillate** too (`@keyframes glintpulse` around each glint's projected
  base opacity `--go`) — so the luminaries shimmer instead of sitting static. CSS scintillation is disabled under
  OS `prefers-reduced-motion` unless `&motion=full` overrides it.

## Live motion & accessibility

The default widget must **visibly animate in normal real-time** wherever the scene has animatable phenomena — a
static-looking sky is a regression, not a "polish" gap.

- **Pipeline.** One rAF loop. `render()` runs each sim-second (state/sky/marker/moon). The **cloud canvas repaints
  ~13 fps** (`paintClouds(simNow()/1000)`); **star twinkle + glint scintillation, rain, fog, lightning** are CSS
  animations, independent of `render()`. The loop **pauses** (and CSS via `.c.paused`) when the iframe is hidden or
  scrolled offscreen (visibilitychange + IntersectionObserver) — battery for a 24/7 embed.
- **Accessibility.** Under OS `prefers-reduced-motion: reduce` the CSS reduced-motion block stops all atmospheric/
  weather animation and the cloud loop paints **one frozen frame** (no animation). `&motion=full` is an honest
  **override** (adds `.c.motionfull`, clears the JS `_RM`/`_REDUCED` flags) so motion runs even under the OS
  preference — for testing or for users who want it. The default still respects the preference.
- **`&debugMotion=1`** overlays live telemetry: rAF ticks/s, cloud-paint/s, reduced-motion, `motion=full`, paused,
  `timeScale`/advancing, **cloud Δ over 10s/60s**, **star Δ** + whether the twinkle animation is active, the
  weather source, and the reason motion is reduced (if any).
- **The qaState-hash trap (read this).** `qaState().clouds.hash` is position-weighted and flips on sub-pixel change,
  so it "changes every frame" even when nothing visibly moves — it produced false PASS reports. **Never claim live
  motion from the hash.** Verify with a real ≥15–60s watch (the `debugMotion` 10s/60s Δ, a centroid-drift probe, or
  a clip): clouds drifting/morphing, stars scintillating, the sky breathing.

## API & data sources

- **Aladhan** `timings` — prayer times (cached per day in localStorage).
- **Open-Meteo** `forecast` — `current=` (model-estimated temp/humidity/wind/cloud layers/visibility/`weather_code`/
  **precipitation**/rain/showers/snowfall/is_day) and `hourly=` 3-day track; plus grid-cell `elevation`.
- Both are keyless and CORS-safe.

## URL / hash & debug parameters

Configuration and diagnostics are read from the fragment after #. Append &debugMotion=1 or &motion=full to that same fragment. A query-only ?debugMotion=1 is not read. The six debugOptic force names are halo, sundogs, pillar, anticrep, paraselene and lunarhalo. Corona, earthshine, refraction and the crepuscular ray require controlled physical scene inputs; no dedicated debugOptic switch forces them.

Real-time motion diagnostic:

```text
index.html#lat=24.47&lon=39.61&label=Madinah&method=4&debugMotion=1
```

Full-motion override (the normal default respects reduced motion):

```text
index.html#lat=24.47&lon=39.61&label=Madinah&method=4&debugMotion=1&motion=full
```

Solar noon halo diagnostic:

```text
index.html#lat=24.47&lon=39.61&label=Madinah&method=4&simTime=12:30&debugOptic=halo
```

Query-only negative control: these flags are not read from before #.

```text
index.html?debugMotion=1&motion=full#lat=24.47&lon=39.61
```

simTime without timeScale freezes the clock-driven scene. Use the real-time recipe above for a 15–60 second motion check. Flag activation alone does not prove visible motion or correct optical pixels.

Lunar force checks require an eligible night Moon. Near-new, below-horizon, daylight and unavailable-surface cases cannot gain moonlight from a diagnostic flag. Retain the physical scene inputs and crops for optics, and the real 15–60 second watch/clip/delta for motion; never use `qaState().clouds.hash` as motion proof.

Common hash options:

- `lat`, `lon`, `label`, `method`, `units` — location + calc method + °C/°F.
- `seed` — varies the synthetic star draw + cloud field identity.
- `timeScale=<n>` — an explicit positive scale enables an anchored preview, including `timeScale=1` (1×) and `timeScale=60` (60×), with ADVANCING, forecast weather, reprojected stars and the SIM readout. With neither clock override, ordinary mode follows the current device wall clock.
- `simTime=HH:MM` — a validated local-time anchor, frozen when `timeScale` is absent; a positive explicit scale advances that anchor independently of device wall corrections. Unresolvable gap/fold times show an unavailable scene.
- `simWx=<wmo code>` — force a weather class; `simPrecip=<mm>` — force synthetic preview precip (to QA the precip gate,
  e.g. `simWx=95&simPrecip=0` ⇒ dry forecast-thunder ⇒ downgraded). `simTemp`, `simFeels`, `simWind`,
  `simWindDir`, `simHumid`, `simCloud`, `simMoon`, `simWax`, `simMoonAlt`, `simMoonH`.
- `qa=1` + `window.qaState()` — a structured snapshot (incl. `wxTruth`).
- `debugLayers=1`, `debugMoon=1`, `debugMotion=1` — on-card readouts (layers / moon / live-motion telemetry).
  `debugDawn=…` — **deprecated no-op** (dawn is not a painted overlay; nothing to force).
  `motion=full` — force full animation even under OS `prefers-reduced-motion` (accessibility override; default respects it).
- `debugOptic=halo|sundogs|pillar|anticrep|paraselene|lunarhalo` — force a (normally condition-gated) optical phenomenon.
- `local=1` — self-configuring mode (coarse auto-detect + in-widget settings, saved locally).
  `preferLocal=1` — hardcoded defaults that a saved local config may override (opt-in). `lp=0..1` — light-pollution dial.

## Config resolution & local mode (`config.js`)

Config logic lives in **`config.js`** (`window.SalahConfig`), a same-origin classic script loaded **before** the
inline page script by **both** `index.html` and `builder.html` — one un-forkable source for parse/validate/
normalize/serialize/load-save-clear-local/coarse-detect. (This deliberately relaxes the old "single self-contained
`index.html`" rule; `index.html` keeps a one-line **legacy fallback** to hash-only parsing if `config.js` 404s.)

- **`WidgetConfig`**: `{v, lat, lon, tz, label, method, school, time, datefmt, units, appearance, lp, seed, source, origin, savedAt, locationEvidence}`.
  `source ∈ {hash, localStorage, coarse-ip, browser-geolocation, place, manual, fallback}`; `origin`, when present,
  preserves the acquisition origin independently of the storage marker. Persisted under `salah_widget:config:v1`
  (separate from prayer/weather caches; every access wrapped in try/catch).
- **Location evidence:** `{intent, source, accuracyM, acquiredAt, provider, area, bounds}`.
  `intent ∈ {fixed-site, device-position, coarse-area, unknown}` and evidence
  `source ∈ {hash, manual, place, browser-geolocation, coarse-ip, legacy, unknown}`. Coordinates select the
  target; this record does not certify the viewer's current presence. Browser `accuracyM` is finite numeric
  metres ≥ 0 or `null` (a reported 0 stays 0); decimal places do not establish accuracy. `acquiredAt` is a finite
  numeric epoch > 0 and ≤ actual `Date.now()`, or `null`. The future-timestamp skew allowance is zero;
  missing/nonpositive/future/malformed time stays unknown, never an age-0 clamp. `provider`/`area` retain
  available text bounded to 80/240 characters. `bounds` is `{south,north,west,east}` with finite ordered
  latitudes in [-90,90] and longitudes in [-180,180], or `null`; no radius is invented.
- **Fix and persistence lifecycle:** `savedAt` is successful settings-write time, separate from `acquiredAt`.
  Saving label/units/method cannot renew a fix. Label/reverse naming retains compatible evidence; coordinate
  edits choose a manual fixed site and clear incompatible acquisition claims. Legacy records retain usable
  coordinates/preferences without substituting `savedAt`; reads do not destructively rewrite them. Saving
  browser-derived targets retains private evidence but downgrades the top-level source for old readers to a
  configured site. Portable hashes describe a fixed configured destination and omit private acquisition history.
  Denied persistence preserves useful in-memory metadata and prior saved bytes with the session-only warning;
  a writable partition may persist within its own permissions and lifetime. No new freshness/radius threshold
  or continuous location tracking follows from this schema.
- **Precedence:** explicit hardcoded hash (unless `local`/`preferLocal`) → saved local → coarse IP/timezone detect
  → manual setup → safe error. **Stale localStorage never overrides an intentional hardcoded embed.**
- **Sync vs async:** hardcoded resolves **synchronously at module load** (byte-identical boot timing — proven by
  Smoke A/B equality of `qaState` stable fields). Only `local`/`preferLocal` **without** a saved config defer to
  the async `coarseDetect()` in `boot()`; failure opens the manual settings panel (never crashes).
- **Coarse detect:** GeoJS (`get.geojs.io/v1/ip/geo.json`) → ipinfo.io fallback, AbortController timeout, IANA tz
  from the device (`Intl`) first. Approximate (IP-based) — surfaced as "estimated area," never "precise."
- **Runtime apply** (`applyConfig`): the settings panel updates the live config **in-memory, no reload** (so it
  works when third-party-iframe storage is blocked). `cacheKey`/`wxKey` are **functions** (not consts) so the new
  location's caches are keyed correctly; the post-config pipeline (`startWeather`/`loadPrayerData`/`startRenderLoop`)
  is shared by `boot()` and apply.
- **Settings affordance:** the header buckle becomes a `role=button` (weather emoji ⇄ ⚙ gear on hover/focus; tap +
  `Enter`/`Space` work; not hover-dependent) **only in local/preferLocal mode** — hardcoded embeds are untouched.
  The panel overlays the prayer display inside the same 325×530 card (internal scroll; never resizes the iframe or
  clips header/footer). Precise geolocation is **only** called from the panel button (user gesture).
- **`qaState().config`** exposes `configSource/configMode/autoDetectSource/autoDetectStatus/storageAvailable/
  storageError/geolocationPermissionState/geolocationLastError/lat/lon/tz/label/hashConfigOverridden/why`.
- **Embed size = card size:** the iframe wrapper is **325×530** — exactly the widget card (`.c`) — in the builder
  preview, the copied snippet, README, and the TablissNG preset. A larger wrapper only adds invisible transparent
  margin, so the builder card/preview are matched to the *visible* widget (530px), not to an oversized box.
- **Install wizard config-carry:** the builder's **Install widget** button copies the OS one-liner; when the config
  is non-default it prepends `SALAH_WIDGET_HASH='<hash>'`, which `install.sh`/`install.ps1` bake into the staged
  preset's iframe (replacing `#local=1`) so the installed widget starts already configured (no re-setup). Bash note:
  `install.sh` uses `shopt -u patsub_replacement` so the hash's `&` separators stay literal in the `${//}` replace
  (bash 5.2+ otherwise treats `&` as the matched text); PowerShell's `.Replace` is already literal.

## Known approximations (honest)

- Weather `current` is a source-dated **model estimate**, not a direct local observation.
  Its preceding-interval amount is not instantaneous rainfall. Source/receipt
  expiry, client clock skew and radar coverage limit availability; radar imagery
  remains unitless and supplies no ground-truth precipitation amount.
- The arc's declination fit absorbs refraction to make sunrise/sunset land on the line (a visual calibration).
- Dhuhr's "hair past the apex" is a small deliberate offset (post-zawāl cue), since minute-resolution data can put
  Dhuhr exactly on solar noon.
- Cloud edges are soft/painterly rather than crisp cumulus. (Overcast was deepened to a **leaden ceiling**
  2026-06-16 — a neutral-grey, stronger `WX.overcast` sky tint + a darker overcast `cloudBase` + a high-coverage
  puff-opacity fill, all overcast/coverage-gated so broken & clear are unchanged and motion is preserved.) The
  cloud renderer is a **stylized 2D puff-cluster + time-noise** field, **not** volumetric; the motion rates are
  **perceptual** (read as alive at widget scale), not measured advection.
- **Solar tone-mapping** uses a real discipline (airmass + transmittance + CCT + ACES) but the **headroom and
  constants are tuned for a pleasing clipped nucleus, not radiometrically calibrated**; CSS can't composite in
  linear light, so the tone-map is baked per gradient-stop in JS.
- **False dawn is not rendered** (fail-closed); **true dawn is the physical twilight sky** + the Fajr marker, not a
  painted layer. A faithful zodiacal-light cue is documented **future work** (needs real ecliptic projection +
  strict dark/no-moon/low-LP/clear gating + very faint + no foreground streak + never implies Fajr).
- The **calendar moon** shows the opaque phase disc at night even when the physical Moon is below the horizon /
  near-new (a deliberate **lunar-calendar** choice, not a literal sky photo) — but it casts **no moonlight** (that
  stays physical-only). Earthshine brightness vs phase is art-directed (never a black cutout).
- Optical phenomena: all **implemented and condition-gated** (shown only under their physical conditions, never
  random) — corner sun + entry path + low-sun **refraction flattening**; crepuscular `.godray` + **anticrepuscular**
  rays; Belt of Venus; solar **22° halo**, **sundogs/parhelia + parhelic circle**, **sun pillar** (all ice-crystal/
  cirrus/cold gated, **registered to the visible corner sun** via `--sunvx/--sunvy`); lunar **22° halo + corona +
  paraselenae** and earthshine. Dedicated diagnostic forcing is limited to halo, sundogs, pillar, anticrep, paraselene and lunarhalo; physical-only effects retain their scene inputs. They are **art-directed approximations
  (believable, not photometric)**; the moon's halo/pillar may show as partial arcs because the halo radius exceeds
  the (mostly in-frame) disc. The **corner-sun body stays top-left** in all states (a layout stylization — the moon
  owns top-right); the azimuthal horizon glow correctly moves left→right dawn→dusk.

## QA matrix (scenes to check before claiming done)

Day: clear noon (**defined sun nucleus**, not a vague brush), sunrise (enters low from the left, warm), sunset
(warm sky, not generic daylight), broken-cloud golden hour, overcast (**warm-white sun through cloud, never a
grey/purple blob**), daytime rain, thunderstorm. Night: clear (stars + scintillation), thin crescent (right limb
in frame, earthshine), gibbous (earthshine), full moon (bright opaque disc, local star wash), **new moon (a faint
ashen OPAQUE calendar disc — never an empty slot, never moonlight), thin-cloud night (halo/corona).
**Moon must be OPAQUE — no stars visible through the disc, in any phase.** Weather truth: `simWx=95&simPrecip=0`
(must downgrade), `simWx=95&simPrecip=5` (thunder), `simWx=65&simPrecip=0` (downgrade), real-time live (source =
current, not forecast). **Live motion (`&debugMotion=1`): a real 15–60s watch — clouds drift/morph, stars
scintillate, sky breathes; cloud Δ 10s ≫ 0. "No visible motion in normal live view" is a FAIL (do NOT trust the
qaState hash).** Optics: use the six supported forces with suitable solar/lunar scene inputs; solar effects register to the **visible** sun, and lunar effects retain physical eligibility. Accessibility:
`prefers-reduced-motion` freezes motion by default; `&motion=full` overrides. Layout: footer visible + header
buckle cut-out (no strap through the buckle) + readability in every scene. Dawn: near-Fajr brightening comes only
from the real twilight sky (no painted band/cone), Fajr clear on the arc.
