# Precipitation models M1–M5 — native real-time prototype comparison (2026-11-16)

Controlled research and prototype comparison only. No product file changed; nothing pushed; **no model is
recommended for adoption**. The models are a browser-injected evaluation overlay (`tools/qa/precip_models.js`,
geometry in `tools/qa/precip_models_geom.js`) on the generated widget at `a196351b` (merged into this branch).
Inputs: the precipitation model advisory, its independent physics verification, the owner's visual finding and
direction of 2026-11-15 (all held outside the repository). Demonstrated defects of the earlier investigation
(`../README.md`) stand.

**Network.** Every browser launch went through `tools/qa/precip_eval_lib.cjs`: the catch-all route is installed on
the context before any page exists, only loopback is continued, every request is counted and logged, and the run
exits 2 on any non-loopback continuation. Result over all 105 retained scene records: **0 non-loopback requests continued**; 11–12 requests per scene, all
stubbed (Aladhan, Open-Meteo) or aborted (fonts.googleapis.com only).

## 1. Declared depiction convention and parameters (PROVISIONAL)

At this card's field of view almost no raindrop is resolvable; physically faithful rain is nearly invisible. The
prototypes therefore take ONE disclosed depiction convention, identical for every regime:

| Constant | Value | Status |
|---|---|---|
| Camera | rectilinear, f = 265 px, az/alt from `skyAz`/`skyAlt` (default 180°/45°), 13.0′/px at centre, 5.5–6.5′ at edges | verified (projection.mjs) |
| Exposure T | 1/60 s (= display frame interval; high-visibility end). Variant: 1/15 s | declared, model-dependent |
| Contrast gain G | 100 on the physical streak contrast 4·f·a²/(z·v·T)·(L_env − L_b). Variant: 400 | declared depiction licence |
| Near shell (M1, M3, M4) | 0.5–1.0 m, D ≥ 0.3 mm | declared |
| Large-drop tail (M2, M5) | 0.7–1.5 m, D ≥ 1.5 mm, ≤ 300 drawn | declared |
| Mid texture (M2, M5) | 1.5 m to the depth where a streak is still ≥ 3 px; D ≥ 0.3 mm; ≤ 9000 strokes per tile (alpha rescaled to keep the mean) | declared |
| Band frustum | V = 0.355·(z₂³ − z₁³) m³ for rows 8–300 | derived |
| Terminal velocity | Atlas 9.65 − 10.3·e^(−0.6D) for D ≥ 0.5 mm; Gunn–Kinzer table (recalled) below | verified ≥ 0.5 mm; recalled below |
| Image motion | parallel layout: v·cos(e_row) + u_f·sin(e_row) (foreshortened per row); perspective: full rectilinear projection (fan from the radiant) | verified geometry |
| Wind at drop height | 0.8 × 10 m wind (1/7 law) | recalled |
| Gust | σ_u = (gust − wind)/3, seeded value noise, 8 s scale, coherent across view, each drop lags v/g | recalled peak factor |
| Extinction (veil) | σ = π·N0/Λ³ (= 0.365·R^0.63 for Marshall–Palmer), alpha = 1 − e^(−σ·H/sin e) toward the drop environment | verified (MP) |
| Rate | product's own conversion: interval amount × 3600/900 | product convention |

Regime-dependent DECLARED parameters (the physics alone does not fix these):

| Regime | Fixture amount → rate | DSD family | Cloud base H (from dew-point spread × 125 m) | Structure field (M3/M5) |
|---|---|---|---|---|
| Drizzle (53) | 0.08 mm → 0.32 mm/h | drizzle exponential N0 30 000, Λ 5.7R^−0.21 (recalled, unverified) | 104 m | uniform (amp 0.05) |
| Light (61) | 0.3 mm → 1.2 mm/h | Marshall–Palmer | 347 m | amp 0.1, 8 s |
| Moderate (63) | 1.25 mm → 5 mm/h | Marshall–Palmer | 347 m | amp 0.2, 8 s |
| Heavy (65) | 3 mm → 12 mm/h (class interior) | Marshall–Palmer | 312 m | amp 0.45 + travelling sheets 2.5 s |
| Scattered showers (81, 45 % cover) | 0.75 mm → 3 mm/h cell mean | convective N0 1400, Λ 3.0R^−0.21 (recalled, unverified) | 1007 m | shafts at deck-cluster peaks, 1.5 km path |

Drizzle extinction is not modelled (the provider visibility of 3 km reaches the product's own aerosol path; the
overlay adds no drizzle veil, so nothing is counted twice). All numbers live in one object `P` at the top of
`precip_models.js`; `window.__PM_PARAMS` overrides them. The regime ratios that result (for example N(>2 mm)
light : moderate : heavy) are a declared range of 7–230 depending on rates and DSD, not a constant.

