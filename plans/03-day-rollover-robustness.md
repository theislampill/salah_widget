# Plan 03 — Fix day-rollover offline robustness — prevent silent replay of previous day's prayer times

> **Status:** ✅ DONE (2026-06-16). Module-scope `_prayerStale`/`_rolloverBusy`/`_rolloverNextTry` + `_ROLLOVER_RETRY_MS=60000`; rollover branch now advances the day only on confirmed data (cache-hit or fetch-success), throttles the refetch, and updates `lastDate` on confirm so `prayerDate` is honest; `qaState().cache` exposes `prayerStale` + `rolloverPendingMs`. **Decision on the "optional UI cue": NOT added** — a visible card change is outside the no-UI-redesign constraint and the user isn't here to sign off; the truthful signal lives in `qaState` (a visible cue remains an opt-in follow-up). Verified by deterministic preview repro: offline midnight → `prayerStale:true`, `prayerDate` stays `16-06-2026`, `rolloverPendingMs:~58000` (throttle armed); cache-seed recovery → advances to `17-06-2026`, stale clears. New smoke (28/28).  ·  **Class:** correctness  ·  **Priority:** P1  ·  **Effort:** M  ·  **Risk:** med
> **Do now?** Yes — recommended soon  ·  **Plan-review verdict:** `needs-fixes` (7 required fixes — see end)  ·  **Depends on:** none
>
> Read-only plan from `/implementaudit` (workflow `wf_f498de17-f7b`, investigate → adversarial critique). Grounded against `index.html` @ commit `91d0fc1` (~1951 lines). **No source was changed.** Line numbers drift — re-verify the anchors before editing.

## Problem
Crossing midnight offline (simulated or real) with an empty cache for the new day silently displays the previous day's prayer times. The bug goes undetected because no stale-state signal is surfaced to the user or qaState(). This is a truthfulness violation: the widget claims to show today's prayers but shows yesterday's.

## Root cause
In the loop() day-rollover branch (lines 1922–1926), _lastDateStr is advanced BEFORE the new day's data is confirmed. The fetch at line 1924 has an empty .catch() with no retry, no stale flag, and no observable state change if it fails. If the new-day cache is absent (loadCache returns null at line 1923) and the fetch fails (offline or network error), the code silently renders `today` (still holding yesterday's data) without advancing it or signalling staleness.

## Current behavior
- Sim-midnight is crossed: n.dateStr != _lastDateStr triggers the branch.
- _lastDateStr is immediately advanced to n.dateStr (line 1925).
- loadCache(ds) is attempted; if the new-day cache is absent, it returns null and today is NOT updated (line 1923 no-op).
- fetchTimings(ds) is called but its .catch is empty; if it fails, nothing happens (line 1924).
- render() is called from line 1930 on the next sim-second, painting yesterday's times with tomorrow=null, day-date = tomorrow (AH only), creating a false snapshot.
- No qaState() field exposes that the rollover failed or that prayer times are stale.

## Desired behavior
- _lastDateStr is only advanced AFTER the new day's data is confirmed present (either cached or fetched).
- If the new-day fetch fails offline, a throttled retry is scheduled (no infinite loop, but no silent surrender).
- A stale-state signal is added to qaState() (e.g., cache.prayerStale / cache.rolloverPending / cache.rolloverFailedAt) and optionally a subtle non-intrusive UI cue (CSS data attribute or class).
- If the fetch fails and there is no cache, today is NOT advanced, and qaState() truthfully reports the old date + stale state so the UI can warn or degrade gracefully.
- Times are never presented as "today" unless today's data is actually present.

## Code anchors (re-verify line numbers before editing)
**`index.html:574–580 loadCache / saveCache`**
Prayer cache load/save. loadCache returns null if absent or date mismatch — the day-rollover logic treats null as 'must fetch.''

````js
function loadCache(dateStr){ try{ const j=JSON.parse(localStorage.getItem(cacheKey)); if(j&&j.date===dateStr) return j.data; }catch(e){} return null; } function saveCache(dateStr,data){ try{ localStorage.setItem(cacheKey,JSON.stringify({date:dateStr,data})); }catch(e){} }
````

**`index.html:581–596 fetchTimings`**
Prayer-times fetch with 3 internal retries (900ms, 1800ms). Throws on final failure. The DAY-ROLLOVER fetch caller swallows this with .catch(()=>{}).

