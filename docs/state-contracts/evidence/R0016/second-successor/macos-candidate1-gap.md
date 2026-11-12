FINAL

# Independent review — macOS terminal-parent harness correction

**GAP-REVISE.** The frozen correction preserves the original child, sandbox, and outer 30-second timeout, and its normal drain/reap path is consistent with the retained diagnostic evidence. Two error/acceptance boundaries still require correction: cleanup signals the numeric PID after `waitpid` reports that no matching child exists, and a zero exit observed after the declared 25-second work deadline can still pass. Both are reproduced through inert exact-parent control-flow oracles; neither is claimed as an observed macOS failure.

This review grants no product acceptance, native macOS qualification, publication, merge, issue closure, or audit closure authority. The root remains the sole source writer. Other product changes are outside this review and were checked only for byte preservation against the supplied candidate2 baseline.

## Exact source and reviewer identity

| Item | Identity / attestation |
| --- | --- |
| Reviewer | `/root/windows_diagnostic_review`, independently assigned this bounded macOS harness review |
| Requested canonical model | `gpt-6-astra`, continuing inherited reviewer; no model override or respawn |
| Actual canonical model self-report | `gpt-6-astra`, identified in this session as GPT-6 Astra Pro; no independent provider-routing attestation |
| Candidate directory | `/tmp/r0016-successor-20261111/recovery/macos-harness-candidate-1/` |
| Freeze SHA256 | `abefe111f478a2b0dc9a286ca114bc74b5e2e32f3aa06c9dfea66dc9481d58c6` |
| Candidate harness SHA256 | `f9eb146d50e13b3b0361586bf38c266db300e049e37dd9a83fdd2f7b412c271b` |
| Extracted terminal probe SHA256 | `ce2cf350f4738875dd34d98efcc5ce6ff8428948d55581af9a897903f2909a2f` |
| Product harness baseline | `/tmp/r0016-successor-20261111/recovery/product-fix-candidate-2/tests/install-preview.py`, SHA256 `653f4328ce02544f64fa6e9c02989c4afa53abc01ef7556451961cf9cff832cf` |
| Repository HEAD observed | `9c51a09e0e21722fdf9c7eafb2c7d9c1bf4ec196` |
| Repository tree observed | `7255c19060376234641d962cdf0fc20b7c0be72c` |
| Native diagnostic bridge source | `503a4d57852b195dce4c36c5b8ab9299c9036e95`, tree `f16971c25d7af8fb7468d232a27688a78874747c`, run `43088148764` |
| Original source / dependency provenance | Original source `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5`, tree `988d6191b24c6f64b6c71014a0077be1e48c4327`; dependency base `bf566111fe530b5de2c7c63ca4586e83d5f4b965` |
| Independence | No authoring notes or other product reviewer conclusions were used. The specifically supplied native receiving report/adjudication were read as historical evidence, and selected original captures were independently hashed/read. |
| Write boundary | This report and this candidate's `independent-evidence/` only. No repository/source changes, real signals, subject process launches, PTYs, native tests, workflows, remote mutations, or Git reference changes. |

The live worktree still contains the five root-owned installer/test edits noted in earlier binding work. This report is bound to the frozen files above and does not accept those other edits.

## Source and native-evidence boundary

The harness text before and after the embedded `terminal_probe` literal is byte-identical to the supplied candidate2 harness. The extracted literal exactly equals the frozen `terminal-probe.py`. The original child `if pid==0` block is byte-identical, SHA256 `3774840e5c68c186a2f70ba77083fa6159b73feaaba1e6f21e15fecb8c26f2cb`. The old complete terminal snippet has SHA256 `8ed996292207a690dd3f1ef153b2cf8650a8594aa7e3c8bffb30b6017407d904`, matching the retained native original. `darwin_profile`, `sandbox_run(timeout=30)`, the terminal invocation, and its outer return-code/JSON gates are unchanged.

The supplied native adjudication has SHA256 `6871d3ec1417072b35e45a832fde66301488c1da40ad20fdc8309fe3d17960e6`. In the retained same-profile and host-control observations, raw PTY bytes equal `native terminal control\r\n`; actual `waitpid.after` records identify the respective children with status 0; `cleanup.final` records `reaped=true`, `masterClosed=true`, and no signals. The selected raw phase/stdout/stderr/PTY hashes reconcile with the adjudication. The native report records zero product rows. These observations support the drain-before-wait correction, but do not exercise this new compact parent's error paths or establish product qualification.

