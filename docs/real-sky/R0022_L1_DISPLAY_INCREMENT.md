# R0022-L1 — settled lunar atmosphere/display coherence

Specification revision 1. Linked sub-increment of existing #34/R0022, coordinated
from #33/R0021 startup successor S10. No new canonical issue. **OPEN: attribution
is demonstrated; the ordinary full scene is not visually accepted.** The audit
coordinator owns publication of the linked issue comments and execution DAG.

## Problem, authority and preserved work

The owner rejected the concentrated white left-edge source and broad grey wash
in a clear Isha capture. Both supplied attachments are unchanged PR42 baseline:
product main `18ff14860ff41c084b1db5f396bb62aa9c22b1be`, runtime
`f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260`.
The contact sheet matches `before-chromium-clear/video-review/contact.png` after
resizing; the single crop is pixel-identical to `before-firefox-clear/cold-04.png`.
PNG byte hashes differ for the re-encoded crop. `OWNER_GLOW_ATTACHMENT_BINDING.json`
contains hashes, sizes and comparisons. Do not confuse these with the candidate
contact sheet or the separate invalid partial-build capture.

The original R0022 physical-light eligibility rows remain inherited evidence.
Its native-consumer and callback-cost gaps remain separate obligations. This
increment does not restart V5, CP9, the 37-issue audit, or a calibration programme.
Keep V1, approved body footprints, full V5 terrain/material/Earthshine, original
catalogue/diffuse inputs and all age/phase/generation fences unchanged.

## Bound scene and demonstrated attribution

Ordinary captures use accepted saved Orlando: latitude28.5383, longitude-81.3792,
height0m, America/New_York; a wall-clock fixture anchored at2026-09-25T02:00:00Z
advances at real1x. That is September24 at22:00 EDT. No SIM time/phase override is
used. Prayer dates match the local date and next Fajr date; timetable times and
weather are explicitly synthetic. Clear weather is WMO0, cloud0%, precipitation0,
visibility20km, temperature28C, RH45%, wind2m/s. `Isha` is only the UI label.

The frozen baseline attribution frame has accepted UTC1790301627024.69ms,
generation0; camera azimuth180°, elevation45°, vertical FOV90°, roll0°,325x530.
Physical Sun: altitude-35.4837365°, azimuth291.5852594°. Physical Moon:
altitude44.0311887°, azimuth134.8411277°, phase angle19.8931018°,
illuminated fraction0.97016455, distance382363.719km, radius0.2603438°.
The existing native calendar ephemeris differs slightly from this separate
low-order physical-sky ephemeris; neither was changed or represented as calibrated.

The physical Moon projects to **(3.557,223.536) native pixels**. Its atmospheric
aureole therefore lies at the observed left hotspot. The approved enlarged
calendar body occupies its existing upper-right slot. No stale/default Sun or
wrong-clock hypothesis is needed to explain these pixels.

At pixel(3,218), the model reports lunar0.547685 and natural0.000183cd/m²;
at(160,80), lunar0.003507 and natural0.000142; at(160,400), lunar0.007223 and
natural0.000293. Solar and local-light contributions are zero in this scene.
These are **empirical model outputs**, not measurements. Inputs use estimated
standard pressure1013.25hPa, aerosol optical depth0.06, albedo0.9, g0.76,
cloud transmission1 and explicit assumed non-stellar residual0.00014cd/m².
The model is KS1991-derived lunar scattering with a finite near-aureole, neutral
lunar/night spectral proxies and documented limitations. The native deep-night
path retains the reference exponential display encoding; effective exposure is
about10.6 (nominal24). Day/twilight adaptation does not operate at this depth.

Matched baseline and startup candidate controls reproduce the same result.
Frozen atmospheric reconstruction differs from the actual accepted field by at
most8.88e-16 baseline /4.44e-16 candidate. Same exposure is retained in each
ablation; no re-metering is allowed to confound removal of a component.

| Diagnostic intervention | Left ROI mean code | Open-sky ROI | Lower wash ROI |
|---|---:|---:|---:|
| Full baseline/candidate |240.8 /240.8|100.0 /100.0|138.6 /138.6|
| Remove native solar overlays |240.8|100.0|138.6|
| Remove calendar body and native lunar optics |240.8|100.0|138.6|
| Remove catalogue |240.8|100.0|138.6|
| Remove registered diffuse |240.8|99.1|138.5|
| Remove residual night only |240.7|98.4|136.6|
| Remove physical lunar atmospheric field only |33.1|27.5|38.5|

