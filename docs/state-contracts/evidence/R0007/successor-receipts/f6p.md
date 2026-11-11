# Firefox reordered six — native presentation findings

**FINAL — findings only, revision 2 (report correction).** Written 2026-11-10T20:50:38.462696+00:00. Exact run **42893839473 / attempt 1**, commit **9ed55e91db6df02f2bd1dfde153949a5bfb15811**, tree **786bceafa75231953599cb88bb5dbc2ef74a9eb3**. This final report replaces only this review’s earlier PARTIAL draft. It grants no acceptance, readiness, lifecycle, currentness, merge, release, or closure authority.

## Revision 2 correction history

Root receiving identified a **report-level evidence mismatch** in revision 1: I described all 24 listed faces as loaded by conflating FontFaceSet.status with individual face status. Direct readback of `trace.json#/fonts/faces` in all six original cases shows **3 loaded faces and 21 unloaded faces**, with24 actual display values of swap; the set-level status is loaded. Revision 2 corrects the prose and structured per-face counts. It also makes explicit that F1 had no async barrier, while F2 had the barriers/asymmetric dirty condition. The 11 partial frames, all target observations, video hashes, source anchors, and absence of causal attribution are unchanged.

The exact revision 1 reports are preserved at [revision1 Markdown](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/revision1/firefox_reordered_six_presentation.md) (SHA256 `7fda6008c598034c547c21cb3741fc8a3102f08f894e6a01b62448d42245d265`) and [revision1 JSON](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/revision1/firefox_reordered_six_presentation.json) (SHA256 `3f9ae1e8b8a44989ecd9ec4d63deb07f5091b878ba558dbab527e3a3b61d2eae`). The original delivery inventory is preserved alongside them. [report-correction-v2.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/report-correction-v2.json) records exact raw trace hashes, per-face counts, loaded family/weight records, and this correction. This correction changes no product/source/native/controller state and introduces no new pixel finding.

## Findings at a glance

The two healthy videos show the correct distinct overnight outcomes. The reordered case first records **Isha 00:31 / 1h 31m left until Isha** with the Isha row filled; the ordinary case first records **Fajr 05:00 / 6h 0m left until Fajr** with the Fajr row filled. All four intentional variants have visible outcomes that distinguish them from the fresh reordered control. These are actual media observations, independent of the workflow or producer exit status.

There is also contrary initial readability evidence: **four intervals totaling 11 recorded frames** show status text and empty row boxes while other expected card text is absent. The healthy ordinary case is one of those four. These intervals precede the numeric next-target displays; they must remain in the record even though the later endpoint states are coherent. The cause is unassigned. The binding criterion is the initial/error readable-card portion of **A02 /7.12.b and A07 /7.15.d**, not a newly invented contrast or date-format threshold.

| Case | First recorded named current | First numeric target / key later state | Visible next highlight | Confirmed early partial text |
|---|---|---|---|---|
| `NE07-reordered24` | n193 /7.720 s — Maghrib | n253 / 10.120 s — 00:31; 1h 31m left until Isha | Isha 00:31 | None confirmed |
| `NE07-ordinary24` | n62 /2.480 s — Isha | n159 / 6.360 s — 05:00; 6h 0m left until Fajr | Fajr 05:00 | n60–61 /2.400–2.440 s |
| `NE07-mut-hardcoded-fajr` | n63 /2.520 s — Maghrib | n168 / 6.720 s — 05:00; 6h 0m left until Fajr | Fajr 05:00 | n60–62 /2.400–2.480 s |
| `NE07-mut-name-order` | n63 /2.520 s — Maghrib | n147 / 5.880 s — 05:00; 6h 0m left until Fajr | Fajr 05:00 | n60–62 /2.400–2.480 s |
| `NE07-mut-lost-date` | n62 /2.480 s — Maghrib | No numeric target through n502 /20.080 s; footer resolves n151 /6.040 s | None | n59–61 /2.360–2.440 s |
| `NE07-mut-independent-label` | n61 /2.440 s — Maghrib | n162 / 6.480 s — 00:31; 1h 31m left until Fajr | Isha 00:31 | None confirmed |

All frame numbers are **zero-based native video indexes** and all times in this table are **video PTS seconds**. They are not page-clock times. The full frame associations, original WebM hashes, exact decoded RGB hashes, and derived PNG hashes are in [bounded-observation-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/bounded-observation-index.json).

## Immutable evidence and method

Original archive: [r0007-windows-native-42893839473-1.zip](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/r0007-windows-native-42893839473-1.zip), **4,354,261 bytes**, SHA256 **a2310e03b0f4f75260ae2a17c7cf01ca323821735d73fc17565a4733272f730d**. Its 90-member identity and selected original evidence bytes were rechecked locally. Original extraction: `/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd`. No original file was edited.

The six original videos contain **3,183 frames** at **25 fps** (40 ms PTS spacing), VP8, recorded dimensions **370×570**, time base 1/1000. Every frame was indexed. All **810 unique whole-RGB states** were visually inspected in **137 native-scale contact sheets**; exact RGB duplicates reuse their proven representative without a perceptual threshold. Suspected text cuts in an overview were checked in individual full 370×570 images. Apparent omissions that resolved as complete glyphs in the individual frame were not retained as contrary findings. The six target/footer transition windows were subsequently revisited at full recorded cadence; their labels and panels were checked against the frame index.

