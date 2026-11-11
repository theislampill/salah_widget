# Firefox font-use diagnostic — native presentation findings

**FINAL — findings only.** Written 2026-11-10T21:06:01.188466+00:00. Exact run **42898554321 / attempt 1**, commit **1075bd47b9a392cf2a7760c6f722c04911ffad54**, tree **4d209e02084c99002ddf0f7f7509d62f3c409b79**. This report finishes the commissioned two-video diagnostic review. It supplies no product acceptance, readiness, currentness, lifecycle, merge, release, or closure authority.

## Result: neither arm recurs; the diagnostic is inconclusive

Neither complete recording reproduces the earlier partially textless formed-card/empty-row-box failure pattern. The original fall case and the disposable fallback-font case both show complete unavailable-prayer cards and later readable, coherent **Isha current / Fajr 05:00  / 4h 30m remaining** target cards. Their letter shapes differ visibly, but both retain six named timetable rows, the next-row fill, the current-row outline, header, and footer.

This is the **“neither recurs → inconclusive”** outcome declared in the prospective [font-use plan](sandbox:/workspace/scratch/66b3aaff4329/recovery/font-use-plan.md) (SHA256 `e7e4fed6b66780220835d2e11571ce8d1a8bcde69ee7c3011425eb9b2dd123a0`). Without recurrence in the baseline arm, the pair does not discriminate the cause of the historical failures or demonstrate a cure. Historical contrary frames remain in their separately bound records. This result alone does not justify an identical repeat or a production font-policy change.

| Observation | Original NE07-fall24 | Disposable NE07-font-fallback-fall24 |
|---|---|---|
| Whole recording |474 frames,124 exact RGB states; final n473 /18.920 s |433 frames,104 exact RGB states; final n432 /17.280 s |
| Before first widget card |No visible widget through n93 /3.720 s |No visible widget through n11 /0.440 s |
| Authored Loading |No such state recorded |n12 /0.480 s through n58 /2.320 s |
| First complete unavailable-prayer card |n94 /3.760 s |n59 /2.360 s |
| Last unavailable-prayer frame |n162 /6.480 s |n123 /4.920 s |
| First recorded current plus target |n163 /6.520 s |n124 /4.960 s |
| Visible target in both |05:00; 4h 30m left until Fajr; Fajr 05:00 filled; Isha 19:30 outlined |Same target/name/countdown/highlights, with different letter shapes |
| Confirmed partial-text intervals |None in recorded cadence |None in recorded cadence |

Frame numbers are zero-based. Every time in this table is **that recording’s video PTS**, not page time or a shared start clock. The baseline’s initial white page and the fallback’s authored Loading phase are retained as actual differences. They are not converted into a font-cause diagnosis, a speed result, or a new loading-duration threshold.

![First recorded complete target in each arm](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/first-target-pair.png)

The paired image compares the same named visible state. Its two PTS values are not synchronized. Exact original-video/decoded-frame/derived-PNG hashes are retained in [pair-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/pair-index.json) and [bounded-observation-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/bounded-observation-index.json).

## Original evidence and complete-cadence method

Archive: [r0007-windows-native-42898554321-1.zip](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/r0007-windows-native-42898554321-1.zip), **3,333,958 bytes**, SHA256 **59ab89acf24f5f8c8b16da6a7af914ec9a0ccc8781a83d407050734f936945db**. The archive has 38 members. Its embedded acquisition binding names the exact commit/tree above and recipe SHA256 `c49212867eec372aed08a95373b17d14d97cca6a7cf67eb6e99e9865fdab22d1`. Run/job/artifact identities in the commission are 42898554321 /130118068056 /13802525743; those are parent-receipted identities, while the archive bytes and embedded binding were checked locally. No remote query or acquisition was performed by this reviewer.

Original extraction: `/workspace/scratch/66b3aaff4329/native-artifacts/42898554321-1-original/r0007-native-yeo722p8`. Both original videos are VP8, 370×570, 25 fps, time base 1/1000. The complete 907-frame population was indexed at 40 ms recorded PTS intervals. All 228 unique whole-RGB states were visually inspected through 39 native-scale sheets. Exact duplicate RGB states reuse a proven representative image; there was no perceptual threshold or 0.5-second sampling. Every suspected overview-only text cut was checked in its individual 370×570 native frame. Those checks did not confirm any missing text. The fallback n316 header was additionally inspected in a bounded nearest-neighbor enlarged crop, which reads NEWYORK completely.

