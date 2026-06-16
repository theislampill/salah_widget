# salah_widget — Plans

Deeply-reasoned, **read-only** plans for the widget's outstanding/deferred work. Produced by `/implementaudit`
in its plan-lane (no source was changed) on 2026-06-16, grounded against `index.html` @ commit `91d0fc1`
(~1951 lines). Each plan is **self-contained**: problem, root cause, current vs desired behaviour, verified code
anchors, a minimal approach, alternatives, regression guardrails, Smoke-A/Smoke-B, falsifiable acceptance
criteria, rollback — and an **adversarial plan-review** section whose required-fixes must be folded in *before*
any code is written.

> **UPDATE 2026-06-16 — all plans now IMPLEMENTED in the working tree (UNCOMMITTED).** Plans 01–07 + both
> doc-hygiene fixes are done and verified in preview; plan 08 (false-dawn) is terminally **deferred** (kept
> unbuilt by design). A user-reported **moon-spin + emoji-mismatch** bug was also fixed (the moon now renders
> upright — bright limb right=waxing/left=waning, no parallactic rotation, matching the footer emoji). See each
> plan's `Status:` line for what shipped + its proof. `tests/smoke.html` is **31/31**.
> **Nothing is committed** — a commit to `main` deploys to Pages, so that needs explicit authorization.
>
> **➡ Round 2:** post-implementation residuals are planned in [`round-2/`](round-2/README.md) — a trivial dead-code
> cleanup, test-hardening, a radar-precip research spike, and decision-gated/optional-polish items. Read-only; the
> round-1 plans below stay as the implemented record.
>
> **`main` deploys to GitHub Pages, so a commit to `main` is a deploy** — do not commit/push without being
> asked. Three scratch files (`_mag_extract.txt`, `noaa_clouds.html`, `workspaceaisalah_widget_photopills.html`)
> must never be committed.

## How these were produced

A 16-agent workflow (`wf_f498de17-f7b`): one read-only investigator per item produced a structured plan spec
grounded in the real current code, then an independent **adversarial critic** verified each spec against
`index.html` for grounding errors, missing regressions, weak acceptance criteria, and scope creep. Every plan
below therefore carries its own "Plan review" section. **All eight came back `needs-fixes`** — the specs are
sound in intent but each has concrete gaps (mostly: tolerances stated too loosely, a drifted line anchor, or an
under-specified acceptance check). Resolve a plan's required-fixes first; they are cheap and they are the
difference between "looks done" and "is done".

## The plans

| # | Plan | Class | Priority | Effort | Risk | Do now? |
|---|------|-------|----------|--------|------|---------|
| [01](01-solar-elevation-helper.md) | Shared solar-elevation helper (de-dupe `drawArc`/`sunAltAt`) | correctness/DRY | P1 | M | med | yes |
| [02](02-sun-tonemap-purity.md) | Lift corner-sun tone-map `paint()`→`atmosphere()` | architecture/SRP | P1 | M | med | yes |
| [03](03-day-rollover-robustness.md) | Day-rollover offline robustness (stop silent wrong-day) | correctness/BASE | P1 | M | med | yes |
| [04](04-overcast-leaden-deck.md) | Overcast leaden ceiling (most-flagged visual residual) | visual | P1 | M | med | yes |
| [05](05-reduced-motion-single-source.md) | Unify reduced-motion (three-site drift) | maintainability | P2 | M | med | yes |
| [06](06-moonsky-ordering-safety.md) | Make `renderMoon`→`atmosphere` (`moonSky`) ordering safe | robustness | P2 | S | low | yes |
| [07](07-moon-optics-polish.md) | Moon-halo debug key + halo/paraselenae arc-clip polish | optics | P2 | S | low | yes |
| [08](08-false-dawn-zodiacal.md) | Faithful false-dawn / zodiacal light (or buildable defer) | feature | P2 | M | med | **deferred** |

Source list (authoritative): `ARCHITECTURE.md` → *Deferred follow-ups* + *Remaining risks*; `HANDOFF.md` →
*Known residuals / candidate next work*; `OPTICS.md` → false-dawn future-work spec.

## Recommended execution order (waves)

Sequenced by regret-cost, not just priority. Do a wave, verify it, then decide the next.

- **Wave 1 — low-regret correctness & quick wins.** [03](03-day-rollover-robustness.md) (isolated, pure
  truthfulness win), [06](06-moonsky-ordering-safety.md) and [07](07-moon-optics-polish.md) (both S/low —
  zero or near-zero visual change). These touch nothing sacrosanct and are individually revertible.
- **Wave 2 — physics refactors (rigor required).** [01](01-solar-elevation-helper.md) then
  [02](02-sun-tonemap-purity.md). Both refactor the "sacrosanct" sun/arc physics. Do **only** with the
  numeric before/after discipline their plan-reviews demand (an `altDeg` grid diff and a pixel/RMSE image diff —
  *not* eyeballing). 01 first: it establishes a single solar-elevation source that 02 and 08 both want to lean on.
