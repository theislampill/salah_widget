# salah_widget — AGENTS

How agents (human or AI) should work on this repo. The runtime entry is generated `index.html`; changes are
visual and physics-adjacent, so **review is dominated by looking at rendered pixels**, not by reading metrics.

## CP9 source ownership and qualification

Read `docs/real-sky/INTEGRATION.md` and the retained post-CP9 DAG before changing
this candidate. Edit native UI, prayer/weather, geometry, PBR, Earthshine and
embedded lunar textures in `src/native/index.html`; edit config and builder in
`src/native/`. Integration owners are `real-sky/native-*.mjs` and
`native-host-hooks.js`. Rebuild with `python tools/build_native.py`; never patch
generated root entries, bundles, worker, data, CSS or copied `real-sky/core`. The builder is all-or-nothing on detected failure (nothing is written until every guard passes) and never edits outside its declared generated set, recorded in `GENERATED.json`; run one build per tree at a time (R0029). A build deletes any `.js` file in `moon/file-data/` and any `.mjs` file in `real-sky/core/src/` or `real-sky/core/integration/` that it does not produce, tracked or untracked, so keep no files of your own there.
`vendor/real-sky` retains immutable scientific source and oracle fixtures.
The requested bottom-border fix is authored in `tools/native_core_horizon.py`;
the builder applies that one digest-guarded horizon-predicate correction while
copying the core. Keep its boundary and drift regression tests with the change.
R0027 adds one more, retention-only, digest-guarded core transform:
`tools/native_core_spectral_cache.py` bounds the inner exact-B-V fit cache of
`src/spectral.mjs` (12,000, FIFO); spectral numbers stay bit-identical. It is
not blanket authority and does not widen the horizon exception; see
`docs/state-contracts/R0027.md` and its tests.
Run its builders/tests in a disposable copy. Historical PASS does not qualify
this candidate. The existing gates below remain requirements, not blanket PASS.

The dependent Moon candidate adds authored `moon/src/`, lossless `moon/assets/`
and the supplied `moon/moon_kernel.wasm`. `tools/build_moon.py` runs through the
native builder; never edit its generated host/worker/chunks or expanded entries.
Native phase/time/configuration still belong to `src/native/index.html`; the
device-resolution lunar foreground belongs to `moon/src/moon-detail.mjs`.
Read `docs/moon/QUALIFICATION.md` for this candidate's evidence and limitations.
The CP9 comparison ledger remains PARTIAL/BLOCKED; Moon integration does not
close N001/N002/N003 or authorize merge/deployment.

## Implicit-state registry

`IMPLICIT_STATES.md` is the repository-wide implicit state-machine registry (`ISM-*`; audit: `docs/audit/post-rlgwo/REPORT.md`).
For the installers (`ISM-INST-*`) it records states, guards, invariants, evidence and open findings for staging trust, artifact
admission, cleanup, preview and manual hand-off. Consult it before changing that
behaviour in `install.sh`/`install.ps1` or performing a consequential transition; for any other family, consult the entry naming a mechanism before changing it.
Record materially relevant discoveries there, linking the `docs/state-contracts/`
contracts rather than duplicating them. It grants no execution authority and proves
no runtime behaviour.
Regression evidence is the verdict of `python tools/cp9/run_native_regressions.py --output <new dir>`
over the registered population and the exact expected-failure ledger (`tests/regression-population.json`,
`tests/expected-failures.json`; `docs/state-contracts/R0028.md`), quoted verbatim (for example
`PASS_WITH_DECLARED_FAILURES (n)`), not the node glob alone.
A change that adds, renames or removes an instrument (`tests/*.cjs|js|mjs|py`, `tests/**/*.test.cjs|.test.mjs|_test.py`,
`moon/tests/*`, `tools/**/test_*.py`) edits `tests/regression-population.json` in the same commit: a new or renamed
`tests/*.test.cjs` goes in `nativeTestGlob`; any other instrument gets a `commands` entry (argv, protocol, inputs, covers),
a `modules` entry (imported helper) or an `exclusions` entry (reason, owner; native recipes also record `recipe`
argv and protocol). Removed instruments are deleted there, with any ledger entry in `tests/expected-failures.json`.
Verify with `python tools/cp9/run_native_regressions.py --output <new dir> --select native-runner-contract`: the
census always covers the whole tree, and any `setupErrors` (unregistered or missing instrument) make it INCOMPLETE.

## Golden rules