Fresh decoding from each immutable original reproduced every indexed RGB hash. Every representative PNG, contact-sheet panel, and contiguous critical-window panel matched its source frame. These checks verify custody and indexing, not visual acceptance. There are **zero original PNG screenshots**: the case receipts explicitly say `native-video-only`, and `nativeImageReceipts` is empty. The PNGs linked here are lossless derivatives of original video, outside the originals. The video compression and recorder cadence remain part of the evidence.

| Case | Original WebM | Bytes / frames | Original WebM SHA256 |
|---|---|---:|---|
| `NE07-reordered24` | [page@4a47e4863e0f087efceec42fde156b1d.webm](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-reordered24/attempt-0001/consumer/NE07-reordered24/video/page@4a47e4863e0f087efceec42fde156b1d.webm) | 331,957 / 641 | `1d394f7c0e26296cc1cd29df6d1b19aeabdf137deea8fe37e467882bbdf8f9fa` |
| `NE07-ordinary24` | [page@cd9554e932ae0fabad7f9284b8c76039.webm](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-ordinary24/attempt-0001/consumer/NE07-ordinary24/video/page@cd9554e932ae0fabad7f9284b8c76039.webm) | 333,764 / 494 | `381530b4fce99c8194454d0fcedca07608e1d6c1b6c63cbd968e10fcbb99d5be` |
| `NE07-mut-hardcoded-fajr` | [page@85a7ea1920088616b9683f8a79798ead.webm](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-mut-hardcoded-fajr/attempt-0001/consumer/NE07-mut-hardcoded-fajr/video/page@85a7ea1920088616b9683f8a79798ead.webm) | 364,055 / 517 | `41367df46a3e63d14e701bb66f6a7b2932c98c3fc6fbe16ed1a4d93fb100032f` |
| `NE07-mut-name-order` | [page@141612381d1be38cc9ee056e9b8802c5.webm](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-mut-name-order/attempt-0001/consumer/NE07-mut-name-order/video/page@141612381d1be38cc9ee056e9b8802c5.webm) | 331,218 / 497 | `1179f18807fae76bef57a7f6a3dd405242f7320158bea17109d94a3bb456fc77` |
| `NE07-mut-lost-date` | [page@cb7c452616243a0fe522ee5bc000326b.webm](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-mut-lost-date/attempt-0001/consumer/NE07-mut-lost-date/video/page@cb7c452616243a0fe522ee5bc000326b.webm) | 311,905 / 503 | `3b7ccabc7eeefa6511a9f2d60c5c0664fe4ccd0a4468940d4a243ee91b18eb60` |
| `NE07-mut-independent-label` | [page@98902013726b9e2767c0e7ecba47b5bd.webm](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-mut-independent-label/attempt-0001/consumer/NE07-mut-independent-label/video/page@98902013726b9e2767c0e7ecba47b5bd.webm) | 372,697 / 531 | `a8a7ed505f32313daf3d43f12db8d6aa01497dfe0705625702b0b3e14f5dcfd7` |

The raw binding in [bound-cases.json](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/bound-cases.json) names recipe SHA256 `23dc2b48e41675333951909692d6b9f4f1e07f11bf97fd47d769f44a1995baae`, the exact commit/tree above, and `oraclesChanged:false`. All six document receipts identify source-index SHA256 `983f8b609eba48821e8d8c539cca7d0b9e40caf3f35a924514a4e93eb24766e9` and fixture SHA256 `12e37a2dc97719c3e05de9095b5aa26833f99bdb09bf664d381373cbf09ea18f`. Injected observed-document hashes are retained per case in the JSON report and source index; they are not asserted identical across variants.

All six original browser identities agree: **headed Firefox 153.0, Windows AMD64**, Playwright-managed Firefox 1538, executable SHA256 `9571c9a49d6d4de3e4c3b14e2e4bd6521e5b879f4ab6c95143e2098cb66e6618`. The presentation requests specify a 325×530 CSS card, 293×180 arc at (16,53), and 370×570 viewport. The full native video shows the whole card and surrounding viewport. **DPR was not independently found in the identity/presentation fields inspected by this lane**; I do not invent DPR 1 or a full-environment qualification. The source receiver owns that broader binding. In every raw final trace, **FontFaceSet.status is `loaded`, 24 faces are listed, and the individual face statuses are 3 `loaded` plus 21 `unloaded`; all 24 have actual `display:swap`**. The set-level status must not be conflated with all faces being loaded. These final status values do not identify the cause of any transient text absence.

## Healthy controls and intentional negatives

The criteria below refer to [acceptance-ledger.md](sandbox:/workspace/scratch/66b3aaff4329/salah_widget/docs/state-contracts/evidence/R0007/acceptance-ledger.md) (locally read SHA256 `2e15b9f4a670212caa4a67ad37ad21deaa13531d61f4826e90de95f198c51fdc`). ES07-01 requires reordered tomorrow Isha 00:31 /08-09-2026 /91 minutes; ES07-02 preserves ordinary Fajr 05:00 /360 minutes; ES07-11 requires key, clock, date, zone, epoch, highlight, and consumer text to identify one selection. ES07-12 keeps current timetable/calendar usable when only the next endpoint is unavailable. ES07-14 binds actual native evidence to the candidate. This review does not re-decide A01 or the wider NY/DST/first-dirty A04/A05/A06 obligations.

