# R0041 preview-host clear: empty Moon slot after `SalahSkyPreview.clear` (bounded product correction)

Work order R0041 (issue 143), owner-authorised bounded correction of the route recorded in contract section 11.10.
Branch `claude/r0041-preview-clear-20261124`, from `a06e9ae5`. This note does not edit the contract or the
registry; proposed wording for both is at the end.

## Cause (instrumented, not only read)

The previous round's reading (section 11.10) assumed the SVG Moon takes the slot after the preview clears. The
diagnostic recipe `tools/qa/r0041/pc-probe.cjs` (Chromium headed, real DPR 2, full motion, synthetic Madinah fixture,
loopback only) shows the state at the call on the unfixed tree. The first probe run (2 clears, both in this state;
printed to the console, not retained as a file) is tabulated:

| Instant | `.real-sky-composed` | `.real-sky-preview-ready` | Moon detail visible | detail owner | SVG `.mphoto` |
|---|---|---|---|---|---|
| before `clear()` | yes | yes | yes | `refined-sky` | hidden |
| same task after `clear()` | yes | no | **no** | `refined-sky` | hidden |
| animation frames 0-1 (about 5 ms) | yes | no | **no** | `refined-sky` | hidden |
| frame 2 or 3 (about 20-50 ms) | yes | no | yes (refined sky recomposed) | `refined-sky` | hidden |

The retained before run (`probe-before.json`, 2 clears) caught the other branch: the refined sky had NOT yet
recomposed, the preview owned the disc, its clear hid it, the SVG Moon was revealed (no `.real-sky-composed`) and the
preview recomposed the disc in the next frame; the empty slot needs the composed state. After the fix
(`probe-after.json`, 2 clears, both composed) the refined-sky disc stays visible in the same task and every following
frame. So the defect is timing-dependent: in the recorded cases, 1.5 s after `SalahRealSky.invalidate` the refined sky
has already composed again and owns the device-resolution
disc. `SalahSkyPreview.clear()` (`real-sky/native-preview-host.mjs:47` at `a06e9ae5`) called
`window.SalahMoonDetail?.clear()` unconditionally, which hides the detail canvas (`moon/src/moon-detail.mjs:49`).
The SVG Moon cannot take over, because `.c.real-sky-composed .sky .mphoto{visibility:hidden!important}`
(`real-sky/native-sky.css:14`) hides it independently of the preview class. Nothing in that task recomposes the disc,
so the slot shows the refined sky (stars) until the refined sky's next compose (its 50 ms compose cadence,
`real-sky/native-host.mjs` `animate`). The preview's clear was withdrawing a disc it did not own. The refined
sky's own withdrawal already has the symmetric guard (`real-sky/native-host.mjs:88-90`, `previewOwnsDetail`); the
preview's did not. `vendor/real-sky` is not involved; both files are first-party.

## The change

- `moon/src/moon-native.mjs` (the runtime-owned presenter handle, `window.SalahMoonDetail`): new
  `clearFor(owner)`. It withdraws the detail unless the detail is visible and was composed by a different sky owner
  (`state.skyOwner`, written by `moon-detail.mjs` at compose); returns whether it withdrew. `clear()` is unchanged.
  `moon-detail.mjs` stays byte-identical (pinned).
- `real-sky/native-preview-host.mjs` `clear(reason, all=false)`: withdraws through `clearFor('atmospheric-preview')`;
  `all=true` (used only by `awaitInput`, where no sky owner is current) and a handle without `clearFor` keep the
  historical full `clear()`. The awaiting re-entry path is unchanged.
- No await, timer, frame request or poll added on either path (test R41-PC-5); no prayer code touched.
- Truth: the retained disc is the refined sky's own, composed for its current frame from the runtime's accepted
  record. It stays only while both of its owners hold it: the refined host withdraws it on any currentness failure
  (`native-host.mjs` `clear`, which calls `SalahMoonDetail.clear()` unless the preview owns the disc), and the Moon
  runtime's `fallback()` (identity, clock, epoch, pause, hidden) calls the unconditional `detail.clear()`. Nothing
  invalid is retained to hide the failure, and the phase disc is not involved.
- Generated entries rebuilt (`index.html`, `offline.html`, `moon/moon-host.js`, `GENERATED.json`, `moon/BUILD.json`);
  generated-identity pins re-bound (`tools/qa/r0041/rebind-pins.cjs`, the docs-contract entry pin, the first-paint
  split pin in `tests/native-script-contract.js`, because the startup bundle carries the preview host).
- Census `tests/r0041-presenter-census.test.cjs`: `.clearFor(` counted as a detail writer; moon-native 3, preview
  host 3.