````js
async function fetchTimings(dateStr){ const u=`https://api.aladhan.com/v1/timings/${dateStr}?latitude=${enc(lat)}&longitude=${enc(lon)}&method=${enc(method)}&school=${enc(school)}`; let err; for(let i=0;i<3;i++){ try{ const r=await fetch(u,{cache:"no-store",referrerPolicy:"no-referrer"}); const j=await r.json(); if(j&&j.data&&j.data.timings){ if(j.data.meta&&j.data.meta.timezone) tz=j.data.meta.timezone; return j.data; } throw new Error("bad api"); }catch(e){ err=e; if(i<2) await sleep(900*(i+1)); } } throw err; }
````

**`index.html:1922–1926 day-rollover branch in loop()`**
THE BUG SITE: _lastDateStr is advanced BEFORE confirming new-day data; empty .catch swallows fetch failure silently.

````js
if(n.dateStr!==_lastDateStr){ if(_lastDateStr){ tomorrow=null; const ds=n.dateStr, c=loadCache(ds); if(c) today=c; fetchTimings(ds).then(d=>{today=d;saveCache(ds,d);}).catch(()=>{}); renderMoon(); _starsProjected=false; } _lastDateStr=n.dateStr; }
````

**`index.html:1897 initialization`**
_lastDateStr initialized from boot-time lastDate. On the first midnight-crossing, _lastDateStr is non-empty, so the branch triggers.

````js
let _raf=null, _onScreen=true, _lastSec=-1, _lastDateStr=lastDate||"", _lastWx=0, _lastCloud=0;
````

**`index.html:1773–1810 render() prayer UI updates`**
render() derives date display and prayer state from today (and tomorrow). If today is stale, the display is false.

````js
const M=model(); ... $('#ce').innerHTML = g ? ... ; const ahH = (afterMaghrib && tmrwH) ? tomorrow.date.hijri : h; ...
````

**`index.html:1840–1843 qaState().cache`**
qaState().cache currently reports prayerDate (lastDate) and prayerLoaded (!!today), but NO flag for rollover failure / stale prayer times. Must add prayerStale / rolloverPending.

````js
cache:(()=>{ const wxAge=lastWxAt?Math.round((Date.now()-lastWxAt)/1000):null; return { weatherSource: weather?(weather.src||"current"):"none", weatherAgeSec: wxAge, weatherStale: (SIM.wx!=null)?false:(lastWxAt? (Date.now()-lastWxAt)>15*60*1000 : true), lastWeatherRefresh: lastWxAt?new Date(lastWxAt).toISOString():null, forecastTrackLoaded: !!weatherTrack, prayerDate: lastDate||null, prayerLoaded: !!today, tomorrowLoaded: !!tomorrow, simulated:(SIM.wx!=null||SIM.time!=null||SIM.moon!=null) }; })()
````

**`index.html:1972–1976 boot() initial fetch`**
Boot DOES wait + handles errors; day-rollover does NOT. Inconsistency in error policy across call-sites.

````js
const ds=nowParts().dateStr; const cached=loadCache(ds); if(cached){ today=cached; if(cached.meta&&cached.meta.timezone) tz=cached.meta.timezone; lastDate=ds; render(); } try{ today=await fetchTimings(ds); saveCache(ds,today); lastDate=ds; render(); }catch(e){ if(!today) showError("Could not load prayer times"); }
````

## Approach
1. **Add stale-state tracking.** Introduce a module-scoped `_prayerStale = false` flag and a `_rolloverFailedAt = null` timestamp (to throttle retries). Also track `_rolloverRetries = 0` to limit retry attempts.

2. **Restructure the day-rollover branch (lines 1922–1926).** The logic becomes:
   - Check if date changed: `if(n.dateStr !== _lastDateStr && _lastDateStr)` (only if we have a prior date, to skip t0 boot).
   - Attempt to load new-day data: `const c = loadCache(ds); if(c) { today = c; _prayerStale = false; _lastDateStr = ds; }`
   - If cache miss, DO NOT advance _lastDateStr yet. Instead, try fetchTimings with a new error handler that:
     - On success: advance _lastDateStr, clear stale flags, reset retry count.
     - On failure: set _prayerStale = true, record _rolloverFailedAt = now, increment retry counter.
   - Throttle retries: only attempt fetch if (now - _rolloverFailedAt > RETRY_DELAY) and retries < MAX_RETRIES.

