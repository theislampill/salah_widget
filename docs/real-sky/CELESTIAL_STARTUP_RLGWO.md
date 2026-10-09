# R0021 current-root startup increment — revision 1

Status: REQUEST CHANGES at reviewed head `f0647b44e10c9ce4f80895b52861893c347512fd`.
The [active review amendment](PR43_REVIEW_REVISION.md) reopens initial-entry and
font-arrival qualification in this same work order. S1, actual-parent qualification
and S10 remain open. This increment does not close #33.
Specification update 4 incorporates S10 attribution and the bounded startup
implementation under the same named successor revision 1; it
does not allocate a new canonical work order. The audit coordinator owns the
single coordinated #33 successor comment and consolidated DAG publication.

Owner request: diagnose, specify, implement, qualify and deliver a separate Draft
repair PR. No merge, deployment, V1 change, PR38 donor or mutation of the parallel
37-issue audit. The audit remains pinned to main
`18ff14860ff41c084b1db5f396bb62aa9c22b1be` (PR42 reviewed head
`4bccdf43363926c3077f60de87e5617ccb9abcb9`). No new canonical R number is allocated.

Baseline runtime: `f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260`.
Baseline root: `ff728552442f4bcce7f213a089bf01d4cf70ea8d74040bdd3323768ca453beee`.
Both local identities and the public root bytes were verified at intake. The
diagnosis ZIP SHA-256 is
`3347bf1c791fc834a8e5638ac2ba636f0515b7c7601160a4a128655dba851e9e`;
all 19 manifest entries match. Its diagnostic clocks are synthetic, not latency
measurements. Earlier growing Moon images concern V1 and are excluded.

## Objective and initial-quality contract

For an accepted observer/time, present a coherent first celestial scene at the
unchanged 325x530 card / 330x534 iframe footprint. Where the current calendar Moon
and real stellar anchors are warranted, neither principal component may be absent
for seconds after the sky appears. Prayer and settings readiness stays independent.
Unknown location is a separate truthful acquiring state. Synthetic weather is
labelled in every controlled receipt; rain may legitimately obscure real stars.

Initial quality is separate from full catalogue/diffuse and full V5 terrain
quality. Initial stars must derive deterministically from the same pinned
catalogue and use the same astrometry, extinction, flux and PSF. Initial lunar
presentation must derive from V5 inputs, use current native geometry, the existing
V5 material/Earthshine/profile operator, opaque coverage and unchanged foreground
composition. No legacy blue Moon, random stars, whole-widget loading gate,
guessed sleep, cosmetic fade, global brightening or reduced final quality.

Predeclared reference budgets (before the repair): Windows, Ryzen 7 9800X3D,
installed Chromium and Firefox, ordinary 1x, local HTTP without transport
throttling, saved accepted observer, DPR1 and DPR2:

| Requirement | Chromium | Firefox |
|---|---:|---:|
| Navigation to first complete scene | <=1000 ms | <=1500 ms |
| Accepted native scene to complete presentation | <=250 ms | <=400 ms |
| First scene to principal-content frame gap | <=80 ms | <=80 ms |
| Startup response versus same-engine baseline first scene | <=250 ms extra | <=400 ms extra |

The 80 ms allowance is two frames of the retained 25 fps recording, not a delayed
reveal design. Any uncovered first-frame interval is reported, not inferred PASS.
Cold, cache-warm and fresh-tab results stay separate. These are reference-machine
budgets, not guarantees on arbitrary hardware/network. Delayed/missing full assets
must not block an independently current initial scene.

Before accepting a compact lunar candidate, compare it with the approved final
renderer at the actual footprint for new/crescent/half/gibbous/full, both phase
senses and relevant DPRs. Predeclare interior encoded RGB RMS <=4/255 and p95
absolute difference <=12/255, silhouette displacement <=0.5 device pixel, plus
visual rejection of an obvious appearance/geometry swap even if metrics pass.
The existing .0416 device-pixel phase displacement and 30,000 ms sky age fences
remain unchanged. These initial-quality bounds do not relabel initial data as
scientifically refined V5 terrain.

## Semantic owners and dependencies

