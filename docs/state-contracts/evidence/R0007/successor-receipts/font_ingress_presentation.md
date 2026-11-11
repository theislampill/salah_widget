# Independent font ingress presentation review

Status: **FINAL — complete recording coverage; bounded pixel findings only.**

## Finding

The normal arm contains **one observed interval where previously readable populated text disappears or becomes partial**. Frame **337**, PTS **13.480 s**, is readable. Frames **338–346**, PTS **13.520–13.840 s**, lose the center name/time, most of the countdown, all six row names/times, the populated footer, and the dash in the circular header control. Frame **347**, PTS **13.880 s**, restores them. The nine missing/partial presentations occupy **nine encoded 40 ms frame slots, [13.520, 13.880), or 0.360 s on this WebM timeline**. That is not a claimed physical onset, physical first-paint measurement, page elapsed duration, or host-clock duration.

The fallback arm shows **no populated prayer state anywhere in its recording**. After its startup viewport it displays “Prayer times unavailable,” named prayer rows with dash times, and unavailable date labels through frame **330**, PTS **13.200 s**. It therefore provides no observed equivalent populated-state fallback transition against which to qualify the normal arm's loss. A paired populated-readability conclusion is **unestablished**.

The normal arm restores the lost text and remains visibly populated through its last frame, **693 at 27.720 s**. No additional disappearance of previously visible required text is observed in the reviewed encoded frames. The historical 23 missing-text intervals and original readability criteria remain **open**.

## Evidence identity and independence

The original ZIP is `/workspace/scratch/66b3aaff4329/native-artifacts/r0007-windows-native-42920631317-1.zip`, **3,111,326 bytes**, SHA-256 `50e90fb8196e73d9a9af5ac5bc68ba9f95df032c524980e73a4fdb0aa028e5e5`. Size and digest were verified locally before review, and the digest was rechecked after derivation. The original extracted artifacts were read only.

| Recording | Source bytes | Original WebM SHA-256 | Frames | Exact RGB states viewed | First/last frame PTS | Container duration |
|---|---:|---|---:|---:|---|---|
| NE07-fall24 | 479,317 | `aa7f9d8876da3d0e6530439c8a7006a8c80993fcc3720c73c211f0d8a98b2ae9` | 694 | 172 | 0.000 / 27.720 s | 27.760 s |
| NE07-font-fallback-fall24 | 201,167 | `fc88320160d5bf874d1ca6fdd8dd91eb45e034debbc2abd956c9724fa2497281` | 331 | 85 | 0.000 / 13.200 s | 13.240 s |

The supplied publication identifiers are commit `4bac6a4781fce62f08ab550a20fe5234d3ebb746` and tree `a5e51a591200296e3e73b9ecedbd8c0539e07ee5`. This pixel receiver did not independently verify that publication binding and does not assume its separate receipt.

This reviewer did not author the product, harness, or acquisition and did not read the other receiver's verdict or the author's implementation report. Only the top-level trace field names/types/counts were inspected; no trace state or timing content supplied the pixel classifications. No browser, native app, network action, or new acquisition was used. No repository/index/ref/controller or original artifact was modified. Root retains execution, publication, acceptance, and whole-contract closure authority.

## Complete coverage and derivation

Both original VP8 recordings were decoded at **370 × 570 RGB24**, with native PTS retained and no temporal sampling. Every frame has a 40 ms duration, all native PTS increments are 40 ms, and indices are zero-based. All **1,025** frames map to **257** exact RGB states. Every one of those states was actually viewed in **23 full-frame contact sheets**, whose embedded video frames remain at their original pixel dimensions. Supplemental full frames, before/during/after strips, and nearest-neighbor enlarged crops were also viewed.

Deduplication used the complete frame's RGB bytes. A second full decode compared **every original frame byte-for-byte** against its mapped representative PNG and checked its SHA-256. No visually similar state, text-equivalent state, near-duplicate, or short interval was removed. Repeated states retain every original index and PTS in `frame-map.csv`; `exact-rgb-runs.json` retains chronological runs; `observations-per-frame.csv` provides the visible state and region observations for every frame.

