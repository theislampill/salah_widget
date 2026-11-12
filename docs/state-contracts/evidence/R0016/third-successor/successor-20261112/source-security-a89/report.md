# R0016 independent source/security review — first phase

## Disposition and authority

**Bounded technical source disposition: PASS.** I found no concrete R0016 source/security defect in the two complete installer files at candidate `a89bbb3ddac639cc787ba08d030e8b2539057387`, tree `efa716f4c8f1fe61c1a5a85b48bd97e813305d16`, or in the reviewed full20 acquisition changes. The final immutable documentation/evidence tree and the native-evidence joins remain **GAP** in this first-phase review. This is not readiness, acceptance, merge authority, distribution qualification, an audit-assess result, or audit closure.

The comparison base is accepted main `3b0e614114ef066de40db117d0e85c0031cf3e30`, tree `ffe72c83f59e56caf035ce2a44629ad516e55ab9`. Acquisition-change preservation was also compared with `8a360f5` and the installer bytes at `9c05df0` and `12904a8`.

The review is an ordinary independent technical review returned to the root governor. After I read `audit-assess` v0.4.0, I asked the governor for the formal route envelope it requires. The governor clarified that this assignment was outside audit-assess routing, that the canonical package layout had not been established, and that no formal child-skill authority was requested. No envelope, package proof, or audit authority is invented here. Root retains all acceptance/currentness/lifecycle decisions.

Reviewer identity: `/root/final_source_security`. The assignment requested no model override. The available developer self-identification is **GPT-6 Astra Pro**; a backend model attestation is not exposed to this reviewer. This is a declared identity, not independent proof of an exact backend variant or a claim of a different-model review. I had no candidate-authoring context or authoring role, read source before other current reviewer findings, and did not read those findings for this first-phase result.

## Evidence and verification

