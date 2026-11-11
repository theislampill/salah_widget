# Independent exact review: observation of the existing host sleep

**Verdict: PASS within the bounded three-file source and effects scope.** No code defect or review-blocking gap was found in this exact packet. This is a findings-only receipt; it is not native acceptance or whole R0007 acceptance.

## Exact reviewed identity

- Immutable base commit: `4bac6a4781fce62f08ab550a20fe5234d3ebb746`.
- Immutable base tree: `a5e51a591200296e3e73b9ecedbd8c0539e07ee5`.
- Source manifest: `/workspace/scratch/66b3aaff4329/recovery/ingress-sleep-observation/source-manifest.json`.
- Source manifest SHA-256: `09d151f36eeaef26c5dc1806288ced740657fe09b1e4766e5fc47860050adbc1`.
- Source patch SHA-256: `521fcf9a51dae1ede87ae6a3db2b0b36e320a03438ae70d974fa56e289e25f07`.
- All three candidate sizes and hashes, base copies, Git blob identities, and eight unchanged supporting files were checked against the immutable base. The final candidate hashes were rechecked before this receipt was written.

| Reviewed path | Bytes | Candidate SHA-256 |
| --- | ---: | --- |
| `tools/cp9/r0007_browser.py` | 43471 | `8d23a6d459e1a8010bf1c5bb66a773d165aa0b8ccc0fdc1ad7710ef38abcf09e` |
| `tests/test_r0007_operation_timing.py` | 6064 | `d2e46533d1723b61c5314a2a325f659203874a588e90caa8f221221fd892afd2` |
| `tests/rlgwo/R0007-native-request.json` | 610 | `47fc789210cabf470e641b876a25e3ecfbe4927477c60b6799acfd2fd1cd7f2f` |

## Findings

### SO-R1 — PASS

The driver is byte-exactly the immutable original with only the specified sleep hunk replaced. In ingress-active cases, one existing time.sleep(action["ms"]/1000) is invoked through the unchanged measure/observe_operation; the no-mode direct call is retained. No added page call, wait, retry, release, scheduler pump, fixture effect or deadline change appears in the source delta.

### SO-R2 — PASS

All six candidate timing tests pass. The same exact candidate tests against the privately copied original driver fail with exactly two assertion failures and zero errors: successful and failed diagnostic sleeps lack operationTimings. This independently demonstrates call-site sensitivity rather than helper-only coverage.

### SO-R3 — PASS

The diagnostic sleep failure path retains a failed host timing row and safe error type, omits untrusted error text, suppresses displayed cause chaining, propagates failure and prevents the following release. The unchanged 52-control ingress suite passes, including driver finalization, cleanup and selected/absent-mode error-custody controls.

### SO-R4 — PASS

An independent probe executes the actual AST dispatcher and local measure for both unchanged seven-action recipes, with only native/time boundaries doubled. It confirms one requested 0.25-second sleep at index 2, release at index 3, identical external effects between original and candidate, and exact original/candidate absent-mode trace parity. The added timing row supports pre-sleep, enclosed sleep and post-sleep host elapsed partitions using adjacent existing brackets.

### SO-R5 — PASS

The pure request planner selects the same two cases as the original request: NE07-fall24 and NE07-font-fallback-fall24; Firefox only, headed, video-only, two planned cells. The unchanged recipe requires serial execution. Only requestId/reason change; no native collector entry point was invoked.

## Fresh independent verification

| Check | Observed result | Evidence |
| --- | --- | --- |
| Candidate timing/dispatch controls | 6 passed; exit 0 | `recovery/sleep-observation-exact-review/green-timing.log` |
| Unchanged ingress controls | 52 passed; exit 0 | `recovery/sleep-observation-exact-review/green-ingress.log` |
| Candidate timing tests against immutable original driver | 6 executed; 2 expected assertion failures; 0 errors; exit 1 | `recovery/sleep-observation-exact-review/red-original-driver.log` |
| Actual seven-action dispatcher probe, both recipe cases | PASS; original effects retained, index 2 sleep/index 3 release, exact absent-mode trace parity | `recovery/sleep-observation-exact-review/real-recipe-probe.json` |
| Pure request planner | Same finite headed Firefox video-only two-case plan; request `r0007-font-ingress-20261110-02` | Same probe receipt |

The original-driver negative control was copied into the review's own evidence directory; no target source, Git ref/index, or audit controller was modified. The 52 existing controls create temporary synthetic Git repositories and boundary fixtures inside that same permitted directory. No native browser, real server, network acquisition, workflow or publication was used. Python bytecode writes were disabled.

The additional probe closes a specific qualification detail left by the two-action unit fixture: it verifies the real recipe's action index 2 and all seven original actions, and compares original/candidate effects. Its timestamps are deliberately synthetic. It does not measure a real sleep or reproduce the historical gap.

## Residual boundaries

- This receipt does not review a future final publication manifest or any docs/evidence additions. It does not authorize publication, merge, native execution, whole R0007 acceptance or closure.
- The new interval encloses the host sleep invocation plus ordinary measurement overhead and possible rescheduling. It is not a kernel-only sleep duration, and instrumentation is not guaranteed to leave observed elapsed scheduling identical.
- All probe clock values and native objects are synthetic. Host monotonic brackets do not associate native performance clocks or video frames and do not establish the historical host/OS/browser cause.
- The observation change provides no timing cure or guarantee that the original body release will beat its unchanged 10-second deadline. A successful later run would not explain the historical failed pair.
- CSS identity or independent equivalence, complete request/body custody, phase/terminal/finalization/cleanup and independent full-video/pixel review remain required before any future paired inference. Existing setup failure and readability observations receive no waiver from this source PASS.

## Evidence custody

The JSON companion records exact evidence paths, byte counts and SHA-256 values, plus the test commands and request plan. A separately supplied final publication manifest must be received on its own merits; this receipt covers only the exact three changed source/request/test paths above.
