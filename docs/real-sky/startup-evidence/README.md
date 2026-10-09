# Celestial startup evidence index

This is selected evidence for the unmerged #33/R0021 startup Draft PR, specification
revision 1 / update 4. Read the [qualification record](../CELESTIAL_STARTUP_QUALIFICATION.md)
and [requirement matrix](../CELESTIAL_STARTUP_RLGWO.md) before interpreting PASS.
S1 strict timing/coverage, callback costs, actual extension-parent qualification
and S10/R0022-L1 remain open. These files do not authorize issue closure or release.

Baseline product: `18ff14860ff41c084b1db5f396bb62aa9c22b1be`, runtime
`f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260`.
Final candidate runtime:
`4c764068d0d19afe4d440376ed765a373c7afead594b5d16ef22402dd02ef799`.
The [inventory](RUNTIME_IDENTITY_FINAL.json), [preservation comparison](PRESERVED_RUNTIME.json),
[public baseline readback](SERVED_FINAL_READBACK.json), [copy provenance](PROVENANCE.json)
and `MANIFEST.json` distinguish source, built, captured and served identities.
The manifest hashes each selected file except itself; it is not a product gate.

## Ordinary first seconds

These videos start before navigation. They preserve normal CSS, the 330x534
iframe and 325x530 card at 1x. Weather/provider data is synthetic and the accepted
Date fixture advances at real 1x. No application getter or PNG request runs during
the first 15 seconds. Cold and reload share a page recording; new-tab has its own
recording. Use the navigation/source-clock receipts to locate each segment rather
than interpreting video time or the external rAF marker as navigation time.

| Engine | Baseline cold + warm reload | Candidate cold + warm reload | Baseline new tab | Candidate new tab |
|---|---|---|---|---|
| Chromium | [clip](clips/baseline-chromium-cold.webm) | [clip](clips/candidate-chromium-cold.webm) | [clip](clips/baseline-chromium-new-tab.webm) | [clip](clips/candidate-chromium-new-tab.webm) |
| Firefox | [clip](clips/baseline-firefox-cold.webm) | [clip](clips/candidate-firefox-cold.webm) | [clip](clips/baseline-firefox-new-tab.webm) | [clip](clips/candidate-firefox-new-tab.webm) |

The [measured budget results](TIMING.json) retain failures and uncovered intervals.
Normal-size first scene/Moon/star crops and contact sheets are in
[`timing/baseline-chromium`](timing/baseline-chromium/contact.png),
[`baseline-firefox`](timing/baseline-firefox/contact.png),
[`candidate-chromium`](timing/candidate-chromium/contact.png), and
[`candidate-firefox`](timing/candidate-firefox/contact.png).
Adjacent JSON files bind browser, fixture, resource/cache, navigation and source
clocks. The native recorder [receipt](capture-driver-receipt.json) describes the
isolated driver modification. The marker is parent performance milliseconds and
can freeze; filenames and requested screenshot times are not measured latency.
The [compositor diagnostic](compositor-clock.json) separately rejects expected
display estimates as evidence of actual presentation. Videos are resampled at
25 fps; missing native source frames are never filled with asserted product data.

## Initial, preview and final

- [Chromium complete compositions](transitions/chromium-contact.png) and
  [Firefox complete compositions](transitions/firefox-contact.png), with separate
  full frames and lunar crops in `transitions/`, bind to the [selection receipt](transitions/receipt.json).
  They come from instrumented lifecycle videos and qualify appearance, not startup
  latency. All preserve the original full composition, including the S10 defect.
- [Chromium lifecycle clip](clips/seal-chromium-lifecycle.webm) and
  [Firefox lifecycle clip](clips/seal-firefox-lifecycle.webm) reach current refined
  V5 at the final runtime. [Stage traces](STAGES.json) distinguish initial CPU,
  transport/decode, worker-row preparation, first pass, messages and publication.
- [40 retained-reference comparisons](initial/comparison.json),
  [DPR1 actual-footprint pairs](initial/actual-footprint-dpr1.png),
  [DPR2 pairs](initial/actual-footprint-dpr2.png) and
  [sampler byte-equivalence](initial/sampling-equivalence.json) qualify the bounded
  initial Moon. Gallery images retain their earlier consumer identity; exact-field
  equivalence plus the 40 final-consumer comparisons provide the explicit reuse
  bridge. No scientific final-terrain claim comes from these images.