I read repository `AGENTS.md` and fetched the actual current [issue #22 contract](https://github.com/theislampill/salah_widget/issues/22) using the GitHub connector. The captured issue reports `updated_at=2026-11-12T06:23:59Z`; its complete returned body is retained in `issue22.json`. I read both installer files in full, the full20 carrier in full, the acquisition diff, the original direct-entry receiving predicates and relevant common/profile/source-input functions. I also inspected the calibration driver's fixed derivation and receiving logic without running it.

| Exact product file | Git blob | SHA-256 | Bytes |
| --- | --- | --- | ---: |
| `install.sh` | `e2e2640eb85adf302c87305cd68d642743785bb1` | `27442c0e6a6dbd6390ba1ea9b8b3efa2bfb2a910037e2c415756f9169a5c7b3f` | 46,460 |
| `install.ps1` | `28cfdae73305a2a2e5a58e30878bffea7b5142b8` | `07671cb9e6a0afb8eb9051a0a5f378d12e577877453a773860b3cf94d5e2951a` | 111,249 |

`source-manifest.json` inventories the 27 exact candidate files copied for examination. An inventory entry does not claim that every byte of every ancillary fixture received the same full read as the installers. `source_checks.py` performs inert comparisons and parsing only. It ran with **86/86 checks passing**, including exact source copies, acquisition pin joins, byte preservation of the accepted R13 lexer/R15 Windows staging block, original receiver-function preservation, retention of original case assertions, unchanged twenty-case denominator and budgets, Python AST parsing, and an isolated `bash -n` syntax check. The script neither imports nor executes an installer or native test harness. `checks.json` preserves the individual results. No native installer execution or original native receiving campaign was performed by this reviewer.

## Claim-level findings

### SS-01 — Bash entry preview and alternate artifact callers: PASS

At `install.sh:55–64`, platform and option validation precede discovery and staging. Main performs discovery at lines 818–835, then takes the offline branch at lines 840–871. That branch only reports plans, counts eligible/held/refused targets, keeps `ask` unresolved, retains the dashboard-replacement warning, and exits. The no-target and no-eligible routes are non-success. Terminal acquisition and the first selection read are after the preview exit at lines 874–876; staging is after a nonempty eligible selection at line 911.

The early boundary is reinforced at the artifact/effect helpers. `initialize_staging` refuses preview before checking or allocating roots (189–205); `select_asset` refuses before Python/network resolution (560–590); `download_tablissng_asset` refuses before root validation, cache inspection, mkdir or download (593–622); and `retain_asset`, `expand_chromium_asset`, `download_preset`, `install_tablissng`, and `show_import_instructions` have leading preview refusals (637, 654, 701, 731, 784). Those artifact helpers fail without printing a usable path. A cached ZIP, XPI, preset or unpacked directory therefore cannot become a successful preview artifact through one of these helpers.

`copy_text` returns non-success before clipboard commands, so existing `&& ok "Copied…"` callers cannot print a copied-success message for a suppressed copy (260–275). `open_url` returns before browser execution under either opening-suppression switch (236–257). The EXIT trap is installed before discovery, but `cleanup_staging` checks `DRY_RUN=0` and a nonempty owned scratch root before any identity probe or deletion (208–219). Preview cannot delete an earlier cache/manual bundle through that trap.

### SS-02 — PowerShell entry preview, cache and compiler boundaries: PASS

The environment-derived install source is explicitly validated at `install.ps1:34–37`; parameter binding and this validation occur before discovery or staging. The top level defines helpers and initializes empty in-memory state, then runs discovery. The preview branch at 1640–1666 precedes `Read-Host` selection at 1670 and `Initialize-Staging` at 1700. It preserves eligible/held/refused distinctions, unresolved remote facts, unresolved `ask`, manual NoOpen wording, the replacement warning, and unsuccessful zero-eligible behavior.

`Get-LatestRelease` checks `DryRun` before the in-process release cache (1141–1151). Selection, download and expansion refuse preview before artifact admission or effects (1154, 1334, 1371). `Download-Preset` returns `$null` before it can create a candidate or issue a request (1467–1469). `Show-ImportInstructions` and `Install-TablissNG` return before actual import/installation work or any store/fallback confirmation (1501–1502, 1535–1536). `Copy-Text` returns `$false` (788–795); host diagnostics do not populate the success pipeline with a pretend artifact. `Open-TargetUrl` returns before `Start-Process` (768–785).

The compiler/native helpers also have leading preview checks, including cached-type reuse: `Initialize-CompilerNative` checks before its existing-type return (57–61), and `Initialize-StagingNative` checks before `StageNative` type reuse (338–342). Compiler scratch creation, compiler invocation, private file/directory creation, staging initialization, artifact transactions, publication and archive work are guarded independently. Both compiler cleanup and owned-scratch cleanup return immediately under preview (228–230, 727–730). Defining the embedded C# string does not compile or execute it at top level.

The source-visible network routes are release lookup and downloads in these guarded helpers. Discovery reads local metadata. This is a source reachability finding; it is not a claim of independent global Windows transport containment or a complete accounting of native host startup behavior.

### SS-03 — Bash implicit temporary input and macOS discovery: PASS

The complete candidate Bash file contains no `<<` token. Former shell here-documents/here-strings now use process-substitution pipes or `printf` literals. This matters for Apple Bash 3.2 because parser/input transport must not create a hidden temporary file before an otherwise correct preview guard. The replacement preserves `read` in the current shell where target arrays/counters must survive.

Firefox preview runs Python with `-B` (378–383). When macOS resolves `python3` to the system developer-tool shim, `firefox_discovery_python` uses the selected toolchain path, resolves symlinks with a bounded loop, requires a physical executable under that toolchain, and refuses to invoke the original shim (327–358). Unavailable parsing leaves Firefox metadata unknown/held rather than authorizing installation from false/false extension flags. These source measures do not extend the separate macOS native transport-observability scope.

### SS-04 — R13 strict JSON lexer: PASS

`Test-StrictJson` at `install.ps1:942–1012` is byte-identical to the accepted-main block. It uses one `Match`/`NextMatch` sequence, a `\G`-anchored lexer, contiguous-index checks and a final whole-input consumption check. Whitespace alone cannot mark a root complete. The explicit frame stack enforces keys, colons, values and separators, including trailing-comma and unfinished-container refusal. JSON key escapes are decoded before insertion into an ordinal-ignore-case set, matching the downstream PowerShell property's case-insensitive lookup and preventing escaped/case-aliased duplicate-key ambiguity.

The string lexer alternatives distinguish ordinary characters from backslash escapes; the changed traversal does not introduce overlapping token alternatives or drop grammar validation. Discovery still converts unsupported/malformed metadata to a held result. This review establishes preservation and source structure, not a new native performance measurement.

### SS-05 — R15 private staging and retention boundaries: PASS

The entire Windows compiler/staging block from `Initialize-CompilerNative` through `Clear-OwnedScratch` is byte-identical to accepted main. The final parent policy admits user, SYSTEM or Administrators ownership only with the stated trusted-write predicate; ancestor admission separately accommodates the servicing principal. It does not transfer that broader parent policy to the private child. Private children are created exclusively with a user-owned protected descriptor and checked for the one full-control user ACE. Native path readback rejects reparse/non-disk objects, checks physical path and NTFS file identity, and holds directory leases through sensitive work. Compiler source/output and published artifacts have additional byte/identity checks. Cleanup retains material when custody cannot be proved and never treats an earlier manual bundle as disposable scratch.

The Bash B2 staging path remains `${TMPDIR:-/tmp}` admitted through `trusted_parent`, followed by private `mktemp` children under that parent and HOME (189–205). The supplied spelling may traverse only root-owned symlinks in root-owned non-group/other-writable containers; the resolved physical ancestry is then checked for owner/mode, including the root-owned sticky temporary-parent allowance (97–149). Private roots require the recorded device/inode/owner/mode identity and mode 700 (152–162); staged path traversal rejects symlinks and invalid components (165–186). Preview never calls the initializer and guarded helpers do not adopt roots or change permissions.

These are the existing supported local ownership boundaries. I found no concrete weakening from the preview integration. They are not a promise of security against an already-compromised same-user process or a new platform containment qualification.

### SS-06 — Normal manual flow and NoOpen preservation: PASS

The source still stages validated files and offers manual browser installation/import after ordinary selection. NoOpen remains local to browser opening: clipboard handoff, acquisition, retained files and manual confirmations remain on normal paths. The preview descriptions now explicitly show manual URL handling when NoOpen is also present. Both final normal summaries retain the manual-action boundary rather than claiming that pressing Enter proved browser installation. The PowerShell fallback is behind the leading installation preview guard, so a suppressed/failed preview asset cannot reach store confirmation.

The exact canonical preset input in the full20 carrier remains pinned. The reviewed acquisition changes do not edit either installer, the preset, browser discovery, UI/physics code or configuration encoding.

### SS-07 — Full20 acquisition isolation and strict comparator preservation: PASS

The added preparation is confined to `positive` and `no-open`. PowerShell 7 sets its scoped prelaunch no-gather environment only for those two cases; the other 18 cases retain the original environment requirement. PowerShell 5.1 uses a source-free native `ConvertFrom-Json` calibration process, observes its command/module/assembly identity, waits within the existing 60-second child budget, and records separate process/nonces. This is an observed preparation workload, not proof of the cause of historical warm20 variation.

The direct composition records all six warm/product inventory phases and four raw analysis-cache phases. It requires completed preparation's final rows to equal the product's initial rows, verifies preparation/product environment relationships, and retains the raw values. The original normal input postcondition still requires exact identity/name/security/byte equality outside the single validated retained bundle, with only the existing source-declared TEMP-parent mtime allowance. The analysis cache remains in the full input inventory and receives no exclusion. The original eight-entry retained inventory and normal effect arguments/counts remain enforced.

Mechanical comparison established byte identity for every preexisting direct-harness function except `_case_impl`, preservation of every original `require` predicate in that case function, and byte identity of the common/profile/product support and native driver inputs. The full20 wrapper requires the exact ordered twenty-case list, typed expected exits, complete input inventories, original receivers, raw receipt/file bindings and exact source pins. Its list, failure set and budget are unchanged. In particular, the 60-second child/setup limits were not extended by these changes.

Direct launch, host-only baseline and separate held full-file invocation are separate observations. The source-input relation checks actual read-context equivalence while retaining physical phase rows and lifecycle differences. It does not make full process lifecycles equal by subtraction. The wrapper explicitly records `independentHardContainment='NOT_ACQUIRED'` and null global transport telemetry; the Job Object bounds owned process lifetime. Neither a flag nor empty spy events proves global containment.

The older calibration driver pins its historical harness/carrier bytes and remains diagnostic-only. Its pinned dependencies are intentionally different from the newly integrated full20 carrier; a current-tree rerun cannot silently reinterpret it as a full20 result.

## Remaining joins: GAP

1. **Final immutable tree.** The governor said the current R0016 contract/matrix documents were being corrected in another lane. This review does not qualify those final bytes. On receipt of the final commit/tree, compare every installer/source input with this manifest, review the exact remaining delta, and bind this report only if the reviewed source is unchanged or any change is independently assessed.

2. **Native full20 originals.** This reviewer did not independently receive run `43220592915` artifacts. The root's assignment described a PS7 success awaiting original receiving, a PS5.1 first-attempt ACL setup/capture timeout before installer execution, and a same-candidate second attempt then running. These are parent-provided campaign status, not this review's native verdict. The final join must preserve the failure and bind each admitted original run/attempt, all twenty rows, command host, source/test bytes, real process observations and unchanged deadlines. No missing native pass is inferred here.

3. **Other native/platform joins.** The provided POSIX/core/routes/docs receiving packets belong to their respective receiving owners. Match the current installer blobs and relevant fixture/driver bytes to those exact original runs. Preserve macOS transport-observability limitations, Windows `NOT_ACQUIRED` hard containment, and raw direct/held/host lifecycle differences. This source finding supplies none of those missing observations by implication.

4. **Contract and public wording.** Final contract, matrix and evidence summary must distinguish the source finding from native observed results, historical diagnostics and distribution/closure. They must state the actual scoped normal preparation, preserve pending/unacquired limitations, and avoid representing a source-free calibration or the exact-source review as installed/deployed completion. The owner-approval-before-merge boundary remains with root.

## Output custody

All reviewer writes are under `/workspace/scratch/0dd4b9b6a244/reviews/final_source_security`. No repository or `.IMPLEMENTAUDIT` mutation, installer execution, external publication, commit, push, merge or issue update occurred in this lane. `hash-manifest.json` binds the first-phase report, checks, captured contract and exact-source inventory. A later final-tree join should be a separate artifact so this first-phase scope remains legible.
