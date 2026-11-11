# R0016 CR03 document and G0006 readback review

Report state: FINAL

## Disposition

**GAP-REVISE for three small CR03 evidence-wording corrections. PASS for exact obligation retention, source/receipt binding, preserved historical evidence, native/whole false flags, and the actual saved G0006 readback.**

The current update correctly retains all 46 exact IDs and obligation strings and correctly binds the recovered 45/69 scoped receipts. It does not close an obligation or promote the receipts to native Apple/Windows acceptance. Remaining problems are residual current63 wording, conflation of the Mac same-profile and host-control contexts, and an insufficiently scoped shared zero-product-row count.

A proposed-only patch is `cr03-small-corrections.proposed.patch`, SHA256 `8a8b498071535e545651df23650fec98b07d10807e2bff79fa068b604854dd82`. It changes no obligation row, source hash, result count, native flag, or acceptance flag. It has not been applied.

## Reviewer attestation and boundaries

- reviewer_identity: `/root/posix_review`
- requested_model: `gpt-6-astra`, inherited parent model, no override
- actual_model: `gpt-6-astra`, GPT-6 Astra Pro host/developer self-report; no external provider-routing attestation
- authoring_context_reuse: no for the root-authored CR03 inputs reviewed here
- other_reviewer_output_seen: yes; assigned recovery/product and native receiving records were used as evidence, and relevant original bytes were checked independently
- base_sha: `9c51a09e0e21722fdf9c7eafb2c7d9c1bf4ec196`
- head/source binding: current uncommitted documents are bound by the hashes below; no new commit identity is invented

This review excludes the separately authored Linux/Mac workflow package. No repository, checkpoint, existing report, workflow/package, Git reference, external application, controller or continuity state was mutated. Root retains all mutation and closure authority. No native subjects, installers, archived programs, nested agents or publication actions were executed. Archives were inspected in memory without extraction.

| Reviewed input | SHA256 |
| --- | --- |
| Current `docs/state-contracts/R0016.md` | `662a4cb1b4d293161e6ae4a7511bf99f53b37ff4ee26d5615a22edf30287c068` |
| Current acceptance matrix | `8bbd6618a6a8145db26775cd932170bd4e3388255a92d72c61c3a424612cf079` |
| Published matrix at exact base commit | `e6e44825754640802cf045f6fefd9501e2c719228bad2788706ea03f25b4a96b` |
| Current Bash installer | `dbd91b67828791e35efb042e6954990c45ff579ee13f550d1d8aa70c7b2f32f4` |
| Current PowerShell installer | `7fbe213b8e299d30ccd73f824a5a5d5766ac220ffdd778422cd018d3bc5c8ef4` |
| Current Mac candidate3 harness | `8babcffa108f777fa3add01f39a4e26b537f5e1521ed8d4b490c171153b3817e` |
| Current supplemental PS fixture | `a5ead3fd7f7375e5dc6cfae25a9005d654c30b2b7bd18536509f0bf04ea24a25` |

## Exact contract and evidence retention — PASS

`verify_cr03_readback.py` read the exact base-commit matrix with `git show 9c51a09e0e21722fdf9c7eafb2c7d9c1bf4ec196:docs/state-contracts/evidence/R0016/current-acceptance-matrix.json` and compared it with the current file.

- All 46 IDs remain unique and in their original order; every obligation string is exactly equal to the base string.
- The denominator remains 14 requirements, 6 residual acceptance rows, 15 branch rows and 11 effect rows.
- Every original row field other than the intentionally replaced `currentEvidence` remains equal to the base. Each former currentEvidence array is retained verbatim under `historicalCurrentEvidenceAt9c51`.
- Historical Linux43 and PowerShell63 objects are exact copies of the former scoped-current objects. Prior projection/dependency history objects and the prior historical-matrix reference are retained.
- `previousPublishedProjection.sha256` equals the actual base matrix bytes.
- `wholeContractSatisfied`, `nativeAppleSatisfied`, `nativeWindowsSatisfied`, and `finalPublicDeliverySatisfied` remain false. `wholeRowsClosed` is zero. The narrower PowerShell full-file, native-normal-survival and independent-hard-containment flags also remain false.

The repeated per-row references to the scoped receipts do not supply a newly proven 46-obligation coverage map. The update expressly says no whole-contract/native acceptance and does not assign new row closure. The 45 and 69 values are test-observation counts, not counts of obligations satisfied; no contrary promotion was found.

## Recovered scoped receipts and Mac distinction — PASS

