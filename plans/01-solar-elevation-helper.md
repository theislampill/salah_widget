# Plan 01 — Shared solar-elevation helper (de-duplicate drawArc / sunAltAt math)

> **Status:** ✅ DONE (2026-06-16) — **pure extraction** (resolved the critique's "pixel-identical vs ±0.01°" contradiction by demanding the strictest bound: **bit-identical**). New `solarElevationDeg(M,a)` holds the math verbatim (recomputes `dayLen`/`polar`/`noonT`, keeps the 27.5° clamp, the `cl` clamp lives inside it, returns raw degrees); `sunAltAt` is now a thin alias; `drawArc`'s `elevDeg` calls it (keeping `polar`/`noonT` which it uses elsewhere). Verified by hashing `drawArc(model())` + a 0–1440/15-min `sunAltAt` grid **before vs after** across three paths — Madinah (refinement-active, near-solstice), Singapore (phi≈0, refinement-skipped), Tromsø (polar/midnight-sun): all six hashes **exactly equal**. 28/28 smoke; `atmosphere` ok.  ·  **Class:** correctness  ·  **Priority:** P1  ·  **Effort:** M  ·  **Risk:** med
> **Do now?** Yes — recommended soon  ·  **Plan-review verdict:** `needs-fixes` (10 required fixes — see end)  ·  **Depends on:** none
>
> Read-only plan from `/implementaudit` (workflow `wf_f498de17-f7b`, investigate → adversarial critique). Grounded against `index.html` @ commit `91d0fc1` (~1951 lines). **No source was changed.** Line numbers drift — re-verify the anchors before editing.

## Problem
The solar-elevation math is duplicated verbatim in two places: drawArc (lines 1040-1047) and sunAltAt (lines 1166-1174). Both compute the same refined declination, hour angle, and elevation formula. This duplication is a **documented drift surface** — the two functions are explicitly documented to "MUST match exactly" (comments at 1164-1165, 1043-1044). A real bug already happened: sunAltAt's declination clamp was 24° while drawArc's was 27.5°, causing the sky-physics elevation to diverge from the rendered arc near solstice, breaking the invariant "sunrise glow must fire when the arc's sunrise dot is on the horizon". It was manually fixed, but the root cause (duplicated code) remains.

## Root cause
No shared helper function for the solar-elevation math. Two independent copies of the hour-angle formula + declination-refinement logic means future edits will silently diverge. The 24°/27.5° clamp mismatch was a manual synchronization failure.

## Current behavior
- drawArc(M) computes elevation at line 1047: `Math.asin(cl(Math.sin(phi)*Math.sin(decl)+Math.cos(phi)*Math.cos(decl)*Math.cos(Hof(a)*DEG)))/DEG`, with refined declination at lines 1041-1044 and hour angle Hof at line 1045. All inputs (phi, M.sunset, M.sunrise, M.noon, noonT calculation) are derived locally.
- sunAltAt(M, a) computes elevation at line 1174 with identical formula, derivation order, clamping logic, and constants (27.5° clamp at line 1171).
- sunMetrics(M) calls sunAltAt(M, M.nowAbs) to get current altitude; physSky and atmosphere then consume the result.
- No single source of truth; the comment at line 1164 is the only human contract.

## Desired behavior
Create a single shared helper `solarElevationDeg(M, atTime)` that encapsulates the full solar-elevation pipeline: polar-day detection, noon-transit calculation, declination refinement with the 27.5° clamp, hour-angle conversion, and the final elevation formula. Both drawArc and sunAltAt call this helper. The arc is "sacrosanct" — the refactor is valid ONLY if every rendered pixel (SVG path, prayer-marker positions, eye-of-needle) remains pixel-identical before vs after, and the sky colours/optics (sunMetrics output) are numerically identical to <0.1° elevation error at all times.

## Code anchors (re-verify line numbers before editing)
**`index.html:1027-1077 (drawArc)`**
The elevation computation is 40 lines into drawArc; the key math lives in the const declarations for DEG, phi, dayLen, polar, noonT, decl refinement, Hof, cl, and elevDeg.

````js
function drawArc(M){...const DEG=Math.PI/180, phi=(+(q.get("lat"))||0)*DEG;...const dayLen=M.sunset-M.sunrise, polar=dayLen<30||dayLen>1410;...const noonT=polar?M.noon:(M.sunrise+M.sunset)/2;...let decl=M.decl;...const HsrDeg=((M.sunset-M.sunrise)/2)*0.25, tp=Math.tan(phi);...if(!polar && Math.abs(tp)>0.05){ const d=Math.atan(-Math.cos(HsrDeg*DEG)/tp);...if(isFinite(d)&&Math.abs(d)<27.5*DEG) decl=d; }...const Hof=a=>(a-noonT)*0.25;...const cl=x=>x<-1?-1:x>1?1:x;...const elevDeg=a=>Math.asin(cl(Math.sin(phi)*Math.sin(decl)+Math.cos(phi)*Math.cos(decl)*Math.cos(Hof(a)*DEG)))/DEG;
````

**`index.html:1163-1175 (sunAltAt + sunMetrics)`**
Identical constants and formula to drawArc. The only difference: sunAltAt is parameterized on `a` (time), while drawArc defines elevDeg as a closure.

````js
function sunAltAt(M,a){...const DEG=Math.PI/180, phi=(+(q.get("lat"))||0)*DEG;...const dayLen=M.sunset-M.sunrise, polar=dayLen<30||dayLen>1410;...const noonT=polar?M.noon:(M.sunrise+M.sunset)/2;...let decl=M.decl;...const HsrDeg=((M.sunset-M.sunrise)/2)*0.25, tp=Math.tan(phi);...if(!polar && Math.abs(tp)>0.05){ const d=Math.atan(-Math.cos(HsrDeg*DEG)/tp); if(isFinite(d)&&Math.abs(d)<27.5*DEG) decl=d; }...const Hof=(a-noonT)*0.25;...const cl=x=>x<-1?-1:x>1?1:x;...return Math.asin(cl(Math.sin(phi)*Math.sin(decl)+Math.cos(phi)*Math.cos(decl)*Math.cos(Hof*DEG)))/DEG;}
````

**`index.html:1176-1181 (sunMetrics)`**
Sole consumer of sunAltAt outside drawArc. Used by physSky to drive sky colour + optics.

````js
function sunMetrics(M){...const altDeg=sunAltAt(M,a);...const altN=Math.max(-1,Math.min(1,altDeg/46));...return { x:6+(a-start)/1440*88, y:60-Math.max(0,altN)*44, altN, altDeg };
````

**`index.html:1198-1223 (physSky)`**
Consumes sunMetrics result; drives all sky-colour physics from the altitude. A 0.1° drift would shift the warm glow, stars, and accent colours.

````js
function physSky(M, sm){...const e=sm.altDeg;...const lum=skyLum(e);...const warm=clamp((e+12)/11)*(1-clamp((e-1)/9));
````

## Approach
1. **Extract the shared helper** (inline, no new file): create `solarElevationDeg(M, atTime)` that returns one number (degrees, -90 to +90, without clamping to allow negative angles for nighttime). The function body absorbs lines ~1040-1047 (or 1166-1174) exactly, with `a=atTime` substituted for the closure parameter.

2. **Signature and placement**: Define the helper immediately after `sunMetrics` (around line 1182), before `skyLum`. This keeps it near the callers (drawArc needs it as a closure factory, sunAltAt returns it directly, physSky reads the result).

3. **Update drawArc** (line 1027): Replace lines 1040-1047 with a single call to the helper. Since drawArc needs `elevDeg` as a closure `elevDeg(a)`, wrap it: `const elevDeg=a=>solarElevationDeg(M,a)`. This guarantees every call inside drawArc uses the same formula.

4. **Update sunAltAt** (line 1163): Replace the entire function body (lines 1166-1174) with a direct return: `return solarElevationDeg(M,a);`. This shrinks the function to a one-liner.

5. **Characterization (CRITICAL)**: Before claiming the refactor is valid, run the full SVG arc through the before-and-after code side-by-side using a deterministic scene (e.g., Madinah at noon, a Ramadan date with ~12h daylen, a polar-day scene). Pixel-by-pixel comparison of the rendered path, prayer-dot positions, and eye-of-needle placement. The Catmull-Rom curve and spline arc-length calculations in drawArc must produce identical cumulative chord lengths. Run sunMetrics on a grid of times (every 30 min over 24h) and confirm altDeg matches to <0.01°. If either diverges, the helper has a subtle bug or rounding error.

6. **Regression gates**: Run tests/smoke.html (weather-truthfulness, moon, dawn) to confirm no sky-colour regressions. Spot-check qaState().render with the live widget over a 30s real-time window (no simTime to freeze the clock) and compare rAF counts, motion telemetry, and sky colours before/after.

7. **Update comments**: Leave the "MUST match" comment intact at sunAltAt (now a one-liner, so the comment's message is even more important). Add a note above the helper explaining why it exists (the 24°/27.5° bug history and the immutability invariant).

## Alternatives considered (and rejected)
- **Create a parameter-driven drawArc variant that accepts an elevation callback, avoiding code duplication at the function-call level** — Over-engineering. The refactor goal is to **prevent drift**, not to abstraction-layer the entire arc pipeline. A helper focused narrowly on the elevation formula is simpler, easier to review, and leaves drawArc's spline/tanh/bisection logic untouched (those are arc-specific and correct as-is).
- **Inline the helper logic directly at every call site (no separate function, just ensure identical copies)** — Defeats the purpose. The bug happened *because* identical copies diverged (24° vs 27.5° clamp). A shared function is the only way to guarantee future edits stay in sync.
- **Create a high-level 'SolarState' object computed once per tick (M.sun = {elevation, azimuth, ...}) so all consumers share one ref** — Scope creep. The task is to de-duplicate elevation math, not to refactor the model/state flow. Adding a new object changes the atmosphere/paint contracts and risks introducing new drift surfaces in azimuth or time-basis.
- **Move the helper to a separate `<script>` block or external file** — Breaks the static/no-build constraint. The widget is one self-contained inline HTML file; splitting it violates the core design principle.

## Owner / source touchpoints
- index.html:1040-1047 (drawArc: replace lines, keep closure wrapper)
- index.html:1163-1175 (sunAltAt: replace body with one-liner return)
- index.html:~1182 (new location for solarElevationDeg helper definition)
- index.html:1043-1044, 1171 (update comments if clarification is needed, but do NOT change the 27.5° clamp value)

## Regression risks (forbidden-regression guardrails)
- **Arc pixel-drift (CRITICAL)**: Any rounding difference (e.g., a different order of operations in the helper vs the original closures) will shift the Catmull-Rom curve's control points and misalign the prayer dots. The eye-of-needle ring must thread the path at the exact same cumulative arc-length. Verify with a pixel-level screenshot comparison.
- **Sky-colour shift**: If the helper's elevation differs from sunAltAt's output by >0.1°, skyLum will step through the twilight bands (civil→nautical→astronomical) at the wrong time, causing the Belt of Venus, warm glow, and stars to appear/disappear at the wrong moment (test against AGENTS.md gate F: 'dawn is honest').
- **Dhuhr dot mispositioning (AGENTS.md gate)**: The dot is held past the apex (noonT+11, line 1122). If the helper breaks the noonT calculation, the apex position drifts and the dot sits on the apex instead of past it (instant FAIL under gate M98-99).
- **Closure variable capture in drawArc**: If solarElevationDeg closes over the wrong variables (e.g., a stale `phi` or `decl`), the arc will distort for non-Madinah latitudes. Test at lat=0 (equator, phi=0) and lat=70 (high-latitude summer, polar day).
- **Hour-angle basis mismatch**: If the helper's `Hof` calculation differs from drawArc's closure version (e.g., using a different time reference), the entire arc will shift left/right. The 'now' insertion (line 1084-1085) depends on consistent Hof timing.
- **Polar-day logic divergence (AGENTS.md forbidden regression)**: If the polar flag or noonT calculation changes, polar-night/midnight-sun days will render with the wrong shape (ALT branching at line 1054-1076 expects correct noonT). Test with `&simTime=01:00` near the Arctic Circle.

## Smoke A — capture BEFORE any change
- Render the widget at Madinah (lat=24.47, lon=39.61) at Dhuhr (noon) on a spring-equinox date (e.g., simTime=12:30) and screenshot the arc + prayer dots.
- Take a crop of the eye-of-needle ring and its tangent line (should thread the path with no gap).
- Log `window.qaState().render.currentKey` and `window.qaState().render.sunAltDeg` at 15-minute intervals (04:00, 04:30, ..., 20:00) and record the altitude progression.
- Render qaState().sunMetrics values (x, y, altDeg) at M.nowAbs over a 12-hour span and plot them (should be a smooth 1D curve).
- Take a full screenshot of the sky at sunrise (simTime=05:50) and record the sky colours (--g1, --g2, --g3, --accent) from the CSS custom props.
- Screenshot the widget with `&qa=1` to capture qaState() output.
- Take a high-zoom crop of the Dhuhr dot position relative to the apex (it should sit visibly PAST the peak, not on it).

## Smoke B — verify AFTER the change
- Render the widget after the refactor at the same Madinah scene and compare the arc path (SVG d= attribute) byte-for-byte (or pixel-identical rendering).
- Verify the eye-of-needle ring threads the path with zero divergence (measure the distance from ring center to nearest path point; should be <0.1px).
- Replay the sunMetrics log from smokeA: run the same 15-minute grid and confirm altDeg values match to within ±0.01°.
- Re-plot sunMetrics x/y over the same 12-hour span and overlay it on the original plot; the curves should be indistinguishable.
- Screenshot the sky at sunrise and diff the CSS custom props (--g1, --g2, etc.) against smokeA; they must match or differ by <1 unit per RGB channel (tolerance for rounding error).
- Run tests/smoke.html and confirm: all PASS counts match or increase (no new FAILs).
- Screenshot the Dhuhr dot and confirm it sits at the same position relative to the apex as before.
- Load the widget without simTime and watch the live clock for 30 seconds; confirm cloud drift, star twinkle, and sky breathing are visible (no frozen motion) and match the before refactor behavior.
- Compare render telemetry: `qaState().render.fps`, `qaState().render.cloudsPaintRate`, and motion timing should be unchanged.

## Acceptance criteria (falsifiable)
- The arc SVG path (line 1147, the d attribute) is pixel-identical before and after the refactor when rendered in the same browser at the same screen resolution (test at 1x scale).
- sunMetrics(M).altDeg at M.nowAbs matches its pre-refactor value to within ±0.01° for all times of day on 5 diverse test dates (equinox, solstice, Ramadan, polar day, polar night).
- Prayer-dot positions (cx, cy in the SVG, computed via X(pabs) and Y(pabs)) are identical before and after (within ±0.1px) for all six prayer markers (Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha).
- Eye-of-needle ring (lines 1130-1137) threads the path at the identical cumulative arc-length before and after (within ±0.5px along the path).
- Sky custom props (--g1, --g2, --g3, --accent, --accent2, --glow, --hor) recorded from physSky output match their pre-refactor values to within ±2 RGB units at sunrise, noon, sunset, and Fajr-time on a standard day.
- The Dhuhr dot sits visibly past the arc apex (never on it) — verify with a crop showing the dot clearly offset from the peak.
- tests/smoke.html passes all weather/moon/dawn assertions; no new FAILs or SKIPs introduced by the refactor.
- Live real-time widget animates (clouds drift, stars twinkle) visibly over 15–60s, matching pre-refactor motion rates (verified with `?debugMotion=1` or a real clock).
- Code diff is minimal: solarElevationDeg definition (~8 lines), drawArc elevation-math replacement (1 line), sunAltAt body replacement (1 line). No other changes to logic or variable names.

## Rollback
If any acceptance criterion fails:
1. Revert the helper definition and the two call sites to their original duplicated form.
2. Re-run smokeB tests to confirm the original behavior is restored.
3. Document what went wrong (e.g., "rounding in Math.asin differs slightly when called twice vs once", "phi capture was stale") so the next attempt avoids it.
4. Do NOT attempt a second refactor without understanding the root cause of the first failure (it is likely a subtle floating-point or scope issue, not a logic bug).

## Dependencies / sequencing
_(none)_

## Open questions
- Should the helper return raw elevation (which can be <-90° for nighttime) or clamp it to [-90, 90]? Currently both drawArc and sunAltAt avoid explicit clamping; the `cl` clamp only applies to the asin argument, not the result. The helper should return raw degrees to preserve nighttime information for physSky (which uses negative elevations for twilight and night logic). Confirm with OPTICS.md if negative elevations are ever used downstream.
- Does the 27.5° clamp on declination refinement need any documentation update? The current comment (line 1044, 1171) explains the rationale (absorbs refraction) but a one-line helper definition might warrant a secondary note explaining why the clamp matters (near-solstice fit). Defer until code review, but mention it now.
- Will the helper be called millions of times per frame (drawArc calls elevDeg ~360 times per arc sample)? If so, is function-call overhead a concern, or should it be inlined as a macro-like expression? Given JS engines' inlining and JIT, probably not an issue, but measure if performance regression is suspected.
- Should the helper validate its inputs (M.sunset >= M.sunrise, a in a reasonable range) or fail silently (current behavior)? Current code has no guards; the helper should inherit that. Do NOT add validation unless a real-world bug case is known.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. CRITICAL: Clarify helper signature and document ALL intermediate calculations it performs. Current spec says 'absorbs lines ~1040-1047' but omits that it must ALSO recompute dayLen, polar, noonT from M. Proposed signature: `function solarElevationDeg(M, atTime){ /* recompute dayLen, polar, noonT, then apply lines 1040-1047 logic */ }`
2. CRITICAL: Define whether floating-point tolerance is ±0.01° (sunMetrics.altDeg) or ±0.1° (pixel-drift acceptable) or ±0.5px (Catmull-Rom curve tolerance). Current spec contradicts itself. Recommend: Accept ±0.1° elevation error OR pixel-mismatch up to ±1px along the arc path, NOT ±0.01° with pixel-identical demand.
3. CRITICAL: Specify how the extracted helper will handle the `cl` (clamp) function — will it be defined inside the helper (tiny overhead) or inlined into the asin expression? Current spec is ambiguous.
4. Add explicit test case for POLAR DAYS (dayLen<30 or dayLen>1410) to verify the helper's `polar` flag matches drawArc's. Test should cover Arctic summer (dayLen~1440, polar=true) and Antarctic night (dayLen~0, polar=true).
5. Add explicit verification step: Call sunMetrics(M) 144 times (every 10-min interval over 24h) BEFORE refactor and log altDeg array. After refactor, replay and diff. Use automated tolerance check (fail if any diff > 0.05°), not manual screenshot comparison.
6. Modify smokeA step 2 ('Take a crop of the eye-of-needle ring'): Add measurement instruction — 'Distance from ring center to nearest arc path point must be <0.2px before refactor; record this number as baseline.'  SmokeB step 2 repeats measurement and compares baseline vs post-refactor.
7. Modify smokeB step 3 ('Verify eye-of-needle...within ±0.5px'): Change to 'within ±0.5px of PRE-REFACTOR baseline' — this removes ambiguity about what 'correct' means.
8. Explicitly add to acceptance criteria: 'The helper solarElevationDeg(M, atTime) is called from drawArc as `elevDeg=a=>solarElevationDeg(M,a)` and from sunAltAt as `return solarElevationDeg(M,a)` — no other elevation formulas exist in the file after refactor.' (Prevents accidental duplication.)
9. Document the open question about negative elevations: If physSky uses negative altDeg for twilight/night logic, confirm the helper returns raw degrees without output clamping (the current code only clamps the asin argument, not the result). Add a comment: `// Returns raw degrees [-90,+90]; negative = below horizon / twilight / night. Do NOT clamp output.`
10. Add a rollback instruction detail: If the refactor causes any pixel drift OR any smoke test FAIL, the agent MUST log the exact diff (e.g., 'elevDeg(M.noon) before=45.3142°, after=45.3156° → arc Y shift ±0.5px') before reverting. This diagnostic is critical for understanding floating-point sensitivity.

**Missing risks the spec omitted:**
- FLOATING-POINT ROUNDING: Order of operations in extracted helper vs closure (e.g., (a-noonT)*0.25 computed once vs computed twice with different FPU state) may produce ±0.001–0.01° elevation error, shifting the arc's SVG path pixels — contradicts acceptance criterion 'pixel-identical'.
- POLAR-FLAG EDGE CASE: If M.sunrise and M.sunset have rounding that causes one code path to compute dayLen=30.001 (polar=true) and another to compute dayLen=29.999 (polar=false), the ALT branch will mismatch, distorting the arc. No guard against this.
- DHUHR DOT MISPOSITIONING: The dot is held at noonT+11 (line 1122, not shown in anchors). Spec does not verify that helper's noonT matches drawArc's noonT exactly — any difference breaks the dot position regression gate.
- MOTION TIMING / PERFORMANCE: drawArc calls elevDeg ~360 times per frame. Extracting a function may increase call stack depth or GC pressure; no performance profile required by spec.
- CL FUNCTION REDEFINITION: Both drawArc and sunAltAt define local `cl` clamp. If extracted into helper, `cl` is defined once but reused; if inlined into helper, code duplication remains. Spec does not clarify which.
- SMOKE TEST GAP: The spec's smokeA/smokeB lists 'Render the widget after refactor' but does not explicitly state that the arc must be re-rendered in the EXACT SAME ENGINE — it only says pixel-identical. No verification that drawArc's other logic (Catmull-Rom, spline arc-length, cumulative chord, dash-reveal) is unaffected.
- ACCEPTANCE CRITERION CONTRADICTION: 'Arc SVG path pixel-identical' vs 'sunMetrics.altDeg within ±0.01°' are contradictory — 0.01° elevation error translates to ~0.5–1px Y shift on a 180px canvas.

**Weak acceptance criteria (a broken change could still pass):**
- Acceptance criterion 'arc SVG path pixel-identical' could pass if the SVG d attribute happens to round to the same integer-pixel coordinates despite 0.01° elevation drift (sub-pixel differences masked by rasterization).
- Smoke test 'eye-of-needle ring threads the path within ±0.5px' could pass if ring-path distance remains <0.5px despite 0.01° elevation error (tolerance is coarse for a visual regression test).
- Prayer-dot position criterion 'identical before and after (within ±0.1px)' could pass if the dot's computed X and Y round to the same screen pixels, masking sub-pixel elevation drift.
- Sky-color criterion 'RGB units match within ±2' could pass if physSky's quantization (integer RGB channels) masks a 0.01–0.1° altitude error that would shift twilight zones by <1 unit per channel.
- The criterion 'tests/smoke.html passes all assertions' is NOT called out in the plan's acceptance list but mentioned in smokeB — if a test runs but crashes, it would FAIL the prior criteria but might not be in the explicit PASS gate.
- Live-motion visual inspection criterion ('clouds drift, stars twinkle') is entirely subjective — no threshold defined for 'clearly visible' motion, so a refactor that halves frame-rate might still appear to 'animate' to human eye.

**Scope concerns:**
- Plan respects the single-file / no-build constraint — helper is inline, no new files. Correct.
- Plan explicitly avoids scope creep ('not to abstraction-layer the entire arc pipeline') — helper is narrow (elevation only). Correct.
- However, plan does NOT characterize or guard the Catmull-Rom + spline arc-length logic (lines 1087–1130 in drawArc) — if the extracted helper produces even 0.001° elevation error, the cumulative chord-length calculations will drift, misaligning the dash-reveal and eye-of-needle ring. The plan assumes drawArc's non-elevation logic is untouched and correct, but provides no verification mechanism for the spline geometry.
- Plan forbids broader refactors (correct) but the helper extraction IS a refactor of the core physics — the 'sacrosanct arc' constraint applies strictly. Spec does not define what 'pixel-identical' tolerance actually means for Catmull-Rom curves (e.g., is ±1px acceptable? The spec says 0px).

**Grounding issues (claims to re-check against current code):**
- Plan correctly identifies line numbers (1027 drawArc, 1040-1047 elevation math, 1163 sunAltAt, 1174 return, 1176 sunMetrics) — these match the current 1951-line file.
- Both declination clamps are already synchronized at 27.5° (lines 1044 and 1171), confirming the historical 24°/27.5° drift mentioned in the plan is already fixed.
- Plan spec correctly notes that polar/noonT are prerequisites (lines 1035-1036 in drawArc and 1167-1168 in sunAltAt) but underspecifies that the helper MUST recompute these from M, not import them from closure.

**Reviewer notes:** The plan is sound in intent but has three specific hazards: (1) it demands 'pixel-identical' rendering alongside allowing ±0.01° elevation drift (physically incompatible), (2) it underspecifies the helper's inputs/outputs and how it recomputes prerequisites, and (3) it lacks a concrete floating-point rounding tolerance and a measurement-based verification step for the arc geometry. The acceptance criteria are written at too high a level (qualitative 'snapshot' comparisons) rather than quantitative (altDeg array diff, ring-to-path distance baseline, spline-geometry hash). Fixing these requires: (a) explicit tolerance values (e.g., ±0.1° elevation, ±1px arc path), (b) numerical verification (sunMetrics grid + automated diff checker), and (c) baseline measurement before refactor + delta-from-baseline after. Without these, a broken implementation could pass 'eyeball' gates. The refactor itself is justified and minimal (no scope creep, no new files), but its verification is underspecified.
