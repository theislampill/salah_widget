# ES21-12 bounded retirement attempt (head 68891b4f, base main 32f97b06)

Chromium 148.0.7778.96 (Playwright 1.60), headless, one browser at a time, `--cells retirement` only.
Candidate is the R0021 worktree (served `index.html` `0f765e33…`). Control is a read-only checkout of `71d4a8f6`,
which has main's bytes (served `index.html` `9f2fb30b…`; report `root` label `r000f`). Fragment for every run:
`#lat=24.47&lon=39.61&tz=UTC&label=Fixture&method=4&qa=1&simWx=3&simCloud=100&timeScale=4`. Each `<run>.run.log` is
the driver's one-line summary, and `<run>/chromium-report.json` the full report.

| Run | Driver option | Precondition | Cell | Retiring JS image events by stack | CDP retiring requests |
|---|---|---|---|---|---|
| `a1-candidate-overcast-ts4` | original driver (no `--in-page-prayer`) | not met: mask constant `linear-gradient(#fff,#fff)`; prayer fetch blocked by `connect-src 'self'` | precondition-not-met | 0 | 0 |
| `a2-candidate-overcast-ts4-prayer` | `--in-page-prayer` | met | FAIL | 8 render loop | 8 |
| `a2-control-71d4a8f6-overcast-ts4-prayer` | `--in-page-prayer` | met | FAIL | 1 lifecycle dispose + 8 render loop | 9 |
| `a3-candidate-overcast-ts4-prayer-repeat` | `--in-page-prayer` | met | FAIL | 8 render loop | 8 |
| `a3-control-71d4a8f6-overcast-ts4-prayer-repeat` | `--in-page-prayer` | met | FAIL | 1 lifecycle dispose + 7 render loop | 9 (one not matched by a JS event) |

These reports predate the `initiators` field; the stack classification above was read from `retiringImages[].stack`.
The `a1` report also predates `options.inPagePrayer`. Interpretation: `docs/state-contracts/R0021.md`, section
"Base is main 32f97b06 …", and the "Review follow-up" section.
