# Plan 08 — Faithful false-dawn (zodiacal light) — implementation plan or deferred spec

> **Status:** ⏸️ DEFERRED — terminal decision (2026-06-16): **kept unbuilt**, as designed. The user explicitly rejected a painted false-dawn cone/slash, and a *faithful* zodiacal cue needs inputs the 2-D widget does not have (true ecliptic-tilt projection) plus strict dark-sky/no-moon/low-LP gating; building anything less would reintroduce the rejected artefact. This plan stays as the buildable spec for a future implementer. **User re-confirmed (2026-06-16):** keep it terminally deferred + unrendered in production; a faint generic eastern wedge is NOT enough; **do not spend further engineering unless it becomes a separately-scoped research-quality optic.** If ever attempted, the MINIMUM bar is: true ecliptic-tilt projection (or an equivalently defensible ecliptic approximation), strict dark-sky gating, low/no moonlight, low light-pollution, clear/low-cloud horizon, and extremely faint opacity — visually distinct from physical twilight, never implying Fajr, never replacing the real twilight sky, off the instant any gate fails. **Its safe pre-req WAS done:** the stale, self-contradicting `index.html` comment claiming false dawn "IS painted … (gates below)" was deleted (doc-hygiene #1) — code/comments now consistently state false dawn is NOT rendered. `trueDawnTwilight` remains a qaState-only diagnostic; smoke still asserts no `.falsedawn`/`.truedawn` elements.  ·  **Class:** feature  ·  **Priority:** P2  ·  **Effort:** M  ·  **Risk:** med
> **Do now?** Deferred (keep unbuilt until faithful)  ·  **Plan-review verdict:** `needs-fixes` (8 required fixes — see end)  ·  **Depends on:** 1 — see "Dependencies / sequencing"
>
> Read-only plan from `/implementaudit` (workflow `wf_f498de17-f7b`, investigate → adversarial critique). Grounded against `index.html` @ commit `91d0fc1` (~1951 lines). **No source was changed.** Line numbers drift — re-verify the anchors before editing.

> **Maintainer note (added during synthesis, 2026-06-16):** The first code anchor below quotes a **stale,
> self-contradicting comment** at `index.html:1483–1484` claiming false dawn *"IS painted … (gates below)."*
> That is wrong: the operative code (line 1492) computes only the `trueDawn` **diagnostic** scalar, nothing is
> painted, there are no such gates, and the corrected comment immediately below it (1487–1490) plus line 1670
> confirm *"false dawn is not rendered."* The plan's prose ("Current behavior: false dawn is NOT rendered") is
> the accurate description. **Pre-req cleanup for this plan (and a doc-hygiene fix in its own right): delete the
> stale 1483–1484 comment** so it can never mislead a future implementer into thinking a paint path already
> exists. This is exactly the kind of leftover the user's false-dawn removal was meant to eliminate.

## Problem
The widget currently does NOT render false dawn (al-fajr al-kādhib / zodiacal light). A generic CSS cone was removed because it read as a lens-flare/godray slash and showed under a bright moon (fail-closed). The OPTICS.md and DESIGN.md specs call this "future work only" and require a faithful implementation to honour: ecliptic-tilt projection (NOT a fixed diagonal), eastern pre-sunrise anchor, triangular/wedge falloff, STRICT dark-sky + low/no-moon + low-LP + clear/haze gating, very low opacity, NO foreground-crossing slash, and ZERO effect on Fajr/UI state. The question: is this buildable within a 2-D canvas/CSS widget, or should it remain deferred with a precise spec for a future implementer?

## Root cause
False dawn is an astrophysical phenomenon — sunlight scattered by interplanetary dust along the ecliptic plane — that requires knowing the ecliptic's true 3-D orientation projected to the 2-D screen. The widget does NOT currently compute ecliptic tilt or derive it from the location's latitude, the season (solar declination), and time (hour angle). Without this input, any false-dawn cue is a fixed diagonal or radial shape, which the user explicitly rejected as reading like a painted lens-flare/godray. The previous attempt (a generic CSS cone) was abandoned correctly.

## Current behavior
False dawn is NOT rendered. The `trueDawnTwilight` scalar exists in the atmosphere state vector (line 1565 in index.html, currently called `trueDawnTwilight` but documented as a diagnostic-only). It paints nothing. The DEBUGDAWN parameter (line 499) is a deprecated no-op. The DESIGN.md comment (lines 75–77) states false dawn is "future work only" and lists the required properties. OPTICS.md (lines 37–43) documents the removal and the gating spec.

## Desired behavior
Either: (1) A faithful zodiacal-light cue that only appears when the ecliptic is in the eastern pre-sunrise sky, the sky is genuinely dark, the moon is dim/low/new, light pollution is low, the air is clear/low-haze, and visibility is good — OR (2) A DEFERRED spec that documents exactly what a future implementer must add to the codebase to make (1) possible.

## Code anchors (re-verify line numbers before editing)
**`index.html:1481–1492`**
Current code: trueDawn is a diagnostic scalar, never painted; false dawn is explicitly deferred.

````js
// DAWN. TRUE dawn (al-fajr al-ṣādiq) is NOT painted as a separate layer — it IS the real physical twilight
// (skyLum's astronomical→nautical→civil progression + the warm horizon scatter at the sun's azimuth, all above)
// plus the Fajr marker/time on the arc. `trueDawn` below is kept ONLY as a 0..1 DIAGNOSTIC scalar (qaState), not
// rendered. FALSE dawn (al-fajr al-kādhib, the zodiacal cue) IS painted — a real phenomenon the twilight engine
// doesn't produce — but only as a RARE, FAINT, FAIL-CLOSED cue (gates below); it never drives the prayer clock.
const dep=-sm.altDeg, morning=M.nowMin<M.noon, clearish=(cls==="clear"||cls==="cloud"||cls==="fog");
// TRUE DAWN is the physical twilight sky (the gradient/glow above) + the Fajr marker — NOT painted. `trueDawn`
// is kept ONLY as a 0..1 DIAGNOSTIC scalar (qaState), never rendered. FALSE DAWN (zodiacal light) is NOT rendered
// at all (fail-closed): a generic CSS cone read as a decorative lens-flare slash and showed under a bright moon.
// A faithful zodiacal cue is FUTURE WORK (needs real ecliptic-tilt projection + strict dark-sky/no-moon/low-LP/
// clear-sky gating + very faint, no foreground-crossing streak, never implying Fajr). See DESIGN.md.
const trueDawn = (morning&&clearish) ? clamp((17.5-dep)/3.0)*clamp(dep/1.5) : 0;
````

**`index.html:1565`**
trueDawn (false dawn) is exported in the atmosphere state vector as trueDawnTwilight (misnamed in the return object — should clarify whether this is false or true dawn diagnostic).

````js
antiX: 100-sm.x, belt, airglow:[airCol[0],airCol[1],airCol[2],airCol[3]], aurora, trueDawnTwilight: trueDawn,
````

**`index.html:75–81 (CSS)`**
CSS comment clearly states the requirements and failure reason.

````js
/* DAWN — NEITHER false nor true dawn is a painted overlay (fail-closed). TRUE dawn IS the real physical twilight
   sky (the skyLum astronomical→nautical→civil progression + the warm horizon scatter at the sun's azimuth) plus the
   Fajr marker  ime on the arc. FALSE dawn (al-fajr al-kādhib \ zodiacal light) is NOT rendered: a generic CSS cone
   read as a decorative lens-flare slash and showed under a bright moon, so it was removed. A faithful zodiacal-light
   cue is FUTURE WORK only — it would require true ecliptic-tilt projection, strict dark-sky + low/no-moon + low
   light-pollution + clear-sky gating, very faint opacity, no foreground-crossing streak, and must never imply Fajr.
   See DESIGN.md › "False dawn vs true dawn". */
````

**`DESIGN.md:72–77`**
Design spec clearly documents why it was removed and what is required for a faithful implementation.

````js
**False dawn** (al-fajr al-kādhib, the zodiacal light) is **NOT rendered.** A generic CSS cone was tried and
  removed: unmodeled, it read as a decorative lens-flare/godray slash and (wrongly) showed under a bright moon.
  Rather than ship an inaccurate cue, the widget **fails closed** — it shows nothing for false dawn.
- **Future work (only):** a faithful zodiacal-light cue would require a real ecliptic-tilt projection, strict
  dark-sky gating, low/no moonlight, low light-pollution, clear sky / minimal low cloud, very faint opacity, no
  foreground-crossing streak, and it must never imply Fajr has entered. Until all of those hold, it stays unbuilt.
````

**`OPTICS.md:37–43`**
Optics spec: the precise required properties for a faithful zodiacal-light cue.

````js
### False dawn (zodiacal light) — *NOT rendered (future work)*
- **Family:** sunlight scattered by interplanetary dust along the ecliptic.
- **Status:** **disabled in production.** A generic CSS cone read as a lens-flare/godray slash and showed under a
  bright moon, so it was removed (fail-closed).  **Verdict:** removed.
- A faithful future implementation must use: projected ecliptic orientation (not a fixed diagonal), eastern
  pre-sunrise anchor, triangular/wedge falloff, strict dark-sky + low/no-moon + low-light-pollution + clear/haze
  gating, very low opacity, no foreground-crossing slash, and no effect on Fajr/UI state.
````

## Approach
RECOMMENDATION: **DEFER** with a concrete, executable spec. The reason: the widget does not currently compute the ecliptic plane's true 3-D orientation (ecliptic tilt relative to the horizon) for a given lat/lon/time/season. Deriving this requires: (1) the solar declination (seasonal axis tilt — already available in `drawArc` via a fit clamp, but not exported to `atmosphere`), (2) the sun's hour angle (available as part of the solar-elevation calc), and (3) the anti-solar azimuth (already computed as `--antix`). With these, the ecliptic's inclination on the screen can be projected, allowing a faithful wedge-shaped cue that tilts with the season and latitude, not a static diagonal. **The minimal deferred spec:**

1. **Compute ecliptic tilt:** In `atmosphere()`, after `sunMetrics(M)` (line 1407), derive the ecliptic's apparent slope on the screen:
   - Extract or compute the solar declination δ (currently fit in `drawArc`, lines 1004–1147, but not available to `atmosphere` — small refactor needed).
   - The ecliptic's inclination to the horizon is driven by `obliquity ≈ 23.44°`, the observer's latitude φ, the sun's hour angle H, and the season (δ).
   - Project this to screen angle: `eclipticTiltDeg = f(lat, H, δ, obliquity)` (a real spherical-trig formula, ~3 lines).
   - Export as a new `atmosphereState` field: `eclipticTilt`.

2. **Gate the cue:**
   - `morning && clearish` (already computed, line 1486).
   - `sm.altDeg < −8°` (sun well below twilight, so zodiacal light doesn't read as Fajr).
   - `moonObject < 0.2` (moon is dim, new, or below horizon — gates moonLight wash).
   - `LPOLL < 0.3` (not light-polluted; low-LP requirement).
   - `clLow + clMid < 0.4` (clear to broken-cloud, no overcast deck; blocks low cloud).
   - `D.haze < 0.5` (not hazy; aerosol-optical transparency needed).
   - Composite gate: `falseDawn = morning && clearish && (sm.altDeg < −8) && (moonObject < 0.2) && (LPOLL < 0.3) && (clLow + clMid < 0.4) && (D.haze < 0.5) ? [0..0.08] : 0` (very low opacity floor).

3. **Render approach:**
   - In `paint()` (line 1535+), add a new CSS custom prop: `--falsedawn-tilt: <eclipticTiltDeg>` and `--falsedawn-op: <opacity>`.
   - Add CSS `.atmo .falsedawn` rule with a **radial gradient** (or conic) anchored to `var(--antix)` (sun's azimuth), tilted by `rotate(var(--falsedawn-tilt))`, with a **triangular/wedge falloff** (using a `mask-image` radial-gradient, hard 0% to soft 100%), opacity `var(--falsedawn-op)`, `mix-blend-mode: lighten` or `screen` (to avoid occlusion under clouds), and a **very low saturation** (pale golden, ~rgba(220, 200, 100, 0.04) blended with the sky tone).
   - **Critical:** anchored ONLY to the anti-solar point (`--antix`, which follows the sun's azimuth from east→west), never to the visible corner sun (`--sunvx/--sunvy`). This keeps it "geographically anchored," not a visual decoration.

4. **Validation (false-dawn-specific):**
   - Never shows if moon is bright (moonObject > 0.2).
   - Disappears before dawn brightens to civil twilight (sm.altDeg > −6°).
   - Tilts with ecliptic for the observer's latitude (test: equator vs ±60° should show different tilt angles).
   - Zero effect on Fajr time, the arc, or the UI (purely visual).
   - Does NOT read as a lens-flare slash or a fixed diagonal.

If this spec is accepted, the implementer must:
- Add a `declination` helper or export the fit from `drawArc`.
- Add `eclipticTilt` computation to `atmosphere`.
- Add the gating logic (5 conditions above).
- Add the CSS rule + `paint()` assignments.
- Test under the acceptance criteria below.

If the spec is rejected (e.g., "the 2-D projection is still too approximate"), the feature remains deferred indefinitely.

## Alternatives considered (and rejected)
- **Implement a minimal false-dawn cue now using a fixed-angle wedge (ecliptic tilt approximated as constant ≈23°)** — Violates the "not a fixed diagonal" requirement. The ecliptic tilt DOES vary significantly with latitude and season — at the equator it's nearly vertical; at ±60° it's shallow. A fixed 23° would look wildly wrong at high latitudes. User feedback explicitly rejected static slashes.
- **Use a photometric model to estimate zodiacal-light brightness from heliocentric distance and scattering angle** — Overkill for a 2-D canvas widget. The widget is already "art-directed approximations, believable, not photometric" (DESIGN.md:267). A calibrated gate (5 conditions above) is sufficient for truthfulness — it fails closed when conditions don't support the cue.
- **Add false dawn as a debug-only feature under ?debugOptic=falsedawn** — The spec requires false dawn to be GATED, not forced. Forcing it under bad conditions (bright moon, overcast, noon) would be a lie. Debug forcing is valid for OPTICS that have a clear physical condition (halo = have cirrus), but false dawn's gating is complex and multi-faceted; forcing it would immediately violate truthfulness.
- **Implement it as a painted DOM element (not CSS) for more control** — Breaks the static/no-build/single-file constraint. All visual effects are CSS-driven or canvas (clouds); painting a DOM false-dawn layer would require JS geometry math on every frame, which is slower than CSS gradients and couples render() more tightly. The CSS approach is sufficient for a wedge shape.
- **Reuse the existing crepuscular-ray machinery (the .godray conic) and gate it differently** — Godray is a CONIC from the visible sun (`--sunvx/--sunvy`), radiating outward. False dawn is a WEDGE from the azimuth (`--antix`), tilted by ecliptic. The shape, anchor, and gate are fundamentally different. Coupling them would create confusion and make regression easier.

## Owner / source touchpoints
- index.html:1407 (atmosphere signature: add ecliptic computation)
- index.html:1486–1492 (dawn-gating logic: enhance falseDawn gate)
- index.html:1534–1568 (atmosphere return object: add eclipticTilt, falseDawnOpacity fields)
- index.html:1670 (paint comment: update no-dawn note)
- index.html:1666–1676 (paint CSS-prop assignments: add --falsedawn-tilt, --falsedawn-op)
- index.html:75–81 (CSS: add .atmo .falsedawn rule)
- index.html:499 (DEBUGDAWN param: keep as no-op or repurpose to ?debugOptic=falsedawn)

## Regression risks (forbidden-regression guardrails)
- Painting a false-dawn layer that shows during the day or under a bright moon (violates fail-closed + truthfulness gate)
- A tilted cue that reads as a diagonal slash or lens-flare, not as 3-D celestial geometry (violates user rejection of static cone)
- False dawn showing OVER the foreground text/arc, appearing to bracket Fajr (violates "no effect on Fajr/UI state" — ensure z-index is low, behind prayer panel)
- Ecliptic tilt computed incorrectly at high latitudes or near solstice, causing the cue to point in the wrong direction (test latitude sweep)
- Adding a new `eclipticTilt` field to `atmosphere` without ensuring it stays at 0 when false dawn is gated to 0 (no stale optics leaking)
- CSS variable `--falsedawn-tilt` is set on every frame — ensure this doesn't slow the paint loop or cause layout thrashing

## Smoke A — capture BEFORE any change
- Baseline (BEFORE implementation):
- 1. qaState() does NOT include falseDawnOpacity or eclipticTilt fields.
- 2. tests/smoke.html reports NO false-dawn painted layers (`.falsedawn` does not exist in the DOM).
- 3. Inspect the CSS: `.atmo .falsedawn` rule does NOT exist in the stylesheet.
- 4. At dawn with clear sky, new moon, low LPOLL, sun at −20°: no visible cue appears.
- 5. Under ?debugLayers=1, no 'false dawn' opacity is logged.

## Smoke B — verify AFTER the change
- After deferred spec acceptance (minimal post-spec setup, before full implementation):
- 1. qaState() includes falseDawnOpacity (0 or numeric) and eclipticTilt (degrees) fields.
- 2. Eclipse-tilt computation returns sensible values: varies with lat/season/time, not constant.
- 3. At dawn with clear sky, new moon, low LPOLL, sun at −20°: false-dawn cue is faintly visible as a pale wedge from the eastern horizon, tilted according to the ecliptic.
- 4. At dawn with bright full moon: cue disappears (gated by moonObject < 0.2).
- 5. At dawn with overcast (clLow + clMid > 0.5): cue disappears (gated by low/mid cloud).
- 6. At noon: cue absent regardless (gated by morning && sm.altDeg < −8).
- 7. At sunrise/sunset high-latitude (e.g., lat=60): ecliptic tilt is shallow, not steep (visually correct, not a fixed angle).
- 8. The cue does NOT appear over the prayer list/arc (z-index 0, behind all foreground).
- 9. Under ?debugLayers=1, falseDawnOpacity is logged and changes with gating conditions.
- 10. Fajr time/UI unchanged; the cue is purely visual, zero effect on computation.

## Acceptance criteria (falsifiable)
- The false-dawn cue NEVER renders when the moon is bright (qaState().moonObject >= 0.2).
- The cue NEVER renders when low+mid cloud cover (clLow + clMid) exceeds 40% (overcast/partly cloudy blocks it).
- The cue NEVER renders when LPOLL >= 0.3 (light-polluted skies).
- The cue NEVER renders when haze (D.haze) >= 0.5 (murky air blocks it).
- The cue NEVER renders when solar elevation is above −8° (Civil twilight threshold; after that the morning sky is too bright and zodiacal light is invisible).
- The cue NEVER renders during daytime (sm.altDeg > 0).
- The cue's tilt angle (eclipticTilt) is visibly DIFFERENT at lat=0° (equator) vs lat=60° (high), and shifts between equinox and solstice (test qaState() for eclipticTilt field values, or visual inspection).
- The cue does NOT read as a fixed diagonal slash or lens-flare — it appears as a pale, diffuse, triangular glow anchored to the eastern horizon, consistent with zodiacal light.
- A screenshot of a dawn scene (clear, new moon, low LP) shows the cue as a barely-visible pale golden wedge from the east, NOT as a bright decorative element.
- The cue has zero effect on Fajr time/marker: the arc, countdown, and prayer list are unchanged.
- Fajr comes from the astronomical/nautical/civil twilight progression (skyLum + the physical sky), not from the false-dawn cue.
- Under ?qa=1, qaState().sky.falseDawnOpacity is present and reflects the gate (0 when moon is bright, >0 when clear/dark).
- No regression: the true dawn (physical twilight + Fajr marker) remains unchanged; no painted true-dawn band appears.

## Rollback
["If the ecliptic-tilt projection is found to be mathematically flawed (e.g., the formula produces incorrect angles at high latitudes):", "- Revert the `eclipticTilt` computation to a constant/approximation or remove false dawn entirely.", "- Clear the `--falsedawn-*` CSS props in paint().", "- Comment out or remove the `.atmo .falsedawn` CSS rule.", "- Remove falseDawnOpacity/eclipticTilt from the atmosphere return object.", "If users report the cue looks wrong (e.g., points in the wrong direction, tilts when it shouldn't):", "- Verify the gating logic: turn off false dawn if sun > −8°, moon > 0.2, haze > 0.5, LPOLL > 0.3, or cloud > 40%.", "- If gating is correct but the visual still reads as a slash/lens-flare, the 2-D projection is insufficient and the feature must be deferred again until a 3-D scene-graph widget is possible.", "Full rollback is low-risk: the feature is currently disabled (falseDown = 0 always), so reverting only removes the new code, no prior state to corrupt."]

## Dependencies / sequencing
- ecliptic-tilt computation requires a `declination` value to be available in `atmosphere()` — currently it is fit in `drawArc()` (lines 1004–1147) and not exported. A small refactor is needed to either (a) compute declination once at the start of atmosphere() using the same fit or (b) pre-compute it at the top level and pass it in as a parameter. Option (a) is preferred (no coupling increase).

## Open questions
- 1. **Ecliptic-tilt math:** Is the spherical-trig formula `eclipticTiltDeg = f(lat, H, δ, obliquity)` correctly approximated as a 2-component function (season + hour angle modulated by latitude)? A full derivation and test at equator/high-lat/solstice is needed before implementation.
- 2. **Render anchor choice:** Should the cue be anchored to `--antix` (sun's azimuth, 0°–100%) or the anti-solar point directly? Anchoring to `--antix` makes it rotate with the sun, but false dawn is a property of the ecliptic, not the sun's azimuth. At sunset (sun in the west), a faint false dawn might be visible on the *eastern* horizon — but the anti-solar point is westerly. Should the cue appear *opposite* the sun? (Research: zodiacal light is visible in the direction of the ecliptic's node closest to the observer, which varies with season/time/latitude.)
- 3. **Gating threshold tuning:** Are the hard gates (moon < 0.2, LPOLL < 0.3, cloud < 0.4, haze < 0.5, altDeg < −8) physically justified, or are they art-direction approximations? Should they be parametrized or user-tunable?
- 4. **Opacity floor:** Is 0.04 (very pale, barely-visible) the right opacity, or should it be even fainter (0.02) or richer (0.08)? This requires real-sky observation or reference photos.
- 5. **Should false dawn be a user-configurable gate?** E.g., a `?falsedawn=enabled` param to turn the cue on/off? Currently the widget has no feature toggles, only debug overrides. If false dawn is controversial, a quiet opt-in may be prudent.
- 6. **Future-proofing:** Should the spec explicitly document that a 3-D scene-graph (WebGL) widget could render zodiacal light more faithfully (as a tilted cone in 3-D space)? Or keep the spec narrowly scoped to CSS-only?

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. FIX #1 (critical): Provide the ecliptic-tilt formula or a reference. The plan states 'eclipticTilt = f(lat, H, δ, obliquity)' is a 'real spherical-trig formula, ~3 lines' but does not give the formula. Before implementation, provide: (a) the exact formula in pseudocode or a Meeus chapter reference, (b) test vectors at equator/±30°/±60° latitude for equinox/solstice, and (c) verification that the formula matches the expected geometry (ecliptic is vertical at the equator, nearly horizontal at high latitudes). Without this, the implementer must derive the math cold, risking a broken implementation.
2. FIX #2 (critical): Refactor declination export to avoid duplication and sky-arc divergence. The plan calls for declination to be available in atmosphere(). Specify ONE of: (a) Compute declination ONCE in model() and return it so both drawArc and atmosphere receive the same value (preferred, zero coupling), (b) Export a 'declination' helper function used by both drawArc and atmosphere (with a comment that they MUST stay in sync), or (c) Document the exact line-for-line code duplication needed and add a comment linking the two. Do NOT leave this as 'a small refactor'—spell out the code location, the new/changed lines, and the synchronization guarantee.
3. FIX #3 (critical): Define the ecliptic-tilt render anchor. The plan uses '--antix' (sun's azimuth) but OpenQuestion #2 flags that zodiacal light is 'a property of the ecliptic, not the sun's azimuth'. At sunset (sun in the west), should false dawn still appear on the eastern horizon (opposite the sun)? Or only in the eastern pre-sunrise? The spec says 'eastern pre-sunrise anchor' but does NOT clarify whether the cue should appear at dusk on the OPPOSITE side. Add a subsection to the spec: 'Render anchor: ...' with the answer. Without clarity, the implementer may anchor it to the wrong azimuth.
4. FIX #4 (critical): Provide the gating-threshold justification or make them parametrized. The plan lists hard thresholds: moon < 0.2, LPOLL < 0.3, cloud < 0.4, haze < 0.5, altDeg < −8. The spec says these are 'art-direction approximations' but does NOT cite observational data, literature, or user feedback. Either: (a) Justify each threshold with a reference (e.g., Meeus, USNO, or a user report), or (b) Mark them as 'TUNABLE' and provide a mechanism to adjust (e.g., ?falseDawnGate=moon:0.3,LPOLL:0.4). This prevents a future user or maintainer from wondering 'why 0.2 and not 0.25?'
5. FIX #5 (required): Specify the TDZ/declaration order guarantee for the new eclipticTilt and falseDawnOpacity fields. The plan states to add them to the atmosphere() return object (line 1534+). Verify: (a) that all upstream uses of clLow/clMid/clHigh are placed AFTER their declaration (line 1496), and (b) that the new falseDawn computation is placed AFTER cloudSunCol (line 1474), since the spec mentions 'very low saturation (pale golden, ~rgba(220, 200, 100, 0.04) blended with the sky tone)' — if this blend uses A.cloudSunCol, it must be available. Add a comment block: '// FALSE DAWN (zodiacal light) — computed below, uses cloudSunCol (line 1474) which is AFTER clLow/clMid/clHigh declaration'.
6. FIX #6 (required): Provide CSS rule with explicit z-index and mask-image details. The spec calls for 'a radial gradient (or conic) anchored to var(--antix), tilted by rotate(var(--falsedawn-tilt)), with a triangular/wedge falloff (using a mask-image radial-gradient)'. But CSS mask-image with a radial-gradient is non-trivial (the gradient must be radial FROM the anti-solar point, not from the screen center). Provide the FULL CSS rule, including: (a) the mask-image formula with exact parameters, (b) z-index: 0 explicitly set, (c) a comment linking to DESIGN.md #False-dawn-vs-true-dawn, and (d) mix-blend-mode (the spec suggests lighten or screen, which are different—clarify which is correct).
7. FIX #7 (required): Add smokeA/smokeB test for eclipse-tilt computation. The spec includes a detailed smokeA/smokeB, but smokeB step #7 says 'At sunrise/sunset high-latitude (e.g., lat=60): ecliptic tilt is shallow, not steep'. This is a VISUAL test (screenshot), not a qaState metric. The plan must specify: (a) the EXACT URL parameter combo to test (e.g., ?qa=1&lat=60&simTime=EQUINOX&simMoon=new&simWx=clear&simPrecip=0), (b) the EXPECTED visual (e.g., 'a pale wedge tilted ~15° from the horizon, not 45°'), and (c) a reference screenshot or luma threshold if available. Without this, smokeB is unexecutable.
8. FIX #8 (required): Clarify acceptance-criterion #7 with a pixel-diff tolerance. Criterion #7 says 'eclipticTilt is visibly DIFFERENT at lat=0° vs lat=60°'. Specify: (a) the MINIMUM tilt delta (degrees) that is visibly detectable on a 325px widget (e.g., '>5° difference is obvious, >2° is subtle, <1° is imperceptible'), and (b) the expected tilt values at equator vs ±60° latitude at equinox/solstice (e.g., 'At equinox, equator ≈90°, ±60° ≈30°'). Without numbers, the criterion is unverifiable.

**Missing risks the spec omitted:**
- REGRESSION RISK (TDZ ordering): The spec calls for ecliptic-tilt computation in atmosphere() 'after sunMetrics(M)' at line 1407. But declination is NOT currently available to atmosphere() — it is computed locally in drawArc (line 1015) and sunAltAt (line 1169). The spec says 'small refactor needed' to either (a) compute declination in atmosphere() or (b) pass it as a parameter. HOWEVER: if declination is recomputed in atmosphere() WITHOUT identical logic to drawArc/sunAltAt, the sky physics will diverge from the arc (a FORBIDDEN regression: 'sunrise glow must fire when the arc's sunrise dot is on the horizon'). The plan underestimates this risk.
- REGRESSION RISK (false dawn visible under bright moon): The spec gates false dawn with 'moonObject < 0.2'. moonObject is computed at line 1418 as 'moonUp*darkness*phaseVis' — this value is present and correct. But the plan does NOT verify that a moonObject=0.19 (barely below threshold) passes a visual inspection test of 'moon is genuinely dim/new/low', not just a metric. Pixels > metrics.
- REGRESSION RISK (ecliptic tilt formula untested): The spec mentions a 'real spherical-trig formula ~3 lines' for ecliptic tilt but provides NO formula, test values, or verification that it produces correct angles at high latitudes or near solstice. The 'openQuestions' section flags this as TBD. A broken formula (e.g., constant 23°) will silently produce a static diagonal, violating the 'not a fixed diagonal' requirement.
- REGRESSION RISK (z-index/layer order): The plan states the cue must be 'z-index 0, behind prayer panel'. But NO plan modification ensures z-index is explicitly set or tested. If the CSS rule is placed carelessly, it could render OVER the arc/prayer list, violating the 'no effect on Fajr/UI state' requirement.
- REGRESSION RISK (opacity floor leakage): The plan mentions 'ensure eclipticTilt stays at 0 when false dawn is gated to 0 (no stale optics leaking)'. But the spec does NOT show the code that ZEROS eclipticTilt when false dawn is gated. A stale eclipticTilt value (set once, never reset) would cause the CSS to recompute the tilt on every frame even when the cue is opacity=0, wasting cycles.
- WEAK ACCEPTANCE: The acceptance criteria include 'The cue's tilt angle (eclipticTilt) is visibly DIFFERENT at lat=0° (equator) vs lat=60° (high)'. But 'visibly different' is subjective and not a pass/fail gate. A subtle 2° difference might be undetectable on a 325px widget. The plan does not specify a minimum detectable difference.
- WEAK ACCEPTANCE: 'The cue does NOT read as a fixed diagonal slash or lens-flare — it appears as a pale, diffuse, triangular glow anchored to the eastern horizon'. This is entirely visual/pixel-based but the acceptance criteria do not mandate a screenshot comparison or a pixel-diff test. A broken implementation could pass all numeric gates but fail visually.
- MISSING SPEC: The plan defers the ecliptic-tilt formula ('openQuestions' #1) to 'a future implementer', but if the math is flawed or unavailable, the feature cannot be built. The plan is ACCEPTING the feature as deferred WITH AN OPEN MATHEMATICAL QUESTION, which means it is NOT truly buildable as currently written.

**Weak acceptance criteria (a broken change could still pass):**
- Acceptance criterion: 'The cue NEVER renders when the moon is bright (qaState().moonObject >= 0.2).' — This is numeric (qaState metric), but a user could verify the metric is correct while the visual rendering still shows a faint cue because (a) the CSS `mix-blend-mode: lighten` is additive and a 0% opacity property still has computational side-effects, or (b) a browser rendering bug. The plan does not mandate a screenshot test.
- Acceptance criterion: 'A screenshot of a dawn scene (clear, new moon, low LP) shows the cue as a barely-visible pale golden wedge from the east, NOT as a bright decorative element.' — But 'barely-visible' and 'pale golden' are subjective. A 0.04 opacity element might be invisible on one screen and visible on another (brightness, contrast, color profile). No reference image or luma threshold is provided.
- Acceptance criterion: 'The cue's tilt angle (eclipticTilt) is visibly DIFFERENT at lat=0° (equator) vs lat=60°' — But does the test require a SCREENSHOT DIFF, a qaState numeric read, or a visual inspection? If numeric, a correct formula might still produce a barely-perceptible visual difference. If visual, the threshold for 'different' is unmeasurable.
- Acceptance criterion: 'Fajr comes from the astronomical/nautical/civil twilight progression (skyLum + the physical sky), not from the false-dawn cue.' — This is verified by checking that Fajr TIME is unchanged, but the time-calculation is NOT touched by this plan. A regression in the gating logic that accidentally suppresses Fajr's cue (via z-index or blend-mode) would not affect the TIME, so this criterion passes even with a visual regression.

**Scope concerns:**
- SCOPE CREEP RISK — 'Open math work': The spec explicitly defers the ecliptic-tilt formula to 'future work' and lists it as 'openQuestions #1'. The plan is titled 'implementation plan or deferred spec', yet it RECOMMENDS DEFERRAL without providing the buildable math. This is not a weakness in the plan's reasoning (deferral is justified), but the spec is INCOMPLETE. A true 'implementation plan' would include the formula or an algorithm reference (e.g., Meeus 'Astronomical Algorithms' §13.3). A true 'deferred spec' would be executable by a DIFFERENT implementer from the math alone — it currently is not.
- SCOPE VIOLATION RISK — refactor needed for declination: The plan states 'a small refactor is needed' to export declination to atmosphere(). But the spec calls this 'Option (a) is preferred (no coupling increase)'. However, re-computing declination in atmosphere() creates a DUPLICATION RISK: if drawArc and atmosphere diverge (e.g., one uses a fit, one uses the raw formula), the sky physics will diverge from the arc (a FORBIDDEN regression). The plan mentions this concern in the 'dependsOn' section but does NOT provide a CONCRETE refactor strategy (e.g., 'compute declination once at model() and pass it to both drawArc and atmosphere'). This is a load-bearing fix that the plan hand-waves.
- SCOPE VIOLATION RISK — 'Must never exceed 2-D canvas/CSS': The plan is constrained to CSS + 2-D, but the spec notes (under 'Future-proofing' openQuestions #6) 'should the spec explicitly document that a 3-D scene-graph (WebGL) widget could render zodiacal light more faithfully'. This is NOT a scope violation per se, but it hints that the 2-D CSS approach is a KNOWN LIMITATION. The plan does NOT explicitly reject WebGL or explain why 2-D is sufficient for a 'faithful' cue. This leaves ambiguity: is a 2-D cue 'faithful' or a 'best-effort approximation'? (The DESIGN.md says 'realism-adjacent, believable, never random', not photometric, but the spec for false dawn uses the word 'faithful'—a potential contradiction.)

**Grounding issues (claims to re-check against current code):**
- CONFIRMED GROUNDING: All major cited line refs match the current index.html (1951 lines). CSS DAWN comment at lines 75-81 matches spec exactly. Code comments at lines 1481-1492 match spec. atmosphere() return object at line 1565 exports trueDawnTwilight as documented.
- CONFIRMED: DEBUGDAWN param exists at line 499 as DEPRECATED no-op. No paint code yet exists for false dawn.
- CONFIRMED: clLow/clMid/clHigh declared at line 1496, initialized at lines 1497-1498, used from line 1503 onward — TDZ/lexical ordering is safe for new false-dawn gating logic placed AFTER line 1498.
- CONFIRMED: sunMetrics() called at line 1407 in atmosphere(). declination is computed in drawArc (line 1015) and sunAltAt (line 1169), but NOT exported from atmosphere().
- CONFIRMED: renderMoon() called at line 1775 before atmosphere() is invoked (line 1805 via applyTheme→paint→atmosphere). moonSky temporal coupling is respected.
- CONFIRMED: Line 1670 comment states '(No painted dawn layers — true dawn is the physical twilight sky + Fajr marker; false dawn is not rendered.)' — this is where the new CSS props would be assigned.

**Reviewer notes:** SUMMARY: The plan is well-reasoned, correctly cites the codebase, and respects the forbidden regressions and render-boundary invariants. The RECOMMENDATION to DEFER with a concrete spec is SOUND — false dawn is astrophysically non-trivial and a botched 2-D implementation is worse than no cue at all. However, the deferred spec itself is INCOMPLETE: it punts the load-bearing math (ecliptic-tilt formula) to 'future work' without providing it, and it does not fully address the refactoring needed to export declination without risking sky-arc divergence. The plan is NOT execution-ready for an implementer; it is a FRAMEWORK that a senior reviewer must hand-off to an astronomer or a specialist who can fill in the math + provide test vectors. The acceptance criteria are mostly numeric (qaState gates) but the CRITICAL regression tests (screenshot of the cue, visual tilt difference) are entirely subjective without reference images. VERDICT: NEEDS-FIXES before an implementer can take it on. The deferral decision is correct, but the spec must be completable by someone who does NOT have the context of this conversation.
