# R0027 regression comparison

Base = disposable `git archive` export of main `645b53cc`; candidate = export of the candidate head (after the
identity rebind commit). Exports carry no `.git`, so suites that read historical Git objects report INCOMPLETE
identically in both. Node v24.14.0, Python 3.11.9, Windows.

| Suite (command) | Base | Candidate |
|---|---|---|
| `node --test tests/*.test.cjs tests/*.test.mjs` | 748 tests, 744 pass, 0 fail, 4 todo | 748 tests, 744 pass, 0 fail, 4 todo (before the rebind: 740 pass, 4 fail in `tests/r0017-adapters.test.cjs`, "First-paint source identity mismatch") |
| `node --test --test-concurrency=1 tests/real-sky/*.test.mjs` | 292/292 | 322/322 (+30 R0027) |
| `python tools/cp9/qualify_candidate.py --groups integration` | integration exit 0, 292/292 | integration exit 0, 322/322 |
| `node tests/r0017-transport.cjs` | exit 0 | exit 0 after rebind (exit 1 before: legacy structural pin) |
| `node tests/native-script-contract.js` | exit 0 | exit 0 |
| `node tests/rlgwo-docs-contract.cjs` | exit 1, 64 cases, 50 pass, 14 fail | exit 1, 64 cases, 50 pass, 14 fail; failing set identical: True |
| `python tests/real-sky/native_horizon_build_test.py` | OK | OK |
| `python tests/real-sky/native_spectral_cache_build_test.py -v` | absent | Ran 8 tests, OK |
| `python tools/verify_v1.py` | PASS | PASS |
| disposable rebuild x2 of the candidate export | — | all generated files byte-identical to the committed tree |

`PYTHONUTF8=1 python tools/cp9/run_native_regressions.py --output <dir>` (overall FAIL in both; every command row identical):

| Command | Base | Candidate |
|---|---|---|
| native-runner-contract | PASS {"tests": 42} | PASS {"tests": 42} |
| native-test-glob | INCOMPLETE {"tests": 729, "pass": 725, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 4} | INCOMPLETE {"tests": 729, "pass": 725, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 4} |
| r0001-date-sinks | FAIL {"passCases": 12, "failCases": 1} | FAIL {"passCases": 12, "failCases": 1} |
| r0007-countdown | PASS {"tests": 23, "pass": 23, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 0} | PASS {"tests": 23, "pass": 23, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 0} |
| r0008-timezone | PASS {"tests": 37, "pass": 37, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 0} | PASS {"tests": 37, "pass": 37, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 0} |
| r0009-date-selection | FAIL {"passCases": 21, "failCases": 1} | FAIL {"passCases": 21, "failCases": 1} |
| r000f-intent | PASS {"passLines": 21, "failLines": 0} | PASS {"passLines": 21, "failLines": 0} |
| r000f-reset | PASS {"passLines": 9, "failLines": 0} | PASS {"passLines": 9, "failLines": 0} |
| r0010-preferences | PASS {"passLines": 9, "failLines": 0} | PASS {"passLines": 9, "failLines": 0} |
| r0011-storage | FAIL {"passLines": 3, "failLines": 1, "unparsedOutput": true} | FAIL {"passLines": 3, "failLines": 1, "unparsedOutput": true} |
| r0012-clipboard | PASS {"passLines": 11, "failLines": 0} | PASS {"passLines": 11, "failLines": 0} |
| r0012-effects | PASS {"passLines": 3, "failLines": 0} | PASS {"passLines": 3, "failLines": 0} |
| r0017-cloud-visibility | PASS {"passCases": 39, "failCases": 0} | PASS {"passCases": 39, "failCases": 0} |
| r0017-contract | PASS {"passCases": 35, "failCases": 0} | PASS {"passCases": 35, "failCases": 0} |
| r0017-transport | PASS {"passCases": 32, "failCases": 0} | PASS {"passCases": 32, "failCases": 0} |
| r0017-weather | PASS {"passCases": 6, "failCases": 0} | PASS {"passCases": 6, "failCases": 0} |
| r0018-appearance | PASS {"passCases": 17, "failCases": 0} | PASS {"passCases": 17, "failCases": 0} |
| r0018-timetable-contrast | INCOMPLETE {} | INCOMPLETE {} |
| r0019-date-disclosure | FAIL {"passCases": 15, "failCases": 1} | FAIL {"passCases": 15, "failCases": 1} |
| r001a-radio | PASS {"passLines": 8, "failLines": 0} | PASS {"passLines": 8, "failLines": 0} |
| r001d-lifecycle | PASS {"passLines": 11, "failLines": 0} | PASS {"passLines": 11, "failLines": 0} |
| r001f-deadline | PASS {"passLines": 13, "failLines": 0} | PASS {"passLines": 13, "failLines": 0} |
| r0020-clock | PASS {"tests": 44, "pass": 44, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 0} | PASS {"tests": 44, "pass": 44, "fail": 0, "cancelled": 0, "skipped": 0, "todo": 0} |
| r0021-reveal | INCOMPLETE {} | INCOMPLETE {} |
| r0022-baseline-balance | INCOMPLETE {} | INCOMPLETE {} |
| r0022-lunar-consumers | INCOMPLETE {"passLines": 24, "failLines": 0} | INCOMPLETE {"passLines": 24, "failLines": 0} |
| r0023-metadata | INCOMPLETE {} | INCOMPLETE {} |
| r0025-continuity | PASS {"passLines": 9, "failLines": 0} | PASS {"passLines": 9, "failLines": 0} |
| r0025-lifecycle | PASS {"passLines": 16, "failLines": 0} | PASS {"passLines": 16, "failLines": 0} |

The four FAIL rows (r0001, r0009, r0011, r0019) are the known `tests/r0011-fixture.cjs` crash on main, unrelated to
R0027 and untouched. rlgwo failing cases (both): docs composed: actual smoke terminal contract and held qualification; docs composed: admitted synthetic lane and immediate withdrawal stay separate; docs composed: cloud monotonic intervals, old wind, identity and suspension; docs composed: current and forecast quantity windows retain unavailable metadata; docs composed: default glass and opt-in contrast keep distinct gates; docs composed: neutral initial reveal and separate texture failure; docs composed: one selected provider calendar decision and complete-value access; docs composed: opaque calendar Earthshine versus atmospheric lunar eligibility; docs composed: ordinary wall and explicit anchored one-times authorities; docs composed: useful model estimate without local observation or arrival; docs: ARCHITECTURE.md no positive query-only diagnostic recipe; docs: HANDOFF.md no positive query-only diagnostic recipe; source: actual model-live negative and admitted synthetic wet, expiry and outage; source: six real force branches and unsupported-string mutant