| Recording | SHA-256 of concatenated decoded RGB bytes |
|---|---|
| NE07-fall24 | `1f33f495ac90eba9bfab1c0680de1bc8f7c4506b011f67ddbd0dd0c8498ecd9d` |
| NE07-font-fallback-fall24 | `91131694c23a15c4deee296bc406c37781aaa8c5092cba38636058bd6057b426` |

The derivation preserves **35 named boundary frames**, **210 unaltered regional crops**, and **210 corresponding 3× nearest-neighbor inspection views**. Each crop has a recorded source index, PTS, rectangle, and hash in `detail-assets.json`. `viewed-evidence.json` distinguishes the images actually inspected; it does not claim that every generated crop was individually viewed. Complete coverage comes from viewing every exact full-frame state and verifying the equality map for every original frame.

## Observed chronology

### NE07-fall24

| Frames, inclusive | First–last PTS (seconds) | Visible presentation |
|---|---|---|
| 0–9 | 0.000000–0.360000 | Mostly pale viewport; narrow left edge fragment; product panel and required text absent. |
| 10–46 | 0.400000–1.840000 | Dark rounded panel, two center dash placeholders, Loading… status; header label, prayer rows and footer text not present. |
| 47–282 | 1.880000–11.280000 | NEWYORK; center dash placeholders; Prayer times unavailable; all six row names and six dash times; Gregorian date unavailable and Hijri date unavailable. |
| 283–337 | 11.320000–13.480000 | Isha, 05:00, 4h 30m left until Fajr, all six named/timed rows and populated footer visible. |
| 338–346 | 13.520000–13.840000 | Isha and 05:00 absent; countdown retains only 4h 30m; all six row names/times and footer text absent. NEWYORK and graph/card structure remain. Header circular control loses its dash. |
| 347–693 | 13.880000–27.720000 | Center, complete countdown, all six row names/times, header control dash and populated footer restored and remain visible through the last frame. Later glyph-shape changes remain readable. |
### NE07-font-fallback-fall24

| Frames, inclusive | First–last PTS (seconds) | Visible presentation |
|---|---|---|
| 0–45 | 0.000000–1.800000 | Mostly pale viewport; narrow left edge fragment; no product panel or readable required text. |
| 46–330 | 1.840000–13.200000 | NEWYORK; center dash placeholders; Prayer times unavailable; all six row names and six dash times; Gregorian date unavailable and Hijri date unavailable. No populated prayer center/time/countdown or populated row times appears before recording end. |

The normal arm's small footer status reads “Real sky loading…” for frames **47–81** (1.880–3.240 s), then “Sky preview · refining…” for **82–131** (3.280–5.240 s), then is absent from frame **132** (5.280 s). The unavailable date labels remain. The fallback arm shows the same two small status messages for **46–50** (1.840–2.000 s) and **51–151** (2.040–6.040 s), respectively; the small status line is absent from **152** (6.080 s), with both unavailable date labels retained through the end. These are observed text transitions, not inferred page-event timestamps.

No “Loading…” panel is visible in the fallback recording's encoded frames; its first captured panel is already the explicit unavailable presentation. No claim is made about an uncaptured physical state between frames.

## Glyph-level loss and recovery

The readable populated presentation has header **NEWYORK**, center label **Isha**, center time **05:00**, and countdown **4h 30m left until Fajr**. All six rows are readable:

| Row | Visible time |
|---|---|
| Fajr | 05:00 |
| Sunrise | 06:00 |
| Dhuhr | 12:00 |
| Asr | 15:30 |
| Maghrib | 18:00 |
| Isha | 19:30 |

The populated footer visibly contains **2026-11-01 CE**, **1448-02-19**, and a moon-like symbol with **19**. A small glyph before the Hijri date is visible but is not confidently transcribed at this resolution.

During frames 338–346, **Isha**, **05:00**, **left until Fajr**, every one of the six row names, every numeric row time, and the populated footer are absent. Only **4h 30m** remains from the countdown. **NEWYORK** remains readable, while the circular control's dash disappears. The graph, nodes, progress strip, row outlines, Fajr highlight, moon, and star background remain visible. This is a selective text loss in a populated card, not an entirely blank recorded frame. All listed missing text returns together in frame 347.

