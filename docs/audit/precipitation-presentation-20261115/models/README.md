# Precipitation models M1–M5 — native real-time prototype comparison (revision 2, 2026-11-16)

Controlled research and prototype comparison only. No product file changed; nothing pushed; **no renderer is
selected and none is recommended for adoption.** The models are a browser-injected evaluation overlay
(`tools/qa/precip_models.js`; geometry `tools/qa/precip_models_geom.js`) on the generated widget at `a196351b`
(no precipitation code differs at main `47faae32`). Revision 2 follows the independent review of the prototypes
(two blocking findings, nine advisory) and the owner's prototype feedback and clarification of 2026-11-16. Superseded
statements of revision 1 are corrected in place; the revision-1 record is in git history.

**Human perception.** No human test has been run. Every appearance statement below is either the author's own
viewing of native-size real-time clips (a model looking at frames, not a person watching motion) or a frame
metric. Neither is human visual perception, and neither may be reported as such.

**Network.** Every browser launch went through `tools/qa/precip_eval_lib.cjs` (catch-all route on the context
before any page, only loopback continued, every request logged, exit 2 on any escape). Revision-2 runs: 49 scene
records (Chromium, Firefox, WebKit), **0 non-loopback requests continued**; aborted host only fonts.googleapis.com;
provider requests stubbed (Aladhan, Open-Meteo). Revision-1 runs: 105 records, 0.

## 1. Evidence index (owner folder `plans/precipitation-evidence/models/`, untracked)

| Folder | What | Status |
|---|---|---|
| `blind-pack/` | 90-clip pack of revision 1 | **INVALID as a recognition test** (scene fixtures differ per regime); preserved unmodified with `LIMITATION.md` |
| `blind-pack-controlled/` | 144 clips, 4 blocks with one held scene each × 6 conditions (incl. no-rain control) × 6 presentations; key in a separate folder | ready for a human test; **not run** |
| `HUMAN-TEST-PROTOCOL.md` | recognition and naturalness questions, scoring, thresholds | protocol only |
| `controlled/` | per block and condition: product, M1–M5 side by side (real time) | revision 2 |
| `conventions/` | M1 with shell 0.5–1 / 1–3 / 3–10 m × gain 25 / 50 / 100 / 400, moderate and heavy | revision 2 |
| `layers/` | M2 and each of its layers alone (veil, texture, near streaks) | revision 2 |
| `expiry-v2/` | immediate withdrawal vs in-flight completion, claim-withdrawal frame marked | revision 2; supersedes `expiry/` |
| `cross-engine/` | Firefox and WebKit, day / twilight / moonlit night | revision 2 |
| `compare/`, `strips/`, `orientation/`, `reduced/`, `evidence-semantics/` | revision-1 sets; `compare/day-moderate-w8` regenerated (was 0 bytes) | revision 1 (+ fix) |

## 2. Parameter integrity — every non-derived value, with derivation and proposed class

Classes: **P** physically justified (derived or sourced), **C** perceptual convention (declared depiction licence; not
physics), **U** unsupported effect (adds or shapes appearance without a physical basis). Proposed by the author;
to be assessed independently. All values live in the object `P` in `precip_models.js` (overridable by
`window.__PM_PARAMS`).