### F6-P01 — NE07-reordered24

**Binding criterion:** ES07-01, ES07-11, ES07-12, ES07-14. **Finding type:** OBSERVED_HEALTHY_ENDPOINT.

The recording is blank through n188 (7.520 s). The first card at n189 (7.560 s) already contains all six row names with dash times, central dashes, the unavailable-prayer message, and unavailable date labels. The first named current card is n193 (7.720 s): Maghrib, a central dash, and Countdown unavailable. Its six numeric rows are Fajr 05:00, Sunrise 06:00, Dhuhr 12:00, Asr 15:30, Maghrib 18:00, Isha 00:30. Maghrib is outlined; Isha 00:30 is treated as past.

The unavailable state persists through n252 (10.080 s). At n253 (10.120 s), the first recorded numeric target is 00:31, the countdown is 1h 31m left until Isha, and Isha 00:31 is the filled next row. Maghrib remains the current name and outlined18:00 row. The footer shows 2026-09-07CE and 1448-02-19. That coherent target persists through n640 (25.600 s), the final frame. No earlier wrong numeric target or confirmed partial text was found in the recorded sequence.

The visible footer is the current civil date, not a printed promise that the next target occurs on that date. The separate final completed receipt binds the Isha endpoint to 08-09-2026, UTC, epoch 1788827460000, 91 minutes after accepted now 1788822000000. This is source context supporting date/zone association, not an assertion that those fields are printed in the pixels.

**Actual media anchors:** [n253 /10.120 s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-reordered24/frames/frame-000253.png), PNG SHA256 `a9d8c8c8c8b1aaf0646d23f2f42acf4fff7fb3b0b85c54890c6b5ec3c605ce62`, decoded RGB SHA256 `93f73a9bafd01057b20929755464c5ee55be5c3b4bf5cd9f1ebddec79e08ba90`; [contiguous native-cadence transition](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-reordered24/critical-windows/target-onset-01.png); [final n640 via exact representative n640](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-reordered24/frames/frame-000640.png).

**Separate raw source anchor:** [original trace.json](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-reordered24/attempt-0001/consumer/NE07-reordered24/trace.json) `#/snapshots/7`, completed ordinal 5, page `realElapsedMs=9129`. Trace SHA256 `65fb29a9769f9d3e36a2afa1436ba4ca57e46a673e841d1bff8338645210e33b`. This pointer is not assigned to a video PTS.

**Bounded consequence and next action:** The healthy reordered cell visibly selects tomorrow Isha rather than Fajr and retains the six current timetable rows. This supports the bounded recorded native endpoint witness. Parent may compose these original pixels with the independently received source/selection evidence; no new acquisition is requested by this finding.

### F6-P02 — NE07-ordinary24

**Binding criterion:** ES07-02, ES07-11, ES07-12, ES07-14. **Finding type:** OBSERVED_HEALTHY_ENDPOINT_WITH_INITIAL_READABILITY_EXCEPTION.

After blank frames 0–15, an authored Loading display is recorded at n16 (0.640 s) through n59. The partial error card at n60–61 is retained below. At n62 (2.480 s), the complete current card reads Isha, dash, and Countdown unavailable; the ordinary current timetable ends with Isha 19:30, which is outlined. All six row names and times are present.

The first next target is n159 (6.360 s), immediately following an unavailable frame at n158 (6.320 s): 05:00, 6h 0m left until Fajr, Fajr 05:00 filled, Isha 19:30 outlined. The footer shows 2026-09-07CE and 1448-02-19. This remains coherent through final frame n493 (19.720 s; exact representative n489). The final source receipt separately binds Fajr to 08-09-2026 UTC, epoch 1788843600000, 360 minutes from the unchanged now.

This distinct ordinary result is the legitimate Fajr companion. It supports the bounded ES07-02 endpoint observation while retaining, rather than excusing, the initial readability exception.

**Actual media anchors:** [n159 /6.360 s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-ordinary24/frames/frame-000159.png), PNG SHA256 `4858926b50ffd4e9be8f450aa3cd41d4be6c10d5d50473d10b708e48875a16d4`, decoded RGB SHA256 `6a63eb3c6c76fc7e89df3239d2b8ce635a37f56dc04b702c694dca8e2e22782b`; [contiguous native-cadence transition](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-ordinary24/critical-windows/target-onset-01.png); [final n493 via exact representative n489](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-ordinary24/frames/frame-000489.png).

**Separate raw source anchor:** [original trace.json](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-ordinary24/attempt-0001/consumer/NE07-ordinary24/trace.json) `#/snapshots/7`, completed ordinal 5, page `realElapsedMs=5698`. Trace SHA256 `f4d256f0e9c905a23a8ca734846b8c9fe73e01fa50644dc013239fa35804b8d0`. This pointer is not assigned to a video PTS.