- **Screenshots override metrics.** A passing `qaState()` number does not pass a cycle if the screenshot looks
  wrong. Every visual claim needs a crop/clip.
- **Truthfulness over drama.** Never make the widget claim a condition it can't support (see "Weather" below).
- **Do not commit unless explicitly asked.** When asked, `main` is the GitHub Pages deploy branch.
- **No broad refactors mixed into a feature/fix.** Keep diffs inspectable. Document before refactoring.
- **Physics gates the art.** Optical phenomena must be condition-gated (ice vs droplet, low-sun + broken cloud,
  humidity, etc.), never random or always-on.

## Atmospheric coherence and perceptual fidelity (owner design standard)

Owner design standard, 2026-11-15. It adds to every work order's own acceptance rows; it does not replace them.
It is an affirmative design, research and improvement objective, not only a stricter review threshold.

- **First-class goal.** Atmospheric art direction and perceptual fidelity are first-class engineering goals.
  Physical credibility and evidence truthfulness stay non-negotiable; temporal continuity
  and visual composition are part of correctness at the presentation boundary.
- **Target.** Physically grounded atmospheric art direction, perceptual fidelity and temporal coherence in a
  glanceable ambient interface. The sky and weather read as ONE coherent, continuously evolving environment, not a
  collection of independently calculated or animated effects.
- **Relationships that must hold together:** time-of-day colour progression, solar elevation, scattering, haze,
  cloud coverage and illumination, precipitation, wind, visibility, twilight, moonlight and colour balance. Each
  weather condition has a distinct but physically credible atmospheric identity — never an icon or a uniform
  overlay. Expressive without being arbitrary; physically informed without being sterile: physical models set
  the admissible relationships, composition, colour and motion make them convincing.
- **Aspiration.** Exceed the perceptual quality and environmental coherence of well-art-directed legacy real-time
  sky systems through better physical grounding, temporal behaviour, integration and information accuracy — not
  by adding more effects.
- **Software transitions are not weather events.** An abrupt software-state transition must not be presented as an
  abrupt environmental event. Evidence authority and factual claims (temperature, condition, precipitation
  statements) change at the instant authority changes; cloud motion, illumination and presentation keep temporal
  continuity.
- **Two evaluation criteria, neither substituting for the other, and their composition.** *Physical fidelity:*
  defensible inputs and
  relationships, weather provenance, illumination, atmospheric behaviour, stated limitations. *Experiential
  fidelity:* coherent tonal composition, convincing environmental mood, legible weather differentiation, spatial
  and temporal continuity, absence of rendering artifacts, restrained motion, readable prayer information. The
  final judgment is on how they compose: subsystems that each pass can still interact into an implausible or
  artificial scene. No numerical aesthetic score replaces that judgment.
- **Judge the whole experience** across representative times of day and weather conditions, INCLUDING
  TRANSITIONS, from clips or frame sequences — not isolated effects or stills alone. A technically safe or
  pixel-neutral result is not thereby the best result, and a jarring but defensible behaviour is not to be
  recommended as a permanent residual when a proportionate correction exists. Clips add to the stills listed under
  "Evidence requirements"; they do not replace them, and "Screenshots override metrics" applies to clips equally.
- **Reduced motion.** Under `prefers-reduced-motion` gate M0 governs: transitions are reduced by default and
  `motion=full` (in the URL fragment) overrides. The continuity requirement above is judged in the full-motion
  presentation; the reduced presentation must still be truthful and must not flash.
- **For workers.** State in the contract how the change affects the coherence of the whole scene, not only the
  effect changed. Use day / twilight / night and clear / cloudy / precipitating conditions, and the transitions
  the change can trigger, as the coverage guide: coverage is comprehensive but risk-proportionate — every
  materially affected scene and transition is qualified; combinations a change cannot affect need not be.
- **Fidelity verdicts.** For any change affecting sky, weather, clouds, Moon, solar optics or presentation,
  reviewers and visual judges give separate verdicts on physical fidelity and on experiential fidelity, with
  transition clips where motion or state transitions are involved.
- **Pursue improvements.** Where the implementation falls meaningfully short of this standard, investigate and
  propose the improvement: under the owning work order where one exists, otherwise through a researched,
  independently reviewed work order — never by silently expanding unrelated work. A new phenomenon, model or
  treatment may be researched and evaluated experimentally; research, experimental implementation, production
  adoption and final visual acceptance are separate authorisations.
