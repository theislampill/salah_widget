# 🕌 Salah Widget

A tiny, self-contained prayer-times widget you can embed anywhere that accepts an
`<iframe>` — built for [TablissNG](https://github.com/BookCatKid/TablissNG) new-tab
dashboards, but works in Notion, a personal site, or anywhere else.

No build step, no dependencies, no tracking. One static HTML file that reads its
configuration from the URL and fetches times from the free
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
  style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden"
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
# Windows PowerShell
irm https://raw.githubusercontent.com/theislampill/salah_widget/main/install.ps1 | iex
```

It **never** silently installs extensions or writes to browser storage — it downloads the
asset, opens the browser's own install page, and stages the preset for **manual** import. It
runs code from this repo, so review-first works too:
`curl -fsSLO …/install.sh` → `less install.sh` → `bash install.sh`.
**Note:** importing the preset *replaces* your current TablissNG dashboard with a clean layout
containing the widget; precise in-widget location additionally needs the iframe's
`allow="geolocation"` (some hosts strip it — coarse auto-detect still works).

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
  style="width:330px;height:534px;border:0;border-radius:28px;overflow:hidden"
  scrolling="no">
</iframe>
```

The in-widget settings panel supports location (name, latitude, longitude), calculation
method, Asr school, 12/24-hour, date format, and temperature units. A **location pin** beside
the location field shows the source — **red** = estimated from your IP (the default),
**glowing** = precise GPS (tap it to request browser permission), **grey** = manually set.
Type a place name to **search** (Enter cycles multiple matches; **Shift+Enter** keeps a custom
display name without moving the coordinates). Changes **save automatically** when you close the
panel; the **↺** icon resets (clears your saved settings and re-detects).

### Modes & precedence

| Mode | URL | Behaviour |
|------|-----|-----------|
| **Hardcoded** | `#lat=…&lon=…` | Fixed location baked into the URL. Unchanged, classic behaviour. A saved local config **never** overrides it. |
| **Local** | `#local=1` | Saved local config → else coarse auto-detect → else in-widget manual setup. |
| **Prefer-local** | `#preferLocal=1` | Like hardcoded, but a saved local config (if any) **may** override the hash defaults — because the URL explicitly opted in. |

Resolution order: explicit hardcoded hash (unless `local=1`/`preferLocal=1`) → saved local
config → coarse IP/timezone detect → manual setup → safe error state.

### Auto-detect, precise location & privacy

- **Coarse auto-detect is approximate** — it's based on your **IP address and timezone**, not
  GPS. It necessarily sends your IP to the geolocation provider
  ([GeoJS](https://www.geojs.io/), with [ipinfo.io](https://ipinfo.io) as a fallback); this
  widget itself does no tracking and stores nothing about you on any server. We say
  **"estimated area,"** never "precise location."
- **Precise location is optional and user-triggered.** The "Use precise location" button asks
  your browser's permission (`navigator.geolocation`) — it is **never** called automatically.
  In an iframe it usually requires `allow="geolocation"` on the `<iframe>` (the local-mode
  snippet from the builder includes it). If a host (e.g. TablissNG) strips that attribute or
  you deny permission, the widget falls back gracefully — coarse auto-detect and manual setup
  still work.
- **Saved settings stay local** to your browser/profile. If storage is blocked or partitioned
  (private browsing, strict third-party-iframe storage), saving is unavailable — the widget
  says so and your changes still apply **for the current session** (it never crashes).
- **TablissNG:** coarse auto-detect works inside the iframe if your network/ad-blocker allows
  the request; precise location works only if TablissNG preserves `allow="geolocation"`;
  saved settings persist only if it doesn't partition iframe storage. All three degrade
  gracefully when not available.

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
- **Offline-friendly** — the day's times are cached in `localStorage`, so the widget
  paints instantly on reload and survives a flaky connection.
- **Auto-retry** on API hiccups, and an automatic refresh when the day rolls over.
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
weather by [Open-Meteo](https://open-meteo.com) — both free and key-less. The widget makes
direct browser requests to these APIs and stores nothing about you.
