# Plan R2-04 — Moon hemisphere orientation — upright N-only vs southern-aware

> **Status:** ⏸️ DEFERRED by decision (2026-06-16) — **keep the current upright N-only moon**; close unless southern-hemisphere support is explicitly in scope. Priority order set by the user: (1) the rendered moon and footer emoji must agree with each other [holds today]; (2) don't confuse ordinary users; (3) exact local-sky orientation is lower priority. **No code change.** If southern support is taken up later, implement it deliberately per the spec below: automatic latitude-based handling + an explicit `?hemisphere=north|south|auto` override; mirror BOTH the rendered moon AND the footer emoji together (never one without the other); add screenshots/smokes for north, south, and near-equator. Must NOT reintroduce any time-varying rotation (the moon stays non-spinning).  ·  **Class:** feature  ·  **Priority:** P1  ·  **Effort:** S  ·  **Risk:** low
> **Do now?** Deferred / decision-gated  ·  **Plan-review verdict:** `needs-fixes` (6 required fixes — see end)  ·  **Depends/notes:** see "Dependencies / notes"
>
> Read-only round-2 plan from `/implementaudit` (workflow `wf_3f9f2919-894`, investigate → adversarial critique). Grounded against the **current working tree** (`index.html` with the 2026-06-16 uncommitted pass applied; HEAD `91d0fc1`). **No source was changed.** Re-verify anchors before editing.

## Problem
The moon currently renders with an upright, N-hemisphere-only orientation. When waxing, the lit side is on the RIGHT; when waning, on the LEFT. This matches the Unicode/Northern convention for the phase emoji. However, in the Southern Hemisphere (lat < 0), the REAL moon's lit side is mirrored: southern waxing is lit LEFT, waning is lit RIGHT. The widget shows moon and emoji "mirrored" vs the user's actual sky at southern latitudes.

## Root cause
The parallactic χ−q rotation was removed 2026-06-16 to prevent the disc from spinning and mismatching the emoji. The `waxing` flag passed to `renderMoonPBR(frac, waxing)` controls the light direction via `Lx = (waxing ? 1 : -1) * sin(pa)` (line 778), and `phaseEmoji(phase)` is computed without latitude dependency. Neither accounts for southern-hemisphere observers.

## Current behavior
The moon is rendered upright with no parallactic rotation. The `waxing` flag is global/hemisphere-agnostic. The lit side is always right-on-waxing, left-on-waning, matching the N-convention emoji. Southern-hemisphere users see the moon's bright limb mirrored vs their real sky, although emoji and disc remain mutually consistent.

## Desired behavior
**OPTION A (Recommended: KEEP upright N-only)**: No code change. Zero risk, zero cost, matches DESIGN.md line 139–140 rationale. **OPTION B (Hemisphere-aware)**: For `lat < 0`, flip BOTH the rendered moon's lit side (flip `waxing` boolean) AND the emoji in lockstep, keeping the moon upright (no parallactic rotation, no spin). **OPTION C (Document only)**: Add a southern-hemisphere note to DESIGN.md.

## Code anchors (re-verify line numbers before editing)
**`index.html:716–721`**
Computes waxing: chi < 0 using sun-moon phase angle. Hemisphere-agnostic. Phase angle correct; its interpretation (which limb appears lit) depends on hemisphere.

````js
function moonIllum(date){...return {fraction:(1+Math.cos(inc))/2, waxing:chi<0, chi};}
````

**`index.html:778`**
Lx sign controls bright-limb direction (waxing→+Lx→lit RIGHT, waning→−Lx→lit LEFT). For OPTION B, flip waxing before passing it.

````js
const pa=Math.acos(2*frac-1), Lx=(waxing?1:-1)*Math.sin(pa), Lz=Math.cos(pa);
````

**`index.html:832`**
Maps 0..1 synodic phase to 8-step emoji. No latitude adjustment. For OPTION B, flip the phase before calling.

