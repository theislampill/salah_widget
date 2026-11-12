# R0016 independent product and checkpoint recovery review

Report state: FINAL

## Reviewer attestation

```yaml
reviewer: /root/product_recovery
requested_model: gpt-6-astra
actual_model: gpt-6-astra
model_evidence: canonical self-report, not independent provider telemetry
authoring_context_reuse: no
context_isolation: fork_turns=none, confirmed by root
other_reviewer_visibility: historical reports explicitly included in this recovery scope; no contemporaneous reviewer findings consumed
base_sha: 503a4d57852b195dce4c36c5b8ab9299c9036e95
base_tree: f16971c25d7af8fb7468d232a27688a78874747c
head_sha: 9c51a09e0e21722fdf9c7eafb2c7d9c1bf4ec196
head_tree: 7255c19060376234641d962cdf0fc20b7c0be72c
candidate_kind: frozen unpublished files, not a new Git commit
route: ordinary independent child-agents recovery review
closure_authority: none
```

Root clarified that no internal `audit-assess` route was intended. This report is evidence for root reconciliation. It does not authorize mutation, currentness promotion, native execution, publication, integration or closure. No repository/shared source was edited; no installer, PowerShell runtime, PTY child, native diagnostic, workflow or external operation was run. Writes were confined to `/tmp/r0016-successor-20261111/second-successor/product-review`.

Read confirmation: applicable repository `AGENTS.md`; implementaudit `references/child-agents.md` and `## Finding Row Contract`; frozen candidate 1/2 source deltas, freeze manifests and final product reports; current source entry/preview boundaries; R0013 discovery and downstream interface sections; R0015 candidate interface and relevant native6 limits; all 46 obligation texts and their retained scope fields in the current matrix; G0005 manifest/restore text; preserved actual product/oracle receipts. Proposed diagnostic reports were inventoried by identity and disposition only and receive no product acceptance credit. No ancestor AGENTS file exists at `/AGENTS.md`, `/tmp/AGENTS.md` or `/tmp/r0016-successor-20261111/AGENTS.md`.

## Disposition and scope

**GAP-REVISE for the current acceptance projection (existing CR-03).** Checkpoint integrity, candidate 2 identity, the two bounded product repairs and the three repaired regression predicates pass the checks described here. No additional product-source defect was established. The live matrix and R0016 prose still identify pre-repair source/test evidence as current and need exact-candidate reconciliation before use as a current review or delivery record.

Candidate 2's original FINAL PASS is recovered, not expanded. Its scope is the two product changes and three oracle corrections. The current Mac harness has a separate later history and must retain its own qualification boundary. Neither this report nor 45 Bash / 69 supplemental PowerShell observations closes native Apple, Windows or whole-contract obligations.

## 1. G0005 recovery integrity

Both the original local ZIP and independent-readback ZIP are exactly **23,131,994 bytes**, SHA-256 **`c3f5892ddfed936bc4f43c4a8d2b9966caad23343f55e57c97248691bacde125`**. Both pass ZIP CRC checking. This agrees with the supplied provider identity `libfile_9a865c035584819187da3ed3ee7f1a00` and the retained local receipts; this reviewer did not perform a new remote download or metadata call.

The archive contains 5,369 entries: 5,368 files plus `CHECKPOINT-MANIFEST.json`. Every manifest size/hash was independently recomputed and matched. There are no duplicated names, missing or extra unmanifested payload files, absolute paths or parent-traversal names. The one recorded symlink is metadata only and was not materialized. Manifest SHA-256 is `5093023ff7ed00e66f8830ff471cad85b8cbd58b0caa1c6b980e2a8189c26b32`.

The archived Git bundle is 100,683 bytes, SHA-256 `218a9653ccd3eb98c83e993017cedcd45bd1c37cc9dbcd822b4655b0b8803869`. `git bundle verify` succeeds against the existing repository and names the expected branch head `9c51a09e0e21722fdf9c7eafb2c7d9c1bf4ec196`. It requires foundation `65c995e1aa49dd69834b5ea8ad9242dc3d28c4e5`; it is not a complete standalone repository bundle. There are exactly two commits between that foundation and the recovered head.

The embedded G0002 archive is 12,338,145 bytes, SHA-256 `dcde2f25ad131d0841c08fd164ba47a2201f8aa525522c4912e5242b12208aa6`, with no CRC error. It retains all six original failed artifact ZIPs: 13863975129, 13864196347, 13864365018, 13867114561, 13867274335 and 13868376534.

A strict, in-memory application of `working-tree/changes.patch` to the exact recovered HEAD blobs reconstructs all five archived modified files byte for byte. The same check applies candidate 2's `source.diff` to its declared `503a4d57...` base and reconstructs all five frozen candidate files. No source files were written by these reconstructions.