- **Interface identity is preserved; rendering defects are not.** Fixed: the 325×530 card geometry, glass and
  translucent presentation, header and footer, drop shadow, typography and prayer hierarchy, established
  interactions and accessibility. Not frozen: sky colours, atmospheric coefficients, approximations, transitions
  or artifacts that are demonstrably deficient. Visual conservatism is risk management, not an aesthetic goal: do
  not optimise for zero changed pixels when the existing pixels are the problem, and do not assume more effects,
  complexity or contrast is better.
- **Gates that stay in force.** No major renderer refactor or redesign; no vendored/copied-core change without owner
  authority; owner
  approval for production visual changes, scientific-core changes and anything a work order reserves to the
  owner. Prayer correctness, weather truthfulness, source authority and privacy are hard constraints. Richness
  comes from coherent rendering, accurate information and art direction, not visual complexity.

## Subagent roles & what each reviews

- **GitHub/source auditor** — confirms the committed `index.html` matches what's served; lists the relevant
  systems before any edit.
- **Runtime DOM/CSS/canvas auditor** — measures live geometry (header/footer, cloud band vs dashed horizon, moon
  layers/radius/alpha **+ disc opacity/occlusion (no stars through)**, buckle cut-out vs strap, rain origin vs
  cloud columns) and reports numbers + crops.
- **Live-motion auditor** — proves the default real-time widget actually animates over 15–60s (cloud drift/morph,
  star scintillation, sky breathing) via `&debugMotion=1` Δ / a clip / a centroid-drift probe. **Must NOT cite the
  `qaState().clouds.hash` as motion evidence** (it flips on sub-pixel change — it produced false PASS reports).
- **Atmospheric-optics researcher** — supplies condition gates, geometry, colour orders, gradient recipes for each
  phenomenon before it is coded.
- **Islamic dawn / Fajr semantics researcher** — verifies false-dawn (vertical) vs true-dawn (horizontal) and the
  Fajr depression range; confirms dawn visuals never drive the prayer clock.
- **Solar / lunar renderer art directors** — judge sun placement/optics and moon PBR/earthshine/halo/corona from
  forced-condition crops.
- **Cloud/weather lighting judge** — structure, lighting, weather linkage, and **continuity** (no slideshow).
- **Star/night-sky judge** — variety, twinkle (visible but not cartoonish), moon wash, location/weather response.
- **UI/layout invariant judge** — footer visible + header geometry + readability in *every* scene.
- **Documentation architect / code-comment reviewer** — keep DESIGN.md/AGENTS.md and the high-value comments true.
- **Skeptic visual panel (≥5)** — may FAIL any cycle; must list failures and residual approximations.
- **Regression judge** — diffs old screenshots vs current; flags anything that got worse.

