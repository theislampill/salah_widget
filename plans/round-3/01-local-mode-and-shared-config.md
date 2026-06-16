# Plan 01 — Shared `config.js` + local self-configuring mode

**Status:** ✅ DONE (2026-06-16, UNCOMMITTED — `main`→Pages needs explicit go-ahead). Shipped exactly as planned.
Proof: hardcoded embed **byte-identical** (Smoke A/B: `sunEl` 61.1, Dhuhr→Asr leftMin 73 progress 0.637, all six
prayer times, ☀️ buckle, no settings affordance) — re-confirmed after every change. `#local=1` coarse-detects via
GeoJS (live), renders, shows the concise label. Settings panel verified opening by **mouse + keyboard (Enter) +
Esc**, fields populated from config, **Apply** (live, no reload → London/BST/°C), **Save**+reload (persists,
`source:localStorage`), **Reset** (clears + re-detects), **Use precise location** success (Tokyo) + denied
(graceful, form preserved), **storage-blocked** (no crash, applied in-session, clear message), **detect-failure →
manual** (panel opens, Paris applies). Builder emits both snippets (portable byte-identical; local adds
`allow="geolocation"`). Nested-iframe (TablissNG-equivalent) local mode auto-detects. `qaState().config` added.
`tests/smoke.html` **61/61** (+21 config-contract smokes). Phases P0–P7 all complete. Deviations from plan: none of
substance — `lp`/`seed` flow through `config.js` round-trips but are intentionally **omitted from the settings panel
UI** to keep it low-clutter (per the task's "if low-clutter" allowance); the 25px header buckle is kept at its
existing size (header geometry is a hard invariant) so its touch target is small but functional.

## 1. Feasibility evidence (the make-or-break spike)

Live cross-origin `fetch` from the preview browser (origin `http://localhost:5577`), control = Open-Meteo CORS
(works, proves outbound is functional):

| Endpoint | Result | Verdict |
|---|---|---|
| `get.geojs.io/v1/ip/geo.json` | `type:cors` 200, 118 ms; returns `latitude, longitude, city, region, country, timezone` (IANA), `accuracy`, `ip` | **PRIMARY** |
| `ipinfo.io/json` | `type:cors` 200; returns `city, region, country, loc:"lat,lon"`, `timezone` (IANA) | **FALLBACK** |
| `ipapi.co/json/` | `Failed to fetch` in both cors + no-cors (22 ms) → host unreachable in sandbox; cannot verify | rejected (unverifiable) |
| `freeipapi.com/api/json` | no-cors opaque OK (reachable) but cors `Failed to fetch` → **no ACAO header** | rejected (CORS) |
| `ipwho.is/` | 403 `"CORS is not supported on the Free plan"` | rejected |
| `ip-api.com/json/` | 403 `"SSL unavailable … order a key"` → HTTPS = paid; mixed-content on Pages | rejected |

GeoJS: free, no key, no registration, explicit CORS, "no rate limits (yet)", MaxMind GeoLite (honestly coarse →
"estimated area"), published privacy policy. The `accuracy` field lets us be honest about coarseness.

## 2. `WidgetConfig` contract (canonical shape)

```
{
  v: 1,                 // schema version (persistence + migration)
  lat: Number|null,     // -90..90
  lon: Number|null,     // -180..180
  tz:  String,          // IANA name, "" => let Aladhan/Open-Meteo derive from lat/lon
  label: String,        // location display name
  method: String,       // Aladhan method id "0".."16"
  school: String,       // "0" (Shafiʿi…) | "1" (Hanafi)
  time: "12"|"24",
  datefmt: String,      // Unicode token string (e.g. "YYYY-MM-DD")
  units: "f"|"c",
  lp: Number,           // 0..1 light pollution (optional extra; index already supports ?lp=)
  seed: Number|null,    // optional star seed (only if trivially supported; else omitted)
  source: "hash"|"localStorage"|"coarse-ip"|"browser-geolocation"|"manual"|"fallback",
  savedAt: Number|null  // epoch ms, set on persist
}
```

`window.SalahConfig` API (all pure/synchronous except detect/geolocate):
`DEFAULTS`, `parseHash(hashStr) -> {cfg, flags:{local,preferLocal}}`, `validate(cfg) -> {ok, errors}`,
`normalize(cfg) -> cfg` (clamp/coerce), `serialize(cfg) -> hashString` (omits defaults; back-compat),
`loadLocal()`, `saveLocal(cfg) -> {ok, error?}`, `clearLocal() -> {ok}`, `storageAvailable() -> {ok, error?}`,
`coarseDetect({timeoutMs}) -> {ok, cfg?, source, status}` (GeoJS→ipinfo, `Intl` tz first), `KEY`.
Resolution helper `resolve(hashStr) -> {cfg, mode, needsDetect}` (sync part) is consumed by `index.html`.

## 3. Precedence (resolution algorithm)

```
{cfg:hashCfg, flags} = parseHash(location.hash)
mode = flags.local ? "local"
     : flags.preferLocal ? "preferLocal"
     : (hashCfg.lat!=null && hashCfg.lon!=null) ? "hardcoded"
     : "bare"

hardcoded   : CONFIG = normalize(hashCfg, source:"hash")            // localStorage IGNORED (sync)
preferLocal : saved = loadLocal()
              CONFIG = saved? saved(source:"localStorage")
                     : hashCfg.lat? normalize(hashCfg,"hash")        // hash is the default it opted to allow override of
                     : needsDetect                                    // -> detect -> manual
local       : saved = loadLocal()
              CONFIG = saved? saved(source:"localStorage") : needsDetect   // -> detect -> manual
bare        : keep existing behavior -> showError("Add lat & lon to the URL")
```

Non-location prefs (method/school/time/units/datefmt/lp) from the hash are layered as **defaults beneath** the
winning location source, so `#local=1&units=c` still honours the unit preference. The async `needsDetect` path
runs in `boot()`: `coarseDetect()` success → `source:"coarse-ip"` (not auto-saved; user can Save); failure →
open the manual settings panel (`source:"manual"`, then `"fallback"` if the user never sets coordinates).

Key safety: **hardcoded resolves fully synchronously at module load** (hash parse + nothing else), preserving
the exact current boot timing. Only `local`/`preferLocal` without a saved config defer to async detect.

## 4. Phases

**P0 — Smoke A baseline.** Capture `qaState()` + screenshot for the hardcoded Madinah embed and the bare-URL
error, pre-mutation. Re-verify the smoke suite is green (40/40) as the starting line.

**P1 — `config.js`.** Implement `window.SalahConfig` (§2). No wiring yet. Unit-smoke it standalone.

**P2 — index.html core refactor.** Load `config.js` before the inline script. Replace top-level
`const lat/lon/method/school/fmt24/units/datefmtStr/label/LPOLL` with mutable bindings populated from
`SalahConfig.resolve(location.hash)`; keep `q` for SIM/debug flags. Convert `cacheKey`/`wxKey` **const →
function** and update call sites. `boot()`: hardcoded → unchanged path; `needsDetect` → await `coarseDetect()`,
update CONFIG, else open manual panel. **Acceptance:** Smoke B (hardcoded) byte-identical to Smoke A
(`qaState` deep-equal on stable fields + screenshot match); bare URL still errors; 40/40 smokes still green.

**P3 — coarse auto-detect runtime.** `#local=1` first run with no saved config → detect → render times; on
failure → manual panel (never crash). Disclose the IP send in the panel. **Acceptance:** `#local=1` renders
real prayer times from detected area; killing the network shows manual setup, no console throw.

**P4 — settings affordance + panel.** `.buckle` → `<button aria-label="Widget settings">` (reset styles to
preserve visuals), weather-emoji⇄gear morph on `:hover`/`:focus-visible`, opens on click/Enter/Space/touch;
gated to local/preferLocal mode. Compact in-card panel (`.c.settings-open` swaps `.panel/.times/.d` for the
form) with all fields + actions: Save locally · Apply (no save) · Use estimated area · Use precise location ·
Reset local · Cancel. `applyConfig(cfg,{save})` updates CONFIG + bindings, recomputes keys, re-fetches
timings/weather, re-renders — **in-memory, no reload** (works when storage is blocked). **Acceptance:** panel
opens by mouse/keyboard/touch; Apply changes location live; Save persists; closing restores the exact normal
view; iframe never resizes; header/footer never clipped.

**P5 — precise geolocation.** "Use precise current location" button → `navigator.geolocation.getCurrentPosition`
only on click; success → `source:"browser-geolocation"`; denied/blocked/timeout → keep current config + show a
useful message, no break. **Acceptance:** denied path does not break setup.

**P6 — builder.html.** Load `config.js`; replace `hash()` with `SalahConfig.serialize`. Add an embed-mode
toggle: Portable (hardcoded lat/lon) vs Local self-configuring (`#local=1`, snippet includes
`allow="geolocation"`). Docs: coarse=approximate IP/tz, precise=permission (+ iframe `allow`), local-storage
caveats, TablissNG. **Acceptance:** both snippets generate correctly; existing portable behavior intact.

**P7 — qaState + smokes + docs.** Extend `qaState()` with `config{source,mode,autoDetectSource,autoDetectStatus,
storageAvailable,storageError,geoPermission,geoLastError,lat,lon,tz,label,hashOverridden,why}`. Add deterministic
config-logic smokes (load `config.js` in the harness). Update DESIGN/ARCHITECTURE/HANDOFF/README + memory.

## 5. Risk register (FMEA-lite)

| Risk | Sev | Detect | Mitigation |
|---|---|---|---|
| Refactor drifts hardcoded render | high | Smoke A/B diff | sync module-load resolve; deep-equal qaState + screenshot |
| `cacheKey` captured stale (pre-detect) | high | smoke: key reflects config | convert to function, recompute per call |
| localStorage throws (Safari private / partitioned 3rd-party iframe) | med | mock-throw smoke | every access try/catch; storageAvailable probe; in-memory apply still works |
| Detect hangs | med | manual net-kill | AbortController timeout (6 s) → fallback chain → manual |
| Gear disturbs liquid-glass header / clips card | med | screenshot + inspect | button = same box as `.buckle`; reset UA styles; no layout shift |
| Settings panel overflows 325×530 | med | screenshot | internal `overflow-y:auto`; no iframe resize |
| local=1 + stale saved config silently wrong | med | precedence smoke | local applies saved only with explicit opt-in; Reset clears |
| TDZ in atmosphere() / module-load ordering | med | console throw eval | config.js loads first; bindings set before any consumer |
| ipinfo anon rate-limit | low | status logged | GeoJS primary; ipinfo only on GeoJS failure; both fail → manual |

## 6. Adversarial self-critique (Stage 6)

- **"You can't prove byte-identical with a screenshot — the sky animates."** True. Equivalence is asserted on
  `qaState()` *stable* fields (sunEl, prayer set, geometry, wx source, config) deep-equal between A and B at the
  same `simTime`, plus a screenshot at a frozen `simTime` for layout — not the live cloud hash (the documented
  trap). Folded into P2 acceptance.
- **"`Intl` tz can disagree with the detected IP region (VPN/travel)."** Acceptable: `Intl` is the device's own
  zone and is the honest 'where the clock is'; lat/lon come from IP. If they conflict the user can correct in
  settings. Documented as a known approximation, not a bug.
- **"Loading config.js adds a render-blocking fetch → flash."** Same-origin static, parsed before the inline
  script; negligible. But if `config.js` 404s the widget must not white-screen → inline a one-line guard:
  if `window.SalahConfig` is missing, fall back to legacy hash-only parsing (degrade, log once). Folded into P2.
- **"Gear in hardcoded mode would change existing embeds."** That's why the affordance is gated to
  local/preferLocal. Hardcoded embeds get no gear, no settings, no `data-*` change → visually identical.
- **"Apply-without-reload requires re-running half of boot()."** Yes — factor the post-config pipeline
  (fetchTimings + loadWx/fetchWeather + renderMoon + render + key recompute) into a callable `applyConfig()` so
  both boot() and the settings Apply use one path (no divergence). Folded into P4.
- **"Smokes for detect/geolocation/storage-partition aren't deterministic."** Correct — those are preview/manual
  receipts; only the pure config logic (parse/serialize/validate/precedence/storage-with-mock) is unit-smoked.
  Stated honestly in the matrix (no silent cap).

**Self-critique verdict:** required fixes (frozen-sim equivalence, config.js-missing guard, single applyConfig
path) folded into the phase acceptance criteria above. Plan is executable.
