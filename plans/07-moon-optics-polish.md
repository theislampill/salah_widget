# Plan 07 — Moon-halo debug key + halo/paraselenae arc-clip polish

> **Status:** ✅ DONE (2026-06-16). (a) Added `?debugOptic=lunarhalo` (made `lunarHalo` `let` so the debug block can force it to 0.95) — verified forcing it on a clear night renders a clear ring; moon stays opaque (`--moonocc`/`--moongrp`=1.0); 28/28 smoke. (b) **Committed to remedy (c) — document the limit** (not radius-reduction, not clip-path): measured the moon disc at center ≈(267,56) r≈50px, only ~56px from top/right edges, so a true-scale ring (r≈135px) MUST overrun those edges; a radius small enough to fit (≤~56px) would collapse into a corona and break the "distinct 22° ring" contract. The card's `overflow:hidden` already clips it to a clean partial arc that reads as a coherent halo. Documented in OPTICS.md.  ·  **Class:** optics  ·  **Priority:** P2  ·  **Effort:** S  ·  **Risk:** low
> **Do now?** Yes — recommended soon  ·  **Plan-review verdict:** `needs-fixes` (9 required fixes — see end)  ·  **Depends on:** none
>
> Read-only plan from `/implementaudit` (workflow `wf_f498de17-f7b`, investigate → adversarial critique). Grounded against `index.html` @ commit `91d0fc1` (~1951 lines). **No source was changed.** Line numbers drift — re-verify the anchors before editing.

## Problem
Two residual optics QA issues prevent efficient testing and acceptance of moon halo behaviour: (a) The moon halo has NO separate debug key — `?debugOptic=halo` forces the SUN halo only, making it impossible to QA the lunar halo independently. (b) The moon halo/paraselenae can render as PARTIAL ARCS because the halo radius (r=120 in scaled SVG) exceeds the disc and clips at the card edge or against the moon's in-frame pocket, breaking the visual coherence of the ring. OPTICS.md already notes (a); HANDOFF.md flags (b) as a residual.

## Root cause
(a) The `DEBUGOPTIC` param parser (line 1517) has no case for a separate lunar halo key — the word "halo" was claimed by the sun. (b) The moon halo circle is rendered at a fixed radius (r=120 in SVG units, ~192px effective) that may exceed the visible moon pocket or card bounds; no overflow handling or clip-path gating is in place to clip the ring gracefully or reposition it to stay fully in-frame.

## Current behavior
(a) `?debugOptic=halo` forces `sunHalo=0.95` only (line 1517); `lunarHalo` is computed from cloud/moon state but cannot be forced for isolated testing. (b) The moon halo `.mhalo` circle (line 400) renders at `r="120"` with CSS `opacity:var(--mhalo,0)` (line 168); when forced to opacity ~0.85 (line 1678), it paints a full circle in SVG space, which may clip at the card boundary (`overflow:hidden`, line 27) or extend outside the moon's in-frame pocket (below the temporary strap, above the arc), showing as a partial arc rather than a coherent ring.

## Desired behavior
(a) Add `?debugOptic=lunarhalo` to force the moon halo independently for QA (or another key like `moonhalo`). When set, force `lunarHalo` to a visible opacity (e.g., 0.85–0.95) so the ring can be inspected under any cloud condition. (b) Investigate the halo clip cause and either: (1) reduce the halo radius so it stays fully in-frame; (2) apply a clip-path or overflow handling to the moon SVG group so the ring clips coherently (not a jagged edge, a clean circle boundary); or (3) if a full ring cannot fit the card, document the limit honestly in OPTICS.md and accept the partial arc as a known approximation. The acceptance criterion is that the ring either reads as a coherent circle (entire or clipped gracefully) or the limit is explicitly documented.

## Code anchors (re-verify line numbers before editing)
**`index.html:500`**

````js
const DEBUGOPTIC = q.get("debugOptic");           // ?debugOptic=halo|sundogs|pillar|anticrep|paraselene → force a (condition-gated) optical phenomenon
````

**`index.html:1517`**
Debug optics forcing logic — no case for lunar halo.

