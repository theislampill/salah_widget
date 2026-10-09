# Current-root celestial startup — qualification record

**Affected qualification reopened:** the independent owner-supplied review of
`f0647b44e10c9ce4f80895b52861893c347512fd` requests changes to initial HTML delivery
and deferred-font fitting. The [active amendment](PR43_REVIEW_REVISION.md) owns
the correction and fresh evidence. The retained results below describe their
original bytes and do not qualify the revision.

This is the separate #33/R0021 startup successor, revision 1. It is implemented
work for a **Draft repair PR**, not an audit closure, owner visual acceptance,
merge or deployment. [Specification](CELESTIAL_STARTUP_RLGWO.md) defines the
unchanged budgets and [R0022-L1](R0022_L1_DISPLAY_INCREMENT.md) owns the confirmed
settled lunar display defect. Strict S1 timing/coverage and full-scene S10 remain
open; neither has been silently marked passed.

## Identity and evidence custody

The baseline is PR42's actual merged main
`18ff14860ff41c084b1db5f396bb62aa9c22b1be`, reviewed head
`4bccdf43363926c3077f60de87e5617ccb9abcb9`, runtime
`f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260`.
The original audit evidence stays at
`b879573c298f19189d1f2392108b8b9f3b2cda0b`. The repair branch advances separately.
No PR38 work, V1 files or another checkout were used as mutable donors.

Final candidate runtime SHA-256:
`4c764068d0d19afe4d440376ed765a373c7afead594b5d16ef22402dd02ef799`.
Generated root SHA-256:
`51c09cfdd0bb535018ba76c02878c7bb8574b82a957de0c62392ed379f4834ef`.
The PR's Git head binds these files; the runtime hash covers product files rather
than this documentation. See the [complete runtime inventory](startup-evidence/RUNTIME_IDENTITY_FINAL.json).
The public readback still matches baseline: this PR has not been deployed.

Full local custody is `C:/Users/theis/Documents/Codex/celestial-startup-repair-20261008`.
Portable selected evidence is in the [evidence index](startup-evidence/README.md).
Its manifest binds
original receipts, selected ordinary frames/videos and explicitly modified
diagnostics. Rejected captures and earlier runtime measurements remain in local
custody; they are not silently replaced by later successful cases.

The supplied archive's 39 assertions establish control-flow/predicate behaviour.
They are not measured seconds or lunar numerical qualification. Actual baseline
browser captures reproduce seconds of missing principal celestial objects.

## Measured first seconds and causal breakdown

Times below are milliseconds from navigation to the first retained native source
frame containing the specified pixels. They are receipt upper bounds, not
physical-monitor photon times. Each candidate's first captured scene contains
atmosphere, the initial V5-derived Moon and real catalogue anchors together.
Baseline first stars and first Moon are independently detected. These are the
ordinary runs, without app getter or screenshot polling during the first 15 s.

| Engine / document | Baseline scene | Baseline stars | Baseline Moon | Candidate complete scene | Accepted scene to candidate receipt | Added time over baseline scene |
|---|---:|---:|---:|---:|---:|---:|
| Chromium cold | 588.0 | 1194.0 | 7283.0 | 651.6 | **289.1** | 63.6 |
| Chromium cache-warm reload | 217.2 | 428.2 | 6252.2 | 493.7 | 176.8 | **276.5** |
| Chromium fresh new tab | 303.0 | 655.0 | 6247.0 | 469.4 | 158.3 | 166.4 |
| Firefox cold | 721.0 | 1174.0 | 17684.0 | 1007.0 | 235.0 | 286.0 |
| Firefox cache-warm reload | 411.3 | 533.3 | 16846.3 | 598.4 | 188.0 | 187.1 |
| Firefox fresh new tab | 291.4 | 466.4 | 16329.4 | 495.6 | 210.0 | 204.1 |

The bold values fail the original Chromium 250 ms bounds. All six navigation
bounds pass; captured content appears together, but that is not exhaustive frame
coverage. Maximum uncovered first intervals are Chromium 298/295/287 ms and
Firefox 113/153.4/44 ms for cold/reload/new-tab. Only the last Firefox case passes
the full focused predicate. **S1 remains PARTIAL with strict failures**, not an
eventual-ready PASS. [TIMING.json](startup-evidence/TIMING.json) retains per-case
checks, source identities and the exact acceptance inputs.

