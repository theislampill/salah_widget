# R003F B0 corrected serving and UI admission

This is a **corrected harness**, with an explicit transformation receipt. It is
not the unchanged published B0 recipe, a product change, a candidate promotion,
or a native acceptance result. The implementation below has no browser-launch
authority. Hosted execution remains with the coordinator after independent review.

## Defect and custody

The original `tools/qa/r003f_capture.cjs` serves `.css` as
`application/octet-stream`. A control starts that actual server and reads
`/real-sky/native-sky.css` over loopback HTTP: status 200, 1,854 bytes, SHA-256
`298a11d0d91a801de2e8f63b7e4997ff33d7a7423ebd0e4c8a0bbd5710f68f31`.
The corrected server returns `text/css` for exactly the same bytes. No stylesheet
or other product file is patched or copied by this materializer.

The earlier B0 run retains its raw `MEASURED` report. Its separate, derived
**harness-faithfulness disposition is INCOMPLETE**; the private observations
cannot establish a valid full-widget baseline. Capture filenames, content
hashes, measurements and images remain in the private evidence package. This
correction does not rewrite those records. The existing `prayerLoaded`
assertion does not establish that the prayer UI is present inside the card.
An actual execution of the original `capture()` function with a displaced-UI
boundary double reproduces that admission gap.

## Source admission and output

Run the materializer with explicit source and fresh output paths:

```sh
node ORCHESTRATION/tools/qa/hosted-native/r003f_materialize.cjs \
  --source IMMUTABLE_RESEARCH \
  --out NEW_DISPOSABLE_CORRECTED_SOURCE
```

The source reference is commit
`156f95d0e3ec692919dc33a1c68f76ea3ef91353`. Admission checks the exact per-file
SHA-256 values below, so the same unchanged files from immutable research
`55d1b3edb66d2c35679707120b01ee1d3455e4a3` also qualify. This check makes no
claim that the caller's checkout HEAD was inspected. Symlinked input members,
wrong hashes, a reused output directory, an output inside the source, and missing
or ambiguous patch anchors are refused. All source bytes are admitted before
the output directory is created.

| Required source member | Original SHA-256 | Disposition |
|---|---|---|
| `tools/qa/r003f_owner_baseline.cjs` | `a270d91d05b16d0238ac9058eec09561f0739ec0d599a636fef585f6979bede0` | Copy with guarded UI observation, admission, and harness identity additions |
| `tools/qa/r003f_capture.cjs` | `af84f6c9de2534658ddc327618622a6b33803a141c026927a44890805317b982` | Copy with guarded CSS MIME and read-only UI observation additions |
| `tools/qa/r003f_p1.cjs` | `eaabdfa55a1043a701ef08643b7a304cce6bad217073f2d30f3c51ecc599d380` | Copy unchanged |
| `tools/qa/r003f_grid.cjs` | `532de10b100f3388b1fa677a4e61c1afdb221628c23c50b1229a2530ef1845a3` | Copy unchanged |
| `tools/qa/r0033_isolation.cjs` | `2aef5788ea21cf33a201348e2e4ab901c6d0a8d7c16251859411768cb4b8132a` | Copy unchanged |
| `tools/qa/v1_net_guard.cjs` | `2b00cb52a72384862156f7ba771bc5daedcb420780b05b84cf8366962b4affab` | Copy unchanged |
| `real-sky/native-sky.css` | `298a11d0d91a801de2e8f63b7e4997ff33d7a7423ebd0e4c8a0bbd5710f68f31` | Validate only; do not copy or change |

The new `tools/qa/hosted-native/r003f_ui.cjs` is copied into the corrected source
directory. `materialization.json` records the materializer digest, all source and
output digests and byte counts, and the preimage/postimage hashes and exact count
of each source-anchor replacement. Its paths are relative resource names. It
records `PREPARED`, `nativeExecution: NOT_RUN`, and `matrixMotion: NOT_INCLUDED`.

