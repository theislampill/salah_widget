# salah_widget — DESIGN

A single self-contained `index.html` Islamic prayer-times widget, deployed via GitHub Pages and embedded as an
iframe (e.g. in TablissNG). No build step, no dependencies. All logic, styles, and the atmospheric renderer live
in one file. `builder.html` is a small config/URL generator.

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
- **Day-rollover stale cue:** if the calendar day rolls over but the new day's timings can't be loaded (offline /
  fetch failure with no new-day cache), the widget keeps the prior day's times, does NOT advance the date, and sets
  `_prayerStale` → a quiet worded **"stale"** chip (warm amber, not alarming) appears by the Hijri date + a faint
  date-row desaturation. Set from `render()` via `.c[data-stale="prayer"]` (never read by `atmosphere()`); scope is
  **prayer-time staleness only** (weather staleness stays in `qaState`). `qaState().cache` exposes `prayerStale` +
  `rolloverPendingMs`.
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

There is **one** temporal source: `simTime = simBase + realElapsed*TIMESCALE` (`simNow()`/`simDate()`/`nowParts()`).
Each render tick:

1. `atmosphere(M)` derives **one pure state vector** from the physical drivers (solar elevation, lunar geometry/
   phase, gated weather) in a fixed order — colours, opacities, light directions, optics strengths. It touches no
   DOM.
2. `paint(A)` is the **only** place that writes to the DOM (typed `@property` custom props that interpolate, plus
   a few SVG nodes and the canvas cloud state).

`physSky(elevation)` + `skyLum()` is the sole sky-colour source (no name→palette lookup).

## Sun layers & optical phenomena

- `.atmo .suncorner` is the large **clipped corner sun**: a **defined white nucleus** (a generous bright core) + a
  warm-gold body edge + a broad corona + faint rays, screen-blended. It **enters from off the left edge** near the
  dashed horizon at sunrise and climbs up-and-left, cresting high into the top-left corner at noon (driven by solar
  elevation). It sits *behind* the cloud layer (clouds can occlude it).
- **Solar tone-mapping / white-balance** (the disc colour discipline): the sun colour is **scene-referred, then
  tone-mapped** — never display-gamma colours multiplied by a weather "mute" (which produced a dim grey/purple
  blob). Pipeline: Kasten–Young **airmass** → Beer–Lambert **beam transmittance** × per-class **cloud
  transmittance** → a **CCT(elevation)** blackbody colour (≈2000 K horizon → ≈5500 K noon) → **ACES** (Narkowicz)
  tone-map. The nucleus carries enough radiance to **clip to a defined white body even through cloud**; the corona/
  body carries the colour and the dimming; cloud **desaturates toward warm-white, never cold grey/purple**. A small
  transmittance floor keeps the horizon sun a glowing warm disc (not a dark smudge); `--sunflat` ovalises it near
  the horizon (refraction).
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
- **Two distinct lunar optics**, gated by cloud type/humidity: a **22° ice halo** (`.mhalo`, a discrete ring with
  a dark inner gap, red-inner/blue-outer, from cirrus) vs a **droplet corona** (`.mcorona`, a small near-white
  aureole with pastel rings hugging the disc, from altostratus/fog/humidity). The generic `.mglow` is subtle and
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
  "Live motion".) Time is `simNow` seconds, so `?timeScale=` accelerates it; reduced-motion paints one frozen frame.
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
- **Conservative precip gate** (`gateWeatherCode(raw,w,radarMm)`): a precip/thunder code is honoured only with
  **active observed precipitation** (`≥ 0.05 mm`; thunder additionally needs `≥ 0.8 mm`). The observed evidence is
  `max(Open-Meteo nowcast, RainViewer radar)`. Otherwise the code is **downgraded** to the cloud state implied by
  the observed cloud cover. No evidence ⇒ no rain/lightning/`data-fx="thunder"` (fail-safe).
- **True radar (`fetchRadar`, RainViewer):** an INDEPENDENT observed-precip sensor — it samples the radar tile's
  pixel-neighbourhood at the site (CORS-readable tiles) into a coarse mm proxy. **Confirm-only** (it can keep a
  precip code the model nowcast missed, but the gate only ever gates DOWN, so radar never fabricates rain) and
  **fail-closed** (error / coverage gap / stale > 20 min / sim ⇒ ignored ⇒ nowcast-only behaviour). `qaState().wxTruth`
  exposes `radarSource`/`radarPrecipMm`/`radarAgeSec`/`radarConfirming`/`effectivePrecipMm` + the full source chain.
  *Honest limit:* radar coverage has gaps and the mm proxy is alpha-density, not calibrated dBZ — both safe under
  confirm-only + fail-closed.

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
  OS `prefers-reduced-motion` unless `?motion=full` overrides it.