````js
if(DEBUGOPTIC==="halo")sunHalo=0.95; else if(DEBUGOPTIC==="sundogs")sunDogs=0.95; else if(DEBUGOPTIC==="pillar")sunPillar=0.9; else if(DEBUGOPTIC==="anticrep")antiCrep=0.8; else if(DEBUGOPTIC==="paraselene")moonParhelia=0.9;
````

**`index.html:1503`**
Lunar halo gate (ice-crystal refraction, cirrus + bright moon).

````js
const lunarHalo  =clamp((clHigh-0.06)/0.34)*clamp((0.66-clHigh)/0.42)*(1-clLow)*(1-0.7*clMid)*moonLume;
````

**`index.html:1678`**
Moon halo opacity CSS prop write (screen-blend, fixed boost).

````js
c.style.setProperty("--mhalo",Math.min(0.85,1.5*A.lunarHalo).toFixed(3));     // 22° ice halo ring — only with thin cirrus (boosted so the ring reads through the cloud)
````

**`index.html:400`**
Moon halo SVG circle element at r=120 in scaled (0.62×) SVG space.

````js
<circle class="mhalo" r="120"/>                 <!-- 22° ICE-crystal halo ring (cirrus); shown only with thin high cloud -->
````

**`index.html:398`**
Moon group position: fixed translate + scale.

````js
<g class="moon" transform="translate(250 64) scale(0.62)">
````

**`index.html:168`**
Moon halo CSS: no overflow/clip-path gating; opacity is the only control.