The frozen offline materialization produced these corrected identities:

| Resource | SHA-256 |
|---|---|
| Materializer source | `2fc95820151e08ff416ce10890a801045a960cd49c65eff499a1cf0ee4473fbc` |
| Corrected `tools/qa/r003f_owner_baseline.cjs` | `2f67e80d35e5ff953489e0a1ebb817746f96f3bc5e541943c8b8178d6a599531` |
| Corrected `tools/qa/r003f_capture.cjs` | `fcee26c4ce9d1304c11fe5a44620b2528deabcc165f1e2d6e7e9d2e92f7db280` |
| New `tools/qa/hosted-native/r003f_ui.cjs` | `ccce93bcbe1bcd4834789e03ead8a2a104710e4955e05d57cc846ab4a341c82a` |
| `materialization.json` | `fab2e2ad49a14eee2ba715fb75365fa4b0abfa48a1d8b60247343ad29b1021e5` |

The four remaining copied helper digests equal their original table entries.
The materializer returns exit 0 and the same receipt as JSON on stdout. Refusal
returns exit 2 with an `INCOMPLETE` error on stderr. The fresh output and files
are private (0700 directories and 0600 files, subject to a more restrictive umask).

## Admission added to each B0 capture

The copied `facts()` function records `state.nativeUi` immediately before the
existing screenshot call. A second read-only observation after the screenshot
records `captures[tag].nativeUiAfter`. These are two browser evaluation task
boundaries; they do not prove presented-frame latency, contrast, or visual
quality. The PNG remains necessary for visual judgment.

Both receipts use `R003F/native-ui/1`. They retain card-relative rectangles,
text, prayer identities, relevant computed styles, and ancestor visibility
styles. Admission requires:

- Exactly one 325×530 card and one header, prayer container, and footer, with
  positive rectangles wholly inside the card.
- The populated location and weather text, the buckle, and both populated date
  values inside their respective header/footer rectangles.
- Exactly six distinct rows in the order Fajr, Sunrise, Dhuhr, Asr, Maghrib,
  Isha. Each row has its matching label and a populated displayed time, and
  each row and its text rectangles remain inside the prayer container/card.
- Visible computed styles, positive opacity through the ancestor chain,
  positive text font size, nontransparent text color, the native grid/flex
  layouts, and an ordered, nonoverlapping header/prayer/footer stack.
- The real refined and preview canvases retain absolute positioning from the
  stylesheet. A hidden preview after refined composition remains valid.

The collector reads DOM, geometry, and computed style only. It calls no product
API and changes no DOM, storage, clock, weather, or Moon state. A collector error
or failed post-capture evaluation is retained as an incomplete receipt. Host
admission recomputes the predicates from the recorded observation, so a forged
`status: PASS` alone is insufficient.

The captured PNG and both UI receipts are retained **before** admission. Every
original B0 physics assertion runs unchanged and in the original order, before
the new UI assertions. In particular, an original physical-light Andon retains
its original precedence even when the UI is incomplete or its second read
fails. The original shared `checkState()` and `checkPair()` implementations are
byte-identical; no numerical tolerance, original oracle, physical gate, clock,
fixture, waiting period, or network assertion is relaxed.

The native report preserves protocol `R003F/P1/B0-owner/2` and adds a `harness`
object naming `R003F/corrected-harness/1`, with the actual materialization,
driver, capture-helper, and UI-helper digests. Original exits remain:

| Exit | Raw report meaning |
|---|---|
| 0 | `MEASURED`, after original measurements and added UI admission |
| 2 | `INCOMPLETE`, including absent or displaced UI |
| 3 | `ISOLATION FAIL`, preserving original isolation precedence |
| 4 | `FAIL (Andon)` for the original calendar-light failure |

## Coordinator invocation after review

