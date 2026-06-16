# HANDOFF — salah_widget

Context for a fresh agent picking up this repo. The durable design/process docs already exist — read those first
and don't expect this file to repeat them.

## Read these first (do not duplicate)

- `DESIGN.md` — architecture, layout invariants, arc/dawn semantics, atmosphere/sun/moon/cloud/star systems, the
  weather-truthfulness policy, all URL/debug params, known approximations, QA matrix.
- `AGENTS.md` — how to work here: review process, PASS/FAIL gates, **"screenshots override metrics"**, forbidden
  regressions, **commit policy (do not commit unless explicitly asked)**, and run/debug recipes.
- Auto-memory: `C:\Users\theis\.claude\projects\C--workspace-ai-salah-widget\memory\` — `MEMORY.md` index +
  `background-overhaul-progress.md` (a turn-by-turn log of the whole overhaul; the newest entries are this work).
- Git history is the source of truth for *what changed*. Latest commits on `main`:
  - `6bde513` — weather truthfulness + cloud continuity + false/true dawn + optics suite + arc/header fixes + docs.
  - `1dcda23` — living-atmosphere renderer overhaul + liquid-glass header + arc fixes.
  Use `git log -p` / `git show <hash>` for detail rather than re-deriving it.

## Project shape

One self-contained `C:\workspace\ai\salah_widget\index.html` (≈1700 lines: all CSS + JS + the atmospheric
renderer inline). `builder.html` is a config/URL generator. **Deploys via GitHub Pages from `main`**, so a commit
to `main` is a deploy — that's the user's established workflow. Repo: github.com/theislampill/salah_widget.
Data: Aladhan (prayer times) + Open-Meteo (weather) — both keyless/CORS-safe, no secrets in the repo.

## Working state

The live-motion + photometric + moon/dawn/buckle pass is **committed** as `91d0fc1` on `main` (live on Pages).
A **newer UNCOMMITTED pass** (2026-06-16) is in the working tree, in two waves. **Round-1 impl:** shared
`solarElevationDeg` helper, sun tone-map lifted into `atmosphere`, day-rollover robustness, reduced-motion unified,
overcast leaden deck, moonSky-ordering guard, `?debugOptic=lunarhalo`, the moon-upright/anti-spin fix. **Round-2 impl:**
dead-code removal (`moonParallactic` + unused `chi`), a quiet worded day-rollover "stale" cue, `applyCloudState()`
extracted from `paint`, debugMotion telemetry extracted from `boot`, **true radar** (RainViewer, confirm-only +
fail-closed, via `fetchRadar`/`gateWeatherCode(raw,w,radarMm)`), +9 smokes (**`tests/smoke.html` now 40/40**).
Deferred by decision: moon hemisphere (upright N-only) + false-dawn (unbuilt). Radar precip: researched, wiring
gated on a source decision. Touched: `index.html`, `DESIGN.md`, `ARCHITECTURE.md`, `OPTICS.md`, `HANDOFF.md`,
`tests/smoke.html`, `plans/` (+ `plans/round-2/`). Three stray scratch files
(`_mag_extract.txt`, `noaa_clouds.html`, `workspaceaisalah_widget_photopills.html`) remain untracked and must
**never** be committed. **Do not commit unless the user explicitly asks** (a commit to `main` deploys to Pages).

What changed in the (committed `91d0fc1`) live-motion pass (all verified live in preview, no console throws):
- **Live motion (headline):** cloud advection/lifecycle were ~100× too slow (≈4 px/min → read as a frozen
  wallpaper while the `qaState` hash "changed" every frame). Now ≈70 screen-px/min at moderate wind + visible
  morph. Added `?debugMotion=1` telemetry overlay and `?motion=full` (honest override of OS reduced-motion).
- **Sun:** scene-referred **tone-mapping** (Kasten–Young airmass + Beer–Lambert + per-class cloud transmittance +
  CCT blackbody + ACES) — fixes the grey/purple blob; **defined white nucleus + warm-gold body edge** (restored
  after a tone-map regression that greyed the disc); sunrise enters low-left; **optics register to the VISIBLE
  corner sun** (`--sunvx/--sunvy`) — fixes the center-screen halo FAIL.
- **Moon:** now **OPAQUE** (`moonShow` = one night opacity for disc + occluder; no stars through); **physical vs
  calendar** split (calendar disc shows the phase at night even below-horizon/new, but **moonbeam is physical-
  only — no faked light**); **mostly in-frame** (pocket below temp strap / above the arc) so the phase reads;
  ~+13% bigger. `qaState().moonTruth` added.
- **Dawn:** **removed both painted overlays** (fail-closed). True dawn = the real physical twilight sky + Fajr
  marker; **false dawn is NOT rendered** (an unmodeled CSS cone read as a lens-flare slash and showed under a
  bright moon). `debugDawn` is a deprecated no-op; a faithful zodiacal cue is future work only.
- **Header buckle:** strap inner ends **masked** (circular cut-out) so no strap shows through the translucent
  buckle (z-index alone can't — translucent glass reveals what's under it).

## Dev / verify loop (how this work was actually done)

- A static dev server runs via the preview MCP (`.claude/launch.json`, name `static`, port 5577). Drive it with
  `mcp__Claude_Preview__preview_*` (load via ToolSearch). Navigate by setting `location.href` to a hash URL then
  `location.reload()`; wait ~2.5–4 s (the Aladhan fetch can briefly show "Loading…", retry if so).
- Force scenes with the sim/debug params documented in DESIGN.md (`simTime`, `simWx`, `simPrecip`, `simMoon…`,
  `timeScale`, `debugDawn`, `debugOptic`, `qa=1` → `window.qaState()`).
- **Verify with pixels + `qaState`, not assumptions.** Independent skeptic subagents (general-purpose, given the
  serverId, driving the preview and screenshotting) were used as judges; they share the one preview server so
  they must run **sequentially**.

## Gotchas learned the hard way (these will bite you)

- The preview **`preview_console_logs` tool repeatedly reported "No console logs" even when JS was throwing.** To
  catch a silent breakage, eval `(()=>{try{atmosphere(model());return 'ok'}catch(e){return e.message}})()`. A
  thrown `atmosphere()` shows up as `qaState().sunEl === 0` and a sky stuck dark at midday.
- **`atmosphere()` has strict lexical ordering (TDZ).** Cloud layers (`let clLow,clMid,clHigh`), `ray`,
  `cloudSunCol`, `moonLume` are declared partway down. New code that uses them must be placed *after* their
  declarations or you get "Cannot access 'X' before initialization" (this exact bug was hit + fixed).
- **`simTime` without `timeScale` sets TIMESCALE=0 → the clock is frozen**, so cloud drift/animation won't show
  in a still test. Use real-time, a `timeScale` value, or a direct `paintClouds(t1)` vs `paintClouds(t2)` probe.
- The preview browser sometimes reports `prefers-reduced-motion: reduce`, which **freezes the cloud canvas at a
  fixed time** — another reason a still can look static. Check `matchMedia(...).matches`.
- The preview **viewport occasionally zooms** mid-session; reset with `preview_resize` to ~390×600 to see the
  whole 325×530 card.
- **The `qaState().clouds.hash` is a TRAP for "is it moving?"** It is position-weighted and flips on sub-pixel
  change, so it changes every frame even when the sky is visually frozen — this caused repeated false PASS reports.
  **Prove motion only with a real 15–60s watch / `?debugMotion=1` 10s–60s Δ / a centroid-drift probe**, never the
  hash. (The user treats their live observation as ground truth over any metric — rightly.)
- **Moon orientation:** the disc is now **upright** (no rotation) — `renderMoonPBR(frac, waxing)` bakes the lit
  side (right=waxing, left=waning) with the maria fixed, so `.mfeatures` has **no `transform`** and the moon never
  spins (it previously rotated to the parallactic bright-limb angle `χ−q`, which read as the moon spinning over
  time + mismatching the footer emoji — removed). `.moccluder` is still the clean un-rotated circle for disc
  geometry. The lit side **must** match the footer phase emoji (waxing→right, waning→left) — smoke-guarded.
- **The Moon is OPAQUE.** Never make it "subtle" by lowering `--moongrp`/group opacity — that makes stars show
  through (a hologram). Subtlety for a calendar/new moon = a *dark ashen* disc at full opacity; dimness lives in the
  PBR render + (the absence of) moonlight, never in transparency.
- `paint(A)` is the only DOM writer; top-level `let`/`const` in the page ARE reachable from `preview_eval`
  (global lexical env), which is how the live probes above work.

## Known residuals / candidate next work (honest, from the judge panels)

- **Overcast leaden deck:** addressed 2026-06-16 — neutral-grey + stronger `WX.overcast` sky tint, darker overcast
  `cloudBase`, and a high-coverage puff-opacity fill (all overcast/coverage-gated; broken & clear unchanged, motion
  preserved, moon opaque). Overcast now reads as a leaden ceiling; final aesthetic dial is the maintainer's eye.
- **False dawn (zodiacal light) — future work, currently NOT rendered.** A faithful cue needs real ecliptic-tilt
  projection + strict dark-sky/no-moon/low-light-pollution/clear gating + very faint opacity + no foreground-
  crossing streak + must never imply Fajr. Until all hold, it stays unbuilt (fail-closed). True dawn is the
  physical twilight sky — do not re-add a painted band.
- **Optics are art-directed approximations, not photometric** — but they now **register to the visible corner
  sun** (`--sunvx/--sunvy`), so the old "halo center-screen" bug is fixed. The moon's halo/paraselenae may still
  show as partial arcs (halo radius > the disc). Sun tone-mapping constants are tuned, not radiometric.
- Weather precip evidence is Open-Meteo's **nowcast, not true radar** (documented limitation). If a CORS-safe
  radar/nowcast precip source is found, wiring it into `gateWeatherCode` would make the gate ground-truth.

## Do NOT reintroduce (the user has explicitly rejected these)

- A **painted true-dawn horizontal band** or a **false-dawn diagonal cone/slash** — dawn is the physical sky; false
  dawn is fail-closed. (The user called painted dawn "strips" illegitimate, then "gross/inaccurate".)
- A **transparent moon** (stars through the disc). The Moon is opaque; never lower group opacity to make it subtle.
- A **moonless / empty-slot normal night** or a "new moon invisible" rule. New moon = a faint **opaque** ashen
  calendar disc.
- A **z-index-only** buckle fix (translucent glass still shows the strap) — keep the mask cut-out.
- Claiming live motion from `qaState().clouds.hash`. Use a real watch / `debugMotion` Δ.
- A **grey/purple sun blob** or a sun with no defined nucleus.

## Suggested skills

- **`superpowers:brainstorming`** — before any new feature/large change, to pin down scope (this project's tasks
  arrive as big multi-part prompts; clarifying first prevents shallow passes).
- **`anthropic-skills:ui-ux-pro-max`** — for any header/belt/arc/list layout or readability change (the layout
  invariants are strict; see AGENTS.md "forbidden regressions").
- **`deep-research`** (Workflow) — for any further physical-phenomenon work; the prior passes used it to get gated
  recipes before coding, and the reports are referenced from the memory log.
- **`superpowers:debugging`** — if something renders wrong; remember the silent-throw gotcha above (use the
  try/catch eval) rather than trusting the console tool.
- Reach for the **Workflow / multi-judge** pattern (sequential preview-driving judges) when verifying visual/
  physics changes, per AGENTS.md — and only commit when explicitly asked.