````js
function phaseEmoji(p){ return ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][Math.round(((p||0)%1)*8)%8]; }
````

**`index.html:840–848`**
Call site where waxing is extracted and passed to renderMoonPBR. For OPTION B: insert `const waxingDisplay = lat < 0 ? !waxing : waxing;` and pass waxingDisplay.

````js
const il=moonIllum(date); frac=il.fraction; waxing=il.waxing;...renderMoonPBR(frac, waxing);
````

**`index.html:1808`**
Footer emoji. For OPTION B: wrap with phase flip: `phaseEmoji(lat < 0 ? (1 - moonNow().phase) : moonNow().phase)`.

````js
const tail = (!afterMaghrib && tmrwH) ? ` <span class="mph pre">| ${phaseEmoji(moonNow().phase)} ${tomorrow.date.hijri.day}</span>` : "";
````

**`index.html:871`**
Explicitly removes rotation transform, confirming upright moon. For OPTION B, this ensures no parallactic angle—flip is purely a light-direction sign change.

````js
const feat=$(".mfeatures"); if(feat) feat.removeAttribute("transform");
````

**`DESIGN.md:139–140`**
Documents the N-hemisphere convention choice. For OPTION C, add southern-hemisphere caveat here.

````js
The trade-off is the moon is the upright N-hemisphere view, not tilted 'as seen from your exact location' — consistent with the upright emoji, and the right call for a corner widget.
````

**`tests/smoke.html:120–131`**
Current smoke tests verify N-only. For OPTION B, keep as regression checks and add southern tests (lat<0).

````js
ok("WAXING moon is lit on the RIGHT (matches 🌒/🌓/🌔)", side==="RIGHT", ""+side);...ok("WANING moon is lit on the LEFT (matches 🌖/🌗/🌘)", side==="LEFT", ""+side);
````

## Approach
**Recommended: OPTION A (no code change).** The widget is a corner widget with a canonical upright emoji, not a portable planetarium. DESIGN.md already documents this trade-off. **If OPTION B:** (1) In `renderMoon()` (~line 843), compute `const waxingDisplay = lat < 0 ? !waxing : waxing;` before calling `renderMoonPBR(frac, waxingDisplay)`. (2) In footer emoji (~line 1808), wrap phaseEmoji: `phaseEmoji(lat < 0 ? (1 - moonNow().phase) : moonNow().phase)`. Both are static sign flips, not time-varying angles—no spin.

## Alternatives considered (and rejected)
- **Reintroduce the parallactic χ−q rotation to show the moon 'true to your sky' at any latitude** — Removed 2026-06-16 because it made the disc visibly SPIN over time and mismatch the static upright emoji. Reintroducing angle-based rotation violates the FORBIDDEN REGRESSION (no spin) and breaks emoji alignment.
- **Keep the upright N-only view but allow a lat-based UI toggle (e.g., ?southernMode=1)** — Adds config state and test surface. Unless strong southern-user demand, complexity not justified.
- **Flip ONLY the emoji (not the rendered disc)** — Would make emoji and disc inconsistent at southern latitudes, violating the core contract (DESIGN.md:137).
- **Use a sophisticated orientation model (e.g., selenocentric latitude, real libration, etc.)** — The issue is a simple hemisphere flip, not libration. Overengineering adds complexity and DOM cost for marginal gain on a corner widget.

## Owner / source touchpoints
- index.html:716–721 (moonIllum — computes waxing, hemisphere-agnostic)
- index.html:770–827 (renderMoonPBR — lights disc; Lx controls bright-limb)
- index.html:828–832 (moonNow/phaseEmoji — phase to emoji, no lat)
- index.html:834–848 (renderMoon — waxing call site, option B insertion point)
- index.html:1808 (footer emoji call site, option B insertion point)
- DESIGN.md:139–140 (documents upright N-hemisphere choice)
- tests/smoke.html:120–131 (current moon orientation smokes)