Five contiguous onset windows and two native state-comparison pairs were checked. Fresh decoding from the original videos reproduced every indexed frame hash. Every unique PNG and every contact/window/pair panel matched its source RGB bytes. There are **zero original screenshot PNGs**; all presentation receipts say native-video-only and nativeImageReceipts is empty. The linked PNGs are lossless derivatives of the original compressed video, stored outside the originals.

| Case | Original video | Bytes / frames | Original SHA256 |
|---|---|---:|---|
| `NE07-fall24` | [page@99eda0b14d33524efc1e66252fd3043d.webm](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42898554321-1-original/r0007-native-yeo722p8/firefox/NE07-fall24/attempt-0001/consumer/NE07-fall24/video/page@99eda0b14d33524efc1e66252fd3043d.webm) | 308,391 /474 | `5912218dc2dcccfaf7af742535a4b8dc277d6691a8cea3149d61e5e8dd6a7daa` |
| `NE07-font-fallback-fall24` | [page@5bdbc6023fc0624cef3ce8d69b6cd06f.webm](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42898554321-1-original/r0007-native-yeo722p8/firefox/NE07-font-fallback-fall24/attempt-0001/consumer/NE07-font-fallback-fall24/video/page@5bdbc6023fc0624cef3ce8d69b6cd06f.webm) | 313,060 /433 | `0a82e33b759a651a6152033e0851440b075d85464239ef51fc05d112449bd36b` |

## Actual visible sequences

### NE07-fall24

Frames 0–93 show no widget card; browser transfer/status text can appear outside the later widget area. The first recorded card at **n94 /3.760 s** already has NEWYORK, both central dashes, Prayer times unavailable, all six named rows with dash times, and Gregorian/Hijri date-unavailable labels. The same complete unavailable-prayer state continues through n162. No separate authored Loading card or named-current/Countdown unavailable intermediate state was recorded.

At **n163 /6.520 s**, immediately after unavailable n162 /6.480 s, the card shows Isha as current,05:00 as the next time, 4h 30m left until Fajr, Fajr 05:00 filled, and Isha 19:30 outlined. The other rows are Sunrise 06:00, Dhuhr 12:00, Asr 15:30, and Maghrib 18:00. The footer reads 2026-11-01CE and 1448-02-19, with the small phase/19 indicator. This complete state remains through final **n473 /18.920 s**, whose exact RGB representative is n467. No earlier wrong numeric target or individually confirmed partial-text interval was found.

**Exact first error witness:** [n94 /3.760 s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/NE07-fall24/frames/frame-000094.png); PNG SHA256 `ffe2e638d3779672b709b65c4782b1ad87baacc79ac6a269d0527ee3915aa69c`; full decoded RGB SHA256 `25452a7cb992d0eec01933faa8e76a05a247939c83f1b926a97160eba7d56943`.

**Exact first target witness:** [n163 /6.520 s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/NE07-fall24/frames/frame-000163.png); PNG SHA256 `9ad3dd2f21a1901e71e805781b927036a3b8ca25bfae76c0f61fd044e3bf357f`; full decoded RGB SHA256 `db1b76262318c5a94ecaff48d8000983fec60c537606c92350859013f2435dbc`.

**Contiguous full-cadence anchors:** [first-error](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/NE07-fall24/critical-windows/first-error.png), [first-target](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/NE07-fall24/critical-windows/first-target.png). [Final recorded state via exact RGB representative](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/NE07-fall24/frames/frame-000467.png).

### NE07-font-fallback-fall24

Frames 0–11 show no widget card. At **n12 /0.480 s**, the authored Loading state appears with two central dashes; the timetable and date text have not yet been introduced. That loading state continues through n58. It is recorded as the authored loading phase, distinct from the historical formed cards whose row boxes were present but expected row text was missing.

At **n59 /2.360 s**, immediately after loading n58 /2.320 s, the unavailable-prayer card is complete: NEWYORK, two central dashes, Prayer times unavailable, six named dashed rows, and unavailable Gregorian/Hijri date labels. It remains complete through n123. At **n124 /4.960 s**, immediately following n123 /4.920 s, the current/next state is Isha /05:00  / 4h 30m left until Fajr. Fajr 05:00 is filled, Isha 19:30 outlined, and all six row names/times are present. The footer shows 2026-11-01CE and 1448-02-19 with the small phase/19 indicator. This remains complete through final **n432 /17.280 s**, exact representative n424.

