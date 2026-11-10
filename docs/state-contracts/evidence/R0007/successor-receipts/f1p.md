# Firefox timing native presentation — F1 single case

**Status: FINAL_FINDINGS_ONLY.** 2026-11-10T20:18:05.019839+00:00. No acceptance, readiness, lifecycle or closure authority.

The first recorded recovered target is **frame n199, PTS 7.960**: Maghrib remains current, the target reads **00:31**, the countdown reads **1h 31m left until Isha**, and the **Isha 00:31** row acquires the next highlight. The immediately preceding frame n198/7.920 remains explicit Countdown unavailable. The correct recovered presentation remains in the recording through n570/22.800. **No partial-text interval is confirmed in this new F1 recording.**

## Immutable binding and independence

- Original run **42890592160**, attempt1, case **Firefox NE07-reordered24** only.
- Commit **c5d46c3c02dd993fbf6746ec3591184e74cc2fb6**, tree **3d35264204e4660b8bf5c29dd3a257b7ab29f7ee**; recipe SHA-256 **23dc2b48e41675333951909692d6b9f4f1e07f11bf97fd47d769f44a1995baae**, `oraclesChanged:false`.
- [r0007-windows-native-42890592160-1.zip](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/r0007-windows-native-42890592160-1.zip): **696,859 bytes**, SHA-256 `4f37f98e65d2ba0cfaaf346f3ecb692e8481778bedc8d579d0a7b1eaeccd894a`. Fresh size/hash matched before inspection.
- Original read-only case directory: `/workspace/scratch/66b3aaff4329/native-artifacts/42890592160-1-original/r0007-native-aljt7vol/firefox/NE07-reordered24/attempt-0001/consumer/NE07-reordered24`.
- Parent supplies controller **G0005/6f034804** and retains sole mutation/lifecycle authority. No controller, source, index, ref, browser, native acquisition or network effects occurred in this lane.
- Reviewer/model self-report: `/root/native_preservation_review`, **GPT-6 Astra Pro**. This is my own serial image/trace review. An attempted narrow existing-child followup was refused by the agent thread limit; no child corroboration is claimed for F1. Other source receiver conclusion reports were not read.
- F2 is separately bound and will have a separate report. This document does not review Moon/science, repeat A01 comparisons, or revise earlier partial-text findings.

## Original video and coverage

The original [native video](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42890592160-1-original/r0007-native-aljt7vol/firefox/NE07-reordered24/attempt-0001/consumer/NE07-reordered24/video/page@c96b0fefdef042891e5c1dd7b507b1e0.webm) is **389,935 bytes**, SHA-256 `916adbb81f5a9c149d83225f5c65367dd008a36e164ee251d7596bb4903f5a2e`. It is VP8, 370×570, 25fps, timebase 1/1000, duration 22.840 seconds. There are **571 frames**, zero-based n0–570, original PTS 0.000–22.800 at 40 ms intervals.

Every original decoded frame is indexed at its original ffprobe PTS and full RGB SHA-256. Exact full-frame duplicates reuse one lossless representative PNG; all original frame numbers and timestamps remain in the index. There are **149 exact distinct full RGB states**, all viewed in 25 contact sheets. No perceptual similarity tolerance was used. The contact crop is the top-left 325×530 area, a browsing aid; full 370×570 native frames decide readable-card claims and preserve the recorded narrow blue left edge and browser status strip below the card. The card’s source geometry receipt separately says 325×530. I do not infer pixel geometry or timing from that scalar receipt.

I inspected full native frames for every frame in the initial-current window n116–119, target-onset window n197–200 and terminal window n567–570, plus the individual frames and nearest2x crops listed in the observation index. Some multi-frame views suggested softened or truncated letters; the relevant individual full-size frames and exact crops retain the text. Those provisional sheet impressions are not promoted to native artifact defects. The derivative crops were checked against their full-frame source pixels without mismatch.

## Recorded phase sequence

| Native frames / PTS | Actual visible state | Bound interpretation |
|---|---|---|
| n0–22 /0.000–0.880 | Blank page area, narrow blue left recorded edge | No populated card is visible |
| n23–117 /0.920–4.680 | Dark authored card, central dashes, Loading… | No six-row/date-footer population yet; not claimed as a complete timetable |
| **n118–198 /4.720–7.920** | **UTCFIXTURE; Maghrib; dash; Countdown unavailable; all six numeric rows; current Maghrib outline** | First recorded admitted-current card. Dates are ellipsized around Sunset date update unavailable |
| **n199–570 /7.960–22.800** | **Maghrib;00:31;1h 31m left until Isha; Isha 00:31 highlighted; complete six rows and date footer** | First recorded target, countdown and row highlight appear together; no earlier wrong positive target witnessed |

