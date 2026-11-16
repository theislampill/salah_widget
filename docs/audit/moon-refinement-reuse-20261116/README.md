DRAFT — Q1 section staged; front section and measured sections follow.

## Q1. Complete input identity of the refined Moon result

Source identity: `main` 47faae32 (`moon/BUILD.json`: worker `e6d3f732…`, kernel `4fcf7888…`, asset manifest
`3d4cb527…`). Line numbers are of the authored sources at that commit.

### How the refined scene is built

`poll()` (`moon/src/moon-native.mjs` L166-187) calls `scene(s)` (L104-107) = `nativeCalendarMoonScene(s,profile())`
(`moon/src/moon-precision.mjs` L63-68). That scene has a fixed raster and camera — `size:540`, `outSize:300`,
`diameter:288`, `basis:[0,1,0,0,0,1,1,0,0]`, `earth:[384400,0,0]`, `distance:384400`, `extent:1.08`, `tilt:0` —
and exactly one varying physical quantity, the Sun direction `[cos α, ±sin α, 0]`, where:

- **advancing clock** (`timeScale>0`, every normal live tab): `α = acos(2f−1) ∓ 2·0.0416/D_max·(1−1e−9)`, i.e. the
  *continuous* native phase angle shifted to a leading edge. **It is not quantised.**
- **frozen clock** (`timeScale==0`, i.e. `simTime` without `timeScale`, QA scenes): `α = acos(2·f_c−1)` with
  `f_c = canonicalFraction(f, D)` (L55-60), the nearest point of a grid of spacing `4·0.0416/max(104,D)` rad.

`D` = `ceil(max(rect.w, rect.h)·dpr)` of `.mphoto` (L39), `D_max = ceil(D·max(1, maximumPresentationRatio))`
(L40), `maximumPresentationRatio = 1.13/(1.11+0.02·up)` (`src/native/index.html` L4697), `up = clamp((alt+2)/6)`
of the observer's Moon altitude (L2296). `f` = `moonSky.frac` from `moonIllum(date)` (geocentric; L2072-2077),
`moonPhase(date)` (mean synodic) when lat/lon are not finite, or `simMoon` (L2289-2292).

### Dependency table

| Input | Enters the refined SURFACE bytes? | Path (file:line at 47faae32) |
|---|---|---|
| Phase angle α (UTC → geocentric ephemeris) | **Yes**, continuously (advancing clock) | precision L64-66; index.html L2072-2077 |
| Phase quantisation | **Only in the frozen clock** (grid 4·0.0416/max(104,D) rad); advancing clock uses a continuous leading edge | precision L49-60, L65 |
| Waxing flag | Yes (sign of Sun y; also in `scope`) | precision L67; native L47 |
| Phase source (ephemeris vs mean synodic vs `simMoon`) | Yes (different `f` for the same instant) | index.html L2289-2292 |
| Libration, Earth distance | **No**: basis and Earth vector fixed (mean-libration calendar Moon) | precision L67 |
| Position angle / parallactic rotation | **No** (`tilt:0`, upright Moon) | precision L67; index.html L2077 comment |
| Observer lat/lon, height | **Not directly** (`f` is geocentric). **Indirectly yes**: Moon altitude → `up` → `D` (group scale 1.11…1.13) and `D_max` → leading-edge offset of α; frozen clock: `D` → grid | native L39-40; index.html L2296-2297, L4697 |
| `simMoon`, `simWax` | Yes (via `f`, waxing) | index.html L2290 |
| `simMoonAlt`, `simMoonH` | Indirectly (via `up` → `D`, `D_max`) | index.html L2294 |
| DPR | Only through `D` (and so α); the raster is DPR-independent (540/300/288) | native L39; precision L67 |
| On-screen disc size / canvas size | Only through `D`; output canvas fixed 300×300 | native L12, L39 |
| Scene metadata `phaseQuantumRadians`, `phaseDisplayDiameter`, `requestedNativeFraction`, `geometryConvention` | No pixel effect; they are in the scene JSON, which the host compares for result admission | precision L67; native L247 |
| DEM / colour assets | Yes; digests in `manifestIdentity` → `physicalIdentity` | engine L41, L50, L73, L117 |
| WASM kernel | Yes; `manifest.wasm.sha256` in `manifestIdentity` | engine L66, L73 |
| JS surface code (V5 tone map, pool join/filter, calendar proxy, sRGB encode) | Yes; **not** in `physicalIdentity` (only in the worker source digest) | surface_v5; pool L193-205; calendar L8-41 |
| Profile (calendar / reference) | Yes (`profileIdentity`; `profileMode` in `scope`) | native L29, L47; surface_v5 L69 |
| Quadrature rule / stopping rule | Yes (part of the worker source); the final `physicalIdentity` records the last step's rule | quality L77-113; engine L117 |
| Worker count / shard layout | Fixed at 4 in product; measured below (2 vs 4) | pool L143, L151, L164 |
| Tier | initial (main-thread receiver), preview (64-sample step), refined (`result`) are different bytes | native L114; quality L101 |
| Earthshine | Yes, but fixed geometry for a given α (Earth vector constant) | engine L110 |
| Calendar / below-horizon proxy | Its *bytes* (`calendarLinear`, `calendarRgba`) are a pure function of the result + material; its *blend weight* `up` is applied afterwards | calendar L8-41; native L50-60 |
| Display mapping after the surface (device-resolution projection, sky gas, cloud, opacity, exposure, placement) | No — applied downstream by `moon-detail.mjs` and the native compositor | detail L43-141 |
| Time of day / day suppression | **No effect on bytes, and no effect on scheduling**: `poll()` has no day or horizon gate | native L166-187; index.html L3235-3243 |
| Browser engine (JS `Math` passed to WASM as imports; JS-side `**`, `expm1`, `acos`) | Measured in Q2 | engine L67; kernel L9-12; surface_v5 L15, L32 |
| Host scope (generation, sceneIdentity incl. lat/lon/tz/clock anchor, dpr, profile) | Not in the bytes; in `scope`/`key`, which fence admission | native L43, L47, L65 |