## Regression risks (forbidden-regression guardrails)
- FORBIDDEN: Reintroducing spin. OPTION B must be static boolean flip, not angle. Time-varying angle regresses the 2026-06-16 fix. Verification: .mfeatures has no transform; no rotation over 10-min watch.
- Emoji misalignment. Disc flip without emoji flip (or vice versa) breaks consistency. Both must flip in lockstep. Verification: waxing disc lit-LEFT pairs with LEFT-lit emoji at lat<0.
- Static, not dynamic. Flip depends only on immutable latitude, not time. If inside per-tick loop or time-dependent, disc flickers. Verification: flip computed once per renderMoon() call.
- Northern regression. lat > 0 users must see moon unchanged. Existing smoke tests (lines 124–131) must pass unmodified.
- Cache coherence. Waxing is deterministic per hemisphere; no cache issue expected, but if memoized, key must include latitude.

## Smoke A — capture BEFORE any change
- OPTION A (no change): all 31 existing smoke tests pass unchanged.
- OPTION A: Southern user at lat=-34.05, lon=18.42 during waxing sees moon lit RIGHT (N-view), emoji 🌒 (N-convention), both consistent, neither matching real sky. User informed by DESIGN.md of trade-off.

## Smoke B — verify AFTER the change
- OPTION B: Northern smoke (lat>0) waxing moon lit RIGHT, emoji 🌒/🌓/🌔, no rotation, all 31 tests pass.
- OPTION B: Southern smoke (lat<0, new test) waxing moon lit LEFT, emoji 🌖/🌗/🌘, no rotation, matches real southern sky. Example: lat=-34.05&lon=18.42&simMoon=0.3&simWax=1&simMoonAlt=55.
- OPTION B: Emoji correctness—southern waxing gibbous (frac~0.7) returns 🌗 (now correct for south); northern same phase returns 🌓 (correct for north); both pair with rendered discs.
- OPTION B: No spin—10-minute watch shows moon static/upright, terminator sweeps maria, no rotation transform, .mfeatures has no transform at either hemisphere.

## Acceptance criteria (falsifiable)
- (A1) OPTION A chosen: code unchanged; DESIGN.md notes N-hemisphere convention; 31/31 smoke tests pass; southern users see working widget with mirrored disc (acceptable for corner widget).
- (B1) OPTION B chosen: renderMoon() at line ~843 computes `const waxingDisplay = lat < 0 ? !waxing : waxing;` and passes to renderMoonPBR (≤3 lines).
- (B2) OPTION B: footer emoji at line ~1808 flipped in lockstep: `phaseEmoji(lat < 0 ? (1 - moonNow().phase) : moonNow().phase)` (≤3 lines).
- (B3) OPTION B: no parallactic rotation reintroduced. 10-minute watch shows moon still/upright; .mfeatures has no transform; terminator sweeps maria. Smoke: `ok('no rotation', !feat.getAttribute('transform'), …)` passes both hemispheres.
- (B4) OPTION B: northern tests (lines 124–131) pass unchanged. Southern tests added, all pass (lit side matches emoji, no spin).
- (B5) OPTION B: qaState().moonTruth.waxing accurate (unchanged); calendar emoji reflects hemisphere-aware phase; no inconsistency.
- (B6) OPTION B: sim scenario (simMoon=0.3&simWax=1 at lat<0) shows left-lit disc and left-lit emoji; same simWax at lat>0 shows right-lit disc and right-lit emoji.

## Rollback
OPTION B changes are two small, isolated boolean flips (lines ~843 and ~1808). Rollback: revert both lines and re-run smoke tests to confirm northern cases pass. No cache/state to clean up; purely render-time logic.

## Dependencies / notes
- Round-1 plans (2026-06-16) complete — moon is upright, emoji consistent, no parallactic rotation.
- Current smoke tests pass (31/31, lines 120–131 verify upright and left/right lit sides).
- No technical blockers; decision (A vs B) is a product/UX call.

