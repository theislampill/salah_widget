# R0017 — replacement map for five inherited synthetic-star exclusions

## Result and limit

The four permitted source/VM suites passed **19/19 tests**, with no failures, cancellations, skips, or TODOs. One serial Node command exited **0** in **8.306070104 seconds** of monotonic wall time, within its 90-second bound. This run establishes the specific assertions below. **It does not fully replace any of the five historical cases.** Preserve all five as explicit historical exclusions with the individual residuals in this report; do not add them to the 19 passing tests or describe their replacement coverage as complete.

No browser, native-pixel, full-worker scene, provider, delivery, or heavy rendering campaign was run. No product/test assertions were edited. The only worktree population was acquisition of six exact current-HEAD prerequisite files, authorized by root. No old bytes or generated-core substitutes were used.

## Source and execution custody

- Checkout: `/workspace/scratch/7a8daf93afaa/r0017-explicit-work`.
- HEAD before and after the run: `f71fef6ccf7e4efcb57b5a26688d2360461a3253`.
- HEAD tree: `79aedcac840d624b5ea423922314f0832dc3f750`.
- Execution: 2026-11-07 03:39:56–03:40:04 UTC; Node `v24.22.1`; Linux x86_64; Python `3.12.14` timing wrapper.
- All **58 recorded files** matched their inspection hashes before launch and remained identical after the command. This includes the 44-module static relative-import closure, the two data inputs, and the additional source/case definitions used for the mapping. The full records are in `dependency-inspection.json`, `pre-run-files.json`, and `post-run-files.json` under the evidence directory. Concurrent runner/adapter changes elsewhere are outside this stability claim.
- The missing prerequisites were four vendor modules totaling 22,320 bytes, the 1,113-byte runtime manifest, and the 5,511,897-byte bright-star catalogue. They were first inspected from exact HEAD Git objects and then populated by six explicit sparse-checkout patterns. SHA-256 equality was verified before execution. No registered-starlight tiles or large historical research tree was acquired.
- An initial `git sparse-checkout add --no-cone ...` attempt returned 129 because this Git version does not accept that option on `add`. The worktree was already in non-cone mode; the supported `git sparse-checkout add` command succeeded. This was an acquisition-command correction, not a test failure.

Reproduction command, run from that checkout:

```sh
node --test --test-reporter=tap --test-concurrency=1 \
  tests/real-sky/native-star-preview.test.mjs \
  tests/real-sky/native-host-streams.test.mjs \
  tests/real-sky/cp9-scintillation.test.mjs \
  tests/real-sky/native-bootstrap.test.mjs
```

The complete merged stdout/stderr is `evidence/star-replacements/selected-four.tap.log`; exit, timing, command, tool versions, timeout, input acquisition, and hash metadata are in `selected-four.run.json`. TAP itself reports 8,183.908962 ms; the 8.306-second figure includes process-launch/wait overhead and is the measured command duration. Neither duration is a browser performance claim.

## Why the synthetic cases are historical

The actual generated `index.html` replaces the authored synthetic producer. `tools/build_native.py` lines 48–64 replace the `PROJECTED STARFIELD` block with an empty `_starEls` array, an acceptance-key `projectStars`, a no-op `refreshStarAppearance`, and `buildStars` that clears `.stars`, `.starglints`, and `.milkyway`. This replacement is present around `index.html` lines 5507–5516. The builder also hides those old groups. The authored `src/native/index.html` still contains the legacy producer, so inspecting the authored file alone would give the wrong deployed-owner conclusion.

The old case bodies read `_starEls` or `_glintEls` and compare DOM coordinates/transforms/opacities. An unchanged empty star array could make a positional equality vacuously green; the old glint array is absent in the generated replacement. Excluding these obsolete array consumers is justified. That fact alone does not prove the replacement scene behaves correctly.

The current caller chain is concrete:

