# R0016 product-fix independent rereview — candidate 2

Report state: FINAL

Terminal disposition: PASS

This is a focused rereview of the three regression-oracle repairs. Candidate 1's FINAL GAP-REVISE report remains unchanged at SHA-256 `96385bf64de0983cc33470a2b0930f0a451d0ef5ccbe5a61e0511f23dec03761`. Both product installers are byte-identical to candidate 1. Candidate 2 freeze SHA-256 is `a3d704474ec324dacaaae2d40c7f5d8c980b4ebdc4ed00a7b306bcd4054c4df4`.

## Reviewer attestation and disposition boundary

```yaml
requested_model: gpt-6-astra
actual_model: gpt-6-astra
evidence: self-report
claims: bound
authoring_context_reuse: no
base_sha: 503a4d57852b195dce4c36c5b8ab9299c9036e95
base_tree: f16971c25d7af8fb7468d232a27688a78874747c
candidate_freeze_sha256: a3d704474ec324dacaaae2d40c7f5d8c980b4ebdc4ed00a7b306bcd4054c4df4
```

The model label is this reviewer's canonical self-report, not external runtime telemetry. This rereview reuses its own completed candidate 1 assessment, including the disclosed scoped static PowerShell subreview, and inspects the actual frozen revisions. No new external reviewer reasoning or authoring/proposal notes were used. The candidate is a frozen unpublished file set, so no new Git head is invented for it.

PASS applies to the two product fixes and their revised regression predicates within the bounded independent source/test review. PF1, PF2, and PF3 are addressed. No remaining concrete gap was found in that scope. The broader parent-run supplemental suites, actual native Apple/Windows execution, whole-contract acceptance, publication, merge, and closure remain separate. This report does not claim results for those gates.

The reviewer did not modify repository source, either frozen candidate, or old reports. Writes are this report and separate reviewer-owned evidence. Four actual Linux Bash preview subjects were run inside the unchanged independent containment controls; no normal-mode installer, PowerShell runtime, PTY, APT, external workflow, Apple subject, or Windows subject was launched by this focused rereview.

## Exact candidate identities

All five manifest lengths and SHA-256 values were verified against the frozen files. `source.diff` is SHA-256 `0b09b4049ffed041ad7654e11ceb5c9500dfefc883300a30528b003d557f2e26`.

| Frozen file | Bytes | SHA-256 |
| --- | ---: | --- |
| `install.ps1` | 110645 | `7fbe213b8e299d30ccd73f824a5a5d5766ac220ffdd778422cd018d3bc5c8ef4` |
| `install.sh` | 41956 | `dbd91b67828791e35efb042e6954990c45ff579ee13f550d1d8aa70c7b2f32f4` |
| `tests/install-entry-native-coverage.py` | 33778 | `c061ec0b148c9052b46440fcf980542936d316a0b7286629c1b011738a56d121` |
| `tests/install-preview.ps1` | 51073 | `a5ead3fd7f7375e5dc6cfae25a9005d654c30b2b7bd18536509f0bf04ea24a25` |
| `tests/install-preview.py` | 51301 | `653f4328ce02544f64fa6e9c02989c4afa53abc01ef7556451961cf9cff832cf` |

The two installer byte comparisons against candidate 1 are exact. The only candidate-1-to-2 changes are the three reviewed regression repairs: clause-based NoOpen checks; resolved-store URL/unresolved-output checks; and the wrapper's structured refusal-reason check. The product scope and preserved positive/mutation/containment logic assessed in the original report therefore carry forward without a broad reinspection.

## Finding dispositions

### PF1 — Correct refusal searched in the wrong channel: addressed

