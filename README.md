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

- **Current model weather** — Open-Meteo condition and temperature in the header
  are current model estimates, not direct local observations. A missing, null or
  invalid temperature stays blank; genuine numerical zero displays `0°`.
  Celsius, Fahrenheit and legitimate negative temperatures remain supported.
  A valid condition can remain visible when optional measurements are unavailable.
  Invalid or missing precipitation cannot authorize wet effects; a genuine zero
  is a valid dry amount. Eligible quantities can support labelled model rain or
  snow, while a thunder condition alone cannot authorize lightning. These value
  rules require no new provider, configuration field, cache migration or installer
  change.
  Freshness uses the model's source-valid `current.time` in the captured request
  timezone, its positive preceding-interval duration, and retrieval time separately.
  Both source and retrieval ages must be between zero and **15 minutes, inclusive**;
  even a timestamp 1 ms in the future is ineligible. A new download cannot renew
  an old source record. Invalid or expired current data shows an em dash and blank
  temperature and stops unsupported clouds, rain/snow particles and lightning.
  Optional missing precipitation alone does not invalidate an otherwise eligible
  model condition. Client clock skew can temporarily withhold useful data.
  Radar retains mosaic frame-generation, index-generation and retrieval times
  separately: frame and retrieval ages each have an inclusive **20-minute** limit,
  with no future allowance. Index time never replaces a missing frame time.
  Valid timestamps do not establish local radar coverage or ground observation;
  imagery remains unitless and cannot authorize precipitation amounts or strikes.
- **Weather-reactive color theme** — the palette shifts with the sky: warm gold under a
  clear day, deep indigo on a clear night, muted grey when cloudy, cool steel-blue for
  rain, icy for snow, and charcoal-violet for thunderstorms. Day vs. night is derived
  from the prayer Sunrise/Sunset times, so it always matches the widget.
- **Next prayer** front and centre. The countdown measures actual elapsed time from
  the current instant to the selected prayer instant in the location's IANA time
  zone, including DST changes. The timetable, prayer arc and progress keep their
  existing wall-clock presentation. The duration rounds to the nearest second,
  then displays hours and whole minutes at one hour or more, whole minutes at one
  minute or more, and seconds below one minute.
- **Progress bar** showing how far you are through the current interval.
- **Time-zone correct** — a supplied `tz` is an initial hint. Valid selected-cache or
  prayer-provider metadata resolves the location's time zone; a timetable is accepted
  as current only for that zone's civil date at adoption. The times and countdown
  reflect the *location's* clock, no matter where you view the widget.
  If the prayer endpoint is nonexistent, ambiguous or otherwise unsupported, or
  required next-day data is missing or for the wrong day, the next-time field shows
  **—** and the countdown reads **Countdown unavailable**. The valid current-day
  timetable, date and arc remain available; no estimated tomorrow Fajr or invented
  exact time is displayed. A valid matching tomorrow record restores the countdown
  on the next eligible visible render, including in a frozen preview.
- **Cached prayer data** — only an admitted selected current-day record can paint
  current before refresh. Corrupt cache is a miss; healthy live recovery remains
  reachable. Valid wrong-day cache may resolve the zone but cannot be called current.
  Valid current data survives a failed refresh or denied persistence. Existing
  `salah:lat|lon|_cacheTz|method|school` bytes remain compatible without scanning,
  purging or migration; this is not an offline-application guarantee.
  The selected legacy key retains the configuration's initial zone component even
  after the location zone resolves. A zone-free key is not a replacement for it.
  With no usable cached zone, boot may request the hint's day first. Valid metadata
  can then require one corrected current-day request; the bootstrap day's record
  cannot be displayed as current for a different resolved civil date.
- **Invalid prayer records** — Fajr, Sunrise, Dhuhr, Asr, Maghrib and Isha all
  require valid clocks, a matching Gregorian date and a usable IANA time zone.
  Malformed records and unsuccessful or contradictory provider responses are
  rejected before adoption or caching. Sunset is optional, with Maghrib as its
  fallback. Supported parenthesized clock suffixes and equal or reordered polar
  schedules remain valid; increasing event order is not required. With no usable
  current record, the six timetable rows and next time show **—** rather than
  invented times. Healthy same-day data restores the timetable without a reload
  at the next eligible visible recovery opportunity described below.
