> **Lane working paper.** This is supporting detail produced by one census lane of the post-RLGWO audit at baseline `363c3e53`. It is superseded by [IMPLICIT_STATES.md](../../../../IMPLICIT_STATES.md), [REPORT.md](../REPORT.md), [CROSSWALK.md](../CROSSWALK.md) and [FINDINGS.md](../FINDINGS.md) wherever they differ; the integrator's corrections are listed in REPORT.md. Probe paths `probes/<lane>/` refer to [../probes/](../probes/README.md).

# Lane E — Moon pipeline (post-RLGWO implicit state-machine audit)

Baseline `363c3e53` (main). Historical reference `f71fef6c`. Read-only; nothing in the repository was changed.
Line numbers are at the baseline. Authored sources come first. Generated counterparts: `moon/moon-host.js`
(the host wrapper: HOST_UNITS + `moon-native.mjs` + head owner + refinement tail), `moon/moon-worker.js`, and the
inline copies in root `index.html` (`<script id="moon-initial-code">` at L3152, the native script at L4198,
`<script id="moon-refinement-code">` at L7690) and `offline.html` (refinement call at L8174).

**What changed f71fef6c → 363c3e53 in this lane.** Only R0021 (#33) touched the Moon sources: commits `33e323c1`,
`dcc8206b`, `de68e848` and `145b7ba9`, merged via `65f7c75a`. The changes are:
- `moon/src/moon-native.mjs`: +31/−6 lines.
- New `moon/src/moon-install-guard.mjs`.
- `tools/build_moon.py`: one new HOST_UNITS entry.
- New `moon/tests/native-instance-retirement.test.cjs`.
- `src/native/index.html`: one Moon-adjacent line (`paintLunarOptic(c,key,"0")` in `paintCelestialWithoutTimetable`, from R000B `ea9f8300`).

`moon-worker`, `moon-pool`, `moon-engine`, `moon-quality`, `moon-detail`, `moon-initial*`, `moon-first-paint`,
`moon-precision`, `moon-calendar` and `moon_kernel.c` are byte-unchanged (`git diff --stat`). R0022 (#34) and
R001D (#29) closed before `f71fef6c`, so their effects are already in the historical baseline.

---

## 1. Machine census

### N11 — Legacy lunar texture/canvas fallback (dormant generated owner)
- **Scope/decision:** decodes the legacy albedo/normal maps and decides whether a legacy PBR or calendar-fallback raster is written to `.mphoto`.
- **Sources:**
  - `src/native/index.html` L1892–1907 (`loadMoonMaps`, `fail`, `grab`, `done`).
  - L1911–1951 (`renderMoonCalendarFallback`).
  - L1953–1956 (`renderMoonPBR` delegates when `window.SalahMoonRuntime` is truthy).
  - L1957+ (`renderMoonLegacyPBR`).
  - Generated: `index.html` inside the native script.
- **State:** `_mAlb/_mNrm` (null/decoded); `_pbrReady`; `_pbrPending` (newest frac/waxing); `_pbrFailed`; `_moonFallbackReady`; cached last frac/wax/up/albedo.
- **Transitions:**

  | Event | Guard | Effect |
  |---|---|---|
  | image onload | `!window.SalahMoonRuntime` *at callback time* | store decoded data → `done()` → `_pbrReady` |
  | image onerror / decode exception | `!SalahMoonRuntime` | `_pbrFailed=true` → calendar fallback raster |
  | `renderMoonPBR` | runtime present | `runtime.request()` (modern owner) |
  | `renderMoonPBR` | runtime absent | legacy PBR; pending if not ready |
- **Invariant:** legacy decode never counts as modern readiness (L2233–2238 comment, `moon-ready` requires `runtime.surface()`).
- **Observed facts:**
  - The callbacks test the *live* slot, so when the runtime slot is empty (wrapper construction failure clears it, `moon-native.mjs` L298) the legacy path becomes active: it decodes the maps and writes `.mphoto` every minute.
  - Its output is never revealed, because `updateSkySurface` (L2238) requires the runtime.
  - `_pbrFailed` is the only "surface failed" input to lunar-light eligibility (NEW-E-05).
- **Hypotheses:** in the runtime-absent fault path, the legacy decode and render cost is pure waste.
- **Unknowns:** the native cost of that wasted legacy work.
- **Enforcement:** doc = comments; impl = implicit; verif = unit (VM harness `tests/r0022-lunar-consumers.cjs` exercises this legacy path because the harness loads only the native inline script, `tests/r001d-harness.cjs` L55–103).

### N12 — Native lunar geometry production and consumption receipts
- **Sources:**
  - `src/native/index.html` L2026–2039 (`moonGeometryIdentity`, `moonGeometryObservation`).
  - L2061–2090 (`nativeLunarSnapshot`, `renderMoon`).
  - L3326–3338 (`_lastMoonPaint`, `applyTheme`).
  - L4167–4184 (`SalahMoonHost.capture/publish/fallback`).
  - L3494 (minute cadence in `render`).
- **State:** `moonSky` plus its production stamp `_epochMin/_min/_context` (stamped only when finite); `lastMoonMin`; `_moonStaleWarned`; `_lastMoonPaint{status: completed|unavailable|failed, stage, fresh, observation}`.
- **Transitions:**
  - `renderMoon` writes the paired moon/mask transforms and stamps on success.
  - An observation is `fresh` only if epochMinute, minute and context all match.
  - `applyTheme` seals its receipt at the attempt, including on failure.
  - `capture()` is the sole native identity producer for the runtime.
- **Unchanged since f71fef6c.**
- **Observed facts:** `render()` calls `renderMoon()` (L3494) **before** prayer publication (L3499–3516). `renderMoon` → `renderMoonPBR` → `SalahMoonRuntime.request()` is not isolated (see EF-E01).
- **Hypotheses:** none beyond EF-E01.
- **Unknowns:** native pixel/mask alignment, which is not re-verified here.
- **Enforcement:** doc = comments + R001D certificate (#29); impl = partly explicit; verif = unit (`tests/r0022-lunar-consumers.cjs`, run: 24 pass / 2 fail, both failures in star-wash synthetic cases).

### NEW-E-01 — Moon wrapper admission, construction unwind and replay refusal (R0021)
- **Scope:** decides whether a host wrapper evaluation may construct a runtime, and what remains after construction throws.
- **Sources:**
  - `moon/src/moon-install-guard.mjs` L6 (first HOST_UNIT, `tools/build_moon.py` L12).
  - `moon/src/moon-native.mjs` L8 (dispose predecessor), L245 (detail handle), L246–300 (try/registration/catch).
  - Generated: `index.html` L3226 (refusal string), `moon/moon-host.js`.
- **States:** `no runtime` → `constructing` → `registered (live)` → `disposed`; `constructing` → `construction-failed → cleaned (slot null, status disposed)`; `replay-refused` (the throw happens before any unit runs).
- **Transitions:**

  | Event | Guard | Effect |
  |---|---|---|
  | wrapper eval | slot empty or `.disposed` | construct; L8 `dispose()` is a no-op on an already disposed runtime |
  | wrapper eval | live runtime (`!disposed`, including pre-R0021 runtimes without the getter) | throw at L6; no global is replaced |
  | throw inside try (L247–291) | — | clear the interval and rAF, remove the listener, close the worker, release the detail only if held (L297), clear the slot only if it still holds `registered` (L298), rethrow |
  | `startMoonDetail()` throw (L245, outside try) | — | nothing has been acquired yet; propagates |
- **Invariants:** at most one live runtime and detail pair; an old dispose never touches a successor (captured `detail`, L284 conditional slot clear).
- **Observed facts:**
  - The rethrow aborts the rest of the host wrapper. `window.SalahMoonHead` and `SalahPrepareFirstPaint?.()` (`build_moon.py` L120–128) are skipped (EF-E07).
  - The refinement tail `window.SalahMoonRuntime.installWorkerSource(...)` then throws a TypeError on the null slot (EF-E04).
- **Hypotheses:** none.
- **Unknowns:** a real-browser natural construction failure; only an injected one is recorded (R0021 contract, sections F/G).
- **Enforcement:**
  - doc: state contract `docs/state-contracts/R0021.md` (ES21-04/05/06/07).
  - impl: explicit and enforced.
  - verif: unit (`moon/tests/native-instance-retirement.test.cjs`, 12 cases) + mutation (m9, m20 killed per contract) + native (cells `moon-replay` and `moon-construction`, Chromium and Firefox, per contract) + delta review G.

### R19 — Lunar host accepted / pending / waiting-preview / presentation transaction
- **Sources:** `moon/src/moon-native.mjs` L13–16 (state), L18–48 (`capture`, `key`, `scope`, `phaseDrift`, `sameScope`, `matches`), L49–54 (`fallback`, `clear`), L75–91 (`adopt`, `presentation`), L124–144 (`poll`), L193–227 (worker message admission), L261–283 (`request`, `surface`, `state`, `detailEnabled`); `moon/src/moon-precision.mjs` L1–27.
- **Independent dimensions:**
  - `accepted` (null | initial | preview | refined record with epoch/scope/scene);
  - `pending` (null | {id, key, scope, epoch, scene});
  - `waitingPreview` (null | message+record);
  - `epoch`/`serial` counters;
  - `clock` (null | anchor);
  - `profileMode` (calendar | reference); `referenceScene`;
  - texture bytes and `textureUp`;
  - `status.status` (loading | waiting-native | paused | ready-for-scene | rendering | refining | ready | unavailable | disposed | waiting-refinement-source);
  - DOM: `.mphoto` href, `.c.moon-ready`, `.moon-mask-disc.mask-on`, detail canvas visibility.
- **Transitions:**

  | Event | Guard | Effect |
  |---|---|---|
  | scope, clock or pause change | — | `clear`: epoch++, serial++, cancel, `fallback` |
  | pending exceeds the .0416 px budget | — | cancel and re-issue |
  | worker preview | current id/scope/scene | stored as `waitingPreview`; adopted only by a read-time `presentation()` |
  | result | `quality.status==='empirical-adaptive'` | adopt |
  | stale or duplicate id | — | `rejected++` |
  | `failed` | accepted still `matches` | retain it; otherwise fallback |
- **Accepted vs displayed:**
  - `accepted` is host authority.
  - Displayed state is `.mphoto` (published by `syncTexture` → `SalahMoonHost.publish`) plus `moon-ready`, which is toggled only when `updateSkySurface` runs. `paint()` calls it each `render()` (≈1 Hz, L3275), so the reveal can lag a time-based loss of currentness by ≤ one render tick.
  - A stale `.mphoto` href persists after `fallback` but is hidden by the class.
- **Observed facts:**
  - The getters `surface()`, `state` and `detailEnabled` call `presentation()`, which can **adopt a waiting preview and publish** (L89, L275, L277, L283). `qaState().moonTruth` invokes them (`src/native/index.html` L3608). See EF-E06.
  - Covered by tests: `moon/tests/host.test.cjs` L94 ("surface may adopt a deferred preview…"), L284–289 (A→B→A, profile, DPR, seek, hide).
- **Hypotheses:** the reveal lag is ≤1 s and has no visual consequence (not measured).
- **Unknowns:** native timing.
- **Enforcement:** doc = comments; impl = partly explicit (identity fences explicit; read-time side effects implicit); verif = unit (host.test.cjs, 50+ cases; ran 133/133 for `moon/tests`).

### R20 — Runtime installation, worker source, bounded retry and deadlines
- **Sources:**
  - `moon-native.mjs` L55–70 (`closeWorker`, `failed`), L182–232 (`start`), L251–260 (`installWorkerSource`), L282 (`retry`), L284 (`dispose`), L291 (deferred double-rAF start).
  - `tools/build_moon.py` L129–131, L138 (refinement tail).
- **State:**
  - `MOON_WORKER_SOURCE` (null | pinned string); `startFrame`; `worker`/`url`; `ready`; `deadline` (120 s boot / 240 s render); `lastError`;
  - `retryCount` (0..3, never reset); `status.errors` (≤8); `disposed`.
- **Transitions:**

  | Event | Guard | Effect |
  |---|---|---|
  | `installWorkerSource(src)` | not disposed; length and SHA pin match | pin the source; if no worker and no startFrame, start via double rAF |
  | `installWorkerSource(src)` | identity mismatch | throws |
  | `installWorkerSource(src)` | same source | idempotent `true` |
  | `start` | — | new Blob URL + Worker; callbacks gated on `worker===w` |
  | `failed` | — | serial++, revoke the initial head, close the worker |
  | `retry()` | not disposed, no worker, source present, `retryCount<3` | `start` |
- **Observed facts:**
  - **No product code calls `retry()`.** Repo-wide grep of `real-sky/`, `src/native/` and `moon/src` finds no caller; only tests and QA drivers call it. Every worker failure is terminal for the page lifetime (EF-E02).
  - The refinement tail call is unguarded (EF-E04).
  - Boot deadline 120 s (L230); render deadline 240 s (L143) is not extended by a preview.
- **Unknowns:** worker-failure incidence in the field.
- **Enforcement:** doc = comments + R0021 contract (ES21-06/11); impl = explicit for the bounds, implicit for the absent recovery owner; verif = unit (host.test.cjs L164, L264, L290, L296–297; native-instance-retirement ES21-06) + native (R0021 `moon-asset-failure` cell, retries driven by the QA driver).

### R21 — One-shot initial-head eligibility and irreversible retirement
- **Sources:** `moon-native.mjs` L15, L50 (`revokeInitialHead`), L92–107 (`takeInitialHead`), L108–123 (`initialPresentation`), L279 (`finishInitialDocument`).
- **State:** `initialHeadEligible` (true → false, irreversible); `SalahFirstPaint.moon.result` nulled on revoke; `status.firstInitial`; `status.initialRejected`; `status.initialError` (sticky).
- **Transitions:** `takeInitialHead` always revokes first, then admits only generation 0, rate 1, unpaused, calendar profile, the same scope, time continuity within 1000 ms, the receiver SHA and an equal profile. Any `clear` except the initial-document invalidation revokes.
- **Observed facts:**
  - Unchanged since f71fef6c.
  - **New:** the `catch` at L122 sets `status.initialError`, which L109 then treats as a permanent disable of the whole initial V5 tier, not just the head (EF-E10).
- **Enforcement:** doc = comments; impl = partly explicit; verif = unit (host.test.cjs L114, L125, L75).

### R22 — Offline chunk DOM/script transport lease
- **Sources:** `moon-native.mjs` L145–181 (`offlineTransport`); generated chunks `moon/file-data/*.js` (`build_moon.py` L109–116).
- **State:** `at`, `seen`, `chunkScript`, `nextTimer`, the DOMContentLoaded listener, `stopOffline`.
- **Invariants:**
  - A chunk is accepted only for the current worker, the exact owning script element and `document.currentScript`.
  - Ordering is enforced by index, name and last flag.
  - Inert embedded nodes are retained so a retry can replay them.
- **Unchanged.** Unit-covered (host.test.cjs L35, L44, L61, L264).
- **Enforcement:** doc = comments; impl = partly explicit; verif = unit.

### R23 — Top worker boot, newest-job pump and cancellation
- **Sources:** `moon/src/moon-worker.mjs` L4–17 (`read`, `boot`), L18–36 (`pump`), L62–75 (message handler, `unhandledrejection`).
- **State:** `enginePromise`, `latest`, `running`, `serial`, `offlineParts`.
- **Observed facts:**
  - `read()` fetches with `cache:'force-cache'` (L6) — see NEW-E-03.
  - Any unhandled rejection in the worker realm is reported as `boot-error` (L75), which the host treats as `failed` even after `ready` (`moon-native.mjs` L197).
  - The no-lost-wakeup `finally` holds (L35).
- **Unchanged.**
- **Enforcement:** doc = comments; impl = implicit; verif = unit (`tests/real-sky/moon-worker-fixture.test.mjs`, passed).

### R24 — Shard RPC bridge promises and sticky failure
- **Sources:** `moon/src/moon-pool.mjs` L6–27.
- **Behaviour:**
  - `failure` is sticky for any non-AbortError (L18–20) or transport error.
  - There is no per-RPC timeout; liveness is delegated to the host's 120/240 s deadlines.
- **Unchanged.** Unit tests include "an idle row-worker failure is terminal…" (`moon/tests/pool.test.cjs`).
- **Observed facts:** sticky shard failure → pool rejects → top worker posts `error` → host `failed` → worker closed → no product retry (EF-E02).
- **Enforcement:** doc = comments; impl = partly explicit; verif = unit.

### R25 — Pool row ownership, sparse reuse and join barrier
- **Sources:** `moon-pool.mjs` L28–98.
- **Observed facts:**
  - The `allSettled` barrier (L59) guarantees every shard has replied before the next top-level job, so a new `shard-render` cannot hit the engine's `active` guard (`moon-engine.mjs` L76). Traced; no defect.
  - `this.material` (≈N²·3 Float32, N=540 ≈ 3.5 MB) is retained per pool for `nativeCalendarResult` (`moon-calendar.mjs` L34).
- **Unchanged.**
- **Enforcement:** doc = comments; impl = partly explicit; verif = unit (`pool.test.cjs`).

### R26 — Engine exclusive execution, asset admission and caches
- **Sources:** `moon/src/moon-engine.mjs` L19–52 (`admitScene`, `decodeAsset`), L63–131.
- **Unchanged.** The original qualification SD-F02 still applies: a native frame-allocation refusal can leave a stale `cameraKey`. It is unreachable in product because any engine error is terminal for the worker.
- **Enforcement:** doc = comments; impl = partly explicit; verif = unit (`kernel.test.cjs`, `quality.test.cjs`).

### R27 — Cooperative MessageChannel yield
- **Sources:** `moon-engine.mjs` L57–62.
- **Unchanged.** One module channel with a FIFO queue; worker termination abandons continuations.
- **Enforcement:** doc = comments; impl = implicit; verif = indirect only.

### R28 — Adaptive refinement and final quality admission
- **Sources:** `moon/src/moon-quality.mjs` L9–45; host gate at `moon-native.mjs` L222.
- **Unchanged.** `limit-reached` is labelled, and the host treats it as `failed` (terminal, EF-E02).
- **Enforcement:** doc = comments; impl = explicit; verif = unit (`quality.test.cjs`, 31 s case passed).

### R29 — Detail adoption, projection cache and DOM visibility owner
- **Sources:** `moon/src/moon-detail.mjs` L43–141 (byte-identical, pinned); the R0021 handle wrapper at `moon-native.mjs` L245.
- **Changed by R0021:**
  - The runtime now owns a captured handle: idempotent `dispose`; `adopt` refused after retirement; `available` false after retirement.
  - The inner `adopt` still has no disposed guard, but the handle masks it.
- **Caches:** one `projected` entry (key + table identity), one `prepared` per frame, `last` frame/key/cloud.
- **Observed facts:** `compose` can throw (`Moon detail viewport budget`, `Unsupported lunar cloud filter`, L62, L87) into the sky compositor (sky lane owns those callers).
- **Enforcement:** doc = comments + R0021 contract (10.11); impl = partly explicit; verif = unit (`tests/real-sky/moon-projection-cache.test.mjs`, passed; native-instance-retirement ES21-07).

### R30 — Admitted initial receiver and canonical render closure
- **Sources:** `moon/src/moon-initial.mjs` L9–69; `moon-initial-compact.mjs`; boot at `build_moon.py` L118 (`SalahMoonInitialError`).
- **Unchanged.** On decode failure `SalahMoonInitial` is undefined. `initialPresentation` refuses (L109), and the head compose throws `Head Moon qualified initial unavailable` (`moon-first-paint.mjs` L29), so the whole first paint records an error (`real-sky/native-first-paint.mjs` L50).
- **Enforcement:** doc = comments; impl = partly explicit; verif = unit (`initial.test.cjs`, `compact-codec.test.cjs`).

### R37 — C/WASM retained kernel state, frame arena and source witness
- **Sources:** `moon/src/moon_kernel.c` L19–28 (`space`, 512 MiB ceiling), L77–96, L198–261 (`frame_mark`, `begin_scene`), L264–318.
- **Unchanged.** There are four shard instances per Moon worker, each with its own ≤512 MiB heap ceiling and a high-water allocation that never shrinks.
- **Enforcement:** doc = comments; impl = implicit; verif = unit (`kernel.test.cjs`), with no native memory census.

### NEW-E-02 — Native Moon reveal gate (`moon-ready` / `mask-on`)
- **Sources:** `src/native/index.html` L2225–2241 (`beginSkyScene`, `updateSkySurface`), CSS L178 and L185.
- **Decision:** `.moon` is visible iff `SalahMoonRuntime.surface()` is non-null, `.mphoto` has an href and `_skySceneKey!==null`. The mask additionally requires `_skyMoonPresence>0`.
- **States:** hidden (no runtime / no current presentation / no scene) ↔ revealed.
- **Observed facts:**
  - With no runtime registered there is **no Moon disc on any tree**: legacy maps decode but are never revealed. This is recorded natively in the R0021 contract, section F, "Moon construction failure: visible consequence" (EF-E03).
  - In normal operation, the AGENTS gate D "never an empty moon slot" depends on R19/R21 always producing an initial V5 presentation.
- **Enforcement:** doc = comments ("Decoded legacy maps are never terrain readiness"); impl = explicit; verif = native (R0021 `moon-construction` cell, both engines).

### NEW-E-03 — Worker asset HTTP acquisition and browser-cache admission
- **Sources:** `moon/src/moon-worker.mjs` L5–10 (`read`); manifest sizes from `MOON_ASSET_MANIFEST`.
- **Decision:** whether a cached HTTP response is used for `dem.bin.gz` / `colour.bin.gz`.
- **States:** fetched-ok | HTTP error (`Moon asset HTTP <status>`) | size/truncation error.
- **Observed facts:**
  - `cache:'force-cache'` returns any cached response, including a heuristically cached error.
  - R0021 contract G item 4 records Firefox 153 serving a cached 404 to every later retry with zero server requests (cell b21), and a final state of `unavailable` on both trees.
- **Hypotheses:** a page reload may also not recover while the cached error persists, because force-cache does not revalidate. Not tested.
- **Unknowns:** Chromium heuristic-caching behaviour for 404 under force-cache; production server `Cache-Control` on errors.
- **Enforcement:** doc = R0021 contract note (routed, not fixed); impl = implicit; verif = native (b20/b21 Firefox).

### NEW-E-04 — Moon page-lifecycle withdrawal (visibility) and worker lifetime
- **Sources:** `moon-native.mjs` L239 (`visibility`), L248 (listener), L287 (`setInterval(poll,250)`), L129 (paused).
- **Transitions:**
  - hidden → `clear('document hidden')`: cancels the job, drops `accepted` (including a refined surface) and revokes the head.
  - visible → `clock=null; poll()`: re-adopts the initial V5 and re-issues a full adaptive render.
- **Observed facts:**
  - There is no `pagehide`/`pageshow`/`freeze` handler. The worker, its four nested shard workers and the 250 ms interval are never terminated by lifecycle events; termination comes only from `dispose` or document unload.
  - The poll runs at 4 Hz for the page lifetime, with a layout read per poll (`getBoundingClientRect`, L26) whenever geometry is requested.
- **Unknowns:** bfcache freeze/restore behaviour for the Moon worker. R0021 obtained a bfcache restore only in headed Chromium, and for the sky.
- **Enforcement:** doc = comments; impl = partly explicit; verif = unit (host.test.cjs L289 "hide return does not retain a predecessor").

### NEW-E-05 — Native physical lunar-light eligibility (R0022)
- **Sources:** `src/native/index.html` L2992–3003 (`nativeLunarPresentation`, `lunarPresentation(..., _pbrFailed)`), consumers at L3055–3177.
- **Decision:** moonlight, beam, glow, star wash, cloud light and lunar optics.
- **Guards:** `surfaceFailed` (from `_pbrFailed`) × `moonUp` × `darkness` × `phaseVis`.
- **Observed facts:**
  - In the generated app `_pbrFailed` can never become true while a runtime exists (`fail()` returns early, L1898). The `surface-unavailable` reason is therefore unreachable there.
  - Eligibility does not consult the modern surface's currentness (`runtime.surface()`) (EF-E05).
  - Tests exercise only the legacy, runtime-absent VM path.
- **Enforcement:** doc = R0022 certificate (#34, comment 6220885146) + comments; impl = explicit; verif = unit (`tests/r0022-lunar-consumers.cjs`).

---

## 2. Historical-to-current reconciliation

| Original | RLGWO / commits | Code change | Disposition | Evidence |
|---|---|---|---|---|
| **RF01** | R0021 #33; `dcc8206b`, `de68e848`, `145b7ba9` | Guard refuses replay over a live runtime (`moon-install-guard.mjs` L6). Detail captured lexically (`moon-native.mjs` L245). Dispose clears the slot only if held (L284). The leading `SalahMoonDetail?.dispose()` reaper was removed. | **resolved and independently verified** (by refusal policy, not safe replacement) | native-instance-retirement ES21-04/05 (re-run, pass); mutants m4/m9/m13/m14/m20 killed (contract); native `moon-replay` cells PASS candidate / FAIL control, both engines; delta review G. Projection direction "acquire into instance-owned record" was taken; "atomic replacement" was not (replay is unsupported by owner decision ES21-05). |
| N11 | none | none | still implicit or vulnerable (dormant, but now reachable in the runtime-absent fault path) | L1898/1899 live-slot check; NEW-E-02 |
| N12 | none since baseline (R001D, R0022 prior) | none | implemented but not fully verified | EF-E01 propagation probe |
| R19 | R0021 (handle only) | `fallback`/`adopt` use the captured `detail` | implemented but not fully verified | host.test.cjs; read-time side effects (EF-E06) still implicit |
| R20 | R0021 | try/catch unwind; `disposed` getter | partly resolved | Construction cleanup explicit. Retry has no product owner (EF-E02); unguarded refinement tail (EF-E04, routed G2, not done). |
| R21 | none | none | implemented but not fully verified | sticky `initialError` (EF-E10) |
| R22 | none | none | implemented but not fully verified | unit only; no native offline run here |
| R23 | none | none | still implicit or vulnerable | force-cache admission (NEW-E-03); `unhandledrejection` → boot-error after ready |
| R24 | none | none | implemented but not fully verified | sticky by design; recovery boundary is a new worker, which nothing triggers |
| R25 | none | none | implemented but not fully verified | barrier traced |
| R26 | none | none | implemented but not fully verified | SD-F02 qualification unchanged |
| R27 | none | none | still implicit or vulnerable (benign) | no focused test |
| R28 | none | none | resolved and independently verified (finite policy) | quality.test.cjs |
| R29 | R0021 | runtime-owned handle (idempotent dispose, retired-adopt refusal) | resolved and independently verified (lifetime); cache protocol implemented but not fully verified | ES21-07 tests; projection-cache test |
| R30 | none | none | implemented but not fully verified | initial-decode failure couples to the first paint (EF-E07) |
| R37 | none | none | implemented but not fully verified | no native memory census |

Original GDOPL direction (GDOPL_FINAL §"temporal ownership", L85) was taken for RF01. Its §"Cache admission" call
for a shared priority contract (prayer > first celestial > refinement, L103) was **not** implemented for the Moon:
EF-E01 shows the Moon still runs synchronously inside the prayer render, ahead of prayer publication.

---

## 3. Findings

### EF-E01 — An exception from the optional Moon runtime aborts prayer publication and halts the render loop
- **Machines:** N12, R19, R20; the native N19 loop.
- **Evidence class:** **demonstrated** (propagation). The trigger is **speculative**: no natural throw was found in `request()`/`poll()`.
- **Trace:**
  - `src/native/index.html` L3877: `loop()` calls `render()` with no try/catch.
  - L3494: `renderMoon()` runs before prayer DOM writes (L3499–3516).
  - → L2089 `renderMoonPBR` → L1954 `window.SalahMoonRuntime.request()` → `moon-native.mjs` L261–273 `poll`/`presentation`/`syncTexture`/`SalahMoonHost.publish`.
  - None of these is try-wrapped, except `initialPresentation` and `capture`.
  - A throw also skips L3888 `_raf=requestAnimationFrame(loop)`, so the loop stops.
- **Probe:** `probes/E/moon-throw-blocks-prayer.cjs` uses the existing read-only VM harness on root `index.html`. Control: `.cn`="Isha" and `.times` repopulated. With a stub runtime whose `request()` throws: `render()` throws, `.cn` stays "SENTINEL" and `.times` stays empty.
- **Severity:** high if triggered (hard constraint: optional astronomy must not block prayer). Materiality is conditional on a throw in `request()`.
- **Candidate throw sites (unproven):**
  - `ImageData` size mismatch in `syncTexture`.
  - A `detail.adopt` RangeError inside `presentation()` for a queued preview.
  - `worker.postMessage` at L133/L142 (not wrapped, unlike L53).
  - `canvas.toDataURL` under memory pressure.
- **Open question:** should the native host isolate optional Moon calls (try/catch or after-publication ordering)? This is an owner decision.

### EF-E02 — Bounded Moon retry has no product owner; every worker failure is terminal for the page lifetime
- **Machines:** R20, R23, R24, R28.
- **Evidence class:** **demonstrated** (code trace + grep).
  - `retry()` at `moon-native.mjs` L282 is called only from tests and drivers.
  - `failed()` (L59–70) closes the worker.
  - No lifecycle, visibility or timer path calls `start()`. `start` is reached only from L258 (source install) and L291 (first boot).
- **Terminal triggers:** asset HTTP error, 120 s boot deadline, 240 s render deadline, `limit-reached` quality (L222), result-contract mismatch, sticky shard error, worker `unhandledrejection`.
- **Effect:** the Moon remains at the initial V5 tier (or an adopted preview) until reload; status `unavailable`. The opaque disc survives only while the initial tier works (see EF-E10).
- **Severity:** medium. This is a quality degradation, not a contract violation, and it is silent to the user.
- **Unknowns:** failure incidence in the field.

### EF-E03 — No Moon disc after a Moon-wrapper construction failure (empty slot)
- **Machines:** NEW-E-01, NEW-E-02, N11.
- **Evidence class:** **demonstrated** natively for an injected failure (R0021 contract §F, cells `moon-construction`, Chromium and Firefox). Traced: `moon-native.mjs` L298 clears the slot, and `src/native/index.html` L2238 requires the runtime.
- **Effect:**
  - The forbidden "empty moon slot" outcome appears in this fault path.
  - The legacy maps still decode and the legacy PBR renders into a hidden `.mphoto` (wasted work).
  - Lunar-light consumers can stay active (EF-E05).
- **Severity:** medium (fault path only). It is routed as an owner decision (contract G1), and no RLGWO text requires a fallback owner.
- **Open question:** should the existing calendar fallback be admitted when no runtime is registered? This conflicts with "no legacy substitution".

### EF-E04 — Unguarded refinement-tail `installWorkerSource`
- **Machines:** R20, NEW-E-01.
- **Evidence class:** **demonstrated** (R0021 contract §F: a `TypeError … installWorkerSource` on the empty slot). The call is at `tools/build_moon.py` L130; generated `index.html` L7690, `offline.html` L8174, `moon/moon-host.js` L1045.
- **Also:** an identity mismatch throws (`moon-native.mjs` L253/L255) in the same uncaught tail.
- **Effect:** an isolated `<script>` error; prayer is unaffected (separate script after native boot). Disposed runtime → returns `false`; guard-refused replay → idempotent on the old runtime.
- **Severity:** low. Routed (G2), not repaired.

### EF-E05 — Lunar-light eligibility is not bound to modern surface availability
- **Machines:** NEW-E-05, N11, NEW-E-02.
- **Evidence class:** **plausible risk**.
- **Trace:**
  - `src/native/index.html` L3003 passes `_pbrFailed`.
  - L1898 makes `_pbrFailed` unreachable while a runtime exists.
  - In the runtime-absent path, the legacy maps succeed, so `_pbrFailed` stays false and moonlight stays eligible while `.moon` is hidden.
  - In normal operation, `awaiting-terrain` states (for example `initialError` with no worker yet, or after `fallback`) likewise keep sky tint, cloud moonlight and star wash on (L3069, L3141, L3176).
- **Mitigation:** `.mbeam`/`.mglow` sit inside the hidden `.moon` group (L531, L537).
- **Severity:** low–medium (truthfulness: "never faked light"). The `surface-unavailable` reason is dead code in the generated app.
- **Unknown:** whether the visible sky/cloud tint differs enough to matter (pixels not examined).

### EF-E06 — Lunar diagnostic and readiness getters mutate presentation state
- **Machines:** R19, N12 (R001D scope).
- **Evidence class:** **demonstrated** (code + existing test).
  - `state` (L283), `surface()` (L275) and `detailEnabled` (L277) call `presentation()`, which adopts `waitingPreview` (L89 → `adopt` → `detail.adopt`, `syncTexture` → `publish` → `toDataURL` + `updateSkySurface`).
  - `moon/tests/host.test.cjs` L94 asserts that `surface()` adoption.
  - `qaState().moonTruth` reads `runtime.surface()` and `runtime.state` (`src/native/index.html` L3608).
- **Effect:**
  - A QA read can advance displayed state and do canvas encode work.
  - `moonTruth.surface` reports read-time currentness, not the consumed frame. `lastConsumed` is correctly separate.
- **Severity:** low (observability truthfulness).

### EF-E07 — A Moon-wrapper or initial-receiver failure removes the whole-sky first paint
- **Machines:** NEW-E-01, R30, R14 (sky lane).
- **Evidence class:** **demonstrated** by trace; the R0021 contract §F records "the same rethrow also skips `SalahMoonHead` and the first paint".
  - `build_moon.py` L120–129: `head_owner` (defines `SalahMoonHead` and calls `SalahPrepareFirstPaint`) follows `moon-native.mjs` in the same IIFE.
  - `real-sky/native-first-paint.mjs` L34 calls `window.SalahMoonHead.compose` unguarded inside a try that sets `SalahFirstPaint.error`.
  - With `SalahMoonInitial` absent, `moon-first-paint.mjs` L29 throws for any visible Moon.
- **Severity:** low (coupling of optional subsystems; prayer is unaffected).

### EF-E08 — Hidden-tab return discards a still-valid refined surface
- **Machines:** NEW-E-04, R19.
- **Evidence class:** **demonstrated** by trace (`moon-native.mjs` L239 → `clear` → `fallback`; host.test.cjs L289 asserts it).
- **Effect:** each hide/show re-runs the full 64→8192 adaptive pipeline. This is intentional truth-first behaviour (a clock seek is undetectable while paused), but it costs CPU.
- **Severity:** low (efficiency).

### EF-E09 — Near-continuous refinement at 1× and an unpooled resource footprint
- **Machines:** R19, R25, R37.
- **Evidence class:** **plausible risk**, from a **model estimate only**, never measured.
  - A refinement restarts when the drift reaches `PHASE_POSITION_BUDGET/4` past the leading-edge target (L139; lead `2·budget/maxD`, `moon-precision.mjs` L24).
  - At ≈1.48e-4 rad/min of phase motion, that is ≈12 min at D≈108 device px and ≈4 min at D≈324.
  - An adaptive render takes up to ≈169 s (host.test.cjs L299, Firefox).
- **Footprint:** each Moon worker holds four nested WASM instances, each with a ≤512 MiB ceiling and non-shrinking pages (`moon_kernel.c` L25).
- **Severity:** low–medium efficiency; no whole-widget budget exists (the original GDOPL point, unchanged).

### EF-E10 — A transient initial-render exception permanently disables the initial V5 tier
- **Machines:** R21, R30, NEW-E-02.
- **Evidence class:** **plausible risk**. `moon-native.mjs` L122 sets `status.initialError`, and L109 refuses forever after. Combined with EF-E02, a later worker failure leaves no presentable surface, which means an empty slot.
- **Severity:** low (no transient trigger identified).

### EF-E11 — The 240 s refinement deadline sits close to the observed run time
- **Machines:** R20, R28.
- **Evidence class:** **plausible risk**. L143 sets 240 s against a 169 s observed Firefox run (host.test.cjs L299), a margin of about 1.4×. On slower devices the deadline fires, then the run is terminal (EF-E02). The preview does not extend the deadline.
- **Severity:** low–medium. Device distribution unknown.

### Classified recorded observations
| Observation | Location | Classification |
|---|---|---|
| Firefox cached-404 Moon non-recovery | `moon-worker.mjs` L6 `force-cache` (NEW-E-03) + no product retry (EF-E02) | demonstrated (R0021 b21); pre-existing; routed, not fixed |
| No Moon after an injected wrapper-construction failure | `src/native/index.html` L2238 + `moon-native.mjs` L298 | demonstrated (EF-E03) |
| Unguarded `installWorkerSource` | `tools/build_moon.py` L130 | demonstrated, isolated (EF-E04) |
| Can optional Moon block prayer? | `src/native/index.html` L3494 before L3499; L3877 without try | **yes, if `request()` throws**: propagation demonstrated by probe; no natural trigger found (EF-E01). Script-level failures (wrapper, refinement tail) do **not** block prayer (separate `<script>` elements). |

---

## 4. GDOPL inputs (Gradient Descent Over the Project Lagrangian)

These are schematic only. No weights, gradients or optima are claimed. Hard constraints in play:
- **F_hard:** optional astronomy never blocks prayer; truthful lunar provenance and light; accepted vs displayed state stay separated; instance-owned disposal; canonical source ownership (`moon/src/*` authored, generated host never edited); the AGENTS gate D opaque calendar Moon.

| # | Interaction | Current q | Neighbour q' = apply(q, η) | Anticipated benefit / regression cost | Evidence | Class |
|---|---|---|---|---|---|---|
| G1 | Moon ↔ prayer render ordering | `renderMoon()` synchronous before prayer DOM writes; no isolation | η1: try/catch around Moon calls in `renderMoon`/`paint`; η2: move `renderMoon` after prayer publication | Removes a hard-constraint dependency on "Moon never throws". Cost: masked Moon errors need a receipt; ordering change may alter the first-paint Moon/geometry stamp (N12 freshness) | Probe EF-E01; no before/after | plausible improvement requiring verification |
| G2 | Worker failure → recovery owner | sticky, terminal; `retry()` unowned | η: bounded automatic retry (backoff, on visibility resume), reusing `retryCount≤3` | Refined Moon recovers from transient failures. Cost: retry CPU and network; a cached 404 still defeats it (G3) | Code trace; R0021 b8/b19 show retry works when driven | plausible improvement requiring verification |
| G3 | Asset fetch cache admission | `force-cache` | η: `cache:'default'`, or a `no-cache` retry attempt | Firefox cached-error recovery. Cost: revalidation traffic for large assets | R0021 b20 vs b21 (server-side change only) | plausible improvement requiring verification |
| G4 | Wrapper replay vs live runtime (RF01) | f71fef6c: replay disposed the successor detail | 363c3e53: pre-effect refusal + captured detail + conditional slot clearing | Single live pair. Cost: hot replay unsupported (owner-approved) | before/after source + tests + mutants + native cells | **demonstrated improvement** |
| G5 | Runtime absent → reveal | no disc (gate requires runtime) | η: admit the native calendar fallback when slot is null | AGENTS "never empty slot". Cost: conflicts with "no legacy substitution"; needs pixel review | R0021 §F native | incomparable (owner decision) |
| G6 | Light eligibility ↔ visible surface | `surfaceFailed=_pbrFailed` | η: `surfaceFailed=!SalahMoonRuntime?.surface()` | Truthful "no light without a disc". Cost: moonlight flicker during scene transitions; consumer timing | trace only | insufficient evidence |
| G7 | Diagnostics ↔ presentation | getters adopt and publish | η: pure-read diagnostics; adoption only in `request`/`poll` | Truthful QA and no read-induced work. Cost: preview handoff timing (`host.test.cjs` L94 contract) | trace + test | plausible improvement requiring verification |
| G8 | Hidden tab ↔ accepted refined | discard on hide | η: retain and recheck scope/clock on resume | Avoids re-render. Cost: stale-authority risk after a hidden seek | trace | retain (truth-first) |
| G9 | Refinement cadence / footprint | continuous ~4–12 min restarts; 4 WASM shards | η: fewer shards or a longer refresh bound | CPU and memory. Cost: latency and accuracy bound | model estimate only | insufficient evidence |
| G10 | Moon wrapper ↔ sky first paint | head owner after `moon-native` in one IIFE | η: guard `SalahMoonHead` absence in first paint; split head owner | Sky first paint survives a Moon failure. Cost: generated-layout change | trace + R0021 note | plausible improvement requiring verification |

Comparison to the original projection: the RF01 temporal-ownership direction was taken and verified. The shared
priority contract (prayer > celestial > refinement) was not taken; G1 is its concrete instance in this lane.

---

## 5. Coverage

**Read fully:**
- `moon/src/moon-native.mjs`, `moon-install-guard.mjs`, `moon-detail.mjs`, `moon-worker.mjs`, `moon-pool.mjs`, `moon-engine.mjs`, `moon-quality.mjs`, `moon-first-paint.mjs`, `moon-initial.mjs`, `moon-precision.mjs`, `moon-calendar.mjs`.
- `tools/build_moon.py` L105–151.

**Sampled:**
- `moon-initial-compact.mjs` (throw sites); `moon_kernel.c` (allocator and arena symbols).
- `src/native/index.html` Moon regions: L178–200, L530–537, L1885–2095, L2215–2250, L2988–3040, L3055–3177, L3268–3338, L3482–3530, L3600–3624, L3866–3892, L4167–4184.
- `real-sky/native-first-paint.mjs`, `native-assets.mjs` L60–80, `native-host.mjs` and `native-preview-host.mjs` (Moon call sites only).
- `docs/state-contracts/R0021.md`, by grep plus sections F/G.
- Issues #29 and #34 (body and certificate excerpts).
- Original catalogue entries N11, N12, R19–R30, R37 and RF01; GDOPL_FINAL.

**Not examined:**
- `surface_v5.mjs`, `asset-digest.mjs` internals; the full kernel numerics.
- `moon/tests/browser_check.py`, `tests/real-sky/moon_*_test.py`.
- Native pixels; a real browser (not permitted).

**Tests and probes run** (no tree writes; `git status` clean afterwards):
- `node --test moon/tests/*.test.cjs`: 133/133 pass.
- `node --test` on `tests/real-sky/moon-projection-cache`, `moon-worker-fixture`, `native-lunar-*`, `native-moon-admission`, `native-worker-lunar-display`, and `tests/moon-fixture-anchors`: 31/31 pass.
- `node tests/r0022-lunar-consumers.cjs`: 24 pass / 2 fail. Both failures are star-wash synthetic cases ("glints release wash…", "ordinary render refreshes star appearance…"), outside the lunar-light gates.
- Probe `probes/E/moon-throw-blocks-prayer.cjs` (VM, network denied): confirms EF-E01 propagation.
