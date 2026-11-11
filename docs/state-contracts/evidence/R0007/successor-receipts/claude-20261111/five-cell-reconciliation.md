# R0007 — reconciliation of the five unaccepted cells of run 42953929662

Author: successor root (Claude Fable 5.2, self-report), 2026-11-11. This is a reuse argument for owner decision,
not a new observation of the five cells. **Run 42953929662 remains FAILURE** and no oracle, deadline, recipe or
adjudication rule was changed.

## 1. What failed, from the run's own artifact

Artifact 13826760980 (`sha256:5cd77bfefcc7c3ea3d9548b94f3d5ead43a5c5fd66b4fbeaafd3211e1ccd4822`), candidate
`a71d7df097db029a90518491e2ccc15c6307e13a`.

| Cell | Adjudication | Originating failure (for the two healthy cells the other false acceptance terms are downstream of it) |
|---|---|---|
| `NE07-recovery12` (healthy) | `OBSERVATION_NOT_ACCEPTED` | action 4 `release tomorrow` raised "No pending boundary tomorrow:1" |
| `NE07-wall-ordinary-control` (healthy) | `OBSERVATION_NOT_ACCEPTED` | action 3 `release capture-current` raised "No pending boundary capture-current:1" |
| `NE07-mut-remove-next-dirty` | `MUTANT_NOT_QUALIFIED` | `healthyControlsAccepted:false` (controls `recovery24`, **`recovery12`**) |
| `NE07-mut-wall-fall` | `MUTANT_NOT_QUALIFIED` | `healthyControlsAccepted:false` (controls `fall24`, **`wall-ordinary-control`**) |
| `NE07-mut-wall-spring` | `MUTANT_NOT_QUALIFIED` | `healthyControlsAccepted:false` (controls `spring24`, **`wall-ordinary-control`**) |

For the three mutants every other acceptance term in `tools/qualification/r0007_native.py` (lines 341–350) is true
in their `adjudication.json`: native setup, cleanup, capture evidence, producer exit 1, trace `FAIL` with
`expectedOracleFailure`, and the failure text contains `expectedFailureContains`, as the rule requires
(`dom/.nt/text: expected '00:31', observed '—'`; `render/leftMin: expected 270, observed 210`;
`render/leftMin: expected 150, observed 210`). The mutants themselves were rejected as intended on the candidate;
they lack only the credit of a healthy control. **So the five cells reduce to the two healthy-cell failures.**

## 2. Why the two healthy cells failed — demonstrated proximate cause

From each cell's `trace.json` (`operationTimings` are host-monotonic; `rawOnFailure.events` / `timerLog` are page
`realElapsedMs`):

**`NE07-wall-ordinary-control`.** The fixture held the current-day body at page 2038 ms (`body-hold`). The product
armed its unchanged 10 000 ms deadline (timer 4, started 2038). The harness then issued one `capture.bounds` call
that returned after **10.484 s** (host 2563 → 13047 ms after navigation start). During that call the product's
timer 4 fired at page 12096 ms and the body was aborted (`body-abort` 12096), as designed. The recipe's 250 ms
sleep followed and `release` ran at host 13297 ms — after the boundary no longer existed.

**`NE07-recovery12`.** The fixture held the next-day body at page 886 ms; the product's 10 000 ms deadline (timer 5,
started 842) fired at page 10899 ms (`body-abort`), and the product retried at 11897 ms (occurrence 2 held). On the
host, `capture.bounds` took 2.078 s and the font-settlement `wait.async` took **8.500 s** although the page
evaluated that predicate in 133 ms (raw `performance.now()` 12817 → 12950 ms, about +522 ms against fixture
`realElapsedMs`). The page-side wait state was created at least 5.69 s after the host issued the call, while page
timers before it ran on schedule — the page event loop was free and the call had not yet arrived, so product
main-thread blocking is excluded for this cell and the delay is upstream (driver, protocol, browser parent process
or runner). For `wall-ordinary-control` there is no page-side receipt for the bounding-box call; page timers ran
during it and the deadline fired 58 ms late, which excludes a continuous product block but not shorter ones. `release tomorrow` (occurrence 1) ran at host
15625 ms — after occurrence 1 had been aborted by the deadline.

In both cells the failing step is therefore the harness releasing a held response later than the product's own
10 s request deadline, because a single harness call resided 8.5–10.5 s on the runner. That is **demonstrated**
for these two cells. The product behaved as specified (deadline, abort, retry).

What is **not** demonstrated: why harness calls reside that long on the hosted runner (driver, recorder, scheduler
or page main-thread contention), and whether the font correction changes how often it happens. Known facts bearing
on that: (a) the same class is recorded on the pre-correction source `1e3610d9` in run 42925667946, where a
requested 250 ms sleep resided 8.141 s / 5.812 s and both original releases failed after the unchanged 10 s
deadline (that run used the font-ingress diagnostic profile on `fall24` / `font-fallback-fall24`); (b) in run 42834337271 (pre-correction, no per-call timing) `NE07-reordered24` failed with the same
"No pending boundary tomorrow:1" error and its four dependent mutants were `MUTANT_NOT_QUALIFIED`; (c) in the
present run multi-second residences occur in most cells, including accepted ones (`fall24` `capture.bounds` 9.12 s,
`spring24` `wait` 8.66 s, `ordinary24` navigation 8.59 s) — a cell fails only when the residence between hold and
release exceeds 10 s. Pre-correction per-call timings exist for only a handful of Firefox cells (two in run 42925667946, two in 42920631317, three in the F1/F2 runs), so no frequency comparison
is claimed.

