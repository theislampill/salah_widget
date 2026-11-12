> **Lane working paper.** This is supporting detail produced by one census lane of the post-RLGWO audit at baseline `363c3e53`. It is superseded by [IMPLICIT_STATES.md](../../../../IMPLICIT_STATES.md), [REPORT.md](../REPORT.md), [CROSSWALK.md](../CROSSWALK.md) and [FINDINGS.md](../FINDINGS.md) wherever they differ; the integrator's corrections are listed in REPORT.md. Probe paths `probes/<lane>/` refer to [../probes/](../probes/README.md).

# Lane G — independent second omission pass

Baseline `363c3e536c8004935ef80230e43f7712e339e3a5` (worktree read-only; source files only). Line numbers are for
the authored source at that SHA. `S:` = `src/native/index.html`, `CFG:` = `src/native/config.js`,
`B:` = `src/native/builder.html`.

Method: before reading any lane findings, I read only the six lanes' `machines` arrays (id, name, sources) and the
registry headings `ISM-INST-001…007`. I then ran the nine search strategies on the source. Only after writing the
omission list below did I grep the lane Markdown for each candidate's keywords, to classify it. Candidates that a
lane already covered were dropped, and are listed under each strategy as "covered by".

Probes (effect-free; no network, DOM or browser; they read source through `git show` on stdin):
- `probes/G/tz-hint-probe.cjs`: extracts `utcFields/zoneFormatter/projectInZone/partsInTz/prayerCivilDay/prayerNextDay` and evaluates them in a `vm`.
- `probes/G/tz-identity-probe.cjs`: evaluates `config.js` in a `vm` with a stub Storage, then applies the `skySceneIdentity` formula.

## 1. Omissions

Summary: 7 omissions. By type: (a) 0, (b) 3, (c) 4. By materiality: medium 1, low-medium 2, low 4.

| id | type | name | materiality | evidence class |
|---|---|---|---|---|
| OM-01 | c | Provider timezone adoption re-keys the sky/Moon scene (tz hint → adopted tz) | medium | demonstrated (source trace + config probe); runtime visual effect not reproduced |
| OM-02 | c | `tz` is a parse-only configuration field: the builder never emits it, so every portable embed boots on the `America/New_York` hint | low-medium | demonstrated (probe) |
| OM-03 | b (C01, N04, N08, N22) | Per-location prayer/weather cache namespace lifecycle: no eviction, survives Reset, shares quota with config persistence | low-medium | demonstrated (source) for lifecycle; speculative for quota coupling |
| OM-04 | b (N22, N20; adjoins F-C04) | In-memory provenance marker `source:"localStorage"` survives a successful `clearLocal` | low | demonstrated (source trace) |
| OM-05 | b (C02, NEW-D-05) | Diagnostic acquisition flags (`_autoDetectStatus/_autoDetectSource/_geoLastError`) are boot-only and can stick | low | demonstrated (source trace) |
| OM-06 | c (extends NEW-C-02) | 325×530 card geometry duplicated as literals across the renderer modules | low | observed (source) |
| OM-07 | c (R14 ↔ R01/R15) | First paint re-parses the fragment with semantics that differ from the native snapshot | low | demonstrated (source) for blank camera parameter; speculative impact |

### OM-01 — Provider timezone adoption re-keys the sky/Moon scene

- **Why it is a transition.**
  - The accepted sky scene key `_skySceneKey` is compared every paint with `skySceneIdentity()`. That identity is `[lat,lon,tz,wall|anchor]` (S:2217-2220).
  - `tz` has an unguarded state change: hint (config) → provider-adopted zone.
  - Writers: `bindConfig` S:686; `loadPrayerData` S:3676, 3691, 3697; `adoptPrayerBundle` S:1213.
  - Any change makes `paint()` (S:3244-3246) or `paintCelestialWithoutTimetable()` (S:3020) call `beginSkyScene(_skyInitialDocument)`. That call:
    - invalidates the Moon runtime (S:2227);
    - re-adds `sky-pending`/`sky-initializing` and removes `moon-ready` (S:2228);
    - nulls the key, un-commits the scene, clears `_starsProjected` (S:2229);
    - withdraws the cloud publication as "scene superseded" (S:2230).
  - The same `tz` also enters:
    - `moonGeometryObservation` context `[lat,lon,tz]` (S:2031-2037);
    - `SalahMoonHost.capture().sceneIdentity` (S:4170-4171), which keys Moon jobs in `moon/src/moon-native.mjs` L31/L35;
    - the native identity in `real-sky/native-contract.mjs` L9 (`s.tz`) through `real-sky/native-host-hooks.js` L42.
