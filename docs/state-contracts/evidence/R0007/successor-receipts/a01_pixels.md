# Firefox A01 / 7.12.a — three native arc pairs

**Fresh findings dated 2026-11-10. This is a new comparison, not a recovered historical report.**

All three requested pairs have exactly equal retained actual SVG child bytes and equal measured layout at the `actual-arc` render. The native card and arc images support the intended result: spring changes **2h 30m → 3h 30m**, fall changes **4h 30m → 3h 30m**, and ordinary remains **3h 30m**. The inspected images show the same arc placement, six readable rows, selected Fajr row, header and footer arrangement.

The ordinary comparison carries a concrete environment qualification: its two runs loaded different font resource URLs. Browser identity, requested font CSS, loaded face metadata and measured layout match, and no visible layout regression appears in the compared images. Exact font-response byte equivalence is not established. This finding must remain explicit when the parent composes the evidence.

Reviewer: `/root/native_preservation_review`. Model: **GPT-6 Astra Pro**, self-report. **Findings only; no acceptance, readiness, lifecycle, merge, release or closure authority.** The [structured report](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/firefox_a01_pair_comparison.json) contains exact source pointers, full hashes, environment records, frame PTS, and the qualifications below.

## Binding criterion and scope

The original and FF20 bound recipes contain the same `/comparisonRequirements/0` rule:

> Actual .arc SVG bytes/geometry must match within each same-input interval-only pair; correct vs wall mutant .left differs for spring/fall and agrees for ordinary. Compare original native arc/card/header/footer pixels; no invented tolerance or source-only visual acceptance.

The [acceptance ledger](sandbox:/workspace/scratch/66b3aaff4329/salah_widget/docs/state-contracts/evidence/R0007/acceptance-ledger.md) A01 /7.12.a and 7.12 rows require the real SVG and native arc/layout pair. Its currently read SHA-256 is `2e15b9f4a670212caa4a67ad37ad21deaa13531d61f4826e90de95f198c51fdc`. The case review requirements also bind candidate, source, fixture, driver, browser, OS, fonts, viewport and DPR. These requirements supply the limits of this comparison; no new contrast threshold, date-format rule, pixel tolerance, or absolute physical-presentation requirement is added.

Only these pairs were compared:

| Pair | Healthy case | Wall-subtraction case |
|---|---|---|
| Spring | FF20 `NE07-spring24` | FF20 `NE07-mut-wall-spring` |
| Fall | FF20 `NE07-fall24` | FF20 `NE07-mut-wall-fall` |
| Ordinary | Original-run `NE07-dst-ordinary24` | FF20 `NE07-wall-ordinary-control` |

No broad sky, Moon, motion, science or other consumer review was repeated. The additional A06 seconds-only obligation remains outside these cases. The previous partial-text observations remain unchanged.

## Immutable evidence and comparable inputs

| Run | Bound head | Bound tree | Archive SHA-256 |
|---|---|---|---|
| 42814263285 attempt1 | `387473a36cc2cbc582c5e2720ae5b60bc362c3d7` | `93fc43cde6f4ed47c8d9c1acfd904426aa1d402f` | `79c0b5a142b247c52f1c87a874272fae3153e910a74e793521482f17d72c0a12` |
| 42834337271 attempt1 | `0f2e8e5f6f5317ba88d01f47b49987962dc8d22e` | `765c45c040512de6af49616622a5a435ae7312d6` | `1905e2dfee6c482895beb1ba19e068ae80feaeadaab08305d89ea3100344b653` |

The archive digests were freshly verified during recovery. This new review extracted 98 exact original members into its own `raw` directory. [Raw-member custody](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/raw-members.json) records every original ZIP member, local copy, size and SHA-256. Original archives and previous recovery records were not changed.

Within each pair, `entry`, URL fragment, clock policy, cache seeds, complete response rules and ordered actions match exactly. The shared fragment selects New York coordinates, method2, school0, 24-hour format and `America/New_York`. Current and next-day prayer fixtures contain the same six displayed prayer times. Weather and radar are authored offline failures. The case identifiers and intended wall variant metadata differ; they were not erased from the underlying records.