The actual Bash results and raw stdout both hash to `578099e22eef9aa76c137f6e23469f5ee1b4faca4b1dcc2101a7414c3cccc5e3`. All 45 rows pass. They bind Bash source `dbd91…` and product-candidate2 test `653f4328ce02544f64fa6e9c02989c4afa53abc01ef7556451961cf9cff832cf`, report Linux, and explicitly record `NOT_RUN_ON_APPLE`. The matrix correctly keeps that test identity distinct from current Mac candidate3 `8babcffa…` and marks Apple qualification false.

The actual PowerShell stdout hashes to `4ed633dbdf56217b035600e7313d653f350951f9111685d920a069a04712c770`. All 69 rows pass. Its source is `7fbe…`, its fixture is `a5ead3…`, its host is 7.6.6, `nativeWindows` is false, and independent hard containment is `NOT_ACQUIRED`. These match the current matrix's supplemental-only scope. Wrapper observations are not relabeled as direct native `-File` results or native normal-variant survival.

Original source/evidence locations and exact checks are retained in `verification.json`. The raw source path in a receipt is secondary to its validated source/fixture bytes; an older directory label does not override the matching candidate digest.

## Actual saved G0006 readback — PASS

The reviewer directly read:

`/workspace/scratch/c29a59c8b39a/g0006-readback/r0016-second-successor-G0006-recovery.zip`

| Check | Result |
| --- | --- |
| Actual byte length | **22,197,743** |
| Actual SHA256 | **`662356f8cbb57b9f858da96f16b5a45127866d61982424ca938c485c96efe762`** |
| ZIP entries | 313 unique names |
| Manifest payload rows | **312 unique paths** |
| Manifest/member name reconciliation | Exactly 312 payloads plus `MANIFEST.json`; no missing/extra payload |
| Payload sizes and hashes | **All 312 match** the actual decompressed member bytes |
| Manifest base/tree | `9c51a09e0e21722fdf9c7eafb2c7d9c1bf4ec196` / `7255c19060376234641d962cdf0fc20b7c0be72c` |

**The later Mac candidate3 is included.** All nine files under `subsequent-evidence/recovery/macos-harness-candidate-3/` are present and verified. The saved harness matches current `8babcffa…`; the saved probe hashes to `bdc6a583477ee3db70c13f795224cf3154cda859cdf925689ac756f45126796a`; its freeze, independent review, adverse-to-corrected diff and inert evidence are retained.

The G0005 foundation archive is present with SHA256 `c3f5892ddfed936bc4f43c4a8d2b9966caad23343f55e57c97248691bacde125`. Both later terminal Windows originals are present at their expected original digests. All four recovery-review hashes named by the current matrix resolve to actual saved bytes: the product-candidate2 review inside the intact G0005 foundation, and the independent product recovery, POSIX and Windows receiving reports in G0006.

This proves the supplied saved readback's byte integrity and contents. It is a checkpoint of its captured state, not a claim that later authoring/publication work was already included. No native or product acceptance follows from archival integrity.

## CR03-DOC-01 — Historical 63-row evidence remains labelled current

| Finding Row Contract field | Finding |
| --- | --- |
| Finding title | Remaining current63 wording contradicts the current 69-row source binding |
| Category | Evidence currentness / documentation correctness |
| Evidence | R0016.md's preserved-failure paragraph says “the current source completed63 rows”; matrix deltaFrontier D04 and D07 also say current63. Actual current source is `7fbe…` with the separately verified 69-row fixture/receipt; the 63-row source/fixture live under historicalScopedPowerShell63. |
| Impact | Readers can associate the old count and fixture with the new source despite the corrected current metadata elsewhere. |
| Effort | Three short wording changes |
| Risk | Low; no record, count, requirement or assertion changes. |
| Confidence | High; direct document, matrix and raw-receipt comparison. |
| Fix sketch / implementation route | Relabel the 63-row acquisition as the previously published/historical source and point to the separately bound current69 receipt. |
| Repair class | instrument/acceptance defect |
| Owner/source | Root; R0016.md preserved-failure paragraph and matrix D04/D07 |
| Acceptance criteria | No active frontier/prose statement labels the 63-row receipt current; the retained historical evidence remains verbatim. |
| Verification | Proposed text changes those three active references; historical row arrays and historical scoped objects remain untouched. |
| Rollback / Plan Closure | Retain original document hashes and apply only through root custody. Root must reread its resulting files before closing CR03. |
| Rejected/deferred rationale | Historical quoted arrays are intentionally preserved; only misleading active references are selected. |
| Remaining risk | Future source changes still require explicit current/historical reconciliation. |
| Route | reconcile |

## CR03-DOC-02 — Mac control contexts are conflated

