# R0033 closure-audit native observations, 2026-11-23

Raw results of `tools/qa/r0033_closure_cells.cjs`, run while preparing the R0033 closure. The requirement audit found
three acceptance rows whose recorded evidence did not cover the issue's own accepting observation (contract §15.5):
R33-17 (two of its four named scenes), R33-11 (native crop) and R33-15 (cloud half of the sky/cloud comparison). These
runs produce those observations. One directory per cell and engine:
- `run.json`: the arguments, start and end UTC, and the exit code. Served trees are written as `<tree sha>`.
- `stdout.jsonl` and `result.json`: the cell's JSON result with its isolation verdict.
- `stderr.txt`.
- the PNGs the result names: full cards, plus `-moon.png` crops of the Moon slot when a disc rectangle exists.
- `<cell>-<engine>-requests.json`: every request with its disposition, the Moon asset requests the loopback server
  saw, and the verdict.

## Method

- **Environment.** Playwright 1.60.0, headless. Chromium 148.0.7778.96, Firefox 150.0.2, WebKit 26.4, on one Windows
  host. One browser at a time, each started through `tools/qa/r0033_isolation.cjs`.
- **Fixture.** Viewport 325×530, DPR 1, zone Asia/Riyadh, reduced motion (as the first slice's `scenes` cell). The
  Playwright clock is installed at 2026-09-08T19:00:00Z and resumed. Prayer comes from a fixture, weather from an
  in-page fixture, and radar is refused in the page. No provider was contacted.
- **Served trees.** Each tree was a disposable `git worktree add --detach` checkout. Its root `index.html` blob
  equals the commit's (checked with `git hash-object`). The checkouts were removed and pruned afterwards.
- **Faults.** All faults were injected from the harness; no product file was edited:
  - the Moon assets were held open (`stall`) or answered 404 `no-store` by the loopback server;
  - the construction failure is the Moon wrapper's 250 ms interval throwing once (the seam of
    `tools/qa/r0033_native_cells.cjs`);
  - the initial-tier failure replaces the frozen `SalahMoonInitial` receiver, through an accessor installed before
    the wrapper runs, with an equally frozen object that has the same `identity` and whose `render()` throws while
    armed.
- **Reads.** `neutrality` reads the DOM and CSS custom properties only, so the older trees' adopting getters are never
  called by the recipe. `twotier` and `cloudlight` run on main `d33adfa0` and read `SalahMoonRuntime.observe()` and
  `qaState()`, which are pure reads there (R0036).

## R33-17: pixel neutrality, the two scenes not run before

**Comparison.** Before = `8990c36d` (first parent of the pull request 139 merge, `git log --first-parent`). After =
`a196351b` (the pull request 139 merge). This is pull request 139 measured against its own parent.

Later merges change product files: pull request 142 (R0036) changes `moon/src/moon-native.mjs` and
`src/native/index.html`. So `8990c36d` against current main would not isolate R0033, and the optional second
comparison (`a196351b` against `d33adfa0`) was not run. The later product-free R0033 merges (pull requests 147 to 151)
change no product file.

**Scenes.** Moon assets were held, so only the initial tier presents, as in the first slice's `scenes` cell.
- `dayclear`: `simTime=12:30&simWx=0`.
- `halfcloud`: `simTime=22:00&simWx=2&simCloud=50&simMoon=0.5&simWax=1&simMoonAlt=20&simMoonH=42`.

**Loads.** Every load used a fresh context, in the order before-0, after-0, before-1, after-1, before-2, after-2.
Repeat 0 is the first load of each tree in the browser: it is recorded and compared, but the verdict uses repeats 1
and 2. Each load settled (`real-sky-composed`, no `sky-pending`, plus `moon-ready` at night), then waited 3 s before
the screenshot.

**Determinism** was established per cell: the same tree loaded twice gives 0 differing pixels (repeat 1 against
repeat 2, both trees, all six cells).

Each cell shows differing pixels / maximum channel delta, over the whole card (172,250 px) and, at night, over the
Moon box (the disc plus 14 px).

| Scene | Engine | Before vs after, repeat 1 / repeat 2 | Same-tree repeats (before; after) | First load vs repeat 1 (before; after) | Exit |
|---|---|---|---|---|---|
| dayclear | Chromium | 0/0 ; 0/0 | 0/0 ; 0/0 | 0/0 ; 0/0 | 0 |
| dayclear | Firefox | 0/0 ; 0/0 | 0/0 ; 0/0 | 1/26 ; 0/0 | 3 (isolation, below) |
| dayclear | WebKit | 0/0 ; 0/0 | 0/0 ; 0/0 | 1/27 ; 0/0 | 0 |
| halfcloud | Chromium | 0/0 ; 0/0 (Moon box 0/0) | 0/0 ; 0/0 | 51/12 (Moon box 0) ; 0/0 | 0 |
| halfcloud | Firefox | 0/0 ; 0/0 (Moon box 0/0) | 0/0 ; 0/0 | 0/0 ; 0/0 | 3 (isolation, below) |
| halfcloud | WebKit | 0/0 ; 0/0 (Moon box 0/0) | 0/0 ; 0/0 | 0/0 ; 0/0 | 0 |

