# Combined R0007 native observation, commit 3422c353 (index.html sha256 dc2af3801a43...97dc82), Firefox only

Model: Sonnet 5.5 (claude-sonnet-5-5). Targeted observation, not acceptance.

The harness accepted the combined candidate with no hash or identity refusal. All 4 healthy cells met their source assertions and the mutant failed with its intended assertion. One video anomaly (NE07-ordinary24) is listed below.

**Not run:** Chromium. Playwright 1.62 expects `chromium-1234` (151.0.7922.34), and only `chromium-1223` is installed. I did not download it. Firefox is `firefox-1538`.

**Command** (`PYTHONUTF8=1`, venv python), exit 0:
`tools/qualification/r0007_native.py --source-root <checkout> --evidence-root <scratch>\r000b\combined-r0007-native --engine firefox --headed --video-only --case-id NE07-reordered24 --case-id NE07-ordinary24 --case-id NE07-recovery24 --case-id NE07-fall24 --case-id NE07-mut-hardcoded-fajr`

The checkout stayed clean. Evidence is in `<scratch>\r000b\combined-r0007-native\` (run in `r0007-native-62h_mv0y\`, frames in `frames\`, this receipt in `RECEIPT.md`).

| Cell (Firefox) | Adjudication | Expected vs observed (trace final snapshot) | Page errors / unexpected requests | Video check |
|---|---|---|---|---|
| NE07-reordered24 | SOURCE_ASSERTIONS_MET_PIXELS_PENDING, trace PARTIAL_FIRST_PRESENTATION_REVIEW_REQUIRED, failure null | Isha expected; observed next=Isha, `.nt` 00:31, 91 min ("1h 31m left until Isha"), `next-day-target`, nextDate 08-09-2026 | none / none | Final frame shows Maghrib, big 00:31, "1h 31m left until Isha". |
| NE07-ordinary24 | MET, failure null | Fajr 05:00, 360 min expected; observed Fajr, 05:00, 360 ("6h 0m left until Fajr"), `next-day-target` | none / none | **Anomaly:** the video never shows the correct state (see below). |
| NE07-recovery24 | MET, trace PASS_ASSERTIONS_PENDING_PIXEL_REVIEW | Recovery to Isha 00:31, 91 min expected; observed `next-day-required` (next=null) across renders 2 to 5, then render 6 `next-day-target`, Isha, 00:31, 91 min | none / none | Final frame shows Maghrib, 00:31, 1h 31m until Isha. |
| NE07-fall24 | MET, failure null | Fajr, 270 min expected; observed Fajr, 05:00, leftMin 270, `same-day-target`, timetableDate 01-11-2026 | none / none | Final frame shows Isha, 05:00, "4h 30m left until Fajr". |
| NE07-mut-hardcoded-fajr | INTENDED_MUTANT_ASSERTION_REJECTED, producer exit 1, `healthyControlsAccepted` true | `AssertionError("render/nextKey: expected 'Isha', observed 'Fajr'")` | none / none | Final frame shows 05:00 / "6h 0m left until Fajr" (wrong, as intended). |

For all five cells the pending list is empty, `pageErrors` is `[]`, and `unexpected` is `[]`. The traces have no console-error key, so I cannot confirm console state beyond that. This also shows R000B's no-timetable ("Prayer times unavailable") and weather path produced no page errors in these runs. Fonts settled (`status` loaded) in every cell, and no known-stall "No pending boundary" occurred. I made no re-runs.

**Document hash:** `document-hashes.json` binds `source` = dc2af3801a4314d062ed904c7c95610a0f6afd37166e1e7ef88cf1d5bd97dc82 in every cell. That matches the checkout's `index.html` and is the combined build. The `observed` field differs per cell, from 2973f0d2 to ac517952 (the "observed" field presumably hashes the served, instrumented page; I did not check what it covers).

**Video check** (ffmpeg, 25 fps; frames are 370x570, and I used your pixel regions as given):
- **Frames:** I opened one 3-frame montage per cell with Read instead of 3 separate images.
  - Early frame: blank, or "Prayer times unavailable" with "—" placeholders.
  - After data arrives: for reordered, recovery and mutant, "Countdown unavailable" with a "—" big time (reordered shows Maghrib, with the date row and some rows faded). This is the transient `next-day-required` state before tomorrow's payload.
- **Web-font blanking check:** no frame after row text first appears has rows < 150 while the mono line is >= 800, in any cell. Rows (x 30..305, y 296..490) reach about 1295 to 3770 steps per frame once text appears, and the mono line (y 258..282) about 500 to 2030.
- **NE07-ordinary24 anomaly:** the video final frame (f0150, 6.0 s) still shows "Isha / — / Countdown unavailable" with a "Waiting for 127.0.0.1..." status bar, and the Isha row highlighted at 19:30. The trace says the correct state (05:00, 6h 0m left until Fajr) rendered at about 2708 ms, so the recording does not show it. I could not tell whether this is recorder lag or a hold of the second fetch. The trace is internally consistent and the assertions passed, but a reviewer should not rely on this cell's video as pixel evidence.

**Harness caveats:** every cell's `presentationAssociations` and `firstFrameAcceptance` are UNVERIFIED_PENDING_INDEPENDENT_REVIEW, and some entries are `UNVERIFIED_ORDINAL_MISMATCH` (first-current for fall24 and ordinary24, the "unavailable" capture for reordered and mutant). The harness itself labels native pixel acceptance PARTIAL.

**Observation, not a certification:** on this combined build in Firefox, the decisive reordered case selects tomorrow's Isha at 00:31 (91 min) and the frozen-overnight recovery on the next dirty frame reaches the same value. I observed nothing Chromium-related.
