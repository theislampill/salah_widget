# salah_widget — Plans, Round 2 (post-implementation residuals)

Deeply-reasoned, **read-only** plans for what's outstanding **after** the 2026-06-16 implementation pass (round-1
plans 01–08 + the moon-spin/emoji fix, all applied and sitting **uncommitted** in the working tree). Produced by
`/implementaudit` (plan-lane, no source changed) on 2026-06-16, grounded against the **current** `index.html`
(HEAD `91d0fc1` + the uncommitted pass). Same format as round-1: each plan is self-contained and carries an
**adversarial plan-review** whose required-fixes must be folded in before coding.

> **Honest framing:** the widget is in good shape after round-1. This round is **incremental** — one trivial
> cleanup, test-hardening, one real feature (radar precip), and the rest are decision-gated or optional polish the
> investigators themselves marked "don't do now." Nothing here is a bug or a regression.
>
> **UPDATE 2026-06-16 — implemented per user decisions (UNCOMMITTED).** 01 (dead-code), 02 (smokes → 35/35),
> 05 (stale cue), 06 (`applyCloudState`), 07 (telemetry extract) are **DONE**; 04 (moon hemisphere) and round-1's 08
> (false-dawn) are **deferred by decision**; 03 (radar) is **researched, wiring gated on your external-source
> decision** (not wired — it needs a new third-party dependency). See each plan's `Status:` line. **Nothing is
> committed** — a commit to `main` deploys to Pages, so that needs explicit authorization.

## How these were produced

A 14-agent workflow (`wf_3f9f2919-894`): one read-only investigator per item → an independent adversarial critic.
6 of 7 came back `needs-fixes` (sound intent, gaps to fold in); **`smoke-coverage-expansion` came back `sound`.**

## The plans

| # | Plan | Class | Priority | Effort | Risk | Do now? |
|---|------|-------|----------|--------|------|---------|
| [01](01-dead-code-cleanup.md) | Remove dead `moonParallactic()` + unused `chi` (from the moon-upright fix) | cleanup | P2 | S | low | **yes** |
| [02](02-smoke-coverage-expansion.md) | Expand `tests/smoke.html` (offline rollover, continuity, motion liveness) | tests | P1 | M | low | **yes** |
| [03](03-radar-precip-source.md) | CORS-safe radar/nowcast precip → make the weather gate ground-truth | research | P1 | L | low | **yes** |
| [04](04-moon-hemisphere-orientation.md) | Moon hemisphere: upright N-only vs southern-aware (decision) | feature | P1 | S | low | decision |
| [05](05-day-rollover-ui-cue.md) | Visible stale indicator (the cue deferred from round-1 plan 03) | ux | P2 | S | low | deferred |
| [06](06-extract-applycloudstate.md) | Extract `applyCloudState()` out of `paint()` (last SRP impurity) | architecture | P2 | S | low | deferred |
| [07](07-extract-motion-telemetry.md) | Extract debugMotion telemetry out of `boot()` (SRP tangle #3) | architecture | P2 | M | med | deferred |

## Recommended execution order (waves)

- **Wave A — do-now, low-regret.** [01](01-dead-code-cleanup.md) (trivial, ~6-line deletion — do it next time you
  touch the moon code) → [02](02-smoke-coverage-expansion.md) (strengthen the safety net **first**, so the offline
  day-rollover path and cloud continuity are smoke-guarded before any further change). Then
  [03](03-radar-precip-source.md) as a **research spike** — it's the only real new feature, but `L` effort with an
  external-data dependency; treat it as "investigate + prototype behind a fail-closed gate," not a quick win.
- **Wave B — decision-gated (your call).** [04](04-moon-hemisphere-orientation.md): keep the moon upright N-only
  (simplest, moon+emoji stay consistent, never spins — recommended) **or** make it southern-aware (mirror both the
  moon's lit side *and* the emoji for `lat<0`). [05](05-day-rollover-ui-cue.md): whether to add a subtle visible
  "times may be stale" cue (today it's `qaState`-only). Both are UX preferences — pick the behaviour, then it's a
  small change.
- **Wave C — optional architecture polish.** [06](06-extract-applycloudstate.md) and
  [07](07-extract-motion-telemetry.md) close the last two SRP items from `ARCHITECTURE.md`. The investigators rated
  both `recommendNow: false` — do them only if you're already in that code; they're readability wins, not fixes,
  and they touch `paint()`/`boot()` (so verify clouds/telemetry are byte-identical after).

## Cross-cutting themes the critics surfaced

1. **Re-verify the smoke count.** It's now **31** (round-1 added moon-orientation + day-rollover + reduced-motion
   smokes). Several specs hard-coded older counts — check `tests/smoke.html` before asserting.
2. **Quantify acceptance; don't lean on vague visual checks.** Recurring critique: "moon opaque (`--moongrp~1`)"
   and "correct position" need a measured assertion (a `qaState`/computed-style value or a bounding box), not an
   eyeball — same discipline that caught the round-1 `--sunray` regression.
3. **Don't touch `paint()`/`boot()`/`renderMoon` without a before/after equivalence proof.** Plans 06/07 are pure
   refactors — hold them to byte-identical output (clouds drift identically; the debug overlay is unchanged).
4. **Never reintroduce the moon spin or the parallactic χ−q rotation.** Plans 01 and 04 both touch the moon —
   the moon must stay upright, non-spinning, lit-side-matches-emoji (smoke-guarded).

## Captured as notes (not deep plans)

- **Commit & deploy the uncommitted 2026-06-16 work — the #1 real next action.** Everything from round-1 + the moon
  fix is verified in-tree (31/31) but **uncommitted**; `main` → Pages, so it needs your explicit go-ahead. This is
  an action awaiting authorization, not a planning item.
- **Overcast final look (round-1 plan 04).** Implemented conservatively; the exact "how leaden" is your visual
  call — say the word to dial it stronger/softer. Not re-planned here.
- **`moonSky` ordering is a detector, not enforcement** (warn + `moonSkyFresh` flag, not a throw). Deliberate (a
  throw would break the direct `atmosphere(model())` calls in `qaState`/debug). Leave as-is unless a reorder
  regression actually occurs; hardening to lazy-compute is possible but low-value.
- **Doc-staleness in `ARCHITECTURE.md` "Deferred follow-ups":** the *Day-rollover robustness* and *Reduced-motion
  single source* bullets are now **done** (this session) but still listed as open — refresh them when next editing
  that doc (trivial; bundle with another edit).
- **Single-file decision still holds** — no Stage-5 split (re-affirmed in round-1's README).
