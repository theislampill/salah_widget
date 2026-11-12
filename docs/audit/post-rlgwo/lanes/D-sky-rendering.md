> **Lane working paper.** This is supporting detail produced by one census lane of the post-RLGWO audit at baseline `363c3e53`. It is superseded by [IMPLICIT_STATES.md](../../../../IMPLICIT_STATES.md), [REPORT.md](../REPORT.md), [CROSSWALK.md](../CROSSWALK.md) and [FINDINGS.md](../FINDINGS.md) wherever they differ; the integrator's corrections are listed in REPORT.md. Probe paths `probes/<lane>/` refer to [../probes/](../probes/README.md).

# Lane D — sky, cloud, star and optical rendering; scene composition; native sky workers; invalidation and lifecycle

Baseline: main `363c3e53` (worktree `post-rlgwo-audit`). Historical reference: original audit at `f71fef6c`.
Read-only, documentation-only. Line numbers are approximate at the baseline. Authored source is cited first;
the generated counterpart is noted as `gen:`. The Moon pipeline (lunar runtime, detail owner, PBR, lunar
workers) belongs to lane E and is referenced here only where the sky side consumes it.

Conventions. Enforcement is given on three axes: **Doc** (none / comments / state contract / registry),
**Impl** (implicit / partly explicit / explicit and enforced), **Verif** (none / unit tests / mutation or
negative controls / native or browser evidence / independent review). "Observed" means read in source or
returned by a test or probe I ran. Nothing in this file is observed browser runtime behaviour unless it cites
a retained native record, and those records are cited as other people's evidence.

---

## 1. Machine census

### N13 — Sky scene identity, first-document warrant and renderer-surface commit
- **Scope / decision:** decides when an accepted celestial scene is "the" scene, when transitions are suppressed (`sky-pending`, `sky-initializing`), when the Moon surface class may show (`moon-ready`, `mask-on`), and when the first full scene is committed.
- **Sources:** `src/native/index.html` `skySceneIdentity` 2217-2220, `beginSkyScene` 2225-2232, `updateSkySurface` 2236-2241, `commitSkyScene` 2242-2252, `paintCelestialWithoutTimetable` 3017-3040, `paint` scene-key adoption 3244-3249, `boot` 3779-3849. `tools/build_native.py:72-73` injects `SalahSkyPreview.clear` + `SalahRealSky.invalidate` at the start of `beginSkyScene` and `SalahNativeSkyHost.notify()` after `commitSkyScene`. gen: `index.html:5655`.
- **State dimensions:** `_skySceneKey` (null / identity string); `_skyCommitted` (bool); `_skyMoonPresence` (0..1); `_skyInitialDocument` (one-use bool); card classes `sky-pending`, `sky-initializing`, `moon-ready`; mask class `mask-on`; cloud publication receipt reset by `withdrawCloudState(null,"scene superseded"|"uninitialised")` (R000B, 2230).
- **Events / transitions:**

| Event | Guard | Effect |
|---|---|---|
| boot / config apply (non-presentation) / `SalahClock.set` | — | `beginSkyScene`: add pending classes, null key, uncommit, withdraw clouds, (gen) clear preview + invalidate refined |
| `paint(A)` or no-timetable paint sees identity ≠ `_skySceneKey` | identity ≠ null | `beginSkyScene(_skyInitialDocument)` then adopt key |
| `commitSkyScene(A)` | not committed, key set, fresh Moon observation, `_starProjectionKey===_skySceneKey` | paint clouds, force style resolution, remove `sky-pending` then `sky-initializing` |
| `finishInitialSkyDocument` | first call | warrant consumed permanently (also tells Moon runtime) |
| config presentation-only change (R0003) | `change.path==="presentation"` | no scene invalidation (3741-3748) |

- **Identity contents:** `[lat,lon,tz, wall | _simBase:_simTz:_rafT0:TIMESCALE]`; civil day and weather are intentionally excluded.
- **Invariants:** no stale target becomes current by association; the initial warrant is one-use; first complete scene resolves styles before transitions are restored.
- **Failure / recovery:** a `commitSkyScene` precondition that never holds leaves `sky-initializing` (transition suppression) in place; this does not hide content. Moon readiness depends only on `SalahMoonRuntime.surface()` (2238); R0021's native record notes that a Moon-runtime construction failure therefore shows no Moon (routed to lane E).
- **Risks:** `paintCelestialWithoutTimetable` removes `sky-pending` without committing (3037); commit then waits for the full painter. Identity includes `_rafT0`, so each explicit clock control produces a distinct scene even for the same rate/anchor (intended).
- **Enforcement:** Doc comments + `docs/state-contracts/R0021.md` (startup/reveal history); Impl partly explicit; Verif unit tests (`tests/r0021-reveal.cjs` – 17/18 pass, one unrelated byte-pin fail I ran), native evidence from R0021 cells (first-boot, live-handoff).
- **Observed:** identity excludes weather and day; gen injects preview clear + refined invalidate into every `beginSkyScene`. **Hypotheses:** none new. **Unknowns:** real first-paint ordering in browsers other than the retained Chromium/Firefox runs.

### N14 — Star projection / catalogue contract and held appearance
- **Scope:** which component owns stars. In source a 420-star synthetic catalogue with CSS twinkle; in the generated app the block is replaced by a readiness stub and the refined/preview real-sky catalogue owns star pixels.
- **Sources:** source `src/native/index.html` 2102-2214 (`projectStars`, `refreshStarAppearance`, `buildStars`); generated replacement `tools/build_native.py:51-67` (gen `index.html:5636`); star pixels `real-sky/native-star-preview.mjs`, worker catalogue `real-sky/native-engine.mjs:10-26`; CSS `.milkyway,.stars,.starglints{display:none!important}` `tools/build_native.py:84`.
- **States:** generated: `_starProjectionKey` (null / scene key), `_starsProjected` (bool). Source-only: catalogue built/unbuilt, per-star base, `_starLightKey`.
- **Transitions (generated):** `projectStars(date)` records key and validity; invalid → `SalahRealSky.invalidate('invalid native projection input')`. `refreshStarAppearance` is a no-op. `buildStars` clears the three SVG groups. `render()` calls `projectStars` every render while `ADVANCING` (3497), cheap in the stub.
- **Invariants:** one star owner in the shipped app. Positions held in ordinary live view.
- **Scintillation:** the refined job sets `scintillation:{strength:0}` (`real-sky/native-contract.mjs` `nativeJob`, line ~20). `docs/real-sky/QUALIFICATION.md:130-132` states registered-star scintillation stays at the CP9 setting. The generated app therefore has no star-twinkle producer in source; see finding D-F06.
- **Enforcement:** Doc comments + QUALIFICATION.md (DESIGN.md still describes the replaced CSS twinkle); Impl partly explicit (generated substitution is digest-free text replacement guarded by `index()`); Verif unit tests (`tests/real-sky/cp9-scintillation.test.mjs` asserts disabled strength contract), `r0022-lunar-consumers` case "ordinary render refreshes star appearance…" FAILS against generated `index.html` (ran; expects source behaviour).
- **Observed:** stub semantics; strength 0. **Hypotheses:** none. **Unknowns:** whether any visual star motion exists natively beyond preview re-projection under `timeScale`.