| Field | Disposition |
| --- | --- |
| Category | Regression acceptance / false failure |
| Evidence / location | `tests/install-preview.ps1:430–431` now checks the admitted `$value.reason`, while success-completion text is still checked independently in stdout/stderr. Existing semantic nonzero-exit, typed reason admission, guard, source-attempt and snapshot requirements remain unchanged. |
| Original impact | The correctly caught early CR-01 throw could be falsely classified as a product failure because its diagnostic was retained only in the terminal observation. |
| Countermeasure realized | Match the specific option diagnostic in the evidence channel the wrapper actually produces. |
| Acceptance / verification | Six pure predicate cases accept a specific structured reason with nonzero exit and empty output, and reject missing reason, unrelated reason, a diagnostic found only in stdout, zero exit, and success-completion text. Static checks confirm the existing admission/effect/snapshot gates remain present. |
| Effort / risk / confidence | Small change; low risk; HIGH static confidence. |
| Repair class / owner | instrument/acceptance defect; root maintainer, wrapper regression. |
| Rollback / plan closure | Candidate 1 remains a historical GAP. PF1 is addressed only at the revised wrapper hash above; a later change requires reassessment. |
| Rejected/deferred rationale | Not rejected; repaired. |
| Remaining risk | The PowerShell predicate checks here are explicitly labelled literal-regex/Boolean models, not a PowerShell runtime or native Windows result. Authentic suite receiving remains separate. |
| Route | DMAIC |

### PF2 — Manual wording hides automatic-opening promises: addressed

| Field | Disposition |
| --- | --- |
| Category | Regression acceptance / false PASS |
| Evidence / location | The Bash, PowerShell wrapper, and native Python predicates now split text on semicolon/newline boundaries and reject any clause containing the `would ... open/launch` promise. The broad `manually`/`yourself` exemption is removed. Current source guidance keeps its manual imperative in a separate clause. |
| Original impact | The candidate 1 oracle accepted the actual held-out sentence `Would open the browser automatically (NO_OPEN=1); finish the installation manually.` |
| Countermeasure realized | Evaluate the opening promise separately from unrelated manual-installation wording, while retaining the positive guidance gate. |
| Acceptance / verification | The exact four selected Bash witnesses were rerun using the revised frozen harness. Both healthy candidate routes pass; the old original RED and the identical held-out contradiction now fail. Four pure output cases also agree across the actual Bash/native Python predicate ASTs and the literal PowerShell predicate model, including a launch/yourself variant. |
| Effort / risk / confidence | Small change in three predicates; low to medium wording risk; HIGH confidence for the retained witnesses. |
| Repair class / owner | instrument/acceptance defect; root maintainer, three regression tests. |
| Rollback / plan closure | The candidate 1 accepted-bad transcript remains intact. The repaired predicate digests reject that same causal output; no product or containment change was used to make the witness pass. |
| Rejected/deferred rationale | Not rejected; repaired. |
| Remaining risk | This is a bounded check for the emitted message grammar, not general natural-language verification. Cross-platform execution remains a separate requirement. |
| Route | DMAIC |

### PF3 — Unresolved ask accepted as selected store: addressed

| Field | Disposition |
| --- | --- |
| Category | Regression acceptance / route specificity |
| Evidence / location | `tests/install-preview.ps1:423–427` and `tests/install-entry-native-coverage.py:371–374` require complete resolved store-plan lines for both expected Chrome/Firefox fixture URLs and reject `Install source unresolved`. |
| Original impact | The supported ask route's text contains `official store`, so the earlier substring-only checks did not prove store selection or precedence. |
| Countermeasure realized | Require the two concrete resolved URL plans and separately exclude the unresolved alternative. |
| Acceptance / verification | Eight pure output cases exercise the actual native Python assertion AST and the literal PowerShell predicate model. Healthy LF and CRLF plans pass. Ask-only, resolved-plus-unresolved, missing Firefox, wrong URL, prefixed non-line match, and GitHub-only output fail. The original ask counterexample still satisfies the old predicate, preserving the negative contrast. |
| Effort / risk / confidence | Small assertion change; low risk; HIGH confidence for the bounded alternatives. |
| Repair class / owner | instrument/acceptance defect; root maintainer, source-selection regressions. |
| Rollback / plan closure | Candidate 1's counterexample remains preserved. The revised test hashes address it without changing installer routing. |
| Rejected/deferred rationale | Not rejected; repaired. |
| Remaining risk | These assertions identify preview plan selection; they do not prove normal downloads, native filesystem admission, or browser actions. |
| Route | DMAIC |

