# R0021 current-root startup increment — revision 1

Status: investigation and qualification in progress. This increment does not close #33.
Specification update 2 adds S10 under the same named successor revision 1; it
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
- [ ] Obtain serialized browser/terrain slot from the original audit coordinator.
- [ ] Preserve ordinary first-seconds baseline video, both engines, direct/iframe,
  repeated cold/warm/new-tab, clear/partly/rain/night and daytime controls.
- [ ] Trace transport, parsing/admission, row initialization, first computation,
  publication and visible pixels separately; retain uninstrumented visual runs.
- [ ] Test a compact same-catalogue bootstrap; prove current code fails its early
  appearance requirement before implementing source splitting.
- [ ] Compare a compact V5-input lunar evaluation with approved full rendering.
  Accept only a bounded measured candidate; warm reuse alone is insufficient.
- [ ] Integrate initial and later presentation with unchanged authority fences;
  add focused negative controls before changing their owners.
- [ ] Rebuild deterministically twice; check frozen V1 and unchanged full inputs.
- [ ] Qualify first complete scene, transition, slow/missing assets, native
  settings/prayers, file entry, DPRs, both engines and targeted lifecycle fences.
- [ ] Reconcile requirement-to-evidence matrix, remaining limitations and #33
  overlap; commit/push this isolated branch and create its separately reviewed Draft PR.

Rollback is the isolated patch/PR withdrawal; production is untouched. Do not
reset, clean, stash, rebase or force-push. Done means the bounded authored fix,
rebuilt deliveries, measured before/after evidence and truthful matrix are in a
separate Draft PR, with its exact runtime/head communicated to the audit owner.

## Requirement-to-evidence matrix

All rows remain OPEN until the stated evidence is recorded against final bytes.

| ID | Closure evidence | Status |
|---|---|---|
| S1 first scene | pre-navigation uninstrumented video, frame coverage, measured budgets | OPEN |
| S2 real early stars | same-source subset identity, clear known anchors, full-pack hold, rainy contrast control | OPEN |
| S3 current early Moon | source-bound initial evaluation, phase/opacity/material comparison at footprint | OPEN |
| S4 continuity | initial -> preview -> refined crops/clip, geometry and no-star-leak controls | OPEN |
| S5 resilience | slow/missing full inputs, retry and continued current initial presentation | OPEN |
| S6 authority | location A-B-A, seek, profile/reference, DPR and stale-result negatives | OPEN |
| S7 entry/readiness | cold/warm/new-tab/direct/iframe/file, both engines, prayer/settings | OPEN |
| S8 preservation | V1 hashes, full scientific assets/kernel/profile, deterministic runtime | OPEN |
| S9 audit delivery | #33 exception reconciliation, exact audit/repair identities, Draft PR only | OPEN |
| S10 night full-composition attribution | bind owner captures; isolate left hotspot and broad wash independently; matched ordinary full-scene first/preview/final controls | OPEN |

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
byte-identical. Attribution remains pending. The single source-of-truth audit
publication remains the coordinator's comment, with audit evidence commit
`b879573c298f19189d1f2392108b8b9f3b2cda0b` separate from product main `18ff1486`.

## Intake limitations

The available computer-use surfaces contain only an empty in-app browser and MCP
Apps. No owner's Firefox/extension new-tab surface is connected. Isolated browser
iframe evidence will not be called an actual extension-parent reproduction.
The root page was fetched successfully; a top-level `CP9_RUNTIME_IDENTITY.json`
request returned 404 because that is not a public runtime-manifest path.
