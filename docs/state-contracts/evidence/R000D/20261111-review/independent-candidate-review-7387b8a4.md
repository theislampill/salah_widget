# R000D independent review, candidate 7387b8a4 (tree 7c25d432), model claude-sonnet-5-5

VERDICT: PASS_WITH_FINDINGS. No blockers. Checked: source semantics, source tests, my own mutations, native cells in both engines. Not checked: CI, other platforms.

## 1. Identity and scope
- Commit and tree match. The diff touches 33 paths, 1935 insertions and 48 deletions.
  - Authored product: src/native/index.html (+42).
  - Generated, with identical hunks: index.html, offline.html, moon/BUILD.json.
  - Tests: 9 files (3 new, 6 rebinds).
  - Tools: tools/qa/run_r000d_native.py.
  - Docs: README, DESIGN, R000D.md.
  - Evidence: PNGs, JSON and logs.
- The whole src diff is only the retry change: `_wxRetry`, `retryClockDomain`, `retryGate`, `retryDiagnostics`, the two fetch gates and stamps, `qaState().wxTruth.retry`, and the reset. No R000B eligibility or withdrawal edit, no R0007 selection or font-gate edit, no deadline or ownership change.
- v1/ is untouched and `verify_v1.py` prints PASS. After `build_native.py`, `git status --porcelain` is empty. The review worktree is clean.

## 2. Semantics (read from the code)
- (a) Guard order is identical. Weather: SIM, then target, then busy, then the fresh-data shortcut (weather only, on the UTC `lastWxAt` and `selectedWeather`), then spacing. Radar: SIM, target, busy, spacing.
- (b) The stamp position is unchanged: after `beginRequest`/`beginAttempt` succeed, with `lastWxTry`/`lastRadarAt` set on the same line. Old assignments: init, the QA boot reset (`lastWxAt`/`lastWxTry` only), and `resetForNewLocation`. The new code clears the record in `resetForNewLocation` and nowhere else.
  - Not clearing the record at the QA boot reset is harmless, because the record is still null at that point.
  - `lastWxTry` and `lastRadarAt` are now write-only, kept for compatibility.
- (c) `_RAFNOW` is raw `performance.now()` with a `Date.now()` fallback (line 873). It is not scaled by `timeScale` and it does not pause. Spacing therefore ignores timeScale demos and runs on while the page is hidden. This matches the old wall behaviour except under clock steps. Behaviour across OS sleep is UNKNOWN; the docs make no sleep claim.
- (d) The boundary is strict `<`, so a request is eligible at exactly 60000 and 600000 ms, same as before.
- (e) The unset sentinel is `null`, distinct from elapsed 0. The two records are independent. `retryClockDomain()` is evaluated per attempt, the stamp carries the clock, and a fallback host reports `wall-fallback` with a "degraded" guarantee. Nothing claims monotonic behaviour on the fallback.
- (f) No existing test or tool deep-equals `wxTruth`. Consumers read fields. The full suite is green.

## 3. Tests (literal)
- Candidate `node --test tests/*.test.cjs tests/*.test.mjs`: 748 tests, 744 pass, 0 fail, 4 todo. Main via git archive: 713, 709, 0, 4.
- `r0017-transport.cjs` exits 0. `weather-no-timetable-assembly.test.py` ran 9 OK. The native-oracles suite ran 78 OK.
- The state, mutation, r000d and r000c files together: 184 tests, 180 pass, 0 fail, 4 todo.
- RED against main's index.html with the logged command: 23 tests, 5 pass, 18 fail. That matches the claim. The failures are real request-count failures (rollback, +-1 h boundaries, forward step) plus missing-surface errors on the new diagnostics.
- The new tests run the real `fetchWeather`, `fetchRadar`, admission and `qaState` through the r000c vm fixture, with independent Date and performance.now doubles. They are not a re-implementation.
- The changed lines in existing tests are legitimate rebinds. The wall advance now also advances elapsed, the reset emulation also clears `retry`, and `_wxRetry` declarations were added to the harnesses. The same assertions stay. The hash pins were rebound to the new source.
- My mutation (i), spacing reverted to wall time and rebuilt: ES0D-01, -02, -03 (+-1 h), -07, -08 (across a step) and the R0006 cold-retry tests go red.
- My mutation (ii), reset of `_wxRetry` dropped from `resetForNewLocation`: caught by "ES0D-13 current config contract..." and "obsolete weather settlement...A-to-B-to-A". Coverage is adequate.
- Both mutated runs also tripped about 20 source-hash identity pins. That is expected noise and is not evidence of detection.

## 4. Criteria

