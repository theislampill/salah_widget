# Plan 02 — Lift corner-sun tone-mapping out of paint() into atmosphere()

> **Status:** ✅ DONE (2026-06-16) — **pure move** of the tone-map math (Kasten–Young airmass + Beer–Lambert + per-class cloud transmittance + CCT blackbody → ACES) from `paint()` into `atmosphere()`, returned as `sunCoreRGB`/`sunMidRGB` (rgb() strings) + `sunCloudT`; `paint()` now only WRITES them. Inputs `D.haze≡aerosolDensity` / `D.cloud≡cloudCover` make it byte-identical — proven by recomputing the OLD formula inline and matching `A.sunCoreRGB`/`A.sunMidRGB` **and** the actual CSS across 4 branch-distinct scenes (clear-noon hi-CCT, sunrise lo-CCT, overcast, thunder). **Smoke caught a real regression**: paint's `--sunray` still referenced the moved `Tcloud` → threw after `--suncore` but before `--moongrp` (5 night/observability fails); fixed by exposing `sunCloudT` from atmosphere. Final 28/28; nucleus defined, never grey/purple.  ·  **Class:** architecture  ·  **Priority:** P1  ·  **Effort:** M  ·  **Risk:** med
> **Do now?** Yes — recommended soon  ·  **Plan-review verdict:** `needs-fixes` (5 required fixes — see end)  ·  **Depends on:** none
>
> Read-only plan from `/implementaudit` (workflow `wf_f498de17-f7b`, investigate → adversarial critique). Grounded against `index.html` @ commit `91d0fc1` (~1951 lines). **No source was changed.** Line numbers drift — re-verify the anchors before editing.

