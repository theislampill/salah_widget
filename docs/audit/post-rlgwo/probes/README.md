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