- **Event ordering that makes it routine (boot).**
  1. `boot()` paints the shell with the hint zone (`render()` S:3818 → `paintCelestialWithoutTimetable` adopts `_skySceneKey` with the hint).
  2. It publishes the preview and calls `finishInitialSkyDocument()` (S:3825-3827).
  3. It yields (S:3832-3840).
  4. Only then does `loadPrayerData()` write `tz=cached.timezone` (S:3676) or `tz=data.meta.timezone` (S:3691).
  - The next paint sees a new identity and begins a second scene. By then `_skyInitialDocument` is false, so the Moon invalidation is non-initial and the one-shot initial head (E-lane R21) is retired.
  - This happens even with a warm prayer cache, because the cache is read after the yield.
- **Also on runtime apply.** A broad `applyConfig` calls `bindConfig(cfg)`, which writes `tz=c.tz||tz` (S:686, 3751). The settings form round-trips `CONFIG.tz`, which is the hint (S:4026). So every broad apply resets `tz` to the hint, then flips it again on adoption.
- **When hint ≠ provider zone.** Every portable builder embed outside America/New_York (see OM-02). Also any local-mode user whose device zone differs from the site zone (coarse detection uses `Intl` first, CFG:262, 295).
- **Sources.** S:2217-2252, 3017-3021, 3242-3249, 3669-3700, 3779-3849, 686, 2026-2037, 4168-4176; `real-sky/native-host-hooks.js` L20-44; `real-sky/native-contract.mjs` L3-10; `real-sky/native-first-paint.mjs` L13-18 (the head also uses the hint: `sceneIdentity:[lat,lon,c.tz||'America/New_York','wall']`); `moon/src/moon-native.mjs` L23-35.
- **Classification.** (c), an unlisted coupling between:
  - NEW-A-03, whose reader list omits `skySceneIdentity`, `moonGeometryObservation` and the native/Moon capture;
  - N13 and R01, whose identity contents are listed but whose tz-adoption trigger is not;
  - R19/R21 and R14.
- **Materiality: medium.**
  - No prayer value changes.
  - It touches the hard-constraint area "accepted vs displayed state" and the boot-presentation contract that R14/R21/first-paint engineering protects.
  - Cost: one redundant scene teardown per boot, plus a discarded Moon/refined job. There is a plausible visible re-pending of celestial layers after the timetable arrives.
  - The ordinary wall-clock sky does not depend on the civil zone: UTC + lat/lon determine it. So `tz` in an ordinary-mode identity carries no astronomical information.
- **Tests.** The retained first-paint/boot tests use a site whose zone equals the default hint:
  - `tests/real-sky/native-first-paint.test.mjs` L20-22 (Orlando, `America/New_York`);
  - L61-65 (cache and provider both `America/New_York`).
  - The flip case is therefore not exercised.
- **Observed facts.**
  - Identity contains `tz` (S:2219).
  - Paint begins a new scene on any identity change (S:3245-3246).
  - Loader writes `tz` after `finishInitialSkyDocument` (S:3827 before S:3846 → S:3676).
  - Probe: builder serialization of a Madinah draft has no `tz`, and resolves to the hint `America/New_York`. The identity changes from `24.47|39.61|America/New_York|wall` to `24.47|39.61|Asia/Riyadh|wall`.
- **Hypotheses.**
  - The second scene causes a brief re-pending or flash of Moon/sun layers, and a full refined-sky and Moon re-render on every such boot.
  - Retained startup evidence recorded with the AGENTS recipe (`#lat=24.47&lon=39.61…`, no `tz`) includes this second scene.
- **Unknowns.** Pixel-level visibility of the re-pending (no browser run). Whether `real-sky/native-lifecycle.mjs` coalesces the two identities fast enough to hide it.

### OM-02 — `tz` is a parse-only configuration field