## 3. Exact source identities for evidence reuse

| Item | Identity |
|---|---|
| Earlier accepted observation of all five cells | run 42834337271, head `0f2e8e5f6f5317ba88d01f47b49987962dc8d22e`: `recovery12`, `wall-ordinary-control` = `SOURCE_ASSERTIONS_MET_PIXELS_PENDING`; `mut-remove-next-dirty`, `mut-wall-fall`, `mut-wall-spring` = `INTENDED_MUTANT_ASSERTION_REJECTED_PIXELS_PENDING` |
| Product bytes `0f2e8e5f` → `1e3610d9` | `src/native/index.html`, `index.html`, `offline.html` identical (`git diff --quiet`) |
| Product bytes `1e3610d9` → candidate | `src/native/index.html` differs in 46 changed lines (+40/−6), all the font gate (stylesheet link id, the two custom properties, the `html.webfonts body` rule, the two date-dialog `font-family` declarations, the `requestWebfonts` block and comments); generated `index.html` / `offline.html` are the builder's output of that source (independently reproduced byte for byte) |
| Recipe definitions of the five cells | `tests/rlgwo/R0007-next-event-recipes.json` case objects for all five are identical at `0f2e8e5f` and the candidate (actions, expected values, `expectedFailureContains`, controls) |
| Fixture | `tests/rlgwo/prayer-browser-fixture.cjs` differs only by an added diagnostic `font-fallback` variant not used by these cells |
| Functional predicates | selector, admission, adoption, model and render code are byte-identical; the gate adds one call to the already-existing `cnFontChanged()` (fit-cache invalidation + dirty frame), the same call the old source made from its font events |

## 4. Fresh functional observations on the candidate that bear on the same obligations

- Recovery path (7.07, A05, ES07-06): `recovery24`, `dst-recovery24` and `dst-recovery12` met their source
  assertions on the candidate — the UTC recovery path in 24 h format and the 12 h format on the DST recovery path.
  Only the UTC + 12 h combination (`recovery12`) is not freshly observed.
- Wall-arithmetic discrimination (7.10, A01, A06): `mut-wall-spring` and `mut-wall-fall` produced the exact intended
  rejections (observed 210 against 150 / 270) on the candidate; `spring24` and `fall24` (their other controls) met
  their assertions. Only the ordinary-210 control cell is not freshly observed.
- `mut-remove-next-dirty` produced the exact intended rejection; its other control `recovery24` met its assertions.

## 5. Proposed disposition

The five obligations are discharged for this candidate by **reuse** of run 42834337271 across a product delta that
is confined to typography gating, supported by the fresh same-path observations in §4 — not by run 42953929662,
which stays FAILURE with these five cells unaccepted in it. No further acquisition is proposed: a rerun could only add a fresh observation; it is not needed to settle a
functional question, because the delta does not touch the functional predicates.

Residuals kept open at their actual scope: the cause of multi-second harness-call residence on the hosted runner;
no fresh candidate observation of `recovery12` and `wall-ordinary-control`; one unexplained historical Chromium
row-only frame; on-demand non-latin font subsets can still blank briefly; Firefox-only hosted observation of the
correction.

## 6. Independent review of this argument

A separate reviewer (model self-report Claude Opus 5.5; no authoring role) re-derived the numbers from a fresh
download of the artifact (byte-identical, digest confirmed), the original run-42834337271 archive and Git, and
returned **SUFFICIENT_WITH_CONDITIONS**. Its corrections are applied above. Its conditions, which stand:

1. `recovery12` (UTC + 12 h) and `wall-ordinary-control` (the ordinary-day control of the wall-countdown mutants)
   are discharged **only** by run 42834337271 plus code identity — there is no fresh candidate observation of them.
2. First-frame / pixel review stays pending in the adjudications of both runs (`PARTIAL_INDEPENDENT_PIXELS_REQUIRED`);
   this reuse argument does not discharge it. For run 42834337271 the predecessor's independent pixel review
   (`ff20p`) is the existing record; for run 42953929662 only the row-text readability receipt exists.

Its analysis of the one behavioural touchpoint: the gate's only runtime effect is a single `cnFontChanged()` after
its loads resolve, the same call the old source made from font events. The recipes' pre-release wait requires font
settlement and `dirty===false`, so that frame is always consumed before release and cannot wake a frozen page
afterwards. The candidate run shows it: in `mut-remove-next-dirty` the font renders came at 2140 / 2197 ms and
nothing rendered after release (4513 ms) — the dash was still showing at 10160 ms, so the mutant was not masked;
in `recovery24` the single post-release render (6773 ms) is the adoption frame, 41 ms after release.

It marked UNKNOWN: the root cause of the runner stalls; host↔page clock alignment beyond ordering bounds; it did
not rerun the builder (the earlier exact-candidate review did).
