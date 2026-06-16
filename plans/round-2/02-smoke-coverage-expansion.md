# Plan R2-02 — Expand tests/smoke.html with offline rollover, cloud continuity, and reduced-motion liveness tests

> **Status:** ✅ DONE (2026-06-16, partial-by-design) — added 4 **reliable** smokes: reduced-motion liveness (matchMedia override → `--sunpulse` freezes to 1, restore → animates) ×2, and cloud continuity (overcast deck present + evolves between frames; `cloudFieldSeed` stable across reads) ×2 → **35/35**. The full **offline-midnight-crossing** end-to-end stays a **manual/preview** check (documented): the off-screen smoke iframe pauses its rAF loop (IntersectionObserver), so a loop-driven rollover can't fire there, and top-level `let`s (`_prayerStale`) aren't window-accessible to force from the parent. That path was proven deterministically in preview this session (fetch-override + sim-midnight crossing).  ·  **Class:** tests  ·  **Priority:** P1  ·  **Effort:** M  ·  **Risk:** low
> **Do now?** Yes — recommended soon  ·  **Plan-review verdict:** `sound` (5 required fixes — see end)  ·  **Depends/notes:** see "Dependencies / notes"
>
> Read-only round-2 plan from `/implementaudit` (workflow `wf_3f9f2919-894`, investigate → adversarial critique). Grounded against the **current working tree** (`index.html` with the 2026-06-16 uncommitted pass applied; HEAD `91d0fc1`). **No source was changed.** Re-verify anchors before editing.

## Problem
tests/smoke.html (currently 31/31 pass) covers core behavior (weather truthfulness, moon optics, dawn, continuity) but has gaps in three under-verified areas: (a) the day-rollover offline path — when crossing midnight offline with no cache for the new day, the code now sets `_prayerStale=true` and throttles retries (plan 03, done 2026-06-16), but smoke only checks field existence (prayerStale is present), NOT the real offline→stale→recovery flow; (b) cloud continuity under eased coverage — smoke checks `cloudFieldSeed` is stable per read (deterministic), but does NOT verify the deck doesn't reseed on a weather refresh or fast-forward; (c) reduced-motion liveness — `isMotionReduced()` (line 509) now centralizes the motion check (single source of truth, live override via `?motion=full`), but smoke has NO test that motion freezes under OS `prefers-reduced-motion` (only the on-card telemetry `?debugMotion=1` exists for manual inspection). These gaps mean a regression in any of these paths (silent stale replay, accidental reseed, motion not freezing) would pass smoke.

## Root cause
The three gaps exist because: (a) offline rollover was implemented/verified manually (a targeted preview repro: override `window.fetch`, load with `simTime` near midnight, fast-forward across it, watch `qaState().cache.prayerStale` flip and recovery occur) — not yet automated in smoke; (b) continuity is implicit in the existing seed check (it doesn't reseed on read, but smoke doesn't exercise an eased coverage change); (c) reduced-motion has no smoke (only a manual CSS override test, `?motion=full`). All three behaviors are deterministic and smoke-testable; they were omitted due to build-out scope and prioritization. They are now worth automating as confidence gates before any future refactoring.

## Current behavior
(a) Offline rollover: crossing midnight offline with no new-day cache sets `_prayerStale=true`, `rolloverPendingMs` is exposed in `qaState().cache`, and the fetch is throttled to retry every 60s (lines 1933–1951, day-rollover branch). Manual preview confirms this works; smoke does NOT test it. (b) Cloud continuity: `cloudFieldSeed` is stable per read (line 1848 in wxTruth), and coverage eases on refetch (lines 1663–1664 in paint); smoke asserts seed is not reseeded across two reads (line 113), but does NOT simulate a weather refresh or eased-coverage change. (c) Reduced-motion: `isMotionReduced()` (line 509) reads `matchMedia("prefers-reduced-motion: reduce")` live + respects `?motion=full`, and the loop freezes cloud animation + moon glow on reduced-motion (lines 1959, 1637). Smoke has NO test; on-card telemetry `?debugMotion=1` shows the state but is manual.

