# R0007 Firefox missing-text — causal finding (successor root, 2026-11-11)

## Observation recovered from CI (unchanged, historical)
In every inspected loss frame (e.g. ingress01 normal arm frames 338–346, F6 n59–62) exactly the text whose
`font-family` list begins with a web font disappears: `.cn`/`.nt`/`.until-prayer` (Fraunces) and everything
inheriting `--font-body` (Inter: timetable rows, footer, "left until"). Text that does not name a web font stays:
the location label (`system-ui`, src/native/index.html:295) and the monospace countdown (`.left`, line 405).
In ingress01 the Firefox status panel changes to "Transferring data from fonts.googleapis.com" on the first
blank frame.

## Local discriminator (no Playwright routing; HTTP cache untouched)
Harness: scratchpad/scripts/ff_font_delay.cjs + frame_text_series.py + dip_report.py. Page = generated
`index.html` of 1e3610d9 with only the stylesheet href pointed at a local mirror of the same Google CSS/woff2
(served by the script's own HTTP server with CSS delayed 3000 ms and fonts 1500 ms, so text is on screen before
the stylesheet activates). Headed Firefox 153.0 (Playwright 1.62 build 1538 — the CI build), 370×570, video 25 fps.

| Arm | Runs | Web-font text dip at stylesheet activation | Non-web-font text |
|---|---|---|---|
| as-is, hardware WebRender | 3 | 3/3 (1–3 frames) | never dips |
| as-is, software WebRender | 4 | 4/4 (2–3 frames) | never dips |
| control: `gfx.downloadable_fonts.enabled=false` | 4 | 0/4 | never dips |
| `gfx.downloadable_fonts.fallback_delay_short=0` | 2 | 0/2 | never dips |
| `gfx.downloadable_fonts.fallback_delay_short=1000` | 2 | 1/2: 25 frames = 1.00 s; 1/2: none (unexplained) | never dips |
| prototype remedy (gate families on loaded faces) | 4 | 0/4 (two recordings have irregular early frames) | — |

The dip begins at the `fonts.loading` event (stylesheet `media` print→all makes the @font-face rules apply to
already-painted text) and ends ~100 ms later, well before `loadingdone` (~1.5 s later).

## Cause
Gecko applies a short *block period* (pref `gfx.downloadable_fonts.fallback_delay_short`, default 100 ms) to
`font-display: swap` faces: text that resolves to a still-loading web font is painted invisible until the timer
fires, then fallback is shown, then the real font swaps in. Because the page activates its font stylesheet late
(`media="print"` → `all` on load), that block period lands on text that is already visible, producing a blank of
~100 ms on a fast machine and longer when the main thread is busy (CI: 80–360 ms). This is specified behaviour
(CSS Fonts 4 allows an "extremely small" block period for `swap`), not a Gecko defect, and it is independent of
the prayer selector. It is also independent of request routing/caching: it reproduces with no routing at all.

## Limits
- Reproduced on one Windows 11 machine, Firefox 153.0 (and the same signature on 150.0.2 was not separately
  analysed). CI runner timing was not reproduced; the CI intervals are attributed by matching signature
  (which text vanishes, when, status-panel text), not by re-running CI.
- One `fallback_delay_short=1000` run showed no dip; unexplained.
- The single Chromium row-only frame (original reordered-iframe n31) is a different signature and is NOT explained.
- The 8.141 s / 5.812 s sleep-wrapper residence in native02 is a harness/host matter and is NOT explained here.