1. `SalahNativeSkyHost.capture()` in `real-sky/native-host-hooks.js` supplies accepted `simNow()` UTC, coordinates, generation, scene identity, camera and weather. `notify()` requests the refined renderer. It does not pass the legacy decorative `SIM.moon` value as the physical Moon state.
2. `nativeJob()` in `real-sky/native-contract.mjs` validates the snapshot and retains its UTC/observer. `nativeResultCurrent()` requires matching native identity and at most 30 accepted-UTC seconds of age.
3. `renderNativeBackgroundPreview()` in `real-sky/native-preview.mjs` computes physical sky state from that observer and derives lunar/solar/background radiance and exposure. It does not simply reuse the old per-star opacity wash.
4. `NativeStarPreview.render()` in `real-sky/native-star-preview.mjs` calls the real `projectCatalogue()` on the current job, then uses physical Moon occultation, spectral flux, atmospheric transmission and the reference PSF. `joinNativeStarPreview()` joins the stellar field to the background; `nativeStarPreviewRegion()` applies the calendar mask.
5. `prepareNativeFirstPaint()` uses the independent bootstrap for an admitted ordinary snapshot. `startNativeSkyPreview().update()` captures fresh host inputs and calls the preview/catalogue/compositor chain. Publication rechecks currentness. The refined `startNativeSky()` uses `NativeSkyLifecycle` and a worker, then composes the accepted result. The four executed suites call the numerical modules and the encoder directly; they do **not** execute these browser/worker publication paths.

## Executed case index

IDs below are report references to the exact TAP case names, not new tests.

| ID | Exact existing case | What its assertions establish |
|---|---|---|
| B1 | `real bright sources can be admitted without requesting or parsing the full pack` | `fromBootstrap` admits 921 approved bright records, preserves their consumed astrometry/spectral fields and catalogue/seed identity, and keeps the seed below 130,000 bytes. The test derives its fixture from the full catalogue; it is not a network interception test. |
| B2 | `bootstrap uses exactly the approved preview photons for independent observer/time controls` | For three explicit observer/time snapshots, bootstrap and full-catalogue preview produce byte-identical linear stellar fields. It proves equivalence at those snapshots, not an old-to-new host transition. |
| B3 | `independent bootstrap refuses tampering, wrong ancestry, empty and nonfinite records` | Wrong hash/size/ancestry, empty rows, null RA, and excessive magnitude are rejected. |
| S1 | `asynchronous catalogue admission keeps exact pinned sources and rejects equal-length tampering` | Sync/async catalogue and identity match; their stellar field at the same job matches; equal-length catalogue tampering and altered catalogue/manifest sizes fail. |
| S2 | `separable preview PSF preserves every reference linear sample, including fractional and clipped sources` | Synthetic controlled point sources produce exactly the reference renderer's linear samples, drawn count, and encoded output at four exposures. This tests the numerical PSF, not the current catalogue caller lifecycle. |
| S3 | `current bright-catalogue stars return through apparent contrast, without a solar/prayer switch` | At four accepted UTCs around twilight, diagnostic UTC matches input, sources respect magnitude ≤4.5, daytime adds no visible stars, and later twilight/night gains visible stellar contrast. |
| S4 | `preview rejects corrupt catalogue and preserves opaque lunar cutout plus once-only clouds` | Catalogue corruption rejects; a zero calendar mask removes distant sources while retaining foreground atmosphere; an opaque cloud covers stars with exact cloud bytes. This is calendar occlusion/cloud composition, not a Moon-phase wash transition. |
| S5 | `sparse preview encoding and moving lunar mask equal the full linear compositor byte for byte` | At three times, prepared RGBA equals full encoding, and a prescribed fractional/opaque mask region equals the full calendar compositor. It does not drive a real DOM Moon transform over time. |
| S6 | `daylight work culling uses an encoded contrast bound and preserves the exact displayed result` | Full and contrast-bounded previews match displayed bytes across four snapshots; daylight is culled where provably invisible, while midnight retains actual star work. |
| S7 | `display preparation does not allocate unused full raw sky planes` | Prepared output has bounded raw-plane allocation, exact atmosphere and combined raw fields, exact encoded bytes, and stable repeated access to the same raw field. |
| S8 | `prepared sky owns its source bytes and stars; later inputs cannot alter lunar masks or raw fields` | After caller-owned background and star inputs are overwritten, the prepared frame retains saved atmosphere/stars and correct mask/raw results. |
| S9 | `unused malformed stellar tail is rejected before any displayed frame can be prepared` | Invalid final stellar channels are rejected even when marked below display-byte resolution. |
| C1 | `native disabled scintillation uses the real strength contract, not an ignored enabled flag` | `nativeJob(..., true)` supplies options to the actual vendor `scintillationFactor`; three source IDs at four times return exactly 1 with reduced motion explicitly false. This proves disabled modulation, not glint wash or geometry. |
| H1 | `per-call intervals cross all oracle edges forwards/backwards after repeated hits` | Native encoding matches the oracle across all transition edges and multiple exposures, without mutating raw inputs. |
| H2 | `private destination writes only its declared region and preserves exact return identity` | Encoding writes exactly its specified destination span and preserves prefix/suffix bytes and return identity. |
| H3 | `finite-product overflow saturation and neutral channels survive an interval hit` | Overflow/neutral-channel output remains oracle-exact at the tested exposures. |
| H4 | `invalid channels after an interval hit still reject without a successful result` | Nonfinite channels cannot be hidden by the encoder's previous-interval optimization. |
| H5 | `destination alignment/range/type and invalid exposure/dimension reject` | Malformed destination, offsets, exposure and dimensions reject. |
| H6 | `boundary comparison and destination-offset mutations are killed by exact controls` | Actual encoder-fragment mutants for an inclusive boundary and lost offset are detected. These are encoder guards, not star-owner or lunar-light guards. |

