# Registered-suite drift: direct runs, 3x each (main 645b53cc clean worktree vs candidate)

| Suite | Runner argv | Main exit ×3 | Main s ×3 | Cand exit ×3 | Cand s ×3 | FAIL records main / cand | First failure (identical on both trees) |
|---|---|---|---|---|---|---|---|
| `r0001-date-sinks` | `node --test-reporter=tap tests/r0001-date-sinks.cjs` | 1/1/1 | 0.52/0.5/0.52 | 1/1/1 | 0.47/0.47/0.48 | 1 / 1 | { / "name": "missing dates expose explicit successor unavailable output", / "status": "FAIL", / "error": "el.style.getPropertyValue is not a function" |
| `r0009-date-selection` | `node --test-reporter=tap tests/r0009-date-selection.cjs` | 1/1/1 | 1.12/1.23/1.05 | 1/1/1 | 0.97/1.02/0.97 | 1 / 1 | { / "name": "wrong current context withholds the model and never relabels old AH as current", / "status": "FAIL", / "error": "el.style.getPropertyValu |
| `r0018-appearance` | `node --test-reporter=tap tests/r0018-appearance.cjs` | 0/0/0 | 0.36/0.38/0.38 | 0/0/0 | 0.34/0.38/0.36 | 0 / 0 | — |
| `r0019-date-disclosure` | `node --test-reporter=tap tests/r0019-date-disclosure.cjs` | 1/1/1 | 0.81/0.78/0.77 | 1/1/1 | 0.89/0.8/0.77 | 1 / 1 | { / "name": "missing invalid and no-model values clear previously hidden full dates", / "status": "FAIL", / "error": "el.style.getPropertyValue is not |
| `r0021-reveal` | `node --test-reporter=tap tests/r0021-reveal.cjs --cp8-snapshot-only` | 1/1/1 | 1.55/1.48/1.58 | 1/1/1 | 1.53/1.58/1.59 | 1 / 1 | PASS daytime real surface has no mask target or calendar group presence / PASS mask follows the actual transform transition and existing withdrawal du |
| `r0022-baseline-balance` | `node --test-reporter=tap tests/r0022-baseline-balance.cjs` | 1/1/1 | 1.69/1.69/1.62 | 1/1/1 | 1.76/1.67/1.72 | 7 / 7 | PASS daylight preserves protected solar/sky/calendar outputs with explicit accepted solar mapping / PASS below horizon preserves protected solar/sky/c |
| `r0022-lunar-consumers` | `node --test-reporter=tap tests/r0022-lunar-consumers.cjs --cp8-snapshot-only` | 0/0/0 | 1.61/1.59/1.56 | 0/0/0 | 1.7/1.66/1.8 | 0 / 0 | — |
