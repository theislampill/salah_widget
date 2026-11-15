# R0034-A1 before/after evidence (our renders only)

Base `origin/main` 516d8cc8 ("main") vs the A1 candidate ("candidate"). No owner screenshot is included or derived.
Contract and acceptance ledger: `docs/state-contracts/R0034-A1.md`.

## VM matrix (deterministic, cloud-free refined raster) — `vm-scene-diff.json`, `sheets/vm-*.png`

`node tools/qa/r0034_a1_scene_diff.mjs --base origin/main --out <dir>`. Each sheet: main | candidate | per-pixel
max-channel code difference ×16. File tags are UTC: Orlando (EST, UTC−5) 1526 = 10:26, 1714 = 12:14, 2045 = 15:45,
2115 = 16:15, 2210 = 17:10, 2255 = 17:55, 2340 = 18:40, 0300 = 22:00; Madinah (UTC+3) 0530 = 08:30, 0830 = 11:30,
1330 = 16:30, 1440 = 17:40. `vis20` / `vis6` = 20 km / 6 km visibility.

## Native (frozen instant; composite + raw refined canvas) — `native-summary.json`, `sheets/native-*.png`

`tools/qa/r0034_artifact_probe.cjs` with a `freeze:true` plan, served base and candidate trees from loopback; all
non-loopback requests aborted; Playwright Firefox 150, Chromium 148, WebKit; DPR 1 (and 1.5 for the owner scene);
headed Firefox for the owner scene. Sheets: `-card` (main | candidate, kept for Firefox only), `-crop2x` (card
x 0–200, y 230–420 at 2×), `-resid12` (luminance minus σ 25 Gaussian ×12, card x 12–317, y 245–430). Scene tags:
`orl1026` (owner scene), `orl1026dpr15`, `orl1214v6` (12:14, 6 km), `orl1545` (Sun 20°, off-camera), `orl1755`
(twilight), `mad1130` (Madinah 11:30). Native composites carry live cloud capture noise (main-vs-main 4–7 codes in
rows < 183, ≤ 1 code below); byte identity is decided by the VM matrix.

## Suites

See the candidate's final report and `docs/state-contracts/R0034-A1.md`.