| Frame | Native PTS, seconds | Observation | Exact RGB SHA-256 |
|---:|---:|---|---|
| 337 | 13.480000 | last_readable_before | `812a9be08da0a267d79756ff4e128426110186ecc6d9739712297bc7e0d33c5c` |
| 338 | 13.520000 | missing_partial | `b6b5f336e2cc82082478e205f9e71e8d1d69bc8c7919cd3a113c26a1954f558f` |
| 346 | 13.840000 | missing_partial | `42bea265dd23eae29a7570a59276bcb7a01fe5a87cd89a5c7608cee899bc5967` |
| 347 | 13.880000 | first_readable_after | `4def996f25ba1043c4787db865d3ca3ae26ad990f14ad7cdea36adb4c57021d8` |

The full eleven-frame boundary mapping—last readable, all nine missing/partial frames, and first restored frame—is in `loss-interval-frames.json`, including full-frame PNG hashes. Frames 342 and 344 are byte-identical to viewed representative 340; frames 343 and 345 are byte-identical to viewed representative 341. The remaining missing frames 338, 339, 340, 341, and 346 are distinct states and were individually present in the viewed contact sheet. The narrow interval was not sampled away.

The further recorded changes at **398→399** (15.920→15.960 s; footer glyph shape/spacing) and **521→522** (20.840→20.880 s; center-time and row-time glyph shapes) retain readable required text. They are recorded as visible changes only; no font-family or request-level causal attribution is made.

## Bounded conclusion and limitations

- No WebM/page/host clock origin has been established. All indices and times are zero-based decoded frame indices and native WebM PTS. No host or page event is aligned to these frames, and no tolerance or physical first-paint time is invented.
- This is one controlled diagnostic acquisition. It does not establish the historical cause of 23 earlier missing-text intervals or close the original readability criteria.
- The fallback recording has no populated prayer center/time/countdown or populated row-time state. Its lack of a populated-state loss cannot establish readability of the corresponding populated fallback state or a valid paired outcome.
- Actual pair realization, CSS identity, cleanup, font-ingress control correctness, acquisition provenance beyond the supplied files, and acceptance are separate receiving gates; this pixel review assumes none of them.
- Both routed arms share cache-disabled conditions. This pixel finding is not a cache-enabled comparison or a test of font-service suppression.
- The count of 21 unloaded font faces is not treated as a defect. Pixels do not identify a font family, causal request, browser subsystem, Gecko defect, or root cause.
- The recordings are 370x570 lossy VP8 at 25 fps. Exact coverage concerns every encoded frame; it cannot exclude a physical event between captured frames, before the first frame, after the last frame, outside the captured viewport, or hidden by recording compression.
- Blank startup, visible dash placeholders, loading text, and explicit unavailable text are documented as observed presentation states, not automatically reclassified as defects or proof that data should already be available.
- The small glyph preceding the Hijri date is visible in populated frames but is not confidently transcribed at this capture resolution. The right footer also visibly includes a moon-like symbol and 19. The bottom browser status line is clipped by the captured lower edge; it is not used to establish network delivery or clock alignment.

## Deliverables and audit hashes

All new work is confined to `/workspace/scratch/66b3aaff4329/recovery/font-ingress-presentation-derived` and the two requested review files. The complete machine-readable review is `/workspace/scratch/66b3aaff4329/recovery/reviews/font_ingress_presentation.json`. The complete file/hash inventory is `/workspace/scratch/66b3aaff4329/recovery/font-ingress-presentation-derived/evidence-manifest.json`, SHA-256 **`35a5d414734a1c7138e3766346ff7f875cc3a5ff3c1ce856e2d67c921f359a3d`**. It includes the decoder and detail-derivation scripts, exact frame/PTS maps, decode receipts, byte-equality verification, observed-state maps, all contact sheets, full frames, crops, and the actual-view log. The inventory excludes itself and the subsequently generated report receipt to avoid circular hashes.

`report-receipt.json` records SHA-256 values for both final review files and the inventory. `coverage-verification.json` mechanically verifies complete frame/state coverage; `viewed-evidence.json` lists all actual image views and their hashes. Original ZIP and WebM hashes were unchanged at finalization. No whole-contract readiness or closure decision is made here.