The materialized directory is disposable source, outside the private capture
tree. Copy its `materialization.json` into the private capture's preparation
receipts before execution. The supplied runtime remains the separately admitted,
unchanged generated main tree, including `tests/r0002-ordinary.json` and all of
its real assets. The coordinator must preserve its existing main source/build
identity, fresh network namespace, non-root browser isolation controls, final
network ledger, and encrypted private retention. This helper does not replace
or establish those controls, and does not itself consume the hosted isolation
receipt.

Only the coordinator may run the reviewed native driver:

```sh
node CORRECTED_SOURCE/tools/qa/r003f_owner_baseline.cjs \
  --root ADMITTED_GENERATED_MAIN \
  --out NEW_PRIVATE_CAPTURE \
  --engine chromium \
  --dpr 1 \
  --playwright EXPLICIT_PLAYWRIGHT_MODULE_DIRECTORY \
  --pngjs EXPLICIT_PNGJS_MODULE_DIRECTORY
```

The unchanged driver also accepts `--engine firefox|webkit`, `--dpr 2`, and an
explicit `--executable` path. Start with one corrected Chromium/DPR1 B0 capture
set and inspect its four PNGs, UI receipts, original measurements, and final
isolation verdict before choosing a follow-up. Each refined wait still allows
150 seconds plus 2.5 seconds of settling; an outer 900-second budget can bound
the four-capture set without shortening those original waits. A timeout remains
incomplete evidence. No full matrix or owner decision follows from this offline
preparation.

The wider matrix and motion drivers are deliberately not copied or qualified
here. They have additional capture and rejected-observation paths whose UI
receipt retention needs separate controls before extending this B0 correction.
The matrix's `header-toggle` diagnostic changes and removes a no-op CSS custom
property; its separate hidden-frame diagnostic hides only the Moon layers.
Neither fact is evidence that the whole matrix has been qualified here. The B0
correction supplies no matrix, full-motion, cross-engine, or DPR2 result.

## Offline controls and registry integration

Run the focused actual-function controls without a browser:

```sh
node --test --test-reporter=tap \
  tools/qa/hosted-native/r003f_harness_controls.cjs
```

There are **30 controls**. They exercise real loopback HTTP and actual source
materialization, compile both corrected helpers, execute the serialized browser
observer against frozen DOM boundary doubles, and execute the actual original
and corrected `capture()` functions with explicit PNG/page boundary doubles.
They demonstrate the old admission gap, both successful and rejected corrected
paths, before/after receipt and PNG retention, failed reads, source/anchor
refusals, and original physical assertion/Andon precedence. These controls are
source and orchestration evidence; their DOM/PNG doubles do not qualify native
rendering or pixels.

Central integration now registers `hosted-native-r003f-harness-controls` with
protocol `auto`, `expectedCases: 30`, the TAP argv above, and
`covers: ["tools/qa/hosted-native/r003f_harness_controls.cjs"]`. Its complete
input population is these three new files plus all seven source members in
the source table:

```text
tools/qa/hosted-native/r003f_harness_controls.cjs
tools/qa/hosted-native/r003f_materialize.cjs
tools/qa/hosted-native/r003f_ui.cjs
tools/qa/r003f_owner_baseline.cjs
tools/qa/r003f_capture.cjs
tools/qa/r003f_p1.cjs
tools/qa/r003f_grid.cjs
tools/qa/r0033_isolation.cjs
tools/qa/v1_net_guard.cjs
real-sky/native-sky.css
```

Duplicate module/exclusion classifications were removed for those now-selected
inputs; their classification does not promote a native verification level.
The old recipe's custody and the corrected recipe's distinct identity remain
explicit in the integration documentation. Fresh registered controls also cover
preparation process/byte refusal, no fallback on failed preparation, campaign
forwarding, report identity/population and UI-receipt completeness. The original
physical and isolation failure meanings are preserved. A passing source-control
selection is not an actual corrected native result.
