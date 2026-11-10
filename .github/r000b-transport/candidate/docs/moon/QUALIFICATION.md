# CP9 dependent Moon candidate — receiving qualification

**PR42 follow-up:** the [current hotfix register](../real-sky/STARTUP_CLOUD_HOTFIX.md)
owns the later lunar calendar/composition, bounded terrain-preview/refined
continuity and native corona-order changes. Refined-only withholding was rejected
as a continuity regression. The receiving/release receipts below remain historical;
they do not qualify those changed postimages. V5 kernel, terrain assets and
material profile remain unchanged. Joined PR42 browser qualification is separate
from the original renderer rollout and does not authorize another merge.

**Corrected candidate, 2026-10-07:** see the [release qualification](RELEASE_CANDIDATE.md),
[rim correction](RIM_CORRECTION.md) and [normal-clock currentness fix](CLOCK_CURRENTNESS.md).
The receipts below describe the preceding candidate. The follow-up qualifies
the corrected runtime in Windows Chromium and Firefox for the user's bounded
normal-clock rollout. Historical N001/N002/N003 statuses are unchanged.

**Original receiving qualification: PARTIAL overall; dependent Draft PR only.** The supplied
Moon implementation passes the scoped receiving checks below. This does not
close CP9-N001, N002 or N003, certify all visual gates, or repeat the V5 research
programme. Measurements are from Windows on 2026-10-07.

## Identity and application

