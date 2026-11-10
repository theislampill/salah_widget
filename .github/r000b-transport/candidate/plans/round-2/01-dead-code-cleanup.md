# Plan R2-01 — Remove dead code: moonParallactic function + unused chi return

> **Status:** ✅ DONE (2026-06-16) — deleted `moonParallactic()` (zero callers) and dropped the unused `chi` from `moonIllum()`'s return (kept the internal `chi<0` for `waxing`). Grep confirms no `moonParallactic`/`il.chi` references; moon orientation smokes (upright + waxing-right + waning-left) still pass; 35/35.  ·  **Class:** cleanup  ·  **Priority:** P2  ·  **Effort:** S  ·  **Risk:** low
> **Do now?** Yes — recommended soon  ·  **Plan-review verdict:** `needs-fixes` (3 required fixes — see end)  ·  **Depends/notes:** see "Dependencies / notes"
>
> Read-only round-2 plan from `/implementaudit` (workflow `wf_3f9f2919-894`, investigate → adversarial critique). Grounded against the **current working tree** (`index.html` with the 2026-06-16 uncommitted pass applied; HEAD `91d0fc1`). **No source was changed.** Re-verify anchors before editing.

## Problem
The 2026-06-16 moon-upright fix removed the parallactic rotation from the moon disc (the χ−q angle rotation that made the moon visibly spin). This left two pieces of dead code: (1) the `moonParallactic(date, latDeg, lonDeg)` function (line 724–727) which is defined but never called, and (2) the `chi` field returned by `moonIllum(date)` (line 721, returned in the object as `chi`) which is computed but never read by any caller. Both are vestiges of the old rotation logic and should be removed to clean up the codebase.

## Root cause
When the moon orientation was fixed to upright (removing the parallactic rotation), the code that consumed `moonParallactic()` and `il.chi` was removed, but the function definition and the return field were left in place. No caller currently depends on either.

## Current behavior
The moon is upright and renders correctly (lit side right for waxing, left for waning, matching the footer emoji). `moonParallactic()` is a dead function. `moonIllum()` still computes and returns `chi` (but using `chi<0` internally for the `waxing` boolean, which must be kept).

## Desired behavior
Same moon rendering (no visual change). `moonParallactic()` is deleted entirely. `moonIllum()` stops returning the unused `chi` field, but still computes the internal `chi` variable if it is needed to determine `waxing`. If the internal chi computation can be eliminated (because waxing can be determined another way), do so; but if chi is needed for `waxing`, keep the computation and only drop the returned field.

## Code anchors (re-verify line numbers before editing)
**`index.html:716–722`**
The chi variable is used ONLY to determine waxing (chi<0) and to return it. It must be kept if waxing requires it; the return field must be dropped.

