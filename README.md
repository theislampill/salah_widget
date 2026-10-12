# 🕌 Salah Widget

A compact prayer-times widget you can embed anywhere that accepts an
`<iframe>` — built for [TablissNG](https://github.com/BookCatKid/TablissNG) new-tab
dashboards, but works in Notion, a personal site, or anywhere else.

Static delivery, with saved configuration in browser storage and service requests described below. Configuration comes from the URL;
prayer times come from the free [Aladhan API](https://aladhan.com/prayer-times-api).
This **CP9 integration candidate is not the deployed main version**. It adds an
admitted star catalogue and physical sky in an optional worker while preserving
the prayer widget. See [integration, evidence and open gates](docs/real-sky/INTEGRATION.md).

For development, edit `src/native/` and the authored `real-sky/native-*` adapters,
then run `python tools/build_native.py`. Serve with `python -m http.server 8000`
and open `http://localhost:8000/index.html`. `offline.html` embeds sky assets for
local file entry; live prayer/weather and fonts still need network access.
Root entries and sky bundles are generated; do not hand-edit them.

**Live widget:** <https://theislampill.github.io/salah_widget/>
**Build your own embed:** <https://theislampill.github.io/salah_widget/builder.html>

---

## Quick start

The easiest path is the **[builder page](https://theislampill.github.io/salah_widget/builder.html)** —
it auto-detects your time zone, can use your browser location, shows a live preview,
and gives you a copy-paste snippet.

Or write the iframe yourself:

```html
<iframe
  title="Prayer Times"
  referrerpolicy="no-referrer"
  src="https://theislampill.github.io/salah_widget/#lat=24.4672&lon=39.6142&tz=Asia%2FRiyadh&label=Madinah&method=4&school=0"
  style="width:325px;height:530px;border:0;border-radius:28px;overflow:hidden"
  scrolling="no">
</iframe>
```

Everything after the `#` is configuration — change it to your own location.

### Using it in TablissNG

TablissNG can't run scripts, but it can embed an iframe. Add an **HTML / iframe**
widget and paste the snippet above (with your own coordinates).

### One-line install (optional setup wizard)

Don't want to set TablissNG up by hand? A small installer detects your browser, downloads the
right TablissNG extension asset, and stages a ready-made preset (this widget in
self-configuring mode) for you to import. The **Install widget** button on the
[builder](https://theislampill.github.io/salah_widget/builder.html) copies the command for
your OS:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/theislampill/salah_widget/main/install.sh | bash
```
```powershell
# Windows PowerShell 5.1 (powershell.exe), or supported PowerShell 7 (pwsh.exe)
irm https://raw.githubusercontent.com/theislampill/salah_widget/main/install.ps1 | iex
```

The Windows response-string command executes the downloaded text in the host
where you paste it. Windows PowerShell 5.1 is the declared minimum; the retained
PowerShell 7 qualification is version 7.6.6. The commands below use one selected
host. Your execution policy still applies; a policy refusal is not installation.

If you configured the widget in the builder, **Install widget** carries its
encoded settings through `SALAH_WIDGET_HASH` into the preset iframe. For a
reviewed local-file invocation, keep that environment value, or pass
`-WidgetHash` on Windows, if you want the same configuration.

The wizard downloads and stages files, offers clipboard paths and opens the
browser's manual pages. Extension installation and preset import remain manual;
it does not silently install extensions or write to browser extension storage.
**Importing the preset replaces your current TablissNG dashboard** with the
widget layout. Precise in-widget location also needs the iframe's
`allow="geolocation"`; hosts may strip it, while coarse auto-detect still works.

It runs code from this repo, so review-first works too:
`curl -fsSLO …/install.sh` → `less install.sh` → `bash install.sh`.

#### Review a pinned file first

These examples download the installer at a pinned source commit. Read it,
use the optional offline preview, then run normal mode when ready:

On Windows, `Invoke-WebRequest -OutFile` keeps the downloaded file bytes. Review
with `Get-Content -LiteralPath`; do not resave the file through
`Get-Content`/`Set-Content` or change its encoding. Choose either host below:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/theislampill/salah_widget/18ff14860ff41c084b1db5f396bb62aa9c22b1be/install.ps1" -OutFile ".\install.ps1"
Get-Content -LiteralPath ".\install.ps1"
powershell.exe -NoProfile -File ".\install.ps1" -DryRun
powershell.exe -NoProfile -File ".\install.ps1"
```

For the supported PowerShell 7 host, replace the two `powershell.exe` calls with
`pwsh.exe -NoProfile -File ".\install.ps1" -DryRun` and
`pwsh.exe -NoProfile -File ".\install.ps1"`. Run one host's normal command.

With reviewed local files, `-DryRun` performs offline local discovery and prints
planned actions. Preview creates no staging or usable artifacts and is neither
installation nor staged completion.

---

## Self-configuring (local) mode

If you don't want to hard-code coordinates — e.g. a generic embed that anyone can drop in —
use **local mode**. Add `#local=1` to the URL and the widget will:

1. try a **coarse, permission-free area auto-detect** (approximate, IP/timezone-based),
2. show prayer times for that estimated area,
3. let the viewer **open settings inside the widget** (tap/click the header buckle — it
   morphs into a ⚙ gear on hover/focus; keyboard `Enter`/`Space` and touch work too) to
   correct the location or any setting,
4. **save their choice locally** (in their own browser) for next time.

```html
<iframe
  title="Prayer Times"
  src="https://theislampill.github.io/salah_widget/#local=1"
  allow="geolocation"
  style="width:325px;height:530px;border:0;border-radius:28px;overflow:hidden"
  scrolling="no">
</iframe>
```

A generic `#local=1` embed chooses method and units automatically after area detection. A local embed exported by the builder includes the selected method and temperature units as defaults for a viewer with no saved configuration, for example `#local=1&method=2&units=f`. An existing saved configuration in that viewer’s browser takes priority over those defaults. The generic preset remains `#local=1`.

The in-widget settings panel supports location (name, latitude, longitude), calculation
method, Asr school, 12/24-hour, date format, and temperature units. A **location pin** beside
the location field identifies an estimated area, browser/saved browser position, or manually
selected site. Its title reports available accuracy in metres and original fix age; tap it
to request a browser position.
Type a place name to **search** (Enter cycles multiple matches; **Shift+Enter** keeps a custom
display name without moving the coordinates). Changes **save automatically** when you close the
panel. If persistence fails, changes apply for this session and Settings retains a warning. The **↺** icon removes only saved widget configuration and then re-detects if removal succeeds; prayer/weather caches and provider-held data are unaffected.

### Modes & precedence

| Mode | URL | Behaviour |
|------|-----|-----------|
| **Hardcoded** | `#lat=…&lon=…` | Fixed location baked into the URL. Unchanged, classic behaviour. A saved local config **never** overrides it. |
| **Local** | `#local=1` | Saved local config → else coarse auto-detect → else in-widget manual setup. |
| **Prefer-local** | `#preferLocal=1` | Like hardcoded, but a saved local config (if any) **may** override the hash defaults — because the URL explicitly opted in. |

Resolution order: explicit hardcoded hash (unless `local=1`/`preferLocal=1`) → saved local
config → coarse IP/timezone detect → manual setup → safe error state.

### Auto-detect, precise location & privacy

Saved configuration uses this browser's storage. Local persistence does not prevent external requests: the table below describes the current recipients, triggers and sent fields. This is a description of source construction and caller controls, not a new transmission trace. Connection IP accompanies external requests. Provider retention or handling is not established by this widget-source description.

| Request group | Trigger | Recipient | Sent fields and limits |
| --- | --- | --- | --- |
| Approximate area detection | Builder initialization; widget coarse-detection paths, including local/preferLocal resolution and Reset re-detection when the resolver requires it. | GeoJS `https://get.geojs.io/v1/ip/geo.json`, then `https://ipinfo.io/json` on failure. | Connection IP; neither URL has typed-query or coordinate parameters. IANA timezone detection uses local `Intl`. IP-derived area is approximate and is not precise permission or GPS. |
| Place/postcode search | Builder one-second debounce or Enter; widget Settings Enter. Trimmed queries shorter than 2 make no request. | Nominatim `https://nominatim.openstreetmap.org/search` | `q` contains the trimmed query; `format=jsonv2`, `addressdetails=1`, `limit=5`. `countrycodes` is the known home country only for a query containing a digit; alphabetic London has no digit-country bias. |
| Canadian-style prefix assist | Whitespace removed from a query with a leading letter-digit-letter pattern; in addition to Nominatim. | Zippopotam `https://api.zippopotam.us/ca/<FSA>` | First 3 matched characters, uppercased: `M5V2T6` → `/ca/M5V`. No complete postcode or widget coordinates are appended. This is a prefix test, not complete-postcode validation; malformed longer queries with that prefix also trigger it. |
| Builder coordinate reverse lookup | Eligible coordinate edits after 700 ms debounce, or permission-granted builder location acquisition. Stale/non-numeric coordinates and both automatic label/method controls off produce no request. | BigDataCloud `https://api.bigdatacloud.net/data/reverse-geocode-client` | `latitude`, `longitude`, `localityLanguage=en`, e.g. `51.5`/`-0.12`. This is the builder caller; in-widget browser location does not invoke builder reverse geocoding. |
| Prayer requests | Eligible date-specific prayer acquisition, subject to existing cache/currentness rules. | Aladhan `https://api.aladhan.com/v1/timings/<date>` | `latitude`, `longitude`, `method`, `school`; requested date in the path. |
| Weather requests | Eligible active current/hourly acquisition, subject to cache, simulation and currentness guards. | Open-Meteo `https://api.open-meteo.com/v1/forecast` | `latitude`, `longitude`, `timezone`, `temperature_unit` (celsius/fahrenheit), `wind_speed_unit=ms`, `forecast_days=3`, and the current/hourly field selections listed below. These requests do not establish direct local precipitation observation. |
| Radar evidence requests | Eligible manifest, then returned latest-past frame/tile under existing weather guards. | RainViewer `https://api.rainviewer.com/public/weather-maps.json` and returned tile host/frame. | Returned host + frame path + `/256/<z>/<x>/<y>/2/1_1.png`; x/y indices derive from coordinates and disclose a location-derived area. The manifest has no coordinate query. Image alpha is not millimetres or direct local observation. |
| Font loading | Page stylesheet/font loading, subject to cache/network policy. | Google Fonts stylesheet `fonts.googleapis.com` and font resources `fonts.gstatic.com`. | Family/style/weight stylesheet request and returned font-resource URLs; no widget location/search fields in these source URLs. Cache-dependent declarations do not mean every font is fetched on every load. |

Open-Meteo's exact selected fields are:

```text
current=temperature_2m,apparent_temperature,relative_humidity_2m,dew_point_2m,wind_speed_10m,wind_direction_10m,wind_gusts_10m,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,visibility,is_day,weather_code,precipitation,rain,showers,snowfall
hourly=temperature_2m,apparent_temperature,relative_humidity_2m,dew_point_2m,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation,weather_code,visibility,is_day
```

- **Browser location is optional and user-triggered.** The location pin requests one browser position after permission. Its reported accuracy may be known in metres or unknown; five decimal places do not measure accuracy. In an iframe, the local snippet includes `allow="geolocation"`, and the embedding parent's Permissions Policy and user grant also apply. Stripping delegation or restricting parent policy can block acquisition; coarse/manual setup remains available.
- **Acquisition and saving are separate.** A browser position retains its original acquisition time and reported accuracy; a saved browser position is a stored target and does not establish current presence. Saving settings does not renew a fix. Missing, malformed, nonpositive or future acquisition timestamps stay unknown; future timestamps have zero skew allowance against `Date.now()`. Portable URLs describe a configured destination and omit private acquisition history.
- **Storage outcome is measured.** Saved settings use this browser's storage. If writing is unavailable, changes still apply for the current session and Settings shows a retained warning. A partition can be writable and retain settings within that partition. Saving and persistence depend on the host's actual storage permissions and lifetime; blocked writes cause the session-only warning.
- **Reset scope.** Reset removes only the saved widget configuration (`salah_widget:config:v1`); it does not erase prayer/weather caches or data held by external providers. Successful removal may re-detect the area and issue the coarse request above. Failed removal reports the failure and leaves the existing target usable.
- **TablissNG conditions.** Coarse acquisition depends on permitted provider access; browser position depends on preserved delegation, parent policy and user grant; saving depends on writable host storage and its lifetime. These conditions are not a claim that a particular TablissNG version or partition policy has been qualified.

---

## Configuration (URL hash parameters)

| Param    | Required | Default            | Description |
|----------|:--------:|--------------------|-------------|
| `lat`    | ✅       | —                  | Latitude, e.g. `28.93084` |
| `lon`    | ✅       | —                  | Longitude, e.g. `-82.39122` |
| `tz`     |          | *auto*             | **Auto-detected from the coordinates** — you normally don't need to set it. The countdown and day-rollover use the *location's* zone (so Madinah always shows Madinah time, whatever device you view it on). Pass an IANA zone (e.g. `Europe/London`, `/` encoded as `%2F`) only as a fallback for the first paint. |
| `label`  |          | `Prayer Times`     | Location name shown on the widget. Encode spaces as `%20`. |
| `method` |          | `2` (ISNA)         | Calculation method — see table below. |
| `school` |          | `0`                | Asr calculation: `0` = standard, `1` = Hanafi (later Asr). |
| `time`   |          | `24`               | Clock format: `24` (15:45) or `12` (3:45 PM). |
| `datefmt`|          | `YYYY-MM-DD`       | Date format as a token string — `YYYY`/`YY` year, `MMMM`/`MMM`/`MM`/`M` month, `DD`/`D` day (e.g. `DD MMMM YYYY`, `MMM D, YYYY`). The old preset keys `iso`/`us`/`eu`/`long` still work. Applies to both the Gregorian and Hijri dates. |
| `units`  |          | `f`                | Weather temperature: `f` (°F) or `c` (°C). |
| `local`  |          | —                  | `#local=1` → [self-configuring mode](#self-configuring-local-mode): coarse auto-detect + in-widget settings, saved locally. When set, hash `lat`/`lon` are ignored in favour of the saved/detected config. |
| `preferLocal` |     | —                  | `#preferLocal=1` → use hash `lat`/`lon` as defaults, but let a saved local config override them (opt-in). |
| `lp`     |          | `0`                | Light-pollution dial `0`–`1` — raises the night-sky glow and erases the faintest stars / Milky Way. |

> Tip: don't know your coordinates? Right-click your location on
> [OpenStreetMap](https://www.openstreetmap.org) → **Show address**, or just use the
> 📍 button on the builder page.

### Calculation methods

| `method` | Authority |
|:--------:|-----------|
| 0  | Shia Ithna-Ashari |
| 1  | University of Islamic Sciences, Karachi |
| 2  | Islamic Society of North America (ISNA) |
| 3  | Muslim World League |
| 4  | Umm al-Qura University, Makkah |
| 5  | Egyptian General Authority of Survey |
| 7  | Institute of Geophysics, University of Tehran |
| 8  | Gulf Region |
| 9  | Kuwait |
| 10 | Qatar |
| 11 | Majlis Ugama Islam Singapura, Singapore |
| 12 | Union des Organisations Islamiques de France |
| 13 | Diyanet İşleri Başkanlığı, Turkey |
| 14 | Spiritual Administration of Muslims of Russia |
| 15 | Moonsighting Committee Worldwide |
| 16 | Dubai |

---

## Features

- **Live local weather** — current condition and temperature (from Open-Meteo) shown in
  the header.
- **Weather-reactive color theme** — the palette shifts with the sky: warm gold under a
  clear day, deep indigo on a clear night, muted grey when cloudy, cool steel-blue for
  rain, icy for snow, and charcoal-violet for thunderstorms. Day vs. night is derived
  from the prayer Sunrise/Sunset times, so it always matches the widget.
- **Next prayer** front and centre with a live, per-second countdown.
- **Progress bar** showing how far you are through the current interval.
- **Time-zone correct** — the time zone is resolved from the coordinates, so the times and
  countdown always reflect the *location's* clock, no matter where you view the widget.
- **Cached prayer data** — only an admitted selected current-day record can paint
  current before refresh. Corrupt cache is a miss; healthy live recovery remains
  reachable. Valid wrong-day cache may resolve the zone but cannot be called current.
  Valid current data survives a failed refresh or denied persistence. Existing
  `salah:lat|lon|_cacheTz|method|school` bytes remain compatible without scanning,
  purging or migration; this is not an offline-application guarantee.
- **Bounded retry** — each prayer operation has at most three attempts, with
  900/1800 ms backoffs and a 10000 ms deadline for the full asynchronous fetch/body
  attempt. Bootstrap and corrected-day requests share that budget. Three timeouts
  total a nominal 32700 ms, plus event-loop scheduling; timers cannot preempt
  synchronous parsing or a blocked event loop and do not guarantee provider latency.
  Same-day no-data recovery and failed tomorrow acquisition use a 60-second
  operation-start cadence on `performance.now()` hosts, with busy ownership preventing
  overlap. A valid matching tomorrow suppresses redundant requests; day and generation
  changes reclassify eligibility. Hidden/offscreen loops pause, so the first resumed
  eligible opportunity starts one operation without background or catch-up guarantees.
  Real elapsed eligibility is independent of `simTime`, `timeScale` and wall-clock
  correction. The retained `Date.now()` fallback is not claimed monotonic.
- **Weather retry** — fetch plus JSON body consumption shares one 10-second application
  attempt. A radar manifest fetch plus JSON body shares a separate 10-second
  attempt; once accepted, a new 10-second Image attempt covers dispatch and
  result consumption. The nominal combined radar application wait is at most
  20 seconds while JavaScript is runnable; this is not a hard wall-time recovery
  guarantee during blocked/suspended execution or scheduling delays.
  Weather retry is eligible after 60 seconds and radar after 10 minutes from
  their respective last attempt starts, using the existing client wall clock.
  An eligible current record plus a retained hourly track can skip weather
  refetch for less than 15 minutes after the last accepted current receipt.
  Valid coordinates and free request ownership still matter. The ordinary
  visible render loop offers approximately 30-second opportunities outside an
  advancing sweep; eligibility and timeout release are not immediate retry or
  successful recovery.
  On performance-clock hosts, the absolute elapsed attempt deadline is checked
  as well as the timer: a late fetch/body/Image completion is rejected even if
  suspension delayed timer delivery. The existing `Date.now()` fallback is a
  wall clock and is not promised to be monotonic. Timeouts settle the wrapper,
  release ownership and ignore late results; abort is best effort and detached
  Image handlers do not prove physical cancellation of every download. No
  provider-health, offline-service or memory-recovery guarantee is implied.
- Passed prayers dim; the upcoming one is highlighted.
- Gregorian (CE) date bottom-left and Hijri (AH) date bottom-right, in your chosen
  `datefmt` (defaults to ISO `YYYY-MM-DD`).

---

## Files

| File           | Purpose |
|----------------|---------|
| `index.html`   | The widget itself. |
| `builder.html` | Interactive embed-code generator (portable **and** self-configuring snippets). |
| `config.js`    | Shared `WidgetConfig` module (`window.SalahConfig`) — parse / validate / serialize / load-save local config / coarse auto-detect. Loaded by both `index.html` and `builder.html` so config logic can't fork. |
| `install.sh` / `install.ps1` | Optional setup wizard (macOS-Linux / Windows): detects the browser, downloads the TablissNG extension asset, and stages the preset for manual import. No silent installs. |
| `presets/salah-widget.tablissng.json` | A ready-made TablissNG dashboard export (this widget in self-configuring mode) that the installer imports. |

---

## Credits

Prayer time calculations by the [Aladhan API](https://aladhan.com/prayer-times-api), and
weather by [Open-Meteo](https://open-meteo.com) — both free and key-less. These
browser requests carry the configured location and request context. Settings
and caches are stored in the browser when storage is available.
Provider retention or handling is not established by this widget-source description.

## Preserved V1 compatibility URL

After the preservation PR is merged and Pages deploys, `/salah_widget/v1/` serves
the frozen pre-overhaul application. The root URL remains the current version.
V1's clock, location, prayer timetable, weather and externally hosted fonts remain
live. Local settings and caches use V1-specific keys; valid existing root settings
are copied once without changing root data.

```html
<iframe
  title="Prayer Times"
  referrerpolicy="no-referrer"
  allow="geolocation"
  src="https://theislampill.github.io/salah_widget/v1/#local=1"
  style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden"
  scrolling="no">
</iframe>
```

For the current version, change only `src` to
`https://theislampill.github.io/salah_widget/#local=1`.
The iframe dimensions and internal card layout are unchanged.
See [preservation provenance, validation and limitations](docs/V1_PRESERVATION.md).
