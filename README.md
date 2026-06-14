# 🕌 Salah Widget

A tiny, self-contained prayer-times widget you can embed anywhere that accepts an
`<iframe>` — built for [TablissNG](https://github.com/BlieNuckte/tabliss) new-tab
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
  src="https://theislampill.github.io/salah_widget/#lat=28.93084&lon=-82.39122&tz=America%2FNew_York&label=Central%20FL&method=2&school=0"
  style="width:330px;height:285px;border:0;border-radius:28px;overflow:hidden"
  scrolling="no">
</iframe>
```

Everything after the `#` is configuration — change it to your own location.

### Using it in TablissNG

TablissNG can't run scripts, but it can embed an iframe. Add an **HTML / iframe**
widget and paste the snippet above (with your own coordinates).

---

## Configuration (URL hash parameters)

| Param    | Required | Default            | Description |
|----------|:--------:|--------------------|-------------|
| `lat`    | ✅       | —                  | Latitude, e.g. `28.93084` |
| `lon`    | ✅       | —                  | Longitude, e.g. `-82.39122` |
| `tz`     |          | `America/New_York` | IANA time zone, e.g. `Europe/London`. URL-encode the `/` as `%2F`. |
| `label`  |          | `Prayer Times`     | Location name shown on the widget. Encode spaces as `%20`. |
| `method` |          | `2` (ISNA)         | Calculation method — see table below. |
| `school` |          | `0`                | Asr calculation: `0` = standard, `1` = Hanafi (later Asr). |
| `time`   |          | `12`               | Clock format: `12` (3:45 PM) or `24` (15:45). |
| `units`  |          | `f`                | Weather temperature: `f` (°F) or `c` (°C). |

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
- **Time-zone correct** — the countdown uses the configured `tz`, so it's accurate even
  if the device's clock is set to a different zone.
- **Offline-friendly** — the day's times are cached in `localStorage`, so the widget
  paints instantly on reload and survives a flaky connection.
- **Auto-retry** on API hiccups, and an automatic refresh when the day rolls over.
- Passed prayers dim; the upcoming one is highlighted.
- Hijri date shown alongside the Gregorian date.

---

## Files

| File           | Purpose |
|----------------|---------|
| `index.html`   | The widget itself. |
| `builder.html` | Interactive embed-code generator. |

---

## Credits

Prayer time calculations by the [Aladhan API](https://aladhan.com/prayer-times-api), and
weather by [Open-Meteo](https://open-meteo.com) — both free and key-less. The widget makes
direct browser requests to these APIs and stores nothing about you.
