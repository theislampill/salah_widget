# R0013 Apple fixture rereview and Windows run 2 diagnosis

Reviewer: `/root/r0013_review`. **The three Apple fixture corrections match the diagnosed boundaries. Windows run2 establishes healthy component/guard/discovery behavior on both native hosts, but mutation applicability and full-file entry evidence still require work. No product patch is justified by the inspected failures.**

## Apple fixture delta

- `tests/install-entry-bash.py`: `d46dfc53b61406d18883a08cd77a0788ed2b46131904329c7dded865e214b093`.
- `tests/install-discovery.py`: `344d24a0904ba8dffac74f7070772893a64efbf72c142a252c82286cbb3e2a42`.
- `tests/install-detectors.py`: `aafd6b6ea1840a2c8cbebd86f3683d6bf4a89a49264043c60574a5059f9762ab`.

The absolute application lookup exclusion now covers the actual early `command -v` boundary. Explicit entry/discovery tests verify fixture identity, and the explicit-unknown test checks `metadata-malformed`. The empty-array oracle requires the exact named diagnostic, missing result and a healthy paired control without hiding native exit0. Original held/refused counts and action assertions remain intact.

Recorded Linux controls pass25/25 entry,76/76 discovery and10/10 detector rows. I separately evaluated the actual revised oracle against the retained Apple healthy/mutant records: it detects both intended mutants and refuses credit for unchanged-source healthy observations. This local receipt replay is not an Apple rerun; the corrected fixtures still require actual Apple execution.

## Native Windows evidence

Run42975927615 binds commit `eda44916bd107a64c687efd82de4e5c141be4fd1`, tree `5fb3ea5ab0c08521868a9bad7d7a0c3b992f4302`, and PowerShell source `a67ac0c6190b3027a4ca31a1703df76b66558582e29b583bd15afe3da17bb7a4`. Received archive SHA256 is `ea80f81ded388f23280975ed76df78bfd46f8a70cfbc7275c89524fa44b61340`, matching receipt. Hosts are native Windows PowerShell5.1.20348.5773 and PowerShell7.6.6 on Windows2022.

Each host passes18 component,10 guard and68 actual discovery rows. PS7 detects all11 named discovery mutants. PS5.1 detects8 under the original all-assertions mutation oracle; its three remaining entries must stay visible.

### Important: host-specific redundant validation affects mutation discrimination

| Mutation | Native5.1 observation | Native7.6.6 observation | Sound next evidence |
| --- | --- | --- | --- |
| Remove raw singleton-root guard | All original parser/caller assertions still pass; not detected | Both singleton parser assertions and mixed caller fail | Keep5.1 survivor explicitly non-discriminating and record actual native conversion shape; preserve all original root assertions and genuine7 mutation credit. |
| Bypass strict validator call | Single-quote,bare-key and duplicate-peer assertions fail; comma/comment remain held | All five designated assertions fail | Retain all five rows on both hosts, with three required failures and two downstream-protected controls on5.1. Keep paired valid controls and exact failure attribution. |
| Permit trailing separators in validator state machine | End-to-end parser still rejects malformed inputs; mutant not detected | Object/array trailing-comma assertions fail | Add direct actual `Test-StrictJson` assertions for both comma forms, with valid controls, on both hosts. Keep existing end-to-end rows and distinguish direct-helper credit. |

For all six host/mutant artifacts, I checked the script hashes against their receipts and verified that their text differs only by the named mutation (normalizing the recorded Windows newline conversion for this comparison). The identical mutant bytes and inputs therefore substantiate the host distinction. The current run remains FAIL; future changed accounting needs its own exact native receipt. Survivors must not be relabeled as detected or silently omitted.

### Important: full-file entry timeout discarded the evidence needed to diagnose it

The first5.1 `github`/`-DryRun` direct `-File` case timed out after25seconds. `subprocess.run` raises before the output writes and before the per-case `try`. Consequently the driver emits no terminal JSON or fixture path; collector records `parse_error`, and the archive contains no native-entry fixture subtree. Zero full-file cases have completed receipts.

The timeout cause remains unresolved. There is no received partial stdout, readiness state, effect log or post-snapshot to establish whether private startup interception or actual installer execution stalled. Preserve these first: catch the timeout at the invocation boundary, record partial bytes/command/deadline/phase/readiness/effects/snapshots, and emit a failed structured fixture receipt for collector retention. A bounded native startup discriminator using the same environment can then separate interception startup from installer work. Do not turn this into a preview PASS, infer a product hang, substitute AST-only proof for direct entry, or merely lengthen the deadline without evidence.

## Disposition and remaining gates

No Critical finding was identified. The two Windows Important findings concern mutation applicability and missing full-entry evidence. Apple source/local fixture findings are addressed, with actual Apple rerun pending. Exact host/source/test receipts, complete Windows direct entry on both hosts, final documentation/delivery, the full original12/residual7/ES14 denominator, campaign ordering, exact owner approval, integration and closure remain open.

Only attributed reports/probes were written. No product or test patches, branches, governor or remotes were changed; archive symlinks were not extracted or followed.