3. **Expose stale state in qaState().** Add to the cache object:
   - `prayerStale: _prayerStale` — boolean flag indicating the prayer times may be from a previous day.
   - `rolloverPendingMs: _rolloverFailedAt ? (now - _rolloverFailedAt) : null` — elapsed time since a failed rollover attempt, for debugging.

4. **Optional: subtle UI cue.** If `_prayerStale`, add a class or data-attribute (e.g., `data-stale="prayer"`) to `.c` so CSS can render a very faint visual indicator (e.g., a 1–2px bottom border, a slight desaturation, or a corner chip). The cue must be non-intrusive (fail closed: subtle, not alarming) and must NEVER be hidden by error-hiding.

5. **Test deterministically in smoke.html.** Add a new integration scene that forces a day rollover offline (use `?simTime=23:59` then `?simTime=00:05` with no cache / network forced offline via dev tools) and assert qaState().cache.prayerStale === true and qaState().cache.prayerDate != qaState().sim date on the second load.

6. **Preserve the single-file character.** All changes are scoped to the boot() closure and the qaState() function; no new files, no npm, no build step.

## Alternatives considered (and rejected)
- **Never advance _lastDateStr until data is confirmed; always retry on fail.** — Infinite retry loop risk if network is down for hours. Throttling + finite attempt count is safer. Also, silently retrying forever masked the bug; the user deserves to know a rollover is pending.
- **Fail-fast: if rollover fetch fails, show an error dialog.** — Harsh UX for a transient offline glitch at 3am (common). Stale-state flag + optional subtle cue is user-friendly and truthful without being alarming. The widget degrades gracefully.
- **Cache both today and yesterday; if rollover fails, keep showing yesterday + label it 'last known'.** — More complex state machine. The truthfulness requirement is simpler: don't show yesterday as if it's today. A stale flag is sufficient; the user can decide what to do.
- **Use Service Worker to handle offline cache with a fallback strategy.** — Violates the single-file / no-build constraint. SW requires manifest registration and separate JS. Not justified for a straightforward fix.

## Owner / source touchpoints
- index.html:1897 _prayerStale init (new)
- index.html:1919–1926 loop() day-rollover branch (REWRITE)
- index.html:1840–1843 qaState().cache (ADD prayerStale / rolloverPendingMs)
- index.html:~1750 data-attribute conditional in paint() or render() (OPTIONAL, if UI cue added)
- tests/smoke.html (ADD integration scene for offline day-rollover repro)

## Regression risks (forbidden-regression guardrails)
- Modifying the day-rollover loop branch could accidentally break the boot-time initialization or cause a double-render. MITIGATION: preserve the exact condition `if(_lastDateStr)` to skip rollover on first boot.
- The retry throttle must not fire on every frame (would spam console). MITIGATION: timestamp-check _rolloverFailedAt, require > 30–60 s elapsed before retry.
- Adding data-stale attribute must not interfere with existing data-fx behavior. MITIGATION: use a separate namespace or only add the class/attribute in qaState() (diagnostic), not on the DOM in real-time (unless requested by the user).
- If prayerStale is true but the UI cue is too visible, it could confuse users. MITIGATION: make the cue CSS-only, very faint (1–2px border, no text, no emoji), and only show under ?debugLayers=1 or qaState() polling.

## Smoke A — capture BEFORE any change
- 1. Open the widget with live internet at, e.g., 23:55 local time with simTime. Verify today's prayers load and cache saves. 2. Force offline (DevTools > Network > Offline). 3. Advance simTime to 00:05 (next day). 4. Observe: qaState().cache.prayerStale should be FALSE (today's cached data is still shown, which is OK; no network is available yet). 5. Reconnect network. 6. Advance simTime to 00:15. 7. Observe: qaState().cache.prayerStale should become FALSE again once the new-day fetch completes. 8. Verify qaState().cache.prayerDate updates to tomorrow's date. 9. Render shows new day's Fajr time. 10. qaState().cache.rolloverPendingMs is null (no failed retry in flight).

