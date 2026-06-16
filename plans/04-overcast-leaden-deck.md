# Plan 04 — Plan: Overcast reads as a heavy leaden ceiling, not hazy

> **Status:** ✅ DONE (2026-06-16) — **conservative, regression-free improvement** (final aesthetic dial is the user's; it's subjective and they're the visual judge). Three overcast-/coverage-gated edits: (1) `WX.overcast` sky tint → more neutral-grey + stronger (`[60,68,80]`/`.50` → `[56,60,68]`/`.60`) so the sky *behind* the clouds reads leaden, not blue — the highest-impact lever; (2) overcast-only `cloudBase` darkening (luminance 135→118); (3) coverage-gated puff-opacity boost (`cov>0.7`) to fill gaps. Sun is **unaffected** (tone-map keys off `cls`/cloud, not `cloudBase`). Verified: overcast-noon clearly leaden vs baseline; overcast-night opaque moon (1.0/1.0) + ashen (not muddy) + `starOp`0.07; **broken & clear visually unchanged** (gating); motion preserved (paintClouds t=10/40/70 morph+advect); 28/28.  ·  **Class:** visual  ·  **Priority:** P1  ·  **Effort:** M  ·  **Risk:** med
> **Do now?** Yes — recommended soon  ·  **Plan-review verdict:** `needs-fixes` (7 required fixes — see end)  ·  **Depends on:** none
>
> Read-only plan from `/implementaudit` (workflow `wf_f498de17-f7b`, investigate → adversarial critique). Grounded against `index.html` @ commit `91d0fc1` (~1951 lines). **No source was changed.** Line numbers drift — re-verify the anchors before editing.

## Problem
The overcast sky (coverage approaching 1.0) currently reads as "a touch hazy" rather than a heavy, leaden ceiling. This is the single most-flagged remaining visual residual. The cloud deck lacks the density, flatness, and oppressive low luminance of real overcast; gaps in the puff-cluster field let the sky show through even at high coverage, and the base tint may be too warm or too bright.

## Root cause
The cloud renderer (paintClouds, lines 1329–1376) uses overlapping soft puffs on a tiny canvas (72×118px, CSS-upscaled), with coverage controlling cluster count via the `gate` sigmoid. At high coverage (cov→1), the gate smoothly fades in all N clusters, but soft radial-gradient edges leave visible gaps. Additionally, the cloudBase tint (lines 1465–1471) may be too saturated or bright at overcast, and the topBrightness bound in paint() (if any) may not be sufficiently dark/compressed at high coverage. The lifecycle/advection motion preserves visual interest but can make the deck feel scattered rather than dense.

## Current behavior
Load index.html with `?simWx=3&simCloud=100&simTime=12:30` (overcast at noon): the sky shows a pale, diffuse cloud field; the dashed horizon is clearly visible; gaps between puff clusters let sky colour through; the overall read is "hazy" or "misty," not "oppressive ceiling." Stars at night under overcast (simTime=01:00) show faintly, and the coverage-driven opacity doesn't fully occlude them.

## Desired behavior
An overcast day (coverage ≥ 0.85) should render a **dense, flat, lower-luminance deck** that reads as a heavy, impending ceiling—the sky largely occluded from below, with only subtle internal texture and motion (no slideshow, no puffiness). At night, the deck is a dark ashen underlit dome. The dashed horizon should be mostly or fully hidden. Stars should be nearly invisible even at high humidity. The cloudBase tint should shift toward neutral grey-white (cool, not warm), and the overall luminance should drop noticeably. Motion (advection/lifecycle) remains but at lower amplitude. The definition: **leaden ≠ uniform-dead-grey**; subtle internal structure + motion must remain, but it reads as a **structural ceiling, not a scattered field**.

## Code anchors (re-verify line numbers before editing)
**`index.html:1465–1471 (atmosphere function, cloudBase tint calculation)`**
cloudBase is tinted darker under wet conditions, but at high coverage the warmth from the low-sun term dominates. The overall luminance may not compress enough. Overcast specifically needs to suppress warm undertones and ensure a cooler, denser base tint.

````js
const wet=(cls==="rain"||cls==="thunder"||cls==="overcast")?1:(cls==="drizzle"||cls==="snow"||cls==="fog")?0.5:0;
  let cloudBase=mixRGB([232,236,243],[196,206,220],wet);
  cloudBase=mixRGB(cloudBase,[66,74,90],0.55*wet);
  const dayK=day?1:clamp((sm.altDeg+8)/10);
  cloudBase=mixRGB([34,44,66],cloudBase,dayK);
  if(sm.altDeg<18){ const warmU=clamp((18-sm.altDeg)/16)*(day?1:0.3); cloudBase=mixRGB(cloudBase,[255,166,102],0.62*warmU); }
````

**`index.html:1335–1376 (paintClouds function, cluster rendering)`**
The puff clustering uses soft radial gradients (lines 1314–1323) that fade to 0 at the edge, leaving gaps even at high coverage. The aMul (amplitude multiplier) is life*gate, which can be low when gate is low (life is 0..1 noise-driven). At overcast, clusters should have higher combined opacity/density and less visible gaps. The lifecycle morph (lines 1349–1357) is calibrated for perceptual motion, but at overcast it may cause visual 'looseness'.

````js
function paintClouds(t){
  if(!_cloudCv){ _cloudCv=document.querySelector(".cloudcanvas"); if(!_cloudCv) return; _cloudCtx=_cloudCv.getContext("2d"); }
  const W=_cloudCv.width,H=_cloudCv.height,S=cloudState,ctx=_cloudCtx;
  ctx.clearRect(0,0,W,H);
  ...decks=[...]; for(let di=0;di<3;di++){
    const dk=decks[di], cov=dk[0]; if(cov<0.02) continue;
    ...
    const gate=clamp((cov*n*1.25 - i)*1.2);  // coverage decides how many clusters are active
    const aMul=life*gate; if(aMul<0.02) continue;
    ...for(let pi=0;pi<_PUFF.length;pi++){
      ...const tB=clamp(0.5-p[1]*0.95);  // top lit, base shaded
      ..._drawPuff(ctx,px,py,pr,col,aBase);  // aBase = dop*aMul*0.5
    }
````

**`index.html:1314–1323 (_drawPuff function, puff rendering with soft edges)`**
The radial gradient has a 0.42 factor at 0.8r (softening) and fades fully to 0 at 1r (edge). This produces beautiful soft puffs for broken clouds but soft edges visible between puffs at overcast. Puff-to-puff opacity/coverage needs review.

````js
function _drawPuff(ctx,x,y,r,col,a){
  if(r<0.6||a<0.012) return;
  const c=(col[0]|0)+","+(col[1]|0)+","+(col[2]|0);
  const g=ctx.createRadialGradient(x,y,r*0.12,x,y,r);
  g.addColorStop(0,  "rgba("+c+","+a.toFixed(3)+")");      // plateau core
  g.addColorStop(0.5,"rgba("+c+","+a.toFixed(3)+")");      // plateau
  g.addColorStop(0.8,"rgba("+c+","+(a*0.42).toFixed(3)+")");  // soft falloff
  g.addColorStop(1,  "rgba("+c+",0)");                      // edge fade to 0
  ctx.fillStyle=g; ctx.beginPath(); ctx.arc(x,y,r,0,6.2832); ctx.fill();
````

**`index.html:1337–1342 (decks definition, coverage → cluster slots)`**
Low deck: 7 slots, dop=1.0. Mid: 6 slots, dop=0.9. High: 5 slots, dop=0.5. As cov→1, all slots activate with life-weighted opacity. At overcast, dop (deck opacity) may need to increase or the gate curve steepened to reduce visible clustering.

````js
const decks=[
    [S.covLow, 31, 0.205, 0.05, S.tLow, 1.0, 19.1+_cs, 7],   // low cumulus deck
    [S.covMid, 26, 0.135, 0.05, S.tMid, 0.9, 4.7+_cs,  6],   // mid deck
    [S.covHigh,20, 0.07,  0.04, S.tHi,  0.5, 11.3+_cs, 5],   // thin high wisps
````

**`index.html:1649 (smoke.html::overcast test, acceptance definition)`**
Smoke tests (pure + integration) do not yet capture overcast visual density. A future test should verify coverage easing and non-slideshow, but visual pixels override metrics.

````js
No test currently; smoke.html has no visual overcast expectation yet. The DESIGN.md residual note (line 251) states: 'Cloud edges are soft/painterly rather than crisp cumulus; overcast reads a touch hazy rather than heavy-leaden (most-flagged remaining item).'
````

## Approach
1. **Identify the gap mechanism:** confirm whether gaps are due to (a) puff soft-edge falloff, (b) low aMul (life*gate) at overcast, or (c) a combination. Trace a sample high-coverage render to measure puff opacity at boundaries.

2. **Tighten cloudBase tint for overcast:** modify the `cloudBase` calculation (lines 1465–1471) to suppress warm low-sun undertones specifically when `cls=="overcast"` and shift toward cooler, lower-luminance grey-white. Test the tint at noon and sunset.

3. **Boost cluster density at high coverage:** increase the gate steepness or add a coverage-squared term so that at cov≥0.85, aMul is higher and gaps are minimal. Ensure life still modulates (no frozen slab).

4. **Optionally increase puff base opacity (aBase):** if gaps remain, raise `aBase = dop*aMul*0.5` to `dop*aMul*0.6` or `0.65` specifically at overcast coverage, to reduce inter-puff visibility. Verify no loss of motion.

5. **Verify no slideshow/continuity loss:** confirm cloudState easing still works; coverage changes still ease smoothly. Run a 15-min simulated refresh (via debug sim).

6. **Screenshot matrix acceptance:** clear day (unchanged), broken cloud (unchanged), overcast day at noon (leaden, dashed horizon hidden), overcast at sunset (warm-white sun, dark deck), overcast night (dark ashen dome, stars nearly invisible), overcast→clear transition (smooth easing, no pop).

7. **Live motion verification:** overcast real-time (15–60s watch + debugMotion) shows subtle drift/morphing, not frozen.

8. **No regressions:** clear/broken sky unchanged; moon still opaque; no painted dawn; sun still tone-mapped correctly under overcast.

## Alternatives considered (and rejected)
- **Increase puff circle radius or cluster count at overcast** — Would make the deck denser but risks making individual puff shapes visible ('puffy' look), defeating the 'structural ceiling' goal. The current soft-puff design is right; we need opacity/tint, not geometry.
- **Replace the puff-cluster approach with a volumetric FBM density field** — Out of scope; would require rewriting paintClouds and risks losing the 'continuity' (no reseed) invariant. The DESIGN.md and ARCHITECTURE.md state the puff-cluster + time-noise field is load-bearing.
- **Add a post-process 'overcast overlay' CSS layer that darkens/flattens the deck** — Violates the render boundary: paint(A) writes sky/light custom props; adding a DOM overlay would couple presentation to the canvas and complicate the layer order. Changes should be in cloudBase tint + paintClouds opacity.
- **Gate the overcast-specific changes on a new coverage-weighted scalar, separate from wx-class** — Unnecessary indirection; overcast is already a cls==='overcast' condition. Use cls directly to adjust tint + gate steepness.
- **Reduce puff size (R0) at overcast to create a finer-grained texture** — Small puffs would clump and read as uniform noise, not 'structured ceiling.' The 31px/26px/20px R0 is calibrated for visual interest; changing it risks a 'dead' deck.

## Owner / source touchpoints
- index.html:1465–1471 (cloudBase tint calculation in atmosphere)
- index.html:1344–1375 (paintClouds gate logic and aMul opacity, especially the gate sigmoid and aBase multiplier)
- index.html:1350 (gate=clamp((cov*n*1.25 - i)*1.2) — the curve controlling cluster activation)
- index.html:1360 (aBase=dop*aMul*0.5 — puff base opacity)
- index.html:1498 (clLow/clMid/clHigh overcast split in atmosphere — currently [0.92, 0.85, 0.5])

## Regression risks (forbidden-regression guardrails)
- **Static/frozen sky:** if aMul is boosted too aggressively or lifecycle is suppressed, the deck reads as a frozen slab (violates FORBIDDEN M0). Verify live motion remains visible over 15–60s.
- **Slideshow on weather refresh:** if the gate curve changes cause cluster activation/deactivation to be sharp (binary), coverage easing may produce visible pop-in/out (violates FORBIDDEN 'continuity'). Maintain the smooth sigmoid.
- **Grey/purple sun under overcast:** if cloudBase tint overshoots toward cool grey, the sun tone-map in paint() may not compensate, resulting in a cold blob. The tone-map (lines 1586–1632) already uses Tcloud transmittance to warm the nucleus; verify it still works.
- **Stars visible at night overcast:** if cloudBase luminance stays high, star opacity may not compress enough (stars are gated by weather class + cloud cover). Confirm stars are ≤10% visible at overcast night.
- **Broken/clear clouds degraded:** changes to gate or aMul must only affect overcast (cov≥0.85). Broken clouds (cov=0.2–0.5) should render unchanged. Use a conditional gate factor keyed to coverage.
- **Layout/footer clipped:** paintClouds only writes to the canvas; no DOM geometry changes. No regression risk here, but verify the CSS upscaling of the canvas does not shift layer positions.

## Smoke A — capture BEFORE any change
- 1. Load real-time clear sky (no simWx): **baseline motion visible** over 15–60s (cloud drift, sky breathing, star twinkle). Record cloud Δ from debugMotion.
- 2. Load overcast at noon (`?simWx=3&simCloud=100&simTime=12:30`): **screenshot the dashed horizon** — capture the current hazy appearance for comparison.
- 3. Load overcast at sunset (`?simWx=3&simCloud=100&simTime=18:55`): **crop the sun + cloud deck** — current warm undertone.
- 4. Load overcast at night (`?simWx=3&simCloud=100&simTime=01:00`): **screenshot the dark deck + stars** — current star visibility.
- 5. Run a coverage-easing sim: `?simWx=2&simCloud=20&timeScale=3600&simTime=06:00` → the deck should ease toward overcast (~50% per minute change) with **no pop-in/out**.
- 6. Record `qaState().clouds` for the baseline: coverage, hash (for continuity check post-fix).

## Smoke B — verify AFTER the change
- 1. **Overcast-at-noon screenshot:** dashed horizon mostly/fully hidden; deck reads dense, cool-toned, oppressive; no visible puff-cluster gaps.
- 2. **Overcast-at-sunset screenshot:** warm sun visible but with a clearly warm-white nucleus (not grey), surrounded by a dark leaden deck (no hazy sky showing through).
- 3. **Overcast-at-night screenshot:** dark ashen dome underlit by faint internal gradients; stars nearly invisible or ≤5% visible (compare qaState star opacity); no bright patches.
- 4. **Clear-sky motion baseline matches:** real-time clear still shows drift/morph over 15–60s; debugMotion Δ ≈ baseline (no slowdown).
- 5. **Coverage easing repeats:** `simCloud=20→100` (or via refetch) eases smoothly; no visible pop-in; cloudFieldSeed remains stable (qaState.wxTruth.cloudFieldSeed unchanged per read).
- 6. **Broken clouds unchanged:** broken-cloud test (`?simWx=2&simCloud=50&simTime=12:30`) shows gaps, drifting clusters, sky showing through (pre-fix appearance). No regression.
- 7. **Moon opaque over overcast:** new/bright moon under overcast (`?simWx=3&simCloud=100&simMoon=0.5`) shows opaque disc; no stars visible through; --moongrp and --moonocc ~1 at night.
- 8. **Live motion real-time:** widget with no sim params, real clock, overcast region; watch 15–60s — cloud deck visibly drifts/morphs (not frozen); debugMotion 10s/60s Δ ≫ 0.

## Acceptance criteria (falsifiable)
- **Visual: Leaden density.** Screenshot matrix (clear, broken, overcast-day-noon, overcast-day-sunset, overcast-night) shows overcast as a heavy, mostly-opaque ceiling with low luminance and cool tint. Dashed horizon nearly/fully hidden. Puff clusters visible only as subtle texture, not as scattered gaps.
- **Visual: Sun under overcast.** At overcast noon, the sun is a warm-white defined nucleus with a warm-gold body edge (tone-mapped, not grey/purple). At sunset, both sun and deck are warm but cohesive, not hazy-separated.
- **Visual: Stars at overcast night.** qaState().starOpacity ≤ 0.10 at overcast night (compared to baseline clear night). Screenshot: stars are barely visible (not absent, but deeply suppressed).
- **Continuity: No slideshow.** Coverage eases smoothly over 15–60s real-time (no pop-in/out clusters). `qaState().wxTruth.cloudFieldSeed` is stable across successive qaState() reads (same day, same location).
- **Motion: Live drift/morph.** Real-time overcast widget (no simTime) shows visible cloud drift + morphing over 15–60s watch. `debugMotion` reports 10s/60s Δ ≫ 0 (exact threshold: ≥15px total movement or ≥3% opacity change over 60s, conservative).
- **Regression: Clear + broken unchanged.** Clear-sky scene and broken-cloud scene are pixel-identical to baseline (crop comparison or qaState metrics unchanged). `paintClouds` is called at same rate.
- **Regression: Moon opaque.** Moon under heavy cloud (any phase, any night) shows no stars through the disc. --moongrp and --moonocc at full opacity (~0.95+) at night.
- **Regression: Sun tone-map.** Sun under overcast (any elevation) is warm-white (never grey/purple). Transmittance floor (--suncore) is still visible at low sun. Nucleus is defined (not a vague brush).
- **Gate: No frozen slab.** Overcast does not read as a uniform, static, featureless grey. Subtle internal structure and motion remain (texture + advection, both observable in screenshots/motion clips).

## Rollback
Revert to the committed index.html HEAD. If partial: (1) undo cloudBase tint changes (lines 1465–1471), (2) revert gate/aMul logic (lines 1350, 1360), (3) revert coverage splits (line 1498), (4) run smoke tests to confirm no regressions. Visual proof: overcast returns to current hazy appearance; clear/broken unchanged.

## Dependencies / sequencing
_(none)_

## Open questions
- **Exact gate steepness:** the current gate=clamp((cov*n*1.25 - i)*1.2) produces a smooth sigmoid. Should we add a coverage-squared term (e.g., cov*cov) to steepen it only above cov=0.85? Or adjust the multiplier 1.25 → 1.3–1.4? Requires manual tuning + screenshot review.
- **CloudBase tint warmth suppression:** at overcast, how much should we suppress the warm low-sun term (lines 1470–1471)? Proposal: multiply warmU by `cls==='overcast'?0.3:1` to keep low-sun warmth 30% of normal at overcast, else full. Alternative: gate it entirely (×0 at overcast). Needs visual test.
- **Puff opacity floor:** if aMul gets low (life≈0.1, gate≈0.5 at overcast, aMul≈0.05), should there be a minimum opacity so puffs are never fully transparent? Current: aMul<0.02 → continue (skip puff). Proposal: reduce threshold to 0.01 or add a 0.03 floor to aMul. Risk: more dense, but also more visual noise.
- **Deck opacity (dop) for low:** currently dop=1.0 for low deck, dop=0.9 for mid, dop=0.5 for high. At overcast, should dop increase (e.g., 1.0→1.1, 0.9→0.95) to ensure complete occlusion? Or keep as-is and rely on gate boosting? Proposal: keep dop, boost gate only (simpler, fewer variables).
- **Coverage split (clLow/clMid/clHigh):** currently overcast is [0.92, 0.85, 0.5]. Should the low deck be even denser (0.95+)? Or should we reduce high to 0.3–0.4 so the thin veil doesn't lighten the deck? Currently the mid/high together account for 1.35 coverage (normalized), which may be spreading the deck too thin. Proposal: test [0.95, 0.80, 0.3] for overcast.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. Specify exact gate formula with numbers. Proposal in plan: 'add coverage² term' or 'adjust multiplier 1.25→1.3–1.4'. Pick ONE and commit. Example: const gate=clamp((cov*n*(1.25+0.3*Math.max(0,cov-0.85))-i)*1.2) or const gate=clamp((cov*n*1.4-i)*1.2) when cov≥0.85.
2. Verify cloudBase tint + new formula does NOT grey/purple the sun. Compute worst-case tone-map: overcast weather + solar elevation 0° (horizon) + new cloudBase tint. Show the resulting --suncore RGB. Assertion: R+G+B ≥600 (not grey) AND NOT purple (R+B should NOT be >G+50). Document the calculation in the plan narrative or a verification script.
3. Confirm overcast wxClass and star-opacity gating. (1) Verify wxClass('overcast') returns 'overcast' (not 'cloud'). (2) At lines 1450–1459, check Milky Way/star gate for overcast: current code has no explicit case, defaults to 0 (stars off). Plan must verify this is safe or propose a fix (e.g., stars*0.1 for overcast, gentle suppression instead of hard gate).
4. Ensure NO TDZ violations. If cloudBase tint modification (lines 1465–1471) references clLow/clMid/clHigh, move the block to AFTER line 1498 or declare the variables earlier. Current code is safe; document the ordering invariant in the plan to prevent future drift.
5. Define 'subtle internal structure' quantitatively. Commit to a visual threshold in the acceptance criteria. Example: 'At least 3–5 distinct puff silhouettes readable per cluster at overcast; individual puffs remain silhouetted, not merged into a uniform wash. Verified at 5cm viewing distance / representative crop.' OR a pixel-level spec.
6. Define motion threshold per-weather. Current acceptance: debugMotion Δ ≥15px/10s or ≥3% opacity/60s. Refine for overcast: specify expected Δ for calm vs windy conditions. Or: propose a baseline (clear-sky real-time motion Δ) and assert overcast Δ ≥ 80% of baseline.
7. Add qaState observability. Plan must propose adding to qaState: (a) cloudBaseLuminance (RGB avg / 255), (b) starOpacity at overcast, (c) a horizon-alpha or dashed-line brightness metric to measure 'hidden.' Examples: cloudBaseLuminance: (A.cloudTint[0]+A.cloudTint[1]+A.cloudTint[2])/3/255, starOpacity: A.starOpacity, horizonAlpha: (read --g3 opacity from DOM computed style).

**Missing risks the spec omitted:**
- Static/frozen sky (M0): plan mentions 'verify motion remains' but does not characterize the sharp gate-curve scenario where clusters pop in/out visibly on coverage easing, reading as jerky. No justification for coverage² term or steepness multiplier (1.25 → 1.3–1.4).
- Slideshow/continuity: plan does not address interaction between boosted aMul/gate and the cloudState easing curve (ce=0.08, line 1658). If aMul jumps and ease curve can't smooth it, a visible stutter could appear on coverage changes.
- Grey/purple sun: if cloudBase tint overshoots toward cool grey at overcast, the tone-map at line 1602 (warm-white-balance via mixRGB) may not compensate. Plan does not compute worst-case --suncore RGB (overcast + 0° sun + new cloudBase) to verify it stays warm-white (never grey <200,200,200 or purple).
- Stars 'invisible' at overcast night: wxClass('overcast') returned value is NOT verified. Milky Way gate at line 1459 has no explicit case for cls==='overcast', defaulting to 0. Could cause regression where stars vanish entirely instead of suppressing gently. Star-opacity reduction mechanism is unclear.
- TDZ/Lexical ordering: if plan modifies cloudBase tint (lines 1465–1471) to reference clLow/clMid/clHigh, ReferenceError because those vars are declared at line 1498. Current code is safe, but any change must not reference coverage-split variables before their declaration.

**Weak acceptance criteria (a broken change could still pass):**
- 'Dashed horizon mostly/fully hidden': screenshot-based criterion but qaState() has NO metric for horizon visibility. A darker-tinted puff cluster could reduce horizon brightness subjectively while remaining faintly visible—screenshot might read as 'mostly hidden' but fail under pixel-level scrutiny. Need quantitative horizon-alpha or luminance threshold.
- 'Leaden, not scattered': criterion says 'subtle internal structure + motion remain' but does not define 'subtle.' A boost to aMul that merges puffs could read as uniform blob with no distinguishable silhouettes. Need visual/pixel-level specificity (e.g., 'puff silhouettes distinguishable at 5cm from 2560×1620 view').
- 'Motion: Live drift/morph': debugMotion Δ ≥15px over 10s or ≥3% opacity is conservative and weather-dependent. Overcast in calm wind may not reach 15px in 10s but still animate. Need per-condition threshold (overcast+calm vs overcast+gale).
- 'Stars ≤10% visible': if qaState().starOpacity is used but plan does NOT verify current code computes it for overcast condition, criterion is circular. Need a live measured example (Madinah 01:00 overcast, new code).

**Scope concerns:**
- Accumulating overcast-specific gates: plan proposes FOUR independent overcast adjustments (gate steepness, aBase boost, cloudBase tint suppression, coverage-split change). Each is condition-gated correctly, but plan does NOT justify interaction. E.g., if all four applied, is the result 'oppressive ceiling' or 'frozen dead-grey slab'? Does boosting gate+dop mask motion? Needs a prioritized order (1–2 highest-impact changes justified, others secondary/optional) or a full interaction matrix (out of scope but acknowledge the risk).

**Grounding issues (claims to re-check against current code):**
_(none)_

**Reviewer notes:** **Summary:** The plan correctly identifies the visual residual (overcast reads hazy, not leaden) and proposes sound architectural changes (gate boosting, cloudBase tint, dop adjustments, optional coverage-split). Code citations are accurate (lines 1465–1471, 1350, 1360, 1498 all verified). Render boundary, moon-ordering, and TDZ invariants are honored in the core approach. HOWEVER: (1) gate formula is vague ('1.3–1.4' or 'coverage² term' — pick one); (2) sun tone-map under new cloudBase is NOT verified (risk of grey/purple sun); (3) overcast wxClass + star-opacity gating is ambiguous (potential regression); (4) acceptance criteria mix subjective measures ('subtle,' 'mostly hidden') with qaState metrics (no current horizon-alpha or cloudBase-luminance observation surface); (5) no justification for applying all four changes vs a phased approach. The plan is **strategically sound but tactically incomplete**. Fix the formula, compute the sun tone-map, confirm star gating, refine the acceptance criteria with measurable thresholds, and add qaState observability — then it is **execution-ready**.