The fallback target digits and serif names differ visibly from the baseline, and the body text shapes differ. In the actual native frames these glyphs remain readable and within their card, row, and footer regions. No confirmed partial-text interval, contradictory target label, or new text clipping was found in the recorded sequence.

**Exact first error witness:** [n59 /2.360 s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/NE07-font-fallback-fall24/frames/frame-000059.png); PNG SHA256 `2e4e96be5e1cdcc37639a1982b3081814373e9de9c11ed187b0f7079bf79c672`; full decoded RGB SHA256 `03b608fc9609f8aede54c1ab8b028645c4cb04bb08e665cf094cafc65dd69816`.

**Exact first target witness:** [n124 /4.960 s](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/NE07-font-fallback-fall24/frames/frame-000124.png); PNG SHA256 `8c7308118c61d340d159a408f9b020ac4aa93fadb7a81fe1ab7102cc4e4e84a9`; full decoded RGB SHA256 `a056d29bdbe27698b7ed4b38ae67beafab2bb33fd2e2c85a34cb9bb282387db0`.

**Contiguous full-cadence anchors:** [authored-loading](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/NE07-font-fallback-fall24/critical-windows/authored-loading.png), [first-error](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/NE07-font-fallback-fall24/critical-windows/first-error.png), [first-target](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/NE07-font-fallback-fall24/critical-windows/first-target.png). [Final recorded state via exact RGB representative](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/NE07-font-fallback-fall24/frames/frame-000424.png).

## Font status and geometry: separate observations

The previous F6 report’s set-status/per-face-count error was corrected and revision2 frozen before interpreting this pair. Here the counts come directly from each original `trace.json#/fonts/faces`, not from FontFaceSet.status alone.

| Raw final font observation | Baseline | Fallback |
|---|---:|---:|
| FontFaceSet.status |loaded |loaded |
| Listed faces |24 |24 |
| Individual face status loaded |3 |0 |
| Individual face status unloaded |21 |24 |
| Actual display swap |24 |24 |

The baseline’s three loaded entries are Fraunces normal weight 400–700, Inter normal 400, and Inter normal 600. The fallback has no loaded entry among the 24 registered faces. Both final startup-settlement records report settled=true, pendingDeferred=0, and no lifecycle errors. These final records are not assigned retrospectively to the first recorded card: each retained render snapshot exposes only the font-set string loaded, without per-face counts. Neither the string nor the final counts prove whether a particular glyph was visible; the native frames answer that separate question.

The recorded declared/computed stacks change as expected for the diagnostic: the baseline body stack begins Inter and the display stack begins Fraunces; the fallback begins system-ui for body text and Georgia for display text. The countdown’s ui-monospace stack is retained. A captured font-stack string does not identify the exact resolved font file used for every glyph. Complete served-document reconstruction and the claim that only the commissioned two replacements occurred belong to independent source receiving. This lane verified the retained case-input objects differ only in caseId and variant, and inspected the actual captured stacks, hashes, geometry, and pixels.

At each arm’s last unique completed render (`#/snapshots/3`, ordinal 3), the recorded containers below are **exactly equal in the raw numeric values**, without an invented tolerance. Values displayed in this table are rounded to three decimals for readability; the JSON report keeps the exact recorded values and equality checks.

| Selector | Common x,y,width,height (CSS px) | What this establishes |
|---|---|---|
| `.c` | 0, 0, 325, 530 | Requested card container |
| `.cn` | 16, 120.75, 293, 34.5 | Current-name container |
| `.nt` | 16, 179.75, 293, 46 | Next-time container |
| `.left` | 16, 258.3, 293, 24.3 | Countdown container |
| `.times` | 16, 292.2, 293, 202.2 | Six-row timetable container |
| `.d` | 16, 502.4, 293, 17.933 | Date footer container |
| `.arc` | 16, 53, 293, 180 | Arc container |
| `.buckle` | 150, 16, 25, 25 | Header control container |