Independent instrumented runs distinguish acquisition, CPU work, messages and
application publication. They do not replace the ordinary timing table.

| Stage | Chromium final lifecycle | Firefox final lifecycle | Firefox with both full assets delayed 8 s |
|---|---:|---:|---:|
| Initial lunar CPU evaluation | 65.2 ms | 80 ms | 92 ms |
| Two compressed lunar asset reads | 152.4 / 272.6 ms | 193 / 216 ms | 8088 / 8152 ms |
| Per-row engine preparation, including decoding | 497.9 / 530.9 ms | 710 / 730 ms | 720 / 721 ms |
| First full-spatial 540 px, 64-sample passes | 4460.4 / 4453.4 ms | 16242 / 16311 ms | 14759 / 15091 ms |
| First terrain-preview message, from navigation | 6418.8 ms | 18270.6 ms | 25059.7 ms |
| First refined V5 message, from navigation | 26809.2 ms | 85632.6 ms | 93425.7 ms |
| Refined application publication, from navigation | 26842.4 ms | 85657.6 ms | 93452.7 ms |
| Later observed current refined V5 | 27220.2 ms | 85811.6 ms | 94399.7 ms |

The local large Moon delay is dominated by the first terrain calculation, not
the successful asset request. The owner's longest production-network delay is
not measured here. The original 9,807,339-byte full sky pack still takes transport,
JavaScript evaluation and catalogue admission before its full preview: in the
Chromium trace its response ends at child-clock 849.1 ms, catalogue admission
starts 861.5 and ends 891.0; Firefox is 892/954/978 ms. Those gaps include scheduling,
so they are not presented as pure parse CPU time. Initial bootstrap stars no
longer wait for any of those stages. [STAGES.json](startup-evidence/STAGES.json)
retains resource timing, decoding, row work, sky admission and publication clocks.
Cache-warm receipts retain zero-transfer/cache evidence and server request logs;
route-based font diagnostics are explicitly excluded from cache claims.

The cold-start tradeoff is explicit: generated HTTP root grows from 547,654 to
6,082,431 bytes because the independent initial lunar data is inline. This removes
dependency on the 52.4 MB terrain transfer and first terrain pass, but does not
qualify startup on a throttled initial-document connection. The full single-file
entry is larger as well. Arbitrary hardware/network guarantees are not inferred
from localhost reference-machine results.

## Focused verification and evidence reuse

The final focused run reports **683 tests: 679 passed, zero failed, four inherited
TODOs**. Seven additional first-scene predicate controls pass. These include
eventual-ready and missing-pixel counterexamples; synthetic predicate clocks are
never performance evidence. The 40 current-consumer lunar comparisons satisfy the
predeclared pixel limits. V1 preservation and its disposable tamper negative pass.
Two native builds reproduce the exact final runtime; rebuilding the derivative
in a separate evidence directory reproduces binary and manifest byte for byte.
The [checks](startup-evidence/checks/seal-focused-tests.log),
[build receipt](startup-evidence/BUILD_DETERMINISM.json) and
[derivation receipt](startup-evidence/DERIVATIVE_DETERMINISM.json) are retained.

The portable matrix contains 30 capture cases and their cold/reload/new-tab rows.
Final-runtime rebindings cover ordinary startup in both engines, Chromium DPR1
and Firefox DPR2 lifecycle controls, delayed Firefox full recovery, and both
single-file engines. Earlier `d1255df4` weather/day/dawn/direct/file/failure cases
remain explicitly labelled with that runtime. Their untouched physical and
composition owners, identical initial fields and focused final rebindings support
bounded reuse; they are not falsely called reruns at `4c764068`. The source/runtime
inventories allow a reviewer to reject reuse if an affected owner differs.

Both final lifecycle controls exercise visible settings, location A-B-A,
generation/epoch, seek and return to live, reference-profile withdrawal and
calendar return, invalid physical reference, phase bounds and stable body size.
Slow/missing full inputs retain only a current initial scene. Chromium retry and
the final delayed Firefox run reach a current refined V5 result. Day and dawn
controls distinguish physical twilight from local solar-body eligibility.
Unknown-location acquisition and a five-second prayer delay are separate cases.
The actual extension/new-tab parent remains unverified.

The [transition crops](startup-evidence/transitions/receipt.json) are full ordinary
compositions selected from instrumented lifecycle recordings for appearance, not
latency. They show stable lunar silhouette, phase, texture and opaque footprint
across initial, preview and final tiers at normal 1x. They also visibly retain the
S10 hotspot/wash. They therefore support lunar continuity and **do not establish
an acceptable bright-Moon full-scene result**.