````js
.mhalo{fill:url(#mhalog);mix-blend-mode:screen;filter:blur(2.5px);opacity:var(--mhalo,0);transition:opacity 1.8s}
````

**`index.html:27`**
Card overflow hidden — clipping boundary.

````js
color:var(--text);overflow:hidden}
````

**`OPTICS.md:113`**
Documented residual in OPTICS.md.

````js
(Forcing `?debugOptic=halo` forces the *sun* halo; the moon halo has no separate debug key — noted.)
````

**`HANDOFF.md:98`**
Documented residual clipping issue in HANDOFF.md.

````js
Optics are art-directed approximations, not photometric — but they now **register to the visible corner sun** (`--sunvx/--sunvy`), so the old "halo center-screen" bug is fixed. The moon's halo/paraselenae may still show as partial arcs (halo radius > the disc).
````

## Approach
**Step 1: Add the debug parameter (minimal wiring).** In the `DEBUGOPTIC` forcing block (index.html line 1517), add a new `else if` clause: `else if(DEBUGOPTIC==="lunarhalo")lunarHalo=0.95;` (or use `0.85` if 0.95 is too bright). This forces the lunar halo to a visible opacity regardless of cloud/moon conditions, allowing isolated QA. **Step 2: Investigate the clip cause.** In a test scene with `?debugOptic=lunarhalo&simWx=3&simMoon=0.8&simMoonAlt=45` (thin cirrus, bright moon high in the sky), measure the halo render area. The circle r=120 in 0.62× scale ≈ 193.5px logical radius; the moon group centre is at translate(250,64), meaning the halo extends to y=64±193.5 ≈ [−129.5, 257.5] in viewport units. The card is 325×530; the top is at 0, so the halo is clipped top. The moon's in-frame pocket is roughly y:64±(45px/0.62≈72.6px) ≈ [−8.6, 136.6], so bottom clipping is less severe. **Step 3: Choose a remedy.** (a) **Reduce radius:** The 22° ice halo should ring the moon's visual edge. At scale 0.62, the moon disc image is 96px; the halo should not much exceed it. Reduce r from 120 to ~95–100 so the full circle fits in-frame (trade: slightly tighter ring, less halo). (b) **Clip-path:** Apply `clip-path:circle(...)` to `.moon` group or use SVG `<clipPath>` to define a card-bounded circular clip; the halo then clips cleanly at the boundary, but the clipped arc reads as incomplete. (c) **Accept + document:** If neither is justified, update OPTICS.md to explicitly state "The moon halo may show as a partial arc because the ring radius exceeds the in-frame pocket" — this is honest and avoids a rushed fix. **Recommend (a)** because it preserves the ring's visual integrity and is the simplest change. Test with smoke.html (no dedicated moon-halo smoke yet, but visual inspection with `?debugOptic=lunarhalo` in a real preview). **Step 4: Update OPTICS.md comment** (line 113) to read `(A separate debug key ?debugOptic=lunarhalo now forces the moon halo; clipping is minimal/expected as the ring is large.)` or similar, to reflect the fix. **Step 5: Verify no regression.** Run the same scenes as in DESIGN.md QA matrix (clear night with moon, thin-cloud night, new moon) and confirm the moon, stars, and arc are unaffected. Ensure `?debugOptic=lunarhalo` and `?debugOptic=halo` do not interfere.

## Alternatives considered (and rejected)
- **Keep the debug key as is and document the limitation in OPTICS.md only.** — Defers the core testing pain: a QA engineer cannot force the moon halo in isolation to verify its condition gate or colour without also having to set up the right cloud/moon/time state every time. The doc note is nice-to-have but does not solve the practical workflow issue.
- **Add a new CSS variable like `--mhalo-force` that can be set directly via a style tag in the URL (e.g., a builder option).** — Out of scope for a single-file widget; the builder.html shares no JS with index.html (architectural rule). The debug params already exist for this use case.
- **Expand the halo radius further and accept the full clipping; paint the arc off-card.** — SVG overflow is controlled by the card's `overflow:hidden`, so it would not be visible and would offer no testing value. Defeats the purpose of the debug key.
- **Dynamically compute the halo radius based on moon position to fit in-frame.** — Over-engineered: the halo is a fixed geometric optic (22° ice-crystal refraction angle); varying its radius would break the realism contract. Better to pick a single optimal radius and stick with it.

## Owner / source touchpoints
- index.html:1517 (add `else if(DEBUGOPTIC==="lunarhalo")lunarHalo=0.95;` branch)
- index.html:400 (optionally reduce `r="120"` to `r="95"` or `r="100"` if clip remedy is chosen)
- index.html:113 in OPTICS.md (update the comment about the lack of debug key)

## Regression risks (forbidden-regression guardrails)
- If the halo radius is reduced, the visual ring becomes tighter/smaller — verify that it still reads as a coherent 22° phenomenon and doesn't look like a close aureole or corona. Smoke check: thin cirrus night with `?debugOptic=lunarhalo` should show a distinct ring with the red-inner/blue-outer gradient, not a glow.
- Adding a new `DEBUGOPTIC` case could accidentally interfere with existing cases if the string comparison is duplicated or if a typo is introduced (e.g., 'lunarhalo' vs 'moonhalo'). Verify case-sensitivity and exact spelling in tests.
- Changing the halo radius may affect the fade-out area if the gradient is tuned for r=120; test that the radial-gradient color stops still look right at the new radius. The gradient 'id=mhalog' (line 370) uses offset percentages; they scale proportionally to the radius, so should be OK, but visual inspection is needed.
- Forbidden regression: the moon must remain OPAQUE (stars never show through), moonlight must be physical-only (no fake glow on new moon), the moon's position in the pocket must not shift, and the arc/panel layout must be unaffected. These are unrelated to the halo fix but are touchpoints in the render path.

## Smoke A — capture BEFORE any change
- Baseline: Load `index.html?lat=24.47&lon=39.61&simTime=01:00&simWx=3&simMoon=0.8&simMoonAlt=45` (thin cirrus, bright moon, high altitude) and observe the moon halo's current opacity/clipping behaviour with ?debugOptic not set (lunarHalo gate active).
- Measure the moon's visual radius and the halo's full extent (with the moon's bounding box via `.moccluder` and visual extent of the halo circle; use `?debugMoon=1` to see layer radii).
- Take a screenshot with the baseline (halo gate inactive) and another with `?debugOptic=halo` (sun halo forced) to verify they don't interfere.
- Record the current halo radius in the SVG (r=120) and the moon transform (scale(0.62)) for reference in measurement.

## Smoke B — verify AFTER the change
- After adding the debug key: Load the same scene with `?debugOptic=lunarhalo` and verify lunarHalo is forced to ~0.95 opacity (check via `window.qaState().lunarHalo` or visual opacity in the CSS).
- Verify the halo ring renders at its full extent (top and bottom clipping, if any) and observe whether it reads as coherent or partial.
- If the radius is reduced, re-measure the halo extent and confirm it stays within the card bounds (y ∈ [0,530]) and the moon's in-frame pocket.
- Take a screenshot with `?debugOptic=lunarhalo` alone and confirm it DIFFERS from `?debugOptic=halo` (sun halo).
- Test the moon's calendar state (new moon + high moon): `?debugOptic=lunarhalo&simMoon=0.01&simWax=1&simMoonAlt=45` should show the moon as a faint opaque disc but with the halo ring forced to 0.95 opacity (moon opaque, halo visible, no moonlight).
- Verify the forbidden regressions: moon is opaque (no stars through, `--moonocc/--moongrp ~1`), arc and panel unaffected, and new/old debug optic keys don't cross-trigger.
- Run the QA matrix scenes from DESIGN.md (clear noon, sunrise, thin-crescent night, full moon, new moon, thin-cloud night with all optics — each with `?debugOptic=<key>`) and verify no visual regressions.

## Acceptance criteria (falsifiable)
- (a) `?debugOptic=lunarhalo` is a valid parameter that forces `lunarHalo` to a visible opacity (≥0.85) regardless of cloud/moon conditions, as confirmed by visual render or `qaState().lunarHalo`.
- (b) The moon halo ring renders either (i) fully in-frame with no clipping, or (ii) clipped gracefully at the card edge with a clean circular boundary, or (iii) documented in OPTICS.md as a known approximation.
- (c) The halo ring's colour (red-inner → blue-outer gradient) is visually intact and reads as a distinct 22° ice-crystal optic, not an aureole or glow.
- (d) `?debugOptic=halo` (sun halo) and `?debugOptic=lunarhalo` (moon halo) are independent; forcing one does not affect the other.
- (e) No forbidden regression: moon remains opaque (--moonocc/--moongrp ~1 at night), no stars show through, moonlight is physical-only (zero on new moon below horizon), arc and prayer panel layout are unaffected, and the QA matrix scenes all pass visual inspection.

## Rollback
`git diff index.html` should show only the addition of the `else if(DEBUGOPTIC==="lunarhalo")lunarHalo=0.95;` clause (1–2 lines) and optionally the radius change (r="120" → r="95"` if chosen, 1 line), and a 1-line update to OPTICS.md line 113. Revert by `git checkout -- index.html OPTICS.md`.

## Dependencies / sequencing
_(none)_

## Open questions
- (Deferred design choice) Should the halo radius be reduced from 120 to ~95–100, or should a clip-path be applied, or should the limitation be documented and the partial arc accepted? This is a style/correctness trade — recommend visual testing with a judge panel if the choice is unclear. (Currently recommending radius reduction as the simplest, least-risky approach.)
- (Clarification) OPTICS.md currently states 'halo/paraselenae may show as partial arcs (halo radius > the disc)' — is this an acceptable approximation or a known bug? The plan assumes it is acceptable IF documented, or fixable via radius reduction. Confirm the intent.
- (Future work, out of scope) The moon halo is described as 'art-directed approximations, not photometric' — should the 22° radius be tuned post-implementation based on live screenshots, or is the current SVG-space radius considered final?

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. CRITICAL: Step 3 must be rewritten to COMMIT to ONE remedy: (a) reduce r from 120 to 95 [and re-tune gradient offsets if visual testing shows regression], OR (b) apply a clip-path with specific (cx, cy, r) geometry [specify what this geometry is], OR (c) accept the partial arc and update OPTICS.md [specify the new comment text and rationale]. The plan as written leaves this open.
2. Acceptance criterion (a) must be revised to require VISUAL verification: 'The moon halo is visibly rendered with opacity ≥0.85 (confirmed by taking a screenshot with ?debugOptic=lunarhalo, not just checking qaState().lunarHalo).' The metric alone is insufficient.
3. Acceptance criterion (c) must be strengthened with a baseline: '... and visually matches [a screenshot of the moon halo under natural conditions, e.g., ?simWx=3&simMoon=0.8&simMoonAlt=45 without forcing] in terms of colour spread, ring tightness, and gradient fade. [Judge's visual sign-off required.]'
4. Acceptance criterion (e) must include explicit test scenes: 'Forbidden regression verified by running: (1) ?qa=1 to check moon opacity metrics, (2) ?debugOptic=lunarhalo&simWx=0&simMoon=0.01&simMoonAlt=-30 to verify no stars show through at new moon + clear sky, (3) the full QA matrix from DESIGN.md with ?debugOptic=lunarhalo in each scene.'
5. If remedy (a) is chosen (reduce radius), the plan must specify: (1) the new r value (e.g., 95 or 100), (2) whether gradient offsets must be re-tuned (and if so, what the new offsets are), and (3) a smoke test that compares the new halo's visual appearance (colour, ring definition, fade) against the baseline r=120 halo.
6. If remedy (b) is chosen (clip-path), the plan must specify: (1) the target clip-path geometry (e.g., 'circle(X px at 250px 64px scaled 0.62)'), (2) whether this is a CSS clip-path on .moon or an SVG <clipPath>, and (3) a smoke test that verifies the halo clips cleanly (not jaggedly) at the boundary.
7. SmokeB must include a UNIFIED test for criterion (d): Load `?debugOptic=halo&debugOptic=lunarhalo&simWx=3&simMoon=0.8` and verify that (1) both optics are forced to 0.95 (or last-one-wins if that's the designed behavior), and (2) the sun halo and moon halo do not interfere with each other's CSS props or visibility.
8. SmokeB must add a CSS-consistency check: After loading `?debugOptic=lunarhalo`, call `getComputedStyle(document.querySelector('.c')).getPropertyValue('--mhalo')` and verify it is ≥ 0.85. This ensures the CSS prop write (line 1678) is actually applied, not just the state metric.
9. The plan must explicitly document the TDZ and render-order invariants: 'lunarHalo is declared at line 1503 (before the debug-forcing block at line 1517), so the order is safe. moonSky.alt (used at line 1516 in moonParhelia) is set by renderMoon() (line 1775) before atmosphere() is called (line 1805 via applyTheme), so the moon-state temporal coupling is preserved. Future edits that move the debug-forcing code or change the render order must maintain these invariants.'

**Missing risks the spec omitted:**
- The plan's Step 3 leaves the halo-clipping remedy OPEN (reduce radius vs. clip-path vs. accept+document) without committing to one, creating implementation ambiguity. A partial implementation that adds the debug key but does NOT reduce the radius or apply a clip-path may still show partial arcs, leaving the core visual problem unsolved.
- The gradient offsets in id="mhalog" (lines 370–377) use percentage stops (55%, 62%, 68%, 75%, 86%) relative to the gradient's r attribute, not the circle's r. If the circle radius is reduced from 120 to 95 without re-tuning the gradient stops, the visual appearance of the ring (tightness, colour spread, falloff) will change in unpredictable ways. The plan lists this as a regression risk but does NOT include a verified baseline in the acceptance criteria.
- Acceptance criterion (c) requires the halo to 'read as a distinct 22° ice-crystal optic, not an aureole or glow,' but the smoke tests include only a single `?debugOptic=lunarhalo` screenshot, not a side-by-side comparison with a known-good baseline. A visually broken halo (e.g., a glow instead of a ring, or a misaligned gradient) could still pass.
- Acceptance criterion (e) lists multiple sub-checks ('moon remains opaque', 'stars never show through', 'moonlight is physical-only', 'arc/panel unaffected') but does NOT specify the test scenes or the verification method (screenshot, qaState, manual inspection). Some checks (e.g., 'stars never show through at new moon') require specific dark-sky conditions that are not explicitly tested.
- The plan's calculation of the halo clipping extent ([−129.5, 257.5] in viewport y) is correct but the plan does NOT explain what this means for the remedy or whether the card [0, 530] boundary justifies a clip-path at a specific (cx, cy, r) — this leaves ambiguity about how a clip-path remedy would actually work.
- The plan does NOT verify that the CSS props --mhalo and --moongrp are independent and that forcing --mhalo to 0.95 does NOT inadvertently affect moon opacity or the occluder. While the code shows they are independent, the plan should articulate this invariant.
- The plan recommends reducing the halo radius to 95–100 as 'the simplest, least-risky approach' but does NOT provide a measured justification (e.g., 'at 95px the halo fits fully in-frame and matches the 22° angle expectation'). The recommendation is qualitative, not quantitative.
- The smoke tests include a check for `qaState().lunarHalo ≈ 0.85–0.95` but do NOT verify that this state actually manifests as a visible CSS opacity applied to the SVG circle. If the CSS prop write (line 1678) is accidentally broken, the state would be high but the visual halo would be invisible, and the test would not catch it.

**Weak acceptance criteria (a broken change could still pass):**
- Criterion (a) — 'confirmed by visual render or qaState().lunarHalo' — accepts a METRIC without verifying VISUAL consistency. A broken gradient or missing CSS prop could cause qaState() to show 0.95 while the halo is invisible or malformed.
- Criterion (c) — 'reads as a distinct 22° ice-crystal optic' — is subjective ('distinct', 'reads as') without a baseline screenshot or a judge's sign-off. A glow that happens to be blue-tinged could be claimed as 'reading as optic-like' and pass.
- Criterion (d) — 'are independent; forcing one does not affect the other' — is tested separately in smokeB (halo alone, lunarhalo alone) but not together. If DEBUGOPTIC is parsed left-to-right and the last case overwrites earlier ones, simultaneous forcing could fail silently.
- Criterion (e) — 'no forbidden regression: moon remains opaque' — lists multiple checks but does NOT specify how to verify 'stars never show through' at the edge case (new moon, clear sky, full darkness). The QA matrix in DESIGN.md does include 'new moon (a faint ashen OPAQUE calendar disc — never moonlight)' but the smoke tests do NOT explicitly run this scenario with the debug-key forced.

**Scope concerns:**
- The plan's Step 3 offers three mutually exclusive remedies but recommends one without a decisive argument. This creates scope ambiguity: is the implementation ONLY the debug-key addition (1 line), or must it also include the radius reduction (1 additional line) or a clip-path (3+ additional lines)? The plan should commit to ONE remedy.
- The plan's 'Step 4: Update OPTICS.md' proposes a one-line comment change, but if the remedy chosen is (c) 'accept+document', the comment must be MORE substantial (documenting the partial-arc limitation, the card geometry, and the design choice). The plan underestimates the doc work for remedy (c).

**Grounding issues (claims to re-check against current code):**
_(none)_

**Reviewer notes:** The plan's core idea is sound: add a debug parameter to force the moon halo independent of the cloud/moon state for QA testing, and optionally address the residual clipping issue. The grounding (line numbers, code quotes, doc references) is CORRECT. However, the plan leaves the ROOT CAUSE unresolved: it offers three possible remedies for the halo clipping (reduce radius, clip-path, accept+document) but recommends one without justification and does not commit to any. This creates two execution risks: (1) an implementation that adds the debug key but does NOT fix the clipping, leaving the visual problem unsolved, and (2) an implementation that reduces the radius without re-tuning the gradient, causing a visual regression. The acceptance criteria are also weak on verification: they accept qaState metrics without visual confirmation, and they use vague language ('visually intact', 'reads as distinct') without baseline references or judge sign-off. The plan should be rewritten to commit to a single clipping remedy (preferably with a measured argument for why), tighten the acceptance criteria to require visual verification and baseline comparisons, and expand the smoke tests to catch CSS-consistency failures (e.g., state high but opacity not applied). The TDZ and render-order invariants are NOT violated but should be explicitly documented. Overall verdict: NEEDS-FIXES because the scope ambiguity (which remedy?) and weak acceptance criteria could result in a partial or visually incorrect implementation passing review.
