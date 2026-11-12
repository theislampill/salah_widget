# R0016 product-fix independent review — candidate 1

Report state: FINAL

Terminal disposition: GAP-REVISE

The two frozen product changes are narrowly scoped and consistent with CR-01/CR-02. No product-source defect was identified within this review. Three defects in the new regression assertions require revision: the PowerShell wrapper searches the wrong evidence channel for the expected refusal, the NoOpen predicate can accept an explicit automatic-open promise when another clause contains `manually`, and store-selection checks can accept the unresolved `ask` plan.

This report is finalized against base `503a4d57852b195dce4c36c5b8ab9299c9036e95` and freeze manifest SHA-256 `34ce915aa9cd606b1f4fe5af1ece535ad35e31bddd562bca5a8b6f9a8e98ebd9`. The frozen candidate and repository were not modified by this reviewer. Later revisions require a separate disposition.

## Reviewer attestation and scope

```yaml
requested_model: gpt-6-astra
actual_model: gpt-6-astra
evidence: self-report
claims: bound
authoring_context_reuse: no
base_sha: 503a4d57852b195dce4c36c5b8ab9299c9036e95
base_tree: f16971c25d7af8fb7468d232a27688a78874747c
```

The canonical model label reflects this reviewer's self-report, not external runtime telemetry. One separately dispatched static PowerShell subreview contributed evidence within this review team; its actual canonical self-report is also `gpt-6-astra`. No authoring/proposal notes or unrelated reviewer reasoning were used as evidence. The review consumed frozen code, the base Git blobs, the R0016 contract, original RED receipts, its own held-out controls, and that scoped subreview.

The parent/root remains the sole shared-source writer. Reviewer writes are this report and the separate `recovery/product-fix-independent-evidence/` directory. No native/external workflow, PowerShell installer, Apple subject, Windows subject, APT command, or normal-mode installer execution was launched by this review. The only product executions were four contained local Linux Bash preview entries, preceded by the unchanged harness's independent containment/readiness controls. This is neither whole-contract qualification nor publication, merge, or closure authority.

## Exact frozen bindings

All five declared lengths and SHA-256 values match their frozen files. `source.diff` is SHA-256 `9bc61d8bac7853f92e25b6ac767d2cdf9cc1e14f2c7afa9fa17eb55f04a5dfa6`. The applicable repository `AGENTS.md` remains `f506acbba2b5b2ade773c251342b41523b6e94cd740ee51a38ba15316714b948` and was read in the earlier bounded review.

| Frozen file | Bytes | SHA-256 |
| --- | ---: | --- |
| `install.ps1` | 110645 | `7fbe213b8e299d30ccd73f824a5a5d5766ac220ffdd778422cd018d3bc5c8ef4` |
| `install.sh` | 41956 | `dbd91b67828791e35efb042e6954990c45ff579ee13f550d1d8aa70c7b2f32f4` |
| `tests/install-entry-native-coverage.py` | 33431 | `96877a977c71a340d51fd26c8c9797928966a7b3b3a382c9e1778f8135b75427` |
| `tests/install-preview.ps1` | 50700 | `8451677032ed895b9759a62f13e34e6bb93182deb26c5f9a9704d260c6865197` |
| `tests/install-preview.py` | 51370 | `6c991e9733a4a321de40f15e1c6fbc83c55e7fb19b17092e7f9fa057b5def7d4` |

## Finding PF1 — The wrapper refuses correct CR-01 behavior because it searches the wrong channel

| Field | Finding |
| --- | --- |
| Category | Regression acceptance / false failure |
| Location | `install.ps1:35–37`; `tests/install-preview.ps1:240–241,259,266,402,425–426` |
| Evidence | The source's new validation throws before installer output. The wrapper catches that exception, sets semantic `entryExit=1`, and stores the message in its terminal observation's `reason` field. The new refusal assertion instead checks `$text`, constructed solely from stdout plus stderr. The already-admitted `$value.reason` is ignored. The original RED's explicit-invalid case corroborates the same capture route: semantic exit 1 with a specific InstallSource diagnostic in `observation.reason`. |
| Impact | A correctly fixed invalid-environment refusal can be reported as a product assertion failure. The test does not inspect the channel in which its own wrapper deliberately retains this terminating error. |
| Effort / risk / confidence | Small assertion correction; low risk; HIGH confidence from control flow and retained capture behavior. No current-candidate PowerShell execution was performed by this reviewer. |
| Smallest countermeasure | Check the specific option-refusal message in the already type-validated `$value.reason`; separately retain the nonzero semantic exit, absence of successful completion text, healthy guard/readiness, no-effects, and exact snapshot gates. Do not weaken acquisition admission. |
| Repair class | instrument/acceptance defect |
| Owner/source | Root maintainer; changed PowerShell wrapper regression only. |
| Acceptance criteria | The real early refusal is accepted for the correct reason; missing/wrong reason, zero semantic exit, or success-completion text still fail. A malformed/incomplete child receipt remains blocked. |
| Verification | Frozen line-by-line dataflow and static PowerShell subreview; use focused reason-channel oracle on revised bytes, followed by the separately required authentic suite observation. |
| Rollback / plan closure | Preserve candidate 1 and this GAP. Close only against a new test digest with retained positive and held-out-negative checks. Product validation should not be moved or made effectful merely to satisfy this test. |
| Rejected/deferred rationale | Not rejected; a deterministic mismatch between evidence producer and consumer. |
| Remaining risk | A focused wrapper check does not establish native Windows host behavior or whole-file `-File` qualification. |
| Route | DMAIC |