## Test (`tests/r0041-preview-clear.test.cjs`, registered in `nativeTestGlob`)

Drives the REAL preview host source against the REAL runtime handle (`moon-native.mjs` through the unmodified rig of
`moon/tests/host.test.cjs`, an accepted refined record) on one shared window.

- R41-PC-1: refined sky composes the disc through the handle; `SalahSkyPreview.clear()`; in the SAME task the preview
  withdrew (`real-sky-preview-ready` removed, status `pending`), `.real-sky-composed` still set, and the detail is
  visible with the same frame, unchanged render count, and the runtime's `observe()` record, epoch, generation and
  source unchanged.
- R41-PC-2: a disc the preview composed is still withdrawn by the preview's clear.
- R41-PC-3: an identity change (runtime fallback) still hides a refined-sky disc; the owner may withdraw its own disc.
- R41-PC-4: awaiting input (paused) keeps the full withdrawal.
- R41-PC-5: no await/Promise/timer/frame request on the clear path or in `clearFor`.
- RED on the pre-change sources (`R41_PC_PREVIEW_SOURCE`, `SALAH_MOON_SOURCE_DIR` pointed at `a06e9ae5` copies):
  PC-1 fails with "empty Moon slot: the preview hid the refined sky's disc"; PC-3 fails (no `clearFor`); PC-2, PC-4,
  PC-5 pass. GREEN on this branch: 5 of 5.

## Native (recipe `tools/qa/r0041/swp.cjs`, flag `preview`, unchanged; per clear `tools/qa/r0041/pv-clear.cjs`)

Four concurrent `preview` cells per launch at 2026-11-18T16:30:00Z (Madinah, method 4, synthetic fixtures), 75 s
per cell, one launch at a time, headed. Chromium 148.0.7778.96 ratio 2 = `--force-device-scale-factor=2` plus
context `deviceScaleFactor` 2. A clear counts if at least one rule-v3 ABSENT recorded frame lies in
[call - 40 ms, call + 1000 ms). Before = contract section 11.10 (candidate `51377ef7`; the product files are
identical to `a06e9ae5`, `git diff 51377ef7 a06e9ae5 -- real-sky moon/src index.html` is empty).

| Engine, ratio, motion | Tree | Launches / cells (valid) | Clears | Clears followed by >= 1 ABSENT frame | ABSENT frames total | End control (ABSENT / frames) | Allowed non-loopback |
|---|---|---|---|---|---|---|---|
| Chromium 2 full | before `51377ef7` | 2 / 8 (8) | 72 | **50** | - | 317 / 317 | 0 |
| Chromium 2 full | main `4ca5ef16` | 2 / 8 (8) | 72 | **48** | - | 345 / 345 | 0 |
| Chromium 2 full | this branch | 2 / 8 (8) | 72 | **0** | 0 of 14,916 judged | 321 / 321 | 0 |
| Chromium 1 full | this branch | 1 / 4 (4) | 36 | **0** | 0 of 7,444 | 204 / 204 | 0 |
| Chromium 2 reduced | this branch | 1 / 4 (4) | 36 | **0** | 0 of 7,462 | 206 / 206 | 0 |
| Firefox 150.0.2, 1 full | this branch | 1 / 4 (4) | 36 | **0** | 0 of 7,444 | 151 / 151 | 0 |
| WebKit 26.4, 1 full | this branch | 1 / 4 (0 valid) | 36 | NOT OBTAINED | (0 of 2,996 readable) | 0 / 0 | 0 |

WebKit: every cell is invalid (`bounded page call timed out: screenshot`; 1,105-1,352 recorded frames per cell
had unreadable time markers and the end control recorded no frame), so the detector was not shown to work there and
no WebKit result is claimed. Firefox and WebKit have no before measurement (section 11.10 measured Chromium only).

The end control (the Moon hidden by a style at the end of every cell) is detected as ABSENT in every frame, so the
detector can see an empty slot in these recordings. No ABSENT frame was found away from a clear either.

## Healthy rendering (pixel identity, `tools/qa/r0041/pixel-identity.cjs`, Chromium ratio 1, reduced motion)

Frozen page clock, settled refined Moon, then a 1 s hide and show; tree A (`a06e9ae5`) loaded twice for the noise
floor. Card 172,250 pixels.

| Scene (instant) | State | A vs A (noise): card / Moon slot differing | A vs this branch: card / Moon slot differing (largest channel difference) |
|---|---|---|---|
| Crescent, 13 Nov 2026 16:00 Z (phase 0.151) | settled after load | 66 / 0 (16) | 66 / **0** (16) |
| Crescent | after hide and show | 0 / 0 | **0 / 0** |
| Half, 17 Nov 2026 16:30 Z (phase 0.541), run 1 | settled after load | 0 / 0 | **64 / 3** (15; slot 4) |
| Half, run 1 | after hide and show | 0 / 0 | **0 / 0** |
| Half, run 2 | settled after load | 0 / 0 | **51 / 0** (15) |
| Half, run 2 | after hide and show | 0 / 0 | **0 / 0** |

