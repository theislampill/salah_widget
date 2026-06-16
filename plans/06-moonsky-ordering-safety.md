# Plan 06 — Make renderMoon → atmosphere (moonSky) ordering coupling safe

> **Status:** ✅ DONE (2026-06-16) — implemented with a **corrected mechanism**: the plan's "tick per `render()`, stamp in `renderMoon()`" design was found broken (`renderMoon` is minute-gated, runs ~1/min while `render` runs ~1/sec, so a per-frame tick would mismatch ~59/60 frames and throw constantly; also `qaState()` calls `atmosphere()` directly, so a hard throw is unsafe). Shipped instead: stamp `moonSky._min=mm` only when `renderMoon` runs; pure `A.moonSkyFresh` flag from `atmosphere()`; one-shot `console.warn` at the render boundary (not inside pure `atmosphere`); `qaState().moonTruth.moonSkyFresh`; new smoke assertion (27/27).  ·  **Class:** robustness  ·  **Priority:** P2  ·  **Effort:** S  ·  **Risk:** low
> **Do now?** Yes — recommended soon  ·  **Plan-review verdict:** `needs-fixes` (7 required fixes — see end)  ·  **Depends on:** none
>
> Read-only plan from `/implementaudit` (workflow `wf_f498de17-f7b`, investigate → adversarial critique). Grounded against `index.html` @ commit `91d0fc1` (~1951 lines). **No source was changed.** Line numbers drift — re-verify the anchors before editing.

## Problem
moonSky is a shared mutable state (alt, H, frac, up, sx, sy) written exclusively by renderMoon() and read by atmosphere(), projectStars(), and qaState(). The contract is a CONVENTION: renderMoon must execute before atmosphere in a single render tick, or atmosphere() silently receives stale moonSky values. This silent-stale failure mode is invisible to the renderer and can corrupt optical phenomena gated on moonSky (lunar halo, paraselenae at line 1516; lunar optics scaling in moonLight/moonUp/moonLume; moon position in cloud lighting line 1558). A careless reorder of render() calls would not raise an error — the sky would just render the moon's previous-frame geometry.

## Root cause
The renderMoon → atmosphere dependency is enforce only by coding discipline (the comment at line 827 and ARCHITECTURE.md § "High-risk mutation points"). There is no temporal assertion, versioning, or check to catch accidental reordering. The coupling lives across function boundaries with no validation layer.

## Current behavior
render() at line 1775 calls renderMoon() when the minute changes, then at line 1805 calls applyTheme (which invokes atmosphere(M)). The moonSky object is always in ONE of two states: (a) the current frame's fresh values (after renderMoon runs) or (b) the previous frame's stale values (before renderMoon runs this tick). atmosphere() has no way to know which. If render() is ever reordered or if projectStars() calls atmosphere() out of order, the error is silent.

## Desired behavior
atmosphere() should fail LOUDLY and EARLY if it detects that moonSky was not updated this tick, or it should recompute the moon state on first read (lazy-compute). In production, every rendered frame is astronomically correct. In tests, a deliberate skip of renderMoon() should be detectably broken — the guard fires, the test fails clearly, preventing a silent-stale regression.

## Code anchors (re-verify line numbers before editing)
**`index.html:827`**
the shared state object; initialized with plausible defaults

````js
let moonSky={alt:25,H:0,frac:0.5,up:1};                           // shared cinematic-moon state (read by applyTheme)
````

**`index.html:828-870`**
the exclusive writer of moonSky; updates alt, H, frac, up, sx, sy, rotDeg

````js
function renderMoon(){...}
````

**`index.html:1402-1568`**
reads moonSky.alt at line 1415; moonSky.alt again at line 1516 (paraselenae); moonSky.sx/sy at line 1558 (cloud moon position)

