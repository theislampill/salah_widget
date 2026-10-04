# HANDOFF — salah_widget

Context for a fresh agent picking up this repo. The durable design/process docs already exist — read those first
and don't expect this file to repeat them.

## Read these first (do not duplicate)

- `DESIGN.md` — architecture, layout invariants, arc/dawn semantics, atmosphere/sun/moon/cloud/star systems, the
  weather-truthfulness policy, all URL/debug params, known approximations, QA matrix.
- `AGENTS.md` — how to work here: review process, PASS/FAIL gates, **"screenshots override metrics"**, forbidden
  regressions, **commit policy (do not commit unless explicitly asked)**, and run/debug recipes.
- [Implementation dossier](docs/rlgwo-implementation-dossier.md) — current 37-row/eight-join disposition,
  bounded public receipts, actual reviewer records and remaining qualification cells.
- Git history is the source of truth for *what changed*. Historical June main records (not the current HEAD
  or public-byte qualification):
  - `37084ae` — local self-configuring mode (`#local=1`) + shared `config.js` + in-widget settings + TablissNG wizard.
  - `90928c8` — true radar (RainViewer) confirm-only precip evidence for the weather gate.
  - `a10af5c` — living-sky round 2 (solar/lunar correctness, day-rollover truth, SRP extractions, smokes).
  - `91d0fc1` — living-sky rescue + architecture/optics hardening, observability & smokes.
  Use `git log -p` / `git show <hash>` for detail rather than re-deriving it.

## Project shape

`index.html` (runtime CSS + JS + atmospheric renderer inline) +
**`config.js`** — the one shared module (`window.SalahConfig`: parse/validate/serialize/load-save-local/
coarse-detect), loaded by both `index.html` and `builder.html`. **As of 2026-06-16 the "single self-contained
index.html" invariant is deliberately relaxed** (maintainer decision) to keep config logic un-forkable; `config.js`
is the *only* extracted module and `index.html` falls back to legacy hash parsing if it 404s. `builder.html` is the
config/URL generator (portable + self-configuring snippets). **Deploys via GitHub Pages from `main`**, so a commit
to `main` is a deploy — that's the user's established workflow. Repo: github.com/theislampill/salah_widget.
Data: Aladhan (prayer times) + Open-Meteo (model weather) + RainViewer (tile diagnostics) + GeoJS/ipinfo
(coarse IP geolocation). README lists actual recipients/fields/triggers. Provider availability and cross-origin
behavior require current checks; no local-observation or retention guarantee follows from this list.

## Working state

