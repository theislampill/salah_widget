FINAL

# Focused independent rereview — macOS parent candidate3

**PASS for the narrow MHR-001 and MHR-002 corrections at the frozen candidate3 identities below.** The original ownership-loss witness no longer signals the PID, and failed or unexpected ownership reads prevent later signaling. A terminal result first observed after the declared work deadline is now rejected while retaining the actual observed status. The original child source, sandbox, outer 30-second ceiling, and unrelated harness bytes remain unchanged.

This is source/control-flow and inert-oracle evidence only. It grants no native macOS qualification, product acceptance, publication, merge, issue closure, or audit closure authority. The root remains the sole source writer. No new material finding was established within this focused rereview.

## Exact identities and independence

| Item | Identity / attestation |
| --- | --- |
| Reviewer | `/root/windows_diagnostic_review`, same independent reviewer who issued the candidate1 findings |
| Requested canonical model | `gpt-6-astra`, continuing inherited reviewer; no override or respawn |
| Actual canonical model self-report | `gpt-6-astra`, identified in this session as GPT-6 Astra Pro; no independent provider-routing attestation |
| Frozen directory | `/tmp/r0016-successor-20261111/recovery/macos-harness-candidate-3/` |
| Candidate3 freeze SHA256 | `256118c296adb56fc0c50d782e6c1f8962c5c11032130d99944ca8aa29f87c7e` |
| Candidate3 harness SHA256 | `8babcffa108f777fa3add01f39a4e26b537f5e1521ed8d4b490c171153b3817e` |
| Candidate3 terminal probe SHA256 | `bdc6a583477ee3db70c13f795224cf3154cda859cdf925689ac756f45126796a` |
| Candidate1 harness SHA256 | `f9eb146d50e13b3b0361586bf38c266db300e049e37dd9a83fdd2f7b412c271b` |
| Candidate1 terminal probe SHA256 | `ce2cf350f4738875dd34d98efcc5ce6ff8428948d55581af9a897903f2909a2f` |
| Product-harness preservation baseline | `product-fix-candidate-2/tests/install-preview.py`, SHA256 `653f4328ce02544f64fa6e9c02989c4afa53abc01ef7556451961cf9cff832cf`; the prior review established that only the embedded parent changed from that baseline |
| Repository HEAD / tree observed | `9c51a09e0e21722fdf9c7eafb2c7d9c1bf4ec196` / `7255c19060376234641d962cdf0fc20b7c0be72c` |
| Historical native bridge source | `503a4d57852b195dce4c36c5b8ab9299c9036e95`, tree `f16971c25d7af8fb7468d232a27688a78874747c`, run `43088148764` |
| Original source / dependency provenance | Original source `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5`, tree `988d6191b24c6f64b6c71014a0077be1e48c4327`; dependency base `bf566111fe530b5de2c7c63ca4586e83d5f4b965` |
| Candidate1 review preserved | SHA256 `208f2648ff7313c700304966aadf57c9c4934f5ad91bf5a1e2b361ee983523c5`; its FINAL GAP-REVISE report, all seven manifest entries, and all fourteen original scenario records remain unchanged |
| Intermediate macOS candidate2 | Not read or evaluated in this review. No review, native execution, or publication claim is supplied for that intermediate repair. This is distinct from the product-harness baseline named above. |
| Independence | Reused this reviewer's candidate1 source analysis and inert witnesses. No authoring notes or other product reviewer conclusions were read. No broad product or native review was repeated. |
| Writes | This separate report and candidate3 `independent-evidence/` only. No frozen source, candidate1 evidence, repository file, staging entry, or Git reference was changed. |

## Correction dispositions