| Pair | Fixed now UTC | Healthy target UTC | Healthy / wall minutes | Current civil footer |
|---|---|---|---:|---|
| Spring | 2026-03-08 06:30 | 2026-03-08 09:00 | 150 / 210 | 2026-03-08 |
| Fall | 2026-11-01 05:30 | 2026-11-01 10:00 | 270 / 210 | 2026-11-01 |
| Ordinary | 2026-09-07 05:30 | 2026-09-07 09:00 | 210 / 210 | 2026-09-07 |

The runtime clock flags are `TIMESCALE:1`, `FOLLOW_WALL_CLOCK:true`, `ADVANCING:false` in these cases; the fixture fixes the sampled wall epoch. They are not described as `TIMESCALE:0` recovery cases. The target is Fajr05:00 in each pair. The retained decorative pre-first interval stays `prevMin:-270`, `nextMin:300`, `progress:0.631578947368421`, `progressKind:decorative-before-first`. Changing elapsed countdown does not change those wall-arc fields in these witnesses.

The two retained source maps each contain147 entries. Comparing those existing bindings found144 equal hashes and three differences: the recipe file, `r0007_browser.py`, and `r0007_font_observer.js`. This was a digest-map comparison, not a repeated147-file or299-blob qualification campaign. The base generated document hash is identical in every case: `983f8b609eba48821e8d8c539cca7d0b9e40caf3f35a924514a4e93eb24766e9`. The fixture hash is `12e37a2dc97719c3e05de9095b5aa26833f99bdb09bf664d381373cbf09ea18f` in every retained document receipt and in the freshly read fixture bytes.

The [six bound instrument files](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/bound-instrument-source-manifest.json) were read at their literal commits and their byte hashes match the retained source maps. Their [bounded diff](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/bound-instrument-source.diff) changes awaited recovery-observer dispatch and native stylesheet-terminal recording. The six compared cases use identical synchronous actions and do not invoke the changed async recovery barrier. The browser context creation call is unchanged. The fixture's literal wall variant replaces `leftMin, nowEpoch, nextEpoch,` with `leftMin:nextMin-nowMin, nowEpoch, nextEpoch,`. The native observed-document hashes differ by case and variant and are retained individually; they are not mislabeled identical.

## Exact actual SVG and layout comparison

Every case's `actual-arc-presentation.json` reports **before3 / after3 / receipt3**, with `.arc` bounds **x16,y53,width293,height180**. The corresponding original trace record is `/snapshots/3`, repeated at `/snapshots/6`. The retained `.arc.innerHTML` is exactly **71,630 UTF-8 bytes** in all six cases, SHA-256:

`73758a0e4a589f735f3ecaf6dd6fed395d75b295a48454ccd2318c54fa3ead7c`

All16 parsed SVG child nodes match, including complete path strings and every attribute. The comparison uses actual native DOM output retained by the run, not a stub or a newly rendered SVG. The saved files are explicitly `.svg-inner.html` fragments; they are not falsely described as independently captured outer SVG documents. [Computed source comparison](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/source-comparison-data.json) retains the full parsed comparison and source anchors.

| Marker | Retained class | cx | cy | r |
|---|---|---:|---:|---:|
| Fajr | `dot next` | 62.22 | 136.03 | 5 |
| Sunrise | `dot ring` | 74.40 | 104.00 | 5 |
| Dhuhr | `dot` | 149.73 | 0.07 | 5 |
| Asr | `dot` | 190.14 | 31.61 | 5 |
| Maghrib | `dot` | 220.60 | 104.00 | 5 |
| Isha | `dot` | 238.88 | 148.75 | 5 |

The horizon remains y104. The visible Sunrise marker is hollow in the inspected crops. The lower-left glowing current-time ring is distinct from the Fajr `dot next`; they were not conflated in this review.

At actual-arc ordinal3, all13 captured element rectangles and their font-family strings match exactly across each pair. Representative measured rectangles are:

| Element | x | y | Width | Height |
|---|---:|---:|---:|---:|
| Card `.c` | 0 | 0 | 325 | 530 |
| Arc `.arc` | 16 | 53 | 293 | 180 |
| Header buckle | 150 | 16 | 25 | 25 |
| Current name `.cn` | 16 | 120.75 | 293 | 34.5 |
| Target clock `.nt` | 16 | 179.75 | 293 | 46 |
| Countdown `.left` | 16 | 258.29998779296875 | 293 | 24.300003051757812 |
| Six-row group `.times` | 16 | 292.20001220703125 | 293 | 202.1999969482422 |
| Footer `.d` | 16 | 502.3999938964844 | 293 | 17.933334350585938 |