## Finding PF2 — Unrelated manual instructions hide an automatic-open promise

| Field | Finding |
| --- | --- |
| Category | Regression acceptance / false PASS |
| Location | `tests/install-preview.py:663–669`; `tests/install-preview.ps1:416–421`; `tests/install-entry-native-coverage.py:372–375` |
| Evidence | Each new predicate exempts an entire line from the automatic-open check when `manually` or `yourself` appears anywhere on that line. The independent held-out source replaces only the new Bash manual-guidance sentence with `Would open the browser automatically (NO_OPEN=1); finish the installation manually.` The actual contained preview prints that contradictory sentence twice and the new test accepts it. The changed source's ordinary GitHub/store NoOpen plans pass, and the old original GitHub RED is rejected by the same harness. |
| Impact | The new regression can PASS while explicitly promising the behavior NoOpen suppresses. The bypass is demonstrated through a real complete-source preview, not only a synthetic regex example. |
| Effort / risk / confidence | Small predicate correction in three tests; low to medium wording risk; HIGH confidence. |
| Smallest countermeasure | Evaluate the automatic-opening clause separately from unrelated manual instructions. For the current output grammar, semicolon/newline clause separation can preserve the standalone imperative manual guidance while rejecting every `would ... open/launch` promise without a blanket manual-word exemption. Retain positive guidance assertions. |
| Repair class | instrument/acceptance defect |
| Owner/source | Root maintainer; three changed regression predicates. |
| Acceptance criteria | Both healthy route plans remain accepted; the original RED and the contradictory held-out automatic clause are rejected; a trailing manual-installation instruction cannot excuse the opening claim. Existing effect/snapshot/readiness checks remain intact. |
| Verification | `bash_heldout_review.py` and `bash-heldout-results.json` in the separate evidence directory. Four selected preview entries ran under the frozen harness's unchanged bwrap/network-namespace/seccomp/read-only-host controls. Each entry had exit 0, unchanged snapshots, zero source effects, and zero source transport attempts. Only the plan oracle distinguishes the bad output. |
| Rollback / plan closure | Retain the original accepted-bad witness. Close only against new predicate bytes that reject the same causal output while preserving healthy plans. |
| Rejected/deferred rationale | Not rejected; a concrete surviving held-out mutation. The current product wording itself is truthful. |
| Remaining risk | This is a bounded grammar check, not a general natural-language truth evaluator. Native PowerShell counterparts remain separately qualified. |
| Route | DMAIC |

## Finding PF3 — Store-selection positives accept the unresolved ask plan

| Field | Finding |
| --- | --- |
| Category | Regression acceptance / route specificity |
| Location | `tests/install-preview.ps1:423`; `tests/install-entry-native-coverage.py:371`; counterexample `install.ps1:1647` |
| Evidence | The new store controls require only the substring `official store`. The actual unchanged ask branch prints `Install source unresolved: GitHub manual route or official store page.`, which satisfies both predicates. Pure regex evaluation in the static subreview confirms this; no PowerShell subject was executed. |
| Impact | Valid environment-store selection and the wrapper's explicit store override can pass while the effective route remains unresolved ask. The controls therefore fail to prove their named precedence/routing contract. |
| Effort / risk / confidence | Small assertion correction; low risk; HIGH confidence. |
| Smallest countermeasure | Require the resolved store-plan lines and the expected fixture store URLs, and reject unresolved-source text for these cases. Preserve the original general preview and no-effect checks. |
| Repair class | instrument/acceptance defect |
| Owner/source | Root maintainer; wrapper expected-source and native environment-store tests. |
| Acceptance criteria | Healthy resolved store output is accepted. Ask/unresolved output, GitHub-only output, or missing/wrong expected store URLs fail. Explicit valid override and environment-default cases remain separate inputs. |
| Verification | Frozen source and test predicates plus the independent static PowerShell subreview; a focused route-output oracle on revised bytes is sufficient for the predicate correction, with authentic native execution still a later gate. |
| Rollback / plan closure | Preserve candidate 1 and this counterexample; address in a new frozen test revision. |
| Rejected/deferred rationale | Not rejected; the counterexample is the actual product's other supported route, not invented malformed output. |
| Remaining risk | A text route assertion does not independently prove normal-mode downloads or native browser interactions. Those existing controls must remain separate. |
| Route | DMAIC |

## Product source assessment