B1–B3 are in `tests/real-sky/native-bootstrap.test.mjs` (lines 18, 32, 42); S1–S9 in `native-star-preview.test.mjs` (15, 26, 36, 45, 55, 67, 79, 94, 103); C1 in `cp9-scintillation.test.mjs` (5); H1–H6 in `native-host-streams.test.mjs` (7, 12, 18, 22, 25, 31). All nineteen passed in the recorded command.

## Mapping each inherited exclusion

### 1. `ordinary held star positions remain stable across a healthy render`

**Selected source:** `tests/r0021-reveal.cjs`, lines 14–17, under `--cp8-snapshot-only`.

**Old observation:** Run the actual native render, advance ordinary wall and monotonic clocks by 60,000 ms, render again, and require identical `_starEls` display/cx/cy values.

**Replacement coverage:** S8 is a direct useful current-owner assertion that a prepared stellar snapshot cannot be changed by later caller input mutation. S7 additionally verifies stable raw-field access. S1 gives same-job equivalence across catalogue admission paths. C1 excludes a disabled modulation source. These establish numerical determinism and ownership of a prepared frame; none runs two ordinary native renders and compares current catalogue positions.

**Applicability and residual R17-STAR-01:** Literal synthetic-DOM immobility over a minute is historical. Current numerical stars are projected from accepted UTC, and currentness rejects a frame older than 30 accepted seconds; imposing minute-long physical immobility would not preserve the current contract. The unproved retained observation is that actual ordinary host publication uses the correct accepted scene and only legitimately current catalogue geometry, without accidental stale reuse or unintended changes. No full current-caller replacement proof was executed here.

### 2. `first accepted target cannot retain the unresolved-coordinate projection`

**Selected source:** `tests/r0021-reveal.cjs`, lines 18–20.

**Old observation:** Build stars with null coordinates, adopt valid coordinates, render, then compare its array positions with an explicit `projectStars(simDate())` call.

**Replacement coverage:** B1/B3 and S1 prove admission of real pinned catalogue sources and rejection of malformed inputs to that admission. B2 proves bootstrap/full projection equivalence at valid observers. The inspected current `nativeJob` rejects missing coordinates, and preview `update()` clears unavailable accepted input before constructing a fresh job. These are relevant mechanisms, but the executed four suites do not drive an invalid-observer state followed by the first valid target through the real host and catalogue publication consumer.

**Residual R17-STAR-02:** The actual unavailable-to-first-valid target transition with real catalogue output remains unexecuted in this evidence. Valid-source admission or equality of two valid numerical paths cannot establish that stale unresolved output is absent at publication.

### 3. `same-day explicit preview anchor correction reprojects accepted stars`

