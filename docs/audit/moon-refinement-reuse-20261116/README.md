# Moon refinement reuse and scheduling: feasibility assessment (2026-11-16)

Research only, under the owner directive of 2026-11-16 (sections 3 and 5). Nothing here changes the product: no
cross-tab storage, no change to the refinement stopping rule, no change to R0033's accepted decisions, no product
path change. Probes run the generated product worker unchanged, or an in-memory copy with one documented string
patch. Source identity: `main` 47faae32b21e08adc8928f139f0c5387c7316e71 (`moon/BUILD.json`: worker
`e6d3f732…`, kernel `4fcf7888…`, asset manifest `3d4cb527…`). Evidence: `evidence/`. Probes: `harness/`.
Every browser launch went through the startup-advisory isolation helper (copied as `harness/iso.cjs`).
**Isolation: 14 isolated environments, 597 request records across all layers (169 loopback-served, 5 proxy-refused,
197 route decisions, 226 browser-observed). The 25 external attempts (`fonts.googleapis.com`, `aus5.mozilla.org`)
were all refused: 0 allowed off loopback** (per-run proxy, route and browser logs; section 7).

Dispositions use the directive's three values: CONFIRMED, REFUTED, UNDETERMINED. Facts (F) are measured or read
from source at the commit above; hypotheses (H) are reasoned but not measured; unknowns (U) are open.

## Front section (for the owner)

### Answer in brief

The refined Moon is a pure function of a small scene whose only varying input is the Sun direction (the phase
angle), and it is reproducible bit-for-bit within each engine and, for the scenes tested, across Chromium, Firefox and WebKit. But the advisory's premise that the scene "depends only on a phase bucket" is **refuted for the
normal live widget**: an advancing clock gives every refinement a *continuous* phase angle (the native phase plus a
leading-edge offset), so two tabs never request the same scene and no stored result could ever be hit. The phase
is quantised only when the clock is frozen. Memoisation is therefore possible only after one product change: snap
the advancing-clock scene to a fixed phase grid. That changes what the Moon worker computes, so it needs owner
authority even before any storage question arises.

Today each visible tab refines about 205 (median day; range 118–240) times a day at DPR 1 and 360 at DPR 2. In every engine,
**about 46 % of that work is done while the Moon is day-suppressed**, and in some of it the Moon is also below the
horizon. Any time the
refinement takes longer than the remaining validity of the old result (observed live in Firefox at DPR 2: 18 s on the preview tier in 12 minutes), the visible
Moon falls back to the preview tier. The work also hits a pathology that the advisory did not report. On about 25
occasions a year, near full and new Moon, the product's waxing flag disagrees with the direction in which the phase
angle is moving, for 1 to 261 minutes each time. The leading edge then points the wrong way, and at every native minute step the refined Moon expires. The disc then drops to the main-thread initial tier, then to the preview, then returns to refined after a new job. Live, on 24 Nov: 5 jobs in 4 minutes, about 10 s of every minute below the refined tier. The model gives about 77 such expiries a month at this location, only while the Moon is high.

### Strongest supported option (not recommended for adoption)