The native pair shows complete text fitting those regions, while the letters themselves differ. Matching container geometry is not a claim of identical glyph dimensions, rasterization, background scene, or rendering latency. Incidental background changes remain outside this text diagnostic; no Moon/science/motion comparison was undertaken.

## Raw input and render association

Both retained inputs use the same index.html entry, NewYork coordinates/label, 24-hour format, America/New_York zone, fixtures, cache seeds, actions, oracle, and deadline. Direct comparison found only caseId and variant differing. The fixed accepted now is **2026-11-01T05:30:00Z**, epoch **1793511000000**; the literal target is **2026-11-01T10:00:00Z**, epoch **1793527200000**, giving 270 minutes. The separate receipt identifies local Fajr 05:00 on 01-11-2026 in America/New_York. The visible NEWYORK header is a location label, not a printed IANA-zone or epoch value.

The seven unchanged case actions wait for the held capture-current body, take a read-only loading capture, sleep 250 ms, release that body, wait for an admitted current render, request first-current, and request actual-arc. The first-current predicate requires admitted current date/timetable, not the expected target name or clock. No async barrier is introduced into these cases. No native acquisition or local product render was run by this review.

| Raw source sequence | Baseline page realElapsedMs | Fallback page realElapsedMs |
|---|---:|---:|
| Initial completed ordinal 1, `#/snapshots/0` |909 |786 |
| Held current body, `#/events/5` |1053 |853 |
| Release and JSON settle, `#/events/6` and `/7` |5965 |4340 |
| First admitted completed ordinal 2, `#/snapshots/2` |6042 |4421 |
| Completed ordinal 3, `#/snapshots/3` |6153 |4441 |

All six unique completed snapshots keep the same fixed wall epoch. Each initial render is null with the unavailable-prayer DOM text. Both subsequent completed renders in each arm have Isha/Fajr 05:00/270 and the same selected date/zone/epoch. The raw footer at ordinal 2 lacks the small phase/19 suffix; ordinal 3 includes it. The first recorded complete target frames already show that suffix. This content is consistent with the later recorded state, but it is not used to invent an exact PTS-to-ordinal assignment. All-render semantics and actual native pixels remain complementary evidence.

| Presentation request | Both arms: before / after / selected receipt ordinal |
|---|---|
| Loading, video-only |1 /1 /1 |
| First-current, video-only |**3 /3 /2** |
| Actual-arc, video-only |3 /3 /3 |

The first-current ordinal mismatch is retained. An earlier receipt selected as ordinal 2 is not a still image of ordinal 2, and there are no screenshot files to promote into such proof. The video establishes the first **recorded** target display; the complete semantic sequence shows no intervening wrong next target. **There is no verified bridge from video PTS to page realElapsedMs.** The report makes no absolute physical first-presentation claim between 40 ms recorder samples and no cross-arm speed claim from the different PTS values. This intrinsic resolution limit alone does not request a rerun or create an impossible product requirement.

| Case | Raw trace SHA256 | Post-admission pointers |
|---|---|---|
| `NE07-fall24` | `a72d9f94bb6267fe9ebea8206d016cedc287c7a9cf902cd26f8b0828bc2ba9df` ([trace.json](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42898554321-1-original/r0007-native-yeo722p8/firefox/NE07-fall24/attempt-0001/consumer/NE07-fall24/trace.json)) | `#/snapshots/2`, `#/snapshots/3` |
| `NE07-font-fallback-fall24` | `64b6252809d28f7c3c301f3d591528cd0c59e047cea0d02ec2f0a6c577f26e0b` ([trace.json](sandbox:/workspace/scratch/66b3aaff4329/native-artifacts/42898554321-1-original/r0007-native-yeo722p8/firefox/NE07-font-fallback-fall24/attempt-0001/consumer/NE07-font-fallback-fall24/trace.json)) | `#/snapshots/2`, `#/snapshots/3` |

Both raw producers exited 0 with terminalState exited and empty pageErrors arrays. The native producer still labels independent pixel review as required. Exit status and font-set/DOM values were not used to infer readability. Browser identities match: headed Firefox 153.0 on Windows AMD64, Playwright-managed executable SHA256 `9571c9a49d6d4de3e4c3b14e2e4bd6521e5b879f4ab6c95143e2098cb66e6618`. Source-index SHA256 is `983f8b609eba48821e8d8c539cca7d0b9e40caf3f35a924514a4e93eb24766e9`; fixture SHA256 is `50642398dbb3ebacb36912cb2977b69e1520d60aaaf5f2dc4d2de63db6c107d2`. Per-arm observed-document hashes are retained in the structured report. The presentation requests specify a 325×530 CSS card in a 370×570 viewport. No unrecorded DPR or complete source qualification is invented here.

