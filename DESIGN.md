# salah_widget — DESIGN

A static Islamic prayer-times widget, deployed via GitHub Pages and embedded as an iframe (e.g. in TablissNG).
No build step or new dependency. Runtime styles, prayer logic and atmospheric rendering stay in `index.html`;
`config.js` is the shared configuration module, and `builder.html` generates configuration URLs.

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
- **Timetable appearance:** Liquid glass is the default (`appearance=glass`), including absent/legacy values.
  High contrast (`appearance=contrast`) adds local dark backing beneath both ordinary and upcoming cells.
  Default glass fades only elapsed prayers; future rows stay normal, with the current inset and next-prayer tint.
  High contrast keeps every row at full opacity while retaining those current/next highlights. The **4.5:1 white-underlay
  stress gate applies to the contrast option**; default glass does not claim that guarantee. Actual crops still
  decide readability and geometry, not the authored backing ratio alone.

## Prayer-time logic & arc semantics

- Times come from the **Aladhan API**, with admission before state/cache adoption. Only the selected original
  timezone-bearing cache key is read; no zone-free scan, migration or deletion is implied. Cache-zone discovery
  precedes current-day selection; an empty-cache hint response can discover the zone without painting its wrong
  day. A single corrected-day fetch shares the total three-attempt budget.
- **Calendar selection:** one `selectCalendarDisplay(M)` decision uses the captured model instant, strict
  matching Gregorian record day and configured zone. Before Maghrib, usable current AH can show a matching
  next-day preview. At/after Maghrib, AH advances only from usable matching tomorrow; otherwise it retains a
  usable current value with **Sunset date update unavailable**, or says **Hijri date unavailable**. The selected
  Aladhan payload supplies its calendar method; absent metadata says **calendar convention unavailable**.
  Prayer method does not establish a calendar convention. No offset, persisted hold or anomaly detector is
  added; backwards corrections/duplicate/skipped labels remain provider selections, with neutral anomaly data.
- Either footer date button opens complete formatted values and this selection explanation in a stable native
  dialog. Compact ellipsis stays within the fixed footer; literal format/provider text is encoded at markup
  sinks. Selection changes update the open dialog without rebuilding its focused controls.
- **Day-rollover stale cue:** if the calendar day rolls over but the new day's timings can't be loaded (offline /
  fetch failure with no new-day cache), the widget keeps usable prior timings and sets
  `_prayerStale` → a quiet worded **"stale"** chip (warm amber, not alarming) appears by the Hijri date + a faint
  date-row desaturation. Set from `render()` via `.c[data-stale="prayer"]` (never read by `atmosphere()`); scope is
  **prayer-time staleness only**. Calendar unavailability and current-model weather eligibility remain separate.
  `qaState().cache` exposes `prayerStale` + `rolloverPendingMs`.
- Late prefetch can become current after a day boundary; matching tomorrow is promoted before clearing it.
  Accepted bundles and operation completion mark `_renderDirty`, consumed by the existing loop even in frozen
  preview and on the first resumed visible frame. No async completion creates another animation loop.
- Prayer attempts bound complete headers/body/parse/adoption to **10 seconds**, at most three attempts with
  900/1800ms backoff. Same-day recovery starts use a **60-second real elapsed cooldown**; hidden/offscreen pause
  stops those opportunities. Cancellation is cleanup; captured generation/operation/attempt/deadline identity
  decides adoption. These policy values cannot preempt blocked JavaScript or guarantee provider timing.
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
- Debug: `&debugDawn=…` is a **deprecated no-op** — there is no painted dawn layer to force.

## Atmosphere state model

There is **one civil scene API** (`simNow()`/`simDate()`/`nowParts()`) with two explicit authorities. Ordinary
loads with neither `simTime` nor `timeScale` follow `Date.now()`, including backward corrections. Explicit
preview intent uses an anchor plus monotonic elapsed × rate; **`timeScale=1` is an anchored 1× ADVANCING preview**.
`simTime` without a rate freezes the clock-driven scene. Cloud decoration integrates bounded visual elapsed
intervals in the existing loop; it does not determine prayer/solar/lunar civil time.

`epochForTzTime` accepts only a unique Gregorian integer-minute inverse in its inspected ±24-hour offset domain.
Gaps, folds and invalid/unsupported mappings remain unavailable; this is not universal historical timezone
support. A rejected explicit anchor shows **Simulation time unavailable**, withdrawing clock-dependent output
while preserving geometry and Settings access. A usable timetable with an unresolved intended endpoint shows
**Countdown unavailable** instead of wall-minute subtraction.