## 2. The models as built

- **M1 — DSD near-streak field (control).** Streaks sampled from the DSD in the near shell; length, width, alpha,
  lean per drop from D, z and the wind; colour = the drop's environment (blurred composed sky + deck, with Sun and
  eligible-Moon kernels), so contrast follows L_env − L_b and nothing glows without a lit source.
- **M2 — depth-layered volume.** Large-drop near tail + two DSD-generated mid-depth texture tiles scrolled with
  parallax (re-seeded lateral offset at each wrap) + far veil from σ(R) to the cloud base; Sun body dimmed by the
  same transmission (the disc stays sharp).
- **M3 — structure-first.** A rate field ρ(x, t) with mean 1 (rate conserved), bound to the deck: no rain without
  cloud above; showers as shafts at the column-density peaks of the deck, travelling with it and trailing ~12°
  against the drift; heavy rain with travelling sheets; streak spawn and local veil follow ρ.
- **M4 — scene response first.** Veil and Sun dimming as M2, soft fall-streak fibres hanging from each column's own
  cloud base (deck-lit), only 15 % of the M1 streak population.
- **M5 — hybrid.** M3's field modulating M2's layers, plus M4's fibres.

## 3. What I saw (own viewing of native-size real-time clips; model judges, not humans)

Daylight (noon, overcast deck), per regime:

| Model | Drizzle | Light | Moderate | Heavy | Showers | Aesthetic / plausibility note |
|---|---|---|---|---|---|---|
| current product | 11 pale ticks | 32 vertical ticks | same | same | same | uniform canned ticks; same in every regime |
| M1 | nothing | a few faint ticks | faint fleeting streaks | short fast streaks, sparse | sparse long streaks | truthful but **nearly invisible**: env ≈ background against a bright overcast. FAILS legibility by day at G = 100 |
| M2 | nothing | very faint texture | fine oriented texture + softened deck | **dense oriented texture, deck loses structure — reads as heavy rain** | uniform texture (no localisation) | the most rain-like by day; at G = 400 the tile boundary of the texture became visible as a lighter rectangle (artifact) |
| M3 | nothing | faint | veil + faint streaks | veil + moving sheets | shafts not legible at native size | shafts as built read as faint grey smears; **showers-as-shafts FAILED** at this cover |
| M4 | nothing | veil barely | veil | veil + fibres under the base | fibres | fibres read as grey vertical smudges/barcode under the deck — **artificial**; motion minimal |
| M5 | nothing | faint | texture + veil | texture + veil + fibres | texture + fibres | inherits M2's legibility and M4's artificial fibres |

Twilight (blue hour): every model's streaks are near-invisible (environment-coloured on a darker sky); the product's
pale luminous streaks are the only visible particles and they are an invented light. Veil models soften the deck
slightly. Moonlit night: faint grey streak texture near the Moon in M2/M3 (the Moon kernel), nothing elsewhere —
truthful, low legibility. Moonless night: no model shows rain (truthful; physically not available without light);
the product shows luminous streaks (invented light). **Night regime discrimination by particles FAILED for all
models, as the physics predicts**; only the label carries it.

Drizzle: invisible in every model at G = 100 and G = 400 (drops < 0.5 mm, 2–3 px, contrast ~10× below light rain).
A separate declared stipple convention would be needed (verifier); not built — **drizzle FAILED for all models**.

Light vs moderate: separable only in M2 (texture density) and only with attention; light rain is near-invisible in
all models, consistent with the verifier's 76–80 % deck-detail retention. Heavy is clearly separable in M2/M5.

Integration time 1/15 s (variant `~67`): streaks longer but fainter, as the 1/T law predicts; less legible than
1/60 s. Gain 400 (variant `^400`, still one global constant): M1 light/moderate ticks appear; M2 light/moderate
become textured; drizzle still nothing; M2 tile artifact visible.

Parallel versus perspective (fanning) projection: at G = 100 by day the difference was **not perceptible** to me in
the moderate 8 m/s cell; streaks are too faint to show the fan. Both are kept (`frame-moderate-w8`).

## 4. Direction: wind × camera

`tests/precip-eval-direction.test.cjs` asserts the verifier's table against the shared geometry module (6 tests,
pass): at az 180 a W wind leans the lower end LEFT (≈ 60.5° at centre for 1 mm drops at 5 m/s), E wind RIGHT, N wind
(away) no lean and 2.2× faster flow, S wind (toward) no lean and rising flow when S > v_t·cot e; at az 90 the table
rotates (N → right, S → left, W away, E toward); a 180° wind rotation flips the lean at every azimuth; calm air
fans from the top-centre edge (≈ 31° at ±100 px).

