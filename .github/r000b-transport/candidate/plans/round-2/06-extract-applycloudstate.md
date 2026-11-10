# Plan R2-06 — Extract cloudState mutation from paint() into applyCloudState(A)

> **Status:** ✅ DONE (2026-06-16) — **pure extraction**: the cloudState mutation moved from `paint()` into a top-level `applyCloudState(A)` that `paint()` calls internally (render() does NOT learn cloud internals, per the decision). Identical statements + order; cloud math/easing/seed/wind/tints/sun-moon lighting/`_cloudDirty` unchanged. Verified: `cloudState.tgtLow` tracks `A.cloudLayerLow`, deck renders + morphs+advects (`moving:true`), `cloudFieldSeed` stable (continuity smoke), overcast visually equivalent; 35/35. `paint()` now writes only sky CSS (+ this one clearly-separated side-effect call).  ·  **Class:** architecture  ·  **Priority:** P2  ·  **Effort:** S  ·  **Risk:** low
> **Do now?** Deferred / decision-gated  ·  **Plan-review verdict:** `needs-fixes` (7 required fixes — see end)  ·  **Depends/notes:** see "Dependencies / notes"
>
> Read-only round-2 plan from `/implementaudit` (workflow `wf_3f9f2919-894`, investigate → adversarial critique). Grounded against the **current working tree** (`index.html` with the 2026-06-16 uncommitted pass applied; HEAD `91d0fc1`). **No source was changed.** Re-verify anchors before editing.

## Problem
paint(A) mutates global `cloudState` (lines 1658-1669), writing coverage targets, easing/snapping logic, wind vectors, tints, sun/moon positions, and the `_cloudDirty` flag. This is the LAST render-layer side effect in paint() after the corner-sun tone-map was lifted into atmosphere() in the 2026-06-16 pass. The mutation violates SRP: paint() is supposed to be a pure DOM writer, but it also advances cloud state continuity (ease-vs-snap), which is a presentation/animation concern, not a CSS property write.

## Root cause
The cloudState block was left in paint() during the tone-map lift because it is tightly coupled to the ease/snap continuity invariant (the ADVANCING check, _cloudReady flag, coverage easing formula ce=ADVANCING?1:0.08). Separating it requires clarity on whether it belongs in render() (alongside renderMoon → atmosphere) as a pre-atmosphere step, or stays in paint() as a clearly-marked, side-effecting subsection that is logically separate from CSS writes.

## Current behavior
paint(A) { [lines 1599–1657: pure CSS writes] [lines 1658–1669: cloudState mutation — 11 lines] [lines 1670–1702: more CSS writes + debug] }. The cloudState block reads A.cloudLayerLow/Mid/High (from atmosphere) and previous cloudState values, writes to CS.covLow/Mid/High (eased or snapped), CS.tgtLow/Mid/High, CS.wx/wy/wspd, CS tints, sun/moon screen positions, CS.sunUp, and sets _cloudDirty=true. The ease-vs-snap branch (line 1663-1664) is the heart: if (!_cloudReady && total-coverage > 0.05) snap, else ease with ce=ADVANCING?1:0.08. paintClouds(t) (line 1338) reads cloudState and re-renders every 76ms (or frozen under reduced-motion), relying on cloudState.covLow/Mid/High continuity to avoid slideshow.

## Desired behavior
Extract the 11-line cloudState block into a separate applyCloudState(A) function. Call it either: (A) from render() right before applyTheme(M), alongside renderMoon (makes render() the orchestrator of all state-mutation steps), OR (B) from within paint(A), immediately after the CSS header and before any CSS writes, with a clear comment block marking it as "side-effecting, not pure." The extraction must preserve: (1) the ADVANCING fast-forward snap (cloudState advances instantly when ADVANCING=true), (2) the ease continuity (when ADVANCING=false, covLow/Mid/High ease with 8% per frame, no slideshow on a 15-min refetch), (3) the _cloudDirty flag (paintClouds re-renders when true), (4) the stable identity (_cloudFieldSeed and the per-location cloud population). Behaviour-identical: clouds render + drift exactly as before.

## Code anchors (re-verify line numbers before editing)
**`index.html:1309`**

````js
let _cloudReady=false;   // false until the deck is first established (then coverage changes EASE instead of snapping)
````

