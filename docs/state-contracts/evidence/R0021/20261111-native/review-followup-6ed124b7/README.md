# Review follow-up runs (review of 6ed124b7)

Chromium 148.0.7778.96 (Playwright 1.60), headless, one browser at a time, `--in-page-prayer`, fragment
`#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1&simWx=3&simCloud=100&timeScale=4`. Candidate is the R0021
worktree (served `index.html` `0f765e33…`). Control is a read-only checkout of `71d4a8f6`, which has main's bytes
(served `9f2fb30b…`; report `root` label `r000f`). The driver includes the navigation precondition and the
retirement `initiators` field.

| Run | Cell | Precondition | Result | Key counts |
|---|---|---|---|---|
| `n1-candidate-navigation` | navigation (real navigation to `about:blank`) | met | PASS | 0 data:/blob: CDP requests |
| `n2-candidate-navigation` | navigation | met | PASS | 0 |
| `n1-control-71d4a8f6-navigation` | navigation | met | FAIL | 1 `data:image/png` Image request |
| `n2-control-71d4a8f6-navigation` | navigation | met | FAIL | 1 `data:image/png` Image request |
| `r1-candidate-retirement` | retirement (synthetic pagehide) | met | FAIL | retirementInitiated 0, renderLoop 8, other 0, CDP 7 |
| `r1-control-71d4a8f6-retirement` | retirement | met | FAIL | retirementInitiated 1, renderLoop 7, other 0, CDP 8 |

Interpretation: `docs/state-contracts/R0021.md`, section "Review follow-up".