Note: judges that drive the live preview must run **sequentially** (one shared preview server; parallel judges
stomp on each other's scenes). State this honestly rather than faking a simultaneous panel.

## Required PASS/FAIL gates

A cycle PASSES only when, with **screenshot/clip evidence**:

- A — Sun is a **defined radiant body with a clear nucleus**, not a vague brush; colour is **tone-mapped/white-
  balanced** (airmass + transmittance + CCT + ACES) — under cloud it goes **warm-white, never a grey/purple blob**.
- B — Sunrise **enters low from the left** near the horizon (warm glowing disc); sunset sky is warm (not generic
  daylight); low-sun colour believable; low-sun refraction flattening.
- C — Solar optics distinct + gated (halo / parhelia / pillar / crepuscular / anticrepuscular / refraction), each
  only under its physical condition, and **registered to the VISIBLE corner sun** (`--sunvx/--sunvy`) — a center-
  screen halo is a FAIL.
- D — Moon is **OPAQUE every night (no stars through the disc)** and **meaningfully present every night** — a new/
  below-horizon moon shows a faint **ashen opaque calendar disc with NO moonlight** (never blank, never faked
  light); the disc is **mostly in frame** so the phase reads. Earthshine correct across crescent/half/gibbous/full
  (gibbous dark side faint **but textured, never a black cutout**). **Fault-path clause (owner decision 2026-11-22,
  R0041):** in a genuine renderer-failure state only (the start-up Moon renderer missing, failed to decode, throwing
  or with its retry budget spent, and no valid refined record), the slot may show the untextured phase disc. That
  is an exception to the TEXTURE requirement alone — never to opacity or Moon presence, which hold in every state —
  and it must be disclosed in `qaState().moonTruth` (`degraded`, `limitation`). The normal V5 Moon stays fully
  textured; the plain disc is never an ordinary tier and never stands in for available V5 material
  (`docs/state-contracts/R0041.md`).
- E — Lunar corona (small, close) vs 22° halo (large ring) vs paraselenae (lateral, rare) are distinct + gated.
- F — **Dawn is honest, not painted:** true dawn is the **real physical twilight sky** (dark at Fajr depth,
  brightening toward sunrise) + the Fajr marker — **no horizontal "true-dawn band."** False dawn is **fail-closed
  (not rendered)** — **no diagonal cone / lens-flare slash**, and nothing under a bright moon.
- G — Clouds structured, lit, weather-linked; small distinct cells; mostly around/above the dashed 0° horizon.
- H — Rain/lightning originate from cloud systems and vary by weather type/intensity.
- I — Stars beautiful/alive/varied; **not** a spinning or static image; anchors + their glints **scintillate**.
- J — Header belt (buckle **cut-out**, no strap through it) + footer + prayer UI intact and readable in every scene.
- **M0 (live motion) — the default real-time widget VISIBLY animates over 15–60s where the scene allows (clouds
  drift/morph, stars scintillate, sky breathes). Proven by a real watch / `&debugMotion=1` Δ, NEVER the qaState
  hash. Accessibility: `prefers-reduced-motion` reduces it by default; `&motion=full` overrides.**
- K/L/M — DESIGN.md + AGENTS.md + HANDOFF.md current; high-value comments present; approximations stated honestly.

## Evidence requirements (per cycle)

Crops/clips for: clear-day apex (**defined nucleus**), sunrise (enters low-left), sunset (warm sky), overcast
(**warm-white sun, not grey/purple**), forced parhelia/halo/pillar (**ringing the visible sun**), forced
crepuscular/anticrepuscular, crescent (**right limb in frame**)/half/gibbous/full moon, **new moon (opaque ashen
calendar disc)**, **moon-opacity proof (no stars through the disc)**, forced lunar corona/halo/paraselene, daytime
clouds, moonlit night clouds, rain + thunder, star twinkle, **header buckle cut-out (zoom — no strap through)**,
header/footer, near-Fajr (real twilight, **no painted dawn band/cone**). Plus a **real 15–60s live-motion clip /
`debugMotion` 10s–60s Δ** (the headline gate), 5m/15m/60m/day simulated deltas, and `motion=full` vs reduced-motion.
Judges list failures and residual approximations. **Screenshots/Δ — never the qaState hash — decide motion.**

## Forbidden regressions (instant FAIL)

- **No visible motion in normal live real-time view** (a static "wallpaper" sky). Verify with a real 15–60s watch
  / `&debugMotion=1` 10s–60s Δ — **NOT** the `qaState().clouds.hash` (it flips on sub-pixel change and lies).
- The **moon rendered transparent** — stars visible *through* the disc, in ANY phase. The Moon is an opaque body.
- An **empty moon slot / moonless normal night.** A new/below-horizon moon must still show a faint **ashen OPAQUE
  calendar disc** (no moonlight) — never blank sky, never a "new moon invisible" rule.
- A **painted false-dawn cone or horizontal true-dawn band/strip.** Dawn = the real physical twilight sky + the
  Fajr marker; false dawn is **fail-closed** (not rendered) until properly modeled.
- The **sun rendered as a dim grey/purple blob** or a vague brush with **no defined nucleus** (use the scene-
  referred tone-map; cloud → warm-white, never cold grey).
- **Solar optics (halo / sundogs / pillar) detached from the visible sun** (they must register to `--sunvx/--sunvy`,
  not the arc-sun azimuth). A center-screen halo is an instant FAIL.
- Footer date row clipped or any header change that **moves the content stack**.
- **Builder/embed:** the iframe wrapper size drifting from the widget card — it must be **325×530** (= `.c`) in the
  builder preview, the copy snippet, every current-version README snippet, and the TablissNG preset (an oversized
  wrapper adds invisible margin and misaligns the builder card/buttons). The one documented exception is the frozen
  V1 README snippet, which stays 330×534: that is V1's own card-plus-drop-shadow footprint, and the shadow is part
  of the design (owner decision, R0037 DG2; `docs/state-contracts/R0037.md`).
- Header buckle off-centre, straps full-width, a heavy drop shadow, or **any strap geometry visible THROUGH the
  translucent buckle** (the strap inner ends must be *masked/cut*, not merely z-indexed — translucent glass reveals
  what's under it).
- Sunrise marker drawn as a filled dot (it is a **ring**) or off the dashed line; Maghrib off the line; **Dhuhr
  on the apex**.
- The moon's dark limb rendered as a **black cutout**, or a jaggy/stroked moon edge.
- The **untextured phase disc shown outside a genuine renderer-failure state** (while the start-up receiver or a
  valid refined record can serve the scene), shown **without its `moonTruth` disclosure**, or carrying more
  moonlight than the refined disc would at that instant (gate D fault-path clause).
- A **generic** glow standing in for a gated optical phenomenon.
- **Claiming direct local rain/lightning observations from model or uncalibrated radar data**, or letting
  hourly forecasts overwrite current conditions in real time. The owner's PR42 policy explicitly permits
  labelled fresh current-model rain/snow with supporting admitted quantities. Keep condition presentation,
  model effect permissions and direct-observation authority separate; see DESIGN.md. The live lane is a
  labelled model estimate; the synthetic present lane (`synthetic-present-v1`) is QA-only and never fed by a provider.
- Clouds that **reseed / slideshow** on weather refresh or per render tick.
- Replacing the accurate PBR moon lighting with a flat sprite; making physics "ugly". (The gate D fault-path
  clause is the one exception, and only to texture: a disclosed renderer-failure fallback, never a rendering tier.)

## Commit policy

Do not commit or push unless the user explicitly asks. When asked: commit the **relevant source + docs**
(`index.html`, `config.js`, `builder.html`, `install.sh`/`install.ps1`, `presets/`, `tests/`, the `*.md` docs) —
**never** the stray research scratch files (`noaa_clouds.html`, `*_photopills.html`, `_mag_extract.txt`, etc.).
`main` deploys to GitHub Pages, so a commit to `main` is a deploy. End commit messages with the standard
`Co-Authored-By` line.

The qualification gate `.github/workflows/qualification.yml` (R002A, issue 91) runs on pull requests to `main`,
pushes to `main` and dispatch: build twice with a clean tree, the registered population under the exact ledger,
`verify_v1` and pin coherence. It is **advisory** (owner decision DG-1(a)): no check is required, so it detects
and cannot prevent a deploy. Quote each job's verdict string (for example `PASS_WITH_DECLARED_FAILURES (n)`),
never the check colour. After a merge, the delivery step reads the public bytes back with
`tools/qualification/delivery_identity.py --commit <merge sha>` (workflow `delivery-identity.yml`); a
certificate cites that receipt, and only an `identical` verdict for the exact commit. The suites job installs
exactly two hash-locked wheels (`numpy`, `scipy`, `tools/qualification/gate-requirements.txt`) that the vendor
scientific suite imports; it is the gate's only network use beyond checkout and pinned actions. Declared counts are
host-conditional: the Linux runner declares three fewer entries (R28-L12/L14/L17, condition `symlink-unavailable`)
than a host that cannot create symlinks.
See `docs/state-contracts/R002A.md`.

Retained evidence is kept in git but not published (R002B, owner decision DG-2(a)): `_config.yml` excludes
`docs/real-sky/evidence`, `docs/rlgwo-execution`, `docs/state-contracts/evidence` and `docs/moon/evidence`
from the Pages build. Cite evidence by commit-pinned github.com links, never github.io; put new evidence
under one of those trees, and measure the payload with `tools/pages_payload.py` (bound 1,000,000,000
regular-file bytes; `docs/state-contracts/R002B.md`).

## Running / debugging common scenarios

Configuration and diagnostics are read from the fragment after #. Append &debugMotion=1 or &motion=full to that same fragment. A query-only ?debugMotion=1 is not read. The six debugOptic force names are halo, sundogs, pillar, anticrep, paraselene and lunarhalo. Corona, earthshine, refraction and the crepuscular ray require controlled physical scene inputs; no dedicated debugOptic switch forces them.

Real-time motion diagnostic:

```text
index.html#lat=24.47&lon=39.61&label=Madinah&method=4&debugMotion=1
```

Full-motion override (the normal default respects reduced motion):

```text
index.html#lat=24.47&lon=39.61&label=Madinah&method=4&debugMotion=1&motion=full
```

Solar noon halo diagnostic:

```text
index.html#lat=24.47&lon=39.61&label=Madinah&method=4&simTime=12:30&debugOptic=halo
```

Query-only negative control: these flags are not read from before #.

```text
index.html?debugMotion=1&motion=full#lat=24.47&lon=39.61
```

simTime without timeScale freezes the clock-driven scene. Use the real-time recipe above for a 15–60 second motion check. Flag activation alone does not prove visible motion or correct optical pixels.

Lunar force checks require an eligible night Moon. Near-new, below-horizon, daylight and unavailable-surface cases cannot gain moonlight from a diagnostic flag. Retain the physical scene inputs and crops for optics, and the real 15–60 second watch/clip/delta for motion; never use `qaState().clouds.hash` as motion proof.

Serve the folder statically and open `index.html#lat=24.47&lon=39.61&label=Madinah&method=4`.

- Day positions: `&simTime=12:30` (noon), `&simTime=05:50` (sunrise), `&simTime=18:55` (sunset/golden hour).
- Weather visuals: `&simWx=2&simCloud=50` (broken), `&simWx=3&simCloud=100` (overcast), `&simWx=63` (rain),
  `&simWx=95` (thunder), `&simWx=45` (fog).
- **Weather-truth QA**: `&simWx=95&simPrecip=0` must downgrade (no thunder/rain); `&simWx=95&simPrecip=5` keeps
  thunder; check `qaState().wxTruth` for the source/reason chain.
- Moon: `&simMoon=0.08&simWax=1&simMoonAlt=20&simMoonH=42` (crescent), `&simMoon=0.92…` (gibbous), `&simMoon=0.98…`
  (full); thin-cloud halo/corona via `&simWx=2&simCloud=30` on a moon scene. `simMoon*` drives the native disc,
  the native moonlight and the Moon worker scene only; it does not override the refined sky's real-ephemeris
  lunar-scattering inputs. Lunar-light or whole-sky evidence made under `simMoon*` must therefore use a clock instant
  at which the real Moon is consistent with the simulated one (for example below the horizon for a "no moonlight"
  scene), or state the divergence (DESIGN.md "URL parameters"; `docs/state-contracts/R0033.md` §14).
- **Live motion**: load real-time (no `simTime`) and **watch ~15–60s** — clouds must drift/morph, stars
  scintillate, sky breathe. `&debugMotion=1` shows rAF/s, cloud-paint/s, reduced-motion, paused, **cloud Δ 10s/60s**,
  star Δ, reason. `&motion=full` forces motion under OS reduced-motion. `&timeScale=1800` fast-forwards a day.
- **Moon opacity**: any night moon — confirm **no stars show through the disc**; new moon (`&simMoon=0.01`) shows a
  faint **opaque** ashen calendar disc with `qaState().moonTruth.moonlightOpacity == 0`.
- Readouts: `&debugLayers=1`, `&debugMoon=1`, `&debugMotion=1`, `&qa=1` then `window.qaState()` (incl. `wxTruth`,
  `moonTruth`). `&debugDawn=…` is a deprecated no-op (dawn is not painted).
- **Diagnostic reads observe without acting (R0036).** `qaState()`, its CP9 wrapper, the `debugMotion` overlay and
  the smoke instrument write no storage, adopt or publish no Moon texture (`SalahMoonRuntime.observe()` only), withdraw
  no clouds, paint no header and issue no request, so polling them does not change what they measure. Never read the
  adopting `SalahMoonRuntime.surface()`/`state`/`detailEnabled` from a new diagnostic. `qaState().cache.simulated` and
  `cache.overrides` name every effective override; the weather/radar `requests.*.admission` field gives the admission
  outcome beside the transport `state` (DESIGN.md).
- **Diagnostic overrides are not visibly badged (owner decision G1 = A, issue 103).** Every `sim*`, `debugOptic`,
  `timeScale` recipe above shows synthetic weather/clock/Moon/optics with provenance only in the header title/ARIA
  label, the `.simclock` read-out of an advancing clock and `qaState()`. A crop from such a URL is simulation evidence:
  say so in the evidence, and never copy such a URL into an embed, preset or README snippet.
- Preview gotcha: `simTime` without `timeScale` freezes the clock (TIMESCALE 0), so cloud drift won't be visible
  in a still test — use a real-time / `timeScale` watch to see motion. Calling `paintClouds(t)` directly at two
  `t` values does not show drift: motion integrates elapsed frame time, not `t`.

## Frozen V1 compatibility snapshot

v1/ is the frozen pre-overhaul compatibility snapshot. Normal builds and renderer integrations must neither regenerate, overwrite nor delete it. Any deliberate change requires explicit owner authority and disclosure.

Run `python tools/verify_v1.py` after builds/integrations. It verifies V1 independently
of the current root runtime. See `docs/V1_PRESERVATION.md` for provenance, storage
isolation, focused comparison checks and the pending deployment smoke procedure.