| # | Parameter | Value | Derivation / evidence | Proposed class |
|---|---|---|---|---|
| a | Rate per regime (fixture) | 0.32 / 1.2 / 5 / 12 / 3 mm/h | interval amount × 3600/900, the product's own conversion; light and moderate class interiors; heavy 12 chosen inside "heavy > 7.6 mm/h" (20 is the upper band); showers 3 is a cell MEAN | P (as test input; not a renderer parameter) |
| b | DSD families | Marshall–Palmer N0 8000, Λ 4.1R^−0.21; drizzle N0 30 000, Λ 5.7R^−0.21; convective N0 1400, Λ 3.0R^−0.21 | MP verified (stratiform average); the two Joss–Waldvogel-type families recalled, not verified | P for MP; P-unverified for drizzle/convective |
| c | Cloud base | 125 m per °C of dew-point spread, clamp 100–2000 m | standard lifting-condensation approximation (recalled); per-fixture 104–1007 m in revision 1, one value (347 m) in the controlled blocks | P-approximate |
| d | Drizzle extinction forced to 0 | `drizzleSigmaZero` | not derived: avoids counting drizzle twice when the provider visibility already feeds the product's aerosol path | C (accounting convention) |
| e | Structure-field amplitudes | 0.05 / 0.1 / 0.2 / 0.45, scales 8 / 3.5 s, heavy sheets 0.35 @ 2.5 s, thresholds 2.5 / 7.6 mm/h | chosen by hand; not derived from the DSD or any measured rain-field statistic; they are how M3/M5 separate regimes | **U** |
| f | M4 streak fraction; fibres | 0.15; 70 fibres, length log10(1+R)/1.7·60+10 px, width 2–5 px, colour × 0.8, alpha 1−e^(−σ·0.6 km) | no physical source; fibre geometry rate-independent except through σ | **U** |
| g1 | Sun kernel in the drop environment | 0.55·sunamt·(1−cloud²), gaussian σ 120 px | approximates the drop's ~30° refraction neighbourhood (~150 px) including the DOM Sun, which is not in the sky canvas; amplitude chosen | C (shape motivated, amplitude not derived) |
| g2 | **Moon kernel** | revision 1: 0.35·moonLit, σ 120 px (undeclared); revision 2: **0 (removed)** | revision 1 raised the moonlit band by +2.4 … +2.8 L* (review); magnitude not derived from forward scattering | **U** in revision 1; removed |
| h | Rendering licences | line width ≥ 1 px (+0.6), alpha cap 0.92, tile ≤ 9000 strokes with alpha × (count/cap), soft-layer upscale, rows 8–300 with fade 255–300, Sun dimming floor 3° | width floor keeps sub-pixel drops drawable; the alpha × coverage term (a² in the contrast) keeps energy, but the +0.6 px floor adds ~1.6–2× energy for sub-pixel streaks; tile rescale preserves the mean, not the variance | C, with the +0.6 px floor **U** |
| i | Showers veil | revision 1: σ(cell mean) over the whole view; revision 2: only where the M3/M5 field localises rain, none in M1/M2/M4 | a cell mean is not a local rate; revision 1 lifted horizon L* +1.2–1.5 and cut clock contrast 8 % (review) | revision 1 **U**; revision 2 P |
| S1 | Exposure T | 1/60 s (variant 1/15 s) | display frame interval; per-streak contrast ∝ 1/T, so 1/60 s is the high-visibility end | C |
| S2 | **Contrast gain G** | 100 (sweep 25–400) | the physical per-streak contrast 4·f·a²/(z·v·T) is 0.1–0.4 % of the environment–background difference; G multiplies it. This is a declared contrast enhancement, **not physics** | C — an explicit contrast enhancement; must never be presented as physical |
| S3 | **Near shell** | 0.5–1.0 m (sweep 1–3, 3–10 m) | chosen so that streaks are ≥ 1–3 px long and countable; distortions in section 3 | C |

## 3. The depiction conventions examined (owner item 3)

Physics at this card (f = 265 px, 13′/px at centre): a 1 mm drop at 1 m is 0.27 px wide and 3–4 px long per 1/60 s
frame after foreshortening; its contrast is 0.33 % of (L_env − L_b). A 0.3 mm drizzle drop at 1 m: 0.08 px wide,
2.4–3.7 px long, 0.12 %. Drops beyond ~3–10 m are sub-pixel in both directions.

Sweep (`conventions/`, M1, real time, same controlled scene; metrics from the encoded clips, 25 fps):

| Shell | Gain | Streak length p50 / p90 px | Drawn per frame | Changing-structure energy E (moderate / heavy; dry floor 0.22) |
|---|---|---|---|---|
| 0.5–1 m | 25 / 50 / 100 / 400 | 4.3 / 11.8 | 290 / 410 | 0.37–0.42 / 0.51–0.56 / 0.59–0.73 / 0.80–0.97 |
| 1–3 m | 25 … 400 | 1.6 / 4.0 | ~510 (cap; alpha compensated) | 0.51–0.71 (flat above G 50) |
| 3–10 m | 25 … 400 | 0.5 / 1.3 | ~520 (cap; alpha compensated) | 0.40–0.43 (flat at every gain) |

