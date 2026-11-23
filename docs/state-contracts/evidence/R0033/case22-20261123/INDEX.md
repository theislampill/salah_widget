# R0033 smoke case 22 amendment: runs of 2026-11-23

Raw results for the case-22 instrument amendment (contract §11, last item). Each `<tree>-<engine>.jsonl` is the
verbatim stdout line of `node tools/qa/r0033_remaining_cells.cjs --cell smoke --root <tree> --out <dir> --engine
<engine> --playwright <pkg>` (the cell's JSON, with its isolation verdict). The three `base-smoke-<engine>-requests.json`
files are the request ledgers of the amended-instrument runs on the unmutated tree. Nothing is edited.

Trees (all `git archive 1fa6123a` plus one file or mutation, in a disposable copy; served `index.html` sha256 prefix
in brackets):

- `base`: the amended `tests/smoke.html` (case 22 through `calendarScene`); product unchanged [`c2c827c7e5d4`].
- `m1a`: amended smoke; product mutant "light without a presented disc": `lunarPresentation` passes `false` as
  `surfaceFailed` (M4 withholding reverted) and `SalahMoonHost.publish` no longer sets the `.mphoto` href [`eb867e551c81`].
- `m1b`: amended smoke; product mutant "disc group hidden, light on": `--moongrp` written as 0 [`1a6efc850c06`].
- `m2`: amended smoke; product mutant "no light with the disc presented": `nativeLunarPresentation` returns
  `moonlight` 0 [`780dc166ea6c`].
- `m3`: amended smoke; product mutant "unjustified light": the native `moonObject` ignores altitude and phase
  (`surfaceFailed?0:darkness`), so a new or below-horizon Moon is lit [`dedf7869ce20`].
- `old-base`, `old-m1a`: controls with the pre-amendment `tests/smoke.html` (case 22 through `scene`, off the
  viewport) on the `base` and `m1a` products.

Playwright 1.60.0, headless; Chromium 148, Firefox 150.0.2, WebKit 26.4; one browser at a time, each started through
`tools/qa/r0033_isolation.cjs`. Every Firefox run has one CONNECT to `aus5.mozilla.org:443` refused at the loopback
proxy (`refusedAtProxy` 1, `allowedOffLoopback` 0), so its strict verdict exits 3. `base-chromium` and
`base-firefox` are the second runs of those cells: the first runs (made while the full regression runner ran
alongside) were overwritten by mistake; the first Chromium run was PASS 141/0, the first Firefox run was FAIL 140/1 with
cases 21 and 22 executed and one unrelated weather assertion failed ("actual live model remains useful without
synthetic observation authority"), not reproduced in the rerun or in the four Firefox mutant runs.