| ID | Judgment | Gap |
|---|---|---|
| 01 | MET_BY_SOURCE_TEST and MET_BY_NATIVE_OBSERVATION | Weather at the real gate. Native used a 2 h step only; source also used 5 min. |
| 02 | MET_BY_SOURCE_TEST and MET_BY_NATIVE_OBSERVATION | Native checked radar at the gate through `qaState().wxTruth.radarAvailable`. |
| 03 | MET_BY_SOURCE_TEST and MET_BY_NATIVE_OBSERVATION | Source covers wall steps of 0 and +-1 h. Native observed 1 to 1 requests at -1 ms and 1 to 2 at the interval, for both sources. |
| 04 | MET_BY_SOURCE_TEST | Native never stamps at elapsed 0, which is fine. |
| 05 | MET_BY_SOURCE_TEST and MET_BY_NATIVE_OBSERVATION | Native showed `currentEligible` and `radarAvailable` false after the step. |
| 06 | MET_BY_SOURCE_TEST | Native shows only the fresh-data-satisfied state before the step. |
| 07 | MET_BY_SOURCE_TEST | Not observed natively. |
| 08 | MET_BY_SOURCE_TEST | Not observed natively. |
| 09 | MET_BY_SOURCE_TEST | Ordinary cadence plus the existing r000c and r000d suites. |
| 10 | MET_BY_SOURCE_TEST | "No timer loop" is a regex over the weather region plus a settled-timer check. |
| 11 | MET_BY_SOURCE_TEST | The R0003 harness stubs `fetchWeather` and `fetchRadar`, so it proves one poll per source on resume, not the real gate. |
| 12 | MET_BY_SOURCE_TEST | Not observed natively. |
| 13 | MET_BY_SOURCE_TEST | Follows the current config contract: any non-appearance change clears both records. Per-source reset belongs to R0003. |
| 14 | PARTIAL | Weather reaches `#wt` showing 20 deg natively. Radar recovery is observed only as `qaState().radarAvailable`; the fixture has no visible radar effect. |
| 15 | MET_BY_SOURCE_TEST | Diagnostics also read natively. |
| 16 | OPEN_UNTIL_DELIVERY | Needs CI, review and merge. Generated parity and `BUILD.json` are consistent locally. |

R000D.md does not claim acceptance. Its table is labelled "Planned proof". The only over-claim is minor: "twice per engine" for native runs, which I did not re-count (I ran once). D1 to D3 are honoured. D2: the fallback is disclosed and there is no discontinuity guard. D3: no new timer, and 60/600 s are preserved.

## 5. Native (my run, one per engine; evidence in `<scratch>`/r000d/independent-review/native)
- Driver: replaces Date and performance.now independently with in-page doubles, never touching the OS clock. It controls provider responses and serves the checkout bytes unchanged. Candidate index.html SHA256 is e41ba434..., and the main copy I served is dc2af380....
- Firefox 153.0: all five cells (accepted, rejected, weatherBoundary, radarBoundary, loopRecovery) PASS. 0 console errors.
- Chromium 148.0.7778.96: all five PASS. Two console entries: an `ERR_FAILED` on a font that is routed away, and a canvas readback warning.
- Counts in both engines: 1 to 1 at 59 999 ms and 1 to 2 at 60 000 ms; the same pattern for radar at 599 999 and 600 000 ms. State was `cooldown` before the boundary.
- After the 2 h correction, in both engines: `currentEligible` false, `radarAvailable` false, `#wt` empty. After recovery: `#wt` shows 20 deg, `radarAvailable` true, and loop recovery made exactly one new request per source (3 calls each).
- Screenshots: after the correction, the header pill is empty and the card shows the clear-sky Forenoon view. After recovery, the header shows a cloud icon and 20 deg, with cloudy sky. The prayer clock moved (Fajr/Sunrise) because it follows the stepped wall clock; that is expected.
- Main control (Chromium, `--root` pointed at main, `--cells loop`): loopRecovery FAIL, so the defect reproduces on main.

## 6. Findings
- Should-fix (docs): R000D.md says "twice per engine". Either say once, or keep the earlier run logs.
- Note: native exercises only a 2 h backward step. Smaller steps are covered by source tests only.
- Note: radar has no visible consumer natively, so ES0D-14 is PARTIAL for radar. The reasoning is in the code and `qaState`.
- Note: `lastWxTry` and `lastRadarAt` are now unread. A comment says so.
- Note: `retry.clock` in diagnostics describes the current host, while the per-source `clock` is the stamp. This is fine; there is no realistic mixed case.

UNKNOWN: OS sleep and background-resume behaviour of `performance.now`; hosted CI; any engine other than Chromium and Firefox.
