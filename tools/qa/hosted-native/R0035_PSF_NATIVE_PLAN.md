# R0035 paired PSF native caller plan

Root approved this bounded diagnostic on 2026-11-26 before implementation.
Base: `6d0460bfa125592afdeb08a561a5d3cfb2a0b516`. Reviewed transform source:
`c96136f2ee7085f73c8642adb58943cb03796985`. No native execution is part of
source qualification; exact full-tree independent review precedes activation.

## Admission seam

`native_trials.main` calls `check_plan` before importing Playwright. Its original
checker recognizes only `independent-reconstruction` as a same-build lab, hashes
the original lab receipt, and rejects the derived renderer. The new operational
entry therefore uses an explicit, source-pinned adapter on a private loaded
driver module. It preserves the original source and scientific predicates; it
does not claim an unchanged operational driver. The adapter admits a distinct
derived plan only after complete original/derived population proof, and calls
the original `producer_flags(..., reconstructed=True)` and
`verify_reconstructed_flags` on the actual arms. The original `assess`, clock,
trial loop, readiness, measured interval, and source files remain unchanged.

## Implementation sequence

1. Import the reviewed helper/test/plan/contract exactly; preserve existing
   registry entries. Add meaningful RED controls before new implementation.
2. Add a narrow Node file entry that calls the reviewed transform, inverses,
   and combined identity. Add Python materialization/current admission with
   full populations and genuine literal-task common/optional process custody.
3. Add a named plan adapter and route/trial custody entry. Retain original
   trial reports, summaries, qualification failures, exceptions, and cleanup.
4. Add opt-in canonical paired dispatch, runtime binding, actual current
   readmission before and after each lane, original assessment replay, strict
   namespace/actual-process precedence, and complete-pair admission.
5. Extend the capture pipeline's complete-record status gate explicitly.
   Add the reviewed helper to orchestration sparse inputs. Do not change
   campaign selection or transport/crypto behavior.
6. Run old relevant registered controls and new controls. Perform genuine
   fresh source-only common and PSF preparation in a private task under
   `/home/agent/salah-cont-acc075`, preserving all failed attempts. Freeze exact
   source/docs and provide private evidence for independent review.

## Fixed dispatch and scope

Only `r0035Psf: true`, selected R0035, Chromium, DPR 1, timing, full population,
guard off, amplitude 1, glass 0.5, margin 4. Two ordered lanes: reference then
derived. Each runs the original main/unmodified/mitigated arms, one round of
15 seconds, ordinary dark/normal clock, original five-second warmup and one-Hz
producer probe. No cost/stage collector or added per-frame host writes.
The reference and candidate use separate disposable roots; the original lab
and all core/vendor source remain intact. Only candidate stellar replay's
renderer import changes, and one derived renderer module is added.

The fixed one-pair order is a diagnostic limitation. No counts-based speed
claim, policy decision, tuning, owner decision, human acceptance, or whole
work-order completion follows. Original failure remains failure; a partial
pair cannot become observed qualification. The distinct successful diagnostic
status requires complete original admission plus current custody for both
members at aggregate intake.

## Uncalibrated ceilings

Common 900 + optional materializer 240 + planner 120 + preparation reserve 75
= 1335 within preparation 1350. Outer current readmission: 120.
Each lane: original allowance 480 + adapter/finalization reserve 60 = child
540; inner preadmission 120; post source 120 + original replay 30 = 150;
namespace/control 75; total 885. Two lanes 1770. Total enumerated ceiling
1350 + 120 + 1770 = 3240. Coordinator 3540 leaves 300; selected step 60 minutes
leaves 60 further seconds. Nested Node transforms/checks use 30 seconds inside
their parent envelopes. Shared job, acquisition, and sealing ceilings stay
unchanged. These are ceilings, not calibration or performance evidence.