### N15 — Cloud population, motion integration, coverage and paint cache
- **Scope:** procedural cloud deck: population identity, wind integration, coverage easing/withdrawal, raster and column density for rain coupling.
- **Sources:** `src/native/index.html` `_cloudMotion` 2756, `cloudSceneIdentity` 2757-2761, `syncCloudMotionPreference` 2762-2764, `rebaseCloudMotion` 2765-2767, `advanceCloudMotion` 2768-2795, `paintClouds` 2817-2877, `applyCloudState` 3222-3241, loop cadence 3880-3883, `setVis` 3892. gen `index.html:6249`, `6654`.
- **State dimensions:** population key (`[lat,lon,seed,wall|anchor]`, day/weather excluded); `phase[3]`, `life[3]`, `wander`, `lastRt`, `paused`, `reduced`; coverage `cov*`/`tgt*`; `_cloudReady`; `_cloudDirty`; `_colDens`; canvas/context.
- **Transitions:**

| Event | Effect |
|---|---|
| identity change | reseed population from position + floor(UTC day at start); reset phases (2771-2779) |
| healthy elapsed 0<Δ≤2 s, visible, not reduced | integrate old wind × Δ × rate, then wrap (2784-2793) |
| hidden / reduced / Δ>2 s | no travel; `lastRt` rebased (2784) |
| visibility or reduced-preference change | rebase / mark dirty (2762-2767, 3892) |
| first admitted deck | snap coverage; `_cloudReady=true` (3233) |
| later deck | ease 0.08 per paint (1 under `ADVANCING`) (3234) |
| decision `unavailable` | `withdrawCloudState` zeroes coverage, density, canvas (2730-2741, 3228-3230) |

- **Invariants:** weather refresh changes coverage/light, never population (R0025); hidden time does not accumulate travel; withdrawal is immediate (truth over continuity).
- **Cadence:** full motion repaints every >76 ms; reduced motion repaints only when dirty (3881-3883). Every `paintClouds` call re-runs `reconcileCloudPublication()` (2818) and the loop also calls it once per frame (3880); `weatherDecision` is memoised (`_wxDecisionCache`, 1720-1744) so the repeated call is a cache hit unless the record object changes (see NEW-D-01).
- **Enforcement:** Doc comments + R000B contract; Impl partly explicit; Verif unit tests (`tests/r0025-context.cjs`, `r0025-continuity.cjs`, `r0025-lifecycle.cjs` all exit 0 — ran), `r0024-cloud-expiry.test.cjs` (not run), mutation harness `r0025-mutations.cjs` (not run: writes files).
- **Observed:** population and integration as tabled; easing is per paint call, so its time constant depends on render cadence. **Hypotheses:** none. **Unknowns:** continuity across bfcache restore (no native restore was obtainable per R0021 record).

### N16 — Precipitation population, cloud-origin gating and lightning
- **Sources:** `buildWeather` 2255-2268 (5 fog, 32 drops, 40 flakes, bolt/flash re-ordered), `tieRainToClouds` 2882-2894, lightning bucket `render` 3528, `genLightning` 3460-3475, publication of `data-fx/precip/lightning` `paint` 3302-3305 and `withdrawWeatherEffects` 2722-2729.
- **States:** particle pool built once (`_sceneBuilt`); `_rainTiedFx` (""/class); per-particle inline `display`; `data-precip`, `data-lightning` on/off; `_lastBolt` bucket.
- **Transitions:** precipitation on → gate each particle on column density > 0.16 × max, only if max ≥ 2; off → clear inline display once. Lightning only when `visualPermissions.lightning` (synthetic `src==="sim"` thunder, or qualified present evidence) and only in the timetable branch; bucket = floor(simNow/2600).
- **Invariants:** forecast/model thunder never authorises lightning (1709-1713); no profile ≠ clear column.
- **Risks:** gating reads `d.style.left` per particle each paint (string parse); bounded (72 nodes).
- **Enforcement:** Doc comments + DESIGN.md; Impl implicit; Verif unit tests (`r0024-particle-origin.test.cjs`, `r000c-weather.test.cjs`; not run here).
- **Observed / Unknowns:** CSS animation completion is not observed by JS.

### N17 — Atmosphere publication, optical fade state and last-consumed diagnostics
- **Sources:** `atmosphere` 3041-~3220, `nativeSolarPresentation` 2909-~2990, `lunarPresentation` 3003, `paintLunarOptic` 3004-3016, `paint` 3242-3325, `applyTheme` 3327-3338, `rememberWeatherEffects` 2714-2721, `qaState` 3539-3624.
- **States:** published CSS variables; per-optic `visibility:inherit` override until computed opacity reaches 0; `_lastMoonPaint` {completed/unavailable/failed, stage}; `_lastWeatherEffects` receipt (new since R000B); `_lastRender`.
- **Transitions:** `applyTheme` records attempt, rethrows on failure (3334-3337) — the native loop does not catch it (see N19). No-timetable path zeroes optics and publishes bodies only (3030-3037).
- **Invariants:** physical eligibility separate from aesthetic opacity; diagnostics report last-consumed, not recomputed, lunar light (3613-3615).
- **Diagnostics side effects:** `qaState()` recomputes `atmosphere(M)`, reads back the cloud canvas, and calls `SalahConfig.storageAvailable()` which writes and removes a localStorage probe key (`src/native/config.js:211-217`). `updateMotionDbg` calls `qaState()` once per second under `&debugMotion=1` (3638).
- **Enforcement:** Doc comments + R001D/R0022 issue contracts; Impl partly explicit; Verif unit tests (`r001d-lifecycle.cjs` exit 0 — ran; `r0022-lunar-consumers.cjs` 9/10 pass — ran).

### N19 — Render loop: painting, visibility, motion side
- **Sources:** `startRenderLoop` 3855-3898 (`loop` 3869-3889, `start/stop/setVis` 3890-3897). gen `index.html:7288`.
- **States:** `_loopStarted`; `_raf` (null/id); `_onScreen`; `_lastSec`; `_lastCloud`; `_lastWx`; CSS `paused`, `fast`, `motionfull`.
- **Transitions:** per frame: simulation check → `maintainPrayerDay` → provider poll (≥30 s, not while `ADVANCING`) → `render()` on new sim-second or dirty → `reconcileCloudPublication` → reduced/full cloud paint → telemetry → `SalahSkyPreview.present` → schedule next. Hidden/offscreen → `stop()` cancels and nulls `_raf`; visible → `start()` only if `_raf` null.
- **Failure:** no `try/finally`; `_raf` is reassigned only at the tail (3888). An exception anywhere above leaves `_raf` holding the id of the frame that already ran, no next frame is scheduled, and `start()` will not reschedule because `_raf` is non-null; only `stop()` (hide) then `start()` (show) recovers. `applyTheme` explicitly rethrows (3336). Contrast: refined `animate` catches and always reschedules (`real-sky/native-host.mjs:253`).
- **Enforcement:** Doc comments; Impl implicit; Verif none for exception recovery.
- **Observed:** as above. **Hypotheses:** NH02 remains (no ordinary reachable throw demonstrated). **Unknowns:** whether any production input makes `render`/`paint`/`paintClouds` throw.

