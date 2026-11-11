# Root-run Chromium observation of R0007 cells on the combined R000B candidate (NOT independent)

Run by the successor root (Claude Fable 5.2, self-report) on 2026-11-11, local Windows 11 host, because the
independent tester had no Chromium build matching Playwright 1.62. Python Playwright 1.60.0 with its own
Chromium 148.0.7778.96 (build 1223), headed. This is not the Chromium build used by the hosted R000B cells
(156.0.8078.0) or by the R0007 hosted cohort.

Command (PYTHONUTF8=1), exit 0, checkout clean before and after, detached at 3422c35315a435a2030464427a35c3578c5c59cf:
`tools/qualification/r0007_native.py --source-root . --evidence-root <scratch> --engine chromium --headed --case-id NE07-reordered24 --case-id NE07-ordinary24 --case-id NE07-recovery24 --case-id NE07-fall24 --case-id NE07-mut-hardcoded-fajr`

| Cell | Adjudication | Last render observed | Page errors | Bound source |
|---|---|---|---|---|
| NE07-reordered24 | SOURCE_ASSERTIONS_MET_PIXELS_PENDING | nextKey Isha, leftMin 91, next-day-target | [] | dc2af380… (combined index.html) |
| NE07-ordinary24 | SOURCE_ASSERTIONS_MET_PIXELS_PENDING | nextKey Fajr, leftMin 360, next-day-target | [] | dc2af380… |
| NE07-recovery24 | SOURCE_ASSERTIONS_MET_PIXELS_PENDING | nextKey Isha, leftMin 91, next-day-target | [] | dc2af380… |
| NE07-fall24 | SOURCE_ASSERTIONS_MET_PIXELS_PENDING | nextKey Fajr, leftMin 270, same-day-target | [] | dc2af380… |
| NE07-mut-hardcoded-fajr | INTENDED_MUTANT_ASSERTION_REJECTED_PIXELS_PENDING | `AssertionError("render/nextKey: expected 'Isha', observed 'Fajr'")` | [] | dc2af380… |

Not done: no independent review of this run; no pixel/video review of these Chromium cells; the harness itself
labels native pixel acceptance PARTIAL.