What the conventions preserve: number density per shell (from the DSD), the order of fall speeds and lengths, the
lean from u/v_t(D), environment-coloured contrast (no light source invented). What they distort:
- **Width.** Every drawn streak is ≥ 1 px (with the +0.6 px floor about 1.6 px) where the physical width is
  0.1–0.3 px: aspect ratio 3–6× too thick.
- **Contrast.** G × 100 makes a 0.3 % streak 30 %: the drawn streaks are the brightest/darkest elements of the band
  although physically they are the faintest.
- **Depth.** Only the nearest half-metre is drawn as streaks. In the sweep, moving the shell outward does not add
  depth: at 3–10 m the streaks become sub-pixel and the energy stays at ~2× the dry floor whatever the gain — far
  rain is a fine shimmer and veil, not streaks. Raising G cannot create parallax that the geometry does not have.
- The owner's hypothesis that near-shell × 100 streaks read as scratches on the glass: **not supported as the main
  cause by this evidence** — M1 near-shell streaks are sparse; the dense diagonal/vertical texture the owner saw is
  M2's mid-depth texture (section 4a). Near-shell streaks at G 400 do approach that look; at G 25–50 they are barely
  visible.
- Applying one convention to every regime keeps regime differences physical; it does not validate the convention.

## 4. The owner's impressions, investigated in real-time motion (frame metrics + own viewing)

**(a) Dense texture reads as scratches / surface hatching — reproduced, cause identified.** The texture is M2's
mid-depth layer (also in M5). `layers/`: texture alone carries the motion (E 1.25 moderate, 1.79 heavy, against 0.21–0.25
for veil alone and 0.46–0.61 for near streaks alone). Its strokes are generated once per regime and scroll rigidly:
**one lean per layer (zero angle dispersion), one speed per layer, uniform coverage over clouds and gaps** (no
column gating). Real rain has a spread of angles and lengths from the drop-size distribution and independent
drops; M1's streaks, sampled per drop, show an angle s.d. of 19–22° and lengths 1.4–9.7 px (p10–p90, moderate),
M2's near tail 11–17°, the texture 0°. Spatial self-similarity of the moving component (max autocorrelation at
lags 8–160 px): product 0.035, M2 0.031–0.039 after the tile fix (revision-1 128 px tile: a measurable peak). The
regularity that remains is the rigid parallel stroke field, not the tile period.

**(b) M2's wash substituting haze for rain — not supported by the measurements.** Veil alone: band L* +0.05 … +0.3,
fine-detail −1 %, motion at the dry floor; computed alpha at the lowest row 0.37 (moderate) / 0.55 (heavy), but the
veil colour is the blurred local sky, so lightness hardly changes (physically correct: airlight ≈ surrounding
radiance). M2's legibility comes from the texture of (a), not from haze.

**(c) M4/M5 smudging — cause: the base fibres.** 2–5 px wide, soft, near-vertical strokes hanging from each column's
cloud base, strength independent of rate except through σ (item f). Physically, fall streaks below a 300 m base are
real but at 13′/px would be a soft gradation over hundreds of pixels, not discrete bars; no physically grounded
discrete-fibre treatment was found. The physically grounded cloud-base response is the deck-detail transmission
(the veil). Recorded as a failure of naturalness and of physical modelling.

**(d) Variants hard to tell apart.** Confirmed for light vs moderate in all models, heavy vs thunderstorm (rain cannot
separate them), parallel vs fanning projection, and 1/15 s vs 1/60 s exposure except as "fainter". The scene-
controlled human test is the instrument for this; it has not been run.

**(e) Prayer clarity** (controlled blocks; text-box luminance ratio, comparative; row values are the mean over the six
rows):

