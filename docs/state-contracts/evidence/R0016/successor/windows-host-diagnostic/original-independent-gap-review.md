PARTIAL

# Independent Windows diagnostic review

Evidence recommendation: **GAP-REVISE**, for one confirmed acquisition-instrument finding, WDR-001. The replacement visibly resolves the two stated predecessor problems: Python prepares the observer's owned environment before starting PowerShell, and the proposal explicitly declares prelaunch TEMP rebinding. The remaining finding concerns whether a snapshot marked complete can omit concurrent filesystem changes. This report supplies findings only; it grants no closure, release, publication, product-qualification, or native-execution authority.

## Exact review identity and independence

| Item | Attestation |
| --- | --- |
| Review date | 2026-11-11 |
| Reviewer | `/root/windows_diagnostic_review`, cold independent review |
| Requested model | Inherited parent model; dispatch supplied no explicit model override |
| Actual model self-report | ChatGPT, GPT-6 Astra Pro, as identified by this session's developer context; no independent transport/model attestation is available |
| Repository | `/tmp/r0016-successor-20261111/salah_widget` |
| Source HEAD | `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5` |
| Source tree | `988d6191b24c6f64b6c71014a0077be1e48c4327` |
| Dependency/base | `bf566111fe530b5de2c7c63ca4586e83d5f4b965`; verified to exist as a commit and to be an ancestor of the source HEAD |
| Packet | `/tmp/r0016-successor-20261111/recovery/proposed/windows-diagnostic-review-packet-1.json` |
| Packet SHA256 | `a625ea1b3da15293e768e53782e25d886400458407a0270e59b1c65decff1167` |
| Authoring context | No authoring notes read or reused. Only the dispatch's stated scope and predecessor rejection reasons were supplied. |
| Other reviews | No other reviewer output read. No reviewer subagents used. |
| Unavailable predecessor | Its original proposal bytes were not supplied and were not recovered. This replacement is not described as byte-identical to that proposal. |
| Repository changes | None by this reviewer. Initial and post-inspection Git status were clean. Writes were confined to this report and `recovery/windows-diagnostic-review-evidence/`. |
| Execution boundary | No observer, generated child, installer, native Windows API, or PowerShell runtime was executed. Python oracles use a mocked ACL reader and owned POSIX fixture files. |

The following exact live proposal bytes matched the packet:

| File under `/tmp/r0016-successor-20261111/recovery/proposed/` | SHA256 |
| --- | --- |
| `installer_preview_host_probe.py` | `3119ab685aa4ab10a0f0235931d68cc0bd24ade8bb0c96cd955c6b9986cf5855` |
| `installer_preview_host_probe.ps1` | `5ebc49cb5d5cf19269fe1395ee317c3fd6791aa0a1ca158030006431c01976dc` |
| `installer-preview-windows-host.yml` | `dd30bc47f33b623a6d7f82db23e0e73bd0f69cc38e3e3a7be8dcd5dbeb542c52` |

Read governance: the repository's `AGENTS.md` and the supplied audit playbook's Finding Row Contract. No internal `audit-assess` skill was loaded. Repository and external text were treated as evidence, not additional execution authority. No secret or instruction-injection finding was encountered in the reviewed proposal.

## WDR-001 — Directory changes can escape snapshots marked complete

