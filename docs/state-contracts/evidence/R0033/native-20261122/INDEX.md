# R0033 native runs, 2026-11-22

Raw results of the first execution of `tools/qa/r0033_remaining_cells.cjs` (contract §13.1, §13.2). One directory per
run: `run.json` (arguments, start and end UTC, exit code), `stdout.jsonl` (the cell's JSON line, with its isolation
verdict), `stderr.txt`, and `<cell>-<engine>[-dprN][-xR]-requests.json` (every request with its disposition, the
Moon asset requests the loopback server saw, and the verdict).

Served tree: `git archive 27314935`; product bytes identical at every later head of the branch (served `index.html`
sha256 `c2c827c7e5d4d203a757483de1b8d3e01c8d31984a20b8ad9d06e5a799d5ae12`). Playwright 1.60.0, headless; Chromium
148.0.7778.96, Firefox 150.0.2, WebKit 26.4. One browser at a time, each started through
`tools/qa/r0033_isolation.cjs`. Recipe versions: `secondload`, `fileentry`, `smoke` (Chromium, WebKit, first Firefox)
and `throttle` ran at commit `cbf19fde`; the later Firefox smokes and the `m5` cells ran with the isolation module of
commit `183abf5c` (Firefox background services off, verdict breakdown). Command form:
`node tools/qa/r0033_remaining_cells.cjs --cell <cell> --root <tree> --out <dir> --engine <engine> --playwright <pkg> [--dpr N] [--minutes 30] [--rate R --samples 3]`.

Projection: in `final-fileentry-chromium/fileentry-chromium-requests.json` the local path of the served tree inside
`file:` URLs is replaced by `<tree>` (74 URLs); nothing else is edited.

Firefox smoke attempts: `final-smoke-firefox` (two CONNECT attempts to `aus5.mozilla.org:443` refused by the loopback
proxy), then `final2` to `final5` while hardening the Firefox launch prefs; each still had one refused attempt about
31 s after launch. Every one is retained; none allowed a request off loopback. The smoke result is the same in all
five (140 pass, case 22 failed).

`m5` cells (`final-m5-<engine>-dpr<N>`): Chromium DPR 1, 2, 3 exit 0; Firefox DPR 1 exit 0; Firefox DPR 2 and 3 exit 3
because one browser update attempt each (`aus5.mozilla.org:443`) reached the refusing proxy and was answered 403
(`allowedOffLoopback` 0). Their measurement records are complete.
