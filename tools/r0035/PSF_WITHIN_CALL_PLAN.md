# R0035 within-call Gaussian experiment implementation plan

> Execute inline in the receiving R0035 worktree. Root owns the independent
> exact-tree review and all later publication or native work. No descendants.

**Goal:** Test reuse of horizontal Gaussian integrals within one PSF splat while
preserving the unchanged reference's complete Float64 result and failure behavior.

**Architecture:** A source-only transform admits the exact reference renderer and
stellar replay by SHA-256, derives a separately named renderer, and redirects only
the disposable replay import. It leaves vendor, generated core, original lab,
workflow, campaign, spectral calculations and publication policy untouched.

**Tech stack:** Node ES modules, Node's test runner and VM module loader, the
unchanged Python lab hook recipe. No dependency or native browser acquisition.

**Spec:** Continuation handoff dated 2026-11-26, section 6D; the first recommendation
of the retained run 45747687166 offline cost review; issue 102 and its owner
decisions. The owner has authorized this experiment and opted out of routine
design/plan confirmation. These are source tests, not native or human acceptance.

## Global constraints

- Keep reference and original product/lab paths byte-identical.
- Preserve validations and their order, clipping, subpixel coordinates, the
  unchanged `erf`, `wx*wy`, `Math.max`, `rgb[c]*w`, row/pixel/channel order, and each
  separate channel/component call. No cross-call state or cache key.
- Compute each horizontal weight lazily during the first visited row; reuse it
  only on later rows of that invocation. The first row keeps its evaluation order.
- Compare entire Float64 buffers, including nonzero initial values and repeated
  overlapping splats. Encoded pixel equality alone is insufficient.
- Preserve original producer, initial-status and cadence failures. Original
  native timing, captures, human evaluation and owner choices remain outstanding.
- Exception coverage concerns ordinary numeric inputs, the original validation
  failures and tested access faults with stable math intrinsics. It does not
  prove equivalence under altered intrinsics, concurrent mutation or allocation
  exhaustion, nor exhaust all binary64 inputs.

## Review focus

1. Clipped/empty supports, tiny/broad sigma and subpixel boundaries must retain
   all writes and rounding, including zero channels and signed zero.
2. Invalid arguments and buffer/RGB access faults must preserve error type,
   message, access order and the completed buffer prefix in the tested domain.
3. Calls of different widths, locations, sigma, channel and part must never
   inherit horizontal values from an earlier call.
4. The independent original scene recipe must use its digest-verified catalogue
   and diffuse asset, original foreground/encoder and original lab host hooks.
5. A changed reference, transformed-byte mutation or incorrect inverse must not
   receive an admitted experiment identity.

## Task 1: Guarded reversible derivative and raw parity

Files: `tools/r0035/psf_within_call.mjs` and
`tools/r0035/psf_within_call_controls.cjs`.

Interface: `deriveRenderer(bytes)`, `restoreRenderer(bytes)`,
`deriveStellarReplay(bytes)` and `restoreStellarReplay(bytes)` return Buffers.
`experimentIdentity(reference, candidate, stellar, redirected)` validates every
pair and returns only source identities and the source-only scope.

- [x] Write and retain RED controls before adding the transform.
- [x] Implement exact digest/seam guards and inverse verification.
- [x] Verify raw full-buffer equality over explicit boundary cases and a fixed
  bounded numeric population; retain thrown outcomes and access-fault prefixes.
- [x] Demonstrate fewer actual `Math.exp` evaluations with equivalent returned
  values in a source-only counting realm; do not infer CPU or native speedup.
- [x] Require arithmetic, subpixel, clipping, Float32 and shared-state mutants to
  fail exact-output controls; require source-identity mutations to be rejected.

## Task 2: Original-source populations and downstream behavior

File: extend `tools/r0035/psf_within_call_controls.cjs`.

Interface: independent VM graphs load the untouched original scene recipe;
the candidate graph redirects only stellar replay to the derived renderer.
Both graphs use the pinned original `patch_refined` hook transformation.

- [x] Bind actual catalogue, manifest, diffuse bytes and all imported source.
- [x] Compare every patch and raster Float64 value for the original ten
  day/twilight/near-Fajr/moonlit/dark preview/refined source scenes.
- [x] Compare nominal bytes, variable indices, source/center counts, complete
  replay outputs, overlays and motion gating under bounded nonuniform
  cloud/calendar/glass foregrounds and repeated overlaps.
- [x] Retain original membership/flux/nominal failure behavior where exercised;
  state plainly that reconstructed source scenes are not captured native inputs.

## Task 3: Registry, contract, verification and freeze

Files: `tests/regression-population.json`,
`docs/state-contracts/R0035-psf-within-call.md`, this plan.

- [x] Register the new command with the complete source/data input closure.
- [x] Run the new registered command, original affected R0035 source controls
  and the complete registry census using the unchanged runner.
- [x] Verify the diff contains only the new experiment, controls/docs and one
  registry addition; retain original records and every failed setup/control.
- [x] Record exact bounded findings and remaining native/human limits in the
  private report, then commit source/docs only for root's independent review.

## Execution rulings

The source experiment has no operational materializer or hosted selector. Test
VMs derive the candidate in memory, so a passing source result cannot activate
or replace a native recipe. Root's supplied worktree and private report paths
supersede generic skill workspace locations. No private evidence enters Git.

## Author source verification

The unchanged registered runner returned **PASS** with no setup errors and
`sourceUnchanged: true`: runner contract 46 cases, original stage source controls
12, original cost source controls 10, and new within-call controls 13. The
original replay/scope suites also passed all 12 cases. These populations are
reported separately; repeated runs are not added into a unique grand total.
The complete registry census ran as part of the registered invocation.

The private record retains the initial RED and both corrected harness failures.
The independent exact-tree review and all native/human qualification remain
outstanding. These author source results do not change the original failures.