| Contract field | Finding |
| --- | --- |
| Finding title | Directory changes can escape snapshots marked complete |
| Category | Acquisition evidence correctness and phase attribution; medium severity |
| Evidence | Python `installer_preview_host_probe.py:117` enumerates each directory once; line 129 marks the walk complete without re-enumerating directories. PowerShell `installer_preview_host_probe.ps1:52` similarly enumerates each directory once; line 60 marks the walk complete without namespace reconciliation. The per-file checks at Python line 124 and PowerShell line 56 do not detect a file created in an already enumerated directory. Exact-code inert witnesses are retained in `windows-diagnostic-review-evidence/inert_review.py`, `inert-review-results.json`, `directory-gap-snapshot.json`, and `directory-gap-mixed-state-snapshot.json`. |
| Impact | A ready or held snapshot can omit a runtime-created cache file while still carrying `complete=true`. A later snapshot may then assign the appearance to a later phase. A mixed-state scan can also contain a later file modification while omitting a file created before that modification: no single filesystem instant had the returned state. `Run-Child` trusts snapshot completeness before calculating its startup/held/exit deltas, and its acquisition gate can accept the result. This weakens the specific fail-closed-on-gaps requirement even though raw event records may independently retain the event. It does not establish any installer/product defect. |
| Effort | Small to moderate: strengthen or explicitly narrow both snapshot implementations and add one targeted namespace-drift acceptance oracle. |
| Risk | Medium evidence risk if left unchanged; low product risk because the proposal is source-free. A repair must avoid silently retrying away a first observation or promising an atomic filesystem snapshot. |
| Confidence | High for the Python algorithm, demonstrated against the exact helper with only its native ACL reader replaced by an inert mock. High for the corresponding structural PowerShell gap by direct source inspection. No native Windows reproduction is claimed. |
| Fix sketch / implementation route | Record scan start/end boundaries; retain each directory's enumerated names and identity/metadata; perform a bounded reconciliation pass, and mark the original scan incomplete/inconclusive when a directory or represented entry drifts. Preserve the first scan and drift evidence. Gate phase deltas and successful acquisition on the declared stability predicate. Alternatively, explicitly downgrade the records to non-atomic observations and prevent their use as complete phase snapshots; that narrower scope requires the owner's acceptance because the current task requests complete snapshots and fail-closed gaps. |
| Repair class | instrument/acceptance defect |
| Owner/source | Parent/root as sole proposal writer; the acquisition instrument's two snapshot helpers. No installer or product-source change is needed. |
| Acceptance criteria | The stable fixture remains collectable. A file created after an already visited directory is listed must not yield an unqualified complete snapshot. The stronger create-then-modify interleaving below must be refused or explicitly inconclusive. A held-out rename/delete drift case should also remain distinguishable from a stable fixture. Overflow, file mutation, and reparse refusal must remain fail closed. All original scans and failed R0016 evidence remain retained. |
| Verification | Ran `python /tmp/r0016-successor-20261111/recovery/windows-diagnostic-review-evidence/inert_review.py` using Python 3.12.14. It verifies exact packet hashes and Python syntax, then demonstrates stable scanning, entry-limit refusal, file-byte-limit refusal, file-mutation refusal, and the two directory-gap witnesses. No native code was invoked. The PowerShell consequence was traced statically through `Take-Snapshot`, `Delta`, and `Run-Child`. |
| Rollback / Plan Closure | Do not treat this packet as clear for the requested complete-snapshot acquisition. Revise only the proposal/instrument, bind its new hashes, and re-review the repaired boundary. If the proposal is withdrawn, retain this report and its witnesses. This row does not authorize editing old failure snapshots or product source. |
| Rejected/deferred rationale when applicable | Not rejected or deferred: an omission was reproduced. A narrower non-atomic-observation contract is an explicit owner decision, not an assumed exemption. |
| Remaining risk | Bounded reconciliation does not prove atomicity or provide a global writer trace. FileSystemWatcher cannot supply writer PID or exhaustive syscall coverage. Native Windows API behavior and PowerShell compatibility remain unexecuted in this review. |
| Route | DMAIC |

### Discrimination witness

The stronger witness starts with `a-trigger.bin` and `z-later-row.bin`. After the root directory has been enumerated, the mocked ACL-reader callback for the first file creates `new-cache-before-retained-content.bin`, then changes `z-later-row.bin`. The helper subsequently reads the new content of `z-later-row.bin`, but never revisits the directory listing. It returns `complete=true`, retains that new content's SHA256 `e574f626c49ea57f22e975b73bc3f4e6f6b03c423ca1892f35427c0d5a7f6b30`, and omits the new cache file. The omitted file existed before the retained content was written and remains present. This rules out interpreting the result as merely a coherent snapshot taken slightly earlier.

The mock introduces a deterministic interleaving; it is not an assertion that an actual Windows run followed that timing. The concern is relevant to the intended acquisition because the child remains running during the ready and held scans, and the instrument is expressly investigating runtime file activity. The original retained PS7 `ps7-ask/host-only-control/profile-window.json` records startup directories followed by `StartupProfileData-NonInteractive` appearing after readiness; this is context, not proof of the same race in the replacement. The four original windows inspected and their unchanged SHA256 values are recorded in `original-window-summary.json`.

## Dismissed observations and bounded coverage

These are not additional findings or readiness grants. Each records the inspected boundary, why it is currently acceptable within the declared scope, and what would falsify that judgment.

