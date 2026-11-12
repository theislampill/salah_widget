# Post-RLGWO audit probes

Small, effect-free scripts used as evidence by the post-RLGWO audit, with their recorded outputs.
They make no network requests (provider calls are stubbed inside the repository's own VM
harnesses), launch no browser and write nothing into the repository. Each takes the repository
root (or reads a source file from standard input) as an argument; none embeds a local path.

| Folder | Script | Evidence for | Output |
|---|---|---|---|
| `A/` | `lane-a-probes.cjs <repo>` (P1–P5), `parity.cjs <repo>` | PRA-F-02, PRA-F-14, PRA-F-21; NF01 fixed; presentation path; authored/generated parity | `probe-results.json` (lane run), `*.rerun.out.*` (integrator re-run) |
| `B/` | `wx-outcome-probe.cjs <repo>`, `wx-quarter-gap-probe.cjs <repo>` | PRA-F-15 (`received` on rejection), PRA-F-16, PRA-F-03 | `*.out.json` |
| `C/` | `reset-close-probe.cjs <repo>`, `reset-label-probe.cjs <repo>`, `reverse-error-probe.cjs <repo>` | PRA-F-04, PRA-F-05 | `*.json` (integrator re-run reproduced them) |
| `D/` | `forecast-identity-probe.mjs <repo>` | PRA-F-10 (worker durations are parameters, not measurements) | `forecast-identity-probe.rerun.out.json` |
| `E/` | `moon-throw-blocks-prayer.cjs <repo>` | PRA-F-01 (injected fault) | `moon-throw-blocks-prayer.rerun.out.json` |
| `F/` | `classify.py <sha>` (run inside the repository) | tree classification in REPORT.md | printed table |
| `G/` | `git show <sha>:src/native/config.js \| node tz-identity-probe.cjs`; `git show <sha>:src/native/index.html \| node tz-hint-probe.cjs` | PRA-F-08, PRA-F-02 | `*.rerun.out.json` |
| `integrator/` | `date_instruments.sh`, `pages_payload_estimate.sh` | PRA-F-06, PRA-F-07 | `instrument_results.txt` |

Sanitisation: the lane D probe originally embedded an absolute local path; the committed copy
takes the repository root as its first argument instead. Lane helper scripts that only wrote
lane JSON, the instrument logs (they record absolute source paths) and lane F's raw `gh` query
dumps are not committed. Lane C's attempted run against `f71fef6c` (`reset-close-ref.cjs`)
failed with `ENOBUFS` and produced no result; it is omitted.

## Reproducing each probe (from the repository root)

Paths are relative to the repository root; `P=docs/audit/post-rlgwo/probes`. Node 24 and Python 3
were used. None needs network access.

| Probe | Harness it uses | Command |
|---|---|---|
| A `lane-a-probes.cjs` | `tests/r0003-harness.cjs` (repository VM harness: stubbed fetch, storage, timers) | `node $P/A/lane-a-probes.cjs .` |
| A `parity.cjs` | plain source extraction from `src/native/index.html` and root `index.html` | `node $P/A/parity.cjs .` |
| B `wx-outcome-probe.cjs`, `wx-quarter-gap-probe.cjs` | `vm` evaluation of the authored weather regions of `src/native/index.html`, stubbed fetch/Image/clock | `node $P/B/wx-outcome-probe.cjs .` and `node $P/B/wx-quarter-gap-probe.cjs .` |
| C `reset-close-probe.cjs`, `reset-label-probe.cjs`, `reverse-error-probe.cjs` | `tests/r000f-fixture.cjs` (settings and builder VM fixture; `applyConfig` stubbed) | `node $P/C/<name>.cjs .` |
| D `forecast-identity-probe.mjs` | imports `real-sky/native-lifecycle.mjs` and `native-contract.mjs` directly; fake clock; worker durations are parameters | `node $P/D/forecast-identity-probe.mjs .` (the JSON array is followed by one diagnostic line) |
| E `moon-throw-blocks-prayer.cjs` | `tests/r001d-harness.cjs` over the generated root `index.html` | `node $P/E/moon-throw-blocks-prayer.cjs .` |
| F `classify.py` | `git ls-tree` of the given commit | `python $P/F/classify.py 363c3e53` |
| G `tz-identity-probe.cjs` | `vm` evaluation of `src/native/config.js` read from stdin | `git show 363c3e53:src/native/config.js \| node $P/G/tz-identity-probe.cjs` |
| G `tz-hint-probe.cjs` | `vm` evaluation of extracted time functions read from stdin | `git show 363c3e53:src/native/index.html \| node $P/G/tz-hint-probe.cjs` |
| integrator `date_instruments.sh` | `git archive` extraction into an output directory; `GIT_DIR` set to the repository | `bash $P/integrator/date_instruments.sh "$PWD" "$(git rev-parse --git-common-dir)" <out-dir> <sha>...` |
| integrator `pages_payload_estimate.sh` | `git ls-tree -r -l` sums | `bash $P/integrator/pages_payload_estimate.sh 06772824 f71fef6c 363c3e53` |
