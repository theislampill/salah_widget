# R0033 row R33-09: worker CPU throttling, 2026-11-23

Raw results of `tools/qa/r0033_worker_throttle.cjs` (contract §13.3). Chromium 148.0.7778.96 (Playwright 1.60.0,
headless), Windows 11, 16 logical processors. One browser at a time, each started through
`tools/qa/r0033_isolation.cjs`; every run 0 requests allowed off loopback.

- `calibration/calibrate-<method>[-xR].jsonl`: one JSON line per method. A fixed benchmark (an integer JS loop and
  a hand-assembled WASM loop, 4e8 steps each, 5 repetitions, medians) in a dedicated worker, and the JS loop on the
  main thread, before (`before`), while (`during`) and after (`after`) the method is applied; `slowdown` is
  during/before. `<...>-requests.json` is the request ledger of the run. No product code is loaded by a calibration
  run.
- `refine-jobcap-xR-dprN/`: the R33-09 cells. `run.json` (arguments, start and end UTC, exit code), `stdout.jsonl`
  (the cell's JSON line with its isolation verdict), `stderr.txt`, and the request ledger. Served tree:
  `git archive 1fa6123a` (served `index.html` sha256
  `c2c827c7e5d4d203a757483de1b8d3e01c8d31984a20b8ad9d06e5a799d5ae12`, the same bytes as the 2026-11-22 runs).
- `refine-jobcap-x6-dpr3-rerun/`: a second run of the ×6 DPR 3 cell, made because the first run's in-page
  calibration was outside tolerance; the rerun was outside tolerance in the same direction.
- `throughput-jobcap-xR-dprN/` (`--mode refine-throughput`): the concurrency-adjusted cells. The renderer is joined
  to the job uncapped, its mean busy cores B over the 3 unthrottled refinements is measured by job accounting, and the
  cap is B/R cores; a 4-worker simultaneous calibration (expected per-loop slowdown 4/cap, ±20 %; job CPU ±10 % of the
  cap) decides validity. Each sample records its CPU-seconds and busy cores.

Model limits. The `refine-jobcap-*` cells cap the whole renderer at 1/R of ONE logical processor: one thread alone
runs at 1/R, but the refinement (about 55 CPU-s over about 2.7 busy cores) slows about ×10 (nominal ×4) and ×16
(nominal ×6, arithmetic). They are a pessimistic single-slow-core bound, not a ×4/×6 measurement. The
`throughput-jobcap-*` cells approximate R-times-slower cores in aggregate only: a Job Object has no per-thread rate,
so serial phases run faster and parallel phases slower than 1/R; only the total demand is served R times more
slowly. One host (16 logical processors), Chromium only, one Moon scene; GPU and browser processes are not capped.

Command form: `node tools/qa/r0033_worker_throttle.cjs --mode <calibrate|refine|refine-throughput> --method <m> [--rate R] [--dpr N]
[--samples 3] [--reps 5] [--root <tree>] --out <dir> --playwright <pkg>`.