- **Why it matters.** `parseHash` accepts `tz` (CFG:126) and `normalize` defaults it to `America/New_York` (CFG:29, 145). `serialize` never writes it (CFG:182-206).
  - Builder output therefore never carries a zone. B:212 `hash()` goes through `serialize`.
  - README examples do carry one (README L36 `…#lat=24.4672&lon=39.6142&tz=Asia…`).
  - The hint then:
    - freezes the prayer cache key `_cacheTz` (S:680, 686, 1067), so all portable builder embeds key under `America/New_York`;
    - seeds the first weather request zone, because `fetchWeather` S:3845 captures `op.requestZone=tz` (S:1076, 1450) synchronously before `loadPrayerData` writes the cached zone (S:3846 → S:3676);
    - seeds the first-paint identity (OM-01);
    - is round-tripped by the settings form (S:4026).
- **Classification.** (c): builder ↔ widget ↔ README contract on a field with no shared source of truth for whether it is emitted. It combines with A-F01, an invalid hint that is fatal; that finding is already covered.
- **Materiality: low-medium.** It drives OM-01. Weather epochs stay correct, because admission uses the captured zone (S:1327-1334, 1356). The cache key is stable, as the README L397-400 discloses.
- **Observed facts.** Probe `tz-identity-probe.cjs`: `serializedHash = lat=24.47&lon=39.61&label=Madinah&method=4&school=0`, `containsTz=false`, `resolvedTzHint=America/New_York`.
- **Hypotheses.** For non-hour-offset sites, a hint-zone weather request returns a 3-day window aligned to the hint zone's midnight instead of the site's.
- **Unknowns.** Open-Meteo hourly alignment for half-hour-offset zones under a foreign `timezone=` (not contacted).

### OM-03 — Per-location cache namespace lifecycle

- **State.** One `salah:<lat>|<lon>|<_cacheTz>|<method>|<school>` key per prayer configuration (S:1067, 1126). One `salahwx:<lat>|<lon>|<units>` key per weather target (S:1292, 1471).
  - The only `removeItem` calls in authored source are `clearLocal` (config key only, CFG:247) and the storage probe (CFG:215).
  - Nothing scans, evicts or migrates these keys. README L397-400 says this explicitly for the prayer key.
  - Weather entries older than 6 h are ignored on read (S:1408), but never deleted.
- **Transitions not modelled by any census machine.**
  - The key set only grows: each new coordinate/method/school/units combination adds a key.
  - Settings Reset leaves every key, including coordinates in key names. Browser-position coordinates come from `toFixed(5)` (S:4114).
  - Storage quota is shared with `salah_widget:config:v1`. A full origin makes `saveLocal` fail (CFG:242-244), which becomes the N22 "session-only" warning.
- **Classification.** (b) of C01/N22 (persistence) and N04/N08 (cache readers/writers). The census lists the keys, but not their lifecycle or the cross-coupling with config persistence.
- **Materiality: low-medium (privacy, disclosed).** README L281 states that Reset does not erase prayer/weather caches. Coordinates in key names are not called out.
- **Evidence.** Demonstrated (source) for "no eviction / Reset leaves keys". Speculative for quota exhaustion: entries are small, so many distinct targets would be needed.
- **Unknowns.** Partitioned-storage lifetime in TablissNG. Whether `offline.html` (same origin, same keys) adds to the same namespace in practice.

### OM-04 — Provenance marker survives a successful `clearLocal`

- **Transition.** `_resetLocal` publishes the cleared outcome (S:4124-4125) without touching `CONFIG`.
  - If the continuation is abandoned (detect failure S:4143, or panel closed so `_ownsSetLookup` fails at S:4131), `CONFIG.source` stays `"localStorage"` (set at S:3738).
  - On the next open, `_populateSettingsForm` derives `_setLocationSaved=CONFIG.source==="localStorage"` (S:4038). `_setPin` then labels a device-position target "Saved browser position" (S:3966) even though nothing is saved.
  - `classifyConfigChange` is unaffected, because it compares `origin||source` (S:730).
- **Classification.** (b) of N22/N20. It adjoins C's F-C04 (runtime ≠ storage after Reset + close), which records the status text but not this provenance label.
- **Materiality: low.** Truthful location provenance, label only.
- **Evidence.** Demonstrated by source trace; no probe was run.

### OM-05 — Diagnostic acquisition flags are boot-only and can stick

- **Facts.**
  - `_autoDetectStatus` is set `"pending"` at S:3794.
  - If a newer generation supersedes boot detection, `boot()` returns at S:3796 before writing `"ok"`/`"failed"`. `qaState()` then reports `autoDetectStatus:"pending"` forever (S:3586).
  - Reset's coarse detection (S:4130) never updates `_autoDetectStatus`/`_autoDetectSource`.
  - `_geoLastError` is cleared only by a successful GPS read (S:4114). A later manual/place location keeps the old error.