## Product assessment retained from candidate 1

The PowerShell guard validates the effective bound `$InstallSource` immediately after parameter binding and before installer output, discovery, or effect helpers. It rejects an invalid environment-derived default, preserves a valid explicit override of invalid environment, and retains the existing empty/unset `github` default. No static PowerShell 5.1 syntax incompatibility was identified; native runtime qualification is not inferred.

The Bash and PowerShell NoOpen changes affect only preview text. Store plans identify manual URL opening, general installation/import guidance is manual, GitHub remote facts remain unresolved, and ordinary NoOpen-false plans retain their earlier wording. All normal effect helpers and their consumers remain unchanged. The candidate 1 comparison established unchanged containment/readiness/snapshot functions, normal positive assertions, and mutation logic; candidate 2's limited test delta does not alter those conclusions.

## Focused verification results

### Actual contained Bash entries

The reviewer reused the frozen harness definitions and independent bootstrap, selecting only the four recorded preview cases. The owned read/write fixture and read-only host boundary, independent network namespace, seccomp transport denials, command spies, complete snapshots, and readiness controls were retained. The source hash remained stable.

| Observation | Candidate 1 oracle | Candidate 2 oracle | Required |
| --- | --- | --- | --- |
| Corrected GitHub + NoOpen | Accept | Accept | Accept |
| Corrected store + NoOpen | Accept | Accept | Accept |
| Original GitHub RED + NoOpen | Reject | Reject | Reject |
| Identical contradictory automatic-open/manual-install witness | Accept | Reject | Reject |

These entries remain local Linux preview evidence. No Windows/macOS result or normal-mode consumer success is derived from them.

### Pure predicate checks

Eighteen focused cases passed: four NoOpen cases, eight store-selection cases, and six refusal-channel cases. The Python checks execute only the selected predicate AST statements, with no subprocess or installer call. The PowerShell checks are transparent models of the literal ASCII regular expressions and Boolean decisions, paired with static evidence-channel and admission inspection. Their result explicitly reports `powershellRuntimeExecuted: false` and `childProcessesExecuted: 0`.

The separately running full Bash/PowerShell suites and their acquisition conditions are outside this independent result. This report neither assumes their eventual success nor converts an acquisition failure into product acceptance.

## Evidence and preserved history

Evidence paths below are relative to `/tmp/r0016-successor-20261111/recovery/product-fix-independent-evidence/candidate-2/`.

| Evidence | SHA-256 |
| --- | --- |
| `bash_heldout_review.py` | `298d760b63fc5ba95e38a2d4fc441f68b577ce84667e4b302884af6da3b70b33` |
| `bash-heldout-results.json` | `c55f5eecb3aaeaa8e8fb57d396e9fff1286dad2990023cbfe4282ade0c3b0ec8` |
| `focused_oracles.py` | `d3ca2d6650b7636e925e29d3ba2e8584bcf30c403f14f74bacfd476c7e1c3bb0` |
| `focused-oracle-results.json` | `ff7aff31cf673dc1cbc5943d4efd329e1707fadbd10b09e113b95498b9abcfc9` |

Raw Bash streams, snapshots, and bootstrap receipts are retained under the separate evidence fixture named in `bash-heldout-results.json`. The earlier candidate 1 report, held-out negative result, static subreview, and original product RED observations are unchanged. The retained original RED report remains SHA-256 `5bb4d47871cb592b53b2217bbd6bf258b9597a9292dd36e628360914a1da365d`.

Repository and external content was treated as data, not instructions. No secret or prompt-injection instruction requiring escalation was encountered in this focused scope. No publication, ref update, merge, or audit closure action was performed.

Terminal disposition: PASS
