# Plan R2-05 — Day-rollover visible stale indicator (optional subtle visual cue)

> **Status:** ✅ DONE (2026-06-16) — per your spec: a quiet **worded** "stale" chip (warm amber, uppercase, not red/alarming) by the Hijri date + a faint date-row desaturation (secondary), shown only when `_prayerStale` is true. Set from `render()` via a `data-stale="prayer"` attribute on `.c` + a leading `<span class="staletag">` in `#ah`; never read by `atmosphere()`. **No card border.** Prayer-staleness ONLY (weather staleness stays in qaState). Verified: forcing the stale state shows "STALE" + desaturation; recovery clears both; barely-there but readable; 35/35.  ·  **Class:** ux  ·  **Priority:** P2  ·  **Effort:** S  ·  **Risk:** low
> **Do now?** Deferred / decision-gated  ·  **Plan-review verdict:** `needs-fixes` (6 required fixes — see end)  ·  **Depends/notes:** see "Dependencies / notes"
>
> Read-only round-2 plan from `/implementaudit` (workflow `wf_3f9f2919-894`, investigate → adversarial critique). Grounded against the **current working tree** (`index.html` with the 2026-06-16 uncommitted pass applied; HEAD `91d0fc1`). **No source was changed.** Re-verify anchors before editing.

## Problem
When a day-rollover fetch fails offline, the widget keeps the prior day's times with `_prayerStale=true` set (qaState diagnostic only — no visible on-card signal). Users see NO visual cue that displayed prayer times may be from yesterday, violating fail-open transparency. The stale state is observable via qaState() but not visibly apparent on the card itself.

## Root cause
Plan 03 deliberately deferred UI-visible stale indicator to respect the no-UI-redesign constraint. The `_prayerStale` flag was added as pure state (line ~999) but is never read outside qaState() (~1854). Render-boundary enforcement kept it diagnostic only.

## Current behavior
When `_prayerStale === true` (offline day-rollover failed): the footer date row (`.d` at line 449) displays the cached old day's Gregorian + Hijri dates unchanged; the prayer list rows show old timings. qaState().cache.prayerStale reads true, but the card itself has NO visual distinguisher from a normal non-stale state. The user cannot tell the times are stale by looking.

## Desired behavior
Add a NON-intrusive, fail-safe visible cue shown ONLY when `_prayerStale === true`. The cue must: (1) never alarm or hide errors; (2) respect layout invariants (no reflow, footer stays visible, 325×530 fixed); (3) be subtle enough for a persistent corner widget; (4) vanish instantly when stale clears. Three minimal options graded by subtlety: OPTION A (1–2px faint warm bottom-border on `.c`, ~0.3s transition into/out); OPTION B (slight opacity/desaturation dip on footer date row `.d`, ~5% opacity reduction + faint warm tint); OPTION C (tiny "·stale" text chip right-aligned near Hijri date in `.ah`, 8px sans-serif, ~40% opacity).

## Code anchors (re-verify line numbers before editing)
**`index.html:999`**
_prayerStale is the state variable set by day-rollover branch (lines 1937-1948). This plan reads it in render() only.

````js
let _prayerStale=false, _rolloverBusy=false, _rolloverNextTry=0; const _ROLLOVER_RETRY_MS=60000;
````

**`index.html:1937-1948`**
Day-rollover branch sets _prayerStale to true when new-day fetch fails (no cache, network error). Clears to false on successful fetch or cache hit.

````js
if(c){ today=c; tomorrow=null; lastDate=ds; _prayerStale=false; ... } else { ... _prayerStale=true; ... }
````

**`index.html:1789-1810`**
render() function orchestration. Add data-stale attribute write here: document.querySelector('.c').dataset.stale = _prayerStale ? 'prayer' : '';

````js
$(".cn").textContent = M.currentKey; ... fitCn(M); applyTheme(M);
````

**`index.html:18-27`**
.c root CSS rule. Add [data-stale="prayer"] selector AFTER this block (or within .c) to style the stale cue (one of three options: border, opacity, or inline chip).