## Matched controls and residual lighting

The [matrix summary](matrix-summary.json) links through case names to `matrix/`.
Each directory contains the exact runtime, compact original receipt and final
full-composition PNG; lifecycle cases also contain settings-open captures.
The 30 cases cover both engines, DPR1/2, clear/partly cloudy/rain, physical lunar
negative, dawn/day, accepted versus acquiring location, prayer delay, real cache
reuse, direct/iframe/file/offline-file and missing/delayed/retried full assets.
The [rain clip](clips/final-firefox-rain.webm) is an earlier `d1255df4` control,
not relabelled final-runtime evidence. The qualification record explains reuse.
Generic iframe capture does not verify the owner's unavailable extension parent.

The owner's two glow images are unchanged baseline; see the
[attachment binding](OWNER_GLOW_ATTACHMENT_BINDING.json). Original/recomposed,
single-layer and restored full controls are retained in `glow/` for both baseline
and candidate. The [pixel attribution](GLOW_PIXEL_ATTRIBUTION.json) shows that
removing the physical lunar atmospheric field removes the left concentration and
most grey wash. The removal is **diagnostic only**, never a repaired-widget target.
[Baseline full](glow/baseline-full-control.png),
[candidate full](glow/candidate-full-control.png),
[diagnostic removal](glow/candidate-no-physical-lunar-field.png), and
[restored full](glow/candidate-restored-full.png) must be judged together.
The existing [R0022-L1 increment](../R0022_L1_DISPLAY_INCREMENT.md) specifies the
remaining display/registration investigation and acceptance; S10 stays open.

## Checks and rejected evidence

[Focused tests](checks/seal-focused-tests.log): 679 passed, zero failed, four
inherited TODOs. [Seven predicate controls](checks/seal-first-scene-controls.log)
use synthetic timestamps only. [V1 preservation](checks/seal-frozen-v1.log),
[two builds](BUILD_DETERMINISM.json) and [derivative reproduction](DERIVATIVE_DETERMINISM.json)
pass. [Command receipts](verification-progress.json) record exact executables,
arguments, start/end times and exit status. There is no claim of GitHub CI.

Retained failed boot/day fixture logs show tests that initially failed to advance
the newly explicit rendering/task boundary. Their corrected fixtures advance
the boundary without changing production timing or weakening ownership assertions.
The original control-flow assertions, old driver/protocol failure, impossible
Hijri fixture, discarded coarse/no-shadow lunar probes and rejected compositor
estimates remain classified in the qualification record and local custody.

Full custody, including raw native frames, CPU/compositor traces, prior candidates,
rejected runs, full retained reference fields and disposable browser profiles:
`C:/Users/theis/Documents/Codex/celestial-startup-repair-20261008`.
This portable selection does not pretend to contain every intermediate byte.

## Focused reproduction

Use the installed versions recorded in receipts. Do not clear the owner's profile
or replay long terrain work merely to regenerate reports. Choose a fresh evidence
directory and obtain the single-machine browser/terrain lease first.

```text
python tools/build_native.py
python tools/verify_v1.py --negative-control
python tests/real-sky/first_complete_scene_test.py
node --test moon/tests/initial.test.cjs tests/real-sky/native-bootstrap.test.mjs tests/real-sky/native-startup-critical-path.test.mjs
python tools/cp9/celestial_startup_check.py --root <verified-checkout> --out <fresh-output> --scene clear --entry iframe --dpr 1 --persistent-profile --modes cold,warm-reload,new-tab --video --video-only --duration 18 --driver-node <recorded-node> --driver-cli <isolated-recording-driver>/cli.js
python tools/cp9/review_startup_frames.py <capture-output>
```

Set `SALAH_BROWSER`, `SALAH_BROWSER_EXECUTABLE` and `SALAH_CAPTURE_NATIVE_FRAMES=1`
explicitly; use `prepare_capture_driver.py <installed-driver> <fresh-copy>` for the
recorded driver family. It refuses unsupported source anchors. The full focused
test list is in the command receipt. `--trace --lifecycle --duration 120` is a
separate causal/control run; `--cdp-filmstrip` is Chromium-only diagnostic work.
No browser APIs, trace annotations or app publication clocks substitute for
ordinary first-seconds pixels or missing coverage.