| Boundary | Owner | Required invariant |
|---|---|---|
| Observer, time, phase, approved geometry, prayer/settings | src/native/index.html and config.js | One native authority; no new clock/config owner |
| Bright catalogue preview | real-sky/native-star-preview.mjs, native-preview-host.mjs | Exact parent identity, unchanged source projection/transport |
| Initial presentation | native-first-paint.mjs and native build integration | No atmosphere-only accepted scene followed by object insertion |
| Lunar admission/currentness | moon/src/moon-native.mjs, moon-precision.mjs | Generation, seek, A-B-A, profile, reference, DPR and phase fences |
| V5 material and body/cloud join | surface_v5.mjs, moon-calendar.mjs, moon-detail.mjs | Neutral Earthshine, opaque body, clouds once |
| Full acquisition/refinement | native-assets.mjs, moon-worker/pool/engine/quality | Preserve complete assets, quality tiers and recovery |
| Generated deliveries | tools/build_native.py, tools/build_moon.py | Deterministic builds; no hand-edited generated output; frozen V1 |

R0003/R0004/configuration and R0008/R0020 clocks remain consumed dependencies.
R0022 physical lighting is retained. CP9 N001/N002 remain PARTIAL and N003 BLOCKED;
this bounded repair cannot certify every platform or accelerated traversal.

## Implementation and evidence plan

- [x] Verify main, PR42, root bytes, source ownership, ZIP and baseline runtime;
  isolate `codex/celestial-startup-repair` without changing other worktrees.
- [x] Obtain serialized browser/terrain slot from the original audit coordinator.
- [x] Preserve ordinary first-seconds baseline video, both engines, direct/iframe,
  repeated cold/warm/new-tab, clear/partly/rain/night and daytime controls.
- [x] Trace transport, parsing/admission, row initialization, first computation,
  publication and visible pixels separately; retain uninstrumented visual runs.
- [x] Test a compact same-catalogue bootstrap; prove current code fails its early
  appearance requirement before implementing source splitting.
- [x] Compare a compact V5-input lunar evaluation with approved full rendering.
  Accept only a bounded measured candidate; warm reuse alone is insufficient.
- [x] Integrate initial and later presentation with unchanged authority fences;
  add focused negative controls before changing their owners.
- [x] Rebuild deterministically twice; check frozen V1 and unchanged full inputs.
- [x] Exercise first complete scene, transition, slow/missing assets, native
  settings/prayers, file entry, DPRs, both engines and targeted lifecycle fences.
  Qualification retains the S1 failures, actual-parent gap and S10 below.
- [ ] Reconcile requirement-to-evidence matrix, remaining limitations and #33
  overlap; commit/push this isolated branch and create its separately reviewed Draft PR.

Rollback is the isolated patch/PR withdrawal; production is untouched. Do not
reset, clean, stash, rebase or force-push. Done means the bounded authored fix,
rebuilt deliveries, measured before/after evidence and truthful matrix are in a
separate Draft PR, with its exact runtime/head communicated to the audit owner.

## Requirement-to-evidence matrix

Numerical implementation evidence and consumer qualification are distinct. The
[qualification record](CELESTIAL_STARTUP_QUALIFICATION.md) binds the final runtime
and the [portable evidence index](startup-evidence/README.md) locates each receipt.
PASS below means the stated bounded check passed, not issue closure or acceptance
of the whole widget. S10 cannot pass from timings or lunar-only comparisons.

