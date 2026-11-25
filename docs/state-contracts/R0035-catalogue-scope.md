# R0035 · Does the preview magnitude cutoff describe the refined sky?

**Decision input for [issue 102](https://github.com/theislampill/salah_widget/issues/102).** On the tested dark, clear frame, **1,235 of the 1,404 stars that pass the refined renderer’s display-contrast criterion are absent from the bright preview catalogue**. For every one of those 1,235 stars, its removal changes at least one RGB channel by one code or more at its center when the worker-returned raster is encoded. A preview-only selection would exclude 88% of this frame's model-detectable stars *before* the foreground or the glass. This result supports retaining the faint population for comparison when evaluating the proposed cutoff.

These are offline measurements of the unchanged renderer at `df644ef60156b67b5c487395176369bcec7a0d7b`. They address the [owner’s request to explain the exclusions](https://github.com/theislampill/salah_widget/issues/102#issuecomment-6915419130). The [earlier round](https://github.com/theislampill/salah_widget/issues/102#issuecomment-6915335881) identified the experimental producer as local head `e1d66c17`. That head was unavailable for this measurement. The scene inputs below were chosen independently. Reproducing the previously reported 155 bright and 1,182 faint stars requires the original scene and stage definitions. Candidate frame-time, glass appearance, temporal fidelity and human perception require separate evidence.

## Observations

Fixed synthetic site at 24.47° N, 39.61° E, sea level. Stock south-facing camera, 45° altitude, 90° vertical field, 325 × 530 at DPR 1. All rows use synthetic 20 km visibility at 10 °C, clear foreground assumption, zero local light-pollution parameter and the pinned tier-128 registered diffuse asset. The UTC instants and solar/lunar altitudes are retained in the result. “Near −18°” describes solar geometry only. The criterion columns use the physical worker diagnostic. The two RGB columns encode the raster returned by the worker, before the host accepts it.

| Scene | Sun altitude | Preview members passing criterion / projected | Refined-only passing criterion / projected | Refined-only passing criterion with a worker-raster RGB change at ±1% | At ±5% on the same raster |
|---|---:|---:|---:|---:|---:|
| Dark, Moon below horizon | −48.60° | 169 / 169 | 1,235 / 1,250 | 792 | 1,222 |
| Moonlit, Moon at +40.76° | −50.25° | 157 / 159 | 1,198 / 1,329 | 542 | 1,178 |
| Near −18° | −18.05° | 134 / 134 | 1,272 / 1,296 | 798 | 1,250 |
| Morning twilight | −4.79° | 0 / 119 | 0 / 1,189 | 0 | 0 |
| Daylight | +48.60° | 0 / 136 | 0 / 955 | 0 | 0 |

In morning twilight, removing 14 individual stars (four bright, ten faint) changes a center RGB code on the worker-returned raster. An independent reviewer repeated the withdrawals after the host’s atmospheric adaptation on that same scene and counted 23 (11 bright, 12 faint), still before foreground composition. The physical detectability count is zero in both comparisons. In daylight, zero of the 1,091 projected stars passes the physical criterion, and zero changes an RGB code in the worker-raster withdrawal test. The census supplies no post-adaptation daylight byte count. A changed byte alone would therefore be a poor eligibility rule. The scene populations and lunar geometries vary between rows. Their differences do not isolate the effect of moonlight.

## What the measurements mean

- **Population.** The experiment joins the actual membership of `NativeStarPreview` (visual magnitude ≤ 4.5) by source ID to the projected emitters and individual diagnostics returned by `NativeSkyEngine.render(nativeJob(snapshot, true))`. It requires a ready, registered frame and the shipped worker setting of zero scintillation. Each projected source in these five scenes had one source diagnostic and a complete background at its direction.
- **Model detectability.** The physical renderer’s `displayVisibility` sets its `detectable` flag at a modeled central luminance contrast of 2/255 in nonlinear display space. The census requires a complete background and positive altitude and cross-checks the result against the frame total. Human visibility, especially through frosted glass, needs separate observation.
- **Pixel test.** For one source at a time, use its spectral flux after transport and the renderer’s pixel-integrated point-spread function at its true fractional position. Keep the worker-returned linear raster, neighboring stars and worker exposure. At its center pixel, remove just that source or change its flux by ±1% and ±5%, then use the native display encoder. A response means at least one RGB channel changes relative to the nominal frame in either direction. Overlapping sources can share a pixel. The table counts each source separately. The fixed perturbations measure sensitivity to quantization. Candidate ×1/×2 strengths and temporal behavior require the producer.
- **Control.** A registered test compares that one-pixel calculation with complete independent rerenders of a target and an overlapping neighbor at several subpixel positions, including edges, across weak and strong flux on nonuniform backgrounds. The oracle uses the reference encoder. It exercises both detected and sub-code changes for each sensitivity probe. Replacing the source’s subpixel position with the pixel center or crediting the overlapping neighbor’s flux to the target each made this test fail.

## Application to the candidate

The public renderer uses the magnitude cutoff to bound the start-up preview while the richer frame is pending. Applying that same cutoff to a refined frame would exclude sources with observable display contributions. For the candidate comparison, separate the two presentation tiers, then count exclusions by actual star ID at successive decisions, including physical occultation and altitude, complete/detectable background, calendar-Moon and cloud transmission, and glass treatment. Retain the IDs that change treatment near glass boundaries. The result JSON lists the three highest-contrast contributing refined-only examples in each applicable scene, with card coordinates, for use when comparing a replay to the full card.

The census stops at the worker return. Below −20° solar altitude the worker has already applied the native lunar night presentation, which covers the two night rows. At and above −20° the host subsequently derives atmospheric fields with `nativeAtmosphereFields` and calls `nativeSkyPresentation`. Its adjusted sky background can change quantization around a star in the three remaining rows. Calendar-Moon, painted-cloud, glass and prayer-interface composition follow. Establishing how many faint sources can modulate on the finished card, and whether their flicker is perceptible, requires those later layers and the actual producer. The authorized changed-rectangle WebKit comparison still needs the original unmodified producer, its mitigated counterpart and main under equivalent conditions. The amplitude, glass treatment, magnitude policy and final visual acceptance remain with the owner.

## Reproduce

Run from the repository root with Node (recorded with v24.22.3). Both programs read local assets only.

```sh
node tools/r0035/assess_catalogue_scope.mjs > /tmp/r0035-catalogue-scope.json
cmp /tmp/r0035-catalogue-scope.json docs/state-contracts/evidence/R0035/catalogue-scope.json
node --test tests/r0035-star-scope.test.cjs tests/real-sky/cp9-scintillation.test.mjs tests/real-sky/native-star-preview.test.mjs
```

[Retained scene inputs, counts, catalogue/asset hashes and example star coordinates](evidence/R0035/catalogue-scope.json).