Clips `orientation/orient-moderate-{w8,e8,n8,s8}-az{180,90}--compare.webp` (product, M1 parallel, M1 perspective,
M2). Overlay rain follows the geometry in all eight. **Agreement with the product's clouds holds only at az 180**:
the product's cloud drift uses `windX = −sin θ` with no camera azimuth (asserted as a documented fact in the test),
so at `skyAz=90` the deck drifts left for a W wind while the rain correctly has no lateral component, and the
clouds do not drift for N/S winds while the rain leans. The rain cannot agree with a cloud drift that is not
projected; this is a cloud-motion (issue 124 / ISM-SKY-003) finding, not a rain choice. The product's own rain
slant is opposite to its cloud drift at every azimuth (confirmed again). A measured cloud-drift probe from the
deck's column profile was too coarse to use as evidence (inconsistent signs at a few px/s) and is not cited.

## 5. Expiry: immediate withdrawal (a) versus bounded in-flight completion (b) — candidate policy, not chosen

Clips `expiry/expiry-{moderate,heavy}-{current,M1-immediate,M1-complete,M2-immediate,M2-complete,M5-complete}.webp`:
the provider stub fails after the first record, the clock is set to 3 s before the quarter-hour boundary, 12 s
real time. On `main` the product withdraws at the boundary (+0.2 s sample: `data-precip off`, `fx unavailable`):
deck, tint, particles and header go together; there is no atmospheric hold on main (R002F-A2 is not merged), so
the clips isolate the particle policy only.

(b) as built: no drop is emitted after the withdrawal frame (a drop whose cycle starts after it is never drawn);
already-emitted drops keep the inputs frozen at the last eligible frame and are clipped by an emission front that
moves down at each layer's own screen speed; veil, shafts and fibres (state-bearing) stop at once; nothing renews
intensity, emission, claims or evidence. Maximum visible time after expiry:

| Layer | Derivation | Bound |
|---|---|---|
| Near streaks (M1/M3/M4) as implemented | each drawn drop lives one 180 ms cycle | 0.18 s (measured: 0 drawn by the +0.5 s sample) |
| Near streaks, physical | band 292 px / (f·v(0.3 mm)/1.0 m) | 0.94 s |
| Large-drop tail (M2/M5) | 292 / (f·v(1.5 mm)/1.5 m) | 0.30 s |
| Mid texture (M2/M5) | 292 / (f·v(D_ref)/5.2 m), D_ref = max(0.6, D0) | drizzle 2.3 s, light 1.5 s, moderate 1.2 s, heavy 1.1 s, showers 1.1 s |

Reconciliation: issue 96's hard constraint says an expired record "must not drive the header, clouds, particles or
optics for a single frame" and rejects any grace or fade-out. Policy (b) shows particles from an expired record
for up to ~1–2 s, so it **contradicts that constraint as written**; adopting it would need an explicit owner
amendment and independent review under R002F's owner (it does not follow from any atmospheric-hold decision).
Policy (a) is what the constraint requires. Visual consequence observed: (a) the near streaks vanish in one
frame (with the deck on main); (b) the near layer empties within a fraction of a second and the M2 texture drains
downward for ~1 s — at native size the difference is small next to the deck's own withdrawal on main.

## 6. Evidence semantics: rain category with amount UNAVAILABLE (presentation prototype only)

Fixture: code 63, `precipitation: null`. Today (live lane): `renderCode 63`, `data-fx=rain` (rain veil/tint/deck),
icon 🌧️, title "Rain — Open-Meteo current model estimate … quantitative effect decision: rain model code but
interval precip unavailable → overcast", particles off. The SIM lane cannot express "unavailable" (an unset
`simPrecip` becomes a code default).

Treatments (clips `evidence-semantics/evidence-unavailable--compare.webp`: product today, then M1/M2/M4 drawn at
a category-only minimum rate):

| Treatment | Label (icon `title`/`aria-label`; no layout change — the visible header stays icon + temperature) | Look | Particles | Assessment |
|---|---|---|---|---|
| T-A | "Model estimate: rain — amount unavailable; not observed" | rain category look as today | none | consistent with the owner's ruling; keeps the category, claims no amount |
| T-B | same label | cloud cover as admitted, no rain veil/tint | none | also consistent; the look no longer implies a rate; must not read as "dry" (icon stays rain) |
| T-C | same label + "depiction not quantified" in the hidden text | as T-A | drawn at 0.1 mm/h | **an unsupported rate**: any number is invented; at 0.1 mm/h it is also invisible in M1/M2/M4 by day, so it buys nothing. Not defensible as quantitative; shown for judgement only |

Truth table (category × amount × observation; live and SIM):

