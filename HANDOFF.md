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

Clean. Working tree has only untracked files: `HANDOFF.md` (this), and three stray research scratch files
(`_mag_extract.txt`, `noaa_clouds.html`, `workspaceaisalah_widget_photopills.html`) that must **never** be
committed. Everything intended is committed + pushed.

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
- `paint(A)` is the only DOM writer; top-level `let`/`const` in the page ARE reachable from `preview_eval`
  (global lexical env), which is how the live probes above work.

## Known residuals / candidate next work (honest, from the judge panels)

- **Clouds** are believable stacked-puff cumulus but edges read soft/painterly, and **overcast reads hazy rather
  than a heavy leaden ceiling**. Crisper cumulus + a denser overcast deck is the most-flagged remaining item.
- **Optics are art-directed approximations, not photometric.** The solar halo/sundogs/pillar attach to the
  *arc-sun* screen position (the established `.godray` convention), so they coexist with the separate top-left
  corner-sun body; the moon's halo/paraselenae render as partial arcs/spots (the moon is corner-clipped); the
  parhelic-circle band looks a touch broad at the forced debug max (fainter under real cirrus gating). None were
  run through a full 5-judge skeptic panel — that's the verification gap to close before calling them "done".
- Header buckle currently holds the **weather icon**; a phase-accurate moon glyph was noted earlier as a cosmetic
  wish, not done.
- Weather precip evidence is Open-Meteo's **nowcast, not true radar** (documented limitation). If a CORS-safe
  radar/nowcast precip source is found, wiring it into `gateWeatherCode` would make the gate ground-truth.

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