- **Wave 3 — visual judgment.** [04](04-overcast-leaden-deck.md). The highest-value *visible* fix and the
  hardest to "prove" — it lives or dies on screenshot panels (overcast day / overcast night moonlit-rim /
  broken→overcast transition) and on confirming clear & broken scenes are untouched. "Pixels override metrics."
- **Wave 4 — deferred feature.** [08](08-false-dawn-zodiacal.md) is `recommendNow: false` and should stay
  unbuilt until it can be made genuinely faithful. Its own plan depends on 01 (it needs the fitted declination
  available inside `atmosphere()`). Build it only if all its strict gates can hold; otherwise it remains the
  documented fail-closed non-feature it is today.
- **Alongside any motion work:** [05](05-reduced-motion-single-source.md) — fold in whenever you're already in
  the motion/loop code.

## Cross-cutting themes the critics surfaced (read before starting any wave)

1. **State a numeric tolerance, then measure it.** Plans 01 and 02 both shipped self-contradictory acceptance
   ("pixel-identical" *and* "±0.01°"). Pick one quantitative bound (e.g. ±0.1° elevation; image-diff RMSE
   < 0.5%) and verify with a tool, not an eyeball. This is the single most common gap across the set.
2. **Guard the render boundary, every time.** `atmosphere(M)` is a pure state vector; `paint(A)` is the only
   sky-DOM writer; `renderMoon()` must run before `atmosphere()` (the `moonSky` coupling). Plan 02 *is* this
   discipline; plan 03 must keep its new `_prayerStale` flag out of `atmosphere()`; plan 06 hardens the coupling
   itself. Any new state that leaks across these lines is a regression.
3. **A "shared solar state" is the latent theme.** 01 creates a single solar-elevation helper; 08 needs the
   fitted declination inside `atmosphere()`; 02 already reads `A.solarElevationDeg`. Doing 01 first turns the
   duplicated `decl`/elevation math into one source the others reuse — sequence accordingly, but resist scope-
   creeping 01 into a full "SolarState object" (its own plan rejects that as over-engineering).
4. **Re-verify every anchor.** Line numbers drift (the file grew; the critics already caught a ~1972→1884 drift
   in plan 03). Treat the quoted code as the ground truth and re-locate it before editing.
5. **Honour the invariants list.** No static sky · opaque moon (subtlety = dark ashen disc, never transparency)
   · no painted dawn band / no false-dawn slash · defined white sun nucleus, never grey/purple · optics register
   to `--sunvx/--sunvy` · no strap through the buckle · never claim motion from `qaState().clouds.hash`. Each
   plan's "Regression risks" maps its work to these.

## Execution protocol (when a plan is authorized)

Run each authorized plan through the `/implementaudit` gates:

1. **Smoke A first** — capture the plan's baseline (screenshots + `qaState()` values) *before* touching code.
2. **Patch owner/source**, minimally; preserve the static / no-build / no-dependency / single-file character.
3. **Smoke B** — re-run the plan's verification and diff against Smoke A with the agreed numeric tolerance.
4. **Verify in the preview**, not by assertion — drive the dev server, screenshot, read `qaState()`. The
   `qaState().clouds.hash` is a trap; prove motion with a real watch / `?debugMotion=1` Δ.
5. **Run `tests/smoke.html`** — it must stay green (26/26); add a new characterization smoke when a plan says so
   (03 and 05 each call for one).
6. Stop at the commit gate — **do not commit/push unless explicitly asked** (commit to `main` = deploy).

## Decision record — keep `index.html` a single file (Stage-5 split NOT done)

The readiness investigation deliberately did **not** split `index.html`. Rationale: the analysis did not show
the file is too fragile to patch in place; splitting would break the core static / no-build / no-dependency /
single-file character that makes the widget trivially deployable as a GitHub-Pages iframe. **Keep it one file.**

Revisit this decision only if a concrete trip-wire is crossed — e.g.: a change genuinely cannot be made without
editing the same function from two unrelated concerns repeatedly; the renderer needs unit tests that can't run
against the inline form; or the file becomes large enough that load-time/parse-time is measurably hurting the
embed. None of those hold today. (The related deferred micro-refactors — extracting the motion-telemetry
closures out of `boot()`, or a separate `applyCloudState()` — are individually optional and are *not* a file
split; treat them as part of whichever plan touches that code, not as standalone work.)

## Doc-hygiene quick-fixes (not full plans)

Two small, no-risk cleanups found while grounding these plans — **both DONE (2026-06-16)**:

1. ✅ **Stale, self-contradicting code comment.** The dawn comment block claiming false dawn *"IS painted … (gates
   below)"* was deleted — code/comments now consistently state false dawn is NOT rendered (only `trueDawn`, a
   qaState diagnostic, exists). (Pre-req of [plan 08](08-false-dawn-zodiacal.md).)
2. ✅ **Stale `HANDOFF.md` → *Working state*.** Refreshed: the live-motion pass is recorded as committed `91d0fc1`,
   and this 2026-06-16 plans-implementation pass is noted as the current uncommitted working-tree change.