Each render tick:

1. `atmosphere(M)` derives **one pure state vector** from the physical drivers (solar elevation, lunar geometry/
   phase, gated weather) in a fixed order — colours, opacities, light directions, optics strengths. It touches no
   DOM.
2. `paint(A)` writes sky CSS/state (typed `@property` custom props plus its explicit cloud-state step).
   Prayer, arc, calendar, moon geometry and stellar projection retain their own explicit DOM writers.

**Initial reveal:** celestial/weather decorations start hidden over a neutral usable card. The initial commit
requires a fresh consumed lunar observation and matching stellar projection, resolves the initial styles with
transitions suppressed, then restores ordinary transitions. It does not wait for a guessed timer, fonts or
weather. Real decoded PBR texture/href readiness is separate: a pending/failed lunar surface is unavailable
and earns no textured calendar-disc success. Native first-compositor-frame evidence remains required.

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

- The Moon is an **OPAQUE body — you never see stars through it.** Its decoded PBR calendar surface stays
  opaque/textured at night; the existing group fade blends it into twilight. An independent luminance cutout
  masks the filtered `.stellar-background` (stars, glints and Milky Way) through that fade. The cutout follows
  the moon's transform and actual image radius; it is not a black lunar sprite. Daylight withdraws the surface
  and cutout. Heavy cloud covers the Moon by layer order. Native edge/transition/day-no-hole controls must
  verify this composition; opacity numbers or failed texture decode cannot pass the calendar-disc gate.
- **Physical vs calendar moon.** This widget is also a **lunar-calendar** instrument, so the Moon stays
  meaningfully present **every night** — even when the physical Moon is below the horizon or near-new — by rendering
  the real **opaque phase disc** (a new moon is a *dark ashen disc*, not a blank slot or a transparent one). The
  physical-vs-calendar distinction separates surface appearance from **all atmospheric moonlight consumers**.
  Shared `moonLightEligible` gates the beam, cloud rim, local star wash, generic glow, halo/corona and paraselenae.
  Near-new fraction ≤0.02, zero horizon permission or daylight gives no atmospheric lunar light, including
  forced `lunarhalo`/`paraselene`. This cutoff does not mean zero surface radiance: PBR night-side/Earthshine
  remains separate, **never faked atmospheric light** for the calendar moon. So the calendar moon
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
- **Visual time:** travel, lifecycle and wander advance from real monotonic visual intervals scaled by the
  existing preview rate. The old wind covers the preceding interval before new wind controls future travel.
  Empty decks advance the same state. Repeated reads at the same monotonic instant are idempotent; a repeated
  civil timestamp is not an elapsed-time control. Hidden/reduced intervals hold and rebase; a missing-frame
  gap over two seconds is discarded as suspension, without a travel backlog. An explicit seek/reanchor rebuilds
  deterministically with zero initial displacement. Bounded phases and intersecting periodic copies handle
  edge travel. Rates are artistic; only a real 15–60s watch/clip qualifies perceptible motion.
- **Lighting**: warm sun rim / silver lining on the sun-facing side, cool moonlit edges at night, leaden
  undersides in storm, lit tops / shaded bases for volume; rain/fog diffuse.
- **Continuity**: population identity uses signed accepted coordinates, explicit `seed` and the explicit preview
  anchor/rate where applicable. The initial civil-day seed contribution is captured once: ordinary UTC
  day/month/year changes, default-wall zone corrections and weather refresh retain population. Live coverage **eases** toward its target so a
  15-minute refetch grows/erodes the existing deck smoothly (snapping only on first establishment and under
  fast-forward) — no "slideshow".
- **Rain** uses actual visible cloud footprints (`_colDens`), fading before the prayer list. Columns grant no
  precipitation permission. Marked previews and separately admitted synthetic QA can exercise rain/snow/
  lightning; ordinary selected live adapters cannot permit those strong local effects.
- **Lightning** is a **procedural branching channel** (midpoint-displacement stepped leader + forks from the
  cloud base, sometimes reaching the lower third), regenerated each strike, with a persistent storm-glow so the
  storm reads between strikes — not a symbolic bolt.

### Weather truthfulness (critical)

