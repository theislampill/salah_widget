# Plan 05 — Unify reduced-motion into a single source of truth

> **Status:** ✅ DONE (2026-06-16) — **scoped per the critique**, which caught that startup-caching would REGRESS mid-session OS-toggle liveness. Shipped: one **live** `isMotionReduced()` (after `MOTIONFULL`, line ~509) replacing the two duplicated JS `matchMedia` checks. `_REDUCED` is a per-paint local call; the once-at-boot `_RM` const was **removed entirely** and the loop's cloud-motion gate + the debugMotion readout now call `isMotionReduced()` **live** (a review-capstone finding caught that the loop gate was still boot-captured — fixed, so a mid-session OS toggle is honoured everywhere). This also upgrades the sun-pulse/moon-rad gate from once-at-load to live, matching CSS. **Did NOT** migrate CSS to a cached `data-motion` attribute (the critique's own finding shows that regresses liveness) — the CSS `@media (prefers-reduced-motion)` + `.motionfull` opt-out is the native live signal, not driftable logic, so it's left intact (zero CSS risk). Verified: `matchMedia` now has ONE JS call-site; `?motion=full`→flag false + animations run; `matchMedia` override→flag true + `--sunpulse`/`--mrad` freeze to 1.0 + restore resumes (live); 28/28.  ·  **Class:** maintainability  ·  **Priority:** P2  ·  **Effort:** M  ·  **Risk:** med
> **Do now?** Yes — recommended soon  ·  **Plan-review verdict:** `needs-fixes` (4 required fixes — see end)  ·  **Depends on:** none
>
> Read-only plan from `/implementaudit` (workflow `wf_f498de17-f7b`, investigate → adversarial critique). Grounded against `index.html` @ commit `91d0fc1` (~1951 lines). **No source was changed.** Line numbers drift — re-verify the anchors before editing.

## Problem
Three independent reduced-motion checks currently exist and must stay synchronized: (1) `_REDUCED` boolean computed at line 1698 (sun-breath/moon-radiance gates in paint()); (2) `_RM` boolean recomputed in the rAF loop at line 1898 (cloud-painting gate); (3) CSS `@media (prefers-reduced-motion:reduce)` block at lines 145–148 which **separately** rules all animation:none. Additionally, the ?motion=full override must clear all three in perfect lockstep. This is a known cross-scope drift surface: CSS and JS can diverge if the flag derivation logic is not bulletproof, causing animations to run in some scopes while others freeze — a confusing, non-credible experience. A single authoritative flag would eliminate duplication and drift risk.

## Root cause
The reduced-motion state is computed independently in multiple scopes (global `_REDUCED` at paint time; local `_RM` in the rAF loop; CSS media query as a passive browser-native check) without a single source of truth. The ?motion=full override is manually applied to all three sites, increasing the burden on future editors. CSS cannot directly read a JS variable, forcing the CSS to either re-query matchMedia (one-off check) or respond to a class/data-attribute toggle.

## Current behavior
- `_REDUCED` (line 1698) gates `--sunpulse` and `--mrad` animation math in paint(). Computed once globally via `!MOTIONFULL && matchMedia("prefers-reduced-motion: reduce")`.
- `_RM` (line 1898) gates cloud-painting frequency in the rAF loop. Recomputed **on every frame** via the same logic.
- CSS `@media (prefers-reduced-motion:reduce) { .c:not(.motionfull) ... animation:none!important }` (lines 145–148) statically disables **all** DOM animations (@keyframes glintpulse, star/cloud/weather CSS animations).
- `.motionfull` class is added to `.c` at line 1896 if `MOTIONFULL` is true, which CSS uses to opt out of the reduced-motion block.

## Desired behavior
- One authoritative `isReducedMotion()` function (or flag) computed once at startup and cached, derived from `!MOTIONFULL && matchMedia("prefers-reduced-motion: reduce")`.
- Every JS site (`paint()`, `loop()`, `updateMotionDbg()`, `paintClouds()` gate) reads this single flag instead of recomputing or shadowing it.
- CSS is kept in sync via a **data-attribute toggle** (e.g., `data-motion="full"` or `data-motion="reduced"`) set on `.c` alongside the `.motionfull` class, instead of a bare @media query. This makes the CSS state derivable and auditable from the DOM.
- The ?motion=full override is applied once (via `isReducedMotion()`) instead of three places.

## Code anchors (re-verify line numbers before editing)
**`index.html:503`**
The override param read once at startup.