## Binding consequence and smallest next action

The relevant readability obligations are A02 /7.12.b and A07 /7.15.d in [acceptance-ledger.md](sandbox:/workspace/scratch/66b3aaff4329/salah_widget/docs/state-contracts/evidence/R0007/acceptance-ledger.md). ES07-11/14 and the original fall case’s A04 metadata govern coherent consumers and native binding. This diagnostic records a positive bounded observation for the two actual sequences: their complete error and target cards are readable at recorded cadence. It does not close the earlier readability findings, expand the native acceptance denominator, or qualify the disposable fallback variant for production.

The prospective plan distinguishes four outcomes: baseline-only recurrence would narrow the optional-font hypothesis; recurrence in both would show font use alone insufficient; fallback-only recurrence would be contrary or inconclusive; and **no recurrence in either arm is inconclusive**. The last outcome is the actual observation here. The smallest supported action is to preserve this result beside the historical failures and return it to the parent’s existing cause/contract review. No additional run, product font change, provider campaign, or broad renderer/science work is requested by this finding.

## Tooling limitation and independence

One exploratory trace inspection mistakenly printed an unfiltered DOM object. Its oversized output was truncated and contained product HTML and embedded image/SVG data. That output is not credited as a complete read or as pixel evidence, and its payload is not reproduced in this report. The output path was stopped. Recovery explicitly whitelisted short named-selector text, geometry, declared font stacks, render values, event fields, and per-face counts. A local helper also initially expected snapshot fonts to be an object; the actual string field was then handled separately from the final face array. Both are tooling-only limitations, with no original artifact mutation or established product consequence. See [tooling-limitations.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/tooling-limitations.json).

Reviewer self-report: **GPT-6 Astra Pro**, agent `/root/native_preservation_review`. This is the continuing media-review lane, not a new cold reviewer or a second human review. Actual full recordings were inspected before their current semantic/font/geometry summaries. I did not read independent source-receiving conclusions. I read the prospective plan and checked the exact plan-review file hash without importing its conclusions. Earlier unavailable child-thread capacity was handled serially; no child result is credited here.

The parent’s latest supplied continuity capsule is **G0009@ef586463da096e6daaeb96993034dfb9216202b3**. It is retained as parent-reported context, not an independent currentness determination. F6’s authorized report-only correction was completed first: exact revision1 preserved, revision2 frozen, all pixel fields unchanged. This FUSE work changed only its assigned reports and derivative directory. No browser/server/native/workflow, source/index/ref, network/publication, or shared-controller action was performed.

## Verification and deliverables

Fresh verification matched **20 selected original files** directly to the immutable ZIP, all 907 redecoded frame hashes/PTS values, all 228 unique PNGs, all 39 contact sheets, five onset windows, and two comparison pairs. The previously frozen F1/F2/Chromium reports and corrected F6 revision2 reports remained byte-for-byte unchanged during this review. Hash preservation is a custody statement, not a re-endorsement of prior conclusions.

- [firefox_font_use_presentation.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/reviews/firefox_font_use_presentation.json): Structured findings, exact frames, source pointers, per-face counts and limits.
- [bounded-observation-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/bounded-observation-index.json): 38 selected native anchors and whole-recording phase ranges.
- [critical-window-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/critical-window-index.json): Five contiguous full-cadence transition windows.
- [pair-index.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/pair-index.json): First-target and final-state pairs with exact source associations.
- [source-association.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/source-association.json): Whitelisted raw context without HTML or embedded image payloads.
- [verification.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/verification.json): Fresh original-byte/full-frame/index checks.
- [inventory.json](sandbox:/workspace/scratch/66b3aaff4329/recovery/firefox-font-use-derived-20261110/inventory.json): Actual written-file inventory, excluding its own hash.

Verification SHA256 `5974c7d4384544408842826a79b376cc68526787a36ac60734ac0a0d2b1d59f9`. Final report status describes completion of this bounded findings document only. **The diagnostic is inconclusive; historical readability remains open.**
