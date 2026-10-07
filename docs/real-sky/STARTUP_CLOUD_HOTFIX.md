# Current-widget startup and cloud repair

This repair targets deployed main `c1a480c97e9af188cf57704502d818c0584cf265`
(tree `beb1c39ddc750c22e7276f2ca8a1f8c58bd44d16`). Public index, config,
sky bundle/CSS and Moon host matched that source byte-for-byte at intake.
It does not deploy itself. The repair PR head is the publication pin; main and
the frozen V1 remain unchanged until an owner merges it.

Runtime inventory SHA256:
`90576a5396548e1deb3f0bcf405f0d2a824113181d3a0f189f51b09bd20c63f5`.
The [evidence index](evidence/startup-cloud-20261007/INDEX.json) binds retained
captures, receipts and the runtime inventory. Historical donor byte-identical
receipts do not qualify these deliberately modified postimages.

## Diagnosis and repair

**R1:** before the first physical frame, the CSS exposed the old blue themed
background, grain and weather veils. Acceptance then replaced that entire
presentation about 2–3 seconds into the controlled load. Separately, the prayer
progress bar's first assigned width animated from zero for 0.9 seconds. It was
prayer progress, not an intentional loading indicator.

The current shell now owns the background and overlay policy from stylesheet
application, including loading, invalidation and recovery. It uses the existing
neutral pending background. A valid physical frame adds the sky through a
180 ms opacity transition (none under reduced motion), driven by acceptance,
without a timeout or withholding the prayer UI. Invalidated light is hidden
immediately. The first prayer width is hydrated without animation; subsequent
clock updates retain the existing transition. Native Moon loading/failure
fallback and the V5 preview/refinement lifecycle remain available.

**R2/R3:** native clouds are painted into an 8-bit premultiplied canvas, then
read back as unassociated RGB. At low alpha, rounding can recover channels of
255, sometimes different channels in adjacent pixels. The old join inverted
the HDR tone map *before* multiplying by coverage. It interpreted those rounded
channels as very bright radiance, producing coloured edge beads and crawling
noise. This reproduced in Chromium and Firefox; it was not random worker data.

Cloud colour now joins in bounded display-linear light, using the same source
alpha once. For scene channel `L`, exposure `E`, decoded cloud colour `C`, alpha
`a`, the displayed channel is `(1-exp(-E*L))*(1-a) + C*a`. Its bounded inverse
feeds the existing shared encoder. Zero cloud alpha preserves the original
scene channel exactly. Both the base sky and device-resolution Moon use this
one authored operator. There is no added blur, new noise, exposure change,
texture replacement, DPR change, or cloud-motion suppression.

The host prepares and validates the whole foreground update before publishing
pixels. A malformed capture retains the last coherent frame only while that
frame's original generation/epoch/scene and 30-second age fences still pass.
It is never retained across a seek, configuration change or invalidation.

## Authored ownership

| File | Change |
| --- | --- |
| `src/native/index.html` | First prayer-progress hydration only |
| `tools/build_native.py` | Current startup CSS and shared transfer bundling |
| `real-sky/native-cloud-transfer.mjs` | Bounded display-colour join and RGBA validation |
| `real-sky/native-composition.mjs` | Base sky/cloud consumer |
| `real-sky/native-host.mjs` | Atomic foreground publication and bounded good-frame retention |
| `moon/src/moon-detail.mjs` | Same cloud operator for the device-resolution lunar footprint |
| `tools/build_moon.py` | Bundle and hash the shared cloud owner |

Generated `index.html`, `offline.html`, native sky bundle/CSS, Moon host/worker
and `moon/BUILD.json` were regenerated. The numerical kernels, terrain/data,
phase precision, currentness scheduler, star catalogue and native cloud painter
are unchanged. The Moon worker changes because its existing build also includes
the detail module; no numerical terrain function changed.

## Qualification boundary

Windows Chromium 148.0.7778.96 and Firefox 150.0.2 were exercised with the real
330×534 iframe, plus direct entry, cold contexts and warm navigation, bright
and dark cloud cases, and DPR 1/2/3. Central Florida reproductions use assumed
Orlando coordinates, controlled October 7–8 time, provider fixtures and retained
fonts. They are not claims about live Florida weather or provider accuracy.
Dates in inherited Moon/horizon fixtures intentionally differ. Warm navigation
retains the browser context and storage; request routing disables the HTTP
cache, so this is not a cache-warm network timing claim.

The deployed implementation fails the startup-shell, first-progress, cloud
transfer and bad-capture controls. The one-alpha-byte magenta control changes
from `[60,0,60]` to the independently calculated `[13,0,13]`. Paired moving-cloud
captures and exact scalar references isolate the colour amplification from
legitimate cloud motion. Per-case receipts record edge changes and errors.

| Actual entry | DPR | Maximum old → repaired edge step |
| --- | ---: | ---: |
| Chromium day iframe | 1 | 132 → 52 codes |
| Chromium night iframe | 2 | 104 → 29 codes |
| Chromium day direct | 3 | 131 → 41 codes |
| Firefox day iframe | 1 | 136 → 47 codes |
| Firefox night iframe | 2 | 77 → 25 codes |
| Firefox night direct | 3 | 77 → 28 codes |