**Day deferral with an anticipatory dusk start, kept inside the current scene definition.** This is candidate (B)
with the startup advisory's day-deferral prototype as its base. No refinement runs while `_skyMoonPresence` is 0.
One refinement starts ahead of the dusk reveal, with a lead time between the measured duration and the validity
window (section 4B). It needs no storage, no new identity and no new presentation tier. It removes about 46 % of
steady-state refinement work. It adds one refinement per evening and leaves the night-time cadence, the
stopping rule and every accepted R0033 state unchanged. Its risks are a dusk race (a reveal that comes before the
result, which today's continuous work hides) and a moving reveal instant under weather changes. It is still a
scheduling change under R0033 DG-4 ("no new budget; keep accepted limits"), so the owner must decide it.

### Strongest competing alternative

**Exact memoisation on a canonical phase grid (candidate A), in memory first and across tabs second.** The
advisory's preferred design, corrected. The scene's phase angle is snapped to a grid that keeps the existing
0.0416 device-pixel bound. The key is (worker-source digest, engine Math fingerprint, profile, grid index, waxing),
which holds nothing derived from location. The value is the refined result (8.88 MB raw, about 2.3 MB gzip). Its
strength: a second tab, a hide/show cycle or a reload inside the same grid cell presents the refined Moon at once,
with zero worker time. Its costs: a product change to the scene definition; storage failure modes (opaque origins,
partitioned iframes, no OPFS in the WebKit build tested); an admission rule that has to be designed so that a cache
read is never mistaken for a worker result in R0033's recovery accounting; and, without (B), no reduction in
steady-state work for a single long-lived tab. Over a lunar month there are about 8,150 (DPR 1) to 16,300 (DPR 2) grid cells,
so a store can only ever hold the current and next cell, never a calendar of results.

### Verified from evidence in this audit

- Same engine: identical refined bytes across repeated renders in one worker, a new tab, a new browser process,
  2 instead of 4 shards, concurrent tabs and DPR 1 versus DPR 2 (`evidence/determinism.json`, `evidence/supplement.json`).
- Across engines: byte-identical for scenes G and C across Chromium 148, Firefox 150 and WebKit 26.4, although the engines' `Math` functions differ. The identity is observed, not guaranteed (`evidence/determinism-analysis.json`).
- Display-referred stopping: measured at the real disc size (108 px at DPR 1, 216 px at DPR 2):
  - after the 256-sample step, 67–75 % of the refinement time remains (Chromium, four phases), yet it changes the
    DPR-1 display by at most 0.26 code;
  - the 1,024-sample step is within 0.11 code (DPR 1) and 0.25 code (DPR 2) of the final result.

  Source: `evidence/determinism.json` `steps` and `evidence/supplement.json`. The stopping rule is not changed.
- Cadence and the wrong-way leading edge: `evidence/cadence-sim-30d.json` (a replay of the host's own decision rule
  over the product's own ephemeris), `evidence/waxing-mismatch-365d.json`, and live observation
  `evidence/live.json`.
- Storage: IndexedDB and the Cache API stored and read back a 8,884,800-byte entry intact in all three engines.
  OPFS worked in Chromium and Firefox but is absent from the WebKit build tested. All three refuse storage in an
  opaque-origin iframe (`evidence/storage-probe.json`).

### Unresolved

- Real Safari, real Chrome or Edge profiles, other machines and other CPUs (only Playwright builds on one 16-core
  Windows host were tested). The cross-machine claim in section 2(f) is an argument from the arithmetic, not a
  measurement.
- Worker CPU was not traced. The CPU figures here are wall time × 4 shards (an upper-bound estimate). The
  startup advisory's CDP traces (77–94 s in the first 30 s) remain the only measured CPU.
- Whether the wrong-way leading-edge interval is visible to a viewer (disc tier changes, main-thread initial
  re-renders), beyond the counts recorded in section 3.
- R0033 row R33-19 (the M5 30-minute duty-cycle record) is still not produced. This audit's cadence data informs
  it but does not discharge it.

### Owner decisions this would need

1. Whether the advancing-clock scene may be snapped to a canonical phase grid (precondition for any memoisation;
   changes what the worker computes; affects the R0033 DG-4 baseline and ISM-MOON-003).
2. Whether refinement may be deferred while the Moon is day-suppressed and started ahead of dusk (a scheduling
   change under DG-4).
3. Separately, and only after 1: whether the first cross-tab store may be introduced. That decision includes the
   storage technology, the size bound, the eviction rule, and whether a store hit is a new presentation source in
   the ISM-MOON-003 transaction.
4. Separately: whether a defect work order should own the wrong-way leading edge near full and new Moon (section
   3.4). It is a correctness and efficiency defect of the accepted V5 behaviour, independent of reuse.
5. Display-referred stopping (C) changes the accepted stopping rule and is not recommended by this evidence for a
   first step. The measured margin is reported for the owner only.

---

## 1. Q1 — Complete input identity of the refined Moon result

Source identity: `main` 47faae32 (`moon/BUILD.json`: worker `e6d3f732…`, kernel `4fcf7888…`, asset manifest
`3d4cb527…`). Line numbers are of the authored sources at that commit.

### How the refined scene is built

`poll()` (`moon/src/moon-native.mjs` L166-187) calls `scene(s)` (L104-107) = `nativeCalendarMoonScene(s,profile())`
(`moon/src/moon-precision.mjs` L22-27). That scene has a fixed raster and camera — `size:540`, `outSize:300`,
`diameter:288`, `basis:[0,1,0,0,0,1,1,0,0]`, `earth:[384400,0,0]`, `distance:384400`, `extent:1.08`, `tilt:0` —
and exactly one varying physical quantity, the Sun direction `[cos α, ±sin α, 0]`, where:

- **advancing clock** (`timeScale>0`, every normal live tab): `α = acos(2f−1) ∓ 2·0.0416/D_max·(1−1e−9)`, i.e. the
  *continuous* native phase angle shifted to a leading edge. The scene itself is not snapped to any grid. The
  native fraction steps once per simulated minute (index.html L3841), and `D_max` takes integer values, so two tabs
  on one device with the same DPR, zoom and Moon-altitude class that start a job in the same native minute do
  request bit-identical scenes. Any other pair does not.

  **The host's job `key` is bucketed even though the scene is not.** `key(s)` (native L43) holds
  `physicalFraction = canonicalFraction(f, D)`, the grid-snapped fraction (native L41). The scene sent to the
  worker uses the unsnapped leading edge. Two jobs with equal host `key` can therefore have different bytes. This
  most likely explains the advisory's "phase bucket", and it is a trap for any future cache keyed on `key`.
- **frozen clock** (`timeScale==0`, i.e. `simTime` without `timeScale`, QA scenes): `α = acos(2·f_c−1)` with
  `f_c = canonicalFraction(f, D)` (L55-60), the nearest point of a grid of spacing `4·0.0416/max(104,D)` rad.

`D` = `ceil(max(rect.w, rect.h)·dpr)` of `.mphoto` (L39), `D_max = ceil(D·max(1, maximumPresentationRatio))`
(L40), `maximumPresentationRatio = 1.13/(1.11+0.02·up)` (`src/native/index.html` L4697), `up = clamp((alt+2)/6)`
of the observer's Moon altitude (L2296). `f` = `moonSky.frac` from `moonIllum(date)` (geocentric; L2072-2077),
`moonPhase(date)` (mean synodic) when lat/lon are not finite, or `simMoon` (L2289-2292).

### Dependency table

| Input | Enters the refined SURFACE bytes? | Path (file:line at 47faae32) |
|---|---|---|
| Phase angle α (UTC → geocentric ephemeris) | **Yes**, continuously (advancing clock) | precision L23-25; index.html L2072-2077 |
| Phase quantisation | **Only in the frozen clock** (grid 4·0.0416/max(104,D) rad); advancing clock uses a continuous leading edge | precision L8-19, L24 |
| Waxing flag | Yes (sign of Sun y; also in `scope`) | precision L26; native L47 |
| Phase source (ephemeris vs mean synodic vs `simMoon`) | Yes (different `f` for the same instant) | index.html L2289-2292 |
| Libration, Earth distance | **No**: basis and Earth vector fixed (mean-libration calendar Moon) | precision L26 |
| Position angle / parallactic rotation | **No** (`tilt:0`, upright Moon) | precision L26; index.html L2077 comment |
| Observer lat/lon, height | **Not directly** (`f` is geocentric). **Indirectly yes**: Moon altitude → `up` → `D` (group scale 1.11…1.13) and `D_max` → leading-edge offset of α; frozen clock: `D` → grid | native L39-40; index.html L2296-2297, L4697 |
| `simMoon`, `simWax` | Yes (via `f`, waxing) | index.html L2290 |
| `simMoonAlt`, `simMoonH` | Indirectly (via `up` → `D`, `D_max`) | index.html L2294 |
| DPR | Only through `D` (and so α); the raster is DPR-independent (540/300/288) | native L39; precision L26 |
| On-screen disc size / canvas size | Only through `D`; output canvas fixed 300×300 | native L12, L39 |
| Scene metadata `phaseQuantumRadians`, `phaseDisplayDiameter`, `requestedNativeFraction`, `geometryConvention` | No pixel effect; they are in the scene JSON, which the host compares for result admission | precision L26; native L247 |
| DEM / colour assets | Yes; digests in `manifestIdentity` → `physicalIdentity` | engine L41, L50, L73, L117 |
| WASM kernel | Yes; `manifest.wasm.sha256` in `manifestIdentity` | engine L66, L73 |
| JS surface code (V5 tone map, pool join/filter, calendar proxy, sRGB encode) | Yes; **not** in `physicalIdentity` (only in the worker source digest) | surface_v5; pool L79-91; calendar L8-41 |
| Profile (calendar / reference) | Yes (`profileIdentity`; `profileMode` in `scope`) | native L29, L47; surface_v5 L69 |
| Quadrature rule / stopping rule | Yes (part of the worker source); the final `physicalIdentity` records the last step's rule | quality L9-45; engine L117 |
| Worker count / shard layout | Fixed at 4 in product; measured below (2 vs 4) | pool L29, L37, L50 |
| Tier | initial (main-thread receiver), preview (64-sample step), refined (`result`) are different bytes | native L114; quality L33 |
| Earthshine | Yes, but fixed geometry for a given α (Earth vector constant) | engine L110 |
| Calendar / below-horizon proxy | Its *bytes* (`calendarLinear`, `calendarRgba`) are a pure function of the result + material; its *blend weight* `up` is applied afterwards | calendar L8-41; native L50-60 |
| Display mapping after the surface (device-resolution projection, sky gas, cloud, opacity, exposure, placement) | No — applied downstream by `moon-detail.mjs` and the native compositor | detail L43-141 |
| Time of day / day suppression | **No effect on bytes, and no effect on scheduling**: `poll()` has no day or horizon gate | native L166-187; index.html L3235-3243 |
| Browser engine (JS `Math` passed to WASM as imports; JS-side `**`, `expm1`, `acos`) | Not observed for the tested scenes (Q2), not structurally excluded | engine L67; kernel L9-12; surface_v5 L15, L32 |
| Host scope (generation, sceneIdentity incl. lat/lon/tz/clock anchor, dpr, profile) | Not in the bytes; in `scope`/`key`, which fence admission | native L43, L47, L65 |

### Minimal correct cache key, and dispositions

**For the surface bytes** the key is: (worker-source SHA-256, which covers kernel, assets and all JS; engine
identity, see Q2; profile fingerprint; the exact Sun vector bits, i.e. α and waxing; tier = refined). Raster, camera,
Earth vector and extent are constants of that worker source. DPR, D, canvas size, location, time of day and weather
do not enter the bytes except through α.

**For a reusable key** α must come from a canonical grid (section 4A), because the live α is continuous and, through
`D` and `D_max`, weakly depends on the observer's Moon altitude and on DPR.

- Advisory claim "the refined scene depends only on a phase bucket … and nothing local": **REFUTED** for the
  advancing clock: α is continuous and depends on `up` through `D` and `D_max`. Coincidence needs the same native
  minute and the same `D` and `D_max`, so the useful cross-tab hit rate is near zero. It is the host `key`, not the
  scene, that is bucketed; **CONFIRMED** for the frozen clock (grid
  `4·0.0416/max(104,D)`), where only the DPR-dependent `D` selects the grid.
- "Bucket ≈ 11 min at DPR 1": **CONFIRMED as the validity window, not as a bucket.** `4·0.0416/D` rad at the
  measured `D = 109` (rect 107.8 × 108.1 CSS px at `up = 1`, `evidence/live.json`) and the measured 30-day mean phase
  rate 2.31 × 10⁻⁶ rad/s is 661 s; the advisory's 650 s used D = 104 and the mean synodic rate. The re-render
  interval is shorter (section 3).
- "Nothing local enters the refined SURFACE": **CONFIRMED for the bytes given α**; placement, rotation (none),
  atmospheric tint, opacity and cloud are applied afterwards by `moon-detail.mjs` and the native compositor. Local
  quantities enter only the choice of α (above).

## 2. Q2 — Determinism

Method (`harness/determinism.cjs`, `harness/moonprobe.html`, `harness/supplement.cjs`). Each run passes a probe
page the exact scene the host would build (literal Sun vectors). The page runs the generated product worker
`moon/moon-worker.js`, SHA-256 `e6d3f732…`, which equals the BUILD.json pin and is recorded per run. The page
hashes every published field of the `result` message: `rgba`, `calendarRgba`, `surfaceLinear`, `surfaceCoverage`
and `calendarLinear`. Scenes: G (f 0.80 waxing), C (0.15 waxing), H (0.50 waning), F (0.98 waning). Engines:
HeadlessChrome 148.0.7778.96, Firefox 150.0, WebKit 26.4 (Playwright builds, Windows 11, 16 logical cores).

| Condition | Runs | Distinct result hash tuples | Disposition |
|---|---|---|---|
| (a) Repeat in one worker (G ×3, which takes the sparse full-mask path on the reused camera) | 3 per engine | 1 per engine | **CONFIRMED** byte-identical |
| (a′) Camera-cache reuse: C rendered after G in the same worker vs C in a fresh worker | 2 (Chromium) | 1 | **CONFIRMED** |
| (b) New tab, new browser process | 2 per engine | 1 (same as (a)) | **CONFIRMED** |
| (b′) Two tabs refining G at the same time (contention) | 2 (Chromium) | 1 | **CONFIRMED** |
| (c) 2 shards instead of 4 (in-memory patch of `MoonPool.create`) | 2 (Chromium) | 1 (same as 4 shards) | **CONFIRMED** |
| (c′) Stepwise variant (every step published; final result) | 4 scenes Chromium, G in Firefox and WebKit | equal to the product variant | **CONFIRMED** |
| (d) Across Chromium, Firefox, WebKit, G and C | 22 G runs, 4 C runs in total | 1 per scene across all engines | **CONFIRMED for these scenes**; not structurally guaranteed (below) |
| (e) DPR 1 vs DPR 2 (same scene) | 2 (Chromium) | 1 | **CONFIRMED**: the raster does not depend on DPR |
| (f) Across machines | not testable here | — | **UNDETERMINED** (argument below) |

G was rendered 10 times in Chromium, 6 in Firefox and 6 in WebKit. Every one of the 22 G runs, across all three
engines, gave rgba `fb1fa27d…` and surfaceLinear `2e6d57bd…`. The analysis compared the exported bytes
(`evidence/determinism-analysis.json`): 0 differing rgba or calendarRgba pixels, 0 differing surfaceLinear floats,
and 0 rounded-code differences in the display projections at 108 and 216 px, for every engine pair and both scenes.

**Why cross-engine identity is observed but not guaranteed.** The kernel imports `sin, cos, asin, atan, exp, expm1,
log, atan2, pow` from the page's `Math` (`moon/src/moon_kernel.c` L9-12; `moon-engine.mjs` L67). The V5 tone map
and the sRGB encoding use JS `expm1` and `**` (`surface_v5.mjs` L15, L32). The probe hashed each of those functions
over 200,000 pseudo-random arguments per engine (`math` in `evidence/determinism-analysis.json`):

- Chromium and Firefox differ in `sin`, `cos` and `pow`.
- WebKit differs from Chromium in `sin`, `cos`, `pow`, `asin`, `atan`, `exp`, `expm1`, `log`, `atan2` and `acos`.
- WebKit's `sin`, `cos` and `pow` hashes equal Firefox's.

So the engines do compute different `Math` results somewhere in the argument space, yet the published float32 and
8-bit surfaces came out identical for these scenes. The reason is not established. Two hypotheses are open: the
differences are last-bit f64 differences that the float32 and 8-bit publication absorbs, or the kernel's arguments
avoid the arguments where the engines disagree. Either way, identity is an observed property of these two scenes,
not a property of the arithmetic.

**There is a second engine dependence, in the product path, that the probe deliberately bypassed.** The host builds
the Sun vector with JS `Math.acos`, `cos` and `sin` (precision L23-25). For the four probe fractions those inputs
were bit-equal in all engines (`sceneInputs`), but WebKit's `acos` hash differs over random arguments. Equal native
fractions can therefore give different scene vectors in different engines.

**Consequence for memoisation.** Cross-engine identity does not matter for a browser-local store: storage is per
browser profile, so a store is never shared between engines. Within one engine build, (a)–(c) and (e) support exact
memoisation. Because `Math` implementations can change between engine versions, a key that is safe across browser
updates must carry an engine identity (a runtime `Math` self-test fingerprint, or the user-agent version), unless
the scene and kernel arithmetic stop depending on host `Math`. The second option is a kernel recompile, which R0021
excluded from that increment.

**Scope of the cross-engine result.** Cross-engine identity covers two literal Sun vectors passed straight to the
worker: G `[0.6, 0.8, 0]` and C. Those are not the vectors the host builds; the host uses `Math.acos`, `cos` and
`sin`, which differ in WebKit. H, F, the real leading-edge angles and the full-Moon (α ≈ 0.09) and near-new regimes
were Chromium-only or untested.

**(f) Across machines (UNDETERMINED; hypothesis only).**

- WebAssembly f64 arithmetic is IEEE-754 and deterministic except for NaN payloads.
- Whether one engine version gives the same bytes on every machine depends on its `Math` implementation.
  SpiderMonkey's `pow` and `exp` can defer to the platform C library, and Chromium and Firefox already disagree on
  `sin`/`cos` here. "Same engine version, same bytes on any machine" is therefore only a hypothesis (H2).
- JavaScriptCore relies more on the platform C library, so real Safari on macOS or iOS may differ from Playwright
  WebKit on Windows. This audit did not test Safari, and it does not claim Safari behaviour.

The worker joins shard rows by ownership and filters and encodes once on one thread (`moon-pool.mjs` L62-91).
No floating-point reduction depends on scheduling, which is consistent with (b′) and (c).

## 3. Q3 — Steady-state refinement frequency

### 3.1 The rule, from source

- `poll()` runs every 250 ms (native L344) and from `request()` on native paints.
- It starts a new job when no pending job matches and the accepted non-initial record's signed drift has reached
  `B/4` (native L182; B = 0.0416 device px). A job's scene is created at the leading edge, with a signed drift of
  about −B (precision L24), so a new job starts after the phase has moved about `2.5·B/D` rad.
- The accepted record stays presentable until the drift exceeds +B, about `4·B/D` from its creation (native L66).
  A replacement must therefore finish within about `1.5·B/D` of phase, or the visible tier drops to the stored
  preview (L177, L118-125) or to the main-thread initial tier (L178).
- The native phase seen by `capture()` (`moonSky.frac`) is refreshed once per simulated minute (index.html L3841,
  L2302-2314), so job starts fall on minute boundaries.
- There is **no day, horizon or visibility gate other than `document.hidden`**. A hide clears everything and the
  next show recomputes (ISM-MOON-019).

| D (device px) | Validity window 4B/D | Re-render interval ≈ 2.5B/D (rounded up to a minute) | Must finish within ≈ 1.5B/D |
|---|---|---|---|
| 109 (DPR 1, measured) | 661 s | ≈ 7.1 min → 8 min at the live phase rate | 248 s |
| 217 (DPR 2, measured) | 332 s | ≈ 3.6 min → 4 min | 125 s |

(Mean phase rate over the 30 days from 16 November 2026: 2.31 × 10⁻⁶ rad/s, from the product ephemeris. The live
runs saw 2.25 × 10⁻⁶ rad/s.)

### 3.2 Live observation (the real product, `evidence/live.json`, summary `evidence/live-summary.json`)

| Cell | Moon jobs posted | Job starts (wall s) | Results (job duration) | Visible tier, 1-s samples | Notes |
|---|---|---|---|---|---|
| Chromium DPR 1, night, `timeScale=4`, 480 s | 5 | 2, 120, 240, 360, 480 | 4 (30–40 s) | refined 435, preview 34, initial 4 | every 8 sim-min; D = 109 |
| Chromium DPR 1, **day**, `timeScale=4`, 300 s | 3 | 2, 120, 240 | 3 (41–53 s) | refined 254 (slot day-suppressed) | full refinement while invisible |
| Chromium DPR 2, night, `timeScale=2`, 480 s | 5 | 2, 120, 240, 360, 480 | 4 (33–43 s) | refined 430, preview 37, initial 6 | every 4 sim-min; D = 217 |
| Firefox DPR 2, night, real time, 720 s | 4 | 4, 241, 481, 721 | 3 (102–139 s) | refined 577, preview 118, initial 15 | every 4 min; job 3 (139 s) outlived the ≈125 s window: **preview shown 602–620 s** |
| Chromium DPR 1, wall clock shifted into the 24 Nov full-Moon mismatch interval, 240 s | 5 | 4, 60, 120, 180, 240 | 4 (8–10 s) | refined 196, preview 29, initial 12 | f falls while waxing = true; the refined record **expired at every minute step** (initial → preview → refined each minute) |
| Same, control one day earlier, 240 s | 1 | 3 | 1 (19 s) | refined 214, preview 16, initial 4 | normal: no expiry |
| Same, 8 Dec new-Moon mismatch interval (Moon below the horizon), 180 s | 1 | 5 | 1 (13 s) | refined 162, preview 10, initial 5 | no expiry, as modelled (`up < 1` slack; phase nearly stationary) |

The probe counted only Moon jobs (messages carrying a lunar scene). The raw "renders posted" totals in the run
logs also count the refined-sky worker. `timeScale` compresses the phase motion, not the job duration, so the
accelerated cells overstate the share of time spent in preview.

### 3.3 Thirty-day model (`harness/cadence-sim.cjs` → `evidence/cadence-sim-30d.json`)

The model replays the host decision rule above at 250 ms with the minute-stepped native phase, the product
ephemeris and measured job durations, for one always-visible tab at the fixture location (Madinah; the location
matters only for the day and horizon accounting and for `up`). It reproduces the live cadence: 8 and 4
simulated minutes.

| Engine / DPR | Jobs per day, median (range) | Worker busy fraction | Of busy time: day-suppressed / Moon below horizon | Visible tier: refined / preview / initial | Est. worker CPU per day (4 × wall, upper bound) |
|---|---|---|---|---|---|
| Chromium DPR 1 (31.1 s) | 205 (118–240) | 7.1 % | 46.1 % / 48.1 % | 99.9 / 0 / 0.1 % | 6.9 h |
| Chromium DPR 2 | 360 (229–480) | 13.2 % | 46.5 % / 48.6 % | 99.9 / 0 / 0.1 % | 12.7 h |
| WebKit DPR 1 (46.2 s) | 205 | 10.6 % | 46.1 % / 48.1 % | 99.86 / 0 / 0.14 % | 10.2 h |
| WebKit DPR 2 | 360 | 19.6 % | 46.5 % / 48.6 % | 99.86 / 0 / 0.14 % | 18.8 h |
| Firefox DPR 1 (153.2 s) | 205 | 34.8 % | 46.5 % / 48.5 % | 99.8 / 0 / 0.2 % | 33.4 h |
| Firefox DPR 2 (153.2 s) | 360 | **64.7 %** | 46.7 % / 48.8 % | **85.2 / 14.6 / 0.2 %** | 62.1 h |
| Firefox DPR 2 at the advisory's 115 s | 360 | 48.6 % | 46.6 % / 48.7 % | 98.0 / 1.9 / 0.2 % | 46.6 h |

**This section is a MODEL REPLAY, not a measurement.** It uses one mid-phase duration per engine for every phase.
Live jobs near full Moon took 8–14 s in Chromium, against 31 s at mid phase. The job counts per day, which the rule
drives, are insensitive to duration. The busy fractions, the CPU column and the Firefox preview share depend
directly on the single duration.

The "CPU" column is 4 shards × busy wall time. It exceeds 24 h because four workers run at once. It is an upper
bound, not a trace (U3).

### 3.4 Is work repeated unnecessarily? Dispositions

- **Same identity recomputed in steady state: REFUTED for an undisturbed tab.** α advances between jobs, so no two
  jobs share a scene.
- **Work that is never presented: CONFIRMED.**
  - About 46 % of all job time runs while the slot is day-suppressed. Of the day's jobs, only the one whose cell
    spans the dusk reveal can ever be shown.
  - Work while the Moon is below the horizon is presented, as the ashen calendar disc, at night.
- **Valid work discarded: CONFIRMED.**
  - Every hide/show throws away a still-valid refined result and recomputes it (ISM-MOON-019; known, PRA-F-26).
  - Inside a waxing-flag/phase-direction mismatch interval (F7), the leading edge points the wrong way. Each
    minute step of the native phase can then push the accepted record past −B: it expires, the main-thread initial
    tier is rendered (native L143-161), and a new job starts.
  - With the Moon high (`up = 1`, so `D_max = D` and no slack), the model gives 47 expiries and 49 jobs in the 3 h
    around the 24 Nov full Moon, with the initial tier visible 14 % of that time
    (`evidence/cadence-sim-fullmoon-window.json`). It gives about 77 expiries per month at this location.
  - With the Moon low or below the horizon (`up < 1` gives 2 % slack), the 8 Dec interval produced no expiry.
  - **Live confirmation** (24 Nov 16:30 UTC, Chromium DPR 1, real time): 5 jobs in 240 s, one per native minute, against 1 in the control a day earlier. Each minute the disc went initial → preview → refined, about 10 s of every 60 s below the refined tier. The 8 Dec cell had 1 job and no expiry. Visibility of these swaps was not judged (U2): each is an initial ↔ terrain swap of the R0033 F-2 kind.
- **Refined lost between jobs (not "never current"): observed once, Firefox DPR 2.** In the single 720 s live run, the
  third job (138.9 s) outlived its predecessor's record. That record expired at 599 s, the sixth native minute step
  after its creation, and the preview was shown from 599 to 617 s (18 s). The refined tier was current for 577 of
  710 s. The model, using one 153 s duration, gives 85 % refined. At the advisory's 115 s that would be 98 %. At
  DPR 3 the window is about 83 s at D ≈ 326, so it would be worse (model only).

## 4. Q4 — Candidates against the current V5 baseline

Baseline (current accepted V5 behaviour, unchanged by this audit): continuous refinement in every visible tab,
day and night. The tab keeps one accepted result, re-requests once the phase drift reaches `B/4`, and drops it on
hide. Time to the refined Moon on a fresh tab at night (startup advisory, DPR 1, medians cold/warm): Chromium
31/28 s, Firefox 108/123 s, WebKit 30/36 s. Pure refinement time in this audit (uncontended, fresh worker, mean of
the product runs): Chromium 31.1 s, Firefox 153.2 s, WebKit 46.2 s (`evidence/determinism.json`). Firefox and
WebKit were slower here than in the startup advisory; the cause is not established (different session and load).

### 4A. Exact memoisation

**Does an in-memory memo exist today? No.** The tab keeps exactly one `accepted` record and skips a new job only
while `phaseDrift < B/4` (native L182). The other caches are intra-computation or downstream, and none returns a
refined result for an identity:

- the engine's camera cache (`cameraKey`, engine L89-99) and the pool's `lightKey` (pool L48), which reuse the
  camera receivers across Sun changes;
- R0022's one material-projection cache in `moon-detail.mjs` (`docs/real-sky/LUNAR_DISPLAY.md`, "Bounded Moon
  projection reuse"), which reuses the device projection downstream of the surface.

R0027's bound (`tools/native_core_spectral_cache.py`, 12,000 FIFO) is a precedent for a bounded cache, in the sky
core, and has no Moon role. After any `clear()` (hide, clock jump, scope, DPR or profile change) the next result is
recomputed from scratch, even when the old one would still satisfy the 0.0416 px bound. ISM-MOON-019 records this
as intentional (truth-first).

**Precondition (product change).** Advancing-clock scenes are continuous (section 1), so an exact key never repeats
across tabs. A store needs a canonical grid. One example design (not evaluated in the product): snap the scene α to
the grid point `g_k = k·q` that is nearest the leading edge. Choose the spacing `q` and the selection so that, for
every instant the host would present the record, the existing `matches()` bound `|D/2·(α_now−g_k)| ≤ 0.0416` still
holds. With `q = 2·0.0416/D_class` a cell is usable for at least half of the current validity window. The grid must
be defined per DPR class, because D enters the bound. It must not be defined per location: the up-dependent `D_max`
term has to be dropped or bounded by its maximum (ratio 1.018), so that nothing location-derived enters the key.

**Key (minimal, location-free).**

- worker-source SHA-256: covers the kernel, the asset manifest and every JS step;
- engine identity (Q2);
- profile fingerprint;
- grid index `k` and waxing flag;
- tier (`refined` only).

The DPR class enters only through `k`'s grid. Verified: none of these is derived from lat, lon, height, timezone
or weather (section 1 table). The current `physicalIdentity` (engine L117) is not sufficient alone, because it omits
the JS display code.

**Value and size (measured, `evidence/determinism-analysis.json` `entrySize`).**

- Raw, everything that `adopt()` needs (native L108-116): rgba 360,000 + calendarRgba 360,000 + surfaceLinear
  3,499,200 + calendarLinear 3,499,200 + surfaceCoverage 1,166,400 = **8,884,800 B**. This is independent of DPR.
- gzip-9 without calendarLinear: **2,317,137 B**. calendarLinear is surfaceLinear × one scalar gain (`moon-calendar.mjs`
  L15-16), so it can be rebuilt from the stored surface and a stored gain.
- In memory, adoption also builds two prefix tables of 541²×4 f64 each, 9.37 MB each (`moon-detail.mjs` L5-15).

**Entries per lunar month.** The phase angle sweeps 2π per synodic month. At `q = 2·0.0416/D`, that is 2π/q ≈
8,150 cells at D = 108 and ≈ 16,300 at D = 216: about 72 GB raw per month at DPR 1. A store can only ever be a
small ring of the current and next cells (≤ 2 entries, ~18 MB raw or ~5 MB compressed per DPR class). It cannot be
a calendar.

**Storage options (measured, `evidence/storage-probe.json`, an 8,884,800-byte entry with SHA-256 read-back).**

| | Chromium 148 | Firefox 150 | WebKit 26.4 (Playwright, Windows) |
|---|---|---|---|
| IndexedDB write/read, integrity | ok, 15/5 ms | ok, 153/41 ms (measured under load) | ok, 411/24 ms |
| Cache API | ok, 29/21 ms | ok, 328/55 ms | ok, 149/66 ms |
| OPFS (main thread, `createWritable`) | ok | ok | **unavailable** (`navigator.storage.getDirectory` undefined) |
| Opaque-origin (sandboxed) iframe | all SecurityError | all SecurityError | IDB/Cache SecurityError, OPFS TypeError |
| `storage.estimate()` quota | 6.4 GB | 10.7 GB | not available |

**Failure modes.** Every failure below must fall back to compute-as-today, must not count against the R0033
recovery budget, and must not set `bootCache` to `no-cache`:

- Opaque or `file://` origins (`offline.html`, sandboxed embeds): no store.
- Private windows: the store is ephemeral or absent (platform behaviour; not measured here).
- Storage denied, or quota exceeded.
- Eviction during a read.
- A corrupt or truncated entry: the stored SHA-256 must be checked before admission.
- A new deploy: the worker-source digest in the key invalidates the entry; old keys are evicted.
- Concurrent writes from several tabs: identical bytes, so last-writer-wins is safe if writes are atomic.

The TablissNG embed is an iframe under an extension page. Third-party storage partitioning keys the store by the
top-level site, so it is shared across the extension's tabs but not with a direct visit (H; not measured).

**Admission rule (currentness).** A stored entry is admitted only by the same read-time predicate as a worker
result:

- the record's grid α must satisfy `matches()` against the current capture: same scope, same epoch, same waxing,
  and `|drift| ≤ 0.0416` device px at the current D;
- it is presented under the current epoch, as if a `result` had arrived for the current pending identity;
- it never satisfies `takeInitialHead` (ISM-MOON-005);
- it never survives a `clear()` (ISM-MOON-019) except by being re-read and re-validated afterwards;
- a read that is in flight across a `clear()` is discarded (epoch fence).

A cached surface is thus presented only for the cell it was computed for and only while that cell is within the
bound. R0033's recovery states (`idle`/`scheduled`/`exhausted`) are untouched: a store hit while recovery is
`scheduled` may present a surface but does not cancel the recovery, and it does not count as `recovered`. These are
design requirements, not implemented behaviour.

**Saving (estimate, not prototyped in the product).**

- On a hit, time to the refined Moon is a store read plus SHA-256 plus adoption: tens of ms (IDB read 5–41 ms
  measured; hashing and prefix tables not measured) instead of 31/153/46 s, and no worker CPU for that cell.
- Steady state for a single long-lived tab: no saving. Each new cell still has to be computed once, by some tab.
- With N tabs open, the steady-state work divides by about N.
- Risks to fidelity: none to the surface itself (byte-identical by Q2), provided the integrity check and the key are
  complete.
- Risks to truthfulness and currentness: confined to the admission rule above.
- Needs owner decisions 1 and 3 (front section).

### 4B. Anticipatory dusk scheduling (with day deferral)

**What is today.** Refinement runs whatever the time of day (Q3), so at dusk the refined Moon is usually already
current. B is only meaningful together with day deferral, which is what saves work.

**The reveal instant.** The Moon slot is revealed when `_skyMoonPresence = clamp(darkness·1.8) > 0`, i.e. at solar
elevation −3° (index.html L3241-3243). Moonrise is not a reveal, because a below-horizon Moon is still shown as the
calendar disc (gate D).

**Lead time.** A job started at t₀ with the leading edge is presentable while its drift stays within ±0.0416 px:
for about 4B/D of phase (Q3 table). That is ≈ 10.4 min at D = 108 and ≈ 5.2 min at D = 216 (mean rate). The lead L
must satisfy duration ≤ L ≤ validity − duration. The validity window starts when the job's scene is created, not
when its result arrives:

- Chromium: 31–35 s ≤ L ≤ ~620 s (DPR 1) or ~295 s (DPR 2).
- WebKit: 40–51 s ≤ L ≤ ~610 s or ~280 s.
- Firefox: 102–169 s ≤ L ≤ ~490–560 s (DPR 1) or ~160–230 s (DPR 2).

These bounds use mid-phase durations; full-Moon jobs are shorter (8–14 s in Chromium, live).

- For Firefox at DPR 2 the feasible window is narrow and can close: with a 169 s job the upper bound is about 163 s,
  below the duration.
- The advisory's rule ("2× last duration, floor 60 s") exceeds the upper bound there.
- The rule considered earlier ("max(1.2 × duration, 60 s), capped at half the validity window") also cannot be
  satisfied there: 166 s < 1.2 × 153 s.
- At DPR 3, B is not feasible in Firefox.

This is analysis, not prototyped.

**Cost.**

- On days it is not needed: one refinement per evening, against today's 118–480 a day per tab (Q3).
- Saving: the share of steady-state work done while day-suppressed, about 46 % in the model.

**Risks.**

- A reveal before the result, for example when the lead was misjudged or the job was slower than measured. The
  reveal depends on solar elevation only (`moonShow = clamp(darkness·1.8)`, `darkness = clamp(−(e+3)/9)`,
  index.html L3237, L3243), so its instant is predictable. The preview and initial tiers cover a late result, as
  they do today on a fresh tab.
- Gate D is unaffected: the initial tier still presents at reveal.
- It changes R0033 DG-4's frozen scheduling: owner decision 2.

### 4C. Display-referred stopping (measured margin only; the rule is NOT changed)

Per-step results against the final result. **Scope:**

- the metric is a surface-only proxy;
- Chromium covers four phases (G, C, H, F), and Firefox and WebKit only G, with identical step bytes;
- full-Moon (α ≈ 0.09) and near-new phases, where the dark limb and Earthshine dominate, were not measured;
- the device compositor (exposure, sky gas, opacity, cloud) was not measured.

Sources: `evidence/determinism.json` `steps` and `evidence/supplement.json`. Metrics, each taken as the maximum over
all disc pixels, limb and terminator included:

- the published 300-px texture, premultiplied (as displayed over black);
- `projectSurfaceCodes` at the real disc size: 108 px at DPR 1, 216 px at DPR 2. This is the product's own
  box-filter display projection (`moon-detail.mjs` L142-149), used as a proxy for the device-resolution compositor.

| Step (samples) | Chromium time to end of step (G/C/H/F, s) | Projected 108 px: max code / px with a rounded change | Projected 216 px: max / px | 300-px texture, premultiplied: max / px |
|---|---|---|---|---|
| 64 (preview) | 2.7–3.3 | 0.44–1.16 / 44–253 | 1.4–4.35 / 162–1,074 | 3–8 / 262–1,930 (straight) |
| 256 | 7.0–8.8 | 0.12–0.26 / 11–26 | 0.32–1.00 / 51–80 | 1–2 / 96–135 |
| 1,024 | 16.4–28.6 | 0.06–0.11 / 4–7 | 0.15–0.25 / 13–28 | 1 / 25–37 |
| 4,096 (final) | 23.0–35.4 | 0 | 0 | 0 |

**Reading (F).**

- At DPR 1, everything after the 256-sample step changes the displayed disc by at most 0.26 code in at most 26
  pixels. That is 67–75 % of the refinement time (Chromium; for G, everything after 8.8 of 35.4 s).
- At DPR 2, the 256 step is still up to 1.0 code. The 1,024 step is within 0.25 code, and only the final 4,096 step
  (2.7–7.6 s, 10–25 %) is below a quarter code.
- The 1,024 step is the longest step (8.8–20.5 s in Chromium, 88–100 s in Firefox) although it touches only
  2,266–5,720 receivers. Those are the terminator and ambiguous receivers. The rows are contiguous per shard
  (pool L50), so this step is plausibly shard-imbalanced, as the advisory suggested (H; per-shard times were not
  recorded per step).

**Risks to fidelity.** The residual changes sit on the terminator and on Earthshine-lit relief, exactly where gate D
and the PBR judgement look. 0.5 code is below one display code, but the criterion has not been judged visually
(screenshots override metrics). Stopping earlier would also change the `empirical-adaptive` label, which the host
requires (native L266).

**Status.** Measured margin only; no recommendation either way. Any use would amend R0033's accepted limits and the
ISM-MOON-012 rule, which is an owner decision.

### 4D. Combinations

| Combination | Time to refined Moon | Worker CPU (steady state, one tab) | New risks | Owner decisions |
|---|---|---|---|---|
| B alone (day deferral + dusk lead) | unchanged at night; ready at dusk if the lead holds | − about 46 % | dusk race | 2 |
| A in memory only (survives hide/show) | ~0 after a hide within the cell | small (hide/show repeats only) | admission across `clear()` | 1 (+ ISM-MOON-019 change) |
| A across tabs | ~0 for a second tab or a reload in the cell | ÷N with N tabs | store failure modes, first cross-tab store | 1, 3 |
| A + B | as A | − about 46 % and ÷N | union | 1, 2, 3 |
| C (any) | − 67–75 % (DPR 1) / − 10–25 % (DPR 2) of compute time | same fraction | terminator fidelity, quality label | 5 |
| Fix of the wrong-way leading edge (section 3.4) | removes the storm | removes about 77 extra jobs and main-thread initial renders a month (this location) | none to fidelity | 4 |

## 5. Q5 — What must not change without explicit owner authority, and what a work order would own

### 5.1 Must not change without explicit owner authority

- The refinement stopping rule: `moon/src/moon-quality.mjs` L27-45 (rules 64/256/1,024/4,096/8,192; receiver
  threshold 0.125 code; projected gate 0.5 code from step 3), and the host's `empirical-adaptive` admission
  (`moon-native.mjs` L266). Candidate C changes it.
- The scene definition and its currentness bound: `nativeCalendarMoonScene` (precision L22-27), the 0.0416
  device-pixel budget (`PHASE_POSITION_BUDGET`, precision L9) and its read-time check `matches()` (native L66), which is
  checked again at every publication and read. Candidate A changes the scene definition.
- R0033 DG-1…DG-5 as recorded in `docs/state-contracts/R0033.md` L13-17: the DG-1 = B construction-failure state;
  the DG-2 recovery budget (three automatic attempts at 30 s / 2 min / 10 min per page lifetime, not restored by
  success); DG-3 cache modes (`force-cache` on the first boot, `no-cache` after a failure); DG-4 "no new budget;
  keep accepted limits, measure"; DG-5 documentation of the `simMoon*` limit. Candidates A and B both alter what
  DG-4 froze.
- The ISM-MOON-003 transaction (accepted / pending / waitingPreview; result validation at native L242-266) and the
  rule that only a worker `result` with `empirical-adaptive` quality becomes a refined surface.
- ISM-MOON-019 truth-first withdrawal (hidden → `clear`): no refined surface survives a hide. An in-tab memo that
  re-admits after a hide changes it.
- ISM-MOON-005: the initial head is a one-shot lease, not a cache, and is revoked irreversibly.
- `moon/src/moon-detail.mjs` stays byte-identical (pinned initial-receiver source; R0021 10.11). R0022 approved
  exactly one material-projection cache there (`docs/real-sky/LUNAR_DISPLAY.md` "Bounded Moon projection reuse").
- R0021 accepted boundaries: no kernel recompile and no global scheduler in that increment
  (`docs/state-contracts/R0021.md` L16-30), the worker source pin, `vendor/real-sky` immutability and the CSP. A
  cross-engine determinism fix (moving the `Math` imports into the WASM module) would be a kernel recompile.
- Gate D: an opaque Moon every night and an ashen calendar disc. A store hit must never present a disc that is
  not current (the bound above), and a store failure must never leave the slot empty.
- R0036: diagnostics write no storage. No diagnostic may populate or read a Moon store.
- Privacy: no store exists today. The first one must hold no location-derived quantity in its key or value.

### 5.2 What a work order would have to own

- **Wrong-way leading edge (defect, independent of reuse).** Choose the leading-edge direction from the actual
  direction of the native phase angle, not from the χ-sign waxing flag, or make the bound symmetric while the two
  disagree. Keep `waxing` (the rendered bright-limb side) unchanged. Witnesses: the 25 intervals in
  `evidence/waxing-mismatch-365d.json`, the live window cell in `evidence/live.json`, all three engines. Registry:
  ISM-MOON-003 and ISM-MOON-012 rows.
- **Day deferral and dusk lead (B).** New explicit states (`deferred-day` → `armed` → `refining` → `current`), the
  lead-time rule, a guard for the reveal race, and an interaction table with R0033 recovery: a deferral is not a
  failure and does not spend the budget. Evidence: a refined Moon at the reveal frame in at least 19 of 20 dusk
  runs per engine, no frame without a disc, and CPU traces by day.
- **Canonical grid plus reuse (A).** The grid definition and its proof that the bound still holds. A new registry
  entry for refined-result store admission (states: miss / reading / verified / admitted / rejected-corrupt /
  unavailable). The key composition and its privacy test. The integrity check (SHA-256 of the stored bytes against
  the record). Version invalidation, eviction to at most two entries per key class, and cross-tab write races
  (last-writer-wins on identical bytes is safe; partial writes must be invisible). A cache read must never touch
  `recovery`, `bootCache` or `retryCount`. Evidence: byte equality of cached and fresh results for 20 cells, the
  failure matrix (opaque origin, quota, private mode, corruption, new deploy), and time-to-refined on a hit
  (n ≥ 10 per engine).
- **Display-referred stopping (C)**, if ever pursued: an amendment of the accepted rule with its own criterion per
  phase × DPR 1/2/3 × engine, including the terminator and Earthshine regions.

## 6. Facts, hypotheses, unknowns

**Facts (F)**

- F1. The refined scene has a fixed raster, camera, Earth vector and extent. Its only varying input is the Sun
  direction, set by α and the waxing flag (precision L22-27).
- F2. With an advancing clock, α is continuous: the native phase plus a leading edge of `2·0.0416/D_max`. With a
  frozen clock it is snapped to a grid of `4·0.0416/max(104,D)` (precision L14-25).
- F3. `D` (109 at DPR 1, measured) and `D_max` depend on DPR and on the observer's Moon altitude `up`
  (native L39-40; index.html L2296-2297, L4697).
- F4. Refined bytes were identical across repeat, tab, process, concurrency, shard count and DPR in Chromium, and
  across Chromium 148, Firefox 150 and WebKit 26.4 for two scenes (22 G runs in all), although the engines' `Math`
  functions differ.
- F5. A refined entry is 8,884,800 B raw (2,317,137 B gzip-9 without calendarLinear), independent of DPR.
- F6. Refinement runs by day and below the horizon. There is no gate in `poll()` (native L166-187), and the live
  day run made 3 refinements in 5 min at `timeScale=4`. Re-render timing follows the minute-stepped native phase
  (live: every 8 simulated minutes at D = 109, as modelled).
- F7. In the product's own ephemeris, the waxing flag and the direction of α disagree 25 times a year, for 0.7–261
  minutes each, 49 hours in total (`evidence/waxing-mismatch-365d.json`).
- F8. IndexedDB and the Cache API hold a refined-size entry intact in all three engines. OPFS is missing in the
  tested WebKit build. Opaque origins refuse all three.
- F10. Live: inside the 24 Nov interval the refined record expired at every native minute step (5 jobs in 4 min, against 1 in the control). In Firefox at DPR 2, real time, a 139 s job outlived the ≈125 s window and the preview tier was shown for 18 s.
- F9. Every step after the 256-sample step changes the projected display at 108 px by ≤ 0.26 code. At 216 px the
  same holds for the steps after 1,024 samples, at ≤ 0.25 code.

**Hypotheses (H)**

- H1. Identical cross-engine bytes come from the float32 and 8-bit publication absorbing last-bit `Math`
  differences. This is not proven, and other scenes or engine versions could differ.
- H2. Within one engine version, results are identical across machines (fdlibm-style software `Math` in V8 and
  SpiderMonkey; IEEE WASM). Not tested.
- H3. The 1,024-sample step is shard-imbalanced, because its terminator receivers are concentrated in a few
  contiguous rows.
- H4. The worker CPU per refinement is below 4 × wall time, because sparse steps leave shards idle. The CPU figures
  here are upper bounds.
- H5. In the TablissNG extension embed, a store would be partitioned by the extension's top-level site.

**Unknowns (U)**

- U1. Real Safari, real Chrome or Edge profiles, low-core machines, and throttled CPUs.
- U2. Whether a refined → initial tier swap inside a wrong-way interval is visible: it is about the size of
  R0033 F-2, but no clip was taken.
- U3. Measured CPU traces. R33-19 (the M5 record) is still open.
- U4. Store behaviour in private windows, under quota pressure, under eviction during a read, and in real extension
  embeds.
- U5. The cause of the Firefox and WebKit refinement times measured here (153 s / 46 s) being longer than the
  startup advisory's (108–123 s / 30–36 s).

## 7. Isolation and reproduction

- Helper: `harness/iso.cjs`, which is `docs/audit/startup-advisory-20261115/harness/iso.cjs` at `2e9a6159` plus one
  `deviceScaleFactor` option. The layers are unchanged: a loopback-only proxy with no forwarding code; Chromium
  host-resolver rules mapping every non-loopback host to NOTFOUND; a context `**/*` route installed before any
  navigation and never removed; an in-page provider shim; and `finish()`, which throws if any non-loopback request
  was allowed.
- Totals (`evidence/isolation-totals.json`): 14 environments, 597 records, **0 allowed**. The 25 external records
  are several layers' records of the same few requests; there were two distinct external hosts
  (`fonts.googleapis.com`, `aus5.mozilla.org`), and both were refused.
- Publication: `docs/audit/` is not in the `_config.yml` Pages exclusion list (R002B). This tree would be published
  with the site unless the owner excludes it, as would the startup-advisory tree. That is a repository convention
  question.
- Errata: `evidence/determinism-analysis.json` `entrySize.note` cites `moon-precision.mjs L67`. The correct
  locator is L26. The generated file is left unedited.
- Firefox recorded no Playwright route decisions in these runs. Its catch-all was the proxy (all requests reached
  it as `proxy-loopback`, and `aus5.mozilla.org` and `fonts.googleapis.com` were refused there). This deviation is
  recorded, not hidden.
- No packet capture was taken, so non-HTTP escape is untested (as in the startup advisory).

Reproduction, from `harness/`, with `PLAYWRIGHT_PKG` set to the global Playwright package and `TMP`/`TEMP` under
scratch:

```text
node determinism.cjs <repoRoot> <out.json> <bytesDir> chromium,firefox,webkit   # ~25 min
node supplement.cjs  <repoRoot> <out.json>                                       # ~2 min
node analyse.cjs     <repoRoot> <determinism.json> <bytesDir> <out.json>
node storage.cjs     <repoRoot> <out.json> 8884800
node live.cjs        <repoRoot> <out.json> chromium 1 480 "&simTime=22:00&timeScale=4" <label>
node live.cjs        <repoRoot> <out.json> chromium 1 240 "" <label> 2026-11-24T16:30:00Z  # mismatch window
node cadence-sim.cjs <repoRoot> 2026-11-16T00:00:00Z 30 '<durations json>' <out.json>
node waxing-mismatch.cjs <repoRoot> 2026-11-16T00:00:00Z 365 <out.json>
```

The exported surface bytes (`bytesDir`, about 21 MB) were scratch-only and are deleted. `determinism-analysis.json`
keeps their comparison. The machine was one 16-logical-core Windows 11 host, headless, with no throttling.