Clear-scene cloud removal has no effect. Removing glass changes row styling but
does not remove the hotspot or sky wash. Original full composition, equal-output
recomposition control, every ablation and restored full composition are retained
in `glow-baseline-clear` and `glow-candidate-clear`, with `GLOW_PIXEL_ATTRIBUTION.json`.
The baseline wrapper failed only while resolving its already-written video path;
`RECOVERY_RECEIPT.json` independently binds the completed capture, unchanged runtime,
video and current refined V5 result. It was not replayed or called a product failure.

**Disposition:** an existing settled lunar-atmosphere display/composition defect,
reproduced without amplification by the startup repair. The near physical field
saturates in the display, and its neutral broad contribution raises most of the
card. This does not prove that the numerical illumination is calibrated or wrong.
Removing all lunar scattering is attribution evidence, **not a repair proposal**.

## Semantic owners and executable remaining work

`real-sky/native-preview.mjs` owns atmospheric display mapping and preview fields;
`real-sky/native-host.mjs` owns the accepted full-frame display join;
`real-sky/native-first-paint.mjs` owns the first background. The retained
`vendor/real-sky` numerical source is immutable here; generated `real-sky/core`
must not be patched. `moon/src/moon-detail.mjs` retains calendar body composition.

1. Consume the retained matched frames, inputs and ablations. Verify the exact
   runtime before further work; do not repeat terrain research or attribution.
2. Establish the display contract for legitimate broad lunar illumination versus
   the bounded near-aureole in this calendar UI. Compare these bounded hypotheses:
   (a) an explicit lunar-only highlight/adaptation mapping at the existing physical
   direction, preserving non-lunar channels and directional ordering;
   (b) registration of only a separately identified compact display aureole to the
   approved body, leaving broad physical illumination in camera coordinates.
   Neither is accepted by this specification. Check units/solid-angle/exposure
   first; if a conversion defect is demonstrated, correct that owner instead.
3. Reject a hypothesis if it merely hides this crop, dims the whole sky, removes
   all lunar scattering, relocates the whole directional field, changes body size,
   raises stars, doubles weather transmission or regresses twilight. Preserve raw
   radiance separately from any expressly declared display mapping.
4. Use the current full-composite render as control, then predeclare the proposed
   display bounds and review matched alternatives. The owner must approve actual
   complete scenes; a stripped diagnostic or lunar-only error metric cannot close L1.
5. Qualify physically eligible bright-Moon clear and cloudy/rainy nights; real
   below-horizon and low-illumination lunar negatives; dawn on both sides of the
   horizon and day. Check first -> initial -> preview -> refined1x composition in
   Chromium/Firefox, DPR1/2, same native inputs, fixed body footprint, opaque Moon,
   correct occlusion, catalogue identity, source eligibility and raw-field retention.
6. Rerun only changed display/registration/eligibility and startup invariants.
   Keep first-complete-scene budgets unchanged. Preserve slow/missing-full-asset
   recovery and generation, seek, A-B-A and profile fences. Obtain separate review
   and owner authorization before integration; no merge/deploy authority is implied.

Executable entry: `tools/cp9/celestial_startup_check.py --root <verified-tree>
--out <new-evidence-directory> --scene clear --modes cold --duration 180 --layers`.
Use the recorded browser executable/driver and corresponding rainy, incident,
moon-negative, dawn and day cases. `--layers` deliberately modifies only the
post-startup diagnostic presentation; its images must never pass as repaired UI.

The actual extension/new-tab parent remains unavailable. A generic iframe does
not qualify it. Encoded marker values are parent `performance.now()` milliseconds,
not simulation time or filenames; they may freeze during shared-thread work.
Preserve the source capture intervals and actual video frame timing when judging
latency. `Moon False` was an image-region detector, not physical-light eligibility.

## Closure and DAG handoff

S10/#33 may consume the attribution but remains visually OPEN until L1 supplies
owner-accepted full-composition evidence. Completed startup implementation and
source/phase qualification must be reused, not repeated. The separate startup Draft
PR is implemented-unmerged work, never a closure or deployment receipt. Coordinator
publication links this file and its exact commit to #34 and #33, preserving audit
evidence `b879573c298f19189d1f2392108b8b9f3b2cda0b` and product baseline18ff1486.
