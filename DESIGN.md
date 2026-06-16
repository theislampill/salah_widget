# salah_widget — DESIGN

A single self-contained `index.html` Islamic prayer-times widget, deployed via GitHub Pages and embedded as an
iframe (e.g. in TablissNG). No build step, no dependencies. All logic, styles, and the atmospheric renderer live
in one file. `builder.html` is a small config/URL generator.

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
- **Header belt**: a bare `1fr auto 1fr` grid (no background of its own) holding two **content-fit** glass straps
  — location (left) and temperature (right) — flanking a **~25px circular icon "buckle"** that is *centred on the
  widget* and **cuts** the belt (the straps tuck ~7px under it via negative margin; the buckle's z-index covers
  them, so no strap shows behind it). Straps are **thinner** than the buckle. Subtle inner-glass only — no heavy
  drop shadow. Outer strap padding is a touch wider than the buckle-to-text gap so the spacing reads even around
  the round buckle. The belt has a fixed height so it never moves the content stack / footer.
- Large **moon** lives clipped in the **top-right** corner; large clipped **sun** in the **top-left**.

## Prayer-time logic & arc semantics

- Times come from the **Aladhan API** (`fetchTimings`), cached in `localStorage`. The Islamic (Hijri) day rolls
  over at **Maghrib**, not midnight; the AH date and the moon-phase preview update accordingly.
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

Islamically distinct, and rendered distinctly (not one generic bright dawn):

- **False dawn** (al-fajr al-kādhib, the zodiacal "wolf's tail"): a faint **vertical, column-like** glow on the
  eastern horizon that appears before true dawn and then fades. It **does not** begin Fajr and must not trigger
  any Fajr/sunrise styling.
- **True dawn** (al-fajr al-ṣādiq): a **horizontal** whiteness spreading **along** the horizon; this begins Fajr.
- Around Fajr (solar depression roughly −15° to −18°), the sky stays **dark** with only a faint true-dawn horizon
  thread — never a bright sunrise palette. The arc and countdown always follow the API timings; the dawn visuals
  are explanatory atmospheric layers, not the prayer clock.
- Debug: `?debugDawn=false` / `?debugDawn=true` force the two states for inspection (see params).

## Atmosphere state model

There is **one** temporal source: `simTime = simBase + realElapsed*TIMESCALE` (`simNow()`/`simDate()`/`nowParts()`).
Each render tick:

1. `atmosphere(M)` derives **one pure state vector** from the physical drivers (solar elevation, lunar geometry/
   phase, gated weather) in a fixed order — colours, opacities, light directions, optics strengths. It touches no
   DOM.
2. `paint(A)` is the **only** place that writes to the DOM (typed `@property` custom props that interpolate, plus
   a few SVG nodes and the canvas cloud state).

`physSky(elevation)` + `skyLum()` is the sole sky-colour source (no name→palette lookup).

## Sun layers & optical phenomena

- `.atmo .suncorner` is the large **clipped corner sun**: a defined nucleus + a broad corona + faint radiating
  rays, screen-blended. It **rises from the left edge** near the horizon at sunrise and climbs up-and-left to the
  top corner at noon (driven by solar elevation), tightening/whitening high and broadening/warming low. Clouds
  attenuate and recolour it; it sits *behind* the cloud layer (clouds can occlude it).
- `.atmo .sun` / `.scatter` / `.belt` (Belt of Venus) / `.wfx .godray` (crepuscular shafts) / `.sunhaze` are the
  supporting atmospheric glows tied to the real arc-sun screen position.
- **Optical phenomena are condition-gated, never random** (ice-crystal vs water-droplet, low-sun + broken-cloud,
  etc.). See "Known approximations" for which are implemented vs scoped.

## Moon — PBR, earthshine, halo/corona

- `.mphoto` is a **physically-lit** disc: real LRO albedo + LOLA normals, Lommel-Seeliger + lunar-Lambert
  reflectance with an opposition surge, rendered to a **300px supersampled** backing canvas with **coverage-AA**
  on the limb (no jaggies/stroke), oriented to the true bright-limb angle for the phase.
- **Earthshine**: a smooth curve `es = 0.09 + 0.34·(1−frac)^1.7` (steeper-than-linear toward full) × albedo —
  moderate ashen glow at thin crescent (the lit crescent still dominates), faint **textured** terrain at gibbous
  (never a black cutout), a small floor at full.
- **Two distinct lunar optics**, gated by cloud type/humidity: a **22° ice halo** (`.mhalo`, a discrete ring with
  a dark inner gap, red-inner/blue-outer, from cirrus) vs a **droplet corona** (`.mcorona`, a small near-white
  aureole with pastel rings hugging the disc, from altostratus/fog/humidity). The generic `.mglow` is subtle and
  breathes gently with simTime/haze — it is **not** the dominant element and does not flatten the whole sky.
- `.moccluder` hides stars behind the disc by day; `.mbeam` is the moonlight cast at night.

## Cloud & weather engine

- Clouds are **clusters of overlapping soft puffs** (stacked circles drawn with canvas radial gradients) — a
  cumulus base + lit rounded top, **geometry-gradient soft-but-defined edges**, a noise-driven **lifecycle**
  (grow/erode, no popping) and **wind advection**. Coverage decides how many clusters are active (broken → a few
  puffs with gaps; overcast → many overlapping into a solid deck). Clusters live **around/above the dashed 0°
  horizon**, above the hero.
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