| Finding Row Contract field | MHR-001 disposition | MHR-002 disposition |
| --- | --- | --- |
| Finding title | Cleanup signaling after child ownership loss — corrected at the reviewed boundary | Late terminal result bypassing the work deadline — corrected at the reviewed boundary |
| Category | Cleanup ownership / process-safety boundary | Deadline / acquisition acceptance |
| Evidence | Candidate3 probe line 4 establishes default SIGCHLD disposition before fork. Lines 39–45 latch failed/unknown primary waits as ownership loss. Lines 54–65 allow a cleanup signal only after a fresh exact-child wait returns no available status; lost ownership prevents entry. Lines 70–71 stop and record later wait errors. The original ECHILD witness and new primary/cleanup loss controls send no subsequent signal. | Candidate3 probe lines 41–44 store the actual reaped status, then check the monotonic observation against the 25-second deadline before accepting success. Original late-zero and new late-sentinel witnesses at mock time 26 retain `childReaped=true`, `childExit=0`, and return false without signaling the reaped child. |
| Impact | The original unowned numeric-PID kill path is removed. An error or unexpected identity is not converted into successful reaping or restored signaling authority. | The original unchecked late-success path is removed. A status first observed beyond the work budget no longer establishes successful acquisition. |
| Effort | Narrow implemented parent-only change | Narrow implemented parent-only change |
| Risk | Native signal disposition and wait behavior remain to be exercised in their intended host. Unknown ownership remains incomplete rather than forcing cleanup. | Late observation can correctly produce an incomplete bootstrap even when the child eventually exits zero. The outer 30-second limit is unchanged. |
| Confidence | High for exact source and inert control-flow evidence; no native execution credit | High for exact source and deterministic clock witnesses; no native timing credit |
| Fix sketch / implementation route | Implemented pre-fork SIGCHLD setup, permanent pre-signal ownership-loss latch, immediate nonblocking ownership recheck before the sole cleanup signal, and `childOwnershipLost` reporting. | Implemented post-reap observation-time gate while retaining actual status and keeping cleanup separate from successful work. |
| Repair class | instrument/acceptance defect | instrument/acceptance defect |
| Owner/source | Root; embedded macOS terminal parent | Root; embedded macOS terminal parent |
| Acceptance criteria | Original ECHILD produces no signal and no invented reap/status. Generic failed/unknown primary waits do not regain authority on a hypothetical later successful read. Cleanup ownership loss does not signal. An interruption after simulated status consumption is handled through the cleanup ownership check. Demonstrably owned cleanup remains bounded and cannot pass. Met by the focused controls. | Exact sentinel/zero status observed just before the cutoff may pass; first observation at time 26 must fail with actual status retained and no signal to a reaped child. Late sentinel delivery also fails. Timeout followed by cleanup-produced zero remains false. Met by the focused controls. |
| Verification | Candidate3 exact parent evaluated through the retained reviewer-owned mock scenario classes plus focused extensions; all OS/PTY/signal/wait/descriptor/select/time operations replaced by inert objects. Every simulated kill is preceded immediately in the call trace by `waitpid` result `(0, 0)` for the exact child, with the default signal policy established before fork. | The same exact-parent oracle verifies late-zero, late-sentinel, just-before-deadline, and cleanup-zero cases. The late cases report the observed zero status but return exit 2 with the deadline error. |
| Rollback / Plan Closure | Preserve candidate1's negative evidence and this separate rereview. This supports the correction only at the frozen hashes; root/owner retains source and lifecycle decisions. | Preserve the original late-pass witness and candidate3 rejection record. No timeout expansion, child change, or sandbox relaxation is required or reviewed. |
| Rejected/deferred rationale when applicable | Original finding remains valid for candidate1; it is not relabeled a false positive. Candidate3 corrects its accepted boundary. | Original finding remains valid for candidate1; candidate3 now rejects that exact late observation. |
| Remaining risk | No global process proof, native cleanup proof, or guarantee of recovering an unknown child is supplied. `childOwnershipLost` must not be interpreted as successful cleanup. | Observation time is not the child's exact kernel exit time. This review validates the declared observation gate, not an exact native timing diagnosis. |
| Route | DMAIC | DMAIC |

## Focused evidence and no-regression checks

The harness prefix and suffix outside `terminal_probe` remain byte-identical between candidate1 and candidate3. The probe literal exactly equals the frozen `terminal-probe.py`. The child block remains byte-identical at SHA256 `3774840e5c68c186a2f70ba77083fa6159b73feaaba1e6f21e15fecb8c26f2cb`. The explicit pre-fork SIGCHLD policy is part of the reviewed parent correction. `darwin_profile`, the original `sandbox_run(timeout=30)`, and the terminal invocation/outer acceptance gates did not change.

The focused oracle reused all fourteen original scenario definitions without importing or running the old driver's top-level body. Ten additional cases cover permanent generic ownership-read failure, permanent unknown identity, cleanup ECHILD, cleanup unknown identity, ECHILD after the single owned cleanup signal, owned cleanup yielding zero, just-before-deadline success, late sentinel delivery, SIGCHLD setup failure before fork, and an interruption after simulated kernel reaping.

All **24** scenarios produced their expected results: three positive controls and twenty-one refusals or errors. The original ordinary nonzero-status, extra-output, EOF, timeout, never-reaped cleanup, descriptor setup/close, and fork-failure cases remain fail closed. A failed SIGCHLD setup prevents the mocked fork. The never-reaped mock cleanup remains below the outer ceiling. The only simulated signal sites occur after an immediate exact-child ownership check and do not yield acceptance, including when cleanup later supplies zero status.

The candidate1 report and all seven entries in its evidence manifest were rehashed and remain unchanged. Its original fourteen records remain preserved; the new results are written only under candidate3. The intermediate macOS candidate2 was not used to substitute for either the original failing evidence or this reviewed correction.

## Artifacts and limits

Evidence is under `/tmp/r0016-successor-20261111/recovery/macos-harness-candidate-3/independent-evidence/`:

- `source-and-preservation.json` — exact candidate identities, unchanged child/sandbox/timeout, and candidate1 preservation checks.
- `candidate1-candidate3-parent.diff` — independent diff of the reviewed parent boundary.
- `inert_parent_rereview.py` — reuse of the retained scenario classes and the focused extensions.
- `inert-rereview-results.json` — all twenty-four outcome/call-trace records.

No real process or PTY was created, no real signal or wait operation was issued, and no native subject, sandbox, workflow, installer, or full harness was launched. The exact parent was evaluated only with inert imported operations and a positive mock PID that makes the unchanged child branch unreachable. The historical native drain evidence was not re-executed or promoted into product acceptance. All native and product-qualification limits from candidate1's review remain in force.

PASS