### Captured files versus live files

For 5,355 directly mappable archive paths, 5,354 remain byte-identical: 22 audit files, 5,322 recovery files and 10 working-tree files. The only changed captured file is `working-tree/tests/install-preview.py`. No directly mapped file is missing. Additional live paths absent from the direct manifest are not automatically post-capture additions: some older evidence is inside G0002 and some in-progress reports were deliberately excluded. The detailed inventory keeps that distinction.

| File | Candidate 2 SHA-256 | G0005 / live relation |
| --- | --- | --- |
| `install.ps1` | `7fbe213b8e299d30ccd73f824a5a5d5766ac220ffdd778422cd018d3bc5c8ef4` | Candidate 2 = G0005 = live; 110,645 bytes |
| `install.sh` | `dbd91b67828791e35efb042e6954990c45ff579ee13f550d1d8aa70c7b2f32f4` | Candidate 2 = G0005 = live; 41,956 bytes |
| `tests/install-entry-native-coverage.py` | `c061ec0b148c9052b46440fcf980542936d316a0b7286629c1b011738a56d121` | Candidate 2 = G0005 = live; 33,778 bytes |
| `tests/install-preview.ps1` | `a5ead3fd7f7375e5dc6cfae25a9005d654c30b2b7bd18536509f0bf04ea24a25` | Candidate 2 = G0005 = live; 51,073 bytes |
| `tests/install-preview.py` | `653f4328ce02544f64fa6e9c02989c4afa53abc01ef7556451961cf9cff832cf` | Candidate 2: 51,301 bytes; G0005: 53,719 bytes / `f9eb146d50e13b3b0361586bf38c266db300e049e37dd9a83fdd2f7b412c271b`; live: 54,527 bytes / `8babcffa108f777fa3add01f39a4e26b537f5e1521ed8d4b490c171153b3817e` |

The live last file exactly equals `recovery/macos-harness-candidate-3/install-preview.py`. Its embedded probe exactly equals candidate 3's `terminal-probe.py`, SHA-256 `bdc6a583477ee3db70c13f795224cf3154cda859cdf925689ac756f45126796a`. Candidate 2 product harness and current harness are byte-identical outside that literal; AST comparison likewise shows only `bootstrap` changed among 20 functions. The six-function native coverage harness is entirely unchanged from candidate 2.

G0005 includes Mac harness candidate 1 only. Candidate 1's subsequently completed review is GAP-REVISE, SHA-256 `208f2648ff7313c700304966aadf57c9c4934f5ad91bf5a1e2b361ee983523c5`: ownership-loss cleanup could signal an unowned PID, and late success could evade the declared work deadline. Candidate 3's separate bounded PASS report is SHA-256 `c39a4f5ed3668802576f147c2887b4c4a72acfa20f31fe4611d8b2a14329e520`. This recovery review binds that later history; it does not independently qualify the native Mac correction. Restoration from G0005 alone would recover the older harness and lacks those later reports. Root should preserve the later source/evidence in its next checkpoint rather than treating G0005 as a current-code checkpoint.

## 2. Product correctness and interface preservation

Published HEAD's installers differ from R0015 head `bf566111fe530b5de2c7c63ca4586e83d5f4b965` by exactly three usage-comment additions each. Their HEAD hashes are PowerShell `b579fb83c91c9f45b7ca461f6e7a1cafbc7af1e2132dee5b1cb333623ac2cc3e` and Bash `9e0facbed4053dddbf676c58e4a07515371cdd7f35ad4d85164486d2c71fdb9c`. The unpublished product delta is confined to the following changes.

**CR-01:** PowerShell validates the effective bound `$InstallSource` immediately after parameter binding and `$ErrorActionPreference`, before installer output, discovery or effect-helper calls. This rejects an invalid environment-derived default and retains a valid explicit override of an invalid environment. Empty/unset environment still selects the existing `github` default. Case-insensitive PowerShell membership agrees with the existing route comparisons. Source remains ASCII and retains `#requires -Version 5.1`; this is source-level compatibility assessment, not native PS5.1 execution.

**CR-02:** Bash and PowerShell branch preview messages on the existing NoOpen value. Store plans identify a URL to open manually; generic installation/import instructions describe manual opening. Non-NoOpen wording is unchanged. GitHub metadata/version/path facts and `ask` choices remain unresolved. The preview paths still return before terminal acquisition, staging, normal import/installation or cleanup effects.

