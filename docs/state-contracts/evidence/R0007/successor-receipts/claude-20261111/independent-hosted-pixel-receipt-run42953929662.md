# Independent hosted-pixel receipt — run 42953929662 (evidence receiving, not acceptance)

Receiver: separate reviewer context, model self-report Claude Sonnet 5.5; own analysis code; did not author or review the source.
This file is the root's transcription of that receiver's report (its original lives only in the successor's local scratch area).

- Run 42953929662: head `a71d7df097db029a90518491e2ccc15c6307e13a`, conclusion failure. Artifact 13826760980, 29,663,473 bytes, `sha256:5cd77bfefcc7c3ea3d9548b94f3d5ead43a5c5fd66b4fbeaafd3211e1ccd4822`.
- Rule, frozen after tuning on the OLD run only: blank-rows frame = monospace-line edge count (y 258–282, |dx| ≥ 40) ≥ 800 AND rows-region edge count (x 30–305, y 296–490) ≤ 8.
- OLD run 42834337271: all seven published healthy ranges reproduced exactly (recovery24 69–70, recovery12 55–57, equal-polar 59–60, fall24 56–57, fold 58, dst-recovery12 60–63, wall-ordinary-control 62–64). Overall 29 frames / 12 cells against the published 26 / 11: extras are ordinary24 252–254 and one additional mutant frame. The receiver could not reconcile the published 26 with the listed ranges.
- NEW run 42953929662: **0 flagged frames in 0 of 20 cells**; after first row text no frame in any cell has rows ≤ 8 (minimum 11–12 in equal-polar / ordinary24, which are faint-contrast rows, not blank).
- Contact sheets made for all 20 new cells; viewed: recovery24, fall24, recovery12, wall-ordinary-control, dst-recovery12, mut-lost-date, plus old fall24 and equal-polar. Old loss: card, sky and monospace status line painted, six row pills empty, status bar contacting fonts.googleapis.com. New: the first painted card frame already has row labels and times while the status bar shows the font hosts being contacted. Text crisp and unclipped in the zoomed frames viewed.
- UNKNOWN to the receiver: a visible fallback→web-font swap at the scale viewed; why new `NE07-fold` has 199 frames against 490; causes of adjudication differences (9 cells differ in status between the runs, 11 are the same).
- Python controls with Playwright 1.62.0: candidate 55 tests, 3 failures (DriverLifecycleTests); reverting only the owned-abort line → 5 failures (two tests flip pass→fail, none fail→pass).
