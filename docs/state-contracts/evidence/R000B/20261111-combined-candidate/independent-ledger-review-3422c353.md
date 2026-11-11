VERDICT: ACCURATE_WITH_CORRECTIONS (model: Sonnet 5.5, claude-sonnet-5-5). Scratch dir: <scratch>

1. IDENTITY (verified)
- HEAD 3422c353, tree df088b6b. The f540f076..HEAD diff has 5 paths, all under docs/state-contracts/: R000B.md, R000B_ACCEPTANCE.md, 2 new evidence .md files, generated manifest. Base dbf3370f is an ancestor.
- PR #72: open, draft, head 3422c353, base dbf3370f, mergeable/clean.
- Runs on 3422c353: only "R0017 Pages payload", skipped. No R000B workflow ran on it. Run 42963236609: head f540f076, success, 6/6 jobs success.
- Nothing states that 3422c353 differs from f540f076 only in docs, or that no workflow ran on it.

2. LEDGER SECTION
(a) Append-only: 0 removed lines in the acceptance file.
(b) 46 rows, each ID once. They match the IDs in sections 4-6.
(c) Original dispositions say "Actual native ... remains pending" and keep Firefox as inherited original limits. The ledger scopes new native results to "actual engine and OS", so Chromium-only is not a hidden requirement. The native expected JSONs only pin identity; the assertions live in the driver run_r000b_withdrawal.py (117/139/72 checks, all true).

My status counts: re-observed 15, transfers 8, source-tested only 8, open 15. The ledger claims 16 / 9 / 6 / 15.

Row corrections:
- ES0B-15, OVER-CLAIM. Generated reproduction and a source-scope review are not native re-observation. Original text keeps native/pixel qualification, public evidence and terminal gates open. Change status to "source-tested only"; limit: "Native observation of the generated runtime is by the other rows; pixel review PENDING; four R000C TODOs; reviewer identity self-reported".
- B16 and ES0B-14, over-claim risk. Original text requires real pixels, useful motion and native review, or a visible-column rain-origin check. The receipts say pixel review is PENDING and the mask PNGs were not inspected. Keep the status only with the Limit prefixed "Driver assertions only; pixel/video review of the native cells NOT done."
- ES0B-02, unclear. It rests on checks whose mask PNGs were not inspected. Use the same prefix.
- ES0B-04. The scene is midnight/night, so no Sun or catalogue was observed, and the receipt says Moon-worker diagnostics were deliberately unread. Add that to the Limit.
- B04, mislabelled. The review's transfer list was B01-B03, B05, B06, B09-B12 and omits B04. The row cites a re-executed cohort. Change status to "source-tested only".
- B11 and B12, soft. They are marked "transfers" but sit on N09/N15 owners in the changed region, and the review says R0007 changed render/selectPrayerEvent, which R000B's render branch touches. They are backed only by the node re-run, so "source-tested only" is safer. I count them as transfers; this is optional.
- ES0B-03 is conservative. The driver has a native healthyRefresh stage (healthyRefreshContinuity) and the receipt says all checks were true, but the receipt does not name it. Leave it, and mark the native status UNKNOWN.
- D01 and D06 evidence says "PR branch head equals f540f076" and "f540f076 pushed". Append: "Merge candidate is docs-only successor 3422c353 (5 docs/state-contracts paths; runtime and generated trees unchanged); no R000B native workflow ran on it."
- B17: the reviewer's two doc findings are in fact fixed (the "7 failures" wording, and the identity supersession pointer).

3. LIMITS LIST
Carried accurately: Chromium-only headless Linux synthetic fixture, midnight coincidence, mis-timed screenshots, "Rain 24°", truncated footers, pixel review PENDING and uninspected PNGs, cp1252 66/78, R0021, R0017 pin, self-reported identities.
Missing or softened:
- Moon-worker diagnostics deliberately unread.
- The reduced-cell "thin ticks" anomaly appears only in B16, not the limits list.
- The video SHA was not re-hashed.
- The hidden-after-901s card shows stale prayer rows and arc.
- A transient baseline frame shows a black moon on main.
- Recovered footers show the Hijri artefact "1500-01-02".
- The fixture actually served is r000b-no-timetable-fixture.html.
- The review notes that the identity-pin tests are tripwires, and that R0007 behaviour tests are masked unless the pin is admitted.
- The review states R0007 render/selectPrayerEvent changes in the R000B render branch are only source-tested.
Add each as a bullet.

4. R000B.md
- 29 failures at d5ede8b9 is arithmetically consistent: 713 - 680 - 4 = 29.
- 22 identity pins (b5f8ee3c) plus 7 named harness gaps (d6500a09) is correct; I counted 7 listed entries.
- The run 42963236609 head f540f076 / success / 6 jobs statements match the API.
- No sentence claims acceptance, completion, Firefox coverage or merge.

5. MANIFEST
- python tests/weather-no-timetable-assembly.test.py (run in a scratch clone at 3422c353): "Ran 9 tests ... OK".
- tools/qa/r000b_assemble_candidate.py without --publish, run in a scratch clone outside the checkout (it runs the builder): exit 0, status VERIFIED_BUILD_NOT_PUBLISHED, published false, changed [], candidateCommit 3422c353, candidateTree df088b6b.
- The manifest's R000B.md hash is 8c4ec7f4... and its ACCEPTANCE hash is 33230eec.... Both equal the actual SHA-256 of the files.
- The two evidence file hashes in the manifest also match the files.

6. PRE-MERGE GAPS NOT DISCLOSED
- R0007 date-aware selection is merged into R000B's no-timetable render branch and is only source-tested (review section 6). It is not in the limits. Smallest observation: one native cell on the combined candidate with a populated timetable around midnight/next-day selection.
- Pixel and video review of the native cells is disclosed as PENDING. The B08, B16 and ES0B-14 pixel obligations stay unproved until a reviewer inspects the PNGs, video and masks.
- The inclusive 900000 ms boundary is disclosed. It would be settled by a native cell where source age expires away from midnight.

UNKNOWN: GitHub comments #33/#72; the independent receipt's own accuracy beyond file consistency; the hosted artifact bytes (not re-downloaded).