## Open questions
- Do we have southern-hemisphere users? Product data on southern-latitude traffic. If <1%, OPTION A is right. If >10%, OPTION B justified. Interim: assume A (safest).
- Is 'me-centered true-to-my-sky' a use case? Current design is 'canonical reference' (emoji-consistent), not 'planetarium'. Clarify intent: is truthfulness to observer's actual sky required, or is emoji consistency sufficient? DESIGN.md suggests latter.
- If OPTION B, audit for other N-only biases? Stars, sun, cloud positions are already per-observer. Most optics are azimuthal, not limb-dependent, but worth a sweep.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. MUST FIX: Provide explicit derivation or citation for why (1 - phase) inverts the emoji correctly. Concrete example: northern observer at phase=0.25 (waxing gibbous, ~0.375 illuminated) sees emoji 🌒; southern observer at SAME illuminated fraction should see which emoji? If 🌖 (mirrored), prove 1 - 0.25 = 0.75 maps to 🌖 via the phaseEmoji lookup (currently Math.round(0.75*8) = 6 → 🌖; for north 0.25 → round(2) = 🌒 at index 2). Show the math.
2. MUST FIX: Add explicit southern smoke test to acceptance criteria. Example: 'Test with lat=-34.05&lon=18.42&simMoon=0.3&simWax=1&simMoonAlt=55. Expected: moon is LIT on the LEFT (inverted from north's RIGHT), emoji is 🌖 or 🌗 (inverted from north's 🌒 or 🌓), no rotation transform. This test is added to tests/smoke.html lines ~132–140 and must pass before merge.'
3. MUST FIX: Clarify sim parameter semantics in the code insertion. Either (1) show the exact code change with comments explaining that the conditional flip is applied to the REAL (non-sim) waxing value ONLY, or (2) confirm that the flip is applied AFTER the sim-vs-real branch so that forced sim values are NOT re-flipped. Document in code: `// hemisphere-aware flip is applied only to real computed waxing, not to forced SIM.wax`.
4. SHOULD FIX: Update acceptance criterion (B1) to say 'line ~848 (the renderMoonPBR call, after the SIM/lat/lon conditional block)' instead of '~843'.
5. SHOULD FIX: Document whether moonSky.frac remains the illuminated fraction (unflipped) and verify that this is correct for cloud lighting and qaState(). If frac stays unflipped, add a comment: `// moonSky.frac is always the true illuminated fraction (no hemisphere flip); waxing_display is a separate transform only for rendering light direction and emoji`.
6. SHOULD FIX: Provide rollback scenario for OPTION B: 'To rollback OPTION B: (1) Remove the hemisphere-aware conditional at line ~848. (2) Revert emoji flip at line ~1808. (3) Run full smoke test suite (31 northern + N southern); all must pass. (4) No state to clean up; changes are render-time only.' This is already in the plan; just make it explicit in the implementation steps.

**Missing risks the spec omitted:**
- CRITICAL: Phase-flipping logic not justified. The plan assumes (1 - phase) inverts the emoji correctly for southern observers, but does NOT prove that synodic PHASE values themselves flip under hemisphere mirror—only that light direction does. If (1 - phase) is wrong, emoji will mismatch disc even after the fix, breaking the core contract (DESIGN.md:137: 'disc and emoji must be consistent').
- Asymmetry risk: Plan flips waxing (sign of Lx in renderMoonPBR) AND phase (in emoji lookup). These are separate transformations on separate state. Are they guaranteed to be inverses? If not, lit side and emoji misalign at southern latitudes.
- Cache coherence unaddressed: moonSky is populated at line 870 with the unflipped frac/waxing; emoji is flipped at line 1808. Is moonSky.frac still the true illuminated fraction? This affects cloud lighting (line 1584: cloudMoonLit depends on moonSky) and qaState().render. Side effect undocumented.
- Sim parameter coupling ambiguous: renderMoonPBR is called AFTER sim-vs-real branch (line 848, after the if/else-if/else block ending at 843). The plan says to insert flip BEFORE line 848. Does this apply the flip ON TOP of sim-forced values? Smoke tests must verify that simWax=1&lat<0 does NOT double-flip.
- No southern smoke test provided: Plan mentions 'southern tests added, all pass' (B4) but provides neither the test URL nor expected emoji. Without explicit southern test, cannot verify the fix works or that acceptance criteria are met.

**Weak acceptance criteria (a broken change could still pass):**
- (B1) 'renderMoon() at line ~843' — should be '~848' (5-line offset); plan was not re-verified against current code.
- (B4) 'Southern tests added, all pass (lit side matches emoji, no spin)' — criteria do NOT specify which southern test URL to use or what emoji is expected. E.g., for lat=-34&lon=18&simMoon=0.3&simWax=1 (forced waxing), is the expected emoji 🌖/🌗/🌘 (LEFT-lit, inverted from north)? Without this, acceptance is unverifiable.
- (B6) 'sim scenario (simMoon=0.3&simWax=1 at lat<0) shows left-lit disc and left-lit emoji' — good intent, but does NOT state the EXPECTED EMOJI. Is it mirrored emoji (🌖 instead of 🌒)? Is moonSky.frac flipped or not? Unspecified.
- OPTION B code insertion point is after line 843–848 (the waxing resolution), but plan does NOT clarify whether the conditional flip applies BEFORE or AFTER sim-forced values. If applied AFTER, sim=1 may double-flip at southern latitudes (correct). If unclear to implementer, risk of off-by-one logic error.

**Scope concerns:**
- OPTION selection deferred: Plan offers three options (A: no change, B: hemisphere-aware flip, C: documentation only) and RECOMMENDS A, but leaves final decision to reviewer. This is acceptable for a proposal, but means OPTION B acceptance criteria depend on whether OPTION B is actually chosen—creating a conditional specification.
- Incomplete OPTION B specification: If OPTION B is chosen, the plan MUST provide (1) the phase-flipping derivation, (2) explicit southern smoke test URL + expected emoji, (3) confirmation that sim parameters are handled correctly. Without these, the plan is unimplementable and unverifiable.
- No migration path from A to B: If A is initially chosen and later changed to B, the plan does NOT specify a verification strategy (e.g., 'add southern tests first, then apply the flip, re-run all 31+new southern tests'). Rollback is documented, but migration is not.

**Grounding issues (claims to re-check against current code):**
- Line number drift: Plan cites '~line 843' for renderMoonPBR call site; actual code has it at line 848 (5-line offset). Within '~' approximation but indicates the plan was not re-verified against CURRENT uncommitted code.
- All quoted code snippets (lines 716–721, 778, 832, 1808, 871, DESIGN.md 139–140) match the current index.html exactly. Lat variable IS globally scoped (line 456) and accessible in renderMoon().
- Smoke tests (lines 120–131 of tests/smoke.html) verify upright moon + correct lit side for northern hemisphere. No southern-hemisphere test provided by the plan.

**Reviewer notes:** VERDICT: The plan is WELL-STRUCTURED and cites the codebase accurately, but OPTION B (hemisphere-aware rendering) is INCOMPLETELY SPECIFIED. OPTION A (no change) is SOUND and requires zero work. If OPTION B is chosen, the three Required Fixes above MUST be addressed before implementation and verification. The core question is: does (1 - phase) correctly invert the emoji for southern observers, or should the emoji array itself be mirrored? The plan assumes the former but provides no derivation. A physics-based or empirical verification (e.g., check what a real southern-hemisphere moon app does) is needed. The plan also does not specify what southern smoke tests should expect, making it impossible to verify the fix without guessing the intended behavior. Once these gaps are filled, the implementation is straightforward (three small boolean flips in two places, no state or cache changes). The render-boundary invariants (no animation, pure render-time logic, moonSky coupling to atmosphere via line 1584) are respected in the design.