## Smoke B — verify AFTER the change
- 1. Open the widget with live internet. Load today's prayers. 2. Force offline and navigate to ?simTime=23:55 (clearing hash to bypass cache). 3. Wait 5s. 4. Advance simTime to 00:05 (midnight). 5. Inspect qaState(): prayerDate should still be yesterday (because new-day fetch failed + no cache), prayerStale should be TRUE, rolloverPendingMs should be > 0. 6. Verify the rendered prayer list still shows YESTERDAY's times (and a subtle stale cue if implemented). 7. Reconnect network. 8. Advance simTime to 01:00 (to trigger retry on next loop). 9. Observe prayerStale → FALSE, prayerDate → new day, rendered times update. 10. Take a screenshot showing the transition from stale to live. NO SILENT REPLAY of yesterday as today.

## Acceptance criteria (falsifiable)
- DETERMINISTIC REPRO: cross sim-midnight offline with an empty cache for the new day using two device-offline dev-tools scenes (1. with cache present, 2. without cache). Verify smokeA and smokeB pass. (Screenshots + QA log)
- qaState().cache exposes prayerStale (boolean) and rolloverPendingMs (ms since failed rollover, or null). Both fields are read in qaState() without throwing. (qaState() JSON dump)
- When prayerStale === true, the rendered prayer times and date are NOT falsely presented as 'today' — either the old date is shown in footer with a stale indicator, or the widget does not advance _lastDateStr until data is confirmed. (screenshot comparison before/after rollover)
- Throttled retry: the rollover fetch is NOT attempted more than once per ~60 seconds during an offline window. (motion telemetry or console log showing retry delay)
- Optional UI cue (if implemented): a very subtle non-intrusive visual (e.g., 1–2px border, faint desaturation, or a corner chip) appears ONLY when prayerStale is true and is removed once stale state clears. The cue does NOT hide or override error messages. (screenshot with and without cue)
- Boot-time init still works: online at boot, load today's prayers, cache them. Verify no regression in the prayer list, arc, or date display. (smoke.html integration test: boot with live network passes)
- AH roll-over semantics unbroken: after Maghrib, the AH date updates to tomorrow even if the new-day fetch is still in flight. (qaState() shows afterMaghrib state correctly)

## Rollback
The day-rollover branch (lines 1922–1926) is small and scoped. Rollback: revert the entire boot() closure to the prior version. No data-migration or cache-invalidation needed (the stale flag is purely diagnostic, not persisted). A fast-forward cherry-pick is also safe: the stale-state tracking is new code that doesn't interfere with the old branch.

## Dependencies / sequencing
_(none)_

## Open questions
- Should the retry throttle delay be ~30s, ~60s, or ~300s? At 1 Hz rAF, a 60s delay means ~60 frames between attempts; 300s (~5 min) is more conservative if the network is flaky. Recommend 60s as a balance: observable user-facing recovery, but not spam.
- If the rollover fails and there is no cache, should we keep rendering yesterday's times or show a minimal error? RECOMMEND: show yesterday's times + a subtle stale indicator (no harsh error) so the user can manually refresh if needed.
- Should the retry counter cap at 3 or 10 attempts? With a 60s throttle, 10 attempts = 10 min of offline time before giving up. RECOMMEND: cap at 3 (180s = 3 min), then stop retrying but keep the stale flag active. The user can manually refresh or reconnect.
- Is the qaState().cache.rolloverPendingMs diagnostic field valuable for the end user, or only for developers debugging offline? It is useful for telemetry / log analysis. RECOMMEND: include it, but don't surface it in the UI unless ?debugLayers=1.

---

## Plan review (adversarial critique) — fold these in BEFORE executing
**Verdict:** `needs-fixes`