These comparisons replay the *same* moving native cloud samples through the
old and repaired joins, over a fixed dark background, at alpha ≤ 8%. Every
repaired case has zero code error against the independent display reference.
They measure the removed amplification, not an assertion that moving clouds
never change pixels. The screenshots below use separate actual-widget runs;
their motion is not phase aligned. Enlarged crops use nearest-neighbour scaling.

![Cloud edges before and after](evidence/startup-cloud-20261007/screens/cloud-before-after.png)

[Moving before/after crops](evidence/startup-cloud-20261007/screens/cloud-motion-before-after.gif),
[deployed startup](evidence/startup-cloud-20261007/screens/before-startup.png),
[repaired Chromium startup](evidence/startup-cloud-20261007/screens/after-startup.png),
[repaired Firefox startup](evidence/startup-cloud-20261007/screens/firefox-after-startup.png).
The repaired startup captures deliberately show the neutral current shell
before the accepted physical sky; final sky pixels are not claimed immediate.

The focused browser logger combines continuous DOM observations with actual
compositor screenshots. Firefox may suppress an init-script rAF chain inside
the iframe; a callback-count-only gate was a harness failure, not product
evidence. Its failed receipts are retained externally. The corrected observer
also samples timers and distinguishes a hidden prepaint grain node from a
visible legacy overlay. It still requires the full startup interval and early
screenshots; a vacuous empty observation cannot pass.

The actual 1× root/V1 iframe runs reached fully refined `empirical-adaptive`
terrain at 45.016 seconds (Chromium) and 143.094 seconds (Firefox). Each completed
16 date/settings interactions, including eight during refinement, advanced
the clock/countdown, recovered after a worker failure, and verified V1's local
dependencies and independent settings. Startup/preview screenshots are not
Moon visual qualification. The file-entry run reached full refinement at
61.984 seconds and passed opacity, single-cloud, A→B→A, malformed-result and
retry controls: 3,497 opaque interior samples had zero star leakage; 1,225 cloud
samples were within one code of the independent display-colour reference.

Affected checks: 117 CP9 Node tests, 18 Python tests, 38 Moon component tests;
native browser smoke 141/141; lifecycle 19 cases / 386 assertions; full-frame
composition exactly matched its independent reference. Cached *unchanged
physical surfaces* were reused only for presentation checks: Chromium passed
36 half-Moon DPR/placement cases and Firefox one bounded half-Moon case, with
independent outer-limb comparison. Fresh normal-clock solves are separate above.
The inherited bottom-border regression control passed. Two builds reproduced
identical runtime bytes and frozen V1 hashes.

[Fully refined Moon with native clouds](evidence/startup-cloud-20261007/screens/native-clouds.png),
[half-Moon crop](evidence/startup-cloud-20261007/screens/half-moon.png),
[Firefox root iframe](evidence/startup-cloud-20261007/screens/combined-firefox-root-iframe.png),
[frozen V1 iframe](evidence/startup-cloud-20261007/screens/combined-firefox-v1-iframe.png).

Focused reproduction commands (set `SALAH_BROWSER` and
`SALAH_BROWSER_EXECUTABLE` to the installed Chromium or Firefox first):

```text
python tools/cp9/cloud_hotfix_check.py --root . --out <evidence> --fonts <fixture-fonts> --browser chromium --dpr 1
python tools/cp9/cloud_hotfix_check.py --root . --out <evidence> --fonts <fixture-fonts> --browser firefox --dpr 2 --night
node --test tests/real-sky/*.test.mjs
python -m unittest discover -s tests/real-sky -p "*_test.py"
python tools/test_moon.py --output <evidence>
python tools/verify_v1.py --check-pages --negative-control
```

Use distinct output directories per browser/case; add `--direct` for root mode.
The retained receipts include exact commands and broader native/Moon controls.

The broad native run retains its eight historical failures: one in
`r0021-reveal`, seven in `r0022-baseline-balance`; four TODOs also remain. Its
counts match the pre-hotfix baseline. This is not an all-green historical suite
or closure of N001/N002 PARTIAL or N003 BLOCKED. Pixel probes emitted Chromium's
readback-performance advisory; the smoke server logged cancelled connections
as its harness replaced iframes. Unexpected page errors/local-asset failures
were absent from the accepted actual-entry checks.

## V1 and publication

No `v1/` file, settings key, iframe size, card geometry, remote service,
repository rule, main branch or existing PR was modified. Public V1 index,
config, version and manifest matched their frozen hashes. `verify_v1.py
--check-pages --negative-control` passed; the disposable tampered file failed
as required. Do not use `--check-root` after the renderer overhaul.

After independent review, merge only this repair PR with a merge commit and
`--match-head-commit` pinned to the reported repair head. Recheck main remains
the recorded base first; reconcile and requalify if it moved. Do not enable
auto-merge, use admin bypass, delete branches or merge PR #38.

Wait for a successful Pages build/deployment whose commit is the resulting main
merge SHA. Then compare public root index/config/sky CSS+bundle/Moon host with
that merged tree, and all four public V1 files with the frozen manifest/version
hashes. Smoke both exact `#local=1` iframe URLs; confirm the new startup shell,
cloud motion, prayer/settings readiness, and fully refined Moon. A preview-only
capture is insufficient. A failed deployment/live check requires preserving
evidence and diagnosing it, not rewriting main or V1. This public repair smoke
remains pending because this task publishes a repair PR, not a deployment.