Primary critical windows: [initial current onset](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/initial-current-native-cadence.png), [recovered target onset](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/target-onset-native-cadence.png), [terminal four native frames](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/terminal-native-cadence.png).

The source trace contains an initial Prayer times unavailable render and an intermediate error-output record with a named current prayer while the row times are placeholders. The video does not separately show those semantic phases: its recorded sequence goes from Loading directly to the populated Maghrib unavailable card at n118. I do not promote the source intermediate to a partial-text pixel interval or assign a page time to n118.

## Target coherence and native readability

At n199 the visible current name is Maghrib. The large 00:31 matches the Isha 00:31 highlighted row; the countdown explicitly says1h 31m until Isha. Maghrib 18:00 keeps its current outline. The remaining rows read Fajr 05:00, Sunrise 06:00, Dhuhr 12:00 and Asr 15:30. All six names/times, current/next treatments, the UTCFIXTURE header and the central text are readable to this reviewer in the native full frames. Past rows are very pale against the warm background; that observed treatment is retained without a new contrast threshold.

The current civil footer becomes **2026-09-07 CE** and the Hijri footer **1448-02-19** at the first recorded target. The target’s next civil date, zone and epoch are not fully printed beside the large time; the raw render receipt binds **08-09-2026 /UTC /1788827460000**, with fixed accepted now **1788822000000** and 91 minutes. The footer showing September7 is the current civil date, not a wrong target date.

Before recovery the footer visibly says **Sunset date update unavailable**, with ellipsized Gregorian and Hijri strings. Full dates cannot be read from those pixels. No full-date formatting requirement is added. Small sky loading/refining status and scene changes are retained in the video but are not a Moon/science assessment or a cause diagnosis.

## Exact native frame anchors

| Witness | Native index / PTS | Representative PNG SHA-256 |
|---|---|---|
| [Last Loading frame](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/frames/frame-000115.png) | n117 /4.680 | `54d80e74d4fea89c9a24892feb0ab5d0ac787e74d41dd948f3aa05f5d4079f41` |
| [First named-current card](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/frames/frame-000118.png) | n118 /4.720 | `60831ebce62daaa83873837d5b128164c9c2eb6afbbe802c3eb6ad7199f6a259` |
| [Last unavailable target](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/frames/frame-000176.png) | n198 /7.920 | `8002355848e8d52ea83ca20b4fcfe0aceec2e12edeb0a36a4f1a33a6ed11da5f` |
| [First recovered target](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/frames/frame-000199.png) | n199 /7.960 | `d1da320655f35502a252c797464ca6f2421e8577b03cab0662731a2ec8d7b8c6` |
| [Terminal recorded frame](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/frames/frame-000562.png) | n570 /22.800 | `1e2c2f94354cabdbf44dd2f91f68c49c25979cec855d0f584a49b0e4fadd7076` |

A representative PNG may name an earlier frame because the exact full RGB value repeats. The frame index retains the native ordinal/PTS of every repeat.

## Raw page chronology, kept separate from video PTS

There are **six unique noncheckpoint completed-render snapshots** and **four error-output snapshots**. All first five completed renders are unavailable; the sixth is the only positive next-target render. No positive wrong target appears in the captured all-render sequence. Checkpoint-labelled copies of render receipts are not additional renders.

| Raw trace anchor | Page elapsed ms | Recorded source state |
|---|---:|---|
| `#/events/10` |1389|Body held, key tomorrow:1|
| `#/events/14` |7463|Occurrence1 released|
| `#/events/15` |7463|Occurrence1 JSON settled|
| `#/snapshots/9` |7519|First completed positive render, ordinal6: Isha 00:31,91 minutes, next date08-09-2026, UTC|
| `#/checkpointSnapshots/1` |18395|Read-only matching-tomorrow-settled checkpoint, ordinal6 retained|

All original snapshots retain the same wall epoch 1788822000000 and `TIMESCALE:0`, `FOLLOW_WALL_CLOCK:false`, `ADVANCING:false`. There is no error-output snapshot after settlement. The independently received source lane reports this as occurrence1 release before its 11335 ms deadline; this media report does not duplicate that source qualification or derive a video latency from it.

