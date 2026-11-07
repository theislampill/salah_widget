# R0017 independent cold intake review

## Disposition: PASS for intake readiness

The commission and live amendments provide a coherent, bounded implementation contract. No unresolved scope decision prevents implementation. This disposition authorizes no new action and certifies no candidate: the baseline runner does not satisfy the new contract, and an independent review of the actual immutable candidate remains necessary. This was a read-only intake; I ran no regression campaign, changed no source, and published nothing.

The implementation plan is directionally sound. Preserve the execution gates below as acceptance requirements, not optional follow-up work. In particular, a runner/parser unit-test PASS alone cannot establish ES17-07, ES17-11, ES17-13, or ES17-14.

## Evidence and identity

I read the entire commission at `commission/prompts/01_R0017_EXECUTE.md`, `live/issue23.md`, all five `live/comments23-*.md` files, and `live/comments68-6700145812.md`. The observed live checkout was `/workspace/scratch/7a8daf93afaa/r0017-explicit-work`, branch `pro/r0017-explicit-regression-lifecycle-20261106`, HEAD `f71fef6ccf7e4efcb57b5a26688d2360461a3253`, tree `79aedcac840d624b5ea423922314f0832dc3f750`. At the initial identity check the only untracked entry was audit workflow metadata. Root and the adapter investigator subsequently began implementation, so this report is not a review of the final working tree.

Source reads included `AGENTS.md`, the complete baseline `tools/cp9/run_native_regressions.py`, its actual caller `tools/cp9/qualify_candidate.py`, the README smoke qualification section, `tests/r0017-contract.cjs`, `tests/r0017-transport.cjs`, current date-sink/weather fixture code, and the exact f71 version of `tests/r0011-fixture.cjs`. Searches covered runner-result consumers and relevant extraction, history, timer, and exclusion code. I also read the retained historical audit's `evidence/TEST_ABNORMALITIES.md` and `evidence/tests/adjudication.json`. Those historical results were inspected, not rerun. The earlier checkout under `/workspace/scratch/8ab1bbbe9699` was not used.

Live references:

