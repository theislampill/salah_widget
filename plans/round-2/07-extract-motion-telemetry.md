# Plan R2-07 — Extract debug motion-telemetry closures out of boot()

> **Status:** ✅ DONE (2026-06-16) — **pure extraction**: `_cloudAlphaNow`/`_starSampleNow`/`_motHist`/`updateMotionDbg` moved out of `boot()` to module scope; the loop's rate counters (`_rafPS`/`_cloudPS`) stay in `boot()` and are passed into `updateMotionDbg(rafPS,cloudPS,cEl)`, so the boot lifecycle / rAF scheduling / `start`/`stop`/`setVis` / visibility + IntersectionObserver behaviour are **untouched**. Verified: normal (non-debug) runtime unchanged + 35/35; `?debugMotion=1` overlay renders byte-identically (`rAF …/s cloudPaint …/s …`); `atmosphere` ok.  ·  **Class:** architecture  ·  **Priority:** P2  ·  **Effort:** M  ·  **Risk:** med
> **Do now?** Deferred / decision-gated  ·  **Plan-review verdict:** `needs-fixes` (8 required fixes — see end)  ·  **Depends/notes:** see "Dependencies / notes"
>
> Read-only round-2 plan from `/implementaudit` (workflow `wf_3f9f2919-894`, investigate → adversarial critique). Grounded against the **current working tree** (`index.html` with the 2026-06-16 uncommitted pass applied; HEAD `91d0fc1`). **No source was changed.** Re-verify anchors before editing.

## Problem
The motion-telemetry subsystem (`updateMotionDbg`, `_cloudAlphaNow`, `_starSampleNow`, and the `_motHist` state array, along with supporting accumulators `_rafN`, `_cloudN`, `_tickAcc`, `_rafPS`, `_cloudPS`) is currently implemented as inner closures/state of the `boot()` function (lines 1912–1929, 1961). This is documented as ARCHITECTURE.md SRP tangle #3: "`boot()` carries the whole motion-telemetry subsystem as inner closures. Deferred: extract to top-level `DEBUGMOTION`-gated helpers in a debug-tooling pass." The closures read loop/boot-scoped variables (`cEl`, `_lastCloud`, `_lastSec`, and indirect references to `DEBUGMOTION`/`ADVANCING`/`MOTIONFULL`/`TIMESCALE`), making them technically boot-coupled. Extraction improves testability, readability, and decouples the debug UI from the core render loop — but carries a non-trivial regression risk (editing boot() is high-touch).

## Root cause
The motion-telemetry overlay is a debug-only feature gated by `?debugMotion=1`. It emerged incrementally to prove the sky animates in real-time (DESIGN.md §Live motion & accessibility, AGENTS.md §Live-motion auditor). The functions were added inside `boot()` to access the rAF counters and the cloud canvas immediately — a pragmatic local placement that was never extracted when the feature stabilized.

## Current behavior
- `?debugMotion=1` displays an overlay (`.dbgmotion` element, lines 164 CSS) showing: rAF ticks/s, cloud-paint/s, reduced-motion status, motion=full status, paused status, timeScale/advancing, cloud Δ over 10s/60s, star Δ + twinkle-animation status, weather source, and the reason motion is reduced (if any).
- Implemented as three nested functions + one const inside `boot()`: `_cloudAlphaNow()` (line 1913) reads the cloud canvas alpha-channel sum, `_starSampleNow()` (line 1914) samples a visible twinkling star's opacity, `updateMotionDbg()` (lines 1915–1929) builds the telemetry text, plus `_motHist` (line 1912) stores 61 history samples {a,s} (cloud alpha, star opacity).
- Supporting state: `_rafN`, `_cloudN` (frame counters, reset per second), `_tickAcc`, `_rafPS`, `_cloudPS` (per-second rates), all declared line 1912.
- The `loop()` function increments `_rafN++` (line 1931), increments `_cloudN++` on cloud paints (lines 1959–1960), and calls `updateMotionDbg()` once per second if `DEBUGMOTION` (line 1961).
- **ZERO behavior change when `DEBUGMOTION` is off**: the functions are never called, and the telemetry state is inert overhead.

