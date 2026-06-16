# salah_widget — AGENTS

How agents (human or AI) should work on this repo. The widget is one self-contained `index.html`; changes are
visual and physics-adjacent, so **review is dominated by looking at rendered pixels**, not by reading metrics.

## Golden rules

- **Screenshots override metrics.** A passing `qaState()` number does not pass a cycle if the screenshot looks
  wrong. Every visual claim needs a crop/clip.
- **Truthfulness over drama.** Never make the widget claim a condition it can't support (see "Weather" below).
- **Do not commit unless explicitly asked.** When asked, `main` is the GitHub Pages deploy branch.
- **No broad refactors mixed into a feature/fix.** Keep diffs inspectable. Document before refactoring.
- **Physics gates the art.** Optical phenomena must be condition-gated (ice vs droplet, low-sun + broken cloud,
  humidity, etc.), never random or always-on.

## Subagent roles & what each reviews

- **GitHub/source auditor** — confirms the committed `index.html` matches what's served; lists the relevant
  systems before any edit.
- **Runtime DOM/CSS/canvas auditor** — measures live geometry (header/footer, cloud band vs dashed horizon, moon
  layers/radius/alpha **+ disc opacity/occlusion (no stars through)**, buckle cut-out vs strap, rain origin vs
  cloud columns) and reports numbers + crops.
- **Live-motion auditor** — proves the default real-time widget actually animates over 15–60s (cloud drift/morph,
  star scintillation, sky breathing) via `?debugMotion=1` Δ / a clip / a centroid-drift probe. **Must NOT cite the
  `qaState().clouds.hash` as motion evidence** (it flips on sub-pixel change — it produced false PASS reports).
- **Atmospheric-optics researcher** — supplies condition gates, geometry, colour orders, gradient recipes for each
  phenomenon before it is coded.
- **Islamic dawn / Fajr semantics researcher** — verifies false-dawn (vertical) vs true-dawn (horizontal) and the
  Fajr depression range; confirms dawn visuals never drive the prayer clock.
- **Solar / lunar renderer art directors** — judge sun placement/optics and moon PBR/earthshine/halo/corona from
  forced-condition crops.
- **Cloud/weather lighting judge** — structure, lighting, weather linkage, and **continuity** (no slideshow).
- **Star/night-sky judge** — variety, twinkle (visible but not cartoonish), moon wash, location/weather response.
- **UI/layout invariant judge** — footer visible + header geometry + readability in *every* scene.
- **Documentation architect / code-comment reviewer** — keep DESIGN.md/AGENTS.md and the high-value comments true.
- **Skeptic visual panel (≥5)** — may FAIL any cycle; must list failures and residual approximations.
- **Regression judge** — diffs old screenshots vs current; flags anything that got worse.

