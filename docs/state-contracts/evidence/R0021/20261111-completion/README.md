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

## Review follow-up runs

Driver `9a070e65` was used for the b8 runs. `d6af6493` fixed two driver defects found in b8 and was used for every
later run:

- **b8-control `moon-asset-failure`:** it failed only because the pre-R0021 runtime has no `disposed` field.
- **b8-candidate rAF split:** the record read `null` instead of 0.

| Dir | Options | Result |
|---|---|---|
| `b8-{candidate,control}-chromium` | all cells, including `moon-asset-failure` and the clear-sky presentation scenes | candidate pass; control fail (its `moon-asset-failure` FAIL is the field defect above) |
| `b9-{candidate,control}-firefox` | all cells | candidate pass; control fail; `moon-asset-failure` PASS on both trees |
| `b10a`, `b10b-{candidate,control}-chromium-headed-bfcache` | `--headed --enable-bfcache --cells retirement-bfcache` | real bfcache restore (`persisted:true`); candidate PASS, control FAIL (1 retirement image) |
| `b11-{candidate,control}-firefox-headed` | `--headed --cells retirement-bfcache` | `persisted:false`; candidate PASS; control precondition-not-met |
| `b12-{candidate,control}-chromium` | `--cells retirement-bfcache,moon-asset-failure` | rAF split re-run: candidate PASS/PASS; control FAIL (CSP-blocked retirement image) / PASS |
| `n2-mutant-skip-dispose-census-chromium` | `--root` scratch mutant (asset reset skips predecessor disposal), `--cells first-boot,census` | census FAIL (peak 4 refined canvases and workers): the positive control works |
| `b13-{candidate,control}-chromium-reduce-realclock` | `--reduced-motion`, no `timeScale` | precondition-not-met on both |
| `b14-{candidate,control}-chromium-reduce-published` | `--reduced-motion --precondition published` | PASS on both: 0 retiring images, non-discriminating |
| `b15-{candidate,control}-firefox-reduce-published` | same, Firefox | PASS on both: non-discriminating |
| `c5-chromium`, `c6-firefox` | `--compare-presentation`, b8 / b9 candidate vs control | pass (6 scenes) |

Redaction: five run logs (b8 and b12 of both trees, plus b13-candidate) contain harmless `ConnectionAbortedError`
tracebacks from the fixture HTTP server. Two prefixes in those tracebacks were replaced: the local Python installation prefix with `<python>`,
and the repository checkout path with `<repo>`. Nothing else in any log was changed.

Interpretation: `docs/state-contracts/R0021.md`, "Completion ledger 2026-11-11", sections D, E and F.