**Bounded consequence and next action:** The healthy ordinary cell visibly retains the legitimate Fajr outcome and does not reject all overnight targets. Its earlier partial error text is a separate observed readability exception, not erased by the later correct target. Compose this endpoint witness with ES07-02 source evidence and retain F6-P07 for the earlier two recorded partial frames.

### F6-P03 — NE07-mut-hardcoded-fajr

**Binding criterion:** ES07-01, ES07-11. **Finding type:** OBSERVED_INTENDED_NEGATIVE.

The first card at n58 (2.320 s) has the complete six named dashed rows and unavailable dates; no authored Loading card is recorded in this video. At n60–62, the status changes to Countdown unavailable with arc and row outlines present but the current name, central dash, row text, and date footer absent. The complete Maghrib unavailable card returns at n63 (2.520 s).

At n168 (6.720 s), following n167 (6.680 s) unavailable, the variant displays 05:00, 6h 0m left until Fajr, and a filled Fajr 05:00 row. Maghrib 18:00 remains outlined and Isha 00:30 remains past. This wrong Fajr target persists through n516 (20.640 s). The fresh healthy reordered companion with the same fixture selects Isha 00:31/91 instead. The pixels therefore show the intended hardcoded-Fajr defect, with the earlier partial interval separately retained.

**Actual media anchors:** [n168 /6.720 s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-hardcoded-fajr/frames/frame-000168.png), PNG SHA256 `0686a199b132108aab8040bb0bac3e481a1cddeb86fc59e7864834f967711ea2`, decoded RGB SHA256 `b4d26153c5f7f67aefe99aa24c36d86e3880ca8fd88680cba08783aed0d8e0e0`; [contiguous native-cadence transition](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-hardcoded-fajr/critical-windows/wrong-target-onset-01.png); [final n516 via exact representative n516](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-hardcoded-fajr/frames/frame-000516.png).

**Separate raw source anchor:** [original trace.json](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-mut-hardcoded-fajr/attempt-0001/consumer/NE07-mut-hardcoded-fajr/trace.json) `#/snapshots/9`, completed ordinal 6, page `realElapsedMs=5607`. Trace SHA256 `532e22d188a4373514af11a00d8ccc1eff5c27f15d1f5ae9c117288898ed45ba`. This pointer is not assigned to a video PTS.

**Bounded consequence and next action:** The commissioned hardcoded-Fajr variant visibly selects the later Fajr endpoint instead of the healthy same-input Isha 00:31/91 outcome. This is actual native mutation discrimination, not an inferred product regression. Retain the same-invocation healthy comparison and the original wrong-target frame; keep the separate initial partial-text finding.

### F6-P04 — NE07-mut-name-order

**Binding criterion:** ES07-01, ES07-11. **Finding type:** OBSERVED_INTENDED_NEGATIVE.

An authored Loading display begins n15 (0.600 s). A complete unavailable-prayer card occurs n57–59, followed by the individually confirmed missing-text interval n60–62. The complete Maghrib/dash/Countdown unavailable card is first recorded at n63 (2.520 s).

At n147 (5.880 s), following unavailable n146 (5.840 s), the target becomes 05:00 with 6h 0m left until Fajr and the Fajr 05:00 row filled. Maghrib 18:00 stays outlined; Isha 00:30 stays past. The wrong result persists through final n496 (19.840 s; exact representative n488). This matches the commissioned negative’s semantic wrong-selection result and is visibly distinct from healthy reordered Isha 00:31/91.

**Actual media anchors:** [n147 /5.880 s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-name-order/frames/frame-000147.png), PNG SHA256 `6389ef7a21a264c086864a44d9797e70363c519c360efe04274fe4d1859dfb09`, decoded RGB SHA256 `2cd114edc3961e30aa32f874043201b63f9071af8b60d9c22d6377fe0981a68b`; [contiguous native-cadence transition](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-name-order/critical-windows/wrong-target-onset-01.png); [final n496 via exact representative n488](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-name-order/frames/frame-000488.png).

**Separate raw source anchor:** [original trace.json](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-mut-name-order/attempt-0001/consumer/NE07-mut-name-order/trace.json) `#/snapshots/7`, completed ordinal 5, page `realElapsedMs=5440`. Trace SHA256 `94dce6df724922ac065c28c1b37a0ae59542ba6fc17dabf9a977371738301f0a`. This pointer is not assigned to a video PTS.

**Bounded consequence and next action:** The commissioned name-order variant visibly substitutes Fajr 05:00/360 for the healthy same-input Isha 00:31/91. Its outcome is distinguishable in the actual card pixels. Retain the same-invocation healthy comparison and this native wrong-target evidence; retain the separate initial partial interval.

### F6-P05 — NE07-mut-lost-date

**Binding criterion:** ES07-11, ES07-12. **Finding type:** OBSERVED_INTENDED_NEGATIVE.

An authored Loading display starts n14 (0.560 s); n59–61 show the partial error card. A complete Maghrib current card appears at n62 (2.480 s), with a central dash and Countdown unavailable. All six current timetable rows are present, Maghrib 18:00 outlined, and Isha 00:30 past.