Note: judges that drive the live preview must run **sequentially** (one shared preview server; parallel judges
stomp on each other's scenes). State this honestly rather than faking a simultaneous panel.

## Required PASS/FAIL gates

A cycle PASSES only when, with **screenshot/clip evidence**:

- A — Sun is a **defined radiant body with a clear nucleus**, not a vague brush; colour is **tone-mapped/white-
  balanced** (airmass + transmittance + CCT + ACES) — under cloud it goes **warm-white, never a grey/purple blob**.
- B — Sunrise **enters low from the left** near the horizon (warm glowing disc); sunset sky is warm (not generic
  daylight); low-sun colour believable; low-sun refraction flattening.
- C — Solar optics distinct + gated (halo / parhelia / pillar / crepuscular / anticrepuscular / refraction), each
  only under its physical condition, and **registered to the VISIBLE corner sun** (`--sunvx/--sunvy`) — a center-
  screen halo is a FAIL.
- D — Moon is **OPAQUE every night (no stars through the disc)** and **meaningfully present every night** — a new/
  below-horizon moon shows a faint **ashen opaque calendar disc with NO moonlight** (never blank, never faked
  light); the disc is **mostly in frame** so the phase reads. Earthshine correct across crescent/half/gibbous/full
  (gibbous dark side faint **but textured, never a black cutout**).
- E — Lunar corona (small, close) vs 22° halo (large ring) vs paraselenae (lateral, rare) are distinct + gated.
- F — **Dawn is honest, not painted:** true dawn is the **real physical twilight sky** (dark at Fajr depth,
  brightening toward sunrise) + the Fajr marker — **no horizontal "true-dawn band."** False dawn is **fail-closed
  (not rendered)** — **no diagonal cone / lens-flare slash**, and nothing under a bright moon.
- G — Clouds structured, lit, weather-linked; small distinct cells; mostly around/above the dashed 0° horizon.
- H — Rain/lightning originate from cloud systems and vary by weather type/intensity.
- I — Stars beautiful/alive/varied; **not** a spinning or static image; anchors + their glints **scintillate**.
- J — Header belt (buckle **cut-out**, no strap through it) + footer + prayer UI intact and readable in every scene.
- **M0 (live motion) — the default real-time widget VISIBLY animates over 15–60s where the scene allows (clouds
  drift/morph, stars scintillate, sky breathes). Proven by a real watch / `?debugMotion=1` Δ, NEVER the qaState
  hash. Accessibility: `prefers-reduced-motion` reduces it by default; `?motion=full` overrides.**
- K/L/M — DESIGN.md + AGENTS.md + HANDOFF.md current; high-value comments present; approximations stated honestly.

## Evidence requirements (per cycle)

Crops/clips for: clear-day apex (**defined nucleus**), sunrise (enters low-left), sunset (warm sky), overcast
(**warm-white sun, not grey/purple**), forced parhelia/halo/pillar (**ringing the visible sun**), forced
crepuscular/anticrepuscular, crescent (**right limb in frame**)/half/gibbous/full moon, **new moon (opaque ashen
calendar disc)**, **moon-opacity proof (no stars through the disc)**, forced lunar corona/halo/paraselene, daytime
clouds, moonlit night clouds, rain + thunder, star twinkle, **header buckle cut-out (zoom — no strap through)**,
header/footer, near-Fajr (real twilight, **no painted dawn band/cone**). Plus a **real 15–60s live-motion clip /
`debugMotion` 10s–60s Δ** (the headline gate), 5m/15m/60m/day simulated deltas, and `motion=full` vs reduced-motion.
Judges list failures and residual approximations. **Screenshots/Δ — never the qaState hash — decide motion.**

## Forbidden regressions (instant FAIL)

- **No visible motion in normal live real-time view** (a static "wallpaper" sky). Verify with a real 15–60s watch
  / `?debugMotion=1` 10s–60s Δ — **NOT** the `qaState().clouds.hash` (it flips on sub-pixel change and lies).
- The **moon rendered transparent** — stars visible *through* the disc, in ANY phase. The Moon is an opaque body.
- An **empty moon slot / moonless normal night.** A new/below-horizon moon must still show a faint **ashen OPAQUE
  calendar disc** (no moonlight) — never blank sky, never a "new moon invisible" rule.
- A **painted false-dawn cone or horizontal true-dawn band/strip.** Dawn = the real physical twilight sky + the
  Fajr marker; false dawn is **fail-closed** (not rendered) until properly modeled.
- The **sun rendered as a dim grey/purple blob** or a vague brush with **no defined nucleus** (use the scene-
  referred tone-map; cloud → warm-white, never cold grey).
- **Solar optics (halo / sundogs / pillar) detached from the visible sun** (they must register to `--sunvx/--sunvy`,
  not the arc-sun azimuth). A center-screen halo is an instant FAIL.
- Footer date row clipped or any header change that **moves the content stack**.
- **Builder/embed:** the iframe wrapper size drifting from the widget card — it must be **325×530** (= `.c`) in the
  builder preview, the copy snippet, README, and the TablissNG preset (an oversized wrapper adds invisible margin
  and misaligns the builder card/buttons).
- Header buckle off-centre, straps full-width, a heavy drop shadow, or **any strap geometry visible THROUGH the
  translucent buckle** (the strap inner ends must be *masked/cut*, not merely z-indexed — translucent glass reveals
  what's under it).
- Sunrise marker drawn as a filled dot (it is a **ring**) or off the dashed line; Maghrib off the line; **Dhuhr
  on the apex**.
- The moon's dark limb rendered as a **black cutout**, or a jaggy/stroked moon edge.
- A **generic** glow standing in for a gated optical phenomenon.
- **Claiming rain/thunderstorm without active observed-precip evidence**, or letting the hourly forecast overwrite
  the current observed condition in real-time.
- Clouds that **reseed / slideshow** on weather refresh or per render tick.
- Replacing the accurate PBR moon lighting with a flat sprite; making physics "ugly".

## Commit policy

Do not commit or push unless the user explicitly asks. When asked: commit the **relevant source + docs**
(`index.html`, `config.js`, `builder.html`, `install.sh`/`install.ps1`, `presets/`, `tests/`, the `*.md` docs) —
**never** the stray research scratch files (`noaa_clouds.html`, `*_photopills.html`, `_mag_extract.txt`, etc.).
`main` deploys to GitHub Pages, so a commit to `main` is a deploy. End commit messages with the standard
`Co-Authored-By` line.

## Running / debugging common scenarios

Serve the folder statically and open `index.html#lat=24.47&lon=39.61&label=Madinah&method=4`.

- Day positions: `&simTime=12:30` (noon), `&simTime=05:50` (sunrise), `&simTime=18:55` (sunset/golden hour).
- Weather visuals: `&simWx=2&simCloud=50` (broken), `&simWx=3&simCloud=100` (overcast), `&simWx=63` (rain),
  `&simWx=95` (thunder), `&simWx=45` (fog).
- **Weather-truth QA**: `&simWx=95&simPrecip=0` must downgrade (no thunder/rain); `&simWx=95&simPrecip=5` keeps
  thunder; check `qaState().wxTruth` for the source/reason chain.
- Moon: `&simMoon=0.08&simWax=1&simMoonAlt=20&simMoonH=42` (crescent), `&simMoon=0.92…` (gibbous), `&simMoon=0.98…`
  (full); thin-cloud halo/corona via `&simWx=2&simCloud=30` on a moon scene.
- **Live motion**: load real-time (no `simTime`) and **watch ~15–60s** — clouds must drift/morph, stars
  scintillate, sky breathe. `&debugMotion=1` shows rAF/s, cloud-paint/s, reduced-motion, paused, **cloud Δ 10s/60s**,
  star Δ, reason. `&motion=full` forces motion under OS reduced-motion. `&timeScale=1800` fast-forwards a day.
- **Moon opacity**: any night moon — confirm **no stars show through the disc**; new moon (`&simMoon=0.01`) shows a
  faint **opaque** ashen calendar disc with `qaState().moonTruth.moonlightOpacity == 0`.
- Readouts: `&debugLayers=1`, `&debugMoon=1`, `&debugMotion=1`, `&qa=1` then `window.qaState()` (incl. `wxTruth`,
  `moonTruth`). `&debugDawn=…` is a deprecated no-op (dawn is not painted).
- Preview gotcha: `simTime` without `timeScale` freezes the clock (TIMESCALE 0), so cloud drift won't be visible
  in a still test — use the direct `paintClouds(t)` probe or a real-time / `timeScale` watch to see motion.