| ID | Closure evidence | Status |
|---|---|---|
| S1 first scene | [Ordinary timing/coverage](startup-evidence/TIMING.json), before/after clips and native frames | **PARTIAL / strict FAIL**: co-captured objects; Chromium cold 289.1 ms >250, reload added 276.5 ms >250; coverage gaps retained |
| S2 real early stars | Bootstrap identity/flux tests, ordinary clear frames, full-pack hold and rainy controls | **PASS, scoped**: 921 same-source records; no global gain; occlusion/contrast separate from admission |
| S3 current early Moon | [40 reference comparisons](startup-evidence/initial/comparison.json), source identity, phase/opacity/material controls | **PASS, initial-quality scope**: max RMS .385564/255, p95 1, identical coverage; full science remains separate |
| S4 continuity | [Initial/preview/final composition](startup-evidence/transitions/receipt.json), DPR1/2 crops, opacity/currentness tests | **PASS, lunar scope**: stable footprint/phase/material; whole-scene acceptance remains S10 |
| S5 resilience | [Matrix](startup-evidence/matrix-summary.json): missing/retry, 8 s full-asset delay, current final V5 | **PASS, scoped**: independent initial, controlled recovery, final Firefox delayed result current |
| S6 authority | Final Chromium/Firefox lifecycle receipts; generation, A-B-A, seek, profile/reference and DPR tests | **PASS, scoped**: unchanged .0416 px and 30 s fences; no stale-reference fallback |
| S7 entry/readiness | Direct/iframe/index-file/offline-file; cold/reload/new-tab; DPR1/2; settings/prayer fixtures | **PARTIAL**: isolated browser controls pass; actual extension/new-tab parent unavailable; slow initial-document network unqualified |
| S8 preservation | [V1 check](startup-evidence/checks/seal-frozen-v1.log), [preserved inputs](startup-evidence/PRESERVED_RUNTIME.json), two builds and derivative reproduction | **PASS, scoped**: V1, full V5/assets/core/catalogue/diffuse unchanged; deterministic final runtime |
| S9 audit delivery | Published coordinated #33/#34 increments; original audit identity; separate Draft PR and final head/runtime handoff | **REVIEW PENDING**: coordinator owns comments/DAG; no closure, merge or deployment |
| S10 night full-composition attribution | [Capture binding](startup-evidence/OWNER_GLOW_ATTACHMENT_BINDING.json), [matched layer controls](startup-evidence/GLOW_PIXEL_ATTRIBUTION.json), original/restored full scenes | **OPEN**: attribution complete; existing settled lunar display defect assigned to #34/R0022-L1; no acceptable bright-Moon full-scene result claimed |

### S10 owner steer and evidence boundary

The strong left-edge white concentration and general grey wash are not accepted
appearance targets. Initial lunar RGB/coverage agreement alone cannot pass this
row. Bind images before attributing them; compare unchanged baseline and repair,
then remove one layer or physical contribution at a time in explicitly labelled
diagnostics. Preserve every original full composition. Distinguish physical
lunar illumination from the calendar body's visibility and from solar overlays;
night UI labels and a crop detector's `Moon False` do not establish either.