- **Bounded retry** — each prayer operation has at most three attempts, with
  900/1800 ms backoffs and a 10000 ms deadline for the full asynchronous fetch/body
  attempt. Bootstrap and corrected-day requests share that budget. Three timeouts
  total a nominal 32.7 seconds (32700 ms), plus event-loop scheduling; timers cannot
  preempt synchronous parsing or a blocked event loop. This is neither a hard
  real-time CPU guarantee nor a guarantee of provider latency.
  Same-day no-data recovery and failed tomorrow acquisition use a 60-second
  operation-start cadence on `performance.now()` hosts, with busy ownership preventing
  overlap. A valid matching tomorrow suppresses redundant requests; day and generation
  changes reclassify eligibility. Hidden/offscreen loops pause, so the first resumed
  eligible opportunity starts one operation without background or catch-up guarantees.
  Real elapsed eligibility is independent of `simTime`, `timeScale` and wall-clock
  correction. The retained `Date.now()` fallback is not claimed monotonic.
  Day rollover and settings changes recheck the response's day and request owner
  before adoption. If the day moves again during correction, the original operation
  settles without another correction; existing bounded recovery remains eligible.
  Accepted changes mark the prayer presentation dirty for the next visible render.
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
  The deadline continues through JSON body consumption: receiving HTTP 200
  headers does not restart or remove it. A timed-out refresh cannot renew an
  accepted record's source or receipt time. If current weather expires, its
  temperature becomes unavailable; an hourly forecast or recovered radar image
  cannot replace it. A later eligible current response must pass admission
  before restoring the weather display. Open-Meteo recovery remains a model
  estimate, not proof of observed local precipitation.
  The weather cache's six-hour retention window is storage compatibility, not
  live authority. Retained legacy records without valid source metadata remain
  unavailable until a healthy eligible response arrives; failed refreshes cannot
  renew their source or receipt time. Prayer-cache rules are separate. These
  caches do not make the widget a self-contained offline app.
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
  Missing or malformed optional Hijri data does not invalidate the six required
  prayer times. Without a usable selected Hijri date, its value is **Hijri date
  unavailable**; the compact footer may truncate it, and **Calendar dates** shows
  the complete explanation. Structural checks require month 1–12, day 1–30 and
  a positive integer year; they do not calculate a religious calendar.
  Name-bearing formats require a string month name; numeric-only formats do not.

Click or tap either CE or AH date, or Tab to it and press Enter or Space, to open **Calendar dates**. It shows both complete selected dates, any preview and the current explanation. Scroll and select long values to read their full text. Close or Escape dismisses the view and returns focus to the date that opened it. Reading dates does not apply settings, save data or request another calendar value.

---

## Files

| File           | Purpose |
|----------------|---------|
| `index.html`   | The widget itself. |
| `builder.html` | Interactive embed-code generator (portable **and** self-configuring snippets). |
| `config.js`    | Shared `WidgetConfig` module (`window.SalahConfig`) — parse / validate / serialize / load-save local config / coarse auto-detect. Loaded by both `index.html` and `builder.html` so config logic can't fork. |
| `install.sh` / `install.ps1` | Optional setup wizard (macOS-Linux / Windows): detects the browser, downloads the TablissNG extension asset, and stages the preset for manual import. No silent installs. |
| `presets/salah-widget.tablissng.json` | A ready-made TablissNG dashboard export (this widget in self-configuring mode) that the installer imports. |

### Deterministic smoke test

The no-build [smoke page](tests/smoke.html) characterizes the widget with controlled inputs. Copy a complete candidate tree to a disposable directory and use a fresh disposable browser profile or isolated test context. Serve it on an unused loopback origin; do not use your normal widget/Pages origin or clear its storage. For example, replace the directory below with your disposable copy:

```powershell
python -m http.server 8765 --bind 127.0.0.1 --directory 'C:\path\to\disposable-tree'
```