No discovery producer, target record schema, eligibility rule, staging helper, admission predicate, retained-bundle rule, selector tier, clipboard implementation or normal caller changed. R0013's known/unknown/legacy eligibility and independently usable peers remain intact. R0015's private staging, admitted outputs, retained manual bundles and no-deletion boundaries retain their owner implementation. The PowerShell guard legitimately affects option refusal in both modes; the NoOpen changes are preview wording only.

The frozen Bash source passes `bash -n`. Python test source parses without executing its top-level code. No additional product-source defect was found in this bounded delta.

## 3. Original oracle failures and exact final disposition

Candidate 1's report remains FINAL **GAP-REVISE**, SHA-256 `96385bf64de0983cc33470a2b0930f0a451d0ef5ccbe5a61e0511f23dec03761`. Candidate 2's report remains FINAL **PASS**, SHA-256 **`204dc74a4b24b0804e975e0dc618ea831c31841c07904a65d34b4c70aad47902`**. Candidate 2 freeze SHA-256 is `a3d704474ec324dacaaae2d40c7f5d8c980b4ebdc4ed00a7b306bcd4054c4df4`. Both installers are byte-identical between the two candidates; only the three regression predicates changed.

| Original finding | Concrete original failure | Candidate 2 disposition and independent recovery check |
| --- | --- | --- |
| PF1: wrong refusal channel | Wrapper catches the early validation throw into structured `reason` with nonzero semantic exit, while the assertion searches only stdout/stderr. Correct refusal can falsely fail. | Addressed: inspect admitted `$value.reason`; retain nonzero exit, no completion text, typed receipt, readiness, no-effects and snapshot checks. Six pure reason-channel controls reproduce the required accept/reject outcomes. |
| PF2: manual-word exemption hides opening promise | `Would open the browser automatically (NO_OPEN=1); finish the installation manually.` was accepted because `manually` anywhere on the line exempted the whole line. | Addressed: split semicolon/newline clauses and reject `would ... open/launch` without the broad exemption. Both healthy routes remain accepted. Original RED and the byte-identical contradictory witness are rejected. |
| PF3: store assertion accepts ask | The actual unresolved ask plan contains `official store`, satisfying the old substring-only store test. | Addressed: require full resolved Chrome and Firefox store URL lines and reject unresolved-source text. Eight pure route controls accept healthy LF/CRLF output and reject ask-only, mixed unresolved, missing/wrong URL and non-line matches. |

For PF2 this reviewer verified raw stream hashes and replayed the actual candidate 1 and candidate 2 Python predicate ASTs over all eight preserved actual Bash transcript records. The contradictory stdout is byte-identical across candidate 1 and 2, SHA-256 `15a29f0c15e986e2bb0c7c0baed0e57697d92ff62f38700a58a326a2a65d9f5c`. Candidate 1 accepts it; candidate 2 rejects it. Both candidate runs' retained observations report exit 0, readiness true, unchanged snapshots, zero source effect events and zero source transport attempts. The failure is therefore the original plan oracle, not an acquisition failure hidden by the repair.

The retained 18-case focused oracle script was inspected and rerun with only its output-directory assignment changed to this review's scratch directory. It executes selected Python predicate ASTs and transparent models of literal PowerShell regex/Boolean decisions; it executes no installer, child process or PowerShell runtime. All 18 expectations pass, all five candidate bindings match, and its result is byte-identical to the historical result, SHA-256 `ff7aff31cf673dc1cbc5943d4efd329e1707fadbd10b09e113b95498b9abcfc9`.

The original product RED is also preserved. Its independently received evidence records five product failures across two product findings: invalid PowerShell environment-default source acceptance, plus Bash and PowerShell GitHub/store NoOpen plans. It retains healthy default/override controls and explicitly separates an intentional open-guard control failure. Original report SHA-256 is `5bb4d47871cb592b53b2217bbd6bf258b9597a9292dd36e628360914a1da365d`; it is not relabeled by later GREEN evidence.

## 4. Exact 45 / 69 historical evidence

| Evidence | Observed results and immutable binding | Limit |
| --- | --- | --- |
| `recovery/product-fix-local-v3/launch-bash/r0016-preview-uf86zd1q/results.json` | 45/45; raw/result SHA-256 `578099e22eef9aa76c137f6e23469f5ee1b4faca4b1dcc2101a7414c3cccc5e3`; installer `dbd91b67...`; fixture `653f4328...`; terminal exit 0, no timeout, bound bytes unchanged | Linux Bash 5.2.37; `NOT_RUN_ON_APPLE`. The later Mac harness bytes are not the tested fixture. |
| `recovery/product-fix-local-v2/launch-powershell/stdout.raw` | 69/69; SHA-256 `4ed633dbdf56217b035600e7313d653f350951f9111685d920a069a04712c770`; installer `7fbe213b...`; core fixture `a5ead3fd...`; acquisition fixture `b7938e60...`; terminal exit 0, no timeout, bound bytes unchanged | Supplemental Linux PowerShell 7.6.6; `nativeWindows=false`; the core explicitly records `independentHardContainment=NOT_ACQUIRED`. It is not native Windows whole-file acceptance. |