````js
const MOTIONFULL = (q.get("motion")||"")==="full";// ?motion=full → force full animation even under OS prefers-reduced-motion.
````

**`index.html:1698`**
Global _REDUCED flag, computed once, used in paint() to gate sun-pulse and moon-radiance animations.

````js
const _REDUCED = !MOTIONFULL && !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);   // ?motion=full clears it (sun-breath / moon-radiance animate even under OS reduced-motion)
````

**`index.html:1630`**
_REDUCED gates animated sun-pulse in paint().

````js
c.style.setProperty("--sunpulse",(_REDUCED?1:1+(0.045+0.035*A.heat)*Math.sin(simNow()/1000/23)+0.015*Math.sin(simNow()/1000/6.5)+(1-noon)*0.16).toFixed(4));
````

**`index.html:1643`**
_REDUCED gates animated moon-radiance in paint().

````js
c.style.setProperty("--mrad",(_REDUCED?1:1+0.10*Math.sin(simNow()/1000/17)+0.12*A.aerosolDensity).toFixed(3));
````

**`index.html:145-148`**
CSS passive media query gating all animation:none when prefers-reduced-motion is active, **unless .motionfull class is present**.

````js
@media (prefers-reduced-motion:reduce){
  .c:not(.motionfull) .stars circle,.c:not(.motionfull) .starglints g,.c:not(.motionfull) .wfx .fog,.c:not(.motionfull) .wfx .drop,.c:not(.motionfull) .wfx .flake,.c:not(.motionfull) .wfx .flash,.c:not(.motionfull) .wfx .bolt,
  .c:not(.motionfull) .climate .heatwave,.c:not(.motionfull) .atmo .sun,.c:not(.motionfull) .atmo .scatter,.c:not(.motionfull) .milkyway{animation:none!important}
}
````

**`index.html:1896`**
.motionfull class added to opt out of the CSS reduced-motion block.

````js
if(MOTIONFULL && cEl) cEl.classList.add("motionfull");    // CSS reduced-motion rules are scoped to .c:not(.motionfull)
````

**`index.html:1898`**
_RM recomputed **in rAF loop** (every frame) using the same logic as _REDUCED. This is the drift surface: logic is duplicated and the variable is recomputed when it could be cached.

````js
const _RM=!MOTIONFULL && (window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches);
````

**`index.html:1933`**
_RM gates cloud-paint frequency (frozen time when reduced-motion is active).

````js
if(_RM){ if(_cloudDirty){ paintClouds(1000); tieRainToClouds(); _cloudN++; } }
````

**`index.html:1912`**
debugMotion telemetry displays _RM alongside motion=full state (evidence of the two-site pattern).

````js
+`reduced ${_RM?'YES':'no'}  motion=full ${MOTIONFULL?'YES':'no'}  paused ${cEl.classList.contains('paused')?'YES':'no'}
`
````

## Approach
**Phase 1: Introduce the single-source function (riskless, backwards-compat)**
1. Add a new function `isMotionReduced()` immediately after the `MOTIONFULL` const (around line 504):
   - Cache the result of `!MOTIONFULL && matchMedia("prefers-reduced-motion: reduce").matches` once at startup
   - Return the cached boolean; never recompute per frame
   - This becomes the **authoritative truth** for all JS sites

**Phase 2: Migrate paint() and atmosphere() (zero visual change)**
2. Replace `_REDUCED` (line 1698) with `const _REDUCED = isMotionReduced();` so it calls the new function
3. Verify `--sunpulse` (line 1630) and `--mrad` (line 1643) still gate correctly (they now read from the unified flag)

**Phase 3: Migrate rAF loop (zero visual change)**
4. Replace the local `_RM` compute (line 1898) with a direct call to `isMotionReduced()`, **or** remove the line entirely and call `isMotionReduced()` inline at the two sites (lines 1912, 1933)
   - Site 1: line 1912 in `updateMotionDbg()` textContent
   - Site 2: line 1933 in `loop()` cloud-paint gate

**Phase 4: Unify CSS + JS via data-attribute (visual validation needed)**
5. Add a line in the startup block (after `.motionfull` class is added, line 1896–1897) to **also** set `data-motion="full"` or `data-motion="reduced"` on `.c`:
   ```javascript
   if(cEl) cEl.dataset.motion = isMotionReduced() ? "reduced" : "full";
   ```