**Selected source:** `tests/r0021-reveal.cjs`, lines 21–23.

**Old observation:** After a render, advance `_simBase` by one hour on the same day, render again, and compare its array positions with manual current projection.

**Replacement coverage:** S3 exercises the same catalogue preview renderer at four UTCs, checks reported UTC and actual changing visible contrast. B2 compares actual bootstrap/full fields at three independent observer/time inputs. In source, `skySceneIdentity()` includes the explicit anchor fields, `capture()` supplies `simNow()`, and `NativeStarPreview.render()` projects the current job's observer. The tests nevertheless supply snapshots directly; they do not edit `_simBase`, follow its accepted host identity, or observe the replacement native publication.

**Residual R17-STAR-03:** A same-day explicit anchor seek through the actual host to newly projected catalogue output, including rejection of a pending old completion, is not established by this four-suite run. Timestamp diagnostics alone cannot discharge that causal transition.

### 4. `glints release wash with held star projection`

**Selected source:** `tests/r0022-lunar-consumers.cjs`, lines 59–66, under `--cp8-snapshot-only`.

**Old observation:** In an ordinary fixture, render `SIM.moon = "1"`, hold glint transform positions while advancing 60 seconds and changing `SIM.moon = "0.01"`, and require different glint opacities.

**Replacement coverage:** The synthetic glint producer is removed. C1 proves that the current native strength contract disables the optional scintillation factor. S3 proves that current catalogue stars respond to apparent background contrast, and S4/S5 prove exact calendar-mask/cloud composition. None compares full-Moon versus near-new-Moon atmospheric light or drives a wash-release transition. Scintillation, opaque calendar masking, and lunar-background wash are distinct effects.

**Residual R17-STAR-04:** The obsolete synthetic glint animation/opacity case is not applicable. The still-meaningful current observation—accepted physical lunar-background changes reach apparent stellar contrast without stale wash or an extra per-star dimmer—remains unproved by these suites. Changing the decorative `SIM.moon` field is not itself a substitute for controlling the current physical Moon/background owner.

### 5. `ordinary render refreshes star appearance while held projection stays fixed`

**Selected source:** `tests/r0022-lunar-consumers.cjs`, lines 90–97.

**Old observation:** Render synthetic stars under full-Moon simulation, advance ordinary clocks by 60 seconds, change to near-new-Moon simulation, require unchanged cx/cy and changed opacity.

**Replacement coverage:** S3 supplies a real catalogue/background/compositor contrast positive across different UTCs. S4/S5 establish exact one-time foreground/mask treatment, S8 preserves prepared input ownership, and H1/H4/H6 exclude several encoder cache/validation errors. These are real controls against stale or malformed numerical output. The encoder suite imports `native-host.mjs` but calls only encoding functions; it does not run `startNativeSky()` or prove a renderer lifecycle.

**Residual R17-STAR-05:** No executed test holds or refreshes a current catalogue frame through the ordinary host while changing the accepted physical lunar background and proving the appropriate appearance change. The old “fixed positions after one minute” subassertion belongs to removed synthetic behavior; current accepted-UTC geometry must remain governed by the present physical/currentness contract. A meaningful replacement must test fresh appearance at the correct accepted scene, not reintroduce synthetic opacity or freeze physical time.

## Additional existing tests inspected, but not executed here

These are precise candidate coverage, not new PASS evidence:

- `native-contract.test.mjs`: `invalid/missing observer or scene is not coerced to a valid sky` rejects null/nonfinite coordinates, UTC and scene; `new target rejects a late prior-generation result` tests the actual identity guard. These directly support parts of R17-STAR-02 at the contract layer, without catalogue pixels.
- `native-lifecycle.test.mjs`: `invalid input clears and cannot retain old diagnostic authority`, `A→B obsolete successful completion cannot paint A`, and `short explicit seek changing native anchor also fences` invoke the actual `NativeSkyLifecycle` with controlled worker completions. They address stale transition authority for R17-STAR-02/03, but returned rasters are doubles and do not prove current stellar projection.
- `native-preview-host.test.mjs`: `catalogue admission preserves the current atmosphere and defers first stellar paint to a separate native turn`, `invalid catalogue cannot become the displayed identity or defer currentness validation`, `late catalogue hash completion cannot resurrect a revoked asset admission`, and `first frame and full-pack reset/failure retain the independent same-catalogue bootstrap` exercise the actual host function with catalogue/render/currentness doubles. Their assertions concern admission, publication identity and scheduling; they do not prove real sky geometry or lunar wash.