````js
.c{ --g1:#0b1430; ... border:1px solid color-mix(in srgb,var(--accent) 30%,transparent); ... }
````

**`index.html:449`**
Footer date row. OPTION B and C affect this element. OPTION A (card border) does not touch it. Verify no layout shift when option is applied.

````js
<div class="d"><span class="ce" id="ce"></span><span class="ah" id="ah"></span></div>
````

**`tests/smoke.html:78-91`**
Integration test harness. Add a new scene here to test offline day-rollover stale cue. Scene should cross midnight offline, assert prayerStale===true, verify cue visible, then recover and assert cue gone.

````js
async function scene(hash,name,fn){ const ww=await loadUntil(hash, 8000, prayerReady); ... }
````

## Approach
1. Add a data-attribute `data-stale="prayer"` to `.c` when `_prayerStale === true`, cleared when false. Attribute is set ONLY in render() (where model state is fresh + `_prayerStale` is known), NOT read by atmosphere() (render-boundary honored). 2. Choose ONE minimal CSS option (A, B, or C) and style via `[data-stale="prayer"]` selector. 3. Verify zero layout shift (use transition, no margin/padding changes). 4. Test with offline day-rollover scene (`?simTime` + DevTools offline + cross midnight) — cue appears on stale, vanishes on recovery. 5. Acceptance: cue shows/hides correctly, no reflow, no alarm visual, clear-sky + cloud scenes both readable. Maintainer chooses final look; plan recommends OPTION A (subtle, non-distracting, common pattern).

## Alternatives considered (and rejected)
- **No visible cue — stale state remains qaState() diagnostic only, user must inspect console/qa for staleness** — Fails transparent-fail UX goal. A user offline at midnight crosses into the next day with no on-card warning. Silent stale is not credible for a widget designed for 24/7 embeds. Plan 03 deferred it as 'optional' but users deserve to know.
- **Show a prominent error banner ('Prayer times out of date — reconnect to refresh') at the top of the card** — Too intrusive & changes the layout (violates fixed invariant). Error banners are for serious conditions; a transient offline stale state at 3am should degrade gracefully without alarming.
- **Flash the card background or pulse the footer with a 'stale' color (e.g., muted red tint)** — Too dramatic. Pulsing motion draws eyes unnecessarily and reads as an alert/emergency. Subtle > alarming.
- **Overlay a semi-transparent warning icon/emoji (⚠ or ⏱) over the prayer times** — Occludes content. The prayer list is the hero; anything that hides it is a regression. Also too visual/dramatic.
- **Desaturate the entire card (reduce --accent, --text opacity globally)** — Too broad and hard to reverse. Bleaches the whole sky/UI, making it look broken rather than 'stale'. Also affects non-stale elements.
- **Stale indicator via a corner chip (e.g., a small '·STALE' label in top-left or bottom-right)** — Visible but clutters the corner-sun region or competes with the prayer list. OPTION C (inline in footer) is less intrusive.

## Owner / source touchpoints
- index.html:999 — _prayerStale state variable (already present, no change needed)
- index.html:1937-1948 — day-rollover branch (already sets _prayerStale, no change needed)
- index.html:1789-1810 — render() function; ADD data-stale attribute write to .c
- index.html:18-27 — .c CSS root rule; ADD [data-stale="prayer"] selector for chosen visual option
- tests/smoke.html — ADD new integration scene to test offline day-rollover + stale cue visibility

## Regression risks (forbidden-regression guardrails)
- Setting data-stale attribute in render() could slow down frame rate if called excessively — MITIGATION: only write if stale state changes (gate on _prayerStale !== lastStaleState), not every frame. Or use a no-op re-write (modern DOM is smart about no-change rewrites).
- Styling [data-stale="prayer"] could interact with existing [data-fx] weather selectors (e.g., .c[data-fx=thunder] .arc) — MITIGATION: use orthogonal selectors (data-stale styles ONLY the card border/opacity/footer, NOT the arc or sky), test in all weather states (clear, cloud, rain, thunder).
- Transition on border/opacity could stutter if the browser's repaints are slow — MITIGATION: use hardware-accelerated properties only (opacity, border inset-color, transform). Avoid box-shadow on large elements; opacity is safe.
- Adding a visible cue could change the visual hash/screenshot diff in QA — MITIGATION: expected regression, update baseline screenshots after implementation. The smoke test will assert that non-stale scenes are visually UNCHANGED and stale scenes show the cue.
- If the cue is too visible or shows under normal (non-stale) conditions, users will get alert fatigue — MITIGATION: set data-stale ONLY when _prayerStale === true (not on every glitch); make the cue very subtle (OPTION A: 1px, OPTION B: ~3% opacity); test with Smoke B to confirm cue appears ONLY when offline+stale.

## Smoke A — capture BEFORE any change
- 1. Load widget online, simulate midnight at ~23:59 local time with ?simTime=23:59. Verify today's prayers load, cache saves. 2. Check window.qaState().cache.prayerStale === false (no stale state yet).
- 3. Inspect the card via DevTools: .c element has NO data-stale attribute (or it is empty). 4. Visually: the card is fully readable with no visible 'stale' cue (footer is normal brightness/saturation).
- 5. Advance ?simTime=00:05 (crossed midnight). Verify tomorrow's prayer data is cached (simulate Aladhan cache hit or fast response). 6. Observe: prayerDate in qaState() should advance to the new day; prayerStale should remain false. 7. Card is normal-looking (no stale cue, because new-day cache was found). Layout unchanged.
- 8. Once new-day times render: verify prayer list updates to new day, footer date updates, no visual disruption.

## Smoke B — verify AFTER the change
- 1. Load widget online. Advance to ~23:59 local time with ?simTime=23:59. Verify today's prayers load. 2. Force OFFLINE via DevTools Network tab (set to Offline mode).
- 3. Advance ?simTime=00:05 (crossed midnight). New-day fetch will fail because offline + no cache. 4. Inspect window.qaState(): cache.prayerStale === true, cache.prayerDate is STILL yesterday (not advanced), cache.rolloverPendingMs > 0.
- 5. CRITICAL: Visually inspect card screenshot: the .c element now shows the stale cue. If OPTION A (bottom-border): faint warm 1–2px border at bottom edge. If OPTION B (footer desaturation): date row .d is slightly dimmed vs prayer times. If OPTION C (inline chip): tiny '·stale' label in #ah.
- 6. Verify footer date is STILL yesterday; prayer times shown are yesterday's (no silent replay as today).
- 7. Reconnect network (unset DevTools Offline) or advance ?simTime=01:00 to trigger retry. 8. Observe: fetchTimings() succeeds, prayerStale → false, prayerDate → new day, times update. 9. CRITICAL: Stale cue DISAPPEARS instantly (transition ~0.3s). Layout does NOT reflow. Footer readable.
- 10. Compare before/after screenshots: stale scene clearly distinguished by cue; readable in cloud/rain/thunder states.

## Acceptance criteria (falsifiable)
- VISIBLE CUE APPEARS: when _prayerStale === true, card shows chosen visual cue (A/B/C) within one render tick. Verified by qaState() + screenshot.
- VISIBLE CUE DISAPPEARS: when _prayerStale === false, cue removed instantly (transition ≤0.3s).
- LAYOUT INVARIANT: No reflow; card 325×530, footer visible, prayer grid unchanged. Use transition + opacity/border-color only.
- NO SILENT REPLAY: when stale, footer date displays YESTERDAY; new date does NOT appear until fetch succeeds.
- RENDER-BOUNDARY HONORED: _prayerStale read ONLY in render() for data-stale write, and qaState() diagnostics. atmosphere() never references _prayerStale.
- READABLE IN ALL SCENES: cue does not degrade readability in clear/cloud/rain/thunder/fog/snow states. Subtle, not bright/flashy.
- STALE CLEARS ON RECOVERY: offline→stale (prayerStale=true, cue visible) → reconnect/fetch succeeds → prayerStale=false, cue vanishes, times update.
- NO REGRESSION: when prayerStale === false, card is pixel-identical to previous implementation. Cue does NOT show, no visual noise. Tested by Smoke A + baseline comparison.

## Rollback
Revert: (1) remove data-stale attribute assignment from render() (~5 lines at line 1810); (2) remove [data-stale="prayer"] CSS rule from .c styling (~15–20 lines); (3) remove/revert smoke test added to tests/smoke.html. No other state affected; _prayerStale remains as diagnostic in qaState(). Clean line-delete; no data migration.

## Dependencies / notes
- Plan 03 day-rollover robustness (DONE 2026-06-16) — this plan assumes _prayerStale exists and is correctly set in loop() day-rollover branch (lines 1937-1948). Verify before starting.

## Open questions
- DECISION: Which visual option (A: bottom-border, B: footer desaturation, C: inline chip) does the maintainer prefer? Recommend OPTION A (1–2px faint warm bottom-border, non-distracting, common pattern).
- TIMING: Instant (0s) or smooth (0.3–0.5s) transition? Recommend 0.3s (reads as intentional, not a glitch).
- SCOPE: Mandatory or optional for shipping? Plan 03 marked it 'optional' but UX goal (fail-open transparency) recommends MANDATORY.
- GATE: Show always (visible to users), or only at ?debugLayers=1 (dev-only)? Recommend VISIBLE TO USERS (it is a truthfulness signal, not a debug detail). Cue is subtle enough not to alarm.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. Clarify insertion point: Specify that data-stale write occurs AFTER line 1809 (footer date render) and BEFORE line 1815 (applyTheme call), not at 'line ~1810' (which is a comment). Add a concrete code location: 'After line 1809, add: document.querySelector(".c").dataset.stale = _prayerStale ? "prayer" : "";'
2. Commit to one visual option or parametrize the smoke test: Either (a) the plan must select one of OPTION A/B/C as the canonical implementation (recommended: OPTION A with explicit rationale), OR (b) the smoke test must be written to detect and validate whichever option is applied (with conditional assertions per option). Current plan lists three options but leaves the choice unresolved.
3. Initialize or document the performance gate: If using a lastStaleState gate, add 'let lastStaleState = false;' at module scope (~line 999, after _prayerStale). If no gate, add a comment: '// DOM is smart about no-op attribute sets; no gate needed.' and remove the MITIGATION bullet from regressionRisks.
4. Scope transition rule to @media (prefers-reduced-motion): Ensure the [data-stale="prayer"] transition rule (if applied) is inside the @media (prefers-reduced-motion: no-preference) block (lines 42–44) so motion-reduced users see instant transitions, not 0.3s eases. Add a CSS comment: '/* Respect OS reduced-motion preference */'.
5. Verify CSS approach for bottom-border (OPTION A): Test or document that adding a border-bottom via [data-stale="prayer"] does not cause reflow. Consider using box-shadow (e.g., 'box-shadow: inset 0 -1px 0 rgba(248,216,120,0.3)') instead of a second border to avoid stacking height increases. Add a note: 'Use inset box-shadow to avoid reflow, not a stacked border-bottom.'
6. Add defensive CSS comment: In the [data-stale="prayer"] rule, add '/* ONLY matches data-stale="prayer" (exact value); generic [data-stale] matches are not intended */' to prevent future developer errors.

**Missing risks the spec omitted:**
- Performance gate for no-op attribute writes: plan mentions 'MITIGATION: only write if stale state changes (gate on _prayerStale !== lastStaleState)' but does not define or initialize the lastStaleState variable. If the write happens every frame unconditionally, DOM overhead is low but not zero. Requires either explicit variable initialization or documented explanation that modern DOM handles no-ops efficiently.
- Transition rule scope: the existing @media (prefers-reduced-motion: no-preference) block (lines 42–44) applies to .c custom-prop transitions. Adding [data-stale="prayer"] transition outside this block could violate the motion-reduction contract, causing motion-reduced users to see instant snap while full-motion users see 0.3s ease — a visual inconsistency.
- CSS attribute persistence: if [data-stale="prayer"] write uses empty string ('') vs null, the attribute may not fully clear or may leave residual state. If a later developer writes generic [data-stale] selector (no value check), unintended styles could leak.
- Test parametrization ambiguity: Smoke B step 5 says 'Visually inspect card screenshot: the .c element now shows the stale cue' but does not specify which of the three options (A/B/C) is expected. If the maintainer chooses OPTION C (inline chip) but smoke test is written for OPTION A (border), the test fails incorrectly.

**Weak acceptance criteria (a broken change could still pass):**
- Acceptance criterion 'Layout invariant: No reflow; card 325×530, footer visible, prayer grid unchanged' does not validate against the actual CSS chosen. OPTION A (bottom-border) is recommended but untested; a stacked border-bottom on .c could add 1px height unless the rule uses box-shadow or modifies the existing border inset property. Plan assumes no-reflow but does not verify CSS implementation.
- Acceptance criterion 'No silent replay: when stale, footer date displays YESTERDAY; new date does NOT appear until fetch succeeds' relies on the footer render logic (lines 1801–1809) being unchanged. Plan does not verify that _prayerStale does not affect the date-rendering path (it shouldn't, but no explicit guard in render() prevents future date-logic mutations).
- Smoke A (non-stale baseline) does not explicitly test that the card is pixel-identical to the previous build without the plan applied. The acceptance criterion states 'when prayerStale === false, card is pixel-identical to previous implementation' but the smoke test only checks qaState and property values, not rendered pixel output or screenshot diff.
- The open question 'DECISION: Which visual option (A: bottom-border, B: footer desaturation, C: inline chip) does the maintainer prefer?' is left unresolved in the plan. Until the maintainer commits to one option, the CSS and smoke test cannot be finalized. Plan treats this as a design choice but does not gate implementation on a decision.

**Scope concerns:**
- No-build / single-file constraint: HONORED. Plan adds ~5 lines of JS + ~15–20 lines of CSS inline. ✓
- Minimal change: HONORED. ~25 line delta total. ✓
- Render-boundary enforcement: HONORED. data-stale is set in render() only, atmosphere() never reads _prayerStale. ✓
- Moon constraints: HONORED. renderMoon() and mfeatures transforms untouched. Moon stays upright and lit-side-matches-emoji. ✓
- Forbidden regressions: No static sky, no transparent moon, no optics detach, no motion claim, no spinning moon. All clear. ✓

**Grounding issues (claims to re-check against current code):**
- Plan cites insertion point as 'line ~1810' but line 1810 is a comment block about moonSky coupling; actual insertion should be after line 1809 (footer date render) and before line 1815 (applyTheme call). Minor documentation drift, but the intent is clear.
- CSS selector specificity not verified for OPTION A (bottom-border). Current .c has 'border: 1px solid' at line 26; adding a second 'border-bottom' via [data-stale="prayer"] may cause reflow or stacking issues. Plan assumes simple CSS addition but does not validate against existing border rules or @property cascades.

**Reviewer notes:** The plan is conceptually sound and well-grounded in the current codebase. All code references are verified to exist and match the current state (round-1 pass applied). The render-boundary constraint is honored (atmosphere() never reads _prayerStale; render() is the sole writer). The minimal-change and no-build constraints are met. Forbidden regressions (static sky, transparent moon, spinning moon, optics detach, motion claim) are all avoided. However, the plan has specification gaps that must be resolved before coding: (1) the exact insertion point is off by ~5 lines (documentation drift, not logic error), (2) no commitment to a visual option (leaves smoke test unspecifiable), (3) missing performance-gate initialization, (4) transition rule not scoped to @media (prefers-reduced-motion), and (5) CSS approach not validated against reflow. These are all LOW-risk, high-confidence fixes. Once addressed, the plan is ready for implementation.