### R01 — Native sky snapshot identity, epoch, freshness and throughput admission
- **Sources:** `real-sky/native-lifecycle.mjs` 8-93; `real-sky/native-contract.mjs` `nativeIdentity` 3-9, `nativeJob` 10-23, `nativeResultCurrent` 25; snapshot producer `real-sky/native-host-hooks.js` `capture` 20-49. gen `real-sky/native-sky.js:1262`, `2158`.
- **State dimensions:** `epoch`; `identity`; `observed{now,utcMs,rate,paused}`; `latest`, `pending`, `displayed` jobs; `availability{status,reason}`; counts; `durations` (WeakMap).
- **Identity key:** `[sceneIdentity, generation, lat, lon, heightM, camera, weather{src,temp,rh,vis,cloud,code,wind}, lp, reducedMotion, allowEstimates, units, tz, timeScale, elevationSource, elevationOwner]`.
- **Transitions:**

| Event | Result |
|---|---|
| identity change / pause toggle / clock jump >1 s | `invalidate` → epoch++ → `onInvalidate` (host `clear`) |
| displayed result older than 30 s accepted UTC | `displayed=null`, `onInvalidate('native frame expired')` without epoch bump |
| request: same pending UTC / pending / unchanged / throttled | coalesced (interval min(4 s, 15 s/rate)) |
| result for stale job | rejected; `rate-throughput` availability ONLY if same epoch AND same identity AND rate>1 AND age >30 s (24-26) |
| result current | `available/current-frame`; `onResult` |
| dispose | invalidate, terminal, queue disposed |

- **Consumed fields:** `nativeJob` uses only `weather.vis`, `weather.temp`, `weather.src` (and acceptance bool); `rh`, `cloud`, `code`, `wind` are in the identity but not in the job (D-F02).
- **Risks:** an identity that changes faster than one worker render can never accept a result, and that case is not reported as `rate-throughput` (D-F01, demonstrated by probe).
- **Enforcement:** Doc comments; Impl explicit and enforced (single class, fenced); Verif unit tests (`native-lifecycle.test.mjs`, `native-contract.test.mjs` pass — ran) + R0027 native run1 recorded `rate-throughput` at 120×.

