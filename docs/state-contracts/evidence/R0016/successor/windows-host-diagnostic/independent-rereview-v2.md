FINAL

# Windows diagnostic independent rereview — v2

**PASS for the narrow WDR-001 correction and its declared bounded stability contract.** The original gap witnesses still distinguish the preserved pre-repair bytes from v2. V2 retains both completed inventories, marks namespace drift incomplete, and gates the Python observer pre/post records on that result. A separate rename/delete case also refuses acquisition after saving the discrepant inventories. No new material finding was established in this focused correction review.

This is findings evidence, not release, publication, audit-closure, native-execution, or product-qualification authority. No PowerShell or native Windows subject ran. The first review's native-compatibility limitations remain in force.

## Reviewer and exact identities

| Item | Attestation |
| --- | --- |
| Reviewer | `/root/windows_diagnostic_review`, same independent reviewer as the original cold review |
| Review date | 2026-11-11 |
| Requested canonical model | `gpt-6-astra`, as requested for this rereview; no agent respawn or model override was performed |
| Actual canonical model self-report | `gpt-6-astra` — this session identifies itself as GPT-6 Astra Pro. This is a model self-report, not independent provider-routing attestation. |
| Independence | Reused only this reviewer's prior cold review, its witnesses, and the hash-matched preserved v1 source. No authoring-notes file or another reviewer's report was read. The freeze manifest's author test claims were not used as verification. |
| Repository | `/tmp/r0016-successor-20261111/salah_widget` |
| Original reviewed source HEAD | `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5` |
| Original reviewed source tree | `988d6191b24c6f64b6c71014a0077be1e48c4327` |
| Current observed source HEAD | `503a4d57852b195dce4c36c5b8ab9299c9036e95` |
| Current observed source tree | `f16971c25d7af8fb7468d232a27688a78874747c` |
| Dependency/base | `bf566111fe530b5de2c7c63ca4586e83d5f4b965`, verified as an ancestor of current HEAD |
| Original installer/test commit boundary | Git comparison of `install.ps1`, `install.sh`, `tests`, and `AGENTS.md` between `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5` and `503a4d57852b195dce4c36c5b8ab9299c9036e95` returned unchanged. This is a commit-to-commit statement, not a claim about uncommitted edits. |
| Live worktree at final identity capture | Modified: `install.ps1`, `install.sh`, `tests/install-entry-native-coverage.py`, `tests/install-preview.ps1`, and `tests/install-preview.py`. Those ongoing root-owned edits were neither inspected nor changed by this reviewer and are excluded from this rereview's PASS. The worktree was clean at this rereview's initial check. |
| V2 freeze manifest | `/tmp/r0016-successor-20261111/recovery/proposed/installer_preview_host_probe-v2-freeze.json`, SHA256 `d1fdfb1a370b43629497d5c21e9536f9b261a3fae2f714bd20ecd42ee86f1188` |
| Original packet | SHA256 `a625ea1b3da15293e768e53782e25d886400458407a0270e59b1c65decff1167`; it binds v1, not this v2 correction |
| Original review preserved | `/tmp/r0016-successor-20261111/recovery/proposed/windows-diagnostic-independent-review.md`, unchanged SHA256 `d6fe1ab40d72dea474ce89d82a5ac193824fadc95cc39109298de3e6c9beafe2` |
| Allowed writes used | This new report and `recovery/windows-diagnostic-review-evidence/v2/` only |

Live v2 proposal bytes:

| File under `/tmp/r0016-successor-20261111/recovery/proposed/` | SHA256 |
| --- | --- |
| `installer_preview_host_probe.py` | `6776bc7b3d4e88d04f1dd811f5b7df0ea1553a7b8824f1f3e921c649c1aae9df` |
| `installer_preview_host_probe.ps1` | `1f62bb1994f3390fd63461daff4aaed4a264b2f194f85fedd55c920c8c8f93d4` |
| `installer-preview-windows-host.yml` | `dd30bc47f33b623a6d7f82db23e0e73bd0f69cc38e3e3a7be8dcd5dbeb542c52` |

The preserved v1 Python and PowerShell sources under `proposed/host-probe-v1/` independently matched their original reviewed SHA256 values, respectively `3119ab685aa4ab10a0f0235931d68cc0bd24ade8bb0c96cd955c6b9986cf5855` and `5ebc49cb5d5cf19269fe1395ee317c3fd6791aa0a1ca158030006431c01976dc`. These are the prior review's actual v1 proposal, not the unavailable earlier rejected proposal. No identity claim is made about the unavailable proposal.

## WDR-001 correction disposition