Open-Meteo `current=` and `hourly=` are **model products**. Eligible current data remains useful temperature/
cloud/fog/visibility information, displayed with **≈** and a model-estimate/unobserved-local-precipitation
accessible description. Absent/expired current shows **? / Weather unavailable**. Source and receipt ages must
both be nonnegative and no older than fifteen minutes, with positive source interval, units and captured target
identity. Expiry withdraws current temperature, wind, cloud and humidity inputs; readable retained data has no
current render authority.

- **Strong local rain/snow/lightning permission is closed for the selected live adapters.** Model WMO codes/
  amounts and RainViewer tile palette/alpha cannot establish supported wet, supported dry, lightning or arrival.
  Unknown local observation is not observed dry. Live nearby/approach remains unavailable; no new provider,
  radar motion estimator or ETA is introduced. RainViewer tile diagnostics/freshness remain inspectable without
  calibrated mm authority or a confirm-only safety claim.
- **Quantity windows:** current precipitation is a **preceding-interval** amount in mm; a derived mm/h value is
  only an interval mean. Forecast precipitation is the stepped source amount for the **preceding-hour** window.
  Neither supplies instantaneous intensity, onset, arrival or probability. Missing issue time, probability/event,
  coverage/health and native/interpolated spatial precision remain unavailable.
- **Explicit preview:** `SIM.wx` and ADVANCING hourly interpolation remain visibly marked SIM. Model thresholds
  (`≥0.05mm` precipitation, `≥0.8mm` thunder) still distinguish preview/gated model categories; they do not grant
  live present permission. The forecast track never becomes a local observation.
- **Admitted synthetic QA:** `synthetic-present-v1` is a separate test lane, requiring exact synthetic identity,
  target generation, qualified direct point coverage/operational health, measurement and underlying observation
  times, receipt and an exclusive lease end. A fresh receipt cannot renew an old/unknown underlying observation.
  Its fixture device-target policy additionally requires actual original browser fix age ≤5 minutes and reported
  accuracy ≤250m; fixed sites are configured points, not device-presence claims. These are fixture policy bounds,
  not a certified live provider radius. Wet/model-clear can render rain; dry/conflicting/unknown cannot borrow
  model permission. Lightning additionally needs qualified synthetic lightning with current rain. Expiry, rain
  end, outage and superseded generation withdraw particles immediately, independently of cloud easing.
  No production network/hash setter or `trusted:true` field supplies this admission shortcut.

`qaState().wxTruth` separates target/fix age, model/present/disagreement, spatial/horizon/forecast, source/receipt/
quantity and permissions/lane/final paint. `observedPrecipMm` is populated only from qualified synthetic amount
evidence; its legacy name does not reclassify the live model.

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

- **Pipeline.** One rAF loop. `render()` runs on changed civil seconds or accepted dirty state (state/sky/marker/moon). The **cloud canvas repaints
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
- **Open-Meteo** `forecast` — `current=` (model temp/humidity/wind/cloud layers/visibility/`weather_code`/
  **precipitation**/rain/showers/snowfall/is_day) and `hourly=` 3-day track; plus grid-cell `elevation`.
