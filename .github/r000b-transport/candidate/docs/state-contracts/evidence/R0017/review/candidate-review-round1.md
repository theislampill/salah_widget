# Independent source review: R0017 / #23

## Disposition

**GAP-REVISE** — the reviewed evaluator admits two malformed or contradictory child outputs as a successful command and successful invocation. This is a pre-commit source finding, not final candidate acceptance. Immutable candidate head/tree and joined evidence have not yet been supplied.

## Reviewer and independence

- Reviewer: `/root/candidate_review`.
- Actual model self-report: ChatGPT, GPT-6 Astra Pro.
- `authoring_context_reuse: no`.
- `other_reviewer_output_seen: no`.
- Read-only independent source inspection. No product/source edits, commits, broad suites, browser campaigns, terrain/science/native campaigns, network publication, or subagents were performed. This report is the requested review artifact.
- Authority is limited to evaluating the scoped evaluator repair and review readiness. No merge, deployment, whole-issue closure, or residual waiver is granted.

## Identity and evidence binding

- Required base commit: `f71fef6ccf7e4efcb57b5a26688d2360461a3253`.
- Required base tree: `79aedcac840d624b5ea423922314f0832dc3f750`.
- Observed worktree HEAD at the time of the probes: `f71fef6ccf7e4efcb57b5a26688d2360461a3253`.
- Observed worktree HEAD tree: `79aedcac840d624b5ea423922314f0832dc3f750`.
- Immutable candidate commit/tree: **not yet supplied**. The reviewed implementation is the staged working overlay in `/workspace/scratch/7a8daf93afaa/r0017-explicit-work`, not the base tree itself.
- Inspected evaluator SHA-256: `88a3b3e8672a2f79a2cbdf455e1389ec141a3d2ddbc800a2eeff00a91b2217a3` (`tools/cp9/run_native_regressions.py`).
- Inspected control fixture SHA-256: `8f7b2f5ad21f71eb6af739e2461435ec6647da1cd50b24a8e5d8fda10a980128` (`tests/test_native_regression_runner.py`).
- These findings are bound to those bytes. Any subsequent repair requires refreshed identity and verification before final acceptance.

## Findings

### F1 — a named result array overrides contradictory failure totals

Location: `tools/cp9/run_native_regressions.py`, `classify_output`, named-results branch.

Input:

```json
{"passed":0,"failed":1,"results":[{"name":"actual case","status":"PASS"}]}
```

The classifier validates aliases against each other, but once `results` is a list it ignores the numeric summary fields. The above contradictory output returns `status: PASS`, `executionProven: true`, `passCases: 1`, and `failCases: 0`.

I exercised the actual `runner.run` path through the implementation's controlled child fixture with exit code zero and a controlled one-second clock. The command status and aggregate status were both **PASS**. The healthy named-results control also remained PASS. This is not merely a helper-level assertion.

The supplied failure count is direct contradictory evidence and must not become PASS. This violates ES17-04's malformed/contradictory output contract. Validate every supplied count/declared-population field against the named cases or reject mixed inconsistent envelopes as INCOMPLETE. Add a regression through the actual command path.

### F2 — a prefixed, indented truncated envelope is skipped to salvage a success object

Location: `tools/cp9/run_native_regressions.py`, `terminal_json`, JSON-offset discovery.

Input (literal line breaks):

```text
before
  {"truncated":
{"results":[{"name":"actual case","status":"PASS"}]}
```

Offsets are collected only for a `{` at column zero, with a separate exception only when the entire output begins with an object after leading whitespace. Because this output has a preceding text line, the malformed indented object is invisible to discovery. The later object is parsed as the final success envelope, although it is nested in an unclosed earlier JSON object.

Again I exercised `runner.run` through the controlled child boundary. With exit zero, the output classifier, command verdict, and invocation verdict all became **PASS**; the measured command elapsed remained one second. This violates the explicit ES17-04 requirement not to salvage a nested/later success object from a broken earlier envelope.

Admit only the supported complete output grammar and recognize earlier line-leading JSON with indentation, so a malformed earlier object prevents a later success from being used as completion evidence. Preserve the two actual diagnostic JSON shapes already supported. Add this prefixed/indented negative alongside the existing leading-truncated negative.

## Probe method

Loaded the submitted `tests/test_native_regression_runner.py` using `importlib`, instantiated `RunnerLifecycleTests`, called `setUp`, and ran `run_fixture` separately for the healthy control and each input above. This invokes the actual evaluator entry point, log classification, command lifecycle, receipt serialization, and summarization while replacing only the child execution and clocks with the existing explicit doubles. Each probe made exactly one child call. Temporary fixtures were cleaned up. `PYTHONDONTWRITEBYTECODE=1` prevented bytecode writes.

Observed result for both negatives:

```json
{"status":"PASS","command_status":"PASS","output":{"format":"json-results","status":"PASS","executionProven":true,"counts":{"passCases":1,"failCases":0},"reason":"complete named result array","exclusions":[]},"seconds":1,"calls":1}
```

## Inspection completed and remaining acceptance work

Read the full R0017 commission and repository AGENTS instructions, the full proposed evaluator and evaluator controls, the shared script contract and adapter controls, the changed bootstrap/transport/adaptor sections, the R0017 contract document, and the unchanged real evaluator consumer `tools/cp9/qualify_candidate.py`. Traced imports from affected adapter owners to their real fixture consumers. No product/runtime/generated/science/V1/installer modification was observed in the staged changed-path list.

Final acceptance still requires the repaired immutable candidate base/head/tree, the complete base-to-head diff including packaged evidence, exact evidence binding and the real product-guard mutation receipts. The two findings above are sufficient to withhold acceptance now; no final evidence conclusion is inferred from source alone.

## Residuals explicitly preserved

The unavailable exact historical `8b83df029966c203a503ab217d121c48b8ee6e8a` input, the real PBR equality failure versus the retained `47c0fa0c6e32618f22b43b6a18717908b0de5f5e` baseline, five still-required replacement stellar observations, four TODO joins, and fresh browser/platform observations remain unresolved or unrun as specified by the commission. None is a pass or an automatic waiver. The original smoke closure is a distinct historical claim and is not enlarged by this review.