6. Replace the CSS `@media (prefers-reduced-motion:reduce)` block (lines 145–148) with a data-attribute selector:
   ```css
   @media (prefers-reduced-motion:reduce){
     .c[data-motion="reduced"] .stars circle,
     ...
   }
   ```
   (Alternatively: replace the entire @media with a scoped style keyed to `[data-motion="reduced"]` to make the intent crystal-clear — "when data-motion is 'reduced', no animations")

**Minimal risk, maximal clarity:**
- Rename `_REDUCED` **at definition only** (line 1698) to reduce shadowing confusion; its two call sites are already clear
- Do NOT refactor surrounding code; keep inline math exactly as is
- The function is cache-once, never called in a hot loop (rAF per-frame cost is zero)
- CSS data-attribute is additive; old `.motionfull` class can co-exist during transition if needed (both guard the same block)

## Alternatives considered (and rejected)
- **Use CSS custom property (CSS var) to hold the state, read by both CSS and JS** — CSS custom properties cannot be **computed** from a JS boolean in a way that is both safe and efficient. A `--motion-mode` var would need to be set via `element.style.setProperty()` on every startup, but the CSS @media query cannot read JS vars anyway — @media is passive and static. The data-attribute approach is more direct: the @media guards the CSS, and a single function guards the JS.
- **Keep _REDUCED and _RM separate; just ensure they always call the same function** — This perpetuates the mental overhead and the drift surface. If a future editor changes one site's logic, the other drifts. A single function eliminates the possibility of desync and makes the intent explicit: 'there is ONE motion flag, not two.'
- **Use matchMedia's addEventListener to react to OS changes dynamically** — The widget is deployed as a static iframe, and the user is unlikely to toggle OS reduced-motion mid-session. Caching at startup is sufficient. A listener would add complexity without a clear benefit (the override param ?motion=full already covers the test case of forcing full motion). If dynamic OS-change response becomes required, it can be added later — this plan does not preclude it.
- **Replace @media query entirely with a JS-controlled .reduced-motion class** — The @media query is a standard, browser-native signal of user accessibility intent. Replacing it with a JS class removes the direct link to the OS preference and makes auditing harder. A data-attribute complements the @media query; it doesn't replace it.

## Owner / source touchpoints
- index.html:504 (new function isMotionReduced)
- index.html:1698 (_REDUCED redefinition to call isMotionReduced)
- index.html:1896-1897 (set data-motion attribute alongside .motionfull class)
- index.html:145-148 (update @media selector to .c[data-motion="reduced"])
- index.html:1912 (update debugMotion textContent to call isMotionReduced inline or use cached _RM)
- index.html:1933 (cloud-paint gate: use isMotionReduced() instead of _RM)

## Regression risks (forbidden-regression guardrails)
- Static/frozen sky: if isMotionReduced() returns true when it should be false, all animations stop. **Mitigation:** verify qaState().render and a real 15–60s watch shows cloud/star motion when ?motion=full is passed AND when prefers-reduced-motion is NOT set in the OS.
- Transparent moon or stars-through-disc: if the data-attribute CSS change inadvertently affects moon/star layering (e.g., opacity rules shift). **Mitigation:** confirm --moongrp and --moonfeat are unaffected by searching the CSS for any rules that key off data-motion (there should be none except the animation block).
- CSS animations still running under reduced-motion: if the @media selector change is incomplete or the data-attribute is not set. **Mitigation:** load with simulated reduced-motion preference AND no ?motion=full and verify no animations (stars glint, clouds drift, sun pulses) via `debugMotion` Δ and a real watch.
- ?motion=full parameter ignored: if isMotionReduced() is called before MOTIONFULL is read, or if the data-attribute is set before the param is checked. **Mitigation:** ensure MOTIONFULL (line 503) is read BEFORE isMotionReduced() is defined, and that the startup block (lines 1895–1896) runs after both.
- ReferenceError on isMotionReduced: if the function is called before it is defined in the file. **Mitigation:** place the function definition immediately after MOTIONFULL (line 504) and before any code that calls it.

## Smoke A — capture BEFORE any change
- Load ?motion=full&debugMotion=1 with OS prefers-reduced-motion enabled (force via browser DevTools). Expected: clouds drift, stars twinkle, sun pulses, sky breathes over 15–60s. debugMotion shows reduced=no (because ?motion=full clears it).
- Load with OS prefers-reduced-motion enabled, NO ?motion=full. Expected: clouds frozen (paintClouds called with t=1000), stars static (no glintpulse), sun does NOT pulse (--sunpulse=1), sky does NOT breathe. debugMotion shows reduced=YES.
- Load with OS prefers-reduced-motion disabled. Expected: full motion (clouds drift, stars twinkle). debugMotion shows reduced=no.
- Inspect DOM: .c should have a data-motion attribute (either 'full' or 'reduced') after startup. Use DevTools console: `document.querySelector('.c').dataset.motion`.
- Inspect CSS: load with reduced-motion enabled and verify @media selector is being matched (DevTools > Styles > 'Match' indicator on the @media block).