Initial attachment binding: the contact sheet is a resized copy of
`before-chromium-clear/video-review/contact.png`; the single 390x600 crop is
pixel-exact to `before-firefox-clear/cold-04.png`. Both are unchanged baseline
runtime `f443cf0820e6879dfa7c3ce857d6b2baf554b1fdd2f889433d22e2c532cec260`.
The attachment/source byte hashes, dimensions and image comparison are retained
in `OWNER_GLOW_ATTACHMENT_BINDING.json`; different PNG encodings are not claimed
byte-identical. Matched full compositions and fixed-exposure, single-component
controls attribute both the hotspot and most broad wash to the existing physical
lunar atmosphere/display field. Solar overlays, the calendar body, stars,
registered diffuse light, clear clouds and glass do not account for it. This is
an existing settled display defect, reproduced without amplification, not proof
that the numerical field is calibrated or wrong. See the coordinated existing
[#34/R0022-L1 increment](R0022_L1_DISPLAY_INCREMENT.md) for exact inputs, ROI
measurements, semantic owners and executable next tests. Removing lunar scattering
was a diagnostic, never the product repair. S10 stays OPEN for full-scene acceptance.
The single source-of-truth audit
publication remains the coordinator's comment, with audit evidence commit
`b879573c298f19189d1f2392108b8b9f3b2cda0b` separate from product main `18ff1486`.
The coordinator published the [complete #33 successor](https://github.com/theislampill/salah_widget/issues/33#issuecomment-6074561470)
and [linked #34/R0022-L1 increment](https://github.com/theislampill/salah_widget/issues/34#issuecomment-6074562566).
Its documents-only consolidated package is pinned to
`21e7a84365fae37a86cae5c7d5e41008c0adc53f`. That planning publication is not product
integration or acceptance of this branch.

## Bounded implementation and discriminating controls

The generator admits 921 lossless enabled catalogue records at magnitude <=4.5
without the full 9,807,339-byte catalogue/diffuse pack. The same astrometry,
spectral flux, extinction and reference PSF produce exactly matching preview
photon buffers in independent observer/time controls. Full admission still uses
the original manifest. Reset/failure preserves the independent current bootstrap;
pending obsolete admissions cannot replace it or unnecessarily rebuild its sky.

The initial Moon representation contains 196,435 full-spatial V5 receivers,
source material and canonical terrain visibility boundaries, not a phase image
or a prior document's accepted surface. Its 3,965,156 bytes are pinned to the
original terrain/colour/kernel and generator source. Current native phase is
evaluated with 16 solar samples and an analytic Lambert Earth integral. It uses
the unchanged V5 material/display and calendar-proxy contract. Off-plane terrain,
finite Earth-source spread and convergence remain full-worker obligations. The
derivation records 2,018 unresolved trace calls and 21 held-out single-boundary
disagreements; those are not relabelled scientific success.

Forty retained-reference comparisons cover ten phase/sense cases, DPR1/2 and two
subpixel alignments at the actual maximum footprint. Maximum interior encoded
RGB RMS is 0.385564/255, p95 is 1, and coverage is identical. The retained full
adaptive reference hashes and exact consumer hash determine reuse. Rejected
coarse terrain, no-shadow and different receiver-grid experiments remain evidence
of why the accepted representation is full-spatial. This does not change the
approved native body size or final terrain quality.

Current-generation/seek/A-B-A/profile/reference/DPR and phase-error checks remain
at initial calculation, admission and presentation. Initial availability never
permits a stale result or an unqualified physical reference view. Current initial
pixels survive full-asset failures and are replaced by current preview/refined
results without the old initial absence. Prayer-data acquisition does not own
celestial availability. Unknown observer acquisition remains a separate case.

Measured critical-path corrections remove unused legacy-map readback, redundant
full-size raster upload/readback and unchanged-bootstrap reconstruction. Canvas
buffers exported/read back synchronously use CPU storage. Initial foreground
follows native geometry exactly once. The optional remote stylesheet is
nonblocking; its ordinary font/fallback stack is retained. Full-pack/terrain
preparation and fresh provider work get a browser paint opportunity after the
complete initial scene. Retained weather is consumed synchronously. There is no
sleep, hidden card, longer loading gate or enlarged numerical budget.

The last focused optimizations preserve arithmetic and clock ownership:
initial receiver box sampling prepares shared axis indices once; civil projection
reuses only the immutable current-zone formatter, never a projected time; prayer
name fitting snapshots one unchanged arc matrix for its 201 original samples.
The provider continuation runs in a normal queued task after the rendering
callbacks, because resolving a promise inside rAF otherwise resumes before that
rendering step ends. No elapsed-time delay or presentation guarantee is inferred
from this scheduling boundary. The retained strict S1 failures remain failures.

### S1 remaining presentation frontier

The latest Chromium ordinary capture observes Moon, real stars and atmosphere
together at 651.6/493.7/469.4 ms for cold/reload/new-tab. Cold accepted native
capture to visible receipt is 289.1 ms versus the unchanged 250 ms budget. Reload
adds 276.5 ms over its matched baseline first scene versus the 250 ms allowance.
These misses prevent a strict S1 PASS even though the multi-second insertion is
absent from the captured first scenes. Earlier candidates and misses are retained.
Sparse browser delivery also leaves uncovered startup intervals exceeding 80 ms;
co-capture does not prove a zero gap between every actual presented frame.

Next executable test: run `tools/cp9/celestial_startup_check.py` against the exact
PR runtime with `--modes cold --video --video-only --trace --cdp-filmstrip`, then
`tools/cp9/review_compositor_frames.py` and the ordinary source-frame reviewer.
Use the presentation-feedback join, not expected-display estimates, to separate
the already-published lunar/sky work from first raster/compositor and provider
tasks. Compare one owner at a time and keep ordinary uninstrumented repeats.
Any next correction must reduce measured work while preserving the original
scene, budgets and currentness fences. Do not retry until a lucky sample passes,
hide the scene, change its body size or relabel publication as visible pixels.

Qualification distinguishes native source frames from video resampling, trace
throttling and application publication. Source-frame receipts record browser
timestamps and wall-time receipt bounds; parent rAF markers can freeze. Ordinary
first-seconds runs do not poll application getters. Earlier fixture revision 1
inherited impossible Hijri days in September and cannot qualify calendar
readiness. Revision 2 retains the same accepted Gregorian scene and supplies
explicitly synthetic valid civil-calendar dates. Rejected receipts are retained.

## Intake limitations

The available computer-use surfaces contain only an empty in-app browser and MCP
Apps. No owner's Firefox/extension new-tab surface is connected. Isolated browser
iframe evidence will not be called an actual extension-parent reproduction.
The root page was fetched successfully; a top-level `CP9_RUNTIME_IDENTITY.json`
request returned 404 because that is not a public runtime-manifest path.