- Source: [Draft PR #39](https://github.com/theislampill/salah_widget/pull/39),
  `codex/cp9-real-sky-integration`, head
  `1977217cc2ac26fcc436b991aff498d306a0cd26`. Live readback matched the donor pin;
  there was no later CP9 work to reconcile. The comparison branch was not edited.
- Receiving branch: `codex/cp9-moon-v5-integration`, created from that exact head.
  The PR base is the CP9 branch, not `main`.
- Donor: `Salah_Moon_CP9_Integration.zip`, 58,649,788 bytes, SHA-256
  `4dc3a9707b1dc7c5605b161e309c852464a6c57bc95fd35133021c020660f0e4`.
  Original package verification passes: 106 manifest files / 60,355,524 bytes.
- Final runtime SHA-256:
  `13fb06bc273dfed97ba49a1e3353c1e0062312e956b97b596294e0fe997ae58b`.
  [Full runtime inventory](CANDIDATE_RUNTIME_IDENTITY.json) binds root entries,
  CP9 delivery and every Moon delivery asset, worker, kernel and file chunk.
  Source/test inventory and raw observations are in [evidence](evidence/README.md).
- PR #38 was not fetched or used as an implementation donor. The integration
  package supplied the implementation and focused numerical evidence. The later
  request to compare four phases against original V5 renders exposed one missing
  reference dependency: the integration package did not contain that four-phase
  reference set. Only Part01's gallery and selected provenance metadata were
  inspected; four embedded PNGs were matched to the original manifest. Parts
  02–15 remain unopened. No V5 research campaign was rerun. The selected read
  scope and hashes are in [reference custody](evidence/v5-phase-references/reference-custody.json).

The original guarded `--check` passed all 96 preimages. The original `--apply`
then refused **before writes** because its inventory treated a linked worktree's
root `.git` pointer file as a payload path. An external copy of the installer was
corrected to omit only receiver Git metadata. Payload `.git` remains forbidden;
the pin, protected-branch, clean-tree, preimage, late-drift, rollback, output and
deterministic-build guards remain active. The original ZIP and extracted package
are unchanged. [Reviewed adapter diffs](receiving/README.md) and failed receipts
are retained.

The corrected guarded application wrote 149 paths from 26 payload files and 125
generated outputs (two overlaps). Both staged builds matched. The **original,
unmodified installer** subsequently verified all 189 installed postimages,
including after two repository-builder runs before the separately requested
horizon fix below. No generated output was
force-copied. Installer controls: 20 PASS, two explicit Windows symlink-creation
privilege SKIPs; the original Windows fixture failures are retained.

The user's later request to fix the black bottom border adds one authored,
digest-guarded correction in `tools/native_core_horizon.py`. The immutable vendor
input stays unchanged; the builder regenerates the copied core and bundles.
The original installer correctly reports drift on the final candidate: exactly
five declared postimages now differ (`tools/build_native.py`, copied physical-sky
renderer, worker, sky bundle and offline entry). This is **not** a final
source-identical donor claim or a bypassed installer guard.
[Explicit post-donor delta](evidence/post-horizon/post-donor-delta.json) and the
original refusal are retained. Two further builds reproduce the final runtime.

## Semantic owners and change boundary

| Owner | Change |
|---|---|
| `src/native/index.html` | Native lunar phase/time/configuration identity; request, publish, invalidation and legacy-fallback boundary. Prayer/calendar/settings implementations remain the native owners. |
| `real-sky/native-host-hooks.js` | Supplies the current lunar surface and explicit renderer diagnostics. |
| `real-sky/native-host.mjs` | Joins the device-resolution Moon and clears it with CP9 currentness; existing sky physics raster remains unchanged. |
| `moon/src/`, `moon/assets/`, manifest, C/WASM | Exact supplied host, worker, adaptive terrain solver, V5 presentation, material and metric terrain. No artistic or numerical retuning. |
| `tools/build_native.py`, `tools/build_moon.py` | Deterministically regenerate root HTTP/offline entries, host/worker and local file-data chunks. |
| `tools/native_core_horizon.py` | Digest-guarded correction of an exact-horizon visibility decision in the copied CP9 physical renderer; immutable vendor bytes retained. |
| Native fixture loaders, `tools/cp9/native_lifecycle_check.py` | Admit only the exact new transport initializer and Moon script; keep unknown/duplicate-script rejection. CP9 fault instrumentation leaves the separate Moon worker protocol to its dedicated tests. |
| `tools/cp9/runtime_identity.py`, `moon_receiving_check.py`, `moon_visual_acceptance.py`, tests | Bind new delivery assets and qualify actual entry, refined worker-to-pixel lineage, phase references, opaque composition, refinement UI and stale/failure recovery. |
| `.gitattributes`, AGENTS/DESIGN/HANDOFF, qualification docs | Preserve sealed bytes and distinguish parent evidence from this candidate. |

All Moon runtime, data, profile and kernel postimages still match the donor.
The five explicit deviations above belong only to the requested CP9 horizon
fix and its deterministic generation. Other changes are receiving tests,
fixture compatibility, documentation and byte-custody rules. Vendor scientific
sources, masks/encoding equations, settings/configuration implementation,
builder UI and the inherited DAG ledger remain unchanged.
Git whitespace checks retain raw receipt CRLF, literal test-output whitespace,
unified-patch context and the donor's sealed extra EOF lines through narrow path
attributes. Those bytes are not normalized to make receipts or donor hashes pass.

## Checks on the receiving candidate

Counts are correlated tests, not independent reviewers or scientific replication.
Commands, runtime hashes, raw results, failed attempts and selected pixels are
indexed under [evidence](evidence/README.md).
The initial receiving runtime was `ef2631518e46da8548b9269f8a113ea6eb5926a3adfe37bd651a0d918b9e65cf`.
Its receipts remain historical after the boundary fix. The final four-phase
acceptance and `post-horizon/` checks bind the final runtime above. Native inline
owners and the generated HTTP index remain byte-identical to that initial
receiving runtime, so their expanded regression results remain applicable.

| Check | Result and scope |
|---|---|
| Supplied Moon component tests | **33 PASS**, including actual small terrain/WASM work and host/profile/currentness/failure controls. |
| Supplied Moon builder/asset tests | **2 PASS**. |
| CP9 JavaScript integration | **114 PASS** on the final runtime (109 retained, two Moon/CP9 fixture controls, three horizon boundary/radiance regressions). |
| Python launcher/collector/runtime identity/build guard | **18 PASS** (5 + 11 + 1 + 1); Moon asset changes alter identity and CP9 source drift refuses the horizon correction. |
| Expanded native regression commands | **887 PASS, eight unchanged historical failures, four TODOs, five explicit removed-producer exclusions** across 28 commands. Parent baseline: 881 PASS with the same eight failures, four TODOs and five exclusions. Six added fixture controls account for the pass increase. |
| Native browser smoke | **141 assertions PASS**, all 30 required callbacks, no page errors, after fixing the fixture's two hardcoded script counts. |
| CP9 native scene matrix | **15 scenes / 88 assertions PASS** in Chromium: day/twilight/night, clouds/fog, source support and physical/calendar separation. Expanded-document fixture; all captures report Moon `loading`, so this covers CP9 plus the native fallback, not refined terrain or actual entry. |
| CP9 lifecycle/assets/currentness | **19 cases / 386 assertions PASS**: slow/missing/corrupt assets, worker constructor/startup/post/render/crash/message faults, target/time transitions, prayer/calendar and settings under failure. |
| CP9 page/elevation/resize | **87 assertions PASS**. |
| CP9 presentation cache | **13 assertions PASS**. |
| Existing material/composition controls | 8,047 opaque fallback lunar pixels differ by **zero** codes; full 325×530 foreground composition differs by **zero** codes, with incorrect-equation and moved-geometry controls. These short runs cover the retained PBR fallback, not final terrain. |
| Supplied browser runner | HTTP DPR 1 and DPR 3: **7 checks each PASS_SCOPED**. Missing, truncated and corrupt assets: **8 each PASS_SCOPED**, using explicitly small 40px physical-reference solver workloads for fault recovery. |
| Actual HTTP terrain phases | Refined 540px canonical half, crescent, gibbous, full, new and below-horizon token captured. Original series: 16 recorded checks; its initial cloud-presence claim is superseded as described below. All other recorded controls remain applicable. |
| Corrected actual HTTP / regular file entry | **11 checks each PASS_SCOPED**: visible native clouds, opaque direct-light rejection, one cloud application, A→B→A rejection, matching malformed result withdrawal and retry. |
| Single-file `offline.html` | Initial supplied runner: **7 checks PASS_SCOPED** after its root-bound file-route correction. Final actual Windows `file:` run: **11 checks PASS_SCOPED**, including full terrain, visible native clouds, opaque composition, stale/malformed-result recovery and same-document retry. No browser security bypass. |
| Refinement UI | Final HTTP and single-file runs: **11 checks each PASS_SCOPED**, each with 16 date/settings actions split between initial rendering and `refining`; eight actions per run occur explicitly after the preview. |
| Strict refined visual acceptance | **Four phases PASS_SCOPED on final runtime**, each `ready`, `pending=false`, `empirical-adaptive`, zero unsettled samples. Exact accepted WASM arrays feed the detail join; current terrain feeds the base compositor; legacy-poison and restore crops are pixel-identical. |
| Bottom-border regression | **Four actual HTTP crops PASS_SCOPED**: unchanged PR39 and fixed candidate, overcast and night. Footer geometry remains intact; final-row brightness no longer collapses. |

The eight native failures remain failures: six old balance cases reference the
retired `_glintEls` consumer; two historical comparisons demand pre-CP9 PBR source
bytes. They also fail on the unchanged source PR #39. No assertion or threshold
was weakened to hide them. The affected transport fixture was rerun after the
final document-wrapper fix; unrelated native suites were not replayed again.

All browser results above use sandbox-enabled Chromium **148.0.7778.96** on
Windows, Playwright **1.57.0**, Python **3.11.9**; Node tests use **22.16.0**.
Provider/date/weather fixtures are explicitly synthetic. Actual HTTP runs use a
local server and real browser resource requests; the donor runner's original
HTTP route-fulfilled tests are labelled separately. This is not current live
provider, deployment-CSP, BFCache, Firefox, WebKit or Safari requalification.

## Pixels, timing and failure evidence

The [primary phase gallery](evidence/README.md#pixels) shows actual fully refined
terrain in the final widget, with native header, six prayer rows and footer intact.
The earlier 15-scene matrix explicitly reported Moon **loading**; those images
show native fallback and are excluded from Moon visual acceptance. The V5 dark
side remains muted and textured in crescent/gibbous views; the new and
below-horizon calendar disc remains an opaque ashen presence with zero declared
Moonlight. These are visual observations, not calibrated colour measurements.

For all four final captures, the worker reports kernel
`metric-radial-terrain-wasm-mb1`, the accepted physical/profile identities match,
and the detail layer adopts the exact final worker arrays. `lunarSurface()`
returns the accepted terrain canvas. The hidden `.mphoto` references its published
PNG; both `.mphoto` and `.moccluder` have computed `visibility:hidden`. The visible
device-resolution canvas supersedes the lower-resolution CP9 terrain raster.
The nonzero base `moonPixels` count therefore represents the **new terrain**,
not an old PBR layer on top. Poisoning both the legacy canvas and SVG href with
magenta changes **zero crop pixels**; restoration also changes zero. Hiding the
detail canvas changes 27,787–34,238 pixels, exposing the coarser current terrain.
Fallback remains intact for loading, failure and recovery.

| Final phase | Refinement time | Original V5 D208 max / RMS colour-code difference |
|---|---:|---:|
| Waxing crescent, 0.12 | 54.531 s | 1 / 0.057664 |
| Half, 0.50 | 60.375 s | 1 / 0.035463 |
| Gibbous, 0.75 | 43.687 s | 1 / 0.016025 |
| Near-full, 0.99 | 19.687 s | 1 / 0.040895 |

These are sequential actual-widget captures at DPR 2. Reference comparisons
independently area-integrate the actual worker's linear surface at the original
D208 footprint on black. The reference profile hash is unchanged. Tiny phase
bucket and angular-rule differences remain; this comparison is not a new dense
scientific convergence campaign. Direct crop inspection shows the V5 neutral
terrain and textured dark side, unlike the retained smooth blue native fallback.

The actual adopted surface rejected an extreme direct-star/diffuse background
in **3,497 opaque interior pixels with zero code changes**; 1,236 boundary
channels changed as a positive control. An independently calculated constant
cloud foreground equation agreed within one quantization code over 1,225
interior pixels. 2,450 channel controls distinguished an erroneous second
transmission. The corrected native cloud scene has 5,954 pixels above alpha 16
(maximum 229) and visible clouds across the Moon. Both scalar controls and
rendered crops are retained; numerical telemetry alone is not the visual claim.

Native configuration A→B→A advanced the epoch from the stale result's 5 to 9 and
rejected the prior result twice. Matching malformed numerical output withdrew
the surface to the native fallback, preserving six rows; explicit retry restored
the refined surface. Supplied tests separately exercised real worker exceptions,
profile changes, superseded phases, asset faults and disposal.

The inherited bright-scene text has modest contrast; no contrast redesign or
blanket visual-gate PASS is implied by the scene matrix. The refined phase and
cloud evidence is the separate actual-entry gallery.

**Fixed visual defect identified during receiving review:** a dark strip appeared
inside the bottom border in bright/overcast scenes. A paired actual-HTTP probe
reproduces it on both unchanged PR #39 and this Moon candidate. Removing CSS
card shadow, footer text, prayer glass or the native SVG does not remove it;
hiding the physical-sky canvas does. In the unchanged CP9 core's
`physical-sky-renderer.mjs`, the default 45-degree camera / 90-degree field puts
the last interpolation-grid row exactly on the horizon. Its optimized `above`
predicate returns false at the centre despite inverse projection reporting zero
degrees. That zero-initialized grid row is then interpolated into the last
approximately eight pixels. Parent centre-row RGB falls from (129,125,120) at
y=522 to (34,33,31) at y=529. The correction resolves near-zero optimized decisions
through the existing authoritative inverse projection. Its 1e-12 band selects
that exact test; it does **not** admit negative altitudes or shift the camera.
The final bright-scene values are (132,127,122) and (129,123,117); night values
are (36,36,36) and (35,35,35), instead of the parent's final (4,4,4).
[Before/after crops and boundary tests](evidence/README.md#horizon-boundary-fix)
prove the strip is gone on this branch. PR39 and the inherited ledger remain
unchanged; no unrelated scientific or DAG obligation is closed.

| Timing on this host | Observation |
|---|---|
| Final prayer readiness | 0.516 s HTTP / 0.641 s single-file. |
| Final first terrain preview | 7.328 s HTTP / 7.594 s single-file. |
| Final canonical half terrain | 56.187 s HTTP / 56.610 s single-file at DPR 1. The separate DPR 2 four-phase run is tabulated above. Earlier regular-file entry: 55.813 s; donor-runner HTTP: 62.656 s at DPR 1 / 58.796 s at DPR 3. |
| Earlier warm phase observations | Crescent 0.08: 42.218 s; gibbous 0.92: 31.547 s; full: 7.750 s; new: 13.125 s. These are pre-horizon receiving observations. |
| Final loading/rendering/refining UI | Maximum heartbeat 69.7 ms HTTP / 76.7 ms single-file; maximum scheduled action delay 12.3 / 27.5 ms. All 16 actions per run opened; both unchanged 250 ms limits met. |
| Loaded donor-runner DPR 1 | Maximum heartbeat 28.6 ms; maximum automation dialog round trip 62 ms. |
| Local detail join | Observed maximum 15.8 ms at DPR 1 / 54.4 ms at DPR 3 in the donor runner. This is separate from worker terrain time. |

These are single-host observations, not percentiles or a performance campaign.
The donor runner also records startup-inclusive heartbeat maxima of **566.4 ms**
(HTTP DPR 1), 408.6 ms (DPR 3) and 446.9 ms (single-file entry). They are retained,
not replaced by the later post-prayer-ready measurements. They prevent a blanket
claim that startup always meets 250 ms. Refinement remains expensive, with the
native PBR then terrain preview serving as progressive presentation.

Three 20-second wall-clock watches used actual changed cloud pixels, screenshots
and video: default 28,344 changed channels; OS reduced motion 333 small changes;
`motion=full` 28,898. The clock remained current and six prayer rows stayed
present. Reduction is substantial, not literal pixel immobility. This evidence
does not use `qaState().clouds.hash` as a motion proxy.

## Receiving-tool corrections and limitations

The original file runner aborted its own `file:` URL through a hostname filter;
the receiving adapter permits only paths beneath the candidate root. The first
native smoke failed because document wrapping still expected three product
scripts; it now preserves the exact reviewed five script bodies and one labelled
test bridge. Original failures and corrected passes are retained.

The initial phase-series cloud setup cleared weather and called `fetchWeather`,
which intentionally returns in simulation mode. Its `native-clouds` assertion
therefore did **not** establish cloud presence. That raw record and harness are
preserved as superseded for this one claim. The final harness uses the existing
`startWeather` owner, asserts substantial painted alpha, and captures actual
clouds on HTTP and file entries. Earlier UI actions covered loading/rendering;
the final strengthened run also requires actual actions in `refining`.

The default remains the supplied canonical calendar geometry and empirical
adaptive angular criterion, not automatic high-accuracy observer ephemeris or
independent dense-reference convergence certification. Metric terrain, fixed V5
profile, grey finite Earth and appearance-oriented material remain the donor's
model. Only the later requested original phase-reference dependency required a
selective Part01 gallery/metadata read; no other research parts were needed. See the
[unaltered donor report](donor/REPORT.md) for the original evidence boundaries.

The first visual-lineage harnesses exposed incorrect test assumptions, retained
with failed receipts: raw canvas hashes differ at partially covered edges; the
base compositor legitimately contains the new terrain beneath the DPR canvas;
and repeated Chromium readback can change the canvas backing store and PNG bytes.
A standalone synthetic probe reproduces the last effect without the Moon.
The final check snapshots the publication before readback, requires every opaque
RGB byte and all coverage bytes to equal the worker output, and bounds partial
edge premultiplied error to one code. Worker identity and exact detail-array
lineage, hidden-legacy controls and screenshot restoration remain mandatory.

The single-file entry is **80,467,370 bytes**; local multi-file chunks and assets
also enlarge the checkout. WASM needs the intended script/worker/WASM capabilities
under a deployment's policy. The smoke fixture's CSP and short fallback run do
not certify long-running refined terrain under every deployment CSP. There is
no web-security, CORS or file-access bypass in these results. Windows symlink
guards have two explicitly unexercised privilege cases. No independent visual
panel, cross-engine campaign or broad A–M PASS is claimed.

The [parent CP9 ledger](../real-sky/DAG_LEDGER.json) is unchanged: **N001 PARTIAL**
pending independent source/evidence review; **N002 PARTIAL** with high-rate
availability still open; **N003 BLOCKED on prerequisites** with partial platform
evidence. Moon addition does not satisfy those unrelated obligations. Next steps
are review of this dependent Draft PR and separately authorized work on the open
gates; neither PR is merged.