**`index.html:1313-1315`**

````js
let cloudState={covLow:0,covMid:0,covHigh:0,tgtLow:0,tgtMid:0,tgtHigh:0,wx:-0.7,wy:0.2,wspd:0.15,
  tLow:[208,214,226],tMid:[232,236,243],tHi:[233,238,247],sunX:0.5,sunY:0.3,sunUp:0,
  sunCol:[255,247,232],moonCol:[206,220,246],moonX:0.84,moonY:0.1,moonLit:0};
````

**`index.html:1658-1669`**

````js
// cloud DECKS render on the canvas density field (paintClouds). MUTATE the shared state (no per-tick realloc).
  const CS=cloudState;
  CS.tgtLow=A.cloudLayerLow; CS.tgtMid=A.cloudLayerMid; CS.tgtHigh=A.cloudLayerHigh;
  // Establish the deck promptly the FIRST time clouds appear (snap), then EASE every later coverage change so a
  // 15-min refetch grows/erodes the EXISTING deck smoothly — no popping/slideshow. Fast-forward snaps (must track).
  if(!_cloudReady && (CS.tgtLow+CS.tgtMid+CS.tgtHigh)>0.05){ CS.covLow=CS.tgtLow; CS.covMid=CS.tgtMid; CS.covHigh=CS.tgtHigh; _cloudReady=true; }
  else { const ce=ADVANCING?1:0.08; CS.covLow+=(CS.tgtLow-CS.covLow)*ce; CS.covMid+=(CS.tgtMid-CS.covMid)*ce; CS.covHigh+=(CS.tgtHigh-CS.covHigh)*ce; }
  CS.wx=A.windUX; CS.wy=A.windUY; CS.wspd=0.06+0.6*A.windSpeedNorm;
  CS.tLow=A.cloudTint2; CS.tMid=A.cloudTint; CS.tHi=A.cloudTintHi;
  CS.sunX=A.sunX/100; CS.sunY=A.sunY/100; CS.sunUp=clamp((A.solarElevationDeg+1)/5);   // clouds stay sun-lit even at a low golden-hour sun
  CS.sunCol=A.cloudSunCol; CS.moonCol=A.cloudMoonCol; CS.moonX=A.cloudMoonX; CS.moonY=A.cloudMoonY; CS.moonLit=A.cloudMoonLit;
  _cloudDirty=true;
````

**`index.html:1338-1384`**