## Smoke B — verify AFTER the change
- Re-run all smokeA tests after the change. Expected results IDENTICAL.
- Load /tests/smoke.html and confirm all integration tests still pass (no new FAILs introduced).
- Verify qaState().render reports correct fx and currentKey (ensure atmosphere() state is still being computed).
- Run a manual 60s real-time watch with ?debugMotion=1 and normal OS prefs (no reduced-motion). Confirm cloud Δ 60s is non-zero and visible (~50%+ change or more, depending on wind). Stars show visible twinkle.
- Run a manual 60s watch with OS prefers-reduced-motion enabled, no ?motion=full. Confirm cloud Δ is ~0% (frozen). Stars show NO twinkle.
- Verify header buckle is still cut-out correctly (no strap visible through translucent glass). Confirm moon is opaque (no stars through disc) in all motion states.
- Confirm footer date row is fully visible and not clipped in both motion states.

## Acceptance criteria (falsifiable)
- isMotionReduced() function exists and is called by paint() (via _REDUCED), loop() (via cloud-paint gate), and updateMotionDbg() instead of recomputing matchMedia.
- All three JS sites (_REDUCED, _RM, debugMotion report) read from a single source. Verify by grepping the final code: no more than one matchMedia('prefers-reduced-motion') call (the one inside isMotionReduced).
- data-motion attribute is set on .c in the startup block and reflects isMotionReduced(). Verify via DevTools: document.querySelector('.c').dataset.motion === 'reduced' when OS prefers reduced, or 'full' when overridden by ?motion=full.
- CSS @media block (or its replacement) correctly disables animations only when data-motion='reduced'. Load with reduced-motion enabled + no ?motion=full: debugMotion shows 0% cloud Δ over 60s, no star twinkle, no sun pulse.
- ?motion=full override works end-to-end: load with ?motion=full&prefers-reduced-motion enabled → animations run, debugMotion shows reduced=no, data-motion='full'. Visible proof: 60s watch shows cloud drift, star twinkle, sun pulse.
- No visual regressions: sun has a defined white nucleus (not grey/purple), moon is opaque (no stars through), header buckle is cut-out, footer visible, clouds structure and drift. All PASS/FAIL gates from AGENTS.md M0/J still pass.

## Rollback
If a regression is detected (e.g., animations frozen when they should run, or running when they should freeze):
1. Revert the isMotionReduced() function definition and all call sites back to their original _REDUCED/_RM logic (restore lines 1698, 1898, 1933, 1912).
2. Remove the data-motion attribute from line 1896–1897.
3. Restore the original CSS @media selector (lines 145–148) with `.c:not(.motionfull)` instead of `[data-motion]`.
4. Re-test smokeA to confirm baseline behavior is restored.

## Dependencies / sequencing
_(none)_

