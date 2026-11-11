# R0021 completion runs (Phase B, 2026-11-11)

Driver: `tools/qa/run_r0021_native.py`. The b1–b6 runs used commit `a31346eb`. The b7 runs and the c1–c4
comparisons used `7ec004db`; that commit only fixed the informational Firefox stack classifier. Settings for every
run:

- headless;
- one browser at a time;
- fixture CSP sent as a header.

Builds compared:

- **Candidate:** the completion branch. Served `index.html` is `0f765e33…`; product bytes equal `294d2d37`.
- **Control:** `git archive 32f97b06` (pre-R0021 main), extracted outside the repository. Served `index.html` is
  `9f2fb30b…`.

Unless noted, every run used `--in-page-prayer --fragment
'#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1&simWx=3&simCloud=100&timeScale=4'`.

| Dir | Engine | Options | Result |
|---|---|---|---|
| `b1-candidate-chromium` | Chromium 148 | all cells | pass (retirement-synthetic diagnostic FAIL) |
| `b1-control-chromium` | Chromium 148 | all cells, control | fail |
| `b2-{candidate,control}-chromium-bfcache` | Chromium | `--enable-bfcache --cells retirement-bfcache` | candidate PASS, control FAIL; no bfcache restore (`BrowsingInstanceNotSwapped`, `BackForwardCacheDisabledForDelegate`) |
| `b3-{candidate,control}-chromium-reduce` | Chromium | plus `--reduced-motion` | precondition-not-met on both |
| `b4-candidate-firefox` | Firefox 153 | all cells | pass (diagnostic FAIL); initiator classes mislabelled `other` (classifier defect, fixed in `7ec004db`) |
| `b4-control-firefox` | Firefox 153 | all cells, control | fail |
| `b5-{candidate,control}-firefox-reduce` | Firefox | `--reduced-motion --cells retirement-bfcache` | precondition-not-met on both |
| `b6-candidate-{chromium,firefox}-presentation2` | both | `--cells presentation` only, without `--in-page-prayer`/`--fragment` (the cell uses its own fixed scenes and prayer record) | capture; overall `pass` is false by construction because no acceptance cell ran |
| `b7-{candidate,control}-firefox-classified` | Firefox | `--cells retirement-synthetic,retirement-bfcache` | candidate PASS, control FAIL; corrected initiator counts |
| `c1-chromium`, `c2-firefox` | — | `--compare-presentation` candidate b1/b4 vs control b1/b4 | pass (identical / within repeat noise) |
| `c3-chromium-candidate-repeat`, `c4-firefox-candidate-repeat` | — | candidate b1/b4 vs b6 | pass (repeat-noise baseline) |

Interpretation: `docs/state-contracts/R0021.md`, "Completion ledger 2026-11-11", sections D and E.