- **Classification.** (b) of C02 (acquisition) and NEW-D-05 (diagnostic telemetry).
- **Materiality: low.** Truthful evidence: `qaState` is used as qualification evidence.

### OM-06 — 325×530 geometry duplicated across the renderer modules

- **Sites.** S:482, 520-521, 551, 554 (SVG viewBox/mask); S:2072, 2088 (`sx:x/325, sy:y/530`); S:2986-2987 (`--sunvx/--sunvy` normalisation).
  - `real-sky/native-contract.mjs` L20 (`view.width/height`); `native-engine.mjs` L20; `native-host.mjs` L74, 95, 107-113, 146, 181-191; `native-composition.mjs` L109-156; `native-first-paint.mjs` L23, 30; `native-preview.mjs` L19, 22, 39; `native-host-hooks.js` L35 (solar anchor scale through `vr.width/height`).
- **Classification.** (c) extending NEW-C-02. The census binds 325×530 to builder/README/preset only. The physics raster, masks and `--sunvx/--sunvy` registration (an AGENTS gate C invariant) depend on the same literal without a shared constant or check.
- **Materiality: low (maintainability).** The values agree at baseline (observed).

### OM-07 — First paint re-parses the fragment with diverging semantics

- **Facts** (`real-sky/native-first-paint.mjs` L11-21 vs `native-host-hooks.js` L23, 41-42 and S:794-802):
  - **Blank camera parameter.** First paint uses `Number(params.get(k))`, so `#skyAz=` becomes `0`. Native `cameraNumber` makes a blank value `NaN`, and `nativeIdentity` then throws `Invalid native camera azimuth` (`native-contract.mjs` L7). The head renders a sky the native renderer refuses.
  - **Temporal exclusion list.** First paint excludes `simTime|simDate|timeScale`. `simDate` is not a native parameter (S:770-784 has none), so `#simDate=` suppresses first paint for a no-op key.
  - **Duplicated formulas.** First paint re-derives reduced motion (`params.get('motion')!=='full'&&matchMedia…`) and the identity format `[lat,lon,tz,'wall']`. These must equal `isMotionReduced` (S:802) and `skySceneIdentity` (S:2219) without a shared source. The S:162 comment says the matchMedia duplication was unified.
- **Classification.** (c) between R14 (first paint) and R01/R15 (native snapshot).
- **Materiality: low.** These are diagnostic parameters. The identity duplication is tested only for the default-zone case (`native-first-paint.test.mjs` L22).

## 2. Per-strategy results