````js
function moonIllum(date){
  const d=_toDays(date), s=_sunCoords(d), m=_moonCoords(d), sd=149598000;
  const phi=Math.acos(Math.sin(s.dec)*Math.sin(m.dec)+Math.cos(s.dec)*Math.cos(m.dec)*Math.cos(s.ra-m.ra));
  const inc=Math.atan2(sd*Math.sin(phi), m.dist-sd*Math.cos(phi));
  const chi=Math.atan2(Math.cos(s.dec)*Math.sin(s.ra-m.ra), Math.sin(s.dec)*Math.cos(m.dec)-Math.cos(s.dec)*Math.sin(m.dec)*Math.cos(s.ra-m.ra));
  return {fraction:(1+Math.cos(inc))/2, waxing:chi<0, chi};
````

**`index.html:723–727`**
Defined at line 724–727; no caller exists (grep moonParallactic\s*\( shows only the definition).

````js
// parallactic angle q of the Moon for this place/time (radians)
function moonParallactic(date, latDeg, lonDeg){
  const lw=_RAD*-lonDeg, ph=_RAD*latDeg, d=_toDays(date), c=_moonCoords(d), H=_sid(d,lw)-c.ra;
  return Math.atan2(Math.sin(H), Math.tan(ph)*Math.cos(c.dec)-Math.sin(c.dec)*Math.cos(H));
}
````

**`index.html:840`**
renderMoon() only reads il.fraction and il.waxing; never il.chi.

````js
const il=moonIllum(date); frac=il.fraction; waxing=il.waxing;
````

**`index.html:871`**
Confirms no parallactic transform is applied; upright design is in effect.

````js
const feat=$(".mfeatures"); if(feat) feat.removeAttribute("transform");   // moon is upright (no parallactic rotation); the lit side is baked by renderMoonPBR per waxing/waning
````

## Approach
1. **Delete moonParallactic() entirely** (lines 723–727). It is dead code with zero callers.
2. **Keep the chi computation in moonIllum()** (line 720) because it is used to determine `waxing=chi<0` (line 721), which is returned and consumed by renderMoon().
3. **Remove chi from the returned object** (line 721). Change `return {fraction:(1+Math.cos(inc))/2, waxing:chi<0, chi};` to `return {fraction:(1+Math.cos(inc))/2, waxing:chi<0};`.
4. **Verify no regressions** via smoke tests (31/31 must pass) and visual inspection: moon still upright, still opaque, lit side matches emoji (right for waxing, left for waning).
5. **Grep verification**: confirm zero matches for `moonParallactic` (except the deleted function definition) and `il.chi` (or any dotted access to chi on the il object).

## Alternatives considered (and rejected)
- **Keep moonParallactic() for potential future use** — Dead code is a maintenance burden (the maintainer must remember what it does and whether to update it if the moon ephemeris code changes). There is no stated future use case. If parallactic rotation is ever re-added, the developer can search git history and restore the exact function and any callers at that time. Deleting unused code keeps the surface minimal.
- **Keep chi as a returned field for observability/debugging** — If chi is useful for debugging or observability, it should be explicitly guarded behind a debug flag (e.g., only included in qaState() or a debug-overlay query param), not silently returned. Currently it is unused by any consumer. If future debugging needs chi, add it explicitly with a clear purpose comment.
- **Refactor waxing to NOT use chi, eliminating the chi computation entirely** — The sign of chi (chi<0 for waxing) is a legitimate, efficient way to determine the moon's waxing/waning phase from the sun–moon angle geometry. Replacing it with an alternative (e.g., comparing moon/sun longitude directly) would require different math and may not be more efficient. Keep the chi computation; only drop the return.

## Owner / source touchpoints
- index.html:716–722 (moonIllum definition + return object)
- index.html:723–727 (moonParallactic definition — delete entirely)
- index.html:840 (renderMoon caller of moonIllum)
- index.html:871 (renderMoon comment about no parallactic rotation)
- HANDOFF.md:83–87 (documentation: moon is upright, no parallactic χ−q rotation)
- tests/smoke.html:120–131 (moon orientation smokes: upright, lit side matches emoji)

## Regression risks (forbidden-regression guardrails)
- Moon is not opaque (stars visible through disc, --moongrp lowered by accident) — Smoke: verify --moongrp>0.9 at qaState().moonTruth.
- Waxing/waning phase inverted (lit side left when should be right or vice versa) — Smoke: moonLitSide must return 'RIGHT' for waxing, 'LEFT' for waning.
- Moon rendered as NaN or invisible (waxing not initialized correctly after chi is removed) — Visual: moon must appear in correct position with correct phase.
- renderMoon stops being called or atmosphere() is stale — Smoke: moonSkyFresh must be true (renderMoon ran before atmosphere this tick).

## Smoke A — capture BEFORE any change
- Load widget with real coords + default simTime. Verify moon is visible, opaque (--moongrp~1), upright (no transform on .mfeatures). Screenshot moon appearance (shape, position, lit side).
- Smoke test suite: 31/31 tests pass (all green, no regressions in weather/prayer/arc/moon/star/dawn logic).
- qaState() check: moonTruth.moonSkyFresh===true (renderMoon ran before atmosphere).
- grep confirmation: moonParallactic is deleted (zero matches); il.chi is unreferenced (zero matches for il\[.*chi|il\.chi).

## Smoke B — verify AFTER the change
- Waxing moon (simMoon=0.6, simWax=1): visual check that lit side is RIGHT. Smoke assertion: moonLitSide(ww)==='RIGHT'.
- Waning moon (simMoon=0.6, simWax=0): visual check that lit side is LEFT. Smoke assertion: moonLitSide(ww)==='LEFT'.
- New/crescent moon (simMoon=0.01, simWax=1): calendar disc opaque at night, no moonlight (moonlightOpacity===0). Visual: dark ashen disc (never transparent, never bright).
- Fast-motion stress (simTime spanned across waxing/waning cycle): moon phase transitions smoothly, lit side sweeps correctly, disc never rotates ('record-player' spin gone).

## Acceptance criteria (falsifiable)
- DELETED: moonParallactic function (lines 723–727 removed).
- MODIFIED: moonIllum() return statement (line 721) changed from {fraction, waxing, chi} to {fraction, waxing}. Internal chi computation kept (line 720) because waxing=chi<0 uses it.
- SMOKE: All 31 tests in tests/smoke.html pass (no regressions in moon, weather, arc, prayer, or optics).
- GREP: Zero matches for 'moonParallactic(' (except deleted definition). Zero matches for 'il\.chi|il\[.*chi' (no caller reads the field).
- VISUAL: Moon is upright (no transform on .mfeatures). Lit side matches footer emoji: right for waxing, left for waning. Opaque at all phases (--moongrp>0.9 even at new moon).
- QASTATE: qaState().moonTruth.moonSkyFresh===true; moonlight and calendar states accurate per phase/altitude.

## Rollback
If a regression occurs (moon inverts, disappears, or becomes transparent), the fix is: (1) restore moonParallactic function and (2) restore chi field to moonIllum return. The change is minimal (two simple deletions) and git diff/git log will show the exact lines removed if emergency restoration is needed. No data structures changed, no API contracts broken besides the internal return object shape (no external consumers).

## Dependencies / notes
- 2026-06-16 moon-upright fix (already applied, uncommitted in working tree): renderMoon no longer applies parallactic rotation; renderMoonPBR lights the bright limb per waxing flag only.

## Open questions
- Is chi ever logged to console or inspected in devtools for debugging? (Grep for 'chi' in codebase confirms no such use, but if a developer had an ad-hoc breakpoint habit, document that chi will no longer be available in moonIllum return.)

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. Before proceeding: Re-verify the test count in tests/smoke.html. If current count differs from 31, update the smokeA acceptance criterion.
2. Before proceeding: Quantify the moon opacity check. Either (a) add a qaState() assertion for --moongrp value (if exposed in qaState), or (b) define clear visual-diff guidance (e.g., 'moon disc opaque at all phases; no stars visible through disc').  Current plan text 'Verify moon is visible, opaque (--moongrp~1)' is too vague.
3. Before proceeding: Specify what 'correct position' means in smokeA. Example: 'Moon in top-right corner (x≈268, y≈55–58 per renderMoon line 866–867); fully on-card; lit limb and crescent shape fully visible; no frame clipping on right edge.'

**Missing risks the spec omitted:**
- Smoke test count (31/31) not re-verified against current tests/smoke.html; if tests were added, criterion fails silently.
- --moongrp opacity check stated as 'Verify moon is visible, opaque (--moongrp~1)' but no quantified assertion provided; plan relies on visual-only validation without a formal test.
- Moon 'visible in correct position' (smokeA) is subjective and not specified (e.g., should be in top-right corner, fully on-card, no clipping).

**Weak acceptance criteria (a broken change could still pass):**
- SMOKE: All 31 tests pass — the count 31/31 is assumed but not verified against current tests/smoke.html.
- VISUAL: Moon is upright + opaque — the 'opaque (--moongrp>0.9)' check is a screenshot/visual assertion, not a quantified test assertion.
- VISUAL: Moon in correct position — 'must appear in correct position' has no defined bounding-box or frame-completeness criterion.

**Scope concerns:**
_(none)_

**Grounding issues (claims to re-check against current code):**
_(none)_

**Reviewer notes:** Code grounding is ACCURATE (all line refs and quotes verified). Scope is MINIMAL (6-line diff: delete moonParallactic function 724–727, remove chi from moonIllum return 721). Rendering boundary and forbidden-regression constraints are honored (no touch to paint/boot/renderMoon; moon stays upright + non-spinning + emoji-matched lit-side via smokeB tests). The core change is SOUND: chi is required for waxing (chi<0), so internal computation is kept; only the returned chi field is dropped. waxing boolean will not invert. Primary weakness: acceptance criteria rely on unverified test counts and subjective visual checks without quantification. Before execution, re-verify smoke.html test count and clarify opacity/position criteria to ensure unambiguous pass/fail.