No numeric next target or next-filled row appears anywhere in the recording. At n151 (6.040 s), the footer resolves to 2026-09-07CE and 1448-02-19, but the dash and Countdown unavailable remain. They persist through final n502 (20.080 s), whose exact representative is n434. The final completed receipt separately records tomorrowDay08-09-2026 while nextKey/nextDate remain null and the selection reason is no-supported-future-event. Combined with the healthy same-input control, that later whole-recording absence is the intended lost-date negative witness. The normal pre-adoption unavailable state alone would not establish a defect.

**Actual media anchors:** [n151 /6.040 s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-lost-date/frames/frame-000151.png), PNG SHA256 `f0233b5a8f840e307d3270f51c1231191e9ca7ecc7ae4f3b0795fef1b49a995a`, decoded RGB SHA256 `97a90d882732b7390c5195045f21b428937a663ab6cf7e100d02735f34619e67`; [contiguous native-cadence transition](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-lost-date/critical-windows/footer-resolution-target-absent-01.png); [final n502 via exact representative n434](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-lost-date/frames/frame-000434.png).

**Separate raw source anchor:** [original trace.json](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-mut-lost-date/attempt-0001/consumer/NE07-mut-lost-date/trace.json) `#/snapshots/8`, completed ordinal 5, page `realElapsedMs=5654`. Trace SHA256 `8aae299dc8f41b5fe119caefc0ab0410fe3c7d4b8b2cd72e9c15ab332fa1782e`. This pointer is not assigned to a video PTS.

**Bounded consequence and next action:** The lost-date variant never displays a numeric next target or next-filled row within its full recording. Its footer resolves while the current timetable remains, and the raw final completed render independently records tomorrow adoption with no supported future event. The expected initial unavailable state is not itself classified as a defect. Retain the whole-recording absence plus the final adopted source receipt and healthy reordered companion; do not credit pre-adoption unavailability alone as mutation discrimination.

### F6-P06 — NE07-mut-independent-label

**Binding criterion:** ES07-11. **Finding type:** OBSERVED_INTENDED_NEGATIVE.

An authored Loading display starts n17 (0.680 s). The first full named current card at n61 (2.440 s) is Maghrib/dash/Countdown unavailable. There is no recorded Prayer times unavailable card and no individually confirmed partial-text interval in this video.

At n162 (6.480 s), following unavailable n161 (6.440 s), the card displays 00:31 and 1h 31m left until Fajr, while Isha 00:31 is the filled next row and Maghrib 18:00 is outlined. The contradiction is visible within the same native frame: the label names Fajr, while the clock, minutes, and filled row correspond to Isha. It persists through n530 (21.200 s; exact representative n528). The final raw completed receipt also identifies Isha/00:31/91 while its consumer text says until Fajr. This directly witnesses the intended ES07-11 contradictory-label defect.

**Actual media anchors:** [n162 /6.480 s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-independent-label/frames/frame-000162.png), PNG SHA256 `717da8b90387390c309f4134a091eae524d7b8107cd03ae54fc92434841e370c`, decoded RGB SHA256 `dff2024c535759a890dde1c13b3fae40d0c8dbc0bd1169372f0f04f9cf691a02`; [contiguous native-cadence transition](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-independent-label/critical-windows/wrong-label-onset-01.png); [final n530 via exact representative n528](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-independent-label/frames/frame-000528.png).

**Separate raw source anchor:** [original trace.json](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42893839473-1-original/r0007-native-7kqmvypd/firefox/NE07-mut-independent-label/attempt-0001/consumer/NE07-mut-independent-label/trace.json) `#/snapshots/9`, completed ordinal 6, page `realElapsedMs=5963`. Trace SHA256 `2e1e5f645ef22538a208082fca97204f04b8d83eec39df05fb6e23e39a0363fb`. This pointer is not assigned to a video PTS.

**Bounded consequence and next action:** The independent-label variant visibly names Fajr while the clock, minutes, and filled row identify Isha. This is a direct same-card contradictory-consumer witness against ES07-11. Retain this actual contradictory frame and the healthy reordered reference; no additional renderer or native campaign is justified by this bounded finding.

## F6-P07 — initial partial text, preserved as contrary evidence

**Criterion:** A02 /7.12.b requires a readable six-row 325×530 card with header/footer through first/loading/error/recovery states; A07 /7.15.d preserves the shared readable card. The actual witness here is missing visible text in otherwise formed error/current-unavailable cards. No contrast ratio, forced full target-date label, or elapsed-loading threshold has been introduced.