## MHR-001 — Cleanup can signal a PID after child ownership is lost

| Finding Row Contract field | Finding |
| --- | --- |
| Finding title | Cleanup can signal a numeric PID after `waitpid` reports no matching child |
| Category | Cleanup ownership and process-safety boundary; high conditional impact |
| Evidence | `terminal-probe.py:37` calls `waitpid(pid, WNOHANG)`. `ChildProcessError` is caught by the broad handler at line 42, leaving `reaped=False`. The `finally` branch at line 47 then calls `kill(pid, SIGKILL)` at line 49. The inert `lost_child_echild` case retains the exact sequence `waitpid -> ECHILD`, then a kill attempt against that same now-unowned numeric PID. Corresponding harness lines are 546, 551, 556, and 558. |
| Impact | After a no-child result, the local false `reaped` flag does not establish an unreaped direct child. A signal based only on that flag can target an unrelated process if the PID has become reusable. The probe's final acceptance remains false in this case, but the cleanup side effect violates the requested no-stale-PID boundary. No actual PID reuse or unintended signal was observed or performed in this review. |
| Effort | Small, localized parent-only cleanup/ownership change |
| Risk | Conditional cross-process signaling risk if left unchanged; a repair must not invent an exit status or silently claim successful cleanup after losing ownership. |
| Confidence | High for the demonstrated control flow and the documented meaning of `ChildProcessError`; likelihood under the previously observed native host is not established. |
| Fix sketch / implementation route | Track loss of waitable-child ownership separately from successful reaping. On `ECHILD`, preserve the unknown status/error, revoke signaling eligibility, and remain incomplete. Before cleanup signaling, account for a child that has already become terminal, and explicitly establish or check the parent signal/reaping policy so the unreaped-child argument is valid. Never turn `ECHILD` into an invented successful reap. Keep the original child bytes and outer timeout unchanged. |
| Repair class | instrument/acceptance defect |
| Owner/source | Root; embedded macOS terminal parent in `tests/install-preview.py` |
| Acceptance criteria | A direct wait returning `ECHILD` must produce no subsequent signal to that numeric PID, no claimed successful reap, and a non-passing result. Preserve a positive exact-child zero-exit control. Preserve bounded cleanup for a demonstrably owned live child and an incomplete result when actual reaping cannot be observed. Include an ownership-loss case during failure cleanup, not only the normal wait path. |
| Verification | `independent-evidence/inert_parent_review.py` executes the exact frozen parent flow with imports replaced by inert OS/PTY/select/clock objects. The mocked fork always returns a positive parent-side PID; the child block is never entered. `inert-parent-results.json` records the attempted kill after ECHILD. No real process, signal, descriptor, or PTY is used. |
| Rollback / Plan Closure | Keep the frozen candidate and this negative evidence. Revise the parent only, freeze new hashes, and re-review the ownership error path before using the correction as the accepted harness. This report does not authorize repository edits or native execution. |
| Rejected/deferred rationale when applicable | Not dismissed merely because prior native successful runs needed no cleanup: those runs do not exercise ownership-loss error handling. |
| Remaining risk | The correct zero-exit path is unaffected by this finding. Any child ownership or signal-policy precondition must be stated and checked; no global process census is requested or established. |
| Route | DMAIC |

Python's primary [os.waitpid documentation](https://docs.python.org/3.15/library/os.html#os.waitpid) distinguishes `(0, 0)` for a matching child with no immediately available status from `ChildProcessError` when no matching child can be waited for. The finding is based on that distinction, not on a claim that every wait error implies PID reuse.

## MHR-002 — A late terminal result can bypass the declared work deadline

