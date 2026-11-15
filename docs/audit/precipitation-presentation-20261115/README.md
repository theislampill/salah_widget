# Precipitation presentation — evaluation (2026-11-15)

Research and evaluation only. No product file is changed on this branch; every experimental variant is a
browser-injected overlay inside the evaluation harness (`tools/qa/precip_eval_levers.js`) and is not a merge
candidate. Any production change needs its own work order and the owner's visual approval afterwards.

- Measured commit: `8990c36d` (main at start of measurement; R0032 radar disabled, R0031 GPS). Main later moved to
  `a196351b` (R0033 Moon recovery) with no change to precipitation code; `93f7c262..8990c36d` touched no
  precipitation presentation either (only radar labels).
- Owner finding under test: rain "reads as overly uniform and insufficiently integrated with the scene … more like a
  canned overlay than a physically and visually coherent weather state".
- Builds on, and re-verifies, the independent stage-2 survey judgement (precipitation section) rather than repeating
  it. Its claims (1) fixed 32-drop overlay varying by opacity only and (2) partial rain look on the data path without
  evidence are both **confirmed** below, with additional defects it did not report.

Harness (all registered in `tests/regression-population.json`): `tools/qa/precip_eval_capture.cjs` (capture),
`precip_eval_lib.cjs` (loopback server, stubbed Aladhan/Open-Meteo/RainViewer, catch-all route installed on the
context before any page exists, only loopback continued, run fails on any non-loopback escape),
`precip_eval_levers.js` (overlay), `precip_eval_report.py` (metrics, sheets, animations). Card 325x530, DPR 1,
Madinah, 2026-09-23, data path (Open-Meteo current fixture with admitted precipitation) unless marked "sim".
**Network: every run logged `continuedExternal = 0`; the only aborted host was fonts.googleapis.com.**

Two capture modes:
- *stepped* (metrics): mocked paused clock advanced 1/15 s per frame; every CSS animation paused and its
  `currentTime` advanced by the same step; two lossless screenshots per frame (card, and card with the streak layer
  hidden) so `|a-b|` isolates the rain; streak geometry per frame. 10 s x 15 fps (wind matrix 6 s).
- *realtime* (motion evidence): mocked clock running at wall rate, CSS/rAF unassisted, Playwright video,
  headed Chromium and Firefox, headless WebKit.

Clips: 96 baseline (intensity x time, wind, gust, sim twins, no-evidence twin), 20-cell evaluation matrix
(light / moderate / heavy / scattered / storm x noon / dusk x calm / 10 m/s), each lever alone on three cells, a
control (overlay with all levers off), the combined variant on all 20 cells, both slant signs, three engines on the
headline cells, reduced-motion probes. Metrics: `metrics/baseline-clips.json`, `metrics/evaluation-clips.json`.

## Part A — what exists

### A1 Producer and parameter mapping (`src/native/index.html` at 8990c36d)

| Element | Anchor | Fact |
|---|---|---|
| Pool | `buildWeather` L2453, drops L2459 | 32 `.drop` divs, built once, deterministic: `left=(i*7.3+2)%100 %`, height `12+(i%4)*3` (12/15/18/21 px), duration `0.6+(i%5)*0.08` s (0.60–0.92), delay `-i*0.09` s; plus 40 `.flake`. No RNG, no re-seeding: **each drop falls in the same column forever**. |
| Streak | L236 | width 1.5 px, pale blue gradient `#b9dcf5` 0 → 0.8 alpha, `top:19%` (cloud base ≈ y 91). |
| Motion | `@keyframes fall` L250 | translate (0,−10) → (`--rain-slant`, 132 px); opacity 0 → `--rain-op` (22–60 %) → 0. **Translate only: the streak never rotates**, so with wind it is a vertical stick moving diagonally (see zoom in "Demonstrated defects"). |
| Intensity | `rainOp` L3387 | `0.42 + 0.6·clamp((mm − 0.1)/6)` of the **raw interval amount**, 0.72 if unknown; saturates at 6.1 mm per 15 min. The only intensity response. |
| Class reveal | L272–274 | rain/thunder: all 32; drizzle: every 3rd (11) with `opacity:.6; animation-duration:.85s`; thunder `animation-duration:.4s`. **The drizzle and thunder durations and the drizzle opacity are dead CSS**: inline `animationDuration` beats the stylesheet and the keyframe opacity beats the declared opacity (computed `animationDuration` measured 0.6/0.68/0.76 s for thunder and drizzle). |
| Slant | `rainSlant` L3413, set L3499 | `windX·wind01·120` px over the 132 px fall, `wind01 = clamp((m/s − 0.5)/13.5)`, `windX = −sin(dir)` (map convention). Identical for drizzle, rain and storm; snow ×2.5. Saturates at 14 m/s (10 m/s → 32.5°, 20 m/s → 42.3°). |
| Gust | `wxDrivers` L1789 | normalised, **read by nothing** (confirms issue 124 research). Clips with gust 8.5 vs 22 m/s are metric-identical. |
| Cloud origin | `tieRainToClouds` L3091 | a drop is hidden when its column density ≤ 0.16 × max (gate H mechanism). |
| Reduced motion | L164 | `animation:none!important` → 32 streaks frozen at `top:19%`, **opacity 1** (ignores `--rain-op`): a comb across the sky at the deck base. |
| Lightning | flash/bolt L239–277, bucket L~3805 | only with `visualPermissions.lightning` (SIM thunder); never on the data path (fixture thunder clips: lightning off). |