| Case | Actual recorded interval | What is visible / absent | First complete card after interval |
|---|---|---|---|
| `NE07-ordinary24` | [n60@2.400s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-ordinary24/frames/frame-000060.png), [n61@2.440s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-ordinary24/frames/frame-000061.png) | Header/Prayer times unavailable and six row boxes visible, central dashes/row names/times/date footer absent; complete current card n62. | [n62@2.480s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-ordinary24/frames/frame-000062.png) |
| `NE07-mut-hardcoded-fajr` | [n60@2.400s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-hardcoded-fajr/frames/frame-000060.png), [n61@2.440s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-hardcoded-fajr/frames/frame-000061.png), [n62@2.480s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-hardcoded-fajr/frames/frame-000062.png) | Arc, UTCFIXTURE, Countdown unavailable, six empty row boxes and outlined Maghrib-position row visible; current name/central dash/row names/times/date footer absent. Complete Maghrib card n63. | [n63@2.520s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-hardcoded-fajr/frames/frame-000063.png) |
| `NE07-mut-name-order` | [n60@2.400s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-name-order/frames/frame-000060.png), [n61@2.440s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-name-order/frames/frame-000061.png), [n62@2.480s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-name-order/frames/frame-000062.png) | Arc, UTCFIXTURE, Countdown unavailable, six empty row boxes and outlined Maghrib-position row visible; current name/central dash/row names/times/date footer absent. Complete Maghrib card n63. | [n63@2.520s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-name-order/frames/frame-000063.png) |
| `NE07-mut-lost-date` | [n59@2.360s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-lost-date/frames/frame-000059.png), [n60@2.400s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-lost-date/frames/frame-000060.png), [n61@2.440s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-lost-date/frames/frame-000061.png) | UTCFIXTURE/Prayer times unavailable and six empty row boxes visible; central dashes/row names/times/date footer absent. Complete Maghrib card n62. | [n62@2.480s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/NE07-mut-lost-date/frames/frame-000062.png) |

These are **four distinct initial intervals, 11 recorded frames**, not eleven browser exceptions or eleven separate product diagnoses. They occur after any recorded authored Loading state, during the initial error/current-unavailable sequence, and before the first numeric target. Because there is no verified clock bridge, I do not label them physically before or after the fixture’s page-clock release. The video sequence itself establishes the unavailable-before-numeric-target phase. Neither healthy reordered nor independent-label has a confirmed comparable partial interval in its recorded cadence.

The partial ordinary/lost-date error cards retain the UTCFIXTURE header, Prayer times unavailable, and six empty row boxes; central dashes, row names/times, and date footer are absent. The hardcoded/name-order partial cards retain the arc, UTCFIXTURE, Countdown unavailable, six boxes, and an outlined Maghrib-position row; the current name, central dash, row text, and date footer are absent. The adjacent complete frames contain those missing elements. This is stronger evidence than an apparent omission in a multi-image overview: all 11 were individually inspected in their full original-video-derived native frames.

**Bounded consequence:** a blanket assertion that every initial/error/current-unavailable frame is fully readable is unsupported by these recordings. The later correct healthy targets and the expected four negative outcomes remain separately observed. The intended faint styling of past rows, ordinary unavailable labels, and compact ellipsized date-status footer are not themselves classified as additional violations. In complete frames the row letters and times are present; no contrast threshold is invented.

**Cause and smallest supported next action:** attribution to product rendering, font loading, browser/compositor, environment, or recording is unestablished. All six raw final traces have set-level status loaded, 24 listed faces with **3 loaded and 21 unloaded**, and actual display swap for all 24. Set-level or final-settled flags cannot explain or erase earlier pixels. The parent should retain these 11 exact frames and adjacent complete frames, inspect the existing early render/font records as needed, and keep a scoped readability disposition open until its consequence is decided. This finding does not call for a broad native, celestial, motion, or source campaign. It does not itself authorize or require a new acquisition.

### Exact partial-frame custody

| Case / frame | Video PTS | Derived PNG SHA256 | Decoded full-RGB SHA256 |
|---|---:|---|---|
| `NE07-ordinary24` n60 | 2.400 | `c4b80cd25f1d8e9cbe1eb1cc3453ce01e99e1baa411899a8ab5485afd3d4724a` | `455921433521aa5ea7d6e2ceb6a7a6eab839e2b4bb4ab3235002ed049e26427a` |
| `NE07-ordinary24` n61 | 2.440 | `f37397e3ba486299c57af3e2023f8aba4501145a0cc8121df9635022ae7f30df` | `4cad0c83cb700169fb875dd5772980d3211236bdf78429ded4199ef5162eb152` |
| `NE07-mut-hardcoded-fajr` n60 | 2.400 | `49aad965d2a9dde60ad2aae83b759166987a710932506e6e8c0aca0be337a815` | `10248b3643bf77bac72c26b370f2f39bd028b602e61d7a09297ccbb362c46e5f` |
| `NE07-mut-hardcoded-fajr` n61 | 2.440 | `71151a711ae1902a805968fa01ee1b84836926d2d361d94a04240970d0323c43` | `db080374f383f121c32d8bf25777d87ece848fd6cb7b92e1ee1260860d16db17` |
| `NE07-mut-hardcoded-fajr` n62 | 2.480 | `446944519e5b01fefa807e9f0cab9a5a9f7ddc466fb85023c22a05ee1e7b1e7f` | `b6a8690c8146abbe98667bc9d8ca6558c8bacc6b2cb11c08653ad62931632dd1` |
| `NE07-mut-name-order` n60 | 2.400 | `59753ca6fadedce1f454fc1e0af46039b7448d72c0f019998ec24091eb10f6f9` | `ad460f2f5a0acd2a6d395fc7172cc12a0977f435bc3f79343b18d2e987c2bb01` |
| `NE07-mut-name-order` n61 | 2.440 | `c1f839fab0981fced1c8f3f2079f3d8573e3ebcdbfe9e4a72993477061c9e3f4` | `190058589acd6e04afac909fc5f735b4c102d1c944775e5db2593e366c9b337c` |
| `NE07-mut-name-order` n62 | 2.480 | `33bf2fa3d67a999c63b6d85687c0f87bcaea45f3779af10fe0a05679ea1730cb` | `ff595bdc0ec1fd626b969b598f2467712282ea08435fd7ae7ebac736cd1f832b` |
| `NE07-mut-lost-date` n59 | 2.360 | `d46356b618c154f8d4b8c7f5d2beeac332e65a566fd9b0f01f53ced0efbc9d81` | `5bda29992b00dbd681f68f84cd2dec66b9d91588970f2588f995103c7dc9bec2` |
| `NE07-mut-lost-date` n60 | 2.400 | `3e41ef7644b8605ced0ba7bbffd484cc35ca901d67b0bfe0446dc1af4128575c` | `f3ad9a9231ebc4f41506a53f1db08a85f268d13c91a0bb137f7ba08dbe9ca48e` |
| `NE07-mut-lost-date` n61 | 2.440 | `a4e2f9e5620f36861aefdc27660cc6b1b2813f2c0413a93b95c6037deb8c680e` | `2a504f3395aa192e19905ed444430ed5fd0671f2e419cadd4e5c5082983fbc80` |