Open each mode as a separate document:

- `http://127.0.0.1:8765/tests/smoke.html?fixture=healthy`
- `http://127.0.0.1:8765/tests/smoke.html?fixture=reject`
- `http://127.0.0.1:8765/tests/smoke.html?fixture=hang`
- `http://127.0.0.1:8765/tests/smoke.html?fixture=bootstrap-error`

`healthy` supplies matched prayer responses. `reject` rejects prayer fetches; `hang` leaves them pending. Neither negative mode can count an unconsumed response as ready. Their readiness deadline normally produces **INCOMPLETE**, with **FAIL** taking precedence if an error is recorded. `bootstrap-error` deliberately fails before widget parsing and is **FAIL**. These are separate controlled runs, not an offline skip or successful fallback.

The denominator is **30 named required callbacks**, with **141 expected assertions** in the current source. **PASS** requires every callback to finish with exactly its declared assertion count and no failed assertion or other error. The executed count includes cases recorded as `executed` or `failed`; `pending` or `missing` cases remain missing. A recorded failed assertion or callback, harness or bootstrap error makes the summary **FAIL**, even when cases are also missing. With no recorded failure, any missing case makes it **INCOMPLETE**. The `pass`/`fail` counters count assertion/error log lines, not completed callbacks; read `required.total`, `required.executed`, `required.missing` and each case in `window.__smoke`. Late callbacks cannot complete a missing case. The existing limits are 8 seconds for scene readiness, 4 seconds for a required callback and 3 seconds for Moon image decoding.

[The wrapper](tests/widget-fixture.html) installs a fresh private Map-backed `localStorage` for each fixture before product parsing; config checks receive separate private or denied stores. No test requires clearing user-origin data. It starts no-argument `Date`/`Date.now()` at **2026-09-07T09:30:00.000Z**, retains explicit date arguments (controlled cases can advance the private clock), and uses latitude **24.47**, longitude **39.61**, Madinah, method **4**, school **0**, timezone **Asia/Riyadh** and `qa=1`. Its only admitted Aladhan requests are the four-parameter timings requests for **07-09-2026** and **08-09-2026**. Synthetic timings are Fajr 05:00, Sunrise 06:00, Dhuhr 12:00, Asr 15:30, Sunset/Maghrib 18:00 and Isha 19:30. Gregorian and invented Hijri fields are test inputs, not a Hijri conversion claim. The initial 12:30 scene checks actual current Dhuhr, next Asr 15:30 and 180 minutes remaining. Weather uses a fixed Open-Meteo model input and an empty RainViewer index; admitted synthetic weather records exercise their own lane. None is a direct local weather observation.

Readiness binds the unique run, attempt, document, exact scene hash and fetched `index.html` SHA-256. It also requires actual current-day `Response.json()` consumption, the matching weather bridge and prayer/render state. An earlier iframe, matching hash alone or stale response is insufficient. Save the final summary, `window.__smoke`, every attempt's fixture/request/JSON/error ledger, browser/version and file hashes before opening the next mode. The fixture's source digest identifies the fetched index; record config, wrapper and other runtime identities separately.

The wrapper keeps product script bodies unchanged and rejects unknown script/digest/resource anchors. Its current anchors reject the inline Moon startup/refinement layout (`moon-initial-code` / `moon-refinement-code`) with **Unreviewed widget script anchors**; that entry needs a separately reviewed wrapper adaptation before this instrument can qualify it. Retain the failure rather than bypassing the guard. The fixture removes the three known external font links and its policy blocks fonts and external connections. Controlled time, synthetic providers and suppressed fonts cannot certify appearance, readability, normal-live **M0** motion, public deployment or every platform. The smoke page's scope notice and separate native/delivery gates still apply.

For an authorized public delivery check, use a separate fresh browser profile or isolated test context with no owner settings. Open the delivered HTTPS `tests/smoke.html` under the site's base URL, with each of the same four `?fixture=` modes. Bind the served README, index, config and wrapper hashes to the exact approved release; a loopback run does not supply public delivery evidence.


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