````js
function paintClouds(t){
  if(!_cloudCv){ _cloudCv=document.querySelector('.cloudcanvas'); if(!_cloudCv) return; _cloudCtx=_cloudCv.getContext('2d'); }
  const W=_cloudCv.width,H=_cloudCv.height,S=cloudState,ctx=_cloudCtx;
  ctx.clearRect(0,0,W,H);
  const cols=(_colDens&&_colDens.length===W)?_colDens:(_colDens=new Float32Array(W)); cols.fill(0);
  if(S.covLow+S.covMid+S.covHigh<0.02){ _cloudDirty=false; return; }   // clear sky → nothing
  [paintClouds engine reads cloudState and renders the canvas]
````

**`index.html:1704`**

````js
function applyTheme(M){ paint(atmosphere(M)); }                 // physical state → render
````

**`index.html:1776-1815`**

````js
function render(){
  if(!today) return;
  syncWeather();                                              // sim/fast-forward: pull weather from the forecast track at simTime
  const M=model();
  const mm=Math.floor(M.nowMin); if(mm!==lastMoonMin){ lastMoonMin=mm; renderMoon(); moonSky._min=mm; }   // re-render the moon each minute so its orientation/earthshine track the evening; stamp the minute so atmosphere() can detect a stale / out-of-order moonSky
  [... prayer UI + arc writes ...]
  if(moonSky._min!==mm && !_moonStaleWarned){ _moonStaleWarned=true; console.warn("salah_widget: moonSky stale this tick..."); }
  applyTheme(M);
  [observability + lightning]
````

**`index.html:1959-1960`**

````js
if(isMotionReduced()){ if(_cloudDirty){ paintClouds(1000); tieRainToClouds(); _cloudN++; } }   // LIVE reduced-motion (single source; honours a mid-session OS toggle)
    else if(rt-_lastCloud>76){ _lastCloud=rt; paintClouds(simNow()/1000); tieRainToClouds(); _cloudN++; }
````

## Approach
**Option A (recommended): Call applyCloudState(A) from render() before applyTheme(M).** Rationale: render() already orchestrates the side-effecting steps (renderMoon → atmosphere/paint chain); placing applyCloudState(A) before applyTheme mirrors the logical order (all state-mutation preparatory steps, then rendering). This makes the render-layer contract clear: state setup (renderMoon + applyCloudState) → pure atmosphere() → pure paint(). Call site: render() line 1815 becomes `applyCloudState(atmosphere(M)); applyTheme(M);` — but atmosphere(M) is called twice (inefficient). Better: `const A=atmosphere(M); applyCloudState(A); paint(A);` to unroll applyTheme inline. Result: three fully-separated steps (renderMoon/applyCloudState/paint) that are visually aligned, easy to reorder if needed, and clearly document that applyCloudState is a side effect. Minimal edit: add applyCloudState() before the applyTheme call, update applyTheme inline. **Option B (minimal change): Keep applyCloudState(A) as the FIRST step inside paint(A).** Rationale: paint() already owns the cloudState write-through (it's the sole place that mutates cloudState), so grouping it at the top of paint (with a clear comment block) keeps all cloudState writes in one function. Call site: no change to render(). Result: paint() logically becomes two sections: (1) applyCloudState—side-effecting, (2) CSS writes—pure. Risk: the two-part structure is less obvious to future readers, and paint() is still "impure" (just clearly documented). **Chosen: Option A**, because it aligns with the earlier tone-map lift (atmosphere → paint separation) and makes render() the orchestration point for all side effects. If Option A regresses (sky/clouds out-of-sync), Option B is a safe fallback—the extraction logic is identical, only the call site changes.

## Alternatives considered (and rejected)
- **Fold applyCloudState into atmosphere(), returning cloudState updates as part of the atmosphere object** — Violates the render-boundary purity contract: atmosphere(M) is documented as a PURE state vector (no DOM, no side effects, no mutable shared state writes). Cloudstate is a mutable, shared-memory object that persists across frames and drives canvas paint timing—exposing it from atmosphere breaks the purity invariant and makes atmosphere a hybrid (part computation, part mutation). Also, it couples the layer-algebra (cloudLow/Mid/High coverage values in A) with the presentation-timing decision (ease vs snap based on ADVANCING flag), muddying the physics/render boundary.
- **Keep cloudState mutation in paint(), but separate it into a named inner function applyCloudState(A) that paint() calls** — Reduces refactoring friction but leaves paint() impure and doesn't improve readability—paint() still owns the side effect, just delegates to a helper. It's a middle ground that doesn't clarify the contract. Given the architecture goal (paint() = pure DOM writer), the goal is to move the mutation OUT of paint(), not just refactor it within.
- **Hoist cloudState writes into a global pre-paint step in loop() at every iteration** — Would require cloudState updates to be driven from loop() directly, reading A.cloudLayer* and ADVANCING — but A (the atmosphere state) is only computed once per render() via applyTheme(). This would either (1) duplicate the atmosphere computation in loop(), or (2) break the one-call-per-frame contract and recompute it twice. Too costly and error-prone.
- **Introduce a separate render-timing scheduler for cloudState that runs independent of paint()** — Over-engineering. The cloudState update is lightweight (a few field copies + an ease formula). The ADVANCING check is already the right gate (it's consulted elsewhere in render). No need for a separate subsystem.

## Owner / source touchpoints
- index.html:~1309
- index.html:~1313-1315
- index.html:~1658-1669
- index.html:~1338-1384
- index.html:~1704
- index.html:~1776-1815
- index.html:~1959-1960

## Regression risks (forbidden-regression guardrails)
- **Ease/snap continuity broken:** If the ce=ADVANCING?1:0.08 logic is miscopied or the _cloudReady flag is not initialized correctly, coverage changes will either snap instantly (no easing, visible popping) or stay frozen. Smoke: watch a 15-min refetch fetch at real-time (ADVANCING=false) and confirm clouds grow/erode smoothly over 10-20 frames, not pop-in or freeze. Expected behaviour: covLow progresses from 0→0.5 in ~20 frames (0.08*20≈1.6 updates).
- **Fast-forward snap broken:** If applyCloudState is called after atmosphere (not before), or if ADVANCING is consulted at the wrong scope, clouds will ease during fast-forward and appear to lag. Smoke: set ?timeScale=60 and confirm clouds snap to target coverage instantly (frame-to-frame), not easing. If clouds ease during fast-forward, ADVANCING is not being read correctly.
- **_cloudDirty flag not set:** If the line `_cloudDirty=true` is omitted or moved outside applyCloudState, paintClouds will not re-render when cloudState changes (e.g. a weather refetch). Smoke: fetch new weather and confirm clouds re-paint within 76ms (or immediately under reduced-motion). Check the cloud-alpha Δ in qaState() or watch the canvas re-render on screen.
- **Cloud identity lost:** If applyCloudState is called in the wrong order relative to atmosphere or if cloudState is re-allocated (instead of mutated in-place), the per-location cloud population (_cloudFieldSeed) will reseed and clouds will pop in/out. This is the hardest to detect visually; use qaState().clouds.hash before/after a 15-min refetch and confirm it is continuous (hash evolves, not jumps to a new tree).
- **Render loop mismatch:** If applyCloudState is called from render() but paintClouds still runs on its own ~76ms timer (line 1959-1960), there could be a phase shift where cloudState values change but paintClouds hasn't run yet. This is acceptable (paintClouds will catch up in the next interval), but if the timing is too loose, clouds may appear to lag by up to 76ms. Expected: lag is <1 frame visually (imperceptible at real-time).
- **ADVANCING scope leak:** The ADVANCING flag is global. If applyCloudState is inlined or copied incorrectly, ADVANCING might be shadowed by a local var or captured from the wrong scope. Verify ADVANCING is the GLOBAL var, not a function parameter.
- **Violate render-boundary purity:** Any additional mutations introduced during the extraction (e.g. writing to _cloudDirty from atmosphere, or reading _cloudReady from paint) would break the purity contract further. Must keep cloudState/ADVANCING/_cloudReady/_ cloudDirty as the only mutable state touched by applyCloudState.

## Smoke A — capture BEFORE any change
- Screenshot at real-time (ADVANCING=false, no ?timeScale), clear sky → broken cumulus (0.2 coverage) over 30s: cloud clusters birth/grow/erode smoothly with no visible popping. Hash the cloud canvas (`qaState().clouds.hash`) at t=0s, t=15s, t=30s; confirm hash changes continuously (no loops or jumps).
- Screenshot at real-time, trigger a simulated weather change (e.g. ?simWx=80 → 95), watch the cloud coverage transition from broken to overcast over 15-20 frames at real-time; confirm NO snap/pop, smooth easing from cov≈0.2 → 0.9.
- Screenshot at fast-forward (?timeScale=60, clear→overcast change), confirm clouds snap to full coverage in one frame; no easing visible.
- QA readout (?qa=1): confirm cloudLayerLow/Mid/High values in atmosphere match cloudState.tgtLow/Mid/High after a paint cycle.
- Console: no errors, no warnings (except the one-shot moonSky stale warning if the render order is intentionally broken for testing).

## Smoke B — verify AFTER the change
- Same three screenshots as Smoke A, pixel-compared side-by-side: clouds are **visually identical** (same silhouettes, same positions, same tints, same sun/moon rim light). Diff shows <1% pixel delta (only timing jitter in the FBM advection, not a structural change).
- Same QA readouts as Smoke A: cloudLayerLow/Mid/High, cloudState.covLow/Mid/High, cloudState.tgtLow/Mid/High are identical before and after extraction.
- Cloud-alpha telemetry (?debugMotion=1): cloudΔ 10s / 60s values are within ±2% of Smoke A (confirms advection rate is unchanged).
- Reduced-motion mode (?motion=no or via OS): cloud frame is frozen (painted once), and redrawn only if weather changes (not continuously). After extraction, behaviour is identical.
- Live moon-rim light on clouds: extract by placing applyCloudState BEFORE paint, so cloudState.moonX/moonY are updated from atmosphere's computed moon screen position. Verify the cool moon-rim glow on cloud edges at night is continuous (no jump when moon rises/sets or when weather fetches). This is a tight coupling check.
- Run `tests/smoke.html`: all characterization smokes pass (currently 31/31; post-extraction must remain 31/31 or account for changes).

## Acceptance criteria (falsifiable)
- **Cloud continuity:** Ease-vs-snap branching is byte-identical after extraction. No 1-frame discontinuities in cloudState.covLow/Mid/High (diff-check BEFORE vs AFTER qa states). Specifically: covLow at real-time should increase by ce*(tgtLow-covLow)≈0.08*Δ per frame; at fast-forward, should jump to tgtLow in one frame.
- **Visual identity:** A side-by-side pixel diff of clouds (screenshot at real-time, same location, same time-of-day, same weather) before and after extraction shows <1% delta (only sub-pixel FBM noise jitter, no structural change in cluster count/size/position). RMSE of cloud silhouette alpha <0.5% per column.
- **Render-boundary integrity:** atmosphere(M) remains pure (no side effects, no DOM writes, deterministic return value). paint(A) is called exactly once per render tick (confirm via `_lastRender` telemetry). applyCloudState(A) is called exactly once per render tick, with the same A object. No double-calls, no skipped calls.
- **Painting order:** If applyCloudState is moved to render(), it must be called BEFORE applyTheme (cloudState is populated BEFORE atmosphere reads it for initialization, or atmosphere outputs are fed to applyCloudState). Verify: applyCloudState(A=atmosphere(M)); paint(A) order is preserved.
- **ADVANCING fidelity:** At ADVANCING=true, cloudState.covLow/Mid/High jump to targets in one frame (ce=1.0). At ADVANCING=false, they ease with 8% per frame (ce=0.08). No missed frames, no off-by-one. Verified by a fast-forward screenshot (1 frame snap) vs a real-time sequence (smooth 15+ frame ramp).
- **_cloudDirty flag:** Set to true on every call to applyCloudState (even if cloudState hasn't logically changed, to ensure paintClouds re-renders on schedule). Verify: if _cloudDirty=false at the start of applyCloudState, it is true at the end.
- **Cloud field identity:** _cloudFieldSeed is never recomputed, never reseeded. cloudState object is mutated in-place, never re-allocated. After 1 hour of sim time at a fixed location, qaState().clouds.hash is continuous (hash evolves but never loops/repeats on a short watch). No pop-in/pop-out clusters.
- **No new regressions:** `tests/smoke.html` passes all characterization tests (31/31). If the test count changes, it is because a new assertion was added to verify the extraction, not because an existing assertion broke.
- **applyCloudState function exists and is exported:** The function applyCloudState(A) is defined at the top level (not nested inside render or paint). It is callable as a standalone function (for future testing/debugging, though not required to be used outside render). Signature: function applyCloudState(A) { /* side-effect: mutates cloudState and _cloudDirty */ }.
- **Documentation:** The extraction includes a clear comment block in render() or paint() (depending on call site choice) explaining: (1) why cloudState mutation is a side effect (it advances animation state, not just CSS), (2) the ease/snap continuity invariant (first-snap, then-ease), (3) the ADVANCING fast-forward override (snaps instantly). This comment is the reference for future maintainers.
- **Line-by-line correctness:** All 11 lines of the cloudState block (1658-1669) are preserved byte-for-byte in applyCloudState, with no reordering or reformatting that could change semantics (e.g., the ce=ADVANCING?1:0.08 line must not be touched; the CS.sunUp calculation must not be simplified).

## Rollback
If clouds become visibly discontinuous (popping/sliding/freezing) or drift/advection appears broken, revert the function extraction and inline the cloudState block back into paint() at lines 1658-1669. The feature is optional polish; no user-facing feature depends on it. Rollback is a Git revert of the one commit; no data loss or state corruption. If the rollback is needed, the root cause (usually a scope/ordering error in applyCloudState or the call site) should be diagnosed before re-attempting the extraction.

## Dependencies / notes
- The 2026-06-16 pass is already APPLIED (tone-map lifted, moonSky ordering guard in place, overcast tweaks done, reduced-motion unified). This plan is the final optional-polish SRP item listed in ARCHITECTURE.md's "Deferred follow-ups"; it depends on those being complete but not on any other outstanding plan.

## Open questions
- **Call site design decision:** Option A (render() orchestration) or Option B (paint() subsection)? Option A is architecturally cleaner (render = state setup + render) but requires inlining applyTheme. Option B is a minimal edit but leaves paint() impure. Recommendation: **Option A**, executed as `const A=atmosphere(M); applyCloudState(A); paint(A);` to replace the current `applyTheme(M)` call in render(). If this regresses, Option B is a known fallback.
- **Should applyCloudState be exposed for testing?** Currently, all QA state comes from qaState(), which reads cloudState indirectly. If a future test needs to inspect cloudState directly, applyCloudState should be a top-level function (not a closure). Recommendation: define it at the top level for debuggability, even if not exported.
- **Is the 0.08 ease constant correct, or should it be calibrated?** The 15-20 frame ramp (ce=0.08, so Δ ≈ 0.08 per frame) was set to be "perceptible" over 15-60s real-time. Verify against observer feedback or a video slow-motion watch before finalizing. Recommendation: post-extraction, capture before/after video and confirm timing _feels_ identical.
- **Is there value in memoizing cloudState between render ticks?** Currently, cloudState is updated every frame even if nothing has changed (A values are the same). A minor optimization would be to check if A.cloudLayerLow/Mid/High differ from CS.tgtLow/Mid/High before updating. Recommendation: NOT worth it; the update cost is trivial. Keep the current eager-update logic for simplicity.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. 1. **Verify all applyTheme call-sites**: Before extracting, audit the codebase to confirm applyTheme(M) is called ONLY from render() line 1815. If it is called elsewhere, either (a) redefine applyTheme to delegate to the new call pattern, or (b) update all call-sites. DO NOT commit a change where atmosphere() is computed twice per frame.
2. 2. **Document moon-ordering invariant explicitly**: Add a comment block in render() that makes EXPLICIT the temporal dependency: 'renderMoon() MUST run before applyCloudState()/atmosphere()/paint(). If this order changes, the moonSky._min staleness check will silently fail (it only detects delays in atmosphere, not in applyCloudState).' Link this comment to the staleness-check line 1814.
3. 3. **Add day-rollover invalidation of _cloudReady (separate commit or note)**: The plan assumes _cloudReady correctly gates the snap-vs-ease logic. However, _cloudReady is never reset on day rollover. This causes clouds to EASE instead of snap on day 2+. This is a PRE-EXISTING BUG that extraction will NOT fix. The plan should either (a) fix it as a separate commit before extracting applyCloudState, or (b) explicitly document it as 'KNOWN ISSUE: _cloudReady not reset on rollover; will be fixed in follow-up'. Do NOT extract without addressing this.
4. 4. **Provide a pre-commit QA script, not just observational smoke tests**: The plan lists visual smoke tests (watching clouds for 15 min). Instead, add a concrete ?qa=1 check that can be SCRIPTED: (a) Set ?timeScale=60, ?simWx=20 (clear), then ?simWx=95 (overcast) at t=0. Snapshot qaState().cloudState.covLow at t=0, t=100ms (should be ~0.05 snapped), then t=500ms (should ease toward target). (b) Repeat at ADVANCING=false (normal real-time). Compare before/after hashes. If any regression, fail the smoke test before merge.
5. 5. **Clarify Option A vs B decision**: The plan RECOMMENDS Option A (call from render()) but does NOT make a DECISION. State clearly: 'CHOSEN: Option A (call from render() before applyTheme). Rationale: render() becomes the orchestrator of all state-mutation steps (renderMoon, applyCloudState, then paint), making the side-effect boundary explicit.' OR defer the choice to the implementer with explicit trade-off: 'Option A: clearer orchestration, but inlines applyTheme and requires audit of all call-sites. Option B: minimal change, but leaves paint() impure. Recommendation: Option A, pending call-site audit.' Implement the decision, do NOT leave it as future-work guesswork.
6. 6. **Strengthen acceptance criterion 4 (Painting order)**: Rewrite as: 'No code path calls paint(A) directly except from the main render() result. All render() code that writes DOM for the sky follows this sequence: 1) renderMoon(), 2) applyCloudState(A), 3) paint(A) where A comes from a SINGLE atmosphere(M) call. Verify by grep for all paint( calls in the codebase and confirm none are outside render().'
7. 7. **Document ADVANCING scope dependency**: Add a comment above applyCloudState(A): '/* READS global ADVANCING (fast-forward gate, line 546). If ADVANCING is refactored to be a parameter, this function signature MUST be updated. */' This prevents silent breakage if atmosphere is refactored to take ADVANCING as a parameter.

**Missing risks the spec omitted:**
- **Double atmosphere() compute (Option A)**: The plan proposes calling `const A=atmosphere(M); applyCloudState(A); paint(A);` to replace `applyTheme(M)`. However, `applyTheme(M)` is defined as `function applyTheme(M){ paint(atmosphere(M)); }` (line 1704). If the extraction moves applyCloudState to render() with inline unrolling, the call sequence becomes atmosphere→applyCloudState→paint. But if later code path or a legacy call still invokes `applyTheme(M)`, atmosphere will be computed TWICE per frame (inefficient, and semantically wrong if M changes between calls). The plan must verify that ALL call-sites of the old applyTheme(M) are rewritten, or applyTheme must be redefined to NOT recompute atmosphere.
- **Moon geometry staleness coupling**: render() has a one-shot staleness warning (line 1814) that checks `moonSky._min !== mm` after the renderMoon block. This is a TEMPORAL DEPENDENCY: renderMoon() MUST run before atmosphere()/applyTheme(). If applyCloudState(A) is inserted into render() before applyTheme, and if applyCloudState reads from A (which comes from atmosphere), then the call order MUST be: renderMoon → [applyCloudState] → applyTheme. The plan states this but does NOT verify that the inlined call `const A=atmosphere(M); applyCloudState(A); paint(A);` preserves the renderMoon→atmosphere ordering. A future maintainer could easily reorder these lines and silently break the invariant without hitting the staleness warning (because the warning only checks paint, not applyCloudState).
- **ADVANCING not captured**: The plan extracts applyCloudState(A) as a top-level function. Line 1664 reads `const ce=ADVANCING?1:0.08;` — ADVANCING is a global const (line 546). When applyCloudState is extracted, it will still reference the global ADVANCING, which is correct. BUT the plan does NOT document this dependency; a future refactor that scopes ADVANCING locally (e.g., passing it as a parameter to atmosphere) would silently break applyCloudState if the parameter is not threaded through.
- **_cloudReady flag state not invalidated on new day**: _cloudReady is set to true on first cloud appearance (line 1663). If a user views the widget for 24h, the day rolls over (new day, new location seed per line 1344), but _cloudReady remains true. On the new day, clouds will EASE instead of snap the first time they appear, violating the 'establish the deck promptly' contract. The plan does NOT mention day-rollover invalidation of _cloudReady, and the current paint() code ALSO has this bug. Extracting the code will not FIX it, but the plan should AT LEAST flag it as a pre-existing issue to be addressed separately.

**Weak acceptance criteria (a broken change could still pass):**
- **Acceptance criterion 1 (Cloud continuity)**: The criterion states 'Ease-vs-snap branching is byte-identical after extraction' and 'covLow at real-time should increase by ce*(tgtLow-covLow)≈0.08*Δ per frame'. But this only tests the MATH, not the SEMANTICS. If applyCloudState is called at the WRONG time in render() (e.g., after applyTheme instead of before), the test will PASS (the easing formula is still byte-identical) but the clouds will behave wrongly (stale A values, or out-of-order atmosphere writes). A stronger test would be: 'A.cloudLayerLow equals cloudState.tgtLow within 1 frame after applyCloudState is called, when ADVANCING=false. At ADVANCING=true, A.cloudLayerLow equals cloudState.covLow immediately after applyCloudState.'
- **Acceptance criterion 4 (Painting order)**: States 'applyCloudState(A=atmosphere(M)); paint(A) order is preserved'. But this doesn't PREVENT a bug: if a legacy call to `applyTheme(M)` still exists somewhere, it will call `paint(atmosphere(M))` AGAIN, and applyCloudState will not have run, so paintClouds will render stale cloudState. The test should explicitly verify: 'No function calls paint(A) directly; all render-path DOM writes go through paint(A) where A comes from the same atmosphere(M) call that fed applyCloudState(A).' This is not in the criteria.
- **Acceptance criterion 8 (applyCloudState function export)**: States the function 'is callable as a standalone function (for future testing/debugging, though not required to be used outside render)'. But if applyCloudState is only called from render() and never tested standalone, a future maintainer might not realize it REQUIRES A to be fresh (not stale from a previous render). The criterion should add: 'If tests call applyCloudState() directly, they MUST verify that cloudState mutations match the A parameter (no lag, no stale reads from a previous A).'
- **Smoke test A, item 3**: States 'QA readout (?qa=1): confirm cloudLayerLow/Mid/High values in atmosphere match cloudState.tgtLow/Mid/High after a paint cycle.' But this is a TIMING-INSENSITIVE test — it will pass whether applyCloudState runs before or after atmosphere. The test should specify: 'WITHIN paint(A), BEFORE any CSS write, cloudState.tgtLow/Mid/High have been updated from A.cloudLayerLow/Mid/High. AFTER paint(A) returns, cloudState.tgtLow matches A.cloudLayerLow exactly.' This tightens the coupling check.

**Scope concerns:**
- **Over-engineering: optional polish status**: The plan is explicitly marked as 'optional polish' in ARCHITECTURE.md (deferred follow-up, not blocking). The extraction is a SRP cleanups — paint() is 'impure' in a well-isolated block (11 lines out of ~100). Extracting it reduces technical debt but does NOT fix a bug or add a feature. Given the time cost (test harness, regression risk), it may not be worth doing unless the plan includes a strong maintenance/readability payoff. The plan does NOT argue WHY this extraction is better than the current 'isolated-but-inline' code (e.g., cleaner call graph? easier to mock in tests? less coupling to atmosphere's TDZ?).
- **Inlining applyTheme without strong justification**: The proposed Option A inlines applyTheme(M) into `const A=atmosphere(M); applyCloudState(A); paint(A);`. This changes the abstraction: render() now knows the internal structure of applyTheme (atmosphere→paint). If future changes need to inject a step between atmosphere and paint (e.g., a cache-invalidation or a debug hook), the inlining will make it harder to add without duplicating logic. The plan should justify this trade-off explicitly: does readability of render() outweigh the loss of applyTheme as a clear boundary?
- **No fallback plan if Option A regresses**: The plan mentions 'If Option A regresses, Option B is a known fallback' — but the regression window is the TIME BETWEEN commit and detection. If clouds appear frozen/easing during fast-forward for an hour before a user reports it, the bug is subtle. The plan should recommend a SMOKE TEST that runs BEFORE commit (e.g., ?qa=1 snapshot of cloudState easing/snapping at both ADVANCING=true and ADVANCING=false), not just 'watch for 15 min and see if it feels right'.

**Grounding issues (claims to re-check against current code):**
_(none)_

**Reviewer notes:** **Summary**: The plan is SOUND in concept and correctly identifies the 11-line cloudState block as a render-layer side effect that should logically be separated from CSS writes. The code anchors are ACCURATE, the regression risks are MOSTLY IDENTIFIED, and the Option A approach is architecturally clean. HOWEVER, the plan has THREE CRITICAL GAPS that MUST be fixed before implementation:

1. **Double-compute trap**: Option A inlines applyTheme, risking atmosphere() being called twice if legacy call-sites are not rewritten. The plan does not require an audit.

2. **Moon ordering silent failure**: If applyCloudState is called in the wrong place within render(), the moon-staleness check won't detect it. The plan underestimates this risk.

3. **Pre-existing _cloudReady bug**: The plan extracts cloudState logic that has a latent day-rollover bug (_cloudReady never resets). Extraction doesn't FIX it, but the plan must AT LEAST flag and defer it.

RequiredFixes #1, #2, #3, and #4 above are BLOCKING. RequiredFixes #5, #6, #7 are STRONGLY RECOMMENDED (architecture clarity, future-proofing, strong testing).

**Recommendation**: APPROVE with conditions. The plan is minimal, justified, and improves SRP. But require the implementer to:
- Audit ALL paint() and applyTheme() call-sites (should be just render())
- Add explicit moon-ordering comments to guard against reordering
- Flag (or fix) the _cloudReady day-rollover issue
- Implement a scripted QA check (not just visual smoke tests)
- Make a FINAL decision between Option A and B, with rationale

If these are addressed, the extraction is LOW RISK and good debt cleanup.