## Source sequence, input comparison, and capture limits

The original inputs use `index.html` and the same latitude/longitude, UTCfixture label, 24-hour format, UTC zone, and 23:00 simulation hash. Their clock policy fixes **2026-09-07T23:00:00Z**, epoch **1788822000000**. Entry, hash, clock policy, and cache seeds match across all six. Every mutant has response rules exactly matching the healthy reordered case. The ordinary healthy fixture intentionally differs: its current Isha is 19:30 rather than the reordered 00:30. The source, fixture, browser executable, and invocation match; per-case injected document hashes differ as recorded. These are fresh same-invocation control comparisons, not credit borrowed from the failed earlier reordered acquisition. Exact file hashes and safe raw fields are in [source-association.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/source-association.json).

The nine ordered actions wait for admitted today and pending tomorrow, make an unavailable capture request, **directly release tomorrow**, wait for JSON settlement, sleep 250 ms, take a read-only checkpoint, request the first matching admitted-current/tomorrow capture, and request the arc capture. **There is no asynchronous recovery barrier in these F6 cases and `asyncWaitReceipts` is absent.** The first-current predicate checks admitted current/tomorrow dates, not the expected target key or clock. **F1’s reordered timing case had no async barrier. F2’s NY pair had the barriers and an asymmetric dirty condition. F6’s six cases have no async barrier.** No F2 barrier qualification is transferred into this report, and no barrier credit is implied for F1. `readOnly:false` capture metadata is retained in the raw action list; this media lane does not reinterpret driver internals or confer their source qualification.

All 32 unique completed-render snapshots keep the same wall epoch, TIMESCALE=0, FOLLOW_WALL_CLOCK=false, and ADVANCING=false. Initial ordinal 1 has render=null and the unavailable-prayer DOM state. Every subsequent completed snapshot before the final adoption render has a null next target and Countdown unavailable. The final completed snapshots produce the outcomes shown below. These raw semantic sequences corroborate the selection order; they are not substituted for a visual observation of any missing glyph.

| Case | Completed ordinal @ page realElapsedMs sequence | Held tomorrow / release+settle (page ms) | Final raw result |
|---|---|---|---|
| `NE07-reordered24` | 1@1181, 2@1544, 3@7016, 4@7058, 5@9129 | 1550 / 9085 | Isha / 00:31 / 91 |
| `NE07-ordinary24` | 1@809, 2@1191, 3@2142, 4@2188, 5@5698 | 1197 / 5647 | Fajr / 05:00 / 360 |
| `NE07-mut-hardcoded-fajr` | 1@792, 2@1176, 3@2055, 4@2140, 5@2247, 6@5607 | 1182 / 5542 | Fajr / 05:00 / 360 |
| `NE07-mut-name-order` | 1@721, 2@1119, 3@2090, 4@2168, 5@5440 | 1126 / 5380 | Fajr / 05:00 / 360 |
| `NE07-mut-lost-date` | 1@755, 2@1170, 3@2153, 4@2242, 5@5654 | 1176 / 5642 | null / — / nonfinite; endpoint-unresolved |
| `NE07-mut-independent-label` | 1@746, 2@1141, 3@2258, 4@2315, 5@2357, 6@5963 | 1149 / 5893 | Isha / 00:31 / 91; DOM until Fajr |

Exact event pointers are retained per case in the JSON report. Tomorrow body-hold is `#/events/10`; release/json-settle is `#/events/13` and `#/events/14` except hardcoded and independent-label, where they are`#/events/14` and `#/events/15`. The 32 unique completion pointers are also retained there. The 21 intervening error-output snapshots record expected Countdown unavailable output; they are **not 21 thrown render/page errors**. All six `pageErrors` arrays are empty. Healthy producer exits are 0; the four negatives exit 1 with the expected assertions after normal process exit. No exit value or overall SUCCESS label was used as pixel proof.

