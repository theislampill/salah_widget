# R0017 runner draft: independent bounded review

## Scope and result

**Draft review disposition: GAP-REVISE.** This is a draft-level recommendation to root, not final candidate acceptance.

This is an ordinary separately attributed draft review by `/root/governor_setup`. It is not a routed `audit-assess`/`audit-andon` result, immutable-candidate acceptance, or lifecycle decision. No repository or installed-package file was edited, and no inherited suite or native renderer was launched. The only mutations were review evidence and synthetic fixture bytes outside the worktree.

Against the frozen draft identified below, the probes reproduced **four false-PASS classifications and one lost-terminal interruption path**. They also exposed a source-change aggregate-precedence concern and a conditional whole-command historical dependency. Healthy JSON, TAP, and two-command run controls passed. These results supplement root's five named parser probes rather than repeating them.

| ID | Priority | Actual result | ES17 relationship |
|---|---|---|---|
| F1 | High | Duplicate JSON `results` keys erase an earlier FAIL before validation; classification is PASS | ES17-04; known schema/complete-envelope requirement |
| F2 | High | Contradictory `pass`/`passed` and `fail`/`failed` aliases classify PASS | ES17-04, ES17-12 |
| F3 | High | TAP `1..0`, no case lines, positive totals classifies PASS | ES17-04, ES17-12; counts do not establish execution identity |
| F4 | High | A sole TAP SKIP case is counted as pass and classifies PASS | ES17-10, ES17-12 |
| F5 | High | Cancellation during classification escapes after child exit; receipt remains RUNNING with zero command records | ES17-06; interruption/terminal persistence |
| O1 | Review concern | Source change changes aggregate FAIL to INCOMPLETE despite retained FAIL records | Separate evidence/result semantics; ES17-12/13 |
| O2 | Conditional scope limitation | Missing exact history prevents every case in mixed `r0021-reveal` command from launching | ES17-09/14; optional historical dependencies |

## Frozen inputs and source stability

All executable probes imported this saved copy, not a moving source module:

`/workspace/scratch/7a8daf93afaa/runner-review-evidence/inputs/tools/cp9/run_native_regressions.py`

- Runner snapshot SHA-256: `4aa993b98ae364a633d71eccd44a6eecaf7f9dd22c456760ea977797f7614daa` (21,650 bytes, 391 lines).
- Test snapshot SHA-256: `15e8efa8a16fd2cca93226e6e897fb526f2621d6021938d0a862ae6d25c0efe2` (14,621 bytes, 273 lines).
- Initial reconnaissance saw runner hash `9707a4b3458394762b36a67d6121593d22e6fb1ccee7d26418427635d2fab159`; it changed before the frozen copy was made. No probe result is attributed to that earlier hash.

Root continued authoring during review. Final readback hashes are at the end of this report and in `runner-review-evidence/input-manifest.json`. Findings bind the frozen snapshot and need only their affected discriminators rechecked after relevant changes. This report does not claim the moving current candidate retains every finding.

The snapshot tests already cover root's conflicting per-case `status`/`result`, outer INCOMPLETE versus inner FAIL, leading truncated JSON, TAP `not ok` versus zero fail totals, and setup-exception stack recognition. This review did not rerun those exact cases.

## F1 — Duplicate JSON properties hide an observed FAIL

The exact classifier input was:

```json
{"results":[{"name":"real case","status":"FAIL"}],"results":[{"name":"real case","status":"PASS"}]}
```

`classify_output` returned `status: PASS`, `executionProven: true`, and `{passCases: 1, failCases: 0}`. The complete raw object contains two conflicting result populations; Python's ordinary decoder retains the second property before subsequent validation sees it. The distinct-name/per-case-state checks cannot recover the discarded population.

Owner: snapshot `terminal_json` at line 150, then `classify_output` result-array branch. This differs from root's `status`/`result` conflict mutant inside one case. A decoder-level duplicate-property refusal is needed if this JSON is to be treated as a known, unambiguous terminal schema. Do not silently choose the successful duplicate.

Evidence: `probe-run-5e006b632043/duplicate-json-results-hides-fail.txt` and the corresponding observation in `observations.json`.

## F2 — Summary aliases can contradict each other and still pass

Exact input:

```text
PASS real case
{"pass":1,"passed":0,"fail":0,"failed":1}
```

Observed classification: PASS, `executionProven: true`, `{passLines: 1, failLines: 0}`. Both aliases are recognized by the implementation, but line 213 silently prefers `pass`/`fail` when both are present. It never checks consistency with `passed`/`failed`. The same output therefore explicitly declares one failure under a supported alias and one success under the preferred pair.

Reject contradictory recognized alias fields before trusting the matched line counts. This is a different schema branch from root's per-case `status`/`result` check.

Evidence: `probe-run-5e006b632043/conflicting-summary-aliases.txt` and `observations.json`.

