# Windows reconstruction candidate 1 — independent source-free carrier review

State: **FINAL**. Disposition: **PASS for the bounded source-free carrier code and exact recovered PowerShell inputs**.

This PASS covers the inspected ten-control acquisition path only. The NEW Python receiver remains **GAP-REVISE** in `windows-core-review-candidate1.md`; there is no overall Windows PASS. This report is not native product acceptance, workflow approval, publication authorization or a lifecycle decision.

Requested model: inherited parent without override. Actual model: host-declared GPT-6 Astra Pro; provider deployment identifier unavailable. `authoring_context_reuse: no`. The reviewer authored none of these Windows bytes. Only inert file reads, hashing, Python receipt checks and source inspection occurred. PowerShell parsing, the ten controls and native timing/semantics have not been executed by this reviewer.

## Exact identity and received inputs

Packet manifest SHA256: `08d7be4b936d269589efe597bb0dfbd3c707e6a0d1434a8fcfdd821b34e33923`. All 25 payloads totaling 398418 bytes match their declared identities.

| Carrier input | Bytes | SHA256 |
| --- | ---: | --- |
| NEW install-preview-carrier-controls.ps1 | 13102 | `733ff1ebc15b6e83e319313c33cbf67a888763a27388155d52ebe0e7c0497e04` |
| Exact recovered install-preview.ps1 | 57909 | `e5db234866df5fa41862dbb1d67fed4594b77b882823bfd631a9c5bf98525916` |
| Exact recovered install-preview-window.ps1 | 13117 | `05318962698c269fb1d8b873e31b80b3ffe526739e21a49b5cf0459d523dcb83` |
| Exact recovered install-preview-acquire-timed.ps1 | 22009 | `b7938e602fcf3864462f08b4748a139e894b8c4802d8643840d4439894a0ffd1` |

The three recovered files were compared byte-for-byte with their declared original G0010 paths as well as with the packet base/proposed copies. The carrier is explicitly a NEW reconstruction. No missing historical final carrier, final receiver, historical 37-check result or native PASS is assigned to it.

Independent static receipt: `/tmp/r0016-third-20261111/work/independent_review/windows-core-candidate1/carrier-static-receipt.json`, SHA256 `e91adfefe60048731a5683aae444d327e94b935ee676866c70c56a2ae7155299`.

## Source-free execution boundary

The adapter has no installer SourceFile parameter. It reads and freezes the three declared fixture inputs plus itself, verifies literal SHA256 values for the recovered inputs, and rechecks originals and retained copies after the control run. It never invokes the producer or acquisition script as a complete top-level program.

The acquisition library contributes only five selected function definitions. The definition-only window library contributes its exact six functions; its top-level statement count must match that whitelist. The producer contributes only its unique `New-PreviewCase` definition, unique embedded single-quoted driver and uniquely delimited control span ending before Helpers dispatch. It refuses ambiguous definitions/delimiters and a span containing the product dispatch helpers or SourceFile reference. Inputs are checked by the native parser before the extracted pieces are evaluated.

The exact recovered embedded driver has SHA256 `d81ce7e94bb1545acff16c080e0c8fa136bef02dc857bfafe2b44fdeb5b9bc50`; the source-free control span has SHA256 `15450034c2a9c790893963c4aea112d2819046fb3c64b5b47ef024ed3df68c38`. These are derived source-byte identities, not runtime observations.

The adapter initializes source/function placeholders as owned synthetic files. The four guard cases execute only an owned method-write control or an owned loopback control. The six wrapper cases replace the source with individually written inert scripts. Their cases are exactly fallthrough, explicit exit 0, explicit exit 17, throw, finally followed by exit 17, and parameter rejection before its body. The expected inventory requires ten unique cases. The embedded driver's complete-source call therefore receives these synthetic files, not install.ps1.

The Python receiver under adverse review is neither imported nor invoked by the adapter or the extracted span. Its failure does not introduce a dependency into this source-free path.

## Host, command and capture binding

Native admission requires Windows and an absolute current process executable. The selected host must be Desktop 5.1 or Core exactly 7.6.6. Both imported launch functions set ProcessStartInfo.FileName to that same current executable. Their Arguments value is constructed directly as `-NoProfile -File` plus the supplied File value, and that same File value is recorded as nativeFile. The reviewed adapter supplies the exact extracted driver to every launch and checks the retained launch host, PID, nativeFile and fixed 60-second budget afterward.

The post-launch carrier comparison does not independently parse the raw arguments field. For this bounded adapter, command identity is supported by the exact pinned constructor just described and fresh owned launches. This report does not qualify that comparison as an admission API for arbitrary external or reconstructed receipts; the NEW receiver's missing argument checks remain a separate concrete GAP.

The inherited observer closes stdin, starts asynchronous stdout/stderr reads, checks completion, and retains raw output. The adapter requires explicit drain completion, no expired kill grace, and a terminal-observation duration below 60000 ms for each control. The held observer retains before/after PID/nonce signal and ACK files, refuses late ACK acceptance at 20 seconds, and refuses a terminal first observed at or after the child deadline. Existing bounds remain 60-second child budget, 20-second ACK, 5-second kill grace and 2 seconds per output drain. These controls are inspected behavior pending native execution, not acquired timing results.

## Snapshot and control scope

The exact window Snapshot-Subject definition supersedes the older acquisition snapshot definition in the adapter. It retains the subject root and descendants, paths, attributes, timestamps, native owner/group/DACL, regular-file hashes/lengths and link targets. Held snapshots use two complete agreeing passes. No TEMP entry, startup-profile name, timestamp or ACL is filtered out.

Full prelaunch/postexit observations remain separate from the six held invocation windows. An unequal full host lifecycle is retained as unequal; matching held snapshots do not rewrite it. The four source-free guard controls supply allow/deny companions for the owned method write and loopback connection. Their interception evidence is not an operating-system sandbox. The report explicitly records `independentHardContainment=NOT_ACQUIRED` and keeps external runtime/containment prerequisites outside its claim.

Setup failures, incomplete case inventories, mismatched custody, capture failures or semantic-control failures remain BOOTSTRAP_BLOCKED. The adapter does not label these as installer assertion failures or installer product PASS.

## Verification and remaining scope

All 16 supplied pure static checks were rerun in the reviewer's private copy and passed. The reviewer additionally traced all selected function inputs, the exact source-free control span, both launch constructors, the held-gate boundary, native host gate and final result classification. No decision-changing code defect was found in this bounded acquisition path.

PowerShell parse/execution credit remains zero in this review. The first actual native run must provide its own parser, launch, raw output, complete snapshots, control-result and custody evidence for these exact bytes. The separate route/workflow pair was not part of this packet and has not yet been reviewed here.

Historical G0010 adverse evidence remains preserved, including the prior FINAL GAP review SHA256 `8b0433523810046ef938eb0256e76d26ee1803dafc73a99c36834e3185f8a061`. No old source-free native observation is reused as execution evidence for the NEW adapter. Helpers, product wrappers, direct -File behavior, normal/NoOpen variants, whole-contract acceptance and publication remain outside this PASS.

Return to root: the exact carrier and three PowerShell inputs above pass independent source review for a separately qualified ten-control source-free acquisition. Root retains decisions about route integration, native dispatch and subsequent evidence receiving. The NEW receiver remains blocked independently.