The 24 entries at `#/fonts/faces/*/display` record **swap**. This is actual recorded FontFace metadata. It does not explain the absence/presence of partial text, establish a causal fix, or supersede older contrary recordings.

## Presentation association and remaining limits

All three presentation receipts explicitly say **native-video-only**. No original PNG is expected or invented.

| Receipt | Before /after /receipt ordinal | Permitted use |
|---|---|---|
| unavailable-presentation.json |**5/5/2**|Retained mismatch; cannot establish exact first-matching-render pixels|
| first-current-presentation.json |**6/6/6**|Aligned selected source render; does not identify a video frame or physical presentation instant|
| actual-arc-presentation.json |**6/6/6**|Aligned latest source render; no reopened A01 pair claim|

The video’s PTS and the page’s `realElapsedMs` have no verified mapping. The elapsed times above are never subtracted from video PTS. The bounded conclusion combines the **first recorded visible target**, the immediately preceding recorded unavailable frame, and the **all-render semantic sequence**. At 25fps, a state between adjacent 40 ms samples can remain unrecorded. I make no absolute physical-first-presentation or exact release-to-visible latency claim, and do not turn the recorder resolution into a new impossible product criterion.

## Findings and smallest supported next actions

### F1-P01 — supported recorded recovery observation

**Binding:** A05 /7.15.b, A02 /7.12.b.

**Actual witness:** n198/7.920 unavailable → n199/7.960 Maghrib /00:31 /1h 31m until Isha /Isha 00:31 highlighted. Correct state persists to n570/22.800.

**Bounded consequence:** First recorded visible eligible target and matching row/countdown are available from this exact one-cell artifact; all-render semantics independently contain one correct positive render after settlement.

**Smallest supported next action:** Parent may compose these bounded media findings with independent occurrence1/deadline/source receiving; no new native acquisition requested by this finding.

### F1-P02 — bounded readable-card/partial-text observation

**Binding:** A02 /7.12.b, A07 /7.15.d card only.

**Actual witness:** Full native initial/current, target onset and terminal frames contain all six numeric rows, header, central text and appropriate footer; no confirmed partial-text interval across the complete distinct-state review.

**Bounded consequence:** This new single recording supplies a visible readable-current/recovery witness. Blank/loading phases and ellipsized unavailable footer remain explicit; previous contrary partial-text evidence is not superseded.

**Smallest supported next action:** Keep the phase and recording-resolution limits in whole-contract composition; no contrast or full-date requirement is invented.

### F1-L01 — instrument/association limit

**Binding:** A02 /7.12.b, A05 /7.15.b.

**Actual witness:** Video-only unavailable receipt5/5/2; first-current and arc6/6/6. Recorder25fps; no PTS/page mapping.

**Bounded consequence:** There is no original PNG first-visible proof. The first recorded video target is independently witnessed, while exact physical presentation time and page-event latency remain unclaimed.

**Smallest supported next action:** Retain the mismatch and use separate recorded-frame/all-render evidence; only a separate common-clock timing claim would require an additional presentation witness.

## Exact evidence records

- [frame-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/frame-index.json) — 238626 bytes, SHA-256 `d1b8737a6b7676eca288d741a59be3e1eded0cd5c48e2ba01753322a80f94b78`.
- [native-contact-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/native-contact-index.json) — 9855 bytes, SHA-256 `d2c9309bc407cd3bff54b3a37d414d2bec3f71536eda764a656cb683b9eefadd`.
- [critical-window-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/critical-window-index.json) — 1013 bytes, SHA-256 `b6a8485905e02d68071e2a1f549233d67bbc79da41175e6bf2476f3e03f9b36f`.
- [central-detail-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/central-detail-index.json) — 1487 bytes, SHA-256 `c891dcee9764efe6e9b9a208086d7af491708719c8d7815f12a04b06ecc0d9e8`.
- [source-association.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/source-association.json) — 59584 bytes, SHA-256 `1318365270e39951af588db3ca9f298711bd6516dd7f18c1925130ddea2dcb53`.
- [bounded-observation-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-timing-derived-20261110/bounded-observation-index.json) — 6318 bytes, SHA-256 `246741db2b101110a8c6d9eb7096adee2f94620858e41e42627def2525894955`.

Original trace SHA-256: `b766d26c732320df43ac26c4b76c286d650cb5f95369dec9c81e2bb2c069649e`. All original bytes remain read-only. Earlier Chromium/A01/preservation reports are unchanged.
