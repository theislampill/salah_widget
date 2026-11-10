# Bounded numerical comparison: no supported product change

The owner explicitly approved this one comparison on 2026-10-18: **“Approve this bounded numerical comparison”**. The approved question specified the exact retained failed scene, the existing 8192-sample rule `64 radial × 128 angular` versus `32 × 256`, existing accuracy controls, unchanged sample ceiling/quality gates/H1/V5/geometry/assets, no Firefox profiling and no implementation unless supported. This approval does not amend TA1–TA3 or authorize another sampling search.

Source HEAD is `f35ccd403bbb04a613cc13aa8f91556561f20c4c`; product runtime remains `f3e7ff1be9d77b224caaf988791b7616c187b6c4a768a34192826a5dbdd5992c`. The experiment loaded authored sources in Node22 and substituted only `8192:[64,128]` with `8192:[32,256]` in a separate function. The experimental `.mjs` here is evidence, not installed product source. Each arm used a fresh four-row `MoonPool`, the actual kernel/assets and the existing test adapter. No browser or production file was changed.

| Observation | Original 64×128 | Experimental 32×256 |
| --- | --- | --- |
| Adaptive status | `limit-reached` | `empirical-adaptive` |
| Final projected change | 0.8783235549926758 | 0.12836551666259766 |
| Unsettled receivers / receiver heuristic remaining | 17 / 17 | 0 / 12 |
| Final receiver maximum change | 1.4474468231201172 | 0.309814453125 |

The original failure reproduced exactly. Scene, assets, profile, masks and numerical results through4096 matched; final coverage matched. Independent review recomputed all22 stored arrays, each rule-specific physical identity, both projected comparisons and zero changed unselected receivers. Changing radial/azimuth legitimately changes the physical identity; those identities are verified separately.

**The alternative is unsupported for implementation.** Its final step changes azimuth only, retaining32 radial nodes from4096. The two8192 rules differ by maximum0.5759053230285645 and0.7499580383300781 in the two projected offsets. These are contrary accuracy evidence, not a newly invented failure threshold, and the original64×128 rule is not an independent accuracy oracle. The literal adaptive gate PASS therefore does not establish radial convergence. Existing unchanged kernel/V5 and pool controls retain their material, geometry and assembly scopes; they cannot settle this quadrature-accuracy question. Repeating them would not supply the missing independent reference.

The independent [result review](../reviews/quadrature-r112-result-review-r1.json) recommends preserving the comparison without implementing the alternative or acquiring further variants. [Verification](../reviews/quadrature-r112-verification-r1.json), [preflight](../reviews/quadrature-r112-preflight-review-r2.json), [complete result](RESULT.json) and [host execution](EXECUTION.json) retain the exact evidence. The host timeout was600seconds; each arm also had a240second cooperative limit including initialization. The operation returned normally in approximately74seconds, released its lock, and left product sources unchanged. Elapsed times are not a performance comparison.

## Reproduction and custody

`compare_quadrature.cjs` takes three positional arguments: an isolated checkout at the source HEAD above, a new output directory, and the published `reviews/firefox-dpr2-quality-source-r69-review.json`. Run it with Node22 under a600second host subprocess timeout. Source identities, the one substitution, asset digests and the exact scene are asserted or recorded. The historical wrapper is path-projected provenance; use the three actual local argument paths rather than its role placeholders.

The `.bin.gz` files preserve native typed-array payloads from the Windows x64 run. RESULT identifies each type, element count, decoded SHA-256 and compressed SHA-256. Decompress and interpret the declared little-endian typed elements; no interpolation or image reconstruction is necessary to recompute the recorded differences. The public scene record is path-projected, so its file hash differs from the historical original pin while `observed.acceptedPreviewScene` is unchanged. A fresh replay must disclose that input-file identity distinction.

The adopted final order, SHA-256 `8d21668218160cb3de67a761405f5f794e9d1bfdf4a04da3fb53ad6ce54eb67d`, section5 states: “Use one bounded current discriminator, and if the adverse requirement remains unresolved, return its precise scientific/product decision rather than a general Firefox campaign.” The additional owner-approved comparison is now exhausted. The remaining scientific question is radial and angular convergence jointly; another azimuth-only gate PASS cannot answer it. Any further numerical strategy or reference calculation requires its own bounded decision. No numerical impossibility, fixed defect, revised quality threshold, sample-budget increase, final qualification or merge approval is claimed.