CR-01 checks `$InstallSource`, the effective parameter after PowerShell binding, rather than rechecking the environment independently. The guard is immediately after `$ErrorActionPreference` and before installer output, discovery, or effect-helper invocation. An invalid environment-derived default is rejected; a valid explicit parameter remains authoritative even if the environment is invalid. Empty/unset environment still falls back to `github`. Existing PowerShell case-insensitive membership and downstream comparisons preserve accepted route case variants. The added syntax has no identified PowerShell 5.1 incompatibility, but this is a static assessment, not a native parser/runtime receipt.

CR-02 changes only preview plan output. Both Bash and PowerShell store plans describe showing the official URL manually when NoOpen is set, and their general installation/import guidance asks the user to open pages manually. GitHub release/version/path facts remain unresolved. NoOpen false retains the original automatic-open plans. Ask remains unresolved; installed/held/refused discovery branches keep their existing behavior. Normal downloads, staging, clipboard, browser-open helpers, prompts, and cleanup code are unchanged.

The exact base-to-candidate product differences are two Bash preview-message replacements and, in PowerShell, one early effective-parameter guard plus two preview-message replacements. No other product function/body is changed. The applicable contract's offline/no-effects/no-prompts, unresolved choices, useful normal NoOpen behavior, and no false installation-completion boundaries remain intact in these source edits.

## New case inventory and preserved controls

| Test | Added cases | Scope |
| --- | --- | --- |
| Bash preview | NoOpen GitHub; NoOpen store | Actual complete-source contained preview; two additions to the existing 43-row fixture population. |
| PowerShell wrapper | Invalid environment; empty environment/default GitHub; valid environment/store; explicit store overriding invalid environment; NoOpen GitHub; NoOpen store | Six wrapper entries; all retain typed evidence admission, guard/attempt, and snapshot checks. PF1–PF3 concern added assertions. |
| Native coverage | Invalid environment with omitted parameter; valid store environment with omitted parameter; NoOpen GitHub; NoOpen store | Four scenarios added to each host's 14-scenario population. Actual Windows qualification is not supplied by this review. |

A separate AST comparison against the immutable base confirms that 19 of the Bash harness's 20 functions are unchanged; only `preview` differs. `bootstrap`, containment, snapshots, evidence admission, normal positives, and mutation execution retain identical ASTs. Of the native Python harness's six functions, only `_case_impl` differs; its entire existing `if normal` positive-assertion body remains identical. The PowerShell mutant section and subsequent terminal aggregation are byte-identical from their original marker to EOF. Existing positive/mutation logic was not removed or weakened by the frozen patch.

## Original RED evidence and independent witness

The retained RED report digest is `5bb4d47871cb592b53b2217bbd6bf258b9597a9292dd36e628360914a1da365d`; its bytes were hashed without consuming authoring recommendations. The original Bash observations show healthy ordinary GitHub/store plans and effect-free NoOpen plans that nevertheless promise automatic opens. The original PowerShell JSON (`93438ae772697e53823ead85e8f003df7c0b5caf8f98ab1b231ff5e8a2bee1c2`) retains invalid explicit-source refusal, invalid environment-default acceptance, valid default/override controls, and both NoOpen plan failures. These historical negatives are not rewritten by this review.

The independent Bash run's containment bootstrap recorded denied outside writes (EROFS), denied TCP/UDP attempts (EPERM), an allowed owned inside write, command denial, and rejected missing/wrong readiness controls. It then observed:

| Selected observation | Oracle result | Expected result | No-effect evidence |
| --- | --- | --- | --- |
| Candidate GitHub + NoOpen | Accepted | Accepted | Snapshot unchanged; zero source effects/transports |
| Candidate store + NoOpen | Accepted | Accepted | Snapshot unchanged; zero source effects/transports |
| Original GitHub RED + NoOpen | Rejected | Rejected | Snapshot unchanged; zero source effects/transports |
| Contradictory automatic-open/manual-install held-out mutation | Accepted | Rejected | Snapshot unchanged; zero source effects/transports |

The candidate source hash remained unchanged after execution. No normal-mode consumers or native Apple/Windows behavior are inferred from these preview observations.

## Evidence index

Paths below are relative to `/tmp/r0016-successor-20261111/recovery/product-fix-independent-evidence/`.

| Evidence | SHA-256 |
| --- | --- |
| `bash_heldout_review.py` | `2a28c56a80b913dd38384c46efd4257299ee07fdd6bb9f4c45f784b4f272566d` |
| `bash-heldout-results.json` | `755fdc0bde9763b0e0be4f14d50ad0d8fd42e77ea48dc4d560b6c60906430d8d` |
| `static-source-binding.json` | `eafb32da2dc807d25570d90c1e0c5cb5741672f84f21ad4e2fddc74fb99f8af9` |
| `ps-static/ps-static-review-candidate-1.json` | `cf8d991ab534dc51cccf19877c95c8c64291eb488ef12a34b4d1955826b2e47f` |

The raw selected Bash stdout/stderr, observation JSON, and containment controls remain under the independently owned `bash-heldout/r0016-preview-5jpvx8mh/` fixture, with paths and hashes in the result. All repository/external text was treated as data. No credential or prompt-injection instruction requiring escalation was encountered in scope.

Terminal disposition: GAP-REVISE