These measurements support the source/layout part only. Actual pixels below provide the visual witness.

## Native pixel witnesses

The six original videos are VP8,370×570,25fps with40ms recorded spacing. Twelve unscaled full frames were freshly decoded: each case's previously reviewed first recorded positive target frame and its terminal recorded frame. The prior onset interpretation is reused from this lane's own earlier review; this step freshly inspected the chosen frames rather than re-examining every video frame. Their exact PTS and source hashes are retained. The arc crops are unscaled rectangular crops of those same frames, not another SVG rasterization.

| Case | First positive frame / PTS | Terminal frame / PTS |
|---|---:|---:|
| `NE07-spring24` | 290 / 11.60s | 440 / 17.60s |
| `NE07-mut-wall-spring` | 124 / 4.96s | 406 / 16.24s |
| `NE07-fall24` | 271 / 10.84s | 441 / 17.64s |
| `NE07-mut-wall-fall` | 254 / 10.16s | 456 / 18.24s |
| `NE07-dst-ordinary24` | 282 / 11.28s | 471 / 18.84s |
| `NE07-wall-ordinary-control` | 178 / 7.12s | 348 / 13.92s |

The frame indexes are zero-based. PTS belongs to each recording; equal fixture wall time does not make equal PTS a synchronized scene-refinement age.

### Spring pair

Both cards show Isha, target 05:00, selected Fajr 05:00 row and the same six-row/arc/header/footer arrangement. Healthy countdown 2h 30m; wall variant 3h 30m. Both dates 2026-03-08. Early wall frame includes Sky preview refining status; it is absent in terminal frame. No visible arc or content-stack displacement in inspected frames.

[Full-card comparison](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/derived/spring-full-card-pair.png) · [Arc comparison](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/derived/spring-arc-pair.png)

### Fall pair

Both cards show Isha, target 05:00, selected Fajr 05:00 row and the same six-row/arc/header/footer arrangement. Healthy countdown 4h 30m; wall variant 3h 30m. Both dates 2026-11-01. Stars and native video samples differ without visible arc or content-stack displacement.

[Full-card comparison](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/derived/fall-full-card-pair.png) · [Arc comparison](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/derived/fall-arc-pair.png)

### Ordinary pair

Both cards show Isha, target 05:00, countdown 3h 30m until Fajr, selected Fajr 05:00 row and date 2026-09-07. The two video pairs and original healthy actual-arc PNG preserve the same visible layout and readable header/footer. Early wall-control frame has fewer bright stars and Sky preview refining status; no visible content-stack shift. Actual font delivery URLs differ, so exact font-response byte identity is unproved.

[Full-card comparison](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/derived/ordinary-full-card-pair.png) · [Arc comparison](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/derived/ordinary-arc-pair.png)

Across the images, rows read Fajr05:00, Sunrise06:00, Dhuhr12:00, Asr15:30, Maghrib18:00 and Isha19:30. The main current label is Isha and the large next target clock is05:00; the highlighted row is Fajr. The NewYork header and civil/Hijri date footer are present and readable. No pair-induced stack displacement or footer clipping was observed in these selected witnesses. This is a bounded visual judgment, not a numeric contrast claim.

The original ordinary [actual-arc PNG](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/raw/42814263285/r0007-native-afjxq8ux/firefox/NE07-dst-ordinary24/attempt-0001/consumer/NE07-dst-ordinary24/actual-arc.png) was also inspected directly. It is140,464 bytes, SHA-256 `d81b95f3405b4190bf1aef07153b126d992c707a5c67deab720400c47ac532b0`, and is bound by the actual-arc receipt to ordinal3. Its bytes are identical to the file named `first-current.png`; that name does not repair the latter's receipt mismatch. The screenshot and video have visibly different outer framing/left strip, so no cross-format pixel subtraction or invented registration was used.

The images are **not claimed pixel-identical**. Star visibility/intensity, scene refinement, native video encoding and the intended spring/fall countdown text differ. The visible `Sky preview · refining…` indicator on the early spring wall and ordinary wall frames, absent later, supplies direct evidence of a differing scene phase. Assigning all sky differences specifically to that phase would be an inference, so it is not asserted as a complete cause. The sky differences do not visibly move the compared arc or text stack. No preservation/motion acceptance is drawn from these stills.