## Live motion & accessibility

The default widget must **visibly animate in normal real-time** wherever the scene has animatable phenomena — a
static-looking sky is a regression, not a "polish" gap.

- **Pipeline.** One rAF loop. `render()` runs each sim-second (state/sky/marker/moon). The **cloud canvas repaints
  ~13 fps** (`paintClouds(simNow()/1000)`); **star twinkle + glint scintillation, rain, fog, lightning** are CSS
  animations, independent of `render()`. The loop **pauses** (and CSS via `.c.paused`) when the iframe is hidden or
  scrolled offscreen (visibilitychange + IntersectionObserver) — battery for a 24/7 embed.
- **Accessibility.** Under OS `prefers-reduced-motion: reduce` the CSS reduced-motion block stops all atmospheric/
  weather animation and the cloud loop paints **one frozen frame** (no animation). `?motion=full` is an honest
  **override** (adds `.c.motionfull`, clears the JS `_RM`/`_REDUCED` flags) so motion runs even under the OS
  preference — for testing or for users who want it. The default still respects the preference.
- **`?debugMotion=1`** overlays live telemetry: rAF ticks/s, cloud-paint/s, reduced-motion, `motion=full`, paused,
  `timeScale`/advancing, **cloud Δ over 10s/60s**, **star Δ** + whether the twinkle animation is active, the
  weather source, and the reason motion is reduced (if any).
- **The qaState-hash trap (read this).** `qaState().clouds.hash` is position-weighted and flips on sub-pixel change,
  so it "changes every frame" even when nothing visibly moves — it produced false PASS reports. **Never claim live
  motion from the hash.** Verify with a real ≥15–60s watch (the `debugMotion` 10s/60s Δ, a centroid-drift probe, or
  a clip): clouds drifting/morphing, stars scintillating, the sky breathing.

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
- `debugLayers=1`, `debugMoon=1`, `debugMotion=1` — on-card readouts (layers / moon / live-motion telemetry).
  `debugDawn=…` — **deprecated no-op** (dawn is not a painted overlay; nothing to force).
  `motion=full` — force full animation even under OS `prefers-reduced-motion` (accessibility override; default respects it).
- `debugOptic=halo|sundogs|pillar|anticrep|paraselene` — force a (normally condition-gated) optical phenomenon.
- `local=1` — self-configuring mode (coarse auto-detect + in-widget settings, saved locally).
  `preferLocal=1` — hardcoded defaults that a saved local config may override (opt-in). `lp=0..1` — light-pollution dial.

## Config resolution & local mode (`config.js`)

Config logic lives in **`config.js`** (`window.SalahConfig`), a same-origin classic script loaded **before** the
inline page script by **both** `index.html` and `builder.html` — one un-forkable source for parse/validate/
normalize/serialize/load-save-clear-local/coarse-detect. (This deliberately relaxes the old "single self-contained
`index.html`" rule; `index.html` keeps a one-line **legacy fallback** to hash-only parsing if `config.js` 404s.)

- **`WidgetConfig`**: `{v, lat, lon, tz, label, method, school, time, datefmt, units, lp, seed, source, savedAt}`,
  `source ∈ {hash, localStorage, coarse-ip, browser-geolocation, manual, fallback}`. Persisted under
  `salah_widget:config:v1` (separate from the prayer/weather caches; every access wrapped in try/catch).
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

## Known approximations (honest)

- Weather "current" is a model **nowcast, not radar** — the precip gate is conservative, not ground-truth.
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
  paraselenae** and earthshine. Each can be forced via `?debugOptic=`. They are **art-directed approximations
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
current, not forecast). **Live motion (`?debugMotion=1`): a real 15–60s watch — clouds drift/morph, stars
scintillate, sky breathes; cloud Δ 10s ≫ 0. "No visible motion in normal live view" is a FAIL (do NOT trust the
qaState hash).** Optics: force each via `?debugOptic=` and confirm it rings the **visible** sun. Accessibility:
`prefers-reduced-motion` freezes motion by default; `?motion=full` overrides. Layout: footer visible + header
buckle cut-out (no strap through the buckle) + readability in every scene. Dawn: near-Fajr brightening comes only
from the real twilight sky (no painted band/cone), Fajr clear on the arc.