| Case | Unavailable before / after / selected receipt ordinal | First-current and actual-arc before / after / receipt ordinal | Expected negative diagnostic |
|---|---|---|---|
| `NE07-reordered24` | 4 / 4 / 2 | 5 / 5 / 5 | Healthy source assertions; independent pixels still required |
| `NE07-ordinary24` | 4 / 4 / 2 | 5 / 5 / 5 | Healthy source assertions; independent pixels still required |
| `NE07-mut-hardcoded-fajr` | 5 / 5 / 2 | 6 / 6 / 6 | AssertionError("render/nextKey: expected 'Isha', observed 'Fajr'") |
| `NE07-mut-name-order` | 4 / 4 / 2 | 5 / 5 / 5 | AssertionError("render/nextKey: expected 'Isha', observed 'Fajr'") |
| `NE07-mut-lost-date` | 4 / 4 / 2 | 5 / 5 / 5 | AssertionError("render/nextKey: expected 'Isha', observed None") |
| `NE07-mut-independent-label` | 5 / 5 / 2 | 6 / 6 / 6 | AssertionError('missing actual consumer text: until Isha') |

**F6-L01, association limit:** unavailable requests selected the earlier ordinal 2 while the surrounding actual ordinal was 4 or 5. They are not promoted to an exact earliest-visible still. First-current/arc ordinals match, but these are video-only receipts and they do not include a verified PTS bridge. Therefore this report distinguishes: **(a)** first recorded visible target/countdown/highlight plus separately retained all-completed-render semantics; **(b)** unmatched initial unavailable capture ordinals; and **(c)** physical first presentation between recorder frames, which is not claimed. The matching-tomorrow-settled checkpoints have their own later page times; they are not used as render completion or video timestamps.

The 40 ms recorder cadence is a practical evidence bound. It is not converted into a new impossible product requirement or an automatic reason for rerun. The parent can compose the recorded native onset and semantic order with its whole-contract review. A stronger assertion of exact physical latency or exact frame-to-ordinal coincidence would require a synchronized observation; this report does not invent one.

## Verification, independence, and delivery boundary

Fresh verification compared **56 selected original files** (the six videos, their selected raw receipts/traces/producer files, and the root bound packet/summary) directly with the immutable archive. All 6 video hashes, all 3,183 fresh decoded frame hashes/PTS values, all 810 unique PNG hashes, all 137 contact-sheet panels, and all 18 critical-window sheets matched. The verification record also confirms the frozen F1, F2, and Chromium-six Markdown/JSON reports remain byte-for-byte unchanged. No duplicate pixel review of those completed scopes was performed. See [verification.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/verification.json), SHA256 `0799c884887004611ea607b206565e5445a6b6dd1aa9126e213c44069d5820d5`.

Reviewer self-report: **GPT-6 Astra Pro**, agent `/root/native_preservation_review`. This is a continuing independent media lane, with its own earlier media-review context. I did not author product or observer changes in this commission, and I did not read the other receiving lane’s conclusion reports. I used raw originals, persisted own observations/indexes, and exact frames. The role is not represented as a new cold reviewer or a second human review.

A real context compaction occurred during finalization. I reread the supplied implementaudit spine, recovered the persisted findings/indexes, revisited the six critical transitions and final representative frames, and freshly reverified media custody. The parent-supplied compaction capsule was **G0007@b3a54b387a95c15094003260f68fd996f3a5458c**. During finalization the parent supplied **G0008@569b953d2c2c034e2fb8821cb9fb7d0ab289ba97**, with a separate later diagnostic HEAD1075bd47/tree4d209e. That later diagnostic does not alter this F6 immutable subject. I retained it as the parent’s report only; I did not invalidate/resume or otherwise write a shared controller, and I do not claim independently established currentness. Earlier attempted child continuation was unavailable due the host’s thread limit; no child work is credited to this six-case report.

Authorized writes were limited to these two F6 reports and their bounded derivative directory. No browser/server/workflow/native acquisition, source/index/ref/controller change, network publication, Moon/science/motion/request-storm campaign, or lifecycle action was performed. Earlier F1/F2/Chromium/A01/preservation evidence remains separately bound. This report’s FINAL status describes the finished findings document, not qualification of the product or closure of the governing audit.

### Deliverables

- [firefox_reordered_six_presentation.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/reviews/firefox_reordered_six_presentation.json): Structured findings and exact source/frame anchors.
- [bounded-observation-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/bounded-observation-index.json): 104 selected native frame anchors, contiguous windows, and phase ranges.
- [critical-window-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/critical-window-index.json): 12 contiguous windows,18 native-scale sheets.
- [source-association.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/source-association.json): Safe selected raw source, fixture, event, capture, font, and producer context.
- [video-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/video-index.json): Six original-video hashes and coverage.
- [verification.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/verification.json): Fresh custody, full re-decode, and frozen-report verification.
- [inventory.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-reordered-six-derived-20261110/inventory.json): Actual written-file inventory; excludes its own hash to avoid circularity.