## What changed, and what remains the same

The initial catalogue contains 921 lossless enabled records at magnitude <=4.5
from the same pinned source. Its independent admission does not wait for the
9,807,339-byte full catalogue/diffuse JavaScript pack. Source astrometry,
extinction, spectral flux and PSF are unchanged; the complete pack still refines
the sky through its original admitted path.

The initial Moon uses a deterministic 3,965,156-byte derivative of the V5 terrain,
material and receiver geometry. It evaluates the accepted native phase in this
document. It is not a pre-rendered phase sprite, old Moon, previous document's
surface or scientifically final terrain result. Canonical horizon visibility,
16 solar samples and an analytic Lambert Earth integral are an expressly bounded
initial approximation. The complete 52,410,116 compressed asset bytes, WASM,
two row workers, preview and final adaptive calculation remain in place.

Forty comparisons with retained full adaptive references cover ten phase/sense
cases, DPR1/2 and two subpixel alignments at the actual maximum body footprint.
Maximum interior encoded RGB RMS is 0.385564/255, p95 is 1/255 and coverage is
identical. The reference files and exact initial consumer are hash-bound. The
actual-footprint pairs were inspected for phase, texture, Earthshine and edge
continuity. This supports the initial approximation; it cannot accept a bad full
composition. The derivative retains 2,018 unresolved trace calls and 21 held-out
single-boundary disagreements as limitations, not numerical successes.

Geometry, approved body size, native time/configuration, opacity, Earthshine and
all currentness/seek/generation/A-B-A/profile/reference fences are preserved.
The initial body no longer depends on prayer-provider settlement. Full-asset
failure retains only a still-current initial result; retries retain their original
authority checks. Critical-path changes remove discarded texture readbacks and
redundant raster work, keep optional fonts nonblocking, and give the complete
published scene a paint opportunity before optional preparation/provider work.
There is no timer, whole-card loading gate or enlarged acceptance budget.

The final sampler preserves all initial RGBA, linear, coverage and calendar
fields byte for byte against the previous qualified consumer in ten phase/sense
controls. Its focused box-filter test includes clipped edge coverage. Formatter
reuse preserves DST fold/gap and time-zone A-B-A results; no time result is cached.
Arc fitting retains all 201 path samples with one unchanged transform snapshot.
The provider task is queued outside the rendering callback; that boundary is an
opportunity to paint, never proof that pixels have already appeared.

## Capture method and its limits

Reference: Windows, Ryzen 7 9800X3D, 32 GB, Chromium148.0.7778.96 and Firefox150.0.2.
Browser profiles are disposable. Persistent-profile reload/new-tab controls use
genuine HTTP cache without Playwright routing; transfer size and server requests
distinguish cold and cache-served assets. The owner's profile/storage is untouched.
Ordinary CSS, 325x530 card, 330x534 iframe, 390x600 capture and relevant DPR1/2 are
retained. Direct and file entry are separate controls. The actual extension/new-tab
parent is unavailable and **unverified**.

The accepted saved observer is Orlando28.5383,-81.3792, height0m, America/New_York.
The Date fixture advances at real1x from a documented UTC. Weather and provider
responses are explicitly synthetic. September25 at02:00Z is September24 at22:00EDT;
the incident/physical-lunar-negative case uses October9 at01:00Z. Day and dawn
have their own recorded physical Sun positions. Prayer labels never determine
celestial eligibility. Earlier fixture revision1 inherited impossible Hijri
days; those receipts cannot qualify calendar readiness. Revision2 supplies valid
synthetic civil-calendar dates without changing the Gregorian astronomical scene.

Ordinary video-only runs start recording before navigation and make no app getter
or PNG requests in the first15s. Raw native JPEGs and source/receipt clocks are
retained before the recorder resamples to25fps. The external binary marker encodes
parent `performance.now()` in milliseconds; it may freeze and is not a compositor
clock. A filename/request label is not an actual screenshot time. State getters
after15s qualify later state, never earlier pixels. Trace/CPU/layer runs are labelled
diagnostics and cannot replace ordinary visual controls.