| Finding Row Contract field | Finding |
| --- | --- |
| Finding title | A zero exit observed after the 25-second work cutoff can still pass |
| Category | Acquisition deadline / acceptance false positive; medium severity |
| Evidence | `terminal-probe.py:22` sets `deadline=started+25`. The success branch at line 38 breaks immediately after a successful wait, before the deadline check at line 39. The final `allowed` expression at line 59 does not check when work completed. The inert `late_zero_status` case supplies the original sentinel, then a correct zero wait status observed at mock time 26. The exact program returns exit 0 and `controllingTerminalAllowed=true`, recording `elapsedSeconds=26.0`. Corresponding harness lines are 531, 547, 548, and 568. |
| Impact | The declared 25-second work budget can be consumed into the time reserved for failure cleanup while still producing a success receipt. The unchanged outer 30-second subprocess timeout remains a separate cap; this finding does not allege its removal or an unbounded run. |
| Effort | Small parent-only deadline/observation gate |
| Risk | Low fix risk; stricter deadline accounting may correctly turn a late-observed completion into an incomplete bootstrap result. |
| Confidence | High for the deterministic control-flow witness; no native timing breach is claimed. |
| Fix sketch / implementation route | Record or check the monotonic time after the sentinel and actual terminal status are observed, before permitting success. A status observed beyond the work cutoff must retain the observed status but fail the work-deadline gate. Keep cleanup bounded separately and retain the outer 30-second limit. Check the post-select/read path as well as the wait-success branch. |
| Repair class | instrument/acceptance defect |
| Owner/source | Root; embedded macOS terminal parent in `tests/install-preview.py` |
| Acceptance criteria | A just-before-deadline exact sentinel/zero-status observation may pass. The same observations first obtained at mock time 26 must remain reaped/status-known but return a non-passing result without signaling an already reaped child. A late sentinel must also fail. Timeout plus cleanup-produced zero status must continue to fail. |
| Verification | The exact frozen parent's `late_zero_status` oracle records exit 0, allowed true, elapsed 26 against deadline 25. A separate `cleanup_zero` oracle records actual simulated zero status after the timeout/cleanup path and correctly stays false, showing the finding is specifically the unchecked late-success branch. |
| Rollback / Plan Closure | Preserve this witness, correct the parent acceptance predicate, freeze new hashes, and re-review the boundary. No broader timeout increase, sandbox change, or child change is necessary. |
| Rejected/deferred rationale when applicable | Not dismissed as a violation of the outer 30-second limit: that limit remains intact. The narrower issue is disagreement with the explicitly requested 25-second work plus reserved cleanup contract. If the owner intends a different work-budget contract, that must be stated rather than inferred from the existing late-pass behavior. |
| Remaining risk | Scheduling and observation times are not the child's exact kernel exit time. An observation received after the deadline cannot by itself prove completion was observed within the declared budget. |
| Route | DMAIC |

## Other inspected boundaries and controls

| Control / observation | Outcome and scope |
| --- | --- |
| Exact normal sentinel, LF and CRLF representations | Two positive controls pass after exact-child zero status and master closure, without cleanup signals. CRLF normalization matches the retained native terminal representation. |
| Nonzero child status | Actual simulated exit 77 remains false; the already reaped child is not signaled. |
| Oversize output / EOF before sentinel | Both remain false. The original sentinel is not accepted from partial or extra captured bytes. |
| Sentinel timeout / reap timeout | Both remain false and enter bounded cleanup. |
| Cleanup supplies zero status | Still false because the prior timeout and cleanup signal remain recorded. |
| Cleanup never observes reaping | Remains false, with no invented exit code; the mock cleanup loop terminates before the outer 30-second ceiling. |
| Nonblocking setup / master close / fork failure | Fail closed. Master-close failure after reaping causes no new signal. A simulated fork failure produces no success JSON. |
| Native mechanism evidence | Historical original-child drain evidence is retained and consistent; this new harness's native behavior has not been executed by the reviewer. |
| Other product changes | Not reviewed semantically. The candidate2-to-current diff outside the one embedded probe is empty. |

Fourteen inert scenarios were exercised: two normal controls, ten ordinary fail-closed/error controls, and the two findings above. An initial oracle assertion expected the base `OSError` name for `OSError(11)`; Python specializes it as `BlockingIOError`. Only that oracle assertion was corrected, with the failed first attempt recorded in `oracle-first-attempt.json`. Candidate bytes and scenario behavior were unchanged.

## Evidence and review limits

All evidence below is under `/tmp/r0016-successor-20261111/recovery/macos-harness-candidate-1/independent-evidence/`:

- `source-binding.json` and `source.diff` — exact source hashes, literal binding, original child preservation, and narrow change boundary.
- `inert_parent_review.py` and `inert-parent-results.json` — exact-parent mocked control flow, observations, and failure-path receipts.
- `native-bridge-binding.json` — selected historical native capture hashes and scope; no native rerun.
- `oracle-first-attempt.json` — retained review-oracle assertion correction.

The full harness was not imported or evaluated. The only candidate code evaluated was the parent snippet with every OS, PTY, signal, wait, select, descriptor, and clock operation replaced by inert objects. No native Apple behavior, sandbox enforcement, product assertion, or live cleanup was exercised. The two successful historical native cases do not close the new error-path findings. Findings and suggested repairs are evidence for the root/owner, not mutation or closure authority.

GAP-REVISE
