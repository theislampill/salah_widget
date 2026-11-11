# R0007 request02 native presentation receiving

Status: **FINAL — complete encoded-frame coverage; bounded pixel findings only.**

Both original recordings reach a readable populated prayer card. No selective disappearance or partial loss of previously readable required text was observed in any of the **1,052 encoded frames**, represented by **274 exact full-frame RGB states actually viewed**. This is a finite pixel observation. The supplied workflow remains **FAILURE** (setup success, observe failure, upload success); no normal pass, qualified font intervention, native acceptance, or whole-contract closure is claimed. The historical **24 recorded intervals remain open** and the user's font hypothesis remains **unproven**.

## Finite native recording result

All indices are zero-based. Both files are VP8, **370 × 570**, with nominal and average rates **25/1**, native time base **1/1000**, every PTS increment **40 ms**, and every reported native frame duration **40 ms**. The half-open intervals below sum encoded frame slots; they are not physical presentation durations or page/host elapsed time.

| Recording | Frames / distinct RGB states | Native first–last PTS | Container duration | Readable populated window |
|---|---:|---|---|---|
| NE07-fall24 | 555 / 144 | 0.000–22.160 s | 22.200 s | Frames 473–554; [18.920, 22.200); 82 frames, 3.280 s |
| NE07-font-fallback-fall24 | 497 / 130 | 0.000–19.840 s | 19.880 s | Frames 446–496; [17.840, 19.880); 51 frames, 2.040 s |

The normal arm's frame **472** (18.880 s) is unavailable; **473** (18.920 s) is completely populated. The fallback arm's **445** (17.800 s) is unavailable; **446** (17.840 s) is completely populated. Each last unavailable frame, first populated frame, and final encoded frame was inspected in a native-size strip; the first and final populated frames were supplemented by 3× nearest-neighbor full-frame views. No partially populated transition frame was observed.

## Loading, unavailable, and text-absence chronology

| Arm | Frames inclusive | Encoded interval | Visible state |
|---|---|---|---|
| Normal | 0–18 | [0.000, 0.760) | Pale startup viewport with narrow left fragment; product card and required text absent. |
| Normal | 19–86 | [0.760, 3.480) | Dark card, two center dashes, readable “Loading…”; location, prayer rows, and footer text absent. |
| Normal | 87–472 | [3.480, 18.920) | NEWYORK; center dashes; complete “Prayer times unavailable”; six readable row names with dash times; both unavailable date labels. |
| Normal | 473–554 | [18.920, 22.200) | Complete readable populated presentation through the encoded end. |
| Fallback | 0–17 | [0.000, 0.720) | Pale startup viewport with narrow left fragment; product card and required text absent. |
| Fallback | 18–64 | [0.720, 2.600) | Dark card, two center dashes, readable “Loading…”; location, prayer rows, and footer text absent. |
| Fallback | 65–445 | [2.600, 17.840) | NEWYORK; center dashes; complete “Prayer times unavailable”; six readable row names with dash times; both unavailable date labels. |
| Fallback | 446–496 | [17.840, 19.880) | Complete readable populated presentation through the encoded end. |

These phases preserve every interval in which populated text was absent; they are not silently counted as readable populated frames or automatically treated as selective glyph-loss defects. Once the unavailable labels appear, NEWYORK, the header control dash, all six row names/dashes, and “Gregorian date unavailable” / “Hijri date unavailable” remain readable until the complete populated replacement. No isolated glyph loss or partial required string was observed.

The small sky status changes separately: normal frames **87–91** show “Real sky loading…”, **92–284** show “Sky preview · refining…”, and it is absent from **285**. Fallback frames **65–85**, **86–297**, and **298 onward** show the corresponding stages. Immediate boundaries **91/92**, **284/285**, **85/86**, and **297/298** were actually viewed. Removing this small status leaves all other unavailable labels readable. The loading/unavailable boundaries **18/19**, **86/87**, **17/18**, and **64/65** were likewise preserved and inspected.

## Actual populated labels and retained structure

Both arms show **NEWYORK**, center **Isha**, center time **05:00**, and the complete countdown **4h 30m left until Fajr**. The light highlighted first row is **Fajr — 05:00**. The remaining readable rows are **Sunrise — 06:00; Dhuhr — 12:00; Asr — 15:30; Maghrib — 18:00; Isha — 19:30**. The footer reads **2026-11-01 CE** and **1448-02-19**, followed by a moon-like symbol and **19**; a small symbol before the Hijri date is visible but not confidently transcribed.