## F3 — Empty TAP population can claim positive totals

Exact input:

```text
TAP version 13
1..0
# tests 1
# suites 0
# pass 1
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 1
```

Observed classification: PASS, `executionProven: true`, `tests: 1`, `pass: 1`. There is no `ok`/`not ok` case line at all. The case-number check at lines 174–180 compares two empty sequences and succeeds; the independently positive totals then satisfy the arithmetic check.

This is stronger than an inaccurate count: the parser certifies executed assertions from an explicitly empty plan. Require a nonempty actual applicable population for PASS and reconcile counts with admitted case identities. Node TAP can have nested cases, so a repair should preserve valid nested output rather than assume every total must equal the count of top-level lines.

This does not repeat root's `not ok` versus `# fail 0` mutant.

Evidence: `probe-run-5e006b632043/zero-tap-plan-positive-totals.txt` and `observations.json`.

## F4 — A skipped case becomes a passing case

Starting from the healthy one-case TAP control, the case line alone was changed to:

```text
ok 1 - real case # SKIP historical input absent
```

Totals remained `tests 1`, `pass 1`, `fail 0`, `cancelled 0`, `skipped 0`, `todo 0`. Observed classification is PASS with `pass: 1`; the skipped line is also retained in `exclusions`.

The exclusion condition at line 179 only rejects fewer exclusion lines than declared skips/TODOs. It accepts an explicit skip with zero declared skips, so the sole excluded obligation is simultaneously recorded as a passing obligation. Keeping the text in `exclusions` does not repair the false pass count or verdict. Validate directive/count agreement and preserve skip/TODO non-pass accounting.

Evidence: `probe-run-5e006b632043/tap-skip-counted-as-pass.txt` and `observations.json`.

## F5 — Interruption after child exit drops every terminal record

The probe ran the actual `run` and `execute_command` functions with two immutable planned fake commands, `first` and `later`, and real temporary fixture/log/receipt files. The first fake child wrote a complete PASS object, flushed it, and returned code 0. The classifier boundary was then made to raise `KeyboardInterrupt`, representing a cancellation arriving after `subprocess.run` has returned.

Observed:

```text
exception: KeyboardInterrupt
child calls: first only
saved results.json status: RUNNING
planned commands: first, later
saved command records: []
first.log: retained complete PASS output
```

The catch at line 286 only covers the child-process call; classification at line 294 is outside it. `run` appends a row only after `execute_command` returns. The emitted receipt therefore has no terminal record even for the child that actually exited, and none for the unlaunched remainder. The saved plan survives, but the selected population never receives the promised terminal dispositions.

This is distinct from the existing `test_cancellation_preserves_denominator`, which raises inside the mocked subprocess and exercises the existing catch. Handle a catchable cancellation at the command/run boundary, preserve already observed process facts and logs, terminalize the remaining population under the declared continuation policy, and persist the incomplete result. This finding makes no claim about uncatchable process termination or failing storage.

Evidence: `probe-run-5e006b632043/interrupt-during-classification/receipt/results.json` and `first.log`.

## O1 — Source-change handling overwrites aggregate failure

A fake child changed a real synthetic `input.txt` in the isolated fixture directory and emitted a named FAIL result with exit 0. The actual source census detected the changed bytes. Both command rows were FAIL, with one terminal marker each; `summarize` therefore produced FAIL. Lines 367–369 then unconditionally changed the aggregate to INCOMPLETE because `sourceUnchanged` was false.

The result retained row failures and remained non-PASS. This is a semantic-priority concern, not another false green: the top-level status suppresses the observed FAIL category while `identityError` already describes the separate source-binding problem. Decide explicitly whether aggregate failure should dominate identity incompleteness, and document/test that precedence. It is the same general failure-dominance question as root's outer-INCOMPLETE parser check, exercised at the separate post-run identity boundary.

Evidence: `probe-run-5e006b632043/source-change-overwrites-aggregate-fail/receipt/results.json` plus the initial input digest and retained final `source/input.txt` bytes. The probe script contains both exact synthetic source strings; the runner does not store the entire final source census.

## O2 — Historical requirements are at whole-command granularity

Live preflight confirmed that `47c0fa0c6e32618f22b43b6a18717908b0de5f5e:index.html` is **currently available**, resolving to blob `9851aada8d04019ed47fd727f22d49c87ebd9fab`. There is no current missing-history blocker for this selected command.

A separate cheap controlled-boundary probe changed only `history_input` availability to false while retaining all three actual current inputs. The actual `execute_command` returned one terminal INCOMPLETE/not-started row for `r0021-reveal`; no child was launched. This is truthful at command level, but it suppresses all current subcases along with the historical one.