| | Prayer rows (all blocks) | Clock, day moderate | Clock, day heavy | Clock, day showers | Twilight / night |
|---|---|---|---|---|---|
| M1 | ±0.02 % | +0.6 % | +0.8 % | +0.5 % | +0.1 … +1.7 % |
| M2 | ±0.02 % | −5.9 … −6.9 % | −8.4 … −9.5 % | −0.1 … −0.5 % | +1.5 … +8.2 % |
| M3 | ±0.02 % | −5.5 … −6.0 % | −7.7 … −8.3 % | +0.7 … +1.0 % | up to +16 % (shafts behind the clock) |
| M4 | ±0.02 % | −5.0 … −5.4 % | −6.9 … −8.0 % | +0.2 … +0.6 % | +1.4 … +11.7 % |
| M5 | ±0.02 % | −6.8 … −6.9 % | −9.4 … −10.3 % | −0.7 … −2.9 % | +2.8 … +20 % |

The prayer rows are unaffected (they are opaque glass over the band's lower fade). **The clock band is worse by
5–10 % in moderate and heavy daylight rain for M2–M5**; M1 is neutral. Twilight/night increases mostly reflect the
sequential capture (the no-rain control drifts +1.3 … +3.8 % in the same order), so only values well above that are
attributable. Card, header, footer, rows and glass are DOM-identical in every clip.

## 5. Expiry on one time reference (review F-2)

Method (revision 2): the capture polls the page every 50 ms and timestamps, in ONE node wall clock, the product's
`data-precip`, the header icon, the overlay's frame counter and per-frame record; the screencast frames carry
compositor wall-clock timestamps on the same clock; the claim-withdrawal frame is marked in each clip
(`expiry-v2/`, "claims withdrawn +x.xx s"). Results (±50 ms):

| | Overlay visible after the claim withdrawal |
|---|---|
| Product (immediate) | 0 |
| M1 / M2 immediate | 0 (authority read every frame) |
| M1 in-flight completion | 0.18–0.19 s (one 180 ms drop cycle) |
| M2 in-flight completion | 1.00 s heavy, 1.12 s moderate (mid-depth texture draining downward) |
| M5 in-flight completion | 1.07 s heavy, 1.15 s moderate |

`data-precip` and the header icon change in the same 50 ms sample in every clip; no frame-counter stall. Derived
bounds: near layer 0.94 s, large-drop tail 0.30 s, texture 1.0–1.2 s (moderate/heavy), up to 2.3 s for drizzle.

**Correction of revision 1 and of the review's observation.** The review measured the overlay stopping ~1 s
BEFORE the header in the revision-1 clips. Two harness defects explain unreliable revision-1 expiry evidence:
(1) the overlay cached its inputs, including the authority flag, for 500 ms, so its stop could lag the claim by up
to 0.5 s; (2) the revision-1 clips were cut from frame timestamps only, and frame delivery stopped after ~4 s of
the 12 s capture, so clip time and page time were not tied to one reference. The ~1 s early stop is not
reproduced with the revision-2 instrumentation; the revision-1 expiry clips are withdrawn as evidence.

Status: immediate withdrawal is the **current permitted behaviour**. Bounded in-flight completion is a **research
alternative** that keeps particles visible 0.2–1.2 s after the record expires, which issue 96's hard constraint
prohibits as written ("must not drive the header, clouds, particles or optics for a single frame"). It would need
an explicit owner amendment under R002F's owner. **Neither is declared accepted on this evidence.** R002F and its
A2 candidate were not touched.

## 6. Cross-engine (owner item 5)

Firefox and WebKit: Playwright `recordVideo` (25 fps, lossy VP8; there is no screencast in those engines), day heavy,
twilight heavy, moonlit heavy (+ Firefox day moderate and the moonlit no-rain control) with all six presentations
(`cross-engine/`). Every presentation ran and composited in both engines; 0 network escapes. **The video encoding
smears sub-pixel streaks**, so these clips prove execution and gross composition, not appearance; appearance
judgement in Firefox/WebKit needs lossless capture (not available in those engines through this harness). WebKit
also drops one glyph of the header place name ("MAD NAH") in every presentation including the product — a font
fallback issue outside this scope.

## 7. Five-axis comparison (own viewing of native-size real-time clips + metrics; no human data)

| | Physical correctness | Perceptual naturalness | Regime recognition | Compositional coherence | Performance (ms/frame; 4× CPU) |
|---|---|---|---|---|---|
| Product | invented light at night; rate-blind; lean sign wrong; vertical sticks | canned uniform ticks | opacity only | ungated by light; column-gated | ~0 (CSS) |
| M1 | best of the five (per-drop DSD, v(D), lean, environment colour); G and shell are conventions | sparse, varied streaks; near-invisible by day at G 100 (physically expected) | heavy > moderate > light only faintly; drizzle and night: none (justified) | no column gating (rain over clear patches); clock unaffected | 0.3–1.2; 0.2–4.0 |
| M2 | veil derived; texture DSD-derived but rigid, single-angle, ungated | **texture reads as parallel hatching** (owner, reproduced) | most legible heavy | veil restrained and correctly coloured; clock −6 … −10 % | 2.9–5.5; 18–33 (over a 16.7 ms frame) |
| M3 | field amplitudes not derived (U); shafts failed to localise | quiet; shafts as faint smears | weak | only model besides M5 with cloud gating | 0.4–2.6; 1.7–15 |
| M4 | fibres unsupported (U) | smudges / barcode | weak (veil only) | clock −5 … −8 % | 0.6–1.6; 0.4–17 |
| M5 | inherits e, f | hatching + smudges | M2-like | gated; clock worst (−7 … −10 %) | 3.9–5.8; 17–32 |

**No model qualifies on the present evidence.** M1 is the most physically faithful and the least legible; M2 is the
most legible and reads as an artificial pattern; M3–M5 add unsupported parameters. The human test is outstanding.

## 8. Negative results, each in exactly one category

| Result | Category |
|---|---|
| Drizzle invisible in every model at every gain tried | **physically justified absence** — 0.08 px wide, 2–4 px long, 0.12 % per-streak contrast at 1 m; only mist-like contrast loss would be visible, and that is the provider-visibility path |
| No rain visible at moonless night in any model | **physically justified absence** — drops refract their environment; with no lit source the environment–background difference is ~0 (the product's luminous streaks are invented light) |
| M1 light rain near-invisible by day | **physically justified absence** (0.33 % per-streak contrast at 1 m; deck-detail retention 76–80 % at a 600 m base) |
| M2 texture reads as hatching | perceptual naturalness |
| M4/M5 base fibres read as smudges | perceptual naturalness (and physical modelling: unsupported parameter f) |
| M3 shafts not localised / illegible | physical modelling (field from column density too broad at 45 % cover) |
| Revision-1 showers veil from a cell mean; revision-1 Moon kernel | physical modelling (removed in revision 2) |
| Light vs moderate weak in all models; heavy vs thunderstorm not separable by rain | regime discrimination |
| Parallel vs fanning projection, 1/15 s vs 1/60 s | regime discrimination is not the issue: no perceptible difference (recorded as such) |
| First M4/M5 build at 7–13 fps (blur filter) | physical modelling is not the issue: implementation performance failure, replaced |
| Revision-1 blind pack | evidence failure (scene confound), not a renderer result |

## 9. Unchanged from revision 1 (still valid)

Direction table test (`tests/precip-eval-direction.test.cjs`, 6/6): rain lean follows the camera geometry at az 180
and 90 for W/E/N/S winds; the product's cloud drift ignores `skyAz` (a separate cloud-side finding routed to issue
124), so rain and clouds can agree only at the default camera. Evidence semantics for "rain category, amount
unavailable" (T-A, T-B consistent with the owner's ruling; T-C is an unsupported rate) with the truth table; the
label is hover/assistive only; the simulation lane cannot express "unavailable".

## Reproduce

```text
node tools/qa/precip_models_capture.cjs --pw <playwright> --root . --out <bulk> --only <regex> [--engine firefox|webkit] [--throttle 1] [--models M3,M4,M5]
python tools/qa/precip_models_post.py --bulk <bulk> --only <regex> --anim <dir> --out <summary.json> [--blind <dir> --key <file> --blindrx <regex>]
node --test tests/precip-eval-direction.test.cjs
```
Scene families: `b{day,wind,twi,moon}-<condition>` (controlled), `conv-*`, `layers-*`, `expiry-*`, `day-*`, `twi-*`,
`night*`, `orient-*`, `reduced-*`, `evidence-unavailable`.
