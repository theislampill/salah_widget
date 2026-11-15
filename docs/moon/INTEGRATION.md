# MB1 — V5 terrain Moon browser integration

This is an incremental Moon addition to the CP9 candidate pinned at
`1977217cc2ac26fcc436b991aff498d306a0cd26`, not a replacement repository.
`src/native/index.html` owns accepted lunar time/phase and exposes `SalahMoonHost`.
`moon/src/` contains authored internal script units. `tools/build_moon.py`, invoked
by `tools/build_native.py`, owns generated bundles, chunks, index and offline entries.
Do not edit generated `moon-host.js`, `moon-worker.js` or file-data scripts.

## Model / defaults

The original metric terrain and appearance-oriented NASA material, finite Sun and
Earth integration, V5 profile and WASM numeric kernel are retained. These are not
calibrated spectra. Default geometry remains the canonical upright calendar view;
`setReferenceScene` accepts explicitly supplied body-fixed physical-reference
geometry. An automatic high-accuracy observer ephemeris is not supplied.
The phase-angle cache quantum .0004 rad has a small *geometric* movement bound;
it does not prove every temporal shadow/radiance error. Worker refinement is
expensive (tens of seconds to minutes on tested hosts), not a 60fps shader.

The startup and failure fallback is the V5 initial tier (the compact receiver
surface), never the earlier native PBR: the legacy owner is dormant and never
revealed (R0033, owner decision DG-1 = B). After a valid terrain preview arrives
the initial tier is replaced, then refined using increasing angular orders.
`SalahMoonRuntime.state` reports preview/refinement/currentness/errors and the
`recovery` record. One worker is used, with cancellation and startup/refinement
deadlines. After a worker failure the runtime itself starts a new worker at most
three times per page lifetime (30 s, 2 min, 10 min; never while hidden; contract
and transport-identity failures never retry); those attempts revalidate cached
assets (`no-cache`), while the first boot prefers the cache. The QA driver's
`SalahMoonRuntime.retry()` keeps its own bound of three explicit attempts. If the
runtime cannot be constructed at all, no Moon is shown and no moonlight is cast
(`SalahMoonConstructionError`); see `docs/state-contracts/R0033.md`.
There is no UI-thread terrain fallback and no private astronomical clock.

## Data and outputs

`moon/assets/` is the compressed, lossless UInt16 terrain/material representation.
`moon/asset-manifest.json` pins compressed and decoded identities. WASM is supplied
and verified; applying/rebuilding does not require a compiler. C source is retained
for review. The internal source units are concatenated scripts, not independent
ES-module entrypoints. The static HTTP entry fetches compressed data in the worker.
The multi-file file entry uses generated local script chunks. The single-file
entry embeds those chunks inertly, retaining them for retry. The HTML entry is
large; all source data remain local, while original prayer/weather/fonts can
still use their ordinary services. Content security policy must admit the
intended scripts, Blob worker and WebAssembly; do not bypass site policy.

## Composition and calendar separation

V5 display mapping is applied once. Linear premultiplied lunar surfaces retain
independent coverage; a dark pixel must remain opaque to stars. The device-scale
lunar region joins the existing sky and native cloud field without duplicating
cloud transmission. Below-horizon calendar presence uses the separately declared
.020 × material token, not invented physical Earth/Sun energy. Atmospheric lunar
eligibility remains owned by CP9, not by the larger calendar disc.

## Tests / receiving qualification

Run `python tools/build_native.py` twice and compare the delivered postimage
manifest. `python tools/test_moon.py --output <outside-repo>` runs component tests.
Run `moon/tests/browser_check.py --transport navigation` separately for index.html
(HTTP) and offline.html (file), selecting the actual Chromium executable; the
harness uses controlled date/provider fixtures, not live weather observations.
`--quick` selects an explicitly small physical-reference test (not image-quality
certification). Omit it for the default 540px canonical terrain workload.

Preserve CP9's independently open N001/N002/N003, historical native comparisons,
platform gates and independent review. No research test or package receipt grants
merge/deployment permission. Requalify changed native runtime bytes. Do not rerun
all V5 high-order physics by default merely to apply a source-identical kernel.