The inspected adapter demonstrates the granularity issue directly: `initial source hides only sky decorations and retains usable prayer/settings markup` (snapshot lines 24–28) reads current `source` and checks current markup/CSS without reading Git history. Many other current cases are declared before `moon PBR shader and embedded payloads retain exact accepted bytes`; only that final body reads the historical blob (lines 87–91). The command-wide history prerequisite is imposed by runner `HISTORY_INPUTS`/`check_setup`, before any of those current cases can execute.

This review does not claim those current behavior assertions pass, nor did it run them. If future history unavailability is in scope, preserve current-case execution separately from the affected historical criterion, either through explicit case-level incomplete results or an appropriately split selected population. Preserve the original command/case denominator and exact locator. The same coarse table covers other mixed commands, but only `r0021-reveal` received this controlled boundary reproduction.

Evidence: `history-scope-de0e268be9f4/observation.json`. Its reason expressly labels historical absence as a controlled double, not a claim about the live repository.

## Reproduction and limitations

From `/workspace/scratch/7a8daf93afaa/runner-review-evidence`:

```bash
python3 adversarial_probes.py
python3 history_scope_probe.py
```

Both scripts write new UUID-named evidence directories and import the frozen runner copy. The first script completed with exit 0 in approximately 0.1 seconds; exit 0 means the observation harness completed, not that the runner passed acceptance. The second completed with exit 0 in approximately 0.08 seconds. No real inherited child command runs. The historical availability check is a read-only Git object lookup with the runner's no-lazy-fetch environment.

The first script also tried a complete JSON envelope with 1,200 nested padding arrays. That hypothesis did **not** reproduce a parser exception on this host: the actual classifier/run returned PASS with intact terminals. The evidence label `deep-json-drops-terminals` records the tested hypothesis, not a finding; it is intentionally retained unchanged as original evidence. No claim of a recursion-related defect is made.

Healthy controls showed correct complete JSON/TAP admission and a two-command PASS receipt with exactly one terminal per selected command. I did not rerun the repository's full evaluator tests, broader suites, native campaigns, or root's exact five mutants. This review establishes these draft-level discriminators only.

## Read-file identities

The following exact file hashes cover every source/specification file inspected or byte-hashed for this task. Copied inputs are under `runner-review-evidence/inputs`; source-content inspection for the larger adapter files was targeted, not a full semantic audit.

- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/tools/cp9/run_native_regressions.py` — SHA-256 `4aa993b98ae364a633d71eccd44a6eecaf7f9dd22c456760ea977797f7614daa`
- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/tests/test_native_regression_runner.py` — SHA-256 `15e8efa8a16fd2cca93226e6e897fb526f2621d6021938d0a862ae6d25c0efe2`
- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/AGENTS.md` — SHA-256 `f506acbba2b5b2ade773c251342b41523b6e94cd740ee51a38ba15316714b948`
- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/tests/r0018-timetable-contrast.cjs` — SHA-256 `6d25bbafd0d7755e91a19113ab062a5ed8a56bd182a40346e7fbb8860855fdb0`
- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/tests/r0021-reveal.cjs` — SHA-256 `c66a0b967fd2de957c656f33ad32d9b84099ed7e3ce7f4c0841ac780918f76ca`
- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/tests/r0022-baseline-balance.cjs` — SHA-256 `6ddc11e8291b77e5532688ddec6a296b1ec3840dad8c0817d9779d3ddd847e79`
- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/tests/r0023-metadata.cjs` — SHA-256 `34bc3a071dbebf807ef8503396fa6279b39f7d3a2121b3fa8fc35653f41a0ce8`
- `/workspace/scratch/7a8daf93afaa/commission/prompts/01_R0017_EXECUTE.md` — SHA-256 `6322e8709e43c148c6948e692b8702a5a85465288efcee297f17876ecd137af9`
- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/index.html` — SHA-256 `b4a6831b80439d3002f9cf4fae5bc15943bc9f9f2fa5ab0c4a1fc09f33a57298` (actual setup digest only).
- `/workspace/scratch/7a8daf93afaa/r0017-explicit-work/config.js` — SHA-256 `91a37863cd85e232e9a63bba9db533b82699e63140086ba4b78fcf9c0581ec81` (actual setup digest only).

Final moving-worktree readback at 2026-11-07T03:45:22.805119+00:00:

- `tools/cp9/run_native_regressions.py` — `4aa993b98ae364a633d71eccd44a6eecaf7f9dd22c456760ea977797f7614daa` (21650 bytes).
- `tests/test_native_regression_runner.py` — `ed2cb9098b118083ecf55089a430644352ac04c4568b2fd5052f8543d9b169d7` (18678 bytes).

Authoritative raw observations: `/workspace/scratch/7a8daf93afaa/runner-review-evidence/probe-run-5e006b632043/observations.json` and `/workspace/scratch/7a8daf93afaa/runner-review-evidence/history-scope-de0e268be9f4/observation.json`.
