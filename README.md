# 🕌 Salah Widget

A tiny, self-contained prayer-times widget you can embed anywhere that accepts an
`<iframe>` — built for [TablissNG](https://github.com/BookCatKid/TablissNG) new-tab
dashboards, but works in Notion, a personal site, or anywhere else.

No build step or new dependency. A static HTML runtime and shared configuration module read
configuration from the URL and fetch times from the free
[Aladhan API](https://aladhan.com/prayer-times-api).

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

A small installer detects browser/profile targets, downloads a TablissNG asset when needed,
and stages a preset for **manual** browser installation/import. Normal execution needs an
interactive terminal. The Bash wizard requires a readable controlling terminal (`/dev/tty`)
for every answer; missing terminal input or EOF fails rather than acknowledging an install.

The **Install widget** button on the [builder](https://theislampill.github.io/salah_widget/builder.html)
copies an OS-specific command that fetches published `main`. It does not execute a
local checkout or an unmerged candidate. The published one-liners are:

```bash
# Bash route (macOS / Linux)
curl -fsSL https://raw.githubusercontent.com/theislampill/salah_widget/main/install.sh | bash
```
```powershell
# Windows PowerShell
irm https://raw.githubusercontent.com/theislampill/salah_widget/main/install.ps1 | iex
```

If you've configured the widget in the builder, the **Install widget** button bakes those
settings into the install (via a `SALAH_WIDGET_HASH` the wizard writes into the preset's
iframe), so you don't have to reconfigure after installing.

#### Review and preview local files

To inspect or test a candidate, use its reviewed local files. Read [install.sh](install.sh)
or [install.ps1](install.ps1) in an editor first, then run these commands from that checkout:

```bash
DRY_RUN=1 bash "./install.sh"
```
```powershell
powershell.exe -NoProfile -File ".\install.ps1" -DryRun
```

These are **offline previews**: the installer performs read-only local discovery and prints
planned actions, with no network requests, clipboard changes, browser opens, staging,
file writes, extraction or cleanup. No interactive answers are required. Release/version,
asset paths and an `ask` source choice remain unresolved until execution; no detected or
eligible target is an explicit non-success result. Downloading the script beforehand is a
separate network action. This preview contract applies to the reviewed candidate files;
a `main` one-liner is not evidence that those candidate bytes have been published.

For normal execution after review, use `bash "./install.sh"` or
`powershell.exe -NoProfile -File ".\install.ps1"` in an interactive terminal. The Windows
script requires Windows PowerShell 5.1 or later; use `pwsh.exe` for PowerShell 7 with the
same file arguments. `SALAH_WIDGET_HASH` can carry the builder's percent-encoded fragment
without the leading `#`; preserve its single quotes and encoding when using a local file.
`NO_OPEN=1` / `-NoOpen` suppress browser opening only; they do not make execution a dry-run.

Normal Bash staging uses existing `curl`, Python 3 and native `stat`/`id`/`mktemp` tools.
Native Apple Bash 3.2/macOS qualification is still incomplete; automatic staging can refuse
symlinked or untrusted home/temporary ancestry. The manual iframe/preset route remains available.

#### Keep the files needed by the browser

The Bash wizard creates fresh private scratch and a retained bundle under the validated home
directory, using `$HOME/salah-widget-install.XXXXXXXX`. Repeated asset requests within the
same attempt can reuse its validated download; a later invocation creates fresh roots and
does not adopt a cross-run shared cache or an older retained bundle as a download cache.
Only verified scratch is cleaned up. The retained bundle survives exit and partial failures;
the wizard prints its exact path and labels incomplete work.

Keep the selected Chromium directory **while the unpacked extension is installed**. Preset
JSON/Firefox XPI removal after the actual import/install is optional and manual. The Windows
wizard stages files under `%TEMP%\SalahWidgetInstaller`, rather than the Bash home bundle;
choose a durable location before using **Load unpacked** if temporary-directory cleanup
could remove it, and keep the directory the browser uses.

The wizard does not silently install extensions or directly write extension storage. Finish
the browser installation and preset import yourself; pressing Enter or staging files does
not verify those browser steps.
**Note:** importing the preset *replaces* your current TablissNG dashboard with a clean layout
containing the widget; precise in-widget location additionally needs the iframe's
`allow="geolocation"` (some hosts strip it — coarse auto-detect still works).

---

## Self-configuring (local) mode

If you don't want to hard-code coordinates — e.g. a generic embed that anyone can drop in —
use **local mode**. Add `#local=1` to the URL and the widget will:

1. reuse a valid saved configuration, or try a **coarse, permission-free area auto-detect** (approximate, IP/timezone-based),
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

The in-widget settings panel supports location (name, latitude, longitude), calculation
method, Asr school, 12/24-hour, date format, temperature units and timetable appearance.
The location pin distinguishes an estimated area, a browser position or saved browser
position, and a configured site. Browser location is a one-shot request made by your action;
reported accuracy and original acquisition time are shown when available. Saving settings does not renew
that fix. Missing accuracy or acquisition time remains unknown; editing coordinates chooses a manual site.
Type a place name to **search** (Enter cycles multiple matches; **Shift+Enter** keeps a custom
display name without moving the coordinates). Changes apply when you close the panel. A successful save
retains them in this browser/profile; a refused write leaves the choices active for this session and
reports the persistence failure. Reset attempts to remove the saved configuration before re-detection;
if removal fails, it keeps the selected configuration and reports the failure.

**Liquid glass** is the default appearance. Choose **High contrast** for a dark backing behind timetable
text. Default glass fades only elapsed prayers; future rows stay normal, with distinct current/next highlights.
High contrast keeps every row fully visible while preserving those highlights. The builder includes the
selected appearance in portable and local exports, including explicit `appearance=glass` for its default;
saved viewer settings take precedence in local/prefer-local mode.

### Modes & precedence

| Mode | URL | Behaviour |
|------|-----|-----------|
| **Hardcoded** | `#lat=…&lon=…` | Fixed location baked into the URL. Unchanged, classic behaviour. A saved local config **never** overrides it. |
| **Local** | `#local=1` | Saved local config → else coarse auto-detect → else in-widget manual setup. |
| **Prefer-local** | `#preferLocal=1` | Like hardcoded, but a saved local config (if any) **may** override the hash defaults — because the URL explicitly opted in. |

Resolution order: explicit hardcoded hash (unless `local=1`/`preferLocal=1`) → saved local
config → coarse IP/timezone detect → manual setup → safe error state.
Builder local exports include the selected method, temperature units and appearance for a fresh viewer;
a generic `#local=1` keeps automatic defaults. Portable URLs omit private acquisition metadata and describe
a configured destination, not the sender's or recipient's current device position.

### Auto-detect, precise location & privacy

Settings are stored in your browser/profile, but the widget and builder use external services.
Local storage does not make search or location-based requests local-only. Coarse detection is
approximate; precise browser location is optional and requested by your action. The requests
below depend on the feature used, cache state and network availability.

| Trigger | Recipient and fields |
|---|---|
| Builder's initial area detection; widget local/preferLocal mode when it needs detection; an accepted Reset/re-detect action | GeoJS, then ipinfo.io on failure. The request exposes the connection's IP address. The provider URLs have no user-entered location/query parameters; the device timezone is used locally in configuration resolution. |
| Builder location-name input after its search debounce or Enter; widget Settings place/postcode search on Enter | Nominatim receives the typed query as `q`. A digit-containing query may also send the current home-country bias as `countrycodes`. |
| A search whose whitespace-stripped text begins with letter-digit-letter | Zippopotam receives the uppercase first three characters in its `/ca/` path, in addition to Nominatim receiving the query. This is the implemented prefix trigger, not proof the complete input is a valid Canadian postcode. |
| Builder automatic name/method lookup after eligible coordinate input or a precise-location result | BigDataCloud `reverse-geocode-client` receives `latitude`, `longitude` and `localityLanguage=en`. The in-widget precise path itself does not call this builder reverse function. |
| Prayer-time loading and refresh for the configured location | Aladhan receives latitude, longitude, calculation method, school and requested date. |
| Weather loading and refresh when real-weather acquisition is active | Open-Meteo receives latitude, longitude, timezone, requested units and weather-field selections. |
| Radar loading and refresh when real-weather acquisition is active | RainViewer receives a weather-map manifest request; the returned tile host receives a frame/tile path whose x/y indices are derived from the configured location. |
| Page font loading, subject to browser caching | Google Fonts stylesheet/font hosts receive font resource requests. These resource URLs do not contain the widget's location or search text. |

Reset attempts to remove the saved widget configuration key. It does not clear prayer/weather
caches or erase information held by external services. Browser or embedding-host storage and
permission policies can limit persistence or precise location. This description identifies
client-side request construction; it makes no claim about providers' retention practices.

Source trace: [config.js](config.js) (`coarseDetect`, `geocodeSearch`, `clearLocal`);
[builder.html](builder.html) (`doSearch`, `fillNameFromCoords`, `locate`, `detectArea`);
[index.html](index.html) (`_runSetSearch`, `_usePrecise`, `_resetLocal`, `fetchTimings`,
`fetchWeather`, `fetchRadar` and the font declarations).

- **Precise location is optional and user-triggered.** The "Use precise location" button asks
  your browser's permission (`navigator.geolocation`) — it is **never** called automatically.
  In an iframe it usually requires `allow="geolocation"` on the `<iframe>` (the local-mode
  snippet from the builder includes it). If a host (e.g. TablissNG) strips that attribute or
   you deny permission, browser-location acquisition can be unavailable. Refusal or timeout keeps the
   selected location; coarse auto-detect and manual setup remain available. Browser geolocation does not
   prove a fresh GPS fix or that you still occupy saved coordinates.
- **Saved settings stay local** to your browser/profile, including private browser acquisition metadata.
   Portable snippets omit that history. If storage refuses access or writes, changes can still apply
   **for the current session**, with a persistence warning. Storage may be writable within a partition;
   partitioning alone does not mean writes fail or promise sharing across embedding sites.
- **TablissNG:** coarse auto-detect works inside the iframe if your network/ad-blocker allows
  the request; precise location works only if TablissNG preserves `allow="geolocation"`;
   saved settings depend on the host/browser's storage policy. A writable partition can retain settings
   within that context; it does not promise the same settings in another embed.

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
| `appearance` |      | `glass`            | Timetable appearance: `glass` (Liquid glass) or `contrast` (High contrast). Absent, legacy or unsupported values normalize to glass. |
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

- **Model estimate** — eligible Open-Meteo current data appears with `≈` and temperature in the header;
  its accessible description identifies a model estimate and unobserved local precipitation. Absent or
  expired current data shows `?`. The selected live adapters do not support local falling rain, snow,
  lightning, nearby precipitation or an arrival claim. Explicit SIM/forecast previews are separate.
- **Weather-reactive color theme** — solar geometry and eligible model cloud/temperature/humidity inputs
  influence the palette. Rain/snow/thunder palettes belong to marked previews or qualified synthetic scenes;
  they are not a live local precipitation claim. Prayer Sunrise/Sunset supplies the day/night classification.
- **Next prayer** front and centre with a per-second elapsed countdown. An unavailable or ambiguous intended
  endpoint shows “Countdown unavailable”; a usable timetable can remain visible.
- **Progress bar** showing how far you are through the current interval.
- **Location clock** — admitted prayer data supplies the selected location's timezone. Countdown resolves
  its intended endpoint there; invalid or ambiguous mappings remain unavailable.
- **Offline-friendly** — admitted selected prayer-cache data can display while refresh runs; failed refresh
  retains usable data and marks a stale prayer day separately.
- **Bounded recovery** — up to three ten-second prayer attempts with backoff; same-day retry starts are
  spaced by sixty seconds of real elapsed time while the visible loop runs. Hidden/offscreen pause does
  not provide background recovery.
- The default Liquid glass timetable fades only elapsed prayers; future rows stay normal. It outlines the
  current prayer and tints the next.
  High contrast adds local dark backing and full-opacity text while retaining the current/next highlights.
- Gregorian (CE) and provider-selected Hijri (AH) dates use your `datefmt` (default ISO `YYYY-MM-DD`). Either
  footer button opens complete values and selection context. At/after Maghrib AH advances only using a
  matching usable tomorrow record. Otherwise a usable current value carries “Sunset date update unavailable,”
  or the footer says “Hijri date unavailable.” Calendar method metadata comes from the selected payload;
  it is not inferred from the prayer calculation method.

---

## Files

| File           | Purpose |
|----------------|---------|
| `index.html`   | The widget itself. |
| `builder.html` | Interactive embed-code generator (portable **and** self-configuring snippets). |
| `config.js`    | Shared `WidgetConfig` module (`window.SalahConfig`) — parse / validate / serialize / load-save local config / coarse auto-detect. Loaded by both `index.html` and `builder.html` so config logic can't fork. |
| `install.sh` / `install.ps1` | Optional setup wizard (macOS-Linux / Windows): detects the browser, downloads the TablissNG extension asset, and stages the preset for manual import. No silent installs. |
| `presets/salah-widget.tablissng.json` | A ready-made TablissNG dashboard export (this widget in self-configuring mode) staged for you to import manually. |

---

## Credits

Prayer time calculations by the [Aladhan API](https://aladhan.com/prayer-times-api), and
weather by [Open-Meteo](https://open-meteo.com). The widget makes direct browser requests;
see [request recipients and local persistence](#auto-detect-precise-location--privacy).