| Category | Amount | Observation | Live today | SIM today | T-A | T-B | T-C |
|---|---|---|---|---|---|---|---|
| precipitation | positive | none | label Rain (model est.), rain look, particles at rate | Rain, particles (preview) | unchanged | unchanged | unchanged |
| precipitation | zero | none | label Rain + "→ overcast" note, rain look, no particles | downgraded to cover class (e.g. Clear) — label and look | label "model category rain, no measurable amount", rain look, no particles | cover look, no particles | as T-B (no particles: amount is known zero) |
| precipitation | unavailable | none | as zero (collapsed), "unavailable" only in the note | not expressible | label "amount unavailable", rain look, no particles | "amount unavailable", cover look, no particles | rain look, minimum-rate particles |
| non-precip | positive / zero / unavailable | none | code's condition, no particles | code's condition | unchanged; "amount unavailable" kept as `unknown`, never `dry` | same | same |
| any | any | supported wet / dry (fixture lane) | per present evidence | per present evidence | unchanged | unchanged | unchanged |

The live/SIM inconsistency (SIM turns a zero or default amount into a dry "Clear") is not resolved by any
treatment above; reconciling it is a product decision for the owner (ISM-WX-002).

## 7. Readability, geometry, performance, reduced motion

- Geometry: card, header, footer, every prayer row and the rows' `backdrop-filter` are byte-identical (DOM boxes)
  with every model in every scene; the overlay canvas is a child of `#wxfx` only.
- Text contrast (luminance ratio inside each text box, comparative): prayer rows unchanged (min 1.11 day, 1.17–1.30
  night — the faded elapsed row, independent of rain). Clock/title band minimum by day: product 1.73; M1 1.74–1.75;
  M2/M3/M5 1.64–1.70 in rain and 1.56–1.61 in showers (veil and texture behind the clock); twilight and night
  slightly higher than the product (no luminous streaks). See `models-summary.json`.
- Frame cost (median ms/frame over 120 frames, this host, mocked clock with 1 ms granularity): M1 0.33, M2 3.8,
  M3 2.0, M4 1.4, M5 5.8 (max 7.1). 4× CPU throttle (Chromium `Emulation.setCPUThrottlingRate`, first-pass builds):
  M1 2.4–3.4, M2 18–32, M3 9–11 and M5 23–28 (before the soft-layer change). Real-time capture (CDP screencast,
  compositor timestamps, per clip in `models-summary.json`): product 48–60 fps; M1/M2 49–58; M3/M4 51–58; M5 41–55.
  A first M4/M5 build with a canvas blur filter fell to **7–13 fps** in real time (failed implementation, replaced
  by a quarter-resolution soft layer; those clips are superseded). M2/M5 exceed the advisory's ≤ 1 ms budget.
- Reduced motion (`reduced/`): the product freezes 32 full-opacity streaks in a row (the known comb); every model
  draws one frozen frame at its normal alpha.

## 8. Blind recognition pack

`blind-pack/` (outside the repository, in the owner's plans folder): 90 unlabelled 3 s native-size clips
(6 presentations × 5 regimes × 3 conditions: calm, 8 m/s steady, 8 m/s gusty; all daylight), random names. The key
is in a separate folder (`models-blind-KEY-do-not-give-to-judges/key.json`). Not yet judged.

## 9. Failed prototypes and conflicting evidence (recorded openly)

- Drizzle: invisible in every model (needs a separately declared stipple convention).
- Night without a lit source: no model can show rain truthfully; with the Moon only faint local texture.
- M1 by day at G = 100: nearly invisible; legible only with G = 400 (still a single global constant, but a stronger
  licence).
- M3 showers as shafts: not legible at native size at 45 % cover; M2's showers are uniform.
- M4/M5 fibres: read as artificial grey smudges; first build too slow (7–13 fps).
- M2 at G = 400: visible texture-tile boundary.
- Light versus moderate: weakly separable at best; heavy versus storm: not separable by rain at all.
- Conflict: physically faithful depiction (M1) and legible depiction (M2 texture/veil) pull apart by day; the veil is
  physically supported for heavy rain only (verifier).

## 10. Open questions for the owner

Depiction licence (G, T) — one global constant, chosen from clips; whether drizzle may have a declared stipple;
the night target (label only?); projection frame for weather (only matters once streaks are legible); whether the
product's cloud drift should become camera-aware (issue 124) so rain and clouds can agree at any `skyAz`; expiry
policy (a) or an amendment for (b); unavailable-amount treatment T-A or T-B.

## Reproduce

```text
node tools/qa/precip_models_capture.cjs --pw <playwright> --root . --out <bulk> --only <regex> --secs 4 [--throttle 1] [--models M3,M4,M5]
python tools/qa/precip_models_post.py --bulk <bulk> --anim <dir> --out <summary.json> [--blind <dir> --key <file>]
node --test tests/precip-eval-direction.test.cjs
```