## Problem
paint() violates the Single Responsibility Principle by performing complex tone-mapping derivation (Kasten-Young airmass, Beer-Lambert transmittance, CCT blackbody, ACES tone-map) inline alongside DOM writes. The render boundary contract states: atmosphere() = pure state vector (touches NO DOM), paint() = ONLY DOM writer. Currently, paint() is both deriving complex optical math AND writing CSS, mixing state calculation with presentation. This tangle (documented in ARCHITECTURE.md §1 as SRP tangle #1) blocks clear reasoning about where state is computed vs. where it is rendered, and makes it harder to test/refactor the tone-mapping math independently from CSS writes.

## Root cause
When the corner-sun tone-mapping math was added (scene-referred → attenuate → tone-map pipeline to fix grey/purple-blob bug), it was inlined in paint() lines 1593–1613 because those intermediate values (eC, m, k, Tbeam, Tcloud, CCT, cLin, aces, tm) were treated as transient display values rather than exposing them as part of the atmosphere state vector. The boundary between state (atmosphere) and presentation (paint) was not re-examined after the math was added, so the responsibility drift was never corrected.

## Current behavior
- paint() computes Kasten-Young airmass (m) from solar elevation and aerosol density.
- paint() computes Beer-Lambert beam transmittance (Tbeam) using airmass and optical depth (k).
- paint() computes per-class cloud transmittance (Tcloud) from weather class or cloud cover.
- paint() derives CCT (colour temperature) from solar elevation (2000K horizon → 5500K noon).
- paint() tone-maps the CCT blackbody colour to a linear HDR radiance, applies ACES curve, and clips.
- paint() writes --suncore and --sunmid (the tone-mapped CSS custom props).
- The result: paint() computes 5+ intermediate optical values and produces 2 final colours — it is a physics engine, not a DOM writer.
- Currently confirmed working: sun nucleus clips to white even through cloud; corona desaturates warm (never grey/purple); sunrise/sunset are warm; noon is white-hot.

## Desired behavior
- atmosphere() derives ALL tone-mapping math (airmass, transmittances, CCT, ACES tone-map) and returns two named fields: sunCoreRGB and sunMidRGB (already tone-mapped [r,g,b] or rgb() strings).
- paint() reads A.sunCoreRGB / A.sunMidRGB from the atmosphere state and writes them to --suncore / --sunmid as simple property assignments.
- atmosphere() respects TDZ (Temporal Dead Zone) ordering: the new tone-map block runs AFTER clLow/clMid/clHigh/ray/cloudSunCol/moonLume are declared (they are inputs to airmass/transmittance logic).
- The cloudState mutation (lines 1653–1663 in current paint) is NOT moved — it is a side effect of rendering, not part of the pure atmosphere state. It remains in paint(), clearly separated from the tone-map, or optionally extracted to a separate applyCloudState() step that paint() calls.
- paint() becomes a thin façade: iterate the atmosphere fields and write them to CSS (no conditional logic, no calculations, no state mutations except cloudState).
- atmosphere() stays pure: no DOM access, no CSS writes, just state derivation.

## Code anchors (re-verify line numbers before editing)
**`paint() lines 1585–1632`**
The entire corner-sun tone-mapping block that must be lifted. Lines 1593–1613 compute the airmass, transmittances, CCT, blackbody colour, and ACES tone-map; lines 1606–1613 write --suncore and --sunmid.

````js
{ const e=A.solarElevationDeg, noon=clamp(e/40), sunAmt=clamp((e+1.5)/7);
    // ——— SOLAR TONE-MAPPING / WHITE-BALANCE (scene-referred radiance → attenuate → ACES → display) ———
    // The OLD code multiplied a display OPACITY by a weather "mute" and mixed the colour toward cold grey
    // (206,208,214) → a dim grey/purple BLOB and a vague soft BRUSH. Correct discipline (deep-research §4):
    // build a LINEAR HDR sun radiance (a bright >1 core), attenuate it by airmass + cloud transmittance, then
    // ACES tone-map → the nucleus CLIPS to a DEFINED white body even under cloud, while the corona carries the
    // colour and the dimming. Cloud DESATURATES toward neutral-WARM white (a colour-temp shift), never blue-grey.
    const eC=Math.max(0,e);
    const m=1/(Math.sin(eC*Math.PI/180)+0.50572*Math.pow(eC+6.07995,-1.6364));   // Kasten–Young relative airmass
    const k=0.13+0.07*clamp(A.aerosolDensity);                                    // broadband optical depth: clean → hazy
    const Tbeam=Math.exp(-k*(m-1));                                               // Beer–Lambert beam transmittance
    const _tc={clear:1.0,cloud:0.7,overcast:0.35,thunder:0.22,fog:0.30,rain:0.40,snow:0.55,drizzle:0.6}[A.cls];
    const Tcloud=_tc!=null?_tc:(1-0.65*clamp(A.cloudCover));                      // cloud transmittance (attenuates flux, does NOT grey the colour)
    const CCT=Math.max(2000,Math.min(5800,2000+3500*_ss(e/40)));                  // colour temperature: ~2000K horizon → ~5500K noon
    const _bb=[[2000,255,137,18],[2700,255,169,87],[3500,255,196,137],[4500,255,219,186],[5500,255,228,206],[6500,255,243,239]];
    let cCol=[255,243,239]; for(let i=0;i<_bb.length-1;i++){ if(CCT<=_bb[i+1][0]){ const f=(CCT-_bb[i][0])/(_bb[i+1][0]-_bb[i][0]); cCol=[1,2,3].map(j=>_bb[i][j]+f*(_bb[i+1][j]-_bb[i][j])); break; } }
    cCol=mixRGB(cCol,[255,244,232],(0.12+0.08*clamp(A.cloudCover))*clamp((1-Tcloud)/0.65));   // cloud WARM white-balance (never cold grey)
    const cLin=cCol.map(v=>Math.pow(v/255,2.2));                                  // de-gamma → linear
    const aces=x=>{ x=Math.max(0,x*0.6); return Math.min(1,(x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14)); };   // ACES (Narkowicz)
    const tm=(lin,L)=>rgb(lin.map(c=>Math.round(255*Math.pow(aces(c*L),1/2.2))));  // tone-map a radiance to a display colour
    c.style.setProperty("--sunamt",sunAmt.toFixed(3));
    c.style.setProperty("--suncore",tm(cLin,6.0*Tcloud*(0.22+0.78*Tbeam)));
    let sunmidB=mixRGB([255,150,70],[255,214,170],noon);
    sunmidB=mixRGB(sunmidB,[255,238,218],(1-Tcloud)*0.45);
    c.style.setProperty("--sunmid",rgb(sunmidB));
````

**`paint() lines 1652–1663`**
cloudState mutation: this is a SIDE EFFECT (modifying global mutable state). It must remain in paint(), NOT move into atmosphere(). Decision: keep in paint(), clearly marked as the only mutation in paint(). Alternative: extract to a separate applyCloudState(A) function that paint() calls.

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
  CS.sunX=A.sunX/100; CS.sunY=A.sunY/100; CS.sunUp=clamp((A.solarElevationDeg+1)/5);
  CS.sunCol=A.cloudSunCol; CS.moonCol=A.cloudMoonCol; CS.moonX=A.cloudMoonX; CS.moonY=A.cloudMoonY; CS.moonLit=A.cloudMoonLit;
  _cloudDirty=true;
````

**`atmosphere() lines 1495–1498`**
Cloud layers (clLow/clMid/clHigh) are declared here. The tone-map block must run AFTER this to use clMid for transmittance.

````js
let clLow,clMid,clHigh;
  if(weather && weather.cloudLow!=null){ clLow=clamp(weather.cloudLow/100); clMid=clamp(weather.cloudMid/100); clHigh=clamp(weather.cloudHigh/100); }
  else { const sp=({clear:[0,0,0],cloud:[.2,.55,.4],overcast:[.92,.85,.5],fog:[1,.2,0],drizzle:[.72,.6,.2],rain:[.9,.85,.3],thunder:[.92,.9,.6],snow:[.82,.7,.3]})[cls]||[0,0,0]; clLow=sp[0]; clMid=sp[1]; clHigh=sp[2]; }
````

**`atmosphere() lines 1472–1475`**
cloudSunCol is already derived in atmosphere(); the tone-map math will use clMid and cloudSunCol to set colour temperature.

````js
const sunWarmC=clamp((15-sm.altDeg)/22)*(day?1:0);
  const cloudSunCol=mixRGB([255,247,232],[255,168,96], sunWarmC);
  const cloudMoonCol=mixRGB([206,220,246],[226,232,250], mFrac);
````

**`atmosphere() return object lines 1534–1567`**
The return object structure where sunCoreRGB and sunMidRGB must be added.

````js
return {
    // —— physical drivers (the source of truth) ——
    day, cls, info, code, wxTemp: weather?weather.temp:null,
    solarElevationDeg: sm.altDeg, skyLuminance: skyLum(sm.altDeg), sunX: sm.x, sunY: sm.y,
    ...[continues to line 1567]
````

## Approach
1. **In atmosphere() (lines 1375–1568):** After the cloud-layer derivation (line 1498) and after cloudSunCol (line 1474) and before the return statement (line 1534), insert a new **sun tone-mapping block** that:
   - Reads solar elevation (sm.altDeg), aerosol density (D.aerosolDensity), cloud class (cls), cloud cover (D.cloud or clMid/clLow/clHigh), and already-computed cloudSunCol.
   - Computes Kasten-Young airmass (m).
   - Computes Beer-Lambert beam transmittance (Tbeam).
   - Computes per-class cloud transmittance (Tcloud) using the _tc lookup or clMid if available.
   - Computes CCT from solar elevation.
   - Interpolates the blackbody colour from the _bb LUT.
   - Applies cloud white-balance (desaturates toward [255,244,232]).
   - De-gammas to linear and applies ACES curve.
   - Outputs two fields: **sunCoreRGB** (the tone-mapped nucleus colour as an rgb() string or [r,g,b] array) and **sunMidRGB** (the body/edge colour).
   - Also compute and return **sunAmount** (sunAmt, the presence scalar).

2. **Add to the atmosphere() return object:**
   - `sunCoreRGB`: the tone-mapped nucleus colour (already tone-mapped via ACES; paint() just assigns it).
   - `sunMidRGB`: the tone-mapped body/edge colour.
   - `sunAmount`: the presence opacity (clamp((e+1.5)/7)).
   - (Optional: also return `airmass`, `beamTransmittance`, `cloudTransmittance`, `colorTempK` if needed for debugging, but not strictly required.)

3. **In paint() (lines 1585–1631):**
   - **Delete** the entire tone-mapping block (lines 1593–1613 and the cc/sunmidB assignments).
   - **Replace** with a simple assignment: `c.style.setProperty("--suncore", A.sunCoreRGB);` and `c.style.setProperty("--sunmid", A.sunMidRGB);`.
   - Keep `c.style.setProperty("--sunamt", A.sunAmount.toFixed(3));` (now reading from A, not computing locally).
   - Keep lines 1614–1631 (SOLAR PATH, VISIBLE-SUN screen coordinate, rays, pulse, flattening) — these are still pure CSS property assignments.

4. **TDZ ordering:** Ensure the new tone-map block runs AFTER clLow/clMid/clHigh (line 1498), cloudSunCol (line 1474), and ray/moonLume (lines 1508, 1502) — they may be used by the tone-map logic or by gated optics. Place it around line 1520 (after all those declarations, before the return).

5. **cloudState mutation:** Keep paint's cloudState mutation (lines 1652–1663) UNCHANGED. It is a side effect and belongs in the render layer, not the pure state vector. Document the decision in a comment: "cloudState mutation is a render-layer side effect — paint() applies both the pure atmosphere state AND manages the cloud canvas state."

6. **No new abstractions:** Do NOT split paint() into smaller functions or add new helper closures. Keep the surrounding code idiom (single-letter locals, inline math). The cloudState block stays where it is; the tone-map math is simply lifted out of paint() into atmosphere().

## Alternatives considered (and rejected)
- **Extract cloudState mutation into a separate applyCloudState(A) function called by paint()** — Adds a layer of indirection without removing drift. The current paint() cloudState block is already well-commented and small. Splitting it would make the render pipeline less obvious. The ARCHITECTURE.md already documents this as a deferred follow-up ("extract to top-level DEBUGMOTION-gated helpers"), and that is a broader refactoring. For THIS task, keeping cloudState in paint() is simpler and more aligned with the minimal-change principle.
- **Move ONLY the tone-map MATH into atmosphere(), but keep the CSS property assignments in paint()** — This is the chosen approach — it is the minimal correct refactoring. The alternative would be to return both the derived values (airmass, transmittances, CCT) AND the final colours, which adds clutter. By deriving the final rgb() strings in atmosphere(), paint() becomes a true passthrough.
- **Refactor the _bb blackbody LUT into a named helper function** — The LUT is small (~6 entries) and used only here. Extracting it would add overhead and make the logic less obvious. Keep it inline, matching the surrounding code idiom (short, terse, unabstracted).
- **Use array [r,g,b] for sunCoreRGB/sunMidRGB and convert to rgb() in paint()** — Less elegant. The tone-map math already produces [r,g,b] arrays; converting them to rgb() strings in atmosphere() keeps paint() completely trivial (assign and move on). paint() should not do ANY conversions — it should just write.
- **Return ALL intermediate tone-map values (airmass, Tbeam, Tcloud, CCT, aces-curve) to atmosphere() for observability/debug** — Out of minimal scope. The only values the renderer needs are sunCoreRGB and sunMidRGB. Additional intermediate values can be added later for debug observability (qaState.sunTruth or similar) — that is a separate enhancement. For this task, return only what paint() needs.

## Owner / source touchpoints
- index.html:1376–1531 — atmosphere() function body (where the tone-map block is inserted, before the return statement)
- index.html:1534–1567 — atmosphere() return object (add sunCoreRGB, sunMidRGB, sunAmount)
- index.html:1585–1631 — paint() corner-sun block (delete lines 1593–1613, replace with simple property assignments, keep lines 1606–1631 for path/rays/pulse/flattening)
- index.html:1652–1663 — paint() cloudState mutation (keep as-is; no change)

## Regression risks (forbidden-regression guardrails)
- FORBIDDEN: Sun rendered as grey/purple blob or vague brush with no defined white nucleus — the tone-map MUST clip the nucleus to white even under cloud. TEST: clear noon (white nucleus), sunrise (warm glowing disc), overcast (warm-white nucleus, not grey). GUARD: the ACES curve and CCT blackbody colour must be identical before vs. after; any change to the `aces` function, the _bb LUT, or the Tcloud/Tbeam logic is a regression.
- FORBIDDEN: Sun colour changes between day scenes (sunrise vs. noon vs. sunset). TEST: sunlight transitions must be smooth. GUARD: CCT formula `Math.max(2000,Math.min(5800,2000+3500*_ss(e/40)))` must be exactly the same before vs. after.
- FORBIDDEN: Cloud transmittance (Tcloud) changes, causing sun dimming/brightening to diverge from before. TEST: overcast noon (dim white), thunderstorm (very dim). GUARD: the _tc lookup and fallback formula `(1-0.65*clamp(A.cloudCover))` must be identical.
- FORBIDDEN: Airmass (m) or Beer-Lambert (Tbeam) calculation diverges, causing horizon/low-sun colour shifts. TEST: sunrise at ~5 degrees elevation (warm but not orange). GUARD: Kasten-Young formula and optical depth (k) must match exactly.
- FORBIDDEN: sunAmount (sunAmt) opacity changes, causing the sun to vanish or persist in night. TEST: at solar elevation -1.5°, sunAmt should snap to ~0; above +5.5°, should be > 0.3. GUARD: formula `clamp((e+1.5)/7)` must be identical.
- FORBIDDEN: Tone-map logic runs BEFORE clLow/clMid/clHigh are declared, causing a ReferenceError or stale values (TDZ violation). TEST: no console errors; qaState.sky derives correctly in all weather conditions. GUARD: the tone-map block must be positioned after line 1498.
- FORBIDDEN: cloudState mutation is moved into atmosphere() or deleted, breaking the cloud canvas rendering. TEST: clouds appear and drift; rain/snow origins stay under cloud columns. GUARD: cloudState mutations stay in paint(), lines 1652–1663, unchanged.
- FORBIDDEN: Rendered sun position (--sunvx/--sunvy) diverges from the visible corner-sun body. TEST: optics (halo, sundogs, pillar) register to the same screen point. GUARD: lines 1627–1628 (sunVx/sunVy calculation from sunX2Px/sunLiftPx) are unchanged.

## Smoke A — capture BEFORE any change
- Load the widget with a clear Madinah scene: `index.html#lat=24.47&lon=39.61&label=Madinah&method=4&simTime=12:30&simWx=0&qa=1`. Screenshot the sun nucleus — note the white core, warm-gold body edge, broad corona. Record --suncore and --sunmid from getComputedStyle. Record qaState.sky.sunElevation, aerosolDensity.
- Load sunrise scene: `&simTime=05:50`. Screenshot the sun entering from the left; note the warm orange body, broad corona. Record --suncore and --sunmid.
- Load overcast noon: `&simTime=12:30&simWx=3&simCloud=100`. Screenshot the sun through cloud; nucleus should be warm-white (never grey/purple). Record --suncore and --sunmid.
- Load thunderstorm: `&simTime=15:00&simWx=95&simPrecip=2`. Screenshot the very dim sun through heavy cloud. Record --suncore and --sunmid.
- Check console: no errors; no ReferenceErrors from TDZ violations.
- Check qaState.cache.weatherStale and qaState.cache.prayerLoaded — ensure the widget fully loaded and is reporting state.

## Smoke B — verify AFTER the change
- After the refactor, load the same clear Madinah scene: `index.html#lat=24.47&lon=39.61&label=Madinah&method=4&simTime=12:30&simWx=0&qa=1`. Screenshot the sun nucleus. Visually compare to the BEFORE screenshot: nucleus should be identical white, body should be identical warm-gold, corona identical broad shape and fade. Record --suncore and --sunmid again; values must match within rounding (a few RGB points at most).
- Load sunrise: `&simTime=05:50`. Screenshot and compare to BEFORE. The sun should enter from the exact same screen position, with the exact same warm orange colour, exact same corona breathing.
- Load overcast: `&simTime=12:30&simWx=3&simCloud=100`. Screenshot and compare. The nucleus should still clip to the same warm-white (never cold grey), with the same body edge.
- Load thunderstorm: `&simTime=15:00&simWx=95&simPrecip=2`. Screenshot and compare. Same dim nucleus and corona.
- Load 5 scenes from the DESIGN.md QA matrix: clear noon, sunrise low-left, overcast warm-white sun, crescent moon with no sun occlusion, full moon. Each must match its BEFORE screenshot pixel-for-pixel (or within browser/antialiasing rounding — ~1–2 RGB points, never a visible colour shift).
- Run tests/smoke.html (ensure no FAILS; if PHPs are new, record the reason and add to a follow-up).
- Check console: no errors; debugMotion (if enabled) still shows cloud Δ and star scintillation without stuttering.
- Parse qaState.sky: sunElevationDeg, skyLuminance, glow, horizon, accent must match BEFORE values (no stale state or caching issues).

## Acceptance criteria (falsifiable)
- PIXEL-IDENTICAL rendered sun (nucleus, body, corona) across a scene matrix (clear noon, sunrise low-left, overcast, thunderstorm) before vs. after the refactor. A visual difference of >1% in hue/saturation is a FAIL. Use side-by-side screenshots or overlay diff.
- Console has zero ReferenceErrors or TDZ violations. No undefined variables in the tone-map block or the atmosphere() return object.
- qaState.sky reports the same sunElevationDeg, glow, horizon, accent values before and after (within floating-point rounding). A shift >0.5% is a FAIL (indicates stale state or miscalculation).
- paint() contains NO tone-map math (no Kasten-Young, no Beer-Lambert, no CCT, no ACES). A grep for 'aces' in paint() must return zero matches. A grep for 'Kasten' must return zero in paint().
- atmosphere() returns sunCoreRGB, sunMidRGB, sunAmount fields and they are used by paint(). paint() writes --suncore and --sunmid as simple assignments (no conditional colour logic, no transmittance math).
- cloudState mutations in paint() are unchanged (lines 1652–1663 remain identical). The cloud canvas still drifts and clouds rain from the correct columns.
- Optics (halo, sundogs, pillar) register to the visible sun (--sunvx/--sunvy) and ring the same screen point before vs. after. A center-screen halo (detached from the sun) is a FAIL.
- tests/smoke.html runs without new FAILs. If a new SKIP appears, investigate (likely an unrelated flaky network test, not a regression).

## Rollback
`git diff index.html` to verify only the expected sections changed (atmosphere() tone-map block added, paint() tone-map block replaced with assignments). If a change outside those sections crept in, revert the file and restart. If tests/smoke.html introduces new FAILs not attributable to the refactor (e.g., prayer-fetch network error), document the reason and mark as expected. If pixel screenshots diverge >1% hue, revert and investigate the CCT/ACES logic for a typo (e.g., missing `Math.pow` exponent).

## Dependencies / sequencing
_(none)_

## Open questions
- Does atmosphere() need to return intermediate values (airmass, Tbeam, Tcloud, CCT) for debug observability (qaState.sunTruth)? DEFERRED: not in this task; can be added in a follow-up observability pass.
- Should cloudState mutation be extracted to a separate applyCloudState(A) function as part of broader refactoring? DEFERRED: ARCHITECTURE.md lists this as a future pass; for now, keep in paint().
- Does the _bb blackbody LUT need to be exposed as a shared constant or module export (e.g., for testing or for the builder)? DEFERRED: the builder.html shares no JS with the widget, so no external consumer exists. Keep inline.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. Specify exact insertion point for the tone-map block in atmosphere(): Change 'around line 1520' to 'after line 1508 (after ray declaration, before line 1520, before the return statement on line 1534)'. Alternatively, provide an anchor comment (e.g., '// —— SOLAR TONE-MAPPING BLOCK ——') so the implementer can search for the exact position.
2. Explicitly document output format: State 'sunCoreRGB and sunMidRGB are rgb() strings (e.g., "rgb(255,255,255)") matching the format returned by the rgb() helper function (line 1152). paint() assigns them directly to CSS custom props without conversion.'
3. Tighten grep acceptance criterion: Replace 'A grep for "aces" in paint() must return zero' with 'A grep for (Kasten|Beer|CCT|_bb|Tbeam|airmass|transmittance|aerosolDensity|cloudCover) in paint() must return zero matches in the DERIVED-state context. (These variables may appear in comments; the test checks the LIVE-MATH context, not comments.)'
4. Add missing regression test for tone-map math correctness: 'The aces() ACES curve, the _bb blackbody LUT, the Kasten-Young formula (m=...), the Beer-Lambert formula (Tbeam=...), and the CCT formula (CCT=...) are BYTE-FOR-BYTE identical before and after the refactoring. A diff of tone-map-math-only lines must show zero functional changes (whitespace/variable names OK, math NOT OK). Verify with a diff tool or a manual spot-check of 3–5 key formulas.'
5. Strengthen pixel-diff acceptance: Add 'A quantitative image-diff tool (ImageMagick `compare -metric RMSE` or ssim/perc-dist) on nucleus + body + corona crops shows <0.5% RMS error. Hue shift >2% is a FAIL.' This eliminates subjective screenshot grading.

**Missing risks the spec omitted:**
- Temporal Dead Zone (TDZ) ordering: plan says 'around line 1520' but does not specify exact insertion point. If placed between line 1508 (ray) and the return (1534), it will correctly see ray/moonLume. But if the implementer inserts it at the wrong line, a ReferenceError on clMid or ray will occur. Plan must specify 'after line 1508 (ray declaration)' or provide an anchor comment.
- Tone-map output format ambiguity: plan does not explicitly state whether sunCoreRGB/sunMidRGB are rgb() strings (e.g., 'rgb(255,255,255)') or [r,g,b] arrays. The current paint() code calls tm(cLin, L) which returns rgb(...) strings via the rgb() helper (line 1152). If atmosphere() returns arrays instead, paint() must convert them, violating the 'thin façade' contract.
- Floating-point precision: the newly-moved tone-map math uses intermediate values (m, k, Tbeam, Tcloud, CCT) that may be computed in a different order than the original inline code. Reassociation of floating-point operations (e.g., `a*b*c` vs `(a*b)*c`) can cause sub-pixel colour shifts (>1–2 RGB points). Plan does not guard against this or document acceptable error bounds.
- cloudState temporal coupling not mentioned in TDZ check: paint() reads cloudState (lines 1653–1663) AFTER the atmosphere() return. If any future refactoring tries to move cloudState mutation into atmosphere() as a 'pure' pass, the TDZ ordering could be silently violated (because cloudState is external state, not a local variable).
- Indirect regression: if the new tone-map block in atmosphere() mutates or modifies clMid, D.haze, or other shared inputs used by later code in atmosphere() (e.g., cloud layer rendering), a stale-state bug could occur. Plan assumes all tone-map inputs are read-only.

**Weak acceptance criteria (a broken change could still pass):**
- Grep criterion for 'aces' in paint(): a refactoring that moves Kasten-Young/Beer-Lambert/CCT logic but leaves the ACES curve closure in paint() (or accidentally duplicates it) would PASS the grep test because the substring 'aces' still appears. Better: 'A grep for (Kasten|Beer|CCT|_bb|Tbeam) in paint() must return zero.'
- qaState verification criterion checks sunElevationDeg/skyLuminance/accent but NOT sunCoreRGB/sunMidRGB: these unchanged fields will always match BEFORE values, so the test is not actually verifying the refactoring works. Better: 'A.sunCoreRGB and A.sunMidRGB are populated; paint() reads and assigns them; missing/undefined/null is a FAIL.'
- Pixel-identical criterion allows ±1–2 RGB points (antialiasing rounding): but floating-point reassociation in the newly-moved math could cause larger hue/saturation shifts without pixel-level variation (e.g., a [255,204,128] nucleus becoming [254,203,130] — still 'off-white' but visibly different in context). Better: 'Quantitative pixel-diff tool (ImageMagick compare) on nucleus/body/corona shows <0.5% RMS error; visual inspection shows no hue shift.'
- Smoke tests (A–B) require manual screenshot comparison but do not specify a diff tool: relying on human-eye 'match within rounding' is subjective and slow. Better: quantify with SSIM / perceptual distance metrics.

**Scope concerns:**
- Plan introduces ~8 intermediate local variables (m, k, Tbeam, Tcloud, CCT, cCol, cLin, aces, tm) into atmosphere(), which increases complexity. While the plan says 'match the surrounding code idiom (single-letter locals, inline math)', those single-letter locals are _already_ in the current paint() block. Moving them to atmosphere() is not a violation (they remain local), but it does add density to atmosphere(). Plan does not discuss whether simplification (e.g., inlining some intermediate calcs) is acceptable.
- No explicit statement about whether atmosphere() return object mutation is acceptable: adding sunCoreRGB/sunMidRGB/sunAmount is a **breaking change for code that iterates the return object** (e.g., for(const k in A)). The codebase does not do this currently, but the plan should state this explicitly to guard against future surprises.

**Grounding issues (claims to re-check against current code):**
_(none)_

**Reviewer notes:** Code grounding is solid: all line refs, quoted code snippets, and function names are verified against the current 1951-line index.html. No typos or drift detected in the codebase refs. The plan correctly identifies helper functions (rgb, rgba, mixRGB, _ss, clamp) and the existing return-object structure. The ARCHITECTURE.md § 1 SRP tangle ref is accurate. The plan is sound in spirit but needs tighter execution details (TDZ anchor point, output format) and better acceptance criteria (avoid subjective screenshot grading, specify quantitative bounds). Once those three requiredFixes are applied, the plan is execution-ready.