Their hashes are included because their actual case bodies informed the residual assessment. No test outside the four authorized files was executed, and no existing product/scene failure was suppressed or reclassified as success.

## Recommended exclusion records

Each record should retain its exact legacy case name, `HISTORICAL_EXCLUDED` applicability, the removed producer/consumer explanation above, the relevant executed case IDs, the applicable residual ID, and this run's log/manifest identity. A result may truthfully say that the current replacement modules have these specific passing controls while broader scene observations remain residual. It must not say that all five observations were passed, that file-name similarity is replacement coverage, or that the 19 tests qualify all native/browser lifecycle behavior.

No source change is proposed by this report. The residuals preserve evidence limits for the R0017 evaluator and the relevant existing product owners; they are not requests to waive assertions or expand this task into a new browser campaign.

## Complete input SHA-256 manifest

The JSON manifests also retain byte sizes, observation times, and the import graph. The hashes below are the identical pre/post-run content identities.

| Path | SHA-256 |
|---|---|
| `index.html` | `b4a6831b80439d3002f9cf4fae5bc15943bc9f9f2fa5ab0c4a1fc09f33a57298` |
| `real-sky/core/integration/physical-sky-bridge.mjs` | `af2499993ed15fae7d96ab8704d8fc009bd528e7d9e573c73c79ffe400dd31b1` |
| `real-sky/core/integration/resilient-sky-bridge.mjs` | `e3a1df8e71557db25dd67fb216c360b352229eea35daac89e5a2540983e16b03` |
| `real-sky/core/src/astronomy.mjs` | `491c39dfc4ca12caeec3cc782d8658486f8b41d5ed543daf7e550a8ae7dffff4` |
| `real-sky/core/src/atmosphere.mjs` | `0d1f5a2c80cee47f23d6bd9ae619f003a720aba91a380d077dc84f46165aa54b` |
| `real-sky/core/src/catalogue.mjs` | `94039a57ec47ba3a610c1090b92db325b1e8f8dfa9abef0c3ef2a9fb2faf4651` |
| `real-sky/core/src/diffuse-assets.mjs` | `bf5780ff51a5d41a7f55f839a6ecd8eed6838fa740d4421bc8fdba730a2e8fda` |
| `real-sky/core/src/diffuse-binding.mjs` | `4f5cec34192c8d767d569e2acf2692974fa6d9b46a7dccaf4fa117b84f938847` |
| `real-sky/core/src/diffuse-manifest-pin.mjs` | `c16720ded16cfaf59193e589cee967f9ccf51621bb1e08fa49538843ccca524b` |
| `real-sky/core/src/diffuse-map.mjs` | `b7700bd0c21412f2a61896ca8174d547de7ce3ff475bbd9fc5c935179ab320e4` |
| `real-sky/core/src/diffuse-transport.mjs` | `cb1542f765de523bbf690d7a7b1e8f68bb871bd6a0a86338390d15c4ef85f60c` |
| `real-sky/core/src/latest-render-queue.mjs` | `4652ba4ed7e6bce0116ea1eb942382571061233b6248dc2fdba9d373d8395c6b` |
| `real-sky/core/src/optics.mjs` | `e37c5ae9a4a415d8fecf849cc252abd4267dfeb2e10de395a45a423bab287007` |
| `real-sky/core/src/photometry.mjs` | `c8ae1c83a4fea1511dbd8ce99eb39e8cbfcf6d7745547fffc0258eb1b051d1c1` |
| `real-sky/core/src/physical-sky-renderer.mjs` | `dba25c04f0d1fa65d660fb12dd8d000b7822c38575d6d5efe676441c34da228a` |
| `real-sky/core/src/projection.mjs` | `d76857e2b12889f2848a62861aab4c089cf86fce1559a343036e096765438343` |
| `real-sky/core/src/reference-engine.mjs` | `27fbebcdc32a5c80045d68aa6de465e5e583ab641c8e3fd8e18ed1c9b12d5d21` |
| `real-sky/core/src/reference-worker-client.mjs` | `14502bd262729946a31a6840bdd47d4850cc009b0a37db2d6b474f8793a677c4` |
| `real-sky/core/src/registered-starlight.mjs` | `002756be1f560b9453505fb4ad0b0206897ce1d354e9ed9d74de6412d2d55366` |
| `real-sky/core/src/renderer.mjs` | `173283b65c4b89cd1c85067131183ad2a306199850f41ae070ede463de5add6b` |
| `real-sky/core/src/scene.mjs` | `62f0087c66fceda50c380bdeb6843ad57c4b38299ea74567bc2269752712869d` |
| `real-sky/core/src/sha256.mjs` | `6888c4de48f19a3e7a7380d1c7e846dd4e70f08ce656cc82f1c5bfedcc00c4d8` |
| `real-sky/core/src/sky-background.mjs` | `7001d7cc8c68a24ea8320205bfbe297526a4e75abcc06d4f25c3ed2ca56ba6bf` |
| `real-sky/core/src/sky-state.mjs` | `4f3187db2fb967cb09c3a6a261c0fd351b5afbb9e195d7dbb3da473e0b2f2ab7` |
| `real-sky/core/src/spectral-tables.mjs` | `294dbc1e815a47883aa31c66ef22c2191a31646dfc029e79925e581c7511672a` |
| `real-sky/core/src/spectral.mjs` | `565517270e1cb313e72875409b93199e38237c7b74ed1b452a52ccd6b889120b` |
| `real-sky/core/src/time-scales.mjs` | `2c02d0edfff55973b7ea6fe393d9ec3c7107dce99218b98dc84ad5d6606aeb0b` |
| `real-sky/core/src/visibility.mjs` | `6434a518da871470e007869f64ca42283cb4f79c2816c5763569004ac9aebf61` |
| `real-sky/native-cloud-transfer.mjs` | `a1c9c9cb3f2701623ae4091bce095f5ecd228ad4e91f58e50a1075e9607e7fb3` |
| `real-sky/native-composition.mjs` | `2bbf63a755258bca8fd54f1b164457ee65c9c07a7e7ff9f4b85d2cbef6001a59` |
| `real-sky/native-contract.mjs` | `91e6f44fbffa5f9d49ce49afd610dba0acd1341b894a2af461adb39be8398d1b` |
| `real-sky/native-encoding.mjs` | `48ecb0b15bb40ea1fcb7259ba65b7bf59ddc7ad4a4d1b02188760994e70b6710` |
| `real-sky/native-first-paint.mjs` | `a75ffceb5d8268c633722a67b852c9bd0427ad389d99100e4ba62597cef52452` |
| `real-sky/native-host-hooks.js` | `007529ccb3a3ba73e14fd739e9fbaa9b2030e66e56ca6b2c997ffaa578b6d6eb` |
| `real-sky/native-host.mjs` | `bc869547ac1ba78502e5546b6ca224340347ab95d18d6c6380013b6e5278359f` |
| `real-sky/native-lifecycle.mjs` | `dbe987b7459508e48be149c4446ad090ac0490f6b49d21bd98aa3b09051e5880` |
| `real-sky/native-preview-host.mjs` | `04df3eb1a418c1c06065756b22b1fc6545d2d4ad1c4fdfc644de15b5dec7c2e3` |
| `real-sky/native-preview.mjs` | `e4f70bd5935b31ffd56deff017e854b0afcd192f8937090b8140773af61fce0f` |
| `real-sky/native-star-preview.mjs` | `c91f6558aa2c50eae02069068b950e0d5df348528980496b1806e3670a2dd527` |
| `real-sky/native-worker-policy.mjs` | `bdd47f85b46e6bfa89e3af17970e2665e700831e77359b82c8ec782d565bc9f9` |
| `src/native/index.html` | `6054f1eb3e7f04aa5975707345810b64fc824bc99e17ce3798369a959a123fad` |
| `tests/r0021-reveal.cjs` | `c66a0b967fd2de957c656f33ad32d9b84099ed7e3ce7f4c0841ac780918f76ca` |
| `tests/r0022-lunar-consumers.cjs` | `eafa452f29e6b047d6b9eadefd5f18dc9acedf0340b0af55d5c386d0d5f971cd` |
| `tests/real-sky/cp9-scintillation.test.mjs` | `ee0673896e28bc92228e18e69c574078e165ddd8a4d9aa8ae3b3bfbd192e1b00` |
| `tests/real-sky/native-bootstrap.test.mjs` | `8d751384617ada639c488eb5a4b2c0faad8ef9d80979236b6a8b1090f883782c` |
| `tests/real-sky/native-contract.test.mjs` | `c77c58ff04752e60d525c6e289681a3f4132c83fcb3efcdb66dbe06d1168e449` |
| `tests/real-sky/native-first-paint.test.mjs` | `9337afd8b124e14668c80c4e3b81aa30ca9e5f0f42102be6b9bf4b1702303e87` |
| `tests/real-sky/native-host-streams.test.mjs` | `5095e9b3da478ec286616bb8c655b4da22afd51b0e90c98a0d831280da0b09ca` |
| `tests/real-sky/native-lifecycle.test.mjs` | `cab8ade0346eb097cb3c64e65cf8b3828e2447d2a9f368da3cce4bfd0c947026` |
| `tests/real-sky/native-preview-host.test.mjs` | `6f5151d5075448589c97c8c93f9f74736ffc6b286ea359f93fa7a4e113923fdd` |
| `tests/real-sky/native-star-preview.test.mjs` | `c8ce5ed6d5ee0e99947267c2399fca0e1a64e5703fc9666218f32d05bad8adc4` |
| `tools/build_native.py` | `a0635c58da3d47b421fc4f703361a1b10b6017f67f6cca352db1fc6b0f1c9366` |
| `vendor/real-sky/data/bright-stars.json` | `da5002f0eda9ad3e0f2cc7c95ab423043feea61e8522239d2930ca1945beef2e` |
| `vendor/real-sky/data/registered-starlight/runtime-manifest.json` | `630f169f30b617d947b5e3199eb854e8027a34540dde008da57b925577b777f6` |
| `vendor/real-sky/src/astronomy.mjs` | `491c39dfc4ca12caeec3cc782d8658486f8b41d5ed543daf7e550a8ae7dffff4` |
| `vendor/real-sky/src/photometry.mjs` | `c8ae1c83a4fea1511dbd8ce99eb39e8cbfcf6d7745547fffc0258eb1b051d1c1` |
| `vendor/real-sky/src/time-scales.mjs` | `2c02d0edfff55973b7ea6fe393d9ec3c7107dce99218b98dc84ad5d6606aeb0b` |
| `vendor/real-sky/src/visibility.mjs` | `6434a518da871470e007869f64ca42283cb4f79c2816c5763569004ac9aebf61` |

## Evidence artifact digests

| Artifact | SHA-256 |
|---|---|
| `evidence/star-replacements/inspection-start.json` | `6f798d014e4da52f20297dcd841134a96e041e3dbcde42a3264f9419030d1171` |
| `evidence/star-replacements/dependency-inspection.json` | `cc8c48f9870b2a1aaae02a81db3fd0f7d5a4bdafbc5ee1e42545c9991f20d4fa` |
| `evidence/star-replacements/pre-run-files.json` | `65ba39cd927253d2d20373bc3633aa40a5a74520fecd49edb0e4888a196e46f2` |
| `evidence/star-replacements/post-run-files.json` | `18159be4540481182597a754e90722267096b16a1dce3608507f37f629656a78` |
| `evidence/star-replacements/selected-four.tap.log` | `5e184cf2dd852950e2d9b4093709f5669b466a2a9f71cbd43d58937140e84b57` |
| `evidence/star-replacements/selected-four.run.json` | `9e07c4d04f835a68cdd6b86bd74874e91a612fdea0497b8192ead83f90430102` |
