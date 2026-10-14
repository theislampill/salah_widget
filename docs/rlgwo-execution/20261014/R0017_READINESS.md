# R0017 Moon readiness countermeasure

The original smoke instrument could not execute its required Moon callbacks in
Firefox within the existing eight-second scene deadline. The owner amendment
permits the adjacent startup repair recorded here. The original failed attempts
and independent BLOCKED assessment remain evidence; later results do not rewrite
them.

## Cause and change

Both original terrain row workers computed the entire camera and first lighting
pass, although the pool retained only half of each result. Fresh cold and warm
documents remained late after successful source/asset delivery. Removing this
duplicate work alone was insufficient for the waxing and waning scenes.

The authored `moon-engine.mjs` now computes only validated owned rows, with the
row bounds included in both camera and lighting cache identities. A change of
ownership resets the camera allocation before reuse. The existing kernel remains
unchanged. Per-worker display filtering and quality projections are omitted;
those discarded intermediates are still computed globally after joining.

The native pool uses four disjoint row owners. Every reply must have the correct
scene, profile and row identity and valid complete field shapes. The pool joins
material and diagnostics as well as illumination/coverage, then performs the
existing full-frame filtering and adaptive quality decisions. Missing, foreign,
malformed or cancelled work cannot authorize publication.

This is a memory-for-latency tradeoff: measured summed WASM linear memory at the
540-pixel receiver raster is 653,262,848 bytes, versus 326,631,424 bytes for the
previous two-worker pool. These figures exclude asset copies, JavaScript buffers
and other browser memory. Timings are scoped to the recorded Windows browsers
and machine; they are not universal device-performance guarantees. Low-memory
devices have not been qualified. R0021 / [issue 33](https://github.com/theislampill/salah_widget/issues/33)
separately owns substantially faster first-complete Moon/sky presentation; this
eight-second R0017 smoke result does not satisfy R0021.

## Preservation and evidence

Kernel/WASM, DEM/colour assets, V5 mapping/profile, phase and geometry, native
surface adoption/currentness, opacity, detail composition, prayer/weather/config,
and the smoke page/fixture remain byte-identical to the reviewed base. Generated
host, worker, offline entry and build manifest come from `tools/build_native.py`.
Frozen V1 is separately verified.

The original 30 named callbacks, 141 expected assertions and 4/8/3-second limits
remain intact. Real-WASM comparisons cover both orientations, near-new through
full phases, two/four owners, odd raster boundaries, sparse refinement, calendar
output and counters. Recovery tests interrupt actual camera/lighting work; fourth
reply, cancellation and partial-boot controls retain fail-closed ownership.

Chromium and Firefox each complete all 30 callbacks and 141 assertions under
both native motion preferences. The slowest accepted Moon stage is 7,768 ms.
An earlier attempt on the same final runtime remains INCOMPLETE at 29/30 because
the live-synthetic installation case missed readiness. Its cause is unproven;
the later passing runs do not establish a reliability guarantee or rewrite it.

The [acceptance ledger](R0017_ACCEPTANCE.json), [raw evidence](https://github.com/theislampill/salah_widget/blob/2f9a5b82cd83e3ae7b994f110b58efc92bbb46a6/docs/rlgwo-execution/20261014/R0017_EVIDENCE.zip),
[file manifest](R0017_EVIDENCE_MANIFEST.json) and
[independent review](R0017_REVIEW.json) bind runtime/browser identities, native
results, original pixels and retained failures. Controlled fixed-clock smoke is
not normal-live M0 or general appearance qualification. Public Pages execution
and the issue certificate remain separate post-merge requirements; this document
grants no merge or closure authority.

## Evidence placement and deployment size

The unchanged ZIP is on the non-deploying `codex/r0017-evidence-20261014` branch,
pinned to commit `2f9a5b82cd83e3ae7b994f110b58efc92bbb46a6`. Its 326 members and
SHA-256 `3544f2349137495e2b7b49beb38a46de52a480ffa6c5472a88f24284708c7d8c`
are unchanged. Download it using the linked raw URL in the manifest; raw receipt
paths in the ledger and review resolve from the ZIP root, with the ledger's
explicit `evidence/` base applied to original contrary-evidence entries. Source
paths resolve in the containing source commit. Historical exception log labels
use the ledger's explicit resolver to unchanged repository receipts and compressed
logs at the evidence commit. The original local review and
ledger remain historical records; their pending commit steps are reconciled by
the later exact-head readback linked in PR62.

The ZIP is absent from this source/deployment tree, not merely excluded by an
assumed Pages rule. Its earlier Git object remains in history to preserve custody.
The [packaging and Pages-size receipt](R0017_PACKAGING.json) distinguishes exact
tracked-tree bytes, measured existing Pages payload, and the candidate estimate.
No candidate deployment or size-limit certification is claimed. Pages still uses
`main` at `/`; the evidence branch must never be merged into it.

The owner-approved implementation is `7fb3dd33b5efb2a8d8a187bd5e2a5901b900fce6`.
The packaging receipt above is historical for that head. The delivery-only
successor uses the supported Jekyll exclusion for R000C raw native evidence,
whose immutable resolver is documented in [R000C](R000C/README.md#native-evidence).
The bounded PR62 Pages-payload check uses the active Pages builder and measures
the entire generated output against 1,000,000,000 bytes while comparing protected
consumers. Its compact receipt is retained with the final delivery evidence.