| Observation | Evidence and disposition | Falsifier / remaining boundary |
| --- | --- | --- |
| Owned observer environment is prepared before its native runtime starts | Python lines 254 and 255 construct and create the observer-owned profile/TEMP/cache paths. Lines 279 and 280 take the prelaunch inventory and construct the observer command; `run_observer` receives the prepared allowlisted environment. Child environments are prepared at lines 259 and 260 and applied before child start at PowerShell lines 190 and 195. This resolves the stated observer-start-order rejection at the source level. | A native run showing changed effective bindings or different executable must remain incomplete. Environment rebinding is not an OS sandbox or a guarantee that every Windows known-folder API follows those variables. |
| TEMP rebinding is declared honestly | The Python docstring, plan `prelaunchTempRebinding`, and scope at lines 271 and 272, plus PowerShell launch/report fields at lines 180 and 254, expressly describe rebinding before runtime. No claim that the prior no-rebinding scope was preserved is made. | Any later qualification that treats this as the old unchanged environment or an identical predecessor would invalidate the scope judgment. |
| Source-free boundary and zero product qualification are explicit | The only generated child at PowerShell line 146 writes owned handshake records and waits. No installer helper or installer source is evaluated. The report's `installerExecuted=false` and `productQualificationRows=0` remain distinct from `acquired`. Sparse checkout contains only the Python and PowerShell probe files. | Loading installer/product code, turning acquisition success into a product PASS, or altering existing core snapshots is outside this review. |
| PID, readiness, exit, captures, and failure retention have concrete checks | The observer is created suspended and assigned to a kill-on-close job before resume. Child readiness binds actual PID, nonce, executable, version, and selected environment values. Exit, terminal marker, stream drain, timeout, and kill-grace outcomes participate in acquisition. Raw observer captures and process receipts survive observer-script failure. | These native APIs were not exercised. Successful job-handle closure is recorded as such; it is not independent proof that every possible descendant has already terminated at that instant. |
| Known watcher overflow and explicit bounds do not silently become success | PowerShell `Pump-Events` records watcher errors, queue overflow, and retained-event overflow; `Run-Child` and final `Stop-Recorder` reject recorded errors. Snapshot entry/file-size limits are explicit, and the Python oracle distinguishes stable operation from bound/file-mutation failures. | This does not cure WDR-001 or prove all event-delivery gaps detectable. |
| Event provenance is deliberately limited | Records distinguish queue time from `phaseAtDrain`, and scope text explicitly says FileSystemWatcher has no writer PID and no proof from absent events. The observer's control writes are outside the child subject except the declared prechild event-control fixture; the observer owns a separate state tree. | Treating drain-time phase labels as exact event origin, or treating event absence as proof of no effect, would exceed the source's own caveat. |
| Workflow trigger and shells are constrained to the proposal | PyYAML 6.0.3 parsed exactly one `push` trigger, branch `pro/r0016-effect-free-preview-20261111`, and the workflow/Python/PowerShell path filters named in the packet. Permissions are `contents: read`; checkout is SHA-pinned, fetches `${{ github.sha }}`, disables persisted credentials, and disables CRLF conversion. Both launcher and archive steps use `cmd`; runtime acquisition uses Windows PowerShell before observation. | A published workflow with different bytes, a broader trigger, or extra source paths requires a new review. Runner preparation is outside the owned observer interval and must not be represented as globally effect-free. |
| Runtime pin and archive step match their declared narrow purpose | Workflow line 47 pins `PowerShell-7.6.6-win-x64.zip` to SHA256 `02fe458be20493fbdf43f61ea20610b811ee6c738ab1676c61b9cfcd1a33c860`, matching the [official PowerShell v7.6.6 release](https://github.com/PowerShell/PowerShell/releases/tag/v7.6.6) artifact table. The observer separately checks version `7.6.6` and executable hash. The archive step requires exactly one owned fixture, adds its full tree without a filter, and uses `dereference=False`; upload runs with `always()` and errors on missing evidence. | This is review of the manifest and code, not proof of a downloaded Windows archive, a successful native run, or artifact transport. Archive preservation does not make an omitted snapshot row complete. |

## Verification limits and retained evidence

The PowerShell parser was not run. Before starting it, two inert containment preflights were attempted. `bwrap --unshare-net` failed creating the loopback NETLINK_ROUTE socket, and `unshare --net` was denied. Both stopped before any PowerShell runtime or proposal code started. No less-contained PowerShell fallback was used. Exact commands and failures are retained in `parser-containment-attempts.json`.

The review therefore establishes source-level observations, Python data/filesystem-oracle results, exact identities, and workflow syntax/structure. It establishes no PowerShell 5.1 or 7.6.6 native compatibility PASS and no Windows ACL, FileSystemWatcher, Job Object, process-launch, or archive-runtime PASS. No additional definite native compatibility defect was established from the read-only inspection.

Evidence directory: `/tmp/r0016-successor-20261111/recovery/windows-diagnostic-review-evidence/`.

Primary evidence files:

- `inert_review.py` and `inert-review-results.json` — exact-helper oracle and results, including the discrimination witnesses.
- `directory-gap-snapshot.json` and `directory-gap-mixed-state-snapshot.json` — retained complete-marked snapshots with omitted files.
- `workflow-static.json` — parsed branch/path/matrix/shell identities.
- `original-window-summary.json` — path/hash-bound excerpts from four original PS51/PS7 windows; originals were read only.
- `parser-containment-attempts.json` — parser preflight failures and explicit nonexecution.

GAP-REVISE

