# Reconciled startup and glow handoff

**Definite planning handoff received; implementation remains active and unmerged.** The investigator explicitly authorized this stable snapshot for the DAG seal without waiting for its final PR, and the coordinator read, hashed and acknowledged it. Read the [original handoff](inputs/startup/handoff-rev1/PLANNING_HANDOFF_REV1.md), [source specification](inputs/startup/handoff-rev1/CELESTIAL_STARTUP_RLGWO.md), [frozen input receipt](inputs/startup/handoff-rev1/INPUT_RECEIPT.json), and [machine reconciliation](STARTUP_HANDOFF.json).

The original handoff SHA-256 is `05dc257e4c38a3d58e844c15a64223e4ef3cec8d2187d99a4857d6d6563ee98c`. Branch `codex/celestial-startup-repair` remains on base/HEAD `18ff14860ff41c084b1db5f396bb62aa9c22b1be` with uncommitted work and **no PR at this snapshot**. Its measured runtime is `9d6fbb32384ee58531d721e8c2ac3ff92d6be00991949a40d4fd0f90c518d3ad`; its full [runtime file inventory](inputs/startup/handoff-rev1/ordinary-native-paint-chromium/results.json) is separate from delivered main/runtime `18ff1486`/`f443cf08` and the audit evidence commit `b879573c`.

## Consume completed work; do not repeat it

The initial sky uses 921 enabled real catalogue records through magnitude4.5, independently of the full9.8MB pack. The V5-derived3,965,156-byte receiver tier evaluates current native phase with the preserved material, Earthshine and calendar operators; full terrain, catalogue and diffuse refinement remain intact. The [40-case comparison](inputs/startup/handoff-rev1/initial-qualification-final/comparison.json) records maxRGB RMS0.385564/255, p95 absolute1 and identical coverage across ten phase/sense cases, DPR1/2 and two subpixel placements. This establishes the scoped initial/final lunar comparison, not whole-scene appearance or final scientific quality. Reuse its bound consumer/reference data when unchanged; do not repeat the derivation or revive rejected low-DEM/no-shadow alternatives.

The current repair also removes critical-path waits/readbacks, makes optional font CSS asynchronous, prepares initial foreground once after geometry and uses CPU-backed readback/export buffers. These are active authored changes, not delivered fixes. The previous25-case matrix at `f2653ac6…` and later lifecycle cases at `df5cf88b…` are retained historical evidence, with affected checks requiring final-runtime rebinding.

## Exact remaining startup gates

| Timing | Chromium budget | Firefox budget | Current disposition |
|---|---:|---:|---|
| Navigation → complete scene |1000ms|1500ms|Candidate Chromium716/477/538ms for cold/reload/new-tab; final matrix pending|
| Accepted scene → complete scene |250ms|400ms|Chromium314/175/194ms: cold still fails|
| Principal-content gap |80ms|80ms|Preserve native-frame coverage and actual pixel oracle; no relaxed threshold|
| Extra first-scene versus matched baseline |250ms|400ms|Chromium reload477−217=260ms still fails|

Baseline Chromium first-Moon times are7283/6252/6247ms. The current first coherent Moon/catalogue result is materially earlier, but improvement does not erase the two failing budgets. Prior Firefox native-frame samples meet the bounds; final-runtime Firefox evidence is pending. The [baseline receipt](inputs/startup/handoff-rev1/ordinary-native-before-chromium/results.json), [candidate receipt](inputs/startup/handoff-rev1/ordinary-native-paint-chromium/results.json), and [capture-driver custody](inputs/startup/handoff-rev1/capture-driver/SOURCE_FRAME_RECEIPT.json) preserve the distinction between native source frames and throttled trace screenshots. Receipt times are upper bounds with recorded gaps. Later PNG stills must not be relabelled first-paint evidence.

Older synthetic prayer fixtures contained impossible Hijri days. They remain usable for the bound Gregorian/site celestial attribution, **not calendar readiness**. The final readiness controls use labelled valid synthetic calendar fixtures. The actual extension/new-tab parent remains unavailable; normal direct/iframe/new-document/file tests do not silently close that platform row. Original R0021 callback-cost obligations also remain open; focused startup profiling is not their substitute.

## Explicit left-glow disposition

The owner images were bound to the delivered baseline. Matched baseline/candidate [ablations and receipts](inputs/startup/l1/INPUT_RECEIPT.json) attribute the left hotspot and most broad grey lift to the empirical physical lunar atmospheric field, not the decorative calendar Moon or leftover solar overlays. The near-full physical Moon projects near x3.557/y223.536 in the declared south-facing camera; the enlarged calendar Moon is a different presentation. Raw model values are not calibrated measurements. Primary inspection included the complete-widget and lunar-field-removal controls; subtraction is diagnostic, never an accepted repair.

The named [R0022-L1 revision1](inputs/startup/l1/R0022_L1_DISPLAY_INCREMENT.md) belongs under #34 and supplies the outstanding full-scene S10 input to #33. It requires a bounded display-contract decision, correction and actual full-scene acceptance while preserving the physical fields and V5 surface. Numerical initial-Moon equivalence cannot close it. Do not globally darken the scene, delete legitimate atmosphere, alter the lunar material or move the physical field behind the calendar token.

## Ownership and next handoff

After the immutable handoff, the same investigator reported the serial final matrix active at uncommitted successor runtime `d1255df46f9845f704c5e61cde618133afbef9d7852e6742bb44a4d883792cff`. This is a separately acknowledged progress message, not a replacement source manifest or new PASS. Chromium tracing rejects `expected_display_time` as a false-green first-presentation measurement: the actual `AnimationFrame::Presentation` feedback remains later and agrees with retained receipt bounds. Strict S1, the narrow timing investigation, L1/S10 OPEN and the exclusive lease remain unchanged. The eventual exact PR/head/results supersede only their affected snapshot evidence after intake.

The startup thread retains implementation ownership and the exclusive heavy-browser/terrain lease. It will send the successor exact PR/head/runtime/results; the future executor must consume that result before assigning unresolved work and must not duplicate active implementation or completed40-case/attribution work. Its remaining scope includes the Chromium misses, affected final qualification, deterministic build/source/V1 checks and its separate Draft PR. No merge is authorized here.

This definite planning handoff satisfies the **planning seal** gate. It does not turn active work, timing failures, unavailable native-parent proof, original cost gaps or L1/S10 into PASS. The final graph represents those as distinct execution/review/delivery gates and allows unrelated ready work to proceed.