The source path in these receipts refers to candidate 1 installers; those bytes exactly equal candidate 2 installers, and the fixture hashes are candidate 2. The path spelling is therefore not a stale-source mismatch. The PowerShell 69 receipt is under `product-fix-local-v2`, whereas Bash 45 is under `product-fix-local-v3`; do not assume both are in v3.

The preserved proposed diagnostic review chain separately records packet 2/3 GAP-REVISE, packet 6 PASS, Windows original GAP-REVISE then v2 bounded PASS, and published POSIX/Windows candidate-binding PASS reports. The identity inventory is saved separately. None is a replacement for product results, native acceptance or the 46-obligation matrix.

## 5. Complete denominator and actionable finding

The matrix SHA-256 is `e6e44825754640802cf045f6fefd9501e2c719228bad2788706ea03f25b4a96b`. It contains exactly 46 unique IDs: 14 original requirements, six residual acceptances, 15 branch rows and 11 effect rows. These remain overlapping views of the same contract; 45 and 69 are observation counts, not replacement obligation denominators. All 46 IDs are retained in `matrix-recovery.json`.

### PFR-001 — Reconcile the current matrix and product prose to the recovered candidate (duplicate/continuation of CR-03)

| Finding Row Contract field | Finding |
| --- | --- |
| Finding title | Current evidence projection still names pre-product-fix sources and 43/63 controls |
| Category | Evidence binding / documentation / coverage; proposed priority Important (P2), root assigns final priority |
| Evidence | `docs/state-contracts/evidence/R0016/current-acceptance-matrix.json` still names candidatePS `b579fb83...`, candidateBash `9e0facbe...`, scoped Linux 43 and PS 63, with repeated claims of comment-only source change. `docs/state-contracts/R0016.md:7,29` makes matching pre-repair current-source claims. The verified unpublished products are `7fbe213b...` / `dbd91b67...`, candidate 2 adds 45/69 receipts and four new native-entry scenarios, and the live Bash fixture has a later separate Mac-only hash. |
| Impact | A subsequent current-candidate review or delivery statement can bind to an older source or accidentally carry local candidate 2 proof across a later harness change. The existing false completion flags prevent immediate whole-contract PASS, but do not make the current source associations accurate. |
| Effort | Bounded ledger/prose reconciliation after the joined source/test candidate is fixed; no discovery or staging redesign. |
| Risk | Low implementation risk; material evidence risk if historical receipts are relabeled, original failures disappear or native rows close from supplemental counts. |
| Confidence | HIGH: direct source hashes, original raw result receipts, all matrix rows and the complete source deltas inspected. |
| Fix sketch / implementation route | Preserve the historical matrix/report snapshots. Add the exact current product and fixture identities, distinct candidate 2 and Mac-harness dispositions, and source-bound associations for the 45/69 observations. Map CR-01 to option validation/malformed-option cells and CR-02 to honest plan/NoOpen/store/ask guidance cells. Retain native and delivery residuals on all affected overlapping rows. |
| Repair class | instrument/acceptance defect |
| Owner/source | Root sole repository writer; R0016 matrix, R0016 prose and corresponding audit ledger. |
| Acceptance criteria | Same 46 unique obligation IDs and category counts; current hashes match the final chosen file set; PF1/PF2/PF3 original negatives and later bounded PASS retained; source-free diagnostic outcomes do not close product cells; Linux PS remains supplemental; actual native Apple/PS5.1/PS7, exact-candidate review and final delivery/integration gates remain explicit until separately evidenced. |
| Verification | Recompute file/receipt hashes and matrix IDs; compare current claims against the exact chosen source/test files; require separately authorized native result receiving for native claims. Do not replay a satisfied historical cell merely to change its label. |
| Rollback / Plan Closure | Keep this review and historical files immutable. Revise only the current projection, then root independently checks the joined record. This report does not close CR-03. |
| Rejected/deferred rationale | Not a new duplicate source defect; this is continuation of the already recorded CR-03, now sharpened with the recovered candidate 2 and post-capture identities. |
| Remaining risk | Native complete preview, normal/NoOpen variant survival, actual host filesystem/transport scope, prerequisite integration, owner approval and public delivery remain separately open. |
| Route | reconcile |