- **RainViewer** — manifest/tile diagnostics; no supported local mm, observed-dry or arrival claim. Requests and
  fields are disclosed in [README privacy](README.md#auto-detect-precise-location--privacy).

## URL / hash & debug parameters

Configuration and diagnostics are read from the fragment after `#`. Append `&debugMotion=1` or
`&motion=full` to that same fragment. A query-only `?debugMotion=1` is not read.
The six `debugOptic` force names are `halo`, `sundogs`, `pillar`, `anticrep`, `paraselene` and `lunarhalo`.
Corona, earthshine, refraction and the crepuscular ray require controlled physical scene inputs;
no dedicated `debugOptic` switch forces them.

Complete real-time motion recipes, relative to the served folder:

```text
index.html#lat=24.47&lon=39.61&label=Madinah&method=4&debugMotion=1
index.html#lat=24.47&lon=39.61&label=Madinah&method=4&debugMotion=1&motion=full
```

Copyable force-activation example:

```text
index.html#lat=24.47&lon=39.61&label=Madinah&method=4&simTime=12:30&debugOptic=halo
```

For other switch branches, replace only `halo` with a supported name and select a recorded solar/lunar
scene appropriate to its pixel check. The noon example proves neither lunar visibility nor every
effect's appearance. simTime without timeScale freezes the clock-driven scene. Use the real-time
recipe above for a 15–60 second motion check. Flag activation alone does not prove visible motion or correct optical pixels.

Lunar force positive and near-new negative (new document for each boot flag set):

```text
index.html#lat=24.47&lon=39.61&label=Madinah&method=4&simTime=23:30&simMoon=0.98&simWax=1&simMoonAlt=20&simMoonH=42&debugOptic=lunarhalo
index.html#lat=24.47&lon=39.61&label=Madinah&method=4&simTime=23:30&simMoon=0.01&simWax=1&simMoonAlt=20&simMoonH=42&debugOptic=lunarhalo
```

The negative must retain a decoded opaque Earthshine calendar disc while atmospheric lunar light and halo
remain off. `paraselene` retains the same physical eligibility guard. Corona/Earthshine/refraction/crepuscular
checks still need recorded physical scene inputs. Changing a forced `paintClouds(t)` timestamp does not prove
elapsed cloud travel; its argument initializes/reconstructs civil scene state.

Common fragment parameters:

- `lat`, `lon`, `label`, `method`, `units`, `appearance=glass|contrast` — configured location/preferences.
- `seed` — varies the synthetic star draw + cloud field identity.
- `timeScale=<n>` — explicit anchored preview (n× real time; `1` is still preview); positive rate enables ADVANCING (forecast-driven weather, re-projected stars,
  the sim clock).
- `simTime=HH:MM` — freeze the clock at a time without `timeScale` (TIMESCALE 0).
- `simWx=<wmo code>` — force a preview weather class; `simPrecip=<mm>` — synthetic preview amount (to QA the gate,
  e.g. `simWx=95&simPrecip=0` ⇒ dry forecast-thunder ⇒ downgraded). `simTemp`, `simFeels`, `simWind`,
  `simWindDir`, `simHumid`, `simCloud`, `simMoon`, `simWax`, `simMoonAlt`, `simMoonH`.
- `qa=1` + `window.qaState()` — a structured snapshot (incl. `wxTruth`).
- `debugLayers=1`, `debugMoon=1`, `debugMotion=1` — on-card readouts (layers / moon / live-motion telemetry).
  `debugDawn=…` — **deprecated no-op** (dawn is not a painted overlay; nothing to force).
  `motion=full` — force full animation even under OS `prefers-reduced-motion` (accessibility override; default respects it).
- `debugOptic=halo|sundogs|pillar|anticrep|paraselene|lunarhalo` — the six supported optical force branches.
- `local=1` — self-configuring mode (coarse auto-detect + in-widget settings, saved locally).
  `preferLocal=1` — hardcoded defaults that a saved local config may override (opt-in). `lp=0..1` — light-pollution dial.

## Config resolution & local mode (`config.js`)

Config logic lives in **`config.js`** (`window.SalahConfig`), a same-origin classic script loaded **before** the
inline page script by **both** `index.html` and `builder.html` — one un-forkable source for parse/validate/
normalize/serialize/load-save-clear-local/coarse-detect. (This deliberately relaxes the old "single self-contained
`index.html`" rule; `index.html` keeps a one-line **legacy fallback** to hash-only parsing if `config.js` 404s.)

- **`WidgetConfig`**: `{v, lat, lon, tz, label, method, school, time, datefmt, units, appearance, lp, seed, source, origin, savedAt, locationEvidence}`,
  `source ∈ {hash, localStorage, coarse-ip, browser-geolocation, manual, fallback}`. Persisted under
  `salah_widget:config:v1` (separate from the prayer/weather caches; every access wrapped in try/catch).
- **Private location evidence:** `locationEvidence` keeps intent (`fixed-site`, device-position, coarse-area or
  unknown), acquisition source, `accuracyM`, original `acquiredAt`, provider/area/bounds or null unknowns.
  Browser acquisition uses actual Position accuracy/timestamp, never decimal-derived precision or `savedAt` as
  fix time. Preference/label/reverse-name changes keep original evidence; coordinate edits become manual
  fixed-site. Saved browser positions remain usable targets, not “here now.” Current readers preserve origin
  independently of the outer storage marker; stored browser-origin copies are conservative for older readers.
  Portable/prefer-local/local fragments omit acquisition history. WEATHER captures normalized primitives
  synchronously before awaits and binds consumption to the target generation.
- **Precedence:** explicit hardcoded hash (unless `local`/`preferLocal`) → saved local → coarse IP/timezone detect
  → manual setup → safe error. **Stale localStorage never overrides an intentional hardcoded embed.**
- **Sync vs async:** hardcoded resolves **synchronously at module load**. Only `local`/`preferLocal` **without** a saved config defer to
  the async `coarseDetect()` in `boot()`; failure opens the manual settings panel (never crashes).
- **Coarse detect:** GeoJS (`get.geojs.io/v1/ip/geo.json`) → ipinfo.io fallback, complete-response deadline with optional abort cleanup, IANA tz
  from the device (`Intl`) first. Approximate (IP-based) — surfaced as "estimated area," never "precise."
- **Runtime apply** (`applyConfig`): the settings panel updates the live config **in-memory, no reload** (so it
  works when third-party-iframe storage is blocked). `cacheKey`/`wxKey` are **functions** (not consts) so the new
  location's caches are keyed correctly; the post-config pipeline (`startWeather`/`loadPrayerData`/`startRenderLoop`)
  is shared by `boot()` and apply.
- **Persistence outcome:** save/reset results publish before provider awaits, including a warning available from
  the closed Settings opener. Refused save retains session choices; refused reset retains selected config and
  stops before re-detection. Successful reset removes only the config key. Writable partitioned storage is
  distinct from denied storage. Builder local exports explicitly retain selected method/units/appearance;
  portable and local builder defaults serialize `appearance=glass`, while saved local preferences take priority.
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
  preset's iframe (replacing `#local=1`). Bash uses Python literal string replacement followed by JSON validation;
  PowerShell's `.Replace` is literal. The copied command fetches published `main`, not a local candidate.
  See [README installer usage](README.md#one-line-install-optional-setup-wizard) for reviewed-file execution,
  offline/no-effect preview, terminal requirements and the manual file lifetime. The Bash private retained
  bundle and same-attempt cache are separate from Windows TEMP staging; neither staging nor Enter confirms
  browser installation/import.

## Known approximations (honest)

- Weather current is a **model estimate**; live local observation/nearby/arrival is unavailable for these adapters.
  Synthetic QA proves consumer behavior, not provider skill. The round-4 adaptive-performance governor remains
  held; this continuity work adds no governor, new provider or measured CPU/battery claim.
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
  paraselenae** and earthshine. The six `debugOptic` names above force only their corresponding branches;
  corona, earthshine, refraction and the crepuscular ray need physical scene inputs. They are **art-directed approximations
  (believable, not photometric)**; the moon's halo/pillar may show as partial arcs because the halo radius exceeds
  the (mostly in-frame) disc. The **corner-sun body stays top-left** in all states (a layout stylization — the moon
  owns top-right); the azimuthal horizon glow correctly moves left→right dawn→dusk.

## QA matrix (scenes to check before claiming done)

Required native cells, not a PASS statement: clear noon (**defined sun nucleus**, not a vague brush), sunrise (enters low from the left, warm), sunset
(warm sky, not generic daylight), broken-cloud golden hour, overcast (**warm-white sun through cloud, never a
grey/purple blob**), separately marked preview/admitted synthetic rain, snow and thunderstorm. Night: clear (stars + scintillation), thin crescent (right limb
in frame, earthshine), gibbous (earthshine), full moon (bright opaque disc, local star wash), **new moon (a faint
ashen OPAQUE calendar disc — never an empty slot, never moonlight)**, thin-cloud night (halo/corona).
**Moon must be OPAQUE — no stars visible through the disc, in any phase.** Weather truth: `simWx=95&simPrecip=0`
(must downgrade), `simWx=95&simPrecip=5` (preview thunder), `simWx=65&simPrecip=0` (downgrade), live fresh/expired
model positives with strong effects off; admitted synthetic wet/dry/end/outage/exclusive-expiry/generation
controls. First neutral/reveal and pending/failed texture, twilight interior/edge/exterior star/glint/Milky Way
probes, no daytime hole; cloud wind/day/empty/seek/gap/hidden/reduced transitions. **Live motion (`&debugMotion=1`): a real 15–60s watch — clouds drift/morph, stars
scintillate, sky breathes; cloud Δ 10s ≫ 0. "No visible motion in normal live view" is a FAIL (do NOT trust the
qaState hash).** Optics: use the six supported `&debugOptic=…` branches or controlled physical scene inputs;
confirm solar optics register to the **visible** sun and lunar optics to the moon. Accessibility:
`prefers-reduced-motion` freezes motion by default; `&motion=full` overrides. Layout: footer visible + header
buckle cut-out (no strap through the buckle) + default glass/opt-in contrast readability and real-font/footer
access in the actual 325×530 card. Dawn: near-Fajr brightening comes only
from the real twilight sky (no painted band/cone), Fajr clear on the arc.