## Desired behavior
- Extract the motion-telemetry subsystem to **module-scope (top-level) functions** that are ONLY defined/run when `DEBUGMOTION===true` — NOT inside `boot()`.
- Pass or promote the needed state (`cEl`, rAF/cloud counters `_rafN`/`_cloudN`/`_tickAcc`/`_rafPS`/`_cloudPS`, loop-scope variables like `DEBUGMOTION`/`ADVANCING`/`MOTIONFULL`/`TIMESCALE`) as needed.
- Preserve the identical telemetry display text and history logic (no change to what `?debugMotion=1` shows).
- Preserve **byte-identical overlay behavior when `?debugMotion=1` is on**: the same fields/values, the same 61-sample history window, the same update rate (once per second).
- **Zero overhead / zero behavior change when `DEBUGMOTION` is off** (the functions must not be called, and the telemetry state must not allocate if not needed).
- No change to normal (non-debug) runtime: `?debugMotion` is never present in real production; this is a QA/developer-only feature.

## Code anchors (re-verify line numbers before editing)
**`index.html lines 504`**

````js
const DEBUGMOTION = q.get("debugMotion")==="1";   // ?debugMotion=1 → live motion telemetry overlay (rAF & cloud-paint rates, reduced-motion, paused, cloud/star Δ over 10s/60s, wx source, timeScale, reason)
````

**`index.html lines 1912–1929`**
The three closures and state live inside boot() and access outer variables (cEl, DEBUGMOTION, ADVANCING, MOTIONFULL, TIMESCALE)

````js
let _rafN=0,_cloudN=0,_tickAcc=_RAFNOW(),_rafPS=0,_cloudPS=0; const _motHist=[];
  function _cloudAlphaNow(){ try{ const cv=document.querySelector('.cloudcanvas'),x=cv.getContext('2d'),d=x.getImageData(0,0,cv.width,cv.height).data; let a=0; for(let i=3;i<d.length;i+=4)a+=d[i]; return a; }catch(e){ return 0; } }
  function _starSampleNow(){ const els=document.querySelectorAll('.stars circle'); for(const e of els){ if(e.style.display!=='none' && getComputedStyle(e).animationName==='tw') return +getComputedStyle(e).opacity; } return 0; }
  function updateMotionDbg(){...}
````

**`index.html line 1931`**

````js
_rafN++;
````

**`index.html lines 1959–1961`**

````js
if(isMotionReduced()){ if(_cloudDirty){ paintClouds(1000); tieRainToClouds(); _cloudN++; } }   // LIVE reduced-motion
    else if(rt-_lastCloud>76){ _lastCloud=rt; paintClouds(simNow()/1000); tieRainToClouds(); _cloudN++; }
    if(rt-_tickAcc>=1000){ _rafPS=Math.round(_rafN*1000/(rt-_tickAcc)); _cloudPS=Math.round(_cloudN*1000/(rt-_tickAcc)); _rafN=0;_cloudN=0;_tickAcc=rt; if(DEBUGMOTION) updateMotionDbg(); }
````

**`ARCHITECTURE.md line 74–75`**
Explicit deferred task from the readiness audit.

````js
**`boot()` carries the whole motion-telemetry subsystem** (`updateMotionDbg`/`_cloudAlphaNow`/`_starSampleNow`)
   as inner closures. *Deferred:* extract to top-level `DEBUGMOTION`-gated helpers in a debug-tooling pass.
````

## Approach
1. **Promote state to module-scope** (lines before `boot()`, after the global consts): conditionally declare `_motHist` and the counter variables only if `DEBUGMOTION` is true, to zero out the allocation overhead when the feature is off. Use an `if(DEBUGMOTION){ ... }` block or a conditional initialization pattern.