````js
function atmosphere(M){...const moonUp=clamp((moonSky.alt+2)/6);...
````

**`index.html:1699`**
the render boundary; atmosphere is invoked here, AFTER renderMoon should have run

````js
function applyTheme(M){ paint(atmosphere(M)); }
````

**`index.html:1775`**
renderMoon() is called in render() when the minute boundary crosses

````js
if(mm!==lastMoonMin){ lastMoonMin=mm; renderMoon(); }
````

**`index.html:1805`**
atmosphere is invoked AFTER renderMoon; the temporal coupling site

````js
applyTheme(M);
````

## Approach
Choose option (a) — a cheap tick-versioning guard with an early throw in atmosphere(). Implementation: (1) Add a module-scope `let _moonSkyTickId=0` counter, incremented at the START of render() (before any logic). (2) Inside renderMoon(), set `moonSky._tickId=_moonSkyTickId` AFTER updating all fields. (3) In atmosphere(), on first use of moonSky (before line 1415), add `if(moonSky._tickId!==_moonSkyTickId) throw new Error(...)` with a clear message. In production, the assert always passes because render() increments the tick before calling renderMoon. In tests or if render() is reordered, the assertion fires immediately, failing the render with a clear traceback. (4) No visual change, no structure change, pure safety. (5) Update ARCHITECTURE.md to document the guard as the new enforcement mechanism. This is zero-overhead in the normal path (a single integer comparison) and catches the silent-stale failure mode at first reference.

## Alternatives considered (and rejected)
- **(b) Lazy compute-on-first-read** — Requires calling moonNow() and moonAltAz() from within atmosphere, which pulls the ephemeris twice per tick (once in renderMoon at boot, once in atmosphere if stale). Adds hidden cost + logic duplication + changes atmosphere's contract (it is now impure, mutating moonSky). Higher risk of subtle cache-vs-recompute bugs. Harder to test (stale detection is implicit, not explicit). Better for 'old code that can't be reordered' but salah_widget is small and render() is the single orchestrator.
- **(c) Order-lock comment + refactor** — A loud comment alone (ARCHITECTURE.md update) does not prevent the error, only documents it. Refactoring (e.g., passing moonSky as an argument to atmosphere, or restructuring render()) is higher risk and more intrusive. Violates the 'minimal change' principle. The tick-id guard is cheaper and equally effective.

## Owner / source touchpoints
- index.html:~510 (after boot() config) — add `let _moonSkyTickId=0`
- index.html:1771 (start of render()) — add `_moonSkyTickId++` as the first line
- index.html:~868 (end of renderMoon, after all moonSky field writes) — add `moonSky._tickId=_moonSkyTickId`
- index.html:1413-1415 (in atmosphere, before moonUp is computed) — add the guard check
- ARCHITECTURE.md:183 — update the 'Remaining risks' entry for moonSky to reference the new tick-id guard

## Regression risks (forbidden-regression guardrails)
- If the guard check is placed AFTER other reads in atmosphere (not before line 1415), a stale moonSky could be used for other calcs before the error fires; place it at the very first read site (moonUp computation).
- If _moonSkyTickId is incremented AFTER renderMoon (instead of before), a double-render in a single tick would fool the guard into thinking moonSky is fresh when it is not. Always increment at the START of render().
- If moonSky._tickId is set BEFORE all field updates in renderMoon (not at the end), a partial write could set the tick and freeze the guard open. Set the tick AFTER the last field write (after sx/sy at the end).
- The guard string message must be clear enough to diagnose ('moonSky stale' is too vague; better: 'moonSky not updated this tick — renderMoon must run before atmosphere').
- If the guard is removed or commented out in a later refactor, this coupling is immediately silent-stale again. Document in AGENTS.md that the guard is non-negotiable.

## Smoke A — capture BEFORE any change
- Run the real-time widget and confirm it renders normally (no exceptions).
- Call window.qaState() and confirm moonTruth / moonAltitude reports match the current geometry.
- Load the widget with ?debugMoon=1 and confirm the moon's position, phase, earthshine, and halo/corona are rendered correctly over a few minutes.

## Smoke B — verify AFTER the change
- Run the real-time widget again; confirm no console errors.
- Call window.qaState() and confirm the same.
- Add a test case to tests/smoke.html that deliberately SKIPS renderMoon and calls atmosphere directly (mocking the error path). Confirm the guard fires with the clear message.
- Render a full day simulation (?timeScale=1800) and confirm all moon phenomena (halo at cirrus + high moon, paraselenae at cirrus + low moon, earthshine phases) render as gated (use ?debugOptic=halo / paraselene to force and verify they ring the visible moon, not the arc-sun). Confirm no stale-moon artifacts (e.g., halo at the wrong position because moonSky was from the previous frame).

## Acceptance criteria (falsifiable)
- The widget renders without console errors in real-time and under ?timeScale fast-forward.
- qaState().moonTruth.moonAltitude matches the rendered moon's on-screen position (via ?debugMoon=1 and visual inspection).
- A new test in tests/smoke.html deliberately skips renderMoon (by commenting out the line in render()) and calls atmosphere directly; the guard throws with the exact message 'moonSky not updated this tick — renderMoon must run before atmosphere'. The test harness catches the error and reports it as a FAIL (expected).
- Forced-optic test (?debugOptic=halo with simMoon=0.6, simWax=1, simMoonAlt=30, simCloud=20 for cirrus): the 22° halo rings the visible moon (top-right corner), not the arc-sun center. Repeat for paraselene (?debugOptic=paraselene) to confirm they are lateral to the moon, not floating mid-card. Confirms the guard prevents stale moonSky from breaking optic position.
- Over a 24h sim, the moon's phase/position/earthshine evolve smoothly; no sudden jumps or repeats that would indicate a 'reused frame' stale-state artifact.
- ARCHITECTURE.md § 'Remaining risks' is updated to note: 'The moonSky ordering coupling is now enforced by a tick-id guard in atmosphere(); careless reorders will throw immediately.'

## Rollback
If the guard causes an unexpected false positive (e.g., atmosphere is called from a non-render context in a future refactor), revert the three code changes (remove _moonSkyTickId, the increment in render(), and the set in renderMoon, and the guard check in atmosphere). The coupling will revert to convention-only, and AGENTS.md must be updated to warn that reordering is now a silent-stale risk again. No visual regression; the only cost is loss of safety.

## Dependencies / sequencing
_(none)_

## Open questions
- Should the guard be a throw (hard error, dev-time fail) or a console.warn (silent prod, logged failure)? RECOMMENDATION: throw. This is a correctness bug, not a user-visible UI issue, and should crash early in a test. QA/smoke tests will catch it immediately. Prod widgets will never trigger it (render() is the single orchestrator).
- Should moonSky._tickId be a separate object (e.g., {id:...} wrapper) or a direct property on moonSky? RECOMMENDATION: direct property. moonSky already holds multiple fields; one more property is negligible and avoids a wrapper indirection. Linters may complain about the dynamic property; suppress with a comment if needed.
- Do we need to version projectStars() as well, since it also reads moonSky? RECOMMENDATION: no, not yet. projectStars() is called earlier in render() (line 1778, before renderMoon in most frames) and reads moonSky's screen position (sx/sy) and phase (frac, up). For stars the reads are less time-critical (star positions are fixed in real-time, only re-projected under timeScale). If projectStars is ever called AFTER atmosphere in a refactored render(), the guard in atmosphere will catch the out-of-order issue before stars cause a problem. Monitor, but defer star-side versioning to a follow-up if drift appears.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. FIX 1 — TICK INCREMENT PLACEMENT: Change plan step '(1) add module-scope _moonSkyTickId=0 counter, incremented at the START of render()' to: 'incremented at the START of render() AFTER the `if(!today)return` guard (line 1773), so only rendered frames advance the tick.' This avoids phantom ticks from failed renders.
2. FIX 2 — TICK-ID SET PLACEMENT CLARITY: Explicitly state that moonSky._tickId is set AFTER line 862 (the object reassign), NOT before it. If renderMoon() returns early, the old moonSky remains with the old tick ID (conservative, correct behavior).
3. FIX 3 — GUARD ERROR MESSAGE SPECIFICITY: The plan says 'with a clear message' but doesn't specify it. Recommend: `throw new Error('INTERNAL: moonSky stale — renderMoon() did not run before atmosphere() this tick. Tick mismatch: expected ' + _moonSkyTickId + ', got ' + (moonSky._tickId||'(unset)'))`  — includes the tick IDs for debugging.
4. FIX 4 — TEST HARNESS SPECIFICATION: In Acceptance Criterion 3, explicitly describe the test: (a) Create a harness that calls renderMoon() to set the tick, (b) manually increment _moonSkyTickId without calling renderMoon(), (c) call atmosphere(mockM) and expect a throw with the exact message, (d) wrap in try/catch and report FAIL if no throw. Provide pseudo-code.
5. FIX 5 — OUT-OF-RENDER CALL DOCUMENTATION: Add a note to AGENTS.md or a comment in the code: 'atmosphere() MUST ONLY be called from render()→applyTheme(). Direct or indirect calls from other code paths (tests, debug tools, UI queries) MUST ensure moonSky was updated in the same render tick, or the guard will throw. If a new call site is added, update this invariant.'
6. FIX 6 — OPTICS VISUAL CRITERION SPEC: Criterion 4 should include: 'The halo/paraselenae ring center must be within 2° (visual angle) of the visible moon's center on screen. Captured as a side-by-side crop: forced halo vs unforced (clear sky) over the same moon position.'
7. FIX 7 — SMOKE TEST ACCEPTANCE: Specify that Criterion 5 ('24h smooth evolution') is validated by sampling qaState().moonTruth.moonAltitude every 30 simulated minutes and confirming ∆alt ≤ 15° between samples (natural lunar trajectory limit). No ∆alt > 30° = FAIL (indicates a stale/skipped frame).

**Missing risks the spec omitted:**
- OUT-OF-RENDER CALLS: The guard assumes atmosphere() is called ONLY from render()→applyTheme(). If a future debug tool, test, or new UI feature calls atmosphere() directly (e.g., to preview sky color for a given M), the guard will throw a false-positive on a stale moonSky that was never meant to be updated. atmosphere() is documented as PURE STATE with no explicit render-only contract in the code.
- EARLY-RETURN TICK LOSS: If _moonSkyTickId is incremented at the START of render() (line 1771, before the `if(!today)return` guard at 1772), then a failed render (no today) increments the tick but produces no visual frame. The next successful render will have tickId=N+1 but moonSky might still be N (if renderMoon wasn't called). This is subtle but safe IF DOCUMENTED — the guard will then correctly catch the stale state. However, it violates the principle: 'a tick should correspond to a rendered frame.' RECOMMENDED FIX: increment AFTER the `if(!today)` guard so only frames that render increment.
- PARTIAL-UPDATE VULNERABILITY: renderMoon() reassigns moonSky at line 862. The plan says 'set _tickId AFTER updating all fields.' If any code path in renderMoon() returns early or throws BEFORE line 862, moonSky is stale with a NEW tick ID (misleading the guard into thinking it's fresh). The plan doesn't address this. RECOMMENDED FIX: Set tickId at END of renderMoon(), right after line 862, ONLY if the function reaches it normally. Or wrap the reassign in try/finally.
- TEST HARNESS AMBIGUITY: Acceptance Criterion 3 requires 'a test that deliberately skips renderMoon and calls atmosphere directly.' The plan doesn't specify: (a) how to RESET the tick counter so the test doesn't depend on prior render history, (b) what M object to pass to atmosphere(), (c) how to verify the exact error message. A naïve test could PASS incorrectly if the prior tick ID happens to match.
- OPTICS VISUAL VALIDATION (Criterion 4): Forced-optic test requires manual screenshot inspection ('the halo rings the visible moon, not the arc-sun center'). No automated check, no color tolerance spec, no position tolerance. A halo offset by 2-5% could pass by eye. RECOMMENDATION: specify pixel bounds or a visual diff tool.
- RENDER-BOUNDARY FRAGILITY: atmosphere() is documented as PURE, but paint() calls it within applyTheme(). If atmosphere() ever gains a side-effect (e.g., logging, cache invalidation), or if a refactor moves atmosphere() to a different call site, the tick-ID guard could become a maintenance burden. RECOMMENDATION: document the guard as load-bearing (cannot be removed without re-auditing call sites).

**Weak acceptance criteria (a broken change could still pass):**
- Criterion 2 ('qaState().moonAltitude matches visual') — requires a judge to visually compare screenshot position to qaState number. No tolerance specified. Could pass with ±5° error if not scrutinized.
- Criterion 3 ('guard throws with exact message') — the test harness is not specified. A test could incorrectly PASS if moonSky._tickId happens to equal _moonSkyTickId due to prior state, not because the guard is absent.
- Criterion 4 ('halo rings the visible moon, not arc-sun center') — subjective visual criterion. 'Rings' could mean many positions. No crop/zoom spec, no angular tolerance, no color check.
- Criterion 5 ('no sudden jumps or repeats over 24h sim') — 'sudden' and 'repeat' are vague. What magnitude ∆ counts as sudden? How is 'repeat' distinguished from smooth looping?
- Overall PASS condition is visual-judge-dependent (no automated CI gate); if judges disagree or fail to inspect, the acceptance criteria may pass a broken implementation.

**Scope concerns:**
- MINIMAL SCOPE PRESERVED: ✓ No new files, no build changes, no refactoring. Four surgical changes only: `_moonSkyTickId` var, increment, set, guard check.
- RENDER-BOUNDARY PRESERVED: ✓ atmosphere() remains pure (no DOM writes, no external side-effects introduced).
- SINGLE-FILE CHARACTER PRESERVED: ✓ No new files or dependencies.
- TDZ ORDERING PRESERVED: ✓ All variables used in atmosphere() are declared before their first read; the guard at line 1415 is before all moonSky field reads.

**Grounding issues (claims to re-check against current code):**
- Plan cites 'ARCHITECTURE.md § "Remaining risks" at line 183' — verified correct; the ref documents the coupling as 'convention, not enforced'
- All line number citations in index.html are accurate (±0-2 lines): line 827 moonSky init, 828 renderMoon() start, 862 moonSky reassign, 1415 first moonUp read, 1516 second moonSky.alt read, 1558 moonSky.sx/sy read, 1775 renderMoon call in render(), 1805 applyTheme call
- Code quotes match current file exactly; no semantic drift between plan and implementation

**Reviewer notes:** OVERALL VERDICT: The plan is SOUND IN CONCEPT and solves the REAL PROBLEM (silent-stale moonSky coupling). The code changes are minimal, safe, and non-regressive. HOWEVER, the implementation details have THREE GAPS that must be addressed before coding: (1) tick-increment placement w.r.t. early-return guards, (2) test harness specification for Criterion 3, (3) out-of-render-call vulnerability documentation. The acceptance criteria are WEAK in places (visual-judge-dependent, unspecified tolerances) but acceptable if judges are trained on the visual pass/fail gates listed in AGENTS.md. RECOMMENDATION: Apply the 7 required fixes above as concrete code comments and test pseudo-code before implementation, then proceed. The risk level is low (the guard is cheap, and the impact is zero-visual), but the documentation is critical to prevent future maintenance confusion.