Open-Meteo is fetched once for both `current=` (**observed/nowcast**) and `hourly=` (**forecast track**). Rules:

- In normal **real-time**, the header label/icon, `data-fx`, and precip visuals use the **current/nowcast**
  observed block only. `syncWeather()` only derives `weather` from the forecast track when **ADVANCING** (a
  `?timeScale=` fast-forward/sim preview). A forecast rain/thunder code must **never** be presented as "currently
  raining/storming."
- **Conservative precip gate** (`gateWeatherCode`): a precip/thunder code is honoured only with **active observed
  precipitation** (`current.precipitation ≥ 0.05 mm`; thunder additionally needs ≥ 0.8 mm). Otherwise it is
  **downgraded** to the cloud state implied by the observed cloud cover (overcast/partly/clear). No precip
  evidence ⇒ no rain/lightning/`data-fx="thunder"` (fail-safe).
- **Honest limitation**: Open-Meteo's "current" is a model nowcast, **not** a true radar feed. The gate makes the
  widget conservative (won't over-claim), but it is not radar-accurate. `qaState().wxTruth` exposes the full chain
  (source, raw code, observed precip, activePrecip/activeThunder, display condition, downgrade reason).

## Star / night-sky system

- A synthetic **catalog** projected to the local dome by sidereal time + latitude. In real-time the **positions
  are fixed** (no record-player spin); life comes from per-star CSS **scintillation**, haze, and moonlight. Under
  `timeScale` the sky re-projects coherently.
- **Families**: a faint dust bed, medium field stars, and rare **bright anchors** with coloured halos + 4-ray
  glints; colour temperature varies (blue/white/amber/red). A bright moon **washes its neighbourhood** (local
  star suppression) without flattening the whole sky. Humidity/haze/cloud reduce/soften stars; dry/high sites
  sharpen them. The Milky Way / airglow appear only when plausible.

## API & data sources

- **Aladhan** `timings` — prayer times (cached per day in localStorage).
- **Open-Meteo** `forecast` — `current=` (observed temp/humidity/wind/cloud layers/visibility/`weather_code`/
  **precipitation**/rain/showers/snowfall/is_day) and `hourly=` 3-day track; plus grid-cell `elevation`.
- Both are keyless and CORS-safe.

## URL / hash & debug parameters

Config and debug are read from the URL **hash** (`#…`). Common:

- `lat`, `lon`, `label`, `method`, `units` — location + calc method + °C/°F.
- `seed` — varies the synthetic star draw + cloud field identity.
- `timeScale=<n>` — fast-forward (n× real time); enables ADVANCING (forecast-driven weather, re-projected stars,
  the sim clock).
- `simTime=HH:MM` — freeze the clock at a time (TIMESCALE 0).
- `simWx=<wmo code>` — force a weather class; `simPrecip=<mm>` — force observed precip (to QA the precip gate,
  e.g. `simWx=95&simPrecip=0` ⇒ dry forecast-thunder ⇒ downgraded). `simTemp`, `simFeels`, `simWind`,
  `simWindDir`, `simHumid`, `simCloud`, `simMoon`, `simWax`, `simMoonAlt`, `simMoonH`.
- `qa=1` + `window.qaState()` — a structured snapshot (incl. `wxTruth`).
- `debugLayers=1`, `debugMoon=1` — on-card readouts. `debugDawn=false|true` — force false/true dawn.
- `debugOptic=halo|sundogs|pillar|anticrep|paraselene` — force a (normally condition-gated) optical phenomenon.

## Known approximations (honest)

- Weather "current" is a model **nowcast, not radar** — the precip gate is conservative, not ground-truth.
- The arc's declination fit absorbs refraction to make sunrise/sunset land on the line (a visual calibration).
- Dhuhr's "hair past the apex" is a small deliberate offset (post-zawāl cue), since minute-resolution data can put
  Dhuhr exactly on solar noon.
- Cloud edges are soft/painterly rather than crisp cumulus; overcast reads hazy rather than heavy-leaden.
- Lunar halo shows as a partial arc (the moon is corner-clipped). Earthshine brightness vs phase is art-directed.
- Optical phenomena: all **implemented and condition-gated** (shown only under their physical conditions, never
  random) — corner sun + rising path + low-sun **refraction flattening**; crepuscular `.godray` + **anticrepuscular**
  rays; Belt of Venus; solar **22° halo**, **sundogs/parhelia + parhelic circle**, **sun pillar** (all ice-crystal/
  cirrus/cold gated); lunar **22° halo + corona + paraselenae** and earthshine. Each can be forced for inspection
  via `?debugOptic=`. They are art-directed approximations (believable, not photometric); the moon's halo/pillar
  show as partial arcs/columns because the moon/sun are corner-clipped.

## QA matrix (scenes to check before claiming done)

Day: clear noon (sun apex), sunrise (rising-left), sunset, broken-cloud golden hour, overcast, daytime rain,
thunderstorm. Night: clear (stars), thin crescent (earthshine), gibbous (earthshine), full moon (star wash),
thin-cloud night (halo/corona). Weather truth: `simWx=95&simPrecip=0` (must downgrade), `simWx=95&simPrecip=5`
(thunder), `simWx=65&simPrecip=0` (downgrade), real-time live (source = current, not forecast). Continuity:
30–60s real-time watch (clouds drift, never slideshow). Layout: footer visible + header geometry in every scene.
