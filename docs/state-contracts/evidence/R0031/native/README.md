# R0031 native evidence (R31-13 builder cells, R31-09 wrapper)

Recipe: `node tools/qa/run_r0031_native.cjs --root <tree> --out <fresh dir> --engines chromium,firefox,webkit --playwright <global playwright package>`
(Playwright 1.60.0; Chromium 148.0.7778.96, Firefox 150.0.2, WebKit 26.4; zone Asia/Riyadh; clock installed at
2026-09-07T09:00Z; every external request fulfilled from a fixture, answered 503, or aborted; no real provider).

- `branch/` — candidate tree (`builder.html`, `config.js`, `index.html` SHA-256 in `report.json` `inputs`): 18/18 cells PASS.
- `main/` — control on `91c60ed2` (`git archive`): `non-ok`, `empty` and `local` FAIL in all three engines
  (429 + NA body flips method 4 → 2; `{}` flips 2 → 4; two BigDataCloud requests from local mode); `boot`, `na`,
  `wrapper` PASS. The recipe discriminates.
- Crops: Chromium only (Firefox/WebKit crops were captured but are not retained to keep the evidence small; their
  `wrapper` cells pass with the same 325×530 box and snippet style). The crop shows the builder form, the 325×530
  preview wrapper and the exported snippet; the widget content inside the preview iframe is not rendered at the
  capture moment and is not claimed. The form state differs between the trees by design (main adopted the
  non-OK and empty replies); the snippet style is identical:
  `width:325px;height:530px;border:0;border-radius:28px;overflow:hidden`.
- In the branch crop the label reads "Newark" with coordinates 51.5/-0.12: the pin fix was taken in
  self-configuring mode, which no longer names the place (D-31-1 A).
