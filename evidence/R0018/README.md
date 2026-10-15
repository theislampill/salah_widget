# R0018 / issue #24 evidence

This is the non-deploying evidence for production candidate
`859bdf245ee5e9777a4bb7dd074a9eb3616c6a71`, based on
`ed5e7afbd2fcf7a59050817e2a561bcdbfa9043d`. Do not merge the evidence branch.
The candidate fixes the default timetable with full informational opacity and a
local `rgba(9,17,28,.74)` backing. Elapsed rows recede through tint/border treatment;
the approved opaque NEXT accent/dark text and separate CURRENT inset are preserved.

The [immutable revision-1 specification](R0018.md), [accepted audit](accepted-audit.json)
and [complete captured issue](issue24.json) remain the original scope. Accepted
18-01 is retained; A01-A07 correspond to residual rows 18-02 through 18-08.

| Acceptance | Evidence and bounded result |
| --- | --- |
| A01 / 18-02 | [38 native cases](qualification-index.json): every one of the 12 names/times has effective ancestor opacity 1; default, elapsed, CURRENT, NEXT, future and optional contrast states exercised |
| A02 / 18-03 | Native intended foreground versus every pixel in each original text rectangle's hidden background: minimum **4.8591556626432935:1**, original threshold **4.5:1** unchanged; original pixels retained for independent review |
| A03 / 18-04 | Fresh source-bound noon and white-stress RED before CSS in both engines; matched GREEN, two text/background pairs, exact 12 rectangles, fonts and scene records in `matrix/`; [noon comparison](comparisons/green-firefox-noon-desktop-dpr1-compact-default.png) |
| A04 / 18-05 | Six scenes, default/optional contrast white stress and six reached native loss mutants in the [index](qualification-index.json); [78 source controls](source-tests/summary.json) |
| A05 / 18-06 | 29 exact cross-load geometry comparisons and nine explicitly retained Firefox `.cn.y` differences; [independently reviewed same-page exact-rule reversal](reviews/geometry-and-continuity.json) shows no CSS-caused movement in the settled page; [source/build identities](source-build-currentness.json) and [bounded reuse](reuse/identity.json) |
| A06 / 18-07 | [DESIGN and compatibility](docs/compatibility.json): 19 unchanged interface files, 325×530 card, separate approved 330×534 production wrapper and existing 325×530 builder/copy snippets; optional contrast remains optional |
| A07 / 18-08 | [Exact candidate](candidate-identity.json), [required outputs](outputs.json), final independent review and [delivery state](delivery.json); owner merge approval, actual public delivery, certificate-first closure and final issue readback remain separate gates |

The production diff changes nine files: the authored cell CSS, generated root and
offline entries, DESIGN, and focused fixture/contrast/collector tests. All script
bodies remain exact. Of 135 runtime files, only `index.html` and `offline.html`
change. The [canonical rebuild](final-build-identity.json) reproduced the qualified
runtime exactly. Frozen V1 payload verification passes; [current public V1](v1-current-public-readback.json)
matches all three pinned files. The existing optional Pages preflight's rejection
of any Jekyll configuration is retained on both base and candidate, with
[bounded reconciliation](v1-pages-preflight-reconciliation.json).

## Inputs and raw observations

Installed Chromium 148.0.7778.96 and Firefox 150.0.2 ran serially on Windows in
disposable contexts. The real native source/module/assets are served over local
HTTP. Only the prescribed provider records, pre-boot fixed Date, private empty
storage, optional local white stress and narrowly scoped text visibility control
are fixture inputs. The stale date control delegates through the existing render
owner; it does not invoke a substitute timetable renderer.

The controlled date is 7 September 2026, Madinah 24.47/39.61, Asia/Riyadh, method 4,
school 0. Noon uses `2026-09-07T09:30:00.000Z` and the original display fixtures:
Fajr 04:46, Sunrise 06:05, Dhuhr 12:19, Asr 15:48, Maghrib/Sunset 18:33, Isha 20:03.
These are layout fixtures, not newly certified prayer calculations. Scene times
are 12:30, 05:50, 18:55 and 23:30; broken weather is wx2/cloud50, overcast wx3/cloud100.
Both retain temperature 72°F, humidity45, wind3, direction225 and precipitation0.
Desktop1100×900 and constrained375×800, DPR1/2, compact/long/stale dates and loaded
Inter/Fraunces are recorded. Exact declared font bodies are pinned in `fonts/`.

Each native case retains commands, executable/source/fixture/collector hashes,
full-card images, twelve original text crops, corresponding hidden-background
crops, both visible/background pairs, computed styles, geometry, native renderer
state and transport observations. `visible-pixel-groups.json` indexes identical
decoded green card pixels for efficient viewing; equality is not itself visual
qualification. [Chromium scenes](chromium-scenes-green.png) and
[Firefox scenes](firefox-scenes-green-pair-1.png) are navigation aids; original
native images and comparisons remain the review evidence.

The three mutants restore past opacity .42, remove the ordinary dark backing,
and restore light foreground over the opaque NEXT accent. Each reaches the
intended opacity/contrast failure in both engines, with healthy controls retained.
They keep FAIL statuses; syntax or fixture faults are not counted as loss controls.

## Contrary evidence and limits

[Reconciliation](contrary/reconciliation.json) retains original paired-raster
failures, the exact collector/import versions, summary schema fault, old mutation
seam failure and builder import fault. No failing original is promoted to PASS.
The historical transport diagnostic remains a [raw strict failure](contrary/historical-transport/retention.json)
with zero new qualification credit and an unestablished transport mechanism.

The original historical noon capture had no pinned date. Antialiasing/shadow
changed-pixel maxima remain diagnostics, not formal WCAG ratios. Two independent
native background pairs, stable scene/canvas/style/geometry, valid current native
renderers and unchanged runtime identities gate the new evidence.

The nine Firefox cross-load differences affect only the large current-prayer
label's Y coordinate (up to about0.0333 CSSpx); timetable rectangles and all other
recorded geometry match. Five native old/new rule reversal phases are exactly
equal in geometry, typography, strings, fit key and inline focus style. This
establishes no movement from the CSS change in that settled page, not the precise
original boot-time cause. No tolerance is widened and `.cn` is not excluded.
Early RED collectors did not expose the later `row.boxStyle` field; the index
labels that absence. Unchanged source declarations and the actual-rule native
control supply padding/gap/border/radius preservation, without invented RED data.

Reuse is limited to unchanged scientific/weather/Moon/motion interfaces, by exact
identity to accepted R000D evidence. There is no new whole-CP9, lunar, continuous
motion/video, extension-parent or universal accessibility claim. Fresh affected
timetable pixels are qualified here. PR43 is neither adopted nor a dependency.

## Custody and delivery

The [publication manifest](publication/payload-manifest.json) maps logical raw
paths to published bytes. Large JSON is losslessly gzip-compressed; it decodes to
the exact original SHA-256 and size. Raw originals remain retained locally.
See [publication instructions](publication/README.md). The complete runtime asset
copy is omitted because the exact base commit and 135-file manifest reconstruct
it; native observations, collector versions, fixtures and PNGs are retained.

This packet does not authorize merge. After independent exact-head/base review,
the owner must approve those exact refs. Then the same executor performs approved
delivery, actual served source and native default noon/state readback in both
engines, independent CLOSE-R0018 reconciliation, certificate publication while
issue24 remains OPEN, and verified intentional CLOSED/completed readback.
Commit and PR use non-closing `Implements #24`.