- [Issue #23](https://github.com/theislampill/salah_widget/issues/23).
- [Initial smoke readiness record](https://github.com/theislampill/salah_widget/issues/23#issuecomment-6073045151).
- [Expanded smoke requirements and readiness record](https://github.com/theislampill/salah_widget/issues/23#issuecomment-6074577280).
- [Prior smoke closure certificate](https://github.com/theislampill/salah_widget/issues/23#issuecomment-6181111816) and [closure readback](https://github.com/theislampill/salah_widget/issues/23#issuecomment-6181220586).
- [Current R0017 increment](https://github.com/theislampill/salah_widget/issues/23#issuecomment-6700162946).
- [Shared explicit-state contract and pairwise crosswalk](https://github.com/theislampill/salah_widget/issues/68#issuecomment-6700145812).

## Live discussion versus reconstructed packet

The live R0017 increment and reconstructed commission agree on the lifecycle, distinct result dimensions, all fourteen ES17 acceptance rows, all six required mutants, historical-input treatment, and compatibility requirements. I found no live scope expansion that requires implementing another owner. The R0017 pairs in the compact packet crosswalk agree with the full shared amendment.

Earlier pinning to fd2972 or other historical repair bases is superseded for this increment by the current-main intake requirement. The f71 planning pin remains evidence, not permission to ignore a newer fetched main. Root must retain its fresh-base/readback evidence separately from this intake observation.

The older “remains open” and incomplete readiness comments are superseded by the later actual smoke closure certificate and readback. The current increment preserves that closure and its limitations. It does not require replaying the completed Windows browser campaign merely because the issue is reopened for evaluator work. Conversely, the old certificate is not a certificate for the present f71 runtime or a newly adapted wrapper. README explicitly records that its retained wrapper rejects the current inline Moon startup/refinement layout. The adaptation must qualify that changed test interface honestly.

The original issue's limited implementation authorization was superseded by the explicit execution commission. Its technical invariants remain binding. Cross-owner references are interface obligations and do not convert this task into implementation of all eleven owners.

## Binding scope and preservation requirements

The allowed repair concerns the native regression runner, necessary current-source extraction/bootstrap adapters, their focused regression controls, actual invocation/outcome documentation, and the R0017 state-contract document. Preserve authored product behavior, scientific/vendor/core data, generated runtime bytes, frozen V1, and unrelated owner work unless a concrete bounded dependency is established first. A test harness repair is not authority to change product expectations until an existing rejection becomes green.

The accepted smoke contract remains material:

- Keep `window.__smoke.pass/fail/skip` compatibility, named required callbacks, executed/failed/missing accounting, and FAIL-before-INCOMPLETE-before-PASS precedence. Historical acceptance was 30 required callbacks and 141 assertions; counts and actual completion have different meanings.
- Preserve private storage through every config consumer, including both local and prefer-local resolution. Valid, malformed, absent, and unrelated owner bytes must survive. No real-storage getter/probe or destructive cleanup is acceptable.
- Preserve pre-script private storage, fixed Date, and fetch/Response/json interception. Source identity, exact admitted requests, per-attempt ownership, and no network fallback remain required. Unknown modes, resources, and script boundaries must fail closed.
- Healthy, reject, hang, and bootstrap-error outcomes remain different. Config-only success cannot dominate missing widget execution. Late completion cannot satisfy a successor attempt.
- Preserve explicit reduced/full preference controls, motion override behavior, and exact restoration. Source/VM fixtures do not establish native browser pixels, motion, public delivery, installation, provider health, or cross-platform behavior.
- Preserve the joined weather-model expectations and useful positives. Do not restore an obsolete oracle to obtain green results.

Keep historical failures and unexplained trials visible, including the prior 27/30, 28/30 and 29/30 observations and the 13.827-second Moon trial. Preserve the accepted memory, four-worker, font/clock, and R0021 limitations. New source tests can qualify their own scope without explaining those old observations.

## Output and consumer hazards

These are baseline static findings, supported by the runner and actual caller reads. They are not new runtime failure reports.

| Hazard | Required protection |
|---|---|
| `start` is reused for a JSON character offset after capturing monotonic time. | Separate immutable command start time from parsing offsets; retain controlled one-second leading-JSON and prefixed-JSON regressions. |
| Aggregate status depends only on `exitCode == 0`. | Require proved assertion completion and applicability as well as successful exit. Empty, malformed, unexpected, or incomplete output cannot PASS. |
| Any JSON object with no `results` may yield zero pass/fail cases. Other shapes may raise an uncaught attribute error. | Recognize complete expected schemas, reject unsupported shapes, and record a truthful terminal classification rather than abandon the remaining denominator. |
| TAP extraction accepts whichever summary fields happen to exist, without checking completion or consistent plans/counts. | Validate a complete supported terminal TAP envelope. Missing summaries, cancelled tests, conflicting counts, or truncation cannot be mistaken for completed required assertions. Preserve skipped/TODO counts and their limited meaning. |
| PASS/FAIL lines can be mistaken for a complete contract. | Recognize the actual line-plus-summary formats emitted by selected tests; do not accept an isolated success-looking line as proof of the declared population. |
| Timeout becomes synthetic code 124 without a separate timeout cause. Launch errors can escape before a record exists. | Separate process outcome from semantic outcome; retain actual elapsed time, partial logs, cause, and missing completion. Distinguish a real child exit 124 from runner timeout. |
| Selection is not persisted before launch; `HISTORICAL` filtering removes commands from execution records. | Freeze and persist the selected plan first. Every selected member receives exactly one terminal record, including setup-unavailable, excluded, aborted, and unstarted members. |
| No matching `*.test.cjs` can turn the nominal glob invocation into unintended Node default discovery. | Treat empty or missing selected population as setup evidence; do not silently replace it with a different population. |
| Reusing an output directory overwrites log/result paths. | Use a fresh invocation directory or an explicit collision policy that preserves the original failing record. Bind invocation identity and file custody. |
| No source/runner/test/input/tool binding exists in the baseline result. | Record the actual tree and runner identity, planned population, invocation, host/tool versions, and exact historical dependencies. Detect relevant source change during an invocation. |
| Explicit exclusions coexist with ordinary passing suites. | Preserve exclusions as separate dispositions with case identity, reason, replacement coverage or named residual. Never add their count to passed assertions. |
| Consumer compatibility depends on the runner CLI. | Preserve names, `command`, `exitCode`, `seconds`, `counts`, `log`, exclusions, and aggregate shape; version additions. All semantic non-PASS outcomes must remain nonzero at the CLI boundary. |

`tools/cp9/qualify_candidate.py` is the located actual wrapper consumer. It invokes this runner from the candidate root with `--output`, records the child return code and runtime identity, and does not presently interpret the native JSON schema. Therefore a truthful JSON `INCOMPLETE` paired with a zero CLI exit would still be an integration defect. Its own final exit is deliberately not an ordinary all-green zero; do not silently “clean up” that separate contract. The search establishes this caller inside the inspected checkout, not absence of external consumers.

Actual selected outputs are heterogeneous: Node TAP; PASS/FAIL lines plus a JSON summary; result arrays using either `status` or `result`; lifecycle envelopes with declared/executed/missing/terminal fields; and source-bound pass/fail summaries. Parser tests must exercise those real formats, not only a convenient generic `{results: [...]}` format invented for the runner test.

## Retained failure and adapter ledger

The retained audit selected 28 commands: one native glob and 27 named commands. Fourteen named commands were nonzero. Do not collapse their distinct causes into “script drift.” The following ledger is historical f71 audit evidence and must be rebound to the actual candidate and current input availability.

| Selected command | Historical failure boundary to investigate |
|---|---|
| r0001-date-sinks | Complete-runtime inline-script selection; useful sink/mutant checks must execute after successful extraction. |
| r0009-date-selection | Extraction rejects before intended date-selection behavior. |
| r0010-preferences | Bootstrap dependency `_skyInitialDocument`; 2 passes and 7 failures originally. |
| r0011-storage | Same bootstrap dependency; 17 passes and 1 failure originally. |
| r0017-transport | Wrapper allowlist rejects current script layout; 8 passes and 13 failures originally. |
| r0018-appearance | Extraction/bootstrap boundary; 8 passes and 9 failures originally. |
| r0018-timetable-contrast | Exact historical `ed5e7af` comparison input unavailable in the prior environment. |
| r0019-date-disclosure | Three-script extraction assumption rejects before behavior. |
| r001d-lifecycle | Completion driver does not drive current two-RAF/MessageChannel boot path. |
| r001f-deadline | `_skyInitialDocument` bootstrap dependency; retain actual deadline/cleanup invariants. |
| r0021-reveal | Mixed RAF/bootstrap deficiency and historical `47c0fa` comparison; three removed synthetic-star cases require separate exclusions. |
| r0022-baseline-balance | Exact `fd2972` historical input was unavailable. |
| r0023-metadata | Five historical checks depended on unavailable `fd2972`; 26 positive checks originally. |
| r0025-lifecycle | Fixture selects `.wfx .drop` but the current owner requests `.wfx .drop,.wfx .flake`; retain real particle lifecycle assertions. |

Two additional removed synthetic-projection cases in the passing r0022-lunar-consumers suite remain exclusions. They cannot be hidden by the command's successful exit. Each removed synthetic producer needs a concrete current catalogue/compositor consumer test or an explicit residual. A replacement test name alone is insufficient without showing it exercises the retained observation.

The original native glob had 538 tests: 533 pass, one timeout, four TODO. The unchanged isolated 16-case rerun later passed; contention was plausible, not established. Do not convert this into a product fix claim. The four retained TODO concerns must remain visible and outside passed assertions. Similarly, the historical bright-star input failures and repaired-input rerun were different evidence stages, not permission to replace original results.

For every adapter repair, record invariant, current source owner/symbol, old fixture assumption, original failure, retained behavior, exact adapter delta, healthy through-consumer evidence, discriminating negative, and historical input identity if applicable. A new helper-only test cannot replace the existing caller. Wrong-script/extraction negatives are setup controls; the product-guard mutant must separately reach a valid setup and fail because the real guard was removed.

## Implementation-plan critique and acceptance gates

The plan in `.IMPLEMENTAUDIT/runs/r0017-explicit-regression-lifecycle-Cro7Xr/implementation-plan.md` matches the scope and key design. Its immutable selection, command-owned lifecycle, complete schema recognition, explicit setup contract, actual consumer controls, documentation, and separate exact-commit review are appropriate.

Before declaring this increment ready for review, make the following concrete:

1. Freeze the intended new population. Adding a Python runner self-test command intentionally changes the command denominator; retain the historical 28-command baseline and explain the addition. Its controlled subprocess tests must not recursively invoke the full runner.
2. Define continuation policy operationally. A safely reaped failed process may permit the next independent command; timeout or launch failure must still terminalize every planned member. If descendants or external effects may survive, stop and classify remaining members explicitly. “Continue after errors” is not a sufficient lifecycle rule.
3. Prove all six named mutants: timing reuse, success-text override of nonzero exit, selected-command omission, missing history converted to PASS, wrong-script/helper-only green, and a real product guard removed after valid setup. Preserve both the original regression and the repaired discriminator.
4. Require all ES17-01–14 rows in the final evidence ledger. Unit tests cover only part of the contract; current adapter positives/negatives, preserved storage/transport controls, consumer CLI, historical availability/exclusions, actual tree binding, and per-owner scope need their own evidence.
5. Bind historical checks to exact commit-and-path inputs. Availability can differ from the old audit clone. If reacquisition is unavailable, report that circumstance and unmet comparison; never substitute current main or classify it as an intentional removed-producer exclusion.
6. Keep the wrapper admission narrow. Admit the reviewed current Moon/first-paint/native script boundaries and identity checks; continue rejecting added, duplicated, reordered where relevant, missing, or altered scripts. Preserve actual product script bytes and pre-parser hook order.
7. Publish a bounded result. A successful evaluator increment supplies usable evidence for the owners it actually exercised; it is not blanket certification of the widget, all pairwise joins, prior browser/native limitations, public delivery, or issue closure.

## Handoff

**No intake blocker.** Proceed with the scoped implementation and focused verification. This report should accompany, not replace, the later independent exact-tree review. Acceptance must be based on the final candidate's real evidence, with every selected obligation receiving a truthful disposition.