**Same-campaign continuation — bounded qualification complete:** All 37 implementations are joined; all 37 work orders and all eight joins are QUALIFIED under their bounded contracts.
Two genuine native hidden→visible cycles now qualify R0025/J07/J08 on unchanged daa42 source; first actual resumed render withdraws expired synthetic rain. Actual offscreen recovery remains accepted separately.
Owner-amended controlled Git Bash35/native WSL installer evidence closes R0013/R0015/R0016/J05 without a Mac or NTFS equivalence claim.
The adopted Solar low-left nucleus and cool weighted Moon floor close bounded R0021/R0022/J06; historical failed/rejected variants remain evidence.
Runtime input is `6695f7451bd5b55a06c3f535b2d4020e56cd300a` / tree `2d990ac6b6d8fc06f085bf8d7d74199930553fa9`; index SHA-256 `4f893b21632ea18ece6b50df849aa5c36df8300047b1b0f44cb10df44b2a6c03`.
Final composed source controls, three native visual documents and two actual-caller cost documents have bounded review/custody/Root association.
The measured joined/cache cost increased in these sequential observations; unequal page ages preclude a causal/efficiency/GPU conclusion.
Read the [implementation dossier](docs/rlgwo-implementation-dossier.md) and [current hidden receipt](docs/evidence/rlgwo/receipts/continuation-native.md#r0025-hidden-native).
Owner preview59948 is the native-verified frozen Sep7 synthetic default-Glass fixture on runtime6695; old56666 and other campaign fixture URLs are historical/retired.
Approved DESIGN spacing/placement and display-only Earthshine wording are already applied by Root; substantive component records below remain historical.
A later docs-only HEAD must separately prove unchanged runtime bytes; final HEAD/tree stamps belong outside the committed tree.
Debug overlay/pre-paint CSS, font acquisition, early pending, clipped/approximate art and historical motion limits remain explicit.
All37 bounded work orders/eight joins are qualified. Owner review uses only the new publication HEAD after exact public readback; owner approval, release readiness, global art/M0, merge/main/deployment and issue comments remain separate.

- **Clock/prayer:** ordinary loads follow `Date.now()`, including backward correction; explicit `timeScale=1`
  is anchored ADVANCING preview. Zoned inverse gaps/folds and unresolved intended endpoints remain unavailable.
  Generation/operation/attempt ownership covers complete response bodies and adoption. Selected cache-zone/day
  discovery, a shared three-attempt budget and sixty-second visible recovery retain usable timings; async
  accepted state marks the existing loop dirty rather than creating another loop.
- **Calendar:** one selected provider-record decision supplies AH, method and status. At Maghrib, matching
  usable tomorrow is required to advance; otherwise Sunset date update unavailable/Hijri date unavailable is
  explicit. Complete footer values/provenance are accessible through the date buttons/dialog. No inferred
  calendar method, persisted hold, offset or anomaly correction is added.
- **Weather:** useful live model estimate/≈ and temperature remain while current source/receipt eligibility
  holds; absent/expired current is unknown and removes current inputs. Selected live adapters cannot establish
  local wet/dry/lightning, nearby or arrival, so strong live effects remain off. `synthetic-present-v1` is a
  separately admitted marked QA lane, with original underlying-observation age, exclusive lease, target
  generation and immediate end/outage/expiry withdrawal. It is not a new provider or public hash setter.
- **Location/settings:** original acquisition timestamp/accuracy and intent stay private; preference saving
  does not renew fix age. Portable output omits acquisition history and denotes a configured site. Refused
  save retains session choices; refused Reset retains selected config. Storage partitioning differs from
  denial. Liquid glass is default; High contrast is opt-in. Both builder modes explicitly carry appearance,
  including glass, and saved preferences precede local/prefer-local defaults. Only the contrast option has the
  4.5:1 white-underlay stress gate; default glass earns no blanket ratio claim.
- **Sky/clouds:** neutral first entry reveals on fresh consumed lunar geometry and matching stellar projection.
  PBR decode/href readiness is separate. Terminal failure has a readable opaque procedural phase with no physical light; it cannot supply decoded terrain. Independent
  stellar masking covers stars/glints/Milky Way through twilight fade. Shared atmospheric lunar eligibility
  disables near-new/zero-horizon-permission/daylight atmospheric light while retaining opaque night-side/Earthshine. Signed cloud population
  survives ordinary day/zone/weather changes; old wind covers preceding monotonic intervals. Empty decks advance,
  hidden/reduced periods hold/rebase, gaps over two seconds discard backlog and explicit seeks start at zero
  displacement. Source controls do not award native first-frame/edge/motion/PBR success.
- **Held scope:** the round-4 adaptive-performance governor remains held. No governor/performance success,
  new provider, painted dawn or extra platform qualification belongs to this update.

**Historical reviewed and joined smoke successor:** `48ba16e80f9715e40728349da8c8c5a26d2e4eaa`, tree
`d19b5b8a664059575615674f9561ed628d59ffd9` has **30 declared groups / 141 assertions**: 19 retained groups,
11 actual-weather groups (66 assertions) and an added monotonic-cloud assertion. Root joined it at
`64fdb1241bb3569c6519e39142cbe9e10a3e5872`; those TEST files are outside this documentation branch's older
base. The subsequent PRAYER fixture join `65952878d16ebc4b5e77e4e689b0937311f99bfb` changes tests only;
the runtime bytes remain the same pre-comment composition. Final native smoke execution was pending at that historical cut. Later source-identical runtime smoke is accepted for R0017: three healthy sentinel runs,30 groups/141 assertions each and17 negative/fault/media controls. See the [current bounded smoke receipt](docs/evidence/rlgwo/receipts/smoke-runtime.json).
The instrument runs automatically on navigation; private
injected stores and preparse wrapper isolation persist. PASS requires the full declaration; assertion/bootstrap
error is FAIL; missing callback/assertions/readiness is INCOMPLETE with declared/executed/missing names. The
wrapper binds run/attempt/UUID/hash/source hash and rejects changed source within a run. On root's disposable
loopback origin, the fixture URL is `/tests/smoke.html?fixture=healthy|reject|hang|bootstrap-error` (choose one).
Its source command is:

```text
node --test --test-concurrency=1 tests/r0017-contract.cjs tests/r0017-transport.cjs tests/r0017-weather.cjs
```

The 55 contained controls (35+14+6) are not the native 30/141 ledger. Frozen/controlled Date and suppressed
fonts earn no normal-entry appearance, default live M0, OS reduced/full or public-safety claim.

**Installer candidate contract:** reviewed local-file invocation, terminal requirements and offline/no-effect
preview are documented in [README](README.md#one-line-install-optional-setup-wizard). The builder's one-liner
still fetches published `main`; a local candidate is not public-byte readback. Bash uses Python literal hash
replacement plus JSON validation, fresh private per-attempt scratch and a retained home bundle. Windows keeps
its TEMP staging path. Keep a Chromium unpacked directory while installed; preset/XPI removal is optional and
manual after the browser step. The accepted native Linux DAC cell records owner UID1000/peer UID65534,
49 probes, actual owner EXIT and a fresh UID1000 retained-file consumer. Retention is qualified through that
consumer in the original run; later native fixture availability is unknown. Native Apple Bash 3.2 and real
browser/public qualification remain open. In particular **Apple Bash 3.2** is unavailable in this environment,
so candidate qualification remains PARTIAL until the required real native checks; source parsing is not that
platform witness.

The following main/Pages and preview entries are historical records, not qualification of this candidate.

**Historical June report: prior work committed on `main` and live on Pages.** The local self-configuring mode + shared `config.js` +
in-widget settings panel + TablissNG setup wizard shipped as **`37084ae`**; the living-sky / photometric / radar
passes as `91d0fc1`, `a10af5c`, `90928c8`. So `#local=1`/`#preferLocal=1`, the buckle⇄⚙ settings affordance (local
mode only), the in-card settings panel (in-memory `applyConfig`, no reload), coarse IP detect (GeoJS→ipinfo), and
the byte-identical hardcoded-embed path (proven Smoke A/B) are all live. `tests/smoke.html` **61/61**. Privacy:
coarse detect sends the IP to GeoJS/ipinfo (disclosed), precise geolocation is user-gesture-only, saved config
stays local. Plans: `plans/round-3/`. Deferred by decision: moon hemisphere (upright N-only) + false-dawn (unbuilt,
fail-closed); radar precip wiring gated on a source decision.

**Historical pass — install config-carry + builder/embed-size parity** (committed on top of `37084ae`):
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

The historical scratch files (`_mag_extract.txt`, `noaa_clouds.html`, `workspaceaisalah_widget_photopills.html`)
must **never** be committed. **Do not commit unless the user explicitly asks** (a commit to
`main` deploys to Pages).

What changed in the (committed `91d0fc1`) live-motion pass (all verified live in preview, no console throws):
- **Live motion (headline):** cloud advection/lifecycle were ~100× too slow (≈4 px/min → read as a frozen
  wallpaper while the `qaState` hash "changed" every frame). Now ≈70 screen-px/min at moderate wind + visible
  morph. Added `&debugMotion=1` telemetry overlay and `&motion=full` (honest override of OS reduced-motion).
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

## Dev / verify loop

- Serve statically on a disposable loopback origin. Verify the actual source/URL and storage isolation before
  instrument navigation; smoke autoruns. Root owns the shared native preview lease. June preview tooling/
  port records below are historical and do not establish tools, origin or source identity for a new run.
- Force scenes with the sim/debug params documented in DESIGN.md (`simTime`, `simWx`, `simPrecip`, `simMoon…`,
  `timeScale`, `debugDawn`, `debugOptic`, `qa=1` → `window.qaState()`).
- **Verify with pixels + `qaState`, not assumptions.** Historical skeptic judges drove one shared preview
  sequentially. Additional agents require explicit approval; source receipts do not become independent native
  visual evidence through repetition.

## Gotchas learned the hard way (these will bite you)

- The preview **`preview_console_logs` tool repeatedly reported "No console logs" even when JS was throwing.** To
  catch a silent breakage, eval `(()=>{try{atmosphere(model());return 'ok'}catch(e){return e.message}})()`. A
  thrown `atmosphere()` shows up as `qaState().sunEl === 0` and a sky stuck dark at midday.
- **`atmosphere()` has strict lexical ordering (TDZ).** Cloud layers (`let clLow,clMid,clHigh`), `ray`,
  `cloudSunCol`, `moonLume` are declared partway down. New code that uses them must be placed *after* their
  declarations or you get "Cannot access 'X' before initialization" (this exact bug was hit + fixed).
- **`simTime` without `timeScale` sets TIMESCALE=0 → the clock-driven scene is frozen.** For cloud motion use
  default wall time or an explicit running preview and actual monotonic elapsed. A changed `paintClouds(t)`
  argument alone is no longer a travel probe; it initializes/reconstructs civil state, not ordinary travel.
- The preview browser sometimes reports `prefers-reduced-motion: reduce`, which **freezes the cloud canvas at a
  fixed time** — another reason a still can look static. Check `matchMedia(...).matches`.
- The preview **viewport occasionally zooms** mid-session; reset with `preview_resize` to ~390×600 to see the
  whole 325×530 card.
- **The `qaState().clouds.hash` is a TRAP for "is it moving?"** It is position-weighted and flips on sub-pixel
  change, so it changes every frame even when the sky is visually frozen — this caused repeated false PASS reports.
  **Prove motion only with a real 15–60s watch / `&debugMotion=1` 10s–60s Δ / a centroid-drift probe**, never the
  hash. (The user treats their live observation as ground truth over any metric — rightly.)
- **Moon orientation:** the disc is now **upright** (no rotation) — `renderMoonPBR(frac, waxing)` bakes the lit
  side (right=waxing, left=waning) with the maria fixed, so `.mfeatures` has **no `transform`** and the moon never
  spins (it previously rotated to the parallactic bright-limb angle `χ−q`, which read as the moon spinning over
  time + mismatching the footer emoji — removed). `.moccluder` is still the clean un-rotated circle for disc
  geometry. The lit side **must** match the footer phase emoji (waxing→right, waning→left) — smoke-guarded.
- **The Moon is OPAQUE.** Calendar/new-moon dimness belongs to PBR night-side/Earthshine, with no atmospheric
  lunar light. The existing twilight group fade is retained; its independent binary stellar cutout prevents
  stars/glints/Milky Way showing through. Do not lower lunar opacity as a substitute for the mask. Terminal
  fallback phase/presence is distinct from decoded terrain and never grants atmospheric moonlight. Native edges and daytime no-hole controls remain required.
- `paint(A)` writes sky CSS/state, with an explicit cloud-state step; prayer/arc/date/moon/stellar DOM has other
  writers. Top-level `let`/`const` in the page ARE reachable from the historical `preview_eval`
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
- Live weather is a **model estimate**, not qualified local precipitation. RainViewer palette/alpha provides
  diagnostics, not calibrated mm or local wet/dry/arrival. Synthetic QA is not provider qualification; any
  future live provider needs a separately authorized/admitted contract. No new provider is in this candidate.

## Do NOT reintroduce (the user has explicitly rejected these)

- A **painted true-dawn horizontal band** or a **false-dawn diagonal cone/slash** — dawn is the physical sky; false
  dawn is fail-closed. (The user called painted dawn "strips" illegitimate, then "gross/inaccurate".)
- A **transparent moon** (stars/glints/Milky Way through the disc). Keep the opaque PBR surface and its independent
  stellar mask through the existing twilight fade; dim surface radiance, not an artificial transparency trick.
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