**Result: NOT identical in every pair.** After hide and show both scenes are byte-identical in every run. Crescent
settled: the same 66-pixel difference appears between two loads of the old tree, so it is the scene's run-to-run
variation (as in contract section 7.7). Half settled: A vs A was 0 in both runs, while A vs this branch differed by
64 card pixels (3 in the Moon slot, largest difference 4 codes) in run 1 and 51 card pixels (Moon slot identical) in
run 2. The changing count and the crescent's 66-pixel noise suggest run-to-run variation of the settled-after-load
state, but these runs do not show that: a startup-timing consequence of the change (for example a preview clear
during the start-up hand-over that now leaves the refined disc presented) is not excluded. Not investigated
further within the time box. Evidence `pixel-identity-{crescent,half,half2}.json`.

## Checks

- `python tools/build_native.py` twice: exit 0 both; the second build left no tracked change.
- `python tools/verify_v1.py`: `PASS: frozen V1 payload and anchored manifest`.
- `node tests/rlgwo-docs-contract.cjs`: 71 of 71 (after re-binding its generated-entry pin; 70 of 71 before).
- `node tests/native-script-contract.js` and `node tests/r0017-transport.cjs`: exit 0 after the pin re-binds.
- Moon suite (`node --test --test-concurrency=1 moon/tests/*.test.cjs`, TAP): 248 of 248.
- R0041 suites plus the preview-host unit test (`tests/r0041-*.test.cjs`, `moon/tests/r0041-*.test.cjs`,
  `tests/real-sky/native-preview-host.test.mjs`): 88 of 88.
- `python tools/cp9/run_native_regressions.py --output <temp> --select native-runner-contract`:
  `native-runner-contract 0 PASS {'tests': 46}`, `VERDICT PASS`.
- The full registered population was not run in this round.

## Limits

- The before rate exists only for Chromium ratio 2 full motion; ratio 1 and reduced motion were measured on this
  branch only (0), so for them the result shows absence of the defect, not a measured reduction.
- Recordings are compositor captures, not display captures or human viewing.
- Other routes that call the preview's `clear()` while the refined sky owns the disc (preview paint failures and
  deadline misses while composed) take the same guarded path; they were not exercised natively.
- The test's detail is a stand-in that reports `moon-detail.mjs`'s state fields; the real canvas is exercised only
  natively.

## Proposed wording (for the owner of the contract and registry; not applied here)

Contract, new dated note after section 11.11: "Preview-host clear, corrected (dated note, 2026-11-24). Cause
instrumented: at the clear the refined sky had already recomposed and owned the disc; the preview's
`SalahMoonDetail.clear()` hid it while `.real-sky-composed` hid the SVG Moon, so the slot was empty until the
refined sky's next compose (section 11.10's reading, which assumed the SVG Moon takes over, is corrected). The
runtime presenter handle gains `clearFor(owner)`; the preview withdraws only the disc it composed; awaiting input
keeps the full withdrawal; runtime fallback stays unconditional. Test R41-PC-1..5 (RED on the pre-change sources).
Native Chromium ratio 2 full motion: 0 of 72 clears followed by an ABSENT frame (before 50 of 72; main 48 of 72);
evidence `evidence/R0041/preview-clear-fix/`."

IMPLICIT_STATES, ISM-MOON-013 (detail DOM visibility owner) and ISM-SKY-017 (preview shared DOM handoff), one R0041
row each: "Transition changed: preview `clear(reason)` (not awaiting input) → detail withdrawn only if it is not
visible or its `skyOwner` is `atmospheric-preview` (`SalahMoonDetail.clearFor`); a visible refined-sky disc is left
to its owners (refined host currentness fences, Moon runtime `fallback`). Unchanged: awaiting-input entry and
re-entry (full withdrawal), refined host clear, runtime fallback. Documented: this note. Enforced:
`moon/src/moon-native.mjs` handle `clearFor`, `real-sky/native-preview-host.mjs` `clear`. Verified: VM
`tests/r0041-preview-clear.test.cjs` R41-PC-1..5, census; native Chromium (ratio 1 and 2, both motions)
and Firefox (ratio 1, full motion) 0 of 36; WebKit NOT OBTAINED (invalid cells). Not verified: preview paint-failure and deadline clears while composed; Safari. No status change
proposed."
