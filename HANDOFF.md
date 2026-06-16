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
- Git history is the source of truth for *what changed*. Latest commits on `main` (HEAD `37084ae` + the install/
  builder pass committed on top of it):
  - `37084ae` — local self-configuring mode (`#local=1`) + shared `config.js` + in-widget settings + TablissNG wizard.
  - `90928c8` — true radar (RainViewer) confirm-only precip evidence for the weather gate.
  - `a10af5c` — living-sky round 2 (solar/lunar correctness, day-rollover truth, SRP extractions, smokes).
  - `91d0fc1` — living-sky rescue + architecture/optics hardening, observability & smokes.
  Use `git log -p` / `git show <hash>` for detail rather than re-deriving it.

## Project shape

`C:\workspace\ai\salah_widget\index.html` (≈2100 lines: all CSS + JS + the atmospheric renderer inline) +
**`config.js`** — the one shared module (`window.SalahConfig`: parse/validate/serialize/load-save-local/
coarse-detect), loaded by both `index.html` and `builder.html`. **As of 2026-06-16 the "single self-contained
index.html" invariant is deliberately relaxed** (maintainer decision) to keep config logic un-forkable; `config.js`
is the *only* extracted module and `index.html` falls back to legacy hash parsing if it 404s. `builder.html` is the
config/URL generator (portable + self-configuring snippets). **Deploys via GitHub Pages from `main`**, so a commit
to `main` is a deploy — that's the user's established workflow. Repo: github.com/theislampill/salah_widget.
Data: Aladhan (prayer times) + Open-Meteo (weather) + RainViewer (radar) + GeoJS/ipinfo (coarse IP geolocation,
local mode only) — all keyless/CORS-safe, no secrets in the repo.

## Working state

**All prior work is committed on `main` and live on Pages.** The local self-configuring mode + shared `config.js` +
in-widget settings panel + TablissNG setup wizard shipped as **`37084ae`**; the living-sky / photometric / radar
passes as `91d0fc1`, `a10af5c`, `90928c8`. So `#local=1`/`#preferLocal=1`, the buckle⇄⚙ settings affordance (local
mode only), the in-card settings panel (in-memory `applyConfig`, no reload), coarse IP detect (GeoJS→ipinfo), and
the byte-identical hardcoded-embed path (proven Smoke A/B) are all live. `tests/smoke.html` **61/61**. Privacy:
coarse detect sends the IP to GeoJS/ipinfo (disclosed), precise geolocation is user-gesture-only, saved config
stays local. Plans: `plans/round-3/`. Deferred by decision: moon hemisphere (upright N-only) + false-dawn (unbuilt,
fail-closed); radar precip wiring gated on a source decision.

**Latest pass — install config-carry + builder/embed-size parity** (committed on top of `37084ae`):
- **Install config-carry.** The builder's **Install widget** button copies the OS one-liner and, when the config
  differs from the plain `#local=1` default, prepends `SALAH_WIDGET_HASH='<hash>'`; `install.sh`/`install.ps1` bake
  that hash into the staged preset's iframe (replacing `#local=1`) so an installed widget keeps the builder's
  settings (no re-setup). `install.sh` hit a **bash 5.2 gotcha** — `&` in a `${//}` replacement means "the matched
  text," which mangled the hash's `&` separators; fixed with `shopt -u patsub_replacement` so `&` stays literal
  (PowerShell `.Replace` is literal — fine). Verified: `bash -n` + simulated bake (no leftover `local=1`, JSON
  valid), `install.ps1` parses 0-error, builder copies the right command per mode (portable / local+prefs / plain).
- **Builder card == the *visible* widget.** The widget card (`.c`) is **325×530**, but every iframe wrapper was
  `330×534` — a 5×4px invisible transparent margin — so the builder card (matched to the 534 box) sat 4px below the
  visible widget. Corrected the canonical embed size to **325×530** everywhere (builder preview + copy snippet,
  README ×2, TablissNG preset); the builder card is now `height:530px` (a hard **cap**, not `min-height`) with ~44px
  slack (tighter label margins + note line-height) so it never scrolls. **Install**/**Refresh** share a row (both
  44px; install-row gap = preview gap = 14px). The geo-pin is centered (`padding:0` to drop the inherited `button`
  padding + a square 22×22 svg). Verified in preview: card bottom = visible `.c` bottom (diff 0), buttons delta 0,
  no clipping, no scrollbar. Touched: `builder.html`, `install.sh`, `install.ps1`, `README.md`,
  `presets/salah-widget.tablissng.json` (+ docs). See the **Embed-size invariant** in ARCHITECTURE.md / AGENTS.md.

Three stray scratch files (`_mag_extract.txt`, `noaa_clouds.html`, `workspaceaisalah_widget_photopills.html`)
remain untracked and must **never** be committed. **Do not commit unless the user explicitly asks** (a commit to
`main` deploys to Pages).

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