| # | strategy | result |
|---|---|---|
| 1 | module-level flags assigned in >1 function (S:678-682, 854, 926-934, 1070-1072, 1166-1169, 1263, 1480, 1620, 1892-1893, 2108-2109, 2221-2222, 2271-2274, 2676-2688, 3326-3380, 3476, 3648, 3711, 3907-3911) | OM-04, OM-05 new. Everything else covered: N03/N05 rollover flags, N19 `_loopStarted`, N13 `_skyCommitted/_skyMoonPresence`, N11 `_pbr*`, N15 `_cloud*`, N20/N21 `_set*`, NEW-A-01 webfonts, N18 `_cnFit` |
| 2 | listener/timer/rAF/MessageChannel/fetch/Observer pairing (S, CFG, B, real-sky/*, moon/src/*) | Nothing new. Singleton or idempotent registrations: date dialog S:891-894 `_dateDisclosureBound`; buckle S:4016 class guard; settings S:4044 `_setWired`; IntersectionObserver S:3895 inside the `_loopStarted` singleton. Covered by N07/N19/N20/NEW-D-03/NEW-E-04/R03-R05/R20/R27. No `hashchange`, `storage`, `online/offline`, `freeze/resume` handlers anywhere (C noted `storage`/`hashchange`) |
| 3 | shared mutable state, storage keys, hash, DOM-as-state | OM-03 new (key lifecycle). Keys: `salah_widget:config:v1` (CFG:21), `__sw_probe__` (CFG:214, covered F-C08), `salah:*` (S:1067), `salahwx:*` (S:1292); v1 uses disjoint `salah_widget:v1:*` keys (v1/config.js L21, 145; v1/index.html L735, 767). DOM-class channels `.c.paused` (read by native-host-hooks L42 and S:4176), `sky-pending`, `moon-ready`, `mask-on`: covered by NEW-D-03/NEW-E-02/N13 |
| 4 | caches/memos | Nothing new beyond OM-03. Covered: `_zoneDays` (4-entry FIFO, A), `_partsFormatter`/`_prayerDayFormatter` (A), `_prayerAdmissions` WeakMap (N04), `_wxTargetCache`/`_wxDecisionCache` (B), `_weatherInformationCache` S:1747-1810 (keyed decision+day+zone; implicitly in N09, not named), `_cnFontLoads` (N18), real-sky R16/R31-R34/R36, Moon R26/R29 |
| 5 | time-dependent decisions | Nothing new (A-F08, R000D retry clock, CFG:72 future-epoch rule disclosed in README L279). Clock jumps: prayer cooldown and weather retry use `_RAFNOW`; freshness uses `Date.now` (B covered) |
| 6 | worker init/teardown, error→success | Nothing new: covered by R05/R06/R20/R23-R25, EF-E01..E04. One error→success fallback (`partsInTz` host-zone fallback S:943-946) is covered as A-F01 |
| 7 | cross-file coupling | OM-01, OM-02, OM-06, OM-07 new. Covered: README pins/installer blobs (NEW-F-04/FND-F-10), preset `local=1` (C12), wrapper 325×530 (NEW-C-02), checkpoint `'9'` literal (`real-sky/checkpoint.json` vs `native-assets.mjs` L48, `native-host-hooks.js` L62-63; agree, not material) |
| 8 | installation/publication | Nothing new. No service worker or manifest (grep `serviceWorker`: none). `offline.html` is a same-origin second entry sharing every key (C/E note it). Third-party hosts: Aladhan, Open-Meteo, RainViewer (+ manifest-supplied tile host, BF04), GeoJS, ipinfo, Nominatim, Zippopotam, BigDataCloud (builder, F-C05), Google Fonts (NEW-A-01). Pages/workflows: F |
| 9 | boundaries between machines | OM-01 (tz authority ↔ sky/Moon identity) is the main hand-off gap. Checked with no gap found: boot coarse-detect ↔ settings apply (generation guard S:3796); SalahClock ↔ weather (NEW-B-06); builder ↔ preview storage (C NEW-C-02); render loop ↔ Moon (E); weather ↔ cloud receipt (NEW-B-02/NEW-D-02) |

Strategies not completed:
- **(7) installer constants.** I compared repository URLs only (`B:442-445`, `install.sh` L24/L566, `install.ps1` L23/L1144/L1447/L1458, README L59/L63/L117). I did not diff installer version/digest constants. The registry and lane F own them.
- **(8) Pages state.** Not checked against the live site (no network).
- **(4) internals.** `vendor/real-sky` and `real-sky/core/src/**` internals beyond grep were not read.

## 3. Disagreements with the first pass

I skimmed the lane findings after writing section 1, and spot-checked these claims against the source. None was contradicted:
- A-F01: S:1170-1176, 3671, 3687-3689, 1056.
- A-F02: S:1014 `_simTz!==tz` → `initSim` uses `Date.now()` when `SIM.time==null`.
- C F-C01/F-C04: S:4122-4144.
- D-F03: S:3869-3891; a throw leaves the stale non-null `_raf`, so `start()` is a no-op.
- BF04: S:1530-1541.
- BF06: S:707.

Omissions, not contradictions:
- **NEW-A-03.** Its reader list (A-prayer-time.md, NEW-A-03 "Readers") omits `skySceneIdentity` (S:2219), `moonGeometryObservation` (S:2031), `weatherInformation` (S:1749) and the native/Moon captures (`native-host-hooks.js` L42, S:4171). That is why the tz-adoption scene flip (OM-01) is missing.
- **N13.** D's N13 lists `tz` among the identity contents and says "Hypotheses: none new". The tz-hint → adopted-zone change is a routine trigger of `beginSkyScene`, which the entry does not record.
- **First-paint test coverage.** Lane D's R14 entry and E's first-paint notes treat that coverage as adequate, but both fixtures use the default hint zone (`tests/real-sky/native-first-paint.test.mjs` L20, L61). So the non-default-zone boot path is unverified.