[Full-frame derivation manifest](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/derived-media-manifest.json) and [arc-crop manifest](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/arc-crop-manifest.json) bind every PNG to its exact source video hash, zero-based frame index, PTS and crop operation. No color correction, geometric warping or similarity threshold was applied.

## Capture associations and the real footer transition

All six first-current receipts say **before3 / after3 / receipt2**. They remain mismatched. Original ordinary has native PNGs; FF20's expected acquisition is `native-video-only`, with a1000ms presentation tail and no original screenshot file. Absence of an FF20 PNG is not treated as a failed screenshot acquisition.

The first eligible source render is ordinal2 and actual-arc is ordinal3. The SVG is exactly equal between those ordinals in every case. The target fields and countdown remain equal; page instrumentation timestamps differ. **Whole-card geometry is not identical between those two source snapshots:** `#ah` appends the lunar preview, for example `ه1448-02-19` becomes `ه1448-02-19 | 🌘 19`. Its x changes from209.01666259765625 to168.4499969482422 and width from89.98333740234375 to130.5500030517578. Its y/height and the footer container remain unchanged. This same transition occurs in all six cases; it is a content-span expansion within the stable footer, not an observed pair-induced layout regression. Every selected positive/terminal native frame shows the complete preview.

No exported page-clock-to-video-PTS bridge exists. Consequently, this report does not assign an invented render ordinal to a decoded video frame or promote the eventual PNG to earliest presentation. It composes exact ordinal3 SVG/geometry with visibly eligible video frames and the original ordinal3 ordinary PNG. The physical screen between recorded samples is not claimed observed; recorder resolution is not converted into a new impossible product gate.

## Environment qualification

All six retained browser identities are exactly equal: headed Firefox153.0,Windows AMD64, Playwright-managed executable SHA-256 `9571c9a49d6d4de3e4c3b14e2e4bd6521e5b879f4ab6c95143e2098cb66e6618`. Both run setups record Windows image20261101.353.1,Playwright1.62.0,Node22.23.4 and Python3.12.10. The digest-matched driver context call requests viewport370×570 and device scale factor1; actual video dimensions and presentation viewport receipts are370×570. There is no separate retained evaluated `window.devicePixelRatio` field, so the DPR claim is specifically the bound launch request.

All final font metadata match exactly, including loaded Fraunces400–700 and Inter400/600 face records. The requested Google Fonts CSS URL is identical. Spring and fall pairs also record identical font resource URL sets. Neither run retained font response body digests, so even matching URLs are not promoted to response-byte identity.

The ordinary pair has an additional **observed delivery difference**: original healthy uses `/s/fraunces/v38/...woff2` and `/s/inter/v20/...woff2`; FF20 wall-control uses `/l/font?kit=...` resources. The exact URLs and source `/resourceTiming` records are in the structured report and raw traces. This is not silently normalized away. Matching metadata, glyph appearance and measured rectangles support the bounded layout comparison; they do not establish exact resource or font-byte equivalence.

If the parent requires exact font-response equivalence to receive the cross-run ordinary comparison, the smallest missing observation is any already retained body hash for those actual font loads. If none exists and a matched delivery is required, acquire only the ordinary healthy/wall pair with the same recorded font-delivery profile. This report does not authorize that acquisition or demand a broader renderer replay. The delivery difference itself is not a demonstrated product defect or an invented pixel threshold.

## Findings disposition and remaining limits

| Finding | Affected obligation | Bounded consequence | Smallest supported next action |
|---|---|---|---|
| A01-FF-01: exact SVG/layout equality | A01/7.12.a | All three retained actual-arc pairs have identical SVG and measured layout. | Compose with the native pixel findings. |
| A01-FF-02: native visible comparison | A01/7.12.a, readable card context | Intended countdown differences/agreement appear with no visible pair-induced layout regression in the inspected frames. | No new product observation is justified by these witnesses alone. |
| A01-FF-03: ordinary font delivery difference | Exact font/environment binding | Exact font-response equivalence remains unproved; visible-layout comparison remains available. | Seek existing actual-load body hashes, or a bounded matched-delivery ordinary pair if required by composition. |
| A01-FF-04: capture association limit | First-frame/capture custody | FF20 video frames cannot be assigned invented page ordinals; first-current mismatch and footer content transition remain explicit. | Preserve the bounded association; do not add an absolute physical-presentation gate. |