WMO classes (`wxClass` L2835): 51–57 drizzle; 61–67 and 80–82 rain; 71–77, 85–86 snow; ≥95 thunder. Light /
moderate / heavy (61/63/65) and slight / moderate / violent showers (80/81/82) map to the same class; only the
amount changes `--rain-op`.

Measured per intensity (data path, noon, 4 m/s from 225°; fixture amount per 15 min → widget's own mm/h):

| Cell | mm/15 min (mm/h) | visible streaks | length p50 px | speed p50 px/s | streak opacity p50 | lean |
|---|---|---|---|---|---|---|
| drizzle 53 | 0.2 (0.8) | 11 | 18 | 187.5 | 0.34 | 9.5° |
| light 61 | 0.4 (1.6) | 32 | 16.5 | 187.5 | 0.37 | 9.5° |
| moderate 63 | 1.2 (4.8) | 32 | 16.5 | 187.5 | 0.43 | 9.5° |
| heavy 65 | 4 (16) | 32 | 16.5 | 187.5 | 0.66 | 9.5° |
| violent showers 82 | 8 (32) | 32 | 16.5 | 187.5 | 0.80 | 9.5° |
| storm 95 | 3 (12) | 32 | 16.5 | 187.5 | 0.58 | 9.5° |
| scattered showers 80, 40 % cloud | 0.5 (2) | 32 (noon), 21 (golden) | 16.5 | 187.5 | 0.37 | 9.5° |

Speed p5–p95 is 154–237 px/s in every cell, drizzle included.

### A2 What else changes with precipitation

- Class tables keyed on `data-fx`: veil opacity (drizzle .46, rain .62, thunder .74; L264–270), `WX` tint/accent
  (L2851), cloud underlight `wet` (L3315), default layer split when the record lacks layers (L3349), solar
  `_tcLUT` (L3127: rain 0.40, thunder 0.22) — **used for ray opacity and colour only; the sun body radiance
  `_bodyL` (L3145) ignores cloud and rain** (confirms survey claim 3).
- None of these depends on the amount: light and violent rain share one veil, tint, deck and sun.
- Visibility: the refined sky reads only `vis`, `temp`, `src` (`real-sky/native-contract.mjs` L9–25); rain does
  not alter `vis`. A provider visibility that is low because of rain would reach the aerosol term and `D.haze`; the
  widget adds nothing of its own. SIM fixtures set `vis` 20 km regardless of rain (L3952).
- Measured: horizon-band L* at noon is 64.6–65.1 for light, moderate, heavy, violent, storm and 64.1 for a dry
  overcast deck (dusk: 20.0–21.0 for all). Rain does not lower horizon contrast (band σL 12.9–13.0 for all
  intensities). Sun-region 99.5th-percentile L* is the same for light and heavy rain.
- Deck coverage (survey claim 4, not re-measured): the deck fills the top band only; the Moon stays fully visible
  through heavy rain at dusk (frame in `anim/precip-storm-dusk-before-after.webp`).
- Nothing on the glass panels responds to rain.

### A3 Registry, ownership, tests, truth path

- Owner machine: **ISM-SKY-004** (precipitation population, cloud-origin gating, lightning bucket) — it records
  presence/gating only (32 drops, 0.16 gate, bucket), no intensity, slant, wind or visual states. ISM-SKY-032
  (weather → driver projection) owns `rainOp`/`rainSlant`/`gust`. Admission/truth: ISM-WX-001/002; easing:
  R002F-A1 candidate (issue 96).
- Tests pin presence and gating only: `tests/r0024-particle-origin.test.cjs`, `tests/weather-effects-contract.test.cjs`
  (0.16 gate, permission, withdrawal, strike bucket). No test pins counts, speeds, slant or opacity mapping, so the
  levers below need no accepted-test amendment except where they change the gate semantics (L3) or the
  drop pool (`r0024` reads `.drop` nodes).
- Truth path: `gateWeatherCode` (L2821) requires ≥ 0.05 mm (thunder ≥ 0.8) for the model category →
  `visualPermissions.rain` → `data-precip` (L~3517). The widget itself already converts the interval amount to a
  rate using the provider interval (`averageRateMmH = p·3600/interval`, L1894; header says "4.8 mm/h interval
  average" for 1.2 mm). `rainOp` does not use that rate.
- **No-evidence case (survey claim 2, confirmed):** data-path code 63 with 0 mm → `visualPermissions.rain=false`,
  `data-precip=off`, but `renderCode 63`, `data-fx=rain`, header "Rain — Open-Meteo current model estimate … →
  overcast", rain veil/tint/accent unchanged (horizon L* 64.58 vs 64.64 with 1.2 mm). SIM `simWx=63&simPrecip=0`
  downgrades fully to `clear`. Under the PR42 labelled-model policy this is permitted (no particles = no claim of
  falling rain), so it is not classed as a defect here; it is a coherence and consistency question for the owner.

## Part B — measurements

### B1 Uniformity, structure, periodicity (baseline, all intensities and times)

| Metric | Baseline range | Meaning |
|---|---|---|
| distinct crossing positions at y=160 over 10 s (2 px bins) | 32–38 of 500–590 crossings (drizzle 11) | fixed tracks: every streak re-falls in its column |
| spatial CV of tile density (8x12) | 0.42–0.58 | moderate, but static |
| field density CV over time | 0.04–0.14 | near-constant amount of rain |
| power below 0.5 Hz (tile series) | 0.002–0.04 | no gust, sheet or band structure; energy sits at 1.1–1.7 Hz (loop rates) |
| repeat (mask correlation, lag ≥ 0.4 s) | 0.37–0.41 at 4.2 s | visible quasi-loop (7 × 0.6 s = 5 × 0.84 s) |
| wind 0 / 5 / 10 / 20 m/s | lean 0 / 16.9 / 32.5 / 42.3° for every class | drizzle leans like a downpour |
| gust 8.5 vs 22 m/s | identical | gust unused |

Firefox and WebKit reproduce the mapping (heavy noon windy: n 32, 16.5 px, 187.5 px/s, lean 32.5°, repeat
correlation 0.19–0.26 at shorter clips). Real-time headed clips (Chromium, Firefox) and headless WebKit show the same
fixed-column loop (`anim/precip-realtime-headed-heavy-windy.webp`, last 6 s of a 10 s wall-clock watch).

### B2 Pairwise distinguishability (noon, calm)

Cue counted when it exceeds a stated threshold: count ≥ 20 %, speed ≥ 10 %, length ≥ 15 %, streak opacity ≥ 20 %,
horizon ΔL* ≥ 2. These thresholds are working assumptions from recalled Weber fractions (UNVERIFIED), not fetched.

| Pair | Now: cues | Combined levers: cues |
|---|---|---|
| light vs moderate | **none** (opacity 15 %) | count, speed, length |
| light vs heavy | opacity only | count, speed, length, opacity, horizon |
| moderate vs heavy | opacity only | count, speed, length |
| heavy vs storm | **none** | none (rain rates 16 vs 12 mm/h; storm identity must come from deck/lightning) |
| light vs scattered (1.6 vs 2 mm/h) | horizon (different cloud cover, not rain) | none — L3 did not localise shafts (B4) |

The survey's sim-path result (1, 2.5, 6, 20 mm indistinguishable apart from opacity, saturating at ~6 mm) is
consistent with these data-path numbers.

### B3 Physical expectations (fetched sources unless marked)

- Drop size distribution: Marshall–Palmer N(D) = N0·e^(−ΛD), N0 = 8000 m⁻³ mm⁻¹, Λ = 4.1·R^−0.21 mm⁻¹
  (fetched: Wikipedia "Raindrop size distribution"). Median-volume D0 = 3.67/Λ (standard, recalled, UNVERIFIED):
  1.6 mm/h → 0.98 mm; 4.8 → 1.2; 16 → 1.6; 32 → 1.7.
- Terminal velocity v(D) = 9.65 − 10.3·e^(−0.6·D) m/s, D in mm (fetched: CloudMicrophysics.jl docs, Seifert &
  Beheng 2006 constants; search result attributes the fit to Atlas et al. 1973 and notes poorer accuracy for small
  drops). Light 3.9 m/s, moderate 4.6, heavy 5.7, violent 6.0; drizzle (D < 0.5 mm, fetched: WMO Cloud Atlas
  "drizzle" — drops "appear almost to float") ≈ 1.2 m/s.
- Fall-streak lean: tan θ = u/v (kinematics). With the same 10 m/s across-view wind: drizzle ≈ 83°, light 69°,
  heavy 60°. **Current mapping is flat (32.5° for all) and therefore backwards relative to physics for drizzle vs
  downpour.**
- Optical extinction by rain: γ = k·R^α dB/km, wavelength-independent in the optical windows; μ = 1: k = 1.1394,
  α = 0.7057 (fetched: Korai, Luini, Nebuloni 2018, *Electronics* 7, 407, Table 1). σ = γ/4.343 km⁻¹; Koschmieder
  visibility 3.912/σ (recalled, UNVERIFIED): 1.6 mm/h ≈ 10 km, 4.8 ≈ 4.6 km, 16 ≈ 2.0 km, 32 ≈ 1.2 km.
  **Current presentation: no rate-dependent visibility change at all.**
- Intensity classes: AMS light ≤ 2.5 mm/h, moderate 2.6–7.6, heavy > 7.6 (search result quoting the AMS glossary;
  page itself not fetched — partly verified). Drizzle intensity 0.3 / 0.5 mm/h breakpoints (search result, UNVERIFIED).
- Open-Meteo current `precipitation` as a preceding-15-min amount: UNVERIFIED externally (docs not fetched to avoid
  provider contact); the widget's own code treats it so (L1894). The evaluation uses the same ×4.
- Rain shafts / sheets seen at distance as grey curtains that reduce contrast toward the horizon: consistent with
  the extinction numbers above; no image source fetched (UNVERIFIED as an appearance claim).

## Part C — levers (evaluation overlay only)

All levers read only inputs the widget already admits: `data-precip`/`data-fx` (permission), `selectedWeather()`
amount, wind, direction, gust, the cloud column profile `_colDens`, cloud tint, `--g3`. None touches
`real-sky/core/**`, the refined-frame identity key or the truth gate. The overlay draws only when the widget
published `data-precip="on"`; intensity never exceeds the record. A control (overlay, all levers off) reproduces the
current DOM rain within measurement noise (n 31.5 vs 32, speed 187.5, lean 32.6° vs 32.5°, repeat 0.40 vs 0.41).
Overlay cost: 0.23 ms per frame (Chromium, 300-frame mean). Healthy non-rain scenes are untouched (overlay
returns early; production equivalent keyed on the same permission).

| Lever | What it changes | Physical basis | Before → after (moderate, noon, 10 m/s unless noted) | Honest visual verdict |
|---|---|---|---|---|
| L1 intensity | count within the existing 32 budget, length, speed, width, alpha from R; drizzle as faint short slow drops; streak colour adapts to sky brightness | MP D0, v(D) | speed 187.5 → 213 px/s (heavy 262, light 120 in combo); length 16.5 → 19.4; visible 32 → 21; distinguishable pairs 0/3 → 3/3 | **Physical: better. Experiential: clearly better differentiation; light rain at noon becomes barely visible (truthful but may read as "not raining").** |
| L2 slant | lean = u/v per intensity, oriented streaks (fixes the vertical-stick defect), cap 50° | kinematics | 32.5° vertical sticks → 50° oriented streaks (both signs) | Physical: better. Experiential: better; at the cap all intensities ≥ 8 m/s lean alike. **Sign (map vs cloud convention) is the owner's open decision**: map sign leans right while clouds drift left for a west wind; cloud sign leans with the drift. Both shown in `anim/precip-moderate-windy-noon-sign.webp`; the cloud sign reads as one wind. |
| L3 structure | per-cycle re-seeded positions, advecting fbm sheets (5 px/s per m/s), gust envelope | intermittency (qualitative) | distinct tracks 38 → 158; low-freq power 0.005 → 0.18; field CV 0.10 → 0.22; repeat 0.41 → 0.045 | Physical: plausible. Experiential: **removes the canned loop and fixed comb — the largest single fix for "uniform overlay"**. Shower shafts NOT achieved: with 40 % cover the column profile is broad, spatial CV did not rise (0.52 → 0.37 combo). Gust coupling weak (gust 22 vs 8.5: no consistent difference) — needs redesign. |
| L4 atmosphere | rate-dependent horizon veil (σ(R), 3 km), sun body/corona glare × e^(−1.6σ), deck brightness 1 → down to 0.68 (32 mm/h), blurred curtains under dense columns | Korai et al. extinction | horizon L* 64.9 → 56.7 (heavy 56.4, light 59.3); horizon σL 12.6 → 11.5; sun p99.5 L* 95.0 → 93.5; dusk: ≈ no change | Physical: better (first rate-dependent visibility response). Experiential: **most of the perceived "integration" comes from this lever**; at dusk/night it is nearly invisible (correct: dark curtain on dark sky). Risk: overlaps the R003E aerosol research and the sun-radiance issue (survey finding 2); first curtain draft showed hatching (fixed by blur) — artifacts must be judged at 1x. |
| L5 depth | 55 % far streaks (shorter, slower, fainter) | parallax | length p50 21 → 13.8; opacity 0.44 → 0.24 | Physical: neutral. Experiential: **marginal, reads mostly as "less rain"**; not recommended now. |
| Combined | all five | — | see B2; repeat 0.02–0.05; tracks 95–196 per 10 s | Physical: better on every relation measured. Experiential: more coherent and differentiated, but streak opacity p50 0.15–0.24 (now 0.36–0.66) makes rain at glance scale **too faint**; a tuning floor is needed. Three engines agree (heavy windy: Chromium/Firefox/WebKit lean 50.2°, tracks 196/166/170, horizon L* 56.4/56.3/56.0). |

Reduced motion: the overlay draws a frozen frame at its normal alpha (no comb); `sheets/precip-reduced-motion-now-vs-overlay.webp`.
Determinism: `frame(t)` is a pure function of `t` and the admitted inputs (seeded hash, no `Math.random`), so
`simTime`/mocked-clock runs reproduce exactly; no reseed on weather refresh (seed depends on drop index and cycle).

Composition with R002F-A1 (branch `claude/r002f-a1-eased-weather-transition-20261115`, local): A1 moves the
presentation selectors to `data-wxp`/`data-wxprecip` and a single weight `--wxw` eased over 1.5 s. Every lever
above should key on `data-wxprecip` and multiply its alphas (streaks, veil, curtains, glare and deck deltas) by
`--wxw`, so fading in/out on evidence change stays A1's single owner; the truth instant remains `data-precip`.
Nothing here duplicates A1. R0032 (radar off): no interaction (levers never read radar). R003C (cloud lining) and
R003D (dithering): L4 deck darkening and curtains sit on/under the cloud canvas — sequence after R003C, dither
the veil per R003D. R003E (aerosol/visibility): L4's extinction term must be reconciled with R003E's visibility
mapping so rain and haze do not double-count when a provider `vis` already reflects rain.

## Part D — disposition draft (not filed)

| Owner concern | Classification | Evidence |
|---|---|---|
| Heavy, light and scattered not differentiated | **DEMONSTRATED DEFECT** vs gate H ("vary by weather type/intensity"): count, length, speed, slant identical for all intensities; light vs moderate and heavy vs storm differ by no cue above threshold; drizzle/thunder speed rules are dead CSS | A1 table, B2 |
| Density/spacing too uniform | **DEMONSTRATED** (fixed 32 columns, 4.2 s quasi-loop) and **MEASURED SHORTFALL** vs the design standard ("alive rather than assembled") | B1 |
| No gust structure, sheeting, stochastic variation | **MEASURED SHORTFALL** (low-frequency power ≤ 0.04; gust received and unused — a demonstrated dropped input) | B1 |
| No effect on attenuation/visibility/scattering | **MEASURED SHORTFALL** (horizon L* and contrast identical light → violent; sun body ignores cloud/rain) — physically backwards per Korai et al. | A2, B3 |
| Clouds, tint, glare, precipitation not one environment | **MEASURED SHORTFALL** plus **UNVERIFIED HYPOTHESIS** that L4 + deck coverage fix it; concrete defects: streaks vertical while moving diagonally; rain leans opposite to cloud drift (issue 124); reduced-motion comb at opacity 1; Moon fully visible in heavy rain | A1, A2 |

Additional demonstrated defects found here (not in the survey): (a) streak orientation does not follow its motion
(translate-only keyframe); (b) dead CSS for drizzle/thunder speed and drizzle opacity; (c) reduced-motion freezes
32 full-opacity streaks in a row; (d) `rainOp` uses raw interval mm while the widget's own label uses mm/h.

**Recommended partition:** one bounded precipitation work order ("precipitation presentation fidelity", owner:
ISM-SKY-004 + the `rainOp`/`rainSlant`/`gust` projection in ISM-SKY-032), in two slices:
1. *Slice P1 (smallest, highest value):* L3 positions/structure + L1 intensity + L2 orientation (sign held at the
   current convention until the owner decides issue-124 question 1) + reduced-motion fix + dead-CSS removal. One
   precipitation layer (a small canvas or per-drop CSS variables), budget ≤ 32 streaks, keyed on A1's
   `data-wxprecip`/`--wxw`.
2. *Slice P2:* L4 atmosphere coupling, sequenced after R002F-A1 and reconciled with R003E (visibility) and the
   sun-radiance finding (survey finding 2; separate owner decision). L5 not recommended.
Owner decisions required: slant sign convention; whether the no-evidence data path keeps the rain veil/tint;
L4 strength at the horizon.

Tests needing reasoned amendment: `tests/r0024-particle-origin.test.cjs` and `tests/weather-effects-contract.test.cjs`
if the binary 0.16 gate becomes a soft weight or the pool leaves the DOM; ISM-SKY-004 entry (states for intensity,
structure, reduced motion). New assertions: monotonic speed/length/visible count in R; lean = f(wind/v) monotonic
with drizzle ≥ rain; no fixed track over 10 s; repeat correlation < 0.1; zero streaks and zero veil without
`visualPermissions.rain`; reduced motion static and alpha-bounded; non-rain scenes pixel-identical.

Acceptance evidence for a real implementation: native clips in Chromium, Firefox and WebKit (stepped metrics +
real-time watch, headed in at least one engine) for light/moderate/heavy/scattered/storm x noon/dusk/night x calm/
windy, with the A1 transitions (rain on/off, intensity change, evidence expiry); separate physical and experiential
verdicts from a visual judge; owner approval.

**Do not:** add particles beyond the 32 budget; add splashes, lens drops or puddles; touch `real-sky/core/**`;
add weather fields to the refined-frame identity; let streaks or veil appear without `visualPermissions.rain`;
imply intensity beyond the record; decide the slant sign or winds aloft in implementation; ship L5.

## Limits

- The overlay is a research prototype: tuned briefly, streak alpha too low in the combined variant, shower shafts
  and gust coupling not achieved, curtains quantised at 13 px (blurred). Numbers compare renderers, not truth.
- Thresholds in B2 are recalled, not fetched. Several physical statements are marked UNVERIFIED above.
- Firefox/WebKit cover 2 cells (stepped) and 1 (real-time); WebKit crashed once and was re-run. Real-time clips are
  VP8 video (lossy) and were judged visually, not measured.
- Snow measured only as the existing flake layer (no lever applied). Thunder on the data path never shows lightning
  (by policy); storm-with-lightning measured only on the sim path.
- Bulk frames are outside the repository and were pruned after analysis.

## Files

- `anim/` — before/after animations (stepped, 5 s, 15 fps, sky band y 40–300): light, heavy, scattered, storm-dusk,
  moderate windy with both slant signs, intensities now vs combined, gust ignored now, real-time headed heavy windy.
- `sheets/` — contact sheets: intensity x noon and dusk now, wind now, each lever on moderate windy; reduced-motion.
- `metrics/` — per-clip metrics (geometry, tiles, spectrum, repeat, scene).
- Recipes: `node tools/qa/precip_eval_capture.cjs --pw <pw> --root . --out <bulk> --only <regex> --variant
  base|ctrl|L1|L2|L2c|L3|L4|L5|combo|comboc [--engine firefox|webkit] [--mode realtime --headed 1] [--reduced 1]`;
  `python tools/qa/precip_eval_report.py analyze|sheet|webp|prune --bulk <bulk> ...`.
