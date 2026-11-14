# R0034 sky-physics registry pass

Documentation only. Context: the owner-reported refined-sky artifact tracked under R0034 (issue 101) and the owner's
instruction to make every materially relevant sky/weather machine explicit in the registry. Source read on main
`91c60ed2`. No product, test, tool or generated file changed; nothing was executed in a browser. The entries are
proposals: index codes and count tables in `IMPLICIT_STATES.md` are unchanged, and each new entry carries a
"Proposed status (effective on acceptance)" line, as the registry rule requires.

## 1. Stages traced and entries

| # | Stage | Entry | Kind | One-line finding |
|---|---|---|---|---|
| 1 | Weather record → sky inputs; refined identity | [ISM-SKY-032](../../IMPLICIT_STATES.md#ism-sky-032) new; [ISM-SKY-006](../../IMPLICIT_STATES.md#ism-sky-006) updated; ISM-WX-001/002/005/009 linked | stateless projection | the job reads `vis`, `temp`, `src`; the main identity keys the whole weather copy (`rh`, `cloud`, `code`, `wind` too) |
| 2 | Clouds: generation, seeding, drift, lighting, transfer, albedo | [ISM-SKY-003](../../IMPLICIT_STATES.md#ism-sky-003) updated; [ISM-SKY-034](../../IMPLICIT_STATES.md#ism-sky-034) new; ISM-WX-005, ISM-SKY-016 linked | stateful (003) + stateless transfer | cloud albedo is not physical; painted alpha is the only cloud transmission |
| 3 | Wind | ISM-SKY-003 updated; ISM-SKY-032 | stateless projection into stateful integrator | horizontal drift only; `cloudState.wy` written, never read; calm fallback still drifts |
| 4 | Godrays, crepuscular/anticrepuscular | [ISM-SKY-035](../../IMPLICIT_STATES.md#ism-sky-035) new | memoryless gates + CSS latch | anticrepuscular computed and forceable but hidden in both generated entries |
| 5 | Albedos | ISM-SKY-033, ISM-SKY-034 | constants | no ground albedo; aerosol ω = 0.9 default; no cloud albedo |
| 6 | Scattering, Mie g, aerosol, tone map, quantisation | [ISM-SKY-033](../../IMPLICIT_STATES.md#ism-sky-033) new; [ISM-SKY-023](../../IMPLICIT_STATES.md#ism-sky-023) updated | stateless + registered caches | single scattering only; HG g = 0.76 default; 8-bit rounding without dither |
| 7 | Ozone | ISM-SKY-033 | absent | not modelled; the core warns "No … ozone bands" |
| 8 | Solar disc and solar optics gating | [ISM-SKY-036](../../IMPLICIT_STATES.md#ism-sky-036) new; ISM-SKY-035 | stateless + CSS easing | `--sunvx/--sunvy` jump to target while the body eases 2.4 s |
| 9 | Silver lining / SSS | ISM-SKY-034 | stateless display rim | display rim only; no subsurface or volumetric term |
| 10 | Radar geographic calculation | [ISM-WX-004](../../IMPLICIT_STATES.md#ism-wx-004) updated | stateful transport (existing) | zoom-6 Web Mercator; no tile-range check beyond finiteness |
| 11 | Presentation/compositing chain | [ISM-SKY-037](../../IMPLICIT_STATES.md#ism-sky-037) new | class/CSS-distributed | canvases 325×530 backing shown in a 323×528 padding box (derived); `.grain` noise exists but is hidden |

Stateless stages (pure functions of inputs, with only registered caches or module tables): 1 (projection), 5, 6,
7, 8 (apart from CSS transitions), 9, and the cloud transfer in 2.

## 2. Artifact hypotheses: ownership (hypotheses, not findings)

| Hypothesis | Page-side owner (registered machine) | Outside the page |
|---|---|---|
| Browser GPU dithering of gradients | remaining CSS gradients: glass rows/straps (ISM-SKY-037), sun/halo/godray/rays (ISM-SKY-035/036). The card's own 160° sky gradient is replaced by `#273445` in the generated stylesheet | dithering policy of the browser/GPU |
| Glass `backdrop-filter: blur(7px) saturate(135%)` over a smooth canvas | `.p` rule in `src/native/index.html` (native UI glass; layer in ISM-SKY-037) | filter implementation and its working resolution |
| Canvas quantisation with non-1:1 scaling | quantisation: ISM-SKY-023 (no dither); lattices: ISM-SKY-033 (≈13.5 px preview, ≈7.9 px refined); scaling: ISM-SKY-037 (≈0.994·DPR display ratio, derived) | resampling kernel of the browser |
| Display or colour management | none (no `colorSpace` option; sRGB codes) | OS/display colour management, panel dithering |
| A noise layer | `.grain` feTurbulence layer exists in source, removed by `.c>.grain{display:none!important}` in both generated entries (ISM-SKY-037); no encoder noise (ISM-SKY-023) | none |

Correction to the R0034 contract §5 wording ("a noise layer (none found in code)", "shown at the card's CSS size"):
a noise layer exists in source but is hidden in the shipped app; the canvases are shown in the card's padding box,
not its border box (derived from CSS, not measured).

## 3. Unknowns

- Real canvas rect in a browser and in the owner's embed (the 323×528 figure is derived from `*{box-sizing:border-box}`,
  `.c` 325×530 and its 1 px border).
- The owner's compositor (WebRender hardware/software), zoom and OS scale; `backdrop-filter` working resolution.
- Whether hiding the anticrepuscular element in the physical-sky build is intended.
- Vendor test coverage of the copied scattering constants (vendor suite not examined).

## 4. Not inspected

`vendor/real-sky` sources and oracles; `diffuse-*` and `registered-starlight` internals beyond their registered
entries; `moon/src/*` beyond DPR and albedo greps; star preview internals (ISM-SKY-002, R0035); `v1/`; the
installers; any live browser or provider behaviour.

## 5. Candidate improvements (not implemented)

Ranked by expected value for the owner's purposes (bug fixing, explicit machines, motion/transition clarity, PBR gaps,
presentation), smallest first where value is similar. "Pixels" = whether a healthy existing scene would change. Every
row is a proposal for a future, separately authorised change; none is made here.

| ID | Entry | Class | Evidence (F = fact from source, H = hypothesis) | Smallest change | Blast radius | Pixels | Owner | Verification |
|---|---|---|---|---|---|---|---|---|
| CI-01 | ISM-SKY-032 / 006 | defect | F: main identity keys `rh`, `cloud`, `code`, `wind` that the job never reads; refined frame withdrawn on such updates (`native-contract.mjs` L8) | merge the R0034 branch's consumed-input identity | `real-sky/native-contract.mjs`, lifecycle | no (frames byte-identical) | R0034 | existing ES34-01..05 tests; R0034 native lanes |
| CI-02 | ISM-SKY-037 | presentation / defect candidate | F (derived): canvases 325×530 shown in a 323×528 padding box (L13, L24-33); H: contributes resampling softness | measure the real rect first; if confirmed, size canvases to the border box (e.g. `inset:-1px`) or the backing to the rect | preview/refined hosts, capture scaling, `.c` CSS | yes (slight) | R0034 | native rect probe at DPR 1/1.25; crop diff at the card edge |
| CI-03 | ISM-SKY-035 | defect (doc/code mismatch) | F: `.atmo .anticrep{display:none!important}` in the generated stylesheet (`tools/build_native.py` L112) vs OPTICS.md "production" | decide: show it (drop it from the hide list) or document it as retired | `tools/build_native.py` CSS, OPTICS.md, DESIGN.md | yes if shown | unowned | forced `&debugOptic=anticrep` crop; docs contract |
| CI-04 | ISM-SKY-035/036 | transition clarity | F: `--sunvx/--sunvy` written at target, `.suncorner` transform eases 2.4 s (L71, L3030) | derive the optic anchor from the same eased position or ease the optics' anchor identically | native CSS/paint | yes during lift changes | unowned | sunrise `&simTime=05:50&timeScale=…` clip; halo crop rings the body |
| CI-05 | ISM-WX-004 | defect (edge) | F: tile row/column unchecked beyond finiteness (φ > 85.05°, lon 180) | reject or wrap out-of-range tiles before dispatch, or rely on R0032 disabling acquisition | `fetchRadar` | no | R0032 | unit cases at ±86°, lon 180 |
| CI-06 | ISM-SKY-003 | implicit-machine hardening | F: `cloudState.wy` written, never read; calm fallback drifts (`windX −0.7`) | document as decorative (DESIGN) or remove the dead field | native cloud state | no (removal) | unowned | `r0025-*` continuity tests unchanged |
| CI-07 | ISM-SKY-035 | hardening | F: `--ray`/`--anticrep` not zeroed by `beginSkyScene`/no-timetable paint; zeroed by the next reconcile | zero them with the other optics in `paintCelestialWithoutTimetable` | native paint | no (≤1 frame) | unowned | `weather-no-timetable-withdrawal` extension |
| CI-08 | ISM-SKY-037 | presentation | F: `.p` `blur(7px) saturate(135%)`, `.e,.wt` `blur(8px) saturate(1.2)` sample the canvases; H: amplifies 1-LSB contours | owner check of §5 step (2) of the R0034 contract before any change | native glass CSS | unknown | unowned | owner DevTools toggle; headed Firefox crop |
| CI-09 | ISM-SKY-023 | PBR/presentation gap | F: 8-bit rounding, no dither; H: contours visible on some displays | an ordered/blue-noise ±0.5 LSB dither in the encoders, behind an owner decision (visual change) | both encoders, byte-pinned tests | yes | R0034 (visual decision needed) | encoding tests rebound; periodicity analysis; crops |
| CI-10 | ISM-SKY-033 | PBR gap (missing) | F: no ozone absorption anywhere (core warning L95) | Chappuis-band ozone τ(λ) term in the copied core — requires a vendor/core transform decision | copied core, vendor policy | yes (twilight blue) | unowned | vendor oracle; sunset/twilight crops |
| CI-11 | ISM-SKY-033 | PBR gap (approximated) | F: single scattering + Patat empirical twilight residual; no multiple scattering | none small; a precomputed multiple-scattering LUT would be a core change | copied core | yes | unowned | vendor oracle; near-Fajr crop (gate F) |
| CI-12 | ISM-SKY-033 | PBR (modelled, fixed) | F: Mie HG g = 0.76, ω = 0.9, Ångström 1.3 core defaults; aerosol τ from visibility only | none required; optionally derive g/ω from humidity — owner decision | `nativeJob` | yes | unowned | preview tests; hazy-day crop |
| CI-13 | ISM-SKY-034 | PBR gap (approximated) | F: silver lining = display rim `0.85·facing·sunUp·cosθ`; no forward-scattering phase or SSS | phase-based rim weight using the same HG g | `paintClouds` | yes | unowned | broken-cloud low-sun crop |
| CI-14 | ISM-SKY-035 | gating clarity | F: crepuscular gate depends on mid cover only (`broken(clM)`); corner rays have no weather gate | document; optionally gate rays by transmittance only | native atmosphere | yes if changed | unowned | `&simWx=2&simCloud=50` low-sun crop |
| CI-15 | ISM-SKY-033/034 | PBR (missing, by design) | F: no ground albedo; no cloud albedo; aerosol ω only | none unless a ground-reflection term is wanted | core | yes | unowned | — |
| CI-16 | ISM-SKY-036 | PBR (approximated) | F: limb darkening u = 0.6 below 40°, flat core above; refraction flattening presentational | none; record as approximation | — | no | unowned | sunrise/apex crops (gates A, B) |
| CI-17 | ISM-SKY-037 | presentation (shadows, strokes, fonts) | F: `.c` `box-shadow 0 18px 50px #0008`, 1 px border `color-mix(accent 30%)`; `.p` 1 px `#ffffff2e` stroke + `--glass` inset shadows; fonts via `--font-body` and the optional web-font gate (ISM-PRAY-008) | none identified from source alone | native CSS | — | unowned | UI judge crops (gate J) |

Physics status in one line each: ozone absorption **missing**; multiple scattering **missing** (empirical twilight
residual instead); Mie anisotropy **modelled** (HG, fixed g); silver lining **approximated** (display rim); godray
gating **modelled** (heuristic gate, CSS shafts); albedos: ground **missing**, aerosol ω **modelled** (fixed), cloud
**missing** (painted alpha); solar-disc limb **approximated** (linear u = 0.6 below 40°); wind-driven drift
**modelled** (horizontal, artistic rate).
