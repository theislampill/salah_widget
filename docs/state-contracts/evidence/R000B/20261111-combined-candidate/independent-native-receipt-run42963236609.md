# R000B independent native evidence receipt (run 42963236609) - evidence receiving, NOT acceptance
Model: Sonnet 5.5 (claude-sonnet-5-5).

## Metadata
- Run: head_sha f540f076, completed/success, 2026-11-11 05:03:45Z to 05:17:37Z. 6 jobs, all success (native checkout of baseline only in baseline cell).
- PR branch head still f540f076 -> assemble pushed no commit. Assembly receipt: published=false, changed=[], candidate commit/tree = source commit/tree (f540f076 / c4978345), baseline dbf3370f / a29866be.
- 6 artifacts; zips re-downloaded via API and sha256 == API digests for all 6. Extracted trees: every file in each artifact-manifest.json matched sha/bytes; only artifact-manifest/progress/receipt are unlisted. Video sha not independently re-hashed.

## Identity (all native cells)
Chromium 156.0.8078.0 Linux headless, sandbox requested, exe sha c97b5864 (same in old run). Driver sha b94e342a (= worktree file; identical to old run). Fixture actually served = tests/rlgwo/r000b-no-timetable-fixture.html (sha fa2dabc8, 34208 B), NOT r000b-weather-fixture.html - the workflow/driver never name the latter.
- Candidate cells: index sha dc2af380 == r000b-native-candidate.json indexSha == worktree index.html; runtimeTree f5d49b90 == manifest; expected-manifest sha 7974c772 == repo file.
- Baseline cell: index 5a200d9a == `git show dbf3370f:index.html`; manifest be5c5e10 == repo file. Baseline product = main.
- Zero pageErrors/consoleErrors/unexpectedNetwork/teardownErrors in all 5 cells. Network: fixture-ledger 16 entries candidate (weather 200 x3, radar 200 x1, prayer 200 x3, controlled prayer 503 x9), baseline 9 (1/1/1/6). Identical to old run.

## Per cell (all verdicts from receipts: 117 checks candidate visible cells, 139 hidden, 72 baseline; none non-true)
Timeline (fixture elapsed): healthy 1.5s (rain, cov [.92,.9,.6], header "Rain - Open-Meteo current model estimate; direct local observation unavailable", 24C) -> source age 891-899 s still eligible -> wall midnight at elapsed 10.0s (source age exactly 900000 at midnight) -> 901 s: modelNull, candidate.eligible=false, reason "current model time/interval unavailable, future or expired", srcAge 901168, header "Weather unavailable - no eligible current condition...", fx unavailable, precip off, lightning off; raw weather + cache bytes survive unchanged.

| Cell | Observed | Verdict | Pixels |
|---|---|---|---|
| baseline/default | Expired 901s and repeat (905s): header/fx/precip withdrawn BUT cloudReady=true, coverage [.92,.9,.6], alphaSum 1.77M/1.80M (clouds retained), actualCloud.publication null (no withdrawal receipt). Checks baselineActualCloudDefect, NoWithdrawalReceipt, NoFreshIngress true | BASELINE_DEFECT_DEMONSTRATED_PENDING_PIXEL_REVIEW | Expired cards/video: header "-" icon, no rain, prayer rows "-", but dark blue-grey cloud mass remains at top. One transient video frame (~10.5 s) shows blue sky with black moon disc (main only) |
| candidate/default | Same until expiry; then publication withdrawn-unavailable rev 6, coverage [0,0,0], alphaSum 0, cloudReady false, identical at repeat (idempotent). Fresh weather w/o prayers (el 90s): eligible, pub withdrawn-unavailable/model-estimated-rain, cov 0, precip off, header still "Rain 24C". Recovery (el 130s): eligible-published rev 8, cov restored, rain on; recovered-30s phase progress [.0675,.0844,.1013], 9736 px changed, 700 continuity steps ok | PASS_ASSERTIONS_PENDING_PIXEL_REVIEW | Pre: rain streaks, clouds, 24C rain icon, arc, countdown rows (video 9.5s). Post: no clouds/rain, stars + crescent moon, "-" icon, "Prayer times unavailable", rows "-". Recovered: clouds + rain + 24C |
| candidate/reduced | Same states/receipts; motionPreference reduced=true; phase progress [0,0,0], 0 px changed (holds) | PASS | Same as default; recovered card shows a regular row of thin vertical ticks near top (reduced) - plausibly rain-origin but looks odd |
| candidate/full | Same; reduced=true+full=true (motion on); progress [.0665,.0831,.0997], 9740 px | PASS | Same as default |
| candidate/hidden | Hidden at 5.2s (paused), 901s reached while hidden (pub withdrawn rev 6, clouds 0), 1 visible resume rAF frame, first resume check true (no stale join), resumeDoesNotReplayHiddenMotion ok; later fresh/recovered as default; progress [.0677,.0846,.1016] | PASS | Video at 13-18 s after resume: no clouds/rain, stars+moon. hidden-after-901s card (document hidden) shows stale pre-expiry prayer rows/arc but no weather header/clouds/rain |

## Comparison with run 42813528424 (standalone 68e51aa6)
Same 5 cells, same driver/fixture/browser/check names (counts 72/117/117/117/139), all True in both, same statuses. Stage-by-stage key fields (eligibility, publication, coverage, fx, precip, lightning, header, raw code) identical; request ledger identical. Differences only: index/runtime tree (old e8da0b76/04ab5ba6; new dc2af380/f5d49b90; baseline main index b4a6831b -> 5a200d9a), timings, continuity step counts (e.g. default 587->700), phase deltas (~1-2% jitter). I did not re-fetch old run metadata (head sha) - UNKNOWN.

## Anomalies / caveats
1. "last-eligible-before-midnight" PNGs (both baseline and candidate) are captured after midnight: show "Prayer times unavailable"/withdrawn pixels (candidate: no clouds) while the JSON state (el 8.7s) says eligible. Driver notes screenshots follow the read; video proves withdrawal at ~10.0-10.5 s. Only healthy-before-midnight PNG and video are true "before" pixels.
2. Source-age expiry and calendar rollover coincide (source bound == midnight); inclusiveBoundaryObservation = NOT_NATURALLY_REACHED. Native cells cannot isolate withdrawal by source age alone from day-rollover/prayer-null; exact boundary relies on source tests.
3. Fresh-weather-without-prayers: header says Rain 24C while no clouds/precip drawn (driver check replacementHeaderStillModel expects this).
4. Footer text truncated ("Gregorian date unav...", "Hijri date unav...") in expired states; recovered footers show Hijri "1500-01-02" (fixture artefact).
5. All receipts say pixelReview PENDING; native cloud/foreground mask PNGs and resume-opportunity frames not individually inspected. Moon-worker diagnostics deliberately unread.

## Ledger support (no acceptance granted)
Can support (Chromium only, synthetic fixture, combined candidate dc2af380): withdrawal of clouds/precip/condition header at source age >900s with raw/cache surviving; baseline main retains clouds (defect) vs candidate empty withdrawal receipt; idempotent repeat; fresh weather cannot revive old deck; recovery on ordinary prayer retry; celestial (stars/moon) independent; reduced/full/default motion; controlled-hidden resume; request accounting/no storm; no console/page errors.
Cannot: Firefox/WebKit, real OS sleep/wake (visibility seam only), real network/providers, exact 900000 ms inclusive boundary natively, source-age independent of midnight, final pixel-review closure, publication/merge/delivery rows, anything source-only.