The previous FF20 partial-text intervals, original-run partial-text observations, failed reordered control and its unqualified companions remain separate findings. This later comparison does not erase or adjudicate them. No source assertion or overall run exit was used as pixel acceptance. No other reviewer conclusion report was read.

This is one reviewer's findings. Attempting to reactivate the existing `prayer_arc_pairs` child returned `agent thread limit reached`; no second-review or panel credit is claimed. The new review reused this lane's own previous individual onset observations but performs the pair comparison afresh. It is not a cold review of that lane's own historical conclusions.

## Continuity and write boundary

A real subagent compaction occurred during recovery. After a read-only controller lookup, the parent supplied the verified receipt `refs/implementaudit/continuity-receipts/r0007-successor-restored-20261110/G0002@242f6198c16d4cc9ec4483585779e5261c24aed5` and confirmed this exact delegated frontier. Root retained lifecycle authority. This report records that parent-provided capsule without claiming independent controller verification.

All new report, raw-copy, source-readback and derivative writes are inside this dated comparison directory. No browser, native workflow, product/source, index or ref write was performed by this lane. The earlier frozen recovery inventory remains unchanged and excludes this new work. Historical completed FF20/diagnostic report bytes remain unrecovered; this file is not presented as either of them.

## Original video custody

- `NE07-spring24`: [original video copy](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/raw/42834337271/r0007-native-emmgjllx/firefox/NE07-spring24/attempt-0001/consumer/NE07-spring24/video/page@cd3f4b4176b389442a58804b6b3b9ffd.webm), 308,076 bytes; SHA-256 `1399e28cc8095e48add5f0b6841bf3026612cf844a35dc34050c2fcffc15440a`.
- `NE07-mut-wall-spring`: [original video copy](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/raw/42834337271/r0007-native-emmgjllx/firefox/NE07-mut-wall-spring/attempt-0001/consumer/NE07-mut-wall-spring/video/page@30886630ac107e69014f2afe74c070bb.webm), 305,308 bytes; SHA-256 `af8e4e545b65e6b680402c71b78a00133bf1ea9b81d58ce045987d15c259ced3`.
- `NE07-fall24`: [original video copy](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/raw/42834337271/r0007-native-emmgjllx/firefox/NE07-fall24/attempt-0001/consumer/NE07-fall24/video/page@808469761c4b1957335d2d8127fb1374.webm), 325,198 bytes; SHA-256 `7f2cc03dab1bd12c26e8df36e1b6c84e0d5c116ca88162176350ce39f962e2ea`.
- `NE07-mut-wall-fall`: [original video copy](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/raw/42834337271/r0007-native-emmgjllx/firefox/NE07-mut-wall-fall/attempt-0001/consumer/NE07-mut-wall-fall/video/page@76aaeab7b7f4c731371049520fe36d7f.webm), 299,872 bytes; SHA-256 `e1e929a4fbe0c01d07e77ce74f0d51b9f43773a827c561ac3e86669864cdcb96`.
- `NE07-dst-ordinary24`: [original video copy](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/raw/42814263285/r0007-native-afjxq8ux/firefox/NE07-dst-ordinary24/attempt-0001/consumer/NE07-dst-ordinary24/video/page@a49d146ff344f80c6453b86efa5a6d37.webm), 312,331 bytes; SHA-256 `bb0422476c4bf40707c0ce40e9faefd600b3018b40ea77ba152c3596cd0d8586`.
- `NE07-wall-ordinary-control`: [original video copy](sandbox:/workspace/scratch/66b3aaff4329/recovery/restored-agent-records/firefox-a01-comparison-20261110/raw/42834337271/r0007-native-emmgjllx/firefox/NE07-wall-ordinary-control/attempt-0001/consumer/NE07-wall-ordinary-control/video/page@ecf914c22af01b32bf57ab3d4837a705.webm), 255,653 bytes; SHA-256 `06197795c3574d809020bc7ae53a28f6660e6d3819d8a717decb272c54655d4e`.

Written at `2026-11-10T19:08:16.962027+00:00`. Report status: **findings only, with explicit ordinary font-delivery qualification and capture limits**.
