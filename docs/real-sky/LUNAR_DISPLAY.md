# R0022 lunar atmosphere display

The selected contract is `R0022-L1-H1-K003-H020-v1`. The owner accepted
H1 and the canonical Orlando clear-night full card. The selection is a
calendar display adaptation, not a calibration of lunar-sky photometry.
H2, which registered a compact contribution to the calendar Moon, was rejected.

## Physical and display ownership

`real-sky/native-preview.mjs` owns the lunar-only mapping and the native
atmospheric decomposition. `real-sky/native-host.mjs` supplies that decomposition
at full worker admission on the same grid as its original background. The
existing first-paint and preview callers consume the shared preview function;
`native-first-paint.mjs` needs no separate treatment or startup-branch import.
`tools/build_native.py` generates the root entries and native bundle.

Below solar altitude −20°, the accepted physical model has an exactly zero
solar source. Refined admission samples only the lunar component at the same
worker grid nodes, retaining the worker's full raw sky and exposure. It omits
the additional zero solar/aerosol planes and inactive twilight metadata; it
does not remove any original worker field. At −20° and above, the complete
decomposition remains in use. Preview retains its complete field set.

The input lunar field uses the existing reference-pixel flux convention:
physical sky luminance times the camera pixel solid angle, divided by the
V-band zero-illuminance reference. Fast preview preserves flux per 325×530
reference pixel, including its existing area normalization. This change does
not modify the scientific sky model, physical camera, exposure, catalogue,
diffuse data, or lunar surface.

For the raw lunar RGB vector `L` and original effective exposure `E`, define
`Y = 0.2126 Lr + 0.7152 Lg + 0.0722 Lb`, `z = E Y`, `K = 0.003`, and `H = 0.020`.

```
t(z) = z                                      when z <= K
t(z) = K + H * (z - K) / (H + z - K)           otherwise
Ldisplay = L * t(z) / z                        (zero remains zero)
```

One common RGB scale preserves chromaticity and angular ordering. The shoulder
is identity below the knee, positive above it, and smoothly approaches `K+H`.
Finite floating-point values can tie at the asymptote. It neither relocates the
physical lunar field nor changes the approved enlarged calendar-Moon slot.

The policy changes only the existing night leg of atmospheric presentation.
It has full weight at solar altitude ≤−18°, smoothly fades with the existing
cubic blend over −18° to −12°, and is absent at ≥−12°. The solar/daytime
presentation leg retains its original inputs and mapping. Cloud transmission
still occurs once in the native foreground composition.

`lunarBackgroundLinear` retains the raw physical lunar component.
`physicalSkyBackgroundLinear` retains the raw atmospheric background whenever
presentation changes it. `lunarNightDisplayLinear` is explicitly mapped output;
`linear`, `skyBackgroundLinear`, and `backgroundLinear` carry the selected
presentation into the existing composition. Raw and mapped fields must not be
confused with each other or with measured local photometry.

Deep-night mapping and output assembly share one pass with the same ordered
arithmetic. The operation runs at existing preview construction or worker
admission, not on each foreground paint. Its temporary arrays have fixed native
dimensions; it adds no provider, controller, render chain, canvas or readback.

Refined admission retains at most four camera/grid geometry entries. They hold
directions, their finite three-component vectors, solid angles and interpolation
coordinates, never physical samples,
UTC, atmosphere or exposure. Each call still validates the current physical model and calls its unchanged
exported lunar luminance and cloud-transmission functions. No scattering
equation or calibrated constant is duplicated in the display owner.
The host encoder uses a fixed 26,624-byte search table to locate the original
binary64 encoding thresholds; it does not approximate or change their output
codes. Within one encoding call, a preceding RGB code is reused only while
the current value remains in that exact oracle interval. The composed prefix
and untouched raw tail write into one private final RGBA buffer; validation
and the final publication fence precede visible output. This removes bounded
temporary encoding copies without caching pixels or physical light.
The geometry and encoder caches are included in the scoped resource observation.
The host also retains the last published solar-obstruction URL. It reuses that
URL only when captured cloud alpha and row support match exactly, and clears it
with the previous presentation. This avoids identical PNG encoding; changed
alpha still reaches the original mask producer before publication.

## Preserved eligibility and material contracts

The native calendar-derived illumination, beam, glow, cloud-light and registered
optics retain their shared eligibility gate. Independently computed physical
astronomical moonlight does not acquire a zero gate from decorative SIM phase or
day flags. V5 terrain/material, Earthshine, device-resolution ownership, opaque
calendar composition, outside-Moon stars, source-age and target/generation
fences are unchanged. The accepted midwater/fog corona gate is retained.

## Acceptance scope

The owner accepted canonical clear-scene left/open/lower ROI means
58.6 / 51.9 / 50.0 against the predeclared maxima 85 / 80 / 80, with the complete
prayer card present. These limits apply to that declared scene; they are not
targets for every time, weather condition or source channel. Broad positive
moonlight, weather, dawn/day, currentness, recovery and material preservation
require their own native observations and original pixels.

The six R0022 final dispositions, remaining ordinary full-scene owner acceptance,
production merge, public readback and closure are still pending in this candidate.
The scoped synchronous cost checks have independent acceptance for Chromium DPR 1
and Firefox DPR 2. The fixed allowance is the larger of 0.25 ms or 10% of each
baseline median/p95, after five-second warmups and four paired ABBA rounds.
Refined admission measures 13.8/15.8 ms against 15.84/18.70 ms limits on Chromium,
and 22.36/26.88 ms against 38.17/42.416 ms limits on Firefox. All other measured
scopes pass; Firefox full-preview p95 has only about 0.106 ms margin. Every call,
slow tail and prior failed acquisition remains retained. These are bounded CPU
results, not GPU, battery, ordinary motion or recording qualification.
PR #43 remains a separate draft with retained timing
and actual-extension-parent limitations. R0022 images do not qualify those
startup obligations. The qualified `r0022-l1-full-composition/v1` handoff will
carry only its exact accepted source and scene scope.

Owner-decision evidence: [immutable display packet](https://github.com/theislampill/salah_widget/tree/c44a4d2df44ee9eef59faba9d524f742163e1270/evidence/R0022/owner-display-20261015).

### Bounded Moon projection reuse

The owner-approved R0022 boundary includes `moon/src/moon-detail.mjs` for one
material-projection cache. The adopted prefix-table identities and complete
device projection/presentation-up inputs own its key. New atmospheric frames
still sample current gas, catalogue/diffuse light and exposure/opacity inside
the actual composition path; clouds and the final currentness fence remain
live. H1 and the material/terrain/Earthshine calculations are unchanged.

The one retained projection uses 33 bytes per device pixel, including its
coverage mask shared with the frame join; the additional retained sample array
uses 32 bytes per pixel. Adoption, clear and disposal invalidate it. Invalid
adoption fails closed instead of retaining mixed prefix tables. Canonical Moon
bundles include this source; their byte identities change without a new terrain
solver or numerical model. Exact source and scoped native cost controls pass;
affected native preservation and whole-scene acceptance remain required before
delivery.