Chromium screenshot `expected_display_time` is only an estimate based on a prior
frame and vsync; it must not pass a timing gate. The review tool joins screenshot
source/sequence to `AnimationFrame::Presentation` feedback and brackets the clock
conversion. A retained diagnostic's first complete thumbnail has expected477.7–479.7ms
but actual feedback647.1–649.1ms. The latter agrees with capture receipt, so the
earlier estimate does **not** rescue its strict accepted-scene miss. Thumbnails
cannot qualify stars; normal1x source frames provide that evidence. These are
headless compositor measurements, not physical-monitor photon timestamps.
See Chromium's [screenshot source](https://chromium.googlesource.com/chromium/src/+/8b96632ef93385dbf3039bb44b9447240102dbd9/content/browser/devtools/protocol/tracing_handler.cc)
and [presentation feedback source](https://chromium.googlesource.com/chromium/src/third_party/+/refs/heads/main/blink/renderer/core/frame/animation_frame_timing_monitor.cc).

### Retained failures and rejected approaches

- The strict first-complete-scene predicate rejects the baseline's eventual-ready
  counterexamples, missing principal pixels, getter-only claims, missing coverage,
  excess added loading time and later unwarranted gaps. Its seven synthetic tests
  test the predicate; they are not browser performance results.
- Ordinary Chromium still misses the 250 ms accepted-to-presentation budget on
  cold startup and the matched extra-startup budget on one final reload. Browser
  capture intervals exceed the 80 ms coverage bound in some first seconds. Keep
  S1 open rather than equating co-captured principal objects with exhaustive proof.
- Coarse terrain, omitted shadow and alternate receiver-grid probes did not
  establish the accepted appearance contract. They are not the installed initial
  representation. Warm reuse alone was not selected as the cold-start solution.
- A CPU-backed preview-canvas diagnostic did not materially improve startup and
  was rejected. It is not the ordinary product. The old compositor thumbnail
  detector assumed 390x600 pixels and is rejected; expected-display estimates are
  also rejected as presentation proof.
- The baseline layer wrapper's final video-path error was recovered by exact
  existing file/runtime identity; no native run was replayed. Earlier Firefox
  driver/protocol and partial-build fixtures are not product qualification.
- Earlier lifecycle receipts reported a false `settings.open` annotation by
  checking the wrong CSS class. Their real visibility assertion and screenshots
  passed; the corrected annotation is rebound in the final lifecycle captures.

Preserved source receipts and their hashes distinguish each case. A stripped
no-lunar-light diagnostic and a numerically good Moon crop cannot establish
acceptable ordinary full-scene appearance.

## Glow disposition and full-scene acceptance

Both owner attachments are **unchanged baseline**, not candidate or intentionally
stripped diagnostic: the contact sheet matches `before-chromium-clear`; the single
crop is pixel-identical to `before-firefox-clear/cold-04.png` after PNG decoding.
The original file hashes, timestamps, capture coverage, inputs and runtime/harness
identities are retained in the attachment-binding receipt and linked L1 increment.

The left concentration is the physical Moon's atmospheric field at projected
native coordinate(3.557,223.536), distinct from the enlarged upper-right calendar
body. The broad neutral lunar contribution, passed through the existing display
encoding, explains most of the grey wash. Fixed-exposure ablations remove solar
overlays, calendar body/optics, stars, diffuse, clouds and glass separately. None
removes the hotspot. Removing only physical lunar atmospheric radiance changes
left/open/lower ROI mean codes from240.8/100.0/138.6 to33.1/27.5/38.5. The matched
baseline and candidate full compositions agree without amplification.

That removed-light diagnostic is **not the repaired product or an accepted target**.
This is an existing settled display/composition defect, not a demonstrated wrong
clock, initially visible Sun or calibrated lunar irradiance. S10 remains OPEN
pending the separately coordinated R0022-L1 display/registration decision and
matched owner-accepted full scenes. The executable next tests are specified there;
arbitrary global dimming, deleting scattering or moving every light to the centre
are excluded. Startup timing and lunar-only RGB scores cannot close S10.

## Review, integration and remaining obligations

The coordinator owns #33/#34 comments and the consolidated closure DAG. Completed
derivation/comparisons/attribution must be consumed rather than repeated. Review
the separate Draft PR before any owner-authorized merge; then verify deployed
bytes and the actual native parent before closure. Existing CP9 N001/N002 PARTIAL,
N003 BLOCKED and original callback-cost/native-platform limitations remain honest.
No broad V5 programme, CP9 traversal or 37-issue audit rerun is claimed here.