## Desired behavior
(a) A deterministic offline-rollover smoke that: loads the widget with sim params near midnight offline, fast-forwards across midnight, asserts `prayerStale===true` and `prayerDate` DOES NOT advance (remains yesterday), then either seals network back on OR seeds a cache and asserts recovery (stale clears, date advances). Must NOT flake on timing (use polling + loadUntil's ready-check pattern, reuse `?r=` cache-buster). (b) A cloud-continuity smoke that: captures `cloudFieldSeed` before/after a simulated weather-code change (e.g. `simWx=0` → `simWx=3`), asserts the seed stays the same, optionally asserts coverage does NOT snap (has a history of easing). (c) A reduced-motion smoke (if feasible deterministically) that: detects `matchMedia` and overrides it (via test harness setup), then asserts cloud animation and `--sunpulse`/`--mrad` freeze to `1.0` (no breathing). If direct matchMedia override is not testable in iframe, flag the limitation.

## Code anchors (re-verify line numbers before editing)
**`index.html:1933–1951`**
Day-rollover branch: sets _prayerStale=true on cache miss, throttles retry via _rolloverNextTry gate. Offline-rollover smoke verifies this flow.

````js
if(n.dateStr!==_lastDateStr){ if(_lastDateStr){ const ds=n.dateStr, c=loadCache(ds); if(c){ today=c; tomorrow=null; lastDate=ds; _prayerStale=false; _lastDateStr=ds; renderMoon(); _starsProjected=false; } else { tomorrow=null; _prayerStale=true; const ms=Date.now(); if(!_rolloverBusy && ms>=_rolloverNextTry){ _rolloverBusy=true; _rolloverNextTry=ms+_ROLLOVER_RETRY_MS; fetchTimings(ds).then(d=>{ today=d; saveCache(ds,d); lastDate=ds; _prayerStale=false; _lastDateStr=ds; renderMoon(); _starsProjected=false; _rolloverBusy=false; }).catch(()=>{ _rolloverBusy=false; }); } } } else { _lastDateStr=n.dateStr; } }
````

**`index.html:999–1000`**
Stale-state tracking module-scoped vars. Smoke reads via qaState().cache.prayerStale and rolloverPendingMs.

````js
let _prayerStale=false, _rolloverBusy=false, _rolloverNextTry=0; const _ROLLOVER_RETRY_MS=60000;
````

**`index.html:1854`**
qaState() exposure of prayerStale and rolloverPendingMs (diagnostic fields). Smoke reads these to verify stale state.

````js
prayerStale: _prayerStale, rolloverPendingMs: (_prayerStale ? Math.max(0, _rolloverNextTry-Date.now()) : null),
````

**`index.html:1308`**
Cloud field seed formula: deterministic from location+day+optional seed, NEVER weather-code. Continuity smoke verifies seed is stable across weather changes.

````js
const _cloudFieldSeed=((Math.abs(+lat||0)*12.9+Math.abs(+lon||0)*7.31+(+q.get("seed")||0)*4.7)%617);
````

**`index.html:1848`**
cloudFieldSeed exposed in qaState().wxTruth. Continuity smoke reads this before/after weather mutation.

````js
cloudFieldSeed: _cloudFieldSeed
````

**`index.html:509`**
Single source of motion-reduction decision. Reduced-motion smoke tests this via test hook (if Option A) or documents it as manual-only (if Option B).

````js
const isMotionReduced = () => !MOTIONFULL && !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
````

**`index.html:1601`**
paint() reads isMotionReduced() to freeze --sunpulse and --mrad.

````js
const _REDUCED = isMotionReduced();
````

**`index.html:1637`**
--sunpulse set to 1 if _REDUCED, else animated breathing. Reduced-motion smoke verifies it freezes.

````js
c.style.setProperty("--sunpulse",(_REDUCED?1:1+(0.045+0.035*A.heat)*Math.sin(simNow()/1000/23)+0.015*Math.sin(simNow()/1000/6.5)+(1-noon)*0.16).toFixed(4));
````

**`index.html:1649`**
--mrad set to 1 if _REDUCED, else animated breathing. Reduced-motion smoke verifies it freezes.

````js
c.style.setProperty("--mrad",(_REDUCED?1:1+0.10*Math.sin(simNow()/1000/17)+0.12*A.aerosolDensity).toFixed(3));
````

**`index.html:1959`**
loop() freezes cloud animation (uses frozen simTime 1000) when reduced-motion. Reduced-motion smoke can optionally verify cloud canvas does not animate.

````js
if(isMotionReduced()){ if(_cloudDirty){ paintClouds(1000); tieRainToClouds(); _cloudN++; } }
````

**`tests/smoke.html:52–57`**
loadUntil harness: loads iframe, polls ready-check, resolves when condition is met. Offline-rollover smoke uses this for stale/recovery polling.

````js
function loadUntil(hash, ms, ready){ const want=hash+"&qa=1"; fr.src="../index.html?r="+(++_r)+"#"+want; const t0=Date.now(); return new Promise(res=>{ (function poll(){ let w=null; try{ w=fr.contentWindow; }catch(e){} try{ if(w && hashOf(w)===want && ready(w)) return res(w); }catch(e){} if(Date.now()-t0>ms) return res(null); setTimeout(poll,150); })(); }); }
````

**`tests/smoke.html:111–113`**
Existing continuity smoke (line 113). Expanded plan adds a second scene to verify seed is stable across WEATHER CHANGES (not just reads).

````js
head("continuity + observability"); await scene("lat=24.47&lon=39.61&label=Madinah&method=4&simWx=3&simCloud=100","cloud identity is stable (no reseed per read)",(ww,q)=>{ ok("cloudFieldSeed stable across reads", ww.qaState().wxTruth.cloudFieldSeed===ww.qaState().wxTruth.cloudFieldSeed); });
````

## Approach
**NEW TEST CASES in tests/smoke.html (deterministic, no-build, browser-runnable):**

**1. OFFLINE-ROLLOVER SMOKE:**
- Add a new integration scene that loads with `simTime=23:58&simWx=0`, near midnight.
- Manually inject a fetch override to simulate network down via `ww.window.fetch = () => Promise.reject(new Error("offline"))`.
- Advance `simTime` to cross midnight (00:05 next day, triggering day-rollover branch at line 1933–1951).
- Poll `qaState().cache.prayerStale` and assert it becomes `true`.
- Assert `qaState().cache.prayerDate` remains unchanged (yesterday's date).
- Assert `qaState().cache.rolloverPendingMs > 0` (throttle is armed).
- **Recovery path:** seed cache or restore fetch, verify `prayerStale===false` and `prayerDate` advances.
- **Determinism:** use `loadUntil(hash, timeoutMs, readyFn)` with polling-based ready-checks; no `sleep()`.

**2. CLOUD-CONTINUITY SMOKE (advanced):**
- Verify that changing weather code does NOT reseed `cloudFieldSeed`.
- Load with baseline `simWx=0&simCloud=30`, capture `seed0 = qaState().wxTruth.cloudFieldSeed`.
- Mutate to `simWx=3` (overcast), re-load, re-read seed, assert `seed1 === seed0`.
- Optionally track coverage easing over time (coverage does not snap; is smooth).

**3. REDUCED-MOTION SMOKE:**
- **Option A (intrusive but deterministic):** Add a test hook to index.html: if `?testReducedMotion=1` param is set, `isMotionReduced()` returns `true` (ignoring `matchMedia`).
  - In smoke, load with `?testReducedMotion=1&simTime=02:00&qa=1`.
  - Assert computed `--sunpulse === 1.0` and `--mrad === 1.0` (no breathing).
- **Option B (non-intrusive, skips test):** Document that reduced-motion is manual-only (CSS override + visual inspection), note the limitation in smoke.

**Implementation mechanics:**
- Reuse `loadUntil(hash, ms, ready)` (line 52–57 in smoke.html) for polling-based readiness.
- Inject `fetch` override via `ww.window.fetch = mockFetch` after `loadUntil` returns.
- Offline-rollover recovery: either wait for retry gate to fire (fast-forward via timeScale) or seed cache directly.
- All additions are inline JS in smoke.html; no new files or dependencies.
- **Determinism gates:** polling + explicit state changes, never `sleep()`.

## Alternatives considered (and rejected)
- **Add all three tests in one mega-scene with a complex state machine** — Violates smoke principle of isolated, independent test cases. Single mega-test is flaky and hard to debug.
- **Skip the offline-rollover smoke, rely only on manual preview repro** — Manual repros don't scale. The bug was silent; without automation, a similar regression could slip through.
- **For reduced-motion, skip the test entirely and document it as manual-only** — Leaves a gap. A regression (cloud animation not pausing under reduced-motion) would not be caught. Test hook is minimal.
- **Use a separate test file (tests/advanced-smoke.html) instead of expanding smoke.html** — Fragments the test suite. smoke.html is canonical; keeping tests together aids discovery and CI integration.

## Owner / source touchpoints
- tests/smoke.html (ADD offline-rollover + cloud-continuity + reduced-motion scenes, ~80–120 lines total)
- index.html:1933–1951 (day-rollover; already correct; smoke verifies it)
- index.html:999–1000 (stale-state tracking; smoke reads via qaState)
- index.html:1854 (qaState exposure of prayerStale/rolloverPendingMs)
- index.html:1308, 1848 (cloudFieldSeed calc + exposure; smoke verifies stable)
- index.html:509 (isMotionReduced; optional test hook if Option A chosen)
- index.html:1601, 1637, 1649, 1959 (reduced-motion gates; smoke verifies they freeze motion)

## Regression risks (forbidden-regression guardrails)
- Offline-rollover test could flake if retry-gate timing (60s throttle) is not respected. MITIGATION: use loadUntil polling + explicit fast-forward of simTime, not wall-clock sleep.
- Continuity test assumes cloudFieldSeed calc does NOT change on weather-code update. MITIGATION: verify formula is location+day+optionalSeed ONLY (line 1308).
- Reduced-motion test (Option A) requires a test hook in index.html. MITIGATION: hook is gated by URL param (?testReducedMotion=1) and does NOT affect production paths (single if guard).
- If iframe matchMedia is locked to harness OS setting, Option A may not work. MITIGATION: detect failure; fall back to Option B (skip test, document).
- Expanded smoke.html adds ~3–5 tests (~80–120 lines), increasing CI runtime. MITIGATION: negligible (each scene ~5–10ms); smoke is already fast.

## Smoke A — capture BEFORE any change
- Load with live internet at simTime 23:55. Verify today's prayers load, prayerStale===false.
- Force offline. Advance simTime to 00:05 (cross midnight). Assert prayerStale===true, prayerDate unchanged.
- Wait ≥61s (or fast-forward timeScale) or restore network. Assert prayerStale===false, prayerDate advanced.
- Load with cloudFieldSeed, reload, re-read. Assert seed stability across reads.
- Load with simWx=0, read seed. Mutate to simWx=3, re-read. Assert seed unchanged (no reseed on weather change).
- [Optional] Load with ?testReducedMotion=1&simTime=02:00&qa=1. Verify --sunpulse≈1.0 and --mrad≈1.0 (no breathing).

## Smoke B — verify AFTER the change
- Same as smokeA. All three test suites ADDED; existing 31 tests remain unchanged.

## Acceptance criteria (falsifiable)
- Offline-rollover deterministic test PASSES: load offline (no new-day cache), cross midnight, assert prayerStale===true && prayerDate unchanged, recover (network restored or cache seeded), assert prayerStale===false && prayerDate advanced. Timing deterministic (polling + explicit state changes), no flakiness. (qaState JSON snapshots before/after.)
- Cloud-continuity test PASSES: cloudFieldSeed stable across reads within same scene AND across two scenes with different weather codes (simWx changed). Assert seed0===seed1===seed2. (qaState snapshots.)
- Reduced-motion test PASSES (Option A): load with ?testReducedMotion=1, assert --sunpulse===1.0 and --mrad===1.0 (no sine breathing). (Computed style reads from .c.) OR (Option B): document in smoke that reduced-motion tested manually, add NOTE explaining limitation.
- Smoke summary: all NEW tests PASS deterministically (no sleeps, no timing races), run in <5s added runtime. No flakiness over 10 consecutive runs.
- Regression gate: future changes that accidentally reseed cloud on weather update, fail to throttle rollover retry, or forget to freeze motion under reduced-motion will FAIL smoke and be caught.
- Boot-time regression: existing smoke 31/31 tests still pass (no changes to core behavior, only test additions).

## Rollback
All new tests are additive (new scene() calls in smoke.html). Rollback: delete the three new test blocks. No changes to index.html behavior (unless Option A for reduced-motion, which adds one optional if guard—can be removed if needed). No cache-invalidation or data-migration. Safe cherry-pick in either direction.

## Dependencies / notes
- Plan 03 (day-rollover offline robustness)—DONE 2026-06-16. This plan verifies the fix works.

## Open questions
- **Reduced-motion Approach decision**: is Option A (test hook in index.html + ?testReducedMotion=1 param) acceptable, or Option B (skip test, document limitation) preferred? Option A is slightly intrusive but deterministic; Option B is lower-friction but leaves a gap.
- **Offline-rollover recovery method**: should test restore fetch and wait for retry gate (cleaner but slower, handles 60s throttle), OR seed cache directly via localStorage (faster but less realistic)? Recommend hybrid: fast test path uses cache-seeding, optional extended path tests real retry timing.
- **Cloud-continuity scope**: is testing field-identity stability sufficient (current smoke + added scene), or should smoke also verify coverage-easing (optional tracking of coverage over time)? Current scope is minimally sufficient; easing can be future enhancement.
- **Timing sensitivity**: is 150ms polling interval (line 57 in smoke.html) fast enough for stale condition? Yes, stale is set synchronously on midnight cross; no need to tighten.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `sound`

**Required fixes (resolve before writing code):**
1. **Offline-rollover test MUST verify _rolloverBusy===false on recovery.** Current acceptance criteria only check prayerStale and prayerDate, but _rolloverBusy must also be FALSE to confirm the throttle gate is not still blocking. Add to acceptance: 'assert qaState().cache.rolloverPendingMs is null or undefined once recovery occurs (prayerStale===false).' This is already exposed in qaState() per line 1854, so the test can read it.
2. **Reduced-motion Option decision MUST be made BEFORE implementation.** Plan lists this as an open question. A firm choice is required: (A) add ?testReducedMotion=1 param hook in index.html (minimal, gated), or (B) skip reduced-motion test, document as manual-only, note the limitation in smoke.html comments. Recommendation: Option A is justified (deterministic, deterministic gate, no production side effect if param gated). But decision must be explicit in the final plan.
3. **Cloud-continuity test MUST clarify the mutation mechanism.** If the plan intends two separate loadUntil scenes (one with simWx=0, one with simWx=3), state this explicitly and verify both scenes read the SAME _cloudFieldSeed (lines 1308 + 1848). If the plan intends in-place mutation, clarify how (e.g., mutate the URL hash and reload, or call a global setSimWeather function—neither exists, so this is infeasible). Recommend: use two separate scene() calls, same location, different simWx values.
4. **Offline-rollover recovery path MUST be specified.** Plan lists two options: (1) wait ≥61s for retry gate to fire (slow), or (2) seed cache directly (fast but less realistic). Acceptance criteria must specify ONE. Recommendation: hybrid for fast-path (seed cache immediately, test succeeds in <5s), with an OPTIONAL extended validation that calls fetchWeather/fetchTimings manually to verify the real retry works under load (separate advanced test).
5. **Ensure existing 31-test suite is re-run after additions.** Plan acceptance states 'existing smoke 31/31 still pass' but implementation must verify this is tested (i.e., CI/local run verifies no interference). Add explicit step: 'Run full smoke suite; confirm existing tests still pass 31/31, and new tests pass deterministically over ≥10 runs.'

**Missing risks the spec omitted:**
- Test flakiness risk: offline-rollover smoke relies on deterministic timing of the 60s throttle gate (_ROLLOVER_RETRY_MS). If the test fast-forwards simTime too quickly or if loadUntil polling interval (150ms) misses the exact moment _rolloverNextTry fires, the test could pass even if _rolloverBusy is still true. Mitigation: plan acknowledges this and recommends explicit fast-forward + polling + explicit state changes (no wall-clock sleep), which is sound. However, the plan should explicitly verify _rolloverBusy is FALSE when recovery occurs, not just check prayerStale.
- Reduced-motion Option A requires a test hook in index.html (URL param ?testReducedMotion=1). If the hook is forgotten or misimplemented, the reduced-motion test will silently pass even if isMotionReduced() doesn't actually freeze the animation. Plan does not detail where/how the hook integrates with isMotionReduced() logic. Example: if the hook only sets a flag but doesn't gate the matchMedia call, the test could see real OS-level reduced-motion instead of the forced state. The hook must be placed INSIDE isMotionReduced() itself or the test must verify both the flag AND the CSS computed values.
- Cloud-continuity test mutates simWx parameter but plan does not clarify whether the mutation happens within the SAME widget load (simTime stays frozen) or via a second loadUntil + scene. If it's a second scene, then _cloudFieldSeed is recalculated based on lat/lon/seed query params at boot—so it MUST be stable. But if the plan intends to mutate simWx live (e.g., by writing to a global query object), the test would need to re-run the weather cycle mid-scene, which is not how the widget works. Plan assumes second load: re-verify this.

**Weak acceptance criteria (a broken change could still pass):**
- Offline-rollover acceptance criteria state 'prayerDate unchanged' but plan does not explicitly check that _lastDateStr has NOT advanced. The test should verify both (1) prayerDate (qaState().cache.prayerDate) is still the old date AND (2) _lastDateStr is still the old dateStr (readable via qaState if exposed, or inferred from prayerLoaded not advancing). Current smoke does not expose _lastDateStr; if it stays hidden, the test cannot PROVE the date didn't advance, only that qaState().cache.prayerDate didn't—which could be a cached stale value.
- Reduced-motion Option B (skip test, document limitation) is safer but leaves a gap. Plan acknowledges this as a tradeoff. The decision between Option A and B is marked as an open question, not a firm choice. If Option B is chosen post-review, the plan is weaker: no regression gate for a known behavior (motion freezing under OS reduced-motion).
- Cloud-continuity easing verification is listed as 'optional' in the plan but the primary acceptance criteria only check seed stability, not easing smoothness. The plan claims 'coverage does NOT snap' as desired behavior but provides no explicit assertion for it (coverage history tracking). This is acceptable as a future enhancement, but it means the test does not fully verify the 'continuity' promise.

**Scope concerns:**
- Plan adds ~80–120 lines to tests/smoke.html but does NOT require changes to index.html for offline-rollover or cloud-continuity tests. However, reduced-motion Option A DOES require a new if guard in index.html line 509 (inside isMotionReduced() function). This is a minimal change but MUST be gated by ?testReducedMotion=1 URL param to avoid production-path side effects. Plan acknowledges this as 'minimal if guard' but does not provide the exact code. This is appropriate for a plan document, but implementers must be careful.
- Plan states that reduced-motion tests can use a 'test hook' but does not clarify whether the hook integrates into index.html source or is injected at test time (e.g., via `ww.window.isMotionReduced = ...` mock in smoke.html). If mocking at test time, then the hook risks breaking when renderMoon() or paint() reference the ORIGINAL function closure, not the mocked one. The safest approach is a URL-param conditional gate in index.html, which the plan implies but doesn't explicitly state.
- The plan defers 'Milky Way easing' and 'cloud coverage history tracking' as future work, which is correct. However, acceptance criteria do not include a 'no regression on existing 31 tests' explicit check. Plan assumes existing smoke tests are safe, but adding new test scenes could introduce race conditions (e.g., if framerates vary, the 150ms polling interval might miss state transitions). Plan does not mention how to ensure new tests do not interfere with the existing 31-test suite run (e.g., shared state, cache pollution).

**Grounding issues (claims to re-check against current code):**
_(none)_

**Reviewer notes:** GROUNDING: All code anchors verified. Line 509 (isMotionReduced), 999–1000 (_prayerStale/_rolloverBusy), 1308 (_cloudFieldSeed), 1848 (cloudFieldSeed exposed), 1854 (prayerStale/rolloverPendingMs exposed), 1933–1951 (day-rollover branch), 1601 (_REDUCED = isMotionReduced()), 1636–1637 (--sunpulse freeze), 1649 (--mrad freeze), 1959 (loop reduced-motion path), 1780 (renderMoon before atmosphere), all match current index.html exactly. RENDER BOUNDARY: plan respects it—offline-rollover + reduced-motion + cloud-continuity are all purely observational (read qaState, read computed styles, no DOM writes in test). MOON INVARIANTS: plan does NOT touch moon logic; smoke tests moon via existing tiers (moon orientation, lit-side emoji match). No risk of reintroducing parallactic rotation or spinning. FORBIDDEN REGRESSIONS: plan does not paint dawn, does not mutate --sunvx/--suny optics, does not alter motion from qaState().clouds.hash. DETERMINISM: plan emphasizes polling + explicit state changes, no sleep loops—sound. OPEN DECISIONS: Reduced-motion Option A vs B. Cloud-continuity easing (optional). Offline-rollover recovery method (hybrid recommended). All are recorded in the plan. ACCEPTANCE: criteria are clear and testable, though they require the fixes above to close gaps (especially _rolloverBusy check, reduced-motion decision, cloud-mutation clarification). The plan is fundamentally SOUND in structure, scope, and grounding, but requires clarity on three implementation details before code-phase begins.