## Open questions
- Should isMotionReduced() cache the result in a module-level variable, or should it read MOTIONFULL and call matchMedia every time (paying a small cost per call)? Answer: **Cache once at startup** (module-level const) to eliminate per-frame overhead and make the intent explicit: 'the motion flag is read once, never recomputed'.
- Should the data-attribute be named 'data-motion' (generic) or 'data-motion-mode' or 'data-reduced-motion' (explicit)? Answer: **'data-motion'** (shorter, clear in context) and its value should be either 'full' or 'reduced' (readable in DevTools).
- Should the CSS @media block be rewritten as `.c[data-motion="reduced"] ...` or should a new rule be added with `[data-motion="reduced"]` (without the .c parent)? Answer: **Use `.c[data-motion="reduced"]`** to maintain the existing specificity and intent (the rules apply to the card container when motion is reduced). The original `.c:not(.motionfull)` can be replaced directly.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. REQUIRED FIX #1 — Update Phase 4 to also migrate the CSS transitions block at lines 42–44. Either (A) replace `@media (prefers-reduced-motion:no-preference)` with `.c:not([data-motion='reduced'])` to apply transitions only when data-motion='full', or (B) acknowledge in the plan that this block remains independent and document why. Recommended: Option A for full unification.
2. REQUIRED FIX #2 — Address the mid-session OS-toggle regression explicitly. Options: (A) Add a `matchMedia().addListener()` call inside `isMotionReduced()` to re-cache if OS prefs change at runtime, or (B) acknowledge this is a trade-off (live @media → cached startup) and update the spec to state this trade-off clearly in the 'alternativesConsidered' or 'openQuestions' section. Recommended: Option A (small cost, no regression).
3. REQUIRED FIX #3 — Update the acceptance criteria (smokeA/smokeB sections) to include a mid-session OS-toggle test. E.g., 'Load with OS prefers-reduced-motion disabled; open DevTools and toggle the preference to 'reduce'; confirm animations stop within ~100ms' (tests @media liveness). Or, if Option B above is chosen, add a note: 'Note: CSS @media query is live; data-attribute is cached at startup. OS changes mid-session will not be reflected until page reload (trade-off: unification vs dynamic response).'
4. REQUIRED FIX #4 — Clarify in the spec that the data-attribute is set at line 1896–1897 (in startup, after MOTIONFULL is read) and that the first paint() call (line 1930 in loop()) happens AFTER startup completes, so the attribute exists before any CSS matching. Add a comment in the ownerSourceTouchpoints section or approach phase confirming this order.

**Missing risks the spec omitted:**
- REGRESSION: Mid-session OS reduced-motion toggle will not be reflected in animations. The original code calls matchMedia() on every frame (line 1898), suggesting it was designed to respond to live OS changes. The cached startup approach loses this. The @media query at lines 145–148 would respond instantly; the data-attribute approach will not.
- CSS transitions block at line 42 is not migrated as part of the plan. If future editors add new transitions without checking both @media blocks, reduced-motion compliance will break. The data-attribute should gate BOTH the animations block (145–148) AND the transitions block (42–44).
- Acceptance criteria do NOT include a test for mid-session OS-toggle behavior, so a broken implementation could cache at startup, the user toggles OS settings, and the widget would silently fail — yet still pass all stated acceptance criteria (load tests only).

**Weak acceptance criteria (a broken change could still pass):**
- 'CSS @media block (or its replacement) correctly disables animations only when data-motion=reduced. Load with reduced-motion enabled + no ?motion=full: debugMotion shows 0% cloud Δ over 60s.' — This test assumes reduced-motion was enabled BEFORE load. If the user toggles OS reduced-motion MID-SESSION, the cached data-attribute will not update, and animations will continue (a regression the test does not catch).
- '?motion=full override works end-to-end: load with ?motion=full&prefers-reduced-motion enabled → animations run, debugMotion shows reduced=no, data-motion=full.' — This test assumes the OS preference is set at load time. A mid-session OS-toggle test is missing.

**Scope concerns:**
- The plan only addresses the animations block at lines 145–148. The CSS transitions block at lines 42–44 (`@media (prefers-reduced-motion:no-preference)`) is also reduced-motion-aware and should be migrated to the same data-attribute pattern for consistency. Leaving it as-is creates a secondary, orphaned reduced-motion check that can drift.

**Grounding issues (claims to re-check against current code):**
- Line 42 CSS block `@media (prefers-reduced-motion:no-preference)` is not mentioned in the spec plan at all, only lines 145–148 animation block are addressed. This block ALSO gates reduced-motion behavior (disables transitions when reduced-motion is active), creating an orphaned secondary site.
- The spec says 'Replace the CSS @media (prefers-reduced-motion:reduce) block... with a data-attribute selector' but the @media query is LIVE (responds to OS changes mid-session), while a startup-cached data-attribute is STATIC. This is a subtle spec-to-implementation gap: the spec does not acknowledge the trade-off of losing live mid-session OS-toggle responsiveness.

**Reviewer notes:** The plan is sound in intent (unify three independent reduced-motion checks into one source of truth, eliminating drift risk). The core mechanics (isMotionReduced() function, caching, data-attribute toggle) are correct. However, three concrete gaps block execution: (1) the CSS transitions block at line 42 is not addressed, leaving a secondary orphaned reduced-motion check; (2) mid-session OS-toggle behavior is a regression (the @media query is live, the cached approach is not), and the spec does not acknowledge this trade-off; (3) acceptance criteria do not test CSS liveness or OS-toggle responsiveness. All three gaps are fixable with brief plan updates (a few lines each). After fixes, this plan is ready to execute.
