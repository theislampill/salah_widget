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
  layers/radius/alpha, rain origin vs cloud columns) and reports numbers + crops.
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

- A — Sun apex higher/coherent; the sun is a defined radiant body, not a vague brush.
- B — Sunrise rises from the left near the horizon; sunset accounted for; low-sun colour believable.
- C — Solar optics distinct + gated (halo / parhelia / pillar / crepuscular / anticrepuscular / refraction) —
  each only under its physical condition.
- D — Moon appears meaningfully every night; earthshine correct across crescent/half/gibbous/full (gibbous dark
  side faint **but textured, never a black cutout**).
- E — Lunar corona (small, close) vs 22° halo (large ring) vs paraselenae (lateral, rare) are distinct + gated.
- F — False dawn (vertical) and true dawn (horizontal) are visually + semantically distinct; Fajr sky stays dark
  with a faint horizon thread, not a bright palette.
- G — Clouds structured, lit, weather-linked; small distinct cells; mostly around/above the dashed 0° horizon.
- H — Rain/lightning originate from cloud systems and vary by weather type/intensity.
- I — Stars beautiful/alive/varied; **not** a spinning or static image.
- J — Header belt + footer + prayer UI intact and readable in every scene.
- K/L/M — DESIGN.md + AGENTS.md current; high-value comments present; approximations stated honestly.

## Evidence requirements (per cycle)

Crops/clips for: clear-day apex, sunrise, sunset, forced parhelia/halo/pillar, forced crepuscular/anticrepuscular,
forced false-dawn vs true-dawn, crescent/half/gibbous/full moon, forced lunar corona/halo/paraselene, daytime
clouds, moonlit night clouds, rain + thunder, star twinkle, header/footer. Plus 5m/15m/60m/day simulated deltas
and a 30–60s real-time continuity watch where feasible. Judges list failures and residual approximations.

## Forbidden regressions (instant FAIL)

- Footer date row clipped or any header change that **moves the content stack**.
- Header buckle off-centre, straps full-width, or the belt showing **behind** the buckle, or a heavy drop shadow.
- Sunrise marker drawn as a filled dot (it is a **ring**) or off the dashed line; Maghrib off the line; **Dhuhr
  on the apex**.
- The moon's dark limb rendered as a **black cutout**, or a jaggy/stroked moon edge.
- A **generic** glow standing in for a gated optical phenomenon.
- **Claiming rain/thunderstorm without active observed-precip evidence**, or letting the hourly forecast overwrite
  the current observed condition in real-time.
- Clouds that **reseed / slideshow** on weather refresh or per render tick.
- Replacing the accurate PBR moon lighting with a flat sprite; making physics "ugly".

## Commit policy

Do not commit or push unless the user explicitly asks. When asked: commit only `index.html` (+ docs) — never the
stray research scratch files (`noaa_clouds.html`, `*_photopills.html`, `_mag_extract.txt`, etc.). `main` deploys
to GitHub Pages, so a commit to `main` is a deploy. End commit messages with the standard `Co-Authored-By` line.

## Running / debugging common scenarios

Serve the folder statically and open `index.html#lat=24.47&lon=39.61&label=Madinah&method=4`.

- Day positions: `&simTime=12:30` (noon), `&simTime=05:50` (sunrise), `&simTime=18:55` (sunset/golden hour).
- Weather visuals: `&simWx=2&simCloud=50` (broken), `&simWx=3&simCloud=100` (overcast), `&simWx=63` (rain),
  `&simWx=95` (thunder), `&simWx=45` (fog).
- **Weather-truth QA**: `&simWx=95&simPrecip=0` must downgrade (no thunder/rain); `&simWx=95&simPrecip=5` keeps
  thunder; check `qaState().wxTruth` for the source/reason chain.
- Moon: `&simMoon=0.08&simWax=1&simMoonAlt=20&simMoonH=42` (crescent), `&simMoon=0.92…` (gibbous), `&simMoon=0.98…`
  (full); thin-cloud halo/corona via `&simWx=2&simCloud=30` on a moon scene.
- Motion/cycles: `&timeScale=1800` (fast-forward a day); continuity: load real-time and watch ~60s.
- Readouts: `&debugLayers=1`, `&debugMoon=1`, `&qa=1` then `window.qaState()`.
- Preview gotcha: `simTime` without `timeScale` freezes the clock (TIMESCALE 0), so cloud drift won't be visible
  in a still test — use the direct `paintClouds(t)` probe or a real-time / `timeScale` watch to see motion.