2. **Extract the three helpers to top-level functions** (before `boot()`):
   - `function _cloudAlphaNow()` — NO CHANGES, purely reads the cloud canvas; no local state captured.
   - `function _starSampleNow()` — NO CHANGES, purely reads star DOM; no local state captured.
   - `function updateMotionDbg()` — will read: module-scope state (`_motHist`, `_rafPS`, `_cloudPS`), module-scope constants (`DEBUGMOTION`, `ADVANCING`, `MOTIONFULL`, `TIMESCALE`), and **newly-passed or promoted parameters** (`cEl`, `isMotionReduced` is already a module-level function). The `.dbgmotion` element selector can stay (it's a DOM query, not a closure dependency).

3. **Refactor the counter logic inside loop()**:
   - Change `_rafN++` (line 1931) to a conditional check: `if(DEBUGMOTION) _rafN++;` (minimal cost if the flag is constant).
   - Change both `_cloudN++` increments (lines 1959, 1960) to conditional checks: `if(DEBUGMOTION) _cloudN++;`.
   - Change the per-second aggregation (line 1961) to call the extracted helper: `if(rt-_tickAcc>=1000){ if(DEBUGMOTION){ _rafPS=Math.round(_rafN*1000/(rt-_tickAcc)); _cloudPS=Math.round(_cloudN*1000/(rt-_tickAcc)); _rafN=0;_cloudN=0;_tickAcc=rt; updateMotionDbg(); } else { _tickAcc=rt; } }` to maintain `_tickAcc` for the next tick.

4. **Pass `cEl` to module scope**: currently declared inside `boot()` (line 1907). Either expose it as a module-scope `let` (initialized by `boot()` after the querySelector), or inline the `cEl.classList.contains('paused')` check into `updateMotionDbg()` by doing a fresh querySelector at display time (minor inefficiency, but safer — `cEl` is only ever read in debug mode).

5. **Verify no regression**:
   - `?debugMotion=0` or absent: all telemetry state/functions are unallocated or inert, `loop()` has zero extra cost (the `if(DEBUGMOTION)` guards are compile-time or runtime constants, not branches).
   - `?debugMotion=1`: the overlay text, history window, and update rate are byte-identical.
   - Tests: 31/31 smoke tests pass, especially the qaState contract (which should be unaffected).

6. **Alternative (if `cEl` exposure is too invasive)**: pass `cEl` as a callback or by wrapping the module-scope `updateMotionDbg()` with a bound version inside `boot()` that has closure to `cEl`. But that defeats the extraction goal — prefer the direct module-scope `cEl` initialization.

## Alternatives considered (and rejected)
- **Leave as-is (no extraction).** — Violates SRP intent and increases cognitive load when maintaining boot(); deferred work compounds; the telemetry is a stable, debugger-only feature that does not need to live in the core loop. Not justified.
- **Extract to a separate JS module file (e.g. debug.js).** — Breaks the single-file/no-build constraint (DESIGN.md, HARD CONSTRAINTS). Not allowed.
- **Keep the functions inside boot() but move state declarations to module scope.** — Partial solution; still leaves the functions (closures over module scope) inside boot(), which is less clean. The full extraction is only slightly more work and achieves better separation.
- **Wrap telemetry in a class/object (MotionDebugger).** — Over-engineered for a debug-only feature that is never instantiated twice. Adds indirection without removing coupling. Prefer flat functions + state as-is.
- **Conditionally include the functions only at build time (if DEBUGMOTION constant-folds to false, dead-code-eliminate them).** — No build step in this project (HARD CONSTRAINTS); can't rely on build-time optimization. Runtime `if(DEBUGMOTION)` guards are the only option.

## Owner / source touchpoints
- ARCHITECTURE.md — tangles, deferred items, BASE/ACID/observability
- DESIGN.md — `?debugMotion=1` documented as an accessibility/live-motion QA tool (lines 217–223)
- index.html — `boot()` function (1873–1972), `loop()` inner scope (1930–1963)
- tests/smoke.html — `?debugMotion=1` is NOT tested (it is not a behavioral regression check; it is QA UI). Extraction must preserve the display output.
- AGENTS.md — live-motion auditor role; `?debugMotion=1` is the tool the auditor uses

## Regression risks (forbidden-regression guardrails)
- **Edits to boot() are always high-risk**: `boot()` orchestrates the entire initialization and rAF loop lifecycle, with tight coupling to closure variables, the prayer-timer cache, moon rendering, star projection, and the visibility-change handler. Any misstep in refactoring the counter bumps or the `_tickAcc` reset can break the rAF clock calibration.
- **Closure-to-module-scope variable bindings**: if the extraction passes parameters incorrectly (e.g. using an old/stale value of `cEl` instead of the current element, or forgetting that `isMotionReduced()` is called at display time, not at counter-bump time), the telemetry text will be wrong.
- **The `_tickAcc` reset timing**: line 1961 resets `_tickAcc` inside the `if(rt-_tickAcc>=1000)` block. If the new code skips the reset when `!DEBUGMOTION`, the next tick will see a wrong `rt-_tickAcc` and the rate calculation will diverge. Must ensure `_tickAcc` is always reset.
- **Conditional allocation**: if module-scope state is only allocated when `DEBUGMOTION===true`, and the URL flag changes at runtime (it does not — `DEBUGMOTION` is set once at parse time), the code is safe. But if a future change allows runtime toggling, the extraction will need a reset/allocation/deallocation callback.
- **Counter increment cost**: replacing `_rafN++` with `if(DEBUGMOTION) _rafN++` adds a branch to the hot path (once per rAF frame, ~60 fps). The branch is a module-scope const, so it should be predicted perfectly by the CPU and cost near-zero; but any misplaced check (e.g. in the cloud-paint condition) will measurably slow down the non-debug case.
- **Telemetry text format drift**: the `updateMotionDbg()` display must remain byte-identical. Any accidental edit to the formatting (e.g. adding a space, changing the field order, or using a different precision) will break the `?debugMotion=1` UI and fail verification.
- **DOM query cost in loop**: each call to `updateMotionDbg()` does a `document.querySelector('.dbgmotion')` and `document.querySelectorAll('.stars circle')`. These are cached-efficient on modern browsers, but if the extraction moves them into a hotter path or calls them more often, performance could degrade. The current design (once per second) is safe.

## Smoke A — capture BEFORE any change
- Open `?debugMotion=1` without `?debugMotion` in the URL — verify NO overlay appears and NO telemetry state is allocated (browser DevTools: inspect memory, confirm no `_motHist` array visible in global scope).
- Normal widget load (no debug flags) — verify rAF rate and cloud rate are normal (~60 fps and ~13 fps respectively); no stutter, no extra branches in the hot path.
- Verify all 31/31 smoke tests pass (tests/smoke.html); especially the qaState contract (weather truthfulness, moon orientation, continuity) which must be unaffected.

## Smoke B — verify AFTER the change
- Open `?lat=24.47&lon=39.61&label=Madinah&method=4&debugMotion=1` (with simulated weather, clear sky, full moon at night for star sampling).
- Verify the overlay text displays correctly: rAF rate ≈60–59 /s (or less if reduced-motion), cloud rate ≈13 /s, star Δ changes over 60s (stars twinkling), cloud Δ shows non-zero 10s/60s deltas (clouds drifting), weather source shows 'sim' (not 'current'), timeScale shows 1 (or the configured value).
- Take a screenshot of the overlay and compare character-by-character against the baseline: same field names, same number precision (cloud Δ %.1f, star Δ .3f), same line breaks.
- Toggle the browser's `prefers-reduced-motion` (Settings > Accessibility or via DevTools) mid-display: verify the overlay 'reduced YES' / 'reduced no' switches and the text updates within 1 second (next tick).
- Fast-forward with `?timeScale=10`: verify 'timeScale 10' and 'advancing yes' show, cloud Δ 10s/60s should be larger (faster drift), and the overlay updates smoothly.

## Acceptance criteria (falsifiable)
- ✓ The three telemetry functions (`_cloudAlphaNow`, `_starSampleNow`, `updateMotionDbg`) are defined at module scope (before `boot()`, not inside it).
- ✓ The telemetry state (`_motHist`, `_rafN`, `_cloudN`, `_tickAcc`, `_rafPS`, `_cloudPS`) is declared at module scope and allocated only if `DEBUGMOTION === true` (wrapped in an `if(DEBUGMOTION){ }` block or lazy-initialized).
- ✓ The `loop()` function calls the module-scope `updateMotionDbg()` directly when `DEBUGMOTION && rt-_tickAcc>=1000`, not through a closure.
- ✓ All counter increments (`_rafN++`, `_cloudN++`) are guarded by `if(DEBUGMOTION)` and the cost in the non-debug case is zero or negligible (single branch prediction miss).
- ✓ The `_tickAcc` reset happens on every second (or every loop iteration with checked condition) — NEVER skipped, so the per-second rate calculation stays correct.
- ✓ The overlay text output (`.dbgmotion` textContent) is byte-identical to the pre-extraction version: same field names, same line breaks, same number formatting (%.1f, .3f).
- ✓ When `?debugMotion=1`, the overlay appears, updates every ~1 second, shows cloud Δ 10s/60s and star Δ correctly over 60 seconds, and the history window holds 61 samples.
- ✓ When `?debugMotion` is absent or `0`, the overlay does not appear, the telemetry state is not allocated, and `loop()` runs with zero extra overhead.
- ✓ All 31/31 smoke tests (tests/smoke.html) pass: weather gate, moon, dawn, continuity, moon orientation.
- ✓ No regression in normal (non-debug) runtime: rAF clock, cloud repaint rate (~13 fps), reduced-motion pausing, day-rollover, visibility-change handler all work as before.
- ✓ The extraction changes ONLY the structure (moving functions/state from inside `boot()` to module scope); the behavior (call graph, display output, side effects) is identical.

## Rollback
Revert the commit and restore the three functions and state declarations inside `boot()` (lines 1912–1929). No data migration needed (motion telemetry is not persisted). The `loop()` edits (counter guards, `updateMotionDbg()` call) must also be reverted to the original inline calls. A 1-line rollback to the prior commit is safe.

## Dependencies / notes
- No external dependencies — this is a refactoring within index.html. The prior round-1 work (day-rollover robustness, moon optics, sun tone-map, reduced-motion unification, corner-sun lift) is already in place and must not be modified.

## Open questions
- **Should `cEl` (the `.c` container) be exposed as a module-scope variable?** Currently it is declared inside `boot()` at line 1907 only for use in the lifecycle handlers and in the `if(MOTIONFULL)` check (line 1908). The extracted `updateMotionDbg()` reads `cEl.classList.contains('paused')` and `cEl.dataset.fx` at display time. Options: (A) expose `cEl` as a top-level `let` initialized by `boot()` after the querySelector, or (B) have `updateMotionDbg()` do a fresh `document.querySelector('.c')` each display (minor inefficiency, ~1 ms per second, negligible). Recommend (A) for consistency with the rest of the code (all major DOM queries are cached), but (B) is safer if `cEl` access after `boot()` is discouraged.
- **Is conditional state allocation necessary, or should the state always exist (but be unused when `DEBUGMOTION` is false)?** The telemetry state is ~1 KB (a 61-entry array + a few numbers + the function objects). Always allocating is simpler and has zero cost when the functions are never called (dead code eliminated by engines). Conditional allocation is cleaner (zero footprint when off) but requires careful initialization. Recommend conditional allocation (wrap in `if(DEBUGMOTION){ }`) because the project values lightness and the savings are measurable (even if micro). If implementation becomes fragile, fall back to unconditional allocation.
- **Should the per-second rate calculation continue to run when `DEBUGMOTION` is false?** Currently, `_tickAcc` tracks elapsed time and resets every ~1000 ms. When `DEBUGMOTION` is off, this is wasted work. Recommendation: reset `_tickAcc` only if `DEBUGMOTION`, otherwise keep the prior timestamp for next-tick comparison. But **ensure the `rt-_tickAcc>=1000` condition is always checked**, so stale/fast time does not break future telemetry ticks. Safest approach: always run the aggregation block, but only compute/display rates if `DEBUGMOTION`.
- **Is there any value in extracting this now vs deferring further?** ARCHITECTURE.md marks it as 'deferred'; the motion telemetry is stable and tested. Value: readability (3–4 nested functions inside a 100-line boot() are harder to scan) + testability (can call the helpers standalone for unit testing, though unlikely to be needed) + SRP (boot() is already doing a lot). Cost: medium-high regression risk (edits to boot() are always risky). **Judgment call:** if the next task is the file-split or a major refactor, extract it first to simplify the larger change. Otherwise, defer unless a bug surfaces in the telemetry (then extract while fixing the bug, to avoid tangles). **Recommendation: DEFER.** The value is clean-up/polish; the cost is risk. Not recommendNow.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. FIX 1: Clarify the cEl scope and initialization. EITHER (A) hoist cEl to module scope with a null guard in updateMotionDbg (e.g., 'if(!cEl) return;'), OR (B) have updateMotionDbg do a fresh querySelector('.c') each display (minor inefficiency but safer). Provide the exact code pattern in the approach, not just the concept. Update acceptance criterion to verify both options work.
2. FIX 2: Specify the exact conditional-allocation pattern in JavaScript. Write out: 'let _rafN; if(DEBUGMOTION) { _rafN=0; _cloudN=0; _tickAcc=_RAFNOW(); const _motHist=[]; }' NOT block-scoped. Explain why declaration hoisting is necessary. Update acceptance criterion to check that state is NOT in scope if DEBUGMOTION is false (use browser DevTools to verify).
3. FIX 3: Write the exact refactored loop() logic showing _tickAcc reset handling. Provide the before/after code snippet for line 1961 to show that _tickAcc is reset regardless of DEBUGMOTION. Add an assertion or smoke test that verifies the reset happens every ~1000ms even if DEBUGMOTION is off.
4. FIX 4: Add a smoke test for ?debugMotion=1 that verifies: (1) overlay appears when flag is set; (2) text contains all expected fields in the correct order; (3) overlay updates once per second; (4) 10s/60s delta values change as expected over 60 seconds. Provide the test code in tests/smoke.html.
5. FIX 5: Measure and document the actual CPU cost of the counter guards (if(DEBUGMOTION) _rafN++). Provide a micro-benchmark showing <0.1% overhead on a 60 fps rAF loop, OR rewrite the approach to avoid the branch (e.g., using an unconditional counter that is only displayed if DEBUGMOTION).
6. FIX 6: Add a comment in updateMotionDbg() explaining the try/catch around qaState().wxTruth and ensuring it is preserved in the extracted version. Test the function under network failure / fetch error to confirm it does NOT throw.
7. FIX 7: Reconcile the 'recommendNow: false' conclusion with the 'P2' priority and 'M' effort classification. EITHER change recommendNow to true (if the extraction is justified now), OR lower the priority to P3/P4 and explain why deferral is safer. Update the plan title or summary to reflect the deferral recommendation.
8. FIX 8: Add a performance regression test or micro-benchmark to show that _starSampleNow() and the DOM queries in updateMotionDbg() do NOT cause measurable slowdown. Current code (once per second) is safe, but document the cost baseline so a future refactoring does not accidentally move the call to a tighter loop.

**Missing risks the spec omitted:**
- CRITICAL: The cEl closure dependency is NOT safely resolvable without a guard. Plan says 'expose cEl as module-scope let initialized by boot()' but cEl is declared AFTER boot-scoped setup (line 1907). If cEl is hoisted to module scope, it must be initialized to null BEFORE boot() runs. But updateMotionDbg() reads cEl.classList (line 1923) and cEl.dataset.fx (line 1927) — if render() is called before boot() initializes cEl (unlikely but possible in error cases), this throws. Plan acknowledges this ('option B: fresh querySelector') but recommends (A) without a null guard. Implementation must use cEl?.classList or assign a safe sentinel.
- FRAGILE: Conditional state allocation is ambiguously specified. Plan says 'wrap in if(DEBUGMOTION){}' but does NOT clarify if this is block-scoped (wrong) or declaration-hoisted (correct). The correct pattern is: 'let _rafN; if(DEBUGMOTION){ _rafN=0; }' NOT 'if(DEBUGMOTION){ let _rafN=0; }'. The plan text does NOT specify this, leading to implementation error.
- HIDDEN COST: _tickAcc reset MUST happen every ~1000ms regardless of DEBUGMOTION state, so future rate calculations stay correct. Plan says 'always run the aggregation block' and 'only compute/display rates if DEBUGMOTION' but does NOT write the exact code pattern. If the implementation wraps the ENTIRE if(rt-_tickAcc>=1000) block in if(DEBUGMOTION), the reset is skipped and the next tick's rate calculation diverges permanently.
- OBSERVABILITY GAP: The qaState().wxTruth call (line 1921) throws if qaState is not defined or throws. Plan does NOT mention testing this under network failure or during fetch errors. Current code wraps it in try/catch, but extraction must preserve this. No mention in acceptance criteria.
- MEMORY LEAK RISK: _motHist array cleanup (line 1917, max 61 samples via shift()) will leak if _motHist is declared conditionally and the extraction forgets to reset/clear it across sessions. Plan does NOT address bounds checking or memory cleanup.
- BRANCH COST MISJUDGED: Plan claims 'single branch prediction miss, negligible cost' but does NOT account for the fact that at 60 fps, an unpredicted branch in the rAF loop can cause a 0.1–0.5% CPU overhead (pipeline stall). Modern CPUs predict constant branches well, but this is not guaranteed. Plan should measure actual cost or use a compile-time flag (not available in this no-build project).
- Z-INDEX AND DOM QUERY: If updateMotionDbg() is extracted and the .dbgmotion selector fails (DOM element removed/renamed), the function silently returns (line 1916, 'if(!dm) return'). Plan does NOT ensure the DOM element is ALWAYS present or that its z-index (7) does not conflict with other overlays.
- STAR ANIMATION QUERY: _starSampleNow (line 1914) queries all .stars circle elements every update (~1–2 ms cost per second). Plan does NOT optimize this or suggest caching. Low priority but could degrade performance if later moved to a tighter loop.

**Weak acceptance criteria (a broken change could still pass):**
- BYTE-IDENTICAL OVERLAY TEXT: Plan's criterion 'the overlay text output (`.dbgmotion` textContent) is byte-identical' is WEAK because: (1) does NOT specify encoding/line-break/precision details; (2) does NOT define how to verify (diff? screenshot? smoke test?); (3) NO unit test or smoke assertion captures the exact format. A subtle change like %.1f → %.0f or adding a space would pass the criterion if no one manually inspects. RECOMMENDATION: add a smoke test with a character-by-character or regex assertion on the overlay text format.
- SMOKE TEST COVERAGE: Plan claims '31/31 smoke tests pass' as proof of no regression, BUT tests/smoke.html does NOT test ?debugMotion=1 (it is listed as a debug feature, not a tested behavior at line 245). A broken extraction that stops calling updateMotionDbg() would PASS all 31 tests but FAIL the overlay. Smoke tests verify 'no regression in non-debug case' NOT 'overlay still works.' RECOMMENDATION: add a dedicated smoke test for ?debugMotion=1 that verifies: (1) overlay appears when flag is set; (2) text contains expected fields (rAF, cloudPaint, reduced, motion=full, paused, timeScale, advancing, cloudΔ, starΔ, wx, fx, reason); (3) overlay updates ~once per second.
- COUNTER-INCREMENT COST: Plan says 'if(DEBUGMOTION) _rafN++; minimal cost if the flag is constant' but does NOT measure actual CPU overhead. Claim is plausible (modern CPUs predict constant branches well) but not validated. RECOMMENDATION: measure or provide a micro-benchmark showing <0.1% overhead on the non-debug case.
- CONDITIONAL ALLOCATION PATTERN: Plan says 'only if DEBUGMOTION===true' but does NOT write the exact code pattern. Acceptance criterion says 'state allocated only if DEBUGMOTION' but without specifying the JavaScript pattern (declaration hoisting, block scope, initialization order), an implementation could: (1) declare in an if block (wrong, block-scoped); (2) forget to initialize; (3) leak state across runs. RECOMMENDATION: provide the exact code snippet in the approach, not just the concept.
- TickAcc Reset Safety: Plan says 'ensure _tickAcc is always reset' but does NOT write the refactored code. The acceptance criterion says '_tickAcc reset happens on every second … NEVER skipped' but the implementation details are missing. If the implementation wraps the entire if(rt-_tickAcc>=1000) block in if(DEBUGMOTION), the reset is skipped. RECOMMENDATION: write the exact refactored loop() logic or add an assertion that _tickAcc is reset every tick.

**Scope concerns:**
- WITHIN SCOPE: The extraction stays within boot() and loop() internals. Does NOT modify atmosphere(), paint(), renderMoon(), or the sky rendering. Single-file/no-build character is preserved. No forbidden regressions.
- BOUNDARY-ADJACENT: The extraction is tightly coupled to loop()-scoped state (_lastSec, _lastWx, _lastCloud, _rafN, _cloudN, _tickAcc). A mistake in refactoring the loop will immediately break the entire rAF clock, not just the telemetry. This is a single-point-of-failure for the render loop — the risk is high.
- CONTRADICTORY RECOMMENDATION: Plan itself says 'recommendNow: false' and concludes 'Recommendation: DEFER. The value is clean-up/polish; the cost is risk. Not recommendNow.' This is HONEST but contradicts the 'P2' priority and 'M' effort claim. If the recommendation is to defer, the plan should be labeled as such, not presented as ready-to-execute.
- ALTERNATIVE DISMISSED: Plan briefly considers 'wrap telemetry in a class/object (MotionDebugger)' and rejects it as 'over-engineered.' This is correct, but it means the extraction is a low-value refactoring — it improves readability marginally (moving 3 functions out of a 100-line boot) but adds risk to the highest-touch function in the app (the rAF loop).
- DEFERRED WORK OVERLAPS: ARCHITECTURE.md already lists three deferred items (solarElevationDeg, lift corner-sun tone-map, day-rollover robustness). The motion-telemetry extraction is a FOURTH deferred item. The plan does NOT prioritize which deferred work to tackle first. If the next task is a major refactor (e.g., file split), extracting the telemetry first might simplify that work — but the plan does NOT make this case.

**Grounding issues (claims to re-check against current code):**
- Line numbers and code quotes are ALL VERIFIED against current index.html (lines 504, 1912–1929, 1931, 1961). ARCHITECTURE.md deferred entry is real (line 74–75).
- Plan accurately identifies DEBUGMOTION const declaration at line 504, TIMESCALE at line 545, ADVANCING at line 546, isMotionReduced() at line 509 — all exist and are module-scope consts.
- Plan accurately quotes _cloudAlphaNow (line 1913), _starSampleNow (line 1914), updateMotionDbg (lines 1915–1929) as closures inside boot().
- Plan accurately identifies cEl declared at line 1907 inside boot(), used in updateMotionDbg() at lines 1923, 1927, 1928 (reads .paused and .fx attributes).
- Plan accurately identifies the counter logic at line 1931 (_rafN++), lines 1959–1960 (_cloudN++), and line 1961 (per-second reset and updateMotionDbg call).
- .dbgmotion CSS exists at line 164, DOM element at line 356, selector query at line 1916 — all match plan.

**Reviewer notes:** This plan is SOUND in CONCEPT (the motion-telemetry is a self-contained debug feature that can safely be extracted) but WEAK in SPECIFICATION. The main issues are:

1. **AMBIGUOUS IMPLEMENTATION DETAILS:** The plan does NOT provide exact code snippets for critical sections (conditional allocation, _tickAcc reset, cEl scope). This leaves the implementer guessing, which in a high-touch function like boot() risks regression.

2. **WEAK VERIFICATION CRITERIA:** The acceptance criteria do NOT cover the most likely failure modes (cEl reads undefined, _tickAcc reset is skipped, updateMotionDbg() throws). The smoke tests do NOT test ?debugMotion=1, so a broken extraction could pass all tests.

3. **CONTRADICTORY RECOMMENDATION:** The plan itself says 'Recommendation: DEFER' but is presented as P2 and ready-to-execute. This creates confusion about whether the extraction should happen now or later.

4. **HIGH-TOUCH RISK:** The extraction touches boot() and loop(), the highest-risk functions in the app. A single mistake in the refactoring (e.g., skipping a _tickAcc reset or wrapping code in the wrong scope) breaks the entire rAF clock and the render loop. The risk/benefit analysis favours DEFERRAL.

**VERDICT: NEEDS-FIXES.** The plan should NOT be executed as-is. Required fixes are:
- Provide exact code snippets (not just concepts) for _tickAcc reset, conditional allocation, and cEl scope.
- Add a smoke test for ?debugMotion=1 to catch regressions in the overlay.
- Measure the actual CPU cost of the counter guards.
- Reconcile the 'recommendNow: false' conclusion with the priority classification.
- Strengthen the acceptance criteria to verify both the extraction logic AND the overlay display.

Once these fixes are applied, the plan is low-risk and can proceed. But as-is, it should be DEFERRED until either (1) a bug surfaces in the telemetry (extract while fixing), or (2) the next major refactor (e.g., file split, which ARCHITECTURE.md notes is NOT justified now).