| Contract field | Rereview finding disposition |
| --- | --- |
| Finding title | Directory changes escaping complete snapshots — corrected for the declared two-pass stability observation |
| Category | Acquisition-instrument evidence correctness; original medium-severity finding |
| Evidence | Python `snapshot` at line 135 runs two complete bounded inventories, compares their rows, retains both, and explicitly disclaims atomicity. `save_required_snapshot` at line 146 saves a discrepant aggregate before raising; main calls it before and after the observer at lines 300 and 303. PowerShell `Take-Snapshot` at line 66 requires both passes complete and their serialized rows equal, then retains both passes. The independent v1/v2 discrimination results are in `windows-diagnostic-review-evidence/v2/rereview-results.json`. |
| Impact | The specific persistent namespace-drift witnesses from WDR-001 no longer carry unqualified `complete=true`. Existing PowerShell acquisition gates receive false completeness; the added Python gates prevent observer pre/post drift from reaching successful acquisition. |
| Effort | Narrow implemented instrument change; no product change needed |
| Risk | Residual measurement risk is bounded and disclosed: agreement of two scans does not establish an atomic filesystem instant or exhaustive absence of effects. |
| Confidence | High for exact Python-helper behavior and byte/AST regression boundaries. PowerShell correction is source-reviewed only; no PowerShell parser or native execution claim. |
| Fix sketch / implementation route | Implemented as two fixed complete inventories with exact row comparison, retained pass data and start/end times, no retry loop, no exclusions, and explicit non-atomic scope. |
| Repair class | instrument/acceptance defect |
| Owner/source | Parent/root as sole proposal writer; Python/PowerShell acquisition helpers |
| Acceptance criteria | Stable control stays complete. Both original gap witnesses fail completeness on v2 while remaining failures on original v1. A held-out rename/delete namespace mutation refuses the required-snapshot gate after retaining both scans. Unrelated source, child, budgets, workflow, and process handling stay unchanged. These bounded criteria were met. |
| Verification | Executed `python /tmp/r0016-successor-20261111/recovery/windows-diagnostic-review-evidence/v2/inert_rereview.py` with Python 3.12.14. No main entrypoint, Windows ACL API, observer, generated child, installer, or PowerShell process was invoked. All fixture I/O was inside the review's new v2 evidence directory. |
| Rollback / Plan Closure | Retain the original GAP-REVISE report and its evidence unchanged. This report supports the correction's acceptance at the reviewed byte identities only; the parent/owner retains all publication and lifecycle decisions. A later byte change requires appropriate re-review. |
| Rejected/deferred rationale when applicable | The original finding is not rejected as a false positive: preserved v1 still reproduces it. The correction meets the explicitly bounded acceptance contract; native qualification remains outside this review. |
| Remaining risk | Transient or repeated changes can evade two observations; a two-pass match must never be described as atomicity, writer-PID attribution, or proof of no global effect. Enumeration exceptions remain fail closed and do not produce a successful aggregate. No broader partial-pass recovery guarantee is established. |
| Route | DMAIC |

## Focused independent verification

| Check | Result |
| --- | --- |
| Stable positive control | Complete; exactly two completed inventories retained with equal rows |
| Original simple directory-addition witness | Preserved v1 returns complete; v2 returns incomplete, with the first omission and second observed file both retained |
| Original mixed-state witness | Preserved v1 returns complete for the impossible combined state; v2 returns incomplete and retains both inventories |
| Held-out rename/delete drift | Two different completed inventories retained; `save_required_snapshot` saves the record then refuses it |
| Python change boundary | Prefix containing environment/native ACL helpers unchanged; native process function unchanged; single-pass loop AST unchanged; main differs only in the two required-snapshot calls |
| PowerShell change boundary | Prefix before the inventory helper unchanged; `Delta` and all following bytes unchanged, including child source, watcher, acquisition, and cleanup behavior |
| Workflow | Exact original reviewed SHA256 unchanged; no broad workflow review repeated |
| Prior report/evidence preservation | All eight entries in the prior review manifest were rehashed and remained unchanged |

The independent diff is retained as `v2/independent-v1-v2.diff`. Source, worktree, base ancestry, original installer/tests preservation, and prior-evidence checks are recorded in `v2/identity-and-preservation.json`.

## Scope limits carried forward

The original cold review's scope observations remain applicable because the environment preparation, source-free child, native process implementation, four-child experiment, budgets, and workflow bytes did not change. This correction adds observation work inside each snapshot; it adds no native child and does not alter the stated timeouts. Two completed inventory passes are retained on the comparison/drift path; a non-completing enumeration still fails closed rather than being represented as complete.

No PowerShell parser retry was attempted. The previous containment preflight failures remain the reason no parser/runtime evidence is available. This PASS is solely for the focused source and inert-oracle rereview of WDR-001; it is not a Windows 5.1/7.6.6 runtime PASS, a product PASS, or authority to modify the failed original core snapshots.

PASS