**Required fixes (resolve before writing code):**
1. CRITICAL: Clarify UI cue status (mandatory vs optional). The Approach says 'Optional: subtle UI cue' but this creates ambiguity in acceptance criteria and implementation. Decide and document clearly.
2. REQUIRED: Fix line-number anchor. Change 'index.html:1972–1976 boot() initial fetch' to 'index.html:1884–1888' (the actual fetchTimings + saveCache + lastDate block inside boot()). Update any derived references.
3. REQUIRED: Add render-boundary safeguard comment in code plan. State explicitly: '_prayerStale is NEVER read by atmosphere(); it is qaState() diagnostic only. Any code that reads _prayerStale outside qaState() is a refactoring violation.'
4. REQUIRED: Clarify renderMoon() call timing. Specify: call renderMoon() only if (today was updated from cache OR fetch succeeded), not on every day-rollover trigger. Document the exact condition.
5. REQUIRED: Strengthen smokeB test. Add explicit assertion: `qaState().cache.prayerDate === yesterday` (not just `prayerStale === true`). Include a screenshot showing the date footer still displays yesterday's date while prayerStale is true.
6. REQUIRED: Replace manual 'console log' test (criterion #4) with deterministic assertion. Expose rolloverPendingMs or getRetryDelay() via qaState(), then assert in smokeB that retry delay is >= 60s (e.g., RETRY_DELAY_MS). Do not rely on visual inspection of logs.
7. REQUIRED: Define qaState().cache.rolloverPendingMs return value. Specify: null when no rollover is pending, or >0 ms since the last failed rollover attempt. Document this clearly in the plan and in code comments.

**Missing risks the spec omitted:**
- Render-boundary violation risk: the plan introduces _prayerStale as a module-scoped variable. If a future change accidentally references _prayerStale inside atmosphere() (a PURE function), the render boundary is violated. The plan must explicitly forbid reading _prayerStale in atmosphere(); it is qaState() diagnostic only. Add a code comment to enforce this.
- If loadCache(ds) succeeds on day-rollover, the current code calls renderMoon() unconditionally (line 1924). The plan does not clarify whether renderMoon() should be called only on cache hits, only on fetch success, or always. This may cause redundant moon-rendering or missed updates. The plan must specify the exact timing.

**Weak acceptance criteria (a broken change could still pass):**
- Smoketest B ('cross midnight offline, no cache, expect prayerStale===true') does not verify that prayerDate is NOT advanced. A broken implementation that sets prayerStale=true but also advances _lastDateStr to the new date will pass the test, yet display a false snapshot (new date + old times). REQUIRED: add explicit assertion in smokeB: qaState().cache.prayerDate must still equal yesterday's date (or verify footer display shows old date).
- Acceptance criterion #2 ('qaState().cache exposes prayerStale + rolloverPendingMs without throwing') does not specify what rolloverPendingMs should return when no rollover is pending (null? 0? undefined?). The plan text says 'null' but the test does not enforce this. Add explicit field definitions to qaState().
- Acceptance criterion #4 ('Throttled retry: fetch not attempted more than once per ~60s') requires manual inspection ('motion telemetry or console log showing retry delay'). A broken implementation that retries every frame but logs timestamps will pass. REQUIRED: replace with a deterministic check: expose getRetryDelay() or rolloverPendingMs via qaState(), then assert getRetryDelay() >= 60000 * (retry attempt count) in smokeB.
- Acceptance criterion #5 says the UI cue is 'OPTIONAL' if implemented, but the Approach section #4 lists it as part of the fix: 'Optional: subtle UI cue'. This is contradictory. CLARIFY: Is the stale-state visual cue mandatory (always show when prayerStale=true) or truly optional (may be omitted)? This affects the design surface and testability.

**Scope concerns:**
- No single-file violation, no new files, no npm. Scope is justified (minimal fix to the day-rollover branch). The plan stays within the boot() closure and does not refactor sacred render/loop/atmosphere arc. ✓

**Grounding issues (claims to re-check against current code):**
- Line number drift: plan cites 'index.html:1972–1976 boot() initial fetch' but boot() spans lines 1861–1891, not 1972. The quoted code (fetchTimings async call + saveCache + lastDate assignment) is at lines 1884–1888, not 1972–1976. Update anchor to correct line range.
- The plan references 'index.html:1773–1810 render() prayer UI updates' but render() begins at line 1771 (not 1773) and the qaState-relevant code is mixed across multiple functions. The reference is approximately correct but off by 2 lines for the start.

**Reviewer notes:** ["The bug and root cause are well characterized: _lastDateStr is advanced before new-day data is confirmed, and a silent empty .catch() swallows fetch failures. The fix (stale-flag + throttled retry) is sound.", "Render boundary and TDZ ordering are protected well; no forbidden regressions are at risk (sky, moon, optics, dawn are all isolated from the day-rollover fix).", "The smokeA test (happy path with cache + network) is straightforward and will pass. smokeB (offline + no cache + expect stale state) is the critical test but requires the assertions above to be robust.", "Optional: The plan mentions 'optional' UI cue 3 times but does not decide. Recommend making the cue MANDATORY so the user is always informed when prayer times are stale (fail-closed: stale is better than silent). A 1–2px bottom border or a very faint opacity shift is non-intrusive enough to ship.", "The plan's ~30–50 line addition is minimal and justified. No refactoring of sacred arc."]