**Verdict: IDENTICAL in all six cells.** The before and after cards are byte-identical on repeats 1 and 2. In the
halfcloud cells every load had `moon-ready` and `--moonbeam` 0.405 on both trees; in the dayclear cells no load had
`moon-ready` and `--moonbeam` was 0.

A first load in a fresh browser sometimes differs from later loads of the same tree, outside the Moon box: 1 px in
Firefox and WebKit by day, 51 px in Chromium at night. It happened on the `8990c36d` side in each case, because that
tree is loaded first. An unrecorded trial run (Chromium, halfcloud, without warm-up) showed the same effect at
10,777 px, maximum delta 30, mostly inside the Moon box, on the first load only. This is why repeat 0 is excluded from
the verdict. The cause was not investigated.

## R33-11: initial-tier failure together with worker failure (main `d33adfa0`)

The scene is a clear night, half Moon at +20°. Moon assets answer 404 `no-store` from the start, and the initial
receiver's `render()` throws. Crops are in `twotier-*-<phase>-moon.png`.

| Variant | Phase | Disc (`moon-ready`) | Visible source | Worker recovery | Initial retry | `--moonbeam` | Light reason |
|---|---|---|---|---|---|---|---|
| recover | both failed (first observation) | no | awaiting-terrain | scheduled, 0 attempts | waiting, 1 throw | 0.000 | `surface-unavailable` |
| recover | throw disarmed, clock +61 s, assets still 404 | **yes** | initial-v5 | scheduled, attempt 1 failed (4 asset requests in total) | (record kept) | 0.405 | eligible |
| recover | assets restored, clock +121 s | yes | terrain-preview | idle, 2 attempts, `retryCount` 0 | — | 0.405 | eligible |
| terminal | both failed | no | awaiting-terrain | scheduled, 0 | waiting, 1 | 0.000 | `surface-unavailable` |
| terminal | clock +61 s ×3, +11 min, +2 h | no | awaiting-terrain | **exhausted, 3** | **exhausted, 3** | 0.000 | `surface-unavailable` |

The results are identical in Chromium, Firefox and WebKit (exit 0 in all six; isolation clean).
- **recover.** The initial tier's own re-attempt restores the opaque disc while the refinement worker is still
  failing. The worker's automatic attempt then reaches the terrain once the assets return, with no driver retry.
- **terminal.** When both budgets are spent, the slot is unlit and empty: the DG-1 = B outcome, with no disc, no
  moonlight and reason `surface-unavailable`.

**Limit.** Between the two failures and the initial tier's re-attempt (60 s after the throw, or the next epoch) the
slot is empty and unlit. That is the issue's M2 default policy (`notBefore` = now + 60 s), not a permanent empty slot.
The VM test asserts the same interval.

## R33-15: no lunar light without a presented surface, under cloud (main `d33adfa0`)

The scene is `simTime=22:00&simWx=2&simCloud=50&simMoon=0.5&simWax=1&simMoonH=42`, with Moon assets held (initial
tier). Loads:
- A: healthy, Moon at +20° (surface presented).
- B and B2: construction failure (no runtime, no surface), Moon at +20°.
- C: construction failure, Moon at −20°.

| Engine | B vs B2 (repeat) | **B vs C** (no surface: Moon up vs below) | A vs B (positive control), whole card | A vs B, sky band below the disc box | Exit |
|---|---|---|---|---|---|
| Chromium | 0/0 | **0/0** | 33,317 px / 105 | 8,413 px / 53 | 0 |
| Firefox | 0/0 | **0/0** | 33,000 / 105 | 8,157 / 52 | 0 |
| WebKit | 0/0 | **0/0** | 32,951 / 105 | 8,077 / 61 | 0 |

Light values (`qaState().moonTruth.lunarLight`, every engine):
- **A:** eligible; illumination 0.675; beam 0.405; cloud light 0.675; local star wash 0.575; glow 0.09; halo 0.190;
  corona 0.193.
- **B and C:** eligibility 0, reason `surface-unavailable`, and every consumer 0 (illumination, beam, cloud light,
  star wash, glow, halo, corona, paraselenae).

Mean RGB of the upper 260 px, excluding the disc box (Chromium):
- A: 55.16 / 56.73 / 61.49.
- B, B2 and C: 51.21 / 53.10 / 57.93 (identical).
Firefox and WebKit give the same pattern.

**Reading.** Without a presented surface, a Moon 20° up produces exactly the same card as a Moon below the horizon,
sky and clouds included. So no lunar light reaches the sky, the clouds or the stars without a surface. With a surface
the same scene is lit (positive control).

**Limits.**
- One cloud scene, at 50% simulated cover; the night clouds are faint in this fixture.
- Reduced-motion presentation.
- Initial tier only (refinement held).

## Isolation

`allowedOffLoopback` is 0 in all 15 runs, and the Node guard refused nothing. The two Firefox `neutrality` runs exit
3 because Firefox's own background update service made one CONNECT to `aus5.mozilla.org:443` in each run. The
refusing loopback proxy answered it with 403 and no outbound connection: the known pattern of §13.1. Their
measurements are complete. Every other run exits 0.

Run times in `run.json` are UTC (they cross midnight into 2026-11-24 UTC). The folder carries the local date.