### Preserved residuals and dismissed observations

- **Native coverage remains unproved by this local recovery.** The matrix's whole-contract/native-Apple/native-Windows/final-delivery flags are all false. Keep R0016-A01/A02/A03, 22-09, actual native helper/entry/normal-variant effects and delivery obligations explicit. The inherited R13/R15 native scopes do not automatically prove new preview fixtures or the changed option/message paths.
- **No new native scenario-routing omission found.** The direct-entry harness declares 18 scenarios, including the four new environment/NoOpen cases. The R0016 qualification driver does not restrict that list; its two-scenario restriction is specific to R0015. The separate variant-normal companion intentionally selects positive/no-open. This observation would become a gap if an R0016 invocation narrowed `--scenario` while claiming all 18.
- **G0005 is a valid historical checkpoint, not current code.** Its exclusion of later Mac candidate 3 is expected by capture time, not an archive corruption finding. A new recovery checkpoint must retain the later source and its separate reports before claiming it reproduces the current file set.
- **No additional NoOpen product regression found.** `ask` remains unresolved, installed targets preserve their existing handling, and held/refused targets remain blocked before actions. The review does not demand broad source rewrites or new native effects from these observations.

## 6. Probe limits and retained review errors

The first historical summarizer assumed every row contained `observation`; oracle-rejected rows instead expose `retainedObservation`. It stopped with a `KeyError`, wrote no product files and made no product claim. The corrected reader explicitly handles the retained record and verifies raw byte hashes; the error and correction are retained in `reader-correction.json`. An initial displayed embedded-probe comparison removed a leading newline from only one operand and returned false; the corrected exact-byte comparison matches both 3,596-byte strings at the same SHA-256. This was a reader normalization error, not source drift; `embedded-probe-binding.json` records it.

Only ZIP/hash/manifest inspection, read-only Git checks, pure in-memory patch reconstruction, Bash syntax checking, Python AST inspection and inert predicate replay were performed. Historical native reports were not rerun. Root remains responsible for the currentness/acceptance decision, source changes, native authorization and final closure.

## Evidence files produced by this review

| File in this review directory | SHA-256 |
| --- | --- |
| `archive-verification.json` | `9002302a40b93c50b67d7da73d1d6c8b1c7b684daed411dd88e57c005fda203b` |
| `patch-reconstruction.json` | `41257736a01fa25b18427444e0d3066fe901e12ed75f2ea6b6b8dfe57e2ced69` |
| `embedded-prior-verification.json` | `b6110513fdfb11a6e748e85803ec7517b9878f83c67eafb83252d96ce64d1cbb` |
| `post-capture-inventory.json` | `6398607915495e6e8d478467ebee492af9065071df6d76e7522a322bd9114876` |
| `post-capture-install-preview.diff` | `26ba2dca9f37e5f0cfdbb35e15293475d04e1a422b4a4e1e3569d8979fe42b08` |
| `product-interface-binding.json` | `c03ed47d1a25848650a7c234fc778c89f6f96d1229237c42bf1d044da78cac43` |
| `candidate-to-live-function-binding.json` | `5f5ad6f88fdc63390680ac3bee7671e9d7fb97aaf5bb2821e4b73ab445285828` |
| `mac-postcapture-binding.json` | `4a2bd88541a1e51b3dacb38ff0a371c759cd455268ab835dceaa3ca287731491` |
| `embedded-probe-binding.json` | `d3a150329e52d44ac3648fff51bf259a490462fb8d986d0727772d82250cdeea` |
| `historical-results-binding.json` | `4a2bd1324bc60179696591a55980b927e8d2ed71c96f41ed76763195975c9c4d` |
| `matrix-recovery.json` | `b6cb04404f5e61de9d45267065c440f05ab4011406e8ab6cbf315fa45d94b540` |
| `proposed-review-inventory.json` | `67dffd2af3f7690370bd0ae099f9298bd809d456201d339dc81ed16a6fa35860` |
| `original-oracle-transcript-replay.json` | `5848b4ee5b50e6fe4ed0e945c0c0e1b136d915ee5098c095fdd0f47e158c7b18` |
| `focused-oracle-results.json` | `ff7aff31cf673dc1cbc5943d4efd329e1707fadbd10b09e113b95498b9abcfc9` |
| `recovered_focused_oracles.py` | `9258c52dc05221b6e9f2f61cd44d1c7607266bab3e6cf3d506dfa5b58a617c36` |
| `reader-correction.json` | `072b10bee8f606ea2382476904aede856fc2243f60b31d3e85ec3574c56bd53c` |

Terminal disposition: GAP-REVISE