### R02 — Latest-only serialized render queue
- **Sources:** `real-sky/core/src/latest-render-queue.mjs` 1-31 (copied core).
- **States:** `#next`, `#busy`, `#pending` (≤1), `#disposed`.
- **Transitions:** submit supersedes prior pending; drain one; publish only `id===#next`; `finally` drains newest; dispose resolves pending as disposed.
- **Risk:** a throwing `onResult` hook (the lifecycle's own `onResult` throws on a non-ready current result, `native-lifecycle.mjs:29`) is caught by the queue's `catch` and routed to `onError` for the same id — consistent. Unchanged since f71fef6c.
- **Enforcement:** Doc comments; Impl explicit; Verif unit tests.

### R03 — Native asset loader generation, timeout, suspension and retry
- **Sources:** `real-sky/native-assets.mjs` 4-33.
- **States:** `generation`, `controller`, `suspended`, `disposed`, `value.status` (idle/loading/ready/unavailable/suspended/disposed/superseded).
- **Transitions:** retry: abort prior, `onReset`, race load vs 15 s; suspend: generation++, abort, reset; resume: retry once; dispose terminal.
- **Note:** `start(pack)` is synchronous; if it throws, the loader publishes `unavailable` after `onReset` (22-24); construction custody (R10) now releases the candidate's own resources.
- **Enforcement:** Doc comments + R0021 contract; Impl explicit; Verif unit tests (`native-assets.test.mjs`, `native-construction-ownership.test.mjs` pass — ran) + R0021 native cells.

### R04 — Native asset script, inline pack and page lifecycle ownership
- **Sources:** `real-sky/native-assets.mjs` 38-81 (`reset` 45, `pagehide`/`pageshow` 70-71).
- **Change since f71fef6c (R0021, `dcc8206b`):** `reset` passes `previewHandoff: !suspended && !disposed` and clears the registry slot only if it still holds the retired instance.
- **States:** inline pack consumed once; per-generation script element; `firstFrame` rAF id; listeners.
- **Transitions:** pagehide → cancel first-frame rAF → `suspend()` → refined `dispose({previewHandoff:false})`; pageshow persisted → `resume()` → `retry()` (refetches local `native-data.js` with a new generation query unless the inline pack was used).
- **Gaps:** the preview owner is not suspended on pagehide (see NEW-D-03). bfcache restore was never obtained natively (R0021 §D, "Back/forward cache").
- **Enforcement:** Doc comments + R0021; Impl partly explicit; Verif unit tests + R0021 native (non-persisted navigation cell PASS; persisted restore only synthetic).

### R05 — Reference worker client boot, RPC deadlines and fallback mode
- **Sources:** `real-sky/core/src/reference-worker-client.mjs` 1-53; `real-sky/native-worker-policy.mjs` 1-7.
- **States:** `#mode` (starting/worker/main-thread-fallback/disposed), `#ready`, `#pending` map, `#bootTimer`, `#warnings`.
- **Transitions:** boot timeout 15 s (native-host passes `timeoutMs:15000`) → fail worker; per render timeout 15 s; failure → `requireNativeWorker` throws (no main-thread physics). Unchanged.
- **Risk:** `#warnings` has no cap; one worker failure per instance makes it practically bounded.
- **Enforcement:** Doc comments; Impl partly explicit; Verif unit tests (`cp9-worker-policy.test.mjs` pass — ran).

### R06 — Sky worker boot, engine ownership and transferable raster response
- **Sources:** `tools/build_native.py:31-34` (wrapper text), gen `real-sky/native-worker.js` tail; engine `real-sky/native-engine.mjs` 7-27.
- **Transitions:** boot constructs `NativeSkyEngine` then `ready`; render before boot → error with id; boot error → `{kind:'error', id:undefined}` → client treats as startup failure; unhandled rejection → `fatal`.
- **Per-render recomputation (source):** `catalogue.emitters` re-filters the whole catalogue on every render (`native-engine.mjs:25`); `projectCatalogue` per render is required by physics.
- **Enforcement:** Doc none beyond comments; Impl implicit; Verif unit tests (`native-engine.test.mjs`, not run).

### R07 — Diffuse asset admission, cancellation and content cache
- **Sources:** `real-sky/core/src/diffuse-assets.mjs` 14-69. Cache bounded to manifest entries (comment line 49: at most three). Unchanged.
- **Enforcement:** Doc comments; Impl partly explicit; Verif unit tests.

### R08 — Sky catalogue replacement generation and last-result authority
- **Sources:** `real-sky/core/src/scene.mjs` 11-21. Unchanged. Impl explicit; Verif unit tests.

### R09 — Engine binding selection, load keys and declared physical fallback
- **Sources:** `real-sky/native-engine.mjs` 10-14 (`loaded` set after first `store.load` regardless of outcome); `real-sky/core/integration/resilient-sky-bridge.mjs` 7-18; `physical-sky-bridge.mjs` 5-18. Unchanged. Failed embedded tier stays CP6 fallback until full asset retry (declared). Impl implicit; Verif unit tests.

### R10 — Refined sky construction, accepted frame, displayed frame and DOM commit
- **Sources:** `real-sky/native-host.mjs` `startNativeSky` 60-272. gen `real-sky/native-sky.js:2388`.
- **Change since f71fef6c (R0021 `dcc8206b`, `145b7ba9`; R000B `ea9f8300`):** dispose-then-construct (65); acquisition-time custody `own/release` (70-71) with reverse unwind and primary-cause rethrow (267-271); canvas attached only after a 2D context (75-76); `status.retirement` record and idempotent dispose (263); registry cleared only while registered (264); cloud authority receipts `reconcileClouds/cloudsCurrent` fence compose/publish (R000B, 119, 132, 141, 158-159, 172, 238).
- **State dimensions:** `frame/job` (accepted), `paintedFrame/paintedJob` (displayed), `pendingJob` (decode in flight), `previousPresentation`, `previousSolarMask`, `status.status` (loading/pending/ready/unavailable/retiring/disposed), `status.retirement`, `disposed`.
- **Transitions:**

| Event | Guard | Effect |
|---|---|---|
| `accept(result)` | current, ready | (day/twilight) UI-thread `nativeAtmosphereFields`+`nativeSkyPresentation` (226-228); store frame; `compose()` |
| `compose()` | frame, not disposed | fences; skip if `sameNativePresentation`; else encode, prepare mask, `solarPublication.publish` |
| `publishComposition` | same frame/job, current, cloud receipt current before and after detail compose | putImageData + mask + classes |
| `clear(reason)` | — | withdraw pixels/classes; preview handoff unless `retirement.previewHandoff===false` |
| `failure(e)` | — | retain original displayed job only if still current and cloud receipt current; else clear |
| `animate` | every rAF | try/catch → `failure`; always reschedules (253) |
| `dispose` | not disposed/retiring | record retirement, lifecycle dispose, release all, rethrow first error |

- **Allocation per compose (source):** new `Uint8ClampedArray` + `ImageData` for every non-skipped compose (181, 193); `foreground.capture` does two `getImageData` readbacks (composition 154-156); a changed cloud alpha produces a new PNG data URL (`prepareSolarMask` 127-128) and an `Image.decode`. Compose is attempted every 50 ms when not paused (250 ms reduced) (253).
- **Enforcement:** Doc comments + `docs/state-contracts/R0021.md` lifetime map; Impl partly explicit (custody/retirement explicit; accepted/displayed split implicit in closure variables); Verif unit tests + mutation (17/17 killed per R0021 record) + R0021 native cells (construction, census, retirement-navigation PASS in Chromium and Firefox) + independent review (PASS_WITH_FINDINGS per R0021 §F).

### R11 — Solar cloud mask decode-before-publish transaction
- **Sources:** `real-sky/native-composition.mjs` `NativeSolarMaskPublication` 36-68.
- **Change (R000B):** `pendingContext` kept so callers can cancel a pending decode whose cloud receipt is no longer current (`native-host.mjs:159`, `native-preview-host.mjs:137`).
- **States:** `revision`, `pending{mask,image}`, `pendingContext`, `decoded`, `displayed`, `disposed`.
- **Risk (RF04 unchanged):** no wall-clock settlement bound; R0021 explicitly keeps it UNVERIFIED with no timeout feature.
- **Enforcement:** Doc comments + R0021 ("TA3 per-instance bounds"); Impl partly explicit; Verif unit tests (`cp9-mask-performance.test.mjs`, `native-composition.test.mjs`; not run).

### R12 — Preview base, pending paint, current display and shared DOM handoff
- **Sources:** `real-sky/native-preview-host.mjs` 10-194. gen `index.html:2911` (preview bundle is inline in the head).
- **Change (R0021 10.3, R000B):** refused 2D context returns without attaching (16); custody with unwind (19-27, 189-193); cloud receipt fences (61, 75, 88, 136-137, 164).
- **States:** `value` (current preview), `pendingValue`, `previewFrame`, `baseBytes`, `catalogue`/`catalogueRevision`/`paintedCatalogueRevision`, `nativeDriven`, `disposed`, `status.deadlineMisses` (≤8), card classes `real-sky-preview-ready`, `real-sky-awaiting-input`.
- **Transitions:** `present(now)` calls `update()` when not composed and (catalogue revision changed OR |rate|>10 OR no value OR not current OR >100 ms since paint) (166). `update()` re-renders the numerical background synchronously on the UI thread (`renderNativeBackgroundPreview`, 148) when there is no value, catalogue changed, identity/age not current, or age >20 s (>10 s when |rate|>10) (141). Native loop takes over scheduling on first `present` via the loop (172).
- **Gaps:** healthy `dispose()` (186) does not run its own `owned` releases, so it leaves `window.SalahSkyPreview` pointing at the disposed instance (registry release at 187 runs only on construction failure); no shipped caller invokes `dispose` (grep), so this is latent. In awaiting-input state `present→update→clear` runs every animation frame (D-F04).
- **Enforcement:** Doc comments + R0021; Impl partly explicit; Verif unit tests (`native-preview-host.test.mjs`, construction cases — pass, ran).

### R13 — Asynchronous preview catalogue admission revision
- **Sources:** `real-sky/native-preview-host.mjs` `admitCatalogue` 173-185; `real-sky/native-star-preview.mjs`. Unchanged. `catalogueRequest` generation guards adoption; identical bootstrap does not bump revision. Impl implicit; Verif unit tests.

### R14 — Document head background and initial lunar CSS lease
- **Sources:** `real-sky/native-first-paint.mjs` 10-48; retirement `native-preview-host.mjs` 39-46. Unchanged. Skipped for any `simTime`/`simDate`/`timeScale` fragment (13). `SalahFirstPaint` retired on first successful preview publish or failed currentness. Impl implicit; Verif unit tests (`native-first-paint.test.mjs`).

### R15 — Native snapshot adapter and single paint-hook installation
- **Sources:** `real-sky/native-host-hooks.js` 5-68. Change (R000B): `reconcileClouds()` and `cloudsCurrent()` exported (12-13). `capture(false)` avoids layout; `capture()` measures sun anchor. `notify()` → `SalahRealSky.request()` after every `commitSkyScene` site (gen injection). QA wrapper merges `realSky`/`moonRenderer`.
- **Note:** `reconcileClouds()` is not a pure read: it can withdraw cloud state and repaint the header (`withdrawCloudState`, `src/native/index.html:2739`). It is called from renderer owners (`native-host.mjs:85,158`; `native-preview-host.mjs:47,136`; `native-composition.mjs:132`). The hook comment says "Capture is a consumer"; that is true, but the consumer has effects (D-F08).
- **Enforcement:** Doc comments; Impl implicit; Verif unit tests (`r000b-sky-withdrawal.test.mjs` — pass, ran).

### R16 — Bounded camera/lunar sampling geometry memoisation
- **Sources:** `real-sky/native-preview.mjs` 17-31, 362-382; FIFO at 4 entries each. Unchanged. Impl implicit cache protocol (bounded); Verif unit tests (`cp9-presentation-cache.test.mjs`).

### R17 — Preview raster private-byte custody and lazy fields
- **Sources:** `real-sky/native-star-preview.mjs` 20 (`preparedFields` WeakMap), 139-178. Unchanged. Impl implicit; Verif unit tests.

### R18 — Exact immutable encoding-table initialisation
- **Sources:** `real-sky/native-host.mjs` 11-49; `real-sky/native-encoding.mjs`. Unchanged; one table per realm. Impl implicit; Verif unit tests (`native-encoding.test.mjs`, `native-host-encoding.test.mjs`).

### R31 — Spectral selection and B–V fit retention
- **Sources:** authored transform `tools/native_core_spectral_cache.py` 1-49 applied by `tools/build_native.py:15`; result `real-sky/core/src/spectral.mjs` 9-10, 23-26 (inner `sfFitCache`, FIFO 12,000), 34-43 (outer `sfCache`, add-until-12,000, no eviction). Callers: `sky-background.mjs:75-76`, `native-preview.mjs` twilight fields. gen `index.html:968`, `native-sky.js:299`, `native-worker.js`.
- **Change (R0027, `77014952`, PR #82):** inner bound + FIFO; source/output digests pinned (18-19); vendor bytes untouched.
- **States:** inner map size 0..12,000; outer 0..12,000 (frozen when full). Union of retained sample arrays bounded at 24,000 (test ES27-08 output: `distinctSampleArrays=24000`).
- **Residual:** continuous twilight B–V has near-zero hit rate (test ES27-06: 12,600 altitudes → 12,600 distinct B–V), so each miss still runs a 48-step bisection with a Planck shape per step (23-25). Retention is bounded; recomputation is not reduced.
- **Enforcement:** Doc state contract `R0027.md` + AGENTS.md; Impl explicit and enforced (digest-guarded transform); Verif unit tests + mutation (`spectral-fit-cache-*.test.mjs` pass — ran, 183 total in my run) + browser smoke (R0027 run2, not a bound proof) + independent review (R0027 acceptance reconciliation).

### R32 — Bounded legacy photometry spectral memo
- **Sources:** `real-sky/core/src/photometry.mjs` 27-35 (add below 2048). Unchanged. Impl implicit; Verif unit tests.

### R33 — Atmosphere validation capability and weak coefficient memo
- **Sources:** `real-sky/core/src/atmosphere.mjs` 7 (WeakSet); `sky-background.mjs` 14, 47 (WeakMap keyed by normalised object). Unchanged. Reuse requires object identity; each job normalises a new object, so per-job recomputation (95 bins) is expected. Impl implicit; Verif unit tests.

### R34 — Per-physical-model solar sample grid lifetime
- **Sources:** `real-sky/core/src/sky-background.mjs` 72-96 (`grid` Map ≤ 19×36 nodes per model). Unchanged; a new model per job. Impl implicit; Verif unit tests.

### R35 — Native target-elevation acceptance lease
- **Sources:** `real-sky/native-host-hooks.js` 4-9, 23; injection `tools/build_native.py:69-71`. Unchanged. Impl partly explicit; Verif unit tests (`cp9-elevation.test.mjs`).

### R36 — Catalogue-bound diffuse resource capability
- **Sources:** `real-sky/core/src/diffuse-binding.mjs` 4-18; `registered-starlight.mjs`; bridges. Unchanged. Impl partly explicit; Verif unit tests.

### NEW-D-01 — Preview-lane forecast synthesis feeding the native sky identity
- **Scope:** under `ADVANCING` or `_clockPreview`, the global `weather` record is replaced every `render()` by an interpolated forecast object, and that object is what the sky snapshot, the cloud authority and the weather decision consume.
- **Sources:** `src/native/index.html` `wxAt` 1556-1570 (numeric lerp of rh, wind, cloud, vis, etc.; `temp` rounded; code stepped), `syncWeather` 1573-1581, called from `render` 3485; `selectedWeather` returns the raw record in preview lanes (1380); snapshot weather fields `real-sky/native-host-hooks.js:42`; identity `real-sky/native-contract.mjs:8`.
- **States:** `weather` (object identity changes every render while a track exists); `_wxDecisionCache` misses on each new object (1721).
- **Transitions:** each simulated second (each render) → new weather object → new native identity → lifecycle epoch++ → refined `clear('…')` + preview handoff; preview `update` re-renders its synchronous background on identity change.
- **Effect:** see D-F01/D-F02. With `simWx` set, `syncWeather` returns early (1574), so the R0021/R0027 native runs (`simWx=3…&timeScale=4`, or an in-page current-only record) did not exercise this path.
- **Enforcement:** Doc comments (truthfulness comment only); Impl implicit; Verif none for the sky interaction (probe below is mine, not a repository test).
- **Observed:** source chain; probe reproduces non-acceptance with the real `NativeSkyLifecycle`. **Hypotheses:** this is the mechanism behind the recorded "refined sky can stay pending at `timeScale` ≥ 2 with live forecast weather" observation. **Unknowns:** native worker durations by device; exact browser cadence of `render()` at each rate.

### NEW-D-02 — Cloud publication authority receipt (R000B)
- **Scope:** decides whether painted cloud material (and the refined/preview composition that captured it) is still backed by an eligible weather decision.
- **Sources:** `src/native/index.html` 2685-2752 (`_cloudPublication`, `cloudAuthorityMode`, `cloudAuthorityMatches`, `publishCloudAuthority`, `withdrawCloudState`, `reconcileCloudPublication`, `cloudPublicationCurrent`); writers `applyCloudState` 3239, `beginSkyScene` 2230, render no-model branch 3491, loop 3880, `paintClouds` 2818; consumers in `native-host.mjs`, `native-preview-host.mjs`, `native-composition.mjs:132`.
- **States:** receipt `{revision, state: uninitialised|eligible-published|withdrawn-unavailable|superseded, reason, target, lane, sourceValidAt, retrievedAt, conditionState}` (frozen); private `decision`, `record`, `scene`, `mode`.
- **Transitions:** complete atmosphere with available decision → `eligible-published`; decision unavailable / lane / target / scene / mode change / present-evidence lease expiry → withdraw (zero coverage, density, canvas; header and effects withdrawn). Duplicate publication with identical fields returns the same receipt (2708-2709). Healthy full-model refresh: old receipt remains valid while both records are selected and a prayer model exists (2703-2704).
- **Invariants:** no cloud pixel is published without a current receipt at final publication (re-checked after Moon detail compose).
- **Coupling:** the healthy-refresh branch depends on `model()!==null` (prayer timetable). Without a timetable a changed record withdraws clouds until the next full paint — which cannot run without a timetable; the no-timetable path paints bodies only. This is the R000B policy "when the prayer timetable is unavailable" (`docs/state-contracts/R000B.md` §"Policy when the prayer timetable is unavailable"); recorded as an intentional constraint.
- **Enforcement:** Doc state contract `R000B*.md`; Impl partly explicit; Verif unit tests + mutation (`r000b-sky-withdrawal.test.mjs`, `native-weather-withdrawal.test.mjs` pass — ran; `r000b-remaining.test.cjs` not run) + native (R000B certificate on #11).

### NEW-D-03 — Page-lifecycle fan-out across sky owners
- **Scope:** what happens to each sky owner on `pagehide`, `visibilitychange`, offscreen and persisted `pageshow`.
- **Sources:** `real-sky/native-assets.mjs:70-72` (refined: suspend/resume); `src/native/index.html:3892-3895` (native loop: visibility + IntersectionObserver); `real-sky/native-host.mjs:255` (refined: visibility → forced request); `real-sky/native-lifecycle.mjs:55` (pause toggle → invalidate); `real-sky/native-preview-host.mjs` (no lifecycle listener at all; relies on `capture().paused` and rAF throttling).

| Owner | pagehide | hidden / offscreen | persisted pageshow |
|---|---|---|---|
| Asset loader + refined | suspend → dispose (no preview handoff) | refined frame invalidated (pause is part of R01) | resume → new pack load, new worker |
| Native render loop | (visibility follows) | `stop()`, `.paused`, cloud rebase | `start()` on visible |
| Preview | none | `update` clears + `real-sky-awaiting-input` when paused | none; next `present` rebuilds |
| Cloud motion | — | rebase, no travel | rebase |

- **Risks:** every hide/show and every offscreen toggle withdraws the refined frame and requires a full worker render on return (R01 pause semantics); this is by design but is fan-out. The preview is a page-lifetime singleton with no suspend; before the native loop starts it runs its own rAF (`tick`, 167) indefinitely.
- **Enforcement:** Doc R0021 (retirement only); Impl implicit (distributed); Verif unit (`cp9-page-lifecycle.test.mjs` pass — ran) + R0021 native (non-persisted navigation only; "No restore was obtained in any run").

### NEW-D-04 — Lunar-light eligibility consumption, sky/cloud/star side (R0022)
- **Sources:** `src/native/index.html` `lunarPresentation` → `nativeLunarPresentation` (~2990-3003, `moonLightEligible` 2996), consumers in `atmosphere` 3141, 3156, 3176-3203 (`cloudMoonLit`), `applyCloudState` 3238, `refreshStarAppearance` (source) 2153; generated stub makes star wash a real-sky responsibility (`tools/build_native.py:59`).
- **States:** one eligibility object per atmosphere derivation; recorded into `moonObservation.light` and `_lastMoonPaint`.
- **Observation:** in the generated app two lunar-light producers exist: native `lunarPresentation` (clouds, optics, beam; honours `simMoon*` diagnostics) and the worker's physical Moon (`sky-background.mjs` KS1991, from the real ephemeris for the job's observer). `nativeJob` carries no lunar override. Under diagnostic `simMoon*` the two can disagree; in ordinary live use both derive from real geometry. Hypothesis only.
- **Enforcement:** Doc issue #34 contract; Impl partly explicit; Verif unit tests (`r0022-lunar-consumers.cjs` 9/10, `r0022-baseline-balance.cjs` 9/10 — ran, failures listed in D-F07).

### NEW-D-05 — Diagnostic telemetry state (debugMotion history, qaState)
- **Sources:** `src/native/index.html` `_motHist` 3629-3646 (≤61 entries), `qaState` 3539-3624, `real-sky/native-host-hooks.js:58-67`.
- **States:** bounded history; per-call recomputation.
- **Risks:** in the generated app `_starSampleNow` and `starAnim` query `.stars circle`, which the stub empties (`build_native.py:61`), so the overlay always reports `starΔ 0.000` and `starAnim OFF`; `qaState().stars.visible` counts `_starEls`, which is always empty. `qaState()` performs a localStorage write/remove probe (N17). Bounded; debug-only for the 1 Hz path.
- **Enforcement:** Doc AGENTS.md/DESIGN.md (describe the source implementation); Impl implicit; Verif unit (`r001d-*` exit 0 — ran lifecycle only).

---

## 2. Historical-to-current reconciliation

| Original | RLGWO / commit | Code change (f71fef6c → 363c3e53) | Disposition | Evidence |
|---|---|---|---|---|
| N13 | R000B (#11, PR #72, `ea9f8300`); R0003 (#3, PR #79) | `beginSkyScene` now withdraws cloud receipt (2230); presentation-only config no longer calls `beginSkyScene` (3741-3748) | implemented but not fully verified | unit tests; native first-boot/live-handoff cells (R0021) |
| N14 | none | unchanged | still implicit or vulnerable (doc drift, D-F06) | generated stub; `r0022-lunar-consumers` case fails against generated entry |
| N15 | R000B; R0025 (#37, closed before f71fef6c) | withdrawal through receipt; `paintClouds` reconciles first (2818) | implemented but not fully verified | r0025 suites exit 0; no native continuity record in this lane |
| N16 | R000B | effects withdrawn with receipt in no-model path (3491) | implemented but not fully verified | unit tests |
| N17 | R000B; R001D (#29, pre-f71fef6c) | `_lastWeatherEffects` receipt; `withdrawWeatherEffects` | partly resolved | storage probe side effect remains in `qaState` |
| N19 | none | unchanged loop structure | still implicit or vulnerable (NH02) | no try/finally (3869-3889) |
| R01 | none (indirect: R000B weather fields unchanged) | unchanged | implemented but not fully verified; new interaction D-F01 | my probe; R0027 run1 records rate-throughput at 120× |
| R02, R07, R08, R09, R13, R14, R16, R17, R18, R32, R33, R34, R35, R36 | none | unchanged (`git diff` shows no change to these files) | unchanged — dispositions of the original audit stand (inspected, not re-proved) | diff stat |
| R03 | R0021 (#33, PRs #81/#83) | loader unchanged; reset semantics changed | resolved and independently verified (for construction/retirement) | unit + mutation + native + review |
| R04 | R0021 `dcc8206b` | instance-owned reset; preview handoff intent | implemented but not fully verified (bfcache restore not natively obtained) | R0021 §D |
| R05 | none | unchanged | unchanged | — |
| R06 | none (worker bytes regenerated by R0027 transform only) | spectral transform present in worker | unchanged | — |
| R10 | R0021 `dcc8206b`, `145b7ba9`; R000B `ea9f8300` | custody, retirement record, cloud receipt fences | resolved and independently verified (construction/retirement); accepted-vs-displayed remains implicit | R0021 §D/E/F |
| R11 | R000B | `pendingContext` | partly resolved (RF04 unchanged by decision) | R0021 owner exception |
| R12 | R0021 10.3; R000B | refused context returns; custody; cloud fences | partly resolved (healthy `dispose` asymmetry, D-F05) | unit tests |
| R15 | R000B | two hook methods | implemented but not fully verified | unit tests |
| R31 | R0027 (#69, PR #82, `77014952`) | inner FIFO 12,000 via digest-guarded transform | resolved and independently verified (retention); recomputation unchanged | 183/183 tests in my run incl. mutations; R0027 acceptance ledger |
| RF02 | R0021 ES21-01/02 | canvas after context; unwind | resolved and independently verified | `native-construction-ownership.test.mjs` pass; native construction cell PASS both engines |
| RF03 | R0027 | bound added | resolved and independently verified (bound); no heap/latency claim | ES27 tests |
| NF02 (rendering side) | R000B | no-model branch calls `reconcileCloudPublication(d)` + `withdrawWeatherEffects` (3491) | resolved and independently verified (source + unit + R000B certificate) | `native-weather-withdrawal.test.mjs` pass |
| NH02 | none | unchanged | still implicit or vulnerable (unverified) | source |
| RF04 | none (explicitly retained UNVERIFIED in R0021 owner decision) | `pendingContext` adds a cloud-receipt cancellation path only | still implicit or vulnerable (unverified) | R0021 §"Accepted history" |
| GDOPL projection "independent weather-to-cloud permission" | R000B | taken | demonstrated improvement (see §4) | diff + tests |
| GDOPL projection "bounded cache across both spectral layers" | R0027 | taken for inner layer; outer unchanged (already bounded) | demonstrated improvement (retention) | ES27-08 |

Proposed but not done: the original R01 risk note asked for native evidence of high-rate continuity; no such
record exists for the forecast-track case. The original RF04 next step (determine browser decode settlement)
was deliberately not pursued (owner decision in R0021).

---

## 3. Findings (documentary only)

| ID | Title | Machines | Evidence class | Severity / materiality |
|---|---|---|---|---|
| D-F01 | Interpolated preview-lane forecast weather re-keys the refined sky every simulated second; refined frames are never accepted once one worker render exceeds 1000/rate ms, and the stall is not reported as `rate-throughput` | NEW-D-01, R01, R10, R12 | demonstrated (source chain + effect-free probe with the real lifecycle module) | medium: optional astronomy only (preview remains, prayer unaffected); misleading status ("refining…") and wasted worker work |
| D-F02 | Native snapshot identity contains weather fields the worker job never consumes (`rh`, `cloud`, `code`, `wind`); any change withdraws the displayed refined frame and forces recomputation | R01, R10, R12 | demonstrated (source) | low–medium efficiency; correctness-neutral |
| D-F03 | Native render loop has no exception containment; a throw strands `_raf` until hide/show | N19, N17 | plausible risk (NH02 carried; no reachable throw shown) | medium if triggered (UI clock stops), trigger unknown |
| D-F04 | Preview in awaiting-input state runs `update()→clear()` (with cloud reconciliation and Moon detail clear) every animation frame for the page lifetime | R12, NEW-D-03 | demonstrated (source trace) | low (bare/manual-setup modes) |
| D-F05 | Preview healthy `dispose()` does not release its registry slot; refined owner does | R12 | demonstrated (source); no shipped caller | low (latent API asymmetry) |
| D-F06 | Generated app has no star-scintillation producer; DESIGN.md and the debugMotion star telemetry describe the replaced CSS implementation | N14, NEW-D-05 | demonstrated (source + docs) | medium for documentation/evidence truthfulness (gate I/M0 wording); visual impact unobserved here |
| D-F07 | Retained regression instruments fail at baseline (`r0021-reveal`, `r0022-baseline-balance`, `r0022-lunar-consumers`) | N14, NEW-D-04 | demonstrated (ran) | medium for qualification evidence (continuation of EF01) |
| D-F08 | `reconcileClouds()` used as a capture step by renderer owners has effects (withdrawal, header repaint) | R15, NEW-D-02 | demonstrated (source) | low; ownership clarity |
| D-F09 | Per-compose allocations and PNG mask encode at up to 20 Hz while clouds move | R10, R11 | demonstrated (source); no measurement | optimisation opportunity only |
| D-F10 | Two lunar-light producers in the generated app can diverge under `simMoon*` diagnostics | NEW-D-04 | speculative | low (diagnostic scenes) |
| D-F11 | RF04 mask decode still has no wall-clock bound | R11 | plausible risk (retained UNVERIFIED by owner decision) | low |

### D-F01 — trace
1. `render()` → `syncWeather()` (`src/native/index.html:3485`); with a forecast track and `ADVANCING||_clockPreview`, `weather=wxAt(simNow())` builds a new object with linearly interpolated `rh`, `wind`, `cloud`, `vis` (1556-1570, 1580). `render()` runs once per simulated second (3876-3877).
2. `selectedWeather` returns that record unchanged in preview lanes (1380); `capture()` copies `temp, rh, vis, cloud, code, wind` into the snapshot (`real-sky/native-host-hooks.js:42`).
3. `nativeIdentity` stringifies the weather object (`real-sky/native-contract.mjs:8`). Any change → `observe` sets reason `'new accepted native scene'` → `invalidate` (epoch++) → host `clear()` (`native-lifecycle.mjs:54,63`; `native-host.mjs:83-103`).
4. A worker result is accepted only for the current epoch and identity (`native-lifecycle.mjs:20,70`). The `rate-throughput` availability is set only when epoch AND identity match (24); identity mismatches are silently rejected/superseded, so `status.availability` stays `pending` and the badge shows "Sky preview · refining…" / "Real sky updating…" (`native-host.mjs:82`).
5. Probe `probes/D/forecast-identity-probe.mjs` (real `NativeSkyLifecycle`, fake clock, weather refreshed per simulated second, 20 s wall, request every 500 ms). Results: worker 300 ms → accepted at rate 1 and 2, 0 at rate 10; worker 800 ms → 0 at rate 2 and 10; worker 1200 ms → 0 at rates 1, 2, 10. Constant weather: accepted at every rate. `rate-throughput` was never reported in any lerp run. The probe models cadence; worker durations are parameters, not measurements (R0027 run2 recorded 790–999 ms worker renders in its environment).
- **Not covered by repository evidence:** R0021/R0027 native runs used `simWx` or an in-page current-only record, which bypass `syncWeather`.
- **Open questions:** should preview-lane weather be quantised for the sky identity, or should the identity carry only consumed fields (D-F02)? Either is a product decision; neither is proposed as a fix here.

### D-F02 — trace
`nativeJob` reads `w.vis` (aerosol), `w.temp` (temperature), `w.src` (label) (`native-contract.mjs:11-17`); `rh`, `cloud`, `code`, `wind` appear only in the identity (8). Live weather adoption (`fetchWeather`, `src/native/index.html:1469`) therefore withdraws a current refined frame and its preview even if aerosol and temperature are unchanged. Clouds are fenced separately by the cloud receipt (NEW-D-02), so the identity is not needed for cloud truth.

### D-F03 — trace
`loop` (`src/native/index.html:3869-3889`): calls `maintainPrayerDay`, `render`, `paintClouds`, `tieRainToClouds`, `updateMotionDbg`, `SalahSkyPreview.present` before `_raf=requestAnimationFrame(loop)` at 3888. `applyTheme` rethrows (3336). `start()` guards on `!_raf` (3890), so a stranded non-null id blocks restart until `stop()` (3891). Refined host contrasts at `real-sky/native-host.mjs:253`.

### D-F04 — trace
Bare mode: `boot` starts the preview when coordinates are missing (`src/native/index.html:3791`) and then returns at 3811 without starting the render loop. The preview's own `tick` (`native-preview-host.mjs:167`) calls `present`, which calls `update` whenever `!value` (166); `update` sees `!s.sceneIdentity` and calls `clear()` (127), which runs `host.reconcileClouds()`, `solarPublication.cancel()`, `SalahMoonDetail?.clear()`, `retireFirstPaint()` and class/style writes (47) — every frame.

### D-F05 — trace
`native-preview-host.mjs:186` `dispose(){disposed=true;solarPublication.dispose();retireFirstPaint();catalogue=null;cancelAnimationFrame(raf);canvas.remove();…}` does not execute `owned` (the slot release at 187 is only reached via the constructor `catch`, 190). Refined `dispose` runs `release()` (`native-host.mjs:263-264`).

### D-F06 — trace
Generated stub clears `.stars/.starglints/.milkyway` (`tools/build_native.py:61`) and CSS hides them (84). `nativeJob` sets `scintillation:{strength:0}` (`native-contract.mjs:~20`); `docs/real-sky/QUALIFICATION.md:130-132` keeps that setting. `DESIGN.md:440-449, 458, 466` still describe CSS twinkle and star Δ telemetry. `_starSampleNow`/`starAnim` (`src/native/index.html:3631, 3637`) sample `.stars circle`, empty in the generated app. Visual effect not observed in this lane.

### D-F07 — results I ran
`node tests/r0021-reveal.cjs` exit 1 (FAIL "moon PBR shader and embedded payloads retain exact accepted bytes"); `node tests/r0022-baseline-balance.cjs` exit 1 (FAIL "protected phase-gain guard rejects a changed .08 crescent curve"); `node tests/r0022-lunar-consumers.cjs` exit 1 (FAIL "ordinary render refreshes star appearance while held projection stays fixed :: held projector retained previous moon wash" — the generated stub is a no-op). R0021.md:184 records the same exits before and after its change.

### D-F08 — trace
`reconcileCloudPublication` may call `withdrawCloudState`, which zeroes coverage, clears the cloud canvas, writes effect CSS and repaints the header (`src/native/index.html:2730-2747`). It is invoked inside `NativeForegroundCapture.capture` (`native-composition.mjs:132`), preview/refined `clear` and `compose`. This is correct for truth, but the renderer owners therefore hold a write path into the weather/header owner.

### D-F09 — trace
`native-host.mjs:181` (new framebuffer), 193 (`new ImageData`), `native-composition.mjs:74` (256-entry inverse table per call), 127-128 (`putImageData` + `toDataURL` per changed cloud alpha), 154-156 (two readbacks), compose attempt cadence 50 ms (`native-host.mjs:253`). `sameNativePresentation` skips only when cloud and Moon bytes are identical, which moving clouds rarely are. No performance claim.

---

## 4. GDOPL inputs (Gradient Descent Over the Project Lagrangian)

Schematic only. `q` = current configuration at `363c3e53`. No weights, gradients, optima or convergence.

**Hard feasibility `F_hard` relevant here:** optional astronomy never blocks prayer; truthful weather provenance (no unsupported cloud/precip); accepted state ≠ displayed state; instance-owned disposal; canonical source (generated files via `tools/build_native.py`, copied core untouched except digest-guarded transforms); truthful evidence claims; AGENTS physics/visual contracts (opaque Moon, live motion, no slideshow).

**Modelled constraints `g_j(q) ≤ 0`:** `g1` refined frame age ≤ 30 s accepted UTC; `g2` at most one pending decode and two decoded masks per instance; `g3` spectral fit retention ≤ 12,000; `g4` no orphan canvas/worker after failed construction; `g5` cloud pixels only under a current receipt.

**Loss terms `f_T(q)` (qualitative):** wasted worker renders; UI-thread synchronous preview work; status truthfulness gap; redundant invalidations; documentation drift.

| # | Interaction | Current `q` | Constraints | Neighbour `q' = apply(q, η)` | Anticipated benefit | Regression cost | Evidence | Class |
|---|---|---|---|---|---|---|---|---|
| G1 | Preview-lane forecast lerp × sky identity (D-F01) | identity includes full interpolated weather | g1, truthful provenance | η1: identity uses only job-consumed fields; η2: quantise preview weather for the sky snapshot; η3: report a distinct `identity-churn` availability | refined sky can be accepted at moderate rates; truthful badge | η2 could lag weather visuals; η1 must keep every physics input | probe + source; no native run | plausible improvement requiring verification |
| G2 | Live weather refresh × refined frame (D-F02) | any weather field change withdraws refined + preview | g1, g5 | η1 above | fewer withdrawals/recomputes | must prove clouds remain fenced by the receipt only | source | plausible improvement requiring verification |
| G3 | Weather expiry × clouds without timetable (NF02) | receipt withdrawal in no-model branch | g5 | — (taken) | stale clouds withdrawn independent of prayer | none observed | before/after diff + `native-weather-withdrawal.test.mjs` + R000B certificate | demonstrated improvement |
| G4 | Failed refined/preview construction × DOM (RF02) | custody + unwind | g4 | — (taken) | no orphans | none in pixel trace (R0021 digest identical) | before/after diff + tests + native census | demonstrated improvement |
| G5 | Spectral fit retention (RF03) | inner FIFO 12,000 | g3 | η: uncached path for continuous twilight B–V | removes ~0-hit cache churn | must stay bit-identical; vendor provenance route | ES27-06 shows ~0 hit rate; no timing | demonstrated improvement (retention); recomputation: insufficient evidence |
| G6 | Native loop exceptions (NH02) | no containment | prayer UI liveness | η: reschedule-before-work or try/finally | loop survives a fault | could mask defects; needs a reachable trigger first | source only | insufficient evidence |
| G7 | Mask decode settlement (RF04) | no deadline | g2 | η: wall-clock cancellation | liveness under a stalled decode | owner decided against | none native | retain (owner decision) |
| G8 | Page lifecycle across owners | refined suspended; preview/loop by visibility | instance-owned disposal | η: preview participates in suspend/resume | consistent lifecycle; less background work | adds state; bfcache untestable headless | R0021 records no persisted restore | insufficient evidence |
| G9 | Overlapping state added by RLGWOs | cloud receipt + weather decision cache + effects receipt + R01 identity all describe weather currency | conflicting authority (hard) | η: document one map of which receipt governs which consumer | review clarity | doc-only | source | plausible improvement requiring verification |
| G10 | Accepted vs displayed refined frame | `frame/job` vs `paintedFrame/paintedJob` closures | separation hard constraint | — | — | — | R0021 tests fence both | retain |

Original projection comparison: the two GDOPL_FINAL directions that concern this lane (independent weather-to-cloud
permission; bounded spectral cache) were taken (R000B, R0027) with before/after source and test evidence. The
"whole-widget CPU/memory budget" caution (GDOPL_FINAL ~103) remains open; D-F01/D-F09 add source-level reasons to
measure it, not measurements.

---

## 5. Coverage statement

- **Read fully:** `real-sky/native-host.mjs`, `native-lifecycle.mjs`, `native-contract.mjs`, `native-worker-policy.mjs`, `native-assets.mjs`, `native-first-paint.mjs`, `native-engine.mjs`, `native-preview-host.mjs`, `native-host-hooks.js`, `core/src/latest-render-queue.mjs`, `core/src/reference-worker-client.mjs`, `tools/build_native.py`, `tools/native_core_spectral_cache.py`; `src/native/index.html` 990-1050, 1370-1430, 1540-1600, 1700-1760, 2100-2270, 2640-2920, 3004-3045, 3222-3530, 3539-3900.
- **Sampled:** `native-composition.mjs` (1-33, 70-171), `core/src/spectral.mjs` (1-45), `core/src/sky-background.mjs` (10-96), `native-preview.mjs` (343-355 + cache greps), generated worker tail, `docs/state-contracts/R0021.md` (1-250, 860-1000), `R0027.md` (420-490), DESIGN.md star/motion sections, QUALIFICATION.md 125-136, original catalogue entries for N13-N19, R01-R18, R31-R36, RF02/RF03/NF02/NH02/RF04, GDOPL_* greps.
- **Not examined:** `atmosphere()` body beyond the lunar lines; `native-star-preview.mjs`, `native-cloud-transfer.mjs`, `native-encoding.mjs`, remaining `core/src/*` files (unchanged per diff); `R000B*.md` beyond headings; lane-E Moon sources; browser behaviour (no browser launched).
- **Tests run (no tree writes; `git status` clean afterwards):** `node --test` on 14 files (`native-construction-ownership`, `native-weather-withdrawal`, `native-lifecycle`, `native-contract`, `native-assets`, `native-preview-host`, `native-host-composition`, `spectral-fit-cache-state/-mutations/-generated`, `cp9-page-lifecycle`, `native-cloud-unresolved`, `cp9-worker-policy` under `tests/real-sky/`, plus `tests/r000b-sky-withdrawal.test.mjs`): 183 pass, 0 fail. Direct scripts: `r0021-reveal` exit 1, `r0022-baseline-balance` exit 1, `r0022-lunar-consumers` exit 1, `r0025-context`/`-continuity`/`-lifecycle` exit 0, `r001d-lifecycle` exit 0. `r0025-mutations.cjs` not run (writes files).
- **Probe:** `probes/D/forecast-identity-probe.mjs` (imports the baseline lifecycle and contract modules; no network, DOM or writes). Results are in D-F01.