The displayed target name, time, and highlighted row consistently identify Fajr at 05:00, alongside the visibly separate center label Isha. The countdown agrees textually with the supplied case's 270-minute target interval; this does not bind a page receipt to a video frame. The rounded card, header, moon/star backdrop, plotted arc, progress strip, six-row arrangement and footer remain in the same arrangement through each populated window. A hollow ring remains visible on the ascending arc and a bright outlined marker at its lower left. Pixels alone do not identify their DOM keys. No required group disappears, overlaps another group, or becomes clipped within the captured populated card.

## Coverage, integrity, and identity

Every encoded frame was decoded without temporal sampling. Deduplication used all RGB24 bytes of the **entire frame**, retaining every frame index and native PTS. All **46** contact sheets were actually viewed, with every embedded frame at its native dimensions. A second full decode reread both originals and compared **all 1,052 frames byte-for-byte** with the mapped representative PNGs. All **274** representative PNG hashes matched. Coverage verification also checks each contact-sheet cell, boundary copy, strip, crop, and nearest-neighbor enlargement against its source pixels. `observations-per-frame.csv` and `observations-per-rgb-state.json` retain classifications for every frame and exact state.

The actual-view log contains **63** assets: 46 contact sheets, 10 boundary strips, four enlarged first/last populated frames, and three supplemental full frames. The evidence set preserves **24 named boundary frames**, 24 unaltered regional crops and 24 corresponding 3× views. The regional crops were generated and mechanically checked, not all individually viewed; complete visual coverage comes from the full-state sheets and the exact equality map.

The original ZIP is **1,974,128 bytes**, SHA-256 `213c715555a8daa818a4204cdc48231a3470ef39a403cce6d6c5fb626e162ee2`. All **34 extracted original files** were independently reread and compared byte-for-byte with the ZIP members, and their digests were rechecked at sealing.

| Recording | Original bytes | Original WebM SHA-256 | Concatenated decoded RGB SHA-256 |
|---|---:|---|---|
| Normal | 367,798 | `c333633a9e125ac141d4dee16d62ec2d1240caa1c9709dd7ebe2bbee6fbd7c2d` | `21c90802146dcbc864e3d06972ba4505214ad02d00e48ca2d95f106d546d9aef` |
| Fallback | 308,867 | `2678d8b5a9e484183af3b1709489f9fe51e59f4f2f7d63bcc6eb4e7a4e856871` | `cf56e02185821c1cf4c82fa68d9a5a54a5ee3567afb033dbc9daefec034edadd` |

The artifact records Firefox **153.0**, Windows AMD64, headful, with executable digest `9571c9a49d6d4de3e4c3b14e2e4bd6521e5b879f4ab6c95143e2098cb66e6618`. This receiver read the browser identity, case inputs, loading metadata, and trace field names/types/counts; DOM state did not determine pixel classifications. Supplied source HEAD `1e3610d97b0e33c0bfaa45f528befc998b5209d5` and tree `8ae07f9737f6ec44c8abccbe2f353cb5d76ba829` were not independently publication-verified here. The historical report was consulted for method/format only; the separate new source receiver's report was not read.

## Owner, consequence, and residual

**Root and the product maintainer** receive the bounded observation: both arms visibly populate and neither has a newly observed selective-loss interval within these finite recordings. The original historical readability findings remain open. **The source/timing receiver and root** own intervention qualification: populated pixels do not demonstrate that the intended font intervention or an equivalent exposure was realized. This report does not qualify that comparison or turn a failed observation workflow into a pass.

No page/host/video origin alignment was established. Separate WebM PTS origins cannot support a cross-arm wall-clock comparison or physical first-paint claim. VP8 compression and 25 fps coverage cannot exclude events between frames, beyond the recording, or outside the viewport. The clipped browser status line supplies no timing or network anchor. No font family, defect from 21 unloaded faces, font-service suppression, or Gecko causation is inferred. No readability gate is waived.

**Native acceptance, whole-contract acceptance, and closure authority: NONE.** No repository/index/ref/controller/original/browser/network/workflow/Library mutation or replacement acquisition was performed. Writes are confined to this designated derived directory and the two requested review files.

## Evidence seal

`recovery/native02-presentation-derived/evidence-manifest.json` inventories **434 derived files**, including **406 PNGs**, with exact byte sizes and SHA-256 values. Its digest is **`76c808d94ad16a7006313da3aa8c94b9529f3b167f998b9d0218cb41d24cb907`**. The inventory excludes itself and the final report receipt to avoid circular hashes. `report-receipt.json` binds this Markdown, the machine-readable JSON, and the inventory. `original-custody.json`, `coverage-verification.json`, `viewed-evidence.json`, and `transition-boundary-frames.json` provide the complete source, coverage, actual-view, and immediate-boundary records.