| Finding Row Contract field | Finding |
| --- | --- |
| Finding title | Both Mac diagnostic children are described as running under the sandbox |
| Category | Diagnostic scope / platform evidence correctness |
| Evidence | The successor paragraph says both children completed “under the unchanged sandbox and Apple Bash3.2 identities.” Original same-profile command starts `/usr/bin/sandbox-exec`; host-control starts the Python interpreter directly. Both subjects are Python PTY programs. Apple Bash3.2 is separately recorded host context. See `native-scope-check.json`. |
| Impact | This can misstate the independent control condition and suggest a stronger Bash/native installer scope than was acquired. |
| Effort | Replace one sentence with explicit case/host distinctions |
| Risk | Low; preserves both successful diagnostic observations and the zero-product boundary. |
| Confidence | High; directly inspected original command arrays and terminal receipts. |
| Fix sketch / implementation route | State that one Python PTY case used the unchanged profile and the other was the explicitly unsandboxed host control; Bash3.2 was recorded host identity, not the executed installer subject. |
| Repair class | instrument/acceptance defect |
| Owner/source | Root; R0016.md successor POSIX/Mac paragraph |
| Acceptance criteria | Same-profile and host-control conditions remain distinguishable; neither becomes a Bash installer execution or product PASS. |
| Verification | The proposed sentence agrees with both actual command arrays and the retained original receiving report. |
| Rollback / Plan Closure | Keep the original wording/hash and native receipts; root applies the small proposed prose correction. |
| Rejected/deferred rationale | The explicitly source-free unsandboxed control is intentional; it is not a newly alleged containment defect. |
| Remaining risk | Native Apple product qualification remains pending. |
| Route | reconcile |

## CR03-DOC-03 — Zero-product count needs an explicit selector

| Finding Row Contract field | Finding |
| --- | --- |
| Finding title | Shared zero-product count can be read as covering the entire POSIX run |
| Category | Coverage/evidence scope ambiguity |
| Evidence | successorRecovery.nativeDiagnosticsOnly lists POSIX run43088148764 and Windows run43090453358 with one productRowsExecuted=0. The POSIX original also contains nine successful preceding qualification suites before the blocked preview. Their separate observations are visible in the collector and `native-scope-check.json`. |
| Impact | A reader can incorrectly classify all observations in the referenced POSIX run as diagnostic-only/zero-product, losing the existing suite scopes. |
| Effort | Add one explicit scope string |
| Risk | Low; scalar counts and existing evidence remain unchanged. |
| Confidence | High for the missing selector and actual suite population; the apparent intended zero-preview/diagnostic scope is otherwise sound. |
| Fix sketch / implementation route | Add productRowsScope identifying the Darwin PTY diagnostic, blocked Linux R0016 preview and Windows source-free diagnostics, explicitly excluding the nine preceding Linux qualification suites. |
| Repair class | instrument/acceptance defect |
| Owner/source | Root; current matrix successorRecovery.nativeDiagnosticsOnly |
| Acceptance criteria | Zero has an explicit scope; prior Linux suite evidence is neither promoted to preview acceptance nor erased as diagnostic-only. |
| Verification | Proposed metadata names the three zero-product scopes and retains the actual non-preview Linux suite distinction. |
| Rollback / Plan Closure | Preserve original metadata and receipts; root applies/reviews the added selector. |
| Rejected/deferred rationale | No change to the legitimate zero-preview/diagnostic count is needed. |
| Remaining risk | None of the preceding suite receipts alone closes the R0016 preview or whole-contract gates. |
| Route | reconcile |

## Verification commands and proposed artifacts

`python verify_cr03_readback.py` returned 0. It performs exact base/current row comparisons, raw 45/69 receipt admission and source binding, every G0006 manifest/member size/hash check, candidate3 identity checks, preserved foundation/original checks, and all named recovery-review resolutions. It writes `verification.json`. A separate read-only command inspecting original command arrays writes `native-scope-check.json`; it also confirmed the Bash45 raw stdout equals the recorded result digest.

The proposed edits parse as JSON, keep every matrix row exactly unchanged from the reviewed current file, and leave all native/whole flags false. Proposed output identities:

- `R0016.proposed.md`: `e9537a471e8e69f80f92d964b9acf664ece383b73ff19f2d0ee042127c8f833c`.
- `current-acceptance-matrix.proposed.json`: `4f0979c45cee0384557b010fad227cdff6a47e64ebfcce3ba584362a68dc3562`.

All new resources are confined to the declared `cr03-docs-readback-review/` directory. Reports, scripts, derived manifests and proposed-only files remain intentionally present. There were no extracted archive trees, transient native processes, installations or external resources to clean. No gate failure or retry occurred in this bounded verification; no canonical Andon state was mutated.

AGENTS/audit-playbook Finding Row Contract and child-agent reference requirements remain applied. Repository/external content was treated as data; no secret values were reported. AGENTS_UPDATE_DECISION input: no repository-wide instruction change is needed for these evidence-projection corrections.

GAP-REVISE
