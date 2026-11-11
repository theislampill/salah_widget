# Native media review recovery — 2026-11-10

Status: **findings recovered from retained context and authenticated raw media; original final report files are not recovered**. This record is newly written after workspace expiry. Reviewer: `/root/native_preservation_review`; model: GPT-6 Astra Pro, self-report. No acceptance, release, lifecycle, or closure authority is asserted.

## What survived, and what did not

The three native ZIPs are present and freshly match the previously recorded sizes and SHA-256 digests. `native-media-archive-verification.json` records those checks. Selected original trace, case input, browser identity, producer, adjudication, presentation receipt, and video members from the diagnostic and FF20 archives were extracted into this directory's `media-extracted` subtree, without overwriting any original location. Their exact ZIP member names and freshly calculated hashes are in `native-media-extracted-members.json` (232 files).

The FF20 final assistant handoff survives literally in `ff20-final-handoff.literal.md`. Its historical links refer to the original report locations and do not establish that the linked files survived. The current file is 4,600 bytes, SHA-256 `8d8dd97b6746e45f81fe85e9b8252159b3b24668971ab9966aae66ad292ca032`. Its exact old report hashes are historical identity references, not hashes of recovered report files.

The diagnostic files restored from the checkpoint are only a PARTIAL skeleton: 585-byte Markdown and 471-byte JSON. Exact copies are under `diagnostic-partial-skeleton`. The completed diagnostic report pair and the completed FF20 report pair are absent. No final report has been regenerated and presented as the original. The original report generators and all original derivative-manifest provenance are not claimed recovered.

| Lost completed report | Historical bytes | Historical SHA-256; not a recovered-file claim |
|---|---:|---|
| FF20 Markdown | 67,647 | `42d9c27ad57df02f80fc3117f87f5f1c3b8a4d141aadb42bb38b9a8990ede669` |
| FF20 JSON | 811,952 | `aa2bb70a6d2aa02221f09e9615f43365a8ec3a25591df387253e5a4417892c8f` |
| Three-case diagnostic Markdown | 21,906 | `d21c7953f76a948614cdf03d199b48edeb915fd61da9035d08b6ac1b22beb239` |
| Three-case diagnostic JSON | 288,903 | `810403715b3c13dfa1d680c665881b10338401c2796e28277c8ecf03ad8f3ab2` |

## Newly written recovery records

`ff20-findings.context-recovered.json` recovers the previous observations for all 20 Firefox videos. It retains the 11 early partial-text intervals (26 recorded frames), the nine healthy positive target onsets, the fold unavailable display, five intended mutant observations, and the failed reordered acquisition plus its four unqualified companions. Its current raw trace recount is 91 completed-render records (90 from complete exports plus one selected record from the failed acquisition) and 50 error-output records. An individual visible mutant result is not promoted to a qualified counterexample when its healthy control acquisition failed.

`diagnostic-findings.context-recovered.json` recovers the previous three diagnostic case observations: ordinary24 first positive frame 190 at 7.60 seconds; recovery24 frame 168 at 6.72 seconds; spring24 frame 106 at 4.24 seconds. It retains the recovery partial-text interval at frames 86–89 (3.44–3.56 seconds) and spring interval at 86–87 (3.44–3.48 seconds). Its fresh source recount is 17 completed renders and 10 error outputs. These three cases do not receive the five earlier original-run partial-text cells.

Both JSONs distinguish prior visual interpretation from fresh raw-file rereads. Both are explicitly marked `notOriginalReportBytes: true`. They contain exact raw video/trace/input/browser hashes, media frame counts and PTS, selected source-render anchors, capture ordinal mismatches, and newly regenerated frame hashes. No fresh manual image interpretation was performed as part of this recovery step.

The bounded recovery regenerated 109 selected FF20 full-card frames and 19 diagnostic full-card frames from the authenticated videos. Of the 109 FF20 PNGs, 22 have hashes that survived in literal old tool output: all 22 reproduce those bytes exactly. The other 87 FF20 frames and all 19 diagnostic frames are new derivatives of authenticated original video. They are not claimed byte-identical to lost old PNGs. These distinctions are recorded per frame. `recover-native-media-records.py` is the new recovery script, not the lost original report generator; `native-media-regeneration-receipt.json` records the new outputs and tool versions.

## Scope preserved by recovery

The previously inspected native video is 25 fps (40 ms recorded cadence), 370×570 viewport containing the 325×530 card. First recorded visible state is a bounded media observation. A page-clock-to-video-PTS bridge was not recovered or invented, and unmatched still/capture render ordinals remain unmatched. All-render traces support semantic ordering within their own page clock; they are not substituted for pixels. Recorder resolution is not treated as a new product requirement.

The FF20 source recovery preserves the unchanged-clock late-response observations for four healthy recovery cases and the nonrecovering remove-dirty mutant. It preserves the seven healthy early partial-text cells and four mutant early partial-text cells. The partial frames are observations of missing text during loading or pre-release unavailable phases, not inferred failures of the later healthy endpoint. Their cause remains unassigned. Expected unavailable status, civil-date footer labels, intentionally faded past rows, and coincident equal-time arc markers remain distinct from a contract violation. No new contrast threshold or full-date format rule is imposed.

The prior FF20 review did **not** receive the three Firefox A01/7.12.a same-input healthy-versus-wall-countdown arc pairs. It inspected individual native arcs and parsed individual source coordinates, but did not compare paired retained SVG bytes/geometry plus paired card/arc pixels or bind original-run dst-ordinary24 to FF20 wall-ordinary-control. That comparison is a separately authorized new review after this inventory, not an old recovered conclusion. The prior Chromium three-pair review does not close that Firefox gap. The additional A06 seconds-only obligation is also outside these 20 cases.

The four earlier completed preservation and prayer-presentation report files were found and remain unchanged. Their actual current hashes are recorded as external retained anchors in the inventory. They were not re-reviewed here. Other reviewers' conclusion files were not read for this recovery.

## Boundary and authority

This subagent experienced a real context compaction during recovery. It read the host-supplied implementaudit continuity rules and used only the read-only `--current-controller` lookup. The parent then supplied fresh delegated continuity: controller `r0007-successor-restored-20261110`, receipt `refs/implementaudit/continuity-receipts/r0007-successor-restored-20261110/G0002@242f6198c16d4cc9ec4483585779e5261c24aed5`, reported verified with `--require-current-continuity`. The parent explicitly retained controller and lifecycle ownership and confirmed this lane's frontier as recovery inventory followed by the three existing-artifact Firefox A01 comparisons. This report records that parent-provided capsule without claiming independent controller verification or authority.

All recovery writes are within `recovery/restored-agent-records`. No browser, native workflow, source, index, ref, original artifact, or external state was changed. The inventory covers only files written by this media-recovery lane; sibling reviewers' files in the shared directory are excluded. It is a finite snapshot and will not silently expand to include the later A01 comparison.
